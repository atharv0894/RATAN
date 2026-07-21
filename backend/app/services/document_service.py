import os
import time
import uuid
import hashlib
import logging
from app.database.sqlite import get_db_connection
from app.database.repositories import DocumentRepository, AuditRepository, get_system_user
from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import VectorStore
from app.rag.indexer import Indexer
from app.rag.chunker import Chunker
from app.rag.parsers.factory import ParserFactory
from app.storage.storage_service import StorageService
from app.entity.entity_extractor import EntityExtractor
from app.exceptions import DuplicateDocumentError

class DocumentService:
    def __init__(self):
        self.storage_service = StorageService()
        self.entity_extractor = EntityExtractor()

    @property
    def embedding_service(self):
        from app.services.dependencies import get_embedding_service
        return get_embedding_service()

    @property
    def vector_store(self):
        from app.services.dependencies import get_vector_store
        return get_vector_store()

    @property
    def indexer(self):
        return Indexer(self.embedding_service, self.vector_store)

    def _compute_checksum(self, file_path: str) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def process_and_index(self, filename: str, file_path: str, user_id: str, org_id: str, plant_id: str, dept_id: str, metadata: dict = None, is_reindex: bool = False):
        logging.info(f"[Upload lifecycle] Upload completed for {filename}")
        
        # 1. Validation
        stat = os.stat(file_path)
        if stat.st_size == 0:
            raise ValueError("File is empty.")
            
        checksum = self._compute_checksum(file_path)
        
        conn = get_db_connection()
        doc_repo = DocumentRepository(conn)
        audit_repo = AuditRepository(conn)
        
        try:
            # 1. Duplicate check
            if doc_repo.check_duplicate_checksum(checksum):
                raise DuplicateDocumentError("Checksum already exists in the system.")
                
            # 2. Document Identity
            doc_record = doc_repo.find_by_filename(filename)
            if doc_record:
                if doc_record['status'] in ('PROCESSING', 'INDEXING'):
                    raise ValueError("Cannot create a new version of a document currently being processed.")
                document_id = doc_record['id']
                latest_v = doc_repo.get_latest_version(document_id)
                prev_version_id = latest_v['id'] if latest_v else None
            else:
                meta = metadata or {}
                document_id = doc_repo.create_document(
                    filename=filename, title=meta.get("title", filename), 
                    user_id=user_id, org_id=org_id, plant_id=plant_id, dept_id=dept_id
                )
                
                # Apply initial metadata
                if meta:
                    update_fields = []
                    params = []
                    for key in ['description', 'category', 'equipment', 'language', 'author']:
                        if key in meta:
                            update_fields.append(f"{key} = ?")
                            params.append(meta[key])
                    if update_fields:
                        params.append(document_id)
                        cursor = conn.cursor()
                        cursor.execute(f"UPDATE documents SET {', '.join(update_fields)} WHERE id = ?", tuple(params))
                        
                prev_version_id = None
                
            # Calculate next version number for storage path
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(version_number) as max_v FROM document_versions WHERE document_id = ?", (document_id,))
            next_v = (cursor.fetchone()['max_v'] or 0) + 1
                
            # 3. Storage
            ext = os.path.splitext(filename)[1].lower()
            storage_path = f"documents/{document_id}/v{next_v}/original{ext}"
            
            with open(file_path, "rb") as f:
                self.storage_service.save(f, storage_path)
                
            start_time = time.time()
            emb_model = "sentence-transformers/all-MiniLM-L6-v2"
            vector_db = self.vector_store.__class__.__name__.replace("Store", "")
            meta = self.storage_service.get_metadata(storage_path)
            file_size = meta['size'] if meta else os.path.getsize(file_path)
            mime_type = meta['mime_type'] if meta else "application/pdf"
            
            # 4. Save Version
            version_id = doc_repo.add_version(
                document_id=document_id,
                checksum=checksum,
                size=file_size,
                mime=mime_type,
                storage_path=storage_path,
                chunk_count=0,
                vector_collection=vector_db,
                model=emb_model,
                user_id=user_id
            )
            
            # Add Processing Job
            job_id = str(uuid.uuid4())
            cursor.execute('''INSERT INTO processing_jobs (id, target_type, target_id, status, created_at, updated_at, started_at) 
                              VALUES (?, ?, ?, ?, ?, ?, ?)''',
                           (job_id, 'document_version', version_id, 'QUEUED', time.time(), time.time(), time.time()))
            
            # Transition to PROCESSING
            cursor.execute("UPDATE processing_jobs SET status = 'PROCESSING', updated_at = ? WHERE id = ?", (time.time(), job_id))
            
            cursor.execute("UPDATE document_versions SET status = 'PROCESSING' WHERE id = ?", (version_id,))
            cursor.execute("UPDATE documents SET status = 'PROCESSING' WHERE id = ?", (document_id,))
            conn.commit()
            audit_repo.log("UPLOAD", version_id, "PROCESSING", user_id=user_id)
            
            # 5. Parsing & Extraction
            parser = ParserFactory.get_parser(file_path)
            parsed_doc = parser.parse(file_path, filename=filename, use_ocr=True)
            
            # Update metadata from parsed doc if any
            if parsed_doc.metadata:
                # Mime Type
                if 'mime_type' in parsed_doc.metadata and parsed_doc.metadata['mime_type'] != mime_type:
                    cursor.execute("UPDATE document_versions SET mime_type = ? WHERE id = ?", (parsed_doc.metadata['mime_type'], version_id))
                
                # Knowledge Base Metadata extraction
                update_fields = []
                params = []
                for key in ['description', 'category', 'equipment', 'language', 'author']:
                    # Only apply extracted metadata if the document doesn't already have it
                    if key in parsed_doc.metadata:
                        update_fields.append(f"{key} = COALESCE({key}, ?)")
                        params.append(parsed_doc.metadata[key])
                if update_fields:
                    params.append(document_id)
                    cursor.execute(f"UPDATE documents SET {', '.join(update_fields)} WHERE id = ?", tuple(params))
            
            
            # 6. Chunking
            chunker = Chunker(max_chars=1500, overlap_chars=200)
            chunks, metadatas, chunk_ids = [], [], []
            
            for page in parsed_doc.pages:
                base_meta = {
                    "filename": filename, 
                    "page": page.page_number,
                    "document_id": document_id,
                    "version_id": version_id,
                    "version_number": next_v,
                    "is_latest": 1
                }
                for info in chunker.chunk_page_with_metadata(page, base_meta):
                    info['metadata']['heading'] = info['metadata'].get('section', '')
                    chunks.append(info['text'])
                    metadatas.append(info['metadata'])
                    chunk_ids.append(info['chunk_id'])

            if chunks:
                cursor.execute("UPDATE processing_jobs SET status = 'INDEXING', updated_at = ? WHERE id = ?", (time.time(), job_id))
                cursor.execute("UPDATE document_versions SET status = 'INDEXING' WHERE id = ?", (version_id,))
                conn.commit()
                self.indexer.index_chunks(chunks, metadatas=metadatas, chunk_ids=chunk_ids, document_id=document_id, filename=filename)
                
            cursor.execute("""
                UPDATE document_versions 
                SET chunk_count = ?, vector_count = ?, status = 'READY'
                WHERE id = ?
            """, (len(chunks), len(chunks), version_id))
            cursor.execute("UPDATE documents SET status = 'READY' WHERE id = ?", (document_id,))
            
            cursor.execute("UPDATE processing_jobs SET status = 'COMPLETED', finished_at = ?, updated_at = ? WHERE id = ?", (time.time(), time.time(), job_id))
            conn.commit()
            
            audit_repo.log("INDEX", version_id, "READY", user_id=user_id, execution_time_ms=int((time.time() - start_time)*1000))
            return document_id
            
        except Exception as e:
            if 'version_id' in locals():
                cursor = conn.cursor()
                cursor.execute("UPDATE document_versions SET status = 'FAILED' WHERE id = ?", (version_id,))
                cursor.execute("UPDATE documents SET status = 'FAILED' WHERE id = ?", (document_id,))
                if 'job_id' in locals():
                    cursor.execute("UPDATE processing_jobs SET status = 'FAILED', error_message = ?, finished_at = ? WHERE id = ?", 
                                   (str(e), time.time(), job_id))
                conn.commit()
                audit_repo.log("FAILED_INDEX", version_id, "FAILED", user_id=user_id)
            logging.error(f"[Indexing lifecycle] Indexing failed: {str(e)}")
            raise e
        finally:
            conn.close()

    def get_all_documents(self):
        conn = get_db_connection()
        doc_repo = DocumentRepository(conn)
        docs = doc_repo.list_latest_versions()
        conn.close()
        # Map to V1 response format for API compatibility
        return [{
            "document_id": d["document_id"],
            "filename": d["filename"],
            "status": d["status"],
            "file_size": d["file_size"],
            "chunk_count": d["chunk_count"],
            "storage_provider": "local",
            "version_number": d["version_number"],
            "is_latest": 1,
            "is_deleted": False
        } for d in docs]

    def get_document(self, document_id: str):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.id as document_id, d.filename, d.title, d.description, d.category, 
                   d.equipment, d.language, d.author, COALESCE(v.status, d.status) as status, v.chunk_count, v.uploaded_at as upload_time,
                   v.embedding_model, v.collection_name as vector_db, 0.0 as processing_time,
                   v.storage_path, v.checksum as checksum_sha256, v.version_number, v.is_latest,
                   d.deleted_at, d.deleted_by_user_id, d.delete_reason
            FROM documents d
            LEFT JOIN document_versions v ON d.id = v.document_id AND v.is_latest = 1
            WHERE d.id = ?
        """, (document_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def delete_document(self, document_id: str, user_id: str, reason: str = "User Requested"):
        conn = get_db_connection()
        doc_repo = DocumentRepository(conn)
        audit_repo = AuditRepository(conn)
        
        doc = self.get_document(document_id)
        if not doc:
            return False
            
        if doc['status'] in ('PROCESSING', 'INDEXING'):
            raise ValueError("Cannot delete a document that is currently processing.")
            
        if doc.get('deleted_at') is not None:
            raise ValueError("Document is already deleted.")

        try:
            doc_repo.soft_delete_document(document_id, user_id, reason)
            audit_repo.log("SOFT_DELETE", document_id, "Success", user_id=user_id)
            return True
        except Exception as e:
            # Compensating Transaction Pattern
            # If any failure occurs here, we log it and mark it for cleanup
            logging.error(f"Soft delete failed: {e}. Initiating compensating action.")
            cursor = conn.cursor()
            cursor.execute("UPDATE documents SET status = 'READY', deleted_at = NULL WHERE id = ?", (document_id,))
            conn.commit()
            audit_repo.log("FAILED_DELETE", document_id, "FAILED", user_id=user_id)
            raise e
        finally:
            conn.close()

    def restore_document(self, document_id: str, user_id: str):
        conn = get_db_connection()
        doc_repo = DocumentRepository(conn)
        audit_repo = AuditRepository(conn)
        
        doc = self.get_document(document_id)
        if not doc:
            return False
            
        if doc.get('deleted_at') is None:
            raise ValueError("Cannot restore a document that is not deleted.")
        
        try:
            doc_repo.restore_document(document_id)
            audit_repo.log("RESTORE", document_id, "Success", user_id=user_id)
            return True
        except Exception as e:
            logging.error(f"Restore failed: {e}")
            raise e
        finally:
            conn.close()

    def update_metadata(self, document_id: str, metadata: dict, user_id: str):
        conn = get_db_connection()
        cursor = conn.cursor()
        audit_repo = AuditRepository(conn)
        
        doc = self.get_document(document_id)
        if not doc:
            conn.close()
            return False
            
        if doc['status'] in ('PROCESSING', 'INDEXING'):
            conn.close()
            raise ValueError("Cannot modify metadata of a document currently processing.")
            
        update_fields = []
        params = []
        allowed_fields = ['title', 'description', 'category', 'equipment', 'language', 'author']
        
        for key in allowed_fields:
            if key in metadata:
                update_fields.append(f"{key} = ?")
                params.append(metadata[key])
                
        if update_fields:
            params.append(document_id)
            cursor.execute(f"UPDATE documents SET {', '.join(update_fields)}, updated_at = ? WHERE id = ?", (*params, time.time()))
            conn.commit()
            audit_repo.log("METADATA_UPDATE", document_id, "Success", user_id=user_id)
            
        conn.close()
        return True


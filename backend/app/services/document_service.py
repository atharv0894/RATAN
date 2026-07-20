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

    def process_and_index(self, filename: str, file_path: str, is_reindex: bool = False):
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
                document_id = doc_record['id']
                latest_v = doc_repo.get_latest_version(document_id)
                prev_version_id = latest_v['id'] if latest_v else None
            else:
                document_id = doc_repo.create_document(filename=filename, title=filename)
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
                model=emb_model
            )
            
            # Add Processing Job
            job_id = str(uuid.uuid4())
            cursor.execute('''INSERT INTO processing_jobs (id, target_type, target_id, status, created_at, updated_at) 
                              VALUES (?, ?, ?, ?, ?, ?)''',
                           (job_id, 'document_version', version_id, 'Processing', time.time(), time.time()))
            
            cursor.execute("UPDATE document_versions SET status = 'Processing' WHERE id = ?", (version_id,))
            conn.commit()
            audit_repo.log("UPLOAD", version_id, "Processing")
            
            # 5. Parsing & Extraction
            parser = ParserFactory.get_parser(file_path)
            parsed_doc = parser.parse(file_path, filename=filename, use_ocr=True)
            
            # Update metadata from parsed doc if any
            if 'mime_type' in parsed_doc.metadata and parsed_doc.metadata['mime_type'] != mime_type:
                cursor.execute("UPDATE document_versions SET mime_type = ? WHERE id = ?", (parsed_doc.metadata['mime_type'], version_id))
            
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
                self.indexer.index_chunks(chunks, metadatas=metadatas, chunk_ids=chunk_ids, document_id=document_id, filename=filename)
                
            cursor.execute("""
                UPDATE document_versions 
                SET chunk_count = ?, vector_count = ?, status = 'Indexed'
                WHERE id = ?
            """, (len(chunks), len(chunks), version_id))
            
            cursor.execute("UPDATE processing_jobs SET status = 'Completed', finished_at = ? WHERE id = ?", (time.time(), job_id))
            conn.commit()
            
            audit_repo.log("INDEX", version_id, "Success", execution_time_ms=int((time.time() - start_time)*1000))
            return document_id
            
        except Exception as e:
            if 'version_id' in locals():
                cursor = conn.cursor()
                cursor.execute("UPDATE document_versions SET status = 'Failed' WHERE id = ?", (version_id,))
                if 'job_id' in locals():
                    cursor.execute("UPDATE processing_jobs SET status = 'Failed', error_message = ?, finished_at = ? WHERE id = ?", 
                                   (str(e), time.time(), job_id))
                conn.commit()
                audit_repo.log("INDEX", version_id, "Failed")
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
            SELECT d.id as document_id, d.filename, v.status, v.chunk_count, v.uploaded_at as upload_time,
                   v.embedding_model, v.collection_name as vector_db, 0.0 as processing_time,
                   v.storage_path, v.checksum as checksum_sha256, v.version_number, v.is_latest, 
                   CASE WHEN d.deleted_at IS NOT NULL THEN 1 ELSE 0 END as is_deleted
            FROM documents d
            LEFT JOIN document_versions v ON d.id = v.document_id AND v.is_latest = 1
            WHERE d.id = ?
        """, (document_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def delete_document(self, document_id: str):
        conn = get_db_connection()
        doc_repo = DocumentRepository(conn)
        audit_repo = AuditRepository(conn)
        
        try:
            doc_repo.soft_delete_document(document_id)
            audit_repo.log("SOFT_DELETE", document_id, "Success")
            return True
        except Exception as e:
            logging.error(f"Soft delete failed: {e}")
            raise e
        finally:
            conn.close()

    def restore_document(self, document_id: str):
        conn = get_db_connection()
        doc_repo = DocumentRepository(conn)
        audit_repo = AuditRepository(conn)
        
        try:
            doc_repo.restore_document(document_id)
            audit_repo.log("RESTORE", document_id, "Success")
            return True
        except Exception as e:
            logging.error(f"Restore failed: {e}")
            raise e
        finally:
            conn.close()


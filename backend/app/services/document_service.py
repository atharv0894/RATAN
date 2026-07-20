import os
import time
import uuid
import hashlib
from app.database.sqlite import get_db_connection
from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import VectorStore
from app.rag.indexer import Indexer
from app.rag.document_loaders import DocumentLoader
from app.rag.chunker import Chunker
from app.storage.storage_service import StorageService
from app.entity.entity_extractor import EntityExtractor
from app.exceptions import DuplicateDocumentError
import logging

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
        from app.rag.indexer import Indexer
        return Indexer(self.embedding_service, self.vector_store)

    def _compute_checksum(self, file_path: str) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def get_document_by_checksum(self, checksum: str) -> str:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT document_id FROM documents WHERE checksum_sha256 = ?", (checksum,))
        row = cursor.fetchone()
        conn.close()
        return row["document_id"] if row else None

    def process_and_index(self, filename: str, file_path: str, document_id: str = None, is_reindex: bool = False):
        logging.info(f"[Upload lifecycle] Upload completed for {filename}")
        
        # Checksum validation
        checksum = self._compute_checksum(file_path)
        if not is_reindex:
            existing_id = self.get_document_by_checksum(checksum)
            if existing_id:
                raise DuplicateDocumentError(existing_id)
            
        start_time = time.time()
        
        # Determine model and db
        emb_model = "sentence-transformers/all-MiniLM-L6-v2"
        vector_db = self.vector_store.__class__.__name__.replace("Store", "")
        
        document_id = document_id or str(uuid.uuid4())
        
        # Initialize DB status
        conn = get_db_connection()
        cursor = conn.cursor()
        if not is_reindex:
            cursor.execute(
                '''INSERT INTO documents 
                   (document_id, filename, status, upload_time, embedding_model, vector_db, chunk_count, processing_time)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (document_id, filename, "Processing", time.time(), emb_model, vector_db, 0, 0.0)
            )
        else:
            cursor.execute("UPDATE documents SET status = 'Processing' WHERE document_id = ?", (document_id,))
        conn.commit()
        
        try:
            logging.info(f"[Indexing lifecycle] Indexing started for {document_id}")
            # Load and chunk
            loader = DocumentLoader()
            chunker = Chunker(max_chars=1500, overlap_chars=200)
            pages = loader.load_file(file_path)
            page_count = len(pages)
            
            chunks = []
            metadatas = []
            chunk_ids = []
            
            # Combine all text for classification
            full_text = []
            
            for page in pages:
                page_text = page['text']
                full_text.append(page_text)
                base_meta = {"source": filename, "page_no": page.get('page_no', 1)}
                page_chunks_info = chunker.chunk_text_with_metadata(page_text, base_meta)
                for info in page_chunks_info:
                    chunks.append(info['text'])
                    metadatas.append(info['metadata'])
                    chunk_ids.append(info['chunk_id'])
                    
                    # Entity Extraction per chunk
                    try:
                        extracted_entities = self.entity_extractor.extract_from_text(info['text'])
                        if extracted_entities:
                            self.entity_extractor.save_entities(
                                document_id=document_id,
                                chunk_id=info['chunk_id'],
                                page_number=base_meta['page_no'],
                                section="Content",
                                entities=extracted_entities
                            )
                    except Exception as e:
                        logging.warning(f"Entity extraction failed for chunk {info['chunk_id']}: {str(e)}")
            
            # Document Classification
            doc_class = "Unknown"
            try:
                doc_class = self.entity_extractor.classify_document("\n".join(full_text))
            except Exception as e:
                logging.warning(f"Document classification failed: {str(e)}")
                    
            # Index
            if chunks:
                self.indexer.index_chunks(chunks, metadatas=metadatas, chunk_ids=chunk_ids, document_id=document_id, filename=filename)
                
            processing_time = time.time() - start_time
            logging.info(f"[Indexing lifecycle] Indexing completed for {document_id}")
            
            # Metadata update
            meta = self.storage_service.get_metadata(document_id)
            file_size = meta['size'] if meta else os.path.getsize(file_path)
            mime_type = meta['mime_type'] if meta else "application/pdf"
            storage_path = self.storage_service.get_local_path(document_id) or file_path
            
            # Save to DB
            cursor.execute(
                '''UPDATE documents SET 
                   status = 'Indexed', 
                   chunk_count = ?, 
                   processing_time = ?,
                   storage_provider = ?,
                   storage_path = ?,
                   file_size = ?,
                   page_count = ?,
                   checksum_sha256 = ?,
                   mime_type = ?,
                   index_status = 'Success',
                   last_indexed = ?,
                   document_class = ?
                   WHERE document_id = ?''',
                (len(chunks), processing_time, self.storage_service.provider_name, storage_path, 
                 file_size, page_count, checksum, mime_type, time.time(), doc_class, document_id)
            )
            conn.commit()
            
        except Exception as e:
            cursor.execute("UPDATE documents SET status = 'Failed', index_status = 'Error' WHERE document_id = ?", (document_id,))
            conn.commit()
            logging.error(f"[Indexing lifecycle] Indexing failed for {document_id}: {str(e)}")
            raise e
        finally:
            conn.close()
            
        return document_id

    def get_all_documents(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents ORDER BY upload_time DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_document(self, document_id: str):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE document_id = ?", (document_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

    def delete_document(self, document_id: str):
        doc = self.get_document(document_id)
        if not doc:
            return False
            
        logging.info(f"[Deletion] Deleting {document_id}")
        
        # Delete from DB
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM documents WHERE document_id = ?", (document_id,))
        conn.commit()
        conn.close()
        
        # Delete from vector store
        try:
            if hasattr(self.vector_store, 'delete_by_source'):
                self.vector_store.delete_by_source(doc['filename'])
        except Exception as e:
            logging.warning(f"[Deletion] Warning: Vector delete failed - {e}")
            
        # Try to delete original file in storage
        try:
            self.storage_service.delete(document_id)
        except Exception as e:
            logging.warning(f"[Deletion] Warning: Storage delete failed - {e}")
                    
        return True
        
    def reindex_document(self, document_id: str):
        doc = self.get_document(document_id)
        if not doc:
            return None
            
        logging.info(f"[Reindex] Reindexing {document_id}")
        
        # 1. Read existing PDF
        local_path = self.storage_service.get_local_path(document_id)
        if not local_path or not os.path.exists(local_path):
            raise FileNotFoundError("Original file not found in storage")
            
        # 2. Delete old vectors
        try:
            if hasattr(self.vector_store, 'delete_by_source'):
                self.vector_store.delete_by_source(doc['filename'])
        except Exception as e:
            logging.warning(f"[Reindex] Warning: Vector delete failed - {e}")
            
        # 3. Re-ingest
        return self.process_and_index(doc['filename'], local_path, document_id=document_id, is_reindex=True)


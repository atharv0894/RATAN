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

class DocumentService:
    def __init__(self, embedding_service=None, vector_store=None):
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or VectorStore()
        self.indexer = Indexer(self.embedding_service, self.vector_store)
        self.storage_service = StorageService()

    def _compute_checksum(self, file_path: str) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def check_duplicate_checksum(self, checksum: str) -> bool:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT document_id FROM documents WHERE checksum_sha256 = ?", (checksum,))
        row = cursor.fetchone()
        conn.close()
        return row is not None

    def process_and_index(self, filename: str, file_path: str, document_id: str = None, is_reindex: bool = False):
        print(f"[Upload lifecycle] Upload completed for {filename}")
        
        # Checksum validation
        checksum = self._compute_checksum(file_path)
        if not is_reindex and self.check_duplicate_checksum(checksum):
            raise ValueError("DUPLICATE_CHECKSUM")
            
        start_time = time.time()
        
        # Determine model and db
        emb_model = "BAAI/bge-m3"
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
            print(f"[Indexing lifecycle] Indexing started for {document_id}")
            # Load and chunk
            loader = DocumentLoader()
            chunker = Chunker(max_chars=1500, overlap_chars=200)
            pages = loader.load_file(file_path)
            page_count = len(pages)
            
            chunks = []
            metadatas = []
            chunk_ids = []
            for page in pages:
                page_text = page['text']
                base_meta = {"source": filename, "page_no": page.get('page_no', 1)}
                page_chunks_info = chunker.chunk_text_with_metadata(page_text, base_meta)
                for info in page_chunks_info:
                    chunks.append(info['text'])
                    metadatas.append(info['metadata'])
                    chunk_ids.append(info['chunk_id'])
                    
            # Index
            if chunks:
                self.indexer.index_chunks(chunks, metadatas=metadatas, chunk_ids=chunk_ids)
                
            processing_time = time.time() - start_time
            print(f"[Indexing lifecycle] Indexing completed for {document_id}")
            
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
                   last_indexed = ?
                   WHERE document_id = ?''',
                (len(chunks), processing_time, self.storage_service.provider_name, storage_path, 
                 file_size, page_count, checksum, mime_type, time.time(), document_id)
            )
            conn.commit()
            
        except Exception as e:
            cursor.execute("UPDATE documents SET status = 'Failed', index_status = 'Error' WHERE document_id = ?", (document_id,))
            conn.commit()
            print(f"[Indexing lifecycle] Indexing failed for {document_id}: {str(e)}")
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
            
        print(f"[Deletion] Deleting {document_id}")
        
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
            print(f"[Deletion] Warning: Vector delete failed - {e}")
            pass
            
        # Try to delete original file in storage
        try:
            self.storage_service.delete(document_id)
        except Exception as e:
            print(f"[Deletion] Warning: Storage delete failed - {e}")
            pass
                    
        return True
        
    def reindex_document(self, document_id: str):
        doc = self.get_document(document_id)
        if not doc:
            return None
            
        print(f"[Reindex] Reindexing {document_id}")
        
        # 1. Read existing PDF
        local_path = self.storage_service.get_local_path(document_id)
        if not local_path or not os.path.exists(local_path):
            raise FileNotFoundError("Original file not found in storage")
            
        # 2. Delete old vectors
        try:
            if hasattr(self.vector_store, 'delete_by_source'):
                self.vector_store.delete_by_source(doc['filename'])
        except Exception as e:
            print(f"[Reindex] Warning: Vector delete failed - {e}")
            
        # 3. Re-ingest
        return self.process_and_index(doc['filename'], local_path, document_id=document_id, is_reindex=True)


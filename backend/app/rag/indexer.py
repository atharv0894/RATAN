import os
import time
import traceback
import uuid
import logging
from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import VectorStore

class QdrantUploadError(Exception):
    def __init__(self, error_details: dict):
        self.error_details = error_details
        super().__init__(f"Qdrant upload failed: {error_details.get('reason')}")

class Indexer:
    def __init__(self, embedding_service=None, vector_store=None):
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or VectorStore()
        
    def index_chunk(self, text: str, metadata: dict = None, chunk_id: str = None):
        if not chunk_id:
            chunk_id = str(uuid.uuid4())
        embedding = self.embedding_service.generate_embedding(text)
        
        # Use upsert to overwrite duplicates safely
        self.vector_store.upsert(
            ids=[chunk_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata] if metadata else [{}]
        )
        return chunk_id
        
    def _upsert_with_retry(self, ids, embeddings, documents, metadatas, batch_num):
        max_retries = 3
        base_delay = 1
        
        for attempt in range(max_retries + 1):
            try:
                self.vector_store.upsert(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas
                )
                return
            except Exception as e:
                # Don't retry validation errors, like 400 Bad Request
                if "Bad Request" in str(e) or "Validation" in str(e):
                    raise QdrantUploadError({
                        "status": "failed",
                        "stage": "qdrant_upload",
                        "reason": f"Validation error: {str(e)}",
                        "batch": batch_num,
                        "retry_count": attempt
                    })
                
                if attempt == max_retries:
                    traceback.print_exc()
                    reason = "Write timeout" if "timeout" in str(e).lower() else str(e)
                    raise QdrantUploadError({
                        "status": "failed",
                        "stage": "qdrant_upload",
                        "reason": reason,
                        "batch": batch_num,
                        "retry_count": attempt
                    })
                    
                time.sleep(base_delay * (2 ** attempt))

    def index_chunks(self, chunks: list[str], metadatas: list[dict] = None, chunk_ids: list[str] = None, document_id: str = None, filename: str = None):
        if not chunks:
            return []
            
        if not chunk_ids:
            chunk_ids = [str(uuid.uuid4()) for _ in chunks]
            
        if metadatas is None:
            metadatas = [{} for _ in chunks]

        emb_batch_size = int(os.environ.get("EMBEDDING_BATCH_SIZE", 64))
        # Use a single batch size to fuse embedding and uploading, saving RAM
        batch_size = min(emb_batch_size, int(os.environ.get("QDRANT_BATCH_SIZE", 128)))
        
        total_batches = (len(chunks) + batch_size - 1) // batch_size
        
        if document_id:
            logging.info(f"Document ID: {document_id}")
        if filename:
            logging.info(f"File name: {filename}")
        logging.info(f"Total chunks: {len(chunks)}")
        
        start_time = time.time()
        
        # 1 & 2. Fused Embedding and Upload Loop (Memory Efficient)
        for i in range(total_batches):
            batch_num = i + 1
            logging.info(f"Processing batch {batch_num}/{total_batches}...")
            start_idx = i * batch_size
            end_idx = min(start_idx + batch_size, len(chunks))
            
            batch_chunks = chunks[start_idx:end_idx]
            batch_ids = chunk_ids[start_idx:end_idx]
            batch_metas = metadatas[start_idx:end_idx]
            
            # Generate embeddings
            batch_embeddings = self.embedding_service.generate_embeddings(batch_chunks)
            
            # Upsert with retry logic immediately to free memory
            self._upsert_with_retry(batch_ids, batch_embeddings, batch_chunks, batch_metas, batch_num)
            
        elapsed = round(time.time() - start_time, 1)
        logging.info(f"Indexing completed in {elapsed} seconds.")
        
        return chunk_ids

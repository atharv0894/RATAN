import uuid
from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import VectorStore

class Indexer:
    def __init__(self, embedding_service=None, vector_store=None):
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or VectorStore()
        self.collection = self.vector_store.get_collection()
        
    def index_chunk(self, text: str, metadata: dict = None, chunk_id: str = None):
        if not chunk_id:
            chunk_id = str(uuid.uuid4())
        embedding = self.embedding_service.generate_embedding(text)
        
        # Use upsert to overwrite duplicates safely
        self.collection.upsert(
            ids=[chunk_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata] if metadata else [{}]
        )
        return chunk_id
        
    def index_chunks(self, chunks: list[str], metadatas: list[dict] = None, chunk_ids: list[str] = None):
        if not chunks:
            return []
            
        if not chunk_ids:
            chunk_ids = [str(uuid.uuid4()) for _ in chunks]
            
        # Use batched generation for massive speedup
        embeddings = self.embedding_service.generate_embeddings(chunks)
        
        if metadatas is None:
            metadatas = [{} for _ in chunks]
            
        self.collection.upsert(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )
        return chunk_ids

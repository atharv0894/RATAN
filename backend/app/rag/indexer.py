import uuid
from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import VectorStore

class Indexer:
    def __init__(self, embedding_service=None, vector_store=None):
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or VectorStore()
        self.collection = self.vector_store.get_collection()
        
    def index_chunk(self, text: str, metadata: dict = None):
        chunk_id = str(uuid.uuid4())
        embedding = self.embedding_service.generate_embedding(text)
        
        self.collection.add(
            ids=[chunk_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata] if metadata else [{}]
        )
        return chunk_id
        
    def index_chunks(self, chunks: list[str], metadatas: list[dict] = None):
        if not chunks:
            return []
            
        chunk_ids = [str(uuid.uuid4()) for _ in chunks]
        embeddings = [self.embedding_service.generate_embedding(text) for text in chunks]
        
        if metadatas is None:
            metadatas = [{} for _ in chunks]
            
        self.collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )
        return chunk_ids

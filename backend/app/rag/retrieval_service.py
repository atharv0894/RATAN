from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import VectorStore

class RetrievalService:
    def __init__(self, embedding_service=None, vector_store=None):
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or VectorStore()
        self.collection = self.vector_store.get_collection()
        
    def retrieve(self, query: str, top_k: int = 5):
        query_embedding = self.embedding_service.generate_embedding(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        retrieved_chunks = []
        if results and results['documents'] and len(results['documents']) > 0:
            documents = results['documents'][0]
            metadatas = results['metadatas'][0] if results.get('metadatas') else [{} for _ in documents]
            distances = results['distances'][0] if results.get('distances') else [0 for _ in documents]
            
            for i in range(len(documents)):
                retrieved_chunks.append({
                    "text": documents[i],
                    "metadata": metadatas[i],
                    "distance": distances[i]
                })
                
        return retrieved_chunks

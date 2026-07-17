# pyrefly: ignore [missing-import]
import numpy as np
from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import VectorStore

class RetrievalService:
    def __init__(self, embedding_service=None, vector_store=None):
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or VectorStore()

    def _cosine_similarity(self, a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def mmr(self, query_embedding, docs, embeddings, k=6, lambda_mult=0.5):
        """Maximal Marginal Relevance"""
        if not docs:
            return []
            
        selected = []
        unselected = list(range(len(docs)))
        
        while len(selected) < min(k, len(docs)):
            best_score = -float('inf')
            best_idx = -1
            
            for idx in unselected:
                sim_to_query = self._cosine_similarity(query_embedding, embeddings[idx])
                
                sim_to_selected = 0
                if selected:
                    sim_to_selected = max([self._cosine_similarity(embeddings[idx], embeddings[s_idx]) for s_idx in selected])
                    
                mmr_score = lambda_mult * sim_to_query - (1 - lambda_mult) * sim_to_selected
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = idx
                    
            if best_idx != -1:
                selected.append(best_idx)
                unselected.remove(best_idx)
            else:
                break
                
        return [docs[i] for i in selected]
        
    def retrieve(self, query: str, top_k: int = 6, fetch_k: int = 20, lambda_mult: float = 0.5, where: dict = None):
        query_embedding = self.embedding_service.generate_embeddings([query])[0]
        
        # Include embeddings in the results to compute MMR
        results = self.vector_store.query(
            query_embeddings=[query_embedding],
            n_results=fetch_k,
            include=['documents', 'metadatas', 'distances', 'embeddings'],
            where=where
        )
        
        if not results or not results['documents'] or len(results['documents']) == 0 or not results['documents'][0]:
            return []

        documents = results['documents'][0]
        metadatas = results['metadatas'][0]
        distances = results['distances'][0]
        embeddings = results['embeddings'][0]
        
        # Deduplicate by chunk_id first
        seen_chunks = set()
        unique_docs = []
        unique_embeddings = []
        
        for i in range(len(documents)):
            chunk_id = metadatas[i].get('chunk_id')
            if not chunk_id:
                # Fallback to source + page + hash
                import hashlib
                content_hash = hashlib.sha256(documents[i].lower().encode('utf-8')).hexdigest()
                chunk_id = f"{metadatas[i].get('source')}_{metadatas[i].get('page_no')}_{content_hash}"
                
            if chunk_id not in seen_chunks:
                seen_chunks.add(chunk_id)
                unique_docs.append({
                    "text": documents[i],
                    "metadata": metadatas[i],
                    "distance": distances[i],
                    "chunk_id": chunk_id
                })
                unique_embeddings.append(embeddings[i])
                
        # Apply MMR
        final_chunks = self.mmr(query_embedding, unique_docs, unique_embeddings, k=top_k, lambda_mult=lambda_mult)
        return final_chunks

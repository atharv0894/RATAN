from abc import ABC, abstractmethod
import numpy as np

class SearchStrategy(ABC):
    @abstractmethod
    def execute(self, query: str, query_embedding: list, vector_store, fetch_k: int, top_k: int, where: dict) -> list:
        """Executes the specific search strategy and returns a list of dictionaries with 'text', 'metadata', 'distance', 'chunk_id'"""
        pass
        
    def _cosine_similarity(self, a, b):
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return np.dot(a, b) / (norm_a * norm_b)
        
    def _deduplicate(self, documents, metadatas, distances, embeddings=None):
        seen_chunks = set()
        unique_docs = []
        for i in range(len(documents)):
            chunk_id = metadatas[i].get('chunk_id')
            if not chunk_id:
                import hashlib
                content_hash = hashlib.sha256(documents[i].lower().encode('utf-8')).hexdigest()
                chunk_id = f"{metadatas[i].get('source')}_{metadatas[i].get('page_no')}_{content_hash}"
                
            if chunk_id not in seen_chunks:
                seen_chunks.add(chunk_id)
                meta = metadatas[i]
                
                # Convert Qdrant distance to a rough similarity score (if using Cosine, distance is often 1 - cos_sim or similar, assuming distance here)
                similarity_score = max(0.0, 1.0 - distances[i]) 
                
                unique_docs.append({
                    "document_id": meta.get('document_id', ''),
                    "document_name": meta.get('filename', meta.get('source', '')),
                    "version": meta.get('version_number', 1),
                    "page": meta.get('page', 1),
                    "heading": meta.get('heading', ''),
                    "section": meta.get('section', ''),
                    "chunk_id": chunk_id,
                    "similarity_score": similarity_score,
                    "rerank_score": 0.0, # Will be set by Reranker
                    "metadata": meta,
                    "text": documents[i],
                    "embedding": embeddings[i] if embeddings else None
                })
        return unique_docs

class SimilaritySearch(SearchStrategy):
    def execute(self, query: str, query_embedding: list, vector_store, fetch_k: int, top_k: int, where: dict) -> list:
        results = vector_store.query(
            query_embeddings=[query_embedding],
            n_results=fetch_k,
            include=['documents', 'metadatas', 'distances'],
            where=where
        )
        if not results or not results.get('documents') or len(results['documents'][0]) == 0:
            return []
            
        docs = self._deduplicate(results['documents'][0], results['metadatas'][0], results['distances'][0], None)
        # Sort by distance (Qdrant uses Cosine, so higher distance usually means lower similarity depending on normalization, but we'll assume sorting logic exists in Qdrant)
        # We will just return top_k
        return docs[:top_k]

class MMRSearch(SearchStrategy):
    def execute(self, query: str, query_embedding: list, vector_store, fetch_k: int, top_k: int, where: dict) -> list:
        results = vector_store.query(
            query_embeddings=[query_embedding],
            n_results=fetch_k,
            include=['documents', 'metadatas', 'distances', 'embeddings'],
            where=where
        )
        if not results or not results.get('documents') or len(results['documents'][0]) == 0:
            return []
            
        docs = self._deduplicate(results['documents'][0], results['metadatas'][0], results['distances'][0], results['embeddings'][0])
        
        lambda_mult = 0.5
        selected = []
        unselected = list(range(len(docs)))
        
        while len(selected) < min(top_k, len(docs)):
            best_score = -float('inf')
            best_idx = -1
            
            for idx in unselected:
                sim_to_query = self._cosine_similarity(query_embedding, docs[idx]['embedding'])
                
                sim_to_selected = 0
                if selected:
                    sim_to_selected = max([self._cosine_similarity(docs[idx]['embedding'], docs[s_idx]['embedding']) for s_idx in selected])
                    
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

class MetadataSearch(SearchStrategy):
    """Fallback search when the query is highly structured and vector sim is less important."""
    def execute(self, query: str, query_embedding: list, vector_store, fetch_k: int, top_k: int, where: dict) -> list:
        # Same as similarity search but potentially fetching more and relying entirely on exact metadata filters.
        return SimilaritySearch().execute(query, query_embedding, vector_store, fetch_k, top_k, where)

class HybridSearch(SearchStrategy):
    """Combines metadata exact matches and vector similarity."""
    def execute(self, query: str, query_embedding: list, vector_store, fetch_k: int, top_k: int, where: dict) -> list:
        # In a real hybrid setup with keyword (BM25), we'd merge scores. 
        # Here we mimic it by running MMR with broader fetch_k.
        return MMRSearch().execute(query, query_embedding, vector_store, fetch_k * 2, top_k, where)

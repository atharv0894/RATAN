class Reranker:
    @staticmethod
    def rerank(query: str, chunks: list) -> list:
        """
        Reranks chunks based on semantic distance (from Qdrant/MMR),
        metadata relevance, document version, and section importance.
        """
        if not chunks:
            return []
            
        lower_query = query.lower()
        
        for chunk in chunks:
            base_score = 1.0 / (chunk.get('distance', 1.0) + 0.001) # Inverse of distance
            meta = chunk.get('metadata', {})
            
            # Version Boost
            version = meta.get('version_number', 1)
            base_score += (version * 0.05)
            
            # Heading/Section Similarity Boost
            heading = str(meta.get('heading', '')).lower()
            if heading and any(word in heading for word in lower_query.split()):
                base_score += 0.2
                
            # Exact Term Match in text
            if any(word in str(chunk.get('text', '')).lower() for word in lower_query.split() if len(word) > 4):
                base_score += 0.1
                
            chunk['rerank_score'] = base_score
            
        # Sort by the custom rerank_score descending
        ranked = sorted(chunks, key=lambda x: x.get('rerank_score', 0), reverse=True)
        return ranked

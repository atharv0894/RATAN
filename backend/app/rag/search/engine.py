import time
import logging
from .strategies import SearchStrategy, SimilaritySearch, MMRSearch, HybridSearch, MetadataSearch

class SearchEngine:
    def __init__(self, embedding_service, vector_store):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        
    def _select_strategy(self, intent: str, filters: dict) -> SearchStrategy:
        """Dynamically select strategy based on query intent and filters."""
        if intent in ['Comparison', 'Summary']:
            return MMRSearch()
        elif intent == 'Procedure':
            return HybridSearch()
        elif filters and len(filters) > 2:
            return MetadataSearch()
        else:
            return SimilaritySearch()

    def _validate_filters(self, filters: dict) -> dict:
        """Sanitize and validate metadata filters to prevent injection."""
        allowed_keys = {'organization', 'plant', 'department', 'equipment', 'document_type', 'version', 'status', 'latest_only', 'is_latest'}
        validated = {}
        if filters:
            for k, v in filters.items():
                if k in allowed_keys:
                    validated[k] = v
        return validated

    def _apply_auth_filters(self, filters: dict, user_context: dict) -> dict:
        """Enforce tenant/organization level isolation."""
        if user_context and 'organization' in user_context:
            filters['organization'] = user_context['organization']
        return filters

    def search(self, query: str, intent: str, filters: dict, top_k: int = 6, fetch_k: int = 20, user_context: dict = None) -> tuple:
        """
        Executes a search using the dynamically selected strategy.
        Returns a tuple of (results, strategy_name, latency)
        """
        strategy = self._select_strategy(intent, filters)
        strategy_name = strategy.__class__.__name__
        
        logging.info(f"[SearchEngine] Selected Strategy: {strategy_name}")
        
        start_time = time.time()
        
        query_embedding = self.embedding_service.generate_embeddings([query])[0]
        
        valid_filters = self._validate_filters(filters)
        valid_filters = self._apply_auth_filters(valid_filters, user_context)
        
        where_clause = {"is_latest": 1}
        if valid_filters:
            where_clause.update(valid_filters)
            
        results = strategy.execute(
            query=query,
            query_embedding=query_embedding,
            vector_store=self.vector_store,
            fetch_k=fetch_k,
            top_k=top_k,
            where=where_clause
        )
        
        latency = time.time() - start_time
        logging.info(f"[SearchEngine] Retrieved {len(results)} chunks in {latency:.3f}s")
        
        return results, strategy_name, latency

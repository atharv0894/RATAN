import pytest
from app.rag.search.engine import SearchEngine
from app.rag.search.strategies import SimilaritySearch, MMRSearch, HybridSearch, MetadataSearch

def test_search_engine_strategy_selection():
    engine = SearchEngine(embedding_service=None, vector_store=None)
    
    # Procedure intent -> Hybrid
    strategy = engine._select_strategy("Procedure", {})
    assert isinstance(strategy, HybridSearch)
    
    # Summary intent -> MMR
    strategy = engine._select_strategy("Summary", {})
    assert isinstance(strategy, MMRSearch)
    
    # Highly filtered -> Metadata
    strategy = engine._select_strategy("General", {"plant": "P1", "department": "D1", "equipment": "E1"})
    assert isinstance(strategy, MetadataSearch)
    
    # Basic -> Similarity
    strategy = engine._select_strategy("General", {})
    assert isinstance(strategy, SimilaritySearch)

def test_auth_filter_injection():
    engine = SearchEngine(embedding_service=None, vector_store=None)
    
    user_ctx = {"organization": "CorpA"}
    filters = engine._apply_auth_filters({"plant": "Plant1"}, user_ctx)
    
    assert filters["organization"] == "CorpA"
    assert filters["plant"] == "Plant1"

def test_filter_validation():
    engine = SearchEngine(embedding_service=None, vector_store=None)
    
    malicious_filters = {
        "plant": "Plant1",
        "drop_table": True,
        "__proto__": {}
    }
    
    clean = engine._validate_filters(malicious_filters)
    assert "plant" in clean
    assert "drop_table" not in clean
    assert "__proto__" not in clean

# pyrefly: ignore [missing-import]
from fastapi import APIRouter
from app.models.responses import StatsResponse
from app.services.dependencies import get_document_service
import sys
import io
import time

router = APIRouter()
START_TIME = time.time()

@router.get("", response_model=StatsResponse)
def get_stats():
    from app.rag.vector_store import VectorStore
    
    doc_service = get_document_service()
    docs = doc_service.get_all_documents()
    num_docs = len(docs)
    
    db_type = "Unknown"
    vector_count = 0
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        vector_store = VectorStore()
        store_class = vector_store.__class__.__name__
        if store_class == "QdrantStore":
            db_type = "Qdrant"
            vector_count = vector_store.client.count(collection_name=vector_store.collection_name).count
        elif store_class == "ChromaStore":
            db_type = "Chroma"
            vector_count = vector_store.collection.count()
    except Exception:
        pass
    finally:
        sys.stdout = old_stdout
        
    uptime = time.time() - START_TIME
    
    return StatsResponse(
        documents=num_docs,
        chunks=vector_count,
        vector_database=db_type,
        embedding_model="BAAI/bge-m3",
        llm="GPT-OSS 120B",
        uptime=uptime
    )

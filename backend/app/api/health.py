# pyrefly: ignore [missing-import]
from fastapi import APIRouter
from app.models.responses import HealthResponse
import os
import sys
import io

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def get_health():
    from app.rag.vector_store import VectorStore
    from app.services.document_service import DocumentService
    
    doc_service = DocumentService()
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
        
    return HealthResponse(
        status="ready",
        embedding_model="BAAI/bge-m3",
        vector_db=db_type,
        llm="GPT-OSS 120B",
        fallback_llm="Gemini 2.5 Flash",
        documents=num_docs,
        chunks=vector_count,
        storage_provider=os.environ.get("STORAGE_PROVIDER", "local")
    )

# pyrefly: ignore [missing-import]
from fastapi import APIRouter
from app.models.responses import HealthResponse
import os
import sys
import io

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def get_health():
    num_docs = 0
    try:
        from app.database.sqlite import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM documents")
        row = cursor.fetchone()
        num_docs = row["count"] if row else 0
        conn.close()
    except Exception:
        pass

    db_type = os.environ.get("VECTOR_DB", "qdrant").capitalize()
    vector_count = 0
    
    try:
        if db_type == "Qdrant":
            from qdrant_client import QdrantClient
            client = QdrantClient(url=os.environ.get("QDRANT_URL"), api_key=os.environ.get("QDRANT_API_KEY"), timeout=5.0)
            vector_count = client.count(collection_name="ratan_documents").count
        elif db_type == "Chroma":
            import chromadb
            client = chromadb.PersistentClient(path="./backend/app/storage/chroma")
            collection = client.get_collection("ratan_documents")
            vector_count = collection.count()
    except Exception:
        pass
        
    return HealthResponse(
        status="ready",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        vector_db=db_type,
        llm="GPT-OSS 120B",
        fallback_llm="Gemini 2.5 Flash",
        documents=num_docs,
        chunks=vector_count,
        storage_provider=os.environ.get("STORAGE_PROVIDER", "local")
    )

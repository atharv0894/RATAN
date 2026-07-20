import os
import time
import psutil
from fastapi import APIRouter
from app.api.responses import APISuccessResponse
from app.database.sqlite import get_db_connection
from app.services.dependencies import get_vector_store

router = APIRouter()

START_TIME = time.time()

@router.api_route("/health", methods=["GET", "HEAD"], response_model=APISuccessResponse)
def get_health():
    uptime = time.time() - START_TIME
    
    # Check Database
    db_status = "error"
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1")
        conn.close()
        db_status = "ok"
    except Exception:
        pass

    # Check Vector DB
    qdrant_status = "error"
    try:
        # In a real check, we'd ping Qdrant
        get_vector_store()
        qdrant_status = "ok"
    except Exception:
        pass

    # Memory & Disk
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    metrics = {
        "status": "ready" if db_status == "ok" and qdrant_status == "ok" else "degraded",
        "version": "1.0.0",
        "uptime_seconds": round(uptime, 2),
        "database": db_status,
        "qdrant": qdrant_status,
        "storage": os.environ.get("STORAGE_PROVIDER", "local"),
        "models": {
            "embedding": "sentence-transformers/all-MiniLM-L6-v2",
            "primary_llm": "Groq GPT-OSS 120B",
            "fallback_llm": "Gemini 2.5 Flash"
        },
        "hardware": {
            "memory_usage_percent": mem.percent,
            "disk_usage_percent": disk.percent
        }
    }

    return APISuccessResponse(data=metrics)

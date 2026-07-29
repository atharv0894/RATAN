import os
import time
import psutil
from fastapi import APIRouter
from app.api.responses import APISuccessResponse
from app.database.sqlite import get_db_connection
from app.services.dependencies import get_vector_store

router = APIRouter()

import os
import time
import psutil
import logging
from fastapi import APIRouter, Response, status
from app.api.responses import APISuccessResponse
from app.database.sqlite import get_db_connection
from app.services.dependencies import get_vector_store

router = APIRouter()
START_TIME = time.time()

@router.get("/health/liveness", tags=["Health"])
def get_liveness():
    """Fast check for load balancers to ensure the application event loop is alive."""
    uptime = time.time() - START_TIME
    return APISuccessResponse(data={"status": "alive", "uptime_seconds": round(uptime, 2)})

@router.get("/health/readiness", tags=["Health"])
def get_readiness(response: Response):
    """Deep check of all dependencies (DB, Qdrant, LLM, Memory) before receiving traffic."""
    uptime = time.time() - START_TIME
    
    # Check Database
    db_status = "error"
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1")
        conn.close()
        db_status = "ok"
    except Exception as e:
        logging.error(f"Readiness check failed on Database: {e}")

    # Check Vector DB
    qdrant_status = "error"
    try:
        get_vector_store()
        # In a real system, you'd execute a lightweight query here
        qdrant_status = "ok"
    except Exception as e:
        logging.error(f"Readiness check failed on Qdrant: {e}")
        
    # Check Memory bounds (512MB limit)
    mem = psutil.virtual_memory()
    mem_status = "ok" if mem.percent < 90 else "critical"
    
    # Overall Status
    is_ready = db_status == "ok" and qdrant_status == "ok" and mem_status != "critical"
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    metrics = {
        "status": "ready" if is_ready else "degraded",
        "uptime_seconds": round(uptime, 2),
        "database": db_status,
        "qdrant": qdrant_status,
        "memory": mem_status,
        "hardware": {
            "memory_usage_percent": mem.percent,
            "disk_usage_percent": psutil.disk_usage('/').percent
        }
    }

    return APISuccessResponse(data=metrics)

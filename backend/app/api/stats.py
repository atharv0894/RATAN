import time
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.dependencies import get_document_service, get_current_user, RequireRole
from app.api.responses import APISuccessResponse

router = APIRouter()
START_TIME = time.time()

class StatsResponse(BaseModel):
    documents: int
    chunks: int
    vector_database: str
    embedding_model: str
    llm: str
    uptime: float

@router.get("", response_model=APISuccessResponse[StatsResponse])
def get_stats(current_user: dict = Depends(RequireRole(["Admin", "Plant Manager"]))):
    doc_service = get_document_service()
    
    # Restrict stats to tenant if needed, but since it's admin, they can see tenant stats
    # For a real multi-tenant app, we'd query WHERE organization = current_user["org_id"]
    from app.database.sqlite import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT COUNT(*) as count FROM documents WHERE organization = ?"
    params = [current_user["org_id"]]
    
    if current_user.get("role") == "Plant Manager":
        query += " AND plant = ?"
        params.append(current_user["plant_id"])
        
    cursor.execute(query, tuple(params))
    num_docs = cursor.fetchone()["count"]
    
    # Ideally, Qdrant counts would be filtered by payload
    vector_query = "SELECT SUM(chunk_count) as count FROM document_versions v JOIN documents d ON v.document_id = d.id WHERE d.organization = ?"
    vector_params = [current_user["org_id"]]
    if current_user.get("role") == "Plant Manager":
        vector_query += " AND d.plant = ?"
        vector_params.append(current_user["plant_id"])
        
    cursor.execute(vector_query, tuple(vector_params))
    row = cursor.fetchone()
    vector_count = row["count"] if row and row["count"] else 0
    conn.close()

    uptime = time.time() - START_TIME
    
    stats_data = StatsResponse(
        documents=num_docs,
        chunks=vector_count,
        vector_database="Qdrant",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        llm="Groq GPT-OSS 120B",
        uptime=uptime
    )
    
    return APISuccessResponse(data=stats_data)

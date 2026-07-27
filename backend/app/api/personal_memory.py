import uuid
import time
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.api.responses import APISuccessResponse
from app.services.dependencies import RequireAccountType, get_db_connection

router = APIRouter()

class MemoryCreate(BaseModel):
    memory_type: str
    content: str

@router.get("", response_model=APISuccessResponse)
def list_personal_memories(current_user: dict = Depends(RequireAccountType(["PERSONAL"]))):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM personal_memories 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    """, (current_user["id"],))
    memories = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return APISuccessResponse(data={"memories": memories})

@router.post("", response_model=APISuccessResponse)
def create_personal_memory(payload: MemoryCreate, current_user: dict = Depends(RequireAccountType(["PERSONAL"]))):
    mem_id = str(uuid.uuid4())
    now = time.time()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO personal_memories (id, user_id, memory_type, content, created_at, updated_at) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (mem_id, current_user["id"], payload.memory_type, payload.content, now, now))
    conn.commit()
    conn.close()
    
    return APISuccessResponse(data={"id": mem_id, "message": "Memory added"})

@router.delete("/{memory_id}", response_model=APISuccessResponse)
def delete_personal_memory(memory_id: str, current_user: dict = Depends(RequireAccountType(["PERSONAL"]))):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM personal_memories WHERE id = ? AND user_id = ?", (memory_id, current_user["id"]))
    conn.commit()
    conn.close()
    return APISuccessResponse(data={"message": "Memory deleted"})

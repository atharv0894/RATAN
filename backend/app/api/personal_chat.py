import uuid
import time
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from app.api.responses import APISuccessResponse
from app.services.dependencies import RequireAccountType, get_db_connection

router = APIRouter()

class ChatSessionCreate(BaseModel):
    title: str = "New Chat"
    llm_model: str = "gpt-4o"

class ChatMessageCreate(BaseModel):
    session_id: str
    content: str
    parent_id: Optional[str] = None

@router.get("", response_model=APISuccessResponse)
def list_personal_chats(current_user: dict = Depends(RequireAccountType(["PERSONAL"]))):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, llm_model, created_at, updated_at, is_pinned 
        FROM personal_chats 
        WHERE user_id = ? AND status != 'DELETED'
        ORDER BY updated_at DESC
    """, (current_user["id"],))
    chats = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return APISuccessResponse(data={"chats": chats})

@router.post("", response_model=APISuccessResponse)
def create_personal_chat(payload: ChatSessionCreate, current_user: dict = Depends(RequireAccountType(["PERSONAL"]))):
    session_id = str(uuid.uuid4())
    now = time.time()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO personal_chats (id, user_id, title, llm_model, created_at, updated_at) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (session_id, current_user["id"], payload.title, payload.llm_model, now, now))
    conn.commit()
    conn.close()
    
    return APISuccessResponse(data={"id": session_id, "title": payload.title})

@router.get("/{session_id}", response_model=APISuccessResponse)
def get_personal_chat(session_id: str, current_user: dict = Depends(RequireAccountType(["PERSONAL"]))):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM personal_chats WHERE id = ? AND user_id = ?", (session_id, current_user["id"]))
    session = cursor.fetchone()
    if not session:
        conn.close()
        raise HTTPException(status_code=404, detail="Chat not found")
        
    cursor.execute("SELECT * FROM personal_messages WHERE session_id = ? ORDER BY created_at ASC", (session_id,))
    messages = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return APISuccessResponse(data={"session": dict(session), "messages": messages})

@router.delete("/{session_id}", response_model=APISuccessResponse)
def delete_personal_chat(session_id: str, current_user: dict = Depends(RequireAccountType(["PERSONAL"]))):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE personal_chats SET status = 'DELETED', updated_at = ? WHERE id = ? AND user_id = ?", (time.time(), session_id, current_user["id"]))
    conn.commit()
    conn.close()
    return APISuccessResponse(data={"message": "Chat deleted"})

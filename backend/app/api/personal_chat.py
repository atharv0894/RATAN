import uuid
import time
import json
import re
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.api.responses import APISuccessResponse
from app.services.dependencies import RequirePersonalUser, get_db_connection

router = APIRouter()

# ─── Request Models ───────────────────────────────────────────────────────────

class ChatSessionCreate(BaseModel):
    title: str = "New Chat"
    llm_model: str = "gpt-4o"

class ChatRename(BaseModel):
    title: str

class ChatMessagePayload(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    question: str
    document_id: Optional[str] = None
    chat_history: Optional[List[ChatMessagePayload]] = None
    session_id: Optional[str] = None

# ─── Routes (specific routes MUST come before /{session_id}) ──────────────────

@router.get("", response_model=APISuccessResponse)
def list_personal_chats(current_user: dict = Depends(RequirePersonalUser)):
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
def create_personal_chat(payload: ChatSessionCreate, current_user: dict = Depends(RequirePersonalUser)):
    """Create a new empty chat session and return its ID immediately."""
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


from fastapi import Request
from fastapi.responses import StreamingResponse

@router.post("/message")
async def send_personal_message(fastapi_req: Request, request: ChatRequest, current_user: dict = Depends(RequirePersonalUser)):
    """Stream a message from the personal RAG pipeline and save the result."""
    from app.services.dependencies import get_rag_service
    from app.exceptions import ValidationError
    import logging

    if not request.question or not request.question.strip():
        raise ValidationError("Please provide a valid question.")

    history = [msg.dict() for msg in request.chat_history] if request.chat_history else None
    
    session_id = request.session_id
    if not session_id:
        session_id = str(uuid.uuid4())

    base_where = {"namespace": f"personal/{current_user['id']}"}
    search_query = request.question
    
    match = re.search(r'^\[Attached Document:\s*(.*?)\]\s*(.*)$', request.question, re.DOTALL)
    if match:
        attached_filename = match.group(1).strip()
        search_query = match.group(2).strip()
        base_where["filename"] = attached_filename
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE personal_files SET session_id = ? WHERE filename = ? AND user_id = ? AND session_id IS NULL",
            (session_id, attached_filename, current_user["id"])
        )
        conn.commit()
        conn.close()

    async def event_generator():
        import asyncio
        rag_service = get_rag_service()
        trace_id = getattr(fastapi_req.state, "trace_id", "unknown")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        current_time = time.time()
        
        if not request.session_id:
            title = request.question[:50] + "..." if len(request.question) > 50 else request.question
            cursor.execute(
                "INSERT INTO personal_chats (id, user_id, title, llm_model, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, current_user["id"], title, "gpt-4o", current_time, current_time),
            )
        else:
            cursor.execute(
                "UPDATE personal_chats SET updated_at = ? WHERE id = ? AND user_id = ?",
                (current_time, session_id, current_user["id"]),
            )
            
        cursor.execute(
            "INSERT INTO personal_messages (id, session_id, role, content, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), session_id, "user", request.question, current_time, current_time),
        )
        conn.commit()
        conn.close()

        full_answer = ""
        citations = []
        
        try:
            async for chunk_str in rag_service.generate_answer_stream(search_query, history, base_where, trace_id):
                yield chunk_str
                
                if chunk_str.startswith("data: "):
                    try:
                        data_json = json.loads(chunk_str[6:].strip())
                        if data_json.get("type") == "chunk":
                            full_answer += data_json.get("text", "")
                        elif data_json.get("type") == "done":
                            full_answer = data_json.get("full_answer", full_answer)
                            citations = data_json.get("citations", [])
                    except json.JSONDecodeError:
                        pass
        
        except asyncio.CancelledError:
            logging.warning(f"[Trace: {trace_id}] Client disconnected during SSE stream. Persisting partial response.")
        except Exception as e:
            logging.error(f"[Trace: {trace_id}] Stream generator failed: {e}", exc_info=True)
            yield f'data: {json.dumps({"type": "error", "message": "An internal error interrupted the stream."})}\n\n'
            full_answer += "\n\n(Sorry, an internal error interrupted the stream.)"
            
        if full_answer:
            conn = get_db_connection()
            cursor = conn.cursor()
            ai_time = time.time()
            cursor.execute(
                "INSERT INTO personal_messages (id, session_id, role, content, citations, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), session_id, "assistant", full_answer, json.dumps(citations), ai_time, ai_time)
            )
            conn.commit()
            conn.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ─── Session-specific routes (must come AFTER fixed-path routes) ──────────────

@router.patch("/{session_id}/pin", response_model=APISuccessResponse)
def toggle_pin_personal_chat(session_id: str, current_user: dict = Depends(RequirePersonalUser)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, is_pinned FROM personal_chats WHERE id = ? AND user_id = ?",
        (session_id, current_user["id"]),
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Chat not found")

    new_pin = 0 if row["is_pinned"] else 1
    cursor.execute(
        "UPDATE personal_chats SET is_pinned = ?, updated_at = ? WHERE id = ?",
        (new_pin, time.time(), session_id),
    )
    conn.commit()
    conn.close()
    return APISuccessResponse(data={"session_id": session_id, "is_pinned": bool(new_pin)})


@router.patch("/{session_id}/rename", response_model=APISuccessResponse)
def rename_personal_chat(session_id: str, payload: ChatRename, current_user: dict = Depends(RequirePersonalUser)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM personal_chats WHERE id = ? AND user_id = ?",
        (session_id, current_user["id"]),
    )
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Chat not found")

    cursor.execute(
        "UPDATE personal_chats SET title = ?, updated_at = ? WHERE id = ?",
        (payload.title.strip()[:100], time.time(), session_id),
    )
    conn.commit()
    conn.close()
    return APISuccessResponse(data={"session_id": session_id, "title": payload.title})


@router.delete("/{session_id}", response_model=APISuccessResponse)
def delete_personal_chat(session_id: str, current_user: dict = Depends(RequirePersonalUser)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE personal_chats SET status = 'DELETED', updated_at = ? WHERE id = ? AND user_id = ?",
        (time.time(), session_id, current_user["id"]),
    )
    conn.commit()
    conn.close()
    return APISuccessResponse(data={"message": "Chat deleted"})


@router.get("/{session_id}", response_model=APISuccessResponse)
def get_personal_chat(session_id: str, current_user: dict = Depends(RequirePersonalUser)):
    """Return session metadata + all messages in chronological order."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM personal_chats WHERE id = ? AND user_id = ? AND status != 'DELETED'",
        (session_id, current_user["id"]),
    )
    session = cursor.fetchone()
    if not session:
        conn.close()
        raise HTTPException(status_code=404, detail="Chat not found")

    cursor.execute(
        "SELECT * FROM personal_messages WHERE session_id = ? ORDER BY created_at ASC",
        (session_id,),
    )
    messages = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return APISuccessResponse(data={"session": dict(session), "messages": messages})

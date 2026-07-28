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


@router.post("/message", response_model=APISuccessResponse)
def send_personal_message(request: ChatRequest, current_user: dict = Depends(RequirePersonalUser)):
    """Send a message to the personal RAG pipeline and save the result."""
    from app.services.dependencies import get_rag_service
    from app.exceptions import ValidationError

    if not request.question or not request.question.strip():
        raise ValidationError("Please provide a valid question.")

    history = [msg.dict() for msg in request.chat_history] if request.chat_history else None
    rag_service = get_rag_service()

    # Isolate retrieval to the user's personal namespace only
    base_where = {"namespace": f"personal/{current_user['id']}"}

    # Parse [Attached Document: filename] prefix from frontend
    search_query = request.question
    match = re.search(r'^\[Attached Document:\s*(.*?)\]\s*(.*)$', request.question, re.DOTALL)
    if match:
        attached_filename = match.group(1).strip()
        search_query = match.group(2).strip()
        base_where["filename"] = attached_filename

    result = rag_service.generate_answer(
        query=search_query,
        chat_history=history,
        base_where=base_where,
    )

    conn = get_db_connection()
    cursor = conn.cursor()
    session_id = request.session_id
    current_time = time.time()

    if not session_id:
        # Auto-create session if the frontend didn't pre-create one
        session_id = str(uuid.uuid4())
        title = request.question[:50] + "..." if len(request.question) > 50 else request.question
        cursor.execute(
            "INSERT INTO personal_chats (id, user_id, title, llm_model, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, current_user["id"], title, result.get("provider", "gpt-4o"), current_time, current_time),
        )
    else:
        # Update the timestamp so the chat floats to the top of the sidebar
        cursor.execute(
            "UPDATE personal_chats SET updated_at = ? WHERE id = ? AND user_id = ?",
            (current_time, session_id, current_user["id"]),
        )

    # Persist user message
    cursor.execute(
        "INSERT INTO personal_messages (id, session_id, role, content, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), session_id, "user", request.question, current_time, current_time),
    )

    # Persist assistant message with citations
    cursor.execute(
        "INSERT INTO personal_messages (id, session_id, role, content, citations, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            str(uuid.uuid4()), session_id, "assistant", result["answer"],
            json.dumps(result.get("citations", [])),
            current_time + 0.001,  # tiny offset ensures correct chronological order
            current_time + 0.001,
        ),
    )

    conn.commit()
    conn.close()

    result["session_id"] = session_id
    return APISuccessResponse(data=result)


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

from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.dependencies import get_rag_service, get_current_user, get_tenant_context
from app.api.responses import APISuccessResponse
from app.exceptions import ValidationError

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    question: str
    document_id: Optional[str] = None
    chat_history: Optional[List[ChatMessage]] = None
    session_id: Optional[str] = None

class Citation(BaseModel):
    document_name: str
    version: int
    page: str
    section: str
    chunk_id: str

class RAGResponse(BaseModel):
    answer: str
    citations: List[dict]
    confidence_score: float
    follow_up_questions: List[str]
    intent: str
    provider: str
    session_id: Optional[str] = None

@router.get("/sessions", response_model=APISuccessResponse)
def get_sessions(current_user: dict = Depends(get_current_user)):
    from app.database.sqlite import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, created_at FROM chat_sessions WHERE user_id = ? ORDER BY updated_at DESC", 
        (current_user["id"],)
    )
    rows = cursor.fetchall()
    conn.close()
    return APISuccessResponse(data=[dict(r) for r in rows])

@router.get("/sessions/{session_id}", response_model=APISuccessResponse)
def get_session_messages(session_id: str, current_user: dict = Depends(get_current_user)):
    from app.database.sqlite import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    # Verify ownership
    cursor.execute("SELECT id FROM chat_sessions WHERE id = ? AND user_id = ?", (session_id, current_user["id"]))
    if not cursor.fetchone():
        conn.close()
        from app.exceptions import AuthorizationError
        raise AuthorizationError("Session not found or access denied")
        
    cursor.execute(
        "SELECT id, role, content, created_at FROM chat_messages WHERE session_id = ? ORDER BY created_at ASC", 
        (session_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return APISuccessResponse(data=[dict(r) for r in rows])

@router.post("", response_model=APISuccessResponse)
def create_chat_session(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """Create a new empty chat session and return its ID immediately."""
    from app.database.sqlite import get_db_connection
    import uuid
    import time
    session_id = str(uuid.uuid4())
    now = time.time()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_sessions (id, user_id, title, llm_model, created_at, updated_at) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (session_id, current_user["id"], "New Chat", "gpt-4o", now, now))
    conn.commit()
    conn.close()

    return APISuccessResponse(data={"id": session_id, "title": "New Chat"})

from fastapi import Request
from fastapi.responses import StreamingResponse

@router.post("/message")
async def chat_message_stream(
    fastapi_req: Request,
    request: ChatRequest, 
    current_user: dict = Depends(get_current_user),
    tenant: dict = Depends(get_tenant_context)
):
    """Stream a message from the enterprise RAG pipeline and save the result."""
    if not request.question or not request.question.strip():
        raise ValidationError("Please provide a valid question.")
        
    base_where = {"organization_id": tenant["organization"]}
    
    if request.document_id:
        from app.database.sqlite import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT filename FROM documents WHERE id = ? AND organization = ?", 
            (request.document_id, tenant["organization"])
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            base_where["filename"] = row["filename"]
        else:
            raise ValidationError("Specified document not found or access denied.")

    history = [msg.dict() for msg in request.chat_history] if request.chat_history else None

    # Parse Attached Document syntax from frontend
    import re
    search_query = request.question
    match = re.search(r'^\[Attached Document:\s*(.*?)\]\s*(.*)$', request.question, re.DOTALL)
    if match:
        attached_filename = match.group(1).strip()
        search_query = match.group(2).strip()
        base_where["filename"] = attached_filename
        
    import uuid
    session_id = request.session_id
    if not session_id:
        session_id = str(uuid.uuid4())

    async def event_generator():
        import asyncio
        import json
        import time
        from app.services.dependencies import get_rag_service
        from app.database.sqlite import get_db_connection
        
        rag_service = get_rag_service()
        trace_id = getattr(fastapi_req.state, "trace_id", "unknown")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        current_time = time.time()
        
        if not request.session_id:
            title = request.question[:50] + "..." if len(request.question) > 50 else request.question
            cursor.execute(
                "INSERT INTO chat_sessions (id, user_id, title, llm_model, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, current_user["id"], title, "gpt-4o", current_time, current_time),
            )
        else:
            cursor.execute(
                "UPDATE chat_sessions SET updated_at = ? WHERE id = ?",
                (current_time, session_id),
            )
            
        cursor.execute(
            "INSERT INTO chat_messages (id, session_id, role, content, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
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
            import logging
            logging.warning(f"[Trace: {trace_id}] Client disconnected during SSE stream. Persisting partial response.")
        except Exception as e:
            import logging
            logging.error(f"[Trace: {trace_id}] Stream generator failed: {e}", exc_info=True)
            yield f'data: {json.dumps({"type": "error", "message": "An internal error interrupted the stream."})}\n\n'
            full_answer += "\n\n(Sorry, an internal error interrupted the stream.)"
            
        if full_answer:
            conn = get_db_connection()
            cursor = conn.cursor()
            ai_time = time.time()
            cursor.execute(
                "INSERT INTO chat_messages (id, session_id, role, content, citations, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), session_id, "assistant", full_answer, json.dumps(citations), ai_time, ai_time)
            )
            conn.commit()
            conn.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/search", response_model=APISuccessResponse[RAGResponse])
def chat_search_sync(
    request: ChatRequest, 
    tenant: dict = Depends(get_tenant_context)
):
    """Synchronous search endpoint for the semantic search UI."""
    try:
        if not request.question or not request.question.strip():
            raise ValidationError("Please provide a valid question.")
            
        base_where = {"organization_id": tenant["organization"]}
        
        if request.document_id:
            from app.database.sqlite import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT filename FROM documents WHERE id = ? AND organization = ?", 
                (request.document_id, tenant["organization"])
            )
            row = cursor.fetchone()
            conn.close()
            
            if row:
                base_where["filename"] = row["filename"]
            else:
                raise ValidationError("Specified document not found or access denied.")

        history = [msg.dict() for msg in request.chat_history] if request.chat_history else None

        from app.services.dependencies import get_rag_service
        rag_service = get_rag_service()
        
        import re
        search_query = request.question
        match = re.search(r'^\[Attached Document:\s*(.*?)\]\s*(.*)$', request.question, re.DOTALL)
        if match:
            attached_filename = match.group(1).strip()
            search_query = match.group(2).strip()
            base_where["filename"] = attached_filename
        
        result = rag_service.generate_answer(
            query=search_query, 
            chat_history=history,
            base_where=base_where
        )
        
        return APISuccessResponse(data=RAGResponse(**result))
    except Exception as e:
        import traceback
        traceback.print_exc()
        from app.exceptions import AppException
        raise AppException(500, "INTERNAL_ERROR", str(e))

class RenameSessionRequest(BaseModel):
    title: str

@router.patch("/sessions/{session_id}/rename", response_model=APISuccessResponse)
def rename_session(session_id: str, request: RenameSessionRequest, current_user: dict = Depends(get_current_user)):
    from app.database.sqlite import get_db_connection
    import time
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM chat_sessions WHERE id = ? AND user_id = ?", (session_id, current_user["id"]))
    if not cursor.fetchone():
        conn.close()
        from app.exceptions import AuthorizationError
        raise AuthorizationError("Session not found or access denied")
    cursor.execute("UPDATE chat_sessions SET title = ?, updated_at = ? WHERE id = ?", (request.title.strip(), time.time(), session_id))
    conn.commit()
    conn.close()
    return APISuccessResponse(data={"session_id": session_id, "title": request.title})

@router.patch("/sessions/{session_id}/pin", response_model=APISuccessResponse)
def toggle_pin_session(session_id: str, current_user: dict = Depends(get_current_user)):
    from app.database.sqlite import get_db_connection
    import time
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, is_pinned FROM chat_sessions WHERE id = ? AND user_id = ?", (session_id, current_user["id"]))
    row = cursor.fetchone()
    if not row:
        conn.close()
        from app.exceptions import AuthorizationError
        raise AuthorizationError("Session not found or access denied")
    new_pin = 0 if row["is_pinned"] else 1
    cursor.execute("UPDATE chat_sessions SET is_pinned = ?, updated_at = ? WHERE id = ?", (new_pin, time.time(), session_id))
    conn.commit()
    conn.close()
    return APISuccessResponse(data={"session_id": session_id, "is_pinned": bool(new_pin)})

@router.delete("/sessions/{session_id}", response_model=APISuccessResponse)
def delete_session(session_id: str, current_user: dict = Depends(get_current_user)):
    from app.database.sqlite import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM chat_sessions WHERE id = ? AND user_id = ?", (session_id, current_user["id"]))
    if not cursor.fetchone():
        conn.close()
        from app.exceptions import AuthorizationError
        raise AuthorizationError("Session not found or access denied")
    cursor.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()
    return APISuccessResponse(data={"deleted": session_id})

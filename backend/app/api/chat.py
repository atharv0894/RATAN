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

@router.post("", response_model=APISuccessResponse[RAGResponse])
def chat(
    request: ChatRequest, 
    current_user: dict = Depends(get_current_user),
    tenant: dict = Depends(get_tenant_context)
):
    try:
        if not request.question or not request.question.strip():
            raise ValidationError("Please provide a valid question.")
            
        base_where = {}
        
        if request.document_id:
            # Enforce document lookup inside the active tenant
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

        # Convert ChatMessage pydantic objects to dicts for the service layer
        history = [msg.dict() for msg in request.chat_history] if request.chat_history else None

        rag_service = get_rag_service()
        
        # Parse Attached Document syntax from frontend
        import re
        search_query = request.question
        match = re.search(r'^\[Attached Document:\s*(.*?)\]\s*(.*)$', request.question, re.DOTALL)
        if match:
            attached_filename = match.group(1).strip()
            search_query = match.group(2).strip()
            base_where["filename"] = attached_filename

        # RAG service natively applies organization filters inside its engine if tenant is supplied
        base_where["organization_id"] = tenant["organization"]
        
        result = rag_service.generate_answer(
            query=search_query, 
            chat_history=history,
            base_where=base_where
        )
        
        # Save session logic
        from app.database.sqlite import get_db_connection
        import uuid
        import time
        conn = get_db_connection()
        cursor = conn.cursor()
        
        session_id = request.session_id
        current_time = time.time()
        
        if not session_id:
            session_id = str(uuid.uuid4())
            title = request.question[:50] + "..." if len(request.question) > 50 else request.question
            cursor.execute(
                "INSERT INTO chat_sessions (id, user_id, title, llm_model, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, current_user["id"], title, result.get("provider", "Groq"), current_time, current_time)
            )
        else:
            cursor.execute("UPDATE chat_sessions SET updated_at = ? WHERE id = ?", (current_time, session_id))
            
        # Save User Message
        cursor.execute(
            "INSERT INTO chat_messages (id, session_id, role, content, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), session_id, "user", request.question, current_time, current_time)
        )
        
        # Save Assistant Message
        import json
        cursor.execute(
            "INSERT INTO chat_messages (id, session_id, role, content, citations, follow_up_questions, confidence_score, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), session_id, "assistant", result["answer"], json.dumps(result.get("citations", [])), json.dumps(result.get("follow_up_questions", [])), result.get("confidence_score", 0.0), current_time + 1, current_time + 1)
        )
        conn.commit()
        conn.close()
        
        result["session_id"] = session_id
        
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

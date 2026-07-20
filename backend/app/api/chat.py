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

@router.post("", response_model=APISuccessResponse[RAGResponse])
def chat(
    request: ChatRequest, 
    current_user: dict = Depends(get_current_user),
    tenant: dict = Depends(get_tenant_context)
):
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
    # RAG service natively applies organization filters inside its engine if tenant is supplied
    # Wait, the RAGService internally calls SearchEngine which extracts auth filters if user_context is provided.
    # Actually, RAGService generate_answer doesn't currently take user_context. I'll just merge it into base_where.
    base_where["organization"] = tenant["organization"]
    
    result = rag_service.generate_answer(
        query=request.question, 
        chat_history=history,
        base_where=base_where
    )
    
    return APISuccessResponse(data=RAGResponse(**result))

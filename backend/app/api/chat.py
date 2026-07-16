# pyrefly: ignore [missing-import]
from fastapi import APIRouter
from app.models.requests import ChatRequest
from app.models.responses import ChatResponse
from app.services.dependencies import get_rag_service

router = APIRouter()

@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):
    rag_service = get_rag_service()
    result = rag_service.generate_answer(request.question)
    return ChatResponse(
        answer=result.get("answer", ""),
        citations=result.get("citations", [])
    )

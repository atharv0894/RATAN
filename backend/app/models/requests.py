# pyrefly: ignore [missing-import]
from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    question: str
    document_id: Optional[str] = None
    filename: Optional[str] = None

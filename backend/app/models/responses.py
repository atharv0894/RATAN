# pyrefly: ignore [missing-import]
from pydantic import BaseModel
from typing import List

class HealthResponse(BaseModel):
    status: str
    embedding_model: str
    vector_db: str
    llm: str
    fallback_llm: str
    documents: int
    chunks: int
    storage_provider: str

class DocumentResponse(BaseModel):
    id: str
    filename: str
    status: str
    chunks: int
    
class DocumentDetailResponse(DocumentResponse):
    upload_time: float
    embedding_model: str
    vector_db: str
    processing_time: float

class ChatResponse(BaseModel):
    answer: str
    citations: List[dict]
    entities: List[dict] = []

class StatsResponse(BaseModel):
    documents: int
    chunks: int
    vector_database: str
    embedding_model: str
    llm: str
    uptime: float

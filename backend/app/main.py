# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from pydantic import BaseModel
# pyrefly: ignore [missing-import]
from typing import List, Optional
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import VectorStore
from app.rag.retrieval_service import RetrievalService
from app.rag.rag_service import RAGService
from app.rag.indexer import Indexer

# Load environment variables (e.g. GROQ_API_KEY from .env)
load_dotenv()

app = FastAPI(
    title="RATAN API",
    description="Retrieval-Augmented Technology for Asset Networks",
    version="1.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Shared Dependencies
embedding_service = EmbeddingService()
vector_store = VectorStore()
retrieval_service = RetrievalService(embedding_service, vector_store)

# Initialize RAG Services with injected dependencies
rag_service = RAGService(retrieval_service)
indexer = Indexer(embedding_service, vector_store)

# Pydantic Models for Requests
class QueryRequest(BaseModel):
    query: str

class DocumentChunk(BaseModel):
    text: str
    metadata: Optional[dict] = None

class IndexRequest(BaseModel):
    chunks: List[DocumentChunk]

@app.get("/")
def read_root():
    return {"message": "Welcome to RATAN API"}

@app.post("/api/rag/query")
def query_rag(request: QueryRequest):
    """
    Query the RAG system to get a grounded answer based on industrial knowledge.
    """
    response = rag_service.generate_answer(request.query)
    return response

@app.post("/api/rag/index")
def index_documents(request: IndexRequest):
    """
    Index new document chunks into the vector store.
    """
    texts = [chunk.text for chunk in request.chunks]
    metadatas = [chunk.metadata or {} for chunk in request.chunks]
    
    chunk_ids = indexer.index_chunks(texts, metadatas=metadatas)
    
    return {
        "message": "Successfully indexed chunks",
        "indexed_count": len(chunk_ids),
        "chunk_ids": chunk_ids
    }

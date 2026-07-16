from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import VectorStore
from app.rag.retrieval_service import RetrievalService
from app.rag.rag_service import RAGService
from app.services.document_service import DocumentService

# Singletons
embedding_service = None
vector_store = None
retrieval_service = None
rag_service = None
document_service = None

def get_embedding_service():
    global embedding_service
    if embedding_service is None:
        embedding_service = EmbeddingService()
    return embedding_service

def get_vector_store():
    global vector_store
    if vector_store is None:
        vector_store = VectorStore()
    return vector_store

def get_retrieval_service():
    global retrieval_service
    if retrieval_service is None:
        retrieval_service = RetrievalService(get_embedding_service(), get_vector_store())
    return retrieval_service

def get_rag_service():
    global rag_service
    if rag_service is None:
        rag_service = RAGService(get_retrieval_service())
    return rag_service

def get_document_service():
    global document_service
    if document_service is None:
        # Pass the singleton dependencies so DocumentService doesn't create them again
        document_service = DocumentService(get_embedding_service(), get_vector_store())
    return document_service

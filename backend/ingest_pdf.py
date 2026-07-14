import os
# pyrefly: ignore [missing-import]
import pdfplumber
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

# Load environment variables (e.g. GROQ_API_KEY from .env)
load_dotenv()

from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import VectorStore
from app.rag.indexer import Indexer
from app.rag.retrieval_service import RetrievalService
from app.rag.rag_service import RAGService

def ingest_pdf(pdf_path: str):
    print(f"Reading {pdf_path}...")
    
    # Initialize shared dependencies
    embedding_service = EmbeddingService()
    vector_store = VectorStore()
    indexer = Indexer(embedding_service, vector_store)
    
    chunks = []
    metadatas = []
    
    # Read the PDF using pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if not text:
                continue
                
            # Basic chunking: split by paragraphs (double newlines)
            # You can make this smarter later (e.g., using RecursiveCharacterTextSplitter)
            paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 50]
            
            for p in paragraphs:
                chunks.append(p)
                metadatas.append({
                    "source": os.path.basename(pdf_path),
                    "page_no": page_num
                })
    
    print(f"Extracted {len(chunks)} chunks from the PDF.")
    
    if chunks:
        # Index the chunks
        chunk_ids = indexer.index_chunks(chunks, metadatas=metadatas)
        print(f"Successfully indexed {len(chunk_ids)} chunks into the RAG Vector Store.")
        
    return embedding_service, vector_store

def test_rag_query(embedding_service, vector_store, query: str):
    print(f"\n--- Testing Query ---")
    print(f"Question: {query}")
    
    retrieval_service = RetrievalService(embedding_service, vector_store)
    rag_service = RAGService(retrieval_service)
    
    response = rag_service.generate_answer(query)
    print(f"Answer: {response['answer']}")
    print("Citations:")
    for citation in response['citations']:
         meta = citation.get('metadata', {})
         print(f" - Source: {meta.get('source')} (Page {meta.get('page_no')}) | Score: {citation.get('distance')}")

if __name__ == "__main__":
    pdf_path = "../PRD_Industrial_Knowledge_Intelligence.pdf"
    
    # Ingest the PDF
    embedding_service, vector_store = ingest_pdf(pdf_path)
    
    # Test a query
    test_rag_query(embedding_service, vector_store, "What is the primary objective of RATAN?")

import os
import sys
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import VectorStore
from app.rag.retrieval_service import RetrievalService
from app.rag.rag_service import RAGService

def run_test():
    embedding_service = EmbeddingService()
    vector_store = VectorStore()
    retrieval_service = RetrievalService(embedding_service, vector_store)
    rag_service = RAGService(retrieval_service)

    q1 = "An operator begins a manufacturing procedure after confirming that the correct SOP is available, personnel are authorized, equipment is released, and the work environment is safe. During execution, a required quality check produces a result outside the measurable acceptance criteria, but no immediate safety hazard is identified. According to the SOP, what must happen next, under what conditions may work resume, which documented responsibilities are relevant, and what does the SOP not specify about the final disposition of the affected product or output?"
    
    print("=== Manual Validation ===")
    res1 = rag_service.generate_answer(q1)
    
    print(f"Provider: {res1.get('provider', 'Unknown')}")
    print("\nAnswer:")
    print(res1['answer'])
    print("\nCitations:")
    for c in res1['citations']:
        meta = c['metadata']
        print(f"[{meta.get('source')} Page {meta.get('page_no')} - {meta.get('section')}] (Chunk ID: {c.get('chunk_id')})")

if __name__ == "__main__":
    run_test()

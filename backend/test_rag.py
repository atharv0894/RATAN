import os
import sys
# Ensure app modules can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from dotenv import load_dotenv
load_dotenv()

import pdfplumber
from app.rag.embedding_service import EmbeddingService
from app.rag.qdrant_store import QdrantStore
from app.rag.rag_service import RAGService
from app.services.document_service import Chunker

def test_pdf_rag():
    os.environ["QDRANT_URL"] = ":memory:"
    pdf_path = "../test_data/marathi.pdf"
    question = "या पुस्तकाची आवृत्ती कोणती आहे?"  # What is the version of this book?
    
    print(f"1. Extracting text from {pdf_path} (First 3 pages)...")
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[:3]:
            text += page.extract_text() or "" + "\n"
            
    print("2. Chunking text...")
    chunker = Chunker()
    class DummyPage:
        def __init__(self, text):
            self.text = text
            self.tables = []
    
    chunks = chunker.chunk_page_with_metadata(DummyPage(text), {"organization_id": "test-org", "source": "survey.pdf", "page_no": 1})
    print(f"   Created {len(chunks)} chunks.")
    
    print("3. Connecting to Qdrant and resetting collection to 384 dimensions...")
    qdrant = QdrantStore(collection_name="ratan_documents")
    # This will trigger the dimension check and recreate it for 384 if it was 1024
    qdrant._ensure_collection()
    
    print("4. Generating FastEmbed Embeddings locally...")
    embed_service = EmbeddingService()
    texts = [c['text'] for c in chunks]
    embeddings = embed_service.generate_embeddings(texts)
    
    ids = [f"test-chunk-{i}" for i in range(len(chunks))]
    metadatas = [{"source": "survey.pdf", "organization_id": "test-org", "is_latest": 1} for c in chunks]
    
    print("5. Upserting into Qdrant...")
    qdrant.upsert(ids, embeddings, texts, metadatas)
    
    print(f"\n6. Asking Question: '{question}'")
    rag = RAGService()
    rag.retrieval_service.vector_store = qdrant
    rag.search_engine.vector_store = qdrant
    query_emb = embed_service.generate_embedding(question)
    raw_res = qdrant.query([query_emb], n_results=5, include=[], where={"organization_id": "test-org", "is_latest": 1})
    print(f"RAW QDRANT DOCS FOUND: {len(raw_res['documents'][0])}")
    print(f"Qdrant ID: {id(qdrant)}")
    print(f"RetrievalService Qdrant ID: {id(rag.retrieval_service.vector_store)}")
    
    ret_chunks = rag.retrieval_service.retrieve(question, where={"organization_id": "test-org", "is_latest": 1})
    print(f"RetrievalService chunks found: {len(ret_chunks)}")
    
    result = rag.generate_answer(question, base_where={"organization_id": "test-org"})
    
    print("\n================ ANSWER ================\n")
    print(result["answer"])
    print("\n================ CITATIONS ================\n")
    for c in result["citations"]:
        print(f"- {c['document_name']} (Confidence: {c['similarity_score']:.2f})")

if __name__ == "__main__":
    test_pdf_rag()

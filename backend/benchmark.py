import os
import sys
import time
import logging

# Ensure app modules can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from dotenv import load_dotenv
load_dotenv()

import pdfplumber
from app.rag.embedding_service import EmbeddingService
from app.rag.qdrant_store import QdrantStore
from app.rag.rag_service import RAGService
from app.services.document_service import Chunker

def run_benchmarks():
    print("================ RATAN RAG BENCHMARK ================")
    
    # 1. Initialize services (Connects to Qdrant Cloud if .env is set)
    print("\n[1/5] Initializing Services & Qdrant Cloud...")
    start_time = time.time()
    qdrant = QdrantStore(collection_name="ratan_documents")
    qdrant.reset_collection() # Force reset to apply new strict indexes
    embed_service = EmbeddingService()
    rag = RAGService()
    rag.retrieval_service.vector_store = qdrant
    rag.search_engine.vector_store = qdrant
    print(f"✅ Services Initialized in {time.time() - start_time:.2f}s")

    # 2. Extract Document Context
    print("\n[2/5] Parsing PDF Document (First 10 Pages)...")
    pdf_path = "../test_data/Retrieval-Augmented Generation for Large Language Models: A Survey.pdf"
    text = ""
    start_time = time.time()
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[:10]:
            text += page.extract_text() + "\n"
    print(f"✅ Extracted {len(text)} characters in {time.time() - start_time:.2f}s")

    # 3. Chunking & Embedding
    print("\n[3/5] Chunking and Generating Embeddings...")
    chunker = Chunker()
    class DummyPage:
        def __init__(self, text):
            self.text = text
            self.tables = []
    
    start_time = time.time()
    chunks = chunker.chunk_page_with_metadata(DummyPage(text), {"organization_id": "benchmark-org", "source": "survey.pdf", "page_no": 1})
    print(f"✅ Created {len(chunks)} chunks in {time.time() - start_time:.2f}s")
    
    start_time = time.time()
    texts = [c['text'] for c in chunks]
    embeddings = embed_service.generate_embeddings(texts)
    print(f"✅ Generated {len(embeddings)} embeddings locally in {time.time() - start_time:.2f}s")
    
    # 4. Upsert to Qdrant Cloud
    print("\n[4/5] Upserting to Qdrant Cloud...")
    start_time = time.time()
    ids = [f"bench-chunk-{i}" for i in range(len(chunks))]
    metadatas = [{"source": "survey.pdf", "organization_id": "benchmark-org", "is_latest": 1} for c in chunks]
    qdrant.upsert(ids, embeddings, texts, metadatas)
    print(f"✅ Upserted to Qdrant Cloud in {time.time() - start_time:.2f}s")

    # 5. Question Answering Benchmarks
    print("\n[5/5] Running Complex Queries...")
    
    questions = [
        "What are the core components of the RAG framework?",
        "How does RAG mitigate hallucinations in Large Language Models compared to fine-tuning?",
        "What are the key differences between Naive RAG and Advanced RAG paradigms?"
    ]
    
    for i, q in enumerate(questions):
        print(f"\n--- Query {i+1}: '{q}' ---")
        
        # Measure Retrieval
        ret_start = time.time()
        ret_chunks = rag.retrieval_service.retrieve(q, where={"organization_id": "benchmark-org", "is_latest": 1})
        ret_time = time.time() - ret_start
        print(f"   > Retrieval Time: {ret_time:.3f}s (Found {len(ret_chunks)} chunks)")
        
        # Measure Generation
        gen_start = time.time()
        result = rag.generate_answer(q, base_where={"organization_id": "benchmark-org"})
        gen_time = time.time() - gen_start
        print(f"   > Generation Time (LLM): {gen_time:.3f}s")
        
        # Print Output
        print("\n   [Answer]")
        import textwrap
        print(textwrap.indent(textwrap.fill(result["answer"], width=80), "     "))
        print("\n   [Citations & Confidence]")
        for c in result["citations"]:
            print(f"     - {c['document_name']} (Confidence: {c['similarity_score']:.2f})")

if __name__ == "__main__":
    run_benchmarks()

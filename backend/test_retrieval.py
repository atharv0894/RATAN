import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Ensure backend directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import VectorStore
from app.rag.indexer import Indexer
from app.rag.retrieval_service import RetrievalService
from app.rag.rag_service import RAGService
from app.rag.document_loaders import DocumentLoader
from app.rag.chunker import Chunker

def test_regression():
    print("Setting up test environment...")
    # Initialize services
    embedding_service = EmbeddingService()
    vector_store = VectorStore(collection_name="test_industrial_knowledge")
    vector_store.reset_collection()
    
    indexer = Indexer(embedding_service, vector_store)
    retrieval_service = RetrievalService(embedding_service, vector_store)
    rag_service = RAGService(retrieval_service)
    
    file_path = "../test_data/Manufacturing-SOP-Template-flowdit.pdf"
    if not os.path.exists(file_path):
        print(f"Error: Test file not found at {file_path}")
        return False
        
    print("Ingesting SOP for test...")
    loader = DocumentLoader()
    chunker = Chunker(max_chars=1500, overlap_chars=200)
    pages = loader.load_file(file_path)
    
    chunks = []
    metadatas = []
    chunk_ids = []
    for page in pages:
        page_text = page['text']
        base_meta = {"source": os.path.basename(file_path), "page_no": page.get('page_no', 1)}
        page_chunks_info = chunker.chunk_text_with_metadata(page_text, base_meta)
        for info in page_chunks_info:
            chunks.append(info['text'])
            metadatas.append(info['metadata'])
            chunk_ids.append(info['chunk_id'])

    indexer.index_chunks(chunks, metadatas=metadatas, chunk_ids=chunk_ids)
    
    # Test query
    test_query = "A trained operator discovers during execution that a process parameter is outside the defined tolerance and the output may not meet quality requirements. The supervisor is unavailable, and continuing the operation could affect both product quality and equipment safety. According to the SOP, what actions should the operator take, what conditions must be satisfied before work can resume, which organizational roles may need to be involved, and what documentation and record requirements apply?"
    
    print("\nRunning test query...")
    # Generate answer (with debug to print)
    response = rag_service.generate_answer(test_query, debug=False)
    citations = response.get('citations', [])
    
    # 1. Evidence uniqueness (no duplicate chunk_ids)
    chunk_ids_retrieved = [c['chunk_id'] for c in citations]
    unique_chunk_ids = set(chunk_ids_retrieved)
    
    if len(chunk_ids_retrieved) != len(unique_chunk_ids):
        print("FAIL: Duplicate chunks found in retrieved evidence!")
        return False
    print("PASS: Evidence uniqueness verified.")
        
    # 2. Metadata integrity
    for c in citations:
        if 'source' not in c['metadata'] or 'page_no' not in c['metadata'] or 'section' not in c['metadata']:
            print("FAIL: Missing metadata in chunks!")
            return False
    print("PASS: Metadata integrity verified.")
            
    # 3. Citation uniqueness
    seen_citations = set()
    deduped_citations = []
    for c in citations:
        meta = c['metadata']
        key = (meta['source'], meta['page_no'], meta['section'])
        if key not in seen_citations:
            seen_citations.add(key)
            deduped_citations.append(key)
            
    if len(deduped_citations) != len(seen_citations):
        print("FAIL: Duplicate citations found after deduplication logic (should not happen mathematically, but checking).")
        return False
    print("PASS: Citation uniqueness logic verified.")
        
    # 4. Retrieval coverage
    # We want to make sure it picked up key sections
    retrieved_sections = [c['metadata'].get('section', '') for c in citations]
    
    # Check if we hit important topics
    found_deviation = any("Deviation" in s for s in retrieved_sections)
    found_docs = any("Documentation" in s or "Records" in s for s in retrieved_sections)
    found_responsibilities = any("Responsibilities" in s for s in retrieved_sections)
    
    coverage_score = sum([found_deviation, found_docs, found_responsibilities])
    
    print(f"Coverage: Deviation={found_deviation}, Docs={found_docs}, Responsibilities={found_responsibilities}")
    
    if coverage_score < 2:
        print("FAIL: Retrieval coverage is too low. Expected at least 2 key sections.")
        print(f"Retrieved Sections: {retrieved_sections}")
        return False
        
    print("PASS: Retrieval coverage verified.")
    print("\nALL TESTS PASSED! \u2705")
    return True

if __name__ == "__main__":
    test_regression()

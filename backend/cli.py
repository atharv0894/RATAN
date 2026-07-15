import argparse
import sys
import os
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import VectorStore
from app.rag.indexer import Indexer
from app.rag.retrieval_service import RetrievalService
from app.rag.rag_service import RAGService
from app.rag.document_loaders import DocumentLoader
from app.rag.chunker import Chunker

def get_services():
    embedding_service = EmbeddingService()
    vector_store = VectorStore()
    indexer = Indexer(embedding_service, vector_store)
    retrieval_service = RetrievalService(embedding_service, vector_store)
    rag_service = RAGService(retrieval_service)
    return indexer, rag_service, vector_store

def ingest_file(indexer, file_path: str):
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return
        
    print(f"\nReading and processing {file_path}...")
    loader = DocumentLoader()
    chunker = Chunker(max_chars=1500, overlap_chars=200)
    
    try:
        pages = loader.load_file(file_path)
    except Exception as e:
        print(f"Error loading file: {e}")
        return
        
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

    print(f"Extracted {len(chunks)} text chunks.")
    if chunks:
        indexed_ids = indexer.index_chunks(chunks, metadatas=metadatas, chunk_ids=chunk_ids)
        print(f"Successfully indexed {len(indexed_ids)} chunks into the Vector Store! \u2705")

def interactive_chat(rag_service, debug: bool = False):
    print("\n======================================")
    print("   RATAN Interactive Knowledge Chat   ")
    print("======================================")
    print("Type 'exit' or 'quit' to stop.")
    while True:
        try:
            query = input("\n\U0001F916 Ask a question: ")
            if query.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break
            if not query.strip():
                continue
                
            print("Thinking...")
            response = rag_service.generate_answer(query, debug=debug)
            
            print(f"\n\U0001F4AC Answer:\n{response['answer']}")
            
            if response.get('citations'):
                print("\n\U0001F4DA Citations used:")
                seen_citations = set()
                
                for citation in response['citations']:
                    meta = citation.get('metadata', {})
                    source = meta.get('source', 'Unknown')
                    page = meta.get('page_no', 'N/A')
                    section = meta.get('section', 'N/A')
                    
                    citation_key = (source, page, section)
                    if citation_key not in seen_citations:
                        seen_citations.add(citation_key)
                        print(f" * [{source} Page {page} - Section {section}]")
            else:
                print("\n\U0001F4DA No citations found in the database for this query.")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}")

def main():
    parser = argparse.ArgumentParser(description="RATAN RAG CLI tool")
    parser.add_argument("--ingest", type=str, help="Path to a PDF or TXT file to ingest")
    parser.add_argument("--chat", action="store_true", help="Start an interactive chat session")
    parser.add_argument("--reset", action="store_true", help="Reset the vector database before ingestion")
    parser.add_argument("--debug", action="store_true", help="Enable debug retrieval output")
    
    args = parser.parse_args()
    
    if not args.ingest and not args.chat and not args.reset:
        parser.print_help()
        sys.exit(1)
        
    print("Initializing AI Models (this might take a few seconds)...")
    indexer, rag_service, vector_store = get_services()
    
    if args.reset:
        print("Resetting vector database...")
        vector_store.reset_collection()
        indexer = Indexer(indexer.embedding_service, vector_store)
        rag_service.retrieval_service.vector_store = vector_store
        rag_service.retrieval_service.collection = vector_store.get_collection()
        print("Database reset complete.")
        
    if args.ingest:
        ingest_file(indexer, args.ingest)
        
    if args.chat:
        interactive_chat(rag_service, debug=args.debug)

if __name__ == "__main__":
    main()

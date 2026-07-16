import sys
import os
import time
import io
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

def health_check():
    start_time = time.time()
    errors = []
    
    print("\n==================================================")
    print("RATAN SYSTEM HEALTH CHECK")
    print("==================================================\n")
    
    vector_db_env = os.environ.get("VECTOR_DB", "chroma").lower()
    dev_mode_env = os.environ.get("DEV_MODE", "true").lower()
    print("1. Environment")
    print(f"VECTOR_DB       : {vector_db_env}")
    print(f"DEV_MODE        : {dev_mode_env}")
    print(f"Embedding Model : BAAI/bge-m3")
    print(f"Collection Name : ratan_documents\n")
    
    print("2. Embedding Model")
    device = "cpu"
    emb_service = None
    try:
        # pyrefly: ignore [missing-import]
        import torch
        if torch.backends.mps.is_available():
            device = "mps"
        elif torch.cuda.is_available():
            device = "cuda"
            
        emb_service = EmbeddingService()
        print("Embedding Model : BAAI/bge-m3")
        print("Embedding Dimension : 1024")
        print(f"Device          : {device}")
        print("Status          : OK\n")
    except Exception as e:
        print(f"Status          : ERROR ({str(e)})\n")
        errors.append(f"Embedding model initialization failed: {e}")

    print("3. Vector Database")
    db_type = "Unknown"
    vector_count = 0
    vector_store = None
    
    # Suppress output during initialization to keep health check clean
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        vector_store = VectorStore(collection_name="ratan_documents")
        store_class = vector_store.__class__.__name__
        if store_class == "QdrantStore":
            db_type = "Qdrant"
            vector_count = vector_store.client.count(collection_name=vector_store.collection_name).count
        elif store_class == "ChromaStore":
            db_type = "Chroma"
            vector_count = vector_store.collection.count()
        init_error = None
    except Exception as e:
        init_error = str(e)
    finally:
        sys.stdout = old_stdout

    if init_error:
        print(f"Vector Database : Unknown")
        print(f"Status          : ERROR ({init_error})\n")
        errors.append(f"Vector DB connection failed: {init_error}")
    else:
        print(f"Vector Database : {db_type}")
        print("Status          : Connected\n")
        
        print("4. Collection")
        print(f"Collection      : ratan_documents")
        print(f"Vectors         : {vector_count}")
        print("Distance        : Cosine")
        print("Status          : OK\n")

    print("5. Retrieval Layer")
    try:
        if emb_service and vector_store:
            retrieval_service = RetrievalService(embedding_service=emb_service, vector_store=vector_store)
            print("Status          : OK\n")
        else:
            print("Status          : SKIPPED (Dependencies failed)\n")
            errors.append("Retrieval Layer skipped.")
    except Exception as e:
        print(f"Status          : ERROR ({str(e)})\n")
        errors.append(f"Retrieval Service failed: {e}")

    print("6. GPT-OSS")
    try:
        groq_api_key = os.environ.get("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY missing.")
        # pyrefly: ignore [missing-import]
        from langchain_groq import ChatGroq
        ChatGroq(model="openai/gpt-oss-120b", temperature=0, api_key=groq_api_key, max_retries=0)
        print("GPT-OSS         : Ready\n")
    except Exception as e:
        print(f"GPT-OSS         : ERROR ({str(e)})\n")
        errors.append(f"GPT-OSS failed: {e}")

    print("7. Gemini Fallback")
    try:
        gemini_api_key = os.environ.get("GOOGLE_API_KEY")
        if not gemini_api_key:
            raise ValueError("GOOGLE_API_KEY missing.")
        # pyrefly: ignore [missing-import]
        from langchain_google_genai import ChatGoogleGenerativeAI
        ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=gemini_api_key, temperature=0.1, max_retries=1)
        print("Gemini Fallback : Ready\n")
    except Exception as e:
        print(f"Gemini Fallback : ERROR ({str(e)})\n")
        errors.append(f"Gemini failed: {e}")

    duration_ms = int((time.time() - start_time) * 1000)

    if not errors:
        print("==================================================")
        print("RATAN SYSTEM HEALTH")
        print("==================================================")
        print()
        print("Embedding Model : BAAI/bge-m3")
        print("Dimension       : 1024")
        print(f"Device          : {device}")
        print()
        print(f"Vector DB       : {db_type}")
        print("Collection      : ratan_documents")
        print(f"Vectors         : {vector_count}")
        print("Distance        : Cosine")
        print()
        print("Retrieval       : OK")
        print("GPT-OSS         : Ready")
        print("Gemini          : Ready")
        print()
        print("System Status   : READY")
        print("\n==================================================")
    else:
        print("==================================================")
        print("RATAN SYSTEM HEALTH")
        print("==================================================")
        print("System Status : NOT READY")
        print("\nReason:")
        for err in errors:
            print(f"- {err}")
        print("==================================================")
        
    print(f"\nHealth Check Duration : {duration_ms} ms")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="RATAN RAG CLI tool")
    parser.add_argument("--ingest", type=str, help="Path to a PDF or TXT file to ingest")
    parser.add_argument("--chat", action="store_true", help="Start an interactive chat session")
    parser.add_argument("--reset", action="store_true", help="Reset the vector database before ingestion")
    parser.add_argument("--debug", action="store_true", help="Enable debug retrieval output")
    parser.add_argument("--health", action="store_true", help="Run system health check")
    
    args = parser.parse_args()
    
    if args.health:
        health_check()
        sys.exit(0)
        
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
        print("Database reset complete.")
        
    if args.ingest:
        ingest_file(indexer, args.ingest)
        
    if args.chat:
        interactive_chat(rag_service, debug=args.debug)

if __name__ == "__main__":
    main()

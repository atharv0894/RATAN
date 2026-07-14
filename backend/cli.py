import argparse
import sys
import os
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
import pdfplumber

# Load environment variables (e.g. GROQ_API_KEY from .env)
load_dotenv()

from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import VectorStore
from app.rag.indexer import Indexer
from app.rag.retrieval_service import RetrievalService
from app.rag.rag_service import RAGService

def get_services():
    embedding_service = EmbeddingService()
    vector_store = VectorStore()
    indexer = Indexer(embedding_service, vector_store)
    retrieval_service = RetrievalService(embedding_service, vector_store)
    rag_service = RAGService(retrieval_service)
    return indexer, rag_service

def ingest_file(indexer, file_path: str):
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return
        
    print(f"\nReading and processing {file_path}...")
    chunks = []
    metadatas = []
    
    if file_path.lower().endswith('.pdf'):
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if not text: 
                    continue
                # Split by double newline to grab paragraphs
                paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 30]
                for p in paragraphs:
                    chunks.append(p)
                    metadatas.append({"source": os.path.basename(file_path), "page_no": page_num})
    elif file_path.lower().endswith('.txt'):
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
            paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 30]
            for p in paragraphs:
                chunks.append(p)
                metadatas.append({"source": os.path.basename(file_path)})
    else:
        print("Unsupported file format. Please provide a .pdf or .txt file.")
        return

    print(f"Extracted {len(chunks)} text chunks.")
    if chunks:
        chunk_ids = indexer.index_chunks(chunks, metadatas=metadatas)
        print(f"Successfully indexed {len(chunk_ids)} chunks into the Vector Store! \u2705")

def interactive_chat(rag_service):
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
            response = rag_service.generate_answer(query)
            
            print(f"\n\U0001F4AC Answer:\n{response['answer']}")
            
            if response.get('citations'):
                print("\n\U0001F4DA Citations used:")
                for citation in response['citations']:
                    meta = citation.get('metadata', {})
                    source = meta.get('source', 'Unknown')
                    page = meta.get('page_no', 'N/A')
                    score = citation.get('distance', 0)
                    print(f" - [{source} Page {page}] (Match Score: {score:.2f})")
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
    
    args = parser.parse_args()
    
    if not args.ingest and not args.chat:
        parser.print_help()
        sys.exit(1)
        
    print("Initializing AI Models (this might take a few seconds)...")
    indexer, rag_service = get_services()
    
    if args.ingest:
        ingest_file(indexer, args.ingest)
        
    if args.chat:
        interactive_chat(rag_service)

if __name__ == "__main__":
    main()

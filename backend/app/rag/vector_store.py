import os
import sys

def get_vector_store(collection_name="ratan_documents", **kwargs):
    vector_db_choice = os.environ.get("VECTOR_DB", "chroma").lower()
    dev_mode = os.environ.get("DEV_MODE", "true").lower() == "true"
    
    if vector_db_choice == "qdrant":
        try:
            from app.rag.qdrant_store import QdrantStore
            store = QdrantStore(collection_name=collection_name)
            print("--------------------------------")
            print("RATAN Initializing")
            print("Embedding Model : BAAI/bge-m3")
            print("Vector DB : Qdrant")
            print("Collection : ratan_documents")
            print("Dimension : 1024")
            print("Distance : Cosine")
            print("LLM : GPT-OSS 120B")
            print("Fallback : Gemini 2.5 Flash")
            print("Ready")
            print("--------------------------------")
            return store
        except Exception as e:
            if dev_mode:
                print(f"Qdrant unavailable: {e}")
                print("Using Chroma fallback.")
                from app.rag.chroma_store import ChromaStore
                return ChromaStore(collection_name=collection_name)
            else:
                print(f"Error: Qdrant connection failed in production: {e}")
                sys.exit(1)
    else:
        # Default to Chroma
        from app.rag.chroma_store import ChromaStore
        print("--------------------------------")
        print("RATAN Initializing")
        print("Embedding Model : BAAI/bge-m3")
        print("Vector DB : Chroma (Fallback)")
        print("Collection : ratan_documents")
        print("Dimension : 1024")
        print("Distance : Cosine")
        print("LLM : GPT-OSS 120B")
        print("Fallback : Gemini 2.5 Flash")
        print("Ready")
        print("--------------------------------")
        return ChromaStore(collection_name=collection_name)

class VectorStore:
    def __new__(cls, collection_name="ratan_documents", **kwargs):
        # Acts as a factory
        return get_vector_store(collection_name=collection_name, **kwargs)


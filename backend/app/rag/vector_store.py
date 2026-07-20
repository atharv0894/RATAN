import os
import sys
import logging

def get_vector_store(collection_name="ratan_documents", **kwargs):
    vector_db_choice = "qdrant"
    dev_mode = os.environ.get("DEV_MODE", "true").lower() == "true"
    
    if vector_db_choice == "qdrant":
        try:
            from app.rag.qdrant_store import QdrantStore
            store = QdrantStore(collection_name=collection_name)
            logging.info("--------------------------------")
            logging.info("RATAN Initializing")
            logging.info("Embedding Model : sentence-transformers/all-MiniLM-L6-v2")
            logging.info("Vector DB : Qdrant")
            logging.info("Collection : ratan_documents")
            logging.info("Dimension : 384")
            logging.info("Distance : Cosine")
            logging.info("LLM : GPT-OSS 120B")
            logging.info("Fallback : Gemini 2.5 Flash")
            logging.info("Ready")
            logging.info("--------------------------------")
            return store
        except Exception as e:
            if dev_mode:
                logging.warning(f"Qdrant unavailable: {e}")
                logging.warning("Using Chroma fallback.")
                from app.rag.chroma_store import ChromaStore
                return ChromaStore(collection_name=collection_name)
            else:
                logging.error(f"Error: Qdrant connection failed in production: {e}")
                raise RuntimeError(f"Qdrant connection failed: {e}")
    else:
        # Default to Chroma
        from app.rag.chroma_store import ChromaStore
        logging.info("--------------------------------")
        logging.info("RATAN Initializing")
        logging.info("Embedding Model : sentence-transformers/all-MiniLM-L6-v2")
        logging.info("Vector DB : Chroma (Fallback)")
        logging.info("Collection : ratan_documents")
        logging.info("Dimension : 384")
        logging.info("Distance : Cosine")
        logging.info("LLM : GPT-OSS 120B")
        logging.info("Fallback : Gemini 2.5 Flash")
        logging.info("Ready")
        logging.info("--------------------------------")
        return ChromaStore(collection_name=collection_name)

class VectorStore:
    def __new__(cls, collection_name="ratan_documents", **kwargs):
        # Acts as a factory
        return get_vector_store(collection_name=collection_name, **kwargs)

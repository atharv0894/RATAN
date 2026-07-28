import os
import sys
import logging
from app.rag.qdrant_store import QdrantStore

def get_vector_store(collection_name="ratan_documents", **kwargs):
    try:
        store = QdrantStore(collection_name=collection_name)
        logging.info("--------------------------------")
        logging.info("RATAN Initializing")
        logging.info("Embedding Model :")
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
        logging.error(f"Error: Qdrant connection failed: {e}")
        raise RuntimeError(f"Qdrant connection failed: {e}")

class VectorStore:
    def __new__(cls, collection_name="ratan_documents", **kwargs):
        # Acts as a factory
        return get_vector_store(collection_name=collection_name, **kwargs)

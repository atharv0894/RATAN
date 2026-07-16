# pyrefly: ignore [missing-import]
import chromadb
import os

class ChromaStore:
    def __init__(self, persist_directory="./chroma_db", collection_name="ratan_documents"):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            if not self.collection.metadata or self.collection.metadata.get("embedding_model") != "BAAI/bge-m3":
                self.reset_collection()
        except Exception:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine", "embedding_model": "BAAI/bge-m3", "embedding_dim": "1024"}
            )
            
    def reset_collection(self):
        try:
            self.client.delete_collection(name=self.collection_name)
        except Exception:
            pass
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine", "embedding_model": "BAAI/bge-m3", "embedding_dim": "1024"}
        )
        
    def upsert(self, ids: list[str], embeddings: list[list[float]], documents: list[str], metadatas: list[dict]):
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
    def query(self, query_embeddings: list[list[float]], n_results: int, include: list[str]):
        return self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            include=include
        )
        
    def delete_by_source(self, source: str):
        self.collection.delete(where={"source": source})

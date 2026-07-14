# pyrefly: ignore [missing-import]
import chromadb
# pyrefly: ignore [missing-import]
import os

class VectorStore:
    def __init__(self, persist_directory="./chroma_db", collection_name="industrial_knowledge"):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_or_create_collection(name=self.collection_name)
        
    def get_collection(self):
        return self.collection

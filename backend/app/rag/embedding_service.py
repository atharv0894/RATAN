import os
import logging
from langchain_google_genai import GoogleGenerativeAIEmbeddings

class EmbeddingService:
    def __init__(self, model_name="models/text-embedding-004", device=None, batch_size=8):
        self.device = "api"
        self.batch_size = batch_size
        google_api_key = os.environ.get("GOOGLE_API_KEY")
        if not google_api_key:
            logging.warning("GOOGLE_API_KEY missing. Embeddings will fail.")
            
        self.model = GoogleGenerativeAIEmbeddings(model=model_name, google_api_key=google_api_key)
        print(f"Loading remote API embedding model: {model_name} on {self.device}")
        
    def generate_embeddings(self, texts: list):
        return self.model.embed_documents(texts)
        
    def generate_embedding(self, text: str):
        return self.model.embed_query(text)


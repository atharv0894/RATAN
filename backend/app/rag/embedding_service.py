import os
import logging
# pyrefly: ignore [missing-import]
from langchain_google_genai import GoogleGenerativeAIEmbeddings

class EmbeddingService:
    def __init__(self, model_name="models/text-embedding-004", device=None, batch_size=8):
        # We ignore device and batch_size since it's an API call
        google_api_key = os.environ.get("GOOGLE_API_KEY")
        if not google_api_key:
            logging.warning("GOOGLE_API_KEY is missing! Embeddings will fail.")
        
        self.model = GoogleGenerativeAIEmbeddings(
            model=model_name,
            google_api_key=google_api_key
        )
        self.dimension = 768  # text-embedding-004 dimension
        logging.info(f"Initialized Google Gemini Embeddings: {model_name}")
        
    def generate_embeddings(self, texts: list):
        # langchain embed_documents returns a list of lists of floats
        return self.model.embed_documents(texts)
        
    def generate_embedding(self, text: str):
        return self.model.embed_query(text)

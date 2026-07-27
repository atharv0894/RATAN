import os
import httpx
import logging

class EmbeddingService:
    def __init__(self, model_name="mistral-embed", device=None, batch_size=8):
        self.model_name = model_name
        self.api_key = os.environ.get("MISTRAL_API_KEY")
        if not self.api_key:
            logging.warning("MISTRAL_API_KEY is missing! Embeddings will fail.")
        print(f"Initialized Mistral API Embeddings: {model_name}")
        
    def generate_embeddings(self, texts: list):
        if not texts:
            return []
            
        url = "https://api.mistral.ai/v1/embeddings"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "model": self.model_name,
            "input": texts
        }
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
        embeddings_data = sorted(result["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in embeddings_data]
        
    def generate_embedding(self, text: str):
        return self.generate_embeddings([text])[0]
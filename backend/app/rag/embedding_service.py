# pyrefly: ignore [missing-import]
from sentence_transformers import SentenceTransformer
# pyrefly: ignore [missing-import]
import torch

class EmbeddingService:
    def __init__(self, model_name="BAAI/bge-m3", device=None, batch_size=8):
        if device is None:
            if torch.backends.mps.is_available():
                device = "mps"
            elif torch.cuda.is_available():
                device = "cuda"
            else:
                device = "cpu"
                
        self.device = device
        self.batch_size = batch_size
        self.model = SentenceTransformer(model_name, device=self.device)
        print(f"Loading embedding model: {model_name} on {self.device}")
        
    def generate_embeddings(self, texts: list):
        return self.model.encode(texts, batch_size=self.batch_size, normalize_embeddings=True).tolist()
        
    def generate_embedding(self, text: str):
        return self.generate_embeddings([text])[0]

# pyrefly: ignore [missing-import]
from sentence_transformers import SentenceTransformer
# pyrefly: ignore [missing-import]
import torch
import os

# Drastically reduce RAM footprint for the 512MB Render instance
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
torch.set_num_threads(1)

class EmbeddingService:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2", device=None, batch_size=8):
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
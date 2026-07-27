import logging
from fastembed import TextEmbedding

# Initialize globally to prevent memory spikes on every API call
try:
    # Using a lightweight multilingual model to support Hindi/Marathi within the 512MB RAM limit
    _embedding_model = TextEmbedding(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    logging.info("Initialized fastembed model: paraphrase-multilingual-MiniLM-L12-v2")
except Exception as e:
    logging.error(f"Failed to initialize fastembed model: {e}")
    _embedding_model = None

class EmbeddingService:
    def __init__(self, model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", device=None, batch_size=8):
        self.model_name = model_name
        self.batch_size = batch_size
        
    def generate_embeddings(self, texts: list):
        if not texts:
            return []
            
        if not _embedding_model:
            logging.error("Embedding model is not initialized.")
            return []
            
        # fastembed's .embed() returns a generator of numpy arrays
        embeddings_generator = _embedding_model.embed(texts, batch_size=self.batch_size)
        
        # Convert to standard list of floats
        return [embedding.tolist() for embedding in embeddings_generator]
        
    def generate_embedding(self, text: str):
        embeddings = self.generate_embeddings([text])
        if embeddings:
            return embeddings[0]
        return []
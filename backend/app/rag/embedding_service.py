import logging
from fastembed import TextEmbedding

_embedding_model = None

class EmbeddingService:
    def __init__(self, model_name="BAAI/bge-small-en-v1.5", device=None, batch_size=8):
        self.model_name = model_name
        self.batch_size = batch_size
        
    def _get_model(self):
        global _embedding_model
        if _embedding_model is None:
            try:
                logging.info(f"Lazily initializing fastembed model: {self.model_name}...")
                _embedding_model = TextEmbedding(model_name=self.model_name)
                logging.info("Model initialized successfully.")
            except Exception as e:
                logging.error(f"Failed to initialize fastembed model: {e}")
                raise e
        return _embedding_model

    def generate_embeddings(self, texts: list):
        if not texts:
            return []
            
        model = self._get_model()
            
        # fastembed's .embed() returns a generator of numpy arrays
        embeddings_generator = model.embed(texts, batch_size=self.batch_size)
        
        # Convert to standard list of floats
        return [embedding.tolist() for embedding in embeddings_generator]
        
    def generate_embedding(self, text: str):
        embeddings = self.generate_embeddings([text])
        if embeddings:
            return embeddings[0]
        return []
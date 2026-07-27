import sys
import os
sys.path.append(os.getcwd())
from backend.app.rag.embedding_service import EmbeddingService

try:
    svc = EmbeddingService()
    emb = svc.generate_embedding("Test question")
    print(f"Success! Dimension: {len(emb)}")
except Exception as e:
    import traceback
    traceback.print_exc()

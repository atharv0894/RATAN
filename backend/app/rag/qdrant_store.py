import os
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

class QdrantStore:
    def __init__(self, collection_name="ratan_documents"):
        url = os.environ.get("QDRANT_URL")
        api_key = os.environ.get("QDRANT_API_KEY")
        self.collection_name = collection_name
        self.client = QdrantClient(url=url, api_key=api_key)
        
        self._ensure_collection()

    def _ensure_collection(self):
        collections = self.client.get_collections().collections
        if not any(c.name == self.collection_name for c in collections):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
            )

    def reset_collection(self):
        try:
            self.client.delete_collection(collection_name=self.collection_name)
        except Exception:
            pass
        self._ensure_collection()
        
    def _generate_uuid(self, chunk_id: str) -> str:
        """Qdrant requires integer or UUID ids. We deterministically map our string IDs to UUIDs."""
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))
        
    def upsert(self, ids: list[str], embeddings: list[list[float]], documents: list[str], metadatas: list[dict]):
        points = []
        for i in range(len(ids)):
            payload = metadatas[i].copy() if metadatas[i] else {}
            payload["document_text"] = documents[i]
            # Store original string ID in payload so it's not lost
            payload["original_chunk_id"] = ids[i] 
            
            qdrant_id = self._generate_uuid(ids[i])
            points.append(PointStruct(id=qdrant_id, vector=embeddings[i], payload=payload))
            
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
    def query(self, query_embeddings: list[list[float]], n_results: int, include: list[str]):
        query_vector = query_embeddings[0]
        
        search_result = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=n_results,
            with_payload=True,
            with_vectors=True
        ).points
        
        documents = []
        metadatas = []
        distances = []
        embeddings = []
        
        for hit in search_result:
            payload = hit.payload.copy()
            doc = payload.pop("document_text", "")
            
            # Restore original chunk_id for compatibility
            if "original_chunk_id" in payload:
                payload["chunk_id"] = payload.pop("original_chunk_id")
                
            documents.append(doc)
            metadatas.append(payload)
            # Distance in Chroma is typically 1 - cosine_similarity for cosine space
            distances.append(1.0 - hit.score) 
            embeddings.append(hit.vector)
            
        return {
            'documents': [documents],
            'metadatas': [metadatas],
            'distances': [distances],
            'embeddings': [embeddings]
        }

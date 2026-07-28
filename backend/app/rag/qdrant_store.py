import os
import uuid
# pyrefly: ignore [missing-import]
from qdrant_client import QdrantClient
# pyrefly: ignore [missing-import]
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

class QdrantStore:
    def __init__(self, collection_name="ratan_documents"):
        url = os.environ.get("QDRANT_URL")
        api_key = os.environ.get("QDRANT_API_KEY")
        timeout = float(os.environ.get("QDRANT_TIMEOUT", "30.0"))
        self.collection_name = collection_name
        if url == ":memory:":
            self.client = QdrantClient(location=":memory:", api_key=api_key, timeout=timeout)
        else:
            self.client = QdrantClient(url=url, api_key=api_key, timeout=timeout)
        
        self._ensure_collection()

    def _ensure_collection(self):
            
        # Create indexes for filtering (Required by Qdrant Cloud strict mode)
        # It's safe to call these even if the collection already exists
        try:
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="source",
                field_schema="keyword",
            )
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="organization_id",
                field_schema="keyword",
            )
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="is_latest",
                field_schema="integer",
            )
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="document_id",
                field_schema="keyword",
            )
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="version_id",
                field_schema="keyword",
            )
        except Exception as e:
            print(f"Warning: Payload index creation skipped/failed: {e}")

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
        
    def query(self, query_embeddings: list[list[float]], n_results: int, include: list[str], where: dict = None):
        query_vector = query_embeddings[0]
        
        # Build filter if where clause is provided
        query_filter = None
        if where:
            must_conditions = []
            for k, v in where.items():
                if isinstance(v, dict) and "$in" in v:
                    # Qdrant supports 'should' with multiple MatchValues
                    should_conditions = [FieldCondition(key=k, match=MatchValue(value=val)) for val in v["$in"]]
                    must_conditions.append(Filter(should=should_conditions))
                else:
                    must_conditions.append(FieldCondition(key=k, match=MatchValue(value=v)))
                    
            if must_conditions:
                query_filter = Filter(must=must_conditions)
        
        search_result = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=n_results,
            query_filter=query_filter,
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
        
    def delete_by_source(self, source: str):
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="source",
                        match=MatchValue(value=source)
                    )
                ]
            )
        )
        
    def delete_by_document_id(self, document_id: str):
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
        )
        
    def count_by_document_id(self, document_id: str) -> int:
        res = self.client.count(
            collection_name=self.collection_name,
            count_filter=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
        )
        return res.count
        
    def get_by_chunk_id(self, chunk_id: str):
        qdrant_id = self._generate_uuid(chunk_id)
        results = self.client.retrieve(
            collection_name=self.collection_name,
            ids=[qdrant_id],
            with_payload=True
        )
        if not results:
            return None
            
        payload = results[0].payload
        return {
            "chunk_id": chunk_id,
            "text": payload.get("document_text", ""),
            "metadata": payload
        }

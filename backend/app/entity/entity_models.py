# pyrefly: ignore [missing-import]
from pydantic import BaseModel
from typing import List, Optional

class EntityBase(BaseModel):
    type: str
    value: str

class EntityResponse(EntityBase):
    entity_id: str
    document_id: str
    chunk_id: Optional[str]
    page_number: Optional[int]
    section: Optional[str]
    
class ExtractedEntitiesResponse(BaseModel):
    document_id: str
    entities: List[EntityResponse]

class EntitySearchResponse(BaseModel):
    query: str
    results: List[EntityResponse]

from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.entity.entity_extractor import EntityExtractor
from app.api.responses import APISuccessResponse
from app.services.dependencies import get_current_user, RequireRole
from app.exceptions import NotFoundError

router = APIRouter()
extractor = EntityExtractor()

class EntityResponse(BaseModel):
    id: str
    type: str
    value: str

class EntitySearchResponse(BaseModel):
    query: str
    results: List[EntityResponse]

class ExtractedEntitiesResponse(BaseModel):
    document_id: str
    entities: List[EntityResponse]

@router.get("", response_model=APISuccessResponse[List[EntityResponse]])
def get_all_entities(current_user: dict = Depends(RequireRole(["Admin", "Plant Manager", "Maintenance Engineer", "Quality Engineer", "Operator"]))):
    from app.database.sqlite import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    # Scoped to tenant if we store org_id on entities, currently we do not, so we just group by
    cursor.execute("SELECT * FROM entities GROUP BY entity_value")
    rows = cursor.fetchall()
    conn.close()
    
    response = []
    for r in rows:
        d = dict(r)
        response.append(EntityResponse(
            id=d.get("id", ""),
            type=d.get("entity_type"),
            value=d.get("entity_value")
        ))
    return APISuccessResponse(data=response)

@router.get("/{entity_name}", response_model=APISuccessResponse[EntitySearchResponse])
def search_entities_by_name(entity_name: str, current_user: dict = Depends(get_current_user)):
    results = extractor.search_entities(entity_name)
    entities = []
    for r in results:
        entities.append(EntityResponse(
            id=r.get("id", ""),
            type=r.get("entity_type"),
            value=r.get("entity_value")
        ))
    return APISuccessResponse(data=EntitySearchResponse(query=entity_name, results=entities))

@router.get("/documents/{id}/entities", response_model=APISuccessResponse[ExtractedEntitiesResponse])
def get_document_entities(id: str, current_user: dict = Depends(get_current_user)):
    results = extractor.get_document_entities(id)
    if not results:
        from app.database.sqlite import get_db_connection
        conn = get_db_connection()
        doc = conn.cursor().execute("SELECT id FROM documents WHERE id = ?", (id,)).fetchone()
        conn.close()
        if not doc:
            raise NotFoundError("Document", id)
            
    entities = []
    for r in results:
        entities.append(EntityResponse(
            id=r.get("id", ""),
            type=r.get("entity_type"),
            value=r.get("entity_value")
        ))
    return APISuccessResponse(data=ExtractedEntitiesResponse(document_id=id, entities=entities))

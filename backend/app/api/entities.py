from fastapi import APIRouter, HTTPException
from typing import List
from app.entity.entity_extractor import EntityExtractor
from app.entity.entity_models import EntityResponse, ExtractedEntitiesResponse, EntitySearchResponse

router = APIRouter()
extractor = EntityExtractor()

@router.get("", response_model=List[EntityResponse])
def get_all_entities():
    # Gets a unique list of all entities extracted across all docs
    # Let's query SQLite for unique entities
    from app.database.sqlite import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM entities GROUP BY entity_value")
    rows = cursor.fetchall()
    conn.close()
    
    response = []
    for r in rows:
        d = dict(r)
        d["type"] = d.get("entity_type")
        d["value"] = d.get("entity_value")
        response.append(EntityResponse(**d))
    return response

@router.get("/{entity_name}", response_model=EntitySearchResponse)
def search_entities_by_name(entity_name: str):
    results = extractor.search_entities(entity_name)
    entities = []
    for r in results:
        r["type"] = r.get("entity_type")
        r["value"] = r.get("entity_value")
        entities.append(EntityResponse(**r))
    return EntitySearchResponse(query=entity_name, results=entities)

@router.get("/documents/{id}/entities", response_model=ExtractedEntitiesResponse)
def get_document_entities(id: str):
    results = extractor.get_document_entities(id)
    if not results:
        # Check if doc exists
        from app.database.sqlite import get_db_connection
        conn = get_db_connection()
        doc = conn.cursor().execute("SELECT document_id FROM documents WHERE document_id = ?", (id,)).fetchone()
        conn.close()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
            
    entities = []
    for r in results:
        r["type"] = r.get("entity_type")
        r["value"] = r.get("entity_value")
        entities.append(EntityResponse(**r))
    return ExtractedEntitiesResponse(document_id=id, entities=entities)

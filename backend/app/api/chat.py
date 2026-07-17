# pyrefly: ignore [missing-import]
from fastapi import APIRouter
from app.models.requests import ChatRequest
from app.models.responses import ChatResponse
from app.services.dependencies import get_rag_service
from app.entity.entity_extractor import EntityExtractor

router = APIRouter()
extractor = EntityExtractor()

@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):
    # Entity Extraction from query
    query_entities = extractor.extract_from_text(request.question)
    where_clause = None
    
    if query_entities:
        # Get matching documents for these entities
        from app.database.sqlite import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        doc_ids = set()
        for e in query_entities:
            # Simple match
            cursor.execute("SELECT document_id FROM entities WHERE entity_value LIKE ?", (f"%{e['value']}%",))
            for row in cursor.fetchall():
                doc_ids.add(row[0])
                
        if doc_ids:
            # Map doc_ids to filenames (source in vector store)
            placeholders = ",".join("?" * len(doc_ids))
            cursor.execute(f"SELECT filename FROM documents WHERE document_id IN ({placeholders})", list(doc_ids))
            filenames = [r[0] for r in cursor.fetchall()]
            
            if filenames:
                where_clause = {"source": {"$in": filenames}}
        conn.close()

    rag_service = get_rag_service()
    result = rag_service.generate_answer(request.question, where=where_clause)
    
    return ChatResponse(
        answer=result.get("answer", ""),
        citations=result.get("citations", []),
        entities=query_entities
    )

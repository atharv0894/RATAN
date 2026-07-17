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
    if not request.question or not request.question.strip():
        return ChatResponse(answer="Please provide a valid question.", citations=[], entities=[])
        
    where_clause = None
    
    # Phase 6: Mode 2 Document Search
    if request.filename:
        where_clause = {"source": request.filename}
    elif request.document_id:
        # Resolve document_id to filename
        from app.database.sqlite import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT filename FROM documents WHERE document_id = ?", (request.document_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            where_clause = {"source": row[0]}
        else:
            return ChatResponse(answer="Specified document not found.", citations=[], entities=[])

    # Entity Extraction from query
    query_entities = []
    try:
        query_entities = extractor.extract_from_text(request.question)
    except Exception as e:
        import logging
        logging.warning(f"Entity extraction failed for query: {str(e)}")
        
    # Phase 6: Mode 1 Global Search with Entity Filtering (only if Mode 2 is not active)
    if not where_clause and query_entities:
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

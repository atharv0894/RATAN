import time
import uuid
from typing import List, Dict
from app.entity.entity_patterns import COMPILED_PATTERNS, COMPILED_CLASSIFICATIONS
from app.database.sqlite import get_db_connection

class EntityExtractor:
    def __init__(self):
        pass

    def extract_from_text(self, text: str) -> List[Dict[str, str]]:
        entities = []
        for entity_type, patterns in COMPILED_PATTERNS.items():
            for pattern in patterns:
                matches = pattern.finditer(text)
                for match in matches:
                    entities.append({
                        "type": entity_type,
                        "value": match.group(0).strip()
                    })
        
        # Deduplicate within the same text block
        unique_entities = []
        seen = set()
        for e in entities:
            identifier = (e["type"], e["value"].upper())
            if identifier not in seen:
                seen.add(identifier)
                unique_entities.append(e)
                
        return unique_entities

    def classify_document(self, text: str) -> str:
        for doc_class, patterns in COMPILED_CLASSIFICATIONS.items():
            for pattern in patterns:
                if pattern.search(text):
                    return doc_class
        return "Unknown"

    def save_entities(self, document_id: str, chunk_id: str, page_number: int, section: str, entities: List[Dict[str, str]]):
        if not entities:
            return
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        timestamp = time.time()
        for e in entities:
            entity_id = str(uuid.uuid4())
            cursor.execute(
                '''INSERT INTO entities (entity_id, document_id, chunk_id, entity_type, entity_value, page_number, section, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (entity_id, document_id, chunk_id, e["type"], e["value"], page_number, section, timestamp)
            )
        conn.commit()
        conn.close()

    def get_document_entities(self, document_id: str, org_id: str):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.* FROM entities e
            JOIN documents d ON e.document_id = d.id
            WHERE e.document_id = ? AND d.organization = ?
            ORDER BY e.created_at ASC
        """, (document_id, org_id))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def search_entities(self, query: str, org_id: str):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.* FROM entities e
            JOIN documents d ON e.document_id = d.id
            WHERE e.entity_value LIKE ? AND d.organization = ?
            ORDER BY e.created_at DESC
        """, (f"%{query}%", org_id))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

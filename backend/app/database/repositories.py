import sqlite3
import uuid
import time
from typing import List, Dict, Any, Optional

def get_system_user(cursor: sqlite3.Cursor) -> str:
    cursor.execute("SELECT id FROM users WHERE email = 'system@ratan.local'")
    res = cursor.fetchone()
    if res: return res['id']
    return "unknown"
    
def get_system_org_plant_dept(cursor: sqlite3.Cursor):
    cursor.execute("SELECT id FROM organizations LIMIT 1")
    org = cursor.fetchone()
    cursor.execute("SELECT id FROM plants LIMIT 1")
    plant = cursor.fetchone()
    cursor.execute("SELECT id FROM departments LIMIT 1")
    dept = cursor.fetchone()
    return org['id'] if org else "", plant['id'] if plant else "", dept['id'] if dept else ""

class DocumentRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        
    def find_by_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE filename = ? AND is_deleted = 0", (filename,))
        row = cursor.fetchone()
        return dict(row) if row else None
        
    def get_latest_version(self, document_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM document_versions 
            WHERE document_id = ? AND is_latest = 1 AND is_deleted = 0
        """, (document_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_version_by_id(self, version_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM document_versions WHERE id = ? AND is_deleted = 0", (version_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def create_document(self, filename: str, title: str, doc_type: str = 'Unknown') -> str:
        cursor = self.conn.cursor()
        doc_id = str(uuid.uuid4())
        sys_user = get_system_user(cursor)
        org, plant, dept = get_system_org_plant_dept(cursor)
        now = time.time()
        
        cursor.execute("""
            INSERT INTO documents (
                id, org_id, plant_id, department_id, owner_id, title, filename, 
                document_type, language, equipment, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (doc_id, org, plant, dept, sys_user, title, filename, doc_type, 'en', 'Unknown', now, now))
        self.conn.commit()
        return doc_id
        
    def add_version(self, document_id: str, checksum: str, size: int, mime: str, 
                    storage_path: str, chunk_count: int, vector_collection: str, 
                    model: str, previous_version_id: str = None) -> str:
        cursor = self.conn.cursor()
        version_id = str(uuid.uuid4())
        sys_user = get_system_user(cursor)
        now = time.time()
        
        # Unmark previous latest
        cursor.execute("UPDATE document_versions SET is_latest = 0 WHERE document_id = ?", (document_id,))
        
        # Get next version number
        cursor.execute("SELECT MAX(version_number) as max_v FROM document_versions WHERE document_id = ?", (document_id,))
        res = cursor.fetchone()
        next_v = (res['max_v'] or 0) + 1
        
        cursor.execute("""
            INSERT INTO document_versions (
                id, document_id, version_number, uploaded_by, storage_provider, storage_path,
                mime_type, file_size, checksum, page_count, chunk_count, embedding_model,
                vector_collection, vector_count, is_latest, previous_version_id, created_at, updated_at, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            version_id, document_id, next_v, sys_user, 'local', storage_path,
            mime, size, checksum, 0, chunk_count, model, vector_collection, chunk_count, 1, previous_version_id, now, now, 'Active'
        ))
        
        cursor.execute("UPDATE documents SET updated_at = ? WHERE id = ?", (now, document_id))
        self.conn.commit()
        return version_id

    def list_latest_versions(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT d.id as document_id, d.filename, d.title, 
                   v.id as version_id, v.version_number, v.status, v.file_size, v.chunk_count, v.created_at, v.storage_provider, v.is_deleted
            FROM documents d
            JOIN document_versions v ON d.id = v.document_id
            WHERE v.is_latest = 1 AND d.is_deleted = 0
        """)
        return [dict(r) for r in cursor.fetchall()]

    def soft_delete_document(self, document_id: str):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE documents SET is_deleted = 1 WHERE id = ?", (document_id,))
        cursor.execute("UPDATE document_versions SET is_deleted = 1 WHERE document_id = ?", (document_id,))
        self.conn.commit()
        
    def check_duplicate_checksum(self, checksum: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM document_versions WHERE checksum = ? AND is_deleted = 0 LIMIT 1", (checksum,))
        return cursor.fetchone() is not None

class AuditRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        
    def log(self, action: str, resource: str, status: str, endpoint: str = 'SYSTEM', execution_time_ms: int = 0):
        cursor = self.conn.cursor()
        sys_user = get_system_user(cursor)
        log_id = str(uuid.uuid4())
        now = time.time()
        
        cursor.execute("""
            INSERT INTO audit_logs (
                id, user_id, endpoint, action, resource, status, ip_address, execution_time_ms, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (log_id, sys_user, endpoint, action, resource, status, '127.0.0.1', execution_time_ms, now, now))
        self.conn.commit()

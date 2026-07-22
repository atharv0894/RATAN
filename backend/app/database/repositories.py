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
    cursor.execute("SELECT name FROM organizations LIMIT 1")
    org = cursor.fetchone()
    cursor.execute("SELECT name FROM plants LIMIT 1")
    plant = cursor.fetchone()
    cursor.execute("SELECT name FROM departments LIMIT 1")
    dept = cursor.fetchone()
    return org['name'] if org else "Unknown", plant['name'] if plant else "Unknown", dept['name'] if dept else "Unknown"

class DocumentRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        
    def find_by_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE filename = ? AND deleted_at IS NULL", (filename,))
        row = cursor.fetchone()
        return dict(row) if row else None
        
    def get_latest_version(self, document_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT v.* FROM document_versions v
            JOIN documents d ON v.document_id = d.id
            WHERE v.document_id = ? AND v.is_latest = 1 AND d.deleted_at IS NULL
        """, (document_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_version_by_id(self, version_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT v.* FROM document_versions v
            JOIN documents d ON v.document_id = d.id
            WHERE v.id = ? AND d.deleted_at IS NULL
        """, (version_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def create_document(self, filename: str, title: str, user_id: str, org_id: str, plant_id: str, dept_id: str) -> str:
        cursor = self.conn.cursor()
        doc_id = str(uuid.uuid4())
        now = time.time()
        
        cursor.execute("""
            INSERT INTO documents (
                id, title, filename, owner, organization, plant, department, 
                created_at, updated_at, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (doc_id, title, filename, user_id, org_id, plant_id, dept_id, now, now, 'UPLOADED'))
        self.conn.commit()
        return doc_id
        
    def add_version(self, document_id: str, checksum: str, size: int, mime: str, 
                    storage_path: str, chunk_count: int, vector_collection: str, 
                    model: str, user_id: str) -> str:
        cursor = self.conn.cursor()
        version_id = str(uuid.uuid4())
        now = time.time()
        
        # Unmark previous latest
        cursor.execute("UPDATE document_versions SET is_latest = 0 WHERE document_id = ?", (document_id,))
        
        # Get next version number
        cursor.execute("SELECT MAX(version_number) as max_v FROM document_versions WHERE document_id = ?", (document_id,))
        res = cursor.fetchone()
        next_v = (res['max_v'] or 0) + 1
        
        cursor.execute("""
            INSERT INTO document_versions (
                id, document_id, version_number, checksum, storage_path, collection_name,
                uploaded_by_user_id, uploaded_at, mime_type, file_size, embedding_model, chunk_count,
                vector_count, is_latest, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            version_id, document_id, next_v, checksum, storage_path, vector_collection,
            user_id, now, mime, size, model, chunk_count, chunk_count, 1, 'UPLOADED'
        ))
        
        cursor.execute("UPDATE documents SET updated_at = ? WHERE id = ?", (now, document_id))
        self.conn.commit()
        return version_id

    def list_latest_versions(self, org_id: str) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT d.id as document_id, d.filename, d.title, 
                   d.description, d.category, d.equipment, d.language, d.author,
                   v.id as version_id, v.version_number, v.status, v.file_size, v.chunk_count, v.uploaded_at as created_at
            FROM documents d
            JOIN document_versions v ON d.id = v.document_id
            WHERE v.is_latest = 1 AND d.deleted_at IS NULL AND d.organization = ?
        """, (org_id,))
        return [dict(r) for r in cursor.fetchall()]

    def soft_delete_document(self, document_id: str, user_id: str, reason: str = ""):
        cursor = self.conn.cursor()
        now = time.time()
        cursor.execute("""
            UPDATE documents 
            SET deleted_at = ?, deleted_by_user_id = ?, delete_reason = ?, status = 'DELETED' 
            WHERE id = ?
        """, (now, user_id, reason, document_id))
        cursor.execute("UPDATE document_versions SET status = 'DELETED' WHERE document_id = ?", (document_id,))
        self.conn.commit()
        
    def restore_document(self, document_id: str):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE documents 
            SET deleted_at = NULL, deleted_by_user_id = NULL, delete_reason = NULL, status = 'READY' 
            WHERE id = ?
        """, (document_id,))
        cursor.execute("UPDATE document_versions SET status = 'READY' WHERE document_id = ?", (document_id,))
        self.conn.commit()
        
    def check_duplicate_checksum(self, checksum: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT v.id FROM document_versions v
            JOIN documents d ON v.document_id = d.id
            WHERE v.checksum = ? AND d.deleted_at IS NULL LIMIT 1
        """, (checksum,))
        return cursor.fetchone() is not None

class AuditRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        
    def log(self, action: str, resource: str, status: str, user_id: str, endpoint: str = 'SYSTEM', execution_time_ms: int = 0):
        cursor = self.conn.cursor()
        log_id = str(uuid.uuid4())
        now = time.time()
        
        cursor.execute("""
            INSERT INTO audit_logs (
                id, user_id, endpoint, action, resource, status, ip_address, execution_time_ms, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (log_id, user_id, endpoint, action, resource, status, '127.0.0.1', execution_time_ms, now, now))
        self.conn.commit()

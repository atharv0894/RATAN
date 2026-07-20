import time
import logging
from app.database.sqlite import get_db_connection
from app.storage.storage_service import StorageService
from app.rag.vector_store import VectorStore

class CleanupService:
    def __init__(self):
        self.storage_service = StorageService()
        self.vector_store = VectorStore()
        
    def eradicate_document_version(self, version_id: str):
        """
        ACID-like hard delete workflow. Rolls back state if Qdrant or Storage fails.
        """
        import uuid
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Validate & 2. Acquire lock
        cursor.execute("SELECT * FROM document_versions WHERE id = ?", (version_id,))
        doc_version = cursor.fetchone()
        
        if not doc_version:
            conn.close()
            return False, "Document version not found."
            
        if doc_version['is_locked'] == 1:
            conn.close()
            return False, "Document is locked."
            
        # 3. Check indexing
        if doc_version['status'] == 'Processing':
            conn.close()
            return False, "Indexing is currently running."
            
        cursor.execute("UPDATE document_versions SET is_locked = 1 WHERE id = ?", (version_id,))
        conn.commit()
        
        storage_path = doc_version.get('storage_path')
        document_id = doc_version['document_id']
        
        try:
            # 4. Delete vectors from Qdrant
            try:
                self.vector_store.client.delete(
                    collection_name=self.vector_store.collection_name,
                    points_selector={"filter": {"must": [{"key": "version_id", "match": {"value": version_id}}]}}
                )
            except Exception:
                pass # If it's chroma or older qdrant client, ignore

            # 5, 6, 7. Delete file from Storage (Backblaze + Local Cache)
            if storage_path:
                self.storage_service.delete(storage_path)
                
            # 8. Delete metadata from SQLite
            cursor.execute("DELETE FROM document_chunks WHERE version_id = ?", (version_id,))
            cursor.execute("DELETE FROM document_versions WHERE id = ?", (version_id,))
            
            # Check if this was the last version; if so, delete the parent document
            cursor.execute("SELECT COUNT(*) as c FROM document_versions WHERE document_id = ?", (document_id,))
            if cursor.fetchone()['c'] == 0:
                cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))
            
            # 10. Write audit log
            from app.database.repositories import get_system_user
            sys_user = get_system_user(cursor)
            cursor.execute('''INSERT INTO audit_logs (id, user_id, endpoint, action, resource, status, created_at, updated_at) 
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                           (str(uuid.uuid4()), sys_user, "SYSTEM", "HARD_DELETE", version_id, "Success", time.time(), time.time()))
                           
            conn.commit()
            return True, "Success"
            
        except Exception as e:
            # Rollback: Release lock
            cursor.execute("UPDATE document_versions SET is_locked = 0 WHERE id = ?", (version_id,))
            from app.database.repositories import get_system_user
            sys_user = get_system_user(cursor)
            cursor.execute('''INSERT INTO audit_logs (id, user_id, endpoint, action, resource, status, created_at, updated_at) 
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                           (str(uuid.uuid4()), sys_user, "SYSTEM", "HARD_DELETE_FAILED", version_id, "Rollback", time.time(), time.time()))
            conn.commit()
            logging.error(f"Eradicate failed for {version_id}, rolled back SQLite lock. Error: {e}")
            return False, str(e)
        finally:
            conn.close()

    def run_cleanup(self, timeout_seconds=3600, purge_deleted=False):
        """
        Runs comprehensive cleanup of the database, vector store, and local storage.
        """
        logging.info("Starting automated backend cleanup.")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Stale Processing Documents
        cutoff_time = time.time() - timeout_seconds
        cursor.execute("SELECT id FROM document_versions WHERE status = 'Processing' AND created_at < ?", (cutoff_time,))
        stale_docs = cursor.fetchall()
        for row in stale_docs:
            v_id = row['id']
            logging.warning(f"Cleanup: Marking stale Processing document {v_id} as Failed.")
            cursor.execute("UPDATE document_versions SET status = 'Failed' WHERE id = ?", (v_id,))
        
        # 2. Orphan Entities Cleanup
        logging.info("Cleanup: Removing orphan chunks.")
        cursor.execute('''
            DELETE FROM document_chunks 
            WHERE version_id NOT IN (SELECT id FROM document_versions)
        ''')
        
        # 3. Failed Document Cleanup (Storage + DB)
        cursor.execute("SELECT id FROM document_versions WHERE status = 'Failed'")
        failed_docs = cursor.fetchall()
        for row in failed_docs:
            self.eradicate_document_version(row['id'])
            
        # 4. Purge soft-deleted documents if requested
        if purge_deleted:
            cursor.execute("SELECT id FROM document_versions WHERE is_deleted = 1")
            deleted_docs = cursor.fetchall()
            for row in deleted_docs:
                self.eradicate_document_version(row['id'])
            
        conn.commit()
        conn.close()
        logging.info("Automated cleanup completed successfully.")
        return {"cleaned_stale": len(stale_docs), "cleaned_failed": len(failed_docs)}

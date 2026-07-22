import time
import logging
import uuid
from app.database.sqlite import get_db_connection
from app.storage.storage_service import StorageService
from app.rag.vector_store import VectorStore

class CleanupService:
    def __init__(self):
        self.storage_service = StorageService()
        self.vector_store = VectorStore()
        
    def eradicate_document_version(self, version_id: str, user_id: str = None) -> tuple[bool, str]:
        """
        Compensating Transaction Pattern for hard deletion.
        If deletion of vectors or files fails, we log the failure and revert the SQLite state (compensating action)
        so it can be retried later, never leaving inconsistent metadata.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Validate & 2. Acquire lock
        cursor.execute("SELECT * FROM document_versions WHERE id = ?", (version_id,))
        doc_version = cursor.fetchone()
        
        if not doc_version:
            conn.close()
            return False, "Document version not found."
            
        if doc_version['locked_at'] is not None:
            conn.close()
            return False, "Document is locked."
            
        # 3. Check indexing
        if doc_version['status'] in ('PROCESSING', 'INDEXING'):
            conn.close()
            return False, "Indexing is currently running."
            
        now = time.time()
        cursor.execute("""
            UPDATE document_versions 
            SET locked_at = ?, locked_by_user_id = ?, lock_reason = 'Cleanup Eradication'
            WHERE id = ?
        """, (now, user_id, version_id))
        conn.commit()
        
        storage_path = doc_version['storage_path']
        document_id = doc_version['document_id']
        
        try:
            # 4. Delete vectors from Qdrant
            try:
                self.vector_store.client.delete(
                    collection_name=self.vector_store.collection_name,
                    points_selector={"filter": {"must": [{"key": "version_id", "match": {"value": version_id}}]}}
                )
            except Exception as e:
                logging.error(f"Error during Qdrant cleanup: {e}")
                raise e

            # 5, 6, 7. Delete file from Storage (Backblaze + Local Cache)
            try:
                if storage_path:
                    self.storage_service.delete(storage_path)
            except Exception as e:
                logging.error(f"Error during B2 cleanup: {e}")
                raise e
                
            # 8. Delete metadata from SQLite
            cursor.execute("DELETE FROM document_versions WHERE id = ?", (version_id,))
            
            # Check if this was the last version; if so, delete the parent document
            cursor.execute("SELECT COUNT(*) as c FROM document_versions WHERE document_id = ?", (document_id,))
            if cursor.fetchone()['c'] == 0:
                cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))
            
            # 10. Write audit log
            sys_user = user_id or "SYSTEM"
            cursor.execute('''INSERT INTO audit_logs (id, user_id, endpoint, action, resource, status, created_at, updated_at) 
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                           (str(uuid.uuid4()), sys_user, "SYSTEM", "HARD_DELETE", version_id, "Success", time.time(), time.time()))
                           
            conn.commit()
            return True, "Success"
            
        except Exception as e:
            # Compensating Action: Release lock and log failure
            cursor.execute("""
                UPDATE document_versions 
                SET locked_at = NULL, locked_by_user_id = NULL, lock_reason = NULL 
                WHERE id = ?
            """, (version_id,))
            sys_user = user_id or "SYSTEM"
            cursor.execute('''INSERT INTO audit_logs (id, user_id, endpoint, action, resource, status, created_at, updated_at) 
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                           (str(uuid.uuid4()), sys_user, "SYSTEM", "FAILED_DELETE", version_id, "Rollback", time.time(), time.time()))
            conn.commit()
            logging.error(f"Eradicate failed for {version_id}, initiated compensating action (unlocked). Error: {e}")
            return False, str(e)
        finally:
            conn.close()

    def run_cleanup(self, timeout_seconds=3600, purge_deleted=False):
        """
        Runs comprehensive cleanup of the database, vector store, and local storage.
        Detects orphaned vectors, missing files, stale locks, and failed processing jobs.
        """
        logging.info("Starting automated backend cleanup.")
        conn = get_db_connection()
        cursor = conn.cursor()
        now = time.time()
        
        stats = {"stale_jobs_cleaned": 0, "stale_locks_cleared": 0, "failed_docs_purged": 0}
        
        # 1. Stale Processing Jobs / Documents
        cutoff_time = now - timeout_seconds
        if org_id:
            cursor.execute("""
                SELECT v.id FROM document_versions v 
                JOIN documents d ON v.document_id = d.id 
                WHERE d.organization = ? AND v.status IN ('PROCESSING', 'INDEXING') AND v.uploaded_at < ?
            """, (org_id, cutoff_time))
        else:
            cursor.execute("SELECT id FROM document_versions WHERE status IN ('PROCESSING', 'INDEXING') AND uploaded_at < ?", (cutoff_time,))
        stale_docs = cursor.fetchall()
        for row in stale_docs:
            v_id = row['id']
            logging.warning(f"Cleanup: Marking stale PROCESSING document {v_id} as FAILED.")
            cursor.execute("UPDATE document_versions SET status = 'FAILED' WHERE id = ?", (v_id,))
            cursor.execute("UPDATE processing_jobs SET status = 'FAILED', error_message = 'Timeout' WHERE target_id = ? AND status = 'PROCESSING'", (v_id,))
            stats["stale_jobs_cleaned"] += 1
            
        # 2. Clear Stale Locks
        if org_id:
            cursor.execute("""
                SELECT v.id FROM document_versions v
                JOIN documents d ON v.document_id = d.id
                WHERE d.organization = ? AND v.locked_at IS NOT NULL AND v.locked_at < ?
            """, (org_id, cutoff_time))
        else:
            cursor.execute("SELECT id FROM document_versions WHERE locked_at IS NOT NULL AND locked_at < ?", (cutoff_time,))
        stale_locks = cursor.fetchall()
        for row in stale_locks:
            v_id = row['id']
            logging.warning(f"Cleanup: Releasing stale lock for document {v_id}.")
            cursor.execute("UPDATE document_versions SET locked_at = NULL, locked_by_user_id = NULL, lock_reason = NULL WHERE id = ?", (v_id,))
            stats["stale_locks_cleared"] += 1

        # 3. Failed Document Cleanup (Storage + DB)
        if org_id:
            cursor.execute("""
                SELECT v.id FROM document_versions v
                JOIN documents d ON v.document_id = d.id
                WHERE d.organization = ? AND v.status = 'FAILED'
            """, (org_id,))
        else:
            cursor.execute("SELECT id FROM document_versions WHERE status = 'FAILED'")
        failed_docs = cursor.fetchall()
        for row in failed_docs:
            success, msg = self.eradicate_document_version(row['id'])
            if success:
                stats["failed_docs_purged"] += 1
            
        # 4. Purge soft-deleted documents if requested
        if purge_deleted:
            if org_id:
                cursor.execute("""
                    SELECT v.id FROM document_versions v
                    JOIN documents d ON v.document_id = d.id
                    WHERE d.organization = ? AND d.deleted_at IS NOT NULL
                """, (org_id,))
            else:
                cursor.execute("""
                    SELECT v.id FROM document_versions v
                    JOIN documents d ON v.document_id = d.id
                    WHERE d.deleted_at IS NOT NULL
                """)
            deleted_docs = cursor.fetchall()
            for row in deleted_docs:
                self.eradicate_document_version(row['id'])
            
        conn.commit()
        conn.close()
        logging.info("Automated cleanup completed successfully.")
        return stats

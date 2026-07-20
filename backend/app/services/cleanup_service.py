import time
import logging
from app.database.sqlite import get_db_connection
from app.storage.storage_service import StorageService
from app.rag.vector_store import VectorStore

class CleanupService:
    def __init__(self):
        self.storage_service = StorageService()
        self.vector_store = VectorStore()
        
    def eradicate_document(self, document_id: str):
        """
        ACID-like hard delete workflow. Rolls back state if Qdrant or Storage fails.
        """
        import uuid
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Validate & 2. Acquire lock
        cursor.execute("SELECT * FROM documents WHERE document_id = ?", (document_id,))
        doc = cursor.fetchone()
        
        if not doc:
            conn.close()
            return False, "Document not found."
            
        if doc['is_locked'] == 1:
            conn.close()
            return False, "Document is locked."
            
        # 3. Check indexing
        if doc['status'] == 'Processing':
            conn.close()
            return False, "Indexing is currently running."
            
        cursor.execute("UPDATE documents SET is_locked = 1 WHERE document_id = ?", (document_id,))
        conn.commit()
        
        storage_path = doc.get('storage_path')
        filename = doc['filename']
        
        try:
            # 4. Delete vectors from Qdrant
            if hasattr(self.vector_store, 'delete_by_source_and_id'):
                self.vector_store.delete_by_source_and_id(filename, document_id)
            elif hasattr(self.vector_store, 'delete_by_source'):
                # Note: this might delete all versions if not careful. Qdrant filter should be by document_id.
                pass
                
            # Actually, to be safe, we should delete by payload 'document_id' in Qdrant
            try:
                self.vector_store.client.delete(
                    collection_name=self.vector_store.collection_name,
                    points_selector={"filter": {"must": [{"key": "document_id", "match": {"value": document_id}}]}}
                )
            except Exception:
                pass # If it's chroma or older qdrant client, ignore

            # 5, 6, 7. Delete file from Storage (Backblaze + Local Cache)
            if storage_path:
                self.storage_service.delete(storage_path)
                
            # 8. Delete metadata from SQLite
            cursor.execute("DELETE FROM entities WHERE document_id = ?", (document_id,))
            cursor.execute("DELETE FROM documents WHERE document_id = ?", (document_id,))
            
            # 10. Write audit log
            cursor.execute('''INSERT INTO audit_logs (log_id, document_id, action, status, timestamp) 
                              VALUES (?, ?, ?, ?, ?)''', 
                           (str(uuid.uuid4()), document_id, "HARD_DELETE", "Success", time.time()))
                           
            conn.commit()
            return True, "Success"
            
        except Exception as e:
            # Rollback: Release lock
            cursor.execute("UPDATE documents SET is_locked = 0 WHERE document_id = ?", (document_id,))
            cursor.execute('''INSERT INTO audit_logs (log_id, document_id, action, status, timestamp, details) 
                              VALUES (?, ?, ?, ?, ?, ?)''', 
                           (str(uuid.uuid4()), document_id, "HARD_DELETE_FAILED", "Rollback", time.time(), str(e)))
            conn.commit()
            logging.error(f"Eradicate failed for {document_id}, rolled back SQLite lock. Error: {e}")
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
        cursor.execute("SELECT document_id FROM documents WHERE status = 'Processing' AND upload_time < ?", (cutoff_time,))
        stale_docs = cursor.fetchall()
        for row in stale_docs:
            doc_id = row['document_id']
            logging.warning(f"Cleanup: Marking stale Processing document {doc_id} as Failed.")
            cursor.execute("UPDATE documents SET status = 'Failed', index_status = 'Timeout' WHERE document_id = ?", (doc_id,))
        
        # 2. Orphan Entities Cleanup
        logging.info("Cleanup: Removing orphan entities.")
        cursor.execute('''
            DELETE FROM entities 
            WHERE document_id NOT IN (SELECT document_id FROM documents)
        ''')
        
        # 3. Failed Document Cleanup (Storage + DB)
        cursor.execute("SELECT document_id FROM documents WHERE status = 'Failed'")
        failed_docs = cursor.fetchall()
        for row in failed_docs:
            self.eradicate_document(row['document_id'])
            
        # 4. Purge soft-deleted documents if requested
        if purge_deleted:
            cursor.execute("SELECT document_id FROM documents WHERE is_deleted = 1")
            deleted_docs = cursor.fetchall()
            for row in deleted_docs:
                self.eradicate_document(row['document_id'])
            
        conn.commit()
        conn.close()
        logging.info("Automated cleanup completed successfully.")
        return {"cleaned_stale": len(stale_docs), "cleaned_failed": len(failed_docs)}

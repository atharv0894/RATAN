import time
import logging
from app.database.sqlite import get_db_connection
from app.storage.storage_service import StorageService
from app.rag.vector_store import VectorStore

class CleanupService:
    def __init__(self):
        self.storage_service = StorageService()
        self.vector_store = VectorStore()
        
    def run_cleanup(self, timeout_seconds=3600):
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
        # SQLite cascade handles most of this if pragmas are on, but manually enforce just in case
        cursor.execute('''
            DELETE FROM entities 
            WHERE document_id NOT IN (SELECT document_id FROM documents)
        ''')
        
        # 3. Failed Document Cleanup (Storage + DB)
        cursor.execute("SELECT document_id, filename FROM documents WHERE status = 'Failed'")
        failed_docs = cursor.fetchall()
        for row in failed_docs:
            doc_id = row['document_id']
            filename = row['filename']
            logging.info(f"Cleanup: Eradicating artifacts for failed document {doc_id}.")
            
            # Remove Storage
            try:
                self.storage_service.delete(doc_id)
            except Exception as e:
                logging.error(f"Cleanup storage failed for {doc_id}: {e}")
                
            # Remove Vectors
            try:
                if hasattr(self.vector_store, 'delete_by_source'):
                    self.vector_store.delete_by_source(filename)
            except Exception as e:
                logging.error(f"Cleanup vector store failed for {filename}: {e}")
                
            # Keep DB record but mark as cleaned (or completely delete)
            # We will delete the DB record to avoid pollution
            cursor.execute("DELETE FROM documents WHERE document_id = ?", (doc_id,))
            
        conn.commit()
        conn.close()
        logging.info("Automated cleanup completed successfully.")
        return {"cleaned_stale": len(stale_docs), "cleaned_failed": len(failed_docs)}

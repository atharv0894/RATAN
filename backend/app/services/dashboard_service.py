import time
from app.database.sqlite import get_db_connection

class DashboardService:
    def _execute_scalar(self, query: str, params=()):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            if row:
                return list(row)[0]
            return 0
        finally:
            conn.close()

    def _execute_query(self, query: str, params=()):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_overview(self, org_id: str):
        return {
            "total_documents": self._execute_scalar("SELECT COUNT(*) FROM documents WHERE organization = ? AND deleted_at IS NULL", (org_id,)),
            "active_users": self._execute_scalar("SELECT COUNT(*) FROM users WHERE org_id = ? AND is_deleted = 0", (org_id,)),
            "total_chats": self._execute_scalar("SELECT COUNT(*) FROM chat_sessions s JOIN users u ON s.user_id = u.id WHERE u.org_id = ?", (org_id,)),
            "total_storage_mb": self._execute_scalar("SELECT SUM(file_size) / (1024*1024) FROM document_versions v JOIN documents d ON v.document_id = d.id WHERE d.organization = ? AND d.deleted_at IS NULL", (org_id,)) or 0
        }

    def get_document_analytics(self, org_id: str):
        return {
            "total": self._execute_scalar("SELECT COUNT(*) FROM documents WHERE organization = ? AND deleted_at IS NULL", (org_id,)),
            "by_category": self._execute_query("SELECT category, COUNT(*) as count FROM documents WHERE organization = ? AND deleted_at IS NULL GROUP BY category", (org_id,)),
            "by_department": self._execute_query("SELECT department, COUNT(*) as count FROM documents WHERE organization = ? AND deleted_at IS NULL GROUP BY department", (org_id,)),
            "by_status": self._execute_query("SELECT status, COUNT(*) as count FROM documents WHERE organization = ? AND deleted_at IS NULL GROUP BY status", (org_id,)),
            "latest_uploads": self._execute_query("SELECT title, created_at FROM documents WHERE organization = ? AND deleted_at IS NULL ORDER BY created_at DESC LIMIT 5", (org_id,))
        }

    def get_processing_analytics(self, org_id: str):
        # We assume jobs are linked to documents or versions in the target_id
        return {
            "queued": self._execute_scalar("SELECT COUNT(*) FROM processing_jobs WHERE status = 'QUEUED'"),
            "processing": self._execute_scalar("SELECT COUNT(*) FROM processing_jobs WHERE status = 'PROCESSING'"),
            "completed": self._execute_scalar("SELECT COUNT(*) FROM processing_jobs WHERE status = 'COMPLETED'"),
            "failed": self._execute_scalar("SELECT COUNT(*) FROM processing_jobs WHERE status = 'FAILED'"),
            "recent_failures": self._execute_query("SELECT target_id, error_message, updated_at FROM processing_jobs WHERE status = 'FAILED' ORDER BY updated_at DESC LIMIT 5")
        }

    def get_search_analytics(self, org_id: str):
        return {
            "total_searches": self._execute_scalar("SELECT COUNT(*) FROM audit_logs WHERE action = 'SEARCH'"),
            "avg_latency_ms": self._execute_scalar("SELECT AVG(execution_time_ms) FROM audit_logs WHERE action = 'SEARCH'") or 0,
            "recent_searches": self._execute_query("SELECT resource as query, created_at FROM audit_logs WHERE action = 'SEARCH' ORDER BY created_at DESC LIMIT 10")
        }

    def get_ai_analytics(self, org_id: str):
        return {
            "total_chats": self._execute_scalar("SELECT COUNT(*) FROM chat_sessions s JOIN users u ON s.user_id = u.id WHERE u.org_id = ?", (org_id,)),
            "total_messages": self._execute_scalar("SELECT COUNT(*) FROM chat_messages m JOIN chat_sessions s ON m.session_id = s.id JOIN users u ON s.user_id = u.id WHERE u.org_id = ?", (org_id,)),
            "avg_confidence": self._execute_scalar("SELECT AVG(confidence_score) FROM chat_messages m JOIN chat_sessions s ON m.session_id = s.id JOIN users u ON s.user_id = u.id WHERE u.org_id = ? AND m.role = 'assistant'", (org_id,)) or 0,
            "total_tokens": self._execute_scalar("SELECT SUM(tokens_used) FROM chat_messages m JOIN chat_sessions s ON m.session_id = s.id JOIN users u ON s.user_id = u.id WHERE u.org_id = ?", (org_id,)) or 0
        }

    def get_user_analytics(self, org_id: str):
        return {
            "total_users": self._execute_scalar("SELECT COUNT(*) FROM users WHERE org_id = ? AND is_deleted = 0", (org_id,)),
            "by_role": self._execute_query("SELECT r.name, COUNT(u.id) as count FROM users u JOIN roles r ON u.role_id = r.id WHERE u.org_id = ? AND u.is_deleted = 0 GROUP BY r.name", (org_id,)),
            "by_plant": self._execute_query("SELECT p.name, COUNT(u.id) as count FROM users u JOIN plants p ON u.plant_id = p.id WHERE u.org_id = ? AND u.is_deleted = 0 GROUP BY p.name", (org_id,))
        }

    def get_storage_analytics(self, org_id: str):
        return {
            "total_storage_bytes": self._execute_scalar("SELECT SUM(file_size) FROM document_versions v JOIN documents d ON v.document_id = d.id WHERE d.organization = ? AND d.deleted_at IS NULL", (org_id,)) or 0,
            "total_versions": self._execute_scalar("SELECT COUNT(*) FROM document_versions v JOIN documents d ON v.document_id = d.id WHERE d.organization = ? AND d.deleted_at IS NULL", (org_id,)),
            "total_chunks": self._execute_scalar("SELECT SUM(chunk_count) FROM document_versions v JOIN documents d ON v.document_id = d.id WHERE d.organization = ? AND d.deleted_at IS NULL", (org_id,)) or 0,
            "total_vectors": self._execute_scalar("SELECT SUM(vector_count) FROM document_versions v JOIN documents d ON v.document_id = d.id WHERE d.organization = ? AND d.deleted_at IS NULL", (org_id,)) or 0
        }

    def get_system_health(self):
        try:
            import psutil
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            uptime = time.time() - psutil.boot_time()
        except ImportError:
            cpu, mem, uptime = 0.0, 0.0, 0.0
            
        return {
            "status": "Healthy",
            "cpu_percent": cpu,
            "memory_percent": mem,
            "uptime_seconds": uptime,
            "db_size_mb": 0, # Not easily obtainable here without file ops
            "qdrant_status": "Connected",
            "b2_status": "Connected"
        }

    def get_recent_activity(self, org_id: str, limit: int = 20):
        # Fetch mixed events from audit_logs
        return self._execute_query("""
            SELECT action, resource, status, endpoint, execution_time_ms, created_at, u.full_name as user_name
            FROM audit_logs a
            LEFT JOIN users u ON a.user_id = u.id
            WHERE u.org_id = ? OR a.user_id IS NULL
            ORDER BY a.created_at DESC LIMIT ?
        """, (org_id, limit))

    def get_alerts(self, org_id: str):
        alerts = []
        # Check processing failures
        failed_jobs = self._execute_scalar("SELECT COUNT(*) FROM processing_jobs WHERE status = 'FAILED' AND updated_at > ?", (time.time() - 86400,))
        if failed_jobs > 5:
            alerts.append({"severity": "High", "message": f"{failed_jobs} processing jobs failed in the last 24 hours."})
            
        # Check cleanup failures
        # Check system health
        try:
            import psutil
            if psutil.cpu_percent() > 90:
                alerts.append({"severity": "Critical", "message": "CPU Usage exceeds 90%"})
            if psutil.virtual_memory().percent > 90:
                alerts.append({"severity": "Critical", "message": "Memory Usage exceeds 90%"})
        except ImportError:
            pass
            
        return alerts

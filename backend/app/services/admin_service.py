import uuid
import time
from typing import List, Dict, Any
from app.database.sqlite import get_db_connection
from app.exceptions import NotFoundError, DuplicateResourceError
from app.services.dashboard_service import DashboardService

class AdminService:
    # -----------------------------
    # ORGANIZATIONS
    # -----------------------------
    @staticmethod
    def get_organizations(skip: int = 0, limit: int = 50, org_id: str = None) -> List[dict]:
        conn = get_db_connection()
        cursor = conn.cursor()
        if org_id:
            cursor.execute("SELECT * FROM organizations WHERE id = ? AND is_deleted = 0", (org_id,))
        else:
            cursor.execute("SELECT * FROM organizations WHERE is_deleted = 0 ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, skip))
        orgs = cursor.fetchall()
        conn.close()
        return [dict(o) for o in orgs]

    @staticmethod
    def create_organization(data: dict) -> dict:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM organizations WHERE name = ?", (data["name"],))
        if cursor.fetchone():
            conn.close()
            raise DuplicateResourceError("Organization", data["name"])
            
        org_id = str(uuid.uuid4())
        now = time.time()
        cursor.execute(
            "INSERT INTO organizations (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (org_id, data["name"], now, now)
        )
        conn.commit()
        conn.close()
        
        return {"id": org_id, "name": data["name"], "status": "Active"}

    @staticmethod
    def update_organization(org_id: str, data: dict) -> dict:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = time.time()
        
        fields, values = [], []
        if "name" in data:
            fields.append("name = ?")
            values.append(data["name"])
        if "status" in data:
            fields.append("status = ?")
            values.append(data["status"])
            
        if fields:
            fields.append("updated_at = ?")
            values.append(now)
            values.append(org_id)
            cursor.execute(f"UPDATE organizations SET {', '.join(fields)} WHERE id = ? AND is_deleted = 0", values)
            if cursor.rowcount == 0:
                conn.close()
                raise NotFoundError("Organization", org_id)
            conn.commit()
            
        cursor.execute("SELECT * FROM organizations WHERE id = ?", (org_id,))
        org = cursor.fetchone()
        conn.close()
        return dict(org)

    @staticmethod
    def delete_organization(org_id: str):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE organizations SET is_deleted = 1, status = 'Deleted', updated_at = ? WHERE id = ?", (time.time(), org_id))
        if cursor.rowcount == 0:
            conn.close()
            raise NotFoundError("Organization", org_id)
        conn.commit()
        conn.close()

    # -----------------------------
    # USERS (Global)
    # -----------------------------
    @staticmethod
    def get_all_users(skip: int = 0, limit: int = 50) -> List[dict]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.email, u.full_name, u.status, o.name as org_name, r.name as role
            FROM users u
            JOIN organizations o ON u.org_id = o.id
            JOIN roles r ON u.role_id = r.id
            WHERE u.is_deleted = 0
            ORDER BY u.created_at DESC LIMIT ? OFFSET ?
        """, (limit, skip))
        users = cursor.fetchall()
        conn.close()
        return [dict(u) for u in users]

    @staticmethod
    def update_global_user(user_id: str, data: dict) -> dict:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        fields, values = [], []
        for k in ["full_name", "status", "role_id", "plant_id", "department_id"]:
            if k in data and data[k] is not None:
                fields.append(f"{k} = ?")
                values.append(data[k])
                
        if fields:
            fields.append("updated_at = ?")
            values.extend([time.time(), user_id])
            cursor.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ? AND is_deleted = 0", values)
            if cursor.rowcount == 0:
                conn.close()
                raise NotFoundError("User", user_id)
            conn.commit()
            
        cursor.execute("SELECT id, email, full_name, status FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        return dict(user)

    @staticmethod
    def global_delete_user(user_id: str):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_deleted = 1, status = 'Deleted', updated_at = ? WHERE id = ?", (time.time(), user_id))
        if cursor.rowcount == 0:
            conn.close()
            raise NotFoundError("User", user_id)
        cursor.execute("UPDATE user_sessions SET is_revoked = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

    # -----------------------------
    # ROLES
    # -----------------------------
    @staticmethod
    def get_roles() -> List[dict]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, permissions FROM roles WHERE is_deleted = 0")
        roles = cursor.fetchall()
        conn.close()
        
        # Parse permissions if stored as JSON string; assuming comma-separated for now
        res = []
        for r in roles:
            d = dict(r)
            d["permissions"] = d["permissions"].split(",") if d["permissions"] else []
            res.append(d)
        return res

    @staticmethod
    def create_role(data: dict) -> dict:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM roles WHERE name = ?", (data["name"],))
        if cursor.fetchone():
            conn.close()
            raise DuplicateResourceError("Role", data["name"])
            
        role_id = str(uuid.uuid4())
        now = time.time()
        perms = ",".join(data.get("permissions", []))
        cursor.execute(
            "INSERT INTO roles (id, name, permissions, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (role_id, data["name"], perms, now, now)
        )
        conn.commit()
        conn.close()
        return {"id": role_id, "name": data["name"], "permissions": data.get("permissions", [])}

    @staticmethod
    def update_role(role_id: str, data: dict) -> dict:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        fields, values = [], []
        if "name" in data:
            fields.append("name = ?")
            values.append(data["name"])
        if "permissions" in data:
            fields.append("permissions = ?")
            values.append(",".join(data["permissions"]))
            
        if fields:
            fields.append("updated_at = ?")
            values.extend([time.time(), role_id])
            cursor.execute(f"UPDATE roles SET {', '.join(fields)} WHERE id = ? AND is_deleted = 0", values)
            if cursor.rowcount == 0:
                conn.close()
                raise NotFoundError("Role", role_id)
            conn.commit()
            
        cursor.execute("SELECT id, name, permissions FROM roles WHERE id = ?", (role_id,))
        role = cursor.fetchone()
        conn.close()
        d = dict(role)
        d["permissions"] = d["permissions"].split(",") if d["permissions"] else []
        return d

    @staticmethod
    def delete_role(role_id: str):
        conn = get_db_connection()
        cursor = conn.cursor()
        # Verify no users have this role
        cursor.execute("SELECT id FROM users WHERE role_id = ? AND is_deleted = 0", (role_id,))
        if cursor.fetchone():
            conn.close()
            raise ValueError("Cannot delete role assigned to active users")
            
        cursor.execute("UPDATE roles SET is_deleted = 1, updated_at = ? WHERE id = ?", (time.time(), role_id))
        if cursor.rowcount == 0:
            conn.close()
            raise NotFoundError("Role", role_id)
        conn.commit()
        conn.close()

    # -----------------------------
    # SYSTEM CONFIGURATION
    # -----------------------------
    @staticmethod
    def get_settings() -> dict:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT setting_key, setting_value FROM system_settings")
        settings = cursor.fetchall()
        conn.close()
        return {s["setting_key"]: s["setting_value"] for s in settings}

    @staticmethod
    def update_settings(settings: dict) -> dict:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = time.time()
        for k, v in settings.items():
            # Upsert
            cursor.execute("SELECT id FROM system_settings WHERE setting_key = ?", (k,))
            row = cursor.fetchone()
            if row:
                cursor.execute("UPDATE system_settings SET setting_value = ?, updated_at = ? WHERE id = ?", (str(v), now, row["id"]))
            else:
                cursor.execute("INSERT INTO system_settings (id, setting_key, setting_value, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                              (str(uuid.uuid4()), k, str(v), now, now))
        conn.commit()
        conn.close()
        return AdminService.get_settings()

    # -----------------------------
    # AUDIT LOGS
    # -----------------------------
    @staticmethod
    def get_audit_logs(skip: int = 0, limit: int = 50, org_id: str = None) -> List[dict]:
        conn = get_db_connection()
        cursor = conn.cursor()
        if org_id:
            cursor.execute("""
                SELECT a.id, a.action, a.resource, a.status, a.ip_address, a.created_at, u.email as user_email
                FROM audit_logs a
                LEFT JOIN users u ON a.user_id = u.id
                WHERE u.org_id = ?
                ORDER BY a.created_at DESC LIMIT ? OFFSET ?
            """, (org_id, limit, skip))
        else:
            cursor.execute("""
                SELECT a.id, a.action, a.resource, a.status, a.ip_address, a.created_at, u.email as user_email
                FROM audit_logs a
                LEFT JOIN users u ON a.user_id = u.id
                ORDER BY a.created_at DESC LIMIT ? OFFSET ?
            """, (limit, skip))
        logs = cursor.fetchall()
        conn.close()
        return [dict(l) for l in logs]

    # -----------------------------
    # MAINTENANCE & HEALTH
    # -----------------------------
    @staticmethod
    def run_maintenance_task(task_type: str) -> dict:
        if task_type == "reindex":
            # Mock triggering background job for reindexing
            return {"status": "Started", "message": "Global reindex job queued"}
        elif task_type == "cleanup":
            return {"status": "Started", "message": "Orphaned files and metadata cleanup queued"}
        elif task_type == "repair":
            return {"status": "Started", "message": "Vector index repair queued"}
        else:
            raise ValueError(f"Unknown maintenance task: {task_type}")
            
    @staticmethod
    def get_system_health() -> dict:
        ds = DashboardService()
        return ds.get_system_health()
        
    @staticmethod
    def get_system_statistics(org_id: str = None) -> dict:
        conn = get_db_connection()
        cursor = conn.cursor()
        if org_id:
            stats = {
                "total_organizations": 1,
                "total_users": cursor.execute("SELECT COUNT(*) FROM users WHERE org_id = ? AND is_deleted=0", (org_id,)).fetchone()[0],
                "total_documents": cursor.execute("SELECT COUNT(*) FROM documents WHERE organization = ? AND deleted_at IS NULL", (org_id,)).fetchone()[0]
            }
        else:
            stats = {
                "total_organizations": cursor.execute("SELECT COUNT(*) FROM organizations WHERE is_deleted=0").fetchone()[0],
                "total_users": cursor.execute("SELECT COUNT(*) FROM users WHERE is_deleted=0").fetchone()[0],
                "total_documents": cursor.execute("SELECT COUNT(*) FROM documents WHERE deleted_at IS NULL").fetchone()[0]
            }
        conn.close()
        return stats

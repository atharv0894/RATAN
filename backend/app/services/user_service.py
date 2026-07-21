import uuid
import time
from typing import List, Optional, Dict
from app.database.sqlite import get_db_connection
from app.services.auth_service import AuthService
from app.exceptions import DuplicateResourceError, NotFoundError

class UserService:
    @staticmethod
    def get_users(org_id: str, skip: int = 0, limit: int = 50) -> List[dict]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT u.id, u.email, u.full_name, u.status, u.created_at, r.name as role, p.name as plant, d.name as department
               FROM users u
               JOIN roles r ON u.role_id = r.id
               LEFT JOIN plants p ON u.plant_id = p.id
               LEFT JOIN departments d ON u.department_id = d.id
               WHERE u.org_id = ? AND u.is_deleted = 0
               LIMIT ? OFFSET ?""",
            (org_id, limit, skip)
        )
        users = cursor.fetchall()
        conn.close()
        return [dict(u) for u in users]

    @staticmethod
    def create_user(data: dict) -> dict:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE email = ?", (data["email"],))
        if cursor.fetchone():
            conn.close()
            raise DuplicateResourceError("User", data["email"])
            
        user_id = str(uuid.uuid4())
        now = time.time()
        password_hash = AuthService.get_password_hash(data["password"])
        
        cursor.execute(
            """INSERT INTO users (id, org_id, plant_id, department_id, role_id, email, password_hash, full_name, created_at, updated_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, data["org_id"], data.get("plant_id"), data.get("department_id"), data["role_id"], data["email"], password_hash, data["full_name"], now, now)
        )
        conn.commit()
        
        # Fetch created user info
        cursor.execute(
            """SELECT u.id, u.email, u.full_name, u.status, r.name as role 
               FROM users u JOIN roles r ON u.role_id = r.id WHERE u.id = ?""", 
            (user_id,)
        )
        user = cursor.fetchone()
        conn.close()
        return dict(user)

    @staticmethod
    def update_user(user_id: str, org_id: str, update_data: dict) -> dict:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Ensure user belongs to this org
        cursor.execute("SELECT id FROM users WHERE id = ? AND org_id = ? AND is_deleted = 0", (user_id, org_id))
        if not cursor.fetchone():
            conn.close()
            raise NotFoundError("User", user_id)
            
        fields = []
        values = []
        allowed_updates = ["full_name", "status", "role_id", "plant_id", "department_id"]
        
        for k, v in update_data.items():
            if k in allowed_updates and v is not None:
                fields.append(f"{k} = ?")
                values.append(v)
                
        if fields:
            fields.append("updated_at = ?")
            values.append(time.time())
            values.append(user_id)
            query = f"UPDATE users SET {', '.join(fields)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
            
        cursor.execute(
            """SELECT u.id, u.email, u.full_name, u.status, r.name as role 
               FROM users u JOIN roles r ON u.role_id = r.id WHERE u.id = ?""", 
            (user_id,)
        )
        user = cursor.fetchone()
        conn.close()
        return dict(user)

    @staticmethod
    def delete_user(user_id: str, org_id: str):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_deleted = 1, status = 'Deleted', updated_at = ? WHERE id = ? AND org_id = ?", (time.time(), user_id, org_id))
        if cursor.rowcount == 0:
            conn.close()
            raise NotFoundError("User", user_id)
        
        # Revoke sessions
        cursor.execute("UPDATE user_sessions SET is_revoked = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

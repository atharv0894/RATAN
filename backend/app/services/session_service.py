import time
import logging
import uuid
import hashlib
from typing import Optional, List
from app.database.sqlite import get_db_connection

class SessionService:
    @staticmethod
    def create_session(user_id: str, refresh_token: str, ip_address: str, device_info: str, expires_delta_days: int = 7) -> str:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        session_id = str(uuid.uuid4())
        now = int(time.time() * 1000)
        expires_at = now + (expires_delta_days * 24 * 60 * 60 * 1000)
        
        refresh_token_hash = hashlib.sha256(refresh_token.encode('utf-8')).hexdigest()
        
        cursor.execute(
            """INSERT INTO user_sessions (id, user_id, refresh_token_hash, ip_address, device_info, expires_at, last_activity, created_at, is_revoked)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)""",
            (session_id, user_id, refresh_token_hash, ip_address, device_info, expires_at, now, now)
        )
        conn.commit()
        conn.close()
        return session_id

    @staticmethod
    def validate_and_update_refresh_token(refresh_token: str) -> Optional[dict]:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = int(time.time() * 1000)
        
        refresh_token_hash = hashlib.sha256(refresh_token.encode('utf-8')).hexdigest()
        
        cursor.execute("SELECT id, user_id, expires_at, is_revoked FROM user_sessions WHERE refresh_token_hash = ?", (refresh_token_hash,))
        session = cursor.fetchone()
        
        if not session or session["is_revoked"] or session["expires_at"] < now:
            conn.close()
            return None
            
        cursor.execute("UPDATE user_sessions SET last_activity = ? WHERE id = ?", (now, session["id"]))
        conn.commit()
        
        # Verify user is still active
        cursor.execute("SELECT status FROM users WHERE id = ?", (session["user_id"],))
        user = cursor.fetchone()
        conn.close()
        
        if not user or user["status"] != "Active":
            return None
            
        return {"session_id": session["id"], "user_id": session["user_id"]}

    @staticmethod
    def revoke_session_by_token(refresh_token: str):
        conn = get_db_connection()
        cursor = conn.cursor()
        refresh_token_hash = hashlib.sha256(refresh_token.encode('utf-8')).hexdigest()
        cursor.execute("UPDATE user_sessions SET is_revoked = 1 WHERE refresh_token_hash = ?", (refresh_token_hash,))
        conn.commit()
        conn.close()

    @staticmethod
    def revoke_all_sessions(user_id: str):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE user_sessions SET is_revoked = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

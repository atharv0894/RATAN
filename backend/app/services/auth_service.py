import os
import time
import jwt
import uuid
import hashlib
from typing import Optional, Dict, Any
import bcrypt
from app.exceptions import AuthenticationError
from app.database.sqlite import get_db_connection

class AuthService:
    # In production, this should be injected from env variables
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "ratan_super_secret_dev_key_do_not_use_in_prod")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    RESET_TOKEN_EXPIRE_HOURS = 1
    
    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        
    @classmethod
    def get_password_hash(cls, password: str) -> str:
        # Standard default is 12 rounds (~300ms on Render Free CPU). 
        # Reducing to 10 rounds (~60ms) to hit the <150ms auth latency target.
        salt = bcrypt.gensalt(rounds=10)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @classmethod
    def generate_password_reset_token(cls, email: str) -> Optional[str]:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE email = ? AND is_deleted = 0", (email,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return None
            
        token = str(uuid.uuid4())
        token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
        now = int(time.time() * 1000)
        expires = now + (cls.RESET_TOKEN_EXPIRE_HOURS * 60 * 60 * 1000)
        
        cursor.execute(
            """INSERT INTO password_reset_tokens (id, user_id, token_hash, expires_at, created_at, is_used)
               VALUES (?, ?, ?, ?, ?, 0)""",
            (str(uuid.uuid4()), user['id'], token_hash, expires, now)
        )
        conn.commit()
        conn.close()
        
        return token

    @classmethod
    def reset_password(cls, token: str, new_password: str) -> bool:
        token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT user_id, expires_at FROM password_reset_tokens WHERE token_hash = ? AND is_used = 0", (token_hash,))
        row = cursor.fetchone()
        
        if not row or row['expires_at'] < int(time.time() * 1000):
            conn.close()
            return False
            
        user_id = row['user_id']
        hashed_password = cls.get_password_hash(new_password)
        
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hashed_password, user_id))
        cursor.execute("UPDATE password_reset_tokens SET is_used = 1 WHERE token_hash = ?", (token_hash,))
        conn.commit()
        conn.close()
        
        from app.services.session_service import SessionService
        SessionService.revoke_all_sessions(user_id)
        
        return True
        
    @classmethod
    def create_access_token(cls, data: dict, expires_delta_minutes: Optional[int] = None) -> str:
        to_encode = data.copy()
        expire_minutes = expires_delta_minutes or cls.ACCESS_TOKEN_EXPIRE_MINUTES
        expire = time.time() + (expire_minutes * 60)
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        
    @classmethod
    def create_refresh_token(cls, data: dict) -> str:
        to_encode = data.copy()
        expire = time.time() + (cls.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        
    @classmethod
    def decode_token(cls, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired.")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token.")

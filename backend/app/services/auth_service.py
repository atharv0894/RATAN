import os
import time
import jwt
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from app.exceptions import AuthenticationError

class AuthService:
    # In production, this should be injected from env variables
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "ratan_super_secret_dev_key_do_not_use_in_prod")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        return cls.pwd_context.verify(plain_password, hashed_password)
        
    @classmethod
    def get_password_hash(cls, password: str) -> str:
        return cls.pwd_context.hash(password)
        
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

import uuid
import time
from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from app.services.auth_service import AuthService
from app.services.session_service import SessionService
from app.api.responses import APISuccessResponse
from app.exceptions import AuthenticationError, DuplicateResourceError
from app.database.tidb import get_tidb_connection

router = APIRouter()

class PersonalRegisterRequest(BaseModel):
    full_name: str
    email: str = Field(pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

@router.post("/register", response_model=APISuccessResponse)
def register_personal_user(payload: PersonalRegisterRequest):
    conn = get_tidb_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE email = ?", (payload.email,))
    if cursor.fetchone():
        conn.close()
        raise DuplicateResourceError("User", payload.email)
        
    user_id = str(uuid.uuid4())
    now = time.time()
    password_hash = AuthService.get_password_hash(payload.password)
    
    try:
        cursor.execute(
            """INSERT INTO users (id, account_type, email, password_hash, full_name, created_at, updated_at) 
               VALUES (?, 'PERSONAL', ?, ?, ?, ?, ?)""",
            (user_id, payload.email, password_hash, payload.full_name, now, now)
        )
        cursor.execute(
            """INSERT INTO personal_settings (id, user_id, created_at, updated_at) VALUES (?, ?, ?, ?)""",
            (str(uuid.uuid4()), user_id, now, now)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        raise e
    
    conn.close()
    return APISuccessResponse(data={"message": "Personal user created successfully."})

@router.post("/login", response_model=APISuccessResponse[TokenResponse])
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_tidb_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, password_hash, account_type, email, full_name, failed_login_attempts, locked_until 
        FROM users 
        WHERE email = ? AND account_type = 'PERSONAL' AND status = 'Active' AND is_deleted = 0
    """, (form_data.username,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        raise AuthenticationError("Incorrect email or password")
        
    now = int(time.time() * 1000)
    if user["locked_until"] and user["locked_until"] > now:
        conn.close()
        raise AuthenticationError("Account locked due to too many failed attempts.")
    
    if not AuthService.verify_password(form_data.password, user["password_hash"]):
        failed_attempts = user["failed_login_attempts"] + 1
        locked_until = now + (15 * 60 * 1000) if failed_attempts >= 5 else None
        cursor.execute("UPDATE users SET failed_login_attempts = ?, locked_until = ? WHERE id = ?", (failed_attempts, locked_until, user["id"]))
        conn.commit()
        conn.close()
        raise AuthenticationError("Incorrect email or password")
        
    cursor.execute("UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE id = ?", (user["id"],))
    conn.commit()
    conn.close()
        
    payload = {
        "sub": user["id"],
        "account_type": "PERSONAL",
        "email": user["email"],
        "full_name": user["full_name"],
        "org_id": None,
        "plant_id": None,
        "department_id": None,
        "role": None
    }
        
    access_token = AuthService.create_access_token(data=payload)
    refresh_token = AuthService.create_refresh_token(data={"sub": user["id"]})
    
    ip_addr = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    SessionService.create_session(user["id"], refresh_token, ip_addr, user_agent)
    
    return APISuccessResponse(data=TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    ))

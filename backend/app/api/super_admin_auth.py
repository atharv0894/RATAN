import uuid
import time
from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from app.services.auth_service import AuthService
from app.services.session_service import SessionService
from app.api.responses import APISuccessResponse
from app.exceptions import AuthenticationError
from app.database.tidb import get_tidb_connection

router = APIRouter()

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=APISuccessResponse[TokenResponse])
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_tidb_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.password_hash, u.account_type, u.email, u.full_name, u.failed_login_attempts, u.locked_until, r.name as role 
        FROM users u 
        LEFT JOIN roles r ON u.role_id = r.id 
        WHERE u.email = ? AND u.account_type = 'SUPER_ADMIN' AND u.status = 'Active' AND u.is_deleted = 0
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
        "account_type": "SUPER_ADMIN",
        "email": user["email"],
        "full_name": user["full_name"],
        "org_id": None,
        "plant_id": None,
        "department_id": None,
        "role": "SuperAdmin"
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

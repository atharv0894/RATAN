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

class EnterpriseRegisterRequest(BaseModel):
    org_name: str
    admin_email: str = Field(pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    admin_password: str
    admin_name: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

@router.post("/register", response_model=APISuccessResponse)
def register_organization(payload: EnterpriseRegisterRequest):
    conn = get_tidb_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM organizations WHERE name = ?", (payload.org_name,))
    if cursor.fetchone():
        conn.close()
        raise DuplicateResourceError("Organization", payload.org_name)
        
    cursor.execute("SELECT id FROM users WHERE email = ?", (payload.admin_email,))
    if cursor.fetchone():
        conn.close()
        raise DuplicateResourceError("User", payload.admin_email)
        
    org_id = str(uuid.uuid4())
    admin_id = str(uuid.uuid4())
    now = time.time()
    password_hash = AuthService.get_password_hash(payload.admin_password)
    
    try:
        cursor.execute(
            "INSERT INTO organizations (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (org_id, payload.org_name, now, now)
        )
        cursor.execute("SELECT id FROM roles WHERE name = 'Admin'")
        role_row = cursor.fetchone()
        if not role_row:
            role_id = str(uuid.uuid4())
            cursor.execute("INSERT INTO roles (id, name, permissions, created_at, updated_at) VALUES (?, 'Admin', '*', ?, ?)", (role_id, now, now))
        else:
            role_id = role_row["id"]
            
        cursor.execute(
            """INSERT INTO users (id, account_type, org_id, role_id, email, password_hash, full_name, created_at, updated_at) 
               VALUES (?, 'ORGANIZATION', ?, ?, ?, ?, ?, ?, ?)""",
            (admin_id, org_id, role_id, payload.admin_email, password_hash, payload.admin_name, now, now)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        raise e
    
    conn.close()
    return APISuccessResponse(data={"message": "Organization and Admin created successfully."})

@router.post("/login", response_model=APISuccessResponse[TokenResponse])
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_tidb_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.password_hash, u.account_type, u.org_id, u.plant_id, u.department_id, u.email, u.full_name, u.failed_login_attempts, u.locked_until, r.name as role 
        FROM users u 
        LEFT JOIN roles r ON u.role_id = r.id 
        WHERE u.email = ? AND u.account_type = 'ORGANIZATION' AND u.status = 'Active' AND u.is_deleted = 0
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
        "account_type": "ORGANIZATION",
        "org_id": user["org_id"],
        "plant_id": user["plant_id"],
        "department_id": user["department_id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user["role"]
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

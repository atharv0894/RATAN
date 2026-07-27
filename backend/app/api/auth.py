import uuid
import time
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, Request
# pyrefly: ignore [missing-import]
from fastapi.security import OAuth2PasswordRequestForm
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from app.services.auth_service import AuthService
from app.services.session_service import SessionService
from app.api.responses import APISuccessResponse
from app.exceptions import AuthenticationError, DuplicateResourceError, ValidationError
from app.database.sqlite import get_db_connection
from app.services.dependencies import get_current_user

router = APIRouter()

class OrgRegisterRequest(BaseModel):
    org_name: str
    admin_email: str = Field(pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    admin_password: str
    admin_name: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str

class ForgotPasswordRequest(BaseModel):
    email: str = Field(pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@router.post("/register", response_model=APISuccessResponse)
def register_organization(payload: OrgRegisterRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if org or email exists
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
        # Create Org
        cursor.execute(
            "INSERT INTO organizations (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (org_id, payload.org_name, now, now)
        )
        # Fetch 'Admin' role ID
        cursor.execute("SELECT id FROM roles WHERE name = 'Admin'")
        role_row = cursor.fetchone()
        if not role_row:
            # Seed roles if empty
            role_id = str(uuid.uuid4())
            cursor.execute("INSERT INTO roles (id, name, permissions, created_at, updated_at) VALUES (?, 'Admin', '*', ?, ?)", (role_id, now, now))
        else:
            role_id = role_row["id"]
            
        # Create User
        cursor.execute(
            """INSERT INTO users (id, org_id, role_id, email, password_hash, full_name, created_at, updated_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
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
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.password_hash, u.org_id, u.plant_id, u.department_id, u.email, u.full_name, u.failed_login_attempts, u.locked_until, r.name as role 
        FROM users u 
        LEFT JOIN roles r ON u.role_id = r.id 
        WHERE u.email = ? AND u.status = 'Active' AND u.is_deleted = 0
    """, (form_data.username,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        raise AuthenticationError("Incorrect email or password")
        
    now = int(time.time() * 1000)
    if user["locked_until"] and user["locked_until"] > now:
        conn.close()
        raise AuthenticationError("Account locked due to too many failed attempts. Try again later.")
    
    if not AuthService.verify_password(form_data.password, user["password_hash"]):
        failed_attempts = user["failed_login_attempts"] + 1
        locked_until = now + (15 * 60 * 1000) if failed_attempts >= 5 else None
        cursor.execute("UPDATE users SET failed_login_attempts = ?, locked_until = ? WHERE id = ?", (failed_attempts, locked_until, user["id"]))
        conn.commit()
        conn.close()
        raise AuthenticationError("Incorrect email or password")
        
    # Reset lockouts on successful login
    cursor.execute("UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE id = ?", (user["id"],))
    conn.commit()
    conn.close()
        
    payload = {
        "sub": user["id"],
        "org_id": user["org_id"],
        "plant_id": user["plant_id"],
        "department_id": user["department_id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user["role"]
    }
        
    access_token = AuthService.create_access_token(data=payload)
    refresh_token = AuthService.create_refresh_token(data={"sub": user["id"]})
    
    # Store session
    ip_addr = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    SessionService.create_session(user["id"], refresh_token, ip_addr, user_agent)
    
    return APISuccessResponse(data=TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    ))

@router.post("/refresh", response_model=APISuccessResponse[TokenResponse])
def refresh(payload: RefreshRequest):
    session = SessionService.validate_and_update_refresh_token(payload.refresh_token)
    if not session:
        raise AuthenticationError("Invalid or expired refresh token.")
        
    # Rotate token
    SessionService.revoke_session_by_token(payload.refresh_token)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.org_id, u.plant_id, u.department_id, u.email, u.full_name, r.name as role 
        FROM users u 
        LEFT JOIN roles r ON u.role_id = r.id 
        WHERE u.id = ? AND u.status = 'Active'
    """, (session["user_id"],))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise AuthenticationError("User is no longer active.")
        
    payload = {
        "sub": user["id"],
        "org_id": user["org_id"],
        "plant_id": user["plant_id"],
        "department_id": user["department_id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user["role"]
    }
    
    access_token = AuthService.create_access_token(data=payload)
    new_refresh_token = AuthService.create_refresh_token(data={"sub": session["user_id"]})
    
    SessionService.create_session(session["user_id"], new_refresh_token, "rotated", "rotated")
    
    return APISuccessResponse(data=TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token
    ))

@router.post("/logout", response_model=APISuccessResponse)
def logout(payload: RefreshRequest):
    SessionService.revoke_session_by_token(payload.refresh_token)
    return APISuccessResponse(data={"message": "Logged out successfully"})

@router.get("/me", response_model=APISuccessResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    return APISuccessResponse(data=current_user)

@router.patch("/change-password", response_model=APISuccessResponse)
def change_password(payload: PasswordChangeRequest, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE id = ?", (current_user["id"],))
    user = cursor.fetchone()
    
    if not AuthService.verify_password(payload.old_password, user["password_hash"]):
        conn.close()
        raise ValidationError("Incorrect old password")
        
    new_hash = AuthService.get_password_hash(payload.new_password)
    cursor.execute("UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?", (new_hash, time.time(), current_user["id"]))
    conn.commit()
    conn.close()
    
    # Revoke all other sessions for security
    SessionService.revoke_all_sessions(current_user["id"])
    
    return APISuccessResponse(data={"message": "Password updated successfully. Please log in again."})

@router.post("/forgot-password", response_model=APISuccessResponse)
def forgot_password(payload: ForgotPasswordRequest):
    token = AuthService.generate_password_reset_token(payload.email)
    if token:
        pass # In a real app, send email here. For now, we simulate success.
        
    return APISuccessResponse(data={"message": "If an account with that email exists, a password reset link has been sent."})

@router.post("/reset-password", response_model=APISuccessResponse)
def reset_password(payload: ResetPasswordRequest):
    success = AuthService.reset_password(payload.token, payload.new_password)
    
    if not success:
        raise ValidationError("Invalid or expired password reset token.")
        
    return APISuccessResponse(data={"message": "Password reset successfully. You may now log in."})


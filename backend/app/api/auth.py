import uuid
import time
from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
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
    cursor.execute("SELECT id, password_hash FROM users WHERE email = ? AND status = 'Active'", (form_data.username,))
    user = cursor.fetchone()
    conn.close()
    
    if not user or not AuthService.verify_password(form_data.password, user["password_hash"]):
        raise AuthenticationError("Incorrect email or password")
        
    access_token = AuthService.create_access_token(data={"sub": user["id"]})
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
    
    access_token = AuthService.create_access_token(data={"sub": session["user_id"]})
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
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ? AND status = 'Active'", (payload.email,))
    user = cursor.fetchone()
    
    if user:
        reset_token = str(uuid.uuid4())
        expires_at = time.time() + 3600  # 1 hour
        cursor.execute(
            """INSERT INTO password_reset_tokens (id, user_id, token, expires_at, created_at) 
               VALUES (?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), user["id"], reset_token, expires_at, time.time())
        )
        conn.commit()
        # In a real app, send email here. For now, we simulate success.
        
    conn.close()
    return APISuccessResponse(data={"message": "If an account with that email exists, a password reset link has been sent."})

@router.post("/reset-password", response_model=APISuccessResponse)
def reset_password(payload: ResetPasswordRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = time.time()
    
    cursor.execute(
        "SELECT id, user_id FROM password_reset_tokens WHERE token = ? AND is_used = 0 AND expires_at > ?",
        (payload.token, now)
    )
    token_record = cursor.fetchone()
    
    if not token_record:
        conn.close()
        raise ValidationError("Invalid or expired password reset token.")
        
    new_hash = AuthService.get_password_hash(payload.new_password)
    
    # Update password and invalidate token
    cursor.execute("UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?", (new_hash, now, token_record["user_id"]))
    cursor.execute("UPDATE password_reset_tokens SET is_used = 1 WHERE id = ?", (token_record["id"],))
    conn.commit()
    conn.close()
    
    # Revoke all existing sessions
    SessionService.revoke_all_sessions(token_record["user_id"])
    
    return APISuccessResponse(data={"message": "Password reset successfully. You may now log in."})


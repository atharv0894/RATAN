import uuid
import time
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from app.services.auth_service import AuthService
from app.api.responses import APISuccessResponse, APIErrorDetail
from app.exceptions import AuthenticationError, DuplicateResourceError
from app.database.sqlite import get_db
from app.services.dependencies import get_current_user

router = APIRouter()

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    org_id: str
    role_id: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    org_id: str
    role: str

@router.post("/register", response_model=APISuccessResponse[UserResponse])
def register(payload: UserRegisterRequest, db=Depends(get_db)):
    cursor = db.cursor()
    
    # Check if email exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (payload.email,))
    if cursor.fetchone():
        raise DuplicateResourceError("User", payload.email)
        
    user_id = str(uuid.uuid4())
    password_hash = AuthService.get_password_hash(payload.password)
    now = time.time()
    
    try:
        cursor.execute(
            """INSERT INTO users (id, org_id, role_id, email, password_hash, full_name, created_at, updated_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, payload.org_id, payload.role_id, payload.email, password_hash, payload.full_name, now, now)
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
        
    # Fetch role name
    cursor.execute("SELECT name FROM roles WHERE id = ?", (payload.role_id,))
    role_row = cursor.fetchone()
    role_name = role_row["name"] if role_row else "User"
    
    user_data = UserResponse(
        id=user_id,
        email=payload.email,
        full_name=payload.full_name,
        org_id=payload.org_id,
        role=role_name
    )
    
    return APISuccessResponse(data=user_data)

@router.post("/login", response_model=APISuccessResponse[TokenResponse])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, password_hash FROM users WHERE email = ? AND status = 'Active'", (form_data.username,))
    user = cursor.fetchone()
    
    if not user or not AuthService.verify_password(form_data.password, user["password_hash"]):
        raise AuthenticationError("Incorrect email or password")
        
    access_token = AuthService.create_access_token(data={"sub": user["id"]})
    refresh_token = AuthService.create_refresh_token(data={"sub": user["id"]})
    
    return APISuccessResponse(data=TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    ))

@router.get("/me", response_model=APISuccessResponse[UserResponse])
def get_me(current_user: dict = Depends(get_current_user)):
    return APISuccessResponse(data=UserResponse(**current_user))

from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from app.services.user_service import UserService
from app.api.responses import APISuccessResponse, APIPaginatedResponse, PaginatedMeta
from app.services.dependencies import get_current_user, RequireRole

router = APIRouter()

class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role_id: str
    plant_id: Optional[str] = None
    department_id: Optional[str] = None

class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    status: Optional[str] = None
    role_id: Optional[str] = None
    plant_id: Optional[str] = None
    department_id: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    status: str
    role: str
    plant: Optional[str] = None
    department: Optional[str] = None

@router.get("", response_model=APIPaginatedResponse[UserResponse])
def get_users(
    skip: int = 0, 
    limit: int = 50, 
    current_user: dict = Depends(RequireRole(["Admin", "Plant Manager"]))
):
    users = UserService.get_users(current_user["org_id"], skip, limit)
    
    # Very simplistic pagination mapping for response
    meta = PaginatedMeta(page=(skip // limit) + 1, limit=limit, total=len(users), total_pages=1)
    
    return APIPaginatedResponse(data=[UserResponse(**u) for u in users], meta=meta)

@router.post("", response_model=APISuccessResponse[UserResponse])
def create_user(
    payload: UserCreateRequest, 
    current_user: dict = Depends(RequireRole(["Admin"]))
):
    data = payload.dict()
    data["org_id"] = current_user["org_id"]
    
    user = UserService.create_user(data)
    return APISuccessResponse(data=UserResponse(**user))

@router.patch("/{user_id}", response_model=APISuccessResponse[UserResponse])
def update_user(
    user_id: str, 
    payload: UserUpdateRequest, 
    current_user: dict = Depends(RequireRole(["Admin", "Plant Manager"]))
):
    user = UserService.update_user(user_id, current_user["org_id"], payload.dict(exclude_unset=True))
    return APISuccessResponse(data=UserResponse(**user))

@router.delete("/{user_id}", response_model=APISuccessResponse)
def delete_user(
    user_id: str, 
    current_user: dict = Depends(RequireRole(["Admin"]))
):
    UserService.delete_user(user_id, current_user["org_id"])
    return APISuccessResponse(data={"message": "User successfully deleted"})

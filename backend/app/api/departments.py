from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.organization_service import OrganizationService
from app.api.responses import APISuccessResponse
from app.services.dependencies import get_current_user, RequireRole

router = APIRouter()

class DepartmentCreateRequest(BaseModel):
    plant_id: str
    name: str

class DepartmentResponse(BaseModel):
    id: str
    plant_id: str
    name: str
    status: str

@router.get("", response_model=APISuccessResponse[List[DepartmentResponse]])
def get_departments(
    plant_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    deps = OrganizationService.get_departments(current_user["org_id"], plant_id)
    return APISuccessResponse(data=[DepartmentResponse(**d) for d in deps])

@router.post("", response_model=APISuccessResponse[DepartmentResponse])
def create_department(
    payload: DepartmentCreateRequest,
    current_user: dict = Depends(RequireRole(["Admin", "Plant Manager"]))
):
    dep = OrganizationService.create_department(current_user["org_id"], payload.dict())
    return APISuccessResponse(data=DepartmentResponse(**dep))

@router.delete("/{department_id}", response_model=APISuccessResponse)
def delete_department(
    department_id: str,
    current_user: dict = Depends(RequireRole(["Admin", "Plant Manager"]))
):
    OrganizationService.delete_department(current_user["org_id"], department_id)
    return APISuccessResponse(data={"message": "Department deleted successfully"})

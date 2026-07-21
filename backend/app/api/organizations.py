from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.organization_service import OrganizationService
from app.api.responses import APISuccessResponse
from app.services.dependencies import get_current_user, RequireRole

router = APIRouter()

class OrgUpdateRequest(BaseModel):
    name: str

class OrgResponse(BaseModel):
    id: str
    name: str
    status: str

@router.get("/me", response_model=APISuccessResponse[OrgResponse])
def get_my_organization(current_user: dict = Depends(get_current_user)):
    org = OrganizationService.get_organization(current_user["org_id"])
    return APISuccessResponse(data=OrgResponse(**org))

@router.patch("/me", response_model=APISuccessResponse[OrgResponse])
def update_my_organization(
    payload: OrgUpdateRequest, 
    current_user: dict = Depends(RequireRole(["Admin"]))
):
    org = OrganizationService.update_organization(current_user["org_id"], payload.dict())
    return APISuccessResponse(data=OrgResponse(**org))

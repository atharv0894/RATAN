from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.organization_service import OrganizationService
from app.api.responses import APISuccessResponse
from app.services.dependencies import get_current_user, RequireRole

router = APIRouter()

class PlantCreateRequest(BaseModel):
    name: str
    location: Optional[str] = None

class PlantUpdateRequest(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None

class PlantResponse(BaseModel):
    id: str
    name: str
    location: str
    status: str

@router.get("", response_model=APISuccessResponse[List[PlantResponse]])
def get_plants(current_user: dict = Depends(get_current_user)):
    plants = OrganizationService.get_plants(current_user["org_id"])
    return APISuccessResponse(data=[PlantResponse(**p) for p in plants])

@router.post("", response_model=APISuccessResponse[PlantResponse])
def create_plant(
    payload: PlantCreateRequest, 
    current_user: dict = Depends(RequireRole(["Admin"]))
):
    plant = OrganizationService.create_plant(current_user["org_id"], payload.dict())
    return APISuccessResponse(data=PlantResponse(**plant))

@router.patch("/{plant_id}", response_model=APISuccessResponse[PlantResponse])
def update_plant(
    plant_id: str,
    payload: PlantUpdateRequest,
    current_user: dict = Depends(RequireRole(["Admin"]))
):
    plant = OrganizationService.update_plant(current_user["org_id"], plant_id, payload.dict(exclude_unset=True))
    return APISuccessResponse(data=PlantResponse(**plant))

@router.delete("/{plant_id}", response_model=APISuccessResponse)
def delete_plant(
    plant_id: str,
    current_user: dict = Depends(RequireRole(["Admin"]))
):
    OrganizationService.delete_plant(current_user["org_id"], plant_id)
    return APISuccessResponse(data={"message": "Plant deleted successfully"})

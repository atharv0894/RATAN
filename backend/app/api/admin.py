# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends
from typing import Dict, Any, List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel
from app.api.responses import APISuccessResponse
from app.services.dependencies import get_current_user, RequireRole
from app.services.admin_service import AdminService

router = APIRouter()

def get_admin_service():
    return AdminService()

class OrgCreate(BaseModel):
    name: str
    
class RoleCreate(BaseModel):
    name: str
    permissions: List[str] = []

class OrgUpdate(BaseModel):
    name: Optional[str] = None

class UserGlobalUpdate(BaseModel):
    full_name: Optional[str] = None
    role_id: Optional[str] = None
    status: Optional[str] = None

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    permissions: Optional[List[str]] = None

@router.get("/organizations", response_model=APISuccessResponse)
def list_organizations(
    skip: int = 0, limit: int = 50,
    current_user: dict = Depends(RequireRole(["SuperAdmin", "SYSTEM_ADMIN", "Admin"])),
    service: AdminService = Depends(get_admin_service)
):
    org_id = None if current_user["role"] in ["SuperAdmin", "SYSTEM_ADMIN"] else current_user["org_id"]
    data = service.get_organizations(skip, limit, org_id)
    return APISuccessResponse(data=data)

@router.post("/organizations", response_model=APISuccessResponse)
def create_organization(
    payload: OrgCreate,
    current_user: dict = Depends(RequireRole(["SuperAdmin"])),
    service: AdminService = Depends(get_admin_service)
):
    data = service.create_organization(payload.model_dump())
    return APISuccessResponse(data=data, message="Organization created")

@router.patch("/organizations/{org_id}", response_model=APISuccessResponse)
def update_organization(
    org_id: str,
    payload: OrgUpdate,
    current_user: dict = Depends(RequireRole(["SuperAdmin"])),
    service: AdminService = Depends(get_admin_service)
):
    data = service.update_organization(org_id, payload.model_dump(exclude_unset=True))
    return APISuccessResponse(data=data, message="Organization updated")

@router.delete("/organizations/{org_id}", response_model=APISuccessResponse)
def delete_organization(
    org_id: str,
    current_user: dict = Depends(RequireRole(["SuperAdmin"])),
    service: AdminService = Depends(get_admin_service)
):
    service.delete_organization(org_id)
    return APISuccessResponse(message="Organization deleted")

@router.get("/users", response_model=APISuccessResponse)
def list_all_users(
    skip: int = 0, limit: int = 50,
    current_user: dict = Depends(RequireRole(["SuperAdmin"])),
    service: AdminService = Depends(get_admin_service)
):
    data = service.get_all_users(skip, limit)
    return APISuccessResponse(data=data)

@router.patch("/users/{user_id}", response_model=APISuccessResponse)
def update_global_user(
    user_id: str,
    payload: UserGlobalUpdate,
    current_user: dict = Depends(RequireRole(["SuperAdmin"])),
    service: AdminService = Depends(get_admin_service)
):
    data = service.update_global_user(user_id, payload.model_dump(exclude_unset=True))
    return APISuccessResponse(data=data, message="User updated")

@router.delete("/users/{user_id}", response_model=APISuccessResponse)
def delete_global_user(
    user_id: str,
    current_user: dict = Depends(RequireRole(["SuperAdmin"])),
    service: AdminService = Depends(get_admin_service)
):
    service.global_delete_user(user_id)
    return APISuccessResponse(message="User deleted")

@router.get("/roles", response_model=APISuccessResponse)
def list_roles(
    current_user: dict = Depends(RequireRole(["SuperAdmin", "Admin"])),
    service: AdminService = Depends(get_admin_service)
):
    data = service.get_roles()
    return APISuccessResponse(data=data)

@router.post("/roles", response_model=APISuccessResponse)
def create_role(
    payload: RoleCreate,
    current_user: dict = Depends(RequireRole(["SuperAdmin"])),
    service: AdminService = Depends(get_admin_service)
):
    data = service.create_role(payload.model_dump())
    return APISuccessResponse(data=data, message="Role created")

@router.patch("/roles/{role_id}", response_model=APISuccessResponse)
def update_role(
    role_id: str,
    payload: RoleUpdate,
    current_user: dict = Depends(RequireRole(["SuperAdmin"])),
    service: AdminService = Depends(get_admin_service)
):
    data = service.update_role(role_id, payload.model_dump(exclude_unset=True))
    return APISuccessResponse(data=data, message="Role updated")

@router.delete("/roles/{role_id}", response_model=APISuccessResponse)
def delete_role(
    role_id: str,
    current_user: dict = Depends(RequireRole(["SuperAdmin"])),
    service: AdminService = Depends(get_admin_service)
):
    service.delete_role(role_id)
    return APISuccessResponse(message="Role deleted")

@router.get("/settings", response_model=APISuccessResponse)
def get_settings(
    current_user: dict = Depends(RequireRole(["SuperAdmin", "Admin"])),
    service: AdminService = Depends(get_admin_service)
):
    data = service.get_settings()
    return APISuccessResponse(data=data)

@router.patch("/settings", response_model=APISuccessResponse)
def update_settings(
    settings: Dict[str, Any],
    current_user: dict = Depends(RequireRole(["SuperAdmin"])),
    service: AdminService = Depends(get_admin_service)
):
    data = service.update_settings(settings)
    return APISuccessResponse(data=data, message="Settings updated")

@router.get("/audit", response_model=APISuccessResponse)
def list_audit_logs(
    skip: int = 0, limit: int = 50,
    current_user: dict = Depends(RequireRole(["SuperAdmin", "SYSTEM_ADMIN", "Admin"])),
    service: AdminService = Depends(get_admin_service)
):
    org_id = None if current_user["role"] in ["SuperAdmin", "SYSTEM_ADMIN"] else current_user["org_id"]
    data = service.get_audit_logs(skip, limit, org_id)
    return APISuccessResponse(data=data)

@router.post("/maintenance/{task_type}", response_model=APISuccessResponse)
def run_maintenance(
    task_type: str,
    current_user: dict = Depends(RequireRole(["SuperAdmin"])),
    service: AdminService = Depends(get_admin_service)
):
    data = service.run_maintenance_task(task_type)
    return APISuccessResponse(data=data)

@router.get("/system/health", response_model=APISuccessResponse)
def system_health(
    current_user: dict = Depends(RequireRole(["SuperAdmin", "Admin"])),
    service: AdminService = Depends(get_admin_service)
):
    data = service.get_system_health()
    return APISuccessResponse(data=data)

@router.get("/system/statistics", response_model=APISuccessResponse)
def system_statistics(
    current_user: dict = Depends(RequireRole(["SuperAdmin", "SYSTEM_ADMIN", "Admin"])),
    service: AdminService = Depends(get_admin_service)
):
    org_id = None if current_user["role"] in ["SuperAdmin", "SYSTEM_ADMIN"] else current_user["org_id"]
    data = service.get_system_statistics(org_id)
    return APISuccessResponse(data=data)

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends
from typing import Dict, Any, List
from app.api.responses import APISuccessResponse
from app.services.dependencies import get_current_user, RequireRole, get_tenant_context
from app.services.dashboard_service import DashboardService

router = APIRouter()

def get_dashboard_service():
    return DashboardService()

@router.get("", response_model=APISuccessResponse)
def get_overview(
    current_user: dict = Depends(RequireRole(["Admin", "Plant Manager"])),
    tenant: dict = Depends(get_tenant_context),
    service: DashboardService = Depends(get_dashboard_service)
):
    data = service.get_overview(tenant["organization_id"])
    return APISuccessResponse(data=data)

@router.get("/documents", response_model=APISuccessResponse)
def get_documents_analytics(
    current_user: dict = Depends(RequireRole(["Admin", "Plant Manager"])),
    tenant: dict = Depends(get_tenant_context),
    service: DashboardService = Depends(get_dashboard_service)
):
    data = service.get_document_analytics(tenant["organization_id"])
    return APISuccessResponse(data=data)

@router.get("/processing", response_model=APISuccessResponse)
def get_processing_analytics(
    current_user: dict = Depends(RequireRole(["Admin", "Plant Manager"])),
    tenant: dict = Depends(get_tenant_context),
    service: DashboardService = Depends(get_dashboard_service)
):
    data = service.get_processing_analytics(tenant["organization_id"])
    return APISuccessResponse(data=data)

@router.get("/search", response_model=APISuccessResponse)
def get_search_analytics(
    current_user: dict = Depends(RequireRole(["Admin", "Plant Manager"])),
    tenant: dict = Depends(get_tenant_context),
    service: DashboardService = Depends(get_dashboard_service)
):
    data = service.get_search_analytics(tenant["organization_id"])
    return APISuccessResponse(data=data)

@router.get("/ai", response_model=APISuccessResponse)
def get_ai_analytics(
    current_user: dict = Depends(RequireRole(["Admin", "Plant Manager"])),
    tenant: dict = Depends(get_tenant_context),
    service: DashboardService = Depends(get_dashboard_service)
):
    data = service.get_ai_analytics(tenant["organization_id"])
    return APISuccessResponse(data=data)

@router.get("/users", response_model=APISuccessResponse)
def get_users_analytics(
    current_user: dict = Depends(RequireRole(["Admin", "Plant Manager"])),
    tenant: dict = Depends(get_tenant_context),
    service: DashboardService = Depends(get_dashboard_service)
):
    data = service.get_user_analytics(tenant["organization_id"])
    return APISuccessResponse(data=data)

@router.get("/storage", response_model=APISuccessResponse)
def get_storage_analytics(
    current_user: dict = Depends(RequireRole(["Admin", "Plant Manager"])),
    tenant: dict = Depends(get_tenant_context),
    service: DashboardService = Depends(get_dashboard_service)
):
    data = service.get_storage_analytics(tenant["organization_id"])
    return APISuccessResponse(data=data)

@router.get("/system", response_model=APISuccessResponse)
def get_system_health(
    current_user: dict = Depends(RequireRole(["Admin"])),
    service: DashboardService = Depends(get_dashboard_service)
):
    data = service.get_system_health()
    return APISuccessResponse(data=data)

@router.get("/activity", response_model=APISuccessResponse)
def get_recent_activity(
    limit: int = 20,
    current_user: dict = Depends(RequireRole(["Admin", "Plant Manager"])),
    tenant: dict = Depends(get_tenant_context),
    service: DashboardService = Depends(get_dashboard_service)
):
    data = service.get_recent_activity(tenant["organization_id"], limit=limit)
    return APISuccessResponse(data={"activity": data})

@router.get("/alerts", response_model=APISuccessResponse)
def get_alerts(
    current_user: dict = Depends(RequireRole(["Admin", "Plant Manager"])),
    tenant: dict = Depends(get_tenant_context),
    service: DashboardService = Depends(get_dashboard_service)
):
    data = service.get_alerts(tenant["organization_id"])
    return APISuccessResponse(data={"alerts": data})

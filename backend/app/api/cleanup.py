from fastapi import APIRouter, Depends
from app.services.cleanup_service import CleanupService
from app.api.responses import APISuccessResponse
from app.services.dependencies import RequireRole

router = APIRouter()

@router.post("", response_model=APISuccessResponse)
def run_cleanup(current_user: dict = Depends(RequireRole(["Admin", "SuperAdmin"]))):
    service = CleanupService()
    
    org_id = None if current_user.get("role") == "SuperAdmin" else current_user["org_id"]
    result = service.run_cleanup(org_id=org_id)
    return APISuccessResponse(data={"message": "Cleanup executed", "details": result})

from fastapi import APIRouter, Depends
from app.services.cleanup_service import CleanupService
from app.api.responses import APISuccessResponse
from app.services.dependencies import RequireRole

router = APIRouter()

@router.post("", response_model=APISuccessResponse)
def run_cleanup(current_user: dict = Depends(RequireRole(["Admin"]))):
    service = CleanupService()
    result = service.run_cleanup()
    return APISuccessResponse(data={"message": "Cleanup executed", "details": result})

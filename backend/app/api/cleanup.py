# pyrefly: ignore [missing-import]
from fastapi import APIRouter
from app.services.cleanup_service import CleanupService

router = APIRouter()

@router.post("")
def run_cleanup():
    service = CleanupService()
    result = service.run_cleanup()
    return {"status": "success", "details": result}

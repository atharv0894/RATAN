from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import time
from typing import List, Optional
from app.services.dependencies import get_current_user, RequireRole
from app.database.sqlite import get_db_connection
from app.api.responses import APISuccessResponse
from app.exceptions import AppException

router = APIRouter()

class SettingUpdate(BaseModel):
    setting_value: str

class SettingResponse(BaseModel):
    id: str
    setting_value: str
    description: Optional[str]
    updated_by: Optional[str]

@router.get("", response_model=APISuccessResponse)
def get_system_settings(
    current_user: dict = Depends(RequireRole(["SuperAdmin"]))
):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, setting_value, description, updated_by FROM system_settings")
        rows = cursor.fetchall()
        settings = [dict(row) for row in rows]
        return APISuccessResponse(data=settings)
    finally:
        conn.close()

@router.put("/{setting_id}", response_model=APISuccessResponse)
def update_system_setting(
    setting_id: str,
    update_data: SettingUpdate,
    current_user: dict = Depends(RequireRole(["SuperAdmin"]))
):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM system_settings WHERE id = ?", (setting_id,))
        if not cursor.fetchone():
            raise AppException(404, "NOT_FOUND", "Setting not found")
            
        cursor.execute(
            "UPDATE system_settings SET setting_value = ?, updated_by = ?, updated_at = ? WHERE id = ?",
            (update_data.setting_value, current_user["id"], time.time(), setting_id)
        )
        conn.commit()
        return APISuccessResponse(data={"id": setting_id, "setting_value": update_data.setting_value})
    finally:
        conn.close()

@router.post("/cache/flush", response_model=APISuccessResponse)
def flush_cache(
    current_user: dict = Depends(RequireRole(["SuperAdmin"]))
):
    # Mock flushing cache
    import time
    time.sleep(0.5) 
    return APISuccessResponse(data={"status": "Cache flushed successfully", "cleared_bytes": 1024 * 1024 * 150})

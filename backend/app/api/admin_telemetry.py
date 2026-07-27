import psutil
import time
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel
from app.api.responses import APISuccessResponse
from app.services.dependencies import RequireRole
from app.database.sqlite import get_db_connection
from app.rag.qdrant_store import QdrantStore
from app.services.session_service import SessionService

router = APIRouter()

class TenantToggleResponse(BaseModel):
    org_id: str
    status: str
    message: str

@router.get("/system", response_model=APISuccessResponse)
def get_system_telemetry(current_user: dict = Depends(RequireRole(["SuperAdmin"]))):
    # System RAM & CPU
    ram = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=0.1)
    
    # DB Status
    db_status = "unhealthy"
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        if cursor.fetchone():
            db_status = "healthy"
        conn.close()
    except Exception as e:
        pass

    # Qdrant Vector Count
    vector_count = 0
    try:
        store = QdrantStore()
        col_info = store.client.get_collection(store.collection_name)
        vector_count = col_info.points_count if col_info else 0
    except Exception as e:
        pass

    return APISuccessResponse(data={
        "cpu_usage_percent": cpu_percent,
        "memory_total_mb": round(ram.total / (1024 * 1024), 2),
        "memory_used_mb": round(ram.used / (1024 * 1024), 2),
        "memory_percent": ram.percent,
        "database_status": db_status,
        "qdrant_vector_count": vector_count
    })


@router.get("/tenants", response_model=APISuccessResponse)
def get_tenant_telemetry(current_user: dict = Depends(RequireRole(["SuperAdmin"]))):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT 
            o.id AS org_id,
            o.name AS org_name,
            o.status AS status,
            COUNT(DISTINCT u.id) AS active_users,
            COUNT(DISTINCT d.id) AS total_documents
        FROM organizations o
        LEFT JOIN users u ON u.org_id = o.id AND u.is_deleted = 0
        LEFT JOIN documents d ON d.organization = o.id AND d.is_deleted = 0
        WHERE o.is_deleted = 0
        GROUP BY o.id, o.name, o.status
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    # Also fetch vector counts per tenant from Qdrant if possible, but 
    # since Qdrant doesn't support group by out of the box easily, we can stick to DB document count.
    # We will just return the DB aggregations for efficiency.
    
    tenants = []
    for row in rows:
        tenants.append({
            "org_id": row["org_id"],
            "org_name": row["org_name"],
            "status": row["status"],
            "active_users": row["active_users"],
            "total_documents": row["total_documents"],
        })
        
    conn.close()
    return APISuccessResponse(data={"tenants": tenants})


@router.post("/tenants/{org_id}/toggle-status", response_model=APISuccessResponse[TenantToggleResponse])
def toggle_tenant_status(org_id: str, current_user: dict = Depends(RequireRole(["SuperAdmin"]))):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT status FROM organizations WHERE id = ? AND is_deleted = 0", (org_id,))
    org = cursor.fetchone()
    if not org:
        conn.close()
        raise HTTPException(status_code=404, detail="Organization not found")
        
    new_status = "Inactive" if org["status"] == "Active" else "Active"
    
    cursor.execute("UPDATE organizations SET status = ?, updated_at = ? WHERE id = ?", 
                   (new_status, int(time.time() * 1000), org_id))
    
    # If set to inactive, revoke all active sessions for this org
    revoked_count = 0
    if new_status == "Inactive":
        cursor.execute("SELECT id FROM users WHERE org_id = ? AND is_deleted = 0", (org_id,))
        users = cursor.fetchall()
        for u in users:
            SessionService.revoke_all_sessions(u["id"])
            revoked_count += 1
            
    conn.commit()
    conn.close()
    
    msg = f"Organization is now {new_status}."
    if new_status == "Inactive" and revoked_count > 0:
        msg += f" Revoked sessions for {revoked_count} user(s)."
        
    return APISuccessResponse(data=TenantToggleResponse(
        org_id=org_id,
        status=new_status,
        message=msg
    ))

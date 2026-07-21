from fastapi import APIRouter, Depends
from typing import List, Optional
from pydantic import BaseModel
from app.api.responses import APISuccessResponse, APIPaginatedResponse, PaginatedMeta
from app.services.dependencies import get_db_connection, RequireRole
from app.exceptions import NotFoundError

router = APIRouter()

class ProcessingJobResponse(BaseModel):
    id: str
    target_type: str
    target_id: str
    status: str
    started_at: Optional[float]
    finished_at: Optional[float]
    duration: Optional[float]
    retry_count: int
    error_message: Optional[str]
    created_at: float
    updated_at: float

@router.get("", response_model=APIPaginatedResponse[ProcessingJobResponse])
def list_jobs(
    page: int = 1,
    limit: int = 50,
    status: Optional[str] = None,
    current_user: dict = Depends(RequireRole(["Admin", "Plant Manager", "Maintenance Engineer", "Quality Engineer"]))
):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    offset = (page - 1) * limit
    
    query = "SELECT * FROM processing_jobs"
    count_query = "SELECT COUNT(*) as c FROM processing_jobs"
    params = []
    
    if status:
        query += " WHERE status = ?"
        count_query += " WHERE status = ?"
        params.append(status.upper())
        
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    
    cursor.execute(count_query, params)
    total = cursor.fetchone()['c']
    
    params.extend([limit, offset])
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    data = []
    for r in rows:
        r_dict = dict(r)
        dur = None
        if r_dict['started_at'] and r_dict['finished_at']:
            dur = r_dict['finished_at'] - r_dict['started_at']
        elif r_dict['started_at']:
            import time
            dur = time.time() - r_dict['started_at']
            
        data.append(ProcessingJobResponse(
            id=r_dict['id'],
            target_type=r_dict['target_type'],
            target_id=r_dict['target_id'],
            status=r_dict['status'],
            started_at=r_dict['started_at'],
            finished_at=r_dict['finished_at'],
            duration=dur,
            retry_count=r_dict['retry_count'],
            error_message=r_dict['error_message'],
            created_at=r_dict['created_at'],
            updated_at=r_dict['updated_at']
        ))
        
    meta = PaginatedMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=(total + limit - 1) // limit if limit > 0 else 0
    )
    return APIPaginatedResponse(data=data, meta=meta)

@router.get("/{job_id}", response_model=APISuccessResponse[ProcessingJobResponse])
def get_job(
    job_id: str,
    current_user: dict = Depends(RequireRole(["Admin", "Plant Manager", "Maintenance Engineer", "Quality Engineer"]))
):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM processing_jobs WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise NotFoundError("Processing Job", job_id)
        
    r_dict = dict(row)
    dur = None
    if r_dict['started_at'] and r_dict['finished_at']:
        dur = r_dict['finished_at'] - r_dict['started_at']
    elif r_dict['started_at']:
        import time
        dur = time.time() - r_dict['started_at']
        
    job = ProcessingJobResponse(
        id=r_dict['id'],
        target_type=r_dict['target_type'],
        target_id=r_dict['target_id'],
        status=r_dict['status'],
        started_at=r_dict['started_at'],
        finished_at=r_dict['finished_at'],
        duration=dur,
        retry_count=r_dict['retry_count'],
        error_message=r_dict['error_message'],
        created_at=r_dict['created_at'],
        updated_at=r_dict['updated_at']
    )
    return APISuccessResponse(data=job)

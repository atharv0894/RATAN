import uuid
import time
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.api.responses import APISuccessResponse
from app.services.dependencies import RequirePersonalUser, get_db_connection

router = APIRouter()

@router.get("", response_model=APISuccessResponse)
def list_personal_files(current_user: dict = Depends(RequirePersonalUser)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM personal_files 
        WHERE user_id = ? AND deleted_at IS NULL
        ORDER BY created_at DESC
    """, (current_user["id"],))
    files = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return APISuccessResponse(data={"files": files})

@router.post("", response_model=APISuccessResponse)
def upload_personal_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(RequirePersonalUser)
):
    # Dummy mock upload for architecture placeholder
    file_id = str(uuid.uuid4())
    now = time.time()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO personal_files (id, user_id, filename, storage_path, mime_type, file_size, created_at, updated_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (file_id, current_user["id"], file.filename, f"personal/{current_user['id']}/{file_id}", file.content_type, 1024, now, now))
    conn.commit()
    conn.close()
    
    return APISuccessResponse(data={"id": file_id, "filename": file.filename, "message": "File uploaded successfully."})

@router.delete("/{file_id}", response_model=APISuccessResponse)
def delete_personal_file(file_id: str, current_user: dict = Depends(RequirePersonalUser)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE personal_files SET deleted_at = ? WHERE id = ? AND user_id = ?", (time.time(), file_id, current_user["id"]))
    conn.commit()
    conn.close()
    return APISuccessResponse(data={"message": "File deleted"})

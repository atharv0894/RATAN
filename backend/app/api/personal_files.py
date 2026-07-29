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
        WHERE user_id = ? AND deleted_at IS NULL AND session_id IS NULL
        ORDER BY created_at DESC
    """, (current_user["id"],))
    files = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return APISuccessResponse(data={"files": files})

import os
from fastapi import BackgroundTasks, Form, UploadFile, File
from app.storage.storage_service import StorageService
from app.rag.parsers.factory import ParserFactory
from app.rag.chunker import Chunker
from app.rag.indexer import Indexer
from app.services.dependencies import get_embedding_service, get_vector_store
import logging

@router.post("", response_model=APISuccessResponse)
async def upload_personal_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session_id: str = Form(None),
    current_user: dict = Depends(RequirePersonalUser)
):
    file_id = str(uuid.uuid4())
    now = time.time()
    # Security: Validate file extension
    allowed_exts = (".pdf", ".docx", ".txt", ".md", ".csv")
    if not file.filename.lower().endswith(allowed_exts):
        from app.exceptions import ValidationError
        raise ValidationError(f"Unsupported file format. Allowed: {allowed_exts}")
        
    # Security: Check file size (max 50MB) to prevent disk exhaustion DoS
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > 50 * 1024 * 1024:
        from app.exceptions import ValidationError
        raise ValidationError("File too large (max 50MB)")
    
    # Security: Prevent Path Traversal (CWE-22)
    safe_filename = os.path.basename(file.filename)
    temp_path = f"/tmp/{file_id}_{safe_filename}"
    
    import shutil
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    file_size = os.path.getsize(temp_path)
    
    # Store in TiDB
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO personal_files (id, user_id, filename, storage_path, mime_type, file_size, session_id, created_at, updated_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (file_id, current_user["id"], file.filename, f"personal/{current_user['id']}/{file_id}", file.content_type, file_size, session_id, now, now))
    
    conn.commit()
    conn.close()
    
    # Background processing function
    def process_personal_file():
        try:
            parser = ParserFactory.get_parser(temp_path)
            parsed_doc = parser.parse(temp_path, filename=file.filename, use_ocr=True)
            
            chunker = Chunker(max_chars=1500, overlap_chars=200)
            chunks, metadatas, chunk_ids = [], [], []
            
            for page in parsed_doc.pages:
                base_meta = {
                    "namespace": f"personal/{current_user['id']}",
                    "filename": file.filename,
                    "page": page.page_number,
                    "document_id": file_id
                }
                
                page_chunks = chunker.chunk_page_with_metadata(page, base_meta)
                for info in page_chunks:
                    chunks.append(info['text'])
                    metadatas.append(info['metadata'])
                    chunk_ids.append(info['chunk_id'])
            
            if chunks:
                indexer = Indexer(get_embedding_service(), get_vector_store())
                indexer.index_chunks(chunks, metadatas=metadatas, chunk_ids=chunk_ids, document_id=file_id, filename=file.filename)
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE personal_files 
                SET chunk_count = ?, vector_count = ?, status = 'READY', updated_at = ?
                WHERE id = ?
            """, (len(chunks), len(chunks), time.time(), file_id))
            conn.commit()
            conn.close()
            logging.info(f"Successfully processed personal file {file.filename}")
        except Exception as e:
            logging.error(f"Failed to process personal file: {e}")
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE personal_files SET status = 'FAILED' WHERE id = ?", (file_id,))
            conn.commit()
            conn.close()
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    background_tasks.add_task(process_personal_file)
    
    return APISuccessResponse(data={"id": file_id, "filename": file.filename, "message": "File upload started."})

@router.delete("/{file_id}", response_model=APISuccessResponse)
def delete_personal_file(file_id: str, current_user: dict = Depends(RequirePersonalUser)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE personal_files SET deleted_at = ? WHERE id = ? AND user_id = ?", (time.time(), file_id, current_user["id"]))
    conn.commit()
    conn.close()
    return APISuccessResponse(data={"message": "File deleted"})

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import uuid
from app.services.dependencies import get_document_service
from app.storage.storage_service import StorageService
from app.rag.indexer import QdrantUploadError
from app.exceptions import DuplicateDocumentError

router = APIRouter()
storage_service = StorageService()

@router.post("/upload")
async def upload_documents(file: UploadFile = File(...)):
    print(f"[Upload lifecycle] Upload started for {file.filename}")
    
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Only PDF files are supported")
        
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    
    if size > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")
            
    doc_service = get_document_service()
    
    import tempfile
    import os
    import shutil
    
    # Save to temp file
    fd, temp_path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        doc_id = doc_service.process_and_index(file.filename, temp_path)
        return {
            "status": "uploaded",
            "document_id": doc_id,
            "filename": file.filename,
            "duplicate": False
        }
    except DuplicateDocumentError as e:
        return {
            "status": "already_exists",
            "document_id": e.document_id,
            "filename": file.filename,
            "indexed": True,
            "duplicate": True,
            "message": "Document already indexed. Using existing document."
        }
    except QdrantUploadError as e:
        raise HTTPException(status_code=500, detail=e.error_details)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail={"filename": file.filename, "error": str(e), "status": "Failed"})
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.get("")
def list_documents():
    doc_service = get_document_service()
    docs = doc_service.get_all_documents()
    return [
        {
            "id": d["document_id"],
            "filename": d["filename"],
            "status": d["status"],
            "size": d.get("file_size", 0),
            "pages": d.get("page_count", 0),
            "chunks": d["chunk_count"],
            "upload_date": d["upload_time"],
            "storage_provider": d.get("storage_provider", "local"),
            "version_number": d.get("version_number", 1),
            "is_latest": bool(d.get("is_latest", 1)),
            "is_deleted": bool(d.get("is_deleted", 0))
        } for d in docs
    ]

@router.get("/{document_id}")
def get_document(document_id: str):
    doc_service = get_document_service()
    doc = doc_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return {
        "id": doc["document_id"],
        "filename": doc["filename"],
        "status": doc["status"],
        "chunks": doc["chunk_count"],
        "upload_time": doc["upload_time"],
        "embedding_model": doc["embedding_model"],
        "vector_db": doc["vector_db"],
        "processing_time": doc["processing_time"],
        "storage_path": doc.get("storage_path"),
        "checksum_sha256": doc.get("checksum_sha256"),
        "version_number": doc.get("version_number", 1),
        "is_latest": bool(doc.get("is_latest", 1)),
        "is_deleted": bool(doc.get("is_deleted", 0))
    }

@router.delete("/{document_id}")
def delete_document(document_id: str):
    doc_service = get_document_service()
    try:
        success = doc_service.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": "Document soft-deleted successfully"}
    except Exception as e:
        error_msg = str(e)
        if "locked" in error_msg.lower() or "indexing is currently running" in error_msg.lower():
            raise HTTPException(status_code=409, detail=error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/{document_id}/restore")
def restore_document(document_id: str):
    doc_service = get_document_service()
    doc = doc_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if not doc.get('is_deleted'):
        return {"message": "Document is not deleted"}
        
    try:
        doc_service.restore_document(document_id)
        return {"message": "Document restored successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


import os
import uuid
import tempfile
import shutil
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends
from pydantic import BaseModel
from app.services.dependencies import get_document_service, get_current_user, RequireRole, get_tenant_context
from app.api.responses import APISuccessResponse, APIPaginatedResponse, PaginatedMeta
from app.exceptions import DuplicateDocumentError, ValidationError, NotFoundError, AppException
from app.rag.indexer import QdrantUploadError

router = APIRouter()

class DocumentResponse(BaseModel):
    id: str
    filename: str
    status: str
    chunks: int
    version_number: int
    is_latest: bool
    is_deleted: bool

@router.post("/upload", response_model=APISuccessResponse)
async def upload_documents(
    file: UploadFile = File(...),
    current_user: dict = Depends(RequireRole(["Admin", "Plant Manager", "Maintenance Engineer", "Quality Engineer"]))
):
    allowed_exts = (".pdf", ".docx", ".txt", ".md", ".csv")
    if not file.filename.lower().endswith(allowed_exts):
        raise ValidationError(f"Unsupported file format. Allowed: {allowed_exts}")
        
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    
    if size > 50 * 1024 * 1024:
        raise ValidationError("File too large (max 50MB)")
            
    doc_service = get_document_service()
    
    fd, temp_path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        doc_id = doc_service.process_and_index(file.filename, temp_path)
        return APISuccessResponse(data={
            "status": "uploaded",
            "document_id": doc_id,
            "filename": file.filename,
            "duplicate": False
        })
    except DuplicateDocumentError as e:
        return APISuccessResponse(data={
            "status": "already_exists",
            "document_id": e.document_id,
            "filename": file.filename,
            "duplicate": True,
            "message": "Document already indexed."
        })
    except QdrantUploadError as e:
        raise AppException(500, "QDRANT_ERROR", str(e.error_details))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise AppException(500, "INTERNAL_ERROR", str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.get("", response_model=APIPaginatedResponse[DocumentResponse])
def list_documents(
    page: int = 1, 
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    doc_service = get_document_service()
    docs = doc_service.get_all_documents()
    
    # In a real impl, we'd paginate at the DB level, but doing manual slicing for mock hackathon code
    start = (page - 1) * limit
    end = start + limit
    paginated_docs = docs[start:end]
    
    data = [
        DocumentResponse(
            id=d["document_id"],
            filename=d["filename"],
            status=d["status"],
            chunks=d["chunk_count"],
            version_number=d.get("version_number", 1),
            is_latest=bool(d.get("is_latest", 1)),
            is_deleted=bool(d.get("is_deleted", 0))
        ) for d in paginated_docs
    ]
    
    meta = PaginatedMeta(
        page=page,
        limit=limit,
        total=len(docs),
        total_pages=(len(docs) + limit - 1) // limit
    )
    
    return APIPaginatedResponse(data=data, meta=meta)

@router.get("/{document_id}", response_model=APISuccessResponse[DocumentResponse])
def get_document(document_id: str, current_user: dict = Depends(get_current_user)):
    doc_service = get_document_service()
    doc = doc_service.get_document(document_id)
    if not doc:
        raise NotFoundError("Document", document_id)
        
    return APISuccessResponse(data=DocumentResponse(
        id=doc["document_id"],
        filename=doc["filename"],
        status=doc["status"],
        chunks=doc["chunk_count"],
        version_number=doc.get("version_number", 1),
        is_latest=bool(doc.get("is_latest", 1)),
        is_deleted=bool(doc.get("is_deleted", 0))
    ))

@router.delete("/{document_id}", response_model=APISuccessResponse)
def delete_document(
    document_id: str,
    current_user: dict = Depends(RequireRole(["Admin", "Plant Manager"]))
):
    doc_service = get_document_service()
    try:
        success = doc_service.delete_document(document_id)
        if not success:
            raise NotFoundError("Document", document_id)
        return APISuccessResponse(data={"message": "Document soft-deleted successfully"})
    except Exception as e:
        error_msg = str(e)
        if "locked" in error_msg.lower() or "indexing is currently running" in error_msg.lower():
            raise AppException(409, "DOCUMENT_LOCKED", error_msg)
        raise AppException(500, "INTERNAL_ERROR", error_msg)

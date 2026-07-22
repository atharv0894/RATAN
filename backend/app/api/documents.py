import os
import uuid
import tempfile
import shutil
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Depends, Form, BackgroundTasks
from pydantic import BaseModel
import json
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
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    equipment: Optional[str] = None
    language: Optional[str] = None
    author: Optional[str] = None

class ChunkResponse(BaseModel):
    chunk_id: str
    text: str
    metadata: dict

@router.post("/upload", response_model=APISuccessResponse)
async def upload_documents(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    metadata: str = Form(None, description="Optional JSON string for metadata (title, description, category, equipment, language, author)"),
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
            
        meta_dict = {}
        if metadata:
            try:
                meta_dict = json.loads(metadata)
            except Exception:
                raise ValidationError("Invalid JSON format in metadata field.")
                
        doc_id = doc_service.process_and_index(
            filename=file.filename, 
            file_path=temp_path, 
            user_id=current_user["id"],
            org_id=current_user["org_id"],
            plant_id=current_user.get("plant_id") or "Unknown",
            dept_id=current_user.get("department_id") or "Unknown",
            metadata=meta_dict,
            background_tasks=background_tasks
        )
        return APISuccessResponse(data={
            "status": "UPLOADED",
            "document_id": doc_id,
            "filename": file.filename,
            "duplicate": False
        })
    except DuplicateDocumentError as e:
        return APISuccessResponse(data={
            "status": "ALREADY_EXISTS",
            "document_id": e.document_id,
            "filename": file.filename,
            "duplicate": True,
            "message": "Document checksum already exists."
        })
    except QdrantUploadError as e:
        raise AppException(500, "QDRANT_ERROR", str(e.error_details))
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Fallback cleanup if something failed before the background task was dispatched
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise AppException(500, "INTERNAL_ERROR", str(e))

@router.get("", response_model=APIPaginatedResponse[DocumentResponse])
def list_documents(
    page: int = 1, 
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    doc_service = get_document_service()
    docs = doc_service.get_all_documents(current_user["org_id"])
    
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
            title=d.get("title"),
            description=d.get("description"),
            category=d.get("category"),
            equipment=d.get("equipment"),
            language=d.get("language"),
            author=d.get("author")
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
    doc = doc_service.get_document(document_id, current_user["org_id"])
    if not doc:
        raise NotFoundError("Document", document_id)
        
    return APISuccessResponse(data=DocumentResponse(
        id=doc["document_id"],
        filename=doc["filename"],
        status=doc["status"],
        chunks=doc["chunk_count"],
        version_number=doc.get("version_number", 1),
        is_latest=bool(doc.get("is_latest", 1)),
        title=doc.get("title"),
        description=doc.get("description"),
        category=doc.get("category"),
        equipment=doc.get("equipment"),
        language=doc.get("language"),
        author=doc.get("author")
    ))

@router.get("/chunks/{chunk_id}", response_model=APISuccessResponse[ChunkResponse])
def get_document_chunk(chunk_id: str, current_user: dict = Depends(get_current_user)):
    from app.rag.vector_store import VectorStore
    vs = VectorStore()
    chunk = vs.get_by_chunk_id(chunk_id)
    if not chunk or chunk.get("metadata", {}).get("organization_id") != current_user["org_id"]:
        raise NotFoundError("Chunk", chunk_id)
    return APISuccessResponse(data=ChunkResponse(**chunk))

@router.delete("/{document_id}", response_model=APISuccessResponse)
def delete_document(
    document_id: str,
    current_user: dict = Depends(RequireRole(["Admin", "Plant Manager"]))
):
    doc_service = get_document_service()
    try:
        success = doc_service.delete_document(document_id, user_id=current_user["id"], org_id=current_user["org_id"])
        if not success:
            raise NotFoundError("Document", document_id)
        return APISuccessResponse(data={"message": "Document soft-deleted successfully."})
    except AppException:
        raise
    except Exception as e:
        error_msg = str(e)
        if "processing" in error_msg.lower() or "indexing" in error_msg.lower():
            raise AppException(409, "DOCUMENT_LOCKED", error_msg)
        raise AppException(500, "INTERNAL_ERROR", error_msg)

@router.post("/{document_id}/restore", response_model=APISuccessResponse)
def restore_document(
    document_id: str,
    current_user: dict = Depends(RequireRole(["Admin", "Plant Manager"]))
):
    doc_service = get_document_service()
    try:
        success = doc_service.restore_document(document_id, user_id=current_user["id"], org_id=current_user["org_id"])
        if not success:
            raise NotFoundError("Document", document_id)
        return APISuccessResponse(data={"message": "Document restored successfully."})
    except AppException:
        raise
    except Exception as e:
        raise AppException(409, "RESTORE_FAILED", str(e))

class MetadataUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    equipment: Optional[str] = None
    language: Optional[str] = None
    author: Optional[str] = None

@router.patch("/{document_id}", response_model=APISuccessResponse)
def update_metadata(
    document_id: str,
    request: MetadataUpdateRequest,
    current_user: dict = Depends(RequireRole(["Admin", "Plant Manager", "Maintenance Engineer", "Quality Engineer"]))
):
    doc_service = get_document_service()
    try:
        success = doc_service.update_metadata(document_id, request.dict(exclude_unset=True), user_id=current_user["id"], org_id=current_user["org_id"])
        if not success:
            raise NotFoundError("Document", document_id)
        return APISuccessResponse(data={"message": "Metadata updated successfully."})
    except AppException:
        raise
    except ValueError as e:
        raise AppException(409, "METADATA_UPDATE_FAILED", str(e))
    except Exception as e:
        raise AppException(500, "INTERNAL_ERROR", str(e))

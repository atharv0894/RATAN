# pyrefly: ignore [missing-import]
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from typing import List
import os
import uuid
from app.services.dependencies import get_document_service
from app.storage.storage_service import StorageService

router = APIRouter()
storage_service = StorageService()

@router.post("/upload")
async def upload_documents(file: List[UploadFile] = File(...)):
    print(f"[Upload lifecycle] Upload started for {len(file)} files")
    
    if len(file) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files allowed")
        
    total_size = 0
    for f in file:
        if not f.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=415, detail="Only PDF files are supported")
            
        f.file.seek(0, 2)
        size = f.file.tell()
        f.file.seek(0)
        
        if size > 50 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (max 50MB)")
            
        total_size += size
        
    if total_size > 200 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Total request too large (max 200MB)")
            
    # Process files
    results = []
    doc_service = get_document_service()
    
    for f in file:
        document_id = str(uuid.uuid4())
        # Use StorageService to save the file
        save_path = storage_service.save(f.file, document_id, f.filename)
        
        try:
            doc_id = doc_service.process_and_index(f.filename, save_path, document_id=document_id)
            results.append({"filename": f.filename, "document_id": doc_id, "status": "Indexed"})
        except ValueError as e:
            if str(e) == "DUPLICATE_CHECKSUM":
                storage_service.delete(document_id)
                results.append({"filename": f.filename, "error": "Duplicate document", "status": "Failed", "code": 409})
            else:
                storage_service.delete(document_id)
                results.append({"filename": f.filename, "error": str(e), "status": "Failed", "code": 500})
        except Exception as e:
            storage_service.delete(document_id)
            results.append({"filename": f.filename, "error": str(e), "status": "Failed", "code": 500})
            
    # Check if there were any 409s and handle how to return? The prompt says "return HTTP 409 if identical checksum". 
    # If it's a batch, we can return 409 immediately or mix. If it's single file it's easy. I'll just raise 409 if any duplicate is found for simplicity of prompt constraints, or just return it in results. Wait, "If identical checksum already exists, return HTTP 409."
    # Let's raise HTTPException 409 if the first file fails, or if any fails.
    for r in results:
        if r.get("code") == 409:
            raise HTTPException(status_code=409, detail="Duplicate document uploaded")
        if r.get("code") == 500:
            raise HTTPException(status_code=500, detail="Unexpected error during processing")
        
    return {"message": "Files successfully uploaded and indexed", "results": results}

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
            "storage_provider": d.get("storage_provider", "local")
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
        "processing_time": doc["processing_time"]
    }

@router.delete("/{document_id}")
def delete_document(document_id: str):
    doc_service = get_document_service()
    try:
        success = doc_service.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": "Document deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{document_id}/reindex")
def reindex_document(document_id: str):
    doc_service = get_document_service()
    try:
        doc_id = doc_service.reindex_document(document_id)
        if not doc_id:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": "Document reindexed successfully", "document_id": doc_id}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Original file not found in storage")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
            results.append({
                "status": "uploaded",
                "document_id": doc_id,
                "filename": f.filename,
                "duplicate": False
            })
        except DuplicateDocumentError as e:
            storage_service.delete(document_id)
            results.append({
                "status": "already_exists",
                "document_id": e.document_id,
                "filename": f.filename,
                "indexed": True,
                "duplicate": True,
                "message": "Document already indexed. Using existing document."
            })
        except QdrantUploadError as e:
            storage_service.delete(document_id)
            results.append(e.error_details)
        except Exception as e:
            import traceback
            traceback.print_exc()
            storage_service.delete(document_id)
            results.append({"filename": f.filename, "error": str(e), "status": "Failed", "code": 500})
            
    # Check if there were any 500s
    for r in results:
        if r.get("status") == "failed" and "stage" in r:
            raise HTTPException(status_code=500, detail=r)
        if r.get("code") == 500:
            raise HTTPException(status_code=500, detail="Unexpected error during processing")
        
    # Return single object if 1 file, else list (matches the requested exact response format)
    if len(results) == 1:
        return results[0]
    return results

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

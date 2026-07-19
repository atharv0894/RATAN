import os
import shutil

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

class LocalStorage:
    def __init__(self):
        pass
        
    def save(self, file_obj, document_id: str, original_filename: str) -> str:
        # Create storage layout based on document_id to avoid overwrite
        # Generating a UUID filename as requested
        ext = os.path.splitext(original_filename)[1]
        file_name = f"{document_id}{ext}"
        save_path = os.path.join(UPLOAD_DIR, file_name)
        
        # Read file_obj assuming it's a file-like object with .read()
        file_obj.seek(0)
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file_obj, buffer)
            
        return save_path

    def delete(self, document_id: str) -> bool:
        path = self.get_local_path(document_id)
        if path and os.path.exists(path):
            os.remove(path)
            return True
        return False

    def exists(self, document_id: str) -> bool:
        return self.get_local_path(document_id) is not None

    def get_local_path(self, document_id: str):
        # We need to find the file that starts with document_id
        for f in os.listdir(UPLOAD_DIR):
            if f.startswith(document_id):
                return os.path.join(UPLOAD_DIR, f)
        return None

    def get_metadata(self, document_id: str):
        path = self.get_local_path(document_id)
        if not path:
            return None
        return {
            "size": os.path.getsize(path),
            "mime_type": "application/pdf" if path.endswith(".pdf") else "application/octet-stream"
        }

    def list_documents(self):
        docs = []
        for f in os.listdir(UPLOAD_DIR):
            if os.path.isfile(os.path.join(UPLOAD_DIR, f)):
                docs.append(f)
        return docs

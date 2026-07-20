import os
import shutil

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

class LocalStorage:
    def __init__(self):
        pass
        
    def save(self, file_obj, storage_path: str) -> str:
        save_path = os.path.join(UPLOAD_DIR, storage_path)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        file_obj.seek(0)
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file_obj, buffer)
            
        return save_path

    def delete(self, storage_path: str) -> bool:
        path = os.path.join(UPLOAD_DIR, storage_path)
        if os.path.exists(path):
            os.remove(path)
            # Try to remove empty dir
            try:
                os.rmdir(os.path.dirname(path))
            except OSError:
                pass
            return True
        return False

    def exists(self, storage_path: str) -> bool:
        return os.path.exists(os.path.join(UPLOAD_DIR, storage_path))

    def get_local_path(self, storage_path: str):
        path = os.path.join(UPLOAD_DIR, storage_path)
        if os.path.exists(path):
            return path
        return None

    def get_metadata(self, storage_path: str):
        path = os.path.join(UPLOAD_DIR, storage_path)
        if not os.path.exists(path):
            return None
        return {
            "size": os.path.getsize(path),
            "mime_type": "application/pdf" if path.endswith(".pdf") else "application/octet-stream"
        }

    def list_documents(self):
        docs = []
        for root, dirs, files in os.walk(UPLOAD_DIR):
            for file in files:
                docs.append(os.path.relpath(os.path.join(root, file), UPLOAD_DIR))
        return docs

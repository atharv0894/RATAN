import os
import shutil
import tempfile
import logging
# pyrefly: ignore [missing-import]
from b2sdk.v2 import InMemoryAccountInfo, B2Api

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

class B2Storage:
    def __init__(self):
        self.key_id = os.environ.get("B2_KEY_ID")
        self.app_key = os.environ.get("B2_APPLICATION_KEY")
        self.bucket_name = os.environ.get("B2_BUCKET_NAME")
        
        if not all([self.key_id, self.app_key, self.bucket_name]):
            logging.warning("B2 credentials missing. B2 Storage initialization may fail.")
            
        info = InMemoryAccountInfo()
        self.b2_api = B2Api(info)
        
        try:
            self.b2_api.authorize_account("production", self.key_id, self.app_key)
            self.bucket = self.b2_api.get_bucket_by_name(self.bucket_name)
            logging.info(f"Successfully connected to B2 bucket: {self.bucket_name}")
        except Exception as e:
            logging.error(f"Failed to authenticate with B2: {e}")
            self.bucket = None

    def save(self, file_obj, document_id: str, original_filename: str) -> str:
        if not self.bucket:
            raise Exception("B2 bucket is not initialized.")
            
        ext = os.path.splitext(original_filename)[1]
        file_name = f"{document_id}{ext}"
        
        # Save locally first as a cache/temp
        save_path = os.path.join(UPLOAD_DIR, file_name)
        file_obj.seek(0)
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file_obj, buffer)
            
        # Upload to B2
        try:
            self.bucket.upload_local_file(
                local_file=save_path,
                file_name=file_name
            )
            logging.info(f"Uploaded {file_name} to B2.")
        except Exception as e:
            logging.error(f"Failed to upload to B2: {e}")
            raise e
            
        return save_path

    def delete(self, document_id: str) -> bool:
        if not self.bucket:
            return False
            
        file_name = self._get_filename_from_id(document_id)
        if not file_name:
            return False
            
        # Delete from local cache
        path = os.path.join(UPLOAD_DIR, file_name)
        if os.path.exists(path):
            os.remove(path)
            
        # Delete from B2
        try:
            file_version = self.bucket.get_file_info_by_name(file_name)
            self.b2_api.delete_file_version(file_version.id_, file_name)
            return True
        except Exception as e:
            logging.error(f"B2 Delete error: {e}")
            return False

    def exists(self, document_id: str) -> bool:
        return self._get_filename_from_id(document_id) is not None

    def get_local_path(self, document_id: str):
        # First check local cache
        for f in os.listdir(UPLOAD_DIR):
            if f.startswith(document_id):
                return os.path.join(UPLOAD_DIR, f)
                
        # If not local, we would need to download it from B2
        file_name = self._get_filename_from_id(document_id)
        if file_name and self.bucket:
            download_path = os.path.join(UPLOAD_DIR, file_name)
            try:
                file_download = self.bucket.download_file_by_name(file_name)
                file_download.save_to(download_path)
                return download_path
            except Exception as e:
                logging.error(f"Failed to download from B2: {e}")
                return None
        return None

    def get_metadata(self, document_id: str):
        file_name = self._get_filename_from_id(document_id)
        if not file_name or not self.bucket:
            return None
            
        try:
            file_info = self.bucket.get_file_info_by_name(file_name)
            return {
                "size": file_info.content_length,
                "mime_type": file_info.content_type
            }
        except Exception:
            return None

    def list_documents(self):
        if not self.bucket:
            return []
        docs = []
        for file_version, _ in self.bucket.ls():
            docs.append(file_version.file_name)
        return docs
        
    def _get_filename_from_id(self, document_id: str):
        # Look in local first
        for f in os.listdir(UPLOAD_DIR):
            if f.startswith(document_id):
                return f
        # Otherwise query B2 prefix
        if self.bucket:
            for file_version, _ in self.bucket.ls(folder_to_list=""):
                if file_version.file_name.startswith(document_id):
                    return file_version.file_name
        return None

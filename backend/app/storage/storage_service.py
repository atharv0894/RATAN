import os
from .local_storage import LocalStorage
from .b2_storage import B2Storage

class StorageService:
    def __init__(self):
        provider = os.environ.get("STORAGE_PROVIDER", "local").lower()
        self.provider_name = provider
        if provider == "local":
            self.provider = LocalStorage()
        elif provider == "b2":
            self.provider = B2Storage()
        else:
            raise ValueError(f"Unknown storage provider: {provider}. Use 'local' or 'b2'.")

    def save(self, file_obj, document_id: str, original_filename: str) -> str:
        return self.provider.save(file_obj, document_id, original_filename)

    def delete(self, document_id: str) -> bool:
        return self.provider.delete(document_id)

    def exists(self, document_id: str) -> bool:
        return self.provider.exists(document_id)

    def get_local_path(self, document_id: str):
        return self.provider.get_local_path(document_id)

    def get_metadata(self, document_id: str):
        return self.provider.get_metadata(document_id)

    def list_documents(self):
        return self.provider.list_documents()

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

    def save(self, file_obj, storage_path: str) -> str:
        return self.provider.save(file_obj, storage_path)

    def delete(self, storage_path: str) -> bool:
        return self.provider.delete(storage_path)

    def exists(self, storage_path: str) -> bool:
        return self.provider.exists(storage_path)

    def get_local_path(self, storage_path: str):
        return self.provider.get_local_path(storage_path)

    def get_metadata(self, storage_path: str):
        return self.provider.get_metadata(storage_path)

    def list_documents(self):
        return self.provider.list_documents()

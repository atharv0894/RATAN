from abc import ABC, abstractmethod
from typing import Any
from .models import ParsedDocument

class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: str, filename: str, **kwargs: Any) -> ParsedDocument:
        """Parses a file and returns a unified ParsedDocument."""
        pass
        
    def extract_metadata(self, file_path: str) -> dict:
        """Optional metadata extraction before full parse."""
        import os
        stat = os.stat(file_path)
        return {
            "file_size": stat.st_size,
            "creation_date": stat.st_ctime,
            "modification_date": stat.st_mtime,
        }

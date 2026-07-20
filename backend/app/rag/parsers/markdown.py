from .base import BaseParser
from .models import ParsedDocument, ParsedPage

class MarkdownParser(BaseParser):
    def parse(self, file_path: str, filename: str, **kwargs) -> ParsedDocument:
        metadata = self.extract_metadata(file_path)
        
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()
            
        metadata["page_count"] = 1
        metadata["mime_type"] = "text/markdown"
        
        page = ParsedPage(page_number=1, text=text)
        
        return ParsedDocument(
            filename=filename,
            metadata=metadata,
            pages=[page],
            text=text
        )

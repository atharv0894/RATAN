import csv
from .base import BaseParser
from .models import ParsedDocument, ParsedPage

class CSVParser(BaseParser):
    def parse(self, file_path: str, filename: str, **kwargs) -> ParsedDocument:
        metadata = self.extract_metadata(file_path)
        
        rows = []
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.reader(f)
            for row in reader:
                rows.append(", ".join(row))
                
        text = "\n".join(rows)
            
        metadata["page_count"] = 1
        metadata["mime_type"] = "text/csv"
        
        page = ParsedPage(page_number=1, text=text)
        
        return ParsedDocument(
            filename=filename,
            metadata=metadata,
            pages=[page],
            text=text
        )

# pyrefly: ignore [missing-import]
import pdfplumber
from .base import BaseParser
from .models import ParsedDocument, ParsedPage

class PDFParser(BaseParser):
    def parse(self, file_path: str, filename: str, **kwargs) -> ParsedDocument:
        metadata = self.extract_metadata(file_path)
        pages = []
        full_text = []
        
        with pdfplumber.open(file_path) as pdf:
            if pdf.metadata:
                for k, v in pdf.metadata.items():
                    if isinstance(v, (str, int, float, bool)):
                        metadata[k.lower()] = v
            
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                tables = page.extract_tables() or []
                
                # OCR Fallback simulation if text is completely empty
                if not text.strip() and kwargs.get('use_ocr', False):
                    text = self._perform_ocr(page)
                    
                pages.append(ParsedPage(
                    page_number=i,
                    text=text,
                    tables=[{"data": t} for t in tables]
                ))
                full_text.append(text)
                
        metadata["page_count"] = len(pages)
        metadata["mime_type"] = "application/pdf"
        
        return ParsedDocument(
            filename=filename,
            metadata=metadata,
            pages=pages,
            text="\n\n".join(full_text)
        )
        
    def _perform_ocr(self, page) -> str:
        # In a real scenario, convert page to image and run pytesseract
        return "[OCR Fallback Executed]"

import os
# pyrefly: ignore [missing-import]
import pdfplumber

class DocumentLoader:
    def load_file(self, file_path: str):
        """Loads text from a PDF or TXT file and returns a list of dictionaries with page_no and text."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} not found.")
            
        ext = file_path.lower().split('.')[-1]
        if ext == 'pdf':
            return self._load_pdf(file_path)
        elif ext == 'txt':
            return self._load_txt(file_path)
        else:
            raise ValueError("Unsupported file format. Please provide a .pdf or .txt file.")
            
    def _load_pdf(self, file_path: str):
        pages_content = []
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text:
                    pages_content.append({"page_no": page_num, "text": text})
        return pages_content
        
    def _load_txt(self, file_path: str):
        with open(file_path, 'r', encoding='utf-8') as f:
            return [{"page_no": 1, "text": f.read()}]

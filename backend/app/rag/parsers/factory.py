import os
from .base import BaseParser
from .pdf import PDFParser
from .txt import TXTParser
from .docx import DOCXParser
from .csv import CSVParser
from .markdown import MarkdownParser

class ParserFactory:
    @staticmethod
    def get_parser(file_path: str) -> BaseParser:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            return PDFParser()
        elif ext == '.txt':
            return TXTParser()
        elif ext == '.docx':
            return DOCXParser()
        elif ext == '.csv':
            return CSVParser()
        elif ext == '.md':
            return MarkdownParser()
        else:
            raise ValueError(f"Unsupported file format: {ext}")

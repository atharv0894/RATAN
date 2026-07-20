from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ParsedPage(BaseModel):
    page_number: int
    text: str
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    images: List[Dict[str, Any]] = Field(default_factory=list)

class ParsedDocument(BaseModel):
    filename: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    pages: List[ParsedPage] = Field(default_factory=list)
    text: str = ""

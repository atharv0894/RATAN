from typing import TypeVar, Generic, Optional, Any, List
from pydantic import BaseModel

T = TypeVar('T')

class APIErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None

class APIErrorResponse(BaseModel):
    success: bool = False
    error: APIErrorDetail

class APISuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    meta: Optional[dict] = None

class PaginatedMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int

class APIPaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: List[T]
    meta: PaginatedMeta

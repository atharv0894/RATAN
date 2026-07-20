from fastapi import Request
from fastapi.responses import JSONResponse

class AppException(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: dict = None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}

class NotFoundError(AppException):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(404, "NOT_FOUND", f"{resource} with ID {resource_id} not found.")

class DuplicateResourceError(AppException):
    def __init__(self, resource: str, identifier: str):
        super().__init__(409, "DUPLICATE_RESOURCE", f"{resource} '{identifier}' already exists.")

class ValidationError(AppException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(422, "VALIDATION_ERROR", message, details)

class AuthenticationError(AppException):
    def __init__(self, message: str = "Authentication failed."):
        super().__init__(401, "UNAUTHORIZED", message)

class AuthorizationError(AppException):
    def __init__(self, message: str = "Permission denied."):
        super().__init__(403, "FORBIDDEN", message)

# Specific custom errors from before
class DuplicateDocumentError(DuplicateResourceError):
    def __init__(self, document_id: str):
        super().__init__("Document", document_id)

async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )

async def global_exception_handler(request: Request, exc: Exception):
    import logging
    logging.error(f"Unhandled server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred.",
                "details": {}
            }
        }
    )

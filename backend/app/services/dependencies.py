# Singletons
embedding_service = None
vector_store = None
search_engine = None
rag_service = None
document_service = None

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from app.services.auth_service import AuthService
from app.exceptions import AuthenticationError, AuthorizationError
from app.database.sqlite import get_db_connection

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = AuthService.decode_token(token)
    if payload.get("type") != "access":
        raise AuthenticationError("Invalid token type. Expected access token.")
        
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Token missing user ID.")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.org_id, u.plant_id, u.department_id, u.email, u.full_name, u.status, r.name as role
        FROM users u 
        JOIN roles r ON u.role_id = r.id
        WHERE u.id = ?
    """, (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise AuthenticationError("User not found.")
    if user['status'] != 'Active':
        raise AuthenticationError("User is inactive or deleted.")
        
    return {
        "id": user['id'],
        "org_id": user['org_id'],
        "plant_id": user['plant_id'],
        "department_id": user['department_id'],
        "role": user['role'],
        "email": user['email'],
        "full_name": user['full_name']
    }

class RequireRole:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles
        
    def __call__(self, user: dict = Depends(get_current_user)):
        if user.get("role") not in self.allowed_roles:
            raise AuthorizationError(f"Role {user.get('role')} is not authorized to access this resource.")
        return user

def get_tenant_context(user: dict = Depends(get_current_user)):
    return {
        "organization": user["org_id"],
        "user_id": user["id"],
        "role": user["role"],
        "plant_id": user["plant_id"],
        "department_id": user["department_id"]
    }

def get_embedding_service():
    global embedding_service
    if embedding_service is None:
        from app.rag.embedding_service import EmbeddingService
        embedding_service = EmbeddingService()
    return embedding_service

def get_vector_store():
    global vector_store
    if vector_store is None:
        from app.rag.vector_store import VectorStore
        vector_store = VectorStore()
    return vector_store

def get_search_engine():
    global search_engine
    if search_engine is None:
        from app.rag.search.engine import SearchEngine
        search_engine = SearchEngine(get_embedding_service(), get_vector_store())
    return search_engine

def get_rag_service():
    global rag_service
    if rag_service is None:
        from app.rag.rag_service import RAGService
        rag_service = RAGService(get_search_engine())
    return rag_service

def get_document_service():
    global document_service
    if document_service is None:
        from app.services.document_service import DocumentService
        document_service = DocumentService()
    return document_service

import os
import time
import pytest
from fastapi.testclient import TestClient
import tempfile
import uuid
from unittest.mock import MagicMock, patch

# Set up test DB path before importing the app
TEST_DB = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
os.environ["RATAN_DB_PATH"] = TEST_DB.name
os.environ["B2_BUCKET_NAME"] = "test-bucket"
os.environ["QDRANT_URL"] = "http://localhost:6333"
os.environ["JWT_SECRET_KEY"] = "test_secret_key"
os.environ["JWT_ALGORITHM"] = "HS256"

from app.main import app
from app.database.sqlite import init_db, get_db_connection
from app.services.cleanup_service import CleanupService
from app.services import document_service

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db()
    yield
    os.remove(TEST_DB.name)

@pytest.fixture(scope="module")
def admin_token(setup_database):
    # Register an admin user for tests
    org_id = str(uuid.uuid4())
    plant_id = str(uuid.uuid4())
    role_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    conn = get_db_connection()
    cursor = conn.cursor()
    now = time.time()
    
    # Get or create Role
    cursor.execute("SELECT id FROM roles WHERE name = 'Admin'")
    row = cursor.fetchone()
    if row:
        role_id = row['id']
    else:
        cursor.execute("INSERT INTO roles (id, name, permissions, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                       (role_id, 'Admin', '{"all": true}', now, now))
    # Create Org, Plant, Dept
    cursor.execute("INSERT OR IGNORE INTO organizations (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                   (org_id, 'Test Org', now, now))
    cursor.execute("INSERT OR IGNORE INTO plants (id, org_id, name, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                   (plant_id, org_id, 'Test Plant', now, now))
    dept_id = str(uuid.uuid4())
    cursor.execute("INSERT OR IGNORE INTO departments (id, plant_id, name, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                   (dept_id, plant_id, 'Test Dept', now, now))
    # Create User
    cursor.execute("INSERT OR IGNORE INTO users (id, org_id, plant_id, department_id, role_id, email, password_hash, full_name, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   (user_id, org_id, plant_id, dept_id, role_id, 'admin@test.local', 'hashed', 'Admin User', now, now))
    conn.commit()
    conn.close()
    
    # Generate token
    from app.services.auth_service import AuthService
    token = AuthService.create_access_token({
        "sub": user_id,
        "org_id": org_id,
        "plant_id": plant_id,
        "department_id": dept_id,
        "role": "Admin",
        "email": "admin@test.local",
        "full_name": "Admin User"
    })
    return token

@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture
def mock_storage():
    with patch("app.services.document_service.StorageService") as mock:
        instance = mock.return_value
        instance.save.return_value = "documents/test_file/v1.pdf"
        instance.get_metadata.return_value = {"size": 1024, "mime_type": "application/pdf"}
        instance.get_local_path.return_value = "/tmp/fake.pdf"
        yield instance

@pytest.fixture
def mock_vector_store():
    with patch("app.services.dependencies.get_vector_store") as mock:
        instance = mock.return_value
        instance.client = MagicMock()
        instance.collection_name = "test_col"
        instance.__class__.__name__ = "MockStore"
        yield instance

@pytest.fixture
def mock_vector_store_cleanup():
    with patch("app.services.cleanup_service.VectorStore") as mock:
        instance = mock.return_value
        instance.client = MagicMock()
        yield instance

@pytest.fixture
def mock_indexer():
    with patch("app.services.document_service.Indexer") as mock:
        instance = mock.return_value
        instance.index_chunks.return_value = ["chunk1", "chunk2"]
        yield instance
        
@pytest.fixture
def mock_parser():
    with patch("app.services.document_service.ParserFactory") as mock:
        instance = mock.get_parser.return_value
        mock_doc = MagicMock()
        mock_doc.metadata = {}
        mock_doc.pages = []
        instance.parse.return_value = mock_doc
        yield instance

def create_dummy_pdf(path="test.pdf"):
    with open(path, "wb") as f:
        f.write(f"%PDF-1.4 sample content {uuid.uuid4()}".encode())
    return path

def test_new_upload_success(mock_storage, mock_vector_store, mock_indexer, mock_parser, auth_headers):
    path = create_dummy_pdf("version1.pdf")
    with open(path, "rb") as f:
        response = client.post("/api/v1/documents/upload", headers=auth_headers, files={"file": ("test_doc.pdf", f, "application/pdf")})
        
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "UPLOADED"
    assert "document_id" in data
    assert data["duplicate"] == False
    os.remove(path)

def test_duplicate_upload(mock_storage, mock_vector_store, mock_indexer, mock_parser, auth_headers):
    path = create_dummy_pdf("version1.pdf")
    with open(path, "rb") as f:
        client.post("/api/v1/documents/upload", headers=auth_headers, files={"file": ("test_doc2.pdf", f, "application/pdf")})
        
    with open(path, "rb") as f:
        response = client.post("/api/v1/documents/upload", headers=auth_headers, files={"file": ("test_doc2.pdf", f, "application/pdf")})
        
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["duplicate"] == True
    assert data["status"] == "ALREADY_EXISTS"
    os.remove(path)

def test_new_version_upload(mock_storage, mock_vector_store, mock_indexer, mock_parser, auth_headers):
    path1 = create_dummy_pdf("version_test.pdf")
    path2 = "version2.pdf"
    with open(path2, "wb") as f:
        f.write(b"%PDF-1.4 modified content")
        
    with open(path1, "rb") as f:
        client.post("/api/v1/documents/upload", headers=auth_headers, files={"file": ("version_test.pdf", f, "application/pdf")})
        
    with open(path2, "rb") as f:
        res2 = client.post("/api/v1/documents/upload", headers=auth_headers, files={"file": ("version_test.pdf", f, "application/pdf")})
        
    assert res2.status_code == 200
    data2 = res2.json()["data"]
    assert data2["duplicate"] == False
    
    docs = client.get("/api/v1/documents", headers=auth_headers).json()["data"]
    versions = [d for d in docs if d["filename"] == "version_test.pdf"]
    assert len(versions) == 1
    assert versions[0]["version_number"] == 2
    
    os.remove(path1)
    os.remove(path2)

def test_soft_delete_and_restore(mock_storage, mock_vector_store, mock_indexer, mock_parser, auth_headers):
    path = create_dummy_pdf("delete_test.pdf")
    with open(path, "rb") as f:
        upload_res = client.post("/api/v1/documents/upload", headers=auth_headers, files={"file": ("delete_test.pdf", f, "application/pdf")})
        
    doc_id = upload_res.json()["data"]["document_id"]
    
    del_res = client.delete(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    assert del_res.status_code == 200
    
    # Should not be in regular list
    # Wait, GET /documents might still list it if not filtered, but we filter out deleted_at IS NULL
    docs = client.get("/api/v1/documents", headers=auth_headers).json()["data"]
    assert not any(d["id"] == doc_id for d in docs)
    
    restore_res = client.post(f"/api/v1/documents/{doc_id}/restore", headers=auth_headers)
    assert restore_res.status_code == 200
    
    docs = client.get("/api/v1/documents", headers=auth_headers).json()["data"]
    assert any(d["id"] == doc_id for d in docs)
    
    os.remove(path)

def test_concurrent_delete_fails(auth_headers):
    # If a document is in PROCESSING, delete should fail
    doc_id = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()
    now = time.time()
    
    cursor.execute('''INSERT INTO documents (id, title, filename, owner, organization, plant, department, created_at, updated_at, status)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (doc_id, "proc.pdf", "proc.pdf", "user1", "org1", "plant1", "dept1", now, now, 'PROCESSING'))
    conn.commit()
    conn.close()
    
    res = client.delete(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    assert res.status_code == 409
    assert "processing" in res.json()["error"]["message"].lower()

def test_cleanup_hard_delete_and_rollback(mock_storage, mock_vector_store_cleanup):
    cleanup_service = CleanupService()
    
    doc_id = str(uuid.uuid4())
    ver_id = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()
    now = time.time()
    
    # Soft deleted doc
    cursor.execute('''INSERT INTO documents (id, title, filename, owner, organization, plant, department, created_at, updated_at, deleted_at, status)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (doc_id, "hard_del.pdf", "hard_del.pdf", "user1", "org1", "plant1", "dept1", now, now, now, 'DELETED'))
    cursor.execute('''INSERT INTO document_versions (id, document_id, version_number, checksum, storage_path, collection_name, uploaded_by_user_id, uploaded_at, file_size, embedding_model, chunk_count, vector_count, status)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (ver_id, doc_id, 1, "chk", "path", "qdrant", "user1", now, 10, "m", 1, 1, 'DELETED'))
    conn.commit()
    
    # 1. Test Hard Delete Success
    cleanup_service.run_cleanup(purge_deleted=True)
    cursor.execute("SELECT id FROM documents WHERE id = ?", (doc_id,))
    assert cursor.fetchone() is None
    
    # 2. Test Rollback on Failure (Compensating Transaction)
    doc_id2 = str(uuid.uuid4())
    ver_id2 = str(uuid.uuid4())
    cursor.execute('''INSERT INTO documents (id, title, filename, owner, organization, plant, department, created_at, updated_at, deleted_at, status)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (doc_id2, "hard_del2.pdf", "hard_del2.pdf", "user1", "org1", "plant1", "dept1", now, now, now, 'DELETED'))
    cursor.execute('''INSERT INTO document_versions (id, document_id, version_number, checksum, storage_path, collection_name, uploaded_by_user_id, uploaded_at, file_size, embedding_model, chunk_count, vector_count, status)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (ver_id2, doc_id2, 1, "chk2", "path", "qdrant", "user1", now, 10, "m", 1, 1, 'DELETED'))
    conn.commit()
    
    # Make vector store throw an exception
    mock_vector_store_cleanup.client.delete.side_effect = Exception("Qdrant connection lost")
    
    cleanup_service.run_cleanup(purge_deleted=True)
    
    # Document should STILL exist, but lock should be cleared due to rollback
    cursor.execute("SELECT id, locked_at FROM document_versions WHERE id = ?", (ver_id2,))
    res = cursor.fetchone()
    assert res is not None
    assert res['locked_at'] is None
    
    conn.close()

def test_stale_lock_recovery(mock_vector_store_cleanup):
    cleanup_service = CleanupService()
    ver_id = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()
    now = time.time()
    
    # Create document version with STALE lock (2 hours old)
    stale_time = now - 7200
    cursor.execute('''INSERT INTO documents (id, title, filename, owner, organization, plant, department, created_at, updated_at, status)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', ("doc3", "stale.pdf", "stale.pdf", "user1", "org1", "plant1", "dept1", now, now, 'READY'))
    cursor.execute('''INSERT INTO document_versions (id, document_id, version_number, checksum, storage_path, collection_name, uploaded_by_user_id, uploaded_at, file_size, embedding_model, chunk_count, vector_count, status, locked_at, locked_by_user_id, lock_reason)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (ver_id, "doc3", 1, "chk3", "path", "qdrant", "user1", now, 10, "m", 1, 1, 'READY', stale_time, 'SYSTEM', 'Cleanup Eradication'))
    conn.commit()
    
    stats = cleanup_service.run_cleanup()
    assert stats["stale_locks_cleared"] == 1
    
    cursor.execute("SELECT locked_at FROM document_versions WHERE id = ?", (ver_id,))
    assert cursor.fetchone()['locked_at'] is None
    conn.close()

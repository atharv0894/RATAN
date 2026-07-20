import os
import pytest
from fastapi.testclient import TestClient
import tempfile
import uuid

# Set up test DB path before importing the app
TEST_DB = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
os.environ["RATAN_DB_PATH"] = TEST_DB.name
os.environ["B2_BUCKET_NAME"] = "test-bucket"
os.environ["QDRANT_URL"] = "http://localhost:6333"

# Mock the storage and vector db to prevent actual network calls during tests
from unittest.mock import MagicMock, patch

from app.main import app
from app.database.sqlite import init_db

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db()
    yield
    os.remove(TEST_DB.name)

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
    with patch("app.services.document_service.VectorStore") as mock:
        instance = mock.return_value
        instance.__class__.__name__ = "MockStore"
        yield instance

@pytest.fixture
def mock_indexer():
    with patch("app.services.document_service.Indexer") as mock:
        instance = mock.return_value
        instance.index_chunks.return_value = ["chunk1", "chunk2"]
        yield instance
        
@pytest.fixture
def mock_chunker():
    with patch("app.services.document_service.TextChunker") as mock:
        instance = mock.return_value
        instance.chunk_text_with_metadata.return_value = [{"text": "Sample", "metadata": {}}]
        yield instance

def create_dummy_pdf(path="test.pdf"):
    with open(path, "wb") as f:
        f.write(b"%PDF-1.4 sample content")
    return path

def test_new_upload_success(mock_storage, mock_vector_store, mock_indexer, mock_chunker):
    path = create_dummy_pdf("version1.pdf")
    with open(path, "rb") as f:
        response = client.post("/documents/upload", files={"file": ("test_doc.pdf", f, "application/pdf")})
        
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "uploaded"
    assert "document_id" in data
    assert data["duplicate"] == False
    os.remove(path)

def test_duplicate_upload(mock_storage, mock_vector_store, mock_indexer, mock_chunker):
    path = create_dummy_pdf("version1.pdf")
    # First upload
    with open(path, "rb") as f:
        client.post("/documents/upload", files={"file": ("test_doc2.pdf", f, "application/pdf")})
        
    # Second upload with exactly same file
    with open(path, "rb") as f:
        response = client.post("/documents/upload", files={"file": ("test_doc2.pdf", f, "application/pdf")})
        
    assert response.status_code == 200
    data = response.json()
    assert data["duplicate"] == True
    assert data["status"] == "already_exists"
    os.remove(path)

def test_new_version_upload(mock_storage, mock_vector_store, mock_indexer, mock_chunker):
    path1 = create_dummy_pdf("version1.pdf")
    path2 = "version2.pdf"
    with open(path2, "wb") as f:
        f.write(b"%PDF-1.4 modified content")
        
    # Upload v1
    with open(path1, "rb") as f:
        res1 = client.post("/documents/upload", files={"file": ("version_test.pdf", f, "application/pdf")})
        
    # Upload v2 with same filename but different content
    with open(path2, "rb") as f:
        res2 = client.post("/documents/upload", files={"file": ("version_test.pdf", f, "application/pdf")})
        
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["duplicate"] == False
    
    # Check versions
    docs = client.get("/documents").json()
    versions = [d for d in docs if d["filename"] == "version_test.pdf"]
    assert len(versions) == 1  # Only latest version returned by default
    assert versions[0]["version_number"] == 2
    
    os.remove(path1)
    os.remove(path2)

def test_delete_success_and_restore(mock_storage, mock_vector_store, mock_indexer, mock_chunker):
    path = create_dummy_pdf("delete_test.pdf")
    with open(path, "rb") as f:
        upload_res = client.post("/documents/upload", files={"file": ("delete_test.pdf", f, "application/pdf")})
        
    doc_id = upload_res.json()["document_id"]
    
    # Soft Delete
    del_res = client.delete(f"/documents/{doc_id}")
    assert del_res.status_code == 200
    
    # Verify it is deleted
    docs = client.get("/documents").json()
    assert not any(d["id"] == doc_id for d in docs)
    
    # Restore
    restore_res = client.post(f"/documents/{doc_id}/restore")
    assert restore_res.status_code == 200
    
    # Verify it is restored
    docs = client.get("/documents").json()
    assert any(d["id"] == doc_id for d in docs)
    
    os.remove(path)

def test_delete_missing():
    res = client.delete(f"/documents/{str(uuid.uuid4())}")
    assert res.status_code == 404

def test_cleanup_hard_delete():
    from app.services.cleanup_service import CleanupService
    from app.database.sqlite import get_db_connection
    
    # Generate dummy deleted record
    doc_id = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO documents (document_id, filename, status, upload_time, embedding_model, vector_db, chunk_count, processing_time, is_deleted)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', (doc_id, "hard_delete.pdf", "Indexed", 12345, "model", "qdrant", 1, 0.1, 1))
    conn.commit()
    conn.close()
    
    # Run cleanup to eradicate soft-deleted docs
    cleanup_service = CleanupService()
    # Mocking out vector store and storage calls within cleanup
    cleanup_service.storage_service = MagicMock()
    cleanup_service.vector_store = MagicMock()
    
    res = cleanup_service.run_cleanup(purge_deleted=True)
    
    # Verify it is permanently removed
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE document_id = ?", (doc_id,))
    assert cursor.fetchone() is None
    conn.close()

import pytest
import os
import tempfile
from fastapi.testclient import TestClient

TEST_DB = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
os.environ["RATAN_DB_PATH"] = TEST_DB.name
os.environ["JWT_SECRET_KEY"] = "test_secret_key"
os.environ["JWT_ALGORITHM"] = "HS256"

from app.main import app
from app.database.sqlite import init_db

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db()
    yield
    os.remove(TEST_DB.name)

def test_register_organization():
    import uuid
    suffix = str(uuid.uuid4())[:8]
    response = client.post(
        "/api/v1/enterprise/auth/register",
        json={
            "org_name": f"Test Org {suffix}",
            "admin_email": f"admin_{suffix}@testorg.com",
            "admin_password": "SecurePassword123!",
            "admin_name": "Admin User"
        }
    )
    assert response.status_code == 200
    assert response.json()["success"] is True

def test_login():
    response = client.post(
        "/api/v1/enterprise/auth/login",
        data={
            "username": "admin@testorg.com",
            "password": "SecurePassword123!"
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()["data"]
    assert "refresh_token" in response.json()["data"]

def test_get_me():
    # 1. Login
    login_response = client.post(
        "/api/v1/enterprise/auth/login",
        data={
            "username": "admin@testorg.com",
            "password": "SecurePassword123!"
        }
    )
    token = login_response.json()["data"]["access_token"]
    
    # 2. Get Me
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["data"]["email"] == "admin@testorg.com"

def test_forgot_password():
    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "admin@testorg.com"}
    )
    assert response.status_code == 200

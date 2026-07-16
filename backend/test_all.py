import requests
import time
import os
import sqlite3
import subprocess

BASE_URL = "http://localhost:8000"

def test_health():
    print("--- Testing /health ---")
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    data = r.json()
    print("Health:", data)
    assert 'storage_provider' in data

def test_upload_validations():
    print("--- Testing Upload Validations ---")
    # 1. TXT
    with open("dummy.txt", "w") as f: f.write("hello")
    with open("dummy.txt", "rb") as f:
        r = requests.post(f"{BASE_URL}/documents/upload", files={"file": ("dummy.txt", f)})
    assert r.status_code == 415

    # 2. Oversize
    with open("large.pdf", "wb") as f:
        f.seek(51 * 1024 * 1024)
        f.write(b"\0")
    with open("large.pdf", "rb") as f:
        r = requests.post(f"{BASE_URL}/documents/upload", files={"file": ("large.pdf", f)})
    assert r.status_code == 413
    os.remove("large.pdf")
    os.remove("dummy.txt")
    print("Validations passed.")

def test_duplicate_and_ingestion():
    print("--- Testing Duplicate & Ingestion ---")
    with open("small_test.pdf", "rb") as f:
        r = requests.post(f"{BASE_URL}/documents/upload", files={"file": ("valid1.pdf", f)})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    doc_id = r.json()["results"][0]["document_id"]
    
    # Duplicate
    with open("small_test.pdf", "rb") as f:
        r = requests.post(f"{BASE_URL}/documents/upload", files={"file": ("valid1.pdf", f)})
    assert r.status_code == 409, f"Expected 409, got {r.status_code}"
    
    return doc_id

def test_reindex(doc_id):
    print("--- Testing Reindex ---")
    r = requests.post(f"{BASE_URL}/documents/{doc_id}/reindex")
    assert r.status_code == 200
    print("Reindex passed.")

def test_chat():
    print("--- Testing Chat ---")
    r = requests.post(f"{BASE_URL}/chat", json={"question": "What is SDLC?"})
    assert r.status_code == 200
    print("Chat passed:", r.json().get("answer")[:50], "...")

def test_delete(doc_id):
    print("--- Testing Delete ---")
    r = requests.delete(f"{BASE_URL}/documents/{doc_id}")
    assert r.status_code == 200
    print("Delete passed.")

def run_all():
    try:
        test_health()
        test_upload_validations()
        doc_id = test_duplicate_and_ingestion()
        test_reindex(doc_id)
        test_chat()
        test_delete(doc_id)
        print("\nALL API TESTS PASSED.")
    except AssertionError as e:
        print("\nTEST FAILED:", e)

if __name__ == "__main__":
    run_all()

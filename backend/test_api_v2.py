import requests
import time
import os

BASE_URL = "http://localhost:8000"

def test_api():
    print("Testing /health...")
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    print(r.json())
    
    print("\nTesting /documents (empty or existing)...")
    r = requests.get(f"{BASE_URL}/documents")
    assert r.status_code == 200
    docs = r.json()
    print(docs)

    print("\nTesting upload (dummy text not PDF)...")
    with open("dummy.txt", "w") as f: f.write("hello")
    with open("dummy.txt", "rb") as f:
        r = requests.post(f"{BASE_URL}/documents/upload", files={"file": ("dummy.txt", f)})
    assert r.status_code == 415
    print(r.json())
    
    print("\nTesting upload (valid PDF)...")
    valid_pdf = "small_test.pdf"
    with open(valid_pdf, "rb") as f:
        r = requests.post(f"{BASE_URL}/documents/upload", files={"file": ("handbook.pdf", f)})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    print(r.json())
    doc_id = r.json()["results"][0]["document_id"]
    
    print("\nTesting upload (duplicate PDF - should 409)...")
    with open(valid_pdf, "rb") as f:
        r = requests.post(f"{BASE_URL}/documents/upload", files={"file": ("handbook2.pdf", f)})
    assert r.status_code == 409, f"Expected 409, got {r.status_code}: {r.text}"
    print(r.json())

    print("\nTesting GET /documents/{id}...")
    r = requests.get(f"{BASE_URL}/documents/{doc_id}")
    assert r.status_code == 200
    print(r.json())

    print("\nTesting POST /documents/{id}/reindex...")
    r = requests.post(f"{BASE_URL}/documents/{doc_id}/reindex")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    print(r.json())

    print("\nTesting DELETE /documents/{id}...")
    r = requests.delete(f"{BASE_URL}/documents/{doc_id}")
    assert r.status_code == 200
    print(r.json())

    print("\nTesting /chat...")
    r = requests.post(f"{BASE_URL}/chat", json={"question": "What is SDLC?"})
    assert r.status_code == 200
    print("Chat response received")

    print("\nAll API endpoints hit successfully!")

if __name__ == "__main__":
    test_api()

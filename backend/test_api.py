import requests
import time
import os

BASE_URL = "http://localhost:8000"

def test_api():
    print("Testing /health...")
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    print(r.json())
    
    print("\nTesting /stats...")
    r = requests.get(f"{BASE_URL}/stats")
    assert r.status_code == 200
    print(r.json())
    
    print("\nTesting /documents (empty)...")
    r = requests.get(f"{BASE_URL}/documents")
    assert r.status_code == 200
    print(r.json())

    print("\nTesting upload (dummy text not PDF)...")
    with open("dummy.txt", "w") as f: f.write("hello")
    with open("dummy.txt", "rb") as f:
        r = requests.post(f"{BASE_URL}/documents/upload", files={"file": ("dummy.txt", f)})
    assert r.status_code == 415
    print(r.json())
    
    print("\nTesting /chat...")
    r = requests.post(f"{BASE_URL}/chat", json={"question": "What is SDLC?"})
    assert r.status_code == 200
    print("Chat response received")

    print("\nAll API endpoints hit successfully!")

if __name__ == "__main__":
    test_api()

import requests
import time
import os

BASE_URL = "http://localhost:8000"

def run_tests():
    print("--- 1. Creating Document ---")
    doc_text = [
        "Standard Operating Procedure",
        "Maintenance Manual for Pump P-101 and Valve V-204.",
        "The Operator and Maintenance Engineer should wear PPE.",
        "Follow ISO 9001 and ASME B31.3 standards.",
        "Monitor the Temperature and Flow Rate carefully.",
        "Lockout Tagout (LOTO) is required.",
        "SOP Number: SOP-1234"
    ]
    
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in doc_text:
        pdf.cell(200, 10, txt=line, ln=True)
    pdf.output("entity_test.pdf")
        
    print("--- 2. Uploading Document ---")
    with open("entity_test.pdf", "rb") as f:
        r = requests.post(f"{BASE_URL}/documents/upload", files={"file": ("entity_test.pdf", f)})
    
    assert r.status_code == 200, f"Upload failed: {r.text}"
    doc_id = r.json()["results"][0]["document_id"]
    print(f"Document ID: {doc_id}")
    
    # Wait a sec for DB writes to settle if needed (should be sync though)
    time.sleep(1)
    
    print("--- 3. Testing GET /entities ---")
    r = requests.get(f"{BASE_URL}/entities")
    assert r.status_code == 200
    entities = r.json()
    print(f"Total Unique Entities: {len(entities)}")
    
    # Check if we got expected types
    types = set([e["type"] for e in entities])
    assert "Equipment" in types
    assert "Role" in types
    assert "Standard" in types
    assert "Safety" in types
    assert "Parameter" in types
    print("Types found:", types)
    
    print("--- 4. Testing GET /documents/{id}/entities ---")
    r = requests.get(f"{BASE_URL}/entities/documents/{doc_id}/entities")
    assert r.status_code == 200
    doc_entities = r.json()["entities"]
    print(f"Entities in doc: {len(doc_entities)}")
    assert len(doc_entities) > 0
    
    print("--- 5. Testing GET /entities/{entity_name} ---")
    r = requests.get(f"{BASE_URL}/entities/Pump P-101")
    assert r.status_code == 200
    results = r.json()["results"]
    print(f"Search results for 'Pump P-101': {len(results)}")
    assert len(results) > 0
    
    print("--- 6. Testing Chat Integration ---")
    r = requests.post(f"{BASE_URL}/chat", json={"question": "What should the Maintenance Engineer wear for Pump P-101?"})
    assert r.status_code == 200
    chat_resp = r.json()
    print("Chat response received.")
    print("Entities recognized in chat:", chat_resp.get("entities"))
    assert len(chat_resp.get("entities", [])) > 0
    
    print("--- 7. Cleaning up ---")
    requests.delete(f"{BASE_URL}/documents/{doc_id}")
    os.remove("entity_test.pdf")
    print("ALL TESTS PASSED!")

if __name__ == "__main__":
    run_tests()

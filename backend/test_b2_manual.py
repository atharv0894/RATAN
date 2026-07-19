import os
from dotenv import load_dotenv
load_dotenv()
from app.storage.b2_storage import B2Storage
import tempfile

def test_b2():
    try:
        print("Initializing B2Storage...")
        b2 = B2Storage()
        
        doc_id = "test-doc-123"
        filename = "test.txt"
        
        # Create a dummy file
        print(f"Creating test file {filename}...")
        with tempfile.NamedTemporaryFile("w+", delete=False) as f:
            f.write("Hello from RATAN test")
            temp_path = f.name
            
        print("Uploading to B2...")
        with open(temp_path, "rb") as f:
            b2.save(f, doc_id, filename)
            
        print("Verifying existence...")
        if b2.exists(doc_id):
            print("✅ File exists in B2.")
            meta = b2.get_metadata(doc_id)
            print(f"Metadata: {meta}")
        else:
            print("❌ File not found in B2.")
            
        print("Deleting from B2...")
        b2.delete(doc_id)
        
        print("Verifying deletion...")
        if not b2.exists(doc_id):
            print("✅ File successfully deleted from B2.")
        else:
            print("❌ File still exists in B2.")
            
    except Exception as e:
        print(f"Error testing B2: {e}")

if __name__ == "__main__":
    test_b2()

import os
from dotenv import load_dotenv
load_dotenv()
from app.services.dependencies import get_document_service, get_rag_service
from app.storage.storage_service import StorageService
import uuid

PDF_PATH = os.path.join(os.path.dirname(__file__), "..", "test_data", "marathi_new.pdf")

def test_cloud():
    print(f"Testing cloud ingestion directly with {PDF_PATH}...")
    doc_service = get_document_service()
    storage_service = StorageService()
    
    doc_id = str(uuid.uuid4())
    filename = "marathi-cloud-test.pdf"
    
    print("\n--- STEP 1: Uploading to Cloud ---")
    try:
        with open(PDF_PATH, 'rb') as f:
            saved_path = storage_service.save(f, doc_id, filename)
            print(f"✅ Uploaded to {storage_service.provider_name}. Path: {saved_path}")
            
        print("\n--- STEP 2: Indexing Document ---")
        indexed_id = doc_service.process_and_index(filename, saved_path, document_id=doc_id)
        print(f"✅ Document successfully indexed in Qdrant. ID: {indexed_id}")
    except Exception as e:
        print(f"❌ Error during ingestion: {e}")
        return
        
    print("\n--- STEP 3: Querying Document ---")
    rag = get_rag_service()
    question = "Who is the author of this document?"
    where = {"source": "marathi-cloud-test.pdf"}
    
    try:
        res = rag.generate_answer(question, debug=True, where=where)
        print(f"\n🤖 Answer: {res['answer']}")
    except Exception as e:
        print(f"❌ Error querying: {e}")

if __name__ == "__main__":
    test_cloud()

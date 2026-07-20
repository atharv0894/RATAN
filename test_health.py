import os
import sys

# Mock env
os.environ["VECTOR_DB"] = "qdrant"
os.environ["QDRANT_URL"] = "https://67de497a-e272-4fc4-afd9-52e409a32ba3.australia-southeast1-0.gcp.cloud.qdrant.io"
os.environ["QDRANT_API_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6MTUyYjgwZmQtZDcxZS00MjY0LThmYjktNmNmYmM4YmM5MjdlIn0.QWTECsL9UEK6XOo-0kRXw0UmEcRbxFn6sqfX86nuACc"

sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

from app.api.health import get_health

print("Calling get_health...")
try:
    res = get_health()
    print("Result:", res)
except Exception as e:
    print("Error:", e)

# pyrefly: ignore [missing-import]
import uvicorn
import os

if __name__ == "__main__":
    # Ensure chroma_db directory exists relative to backend
    os.makedirs("chroma_db", exist_ok=True)
    
    # Run the FastAPI server
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

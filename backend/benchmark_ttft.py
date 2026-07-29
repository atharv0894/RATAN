import time
import requests
from test_chat_direct import get_login_token

BASE_URL = "http://localhost:8000"

def run_benchmark():
    print("Running TTFT Benchmark...")
    token = get_login_token()
    if not token:
        print("Login failed, cannot benchmark.")
        return
        
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "question": "Explain how RATAN handles indexing in 3 sentences.",
        "chat_history": []
    }
    
    # Send request
    start_time = time.time()
    
    with requests.post(f"{BASE_URL}/api/v1/personal/chat/message", json=payload, headers=headers, stream=True) as res:
        if res.status_code != 200:
            print("Request failed:", res.status_code)
            return
            
        ttft = None
        for chunk in res.iter_lines():
            if chunk:
                line = chunk.decode('utf-8')
                if line.startswith("data: ") and '"type": "chunk"' in line:
                    if ttft is None:
                        ttft = time.time() - start_time
                        print(f"Time to First Token (TTFT): {ttft:.3f}s")
                elif line.startswith("data: ") and '"type": "done"' in line:
                    total_time = time.time() - start_time
                    print(f"Total Response Time: {total_time:.3f}s")
                    break

if __name__ == "__main__":
    run_benchmark()

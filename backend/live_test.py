import httpx
import json

BASE_URL = "https://ratan-uwno.onrender.com/api/v1"

def register_company():
    print("🚀 Registering company 'coep'...")
    
    payload = {
        "org_name": "coep",
        "admin_email": "admin@coep.edu",
        "admin_password": "securepassword123",
        "admin_name": "COEP System Admin"
    }
    
    response = httpx.post(f"{BASE_URL}/auth/register", json=payload)
    
    if response.status_code == 200:
        print("✅ Success! Response:")
        print(json.dumps(response.json(), indent=2))
        return True
    else:
        print(f"❌ Failed! Status Code: {response.status_code}")
        print(response.text)
        return False

def login():
    print("\n🔑 Logging in as the new admin...")
    
    payload = {
        "username": "admin@coep.edu",
        "password": "securepassword123"
    }
    
    # OAuth2 expects form data, not json
    response = httpx.post(f"{BASE_URL}/auth/login", data=payload)
    
    if response.status_code == 200:
        print("✅ Login Success! Token acquired.")
        token = response.json().get("data", {}).get("access_token")
        print(f"Token (First 20 chars): {token[:20]}...")
        return token
    else:
        print(f"❌ Login Failed! Status Code: {response.status_code}")
        print(response.text)
        return None

def get_me(token):
    print("\n👤 Fetching Admin Profile (/auth/me)...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = httpx.get(f"{BASE_URL}/auth/me", headers=headers)
    
    if response.status_code == 200:
        print("✅ Success! Profile Data:")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"❌ Failed! Status Code: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    # We already registered, so we can skip register_company()
    token = login()
    if token:
        get_me(token)

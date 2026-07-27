import sys
import uuid
import time
import os
from dotenv import load_dotenv

sys.path.append('.')

# Explicitly load .env so that TIDB_HOST is populated
load_dotenv()

from app.services.auth_service import AuthService
from app.database.sqlite import get_db_connection

def create_super_admin():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    email = "superadmin@ratan.com"
    password = "admin"
    password_hash = AuthService.get_password_hash(password)
    
    # Ensure SuperAdmin role exists
    cursor.execute("SELECT id FROM roles WHERE name = 'SuperAdmin'")
    role = cursor.fetchone()
    if not role:
        role_id = str(uuid.uuid4())
        now = time.time()
        cursor.execute("INSERT INTO roles (id, name, permissions, created_at, updated_at) VALUES (%s, 'SuperAdmin', '{\"all\": true}', %s, %s)", (role_id, now, now))
    else:
        role_id = role["id"]
        
    # Ensure Org exists
    cursor.execute("SELECT id FROM organizations WHERE name = 'System'")
    org = cursor.fetchone()
    if not org:
        org_id = str(uuid.uuid4())
        now = time.time()
        cursor.execute("INSERT INTO organizations (id, name, created_at, updated_at) VALUES (%s, 'System', %s, %s)", (org_id, now, now))
    else:
        org_id = org["id"]

    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    if user:
        cursor.execute("UPDATE users SET password_hash = %s, role_id = %s WHERE id = %s", (password_hash, role_id, user["id"]))
        print(f"Updated existing user {email}")
    else:
        user_id = str(uuid.uuid4())
        now = time.time()
        cursor.execute("""
            INSERT INTO users (id, org_id, role_id, email, password_hash, full_name, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, 'Super Admin', %s, %s)
        """, (user_id, org_id, role_id, email, password_hash, now, now))
        print(f"Created new superadmin {email}")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_super_admin()

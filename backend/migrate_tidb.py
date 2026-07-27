import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
from app.database.tidb import get_tidb_connection

conn = get_tidb_connection()
cursor = conn.cursor()
try:
    cursor.execute('ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT FALSE')
    cursor.execute('ALTER TABLE users ADD COLUMN email_verified_at TIMESTAMP NULL')
    cursor.execute('ALTER TABLE users ADD COLUMN verification_token VARCHAR(255)')
    cursor.execute('ALTER TABLE users ADD COLUMN verification_token_expires_at TIMESTAMP NULL')
    conn.commit()
    print("Columns added to TiDB successfully.")
except Exception as e:
    print("Error:", e)
finally:
    cursor.close()
    conn.close()

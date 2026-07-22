import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

def test_tidb_connection():
    print("Testing connection to TiDB Cloud...")
    try:
        conn = pymysql.connect(
            host=os.environ.get("TIDB_HOST"),
            port=int(os.environ.get("TIDB_PORT", 4000)),
            user=os.environ.get("TIDB_USER"),
            password=os.environ.get("TIDB_PASSWORD"),
            database=os.environ.get("TIDB_DATABASE", "sys"),
            ssl_verify_cert=True,
            ssl_verify_identity=True
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"✅ Successfully connected to TiDB!")
        print(f"Database Version: {version[0]}")
        
        conn.close()
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    test_tidb_connection()

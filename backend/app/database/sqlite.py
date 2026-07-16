import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ratan_registry.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            document_id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            status TEXT NOT NULL,
            upload_time REAL NOT NULL,
            embedding_model TEXT NOT NULL,
            vector_db TEXT NOT NULL,
            chunk_count INTEGER NOT NULL,
            processing_time REAL NOT NULL,
            storage_provider TEXT DEFAULT 'local',
            storage_path TEXT,
            file_size INTEGER DEFAULT 0,
            page_count INTEGER DEFAULT 0,
            checksum_sha256 TEXT,
            mime_type TEXT,
            index_status TEXT,
            last_indexed REAL
        )
    ''')
    
    # Quick migration for existing tables
    try:
        cursor.execute("ALTER TABLE documents ADD COLUMN storage_provider TEXT DEFAULT 'local'")
        cursor.execute("ALTER TABLE documents ADD COLUMN storage_path TEXT")
        cursor.execute("ALTER TABLE documents ADD COLUMN file_size INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE documents ADD COLUMN page_count INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE documents ADD COLUMN checksum_sha256 TEXT")
        cursor.execute("ALTER TABLE documents ADD COLUMN mime_type TEXT")
        cursor.execute("ALTER TABLE documents ADD COLUMN index_status TEXT")
        cursor.execute("ALTER TABLE documents ADD COLUMN last_indexed REAL")
    except sqlite3.OperationalError:
        # Columns likely already exist
        pass
    conn.commit()
    conn.close()

init_db()

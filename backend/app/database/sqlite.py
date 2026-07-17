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
            last_indexed REAL,
            document_class TEXT DEFAULT 'Unknown'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entities (
            entity_id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            chunk_id TEXT,
            entity_type TEXT NOT NULL,
            entity_value TEXT NOT NULL,
            page_number INTEGER,
            section TEXT,
            created_at REAL NOT NULL,
            FOREIGN KEY(document_id) REFERENCES documents(document_id) ON DELETE CASCADE
        )
    ''')
    
    # Quick migration for existing tables
    for col, default in [
        ("storage_provider", "'local'"),
        ("storage_path", "NULL"),
        ("file_size", "0"),
        ("page_count", "0"),
        ("checksum_sha256", "NULL"),
        ("mime_type", "NULL"),
        ("index_status", "NULL"),
        ("last_indexed", "NULL"),
        ("document_class", "'Unknown'")
    ]:
        try:
            cursor.execute(f"ALTER TABLE documents ADD COLUMN {col} TEXT DEFAULT {default}")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()

init_db()

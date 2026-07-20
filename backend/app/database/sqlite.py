import sqlite3
import os

default_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ratan_registry.db")
DB_PATH = os.environ.get("RATAN_DB_PATH", default_db_path)

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
            document_class TEXT DEFAULT 'Unknown',
            version_number INTEGER DEFAULT 1,
            uploaded_by TEXT DEFAULT 'system',
            previous_version TEXT,
            is_latest INTEGER DEFAULT 1,
            is_deleted INTEGER DEFAULT 0,
            is_locked INTEGER DEFAULT 0
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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            log_id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            action TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp REAL NOT NULL,
            details TEXT
        )
    ''')
    
    # Indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_filename ON documents(filename)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_checksum ON documents(checksum_sha256)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_status ON documents(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ent_val ON entities(entity_value)")
    
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
        ("document_class", "'Unknown'"),
        ("version_number", "1"),
        ("uploaded_by", "'system'"),
        ("previous_version", "NULL"),
        ("is_latest", "1"),
        ("is_deleted", "0"),
        ("is_locked", "0")
    ]:
        try:
            cursor.execute(f"ALTER TABLE documents ADD COLUMN {col} TEXT DEFAULT {default}")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()

init_db()

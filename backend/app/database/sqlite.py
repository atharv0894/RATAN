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
    # Ensure foreign keys are enforced
    conn.execute("PRAGMA foreign_keys = ON")
    
    from app.database.migrations import run_migrations
    run_migrations(conn)
    
    conn.close()

init_db()

import sys
import os
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

sys.path.append('.')
load_dotenv()

from app.database.sqlite import get_db_connection

def create_entities_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entities (
            entity_id VARCHAR(36) PRIMARY KEY,
            document_id VARCHAR(36) NOT NULL,
            chunk_id VARCHAR(100),
            entity_type VARCHAR(100) NOT NULL,
            entity_value VARCHAR(255) NOT NULL,
            page_number INT,
            section VARCHAR(255),
            created_at DOUBLE NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Entities table created or already exists!")

if __name__ == "__main__":
    create_entities_table()

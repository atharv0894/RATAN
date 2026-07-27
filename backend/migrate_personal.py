import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), "backend"))
load_dotenv("backend/.env")

from app.database.tidb import get_tidb_connection

def migrate():
    conn = get_tidb_connection()
    cursor = conn.cursor()
    try:
        # 1. Update users table (ignore errors if columns already exist)
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN account_type VARCHAR(20) DEFAULT 'ORGANIZATION'")
            print("Added account_type to users")
        except Exception as e:
            print(f"Skipped adding account_type: {e}")
        
        try:
            cursor.execute("ALTER TABLE users MODIFY org_id VARCHAR(36) NULL")
            cursor.execute("ALTER TABLE users MODIFY role_id VARCHAR(36) NULL")
            print("Made org_id and role_id nullable")
        except Exception as e:
            print(f"Skipped modifying columns: {e}")

        # Update superadmin
        cursor.execute("UPDATE users SET account_type = 'SUPER_ADMIN' WHERE email = 'superadmin@ratan.com'")
        
        # 2. Create Personal AI Tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS personal_chats (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                title VARCHAR(255) NOT NULL,
                llm_model VARCHAR(100) NOT NULL,
                created_at DOUBLE NOT NULL,
                updated_at DOUBLE NOT NULL,
                deleted_at DOUBLE,
                is_pinned INT DEFAULT 0,
                metadata TEXT,
                status VARCHAR(50) DEFAULT 'ACTIVE',
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        print("Created personal_chats")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS personal_messages (
                id VARCHAR(36) PRIMARY KEY,
                session_id VARCHAR(36) NOT NULL,
                parent_id VARCHAR(36),
                role VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                citations TEXT,
                tokens_used INT DEFAULT 0,
                latency_ms INT DEFAULT 0,
                created_at DOUBLE NOT NULL,
                updated_at DOUBLE NOT NULL,
                FOREIGN KEY (session_id) REFERENCES personal_chats(id) ON DELETE CASCADE
            )
        ''')
        print("Created personal_messages")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS personal_files (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                filename VARCHAR(255) NOT NULL,
                storage_path VARCHAR(255) NOT NULL,
                mime_type VARCHAR(100),
                file_size INT NOT NULL,
                chunk_count INT DEFAULT 0,
                vector_count INT DEFAULT 0,
                status VARCHAR(50) DEFAULT 'READY',
                created_at DOUBLE NOT NULL,
                updated_at DOUBLE NOT NULL,
                deleted_at DOUBLE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        print("Created personal_files")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS personal_memories (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                memory_type VARCHAR(100) NOT NULL,
                content TEXT NOT NULL,
                created_at DOUBLE NOT NULL,
                updated_at DOUBLE NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        print("Created personal_memories")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS personal_settings (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL UNIQUE,
                preferred_model VARCHAR(100) DEFAULT 'gpt-4o',
                memory_enabled INT DEFAULT 1,
                system_prompt TEXT,
                created_at DOUBLE NOT NULL,
                updated_at DOUBLE NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        print("Created personal_settings")

        conn.commit()
        print("Migration complete!")
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()

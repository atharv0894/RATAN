import os
import pymysql
import uuid
import time
from dotenv import load_dotenv

load_dotenv()

def create_tidb_schema():
    print("Connecting to TiDB to create schema...")
    conn = pymysql.connect(
        host=os.environ.get("TIDB_HOST"),
        port=int(os.environ.get("TIDB_PORT", 4000)),
        user=os.environ.get("TIDB_USER"),
        password=os.environ.get("TIDB_PASSWORD"),
        ssl_verify_cert=True,
        ssl_verify_identity=True
    )
    cursor = conn.cursor()

    # Create our own database and switch to it
    cursor.execute("CREATE DATABASE IF NOT EXISTS ratan_db")
    cursor.execute("USE ratan_db")
    
    # 1. Organizations
    cursor.execute('''
        CREATE TABLE organizations (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(255) UNIQUE NOT NULL,
            created_at DOUBLE NOT NULL,
            updated_at DOUBLE NOT NULL,
            is_deleted INT DEFAULT 0,
            status VARCHAR(50) DEFAULT 'Active'
        )
    ''')
    
    # 2. Plants
    cursor.execute('''
        CREATE TABLE plants (
            id VARCHAR(36) PRIMARY KEY,
            org_id VARCHAR(36) NOT NULL,
            name VARCHAR(255) NOT NULL,
            location TEXT,
            created_at DOUBLE NOT NULL,
            updated_at DOUBLE NOT NULL,
            is_deleted INT DEFAULT 0,
            status VARCHAR(50) DEFAULT 'Active',
            FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE RESTRICT
        )
    ''')
    
    # 3. Departments
    cursor.execute('''
        CREATE TABLE departments (
            id VARCHAR(36) PRIMARY KEY,
            plant_id VARCHAR(36) NOT NULL,
            name VARCHAR(255) NOT NULL,
            created_at DOUBLE NOT NULL,
            updated_at DOUBLE NOT NULL,
            is_deleted INT DEFAULT 0,
            status VARCHAR(50) DEFAULT 'Active',
            FOREIGN KEY (plant_id) REFERENCES plants(id) ON DELETE RESTRICT
        )
    ''')
    
    # 4. Roles
    cursor.execute('''
        CREATE TABLE roles (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(255) UNIQUE NOT NULL,
            permissions TEXT NOT NULL,
            created_at DOUBLE NOT NULL,
            updated_at DOUBLE NOT NULL,
            is_deleted INT DEFAULT 0,
            status VARCHAR(50) DEFAULT 'Active'
        )
    ''')
    
    # 5. Users
    cursor.execute('''
        CREATE TABLE users (
            id VARCHAR(36) PRIMARY KEY,
            org_id VARCHAR(36) NOT NULL,
            plant_id VARCHAR(36),
            department_id VARCHAR(36),
            role_id VARCHAR(36) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            created_at DOUBLE NOT NULL,
            updated_at DOUBLE NOT NULL,
            is_deleted INT DEFAULT 0,
            status VARCHAR(50) DEFAULT 'Active',
            FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE RESTRICT,
            FOREIGN KEY (plant_id) REFERENCES plants(id) ON DELETE SET NULL,
            FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL,
            FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT
        )
    ''')
    
    # 6. Documents
    cursor.execute('''
        CREATE TABLE documents (
            id VARCHAR(36) PRIMARY KEY,
            title TEXT NOT NULL,
            filename VARCHAR(255) NOT NULL,
            description TEXT,
            category VARCHAR(100),
            equipment VARCHAR(100),
            language VARCHAR(50),
            author VARCHAR(255),
            owner VARCHAR(36) NOT NULL,
            organization VARCHAR(36) NOT NULL,
            plant VARCHAR(36) NOT NULL,
            department VARCHAR(36) NOT NULL,
            created_at DOUBLE NOT NULL,
            updated_at DOUBLE NOT NULL,
            deleted_at DOUBLE,
            deleted_by_user_id VARCHAR(36),
            delete_reason TEXT,
            status VARCHAR(50) DEFAULT 'READY',
            FOREIGN KEY (deleted_by_user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    ''')
    
    # 7. Document Versions
    cursor.execute('''
        CREATE TABLE document_versions (
            id VARCHAR(36) PRIMARY KEY,
            document_id VARCHAR(36) NOT NULL,
            version_number INT NOT NULL,
            checksum VARCHAR(255) NOT NULL,
            storage_path TEXT NOT NULL,
            collection_name VARCHAR(255) NOT NULL,
            uploaded_by_user_id VARCHAR(36) NOT NULL,
            uploaded_at DOUBLE NOT NULL,
            mime_type VARCHAR(100),
            file_size INT NOT NULL,
            embedding_model VARCHAR(100) NOT NULL,
            chunk_count INT NOT NULL,
            vector_count INT NOT NULL,
            is_latest INT DEFAULT 0,
            status VARCHAR(50) DEFAULT 'READY',
            locked_at DOUBLE,
            locked_by_user_id VARCHAR(36),
            lock_reason TEXT,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY (uploaded_by_user_id) REFERENCES users(id) ON DELETE RESTRICT,
            FOREIGN KEY (locked_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
            UNIQUE(document_id, version_number)
        )
    ''')
    
    # 8. Document Tags
    cursor.execute('''
        CREATE TABLE document_tags (
            id VARCHAR(36) PRIMARY KEY,
            document_id VARCHAR(36) NOT NULL,
            tag_name VARCHAR(100) NOT NULL,
            created_at DOUBLE NOT NULL,
            updated_at DOUBLE NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            UNIQUE(document_id, tag_name)
        )
    ''')
    
    # 10. Chat Sessions
    cursor.execute('''
        CREATE TABLE chat_sessions (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL,
            title TEXT NOT NULL,
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
    
    # 11. Chat Messages
    cursor.execute('''
        CREATE TABLE chat_messages (
            id VARCHAR(36) PRIMARY KEY,
            session_id VARCHAR(36) NOT NULL,
            parent_id VARCHAR(36),
            role VARCHAR(50) NOT NULL,
            content TEXT NOT NULL,
            citations TEXT,
            follow_up_questions TEXT,
            search_filters TEXT,
            confidence_score DOUBLE,
            tokens_used INT DEFAULT 0,
            latency_ms INT DEFAULT 0,
            created_at DOUBLE NOT NULL,
            updated_at DOUBLE NOT NULL,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
        )
    ''')
    
    # 12. Feedback
    cursor.execute('''
        CREATE TABLE feedback (
            id VARCHAR(36) PRIMARY KEY,
            message_id VARCHAR(36) NOT NULL,
            user_id VARCHAR(36) NOT NULL,
            rating INT NOT NULL,
            issue_category VARCHAR(100),
            comments TEXT,
            created_at DOUBLE NOT NULL,
            updated_at DOUBLE NOT NULL,
            FOREIGN KEY (message_id) REFERENCES chat_messages(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # 13. Audit Logs
    cursor.execute('''
        CREATE TABLE audit_logs (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36),
            endpoint TEXT,
            action VARCHAR(100) NOT NULL,
            resource TEXT NOT NULL,
            status VARCHAR(50) NOT NULL,
            ip_address VARCHAR(100),
            execution_time_ms INT,
            created_at DOUBLE NOT NULL,
            updated_at DOUBLE NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    ''')
    
    # 14. Processing Jobs
    cursor.execute('''
        CREATE TABLE processing_jobs (
            id VARCHAR(36) PRIMARY KEY,
            target_type VARCHAR(100) NOT NULL,
            target_id VARCHAR(36) NOT NULL,
            status VARCHAR(50) NOT NULL,
            started_at DOUBLE,
            finished_at DOUBLE,
            retry_count INT DEFAULT 0,
            error_message TEXT,
            created_at DOUBLE NOT NULL,
            updated_at DOUBLE NOT NULL
        )
    ''')
    
    # 15. System Settings
    cursor.execute('''
        CREATE TABLE system_settings (
            id VARCHAR(36) PRIMARY KEY,
            setting_key VARCHAR(100) UNIQUE NOT NULL,
            setting_value TEXT NOT NULL,
            created_at DOUBLE NOT NULL,
            updated_at DOUBLE NOT NULL
        )
    ''')
    
    # 16. User Sessions
    cursor.execute('''
        CREATE TABLE user_sessions (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL,
            refresh_token VARCHAR(255) UNIQUE NOT NULL,
            ip_address VARCHAR(100),
            device_info TEXT,
            expires_at DOUBLE NOT NULL,
            last_activity DOUBLE NOT NULL,
            created_at DOUBLE NOT NULL,
            is_revoked INT DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # 17. Password Reset Tokens
    cursor.execute('''
        CREATE TABLE password_reset_tokens (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL,
            token VARCHAR(255) UNIQUE NOT NULL,
            expires_at DOUBLE NOT NULL,
            created_at DOUBLE NOT NULL,
            is_used INT DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Indexes
    cursor.execute("CREATE INDEX idx_doc_filename ON documents(filename)")
    cursor.execute("CREATE INDEX idx_doc_deleted_at ON documents(deleted_at)")
    cursor.execute("CREATE INDEX idx_doc_ver_doc_id ON document_versions(document_id)")
    cursor.execute("CREATE INDEX idx_doc_ver_checksum ON document_versions(checksum)")
    cursor.execute("CREATE INDEX idx_doc_ver_status ON document_versions(status)")
    cursor.execute("CREATE INDEX idx_users_email ON users(email)")
    cursor.execute("CREATE INDEX idx_chat_msg_session ON chat_messages(session_id)")
    cursor.execute("CREATE INDEX idx_jobs_status ON processing_jobs(status)")
    cursor.execute("CREATE INDEX idx_user_sessions_user ON user_sessions(user_id)")
    cursor.execute("CREATE INDEX idx_user_sessions_token ON user_sessions(refresh_token)")

    # Seed initial SuperAdmin role for testing
    now = time.time()
    system_role_id = str(uuid.uuid4())
    cursor.execute("INSERT IGNORE INTO roles (id, name, permissions, created_at, updated_at) VALUES (%s, 'SuperAdmin', '{\"all\": true}', %s, %s)",
                   (system_role_id, now, now))
    cursor.execute("INSERT IGNORE INTO roles (id, name, permissions, created_at, updated_at) VALUES (%s, 'Admin', '*', %s, %s)",
                   (str(uuid.uuid4()), now, now))
                   
    conn.commit()
    print("✅ Schema created successfully on TiDB!")
    conn.close()

if __name__ == "__main__":
    create_tidb_schema()

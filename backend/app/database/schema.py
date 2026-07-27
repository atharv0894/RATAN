import sqlite3

def create_schema(cursor: sqlite3.Cursor):
    """Creates the V2 Enterprise Database Schema."""
    
    # 1. Organizations
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS organizations (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at BIGINT NOT NULL,
            updated_at BIGINT NOT NULL,
            is_deleted INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Active'
        )
    ''')
    
    # 2. Plants
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plants (
            id TEXT PRIMARY KEY,
            org_id TEXT NOT NULL,
            name TEXT NOT NULL,
            location TEXT,
            created_at BIGINT NOT NULL,
            updated_at BIGINT NOT NULL,
            is_deleted INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Active',
            FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE RESTRICT
        )
    ''')
    
    # 3. Departments
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id TEXT PRIMARY KEY,
            plant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at BIGINT NOT NULL,
            updated_at BIGINT NOT NULL,
            is_deleted INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Active',
            FOREIGN KEY (plant_id) REFERENCES plants(id) ON DELETE RESTRICT
        )
    ''')
    
    # 4. Roles
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id TEXT PRIMARY KEY,
            org_id TEXT,
            name TEXT NOT NULL,
            permissions TEXT NOT NULL,
            created_at BIGINT NOT NULL,
            updated_at BIGINT NOT NULL,
            is_deleted INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Active',
            UNIQUE(org_id, name)
        )
    ''')
    
    # 5. Users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            account_type TEXT DEFAULT 'ORGANIZATION',
            org_id TEXT,
            plant_id TEXT,
            department_id TEXT,
            role_id TEXT,
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            failed_login_attempts INTEGER DEFAULT 0,
            locked_until BIGINT,
            email_verified INTEGER DEFAULT 0,
            is_verified INTEGER DEFAULT 0,
            email_verified_at BIGINT,
            verification_token TEXT,
            verification_token_expires_at BIGINT,
            provider VARCHAR(20) DEFAULT 'LOCAL',
            google_id VARCHAR(255),
            profile_picture TEXT,
            last_google_login DOUBLE,
            provider_account_id VARCHAR(255),
            created_at BIGINT NOT NULL,
            updated_at BIGINT NOT NULL,
            is_deleted INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Active',
            FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE RESTRICT,
            FOREIGN KEY (plant_id) REFERENCES plants(id) ON DELETE SET NULL,
            FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL,
            FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT
        )
    ''')
    
    # 5a. Personal AI Tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS personal_chats (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            llm_model TEXT NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            deleted_at REAL,
            is_pinned INTEGER DEFAULT 0,
            metadata TEXT,
            status TEXT DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'ARCHIVED', 'DELETED')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS personal_messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            parent_id TEXT,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
            content TEXT NOT NULL,
            citations TEXT,
            tokens_used INTEGER DEFAULT 0,
            latency_ms INTEGER DEFAULT 0,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            FOREIGN KEY (session_id) REFERENCES personal_chats(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS personal_files (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            storage_path TEXT NOT NULL,
            mime_type TEXT,
            file_size INTEGER NOT NULL,
            chunk_count INTEGER DEFAULT 0,
            vector_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'READY',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            deleted_at REAL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS personal_memories (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            memory_type TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS personal_settings (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL UNIQUE,
            preferred_model TEXT DEFAULT 'gpt-4o',
            memory_enabled INTEGER DEFAULT 1,
            system_prompt TEXT,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # 6. Documents
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            filename TEXT NOT NULL,
            description TEXT,
            category TEXT,
            equipment TEXT,
            language TEXT,
            author TEXT,
            owner TEXT NOT NULL,
            organization TEXT NOT NULL,
            plant TEXT NOT NULL,
            department TEXT NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            deleted_at REAL,
            deleted_by_user_id TEXT,
            delete_reason TEXT,
            status TEXT DEFAULT 'READY',
            FOREIGN KEY (deleted_by_user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    ''')
    
    # 7. Document Versions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_versions (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            version_number INTEGER NOT NULL,
            checksum TEXT NOT NULL,
            storage_path TEXT NOT NULL,
            collection_name TEXT NOT NULL,
            uploaded_by_user_id TEXT NOT NULL,
            uploaded_at REAL NOT NULL,
            mime_type TEXT,
            file_size INTEGER NOT NULL,
            embedding_model TEXT NOT NULL,
            chunk_count INTEGER NOT NULL,
            vector_count INTEGER NOT NULL,
            is_latest INTEGER DEFAULT 0,
            status TEXT DEFAULT 'READY',
            locked_at REAL,
            locked_by_user_id TEXT,
            lock_reason TEXT,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY (uploaded_by_user_id) REFERENCES users(id) ON DELETE RESTRICT,
            FOREIGN KEY (locked_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
            UNIQUE(document_id, version_number)
        )
    ''')
    
    # 8. Document Tags
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_tags (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            tag_name TEXT NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            UNIQUE(document_id, tag_name)
        )
    ''')
    

    
    # 10. Chat Sessions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            llm_model TEXT NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            deleted_at REAL,
            is_pinned INTEGER DEFAULT 0,
            metadata TEXT,
            status TEXT DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'ARCHIVED', 'DELETED')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # 11. Chat Messages
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            parent_id TEXT,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
            content TEXT NOT NULL,
            citations TEXT,
            follow_up_questions TEXT,
            search_filters TEXT,
            confidence_score REAL,
            tokens_used INTEGER DEFAULT 0,
            latency_ms INTEGER DEFAULT 0,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
        )
    ''')
    
    # 12. Feedback
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id TEXT PRIMARY KEY,
            message_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK(rating IN (-1, 0, 1)),
            issue_category TEXT,
            comments TEXT,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            FOREIGN KEY (message_id) REFERENCES chat_messages(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # 13. Audit Logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            endpoint TEXT,
            action TEXT NOT NULL,
            resource TEXT NOT NULL,
            status TEXT NOT NULL,
            ip_address TEXT,
            execution_time_ms INTEGER,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    ''')
    
    # 14. Processing Jobs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processing_jobs (
            id TEXT PRIMARY KEY,
            target_type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('QUEUED', 'PROCESSING', 'EMBEDDING', 'INDEXING', 'COMPLETED', 'FAILED', 'CANCELLED')),
            started_at REAL,
            finished_at REAL,
            retry_count INTEGER DEFAULT 0,
            error_message TEXT,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )
    ''')
    
    # 15. System Settings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            id TEXT PRIMARY KEY,
            setting_key TEXT UNIQUE NOT NULL,
            setting_value TEXT NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )
    ''')
    
    # 16. User Sessions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            refresh_token_hash TEXT UNIQUE NOT NULL,
            ip_address TEXT,
            device_info TEXT,
            expires_at BIGINT NOT NULL,
            last_activity BIGINT NOT NULL,
            created_at BIGINT NOT NULL,
            is_revoked INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # 17. Password Reset Tokens
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            token_hash TEXT UNIQUE NOT NULL,
            expires_at BIGINT NOT NULL,
            created_at BIGINT NOT NULL,
            is_used INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_filename ON documents(filename)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_deleted_at ON documents(deleted_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_ver_doc_id ON document_versions(document_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_ver_checksum ON document_versions(checksum)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_ver_status ON document_versions(status)")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE is_deleted = 0")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_orgs_name ON organizations(name) WHERE is_deleted = 0")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_msg_session ON chat_messages(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON processing_jobs(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(refresh_token_hash)")

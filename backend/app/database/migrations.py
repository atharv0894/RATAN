import sqlite3
import logging
import uuid
import time

def run_migrations(conn: sqlite3.Connection):
    cursor = conn.cursor()
    
    # Check if we need to migrate from V1 (has old documents table but no document_versions)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='document_versions'")
    if cursor.fetchone():
        logging.info("Database is already up to date. Checking for Phase 2 & 4 updates...")
        
        # Phase 2: Documents
        cursor.execute("PRAGMA table_info(documents)")
        columns = [info['name'] for info in cursor.fetchall()]
        if 'description' not in columns:
            cursor.execute("ALTER TABLE documents ADD COLUMN description TEXT")
            cursor.execute("ALTER TABLE documents ADD COLUMN category TEXT")
            cursor.execute("ALTER TABLE documents ADD COLUMN equipment TEXT")
            cursor.execute("ALTER TABLE documents ADD COLUMN language TEXT")
            cursor.execute("ALTER TABLE documents ADD COLUMN author TEXT")
            logging.info("Added Phase 2 Knowledge Base metadata columns.")
            
        # Phase 4: Chat Messages
        cursor.execute("PRAGMA table_info(chat_messages)")
        chat_msg_columns = [info['name'] for info in cursor.fetchall()]
        if 'parent_id' not in chat_msg_columns:
            cursor.execute("ALTER TABLE chat_messages ADD COLUMN parent_id TEXT")
            cursor.execute("ALTER TABLE chat_messages ADD COLUMN follow_up_questions TEXT")
            cursor.execute("ALTER TABLE chat_messages ADD COLUMN search_filters TEXT")
            cursor.execute("ALTER TABLE chat_messages ADD COLUMN confidence_score REAL")
            logging.info("Added Phase 4 Chat Message columns.")
            
        # Phase 4: Chat Sessions
        cursor.execute("PRAGMA table_info(chat_sessions)")
        chat_sess_columns = [info['name'] for info in cursor.fetchall()]
        if 'is_pinned' not in chat_sess_columns:
            cursor.execute("ALTER TABLE chat_sessions ADD COLUMN deleted_at REAL")
            cursor.execute("ALTER TABLE chat_sessions ADD COLUMN is_pinned INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE chat_sessions ADD COLUMN metadata TEXT")
            # We can't drop is_deleted easily in SQLite, so we just add the new ones
            logging.info("Added Phase 4 Chat Session columns.")
            
        # Phase 4: Feedback
        cursor.execute("PRAGMA table_info(feedback)")
        feedback_columns = [info['name'] for info in cursor.fetchall()]
        if 'issue_category' not in feedback_columns:
            cursor.execute("ALTER TABLE feedback ADD COLUMN issue_category TEXT")
            logging.info("Added Phase 4 Feedback columns.")
            
        # Phase 5 (V3): Security & Soft Delete Refactor
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [info['name'] for info in cursor.fetchall()]
        if 'failed_login_attempts' not in user_columns:
            logging.info("Starting Phase 5 / V3 Database Migration (Security & Soft Deletes)...")
            
            # 1. Rename existing tables
            cursor.execute("ALTER TABLE users RENAME TO legacy_v2_users")
            cursor.execute("ALTER TABLE roles RENAME TO legacy_v2_roles")
            cursor.execute("ALTER TABLE organizations RENAME TO legacy_v2_organizations")
            
            # 2. Re-create V3 Schema (so it drops constraints and creates new ones)
            from app.database.schema import create_schema
            create_schema(cursor)
            
            # 3. Migrate Organizations
            cursor.execute("""
                INSERT INTO organizations (id, name, created_at, updated_at, is_deleted, status)
                SELECT id, name, created_at, updated_at, is_deleted, status FROM legacy_v2_organizations
            """)
            
            # 4. Migrate Roles (Injecting NULL for org_id initially)
            cursor.execute("""
                INSERT INTO roles (id, org_id, name, permissions, created_at, updated_at, is_deleted, status)
                SELECT id, NULL, name, permissions, created_at, updated_at, is_deleted, status FROM legacy_v2_roles
            """)
            
            # 5. Migrate Users
            cursor.execute("""
                INSERT INTO users (
                    id, org_id, plant_id, department_id, role_id, email, password_hash, full_name, 
                    failed_login_attempts, locked_until, email_verified, created_at, updated_at, is_deleted, status
                )
                SELECT 
                    id, org_id, plant_id, department_id, role_id, email, password_hash, full_name, 
                    0, NULL, 0, created_at, updated_at, is_deleted, status 
                FROM legacy_v2_users
            """)
            
            # 6. Drop legacy tables
            cursor.execute("DROP TABLE legacy_v2_users")
            cursor.execute("DROP TABLE legacy_v2_roles")
            cursor.execute("DROP TABLE legacy_v2_organizations")
            
            # 7. Rename Columns (Requires SQLite 3.25.0+)
            try:
                cursor.execute("ALTER TABLE user_sessions RENAME COLUMN refresh_token TO refresh_token_hash")
                cursor.execute("ALTER TABLE password_reset_tokens RENAME COLUMN token TO token_hash")
            except Exception as e:
                logging.warning(f"Failed to rename token columns directly (might be using old SQLite): {e}")
                
            logging.info("Phase 5 Migration complete.")

        conn.commit()
        return
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
    if not cursor.fetchone():
        logging.info("Fresh database, creating schema...")
        from app.database.schema import create_schema
        create_schema(cursor)
        conn.commit()
        return

    logging.info("Starting V1 to V2 database migration...")
    
    # 1. Create temporary tables for old data
    cursor.execute("ALTER TABLE documents RENAME TO legacy_documents")
    try:
        cursor.execute("ALTER TABLE entities RENAME TO legacy_entities")
    except Exception:
        pass
        
    try:
        cursor.execute("ALTER TABLE audit_logs RENAME TO legacy_audit_logs")
    except Exception:
        pass

    # 2. Create V2 Schema
    from app.database.schema import create_schema
    create_schema(cursor)
    
    # 3. Seed base organizational data for FK constraints (Not strictly needed for documents now, but good for users)
    system_org_id = str(uuid.uuid4())
    system_plant_id = str(uuid.uuid4())
    system_dept_id = str(uuid.uuid4())
    system_user_id = str(uuid.uuid4())
    system_role_id = str(uuid.uuid4())
    
    now = time.time()
    
    cursor.execute("INSERT INTO organizations (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                   (system_org_id, 'System Organization', now, now))
    cursor.execute("INSERT INTO plants (id, org_id, name, location, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                   (system_plant_id, system_org_id, 'System Plant', 'Virtual', now, now))
    cursor.execute("INSERT INTO departments (id, plant_id, name, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                   (system_dept_id, system_plant_id, 'System Dept', now, now))
    cursor.execute("INSERT INTO roles (id, name, permissions, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                   (system_role_id, 'SYSTEM_ADMIN', '{"all": true}', now, now))
    cursor.execute("INSERT INTO users (id, org_id, role_id, email, password_hash, full_name, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (system_user_id, system_org_id, system_role_id, 'system@ratan.local', 'none', 'System Admin', now, now))

    # 4. Migrate Documents -> documents + document_versions
    cursor.execute("SELECT * FROM legacy_documents")
    legacy_docs = cursor.fetchall()
    
    doc_map = {}
    version_counter = {}
    
    for ldoc in legacy_docs:
        ldoc_dict = dict(ldoc)
        filename = ldoc_dict['filename']
        if filename not in doc_map:
            doc_id = str(uuid.uuid4())
            doc_map[filename] = doc_id
            version_counter[doc_id] = 1
            
            deleted_at = ldoc_dict['upload_time'] if ldoc_dict.get('is_deleted', 0) else None
            deleted_by = system_user_id if deleted_at else None
            delete_reason = "Legacy Migration" if deleted_at else None
            doc_status = "DELETED" if deleted_at else "READY"
            
            cursor.execute("""
                INSERT INTO documents (
                    id, title, filename, owner, organization, plant, department, 
                    created_at, updated_at, deleted_at, deleted_by_user_id, delete_reason, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id, filename, filename, system_user_id, system_org_id, system_plant_id, system_dept_id,
                ldoc_dict['upload_time'], ldoc_dict['upload_time'], deleted_at, deleted_by, delete_reason, doc_status
            ))
        else:
            doc_id = doc_map[filename]
            version_counter[doc_id] += 1
        
        # Insert Version
        version_id = ldoc_dict['document_id']
        is_locked = ldoc_dict.get('is_locked', 0)
        locked_at = ldoc_dict['upload_time'] if is_locked else None
        locked_by = system_user_id if is_locked else None
        lock_reason = "Legacy Lock" if is_locked else None
        
        ver_status = "DELETED" if ldoc_dict.get('is_deleted', 0) else "READY"
        
        cursor.execute("""
            INSERT OR IGNORE INTO document_versions (
                id, document_id, version_number, checksum, storage_path, collection_name,
                uploaded_by_user_id, uploaded_at, mime_type, file_size, embedding_model, chunk_count,
                vector_count, is_latest, status, locked_at, locked_by_user_id, lock_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            version_id, doc_id, version_counter[doc_id], ldoc_dict.get('checksum_sha256', ''), 
            ldoc_dict.get('storage_path', ''), ldoc_dict.get('vector_db', 'default'),
            system_user_id, ldoc_dict['upload_time'],
            ldoc_dict.get('mime_type', 'application/pdf'), ldoc_dict.get('file_size', 0), ldoc_dict.get('embedding_model', 'default'),
            ldoc_dict.get('chunk_count', 0), ldoc_dict.get('chunk_count', 0), ldoc_dict.get('is_latest', 1), ver_status,
            locked_at, locked_by, lock_reason
        ))

    # 5. Migrate Audit Logs
    try:
        cursor.execute("SELECT * FROM legacy_audit_logs")
        legacy_logs = cursor.fetchall()
        for log in legacy_logs:
            cursor.execute("""
                INSERT INTO audit_logs (
                    id, user_id, endpoint, action, resource, status, ip_address, execution_time_ms,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log['log_id'], system_user_id, 'SYSTEM', log['action'], log['document_id'], 
                log['status'], '127.0.0.1', 0, log['timestamp'], log['timestamp']
            ))
    except sqlite3.OperationalError:
        pass
        
    # 6. Drop legacy tables
    cursor.execute("DROP TABLE legacy_documents")
    try:
        cursor.execute("DROP TABLE legacy_entities")
    except Exception:
        pass
    try:
        cursor.execute("DROP TABLE legacy_audit_logs")
    except Exception:
        pass

    conn.commit()
    logging.info("Database successfully migrated to V2.")

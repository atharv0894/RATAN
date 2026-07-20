import sqlite3
import logging
import uuid
import time

def run_migrations(conn: sqlite3.Connection):
    cursor = conn.cursor()
    
    # Check if we need to migrate from V1 (has old documents table but no document_versions)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='document_versions'")
    if cursor.fetchone():
        logging.info("Database is already up to date.")
        return
        
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
    if not cursor.fetchone():
        logging.info("Fresh database, no migration needed.")
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
    
    for ldoc in legacy_docs:
        filename = ldoc['filename']
        if filename not in doc_map:
            doc_id = str(uuid.uuid4())
            doc_map[filename] = doc_id
            
            deleted_at = ldoc['upload_time'] if ldoc.get('is_deleted', 0) else None
            
            cursor.execute("""
                INSERT INTO documents (
                    id, title, filename, owner, organization, plant, department, 
                    created_at, updated_at, deleted_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id, filename, filename, system_user_id, system_org_id, system_plant_id, system_dept_id,
                ldoc['upload_time'], ldoc['upload_time'], deleted_at, 'Active'
            ))
        
        doc_id = doc_map[filename]
        
        # Insert Version
        version_id = ldoc['document_id']
        cursor.execute("""
            INSERT INTO document_versions (
                id, document_id, version_number, checksum, storage_path, collection_name,
                uploaded_by, uploaded_at, mime_type, file_size, embedding_model, chunk_count,
                vector_count, is_latest, status, is_locked
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            version_id, doc_id, ldoc.get('version_number', 1), ldoc.get('checksum_sha256', ''), 
            ldoc.get('storage_path', ''), ldoc.get('vector_db', 'default'),
            system_user_id, ldoc['upload_time'],
            ldoc.get('mime_type', 'application/pdf'), ldoc.get('file_size', 0), ldoc['embedding_model'],
            ldoc['chunk_count'], ldoc['chunk_count'], ldoc.get('is_latest', 1), ldoc['status'], ldoc.get('is_locked', 0)
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

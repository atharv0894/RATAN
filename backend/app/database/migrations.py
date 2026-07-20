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
    
    # 3. Seed base organizational data for FK constraints
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
    
    # To group versions of the same file, we need a map of filename -> new document_id
    doc_map = {}
    
    for ldoc in legacy_docs:
        filename = ldoc['filename']
        if filename not in doc_map:
            doc_id = str(uuid.uuid4())
            doc_map[filename] = doc_id
            cursor.execute("""
                INSERT INTO documents (
                    id, org_id, plant_id, department_id, owner_id, title, filename, 
                    document_type, language, equipment, created_at, updated_at, is_deleted, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id, system_org_id, system_plant_id, system_dept_id, system_user_id,
                filename, filename, ldoc.get('document_class', 'Unknown'), 'en', 'Unknown',
                ldoc['upload_time'], ldoc['upload_time'], ldoc['is_deleted'], 'Active'
            ))
        
        doc_id = doc_map[filename]
        
        # Insert Version
        version_id = ldoc['document_id'] # Use the original document_id as the version_id to preserve relationships
        cursor.execute("""
            INSERT INTO document_versions (
                id, document_id, version_number, uploaded_by, storage_provider, storage_path,
                mime_type, file_size, checksum, page_count, chunk_count, embedding_model,
                vector_collection, vector_count, is_latest, previous_version_id, created_at, updated_at,
                is_deleted, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            version_id, doc_id, ldoc.get('version_number', 1), system_user_id, 
            ldoc.get('storage_provider', 'local'), ldoc.get('storage_path', ''),
            ldoc.get('mime_type', 'application/pdf'), ldoc.get('file_size', 0), ldoc.get('checksum_sha256', ''),
            ldoc.get('page_count', 0), ldoc['chunk_count'], ldoc['embedding_model'],
            ldoc['vector_db'], ldoc['chunk_count'], ldoc.get('is_latest', 1), 
            ldoc.get('previous_version', None), ldoc['upload_time'], ldoc['upload_time'],
            ldoc['is_deleted'], ldoc['status']
        ))

    # 5. Migrate Entities -> document_chunks
    try:
        cursor.execute("SELECT * FROM legacy_entities")
        legacy_entities = cursor.fetchall()
        for l_ent in legacy_entities:
            # In V1, entities were mapped to legacy document_id (which is now version_id)
            cursor.execute("""
                INSERT INTO document_chunks (
                    id, version_id, chunk_index, content, page_number, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                l_ent['entity_id'], l_ent['document_id'], 0, l_ent['entity_value'], 
                l_ent.get('page_number', 1), l_ent['created_at'], l_ent['created_at']
            ))
    except sqlite3.OperationalError:
        pass

    # 6. Migrate Audit Logs
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
        
    # 7. Drop legacy tables
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

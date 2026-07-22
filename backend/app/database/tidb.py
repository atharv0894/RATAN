import os
import pymysql
import logging

class TiDBCursorWrapper:
    def __init__(self, cursor):
        self.cursor = cursor
        
    def execute(self, query, params=()):
        # Convert ? to %s for PyMySQL (MySQL syntax)
        converted_query = ""
        parts = query.split("'")
        for i in range(len(parts)):
            if i % 2 == 0:
                parts[i] = parts[i].replace("?", "%s")
        converted_query = "'".join(parts)
        
        # MySQL prefers INSERT IGNORE instead of INSERT OR IGNORE
        if "INSERT OR IGNORE" in converted_query:
            converted_query = converted_query.replace("INSERT OR IGNORE", "INSERT IGNORE")
            
        try:
            self.cursor.execute(converted_query, params)
        except Exception as e:
            logging.error(f"TiDB Query Failed: {converted_query} with params {params}. Error: {e}")
            raise e
        
    def fetchone(self):
        return self.cursor.fetchone()
        
    def fetchall(self):
        return self.cursor.fetchall()
        
    @property
    def lastrowid(self):
        return self.cursor.lastrowid
        
    @property
    def description(self):
        return self.cursor.description
        
    def close(self):
        self.cursor.close()

class TiDBConnectionWrapper:
    def __init__(self, conn):
        self.conn = conn
        
    def cursor(self):
        # We use DictCursor to mimic sqlite3.Row dict-like access
        return TiDBCursorWrapper(self.conn.cursor(pymysql.cursors.DictCursor))
        
    def commit(self):
        self.conn.commit()
        
    def rollback(self):
        self.conn.rollback()
        
    def close(self):
        self.conn.close()

    def execute(self, query, params=()):
        # Some legacy code might call conn.execute directly (like PRAGMA foreign_keys = ON)
        # We ignore PRAGMA statements for MySQL
        if "PRAGMA" in query.upper():
            return None
        cursor = self.cursor()
        cursor.execute(query, params)
        return cursor

def get_tidb_connection():
    conn = pymysql.connect(
        host=os.environ.get("TIDB_HOST"),
        port=int(os.environ.get("TIDB_PORT", 4000)),
        user=os.environ.get("TIDB_USER"),
        password=os.environ.get("TIDB_PASSWORD"),
        database=os.environ.get("TIDB_DATABASE", "ratan_db"),
        ssl_verify_cert=True,
        ssl_verify_identity=True
    )
    return TiDBConnectionWrapper(conn)

import uuid
import time
from typing import List
from app.database.sqlite import get_db_connection
from app.exceptions import DuplicateResourceError, NotFoundError

class OrganizationService:
    # -----------------------------
    # ORGANIZATIONS
    # -----------------------------
    @staticmethod
    def get_organization(org_id: str) -> dict:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, status, created_at FROM organizations WHERE id = ? AND is_deleted = 0", (org_id,))
        org = cursor.fetchone()
        conn.close()
        if not org:
            raise NotFoundError("Organization", org_id)
        return dict(org)

    @staticmethod
    def update_organization(org_id: str, data: dict) -> dict:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = time.time()
        
        if "name" in data:
            cursor.execute("UPDATE organizations SET name = ?, updated_at = ? WHERE id = ?", (data["name"], now, org_id))
        
        conn.commit()
        org = OrganizationService.get_organization(org_id)
        conn.close()
        return org

    # -----------------------------
    # PLANTS
    # -----------------------------
    @staticmethod
    def get_plants(org_id: str) -> List[dict]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, location, status FROM plants WHERE org_id = ? AND is_deleted = 0", (org_id,))
        plants = cursor.fetchall()
        conn.close()
        return [dict(p) for p in plants]
        
    @staticmethod
    def create_plant(org_id: str, data: dict) -> dict:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        plant_id = str(uuid.uuid4())
        now = time.time()
        
        cursor.execute(
            "INSERT INTO plants (id, org_id, name, location, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (plant_id, org_id, data["name"], data.get("location", ""), now, now)
        )
        conn.commit()
        conn.close()
        
        return {"id": plant_id, "name": data["name"], "location": data.get("location", ""), "status": "Active"}

    @staticmethod
    def update_plant(org_id: str, plant_id: str, data: dict) -> dict:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        fields = []
        values = []
        for k in ["name", "location", "status"]:
            if k in data and data[k] is not None:
                fields.append(f"{k} = ?")
                values.append(data[k])
                
        if fields:
            fields.append("updated_at = ?")
            values.append(time.time())
            values.extend([plant_id, org_id])
            
            cursor.execute(f"UPDATE plants SET {', '.join(fields)} WHERE id = ? AND org_id = ? AND is_deleted = 0", values)
            if cursor.rowcount == 0:
                conn.close()
                raise NotFoundError("Plant", plant_id)
            conn.commit()
            
        cursor.execute("SELECT id, name, location, status FROM plants WHERE id = ?", (plant_id,))
        plant = cursor.fetchone()
        conn.close()
        return dict(plant)

    @staticmethod
    def delete_plant(org_id: str, plant_id: str):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE plants SET is_deleted = 1, updated_at = ? WHERE id = ? AND org_id = ?", (time.time(), plant_id, org_id))
        if cursor.rowcount == 0:
            conn.close()
            raise NotFoundError("Plant", plant_id)
        conn.commit()
        conn.close()

    # -----------------------------
    # DEPARTMENTS
    # -----------------------------
    @staticmethod
    def get_departments(org_id: str, plant_id: str = None) -> List[dict]:
        conn = get_db_connection()
        cursor = conn.cursor()
        if plant_id:
            cursor.execute("""
                SELECT d.id, d.plant_id, d.name, d.status 
                FROM departments d JOIN plants p ON d.plant_id = p.id 
                WHERE p.org_id = ? AND d.plant_id = ? AND d.is_deleted = 0 AND p.is_deleted = 0
            """, (org_id, plant_id))
        else:
            cursor.execute("""
                SELECT d.id, d.plant_id, d.name, d.status 
                FROM departments d JOIN plants p ON d.plant_id = p.id 
                WHERE p.org_id = ? AND d.is_deleted = 0 AND p.is_deleted = 0
            """, (org_id,))
            
        deps = cursor.fetchall()
        conn.close()
        return [dict(d) for d in deps]

    @staticmethod
    def create_department(org_id: str, data: dict) -> dict:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify plant belongs to org
        cursor.execute("SELECT id FROM plants WHERE id = ? AND org_id = ? AND is_deleted = 0", (data["plant_id"], org_id))
        if not cursor.fetchone():
            conn.close()
            raise NotFoundError("Plant", data["plant_id"])
            
        dep_id = str(uuid.uuid4())
        now = time.time()
        
        cursor.execute(
            "INSERT INTO departments (id, plant_id, name, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (dep_id, data["plant_id"], data["name"], now, now)
        )
        conn.commit()
        conn.close()
        
        return {"id": dep_id, "plant_id": data["plant_id"], "name": data["name"], "status": "Active"}

    @staticmethod
    def delete_department(org_id: str, dep_id: str):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify dep belongs to a plant that belongs to org
        cursor.execute("""
            SELECT d.id FROM departments d JOIN plants p ON d.plant_id = p.id 
            WHERE d.id = ? AND p.org_id = ?
        """, (dep_id, org_id))
        if not cursor.fetchone():
            conn.close()
            raise NotFoundError("Department", dep_id)
            
        cursor.execute("UPDATE departments SET is_deleted = 1, updated_at = ? WHERE id = ?", (time.time(), dep_id))
        conn.commit()
        conn.close()

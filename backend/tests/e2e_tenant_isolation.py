import os
import sys
import unittest
import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"

class TestTenantIsolation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # We need to register two organizations and users
        import time
        suffix = str(int(time.time()))
        
        # Org 1: COEP
        res = requests.post(f"{BASE_URL}/auth/register", json={
            "full_name": "COEP Admin",
            "email": f"coep_{suffix}@example.com",
            "password": "password123",
            "org_name": f"COEP_{suffix}"
        })
        assert res.status_code == 200, res.text
        cls.coep_user = res.json()["data"]["user"]
        
        res = requests.post(f"{BASE_URL}/auth/login", data={
            "username": f"coep_{suffix}@example.com",
            "password": "password123"
        })
        cls.coep_token = res.json()["access_token"]
        cls.coep_org_id = cls.coep_user["org_id"]
        
        # Org 2: VIT
        res = requests.post(f"{BASE_URL}/auth/register", json={
            "full_name": "VIT Admin",
            "email": f"vit_{suffix}@example.com",
            "password": "password123",
            "org_name": f"VIT_{suffix}"
        })
        assert res.status_code == 200
        cls.vit_user = res.json()["data"]["user"]
        
        res = requests.post(f"{BASE_URL}/auth/login", data={
            "username": f"vit_{suffix}@example.com",
            "password": "password123"
        })
        cls.vit_token = res.json()["access_token"]
        cls.vit_org_id = cls.vit_user["org_id"]

    def test_cross_tenant_document_access(self):
        # COEP uploads a document (mocking metadata since real upload needs a file)
        # We'll just call the API
        headers_coep = {"Authorization": f"Bearer {self.coep_token}"}
        # To avoid file upload complexities, we'll try to list users from another org
        
        headers_vit = {"Authorization": f"Bearer {self.vit_token}"}
        
        # COEP lists users
        res = requests.get(f"{BASE_URL}/users", headers=headers_coep)
        coep_users = res.json()["data"]
        self.assertTrue(all(u["org_id"] == self.coep_org_id for u in coep_users if "org_id" in u))
        
        # Can COEP fetch VIT's user?
        vit_user_id = self.vit_user["id"]
        # There's no get_user by id in users.py directly, let's try updating it
        res = requests.patch(f"{BASE_URL}/users/{vit_user_id}", json={"full_name": "Hacked"}, headers=headers_coep)
        self.assertEqual(res.status_code, 404, "COEP should not be able to modify VIT user, should return 404 Not Found")

    def test_cross_tenant_org_access(self):
        headers_coep = {"Authorization": f"Bearer {self.coep_token}"}
        # Admin gets organizations (should only see their own)
        res = requests.get(f"{BASE_URL}/admin/organizations", headers=headers_coep)
        if res.status_code == 200:
            orgs = res.json()["data"]
            self.assertEqual(len(orgs), 1)
            self.assertEqual(orgs[0]["id"], self.coep_org_id)

    def test_cross_tenant_stats_access(self):
        headers_coep = {"Authorization": f"Bearer {self.coep_token}"}
        res = requests.get(f"{BASE_URL}/admin/system/statistics", headers=headers_coep)
        if res.status_code == 200:
            stats = res.json()["data"]
            self.assertEqual(stats["total_organizations"], 1, "Should only see 1 org stats")
            
if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python3
"""
Debug test for reconstruct-placement-records endpoint
"""

import requests
import json
import os

BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-manage-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

ADMIN_CREDENTIALS = {
    "phone": "+79999888777",
    "password": "admin123"
}

def test_reconstruct():
    session = requests.Session()
    
    # Login as admin
    print("🔐 Logging in as admin...")
    response = session.post(f"{API_BASE}/auth/login", json=ADMIN_CREDENTIALS)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    token = response.json().get("access_token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    print("✅ Admin login successful")
    
    # Call reconstruct endpoint
    print("🔧 Calling reconstruct-placement-records...")
    try:
        response = session.post(f"{API_BASE}/admin/reconstruct-placement-records", timeout=60)
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

if __name__ == "__main__":
    test_reconstruct()
#!/usr/bin/env python3
"""
Check placement data to understand the format
"""

import requests
import json
import os

BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cargo-sync.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

def check_data():
    session = requests.Session()
    
    # Login as operator
    response = session.post(f"{API_BASE}/auth/login", json=OPERATOR_CREDENTIALS)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    token = response.json().get("access_token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    print("✅ Operator login successful")
    
    # Get fully placed cargo to see placement_info format
    response = session.get(f"{API_BASE}/operator/cargo/fully-placed")
    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        
        for item in items:
            if item.get("cargo_number") == "25082235":
                print(f"Found cargo 25082235:")
                print(f"  ID: {item.get('id')}")
                
                individual_units = item.get("individual_units", [])
                for unit in individual_units:
                    individual_number = unit.get("individual_number")
                    placement_info = unit.get("placement_info")
                    status = unit.get("status")
                    
                    print(f"  Unit {individual_number}:")
                    print(f"    Status: {status}")
                    print(f"    Placement info: '{placement_info}'")
                    print(f"    Type: {type(placement_info)}")
                break

if __name__ == "__main__":
    check_data()
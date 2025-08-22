#!/usr/bin/env python3
"""
Check placement_records directly in the database
"""

import requests
import json
import os

BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-cargo-8.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

ADMIN_CREDENTIALS = {
    "phone": "+79999888777",
    "password": "admin123"
}

def check_placement_records():
    session = requests.Session()
    
    # Login as admin
    response = session.post(f"{API_BASE}/auth/login", json=ADMIN_CREDENTIALS)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    token = response.json().get("access_token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    print("✅ Admin login successful")
    
    # Try to get placement records (if there's a debug endpoint)
    response = session.get(f"{API_BASE}/admin/debug/placement-records")
    if response.status_code == 200:
        records = response.json()
        print(f"📊 Found {len(records)} placement records:")
        for record in records:
            print(f"  📦 Record:")
            print(f"    Individual number: {record.get('individual_number', 'N/A')}")
            print(f"    Cargo number: {record.get('cargo_number', 'N/A')}")
            print(f"    Location: {record.get('location', 'N/A')}")
            print(f"    Warehouse ID: {record.get('warehouse_id', 'N/A')}")
            print(f"    Block: {record.get('block_number', 'N/A')}")
            print(f"    Shelf: {record.get('shelf_number', 'N/A')}")
            print(f"    Cell: {record.get('cell_number', 'N/A')}")
            print(f"    Placed by: {record.get('placed_by_operator', 'N/A')}")
            print()
    else:
        print(f"❌ No debug endpoint available: {response.status_code}")
        
        # Try to call reconstruct again to see what it finds
        print("🔧 Calling reconstruct again to see current state...")
        response = session.post(f"{API_BASE}/admin/reconstruct-placement-records")
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Reconstruct results:")
            print(f"  Processed cargos: {data.get('processed_cargos', 0)}")
            print(f"  Reconstructed records: {data.get('reconstructed_records', 0)}")
            print(f"  Message: {data.get('message', 'N/A')}")
        else:
            print(f"❌ Reconstruct failed: {response.status_code}")

if __name__ == "__main__":
    check_placement_records()
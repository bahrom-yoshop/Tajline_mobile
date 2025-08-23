#!/usr/bin/env python3
"""
Check warehouse layout to see what cargo is placed where
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

def check_layout():
    session = requests.Session()
    
    # Login as operator
    response = session.post(f"{API_BASE}/auth/login", json=OPERATOR_CREDENTIALS)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    token = response.json().get("access_token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    print("✅ Operator login successful")
    
    # Get warehouse ID
    response = session.get(f"{API_BASE}/operator/warehouses")
    if response.status_code != 200:
        print(f"❌ Failed to get warehouses: {response.status_code}")
        return
    
    warehouses = response.json()
    warehouse_id = None
    for warehouse in warehouses:
        if "Москва Склад №1" in warehouse.get("name", ""):
            warehouse_id = warehouse.get("id")
            break
    
    if not warehouse_id:
        print("❌ Warehouse not found")
        return
    
    print(f"✅ Found warehouse ID: {warehouse_id}")
    
    # Get warehouse layout
    response = session.get(f"{API_BASE}/warehouses/{warehouse_id}/layout-with-cargo")
    if response.status_code != 200:
        print(f"❌ Failed to get layout: {response.status_code}")
        return
    
    data = response.json()
    layout = data.get("layout", {})
    
    print(f"📊 Warehouse stats:")
    print(f"  Total cells: {data.get('total_cells', 0)}")
    print(f"  Occupied cells: {data.get('occupied_cells', 0)}")
    print(f"  Total cargo: {data.get('total_cargo', 0)}")
    
    print(f"\n🔍 Searching for occupied cells...")
    
    for block_key, block_data in layout.items():
        if not isinstance(block_data, dict):
            continue
            
        shelves = block_data.get("shelves", {})
        for shelf_key, shelf_data in shelves.items():
            if not isinstance(shelf_data, dict):
                continue
                
            cells = shelf_data.get("cells", {})
            for cell_key, cell_data in cells.items():
                if not isinstance(cell_data, dict):
                    continue
                
                if cell_data.get("occupied", False):
                    cargo_info = cell_data.get("cargo", {})
                    print(f"  📦 Found occupied cell at Block {block_key}, Shelf {shelf_key}, Cell {cell_key}:")
                    print(f"    Cargo number: {cargo_info.get('cargo_number', 'N/A')}")
                    print(f"    Individual number: {cargo_info.get('individual_number', 'N/A')}")
                    print(f"    Sender: {cargo_info.get('sender_name', 'N/A')}")
                    print(f"    Recipient: {cargo_info.get('recipient_name', 'N/A')}")
                    print(f"    Placed by: {cargo_info.get('placed_by_operator', 'N/A')}")
                    print()

if __name__ == "__main__":
    check_layout()
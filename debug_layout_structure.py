#!/usr/bin/env python3
"""
Debug the actual layout structure returned by the API
"""

import requests
import json
import os

BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://placement-view.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

def debug_layout():
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
    warehouses = response.json()
    warehouse_id = None
    for warehouse in warehouses:
        if "Москва Склад №1" in warehouse.get("name", ""):
            warehouse_id = warehouse.get("id")
            break
    
    if not warehouse_id:
        print("❌ Warehouse not found")
        return
    
    # Get warehouse layout
    response = session.get(f"{API_BASE}/warehouses/{warehouse_id}/layout-with-cargo")
    if response.status_code != 200:
        print(f"❌ Failed to get layout: {response.status_code}")
        return
    
    data = response.json()
    
    print("📊 Layout structure:")
    print(f"  Keys: {list(data.keys())}")
    print(f"  Total cells: {data.get('total_cells', 0)}")
    print(f"  Occupied cells: {data.get('occupied_cells', 0)}")
    print(f"  Total cargo: {data.get('total_cargo', 0)}")
    
    layout = data.get("layout", {})
    print(f"\n🏗️ Layout structure:")
    print(f"  Layout keys: {list(layout.keys())}")
    
    blocks = layout.get("blocks", [])
    print(f"  Blocks type: {type(blocks)}")
    print(f"  Number of blocks: {len(blocks)}")
    
    if blocks:
        print(f"\n🔍 First block structure:")
        first_block = blocks[0]
        print(f"  Block keys: {list(first_block.keys())}")
        print(f"  Block number: {first_block.get('block_number')}")
        
        shelves = first_block.get("shelves", [])
        print(f"  Shelves type: {type(shelves)}")
        print(f"  Number of shelves: {len(shelves)}")
        
        if shelves:
            print(f"\n📚 First shelf structure:")
            first_shelf = shelves[0]
            print(f"  Shelf keys: {list(first_shelf.keys())}")
            print(f"  Shelf number: {first_shelf.get('shelf_number')}")
            
            cells = first_shelf.get("cells", [])
            print(f"  Cells type: {type(cells)}")
            print(f"  Number of cells: {len(cells)}")
            
            if cells:
                print(f"\n📦 First cell structure:")
                first_cell = cells[0]
                print(f"  Cell keys: {list(first_cell.keys())}")
                print(f"  Cell number: {first_cell.get('cell_number')}")
                print(f"  Is occupied: {first_cell.get('is_occupied')}")
                print(f"  Cargo: {first_cell.get('cargo')}")
    
    # Look for occupied cells
    print(f"\n🔍 Searching for occupied cells...")
    for block in blocks:
        block_num = block.get("block_number")
        shelves = block.get("shelves", [])
        
        for shelf in shelves:
            shelf_num = shelf.get("shelf_number")
            cells = shelf.get("cells", [])
            
            for cell in cells:
                cell_num = cell.get("cell_number")
                if cell.get("is_occupied", False):
                    cargo_list = cell.get("cargo", [])
                    print(f"  📦 Occupied cell at Block {block_num}, Shelf {shelf_num}, Cell {cell_num}:")
                    for cargo in cargo_list:
                        print(f"    Individual number: {cargo.get('individual_number', 'N/A')}")
                        print(f"    Cargo number: {cargo.get('cargo_number', 'N/A')}")
                        print(f"    Placement location: {cargo.get('placement_location', 'N/A')}")

if __name__ == "__main__":
    debug_layout()
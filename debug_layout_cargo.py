#!/usr/bin/env python3
"""
Debug script to see what cargo is actually in the layout
"""

import requests
import json

# Configuration
BACKEND_URL = "https://placement-view.preview.emergentagent.com/api"
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"

def get_auth_token():
    """Get authentication token"""
    response = requests.post(f"{BACKEND_URL}/auth/login", json={
        "phone": WAREHOUSE_OPERATOR_PHONE,
        "password": WAREHOUSE_OPERATOR_PASSWORD
    })
    
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def get_warehouse_id(token):
    """Get warehouse ID"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BACKEND_URL}/operator/warehouses", headers=headers)
    
    if response.status_code == 200:
        warehouses = response.json()
        for warehouse in warehouses:
            if "Москва Склад №1" in warehouse.get("name", ""):
                return warehouse.get("id")
    return None

def debug_layout_cargo(token, warehouse_id):
    """Debug what cargo is actually in the layout"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BACKEND_URL}/warehouses/{warehouse_id}/layout-with-cargo", headers=headers)
    
    if response.status_code == 200:
        layout_data = response.json()
        
        print("=== LAYOUT DEBUG INFO ===")
        print(f"Total cells: {layout_data.get('total_cells', 0)}")
        print(f"Occupied cells: {layout_data.get('occupied_cells', 0)}")
        print(f"Total cargo: {layout_data.get('total_cargo', 0)}")
        print(f"Occupancy percentage: {layout_data.get('occupancy_percentage', 0)}%")
        
        warehouse_info = layout_data.get("warehouse", {})
        layout = warehouse_info.get("layout", {})
        blocks = layout.get("blocks", [])
        
        print(f"\nBlocks found: {len(blocks)}")
        
        all_cargo_found = []
        
        for block in blocks:
            block_number = block.get("number", 0)
            shelves = block.get("shelves", [])
            
            for shelf in shelves:
                shelf_number = shelf.get("number", 0)
                cells = shelf.get("cells", [])
                
                for cell in cells:
                    cell_number = cell.get("number", 0)
                    location_code = f"Б{block_number}-П{shelf_number}-Я{cell_number}"
                    
                    if cell.get("is_occupied", False):
                        cargo_list = cell.get("cargo", [])
                        print(f"\n📍 OCCUPIED CELL: {location_code}")
                        print(f"   Cargo count: {len(cargo_list)}")
                        
                        for i, cargo_info in enumerate(cargo_list):
                            individual_number = cargo_info.get("individual_number", "N/A")
                            cargo_number = cargo_info.get("cargo_number", "N/A")
                            cargo_name = cargo_info.get("cargo_name", "N/A")
                            recipient = cargo_info.get("recipient_full_name", "N/A")
                            
                            print(f"   Cargo {i+1}:")
                            print(f"     Individual Number: {individual_number}")
                            print(f"     Cargo Number: {cargo_number}")
                            print(f"     Cargo Name: {cargo_name}")
                            print(f"     Recipient: {recipient}")
                            
                            all_cargo_found.append({
                                "individual_number": individual_number,
                                "cargo_number": cargo_number,
                                "location": location_code
                            })
        
        print(f"\n=== SUMMARY ===")
        print(f"Total cargo found in layout: {len(all_cargo_found)}")
        
        # Check for specific cargo we're looking for
        target_cargo = ["25082235/01/01", "25082235/01/02", "25082235/02/01"]
        
        print(f"\nLooking for target cargo: {target_cargo}")
        for target in target_cargo:
            found = False
            for cargo in all_cargo_found:
                if target in cargo["individual_number"]:
                    print(f"✅ {target} FOUND at {cargo['location']}")
                    found = True
                    break
            if not found:
                print(f"❌ {target} NOT FOUND")
        
        print(f"\nAll cargo in layout:")
        for cargo in all_cargo_found:
            print(f"  - {cargo['individual_number']} at {cargo['location']}")
    
    else:
        print(f"Error: HTTP {response.status_code}")
        print(response.text)

def main():
    token = get_auth_token()
    if not token:
        print("Failed to get auth token")
        return
    
    warehouse_id = get_warehouse_id(token)
    if not warehouse_id:
        print("Failed to get warehouse ID")
        return
    
    debug_layout_cargo(token, warehouse_id)

if __name__ == "__main__":
    main()
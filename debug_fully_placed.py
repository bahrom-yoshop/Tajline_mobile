#!/usr/bin/env python3
"""
Debug script to understand why fully-placed endpoint returns 0 items
"""

import requests
import json
import os

# Конфигурация для тестирования
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://placement-view.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Тестовые данные оператора склада
OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

def authenticate():
    """Авторизация"""
    session = requests.Session()
    
    response = session.post(
        f"{API_BASE}/auth/login",
        json=OPERATOR_CREDENTIALS,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        auth_token = data.get("access_token")
        session.headers.update({
            "Authorization": f"Bearer {auth_token}"
        })
        
        # Get user info
        user_response = session.get(f"{API_BASE}/auth/me", timeout=30)
        if user_response.status_code == 200:
            user_data = user_response.json()
            return session, user_data
    return None, None

def debug_data():
    """Debug the data structures"""
    session, user_data = authenticate()
    if not session:
        print("❌ Authentication failed")
        return
    
    print("🔍 DEBUGGING FULLY-PLACED ENDPOINT DATA")
    print("=" * 60)
    print(f"User: {user_data.get('full_name')} (ID: {user_data.get('id')})")
    
    # 1. Check individual-units-for-placement
    print("\n1. INDIVIDUAL UNITS FOR PLACEMENT:")
    response = session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement")
    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        print(f"   Found {len(items)} groups")
        
        placed_units_found = []
        
        for i, group in enumerate(items):
            print(f"\n   Group {i+1}:")
            print(f"   - Application: {group.get('application_number', 'N/A')}")
            print(f"   - Cargo ID: {group.get('cargo_id', 'N/A')}")
            print(f"   - Units: {len(group.get('units', []))}")
            
            units = group.get('units', [])
            for j, unit in enumerate(units):
                is_placed = unit.get('is_placed', False)
                print(f"     Unit {j+1}: {unit.get('individual_number', 'N/A')} - Placed: {is_placed}")
                if is_placed:
                    print(f"       Placement info: {unit.get('placement_info', 'N/A')}")
                    placed_units_found.append({
                        'cargo_id': group.get('cargo_id'),
                        'individual_number': unit.get('individual_number'),
                        'placement_info': unit.get('placement_info')
                    })
        
        print(f"\n   📊 SUMMARY: Found {len(placed_units_found)} placed units")
        
    else:
        print(f"   ❌ Error: {response.status_code}")
    
    # 2. Check fully-placed endpoint
    print("\n2. FULLY-PLACED ENDPOINT:")
    response = session.get(f"{API_BASE}/operator/cargo/fully-placed")
    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        print(f"   Found {len(items)} placed applications")
        
        if len(items) == 0:
            print("   🚨 NO APPLICATIONS FOUND - This is the problem!")
            print("   Let's check what the endpoint is looking for...")
            
            # Let's check if there are any operator_cargo records for this user
            print(f"\n   🔍 Checking for operator_cargo records for user {user_data.get('id')}...")
            
        for i, item in enumerate(items):
            print(f"\n   Application {i+1}:")
            print(f"   - Number: {item.get('cargo_number', 'N/A')}")
            print(f"   - Status: {item.get('status', 'N/A')}")
            print(f"   - Placed units: {item.get('placed_units', 0)}/{item.get('total_units', 0)}")
            print(f"   - Is partially placed: {item.get('is_partially_placed', False)}")
    else:
        print(f"   ❌ Error: {response.status_code}")
    
    # 3. Check placement progress
    print("\n3. PLACEMENT PROGRESS:")
    response = session.get(f"{API_BASE}/operator/placement-progress")
    if response.status_code == 200:
        data = response.json()
        print(f"   Total units: {data.get('total_units', 0)}")
        print(f"   Placed units: {data.get('placed_units', 0)}")
        print(f"   Progress: {data.get('progress_percentage', 0)}%")
    else:
        print(f"   ❌ Error: {response.status_code}")
    
    # 4. Check available-for-placement (regular endpoint)
    print("\n4. AVAILABLE FOR PLACEMENT (Regular):")
    response = session.get(f"{API_BASE}/operator/cargo/available-for-placement")
    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        print(f"   Found {len(items)} applications available for placement")
        
        for i, item in enumerate(items):
            print(f"\n   Application {i+1}:")
            print(f"   - Number: {item.get('cargo_number', 'N/A')}")
            print(f"   - ID: {item.get('id', 'N/A')}")
            print(f"   - Operator ID: {item.get('operator_id', 'N/A')}")
            print(f"   - Created by: {item.get('created_by', 'N/A')}")
    else:
        print(f"   ❌ Error: {response.status_code}")

if __name__ == "__main__":
    debug_data()
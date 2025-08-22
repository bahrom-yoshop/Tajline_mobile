#!/usr/bin/env python3
"""
Verify that both pickup requests are showing correctly with cargo names
"""

import requests
import json

def verify_pickup_requests():
    base_url = "https://placement-view.preview.emergentagent.com"
    
    # Login as courier
    courier_login_data = {
        "phone": "+79991234567",
        "password": "courier123"
    }
    
    response = requests.post(f"{base_url}/api/auth/login", json=courier_login_data)
    if response.status_code != 200:
        print("❌ Courier login failed")
        return
    
    courier_token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {courier_token}'}
    
    # Get new requests
    response = requests.get(f"{base_url}/api/courier/requests/new", headers=headers)
    if response.status_code != 200:
        print("❌ Failed to get new requests")
        return
    
    data = response.json()
    new_requests = data.get('new_requests', [])
    
    print(f"📋 Found {len(new_requests)} new requests")
    print("\n🎯 Pickup requests with cargo names:")
    
    pickup_count = 0
    for request in new_requests:
        if request.get('request_type') == 'pickup':
            pickup_count += 1
            print(f"   {pickup_count}. ID: {request.get('id')}")
            print(f"      👤 Sender: {request.get('sender_full_name')}")
            print(f"      📦 Destination (Cargo Name): '{request.get('destination', 'N/A')}'")
            print(f"      📍 Pickup Address: {request.get('pickup_address', 'N/A')}")
            print(f"      📅 Date: {request.get('pickup_date', 'N/A')}")
            print(f"      🕐 Time: {request.get('pickup_time_from', 'N/A')} - {request.get('pickup_time_to', 'N/A')}")
            print()
    
    print(f"✅ Total pickup requests found: {pickup_count}")
    
    # Check if our test requests are there
    test_requests = [req for req in new_requests if req.get('sender_full_name') in ['Тест Наименование', 'Тест Наименование 2']]
    print(f"🧪 Our test requests found: {len(test_requests)}")
    
    for req in test_requests:
        destination = req.get('destination', '')
        if destination in ['Документы и подарки', 'Электроника и техника']:
            print(f"   ✅ {req.get('sender_full_name')}: '{destination}' ✓")
        else:
            print(f"   ❌ {req.get('sender_full_name')}: '{destination}' ✗")

if __name__ == "__main__":
    verify_pickup_requests()
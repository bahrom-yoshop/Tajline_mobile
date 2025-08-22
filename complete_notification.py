#!/usr/bin/env python3
"""
Complete a warehouse notification manually
"""

import requests
import json

def complete_notification():
    base_url = "https://tajline-cargo-7.preview.emergentagent.com"
    
    # Login as operator
    login_data = {
        "phone": "+79777888999",
        "password": "warehouse123"
    }
    
    response = requests.post(f"{base_url}/api/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"Login failed: {response.status_code}")
        return
    
    token = response.json()["access_token"]
    headers = {'Authorization': f'Bearer {token}'}
    
    # Use the notification ID from our test
    notification_id = "WN_1755143728931"  # From the test output
    
    print(f"🔄 Completing notification {notification_id}")
    
    # Complete with cargo details
    cargo_completion_data = {
        "sender_full_name": "Тестовый Отправитель Забора",
        "sender_phone": "+79123456789",
        "sender_address": "Москва, ул. Тестовая Забора, 123",
        "recipient_full_name": "Тестовый Получатель",
        "recipient_phone": "+79987654321",
        "recipient_address": "Душанбе, ул. Получателя, 456",
        "payment_method": "cash",
        "payment_status": "not_paid",
        "delivery_method": "pickup",
        "cargo_items": [
            {
                "name": "Тестовый груз из заявки на забор",
                "weight": 15.5,
                "price": 2500.0
            },
            {
                "name": "Второй груз из заявки на забор",
                "weight": 8.3,
                "price": 1200.0
            }
        ]
    }
    
    complete_response = requests.post(
        f"{base_url}/api/operator/warehouse-notifications/{notification_id}/complete",
        json=cargo_completion_data,
        headers=headers
    )
    print(f"Complete status: {complete_response.status_code}")
    
    if complete_response.status_code == 200:
        complete_data = complete_response.json()
        print(f"✅ Success! Response:")
        print(json.dumps(complete_data, indent=2, ensure_ascii=False))
        
        # Now check placed cargo
        print(f"\n🔍 Checking placed cargo after completion:")
        response = requests.get(f"{base_url}/api/warehouses/placed-cargo", headers=headers)
        print(f"Placed cargo status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            placed_cargo = data.get("placed_cargo", [])
            print(f"Found {len(placed_cargo)} placed cargo items")
            
            for i, cargo in enumerate(placed_cargo):
                print(f"\nCargo {i+1}:")
                print(f"  Number: {cargo.get('cargo_number')}")
                print(f"  Name: {cargo.get('cargo_name')}")
                print(f"  Status: {cargo.get('status')}")
                print(f"  Pickup Request ID: {cargo.get('pickup_request_id')}")
                print(f"  Pickup Request Number: {cargo.get('pickup_request_number')}")
                print(f"  Courier Delivered By: {cargo.get('courier_delivered_by')}")
        
    else:
        print(f"❌ Error: {complete_response.text}")

if __name__ == "__main__":
    complete_notification()
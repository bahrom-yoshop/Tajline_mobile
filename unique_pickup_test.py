#!/usr/bin/env python3
"""
Test pickup request acceptance with unique timestamp-based request
"""

import requests
import json
from datetime import datetime
import time

def test_unique_pickup_acceptance():
    base_url = "https://placement-view.preview.emergentagent.com"
    
    print("🎯 TESTING UNIQUE PICKUP REQUEST ACCEPTANCE")
    print("=" * 60)
    
    # Step 1: Login as operator
    print("\n🔐 Step 1: Login as operator...")
    operator_login = {
        "phone": "+79777888999",
        "password": "warehouse123"
    }
    
    response = requests.post(f"{base_url}/api/auth/login", json=operator_login)
    if response.status_code != 200:
        print(f"❌ Operator login failed: {response.status_code}")
        return False
    
    operator_token = response.json()['access_token']
    operator_headers = {'Authorization': f'Bearer {operator_token}', 'Content-Type': 'application/json'}
    print("✅ Operator login successful")
    
    # Step 2: Create a unique pickup request with timestamp
    print("\n📦 Step 2: Create unique pickup request...")
    timestamp = int(time.time())
    pickup_data = {
        "sender_full_name": f"Тест Отправитель {timestamp}",
        "sender_phone": "+79991234567",
        "pickup_address": f"Москва, ул. Уникальная {timestamp}, 1",
        "pickup_date": "2025-01-22",
        "pickup_time_from": "15:00",
        "pickup_time_to": "17:00",
        "cargo_name": f"Уникальный груз {timestamp}",
        "route": "moscow_to_tajikistan",
        "courier_fee": 800.0
    }
    
    response = requests.post(f"{base_url}/api/admin/courier/pickup-request", json=pickup_data, headers=operator_headers)
    if response.status_code != 200:
        print(f"❌ Failed to create pickup request: {response.status_code}")
        try:
            print(f"Error: {response.json()}")
        except:
            print(f"Raw response: {response.text}")
        return False
    
    pickup_response = response.json()
    unique_request_id = pickup_response['request_id']
    print(f"✅ Unique pickup request created: {unique_request_id}")
    
    # Wait a moment to ensure the request is saved
    time.sleep(1)
    
    # Step 3: Login as courier
    print("\n🚴 Step 3: Login as courier...")
    courier_login = {
        "phone": "+79991234567",
        "password": "courier123"
    }
    
    response = requests.post(f"{base_url}/api/auth/login", json=courier_login)
    if response.status_code != 200:
        print(f"❌ Courier login failed: {response.status_code}")
        return False
    
    courier_token = response.json()['access_token']
    courier_headers = {'Authorization': f'Bearer {courier_token}', 'Content-Type': 'application/json'}
    print("✅ Courier login successful")
    
    # Step 4: Verify the unique request appears in new requests
    print("\n📋 Step 4: Check if unique request appears in new requests...")
    response = requests.get(f"{base_url}/api/courier/requests/new", headers=courier_headers)
    if response.status_code != 200:
        print(f"❌ Failed to get new requests: {response.status_code}")
        return False
    
    data = response.json()
    pickup_requests = data.get('pickup_requests', [])
    
    unique_request_found = False
    request_status = None
    assigned_courier = None
    
    for req in pickup_requests:
        if req['id'] == unique_request_id:
            unique_request_found = True
            request_status = req.get('request_status')
            assigned_courier = req.get('assigned_courier_id')
            print(f"✅ Unique request found: {unique_request_id}")
            print(f"📊 Status: {request_status}")
            print(f"👤 Assigned courier: {assigned_courier}")
            break
    
    if not unique_request_found:
        print(f"❌ Unique request {unique_request_id} not found in new requests")
        print("📋 Available pickup requests:")
        for req in pickup_requests:
            print(f"  - ID: {req['id']}, Status: {req.get('request_status')}, Sender: {req.get('sender_full_name')}")
        return False
    
    # Step 5: MAIN TEST - Try to accept the unique pickup request
    print(f"\n🎯 Step 5: MAIN TEST - Accept unique pickup request {unique_request_id}...")
    print("🔧 ИСПРАВЛЕНИЕ: Любой курьер может принять заявку со статусом 'pending'")
    print(f"📊 Request status before acceptance: {request_status}")
    print(f"👤 Assigned courier before acceptance: {assigned_courier}")
    
    response = requests.post(f"{base_url}/api/courier/requests/{unique_request_id}/accept", headers=courier_headers)
    
    print(f"📊 Response status: {response.status_code}")
    
    if response.status_code == 200:
        print("🎉 SUCCESS! Unique pickup request accepted!")
        print("✅ ИСПРАВЛЕНИЕ РАБОТАЕТ: can_accept logic fixed!")
        try:
            result = response.json()
            print(f"📄 Response: {result}")
        except:
            pass
        return True
    else:
        print("❌ FAILED to accept unique pickup request")
        try:
            error_detail = response.json()
            print(f"📄 Error: {error_detail}")
        except:
            print(f"📄 Raw response: {response.text}")
        return False

if __name__ == "__main__":
    success = test_unique_pickup_acceptance()
    if success:
        print("\n🎉 PICKUP REQUEST ACCEPTANCE FIX CONFIRMED!")
    else:
        print("\n❌ PICKUP REQUEST ACCEPTANCE FIX NEEDS MORE WORK")
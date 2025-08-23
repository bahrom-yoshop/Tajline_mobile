#!/usr/bin/env python3
"""
Test pickup request acceptance with a fresh request
"""

import requests
import json
from datetime import datetime

def test_fresh_pickup_acceptance():
    base_url = "https://tajline-manage-1.preview.emergentagent.com"
    
    print("🎯 TESTING FRESH PICKUP REQUEST ACCEPTANCE")
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
    
    # Step 2: Create a fresh pickup request
    print("\n📦 Step 2: Create fresh pickup request...")
    pickup_data = {
        "sender_full_name": "Тест Отправитель Свежий",
        "sender_phone": "+79991234567",
        "pickup_address": "Москва, ул. Свежая Тестовая, 999",
        "pickup_date": "2025-01-21",
        "pickup_time_from": "14:00",
        "pickup_time_to": "16:00",
        "cargo_name": "Свежий тестовый груз",
        "route": "moscow_to_tajikistan",
        "courier_fee": 750.0
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
    fresh_request_id = pickup_response['request_id']
    print(f"✅ Fresh pickup request created: {fresh_request_id}")
    
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
    
    # Step 4: Verify the fresh request appears in new requests
    print("\n📋 Step 4: Check if fresh request appears in new requests...")
    response = requests.get(f"{base_url}/api/courier/requests/new", headers=courier_headers)
    if response.status_code != 200:
        print(f"❌ Failed to get new requests: {response.status_code}")
        return False
    
    data = response.json()
    pickup_requests = data.get('pickup_requests', [])
    
    fresh_request_found = False
    for req in pickup_requests:
        if req['id'] == fresh_request_id:
            fresh_request_found = True
            print(f"✅ Fresh request found: {fresh_request_id}")
            print(f"📊 Status: {req.get('request_status')}")
            print(f"👤 Assigned courier: {req.get('assigned_courier_id')}")
            break
    
    if not fresh_request_found:
        print(f"❌ Fresh request {fresh_request_id} not found in new requests")
        return False
    
    # Step 5: MAIN TEST - Try to accept the fresh pickup request
    print(f"\n🎯 Step 5: MAIN TEST - Accept fresh pickup request {fresh_request_id}...")
    print("🔧 ИСПРАВЛЕНИЕ: Любой курьер может принять заявку со статусом 'pending'")
    
    response = requests.post(f"{base_url}/api/courier/requests/{fresh_request_id}/accept", headers=courier_headers)
    
    print(f"📊 Response status: {response.status_code}")
    
    if response.status_code == 200:
        print("🎉 SUCCESS! Fresh pickup request accepted!")
        print("✅ ИСПРАВЛЕНИЕ РАБОТАЕТ: can_accept logic fixed!")
        try:
            result = response.json()
            print(f"📄 Response: {result}")
        except:
            pass
        return True
    else:
        print("❌ FAILED to accept fresh pickup request")
        try:
            error_detail = response.json()
            print(f"📄 Error: {error_detail}")
        except:
            print(f"📄 Raw response: {response.text}")
        return False

if __name__ == "__main__":
    success = test_fresh_pickup_acceptance()
    if success:
        print("\n🎉 PICKUP REQUEST ACCEPTANCE FIX CONFIRMED!")
    else:
        print("\n❌ PICKUP REQUEST ACCEPTANCE FIX NEEDS MORE WORK")
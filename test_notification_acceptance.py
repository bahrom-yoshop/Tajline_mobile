#!/usr/bin/env python3
"""
Test notification acceptance functionality
"""

import requests
import json

def test_notification_acceptance():
    base_url = "https://tajline-cargo-7.preview.emergentagent.com"
    
    # Login as operator
    print("🔍 Logging in as operator...")
    operator_login = {
        "phone": "+79777888999",
        "password": "warehouse123"
    }
    
    response = requests.post(f"{base_url}/api/auth/login", json=operator_login)
    if response.status_code == 200:
        operator_token = response.json()['access_token']
        print("✅ Operator logged in successfully")
    else:
        print("❌ Operator login failed")
        return
    
    # Get notifications
    print("\n🔔 Getting warehouse notifications...")
    headers = {'Authorization': f'Bearer {operator_token}'}
    response = requests.get(f"{base_url}/api/operator/warehouse-notifications", headers=headers)
    
    if response.status_code == 200:
        notifications_data = response.json()
        notifications = notifications_data.get('notifications', [])
        
        if notifications:
            notification = notifications[0]  # Get first notification
            notification_id = notification.get('id')
            print(f"✅ Found notification ID: {notification_id}")
            print(f"📄 Notification details: {notification.get('sender_full_name')} - {notification.get('status')}")
            
            # Test accepting the notification
            print(f"\n✅ Testing notification acceptance for ID: {notification_id}")
            response = requests.post(
                f"{base_url}/api/operator/warehouse-notifications/{notification_id}/accept",
                headers=headers
            )
            
            if response.status_code == 200:
                accept_data = response.json()
                print("✅ Notification accepted successfully!")
                print(f"📄 Response: {json.dumps(accept_data, indent=2, ensure_ascii=False)}")
            else:
                print(f"❌ Notification acceptance failed: {response.status_code}")
                print(f"📄 Error: {response.text}")
        else:
            print("❌ No notifications found")
    else:
        print(f"❌ Failed to get notifications: {response.status_code}")

if __name__ == "__main__":
    test_notification_acceptance()
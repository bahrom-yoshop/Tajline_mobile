#!/usr/bin/env python3
"""
Complete pickup workflow test to create warehouse notifications
This simulates the full workflow: operator creates pickup request -> courier accepts -> courier delivers -> warehouse notification created
"""

import requests
import sys
import json
from datetime import datetime

class CompletePickupWorkflowTester:
    def __init__(self, base_url="https://cargo-sync.preview.emergentagent.com"):
        self.base_url = base_url
        self.operator_token = None
        self.courier_token = None
        
        print(f"🔧 COMPLETE PICKUP WORKFLOW TEST FOR WAREHOUSE NOTIFICATIONS")
        print(f"📡 Base URL: {self.base_url}")
        print("=" * 80)

    def login_operator(self):
        """Login as warehouse operator"""
        print("\n🔐 STEP 1: LOGGING IN AS WAREHOUSE OPERATOR...")
        
        operator_login_data = {
            "phone": "+79777888999",
            "password": "warehouse123"
        }
        
        url = f"{self.base_url}/api/auth/login"
        headers = {'Content-Type': 'application/json'}
        
        try:
            response = requests.post(url, json=operator_login_data, headers=headers)
            if response.status_code == 200:
                login_response = response.json()
                self.operator_token = login_response['access_token']
                operator_user = login_response.get('user', {})
                print(f"   ✅ Operator login successful: {operator_user.get('full_name')}")
                print(f"   👑 Role: {operator_user.get('role')}")
                print(f"   🆔 User Number: {operator_user.get('user_number')}")
                return True
            else:
                print(f"   ❌ Operator login failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Operator login error: {e}")
            return False

    def login_courier(self):
        """Login as courier"""
        print("\n🚚 STEP 2: LOGGING IN AS COURIER...")
        
        courier_login_data = {
            "phone": "+79991234567",
            "password": "courier123"
        }
        
        url = f"{self.base_url}/api/auth/login"
        headers = {'Content-Type': 'application/json'}
        
        try:
            response = requests.post(url, json=courier_login_data, headers=headers)
            if response.status_code == 200:
                login_response = response.json()
                self.courier_token = login_response['access_token']
                courier_user = login_response.get('user', {})
                print(f"   ✅ Courier login successful: {courier_user.get('full_name')}")
                print(f"   👑 Role: {courier_user.get('role')}")
                print(f"   🆔 User Number: {courier_user.get('user_number')}")
                return True
            else:
                print(f"   ❌ Courier login failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Courier login error: {e}")
            return False

    def create_pickup_request(self):
        """Create a pickup request"""
        print("\n📦 STEP 3: CREATING PICKUP REQUEST...")
        
        if not self.operator_token:
            print("   ❌ No operator token available")
            return False
        
        pickup_request_data = {
            "sender_full_name": "Диагностика Отправитель 100010",
            "sender_phone": "+79991234567",
            "pickup_address": "Москва, ул. Диагностическая, 100010",
            "pickup_date": "2025-01-20",
            "pickup_time_from": "10:00",
            "pickup_time_to": "18:00",
            "route": "moscow_to_tajikistan",
            "courier_fee": 500.0,
            "destination": "Душанбе, ул. Тестовая, 100010"
        }
        
        url = f"{self.base_url}/api/admin/courier/pickup-request"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.operator_token}'
        }
        
        try:
            response = requests.post(url, json=pickup_request_data, headers=headers)
            if response.status_code == 200:
                pickup_response = response.json()
                pickup_request_id = pickup_response.get('id')
                request_number = pickup_response.get('request_number')
                print(f"   ✅ Pickup request created successfully!")
                print(f"   📋 Request ID: {pickup_request_id}")
                print(f"   📋 Request Number: {request_number}")
                return pickup_request_id, request_number
            else:
                print(f"   ❌ Pickup request creation failed: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   📄 Error: {error_detail}")
                except:
                    print(f"   📄 Raw response: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Pickup request creation error: {e}")
            return False

    def courier_accept_pickup_request(self, pickup_request_id):
        """Courier accepts the pickup request"""
        print(f"\n✅ STEP 4: COURIER ACCEPTS PICKUP REQUEST {pickup_request_id}...")
        
        if not self.courier_token:
            print("   ❌ No courier token available")
            return False
        
        url = f"{self.base_url}/api/courier/pickup-requests/{pickup_request_id}/accept"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.courier_token}'
        }
        
        try:
            response = requests.post(url, headers=headers)
            if response.status_code == 200:
                accept_response = response.json()
                print(f"   ✅ Pickup request accepted by courier!")
                print(f"   📄 Response: {accept_response}")
                return True
            else:
                print(f"   ❌ Pickup request acceptance failed: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   📄 Error: {error_detail}")
                except:
                    print(f"   📄 Raw response: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Pickup request acceptance error: {e}")
            return False

    def courier_pickup_cargo(self, pickup_request_id):
        """Courier picks up the cargo"""
        print(f"\n📦 STEP 5: COURIER PICKS UP CARGO {pickup_request_id}...")
        
        if not self.courier_token:
            print("   ❌ No courier token available")
            return False
        
        url = f"{self.base_url}/api/courier/pickup-requests/{pickup_request_id}/pickup"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.courier_token}'
        }
        
        try:
            response = requests.post(url, headers=headers)
            if response.status_code == 200:
                pickup_response = response.json()
                print(f"   ✅ Cargo picked up by courier!")
                print(f"   📄 Response: {pickup_response}")
                return True
            else:
                print(f"   ❌ Cargo pickup failed: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   📄 Error: {error_detail}")
                except:
                    print(f"   📄 Raw response: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Cargo pickup error: {e}")
            return False

    def courier_deliver_to_warehouse(self, pickup_request_id):
        """Courier delivers cargo to warehouse"""
        print(f"\n🏭 STEP 6: COURIER DELIVERS CARGO TO WAREHOUSE {pickup_request_id}...")
        
        if not self.courier_token:
            print("   ❌ No courier token available")
            return False
        
        url = f"{self.base_url}/api/courier/requests/{pickup_request_id}/deliver-to-warehouse"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.courier_token}'
        }
        
        try:
            response = requests.post(url, headers=headers)
            if response.status_code == 200:
                delivery_response = response.json()
                print(f"   ✅ Cargo delivered to warehouse!")
                print(f"   📄 Response: {delivery_response}")
                return True
            else:
                print(f"   ❌ Cargo delivery to warehouse failed: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   📄 Error: {error_detail}")
                except:
                    print(f"   📄 Raw response: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Cargo delivery to warehouse error: {e}")
            return False

    def check_warehouse_notifications(self):
        """Check warehouse notifications"""
        print("\n📋 STEP 7: CHECKING WAREHOUSE NOTIFICATIONS...")
        
        if not self.operator_token:
            print("   ❌ No operator token available")
            return False
        
        url = f"{self.base_url}/api/operator/warehouse-notifications"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.operator_token}'
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                notifications = response.json()
                notification_count = len(notifications) if isinstance(notifications, list) else 0
                
                print(f"   ✅ Found {notification_count} warehouse notifications")
                
                if notification_count > 0:
                    print("\n   📋 WAREHOUSE NOTIFICATIONS:")
                    for i, notification in enumerate(notifications, 1):
                        notification_id = notification.get('id', 'N/A')
                        notification_number = notification.get('notification_number', 'N/A')
                        pickup_request_id = notification.get('pickup_request_id', 'N/A')
                        status = notification.get('status', 'N/A')
                        sender_name = notification.get('sender_full_name', 'N/A')
                        
                        print(f"   {i}. ID: {notification_id}")
                        print(f"      Number: {notification_number}")
                        print(f"      pickup_request_id: {pickup_request_id}")
                        print(f"      Status: {status}")
                        print(f"      Sender: {sender_name}")
                        print(f"      ---")
                        
                        # Check if this is notification #100010 or similar
                        if str(notification_number) == '100010' or '100010' in str(notification_number):
                            print(f"   🎯 FOUND NOTIFICATION WITH 100010!")
                            return notification
                
                return notifications
            else:
                print(f"   ❌ Failed to get warehouse notifications: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Error getting warehouse notifications: {e}")
            return False

    def test_pickup_request_endpoint(self, pickup_request_id):
        """Test the pickup request endpoint"""
        print(f"\n🔗 STEP 8: TESTING PICKUP REQUEST ENDPOINT...")
        print(f"   📋 GET /api/operator/pickup-requests/{pickup_request_id}")
        
        if not self.operator_token:
            print("   ❌ No operator token available")
            return False
        
        url = f"{self.base_url}/api/operator/pickup-requests/{pickup_request_id}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.operator_token}'
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                pickup_request = response.json()
                print(f"   ✅ Pickup request endpoint working!")
                
                print("\n   📊 PICKUP REQUEST STRUCTURE:")
                for key, value in pickup_request.items():
                    print(f"   {key}: {value}")
                
                return True
            else:
                print(f"   ❌ Pickup request endpoint failed: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   📄 Error: {error_detail}")
                except:
                    print(f"   📄 Raw response: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Error testing pickup request endpoint: {e}")
            return False

    def run_complete_workflow(self):
        """Run complete pickup workflow"""
        print("🚀 STARTING COMPLETE PICKUP WORKFLOW TEST")
        
        # Step 1: Login as operator
        if not self.login_operator():
            print("\n❌ WORKFLOW FAILED: Cannot login as operator")
            return False
        
        # Step 2: Login as courier
        if not self.login_courier():
            print("\n❌ WORKFLOW FAILED: Cannot login as courier")
            return False
        
        # Step 3: Create pickup request
        pickup_result = self.create_pickup_request()
        if not pickup_result:
            print("\n❌ WORKFLOW FAILED: Cannot create pickup request")
            return False
        
        pickup_request_id, request_number = pickup_result
        
        # Step 4: Courier accepts pickup request
        if not self.courier_accept_pickup_request(pickup_request_id):
            print("\n❌ WORKFLOW FAILED: Courier cannot accept pickup request")
            return False
        
        # Step 5: Courier picks up cargo
        if not self.courier_pickup_cargo(pickup_request_id):
            print("\n❌ WORKFLOW FAILED: Courier cannot pickup cargo")
            return False
        
        # Step 6: Courier delivers to warehouse
        if not self.courier_deliver_to_warehouse(pickup_request_id):
            print("\n❌ WORKFLOW FAILED: Courier cannot deliver to warehouse")
            return False
        
        # Step 7: Check warehouse notifications
        notifications = self.check_warehouse_notifications()
        
        # Step 8: Test pickup request endpoint
        if pickup_request_id:
            self.test_pickup_request_endpoint(pickup_request_id)
        
        # Final summary
        print("\n" + "="*80)
        print("📊 COMPLETE PICKUP WORKFLOW SUMMARY")
        print("="*80)
        
        if notifications and isinstance(notifications, list) and len(notifications) > 0:
            print("✅ SUCCESS: Warehouse notifications created through complete workflow")
            print(f"📊 Total notifications: {len(notifications)}")
            
            # Check if any notification has pickup_request_id
            notifications_with_pickup_id = [n for n in notifications if isinstance(n, dict) and n.get('pickup_request_id')]
            if notifications_with_pickup_id:
                print(f"✅ {len(notifications_with_pickup_id)} notifications have pickup_request_id")
                
                # Check for notification #100010 or similar
                target_notifications = [n for n in notifications_with_pickup_id 
                                      if '100010' in str(n.get('notification_number', '')) or 
                                         str(n.get('notification_number', '')) == '100010']
                if target_notifications:
                    print(f"🎯 FOUND TARGET NOTIFICATION(S) WITH 100010!")
                    for notification in target_notifications:
                        print(f"   📋 Notification: {notification.get('notification_number')}")
                        print(f"   🔗 pickup_request_id: {notification.get('pickup_request_id')}")
                else:
                    print("⚠️  No notification with number 100010 found")
            else:
                print("❌ NO notifications have pickup_request_id")
        else:
            print("❌ FAILED: No warehouse notifications created even with complete workflow")
        
        print("\n🎯 DIAGNOSTIC RESULTS:")
        print("1. Complete pickup workflow executed successfully")
        print("2. Check if warehouse notifications were created")
        print("3. Verify pickup_request_id is properly set in notifications")
        print("4. Test the 'Продолжить оформление' button with real data")
        
        return True

if __name__ == "__main__":
    tester = CompletePickupWorkflowTester()
    tester.run_complete_workflow()
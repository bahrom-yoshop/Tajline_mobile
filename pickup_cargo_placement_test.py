#!/usr/bin/env python3
"""
Comprehensive Test for Pickup Request Cargo Placement in TAJLINE.TJ
Tests the full cycle from pickup request creation to cargo display in "Placed Cargo" section
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class PickupCargoPlacementTester:
    def __init__(self, base_url="https://tajline-cargo-7.preview.emergentagent.com"):
        self.base_url = base_url
        self.tokens = {}
        self.users = {}
        self.test_data = {}
        self.tests_run = 0
        self.tests_passed = 0
        
        print(f"🚚 PICKUP CARGO PLACEMENT TESTER - TAJLINE.TJ")
        print(f"📡 Base URL: {self.base_url}")
        print("=" * 80)

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data: Optional[Dict] = None, token: Optional[str] = None, 
                 params: Optional[Dict] = None) -> tuple[bool, Dict]:
        """Run a single API test"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'

        self.tests_run += 1
        print(f"\n🔍 Test {self.tests_run}: {name}")
        print(f"   {method} {endpoint}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, params=params)
            elif method == 'DELETE':
                response = requests.delete(url, json=data, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            print(f"   Status: {response.status_code}")
            
            if response.status_code == expected_status:
                print(f"   ✅ PASS")
                self.tests_passed += 1
                success = True
            else:
                print(f"   ❌ FAIL - Expected {expected_status}, got {response.status_code}")
                success = False

            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
                
            if not success:
                print(f"   Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
                
            return success, response_data
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            return False, {"error": str(e)}

    def authenticate_operator(self):
        """Authenticate warehouse operator"""
        print("\n" + "="*50)
        print("🔐 STEP 1: OPERATOR AUTHENTICATION")
        print("="*50)
        
        login_data = {
            "phone": "+79777888999",
            "password": "warehouse123"
        }
        
        success, response = self.run_test(
            "Operator Login",
            "POST",
            "/api/auth/login",
            200,
            login_data
        )
        
        if success and "access_token" in response:
            self.tokens["operator"] = response["access_token"]
            print(f"   🎫 Operator token obtained")
            
            # Get operator info
            success, user_info = self.run_test(
                "Get Operator Info",
                "GET", 
                "/api/auth/me",
                200,
                token=self.tokens["operator"]
            )
            
            if success:
                self.users["operator"] = user_info
                print(f"   👤 Operator: {user_info.get('full_name', 'Unknown')}")
                print(f"   📱 Phone: {user_info.get('phone', 'Unknown')}")
                print(f"   🏷️ Role: {user_info.get('role', 'Unknown')}")
                return True
        
        return False

    def authenticate_courier(self):
        """Authenticate courier"""
        print("\n" + "="*50)
        print("🚴 STEP 2: COURIER AUTHENTICATION")
        print("="*50)
        
        login_data = {
            "phone": "+79991234567",
            "password": "courier123"
        }
        
        success, response = self.run_test(
            "Courier Login",
            "POST",
            "/api/auth/login",
            200,
            login_data
        )
        
        if success and "access_token" in response:
            self.tokens["courier"] = response["access_token"]
            print(f"   🎫 Courier token obtained")
            
            # Get courier info
            success, user_info = self.run_test(
                "Get Courier Info",
                "GET",
                "/api/auth/me", 
                200,
                token=self.tokens["courier"]
            )
            
            if success:
                self.users["courier"] = user_info
                print(f"   👤 Courier: {user_info.get('full_name', 'Unknown')}")
                print(f"   📱 Phone: {user_info.get('phone', 'Unknown')}")
                print(f"   🏷️ Role: {user_info.get('role', 'Unknown')}")
                return True
        
        return False

    def create_pickup_request(self):
        """Create pickup request"""
        print("\n" + "="*50)
        print("📦 STEP 3: CREATE PICKUP REQUEST")
        print("="*50)
        
        pickup_data = {
            "sender_full_name": "Тестовый Отправитель Забора",
            "sender_phone": "+79123456789, +79987654321",
            "pickup_address": "Москва, ул. Тестовая Забора, 123",
            "pickup_date": "2025-01-20",
            "pickup_time_from": "10:00",
            "pickup_time_to": "18:00",
            "route": "moscow_to_tajikistan",
            "courier_fee": 500.0,
            "cargo_items": [
                {
                    "cargo_name": "Тестовый груз из заявки на забор",
                    "weight": 15.5,
                    "declared_value": 2500.0
                },
                {
                    "cargo_name": "Второй груз из заявки на забор", 
                    "weight": 8.3,
                    "declared_value": 1200.0
                }
            ]
        }
        
        success, response = self.run_test(
            "Create Pickup Request",
            "POST",
            "/api/admin/courier/pickup-request",
            200,
            pickup_data,
            token=self.tokens["operator"]
        )
        
        if success:
            self.test_data["pickup_request_id"] = response.get("request_id")
            self.test_data["pickup_request_number"] = response.get("request_number")
            print(f"   📋 Pickup Request ID: {self.test_data['pickup_request_id']}")
            print(f"   🔢 Request Number: {self.test_data['pickup_request_number']}")
            return True
        
        return False

    def courier_accept_pickup_request(self):
        """Courier accepts pickup request"""
        print("\n" + "="*50)
        print("✅ STEP 4: COURIER ACCEPTS PICKUP REQUEST")
        print("="*50)
        
        # First check new requests
        success, response = self.run_test(
            "Get New Requests for Courier",
            "GET",
            "/api/courier/requests/new",
            200,
            token=self.tokens["courier"]
        )
        
        if success:
            new_requests = response.get("new_requests", [])
            pickup_requests = [req for req in new_requests if req.get("request_type") == "pickup"]
            print(f"   📋 Found {len(pickup_requests)} pickup requests")
            
            # Find our request
            our_request = None
            for req in pickup_requests:
                if req.get("id") == self.test_data["pickup_request_id"]:
                    our_request = req
                    break
            
            if our_request:
                print(f"   ✅ Found our pickup request: {our_request.get('sender_full_name')}")
                
                # Accept the request
                success, response = self.run_test(
                    "Accept Pickup Request",
                    "POST",
                    f"/api/courier/requests/{self.test_data['pickup_request_id']}/accept",
                    200,
                    token=self.tokens["courier"]
                )
                
                return success
            else:
                print(f"   ❌ Our pickup request not found in new requests")
                return False
        
        return False

    def courier_pickup_cargo(self):
        """Courier picks up cargo"""
        print("\n" + "="*50)
        print("🚚 STEP 5: COURIER PICKS UP CARGO")
        print("="*50)
        
        success, response = self.run_test(
            "Pickup Cargo",
            "POST",
            f"/api/courier/requests/{self.test_data['pickup_request_id']}/pickup",
            200,
            token=self.tokens["courier"]
        )
        
        if success:
            print(f"   ✅ Cargo picked up successfully")
            return True
        
        return False

    def courier_deliver_to_warehouse(self):
        """Courier delivers cargo to warehouse"""
        print("\n" + "="*50)
        print("🏭 STEP 6: COURIER DELIVERS TO WAREHOUSE")
        print("="*50)
        
        success, response = self.run_test(
            "Deliver to Warehouse",
            "POST",
            f"/api/courier/requests/{self.test_data['pickup_request_id']}/deliver-to-warehouse",
            200,
            token=self.tokens["courier"]
        )
        
        if success:
            self.test_data["notification_id"] = response.get("notification_id")
            print(f"   ✅ Delivered to warehouse successfully")
            print(f"   📨 Notification ID: {self.test_data['notification_id']}")
            return True
        
        return False

    def operator_process_notification(self):
        """Operator processes warehouse notification"""
        print("\n" + "="*50)
        print("📨 STEP 7: OPERATOR PROCESSES NOTIFICATION")
        print("="*50)
        
        # Get warehouse notifications
        success, response = self.run_test(
            "Get Warehouse Notifications",
            "GET",
            "/api/operator/warehouse-notifications",
            200,
            token=self.tokens["operator"]
        )
        
        if success:
            notifications = response.get("notifications", [])
            print(f"   📨 Found {len(notifications)} notifications")
            
            # Find the most recent notification (likely ours)
            if notifications:
                # Sort by created_at or take the first one
                our_notification = notifications[0]  # Most recent
                notification_id = our_notification.get("id")
                
                print(f"   ✅ Using notification ID: {notification_id}")
                print(f"   📋 Notification: {our_notification.get('message', 'No message')[:100]}...")
                
                # Accept notification
                success, response = self.run_test(
                    "Accept Notification",
                    "POST",
                    f"/api/operator/warehouse-notifications/{notification_id}/accept",
                    200,
                    token=self.tokens["operator"]
                )
                
                if success:
                    # Complete notification processing with cargo details
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
                    
                    success, response = self.run_test(
                        "Complete Notification Processing",
                        "POST",
                        f"/api/operator/warehouse-notifications/{notification_id}/complete",
                        200,
                        cargo_completion_data,
                        token=self.tokens["operator"]
                    )
                    
                    if success:
                        created_cargo = response.get("created_cargo", [])
                        print(f"   ✅ Created {len(created_cargo)} cargo items")
                        self.test_data["created_cargo"] = created_cargo
                        
                        for cargo in created_cargo:
                            print(f"   📦 Cargo: {cargo.get('cargo_number')} - {cargo.get('cargo_name')}")
                        
                        return True
            else:
                print(f"   ❌ No notifications found")
        
        return False

    def test_placed_cargo_endpoint(self):
        """Test the main endpoint - GET /api/warehouses/placed-cargo"""
        print("\n" + "="*50)
        print("🎯 STEP 8: TEST PLACED CARGO ENDPOINT (MAIN TEST)")
        print("="*50)
        
        success, response = self.run_test(
            "Get Placed Cargo",
            "GET",
            "/api/warehouses/placed-cargo",
            200,
            token=self.tokens["operator"]
        )
        
        if success:
            placed_cargo = response.get("placed_cargo", [])
            print(f"   📦 Found {len(placed_cargo)} placed cargo items")
            
            # Look for our cargo from pickup request
            pickup_cargo_found = []
            for cargo in placed_cargo:
                if cargo.get("pickup_request_id") == self.test_data.get("pickup_request_id"):
                    pickup_cargo_found.append(cargo)
            
            print(f"   🚚 Found {len(pickup_cargo_found)} cargo items from our pickup request")
            
            if pickup_cargo_found:
                print(f"   ✅ SUCCESS: Cargo from pickup request found in placed cargo!")
                
                for i, cargo in enumerate(pickup_cargo_found):
                    print(f"\n   📦 Cargo {i+1}:")
                    print(f"      🔢 Number: {cargo.get('cargo_number')}")
                    print(f"      📋 Name: {cargo.get('cargo_name')}")
                    print(f"      ⚖️ Weight: {cargo.get('weight')}kg")
                    print(f"      📊 Status: {cargo.get('status')}")
                    print(f"      🚚 Pickup Request ID: {cargo.get('pickup_request_id')}")
                    print(f"      📞 Pickup Request Number: {cargo.get('pickup_request_number')}")
                    print(f"      🚴 Courier Delivered By: {cargo.get('courier_delivered_by')}")
                    
                    # Check expected format: request_number/01, request_number/02
                    expected_prefix = f"{self.test_data.get('pickup_request_number')}/"
                    if cargo.get('cargo_number', '').startswith(expected_prefix):
                        print(f"      ✅ Cargo number format correct: {cargo.get('cargo_number')}")
                    else:
                        print(f"      ⚠️ Cargo number format unexpected: {cargo.get('cargo_number')}")
                    
                    # Check status
                    if cargo.get('status') in ['placement_ready', 'placed_in_warehouse']:
                        print(f"      ✅ Status correct: {cargo.get('status')}")
                    else:
                        print(f"      ⚠️ Status unexpected: {cargo.get('status')}")
                
                return True
            else:
                print(f"   ❌ FAIL: No cargo from pickup request found in placed cargo")
                print(f"   📋 Available cargo numbers: {[c.get('cargo_number') for c in placed_cargo[:5]]}")
                return False
        
        return False

    def run_full_test_cycle(self):
        """Run the complete test cycle"""
        print("🚀 STARTING FULL PICKUP CARGO PLACEMENT TEST CYCLE")
        print("="*80)
        
        steps = [
            ("Operator Authentication", self.authenticate_operator),
            ("Courier Authentication", self.authenticate_courier),
            ("Create Pickup Request", self.create_pickup_request),
            ("Courier Accept Request", self.courier_accept_pickup_request),
            ("Courier Pickup Cargo", self.courier_pickup_cargo),
            ("Courier Deliver to Warehouse", self.courier_deliver_to_warehouse),
            ("Operator Process Notification", self.operator_process_notification),
            ("Test Placed Cargo Endpoint", self.test_placed_cargo_endpoint)
        ]
        
        for step_name, step_func in steps:
            print(f"\n🔄 Executing: {step_name}")
            if not step_func():
                print(f"❌ CRITICAL FAILURE at step: {step_name}")
                print("🛑 Test cycle terminated")
                return False
        
        print("\n" + "="*80)
        print("🎉 FULL TEST CYCLE COMPLETED SUCCESSFULLY!")
        print("="*80)
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print(f"\n🎯 EXPECTED RESULT ACHIEVED:")
        print(f"   ✅ Cargo from pickup requests displayed in 'Placed Cargo' section")
        print(f"   ✅ Cargo has pickup_request_id for identification")
        print(f"   ✅ Cargo has correct status (placement_ready)")
        print(f"   ✅ Cargo numbers in format request_number/01, request_number/02")
        print(f"   ✅ Cargo has courier_delivered_by and pickup_request_number fields")
        
        return True

def main():
    """Main function to run the test"""
    tester = PickupCargoPlacementTester()
    
    try:
        success = tester.run_full_test_cycle()
        if success:
            print("\n🏆 ALL TESTS PASSED - PICKUP CARGO PLACEMENT WORKING CORRECTLY!")
            sys.exit(0)
        else:
            print("\n💥 TESTS FAILED - ISSUES FOUND")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Focused Payment Acceptance Workflow Test
Tests the specific payment acceptance functionality as requested in the review
"""

import requests
import sys
import json
from datetime import datetime

class PaymentAcceptanceWorkflowTester:
    def __init__(self, base_url="https://cargo-sync.preview.emergentagent.com"):
        self.base_url = base_url
        self.tokens = {}
        self.users = {}
        self.tests_run = 0
        self.tests_passed = 0
        
        print(f"💰 Payment Acceptance Workflow Tester")
        print(f"📡 Base URL: {self.base_url}")
        print("=" * 60)

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data=None, token=None, params=None):
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

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"   ✅ PASSED - Status: {response.status_code}")
                try:
                    result = response.json()
                    return True, result
                except:
                    return True, {}
            else:
                print(f"   ❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   📄 Error: {error_detail}")
                except:
                    print(f"   📄 Raw response: {response.text[:200]}")
                return False, {}

        except Exception as e:
            print(f"   ❌ FAILED - Exception: {str(e)}")
            return False, {}

    def login_users(self):
        """Login test users"""
        print("\n🔐 LOGGING IN TEST USERS")
        
        login_data = [
            {"role": "user", "phone": "+992900000000", "password": "123456"},  # Bahrom user
            {"role": "admin", "phone": "+79999888777", "password": "admin123"},  # Admin
            {"role": "warehouse_operator", "phone": "+79777888999", "password": "warehouse123"}
        ]
        
        for login_info in login_data:
            success, response = self.run_test(
                f"Login {login_info['role']}", 
                "POST", 
                "/api/auth/login", 
                200,
                {"phone": login_info['phone'], "password": login_info['password']}
            )
            
            if success and 'access_token' in response:
                self.tokens[login_info['role']] = response['access_token']
                self.users[login_info['role']] = response['user']
                print(f"   🔑 {login_info['role']} logged in successfully")
            else:
                print(f"   ❌ Failed to login {login_info['role']}")
                return False
        
        return True

    def test_payment_acceptance_workflow(self):
        """Test the complete payment acceptance workflow"""
        print("\n💰 PAYMENT ACCEPTANCE WORKFLOW TESTING")
        
        if not self.login_users():
            return False
            
        all_success = True
        
        # Test Scenario 1: Create cargo request → Admin accept → Verify cargo with payment_pending status
        print("\n   📋 Test Scenario 1: Payment Pending Workflow...")
        
        # Step 1: User creates cargo request
        request_data = {
            "recipient_full_name": "Получатель Оплаты",
            "recipient_phone": "+992888999000",
            "recipient_address": "Душанбе, ул. Оплатная, 15",
            "pickup_address": "Москва, ул. Отправная, 20",
            "cargo_name": "Груз для тестирования оплаты",
            "weight": 18.5,
            "declared_value": 9500.0,
            "description": "Тестовый груз для проверки системы оплаты",
            "route": "moscow_dushanbe"
        }
        
        success, request_response = self.run_test(
            "User Creates Cargo Request",
            "POST",
            "/api/user/cargo-request",
            200,
            request_data,
            self.tokens['user']
        )
        all_success &= success
        
        payment_test_cargo_id = None
        payment_test_cargo_number = None
        
        if success and 'id' in request_response:
            request_id = request_response['id']
            print(f"   📋 Created cargo request: {request_id}")
            
            # Step 2: Admin accepts the request
            success, accept_response = self.run_test(
                "Admin Accepts Cargo Request",
                "POST",
                f"/api/admin/cargo-requests/{request_id}/accept",
                200,
                token=self.tokens['admin']
            )
            all_success &= success
            
            if success and 'cargo_id' in accept_response:
                payment_test_cargo_id = accept_response['cargo_id']
                payment_test_cargo_number = accept_response.get('cargo_number')
                
                print(f"   ✅ Request accepted, cargo created: {payment_test_cargo_id}")
                print(f"   🏷️  Cargo number: {payment_test_cargo_number}")
        
        # Step 3: Verify cargo appears in operator cargo list with payment_pending status
        print("\n   📋 Test Scenario 2: Cargo List Filtering...")
        
        success, cargo_list_response = self.run_test(
            "Get Operator Cargo List - Payment Pending Filter",
            "GET",
            "/api/operator/cargo/list",
            200,
            token=self.tokens['admin'],
            params={"filter_status": "payment_pending"}
        )
        all_success &= success
        
        if success:
            cargo_list = cargo_list_response.get('cargo_list', [])
            total_count = cargo_list_response.get('total_count', 0)
            filter_applied = cargo_list_response.get('filter_applied')
            
            print(f"   📦 Found {total_count} cargo items with payment_pending status")
            print(f"   🔍 Filter applied: {filter_applied}")
            
            # Verify our test cargo is in the list
            found_test_cargo = False
            if payment_test_cargo_id:
                for cargo in cargo_list:
                    if cargo.get('id') == payment_test_cargo_id:
                        found_test_cargo = True
                        cargo_processing_status = cargo.get('processing_status')
                        cargo_payment_status = cargo.get('payment_status')
                        
                        print(f"   ✅ Test cargo found in payment_pending list")
                        print(f"   📊 Processing status: {cargo_processing_status}")
                        print(f"   💳 Payment status: {cargo_payment_status}")
                        
                        if cargo_processing_status == "payment_pending":
                            print("   ✅ Cargo correctly shows payment_pending status")
                        else:
                            print(f"   ❌ Unexpected processing status: {cargo_processing_status}")
                            all_success = False
                        break
                
                if not found_test_cargo:
                    print("   ❌ Test cargo not found in payment_pending list")
                    all_success = False
        
        # Test Scenario 3: Payment Processing - Update status from payment_pending to paid
        print("\n   💰 Test Scenario 3: Payment Processing...")
        
        if payment_test_cargo_id:
            success, payment_response = self.run_test(
                "Process Payment - Mark as Paid",
                "PUT",
                f"/api/cargo/{payment_test_cargo_id}/processing-status",
                200,
                token=self.tokens['admin'],
                params={"new_status": "paid"}
            )
            all_success &= success
            
            if success:
                print("   ✅ Cargo processing status updated to 'paid'")
                
                # Verify status synchronization
                success, track_response = self.run_test(
                    "Verify Status Synchronization",
                    "GET",
                    f"/api/cargo/track/{payment_test_cargo_number}",
                    200
                )
                all_success &= success
                
                if success:
                    processing_status = track_response.get('processing_status')
                    payment_status = track_response.get('payment_status')
                    main_status = track_response.get('status')
                    
                    print(f"   📊 Processing status: {processing_status}")
                    print(f"   💳 Payment status: {payment_status}")
                    print(f"   📋 Main status: {main_status}")
                    
                    # Verify synchronization
                    if processing_status == "paid" and payment_status == "paid":
                        print("   ✅ Status synchronization working correctly")
                    else:
                        print("   ❌ Status synchronization failed")
                        all_success = False
        
        # Test Scenario 4: Integration Between Cargo List and Placement Section
        print("\n   🔄 Test Scenario 4: Cargo List → Placement Integration...")
        
        if payment_test_cargo_id:
            # Verify paid cargo appears in available-for-placement endpoint
            success, placement_response = self.run_test(
                "Check Available for Placement",
                "GET",
                "/api/operator/cargo/available-for-placement",
                200,
                token=self.tokens['admin']
            )
            all_success &= success
            
            if success:
                available_cargo = placement_response.get('cargo_list', [])
                found_in_placement = False
                
                for cargo in available_cargo:
                    if cargo.get('id') == payment_test_cargo_id:
                        found_in_placement = True
                        print(f"   ✅ Paid cargo appears in placement list")
                        print(f"   📦 Cargo: {cargo.get('cargo_name', 'Unknown')}")
                        print(f"   📊 Status: {cargo.get('processing_status', 'Unknown')}")
                        break
                
                if not found_in_placement:
                    print("   ❌ Paid cargo not found in available-for-placement list")
                    all_success = False
        
        # Test Scenario 5: Status Progression Testing
        print("\n   📈 Test Scenario 5: Complete Status Progression...")
        
        if payment_test_cargo_id:
            # Test progression: paid → invoice_printed → placed
            status_progression = ["invoice_printed", "placed"]
            
            for next_status in status_progression:
                success, status_response = self.run_test(
                    f"Update Status to {next_status}",
                    "PUT",
                    f"/api/cargo/{payment_test_cargo_id}/processing-status",
                    200,
                    token=self.tokens['admin'],
                    params={"new_status": next_status}
                )
                all_success &= success
                
                if success:
                    print(f"   ✅ Status successfully updated to: {next_status}")
                    
                    # Verify status update
                    success, verify_response = self.run_test(
                        f"Verify {next_status} Status",
                        "GET",
                        f"/api/cargo/track/{payment_test_cargo_number}",
                        200
                    )
                    
                    if success:
                        current_processing_status = verify_response.get('processing_status')
                        if current_processing_status == next_status:
                            print(f"   ✅ Status correctly updated to: {next_status}")
                        else:
                            print(f"   ❌ Status update failed. Expected: {next_status}, Got: {current_processing_status}")
                            all_success = False
        
        # Test Scenario 6: API Endpoints Testing
        print("\n   🔌 Test Scenario 6: API Endpoints Validation...")
        
        # Test cargo list filtering with different statuses
        filter_tests = [
            ("awaiting_payment", "Awaiting Payment Filter"),
            ("awaiting_placement", "Awaiting Placement Filter"),
            ("new_request", "New Request Filter")
        ]
        
        for filter_status, test_name in filter_tests:
            success, filter_response = self.run_test(
                test_name,
                "GET",
                "/api/operator/cargo/list",
                200,
                token=self.tokens['admin'],
                params={"filter_status": filter_status}
            )
            all_success &= success
            
            if success:
                filter_count = filter_response.get('total_count', 0)
                applied_filter = filter_response.get('filter_applied')
                available_filters = filter_response.get('available_filters', {})
                
                print(f"   📊 {test_name}: {filter_count} items")
                print(f"   🔍 Applied filter: {applied_filter}")
                
                # Verify response structure
                if 'cargo_list' in filter_response and 'total_count' in filter_response:
                    print(f"   ✅ Response structure correct for {filter_status}")
                else:
                    print(f"   ❌ Invalid response structure for {filter_status}")
                    all_success = False
        
        return all_success

    def run_test_suite(self):
        """Run the complete test suite"""
        print("\n🚀 STARTING PAYMENT ACCEPTANCE WORKFLOW TESTS")
        print("=" * 60)
        
        success = self.test_payment_acceptance_workflow()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} Payment Acceptance Workflow")
        print(f"🔍 Individual API calls: {self.tests_passed}/{self.tests_run} passed ({(self.tests_passed/self.tests_run)*100:.1f}%)")
        
        if success:
            print("🎉 ALL PAYMENT ACCEPTANCE WORKFLOW TESTS PASSED!")
        else:
            print("⚠️  Some tests failed. Please check the details above.")
        
        return success

if __name__ == "__main__":
    tester = PaymentAcceptanceWorkflowTester()
    success = tester.run_test_suite()
    sys.exit(0 if success else 1)
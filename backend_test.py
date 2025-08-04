#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for КаргоТранс Application
Tests all endpoints including authentication, cargo management, admin functions, and warehouse operations
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class CargoTransportAPITester:
    def __init__(self, base_url="https://ed0a5ce9-6176-44ad-aa59-bdce5a4a2cad.preview.emergentagent.com"):
        self.base_url = base_url
        self.tokens = {}  # Store tokens for different users
        self.users = {}   # Store user data
        self.cargo_ids = []  # Store created cargo IDs
        self.tests_run = 0
        self.tests_passed = 0
        
        print(f"🚛 КаргоТранс API Tester")
        print(f"📡 Base URL: {self.base_url}")
        print("=" * 60)

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
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"   ✅ PASSED - Status: {response.status_code}")
                try:
                    result = response.json()
                    if isinstance(result, dict) and len(str(result)) < 200:
                        print(f"   📄 Response: {result}")
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

    def test_health_check(self):
        """Test basic health check"""
        print("\n🏥 HEALTH CHECK")
        success, _ = self.run_test("Health Check", "GET", "/api/health", 200)
        return success

    def test_user_registration(self):
        """Test user registration for all roles"""
        print("\n👥 USER REGISTRATION")
        
        # Test data as specified in requirements
        test_users = [
            {
                "name": "Regular User",
                "data": {
                    "full_name": "Иван Петров",
                    "phone": "+79123456789",
                    "password": "123456",
                    "role": "user"
                }
            },
            {
                "name": "Administrator", 
                "data": {
                    "full_name": "Админ Системы",
                    "phone": "+79987654321",
                    "password": "admin123",
                    "role": "admin"
                }
            },
            {
                "name": "Warehouse Operator",
                "data": {
                    "full_name": "Склад Операторов", 
                    "phone": "+79555666777",
                    "password": "warehouse123",
                    "role": "warehouse_operator"
                }
            }
        ]
        
        all_success = True
        for user_info in test_users:
            success, response = self.run_test(
                f"Register {user_info['name']}", 
                "POST", 
                "/api/auth/register", 
                200, 
                user_info['data']
            )
            
            if success and 'access_token' in response:
                role = user_info['data']['role']
                self.tokens[role] = response['access_token']
                self.users[role] = response['user']
                print(f"   🔑 Token stored for {role}")
            else:
                all_success = False
                
        return all_success

    def test_user_login(self):
        """Test user login for all registered users"""
        print("\n🔐 USER LOGIN")
        
        login_data = [
            {"role": "user", "phone": "+79123456789", "password": "123456"},
            {"role": "admin", "phone": "+79987654321", "password": "admin123"},
            {"role": "warehouse_operator", "phone": "+79555666777", "password": "warehouse123"}
        ]
        
        all_success = True
        for login_info in login_data:
            success, response = self.run_test(
                f"Login {login_info['role']}", 
                "POST", 
                "/api/auth/login", 
                200,
                {"phone": login_info['phone'], "password": login_info['password']}
            )
            
            if success and 'access_token' in response:
                # Update token (in case registration token expired)
                self.tokens[login_info['role']] = response['access_token']
                self.users[login_info['role']] = response['user']
            else:
                all_success = False
                
        return all_success

    def test_cargo_creation(self):
        """Test cargo creation by regular user"""
        print("\n📦 CARGO CREATION")
        
        if 'user' not in self.tokens:
            print("   ❌ No user token available")
            return False
            
        cargo_data = {
            "recipient_name": "Петр Сидоров",
            "recipient_phone": "+79888999000", 
            "route": "moscow_to_tajikistan",
            "weight": 25.5,
            "description": "Документы и посылки",
            "declared_value": 15000.0,
            "sender_address": "Москва, ул. Тверская, 1",
            "recipient_address": "Душанбе, ул. Рудаки, 10"
        }
        
        success, response = self.run_test(
            "Create Cargo",
            "POST", 
            "/api/cargo/create",
            200,
            cargo_data,
            self.tokens['user']
        )
        
        if success and 'id' in response:
            self.cargo_ids.append(response['id'])
            print(f"   📋 Cargo created with ID: {response['id']}")
            print(f"   🏷️  Cargo number: {response.get('cargo_number', 'N/A')}")
            
        return success

    def test_my_cargo(self):
        """Test fetching user's cargo"""
        print("\n📋 MY CARGO")
        
        if 'user' not in self.tokens:
            print("   ❌ No user token available")
            return False
            
        success, response = self.run_test(
            "Get My Cargo",
            "GET",
            "/api/cargo/my", 
            200,
            token=self.tokens['user']
        )
        
        if success:
            cargo_count = len(response) if isinstance(response, list) else 0
            print(f"   📊 Found {cargo_count} cargo items")
            
        return success

    def test_cargo_tracking(self):
        """Test cargo tracking without authentication"""
        print("\n🔍 CARGO TRACKING")
        
        # First get a cargo number from created cargo
        if not self.cargo_ids:
            print("   ❌ No cargo created yet")
            return False
            
        # Get cargo details first to get the cargo number
        if 'user' not in self.tokens:
            print("   ❌ No user token available")
            return False
            
        success, my_cargo = self.run_test(
            "Get Cargo for Tracking",
            "GET",
            "/api/cargo/my",
            200,
            token=self.tokens['user']
        )
        
        if not success or not my_cargo:
            print("   ❌ Could not get cargo for tracking")
            return False
            
        cargo_number = my_cargo[0].get('cargo_number') if my_cargo else None
        if not cargo_number:
            print("   ❌ No cargo number found")
            return False
            
        # Test tracking without authentication
        success, response = self.run_test(
            f"Track Cargo {cargo_number}",
            "GET",
            f"/api/cargo/track/{cargo_number}",
            200
        )
        
        return success

    def test_admin_functions(self):
        """Test admin-only functions"""
        print("\n👑 ADMIN FUNCTIONS")
        
        if 'admin' not in self.tokens:
            print("   ❌ No admin token available")
            return False
            
        all_success = True
        
        # Test get all users
        success, users = self.run_test(
            "Get All Users",
            "GET",
            "/api/admin/users",
            200,
            token=self.tokens['admin']
        )
        all_success &= success
        
        if success:
            user_count = len(users) if isinstance(users, list) else 0
            print(f"   👥 Found {user_count} users")
        
        # Test get all cargo
        success, cargo = self.run_test(
            "Get All Cargo",
            "GET", 
            "/api/cargo/all",
            200,
            token=self.tokens['admin']
        )
        all_success &= success
        
        if success:
            cargo_count = len(cargo) if isinstance(cargo, list) else 0
            print(f"   📦 Found {cargo_count} cargo items")
            
        # Test cargo status update
        if self.cargo_ids:
            success, _ = self.run_test(
                "Update Cargo Status to Accepted",
                "PUT",
                f"/api/cargo/{self.cargo_ids[0]}/status",
                200,
                token=self.tokens['admin'],
                params={"status": "accepted"}
            )
            all_success &= success
            
        return all_success

    def test_warehouse_functions(self):
        """Test warehouse operator functions"""
        print("\n🏭 WAREHOUSE FUNCTIONS")
        
        if 'warehouse_operator' not in self.tokens:
            print("   ❌ No warehouse operator token available")
            return False
            
        all_success = True
        
        # Test get warehouse cargo
        success, warehouse_cargo = self.run_test(
            "Get Warehouse Cargo",
            "GET",
            "/api/warehouse/cargo",
            200,
            token=self.tokens['warehouse_operator']
        )
        all_success &= success
        
        if success:
            cargo_count = len(warehouse_cargo) if isinstance(warehouse_cargo, list) else 0
            print(f"   📦 Found {cargo_count} warehouse cargo items")
        
        # Test cargo search
        success, search_results = self.run_test(
            "Search Cargo",
            "GET",
            "/api/warehouse/search",
            200,
            token=self.tokens['warehouse_operator'],
            params={"query": "CG"}
        )
        all_success &= success
        
        if success:
            result_count = len(search_results) if isinstance(search_results, list) else 0
            print(f"   🔍 Found {result_count} search results")
            
        # Test status update with warehouse location
        if self.cargo_ids:
            success, _ = self.run_test(
                "Update Cargo Status to In Transit",
                "PUT",
                f"/api/cargo/{self.cargo_ids[0]}/status",
                200,
                token=self.tokens['warehouse_operator'],
                params={"status": "in_transit", "warehouse_location": "Склад А, Стеллаж 5"}
            )
            all_success &= success
            
        return all_success

    def test_notifications(self):
        """Test notification system"""
        print("\n🔔 NOTIFICATIONS")
        
        if 'user' not in self.tokens:
            print("   ❌ No user token available")
            return False
            
        success, notifications = self.run_test(
            "Get User Notifications",
            "GET",
            "/api/notifications",
            200,
            token=self.tokens['user']
        )
        
        if success:
            notif_count = len(notifications) if isinstance(notifications, list) else 0
            unread_count = len([n for n in notifications if not n.get('is_read', True)]) if isinstance(notifications, list) else 0
            print(f"   📬 Found {notif_count} notifications ({unread_count} unread)")
            
        return success

    def test_error_cases(self):
        """Test error handling"""
        print("\n⚠️  ERROR HANDLING")
        
        all_success = True
        
        # Test invalid login
        success, _ = self.run_test(
            "Invalid Login",
            "POST",
            "/api/auth/login",
            401,
            {"phone": "+79999999999", "password": "wrongpassword"}
        )
        all_success &= success
        
        # Test unauthorized access
        success, _ = self.run_test(
            "Unauthorized Admin Access",
            "GET",
            "/api/admin/users",
            401
        )
        all_success &= success
        
        # Test non-existent cargo tracking
        success, _ = self.run_test(
            "Track Non-existent Cargo",
            "GET",
            "/api/cargo/track/INVALID123",
            404
        )
        all_success &= success
        
        return all_success

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting comprehensive API testing...")
        
        test_results = []
        
        # Run test suites in order
        test_suites = [
            ("Health Check", self.test_health_check),
            ("User Registration", self.test_user_registration), 
            ("User Login", self.test_user_login),
            ("Cargo Creation", self.test_cargo_creation),
            ("My Cargo", self.test_my_cargo),
            ("Cargo Tracking", self.test_cargo_tracking),
            ("Admin Functions", self.test_admin_functions),
            ("Warehouse Functions", self.test_warehouse_functions),
            ("Notifications", self.test_notifications),
            ("Error Handling", self.test_error_cases)
        ]
        
        for suite_name, test_func in test_suites:
            try:
                result = test_func()
                test_results.append((suite_name, result))
                if result:
                    print(f"✅ {suite_name} - PASSED")
                else:
                    print(f"❌ {suite_name} - FAILED")
            except Exception as e:
                print(f"💥 {suite_name} - ERROR: {str(e)}")
                test_results.append((suite_name, False))
        
        # Print final results
        print("\n" + "=" * 60)
        print("📊 FINAL TEST RESULTS")
        print("=" * 60)
        
        passed_suites = sum(1 for _, result in test_results if result)
        total_suites = len(test_results)
        
        for suite_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {suite_name}")
            
        print(f"\n📈 Overall Results:")
        print(f"   Test Suites: {passed_suites}/{total_suites} passed")
        print(f"   Individual Tests: {self.tests_passed}/{self.tests_run} passed")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if passed_suites == total_suites and self.tests_passed == self.tests_run:
            print("\n🎉 ALL TESTS PASSED! Backend API is working correctly.")
            return 0
        else:
            print(f"\n⚠️  {total_suites - passed_suites} test suite(s) failed.")
            return 1

def main():
    """Main test execution"""
    tester = CargoTransportAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())
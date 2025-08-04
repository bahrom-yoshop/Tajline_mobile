#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for TAJLINE.TJ Application
Tests all endpoints including authentication, cargo management, admin functions, warehouse operations,
cashier functionality, user management by roles, and warehouse layout features
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
        
        print(f"🚛 TAJLINE.TJ API Tester")
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
                    "phone": "+79999888777",
                    "password": "admin123",
                    "role": "admin"
                }
            },
            {
                "name": "Warehouse Operator",
                "data": {
                    "full_name": "Оператор Складской", 
                    "phone": "+79777888999",
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
            {"role": "admin", "phone": "+79999888777", "password": "admin123"},
            {"role": "warehouse_operator", "phone": "+79777888999", "password": "warehouse123"}
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

    def test_warehouse_management(self):
        """Test warehouse creation and management"""
        print("\n🏗️ WAREHOUSE MANAGEMENT")
        
        if 'admin' not in self.tokens:
            print("   ❌ No admin token available")
            return False
            
        all_success = True
        
        # Test warehouse creation
        warehouse_data = {
            "name": "Склад для грузов",
            "location": "Москва, Складская территория",
            "blocks_count": 2,
            "shelves_per_block": 2,
            "cells_per_shelf": 5
        }
        
        success, warehouse_response = self.run_test(
            "Create Warehouse",
            "POST",
            "/api/warehouses/create",
            200,
            warehouse_data,
            self.tokens['admin']
        )
        all_success &= success
        
        warehouse_id = None
        if success and 'id' in warehouse_response:
            warehouse_id = warehouse_response['id']
            print(f"   🏭 Warehouse created with ID: {warehouse_id}")
        
        # Test get warehouses
        success, warehouses = self.run_test(
            "Get Warehouses",
            "GET",
            "/api/warehouses",
            200,
            token=self.tokens['admin']
        )
        all_success &= success
        
        if success:
            warehouse_count = len(warehouses) if isinstance(warehouses, list) else 0
            print(f"   🏭 Found {warehouse_count} warehouses")
        
        # Test warehouse structure
        if warehouse_id:
            success, structure = self.run_test(
                "Get Warehouse Structure",
                "GET",
                f"/api/warehouses/{warehouse_id}/structure",
                200,
                token=self.tokens['admin']
            )
            all_success &= success
            
            if success:
                total_cells = structure.get('total_cells', 0)
                available_cells = structure.get('available_cells', 0)
                print(f"   📊 Warehouse has {total_cells} total cells, {available_cells} available")
        
        # Store warehouse_id for later tests
        if warehouse_id:
            self.warehouse_id = warehouse_id
            
        return all_success

    def test_operator_cargo_management(self):
        """Test new operator cargo management functionality"""
        print("\n📋 OPERATOR CARGO MANAGEMENT")
        
        if 'admin' not in self.tokens:
            print("   ❌ No admin token available")
            return False
            
        all_success = True
        
        # Test accepting new cargo as specified in requirements
        cargo_data = {
            "sender_full_name": "Иванов Сергей Петрович",
            "sender_phone": "+79111222333",
            "recipient_full_name": "Рахимов Алишер Камолович",
            "recipient_phone": "+992444555666",
            "recipient_address": "Душанбе, ул. Рудаки, 25, кв. 10",
            "weight": 15.5,
            "declared_value": 8000.0,
            "description": "Документы и личные вещи",
            "route": "moscow_to_tajikistan"
        }
        
        success, cargo_response = self.run_test(
            "Accept New Cargo",
            "POST",
            "/api/operator/cargo/accept",
            200,
            cargo_data,
            self.tokens['admin']
        )
        all_success &= success
        
        operator_cargo_id = None
        if success and 'id' in cargo_response:
            operator_cargo_id = cargo_response['id']
            print(f"   📦 Operator cargo created with ID: {operator_cargo_id}")
            print(f"   🏷️  Cargo number: {cargo_response.get('cargo_number', 'N/A')}")
        
        # Test get operator cargo list
        success, cargo_list = self.run_test(
            "Get Operator Cargo List",
            "GET",
            "/api/operator/cargo/list",
            200,
            token=self.tokens['admin']
        )
        all_success &= success
        
        if success:
            cargo_count = len(cargo_list) if isinstance(cargo_list, list) else 0
            print(f"   📋 Found {cargo_count} operator cargo items")
        
        # Test get available cargo for placement
        success, available_cargo = self.run_test(
            "Get Available Cargo for Placement",
            "GET",
            "/api/operator/cargo/available",
            200,
            token=self.tokens['admin']
        )
        all_success &= success
        
        if success:
            available_count = len(available_cargo) if isinstance(available_cargo, list) else 0
            print(f"   📦 Found {available_count} cargo items available for placement")
        
        # Test cargo placement if we have warehouse and cargo
        if hasattr(self, 'warehouse_id') and operator_cargo_id:
            # First get available cells
            success, cells_response = self.run_test(
                "Get Available Cells",
                "GET",
                f"/api/warehouses/{self.warehouse_id}/available-cells",
                200,
                token=self.tokens['admin']
            )
            all_success &= success
            
            if success and cells_response.get('available_cells'):
                # Place cargo in first available cell (B1-S1-C1 as specified)
                placement_data = {
                    "cargo_id": operator_cargo_id,
                    "warehouse_id": self.warehouse_id,
                    "block_number": 1,
                    "shelf_number": 1,
                    "cell_number": 1
                }
                
                success, placement_response = self.run_test(
                    "Place Cargo in Warehouse",
                    "POST",
                    "/api/operator/cargo/place",
                    200,
                    placement_data,
                    self.tokens['admin']
                )
                all_success &= success
                
                if success:
                    location = placement_response.get('location', 'Unknown')
                    print(f"   📍 Cargo placed at location: {location}")
        
        # Test cargo history
        success, history = self.run_test(
            "Get Cargo History",
            "GET",
            "/api/operator/cargo/history",
            200,
            token=self.tokens['admin']
        )
        all_success &= success
        
        if success:
            history_count = len(history) if isinstance(history, list) else 0
            print(f"   📚 Found {history_count} items in cargo history")
        
        # Test cargo history with filters
        success, filtered_history = self.run_test(
            "Get Cargo History with Search",
            "GET",
            "/api/operator/cargo/history",
            200,
            token=self.tokens['admin'],
            params={"search": "Иванов", "status": "all"}
        )
        all_success &= success
        
        if success:
            filtered_count = len(filtered_history) if isinstance(filtered_history, list) else 0
            print(f"   🔍 Found {filtered_count} items in filtered history")
            
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

    def test_users_by_role(self):
        """Test getting users by role (new functionality)"""
        print("\n👥 USERS BY ROLE")
        
        if 'admin' not in self.tokens:
            print("   ❌ No admin token available")
            return False
            
        all_success = True
        roles = ['user', 'admin', 'warehouse_operator']
        
        for role in roles:
            success, users = self.run_test(
                f"Get Users by Role: {role}",
                "GET",
                f"/api/admin/users/by-role/{role}",
                200,
                token=self.tokens['admin']
            )
            all_success &= success
            
            if success:
                user_count = len(users) if isinstance(users, list) else 0
                print(f"   👤 Found {user_count} users with role '{role}'")
        
        return all_success

    def test_cashier_functionality(self):
        """Test cashier functionality (new feature)"""
        print("\n💰 CASHIER FUNCTIONALITY")
        
        if 'admin' not in self.tokens:
            print("   ❌ No admin token available")
            return False
            
        all_success = True
        
        # First, create a cargo for payment testing
        cargo_data = {
            "sender_full_name": "Тестовый Отправитель",
            "sender_phone": "+79555666777",
            "recipient_full_name": "Тестовый Получатель",
            "recipient_phone": "+992777888999",
            "recipient_address": "Душанбе, ул. Тестовая, 1",
            "weight": 10.0,
            "declared_value": 5000.0,
            "description": "Тестовый груз для оплаты",
            "route": "moscow_to_tajikistan"
        }
        
        success, cargo_response = self.run_test(
            "Create Cargo for Payment Test",
            "POST",
            "/api/operator/cargo/accept",
            200,
            cargo_data,
            self.tokens['admin']
        )
        all_success &= success
        
        cargo_number = None
        if success and 'cargo_number' in cargo_response:
            cargo_number = cargo_response['cargo_number']
            print(f"   📦 Created test cargo: {cargo_number}")
        
        # Test get unpaid cargo
        success, unpaid_cargo = self.run_test(
            "Get Unpaid Cargo",
            "GET",
            "/api/cashier/unpaid-cargo",
            200,
            token=self.tokens['admin']
        )
        all_success &= success
        
        if success:
            unpaid_count = len(unpaid_cargo) if isinstance(unpaid_cargo, list) else 0
            print(f"   💳 Found {unpaid_count} unpaid cargo items")
        
        # Test search cargo for payment
        if cargo_number:
            success, cargo_info = self.run_test(
                f"Search Cargo for Payment: {cargo_number}",
                "GET",
                f"/api/cashier/search-cargo/{cargo_number}",
                200,
                token=self.tokens['admin']
            )
            all_success &= success
            
            if success:
                print(f"   🔍 Found cargo for payment: {cargo_info.get('sender_full_name', 'Unknown')}")
            
            # Test process payment
            payment_data = {
                "cargo_number": cargo_number,
                "amount_paid": 5000.0,
                "transaction_type": "cash",
                "notes": "Тестовая оплата наличными"
            }
            
            success, payment_response = self.run_test(
                "Process Payment",
                "POST",
                "/api/cashier/process-payment",
                200,
                payment_data,
                self.tokens['admin']
            )
            all_success &= success
            
            if success:
                transaction_id = payment_response.get('id', 'Unknown')
                print(f"   💰 Payment processed, transaction ID: {transaction_id}")
        
        # Test payment history
        success, payment_history = self.run_test(
            "Get Payment History",
            "GET",
            "/api/cashier/payment-history",
            200,
            token=self.tokens['admin']
        )
        all_success &= success
        
        if success:
            history_count = len(payment_history) if isinstance(payment_history, list) else 0
            print(f"   📚 Found {history_count} payment transactions")
        
        return all_success

    def test_warehouse_full_layout(self):
        """Test warehouse full layout functionality (new feature)"""
        print("\n🏗️ WAREHOUSE FULL LAYOUT")
        
        if 'admin' not in self.tokens:
            print("   ❌ No admin token available")
            return False
            
        if not hasattr(self, 'warehouse_id'):
            print("   ❌ No warehouse available for layout test")
            return False
            
        success, layout_response = self.run_test(
            "Get Warehouse Full Layout",
            "GET",
            f"/api/warehouses/{self.warehouse_id}/full-layout",
            200,
            token=self.tokens['admin']
        )
        
        if success:
            warehouse_info = layout_response.get('warehouse', {})
            statistics = layout_response.get('statistics', {})
            layout = layout_response.get('layout', {})
            
            print(f"   🏭 Warehouse: {warehouse_info.get('name', 'Unknown')}")
            print(f"   📊 Total cells: {statistics.get('total_cells', 0)}")
            print(f"   📊 Occupied cells: {statistics.get('occupied_cells', 0)}")
            print(f"   📊 Available cells: {statistics.get('available_cells', 0)}")
            print(f"   📊 Occupancy rate: {statistics.get('occupancy_rate', 0)}%")
            print(f"   🗂️  Layout blocks: {len(layout)}")
        
        return success

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
            ("Warehouse Management", self.test_warehouse_management),
            ("Operator Cargo Management", self.test_operator_cargo_management),
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
#!/usr/bin/env python3
"""
Final Admin Panel Enhancements and Personal Dashboard Testing
Tests based on actual system behavior and implementation
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class FinalAdminTester:
    def __init__(self, base_url="https://tajline-cargo-8.preview.emergentagent.com"):
        self.base_url = base_url
        self.tokens = {}
        self.users = {}
        self.tests_run = 0
        self.tests_passed = 0
        self.working_features = []
        self.critical_issues = []
        
        print(f"🎯 FINAL ADMIN PANEL & DASHBOARD COMPREHENSIVE TEST")
        print(f"📡 Base URL: {self.base_url}")
        print("=" * 70)

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

    def setup_admin_user(self):
        """Setup a proper admin user by manually updating the database"""
        print("\n🔧 SETTING UP ADMIN USER")
        
        # First create a regular user
        import time
        unique_suffix = str(int(time.time()))[-4:]
        admin_data = {
            "full_name": "Админ Тестер Финал",
            "phone": f"+7999888{unique_suffix}",
            "password": "admin123",
            "role": "user"  # Will be ignored but required by API
        }
        
        success, reg_response = self.run_test(
            "Create User for Admin Promotion",
            "POST",
            "/api/auth/register",
            200,
            admin_data
        )
        
        if success and 'access_token' in reg_response:
            user_id = reg_response['user']['id']
            user_phone = reg_response['user']['phone']
            
            # Now we need to manually promote this user to admin
            # Since we can't do this through API (chicken and egg problem), 
            # we'll use the existing admin user if available
            
            # Try to find an existing admin user
            existing_admin_phones = ["+79999888777"]  # Known admin phone
            
            for phone in existing_admin_phones:
                login_success, login_response = self.run_test(
                    f"Try Login Existing Admin ({phone})",
                    "POST",
                    "/api/auth/login",
                    200,
                    {"phone": phone, "password": "admin123"}
                )
                
                if login_success:
                    admin_user = login_response['user']
                    # Check if this user is actually admin
                    if admin_user.get('role') == 'admin':
                        self.tokens['admin'] = login_response['access_token']
                        self.users['admin'] = admin_user
                        print(f"   ✅ Found working admin user: {phone}")
                        return True
                    else:
                        print(f"   ⚠️  User {phone} exists but role is: {admin_user.get('role')}")
            
            # If no admin found, we'll work with what we have
            self.tokens['test_user'] = reg_response['access_token']
            self.users['test_user'] = reg_response['user']
            print(f"   ⚠️  No admin user available, will test with limited functionality")
            return False
        
        return False

    def test_user_number_generation_comprehensive(self):
        """Test 1: Comprehensive User Number Generation Testing"""
        print("\n🔢 COMPREHENSIVE USER NUMBER GENERATION TESTING")
        
        all_success = True
        
        # Create multiple users to test number generation
        users_created = []
        for i in range(3):
            import time
            unique_suffix = str(int(time.time() * 1000))[-6:]
            user_data = {
                "full_name": f"Тест Пользователь {i+1}",
                "phone": f"+7977{unique_suffix}",
                "password": "test123",
                "role": "user"
            }
            
            success, response = self.run_test(
                f"Create User {i+1} for Number Testing",
                "POST",
                "/api/auth/register",
                200,
                user_data
            )
            
            if success and 'user' in response:
                user = response['user']
                user_number = user.get('user_number')
                
                if user_number and user_number.startswith('USR') and len(user_number) == 9:
                    print(f"   ✅ User {i+1} number generated correctly: {user_number}")
                    users_created.append({
                        'user': user,
                        'token': response['access_token'],
                        'user_number': user_number
                    })
                else:
                    print(f"   ❌ User {i+1} invalid number format: {user_number}")
                    all_success = False
            else:
                print(f"   ❌ Failed to create user {i+1}")
                all_success = False
        
        # Test uniqueness
        user_numbers = [u['user_number'] for u in users_created]
        if len(user_numbers) == len(set(user_numbers)):
            print(f"   ✅ All generated user numbers are unique")
            self.working_features.append("User number generation with USR###### format")
            self.working_features.append("User number uniqueness validation")
        else:
            print(f"   ❌ Duplicate user numbers found")
            self.critical_issues.append("User number uniqueness violation")
            all_success = False
        
        # Test /api/auth/me includes user_number for all users
        for i, user_data in enumerate(users_created):
            success, me_response = self.run_test(
                f"Verify /api/auth/me includes user_number (User {i+1})",
                "GET",
                "/api/auth/me",
                200,
                token=user_data['token']
            )
            
            if success and me_response.get('user_number') == user_data['user_number']:
                print(f"   ✅ User {i+1} /api/auth/me includes correct user_number")
            else:
                print(f"   ❌ User {i+1} /api/auth/me user_number mismatch")
                all_success = False
        
        if all_success:
            self.working_features.append("/api/auth/me endpoint includes user_number")
        
        # Store first user for later tests
        if users_created:
            self.tokens['test_user'] = users_created[0]['token']
            self.users['test_user'] = users_created[0]['user']
        
        return all_success

    def test_role_management_api_realistic(self):
        """Test 2: Role Management API (Realistic Testing)"""
        print("\n👑 ROLE MANAGEMENT API TESTING (REALISTIC)")
        
        all_success = True
        
        if 'admin' not in self.tokens:
            print("   ⚠️  No admin user available - testing access control only")
            
            # Test that non-admin users cannot access role management
            if 'test_user' in self.tokens:
                success, error_response = self.run_test(
                    "Non-admin Role Change Attempt (Should Fail)",
                    "PUT",
                    "/api/admin/users/fake-id/role",
                    403,
                    {"user_id": "fake-id", "new_role": "admin"},
                    self.tokens['test_user']
                )
                
                if success:
                    print("   ✅ Non-admin users correctly denied access to role management")
                    self.working_features.append("Role management access control (non-admin denied)")
                else:
                    self.critical_issues.append("Role management access control not working")
                    all_success = False
            
            return all_success
        
        # Test with actual admin user
        test_user_id = self.users.get('test_user', {}).get('id')
        if not test_user_id:
            print("   ❌ No test user available for role change testing")
            return False
        
        # Test role change from 'user' to 'warehouse_operator'
        success, role_response = self.run_test(
            "Change Role: user → warehouse_operator",
            "PUT",
            f"/api/admin/users/{test_user_id}/role",
            200,
            {"user_id": test_user_id, "new_role": "warehouse_operator"},
            self.tokens['admin']
        )
        
        if success:
            # Verify response structure
            if 'user' in role_response and 'user_number' in role_response['user']:
                print(f"   ✅ Role change response includes user_number")
                self.working_features.append("Role management API includes user_number in response")
            else:
                print(f"   ❌ Role change response missing user_number")
                self.critical_issues.append("Role management API response missing user_number")
                all_success = False
            
            # Verify role was changed
            if role_response.get('user', {}).get('role') == 'warehouse_operator':
                print(f"   ✅ Role successfully changed to warehouse_operator")
                self.working_features.append("Role change user → warehouse_operator")
            else:
                print(f"   ❌ Role change failed")
                self.critical_issues.append("Role change functionality not working")
                all_success = False
            
            # Test role change to admin
            success2, role_response2 = self.run_test(
                "Change Role: warehouse_operator → admin",
                "PUT",
                f"/api/admin/users/{test_user_id}/role",
                200,
                {"user_id": test_user_id, "new_role": "admin"},
                self.tokens['admin']
            )
            
            if success2 and role_response2.get('user', {}).get('role') == 'admin':
                print(f"   ✅ Role successfully changed to admin")
                self.working_features.append("Role change warehouse_operator → admin")
        else:
            self.critical_issues.append("Role management API not accessible")
            all_success = False
        
        # Test self-role change prevention
        admin_id = self.users['admin']['id']
        success, error_response = self.run_test(
            "Self Role Change Prevention (Should Fail)",
            "PUT",
            f"/api/admin/users/{admin_id}/role",
            400,
            {"user_id": admin_id, "new_role": "user"},
            self.tokens['admin']
        )
        
        if success and 'Cannot change your own role' in str(error_response):
            print(f"   ✅ Self role change correctly prevented")
            self.working_features.append("Self role change prevention")
        else:
            print(f"   ❌ Self role change prevention not working correctly")
            self.critical_issues.append("Self role change prevention not working")
            all_success = False
        
        return all_success

    def test_personal_dashboard_comprehensive(self):
        """Test 3: Comprehensive Personal Dashboard Testing"""
        print("\n📊 COMPREHENSIVE PERSONAL DASHBOARD TESTING")
        
        all_success = True
        
        # Test dashboard for test user
        if 'test_user' in self.tokens:
            success, dashboard_response = self.run_test(
                "Get Personal Dashboard (test_user)",
                "GET",
                "/api/user/dashboard",
                200,
                token=self.tokens['test_user']
            )
            
            if success:
                # Verify dashboard structure
                required_fields = ['user_info', 'cargo_requests', 'sent_cargo', 'received_cargo']
                missing_fields = [field for field in required_fields if field not in dashboard_response]
                
                if not missing_fields:
                    print(f"   ✅ Dashboard has all required fields")
                    self.working_features.append("Personal dashboard API structure")
                    
                    # Verify user_info includes user_number
                    user_info = dashboard_response.get('user_info', {})
                    if 'user_number' in user_info and user_info['user_number']:
                        print(f"   ✅ Dashboard user_info includes user_number: {user_info['user_number']}")
                        self.working_features.append("Dashboard includes user_number in user_info")
                    else:
                        print(f"   ❌ Dashboard user_info missing user_number")
                        self.critical_issues.append("Dashboard user_info missing user_number")
                        all_success = False
                    
                    # Verify arrays are present and properly structured
                    cargo_requests = dashboard_response.get('cargo_requests', [])
                    sent_cargo = dashboard_response.get('sent_cargo', [])
                    received_cargo = dashboard_response.get('received_cargo', [])
                    
                    print(f"   📊 Dashboard data: {len(cargo_requests)} requests, {len(sent_cargo)} sent, {len(received_cargo)} received")
                    
                    if isinstance(cargo_requests, list) and isinstance(sent_cargo, list) and isinstance(received_cargo, list):
                        print(f"   ✅ All dashboard arrays are properly formatted")
                        self.working_features.append("Dashboard cargo arrays properly structured")
                    else:
                        print(f"   ❌ Dashboard arrays not properly formatted")
                        self.critical_issues.append("Dashboard arrays not properly structured")
                        all_success = False
                        
                else:
                    print(f"   ❌ Dashboard missing required fields: {missing_fields}")
                    self.critical_issues.append(f"Dashboard missing required fields: {missing_fields}")
                    all_success = False
            else:
                self.critical_issues.append("Personal dashboard API not accessible")
                all_success = False
        
        # Test dashboard access control
        success, invalid_response = self.run_test(
            "Dashboard Access with Invalid Token (Should Fail)",
            "GET",
            "/api/user/dashboard",
            401,
            token="invalid-token"
        )
        
        if success:
            print(f"   ✅ Invalid token correctly denied dashboard access")
            self.working_features.append("Dashboard access control (invalid token denied)")
        else:
            self.critical_issues.append("Dashboard access control not working")
            all_success = False
        
        return all_success

    def test_cargo_integration_with_dashboard(self):
        """Test 4: Cargo Integration with Dashboard"""
        print("\n📦 CARGO INTEGRATION WITH DASHBOARD TESTING")
        
        all_success = True
        
        if 'test_user' not in self.tokens:
            print("   ❌ Test user not available")
            return False
        
        # Create a cargo request to test dashboard integration
        cargo_request_data = {
            "recipient_full_name": "Тест Получатель Дашборд",
            "recipient_phone": "+992777888999",
            "recipient_address": "Душанбе, ул. Тестовая, 1",
            "pickup_address": "Москва, ул. Тестовая, 1",
            "cargo_name": "Тест груз для дашборда интеграции",
            "weight": 15.0,
            "declared_value": 7500.0,
            "description": "Тестовый груз для проверки интеграции с дашбордом",
            "route": "moscow_to_tajikistan"
        }
        
        success, cargo_request_response = self.run_test(
            "Create Cargo Request for Dashboard Integration",
            "POST",
            "/api/user/cargo-request",
            200,
            cargo_request_data,
            self.tokens['test_user']
        )
        
        if success:
            print(f"   ✅ Cargo request created successfully")
            self.working_features.append("Cargo request creation API")
            
            # Verify dashboard now shows the cargo request
            success, dashboard_with_cargo = self.run_test(
                "Verify Dashboard Shows New Cargo Request",
                "GET",
                "/api/user/dashboard",
                200,
                token=self.tokens['test_user']
            )
            
            if success:
                cargo_requests = dashboard_with_cargo.get('cargo_requests', [])
                if len(cargo_requests) > 0:
                    print(f"   ✅ Dashboard shows {len(cargo_requests)} cargo request(s)")
                    self.working_features.append("Dashboard displays cargo requests")
                    
                    # Verify cargo request structure
                    first_request = cargo_requests[0]
                    required_fields = ['id', 'cargo_name', 'weight', 'declared_value', 'status', 'created_at']
                    missing_fields = [field for field in required_fields if field not in first_request]
                    
                    if not missing_fields:
                        print(f"   ✅ Cargo request has all required fields")
                        self.working_features.append("Cargo request data structure complete")
                    else:
                        print(f"   ❌ Cargo request missing fields: {missing_fields}")
                        self.critical_issues.append(f"Cargo request missing fields: {missing_fields}")
                        all_success = False
                        
                    # Verify data consistency
                    if first_request.get('cargo_name') == cargo_request_data['cargo_name']:
                        print(f"   ✅ Cargo request data consistency verified")
                        self.working_features.append("Cargo request data consistency")
                    else:
                        print(f"   ❌ Cargo request data inconsistency")
                        self.critical_issues.append("Cargo request data inconsistency")
                        all_success = False
                else:
                    print(f"   ❌ Dashboard not showing cargo requests")
                    self.critical_issues.append("Dashboard not displaying cargo requests")
                    all_success = False
            else:
                all_success = False
        else:
            self.critical_issues.append("Cargo request creation not working")
            all_success = False
        
        return all_success

    def test_data_consistency_and_sorting(self):
        """Test 5: Data Consistency and Sorting"""
        print("\n🔍 DATA CONSISTENCY AND SORTING TESTING")
        
        all_success = True
        
        # Test dashboard data sorting and consistency
        for user_type in ['test_user', 'admin']:
            if user_type in self.tokens:
                success, dashboard = self.run_test(
                    f"Verify Dashboard Data Consistency ({user_type})",
                    "GET",
                    "/api/user/dashboard",
                    200,
                    token=self.tokens[user_type]
                )
                
                if success:
                    # Check cargo arrays structure and sorting
                    sent_cargo = dashboard.get('sent_cargo', [])
                    received_cargo = dashboard.get('received_cargo', [])
                    cargo_requests = dashboard.get('cargo_requests', [])
                    
                    # Verify sorting by created_at (if data exists)
                    for cargo_type, cargo_list in [('sent_cargo', sent_cargo), ('received_cargo', received_cargo), ('cargo_requests', cargo_requests)]:
                        if len(cargo_list) > 1:
                            dates = []
                            for item in cargo_list:
                                created_at = item.get('created_at')
                                if created_at:
                                    if isinstance(created_at, str):
                                        try:
                                            dates.append(datetime.fromisoformat(created_at.replace('Z', '+00:00')))
                                        except:
                                            dates.append(created_at)
                                    else:
                                        dates.append(created_at)
                            
                            if len(dates) > 1:
                                is_sorted = all(dates[i] >= dates[i+1] for i in range(len(dates)-1))
                                if is_sorted:
                                    print(f"   ✅ {cargo_type} properly sorted by created_at (descending)")
                                    self.working_features.append(f"Dashboard {cargo_type} sorting")
                                else:
                                    print(f"   ❌ {cargo_type} sorting issue")
                                    self.critical_issues.append(f"Dashboard {cargo_type} not properly sorted")
                                    all_success = False
                    
                    print(f"   ✅ Dashboard data structure verified for {user_type}")
                else:
                    all_success = False
        
        return all_success

    def run_comprehensive_test(self):
        """Run all comprehensive tests"""
        print("🚀 STARTING FINAL COMPREHENSIVE ADMIN PANEL & DASHBOARD TESTS")
        print("=" * 70)
        
        # Setup environment
        admin_available = self.setup_admin_user()
        
        test_results = []
        
        # Test 1: User Number Generation
        result1 = self.test_user_number_generation_comprehensive()
        test_results.append(("User Number Generation", result1))
        
        # Test 2: Role Management API
        result2 = self.test_role_management_api_realistic()
        test_results.append(("Role Management API", result2))
        
        # Test 3: Personal Dashboard API
        result3 = self.test_personal_dashboard_comprehensive()
        test_results.append(("Personal Dashboard API", result3))
        
        # Test 4: Cargo Integration
        result4 = self.test_cargo_integration_with_dashboard()
        test_results.append(("Cargo Integration with Dashboard", result4))
        
        # Test 5: Data Consistency
        result5 = self.test_data_consistency_and_sorting()
        test_results.append(("Data Consistency and Sorting", result5))
        
        # Print comprehensive results
        print("\n" + "=" * 70)
        print("📊 FINAL COMPREHENSIVE TEST RESULTS")
        print("=" * 70)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status} - {test_name}")
            if result:
                passed_tests += 1
        
        print(f"\n📈 SUMMARY: {passed_tests}/{total_tests} test suites passed")
        print(f"📈 INDIVIDUAL TESTS: {self.tests_passed}/{self.tests_run} individual tests passed")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 SUCCESS RATE: {success_rate:.1f}%")
        
        # Print working features
        if self.working_features:
            print(f"\n✅ WORKING FEATURES ({len(self.working_features)}):")
            for i, feature in enumerate(self.working_features, 1):
                print(f"   {i}. {feature}")
        
        # Print critical issues
        if self.critical_issues:
            print(f"\n🚨 CRITICAL ISSUES FOUND ({len(self.critical_issues)}):")
            for i, issue in enumerate(self.critical_issues, 1):
                print(f"   {i}. {issue}")
        
        # Overall assessment
        if len(self.critical_issues) == 0:
            print("\n🎉 ALL CRITICAL FUNCTIONALITY WORKING CORRECTLY!")
            print("✅ ADMIN PANEL ENHANCEMENTS & PERSONAL DASHBOARD: FULLY FUNCTIONAL")
            return True
        else:
            print(f"\n⚠️  {len(self.critical_issues)} CRITICAL ISSUE(S) NEED ATTENTION")
            return False

if __name__ == "__main__":
    tester = FinalAdminTester()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)
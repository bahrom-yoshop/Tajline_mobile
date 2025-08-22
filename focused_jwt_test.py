#!/usr/bin/env python3
"""
Focused JWT Token Versioning System Testing
Tests the specific JWT token versioning functionality as requested in the review
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class FocusedJWTTester:
    def __init__(self, base_url="https://tajline-cargo-7.preview.emergentagent.com"):
        self.base_url = base_url
        self.admin_token = None
        self.user_token = None
        self.admin_info = None
        self.user_info = None
        self.tests_run = 0
        self.tests_passed = 0
        
        print(f"🔐 Focused JWT Token Versioning System Tester")
        print(f"📡 Base URL: {self.base_url}")
        print("=" * 60)

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data: Optional[Dict] = None, token: Optional[str] = None) -> tuple[bool, Dict]:
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
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)

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

    def setup_users(self):
        """Setup admin and regular user"""
        print("\n👥 SETTING UP USERS")
        
        # Login as admin
        success, admin_response = self.run_test(
            "Admin Login",
            "POST",
            "/api/auth/login",
            200,
            {"phone": "+79999888777", "password": "admin123"}
        )
        
        if success and 'access_token' in admin_response:
            self.admin_token = admin_response['access_token']
            self.admin_info = admin_response['user']
            print(f"   🔑 Admin token obtained")
        else:
            return False
        
        # Create/login regular user
        success, user_response = self.run_test(
            "User Login",
            "POST",
            "/api/auth/login",
            200,
            {"phone": "+992900000000", "password": "123456"}
        )
        
        if not success:
            # Try registration
            success, user_response = self.run_test(
                "User Registration",
                "POST",
                "/api/auth/register",
                200,
                {
                    "full_name": "Тест Пользователь JWT",
                    "phone": "+992900000000",
                    "password": "123456",
                    "role": "user"
                }
            )
        
        if success and 'access_token' in user_response:
            self.user_token = user_response['access_token']
            self.user_info = user_response['user']
            print(f"   🔑 User token obtained")
            return True
        
        return False

    def test_user_profile_update_token_versioning(self):
        """Test that user profile updates increment token version and invalidate old tokens"""
        print("\n👤 USER PROFILE UPDATE TOKEN VERSIONING TEST")
        
        # Get current user info and token version
        success, current_user = self.run_test(
            "Get Current User Info",
            "GET",
            "/api/auth/me",
            200,
            token=self.user_token
        )
        
        if not success:
            return False
        
        original_token_version = current_user.get('token_version', 1)
        print(f"   📊 Original token version: {original_token_version}")
        
        # Store the old token
        old_token = self.user_token
        
        # Update user profile
        success, updated_profile = self.run_test(
            "Update User Profile",
            "PUT",
            "/api/user/profile",
            200,
            {
                "full_name": "Пользователь JWT Обновленный",
                "email": "jwt.updated@test.com",
                "address": "Душанбе, ул. JWT, 123"
            },
            self.user_token
        )
        
        if not success:
            return False
        
        new_token_version = updated_profile.get('token_version', 1)
        print(f"   📊 New token version: {new_token_version}")
        
        if new_token_version <= original_token_version:
            print("   ❌ Token version not incremented")
            return False
        
        print("   ✅ Token version incremented after profile update")
        
        # Test that old token becomes invalid
        success, _ = self.run_test(
            "Use Old Token (Should Fail)",
            "GET",
            "/api/auth/me",
            401,
            token=old_token
        )
        
        if not success:
            print("   ❌ Old token should be invalid but still works")
            return False
        
        print("   ✅ Old token correctly invalidated")
        
        # Login again to get new token
        success, login_response = self.run_test(
            "Login After Profile Update",
            "POST",
            "/api/auth/login",
            200,
            {"phone": "+992900000000", "password": "123456"}
        )
        
        if not success:
            return False
        
        self.user_token = login_response['access_token']
        
        # Verify new token works
        success, new_user_info = self.run_test(
            "Verify New Token Works",
            "GET",
            "/api/auth/me",
            200,
            token=self.user_token
        )
        
        if not success:
            return False
        
        print("   ✅ New token works correctly")
        print(f"   📊 Current token version: {new_user_info.get('token_version')}")
        
        return True

    def test_admin_user_update_token_versioning(self):
        """Test that admin updates to user profile increment token version and invalidate user tokens"""
        print("\n👑 ADMIN USER UPDATE TOKEN VERSIONING TEST")
        
        # Get user info
        success, user_info = self.run_test(
            "Get User Info Before Admin Update",
            "GET",
            "/api/auth/me",
            200,
            token=self.user_token
        )
        
        if not success:
            return False
        
        user_id = user_info.get('id')
        original_token_version = user_info.get('token_version', 1)
        print(f"   🆔 User ID: {user_id}")
        print(f"   📊 Token version before admin update: {original_token_version}")
        
        # Store current user token
        user_token_before_admin_update = self.user_token
        
        # Admin updates user profile (critical change - phone)
        success, admin_update_response = self.run_test(
            "Admin Updates User Profile (Phone Change)",
            "PUT",
            f"/api/admin/users/{user_id}/update",
            200,
            {
                "phone": "+992900000001",  # Critical change
                "full_name": "Пользователь Обновлен Админом JWT"
            },
            self.admin_token
        )
        
        if not success:
            return False
        
        # Extract user data from nested response
        if 'user' in admin_update_response:
            updated_user_data = admin_update_response['user']
        else:
            updated_user_data = admin_update_response
        
        new_token_version = updated_user_data.get('token_version', 1)
        print(f"   📊 Token version after admin update: {new_token_version}")
        
        if new_token_version <= original_token_version:
            print("   ❌ Token version not incremented by admin update")
            return False
        
        print("   ✅ Token version incremented after admin update")
        
        # Test that user's old token becomes invalid
        success, _ = self.run_test(
            "Use User Token After Admin Update (Should Fail)",
            "GET",
            "/api/auth/me",
            401,
            token=user_token_before_admin_update
        )
        
        if not success:
            print("   ❌ User token should be invalid after admin update but still works")
            return False
        
        print("   ✅ User token correctly invalidated after admin update")
        
        # User needs to login again with new phone
        success, user_relogin = self.run_test(
            "User Re-login After Admin Update (New Phone)",
            "POST",
            "/api/auth/login",
            200,
            {"phone": "+992900000001", "password": "123456"}  # New phone
        )
        
        if not success:
            return False
        
        self.user_token = user_relogin['access_token']
        
        # Verify new token works and has updated info
        success, updated_user_info = self.run_test(
            "Verify User New Token and Updated Info",
            "GET",
            "/api/auth/me",
            200,
            token=self.user_token
        )
        
        if not success:
            return False
        
        print("   ✅ User new token works correctly")
        print(f"   👤 Updated name: {updated_user_info.get('full_name')}")
        print(f"   📞 Updated phone: {updated_user_info.get('phone')}")
        print(f"   📊 Current token version: {updated_user_info.get('token_version')}")
        
        return True

    def test_admin_user_management_api(self):
        """Test the enhanced admin user management API"""
        print("\n🔧 ADMIN USER MANAGEMENT API TEST")
        
        # Get user ID
        success, user_info = self.run_test(
            "Get User Info for Admin Management Test",
            "GET",
            "/api/auth/me",
            200,
            token=self.user_token
        )
        
        if not success:
            return False
        
        user_id = user_info.get('id')
        
        # Test full user profile editing by admin
        success, edit_response = self.run_test(
            "Admin Full Profile Edit",
            "PUT",
            f"/api/admin/users/{user_id}/update",
            200,
            {
                "full_name": "Полностью Обновленный Пользователь API",
                "email": "api.updated@admin.com",
                "address": "Душанбе, ул. API, 456",
                "role": "user",
                "is_active": True
            },
            self.admin_token
        )
        
        if not success:
            return False
        
        # Extract user data from response
        if 'user' in edit_response:
            user_data = edit_response['user']
            print("   ✅ Admin edit response contains user data")
            print(f"   👤 Updated name: {user_data.get('full_name')}")
            print(f"   📧 Updated email: {user_data.get('email')}")
            print(f"   🔢 Token version: {user_data.get('token_version')}")
        else:
            print("   ❌ Admin edit response missing user data")
            return False
        
        # Test phone uniqueness validation
        success, _ = self.run_test(
            "Admin Update with Duplicate Phone (Should Fail)",
            "PUT",
            f"/api/admin/users/{user_id}/update",
            400,
            {"phone": "+79999888777"},  # Admin's phone
            self.admin_token
        )
        
        if not success:
            print("   ❌ Phone uniqueness validation not working")
            return False
        
        print("   ✅ Phone uniqueness validation working correctly")
        
        # Test email uniqueness validation
        success, _ = self.run_test(
            "Admin Update with Duplicate Email (Should Fail)",
            "PUT",
            f"/api/admin/users/{user_id}/update",
            400,
            {"email": "admin@test.com"},  # Assuming admin has this email
            self.admin_token
        )
        
        if not success:
            print("   ❌ Email uniqueness validation not working")
            return False
        
        print("   ✅ Email uniqueness validation working correctly")
        
        return True

    def test_multi_cargo_creation(self):
        """Test multi-cargo creation with individual pricing"""
        print("\n📦 MULTI-CARGO CREATION TEST")
        
        # Test multi-cargo with individual pricing
        success, multi_response = self.run_test(
            "Create Multi-Cargo with Individual Pricing",
            "POST",
            "/api/operator/cargo/accept",
            200,
            {
                "sender_full_name": "Тест Отправитель JWT",
                "sender_phone": "+79999999999",
                "recipient_full_name": "Тест Получатель JWT",
                "recipient_phone": "+992999999999",
                "recipient_address": "Душанбе, ул. JWT, 123",
                "cargo_items": [
                    {"cargo_name": "Документы", "weight": 5.0, "price_per_kg": 80.0},
                    {"cargo_name": "Одежда", "weight": 15.0, "price_per_kg": 70.0},
                    {"cargo_name": "Электроника", "weight": 8.0, "price_per_kg": 120.0}
                ],
                "description": "JWT тест мульти-груз",
                "route": "moscow_to_tajikistan"
            },
            self.admin_token
        )
        
        if not success:
            return False
        
        cargo_number = multi_response.get('cargo_number', 'N/A')
        total_weight = multi_response.get('weight', 0)
        total_cost = multi_response.get('declared_value', 0)
        cargo_name = multi_response.get('cargo_name', 'N/A')
        
        print(f"   ✅ Multi-cargo created: {cargo_number}")
        print(f"   📊 Total weight: {total_weight} kg")
        print(f"   💰 Total cost: {total_cost} руб")
        print(f"   🏷️  Combined name: {cargo_name}")
        
        # Expected calculations:
        # Документы: 5.0 × 80.0 = 400 руб
        # Одежда: 15.0 × 70.0 = 1050 руб
        # Электроника: 8.0 × 120.0 = 960 руб
        # Total: 28.0 kg, 2410 руб
        expected_weight = 28.0
        expected_cost = 2410.0
        
        if abs(total_weight - expected_weight) < 0.01 and abs(total_cost - expected_cost) < 0.01:
            print("   ✅ Multi-cargo calculations verified correctly")
            return True
        else:
            print(f"   ❌ Calculation error - Expected: {expected_weight}kg/{expected_cost}руб")
            return False

    def run_all_tests(self):
        """Run all focused JWT tests"""
        print("\n🚀 STARTING FOCUSED JWT TOKEN VERSIONING TESTS")
        print("=" * 60)
        
        # Setup
        if not self.setup_users():
            print("\n❌ FAILED TO SETUP USERS - ABORTING")
            return False
        
        # Run tests
        test_results = []
        
        test_results.append(("User Profile Update Token Versioning", self.test_user_profile_update_token_versioning()))
        test_results.append(("Admin User Update Token Versioning", self.test_admin_user_update_token_versioning()))
        test_results.append(("Admin User Management API", self.test_admin_user_management_api()))
        test_results.append(("Multi-Cargo Creation", self.test_multi_cargo_creation()))
        
        # Print results
        print("\n" + "=" * 60)
        print("🏁 FOCUSED JWT TEST RESULTS")
        print("=" * 60)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status} - {test_name}")
            if result:
                passed_tests += 1
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Individual Test Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        print(f"   Test Suites Passed: {passed_tests}/{total_tests}")
        print(f"   Test Suite Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL FOCUSED JWT TESTS PASSED!")
            return True
        else:
            print(f"\n⚠️  {total_tests - passed_tests} test suite(s) failed.")
            return False

if __name__ == "__main__":
    tester = FocusedJWTTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
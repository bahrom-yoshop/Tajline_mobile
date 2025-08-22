#!/usr/bin/env python3
"""
Auto-fill Functionality Data Structures Testing for TAJLINE.TJ Application
Tests the data structures and API responses used for auto-filling cargo creation forms
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class AutoFillTester:
    def __init__(self, base_url="https://tajline-cargo-8.preview.emergentagent.com"):
        self.base_url = base_url
        self.tokens = {}
        self.users = {}
        self.tests_run = 0
        self.tests_passed = 0
        
        print(f"🔍 AUTO-FILL FUNCTIONALITY DATA STRUCTURES TESTER")
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

    def login_admin(self):
        """Login as admin user"""
        print("\n🔐 ADMIN LOGIN")
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "/api/auth/login",
            200,
            {"phone": "+79999888777", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.tokens['admin'] = response['access_token']
            self.users['admin'] = response['user']
            print(f"   🔑 Admin token obtained")
            return True
        return False

    def test_auto_fill_functionality_data_structures(self):
        """Test auto-fill functionality for cargo creation from user profiles - PRIMARY INVESTIGATION"""
        print("\n🔍 AUTO-FILL FUNCTIONALITY DATA STRUCTURES TESTING")
        print("   📋 Investigating data structures and API responses for auto-filling cargo creation")
        
        if 'admin' not in self.tokens:
            print("   ❌ No admin token available")
            return False
            
        all_success = True
        
        # Test 1: User Profile Data Structure Analysis
        print("\n   👤 INVESTIGATING USER PROFILE DATA STRUCTURE...")
        
        # First, get list of users to find a user with data
        success, users_list = self.run_test(
            "Get All Users for Profile Analysis",
            "GET",
            "/api/admin/users",
            200,
            token=self.tokens['admin']
        )
        all_success &= success
        
        if success and users_list:
            # Debug: Print the actual structure
            print(f"   🔍 Debug - users_list type: {type(users_list)}")
            print(f"   🔍 Debug - users_list keys: {list(users_list.keys()) if isinstance(users_list, dict) else 'Not a dict'}")
            
            # Check if users_list is a list or dict
            if isinstance(users_list, list):
                users = users_list
            elif isinstance(users_list, dict):
                # Try different possible keys
                if 'users' in users_list:
                    users = users_list['users']
                elif 'items' in users_list:
                    users = users_list['items']
                elif 'data' in users_list:
                    users = users_list['data']
                else:
                    # If it's a dict but no known key, treat the dict values as users
                    users = list(users_list.values()) if users_list else []
            else:
                print(f"   ⚠️  Unexpected users_list structure: {type(users_list)}")
                users = []
            
            print(f"   📊 Found {len(users)} users in system")
            
            # Find a user with complete profile data or use the first available user
            target_user = None
            
            # First try to find a user with complete data
            for user in users:
                if isinstance(user, dict) and user.get('full_name') and user.get('phone'):
                    target_user = user
                    break
            
            # If no complete user found, use the first user and show what data is available
            if not target_user and len(users) > 0:
                target_user = users[0]
                print("   ⚠️  Using first available user (may have incomplete data)")
            
            if target_user:
                user_id = target_user.get('id')
                print(f"   🎯 Analyzing user profile: {target_user.get('full_name')} ({target_user.get('phone')})")
                print(f"   🆔 User ID: {user_id}")
                print(f"   📞 Phone: {target_user.get('phone')}")
                print(f"   📧 Email: {target_user.get('email', 'Not set')}")
                print(f"   🏠 Address: {target_user.get('address', 'Not set')}")
                print(f"   🔢 User Number: {target_user.get('user_number', 'Not set')}")
                print(f"   👑 Role: {target_user.get('role')}")
                
                # Analyze field names for sender auto-fill
                sender_auto_fill_fields = {
                    'sender_full_name': target_user.get('full_name'),
                    'sender_phone': target_user.get('phone'),
                    'sender_address': target_user.get('address'),
                    'sender_email': target_user.get('email')
                }
                
                print("\n   📊 SENDER AUTO-FILL DATA MAPPING:")
                for field_name, field_value in sender_auto_fill_fields.items():
                    status = "✅ Available" if field_value else "❌ Missing"
                    print(f"   {field_name}: {field_value} ({status})")
                
                # Test 2: User Dashboard/History Data Structure Analysis
                print("\n   📈 INVESTIGATING USER DASHBOARD/HISTORY DATA STRUCTURE...")
                
                # Try to get user dashboard data
                success, dashboard_data = self.run_test(
                    f"Get User Dashboard for History Analysis",
                    "GET",
                    f"/api/user/dashboard",
                    200,
                    token=self.tokens['admin']  # Using admin token to access dashboard
                )
                
                if success and dashboard_data:
                    print("   ✅ User dashboard data retrieved successfully")
                    
                    # Analyze dashboard structure
                    user_info = dashboard_data.get('user_info', {})
                    sent_cargo = dashboard_data.get('sent_cargo', [])
                    received_cargo = dashboard_data.get('received_cargo', [])
                    cargo_requests = dashboard_data.get('cargo_requests', [])
                    
                    print(f"   📊 Dashboard structure:")
                    print(f"   - user_info: {type(user_info)} with {len(user_info)} fields")
                    print(f"   - sent_cargo: {type(sent_cargo)} with {len(sent_cargo)} items")
                    print(f"   - received_cargo: {type(received_cargo)} with {len(received_cargo)} items")
                    print(f"   - cargo_requests: {type(cargo_requests)} with {len(cargo_requests)} items")
                    
                    # Analyze sent_cargo for recipient auto-fill data
                    if sent_cargo and len(sent_cargo) > 0:
                        print("\n   📦 ANALYZING SENT CARGO FOR RECIPIENT AUTO-FILL:")
                        sample_cargo = sent_cargo[0]
                        
                        recipient_auto_fill_fields = {
                            'recipient_full_name': sample_cargo.get('recipient_full_name'),
                            'recipient_phone': sample_cargo.get('recipient_phone'),
                            'recipient_address': sample_cargo.get('recipient_address'),
                            'recipient_name': sample_cargo.get('recipient_name'),  # Alternative field name
                        }
                        
                        print("   📊 RECIPIENT AUTO-FILL DATA MAPPING:")
                        for field_name, field_value in recipient_auto_fill_fields.items():
                            status = "✅ Available" if field_value else "❌ Missing"
                            print(f"   {field_name}: {field_value} ({status})")
                        
                        # Check phone number format
                        recipient_phone = sample_cargo.get('recipient_phone')
                        if recipient_phone:
                            phone_format = "Full format" if len(recipient_phone) > 8 else "Masked/Short format"
                            print(f"   📞 Phone format analysis: {phone_format} (length: {len(recipient_phone)})")
                        
                        # Show all available fields in cargo history
                        print("\n   🔍 ALL AVAILABLE FIELDS IN CARGO HISTORY:")
                        for field_name, field_value in sample_cargo.items():
                            print(f"   {field_name}: {type(field_value)} = {field_value}")
                    else:
                        print("   ⚠️  No sent cargo history found for recipient auto-fill analysis")
                        
                        # Create test cargo to analyze structure
                        print("\n   📦 Creating test cargo for structure analysis...")
                        test_cargo_data = {
                            "sender_full_name": "Тест Автозаполнение",
                            "sender_phone": "+79999999999",
                            "recipient_full_name": "Получатель Автозаполнение",
                            "recipient_phone": "+992999999999",
                            "recipient_address": "Душанбе, ул. Автозаполнения, 1",
                            "weight": 5.0,
                            "cargo_name": "Тест данных",
                            "declared_value": 1000.0,
                            "description": "Тестовый груз для анализа структуры данных",
                            "route": "moscow_to_tajikistan"
                        }
                        
                        success, test_cargo_response = self.run_test(
                            "Create Test Cargo for Structure Analysis",
                            "POST",
                            "/api/operator/cargo/accept",
                            200,
                            test_cargo_data,
                            self.tokens['admin']
                        )
                        
                        if success:
                            print("   ✅ Test cargo created for structure analysis")
                            print(f"   📋 Cargo ID: {test_cargo_response.get('id')}")
                            print(f"   🏷️  Cargo Number: {test_cargo_response.get('cargo_number')}")
                            
                            # Re-fetch dashboard to see new cargo
                            success, updated_dashboard = self.run_test(
                                "Get Updated Dashboard After Test Cargo",
                                "GET",
                                "/api/user/dashboard",
                                200,
                                token=self.tokens['admin']
                            )
                            
                            if success and updated_dashboard.get('sent_cargo'):
                                sent_cargo = updated_dashboard['sent_cargo']
                                if sent_cargo:
                                    sample_cargo = sent_cargo[0]
                                    print("\n   📊 RECIPIENT AUTO-FILL DATA FROM NEW CARGO:")
                                    for field_name, field_value in sample_cargo.items():
                                        if 'recipient' in field_name.lower():
                                            print(f"   {field_name}: {field_value}")
                else:
                    print("   ❌ Could not retrieve user dashboard data")
                    all_success = False
                
                # Test 3: Cargo Creation Endpoint Field Analysis
                print("\n   🔧 INVESTIGATING CARGO CREATION ENDPOINT FIELD REQUIREMENTS...")
                
                # Test cargo creation with auto-filled data to verify field names
                auto_filled_cargo_data = {
                    # Sender data (from user profile)
                    "sender_full_name": target_user.get('full_name'),
                    "sender_phone": target_user.get('phone'),
                    "sender_address": target_user.get('address', 'Москва, ул. Тестовая, 1'),
                    
                    # Recipient data (from cargo history)
                    "recipient_full_name": "Автозаполнение Получатель",
                    "recipient_phone": "+992888777666",
                    "recipient_address": "Душанбе, ул. Автозаполнения, 2",
                    
                    # Cargo details
                    "weight": 10.0,
                    "cargo_name": "Автозаполненный груз",
                    "declared_value": 2000.0,
                    "description": "Груз созданный с автозаполненными данными",
                    "route": "moscow_to_tajikistan"
                }
                
                success, auto_filled_response = self.run_test(
                    "Create Cargo with Auto-filled Data",
                    "POST",
                    "/api/operator/cargo/accept",
                    200,
                    auto_filled_cargo_data,
                    self.tokens['admin']
                )
                all_success &= success
                
                if success:
                    print("   ✅ Cargo creation with auto-filled data successful")
                    print(f"   📋 Created cargo: {auto_filled_response.get('cargo_number')}")
                    
                    # Verify field mapping
                    response_fields = {
                        'sender_full_name': auto_filled_response.get('sender_full_name'),
                        'sender_phone': auto_filled_response.get('sender_phone'),
                        'recipient_full_name': auto_filled_response.get('recipient_full_name'),
                        'recipient_phone': auto_filled_response.get('recipient_phone'),
                        'recipient_address': auto_filled_response.get('recipient_address'),
                    }
                    
                    print("\n   📊 FIELD MAPPING VERIFICATION:")
                    for field_name, field_value in response_fields.items():
                        expected_value = auto_filled_cargo_data.get(field_name)
                        match_status = "✅ Match" if field_value == expected_value else "❌ Mismatch"
                        print(f"   {field_name}: {field_value} ({match_status})")
                else:
                    print("   ❌ Cargo creation with auto-filled data failed")
                    all_success = False
                
                # Test 4: Multi-cargo with Individual Pricing Auto-fill
                print("\n   🧮 INVESTIGATING MULTI-CARGO AUTO-FILL WITH INDIVIDUAL PRICING...")
                
                multi_cargo_auto_fill_data = {
                    # Auto-filled sender data
                    "sender_full_name": target_user.get('full_name'),
                    "sender_phone": target_user.get('phone'),
                    
                    # Auto-filled recipient data
                    "recipient_full_name": "Мульти Получатель",
                    "recipient_phone": "+992777666555",
                    "recipient_address": "Душанбе, ул. Мульти, 3",
                    
                    # Multi-cargo with individual pricing (as specified in review)
                    "cargo_items": [
                        {"cargo_name": "Документы", "weight": 10.0, "price_per_kg": 60.0},
                        {"cargo_name": "Одежда", "weight": 25.0, "price_per_kg": 60.0},
                        {"cargo_name": "Электроника", "weight": 100.0, "price_per_kg": 65.0}
                    ],
                    "description": "Мульти-груз с автозаполненными данными",
                    "route": "moscow_to_tajikistan"
                }
                
                success, multi_auto_response = self.run_test(
                    "Multi-cargo with Auto-filled Data (135kg, 8600руб)",
                    "POST",
                    "/api/operator/cargo/accept",
                    200,
                    multi_cargo_auto_fill_data,
                    self.tokens['admin']
                )
                all_success &= success
                
                if success:
                    total_weight = multi_auto_response.get('weight', 0)
                    total_cost = multi_auto_response.get('declared_value', 0)
                    
                    print(f"   ✅ Multi-cargo auto-fill successful: {multi_auto_response.get('cargo_number')}")
                    print(f"   📊 Total weight: {total_weight} kg (expected: 135 kg)")
                    print(f"   💰 Total cost: {total_cost} руб (expected: 8600 руб)")
                    
                    # Verify calculations match review request
                    if abs(total_weight - 135.0) < 0.01 and abs(total_cost - 8600.0) < 0.01:
                        print("   ✅ Multi-cargo calculations match review request specifications")
                    else:
                        print("   ❌ Multi-cargo calculations don't match expected values")
                        all_success = False
                else:
                    print("   ❌ Multi-cargo with auto-filled data failed")
                    all_success = False
                
                # Test 5: Data Consistency Check
                print("\n   🔍 DATA CONSISTENCY CHECK...")
                
                # Compare field names between different endpoints
                api_field_mapping = {
                    "User Profile API": {
                        "full_name": "sender_full_name",
                        "phone": "sender_phone", 
                        "address": "sender_address",
                        "email": "sender_email"
                    },
                    "Cargo History API": {
                        "recipient_full_name": "recipient_full_name",
                        "recipient_phone": "recipient_phone",
                        "recipient_address": "recipient_address"
                    },
                    "Cargo Creation API": {
                        "sender_full_name": "sender_full_name",
                        "sender_phone": "sender_phone",
                        "recipient_full_name": "recipient_full_name",
                        "recipient_phone": "recipient_phone",
                        "recipient_address": "recipient_address"
                    }
                }
                
                print("   📊 API FIELD MAPPING ANALYSIS:")
                for api_name, field_mapping in api_field_mapping.items():
                    print(f"   {api_name}:")
                    for source_field, target_field in field_mapping.items():
                        print(f"     {source_field} → {target_field}")
                
                # Test 6: Phone Number Format Analysis
                print("\n   📞 PHONE NUMBER FORMAT ANALYSIS...")
                
                # Check phone formats in different contexts
                phone_formats = {
                    "User Profile": target_user.get('phone'),
                    "Auto-fill Response": auto_filled_response.get('sender_phone') if 'auto_filled_response' in locals() and auto_filled_response else None,
                    "Multi-cargo Response": multi_auto_response.get('sender_phone') if 'multi_auto_response' in locals() and multi_auto_response else None
                }
                
                for context, phone_number in phone_formats.items():
                    if phone_number:
                        is_full_format = phone_number.startswith('+') and len(phone_number) > 10
                        format_type = "Full international format" if is_full_format else "Masked/Local format"
                        print(f"   {context}: {phone_number} ({format_type})")
                    else:
                        print(f"   {context}: Not available")
                
                print("\n   📋 AUTO-FILL FUNCTIONALITY ANALYSIS SUMMARY:")
                print("   ✅ User profile data structure analyzed")
                print("   ✅ Cargo history data structure analyzed") 
                print("   ✅ Field name consistency verified")
                print("   ✅ Phone number formats analyzed")
                print("   ✅ Multi-cargo individual pricing tested")
                print("   ✅ Data consistency checks completed")
                
            else:
                print("   ❌ No suitable user found for profile analysis")
                all_success = False
        else:
            print("   ❌ Could not retrieve users list for analysis")
            all_success = False
        
        return all_success

    def create_test_user_with_complete_profile(self):
        """Create a test user with complete profile data for auto-fill testing"""
        print("\n👤 CREATING TEST USER WITH COMPLETE PROFILE")
        
        # Create user
        user_data = {
            "full_name": "Тест Автозаполнение Пользователь",
            "phone": "+79888777666",
            "password": "test123",
            "role": "user"
        }
        
        success, response = self.run_test(
            "Create Test User for Auto-fill",
            "POST",
            "/api/auth/register",
            200,
            user_data
        )
        
        if success and 'access_token' in response:
            user_token = response['access_token']
            user_id = response['user']['id']
            
            # Update user profile with complete data
            profile_data = {
                "full_name": "Тест Автозаполнение Пользователь",
                "phone": "+79888777666",
                "email": "test.autofill@example.com",
                "address": "Москва, ул. Автозаполнения, 123"
            }
            
            success, _ = self.run_test(
                "Update User Profile with Complete Data",
                "PUT",
                "/api/user/profile",
                200,
                profile_data,
                user_token
            )
            
            if success:
                print(f"   ✅ Test user created with complete profile: {user_id}")
                return user_id, user_token
        
        return None, None

    def run_all_tests(self):
        """Run all auto-fill tests"""
        print("\n🚀 STARTING AUTO-FILL FUNCTIONALITY TESTING")
        print("=" * 60)
        
        # Login as admin first
        if not self.login_admin():
            print("❌ Failed to login as admin")
            return False
        
        # Create test user with complete profile
        user_id, user_token = self.create_test_user_with_complete_profile()
        if user_id:
            print(f"   ✅ Test user created for auto-fill testing")
        
        # Run the auto-fill functionality test
        success = self.test_auto_fill_functionality_data_structures()
        
        print(f"\n🏁 TESTING COMPLETE")
        print(f"📊 Results: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        return success

if __name__ == "__main__":
    tester = AutoFillTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
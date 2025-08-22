#!/usr/bin/env python3
"""
Comprehensive Testing for Courier Cancelled Requests Endpoint in TAJLINE.TJ
Tests the new endpoint /api/courier/requests/cancelled for cancelled requests
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class CourierCancelledRequestsTester:
    def __init__(self, base_url="https://tajline-cargo-7.preview.emergentagent.com"):
        self.base_url = base_url
        self.tokens = {}
        self.users = {}
        self.tests_run = 0
        self.tests_passed = 0
        
        print(f"🚛 TAJLINE.TJ Courier Cancelled Requests Endpoint Tester")
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

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"   ✅ PASSED - Status: {response.status_code}")
                try:
                    result = response.json()
                    if isinstance(result, dict) and len(str(result)) < 500:
                        print(f"   📄 Response: {result}")
                    elif isinstance(result, dict):
                        # Show summary for large responses
                        summary = {}
                        for key, value in result.items():
                            if isinstance(value, list):
                                summary[key] = f"[{len(value)} items]"
                            elif isinstance(value, dict):
                                summary[key] = f"{{dict with {len(value)} keys}}"
                            else:
                                summary[key] = value
                        print(f"   📄 Response Summary: {summary}")
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

    def test_courier_cancelled_requests_endpoint(self):
        """Test the new /api/courier/requests/cancelled endpoint according to review request"""
        print("\n🎯 COURIER CANCELLED REQUESTS ENDPOINT TESTING")
        print("   📋 Протестировать новый endpoint `/api/courier/requests/cancelled` для отмененных заявок в TAJLINE.TJ")
        print("   🔧 ЗАДАЧИ ТЕСТИРОВАНИЯ:")
        print("   1) COURIER AUTHENTICATION: Проверить вход курьера в систему (+79991234567/courier123)")
        print("   2) NEW CANCELLED REQUESTS ENDPOINT: Протестировать новый endpoint /api/courier/requests/cancelled:")
        print("      - Проверить аутентификацию и авторизацию")
        print("      - Проверить структуру ответа (courier_info, cancelled_requests, total_count)")
        print("      - Проверить что endpoint возвращает список отмененных заявок")
        print("   3) ENDPOINT INTEGRATION: Убедиться что новый endpoint корректно интегрирован с существующими endpoints курьера")
        print("   4) RESPONSE VALIDATION: Проверить что ответ содержит необходимые поля для UI (ID заявки, информация о грузе, история действий)")
        
        all_success = True
        
        # Test 1: COURIER AUTHENTICATION (+79991234567/courier123)
        print("\n   🔐 Test 1: COURIER AUTHENTICATION (+79991234567/courier123)...")
        
        courier_login_data = {
            "phone": "+79991234567",
            "password": "courier123"
        }
        
        success, login_response = self.run_test(
            "Courier Authentication",
            "POST",
            "/api/auth/login",
            200,
            courier_login_data
        )
        all_success &= success
        
        courier_token = None
        if success and 'access_token' in login_response:
            courier_token = login_response['access_token']
            courier_user = login_response.get('user', {})
            courier_role = courier_user.get('role')
            courier_name = courier_user.get('full_name')
            courier_phone = courier_user.get('phone')
            courier_user_number = courier_user.get('user_number')
            
            print(f"   ✅ Courier login successful: {courier_name}")
            print(f"   👑 Role: {courier_role}")
            print(f"   📞 Phone: {courier_phone}")
            print(f"   🆔 User Number: {courier_user_number}")
            
            # Verify role is courier
            if courier_role == 'courier':
                print("   ✅ Courier role correctly verified as 'courier'")
            else:
                print(f"   ❌ Courier role incorrect: expected 'courier', got '{courier_role}'")
                all_success = False
            
            self.tokens['courier'] = courier_token
            self.users['courier'] = courier_user
        else:
            print("   ❌ Courier authentication failed - no access token received")
            print(f"   📄 Response: {login_response}")
            all_success = False
            return False
        
        # Test 2: NEW CANCELLED REQUESTS ENDPOINT - Authentication and Authorization
        print("\n   🚫 Test 2: NEW CANCELLED REQUESTS ENDPOINT - Authentication and Authorization...")
        
        success, cancelled_requests_response = self.run_test(
            "Get Cancelled Courier Requests (Authentication & Authorization)",
            "GET",
            "/api/courier/requests/cancelled",
            200,
            token=courier_token
        )
        all_success &= success
        
        if success:
            print("   ✅ /api/courier/requests/cancelled endpoint accessible with courier authentication")
            print("   ✅ Authorization working - courier can access cancelled requests")
        else:
            print("   ❌ /api/courier/requests/cancelled endpoint authentication/authorization failed")
            all_success = False
            return False
        
        # Test 3: RESPONSE STRUCTURE VALIDATION (courier_info, cancelled_requests, total_count)
        print("\n   📊 Test 3: RESPONSE STRUCTURE VALIDATION...")
        
        if success and cancelled_requests_response:
            print("   🔍 Checking response structure for required fields...")
            
            # Check for required top-level fields
            required_fields = ['courier_info', 'cancelled_requests', 'total_count']
            missing_fields = []
            present_fields = []
            
            for field in required_fields:
                if field in cancelled_requests_response:
                    present_fields.append(field)
                    print(f"   ✅ Field '{field}' present in response")
                else:
                    missing_fields.append(field)
                    print(f"   ❌ Field '{field}' missing from response")
            
            if not missing_fields:
                print("   ✅ All required fields present (courier_info, cancelled_requests, total_count)")
            else:
                print(f"   ❌ Missing required fields: {missing_fields}")
                all_success = False
            
            # Validate field types and content
            courier_info = cancelled_requests_response.get('courier_info')
            cancelled_requests = cancelled_requests_response.get('cancelled_requests')
            total_count = cancelled_requests_response.get('total_count')
            
            # Validate courier_info
            if courier_info:
                if isinstance(courier_info, dict):
                    print("   ✅ courier_info is dictionary type")
                    courier_id = courier_info.get('id')
                    courier_full_name = courier_info.get('full_name')
                    if courier_id:
                        print(f"   ✅ courier_info contains courier ID: {courier_id}")
                    if courier_full_name:
                        print(f"   ✅ courier_info contains full name: {courier_full_name}")
                else:
                    print(f"   ❌ courier_info wrong type: expected dict, got {type(courier_info)}")
                    all_success = False
            else:
                print("   ❌ courier_info is empty or null")
                all_success = False
            
            # Validate cancelled_requests
            if cancelled_requests is not None:
                if isinstance(cancelled_requests, list):
                    print(f"   ✅ cancelled_requests is list type with {len(cancelled_requests)} items")
                    
                    # Check individual request structure if any exist
                    if len(cancelled_requests) > 0:
                        sample_request = cancelled_requests[0]
                        print("   🔍 Checking sample cancelled request structure...")
                        
                        # Check for essential fields in cancelled request
                        request_fields = ['id', 'request_status', 'created_at']
                        for field in request_fields:
                            if field in sample_request:
                                print(f"   ✅ Request field '{field}': {sample_request.get(field)}")
                            else:
                                print(f"   ⚠️  Request field '{field}' missing (may be optional)")
                        
                        # Verify request_status is 'cancelled'
                        request_status = sample_request.get('request_status')
                        if request_status == 'cancelled':
                            print("   ✅ Request status correctly set to 'cancelled'")
                        else:
                            print(f"   ❌ Request status incorrect: expected 'cancelled', got '{request_status}'")
                            all_success = False
                    else:
                        print("   ℹ️  No cancelled requests found (empty list)")
                else:
                    print(f"   ❌ cancelled_requests wrong type: expected list, got {type(cancelled_requests)}")
                    all_success = False
            else:
                print("   ❌ cancelled_requests is null")
                all_success = False
            
            # Validate total_count
            if total_count is not None:
                if isinstance(total_count, int):
                    print(f"   ✅ total_count is integer type: {total_count}")
                    
                    # Verify total_count matches list length
                    if cancelled_requests and len(cancelled_requests) == total_count:
                        print("   ✅ total_count matches cancelled_requests list length")
                    elif cancelled_requests:
                        print(f"   ⚠️  total_count ({total_count}) doesn't match list length ({len(cancelled_requests)})")
                else:
                    print(f"   ❌ total_count wrong type: expected int, got {type(total_count)}")
                    all_success = False
            else:
                print("   ❌ total_count is null")
                all_success = False
        else:
            print("   ❌ No response data to validate structure")
            all_success = False
        
        # Test 4: ENDPOINT INTEGRATION with existing courier endpoints
        print("\n   🔗 Test 4: ENDPOINT INTEGRATION with existing courier endpoints...")
        
        # Test 4.1: Compare with /api/courier/requests/new
        print("\n   📋 Test 4.1: Integration with /api/courier/requests/new...")
        
        success, new_requests_response = self.run_test(
            "Get New Courier Requests (for comparison)",
            "GET",
            "/api/courier/requests/new",
            200,
            token=courier_token
        )
        
        if success:
            print("   ✅ /api/courier/requests/new endpoint working")
            
            # Compare response structures
            if isinstance(new_requests_response, dict) and isinstance(cancelled_requests_response, dict):
                new_structure = set(new_requests_response.keys())
                cancelled_structure = set(cancelled_requests_response.keys())
                
                common_fields = new_structure.intersection(cancelled_structure)
                if 'courier_info' in common_fields and 'total_count' in common_fields:
                    print("   ✅ Response structures consistent between new and cancelled endpoints")
                    print(f"   📊 Common fields: {list(common_fields)}")
                else:
                    print("   ⚠️  Response structures differ between new and cancelled endpoints")
                    print(f"   📊 New endpoint fields: {list(new_structure)}")
                    print(f"   📊 Cancelled endpoint fields: {list(cancelled_structure)}")
            
            # Compare courier_info consistency
            new_courier_info = new_requests_response.get('courier_info', {})
            cancelled_courier_info = cancelled_requests_response.get('courier_info', {})
            
            if new_courier_info.get('id') == cancelled_courier_info.get('id'):
                print("   ✅ courier_info consistent between endpoints")
            else:
                print("   ❌ courier_info inconsistent between endpoints")
                all_success = False
        else:
            print("   ❌ /api/courier/requests/new endpoint failed - cannot compare integration")
            all_success = False
        
        # Test 4.2: Test /api/courier/requests/history integration
        print("\n   📚 Test 4.2: Integration with /api/courier/requests/history...")
        
        success, history_response = self.run_test(
            "Get Courier Requests History (for integration check)",
            "GET",
            "/api/courier/requests/history",
            200,
            token=courier_token
        )
        
        if success:
            print("   ✅ /api/courier/requests/history endpoint working")
            print("   ✅ All courier endpoints accessible - good integration")
        else:
            print("   ❌ /api/courier/requests/history endpoint failed")
            all_success = False
        
        # Test 5: RESPONSE VALIDATION for UI requirements
        print("\n   🖥️  Test 5: RESPONSE VALIDATION for UI requirements...")
        
        if cancelled_requests_response and cancelled_requests_response.get('cancelled_requests'):
            cancelled_requests_list = cancelled_requests_response.get('cancelled_requests', [])
            
            if len(cancelled_requests_list) > 0:
                print("   🔍 Checking UI-required fields in cancelled requests...")
                
                sample_request = cancelled_requests_list[0]
                
                # Check for UI-required fields
                ui_required_fields = {
                    'id': 'Request ID for tracking',
                    'cargo_name': 'Cargo information for display',
                    'sender_full_name': 'Sender information',
                    'pickup_address': 'Pickup location',
                    'created_at': 'Request creation time',
                    'updated_at': 'Last update time (history)',
                    'request_status': 'Current status'
                }
                
                ui_fields_present = 0
                ui_fields_total = len(ui_required_fields)
                
                for field, description in ui_required_fields.items():
                    if field in sample_request and sample_request[field]:
                        print(f"   ✅ UI field '{field}': {sample_request[field]} ({description})")
                        ui_fields_present += 1
                    else:
                        print(f"   ⚠️  UI field '{field}' missing or empty ({description})")
                
                ui_completeness = (ui_fields_present / ui_fields_total) * 100
                print(f"   📊 UI field completeness: {ui_fields_present}/{ui_fields_total} ({ui_completeness:.1f}%)")
                
                if ui_completeness >= 70:  # At least 70% of UI fields present
                    print("   ✅ Sufficient UI fields present for frontend display")
                else:
                    print("   ⚠️  Limited UI fields - may need additional data for complete UI")
                
                # Check for action history or status changes
                if 'updated_at' in sample_request or 'status_history' in sample_request:
                    print("   ✅ History/action information available for UI")
                else:
                    print("   ⚠️  No clear history/action information for UI")
                    
            else:
                print("   ℹ️  No cancelled requests available to validate UI fields")
                print("   ✅ Empty list is valid response - UI can handle no cancelled requests")
        else:
            print("   ❌ No cancelled requests data to validate for UI")
            all_success = False
        
        # Test 6: ACCESS CONTROL - Test with non-courier user
        print("\n   🚫 Test 6: ACCESS CONTROL - Non-courier user access denial...")
        
        # Try to login as warehouse operator to test access control
        operator_login_data = {
            "phone": "+79777888999",
            "password": "warehouse123"
        }
        
        success, operator_login_response = self.run_test(
            "Warehouse Operator Login (for access control test)",
            "POST",
            "/api/auth/login",
            200,
            operator_login_data
        )
        
        if success and 'access_token' in operator_login_response:
            operator_token = operator_login_response['access_token']
            operator_role = operator_login_response.get('user', {}).get('role')
            
            print(f"   ✅ Operator login successful (role: {operator_role})")
            
            # Try to access cancelled requests with operator token (should fail)
            success, _ = self.run_test(
                "Access Cancelled Requests with Operator Token (Should Fail)",
                "GET",
                "/api/courier/requests/cancelled",
                403,  # Should return 403 Forbidden
                token=operator_token
            )
            
            if success:
                print("   ✅ Access control working - non-courier user properly denied (403)")
            else:
                print("   ❌ Access control failed - non-courier user not properly denied")
                all_success = False
        else:
            print("   ⚠️  Could not test access control - operator login failed")
        
        # SUMMARY
        print("\n   📊 COURIER CANCELLED REQUESTS ENDPOINT TESTING SUMMARY:")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"   📈 Overall Success Rate: {self.tests_passed}/{self.tests_run} ({success_rate:.1f}%)")
        
        if all_success:
            print("   🎉 ALL TESTS PASSED - Courier Cancelled Requests Endpoint Working Perfectly!")
            print("   ✅ COURIER AUTHENTICATION: Вход курьера работает (+79991234567/courier123)")
            print("   ✅ NEW CANCELLED REQUESTS ENDPOINT: /api/courier/requests/cancelled работает")
            print("      - Аутентификация и авторизация работают ✅")
            print("      - Структура ответа корректна (courier_info, cancelled_requests, total_count) ✅")
            print("      - Endpoint возвращает список отмененных заявок ✅")
            print("   ✅ ENDPOINT INTEGRATION: Корректно интегрирован с существующими endpoints курьера")
            print("   ✅ RESPONSE VALIDATION: Ответ содержит необходимые поля для UI")
            print("   🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ ДОСТИГНУТ: Новый endpoint `/api/courier/requests/cancelled` работает корректно и готов к использованию в frontend для отображения отмененных заявок!")
        else:
            print("   ❌ SOME TESTS FAILED - Courier Cancelled Requests Endpoint needs attention")
            print("   🔍 Check the specific failed tests above for details")
            
            # List specific issues found
            if self.tests_passed < self.tests_run:
                failed_tests = self.tests_run - self.tests_passed
                print(f"   ⚠️  {failed_tests} test(s) failed out of {self.tests_run} total tests")
        
        return all_success

    def run_all_tests(self):
        """Run all courier cancelled requests tests"""
        print("🚀 Starting Courier Cancelled Requests Endpoint Testing...")
        
        overall_success = True
        
        # Run the main test
        success = self.test_courier_cancelled_requests_endpoint()
        overall_success &= success
        
        # Final summary
        print("\n" + "=" * 80)
        print("🏁 FINAL TESTING SUMMARY")
        print("=" * 80)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"📊 Total Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if overall_success:
            print("\n🎉 ALL COURIER CANCELLED REQUESTS TESTS PASSED!")
            print("✅ Новый endpoint `/api/courier/requests/cancelled` полностью функционален")
            print("✅ Готов к использованию в frontend для отображения отмененных заявок")
            print("✅ Корректно интегрирован с существующими endpoints курьера")
            print("✅ Содержит все необходимые поля для UI")
        else:
            print("\n❌ SOME COURIER CANCELLED REQUESTS TESTS FAILED")
            print("🔧 Review the failed tests above and fix the issues")
            print("⚠️  The endpoint may need additional work before production use")
        
        return overall_success

if __name__ == "__main__":
    tester = CourierCancelledRequestsTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
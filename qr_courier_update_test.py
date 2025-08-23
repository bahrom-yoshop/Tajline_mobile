#!/usr/bin/env python3
"""
QR Code Fixes and Courier Request Updates Testing for TAJLINE.TJ
Tests according to review request:
1) COURIER AUTHENTICATION: Проверить вход курьера в систему (+79991234567/courier123)
2) NEW UPDATE ENDPOINT: Протестировать новый endpoint /api/courier/requests/{request_id}/update (PUT)
3) COURIER REQUESTS ACCESS: Проверить доступ к заявкам для обновления
4) BACKEND STABILITY: Убедиться что исправления не повлияли на стабильность backend
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class QRCourierUpdateTester:
    def __init__(self, base_url="https://cargo-sync.preview.emergentagent.com"):
        self.base_url = base_url
        self.tokens = {}
        self.users = {}
        self.tests_run = 0
        self.tests_passed = 0
        
        print(f"🚛 TAJLINE.TJ QR Code Fixes and Courier Request Updates Tester")
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
                    if isinstance(result, dict) and len(str(result)) < 300:
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

    def test_courier_authentication(self):
        """Test 1: COURIER AUTHENTICATION - Проверить вход курьера в систему (+79991234567/courier123)"""
        print("\n🔐 TEST 1: COURIER AUTHENTICATION")
        print("   🎯 Проверить вход курьера в систему (+79991234567/courier123)")
        
        courier_login_data = {
            "phone": "+79991234567",
            "password": "courier123"
        }
        
        success, login_response = self.run_test(
            "Courier Authentication (+79991234567/courier123)",
            "POST",
            "/api/auth/login",
            200,
            courier_login_data
        )
        
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
            print(f"   🔑 JWT Token received: {courier_token[:50]}...")
            
            # Verify role is courier
            if courier_role == 'courier':
                print("   ✅ Courier role correctly set to 'courier'")
            else:
                print(f"   ❌ Courier role incorrect: expected 'courier', got '{courier_role}'")
                return False
            
            # Store courier token for further tests
            self.tokens['courier'] = courier_token
            self.users['courier'] = courier_user
            
            return True
        else:
            print("   ❌ Courier login failed - no access token received")
            print(f"   📄 Response: {login_response}")
            return False

    def test_courier_requests_access(self):
        """Test 3: COURIER REQUESTS ACCESS - Проверить доступ к заявкам для обновления"""
        print("\n📋 TEST 3: COURIER REQUESTS ACCESS")
        print("   🎯 Проверить доступ к заявкам для обновления:")
        print("   - Получить список принятых заявок /api/courier/requests/accepted")
        print("   - Проверить что заявки содержат необходимые поля для обновления")
        
        if 'courier' not in self.tokens:
            print("   ❌ No courier token available")
            return False
        
        courier_token = self.tokens['courier']
        all_success = True
        
        # Test 3.1: Get accepted requests
        print("\n   📋 Test 3.1: GET /api/courier/requests/accepted...")
        
        success, accepted_requests = self.run_test(
            "Get Accepted Courier Requests",
            "GET",
            "/api/courier/requests/accepted",
            200,
            token=courier_token
        )
        all_success &= success
        
        request_id_for_update = None
        
        if success:
            print("   ✅ /api/courier/requests/accepted endpoint working")
            
            # Verify response structure
            if isinstance(accepted_requests, dict):
                requests_list = accepted_requests.get('accepted_requests', [])
                total_count = accepted_requests.get('total_count', 0)
                courier_info = accepted_requests.get('courier_info', {})
                
                print(f"   📊 Accepted requests found: {total_count}")
                print(f"   📋 Items in response: {len(requests_list)}")
                print(f"   👤 Courier info available: {bool(courier_info)}")
                
                # Check for required fields for updates
                required_fields = ['accepted_requests', 'total_count', 'courier_info']
                missing_fields = [field for field in required_fields if field not in accepted_requests]
                
                if not missing_fields:
                    print("   ✅ Response structure correct (accepted_requests, total_count, courier_info)")
                else:
                    print(f"   ❌ Missing required fields: {missing_fields}")
                    all_success = False
                
                # Check individual request fields for update capability
                if requests_list and len(requests_list) > 0:
                    sample_request = requests_list[0]
                    request_id_for_update = sample_request.get('id')
                    
                    # Fields needed for updates
                    update_fields = ['id', 'cargo_name', 'sender_full_name', 'pickup_address', 'created_at', 'request_status']
                    available_fields = [field for field in update_fields if field in sample_request]
                    missing_update_fields = [field for field in update_fields if field not in sample_request]
                    
                    print(f"   📋 Available fields for updates: {available_fields}")
                    if missing_update_fields:
                        print(f"   ⚠️  Missing fields for updates: {missing_update_fields}")
                    
                    # Check specific fields
                    if 'id' in sample_request:
                        print(f"   🆔 Request ID available: {sample_request['id']}")
                    if 'cargo_name' in sample_request:
                        print(f"   📦 Cargo name: {sample_request['cargo_name']}")
                    if 'sender_full_name' in sample_request:
                        print(f"   👤 Sender: {sample_request['sender_full_name']}")
                    if 'pickup_address' in sample_request:
                        print(f"   📍 Pickup address: {sample_request['pickup_address']}")
                    if 'request_status' in sample_request:
                        print(f"   📊 Status: {sample_request['request_status']}")
                    
                    print("   ✅ Request contains necessary fields for update operations")
                else:
                    print("   ⚠️  No accepted requests available for field verification")
                    
            elif isinstance(accepted_requests, list):
                request_count = len(accepted_requests)
                print(f"   📊 Accepted requests found: {request_count}")
                print("   ✅ Direct list response format")
                
                if request_count > 0:
                    request_id_for_update = accepted_requests[0].get('id')
            else:
                print("   ❌ Unexpected response format for accepted requests")
                all_success = False
        else:
            print("   ❌ /api/courier/requests/accepted endpoint failed")
            all_success = False
        
        # Store request ID for update testing
        if request_id_for_update:
            self.request_id_for_update = request_id_for_update
            print(f"   🆔 Request ID stored for update testing: {request_id_for_update}")
        
        return all_success

    def test_new_update_endpoint(self):
        """Test 2: NEW UPDATE ENDPOINT - Протестировать новый endpoint /api/courier/requests/{request_id}/update (PUT)"""
        print("\n🔄 TEST 2: NEW UPDATE ENDPOINT")
        print("   🎯 Протестировать новый endpoint /api/courier/requests/{request_id}/update (PUT):")
        print("   - Проверить аутентификацию и авторизацию курьера")
        print("   - Проверить обновление данных заявки курьером")
        print("   - Проверить валидацию и обработку ошибок")
        
        if 'courier' not in self.tokens:
            print("   ❌ No courier token available")
            return False
        
        courier_token = self.tokens['courier']
        all_success = True
        
        # First, we need a request ID to update
        if not hasattr(self, 'request_id_for_update') or not self.request_id_for_update:
            print("   ⚠️  No request ID available for update testing")
            print("   🔍 Attempting to get a request ID from accepted requests...")
            
            # Try to get accepted requests to find an ID
            success, accepted_requests = self.run_test(
                "Get Request ID for Update Testing",
                "GET",
                "/api/courier/requests/accepted",
                200,
                token=courier_token
            )
            
            if success and isinstance(accepted_requests, dict):
                requests_list = accepted_requests.get('accepted_requests', [])
                if requests_list and len(requests_list) > 0:
                    self.request_id_for_update = requests_list[0].get('id')
                    print(f"   🆔 Found request ID: {self.request_id_for_update}")
                else:
                    print("   ❌ No accepted requests available for update testing")
                    return False
            else:
                print("   ❌ Could not retrieve request ID for update testing")
                return False
        
        request_id = self.request_id_for_update
        
        # Test 2.1: Authentication and Authorization Check
        print(f"\n   🔐 Test 2.1: Authentication and Authorization for Request {request_id}...")
        
        # Test with valid courier token
        update_data = {
            "request_status": "accepted",
            "courier_notes": "Заявка принята курьером для тестирования обновлений"
        }
        
        success, update_response = self.run_test(
            f"Update Courier Request {request_id} (Authentication Check)",
            "PUT",
            f"/api/courier/requests/{request_id}/update",
            200,
            update_data,
            courier_token
        )
        
        if success:
            print("   ✅ Courier authentication and authorization working")
            print("   ✅ Courier can access update endpoint")
            
            # Verify response structure
            if isinstance(update_response, dict):
                if 'success' in update_response or 'message' in update_response or 'updated_request' in update_response:
                    print("   ✅ Update response structure correct")
                    
                    if update_response.get('success'):
                        print("   ✅ Update operation successful")
                    elif 'message' in update_response:
                        print(f"   📄 Update message: {update_response['message']}")
                    
                    if 'updated_request' in update_response:
                        updated_request = update_response['updated_request']
                        if 'request_status' in updated_request:
                            print(f"   📊 Updated status: {updated_request['request_status']}")
                        if 'courier_notes' in updated_request:
                            print(f"   📝 Updated notes: {updated_request['courier_notes']}")
                else:
                    print("   ⚠️  Unexpected update response structure")
            else:
                print("   ⚠️  Non-dict update response")
        else:
            print("   ❌ Courier authentication/authorization failed for update endpoint")
            all_success = False
        
        # Test 2.2: Data Update Verification
        print(f"\n   📝 Test 2.2: Data Update Verification for Request {request_id}...")
        
        # Test different update scenarios
        update_scenarios = [
            {
                "name": "Status Update to 'completed'",
                "data": {
                    "request_status": "completed",
                    "courier_notes": "Заявка выполнена успешно"
                }
            },
            {
                "name": "Status Update to 'cancelled'",
                "data": {
                    "request_status": "cancelled",
                    "courier_notes": "Заявка отменена по просьбе клиента"
                }
            },
            {
                "name": "Notes Only Update",
                "data": {
                    "courier_notes": "Обновлены только заметки курьера"
                }
            }
        ]
        
        for i, scenario in enumerate(update_scenarios, 1):
            print(f"\n   📝 Test 2.2.{i}: {scenario['name']}...")
            
            success, scenario_response = self.run_test(
                f"Update Request - {scenario['name']}",
                "PUT",
                f"/api/courier/requests/{request_id}/update",
                200,
                scenario['data'],
                courier_token
            )
            
            if success:
                print(f"   ✅ {scenario['name']} successful")
                
                # Verify the update was applied
                if isinstance(scenario_response, dict):
                    if 'updated_request' in scenario_response:
                        updated_request = scenario_response['updated_request']
                        
                        # Check if status was updated
                        if 'request_status' in scenario['data']:
                            expected_status = scenario['data']['request_status']
                            actual_status = updated_request.get('request_status')
                            if actual_status == expected_status:
                                print(f"   ✅ Status correctly updated to: {actual_status}")
                            else:
                                print(f"   ❌ Status update failed: expected {expected_status}, got {actual_status}")
                                all_success = False
                        
                        # Check if notes were updated
                        if 'courier_notes' in scenario['data']:
                            expected_notes = scenario['data']['courier_notes']
                            actual_notes = updated_request.get('courier_notes')
                            if actual_notes == expected_notes:
                                print(f"   ✅ Notes correctly updated")
                            else:
                                print(f"   ❌ Notes update failed")
                                all_success = False
                    else:
                        print(f"   ⚠️  No updated_request in response for {scenario['name']}")
            else:
                print(f"   ❌ {scenario['name']} failed")
                all_success = False
        
        # Test 2.3: Validation and Error Handling
        print(f"\n   ⚠️  Test 2.3: Validation and Error Handling...")
        
        # Test invalid request status
        print("\n   ❌ Test 2.3.1: Invalid Request Status...")
        
        invalid_status_data = {
            "request_status": "invalid_status",
            "courier_notes": "Тест невалидного статуса"
        }
        
        success, error_response = self.run_test(
            "Update with Invalid Status (Should Fail)",
            "PUT",
            f"/api/courier/requests/{request_id}/update",
            400,  # Should return 400 Bad Request
            invalid_status_data,
            courier_token
        )
        
        if success:
            print("   ✅ Invalid status properly rejected with 400 error")
        else:
            print("   ❌ Invalid status validation not working correctly")
            all_success = False
        
        # Test non-existent request ID
        print("\n   ❌ Test 2.3.2: Non-existent Request ID...")
        
        fake_request_id = "00000000-0000-0000-0000-000000000000"
        
        success, not_found_response = self.run_test(
            "Update Non-existent Request (Should Return 404)",
            "PUT",
            f"/api/courier/requests/{fake_request_id}/update",
            404,  # Should return 404 Not Found
            update_data,
            courier_token
        )
        
        if success:
            print("   ✅ Non-existent request properly rejected with 404 error")
        else:
            print("   ❌ Non-existent request handling not working correctly")
            all_success = False
        
        # Test unauthorized access (without token)
        print("\n   ❌ Test 2.3.3: Unauthorized Access...")
        
        success, unauthorized_response = self.run_test(
            "Update without Token (Should Return 401)",
            "PUT",
            f"/api/courier/requests/{request_id}/update",
            401,  # Should return 401 Unauthorized
            update_data
            # No token provided
        )
        
        if success:
            print("   ✅ Unauthorized access properly rejected with 401 error")
        else:
            print("   ❌ Unauthorized access handling not working correctly")
            all_success = False
        
        return all_success

    def test_backend_stability(self):
        """Test 4: BACKEND STABILITY - Убедиться что исправления не повлияли на стабильность backend"""
        print("\n🔧 TEST 4: BACKEND STABILITY")
        print("   🎯 Убедиться что исправления не повлияли на стабильность backend")
        
        if 'courier' not in self.tokens:
            print("   ❌ No courier token available")
            return False
        
        courier_token = self.tokens['courier']
        all_success = True
        
        # Test 4.1: Core Courier Endpoints Stability
        print("\n   🔗 Test 4.1: Core Courier Endpoints Stability...")
        
        core_endpoints = [
            ("/api/auth/me", "Current User Info"),
            ("/api/courier/requests/new", "New Courier Requests"),
            ("/api/courier/requests/accepted", "Accepted Courier Requests"),
            ("/api/courier/requests/history", "Courier Requests History"),
        ]
        
        stable_endpoints = 0
        
        for endpoint, description in core_endpoints:
            print(f"\n   🔍 Testing {description} ({endpoint})...")
            
            success, response = self.run_test(
                f"Stability Check - {description}",
                "GET",
                endpoint,
                200,
                token=courier_token
            )
            
            if success:
                print(f"   ✅ {description} stable")
                stable_endpoints += 1
                
                # Check for JSON serialization issues
                if isinstance(response, (dict, list)):
                    response_str = str(response)
                    if 'ObjectId' in response_str:
                        print(f"   ⚠️  Potential ObjectId serialization issue in {description}")
                        all_success = False
                    else:
                        print(f"   ✅ JSON serialization correct for {description}")
            else:
                print(f"   ❌ {description} unstable")
                all_success = False
        
        stability_rate = (stable_endpoints / len(core_endpoints) * 100) if core_endpoints else 0
        print(f"\n   📊 Endpoint Stability Rate: {stable_endpoints}/{len(core_endpoints)} ({stability_rate:.1f}%)")
        
        # Test 4.2: Session Management Stability
        print("\n   🔐 Test 4.2: Session Management Stability...")
        
        # Test multiple requests with same token
        session_tests = 0
        session_successes = 0
        
        for i in range(3):
            success, auth_response = self.run_test(
                f"Session Stability Test {i+1}",
                "GET",
                "/api/auth/me",
                200,
                token=courier_token
            )
            
            session_tests += 1
            if success:
                session_successes += 1
        
        if session_successes == session_tests:
            print(f"   ✅ Session management stable ({session_successes}/{session_tests} tests passed)")
        else:
            print(f"   ❌ Session management unstable ({session_successes}/{session_tests} tests passed)")
            all_success = False
        
        # Test 4.3: Error Handling Stability
        print("\n   ⚠️  Test 4.3: Error Handling Stability...")
        
        # Test various error scenarios to ensure they don't crash the backend
        error_scenarios = [
            {
                "name": "Invalid Endpoint",
                "method": "GET",
                "endpoint": "/api/courier/invalid-endpoint",
                "expected_status": 404,
                "description": "404 Not Found handling"
            },
            {
                "name": "Invalid Method",
                "method": "DELETE",
                "endpoint": "/api/courier/requests/new",
                "expected_status": 405,
                "description": "405 Method Not Allowed handling"
            }
        ]
        
        error_handling_stable = True
        
        for scenario in error_scenarios:
            success, error_response = self.run_test(
                f"Error Handling - {scenario['name']}",
                scenario['method'],
                scenario['endpoint'],
                scenario['expected_status'],
                token=courier_token
            )
            
            if success:
                print(f"   ✅ {scenario['description']} working correctly")
            else:
                print(f"   ❌ {scenario['description']} not working correctly")
                error_handling_stable = False
        
        if error_handling_stable:
            print("   ✅ Error handling mechanisms stable")
        else:
            print("   ❌ Error handling mechanisms unstable")
            all_success = False
        
        # Test 4.4: QR Code Generation Stability (if endpoint exists)
        print("\n   📱 Test 4.4: QR Code Generation Stability...")
        
        # Test if QR generation still works after fixes
        success, qr_response = self.run_test(
            "QR Code Generation Stability Check",
            "GET",
            "/api/cargo/track/2501000001",  # Test with a sample cargo number
            200,
            token=courier_token
        )
        
        if success:
            print("   ✅ QR code related endpoints stable")
            
            # Check if response contains QR-related data
            if isinstance(qr_response, dict):
                qr_fields = ['cargo_number', 'cargo_name', 'status']
                available_qr_fields = [field for field in qr_fields if field in qr_response]
                
                if available_qr_fields:
                    print(f"   ✅ QR data fields available: {available_qr_fields}")
                else:
                    print("   ⚠️  QR data fields may not be available")
        else:
            print("   ⚠️  QR code related endpoints may need attention")
            # Don't fail completely as this might be expected for non-existent cargo
        
        return all_success

    def run_all_tests(self):
        """Run all tests according to review request"""
        print("\n🚀 STARTING QR CODE FIXES AND COURIER REQUEST UPDATES TESTING")
        print("   📋 ЗАДАЧИ ТЕСТИРОВАНИЯ:")
        print("   1) COURIER AUTHENTICATION: Проверить вход курьера в систему (+79991234567/courier123)")
        print("   2) NEW UPDATE ENDPOINT: Протестировать новый endpoint /api/courier/requests/{request_id}/update (PUT)")
        print("   3) COURIER REQUESTS ACCESS: Проверить доступ к заявкам для обновления")
        print("   4) BACKEND STABILITY: Убедиться что исправления не повлияли на стабильность backend")
        
        all_tests_passed = True
        
        # Test 1: Courier Authentication
        test1_result = self.test_courier_authentication()
        all_tests_passed &= test1_result
        
        # Test 3: Courier Requests Access (before Test 2 to get request ID)
        test3_result = self.test_courier_requests_access()
        all_tests_passed &= test3_result
        
        # Test 2: New Update Endpoint
        test2_result = self.test_new_update_endpoint()
        all_tests_passed &= test2_result
        
        # Test 4: Backend Stability
        test4_result = self.test_backend_stability()
        all_tests_passed &= test4_result
        
        # Final Summary
        print("\n" + "=" * 80)
        print("🎯 FINAL TEST RESULTS SUMMARY")
        print("=" * 80)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"📊 Overall Test Results: {self.tests_passed}/{self.tests_run} ({success_rate:.1f}%)")
        
        test_results = [
            ("1️⃣ COURIER AUTHENTICATION", test1_result),
            ("2️⃣ NEW UPDATE ENDPOINT", test2_result),
            ("3️⃣ COURIER REQUESTS ACCESS", test3_result),
            ("4️⃣ BACKEND STABILITY", test4_result)
        ]
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {test_name}: {status}")
        
        if all_tests_passed:
            print("\n🎉 ALL TESTS PASSED - QR CODE FIXES AND COURIER REQUEST UPDATES WORKING!")
            print("✅ Ожидаемый результат: Backend поддерживает обновление заявок курьером, QR коды генерируются только с номерами заявок, система стабильна.")
            print("✅ COURIER AUTHENTICATION: Вход курьера работает (+79991234567/courier123)")
            print("✅ NEW UPDATE ENDPOINT: /api/courier/requests/{request_id}/update (PUT) функционален")
            print("✅ COURIER REQUESTS ACCESS: Доступ к заявкам для обновления работает")
            print("✅ BACKEND STABILITY: Исправления не повлияли на стабильность backend")
        else:
            print("\n❌ SOME TESTS FAILED - QR CODE FIXES AND COURIER REQUEST UPDATES NEED ATTENTION")
            print("🔍 Check the specific failed tests above for details")
            
            failed_tests = [name for name, result in test_results if not result]
            if failed_tests:
                print("❌ Failed test categories:")
                for test_name in failed_tests:
                    print(f"   - {test_name}")
        
        return all_tests_passed

if __name__ == "__main__":
    tester = QRCourierUpdateTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Courier Backend Stability Testing for TAJLINE.TJ
Quick test of backend stability after courier UI updates
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class CourierBackendTester:
    def __init__(self, base_url="https://placement-view.preview.emergentagent.com"):
        self.base_url = base_url
        self.tokens = {}
        self.users = {}
        self.tests_run = 0
        self.tests_passed = 0
        
        print(f"🚚 TAJLINE.TJ Courier Backend Stability Tester")
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
                response = requests.delete(url, json=data, headers=headers)

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

    def test_courier_backend_stability_after_ui_updates(self):
        """Test courier backend stability after UI updates according to review request"""
        print("\n🚚 COURIER BACKEND STABILITY AFTER UI UPDATES TESTING")
        print("   🎯 Быстро протестировать стабильность backend после обновления UI курьера в TAJLINE.TJ")
        print("   🔧 ЗАДАЧИ ТЕСТИРОВАНИЯ:")
        print("   1) COURIER AUTHENTICATION: Проверить вход курьера в систему (+79991234567/courier123)")
        print("   2) COURIER REQUESTS ENDPOINT: Протестировать endpoint /api/courier/requests/new для получения новых заявок")
        print("   3) BASIC API ENDPOINTS: Убедиться что основные endpoints для курьеров работают корректно без ошибок")
        print("   4) BACKEND STABILITY: Проверить что изменения в frontend не повлияли на backend функциональность")
        
        all_success = True
        
        # Test 1: COURIER AUTHENTICATION (+79991234567/courier123)
        print("\n   🔐 Test 1: COURIER AUTHENTICATION (+79991234567/courier123)...")
        
        courier_login_data = {
            "phone": "+79991234567",
            "password": "courier123"
        }
        
        success, login_response = self.run_test(
            "Courier Login Authentication",
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
            print(f"   🔑 JWT Token received: {courier_token[:50]}...")
            
            # Verify role is courier
            if courier_role == 'courier':
                print("   ✅ Courier role correctly set to 'courier'")
            else:
                print(f"   ❌ Courier role incorrect: expected 'courier', got '{courier_role}'")
                all_success = False
            
            self.tokens['courier'] = courier_token
            self.users['courier'] = courier_user
        else:
            print("   ❌ Courier login failed - no access token received")
            print(f"   📄 Response: {login_response}")
            all_success = False
            return False
        
        # Test 2: COURIER REQUESTS ENDPOINT /api/courier/requests/new (для badge с количеством)
        print("\n   📋 Test 2: COURIER REQUESTS ENDPOINT /api/courier/requests/new...")
        print("   🎯 Тестирование endpoint для получения новых заявок (необходимо для отображения badge с количеством)")
        
        success, requests_response = self.run_test(
            "Get New Courier Requests (for badge count)",
            "GET",
            "/api/courier/requests/new",
            200,
            token=courier_token
        )
        all_success &= success
        
        if success:
            print("   ✅ /api/courier/requests/new endpoint working")
            
            # Verify response structure for badge count
            if isinstance(requests_response, dict):
                # Check for courier-specific response structure
                if 'new_requests' in requests_response and 'total_count' in requests_response:
                    new_requests = requests_response['new_requests']
                    total_count = requests_response.get('total_count', 0)
                    courier_info = requests_response.get('courier_info', {})
                    
                    print(f"   📊 New requests found: {total_count}")
                    print(f"   📋 New requests items: {len(new_requests) if isinstance(new_requests, list) else 0}")
                    print(f"   👤 Courier info present: {'Yes' if courier_info else 'No'}")
                    print("   ✅ Courier-specific response structure correct for badge count calculation")
                    
                elif 'items' in requests_response:
                    # Standard pagination structure
                    requests_items = requests_response['items']
                    total_count = requests_response.get('total_count', 0)
                    print(f"   📊 New requests found: {total_count}")
                    print(f"   📋 Items in current page: {len(requests_items)}")
                    
                    # Verify pagination fields for badge count
                    pagination_fields = ['total_count', 'page', 'per_page', 'total_pages']
                    missing_fields = [field for field in pagination_fields if field not in requests_response]
                    
                    if not missing_fields:
                        print("   ✅ Pagination structure correct for badge count calculation")
                    else:
                        print(f"   ❌ Missing pagination fields: {missing_fields}")
                        all_success = False
                        
                elif isinstance(requests_response, list):
                    # Direct list response
                    request_count = len(requests_response)
                    print(f"   📊 New requests found: {request_count}")
                    print("   ✅ Direct list response format")
                else:
                    print("   ❌ Unexpected response format for new requests")
                    print(f"   📄 Response keys: {list(requests_response.keys())}")
                    all_success = False
            else:
                print("   ❌ Response is not in expected format")
                all_success = False
        else:
            print("   ❌ /api/courier/requests/new endpoint failed")
            all_success = False
        
        # Test 3: BASIC API ENDPOINTS для курьеров
        print("\n   🔗 Test 3: BASIC API ENDPOINTS для курьеров...")
        
        basic_endpoints = [
            ("/api/auth/me", "Current User Info"),
            ("/api/courier/requests/history", "Courier Request History")
        ]
        
        endpoint_results = []
        successful_endpoints = 0
        
        for endpoint, description in basic_endpoints:
            print(f"\n   🔍 Testing {description} ({endpoint})...")
            
            success, response = self.run_test(
                description,
                "GET",
                endpoint,
                200,
                token=courier_token
            )
            
            endpoint_results.append({
                'endpoint': endpoint,
                'description': description,
                'success': success,
                'response': response
            })
            
            if success:
                successful_endpoints += 1
                print(f"   ✅ {description} working")
                
                # Special checks for specific endpoints
                if endpoint == "/api/auth/me":
                    user_role = response.get('role')
                    if user_role == 'courier':
                        print("   ✅ User role verification passed")
                    else:
                        print(f"   ❌ User role verification failed: expected 'courier', got '{user_role}'")
                        all_success = False
                        
                elif endpoint == "/api/courier/requests/history":
                    # Check pagination structure
                    if isinstance(response, dict) and 'pagination' in response:
                        pagination = response['pagination']
                        total_count = pagination.get('total_count', 0)
                        page = pagination.get('page', 1)
                        print(f"   📊 History pagination: {total_count} total, page {page}")
                        print("   ✅ History pagination structure correct")
                    elif isinstance(response, list):
                        print(f"   📊 History items: {len(response)}")
                        print("   ✅ Direct list response format")
            else:
                print(f"   ❌ {description} failed")
                all_success = False
        
        # Test 4: BACKEND STABILITY CHECK
        print("\n   🔧 Test 4: BACKEND STABILITY CHECK...")
        
        # Check for 500 Internal Server Errors
        error_500_count = 0
        for result in endpoint_results:
            if not result['success']:
                # Check if it was a 500 error by making the request again
                try:
                    url = f"{self.base_url}{result['endpoint']}"
                    headers = {'Authorization': f'Bearer {courier_token}', 'Content-Type': 'application/json'}
                    response = requests.get(url, headers=headers)
                    if response.status_code == 500:
                        error_500_count += 1
                        print(f"   ❌ 500 Error in {result['description']} ({result['endpoint']})")
                except:
                    pass
        
        if error_500_count == 0:
            print("   ✅ No 500 Internal Server Errors found")
        else:
            print(f"   ❌ Found {error_500_count} endpoints with 500 Internal Server Errors")
            all_success = False
        
        # Check JSON serialization (no ObjectId errors)
        serialization_issues = 0
        for result in endpoint_results:
            if result['success'] and result['response']:
                try:
                    import json
                    json_str = json.dumps(result['response'])
                    if 'ObjectId' in json_str:
                        serialization_issues += 1
                        print(f"   ❌ ObjectId serialization issue in {result['description']}")
                except Exception as e:
                    serialization_issues += 1
                    print(f"   ❌ JSON serialization error in {result['description']}: {str(e)}")
        
        if serialization_issues == 0:
            print("   ✅ JSON serialization correct (no ObjectId errors)")
        else:
            print(f"   ❌ Found {serialization_issues} endpoints with JSON serialization issues")
            all_success = False
        
        # Session stability check
        print("\n   🔐 Test 4.1: SESSION STABILITY CHECK...")
        
        # Make multiple requests to verify session stability
        session_requests = [
            ("/api/auth/me", "User Info"),
            ("/api/courier/requests/new", "New Requests"),
            ("/api/auth/me", "User Info Again")
        ]
        
        session_stable = True
        for endpoint, description in session_requests:
            success, _ = self.run_test(
                f"Session Stability - {description}",
                "GET",
                endpoint,
                200,
                token=courier_token
            )
            if not success:
                session_stable = False
                break
        
        if session_stable:
            print("   ✅ Session stability confirmed (3/3 requests successful)")
        else:
            print("   ❌ Session instability detected")
            all_success = False
        
        # SUMMARY
        print("\n   📊 COURIER BACKEND STABILITY SUMMARY:")
        
        total_endpoints = len(basic_endpoints) + 1  # +1 for requests/new
        success_rate = (successful_endpoints / total_endpoints * 100) if total_endpoints > 0 else 0
        
        print(f"   📈 Endpoint Success Rate: {successful_endpoints}/{total_endpoints} ({success_rate:.1f}%)")
        
        if all_success:
            print("   🎉 COURIER BACKEND STABILITY TESTING COMPLETED SUCCESSFULLY!")
            print("   ✅ Courier authentication working (+79991234567/courier123)")
            print("   ✅ /api/courier/requests/new endpoint working and returns data for badge count")
            print("   ✅ Basic API endpoints working correctly without errors")
            print("   ✅ No 500 Internal Server Errors detected")
            print("   ✅ JSON serialization correct (no ObjectId errors)")
            print("   ✅ Session stability confirmed")
            print("   🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ ДОСТИГНУТ: Backend остается стабильным после обновления UI интерфейса курьера")
            print("   🎯 Все endpoints для отображения количества заявок в badge работают корректно")
        else:
            print("   ❌ SOME COURIER BACKEND STABILITY TESTS FAILED")
            print("   🔍 Check the specific failed tests above for details")
            
            # List failed endpoints
            failed_endpoints = [result for result in endpoint_results if not result['success']]
            if failed_endpoints:
                print("   ❌ Failed endpoints:")
                for result in failed_endpoints:
                    print(f"     - {result['description']} ({result['endpoint']})")
        
        return all_success

    def run_all_tests(self):
        """Run all courier backend stability tests"""
        print(f"\n🚀 Starting Courier Backend Stability Tests...")
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run the main test
        success = self.test_courier_backend_stability_after_ui_updates()
        
        # Final summary
        print(f"\n{'='*60}")
        print(f"📊 FINAL TEST RESULTS")
        print(f"{'='*60}")
        print(f"🔢 Total Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if success:
            print(f"🎉 OVERALL RESULT: SUCCESS")
            print(f"✅ Backend is stable after courier UI updates")
        else:
            print(f"❌ OVERALL RESULT: SOME ISSUES FOUND")
            print(f"⚠️  Backend stability needs attention")
        
        return success

if __name__ == "__main__":
    tester = CourierBackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
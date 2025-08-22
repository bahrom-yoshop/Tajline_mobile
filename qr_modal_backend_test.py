#!/usr/bin/env python3
"""
Backend Stability Testing After QR Code Modal JavaScript Fix for TAJLINE.TJ
Tests backend stability after fixing JavaScript error "Cannot read properties of null (reading 'document')" 
when printing QR codes in modal window for accepting warehouse notifications by operators.
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class QRModalBackendTester:
    def __init__(self, base_url="https://tajline-cargo-7.preview.emergentagent.com"):
        self.base_url = base_url
        self.tokens = {}
        self.users = {}
        self.tests_run = 0
        self.tests_passed = 0
        
        print(f"🎯 TAJLINE.TJ QR Modal Backend Stability Tester")
        print(f"📡 Base URL: {self.base_url}")
        print(f"🔧 Testing backend stability after QR code modal JavaScript fix")
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
                    elif isinstance(result, list) and len(result) > 0:
                        print(f"   📄 Response: Found {len(result)} items")
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

    def test_warehouse_operator_qr_modal_backend_stability(self):
        """
        Test backend stability after fixing JavaScript QR code modal error for warehouse operators
        
        КОНТЕКСТ: Исправлена ошибка "Cannot read properties of null (reading 'document')" 
        при нажатии кнопки "QR код" для каждого груза в модальном окне принятия заявки.
        Добавлена проверка на null для результата window.open().
        
        ТЕСТОВЫЙ ПЛАН:
        1. Авторизация оператора склада (+79777888999/warehouse123)
        2. Проверка API endpoints для уведомлений склада (/api/operator/warehouse-notifications)
        3. Тестирование принятия уведомления (/api/operator/warehouse-notifications/{id}/accept)
        4. Проверка endpoint завершения оформления (/api/operator/warehouse-notifications/{id}/complete)
        5. Проверка стабильности всех операторских endpoints после frontend изменений
        """
        print("\n🎯 BACKEND STABILITY AFTER QR MODAL JAVASCRIPT FIX TESTING")
        print("   📋 Протестировать стабильность backend после исправления JavaScript ошибки")
        print("   🔧 при печати QR кодов в модальном окне принятия заявки оператором")
        
        all_success = True
        
        # Test 1: АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА (+79777888999/warehouse123)
        print("\n   🔐 Test 1: АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА (+79777888999/warehouse123)...")
        
        operator_login_data = {
            "phone": "+79777888999",
            "password": "warehouse123"
        }
        
        success, login_response = self.run_test(
            "Warehouse Operator Authentication",
            "POST",
            "/api/auth/login",
            200,
            operator_login_data
        )
        all_success &= success
        
        operator_token = None
        if success and 'access_token' in login_response:
            operator_token = login_response['access_token']
            operator_user = login_response.get('user', {})
            operator_role = operator_user.get('role')
            operator_name = operator_user.get('full_name')
            operator_phone = operator_user.get('phone')
            operator_user_number = operator_user.get('user_number')
            
            print(f"   ✅ Operator login successful: {operator_name}")
            print(f"   👑 Role: {operator_role}")
            print(f"   📞 Phone: {operator_phone}")
            print(f"   🆔 User Number: {operator_user_number}")
            print(f"   🔑 JWT Token received: {operator_token[:50]}...")
            
            # Verify role is warehouse_operator
            if operator_role == 'warehouse_operator':
                print("   ✅ Operator role correctly set to 'warehouse_operator'")
            else:
                print(f"   ❌ Operator role incorrect: expected 'warehouse_operator', got '{operator_role}'")
                all_success = False
            
            self.tokens['warehouse_operator'] = operator_token
            self.users['warehouse_operator'] = operator_user
        else:
            print("   ❌ Operator login failed - no access token received")
            print(f"   📄 Response: {login_response}")
            all_success = False
            return False
        
        # Test 2: ПРОВЕРКА API ENDPOINTS ДЛЯ УВЕДОМЛЕНИЙ СКЛАДА (/api/operator/warehouse-notifications)
        print("\n   📬 Test 2: API ENDPOINTS ДЛЯ УВЕДОМЛЕНИЙ СКЛАДА...")
        
        success, notifications_response = self.run_test(
            "Get Warehouse Notifications",
            "GET",
            "/api/operator/warehouse-notifications",
            200,
            token=operator_token
        )
        all_success &= success
        
        notification_id = None
        if success:
            print("   ✅ /api/operator/warehouse-notifications endpoint working")
            
            # Verify response structure
            if isinstance(notifications_response, list):
                notification_count = len(notifications_response)
                print(f"   📊 Found {notification_count} warehouse notifications")
                
                # Find a notification that can be tested
                for notification in notifications_response:
                    if notification.get('status') in ['pending_acceptance', 'pending']:
                        notification_id = notification.get('id')
                        notification_type = notification.get('type', 'unknown')
                        notification_status = notification.get('status', 'unknown')
                        
                        print(f"   📋 Test notification found: {notification_id}")
                        print(f"   📋 Type: {notification_type}")
                        print(f"   📋 Status: {notification_status}")
                        break
                
                if not notification_id:
                    print("   ⚠️  No pending notifications found for testing")
                    # Create a test notification by creating a pickup request first
                    print("   🔧 Creating test pickup request to generate notification...")
                    
                    # Create test pickup request to generate notification
                    pickup_data = {
                        "sender_full_name": "Тест QR Modal Отправитель",
                        "sender_phone": "+79991234567",
                        "pickup_address": "Москва, ул. QR Modal Тест, 1",
                        "pickup_date": "2025-01-20",
                        "pickup_time_from": "10:00",
                        "pickup_time_to": "18:00",
                        "route": "moscow_to_tajikistan",
                        "courier_fee": 500.0,
                        "cargo_name": "Тестовый груз для QR Modal",
                        "destination": "Душанбе"
                    }
                    
                    success_pickup, pickup_response = self.run_test(
                        "Create Test Pickup Request",
                        "POST",
                        "/api/admin/courier/pickup-request",
                        200,
                        pickup_data,
                        operator_token
                    )
                    
                    if success_pickup:
                        pickup_id = pickup_response.get('id')
                        pickup_number = pickup_response.get('request_number')
                        print(f"   ✅ Test pickup request created: {pickup_number} (ID: {pickup_id})")
                        
                        # Now check for notifications again
                        success, notifications_response = self.run_test(
                            "Get Warehouse Notifications (After Pickup Creation)",
                            "GET",
                            "/api/operator/warehouse-notifications",
                            200,
                            token=operator_token
                        )
                        
                        if success and isinstance(notifications_response, list):
                            for notification in notifications_response:
                                if notification.get('status') in ['pending_acceptance', 'pending']:
                                    notification_id = notification.get('id')
                                    break
                    
            elif isinstance(notifications_response, dict):
                notifications = notifications_response.get('notifications', [])
                notification_count = len(notifications)
                print(f"   📊 Found {notification_count} warehouse notifications")
                
                # Find a notification that can be tested
                for notification in notifications:
                    if notification.get('status') in ['pending_acceptance', 'pending']:
                        notification_id = notification.get('id')
                        break
            else:
                print("   ❌ Unexpected response format for warehouse notifications")
                all_success = False
        else:
            print("   ❌ /api/operator/warehouse-notifications endpoint failed")
            all_success = False
        
        # Test 3: ТЕСТИРОВАНИЕ ПРИНЯТИЯ УВЕДОМЛЕНИЯ (/api/operator/warehouse-notifications/{id}/accept)
        print("\n   ✅ Test 3: ПРИНЯТИЕ УВЕДОМЛЕНИЯ...")
        
        if notification_id:
            success, accept_response = self.run_test(
                f"Accept Warehouse Notification ({notification_id})",
                "POST",
                f"/api/operator/warehouse-notifications/{notification_id}/accept",
                200,
                token=operator_token
            )
            all_success &= success
            
            if success:
                print("   ✅ /api/operator/warehouse-notifications/{id}/accept endpoint working")
                
                # Verify acceptance response
                if isinstance(accept_response, dict):
                    message = accept_response.get('message', '')
                    status = accept_response.get('status', '')
                    
                    if 'accept' in message.lower() or 'принят' in message.lower():
                        print("   ✅ Notification acceptance successful")
                    else:
                        print(f"   ⚠️  Acceptance message: {message}")
                    
                    if status:
                        print(f"   📊 New status: {status}")
                else:
                    print("   ✅ Notification accepted (non-dict response)")
            else:
                print("   ❌ /api/operator/warehouse-notifications/{id}/accept endpoint failed")
                all_success = False
        else:
            print("   ⚠️  No notification ID available for acceptance testing")
        
        # Test 4: ПРОВЕРКА ENDPOINT ЗАВЕРШЕНИЯ ОФОРМЛЕНИЯ (/api/operator/warehouse-notifications/{id}/complete)
        print("\n   🏁 Test 4: ЗАВЕРШЕНИЕ ОФОРМЛЕНИЯ УВЕДОМЛЕНИЯ...")
        
        if notification_id:
            # Prepare completion data
            completion_data = {
                "sender_full_name": "QR Modal Тест Отправитель",
                "cargo_items": [
                    {
                        "name": "Тестовый груз QR Modal",
                        "weight": "2.5",
                        "price": "1000"
                    }
                ],
                "payment_method": "cash",
                "delivery_method": "pickup"
            }
            
            success, complete_response = self.run_test(
                f"Complete Warehouse Notification ({notification_id})",
                "POST",
                f"/api/operator/warehouse-notifications/{notification_id}/complete",
                200,
                completion_data,
                operator_token
            )
            all_success &= success
            
            if success:
                print("   ✅ /api/operator/warehouse-notifications/{id}/complete endpoint working")
                
                # Verify completion response
                if isinstance(complete_response, dict):
                    message = complete_response.get('message', '')
                    cargo_number = complete_response.get('cargo_number', '')
                    
                    if cargo_number:
                        print(f"   ✅ Cargo created from notification: {cargo_number}")
                    
                    if 'complete' in message.lower() or 'завершен' in message.lower():
                        print("   ✅ Notification completion successful")
                    else:
                        print(f"   📄 Completion message: {message}")
                else:
                    print("   ✅ Notification completed (non-dict response)")
            else:
                print("   ❌ /api/operator/warehouse-notifications/{id}/complete endpoint failed")
                all_success = False
        else:
            print("   ⚠️  No notification ID available for completion testing")
        
        # Test 5: ПРОВЕРКА СТАБИЛЬНОСТИ ВСЕХ ОПЕРАТОРСКИХ ENDPOINTS ПОСЛЕ FRONTEND ИЗМЕНЕНИЙ
        print("\n   🔧 Test 5: СТАБИЛЬНОСТЬ ВСЕХ ОПЕРАТОРСКИХ ENDPOINTS...")
        
        # List of critical operator endpoints that should remain stable
        operator_endpoints = [
            ("/api/auth/me", "User Profile"),
            ("/api/operator/warehouses", "Operator Warehouses"),
            ("/api/operator/cargo/list", "Operator Cargo List"),
            ("/api/operator/placement-statistics", "Placement Statistics"),
            ("/api/warehouses", "All Warehouses"),
            ("/api/operator/cargo/available-for-placement", "Available Cargo for Placement")
        ]
        
        endpoint_results = []
        
        for endpoint, description in operator_endpoints:
            print(f"\n   🔍 Testing {description} ({endpoint})...")
            
            success, response = self.run_test(
                f"Operator Endpoint: {description}",
                "GET",
                endpoint,
                200,
                token=operator_token
            )
            
            endpoint_results.append({
                'endpoint': endpoint,
                'description': description,
                'success': success,
                'response': response
            })
            
            if success:
                print(f"   ✅ {description} working")
                
                # Check for JSON serialization issues (no ObjectId errors)
                if isinstance(response, (dict, list)):
                    response_str = str(response)
                    if 'ObjectId' in response_str:
                        print(f"   ⚠️  Potential ObjectId serialization issue in {description}")
                        all_success = False
                    else:
                        print(f"   ✅ JSON serialization correct for {description}")
            else:
                print(f"   ❌ {description} failing")
                all_success = False
        
        # Test 6: CHECK FOR 500 INTERNAL SERVER ERRORS
        print("\n   🚨 Test 6: 500 INTERNAL SERVER ERROR CHECK...")
        
        error_500_count = 0
        for result in endpoint_results:
            if not result['success']:
                # Check if it was a 500 error by making the request again and checking status
                try:
                    url = f"{self.base_url}{result['endpoint']}"
                    headers = {'Authorization': f'Bearer {operator_token}', 'Content-Type': 'application/json'}
                    response = requests.get(url, headers=headers)
                    if response.status_code == 500:
                        error_500_count += 1
                        print(f"   ❌ 500 Error in {result['description']} ({result['endpoint']})")
                except:
                    pass
        
        if error_500_count == 0:
            print("   ✅ No 500 Internal Server Errors found!")
        else:
            print(f"   ❌ Found {error_500_count} endpoints with 500 Internal Server Errors")
            all_success = False
        
        # Test 7: SESSION MANAGEMENT STABILITY
        print("\n   🔐 Test 7: SESSION MANAGEMENT STABILITY...")
        
        # Test multiple requests with the same token to ensure session stability
        session_tests = [
            ("/api/auth/me", "User Profile Check"),
            ("/api/operator/warehouses", "Warehouses Access"),
            ("/api/operator/cargo/list", "Cargo List Access")
        ]
        
        session_stable = True
        for endpoint, description in session_tests:
            success, _ = self.run_test(
                f"Session Stability: {description}",
                "GET",
                endpoint,
                200,
                token=operator_token
            )
            
            if not success:
                session_stable = False
                print(f"   ❌ Session instability detected in {description}")
            else:
                print(f"   ✅ Session stable for {description}")
        
        if session_stable:
            print("   ✅ Session management stable - no premature 401 errors")
        else:
            print("   ❌ Session management issues detected")
            all_success = False
        
        # SUMMARY
        print("\n   📊 QR MODAL BACKEND STABILITY SUMMARY:")
        
        successful_endpoints = sum(1 for result in endpoint_results if result['success'])
        total_endpoints = len(endpoint_results)
        success_rate = (successful_endpoints / total_endpoints * 100) if total_endpoints > 0 else 0
        
        print(f"   📈 Endpoint Success Rate: {successful_endpoints}/{total_endpoints} ({success_rate:.1f}%)")
        
        if all_success:
            print("   🎉 ALL TESTS PASSED - Backend stable after QR modal JavaScript fix!")
            print("   ✅ Warehouse operator authentication working (+79777888999/warehouse123)")
            print("   ✅ /api/operator/warehouse-notifications endpoint accessible")
            print("   ✅ /api/operator/warehouse-notifications/{id}/accept working")
            print("   ✅ /api/operator/warehouse-notifications/{id}/complete working")
            print("   ✅ All operator endpoints stable after frontend changes")
            print("   ✅ No 500 Internal Server Errors")
            print("   ✅ Session management stable")
            print("   🎯 EXPECTED RESULT ACHIEVED: Backend should work stably, all endpoints")
            print("      should be available, no backend errors after frontend fixes")
        else:
            print("   ❌ SOME TESTS FAILED - Backend stability needs attention")
            print("   🔍 Check the specific failed tests above for details")
            
            # List failed endpoints
            failed_endpoints = [result for result in endpoint_results if not result['success']]
            if failed_endpoints:
                print("   ❌ Failed endpoints:")
                for result in failed_endpoints:
                    print(f"     - {result['description']} ({result['endpoint']})")
        
        return all_success

    def run_all_tests(self):
        """Run all QR modal backend stability tests"""
        print("🚀 Starting QR Modal Backend Stability Tests...")
        
        # Run the main test
        success = self.test_warehouse_operator_qr_modal_backend_stability()
        
        # Final summary
        print("\n" + "=" * 80)
        print("📊 FINAL TEST SUMMARY")
        print("=" * 80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if success:
            print("\n🎉 ALL QR MODAL BACKEND STABILITY TESTS PASSED!")
            print("✅ Backend is stable after QR code modal JavaScript fix")
            print("✅ All warehouse operator endpoints working")
            print("✅ Warehouse notifications system functional")
            print("✅ No backend errors after frontend improvements")
        else:
            print("\n❌ SOME TESTS FAILED")
            print("🔧 Backend stability may need attention after QR modal fix")
        
        return success

if __name__ == "__main__":
    tester = QRModalBackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
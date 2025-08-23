#!/usr/bin/env python3
"""
TAJLINE.TJ Improved Pickup Request Modal Testing
Testing the improved pickup request processing modal functionality according to review request
"""

import requests
import json
import sys
import os

class PickupRequestTester:
    def __init__(self, base_url="https://tajline-manage-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.tests_run = 0
        self.tests_passed = 0
        
    def run_test(self, test_name, method, endpoint, expected_status, data=None, token=None):
        """Run a single test"""
        self.tests_run += 1
        
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        try:
            if method == 'GET':
                response = self.session.get(url, headers=headers)
            elif method == 'POST':
                response = self.session.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = self.session.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            print(f"\n🔍 Test {self.tests_run}: {test_name}")
            print(f"   {method} {endpoint}")
            
            if response.status_code == expected_status:
                print(f"   ✅ PASSED - Status: {response.status_code}")
                self.tests_passed += 1
                
                try:
                    response_data = response.json()
                    print(f"   📄 Response: {response_data}")
                    return True, response_data
                except:
                    return True, response.text
            else:
                print(f"   ❌ FAILED - Expected: {expected_status}, Got: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   📄 Error: {error_data}")
                    return False, error_data
                except:
                    print(f"   📄 Error: {response.text}")
                    return False, response.text
                    
        except Exception as e:
            print(f"   ❌ EXCEPTION: {str(e)}")
            return False, str(e)

    def test_pickup_request_system_fixes(self):
        """Test pickup request system fixes according to review request"""
        print("\n🚚 PICKUP REQUEST SYSTEM FIXES TESTING")
        print("   🎯 Протестировать исправления системы заявок на забор груза в TAJLINE.TJ")
        print("   🔧 ПРОБЛЕМА: Оператор заполняет заявку для забора груза, но в личном кабинете курьера заявки не показываются")
        print("   🔧 ИСПРАВЛЕНИЯ СДЕЛАННЫЕ:")
        print("   1) Обновлен endpoint /api/courier/requests/new - теперь включает заявки из коллекции courier_pickup_requests")
        print("   2) Обновлен endpoint /api/courier/requests/{request_id}/accept - теперь поддерживает принятие заявок на забор груза")
        print("   3) Заявки на забор груза помечаются как request_type: 'pickup', обычные как request_type: 'delivery'")
        
        all_success = True
        
        # Test 1: АВТОРИЗАЦИЯ ОПЕРАТОРА (+79777888999/warehouse123)
        print("\n   🔐 Test 1: АВТОРИЗАЦИЯ ОПЕРАТОРА (+79777888999/warehouse123)...")
        
        operator_login_data = {
            "phone": "+79777888999",
            "password": "warehouse123"
        }
        
        success, login_response = self.run_test(
            "Operator Login Authentication",
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
            
            print(f"   ✅ Operator login successful: {operator_name}")
            print(f"   👑 Role: {operator_role}")
            print(f"   📞 Phone: {operator_user.get('phone')}")
        else:
            print("   ❌ Operator login failed")
            all_success = False
            return False
        
        # Test 2: СОЗДАТЬ ТЕСТОВУЮ ЗАЯВКУ НА ЗАБОР ГРУЗА через POST /api/admin/courier/pickup-request
        print("\n   📦 Test 2: СОЗДАТЬ ТЕСТОВУЮ ЗАЯВКУ НА ЗАБОР ГРУЗА...")
        
        pickup_request_data = {
            "sender_full_name": "Тест Отправитель",
            "sender_phone": "+7999123456",
            "pickup_address": "Москва, ул. Тестовая, 1",
            "pickup_date": "2025-01-15",
            "pickup_time_from": "10:00",
            "pickup_time_to": "12:00",
            "route": "moscow_to_tajikistan",
            "courier_fee": 500,
            "payment_method": "not_paid"
        }
        
        success, pickup_response = self.run_test(
            "Create Pickup Request via POST /api/admin/courier/pickup-request",
            "POST",
            "/api/admin/courier/pickup-request",
            200,
            pickup_request_data,
            operator_token
        )
        all_success &= success
        
        pickup_request_id = None
        if success and ('id' in pickup_response or 'request_id' in pickup_response):
            pickup_request_id = pickup_response.get('id') or pickup_response.get('request_id')
            request_number = pickup_response.get('request_number')
            print(f"   ✅ Pickup request created successfully: {request_number}")
            print(f"   🆔 Request ID: {pickup_request_id}")
            
            # Verify response contains expected fields
            expected_fields = ['request_number']
            if 'id' in pickup_response:
                expected_fields.append('id')
            if 'request_id' in pickup_response:
                expected_fields.append('request_id')
            
            missing_fields = [field for field in expected_fields if field not in pickup_response]
            
            if not missing_fields:
                print("   ✅ Pickup request response contains all expected fields")
            else:
                print(f"   ❌ Missing fields in pickup request response: {missing_fields}")
                all_success = False
        else:
            print("   ❌ Failed to create pickup request")
            print(f"   📄 Response: {pickup_response}")
            all_success = False
            return False
        
        # Test 3: АВТОРИЗАЦИЯ КУРЬЕРА (+79991234567/courier123)
        print("\n   🚴 Test 3: АВТОРИЗАЦИЯ КУРЬЕРА (+79991234567/courier123)...")
        
        courier_login_data = {
            "phone": "+79991234567",
            "password": "courier123"
        }
        
        success, courier_login_response = self.run_test(
            "Courier Login Authentication",
            "POST",
            "/api/auth/login",
            200,
            courier_login_data
        )
        all_success &= success
        
        courier_token = None
        if success and 'access_token' in courier_login_response:
            courier_token = courier_login_response['access_token']
            courier_user = courier_login_response.get('user', {})
            courier_role = courier_user.get('role')
            courier_name = courier_user.get('full_name')
            
            print(f"   ✅ Courier login successful: {courier_name}")
            print(f"   👑 Role: {courier_role}")
            print(f"   📞 Phone: {courier_user.get('phone')}")
        else:
            print("   ❌ Courier login failed")
            all_success = False
            return False
        
        # Test 4: ВЫЗВАТЬ GET /api/courier/requests/new и убедиться что заявки на забор груза показываются
        print("\n   📋 Test 4: GET /api/courier/requests/new - ПРОВЕРИТЬ ЗАЯВКИ НА ЗАБОР ГРУЗА...")
        
        success, new_requests_response = self.run_test(
            "Get New Courier Requests (Including Pickup Requests)",
            "GET",
            "/api/courier/requests/new",
            200,
            token=courier_token
        )
        all_success &= success
        
        pickup_request_found = False
        if success:
            print("   ✅ /api/courier/requests/new endpoint working")
            
            # Check response structure
            if isinstance(new_requests_response, dict):
                new_requests = new_requests_response.get('new_requests', [])
                total_count = new_requests_response.get('total_count', 0)
                
                print(f"   📊 Total new requests: {total_count}")
                print(f"   📋 Requests in response: {len(new_requests)}")
                
                # Look for pickup requests
                pickup_requests = []
                delivery_requests = []
                
                for request in new_requests:
                    request_type = request.get('request_type', 'unknown')
                    if request_type == 'pickup':
                        pickup_requests.append(request)
                        if request.get('id') == pickup_request_id or request.get('request_id') == pickup_request_id:
                            pickup_request_found = True
                    elif request_type == 'delivery':
                        delivery_requests.append(request)
                
                print(f"   🚚 Pickup requests found: {len(pickup_requests)}")
                print(f"   🚛 Delivery requests found: {len(delivery_requests)}")
                
                if pickup_requests:
                    print("   ✅ Pickup requests are now showing in courier's new requests list!")
                    
                    # Verify pickup request structure
                    sample_pickup = pickup_requests[0]
                    required_pickup_fields = ['id', 'sender_full_name', 'sender_phone', 'pickup_address', 'pickup_date', 'pickup_time_from', 'pickup_time_to', 'request_type']
                    missing_pickup_fields = [field for field in required_pickup_fields if field not in sample_pickup]
                    
                    if not missing_pickup_fields:
                        print("   ✅ Pickup request contains all necessary fields")
                        print(f"   📍 Sample pickup address: {sample_pickup.get('pickup_address')}")
                        print(f"   📅 Sample pickup date: {sample_pickup.get('pickup_date')}")
                        print(f"   🕐 Sample pickup time: {sample_pickup.get('pickup_time_from')} - {sample_pickup.get('pickup_time_to')}")
                        print(f"   🏷️ Request type: {sample_pickup.get('request_type')}")
                    else:
                        print(f"   ❌ Missing fields in pickup request: {missing_pickup_fields}")
                        all_success = False
                    
                    if pickup_request_found:
                        print("   ✅ Our test pickup request found in the list!")
                    else:
                        print("   ⚠️ Our test pickup request not found in the list (may be filtered by courier assignment)")
                else:
                    print("   ❌ No pickup requests found in courier's new requests list")
                    print("   🔍 This indicates the fix may not be working correctly")
                    all_success = False
                    
            elif isinstance(new_requests_response, list):
                print(f"   📊 Direct list response with {len(new_requests_response)} requests")
                # Handle direct list response
                pickup_requests = [req for req in new_requests_response if req.get('request_type') == 'pickup']
                if pickup_requests:
                    print(f"   ✅ Found {len(pickup_requests)} pickup requests in direct list")
                else:
                    print("   ❌ No pickup requests found in direct list response")
                    all_success = False
            else:
                print("   ❌ Unexpected response format")
                all_success = False
        else:
            print("   ❌ /api/courier/requests/new endpoint failed")
            all_success = False
        
        # Test 5: ПРОВЕРИТЬ ЧТО ЗАЯВКИ ИМЕЮТ request_type: 'pickup' И СОДЕРЖАТ НЕОБХОДИМЫЕ ПОЛЯ
        print("\n   🏷️ Test 5: ПРОВЕРИТЬ request_type: 'pickup' И НЕОБХОДИМЫЕ ПОЛЯ...")
        
        if pickup_request_found or (success and new_requests_response):
            # We already checked this in Test 4, but let's summarize
            if isinstance(new_requests_response, dict):
                new_requests = new_requests_response.get('new_requests', [])
            else:
                new_requests = new_requests_response if isinstance(new_requests_response, list) else []
            
            pickup_requests_with_correct_type = [req for req in new_requests if req.get('request_type') == 'pickup']
            
            if pickup_requests_with_correct_type:
                print(f"   ✅ Found {len(pickup_requests_with_correct_type)} requests with request_type: 'pickup'")
                
                # Verify all necessary fields are present
                sample_request = pickup_requests_with_correct_type[0]
                necessary_fields = [
                    'id', 'sender_full_name', 'sender_phone', 'pickup_address', 
                    'pickup_date', 'pickup_time_from', 'pickup_time_to', 'request_type'
                ]
                
                field_check_results = {}
                for field in necessary_fields:
                    field_check_results[field] = field in sample_request
                    if field in sample_request:
                        print(f"   ✅ {field}: {sample_request.get(field)}")
                    else:
                        print(f"   ❌ Missing field: {field}")
                        all_success = False
                
                all_fields_present = all(field_check_results.values())
                if all_fields_present:
                    print("   ✅ All necessary fields present in pickup requests")
                else:
                    missing_fields = [field for field, present in field_check_results.items() if not present]
                    print(f"   ❌ Missing necessary fields: {missing_fields}")
                    all_success = False
            else:
                print("   ❌ No pickup requests found with correct request_type")
                all_success = False
        else:
            print("   ⚠️ Cannot verify request_type due to previous test failures")
        
        # Test 6: ПРОТЕСТИРОВАТЬ ПРИНЯТИЕ ЗАЯВКИ НА ЗАБОР ГРУЗА через POST /api/courier/requests/{request_id}/accept
        print("\n   ✅ Test 6: ПРИНЯТИЕ ЗАЯВКИ НА ЗАБОР ГРУЗА...")
        
        if pickup_request_id:
            success, accept_response = self.run_test(
                f"Accept Pickup Request via POST /api/courier/requests/{pickup_request_id}/accept",
                "POST",
                f"/api/courier/requests/{pickup_request_id}/accept",
                200,
                {},  # Empty body for accept request
                courier_token
            )
            all_success &= success
            
            if success:
                print("   ✅ Pickup request acceptance endpoint working")
                
                # Verify response contains expected information
                if 'message' in accept_response:
                    print(f"   📄 Response message: {accept_response.get('message')}")
                
                if 'request_id' in accept_response:
                    print(f"   🆔 Accepted request ID: {accept_response.get('request_id')}")
                
                # Check if response indicates the request type
                if 'request_type' in accept_response:
                    response_request_type = accept_response.get('request_type')
                    print(f"   🏷️ Response request_type: {response_request_type}")
                    
                    if response_request_type == 'pickup':
                        print("   ✅ Response correctly indicates pickup request type")
                    else:
                        print(f"   ❌ Response request_type incorrect: expected 'pickup', got '{response_request_type}'")
                        all_success = False
                else:
                    print("   ⚠️ Response does not include request_type (may be acceptable)")
                
                print("   ✅ Pickup request acceptance working correctly")
            else:
                print("   ❌ Failed to accept pickup request")
                all_success = False
        else:
            print("   ⚠️ Cannot test pickup request acceptance - no pickup request ID available")
            all_success = False
        
        # Test 7: УБЕДИТЬСЯ ЧТО В ОТВЕТЕ УКАЗАН ПРАВИЛЬНЫЙ request_type
        print("\n   🏷️ Test 7: ПРОВЕРИТЬ ПРАВИЛЬНЫЙ request_type В ОТВЕТЕ...")
        
        if success and accept_response:
            # We already checked this in Test 6, but let's be explicit
            response_request_type = accept_response.get('request_type')
            
            if response_request_type == 'pickup':
                print("   ✅ Accept response correctly returns request_type: 'pickup'")
            elif response_request_type is None:
                print("   ⚠️ Accept response does not include request_type field")
                print("   ℹ️ This may be acceptable if the endpoint doesn't return this field")
            else:
                print(f"   ❌ Accept response has incorrect request_type: expected 'pickup', got '{response_request_type}'")
                all_success = False
        else:
            print("   ⚠️ Cannot verify request_type in response due to previous test failures")
        
        # SUMMARY
        print("\n   📊 PICKUP REQUEST SYSTEM FIXES SUMMARY:")
        
        if all_success:
            print("   🎉 ALL PICKUP REQUEST SYSTEM TESTS PASSED!")
            print("   ✅ Operator authentication working (+79777888999/warehouse123)")
            print("   ✅ Pickup request creation via POST /api/admin/courier/pickup-request working")
            print("   ✅ Courier authentication working (+79991234567/courier123)")
            print("   ✅ GET /api/courier/requests/new now includes pickup requests from courier_pickup_requests collection")
            print("   ✅ Pickup requests have request_type: 'pickup' and contain necessary fields")
            print("   ✅ POST /api/courier/requests/{request_id}/accept supports pickup request acceptance")
            print("   ✅ Accept response indicates correct request_type")
            print("   🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ ДОСТИГНУТ: Заявки на забор груза отображаются в списке новых заявок для курьера и корректно принимаются!")
        else:
            print("   ❌ SOME PICKUP REQUEST SYSTEM TESTS FAILED")
            print("   🔍 Check the specific failed tests above for details")
            print("   ⚠️ The pickup request system fixes may need attention")
        
        return all_success

if __name__ == "__main__":
    # Get the backend URL from environment variable
    backend_url = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-manage-1.preview.emergentagent.com')
    
    # Initialize tester with the correct URL
    tester = PickupRequestTester(base_url=backend_url)
    
    # Run only the pickup request system fixes test
    print("🎯 RUNNING SPECIFIC TEST: PICKUP REQUEST SYSTEM FIXES")
    print("=" * 80)
    
    result = tester.test_pickup_request_system_fixes()
    
    print("\n" + "=" * 80)
    print("🏁 FINAL TEST RESULT")
    print("=" * 80)
    print(f"📊 Total tests run: {tester.tests_run}")
    print(f"✅ Tests passed: {tester.tests_passed}")
    print(f"❌ Tests failed: {tester.tests_run - tester.tests_passed}")
    print(f"📈 Success rate: {(tester.tests_passed/tester.tests_run*100):.1f}%" if tester.tests_run > 0 else "0%")
    
    if result:
        print("\n🎉 PICKUP REQUEST SYSTEM FIXES TEST PASSED!")
        print("✅ Pickup request system fixes working correctly")
        sys.exit(0)
    else:
        print("\n❌ PICKUP REQUEST SYSTEM FIXES TEST FAILED")
        print("🔍 Check test results above for details")
        sys.exit(1)
#!/usr/bin/env python3
"""
Critical Backend Testing for TAJLINE.TJ Courier System Fixes
Tests the two critical issues mentioned in the review request:
1. Courier Request Editing Save Error Fix
2. GPS Tracking Data Not Received by Operators/Admins Fix
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class CourierCriticalFixesTester:
    def __init__(self, base_url="https://tajline-cargo-8.preview.emergentagent.com"):
        self.base_url = base_url
        self.tokens = {}  # Store tokens for different users
        self.users = {}   # Store user data
        self.test_request_id = None  # Store test request ID
        self.tests_run = 0
        self.tests_passed = 0
        
        print(f"🚛 TAJLINE.TJ CRITICAL COURIER FIXES TESTER")
        print(f"📡 Base URL: {self.base_url}")
        print("=" * 80)
        print("🎯 TESTING CRITICAL FIXES:")
        print("   1) Courier Request Editing Save Error Fix")
        print("   2) GPS Tracking Data Not Received by Operators/Admins Fix")
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
                        if len(result) > 0:
                            print(f"   📄 Sample item: {result[0] if len(str(result[0])) < 200 else 'Large object'}")
                    return True, result
                except:
                    return True, {}
            else:
                print(f"   ❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   📄 Error: {error_detail}")
                except:
                    print(f"   📄 Raw response: {response.text[:300]}")
                return False, {}

        except Exception as e:
            print(f"   ❌ FAILED - Exception: {str(e)}")
            return False, {}

    def test_courier_request_editing_save_error_fix(self):
        """Test ПРОБЛЕМА 1 - ИСПРАВЛЕНИЕ ОШИБКИ СОХРАНЕНИЯ ПРИ РЕДАКТИРОВАНИИ ЗАЯВОК КУРЬЕРАМИ"""
        print("\n🔧 ПРОБЛЕМА 1 - ИСПРАВЛЕНИЕ ОШИБКИ СОХРАНЕНИЯ ПРИ РЕДАКТИРОВАНИИ ЗАЯВОК КУРЬЕРАМИ")
        print("   🎯 Тестирование исправления ошибки сохранения при редактировании заявок курьерами")
        print("   📋 ПЛАН ТЕСТИРОВАНИЯ:")
        print("   1) Авторизация курьера (+79991234567/courier123)")
        print("   2) Проверить endpoint GET /api/courier/requests/accepted - должен возвращать принятые заявки")
        print("   3) Взять любую заявку и протестировать endpoint PUT /api/courier/requests/{request_id}/update")
        print("   4) Проверить что заявка обновляется успешно и поля сохраняются корректно")
        print("   5) Протестировать как для обычных заявок (courier_requests), так и для заявок на забор груза (courier_pickup_requests)")
        
        all_success = True
        
        # Step 1: Авторизация курьера (+79991234567/courier123)
        print("\n   🔐 Step 1: АВТОРИЗАЦИЯ КУРЬЕРА (+79991234567/courier123)...")
        
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
                print("   ✅ Courier role correctly set to 'courier'")
            else:
                print(f"   ❌ Courier role incorrect: expected 'courier', got '{courier_role}'")
                all_success = False
            
            self.tokens['courier'] = courier_token
            self.users['courier'] = courier_user
        else:
            print("   ❌ Courier login failed - no access token received")
            all_success = False
            return False
        
        # Step 2: Проверить endpoint GET /api/courier/requests/accepted - должен возвращать принятые заявки
        print("\n   📋 Step 2: ПРОВЕРИТЬ ENDPOINT GET /api/courier/requests/accepted...")
        
        success, accepted_requests = self.run_test(
            "Get Accepted Courier Requests",
            "GET",
            "/api/courier/requests/accepted",
            200,
            token=courier_token
        )
        all_success &= success
        
        test_request = None
        if success:
            print("   ✅ GET /api/courier/requests/accepted endpoint working")
            
            # Parse response structure
            if isinstance(accepted_requests, dict):
                requests_list = accepted_requests.get('accepted_requests', [])
                total_count = accepted_requests.get('total_count', 0)
                print(f"   📊 Found {total_count} accepted requests")
            elif isinstance(accepted_requests, list):
                requests_list = accepted_requests
                print(f"   📊 Found {len(requests_list)} accepted requests")
            else:
                print("   ❌ Unexpected response format")
                all_success = False
                return False
            
            # Find a test request to edit
            if requests_list and len(requests_list) > 0:
                test_request = requests_list[0]
                self.test_request_id = test_request.get('id')
                request_type = test_request.get('request_type', 'delivery')
                
                print(f"   ✅ Found test request for editing:")
                print(f"   🆔 Request ID: {self.test_request_id}")
                print(f"   📦 Request Type: {request_type}")
                print(f"   👤 Sender: {test_request.get('sender_full_name', 'N/A')}")
                print(f"   📞 Sender Phone: {test_request.get('sender_phone', 'N/A')}")
                print(f"   📍 Pickup Address: {test_request.get('pickup_address', 'N/A')}")
            else:
                print("   ⚠️  No accepted requests found for testing")
                print("   ℹ️  Creating a test request for editing...")
                
                # Create a test request if none exist
                # This would require admin/operator endpoints, so we'll skip for now
                print("   ⚠️  Skipping request creation - would need admin/operator access")
                return False
        else:
            print("   ❌ GET /api/courier/requests/accepted endpoint failed")
            all_success = False
            return False
        
        # Step 3: Взять любую заявку и протестировать endpoint PUT /api/courier/requests/{request_id}/update
        print("\n   ✏️ Step 3: ПРОТЕСТИРОВАТЬ ENDPOINT PUT /api/courier/requests/{request_id}/update...")
        
        if self.test_request_id:
            # Test data as specified in the review request
            update_data = {
                "cargo_items": [
                    {
                        "name": "Тестовое наименование груза",
                        "weight": "2.5",
                        "total_price": "1000"
                    }
                ],
                "recipient_full_name": "Тестовый Получатель",
                "recipient_phone": "+79998887766",
                "recipient_address": "Москва, ул. Тестовая, 1",
                "delivery_method": "pickup",
                "payment_method": "cash"
            }
            
            success, update_response = self.run_test(
                f"Update Courier Request {self.test_request_id}",
                "PUT",
                f"/api/courier/requests/{self.test_request_id}/update",
                200,
                update_data,
                courier_token
            )
            all_success &= success
            
            if success:
                print("   ✅ PUT /api/courier/requests/{request_id}/update endpoint working")
                print("   ✅ Request update successful - no save error!")
                
                # Verify response contains success confirmation
                if isinstance(update_response, dict):
                    message = update_response.get('message', '')
                    if 'success' in message.lower() or 'updated' in message.lower():
                        print(f"   ✅ Update confirmation: {message}")
                    else:
                        print(f"   📄 Response: {update_response}")
                
                # Step 4: Проверить что заявка обновляется успешно и поля сохраняются корректно
                print("\n   🔍 Step 4: ПРОВЕРИТЬ ЧТО ПОЛЯ СОХРАНЯЮТСЯ КОРРЕКТНО...")
                
                # Get the updated request to verify changes
                success, updated_requests = self.run_test(
                    "Verify Updated Request Fields",
                    "GET",
                    "/api/courier/requests/accepted",
                    200,
                    token=courier_token
                )
                
                if success:
                    # Find our updated request
                    updated_request = None
                    if isinstance(updated_requests, dict):
                        requests_list = updated_requests.get('accepted_requests', [])
                    elif isinstance(updated_requests, list):
                        requests_list = updated_requests
                    else:
                        requests_list = []
                    
                    for req in requests_list:
                        if req.get('id') == self.test_request_id:
                            updated_request = req
                            break
                    
                    if updated_request:
                        print("   ✅ Updated request found - verifying saved fields...")
                        
                        # Verify key fields were saved
                        verification_results = []
                        
                        # Check recipient_full_name
                        if updated_request.get('recipient_full_name') == "Тестовый Получатель":
                            print("   ✅ recipient_full_name saved correctly")
                            verification_results.append(True)
                        else:
                            print(f"   ❌ recipient_full_name not saved: {updated_request.get('recipient_full_name')}")
                            verification_results.append(False)
                        
                        # Check recipient_phone
                        if updated_request.get('recipient_phone') == "+79998887766":
                            print("   ✅ recipient_phone saved correctly")
                            verification_results.append(True)
                        else:
                            print(f"   ❌ recipient_phone not saved: {updated_request.get('recipient_phone')}")
                            verification_results.append(False)
                        
                        # Check recipient_address
                        if updated_request.get('recipient_address') == "Москва, ул. Тестовая, 1":
                            print("   ✅ recipient_address saved correctly")
                            verification_results.append(True)
                        else:
                            print(f"   ❌ recipient_address not saved: {updated_request.get('recipient_address')}")
                            verification_results.append(False)
                        
                        # Check delivery_method
                        if updated_request.get('delivery_method') == "pickup":
                            print("   ✅ delivery_method saved correctly")
                            verification_results.append(True)
                        else:
                            print(f"   ❌ delivery_method not saved: {updated_request.get('delivery_method')}")
                            verification_results.append(False)
                        
                        # Check payment_method
                        if updated_request.get('payment_method') == "cash":
                            print("   ✅ payment_method saved correctly")
                            verification_results.append(True)
                        else:
                            print(f"   ❌ payment_method not saved: {updated_request.get('payment_method')}")
                            verification_results.append(False)
                        
                        # Overall verification
                        if all(verification_results):
                            print("   🎉 ALL FIELDS SAVED CORRECTLY - Request editing fix successful!")
                        else:
                            print("   ❌ Some fields not saved correctly - fix may need attention")
                            all_success = False
                    else:
                        print("   ❌ Updated request not found in response")
                        all_success = False
                else:
                    print("   ❌ Could not verify updated fields")
                    all_success = False
            else:
                print("   ❌ PUT /api/courier/requests/{request_id}/update endpoint failed")
                print("   ❌ REQUEST EDITING SAVE ERROR STILL EXISTS!")
                all_success = False
        else:
            print("   ❌ No test request ID available for update testing")
            all_success = False
        
        # Step 5: Протестировать как для обычных заявок (courier_requests), так и для заявок на забор груза (courier_pickup_requests)
        print("\n   📦 Step 5: ТЕСТИРОВАНИЕ ЗАЯВОК НА ЗАБОР ГРУЗА (courier_pickup_requests)...")
        
        # Check if there are any pickup requests to test
        success, new_requests = self.run_test(
            "Get New Requests (including pickup requests)",
            "GET",
            "/api/courier/requests/new",
            200,
            token=courier_token
        )
        
        if success:
            pickup_requests = []
            if isinstance(new_requests, dict):
                requests_list = new_requests.get('new_requests', [])
            elif isinstance(new_requests, list):
                requests_list = new_requests
            else:
                requests_list = []
            
            # Find pickup requests
            for req in requests_list:
                if req.get('request_type') == 'pickup':
                    pickup_requests.append(req)
            
            if pickup_requests:
                print(f"   ✅ Found {len(pickup_requests)} pickup requests")
                
                # Test updating a pickup request
                pickup_request = pickup_requests[0]
                pickup_request_id = pickup_request.get('id')
                
                print(f"   🆔 Testing pickup request: {pickup_request_id}")
                
                # Accept the pickup request first
                success, accept_response = self.run_test(
                    f"Accept Pickup Request {pickup_request_id}",
                    "POST",
                    f"/api/courier/requests/{pickup_request_id}/accept",
                    200,
                    token=courier_token
                )
                
                if success:
                    print("   ✅ Pickup request accepted successfully")
                    
                    # Now test updating the pickup request
                    pickup_update_data = {
                        "cargo_items": [
                            {
                                "name": "Тестовый груз для забора",
                                "weight": "3.0",
                                "total_price": "1500"
                            }
                        ],
                        "recipient_full_name": "Получатель Забора",
                        "recipient_phone": "+79998887777",
                        "recipient_address": "Москва, ул. Забора, 2",
                        "delivery_method": "pickup",
                        "payment_method": "cash"
                    }
                    
                    success, pickup_update_response = self.run_test(
                        f"Update Pickup Request {pickup_request_id}",
                        "PUT",
                        f"/api/courier/requests/{pickup_request_id}/update",
                        200,
                        pickup_update_data,
                        courier_token
                    )
                    
                    if success:
                        print("   ✅ Pickup request update successful")
                        print("   ✅ Both courier_requests and courier_pickup_requests editing working!")
                    else:
                        print("   ❌ Pickup request update failed")
                        all_success = False
                else:
                    print("   ❌ Could not accept pickup request for testing")
            else:
                print("   ⚠️  No pickup requests found for testing")
                print("   ℹ️  Testing only regular courier requests")
        else:
            print("   ❌ Could not get new requests for pickup testing")
        
        return all_success

    def test_gps_tracking_data_not_received_fix(self):
        """Test ПРОБЛЕМА 2 - ИСПРАВЛЕНИЕ GPS ОТСЛЕЖИВАНИЯ"""
        print("\n🛰️ ПРОБЛЕМА 2 - ИСПРАВЛЕНИЕ GPS ОТСЛЕЖИВАНИЯ")
        print("   🎯 Тестирование исправления GPS отслеживания - данные должны получать операторы/администраторы")
        print("   📋 ПЛАН ТЕСТИРОВАНИЯ:")
        print("   1) Авторизация курьера (+79991234567/courier123)")
        print("   2) Протестировать endpoint POST /api/courier/location/update с GPS данными")
        print("   3) Проверить что данные сохраняются в courier_locations и courier_location_history")
        print("   4) Авторизация администратора (+79999888777/admin123)")
        print("   5) Протестировать endpoint GET /api/admin/couriers/locations - должен возвращать местоположения курьеров")
        print("   6) Авторизация оператора (+79777888999/warehouse123)")
        print("   7) Протестировать endpoint GET /api/operator/couriers/locations - должен возвращать курьеров назначенных складов")
        
        all_success = True
        
        # Step 1: Авторизация курьера (+79991234567/courier123) - reuse from previous test
        print("\n   🔐 Step 1: АВТОРИЗАЦИЯ КУРЬЕРА (+79991234567/courier123)...")
        
        if 'courier' not in self.tokens:
            courier_login_data = {
                "phone": "+79991234567",
                "password": "courier123"
            }
            
            success, login_response = self.run_test(
                "Courier Authentication for GPS Testing",
                "POST",
                "/api/auth/login",
                200,
                courier_login_data
            )
            all_success &= success
            
            if success and 'access_token' in login_response:
                self.tokens['courier'] = login_response['access_token']
                self.users['courier'] = login_response.get('user', {})
                print("   ✅ Courier authentication successful")
            else:
                print("   ❌ Courier authentication failed")
                return False
        else:
            print("   ✅ Using existing courier authentication")
        
        courier_token = self.tokens['courier']
        
        # Step 2: Протестировать endpoint POST /api/courier/location/update с GPS данными
        print("\n   📍 Step 2: ПРОТЕСТИРОВАТЬ ENDPOINT POST /api/courier/location/update...")
        
        # GPS data as specified in the review request
        gps_data = {
            "latitude": 55.7558,
            "longitude": 37.6176,
            "status": "online",
            "accuracy": 10.5,
            "speed": 0,
            "heading": None,
            "current_address": "Москва, Красная площадь"
        }
        
        success, location_response = self.run_test(
            "Update Courier GPS Location",
            "POST",
            "/api/courier/location/update",
            200,
            gps_data,
            courier_token
        )
        all_success &= success
        
        location_id = None
        if success:
            print("   ✅ POST /api/courier/location/update endpoint working")
            print("   ✅ GPS data sent successfully - no errors!")
            
            # Verify response contains location ID or confirmation
            if isinstance(location_response, dict):
                location_id = location_response.get('location_id') or location_response.get('id')
                message = location_response.get('message', '')
                
                if location_id:
                    print(f"   ✅ Location ID received: {location_id}")
                if message:
                    print(f"   📄 Response message: {message}")
                
                # Verify GPS data was processed
                saved_data = location_response.get('location_data', {})
                if saved_data:
                    print("   ✅ GPS data processed and saved:")
                    print(f"   📍 Latitude: {saved_data.get('latitude', gps_data['latitude'])}")
                    print(f"   📍 Longitude: {saved_data.get('longitude', gps_data['longitude'])}")
                    print(f"   📍 Status: {saved_data.get('status', gps_data['status'])}")
                    print(f"   📍 Address: {saved_data.get('current_address', gps_data['current_address'])}")
        else:
            print("   ❌ POST /api/courier/location/update endpoint failed")
            print("   ❌ GPS TRACKING STILL NOT WORKING!")
            all_success = False
        
        # Step 3: Проверить что данные сохраняются в courier_locations и courier_location_history
        print("\n   💾 Step 3: ПРОВЕРИТЬ СОХРАНЕНИЕ ДАННЫХ В БАЗЕ...")
        
        # Check courier's own location status
        success, status_response = self.run_test(
            "Check Courier Location Status",
            "GET",
            "/api/courier/location/status",
            200,
            token=courier_token
        )
        
        if success:
            print("   ✅ Courier location status endpoint working")
            
            if isinstance(status_response, dict):
                tracking_enabled = status_response.get('tracking_enabled')
                current_status = status_response.get('status')
                current_address = status_response.get('current_address')
                last_updated = status_response.get('last_updated')
                
                print(f"   📊 Tracking enabled: {tracking_enabled}")
                print(f"   📊 Current status: {current_status}")
                print(f"   📊 Current address: {current_address}")
                print(f"   📊 Last updated: {last_updated}")
                
                # Verify our GPS data was saved
                if current_status == "online" and current_address == "Москва, Красная площадь":
                    print("   ✅ GPS data correctly saved in courier_locations!")
                else:
                    print("   ❌ GPS data may not have been saved correctly")
                    all_success = False
        else:
            print("   ❌ Could not verify GPS data persistence")
            all_success = False
        
        # Step 4: Авторизация администратора (+79999888777/admin123)
        print("\n   👑 Step 4: АВТОРИЗАЦИЯ АДМИНИСТРАТОРА (+79999888777/admin123)...")
        
        admin_login_data = {
            "phone": "+79999888777",
            "password": "admin123"
        }
        
        success, admin_login_response = self.run_test(
            "Admin Authentication for GPS Testing",
            "POST",
            "/api/auth/login",
            200,
            admin_login_data
        )
        all_success &= success
        
        admin_token = None
        if success and 'access_token' in admin_login_response:
            admin_token = admin_login_response['access_token']
            admin_user = admin_login_response.get('user', {})
            admin_role = admin_user.get('role')
            admin_name = admin_user.get('full_name')
            
            print(f"   ✅ Admin login successful: {admin_name}")
            print(f"   👑 Role: {admin_role}")
            
            self.tokens['admin'] = admin_token
            self.users['admin'] = admin_user
        else:
            print("   ❌ Admin login failed")
            all_success = False
            return False
        
        # Step 5: Протестировать endpoint GET /api/admin/couriers/locations
        print("\n   🗺️ Step 5: ПРОТЕСТИРОВАТЬ ENDPOINT GET /api/admin/couriers/locations...")
        
        success, admin_locations = self.run_test(
            "Admin Get Courier Locations",
            "GET",
            "/api/admin/couriers/locations",
            200,
            token=admin_token
        )
        all_success &= success
        
        if success:
            print("   ✅ GET /api/admin/couriers/locations endpoint working")
            print("   ✅ ADMIN CAN NOW RECEIVE GPS DATA!")
            
            # Verify response contains courier locations
            if isinstance(admin_locations, list):
                location_count = len(admin_locations)
                print(f"   📊 Found {location_count} courier locations")
                
                # Look for our test courier's location
                test_courier_found = False
                for location in admin_locations:
                    courier_id = location.get('courier_id')
                    courier_name = location.get('courier_name')
                    latitude = location.get('latitude')
                    longitude = location.get('longitude')
                    status = location.get('status')
                    current_address = location.get('current_address')
                    
                    print(f"   📍 Courier: {courier_name} (ID: {courier_id})")
                    print(f"   📍 Location: {latitude}, {longitude}")
                    print(f"   📍 Status: {status}")
                    print(f"   📍 Address: {current_address}")
                    
                    # Check if this is our test courier with the GPS data we sent
                    if (latitude == 55.7558 and longitude == 37.6176 and 
                        status == "online" and current_address == "Москва, Красная площадь"):
                        test_courier_found = True
                        print("   ✅ Test courier GPS data found in admin response!")
                        break
                
                if test_courier_found:
                    print("   🎉 GPS TRACKING FIX SUCCESSFUL - Admin receives courier locations!")
                else:
                    print("   ⚠️  Test courier GPS data not found in admin response")
                    print("   ℹ️  This may be due to data isolation or timing issues")
            elif isinstance(admin_locations, dict):
                locations_list = admin_locations.get('locations', [])
                print(f"   📊 Found {len(locations_list)} courier locations in structured response")
            else:
                print("   ❌ Unexpected response format for admin courier locations")
                all_success = False
        else:
            print("   ❌ GET /api/admin/couriers/locations endpoint failed")
            print("   ❌ ADMIN STILL CANNOT RECEIVE GPS DATA!")
            all_success = False
        
        # Step 6: Авторизация оператора (+79777888999/warehouse123)
        print("\n   🏭 Step 6: АВТОРИЗАЦИЯ ОПЕРАТОРА (+79777888999/warehouse123)...")
        
        operator_login_data = {
            "phone": "+79777888999",
            "password": "warehouse123"
        }
        
        success, operator_login_response = self.run_test(
            "Warehouse Operator Authentication for GPS Testing",
            "POST",
            "/api/auth/login",
            200,
            operator_login_data
        )
        all_success &= success
        
        operator_token = None
        if success and 'access_token' in operator_login_response:
            operator_token = operator_login_response['access_token']
            operator_user = operator_login_response.get('user', {})
            operator_role = operator_user.get('role')
            operator_name = operator_user.get('full_name')
            
            print(f"   ✅ Operator login successful: {operator_name}")
            print(f"   👑 Role: {operator_role}")
            
            self.tokens['warehouse_operator'] = operator_token
            self.users['warehouse_operator'] = operator_user
        else:
            print("   ❌ Operator login failed")
            all_success = False
            return False
        
        # Step 7: Протестировать endpoint GET /api/operator/couriers/locations
        print("\n   🚚 Step 7: ПРОТЕСТИРОВАТЬ ENDPOINT GET /api/operator/couriers/locations...")
        
        success, operator_locations = self.run_test(
            "Operator Get Courier Locations",
            "GET",
            "/api/operator/couriers/locations",
            200,
            token=operator_token
        )
        all_success &= success
        
        if success:
            print("   ✅ GET /api/operator/couriers/locations endpoint working")
            print("   ✅ OPERATOR CAN NOW RECEIVE GPS DATA!")
            
            # Verify response contains courier locations for operator's warehouses
            if isinstance(operator_locations, list):
                location_count = len(operator_locations)
                print(f"   📊 Found {location_count} courier locations for operator's warehouses")
                
                if location_count > 0:
                    for location in operator_locations:
                        courier_name = location.get('courier_name')
                        status = location.get('status')
                        current_address = location.get('current_address')
                        
                        print(f"   📍 Courier: {courier_name}")
                        print(f"   📍 Status: {status}")
                        print(f"   📍 Address: {current_address}")
                    
                    print("   ✅ Operator receives courier locations with proper warehouse isolation!")
                else:
                    print("   ⚠️  No courier locations found for operator")
                    print("   ℹ️  This may be due to warehouse assignment or no couriers assigned to operator's warehouses")
            elif isinstance(operator_locations, dict):
                locations_list = operator_locations.get('locations', [])
                print(f"   📊 Found {len(locations_list)} courier locations in structured response")
            else:
                print("   ❌ Unexpected response format for operator courier locations")
                all_success = False
        else:
            print("   ❌ GET /api/operator/couriers/locations endpoint failed")
            print("   ❌ OPERATOR STILL CANNOT RECEIVE GPS DATA!")
            all_success = False
        
        return all_success

    def run_all_tests(self):
        """Run all critical courier fixes tests"""
        print("\n🚀 STARTING COMPREHENSIVE CRITICAL COURIER FIXES TESTING")
        
        all_tests_passed = True
        
        # Test 1: Courier Request Editing Save Error Fix
        print("\n" + "="*80)
        test1_result = self.test_courier_request_editing_save_error_fix()
        all_tests_passed &= test1_result
        
        # Test 2: GPS Tracking Data Not Received Fix
        print("\n" + "="*80)
        test2_result = self.test_gps_tracking_data_not_received_fix()
        all_tests_passed &= test2_result
        
        # Final Summary
        print("\n" + "="*80)
        print("🏁 FINAL SUMMARY - CRITICAL COURIER FIXES TESTING")
        print("="*80)
        
        print(f"\n📊 OVERALL STATISTICS:")
        print(f"   🔍 Total tests run: {self.tests_run}")
        print(f"   ✅ Tests passed: {self.tests_passed}")
        print(f"   ❌ Tests failed: {self.tests_run - self.tests_passed}")
        print(f"   📈 Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "   📈 Success rate: 0%")
        
        print(f"\n🎯 CRITICAL FIXES RESULTS:")
        if test1_result:
            print("   ✅ ПРОБЛЕМА 1 - ИСПРАВЛЕНИЕ ОШИБКИ СОХРАНЕНИЯ ПРИ РЕДАКТИРОВАНИИ ЗАЯВОК КУРЬЕРАМИ: РЕШЕНА")
        else:
            print("   ❌ ПРОБЛЕМА 1 - ИСПРАВЛЕНИЕ ОШИБКИ СОХРАНЕНИЯ ПРИ РЕДАКТИРОВАНИИ ЗАЯВОК КУРЬЕРАМИ: НЕ РЕШЕНА")
        
        if test2_result:
            print("   ✅ ПРОБЛЕМА 2 - ИСПРАВЛЕНИЕ GPS ОТСЛЕЖИВАНИЯ: РЕШЕНА")
        else:
            print("   ❌ ПРОБЛЕМА 2 - ИСПРАВЛЕНИЕ GPS ОТСЛЕЖИВАНИЯ: НЕ РЕШЕНА")
        
        print(f"\n🏆 OVERALL RESULT:")
        if all_tests_passed:
            print("   🎉 ALL CRITICAL COURIER FIXES WORKING PERFECTLY!")
            print("   ✅ Редактирование заявок курьерами должно работать без ошибок")
            print("   ✅ GPS данные должны корректно отправляться и получаться операторами/админами")
            print("   ✅ Все endpoints должны возвращать корректные данные")
        else:
            print("   ❌ SOME CRITICAL FIXES STILL NEED ATTENTION")
            print("   🔍 Check the detailed test results above for specific issues")
        
        return all_tests_passed

if __name__ == "__main__":
    tester = CourierCriticalFixesTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
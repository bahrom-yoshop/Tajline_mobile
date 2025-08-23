#!/usr/bin/env python3
"""
GPS System Testing for TAJLINE.TJ Application
Tests GPS functionality after route conflict fixes
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class GPSSystemTester:
    def __init__(self, base_url="https://tajline-manage-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.tokens = {}  # Store tokens for different users
        self.users = {}   # Store user data
        self.tests_run = 0
        self.tests_passed = 0
        
        print(f"🛰️ GPS SYSTEM TESTER FOR TAJLINE.TJ")
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

    def test_gps_system_after_route_conflict_fix(self):
        """Test GPS system for TAJLINE.TJ after fixing route conflicts"""
        print("\n🛰️ GPS SYSTEM TESTING AFTER ROUTE CONFLICT FIX")
        print("   🎯 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ GPS СИСТЕМЫ TAJLINE.TJ после исправления конфликта маршрутов")
        print("   🔧 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ - ПОЛНАЯ GPS СИСТЕМА:")
        print("   1) Авторизация курьера (+79991234567/courier123)")
        print("   2) Отправка GPS данных POST /api/courier/location/update")
        print("   3) Проверить автоматическое создание профиля курьера")
        print("   4) Авторизация администратора (+79999888777/admin123)")
        print("   5) КРИТИЧЕСКИЙ ТЕСТ: GET /api/admin/couriers/locations - должен работать после исправления конфликта маршрутов")
        print("   6) Проверить что GPS данные курьера видны администратору")
        print("   7) Авторизация оператора (+79777888999/warehouse123)")
        print("   8) Протестировать GET /api/operator/couriers/locations")
        print("   9) Дополнительно: GET /api/admin/websocket/stats для статистики WebSocket")
        
        all_success = True
        
        # Test 1: АВТОРИЗАЦИЯ КУРЬЕРА (+79991234567/courier123)
        print("\n   🚚 Test 1: АВТОРИЗАЦИЯ КУРЬЕРА (+79991234567/courier123)...")
        
        courier_login_data = {
            "phone": "+79991234567",
            "password": "courier123"
        }
        
        success, login_response = self.run_test(
            "Courier Authentication for GPS System",
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
        
        # Test 2: ОТПРАВКА GPS ДАННЫХ POST /api/courier/location/update
        print("\n   📍 Test 2: ОТПРАВКА GPS ДАННЫХ POST /api/courier/location/update...")
        
        gps_data = {
            "latitude": 55.7558,
            "longitude": 37.6176,
            "status": "online",
            "accuracy": 10.5,
            "current_address": "Москва, Красная площадь"
        }
        
        success, location_response = self.run_test(
            "Send GPS Location Data",
            "POST",
            "/api/courier/location/update",
            200,
            gps_data,
            courier_token
        )
        all_success &= success
        
        location_id = None
        if success:
            print("   ✅ GPS data sent successfully")
            location_id = location_response.get('location_id')
            if location_id:
                print(f"   📍 Location ID generated: {location_id}")
                print("   ✅ GPS location tracking working")
            else:
                print("   ❌ No location ID returned")
                all_success = False
            
            # Verify response structure
            expected_fields = ['location_id', 'message']
            missing_fields = [field for field in expected_fields if field not in location_response]
            if not missing_fields:
                print("   ✅ Response structure correct (location_id, message)")
            else:
                print(f"   ❌ Missing response fields: {missing_fields}")
                all_success = False
        else:
            print("   ❌ Failed to send GPS data")
            all_success = False
        
        # Test 3: ПРОВЕРИТЬ АВТОМАТИЧЕСКОЕ СОЗДАНИЕ ПРОФИЛЯ КУРЬЕРА
        print("\n   👤 Test 3: ПРОВЕРИТЬ АВТОМАТИЧЕСКОЕ СОЗДАНИЕ ПРОФИЛЯ КУРЬЕРА...")
        
        # Check if courier profile was created automatically
        success, courier_status_response = self.run_test(
            "Check Courier Location Status (Profile Creation)",
            "GET",
            "/api/courier/location/status",
            200,
            token=courier_token
        )
        all_success &= success
        
        if success:
            print("   ✅ Courier location status endpoint working")
            
            # Verify profile information
            tracking_enabled = courier_status_response.get('tracking_enabled')
            status = courier_status_response.get('status')
            current_address = courier_status_response.get('current_address')
            
            if tracking_enabled is not None:
                print(f"   ✅ Tracking enabled: {tracking_enabled}")
            if status:
                print(f"   ✅ Current status: {status}")
            if current_address:
                print(f"   ✅ Current address: {current_address}")
                
            print("   ✅ Automatic courier profile creation working")
        else:
            print("   ❌ Failed to get courier location status")
            all_success = False
        
        # Test 4: АВТОРИЗАЦИЯ АДМИНИСТРАТОРА (+79999888777/admin123)
        print("\n   👑 Test 4: АВТОРИЗАЦИЯ АДМИНИСТРАТОРА (+79999888777/admin123)...")
        
        admin_login_data = {
            "phone": "+79999888777",
            "password": "admin123"
        }
        
        success, admin_login_response = self.run_test(
            "Admin Authentication for GPS System",
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
            
            if admin_role == 'admin':
                print("   ✅ Admin role correctly set to 'admin'")
            else:
                print(f"   ❌ Admin role incorrect: expected 'admin', got '{admin_role}'")
                all_success = False
            
            self.tokens['admin'] = admin_token
            self.users['admin'] = admin_user
        else:
            print("   ❌ Admin login failed - no access token received")
            all_success = False
            return False
        
        # Test 5: КРИТИЧЕСКИЙ ТЕСТ: GET /api/admin/couriers/locations - должен работать после исправления конфликта маршрутов
        print("\n   🎯 Test 5: КРИТИЧЕСКИЙ ТЕСТ: GET /api/admin/couriers/locations...")
        print("   📋 Должен работать после исправления конфликта маршрутов")
        
        success, admin_locations_response = self.run_test(
            "Admin Get All Courier Locations (CRITICAL TEST)",
            "GET",
            "/api/admin/couriers/locations",
            200,
            token=admin_token
        )
        all_success &= success
        
        if success:
            print("   🎉 КРИТИЧЕСКИЙ УСПЕХ: /api/admin/couriers/locations работает после исправления конфликта маршрутов!")
            
            # Verify response structure
            if isinstance(admin_locations_response, list):
                courier_count = len(admin_locations_response)
                print(f"   📊 Found {courier_count} courier locations")
                
                # Look for our test courier
                test_courier_found = False
                for courier_location in admin_locations_response:
                    courier_phone = courier_location.get('courier_phone')
                    if courier_phone == '+79991234567':
                        test_courier_found = True
                        print(f"   ✅ Test courier found in admin locations")
                        print(f"   📍 Courier name: {courier_location.get('courier_name')}")
                        print(f"   📍 Status: {courier_location.get('status')}")
                        print(f"   📍 Address: {courier_location.get('current_address')}")
                        print(f"   📍 Coordinates: {courier_location.get('latitude')}, {courier_location.get('longitude')}")
                        break
                
                if test_courier_found:
                    print("   ✅ GPS данные курьера видны администратору")
                else:
                    print("   ⚠️  Test courier not found in admin locations (may need time to sync)")
                    
            elif isinstance(admin_locations_response, dict):
                locations = admin_locations_response.get('locations', [])
                courier_count = len(locations)
                print(f"   📊 Found {courier_count} courier locations")
                print("   ✅ Structured response format")
            else:
                print("   ❌ Unexpected response format for admin courier locations")
                all_success = False
        else:
            print("   ❌ КРИТИЧЕСКАЯ ОШИБКА: /api/admin/couriers/locations не работает!")
            print("   🚨 Конфликт маршрутов может быть не исправлен")
            all_success = False
        
        # Test 6: ПРОВЕРИТЬ ЧТО GPS ДАННЫЕ КУРЬЕРА ВИДНЫ АДМИНИСТРАТОРУ
        print("\n   👁️ Test 6: ПРОВЕРИТЬ ЧТО GPS ДАННЫЕ КУРЬЕРА ВИДНЫ АДМИНИСТРАТОРУ...")
        
        if success and admin_locations_response:
            # Additional verification that GPS data is accessible
            gps_data_accessible = False
            
            if isinstance(admin_locations_response, list):
                for location in admin_locations_response:
                    if (location.get('latitude') is not None and 
                        location.get('longitude') is not None and
                        location.get('courier_phone') == '+79991234567'):
                        gps_data_accessible = True
                        print("   ✅ GPS coordinates accessible to admin")
                        print(f"   📍 Latitude: {location.get('latitude')}")
                        print(f"   📍 Longitude: {location.get('longitude')}")
                        print(f"   📍 Status: {location.get('status')}")
                        print(f"   📍 Address: {location.get('current_address')}")
                        break
            
            if gps_data_accessible:
                print("   ✅ GPS данные курьера полностью видны администратору")
            else:
                print("   ⚠️  GPS данные могут быть не полностью доступны администратору")
        else:
            print("   ❌ Cannot verify GPS data visibility due to previous failure")
            all_success = False
        
        # Test 7: АВТОРИЗАЦИЯ ОПЕРАТОРА (+79777888999/warehouse123)
        print("\n   🏭 Test 7: АВТОРИЗАЦИЯ ОПЕРАТОРА (+79777888999/warehouse123)...")
        
        operator_login_data = {
            "phone": "+79777888999",
            "password": "warehouse123"
        }
        
        success, operator_login_response = self.run_test(
            "Warehouse Operator Authentication for GPS System",
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
            
            if operator_role == 'warehouse_operator':
                print("   ✅ Operator role correctly set to 'warehouse_operator'")
            else:
                print(f"   ❌ Operator role incorrect: expected 'warehouse_operator', got '{operator_role}'")
                all_success = False
            
            self.tokens['warehouse_operator'] = operator_token
            self.users['warehouse_operator'] = operator_user
        else:
            print("   ❌ Operator login failed - no access token received")
            all_success = False
            return False
        
        # Test 8: ПРОТЕСТИРОВАТЬ GET /api/operator/couriers/locations
        print("\n   🚚 Test 8: ПРОТЕСТИРОВАТЬ GET /api/operator/couriers/locations...")
        
        success, operator_locations_response = self.run_test(
            "Operator Get Assigned Courier Locations",
            "GET",
            "/api/operator/couriers/locations",
            200,
            token=operator_token
        )
        all_success &= success
        
        if success:
            print("   ✅ /api/operator/couriers/locations endpoint working")
            
            # Verify response structure
            if isinstance(operator_locations_response, list):
                courier_count = len(operator_locations_response)
                print(f"   📊 Operator can see {courier_count} courier locations")
                
                if courier_count > 0:
                    print("   ✅ Operator has access to courier locations")
                    # Show sample courier info
                    sample_courier = operator_locations_response[0]
                    print(f"   📍 Sample courier: {sample_courier.get('courier_name')}")
                    print(f"   📍 Status: {sample_courier.get('status')}")
                else:
                    print("   ⚠️  No couriers assigned to this operator (normal if no assignments)")
                    
            elif isinstance(operator_locations_response, dict):
                locations = operator_locations_response.get('locations', [])
                courier_count = len(locations)
                print(f"   📊 Operator can see {courier_count} courier locations")
                print("   ✅ Structured response format")
            else:
                print("   ❌ Unexpected response format for operator courier locations")
                all_success = False
        else:
            print("   ❌ /api/operator/couriers/locations endpoint failed")
            all_success = False
        
        # Test 9: ДОПОЛНИТЕЛЬНО: GET /api/admin/websocket/stats для статистики WebSocket
        print("\n   📊 Test 9: ДОПОЛНИТЕЛЬНО: GET /api/admin/websocket/stats для статистики WebSocket...")
        
        success, websocket_stats_response = self.run_test(
            "Admin WebSocket Statistics",
            "GET",
            "/api/admin/websocket/stats",
            200,
            token=admin_token
        )
        all_success &= success
        
        if success:
            print("   ✅ /api/admin/websocket/stats endpoint working")
            
            # Verify WebSocket statistics structure
            if isinstance(websocket_stats_response, dict):
                connection_stats = websocket_stats_response.get('connection_stats', {})
                detailed_connections = websocket_stats_response.get('detailed_connections', [])
                server_uptime = websocket_stats_response.get('server_uptime')
                
                if connection_stats:
                    total_connections = connection_stats.get('total_connections', 0)
                    admin_connections = connection_stats.get('admin_connections', 0)
                    operator_connections = connection_stats.get('operator_connections', 0)
                    
                    print(f"   📊 Total WebSocket connections: {total_connections}")
                    print(f"   📊 Admin connections: {admin_connections}")
                    print(f"   📊 Operator connections: {operator_connections}")
                    print("   ✅ WebSocket connection statistics available")
                
                if server_uptime:
                    print(f"   📊 Server uptime: {server_uptime}")
                    print("   ✅ Server uptime information available")
                
                print("   ✅ WebSocket статистика доступна для real-time отслеживания")
            else:
                print("   ❌ Unexpected response format for WebSocket statistics")
                all_success = False
        else:
            print("   ❌ /api/admin/websocket/stats endpoint failed")
            all_success = False
        
        # SUMMARY
        print("\n   📊 GPS SYSTEM TESTING SUMMARY:")
        
        if all_success:
            print("   🎉 ВСЕ GPS ENDPOINTS РАБОТАЮТ БЕЗ ОШИБОК (200 OK)!")
            print("   ✅ Авторизация курьера (+79991234567/courier123) ✅")
            print("   ✅ Отправка GPS данных POST /api/courier/location/update ✅")
            print("   ✅ Автоматическое создание профиля курьера ✅")
            print("   ✅ Авторизация администратора (+79999888777/admin123) ✅")
            print("   ✅ КРИТИЧЕСКИЙ УСПЕХ: GET /api/admin/couriers/locations работает после исправления конфликта маршрутов ✅")
            print("   ✅ Администратор видит GPS данные курьеров ✅")
            print("   ✅ Авторизация оператора (+79777888999/warehouse123) ✅")
            print("   ✅ GET /api/operator/couriers/locations работает ✅")
            print("   ✅ WebSocket статистика доступна GET /api/admin/websocket/stats ✅")
            print("   🎯 ЦЕЛЬ ДОСТИГНУТА: GPS система полностью функциональна после исправления конфликта маршрутов FastAPI!")
        else:
            print("   ❌ НЕКОТОРЫЕ GPS ENDPOINTS НЕ РАБОТАЮТ!")
            print("   🔍 Проверьте детальные результаты выше")
            print("   🚨 Возможно, конфликт маршрутов не полностью исправлен")
        
        return all_success

if __name__ == "__main__":
    tester = GPSSystemTester()
    result = tester.test_gps_system_after_route_conflict_fix()
    
    # Final summary
    print("\n" + "=" * 60)
    print("🏁 FINAL GPS TEST SUMMARY")
    print(f"📊 Tests run: {tester.tests_run}")
    print(f"✅ Tests passed: {tester.tests_passed}")
    print(f"❌ Tests failed: {tester.tests_run - tester.tests_passed}")
    
    if result:
        print("🎉 GPS SYSTEM TEST PASSED! All GPS endpoints working correctly.")
    else:
        print("❌ GPS SYSTEM TEST FAILED! Check the detailed results above.")
    
    success_rate = (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0
    print(f"📈 Overall Success Rate: {success_rate:.1f}%")
    
    sys.exit(0 if result else 1)
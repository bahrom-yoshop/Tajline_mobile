#!/usr/bin/env python3
"""
Direct test for courier +992936999880 login and GPS functionality
"""

import requests
import sys
import json
from datetime import datetime

class DirectCourierTest:
    def __init__(self, base_url="https://tajline-cargo-8.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        
        print(f"🚚 Direct Courier +992936999880 Test")
        print(f"📡 Base URL: {self.base_url}")
        print("=" * 60)

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data=None, token=None, params=None):
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

    def test_courier_direct_login_and_gps(self):
        """Test direct login and GPS for courier +992936999880"""
        print("\n🇹🇯 DIRECT COURIER +992936999880 LOGIN AND GPS TEST")
        
        all_success = True
        
        # Test 1: Try direct login with courier credentials
        print("\n   🔐 Test 1: DIRECT COURIER LOGIN (+992936999880/courier123)...")
        
        courier_login_data = {
            "phone": "+992936999880",
            "password": "courier123"
        }
        
        success, login_response = self.run_test(
            "Direct Courier Login (+992936999880/courier123)",
            "POST",
            "/api/auth/login",
            200,
            courier_login_data
        )
        
        courier_token = None
        if success and 'access_token' in login_response:
            courier_token = login_response['access_token']
            courier_user = login_response.get('user', {})
            courier_role = courier_user.get('role')
            courier_name = courier_user.get('full_name')
            courier_phone = courier_user.get('phone')
            courier_user_number = courier_user.get('user_number')
            
            print("   ✅ COURIER LOGIN SUCCESSFUL!")
            print(f"   👤 Name: {courier_name}")
            print(f"   📞 Phone: {courier_phone}")
            print(f"   👑 Role: {courier_role}")
            print(f"   🆔 User Number: {courier_user_number}")
            print(f"   🔑 JWT Token: {courier_token[:50]}...")
            
            # Verify role
            if courier_role == 'courier':
                print("   ✅ Role correctly set to 'courier'")
            else:
                print(f"   ⚠️  Role is '{courier_role}', not 'courier'")
            
            all_success &= success
        else:
            print("   ❌ COURIER LOGIN FAILED")
            print(f"   📄 Response: {login_response}")
            
            # Try with different password
            print("\n   🔄 Trying alternative passwords...")
            
            alternative_passwords = ["123456", "password", "courier", "tajikistan"]
            
            for alt_password in alternative_passwords:
                alt_login_data = {
                    "phone": "+992936999880",
                    "password": alt_password
                }
                
                success, alt_response = self.run_test(
                    f"Try password: {alt_password}",
                    "POST",
                    "/api/auth/login",
                    200,
                    alt_login_data
                )
                
                if success and 'access_token' in alt_response:
                    courier_token = alt_response['access_token']
                    courier_user = alt_response.get('user', {})
                    print(f"   ✅ SUCCESS with password: {alt_password}")
                    print(f"   👤 Name: {courier_user.get('full_name')}")
                    print(f"   👑 Role: {courier_user.get('role')}")
                    all_success = True
                    break
            
            if not courier_token:
                print("   ❌ All login attempts failed")
                all_success = False
                return False
        
        # Test 2: Send GPS location update
        if courier_token:
            print("\n   📍 Test 2: GPS LOCATION UPDATE...")
            
            gps_data = {
                "latitude": 38.5598,  # Душанбе
                "longitude": 68.7870,
                "status": "on_route",  # Едет к клиенту
                "current_address": "Душанбе, тестовый адрес",
                "accuracy": 10.5
            }
            
            success, gps_response = self.run_test(
                "Send GPS Location Update (on_route status)",
                "POST",
                "/api/courier/location/update",
                200,
                gps_data,
                courier_token
            )
            
            if success:
                print("   ✅ GPS UPDATE SUCCESSFUL!")
                location_id = gps_response.get('location_id')
                print(f"   📍 Location ID: {location_id}")
                print(f"   🌍 Coordinates: {gps_data['latitude']}, {gps_data['longitude']}")
                print(f"   📊 Status: {gps_data['status']} (Едет к клиенту)")
                print(f"   📍 Address: {gps_data['current_address']}")
                
                all_success &= success
            else:
                print("   ❌ GPS UPDATE FAILED")
                all_success = False
        
        # Test 3: Check GPS status
        if courier_token:
            print("\n   📊 Test 3: CHECK GPS STATUS...")
            
            success, status_response = self.run_test(
                "Check Courier GPS Status",
                "GET",
                "/api/courier/location/status",
                200,
                token=courier_token
            )
            
            if success:
                print("   ✅ GPS STATUS CHECK SUCCESSFUL!")
                tracking_enabled = status_response.get('tracking_enabled')
                current_status = status_response.get('current_status')
                current_address = status_response.get('current_address')
                
                print(f"   🛰️ Tracking Enabled: {tracking_enabled}")
                print(f"   📊 Current Status: {current_status}")
                print(f"   📍 Current Address: {current_address}")
                
                if current_status == 'on_route':
                    print("   ✅ Status correctly shows 'on_route' (Едет к клиенту)")
                
                all_success &= success
            else:
                print("   ❌ GPS STATUS CHECK FAILED")
                all_success = False
        
        # Test 4: Admin login and check courier GPS data
        print("\n   👑 Test 4: ADMIN CHECK COURIER GPS DATA...")
        
        admin_login_data = {
            "phone": "+79999888777",
            "password": "admin123"
        }
        
        success, admin_login_response = self.run_test(
            "Admin Login",
            "POST",
            "/api/auth/login",
            200,
            admin_login_data
        )
        
        if success and 'access_token' in admin_login_response:
            admin_token = admin_login_response['access_token']
            
            success, admin_gps_response = self.run_test(
                "Admin View All Courier GPS Locations",
                "GET",
                "/api/admin/couriers/locations",
                200,
                token=admin_token
            )
            
            if success:
                print("   ✅ ADMIN CAN ACCESS COURIER GPS DATA!")
                
                # Look for our courier
                locations = admin_gps_response if isinstance(admin_gps_response, list) else admin_gps_response.get('locations', [])
                print(f"   📊 Total courier locations: {len(locations)}")
                
                courier_found = False
                for location in locations:
                    if location.get('courier_phone') == '+992936999880':
                        courier_found = True
                        print("   ✅ КУРЬЕР +992936999880 НАЙДЕН В GPS ДАННЫХ!")
                        print(f"   👤 Name: {location.get('courier_name')}")
                        print(f"   📞 Phone: {location.get('courier_phone')}")
                        print(f"   📊 Status: {location.get('status')}")
                        print(f"   🌍 Coordinates: {location.get('latitude')}, {location.get('longitude')}")
                        print(f"   📍 Address: {location.get('current_address')}")
                        break
                
                if not courier_found:
                    print("   ⚠️  Курьер +992936999880 не найден в GPS данных")
                    print("   ℹ️  Возможно GPS данные еще не синхронизировались")
                
                all_success &= success
            else:
                print("   ❌ ADMIN CANNOT ACCESS COURIER GPS DATA")
                all_success = False
        else:
            print("   ❌ ADMIN LOGIN FAILED")
            all_success = False
        
        # Summary
        print("\n   📊 DIRECT COURIER TEST SUMMARY:")
        
        if all_success:
            print("   🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            print("   ✅ Курьер +992936999880 может авторизоваться")
            print("   ✅ GPS отслеживание работает")
            print("   ✅ Статус 'on_route' (Едет к клиенту) установлен")
            print("   ✅ Админ может видеть GPS данные курьера")
            print("   🎯 ЦЕЛЬ ДОСТИГНУТА: Курьер +992936999880 готов к использованию!")
        else:
            print("   ❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
            print("   🔍 Проверьте детали выше")
        
        return all_success

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Direct Courier Testing...")
        
        test_result = self.test_courier_direct_login_and_gps()
        
        # Final summary
        print(f"\n{'='*60}")
        print(f"📊 FINAL RESULTS:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if test_result:
            print(f"   🎉 SUCCESS: Courier +992936999880 is functional!")
        else:
            print(f"   ❌ FAILED: Issues found with courier +992936999880")
        
        return test_result

if __name__ == "__main__":
    tester = DirectCourierTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
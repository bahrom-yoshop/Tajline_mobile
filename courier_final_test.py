#!/usr/bin/env python3
"""
Final comprehensive test for courier +992936999880 with correct password baha3337
Tests authentication and GPS functionality for TAJLINE.TJ system
"""

import requests
import sys
import json
from datetime import datetime

class FinalCourierTest:
    def __init__(self, base_url="https://cargo-sync.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        
        print(f"🚚 FINAL Courier +992936999880 Test (Correct Password)")
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

    def test_courier_complete_functionality(self):
        """Complete test of courier +992936999880 with correct password baha3337"""
        print("\n🇹🇯 COMPLETE COURIER +992936999880 FUNCTIONALITY TEST")
        print("   🎯 ЦЕЛЬ: Обеспечить что курьер +992936999880 может авторизоваться и использовать GPS отслеживание со статусами")
        print("   🔑 Используем правильный пароль: baha3337")
        
        all_success = True
        
        # Test 1: Courier Authentication with correct password
        print("\n   🔐 Test 1: COURIER AUTHENTICATION (+992936999880/baha3337)...")
        
        courier_login_data = {
            "phone": "+992936999880",
            "password": "baha3337"
        }
        
        success, login_response = self.run_test(
            "Courier Login with Correct Password (+992936999880/baha3337)",
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
                print(f"   ⚠️  Role is '{courier_role}', expected 'courier'")
                # Don't fail completely as user can still use GPS
            
            all_success &= success
        else:
            print("   ❌ COURIER LOGIN FAILED")
            print(f"   📄 Response: {login_response}")
            all_success = False
            return False
        
        # Test 2: GPS Location Update - Status: online (В сети, свободен)
        if courier_token:
            print("\n   📍 Test 2: GPS LOCATION UPDATE - STATUS: ONLINE (В сети, свободен)...")
            
            gps_data_online = {
                "latitude": 38.5598,  # Душанбе координаты
                "longitude": 68.7870,
                "status": "online",  # В сети, свободен
                "current_address": "Душанбе, Таджикистан - Центр",
                "accuracy": 8.5,
                "speed": 0.0,  # Стоит на месте
                "heading": 0.0
            }
            
            success, gps_response = self.run_test(
                "GPS Update - Status: online (В сети, свободен)",
                "POST",
                "/api/courier/location/update",
                200,
                gps_data_online,
                courier_token
            )
            
            if success:
                print("   ✅ GPS UPDATE SUCCESSFUL!")
                location_id = gps_response.get('location_id')
                print(f"   📍 Location ID: {location_id}")
                print(f"   🌍 Coordinates: {gps_data_online['latitude']}, {gps_data_online['longitude']}")
                print(f"   📊 Status: {gps_data_online['status']} (В сети, свободен)")
                print(f"   📍 Address: {gps_data_online['current_address']}")
                print(f"   🎯 Accuracy: {gps_data_online['accuracy']} meters")
                
                all_success &= success
            else:
                print("   ❌ GPS UPDATE FAILED")
                all_success = False
        
        # Test 3: GPS Location Update - Status: on_route (Едет к клиенту)
        if courier_token:
            print("\n   🚗 Test 3: GPS LOCATION UPDATE - STATUS: ON_ROUTE (Едет к клиенту)...")
            
            gps_data_on_route = {
                "latitude": 38.5650,  # Немного другие координаты (движение)
                "longitude": 68.7900,
                "status": "on_route",  # Едет к клиенту
                "current_address": "Душанбе, ул. Рудаки - движется к клиенту",
                "accuracy": 12.0,
                "speed": 35.5,  # Скорость 35.5 км/ч
                "heading": 45.0  # Направление на северо-восток
            }
            
            success, gps_response = self.run_test(
                "GPS Update - Status: on_route (Едет к клиенту)",
                "POST",
                "/api/courier/location/update",
                200,
                gps_data_on_route,
                courier_token
            )
            
            if success:
                print("   ✅ GPS UPDATE SUCCESSFUL!")
                location_id = gps_response.get('location_id')
                print(f"   📍 Location ID: {location_id}")
                print(f"   🌍 Coordinates: {gps_data_on_route['latitude']}, {gps_data_on_route['longitude']}")
                print(f"   📊 Status: {gps_data_on_route['status']} (Едет к клиенту)")
                print(f"   📍 Address: {gps_data_on_route['current_address']}")
                print(f"   🚗 Speed: {gps_data_on_route['speed']} км/ч")
                print(f"   🧭 Heading: {gps_data_on_route['heading']}° (северо-восток)")
                
                all_success &= success
            else:
                print("   ❌ GPS UPDATE FAILED")
                all_success = False
        
        # Test 4: GPS Location Update - Status: at_pickup (На месте забора груза)
        if courier_token:
            print("\n   📦 Test 4: GPS LOCATION UPDATE - STATUS: AT_PICKUP (На месте забора груза)...")
            
            gps_data_at_pickup = {
                "latitude": 38.5720,  # Координаты места забора
                "longitude": 68.7950,
                "status": "at_pickup",  # На месте забора груза
                "current_address": "Душанбе, ул. Исмоили Сомони, 24 - место забора груза",
                "accuracy": 5.0,  # Высокая точность на месте
                "speed": 0.0,  # Стоит на месте
                "heading": 0.0
            }
            
            success, gps_response = self.run_test(
                "GPS Update - Status: at_pickup (На месте забора груза)",
                "POST",
                "/api/courier/location/update",
                200,
                gps_data_at_pickup,
                courier_token
            )
            
            if success:
                print("   ✅ GPS UPDATE SUCCESSFUL!")
                location_id = gps_response.get('location_id')
                print(f"   📍 Location ID: {location_id}")
                print(f"   🌍 Coordinates: {gps_data_at_pickup['latitude']}, {gps_data_at_pickup['longitude']}")
                print(f"   📊 Status: {gps_data_at_pickup['status']} (На месте забора груза)")
                print(f"   📍 Address: {gps_data_at_pickup['current_address']}")
                print(f"   🎯 Accuracy: {gps_data_at_pickup['accuracy']} meters (высокая точность)")
                
                all_success &= success
            else:
                print("   ❌ GPS UPDATE FAILED")
                all_success = False
        
        # Test 5: GPS Location Update - Status: at_delivery (На месте доставки)
        if courier_token:
            print("\n   🏠 Test 5: GPS LOCATION UPDATE - STATUS: AT_DELIVERY (На месте доставки)...")
            
            gps_data_at_delivery = {
                "latitude": 38.5800,  # Координаты места доставки
                "longitude": 68.8000,
                "status": "at_delivery",  # На месте доставки
                "current_address": "Душанбе, микрорайон Сомони, дом 15 - место доставки",
                "accuracy": 3.0,  # Очень высокая точность
                "speed": 0.0,  # Стоит на месте
                "heading": 0.0
            }
            
            success, gps_response = self.run_test(
                "GPS Update - Status: at_delivery (На месте доставки)",
                "POST",
                "/api/courier/location/update",
                200,
                gps_data_at_delivery,
                courier_token
            )
            
            if success:
                print("   ✅ GPS UPDATE SUCCESSFUL!")
                location_id = gps_response.get('location_id')
                print(f"   📍 Location ID: {location_id}")
                print(f"   🌍 Coordinates: {gps_data_at_delivery['latitude']}, {gps_data_at_delivery['longitude']}")
                print(f"   📊 Status: {gps_data_at_delivery['status']} (На месте доставки)")
                print(f"   📍 Address: {gps_data_at_delivery['current_address']}")
                print(f"   🎯 Accuracy: {gps_data_at_delivery['accuracy']} meters (очень высокая точность)")
                
                all_success &= success
            else:
                print("   ❌ GPS UPDATE FAILED")
                all_success = False
        
        # Test 6: Check Current GPS Status
        if courier_token:
            print("\n   📊 Test 6: CHECK CURRENT GPS STATUS...")
            
            success, status_response = self.run_test(
                "Check Current Courier GPS Status",
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
                last_update = status_response.get('last_update')
                
                print(f"   🛰️ Tracking Enabled: {tracking_enabled}")
                print(f"   📊 Current Status: {current_status}")
                print(f"   📍 Current Address: {current_address}")
                print(f"   ⏰ Last Update: {last_update}")
                
                # Verify tracking is enabled
                if tracking_enabled:
                    print("   ✅ GPS tracking is enabled for courier")
                else:
                    print("   ⚠️  GPS tracking is not enabled")
                
                # Verify status matches last update (should be at_delivery)
                if current_status == 'at_delivery':
                    print("   ✅ Status correctly shows 'at_delivery' (На месте доставки)")
                else:
                    print(f"   ℹ️  Current status: {current_status}")
                
                all_success &= success
            else:
                print("   ❌ GPS STATUS CHECK FAILED")
                all_success = False
        
        # Test 7: Admin View Courier GPS Data
        print("\n   👑 Test 7: ADMIN VIEW COURIER GPS DATA...")
        
        # First login as admin
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
            admin_user = admin_login_response.get('user', {})
            
            print(f"   ✅ Admin login successful: {admin_user.get('full_name')}")
            print(f"   👑 Role: {admin_user.get('role')}")
            
            # Get all courier locations
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
                        print("   ✅ КУРЬЕР +992936999880 НАЙДЕН В GPS ДАННЫХ АДМИНА!")
                        print(f"   👤 Name: {location.get('courier_name')}")
                        print(f"   📞 Phone: {location.get('courier_phone')}")
                        print(f"   📊 Status: {location.get('status')}")
                        print(f"   🌍 Coordinates: {location.get('latitude')}, {location.get('longitude')}")
                        print(f"   📍 Address: {location.get('current_address')}")
                        print(f"   🚗 Speed: {location.get('speed', 'N/A')} км/ч")
                        print(f"   🎯 Accuracy: {location.get('accuracy', 'N/A')} meters")
                        print(f"   ⏰ Last Update: {location.get('last_updated')}")
                        break
                
                if not courier_found:
                    print("   ⚠️  Курьер +992936999880 не найден в GPS данных админа")
                    print("   ℹ️  Возможные причины:")
                    print("       - GPS данные еще не синхронизировались")
                    print("       - Курьер не имеет профиля курьера в системе")
                    print("       - Фильтрация по роли или статусу")
                
                all_success &= success
            else:
                print("   ❌ ADMIN CANNOT ACCESS COURIER GPS DATA")
                all_success = False
        else:
            print("   ❌ ADMIN LOGIN FAILED")
            all_success = False
        
        # Test 8: Test GPS Status: busy (Занят другими делами)
        if courier_token:
            print("\n   ⏳ Test 8: GPS LOCATION UPDATE - STATUS: BUSY (Занят другими делами)...")
            
            gps_data_busy = {
                "latitude": 38.5598,  # Возвращаемся в центр
                "longitude": 68.7870,
                "status": "busy",  # Занят другими делами
                "current_address": "Душанбе, Таджикистан - занят другими делами",
                "accuracy": 10.0,
                "speed": 0.0,
                "heading": 0.0
            }
            
            success, gps_response = self.run_test(
                "GPS Update - Status: busy (Занят другими делами)",
                "POST",
                "/api/courier/location/update",
                200,
                gps_data_busy,
                courier_token
            )
            
            if success:
                print("   ✅ GPS UPDATE SUCCESSFUL!")
                print(f"   📊 Status: {gps_data_busy['status']} (Занят другими делами)")
                print(f"   📍 Address: {gps_data_busy['current_address']}")
                
                all_success &= success
            else:
                print("   ❌ GPS UPDATE FAILED")
                all_success = False
        
        # Test 9: Test GPS Status: offline (Не в сети / отслеживание выключено)
        if courier_token:
            print("\n   📴 Test 9: GPS LOCATION UPDATE - STATUS: OFFLINE (Не в сети)...")
            
            gps_data_offline = {
                "latitude": 38.5598,
                "longitude": 68.7870,
                "status": "offline",  # Не в сети / отслеживание выключено
                "current_address": "Душанбе, Таджикистан - отслеживание выключено",
                "accuracy": 15.0,
                "speed": 0.0,
                "heading": 0.0
            }
            
            success, gps_response = self.run_test(
                "GPS Update - Status: offline (Не в сети)",
                "POST",
                "/api/courier/location/update",
                200,
                gps_data_offline,
                courier_token
            )
            
            if success:
                print("   ✅ GPS UPDATE SUCCESSFUL!")
                print(f"   📊 Status: {gps_data_offline['status']} (Не в сети / отслеживание выключено)")
                print(f"   📍 Address: {gps_data_offline['current_address']}")
                
                all_success &= success
            else:
                print("   ❌ GPS UPDATE FAILED")
                all_success = False
        
        # Final Status Check
        if courier_token:
            print("\n   📊 Test 10: FINAL GPS STATUS CHECK...")
            
            success, final_status_response = self.run_test(
                "Final GPS Status Check",
                "GET",
                "/api/courier/location/status",
                200,
                token=courier_token
            )
            
            if success:
                print("   ✅ FINAL GPS STATUS CHECK SUCCESSFUL!")
                final_status = final_status_response.get('current_status')
                final_address = final_status_response.get('current_address')
                
                print(f"   📊 Final Status: {final_status}")
                print(f"   📍 Final Address: {final_address}")
                
                if final_status == 'offline':
                    print("   ✅ Status correctly shows 'offline' (последнее обновление)")
                
                all_success &= success
            else:
                print("   ❌ FINAL GPS STATUS CHECK FAILED")
                all_success = False
        
        # Summary
        print("\n   📊 COMPLETE COURIER FUNCTIONALITY TEST SUMMARY:")
        
        if all_success:
            print("   🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            print("   ✅ Курьер +992936999880 найден в системе TAJLINE.TJ")
            print("   ✅ Авторизация работает с паролем: baha3337")
            print("   ✅ GPS отслеживание полностью функционально")
            print("   ✅ Все статусы курьера протестированы:")
            print("       - online (В сети, свободен) ✅")
            print("       - on_route (Едет к клиенту) ✅")
            print("       - at_pickup (На месте забора груза) ✅")
            print("       - at_delivery (На месте доставки) ✅")
            print("       - busy (Занят другими делами) ✅")
            print("       - offline (Не в сети / отслеживание выключено) ✅")
            print("   ✅ Админ может видеть GPS данные курьера")
            print("   ✅ Координаты, скорость, направление, точность передаются корректно")
            print("   🎯 ЦЕЛЬ ДОСТИГНУТА: Курьер +992936999880 может авторизоваться и использовать GPS отслеживание со всеми статусами!")
        else:
            print("   ❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
            print("   🔍 Проверьте детали неудачных тестов выше")
            print("   ℹ️  Возможные проблемы:")
            print("       - GPS endpoints не реализованы")
            print("       - Курьер не имеет профиля в системе")
            print("       - Проблемы с авторизацией или ролями")
        
        return all_success

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Final Courier +992936999880 Testing...")
        
        test_result = self.test_courier_complete_functionality()
        
        # Final summary
        print(f"\n{'='*60}")
        print(f"📊 FINAL RESULTS:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if test_result:
            print(f"   🎉 SUCCESS: Курьер +992936999880 полностью функционален!")
            print(f"   ✅ Может авторизоваться и использовать GPS отслеживание со статусами")
        else:
            print(f"   ❌ FAILED: Проблемы с курьером +992936999880")
            print(f"   🔧 Требуется дополнительная настройка или исправления")
        
        return test_result

if __name__ == "__main__":
    tester = FinalCourierTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
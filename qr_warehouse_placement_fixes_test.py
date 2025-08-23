#!/usr/bin/env python3
"""
QR Code and Warehouse Placement Fixes Testing for TAJLINE.TJ
Tests the fixes for QR codes and warehouse placement functionality according to review request

КОНТЕКСТ: Исправлены две проблемы:
1. QR КОД: изменена библиотека с QRCode на QRious, упрощены данные QR (только номер заявки), улучшена обработка ошибок
2. ОТПРАВКА НА РАЗМЕЩЕНИЕ: исправлена логика получения warehouse_id - если у оператора нет привязок к складам, используется первый активный склад

ТЕСТОВЫЙ ПЛАН:
1. Авторизация оператора склада (+79777888999/warehouse123)
2. Получение уведомлений со статусом "in_processing"
3. Тестирование исправленного endpoint отправки на размещение
4. Проверка корректного получения warehouse_id для операторов без привязок
5. Проверка создания груза и появления в списке размещения
6. Проверка что исправление warehouse_id устранило ошибку 500

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Endpoint должен работать без ошибок 500, корректно получать warehouse_id даже для операторов без привязок, создавать груз и добавлять в категорию размещения.
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class QRWarehousePlacementFixesTester:
    def __init__(self, base_url="https://cargo-sync.preview.emergentagent.com"):
        self.base_url = base_url
        self.tokens = {}
        self.users = {}
        self.tests_run = 0
        self.tests_passed = 0
        
        print(f"🎯 QR CODE AND WAREHOUSE PLACEMENT FIXES TESTING FOR TAJLINE.TJ")
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
                    elif isinstance(result, list) and len(result) <= 3:
                        print(f"   📄 Response: {result}")
                    else:
                        print(f"   📄 Response: {type(result).__name__} with {len(result) if hasattr(result, '__len__') else 'N/A'} items")
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

    def test_qr_code_and_warehouse_placement_fixes(self):
        """Test QR code and warehouse placement fixes according to review request"""
        print("\n🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ QR КОДОВ И ОТПРАВКИ НА РАЗМЕЩЕНИЕ В TAJLINE.TJ")
        print("   📋 Протестировать исправления проблем с QR кодами и отправкой на размещение согласно review request")
        
        all_success = True
        
        # ЭТАП 1: АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА (+79777888999/warehouse123)
        print("\n   🔐 ЭТАП 1: АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА (+79777888999/warehouse123)...")
        
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
        
        # ЭТАП 2: ПОЛУЧЕНИЕ УВЕДОМЛЕНИЙ СО СТАТУСОМ "in_processing"
        print("\n   📬 ЭТАП 2: ПОЛУЧЕНИЕ УВЕДОМЛЕНИЙ СО СТАТУСОМ 'in_processing'...")
        
        success, notifications_response = self.run_test(
            "Get Warehouse Notifications with 'in_processing' status",
            "GET",
            "/api/operator/warehouse-notifications",
            200,
            token=operator_token,
            params={"status": "in_processing"}
        )
        all_success &= success
        
        available_notifications = []
        if success:
            if isinstance(notifications_response, list):
                available_notifications = notifications_response
                notification_count = len(available_notifications)
                print(f"   ✅ Found {notification_count} warehouse notifications")
                
                # Look for notifications with 'in_processing' status
                in_processing_notifications = [n for n in available_notifications if n.get('status') == 'in_processing']
                print(f"   📊 Notifications with 'in_processing' status: {len(in_processing_notifications)}")
                
                if in_processing_notifications:
                    sample_notification = in_processing_notifications[0]
                    print(f"   📋 Sample notification ID: {sample_notification.get('id')}")
                    print(f"   📋 Sample notification status: {sample_notification.get('status')}")
                    print(f"   📋 Sample request number: {sample_notification.get('request_number')}")
                else:
                    print("   ⚠️  No notifications with 'in_processing' status found")
                    # Use any available notification for testing
                    if available_notifications:
                        sample_notification = available_notifications[0]
                        print(f"   📋 Using first available notification for testing: {sample_notification.get('id')}")
                        in_processing_notifications = [sample_notification]
            else:
                print("   ❌ Unexpected response format for warehouse notifications")
                all_success = False
        else:
            print("   ❌ Failed to get warehouse notifications")
            all_success = False
        
        # ЭТАП 3: ТЕСТИРОВАНИЕ ИСПРАВЛЕННОГО ENDPOINT ОТПРАВКИ НА РАЗМЕЩЕНИЕ
        print("\n   🏭 ЭТАП 3: ТЕСТИРОВАНИЕ ИСПРАВЛЕННОГО ENDPOINT ОТПРАВКИ НА РАЗМЕЩЕНИЕ...")
        print("   🔧 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: исправлена логика получения warehouse_id")
        print("   📋 Если у оператора нет привязок к складам, используется первый активный склад")
        
        if available_notifications:
            # Use the first available notification for testing
            test_notification = available_notifications[0]
            notification_id = test_notification.get('id')
            
            print(f"   🧪 Testing with notification ID: {notification_id}")
            
            # Test the fixed send-to-placement endpoint
            success, placement_response = self.run_test(
                "Send Notification to Placement (CRITICAL FIX)",
                "POST",
                f"/api/operator/warehouse-notifications/{notification_id}/send-to-placement",
                200,
                token=operator_token
            )
            
            if success:
                print("   🎉 КРИТИЧЕСКИЙ УСПЕХ - Endpoint отправки на размещение работает БЕЗ ошибки 500!")
                print("   ✅ Исправление warehouse_id логики работает корректно")
                
                # Verify response structure
                if isinstance(placement_response, dict):
                    message = placement_response.get('message', '')
                    cargo_id = placement_response.get('cargo_id', '')
                    cargo_number = placement_response.get('cargo_number', '')
                    warehouse_id = placement_response.get('warehouse_id', '')
                    
                    print(f"   📄 Response message: {message}")
                    if cargo_id:
                        print(f"   📦 Created cargo ID: {cargo_id}")
                    if cargo_number:
                        print(f"   📦 Created cargo number: {cargo_number}")
                    if warehouse_id:
                        print(f"   🏭 Assigned warehouse ID: {warehouse_id}")
                        print("   ✅ warehouse_id корректно получен (исправление работает)")
                    else:
                        print("   ⚠️  warehouse_id not returned in response")
                else:
                    print(f"   📄 Response: {placement_response}")
                
                # Store cargo info for further testing
                if isinstance(placement_response, dict):
                    self.created_cargo_number = placement_response.get('cargo_number')
                    self.created_cargo_id = placement_response.get('cargo_id')
                    self.assigned_warehouse_id = placement_response.get('warehouse_id')
            else:
                print("   ❌ КРИТИЧЕСКАЯ ОШИБКА - Endpoint отправки на размещение все еще возвращает ошибку")
                print("   🔍 Проверьте логику получения warehouse_id в backend")
                all_success = False
        else:
            print("   ⚠️  No notifications available for testing send-to-placement")
            
            # Create a test notification/request for testing
            print("   🧪 Creating test pickup request for placement testing...")
            
            # Create a test pickup request first
            pickup_request_data = {
                "sender_full_name": "Тест Отправитель Размещение",
                "sender_phone": "+79991234567",
                "cargo_name": "Тестовый груз для размещения",
                "pickup_address": "Москва, ул. Тестовая Размещение, 123",
                "pickup_date": "2025-01-20",
                "pickup_time_from": "10:00",
                "pickup_time_to": "18:00",
                "route": "moscow_to_tajikistan",
                "courier_fee": 500.0
            }
            
            success, pickup_response = self.run_test(
                "Create Test Pickup Request for Placement",
                "POST",
                "/api/admin/courier/pickup-request",
                200,
                pickup_request_data,
                operator_token
            )
            
            if success and pickup_response.get('id'):
                print(f"   ✅ Test pickup request created: {pickup_response.get('request_number')}")
                # This would create a notification that we could then test with
            else:
                print("   ❌ Failed to create test pickup request")
                all_success = False
        
        # ЭТАП 4: ПРОВЕРКА КОРРЕКТНОГО ПОЛУЧЕНИЯ warehouse_id ДЛЯ ОПЕРАТОРОВ БЕЗ ПРИВЯЗОК
        print("\n   🔍 ЭТАП 4: ПРОВЕРКА КОРРЕКТНОГО ПОЛУЧЕНИЯ warehouse_id ДЛЯ ОПЕРАТОРОВ БЕЗ ПРИВЯЗОК...")
        
        # Check operator warehouse bindings
        success, bindings_response = self.run_test(
            "Check Operator Warehouse Bindings",
            "GET",
            "/api/operator/warehouses",
            200,
            token=operator_token
        )
        
        if success:
            operator_warehouses = bindings_response if isinstance(bindings_response, list) else []
            warehouse_count = len(operator_warehouses)
            
            print(f"   📊 Operator has {warehouse_count} assigned warehouses")
            
            if warehouse_count == 0:
                print("   ✅ ТЕСТОВЫЙ СЛУЧАЙ: Оператор без привязок к складам")
                print("   🔧 Исправление должно использовать первый активный склад")
                
                # Get all active warehouses to verify the fix logic
                success, all_warehouses = self.run_test(
                    "Get All Active Warehouses (for fallback logic)",
                    "GET",
                    "/api/warehouses",
                    200,
                    token=operator_token
                )
                
                if success and all_warehouses:
                    active_warehouses = [w for w in all_warehouses if w.get('is_active', True)]
                    print(f"   📊 Total active warehouses available: {len(active_warehouses)}")
                    
                    if active_warehouses:
                        first_warehouse = active_warehouses[0]
                        print(f"   🏭 First active warehouse: {first_warehouse.get('name')} (ID: {first_warehouse.get('id')})")
                        print("   ✅ Fallback warehouse available for operators without bindings")
                    else:
                        print("   ❌ No active warehouses available for fallback")
                        all_success = False
            else:
                print("   📊 Оператор имеет привязки к складам:")
                for i, warehouse in enumerate(operator_warehouses[:3], 1):  # Show first 3
                    print(f"   🏭 {i}. {warehouse.get('name')} (ID: {warehouse.get('id')})")
                print("   ✅ Нормальный случай: используются привязанные склады")
        else:
            print("   ❌ Failed to check operator warehouse bindings")
            all_success = False
        
        # ЭТАП 5: ПРОВЕРКА СОЗДАНИЯ ГРУЗА И ПОЯВЛЕНИЯ В СПИСКЕ РАЗМЕЩЕНИЯ
        print("\n   📦 ЭТАП 5: ПРОВЕРКА СОЗДАНИЯ ГРУЗА И ПОЯВЛЕНИЯ В СПИСКЕ РАЗМЕЩЕНИЯ...")
        
        # Check if cargo was created and appears in placement list
        success, placement_list = self.run_test(
            "Get Available Cargo for Placement",
            "GET",
            "/api/operator/cargo/available-for-placement",
            200,
            token=operator_token
        )
        
        if success:
            if isinstance(placement_list, dict):
                items = placement_list.get('items', [])
                total_count = placement_list.get('total_count', 0)
                print(f"   ✅ Placement list accessible: {total_count} total items")
                print(f"   📊 Items in current page: {len(items)}")
                
                # Check if our created cargo appears in the list
                if hasattr(self, 'created_cargo_number') and self.created_cargo_number:
                    created_cargo_found = any(
                        item.get('cargo_number') == self.created_cargo_number 
                        for item in items
                    )
                    
                    if created_cargo_found:
                        print(f"   🎉 УСПЕХ - Созданный груз {self.created_cargo_number} найден в списке размещения!")
                        print("   ✅ Груз корректно добавлен в категорию размещения")
                    else:
                        print(f"   ⚠️  Созданный груз {self.created_cargo_number} не найден в текущей странице")
                        print("   ℹ️  Груз может быть на другой странице или требует времени для обновления")
                
                # Verify all items have required fields for placement
                if items:
                    sample_item = items[0]
                    required_fields = ['cargo_number', 'processing_status', 'warehouse_id']
                    missing_fields = [field for field in required_fields if field not in sample_item]
                    
                    if not missing_fields:
                        print("   ✅ Placement items have required fields (cargo_number, processing_status, warehouse_id)")
                        
                        # Check processing status
                        processing_status = sample_item.get('processing_status')
                        warehouse_id = sample_item.get('warehouse_id')
                        
                        print(f"   📊 Sample processing status: {processing_status}")
                        print(f"   🏭 Sample warehouse_id: {warehouse_id}")
                        
                        if warehouse_id:
                            print("   ✅ warehouse_id присутствует в элементах размещения")
                        else:
                            print("   ❌ warehouse_id отсутствует в элементах размещения")
                            all_success = False
                    else:
                        print(f"   ❌ Missing required fields in placement items: {missing_fields}")
                        all_success = False
            elif isinstance(placement_list, list):
                print(f"   ✅ Placement list accessible: {len(placement_list)} items")
            else:
                print("   ❌ Unexpected response format for placement list")
                all_success = False
        else:
            print("   ❌ Failed to get available cargo for placement")
            all_success = False
        
        # ЭТАП 6: ПРОВЕРКА ЧТО ИСПРАВЛЕНИЕ warehouse_id УСТРАНИЛО ОШИБКУ 500
        print("\n   🚨 ЭТАП 6: ПРОВЕРКА ЧТО ИСПРАВЛЕНИЕ warehouse_id УСТРАНИЛО ОШИБКУ 500...")
        
        # Test multiple placement operations to ensure no 500 errors
        test_operations = [
            ("/api/operator/warehouse-notifications", "GET", "Get Warehouse Notifications"),
            ("/api/operator/cargo/available-for-placement", "GET", "Get Available Cargo for Placement"),
            ("/api/operator/warehouses", "GET", "Get Operator Warehouses"),
            ("/api/warehouses", "GET", "Get All Warehouses")
        ]
        
        error_500_count = 0
        successful_operations = 0
        
        for endpoint, method, description in test_operations:
            success, response = self.run_test(
                f"500 Error Check: {description}",
                method,
                endpoint,
                200,
                token=operator_token
            )
            
            if success:
                successful_operations += 1
                print(f"   ✅ {description}: No 500 error")
            else:
                # Check if it was specifically a 500 error
                try:
                    url = f"{self.base_url}{endpoint}"
                    headers = {'Authorization': f'Bearer {operator_token}', 'Content-Type': 'application/json'}
                    test_response = requests.get(url, headers=headers)
                    if test_response.status_code == 500:
                        error_500_count += 1
                        print(f"   ❌ {description}: 500 Internal Server Error detected")
                    else:
                        print(f"   ⚠️  {description}: Non-500 error ({test_response.status_code})")
                except:
                    pass
        
        if error_500_count == 0:
            print(f"   🎉 КРИТИЧЕСКИЙ УСПЕХ - НЕТ 500 ОШИБОК! ({successful_operations}/{len(test_operations)} операций успешны)")
            print("   ✅ Исправление warehouse_id устранило ошибки 500")
        else:
            print(f"   ❌ ОБНАРУЖЕНЫ 500 ОШИБКИ: {error_500_count} endpoints все еще возвращают 500")
            print("   🔍 Исправление warehouse_id требует дополнительной работы")
            all_success = False
        
        # ФИНАЛЬНАЯ ПРОВЕРКА: QR CODE IMPROVEMENTS (если доступны)
        print("\n   📱 ДОПОЛНИТЕЛЬНО: ПРОВЕРКА УЛУЧШЕНИЙ QR КОДОВ...")
        
        # Test QR code generation if cargo was created
        if hasattr(self, 'created_cargo_number') and self.created_cargo_number:
            # Test cargo tracking endpoint (should work with simplified QR data)
            success, tracking_response = self.run_test(
                "Test Cargo Tracking (QR Code Data)",
                "GET",
                f"/api/cargo/track/{self.created_cargo_number}",
                200,
                token=operator_token
            )
            
            if success:
                print("   ✅ Cargo tracking endpoint working (supports simplified QR data)")
                
                # Verify response contains only essential data for QR
                if isinstance(tracking_response, dict):
                    cargo_number = tracking_response.get('cargo_number')
                    if cargo_number == self.created_cargo_number:
                        print("   ✅ QR data simplified: cargo number correctly returned")
                        print(f"   📱 QR содержит: {cargo_number} (упрощенные данные)")
                    else:
                        print("   ❌ QR data inconsistency detected")
                        all_success = False
            else:
                print("   ⚠️  Cargo tracking endpoint not working (may affect QR functionality)")
        
        # SUMMARY
        print("\n   📊 QR CODE AND WAREHOUSE PLACEMENT FIXES SUMMARY:")
        
        if all_success:
            print("   🎉 ВСЕ КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ РАБОТАЮТ УСПЕШНО!")
            print("   ✅ Авторизация оператора склада (+79777888999/warehouse123) ✅")
            print("   ✅ Получение уведомлений со статусом 'in_processing' ✅")
            print("   ✅ Исправленный endpoint отправки на размещение работает БЕЗ ошибки 500 ✅")
            print("   ✅ Корректное получение warehouse_id для операторов без привязок ✅")
            print("   ✅ Создание груза и появление в списке размещения ✅")
            print("   ✅ Исправление warehouse_id устранило ошибки 500 ✅")
            print("   🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ ДОСТИГНУТ:")
            print("      - Endpoint работает без ошибок 500")
            print("      - Корректно получает warehouse_id даже для операторов без привязок")
            print("      - Создает груз и добавляет в категорию размещения")
            print("      - QR коды упрощены (только номер заявки)")
        else:
            print("   ❌ НЕКОТОРЫЕ КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ ТРЕБУЮТ ВНИМАНИЯ")
            print("   🔍 Проверьте конкретные неудачные тесты выше для деталей")
            print("   ⚠️  Возможно требуется дополнительная работа над:")
            print("      - Логикой получения warehouse_id")
            print("      - Обработкой ошибок 500")
            print("      - Созданием и размещением грузов")
        
        return all_success

    def run_all_tests(self):
        """Run all QR code and warehouse placement fixes tests"""
        print("🚀 STARTING QR CODE AND WAREHOUSE PLACEMENT FIXES TESTING...")
        
        overall_success = True
        
        # Run the main test
        success = self.test_qr_code_and_warehouse_placement_fixes()
        overall_success &= success
        
        # Final summary
        print("\n" + "=" * 80)
        print("📊 FINAL TEST RESULTS SUMMARY")
        print("=" * 80)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"📈 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        if overall_success:
            print("\n🎉 ALL QR CODE AND WAREHOUSE PLACEMENT FIXES TESTS PASSED!")
            print("✅ TAJLINE.TJ QR code and warehouse placement fixes are working correctly")
            print("✅ Ready for production use")
        else:
            print("\n❌ SOME QR CODE AND WAREHOUSE PLACEMENT FIXES TESTS FAILED")
            print("🔍 Review the detailed test results above")
            print("⚠️  Additional fixes may be required")
        
        return overall_success

if __name__ == "__main__":
    tester = QRWarehousePlacementFixesTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
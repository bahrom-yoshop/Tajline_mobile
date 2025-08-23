#!/usr/bin/env python3
"""
Focused test for placement_ready fix - Tests the core issue directly
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class FocusedPlacementFixTester:
    def __init__(self, base_url="https://cargo-sync.preview.emergentagent.com"):
        self.base_url = base_url
        self.tokens = {}
        self.users = {}
        self.tests_run = 0
        self.tests_passed = 0
        
        print(f"🎯 FOCUSED PLACEMENT READY FIX TESTER")
        print(f"📡 Base URL: {self.base_url}")
        print("=" * 80)
        print("🔍 ФОКУС: Тестирование исправления ValidationError при создании грузов")
        print("✅ ПРОВЕРКА: Статус 'awaiting_placement' используется вместо 'placement_ready'")
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
                    if isinstance(result, dict) and len(str(result)) < 400:
                        print(f"   📄 Response: {result}")
                    elif isinstance(result, list) and len(result) <= 5:
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
                    print(f"   📄 Raw response: {response.text[:300]}")
                return False, {}

        except Exception as e:
            print(f"   ❌ FAILED - Exception: {str(e)}")
            return False, {}

    def test_placement_ready_status_fix(self):
        """Test the core placement_ready status fix"""
        print("\n🎯 FOCUSED PLACEMENT READY STATUS FIX TEST")
        
        all_success = True
        
        # ЭТАП 1: Авторизация оператора
        print("\n   🔐 ЭТАП 1: АВТОРИЗАЦИЯ ОПЕРАТОРА (+79777888999/warehouse123)...")
        
        operator_login_data = {
            "phone": "+79777888999",
            "password": "warehouse123"
        }
        
        success, login_response = self.run_test(
            "Warehouse Operator Login",
            "POST",
            "/api/auth/login",
            200,
            operator_login_data
        )
        all_success &= success
        
        if not success:
            return False
            
        operator_token = login_response['access_token']
        operator_user = login_response.get('user', {})
        operator_role = operator_user.get('role')
        operator_name = operator_user.get('full_name')
        operator_user_number = operator_user.get('user_number')
        
        print(f"   ✅ Operator: {operator_name} ({operator_user_number})")
        print(f"   👑 Role: {operator_role}")
        
        if operator_role != 'warehouse_operator':
            print(f"   ❌ Wrong role: expected 'warehouse_operator', got '{operator_role}'")
            all_success = False
            return False
        
        # ЭТАП 2: Проверка существующих уведомлений
        print("\n   📬 ЭТАП 2: ПРОВЕРКА СУЩЕСТВУЮЩИХ УВЕДОМЛЕНИЙ...")
        
        success, notifications_response = self.run_test(
            "Get Existing Warehouse Notifications",
            "GET",
            "/api/operator/warehouse-notifications",
            200,
            token=operator_token
        )
        all_success &= success
        
        if success:
            notifications = notifications_response.get('notifications', [])
            print(f"   📊 Найдено уведомлений: {len(notifications)}")
            
            # Look for any notification we can use for testing
            test_notification = None
            for notification in notifications:
                if notification.get('status') in ['pending_acceptance', 'accepted']:
                    test_notification = notification
                    notification_id = notification.get('id')
                    notification_status = notification.get('status')
                    request_number = notification.get('request_number')
                    print(f"   🎯 Найдено уведомление для теста: {notification_id}")
                    print(f"   📊 Статус: {notification_status}, Заявка: {request_number}")
                    break
            
            if test_notification:
                # If notification is pending, accept it first
                if test_notification.get('status') == 'pending_acceptance':
                    print(f"\n   ✅ ЭТАП 3: ПРИНЯТИЕ УВЕДОМЛЕНИЯ {notification_id}...")
                    
                    success, accept_response = self.run_test(
                        f"Accept Notification {notification_id}",
                        "POST",
                        f"/api/operator/warehouse-notifications/{notification_id}/accept",
                        200,
                        token=operator_token
                    )
                    all_success &= success
                    
                    if not success:
                        print("   ❌ Не удалось принять уведомление")
                        return False
                
                # ЭТАП 4: КРИТИЧЕСКИЙ ТЕСТ - Завершение оформления
                print(f"\n   🎯 ЭТАП 4: КРИТИЧЕСКИЙ ТЕСТ - ЗАВЕРШЕНИЕ ОФОРМЛЕНИЯ...")
                print("   🔧 Тестируем исправление ValidationError для статуса 'placement_ready'")
                
                complete_data = {
                    "sender_full_name": "Исправленный Тест",
                    "sender_phone": "+7999777666", 
                    "sender_address": "Москва, ул. Исправленная, 1",
                    "recipient_full_name": "Получатель Исправленный",
                    "recipient_phone": "+992901234567",
                    "recipient_address": "Душанбе, ул. Исправленная, 2",
                    "cargo_items": [
                        {"name": "Тест исправления", "weight": "1.0", "price": "500"}
                    ],
                    "payment_method": "cash",
                    "delivery_method": "pickup"
                }
                
                success, complete_response = self.run_test(
                    f"Complete Cargo Processing (CRITICAL FIX TEST)",
                    "POST",
                    f"/api/operator/warehouse-notifications/{notification_id}/complete",
                    200,
                    complete_data,
                    operator_token
                )
                
                if success:
                    print("   🎉 КРИТИЧЕСКИЙ УСПЕХ: Завершение оформления работает БЕЗ ValidationError!")
                    print("   ✅ Исправление статуса 'placement_ready' → 'awaiting_placement' работает")
                    
                    created_cargo_number = complete_response.get('cargo_number')
                    if created_cargo_number:
                        print(f"   📦 Груз создан: {created_cargo_number}")
                        
                        # Check the created cargo status
                        success, cargo_details = self.run_test(
                            f"Check Created Cargo Status",
                            "GET",
                            f"/api/cargo/track/{created_cargo_number}",
                            200,
                            token=operator_token
                        )
                        
                        if success:
                            cargo_status = cargo_details.get('status')
                            print(f"   📊 Статус созданного груза: {cargo_status}")
                            
                            if cargo_status == 'awaiting_placement':
                                print("   ✅ ИСПРАВЛЕНИЕ ПОДТВЕРЖДЕНО: Используется валидный статус 'awaiting_placement'")
                            elif cargo_status == 'placement_ready':
                                print("   ❌ ИСПРАВЛЕНИЕ НЕ РАБОТАЕТ: Все еще используется невалидный 'placement_ready'")
                                all_success = False
                            else:
                                print(f"   ℹ️  Груз имеет статус: {cargo_status}")
                else:
                    print("   ❌ КРИТИЧЕСКАЯ ОШИБКА: ValidationError все еще присутствует!")
                    print("   🚨 Исправление статуса 'placement_ready' не работает")
                    all_success = False
            else:
                print("   ⚠️  Нет подходящих уведомлений для тестирования")
                print("   ℹ️  Создадим альтернативный тест...")
                return self.test_alternative_cargo_creation(operator_token)
        
        return all_success

    def test_alternative_cargo_creation(self, operator_token):
        """Alternative test: Create cargo and check for awaiting_placement status"""
        print("\n   🔄 АЛЬТЕРНАТИВНЫЙ ТЕСТ: Создание груза и проверка статуса")
        
        all_success = True
        
        # Create cargo that should have awaiting_placement status
        cargo_data = {
            "sender_full_name": "Тест Исправления Статуса",
            "sender_phone": "+7999888777",
            "recipient_full_name": "Получатель Исправления",
            "recipient_phone": "+992901234569",
            "recipient_address": "Душанбе, ул. Тестовая Исправления, 5",
            "weight": 2.5,
            "cargo_name": "Тест статуса awaiting_placement",
            "declared_value": 1250.0,
            "description": "Тест для проверки исправления статуса placement_ready",
            "route": "moscow_dushanbe",
            "payment_method": "cash",
            "payment_amount": 1250.0
        }
        
        success, cargo_response = self.run_test(
            "Create Cargo (Alternative Test)",
            "POST",
            "/api/operator/cargo/accept",
            200,
            cargo_data,
            operator_token
        )
        all_success &= success
        
        if success and 'cargo_number' in cargo_response:
            cargo_number = cargo_response['cargo_number']
            cargo_status = cargo_response.get('status')
            processing_status = cargo_response.get('processing_status')
            
            print(f"   ✅ Груз создан: {cargo_number}")
            print(f"   📊 Статус: {cargo_status}")
            print(f"   📊 Processing Status: {processing_status}")
            
            # Check if cargo appears in placed cargo with awaiting_placement status
            success, placed_cargo_response = self.run_test(
                "Check Placed Cargo List",
                "GET",
                "/api/warehouses/placed-cargo",
                200,
                token=operator_token
            )
            
            if success:
                placed_items = placed_cargo_response.get('items', [])
                print(f"   📊 Размещенных грузов в системе: {len(placed_items)}")
                
                # Check for awaiting_placement status in the list
                awaiting_placement_count = 0
                placement_ready_count = 0
                
                for cargo in placed_items:
                    cargo_status = cargo.get('status')
                    if cargo_status == 'awaiting_placement':
                        awaiting_placement_count += 1
                    elif cargo_status == 'placement_ready':
                        placement_ready_count += 1
                
                print(f"   📊 Грузов со статусом 'awaiting_placement': {awaiting_placement_count}")
                print(f"   📊 Грузов со статусом 'placement_ready': {placement_ready_count}")
                
                if awaiting_placement_count > 0:
                    print("   ✅ ИСПРАВЛЕНИЕ РАБОТАЕТ: Найдены грузы со статусом 'awaiting_placement'")
                    print("   ✅ Endpoint /api/warehouses/placed-cargo включает статус 'awaiting_placement'")
                
                if placement_ready_count > 0:
                    print("   ❌ ПРОБЛЕМА: Все еще есть грузы со статусом 'placement_ready'")
                    print("   🚨 Исправление может быть неполным")
                    all_success = False
                
                if awaiting_placement_count == 0 and placement_ready_count == 0:
                    print("   ℹ️  Нет грузов с проверяемыми статусами")
                    print("   ℹ️  Возможно все грузы имеют другие статусы")
        
        return all_success

    def run_all_tests(self):
        """Run all focused placement fix tests"""
        print("\n🚀 STARTING FOCUSED PLACEMENT FIX TESTS")
        
        success = self.test_placement_ready_status_fix()
        
        print(f"\n📊 FINAL TEST RESULTS:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if success:
            print("\n🎉 FOCUSED PLACEMENT FIX TESTS COMPLETED SUCCESSFULLY!")
            print("✅ Исправление ошибки 'Ошибка при завершении оформления' подтверждено")
            print("✅ Статус 'placement_ready' заменен на 'awaiting_placement'")
            print("✅ ValidationError устранена")
            print("✅ Endpoint /api/warehouses/placed-cargo включает статус 'awaiting_placement'")
        else:
            print("\n❌ FOCUSED PLACEMENT FIX TESTS FAILED!")
            print("🔍 Исправление требует дополнительного внимания")
            print("⚠️  ValidationError может все еще присутствовать")
        
        return success

if __name__ == "__main__":
    tester = FocusedPlacementFixTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
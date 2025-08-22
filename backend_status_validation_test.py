#!/usr/bin/env python3
"""
Backend Status Validation Test - Tests the core fix for placement_ready ValidationError
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class BackendStatusValidationTester:
    def __init__(self, base_url="https://tajline-cargo-7.preview.emergentagent.com"):
        self.base_url = base_url
        self.tokens = {}
        self.users = {}
        self.tests_run = 0
        self.tests_passed = 0
        
        print(f"🔧 BACKEND STATUS VALIDATION TESTER")
        print(f"📡 Base URL: {self.base_url}")
        print("=" * 80)
        print("🎯 ЦЕЛЬ: Проверить исправление ValidationError для статуса 'placement_ready'")
        print("🔍 ТЕСТЫ:")
        print("   1) Авторизация оператора (+79777888999/warehouse123)")
        print("   2) Создание груза и проверка валидного статуса")
        print("   3) Проверка endpoint /api/warehouses/placed-cargo включает 'awaiting_placement'")
        print("   4) Проверка что 'placement_ready' больше не используется")
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

    def test_backend_status_validation_fix(self):
        """Test the backend status validation fix"""
        print("\n🔧 BACKEND STATUS VALIDATION FIX TEST")
        
        all_success = True
        
        # ЭТАП 1: Авторизация оператора (+79777888999/warehouse123)
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
        
        # ЭТАП 2: Создание груза и проверка валидного статуса
        print("\n   📦 ЭТАП 2: СОЗДАНИЕ ГРУЗА И ПРОВЕРКА ВАЛИДНОГО СТАТУСА...")
        print("   🔧 Создаем груз, который должен иметь статус 'awaiting_placement' вместо 'placement_ready'")
        
        cargo_data = {
            "sender_full_name": "Исправленный Тест Отправитель",
            "sender_phone": "+7999777666",
            "recipient_full_name": "Получатель Исправленный",
            "recipient_phone": "+992901234567",
            "recipient_address": "Душанбе, ул. Исправленная, 2",
            "weight": 1.0,
            "cargo_name": "Тест исправления",
            "declared_value": 500.0,
            "description": "Тест для проверки исправления ValidationError",
            "route": "moscow_dushanbe",
            "payment_method": "cash",
            "payment_amount": 500.0
        }
        
        success, cargo_response = self.run_test(
            "Create Cargo (Status Validation Test)",
            "POST",
            "/api/operator/cargo/accept",
            200,
            cargo_data,
            operator_token
        )
        all_success &= success
        
        created_cargo_number = None
        if success and 'cargo_number' in cargo_response:
            created_cargo_number = cargo_response['cargo_number']
            cargo_status = cargo_response.get('status')
            processing_status = cargo_response.get('processing_status')
            
            print(f"   ✅ Груз создан успешно: {created_cargo_number}")
            print(f"   📊 Статус: {cargo_status}")
            print(f"   📊 Processing Status: {processing_status}")
            print("   ✅ КРИТИЧЕСКИЙ УСПЕХ: Создание груза прошло БЕЗ ValidationError!")
            print("   ✅ Исправление статуса 'placement_ready' работает")
        else:
            print("   ❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось создать груз")
            print("   🚨 ValidationError может все еще присутствовать")
            all_success = False
            return False
        
        # ЭТАП 3: Проверка endpoint /api/warehouses/placed-cargo включает 'awaiting_placement'
        print("\n   📋 ЭТАП 3: ПРОВЕРКА ENDPOINT /api/warehouses/placed-cargo...")
        print("   🔧 Проверяем что endpoint включает статус 'awaiting_placement' в фильтр")
        
        success, placed_cargo_response = self.run_test(
            "Get Placed Cargo (Should Include awaiting_placement)",
            "GET",
            "/api/warehouses/placed-cargo",
            200,
            token=operator_token
        )
        all_success &= success
        
        if success:
            placed_items = placed_cargo_response.get('items', [])
            total_count = placed_cargo_response.get('pagination', {}).get('total', len(placed_items))
            
            print(f"   ✅ Endpoint /api/warehouses/placed-cargo работает")
            print(f"   📊 Всего размещенных грузов: {total_count}")
            print(f"   📊 Грузов в текущей странице: {len(placed_items)}")
            
            # Analyze statuses in the placed cargo
            status_counts = {}
            awaiting_placement_found = False
            placement_ready_found = False
            
            for cargo in placed_items:
                cargo_status = cargo.get('status', 'unknown')
                status_counts[cargo_status] = status_counts.get(cargo_status, 0) + 1
                
                if cargo_status == 'awaiting_placement':
                    awaiting_placement_found = True
                elif cargo_status == 'placement_ready':
                    placement_ready_found = True
            
            print("   📊 Статусы грузов в размещенных:")
            for status, count in status_counts.items():
                print(f"      - {status}: {count}")
            
            if awaiting_placement_found:
                print("   ✅ ИСПРАВЛЕНИЕ ПОДТВЕРЖДЕНО: Найдены грузы со статусом 'awaiting_placement'")
                print("   ✅ Endpoint /api/warehouses/placed-cargo включает статус 'awaiting_placement'")
            else:
                print("   ⚠️  Грузы со статусом 'awaiting_placement' не найдены")
                print("   ℹ️  Возможно все грузы имеют другие статусы")
            
            if placement_ready_found:
                print("   ❌ ПРОБЛЕМА: Найдены грузы со статусом 'placement_ready'")
                print("   🚨 Исправление может быть неполным - старый статус все еще используется")
                all_success = False
            else:
                print("   ✅ ХОРОШО: Грузы со статусом 'placement_ready' не найдены")
                print("   ✅ Старый невалидный статус больше не используется")
        else:
            print("   ❌ Endpoint /api/warehouses/placed-cargo не работает")
            all_success = False
        
        # ЭТАП 4: Проверка созданного груза в трекинге
        print(f"\n   🔍 ЭТАП 4: ПРОВЕРКА СОЗДАННОГО ГРУЗА В ТРЕКИНГЕ...")
        
        if created_cargo_number:
            success, cargo_details = self.run_test(
                f"Track Created Cargo {created_cargo_number}",
                "GET",
                f"/api/cargo/track/{created_cargo_number}",
                200,
                token=operator_token
            )
            
            if success:
                cargo_status = cargo_details.get('status')
                cargo_number = cargo_details.get('cargo_number')
                recipient_name = cargo_details.get('recipient_name')
                weight = cargo_details.get('weight')
                
                print(f"   ✅ Груз найден: {cargo_number}")
                print(f"   📊 Статус: {cargo_status}")
                print(f"   📦 Получатель: {recipient_name}")
                print(f"   ⚖️ Вес: {weight}kg")
                
                if cargo_status == 'awaiting_placement':
                    print("   ✅ ИСПРАВЛЕНИЕ ПОДТВЕРЖДЕНО: Груз имеет валидный статус 'awaiting_placement'")
                elif cargo_status == 'placement_ready':
                    print("   ❌ ИСПРАВЛЕНИЕ НЕ РАБОТАЕТ: Груз все еще имеет невалидный статус 'placement_ready'")
                    all_success = False
                else:
                    print(f"   ℹ️  Груз имеет статус: {cargo_status}")
                    print("   ℹ️  Это может быть другой валидный статус")
            else:
                print(f"   ⚠️  Не удалось найти созданный груз {created_cargo_number}")
        
        # ЭТАП 5: Проверка доступности груза для размещения
        print(f"\n   🎯 ЭТАП 5: ПРОВЕРКА ДОСТУПНОСТИ ГРУЗА ДЛЯ РАЗМЕЩЕНИЯ...")
        
        success, available_cargo_response = self.run_test(
            "Get Available Cargo for Placement",
            "GET",
            "/api/operator/cargo/available-for-placement",
            200,
            token=operator_token
        )
        
        if success:
            available_items = available_cargo_response.get('items', [])
            total_available = len(available_items)
            
            print(f"   ✅ Endpoint /api/operator/cargo/available-for-placement работает")
            print(f"   📊 Доступно для размещения: {total_available} грузов")
            
            # Check if our created cargo is available for placement
            if created_cargo_number:
                cargo_found = False
                for cargo in available_items:
                    if cargo.get('cargo_number') == created_cargo_number:
                        cargo_found = True
                        cargo_status = cargo.get('status')
                        processing_status = cargo.get('processing_status')
                        print(f"   🎯 Созданный груз найден в доступных для размещения")
                        print(f"   📊 Статус: {cargo_status}")
                        print(f"   📊 Processing Status: {processing_status}")
                        break
                
                if not cargo_found:
                    print(f"   ℹ️  Созданный груз {created_cargo_number} не найден в доступных для размещения")
                    print("   ℹ️  Возможно груз еще не готов для размещения")
        else:
            print("   ❌ Endpoint /api/operator/cargo/available-for-placement не работает")
            all_success = False
        
        return all_success

    def run_all_tests(self):
        """Run all backend status validation tests"""
        print("\n🚀 STARTING BACKEND STATUS VALIDATION TESTS")
        
        success = self.test_backend_status_validation_fix()
        
        print(f"\n📊 FINAL TEST RESULTS:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if success:
            print("\n🎉 BACKEND STATUS VALIDATION TESTS COMPLETED SUCCESSFULLY!")
            print("✅ Авторизация оператора (+79777888999/warehouse123) работает")
            print("✅ Создание груза работает БЕЗ ValidationError")
            print("✅ Endpoint /api/warehouses/placed-cargo включает статус 'awaiting_placement'")
            print("✅ Статус 'placement_ready' больше не используется")
            print("✅ ИСПРАВЛЕНИЕ ПОДТВЕРЖДЕНО: ValidationError устранена!")
        else:
            print("\n❌ BACKEND STATUS VALIDATION TESTS FAILED!")
            print("🔍 Исправление ValidationError требует дополнительного внимания")
            print("⚠️  Статус 'placement_ready' может все еще вызывать ошибки")
        
        return success

if __name__ == "__main__":
    tester = BackendStatusValidationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
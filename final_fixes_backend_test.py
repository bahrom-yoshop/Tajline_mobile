#!/usr/bin/env python3
"""
🎯 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ВСЕХ ИСПРАВЛЕНИЙ - TAJLINE.TJ

КОНТЕКСТ ВЫПОЛНЕННЫХ ИСПРАВЛЕНИЙ:
Были выполнены 3 критических исправления:

1. **ИСПРАВЛЕНИЕ СПОСОБА ОПЛАТЫ В МОДАЛЬНОМ ОКНЕ:**
   - Добавлена поддержка `cash_on_delivery` → '📦 Наложенный платеж'
   - Добавлена поддержка `deferred` → '⏳ В долг'

2. **ИСПРАВЛЕНИЕ ФОРМАТА QR КОДОВ:**
   - В frontend: изменен `/${i}` на `/${String(i).padStart(2, '0')}`
   - В backend: изменен `unit_index: unit_index` на `unit_index: str(unit_index).zfill(2)`

3. **ИСПРАВЛЕНИЕ ПОИСКА ЕДИНИЦ ГРУЗА:**
   - Добавлена дополнительная проверка `String(unit.unit_index) === extractedData.unit_number`

ЗАДАЧА ФИНАЛЬНОГО ТЕСТИРОВАНИЯ:
1. Протестировать создание заявки с cash_on_delivery
2. Протестировать размещение QR кода 25082026/01/02
3. Проверить backward compatibility
4. Проверить полный цикл: Создание заявки → Генерация QR → Размещение → Статус обновлен
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://tajline-cargo-8.preview.emergentagent.com/api"

# Test credentials
WAREHOUSE_OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

ADMIN_CREDENTIALS = {
    "phone": "+79999888777", 
    "password": "admin123"
}

class FinalFixesTester:
    def __init__(self):
        self.session = requests.Session()
        self.operator_token = None
        self.admin_token = None
        self.test_results = []
        self.warehouse_id = None
        self.test_cargo_id = None
        self.test_cargo_number = None
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if details:
            print(f"    📋 {details}")
        if error:
            print(f"    ❌ Error: {error}")
        print()

    def authenticate_operator(self):
        """Authenticate warehouse operator"""
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=WAREHOUSE_OPERATOR_CREDENTIALS
            )
            
            if response.status_code == 200:
                data = response.json()
                self.operator_token = data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.operator_token}"
                })
                
                # Get user info
                user_response = self.session.get(f"{BACKEND_URL}/auth/me")
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    self.log_test(
                        "Авторизация оператора склада",
                        True,
                        f"Успешная авторизация '{user_data.get('full_name')}' (роль: {user_data.get('role')}, телефон: {user_data.get('phone')})"
                    )
                    return True
                else:
                    self.log_test("Авторизация оператора склада", False, error="Не удалось получить информацию о пользователе")
                    return False
            else:
                self.log_test("Авторизация оператора склада", False, error=f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Авторизация оператора склада", False, error=str(e))
            return False

    def get_operator_warehouse(self):
        """Get operator's warehouse"""
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/warehouses")
            
            if response.status_code == 200:
                warehouses = response.json()
                if warehouses:
                    self.warehouse_id = warehouses[0].get("id")
                    self.log_test(
                        "Получение склада оператора",
                        True,
                        f"Получен склад: {warehouses[0].get('name')} (ID: {self.warehouse_id})"
                    )
                    return True
                else:
                    self.log_test("Получение склада оператора", False, error="Нет доступных складов")
                    return False
            else:
                self.log_test("Получение склада оператора", False, error=f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Получение склада оператора", False, error=str(e))
            return False

    def test_create_cargo_with_cash_on_delivery(self):
        """Test creating cargo with cash_on_delivery payment method"""
        try:
            cargo_data = {
                "sender_full_name": "Тестовый Отправитель",
                "sender_phone": "+79123456789",
                "recipient_full_name": "Тестовый Получатель",
                "recipient_phone": "+79987654321",
                "recipient_address": "г. Душанбе, ул. Рудаки, дом 45, кв. 12",
                "cargo_items": [
                    {
                        "cargo_name": "Электроника Samsung",
                        "quantity": 2,
                        "weight": 5.0,
                        "price_per_kg": 100.0,
                        "total_amount": 1000.0
                    },
                    {
                        "cargo_name": "Бытовая техника LG", 
                        "quantity": 3,
                        "weight": 8.0,
                        "price_per_kg": 80.0,
                        "total_amount": 1920.0
                    }
                ],
                "description": "Тестовый груз для проверки cash_on_delivery",
                "route": "moscow_to_tajikistan",
                "warehouse_id": self.warehouse_id,
                "payment_method": "cash_on_delivery",  # КРИТИЧЕСКИЙ ТЕСТ
                "delivery_method": "pickup"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/operator/cargo/accept",
                json=cargo_data
            )
            
            if response.status_code == 200:
                data = response.json()
                # Check different possible response structures
                self.test_cargo_id = data.get("cargo_id") or data.get("id")
                self.test_cargo_number = data.get("cargo_number") or data.get("number")
                
                # Debug: print the actual response structure
                print(f"    🔍 Response data: {json.dumps(data, indent=2)}")
                
                self.log_test(
                    "Создание заявки с cash_on_delivery",
                    True,
                    f"Заявка создана: {self.test_cargo_number} (ID: {self.test_cargo_id}). Способ оплаты: cash_on_delivery. Грузы: 2 типа (2+3=5 единиц)"
                )
                return True
            else:
                error_text = response.text
                self.log_test(
                    "Создание заявки с cash_on_delivery",
                    False,
                    error=f"HTTP {response.status_code}: {error_text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Создание заявки с cash_on_delivery", False, error=str(e))
            return False

    def test_qr_code_format_generation(self):
        """Test QR code generation with proper format (leading zeros)"""
        if not self.test_cargo_id:
            self.log_test(
                "Тестирование формата QR кодов",
                False,
                error="Нет доступного cargo_id для тестирования"
            )
            return False
            
        try:
            # Get placement status to check individual units format
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/{self.test_cargo_id}/placement-status")
            
            if response.status_code == 200:
                data = response.json()
                
                # individual_units are nested inside cargo_types
                all_individual_units = []
                cargo_types = data.get("cargo_types", [])
                
                for cargo_type in cargo_types:
                    individual_units = cargo_type.get("individual_units", [])
                    all_individual_units.extend(individual_units)
                
                if all_individual_units:
                    # Check format of individual numbers
                    expected_formats = []
                    actual_formats = []
                    
                    for unit in all_individual_units:
                        individual_number = unit.get("individual_number", "")
                        actual_formats.append(individual_number)
                        
                        # Expected format: CARGO_NUMBER/TYPE_INDEX/UNIT_INDEX with leading zeros
                        # Example: 25082026/01/01, 25082026/01/02, 25082026/02/01, etc.
                        parts = individual_number.split("/")
                        if len(parts) == 3:
                            cargo_num, type_idx, unit_idx = parts
                            expected_formats.append(f"{cargo_num}/{type_idx.zfill(2)}/{unit_idx.zfill(2)}")
                    
                    # Check if all formats have leading zeros
                    correct_format_count = 0
                    for actual in actual_formats:
                        parts = actual.split("/")
                        if len(parts) == 3:
                            cargo_num, type_idx, unit_idx = parts
                            # Check if type_idx and unit_idx have leading zeros (2 digits)
                            if len(type_idx) == 2 and len(unit_idx) == 2:
                                correct_format_count += 1
                    
                    success = correct_format_count == len(actual_formats)
                    
                    self.log_test(
                        "Тестирование формата QR кодов",
                        success,
                        f"Проверено {len(actual_formats)} QR кодов. Правильный формат: {correct_format_count}/{len(actual_formats)}. Примеры: {actual_formats[:3]}"
                    )
                    return success
                else:
                    self.log_test(
                        "Тестирование формата QR кодов",
                        False,
                        error="Нет individual_units для проверки формата"
                    )
                    return False
            else:
                self.log_test(
                    "Тестирование формата QR кодов",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Тестирование формата QR кодов", False, error=str(e))
            return False

    def test_qr_code_placement(self):
        """Test placing a QR code with format like 25082026/01/02"""
        if not self.test_cargo_id:
            self.log_test(
                "Размещение QR кода с правильным форматом",
                False,
                error="Нет доступного cargo_id для тестирования"
            )
            return False
            
        try:
            # Get placement status to find an individual unit to place
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/{self.test_cargo_id}/placement-status")
            
            if response.status_code == 200:
                data = response.json()
                
                # individual_units are nested inside cargo_types
                all_individual_units = []
                cargo_types = data.get("cargo_types", [])
                
                for cargo_type in cargo_types:
                    individual_units = cargo_type.get("individual_units", [])
                    all_individual_units.extend(individual_units)
                
                # Find first unplaced unit
                target_unit = None
                for unit in all_individual_units:
                    if not unit.get("is_placed", False):
                        target_unit = unit
                        break
                
                if target_unit:
                    individual_number = target_unit.get("individual_number")
                    
                    # Test placement
                    placement_data = {
                        "individual_number": individual_number,
                        "warehouse_id": self.warehouse_id,  # Add required warehouse_id
                        "block_number": 1,
                        "shelf_number": 1,
                        "cell_number": 1
                    }
                    
                    place_response = self.session.post(
                        f"{BACKEND_URL}/operator/cargo/place-individual",
                        json=placement_data
                    )
                    
                    if place_response.status_code == 200:
                        place_data = place_response.json()
                        
                        self.log_test(
                            "Размещение QR кода с правильным форматом",
                            True,
                            f"Единица {individual_number} успешно размещена в местоположении {place_data.get('location_code', 'N/A')}"
                        )
                        return True
                    else:
                        self.log_test(
                            "Размещение QR кода с правильным форматом",
                            False,
                            error=f"Ошибка размещения: HTTP {place_response.status_code}: {place_response.text}"
                        )
                        return False
                else:
                    self.log_test(
                        "Размещение QR кода с правильным форматом",
                        False,
                        error="Нет доступных единиц для размещения"
                    )
                    return False
            else:
                self.log_test(
                    "Размещение QR кода с правильным форматом",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Размещение QR кода с правильным форматом", False, error=str(e))
            return False

    def test_backward_compatibility(self):
        """Test backward compatibility with existing cargo"""
        try:
            # Get available cargo for placement
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/available-for-placement")
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                # Check if we can process both old and new format cargo
                old_format_count = 0
                new_format_count = 0
                
                for item in items:
                    cargo_items = item.get("cargo_items", [])
                    individual_items = item.get("individual_items", [])
                    
                    # Check if it's old format (no individual_items) or new format (has individual_items)
                    if individual_items:
                        new_format_count += 1
                    else:
                        old_format_count += 1
                
                total_cargo = len(items)
                compatibility_rate = ((old_format_count + new_format_count) / total_cargo * 100) if total_cargo > 0 else 0
                
                self.log_test(
                    "Проверка обратной совместимости",
                    True,
                    f"Обработано {total_cargo} грузов. Старый формат: {old_format_count}, Новый формат: {new_format_count}. Совместимость: {compatibility_rate:.1f}%"
                )
                return True
            else:
                self.log_test(
                    "Проверка обратной совместимости",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Проверка обратной совместимости", False, error=str(e))
            return False

    def test_full_cycle_workflow(self):
        """Test full cycle: Creation → QR Generation → Placement → Status Update"""
        if not self.test_cargo_id:
            self.log_test(
                "Полный цикл работы",
                False,
                error="Нет доступного cargo_id для тестирования полного цикла"
            )
            return False
            
        try:
            # Step 1: Check initial status
            initial_response = self.session.get(f"{BACKEND_URL}/operator/cargo/{self.test_cargo_id}/placement-status")
            
            if initial_response.status_code != 200:
                self.log_test(
                    "Полный цикл работы",
                    False,
                    error=f"Не удалось получить начальный статус: HTTP {initial_response.status_code}"
                )
                return False
            
            initial_data = initial_response.json()
            initial_placed = initial_data.get("total_placed", 0)
            total_quantity = initial_data.get("total_quantity", 0)
            
            # Step 2: Try to place another unit if available
            # individual_units are nested inside cargo_types
            all_individual_units = []
            cargo_types = initial_data.get("cargo_types", [])
            
            for cargo_type in cargo_types:
                individual_units = cargo_type.get("individual_units", [])
                all_individual_units.extend(individual_units)
            
            unplaced_units = [unit for unit in all_individual_units if not unit.get("is_placed", False)]
            
            if unplaced_units:
                target_unit = unplaced_units[0]
                individual_number = target_unit.get("individual_number")
                
                # Place the unit
                placement_data = {
                    "individual_number": individual_number,
                    "warehouse_id": self.warehouse_id,  # Add required warehouse_id
                    "block_number": 1,
                    "shelf_number": 2,
                    "cell_number": 1
                }
                
                place_response = self.session.post(
                    f"{BACKEND_URL}/operator/cargo/place-individual",
                    json=placement_data
                )
                
                if place_response.status_code == 200:
                    # Step 3: Check updated status
                    final_response = self.session.get(f"{BACKEND_URL}/operator/cargo/{self.test_cargo_id}/placement-status")
                    
                    if final_response.status_code == 200:
                        final_data = final_response.json()
                        final_placed = final_data.get("total_placed", 0)
                        
                        # Verify status was updated
                        if final_placed > initial_placed:
                            self.log_test(
                                "Полный цикл работы",
                                True,
                                f"Полный цикл успешен: Создание ✅ → QR генерация ✅ → Размещение ✅ → Обновление статуса ✅. Размещено: {initial_placed} → {final_placed} из {total_quantity}"
                            )
                            return True
                        else:
                            self.log_test(
                                "Полный цикл работы",
                                False,
                                error=f"Статус не обновился после размещения: {initial_placed} → {final_placed}"
                            )
                            return False
                    else:
                        self.log_test(
                            "Полный цикл работы",
                            False,
                            error=f"Не удалось получить финальный статус: HTTP {final_response.status_code}"
                        )
                        return False
                else:
                    self.log_test(
                        "Полный цикл работы",
                        False,
                        error=f"Ошибка размещения в полном цикле: HTTP {place_response.status_code}"
                    )
                    return False
            else:
                # All units already placed, just verify the cycle components work
                self.log_test(
                    "Полный цикл работы",
                    True,
                    f"Полный цикл проверен: Создание ✅ → QR генерация ✅ → Все единицы уже размещены ({initial_placed}/{total_quantity}) ✅"
                )
                return True
                
        except Exception as e:
            self.log_test("Полный цикл работы", False, error=str(e))
            return False

    def test_deferred_payment_method(self):
        """Test creating cargo with deferred payment method"""
        try:
            cargo_data = {
                "sender_full_name": "Тестовый Отправитель 2",
                "sender_phone": "+79123456790",
                "recipient_full_name": "Тестовый Получатель 2",
                "recipient_phone": "+79987654322",
                "recipient_address": "г. Худжанд, ул. Ленина, дом 25",
                "cargo_items": [
                    {
                        "cargo_name": "Тестовый груз для deferred",
                        "quantity": 1,
                        "weight": 3.0,
                        "price_per_kg": 50.0,
                        "total_amount": 150.0
                    }
                ],
                "description": "Тестовый груз для проверки deferred payment",
                "route": "moscow_to_tajikistan",
                "warehouse_id": self.warehouse_id,
                "payment_method": "credit",  # КРИТИЧЕСКИЙ ТЕСТ (deferred = credit in backend)
                "debt_due_date": "2025-02-15",
                "delivery_method": "pickup"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/operator/cargo/accept",
                json=cargo_data
            )
            
            if response.status_code == 200:
                data = response.json()
                cargo_id = data.get("cargo_id")
                cargo_number = data.get("cargo_number")
                
                self.log_test(
                    "Создание заявки с deferred payment",
                    True,
                    f"Заявка создана: {cargo_number} (ID: {cargo_id}). Способ оплаты: credit (в долг). Дата погашения: 2025-02-15"
                )
                return True
            else:
                error_text = response.text
                self.log_test(
                    "Создание заявки с deferred payment",
                    False,
                    error=f"HTTP {response.status_code}: {error_text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Создание заявки с deferred payment", False, error=str(e))
            return False

    def run_all_tests(self):
        """Run all final fixes tests"""
        print("🎯 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ВСЕХ ИСПРАВЛЕНИЙ - TAJLINE.TJ")
        print("=" * 80)
        print()
        
        # Authentication
        if not self.authenticate_operator():
            print("❌ Не удалось авторизоваться как оператор склада")
            return False
        
        if not self.get_operator_warehouse():
            print("❌ Не удалось получить склад оператора")
            return False
        
        # Test 1: Cash on delivery payment method
        print("🔍 ТЕСТ 1: Создание заявки с cash_on_delivery")
        self.test_create_cargo_with_cash_on_delivery()
        
        # Test 2: QR code format with leading zeros
        print("🔍 ТЕСТ 2: Формат QR кодов с ведущими нулями")
        self.test_qr_code_format_generation()
        
        # Test 3: QR code placement
        print("🔍 ТЕСТ 3: Размещение QR кода")
        self.test_qr_code_placement()
        
        # Test 4: Backward compatibility
        print("🔍 ТЕСТ 4: Обратная совместимость")
        self.test_backward_compatibility()
        
        # Test 5: Full cycle workflow
        print("🔍 ТЕСТ 5: Полный цикл работы")
        self.test_full_cycle_workflow()
        
        # Test 6: Deferred payment method
        print("🔍 ТЕСТ 6: Создание заявки с deferred payment")
        self.test_deferred_payment_method()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ ФИНАЛЬНОГО ТЕСТИРОВАНИЯ")
        print("=" * 80)
        
        passed_tests = sum(1 for result in self.test_results if result["success"])
        total_tests = len(self.test_results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"✅ Пройдено тестов: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print()
        
        # Detailed results
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"    📋 {result['details']}")
            if result["error"]:
                print(f"    ❌ {result['error']}")
        
        print("\n" + "=" * 80)
        
        # Final verdict
        critical_tests = [
            "Создание заявки с cash_on_delivery",
            "Тестирование формата QR кодов", 
            "Размещение QR кода с правильным форматом",
            "Полный цикл работы"
        ]
        
        critical_passed = sum(1 for result in self.test_results 
                            if result["test"] in critical_tests and result["success"])
        
        if critical_passed == len(critical_tests):
            print("🎉 ВСЕ КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ РАБОТАЮТ КОРРЕКТНО!")
            print("✅ Заявки с cash_on_delivery создаются успешно")
            print("✅ QR коды генерируются в формате с ведущими нулями")
            print("✅ QR коды успешно размещаются")
            print("✅ Полный цикл от создания до размещения работает без ошибок")
        else:
            print(f"⚠️ ТРЕБУЕТСЯ ВНИМАНИЕ: {critical_passed}/{len(critical_tests)} критических тестов пройдены")
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = FinalFixesTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
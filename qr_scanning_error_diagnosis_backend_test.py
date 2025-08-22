#!/usr/bin/env python3
"""
🎯 ДИАГНОСТИКА ОШИБКИ СКАНИРОВАНИЯ QR КОДА: 25082026/01/02

КОНТЕКСТ ПРОБЛЕМЫ:
Пользователь сообщает об ошибке при сканировании QR кода для размещения груза:
- Номер заявки: 25082026
- QR код для сканирования: 25082026/01/02
- Ошибка: "Единица 02 груза типа 01 из заявки 25082026 не найдена"

СИМПТОМЫ ИЗ СКРИНШОТА:
1. В разделе "Размещение" показано 18 грузов для размещения
2. QR код 25082026/01/02 корректно распознается системой как ТИП 3 (единица груза внутри типа)
3. Система ищет: заявка 25082026 → груз типа 01 → единица 02
4. Но выдает ошибку что единица не найдена

ЗАДАЧА ДИАГНОСТИКИ:
1. **Проверить существование заявки 25082026**
2. **Проверить структуру cargo_items**
3. **Проверить individual_items**
4. **Проверить API endpoint**
5. **Проверить совместимость форматов**
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://tajline-cargo-7.preview.emergentagent.com/api"

# Test credentials
WAREHOUSE_OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class QRScanningErrorDiagnoser:
    def __init__(self):
        self.session = requests.Session()
        self.operator_token = None
        self.test_results = []
        self.target_cargo_number = "25082026"
        self.target_qr_code = "25082026/01/02"
        self.found_cargo = None
        
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
        
        status = "✅ НАЙДЕНО" if success else "❌ НЕ НАЙДЕНО"
        print(f"{status} - {test_name}")
        if details:
            print(f"    📋 {details}")
        if error:
            print(f"    ❌ Ошибка: {error}")
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
                self.log_test("Авторизация оператора склада", False, error=f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Авторизация оператора склада", False, error=str(e))
            return False

    def check_cargo_exists_in_placement_list(self):
        """1. Проверить существование заявки 25082026 в списке для размещения"""
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/available-for-placement")
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                pagination = data.get("pagination", {})
                total_count = pagination.get("total_count", 0)
                
                # Поиск заявки 25082026
                target_cargo = None
                for item in items:
                    if item.get("cargo_number") == self.target_cargo_number:
                        target_cargo = item
                        self.found_cargo = item
                        break
                
                if target_cargo:
                    cargo_items = target_cargo.get("cargo_items", [])
                    individual_items = []
                    for cargo_item in cargo_items:
                        individual_items.extend(cargo_item.get("individual_items", []))
                    
                    self.log_test(
                        f"Заявка {self.target_cargo_number} в списке размещения",
                        True,
                        f"Заявка найдена! ID: {target_cargo.get('id')}, cargo_items: {len(cargo_items)}, individual_items: {len(individual_items)} единиц. Всего грузов для размещения: {total_count}"
                    )
                    return True
                else:
                    # Показать все доступные номера для диагностики
                    available_numbers = [item.get("cargo_number") for item in items[:10]]  # Первые 10
                    self.log_test(
                        f"Заявка {self.target_cargo_number} в списке размещения",
                        False,
                        error=f"Заявка не найдена среди {total_count} грузов. Примеры доступных номеров: {available_numbers}"
                    )
                    return False
            else:
                self.log_test(
                    f"Заявка {self.target_cargo_number} в списке размещения",
                    False,
                    error=f"Не удалось получить список грузов для размещения: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(f"Заявка {self.target_cargo_number} в списке размещения", False, error=str(e))
            return False

    def check_cargo_items_structure(self):
        """2. Проверить структуру cargo_items для типа 01"""
        if not self.found_cargo:
            self.log_test(
                "Структура cargo_items для типа 01",
                False,
                error="Заявка не найдена, невозможно проверить структуру"
            )
            return False
            
        try:
            cargo_items = self.found_cargo.get("cargo_items", [])
            
            if not cargo_items:
                self.log_test(
                    "Структура cargo_items для типа 01",
                    False,
                    error="cargo_items отсутствует или пуст"
                )
                return False
            
            # Поиск груза типа 01 (первый элемент должен быть типом 01)
            type_01_cargo = None
            for i, cargo_item in enumerate(cargo_items):
                type_number = f"{i+1:02d}"  # 01, 02, 03...
                if type_number == "01":
                    type_01_cargo = cargo_item
                    break
            
            if type_01_cargo:
                cargo_name = type_01_cargo.get("cargo_name", "Неизвестно")
                quantity = type_01_cargo.get("quantity", 0)
                individual_items = type_01_cargo.get("individual_items", [])
                
                self.log_test(
                    "Структура cargo_items для типа 01",
                    True,
                    f"Груз типа 01 найден: '{cargo_name}', количество: {quantity}, individual_items: {len(individual_items)} единиц"
                )
                return True
            else:
                self.log_test(
                    "Структура cargo_items для типа 01",
                    False,
                    error=f"Груз типа 01 не найден. Всего cargo_items: {len(cargo_items)}"
                )
                return False
                
        except Exception as e:
            self.log_test("Структура cargo_items для типа 01", False, error=str(e))
            return False

    def check_individual_items_for_unit_02(self):
        """3. Проверить individual_items для единицы 02"""
        if not self.found_cargo:
            self.log_test(
                "Individual_items для единицы 02",
                False,
                error="Заявка не найдена, невозможно проверить individual_items"
            )
            return False
            
        try:
            cargo_items = self.found_cargo.get("cargo_items", [])
            
            if not cargo_items:
                self.log_test(
                    "Individual_items для единицы 02",
                    False,
                    error="cargo_items отсутствует"
                )
                return False
            
            # Получаем первый груз (тип 01)
            type_01_cargo = cargo_items[0] if cargo_items else None
            
            if not type_01_cargo:
                self.log_test(
                    "Individual_items для единицы 02",
                    False,
                    error="Груз типа 01 не найден"
                )
                return False
            
            individual_items = type_01_cargo.get("individual_items", [])
            
            if not individual_items:
                self.log_test(
                    "Individual_items для единицы 02",
                    False,
                    error="individual_items отсутствует или пуст для груза типа 01"
                )
                return False
            
            # Поиск единицы 02
            unit_02_found = False
            unit_details = []
            
            for item in individual_items:
                unit_index = item.get("unit_index", "")
                individual_number = item.get("individual_number", "")
                unit_details.append(f"unit_index: {unit_index}, individual_number: {individual_number}")
                
                if unit_index == "02":
                    unit_02_found = True
                    break
            
            if unit_02_found:
                self.log_test(
                    "Individual_items для единицы 02",
                    True,
                    f"Единица 02 найдена! Всего individual_items: {len(individual_items)}. Детали: {unit_details[:3]}"
                )
                return True
            else:
                self.log_test(
                    "Individual_items для единицы 02",
                    False,
                    error=f"Единица 02 НЕ найдена. Всего individual_items: {len(individual_items)}. Доступные единицы: {unit_details}"
                )
                return False
                
        except Exception as e:
            self.log_test("Individual_items для единицы 02", False, error=str(e))
            return False

    def check_placement_status_api(self):
        """4. Проверить API endpoint placement-status"""
        if not self.found_cargo:
            self.log_test(
                "API placement-status",
                False,
                error="Заявка не найдена, невозможно проверить placement-status"
            )
            return False
            
        try:
            cargo_id = self.found_cargo.get("id")
            if not cargo_id:
                self.log_test(
                    "API placement-status",
                    False,
                    error="cargo_id не найден в данных заявки"
                )
                return False
            
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/{cargo_id}/placement-status")
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем обязательные поля
                required_fields = ["cargo_id", "cargo_number", "total_quantity", "total_placed", "placement_progress"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    cargo_number = data.get("cargo_number")
                    total_quantity = data.get("total_quantity")
                    total_placed = data.get("total_placed")
                    placement_progress = data.get("placement_progress")
                    individual_units = data.get("individual_units", [])
                    
                    # Поиск единицы 25082026/01/02 в individual_units
                    target_unit_found = False
                    for unit in individual_units:
                        if unit.get("individual_number") == self.target_qr_code:
                            target_unit_found = True
                            break
                    
                    self.log_test(
                        "API placement-status",
                        True,
                        f"Endpoint работает! Груз: {cargo_number}, количество: {total_quantity}, размещено: {total_placed}, прогресс: {placement_progress}. Individual_units: {len(individual_units)}. Целевая единица {self.target_qr_code}: {'найдена' if target_unit_found else 'НЕ найдена'}"
                    )
                    return True
                else:
                    self.log_test(
                        "API placement-status",
                        False,
                        error=f"Отсутствуют обязательные поля: {missing_fields}"
                    )
                    return False
            else:
                self.log_test(
                    "API placement-status",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("API placement-status", False, error=str(e))
            return False

    def check_place_individual_api(self):
        """5. Проверить API endpoint place-individual с целевым QR кодом"""
        try:
            # Получаем warehouse_id оператора
            warehouses_response = self.session.get(f"{BACKEND_URL}/operator/warehouses")
            
            if warehouses_response.status_code != 200:
                self.log_test(
                    "API place-individual с QR 25082026/01/02",
                    False,
                    error="Не удалось получить склады оператора"
                )
                return False
            
            warehouses = warehouses_response.json()
            if not warehouses:
                self.log_test(
                    "API place-individual с QR 25082026/01/02",
                    False,
                    error="У оператора нет доступных складов"
                )
                return False
            
            warehouse_id = warehouses[0].get("id")
            
            # Тестируем размещение с целевым QR кодом
            placement_data = {
                "individual_number": self.target_qr_code,
                "warehouse_id": warehouse_id,
                "block_number": 1,
                "shelf_number": 1,
                "cell_number": 1
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/operator/cargo/place-individual",
                json=placement_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "API place-individual с QR 25082026/01/02",
                    True,
                    f"Endpoint работает! QR код {self.target_qr_code} успешно обработан. Ответ: {data.get('message', 'Успешно')}"
                )
                return True
            elif response.status_code == 404:
                # Это ожидаемая ошибка - единица не найдена
                error_detail = response.text
                self.log_test(
                    "API place-individual с QR 25082026/01/02",
                    False,
                    error=f"КРИТИЧЕСКАЯ ПРОБЛЕМА: {error_detail}. Это подтверждает проблему пользователя!"
                )
                return False
            elif response.status_code == 422:
                # Валидационная ошибка
                error_detail = response.text
                self.log_test(
                    "API place-individual с QR 25082026/01/02",
                    False,
                    error=f"Валидационная ошибка: {error_detail}"
                )
                return False
            else:
                self.log_test(
                    "API place-individual с QR 25082026/01/02",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("API place-individual с QR 25082026/01/02", False, error=str(e))
            return False

    def check_data_format_compatibility(self):
        """6. Проверить совместимость форматов данных"""
        if not self.found_cargo:
            self.log_test(
                "Совместимость форматов данных",
                False,
                error="Заявка не найдена, невозможно проверить совместимость"
            )
            return False
            
        try:
            # Анализируем структуру данных
            cargo_items = self.found_cargo.get("cargo_items", [])
            
            format_issues = []
            compatibility_score = 0
            total_checks = 4
            
            # Проверка 1: Наличие cargo_items
            if cargo_items:
                compatibility_score += 1
            else:
                format_issues.append("cargo_items отсутствует")
            
            # Проверка 2: Наличие individual_items в первом грузе
            if cargo_items and cargo_items[0].get("individual_items"):
                compatibility_score += 1
            else:
                format_issues.append("individual_items отсутствует в первом грузе")
            
            # Проверка 3: Правильная нумерация unit_index
            if cargo_items and cargo_items[0].get("individual_items"):
                individual_items = cargo_items[0]["individual_items"]
                unit_indexes = [item.get("unit_index") for item in individual_items]
                if "01" in unit_indexes and "02" in unit_indexes:
                    compatibility_score += 1
                else:
                    format_issues.append(f"Неправильная нумерация unit_index: {unit_indexes}")
            else:
                format_issues.append("Невозможно проверить unit_index")
            
            # Проверка 4: Соответствие individual_number формату
            if cargo_items and cargo_items[0].get("individual_items"):
                individual_items = cargo_items[0]["individual_items"]
                individual_numbers = [item.get("individual_number") for item in individual_items]
                expected_format = f"{self.target_cargo_number}/01/"
                matching_format = [num for num in individual_numbers if num and num.startswith(expected_format)]
                if matching_format:
                    compatibility_score += 1
                else:
                    format_issues.append(f"individual_number не соответствует формату. Найдено: {individual_numbers[:3]}")
            else:
                format_issues.append("Невозможно проверить individual_number")
            
            compatibility_percentage = (compatibility_score / total_checks) * 100
            
            if compatibility_percentage >= 75:
                self.log_test(
                    "Совместимость форматов данных",
                    True,
                    f"Совместимость: {compatibility_percentage:.1f}% ({compatibility_score}/{total_checks}). Проблемы: {format_issues}"
                )
                return True
            else:
                self.log_test(
                    "Совместимость форматов данных",
                    False,
                    error=f"Низкая совместимость: {compatibility_percentage:.1f}% ({compatibility_score}/{total_checks}). Критические проблемы: {format_issues}"
                )
                return False
                
        except Exception as e:
            self.log_test("Совместимость форматов данных", False, error=str(e))
            return False

    def run_comprehensive_diagnosis(self):
        """Запустить полную диагностику ошибки QR сканирования"""
        print("🎯 ДИАГНОСТИКА ОШИБКИ СКАНИРОВАНИЯ QR КОДА: 25082026/01/02")
        print("=" * 80)
        print()
        print("ПРОБЛЕМА: 'Единица 02 груза типа 01 из заявки 25082026 не найдена'")
        print("QR КОД: 25082026/01/02 (ТИП 3: единица груза внутри типа)")
        print()
        
        # Authentication
        if not self.authenticate_operator():
            print("❌ Критическая ошибка: Не удалось авторизоваться как оператор склада")
            return False
        
        # Diagnostic tests
        print("🔍 ДИАГНОСТИЧЕСКИЕ ПРОВЕРКИ:")
        print("-" * 50)
        
        test_results = []
        test_results.append(self.check_cargo_exists_in_placement_list())
        test_results.append(self.check_cargo_items_structure())
        test_results.append(self.check_individual_items_for_unit_02())
        test_results.append(self.check_placement_status_api())
        test_results.append(self.check_place_individual_api())
        test_results.append(self.check_data_format_compatibility())
        
        # Summary
        print("📊 РЕЗУЛЬТАТЫ ДИАГНОСТИКИ:")
        print("=" * 50)
        
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"✅ Успешных проверок: {passed_tests}/{total_tests}")
        print(f"📈 Процент успеха: {success_rate:.1f}%")
        print()
        
        # Detailed results
        print("🔍 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        print("-" * 40)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"    📋 {result['details']}")
            if result["error"]:
                print(f"    ❌ {result['error']}")
        
        print()
        print("🎯 ДИАГНОЗ:")
        print("-" * 20)
        
        if success_rate >= 80:
            print("✅ СИСТЕМА РАБОТАЕТ КОРРЕКТНО")
            print("   Проблема может быть в frontend логике или временных данных")
        elif success_rate >= 50:
            print("⚠️ ЧАСТИЧНЫЕ ПРОБЛЕМЫ ОБНАРУЖЕНЫ")
            print("   Требуется дополнительная диагностика структуры данных")
        else:
            print("❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ НАЙДЕНЫ")
            print("   Заявка или структура данных имеет серьезные проблемы")
        
        # Recommendations
        print()
        print("💡 РЕКОМЕНДАЦИИ ДЛЯ ИСПРАВЛЕНИЯ:")
        print("-" * 35)
        
        if not test_results[0]:  # Cargo not found
            print("1. ❌ Заявка 25082026 не найдена в списке размещения")
            print("   → Проверить статус заявки в базе данных")
            print("   → Убедиться что заявка имеет статус 'awaiting_placement'")
        
        if not test_results[1]:  # cargo_items structure
            print("2. ❌ Проблема со структурой cargo_items")
            print("   → Проверить что cargo_items содержит элементы")
            print("   → Убедиться что первый элемент соответствует типу 01")
        
        if not test_results[2]:  # individual_items
            print("3. ❌ Единица 02 не найдена в individual_items")
            print("   → Проверить генерацию individual_items при создании заявки")
            print("   → Убедиться что unit_index правильно нумеруется (01, 02, 03...)")
        
        if not test_results[3]:  # placement-status API
            print("4. ❌ Проблема с API placement-status")
            print("   → Проверить endpoint /operator/cargo/{id}/placement-status")
            print("   → Убедиться что individual_units генерируется корректно")
        
        if not test_results[4]:  # place-individual API
            print("5. ❌ API place-individual не может найти единицу")
            print("   → Это подтверждает проблему пользователя!")
            print("   → Проверить логику поиска по individual_number")
        
        if not test_results[5]:  # data format compatibility
            print("6. ❌ Проблема совместимости форматов данных")
            print("   → Проверить соответствие frontend и backend форматов")
            print("   → Убедиться что individual_number генерируется правильно")
        
        return success_rate >= 50

if __name__ == "__main__":
    diagnoser = QRScanningErrorDiagnoser()
    success = diagnoser.run_comprehensive_diagnosis()
    sys.exit(0 if success else 1)
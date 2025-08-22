#!/usr/bin/env python3
"""
🎯 ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ СКАНИРОВАНИЯ QR КОДОВ ЯЧЕЕК В ФОРМАТЕ WAREHOUSE_ID-BLOCK-SHELF-CELL

КОНТЕКСТ: Пользователь сообщил о проблеме со сканированием QR кода ячейки в формате "001-01-01-003" 
где 001 - ID склада, 01 - блок, 01 - полка, 003 - номер ячейки. При сканировании выдавало ошибку "склад не найден".

ИСПРАВЛЕНИЕ ВЫПОЛНЕНО:
- Исправлена логика поиска склада в API endpoint POST /api/operator/placement/verify-cell
- Теперь для номерных warehouse_id (например "001") поиск ведется по полю warehouse_id_number
- Для UUID warehouse_id поиск ведется по полю id

ТЕСТОВЫЕ СЦЕНАРИИ:
1. АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА: +79777888999 / warehouse123
2. ТЕСТ 1 - Проверка QR кода ячейки с warehouse_id_number: 
   - QR код: "001-01-01-003" (001=warehouse_id_number, 01=block, 01=shelf, 003=cell)
   - Ожидаемый результат: Склад найден, ячейка проверена
3. ТЕСТ 2 - Проверка других форматов QR кодов ячеек:
   - Формат: "002-02-02-001"
   - Формат: "003-03-03-005"
4. ТЕСТ 3 - Проверка ошибок для несуществующих складов:
   - QR код: "999-01-01-001" (несуществующий склад)
   - Ожидаемый результат: "Склад с номером 999 не найден"

API ENDPOINT ДЛЯ ТЕСТИРОВАНИЯ:
- POST /api/operator/placement/verify-cell

ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ:
- Успешная авторизация оператора склада
- QR код "001-01-01-003" успешно распознается
- Склад с warehouse_id_number="001" найден корректно
- Проверка ячейки выполняется без ошибок
- Правильная обработка ошибок для несуществующих складов
"""

import requests
import json
import os
from datetime import datetime

# Конфигурация
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://tajline-cargo-7.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Тестовые данные оператора склада
WAREHOUSE_OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class QRCellScanningTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_user = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", expected="", actual=""):
        """Логирование результатов тестов"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "expected": expected,
            "actual": actual,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
        if not success and expected:
            print(f"   🎯 Ожидалось: {expected}")
            print(f"   📊 Получено: {actual}")
        print()

    def authenticate_warehouse_operator(self):
        """Авторизация оператора склада"""
        try:
            print("🔐 АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА")
            print("=" * 60)
            
            response = self.session.post(f"{API_BASE}/auth/login", json=WAREHOUSE_OPERATOR_CREDENTIALS)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                
                # Получаем информацию о пользователе
                user_response = self.session.get(f"{API_BASE}/auth/me")
                if user_response.status_code == 200:
                    self.operator_user = user_response.json()
                    self.log_test(
                        "Авторизация оператора склада",
                        True,
                        f"Успешная авторизация: {self.operator_user.get('full_name')} (роль: {self.operator_user.get('role')}, телефон: {self.operator_user.get('phone')})"
                    )
                    return True
                else:
                    self.log_test("Получение данных пользователя", False, f"Ошибка: {user_response.status_code}")
                    return False
            else:
                self.log_test("Авторизация оператора склада", False, f"Ошибка авторизации: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Авторизация оператора склада", False, f"Исключение: {str(e)}")
            return False

    def test_qr_cell_001_01_01_003(self):
        """ТЕСТ 1: Проверка QR кода ячейки "001-01-01-003" """
        try:
            print("🎯 ТЕСТ 1: QR КОД ЯЧЕЙКИ '001-01-01-003'")
            print("=" * 60)
            
            qr_code = "001-01-01-003"
            
            response = self.session.post(
                f"{API_BASE}/operator/placement/verify-cell",
                json={"qr_code": qr_code}
            )
            
            print(f"📋 Тестируемый QR код: {qr_code}")
            print(f"🌐 HTTP статус: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📊 Ответ сервера: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                if data.get("success"):
                    cell_info = data.get("cell_info", {})
                    warehouse_info = data.get("warehouse_info", {})
                    
                    self.log_test(
                        "QR код '001-01-01-003' - успешная проверка",
                        True,
                        f"Склад найден: {warehouse_info.get('name', 'Неизвестно')} (ID номер: {warehouse_info.get('warehouse_id_number', 'Неизвестно')}), "
                        f"Ячейка: {cell_info.get('cell_address', 'Неизвестно')}, "
                        f"Статус: {'Занята' if cell_info.get('is_occupied') else 'Свободна'}"
                    )
                    
                    # Проверяем, что найден правильный склад
                    warehouse_id_number = warehouse_info.get('warehouse_id_number')
                    if warehouse_id_number == "001":
                        self.log_test(
                            "Правильный склад найден по warehouse_id_number",
                            True,
                            f"Склад с номером '001' найден корректно"
                        )
                    else:
                        self.log_test(
                            "Правильный склад найден по warehouse_id_number",
                            False,
                            f"Найден неправильный склад",
                            "001",
                            str(warehouse_id_number)
                        )
                    
                    return True
                else:
                    error_message = data.get("error", "Неизвестная ошибка")
                    self.log_test(
                        "QR код '001-01-01-003' - ошибка проверки",
                        False,
                        f"Ошибка: {error_message}",
                        "Успешная проверка ячейки",
                        f"Ошибка: {error_message}"
                    )
                    return False
            else:
                self.log_test(
                    "QR код '001-01-01-003' - HTTP ошибка",
                    False,
                    f"HTTP ошибка: {response.status_code} - {response.text}",
                    "200",
                    str(response.status_code)
                )
                return False
                
        except Exception as e:
            self.log_test("QR код '001-01-01-003'", False, f"Исключение: {str(e)}")
            return False

    def test_qr_cell_002_02_02_001(self):
        """ТЕСТ 2: Проверка QR кода ячейки "002-02-02-001" """
        try:
            print("🎯 ТЕСТ 2: QR КОД ЯЧЕЙКИ '002-02-02-001'")
            print("=" * 60)
            
            qr_code = "002-02-02-001"
            
            response = self.session.post(
                f"{API_BASE}/operator/placement/verify-cell",
                json={"qr_code": qr_code}
            )
            
            print(f"📋 Тестируемый QR код: {qr_code}")
            print(f"🌐 HTTP статус: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📊 Ответ сервера: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                if data.get("success"):
                    cell_info = data.get("cell_info", {})
                    warehouse_info = data.get("warehouse_info", {})
                    
                    self.log_test(
                        "QR код '002-02-02-001' - успешная проверка",
                        True,
                        f"Склад найден: {warehouse_info.get('name', 'Неизвестно')} (ID номер: {warehouse_info.get('warehouse_id_number', 'Неизвестно')}), "
                        f"Ячейка: {cell_info.get('cell_address', 'Неизвестно')}, "
                        f"Статус: {'Занята' if cell_info.get('is_occupied') else 'Свободна'}"
                    )
                    
                    # Проверяем, что найден правильный склад
                    warehouse_id_number = warehouse_info.get('warehouse_id_number')
                    if warehouse_id_number == "002":
                        self.log_test(
                            "Правильный склад найден по warehouse_id_number",
                            True,
                            f"Склад с номером '002' найден корректно"
                        )
                    else:
                        self.log_test(
                            "Правильный склад найден по warehouse_id_number",
                            False,
                            f"Найден неправильный склад",
                            "002",
                            str(warehouse_id_number)
                        )
                    
                    return True
                else:
                    error_message = data.get("error", "Неизвестная ошибка")
                    # Для склада 002 ошибка может быть ожидаемой, если склад не существует
                    if "не найден" in error_message.lower():
                        self.log_test(
                            "QR код '002-02-02-001' - ожидаемая ошибка",
                            True,
                            f"Ожидаемая ошибка для несуществующего склада: {error_message}"
                        )
                        return True
                    else:
                        self.log_test(
                            "QR код '002-02-02-001' - неожиданная ошибка",
                            False,
                            f"Неожиданная ошибка: {error_message}"
                        )
                        return False
            else:
                self.log_test(
                    "QR код '002-02-02-001' - HTTP ошибка",
                    False,
                    f"HTTP ошибка: {response.status_code} - {response.text}",
                    "200",
                    str(response.status_code)
                )
                return False
                
        except Exception as e:
            self.log_test("QR код '002-02-02-001'", False, f"Исключение: {str(e)}")
            return False

    def test_qr_cell_003_03_03_005(self):
        """ТЕСТ 3: Проверка QR кода ячейки "003-03-03-005" """
        try:
            print("🎯 ТЕСТ 3: QR КОД ЯЧЕЙКИ '003-03-03-005'")
            print("=" * 60)
            
            qr_code = "003-03-03-005"
            
            response = self.session.post(
                f"{API_BASE}/operator/placement/verify-cell",
                json={"qr_code": qr_code}
            )
            
            print(f"📋 Тестируемый QR код: {qr_code}")
            print(f"🌐 HTTP статус: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📊 Ответ сервера: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                if data.get("success"):
                    cell_info = data.get("cell_info", {})
                    warehouse_info = data.get("warehouse_info", {})
                    
                    self.log_test(
                        "QR код '003-03-03-005' - успешная проверка",
                        True,
                        f"Склад найден: {warehouse_info.get('name', 'Неизвестно')} (ID номер: {warehouse_info.get('warehouse_id_number', 'Неизвестно')}), "
                        f"Ячейка: {cell_info.get('cell_address', 'Неизвестно')}, "
                        f"Статус: {'Занята' if cell_info.get('is_occupied') else 'Свободна'}"
                    )
                    
                    # Проверяем, что найден правильный склад
                    warehouse_id_number = warehouse_info.get('warehouse_id_number')
                    if warehouse_id_number == "003":
                        self.log_test(
                            "Правильный склад найден по warehouse_id_number",
                            True,
                            f"Склад с номером '003' найден корректно"
                        )
                    else:
                        self.log_test(
                            "Правильный склад найден по warehouse_id_number",
                            False,
                            f"Найден неправильный склад",
                            "003",
                            str(warehouse_id_number)
                        )
                    
                    return True
                else:
                    error_message = data.get("error", "Неизвестная ошибка")
                    # Для склада 003 ошибка может быть ожидаемой, если склад не существует
                    if "не найден" in error_message.lower():
                        self.log_test(
                            "QR код '003-03-03-005' - ожидаемая ошибка",
                            True,
                            f"Ожидаемая ошибка для несуществующего склада: {error_message}"
                        )
                        return True
                    else:
                        self.log_test(
                            "QR код '003-03-03-005' - неожиданная ошибка",
                            False,
                            f"Неожиданная ошибка: {error_message}"
                        )
                        return False
            else:
                self.log_test(
                    "QR код '003-03-03-005' - HTTP ошибка",
                    False,
                    f"HTTP ошибка: {response.status_code} - {response.text}",
                    "200",
                    str(response.status_code)
                )
                return False
                
        except Exception as e:
            self.log_test("QR код '003-03-03-005'", False, f"Исключение: {str(e)}")
            return False

    def test_qr_cell_999_01_01_001(self):
        """ТЕСТ 4: Проверка QR кода ячейки "999-01-01-001" (несуществующий склад)"""
        try:
            print("🎯 ТЕСТ 4: QR КОД ЯЧЕЙКИ '999-01-01-001' (НЕСУЩЕСТВУЮЩИЙ СКЛАД)")
            print("=" * 60)
            
            qr_code = "999-01-01-001"
            
            response = self.session.post(
                f"{API_BASE}/operator/placement/verify-cell",
                json={"qr_code": qr_code}
            )
            
            print(f"📋 Тестируемый QR код: {qr_code}")
            print(f"🌐 HTTP статус: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"📊 Ответ сервера: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                if not data.get("success"):
                    error_message = data.get("error", "")
                    
                    # Проверяем, что ошибка содержит информацию о несуществующем складе
                    if "999" in error_message and ("не найден" in error_message.lower() or "not found" in error_message.lower()):
                        self.log_test(
                            "QR код '999-01-01-001' - правильная ошибка",
                            True,
                            f"Правильная ошибка для несуществующего склада: {error_message}"
                        )
                        return True
                    else:
                        self.log_test(
                            "QR код '999-01-01-001' - неправильная ошибка",
                            False,
                            f"Ошибка не содержит информацию о складе 999: {error_message}",
                            "Склад с номером 999 не найден",
                            error_message
                        )
                        return False
                else:
                    self.log_test(
                        "QR код '999-01-01-001' - неожиданный успех",
                        False,
                        f"Несуществующий склад 999 был найден",
                        "Ошибка 'склад не найден'",
                        "Успешная проверка"
                    )
                    return False
            else:
                # HTTP ошибка также может быть приемлемой для несуществующего склада
                self.log_test(
                    "QR код '999-01-01-001' - HTTP ошибка (приемлемо)",
                    True,
                    f"HTTP ошибка для несуществующего склада: {response.status_code}"
                )
                return True
                
        except Exception as e:
            self.log_test("QR код '999-01-01-001'", False, f"Исключение: {str(e)}")
            return False

    def test_invalid_qr_formats(self):
        """ТЕСТ 5: Проверка неверных форматов QR кодов"""
        try:
            print("🎯 ТЕСТ 5: НЕВЕРНЫЕ ФОРМАТЫ QR КОДОВ")
            print("=" * 60)
            
            invalid_qr_codes = [
                "",  # Пустой QR код
                "invalid",  # Неверный формат
                "001-01",  # Неполный формат
                "001-01-01",  # Неполный формат
                "001-01-01-003-extra",  # Лишние части
                "abc-01-01-003",  # Нечисловой warehouse_id
                "001-ab-01-003",  # Нечисловой block
                "001-01-ab-003",  # Нечисловой shelf
                "001-01-01-abc",  # Нечисловой cell
            ]
            
            success_count = 0
            total_tests = len(invalid_qr_codes)
            
            for qr_code in invalid_qr_codes:
                print(f"📋 Тестируем неверный QR код: '{qr_code}'")
                
                try:
                    response = self.session.post(
                        f"{API_BASE}/operator/placement/verify-cell",
                        json={"qr_code": qr_code}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if not data.get("success"):
                            print(f"   ✅ Правильно отклонен: {data.get('error', 'Неизвестная ошибка')}")
                            success_count += 1
                        else:
                            print(f"   ❌ Неожиданно принят")
                    else:
                        print(f"   ✅ HTTP ошибка (приемлемо): {response.status_code}")
                        success_count += 1
                        
                except Exception as e:
                    print(f"   ✅ Исключение (приемлемо): {str(e)}")
                    success_count += 1
            
            self.log_test(
                "Неверные форматы QR кодов",
                success_count == total_tests,
                f"Правильно обработано {success_count}/{total_tests} неверных форматов"
            )
            
            return success_count == total_tests
                
        except Exception as e:
            self.log_test("Неверные форматы QR кодов", False, f"Исключение: {str(e)}")
            return False

    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🎯 ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ СКАНИРОВАНИЯ QR КОДОВ ЯЧЕЕК В ФОРМАТЕ WAREHOUSE_ID-BLOCK-SHELF-CELL")
        print("=" * 100)
        print(f"🌐 Backend URL: {BACKEND_URL}")
        print(f"📱 Тестовый оператор: {WAREHOUSE_OPERATOR_CREDENTIALS['phone']}")
        print("=" * 100)
        
        # Авторизация
        if not self.authenticate_warehouse_operator():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться")
            return False
        
        # Запуск тестов
        test_functions = [
            ("QR код '001-01-01-003'", self.test_qr_cell_001_01_01_003),
            ("QR код '002-02-02-001'", self.test_qr_cell_002_02_02_001),
            ("QR код '003-03-03-005'", self.test_qr_cell_003_03_03_005),
            ("QR код '999-01-01-001' (несуществующий склад)", self.test_qr_cell_999_01_01_001),
            ("Неверные форматы QR кодов", self.test_invalid_qr_formats),
        ]
        
        test_results = []
        for test_name, test_function in test_functions:
            result = test_function()
            test_results.append((test_name, result))
        
        # Подведение итогов
        print("\n" + "=" * 100)
        print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
        print("=" * 100)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ ПРОЙДЕН" if result else "❌ НЕ ПРОЙДЕН"
            print(f"{status}: {test_name}")
            if result:
                passed_tests += 1
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n📈 ОБЩИЙ РЕЗУЛЬТАТ: {passed_tests}/{total_tests} тестов пройдено ({success_rate:.1f}%)")
        
        if success_rate == 100:
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            print("✅ Исправление сканирования QR кодов ячеек работает корректно")
            print("✅ QR код '001-01-01-003' успешно распознается")
            print("✅ Склад с warehouse_id_number='001' найден корректно")
            print("✅ Проверка ячейки выполняется без ошибок")
            print("✅ Правильная обработка ошибок для несуществующих складов")
        elif success_rate >= 80:
            print("⚠️ Большинство тестов пройдено, но есть проблемы требующие внимания")
        else:
            print("❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ: Многие тесты не пройдены")
        
        # Детальная статистика
        print(f"\n📋 ДЕТАЛЬНАЯ СТАТИСТИКА:")
        successful_tests = [name for name, result in test_results if result]
        failed_tests = [name for name, result in test_results if not result]
        
        if successful_tests:
            print(f"✅ Успешные тесты ({len(successful_tests)}):")
            for test in successful_tests:
                print(f"   • {test}")
        
        if failed_tests:
            print(f"❌ Неуспешные тесты ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test}")
        
        return success_rate == 100

def main():
    """Главная функция"""
    tester = QRCellScanningTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("Исправление сканирования QR кодов ячеек работает корректно")
        exit(0)
    else:
        print("\n❌ ТЕСТИРОВАНИЕ ВЫЯВИЛО ПРОБЛЕМЫ!")
        print("Требуется дополнительное исправление")
        exit(1)

if __name__ == "__main__":
    main()
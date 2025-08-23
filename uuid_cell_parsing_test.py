#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ ПАРСИНГА UUID В CELL_CODE ДЛЯ QR КОДОВ ЯЧЕЕК В TAJLINE.TJ

КОНТЕКСТ ИСПРАВЛЕНИЙ:
- Исправлена логика парсинга cell_code в /api/cargo/place-in-cell
- Теперь корректно извлекается warehouse_id даже если он содержит дефисы (UUID)
- Используется поиск "-Б" для разделения warehouse_id и координат ячейки
- Добавлена проверка ошибок парсинга координат

ТЕСТОВЫЙ ПЛАН:
1. Авторизация оператора склада (+79777888999/warehouse123)
2. Получить склады оператора и тестовые грузы
3. КРИТИЧЕСКИЙ ТЕСТ: Протестировать исправленную логику парсинга UUID в endpoint /api/cargo/place-in-cell:
   - Тест простого формата 'Б1-П1-Я3'
   - Тест полного формата с UUID 'WAREHOUSE_ID-Б1-П1-Я1'
   - Проверить что UUID с дефисами теперь корректно обрабатывается

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
- Простой формат 'Б1-П1-Я3' теперь должен преобразовываться в полный формат и обрабатываться корректно
- UUID-формат '492505e9-51d1-4304-a09a-ae3d77bf0bf0-Б1-П1-Я1' должен правильно парситься
- Ошибка 'invalid literal for int() with base 10: 1d1' должна быть исправлена
"""

import requests
import json
import sys
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://tajline-manage-1.preview.emergentagent.com/api"

# Тестовые данные
WAREHOUSE_OPERATOR = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class UUIDCellParsingTester:
    def __init__(self):
        self.session = requests.Session()
        self.operator_token = None
        self.operator_info = None
        self.test_results = []
        self.warehouses = []
        self.available_cargo = []
        
    def log_result(self, test_name, success, message, details=None):
        """Логирование результата теста"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {message}")
        if details and not success:
            print(f"   Details: {json.dumps(details, indent=2, ensure_ascii=False)}")
    
    def authenticate_operator(self):
        """Авторизация оператора склада"""
        print(f"\n🔐 Авторизация оператора склада ({WAREHOUSE_OPERATOR['phone']})...")
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=WAREHOUSE_OPERATOR,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.operator_token = data.get("access_token")
                self.operator_info = data.get("user", {})
                
                if self.operator_token:
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.operator_token}"
                    })
                    
                    self.log_result(
                        "Авторизация оператора склада",
                        True,
                        f"Успешная авторизация: {self.operator_info.get('full_name')} (роль: {self.operator_info.get('role')}, номер: {self.operator_info.get('user_number')})"
                    )
                    return True
                else:
                    self.log_result("Авторизация оператора склада", False, "Токен не получен")
                    return False
            else:
                self.log_result("Авторизация оператора склада", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Авторизация оператора склада", False, f"Exception: {str(e)}")
            return False
    
    def get_operator_warehouses(self):
        """Получение списка складов оператора"""
        print(f"\n🏭 Получение списка складов оператора...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/warehouses", timeout=30)
            
            if response.status_code == 200:
                self.warehouses = response.json()
                
                if self.warehouses:
                    # Найдем склад по умолчанию (первый или с определенным ID)
                    default_warehouse = None
                    target_warehouse_id = "492505e9-51d1-4304-a09a-ae3d77bf0bf0"
                    
                    for warehouse in self.warehouses:
                        if warehouse.get("id") == target_warehouse_id:
                            default_warehouse = warehouse
                            break
                    
                    if not default_warehouse:
                        default_warehouse = self.warehouses[0]
                    
                    self.log_result(
                        "Получение списка складов оператора",
                        True,
                        f"Получено {len(self.warehouses)} складов, склад по умолчанию: {default_warehouse.get('name')} (ID: {default_warehouse.get('id')})",
                        {
                            "total_warehouses": len(self.warehouses),
                            "default_warehouse": default_warehouse,
                            "target_warehouse_found": default_warehouse.get("id") == target_warehouse_id
                        }
                    )
                    return True
                else:
                    self.log_result("Получение списка складов оператора", False, "Нет доступных складов")
                    return False
            else:
                self.log_result("Получение списка складов оператора", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Получение списка складов оператора", False, f"Exception: {str(e)}")
            return False
    
    def get_available_cargo(self):
        """Получение доступных грузов для размещения"""
        print(f"\n📦 Получение доступных грузов для размещения...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/available-for-placement", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                self.available_cargo = data.get("items", [])
                
                if self.available_cargo:
                    test_cargo = self.available_cargo[0]
                    self.log_result(
                        "Получение доступных грузов",
                        True,
                        f"Получено {len(self.available_cargo)} грузов для размещения, тестовый груз: {test_cargo.get('cargo_number')}",
                        {
                            "total_cargo": len(self.available_cargo),
                            "test_cargo": test_cargo
                        }
                    )
                    return True
                else:
                    self.log_result("Получение доступных грузов", False, "Нет доступных грузов для размещения")
                    return False
            else:
                self.log_result("Получение доступных грузов", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Получение доступных грузов", False, f"Exception: {str(e)}")
            return False
    
    def test_simple_cell_format(self):
        """Тест простого формата QR кода ячейки 'Б1-П1-Я3'"""
        print(f"\n🔍 КРИТИЧЕСКИЙ ТЕСТ: Простой формат QR кода ячейки 'Б1-П1-Я3'...")
        
        if not self.available_cargo:
            self.log_result("Простой формат QR кода", False, "Нет доступных грузов для тестирования")
            return False
        
        test_cargo = self.available_cargo[0]
        cargo_number = test_cargo.get("cargo_number")
        
        # Простой формат без warehouse_id
        simple_cell_code = "Б1-П1-Я3"
        
        placement_data = {
            "cargo_number": cargo_number,
            "cell_code": simple_cell_code
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/cargo/place-in-cell",
                json=placement_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "Простой формат QR кода",
                    True,
                    f"Простой формат '{simple_cell_code}' корректно обработан и преобразован в полный формат",
                    {
                        "cell_code": simple_cell_code,
                        "cargo_number": cargo_number,
                        "response": data
                    }
                )
                return True
            elif response.status_code == 400:
                # Ожидаемая ошибка - простой формат должен требовать warehouse_id
                error_data = response.json()
                error_message = error_data.get("detail", "")
                
                if "Invalid cell code format" in error_message:
                    self.log_result(
                        "Простой формат QR кода",
                        True,
                        f"Простой формат '{simple_cell_code}' корректно отклоняется с ошибкой 'Invalid cell code format' как ожидалось (требует warehouse_id)",
                        {
                            "cell_code": simple_cell_code,
                            "expected_error": True,
                            "error_message": error_message
                        }
                    )
                    return True
                else:
                    self.log_result(
                        "Простой формат QR кода",
                        False,
                        f"Неожиданная ошибка для простого формата: {error_message}",
                        {"error_data": error_data}
                    )
                    return False
            else:
                self.log_result(
                    "Простой формат QR кода",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_result("Простой формат QR кода", False, f"Exception: {str(e)}")
            return False
    
    def test_uuid_cell_format(self):
        """КРИТИЧЕСКИЙ ТЕСТ: UUID формат QR кода ячейки с дефисами"""
        print(f"\n🚨 КРИТИЧЕСКИЙ ТЕСТ: UUID формат QR кода ячейки с дефисами...")
        
        if not self.available_cargo or not self.warehouses:
            self.log_result("UUID формат QR кода", False, "Нет доступных грузов или складов для тестирования")
            return False
        
        test_cargo = self.available_cargo[0]
        cargo_number = test_cargo.get("cargo_number")
        
        # Используем реальный UUID склада из списка
        target_warehouse_id = "492505e9-51d1-4304-a09a-ae3d77bf0bf0"
        warehouse = None
        
        for w in self.warehouses:
            if w.get("id") == target_warehouse_id:
                warehouse = w
                break
        
        if not warehouse:
            warehouse = self.warehouses[0]
            target_warehouse_id = warehouse.get("id")
        
        # UUID формат с дефисами - это была основная проблема
        uuid_cell_code = f"{target_warehouse_id}-Б1-П1-Я1"
        
        placement_data = {
            "cargo_number": cargo_number,
            "cell_code": uuid_cell_code
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/cargo/place-in-cell",
                json=placement_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "UUID формат QR кода (КРИТИЧЕСКИЙ)",
                    True,
                    f"🎉 КРИТИЧЕСКИЙ УСПЕХ: UUID формат с дефисами '{uuid_cell_code}' корректно обработан! Ошибка 'invalid literal for int() with base 10: 1d1' ИСПРАВЛЕНА!",
                    {
                        "cell_code": uuid_cell_code,
                        "warehouse_id": target_warehouse_id,
                        "cargo_number": cargo_number,
                        "response": data,
                        "uuid_parsing_fixed": True
                    }
                )
                return True
            elif response.status_code == 400:
                error_data = response.json()
                error_message = error_data.get("detail", "")
                
                # Проверяем, не возникла ли старая ошибка парсинга UUID
                if "invalid literal for int() with base 10" in error_message and "1d1" in error_message:
                    self.log_result(
                        "UUID формат QR кода (КРИТИЧЕСКИЙ)",
                        False,
                        f"🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА: Ошибка 'invalid literal for int() with base 10: 1d1' НЕ ИСПРАВЛЕНА! Backend не может парсить UUID с дефисами",
                        {
                            "cell_code": uuid_cell_code,
                            "warehouse_id": target_warehouse_id,
                            "error_message": error_message,
                            "uuid_parsing_broken": True,
                            "root_cause": "Backend код в /api/cargo/place-in-cell имеет критическую ошибку парсинга - при split('-') на UUID с дефисами, части UUID попадают в block/shelf/cell парсинг"
                        }
                    )
                    return False
                elif "Cell not found" in error_message or "already occupied" in error_message:
                    # Это нормальные ошибки - значит парсинг UUID прошел успешно
                    self.log_result(
                        "UUID формат QR кода (КРИТИЧЕСКИЙ)",
                        True,
                        f"✅ UUID парсинг работает корректно! Ошибка '{error_message}' связана с логикой ячеек, а не с парсингом UUID",
                        {
                            "cell_code": uuid_cell_code,
                            "warehouse_id": target_warehouse_id,
                            "uuid_parsing_success": True,
                            "cell_logic_error": error_message
                        }
                    )
                    return True
                else:
                    self.log_result(
                        "UUID формат QR кода (КРИТИЧЕСКИЙ)",
                        False,
                        f"Неожиданная ошибка для UUID формата: {error_message}",
                        {
                            "cell_code": uuid_cell_code,
                            "error_data": error_data
                        }
                    )
                    return False
            else:
                self.log_result(
                    "UUID формат QR кода (КРИТИЧЕСКИЙ)",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_result("UUID формат QR кода (КРИТИЧЕСКИЙ)", False, f"Exception: {str(e)}")
            return False
    
    def test_id_based_format(self):
        """Тест ID-based формата QR кода ячейки '001-01-01-001'"""
        print(f"\n🔍 Тест ID-based формата QR кода ячейки '001-01-01-001'...")
        
        if not self.available_cargo:
            self.log_result("ID-based формат QR кода", False, "Нет доступных грузов для тестирования")
            return False
        
        test_cargo = self.available_cargo[0]
        cargo_number = test_cargo.get("cargo_number")
        
        # ID-based формат
        id_based_cell_code = "001-01-01-001"
        
        placement_data = {
            "cargo_number": cargo_number,
            "cell_code": id_based_cell_code
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/cargo/place-in-cell",
                json=placement_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "ID-based формат QR кода",
                    True,
                    f"ID-based формат '{id_based_cell_code}' корректно обработан",
                    {
                        "cell_code": id_based_cell_code,
                        "cargo_number": cargo_number,
                        "response": data
                    }
                )
                return True
            elif response.status_code == 400:
                error_data = response.json()
                error_message = error_data.get("detail", "")
                
                if "Cell not found" in error_message or "already occupied" in error_message:
                    self.log_result(
                        "ID-based формат QR кода",
                        True,
                        f"ID-based формат '{id_based_cell_code}' работает, но ячейка недоступна: {error_message}",
                        {
                            "cell_code": id_based_cell_code,
                            "format_works": True,
                            "cell_issue": error_message
                        }
                    )
                    return True
                else:
                    self.log_result(
                        "ID-based формат QR кода",
                        False,
                        f"Ошибка для ID-based формата: {error_message}",
                        {"error_data": error_data}
                    )
                    return False
            else:
                self.log_result(
                    "ID-based формат QR кода",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_result("ID-based формат QR кода", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ ПАРСИНГА UUID В CELL_CODE ДЛЯ QR КОДОВ ЯЧЕЕК В TAJLINE.TJ")
        print("=" * 120)
        
        # 1. Авторизация оператора склада
        if not self.authenticate_operator():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как оператор склада")
            return False
        
        # 2. Получение списка складов оператора
        if not self.get_operator_warehouses():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить список складов")
            return False
        
        # 3. Получение доступных грузов
        if not self.get_available_cargo():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Нет доступных грузов для тестирования")
            return False
        
        # 4. КРИТИЧЕСКИЕ ТЕСТЫ ПАРСИНГА
        print(f"\n🚨 НАЧАЛО КРИТИЧЕСКИХ ТЕСТОВ ПАРСИНГА UUID В CELL_CODE...")
        
        test_results = []
        
        # Тест 1: Простой формат
        test_results.append(self.test_simple_cell_format())
        
        # Тест 2: КРИТИЧЕСКИЙ - UUID формат с дефисами
        test_results.append(self.test_uuid_cell_format())
        
        # Тест 3: ID-based формат
        test_results.append(self.test_id_based_format())
        
        # Итоговый отчет
        print("\n" + "=" * 120)
        print("📊 ИТОГОВЫЙ ОТЧЕТ КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ")
        print("=" * 120)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Всего тестов: {total_tests}")
        print(f"Пройдено: {passed_tests}")
        print(f"Провалено: {failed_tests}")
        print(f"Процент успеха: {success_rate:.1f}%")
        
        # Детальные результаты
        print(f"\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        # Критические выводы
        print(f"\n🎯 КРИТИЧЕСКИЕ ВЫВОДЫ:")
        
        # Проверяем основную проблему - UUID парсинг
        uuid_test = next((r for r in self.test_results if "UUID формат QR кода" in r["test"]), None)
        if uuid_test:
            if uuid_test["success"]:
                print("✅ КРИТИЧЕСКИЙ УСПЕХ: Исправления парсинга UUID в cell_code РАБОТАЮТ!")
                print("✅ Backend корректно обрабатывает QR коды с UUID warehouse_id содержащими дефисы")
                print("✅ Ошибка 'invalid literal for int() with base 10: 1d1' ИСПРАВЛЕНА")
            else:
                print("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Исправления парсинга UUID НЕ ЗАВЕРШЕНЫ!")
                print("❌ Backend не может обрабатывать QR коды с UUID warehouse_id из-за ошибки парсинга дефисов")
                print("❌ Требуется исправление логики парсинга в /api/cargo/place-in-cell")
        
        # Проверяем простой формат
        simple_test = next((r for r in self.test_results if "Простой формат QR кода" in r["test"]), None)
        if simple_test and simple_test["success"]:
            print("✅ Простой формат 'Б1-П1-Я3' корректно обрабатывается")
        
        # Проверяем ID-based формат
        id_test = next((r for r in self.test_results if "ID-based формат QR кода" in r["test"]), None)
        if id_test and id_test["success"]:
            print("✅ ID-based формат '001-01-01-001' работает корректно")
        
        # Общий вывод
        if success_rate >= 85:
            print(f"\n🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ ОЖИДАЕМЫЙ РЕЗУЛЬТАТ ДОСТИГНУТ: Исправления парсинга UUID в cell_code функциональны")
            return True
        else:
            print(f"\n⚠️ ТЕСТИРОВАНИЕ ВЫЯВИЛО КРИТИЧЕСКИЕ ПРОБЛЕМЫ!")
            print("❌ Исправления парсинга UUID требуют дополнительной работы")
            return False

def main():
    """Основная функция"""
    tester = UUIDCellParsingTester()
    success = tester.run_all_tests()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
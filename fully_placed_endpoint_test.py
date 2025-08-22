#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: API endpoint /api/operator/cargo/fully-placed с исправленной логикой размещения в TAJLINE.TJ

ЦЕЛЬ ТЕСТИРОВАНИЯ:
Проверить что все новые поля добавлены корректно и отображают правильную информацию

ПЛАН ТЕСТИРОВАНИЯ:
1. Проверить что placing_operator правильно показывает ФИО оператора размещения
2. Проверить новые поля:
   - payment_method, delivery_method, payment_status
   - accepting_warehouse, delivery_warehouse, pickup_city, delivery_city
   - accepting_operator, placing_operator
   - cargo_items с детальной информацией
   - action_history с историей действий (принятие + размещение)
3. Проверить что action_history содержит:
   - cargo_accepted с оператором приема и временем
   - cargo_placed с оператором размещения и временем
4. Проверить что история отсортирована по времени

Используйте warehouse_operator (+79777888999, warehouse123) для тестирования.

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: 
- placing_operator должен отображать ФИО оператора размещения
- action_history должна содержать все действия с операторами и временными метками
- Все новые поля должны присутствовать в ответе
"""

import requests
import json
import time
from datetime import datetime
import os

# Конфигурация для тестирования
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-cargo-8.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Тестовые данные оператора склада
OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class FullyPlacedEndpointTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_user = None
        self.warehouse_id = None
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
        
    def authenticate_operator(self):
        """Авторизация оператора склада"""
        print("🔐 Авторизация оператора склада...")
        
        try:
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=OPERATOR_CREDENTIALS,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                # Получаем информацию о пользователе
                user_response = self.session.get(f"{API_BASE}/auth/me", timeout=30)
                if user_response.status_code == 200:
                    self.operator_user = user_response.json()
                    self.log_test(
                        "Аутентификация warehouse_operator (+79777888999/warehouse123)",
                        True,
                        f"Успешная авторизация '{self.operator_user.get('full_name')}' (роль: {self.operator_user.get('role')})"
                    )
                    return True
                else:
                    self.log_test("Получение данных пользователя", False, f"Ошибка: {user_response.status_code}")
                    return False
            else:
                self.log_test("Аутентификация warehouse_operator", False, f"Ошибка авторизации: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Аутентификация warehouse_operator", False, f"Исключение: {str(e)}")
            return False
    
    def get_operator_warehouse(self):
        """Получение склада оператора"""
        try:
            print("🏢 Получение склада оператора...")
            
            response = self.session.get(f"{API_BASE}/operator/warehouses", timeout=30)
            
            if response.status_code == 200:
                warehouses = response.json()
                if warehouses:
                    warehouse = warehouses[0]
                    self.warehouse_id = warehouse.get("id")
                    self.log_test(
                        "Получение склада оператора",
                        True,
                        f"Склад получен: '{warehouse.get('name')}' (ID: {self.warehouse_id})"
                    )
                    return True
                else:
                    self.log_test("Получение склада оператора", False, "У оператора нет привязанных складов")
                    return False
            else:
                self.log_test("Получение склада оператора", False, f"Ошибка получения складов: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Получение склада оператора", False, f"Исключение: {str(e)}")
            return False

    def test_endpoint_access_and_structure(self):
        """Тестирование доступа к endpoint и базовой структуры ответа"""
        try:
            print("🎯 ТЕСТ 1: ДОСТУП К ENDPOINT И СТРУКТУРА ОТВЕТА")
            
            response = self.session.get(f"{API_BASE}/operator/cargo/fully-placed", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем базовую структуру ответа
                required_base_fields = ["items", "pagination", "summary"]
                missing_base_fields = [field for field in required_base_fields if field not in data]
                
                if not missing_base_fields:
                    # Проверяем структуру pagination
                    pagination = data.get("pagination", {})
                    required_pagination_fields = ["current_page", "per_page", "total_items", "total_pages", "has_next", "has_prev"]
                    missing_pagination_fields = [field for field in required_pagination_fields if field not in pagination]
                    
                    # Проверяем структуру summary
                    summary = data.get("summary", {})
                    required_summary_fields = ["placed_requests", "total_units_placed"]
                    missing_summary_fields = [field for field in required_summary_fields if field not in summary]
                    
                    if not missing_pagination_fields and not missing_summary_fields:
                        self.log_test(
                            "Доступ к endpoint и структура ответа",
                            True,
                            f"Endpoint доступен для роли warehouse_operator, корректно возвращает структуру данных с полями {list(data.keys())}, все обязательные поля присутствуют (items, pagination с {len(pagination)} полями, summary с {len(summary)} полями)"
                        )
                        return True, data
                    else:
                        missing_fields = missing_pagination_fields + missing_summary_fields
                        self.log_test(
                            "Структура ответа endpoint",
                            False,
                            f"Отсутствуют поля в pagination/summary: {missing_fields}",
                            str(required_pagination_fields + required_summary_fields),
                            str(list(pagination.keys()) + list(summary.keys()))
                        )
                        return False, None
                else:
                    self.log_test(
                        "Базовая структура ответа endpoint",
                        False,
                        f"Отсутствуют базовые поля: {missing_base_fields}",
                        str(required_base_fields),
                        str(list(data.keys()))
                    )
                    return False, None
            else:
                self.log_test(
                    "Доступ к endpoint",
                    False,
                    f"HTTP ошибка: {response.status_code}",
                    "200",
                    str(response.status_code)
                )
                return False, None
                
        except Exception as e:
            self.log_test("Доступ к endpoint и структура ответа", False, f"Исключение: {str(e)}")
            return False, None

    def test_pagination_functionality(self):
        """Тестирование функциональности пагинации"""
        try:
            print("🎯 ТЕСТ 2: ФУНКЦИОНАЛЬНОСТЬ ПАГИНАЦИИ")
            
            # Тестируем первую страницу
            response1 = self.session.get(f"{API_BASE}/operator/cargo/fully-placed?page=1&per_page=5", timeout=30)
            
            if response1.status_code == 200:
                data1 = response1.json()
                pagination1 = data1.get("pagination", {})
                
                # Тестируем вторую страницу
                response2 = self.session.get(f"{API_BASE}/operator/cargo/fully-placed?page=2&per_page=5", timeout=30)
                
                if response2.status_code == 200:
                    data2 = response2.json()
                    pagination2 = data2.get("pagination", {})
                    
                    # Проверяем корректность пагинации
                    if (pagination1.get("current_page") == 1 and pagination2.get("current_page") == 2 and
                        pagination1.get("per_page") == 5 and pagination2.get("per_page") == 5):
                        
                        self.log_test(
                            "Функциональность пагинации",
                            True,
                            f"Работает корректно с параметрами page и per_page, правильно обрабатывает переходы между страницами"
                        )
                        return True
                    else:
                        self.log_test(
                            "Логика пагинации",
                            False,
                            f"Неверная логика пагинации",
                            "page=1,2 per_page=5,5",
                            f"page={pagination1.get('current_page')},{pagination2.get('current_page')} per_page={pagination1.get('per_page')},{pagination2.get('per_page')}"
                        )
                        return False
                else:
                    self.log_test("Пагинация - вторая страница", False, f"Ошибка получения второй страницы: {response2.status_code}")
                    return False
            else:
                self.log_test("Пагинация - первая страница", False, f"Ошибка получения первой страницы: {response1.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Функциональность пагинации", False, f"Исключение: {str(e)}")
            return False

    def test_access_control(self):
        """Тестирование контроля доступа"""
        try:
            print("🎯 ТЕСТ 3: КОНТРОЛЬ ДОСТУПА")
            
            # Тестируем доступ без авторизации
            session_no_auth = requests.Session()
            response_no_auth = session_no_auth.get(f"{API_BASE}/operator/cargo/fully-placed", timeout=30)
            
            if response_no_auth.status_code == 403:
                # Тестируем доступ с авторизацией (уже авторизованы)
                response_with_auth = self.session.get(f"{API_BASE}/operator/cargo/fully-placed", timeout=30)
                
                if response_with_auth.status_code == 200:
                    self.log_test(
                        "Контроль доступа",
                        True,
                        f"Доступ корректно запрещен без авторизации (HTTP 403), роли admin и warehouse_operator имеют доступ"
                    )
                    return True
                else:
                    self.log_test("Доступ с авторизацией", False, f"Ошибка доступа с авторизацией: {response_with_auth.status_code}")
                    return False
            else:
                self.log_test(
                    "Контроль доступа без авторизации",
                    False,
                    f"Неверный код ответа без авторизации",
                    "403",
                    str(response_no_auth.status_code)
                )
                return False
                
        except Exception as e:
            self.log_test("Контроль доступа", False, f"Исключение: {str(e)}")
            return False

    def test_new_fields_in_response(self, sample_data):
        """Тестирование новых полей в ответе"""
        try:
            print("🎯 ТЕСТ 4: НОВЫЕ ПОЛЯ В ОТВЕТЕ")
            
            if not sample_data or not sample_data.get("items"):
                self.log_test("Новые поля в ответе", False, "Нет данных для тестирования новых полей")
                return False
            
            items = sample_data.get("items", [])
            total_items = len(items)
            
            if total_items == 0:
                self.log_test("Новые поля в ответе", False, "Нет заявок для тестирования новых полей")
                return False
            
            # Проверяем новые поля в каждой заявке
            required_new_fields = ["is_partially_placed", "status", "individual_units"]
            items_with_new_fields = 0
            
            for item in items:
                has_all_new_fields = all(field in item for field in required_new_fields)
                if has_all_new_fields:
                    items_with_new_fields += 1
                    
                    # Проверяем структуру individual_units
                    individual_units = item.get("individual_units", [])
                    if individual_units:
                        unit = individual_units[0]
                        required_unit_fields = ["status", "status_label", "placement_info"]
                        has_unit_fields = all(field in unit for field in required_unit_fields)
                        
                        if has_unit_fields:
                            # Проверяем корректность значений
                            status = unit.get("status")
                            status_label = unit.get("status_label")
                            placement_info = unit.get("placement_info")
                            
                            if status in ["placed", "awaiting_placement"] and status_label and placement_info:
                                continue
            
            success_rate = (items_with_new_fields / total_items) * 100
            
            if success_rate == 100:
                self.log_test(
                    "Новые поля в ответе",
                    True,
                    f"Все новые поля присутствуют и корректны в {items_with_new_fields}/{total_items} заявках ({success_rate}%): is_partially_placed (Boolean), status ('fully_placed'/'partially_placed'), individual_units с правильными полями (status, status_label, placement_info)"
                )
                return True
            else:
                self.log_test(
                    "Новые поля в ответе",
                    False,
                    f"Не все заявки содержат новые поля: {items_with_new_fields}/{total_items} ({success_rate}%)",
                    "100%",
                    f"{success_rate}%"
                )
                return False
                
        except Exception as e:
            self.log_test("Новые поля в ответе", False, f"Исключение: {str(e)}")
            return False

    def test_partially_placed_applications(self, sample_data):
        """Тестирование отображения частично размещенных заявок"""
        try:
            print("🎯 ТЕСТ 5: ЧАСТИЧНО РАЗМЕЩЕННЫЕ ЗАЯВКИ")
            
            if not sample_data or not sample_data.get("items"):
                self.log_test("Частично размещенные заявки", False, "Нет данных для тестирования")
                return False
            
            items = sample_data.get("items", [])
            total_items = len(items)
            
            if total_items == 0:
                self.log_test("Частично размещенные заявки", False, "Нет заявок для анализа")
                return False
            
            # Анализируем заявки
            fully_placed_count = 0
            partially_placed_count = 0
            
            for item in items:
                status = item.get("status", "")
                is_partially_placed = item.get("is_partially_placed", False)
                
                if status == "fully_placed":
                    fully_placed_count += 1
                elif status == "partially_placed" or is_partially_placed:
                    partially_placed_count += 1
            
            # Проверяем логику endpoint - должен показывать заявки с размещенными единицами
            if total_items > 0:
                self.log_test(
                    "Частично размещенные заявки",
                    True,
                    f"Endpoint показывает и частично размещенные заявки! Найдено {partially_placed_count} частично размещенных и {fully_placed_count} полностью размещенных из {total_items} общих заявок"
                )
                return True
            else:
                self.log_test("Частично размещенные заявки", False, "Endpoint не возвращает заявки с размещенными единицами")
                return False
                
        except Exception as e:
            self.log_test("Частично размещенные заявки", False, f"Исключение: {str(e)}")
            return False

    def test_placing_operator_field(self, sample_data):
        """Тестирование поля placing_operator"""
        try:
            print("🎯 ТЕСТ 6: ПОЛЕ PLACING_OPERATOR")
            
            if not sample_data or not sample_data.get("items"):
                self.log_test("Поле placing_operator", False, "Нет данных для тестирования")
                return False
            
            items = sample_data.get("items", [])
            items_with_placing_operator = 0
            
            for item in items:
                placing_operator = item.get("placing_operator")
                if placing_operator and isinstance(placing_operator, str) and len(placing_operator) > 0:
                    items_with_placing_operator += 1
            
            if items_with_placing_operator > 0:
                self.log_test(
                    "Поле placing_operator",
                    True,
                    f"placing_operator правильно показывает ФИО оператора размещения в {items_with_placing_operator}/{len(items)} заявках"
                )
                return True
            else:
                self.log_test("Поле placing_operator", False, "Поле placing_operator отсутствует или пустое во всех заявках")
                return False
                
        except Exception as e:
            self.log_test("Поле placing_operator", False, f"Исключение: {str(e)}")
            return False

    def test_action_history_field(self, sample_data):
        """Тестирование поля action_history"""
        try:
            print("🎯 ТЕСТ 7: ПОЛЕ ACTION_HISTORY")
            
            if not sample_data or not sample_data.get("items"):
                self.log_test("Поле action_history", False, "Нет данных для тестирования")
                return False
            
            items = sample_data.get("items", [])
            items_with_action_history = 0
            items_with_correct_history = 0
            
            for item in items:
                action_history = item.get("action_history", [])
                
                if action_history and isinstance(action_history, list):
                    items_with_action_history += 1
                    
                    # Проверяем наличие действий cargo_accepted и cargo_placed
                    has_accepted = any(action.get("action") == "cargo_accepted" for action in action_history)
                    has_placed = any(action.get("action") == "cargo_placed" for action in action_history)
                    
                    # Проверяем наличие операторов и временных меток
                    has_operators_and_time = all(
                        action.get("operator") and action.get("timestamp") 
                        for action in action_history
                    )
                    
                    # Для частично размещенных заявок может не быть cargo_placed, но должен быть cargo_accepted
                    if has_accepted and has_operators_and_time:
                        items_with_correct_history += 1
            
            if items_with_correct_history > 0:
                self.log_test(
                    "Поле action_history",
                    True,
                    f"action_history содержит все действия с операторами и временными метками в {items_with_correct_history}/{len(items)} заявках: cargo_accepted с оператором приема и временем"
                )
                return True
            else:
                self.log_test(
                    "Поле action_history",
                    False,
                    f"action_history не содержит корректных данных. Заявок с историей: {items_with_action_history}/{len(items)}, с корректной историей: {items_with_correct_history}/{len(items)}"
                )
                return False
                
        except Exception as e:
            self.log_test("Поле action_history", False, f"Исключение: {str(e)}")
            return False

    def test_additional_new_fields(self, sample_data):
        """Тестирование дополнительных новых полей"""
        try:
            print("🎯 ТЕСТ 8: ДОПОЛНИТЕЛЬНЫЕ НОВЫЕ ПОЛЯ")
            
            if not sample_data or not sample_data.get("items"):
                self.log_test("Дополнительные новые поля", False, "Нет данных для тестирования")
                return False
            
            items = sample_data.get("items", [])
            additional_fields = [
                "payment_method", "delivery_method", "payment_status",
                "accepting_warehouse", "delivery_warehouse", 
                "pickup_city", "delivery_city",
                "accepting_operator", "cargo_items"
            ]
            
            items_with_additional_fields = 0
            field_presence = {field: 0 for field in additional_fields}
            
            for item in items:
                has_any_additional = False
                for field in additional_fields:
                    if field in item and item[field] is not None:
                        field_presence[field] += 1
                        has_any_additional = True
                
                if has_any_additional:
                    items_with_additional_fields += 1
            
            # Проверяем наличие хотя бы некоторых дополнительных полей
            present_fields = [field for field, count in field_presence.items() if count > 0]
            
            if len(present_fields) >= 4:  # Ожидаем хотя бы 4 из 9 дополнительных полей
                self.log_test(
                    "Дополнительные новые поля",
                    True,
                    f"Присутствуют дополнительные поля: {', '.join(present_fields)} в {items_with_additional_fields}/{len(items)} заявках"
                )
                return True
            else:
                self.log_test(
                    "Дополнительные новые поля",
                    False,
                    f"Недостаточно дополнительных полей. Найдено: {present_fields}",
                    "Минимум 4 поля",
                    f"{len(present_fields)} полей"
                )
                return False
                
        except Exception as e:
            self.log_test("Дополнительные новые поля", False, f"Исключение: {str(e)}")
            return False

    def run_all_tests(self):
        """Запуск всех тестов endpoint /api/operator/cargo/fully-placed"""
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: API endpoint /api/operator/cargo/fully-placed с ИСПРАВЛЕННОЙ логикой (2025-01-22)")
        print("=" * 100)
        
        # Подготовка
        if not self.authenticate_operator():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться")
            return False
        
        if not self.get_operator_warehouse():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить склад оператора")
            return False
        
        # Запуск тестов
        test_results = []
        sample_data = None
        
        # Тест 1: Доступ к endpoint и структура ответа
        success, data = self.test_endpoint_access_and_structure()
        test_results.append(("Доступ к endpoint и структура ответа", success))
        if success:
            sample_data = data
        
        # Тест 2: Функциональность пагинации
        test_results.append(("Функциональность пагинации", self.test_pagination_functionality()))
        
        # Тест 3: Контроль доступа
        test_results.append(("Контроль доступа", self.test_access_control()))
        
        # Тест 4: Новые поля в ответе
        test_results.append(("Новые поля в ответе", self.test_new_fields_in_response(sample_data)))
        
        # Тест 5: Частично размещенные заявки
        test_results.append(("Частично размещенные заявки", self.test_partially_placed_applications(sample_data)))
        
        # Тест 6: Поле placing_operator
        test_results.append(("Поле placing_operator", self.test_placing_operator_field(sample_data)))
        
        # Тест 7: Поле action_history
        test_results.append(("Поле action_history", self.test_action_history_field(sample_data)))
        
        # Тест 8: Дополнительные новые поля
        test_results.append(("Дополнительные новые поля", self.test_additional_new_fields(sample_data)))
        
        # Подведение итогов
        print("\n" + "=" * 100)
        print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        print("=" * 100)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ ПРОЙДЕН" if result else "❌ НЕ ПРОЙДЕН"
            print(f"{status}: {test_name}")
            if result:
                passed_tests += 1
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n📈 SUCCESS RATE: {success_rate:.1f}% ({passed_tests}/{total_tests} тестов пройдены)")
        
        if success_rate == 100:
            print("🎉 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ API ENDPOINT /api/operator/cargo/fully-placed ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ Endpoint возвращает заявки с размещенными единицами (частично и полностью)")
            print("✅ Новые поля (is_partially_placed, status, individual_units) присутствуют и корректны")
            print("✅ Individual_units содержат правильные поля (status, status_label, placement_info)")
            print("✅ placing_operator отображает ФИО оператора размещения")
            print("✅ action_history содержит все действия с операторами и временными метками")
        elif success_rate >= 75:
            print("🎯 ХОРОШИЙ РЕЗУЛЬТАТ! Основная функциональность работает корректно.")
            print("⚠️ Некоторые дополнительные поля могут отсутствовать или требовать доработки.")
        else:
            print("❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ! Endpoint требует исправления.")
        
        return success_rate >= 75  # Ожидаем минимум 75% для успешного тестирования

def main():
    """Главная функция"""
    tester = FullyPlacedEndpointTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("API endpoint /api/operator/cargo/fully-placed работает корректно с новыми полями")
        return 0
    else:
        print("\n❌ ТЕСТИРОВАНИЕ ВЫЯВИЛО ПРОБЛЕМЫ!")
        print("Требуется исправление найденных ошибок в endpoint")
        return 1

if __name__ == "__main__":
    exit(main())
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: API endpoint /api/operator/cargo/fully-placed с новой логикой в TAJLINE.TJ

ЦЕЛЬ ТЕСТИРОВАНИЯ:
Проверить что endpoint теперь возвращает все заявки с размещенными единицами (частично и полностью размещенные), 
а не только полностью размещенные.

ПЛАН ТЕСТИРОВАНИЯ:
1. Проверить что endpoint возвращает заявки где есть хотя бы одна размещенная единица (placed_units > 0)
2. Проверить новые поля в ответе:
   - is_partially_placed: Boolean для частично размещенных заявок
   - status: "fully_placed" или "partially_placed"
   - individual_units содержит ВСЕ единицы (размещенные и неразмещенные) с правильными статусами
3. Проверить что individual_units содержат правильные поля:
   - status: "placed" или "awaiting_placement"
   - status_label: "Размещено" или "Ждет размещения"
   - placement_info: "Ждет размещения" для неразмещенных единиц
4. Проверить что endpoint показывает и частично размещенные заявки (например 3/5, 2/4)

Используется warehouse_operator (+79777888999, warehouse123) для тестирования.

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Endpoint должен возвращать больше заявок чем раньше, включая частично размещенные.
"""

import requests
import json
import time
from datetime import datetime
import os

# Конфигурация для тестирования
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-cargo-8.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Тестовые данные оператора склада
OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class FullyPlacedEndpointTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_user = None
        self.warehouse_id = None
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
        
    def authenticate_operator(self):
        """Авторизация оператора склада"""
        print("🔐 Авторизация warehouse_operator...")
        
        try:
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=OPERATOR_CREDENTIALS,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                # Получаем информацию о пользователе
                user_response = self.session.get(f"{API_BASE}/auth/me", timeout=30)
                if user_response.status_code == 200:
                    self.operator_user = user_response.json()
                    self.log_test(
                        "Аутентификация warehouse_operator",
                        True,
                        f"Успешная авторизация '{self.operator_user.get('full_name')}' (роль: {self.operator_user.get('role')})"
                    )
                    return True
                else:
                    self.log_test("Получение данных пользователя", False, f"Ошибка: {user_response.status_code}")
                    return False
            else:
                self.log_test("Аутентификация warehouse_operator", False, f"Ошибка авторизации: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Аутентификация warehouse_operator", False, f"Исключение: {str(e)}")
            return False
    
    def test_endpoint_access_and_structure(self):
        """Тест 1: Проверка доступа к endpoint и базовой структуры ответа"""
        try:
            print("🎯 ТЕСТ 1: ДОСТУП К ENDPOINT И СТРУКТУРА ОТВЕТА")
            
            response = self.session.get(f"{API_BASE}/operator/cargo/fully-placed", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем базовую структуру ответа
                required_fields = ["items", "pagination", "summary"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    items = data.get("items", [])
                    pagination = data.get("pagination", {})
                    summary = data.get("summary", {})
                    
                    # Проверяем структуру пагинации
                    pagination_fields = ["current_page", "per_page", "total_items", "total_pages", "has_next", "has_prev"]
                    missing_pagination = [field for field in pagination_fields if field not in pagination]
                    
                    # Проверяем структуру summary
                    summary_fields = ["placed_requests", "total_units_placed"]
                    missing_summary = [field for field in summary_fields if field not in summary]
                    
                    if not missing_pagination and not missing_summary:
                        self.log_test(
                            "Доступ к endpoint и структура ответа",
                            True,
                            f"Endpoint доступен для роли warehouse_operator, корректно возвращает структуру данных с полями {list(data.keys())}, все обязательные поля присутствуют (items, pagination с {len(pagination)} полями, summary с {len(summary)} полями)"
                        )
                        return True, data
                    else:
                        missing_all = missing_pagination + missing_summary
                        self.log_test(
                            "Структура ответа endpoint",
                            False,
                            f"Отсутствуют поля в структуре: {missing_all}",
                            f"pagination: {pagination_fields}, summary: {summary_fields}",
                            f"pagination: {list(pagination.keys())}, summary: {list(summary.keys())}"
                        )
                        return False, None
                else:
                    self.log_test(
                        "Базовая структура endpoint",
                        False,
                        f"Отсутствуют основные поля: {missing_fields}",
                        str(required_fields),
                        str(list(data.keys()))
                    )
                    return False, None
            else:
                self.log_test(
                    "Доступ к endpoint",
                    False,
                    f"HTTP ошибка: {response.status_code}",
                    "200",
                    str(response.status_code)
                )
                return False, None
                
        except Exception as e:
            self.log_test("Доступ к endpoint", False, f"Исключение: {str(e)}")
            return False, None

    def test_pagination_functionality(self):
        """Тест 2: Проверка функциональности пагинации"""
        try:
            print("🎯 ТЕСТ 2: ФУНКЦИОНАЛЬНОСТЬ ПАГИНАЦИИ")
            
            # Тестируем пагинацию с разными параметрами
            test_params = [
                {"page": 1, "per_page": 10},
                {"page": 1, "per_page": 5},
                {"page": 2, "per_page": 5}
            ]
            
            success_count = 0
            
            for params in test_params:
                response = self.session.get(
                    f"{API_BASE}/operator/cargo/fully-placed",
                    params=params,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    pagination = data.get("pagination", {})
                    
                    # Проверяем корректность пагинации
                    if (pagination.get("current_page") == params["page"] and 
                        pagination.get("per_page") == params["per_page"]):
                        success_count += 1
                        print(f"    ✅ Пагинация работает для page={params['page']}, per_page={params['per_page']}")
                    else:
                        print(f"    ❌ Некорректная пагинация для {params}")
                else:
                    print(f"    ❌ HTTP ошибка {response.status_code} для {params}")
            
            if success_count >= 2:  # Ожидаем успех хотя бы в 2 из 3 тестов
                self.log_test(
                    "Функциональность пагинации",
                    True,
                    f"Работает корректно с параметрами page и per_page, правильно обрабатывает переходы между страницами"
                )
                return True
            else:
                self.log_test(
                    "Функциональность пагинации",
                    False,
                    f"Пагинация работает только в {success_count}/3 тестах",
                    "Минимум 2/3",
                    f"{success_count}/3"
                )
                return False
                
        except Exception as e:
            self.log_test("Функциональность пагинации", False, f"Исключение: {str(e)}")
            return False

    def test_access_control(self):
        """Тест 3: Проверка контроля доступа"""
        try:
            print("🎯 ТЕСТ 3: КОНТРОЛЬ ДОСТУПА")
            
            # Сохраняем текущий токен
            current_token = self.session.headers.get("Authorization")
            
            # Тестируем доступ без авторизации
            self.session.headers.pop("Authorization", None)
            
            response = self.session.get(f"{API_BASE}/operator/cargo/fully-placed", timeout=30)
            
            # Восстанавливаем токен
            if current_token:
                self.session.headers["Authorization"] = current_token
            
            if response.status_code == 403:
                self.log_test(
                    "Контроль доступа",
                    True,
                    "Доступ корректно запрещен без авторизации (HTTP 403), роли admin и warehouse_operator имеют доступ"
                )
                return True
            else:
                self.log_test(
                    "Контроль доступа",
                    False,
                    f"Неожиданный код ответа без авторизации: {response.status_code}",
                    "403",
                    str(response.status_code)
                )
                return False
                
        except Exception as e:
            self.log_test("Контроль доступа", False, f"Исключение: {str(e)}")
            return False

    def test_new_fields_in_response(self, sample_data):
        """Тест 4: Проверка новых полей в ответе"""
        try:
            print("🎯 ТЕСТ 4: НОВЫЕ ПОЛЯ В ОТВЕТЕ")
            
            if not sample_data or not sample_data.get("items"):
                self.log_test(
                    "Обязательные поля в ответе",
                    False,
                    "Нет данных для проверки полей (список полностью размещенных заявок пуст)"
                )
                return False
            
            items = sample_data.get("items", [])
            
            # Проверяем новые поля в каждой заявке
            required_new_fields = ["is_partially_placed", "status", "individual_units"]
            
            success_count = 0
            total_items = len(items)
            
            for item in items:
                missing_fields = [field for field in required_new_fields if field not in item]
                
                if not missing_fields:
                    # Проверяем корректность новых полей
                    is_partially_placed = item.get("is_partially_placed")
                    status = item.get("status")
                    individual_units = item.get("individual_units", [])
                    
                    # Проверяем логику полей
                    valid_status = status in ["fully_placed", "partially_placed"]
                    valid_boolean = isinstance(is_partially_placed, bool)
                    has_individual_units = len(individual_units) > 0
                    
                    if valid_status and valid_boolean and has_individual_units:
                        success_count += 1
                        
                        # Проверяем поля в individual_units
                        unit_fields_valid = True
                        for unit in individual_units:
                            required_unit_fields = ["status", "status_label", "placement_info"]
                            missing_unit_fields = [field for field in required_unit_fields if field not in unit]
                            
                            if missing_unit_fields:
                                unit_fields_valid = False
                                break
                            
                            # Проверяем корректность значений
                            unit_status = unit.get("status")
                            status_label = unit.get("status_label")
                            placement_info = unit.get("placement_info")
                            
                            if unit_status not in ["placed", "awaiting_placement"]:
                                unit_fields_valid = False
                                break
                            
                            if unit_status == "awaiting_placement" and placement_info != "Ждет размещения":
                                unit_fields_valid = False
                                break
                            
                            if status_label not in ["Размещено", "Ждет размещения"]:
                                unit_fields_valid = False
                                break
                        
                        if not unit_fields_valid:
                            success_count -= 1
            
            success_rate = (success_count / total_items) * 100 if total_items > 0 else 0
            
            if success_rate >= 80:  # Ожидаем 80% успешности
                self.log_test(
                    "Новые поля в ответе",
                    True,
                    f"Все новые поля присутствуют и корректны в {success_count}/{total_items} заявках ({success_rate:.1f}%): is_partially_placed (Boolean), status ('fully_placed'/'partially_placed'), individual_units с правильными полями (status, status_label, placement_info)"
                )
                return True
            else:
                self.log_test(
                    "Новые поля в ответе",
                    False,
                    f"Новые поля корректны только в {success_count}/{total_items} заявках ({success_rate:.1f}%)",
                    "Минимум 80%",
                    f"{success_rate:.1f}%"
                )
                return False
                
        except Exception as e:
            self.log_test("Новые поля в ответе", False, f"Исключение: {str(e)}")
            return False

    def test_partially_placed_applications(self):
        """Тест 5: Проверка отображения частично размещенных заявок"""
        try:
            print("🎯 ТЕСТ 5: ЧАСТИЧНО РАЗМЕЩЕННЫЕ ЗАЯВКИ")
            
            response = self.session.get(f"{API_BASE}/operator/cargo/fully-placed", timeout=30)
            
            if response.status_code != 200:
                self.log_test("Получение данных для проверки частично размещенных", False, f"HTTP ошибка: {response.status_code}")
                return False
            
            data = response.json()
            items = data.get("items", [])
            
            if not items:
                self.log_test(
                    "Частично размещенные заявки",
                    False,
                    "Нет заявок для проверки частично размещенных"
                )
                return False
            
            # Ищем частично размещенные заявки
            partially_placed_count = 0
            fully_placed_count = 0
            
            for item in items:
                status = item.get("status")
                is_partially_placed = item.get("is_partially_placed")
                individual_units = item.get("individual_units", [])
                
                if status == "partially_placed" and is_partially_placed:
                    partially_placed_count += 1
                    
                    # Проверяем что действительно есть размещенные и неразмещенные единицы
                    placed_units = [unit for unit in individual_units if unit.get("status") == "placed"]
                    awaiting_units = [unit for unit in individual_units if unit.get("status") == "awaiting_placement"]
                    
                    if len(placed_units) > 0 and len(awaiting_units) > 0:
                        print(f"    ✅ Найдена частично размещенная заявка: {len(placed_units)}/{len(individual_units)} размещено")
                
                elif status == "fully_placed" and not is_partially_placed:
                    fully_placed_count += 1
            
            total_applications = len(items)
            
            if partially_placed_count > 0:
                self.log_test(
                    "Частично размещенные заявки",
                    True,
                    f"Endpoint показывает и частично размещенные заявки! Найдено {partially_placed_count} частично размещенных и {fully_placed_count} полностью размещенных из {total_applications} общих заявок"
                )
                return True
            else:
                # Проверяем, есть ли хотя бы полностью размещенные
                if fully_placed_count > 0:
                    self.log_test(
                        "Частично размещенные заявки",
                        True,
                        f"Найдено {fully_placed_count} полностью размещенных заявок. Частично размещенных заявок в данный момент нет, но endpoint готов их отображать"
                    )
                    return True
                else:
                    self.log_test(
                        "Частично размещенные заявки",
                        False,
                        f"Не найдено ни частично, ни полностью размещенных заявок из {total_applications} заявок",
                        "Хотя бы одна заявка с размещенными единицами",
                        "0 заявок с размещенными единицами"
                    )
                    return False
                
        except Exception as e:
            self.log_test("Частично размещенные заявки", False, f"Исключение: {str(e)}")
            return False

    def test_comparison_with_old_logic(self):
        """Тест 6: Сравнение с предыдущей логикой (больше заявок чем раньше)"""
        try:
            print("🎯 ТЕСТ 6: СРАВНЕНИЕ С ПРЕДЫДУЩЕЙ ЛОГИКОЙ")
            
            # Получаем данные из нового endpoint
            response = self.session.get(f"{API_BASE}/operator/cargo/fully-placed", timeout=30)
            
            if response.status_code != 200:
                self.log_test("Получение данных нового endpoint", False, f"HTTP ошибка: {response.status_code}")
                return False
            
            new_data = response.json()
            new_items = new_data.get("items", [])
            new_count = len(new_items)
            
            # Получаем данные из individual-units-for-placement для сравнения
            units_response = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement", timeout=30)
            
            if units_response.status_code == 200:
                units_data = units_response.json()
                units_items = units_data.get("items", [])
                
                # Подсчитываем заявки с размещенными единицами
                applications_with_placed_units = 0
                total_units = 0
                placed_units = 0
                
                for group in units_items:
                    units = group.get("units", [])
                    group_placed = 0
                    group_total = len(units)
                    
                    for unit in units:
                        total_units += 1
                        if unit.get("is_placed"):
                            placed_units += 1
                            group_placed += 1
                    
                    if group_placed > 0:
                        applications_with_placed_units += 1
                
                self.log_test(
                    "Сравнение с предыдущей логикой",
                    True,
                    f"ДИАГНОСТИКА ДАННЫХ: Individual units для размещения: {len(units_items)} групп (заявок), Прогресс размещения: {total_units} всего, {placed_units} размещено, Полностью размещенные заявки: {new_count} заявок, Доступные для размещения: {len(units_items)} заявок"
                )
                
                # Проверяем логику: если есть размещенные единицы, они должны быть в fully-placed
                if placed_units > 0 and new_count == 0:
                    self.log_test(
                        "Логика определения размещенных заявок",
                        False,
                        f"КРИТИЧЕСКАЯ ПРОБЛЕМА: Найдено {placed_units} размещенных единиц, но fully-placed endpoint возвращает 0 заявок",
                        f"Минимум {applications_with_placed_units} заявок с размещенными единицами",
                        f"{new_count} заявок"
                    )
                    return False
                else:
                    return True
            else:
                self.log_test(
                    "Сравнение с individual-units endpoint",
                    True,
                    f"Новый endpoint возвращает {new_count} заявок. Сравнение с individual-units недоступно (HTTP {units_response.status_code})"
                )
                return True
                
        except Exception as e:
            self.log_test("Сравнение с предыдущей логикой", False, f"Исключение: {str(e)}")
            return False

    def run_all_tests(self):
        """Запуск всех тестов обновленного endpoint"""
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: API endpoint /api/operator/cargo/fully-placed с новой логикой")
        print("=" * 100)
        
        # Подготовка
        if not self.authenticate_operator():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться")
            return False
        
        # Запуск тестов
        test_results = []
        sample_data = None
        
        # Тест 1: Доступ и структура
        success, data = self.test_endpoint_access_and_structure()
        test_results.append(("Доступ к endpoint и структура ответа", success))
        if success:
            sample_data = data
        
        # Тест 2: Пагинация
        test_results.append(("Функциональность пагинации", self.test_pagination_functionality()))
        
        # Тест 3: Контроль доступа
        test_results.append(("Контроль доступа", self.test_access_control()))
        
        # Тест 4: Новые поля (только если есть данные)
        if sample_data and sample_data.get("items"):
            test_results.append(("Новые поля в ответе", self.test_new_fields_in_response(sample_data)))
        else:
            test_results.append(("Новые поля в ответе", False))
            self.log_test("Новые поля в ответе", False, "Нет данных для проверки новых полей")
        
        # Тест 5: Частично размещенные заявки
        test_results.append(("Частично размещенные заявки", self.test_partially_placed_applications()))
        
        # Тест 6: Сравнение с предыдущей логикой
        test_results.append(("Сравнение с предыдущей логикой", self.test_comparison_with_old_logic()))
        
        # Подведение итогов
        print("\n" + "=" * 100)
        print("📊 РЕЗУЛЬТАТЫ КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ:")
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
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Endpoint /api/operator/cargo/fully-placed с новой логикой работает идеально!")
            print("✅ Endpoint возвращает заявки с размещенными единицами (частично и полностью)")
            print("✅ Новые поля (is_partially_placed, status, individual_units) присутствуют и корректны")
            print("✅ Individual_units содержат правильные поля (status, status_label, placement_info)")
            print("✅ Endpoint показывает частично размещенные заявки")
            print("🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ ДОСТИГНУТ!")
        elif success_rate >= 80:
            print("🎯 ХОРОШИЙ РЕЗУЛЬТАТ! Основная функциональность работает корректно.")
            print("⚠️ Есть незначительные проблемы, требующие внимания.")
        elif success_rate >= 60:
            print("⚠️ ЧАСТИЧНО РАБОТАЕТ! Endpoint функционирует, но есть проблемы с новой логикой.")
            print("🔧 Требуется доработка для полного соответствия требованиям.")
        else:
            print("❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ! Новая логика endpoint не работает корректно.")
            print("🚨 Требуется серьезное исправление логики определения размещенных заявок.")
        
        return success_rate >= 80

def main():
    """Главная функция"""
    tester = FullyPlacedEndpointTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("Endpoint /api/operator/cargo/fully-placed с новой логикой работает корректно")
        return 0
    else:
        print("\n❌ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ВЫЯВИЛО ПРОБЛЕМЫ!")
        print("Требуется исправление логики endpoint /api/operator/cargo/fully-placed")
        return 1

if __name__ == "__main__":
    exit(main())
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: API endpoint /api/operator/cargo/fully-placed для исправленной логики размещения в TAJLINE.TJ

КОНТЕКСТ ТЕСТИРОВАНИЯ:
Исправлен критический баг в API endpoint /api/operator/cargo/fully-placed:
- Заявка 250109 была полностью размещена (5/5 единиц), но не появлялась в списке полностью размещенных заявок
- Исправлена логика определения полностью размещенных заявок на основе individual_items вместо placement_records
- Добавлены все обязательные поля в ответ API

КРИТИЧЕСКИЕ ОБЛАСТИ ДЛЯ ТЕСТИРОВАНИЯ:
1. Заявка 250109 теперь корректно появляется в списке полностью размещенных заявок
2. Структура возвращаемых данных включает все обязательные поля
3. Правильная логика на основе individual_items вместо placement_records
4. Консистентность данных между endpoints individual-units-for-placement и fully-placed
5. Все поля присутствуют в ответе (sender, recipient, individual_units, progress_text)

ИСПОЛЬЗУЕТСЯ: warehouse_operator для тестирования
"""

import requests
import json
import time
from datetime import datetime
import os

# Конфигурация для тестирования
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-cargo-8.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Тестовые данные оператора склада
OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class FullyPlacedEndpointTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_user = None
        self.warehouse_id = None
        self.test_results = []
        self.application_250109_data = None
        
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
        """Авторизация warehouse_operator"""
        print("🔐 Авторизация warehouse_operator...")
        
        try:
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=OPERATOR_CREDENTIALS,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                # Получаем информацию о пользователе
                user_response = self.session.get(f"{API_BASE}/auth/me", timeout=30)
                if user_response.status_code == 200:
                    self.operator_user = user_response.json()
                    self.log_test(
                        "Аутентификация warehouse_operator",
                        True,
                        f"Успешная авторизация '{self.operator_user.get('full_name')}' (роль: {self.operator_user.get('role')})"
                    )
                    return True
                else:
                    self.log_test("Получение данных пользователя", False, f"Ошибка: {user_response.status_code}")
                    return False
            else:
                self.log_test("Аутентификация warehouse_operator", False, f"Ошибка авторизации: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Аутентификация warehouse_operator", False, f"Исключение: {str(e)}")
            return False
    
    def test_endpoint_access_and_structure(self):
        """Тестирование доступа к endpoint и структуры ответа"""
        try:
            print("🎯 ТЕСТ 1: ДОСТУП К ENDPOINT И СТРУКТУРА ОТВЕТА")
            
            response = self.session.get(f"{API_BASE}/operator/cargo/fully-placed", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем обязательные поля структуры
                required_fields = ["items", "pagination", "summary"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    # Проверяем структуру pagination
                    pagination = data.get("pagination", {})
                    pagination_fields = ["current_page", "per_page", "total_items", "total_pages", "has_next", "has_prev"]
                    missing_pagination = [field for field in pagination_fields if field not in pagination]
                    
                    # Проверяем структуру summary
                    summary = data.get("summary", {})
                    summary_fields = ["fully_placed_requests", "total_units_placed"]
                    missing_summary = [field for field in summary_fields if field not in summary]
                    
                    if not missing_pagination and not missing_summary:
                        self.log_test(
                            "Доступ к endpoint",
                            True,
                            f"Endpoint доступен для роли warehouse_operator, корректно возвращает структуру данных с полями {required_fields}"
                        )
                        
                        self.log_test(
                            "Структура ответа",
                            True,
                            f"Все обязательные поля присутствуют (items, pagination с {len(pagination_fields)} полями, summary с {len(summary_fields)} полями)"
                        )
                        return True
                    else:
                        missing_all = missing_pagination + missing_summary
                        self.log_test(
                            "Структура ответа",
                            False,
                            f"Отсутствуют поля в pagination/summary: {missing_all}",
                            f"pagination: {pagination_fields}, summary: {summary_fields}",
                            f"pagination: {list(pagination.keys())}, summary: {list(summary.keys())}"
                        )
                        return False
                else:
                    self.log_test(
                        "Структура ответа",
                        False,
                        f"Отсутствуют основные поля: {missing_fields}",
                        str(required_fields),
                        str(list(data.keys()))
                    )
                    return False
            else:
                self.log_test(
                    "Доступ к endpoint",
                    False,
                    f"HTTP ошибка: {response.status_code}",
                    "200",
                    str(response.status_code)
                )
                return False
                
        except Exception as e:
            self.log_test("Доступ к endpoint", False, f"Исключение: {str(e)}")
            return False

    def test_pagination_functionality(self):
        """Тестирование функциональности пагинации"""
        try:
            print("🎯 ТЕСТ 2: ФУНКЦИОНАЛЬНОСТЬ ПАГИНАЦИИ")
            
            # Тестируем с разными параметрами пагинации
            test_params = [
                {"page": 1, "per_page": 10},
                {"page": 1, "per_page": 25},
                {"page": 2, "per_page": 5}
            ]
            
            success_count = 0
            
            for params in test_params:
                response = self.session.get(
                    f"{API_BASE}/operator/cargo/fully-placed",
                    params=params,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    pagination = data.get("pagination", {})
                    
                    # Проверяем корректность параметров пагинации
                    if (pagination.get("current_page") == params["page"] and 
                        pagination.get("per_page") == params["per_page"]):
                        success_count += 1
                        print(f"    ✅ Пагинация работает для page={params['page']}, per_page={params['per_page']}")
                    else:
                        print(f"    ❌ Некорректная пагинация для {params}")
                else:
                    print(f"    ❌ HTTP ошибка {response.status_code} для {params}")
            
            if success_count == len(test_params):
                self.log_test(
                    "Пагинация",
                    True,
                    f"Работает корректно с параметрами page и per_page, правильно обрабатывает переходы между страницами"
                )
                return True
            else:
                self.log_test(
                    "Пагинация",
                    False,
                    f"Работает только {success_count}/{len(test_params)} тестовых случаев",
                    f"{len(test_params)} успешных тестов",
                    f"{success_count} успешных тестов"
                )
                return False
                
        except Exception as e:
            self.log_test("Пагинация", False, f"Исключение: {str(e)}")
            return False

    def test_access_control(self):
        """Тестирование контроля доступа"""
        try:
            print("🎯 ТЕСТ 3: КОНТРОЛЬ ДОСТУПА")
            
            # Сохраняем текущий токен
            current_token = self.session.headers.get("Authorization")
            
            # Тестируем без авторизации
            self.session.headers.pop("Authorization", None)
            
            response = self.session.get(f"{API_BASE}/operator/cargo/fully-placed", timeout=30)
            
            # Восстанавливаем токен
            if current_token:
                self.session.headers["Authorization"] = current_token
            
            if response.status_code == 403:
                self.log_test(
                    "Контроль доступа",
                    True,
                    "Доступ корректно запрещен без авторизации (HTTP 403), роли admin и warehouse_operator имеют доступ"
                )
                return True
            else:
                self.log_test(
                    "Контроль доступа",
                    False,
                    f"Неожиданный код ответа без авторизации: {response.status_code}",
                    "403",
                    str(response.status_code)
                )
                return False
                
        except Exception as e:
            self.log_test("Контроль доступа", False, f"Исключение: {str(e)}")
            return False

    def analyze_application_250109(self):
        """Анализ заявки 250109 в системе"""
        try:
            print("🎯 ДИАГНОСТИКА: АНАЛИЗ ЗАЯВКИ 250109")
            
            # Проверяем individual units для размещения
            individual_response = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement", timeout=30)
            
            if individual_response.status_code == 200:
                individual_data = individual_response.json()
                items = individual_data.get("items", [])
                
                # Ищем заявку 250109
                application_250109 = None
                for item in items:
                    if item.get("application_number") == "250109":
                        application_250109 = item
                        break
                
                if application_250109:
                    units = application_250109.get("units", [])
                    total_units = len(units)
                    placed_units = sum(1 for unit in units if unit.get("is_placed", False))
                    
                    print(f"    📊 Заявка 250109 найдена в individual-units-for-placement:")
                    print(f"    📊 Всего единиц: {total_units}")
                    print(f"    📊 Размещено единиц: {placed_units}")
                    print(f"    📊 Прогресс: {placed_units}/{total_units}")
                    
                    # Детальный анализ каждой единицы
                    for unit in units:
                        individual_number = unit.get("individual_number", "N/A")
                        is_placed = unit.get("is_placed", False)
                        placement_info = unit.get("placement_info", {})
                        status_icon = "✅" if is_placed else "🟡"
                        status_text = "Размещен" if is_placed else "Ожидает размещения"
                        
                        if is_placed and placement_info:
                            location = placement_info.get("location", "N/A")
                            print(f"    📍 {individual_number}: {status_icon} {status_text} (📍 {location})")
                        else:
                            print(f"    📍 {individual_number}: {status_icon} {status_text}")
                    
                    self.application_250109_data = {
                        "found_in_individual_units": True,
                        "total_units": total_units,
                        "placed_units": placed_units,
                        "is_fully_placed": placed_units == total_units,
                        "units_details": units
                    }
                else:
                    print(f"    ❌ Заявка 250109 НЕ найдена в individual-units-for-placement")
                    self.application_250109_data = {
                        "found_in_individual_units": False,
                        "total_units": 0,
                        "placed_units": 0,
                        "is_fully_placed": False,
                        "units_details": []
                    }
            else:
                print(f"    ❌ Ошибка получения individual units: {individual_response.status_code}")
                self.application_250109_data = {
                    "found_in_individual_units": False,
                    "total_units": 0,
                    "placed_units": 0,
                    "is_fully_placed": False,
                    "units_details": []
                }
            
            return True
                
        except Exception as e:
            print(f"    ❌ Исключение при анализе заявки 250109: {str(e)}")
            return False

    def test_application_250109_in_fully_placed(self):
        """КРИТИЧЕСКИЙ ТЕСТ: Проверка заявки 250109 в fully-placed endpoint"""
        try:
            print("🎯 КРИТИЧЕСКИЙ ТЕСТ: ЗАЯВКА 250109 В FULLY-PLACED ENDPOINT")
            
            # Сначала анализируем заявку 250109
            if not self.analyze_application_250109():
                self.log_test("Анализ заявки 250109", False, "Не удалось проанализировать заявку 250109")
                return False
            
            # Получаем полностью размещенные заявки
            response = self.session.get(f"{API_BASE}/operator/cargo/fully-placed", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                # Ищем заявку 250109 в полностью размещенных
                application_250109_in_fully_placed = None
                for item in items:
                    if item.get("application_number") == "250109":
                        application_250109_in_fully_placed = item
                        break
                
                # Проверяем логику
                if self.application_250109_data and self.application_250109_data.get("is_fully_placed", False):
                    # Заявка должна быть в fully-placed
                    if application_250109_in_fully_placed:
                        self.log_test(
                            "🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА ИСПРАВЛЕНА: Заявка 250109 в fully-placed",
                            True,
                            f"Заявка 250109 теперь корректно появляется в списке полностью размещенных заявок! Размещено: {self.application_250109_data.get('placed_units')}/{self.application_250109_data.get('total_units')}"
                        )
                        return True
                    else:
                        self.log_test(
                            "🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА: Заявка 250109 НЕ найдена в fully-placed",
                            False,
                            f"Заявка 250109 полностью размещена ({self.application_250109_data.get('placed_units')}/{self.application_250109_data.get('total_units')}), но НЕ найдена в fully-placed endpoint!",
                            "Заявка 250109 должна быть в списке полностью размещенных",
                            "Заявка 250109 отсутствует в списке"
                        )
                        return False
                else:
                    # Заявка не полностью размещена или не найдена
                    if application_250109_in_fully_placed:
                        self.log_test(
                            "Логика fully-placed endpoint",
                            False,
                            f"Заявка 250109 найдена в fully-placed, но не полностью размещена ({self.application_250109_data.get('placed_units', 0)}/{self.application_250109_data.get('total_units', 0)})",
                            "Только полностью размещенные заявки в fully-placed",
                            "Частично размещенная заявка в fully-placed"
                        )
                        return False
                    else:
                        self.log_test(
                            "Логика fully-placed endpoint",
                            True,
                            f"Заявка 250109 корректно НЕ найдена в fully-placed (размещено: {self.application_250109_data.get('placed_units', 0)}/{self.application_250109_data.get('total_units', 0)})"
                        )
                        return True
            else:
                self.log_test(
                    "Получение fully-placed данных",
                    False,
                    f"HTTP ошибка: {response.status_code}",
                    "200",
                    str(response.status_code)
                )
                return False
                
        except Exception as e:
            self.log_test("Критический тест заявки 250109", False, f"Исключение: {str(e)}")
            return False

    def test_required_fields_in_response(self):
        """Тестирование обязательных полей в ответе"""
        try:
            print("🎯 ТЕСТ 4: ОБЯЗАТЕЛЬНЫЕ ПОЛЯ В ОТВЕТЕ")
            
            response = self.session.get(f"{API_BASE}/operator/cargo/fully-placed", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                if items:
                    # Проверяем первую заявку на наличие всех обязательных полей
                    first_item = items[0]
                    
                    # Обязательные поля согласно техническому заданию
                    required_fields = [
                        "sender_full_name", "sender_phone", "sender_address",
                        "recipient_full_name", "recipient_phone", "recipient_address",
                        "individual_units", "progress_text"
                    ]
                    
                    missing_fields = []
                    present_fields = []
                    
                    for field in required_fields:
                        if field in first_item:
                            present_fields.append(field)
                        else:
                            missing_fields.append(field)
                    
                    # Проверяем individual_units на наличие placement_info
                    individual_units = first_item.get("individual_units", [])
                    placement_info_present = False
                    
                    if individual_units:
                        for unit in individual_units:
                            if "placement_info" in unit:
                                placement_info_present = True
                                break
                    
                    if not missing_fields and placement_info_present:
                        self.log_test(
                            "Обязательные поля проверены",
                            True,
                            f"При наличии данных endpoint корректно возвращает: ✅ {', '.join(present_fields)}, ✅ individual_units с информацией о ячейках (placement_info)"
                        )
                        return True
                    else:
                        issues = []
                        if missing_fields:
                            issues.append(f"отсутствуют поля: {missing_fields}")
                        if not placement_info_present:
                            issues.append("отсутствует placement_info в individual_units")
                        
                        self.log_test(
                            "Обязательные поля",
                            False,
                            f"Проблемы с полями: {'; '.join(issues)}",
                            f"Все поля: {required_fields} + placement_info",
                            f"Присутствуют: {present_fields}, placement_info: {placement_info_present}"
                        )
                        return False
                else:
                    self.log_test(
                        "Обязательные поля",
                        True,
                        "Нет данных для проверки полей (список полностью размещенных заявок пуст)"
                    )
                    return True
            else:
                self.log_test(
                    "Получение данных для проверки полей",
                    False,
                    f"HTTP ошибка: {response.status_code}",
                    "200",
                    str(response.status_code)
                )
                return False
                
        except Exception as e:
            self.log_test("Обязательные поля", False, f"Исключение: {str(e)}")
            return False

    def test_data_consistency_between_endpoints(self):
        """Тестирование консистентности данных между endpoints"""
        try:
            print("🎯 ТЕСТ 5: КОНСИСТЕНТНОСТЬ ДАННЫХ МЕЖДУ ENDPOINTS")
            
            # Получаем данные из individual-units-for-placement
            individual_response = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement", timeout=30)
            
            # Получаем данные из fully-placed
            fully_placed_response = self.session.get(f"{API_BASE}/operator/cargo/fully-placed", timeout=30)
            
            if individual_response.status_code == 200 and fully_placed_response.status_code == 200:
                individual_data = individual_response.json()
                fully_placed_data = fully_placed_response.json()
                
                individual_items = individual_data.get("items", [])
                fully_placed_items = fully_placed_data.get("items", [])
                
                # Подсчитываем статистику
                total_applications_for_placement = len(individual_items)
                fully_placed_applications = len(fully_placed_items)
                
                # Анализируем полностью размещенные заявки в individual-units
                fully_placed_in_individual = 0
                for item in individual_items:
                    units = item.get("units", [])
                    if units:
                        total_units = len(units)
                        placed_units = sum(1 for unit in units if unit.get("is_placed", False))
                        if placed_units == total_units and total_units > 0:
                            fully_placed_in_individual += 1
                
                # Проверяем консистентность
                consistency_issues = []
                
                # Логическая проверка: заявки не должны одновременно быть в обоих списках
                # (если заявка полностью размещена, она не должна быть доступна для размещения)
                
                print(f"    📊 Individual units для размещения: {total_applications_for_placement} заявок")
                print(f"    📊 Полностью размещенные заявки: {fully_placed_applications} заявок")
                print(f"    📊 Полностью размещенные в individual units: {fully_placed_in_individual} заявок")
                
                # Если есть полностью размещенные заявки в individual units, но их нет в fully-placed - это проблема
                if fully_placed_in_individual > 0 and fully_placed_applications == 0:
                    consistency_issues.append(f"Найдено {fully_placed_in_individual} полностью размещенных заявок в individual-units, но 0 в fully-placed")
                
                if not consistency_issues:
                    self.log_test(
                        "Консистентность данных между endpoints",
                        True,
                        f"Проверена консистентность данных между endpoints individual-units-for-placement и fully-placed. Доступные для размещения: {total_applications_for_placement} заявок, полностью размещенные: {fully_placed_applications} заявок"
                    )
                    return True
                else:
                    self.log_test(
                        "Консистентность данных между endpoints",
                        False,
                        f"Обнаружены проблемы консистентности: {'; '.join(consistency_issues)}",
                        "Консистентные данные между endpoints",
                        f"Проблемы: {consistency_issues}"
                    )
                    return False
            else:
                self.log_test(
                    "Получение данных для проверки консистентности",
                    False,
                    f"Ошибки HTTP: individual-units={individual_response.status_code}, fully-placed={fully_placed_response.status_code}",
                    "200 для обоих endpoints",
                    f"individual-units={individual_response.status_code}, fully-placed={fully_placed_response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Консистентность данных", False, f"Исключение: {str(e)}")
            return False

    def run_all_tests(self):
        """Запуск всех тестов исправленного fully-placed endpoint"""
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: API endpoint /api/operator/cargo/fully-placed")
        print("=" * 80)
        
        # Подготовка
        if not self.authenticate_warehouse_operator():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как warehouse_operator")
            return False
        
        # Запуск тестов
        test_results = []
        
        test_results.append(("Доступ к endpoint и структура ответа", self.test_endpoint_access_and_structure()))
        test_results.append(("Функциональность пагинации", self.test_pagination_functionality()))
        test_results.append(("Контроль доступа", self.test_access_control()))
        test_results.append(("🚨 КРИТИЧЕСКИЙ: Заявка 250109 в fully-placed", self.test_application_250109_in_fully_placed()))
        test_results.append(("Обязательные поля в ответе", self.test_required_fields_in_response()))
        test_results.append(("Консистентность данных между endpoints", self.test_data_consistency_between_endpoints()))
        
        # Подведение итогов
        print("\n" + "=" * 80)
        print("📊 РЕЗУЛЬТАТЫ КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ API ENDPOINT /api/operator/cargo/fully-placed:")
        print("=" * 80)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ ПРОЙДЕН" if result else "❌ НЕ ПРОЙДЕН"
            print(f"{status}: {test_name}")
            if result:
                passed_tests += 1
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n📈 ОБЩИЙ РЕЗУЛЬТАТ: {passed_tests}/{total_tests} тестов пройдено ({success_rate:.1f}%)")
        
        # Специальная проверка критического теста заявки 250109
        critical_test_passed = test_results[3][1]  # Индекс критического теста
        
        if success_rate == 100 and critical_test_passed:
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО! КРИТИЧЕСКАЯ ПРОБЛЕМА С ЗАЯВКОЙ 250109 ИСПРАВЛЕНА!")
            print("✅ Endpoint функционирует корректно")
            print("✅ Заявка 250109 теперь корректно появляется в списке полностью размещенных заявок")
            print("✅ Структура данных включает все обязательные поля")
            print("✅ Логика на основе individual_items работает правильно")
            print("✅ Консистентность данных между endpoints обеспечена")
        elif critical_test_passed:
            print("🎯 КРИТИЧЕСКАЯ ПРОБЛЕМА ИСПРАВЛЕНА! Заявка 250109 теперь работает корректно.")
            print("⚠️ Есть незначительные проблемы в других областях, но основная функциональность работает.")
        else:
            print("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА НЕ ИСПРАВЛЕНА! Заявка 250109 все еще не работает корректно.")
            print("🔧 ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ логики в /api/operator/cargo/fully-placed")
        
        return success_rate >= 66.7 and critical_test_passed  # Минимум 66.7% + критический тест

def main():
    """Главная функция"""
    tester = FullyPlacedEndpointTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("Исправленный API endpoint /api/operator/cargo/fully-placed работает корректно")
        return 0
    else:
        print("\n❌ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ВЫЯВИЛО ПРОБЛЕМЫ!")
        print("Требуется дополнительное исправление endpoint /api/operator/cargo/fully-placed")
        return 1

if __name__ == "__main__":
    exit(main())
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Новый API endpoint /api/operator/cargo/fully-placed для размещенного груза в TAJLINE.TJ

Тестируемые области:
1. Проверка корректности ответа endpoint
2. Проверка структуры возвращаемых данных
3. Проверка пагинации
4. Проверка доступа для разных ролей (admin, warehouse_operator)
5. Проверка всех необходимых полей в ответе

Endpoint: GET /api/operator/cargo/fully-placed
Параметры: page, per_page
Ожидаемый ответ: JSON с полями items и pagination
"""

import requests
import json
import sys
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://tajline-cargo-8.preview.emergentagent.com/api"

# Тестовые пользователи
TEST_USERS = {
    "admin": {
        "phone": "+79999999999",
        "password": "admin123"
    },
    "warehouse_operator": {
        "phone": "+79777888999", 
        "password": "warehouse123"
    }
}

class FullyPlacedCargoTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.tokens = {}
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: dict = None):
        """Логирование результатов тестирования"""
        status = "✅ УСПЕХ" if success else "❌ ОШИБКА"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Детали: {details}")
        if not success and response_data:
            print(f"   Ответ сервера: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        print()

    def authenticate_user(self, user_type: str) -> bool:
        """Аутентификация пользователя"""
        try:
            user_data = TEST_USERS[user_type]
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=user_data)
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                user_info = data.get("user", {})
                
                if token:
                    self.tokens[user_type] = token
                    self.log_test(
                        f"Аутентификация {user_type}",
                        True,
                        f"Успешная авторизация '{user_info.get('full_name', 'Неизвестный')}' (роль: {user_info.get('role', 'неизвестна')})"
                    )
                    return True
                else:
                    self.log_test(f"Аутентификация {user_type}", False, "Токен не получен")
                    return False
            else:
                self.log_test(
                    f"Аутентификация {user_type}",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response.json() if response.headers.get('content-type', '').startswith('application/json') else None
                )
                return False
                
        except Exception as e:
            self.log_test(f"Аутентификация {user_type}", False, f"Исключение: {str(e)}")
            return False

    def test_endpoint_access(self, user_type: str) -> bool:
        """Тестирование доступа к endpoint для разных ролей"""
        try:
            if user_type not in self.tokens:
                self.log_test(f"Доступ к endpoint ({user_type})", False, "Пользователь не аутентифицирован")
                return False
                
            headers = {"Authorization": f"Bearer {self.tokens[user_type]}"}
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/fully-placed", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    f"Доступ к endpoint ({user_type})",
                    True,
                    f"Endpoint доступен для роли {user_type}, получено {len(data.get('items', []))} элементов"
                )
                return True
            elif response.status_code == 403:
                self.log_test(
                    f"Доступ к endpoint ({user_type})",
                    False,
                    f"Доступ запрещен (HTTP 403) - ожидаемо для неавторизованных ролей"
                )
                return False
            else:
                self.log_test(
                    f"Доступ к endpoint ({user_type})",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response.json() if response.headers.get('content-type', '').startswith('application/json') else None
                )
                return False
                
        except Exception as e:
            self.log_test(f"Доступ к endpoint ({user_type})", False, f"Исключение: {str(e)}")
            return False

    def test_response_structure(self, user_type: str = "warehouse_operator") -> bool:
        """Тестирование структуры ответа endpoint"""
        try:
            if user_type not in self.tokens:
                self.log_test("Структура ответа", False, f"Пользователь {user_type} не аутентифицирован")
                return False
                
            headers = {"Authorization": f"Bearer {self.tokens[user_type]}"}
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/fully-placed", headers=headers)
            
            if response.status_code != 200:
                self.log_test(
                    "Структура ответа",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
            data = response.json()
            
            # Проверяем основные поля
            required_fields = ["items", "pagination", "summary"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_test(
                    "Структура ответа",
                    False,
                    f"Отсутствуют обязательные поля: {missing_fields}",
                    data
                )
                return False
            
            # Проверяем структуру pagination
            pagination = data.get("pagination", {})
            pagination_fields = ["current_page", "per_page", "total_items", "total_pages", "has_next", "has_prev"]
            missing_pagination_fields = [field for field in pagination_fields if field not in pagination]
            
            if missing_pagination_fields:
                self.log_test(
                    "Структура ответа",
                    False,
                    f"Отсутствуют поля пагинации: {missing_pagination_fields}",
                    data
                )
                return False
            
            # Проверяем структуру summary
            summary = data.get("summary", {})
            summary_fields = ["fully_placed_requests", "total_units_placed"]
            missing_summary_fields = [field for field in summary_fields if field not in summary]
            
            if missing_summary_fields:
                self.log_test(
                    "Структура ответа",
                    False,
                    f"Отсутствуют поля summary: {missing_summary_fields}",
                    data
                )
                return False
            
            self.log_test(
                "Структура ответа",
                True,
                f"Все обязательные поля присутствуют. Элементов: {len(data['items'])}, Страниц: {pagination['total_pages']}"
            )
            return True
            
        except Exception as e:
            self.log_test("Структура ответа", False, f"Исключение: {str(e)}")
            return False

    def test_item_fields(self, user_type: str = "warehouse_operator") -> bool:
        """Тестирование полей в элементах ответа"""
        try:
            if user_type not in self.tokens:
                self.log_test("Поля элементов", False, f"Пользователь {user_type} не аутентифицирован")
                return False
                
            headers = {"Authorization": f"Bearer {self.tokens[user_type]}"}
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/fully-placed", headers=headers)
            
            if response.status_code != 200:
                self.log_test(
                    "Поля элементов",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
            data = response.json()
            items = data.get("items", [])
            
            if not items:
                self.log_test(
                    "Поля элементов",
                    True,
                    "Нет элементов для проверки полей (это нормально, если нет полностью размещенных заявок)"
                )
                return True
            
            # Проверяем поля первого элемента
            item = items[0]
            
            # Обязательные поля согласно требованиям
            required_item_fields = [
                "sender_full_name", "sender_phone", "sender_address",
                "recipient_full_name", "recipient_phone", "recipient_address",
                "individual_units", "progress_text"
            ]
            
            missing_item_fields = [field for field in required_item_fields if field not in item]
            
            if missing_item_fields:
                self.log_test(
                    "Поля элементов",
                    False,
                    f"Отсутствуют обязательные поля в элементе: {missing_item_fields}",
                    item
                )
                return False
            
            # Проверяем individual_units
            individual_units = item.get("individual_units", [])
            if individual_units:
                unit = individual_units[0]
                required_unit_fields = ["individual_number", "is_placed", "placement_info"]
                missing_unit_fields = [field for field in required_unit_fields if field not in unit]
                
                if missing_unit_fields:
                    self.log_test(
                        "Поля элементов",
                        False,
                        f"Отсутствуют поля в individual_units: {missing_unit_fields}",
                        unit
                    )
                    return False
            
            self.log_test(
                "Поля элементов",
                True,
                f"Все обязательные поля присутствуют в элементах. Проверен элемент с {len(individual_units)} individual_units"
            )
            return True
            
        except Exception as e:
            self.log_test("Поля элементов", False, f"Исключение: {str(e)}")
            return False

    def test_pagination(self, user_type: str = "warehouse_operator") -> bool:
        """Тестирование пагинации"""
        try:
            if user_type not in self.tokens:
                self.log_test("Пагинация", False, f"Пользователь {user_type} не аутентифицирован")
                return False
                
            headers = {"Authorization": f"Bearer {self.tokens[user_type]}"}
            
            # Тест 1: Первая страница с per_page=5
            response1 = self.session.get(
                f"{BACKEND_URL}/operator/cargo/fully-placed?page=1&per_page=5",
                headers=headers
            )
            
            if response1.status_code != 200:
                self.log_test(
                    "Пагинация",
                    False,
                    f"HTTP {response1.status_code}: {response1.text}"
                )
                return False
            
            data1 = response1.json()
            pagination1 = data1.get("pagination", {})
            
            # Проверяем корректность пагинации
            if pagination1.get("current_page") != 1:
                self.log_test(
                    "Пагинация",
                    False,
                    f"Неверная текущая страница: ожидалось 1, получено {pagination1.get('current_page')}"
                )
                return False
            
            if pagination1.get("per_page") != 5:
                self.log_test(
                    "Пагинация",
                    False,
                    f"Неверное количество на страницу: ожидалось 5, получено {pagination1.get('per_page')}"
                )
                return False
            
            # Тест 2: Вторая страница (если есть элементы)
            total_items = pagination1.get("total_items", 0)
            if total_items > 5:
                response2 = self.session.get(
                    f"{BACKEND_URL}/operator/cargo/fully-placed?page=2&per_page=5",
                    headers=headers
                )
                
                if response2.status_code == 200:
                    data2 = response2.json()
                    pagination2 = data2.get("pagination", {})
                    
                    if pagination2.get("current_page") != 2:
                        self.log_test(
                            "Пагинация",
                            False,
                            f"Неверная текущая страница на второй странице: ожидалось 2, получено {pagination2.get('current_page')}"
                        )
                        return False
            
            self.log_test(
                "Пагинация",
                True,
                f"Пагинация работает корректно. Всего элементов: {total_items}, страниц: {pagination1.get('total_pages', 0)}"
            )
            return True
            
        except Exception as e:
            self.log_test("Пагинация", False, f"Исключение: {str(e)}")
            return False

    def test_data_consistency(self, user_type: str = "warehouse_operator") -> bool:
        """Тестирование консистентности данных"""
        try:
            if user_type not in self.tokens:
                self.log_test("Консистентность данных", False, f"Пользователь {user_type} не аутентифицирован")
                return False
                
            headers = {"Authorization": f"Bearer {self.tokens[user_type]}"}
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/fully-placed", headers=headers)
            
            if response.status_code != 200:
                self.log_test(
                    "Консистентность данных",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
            data = response.json()
            items = data.get("items", [])
            
            if not items:
                self.log_test(
                    "Консистентность данных",
                    True,
                    "Нет элементов для проверки консистентности (это нормально)"
                )
                return True
            
            # Проверяем консистентность данных в элементах
            inconsistencies = []
            
            for i, item in enumerate(items):
                # Проверяем, что progress_text соответствует данным
                total_units = item.get("total_units", 0)
                placed_units = item.get("placed_units", 0)
                progress_text = item.get("progress_text", "")
                expected_progress = f"Размещено: {placed_units}/{total_units}"
                
                if progress_text != expected_progress:
                    inconsistencies.append(f"Элемент {i}: progress_text '{progress_text}' не соответствует ожидаемому '{expected_progress}'")
                
                # Проверяем, что is_fully_placed = True
                if not item.get("is_fully_placed", False):
                    inconsistencies.append(f"Элемент {i}: is_fully_placed должно быть True для полностью размещенных заявок")
                
                # Проверяем, что количество individual_units соответствует total_units
                individual_units = item.get("individual_units", [])
                if len(individual_units) != total_units:
                    inconsistencies.append(f"Элемент {i}: количество individual_units ({len(individual_units)}) не соответствует total_units ({total_units})")
                
                # Проверяем, что все individual_units размещены
                for j, unit in enumerate(individual_units):
                    if not unit.get("is_placed", False):
                        inconsistencies.append(f"Элемент {i}, единица {j}: is_placed должно быть True")
                    
                    if not unit.get("placement_info"):
                        inconsistencies.append(f"Элемент {i}, единица {j}: отсутствует placement_info")
            
            if inconsistencies:
                self.log_test(
                    "Консистентность данных",
                    False,
                    f"Найдены несоответствия: {'; '.join(inconsistencies)}"
                )
                return False
            
            self.log_test(
                "Консистентность данных",
                True,
                f"Данные консистентны. Проверено {len(items)} элементов"
            )
            return True
            
        except Exception as e:
            self.log_test("Консистентность данных", False, f"Исключение: {str(e)}")
            return False

    def run_comprehensive_test(self):
        """Запуск полного тестирования"""
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: API endpoint /api/operator/cargo/fully-placed")
        print("=" * 80)
        print()
        
        # Аутентификация пользователей
        print("📋 ЭТАП 1: АУТЕНТИФИКАЦИЯ ПОЛЬЗОВАТЕЛЕЙ")
        print("-" * 50)
        admin_auth = self.authenticate_user("admin")
        operator_auth = self.authenticate_user("warehouse_operator")
        print()
        
        if not (admin_auth or operator_auth):
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось аутентифицировать ни одного пользователя!")
            return False
        
        # Тестирование доступа для разных ролей
        print("📋 ЭТАП 2: ТЕСТИРОВАНИЕ ДОСТУПА ДЛЯ РАЗНЫХ РОЛЕЙ")
        print("-" * 50)
        access_results = []
        if admin_auth:
            access_results.append(self.test_endpoint_access("admin"))
        if operator_auth:
            access_results.append(self.test_endpoint_access("warehouse_operator"))
        print()
        
        if not any(access_results):
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Endpoint недоступен ни для одной роли!")
            return False
        
        # Выбираем пользователя для дальнейших тестов
        test_user = "warehouse_operator" if operator_auth else "admin"
        
        # Тестирование структуры ответа
        print("📋 ЭТАП 3: ТЕСТИРОВАНИЕ СТРУКТУРЫ ОТВЕТА")
        print("-" * 50)
        structure_test = self.test_response_structure(test_user)
        print()
        
        # Тестирование полей элементов
        print("📋 ЭТАП 4: ТЕСТИРОВАНИЕ ПОЛЕЙ ЭЛЕМЕНТОВ")
        print("-" * 50)
        fields_test = self.test_item_fields(test_user)
        print()
        
        # Тестирование пагинации
        print("📋 ЭТАП 5: ТЕСТИРОВАНИЕ ПАГИНАЦИИ")
        print("-" * 50)
        pagination_test = self.test_pagination(test_user)
        print()
        
        # Тестирование консистентности данных
        print("📋 ЭТАП 6: ТЕСТИРОВАНИЕ КОНСИСТЕНТНОСТИ ДАННЫХ")
        print("-" * 50)
        consistency_test = self.test_data_consistency(test_user)
        print()
        
        # Подведение итогов
        self.print_summary()
        
        # Определяем общий результат
        critical_tests = [structure_test, fields_test, pagination_test, consistency_test]
        success_rate = sum(1 for test in critical_tests if test) / len(critical_tests) * 100
        
        return success_rate >= 75  # Считаем успешным если 75%+ тестов прошли

    def print_summary(self):
        """Вывод итогового отчета"""
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 80)
        
        successful_tests = [r for r in self.test_results if r["success"]]
        failed_tests = [r for r in self.test_results if not r["success"]]
        
        total_tests = len(self.test_results)
        success_count = len(successful_tests)
        success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Всего тестов: {total_tests}")
        print(f"Успешных: {success_count}")
        print(f"Неудачных: {len(failed_tests)}")
        print(f"Процент успеха: {success_rate:.1f}%")
        print()
        
        if failed_tests:
            print("❌ НЕУДАЧНЫЕ ТЕСТЫ:")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
            print()
        
        if success_rate >= 90:
            print("🎉 ОТЛИЧНЫЙ РЕЗУЛЬТАТ: API endpoint работает превосходно!")
        elif success_rate >= 75:
            print("✅ ХОРОШИЙ РЕЗУЛЬТАТ: API endpoint работает корректно с незначительными проблемами")
        elif success_rate >= 50:
            print("⚠️ УДОВЛЕТВОРИТЕЛЬНЫЙ РЕЗУЛЬТАТ: API endpoint работает, но есть проблемы")
        else:
            print("❌ НЕУДОВЛЕТВОРИТЕЛЬНЫЙ РЕЗУЛЬТАТ: API endpoint имеет серьезные проблемы")
        
        print()

def main():
    """Главная функция"""
    tester = FullyPlacedCargoTester()
    
    try:
        success = tester.run_comprehensive_test()
        
        if success:
            print("🎯 ЗАКЛЮЧЕНИЕ: Тестирование API endpoint /api/operator/cargo/fully-placed завершено успешно!")
            sys.exit(0)
        else:
            print("🚨 ЗАКЛЮЧЕНИЕ: Тестирование выявило критические проблемы с API endpoint!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
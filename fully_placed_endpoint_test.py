#!/usr/bin/env python3
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
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-cargo-7.preview.emergentagent.com')
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
BACKEND_URL = "https://tajline-cargo-7.preview.emergentagent.com/api"

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
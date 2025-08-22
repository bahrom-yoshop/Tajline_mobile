#!/usr/bin/env python3
"""
🎯 ПОВТОРНОЕ ТЕСТИРОВАНИЕ: Исправленный Individual Units API в TAJLINE.TJ

КОНТЕКСТ: Исправлена логика backend API endpoint GET /api/operator/cargo/individual-units-for-placement 
для поддержки динамического создания individual units из cargo_items с quantity > 0.

ИСПРАВЛЕНИЯ В КОДЕ:
1. Убрана жесткая фильтрация заявок без individual_items
2. Добавлена логика динамического создания individual units из quantity
3. Поддержка как готовых individual_items, так и создание на лету

ЦЕЛЬ ТЕСТИРОВАНИЯ:
1. Проверить что API теперь возвращает данные для заявок с cargo_items
2. Убедиться в корректности динамического создания individual units
3. Протестировать структуру возвращаемых данных
4. Проверить фильтрацию и пагинацию с реальными данными
5. Убедиться в правильности individual_number формата (250101/01/01)
"""

import requests
import json
import os
from datetime import datetime

# Конфигурация
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://placement-view.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class IndividualUnitsAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_user = None
        self.test_results = []
        self.test_cargo_id = None
        
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
            
            # Данные для авторизации оператора склада
            login_data = {
                "phone": "+79777888999",
                "password": "warehouse123"
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
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
                self.log_test("Авторизация оператора склада", False, f"Ошибка авторизации: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Авторизация оператора склада", False, f"Исключение: {str(e)}")
            return False

    def create_test_cargo_with_multiple_items(self):
        """Создание тестовой заявки с множественными cargo_items для тестирования individual units"""
        try:
            print("🎯 СОЗДАНИЕ ТЕСТОВОЙ ЗАЯВКИ С МНОЖЕСТВЕННЫМИ CARGO_ITEMS")
            
            # Создаем заявку с 2 типами груза: 2 + 3 = 5 единиц общим итогом
            cargo_data = {
                "sender_full_name": "Тестовый Отправитель Individual Units",
                "sender_phone": "+79999111222",
                "recipient_full_name": "Тестовый Получатель Individual Units",
                "recipient_phone": "+79999333444",
                "recipient_address": "г. Душанбе, ул. Тестовая, дом 123",
                "description": "Тестовая заявка для проверки individual units API",
                "route": "moscow_to_tajikistan",
                "payment_method": "cash_on_delivery",
                "delivery_method": "pickup",
                "cargo_items": [
                    {
                        "cargo_name": "Электроника Samsung",
                        "quantity": 2,  # 2 единицы
                        "weight": 5.0,
                        "price_per_kg": 100.0,
                        "total_amount": 500.0
                    },
                    {
                        "cargo_name": "Бытовая техника LG", 
                        "quantity": 3,  # 3 единицы
                        "weight": 8.0,
                        "price_per_kg": 80.0,
                        "total_amount": 640.0
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/operator/cargo/accept", json=cargo_data)
            
            if response.status_code == 200:
                data = response.json()
                self.test_cargo_id = data.get("cargo_id")
                cargo_number = data.get("cargo_number")
                
                self.log_test(
                    "Создание тестовой заявки с множественными cargo_items",
                    True,
                    f"Заявка создана: {cargo_number} (ID: {self.test_cargo_id}). Грузы: Электроника Samsung (2 шт) + Бытовая техника LG (3 шт) = 5 единиц общим итогом"
                )
                return cargo_number
            else:
                error_text = response.text
                self.log_test(
                    "Создание тестовой заявки",
                    False,
                    f"Ошибка создания заявки: {response.status_code} - {error_text}"
                )
                return None
                
        except Exception as e:
            self.log_test("Создание тестовой заявки", False, f"Исключение: {str(e)}")
            return None

    def test_individual_units_api_basic(self):
        """Тест базовой функциональности individual-units-for-placement API"""
        try:
            print("🎯 ТЕСТ 1: БАЗОВАЯ ФУНКЦИОНАЛЬНОСТЬ individual-units-for-placement API")
            
            response = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement")
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем структуру ответа
                required_fields = ["individual_units", "total", "page", "per_page"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    total_units = data.get("total", 0)
                    individual_units = data.get("individual_units", [])
                    
                    self.log_test(
                        "GET /api/operator/cargo/individual-units-for-placement",
                        True,
                        f"Endpoint работает корректно! Получено {len(individual_units)} individual units, всего: {total_units}"
                    )
                    return data
                else:
                    self.log_test(
                        "Структура ответа individual-units-for-placement",
                        False,
                        f"Отсутствуют обязательные поля: {missing_fields}",
                        str(required_fields),
                        str(list(data.keys()))
                    )
                    return None
            else:
                self.log_test(
                    "GET /api/operator/cargo/individual-units-for-placement",
                    False,
                    f"HTTP ошибка: {response.status_code} - {response.text}"
                )
                return None
                
        except Exception as e:
            self.log_test("Базовая функциональность individual-units-for-placement", False, f"Исключение: {str(e)}")
            return None

    def test_individual_units_structure(self, api_data, test_cargo_number):
        """Тест структуры individual units и поиск тестовой заявки"""
        try:
            print("🎯 ТЕСТ 2: СТРУКТУРА INDIVIDUAL UNITS И ПОИСК ТЕСТОВОЙ ЗАЯВКИ")
            
            if not api_data or not api_data.get("individual_units"):
                self.log_test("Структура individual units", False, "Нет данных individual_units в ответе API")
                return False
            
            individual_units = api_data.get("individual_units", [])
            
            # Ищем нашу тестовую заявку среди individual units
            test_units = []
            for unit in individual_units:
                if unit.get("cargo_request_number") == test_cargo_number:
                    test_units.append(unit)
            
            if not test_units:
                self.log_test(
                    "Поиск тестовой заявки в individual units",
                    False,
                    f"Тестовая заявка {test_cargo_number} не найдена среди {len(individual_units)} individual units"
                )
                return False
            
            # Проверяем количество individual units для нашей заявки
            expected_count = 5  # 2 + 3 = 5 единиц
            actual_count = len(test_units)
            
            if actual_count == expected_count:
                self.log_test(
                    "Количество individual units",
                    True,
                    f"Корректное количество individual units: {actual_count} (соответствует сумме quantity cargo_items: 2+3=5)"
                )
            else:
                self.log_test(
                    "Количество individual units",
                    False,
                    f"Неверное количество individual units",
                    str(expected_count),
                    str(actual_count)
                )
                return False
            
            # Проверяем структуру каждого individual unit
            required_unit_fields = ["individual_number", "cargo_request_number", "type_number", "unit_index", "placement_status", "is_placed"]
            
            structure_valid = True
            individual_numbers = []
            
            for i, unit in enumerate(test_units):
                missing_fields = [field for field in required_unit_fields if field not in unit]
                if missing_fields:
                    self.log_test(
                        f"Структура individual unit #{i+1}",
                        False,
                        f"Отсутствуют поля: {missing_fields}"
                    )
                    structure_valid = False
                else:
                    individual_number = unit.get("individual_number")
                    individual_numbers.append(individual_number)
                    
                    # Проверяем формат individual_number (должен быть CARGO_NUMBER/TYPE/UNIT)
                    if "/" in individual_number and len(individual_number.split("/")) == 3:
                        self.log_test(
                            f"Формат individual_number #{i+1}",
                            True,
                            f"Корректный формат: {individual_number}"
                        )
                    else:
                        self.log_test(
                            f"Формат individual_number #{i+1}",
                            False,
                            f"Неверный формат individual_number: {individual_number}",
                            "CARGO_NUMBER/TYPE/UNIT",
                            individual_number
                        )
                        structure_valid = False
            
            if structure_valid:
                self.log_test(
                    "Структура всех individual units",
                    True,
                    f"Все {len(test_units)} individual units имеют корректную структуру. Individual numbers: {individual_numbers}"
                )
            
            return structure_valid
            
        except Exception as e:
            self.log_test("Структура individual units", False, f"Исключение: {str(e)}")
            return False

    def test_individual_number_format(self, api_data, test_cargo_number):
        """Тест формата individual_number (CARGO_NUMBER/TYPE/UNIT)"""
        try:
            print("🎯 ТЕСТ 3: ФОРМАТ INDIVIDUAL_NUMBER")
            
            individual_units = api_data.get("individual_units", [])
            test_units = [unit for unit in individual_units if unit.get("cargo_request_number") == test_cargo_number]
            
            if not test_units:
                self.log_test("Формат individual_number", False, "Нет тестовых units для проверки формата")
                return False
            
            format_valid = True
            expected_patterns = [
                f"{test_cargo_number}/01/01",  # Электроника Samsung, единица 1
                f"{test_cargo_number}/01/02",  # Электроника Samsung, единица 2
                f"{test_cargo_number}/02/01",  # Бытовая техника LG, единица 1
                f"{test_cargo_number}/02/02",  # Бытовая техника LG, единица 2
                f"{test_cargo_number}/02/03",  # Бытовая техника LG, единица 3
            ]
            
            actual_numbers = [unit.get("individual_number") for unit in test_units]
            actual_numbers.sort()
            expected_patterns.sort()
            
            # Проверяем соответствие ожидаемым паттернам
            if set(actual_numbers) == set(expected_patterns):
                self.log_test(
                    "Формат individual_number",
                    True,
                    f"Все individual_number имеют правильный формат (CARGO_NUMBER/TYPE/UNIT): {actual_numbers}"
                )
            else:
                self.log_test(
                    "Формат individual_number",
                    False,
                    f"Неверные individual_number",
                    str(expected_patterns),
                    str(actual_numbers)
                )
                format_valid = False
            
            # Проверяем type_number и unit_index отдельно
            type_numbers = {}
            for unit in test_units:
                type_num = unit.get("type_number")
                unit_idx = unit.get("unit_index")
                
                if type_num not in type_numbers:
                    type_numbers[type_num] = []
                type_numbers[type_num].append(unit_idx)
            
            # Должно быть 2 типа: 01 (2 единицы) и 02 (3 единицы)
            if len(type_numbers) == 2 and "01" in type_numbers and "02" in type_numbers:
                if len(type_numbers["01"]) == 2 and len(type_numbers["02"]) == 3:
                    self.log_test(
                        "Группировка по type_number",
                        True,
                        f"Корректная группировка: тип 01 ({len(type_numbers['01'])} единиц), тип 02 ({len(type_numbers['02'])} единиц)"
                    )
                else:
                    self.log_test(
                        "Группировка по type_number",
                        False,
                        f"Неверное количество единиц в типах: тип 01 ({len(type_numbers.get('01', []))} единиц), тип 02 ({len(type_numbers.get('02', []))} единиц)"
                    )
                    format_valid = False
            else:
                self.log_test(
                    "Группировка по type_number",
                    False,
                    f"Неверные type_number: {list(type_numbers.keys())}"
                )
                format_valid = False
            
            return format_valid
            
        except Exception as e:
            self.log_test("Формат individual_number", False, f"Исключение: {str(e)}")
            return False

    def test_placement_status_defaults(self, api_data, test_cargo_number):
        """Тест значений по умолчанию для placement_status и is_placed"""
        try:
            print("🎯 ТЕСТ 4: ЗНАЧЕНИЯ ПО УМОЛЧАНИЮ (placement_status, is_placed)")
            
            individual_units = api_data.get("individual_units", [])
            test_units = [unit for unit in individual_units if unit.get("cargo_request_number") == test_cargo_number]
            
            if not test_units:
                self.log_test("Значения по умолчанию", False, "Нет тестовых units для проверки")
                return False
            
            defaults_valid = True
            
            for i, unit in enumerate(test_units):
                placement_status = unit.get("placement_status")
                is_placed = unit.get("is_placed")
                
                # Проверяем placement_status = "awaiting_placement"
                if placement_status == "awaiting_placement":
                    self.log_test(
                        f"placement_status unit #{i+1}",
                        True,
                        f"Корректное значение по умолчанию: {placement_status}"
                    )
                else:
                    self.log_test(
                        f"placement_status unit #{i+1}",
                        False,
                        f"Неверное значение placement_status",
                        "awaiting_placement",
                        str(placement_status)
                    )
                    defaults_valid = False
                
                # Проверяем is_placed = false
                if is_placed == False:
                    self.log_test(
                        f"is_placed unit #{i+1}",
                        True,
                        f"Корректное значение по умолчанию: {is_placed}"
                    )
                else:
                    self.log_test(
                        f"is_placed unit #{i+1}",
                        False,
                        f"Неверное значение is_placed",
                        "false",
                        str(is_placed)
                    )
                    defaults_valid = False
            
            return defaults_valid
            
        except Exception as e:
            self.log_test("Значения по умолчанию", False, f"Исключение: {str(e)}")
            return False

    def test_filtering_by_cargo_type(self, test_cargo_number):
        """Тест фильтрации по cargo_type_filter"""
        try:
            print("🎯 ТЕСТ 5: ФИЛЬТРАЦИЯ ПО CARGO_TYPE_FILTER")
            
            # Тестируем фильтрацию по типу груза "01"
            response = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement?cargo_type_filter=01")
            
            if response.status_code == 200:
                data = response.json()
                individual_units = data.get("individual_units", [])
                
                # Ищем наши тестовые единицы типа "01"
                test_type_01_units = [
                    unit for unit in individual_units 
                    if unit.get("cargo_request_number") == test_cargo_number and unit.get("type_number") == "01"
                ]
                
                if len(test_type_01_units) == 2:  # Должно быть 2 единицы типа "01"
                    self.log_test(
                        "Фильтрация по cargo_type_filter=01",
                        True,
                        f"Корректная фильтрация: найдено {len(test_type_01_units)} единиц типа '01'"
                    )
                else:
                    self.log_test(
                        "Фильтрация по cargo_type_filter=01",
                        False,
                        f"Неверная фильтрация по типу '01'",
                        "2 единицы",
                        f"{len(test_type_01_units)} единиц"
                    )
                    return False
            else:
                self.log_test(
                    "Фильтрация по cargo_type_filter=01",
                    False,
                    f"Ошибка запроса с фильтром: {response.status_code}"
                )
                return False
            
            # Тестируем фильтрацию по типу груза "02"
            response = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement?cargo_type_filter=02")
            
            if response.status_code == 200:
                data = response.json()
                individual_units = data.get("individual_units", [])
                
                # Ищем наши тестовые единицы типа "02"
                test_type_02_units = [
                    unit for unit in individual_units 
                    if unit.get("cargo_request_number") == test_cargo_number and unit.get("type_number") == "02"
                ]
                
                if len(test_type_02_units) == 3:  # Должно быть 3 единицы типа "02"
                    self.log_test(
                        "Фильтрация по cargo_type_filter=02",
                        True,
                        f"Корректная фильтрация: найдено {len(test_type_02_units)} единиц типа '02'"
                    )
                    return True
                else:
                    self.log_test(
                        "Фильтрация по cargo_type_filter=02",
                        False,
                        f"Неверная фильтрация по типу '02'",
                        "3 единицы",
                        f"{len(test_type_02_units)} единиц"
                    )
                    return False
            else:
                self.log_test(
                    "Фильтрация по cargo_type_filter=02",
                    False,
                    f"Ошибка запроса с фильтром: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Фильтрация по cargo_type_filter", False, f"Исключение: {str(e)}")
            return False

    def test_filtering_by_status(self, test_cargo_number):
        """Тест фильтрации по status_filter"""
        try:
            print("🎯 ТЕСТ 6: ФИЛЬТРАЦИЯ ПО STATUS_FILTER")
            
            # Тестируем фильтрацию по статусу "awaiting_placement"
            response = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement?status_filter=awaiting_placement")
            
            if response.status_code == 200:
                data = response.json()
                individual_units = data.get("individual_units", [])
                
                # Ищем наши тестовые единицы со статусом "awaiting_placement"
                test_awaiting_units = [
                    unit for unit in individual_units 
                    if unit.get("cargo_request_number") == test_cargo_number and unit.get("placement_status") == "awaiting_placement"
                ]
                
                if len(test_awaiting_units) == 5:  # Все 5 единиц должны иметь статус "awaiting_placement"
                    self.log_test(
                        "Фильтрация по status_filter=awaiting_placement",
                        True,
                        f"Корректная фильтрация: найдено {len(test_awaiting_units)} единиц со статусом 'awaiting_placement'"
                    )
                    return True
                else:
                    self.log_test(
                        "Фильтрация по status_filter=awaiting_placement",
                        False,
                        f"Неверная фильтрация по статусу 'awaiting_placement'",
                        "5 единиц",
                        f"{len(test_awaiting_units)} единиц"
                    )
                    return False
            else:
                self.log_test(
                    "Фильтрация по status_filter=awaiting_placement",
                    False,
                    f"Ошибка запроса с фильтром: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Фильтрация по status_filter", False, f"Исключение: {str(e)}")
            return False

    def test_pagination(self):
        """Тест пагинации"""
        try:
            print("🎯 ТЕСТ 7: ПАГИНАЦИЯ")
            
            # Тестируем пагинацию с per_page=2
            response = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement?page=1&per_page=2")
            
            if response.status_code == 200:
                data = response.json()
                
                page = data.get("page")
                per_page = data.get("per_page")
                total_count = data.get("total")
                individual_units = data.get("individual_units", [])
                
                # Проверяем параметры пагинации
                if page == 1 and per_page == 2 and len(individual_units) <= 2:
                    self.log_test(
                        "Пагинация (page=1, per_page=2)",
                        True,
                        f"Корректная пагинация: страница {page}, элементов на странице {per_page}, получено {len(individual_units)} элементов, всего {total_count}"
                    )
                    return True
                else:
                    self.log_test(
                        "Пагинация (page=1, per_page=2)",
                        False,
                        f"Неверная пагинация: page={page}, per_page={per_page}, получено {len(individual_units)} элементов"
                    )
                    return False
            else:
                self.log_test(
                    "Пагинация",
                    False,
                    f"Ошибка запроса с пагинацией: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Пагинация", False, f"Исключение: {str(e)}")
            return False

    def run_comprehensive_test(self):
        """Запуск полного комплексного тестирования"""
        print("=" * 80)
        print("🎯 ПОВТОРНОЕ ТЕСТИРОВАНИЕ: Исправленный Individual Units API в TAJLINE.TJ")
        print("=" * 80)
        print()
        
        # Шаг 1: Авторизация
        if not self.authenticate_warehouse_operator():
            print("❌ Не удалось авторизоваться. Тестирование прервано.")
            return False
        
        # Шаг 2: Создание тестовой заявки
        test_cargo_number = self.create_test_cargo_with_multiple_items()
        if not test_cargo_number:
            print("❌ Не удалось создать тестовую заявку. Тестирование прервано.")
            return False
        
        # Шаг 3: Тестирование API
        api_data = self.test_individual_units_api_basic()
        if not api_data:
            print("❌ Базовая функциональность API не работает. Тестирование прервано.")
            return False
        
        # Шаг 4: Тестирование структуры данных
        if not self.test_individual_units_structure(api_data, test_cargo_number):
            print("❌ Структура individual units некорректна.")
            return False
        
        # Шаг 5: Тестирование формата individual_number
        if not self.test_individual_number_format(api_data, test_cargo_number):
            print("❌ Формат individual_number некорректен.")
            return False
        
        # Шаг 6: Тестирование значений по умолчанию
        if not self.test_placement_status_defaults(api_data, test_cargo_number):
            print("❌ Значения по умолчанию некорректны.")
            return False
        
        # Шаг 7: Тестирование фильтрации по типу груза
        if not self.test_filtering_by_cargo_type(test_cargo_number):
            print("❌ Фильтрация по cargo_type_filter не работает.")
            return False
        
        # Шаг 8: Тестирование фильтрации по статусу
        if not self.test_filtering_by_status(test_cargo_number):
            print("❌ Фильтрация по status_filter не работает.")
            return False
        
        # Шаг 9: Тестирование пагинации
        if not self.test_pagination():
            print("❌ Пагинация не работает.")
            return False
        
        return True

    def print_summary(self):
        """Вывод итогового отчета"""
        print("\n" + "=" * 80)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 Общая статистика:")
        print(f"   • Всего тестов: {total_tests}")
        print(f"   • Успешных: {passed_tests}")
        print(f"   • Неудачных: {failed_tests}")
        print(f"   • Процент успеха: {success_rate:.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ Неудачные тесты:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
            print()
        
        print("✅ Успешные тесты:")
        for result in self.test_results:
            if result["success"]:
                print(f"   • {result['test']}")
        
        print("\n" + "=" * 80)
        
        if success_rate >= 90:
            print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ Individual Units API работает корректно согласно требованиям.")
        elif success_rate >= 70:
            print("⚠️ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ПРЕДУПРЕЖДЕНИЯМИ")
            print("🔧 Требуются незначительные исправления.")
        else:
            print("❌ ТЕСТИРОВАНИЕ ВЫЯВИЛО КРИТИЧЕСКИЕ ПРОБЛЕМЫ")
            print("🚨 Требуются серьезные исправления перед продакшеном.")
        
        print("=" * 80)

def main():
    """Главная функция"""
    tester = IndividualUnitsAPITester()
    
    try:
        success = tester.run_comprehensive_test()
        tester.print_summary()
        
        return success
        
    except KeyboardInterrupt:
        print("\n⚠️ Тестирование прервано пользователем")
        return False
    except Exception as e:
        print(f"\n❌ Критическая ошибка тестирования: {str(e)}")
        return False

if __name__ == "__main__":
    main()
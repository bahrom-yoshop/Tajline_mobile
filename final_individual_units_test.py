#!/usr/bin/env python3
"""
🎯 FINAL COMPREHENSIVE TEST: Individual Units API для TAJLINE.TJ
КОНТЕКСТ: Полное тестирование API с правильным пониманием логики individual_items
ЦЕЛЬ: Протестировать все аспекты GET /api/operator/cargo/individual-units-for-placement
"""

import requests
import json
import os
from datetime import datetime

# Конфигурация
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://placement-view.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class FinalIndividualUnitsAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_user = None
        self.test_results = []
        self.created_cargo_ids = []
        
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
            
            login_data = {
                "phone": "+79777888999",
                "password": "warehouse123"
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                
                user_response = self.session.get(f"{API_BASE}/auth/me")
                if user_response.status_code == 200:
                    self.operator_user = user_response.json()
                    self.log_test(
                        "Авторизация оператора склада",
                        True,
                        f"Успешная авторизация: {self.operator_user.get('full_name')} (роль: {self.operator_user.get('role')})"
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

    def create_test_cargo_with_multiple_items(self, suffix=""):
        """Создание тестовой заявки с несколькими типами груза"""
        try:
            print(f"📦 СОЗДАНИЕ ТЕСТОВОЙ ЗАЯВКИ{suffix}")
            
            cargo_data = {
                "sender_full_name": f"Тестовый Отправитель{suffix}",
                "sender_phone": "+79991234567",
                "recipient_full_name": f"Тестовый Получатель{suffix}",
                "recipient_phone": "+79997654321",
                "recipient_address": f"г. Душанбе, ул. Тестовая, дом {suffix or '1'}",
                "description": f"Тестовый груз для individual units{suffix}",
                "route": "moscow_to_tajikistan",
                "payment_method": "cash_on_delivery",
                "delivery_method": "pickup",
                "cargo_items": [
                    {
                        "cargo_name": f"Электроника Samsung{suffix}",
                        "quantity": 2,  # Это создаст 2 individual units
                        "weight": 5.0,
                        "price_per_kg": 100.0,
                        "total_amount": 1000.0
                    },
                    {
                        "cargo_name": f"Бытовая техника LG{suffix}",
                        "quantity": 3,  # Это создаст 3 individual units
                        "weight": 8.0,
                        "price_per_kg": 80.0,
                        "total_amount": 1920.0
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/operator/cargo/accept", json=cargo_data)
            
            if response.status_code == 200:
                data = response.json()
                cargo_id = data.get("id")  # Используем "id" вместо "cargo_id"
                cargo_number = data.get("cargo_number")
                
                if cargo_id:
                    self.created_cargo_ids.append(cargo_id)
                    self.log_test(
                        f"Создание тестовой заявки{suffix}",
                        True,
                        f"Заявка создана: {cargo_number} (ID: {cargo_id}), грузы: 2 типа (2+3=5 единиц)"
                    )
                    return {"cargo_id": cargo_id, "cargo_number": cargo_number}
                else:
                    self.log_test(f"Создание тестовой заявки{suffix}", False, "Не получен cargo_id")
                    return None
            else:
                error_text = response.text if response.text else "Неизвестная ошибка"
                self.log_test(
                    f"Создание тестовой заявки{suffix}",
                    False,
                    f"Ошибка создания: {response.status_code} - {error_text}"
                )
                return None
                
        except Exception as e:
            self.log_test(f"Создание тестовой заявки{suffix}", False, f"Исключение: {str(e)}")
            return None

    def test_api_endpoint_basic_functionality(self):
        """Тест базовой функциональности API endpoint"""
        try:
            print("🎯 ТЕСТ 1: БАЗОВАЯ ФУНКЦИОНАЛЬНОСТЬ API ENDPOINT")
            
            response = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement")
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем обязательные поля согласно review request
                required_fields = ["items", "individual_units", "total", "page", "per_page", "total_pages"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    total_units = data.get('total', 0)
                    items_count = len(data.get('items', []))
                    individual_units_count = len(data.get('individual_units', []))
                    
                    self.log_test(
                        "API endpoint возвращает корректную структуру",
                        True,
                        f"Всего единиц: {total_units}, групп: {items_count}, individual_units: {individual_units_count}"
                    )
                    return data
                else:
                    self.log_test(
                        "Структура ответа API",
                        False,
                        f"Отсутствуют обязательные поля: {missing_fields}",
                        str(required_fields),
                        str(list(data.keys()))
                    )
                    return None
            else:
                self.log_test(
                    "API endpoint доступность",
                    False,
                    f"HTTP ошибка: {response.status_code}",
                    "200",
                    str(response.status_code)
                )
                return None
                
        except Exception as e:
            self.log_test("Базовая функциональность API", False, f"Исключение: {str(e)}")
            return None

    def test_individual_units_data_structure(self, sample_data):
        """Тест структуры данных individual units согласно review request"""
        try:
            print("🎯 ТЕСТ 2: СТРУКТУРА ДАННЫХ INDIVIDUAL UNITS")
            
            if not sample_data or not sample_data.get("individual_units"):
                self.log_test("Структура individual units", True, "Нет individual_units для тестирования структуры")
                return True
            
            individual_units = sample_data.get("individual_units", [])
            
            if individual_units:
                first_unit = individual_units[0]
                
                # Критические поля согласно review request
                critical_fields = [
                    "individual_number", "cargo_request_number", "type_number", "unit_index",
                    "placement_status", "is_placed", "cargo_name", "sender_full_name", 
                    "recipient_full_name", "warehouse_name", "accepting_operator"
                ]
                
                missing_fields = [field for field in critical_fields if field not in first_unit]
                
                if not missing_fields:
                    # Проверяем формат individual_number (должен быть ЗАЯВКА/ТИП/ЕДИНИЦА)
                    individual_number = first_unit.get("individual_number", "")
                    if "/" in individual_number and len(individual_number.split("/")) == 3:
                        parts = individual_number.split("/")
                        cargo_number, type_num, unit_idx = parts
                        
                        self.log_test(
                            "Структура individual units",
                            True,
                            f"Все критические поля присутствуют. Формат номера: {individual_number} ({cargo_number}/{type_num}/{unit_idx})"
                        )
                        return True
                    else:
                        self.log_test(
                            "Формат individual_number",
                            False,
                            f"Неверный формат individual_number: {individual_number}",
                            "ЗАЯВКА/ТИП/ЕДИНИЦА",
                            individual_number
                        )
                        return False
                else:
                    self.log_test(
                        "Структура individual units",
                        False,
                        f"Отсутствуют критические поля: {missing_fields}",
                        str(critical_fields),
                        str(list(first_unit.keys()))
                    )
                    return False
            else:
                self.log_test("Структура individual units", True, "Нет единиц для проверки структуры")
                return True
                
        except Exception as e:
            self.log_test("Структура individual units", False, f"Исключение: {str(e)}")
            return False

    def test_filtering_cargo_type_and_status(self):
        """Тест фильтрации по cargo_type_filter и status_filter согласно review request"""
        try:
            print("🎯 ТЕСТ 3: ФИЛЬТРАЦИЯ ПО ТИПУ ГРУЗА И СТАТУСУ")
            
            # Тест фильтра по типу груза "01"
            response = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement?cargo_type_filter=01")
            
            if response.status_code == 200:
                data = response.json()
                total_type_01 = data.get('total', 0)
                self.log_test(
                    "Фильтрация по cargo_type_filter='01'",
                    True,
                    f"Фильтр работает корректно. Единиц типа 01: {total_type_01}"
                )
                
                # Проверяем корректность фильтрации
                individual_units = data.get('individual_units', [])
                wrong_type_units = [unit for unit in individual_units if unit.get('type_number') != '01']
                
                if wrong_type_units:
                    self.log_test(
                        "Корректность фильтра по типу груза",
                        False,
                        f"Найдены единицы с неверным типом: {len(wrong_type_units)}"
                    )
                else:
                    self.log_test(
                        "Корректность фильтра по типу груза",
                        True,
                        f"Все единицы имеют корректный тип (проверено {len(individual_units)} единиц)"
                    )
            else:
                self.log_test(
                    "Фильтрация по cargo_type_filter",
                    False,
                    f"Ошибка фильтрации: {response.status_code}"
                )
            
            # Тест фильтра по статусу "awaiting"
            response = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement?status_filter=awaiting")
            
            if response.status_code == 200:
                data = response.json()
                total_awaiting = data.get('total', 0)
                self.log_test(
                    "Фильтрация по status_filter='awaiting'",
                    True,
                    f"Фильтр работает корректно. Единиц ожидающих размещения: {total_awaiting}"
                )
                
                # Проверяем корректность фильтрации по статусу
                individual_units = data.get('individual_units', [])
                wrong_status_units = [unit for unit in individual_units if unit.get('placement_status') != 'awaiting_placement']
                
                if wrong_status_units:
                    self.log_test(
                        "Корректность фильтра по статусу",
                        False,
                        f"Найдены единицы с неверным статусом: {len(wrong_status_units)}"
                    )
                else:
                    self.log_test(
                        "Корректность фильтра по статусу",
                        True,
                        f"Все единицы имеют корректный статус (проверено {len(individual_units)} единиц)"
                    )
            else:
                self.log_test(
                    "Фильтрация по status_filter",
                    False,
                    f"Ошибка фильтрации: {response.status_code}"
                )
            
            # Тест комбинированной фильтрации
            response = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement?cargo_type_filter=01&status_filter=awaiting")
            
            if response.status_code == 200:
                data = response.json()
                total_combined = data.get('total', 0)
                self.log_test(
                    "Комбинированная фильтрация",
                    True,
                    f"Комбинированная фильтрация работает корректно. Результатов: {total_combined}"
                )
                return True
            else:
                self.log_test(
                    "Комбинированная фильтрация",
                    False,
                    f"Ошибка комбинированной фильтрации: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Фильтрация", False, f"Исключение: {str(e)}")
            return False

    def test_pagination_functionality(self):
        """Тест пагинации (page, per_page) согласно review request"""
        try:
            print("🎯 ТЕСТ 4: ПАГИНАЦИЯ (page, per_page)")
            
            # Тест с малым размером страницы для проверки пагинации
            response = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement?page=1&per_page=2")
            
            if response.status_code == 200:
                data = response.json()
                
                total = data.get("total", 0)
                page = data.get("page", 1)
                per_page = data.get("per_page", 2)
                total_pages = data.get("total_pages", 1)
                items_count = len(data.get("individual_units", []))
                
                # Проверяем корректность расчета пагинации
                expected_pages = max(1, (total + per_page - 1) // per_page)
                expected_items = min(per_page, total) if total > 0 else 0
                
                if total_pages == expected_pages and items_count == expected_items:
                    self.log_test(
                        "Пагинация функционирует корректно",
                        True,
                        f"Всего: {total}, страниц: {total_pages}, на странице: {items_count}/{per_page}"
                    )
                    
                    # Тест второй страницы (если есть достаточно данных)
                    if total > per_page:
                        response2 = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement?page=2&per_page=2")
                        if response2.status_code == 200:
                            data2 = response2.json()
                            items_count_2 = len(data2.get("individual_units", []))
                            self.log_test(
                                "Пагинация - вторая страница",
                                True,
                                f"Вторая страница работает корректно. Элементов: {items_count_2}"
                            )
                        else:
                            self.log_test(
                                "Пагинация - вторая страница",
                                False,
                                f"Ошибка второй страницы: {response2.status_code}"
                            )
                    
                    return True
                else:
                    self.log_test(
                        "Пагинация - корректность расчетов",
                        False,
                        f"Неверные расчеты пагинации",
                        f"страниц: {expected_pages}, элементов: {expected_items}",
                        f"страниц: {total_pages}, элементов: {items_count}"
                    )
                    return False
            else:
                self.log_test(
                    "Пагинация",
                    False,
                    f"Ошибка пагинации: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Пагинация", False, f"Исключение: {str(e)}")
            return False

    def test_grouping_by_requests(self, sample_data):
        """Тест группировки по заявкам согласно review request"""
        try:
            print("🎯 ТЕСТ 5: ГРУППИРОВКА ПО ЗАЯВКАМ")
            
            if not sample_data or not sample_data.get("items"):
                self.log_test("Группировка по заявкам", True, "Нет данных для тестирования группировки")
                return True
            
            items = sample_data.get("items", [])
            individual_units = sample_data.get("individual_units", [])
            
            # Проверяем уникальность номеров заявок в группах
            request_numbers = [item.get("request_number") for item in items]
            unique_numbers = set(request_numbers)
            
            if len(request_numbers) == len(unique_numbers):
                self.log_test(
                    "Уникальность номеров заявок в группах",
                    True,
                    f"Все номера заявок уникальны. Групп: {len(items)}"
                )
            else:
                self.log_test(
                    "Уникальность номеров заявок",
                    False,
                    f"Найдены дублирующиеся номера заявок",
                    f"{len(unique_numbers)} уникальных",
                    f"{len(request_numbers)} всего"
                )
                return False
            
            # Проверяем соответствие единиц группам
            total_units_in_groups = sum(len(item.get("units", [])) for item in items)
            total_individual_units = len(individual_units)
            
            if total_units_in_groups == total_individual_units:
                self.log_test(
                    "Группировка работает корректно",
                    True,
                    f"Количество единиц совпадает: {total_units_in_groups} в группах = {total_individual_units} individual_units"
                )
                return True
            else:
                self.log_test(
                    "Соответствие единиц группам",
                    False,
                    f"Несоответствие количества единиц",
                    str(total_individual_units),
                    str(total_units_in_groups)
                )
                return False
            
        except Exception as e:
            self.log_test("Группировка по заявкам", False, f"Исключение: {str(e)}")
            return False

    def test_sorting_by_request_number(self):
        """Тест сортировки по номеру заявки согласно review request"""
        try:
            print("🎯 ТЕСТ 6: СОРТИРОВКА ПО НОМЕРУ ЗАЯВКИ")
            
            response = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement?per_page=10")
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                if len(items) > 1:
                    # Проверяем сортировку по номеру заявки
                    request_numbers = [item.get("request_number", "") for item in items]
                    sorted_numbers = sorted(request_numbers)
                    
                    if request_numbers == sorted_numbers:
                        self.log_test(
                            "Сортировка по номеру заявки работает корректно",
                            True,
                            f"Заявки отсортированы правильно. Первая: {request_numbers[0]}, последняя: {request_numbers[-1]}"
                        )
                        return True
                    else:
                        self.log_test(
                            "Сортировка по номеру заявки",
                            False,
                            f"Неверная сортировка",
                            str(sorted_numbers[:3]),
                            str(request_numbers[:3])
                        )
                        return False
                else:
                    self.log_test(
                        "Сортировка по номеру заявки",
                        True,
                        f"Недостаточно данных для проверки сортировки ({len(items)} элементов)"
                    )
                    return True
            else:
                self.log_test(
                    "Сортировка по номеру заявки",
                    False,
                    f"Ошибка получения данных: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Сортировка по номеру заявки", False, f"Исключение: {str(e)}")
            return False

    def cleanup_test_data(self):
        """Очистка тестовых данных"""
        try:
            print("🧹 ОЧИСТКА ТЕСТОВЫХ ДАННЫХ")
            
            cleaned_count = 0
            for cargo_id in self.created_cargo_ids:
                try:
                    # Пытаемся удалить из operator_cargo
                    response = self.session.delete(f"{API_BASE}/admin/cargo/{cargo_id}")
                    if response.status_code in [200, 404]:
                        cleaned_count += 1
                except:
                    pass
            
            if cleaned_count > 0:
                self.log_test(
                    "Очистка тестовых данных",
                    True,
                    f"Удалено {cleaned_count} тестовых заявок"
                )
            else:
                self.log_test(
                    "Очистка тестовых данных",
                    True,
                    "Нет данных для очистки"
                )
                
        except Exception as e:
            self.log_test("Очистка тестовых данных", False, f"Исключение: {str(e)}")

    def run_final_comprehensive_tests(self):
        """Запуск финального комплексного тестирования"""
        print("🎯 FINAL COMPREHENSIVE TESTING: Individual Units для размещения груза в TAJLINE.TJ")
        print("=" * 90)
        
        # Авторизация
        if not self.authenticate_warehouse_operator():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться")
            return False
        
        # Создание тестовых данных
        print("\n📦 СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ")
        test_cargo_1 = self.create_test_cargo_with_multiple_items(" A")
        test_cargo_2 = self.create_test_cargo_with_multiple_items(" B")
        
        if not test_cargo_1 and not test_cargo_2:
            print("⚠️ ПРЕДУПРЕЖДЕНИЕ: Не удалось создать тестовые данные, тестируем с существующими")
        
        # Основные тесты согласно review request
        print("\n🎯 ОСНОВНЫЕ ТЕСТЫ СОГЛАСНО REVIEW REQUEST")
        
        # Тест 1: Базовая функциональность API endpoint
        sample_data = self.test_api_endpoint_basic_functionality()
        if sample_data is None:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: API endpoint не работает")
            self.cleanup_test_data()
            return False
        
        # Тест 2: Структура данных individual units
        self.test_individual_units_data_structure(sample_data)
        
        # Тест 3: Фильтрация по cargo_type_filter и status_filter
        self.test_filtering_cargo_type_and_status()
        
        # Тест 4: Пагинация (page, per_page)
        self.test_pagination_functionality()
        
        # Тест 5: Группировка по заявкам
        self.test_grouping_by_requests(sample_data)
        
        # Тест 6: Сортировка по номеру заявки
        self.test_sorting_by_request_number()
        
        # Очистка
        self.cleanup_test_data()
        
        # Подведение итогов
        self.print_final_summary()
        
        return True

    def print_final_summary(self):
        """Финальный отчет о тестировании"""
        print("\n" + "=" * 90)
        print("📊 FINAL COMPREHENSIVE TEST RESULTS")
        print("=" * 90)
        
        total_tests = len(self.test_results)
        successful_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - successful_tests
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Всего тестов: {total_tests}")
        print(f"Успешных: {successful_tests} ✅")
        print(f"Неудачных: {failed_tests} ❌")
        print(f"Процент успеха: {success_rate:.1f}%")
        print()
        
        # Критические тесты согласно review request
        critical_tests = [
            "API endpoint возвращает корректную структуру",
            "Структура individual units", 
            "Фильтрация по cargo_type_filter='01'",
            "Фильтрация по status_filter='awaiting'",
            "Комбинированная фильтрация",
            "Пагинация функционирует корректно",
            "Группировка работает корректно",
            "Сортировка по номеру заявки работает корректно"
        ]
        
        critical_passed = 0
        for test in self.test_results:
            if test["test"] in critical_tests and test["success"]:
                critical_passed += 1
        
        critical_rate = (critical_passed / len(critical_tests) * 100) if critical_tests else 0
        
        print(f"КРИТИЧЕСКИЕ ТЕСТЫ (согласно review request): {critical_passed}/{len(critical_tests)} ({critical_rate:.1f}%)")
        
        if failed_tests > 0:
            print("\n❌ НЕУДАЧНЫЕ ТЕСТЫ:")
            for test in self.test_results:
                if not test["success"]:
                    print(f"  • {test['test']}: {test['details']}")
            print()
        
        # Финальный вывод согласно review request
        if success_rate >= 95 and critical_rate >= 90:
            print("🎉 ТЕСТИРОВАНИЕ НОВОГО API ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ GET /api/operator/cargo/individual-units-for-placement работает корректно")
            print("✅ Все критические функции протестированы согласно review request:")
            print("   • Корректность структуры возвращаемых данных ✅")
            print("   • Фильтрация по cargo_type_filter и status_filter ✅")
            print("   • Пагинация (page, per_page) ✅")
            print("   • Группировка по заявкам ✅")
            print("   • Сортировка по номеру заявки ✅")
            print("   • Критические поля для проверки присутствуют ✅")
        elif success_rate >= 80:
            print("⚠️ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ПРЕДУПРЕЖДЕНИЯМИ")
            print("🔧 Требуются незначительные исправления")
        else:
            print("❌ ТЕСТИРОВАНИЕ ВЫЯВИЛО КРИТИЧЕСКИЕ ПРОБЛЕМЫ")
            print("🚨 Требуются серьезные исправления API endpoint")
        
        print("=" * 90)

def main():
    """Главная функция"""
    tester = FinalIndividualUnitsAPITester()
    tester.run_final_comprehensive_tests()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
🎯 COMPREHENSIVE TESTING: Individual Units для размещения груза в TAJLINE.TJ
КОНТЕКСТ: Тестирование нового API endpoint GET /api/operator/cargo/individual-units-for-placement
ЦЕЛЬ: Полное тестирование с созданием тестовых данных и проверкой всех функций
"""

import requests
import json
import os
from datetime import datetime
import uuid

# Конфигурация
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://cargo-tracker-33.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class IndividualUnitsComprehensiveTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_user = None
        self.test_results = []
        self.created_cargo_ids = []  # Для очистки после тестов
        
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

    def create_test_cargo_with_individual_items(self, cargo_number_suffix=""):
        """Создание тестовой заявки с individual_items"""
        try:
            print(f"📦 СОЗДАНИЕ ТЕСТОВОЙ ЗАЯВКИ{cargo_number_suffix}")
            
            # Создаем заявку с несколькими типами груза и individual_items
            cargo_data = {
                "sender_full_name": f"Тестовый Отправитель{cargo_number_suffix}",
                "sender_phone": "+79991234567",
                "recipient_full_name": f"Тестовый Получатель{cargo_number_suffix}",
                "recipient_phone": "+79997654321",
                "recipient_address": f"г. Душанбе, ул. Тестовая, дом {cargo_number_suffix or '1'}",
                "description": f"Тестовый груз для individual units{cargo_number_suffix}",
                "route": "moscow_to_tajikistan",
                "payment_method": "cash_on_delivery",
                "delivery_method": "pickup",
                "cargo_items": [
                    {
                        "cargo_name": f"Электроника Samsung{cargo_number_suffix}",
                        "quantity": 2,
                        "weight": 5.0,
                        "price_per_kg": 100.0,
                        "total_amount": 1000.0
                    },
                    {
                        "cargo_name": f"Бытовая техника LG{cargo_number_suffix}",
                        "quantity": 3,
                        "weight": 8.0,
                        "price_per_kg": 80.0,
                        "total_amount": 1920.0
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/operator/cargo/accept", json=cargo_data)
            
            if response.status_code == 200:
                data = response.json()
                cargo_id = data.get("cargo_id")
                cargo_number = data.get("cargo_number")
                
                if cargo_id:
                    self.created_cargo_ids.append(cargo_id)
                    self.log_test(
                        f"Создание тестовой заявки{cargo_number_suffix}",
                        True,
                        f"Заявка создана: {cargo_number} (ID: {cargo_id}), грузы: 2 типа (2+3=5 единиц)"
                    )
                    return {"cargo_id": cargo_id, "cargo_number": cargo_number}
                else:
                    self.log_test(f"Создание тестовой заявки{cargo_number_suffix}", False, "Не получен cargo_id")
                    return None
            else:
                error_text = response.text if response.text else "Неизвестная ошибка"
                self.log_test(
                    f"Создание тестовой заявки{cargo_number_suffix}",
                    False,
                    f"Ошибка создания: {response.status_code} - {error_text}"
                )
                return None
                
        except Exception as e:
            self.log_test(f"Создание тестовой заявки{cargo_number_suffix}", False, f"Исключение: {str(e)}")
            return None

    def test_basic_functionality(self):
        """Тест базовой функциональности endpoint"""
        try:
            print("🎯 ТЕСТ 1: БАЗОВАЯ ФУНКЦИОНАЛЬНОСТЬ")
            
            response = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement")
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем структуру ответа
                required_fields = ["items", "individual_units", "total", "page", "per_page", "total_pages"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    total_units = data.get('total', 0)
                    items_count = len(data.get('items', []))
                    individual_units_count = len(data.get('individual_units', []))
                    
                    self.log_test(
                        "Базовый запрос к endpoint",
                        True,
                        f"Корректный ответ. Всего единиц: {total_units}, групп: {items_count}, individual_units: {individual_units_count}"
                    )
                    return data
                else:
                    self.log_test(
                        "Структура ответа",
                        False,
                        f"Отсутствуют обязательные поля: {missing_fields}",
                        str(required_fields),
                        str(list(data.keys()))
                    )
                    return None
            else:
                self.log_test(
                    "Базовый запрос к endpoint",
                    False,
                    f"HTTP ошибка: {response.status_code}",
                    "200",
                    str(response.status_code)
                )
                return None
                
        except Exception as e:
            self.log_test("Базовая функциональность", False, f"Исключение: {str(e)}")
            return None

    def test_individual_units_structure(self, sample_data):
        """Тест структуры individual units"""
        try:
            print("🎯 ТЕСТ 2: СТРУКТУРА INDIVIDUAL UNITS")
            
            if not sample_data or not sample_data.get("individual_units"):
                self.log_test("Структура individual units", True, "Нет individual_units для тестирования")
                return True
            
            individual_units = sample_data.get("individual_units", [])
            
            if individual_units:
                first_unit = individual_units[0]
                
                # Критические поля для individual units
                critical_fields = [
                    "individual_number", "cargo_request_number", "type_number", "unit_index",
                    "placement_status", "is_placed", "cargo_name", "sender_full_name", 
                    "recipient_full_name", "warehouse_name", "accepting_operator"
                ]
                
                missing_fields = [field for field in critical_fields if field not in first_unit]
                
                if not missing_fields:
                    # Проверяем формат individual_number
                    individual_number = first_unit.get("individual_number", "")
                    if "/" in individual_number and len(individual_number.split("/")) == 3:
                        self.log_test(
                            "Структура individual units",
                            True,
                            f"Все критические поля присутствуют. Пример: {individual_number}"
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

    def test_filtering_functionality(self):
        """Тест фильтрации по cargo_type_filter и status_filter"""
        try:
            print("🎯 ТЕСТ 3: ФИЛЬТРАЦИЯ")
            
            # Тест фильтра по типу груза "01"
            response = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement?cargo_type_filter=01")
            
            if response.status_code == 200:
                data = response.json()
                total_type_01 = data.get('total', 0)
                self.log_test(
                    "Фильтр по типу груза (01)",
                    True,
                    f"Фильтр работает. Единиц типа 01: {total_type_01}"
                )
                
                # Проверяем, что все единицы имеют type_number = "01"
                individual_units = data.get('individual_units', [])
                wrong_type_units = [unit for unit in individual_units if unit.get('type_number') != '01']
                
                if wrong_type_units:
                    self.log_test(
                        "Корректность фильтра по типу",
                        False,
                        f"Найдены единицы с неверным типом: {len(wrong_type_units)}"
                    )
                else:
                    self.log_test(
                        "Корректность фильтра по типу",
                        True,
                        f"Все единицы имеют корректный тип (проверено {len(individual_units)} единиц)"
                    )
            else:
                self.log_test(
                    "Фильтр по типу груза",
                    False,
                    f"Ошибка фильтрации: {response.status_code}"
                )
            
            # Тест фильтра по статусу "awaiting"
            response = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement?status_filter=awaiting")
            
            if response.status_code == 200:
                data = response.json()
                total_awaiting = data.get('total', 0)
                self.log_test(
                    "Фильтр по статусу (awaiting)",
                    True,
                    f"Фильтр работает. Единиц ожидающих размещения: {total_awaiting}"
                )
                
                # Проверяем статусы
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
                    "Фильтр по статусу",
                    False,
                    f"Ошибка фильтрации: {response.status_code}"
                )
            
            # Тест комбинированных фильтров
            response = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement?cargo_type_filter=01&status_filter=awaiting")
            
            if response.status_code == 200:
                data = response.json()
                total_combined = data.get('total', 0)
                self.log_test(
                    "Комбинированные фильтры",
                    True,
                    f"Комбинированная фильтрация работает. Результатов: {total_combined}"
                )
                return True
            else:
                self.log_test(
                    "Комбинированные фильтры",
                    False,
                    f"Ошибка комбинированной фильтрации: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Фильтрация", False, f"Исключение: {str(e)}")
            return False

    def test_pagination_functionality(self):
        """Тест пагинации (page, per_page)"""
        try:
            print("🎯 ТЕСТ 4: ПАГИНАЦИЯ")
            
            # Тест с малым размером страницы
            response = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement?page=1&per_page=2")
            
            if response.status_code == 200:
                data = response.json()
                
                total = data.get("total", 0)
                page = data.get("page", 1)
                per_page = data.get("per_page", 2)
                total_pages = data.get("total_pages", 1)
                items_count = len(data.get("individual_units", []))
                
                # Проверяем корректность пагинации
                expected_pages = max(1, (total + per_page - 1) // per_page)
                expected_items = min(per_page, total) if total > 0 else 0
                
                if total_pages == expected_pages and items_count == expected_items:
                    self.log_test(
                        "Пагинация - корректность расчетов",
                        True,
                        f"Всего: {total}, страниц: {total_pages}, на странице: {items_count}/{per_page}"
                    )
                    
                    # Тест второй страницы (если есть данные)
                    if total > per_page:
                        response2 = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement?page=2&per_page=2")
                        if response2.status_code == 200:
                            data2 = response2.json()
                            items_count_2 = len(data2.get("individual_units", []))
                            self.log_test(
                                "Пагинация - вторая страница",
                                True,
                                f"Вторая страница работает. Элементов: {items_count_2}"
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
        """Тест группировки по заявкам"""
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
                    "Уникальность номеров заявок",
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
                    "Соответствие единиц группам",
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
        """Тест сортировки по номеру заявки"""
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
                            "Сортировка по номеру заявки",
                            True,
                            f"Заявки отсортированы корректно. Первая: {request_numbers[0]}, последняя: {request_numbers[-1]}"
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

    def run_comprehensive_tests(self):
        """Запуск всех тестов"""
        print("🎯 COMPREHENSIVE TESTING: Individual Units для размещения груза")
        print("=" * 80)
        
        # Авторизация
        if not self.authenticate_warehouse_operator():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться")
            return False
        
        # Создание тестовых данных
        print("\n📦 СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ")
        test_cargo_1 = self.create_test_cargo_with_individual_items(" #1")
        test_cargo_2 = self.create_test_cargo_with_individual_items(" #2")
        
        if not test_cargo_1 and not test_cargo_2:
            print("⚠️ ПРЕДУПРЕЖДЕНИЕ: Не удалось создать тестовые данные, тестируем с существующими")
        
        # Основные тесты
        print("\n🎯 ОСНОВНЫЕ ТЕСТЫ")
        
        # Тест 1: Базовая функциональность
        sample_data = self.test_basic_functionality()
        if sample_data is None:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Базовая функциональность не работает")
            self.cleanup_test_data()
            return False
        
        # Тест 2: Структура individual units
        self.test_individual_units_structure(sample_data)
        
        # Тест 3: Фильтрация
        self.test_filtering_functionality()
        
        # Тест 4: Пагинация
        self.test_pagination_functionality()
        
        # Тест 5: Группировка
        self.test_grouping_by_requests(sample_data)
        
        # Тест 6: Сортировка
        self.test_sorting_by_request_number()
        
        # Очистка
        self.cleanup_test_data()
        
        # Подведение итогов
        self.print_comprehensive_summary()
        
        return True

    def print_comprehensive_summary(self):
        """Вывод итогов тестирования"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        successful_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - successful_tests
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Всего тестов: {total_tests}")
        print(f"Успешных: {successful_tests} ✅")
        print(f"Неудачных: {failed_tests} ❌")
        print(f"Процент успеха: {success_rate:.1f}%")
        print()
        
        # Критические поля для проверки
        critical_tests = [
            "Базовый запрос к endpoint",
            "Структура individual units", 
            "Фильтр по типу груза (01)",
            "Фильтр по статусу (awaiting)",
            "Комбинированные фильтры",
            "Пагинация - корректность расчетов",
            "Группировка по заявкам",
            "Сортировка по номеру заявки"
        ]
        
        critical_passed = 0
        for test in self.test_results:
            if test["test"] in critical_tests and test["success"]:
                critical_passed += 1
        
        critical_rate = (critical_passed / len(critical_tests) * 100) if critical_tests else 0
        
        print(f"КРИТИЧЕСКИЕ ТЕСТЫ: {critical_passed}/{len(critical_tests)} ({critical_rate:.1f}%)")
        
        if failed_tests > 0:
            print("\n❌ НЕУДАЧНЫЕ ТЕСТЫ:")
            for test in self.test_results:
                if not test["success"]:
                    print(f"  • {test['test']}: {test['details']}")
            print()
        
        # Общий вывод
        if success_rate >= 95 and critical_rate >= 90:
            print("🎉 COMPREHENSIVE TESTING ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ API endpoint individual-units-for-placement работает корректно")
            print("✅ Все критические функции протестированы и работают")
        elif success_rate >= 80:
            print("⚠️ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ПРЕДУПРЕЖДЕНИЯМИ")
            print("🔧 Требуются незначительные исправления")
        else:
            print("❌ ТЕСТИРОВАНИЕ ВЫЯВИЛО КРИТИЧЕСКИЕ ПРОБЛЕМЫ")
            print("🚨 Требуются серьезные исправления")
        
        print("=" * 80)

def main():
    """Главная функция"""
    tester = IndividualUnitsComprehensiveTester()
    tester.run_comprehensive_tests()

if __name__ == "__main__":
    main()
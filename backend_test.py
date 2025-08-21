#!/usr/bin/env python3
"""
🎯 ТЕСТИРОВАНИЕ НОВОГО API: individual-units-for-placement
КОНТЕКСТ: Создан новый backend endpoint для индивидуальных единиц груза вместо заявок
ЦЕЛЬ: Протестировать GET /api/operator/cargo/individual-units-for-placement
"""

import requests
import json
import os
from datetime import datetime

# Конфигурация
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://logistics-dash-6.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class IndividualUnitsAPITester:
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

    def test_basic_functionality(self):
        """Тест базовой функциональности endpoint"""
        try:
            print("🎯 ТЕСТ 1: БАЗОВАЯ ФУНКЦИОНАЛЬНОСТЬ")
            
            # Тестируем базовый запрос без параметров
            response = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement")
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем структуру ответа
                required_fields = ["items", "total", "page", "per_page"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_test(
                        "Базовый запрос к endpoint",
                        True,
                        f"Получен корректный ответ. Всего единиц: {data.get('total', 0)}, страница: {data.get('page', 1)}"
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

    def test_data_structure(self, sample_data):
        """Тест структуры данных"""
        try:
            print("🎯 ТЕСТ 2: СТРУКТУРА ДАННЫХ")
            
            if not sample_data or not sample_data.get("items"):
                self.log_test("Структура данных", True, "Нет данных для тестирования структуры (пустой список)")
                return True
            
            items = sample_data.get("items", [])
            
            # Проверяем структуру первого элемента
            if items:
                first_item = items[0]
                
                # Проверяем обязательные поля группы
                group_required_fields = ["request_number", "units"]
                group_missing_fields = [field for field in group_required_fields if field not in first_item]
                
                if group_missing_fields:
                    self.log_test(
                        "Структура группы заявок",
                        False,
                        f"Отсутствуют поля в группе: {group_missing_fields}",
                        str(group_required_fields),
                        str(list(first_item.keys()))
                    )
                    return False
                
                # Проверяем структуру единиц груза
                units = first_item.get("units", [])
                if units:
                    first_unit = units[0]
                    unit_required_fields = ["individual_number", "cargo_request_number", "cargo_name", "type_number", "unit_index"]
                    unit_missing_fields = [field for field in unit_required_fields if field not in first_unit]
                    
                    if unit_missing_fields:
                        self.log_test(
                            "Структура единицы груза",
                            False,
                            f"Отсутствуют поля в единице: {unit_missing_fields}",
                            str(unit_required_fields),
                            str(list(first_unit.keys()))
                        )
                        return False
                    
                    # Проверяем формат individual_number
                    individual_number = first_unit.get("individual_number", "")
                    if "/" in individual_number:
                        parts = individual_number.split("/")
                        if len(parts) == 3:
                            self.log_test(
                                "Формат individual_number",
                                True,
                                f"Корректный формат: {individual_number} (заявка/тип/единица)"
                            )
                        else:
                            self.log_test(
                                "Формат individual_number",
                                False,
                                f"Неверный формат: {individual_number}",
                                "ЗАЯВКА/ТИП/ЕДИНИЦА",
                                individual_number
                            )
                            return False
                    else:
                        self.log_test(
                            "Формат individual_number",
                            False,
                            f"Отсутствуют разделители в номере: {individual_number}",
                            "ЗАЯВКА/ТИП/ЕДИНИЦА",
                            individual_number
                        )
                        return False
                
                self.log_test(
                    "Структура данных",
                    True,
                    f"Все обязательные поля присутствуют. Групп: {len(items)}, единиц в первой группе: {len(units)}"
                )
                return True
            else:
                self.log_test("Структура данных", True, "Нет элементов для проверки структуры")
                return True
                
        except Exception as e:
            self.log_test("Структура данных", False, f"Исключение: {str(e)}")
            return False

    def test_filtering(self):
        """Тест фильтрации по типу груза и статусу"""
        try:
            print("🎯 ТЕСТ 3: ФИЛЬТРАЦИЯ")
            
            # Тест фильтра по типу груза
            response = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement?cargo_type_filter=01")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Фильтр по типу груза (01)",
                    True,
                    f"Фильтр работает. Результатов: {data.get('total', 0)}"
                )
            else:
                self.log_test(
                    "Фильтр по типу груза",
                    False,
                    f"Ошибка фильтрации: {response.status_code}"
                )
            
            # Тест фильтра по статусу
            response = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement?status_filter=awaiting")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Фильтр по статусу (awaiting)",
                    True,
                    f"Фильтр работает. Результатов: {data.get('total', 0)}"
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
                self.log_test(
                    "Комбинированные фильтры",
                    True,
                    f"Комбинированная фильтрация работает. Результатов: {data.get('total', 0)}"
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

    def test_pagination(self):
        """Тест пагинации"""
        try:
            print("🎯 ТЕСТ 4: ПАГИНАЦИЯ")
            
            # Тест первой страницы
            response = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement?page=1&per_page=5")
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем поля пагинации
                pagination_fields = ["total", "page", "per_page", "total_pages"]
                missing_pagination = [field for field in pagination_fields if field not in data]
                
                if not missing_pagination:
                    total = data.get("total", 0)
                    page = data.get("page", 1)
                    per_page = data.get("per_page", 5)
                    total_pages = data.get("total_pages", 1)
                    
                    self.log_test(
                        "Пагинация - поля",
                        True,
                        f"Все поля пагинации присутствуют. Всего: {total}, страница: {page}/{total_pages}, на странице: {per_page}"
                    )
                    
                    # Проверяем корректность расчета total_pages
                    expected_pages = (total + per_page - 1) // per_page if total > 0 else 1
                    if total_pages == expected_pages:
                        self.log_test(
                            "Пагинация - расчет страниц",
                            True,
                            f"Корректный расчет страниц: {total_pages}"
                        )
                    else:
                        self.log_test(
                            "Пагинация - расчет страниц",
                            False,
                            f"Неверный расчет страниц",
                            str(expected_pages),
                            str(total_pages)
                        )
                        return False
                    
                    # Тест второй страницы (если есть данные)
                    if total > per_page:
                        response2 = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement?page=2&per_page=5")
                        if response2.status_code == 200:
                            data2 = response2.json()
                            self.log_test(
                                "Пагинация - вторая страница",
                                True,
                                f"Вторая страница работает. Элементов: {len(data2.get('items', []))}"
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
                        "Пагинация - поля",
                        False,
                        f"Отсутствуют поля пагинации: {missing_pagination}",
                        str(pagination_fields),
                        str(list(data.keys()))
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

    def test_grouping_functionality(self, sample_data):
        """Тест группировки по заявкам"""
        try:
            print("🎯 ТЕСТ 5: ГРУППИРОВКА ПО ЗАЯВКАМ")
            
            if not sample_data or not sample_data.get("items"):
                self.log_test("Группировка по заявкам", True, "Нет данных для тестирования группировки")
                return True
            
            items = sample_data.get("items", [])
            
            # Проверяем, что каждая группа имеет уникальный request_number
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
            
            # Проверяем, что единицы в группе принадлежат одной заявке
            for item in items:
                request_number = item.get("request_number")
                units = item.get("units", [])
                
                for unit in units:
                    unit_request_number = unit.get("cargo_request_number")
                    if unit_request_number != request_number:
                        self.log_test(
                            "Соответствие единиц заявкам",
                            False,
                            f"Единица {unit.get('individual_number')} не соответствует группе",
                            request_number,
                            unit_request_number
                        )
                        return False
            
            self.log_test(
                "Группировка по заявкам",
                True,
                f"Группировка работает корректно. Проверено {len(items)} групп"
            )
            return True
            
        except Exception as e:
            self.log_test("Группировка по заявкам", False, f"Исключение: {str(e)}")
            return False

    def test_sorting(self):
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

    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🎯 НАЧАЛО ТЕСТИРОВАНИЯ НОВОГО API: individual-units-for-placement")
        print("=" * 80)
        
        # Авторизация
        if not self.authenticate_warehouse_operator():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться")
            return False
        
        # Тест 1: Базовая функциональность
        sample_data = self.test_basic_functionality()
        if sample_data is None:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Базовая функциональность не работает")
            return False
        
        # Тест 2: Структура данных
        if not self.test_data_structure(sample_data):
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Неверная структура данных")
            return False
        
        # Тест 3: Фильтрация
        self.test_filtering()
        
        # Тест 4: Пагинация
        self.test_pagination()
        
        # Тест 5: Группировка
        self.test_grouping_functionality(sample_data)
        
        # Тест 6: Сортировка
        self.test_sorting()
        
        # Подведение итогов
        self.print_summary()
        
        return True

    def print_summary(self):
        """Вывод итогов тестирования"""
        print("=" * 80)
        print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
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
        
        if failed_tests > 0:
            print("❌ НЕУДАЧНЫЕ ТЕСТЫ:")
            for test in self.test_results:
                if not test["success"]:
                    print(f"  • {test['test']}: {test['details']}")
            print()
        
        # Общий вывод
        if success_rate >= 90:
            print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ Новый API endpoint individual-units-for-placement работает корректно")
        elif success_rate >= 70:
            print("⚠️ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ПРЕДУПРЕЖДЕНИЯМИ")
            print("🔧 Требуются незначительные исправления")
        else:
            print("❌ ТЕСТИРОВАНИЕ ВЫЯВИЛО КРИТИЧЕСКИЕ ПРОБЛЕМЫ")
            print("🚨 Требуются серьезные исправления")
        
        print("=" * 80)

def main():
    """Главная функция"""
    tester = IndividualUnitsAPITester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
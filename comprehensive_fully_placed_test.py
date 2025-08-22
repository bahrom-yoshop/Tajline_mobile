#!/usr/bin/env python3
"""
🎯 COMPREHENSIVE TESTING: API endpoint /api/operator/cargo/fully-placed с диагностикой данных

Этот тест проверяет:
1. Работу endpoint /api/operator/cargo/fully-placed
2. Логику определения полностью размещенных заявок
3. Соответствие данных между различными endpoints
4. Диагностику проблем с данными
"""

import requests
import json
import sys
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://placement-view.preview.emergentagent.com/api"

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

class ComprehensiveFullyPlacedTester:
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
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(f"Аутентификация {user_type}", False, f"Исключение: {str(e)}")
            return False

    def diagnose_data_consistency(self, user_type: str = "warehouse_operator") -> bool:
        """Диагностика консистентности данных между endpoints"""
        try:
            if user_type not in self.tokens:
                self.log_test("Диагностика данных", False, f"Пользователь {user_type} не аутентифицирован")
                return False
                
            headers = {"Authorization": f"Bearer {self.tokens[user_type]}"}
            
            # 1. Получаем individual units для размещения
            response1 = self.session.get(f"{BACKEND_URL}/operator/cargo/individual-units-for-placement", headers=headers)
            individual_units_data = response1.json() if response1.status_code == 200 else {}
            
            # 2. Получаем прогресс размещения
            response2 = self.session.get(f"{BACKEND_URL}/operator/placement-progress", headers=headers)
            progress_data = response2.json() if response2.status_code == 200 else {}
            
            # 3. Получаем полностью размещенные заявки
            response3 = self.session.get(f"{BACKEND_URL}/operator/cargo/fully-placed", headers=headers)
            fully_placed_data = response3.json() if response3.status_code == 200 else {}
            
            # 4. Получаем доступные для размещения заявки
            response4 = self.session.get(f"{BACKEND_URL}/operator/cargo/available-for-placement", headers=headers)
            available_data = response4.json() if response4.status_code == 200 else {}
            
            print("📊 ДИАГНОСТИКА ДАННЫХ:")
            print(f"Individual units для размещения: {len(individual_units_data.get('items', []))} групп")
            print(f"Прогресс размещения: {progress_data.get('total_units', 0)} всего, {progress_data.get('placed_units', 0)} размещено")
            print(f"Полностью размещенные заявки: {len(fully_placed_data.get('items', []))} заявок")
            print(f"Доступные для размещения: {len(available_data.get('items', []))} заявок")
            
            # Анализируем individual units
            if individual_units_data.get('items'):
                for i, group in enumerate(individual_units_data['items']):
                    request_number = group.get('request_number', 'Неизвестно')
                    total_units = group.get('total_units', 0)
                    placed_units = group.get('placed_units', 0)
                    units = group.get('units', [])
                    
                    print(f"\\n📋 Группа {i+1}: Заявка {request_number}")
                    print(f"   Всего единиц: {total_units}")
                    print(f"   Размещено единиц: {placed_units}")
                    print(f"   Единиц в массиве: {len(units)}")
                    
                    # Проверяем статус каждой единицы
                    placed_count = 0
                    for unit in units:
                        is_placed = unit.get('is_placed', False)
                        placement_info = unit.get('placement_info', '')
                        individual_number = unit.get('individual_number', '')
                        
                        if is_placed:
                            placed_count += 1
                        
                        print(f"   - {individual_number}: {'✅ Размещен' if is_placed else '❌ Не размещен'} ({placement_info})")
                    
                    print(f"   Фактически размещено: {placed_count}/{len(units)}")
                    
                    # Проверяем, должна ли эта заявка быть в fully-placed
                    if placed_count == len(units) and len(units) > 0:
                        print(f"   🎯 ЗАЯВКА {request_number} ДОЛЖНА БЫТЬ В FULLY-PLACED!")
                        
                        # Проверяем, есть ли она в fully-placed
                        found_in_fully_placed = False
                        for fp_item in fully_placed_data.get('items', []):
                            if fp_item.get('cargo_number') == request_number or fp_item.get('request_number') == request_number:
                                found_in_fully_placed = True
                                break
                        
                        if not found_in_fully_placed:
                            self.log_test(
                                f"Консистентность данных - заявка {request_number}",
                                False,
                                f"Заявка {request_number} полностью размещена ({placed_count}/{len(units)}), но НЕ найдена в fully-placed endpoint"
                            )
                            return False
                        else:
                            print(f"   ✅ Заявка найдена в fully-placed")
                    else:
                        print(f"   ⏳ Заявка не полностью размещена ({placed_count}/{len(units)})")
            
            self.log_test(
                "Диагностика консистентности данных",
                True,
                f"Проанализированы данные из 4 endpoints. Individual units: {len(individual_units_data.get('items', []))}, Fully placed: {len(fully_placed_data.get('items', []))}"
            )
            return True
            
        except Exception as e:
            self.log_test("Диагностика данных", False, f"Исключение: {str(e)}")
            return False

    def test_fully_placed_endpoint_comprehensive(self, user_type: str = "warehouse_operator") -> bool:
        """Комплексное тестирование fully-placed endpoint"""
        try:
            if user_type not in self.tokens:
                self.log_test("Тестирование fully-placed endpoint", False, f"Пользователь {user_type} не аутентифицирован")
                return False
                
            headers = {"Authorization": f"Bearer {self.tokens[user_type]}"}
            
            # Тест 1: Базовый запрос
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/fully-placed", headers=headers)
            
            if response.status_code != 200:
                self.log_test(
                    "Fully-placed endpoint доступность",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
            
            data = response.json()
            
            # Проверяем структуру ответа
            required_fields = ["items", "pagination", "summary"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.log_test(
                    "Структура ответа fully-placed",
                    False,
                    f"Отсутствуют поля: {missing_fields}"
                )
                return False
            
            items = data.get("items", [])
            pagination = data.get("pagination", {})
            summary = data.get("summary", {})
            
            print(f"📊 РЕЗУЛЬТАТЫ FULLY-PLACED ENDPOINT:")
            print(f"Количество элементов: {len(items)}")
            print(f"Пагинация: страница {pagination.get('current_page', 0)}/{pagination.get('total_pages', 0)}")
            print(f"Сводка: {summary.get('fully_placed_requests', 0)} заявок, {summary.get('total_units_placed', 0)} единиц")
            
            # Тест 2: Проверка полей элементов (если есть)
            if items:
                item = items[0]
                required_item_fields = [
                    "sender_full_name", "sender_phone", "sender_address",
                    "recipient_full_name", "recipient_phone", "recipient_address",
                    "individual_units", "progress_text"
                ]
                
                missing_item_fields = [field for field in required_item_fields if field not in item]
                
                if missing_item_fields:
                    self.log_test(
                        "Поля элементов fully-placed",
                        False,
                        f"Отсутствуют поля в элементе: {missing_item_fields}"
                    )
                    return False
                
                # Проверяем individual_units
                individual_units = item.get("individual_units", [])
                print(f"\\n📋 ПЕРВЫЙ ЭЛЕМЕНТ:")
                print(f"Заявка: {item.get('cargo_number', 'Неизвестно')}")
                print(f"Отправитель: {item.get('sender_full_name', 'Неизвестно')}")
                print(f"Получатель: {item.get('recipient_full_name', 'Неизвестно')}")
                print(f"Прогресс: {item.get('progress_text', 'Неизвестно')}")
                print(f"Individual units: {len(individual_units)}")
                
                if individual_units:
                    unit = individual_units[0]
                    required_unit_fields = ["individual_number", "is_placed", "placement_info"]
                    missing_unit_fields = [field for field in required_unit_fields if field not in unit]
                    
                    if missing_unit_fields:
                        self.log_test(
                            "Поля individual_units",
                            False,
                            f"Отсутствуют поля в individual_units: {missing_unit_fields}"
                        )
                        return False
                    
                    print(f"Первая единица: {unit.get('individual_number', 'Неизвестно')} - {'✅ Размещена' if unit.get('is_placed') else '❌ Не размещена'}")
                    print(f"Место размещения: {unit.get('placement_info', 'Неизвестно')}")
            
            # Тест 3: Пагинация
            response_page2 = self.session.get(f"{BACKEND_URL}/operator/cargo/fully-placed?page=2&per_page=5", headers=headers)
            if response_page2.status_code == 200:
                data_page2 = response_page2.json()
                pagination_page2 = data_page2.get("pagination", {})
                
                if pagination_page2.get("current_page") != 2:
                    self.log_test(
                        "Пагинация fully-placed",
                        False,
                        f"Неверная страница в пагинации: ожидалось 2, получено {pagination_page2.get('current_page')}"
                    )
                    return False
            
            self.log_test(
                "Комплексное тестирование fully-placed endpoint",
                True,
                f"Endpoint работает корректно. Найдено {len(items)} полностью размещенных заявок"
            )
            return True
            
        except Exception as e:
            self.log_test("Тестирование fully-placed endpoint", False, f"Исключение: {str(e)}")
            return False

    def test_role_access(self) -> bool:
        """Тестирование доступа для разных ролей"""
        try:
            results = []
            
            # Тест для warehouse_operator
            if "warehouse_operator" in self.tokens:
                headers = {"Authorization": f"Bearer {self.tokens['warehouse_operator']}"}
                response = self.session.get(f"{BACKEND_URL}/operator/cargo/fully-placed", headers=headers)
                
                if response.status_code == 200:
                    self.log_test(
                        "Доступ warehouse_operator",
                        True,
                        f"Оператор склада имеет доступ к endpoint"
                    )
                    results.append(True)
                else:
                    self.log_test(
                        "Доступ warehouse_operator",
                        False,
                        f"Оператор склада НЕ имеет доступ: HTTP {response.status_code}"
                    )
                    results.append(False)
            
            # Тест для admin (если доступен)
            if "admin" in self.tokens:
                headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
                response = self.session.get(f"{BACKEND_URL}/operator/cargo/fully-placed", headers=headers)
                
                if response.status_code == 200:
                    self.log_test(
                        "Доступ admin",
                        True,
                        f"Администратор имеет доступ к endpoint"
                    )
                    results.append(True)
                else:
                    self.log_test(
                        "Доступ admin",
                        False,
                        f"Администратор НЕ имеет доступ: HTTP {response.status_code}"
                    )
                    results.append(False)
            
            # Тест без авторизации
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/fully-placed")
            
            if response.status_code == 401 or response.status_code == 403:
                self.log_test(
                    "Доступ без авторизации",
                    True,
                    f"Доступ корректно запрещен без авторизации: HTTP {response.status_code}"
                )
                results.append(True)
            else:
                self.log_test(
                    "Доступ без авторизации",
                    False,
                    f"Доступ НЕ запрещен без авторизации: HTTP {response.status_code}"
                )
                results.append(False)
            
            return all(results)
            
        except Exception as e:
            self.log_test("Тестирование доступа ролей", False, f"Исключение: {str(e)}")
            return False

    def run_comprehensive_test(self):
        """Запуск полного комплексного тестирования"""
        print("🎯 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ: API endpoint /api/operator/cargo/fully-placed")
        print("=" * 80)
        print()
        
        # Аутентификация пользователей
        print("📋 ЭТАП 1: АУТЕНТИФИКАЦИЯ ПОЛЬЗОВАТЕЛЕЙ")
        print("-" * 50)
        admin_auth = self.authenticate_user("admin")
        operator_auth = self.authenticate_user("warehouse_operator")
        print()
        
        if not operator_auth:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось аутентифицировать оператора склада!")
            return False
        
        # Диагностика данных
        print("📋 ЭТАП 2: ДИАГНОСТИКА КОНСИСТЕНТНОСТИ ДАННЫХ")
        print("-" * 50)
        data_diagnosis = self.diagnose_data_consistency("warehouse_operator")
        print()
        
        # Комплексное тестирование endpoint
        print("📋 ЭТАП 3: КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ FULLY-PLACED ENDPOINT")
        print("-" * 50)
        endpoint_test = self.test_fully_placed_endpoint_comprehensive("warehouse_operator")
        print()
        
        # Тестирование доступа ролей
        print("📋 ЭТАП 4: ТЕСТИРОВАНИЕ ДОСТУПА ДЛЯ РАЗНЫХ РОЛЕЙ")
        print("-" * 50)
        role_access_test = self.test_role_access()
        print()
        
        # Подведение итогов
        self.print_summary()
        
        # Определяем общий результат
        critical_tests = [data_diagnosis, endpoint_test, role_access_test]
        success_rate = sum(1 for test in critical_tests if test) / len(critical_tests) * 100
        
        return success_rate >= 75

    def print_summary(self):
        """Вывод итогового отчета"""
        print("📊 ИТОГОВЫЙ ОТЧЕТ КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ")
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
    tester = ComprehensiveFullyPlacedTester()
    
    try:
        success = tester.run_comprehensive_test()
        
        if success:
            print("🎯 ЗАКЛЮЧЕНИЕ: Комплексное тестирование API endpoint /api/operator/cargo/fully-placed завершено успешно!")
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
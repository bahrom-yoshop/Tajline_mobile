#!/usr/bin/env python3
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
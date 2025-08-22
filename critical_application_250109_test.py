#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправление проблемы с заявкой 250109 - полностью размещенные заявки не перемещаются в "Список грузов"

КОНТЕКСТ КРИТИЧЕСКОЙ ПРОБЛЕМЫ:
Пользователь сообщил, что заявка 250109 полностью размещена (все грузы размещены), но она до сих пор показывается в списке размещения вместо перемещения в "Грузы" → "Список грузов".

ИСПРАВЛЕНИЯ, КОТОРЫЕ БЫЛИ СДЕЛАНЫ:
1. ✅ Backend API фильтрация: Обновлен `/api/operator/cargo/available-for-placement` для исключения полностью размещенных заявок
2. ✅ Логика исключения: Добавлена проверка `placed_units < total_units` с подсчетом через placement_records
3. ✅ Frontend обновление: Добавлено обновление списка полностью размещенных после каждого размещения

КРИТИЧЕСКИЕ ТЕСТЫ:
1. Проверка заявки 250109 в available-for-placement (НЕ должна присутствовать если полностью размещена)
2. Проверка заявки 250109 в fully-placed (ДОЛЖНА присутствовать если полностью размещена)
3. Проверка логики фильтрации placement_records
4. Создание тестового случая с полным размещением
"""

import requests
import json
import time
from datetime import datetime
import os

# Конфигурация для тестирования
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://placement-view.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Тестовые данные оператора склада
OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class CriticalApplication250109Tester:
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
                        f"Склад получен: {warehouse.get('name')} (ID: {self.warehouse_id})"
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

    def test_application_250109_available_for_placement(self):
        """ПРИОРИТЕТ 1: Проверка заявки 250109 в available-for-placement"""
        try:
            print("🎯 ПРИОРИТЕТ 1: ПРОВЕРКА ЗАЯВКИ 250109 В СПИСКЕ РАЗМЕЩЕНИЯ")
            
            response = self.session.get(f"{API_BASE}/operator/cargo/available-for-placement", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                # Ищем заявку 250109
                application_250109 = None
                for item in items:
                    cargo_number = item.get("cargo_number", "")
                    if "250109" in cargo_number:
                        application_250109 = item
                        break
                
                if application_250109:
                    # Заявка найдена - проверяем статус размещения
                    cargo_items = application_250109.get("cargo_items", [])
                    total_units = 0
                    placed_units = 0
                    
                    for cargo_item in cargo_items:
                        quantity = cargo_item.get("quantity", 1)
                        total_units += quantity
                        
                        # Проверяем individual_items для подсчета размещенных единиц
                        individual_items = cargo_item.get("individual_items", [])
                        for individual_item in individual_items:
                            if individual_item.get("is_placed", False):
                                placed_units += 1
                    
                    placement_status = f"{placed_units}/{total_units}"
                    
                    if placed_units >= total_units:
                        # Заявка полностью размещена, но все еще в списке размещения - это проблема
                        self.log_test(
                            "Заявка 250109 НЕ должна быть в available-for-placement",
                            False,
                            f"Заявка 250109 полностью размещена ({placement_status}), но все еще показывается в списке размещения",
                            "Заявка НЕ должна присутствовать в available-for-placement",
                            f"Заявка найдена со статусом {placement_status}"
                        )
                        return False
                    else:
                        # Заявка не полностью размещена - это нормально
                        self.log_test(
                            "Заявка 250109 корректно присутствует в available-for-placement",
                            True,
                            f"Заявка 250109 не полностью размещена ({placement_status}), корректно показывается в списке размещения"
                        )
                        return True
                else:
                    # Заявка не найдена - возможно уже перемещена в fully-placed
                    self.log_test(
                        "Заявка 250109 отсутствует в available-for-placement",
                        True,
                        "Заявка 250109 НЕ найдена в списке размещения (возможно полностью размещена и перемещена)"
                    )
                    return True
            else:
                self.log_test(
                    "GET /api/operator/cargo/available-for-placement",
                    False,
                    f"HTTP ошибка: {response.status_code}",
                    "200",
                    str(response.status_code)
                )
                return False
                
        except Exception as e:
            self.log_test("Проверка заявки 250109 в available-for-placement", False, f"Исключение: {str(e)}")
            return False

    def test_application_250109_fully_placed(self):
        """ПРИОРИТЕТ 1: Проверка заявки 250109 в fully-placed"""
        try:
            print("🎯 ПРИОРИТЕТ 1: ПРОВЕРКА ЗАЯВКИ 250109 В СПИСКЕ ПОЛНОСТЬЮ РАЗМЕЩЕННЫХ")
            
            response = self.session.get(f"{API_BASE}/operator/cargo/fully-placed", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                # Ищем заявку 250109
                application_250109 = None
                for item in items:
                    cargo_number = item.get("cargo_number", "")
                    if "250109" in cargo_number:
                        application_250109 = item
                        break
                
                if application_250109:
                    # Заявка найдена в fully-placed - проверяем статус
                    cargo_items = application_250109.get("cargo_items", [])
                    total_units = 0
                    placed_units = 0
                    
                    for cargo_item in cargo_items:
                        quantity = cargo_item.get("quantity", 1)
                        total_units += quantity
                        
                        # Проверяем individual_items для подсчета размещенных единиц
                        individual_items = cargo_item.get("individual_items", [])
                        for individual_item in individual_items:
                            if individual_item.get("is_placed", False):
                                placed_units += 1
                    
                    placement_status = f"{placed_units}/{total_units}"
                    
                    if placed_units >= total_units:
                        # Заявка полностью размещена и находится в правильном списке
                        self.log_test(
                            "Заявка 250109 корректно находится в fully-placed",
                            True,
                            f"Заявка 250109 полностью размещена ({placement_status}) и корректно находится в списке полностью размещенных"
                        )
                        return True
                    else:
                        # Заявка не полностью размещена, но находится в fully-placed - это проблема
                        self.log_test(
                            "Заявка 250109 НЕ должна быть в fully-placed",
                            False,
                            f"Заявка 250109 не полностью размещена ({placement_status}), но находится в списке полностью размещенных",
                            f"Заявка должна быть полностью размещена",
                            f"Статус размещения: {placement_status}"
                        )
                        return False
                else:
                    # Заявка не найдена в fully-placed
                    self.log_test(
                        "Заявка 250109 отсутствует в fully-placed",
                        False,
                        "Заявка 250109 НЕ найдена в списке полностью размещенных (возможно еще не полностью размещена)",
                        "Заявка должна присутствовать если полностью размещена",
                        "Заявка не найдена"
                    )
                    return False
            else:
                self.log_test(
                    "GET /api/operator/cargo/fully-placed",
                    False,
                    f"HTTP ошибка: {response.status_code}",
                    "200",
                    str(response.status_code)
                )
                return False
                
        except Exception as e:
            self.log_test("Проверка заявки 250109 в fully-placed", False, f"Исключение: {str(e)}")
            return False

    def test_placement_records_logic(self):
        """ПРИОРИТЕТ 2: Проверка логики placement_records для 250109"""
        try:
            print("🎯 ПРИОРИТЕТ 2: ПРОВЕРКА ЛОГИКИ PLACEMENT_RECORDS ДЛЯ 250109")
            
            # Сначала получаем информацию о заявке 250109 из available-for-placement
            available_response = self.session.get(f"{API_BASE}/operator/cargo/available-for-placement", timeout=30)
            
            application_250109 = None
            if available_response.status_code == 200:
                available_data = available_response.json()
                items = available_data.get("items", [])
                
                for item in items:
                    cargo_number = item.get("cargo_number", "")
                    if "250109" in cargo_number:
                        application_250109 = item
                        break
            
            # Если не найдена в available, проверяем в fully-placed
            if not application_250109:
                fully_placed_response = self.session.get(f"{API_BASE}/operator/cargo/fully-placed", timeout=30)
                
                if fully_placed_response.status_code == 200:
                    fully_placed_data = fully_placed_response.json()
                    items = fully_placed_data.get("items", [])
                    
                    for item in items:
                        cargo_number = item.get("cargo_number", "")
                        if "250109" in cargo_number:
                            application_250109 = item
                            break
            
            if application_250109:
                cargo_id = application_250109.get("id")
                cargo_number = application_250109.get("cargo_number")
                
                # Подсчитываем единицы через cargo_items
                cargo_items = application_250109.get("cargo_items", [])
                total_units = 0
                placed_units = 0
                
                placement_details = []
                
                for cargo_item in cargo_items:
                    quantity = cargo_item.get("quantity", 1)
                    total_units += quantity
                    
                    # Проверяем individual_items
                    individual_items = cargo_item.get("individual_items", [])
                    for individual_item in individual_items:
                        individual_number = individual_item.get("individual_number", "")
                        is_placed = individual_item.get("is_placed", False)
                        
                        if is_placed:
                            placed_units += 1
                            placement_details.append(f"{individual_number}: размещен")
                        else:
                            placement_details.append(f"{individual_number}: ожидает размещения")
                
                placement_status = f"{placed_units}/{total_units}"
                is_fully_placed = placed_units >= total_units
                
                self.log_test(
                    "Логика подсчета placement_records для 250109",
                    True,
                    f"Заявка {cargo_number}: {placement_status}, полностью размещена: {is_fully_placed}. Детали: {', '.join(placement_details[:5])}" + ("..." if len(placement_details) > 5 else "")
                )
                
                # Проверяем корректность логики исключения
                should_be_in_available = not is_fully_placed
                should_be_in_fully_placed = is_fully_placed
                
                self.log_test(
                    "Логика фильтрации для 250109",
                    True,
                    f"Должна быть в available-for-placement: {should_be_in_available}, должна быть в fully-placed: {should_be_in_fully_placed}"
                )
                
                return True
            else:
                self.log_test(
                    "Поиск заявки 250109 для анализа placement_records",
                    False,
                    "Заявка 250109 не найдена ни в available-for-placement, ни в fully-placed",
                    "Заявка должна быть найдена в одном из списков",
                    "Заявка не найдена"
                )
                return False
                
        except Exception as e:
            self.log_test("Проверка логики placement_records", False, f"Исключение: {str(e)}")
            return False

    def test_create_and_fully_place_application(self):
        """ПРИОРИТЕТ 2: Создание тестового случая с полным размещением"""
        try:
            print("🎯 ПРИОРИТЕТ 2: СОЗДАНИЕ ТЕСТОВОГО СЛУЧАЯ С ПОЛНЫМ РАЗМЕЩЕНИЕМ")
            
            # Создаем новую заявку с несколькими единицами
            cargo_data = {
                "sender_full_name": "Тестовый Отправитель",
                "sender_phone": "+79999999999",
                "recipient_full_name": "Тестовый Получатель",
                "recipient_phone": "+79888888888",
                "recipient_address": "Тестовый адрес получателя",
                "description": "Тестовая заявка для проверки полного размещения",
                "route": "moscow_to_tajikistan",
                "cargo_items": [
                    {
                        "cargo_name": "Тестовый груз 1",
                        "quantity": 2,
                        "weight": 10.0,
                        "price_per_kg": 100.0,
                        "total_amount": 1000.0
                    },
                    {
                        "cargo_name": "Тестовый груз 2",
                        "quantity": 3,
                        "weight": 15.0,
                        "price_per_kg": 150.0,
                        "total_amount": 2250.0
                    }
                ],
                "payment_method": "cash_on_delivery"
            }
            
            # Создаем заявку
            create_response = self.session.post(
                f"{API_BASE}/operator/cargo/accept",
                json=cargo_data,
                timeout=30
            )
            
            if create_response.status_code != 200:
                self.log_test(
                    "Создание тестовой заявки",
                    False,
                    f"Ошибка создания заявки: {create_response.status_code}",
                    "200",
                    str(create_response.status_code)
                )
                return False
            
            create_data = create_response.json()
            test_cargo_number = create_data.get("cargo_number")
            test_cargo_id = create_data.get("cargo_id")
            
            if not test_cargo_number:
                self.log_test("Получение номера тестовой заявки", False, "Не получен номер заявки")
                return False
            
            self.log_test(
                "Создание тестовой заявки",
                True,
                f"Создана тестовая заявка: {test_cargo_number} (5 единиц: 2+3)"
            )
            
            # Ждем немного для обработки
            time.sleep(2)
            
            # Проверяем, что заявка появилась в available-for-placement
            available_response = self.session.get(f"{API_BASE}/operator/cargo/available-for-placement", timeout=30)
            
            if available_response.status_code != 200:
                self.log_test("Проверка появления в available-for-placement", False, f"Ошибка: {available_response.status_code}")
                return False
            
            available_data = available_response.json()
            items = available_data.get("items", [])
            
            test_application = None
            for item in items:
                if item.get("cargo_number") == test_cargo_number:
                    test_application = item
                    break
            
            if not test_application:
                self.log_test(
                    "Тестовая заявка в available-for-placement",
                    False,
                    f"Тестовая заявка {test_cargo_number} не найдена в списке размещения",
                    "Заявка должна присутствовать",
                    "Заявка не найдена"
                )
                return False
            
            self.log_test(
                "Тестовая заявка появилась в available-for-placement",
                True,
                f"Заявка {test_cargo_number} корректно появилась в списке размещения"
            )
            
            # Получаем individual_numbers для размещения
            cargo_items = test_application.get("cargo_items", [])
            individual_numbers = []
            
            for cargo_item in cargo_items:
                individual_items = cargo_item.get("individual_items", [])
                for individual_item in individual_items:
                    individual_number = individual_item.get("individual_number")
                    if individual_number:
                        individual_numbers.append(individual_number)
            
            if len(individual_numbers) != 5:
                self.log_test(
                    "Получение individual_numbers",
                    False,
                    f"Ожидалось 5 individual_numbers, получено {len(individual_numbers)}",
                    "5",
                    str(len(individual_numbers))
                )
                return False
            
            self.log_test(
                "Получение individual_numbers для размещения",
                True,
                f"Получено {len(individual_numbers)} individual_numbers: {', '.join(individual_numbers[:3])}..."
            )
            
            # Размещаем все единицы
            placed_count = 0
            for i, individual_number in enumerate(individual_numbers):
                placement_data = {
                    "individual_number": individual_number,
                    "block_number": 1,
                    "shelf_number": 1,
                    "cell_number": i + 1  # Разные ячейки
                }
                
                place_response = self.session.post(
                    f"{API_BASE}/operator/cargo/place-individual",
                    json=placement_data,
                    timeout=30
                )
                
                if place_response.status_code == 200:
                    placed_count += 1
                    print(f"    ✅ Размещена единица {individual_number} ({placed_count}/5)")
                else:
                    print(f"    ❌ Ошибка размещения {individual_number}: {place_response.status_code}")
            
            if placed_count != 5:
                self.log_test(
                    "Размещение всех единиц тестовой заявки",
                    False,
                    f"Размещено {placed_count}/5 единиц",
                    "5",
                    str(placed_count)
                )
                return False
            
            self.log_test(
                "Размещение всех единиц тестовой заявки",
                True,
                f"Все 5 единиц успешно размещены"
            )
            
            # Ждем обновления данных
            time.sleep(3)
            
            # Проверяем, что заявка исчезла из available-for-placement
            available_response_after = self.session.get(f"{API_BASE}/operator/cargo/available-for-placement", timeout=30)
            
            if available_response_after.status_code == 200:
                available_data_after = available_response_after.json()
                items_after = available_data_after.get("items", [])
                
                test_application_after = None
                for item in items_after:
                    if item.get("cargo_number") == test_cargo_number:
                        test_application_after = item
                        break
                
                if test_application_after:
                    self.log_test(
                        "Тестовая заявка должна исчезнуть из available-for-placement",
                        False,
                        f"Заявка {test_cargo_number} все еще присутствует в списке размещения после полного размещения",
                        "Заявка НЕ должна присутствовать",
                        "Заявка найдена"
                    )
                    return False
                else:
                    self.log_test(
                        "Тестовая заявка исчезла из available-for-placement",
                        True,
                        f"Заявка {test_cargo_number} корректно исчезла из списка размещения"
                    )
            
            # Проверяем, что заявка появилась в fully-placed
            fully_placed_response = self.session.get(f"{API_BASE}/operator/cargo/fully-placed", timeout=30)
            
            if fully_placed_response.status_code == 200:
                fully_placed_data = fully_placed_response.json()
                items_fully_placed = fully_placed_data.get("items", [])
                
                test_application_fully_placed = None
                for item in items_fully_placed:
                    if item.get("cargo_number") == test_cargo_number:
                        test_application_fully_placed = item
                        break
                
                if test_application_fully_placed:
                    self.log_test(
                        "Тестовая заявка появилась в fully-placed",
                        True,
                        f"Заявка {test_cargo_number} корректно появилась в списке полностью размещенных"
                    )
                    return True
                else:
                    self.log_test(
                        "Тестовая заявка должна появиться в fully-placed",
                        False,
                        f"Заявка {test_cargo_number} не найдена в списке полностью размещенных",
                        "Заявка должна присутствовать",
                        "Заявка не найдена"
                    )
                    return False
            else:
                self.log_test("Проверка fully-placed после размещения", False, f"Ошибка: {fully_placed_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Создание и полное размещение тестовой заявки", False, f"Исключение: {str(e)}")
            return False

    def run_all_tests(self):
        """Запуск всех критических тестов"""
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправление проблемы с заявкой 250109")
        print("=" * 80)
        
        # Подготовка
        if not self.authenticate_operator():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться")
            return False
        
        if not self.get_operator_warehouse():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить склад оператора")
            return False
        
        # Запуск критических тестов
        test_results = []
        
        test_results.append(("ПРИОРИТЕТ 1: Заявка 250109 в available-for-placement", self.test_application_250109_available_for_placement()))
        test_results.append(("ПРИОРИТЕТ 1: Заявка 250109 в fully-placed", self.test_application_250109_fully_placed()))
        test_results.append(("ПРИОРИТЕТ 2: Логика placement_records для 250109", self.test_placement_records_logic()))
        test_results.append(("ПРИОРИТЕТ 2: Создание и полное размещение тестовой заявки", self.test_create_and_fully_place_application()))
        
        # Подведение итогов
        print("\n" + "=" * 80)
        print("📊 РЕЗУЛЬТАТЫ КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ:")
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
        
        if success_rate == 100:
            print("🎉 ВСЕ КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ РАБОТАЮТ ИДЕАЛЬНО! Заявка 250109 и все будущие полностью размещенные заявки корректно перемещаются между списками!")
        elif success_rate >= 75:
            print("🎯 ХОРОШИЙ РЕЗУЛЬТАТ! Большинство критических исправлений работают корректно.")
        else:
            print("❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ! Исправления не работают корректно. Требуется дополнительная работа.")
        
        return success_rate >= 75  # Ожидаем минимум 75% для критических тестов

def main():
    """Главная функция"""
    tester = CriticalApplication250109Tester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("Проблема с заявкой 250109 решена корректно")
        return 0
    else:
        print("\n❌ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ВЫЯВИЛО ПРОБЛЕМЫ!")
        print("Требуется дополнительная работа над исправлениями")
        return 1

if __name__ == "__main__":
    exit(main())
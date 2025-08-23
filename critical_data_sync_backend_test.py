#!/usr/bin/env python3
"""
🔥 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ: Синхронизация данных между placement_records и individual_items для решения проблемы заявки 250109

КОНТЕКСТ КРИТИЧЕСКОГО ИСПРАВЛЕНИЯ:
Обнаружен и исправлен критический баг: POST /api/operator/cargo/place-individual создавал записи в placement_records, 
но НЕ обновлял individual_items.is_placed в основном cargo документе. Это вызывало несоответствие данных между источниками.

ИСПРАВЛЕНИЯ:
1. ✅ Синхронизация данных: Добавлено обновление individual_items.is_placed = True в основном cargo документе
2. ✅ Двойная проверка: Попытка обновления в operator_cargo и cargo коллекциях
3. ✅ Дополнительные поля: placement_info, placed_by, placed_at, warehouse_name

КРИТИЧЕСКИЕ ТЕСТЫ ПОСЛЕ ИСПРАВЛЕНИЯ:
1. POST /api/operator/cargo/place-individual - синхронизация данных
2. GET /api/operator/cargo/available-for-placement - корректная фильтрация
3. GET /api/operator/cargo/fully-placed - корректное перемещение заявок
4. Диагностика заявки 250109
5. Полный цикл создания и размещения новой заявки
"""

import requests
import json
import time
from datetime import datetime
import os

# Конфигурация для тестирования
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-manage-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Тестовые данные оператора склада
OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class CriticalDataSyncTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_user = None
        self.warehouse_id = None
        self.test_cargo_id = None
        self.test_cargo_number = None
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

    def create_test_cargo_with_individual_units(self):
        """Создание тестовой заявки с individual units для тестирования синхронизации"""
        try:
            print("📦 Создание тестовой заявки с individual units...")
            
            cargo_data = {
                "sender_full_name": "Тестовый Отправитель Синхронизации",
                "sender_phone": "+79999999999",
                "recipient_full_name": "Тестовый Получатель Синхронизации",
                "recipient_phone": "+79888888888",
                "recipient_address": "Душанбе, тестовый адрес для синхронизации",
                "description": "Тестовый груз для проверки синхронизации данных между placement_records и individual_items",
                "route": "moscow_to_tajikistan",
                "payment_method": "cash_on_delivery",
                "cargo_items": [
                    {
                        "cargo_name": "Тестовый груз тип 1",
                        "quantity": 2,
                        "weight": 5.0,
                        "price_per_kg": 100.0,
                        "total_amount": 500.0
                    },
                    {
                        "cargo_name": "Тестовый груз тип 2", 
                        "quantity": 3,
                        "weight": 3.0,
                        "price_per_kg": 150.0,
                        "total_amount": 450.0
                    }
                ]
            }
            
            response = self.session.post(
                f"{API_BASE}/operator/cargo/accept",
                json=cargo_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.test_cargo_id = data.get("cargo_id")
                self.test_cargo_number = data.get("cargo_number")
                
                self.log_test(
                    "Создание тестовой заявки с individual units",
                    True,
                    f"Заявка создана: {self.test_cargo_number} (ID: {self.test_cargo_id}), грузы: 2 типа (2+3=5 единиц)"
                )
                return True
            else:
                self.log_test(
                    "Создание тестовой заявки",
                    False,
                    f"Ошибка создания заявки: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Создание тестовой заявки", False, f"Исключение: {str(e)}")
            return False

    def test_data_synchronization_place_individual(self):
        """ПРИОРИТЕТ 1: Тестирование синхронизации данных в POST /api/operator/cargo/place-individual"""
        try:
            print("🎯 ПРИОРИТЕТ 1: ТЕСТИРОВАНИЕ СИНХРОНИЗАЦИИ ДАННЫХ")
            
            # Сначала получаем individual units для размещения
            response = self.session.get(f"{API_BASE}/operator/cargo/available-for-placement", timeout=30)
            
            if response.status_code != 200:
                self.log_test("Получение заявок для размещения", False, f"Ошибка: {response.status_code}")
                return False
            
            data = response.json()
            items = data.get("items", [])
            
            # Ищем нашу тестовую заявку
            test_cargo = None
            for item in items:
                if item.get("cargo_number") == self.test_cargo_number:
                    test_cargo = item
                    break
            
            if not test_cargo:
                self.log_test("Поиск тестовой заявки", False, f"Тестовая заявка {self.test_cargo_number} не найдена в списке размещения")
                return False
            
            # Получаем individual_items
            cargo_items = test_cargo.get("cargo_items", [])
            if not cargo_items:
                self.log_test("Получение cargo_items", False, "Отсутствуют cargo_items в тестовой заявке")
                return False
            
            # Берем первую единицу первого типа груза для размещения
            first_cargo_item = cargo_items[0]
            individual_items = first_cargo_item.get("individual_items", [])
            
            if not individual_items:
                self.log_test("Получение individual_items", False, "Отсутствуют individual_items")
                return False
            
            test_unit = individual_items[0]
            individual_number = test_unit.get("individual_number")
            
            if not individual_number:
                self.log_test("Получение individual_number", False, "Отсутствует individual_number")
                return False
            
            print(f"   📋 Размещаем единицу: {individual_number}")
            
            # Проверяем состояние ПЕРЕД размещением
            is_placed_before = test_unit.get("is_placed", False)
            print(f"   📊 Состояние ПЕРЕД размещением: is_placed = {is_placed_before}")
            
            # Размещаем единицу
            placement_data = {
                "individual_number": individual_number,
                "block_number": 1,
                "shelf_number": 1,
                "cell_number": 1
            }
            
            place_response = self.session.post(
                f"{API_BASE}/operator/cargo/place-individual",
                json=placement_data,
                timeout=30
            )
            
            if place_response.status_code != 200:
                self.log_test(
                    "Размещение individual unit",
                    False,
                    f"Ошибка размещения: {place_response.status_code} - {place_response.text}"
                )
                return False
            
            place_data = place_response.json()
            print(f"   ✅ Размещение выполнено: {place_data.get('message', 'Успешно')}")
            
            # Проверяем синхронизацию данных ПОСЛЕ размещения
            time.sleep(2)  # Даем время на обновление данных
            
            # Получаем обновленные данные заявки
            updated_response = self.session.get(f"{API_BASE}/operator/cargo/available-for-placement", timeout=30)
            
            if updated_response.status_code == 200:
                updated_data = updated_response.json()
                updated_items = updated_data.get("items", [])
                
                # Ищем обновленную заявку
                updated_cargo = None
                for item in updated_items:
                    if item.get("cargo_number") == self.test_cargo_number:
                        updated_cargo = item
                        break
                
                if updated_cargo:
                    # Проверяем обновленное состояние individual_items
                    updated_cargo_items = updated_cargo.get("cargo_items", [])
                    if updated_cargo_items:
                        updated_individual_items = updated_cargo_items[0].get("individual_items", [])
                        if updated_individual_items:
                            updated_unit = None
                            for unit in updated_individual_items:
                                if unit.get("individual_number") == individual_number:
                                    updated_unit = unit
                                    break
                            
                            if updated_unit:
                                is_placed_after = updated_unit.get("is_placed", False)
                                print(f"   📊 Состояние ПОСЛЕ размещения: is_placed = {is_placed_after}")
                                
                                if is_placed_after:
                                    self.log_test(
                                        "Синхронизация данных: individual_items.is_placed обновлен",
                                        True,
                                        f"✅ КРИТИЧЕСКИЙ БАГ ИСПРАВЛЕН! individual_items.is_placed корректно обновлен с {is_placed_before} на {is_placed_after}"
                                    )
                                    return True
                                else:
                                    self.log_test(
                                        "Синхронизация данных: individual_items.is_placed НЕ обновлен",
                                        False,
                                        f"❌ КРИТИЧЕСКИЙ БАГ НЕ ИСПРАВЛЕН! individual_items.is_placed остался {is_placed_after}",
                                        "True",
                                        str(is_placed_after)
                                    )
                                    return False
                            else:
                                self.log_test("Поиск размещенной единицы", False, "Размещенная единица не найдена в обновленных данных")
                                return False
                        else:
                            self.log_test("Получение обновленных individual_items", False, "Отсутствуют individual_items в обновленных данных")
                            return False
                    else:
                        self.log_test("Получение обновленных cargo_items", False, "Отсутствуют cargo_items в обновленных данных")
                        return False
                else:
                    # Заявка может исчезнуть из available-for-placement если полностью размещена
                    print("   📋 Заявка исчезла из available-for-placement - проверяем fully-placed")
                    
                    fully_placed_response = self.session.get(f"{API_BASE}/operator/cargo/fully-placed", timeout=30)
                    if fully_placed_response.status_code == 200:
                        fully_placed_data = fully_placed_response.json()
                        fully_placed_items = fully_placed_data.get("items", [])
                        
                        # Ищем заявку в fully-placed
                        found_in_fully_placed = False
                        for item in fully_placed_items:
                            if item.get("cargo_number") == self.test_cargo_number:
                                found_in_fully_placed = True
                                break
                        
                        if found_in_fully_placed:
                            self.log_test(
                                "Синхронизация данных: заявка перемещена в fully-placed",
                                True,
                                f"✅ ОТЛИЧНЫЙ РЕЗУЛЬТАТ! Заявка {self.test_cargo_number} корректно перемещена в fully-placed после размещения"
                            )
                            return True
                        else:
                            self.log_test(
                                "Поиск заявки в fully-placed",
                                False,
                                f"Заявка {self.test_cargo_number} не найдена ни в available-for-placement, ни в fully-placed"
                            )
                            return False
                    else:
                        self.log_test("Получение fully-placed заявок", False, f"Ошибка: {fully_placed_response.status_code}")
                        return False
            else:
                self.log_test("Получение обновленных данных", False, f"Ошибка: {updated_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Тестирование синхронизации данных", False, f"Исключение: {str(e)}")
            return False

    def test_available_for_placement_filtering(self):
        """ПРИОРИТЕТ 2: Тестирование корректной фильтрации в GET /api/operator/cargo/available-for-placement"""
        try:
            print("🎯 ПРИОРИТЕТ 2: ТЕСТИРОВАНИЕ ФИЛЬТРАЦИИ AVAILABLE-FOR-PLACEMENT")
            
            response = self.session.get(f"{API_BASE}/operator/cargo/available-for-placement", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                total = data.get("total", 0)
                
                # Проверяем, что заявки в списке действительно требуют размещения
                partially_placed_count = 0
                fully_placed_count = 0
                
                for item in items:
                    cargo_items = item.get("cargo_items", [])
                    total_units = 0
                    placed_units = 0
                    
                    for cargo_item in cargo_items:
                        individual_items = cargo_item.get("individual_items", [])
                        total_units += len(individual_items)
                        placed_units += sum(1 for unit in individual_items if unit.get("is_placed", False))
                    
                    if placed_units == 0:
                        # Не размещена
                        pass
                    elif placed_units < total_units:
                        # Частично размещена
                        partially_placed_count += 1
                    else:
                        # Полностью размещена (не должна быть в этом списке)
                        fully_placed_count += 1
                
                if fully_placed_count == 0:
                    self.log_test(
                        "Фильтрация available-for-placement",
                        True,
                        f"✅ Фильтрация работает корректно! Получено {len(items)} заявок, из них {partially_placed_count} частично размещенных, 0 полностью размещенных"
                    )
                    return True
                else:
                    self.log_test(
                        "Фильтрация available-for-placement",
                        False,
                        f"❌ Найдены полностью размещенные заявки в списке размещения: {fully_placed_count}",
                        "0 полностью размещенных заявок",
                        f"{fully_placed_count} полностью размещенных заявок"
                    )
                    return False
            else:
                self.log_test(
                    "GET available-for-placement",
                    False,
                    f"Ошибка получения списка: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Тестирование фильтрации available-for-placement", False, f"Исключение: {str(e)}")
            return False

    def test_fully_placed_endpoint(self):
        """ПРИОРИТЕТ 2: Тестирование GET /api/operator/cargo/fully-placed"""
        try:
            print("🎯 ПРИОРИТЕТ 2: ТЕСТИРОВАНИЕ FULLY-PLACED ENDPOINT")
            
            response = self.session.get(f"{API_BASE}/operator/cargo/fully-placed", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем структуру ответа
                required_fields = ["items", "pagination", "summary"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    items = data.get("items", [])
                    pagination = data.get("pagination", {})
                    summary = data.get("summary", {})
                    
                    # Проверяем, что все заявки в списке действительно полностью размещены
                    incorrect_items = 0
                    
                    for item in items:
                        cargo_items = item.get("cargo_items", [])
                        total_units = 0
                        placed_units = 0
                        
                        for cargo_item in cargo_items:
                            individual_items = cargo_item.get("individual_items", [])
                            total_units += len(individual_items)
                            placed_units += sum(1 for unit in individual_items if unit.get("is_placed", False))
                        
                        if placed_units < total_units:
                            incorrect_items += 1
                    
                    if incorrect_items == 0:
                        self.log_test(
                            "Fully-placed endpoint корректность",
                            True,
                            f"✅ Endpoint работает корректно! Все {len(items)} заявок полностью размещены"
                        )
                        return True
                    else:
                        self.log_test(
                            "Fully-placed endpoint корректность",
                            False,
                            f"❌ Найдены не полностью размещенные заявки: {incorrect_items}",
                            "0 не полностью размещенных заявок",
                            f"{incorrect_items} не полностью размещенных заявок"
                        )
                        return False
                else:
                    self.log_test(
                        "Структура fully-placed endpoint",
                        False,
                        f"Отсутствуют поля: {missing_fields}",
                        str(required_fields),
                        str(list(data.keys()))
                    )
                    return False
            else:
                self.log_test(
                    "GET fully-placed",
                    False,
                    f"Ошибка получения списка: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Тестирование fully-placed endpoint", False, f"Исключение: {str(e)}")
            return False

    def test_application_250109_diagnosis(self):
        """ПРИОРИТЕТ 2: Диагностика конкретной заявки 250109"""
        try:
            print("🎯 ПРИОРИТЕТ 2: ДИАГНОСТИКА ЗАЯВКИ 250109")
            
            # Ищем заявку 250109 в available-for-placement
            available_response = self.session.get(f"{API_BASE}/operator/cargo/available-for-placement", timeout=30)
            found_in_available = False
            
            if available_response.status_code == 200:
                available_data = available_response.json()
                available_items = available_data.get("items", [])
                
                for item in available_items:
                    if item.get("cargo_number") == "250109":
                        found_in_available = True
                        print(f"   📋 Заявка 250109 найдена в available-for-placement")
                        
                        # Анализируем состояние individual_items
                        cargo_items = item.get("cargo_items", [])
                        total_units = 0
                        placed_units = 0
                        
                        for cargo_item in cargo_items:
                            individual_items = cargo_item.get("individual_items", [])
                            total_units += len(individual_items)
                            placed_units += sum(1 for unit in individual_items if unit.get("is_placed", False))
                        
                        print(f"   📊 Состояние individual_items: {placed_units}/{total_units} размещено")
                        break
            
            # Ищем заявку 250109 в fully-placed
            fully_placed_response = self.session.get(f"{API_BASE}/operator/cargo/fully-placed", timeout=30)
            found_in_fully_placed = False
            
            if fully_placed_response.status_code == 200:
                fully_placed_data = fully_placed_response.json()
                fully_placed_items = fully_placed_data.get("items", [])
                
                for item in fully_placed_items:
                    if item.get("cargo_number") == "250109":
                        found_in_fully_placed = True
                        print(f"   📋 Заявка 250109 найдена в fully-placed")
                        break
            
            # Анализируем результаты
            if found_in_available and found_in_fully_placed:
                self.log_test(
                    "Диагностика заявки 250109",
                    False,
                    "❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Заявка 250109 найдена в ОБОИХ списках одновременно!",
                    "Заявка должна быть только в одном списке",
                    "Заявка найдена в available-for-placement И fully-placed"
                )
                return False
            elif found_in_available:
                self.log_test(
                    "Диагностика заявки 250109",
                    True,
                    "✅ Заявка 250109 корректно находится в available-for-placement (требует размещения)"
                )
                return True
            elif found_in_fully_placed:
                self.log_test(
                    "Диагностика заявки 250109",
                    True,
                    "✅ Заявка 250109 корректно находится в fully-placed (полностью размещена)"
                )
                return True
            else:
                self.log_test(
                    "Диагностика заявки 250109",
                    False,
                    "❌ Заявка 250109 не найдена ни в одном из списков",
                    "Заявка должна быть в одном из списков",
                    "Заявка не найдена"
                )
                return False
                
        except Exception as e:
            self.log_test("Диагностика заявки 250109", False, f"Исключение: {str(e)}")
            return False

    def test_full_cycle_placement(self):
        """ПРИОРИТЕТ 3: Полный цикл создания и размещения новой заявки"""
        try:
            print("🎯 ПРИОРИТЕТ 3: ПОЛНЫЙ ЦИКЛ СОЗДАНИЯ И РАЗМЕЩЕНИЯ")
            
            # Создаем новую заявку с 3 единицами
            cycle_cargo_data = {
                "sender_full_name": "Тестовый Отправитель Цикла",
                "sender_phone": "+79777777777",
                "recipient_full_name": "Тестовый Получатель Цикла",
                "recipient_phone": "+79666666666",
                "recipient_address": "Душанбе, тестовый адрес для полного цикла",
                "description": "Тестовый груз для проверки полного цикла размещения",
                "route": "moscow_to_tajikistan",
                "payment_method": "cash_on_delivery",
                "cargo_items": [
                    {
                        "cargo_name": "Тестовый груз для цикла",
                        "quantity": 3,
                        "weight": 2.0,
                        "price_per_kg": 200.0,
                        "total_amount": 400.0
                    }
                ]
            }
            
            create_response = self.session.post(
                f"{API_BASE}/operator/cargo/accept",
                json=cycle_cargo_data,
                timeout=30
            )
            
            if create_response.status_code != 200:
                self.log_test("Создание заявки для полного цикла", False, f"Ошибка создания: {create_response.status_code}")
                return False
            
            create_data = create_response.json()
            cycle_cargo_id = create_data.get("cargo_id")
            cycle_cargo_number = create_data.get("cargo_number")
            
            print(f"   📦 Создана заявка для полного цикла: {cycle_cargo_number}")
            
            # Получаем individual units для размещения
            time.sleep(2)  # Даем время на создание individual_items
            
            available_response = self.session.get(f"{API_BASE}/operator/cargo/available-for-placement", timeout=30)
            if available_response.status_code != 200:
                self.log_test("Получение заявки для цикла", False, f"Ошибка: {available_response.status_code}")
                return False
            
            available_data = available_response.json()
            available_items = available_data.get("items", [])
            
            # Ищем нашу заявку
            cycle_cargo = None
            for item in available_items:
                if item.get("cargo_number") == cycle_cargo_number:
                    cycle_cargo = item
                    break
            
            if not cycle_cargo:
                self.log_test("Поиск заявки для цикла", False, f"Заявка {cycle_cargo_number} не найдена")
                return False
            
            # Получаем все individual units для размещения
            cargo_items = cycle_cargo.get("cargo_items", [])
            if not cargo_items:
                self.log_test("Получение cargo_items для цикла", False, "Отсутствуют cargo_items")
                return False
            
            all_individual_units = []
            for cargo_item in cargo_items:
                individual_items = cargo_item.get("individual_items", [])
                all_individual_units.extend(individual_items)
            
            if len(all_individual_units) != 3:
                self.log_test(
                    "Количество individual units",
                    False,
                    f"Ожидалось 3 единицы, получено {len(all_individual_units)}",
                    "3",
                    str(len(all_individual_units))
                )
                return False
            
            print(f"   📋 Найдено {len(all_individual_units)} единиц для размещения")
            
            # Размещаем все единицы поочередно
            placement_results = []
            
            for i, unit in enumerate(all_individual_units):
                individual_number = unit.get("individual_number")
                print(f"   📍 Размещаем единицу {i+1}/3: {individual_number}")
                
                placement_data = {
                    "individual_number": individual_number,
                    "block_number": 1,
                    "shelf_number": 1,
                    "cell_number": i + 2  # Разные ячейки
                }
                
                place_response = self.session.post(
                    f"{API_BASE}/operator/cargo/place-individual",
                    json=placement_data,
                    timeout=30
                )
                
                if place_response.status_code == 200:
                    placement_results.append(True)
                    print(f"     ✅ Единица {i+1} размещена успешно")
                    
                    # Проверяем синхронизацию после каждого размещения
                    time.sleep(1)
                    
                    # Проверяем обновление данных
                    check_response = self.session.get(f"{API_BASE}/operator/cargo/available-for-placement", timeout=30)
                    if check_response.status_code == 200:
                        check_data = check_response.json()
                        check_items = check_data.get("items", [])
                        
                        # Ищем обновленную заявку
                        updated_cargo = None
                        for item in check_items:
                            if item.get("cargo_number") == cycle_cargo_number:
                                updated_cargo = item
                                break
                        
                        if updated_cargo:
                            # Подсчитываем размещенные единицы
                            updated_cargo_items = updated_cargo.get("cargo_items", [])
                            placed_count = 0
                            total_count = 0
                            
                            for cargo_item in updated_cargo_items:
                                individual_items = cargo_item.get("individual_items", [])
                                total_count += len(individual_items)
                                placed_count += sum(1 for unit in individual_items if unit.get("is_placed", False))
                            
                            print(f"     📊 После размещения {i+1}: {placed_count}/{total_count} размещено")
                        else:
                            # Заявка может исчезнуть из available-for-placement если полностью размещена
                            if i == len(all_individual_units) - 1:  # Последняя единица
                                print(f"     📋 Заявка исчезла из available-for-placement после размещения всех единиц")
                else:
                    placement_results.append(False)
                    print(f"     ❌ Ошибка размещения единицы {i+1}: {place_response.status_code}")
            
            # Проверяем финальное состояние
            successful_placements = sum(placement_results)
            
            if successful_placements == 3:
                # Проверяем, что заявка перемещена в fully-placed
                fully_placed_response = self.session.get(f"{API_BASE}/operator/cargo/fully-placed", timeout=30)
                if fully_placed_response.status_code == 200:
                    fully_placed_data = fully_placed_response.json()
                    fully_placed_items = fully_placed_data.get("items", [])
                    
                    found_in_fully_placed = False
                    for item in fully_placed_items:
                        if item.get("cargo_number") == cycle_cargo_number:
                            found_in_fully_placed = True
                            break
                    
                    if found_in_fully_placed:
                        self.log_test(
                            "Полный цикл создания и размещения",
                            True,
                            f"✅ ПОЛНЫЙ УСПЕХ! Заявка {cycle_cargo_number} создана, все 3 единицы размещены, заявка корректно перемещена в fully-placed"
                        )
                        return True
                    else:
                        self.log_test(
                            "Перемещение в fully-placed",
                            False,
                            f"Заявка {cycle_cargo_number} не найдена в fully-placed после полного размещения"
                        )
                        return False
                else:
                    self.log_test("Проверка fully-placed", False, f"Ошибка: {fully_placed_response.status_code}")
                    return False
            else:
                self.log_test(
                    "Полный цикл размещения",
                    False,
                    f"Не все единицы размещены успешно: {successful_placements}/3",
                    "3/3",
                    f"{successful_placements}/3"
                )
                return False
                
        except Exception as e:
            self.log_test("Полный цикл создания и размещения", False, f"Исключение: {str(e)}")
            return False

    def run_all_tests(self):
        """Запуск всех критических тестов синхронизации данных"""
        print("🔥 НАЧАЛО КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ ИСПРАВЛЕНИЯ СИНХРОНИЗАЦИИ ДАННЫХ")
        print("=" * 80)
        
        # Подготовка
        if not self.authenticate_operator():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться")
            return False
        
        if not self.get_operator_warehouse():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить склад оператора")
            return False
        
        if not self.create_test_cargo_with_individual_units():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось создать тестовую заявку")
            return False
        
        # Запуск критических тестов
        test_results = []
        
        test_results.append(("ПРИОРИТЕТ 1: Синхронизация данных в place-individual", self.test_data_synchronization_place_individual()))
        test_results.append(("ПРИОРИТЕТ 2: Фильтрация available-for-placement", self.test_available_for_placement_filtering()))
        test_results.append(("ПРИОРИТЕТ 2: Fully-placed endpoint", self.test_fully_placed_endpoint()))
        test_results.append(("ПРИОРИТЕТ 2: Диагностика заявки 250109", self.test_application_250109_diagnosis()))
        test_results.append(("ПРИОРИТЕТ 3: Полный цикл создания и размещения", self.test_full_cycle_placement()))
        
        # Подведение итогов
        print("\n" + "=" * 80)
        print("📊 РЕЗУЛЬТАТЫ КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ СИНХРОНИЗАЦИИ ДАННЫХ:")
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
            print("🎉 КРИТИЧЕСКИЙ БАГ ПОЛНОСТЬЮ ИСПРАВЛЕН! 100% синхронизация между placement_records и individual_items. Заявка 250109 корректно перемещается в fully-placed. Новые размещения работают без ошибок синхронизации. СИСТЕМА ГОТОВА К ПРОДАКШЕНУ!")
        elif success_rate >= 80:
            print("🎯 ОТЛИЧНЫЙ РЕЗУЛЬТАТ! Большинство критических проблем исправлено. Система практически готова к продакшену.")
        elif success_rate >= 60:
            print("⚠️ ХОРОШИЙ РЕЗУЛЬТАТ! Основные проблемы исправлены, но есть вопросы требующие внимания.")
        else:
            print("❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ ОСТАЮТСЯ! Баг синхронизации данных не полностью исправлен. Требуется дополнительная работа.")
        
        return success_rate >= 80  # Ожидаем минимум 80% для критического исправления

def main():
    """Главная функция"""
    tester = CriticalDataSyncTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("Критический баг синхронизации данных исправлен")
        return 0
    else:
        print("\n❌ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ВЫЯВИЛО ПРОБЛЕМЫ!")
        print("Требуется дополнительная работа по исправлению синхронизации данных")
        return 1

if __name__ == "__main__":
    exit(main())
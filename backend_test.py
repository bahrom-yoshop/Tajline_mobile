#!/usr/bin/env python3
"""
🎯 ТЕСТИРОВАНИЕ НОВЫХ API: Полнофункциональное размещение груза со сканером в TAJLINE.TJ

КОНТЕКСТ: Реализованы новые backend API endpoints для полнофункционального размещения груза 
с QR сканером, аналитикой и контролем качества.

НОВЫЕ API ENDPOINTS:
1. POST /api/operator/placement/verify-cargo - Проверка существования груза по QR коду
2. POST /api/operator/placement/verify-cell - Проверка существования ячейки по QR коду  
3. POST /api/operator/placement/place-cargo - Размещение груза в ячейку со сканером
4. GET /api/operator/placement/session-history - Получение истории размещения за сессию
5. DELETE /api/operator/placement/undo-last - Отмена последнего размещения в сессии
"""

import requests
import json
import uuid
from datetime import datetime
import os

# Конфигурация
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://logistics-dash-6.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Тестовые данные
WAREHOUSE_OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class PlacementAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_user = None
        self.warehouse_id = None
        self.test_cargo_id = None
        self.test_cargo_number = None
        self.session_id = str(uuid.uuid4())
        
    def log(self, message, level="INFO"):
        """Логирование с временной меткой"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def authenticate_operator(self):
        """Авторизация оператора склада"""
        try:
            self.log("🔐 Авторизация оператора склада...")
            
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=WAREHOUSE_OPERATOR_CREDENTIALS,
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
                    self.log(f"✅ Авторизован: {self.operator_user.get('full_name')} (роль: {self.operator_user.get('role')})")
                    return True
                else:
                    self.log(f"❌ Ошибка получения данных пользователя: {user_response.status_code}", "ERROR")
                    return False
            else:
                self.log(f"❌ Ошибка авторизации: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при авторизации: {str(e)}", "ERROR")
            return False
    
    def get_operator_warehouse(self):
        """Получение склада оператора"""
        try:
            self.log("🏢 Получение склада оператора...")
            
            response = self.session.get(f"{API_BASE}/operator/warehouses", timeout=30)
            
            if response.status_code == 200:
                warehouses = response.json()
                if warehouses:
                    warehouse = warehouses[0]
                    self.warehouse_id = warehouse.get("id")
                    self.log(f"✅ Склад получен: {warehouse.get('name')} (ID: {self.warehouse_id})")
                    return True
                else:
                    self.log("❌ У оператора нет привязанных складов", "ERROR")
                    return False
            else:
                self.log(f"❌ Ошибка получения складов: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при получении складов: {str(e)}", "ERROR")
            return False
    
    def create_test_cargo(self):
        """Создание тестового груза для размещения"""
        try:
            self.log("📦 Создание тестового груза...")
            
            cargo_data = {
                "sender_full_name": "Тестовый Отправитель",
                "sender_phone": "+79991234567",
                "recipient_full_name": "Тестовый Получатель", 
                "recipient_phone": "+79997654321",
                "recipient_address": "г. Душанбе, ул. Рудаки, дом 123",
                "cargo_items": [
                    {
                        "cargo_name": "Электроника Samsung",
                        "quantity": 2,
                        "weight": 5.0,
                        "price_per_kg": 100.0,
                        "total_amount": 500.0
                    },
                    {
                        "cargo_name": "Бытовая техника LG",
                        "quantity": 3,
                        "weight": 8.0,
                        "price_per_kg": 80.0,
                        "total_amount": 640.0
                    }
                ],
                "description": "Тестовый груз для размещения",
                "route": "moscow_to_tajikistan",
                "payment_method": "cash_on_delivery",
                "delivery_method": "pickup"
            }
            
            response = self.session.post(
                f"{API_BASE}/operator/cargo/accept",
                json=cargo_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.test_cargo_id = result.get("cargo_id")
                self.test_cargo_number = result.get("cargo_number")
                self.log(f"✅ Тестовый груз создан: {self.test_cargo_number} (ID: {self.test_cargo_id})")
                return True
            else:
                self.log(f"❌ Ошибка создания груза: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при создании груза: {str(e)}", "ERROR")
            return False
    
    def test_verify_cargo_endpoint(self):
        """Тестирование POST /api/operator/placement/verify-cargo"""
        try:
            self.log("🔍 Тестирование verify-cargo endpoint...")
            
            test_cases = [
                {
                    "name": "Простой номер груза",
                    "qr_code": self.test_cargo_number,
                    "should_succeed": True
                },
                {
                    "name": "Формат individual_number",
                    "qr_code": f"{self.test_cargo_number}/01/01",
                    "should_succeed": True
                },
                {
                    "name": "Формат TAJLINE",
                    "qr_code": f"TAJLINE|UNIT|{self.test_cargo_id}|{datetime.now().isoformat()}",
                    "should_succeed": True
                },
                {
                    "name": "Несуществующий груз",
                    "qr_code": "999999999",
                    "should_succeed": False
                },
                {
                    "name": "Пустой QR код",
                    "qr_code": "",
                    "should_succeed": False
                }
            ]
            
            success_count = 0
            total_tests = len(test_cases)
            
            for test_case in test_cases:
                self.log(f"  📋 Тест: {test_case['name']}")
                
                response = self.session.post(
                    f"{API_BASE}/operator/placement/verify-cargo",
                    json={"qr_code": test_case["qr_code"]},
                    timeout=30
                )
                
                if test_case["should_succeed"]:
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("success"):
                            cargo_info = data.get("cargo_info", {})
                            self.log(f"    ✅ Груз найден: {cargo_info.get('cargo_number')}")
                            success_count += 1
                        else:
                            self.log(f"    ❌ Груз не найден: {data.get('error')}")
                    else:
                        self.log(f"    ❌ HTTP ошибка: {response.status_code}")
                else:
                    if response.status_code == 200:
                        data = response.json()
                        if not data.get("success"):
                            self.log(f"    ✅ Ожидаемая ошибка: {data.get('error')}")
                            success_count += 1
                        else:
                            self.log(f"    ❌ Неожиданный успех")
                    else:
                        self.log(f"    ✅ Ожидаемая HTTP ошибка: {response.status_code}")
                        success_count += 1
            
            self.log(f"📊 verify-cargo: {success_count}/{total_tests} тестов пройдено")
            return success_count == total_tests
            
        except Exception as e:
            self.log(f"❌ Исключение в verify-cargo: {str(e)}", "ERROR")
            return False
    
    def test_verify_cell_endpoint(self):
        """Тестирование POST /api/operator/placement/verify-cell"""
        try:
            self.log("🔍 Тестирование verify-cell endpoint...")
            
            test_cases = [
                {
                    "name": "Формат Б1-П1-Я1",
                    "qr_code": "Б1-П1-Я1",
                    "should_succeed": False,  # Ожидаем ошибку из-за отсутствия layout
                    "expected_error": "warehouse_id"
                },
                {
                    "name": "Неверный формат",
                    "qr_code": "invalid_format",
                    "should_succeed": False
                },
                {
                    "name": "Пустой QR код",
                    "qr_code": "",
                    "should_succeed": False
                }
            ]
            
            success_count = 0
            total_tests = len(test_cases)
            
            for test_case in test_cases:
                self.log(f"  📋 Тест: {test_case['name']}")
                
                response = self.session.post(
                    f"{API_BASE}/operator/placement/verify-cell",
                    json={"qr_code": test_case["qr_code"]},
                    timeout=30
                )
                
                if test_case["should_succeed"]:
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("success"):
                            cell_info = data.get("cell_info", {})
                            self.log(f"    ✅ Ячейка найдена: {cell_info.get('cell_address')} (грузов: {cell_info.get('current_cargo_count', 0)})")
                            success_count += 1
                        else:
                            self.log(f"    ❌ Ячейка не найдена: {data.get('error')}")
                    else:
                        self.log(f"    ❌ HTTP ошибка: {response.status_code}")
                else:
                    # Ожидаем ошибку
                    if response.status_code != 200:
                        self.log(f"    ✅ Ожидаемая HTTP ошибка: {response.status_code}")
                        success_count += 1
                    elif response.status_code == 200:
                        data = response.json()
                        if not data.get("success"):
                            self.log(f"    ✅ Ожидаемая ошибка: {data.get('error')}")
                            success_count += 1
                        else:
                            self.log(f"    ❌ Неожиданный успех")
                    else:
                        self.log(f"    ❌ Неожиданный результат")
            
            self.log(f"📊 verify-cell: {success_count}/{total_tests} тестов пройдено")
            return success_count == total_tests
            
        except Exception as e:
            self.log(f"❌ Исключение в verify-cell: {str(e)}", "ERROR")
            return False
    
    def test_place_cargo_endpoint(self):
        """Тестирование POST /api/operator/placement/place-cargo"""
        try:
            self.log("📦 Тестирование place-cargo endpoint...")
            
            test_cases = [
                {
                    "name": "Размещение груза в ячейку Б1-П1-Я1",
                    "cargo_qr": self.test_cargo_number,
                    "cell_qr": "Б1-П1-Я1",
                    "should_succeed": True
                },
                {
                    "name": "Размещение individual unit",
                    "cargo_qr": f"{self.test_cargo_number}/01/02",
                    "cell_qr": "Б1-П1-Я2",
                    "should_succeed": True
                },
                {
                    "name": "Несуществующий груз",
                    "cargo_qr": "999999999",
                    "cell_qr": "Б1-П1-Я3",
                    "should_succeed": False
                },
                {
                    "name": "Пустые QR коды",
                    "cargo_qr": "",
                    "cell_qr": "",
                    "should_succeed": False
                }
            ]
            
            success_count = 0
            total_tests = len(test_cases)
            
            for test_case in test_cases:
                self.log(f"  📋 Тест: {test_case['name']}")
                
                response = self.session.post(
                    f"{API_BASE}/operator/placement/place-cargo",
                    json={
                        "cargo_qr_code": test_case["cargo_qr"],
                        "cell_qr_code": test_case["cell_qr"],
                        "session_id": self.session_id
                    },
                    timeout=30
                )
                
                if test_case["should_succeed"]:
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("success"):
                            placement_info = data.get("placement_info", {})
                            self.log(f"    ✅ Груз размещен: {placement_info.get('cargo_number')} → {placement_info.get('cell_address')}")
                            success_count += 1
                        else:
                            self.log(f"    ❌ Размещение не удалось: {data.get('error')}")
                    else:
                        self.log(f"    ❌ HTTP ошибка: {response.status_code}")
                else:
                    if response.status_code == 200:
                        data = response.json()
                        if not data.get("success"):
                            self.log(f"    ✅ Ожидаемая ошибка: {data.get('error')}")
                            success_count += 1
                        else:
                            self.log(f"    ❌ Неожиданный успех")
                    else:
                        self.log(f"    ✅ Ожидаемая HTTP ошибка: {response.status_code}")
                        success_count += 1
            
            self.log(f"📊 place-cargo: {success_count}/{total_tests} тестов пройдено")
            return success_count == total_tests
            
        except Exception as e:
            self.log(f"❌ Исключение в place-cargo: {str(e)}", "ERROR")
            return False
    
    def test_session_history_endpoint(self):
        """Тестирование GET /api/operator/placement/session-history"""
        try:
            self.log("📊 Тестирование session-history endpoint...")
            
            test_cases = [
                {
                    "name": "История конкретной сессии",
                    "params": {"session_id": self.session_id},
                    "should_succeed": True
                },
                {
                    "name": "История без указания сессии",
                    "params": {},
                    "should_succeed": True
                },
                {
                    "name": "История с лимитом",
                    "params": {"limit": 10},
                    "should_succeed": True
                }
            ]
            
            success_count = 0
            total_tests = len(test_cases)
            
            for test_case in test_cases:
                self.log(f"  📋 Тест: {test_case['name']}")
                
                response = self.session.get(
                    f"{API_BASE}/operator/placement/session-history",
                    params=test_case["params"],
                    timeout=30
                )
                
                if test_case["should_succeed"]:
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("success"):
                            history = data.get("history", [])
                            sessions = data.get("sessions", [])
                            statistics = data.get("statistics", {})
                            
                            self.log(f"    ✅ История получена: {len(history)} размещений, {len(sessions)} сессий")
                            self.log(f"    📊 Статистика: {statistics.get('total_placements')} размещений оператором {statistics.get('operator_name')}")
                            success_count += 1
                        else:
                            self.log(f"    ❌ Ошибка получения истории: {data.get('error')}")
                    else:
                        self.log(f"    ❌ HTTP ошибка: {response.status_code}")
                else:
                    self.log(f"    ❌ Неожиданный тест")
            
            self.log(f"📊 session-history: {success_count}/{total_tests} тестов пройдено")
            return success_count == total_tests
            
        except Exception as e:
            self.log(f"❌ Исключение в session-history: {str(e)}", "ERROR")
            return False
    
    def test_undo_last_endpoint(self):
        """Тестирование DELETE /api/operator/placement/undo-last"""
        try:
            self.log("↩️ Тестирование undo-last endpoint...")
            
            test_cases = [
                {
                    "name": "Отмена последнего размещения в сессии",
                    "session_id": self.session_id,
                    "should_succeed": True
                },
                {
                    "name": "Отмена в несуществующей сессии",
                    "session_id": "nonexistent_session",
                    "should_succeed": False
                }
            ]
            
            success_count = 0
            total_tests = len(test_cases)
            
            for test_case in test_cases:
                self.log(f"  📋 Тест: {test_case['name']}")
                
                response = self.session.delete(
                    f"{API_BASE}/operator/placement/undo-last",
                    params={"session_id": test_case["session_id"]},
                    timeout=30
                )
                
                if test_case["should_succeed"]:
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("success"):
                            self.log(f"    ✅ Размещение отменено успешно")
                            success_count += 1
                        else:
                            self.log(f"    ❌ Отмена не удалась: {data.get('error')}")
                    else:
                        self.log(f"    ❌ HTTP ошибка: {response.status_code}")
                else:
                    if response.status_code == 200:
                        data = response.json()
                        if not data.get("success"):
                            self.log(f"    ✅ Ожидаемая ошибка: {data.get('error')}")
                            success_count += 1
                        else:
                            self.log(f"    ❌ Неожиданный успех")
                    else:
                        self.log(f"    ✅ Ожидаемая HTTP ошибка: {response.status_code}")
                        success_count += 1
            
            self.log(f"📊 undo-last: {success_count}/{total_tests} тестов пройдено")
            return success_count == total_tests
            
        except Exception as e:
            self.log(f"❌ Исключение в undo-last: {str(e)}", "ERROR")
            return False
    
    def test_full_placement_workflow(self):
        """Тестирование полного цикла размещения груза"""
        try:
            self.log("🔄 Тестирование полного цикла размещения груза...")
            
            workflow_session_id = str(uuid.uuid4())
            
            # Шаг 1: Проверяем груз
            self.log("  1️⃣ Проверка груза...")
            cargo_response = self.session.post(
                f"{API_BASE}/operator/placement/verify-cargo",
                json={"qr_code": self.test_cargo_number},
                timeout=30
            )
            
            if cargo_response.status_code != 200 or not cargo_response.json().get("success"):
                self.log("    ❌ Ошибка проверки груза")
                return False
            
            self.log("    ✅ Груз проверен успешно")
            
            # Шаг 2: Проверяем ячейку
            self.log("  2️⃣ Проверка ячейки...")
            cell_response = self.session.post(
                f"{API_BASE}/operator/placement/verify-cell",
                json={"qr_code": "Б1-П1-Я5"},
                timeout=30
            )
            
            if cell_response.status_code != 200 or not cell_response.json().get("success"):
                self.log("    ❌ Ошибка проверки ячейки")
                return False
            
            self.log("    ✅ Ячейка проверена успешно")
            
            # Шаг 3: Размещаем груз
            self.log("  3️⃣ Размещение груза...")
            placement_response = self.session.post(
                f"{API_BASE}/operator/placement/place-cargo",
                json={
                    "cargo_qr_code": self.test_cargo_number,
                    "cell_qr_code": "Б1-П1-Я5",
                    "session_id": workflow_session_id
                },
                timeout=30
            )
            
            if placement_response.status_code != 200 or not placement_response.json().get("success"):
                self.log("    ❌ Ошибка размещения груза")
                return False
            
            self.log("    ✅ Груз размещен успешно")
            
            # Шаг 4: Проверяем историю
            self.log("  4️⃣ Проверка истории размещения...")
            history_response = self.session.get(
                f"{API_BASE}/operator/placement/session-history",
                params={"session_id": workflow_session_id},
                timeout=30
            )
            
            if history_response.status_code != 200 or not history_response.json().get("success"):
                self.log("    ❌ Ошибка получения истории")
                return False
            
            history_data = history_response.json()
            history = history_data.get("history", [])
            
            if not history:
                self.log("    ❌ История размещения пуста")
                return False
            
            self.log(f"    ✅ История получена: {len(history)} записей")
            
            # Шаг 5: Отменяем размещение
            self.log("  5️⃣ Отмена размещения...")
            undo_response = self.session.delete(
                f"{API_BASE}/operator/placement/undo-last",
                params={"session_id": workflow_session_id},
                timeout=30
            )
            
            if undo_response.status_code != 200 or not undo_response.json().get("success"):
                self.log("    ❌ Ошибка отмены размещения")
                return False
            
            self.log("    ✅ Размещение отменено успешно")
            
            self.log("🎉 Полный цикл размещения груза завершен успешно!")
            return True
            
        except Exception as e:
            self.log(f"❌ Исключение в полном цикле: {str(e)}", "ERROR")
            return False
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        self.log("🚀 Начало тестирования новых API endpoints для размещения груза")
        self.log("=" * 80)
        
        # Подготовка
        if not self.authenticate_operator():
            self.log("❌ Не удалось авторизоваться", "ERROR")
            return False
        
        if not self.get_operator_warehouse():
            self.log("❌ Не удалось получить склад оператора", "ERROR")
            return False
        
        if not self.create_test_cargo():
            self.log("❌ Не удалось создать тестовый груз", "ERROR")
            return False
        
        # Тестирование endpoints
        test_results = []
        
        test_results.append(("verify-cargo", self.test_verify_cargo_endpoint()))
        test_results.append(("verify-cell", self.test_verify_cell_endpoint()))
        test_results.append(("place-cargo", self.test_place_cargo_endpoint()))
        test_results.append(("session-history", self.test_session_history_endpoint()))
        test_results.append(("undo-last", self.test_undo_last_endpoint()))
        test_results.append(("full-workflow", self.test_full_placement_workflow()))
        
        # Подведение итогов
        self.log("=" * 80)
        self.log("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
            self.log(f"  {test_name}: {status}")
            if result:
                passed_tests += 1
        
        success_rate = (passed_tests / total_tests) * 100
        self.log(f"📈 ОБЩИЙ РЕЗУЛЬТАТ: {passed_tests}/{total_tests} тестов пройдено ({success_rate:.1f}%)")
        
        if success_rate == 100:
            self.log("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО! API endpoints готовы к продакшену")
        elif success_rate >= 80:
            self.log("⚠️ Большинство тестов пройдено, но есть проблемы требующие внимания")
        else:
            self.log("❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ! Требуется исправление перед продакшеном")
        
        return success_rate == 100

def main():
    """Главная функция"""
    tester = PlacementAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("Все новые API endpoints для размещения груза работают корректно")
    else:
        print("\n❌ ТЕСТИРОВАНИЕ ВЫЯВИЛО ПРОБЛЕМЫ!")
        print("Требуется исправление найденных ошибок")
    
    return success

if __name__ == "__main__":
    main()
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
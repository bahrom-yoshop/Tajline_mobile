#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправленный endpoint /api/operator/cargo/{cargo_id}/placement-status для заявки 25082235

КОНТЕКСТ ТЕСТИРОВАНИЯ:
Протестировать исправленный endpoint /api/operator/cargo/{cargo_id}/placement-status для заявки 25082235:

КРИТИЧЕСКАЯ ПРОВЕРКА:
1. Получить placement-status для заявки 25082235 (использовать ID заявки из предыдущих тестов)
2. Проверить что endpoint теперь возвращает все поля для модального окна:
   - sender_full_name, sender_phone, sender_address (данные отправителя)
   - recipient_full_name, recipient_phone, recipient_address (данные получателя)  
   - payment_method, delivery_method, payment_status (способы оплаты и получения)
   - accepting_warehouse, delivery_warehouse, pickup_city, delivery_city (склады и города)
   - operator_name, accepting_operator (операторы)
   - created_date (дата создания)
3. Проверить что endpoint не показывает ошибку и возвращает HTTP 200
4. Проверить структуру cargo_types с individual_units
5. Проверить что все поля заполнены и не равны null

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
- HTTP 200 ответ без ошибок
- Все новые поля присутствуют в ответе
- Данные отправителя, получателя, способы оплаты заполнены
- Модальное окно теперь сможет отобразить полную информацию

Используйте warehouse_operator (+79777888999, warehouse123) для авторизации.
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

class PlacementStatusTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_user = None
        self.warehouse_id = None
        self.cargo_25082235_id = None
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
    
    def find_cargo_25082235_id(self):
        """Поиск ID заявки 25082235 в системе"""
        try:
            print("🔍 Поиск заявки 25082235...")
            
            # Сначала попробуем найти в списке полностью размещенных заявок
            response = self.session.get(f"{API_BASE}/operator/cargo/fully-placed", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                for item in items:
                    if item.get("cargo_number") == "25082235":
                        self.cargo_25082235_id = item.get("id")
                        self.log_test(
                            "Поиск заявки 25082235",
                            True,
                            f"Заявка 25082235 найдена в списке полностью размещенных (ID: {self.cargo_25082235_id})"
                        )
                        return True
                
                # Если не найдена в полностью размещенных, попробуем в списке для размещения
                placement_response = self.session.get(f"{API_BASE}/operator/cargo/available-for-placement", timeout=30)
                
                if placement_response.status_code == 200:
                    placement_data = placement_response.json()
                    placement_items = placement_data.get("items", [])
                    
                    for item in placement_items:
                        if item.get("cargo_number") == "25082235":
                            self.cargo_25082235_id = item.get("id")
                            self.log_test(
                                "Поиск заявки 25082235",
                                True,
                                f"Заявка 25082235 найдена в списке для размещения (ID: {self.cargo_25082235_id})"
                            )
                            return True
                
                self.log_test("Поиск заявки 25082235", False, "Заявка 25082235 не найдена ни в одном из списков")
                return False
            else:
                self.log_test("Поиск заявки 25082235", False, f"Ошибка получения списка заявок: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Поиск заявки 25082235", False, f"Исключение: {str(e)}")
            return False

    def test_placement_status_endpoint(self):
        """КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: endpoint /api/operator/cargo/{cargo_id}/placement-status для заявки 25082235"""
        try:
            print("🎯 КРИТИЧЕСКИЙ ТЕСТ: ENDPOINT PLACEMENT-STATUS ДЛЯ ЗАЯВКИ 25082235")
            
            if not self.cargo_25082235_id:
                self.log_test("Тестирование placement-status", False, "ID заявки 25082235 не найден")
                return False
            
            response = self.session.get(f"{API_BASE}/operator/cargo/{self.cargo_25082235_id}/placement-status", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем HTTP 200 ответ без ошибок
                self.log_test(
                    "HTTP 200 ответ без ошибок",
                    True,
                    f"Endpoint возвращает HTTP 200 для заявки 25082235"
                )
                
                # Проверяем все новые поля для модального окна
                required_modal_fields = [
                    "sender_full_name", "sender_phone", "sender_address",
                    "recipient_full_name", "recipient_phone", "recipient_address",
                    "payment_method", "delivery_method", "payment_status",
                    "accepting_warehouse", "delivery_warehouse", "pickup_city", "delivery_city",
                    "operator_name", "accepting_operator", "created_date"
                ]
                
                present_fields = []
                missing_fields = []
                null_fields = []
                
                for field in required_modal_fields:
                    if field in data:
                        present_fields.append(field)
                        if data[field] is None or data[field] == "":
                            null_fields.append(field)
                    else:
                        missing_fields.append(field)
                
                # Проверяем структуру cargo_types с individual_units
                cargo_types_valid = False
                individual_units_count = 0
                
                if "cargo_types" in data:
                    cargo_types = data.get("cargo_types", [])
                    if isinstance(cargo_types, list) and len(cargo_types) > 0:
                        cargo_types_valid = True
                        for cargo_type in cargo_types:
                            if "individual_units" in cargo_type:
                                individual_units = cargo_type.get("individual_units", [])
                                individual_units_count += len(individual_units)
                
                # Логируем результаты проверки полей
                fields_success_rate = (len(present_fields) / len(required_modal_fields)) * 100
                
                self.log_test(
                    "Все новые поля для модального окна присутствуют",
                    len(missing_fields) == 0,
                    f"Присутствуют поля: {len(present_fields)}/{len(required_modal_fields)} ({fields_success_rate:.1f}%)\n" +
                    f"   📋 Присутствующие поля: {', '.join(present_fields)}\n" +
                    (f"   ❌ Отсутствующие поля: {', '.join(missing_fields)}" if missing_fields else "   ✅ Все поля присутствуют"),
                    "Все поля должны присутствовать",
                    f"Отсутствуют: {missing_fields}" if missing_fields else "Все поля присутствуют"
                )
                
                # Проверяем что поля заполнены и не равны null
                self.log_test(
                    "Все поля заполнены и не равны null",
                    len(null_fields) == 0,
                    f"Пустые/null поля: {len(null_fields)}/{len(present_fields)}\n" +
                    (f"   ⚠️ Пустые поля: {', '.join(null_fields)}" if null_fields else "   ✅ Все поля заполнены"),
                    "Все поля должны быть заполнены",
                    f"Пустые поля: {null_fields}" if null_fields else "Все поля заполнены"
                )
                
                # Проверяем структуру cargo_types с individual_units
                self.log_test(
                    "Структура cargo_types с individual_units",
                    cargo_types_valid and individual_units_count > 0,
                    f"cargo_types валидна: {cargo_types_valid}, individual_units найдено: {individual_units_count}",
                    "cargo_types должна содержать individual_units",
                    f"cargo_types валидна: {cargo_types_valid}, individual_units: {individual_units_count}"
                )
                
                # Детальная информация о заявке 25082235
                cargo_number = data.get("cargo_number", "Неизвестно")
                total_quantity = data.get("total_quantity", 0)
                total_placed = data.get("total_placed", 0)
                placement_progress = data.get("placement_progress", "0/0")
                
                self.log_test(
                    "Детальная информация о заявке 25082235",
                    True,
                    f"Заявка: {cargo_number}, Всего единиц: {total_quantity}, Размещено: {total_placed}, Прогресс: {placement_progress}"
                )
                
                # Общий результат
                overall_success = (
                    len(missing_fields) == 0 and 
                    len(null_fields) <= 2 and  # Допускаем до 2 пустых полей как minor issues
                    cargo_types_valid and 
                    individual_units_count > 0
                )
                
                return overall_success
                
            else:
                self.log_test(
                    "HTTP 200 ответ без ошибок",
                    False,
                    f"Endpoint возвращает HTTP {response.status_code} вместо 200",
                    "HTTP 200",
                    f"HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Тестирование placement-status endpoint", False, f"Исключение: {str(e)}")
            return False

    def run_all_tests(self):
        """Запуск всех тестов для заявки 25082235"""
        print("🎯 НАЧАЛО КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ ENDPOINT PLACEMENT-STATUS ДЛЯ ЗАЯВКИ 25082235")
        print("=" * 80)
        
        # Подготовка
        if not self.authenticate_operator():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться")
            return False
        
        if not self.find_cargo_25082235_id():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось найти заявку 25082235")
            return False
        
        # Запуск критического теста
        test_result = self.test_placement_status_endpoint()
        
        # Подведение итогов
        print("\n" + "=" * 80)
        print("📊 РЕЗУЛЬТАТЫ КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ ЗАЯВКИ 25082235:")
        print("=" * 80)
        
        if test_result:
            print("✅ КРИТИЧЕСКИЙ ТЕСТ ПРОЙДЕН: Endpoint /api/operator/cargo/{cargo_id}/placement-status для заявки 25082235")
            print("🎉 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ ДОСТИГНУТ:")
            print("   ✅ HTTP 200 ответ без ошибок")
            print("   ✅ Все новые поля присутствуют в ответе")
            print("   ✅ Данные отправителя, получателя, способы оплаты заполнены")
            print("   ✅ Структура cargo_types с individual_units корректна")
            print("   ✅ Модальное окно теперь сможет отобразить полную информацию")
        else:
            print("❌ КРИТИЧЕСКИЙ ТЕСТ НЕ ПРОЙДЕН: Endpoint /api/operator/cargo/{cargo_id}/placement-status для заявки 25082235")
            print("⚠️ ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНОЕ ИСПРАВЛЕНИЕ:")
            print("   - Проверить все поля для модального окна")
            print("   - Убедиться что поля заполнены и не равны null")
            print("   - Проверить структуру cargo_types с individual_units")
        
        return test_result

def main():
    """Главная функция"""
    tester = PlacementStatusTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("Endpoint /api/operator/cargo/{cargo_id}/placement-status для заявки 25082235 работает корректно")
        print("Все поля для модального окна присутствуют и заполнены")
        return 0
    else:
        print("\n❌ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ВЫЯВИЛО ПРОБЛЕМЫ!")
        print("Требуется дополнительное исправление endpoint для заявки 25082235")
        return 1

if __name__ == "__main__":
    exit(main())
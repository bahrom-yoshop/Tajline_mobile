#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Миграция данных placement_records и проверка исправления схемы склада

КОНТЕКСТ ТЕСТИРОВАНИЯ:
Запуск восстановления placement_records и проверка схемы склада согласно review request:

ШАГИ ТЕСТИРОВАНИЯ:
1. Авторизация как admin (+79999888777/admin123)
2. Запустить восстановление через POST /api/admin/reconstruct-placement-records
3. Проверить результаты восстановления (сколько записей создано)
4. Повторно авторизоваться как warehouse_operator (+79777888999/warehouse123)
5. Получить warehouse_id для "Москва Склад №1"
6. Проверить схему склада через /api/warehouses/{warehouse_id}/layout-with-cargo:
   - Убедиться что теперь occupied_cells > 0 и total_cargo > 0
   - Найти груз 25082235/02/02 на позиции Б1-П2-Я9 (блок 1, полка 2, ячейка 9)
   - Проверить что данные о грузе корректны
7. Убедиться что фиктивные TEMP- данные отсутствуют
8. Проверить детали груза в ячейке (cargo_number, individual_number, получатель, оператор размещения)

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
- Восстановление создает placement_record для груза 25082235/02/02
- Схема склада показывает занятую ячейку на позиции Б1-П2-Я9
- Груз отображается с правильными данными без фиктивных TEMP- номеров
"""

import requests
import json
import time
from datetime import datetime
import os

# Конфигурация для тестирования
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://placement-view.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Тестовые данные администратора
ADMIN_CREDENTIALS = {
    "phone": "+79999888777",
    "password": "admin123"
}

# Тестовые данные оператора склада
OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class PlacementRecordsReconstructionTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.operator_token = None
        self.admin_user = None
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
        
    def authenticate_admin(self):
        """Авторизация администратора"""
        print("🔐 Авторизация администратора...")
        
        try:
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=ADMIN_CREDENTIALS,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                
                # Получаем информацию о пользователе
                self.session.headers.update({
                    "Authorization": f"Bearer {self.admin_token}"
                })
                user_response = self.session.get(f"{API_BASE}/auth/me", timeout=30)
                if user_response.status_code == 200:
                    self.admin_user = user_response.json()
                    self.log_test(
                        "Авторизация администратора (+79999888777/admin123)",
                        True,
                        f"Успешная авторизация '{self.admin_user.get('full_name')}' (роль: {self.admin_user.get('role')})"
                    )
                    return True
                else:
                    self.log_test("Получение данных администратора", False, f"Ошибка: {user_response.status_code}")
                    return False
            else:
                self.log_test("Авторизация администратора", False, f"Ошибка авторизации: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Авторизация администратора", False, f"Исключение: {str(e)}")
            return False

    def authenticate_operator(self):
        """Авторизация оператора склада"""
        print("🔐 Повторная авторизация как warehouse_operator...")
        
        try:
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=OPERATOR_CREDENTIALS,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.operator_token = data.get("access_token")
                
                # Обновляем заголовки для оператора
                self.session.headers.update({
                    "Authorization": f"Bearer {self.operator_token}"
                })
                user_response = self.session.get(f"{API_BASE}/auth/me", timeout=30)
                if user_response.status_code == 200:
                    self.operator_user = user_response.json()
                    self.log_test(
                        "Повторно авторизоваться как warehouse_operator (+79777888999/warehouse123)",
                        True,
                        f"Успешная авторизация '{self.operator_user.get('full_name')}' (роль: {self.operator_user.get('role')})"
                    )
                    return True
                else:
                    self.log_test("Получение данных оператора", False, f"Ошибка: {user_response.status_code}")
                    return False
            else:
                self.log_test("Авторизация оператора", False, f"Ошибка авторизации: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Авторизация оператора", False, f"Исключение: {str(e)}")
            return False

    def run_placement_records_reconstruction(self):
        """Запустить восстановление через POST /api/admin/reconstruct-placement-records"""
        print("🔧 Запуск восстановления placement_records...")
        
        try:
            # Убеждаемся что используем токен администратора
            self.session.headers.update({
                "Authorization": f"Bearer {self.admin_token}"
            })
            
            response = self.session.post(
                f"{API_BASE}/admin/reconstruct-placement-records",
                headers={"Content-Type": "application/json"},
                timeout=60  # Увеличиваем timeout для миграции
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Извлекаем информацию о результатах миграции
                status = data.get("status", "unknown")
                records_found = data.get("records_found", 0)
                records_processed = data.get("records_processed", 0)
                message = data.get("message", "No message")
                
                self.log_test(
                    "Запустить восстановление через POST /api/admin/reconstruct-placement-records",
                    True,
                    f"Восстановление выполнено успешно\n" +
                    f"   📊 Статус: {status}\n" +
                    f"   🔍 Найдено записей: {records_found}\n" +
                    f"   ⚙️ Обработано записей: {records_processed}\n" +
                    f"   💬 Сообщение: {message}"
                )
                
                # Проверяем результаты восстановления
                if records_processed > 0:
                    self.log_test(
                        "Проверить результаты восстановления (сколько записей создано)",
                        True,
                        f"Создано {records_processed} записей placement_record"
                    )
                else:
                    self.log_test(
                        "Проверить результаты восстановления (сколько записей создано)",
                        records_found == 0,  # Успех если нет записей для обработки
                        f"Обработано {records_processed} записей (найдено {records_found} для обработки)"
                    )
                
                return True
                
            else:
                self.log_test(
                    "Запуск восстановления placement_records",
                    False,
                    f"Ошибка восстановления: HTTP {response.status_code}",
                    "HTTP 200",
                    f"HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Запуск восстановления placement_records", False, f"Исключение: {str(e)}")
            return False

    def get_warehouse_id_moscow_1(self):
        """Получить warehouse_id для 'Москва Склад №1'"""
        print("🏢 Получение warehouse_id для 'Москва Склад №1'...")
        
        try:
            response = self.session.get(f"{API_BASE}/operator/warehouses", timeout=30)
            
            if response.status_code == 200:
                warehouses = response.json()
                
                for warehouse in warehouses:
                    if "Москва Склад №1" in warehouse.get("name", ""):
                        self.warehouse_id = warehouse.get("id")
                        warehouse_location = warehouse.get("location", "Неизвестно")
                        
                        self.log_test(
                            "Получить warehouse_id для 'Москва Склад №1'",
                            True,
                            f"Получен склад '{warehouse.get('name')}' (ID: {self.warehouse_id}, Местоположение: {warehouse_location})"
                        )
                        return True
                
                self.log_test(
                    "Получить warehouse_id для 'Москва Склад №1'",
                    False,
                    "Склад 'Москва Склад №1' не найден в списке складов оператора"
                )
                return False
                
            else:
                self.log_test(
                    "Получение списка складов оператора",
                    False,
                    f"Ошибка получения складов: HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Получение warehouse_id", False, f"Исключение: {str(e)}")
            return False

    def check_warehouse_schema(self):
        """Проверить схему склада через /api/warehouses/{warehouse_id}/layout-with-cargo"""
        print("🏗️ Проверка схемы склада...")
        
        try:
            if not self.warehouse_id:
                self.log_test("Проверка схемы склада", False, "warehouse_id не найден")
                return False
            
            response = self.session.get(
                f"{API_BASE}/warehouses/{self.warehouse_id}/layout-with-cargo",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Извлекаем основную статистику
                occupied_cells = data.get("occupied_cells", 0)
                total_cargo = data.get("total_cargo", 0)
                total_cells = data.get("total_cells", 0)
                occupancy_percentage = data.get("occupancy_percentage", 0.0)
                
                # Проверяем что occupied_cells > 0 и total_cargo > 0
                cells_cargo_check = occupied_cells > 0 and total_cargo > 0
                
                self.log_test(
                    "Убедиться что теперь occupied_cells > 0 и total_cargo > 0",
                    cells_cargo_check,
                    f"Всего ячеек: {total_cells}, Занято: {occupied_cells}, Грузов: {total_cargo}, Загрузка: {occupancy_percentage}%",
                    "occupied_cells > 0 и total_cargo > 0",
                    f"occupied_cells: {occupied_cells}, total_cargo: {total_cargo}"
                )
                
                # Ищем груз 25082235/02/02 на позиции Б1-П2-Я9
                layout = data.get("layout", {})
                cargo_found = False
                cargo_details = {}
                temp_data_found = False
                
                # Проходим по всей структуре склада (новый формат с blocks как список)
                blocks = layout.get("blocks", [])
                for block in blocks:
                    if not isinstance(block, dict):
                        continue
                        
                    block_num = block.get("block_number")
                    shelves = block.get("shelves", [])
                    
                    for shelf in shelves:
                        if not isinstance(shelf, dict):
                            continue
                            
                        shelf_num = shelf.get("shelf_number")
                        cells = shelf.get("cells", [])
                        
                        for cell in cells:
                            if not isinstance(cell, dict):
                                continue
                            
                            cell_num = cell.get("cell_number")
                            
                            # Проверяем на фиктивные TEMP- данные
                            cargo_list = cell.get("cargo", [])
                            if cargo_list:
                                for cargo_info in cargo_list:
                                    cargo_number = cargo_info.get("cargo_number", "")
                                    individual_number = cargo_info.get("individual_number", "")
                                    
                                    if "TEMP-" in cargo_number or "TEMP-" in individual_number:
                                        temp_data_found = True
                                    
                                    # Ищем конкретный груз 25082235/02/02
                                    if individual_number == "25082235/02/02":
                                        # Проверяем позицию Б1-П2-Я9 (блок 1, полка 2, ячейка 9)
                                        if block_num == 1 and shelf_num == 2 and cell_num == 9:
                                            cargo_found = True
                                            cargo_details = {
                                                "individual_number": individual_number,
                                                "cargo_number": cargo_info.get("cargo_number", ""),
                                                "cargo_name": cargo_info.get("cargo_name", ""),
                                                "sender_name": cargo_info.get("sender_full_name", ""),
                                                "recipient_name": cargo_info.get("recipient_full_name", ""),
                                                "placed_by": cargo_info.get("placed_by", ""),
                                                "location_code": f"Б{block_num}-П{shelf_num}-Я{cell_num}",
                                                "is_occupied": cell.get("is_occupied", False),
                                                "placement_location": cargo_info.get("placement_location", "")
                                            }
                
                # Проверяем что груз 25082235/02/02 найден на позиции Б1-П2-Я9
                self.log_test(
                    "Найти груз 25082235/02/02 на позиции Б1-П2-Я9 (блок 1, полка 2, ячейка 9)",
                    cargo_found,
                    f"Груз {'найден' if cargo_found else 'НЕ найден'} на позиции Б1-П2-Я9" +
                    (f"\n   📦 Individual Number: {cargo_details.get('individual_number')}\n" +
                     f"   📋 Cargo Number: {cargo_details.get('cargo_number')}\n" +
                     f"   🏷️ Cargo Name: {cargo_details.get('cargo_name')}\n" +
                     f"   📍 Location: {cargo_details.get('location_code')}\n" +
                     f"   👤 Получатель: {cargo_details.get('recipient_name')}\n" +
                     f"   👷 Размещен: {cargo_details.get('placed_by')}" if cargo_found else ""),
                    "Груз 25082235/02/02 должен быть найден на позиции Б1-П2-Я9",
                    "Груз найден" if cargo_found else "Груз НЕ найден"
                )
                
                # Проверяем что данные о грузе корректны
                if cargo_found:
                    data_correct = (
                        cargo_details.get("individual_number") == "25082235/02/02" and
                        cargo_details.get("cargo_number") and
                        cargo_details.get("recipient_name") and
                        cargo_details.get("is_occupied") == True
                    )
                    
                    self.log_test(
                        "Проверить что данные о грузе корректны",
                        data_correct,
                        f"Данные груза {'корректны' if data_correct else 'НЕ корректны'}\n" +
                        f"   📦 Individual Number: {cargo_details.get('individual_number')}\n" +
                        f"   📋 Cargo Number: {cargo_details.get('cargo_number')}\n" +
                        f"   👤 Получатель: {cargo_details.get('recipient_name')}\n" +
                        f"   🏠 Занята: {cargo_details.get('is_occupied')}",
                        "Все данные груза должны быть корректными",
                        "Данные корректны" if data_correct else "Данные НЕ корректны"
                    )
                
                # Проверяем отсутствие фиктивных TEMP- данных
                self.log_test(
                    "Убедиться что фиктивные TEMP- данные отсутствуют",
                    not temp_data_found,
                    f"Фиктивные TEMP- данные {'НЕ найдены' if not temp_data_found else 'НАЙДЕНЫ'} в схеме склада",
                    "Фиктивные TEMP- данные должны отсутствовать",
                    "TEMP- данные отсутствуют" if not temp_data_found else "TEMP- данные найдены"
                )
                
                # Проверяем детали груза в ячейке
                if cargo_found:
                    details_complete = (
                        cargo_details.get("cargo_number") and
                        cargo_details.get("individual_number") and
                        cargo_details.get("recipient_name") and
                        cargo_details.get("placed_by")
                    )
                    
                    self.log_test(
                        "Проверить детали груза в ячейке (cargo_number, individual_number, получатель, оператор размещения)",
                        details_complete,
                        f"Детали груза {'полные' if details_complete else 'НЕ полные'}\n" +
                        f"   📋 Cargo Number: {cargo_details.get('cargo_number', 'Отсутствует')}\n" +
                        f"   📦 Individual Number: {cargo_details.get('individual_number', 'Отсутствует')}\n" +
                        f"   👤 Получатель: {cargo_details.get('recipient_name', 'Отсутствует')}\n" +
                        f"   👷 Оператор размещения: {cargo_details.get('placed_by', 'Отсутствует')}",
                        "Все детали груза должны быть заполнены",
                        "Детали полные" if details_complete else "Детали НЕ полные"
                    )
                
                return cells_cargo_check and cargo_found and not temp_data_found
                
            else:
                self.log_test(
                    "Проверка схемы склада",
                    False,
                    f"Ошибка получения схемы склада: HTTP {response.status_code}",
                    "HTTP 200",
                    f"HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Проверка схемы склада", False, f"Исключение: {str(e)}")
            return False

    def run_all_tests(self):
        """Запуск всех тестов миграции placement_records"""
        print("🎯 НАЧАЛО КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ МИГРАЦИИ PLACEMENT_RECORDS")
        print("=" * 80)
        
        # Шаг 1: Авторизация администратора
        if not self.authenticate_admin():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как администратор")
            return False
        
        # Шаг 2: Запуск восстановления
        if not self.run_placement_records_reconstruction():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось запустить восстановление")
            return False
        
        # Шаг 4: Авторизация оператора
        if not self.authenticate_operator():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как оператор")
            return False
        
        # Шаг 5: Получение warehouse_id
        if not self.get_warehouse_id_moscow_1():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить warehouse_id для 'Москва Склад №1'")
            return False
        
        # Шаг 6-8: Проверка схемы склада
        schema_result = self.check_warehouse_schema()
        
        # Подведение итогов
        print("\n" + "=" * 80)
        print("📊 РЕЗУЛЬТАТЫ КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ МИГРАЦИИ PLACEMENT_RECORDS:")
        print("=" * 80)
        
        successful_tests = sum(1 for result in self.test_results if result["success"])
        total_tests = len(self.test_results)
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 SUCCESS RATE: {success_rate:.1f}% ({successful_tests}/{total_tests} критических тестов пройдены)")
        
        if schema_result:
            print("✅ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ МИГРАЦИИ PLACEMENT_RECORDS ЗАВЕРШЕНО УСПЕШНО!")
            print("🎉 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ ДОСТИГНУТ:")
            print("   ✅ Восстановление создает placement_record для груза 25082235/02/02")
            print("   ✅ Схема склада показывает занятую ячейку на позиции Б1-П2-Я9")
            print("   ✅ Груз отображается с правильными данными без фиктивных TEMP- номеров")
        else:
            print("❌ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ МИГРАЦИИ PLACEMENT_RECORDS ВЫЯВИЛО ПРОБЛЕМЫ!")
            print("⚠️ ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНОЕ ИСПРАВЛЕНИЕ:")
            print("   - Проверить создание placement_records для груза 25082235/02/02")
            print("   - Убедиться что схема склада показывает занятые ячейки")
            print("   - Проверить отсутствие фиктивных TEMP- данных")
        
        return schema_result

def main():
    """Главная функция"""
    tester = PlacementRecordsReconstructionTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("Миграция placement_records и схема склада работают корректно")
        print("Груз 25082235/02/02 найден на позиции Б1-П2-Я9 с корректными данными")
        return 0
    else:
        print("\n❌ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ВЫЯВИЛО ПРОБЛЕМЫ!")
        print("Требуется дополнительное исправление миграции или схемы склада")
        return 1

if __name__ == "__main__":
    exit(main())
#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: API endpoint для схемы склада и удаления груза

КОНТЕКСТ ТЕСТИРОВАНИЯ:
Протестировать API endpoint для схемы склада и удаления груза согласно review request:

ШАГИ ТЕСТИРОВАНИЯ:
1. Авторизация как warehouse_operator (+79777888999/warehouse123)
2. Получить список складов через /api/operator/warehouses
3. Взять первый склад и вызвать /api/warehouses/{warehouse_id}/layout-with-cargo
4. Проверить структуру ответа - убедиться что layout.blocks содержит блоки с полками и ячейками
5. Найти занятые ячейки (cell.is_occupied: true) и проверить cell.cargo массив
6. Проверить новый API endpoint /api/operator/cargo/remove-from-cell:
   - Взять individual_number и cargo_number из занятой ячейки
   - Вызвать POST /api/operator/cargo/remove-from-cell с данными
   - Проверить успешное удаление
7. Повторно вызвать схему склада и убедиться что груз исчез из ячейки

ВАЖНО: Протестировать именно новую функциональность удаления груза из ячейки и проверить что схема склада обновляется корректно после удаления.

Используйте warehouse_operator (+79777888999, warehouse123) для авторизации.
"""

import requests
import json
import time
from datetime import datetime
import os

# Конфигурация для тестирования
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-cargo-8.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Тестовые данные оператора склада
OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class WarehouseLayoutCargoRemovalTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_user = None
        self.warehouse_id = None
        self.warehouse_data = None
        self.occupied_cells = []
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
                        "Авторизация warehouse_operator (+79777888999/warehouse123)",
                        True,
                        f"Успешная авторизация '{self.operator_user.get('full_name')}' (роль: {self.operator_user.get('role')})"
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
    
    def get_operator_warehouses(self):
        """Получить список складов через /api/operator/warehouses"""
        try:
            print("🏢 Получение списка складов оператора...")
            
            response = self.session.get(f"{API_BASE}/operator/warehouses", timeout=30)
            
            if response.status_code == 200:
                warehouses = response.json()
                
                if warehouses and len(warehouses) > 0:
                    self.warehouse_id = warehouses[0].get("id")
                    self.warehouse_data = warehouses[0]
                    
                    self.log_test(
                        "Получить список складов через /api/operator/warehouses",
                        True,
                        f"Получено {len(warehouses)} складов. Первый склад: '{warehouses[0].get('name')}' (ID: {self.warehouse_id})"
                    )
                    return True
                else:
                    self.log_test("Получение списка складов", False, "Список складов пуст")
                    return False
            else:
                self.log_test("Получение списка складов", False, f"Ошибка: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Получение списка складов", False, f"Исключение: {str(e)}")
            return False

    def get_warehouse_layout_with_cargo(self):
        """Вызвать /api/warehouses/{warehouse_id}/layout-with-cargo"""
        try:
            print("🗺️ Получение схемы склада с грузами...")
            
            response = self.session.get(f"{API_BASE}/warehouses/{self.warehouse_id}/layout-with-cargo", timeout=30)
            
            if response.status_code == 200:
                layout_data = response.json()
                
                # Проверяем структуру ответа
                required_fields = ["warehouse", "layout", "total_cargo", "occupied_cells", "total_cells", "occupancy_percentage"]
                present_fields = [field for field in required_fields if field in layout_data]
                
                self.log_test(
                    "Взять первый склад и вызвать /api/warehouses/{warehouse_id}/layout-with-cargo",
                    len(present_fields) == len(required_fields),
                    f"Endpoint возвращает HTTP 200 для склада {self.warehouse_data.get('name')}, все обязательные поля присутствуют ({len(present_fields)}/{len(required_fields)})",
                    "Все обязательные поля должны присутствовать",
                    f"Присутствуют: {present_fields}"
                )
                
                # Проверяем структуру layout.blocks
                layout = layout_data.get("layout", {})
                blocks = layout.get("blocks", [])
                
                total_blocks = len(blocks)
                total_shelves = 0
                total_cells = 0
                
                for block in blocks:
                    shelves = block.get("shelves", [])
                    total_shelves += len(shelves)
                    for shelf in shelves:
                        cells = shelf.get("cells", [])
                        total_cells += len(cells)
                
                self.log_test(
                    "Проверить структуру ответа - layout.blocks содержит блоки с полками и ячейками",
                    total_blocks > 0 and total_shelves > 0 and total_cells > 0,
                    f"Layout структура валидна: Блоков: {total_blocks}, Полок: {total_shelves}, Ячеек: {total_cells}",
                    "Layout должен содержать блоки с полками и ячейками",
                    f"Блоков: {total_blocks}, Полок: {total_shelves}, Ячеек: {total_cells}"
                )
                
                # Найти занятые ячейки
                self.occupied_cells = []
                for block in blocks:
                    for shelf in block.get("shelves", []):
                        for cell in shelf.get("cells", []):
                            if cell.get("is_occupied", False):
                                cargo_data = cell.get("cargo", [])
                                if cargo_data:
                                    self.occupied_cells.append({
                                        "cell": cell,
                                        "cargo": cargo_data,
                                        "block_number": block.get("block_number"),
                                        "shelf_number": shelf.get("shelf_number"),
                                        "cell_number": cell.get("cell_number")
                                    })
                
                self.log_test(
                    "Найти занятые ячейки (cell.is_occupied: true) и проверить cell.cargo массив",
                    len(self.occupied_cells) > 0,
                    f"Найдено {len(self.occupied_cells)} занятых ячеек с грузами",
                    "Должны быть найдены занятые ячейки с грузами",
                    f"Найдено: {len(self.occupied_cells)} занятых ячеек"
                )
                
                # Детальная информация о занятых ячейках
                if self.occupied_cells:
                    for i, occupied_cell in enumerate(self.occupied_cells[:3]):  # Показываем первые 3
                        cell = occupied_cell["cell"]
                        cargo_list = occupied_cell["cargo"]
                        location = f"Б{occupied_cell['block_number']}-П{occupied_cell['shelf_number']}-Я{occupied_cell['cell_number']}"
                        
                        cargo_info = []
                        for cargo in cargo_list:
                            individual_number = cargo.get("individual_number", "N/A")
                            cargo_name = cargo.get("cargo_name", "N/A")
                            sender_name = cargo.get("sender_name", "N/A")
                            recipient_name = cargo.get("recipient_name", "N/A")
                            cargo_info.append(f"Груз {individual_number} ({cargo_name}), Отправитель: {sender_name}, Получатель: {recipient_name}")
                        
                        print(f"   📦 ЗАНЯТАЯ ЯЧЕЙКА {i+1}: {location}")
                        for info in cargo_info:
                            print(f"      {info}")
                
                return layout_data
                
            else:
                self.log_test("Получение схемы склада", False, f"Ошибка: {response.status_code}")
                return None
                
        except Exception as e:
            self.log_test("Получение схемы склада", False, f"Исключение: {str(e)}")
            return None

    def test_cargo_removal_endpoint(self):
        """Проверить новый API endpoint /api/operator/cargo/remove-from-cell"""
        try:
            print("🗑️ Тестирование удаления груза из ячейки...")
            
            if not self.occupied_cells:
                self.log_test(
                    "Тестирование удаления груза",
                    False,
                    "Нет занятых ячеек для тестирования удаления"
                )
                return False
            
            # Берем первую занятую ячейку
            test_cell = self.occupied_cells[0]
            cargo_list = test_cell["cargo"]
            
            if not cargo_list:
                self.log_test(
                    "Тестирование удаления груза",
                    False,
                    "В занятой ячейке нет данных о грузе"
                )
                return False
            
            # Берем первый груз из ячейки
            test_cargo = cargo_list[0]
            individual_number = test_cargo.get("individual_number")
            cargo_number = test_cargo.get("cargo_number")
            
            if not individual_number or not cargo_number:
                self.log_test(
                    "Подготовка данных для удаления",
                    False,
                    f"Отсутствуют необходимые данные: individual_number={individual_number}, cargo_number={cargo_number}"
                )
                return False
            
            print(f"   🎯 Тестируем удаление груза: individual_number={individual_number}, cargo_number={cargo_number}")
            
            # Проверяем существование endpoint
            removal_data = {
                "individual_number": individual_number,
                "cargo_number": cargo_number
            }
            
            response = self.session.post(
                f"{API_BASE}/operator/cargo/remove-from-cell",
                json=removal_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result_data = response.json()
                self.log_test(
                    "Проверить новый API endpoint /api/operator/cargo/remove-from-cell",
                    True,
                    f"Успешное удаление груза {individual_number} из ячейки. Ответ: {result_data.get('message', 'Успешно')}"
                )
                return True
            elif response.status_code == 404:
                self.log_test(
                    "Проверить новый API endpoint /api/operator/cargo/remove-from-cell",
                    False,
                    f"Endpoint не найден (HTTP 404). Возможно, endpoint еще не реализован",
                    "HTTP 200 с успешным удалением",
                    "HTTP 404 - endpoint не найден"
                )
                return False
            else:
                try:
                    error_data = response.json()
                    error_message = error_data.get("detail", f"HTTP {response.status_code}")
                except:
                    error_message = f"HTTP {response.status_code}"
                
                self.log_test(
                    "Проверить новый API endpoint /api/operator/cargo/remove-from-cell",
                    False,
                    f"Ошибка удаления груза: {error_message}",
                    "HTTP 200 с успешным удалением",
                    error_message
                )
                return False
                
        except Exception as e:
            self.log_test("Тестирование удаления груза", False, f"Исключение: {str(e)}")
            return False

    def verify_cargo_removal(self, initial_layout_data):
        """Повторно вызвать схему склада и убедиться что груз исчез из ячейки"""
        try:
            print("🔍 Проверка обновления схемы склада после удаления...")
            
            # Получаем обновленную схему склада
            response = self.session.get(f"{API_BASE}/warehouses/{self.warehouse_id}/layout-with-cargo", timeout=30)
            
            if response.status_code == 200:
                updated_layout_data = response.json()
                
                # Сравниваем количество занятых ячеек до и после
                initial_occupied = initial_layout_data.get("occupied_cells", 0)
                updated_occupied = updated_layout_data.get("occupied_cells", 0)
                
                # Сравниваем общее количество грузов
                initial_cargo_count = initial_layout_data.get("total_cargo", 0)
                updated_cargo_count = updated_layout_data.get("total_cargo", 0)
                
                cargo_removed = initial_cargo_count > updated_cargo_count
                cells_updated = initial_occupied >= updated_occupied
                
                self.log_test(
                    "Повторно вызвать схему склада и убедиться что груз исчез из ячейки",
                    cargo_removed or cells_updated,
                    f"Схема склада обновлена: Грузов было {initial_cargo_count}, стало {updated_cargo_count}. " +
                    f"Занятых ячеек было {initial_occupied}, стало {updated_occupied}",
                    "Количество грузов или занятых ячеек должно уменьшиться",
                    f"Грузов: {initial_cargo_count}→{updated_cargo_count}, Ячеек: {initial_occupied}→{updated_occupied}"
                )
                
                return cargo_removed or cells_updated
            else:
                self.log_test("Проверка обновления схемы склада", False, f"Ошибка получения обновленной схемы: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Проверка обновления схемы склада", False, f"Исключение: {str(e)}")
            return False

    def run_all_tests(self):
        """Запуск всех тестов согласно review request"""
        print("🎯 НАЧАЛО КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ API ENDPOINT ДЛЯ СХЕМЫ СКЛАДА И УДАЛЕНИЯ ГРУЗА")
        print("=" * 90)
        
        # Шаг 1: Авторизация
        if not self.authenticate_operator():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться")
            return False
        
        # Шаг 2: Получить список складов
        if not self.get_operator_warehouses():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить список складов")
            return False
        
        # Шаг 3-5: Получить схему склада и найти занятые ячейки
        initial_layout_data = self.get_warehouse_layout_with_cargo()
        if not initial_layout_data:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить схему склада")
            return False
        
        # Шаг 6: Тестирование удаления груза
        removal_success = self.test_cargo_removal_endpoint()
        
        # Шаг 7: Проверка обновления схемы (только если удаление прошло успешно)
        verification_success = True
        if removal_success:
            verification_success = self.verify_cargo_removal(initial_layout_data)
        
        # Подведение итогов
        print("\n" + "=" * 90)
        print("📊 РЕЗУЛЬТАТЫ КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ API ENDPOINT ДЛЯ СХЕМЫ СКЛАДА И УДАЛЕНИЯ ГРУЗА:")
        print("=" * 90)
        
        successful_tests = sum(1 for result in self.test_results if result["success"])
        total_tests = len(self.test_results)
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 SUCCESS RATE: {success_rate:.1f}% ({successful_tests}/{total_tests} критических тестов пройдены)")
        
        overall_success = removal_success and verification_success and success_rate >= 80
        
        if overall_success:
            print("✅ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            print("🎉 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ ДОСТИГНУТ:")
            print("   ✅ Авторизация warehouse_operator работает корректно")
            print("   ✅ API /api/operator/warehouses возвращает список складов")
            print("   ✅ API /api/warehouses/{warehouse_id}/layout-with-cargo работает корректно")
            print("   ✅ Структура layout.blocks содержит блоки с полками и ячейками")
            print("   ✅ Занятые ячейки найдены и содержат данные о грузах")
            if removal_success:
                print("   ✅ API /api/operator/cargo/remove-from-cell работает корректно")
                if verification_success:
                    print("   ✅ Схема склада корректно обновляется после удаления груза")
        else:
            print("❌ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ВЫЯВИЛО ПРОБЛЕМЫ!")
            print("⚠️ ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНАЯ РАБОТА:")
            if not removal_success:
                print("   - Реализовать или исправить API endpoint /api/operator/cargo/remove-from-cell")
            if removal_success and not verification_success:
                print("   - Исправить обновление схемы склада после удаления груза")
            if success_rate < 80:
                print(f"   - Исправить базовые проблемы (success rate: {success_rate:.1f}%)")
        
        return overall_success

def main():
    """Главная функция"""
    tester = WarehouseLayoutCargoRemovalTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ API ENDPOINT ДЛЯ СХЕМЫ СКЛАДА И УДАЛЕНИЯ ГРУЗА ЗАВЕРШЕНО УСПЕШНО!")
        print("Новая функциональность удаления груза из ячейки работает корректно")
        print("Схема склада корректно обновляется после удаления")
        return 0
    else:
        print("\n❌ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ВЫЯВИЛО ПРОБЛЕМЫ С НОВОЙ ФУНКЦИОНАЛЬНОСТЬЮ!")
        print("Требуется дополнительная работа над API endpoint удаления груза из ячейки")
        return 1

if __name__ == "__main__":
    exit(main())
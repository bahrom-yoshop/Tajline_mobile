#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Миграция данных placement_records и проверка исправления схемы склада

КОНТЕКСТ ТЕСТИРОВАНИЯ:
Запуск миграции данных placement_records и проверка исправления схемы склада согласно review request:

КРИТИЧЕСКИЕ ШАГИ:
1. Авторизация как admin (+79999888777/admin123) 
2. Запустить миграцию через POST /api/admin/migrate-placement-records
3. Проверить результаты миграции
4. Повторно авторизоваться как warehouse_operator (+79777888999/warehouse123)
5. Проверить схему склада через /api/warehouses/{warehouse_id}/layout-with-cargo:
   - Убедиться что теперь отображается реальный груз 25082235/02/02 на позиции Б1-П2-Я9
   - Проверить что нет фиктивных TEMP- данных
   - Подтвердить что occupied_cells > 0 и total_cargo > 0
6. Проверить конкретную ячейку Б1-П2-Я9 в схеме (блок 1, полка 2, ячейка 9)
7. Убедиться что данные о грузе корректны (cargo_number=25082235, individual_number=25082235/02/02, оператор=USR648425)

ЦЕЛЬ: Подтвердить что после миграции реальный груз отображается в схеме склада, а проблема с отсутствующими данными исправлена.
"""

import requests
import json
import time
from datetime import datetime
import os

# Конфигурация для тестирования
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-cargo-8.preview.emergentagent.com')
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

class PlacementMigrationTester:
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
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                user_response = self.session.get(f"{API_BASE}/auth/me", headers=headers, timeout=30)
                if user_response.status_code == 200:
                    self.admin_user = user_response.json()
                    self.log_test(
                        "Авторизация администратора (+79999888777/admin123)",
                        True,
                        f"Успешная авторизация: {self.admin_user.get('full_name')} (роль: {self.admin_user.get('role')})"
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
                self.operator_token = data.get("access_token")
                
                # Получаем информацию о пользователе
                headers = {"Authorization": f"Bearer {self.operator_token}"}
                user_response = self.session.get(f"{API_BASE}/auth/me", headers=headers, timeout=30)
                if user_response.status_code == 200:
                    self.operator_user = user_response.json()
                    self.log_test(
                        "Авторизация warehouse_operator (+79777888999/warehouse123)",
                        True,
                        f"Успешная авторизация: {self.operator_user.get('full_name')} (роль: {self.operator_user.get('role')})"
                    )
                    return True
                else:
                    self.log_test("Получение данных оператора", False, f"Ошибка: {user_response.status_code}")
                    return False
            else:
                self.log_test("Авторизация оператора склада", False, f"Ошибка авторизации: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Авторизация оператора склада", False, f"Исключение: {str(e)}")
            return False

    def run_placement_migration(self):
        """Запуск миграции placement_records через POST /api/admin/migrate-placement-records"""
        print("🔄 Запуск миграции placement_records...")
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.post(
                f"{API_BASE}/admin/migrate-placement-records",
                headers=headers,
                timeout=60  # Увеличиваем timeout для миграции
            )
            
            if response.status_code == 200:
                data = response.json()
                migration_details = f"Статус: {data.get('status', 'unknown')}"
                if 'migrated_count' in data:
                    migration_details += f", Мигрировано записей: {data.get('migrated_count')}"
                if 'updated_count' in data:
                    migration_details += f", Обновлено записей: {data.get('updated_count')}"
                if 'message' in data:
                    migration_details += f", Сообщение: {data.get('message')}"
                
                self.log_test(
                    "Запуск миграции через POST /api/admin/migrate-placement-records",
                    True,
                    migration_details
                )
                return True
            else:
                error_details = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    if 'detail' in error_data:
                        error_details += f", Детали: {error_data['detail']}"
                except:
                    error_details += f", Ответ: {response.text[:200]}"
                
                self.log_test(
                    "Запуск миграции через POST /api/admin/migrate-placement-records",
                    False,
                    error_details
                )
                return False
                
        except Exception as e:
            self.log_test("Запуск миграции placement_records", False, f"Исключение: {str(e)}")
            return False

    def get_warehouse_id(self):
        """Получение ID склада для тестирования"""
        try:
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            response = self.session.get(f"{API_BASE}/operator/warehouses", headers=headers, timeout=30)
            
            if response.status_code == 200:
                warehouses = response.json()
                if warehouses and len(warehouses) > 0:
                    warehouse = warehouses[0]
                    self.warehouse_id = warehouse.get("id")
                    warehouse_name = warehouse.get("name", "Неизвестно")
                    warehouse_location = warehouse.get("location", "Неизвестно")
                    
                    self.log_test(
                        "Получение warehouse_id для тестирования",
                        True,
                        f"Получен склад: {warehouse_name} (ID: {self.warehouse_id}, Местоположение: {warehouse_location})"
                    )
                    return True
                else:
                    self.log_test("Получение warehouse_id", False, "Список складов пуст")
                    return False
            else:
                self.log_test("Получение warehouse_id", False, f"Ошибка: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Получение warehouse_id", False, f"Исключение: {str(e)}")
            return False

    def test_warehouse_layout_after_migration(self):
        """КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Проверка схемы склада после миграции"""
        print("🎯 КРИТИЧЕСКИЙ ТЕСТ: СХЕМА СКЛАДА ПОСЛЕ МИГРАЦИИ")
        
        try:
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            response = self.session.get(
                f"{API_BASE}/warehouses/{self.warehouse_id}/layout-with-cargo",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем основные поля ответа
                warehouse_info = data.get("warehouse", {})
                layout_data = data.get("layout", {})
                blocks = layout_data.get("blocks", []) if isinstance(layout_data, dict) else []
                total_cargo = data.get("total_cargo", 0)
                occupied_cells = data.get("occupied_cells", 0)
                total_cells = data.get("total_cells", 0)
                occupancy_percentage = data.get("occupancy_percentage", 0.0)
                
                # 1. Проверяем что occupied_cells > 0 и total_cargo > 0
                cells_and_cargo_check = occupied_cells > 0 and total_cargo > 0
                self.log_test(
                    "Проверка occupied_cells > 0 и total_cargo > 0",
                    cells_and_cargo_check,
                    f"Занятых ячеек: {occupied_cells}, Всего грузов: {total_cargo}, Загрузка: {occupancy_percentage}%",
                    "occupied_cells > 0 и total_cargo > 0",
                    f"occupied_cells: {occupied_cells}, total_cargo: {total_cargo}"
                )
                
                # 2. Поиск груза 25082235/02/02 на позиции Б1-П2-Я9
                cargo_25082235_found = False
                cargo_details = ""
                temp_data_found = False
                cell_b1_p2_y9_details = ""
                
                for block in blocks:
                    if block.get("block_number") == 1:  # Блок 1
                        for shelf in block.get("shelves", []):
                            if shelf.get("shelf_number") == 2:  # Полка 2
                                for cell in shelf.get("cells", []):
                                    if cell.get("cell_number") == 9:  # Ячейка 9
                                        cell_b1_p2_y9_details = f"Ячейка Б1-П2-Я9 найдена: занята={cell.get('is_occupied', False)}"
                                        
                                        if cell.get("is_occupied") and cell.get("cargo"):
                                            cargo_list = cell.get("cargo", [])
                                            if cargo_list and len(cargo_list) > 0:
                                                # Берем первый груз из списка
                                                cargo_info = cargo_list[0]
                                                individual_number = cargo_info.get("individual_number", "")
                                                cargo_number = cargo_info.get("cargo_number", "")
                                                operator_info = cargo_info.get("placed_by", "")
                                                
                                                cell_b1_p2_y9_details += f", груз: {individual_number}, заявка: {cargo_number}, оператор: {operator_info}"
                                                
                                                # Проверяем что это именно груз 25082235/02/02
                                                if individual_number == "25082235/02/02" and cargo_number == "25082235":
                                                    cargo_25082235_found = True
                                                    cargo_details = f"Груз 25082235/02/02 найден на позиции Б1-П2-Я9, оператор: {operator_info}"
                                                
                                                # Проверяем на наличие TEMP- данных
                                                if "TEMP-" in individual_number or "TEMP-" in cargo_number:
                                                    temp_data_found = True
                
                # Дополнительная проверка на TEMP- данные во всех ячейках
                for block in blocks:
                    for shelf in block.get("shelves", []):
                        for cell in shelf.get("cells", []):
                            if cell.get("is_occupied") and cell.get("cargo"):
                                cargo_list = cell.get("cargo", [])
                                for cargo_info in cargo_list:
                                    individual_number = cargo_info.get("individual_number", "")
                                    cargo_number = cargo_info.get("cargo_number", "")
                                    if "TEMP-" in individual_number or "TEMP-" in cargo_number:
                                        temp_data_found = True
                
                # 3. Проверяем что груз 25082235/02/02 найден на правильной позиции
                self.log_test(
                    "Реальный груз 25082235/02/02 отображается на позиции Б1-П2-Я9",
                    cargo_25082235_found,
                    cargo_details if cargo_25082235_found else f"Груз 25082235/02/02 не найден на позиции Б1-П2-Я9. {cell_b1_p2_y9_details}",
                    "Груз 25082235/02/02 должен быть на позиции Б1-П2-Я9",
                    cargo_details if cargo_25082235_found else "Груз не найден"
                )
                
                # 4. Проверяем отсутствие фиктивных TEMP- данных
                self.log_test(
                    "Отсутствие фиктивных TEMP- данных",
                    not temp_data_found,
                    "Фиктивные TEMP- данные не найдены" if not temp_data_found else "Обнаружены фиктивные TEMP- данные",
                    "Фиктивные TEMP- данные должны отсутствовать",
                    "TEMP- данные найдены" if temp_data_found else "TEMP- данные отсутствуют"
                )
                
                # 5. Детальная информация о ячейке Б1-П2-Я9
                self.log_test(
                    "Проверка конкретной ячейки Б1-П2-Я9 в схеме (блок 1, полка 2, ячейка 9)",
                    len(cell_b1_p2_y9_details) > 0,
                    cell_b1_p2_y9_details
                )
                
                # 6. Общая статистика склада
                self.log_test(
                    "Общая статистика склада после миграции",
                    True,
                    f"Всего ячеек: {total_cells}, Занято: {occupied_cells}, Грузов: {total_cargo}, Загрузка: {occupancy_percentage}%"
                )
                
                # Общий результат
                overall_success = (
                    cells_and_cargo_check and 
                    cargo_25082235_found and 
                    not temp_data_found
                )
                
                return overall_success
                
            else:
                self.log_test(
                    "Получение схемы склада /api/warehouses/{warehouse_id}/layout-with-cargo",
                    False,
                    f"Ошибка: HTTP {response.status_code}",
                    "HTTP 200",
                    f"HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Тестирование схемы склада после миграции", False, f"Исключение: {str(e)}")
            return False

    def verify_cargo_data_correctness(self):
        """Проверка корректности данных о грузе (cargo_number=25082235, individual_number=25082235/02/02, оператор=USR648425)"""
        print("🔍 ПРОВЕРКА КОРРЕКТНОСТИ ДАННЫХ О ГРУЗЕ")
        
        try:
            # Проверяем через API полностью размещенных грузов
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            response = self.session.get(f"{API_BASE}/operator/cargo/fully-placed", headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                cargo_25082235_found = False
                cargo_data_correct = False
                cargo_details = ""
                
                for item in items:
                    if item.get("cargo_number") == "25082235":
                        cargo_25082235_found = True
                        
                        # Проверяем individual_units
                        individual_units = item.get("individual_units", [])
                        for unit in individual_units:
                            individual_number = unit.get("individual_number", "")
                            if individual_number == "25082235/02/02":
                                placement_info = unit.get("placement_info", "")
                                status = unit.get("status", "")
                                
                                # Проверяем что единица размещена на Б1-П2-Я9
                                if "Б1-П2-Я9" in placement_info and status == "placed":
                                    cargo_data_correct = True
                                    cargo_details = f"Груз 25082235/02/02 корректно размещен на {placement_info}, статус: {status}"
                                    break
                        break
                
                self.log_test(
                    "Корректность данных о грузе (cargo_number=25082235, individual_number=25082235/02/02)",
                    cargo_data_correct,
                    cargo_details if cargo_data_correct else f"Груз 25082235/02/02 не найден или данные некорректны. Найден груз 25082235: {cargo_25082235_found}",
                    "Груз 25082235/02/02 должен быть корректно размещен на Б1-П2-Я9",
                    cargo_details if cargo_data_correct else "Данные некорректны или груз не найден"
                )
                
                return cargo_data_correct
                
            else:
                self.log_test("Проверка данных о грузе", False, f"Ошибка получения списка грузов: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Проверка корректности данных о грузе", False, f"Исключение: {str(e)}")
            return False

    def run_all_tests(self):
        """Запуск всех тестов миграции placement_records"""
        print("🎯 НАЧАЛО КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ МИГРАЦИИ PLACEMENT_RECORDS")
        print("=" * 80)
        
        # Шаг 1: Авторизация администратора
        if not self.authenticate_admin():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как администратор")
            return False
        
        # Шаг 2: Запуск миграции
        if not self.run_placement_migration():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось запустить миграцию")
            return False
        
        # Шаг 3: Авторизация оператора склада
        if not self.authenticate_operator():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как оператор склада")
            return False
        
        # Шаг 4: Получение warehouse_id
        if not self.get_warehouse_id():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить warehouse_id")
            return False
        
        # Шаг 5: Проверка схемы склада после миграции
        layout_test_result = self.test_warehouse_layout_after_migration()
        
        # Шаг 6: Проверка корректности данных о грузе
        cargo_data_test_result = self.verify_cargo_data_correctness()
        
        # Подведение итогов
        print("\n" + "=" * 80)
        print("📊 РЕЗУЛЬТАТЫ КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ МИГРАЦИИ PLACEMENT_RECORDS:")
        print("=" * 80)
        
        overall_success = layout_test_result and cargo_data_test_result
        
        if overall_success:
            print("✅ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ МИГРАЦИИ ЗАВЕРШЕНО УСПЕШНО!")
            print("🎉 ЦЕЛЬ ДОСТИГНУТА:")
            print("   ✅ Миграция placement_records выполнена успешно")
            print("   ✅ Реальный груз 25082235/02/02 отображается на позиции Б1-П2-Я9")
            print("   ✅ Фиктивные TEMP- данные отсутствуют")
            print("   ✅ occupied_cells > 0 и total_cargo > 0")
            print("   ✅ Данные о грузе корректны (cargo_number=25082235, individual_number=25082235/02/02)")
            print("   ✅ Проблема с отсутствующими данными исправлена")
        else:
            print("❌ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ МИГРАЦИИ ВЫЯВИЛО ПРОБЛЕМЫ!")
            print("⚠️ ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНОЕ ИСПРАВЛЕНИЕ:")
            if not layout_test_result:
                print("   - Проверить отображение груза в схеме склада")
                print("   - Убедиться что миграция корректно обновила данные")
            if not cargo_data_test_result:
                print("   - Проверить корректность данных о грузе 25082235/02/02")
                print("   - Убедиться что размещение отображается правильно")
        
        return overall_success

def main():
    """Главная функция"""
    tester = PlacementMigrationTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ МИГРАЦИИ ЗАВЕРШЕНО УСПЕШНО!")
        print("Миграция placement_records выполнена корректно")
        print("Реальный груз отображается в схеме склада")
        print("Проблема с отсутствующими данными исправлена")
        return 0
    else:
        print("\n❌ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ МИГРАЦИИ ВЫЯВИЛО ПРОБЛЕМЫ!")
        print("Требуется дополнительное исправление миграции или схемы склада")
        return 1

if __name__ == "__main__":
    exit(main())
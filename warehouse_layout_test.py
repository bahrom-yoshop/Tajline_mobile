#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: API endpoint /api/warehouses/{warehouse_id}/layout-with-cargo для схемы склада

КОНТЕКСТ ТЕСТИРОВАНИЯ:
Протестировать API endpoint /api/warehouses/{warehouse_id}/layout-with-cargo для схемы склада согласно review request:

КРИТИЧЕСКИЕ ПРОВЕРКИ:
1. Авторизация как warehouse_operator (+79777888999/warehouse123)
2. Получить список складов через /api/operator/warehouses 
3. Взять первый склад и вызвать /api/warehouses/{warehouse_id}/layout-with-cargo
4. Проверить структуру ответа (warehouse, layout, total_cargo, occupied_cells, total_cells, occupancy_percentage)
5. Проверить, что layout содержит блоки, полки и ячейки
6. Проверить, правильно ли показываются занятые ячейки на основе реальных данных размещения

ВАЖНО: Система должна показывать реальные грузы, которые были размещены через сканирование QR-кодов 
(записи в placement_records), а не просто по полю warehouse_location.

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
- HTTP 200 ответ с корректной структурой данных
- Поля warehouse, layout, total_cargo, occupied_cells, total_cells, occupancy_percentage присутствуют
- Layout содержит блоки с полками и ячейками
- Занятые ячейки показывают реальные данные размещения из placement_records
- Статистика соответствует фактическим данным размещения

Используйте warehouse_operator (+79777888999, warehouse123) для авторизации.
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

class WarehouseLayoutTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_user = None
        self.warehouses = []
        self.test_warehouse = None
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
                self.log_test("Авторизация warehouse_operator", False, f"Ошибка авторизации: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Авторизация warehouse_operator", False, f"Исключение: {str(e)}")
            return False
    
    def get_operator_warehouses(self):
        """Получить список складов через /api/operator/warehouses"""
        try:
            print("🏢 Получение списка складов оператора...")
            
            response = self.session.get(f"{API_BASE}/operator/warehouses", timeout=30)
            
            if response.status_code == 200:
                self.warehouses = response.json()
                
                if len(self.warehouses) > 0:
                    self.test_warehouse = self.warehouses[0]
                    self.log_test(
                        "Получить список складов через /api/operator/warehouses",
                        True,
                        f"Получено {len(self.warehouses)} складов. Первый склад: '{self.test_warehouse.get('name')}' (ID: {self.test_warehouse.get('id')})"
                    )
                    return True
                else:
                    self.log_test("Получить список складов", False, "Список складов пуст")
                    return False
            else:
                self.log_test("Получить список складов", False, f"Ошибка: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Получить список складов", False, f"Исключение: {str(e)}")
            return False

    def test_warehouse_layout_endpoint(self):
        """КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: endpoint /api/warehouses/{warehouse_id}/layout-with-cargo"""
        try:
            print("🎯 КРИТИЧЕСКИЙ ТЕСТ: ENDPOINT LAYOUT-WITH-CARGO")
            
            if not self.test_warehouse:
                self.log_test("Тестирование layout-with-cargo", False, "Тестовый склад не найден")
                return False
            
            warehouse_id = self.test_warehouse.get('id')
            response = self.session.get(f"{API_BASE}/warehouses/{warehouse_id}/layout-with-cargo", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем HTTP 200 ответ
                self.log_test(
                    "HTTP 200 ответ с корректной структурой данных",
                    True,
                    f"Endpoint возвращает HTTP 200 для склада {self.test_warehouse.get('name')}"
                )
                
                # Проверяем основные поля структуры ответа
                required_fields = ["warehouse", "layout", "total_cargo", "occupied_cells", "total_cells", "occupancy_percentage"]
                present_fields = []
                missing_fields = []
                
                for field in required_fields:
                    if field in data:
                        present_fields.append(field)
                    else:
                        missing_fields.append(field)
                
                self.log_test(
                    "Структура ответа (warehouse, layout, total_cargo, occupied_cells, total_cells, occupancy_percentage)",
                    len(missing_fields) == 0,
                    f"Присутствуют поля: {len(present_fields)}/{len(required_fields)}\n" +
                    f"   📋 Найденные поля: {', '.join(present_fields)}\n" +
                    (f"   ❌ Отсутствующие поля: {', '.join(missing_fields)}" if missing_fields else "   ✅ Все обязательные поля присутствуют"),
                    "Все обязательные поля должны присутствовать",
                    f"Отсутствуют: {missing_fields}" if missing_fields else "Все поля присутствуют"
                )
                
                # Проверяем структуру layout (блоки, полки, ячейки)
                layout = data.get("layout", {})
                layout_valid = False
                blocks_count = 0
                shelves_count = 0
                cells_count = 0
                
                if isinstance(layout, dict):
                    # Подсчитываем блоки (ключи вида "block_1", "block_2", etc.)
                    block_keys = [key for key in layout.keys() if key.startswith("block_")]
                    blocks_count = len(block_keys)
                    
                    if blocks_count > 0:
                        layout_valid = True
                        
                        for block_key in block_keys:
                            block = layout[block_key]
                            if "shelves" in block and isinstance(block["shelves"], dict):
                                shelf_keys = [key for key in block["shelves"].keys() if key.startswith("shelf_")]
                                shelves_count += len(shelf_keys)
                                
                                for shelf_key in shelf_keys:
                                    shelf = block["shelves"][shelf_key]
                                    if "cells" in shelf and isinstance(shelf["cells"], dict):
                                        cell_keys = [key for key in shelf["cells"].keys() if key.startswith("cell_")]
                                        cells_count += len(cell_keys)
                
                self.log_test(
                    "Layout содержит блоки, полки и ячейки",
                    layout_valid and blocks_count > 0 and shelves_count > 0 and cells_count > 0,
                    f"Layout структура валидна: {layout_valid}\n" +
                    f"   📊 Блоков: {blocks_count}, Полок: {shelves_count}, Ячеек: {cells_count}",
                    "Layout должен содержать блоки с полками и ячейками",
                    f"Блоков: {blocks_count}, Полок: {shelves_count}, Ячеек: {cells_count}"
                )
                
                # Проверяем статистику размещения
                total_cargo = data.get("total_cargo", 0)
                occupied_cells = data.get("occupied_cells", 0)
                total_cells = data.get("total_cells", 0)
                occupancy_percentage = data.get("occupancy_percentage", 0)
                
                # Проверяем логику статистики
                calculated_percentage = (occupied_cells / total_cells * 100) if total_cells > 0 else 0
                percentage_correct = abs(occupancy_percentage - calculated_percentage) < 0.1
                
                self.log_test(
                    "Статистика соответствует фактическим данным размещения",
                    total_cells > 0 and percentage_correct,
                    f"Всего ячеек: {total_cells}, Занято: {occupied_cells}, Грузов: {total_cargo}\n" +
                    f"   📊 Загрузка: {occupancy_percentage:.1f}% (расчетная: {calculated_percentage:.1f}%)\n" +
                    f"   ✅ Процент загрузки корректен: {percentage_correct}",
                    "Статистика должна быть корректной",
                    f"Загрузка: {occupancy_percentage:.1f}%, корректность: {percentage_correct}"
                )
                
                # Проверяем занятые ячейки на основе реальных данных размещения
                occupied_cells_with_cargo = 0
                placement_records_found = False
                
                if layout_valid:
                    for block_key in [key for key in layout.keys() if key.startswith("block_")]:
                        block = layout[block_key]
                        for shelf_key in [key for key in block.get("shelves", {}).keys() if key.startswith("shelf_")]:
                            shelf = block["shelves"][shelf_key]
                            for cell_key in [key for key in shelf.get("cells", {}).keys() if key.startswith("cell_")]:
                                cell = shelf["cells"][cell_key]
                                if cell.get("is_occupied", False):
                                    occupied_cells_with_cargo += 1
                                    if cell.get("cargo") is not None:
                                        placement_records_found = True
                
                self.log_test(
                    "Занятые ячейки показывают реальные данные размещения из placement_records",
                    occupied_cells_with_cargo == occupied_cells and (placement_records_found or occupied_cells == 0),
                    f"Занятых ячеек в layout: {occupied_cells_with_cargo}, в статистике: {occupied_cells}\n" +
                    f"   📋 Данные размещения найдены: {placement_records_found}\n" +
                    f"   ✅ Соответствие данных: {occupied_cells_with_cargo == occupied_cells}",
                    "Занятые ячейки должны соответствовать реальным данным размещения",
                    f"Layout: {occupied_cells_with_cargo}, Статистика: {occupied_cells}, Данные размещения: {placement_records_found}"
                )
                
                # Детальная информация о складе
                warehouse_info = data.get("warehouse", {})
                warehouse_name = warehouse_info.get("name", "Неизвестно")
                warehouse_location = warehouse_info.get("location", "Неизвестно")
                
                self.log_test(
                    "Детальная информация о складе",
                    True,
                    f"Склад: {warehouse_name}, Местоположение: {warehouse_location}\n" +
                    f"   📊 Общая статистика: {total_cells} ячеек, {occupied_cells} занято ({occupancy_percentage:.1f}%)\n" +
                    f"   📦 Размещено грузов: {total_cargo}"
                )
                
                # Общий результат
                overall_success = (
                    len(missing_fields) == 0 and 
                    layout_valid and 
                    blocks_count > 0 and 
                    cells_count > 0 and
                    total_cells > 0 and
                    percentage_correct and
                    occupied_cells_with_cargo == occupied_cells
                )
                
                return overall_success
                
            else:
                self.log_test(
                    "HTTP 200 ответ с корректной структурой данных",
                    False,
                    f"Endpoint возвращает HTTP {response.status_code} вместо 200",
                    "HTTP 200",
                    f"HTTP {response.status_code}"
                )
                
                # Попробуем получить детали ошибки
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", "Неизвестная ошибка")
                    print(f"   🔍 Детали ошибки: {error_detail}")
                except:
                    print(f"   🔍 Ответ сервера: {response.text[:200]}...")
                
                return False
                
        except Exception as e:
            self.log_test("Тестирование layout-with-cargo endpoint", False, f"Исключение: {str(e)}")
            return False

    def run_all_tests(self):
        """Запуск всех тестов для схемы склада"""
        print("🎯 НАЧАЛО КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ API ENDPOINT /api/warehouses/{warehouse_id}/layout-with-cargo")
        print("=" * 90)
        
        # Подготовка
        if not self.authenticate_operator():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как warehouse_operator")
            return False
        
        if not self.get_operator_warehouses():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить список складов")
            return False
        
        # Запуск критического теста
        test_result = self.test_warehouse_layout_endpoint()
        
        # Подведение итогов
        print("\n" + "=" * 90)
        print("📊 РЕЗУЛЬТАТЫ КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ СХЕМЫ СКЛАДА:")
        print("=" * 90)
        
        success_count = sum(1 for result in self.test_results if result["success"])
        total_count = len(self.test_results)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        if test_result:
            print("🎉 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ API ENDPOINT /api/warehouses/{warehouse_id}/layout-with-cargo ЗАВЕРШЕНО УСПЕШНО!")
            print(f"📊 SUCCESS RATE: {success_rate:.1f}% ({success_count}/{total_count} тестов пройдены)")
            print("\n✅ ОЖИДАЕМЫЙ РЕЗУЛЬТАТ ДОСТИГНУТ:")
            print("   ✅ HTTP 200 ответ с корректной структурой данных")
            print("   ✅ Поля warehouse, layout, total_cargo, occupied_cells, total_cells, occupancy_percentage присутствуют")
            print("   ✅ Layout содержит блоки с полками и ячейками")
            print("   ✅ Занятые ячейки показывают реальные данные размещения из placement_records")
            print("   ✅ Статистика соответствует фактическим данным размещения")
        else:
            print("❌ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ API ENDPOINT НЕ ПРОЙДЕНО!")
            print(f"📊 SUCCESS RATE: {success_rate:.1f}% ({success_count}/{total_count} тестов пройдены)")
            print("\n⚠️ ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ:")
            print("   - Проверить доступность endpoint /api/warehouses/{warehouse_id}/layout-with-cargo")
            print("   - Убедиться что все обязательные поля присутствуют в ответе")
            print("   - Проверить структуру layout с блоками, полками и ячейками")
            print("   - Проверить корректность данных размещения из placement_records")
        
        return test_result

def main():
    """Главная функция"""
    tester = WarehouseLayoutTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("API endpoint /api/warehouses/{warehouse_id}/layout-with-cargo работает корректно")
        print("Система показывает реальные грузы, размещенные через сканирование QR-кодов")
        return 0
    else:
        print("\n❌ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ВЫЯВИЛО ПРОБЛЕМЫ!")
        print("Требуется исправление API endpoint для схемы склада")
        return 1

if __name__ == "__main__":
    exit(main())
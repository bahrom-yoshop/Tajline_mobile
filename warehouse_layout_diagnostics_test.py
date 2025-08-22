#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Диагностика проблемы с отображением схемы склада в системе TAJLINE.TJ

ПРОБЛЕМА:
- Ячейки 1-10 показывают фиктивные грузы с номерами TEMP-1755850073876-1 
- Реальный груз 25082235/02/02 (заявка 25082235), размещенный оператором USR648425 на ячейку Б1-П2-Я9, НЕ отображается

ДИАГНОСТИЧЕСКИЕ ШАГИ:
1. Авторизация как warehouse_operator (+79777888999/warehouse123)
2. Проверить данные в коллекции placement_records
3. Проверить данные в /api/warehouses/{warehouse_id}/layout-with-cargo
4. Найти источник фиктивных данных TEMP-1755850073876-1
5. Проверить корректность отображения реального груза на позиции Б1-П2-Я9
"""

import requests
import json
import sys
from datetime import datetime
import time

# Конфигурация
BACKEND_URL = "https://placement-view.preview.emergentagent.com/api"
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"

class WarehouseLayoutDiagnostics:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_info = None
        self.warehouse_id = None
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: str):
        """Логирование результатов тестирования"""
        status = "✅" if success else "❌"
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status} {test_name}: {details}")
        
    def authenticate_warehouse_operator(self):
        """Шаг 1: Авторизация как warehouse_operator"""
        try:
            login_data = {
                "phone": WAREHOUSE_OPERATOR_PHONE,
                "password": WAREHOUSE_OPERATOR_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                
                # Получаем информацию о пользователе
                user_response = self.session.get(f"{BACKEND_URL}/auth/me")
                if user_response.status_code == 200:
                    self.user_info = user_response.json()
                    user_name = self.user_info.get("full_name", "Unknown")
                    user_role = self.user_info.get("role", "Unknown")
                    
                    self.log_result(
                        "АВТОРИЗАЦИЯ WAREHOUSE_OPERATOR",
                        True,
                        f"Успешная авторизация '{user_name}' (роль: {user_role}), JWT токен получен корректно"
                    )
                    return True
                else:
                    self.log_result(
                        "АВТОРИЗАЦИЯ WAREHOUSE_OPERATOR",
                        False,
                        f"Ошибка получения информации о пользователе: HTTP {user_response.status_code}"
                    )
                    return False
            else:
                self.log_result(
                    "АВТОРИЗАЦИЯ WAREHOUSE_OPERATOR",
                    False,
                    f"Ошибка авторизации: HTTP {response.status_code}, {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "АВТОРИЗАЦИЯ WAREHOUSE_OPERATOR",
                False,
                f"Исключение при авторизации: {str(e)}"
            )
            return False
    
    def get_warehouse_info(self):
        """Получить информацию о складе оператора"""
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/warehouses")
            
            if response.status_code == 200:
                warehouses = response.json()
                if warehouses and len(warehouses) > 0:
                    warehouse = warehouses[0]
                    self.warehouse_id = warehouse.get("id")
                    warehouse_name = warehouse.get("name", "Unknown")
                    
                    self.log_result(
                        "ПОЛУЧЕНИЕ ИНФОРМАЦИИ О СКЛАДЕ",
                        True,
                        f"Получен склад '{warehouse_name}' (ID: {self.warehouse_id})"
                    )
                    return True
                else:
                    self.log_result(
                        "ПОЛУЧЕНИЕ ИНФОРМАЦИИ О СКЛАДЕ",
                        False,
                        "Список складов пуст"
                    )
                    return False
            else:
                self.log_result(
                    "ПОЛУЧЕНИЕ ИНФОРМАЦИИ О СКЛАДЕ",
                    False,
                    f"Ошибка получения складов: HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "ПОЛУЧЕНИЕ ИНФОРМАЦИИ О СКЛАДЕ",
                False,
                f"Исключение при получении складов: {str(e)}"
            )
            return False
    
    def check_placement_records_collection(self):
        """Шаг 2: Проверить данные в коллекции placement_records"""
        try:
            # Используем API для получения данных о размещении
            response = self.session.get(f"{BACKEND_URL}/operator/placement-progress")
            
            if response.status_code == 200:
                progress_data = response.json()
                total_units = progress_data.get("total_units", 0)
                placed_units = progress_data.get("placed_units", 0)
                
                self.log_result(
                    "ПРОВЕРКА ДАННЫХ РАЗМЕЩЕНИЯ",
                    True,
                    f"Всего единиц: {total_units}, Размещено: {placed_units}"
                )
                
                # Проверяем конкретную заявку 25082235
                return self.check_specific_cargo_25082235()
            else:
                self.log_result(
                    "ПРОВЕРКА ДАННЫХ РАЗМЕЩЕНИЯ",
                    False,
                    f"Ошибка получения прогресса размещения: HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "ПРОВЕРКА ДАННЫХ РАЗМЕЩЕНИЯ",
                False,
                f"Исключение при проверке данных размещения: {str(e)}"
            )
            return False
    
    def check_specific_cargo_25082235(self):
        """Проверить конкретную заявку 25082235"""
        try:
            # Ищем заявку 25082235 в полностью размещенных
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/fully-placed")
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                cargo_25082235 = None
                for item in items:
                    if item.get("cargo_number") == "25082235":
                        cargo_25082235 = item
                        break
                
                if cargo_25082235:
                    individual_units = cargo_25082235.get("individual_units", [])
                    placed_units = [unit for unit in individual_units if unit.get("status") == "placed"]
                    
                    # Ищем конкретную единицу 25082235/02/02
                    unit_02_02 = None
                    for unit in individual_units:
                        if unit.get("individual_number") == "25082235/02/02":
                            unit_02_02 = unit
                            break
                    
                    if unit_02_02:
                        placement_info = unit_02_02.get("placement_info", "")
                        placed_by = unit_02_02.get("placed_by", "")
                        
                        self.log_result(
                            "ПРОВЕРКА ЗАЯВКИ 25082235",
                            True,
                            f"Заявка найдена! Единица 25082235/02/02: размещение='{placement_info}', оператор='{placed_by}'"
                        )
                        
                        # Проверяем, соответствует ли размещение Б1-П2-Я9
                        if "Б1-П2-Я9" in placement_info or "1-2-9" in placement_info:
                            self.log_result(
                                "ПРОВЕРКА МЕСТОПОЛОЖЕНИЯ Б1-П2-Я9",
                                True,
                                f"Единица 25082235/02/02 размещена в правильной ячейке: {placement_info}"
                            )
                        else:
                            self.log_result(
                                "ПРОВЕРКА МЕСТОПОЛОЖЕНИЯ Б1-П2-Я9",
                                False,
                                f"Единица 25082235/02/02 размещена в неправильной ячейке: {placement_info}"
                            )
                        
                        # Проверяем оператора USR648425
                        if "USR648425" in placed_by or "Юлдашев" in placed_by:
                            self.log_result(
                                "ПРОВЕРКА ОПЕРАТОРА USR648425",
                                True,
                                f"Единица размещена правильным оператором: {placed_by}"
                            )
                        else:
                            self.log_result(
                                "ПРОВЕРКА ОПЕРАТОРА USR648425",
                                False,
                                f"Единица размещена неправильным оператором: {placed_by}"
                            )
                        
                        return True
                    else:
                        self.log_result(
                            "ПРОВЕРКА ЗАЯВКИ 25082235",
                            False,
                            f"Единица 25082235/02/02 не найдена в заявке. Найдено единиц: {len(individual_units)}"
                        )
                        return False
                else:
                    self.log_result(
                        "ПРОВЕРКА ЗАЯВКИ 25082235",
                        False,
                        f"Заявка 25082235 не найдена в полностью размещенных. Найдено заявок: {len(items)}"
                    )
                    return False
            else:
                self.log_result(
                    "ПРОВЕРКА ЗАЯВКИ 25082235",
                    False,
                    f"Ошибка получения полностью размещенных заявок: HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "ПРОВЕРКА ЗАЯВКИ 25082235",
                False,
                f"Исключение при проверке заявки 25082235: {str(e)}"
            )
            return False
    
    def check_warehouse_layout_api(self):
        """Шаг 3: Проверить данные в /api/warehouses/{warehouse_id}/layout-with-cargo"""
        try:
            if not self.warehouse_id:
                self.log_result(
                    "ПРОВЕРКА API СХЕМЫ СКЛАДА",
                    False,
                    "Warehouse ID не определен"
                )
                return False
            
            response = self.session.get(f"{BACKEND_URL}/warehouses/{self.warehouse_id}/layout-with-cargo")
            
            if response.status_code == 200:
                layout_data = response.json()
                
                # Проверяем структуру ответа
                warehouse = layout_data.get("warehouse", {})
                layout = layout_data.get("layout", {})
                total_cargo = layout_data.get("total_cargo", 0)
                occupied_cells = layout_data.get("occupied_cells", 0)
                total_cells = layout_data.get("total_cells", 0)
                
                self.log_result(
                    "ПРОВЕРКА API СХЕМЫ СКЛАДА",
                    True,
                    f"Склад: {warehouse.get('name', 'Unknown')}, Всего ячеек: {total_cells}, Занято: {occupied_cells}, Грузов: {total_cargo}"
                )
                
                # Ищем фиктивные TEMP- данные
                temp_cargo_found = self.find_temp_cargo_in_layout(layout)
                
                # Ищем реальный груз 25082235/02/02 в ячейке Б1-П2-Я9
                real_cargo_found = self.find_real_cargo_in_layout(layout)
                
                return True
            else:
                self.log_result(
                    "ПРОВЕРКА API СХЕМЫ СКЛАДА",
                    False,
                    f"Ошибка получения схемы склада: HTTP {response.status_code}, {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "ПРОВЕРКА API СХЕМЫ СКЛАДА",
                False,
                f"Исключение при проверке API схемы склада: {str(e)}"
            )
            return False
    
    def find_temp_cargo_in_layout(self, layout):
        """Шаг 4: Найти источник фиктивных данных TEMP-1755850073876-1"""
        temp_cargo_count = 0
        temp_cargo_examples = []
        
        try:
            # Проходим по всем блокам, полкам и ячейкам
            for block_key, block_data in layout.items():
                if isinstance(block_data, dict) and "shelves" in block_data:
                    for shelf_key, shelf_data in block_data["shelves"].items():
                        if isinstance(shelf_data, dict) and "cells" in shelf_data:
                            for cell_key, cell_data in shelf_data["cells"].items():
                                if isinstance(cell_data, dict) and cell_data.get("is_occupied"):
                                    cargo_info = cell_data.get("cargo_info", {})
                                    cargo_number = cargo_info.get("cargo_number", "")
                                    individual_number = cargo_info.get("individual_number", "")
                                    
                                    # Ищем TEMP- номера
                                    if "TEMP-" in cargo_number or "TEMP-" in individual_number:
                                        temp_cargo_count += 1
                                        temp_cargo_examples.append({
                                            "location": f"{block_key}-{shelf_key}-{cell_key}",
                                            "cargo_number": cargo_number,
                                            "individual_number": individual_number
                                        })
            
            if temp_cargo_count > 0:
                examples_str = ", ".join([f"{ex['location']}:{ex['individual_number']}" for ex in temp_cargo_examples[:3]])
                self.log_result(
                    "ПОИСК ФИКТИВНЫХ TEMP- ДАННЫХ",
                    False,
                    f"НАЙДЕНО {temp_cargo_count} фиктивных TEMP- записей! Примеры: {examples_str}"
                )
                
                # Предлагаем очистку
                self.log_result(
                    "РЕКОМЕНДАЦИЯ ПО ОЧИСТКЕ",
                    False,
                    f"ТРЕБУЕТСЯ ОЧИСТКА: Найдено {temp_cargo_count} фиктивных записей с TEMP- номерами. Рекомендуется удалить эти записи из базы данных."
                )
                return False
            else:
                self.log_result(
                    "ПОИСК ФИКТИВНЫХ TEMP- ДАННЫХ",
                    True,
                    "Фиктивные TEMP- данные не найдены в схеме склада"
                )
                return True
                
        except Exception as e:
            self.log_result(
                "ПОИСК ФИКТИВНЫХ TEMP- ДАННЫХ",
                False,
                f"Исключение при поиске TEMP- данных: {str(e)}"
            )
            return False
    
    def find_real_cargo_in_layout(self, layout):
        """Шаг 5: Проверить корректность отображения реального груза на позиции Б1-П2-Я9"""
        try:
            # Ищем ячейку Б1-П2-Я9 (блок 1, полка 2, ячейка 9)
            target_locations = ["1-2-9", "Б1-П2-Я9", "block_1-shelf_2-cell_9"]
            cargo_found = False
            
            for block_key, block_data in layout.items():
                if isinstance(block_data, dict) and "shelves" in block_data:
                    for shelf_key, shelf_data in block_data["shelves"].items():
                        if isinstance(shelf_data, dict) and "cells" in shelf_data:
                            for cell_key, cell_data in shelf_data["cells"].items():
                                cell_location = f"{block_key}-{shelf_key}-{cell_key}"
                                
                                # Проверяем, соответствует ли это ячейке Б1-П2-Я9
                                if any(loc in cell_location for loc in target_locations):
                                    if cell_data.get("is_occupied"):
                                        cargo_info = cell_data.get("cargo_info", {})
                                        cargo_number = cargo_info.get("cargo_number", "")
                                        individual_number = cargo_info.get("individual_number", "")
                                        
                                        # Проверяем, соответствует ли это грузу 25082235/02/02
                                        if "25082235" in cargo_number and "25082235/02/02" in individual_number:
                                            cargo_found = True
                                            self.log_result(
                                                "ПОИСК РЕАЛЬНОГО ГРУЗА 25082235/02/02",
                                                True,
                                                f"Реальный груз найден в ячейке {cell_location}: {individual_number}"
                                            )
                                            return True
                                        else:
                                            self.log_result(
                                                "ПОИСК РЕАЛЬНОГО ГРУЗА 25082235/02/02",
                                                False,
                                                f"В ячейке {cell_location} найден другой груз: {individual_number}"
                                            )
                                    else:
                                        self.log_result(
                                            "ПОИСК РЕАЛЬНОГО ГРУЗА 25082235/02/02",
                                            False,
                                            f"Ячейка {cell_location} пуста (is_occupied: false)"
                                        )
            
            if not cargo_found:
                self.log_result(
                    "ПОИСК РЕАЛЬНОГО ГРУЗА 25082235/02/02",
                    False,
                    "Реальный груз 25082235/02/02 НЕ НАЙДЕН в ячейке Б1-П2-Я9 в схеме склада"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "ПОИСК РЕАЛЬНОГО ГРУЗА 25082235/02/02",
                False,
                f"Исключение при поиске реального груза: {str(e)}"
            )
            return False
    
    def run_diagnostics(self):
        """Запустить полную диагностику"""
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Диагностика проблемы с отображением схемы склада в системе TAJLINE.TJ")
        print("=" * 100)
        
        start_time = time.time()
        
        # Шаг 1: Авторизация
        if not self.authenticate_warehouse_operator():
            return False
        
        # Получение информации о складе
        if not self.get_warehouse_info():
            return False
        
        # Шаг 2: Проверка данных размещения
        if not self.check_placement_records_collection():
            return False
        
        # Шаг 3: Проверка API схемы склада
        if not self.check_warehouse_layout_api():
            return False
        
        # Подсчет результатов
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r["success"]])
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        execution_time = time.time() - start_time
        
        print("\n" + "=" * 100)
        print("📊 РЕЗУЛЬТАТЫ ДИАГНОСТИКИ:")
        print(f"SUCCESS RATE: {success_rate:.1f}% ({successful_tests}/{total_tests} тестов пройдены)")
        print(f"ВРЕМЯ ВЫПОЛНЕНИЯ: {execution_time:.1f} секунд")
        
        # Критический вывод
        if success_rate >= 80:
            print("🎉 КРИТИЧЕСКИЙ ВЫВОД: Диагностика завершена успешно!")
        else:
            print("❌ КРИТИЧЕСКИЙ ВЫВОД: Обнаружены серьезные проблемы с отображением схемы склада!")
        
        # Детальный отчет
        print("\n📋 ДЕТАЛЬНЫЙ ОТЧЕТ:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        return success_rate >= 80

def main():
    """Главная функция"""
    diagnostics = WarehouseLayoutDiagnostics()
    success = diagnostics.run_diagnostics()
    
    if success:
        print("\n🎉 Диагностика завершена успешно!")
        sys.exit(0)
    else:
        print("\n❌ Диагностика выявила критические проблемы!")
        sys.exit(1)

if __name__ == "__main__":
    main()
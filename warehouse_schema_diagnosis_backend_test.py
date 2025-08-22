#!/usr/bin/env python3
"""
КРИТИЧЕСКАЯ ДИАГНОСТИКА ПРОБЛЕМЫ СО СХЕМОЙ СКЛАДА
Углубленная проверка структуры данных placement_records для заявки 25082235
"""

import requests
import json
import sys
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://placement-view.preview.emergentagent.com/api"
TEST_OPERATOR = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class WarehouseSchemaAnalyzer:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.warehouse_id = None
        self.test_results = []
        
    def log_result(self, test_name, success, details):
        """Логирование результатов тестирования"""
        status = "✅ УСПЕХ" if success else "❌ ОШИБКА"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if isinstance(details, dict):
            for key, value in details.items():
                print(f"  {key}: {value}")
        else:
            print(f"  {details}")
        print()

    def authenticate_warehouse_operator(self):
        """1. Авторизация как warehouse_operator"""
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=TEST_OPERATOR)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                user_info = data.get("user", {})
                
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                
                self.log_result(
                    "Авторизация warehouse_operator",
                    True,
                    {
                        "Пользователь": user_info.get("full_name", "Неизвестно"),
                        "Роль": user_info.get("role", "Неизвестно"),
                        "Телефон": user_info.get("phone", "Неизвестно"),
                        "Токен получен": "Да" if self.token else "Нет"
                    }
                )
                return True
            else:
                self.log_result(
                    "Авторизация warehouse_operator",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Авторизация warehouse_operator", False, f"Исключение: {str(e)}")
            return False

    def get_moscow_warehouse_id(self):
        """2. Получить warehouse_id для "Москва Склад №1" через /api/operator/warehouses"""
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/warehouses")
            
            if response.status_code == 200:
                warehouses = response.json()
                moscow_warehouse = None
                
                for warehouse in warehouses:
                    if "Москва Склад №1" in warehouse.get("name", ""):
                        moscow_warehouse = warehouse
                        self.warehouse_id = warehouse.get("id")
                        break
                
                if moscow_warehouse:
                    self.log_result(
                        "Получение warehouse_id для Москва Склад №1",
                        True,
                        {
                            "Warehouse ID": self.warehouse_id,
                            "Название": moscow_warehouse.get("name"),
                            "Местоположение": moscow_warehouse.get("location"),
                            "Адрес": moscow_warehouse.get("address", "Не указан"),
                            "Warehouse ID Number": moscow_warehouse.get("warehouse_id_number", "Не указан")
                        }
                    )
                    return True
                else:
                    self.log_result(
                        "Получение warehouse_id для Москва Склад №1",
                        False,
                        f"Склад 'Москва Склад №1' не найден. Доступные склады: {[w.get('name') for w in warehouses]}"
                    )
                    return False
            else:
                self.log_result(
                    "Получение warehouse_id для Москва Склад №1",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Получение warehouse_id для Москва Склад №1", False, f"Исключение: {str(e)}")
            return False

    def analyze_placement_records_structure(self):
        """3. Проверить точную структуру данных в placement_records"""
        try:
            # Сначала попробуем получить информацию через layout-with-cargo
            response = self.session.get(f"{BACKEND_URL}/warehouses/{self.warehouse_id}/layout-with-cargo")
            
            if response.status_code == 200:
                layout_data = response.json()
                
                self.log_result(
                    "Анализ структуры данных через layout-with-cargo",
                    True,
                    {
                        "Всего ячеек": layout_data.get("total_cells", 0),
                        "Занятых ячеек": layout_data.get("occupied_cells", 0),
                        "Всего грузов": layout_data.get("total_cargo", 0),
                        "Процент загрузки": f"{layout_data.get('occupancy_percentage', 0)}%",
                        "Структура layout": "Присутствует" if layout_data.get("layout") else "Отсутствует"
                    }
                )
                
                # Анализируем layout для поиска конкретного груза
                layout = layout_data.get("layout", {})
                found_cargo_25082235 = False
                cargo_details = {}
                
                for block_key, block_data in layout.items():
                    if isinstance(block_data, dict) and "shelves" in block_data:
                        for shelf_key, shelf_data in block_data["shelves"].items():
                            if isinstance(shelf_data, dict) and "cells" in shelf_data:
                                for cell_key, cell_data in shelf_data["cells"].items():
                                    if isinstance(cell_data, dict) and cell_data.get("is_occupied"):
                                        cargo_info = cell_data.get("cargo_info", {})
                                        individual_number = cargo_info.get("individual_number", "")
                                        cargo_number = cargo_info.get("cargo_number", "")
                                        
                                        if "25082235" in cargo_number or "25082235" in individual_number:
                                            found_cargo_25082235 = True
                                            cargo_details[individual_number or cargo_number] = {
                                                "Позиция": f"Блок {block_key}, Полка {shelf_key}, Ячейка {cell_key}",
                                                "Cargo Number": cargo_number,
                                                "Individual Number": individual_number,
                                                "Отправитель": cargo_info.get("sender_name", "Неизвестно"),
                                                "Получатель": cargo_info.get("recipient_name", "Неизвестно"),
                                                "Размещен": cargo_info.get("placed_at", "Неизвестно"),
                                                "Оператор": cargo_info.get("placed_by", "Неизвестно")
                                            }
                
                self.log_result(
                    "Поиск заявки 25082235 в layout",
                    found_cargo_25082235,
                    cargo_details if found_cargo_25082235 else "Заявка 25082235 не найдена в layout"
                )
                
                return True
            else:
                self.log_result(
                    "Анализ структуры данных через layout-with-cargo",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Анализ структуры данных", False, f"Исключение: {str(e)}")
            return False

    def check_specific_placement_record(self):
        """4. Прямой поиск записи с cargo_number=25082235 и individual_number=25082235/02/02"""
        try:
            # Попробуем найти информацию через API размещения
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/fully-placed")
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                found_cargo = None
                for item in items:
                    if item.get("cargo_number") == "25082235":
                        found_cargo = item
                        break
                
                if found_cargo:
                    individual_units = found_cargo.get("individual_units", [])
                    target_unit = None
                    
                    for unit in individual_units:
                        if unit.get("individual_number") == "25082235/02/02":
                            target_unit = unit
                            break
                    
                    if target_unit:
                        placement_info = target_unit.get("placement_info", {})
                        
                        self.log_result(
                            "Поиск конкретной записи 25082235/02/02",
                            True,
                            {
                                "Cargo Number": found_cargo.get("cargo_number"),
                                "Individual Number": target_unit.get("individual_number"),
                                "Статус": target_unit.get("status"),
                                "Размещение": placement_info,
                                "Warehouse ID в заявке": found_cargo.get("target_warehouse_id", "Не указан"),
                                "Warehouse Name в заявке": found_cargo.get("target_warehouse_name", "Не указан"),
                                "Accepting Warehouse": found_cargo.get("accepting_warehouse", "Не указан")
                            }
                        )
                        
                        # Проверяем соответствие warehouse_id
                        cargo_warehouse_id = found_cargo.get("target_warehouse_id")
                        matches_warehouse_id = cargo_warehouse_id == self.warehouse_id
                        
                        self.log_result(
                            "Проверка соответствия warehouse_id",
                            matches_warehouse_id,
                            {
                                "Warehouse ID из API": self.warehouse_id,
                                "Warehouse ID в заявке": cargo_warehouse_id,
                                "Соответствие": "Да" if matches_warehouse_id else "НЕТ - ПРОБЛЕМА НАЙДЕНА!",
                                "Возможная причина": "Несоответствие warehouse_id" if not matches_warehouse_id else "ID совпадают"
                            }
                        )
                        
                        return True
                    else:
                        self.log_result(
                            "Поиск конкретной записи 25082235/02/02",
                            False,
                            f"Individual unit 25082235/02/02 не найден. Доступные: {[u.get('individual_number') for u in individual_units]}"
                        )
                        return False
                else:
                    self.log_result(
                        "Поиск конкретной записи 25082235/02/02",
                        False,
                        f"Заявка 25082235 не найдена в fully-placed. Доступные: {[i.get('cargo_number') for i in items]}"
                    )
                    return False
            else:
                self.log_result(
                    "Поиск конкретной записи 25082235/02/02",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Поиск конкретной записи", False, f"Исключение: {str(e)}")
            return False

    def test_layout_with_cargo_api(self):
        """5. Проверить что API /api/warehouses/{warehouse_id}/layout-with-cargo получает правильный warehouse_id"""
        try:
            print(f"🔍 Тестируем API с warehouse_id: {self.warehouse_id}")
            
            response = self.session.get(f"{BACKEND_URL}/warehouses/{self.warehouse_id}/layout-with-cargo")
            
            if response.status_code == 200:
                data = response.json()
                warehouse_info = data.get("warehouse", {})
                
                self.log_result(
                    "Тестирование API layout-with-cargo",
                    True,
                    {
                        "HTTP Status": response.status_code,
                        "Warehouse ID в запросе": self.warehouse_id,
                        "Warehouse ID в ответе": warehouse_info.get("id"),
                        "Warehouse Name": warehouse_info.get("name"),
                        "Warehouse Location": warehouse_info.get("location"),
                        "Warehouse ID Number": warehouse_info.get("warehouse_id_number"),
                        "Соответствие ID": "Да" if warehouse_info.get("id") == self.warehouse_id else "НЕТ",
                        "Всего ячеек": data.get("total_cells"),
                        "Занятых ячеек": data.get("occupied_cells"),
                        "Всего грузов": data.get("total_cargo")
                    }
                )
                return True
            else:
                self.log_result(
                    "Тестирование API layout-with-cargo",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Тестирование API layout-with-cargo", False, f"Исключение: {str(e)}")
            return False

    def analyze_placement_records_debug(self):
        """6. Добавить отладочные сообщения для проверки placement_records"""
        try:
            # Попробуем получить дополнительную отладочную информацию через различные API
            
            # 1. Проверим individual-units-for-placement
            response1 = self.session.get(f"{BACKEND_URL}/operator/cargo/individual-units-for-placement")
            
            if response1.status_code == 200:
                data1 = response1.json()
                items1 = data1.get("items", [])
                
                cargo_25082235_units = []
                for item in items1:
                    if "25082235" in item.get("cargo_number", ""):
                        cargo_25082235_units.append({
                            "Individual Number": item.get("individual_number"),
                            "Cargo Number": item.get("cargo_number"),
                            "Status": item.get("status"),
                            "Warehouse ID": item.get("warehouse_id", "Не указан"),
                            "Target Warehouse": item.get("target_warehouse_name", "Не указан")
                        })
                
                self.log_result(
                    "Анализ individual-units-for-placement для 25082235",
                    len(cargo_25082235_units) > 0,
                    {
                        "Найдено единиц": len(cargo_25082235_units),
                        "Детали": cargo_25082235_units
                    }
                )
            
            # 2. Проверим placement-progress
            response2 = self.session.get(f"{BACKEND_URL}/operator/placement-progress")
            
            if response2.status_code == 200:
                data2 = response2.json()
                
                self.log_result(
                    "Анализ placement-progress",
                    True,
                    {
                        "Всего единиц": data2.get("total_units", 0),
                        "Размещено единиц": data2.get("placed_units", 0),
                        "Ожидает размещения": data2.get("pending_units", 0),
                        "Процент прогресса": f"{data2.get('progress_percentage', 0)}%",
                        "Текст прогресса": data2.get("progress_text", "Неизвестно")
                    }
                )
            
            # 3. Попробуем получить детали конкретной заявки
            response3 = self.session.get(f"{BACKEND_URL}/operator/cargo/25082235/placement-status")
            
            if response3.status_code == 200:
                data3 = response3.json()
                
                cargo_types = data3.get("cargo_types", [])
                placement_details = {}
                
                for cargo_type in cargo_types:
                    individual_units = cargo_type.get("individual_units", [])
                    for unit in individual_units:
                        if unit.get("individual_number") == "25082235/02/02":
                            placement_details = {
                                "Individual Number": unit.get("individual_number"),
                                "Status": unit.get("status"),
                                "Status Label": unit.get("status_label"),
                                "Placement Info": unit.get("placement_info"),
                                "Is Placed": unit.get("is_placed", False)
                            }
                            break
                
                self.log_result(
                    "Детали размещения для 25082235/02/02",
                    bool(placement_details),
                    placement_details if placement_details else "Единица не найдена в placement-status"
                )
            
            return True
                
        except Exception as e:
            self.log_result("Анализ отладочной информации", False, f"Исключение: {str(e)}")
            return False

    def run_comprehensive_analysis(self):
        """Запуск полного анализа проблемы со схемой склада"""
        print("🎯 КРИТИЧЕСКАЯ ДИАГНОСТИКА ПРОБЛЕМЫ СО СХЕМОЙ СКЛАДА")
        print("=" * 80)
        print("Углубленная проверка структуры данных placement_records для заявки 25082235")
        print("=" * 80)
        print()
        
        # Выполняем все проверки по порядку
        steps = [
            ("1. Авторизация warehouse_operator", self.authenticate_warehouse_operator),
            ("2. Получение warehouse_id для Москва Склад №1", self.get_moscow_warehouse_id),
            ("3. Анализ структуры данных placement_records", self.analyze_placement_records_structure),
            ("4. Поиск конкретной записи 25082235/02/02", self.check_specific_placement_record),
            ("5. Тестирование API layout-with-cargo", self.test_layout_with_cargo_api),
            ("6. Отладочный анализ placement_records", self.analyze_placement_records_debug)
        ]
        
        success_count = 0
        total_steps = len(steps)
        
        for step_name, step_function in steps:
            print(f"🔄 Выполняется: {step_name}")
            if step_function():
                success_count += 1
            print("-" * 60)
        
        # Итоговый отчет
        print("\n" + "=" * 80)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ДИАГНОСТИКИ")
        print("=" * 80)
        
        success_rate = (success_count / total_steps) * 100
        print(f"SUCCESS RATE: {success_rate:.1f}% ({success_count}/{total_steps} тестов пройдены)")
        print()
        
        # Анализ результатов
        failed_tests = [result for result in self.test_results if not result["success"]]
        
        if failed_tests:
            print("❌ ОБНАРУЖЕННЫЕ ПРОБЛЕМЫ:")
            for test in failed_tests:
                print(f"  • {test['test']}: {test['details']}")
            print()
        
        # Ключевые выводы
        print("🔍 КЛЮЧЕВЫЕ ВЫВОДЫ:")
        
        if self.warehouse_id:
            print(f"  • Warehouse ID для 'Москва Склад №1': {self.warehouse_id}")
        
        # Поиск проблем с warehouse_id
        warehouse_mismatch_found = False
        for result in self.test_results:
            if "warehouse_id" in str(result.get("details", "")).lower() and not result["success"]:
                warehouse_mismatch_found = True
                break
        
        if warehouse_mismatch_found:
            print("  • ⚠️ НАЙДЕНО НЕСООТВЕТСТВИЕ WAREHOUSE_ID - ЭТО КОРЕНЬ ПРОБЛЕМЫ!")
            print("  • Рекомендация: Проверить синхронизацию warehouse_id между API и placement_records")
        else:
            print("  • ✅ Warehouse_ID соответствует между API и данными")
        
        print()
        print("🎯 ЗАКЛЮЧЕНИЕ:")
        if success_rate >= 80:
            print("  Диагностика завершена успешно. Большинство компонентов работают корректно.")
        else:
            print("  Обнаружены критические проблемы, требующие немедленного исправления.")
        
        print("\n" + "=" * 80)
        
        return success_rate >= 80

def main():
    """Главная функция запуска диагностики"""
    analyzer = WarehouseSchemaAnalyzer()
    
    try:
        success = analyzer.run_comprehensive_analysis()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Диагностика прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка диагностики: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
ДЕТАЛЬНОЕ РАССЛЕДОВАНИЕ РАСХОЖДЕНИЯ ДАННЫХ О ЗАНЯТОСТИ ЯЧЕЕК СКЛАДА "МОСКВА №1"
===============================================================================

НАЙДЕННАЯ ПРОБЛЕМА:
- GET /api/warehouses/{warehouse_id}/cells показывает: 0 занятых ячеек
- GET /api/warehouses/{warehouse_id}/statistics показывает: 2 занятые ячейки (1.0% загрузка)
- Карточка склада показывает: "Занято 2 ячейки, загрузка 1.0%"
- Схема склада показывает: "Занято: 0, Свободно: 210"

КОРЕНЬ ПРОБЛЕМЫ: Statistics API правильно считает 2 занятые ячейки, но Cells API не показывает их как занятые.

ДОПОЛНИТЕЛЬНЫЕ ПРОВЕРКИ:
1. Проверить все ячейки склада на предмет cargo_id
2. Найти грузы, размещенные в этом складе
3. Проверить связь между грузами и ячейками
4. Определить точные координаты проблемных ячеек
"""

import requests
import json
import sys
from datetime import datetime

# Конфигурация
BASE_URL = "https://tajline-cargo-7.preview.emergentagent.com/api"
ADMIN_PHONE = "+79999888777"
ADMIN_PASSWORD = "admin123"

class DetailedWarehouseInvestigation:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.moscow_1_warehouse_id = "9d12adae-95cb-42d6-973f-c02afb30b8ce"  # Из предыдущего теста
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: str):
        """Логирование результатов тестирования"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}: {details}"
        self.test_results.append(result)
        print(result)
        
    def authenticate_admin(self):
        """Авторизация администратора"""
        try:
            login_data = {
                "phone": ADMIN_PHONE,
                "password": ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                return True
            else:
                self.log_result("ADMIN AUTHENTICATION", False, f"Ошибка авторизации: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("ADMIN AUTHENTICATION", False, f"Исключение: {str(e)}")
            return False
    
    def investigate_cells_detailed(self):
        """Детальное исследование всех ячеек склада"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{BASE_URL}/warehouses/{self.moscow_1_warehouse_id}/cells", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                cells = data.get("cells", [])
                
                # Анализируем каждую ячейку
                cells_with_cargo = []
                cells_marked_occupied = []
                
                for cell in cells:
                    cargo_id = cell.get("cargo_id")
                    is_occupied = cell.get("is_occupied", False)
                    block = cell.get("block_number")
                    shelf = cell.get("shelf_number")
                    cell_num = cell.get("cell_number")
                    
                    if cargo_id:
                        cells_with_cargo.append({
                            "location": f"Блок {block}, Полка {shelf}, Ячейка {cell_num}",
                            "cargo_id": cargo_id,
                            "is_occupied": is_occupied
                        })
                    
                    if is_occupied:
                        cells_marked_occupied.append({
                            "location": f"Блок {block}, Полка {shelf}, Ячейка {cell_num}",
                            "cargo_id": cargo_id,
                            "is_occupied": is_occupied
                        })
                
                details = f"Всего ячеек: {len(cells)}, Ячеек с cargo_id: {len(cells_with_cargo)}, Ячеек marked as occupied: {len(cells_marked_occupied)}"
                
                if cells_with_cargo:
                    details += "\n  ЯЧЕЙКИ С CARGO_ID:"
                    for cell in cells_with_cargo:
                        details += f"\n    - {cell['location']}: cargo_id={cell['cargo_id']}, is_occupied={cell['is_occupied']}"
                
                if cells_marked_occupied:
                    details += "\n  ЯЧЕЙКИ MARKED AS OCCUPIED:"
                    for cell in cells_marked_occupied:
                        details += f"\n    - {cell['location']}: cargo_id={cell['cargo_id']}"
                
                self.log_result("DETAILED CELLS INVESTIGATION", True, details)
                return True, cells_with_cargo, cells_marked_occupied
                
            else:
                self.log_result("DETAILED CELLS INVESTIGATION", False, f"Ошибка: {response.status_code}")
                return False, [], []
                
        except Exception as e:
            self.log_result("DETAILED CELLS INVESTIGATION", False, f"Исключение: {str(e)}")
            return False, [], []
    
    def find_cargo_in_warehouse(self):
        """Найти все грузы, размещенные в складе Москва №1"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Проверяем разные endpoints для поиска грузов
            endpoints_to_check = [
                f"/warehouses/{self.moscow_1_warehouse_id}/placed-cargo",
                f"/admin/cargo/list",
                f"/operator/cargo/list"
            ]
            
            found_cargo = []
            
            for endpoint in endpoints_to_check:
                try:
                    response = self.session.get(f"{BASE_URL}{endpoint}", headers=headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Обрабатываем разные форматы ответов
                        cargo_list = []
                        if isinstance(data, list):
                            cargo_list = data
                        elif isinstance(data, dict):
                            if "items" in data:
                                cargo_list = data["items"]
                            elif "cargo" in data:
                                cargo_list = data["cargo"]
                            elif "placed_cargo" in data:
                                cargo_list = data["placed_cargo"]
                        
                        # Фильтруем грузы по складу
                        for cargo in cargo_list:
                            warehouse_id = cargo.get("warehouse_id")
                            target_warehouse_id = cargo.get("target_warehouse_id")
                            status = cargo.get("status", "")
                            
                            if (warehouse_id == self.moscow_1_warehouse_id or 
                                target_warehouse_id == self.moscow_1_warehouse_id or
                                "placed" in status.lower() or "warehouse" in status.lower()):
                                
                                found_cargo.append({
                                    "cargo_number": cargo.get("cargo_number"),
                                    "cargo_id": cargo.get("id"),
                                    "status": status,
                                    "warehouse_id": warehouse_id,
                                    "target_warehouse_id": target_warehouse_id,
                                    "block_number": cargo.get("block_number"),
                                    "shelf_number": cargo.get("shelf_number"),
                                    "cell_number": cargo.get("cell_number"),
                                    "endpoint": endpoint
                                })
                        
                        self.log_result(f"CARGO SEARCH {endpoint}", True, f"Найдено {len(cargo_list)} грузов, из них в складе Москва №1: {len([c for c in cargo_list if c.get('warehouse_id') == self.moscow_1_warehouse_id or c.get('target_warehouse_id') == self.moscow_1_warehouse_id])}")
                        
                except Exception as e:
                    self.log_result(f"CARGO SEARCH {endpoint}", False, f"Ошибка: {str(e)}")
            
            # Убираем дубликаты
            unique_cargo = []
            seen_ids = set()
            for cargo in found_cargo:
                cargo_id = cargo.get("cargo_id")
                if cargo_id and cargo_id not in seen_ids:
                    unique_cargo.append(cargo)
                    seen_ids.add(cargo_id)
            
            details = f"Найдено {len(unique_cargo)} уникальных грузов в складе Москва №1"
            if unique_cargo:
                details += "\n  НАЙДЕННЫЕ ГРУЗЫ:"
                for cargo in unique_cargo:
                    location = ""
                    if cargo.get("block_number") and cargo.get("shelf_number") and cargo.get("cell_number"):
                        location = f" в Блок {cargo['block_number']}, Полка {cargo['shelf_number']}, Ячейка {cargo['cell_number']}"
                    details += f"\n    - {cargo['cargo_number']} (ID: {cargo['cargo_id']}) - статус: {cargo['status']}{location}"
            
            self.log_result("WAREHOUSE CARGO SEARCH", True, details)
            return True, unique_cargo
            
        except Exception as e:
            self.log_result("WAREHOUSE CARGO SEARCH", False, f"Исключение: {str(e)}")
            return False, []
    
    def check_statistics_calculation(self):
        """Проверить как рассчитывается статистика склада"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{BASE_URL}/warehouses/{self.moscow_1_warehouse_id}/statistics", headers=headers)
            
            if response.status_code == 200:
                stats = response.json()
                
                total_cells = stats.get("total_cells", 0)
                occupied_cells = stats.get("occupied_cells", 0)
                free_cells = stats.get("free_cells", 0)
                utilization_percent = stats.get("utilization_percent", 0)
                
                # Дополнительные поля, если есть
                additional_fields = {}
                for key, value in stats.items():
                    if key not in ["total_cells", "occupied_cells", "free_cells", "utilization_percent"]:
                        additional_fields[key] = value
                
                details = f"Statistics API: total={total_cells}, occupied={occupied_cells}, free={free_cells}, utilization={utilization_percent}%"
                
                if additional_fields:
                    details += f"\n  ДОПОЛНИТЕЛЬНЫЕ ПОЛЯ: {json.dumps(additional_fields, indent=2, ensure_ascii=False)}"
                
                # Проверяем откуда берется occupied_cells = 2
                details += f"\n  АНАЛИЗ: Statistics API показывает {occupied_cells} занятых ячеек, но Cells API показывает 0"
                details += f"\n  ВОЗМОЖНАЯ ПРИЧИНА: Statistics считает по другому источнику данных (возможно, по грузам со статусом 'placed_in_warehouse')"
                
                self.log_result("STATISTICS CALCULATION CHECK", True, details)
                return True, stats
                
            else:
                self.log_result("STATISTICS CALCULATION CHECK", False, f"Ошибка: {response.status_code}")
                return False, {}
                
        except Exception as e:
            self.log_result("STATISTICS CALCULATION CHECK", False, f"Исключение: {str(e)}")
            return False, {}
    
    def run_detailed_investigation(self):
        """Запуск детального расследования"""
        print("🔍 ДЕТАЛЬНОЕ РАССЛЕДОВАНИЕ РАСХОЖДЕНИЯ ДАННЫХ О ЗАНЯТОСТИ ЯЧЕЕК СКЛАДА 'МОСКВА №1'")
        print("=" * 95)
        print(f"Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Склад ID: {self.moscow_1_warehouse_id}")
        print()
        
        # Авторизация
        if not self.authenticate_admin():
            print("\n❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться")
            return False
        
        # Детальное исследование ячеек
        cells_success, cells_with_cargo, cells_marked_occupied = self.investigate_cells_detailed()
        if not cells_success:
            print("\n❌ ОШИБКА: Не удалось исследовать ячейки")
            return False
        
        # Поиск грузов в складе
        cargo_success, warehouse_cargo = self.find_cargo_in_warehouse()
        if not cargo_success:
            print("\n❌ ОШИБКА: Не удалось найти грузы в складе")
            return False
        
        # Проверка расчета статистики
        stats_success, stats_data = self.check_statistics_calculation()
        if not stats_success:
            print("\n❌ ОШИБКА: Не удалось проверить статистику")
            return False
        
        # Итоговый анализ
        print("\n" + "=" * 95)
        print("🎯 ИТОГОВЫЙ АНАЛИЗ ПРОБЛЕМЫ")
        print("=" * 95)
        
        print("📊 НАЙДЕННЫЕ ДАННЫЕ:")
        print(f"• Cells API: {len(cells_marked_occupied)} ячеек marked as occupied, {len(cells_with_cargo)} ячеек с cargo_id")
        print(f"• Statistics API: {stats_data.get('occupied_cells', 0)} занятых ячеек")
        print(f"• Найдено грузов в складе: {len(warehouse_cargo)}")
        
        print("\n🔍 ДИАГНОЗ ПРОБЛЕМЫ:")
        if stats_data.get('occupied_cells', 0) == 2 and len(cells_marked_occupied) == 0:
            print("✅ ПРОБЛЕМА ИДЕНТИФИЦИРОВАНА:")
            print("  - Statistics API правильно считает 2 занятые ячейки")
            print("  - Cells API не отмечает эти ячейки как is_occupied=true")
            print("  - Возможно, проблема в синхронизации данных между коллекциями")
            
            if len(warehouse_cargo) >= 2:
                print(f"  - Найдено {len(warehouse_cargo)} грузов в складе, что подтверждает наличие 2 занятых ячеек")
            else:
                print(f"  - Найдено только {len(warehouse_cargo)} грузов, требуется дополнительная проверка")
        
        print("\n💡 РЕКОМЕНДАЦИИ ДЛЯ ИСПРАВЛЕНИЯ:")
        print("1. Проверить синхронизацию поля is_occupied в коллекции warehouse_cells")
        print("2. Убедиться, что при размещении груза обновляется is_occupied=true")
        print("3. Запустить скрипт синхронизации данных между грузами и ячейками")
        print("4. Обновить схему склада на основе данных Statistics API (2 занятые ячейки)")
        
        if warehouse_cargo:
            print("\n📍 КООРДИНАТЫ ЗАНЯТЫХ ЯЧЕЕК (на основе найденных грузов):")
            for cargo in warehouse_cargo:
                if cargo.get("block_number") and cargo.get("shelf_number") and cargo.get("cell_number"):
                    print(f"  - Груз {cargo['cargo_number']}: Блок {cargo['block_number']}, Полка {cargo['shelf_number']}, Ячейка {cargo['cell_number']}")
        
        print(f"\nВремя завершения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True

def main():
    """Основная функция"""
    investigator = DetailedWarehouseInvestigation()
    
    try:
        success = investigator.run_detailed_investigation()
        
        if success:
            print("\n🎉 РАССЛЕДОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            sys.exit(0)
        else:
            print("\n❌ РАССЛЕДОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Расследование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
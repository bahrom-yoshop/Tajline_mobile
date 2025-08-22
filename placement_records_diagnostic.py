#!/usr/bin/env python3
"""
🔍 ГЛУБОКОЕ ИССЛЕДОВАНИЕ: Поиск placement_records для грузов 25082235/01/01 и 25082235/01/02

**ЦЕЛЬ:** Найти где находятся данные о размещенных грузах и почему они не отображаются в layout-with-cargo

**ИССЛЕДОВАНИЕ:**
1. Проверить API fully-placed для поиска размещенных грузов
2. Проверить статистику склада
3. Найти любые размещенные грузы в системе
4. Диагностировать проблему с конкретными грузами 25082235/01/01 и 25082235/01/02
"""

import requests
import json
import sys
from datetime import datetime
import time

# Configuration
BACKEND_URL = "https://placement-view.preview.emergentagent.com/api"
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"

# Test credentials
TEST_CREDENTIALS = {
    "phone": WAREHOUSE_OPERATOR_PHONE,
    "password": WAREHOUSE_OPERATOR_PASSWORD
}

# Global variables
auth_token = None
warehouse_id = None
target_cargo_numbers = ["25082235/01/01", "25082235/01/02"]

def make_request(method, endpoint, data=None, headers=None):
    """Make HTTP request with error handling and timing"""
    url = f"{BACKEND_URL}{endpoint}"
    
    if headers is None:
        headers = {}
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    start_time = time.time()
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method.upper() == "POST":
            headers["Content-Type"] = "application/json"
            response = requests.post(url, json=data, headers=headers, timeout=30)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response_time_ms = int((time.time() - start_time) * 1000)
        return response, response_time_ms
    
    except requests.exceptions.RequestException as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        print(f"❌ Request failed: {e}")
        return None, response_time_ms

def authenticate():
    """Authenticate and get warehouse_id"""
    global auth_token, warehouse_id
    
    print("🔐 Авторизация...")
    response, _ = make_request("POST", "/auth/login", TEST_CREDENTIALS)
    
    if response and response.status_code == 200:
        data = response.json()
        auth_token = data.get("access_token")
        user_info = data.get("user", {})
        print(f"✅ Авторизован как: {user_info.get('full_name')} (роль: {user_info.get('role')})")
    else:
        print("❌ Ошибка авторизации")
        return False
    
    print("🏢 Получение warehouse_id...")
    response, _ = make_request("GET", "/operator/warehouses")
    
    if response and response.status_code == 200:
        warehouses = response.json()
        for warehouse in warehouses:
            if "Москва Склад №1" in warehouse.get("name", ""):
                warehouse_id = warehouse.get("id")
                print(f"✅ Найден склад: {warehouse.get('name')} (ID: {warehouse_id})")
                break
    else:
        print("❌ Ошибка получения складов")
        return False
    
    return True

def check_fully_placed_cargo():
    """Проверить API fully-placed для поиска размещенных грузов"""
    print("\n📦 ПРОВЕРКА ПОЛНОСТЬЮ РАЗМЕЩЕННЫХ ГРУЗОВ:")
    print("="*60)
    
    response, response_time = make_request("GET", "/operator/cargo/fully-placed")
    
    if not response or response.status_code != 200:
        print(f"❌ Не удалось получить данные о полностью размещенных грузах")
        return
    
    try:
        data = response.json()
        items = data.get("items", [])
        
        print(f"📊 Найдено полностью размещенных заявок: {len(items)}")
        
        if not items:
            print("⚠️ Нет полностью размещенных заявок в системе")
            return
        
        # Ищем целевые грузы
        target_found = []
        all_individual_units = []
        
        for item in items:
            cargo_number = item.get("cargo_number", "")
            individual_units = item.get("individual_units", [])
            
            print(f"\n📋 Заявка {cargo_number}:")
            print(f"   Всего единиц: {len(individual_units)}")
            
            for unit in individual_units:
                individual_number = unit.get("individual_number", "")
                status = unit.get("status", "")
                placement_info = unit.get("placement_info", "")
                
                all_individual_units.append(individual_number)
                
                if individual_number in target_cargo_numbers:
                    target_found.append({
                        "individual_number": individual_number,
                        "status": status,
                        "placement_info": placement_info,
                        "cargo_number": cargo_number
                    })
                
                status_icon = "✅" if status == "placed" else "⏳"
                print(f"   {status_icon} {individual_number}: {status} - {placement_info}")
        
        print(f"\n🎯 РЕЗУЛЬТАТ ПОИСКА ЦЕЛЕВЫХ ГРУЗОВ:")
        if target_found:
            print(f"✅ Найдено {len(target_found)} целевых грузов:")
            for cargo in target_found:
                print(f"   - {cargo['individual_number']}: {cargo['status']} ({cargo['placement_info']})")
        else:
            print(f"❌ Целевые грузы {target_cargo_numbers} НЕ найдены среди {len(all_individual_units)} единиц")
            print(f"   Доступные единицы: {all_individual_units[:10]}{'...' if len(all_individual_units) > 10 else ''}")
        
    except Exception as e:
        print(f"❌ Ошибка анализа данных: {e}")

def check_warehouse_statistics():
    """Проверить статистику склада"""
    print("\n📊 СТАТИСТИКА СКЛАДА:")
    print("="*60)
    
    if not warehouse_id:
        print("❌ warehouse_id не определен")
        return
    
    response, _ = make_request("GET", f"/warehouses/{warehouse_id}/statistics")
    
    if not response or response.status_code != 200:
        print(f"❌ Не удалось получить статистику склада")
        return
    
    try:
        stats = response.json()
        
        print(f"📈 Статистика склада 'Москва Склад №1':")
        print(f"   Всего ячеек: {stats.get('total_cells', 0)}")
        print(f"   Занято ячеек: {stats.get('occupied_cells', 0)}")
        print(f"   Свободно ячеек: {stats.get('free_cells', 0)}")
        print(f"   Загрузка: {stats.get('occupancy_percentage', 0)}%")
        print(f"   Всего грузов: {stats.get('total_cargo', 0)}")
        
        if stats.get('occupied_cells', 0) > 0:
            print("✅ В складе есть размещенные грузы согласно статистике")
        else:
            print("⚠️ Статистика показывает 0 размещенных грузов")
        
    except Exception as e:
        print(f"❌ Ошибка анализа статистики: {e}")

def deep_investigation():
    """Глубокое исследование проблемы"""
    print("\n🔍 ГЛУБОКОЕ ИССЛЕДОВАНИЕ ПРОБЛЕМЫ:")
    print("="*60)
    
    # Проверяем layout-with-cargo еще раз
    if warehouse_id:
        response, _ = make_request("GET", f"/warehouses/{warehouse_id}/layout-with-cargo")
        
        if response and response.status_code == 200:
            layout_data = response.json()
            
            occupied_cells = layout_data.get("occupied_cells", 0)
            total_cargo = layout_data.get("total_cargo", 0)
            
            print(f"🏗️ Layout-with-cargo API:")
            print(f"   Занятые ячейки: {occupied_cells}")
            print(f"   Всего грузов: {total_cargo}")
            
            if occupied_cells == 0:
                print("❌ API layout-with-cargo показывает 0 занятых ячеек")
                
                # Проверяем структуру склада
                warehouse_info = layout_data.get("warehouse", {})
                layout = warehouse_info.get("layout", {})
                blocks = layout.get("blocks", [])
                
                print(f"   Блоков в структуре: {len(blocks)}")
                
                # Ищем любые занятые ячейки
                found_occupied = False
                for block in blocks:
                    shelves = block.get("shelves", [])
                    for shelf in shelves:
                        cells = shelf.get("cells", [])
                        for cell in cells:
                            if cell.get("is_occupied", False):
                                found_occupied = True
                                cargo_list = cell.get("cargo", [])
                                print(f"   ✅ Найдена занятая ячейка: {cell.get('location_code')} с {len(cargo_list)} грузами")
                                break
                        if found_occupied:
                            break
                    if found_occupied:
                        break
                
                if not found_occupied:
                    print("   ❌ Ни одной занятой ячейки не найдено в структуре")
            else:
                print("✅ API layout-with-cargo показывает размещенные грузы")
        else:
            print("❌ Не удалось получить данные layout-with-cargo")

def main():
    """Main investigation"""
    print("🔍 ГЛУБОКОЕ ИССЛЕДОВАНИЕ: Поиск placement_records для грузов 25082235/01/01 и 25082235/01/02")
    print("="*100)
    
    if not authenticate():
        print("❌ Не удалось авторизоваться. Исследование невозможно.")
        return
    
    # Проверяем полностью размещенные грузы
    check_fully_placed_cargo()
    
    # Проверяем статистику склада
    check_warehouse_statistics()
    
    # Глубокое исследование
    deep_investigation()
    
    print("\n" + "="*100)
    print("🎯 ЗАКЛЮЧЕНИЕ ИССЛЕДОВАНИЯ:")
    print("Если целевые грузы 25082235/01/01 и 25082235/01/02 не найдены в fully-placed,")
    print("но статистика показывает размещенные грузы, то проблема в:")
    print("1. Грузы не размещены физически")
    print("2. Проблема с данными в базе")
    print("3. API layout-with-cargo не синхронизирован с placement_records")
    print("="*100)

if __name__ == "__main__":
    main()
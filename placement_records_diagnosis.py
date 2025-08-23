#!/usr/bin/env python3
"""
Диагностика placement_records для понимания проблемы с отображением груза в схеме склада
"""

import requests
import json
import os
from datetime import datetime

# Конфигурация для тестирования
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cargo-sync.preview.emergentagent.com')
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

def authenticate_admin():
    """Авторизация администратора"""
    session = requests.Session()
    response = session.post(
        f"{API_BASE}/auth/login",
        json=ADMIN_CREDENTIALS,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    return None

def authenticate_operator():
    """Авторизация оператора"""
    session = requests.Session()
    response = session.post(
        f"{API_BASE}/auth/login",
        json=OPERATOR_CREDENTIALS,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    return None

def main():
    print("🔍 ДИАГНОСТИКА PLACEMENT_RECORDS")
    print("=" * 50)
    
    # Авторизация оператора для получения warehouse_id
    operator_session = authenticate_operator()
    if not operator_session:
        print("❌ Не удалось авторизоваться как оператор")
        return
    
    # Получаем warehouse_id
    warehouses_response = operator_session.get(f"{API_BASE}/operator/warehouses", timeout=30)
    if warehouses_response.status_code != 200:
        print("❌ Не удалось получить список складов")
        return
    
    warehouses = warehouses_response.json()
    if not warehouses:
        print("❌ Список складов пуст")
        return
    
    warehouse = warehouses[0]
    warehouse_id = warehouse.get("id")
    warehouse_name = warehouse.get("name")
    
    print(f"📦 Склад: {warehouse_name}")
    print(f"🆔 Warehouse ID: {warehouse_id}")
    print()
    
    # Проверяем fully-placed API для груза 25082235
    fully_placed_response = operator_session.get(f"{API_BASE}/operator/cargo/fully-placed", timeout=30)
    if fully_placed_response.status_code == 200:
        data = fully_placed_response.json()
        items = data.get("items", [])
        
        cargo_25082235 = None
        for item in items:
            if item.get("cargo_number") == "25082235":
                cargo_25082235 = item
                break
        
        if cargo_25082235:
            print("✅ Груз 25082235 найден в fully-placed:")
            print(f"   📋 ID: {cargo_25082235.get('id')}")
            print(f"   📦 Номер: {cargo_25082235.get('cargo_number')}")
            
            individual_units = cargo_25082235.get("individual_units", [])
            for unit in individual_units:
                individual_number = unit.get("individual_number")
                status = unit.get("status")
                placement_info = unit.get("placement_info")
                print(f"   📍 {individual_number}: {status} - {placement_info}")
        else:
            print("❌ Груз 25082235 не найден в fully-placed")
    
    print()
    
    # Проверяем layout-with-cargo API
    layout_response = operator_session.get(f"{API_BASE}/warehouses/{warehouse_id}/layout-with-cargo", timeout=30)
    if layout_response.status_code == 200:
        layout_data = layout_response.json()
        total_cargo = layout_data.get("total_cargo", 0)
        occupied_cells = layout_data.get("occupied_cells", 0)
        
        print(f"🏗️ Схема склада:")
        print(f"   📊 Всего грузов: {total_cargo}")
        print(f"   🏠 Занятых ячеек: {occupied_cells}")
        
        # Проверяем ячейку Б1-П2-Я9
        layout = layout_data.get("layout", {})
        blocks = layout.get("blocks", [])
        
        cell_found = False
        for block in blocks:
            if block.get("block_number") == 1:
                for shelf in block.get("shelves", []):
                    if shelf.get("shelf_number") == 2:
                        for cell in shelf.get("cells", []):
                            if cell.get("cell_number") == 9:
                                cell_found = True
                                is_occupied = cell.get("is_occupied", False)
                                cargo_list = cell.get("cargo", [])
                                print(f"   🎯 Ячейка Б1-П2-Я9: занята={is_occupied}, грузов={len(cargo_list) if cargo_list else 0}")
                                
                                if cargo_list:
                                    for cargo in cargo_list:
                                        print(f"      📦 {cargo.get('individual_number')} ({cargo.get('cargo_number')})")
                                break
                        if cell_found:
                            break
                if cell_found:
                    break
        
        if not cell_found:
            print("   ❌ Ячейка Б1-П2-Я9 не найдена в схеме")
    else:
        print(f"❌ Ошибка получения схемы склада: {layout_response.status_code}")
    
    print()
    
    # Авторизация администратора для прямого доступа к данным
    admin_session = authenticate_admin()
    if not admin_session:
        print("❌ Не удалось авторизоваться как администратор")
        return
    
    # Проверяем placement_records напрямую (если есть такой API)
    # Попробуем через debug API или создадим специальный endpoint
    print("🔍 Попытка диагностики placement_records...")
    
    # Попробуем найти debug endpoint или создать запрос
    debug_response = admin_session.get(f"{API_BASE}/admin/debug/placement-records?cargo_number=25082235", timeout=30)
    if debug_response.status_code == 200:
        debug_data = debug_response.json()
        print("📋 Placement records для груза 25082235:")
        for record in debug_data:
            print(f"   🆔 ID: {record.get('id', 'N/A')}")
            print(f"   📦 Cargo: {record.get('cargo_number', 'N/A')}")
            print(f"   🔢 Individual: {record.get('individual_number', 'N/A')}")
            print(f"   🏠 Warehouse ID: {record.get('warehouse_id', 'N/A')}")
            print(f"   📍 Location: {record.get('location', 'N/A')}")
            print(f"   👤 Placed by: {record.get('placed_by', 'N/A')}")
            print()
    else:
        print(f"⚠️ Debug API недоступен (HTTP {debug_response.status_code})")
        print("💡 Рекомендация: Создать debug endpoint для диагностики placement_records")

if __name__ == "__main__":
    main()
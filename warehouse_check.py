#!/usr/bin/env python3
"""
Проверка доступных складов для оператора
"""

import requests
import json
import os

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-manage-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Конфигурация
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"

def main():
    session = requests.Session()
    
    # Авторизация
    print("🔐 Авторизация оператора склада...")
    response = session.post(f"{API_BASE}/auth/login", json={
        "phone": WAREHOUSE_OPERATOR_PHONE,
        "password": WAREHOUSE_OPERATOR_PASSWORD
    })
    
    if response.status_code != 200:
        print(f"❌ Ошибка авторизации: {response.status_code}")
        return
    
    data = response.json()
    auth_token = data.get("access_token")
    operator_info = data.get("user")
    
    session.headers.update({
        "Authorization": f"Bearer {auth_token}"
    })
    
    print(f"✅ Авторизован: {operator_info.get('full_name')}")
    
    # Проверяем доступные склады оператора
    print("\n📋 Проверка доступных складов оператора...")
    response = session.get(f"{API_BASE}/operator/warehouses")
    
    if response.status_code == 200:
        warehouses = response.json()
        print(f"✅ Найдено складов: {len(warehouses)}")
        
        for warehouse in warehouses:
            print(f"  🏢 {warehouse.get('name')} (ID: {warehouse.get('id')}, Номер: {warehouse.get('warehouse_id_number', 'N/A')})")
            
            # Пробуем получить layout-with-cargo для каждого склада
            warehouse_id = warehouse.get('warehouse_id_number') or warehouse.get('id')
            print(f"    🔍 Тестирование layout-with-cargo для склада {warehouse_id}...")
            
            layout_response = session.get(f"{API_BASE}/warehouses/{warehouse_id}/layout-with-cargo")
            if layout_response.status_code == 200:
                layout_data = layout_response.json()
                print(f"    ✅ API доступен, структура: {list(layout_data.keys()) if isinstance(layout_data, dict) else type(layout_data)}")
                
                # Проверяем наличие cargo_info
                if isinstance(layout_data, dict) and "cargo_info" in layout_data:
                    cargo_info = layout_data["cargo_info"]
                    print(f"    🎯 cargo_info найдено: {len(cargo_info)} единиц")
                    
                    if len(cargo_info) > 0:
                        print(f"    📦 Пример единицы: {list(cargo_info[0].keys()) if isinstance(cargo_info[0], dict) else type(cargo_info[0])}")
                else:
                    print(f"    ❌ cargo_info не найдено в ответе")
            else:
                print(f"    ❌ Ошибка доступа: {layout_response.status_code} - {layout_response.text}")
    else:
        print(f"❌ Ошибка получения складов: {response.status_code}")
    
    # Также проверим все склады в системе
    print("\n📋 Проверка всех складов в системе...")
    response = session.get(f"{API_BASE}/warehouses/all-cities")
    
    if response.status_code == 200:
        all_warehouses = response.json()
        print(f"✅ Всего складов в системе: {len(all_warehouses)}")
        
        for warehouse in all_warehouses:
            print(f"  🏢 {warehouse.get('name')} (ID: {warehouse.get('id')}, Номер: {warehouse.get('warehouse_id_number', 'N/A')})")

if __name__ == "__main__":
    main()
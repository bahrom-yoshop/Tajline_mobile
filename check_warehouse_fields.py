#!/usr/bin/env python3
"""
Check warehouse fields in detail
"""

import requests
import json

# Configuration
BACKEND_URL = "https://tajline-cargo-7.preview.emergentagent.com/api"
WAREHOUSE_OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

def check_warehouse_fields():
    session = requests.Session()
    
    # Authenticate as warehouse operator
    print("🔐 Авторизация оператора склада...")
    response = session.post(f"{BACKEND_URL}/auth/login", json=WAREHOUSE_OPERATOR_CREDENTIALS)
    
    if response.status_code != 200:
        print(f"❌ Ошибка авторизации: {response.status_code}")
        return False
    
    data = response.json()
    token = data.get("access_token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    print("✅ Авторизация успешна")
    
    # Get warehouses
    print("🏭 Получение складов...")
    response = session.get(f"{BACKEND_URL}/operator/warehouses")
    
    if response.status_code == 200:
        warehouses = response.json()
        print(f"✅ Получено {len(warehouses)} складов")
        
        # Check first warehouse in detail
        if warehouses:
            warehouse = warehouses[0]
            print(f"\n🔍 ДЕТАЛЬНАЯ ПРОВЕРКА ПЕРВОГО СКЛАДА:")
            print(f"   Название: {warehouse.get('name')}")
            print(f"   ID: {warehouse.get('id')}")
            print(f"   Все поля:")
            for key, value in warehouse.items():
                print(f"     {key}: {value}")
        
        return True
    else:
        print(f"❌ Ошибка: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    check_warehouse_fields()
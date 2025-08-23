#!/usr/bin/env python3
"""
Детальная проверка структуры cargo_info
"""

import requests
import json
import os

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cargo-sync.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Конфигурация
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"
TARGET_WAREHOUSE = "d0a8362d-b4d3-4947-b335-28c94658a021"

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
    
    session.headers.update({
        "Authorization": f"Bearer {auth_token}"
    })
    
    print("✅ Авторизация успешна")
    
    # Получаем layout-with-cargo
    print(f"\n📋 Получение layout-with-cargo для склада {TARGET_WAREHOUSE}...")
    response = session.get(f"{API_BASE}/warehouses/{TARGET_WAREHOUSE}/layout-with-cargo")
    
    if response.status_code != 200:
        print(f"❌ Ошибка: {response.status_code} - {response.text}")
        return
    
    data = response.json()
    print("✅ Данные получены")
    
    # Анализируем структуру
    print(f"\n📊 Структура ответа:")
    for key, value in data.items():
        if key == "cargo_info":
            print(f"  {key}: список из {len(value)} элементов")
        else:
            print(f"  {key}: {type(value).__name__} = {value}")
    
    # Детальный анализ cargo_info
    cargo_info = data.get("cargo_info", [])
    print(f"\n🔍 ДЕТАЛЬНЫЙ АНАЛИЗ cargo_info ({len(cargo_info)} единиц):")
    
    for i, unit in enumerate(cargo_info):
        print(f"\n📦 ЕДИНИЦА #{i + 1}:")
        print(f"  Все поля: {list(unit.keys())}")
        
        for key, value in unit.items():
            print(f"    {key}: {value} ({type(value).__name__})")
    
    # Проверяем какие поля присутствуют во всех единицах
    if cargo_info:
        all_fields = set()
        for unit in cargo_info:
            all_fields.update(unit.keys())
        
        print(f"\n📊 СВОДКА ПО ПОЛЯМ:")
        print(f"  Всего уникальных полей: {len(all_fields)}")
        print(f"  Поля: {sorted(all_fields)}")
        
        # Проверяем какие поля есть во всех единицах
        common_fields = set(cargo_info[0].keys())
        for unit in cargo_info[1:]:
            common_fields &= set(unit.keys())
        
        print(f"  Поля во всех единицах: {sorted(common_fields)}")
        
        # Проверяем какие поля отсутствуют в некоторых единицах
        missing_in_some = all_fields - common_fields
        if missing_in_some:
            print(f"  Поля отсутствующие в некоторых единицах: {sorted(missing_in_some)}")

if __name__ == "__main__":
    main()
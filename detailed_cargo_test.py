#!/usr/bin/env python3
"""
Detailed test to examine cargo data structure
"""

import requests
import json

# Конфигурация
BASE_URL = "https://placement-view.preview.emergentagent.com/api"
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"

# Глобальные переменные для токена
auth_token = None

def make_request(method, endpoint, data=None, headers=None):
    """Выполнить HTTP запрос с обработкой ошибок"""
    url = f"{BASE_URL}{endpoint}"
    
    if headers is None:
        headers = {}
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method.upper() == "POST":
            headers["Content-Type"] = "application/json"
            response = requests.post(url, json=data, headers=headers, timeout=30)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        return response
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def authenticate():
    """Авторизация"""
    global auth_token
    
    print("🔐 Авторизация...")
    
    auth_data = {
        "phone": WAREHOUSE_OPERATOR_PHONE,
        "password": WAREHOUSE_OPERATOR_PASSWORD
    }
    
    response = make_request("POST", "/auth/login", auth_data)
    
    if response and response.status_code == 200:
        data = response.json()
        auth_token = data.get("access_token")
        user_info = data.get("user", {})
        print(f"✅ Авторизован как: {user_info.get('full_name')} ({user_info.get('role')})")
        return True
    else:
        print("❌ Ошибка авторизации")
        return False

def examine_individual_units():
    """Детально изучаем individual units"""
    print("\n🔍 Детальное изучение individual units...")
    
    response = make_request("GET", "/operator/cargo/individual-units-for-placement")
    
    if response and response.status_code == 200:
        data = response.json()
        print(f"📊 Полный ответ API:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        items = data.get("items", [])
        print(f"\n📦 Найдено items: {len(items)}")
        
        for i, item in enumerate(items):
            print(f"\n   📋 Item {i+1}:")
            for key, value in item.items():
                print(f"      {key}: {value}")
    else:
        print("❌ Ошибка получения individual units")

def examine_available_cargo():
    """Детально изучаем available cargo"""
    print("\n🔍 Детальное изучение available cargo...")
    
    response = make_request("GET", "/operator/cargo/available-for-placement")
    
    if response and response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        
        print(f"📦 Найдено cargo items: {len(items)}")
        
        for i, cargo in enumerate(items[:1]):  # Показываем только первый для детального анализа
            print(f"\n   📋 Cargo {i+1}:")
            print(f"      cargo_number: {cargo.get('cargo_number')}")
            print(f"      cargo_name: {cargo.get('cargo_name')}")
            
            cargo_items = cargo.get("cargo_items", [])
            print(f"      cargo_items count: {len(cargo_items)}")
            
            for j, cargo_item in enumerate(cargo_items):
                print(f"\n         📦 Cargo Item {j+1}:")
                print(f"            name: {cargo_item.get('name')}")
                print(f"            cargo_name: {cargo_item.get('cargo_name')}")
                
                individual_items = cargo_item.get("individual_items", [])
                print(f"            individual_items count: {len(individual_items)}")
                
                for k, individual_item in enumerate(individual_items):
                    print(f"\n               🔹 Individual Item {k+1}:")
                    print(f"                  individual_number: {individual_item.get('individual_number')}")
                    print(f"                  is_placed: {individual_item.get('is_placed')}")
                    print(f"                  placement_info: {individual_item.get('placement_info')}")
    else:
        print("❌ Ошибка получения available cargo")

def test_verify_cargo_with_known_data():
    """Тестируем verify-cargo с известными данными"""
    print("\n🧪 Тестируем verify-cargo с известными данными...")
    
    # Тестируем основные номера грузов (без individual numbers)
    test_cases = [
        {"qr_code": "250101", "expected_name": "Сумка кожаный"},
        {"qr_code": "25082235", "expected_name": "Самокат ВИВО"}
    ]
    
    for test_case in test_cases:
        qr_code = test_case["qr_code"]
        expected_name = test_case["expected_name"]
        
        print(f"\n   🔍 Тестируем: {qr_code} (ожидается: {expected_name})")
        
        response = make_request("POST", "/operator/placement/verify-cargo", {"qr_code": qr_code})
        
        if response and response.status_code == 200:
            data = response.json()
            success = data.get("success", False)
            cargo_info = data.get("cargo_info", {})
            error = data.get("error", "")
            
            if success:
                cargo_name = cargo_info.get("cargo_name", "N/A")
                cargo_number = cargo_info.get("cargo_number", "N/A")
                individual_number = cargo_info.get("individual_number", "N/A")
                
                print(f"      ✅ SUCCESS!")
                print(f"         - cargo_number: {cargo_number}")
                print(f"         - cargo_name: {cargo_name}")
                print(f"         - individual_number: {individual_number}")
                
                # Проверяем соответствие ожидаемому наименованию
                if expected_name in cargo_name:
                    print(f"         ✅ Наименование соответствует ожидаемому!")
                else:
                    print(f"         ⚠️ Наименование не соответствует: ожидалось '{expected_name}', получено '{cargo_name}'")
            else:
                print(f"      ❌ FAIL: {error}")
        else:
            print(f"      ❌ HTTP error")

def main():
    """Основная функция"""
    print("🔍 ДЕТАЛЬНОЕ ИЗУЧЕНИЕ СТРУКТУРЫ ДАННЫХ ГРУЗОВ")
    print("="*60)
    
    if not authenticate():
        return
    
    # Изучаем individual units
    examine_individual_units()
    
    # Изучаем available cargo
    examine_available_cargo()
    
    # Тестируем verify-cargo
    test_verify_cargo_with_known_data()

if __name__ == "__main__":
    main()
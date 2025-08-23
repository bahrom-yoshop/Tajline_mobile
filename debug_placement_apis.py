#!/usr/bin/env python3
"""
🔍 DEBUG: Детальная диагностика API для размещения
"""

import requests
import json
import time

# Конфигурация
BASE_URL = "https://cargo-sync.preview.emergentagent.com/api"
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"

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
        
        return response
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def authenticate():
    """Авторизация"""
    global auth_token
    
    auth_data = {
        "phone": WAREHOUSE_OPERATOR_PHONE,
        "password": WAREHOUSE_OPERATOR_PASSWORD
    }
    
    response = make_request("POST", "/auth/login", auth_data)
    
    if response and response.status_code == 200:
        data = response.json()
        auth_token = data.get("access_token")
        print("✅ Авторизация успешна")
        return True
    else:
        print("❌ Ошибка авторизации")
        return False

def debug_individual_units_api():
    """Детальная диагностика individual-units-for-placement API"""
    print("\n🔍 ДЕТАЛЬНАЯ ДИАГНОСТИКА: individual-units-for-placement API")
    
    response = make_request("GET", "/operator/cargo/individual-units-for-placement?page=1&per_page=25")
    
    if response and response.status_code == 200:
        data = response.json()
        print(f"📊 Полный ответ API:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        items = data.get('items', [])
        print(f"\n📋 Анализ {len(items)} элементов:")
        
        for i, item in enumerate(items):
            print(f"\n--- Элемент {i+1} ---")
            print(f"cargo_number: {item.get('cargo_number')}")
            print(f"individual_number: {item.get('individual_number')}")
            print(f"is_placed: {item.get('is_placed')}")
            print(f"cargo_name: {item.get('cargo_name')}")
            print(f"status: {item.get('status')}")
    else:
        print(f"❌ Ошибка API: {response.status_code if response else 'No response'}")
        if response:
            print(response.text)

def debug_available_for_placement_api():
    """Детальная диагностика available-for-placement API"""
    print("\n🔍 ДЕТАЛЬНАЯ ДИАГНОСТИКА: available-for-placement API")
    
    response = make_request("GET", "/operator/cargo/available-for-placement?page=1&per_page=25")
    
    if response and response.status_code == 200:
        data = response.json()
        print(f"📊 Полный ответ API:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        items = data.get('items', [])
        print(f"\n📋 Анализ {len(items)} элементов:")
        
        for i, item in enumerate(items):
            print(f"\n--- Элемент {i+1} ---")
            print(f"cargo_number: {item.get('cargo_number')}")
            print(f"placed_count: {item.get('placed_count')}")
            print(f"total_units: {item.get('total_units')}")
            print(f"placement_progress: {item.get('placement_progress')}")
            print(f"cargo_items: {len(item.get('cargo_items', []))}")
            
            # Детальный анализ cargo_items
            cargo_items = item.get('cargo_items', [])
            for j, cargo_item in enumerate(cargo_items):
                print(f"  Cargo Item {j+1}:")
                print(f"    cargo_name: {cargo_item.get('cargo_name')}")
                print(f"    quantity: {cargo_item.get('quantity')}")
                
                individual_items = cargo_item.get('individual_items', [])
                print(f"    individual_items: {len(individual_items)}")
                
                for k, individual in enumerate(individual_items):
                    print(f"      Individual {k+1}:")
                    print(f"        individual_number: {individual.get('individual_number')}")
                    print(f"        is_placed: {individual.get('is_placed')}")
                    print(f"        placement_info: {individual.get('placement_info')}")
    else:
        print(f"❌ Ошибка API: {response.status_code if response else 'No response'}")
        if response:
            print(response.text)

def debug_specific_cargo_250101():
    """Проверка конкретной заявки 250101"""
    print("\n🔍 ДЕТАЛЬНАЯ ДИАГНОСТИКА: Заявка 250101")
    
    # Проверяем каждую единицу заявки 250101
    units_to_check = [
        "250101/01/01",
        "250101/01/02", 
        "250101/02/01",
        "250101/02/02"
    ]
    
    for unit in units_to_check:
        print(f"\n--- Проверка единицы {unit} ---")
        response = make_request("POST", "/operator/placement/verify-cargo", {"qr_code": unit})
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ {unit}: НЕ РАЗМЕЩЕН (доступен для размещения)")
                cargo_info = data.get("cargo_info", {})
                print(f"   cargo_name: {cargo_info.get('cargo_name')}")
                print(f"   status: {cargo_info.get('status')}")
            else:
                error = data.get("error", "")
                if "уже размещен" in error.lower():
                    print(f"🔒 {unit}: РАЗМЕЩЕН ({error})")
                else:
                    print(f"❓ {unit}: НЕИЗВЕСТНО ({error})")
        else:
            print(f"❌ {unit}: ОШИБКА API")

if __name__ == "__main__":
    print("🔍 НАЧАЛО ДЕТАЛЬНОЙ ДИАГНОСТИКИ API")
    print("=" * 60)
    
    if authenticate():
        debug_individual_units_api()
        debug_available_for_placement_api()
        debug_specific_cargo_250101()
    else:
        print("❌ Не удалось авторизоваться")
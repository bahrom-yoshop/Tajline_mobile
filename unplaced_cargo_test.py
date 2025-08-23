#!/usr/bin/env python3
"""
Test to find unplaced cargo units for testing verify-cargo API
"""

import requests
import json

# Конфигурация
BASE_URL = "https://cargo-sync.preview.emergentagent.com/api"
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

def find_unplaced_units():
    """Ищем неразмещенные единицы грузов"""
    print("\n🔍 Ищем неразмещенные единицы грузов...")
    
    response = make_request("GET", "/operator/cargo/individual-units-for-placement")
    
    if response and response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        
        print(f"📊 Найдено individual units для размещения: {len(items)}")
        
        unplaced_units = []
        
        for item in items:
            individual_number = item.get("individual_number", "N/A")
            cargo_name = item.get("cargo_name", "N/A")
            status = item.get("status", "N/A")
            is_placed = item.get("is_placed", False)
            
            if not is_placed:
                unplaced_units.append(individual_number)
                print(f"   ✅ Неразмещен: {individual_number} - {cargo_name} (статус: {status})")
            else:
                print(f"   ❌ Размещен: {individual_number} - {cargo_name}")
        
        return unplaced_units
    else:
        print("❌ Ошибка получения individual units")
        return []

def test_unplaced_units(unplaced_units):
    """Тестируем неразмещенные единицы"""
    print(f"\n🧪 Тестируем {len(unplaced_units)} неразмещенных единиц...")
    
    for individual_number in unplaced_units[:5]:  # Тестируем первые 5
        print(f"\n   🔍 Тестируем: {individual_number}")
        
        response = make_request("POST", "/operator/placement/verify-cargo", {"qr_code": individual_number})
        
        if response and response.status_code == 200:
            data = response.json()
            success = data.get("success", False)
            cargo_info = data.get("cargo_info", {})
            error = data.get("error", "")
            
            if success:
                cargo_name = cargo_info.get("cargo_name", "N/A")
                cargo_number = cargo_info.get("cargo_number", "N/A")
                individual_num = cargo_info.get("individual_number", "N/A")
                print(f"      ✅ SUCCESS!")
                print(f"         - cargo_number: {cargo_number}")
                print(f"         - cargo_name: {cargo_name}")
                print(f"         - individual_number: {individual_num}")
            else:
                print(f"      ❌ FAIL: {error}")
        else:
            print(f"      ❌ HTTP error")

def main():
    """Основная функция"""
    print("🔍 ПОИСК НЕРАЗМЕЩЕННЫХ ГРУЗОВ ДЛЯ ТЕСТИРОВАНИЯ")
    print("="*60)
    
    if not authenticate():
        return
    
    # Ищем неразмещенные единицы
    unplaced_units = find_unplaced_units()
    
    if unplaced_units:
        # Тестируем их
        test_unplaced_units(unplaced_units)
    else:
        print("\n⚠️ Все единицы грузов уже размещены!")
        print("   Для тестирования API verify-cargo нужны неразмещенные единицы.")

if __name__ == "__main__":
    main()
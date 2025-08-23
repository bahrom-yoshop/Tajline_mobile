#!/usr/bin/env python3
"""
Diagnostic test to check what cargo is available in the system
"""

import requests
import json
import time
from datetime import datetime

# Конфигурация
BASE_URL = "https://tajline-manage-1.preview.emergentagent.com/api"
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

def check_available_cargo():
    """Проверяем доступные грузы для размещения"""
    print("\n📦 Проверяем доступные грузы для размещения...")
    
    response = make_request("GET", "/operator/cargo/available-for-placement")
    
    if response and response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        
        print(f"📊 Найдено грузов для размещения: {len(items)}")
        
        # Показываем первые 10 грузов
        for i, cargo in enumerate(items[:10]):
            cargo_number = cargo.get("cargo_number", "N/A")
            cargo_name = cargo.get("cargo_name", "N/A")
            print(f"   {i+1}. {cargo_number} - {cargo_name}")
            
            # Проверяем individual_items если есть
            cargo_items = cargo.get("cargo_items", [])
            for cargo_item in cargo_items:
                individual_items = cargo_item.get("individual_items", [])
                for individual_item in individual_items:
                    individual_number = individual_item.get("individual_number", "N/A")
                    print(f"      └─ Individual: {individual_number}")
        
        return items
    else:
        print("❌ Ошибка получения грузов")
        return []

def test_specific_cargo_numbers():
    """Тестируем конкретные номера грузов"""
    print("\n🧪 Тестируем конкретные номера грузов...")
    
    # Тестируемые номера из review request
    test_numbers = [
        "250101/01/02",
        "25082235/01/01", 
        "25082235/01/02",
        "25082235/02/01",
        "250101",  # Попробуем без individual number
        "25082235"  # Попробуем без individual number
    ]
    
    for qr_code in test_numbers:
        print(f"\n   🔍 Тестируем: {qr_code}")
        
        response = make_request("POST", "/operator/placement/verify-cargo", {"qr_code": qr_code})
        
        if response:
            if response.status_code == 200:
                data = response.json()
                success = data.get("success", False)
                cargo_info = data.get("cargo_info", {})
                error = data.get("error", "")
                
                if success:
                    cargo_name = cargo_info.get("cargo_name", "N/A")
                    cargo_number = cargo_info.get("cargo_number", "N/A")
                    print(f"      ✅ SUCCESS: {cargo_number} - {cargo_name}")
                else:
                    print(f"      ❌ FAIL: {error}")
            else:
                print(f"      ❌ HTTP {response.status_code}")
        else:
            print(f"      ❌ Network error")

def main():
    """Основная функция"""
    print("🔍 ДИАГНОСТИКА ГРУЗОВ В СИСТЕМЕ")
    print("="*50)
    
    if not authenticate():
        return
    
    # Проверяем доступные грузы
    available_cargo = check_available_cargo()
    
    # Тестируем конкретные номера
    test_specific_cargo_numbers()

if __name__ == "__main__":
    main()
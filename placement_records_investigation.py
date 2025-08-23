#!/usr/bin/env python3
"""
🔍 ДИАГНОСТИКА: Исследование placement_records для заявок 25082235 и 250101

ЦЕЛЬ: Понять реальное состояние размещения заявок через placement_records коллекцию
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
    
    start_time = time.time()
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method.upper() == "POST":
            headers["Content-Type"] = "application/json"
            response = requests.post(url, json=data, headers=headers, timeout=30)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response_time = int((time.time() - start_time) * 1000)
        return response, response_time
    
    except requests.exceptions.RequestException as e:
        response_time = int((time.time() - start_time) * 1000)
        print(f"❌ Request failed: {e}")
        return None, response_time

def authenticate():
    """Авторизация"""
    global auth_token
    
    print("🔐 Авторизация оператора склада...")
    
    auth_data = {
        "phone": WAREHOUSE_OPERATOR_PHONE,
        "password": WAREHOUSE_OPERATOR_PASSWORD
    }
    
    response, response_time = make_request("POST", "/auth/login", auth_data)
    
    if response and response.status_code == 200:
        data = response.json()
        auth_token = data.get("access_token")
        user_info = data.get("user", {})
        print(f"✅ Авторизован как: {user_info.get('full_name')} ({user_info.get('role')})")
        return True
    else:
        print(f"❌ Ошибка авторизации: {response.status_code if response else 'Network error'}")
        return False

def investigate_placement_records():
    """Исследование placement_records"""
    print("\n🔍 ИССЛЕДОВАНИЕ PLACEMENT_RECORDS")
    print("="*60)
    
    # Проверяем общую статистику размещения
    print("\n📊 Общая статистика размещения:")
    response, _ = make_request("GET", "/operator/placement-progress")
    
    if response and response.status_code == 200:
        data = response.json()
        print(f"   - Всего единиц: {data.get('total_units', 'N/A')}")
        print(f"   - Размещено единиц: {data.get('placed_units', 'N/A')}")
        print(f"   - Ожидает размещения: {data.get('pending_units', 'N/A')}")
        print(f"   - Процент прогресса: {data.get('progress_percentage', 'N/A')}%")
    else:
        print("   ❌ Не удалось получить общую статистику")
    
    # Проверяем полностью размещенные заявки
    print("\n📋 Полностью размещенные заявки:")
    response, _ = make_request("GET", "/operator/cargo/fully-placed?page=1&per_page=10")
    
    if response and response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        print(f"   - Найдено полностью размещенных заявок: {len(items)}")
        
        for item in items:
            cargo_number = item.get("cargo_number", "N/A")
            status = item.get("status", "N/A")
            print(f"      • {cargo_number} - статус: {status}")
            
            # Проверяем есть ли наши критические заявки
            if cargo_number in ["25082235", "250101"]:
                print(f"        🎯 НАЙДЕНА КРИТИЧЕСКАЯ ЗАЯВКА: {cargo_number}")
                print(f"           Детали: {json.dumps(item, indent=10, ensure_ascii=False)}")
    else:
        print("   ❌ Не удалось получить список полностью размещенных заявок")
    
    # Проверяем individual units для размещения
    print("\n🔧 Individual units для размещения:")
    response, _ = make_request("GET", "/operator/cargo/individual-units-for-placement?page=1&per_page=50")
    
    if response and response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        print(f"   - Найдено individual units: {len(items)}")
        
        # Группируем по заявкам
        cargo_groups = {}
        for item in items:
            individual_number = item.get("individual_number", "")
            if "/" in individual_number:
                cargo_number = individual_number.split("/")[0]
                if cargo_number not in cargo_groups:
                    cargo_groups[cargo_number] = []
                cargo_groups[cargo_number].append(item)
        
        print(f"   - Заявки с individual units: {list(cargo_groups.keys())}")
        
        # Проверяем критические заявки
        for critical_cargo in ["25082235", "250101"]:
            if critical_cargo in cargo_groups:
                units = cargo_groups[critical_cargo]
                print(f"\n      🎯 ЗАЯВКА {critical_cargo}:")
                print(f"         - Individual units: {len(units)}")
                for unit in units:
                    individual_number = unit.get("individual_number", "")
                    status = unit.get("status", "")
                    is_placed = unit.get("is_placed", False)
                    print(f"           • {individual_number}: status={status}, is_placed={is_placed}")
            else:
                print(f"\n      ✅ ЗАЯВКА {critical_cargo}: НЕ найдена в individual units (возможно полностью размещена)")
    else:
        print("   ❌ Не удалось получить individual units")

def check_specific_cargo_status():
    """Проверка статуса конкретных заявок"""
    print("\n🎯 ПРОВЕРКА СТАТУСА КОНКРЕТНЫХ ЗАЯВОК")
    print("="*60)
    
    critical_cargos = ["25082235", "250101"]
    
    for cargo_number in critical_cargos:
        print(f"\n📦 ЗАЯВКА {cargo_number}:")
        
        # Проверяем через verify-cargo API для каждой единицы
        test_units = [
            f"{cargo_number}/01/01",
            f"{cargo_number}/01/02", 
            f"{cargo_number}/02/01",
            f"{cargo_number}/02/02"
        ]
        
        placed_units = 0
        total_units = 0
        
        for unit in test_units:
            response, _ = make_request("POST", "/operator/placement/verify-cargo", {"qr_code": unit})
            
            if response and response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    total_units += 1
                    print(f"   ✅ {unit}: Неразмещен (доступен для размещения)")
                else:
                    error = data.get("error", "")
                    if "уже размещен" in error.lower():
                        placed_units += 1
                        total_units += 1
                        print(f"   🏠 {unit}: УЖЕ РАЗМЕЩЕН - {error}")
                    else:
                        print(f"   ❓ {unit}: {error}")
            elif response and response.status_code == 404:
                print(f"   ❌ {unit}: Не найден")
            else:
                print(f"   ❌ {unit}: Ошибка API")
        
        if total_units > 0:
            placement_percentage = (placed_units / total_units) * 100
            print(f"\n   📊 ИТОГ ДЛЯ {cargo_number}:")
            print(f"      - Всего единиц: {total_units}")
            print(f"      - Размещено: {placed_units}")
            print(f"      - Процент размещения: {placement_percentage:.1f}%")
            
            if placement_percentage == 100:
                print(f"      🎯 ЗАЯВКА {cargo_number} ПОЛНОСТЬЮ РАЗМЕЩЕНА!")
            elif placement_percentage > 0:
                print(f"      ⚠️ ЗАЯВКА {cargo_number} ЧАСТИЧНО РАЗМЕЩЕНА")
            else:
                print(f"      📋 ЗАЯВКА {cargo_number} НЕ РАЗМЕЩЕНА")

def main():
    """Основная функция"""
    print("🔍 ДИАГНОСТИКА PLACEMENT_RECORDS")
    print("="*80)
    print(f"🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 URL: {BASE_URL}")
    
    if not authenticate():
        return
    
    investigate_placement_records()
    check_specific_cargo_status()
    
    print("\n" + "="*80)
    print("🏁 ДИАГНОСТИКА ЗАВЕРШЕНА")

if __name__ == "__main__":
    main()
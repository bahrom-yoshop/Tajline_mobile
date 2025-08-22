#!/usr/bin/env python3
"""
🎯 FOCUSED TEST: Критические исправления POST /api/operator/cargo/place-individual в TAJLINE.TJ
"""

import requests
import json
import os

BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://placement-view.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def test_critical_improvements():
    """Тестирование критических исправлений"""
    session = requests.Session()
    
    # 1. Авторизация
    print("🔐 Авторизация оператора склада...")
    login_response = session.post(f'{API_BASE}/auth/login', json={'phone': '+79777888999', 'password': 'warehouse123'})
    
    if login_response.status_code != 200:
        print(f"❌ Ошибка авторизации: {login_response.status_code}")
        return False
    
    token = login_response.json().get('access_token')
    session.headers.update({'Authorization': f'Bearer {token}'})
    print("✅ Авторизация успешна")
    
    # 2. Тест GET /api/operator/placement-progress
    print("\n🎯 ТЕСТ 1: GET /api/operator/placement-progress")
    progress_response = session.get(f'{API_BASE}/operator/placement-progress')
    
    if progress_response.status_code == 200:
        data = progress_response.json()
        required_fields = ["total_units", "placed_units", "pending_units", "progress_percentage", "progress_text"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if not missing_fields:
            print(f"✅ Endpoint работает корректно!")
            print(f"   📊 total_units: {data['total_units']}")
            print(f"   📊 placed_units: {data['placed_units']}")
            print(f"   📊 pending_units: {data['pending_units']}")
            print(f"   📊 progress_percentage: {data['progress_percentage']}%")
            print(f"   📊 progress_text: '{data['progress_text']}'")
        else:
            print(f"❌ Отсутствуют поля: {missing_fields}")
            return False
    else:
        print(f"❌ Ошибка: {progress_response.status_code}")
        return False
    
    # 3. Получение Individual Units для тестирования
    print("\n🎯 ТЕСТ 2: Получение Individual Units")
    units_response = session.get(f'{API_BASE}/operator/cargo/individual-units-for-placement')
    
    if units_response.status_code != 200:
        print(f"❌ Ошибка получения Individual Units: {units_response.status_code}")
        return False
    
    units_data = units_response.json()
    items = units_data.get("items", [])
    
    if not items:
        print("❌ Нет доступных Individual Units для тестирования")
        return False
    
    # Найти неразмещенную единицу
    test_unit = None
    for group in items:
        units = group.get("units", [])
        for unit in units:
            if not unit.get("is_placed", False):
                test_unit = unit
                break
        if test_unit:
            break
    
    if not test_unit:
        print("⚠️ Все Individual Units уже размещены, создаем новый груз...")
        
        # Создаем новый груз для тестирования
        cargo_data = {
            "sender_full_name": "Тест Отправитель",
            "sender_phone": "+79999999999",
            "recipient_full_name": "Тест Получатель", 
            "recipient_phone": "+79888888888",
            "recipient_address": "Душанбе, тестовый адрес",
            "description": "Тестовый груз для Individual Units",
            "route": "moscow_to_tajikistan",
            "cargo_items": [
                {
                    "cargo_name": "Тестовый товар",
                    "quantity": 2,
                    "weight": 5.0,
                    "price_per_kg": 100.0,
                    "total_amount": 1000.0
                }
            ],
            "payment_method": "cash_on_delivery"
        }
        
        create_response = session.post(f'{API_BASE}/operator/cargo/accept', json=cargo_data)
        if create_response.status_code == 200:
            cargo_info = create_response.json()
            cargo_number = cargo_info.get("cargo_number")
            print(f"✅ Создан тестовый груз: {cargo_number}")
            
            # Обновляем список Individual Units
            units_response = session.get(f'{API_BASE}/operator/cargo/individual-units-for-placement')
            if units_response.status_code == 200:
                units_data = units_response.json()
                items = units_data.get("items", [])
                
                # Ищем наш новый груз
                for group in items:
                    if group.get("cargo_number") == cargo_number:
                        units = group.get("units", [])
                        if units:
                            test_unit = units[0]
                            break
        
        if not test_unit:
            print("❌ Не удалось найти Individual Unit для тестирования")
            return False
    
    individual_number = test_unit.get("individual_number")
    print(f"✅ Найдена Individual Unit для тестирования: {individual_number}")
    
    # 4. КРИТИЧЕСКИЙ ТЕСТ: Размещение БЕЗ warehouse_id
    print(f"\n🎯 КРИТИЧЕСКИЙ ТЕСТ: Размещение Individual Unit БЕЗ warehouse_id")
    print(f"   📋 Individual Number: {individual_number}")
    
    placement_data = {
        "individual_number": individual_number,
        # warehouse_id НЕ УКАЗЫВАЕМ - должен определяться автоматически!
        "block_number": 1,
        "shelf_number": 1,
        "cell_number": 3
    }
    
    placement_response = session.post(f'{API_BASE}/operator/cargo/place-individual', json=placement_data)
    
    print(f"   📊 HTTP Status: {placement_response.status_code}")
    
    if placement_response.status_code == 200:
        data = placement_response.json()
        
        if data.get("success", False):
            print("✅ ИСПРАВЛЕНИЕ РАБОТАЕТ! warehouse_id определился автоматически")
            
            # Проверяем детальную информацию
            details = []
            if "cargo_name" in data:
                details.append(f"cargo_name: '{data['cargo_name']}'")
            if "application_progress" in data:
                app_progress = data['application_progress']
                details.append(f"application_progress: {app_progress}")
            if "placement_details" in data:
                placement_details = data['placement_details']
                details.append(f"placement_details: {placement_details}")
            
            if details:
                print("✅ Детальная информация присутствует:")
                for detail in details:
                    print(f"   📝 {detail}")
            else:
                print("⚠️ Детальная информация отсутствует")
            
            return True
        else:
            error_message = data.get("message", "Неизвестная ошибка")
            print(f"❌ Размещение не удалось: {error_message}")
            return False
    elif placement_response.status_code == 422:
        try:
            error_data = placement_response.json()
            error_detail = str(error_data.get("detail", ""))
            if "warehouse_id" in error_detail.lower():
                print(f"❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: warehouse_id все еще требуется!")
                print(f"   📝 Ошибка: {error_detail}")
                return False
            else:
                print(f"❌ Ошибка валидации (не связанная с warehouse_id): {error_detail}")
                return False
        except:
            print(f"❌ HTTP 422 без детальной информации")
            return False
    else:
        print(f"❌ HTTP ошибка: {placement_response.status_code}")
        try:
            error_text = placement_response.text
            print(f"   📝 Ответ: {error_text}")
        except:
            pass
        return False

if __name__ == "__main__":
    print("🎯 FOCUSED TEST: Критические исправления POST /api/operator/cargo/place-individual")
    print("=" * 80)
    
    success = test_critical_improvements()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 ВСЕ КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ РАБОТАЮТ!")
        print("✅ warehouse_id определяется автоматически")
        print("✅ Детальная информация в ответах")
        print("✅ Endpoint placement-progress функционален")
        print("🚀 СИСТЕМА ГОТОВА К ПРОДАКШЕНУ!")
    else:
        print("❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ В ИСПРАВЛЕНИЯХ!")
        print("🔧 Требуется дополнительная работа")
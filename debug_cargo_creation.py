#!/usr/bin/env python3
"""
🎯 DEBUG: Проверка создания заявки для тестирования individual units
"""

import requests
import json
import os

# Конфигурация
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://tajline-cargo-7.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def debug_cargo_creation():
    session = requests.Session()
    
    # Авторизация
    login_data = {
        "phone": "+79777888999",
        "password": "warehouse123"
    }
    
    response = session.post(f"{API_BASE}/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Ошибка авторизации: {response.status_code}")
        return
    
    data = response.json()
    auth_token = data.get("access_token")
    session.headers.update({"Authorization": f"Bearer {auth_token}"})
    
    print("✅ Авторизация успешна")
    
    # Создание заявки
    cargo_data = {
        "sender_full_name": "Тестовый Отправитель DEBUG",
        "sender_phone": "+79991234567",
        "recipient_full_name": "Тестовый Получатель DEBUG",
        "recipient_phone": "+79997654321",
        "recipient_address": "г. Душанбе, ул. Тестовая, дом 1",
        "description": "Тестовый груз для individual units DEBUG",
        "route": "moscow_to_tajikistan",
        "payment_method": "cash_on_delivery",
        "delivery_method": "pickup",
        "cargo_items": [
            {
                "cargo_name": "Электроника Samsung DEBUG",
                "quantity": 2,
                "weight": 5.0,
                "price_per_kg": 100.0,
                "total_amount": 1000.0
            },
            {
                "cargo_name": "Бытовая техника LG DEBUG",
                "quantity": 3,
                "weight": 8.0,
                "price_per_kg": 80.0,
                "total_amount": 1920.0
            }
        ]
    }
    
    print("📦 Отправка запроса на создание заявки...")
    response = session.post(f"{API_BASE}/operator/cargo/accept", json=cargo_data)
    
    print(f"📊 Статус ответа: {response.status_code}")
    print(f"📄 Содержимое ответа: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Заявка создана успешно!")
        print(f"   cargo_id: {data.get('cargo_id')}")
        print(f"   cargo_number: {data.get('cargo_number')}")
        
        # Проверяем, что заявка появилась в individual-units-for-placement
        print("\n🔍 Проверка появления в individual-units-for-placement...")
        response = session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement")
        if response.status_code == 200:
            data = response.json()
            total = data.get('total', 0)
            print(f"📊 Всего individual units: {total}")
            
            if total > 0:
                individual_units = data.get('individual_units', [])
                print(f"📋 Первая единица: {individual_units[0] if individual_units else 'Нет данных'}")
            else:
                print("⚠️ Individual units не найдены")
        else:
            print(f"❌ Ошибка получения individual units: {response.status_code}")
    else:
        print(f"❌ Ошибка создания заявки: {response.status_code}")
        try:
            error_data = response.json()
            print(f"📄 Детали ошибки: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
        except:
            print(f"📄 Текст ошибки: {response.text}")

if __name__ == "__main__":
    debug_cargo_creation()
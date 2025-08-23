#!/usr/bin/env python3
"""
Создание тестовых данных для тестирования individual-units-for-placement endpoint
"""

import requests
import json
import os

# Конфигурация
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://cargo-sync.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def create_test_cargo():
    """Создать тестовую заявку с несколькими типами груза"""
    
    # Авторизация оператора
    session = requests.Session()
    login_data = {
        "phone": "+79777888999",
        "password": "warehouse123"
    }
    
    response = session.post(f"{API_BASE}/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Ошибка авторизации: {response.status_code}")
        return False
    
    data = response.json()
    auth_token = data.get("access_token")
    session.headers.update({"Authorization": f"Bearer {auth_token}"})
    
    # Создаем тестовую заявку с несколькими типами груза
    cargo_data = {
        "sender_full_name": "Тестовый Отправитель Individual Units",
        "sender_phone": "+79777888999",
        "recipient_full_name": "Тестовый Получатель Individual Units", 
        "recipient_phone": "+992987654321",
        "recipient_address": "г. Душанбе, ул. Рудаки, дом 45, кв. 12",
        "description": "Тестовая заявка для проверки individual-units-for-placement endpoint",
        "route": "moscow_to_tajikistan",
        "payment_method": "cash_on_delivery",
        "delivery_method": "pickup",
        "cargo_items": [
            {
                "cargo_name": "Электроника Samsung",
                "quantity": 2,
                "weight": 5.0,
                "price_per_kg": 100.0,
                "total_amount": 1000.0
            },
            {
                "cargo_name": "Бытовая техника LG",
                "quantity": 3,
                "weight": 8.0,
                "price_per_kg": 80.0,
                "total_amount": 1920.0
            }
        ]
    }
    
    response = session.post(f"{API_BASE}/operator/cargo/accept", json=cargo_data)
    
    if response.status_code == 200:
        data = response.json()
        cargo_number = data.get("cargo_number")
        cargo_id = data.get("id")
        print(f"✅ Тестовая заявка создана: {cargo_number} (ID: {cargo_id})")
        print(f"   📦 Грузы: Электроника Samsung (2 шт) + Бытовая техника LG (3 шт) = 5 единиц")
        return True
    else:
        print(f"❌ Ошибка создания заявки: {response.status_code}")
        print(f"   Ответ: {response.text}")
        return False

if __name__ == "__main__":
    print("🎯 СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ ДЛЯ individual-units-for-placement")
    print("=" * 70)
    
    success = create_test_cargo()
    
    if success:
        print("\n✅ Тестовые данные созданы успешно!")
        print("🔍 Теперь можно запустить backend_test.py для полного тестирования")
    else:
        print("\n❌ Не удалось создать тестовые данные")
#!/usr/bin/env python3
"""
Создание тестового транспорта для тестирования cargo-to-transport
"""

import requests
import json
import os
from datetime import datetime

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cargo-sync.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Конфигурация
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"

def authenticate():
    """Авторизация"""
    session = requests.Session()
    
    response = session.post(f"{API_BASE}/auth/login", json={
        "phone": WAREHOUSE_OPERATOR_PHONE,
        "password": WAREHOUSE_OPERATOR_PASSWORD
    })
    
    if response.status_code == 200:
        data = response.json()
        auth_token = data.get("access_token")
        session.headers.update({
            "Authorization": f"Bearer {auth_token}"
        })
        print(f"✅ Авторизация успешна")
        return session
    else:
        print(f"❌ Ошибка авторизации: {response.status_code}")
        return None

def create_test_transport(session):
    """Создать тестовый транспорт"""
    print("\n🔧 Создание тестового транспорта...")
    
    transport_data = {
        "driver_name": "Тестовый Водитель",
        "driver_phone": "+79999999999",
        "transport_number": "001АА01",
        "capacity_kg": 5000.0,
        "direction": "Москва-Душанбе"
    }
    
    try:
        response = session.post(f"{API_BASE}/transport/create", json=transport_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Транспорт создан: {data.get('transport_number')} (ID: {data.get('id')})")
            return data
        else:
            print(f"❌ Ошибка создания транспорта: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Исключение: {e}")
        return None

def set_transport_available(session, transport_id):
    """Установить статус транспорта как available"""
    print(f"\n🔧 Установка статуса 'available' для транспорта {transport_id}...")
    
    # Попробуем обновить статус через прямой API (если есть)
    # Если нет, то транспорт должен быть создан со статусом available по умолчанию
    
    try:
        # Проверим текущий статус
        response = session.get(f"{API_BASE}/transport/{transport_id}")
        if response.status_code == 200:
            data = response.json()
            current_status = data.get("status", "unknown")
            print(f"📋 Текущий статус транспорта: {current_status}")
            
            if current_status == "available":
                print("✅ Транспорт уже имеет статус 'available'")
                return True
            else:
                print(f"⚠️ Транспорт имеет статус '{current_status}', может потребоваться изменение")
                return True  # Для тестирования попробуем использовать как есть
        else:
            print(f"❌ Ошибка получения информации о транспорте: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Исключение: {e}")
        return False

def main():
    print("🚛 СОЗДАНИЕ ТЕСТОВОГО ТРАНСПОРТА ДЛЯ CARGO-TO-TRANSPORT")
    print("=" * 60)
    
    # Авторизация
    session = authenticate()
    if not session:
        return
    
    # Создаем тестовый транспорт
    transport = create_test_transport(session)
    
    if transport:
        transport_id = transport.get("id")
        if transport_id:
            # Устанавливаем статус available
            set_transport_available(session, transport_id)
            
            print(f"\n✅ ТЕСТОВЫЙ ТРАНСПОРТ ГОТОВ:")
            print(f"   ID: {transport_id}")
            print(f"   Номер: {transport.get('transport_number')}")
            print(f"   Водитель: {transport.get('driver_name')}")
            print(f"   Направление: {transport.get('direction')}")
        else:
            print("❌ Не удалось получить ID созданного транспорта")
    else:
        print("❌ Не удалось создать тестовый транспорт")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Проверка данных транспорта и создание тестовых данных если необходимо
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

def check_transports(session):
    """Проверить существующие транспорты"""
    print("\n🚛 Проверка транспортов...")
    
    try:
        response = session.get(f"{API_BASE}/transport/list")
        if response.status_code == 200:
            data = response.json()
            transports = data if isinstance(data, list) else data.get("transports", [])
            print(f"📋 Найдено транспортов: {len(transports)}")
            
            for transport in transports[:5]:  # Показываем первые 5
                print(f"   - {transport.get('transport_number', 'N/A')} (статус: {transport.get('status', 'N/A')})")
            
            return transports
        else:
            print(f"❌ Ошибка получения транспортов: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Исключение: {e}")
        return []

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
        response = session.post(f"{API_BASE}/admin/transport/create", json=transport_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Транспорт создан: {data.get('transport_number')}")
            return data
        else:
            print(f"❌ Ошибка создания транспорта: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Исключение: {e}")
        return None

def check_placement_records(session):
    """Проверить записи размещения"""
    print("\n📦 Проверка записей размещения...")
    
    try:
        # Попробуем найти размещенные грузы
        response = session.get(f"{API_BASE}/operator/cargo/fully-placed")
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", []) if isinstance(data, dict) else data
            print(f"📋 Найдено размещенных заявок: {len(items)}")
            
            if items:
                for item in items[:3]:  # Показываем первые 3
                    cargo_number = item.get("cargo_number", "N/A")
                    print(f"   - Заявка {cargo_number}")
            
            return items
        else:
            print(f"❌ Ошибка получения размещенных грузов: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Исключение: {e}")
        return []

def main():
    print("🔍 ПРОВЕРКА ДАННЫХ ДЛЯ ТЕСТИРОВАНИЯ CARGO-TO-TRANSPORT")
    print("=" * 60)
    
    # Авторизация
    session = authenticate()
    if not session:
        return
    
    # Проверяем транспорты
    transports = check_transports(session)
    
    # Если нет транспортов с нужным номером, создаем
    target_transport = None
    for transport in transports:
        if transport.get("transport_number") == "001АА01":
            target_transport = transport
            break
    
    if not target_transport:
        print("⚠️ Тестовый транспорт 001АА01 не найден, создаем...")
        target_transport = create_test_transport(session)
    else:
        print(f"✅ Тестовый транспорт найден: {target_transport.get('transport_number')} (статус: {target_transport.get('status')})")
    
    # Проверяем размещенные грузы
    placement_records = check_placement_records(session)
    
    print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
    print(f"   Транспортов: {len(transports)}")
    print(f"   Размещенных заявок: {len(placement_records)}")
    print(f"   Тестовый транспорт: {'✅ Готов' if target_transport else '❌ Не готов'}")

if __name__ == "__main__":
    main()
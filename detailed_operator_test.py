#!/usr/bin/env python3
"""
ДЕТАЛЬНОЕ ТЕСТИРОВАНИЕ: Проблема с регистрацией оператора - детальная диагностика
"""

import requests
import json
import os
from datetime import datetime
import uuid

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cargo-sync.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def test_detailed_operator_creation():
    """Детальное тестирование создания оператора"""
    session = requests.Session()
    
    # 1. Авторизация администратора
    print("🔐 Авторизация администратора...")
    login_data = {
        "phone": "+79999888777",
        "password": "admin123"
    }
    
    response = session.post(f"{API_BASE}/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Ошибка авторизации: {response.status_code} - {response.text}")
        return
    
    data = response.json()
    admin_token = data.get("access_token")
    admin_info = data.get("user", {})
    
    print(f"✅ Авторизация успешна: {admin_info.get('full_name')} ({admin_info.get('role')})")
    
    # 2. Получение списка складов
    print("\n📦 Получение списка складов...")
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = session.get(f"{API_BASE}/warehouses", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Ошибка получения складов: {response.status_code} - {response.text}")
        return
    
    warehouses = response.json()
    print(f"✅ Получено {len(warehouses)} складов")
    
    for i, warehouse in enumerate(warehouses[:3]):
        print(f"   Склад {i+1}: {warehouse.get('name')} (ID: {warehouse.get('id')[:8]}...)")
    
    if not warehouses:
        print("❌ Нет складов для тестирования")
        return
    
    # 3. Тестирование создания оператора с первым складом
    print(f"\n👤 Создание оператора для склада '{warehouses[0].get('name')}'...")
    
    test_operator_data = {
        "full_name": f"Детальный Тест Оператор {datetime.now().strftime('%H%M%S')}",
        "phone": f"+7999{datetime.now().strftime('%H%M%S')}",
        "address": "Детальный тестовый адрес для диагностики",
        "password": "detailtest123",
        "warehouse_id": warehouses[0].get('id')
    }
    
    print(f"📋 Данные запроса:")
    print(f"   - ФИО: {test_operator_data['full_name']}")
    print(f"   - Телефон: {test_operator_data['phone']}")
    print(f"   - Адрес: {test_operator_data['address']}")
    print(f"   - Склад ID: {test_operator_data['warehouse_id'][:8]}...")
    
    response = session.post(f"{API_BASE}/admin/create-operator", json=test_operator_data, headers=headers)
    
    print(f"\n📊 Результат запроса:")
    print(f"   - HTTP статус: {response.status_code}")
    print(f"   - Заголовки ответа: {dict(response.headers)}")
    
    if response.status_code == 200 or response.status_code == 201:
        data = response.json()
        print(f"✅ УСПЕХ: Оператор создан успешно!")
        print(f"   - Сообщение: {data.get('message')}")
        if 'operator' in data:
            operator = data['operator']
            print(f"   - ID оператора: {operator.get('id', 'N/A')[:8]}...")
            print(f"   - Склад: {operator.get('warehouse_name', 'N/A')}")
    else:
        print(f"❌ ОШИБКА: Не удалось создать оператора")
        print(f"   - Статус: {response.status_code}")
        print(f"   - Тело ответа: {response.text}")
        
        try:
            error_data = response.json()
            print(f"   - JSON ошибка: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
        except:
            print(f"   - Не JSON ответ")
    
    # 4. Тестирование с невалидными данными
    print(f"\n🧪 Тестирование с невалидными данными...")
    
    # Тест с пустым warehouse_id
    invalid_data = test_operator_data.copy()
    invalid_data['warehouse_id'] = ""
    invalid_data['phone'] = f"+7999{datetime.now().strftime('%H%M%S')}01"
    
    response = session.post(f"{API_BASE}/admin/create-operator", json=invalid_data, headers=headers)
    print(f"   Пустой warehouse_id: HTTP {response.status_code}")
    
    # Тест с несуществующим warehouse_id
    invalid_data['warehouse_id'] = str(uuid.uuid4())
    invalid_data['phone'] = f"+7999{datetime.now().strftime('%H%M%S')}02"
    
    response = session.post(f"{API_BASE}/admin/create-operator", json=invalid_data, headers=headers)
    print(f"   Несуществующий warehouse_id: HTTP {response.status_code}")
    if response.status_code == 404:
        print(f"      ✅ Корректно отклонен: {response.json().get('detail', 'Warehouse not found')}")
    
    # Тест без warehouse_id
    invalid_data_no_warehouse = {
        "full_name": f"Тест Без Склада {datetime.now().strftime('%H%M%S')}",
        "phone": f"+7999{datetime.now().strftime('%H%M%S')}03",
        "address": "Тестовый адрес без склада",
        "password": "nowarehouse123"
    }
    
    response = session.post(f"{API_BASE}/admin/create-operator", json=invalid_data_no_warehouse, headers=headers)
    print(f"   Без warehouse_id: HTTP {response.status_code}")
    if response.status_code == 422:
        try:
            error_data = response.json()
            print(f"      ✅ Валидация сработала: {error_data.get('detail', 'Validation error')}")
        except:
            print(f"      ✅ Валидация сработала")

if __name__ == "__main__":
    print("🚀 ДЕТАЛЬНОЕ ТЕСТИРОВАНИЕ СОЗДАНИЯ ОПЕРАТОРА")
    print("=" * 60)
    test_detailed_operator_creation()
    print("\n🎯 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
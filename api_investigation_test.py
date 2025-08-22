#!/usr/bin/env python3
"""
API Investigation Test - Understanding the current API structure
"""

import requests
import json
import os

# Конфигурация для тестирования
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://placement-manager.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Тестовые данные оператора склада
OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

def authenticate():
    """Авторизация"""
    session = requests.Session()
    
    response = session.post(
        f"{API_BASE}/auth/login",
        json=OPERATOR_CREDENTIALS,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        auth_token = data.get("access_token")
        session.headers.update({
            "Authorization": f"Bearer {auth_token}"
        })
        return session
    return None

def investigate_apis():
    """Исследование API структуры"""
    session = authenticate()
    if not session:
        print("❌ Ошибка авторизации")
        return
    
    print("🔍 ИССЛЕДОВАНИЕ API СТРУКТУРЫ")
    print("=" * 60)
    
    # 1. Проверяем available-for-placement
    print("\n1️⃣ GET /api/operator/cargo/available-for-placement")
    try:
        response = session.get(f"{API_BASE}/operator/cargo/available-for-placement", timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            print(f"Количество заявок: {len(items)}")
            if items:
                first_item = items[0]
                print(f"Структура первой заявки:")
                print(json.dumps(first_item, indent=2, ensure_ascii=False)[:1000] + "...")
    except Exception as e:
        print(f"Ошибка: {e}")
    
    # 2. Проверяем placement-progress
    print("\n2️⃣ GET /api/operator/placement-progress")
    try:
        response = session.get(f"{API_BASE}/operator/placement-progress", timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Данные прогресса:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Ошибка: {e}")
    
    # 3. Проверяем individual-units-for-placement
    print("\n3️⃣ GET /api/operator/cargo/individual-units-for-placement")
    try:
        response = session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement", timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            print(f"Количество групп: {len(items)}")
            if items:
                first_group = items[0]
                print(f"Структура первой группы:")
                print(json.dumps(first_group, indent=2, ensure_ascii=False)[:1000] + "...")
    except Exception as e:
        print(f"Ошибка: {e}")
    
    # 4. Проверяем placement-status для первой заявки
    print("\n4️⃣ GET /api/operator/cargo/{cargo_id}/placement-status")
    try:
        # Получаем первую заявку
        response = session.get(f"{API_BASE}/operator/cargo/available-for-placement", timeout=30)
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            if items:
                cargo_id = items[0].get("id")
                cargo_number = items[0].get("cargo_number")
                
                status_response = session.get(f"{API_BASE}/operator/cargo/{cargo_id}/placement-status", timeout=30)
                print(f"Status: {status_response.status_code}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"Детали размещения для {cargo_number}:")
                    print(json.dumps(status_data, indent=2, ensure_ascii=False)[:1500] + "...")
                else:
                    print(f"Ошибка получения статуса: {status_response.status_code}")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    investigate_apis()
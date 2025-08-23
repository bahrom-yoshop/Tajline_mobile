#!/usr/bin/env python3
"""
DEBUG: Проблема с массовым удалением в TAJLINE.TJ

Проверяем:
1. Работает ли единичное удаление
2. Какая структура данных ожидается для bulk deletion
3. Проблемы с endpoint'ом
"""

import requests
import json
import os

BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-manage-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def test_debug():
    # Авторизация
    auth_data = {"phone": "+79999888777", "password": "admin123"}
    session = requests.Session()
    
    response = session.post(f"{API_BASE}/auth/login", json=auth_data)
    if response.status_code != 200:
        print(f"❌ Ошибка авторизации: {response.text}")
        return
    
    admin_token = response.json().get("access_token")
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Получаем список грузов
    response = session.get(f"{API_BASE}/cargo/all", headers=headers)
    if response.status_code != 200:
        print(f"❌ Ошибка получения списка грузов: {response.text}")
        return
    
    cargo_list = response.json()
    if len(cargo_list) < 3:
        print("❌ Недостаточно грузов для тестирования")
        return
    
    print(f"✅ Получено {len(cargo_list)} грузов")
    
    # Тестируем единичное удаление
    test_cargo = cargo_list[0]
    cargo_id = test_cargo["id"]
    cargo_number = test_cargo["cargo_number"]
    
    print(f"🧪 Тестируем единичное удаление груза {cargo_number} (ID: {cargo_id})")
    
    response = session.delete(f"{API_BASE}/admin/cargo/{cargo_id}", headers=headers)
    print(f"Единичное удаление: HTTP {response.status_code}")
    print(f"Ответ: {response.text}")
    print()
    
    # Тестируем bulk deletion с разными структурами данных
    test_cargo_ids = [cargo["id"] for cargo in cargo_list[1:3]]
    test_cargo_numbers = [cargo["cargo_number"] for cargo in cargo_list[1:3]]
    
    print(f"🧪 Тестируем массовое удаление грузов: {test_cargo_numbers}")
    print(f"IDs: {test_cargo_ids}")
    print()
    
    # Вариант 1: {"ids": [...]}
    print("1️⃣ Тестируем структуру: {\"ids\": [...]}")
    bulk_data_1 = {"ids": test_cargo_ids}
    response = session.delete(f"{API_BASE}/admin/cargo/bulk", json=bulk_data_1, headers=headers)
    print(f"HTTP {response.status_code}")
    print(f"Ответ: {response.text}")
    print()
    
    # Вариант 2: {"cargo_ids": [...]}
    print("2️⃣ Тестируем структуру: {\"cargo_ids\": [...]}")
    bulk_data_2 = {"cargo_ids": test_cargo_ids}
    response = session.delete(f"{API_BASE}/admin/cargo/bulk", json=bulk_data_2, headers=headers)
    print(f"HTTP {response.status_code}")
    print(f"Ответ: {response.text}")
    print()
    
    # Вариант 3: Прямой список
    print("3️⃣ Тестируем прямой список ID")
    response = session.delete(f"{API_BASE}/admin/cargo/bulk", json=test_cargo_ids, headers=headers)
    print(f"HTTP {response.status_code}")
    print(f"Ответ: {response.text}")
    print()
    
    # Проверяем, есть ли другие bulk endpoints
    print("4️⃣ Проверяем альтернативные endpoints")
    
    # Проверяем POST метод
    response = session.post(f"{API_BASE}/admin/cargo/bulk-delete", json=bulk_data_1, headers=headers)
    print(f"POST /api/admin/cargo/bulk-delete: HTTP {response.status_code}")
    print(f"Ответ: {response.text}")
    print()

if __name__ == "__main__":
    test_debug()
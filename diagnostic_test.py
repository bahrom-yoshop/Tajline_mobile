#!/usr/bin/env python3
"""
Диагностический тест для проверки структуры данных endpoint pickup-requests
"""

import requests
import json
import sys

# Конфигурация
BACKEND_URL = "https://03054c56-0cb9-443b-a828-f3e224602a32.preview.emergentagent.com/api"

ADMIN_CREDENTIALS = {
    "phone": "+79999888777",
    "password": "admin123"
}

OPERATOR_CREDENTIALS = {
    "phone": "+79777888999", 
    "password": "warehouse123"
}

def authenticate(credentials):
    """Авторизация пользователя"""
    response = requests.post(
        f"{BACKEND_URL}/auth/login",
        json=credentials,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        return data["access_token"]
    return None

def main():
    # Авторизация
    admin_token = authenticate(ADMIN_CREDENTIALS)
    operator_token = authenticate(OPERATOR_CREDENTIALS)
    
    if not admin_token or not operator_token:
        print("❌ Ошибка авторизации")
        return
    
    print("✅ Авторизация успешна")
    
    # Создаем тестовую заявку
    pickup_data = {
        "sender_full_name": "Диагностический Отправитель",
        "sender_phone": "+79111222333",
        "pickup_address": "Москва, ул. Диагностическая, д. 123",
        "pickup_date": "2025-01-20",
        "pickup_time_from": "10:00",
        "pickup_time_to": "12:00",
        "destination": "Душанбе, ул. Рудаки, д. 100",
        "cargo_name": "Диагностический груз",
        "weight": 5.5,
        "total_value": 2500.0,
        "declared_value": 2500.0,
        "payment_method": "cash",
        "courier_fee": 500.0,
        "delivery_method": "pickup",
        "description": "Диагностическая заявка"
    }
    
    response = requests.post(
        f"{BACKEND_URL}/admin/courier/pickup-request",
        json=pickup_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    if response.status_code != 200:
        print(f"❌ Ошибка создания заявки: {response.status_code} - {response.text}")
        return
    
    request_data = response.json()
    request_id = request_data.get("request_id")
    print(f"✅ Заявка создана с ID: {request_id}")
    
    # Получаем данные через endpoint
    response = requests.get(
        f"{BACKEND_URL}/operator/pickup-requests/{request_id}",
        headers={"Authorization": f"Bearer {operator_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print("\n📊 СТРУКТУРА ДАННЫХ ENDPOINT:")
        print("=" * 60)
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # Анализируем структуру
        print("\n🔍 АНАЛИЗ СТРУКТУРЫ:")
        print("=" * 60)
        
        sections = ["sender_data", "payment_info", "cargo_info", "request_info", "courier_info", "recipient_data"]
        for section in sections:
            if section in data:
                print(f"✅ {section}: {list(data[section].keys())}")
            else:
                print(f"❌ {section}: отсутствует")
        
        # Проверяем конкретные поля
        print("\n🎯 ПРОВЕРКА КЛЮЧЕВЫХ ПОЛЕЙ:")
        print("=" * 60)
        
        sender_data = data.get("sender_data", {})
        payment_info = data.get("payment_info", {})
        cargo_info = data.get("cargo_info", {})
        
        key_fields = [
            ("pickup_date", sender_data.get("pickup_date")),
            ("pickup_time_from", sender_data.get("pickup_time_from")),
            ("pickup_time_to", sender_data.get("pickup_time_to")),
            ("payment_method", payment_info.get("payment_method")),
            ("total_value", cargo_info.get("total_value")),
            ("declared_value", cargo_info.get("declared_value"))
        ]
        
        for field_name, field_value in key_fields:
            status = "✅" if field_value is not None else "❌"
            print(f"{status} {field_name}: {field_value}")
    
    else:
        print(f"❌ Ошибка получения данных: {response.status_code} - {response.text}")
    
    # Очистка
    requests.delete(
        f"{BACKEND_URL}/admin/pickup-requests/{request_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    print(f"\n✅ Тестовая заявка {request_id} удалена")

if __name__ == "__main__":
    main()
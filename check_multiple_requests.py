#!/usr/bin/env python3
"""
Проверка нескольких заявок на забор груза для подтверждения диагноза
"""

import requests
import json

def check_multiple_pickup_requests():
    """Проверка нескольких заявок на забор груза"""
    base_url = "https://placement-view.preview.emergentagent.com"
    
    print("🔍 ПРОВЕРКА НЕСКОЛЬКИХ ЗАЯВОК НА ЗАБОР ГРУЗА")
    print("="*60)
    
    # Авторизация оператора
    login_data = {
        "phone": "+79777888999",
        "password": "warehouse123"
    }
    
    response = requests.post(f"{base_url}/api/auth/login", json=login_data)
    
    if response.status_code != 200:
        print("❌ Ошибка авторизации")
        return
    
    token = response.json().get('access_token')
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Список заявок для проверки
    request_ids = ["100040", "100041", "100042", "100043", "100044"]
    
    for request_id in request_ids:
        print(f"\n📋 ПРОВЕРКА ЗАЯВКИ {request_id}:")
        
        response = requests.get(f"{base_url}/api/operator/pickup-requests/{request_id}", headers=headers)
        
        if response.status_code == 200:
            request_data = response.json()
            
            # Проверяем данные получателя
            recipient_data = request_data.get('recipient_data', {})
            
            if recipient_data:
                recipient_name = recipient_data.get('recipient_full_name', '')
                recipient_phone = recipient_data.get('recipient_phone', '')
                recipient_address = recipient_data.get('recipient_address', '')
                
                filled_count = sum(1 for field in [recipient_name, recipient_phone, recipient_address] 
                                 if field and str(field).strip())
                
                print(f"  ✅ recipient_data найдены: {filled_count}/3 полей заполнено")
                if recipient_name:
                    print(f"    👤 Имя: {recipient_name}")
                if recipient_phone:
                    print(f"    📞 Телефон: {recipient_phone}")
                if recipient_address:
                    print(f"    📍 Адрес: {recipient_address}")
                
                if filled_count == 3:
                    print(f"  🎉 Все данные получателя заполнены")
                elif filled_count > 0:
                    print(f"  ⚠️  Данные получателя заполнены частично")
                else:
                    print(f"  ❌ Данные получателя пустые")
            else:
                print(f"  ❌ recipient_data отсутствуют")
            
            # Проверяем статус заявки
            request_info = request_data.get('request_info', {})
            status = request_info.get('status', 'unknown')
            print(f"  📊 Статус: {status}")
            
        elif response.status_code == 404:
            print(f"  ❌ Заявка {request_id} не найдена")
        else:
            print(f"  ❌ Ошибка {response.status_code} при получении заявки {request_id}")

if __name__ == "__main__":
    check_multiple_pickup_requests()
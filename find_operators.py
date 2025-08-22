#!/usr/bin/env python3
"""
🔍 ПОИСК ДОСТУПНЫХ ОПЕРАТОРОВ СКЛАДА ДЛЯ ТЕСТИРОВАНИЯ
"""

import requests
import json

# Конфигурация
BACKEND_URL = "https://placement-view.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "phone": "+79999888777",
    "password": "admin123"
}

def find_operators():
    session = requests.Session()
    
    # Авторизация администратора
    try:
        response = session.post(
            f"{BACKEND_URL}/auth/login",
            json=ADMIN_CREDENTIALS,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            admin_token = data["access_token"]
            session.headers.update({
                "Authorization": f"Bearer {admin_token}"
            })
            print("✅ Авторизация администратора успешна")
        else:
            print(f"❌ Ошибка авторизации администратора: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Ошибка авторизации: {e}")
        return
    
    # Получение списка пользователей
    try:
        response = session.get(f"{BACKEND_URL}/admin/users")
        
        if response.status_code == 200:
            data = response.json()
            users = data.get('items', []) if isinstance(data, dict) else data
            
            print(f"\n📋 Найдено пользователей: {len(users)}")
            
            # Ищем операторов склада
            operators = [u for u in users if u.get('role') == 'warehouse_operator']
            print(f"🏭 Операторов склада: {len(operators)}")
            
            for i, operator in enumerate(operators[:5], 1):  # Показываем первых 5
                print(f"   {i}. {operator.get('full_name', 'N/A')} - {operator.get('phone', 'N/A')} (ID: {operator.get('id', 'N/A')})")
                print(f"      Активен: {operator.get('is_active', 'N/A')}")
                
            # Также ищем всех пользователей с телефонами, содержащими 777888999
            matching_users = [u for u in users if '777888999' in u.get('phone', '')]
            if matching_users:
                print(f"\n🔍 Пользователи с номером содержащим '777888999':")
                for user in matching_users:
                    print(f"   - {user.get('full_name', 'N/A')} - {user.get('phone', 'N/A')} (Роль: {user.get('role', 'N/A')}, Активен: {user.get('is_active', 'N/A')})")
            
        else:
            print(f"❌ Ошибка получения пользователей: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка получения пользователей: {e}")

if __name__ == "__main__":
    find_operators()
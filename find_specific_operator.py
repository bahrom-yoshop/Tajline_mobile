#!/usr/bin/env python3
"""
🔍 ПОИСК КОНКРЕТНОГО ОПЕРАТОРА USR648400
"""

import requests
import json

# Конфигурация
BACKEND_URL = "https://tajline-cargo-7.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "phone": "+79999888777",
    "password": "admin123"
}

def find_specific_operator():
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
            
            # Ищем конкретного пользователя USR648400
            target_user = None
            for user in users:
                if user.get('user_number') == 'USR648400':
                    target_user = user
                    break
            
            if target_user:
                print(f"\n🎯 НАЙДЕН ЦЕЛЕВОЙ ПОЛЬЗОВАТЕЛЬ:")
                print(f"   Имя: {target_user.get('full_name', 'N/A')}")
                print(f"   Телефон: {target_user.get('phone', 'N/A')}")
                print(f"   Номер: {target_user.get('user_number', 'N/A')}")
                print(f"   Роль: {target_user.get('role', 'N/A')}")
                print(f"   Активен: {target_user.get('is_active', 'N/A')}")
                print(f"   ID: {target_user.get('id', 'N/A')}")
                
                # Попробуем авторизоваться с этими учетными данными
                test_credentials = {
                    "phone": target_user.get('phone'),
                    "password": "warehouse123"
                }
                
                print(f"\n🔐 ТЕСТИРОВАНИЕ АВТОРИЗАЦИИ:")
                print(f"   Телефон: {test_credentials['phone']}")
                print(f"   Пароль: warehouse123")
                
                test_response = requests.post(
                    f"{BACKEND_URL}/auth/login",
                    json=test_credentials,
                    headers={"Content-Type": "application/json"}
                )
                
                if test_response.status_code == 200:
                    print(f"   ✅ АВТОРИЗАЦИЯ УСПЕШНА!")
                    test_data = test_response.json()
                    print(f"   Пользователь: {test_data['user']['full_name']}")
                    print(f"   Роль: {test_data['user']['role']}")
                else:
                    print(f"   ❌ АВТОРИЗАЦИЯ НЕУСПЕШНА: HTTP {test_response.status_code}")
                    print(f"   Ответ: {test_response.text}")
                
            else:
                print(f"\n❌ Пользователь USR648400 НЕ НАЙДЕН")
                
                # Ищем пользователей с похожими номерами
                similar_users = [u for u in users if u.get('user_number', '').startswith('USR648')]
                if similar_users:
                    print(f"\n🔍 Пользователи с похожими номерами:")
                    for user in similar_users:
                        print(f"   - {user.get('full_name', 'N/A')} - {user.get('phone', 'N/A')} (Номер: {user.get('user_number', 'N/A')}, Роль: {user.get('role', 'N/A')})")
                
                # Ищем всех операторов
                operators = [u for u in users if 'operator' in u.get('role', '').lower()]
                if operators:
                    print(f"\n🏭 Все операторы в системе:")
                    for user in operators:
                        print(f"   - {user.get('full_name', 'N/A')} - {user.get('phone', 'N/A')} (Номер: {user.get('user_number', 'N/A')}, Роль: {user.get('role', 'N/A')})")
                
        else:
            print(f"❌ Ошибка получения пользователей: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка получения пользователей: {e}")

if __name__ == "__main__":
    find_specific_operator()
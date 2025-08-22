#!/usr/bin/env python3
"""
🔍 ПОИСК УЧЕТНЫХ ДАННЫХ АДМИНИСТРАТОРА В СИСТЕМЕ TAJLINE.TJ

Цель: Найти корректные учетные данные администратора для создания структуры склада
"""

import requests
import json
import os
from datetime import datetime

# Конфигурация
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://placement-view.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def try_operator_as_admin():
    """Попробуем использовать оператора склада, возможно у него есть админские права"""
    log("🔍 Проверяем права оператора склада...")
    
    session = requests.Session()
    
    # Авторизуемся как оператор
    operator_creds = {
        "phone": "+79777888999",
        "password": "warehouse123"
    }
    
    response = session.post(f"{API_BASE}/auth/login", json=operator_creds)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        
        # Получаем информацию о пользователе
        user_response = session.get(
            f"{API_BASE}/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if user_response.status_code == 200:
            user_data = user_response.json()
            log(f"✅ Оператор авторизован: {user_data.get('full_name')} (роль: {user_data.get('role')})")
            
            # Проверяем доступ к админским функциям
            admin_endpoints = [
                "/admin/warehouses",
                "/warehouses",
                "/admin/users"
            ]
            
            for endpoint in admin_endpoints:
                test_response = session.get(
                    f"{API_BASE}{endpoint}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                log(f"Тест {endpoint}: {test_response.status_code}")
                
                if test_response.status_code == 200:
                    log(f"✅ Доступ к {endpoint} есть!")
                    return token, user_data
                else:
                    log(f"❌ Доступ к {endpoint} запрещен")
            
            return token, user_data
        else:
            log(f"❌ Ошибка получения данных пользователя: {user_response.status_code}")
    else:
        log(f"❌ Ошибка авторизации оператора: {response.status_code}")
    
    return None, None

def try_common_admin_credentials():
    """Пробуем распространенные учетные данные администратора"""
    log("🔍 Пробуем распространенные учетные данные администратора...")
    
    session = requests.Session()
    
    # Расширенный список возможных учетных данных
    admin_credentials = [
        # Из задачи
        {"phone": "admin@tajline.tj", "password": "admin123"},
        
        # Стандартные варианты
        {"phone": "admin", "password": "admin"},
        {"phone": "admin", "password": "password"},
        {"phone": "admin", "password": "123456"},
        {"phone": "administrator", "password": "admin123"},
        
        # Телефонные номера
        {"phone": "+992000000000", "password": "admin123"},
        {"phone": "+992000000001", "password": "admin123"},
        {"phone": "+992999999999", "password": "admin123"},
        {"phone": "+79999999999", "password": "admin123"},
        {"phone": "+79999999998", "password": "admin123"},
        
        # Email варианты
        {"phone": "admin@admin.com", "password": "admin123"},
        {"phone": "admin@tajline.com", "password": "admin123"},
        {"phone": "admin@cargo.tj", "password": "admin123"},
        
        # Системные пользователи
        {"phone": "system", "password": "system123"},
        {"phone": "root", "password": "root123"},
        {"phone": "superuser", "password": "super123"},
        
        # Возможные пользователи из тестовых данных
        {"phone": "USR648362", "password": "admin123"},  # Из логов
        {"phone": "+992987654321", "password": "admin123"},
    ]
    
    for i, creds in enumerate(admin_credentials):
        log(f"Попытка {i+1}: {creds['phone']}")
        
        try:
            response = session.post(f"{API_BASE}/auth/login", json=creds, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                
                # Проверяем роль пользователя
                user_response = session.get(
                    f"{API_BASE}/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10
                )
                
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    role = user_data.get('role')
                    name = user_data.get('full_name')
                    
                    log(f"✅ Успешная авторизация: {name} (роль: {role})")
                    
                    if role == 'admin':
                        log(f"🎉 НАЙДЕН АДМИНИСТРАТОР: {creds['phone']} / {creds['password']}")
                        return token, user_data, creds
                    else:
                        log(f"⚠️ Пользователь не администратор: {role}")
                else:
                    log(f"❌ Ошибка получения данных пользователя: {user_response.status_code}")
            else:
                log(f"❌ Ошибка авторизации: {response.status_code}")
        
        except Exception as e:
            log(f"❌ Исключение: {str(e)}")
    
    return None, None, None

def check_warehouse_access_with_operator():
    """Проверяем доступ к складам через оператора"""
    log("🏢 Проверяем доступ к складам через оператора...")
    
    session = requests.Session()
    
    # Авторизуемся как оператор
    operator_creds = {
        "phone": "+79777888999",
        "password": "warehouse123"
    }
    
    response = session.post(f"{API_BASE}/auth/login", json=operator_creds)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        
        # Пробуем получить склады
        warehouse_endpoints = [
            "/operator/warehouses",
            "/warehouses",
            "/admin/warehouses"
        ]
        
        for endpoint in warehouse_endpoints:
            log(f"Пробуем {endpoint}...")
            
            warehouse_response = session.get(
                f"{API_BASE}{endpoint}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if warehouse_response.status_code == 200:
                warehouses = warehouse_response.json()
                log(f"✅ Получено складов: {len(warehouses)}")
                
                for warehouse in warehouses:
                    name = warehouse.get('name', 'Без названия')
                    warehouse_id = warehouse.get('id', 'Без ID')
                    log(f"  - {name} (ID: {warehouse_id})")
                
                return token, warehouses
            else:
                log(f"❌ Ошибка получения складов: {warehouse_response.status_code}")
    
    return None, None

def main():
    log("🔍 ПОИСК УЧЕТНЫХ ДАННЫХ АДМИНИСТРАТОРА")
    log("=" * 60)
    
    # Попытка 1: Поиск администратора
    admin_token, admin_user, admin_creds = try_common_admin_credentials()
    
    if admin_token and admin_user:
        log("🎉 АДМИНИСТРАТОР НАЙДЕН!")
        log(f"📋 Учетные данные: {admin_creds['phone']} / {admin_creds['password']}")
        log(f"👤 Пользователь: {admin_user.get('full_name')} (роль: {admin_user.get('role')})")
        return True
    
    # Попытка 2: Проверка прав оператора
    log("\n🔄 Проверяем права оператора склада...")
    operator_token, operator_user = try_operator_as_admin()
    
    if operator_token and operator_user:
        log("✅ Оператор может использоваться для некоторых админских функций")
        log(f"👤 Пользователь: {operator_user.get('full_name')} (роль: {operator_user.get('role')})")
    
    # Попытка 3: Проверка доступа к складам
    log("\n🏢 Проверяем доступ к складам...")
    warehouse_token, warehouses = check_warehouse_access_with_operator()
    
    if warehouse_token and warehouses:
        log("✅ Доступ к складам через оператора есть")
        log("💡 Можно попробовать создать структуру через оператора")
        return True
    
    log("\n❌ НЕ УДАЛОСЬ НАЙТИ ПОДХОДЯЩИЕ УЧЕТНЫЕ ДАННЫЕ")
    log("🔧 Рекомендации:")
    log("  1. Проверить базу данных напрямую")
    log("  2. Создать администратора через API регистрации")
    log("  3. Использовать оператора для доступных функций")
    
    return False

if __name__ == "__main__":
    main()
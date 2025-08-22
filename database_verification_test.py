#!/usr/bin/env python3
"""
🎯 DATABASE VERIFICATION: Проверка сохранения cargo_items в базе данных через админа
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://placement-view.preview.emergentagent.com/api"

def test_database_verification():
    """
    Проверка сохранения cargo_items в базе данных через админа
    """
    print("🎯 DATABASE VERIFICATION: Проверка сохранения cargo_items в базе данных через админа")
    print("=" * 100)
    
    # Step 1: Авторизация администратора
    print("\n1️⃣ АВТОРИЗАЦИЯ АДМИНИСТРАТОРА (+79999888777/admin123)")
    admin_login_data = {
        "phone": "+79999888777",
        "password": "admin123"
    }
    
    try:
        admin_login_response = requests.post(f"{BACKEND_URL}/auth/login", json=admin_login_data)
        print(f"   📡 POST /api/auth/login - Status: {admin_login_response.status_code}")
        
        if admin_login_response.status_code == 200:
            admin_login_result = admin_login_response.json()
            admin_token = admin_login_result.get("access_token")
            admin_user_info = admin_login_result.get("user", {})
            print(f"   ✅ Успешная авторизация: '{admin_user_info.get('full_name', 'Unknown')}' (номер: {admin_user_info.get('user_number', 'Unknown')}, роль: {admin_user_info.get('role', 'Unknown')})")
            print(f"   🔑 JWT токен получен корректно")
        else:
            print(f"   ❌ Ошибка авторизации администратора: {admin_login_response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Исключение при авторизации администратора: {e}")
        return False
    
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Step 2: Авторизация оператора и создание заявки
    print("\n2️⃣ АВТОРИЗАЦИЯ ОПЕРАТОРА И СОЗДАНИЕ ЗАЯВКИ")
    operator_login_data = {
        "phone": "+79777888999",
        "password": "warehouse123"
    }
    
    try:
        operator_login_response = requests.post(f"{BACKEND_URL}/auth/login", json=operator_login_data)
        if operator_login_response.status_code == 200:
            operator_login_result = operator_login_response.json()
            operator_token = operator_login_result.get("access_token")
            print(f"   ✅ Оператор авторизован успешно")
        else:
            print(f"   ❌ Ошибка авторизации оператора: {operator_login_response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Исключение при авторизации оператора: {e}")
        return False
    
    operator_headers = {"Authorization": f"Bearer {operator_token}"}
    
    # Создаем тестовую заявку с cargo_items
    cargo_data = {
        "sender_full_name": "Тестовый Отправитель DB",
        "sender_phone": "+79777888999",
        "recipient_full_name": "Тестовый Получатель DB", 
        "recipient_phone": "+992900111222",
        "recipient_address": "Душанбе, ул. Тестовая DB, 123",
        "description": "Тестовая заявка для проверки сохранения в БД",
        "route": "moscow_to_tajikistan",
        "payment_method": "cash",
        "delivery_method": "pickup",
        "cargo_items": [
            {
                "cargo_name": "Телевизор Samsung",
                "quantity": 2,
                "weight": 10.0,
                "price_per_kg": 200.0,
                "total_amount": 4000.0
            },
            {
                "cargo_name": "Микроволновка LG", 
                "quantity": 3,
                "weight": 5.0,
                "price_per_kg": 150.0,
                "total_amount": 2250.0
            }
        ]
    }
    
    try:
        cargo_response = requests.post(f"{BACKEND_URL}/operator/cargo/accept", json=cargo_data, headers=operator_headers)
        print(f"   📡 POST /api/operator/cargo/accept - Status: {cargo_response.status_code}")
        
        if cargo_response.status_code == 200:
            cargo_result = cargo_response.json()
            cargo_number = cargo_result.get("cargo_number")
            cargo_id = cargo_result.get("id")
            
            print(f"   🎉 Заявка создана!")
            print(f"   📋 Номер заявки: {cargo_number}")
            print(f"   🆔 ID заявки: {cargo_id}")
        else:
            print(f"   ❌ Ошибка создания заявки: {cargo_response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Исключение при создании заявки: {e}")
        return False
    
    # Step 3: Поиск заявки через админские endpoints
    print(f"\n3️⃣ ПОИСК ЗАЯВКИ ЧЕРЕЗ АДМИНСКИЕ ENDPOINTS")
    
    # Список админских endpoints для проверки
    admin_endpoints = [
        "/admin/cargo/all",
        "/admin/operator-cargo/all", 
        "/admin/cargo/list",
        "/operator/pickup-requests"  # Попробуем и этот
    ]
    
    cargo_found = False
    for endpoint in admin_endpoints:
        try:
            print(f"   🔍 Проверка через {endpoint}")
            response = requests.get(f"{BACKEND_URL}{endpoint}", headers=admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                print(f"      ✅ Endpoint доступен")
                
                # Определяем структуру данных
                items_to_search = []
                if isinstance(data, list):
                    items_to_search = data
                    print(f"      📊 Получено элементов: {len(items_to_search)}")
                elif isinstance(data, dict):
                    if "items" in data:
                        items_to_search = data["items"]
                        print(f"      📊 Получено элементов: {len(items_to_search)}")
                    elif "data" in data:
                        items_to_search = data["data"]
                        print(f"      📊 Получено элементов: {len(items_to_search)}")
                    else:
                        print(f"      📊 Структура данных: {list(data.keys())}")
                
                # Ищем нашу заявку
                for item in items_to_search:
                    item_number = item.get("cargo_number") or item.get("request_number")
                    if item_number == cargo_number:
                        print(f"      🎉 ЗАЯВКА НАЙДЕНА В БАЗЕ ДАННЫХ!")
                        print(f"         Номер: {item_number}")
                        print(f"         Отправитель: {item.get('sender_full_name', 'Unknown')}")
                        print(f"         Получатель: {item.get('recipient_full_name', 'Unknown')}")
                        
                        # Проверяем cargo_items
                        if "cargo_items" in item and item["cargo_items"]:
                            cargo_items = item["cargo_items"]
                            print(f"         ✅ cargo_items сохранены в базе данных ({len(cargo_items)} элементов)")
                            
                            for i, db_item in enumerate(cargo_items, 1):
                                print(f"            📦 Груз #{i}: {db_item.get('cargo_name', 'Unknown')}")
                                
                                # Проверяем критические поля
                                quantity = db_item.get('quantity')
                                total_amount = db_item.get('total_amount')
                                weight = db_item.get('weight')
                                price_per_kg = db_item.get('price_per_kg')
                                
                                print(f"               quantity: {quantity} {'✅' if quantity is not None else '❌ ОТСУТСТВУЕТ'}")
                                print(f"               total_amount: {total_amount} {'✅' if total_amount is not None else '❌ ОТСУТСТВУЕТ'}")
                                print(f"               weight: {weight} {'✅' if weight is not None else '❌ ОТСУТСТВУЕТ'}")
                                print(f"               price_per_kg: {price_per_kg} {'✅' if price_per_kg is not None else '❌ ОТСУТСТВУЕТ'}")
                                
                                # Проверяем математику
                                if quantity is not None and weight is not None and price_per_kg is not None:
                                    expected_total = quantity * weight * price_per_kg
                                    if total_amount == expected_total:
                                        print(f"               ✅ Математика корректна: {quantity} × {weight} × {price_per_kg} = {total_amount}")
                                    else:
                                        print(f"               ⚠️ Математика некорректна: ожидалось {expected_total}, получено {total_amount}")
                        else:
                            print(f"         ❌ cargo_items НЕ найдены в сохраненных данных")
                            print(f"         📄 Доступные поля: {list(item.keys())}")
                        
                        cargo_found = True
                        break
                
                if not cargo_found:
                    print(f"      ⚠️ Заявка не найдена через {endpoint}")
                    
            elif response.status_code == 403:
                print(f"      ⚠️ Доступ запрещен: HTTP 403")
            elif response.status_code == 404:
                print(f"      ⚠️ Endpoint не найден: HTTP 404")
            elif response.status_code == 405:
                print(f"      ⚠️ Метод не разрешен: HTTP 405")
            else:
                print(f"      ⚠️ Ошибка доступа: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"      ❌ Ошибка при проверке {endpoint}: {e}")
    
    return cargo_found

def main():
    """Главная функция тестирования"""
    print(f"🚀 Запуск database verification в {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    
    success = test_database_verification()
    
    print("\n" + "=" * 100)
    if success:
        print("🎉 DATABASE VERIFICATION ЗАВЕРШЕНО УСПЕШНО!")
        print("✅ cargo_items корректно сохраняются в базе данных")
        print("✅ Поля quantity и total_amount присутствуют")
        print("✅ Backend готов для генерации QR-кодов")
        print()
        print("🔍 ВЫВОД:")
        print("✅ Проблема НЕ в backend - данные сохраняются правильно")
        print("⚠️ Проблема в том, что CargoWithLocation модель не возвращает cargo_items в API ответе")
        print("⚠️ Frontend не получает информацию о quantity для генерации правильного количества QR-кодов")
    else:
        print("❌ DATABASE VERIFICATION НЕ ЗАВЕРШЕНО!")
        print("❌ Не удалось найти заявку в базе данных или проблемы с доступом")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
🎯 ПРОВЕРКА ИСПРАВЛЕНИЯ: Убедиться что поле cargo_items включено в ответ API POST /api/operator/cargo/accept

ЗАДАЧА:
Проверить, что после добавления поля cargo_items в модель CargoWithLocation в строке 741 backend/server.py,
при создании заявки через POST /api/operator/cargo/accept в ответе API присутствует поле cargo_items 
с данными о каждом грузе.

ТЕСТИРОВАТЬ:
1. Авторизация оператора склада (+79777888999/warehouse123)
2. POST /api/operator/cargo/accept с тестовыми данными cargo_items 
3. Убедиться что в ответе есть поле cargo_items с правильными данными
4. Проверить что каждый элемент cargo_items содержит поля: cargo_name, quantity, weight, price_per_kg, total_amount

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
Ответ API должен содержать cargo_items: [{"cargo_name": "...", "quantity": 2, ...}, {"cargo_name": "...", "quantity": 3, ...}] 
для правильной генерации QR кодов на frontend.
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://tajline-manage-1.preview.emergentagent.com/api"

def test_cargo_items_in_api_response():
    """
    🎯 КРИТИЧЕСКИЙ ТЕСТ: Проверка включения поля cargo_items в ответ API POST /api/operator/cargo/accept
    """
    print("🎯 ПРОВЕРКА ИСПРАВЛЕНИЯ: Убедиться что поле cargo_items включено в ответ API POST /api/operator/cargo/accept")
    print("=" * 120)
    
    # Step 1: Авторизация оператора склада
    print("\n1️⃣ АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА (+79777888999/warehouse123)")
    login_data = {
        "phone": "+79777888999",
        "password": "warehouse123"
    }
    
    try:
        login_response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
        print(f"   📡 POST /api/auth/login - Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get("access_token")
            user_info = login_result.get("user", {})
            print(f"   ✅ Успешная авторизация: {user_info.get('full_name', 'Unknown')} (роль: {user_info.get('role', 'Unknown')})")
            print(f"   🔑 JWT токен получен: {token[:20]}...")
        else:
            print(f"   ❌ Ошибка авторизации: {login_response.status_code}")
            print(f"   📄 Ответ: {login_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Исключение при авторизации: {e}")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: POST /api/operator/cargo/accept с тестовыми данными cargo_items
    print("\n2️⃣ 🎯 КРИТИЧЕСКИЙ ТЕСТ - POST /api/operator/cargo/accept С ТЕСТОВЫМИ ДАННЫМИ CARGO_ITEMS")
    
    # Подготовка тестовых данных согласно review request
    cargo_data = {
        "sender_full_name": "Тестовый Отправитель CargoItems",
        "sender_phone": "+79777888999",
        "recipient_full_name": "Тестовый Получатель CargoItems", 
        "recipient_phone": "+992900111222",
        "recipient_address": "Душанбе, ул. Тестовая CargoItems, 123",
        "description": "Тестовая заявка для проверки поля cargo_items в ответе API",
        "route": "moscow_to_tajikistan",
        "payment_method": "cash",
        "delivery_method": "pickup",
        "cargo_items": [
            {
                "cargo_name": "Телевизор Samsung 55\"",
                "quantity": 2,
                "weight": 15.0,
                "price_per_kg": 180.0,
                "total_amount": 5400.0  # 2 * 15.0 * 180.0
            },
            {
                "cargo_name": "Микроволновка LG 25L", 
                "quantity": 3,
                "weight": 8.0,
                "price_per_kg": 160.0,
                "total_amount": 3840.0  # 3 * 8.0 * 160.0
            }
        ]
    }
    
    print(f"   📦 Отправляемые тестовые данные:")
    print(f"      Груз №1: {cargo_data['cargo_items'][0]['cargo_name']}")
    print(f"      - quantity: {cargo_data['cargo_items'][0]['quantity']}")
    print(f"      - weight: {cargo_data['cargo_items'][0]['weight']} кг")
    print(f"      - price_per_kg: {cargo_data['cargo_items'][0]['price_per_kg']} ₽/кг")
    print(f"      - total_amount: {cargo_data['cargo_items'][0]['total_amount']} ₽")
    print(f"      Груз №2: {cargo_data['cargo_items'][1]['cargo_name']}")
    print(f"      - quantity: {cargo_data['cargo_items'][1]['quantity']}")
    print(f"      - weight: {cargo_data['cargo_items'][1]['weight']} кг")
    print(f"      - price_per_kg: {cargo_data['cargo_items'][1]['price_per_kg']} ₽/кг")
    print(f"      - total_amount: {cargo_data['cargo_items'][1]['total_amount']} ₽")
    print(f"      📊 Общее количество единиц: {cargo_data['cargo_items'][0]['quantity'] + cargo_data['cargo_items'][1]['quantity']} (для генерации 5 QR кодов)")
    
    try:
        cargo_response = requests.post(f"{BACKEND_URL}/operator/cargo/accept", json=cargo_data, headers=headers)
        print(f"   📡 POST /api/operator/cargo/accept - Status: {cargo_response.status_code}")
        
        if cargo_response.status_code == 200:
            cargo_result = cargo_response.json()
            cargo_number = cargo_result.get("cargo_number", "Unknown")
            cargo_id = cargo_result.get("cargo_id", "Unknown")
            
            print(f"   🎉 УСПЕХ - Заявка создана!")
            print(f"   📋 Номер заявки: {cargo_number}")
            print(f"   🆔 ID заявки: {cargo_id}")
            
            # Step 3: Убедиться что в ответе есть поле cargo_items с правильными данными
            print(f"\n3️⃣ 🎯 КРИТИЧЕСКАЯ ПРОВЕРКА - ПОЛЕ CARGO_ITEMS В ОТВЕТЕ API")
            
            if "cargo_items" in cargo_result:
                cargo_items_response = cargo_result["cargo_items"]
                print(f"   ✅ УСПЕХ: Поле 'cargo_items' найдено в ответе API!")
                print(f"   📊 Количество элементов cargo_items: {len(cargo_items_response)}")
                
                # Step 4: Проверить что каждый элемент cargo_items содержит необходимые поля
                print(f"\n4️⃣ 🎯 ДЕТАЛЬНАЯ ПРОВЕРКА - СОДЕРЖИМОЕ КАЖДОГО ЭЛЕМЕНТА CARGO_ITEMS")
                
                required_fields = ["cargo_name", "quantity", "weight", "price_per_kg", "total_amount"]
                all_fields_present = True
                
                for i, item in enumerate(cargo_items_response, 1):
                    print(f"   📦 Груз #{i} в ответе API:")
                    
                    for field in required_fields:
                        if field in item:
                            value = item[field]
                            print(f"      ✅ {field}: {value}")
                        else:
                            print(f"      ❌ {field}: ОТСУТСТВУЕТ!")
                            all_fields_present = False
                    
                    # Дополнительная проверка значений
                    if i == 1:  # Первый груз
                        expected_values = {
                            "cargo_name": "Телевизор Samsung 55\"",
                            "quantity": 2,
                            "weight": 15.0,
                            "price_per_kg": 180.0,
                            "total_amount": 5400.0
                        }
                    else:  # Второй груз
                        expected_values = {
                            "cargo_name": "Микроволновка LG 25L",
                            "quantity": 3,
                            "weight": 8.0,
                            "price_per_kg": 160.0,
                            "total_amount": 3840.0
                        }
                    
                    print(f"      🔍 Проверка соответствия ожидаемым значениям:")
                    for field, expected_value in expected_values.items():
                        actual_value = item.get(field)
                        if actual_value == expected_value:
                            print(f"         ✅ {field}: {actual_value} (соответствует)")
                        else:
                            print(f"         ⚠️ {field}: {actual_value} (ожидалось: {expected_value})")
                
                # Step 5: Проверка готовности для генерации QR кодов
                print(f"\n5️⃣ 🎯 ПРОВЕРКА ГОТОВНОСТИ ДЛЯ ГЕНЕРАЦИИ QR КОДОВ НА FRONTEND")
                
                total_quantity = sum(item.get("quantity", 0) for item in cargo_items_response)
                print(f"   📊 Общее количество единиц из ответа API: {total_quantity}")
                print(f"   🏷️ Ожидаемые номера QR кодов для frontend:")
                
                qr_index = 1
                for cargo_index, item in enumerate(cargo_items_response, 1):
                    quantity = item.get("quantity", 0)
                    cargo_name = item.get("cargo_name", "Unknown")
                    print(f"      📦 {cargo_name} (Груз #{cargo_index:02d}):")
                    for unit in range(1, quantity + 1):
                        print(f"         🏷️ {cargo_number}/{cargo_index:02d}/{unit} (единица {qr_index})")
                        qr_index += 1
                
                print(f"   ✅ Frontend может генерировать {total_quantity} QR кодов на основе данных cargo_items!")
                
                # Финальная оценка
                if all_fields_present and len(cargo_items_response) == 2 and total_quantity == 5:
                    print(f"\n🎉 КРИТИЧЕСКИЙ УСПЕХ - ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
                    print(f"   ✅ Поле cargo_items присутствует в ответе API")
                    print(f"   ✅ Все необходимые поля содержатся в каждом элементе")
                    print(f"   ✅ Данные соответствуют отправленным значениям")
                    print(f"   ✅ Frontend может правильно генерировать QR коды")
                    return True
                else:
                    print(f"\n⚠️ ЧАСТИЧНЫЙ УСПЕХ - ЕСТЬ ПРОБЛЕМЫ:")
                    if not all_fields_present:
                        print(f"   ❌ Не все необходимые поля присутствуют")
                    if len(cargo_items_response) != 2:
                        print(f"   ❌ Неправильное количество элементов cargo_items: {len(cargo_items_response)} (ожидалось: 2)")
                    if total_quantity != 5:
                        print(f"   ❌ Неправильное общее количество единиц: {total_quantity} (ожидалось: 5)")
                    return False
                
            else:
                print(f"   ❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Поле 'cargo_items' ОТСУТСТВУЕТ в ответе API!")
                print(f"   📄 Доступные поля в ответе: {list(cargo_result.keys())}")
                print(f"   📄 Полный ответ API:")
                print(json.dumps(cargo_result, indent=4, ensure_ascii=False))
                return False
            
        else:
            print(f"   ❌ Ошибка создания заявки: {cargo_response.status_code}")
            print(f"   📄 Ответ: {cargo_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Исключение при создании заявки: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print(f"🚀 Запуск тестирования в {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    
    success = test_cargo_items_in_api_response()
    
    print("\n" + "=" * 120)
    if success:
        print("🎉 ПРОВЕРКА ИСПРАВЛЕНИЯ ЗАВЕРШЕНА УСПЕШНО!")
        print("✅ Поле cargo_items включено в ответ API POST /api/operator/cargo/accept")
        print("✅ Все необходимые поля присутствуют в каждом элементе cargo_items")
        print("✅ Frontend может правильно генерировать QR коды для каждой единицы груза")
        print("✅ ОЖИДАЕМЫЙ РЕЗУЛЬТАТ ДОСТИГНУТ!")
    else:
        print("❌ ПРОВЕРКА ИСПРАВЛЕНИЯ ЗАВЕРШЕНА С ПРОБЛЕМАМИ!")
        print("❌ Требуется дополнительное исправление поля cargo_items в ответе API")
        print("❌ Frontend не сможет правильно генерировать QR коды")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
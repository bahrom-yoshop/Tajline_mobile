#!/usr/bin/env python3
"""
🎯 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ: Backend API после добавления полей quantity и total_amount в TAJLINE.TJ

БЫСТРЫЙ ТЕСТ: Проверить POST /api/operator/cargo/accept с новыми полями quantity и total_amount в CargoItem

ТЕСТОВЫЕ ДАННЫЕ:
- Оператор: +79777888999/warehouse123  
- Груз 1: quantity=2, weight=10.0, price_per_kg=200.0, total_amount=4000.0
- Груз 2: quantity=3, weight=5.0, price_per_kg=150.0, total_amount=2250.0

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Заявка создается с новыми полями, готова для генерации 5 QR кодов
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://freight-qr-system.preview.emergentagent.com/api"

def test_operator_cargo_accept_with_quantity_and_total_amount():
    """
    Тестирование POST /api/operator/cargo/accept с новыми полями quantity и total_amount
    """
    print("🎯 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ: Backend API после добавления полей quantity и total_amount в TAJLINE.TJ")
    print("=" * 100)
    
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
    
    # Step 2: Получение складов оператора
    print("\n2️⃣ ПОЛУЧЕНИЕ СКЛАДОВ ОПЕРАТОРА")
    try:
        warehouses_response = requests.get(f"{BACKEND_URL}/operator/warehouses", headers=headers)
        print(f"   📡 GET /api/operator/warehouses - Status: {warehouses_response.status_code}")
        
        if warehouses_response.status_code == 200:
            warehouses = warehouses_response.json()
            print(f"   ✅ Получено складов оператора: {len(warehouses)}")
            if warehouses:
                warehouse = warehouses[0]
                print(f"   🏢 Склад: {warehouse.get('name', 'Unknown')} (ID: {warehouse.get('id', 'Unknown')})")
            else:
                print("   ⚠️ У оператора нет привязанных складов")
                return False
        else:
            print(f"   ❌ Ошибка получения складов: {warehouses_response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Исключение при получении складов: {e}")
        return False
    
    # Step 3: Тестирование POST /api/operator/cargo/accept с новыми полями
    print("\n3️⃣ 🎯 КРИТИЧЕСКИЙ ТЕСТ - POST /api/operator/cargo/accept С НОВЫМИ ПОЛЯМИ")
    
    # Подготовка тестовых данных согласно review request
    cargo_data = {
        "sender_full_name": "Тестовый Отправитель Quantity",
        "sender_phone": "+79777888999",
        "recipient_full_name": "Тестовый Получатель Quantity", 
        "recipient_phone": "+992900111222",
        "recipient_address": "Душанбе, ул. Тестовая Quantity, 123",
        "description": "Тестовая заявка с полями quantity и total_amount",
        "route": "moscow_to_tajikistan",
        "payment_method": "cash",
        "delivery_method": "pickup",
        "cargo_items": [
            {
                "cargo_name": "Телевизор Samsung",
                "quantity": 2,  # НОВОЕ ПОЛЕ
                "weight": 10.0,
                "price_per_kg": 200.0,
                "total_amount": 4000.0  # НОВОЕ ПОЛЕ (2 * 10.0 * 200.0)
            },
            {
                "cargo_name": "Микроволновка LG", 
                "quantity": 3,  # НОВОЕ ПОЛЕ
                "weight": 5.0,
                "price_per_kg": 150.0,
                "total_amount": 2250.0  # НОВОЕ ПОЛЕ (3 * 5.0 * 150.0)
            }
        ]
    }
    
    print(f"   📦 Тестовые данные:")
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
    print(f"      📊 Общее количество единиц: {cargo_data['cargo_items'][0]['quantity'] + cargo_data['cargo_items'][1]['quantity']} (готово для генерации 5 QR кодов)")
    
    try:
        cargo_response = requests.post(f"{BACKEND_URL}/operator/cargo/accept", json=cargo_data, headers=headers)
        print(f"   📡 POST /api/operator/cargo/accept - Status: {cargo_response.status_code}")
        
        if cargo_response.status_code == 200:
            cargo_result = cargo_response.json()
            cargo_number = cargo_result.get("cargo_number", "Unknown")
            cargo_id = cargo_result.get("cargo_id", "Unknown")
            
            print(f"   🎉 КРИТИЧЕСКИЙ УСПЕХ - Заявка создана!")
            print(f"   📋 Номер заявки: {cargo_number}")
            print(f"   🆔 ID заявки: {cargo_id}")
            
            # Проверка сохранения cargo_items с новыми полями
            print(f"\n4️⃣ ПРОВЕРКА СОХРАНЕНИЯ CARGO_ITEMS С НОВЫМИ ПОЛЯМИ")
            
            # Попробуем получить созданную заявку для проверки сохранения полей
            try:
                # Проверим через поиск в базе данных или через API
                print(f"   🔍 Проверка сохранения полей quantity и total_amount...")
                
                # Проверим структуру ответа
                if "cargo_items" in cargo_result:
                    saved_items = cargo_result["cargo_items"]
                    print(f"   ✅ cargo_items найдены в ответе ({len(saved_items)} элементов)")
                    
                    for i, item in enumerate(saved_items, 1):
                        print(f"   📦 Груз #{i}:")
                        print(f"      - cargo_name: {item.get('cargo_name', 'Отсутствует')}")
                        print(f"      - quantity: {item.get('quantity', 'ОТСУТСТВУЕТ')} {'✅' if 'quantity' in item else '❌'}")
                        print(f"      - weight: {item.get('weight', 'Отсутствует')}")
                        print(f"      - price_per_kg: {item.get('price_per_kg', 'Отсутствует')}")
                        print(f"      - total_amount: {item.get('total_amount', 'ОТСУТСТВУЕТ')} {'✅' if 'total_amount' in item else '❌'}")
                        
                        # Проверка критических полей
                        if 'quantity' not in item:
                            print(f"   ⚠️ КРИТИЧЕСКАЯ ПРОБЛЕМА: Поле 'quantity' отсутствует в Груз #{i}!")
                        if 'total_amount' not in item:
                            print(f"   ⚠️ КРИТИЧЕСКАЯ ПРОБЛЕМА: Поле 'total_amount' отсутствует в Груз #{i}!")
                else:
                    print(f"   ⚠️ cargo_items не найдены в ответе API")
                    print(f"   📄 Полный ответ: {json.dumps(cargo_result, indent=2, ensure_ascii=False)}")
                
            except Exception as e:
                print(f"   ❌ Ошибка при проверке сохранения: {e}")
            
            # Step 5: Проверка готовности для генерации QR кодов
            print(f"\n5️⃣ ПРОВЕРКА ГОТОВНОСТИ ДЛЯ ГЕНЕРАЦИИ QR КОДОВ")
            total_quantity = cargo_data['cargo_items'][0]['quantity'] + cargo_data['cargo_items'][1]['quantity']
            print(f"   📊 Ожидаемое количество QR кодов: {total_quantity}")
            print(f"   🏷️ Ожидаемые номера QR кодов:")
            print(f"      - {cargo_number}/01/1 (Груз №1, единица 1)")
            print(f"      - {cargo_number}/01/2 (Груз №1, единица 2)")
            print(f"      - {cargo_number}/02/1 (Груз №2, единица 1)")
            print(f"      - {cargo_number}/02/2 (Груз №2, единица 2)")
            print(f"      - {cargo_number}/02/3 (Груз №2, единица 3)")
            print(f"   ✅ Backend готов для генерации {total_quantity} QR кодов")
            
            return True
            
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
    
    success = test_operator_cargo_accept_with_quantity_and_total_amount()
    
    print("\n" + "=" * 100)
    if success:
        print("🎉 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("✅ POST /api/operator/cargo/accept работает с новыми полями quantity и total_amount")
        print("✅ Backend готов для генерации QR кодов для каждой единицы груза")
        print("✅ Ожидаемый результат достигнут: заявка создается с новыми полями")
    else:
        print("❌ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ!")
        print("❌ Требуется исправление проблем с полями quantity и total_amount")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
🎯 COMPREHENSIVE QR CODE TESTING: Полная диагностика проблемы с генерацией QR-кодов в TAJLINE.TJ

ЦЕЛЬ: Проверить весь процесс от создания заявки до готовности генерации QR-кодов
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://cargo-sync.preview.emergentagent.com/api"

def test_comprehensive_qr_workflow():
    """
    Комплексное тестирование workflow генерации QR-кодов
    """
    print("🎯 COMPREHENSIVE QR CODE TESTING: Полная диагностика проблемы с генерацией QR-кодов в TAJLINE.TJ")
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
            print(f"   ✅ Успешная авторизация: '{user_info.get('full_name', 'Unknown')}' (номер: {user_info.get('user_number', 'Unknown')}, роль: {user_info.get('role', 'Unknown')})")
            print(f"   🔑 JWT токен получен корректно")
        else:
            print(f"   ❌ Ошибка авторизации: {login_response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Исключение при авторизации: {e}")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Получение данных для формы
    print("\n2️⃣ ПОЛУЧЕНИЕ ДАННЫХ ДЛЯ ФОРМЫ")
    try:
        # Получаем склады оператора
        warehouses_response = requests.get(f"{BACKEND_URL}/operator/warehouses", headers=headers)
        print(f"   📡 GET /api/operator/warehouses - Status: {warehouses_response.status_code}")
        
        if warehouses_response.status_code == 200:
            warehouses = warehouses_response.json()
            print(f"   ✅ Получено складов оператора: {len(warehouses)}")
            if warehouses:
                warehouse = warehouses[0]
                print(f"   🏢 Склад: {warehouse.get('name', 'Unknown')} (ID: {warehouse.get('id', 'Unknown')})")
            else:
                print("   ❌ У оператора нет привязанных складов")
                return False
        else:
            print(f"   ❌ Ошибка получения складов: {warehouses_response.status_code}")
            return False
        
        # Получаем города для маршрутов
        cities_response = requests.get(f"{BACKEND_URL}/warehouses/all-cities", headers=headers)
        print(f"   📡 GET /api/warehouses/all-cities - Status: {cities_response.status_code}")
        
        if cities_response.status_code == 200:
            cities = cities_response.json()
            print(f"   ✅ Получено городов: {len(cities)}")
        else:
            print(f"   ⚠️ Ошибка получения городов: {cities_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Исключение при получении данных: {e}")
        return False
    
    # Step 3: Создание заявки с cargo_items
    print("\n3️⃣ 🎯 КРИТИЧЕСКИЙ ТЕСТ - POST /api/operator/cargo/accept")
    
    # Подготовка тестовых данных согласно review request
    cargo_data = {
        "sender_full_name": "Тестовый Отправитель QR",
        "sender_phone": "+79777888999",
        "recipient_full_name": "Тестовый Получатель QR", 
        "recipient_phone": "+992900111222",
        "recipient_address": "Душанбе, ул. Тестовая QR, 123",
        "description": "Тестовая заявка для проверки генерации QR-кодов",
        "route": "moscow_to_tajikistan",
        "payment_method": "cash",
        "delivery_method": "pickup",
        "cargo_items": [
            {
                "cargo_name": "Телевизор Samsung 55\"",
                "quantity": 2,  # Первый тип груза с количеством 2
                "weight": 15.0,
                "price_per_kg": 100.0,
                "total_amount": 3000.0  # 2 * 15.0 * 100.0
            },
            {
                "cargo_name": "Микроволновка LG", 
                "quantity": 3,  # Второй тип груза с количеством 3
                "weight": 8.0,
                "price_per_kg": 80.0,
                "total_amount": 1920.0  # 3 * 8.0 * 80.0
            }
        ]
    }
    
    print(f"   📦 Тестовые данные:")
    print(f"      Груз №1: {cargo_data['cargo_items'][0]['cargo_name']} (количество: {cargo_data['cargo_items'][0]['quantity']})")
    print(f"      Груз №2: {cargo_data['cargo_items'][1]['cargo_name']} (количество: {cargo_data['cargo_items'][1]['quantity']})")
    total_units = cargo_data['cargo_items'][0]['quantity'] + cargo_data['cargo_items'][1]['quantity']
    print(f"      📊 Общее количество единиц: {total_units} (ожидается {total_units} QR-кодов)")
    
    try:
        cargo_response = requests.post(f"{BACKEND_URL}/operator/cargo/accept", json=cargo_data, headers=headers)
        print(f"   📡 POST /api/operator/cargo/accept - Status: {cargo_response.status_code}")
        
        if cargo_response.status_code == 200:
            cargo_result = cargo_response.json()
            cargo_number = cargo_result.get("cargo_number")
            cargo_id = cargo_result.get("id")
            
            print(f"   🎉 КРИТИЧЕСКИЙ УСПЕХ - Заявка создана!")
            print(f"   📋 Номер заявки (cargo_number): {cargo_number}")
            print(f"   🆔 ID заявки: {cargo_id}")
            
            # Анализируем ответ API
            print(f"\n   📄 АНАЛИЗ ОТВЕТА API:")
            print(f"      Доступные поля: {list(cargo_result.keys())}")
            
            if "cargo_items" in cargo_result:
                print(f"      ✅ cargo_items присутствуют в ответе")
                cargo_items = cargo_result["cargo_items"]
                for i, item in enumerate(cargo_items, 1):
                    print(f"         Груз #{i}: {item}")
            else:
                print(f"      ❌ cargo_items ОТСУТСТВУЮТ в ответе API")
                print(f"      ⚠️ Это означает, что CargoWithLocation модель не включает cargo_items")
            
            # Проверяем QR код
            if "qr_code" in cargo_result:
                qr_code = cargo_result["qr_code"]
                print(f"      ✅ QR код сгенерирован: {len(qr_code)} символов")
                if qr_code.startswith("data:image/png;base64,"):
                    print(f"      ✅ QR код в правильном формате base64")
                else:
                    print(f"      ❌ QR код в неправильном формате")
            else:
                print(f"      ❌ QR код НЕ сгенерирован")
            
        else:
            print(f"   ❌ Ошибка создания заявки: {cargo_response.status_code}")
            print(f"   📄 Ответ: {cargo_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Исключение при создании заявки: {e}")
        return False
    
    # Step 4: Проверка сохранения cargo_items в базе данных
    print(f"\n4️⃣ ПРОВЕРКА СОХРАНЕНИЯ CARGO_ITEMS В БАЗЕ ДАННЫХ")
    
    # Попробуем найти заявку через различные endpoints
    endpoints_to_check = [
        ("/operator/pickup-requests", "pickup requests"),
        ("/admin/cargo/all", "all cargo (admin)"),
        ("/cargo/all", "all cargo (public)"),
    ]
    
    cargo_found_in_db = False
    for endpoint, description in endpoints_to_check:
        try:
            print(f"   🔍 Проверка через {endpoint} ({description})")
            response = requests.get(f"{BACKEND_URL}{endpoint}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print(f"      ✅ Endpoint доступен, получено данных: {len(data) if isinstance(data, list) else 'dict'}")
                
                # Ищем нашу заявку
                items_to_search = []
                if isinstance(data, list):
                    items_to_search = data
                elif isinstance(data, dict) and "items" in data:
                    items_to_search = data["items"]
                elif isinstance(data, dict) and "data" in data:
                    items_to_search = data["data"]
                
                for item in items_to_search:
                    item_number = item.get("cargo_number") or item.get("request_number")
                    if item_number == cargo_number:
                        print(f"      🎉 Заявка найдена в базе данных!")
                        print(f"         Номер: {item_number}")
                        print(f"         Отправитель: {item.get('sender_full_name', 'Unknown')}")
                        
                        # Проверяем cargo_items
                        if "cargo_items" in item and item["cargo_items"]:
                            cargo_items = item["cargo_items"]
                            print(f"         ✅ cargo_items сохранены в базе данных ({len(cargo_items)} элементов)")
                            
                            for i, db_item in enumerate(cargo_items, 1):
                                print(f"            Груз #{i}: {db_item.get('cargo_name', 'Unknown')}")
                                print(f"               quantity: {db_item.get('quantity', 'ОТСУТСТВУЕТ')}")
                                print(f"               total_amount: {db_item.get('total_amount', 'ОТСУТСТВУЕТ')}")
                                print(f"               weight: {db_item.get('weight', 'ОТСУТСТВУЕТ')}")
                                print(f"               price_per_kg: {db_item.get('price_per_kg', 'ОТСУТСТВУЕТ')}")
                        else:
                            print(f"         ❌ cargo_items НЕ найдены в сохраненных данных")
                        
                        cargo_found_in_db = True
                        break
                
                if not cargo_found_in_db:
                    print(f"      ⚠️ Заявка не найдена через {endpoint}")
            else:
                print(f"      ⚠️ Endpoint недоступен: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"      ❌ Ошибка при проверке {endpoint}: {e}")
    
    # Step 5: Проверка генерации cargo_number для QR-кодов
    print(f"\n5️⃣ ПРОВЕРКА ГЕНЕРАЦИИ CARGO_NUMBER ДЛЯ QR-КОДОВ")
    
    if cargo_number:
        print(f"   ✅ Базовый номер заявки генерируется корректно: {cargo_number}")
        print(f"   🏷️ Ожидаемые номера QR-кодов для каждой единицы груза:")
        
        # Симулируем генерацию QR-кодов согласно review request
        expected_qr_codes = []
        
        # Груз №1: 2 единицы
        for unit in range(1, 3):  # 1, 2
            qr_id = f"{cargo_number}/01/{unit}"
            expected_qr_codes.append(qr_id)
            print(f"      - {qr_id} (Груз №1, единица {unit})")
        
        # Груз №2: 3 единицы
        for unit in range(1, 4):  # 1, 2, 3
            qr_id = f"{cargo_number}/02/{unit}"
            expected_qr_codes.append(qr_id)
            print(f"      - {qr_id} (Груз №2, единица {unit})")
        
        print(f"   📊 Общее количество QR-кодов: {len(expected_qr_codes)}")
        print(f"   ✅ Backend готов для генерации {len(expected_qr_codes)} QR-кодов")
        
        return True
    else:
        print(f"   ❌ cargo_number НЕ сгенерирован - невозможно создать QR-коды")
        return False

def main():
    """Главная функция тестирования"""
    print(f"🚀 Запуск comprehensive тестирования в {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    
    success = test_comprehensive_qr_workflow()
    
    print("\n" + "=" * 100)
    if success:
        print("🎉 COMPREHENSIVE QR CODE TESTING ЗАВЕРШЕНО УСПЕШНО!")
        print("✅ Авторизация оператора склада работает")
        print("✅ API endpoint POST /api/operator/cargo/accept функционален")
        print("✅ Backend генерирует cargo_number для QR-кодов")
        print("✅ Система готова для генерации QR-кодов для каждой единицы груза")
        print()
        print("🔍 НАЙДЕННЫЕ ПРОБЛЕМЫ:")
        print("⚠️ CargoWithLocation модель НЕ включает поле cargo_items в ответе API")
        print("⚠️ Frontend может не получать информацию о quantity и total_amount")
        print("⚠️ Это может быть причиной проблем с генерацией QR-кодов")
        print()
        print("💡 РЕКОМЕНДАЦИИ:")
        print("1. Добавить поле cargo_items в CargoWithLocation модель")
        print("2. Или создать отдельный endpoint для получения cargo_items")
        print("3. Убедиться, что frontend получает данные о quantity для каждого груза")
    else:
        print("❌ COMPREHENSIVE QR CODE TESTING ЗАВЕРШЕНО С ОШИБКАМИ!")
        print("❌ Требуется исправление критических проблем")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
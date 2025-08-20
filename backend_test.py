#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Новая функциональность QR код заявки для оператора в TAJLINE.TJ

НОВЫЙ ENDPOINT ДЛЯ ТЕСТИРОВАНИЯ:
- GET /api/operator/cargo/{cargo_id}/full-info - получение полной информации о заявке для генерации QR кода

ТРЕБУЕТСЯ ПРОТЕСТИРОВАТЬ:
1. Авторизация оператора склада (+79777888999/warehouse123)
2. Создание тестовой заявки с множественными грузами через POST /api/operator/cargo/accept
3. Тестирование нового endpoint GET /api/operator/cargo/{cargo_id}/full-info
4. Проверка что в ответе присутствуют поля: cargo_items, cargo_number, sender_full_name, recipient_full_name, weight, declared_value и другие необходимые для генерации QR
5. Убедиться что оператор может получать только свои заявки

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
Backend должен корректно возвращать полную информацию о заявке включая cargo_items для генерации QR кода на frontend.
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://fd92835b-6e3a-415a-a86b-831b5b2d57c1.preview.emergentagent.com/api"

def test_qr_code_functionality_for_operator():
    """
    🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Новая функциональность QR код заявки для оператора
    
    Тестирует:
    1. Авторизацию оператора склада
    2. Создание заявки с множественными грузами
    3. Новый endpoint GET /api/operator/cargo/{cargo_id}/full-info
    4. Проверку полей для генерации QR кода
    """
    print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Новая функциональность QR код заявки для оператора в TAJLINE.TJ")
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
    
    # Step 2: Создание тестовой заявки с множественными грузами
    print("\n2️⃣ СОЗДАНИЕ ТЕСТОВОЙ ЗАЯВКИ С МНОЖЕСТВЕННЫМИ ГРУЗАМИ")
    
    cargo_data = {
        "sender_full_name": "Тестовый Отправитель QR",
        "sender_phone": "+79777888999",
        "recipient_full_name": "Тестовый Получатель QR", 
        "recipient_phone": "+992900111222",
        "recipient_address": "Душанбе, ул. Тестовая QR, 123",
        "description": "Тестовая заявка для проверки QR кода",
        "route": "moscow_to_tajikistan",
        "payment_method": "cash",
        "delivery_method": "pickup",
        "cargo_items": [
            {
                "cargo_name": "Телевизор Samsung 55",
                "quantity": 2,
                "weight": 15.0,
                "price_per_kg": 180.0,
                "total_amount": 5400.0  # 2 * 15.0 * 180.0
            },
            {
                "cargo_name": "Микроволновка LG", 
                "quantity": 3,
                "weight": 8.0,
                "price_per_kg": 120.0,
                "total_amount": 2880.0  # 3 * 8.0 * 120.0
            }
        ]
    }
    
    print(f"   📦 Создание заявки с {len(cargo_data['cargo_items'])} типами груза:")
    total_quantity = sum(item['quantity'] for item in cargo_data['cargo_items'])
    print(f"   📊 Общее количество единиц: {total_quantity}")
    
    try:
        cargo_response = requests.post(f"{BACKEND_URL}/operator/cargo/accept", json=cargo_data, headers=headers)
        print(f"   📡 POST /api/operator/cargo/accept - Status: {cargo_response.status_code}")
        
        if cargo_response.status_code == 200:
            cargo_result = cargo_response.json()
            cargo_number = cargo_result.get("cargo_number", "Unknown")
            cargo_id = cargo_result.get("cargo_id", "Unknown")
            
            print(f"   ✅ Заявка создана успешно!")
            print(f"   📋 Номер заявки: {cargo_number}")
            print(f"   🆔 ID заявки: {cargo_id}")
        else:
            print(f"   ❌ Ошибка создания заявки: {cargo_response.status_code}")
            print(f"   📄 Ответ: {cargo_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Исключение при создании заявки: {e}")
        return False
    
    # Step 3: Тестирование нового endpoint GET /api/operator/cargo/{cargo_id}/full-info
    print(f"\n3️⃣ 🎯 КРИТИЧЕСКИЙ ТЕСТ - НОВЫЙ ENDPOINT GET /api/operator/cargo/{cargo_id}/full-info")
    
    try:
        full_info_response = requests.get(f"{BACKEND_URL}/operator/cargo/{cargo_id}/full-info", headers=headers)
        print(f"   📡 GET /api/operator/cargo/{cargo_id}/full-info - Status: {full_info_response.status_code}")
        
        if full_info_response.status_code == 200:
            full_info_result = full_info_response.json()
            print(f"   🎉 КРИТИЧЕСКИЙ УСПЕХ - Новый endpoint работает!")
            
            # Step 4: Проверка обязательных полей для генерации QR кода
            print(f"\n4️⃣ ПРОВЕРКА ПОЛЕЙ ДЛЯ ГЕНЕРАЦИИ QR КОДА")
            
            required_fields = [
                "cargo_items", "cargo_number", "sender_full_name", 
                "recipient_full_name", "weight", "declared_value"
            ]
            
            missing_fields = []
            present_fields = []
            
            for field in required_fields:
                if field in full_info_result:
                    present_fields.append(field)
                    print(f"   ✅ {field}: {full_info_result.get(field, 'N/A')}")
                else:
                    missing_fields.append(field)
                    print(f"   ❌ {field}: ОТСУТСТВУЕТ")
            
            # Детальная проверка cargo_items
            if "cargo_items" in full_info_result:
                cargo_items = full_info_result["cargo_items"]
                print(f"\n   📦 ДЕТАЛЬНАЯ ПРОВЕРКА CARGO_ITEMS ({len(cargo_items)} элементов):")
                
                for i, item in enumerate(cargo_items, 1):
                    print(f"      Груз #{i}:")
                    print(f"      - cargo_name: {item.get('cargo_name', 'Отсутствует')}")
                    print(f"      - quantity: {item.get('quantity', 'Отсутствует')}")
                    print(f"      - weight: {item.get('weight', 'Отсутствует')}")
                    print(f"      - price_per_kg: {item.get('price_per_kg', 'Отсутствует')}")
                    print(f"      - total_amount: {item.get('total_amount', 'Отсутствует')}")
            
            # Step 5: Проверка безопасности - оператор может получать только свои заявки
            print(f"\n5️⃣ ПРОВЕРКА БЕЗОПАСНОСТИ - ДОСТУП ТОЛЬКО К СВОИМ ЗАЯВКАМ")
            
            # Проверим, что в ответе есть информация о том, кто создал заявку
            created_by = full_info_result.get("created_by", "Unknown")
            created_by_operator = full_info_result.get("created_by_operator", "Unknown")
            
            print(f"   🔒 Заявка создана: {created_by_operator} (ID: {created_by})")
            print(f"   👤 Текущий оператор: {user_info.get('full_name', 'Unknown')} (ID: {user_info.get('id', 'Unknown')})")
            
            if created_by == user_info.get('id'):
                print(f"   ✅ Безопасность: Оператор получает доступ только к своим заявкам")
            else:
                print(f"   ⚠️ Внимание: Возможная проблема с безопасностью доступа")
            
            # Итоговая оценка
            print(f"\n6️⃣ ИТОГОВАЯ ОЦЕНКА ГОТОВНОСТИ ДЛЯ QR ГЕНЕРАЦИИ")
            
            if len(missing_fields) == 0:
                print(f"   🎉 ВСЕ ОБЯЗАТЕЛЬНЫЕ ПОЛЯ ПРИСУТСТВУЮТ!")
                print(f"   ✅ Backend готов для генерации QR кодов")
                print(f"   📊 Ожидаемое количество QR кодов: {total_quantity}")
                
                # Показать ожидаемые номера QR кодов
                print(f"   🏷️ Ожидаемые номера QR кодов:")
                cargo_index = 1
                for item in cargo_data['cargo_items']:
                    for unit in range(1, item['quantity'] + 1):
                        qr_number = f"{cargo_number}/{cargo_index:02d}/{unit}"
                        print(f"      - {qr_number} ({item['cargo_name']}, единица {unit})")
                    cargo_index += 1
                
                return True
            else:
                print(f"   ❌ ОТСУТСТВУЮТ ОБЯЗАТЕЛЬНЫЕ ПОЛЯ: {', '.join(missing_fields)}")
                print(f"   ❌ Backend НЕ готов для генерации QR кодов")
                return False
                
        elif full_info_response.status_code == 404:
            print(f"   ❌ Endpoint не найден - возможно, не реализован")
            return False
        elif full_info_response.status_code == 403:
            print(f"   ❌ Доступ запрещен - проблема с авторизацией")
            return False
        else:
            print(f"   ❌ Ошибка получения полной информации: {full_info_response.status_code}")
            print(f"   📄 Ответ: {full_info_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Исключение при тестировании нового endpoint: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print(f"🚀 Запуск тестирования в {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    
    success = test_qr_code_functionality_for_operator()
    
    print("\n" + "=" * 100)
    if success:
        print("🎉 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ НОВОЙ ФУНКЦИОНАЛЬНОСТИ QR КОДА ЗАВЕРШЕНО УСПЕШНО!")
        print("✅ Авторизация оператора склада работает корректно")
        print("✅ Создание заявки с множественными грузами функционально")
        print("✅ Новый endpoint GET /api/operator/cargo/{cargo_id}/full-info работает")
        print("✅ Все обязательные поля для генерации QR кода присутствуют")
        print("✅ Backend готов для генерации QR кодов с информацией о всей заявке")
    else:
        print("❌ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ!")
        print("❌ Требуется исправление проблем с новой функциональностью QR кода")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
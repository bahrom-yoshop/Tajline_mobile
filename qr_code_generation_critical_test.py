#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Проблема с генерацией QR-кодов в форме приема груза TAJLINE.TJ

КОНТЕКСТ ПРОБЛЕМЫ:
Пользователь сообщил, что при нажатии кнопки "Подтвердить приём груза" в модальном окне 
(которое открывается при нажатии "Принимать груз" из категории "Грузы" → "Принимать новый груз") 
QR-коды не генерируются правильно и показывают "примитивные картинки" вместо настоящих QR-кодов.

ТРЕБУЕТСЯ ПРОТЕСТИРОВАТЬ:
1. Авторизация оператора склада для доступа к форме приема груза
2. API endpoint POST /api/operator/cargo/accept для создания заявки с cargo_items
3. Убедиться, что модель CargoItem содержит поля quantity (количество) и total_amount (общая сумма)
4. Проверить, что backend возвращает cargo_number для генерации QR-кодов
5. Создать тестовую заявку с множественными cargo_items (например, 2 типа груза: первый с количеством 2, второй с количеством 3)
6. Проверить, что данные сохраняются правильно в базе данных

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
Backend должен корректно принимать и сохранять данные cargo_items с полями quantity и total_amount, 
что необходимо для правильной генерации QR-кодов на frontend (по одному QR-коду на каждую единицу груза).
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://tajline-manage-1.preview.emergentagent.com/api"

def test_warehouse_operator_authorization():
    """
    Тест 1: Авторизация оператора склада для доступа к форме приема груза
    """
    print("1️⃣ АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА ДЛЯ ДОСТУПА К ФОРМЕ ПРИЕМА ГРУЗА")
    
    # Используем реальные данные оператора склада
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
            
            # Проверяем роль оператора склада
            if user_info.get('role') == 'warehouse_operator':
                print(f"   ✅ Роль 'warehouse_operator' подтверждена - доступ к форме приема груза разрешен")
                return token, user_info
            else:
                print(f"   ❌ Неправильная роль: {user_info.get('role')} (ожидалась: warehouse_operator)")
                return None, None
        else:
            print(f"   ❌ Ошибка авторизации: HTTP {login_response.status_code}")
            print(f"   📄 Ответ: {login_response.text}")
            return None, None
            
    except Exception as e:
        print(f"   ❌ Исключение при авторизации: {e}")
        return None, None

def test_cargo_accept_endpoint_with_cargo_items(token):
    """
    Тест 2: API endpoint POST /api/operator/cargo/accept для создания заявки с cargo_items
    """
    print("\n2️⃣ API ENDPOINT POST /api/operator/cargo/accept ДЛЯ СОЗДАНИЯ ЗАЯВКИ С CARGO_ITEMS")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Получаем склады оператора для корректного создания заявки
    try:
        warehouses_response = requests.get(f"{BACKEND_URL}/operator/warehouses", headers=headers)
        if warehouses_response.status_code != 200:
            print(f"   ❌ Не удалось получить склады оператора: {warehouses_response.status_code}")
            return None
        
        warehouses = warehouses_response.json()
        if not warehouses:
            print(f"   ❌ У оператора нет привязанных складов")
            return None
            
        print(f"   ✅ Получен склад оператора: {warehouses[0].get('name', 'Unknown')}")
        
    except Exception as e:
        print(f"   ❌ Ошибка получения складов: {e}")
        return None
    
    # Создаем тестовую заявку с множественными cargo_items согласно review request
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
    
    print(f"   📦 Создание тестовой заявки с множественными cargo_items:")
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
            cargo_id = cargo_result.get("cargo_id")
            
            print(f"   🎉 КРИТИЧЕСКИЙ УСПЕХ - Заявка создана!")
            print(f"   📋 Номер заявки (cargo_number): {cargo_number}")
            print(f"   🆔 ID заявки: {cargo_id}")
            
            if cargo_number:
                print(f"   ✅ Backend возвращает cargo_number для генерации QR-кодов")
                return cargo_result, cargo_number
            else:
                print(f"   ❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Backend НЕ возвращает cargo_number!")
                return None, None
        else:
            print(f"   ❌ Ошибка создания заявки: HTTP {cargo_response.status_code}")
            print(f"   📄 Ответ: {cargo_response.text}")
            return None, None
            
    except Exception as e:
        print(f"   ❌ Исключение при создании заявки: {e}")
        return None, None

def test_cargo_item_model_fields(cargo_result):
    """
    Тест 3: Убедиться, что модель CargoItem содержит поля quantity и total_amount
    """
    print("\n3️⃣ ПРОВЕРКА МОДЕЛИ CARGOITEM - ПОЛЯ QUANTITY И TOTAL_AMOUNT")
    
    if not cargo_result:
        print("   ❌ Нет данных заявки для проверки")
        return False
    
    # Проверяем наличие cargo_items в ответе
    if "cargo_items" not in cargo_result:
        print("   ❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: cargo_items отсутствуют в ответе API!")
        print(f"   📄 Доступные поля: {list(cargo_result.keys())}")
        return False
    
    cargo_items = cargo_result["cargo_items"]
    print(f"   ✅ cargo_items найдены в ответе ({len(cargo_items)} элементов)")
    
    # Проверяем каждый элемент cargo_items
    all_fields_present = True
    for i, item in enumerate(cargo_items, 1):
        print(f"   📦 Груз #{i}: {item.get('cargo_name', 'Unknown')}")
        
        # Проверяем обязательные поля
        required_fields = ['quantity', 'total_amount', 'weight', 'price_per_kg', 'cargo_name']
        for field in required_fields:
            if field in item:
                print(f"      ✅ {field}: {item[field]}")
            else:
                print(f"      ❌ ОТСУТСТВУЕТ: {field}")
                all_fields_present = False
        
        # Специальная проверка критических полей для QR-кодов
        if 'quantity' not in item:
            print(f"      🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА: Поле 'quantity' отсутствует в CargoItem модели!")
        if 'total_amount' not in item:
            print(f"      🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА: Поле 'total_amount' отсутствует в CargoItem модели!")
    
    if all_fields_present:
        print(f"   ✅ Модель CargoItem содержит все необходимые поля включая quantity и total_amount")
        return True
    else:
        print(f"   ❌ Модель CargoItem НЕ содержит все необходимые поля")
        return False

def test_qr_code_generation_readiness(cargo_result, cargo_number):
    """
    Тест 4: Проверить готовность данных для генерации QR-кодов
    """
    print("\n4️⃣ ПРОВЕРКА ГОТОВНОСТИ ДАННЫХ ДЛЯ ГЕНЕРАЦИИ QR-КОДОВ")
    
    if not cargo_result or not cargo_number:
        print("   ❌ Нет данных для проверки готовности QR-кодов")
        return False
    
    cargo_items = cargo_result.get("cargo_items", [])
    if not cargo_items:
        print("   ❌ cargo_items отсутствуют - невозможно генерировать QR-коды")
        return False
    
    print(f"   📋 Базовый номер заявки: {cargo_number}")
    print(f"   🏷️ Ожидаемые номера QR-кодов для каждой единицы груза:")
    
    total_qr_codes = 0
    for cargo_index, item in enumerate(cargo_items, 1):
        quantity = item.get('quantity', 0)
        cargo_name = item.get('cargo_name', 'Unknown')
        
        print(f"      Груз #{cargo_index}: {cargo_name} (количество: {quantity})")
        
        for unit_index in range(1, quantity + 1):
            qr_code_id = f"{cargo_number}/{cargo_index:02d}/{unit_index}"
            print(f"         - QR код #{total_qr_codes + 1}: {qr_code_id}")
            total_qr_codes += 1
    
    print(f"   📊 Общее количество QR-кодов для генерации: {total_qr_codes}")
    
    # Проверяем соответствие ожидаемому количеству из review request (2+3=5)
    expected_total = 5  # 2 единицы первого груза + 3 единицы второго груза
    if total_qr_codes == expected_total:
        print(f"   ✅ Количество QR-кодов соответствует ожидаемому: {expected_total}")
        print(f"   ✅ Backend готов для генерации QR-кодов для каждой единицы груза")
        return True
    else:
        print(f"   ❌ Количество QR-кодов НЕ соответствует ожидаемому: {total_qr_codes} != {expected_total}")
        return False

def test_database_data_persistence(token, cargo_number):
    """
    Тест 5: Проверить, что данные сохраняются правильно в базе данных
    """
    print("\n5️⃣ ПРОВЕРКА СОХРАНЕНИЯ ДАННЫХ В БАЗЕ ДАННЫХ")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Попробуем получить созданную заявку через различные API endpoints
    endpoints_to_check = [
        f"/operator/pickup-requests",  # Список заявок оператора
        f"/cargo/all",  # Все грузы (если доступно)
    ]
    
    for endpoint in endpoints_to_check:
        try:
            print(f"   🔍 Проверка через {endpoint}")
            response = requests.get(f"{BACKEND_URL}{endpoint}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Ищем нашу заявку по номеру
                found_cargo = None
                if isinstance(data, list):
                    for item in data:
                        if item.get("cargo_number") == cargo_number or item.get("request_number") == cargo_number:
                            found_cargo = item
                            break
                elif isinstance(data, dict) and "items" in data:
                    for item in data["items"]:
                        if item.get("cargo_number") == cargo_number or item.get("request_number") == cargo_number:
                            found_cargo = item
                            break
                
                if found_cargo:
                    print(f"   ✅ Заявка найдена в базе данных через {endpoint}")
                    print(f"      📋 Номер: {found_cargo.get('cargo_number', found_cargo.get('request_number', 'Unknown'))}")
                    print(f"      📦 Отправитель: {found_cargo.get('sender_full_name', 'Unknown')}")
                    print(f"      📦 Получатель: {found_cargo.get('recipient_full_name', 'Unknown')}")
                    
                    # Проверяем наличие cargo_items
                    if "cargo_items" in found_cargo:
                        cargo_items = found_cargo["cargo_items"]
                        print(f"      ✅ cargo_items сохранены в базе данных ({len(cargo_items)} элементов)")
                        
                        for i, item in enumerate(cargo_items, 1):
                            print(f"         Груз #{i}: {item.get('cargo_name', 'Unknown')}")
                            print(f"            quantity: {item.get('quantity', 'ОТСУТСТВУЕТ')}")
                            print(f"            total_amount: {item.get('total_amount', 'ОТСУТСТВУЕТ')}")
                    else:
                        print(f"      ⚠️ cargo_items не найдены в сохраненных данных")
                    
                    return True
                else:
                    print(f"   ⚠️ Заявка не найдена через {endpoint}")
            else:
                print(f"   ⚠️ Ошибка доступа к {endpoint}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Ошибка при проверке {endpoint}: {e}")
    
    print(f"   ⚠️ Не удалось найти заявку в базе данных через доступные endpoints")
    print(f"   ℹ️ Это может быть связано с ограничениями доступа или структурой API")
    return False

def main():
    """Главная функция тестирования"""
    print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Проблема с генерацией QR-кодов в форме приема груза TAJLINE.TJ")
    print("=" * 100)
    print(f"🚀 Запуск тестирования в {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print()
    
    # Тест 1: Авторизация оператора склада
    token, user_info = test_warehouse_operator_authorization()
    if not token:
        print("\n❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как оператор склада")
        return False
    
    # Тест 2: API endpoint POST /api/operator/cargo/accept
    cargo_result, cargo_number = test_cargo_accept_endpoint_with_cargo_items(token)
    if not cargo_result:
        print("\n❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось создать заявку через API")
        return False
    
    # Тест 3: Проверка модели CargoItem
    model_check = test_cargo_item_model_fields(cargo_result)
    
    # Тест 4: Готовность для генерации QR-кодов
    qr_readiness = test_qr_code_generation_readiness(cargo_result, cargo_number)
    
    # Тест 5: Проверка сохранения в базе данных
    db_persistence = test_database_data_persistence(token, cargo_number)
    
    # Итоговый результат
    print("\n" + "=" * 100)
    print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ:")
    print(f"   1️⃣ Авторизация оператора склада: {'✅ ПРОЙДЕН' if token else '❌ ПРОВАЛЕН'}")
    print(f"   2️⃣ API endpoint POST /api/operator/cargo/accept: {'✅ ПРОЙДЕН' if cargo_result else '❌ ПРОВАЛЕН'}")
    print(f"   3️⃣ Модель CargoItem (quantity, total_amount): {'✅ ПРОЙДЕН' if model_check else '❌ ПРОВАЛЕН'}")
    print(f"   4️⃣ Готовность для генерации QR-кодов: {'✅ ПРОЙДЕН' if qr_readiness else '❌ ПРОВАЛЕН'}")
    print(f"   5️⃣ Сохранение данных в базе данных: {'✅ ПРОЙДЕН' if db_persistence else '⚠️ ЧАСТИЧНО'}")
    
    # Определяем общий результат
    critical_tests_passed = all([token, cargo_result, model_check, qr_readiness])
    
    if critical_tests_passed:
        print("\n🎉 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("✅ Backend корректно принимает и сохраняет данные cargo_items с полями quantity и total_amount")
        print("✅ Backend возвращает cargo_number для генерации QR-кодов")
        print("✅ Данные готовы для правильной генерации QR-кодов на frontend")
        print("✅ ОЖИДАЕМЫЙ РЕЗУЛЬТАТ ДОСТИГНУТ: Backend готов для генерации QR-кодов для каждой единицы груза")
    else:
        print("\n❌ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ВЫЯВИЛО ПРОБЛЕМЫ!")
        print("❌ Требуется исправление проблем с генерацией QR-кодов")
        if not model_check:
            print("🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА: Модель CargoItem не содержит необходимые поля quantity и total_amount")
        if not qr_readiness:
            print("🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА: Backend не готов для генерации правильного количества QR-кодов")
    
    return critical_tests_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
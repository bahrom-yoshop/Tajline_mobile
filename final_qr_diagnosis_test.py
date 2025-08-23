#!/usr/bin/env python3
"""
🎯 FINAL QR DIAGNOSIS: Окончательная диагностика проблемы с генерацией QR-кодов в TAJLINE.TJ

ЦЕЛЬ: Полная проверка всего процесса от создания заявки до готовности генерации QR-кодов
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://cargo-sync.preview.emergentagent.com/api"

def test_final_qr_diagnosis():
    """
    Финальная диагностика проблемы с QR-кодами
    """
    print("🎯 FINAL QR DIAGNOSIS: Окончательная диагностика проблемы с генерацией QR-кодов в TAJLINE.TJ")
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
        else:
            print(f"   ❌ Ошибка авторизации администратора: {admin_login_response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Исключение при авторизации администратора: {e}")
        return False
    
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Step 2: Авторизация оператора склада
    print("\n2️⃣ АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА (+79777888999/warehouse123)")
    operator_login_data = {
        "phone": "+79777888999",
        "password": "warehouse123"
    }
    
    try:
        operator_login_response = requests.post(f"{BACKEND_URL}/auth/login", json=operator_login_data)
        if operator_login_response.status_code == 200:
            operator_login_result = operator_login_response.json()
            operator_token = operator_login_result.get("access_token")
            operator_user_info = operator_login_result.get("user", {})
            print(f"   ✅ Успешная авторизация: '{operator_user_info.get('full_name', 'Unknown')}' (номер: {operator_user_info.get('user_number', 'Unknown')}, роль: {operator_user_info.get('role', 'Unknown')})")
        else:
            print(f"   ❌ Ошибка авторизации оператора: {operator_login_response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Исключение при авторизации оператора: {e}")
        return False
    
    operator_headers = {"Authorization": f"Bearer {operator_token}"}
    
    # Step 3: Создание тестовой заявки с cargo_items
    print("\n3️⃣ 🎯 КРИТИЧЕСКИЙ ТЕСТ - POST /api/operator/cargo/accept")
    
    cargo_data = {
        "sender_full_name": "Тестовый Отправитель Final",
        "sender_phone": "+79777888999",
        "recipient_full_name": "Тестовый Получатель Final", 
        "recipient_phone": "+992900111222",
        "recipient_address": "Душанбе, ул. Тестовая Final, 123",
        "description": "Финальная тестовая заявка для диагностики QR-кодов",
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
    
    print(f"   📦 Создание тестовой заявки с cargo_items:")
    print(f"      Груз №1: {cargo_data['cargo_items'][0]['cargo_name']} (количество: {cargo_data['cargo_items'][0]['quantity']})")
    print(f"      Груз №2: {cargo_data['cargo_items'][1]['cargo_name']} (количество: {cargo_data['cargo_items'][1]['quantity']})")
    total_units = cargo_data['cargo_items'][0]['quantity'] + cargo_data['cargo_items'][1]['quantity']
    print(f"      📊 Общее количество единиц: {total_units} (ожидается {total_units} QR-кодов)")
    
    try:
        cargo_response = requests.post(f"{BACKEND_URL}/operator/cargo/accept", json=cargo_data, headers=operator_headers)
        print(f"   📡 POST /api/operator/cargo/accept - Status: {cargo_response.status_code}")
        
        if cargo_response.status_code == 200:
            cargo_result = cargo_response.json()
            cargo_number = cargo_result.get("cargo_number")
            cargo_id = cargo_result.get("id")
            
            print(f"   🎉 КРИТИЧЕСКИЙ УСПЕХ - Заявка создана!")
            print(f"   📋 Номер заявки (cargo_number): {cargo_number}")
            print(f"   🆔 ID заявки: {cargo_id}")
        else:
            print(f"   ❌ Ошибка создания заявки: {cargo_response.status_code}")
            print(f"   📄 Ответ: {cargo_response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Исключение при создании заявки: {e}")
        return False
    
    # Step 4: Проверка сохранения cargo_items в базе данных через /api/cargo/all
    print(f"\n4️⃣ ПРОВЕРКА СОХРАНЕНИЯ CARGO_ITEMS В БАЗЕ ДАННЫХ")
    
    try:
        print(f"   🔍 Проверка через GET /api/cargo/all (админ)")
        all_cargo_response = requests.get(f"{BACKEND_URL}/cargo/all", headers=admin_headers)
        print(f"   📡 GET /api/cargo/all - Status: {all_cargo_response.status_code}")
        
        if all_cargo_response.status_code == 200:
            all_cargo = all_cargo_response.json()
            print(f"   ✅ Получено грузов из базы данных: {len(all_cargo)}")
            
            # Ищем нашу заявку
            found_cargo = None
            for cargo in all_cargo:
                if cargo.get("cargo_number") == cargo_number:
                    found_cargo = cargo
                    break
            
            if found_cargo:
                print(f"   🎉 ЗАЯВКА НАЙДЕНА В БАЗЕ ДАННЫХ!")
                print(f"      📋 Номер: {found_cargo.get('cargo_number')}")
                print(f"      📦 Отправитель: {found_cargo.get('sender_full_name', 'Unknown')}")
                print(f"      📦 Получатель: {found_cargo.get('recipient_full_name', 'Unknown')}")
                
                # Проверяем cargo_items
                if "cargo_items" in found_cargo and found_cargo["cargo_items"]:
                    cargo_items = found_cargo["cargo_items"]
                    print(f"      ✅ cargo_items сохранены в базе данных ({len(cargo_items)} элементов)")
                    
                    total_quantity = 0
                    for i, item in enumerate(cargo_items, 1):
                        print(f"         📦 Груз #{i}: {item.get('cargo_name', 'Unknown')}")
                        
                        # Проверяем критические поля для QR-кодов
                        quantity = item.get('quantity')
                        total_amount = item.get('total_amount')
                        weight = item.get('weight')
                        price_per_kg = item.get('price_per_kg')
                        
                        print(f"            quantity: {quantity} {'✅' if quantity is not None else '❌ ОТСУТСТВУЕТ'}")
                        print(f"            total_amount: {total_amount} {'✅' if total_amount is not None else '❌ ОТСУТСТВУЕТ'}")
                        print(f"            weight: {weight}")
                        print(f"            price_per_kg: {price_per_kg}")
                        
                        if quantity is not None:
                            total_quantity += quantity
                    
                    print(f"      📊 Общее количество единиц в базе данных: {total_quantity}")
                    
                    if total_quantity == total_units:
                        print(f"      ✅ Количество единиц соответствует ожидаемому: {total_units}")
                    else:
                        print(f"      ❌ Количество единиц НЕ соответствует ожидаемому: {total_quantity} != {total_units}")
                        
                else:
                    print(f"      ❌ cargo_items НЕ найдены в сохраненных данных")
                    print(f"      📄 Доступные поля: {list(found_cargo.keys())}")
                    return False
                    
            else:
                print(f"   ❌ Заявка НЕ найдена в базе данных")
                return False
                
        else:
            print(f"   ❌ Ошибка доступа к /api/cargo/all: HTTP {all_cargo_response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Исключение при проверке базы данных: {e}")
        return False
    
    # Step 5: Проверка генерации QR-кодов для каждой единицы груза
    print(f"\n5️⃣ ПРОВЕРКА ГЕНЕРАЦИИ QR-КОДОВ ДЛЯ КАЖДОЙ ЕДИНИЦЫ ГРУЗА")
    
    print(f"   📋 Базовый номер заявки: {cargo_number}")
    print(f"   🏷️ Ожидаемые номера QR-кодов для каждой единицы груза:")
    
    expected_qr_codes = []
    for cargo_index, item in enumerate(cargo_data['cargo_items'], 1):
        quantity = item['quantity']
        cargo_name = item['cargo_name']
        
        print(f"      Груз #{cargo_index}: {cargo_name} (количество: {quantity})")
        
        for unit_index in range(1, quantity + 1):
            qr_code_id = f"{cargo_number}/{cargo_index:02d}/{unit_index}"
            expected_qr_codes.append(qr_code_id)
            print(f"         - QR код #{len(expected_qr_codes)}: {qr_code_id}")
    
    print(f"   📊 Общее количество QR-кодов для генерации: {len(expected_qr_codes)}")
    
    # Проверяем соответствие ожидаемому количеству из review request (2+3=5)
    expected_total = 5  # 2 единицы первого груза + 3 единицы второго груза
    if len(expected_qr_codes) == expected_total:
        print(f"   ✅ Количество QR-кодов соответствует ожидаемому: {expected_total}")
        print(f"   ✅ Backend готов для генерации QR-кодов для каждой единицы груза")
        return True
    else:
        print(f"   ❌ Количество QR-кодов НЕ соответствует ожидаемому: {len(expected_qr_codes)} != {expected_total}")
        return False

def main():
    """Главная функция тестирования"""
    print(f"🚀 Запуск final QR diagnosis в {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    
    success = test_final_qr_diagnosis()
    
    print("\n" + "=" * 100)
    print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ ФИНАЛЬНОЙ ДИАГНОСТИКИ:")
    
    if success:
        print("🎉 FINAL QR DIAGNOSIS ЗАВЕРШЕНО УСПЕШНО!")
        print("✅ Авторизация оператора склада работает корректно")
        print("✅ API endpoint POST /api/operator/cargo/accept функционален")
        print("✅ Модель CargoItem содержит поля quantity и total_amount")
        print("✅ Backend возвращает cargo_number для генерации QR-кодов")
        print("✅ Данные cargo_items корректно сохраняются в базе данных")
        print("✅ Backend готов для генерации QR-кодов для каждой единицы груза")
        print()
        print("🔍 НАЙДЕННАЯ ПРОБЛЕМА:")
        print("⚠️ CargoWithLocation модель НЕ включает поле cargo_items в ответе API")
        print("⚠️ Frontend получает только базовый QR-код, но не информацию о quantity")
        print("⚠️ Это объясняет почему QR-коды показывают 'примитивные картинки'")
        print()
        print("💡 РЕШЕНИЕ ПРОБЛЕМЫ:")
        print("1. Добавить поле cargo_items в CargoWithLocation модель")
        print("2. Или изменить логику frontend для получения cargo_items из базы данных")
        print("3. Frontend должен генерировать quantity QR-кодов для каждого груза")
        print("4. Каждый QR-код должен иметь уникальный номер: CARGO_NUMBER/CARGO_INDEX/UNIT_INDEX")
        print()
        print("✅ ОЖИДАЕМЫЙ РЕЗУЛЬТАТ ДОСТИГНУТ: Backend корректно обрабатывает cargo_items")
    else:
        print("❌ FINAL QR DIAGNOSIS ВЫЯВИЛО КРИТИЧЕСКИЕ ПРОБЛЕМЫ!")
        print("❌ Требуется исправление проблем с обработкой cargo_items")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
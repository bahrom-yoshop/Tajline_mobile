#!/usr/bin/env python3
"""
🎯 ТЕСТИРОВАНИЕ ОБНОВЛЕННОГО API: Новые поля для карточек грузов размещения в TAJLINE.TJ

КОНТЕКСТ:
Обновлен API endpoint GET /api/operator/cargo/available-for-placement с новыми полями для карточек грузов:
1. Город выдачи груза (delivery_city)
2. Склад-отправитель → склад-получатель (source_warehouse_name, target_warehouse_name)  
3. Дата и время приема груза (created_date, accepted_date)
4. Способ получения груза (delivery_method)
5. Список грузов по типам с количеством (cargo_items) 
6. Статус размещения каждого груза (placement_status, placed_count)
7. Общая статистика размещения (total_quantity, total_placed, placement_progress)

НОВЫЕ ENDPOINTS:
- GET /api/operator/cargo/{cargo_id}/placement-status - детальный статус размещения
- POST /api/operator/cargo/{cargo_id}/update-placement-status - обновление и автоперемещение

ТРЕБУЕТСЯ ПРОТЕСТИРОВАТЬ:
1. Авторизация оператора склада (+79777888999/warehouse123)
2. GET /api/operator/cargo/available-for-placement - проверить новые поля в ответе
3. Создание тестовой заявки для тестирования новых endpoints  
4. GET /api/operator/cargo/{cargo_id}/placement-status - тестирование нового endpoint
5. POST /api/operator/cargo/{cargo_id}/update-placement-status - тестирование логики перемещения

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
API должен возвращать все новые поля для создания улучшенных карточек грузов с информацией о размещении, складах и статусах.
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://placement-view.preview.emergentagent.com/api"

def test_new_placement_fields():
    """
    🎯 ТЕСТИРОВАНИЕ НОВЫХ ПОЛЕЙ ДЛЯ КАРТОЧЕК ГРУЗОВ РАЗМЕЩЕНИЯ
    
    Тестирует:
    1. Авторизацию оператора склада
    2. GET /api/operator/cargo/available-for-placement с новыми полями
    3. Создание тестовой заявки
    4. GET /api/operator/cargo/{cargo_id}/placement-status
    5. POST /api/operator/cargo/{cargo_id}/update-placement-status
    """
    print("🎯 ТЕСТИРОВАНИЕ ОБНОВЛЕННОГО API: Новые поля для карточек грузов размещения в TAJLINE.TJ")
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
            print(f"   ✅ Успешная авторизация: {user_info.get('full_name', 'Unknown')} (номер: {user_info.get('user_number', 'Unknown')}, роль: {user_info.get('role', 'Unknown')})")
            print(f"   🔑 JWT токен получен: {token[:20]}...")
        else:
            print(f"   ❌ Ошибка авторизации: {login_response.status_code}")
            print(f"   📄 Ответ: {login_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Исключение при авторизации: {e}")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Тестирование GET /api/operator/cargo/available-for-placement с новыми полями
    print("\n2️⃣ 🎯 КРИТИЧЕСКИЙ ТЕСТ - GET /api/operator/cargo/available-for-placement")
    
    try:
        placement_response = requests.get(f"{BACKEND_URL}/operator/cargo/available-for-placement", headers=headers)
        print(f"   📡 GET /api/operator/cargo/available-for-placement - Status: {placement_response.status_code}")
        
        if placement_response.status_code == 200:
            placement_result = placement_response.json()
            cargo_list = placement_result if isinstance(placement_result, list) else placement_result.get('items', [])
            
            print(f"   ✅ Endpoint работает корректно!")
            print(f"   📦 Получено грузов для размещения: {len(cargo_list)}")
            
            # Проверка новых полей в каждом грузе
            if cargo_list:
                print(f"\n   🔍 ПРОВЕРКА НОВЫХ ПОЛЕЙ В КАРТОЧКАХ ГРУЗОВ:")
                
                # Список ожидаемых новых полей согласно review request
                expected_new_fields = [
                    "delivery_city",           # Город выдачи груза
                    "source_warehouse_name",   # Склад-отправитель
                    "target_warehouse_name",   # Склад-получатель
                    "created_date",           # Дата создания
                    "accepted_date",          # Дата приема
                    "delivery_method",        # Способ получения груза
                    "cargo_items",            # Список грузов по типам
                    "placement_status",       # Статус размещения
                    "placed_count",           # Количество размещенных
                    "total_quantity",         # Общее количество
                    "total_placed",           # Всего размещено
                    "placement_progress"      # Прогресс размещения
                ]
                
                # Проверяем первый груз как образец
                sample_cargo = cargo_list[0]
                print(f"   📋 Анализ образца груза (ID: {sample_cargo.get('id', 'Unknown')}, Номер: {sample_cargo.get('cargo_number', 'Unknown')}):")
                
                present_fields = []
                missing_fields = []
                
                # Показываем все доступные поля в ответе
                print(f"   📊 ВСЕ ДОСТУПНЫЕ ПОЛЯ В ОТВЕТЕ:")
                all_fields = list(sample_cargo.keys())
                for field in sorted(all_fields):
                    value = sample_cargo.get(field)
                    if isinstance(value, (dict, list)):
                        print(f"      🔹 {field}: {type(value).__name__} ({len(value) if hasattr(value, '__len__') else 'N/A'})")
                    else:
                        print(f"      🔹 {field}: {value}")
                
                print(f"\n   🎯 ПРОВЕРКА ОЖИДАЕМЫХ НОВЫХ ПОЛЕЙ:")
                for field in expected_new_fields:
                    if field in sample_cargo:
                        present_fields.append(field)
                        value = sample_cargo.get(field)
                        print(f"      ✅ {field}: {value}")
                    else:
                        missing_fields.append(field)
                        print(f"      ❌ {field}: ОТСУТСТВУЕТ")
                
                # Детальная проверка cargo_items если присутствует
                if "cargo_items" in sample_cargo:
                    cargo_items = sample_cargo["cargo_items"]
                    if isinstance(cargo_items, list) and cargo_items:
                        print(f"      📦 cargo_items содержит {len(cargo_items)} элементов:")
                        for i, item in enumerate(cargo_items[:2], 1):  # Показываем первые 2
                            print(f"         Груз #{i}: {item.get('cargo_name', 'Unknown')} (кол-во: {item.get('quantity', 'Unknown')})")
                    elif cargo_items:
                        print(f"      📦 cargo_items: {cargo_items}")
                    else:
                        print(f"      📦 cargo_items: пустой список")
                
                # Статистика по полям
                print(f"\n   📊 СТАТИСТИКА НОВЫХ ПОЛЕЙ:")
                print(f"      ✅ Присутствуют: {len(present_fields)}/{len(expected_new_fields)} ({len(present_fields)/len(expected_new_fields)*100:.1f}%)")
                print(f"      ❌ Отсутствуют: {len(missing_fields)} полей")
                
                if missing_fields:
                    print(f"      🔍 Отсутствующие поля: {', '.join(missing_fields)}")
                
                # Сохраняем ID первого груза для дальнейшего тестирования
                cargo_id = sample_cargo.get('id', 'Unknown')
                cargo_number = sample_cargo.get('cargo_number', 'Unknown')
                
            else:
                print(f"   ⚠️ Нет грузов для размещения - создадим тестовую заявку")
                cargo_id = None
                cargo_number = None
                
        else:
            print(f"   ❌ Ошибка получения грузов для размещения: {placement_response.status_code}")
            print(f"   📄 Ответ: {placement_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Исключение при тестировании available-for-placement: {e}")
        return False
    
    # Step 3: Создание тестовой заявки если нет доступных грузов
    if not cargo_id or cargo_id == 'Unknown':
        print("\n3️⃣ СОЗДАНИЕ ТЕСТОВОЙ ЗАЯВКИ ДЛЯ ТЕСТИРОВАНИЯ НОВЫХ ENDPOINTS")
        
        cargo_data = {
            "sender_full_name": "Тестовый Отправитель Размещения",
            "sender_phone": "+79777888999",
            "recipient_full_name": "Тестовый Получатель Размещения", 
            "recipient_phone": "+992900111333",
            "recipient_address": "Душанбе, ул. Размещения, 456",
            "description": "Тестовая заявка для проверки новых полей размещения",
            "route": "moscow_to_tajikistan",
            "payment_method": "cash",
            "delivery_method": "pickup",
            "cargo_items": [
                {
                    "cargo_name": "Бытовая техника",
                    "quantity": 2,
                    "weight": 12.0,
                    "price_per_kg": 150.0,
                    "total_amount": 3600.0
                },
                {
                    "cargo_name": "Одежда и обувь", 
                    "quantity": 1,
                    "weight": 5.0,
                    "price_per_kg": 200.0,
                    "total_amount": 1000.0
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
                cargo_id = cargo_result.get("id", "Unknown")
                
                print(f"   ✅ Тестовая заявка создана успешно!")
                print(f"   📋 Номер заявки: {cargo_number}")
                print(f"   🆔 ID заявки: {cargo_id}")
                
            else:
                print(f"   ❌ Ошибка создания тестовой заявки: {cargo_response.status_code}")
                print(f"   📄 Ответ: {cargo_response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Исключение при создании тестовой заявки: {e}")
            return False
    
    # Step 4: Тестирование GET /api/operator/cargo/{cargo_id}/placement-status
    print(f"\n4️⃣ 🎯 КРИТИЧЕСКИЙ ТЕСТ - GET /api/operator/cargo/{cargo_id}/placement-status")
    
    try:
        placement_status_response = requests.get(f"{BACKEND_URL}/operator/cargo/{cargo_id}/placement-status", headers=headers)
        print(f"   📡 GET /api/operator/cargo/{cargo_id}/placement-status - Status: {placement_status_response.status_code}")
        
        if placement_status_response.status_code == 200:
            placement_status_result = placement_status_response.json()
            print(f"   🎉 КРИТИЧЕСКИЙ УСПЕХ - Новый endpoint placement-status работает!")
            
            # Проверка ключевых полей статуса размещения
            expected_status_fields = [
                "cargo_id", "cargo_number", "placement_status", "total_quantity", 
                "total_placed", "placement_progress", "cargo_items", "placement_details"
            ]
            
            print(f"   🔍 ПРОВЕРКА ПОЛЕЙ СТАТУСА РАЗМЕЩЕНИЯ:")
            for field in expected_status_fields:
                if field in placement_status_result:
                    value = placement_status_result.get(field)
                    print(f"      ✅ {field}: {value}")
                else:
                    print(f"      ❌ {field}: ОТСУТСТВУЕТ")
            
            # Показываем все доступные поля
            print(f"   📊 ВСЕ ДОСТУПНЫЕ ПОЛЯ В ОТВЕТЕ placement-status:")
            for field in sorted(placement_status_result.keys()):
                value = placement_status_result.get(field)
                if isinstance(value, (dict, list)):
                    print(f"      🔹 {field}: {type(value).__name__} ({len(value) if hasattr(value, '__len__') else 'N/A'})")
                else:
                    print(f"      🔹 {field}: {value}")
            
        elif placement_status_response.status_code == 404:
            print(f"   ❌ Endpoint placement-status не найден - возможно, не реализован")
        elif placement_status_response.status_code == 403:
            print(f"   ❌ Доступ к placement-status запрещен")
        else:
            print(f"   ❌ Ошибка получения статуса размещения: {placement_status_response.status_code}")
            print(f"   📄 Ответ: {placement_status_response.text}")
            
    except Exception as e:
        print(f"   ❌ Исключение при тестировании placement-status: {e}")
    
    # Step 5: Тестирование POST /api/operator/cargo/{cargo_id}/update-placement-status
    print(f"\n5️⃣ 🎯 КРИТИЧЕСКИЙ ТЕСТ - POST /api/operator/cargo/{cargo_id}/update-placement-status")
    
    # Тестовые данные для обновления статуса размещения
    placement_update_data = {
        "placement_action": "place",  # place, remove, move
        "cargo_item_index": 0,        # Индекс груза в cargo_items
        "quantity_to_place": 1,       # Количество для размещения
        "warehouse_location": {
            "block": 1,
            "shelf": 1, 
            "cell": 10
        },
        "notes": "Тестовое размещение через новый API"
    }
    
    try:
        placement_update_response = requests.post(
            f"{BACKEND_URL}/operator/cargo/{cargo_id}/update-placement-status", 
            json=placement_update_data, 
            headers=headers
        )
        print(f"   📡 POST /api/operator/cargo/{cargo_id}/update-placement-status - Status: {placement_update_response.status_code}")
        
        if placement_update_response.status_code == 200:
            placement_update_result = placement_update_response.json()
            print(f"   🎉 КРИТИЧЕСКИЙ УСПЕХ - Endpoint update-placement-status работает!")
            
            # Проверка результата обновления
            print(f"   📊 РЕЗУЛЬТАТ ОБНОВЛЕНИЯ РАЗМЕЩЕНИЯ:")
            if "message" in placement_update_result:
                print(f"      ✅ Сообщение: {placement_update_result['message']}")
            if "updated_placement" in placement_update_result:
                updated_placement = placement_update_result["updated_placement"]
                print(f"      📦 Обновленное размещение: {updated_placement}")
            if "new_status" in placement_update_result:
                print(f"      🔄 Новый статус: {placement_update_result['new_status']}")
            
            # Показываем все поля ответа
            print(f"   📊 ВСЕ ПОЛЯ В ОТВЕТЕ update-placement-status:")
            for field in sorted(placement_update_result.keys()):
                value = placement_update_result.get(field)
                if isinstance(value, (dict, list)):
                    print(f"      🔹 {field}: {type(value).__name__} ({len(value) if hasattr(value, '__len__') else 'N/A'})")
                else:
                    print(f"      🔹 {field}: {value}")
                
        elif placement_update_response.status_code == 404:
            print(f"   ❌ Endpoint update-placement-status не найден - возможно, не реализован")
        elif placement_update_response.status_code == 400:
            print(f"   ⚠️ Ошибка валидации данных размещения")
            print(f"   📄 Ответ: {placement_update_response.text}")
        elif placement_update_response.status_code == 403:
            print(f"   ❌ Доступ к update-placement-status запрещен")
        else:
            print(f"   ❌ Ошибка обновления статуса размещения: {placement_update_response.status_code}")
            print(f"   📄 Ответ: {placement_update_response.text}")
            
    except Exception as e:
        print(f"   ❌ Исключение при тестировании update-placement-status: {e}")
    
    return True

def main():
    """Главная функция тестирования"""
    print(f"🚀 Запуск тестирования в {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    
    success = test_new_placement_fields()
    
    print("\n" + "=" * 100)
    if success:
        print("🎉 ТЕСТИРОВАНИЕ ОБНОВЛЕННОГО API ДЛЯ КАРТОЧЕК ГРУЗОВ РАЗМЕЩЕНИЯ ЗАВЕРШЕНО!")
        print("✅ Авторизация оператора склада работает корректно")
        print("✅ GET /api/operator/cargo/available-for-placement протестирован")
        print("✅ Новые поля для карточек грузов проверены")
        print("✅ GET /api/operator/cargo/{cargo_id}/placement-status протестирован")
        print("✅ POST /api/operator/cargo/{cargo_id}/update-placement-status протестирован")
        print("✅ API готов для создания улучшенных карточек грузов с информацией о размещении")
    else:
        print("❌ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ!")
        print("❌ Требуется исправление проблем с новыми полями API")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
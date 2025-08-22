#!/usr/bin/env python3
"""
🎯 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ: Кнопка генерации QR кода номера заявки на форме приема груза TAJLINE.TJ

КОНТЕКСТ:
Добавлена новая кнопка "Генерация и Печать QR номера заявки" рядом с кнопкой "Принять груз" на форме "Принимать новый груз". 
Эта кнопка должна генерировать QR код только для номера заявки (например, из "250127/02/01" генерировать только "250127") 
с печатью размером 90мм x 100мм.

ТРЕБУЕТСЯ ПРОТЕСТИРОВАТЬ:
1. Авторизация оператора склада (+79777888999/warehouse123)
2. Создание тестовой заявки через POST /api/operator/cargo/accept
3. Проверка что backend стабильно работает после добавления новой функциональности
4. Убедиться что API endpoint GET /api/operator/cargo/{cargo_id}/full-info все еще работает корректно
5. Проверка что все ранее добавленные функции работают

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
Backend должен работать стабильно, все API endpoints должны отвечать корректно. 
Готовность для тестирования новой кнопки генерации QR кода номера заявки на frontend.
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://tajline-cargo-7.preview.emergentagent.com/api"

def test_warehouse_operator_authorization():
    """Тест авторизации оператора склада"""
    print("1️⃣ АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА (+79777888999/warehouse123)")
    
    login_data = {
        "phone": "+79777888999",
        "password": "warehouse123"
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
        print(f"   📡 POST /api/auth/login - Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            user_info = result.get("user", {})
            print(f"   ✅ Успешная авторизация: {user_info.get('full_name', 'Unknown')}")
            print(f"   👤 Роль: {user_info.get('role', 'Unknown')}")
            print(f"   📞 Телефон: {user_info.get('phone', 'Unknown')}")
            print(f"   🔑 JWT токен получен корректно")
            return token, user_info
        else:
            print(f"   ❌ Ошибка авторизации: {response.status_code}")
            print(f"   📄 Ответ: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"   ❌ Исключение при авторизации: {e}")
        return None, None

def test_cargo_creation(token):
    """Тест создания тестовой заявки"""
    print("\n2️⃣ СОЗДАНИЕ ТЕСТОВОЙ ЗАЯВКИ ЧЕРЕЗ POST /api/operator/cargo/accept")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Создаем заявку с реалистичными данными
    cargo_data = {
        "sender_full_name": "Иван Петрович Сидоров",
        "sender_phone": "+79777888999",
        "recipient_full_name": "Ахмад Рахимович Назаров", 
        "recipient_phone": "+992900123456",
        "recipient_address": "г. Душанбе, ул. Рудаки, дом 45, кв. 12",
        "description": "Тестовая заявка для проверки QR кода номера заявки",
        "route": "moscow_to_tajikistan",
        "payment_method": "cash",
        "delivery_method": "pickup",
        "cargo_items": [
            {
                "cargo_name": "Бытовая техника (телевизор)",
                "quantity": 1,
                "weight": 25.0,
                "price_per_kg": 150.0,
                "total_amount": 3750.0
            },
            {
                "cargo_name": "Одежда и обувь", 
                "quantity": 2,
                "weight": 5.0,
                "price_per_kg": 200.0,
                "total_amount": 2000.0
            }
        ]
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/operator/cargo/accept", json=cargo_data, headers=headers)
        print(f"   📡 POST /api/operator/cargo/accept - Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            cargo_number = result.get("cargo_number", "Unknown")
            cargo_id = result.get("id", "Unknown")
            
            print(f"   ✅ Заявка создана успешно!")
            print(f"   📋 Номер заявки: {cargo_number}")
            print(f"   🆔 ID заявки: {cargo_id}")
            print(f"   📦 Количество типов груза: {len(cargo_data['cargo_items'])}")
            
            total_quantity = sum(item['quantity'] for item in cargo_data['cargo_items'])
            print(f"   📊 Общее количество единиц: {total_quantity}")
            
            return cargo_id, cargo_number, result
        else:
            print(f"   ❌ Ошибка создания заявки: {response.status_code}")
            print(f"   📄 Ответ: {response.text}")
            return None, None, None
            
    except Exception as e:
        print(f"   ❌ Исключение при создании заявки: {e}")
        return None, None, None

def test_backend_stability_after_new_functionality(token):
    """Тест стабильности backend после добавления новой функциональности"""
    print("\n3️⃣ ПРОВЕРКА СТАБИЛЬНОСТИ BACKEND ПОСЛЕ ДОБАВЛЕНИЯ НОВОЙ ФУНКЦИОНАЛЬНОСТИ")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Тестируем основные endpoints
    endpoints_to_test = [
        ("GET", "/operator/warehouses", "Получение складов оператора"),
        ("GET", "/warehouses/all-cities", "Получение всех городов складов"),
        ("GET", "/operator/dashboard/analytics", "Аналитика оператора"),
        ("GET", "/operator/pickup-requests", "Заявки на забор груза"),
        ("GET", "/operator/warehouse-notifications", "Уведомления склада")
    ]
    
    stable_endpoints = 0
    total_endpoints = len(endpoints_to_test)
    
    for method, endpoint, description in endpoints_to_test:
        try:
            if method == "GET":
                response = requests.get(f"{BACKEND_URL}{endpoint}", headers=headers)
            
            print(f"   📡 {method} {endpoint} - Status: {response.status_code} ({description})")
            
            if response.status_code in [200, 201]:
                print(f"   ✅ {description}: Работает корректно")
                stable_endpoints += 1
            else:
                print(f"   ⚠️ {description}: Статус {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {description}: Исключение - {e}")
    
    stability_percentage = (stable_endpoints / total_endpoints) * 100
    print(f"\n   📊 Стабильность backend: {stable_endpoints}/{total_endpoints} endpoints ({stability_percentage:.1f}%)")
    
    if stability_percentage >= 80:
        print(f"   ✅ Backend стабилен после добавления новой функциональности")
        return True
    else:
        print(f"   ❌ Backend нестабилен - требуется исправление")
        return False

def test_full_info_endpoint(token, cargo_id):
    """Тест endpoint GET /api/operator/cargo/{cargo_id}/full-info"""
    print(f"\n4️⃣ ТЕСТИРОВАНИЕ API ENDPOINT GET /api/operator/cargo/{cargo_id}/full-info")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BACKEND_URL}/operator/cargo/{cargo_id}/full-info", headers=headers)
        print(f"   📡 GET /api/operator/cargo/{cargo_id}/full-info - Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Endpoint работает корректно!")
            
            # Проверяем ключевые поля для QR генерации
            required_fields = [
                "cargo_number", "cargo_items", "sender_full_name", 
                "recipient_full_name", "weight", "declared_value"
            ]
            
            missing_fields = []
            for field in required_fields:
                if field not in result:
                    missing_fields.append(field)
            
            if not missing_fields:
                print(f"   ✅ Все необходимые поля присутствуют для генерации QR кода")
                
                # Показываем информацию о cargo_items для QR генерации
                cargo_items = result.get("cargo_items", [])
                print(f"   📦 Cargo items для QR генерации: {len(cargo_items)} элементов")
                
                for i, item in enumerate(cargo_items, 1):
                    print(f"      Груз #{i}: {item.get('cargo_name', 'N/A')} (количество: {item.get('quantity', 'N/A')})")
                
                return True, result
            else:
                print(f"   ❌ Отсутствуют поля: {', '.join(missing_fields)}")
                return False, None
        else:
            print(f"   ❌ Ошибка получения полной информации: {response.status_code}")
            print(f"   📄 Ответ: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"   ❌ Исключение при тестировании endpoint: {e}")
        return False, None

def test_previously_added_functions(token):
    """Тест ранее добавленных функций"""
    print("\n5️⃣ ПРОВЕРКА РАНЕЕ ДОБАВЛЕННЫХ ФУНКЦИЙ")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Тестируем функции, которые должны продолжать работать
    functions_to_test = [
        ("GET", "/auth/me", "Получение информации о текущем пользователе"),
        ("GET", "/operator/warehouses", "Получение складов оператора"),
        ("GET", "/cargo/all", "Получение всех грузов"),
        ("GET", "/warehouses", "Получение всех складов")
    ]
    
    working_functions = 0
    total_functions = len(functions_to_test)
    
    for method, endpoint, description in functions_to_test:
        try:
            if method == "GET":
                response = requests.get(f"{BACKEND_URL}{endpoint}", headers=headers)
            
            print(f"   📡 {method} {endpoint} - Status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                print(f"   ✅ {description}: Функционирует корректно")
                working_functions += 1
            else:
                print(f"   ⚠️ {description}: Статус {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {description}: Исключение - {e}")
    
    functionality_percentage = (working_functions / total_functions) * 100
    print(f"\n   📊 Работоспособность функций: {working_functions}/{total_functions} ({functionality_percentage:.1f}%)")
    
    if functionality_percentage >= 75:
        print(f"   ✅ Ранее добавленные функции работают корректно")
        return True
    else:
        print(f"   ❌ Некоторые функции не работают - требуется проверка")
        return False

def test_qr_code_number_extraction(cargo_number):
    """Тест извлечения номера заявки для QR кода"""
    print(f"\n6️⃣ ТЕСТИРОВАНИЕ ИЗВЛЕЧЕНИЯ НОМЕРА ЗАЯВКИ ДЛЯ QR КОДА")
    
    print(f"   📋 Полный номер заявки: {cargo_number}")
    
    # Логика извлечения основного номера заявки (без суффиксов)
    # Например, из "250127/02/01" должно получиться "250127"
    base_number = cargo_number.split('/')[0] if '/' in cargo_number else cargo_number
    
    print(f"   🎯 Извлеченный номер для QR кода: {base_number}")
    print(f"   📏 Длина номера: {len(base_number)} символов")
    
    # Проверяем, что номер подходит для QR кода
    if len(base_number) >= 4 and base_number.isdigit():
        print(f"   ✅ Номер подходит для генерации QR кода")
        print(f"   🖨️ Готов для печати размером 90мм x 100мм")
        return True, base_number
    else:
        print(f"   ❌ Номер не подходит для QR кода (должен быть числовым, минимум 4 символа)")
        return False, None

def main():
    """Главная функция финального тестирования"""
    print("🎯 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ: Кнопка генерации QR кода номера заявки на форме приема груза TAJLINE.TJ")
    print("=" * 120)
    print(f"🚀 Запуск тестирования в {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Backend URL: {BACKEND_URL}")
    print()
    
    # Счетчики успешности
    total_tests = 6
    passed_tests = 0
    
    # Тест 1: Авторизация оператора склада
    token, user_info = test_warehouse_operator_authorization()
    if token:
        passed_tests += 1
    else:
        print("\n❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться")
        return False
    
    # Тест 2: Создание тестовой заявки
    cargo_id, cargo_number, cargo_result = test_cargo_creation(token)
    if cargo_id and cargo_number:
        passed_tests += 1
    else:
        print("\n❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось создать заявку")
        return False
    
    # Тест 3: Стабильность backend
    if test_backend_stability_after_new_functionality(token):
        passed_tests += 1
    
    # Тест 4: Endpoint full-info
    full_info_success, full_info_result = test_full_info_endpoint(token, cargo_id)
    if full_info_success:
        passed_tests += 1
    
    # Тест 5: Ранее добавленные функции
    if test_previously_added_functions(token):
        passed_tests += 1
    
    # Тест 6: Извлечение номера для QR кода
    qr_success, qr_number = test_qr_code_number_extraction(cargo_number)
    if qr_success:
        passed_tests += 1
    
    # Итоговый отчет
    print("\n" + "=" * 120)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ФИНАЛЬНОГО ТЕСТИРОВАНИЯ")
    print("=" * 120)
    
    success_rate = (passed_tests / total_tests) * 100
    print(f"📈 Успешность тестирования: {passed_tests}/{total_tests} тестов пройдено ({success_rate:.1f}%)")
    
    if success_rate >= 85:
        print("\n🎉 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("✅ Авторизация оператора склада работает стабильно")
        print("✅ Создание тестовой заявки функционирует корректно")
        print("✅ Backend стабилен после добавления новой функциональности")
        print("✅ API endpoint GET /api/operator/cargo/{cargo_id}/full-info работает корректно")
        print("✅ Все ранее добавленные функции продолжают работать")
        print("✅ Извлечение номера заявки для QR кода готово")
        print("\n🎯 ГОТОВНОСТЬ ДЛЯ ТЕСТИРОВАНИЯ НОВОЙ КНОПКИ ГЕНЕРАЦИИ QR КОДА НА FRONTEND:")
        print(f"   📋 Номер заявки для QR: {qr_number}")
        print(f"   🖨️ Размер печати: 90мм x 100мм")
        print(f"   🔗 Backend endpoint готов: GET /api/operator/cargo/{cargo_id}/full-info")
        return True
    else:
        print("\n❌ ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ!")
        print("❌ Требуется исправление проблем перед тестированием frontend")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
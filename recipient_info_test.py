#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ ОТОБРАЖЕНИЯ ИНФОРМАЦИИ О ПОЛУЧАТЕЛЕ ДЛЯ ГРУЗОВ ИЗ ЗАБОРА В TAJLINE.TJ

КОНТЕКСТ: Исправлена критическая проблема - добавлены поля получателя в endpoint создания заявки на забор:
1. КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: В функции create_courier_pickup_request добавлены поля recipient_full_name, recipient_phone, recipient_address
2. BACKEND CHAIN: Теперь данные получателя сохраняются при создании → передаются в send_pickup_request_to_placement → отображаются в available-for-placement  
3. FRONTEND: Обновлен для отображения реальных данных получателя без fallback

ТЕСТОВЫЙ ПЛАН:
1. Авторизация оператора склада и курьера
2. Создание заявки на забор с полными данными получателя
3. Проверка что данные получателя сохранились в pickup_request
4. Отправка заявки на размещение  
5. Проверка что груз содержит корректные данные получателя
6. Проверка endpoint /available-for-placement возвращает данные получателя

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Полный цикл от создания заявки до отображения в размещении с сохранением данных получателя (ФИО, телефон, адрес) от курьера/оператора.
"""

import requests
import json
import sys
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://tajline-cargo-8.preview.emergentagent.com/api"

# Тестовые данные
WAREHOUSE_OPERATOR = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

COURIER = {
    "phone": "+79991234567", 
    "password": "courier123"
}

# Данные для тестовой заявки на забор с полными данными получателя
PICKUP_REQUEST_DATA = {
    "sender_full_name": "Тестовый Отправитель Получатель",
    "sender_phone": "+79991112233",
    "pickup_address": "Москва, ул. Тестовая Получатель, 123",
    "pickup_date": "2025-01-20",
    "pickup_time_from": "10:00",
    "pickup_time_to": "18:00",
    "route": "moscow_to_tajikistan",
    "courier_fee": 500.0,
    "destination": "Тестовый груз с данными получателя",
    # КРИТИЧЕСКИЕ ПОЛЯ ПОЛУЧАТЕЛЯ - должны сохраняться
    "recipient_full_name": "Получатель Тестовый Исправленный",
    "recipient_phone": "+992900123456",
    "recipient_address": "Душанбе, ул. Получателя Исправленная, 456"
}

def authenticate_user(phone, password, role_name):
    """Аутентификация пользователя"""
    print(f"\n🔐 Авторизация {role_name} ({phone})...")
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json={
        "phone": phone,
        "password": password
    })
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        user_info = data.get("user")
        print(f"✅ Успешная авторизация: {user_info.get('full_name')} (роль: {user_info.get('role')}, номер: {user_info.get('user_number')})")
        return token, user_info
    else:
        print(f"❌ Ошибка авторизации: {response.status_code} - {response.text}")
        return None, None

def create_pickup_request_with_recipient_data(operator_token):
    """Создание заявки на забор с данными получателя"""
    print(f"\n📦 Создание заявки на забор с полными данными получателя...")
    
    headers = {"Authorization": f"Bearer {operator_token}"}
    
    response = requests.post(f"{BACKEND_URL}/admin/courier/pickup-request", 
                           json=PICKUP_REQUEST_DATA, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        request_id = data.get("request_id")
        request_number = data.get("request_number")
        print(f"✅ Заявка создана успешно: ID={request_id}, номер={request_number}")
        print(f"📋 Данные получателя в заявке:")
        print(f"   - ФИО: {PICKUP_REQUEST_DATA['recipient_full_name']}")
        print(f"   - Телефон: {PICKUP_REQUEST_DATA['recipient_phone']}")
        print(f"   - Адрес: {PICKUP_REQUEST_DATA['recipient_address']}")
        return request_id, request_number
    else:
        print(f"❌ Ошибка создания заявки: {response.status_code} - {response.text}")
        return None, None

def verify_recipient_data_saved(courier_token, request_id):
    """Проверка что данные получателя сохранились в заявке"""
    print(f"\n🔍 Проверка сохранения данных получателя в заявке {request_id}...")
    
    headers = {"Authorization": f"Bearer {courier_token}"}
    
    # Получаем новые заявки курьера
    response = requests.get(f"{BACKEND_URL}/courier/requests/new", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        new_requests = data.get("new_requests", [])
        
        # Ищем нашу заявку
        target_request = None
        for request in new_requests:
            if request.get("id") == request_id:
                target_request = request
                break
        
        if target_request:
            print(f"✅ Заявка найдена в списке новых заявок")
            
            # КРИТИЧЕСКАЯ ПРОВЕРКА: данные получателя должны быть сохранены
            recipient_name = target_request.get("recipient_full_name", "NOT SET")
            recipient_phone = target_request.get("recipient_phone", "NOT SET") 
            recipient_address = target_request.get("recipient_address", "NOT SET")
            
            print(f"📋 ПРОВЕРКА ДАННЫХ ПОЛУЧАТЕЛЯ:")
            print(f"   - recipient_full_name: {recipient_name}")
            print(f"   - recipient_phone: {recipient_phone}")
            print(f"   - recipient_address: {recipient_address}")
            
            # Проверяем что данные НЕ показывают 'NOT SET'
            if (recipient_name != "NOT SET" and recipient_name == PICKUP_REQUEST_DATA["recipient_full_name"] and
                recipient_phone != "NOT SET" and recipient_phone == PICKUP_REQUEST_DATA["recipient_phone"] and
                recipient_address != "NOT SET" and recipient_address == PICKUP_REQUEST_DATA["recipient_address"]):
                print(f"🎉 КРИТИЧЕСКИЙ УСПЕХ: Все данные получателя сохранены корректно!")
                return True
            else:
                print(f"❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Данные получателя НЕ сохранились или неверные!")
                print(f"   Ожидалось: {PICKUP_REQUEST_DATA['recipient_full_name']}")
                print(f"   Получено: {recipient_name}")
                return False
        else:
            print(f"❌ Заявка {request_id} не найдена в списке новых заявок")
            return False
    else:
        print(f"❌ Ошибка получения новых заявок: {response.status_code} - {response.text}")
        return False

def complete_pickup_workflow(courier_token, request_id):
    """Выполнение полного workflow заявки на забор"""
    print(f"\n🚚 Выполнение полного workflow заявки {request_id}...")
    
    headers = {"Authorization": f"Bearer {courier_token}"}
    
    # 1. Принятие заявки курьером
    print("1️⃣ Принятие заявки курьером...")
    response = requests.post(f"{BACKEND_URL}/courier/requests/{request_id}/accept", headers=headers)
    if response.status_code == 200:
        print("✅ Заявка принята курьером")
    else:
        print(f"❌ Ошибка принятия заявки: {response.status_code} - {response.text}")
        return False
    
    # 2. Забор груза
    print("2️⃣ Забор груза курьером...")
    response = requests.post(f"{BACKEND_URL}/courier/requests/{request_id}/pickup", headers=headers)
    if response.status_code == 200:
        print("✅ Груз забран курьером")
    else:
        print(f"❌ Ошибка забора груза: {response.status_code} - {response.text}")
        return False
    
    # 3. Доставка на склад
    print("3️⃣ Доставка груза на склад...")
    response = requests.post(f"{BACKEND_URL}/courier/requests/{request_id}/deliver-to-warehouse", headers=headers)
    if response.status_code == 200:
        print("✅ Груз доставлен на склад")
        return True
    else:
        print(f"❌ Ошибка доставки на склад: {response.status_code} - {response.text}")
        return False

def check_warehouse_notification_with_recipient_data(operator_token, request_number):
    """Проверка уведомления склада с данными получателя"""
    print(f"\n📬 Проверка уведомления склада для заявки {request_number}...")
    
    headers = {"Authorization": f"Bearer {operator_token}"}
    
    response = requests.get(f"{BACKEND_URL}/operator/warehouse-notifications", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        notifications = data.get("notifications", [])
        
        # Ищем уведомление для нашей заявки
        target_notification = None
        for notification in notifications:
            if notification.get("request_number") == request_number:
                target_notification = notification
                break
        
        if target_notification:
            notification_id = target_notification.get("id")
            print(f"✅ Уведомление найдено: {notification_id}")
            
            # Проверяем pickup_request_id
            pickup_request_id = target_notification.get("pickup_request_id")
            if pickup_request_id:
                print(f"📋 pickup_request_id: {pickup_request_id}")
                return notification_id, pickup_request_id
            else:
                print(f"⚠️ pickup_request_id отсутствует в уведомлении")
                return notification_id, None
        else:
            print(f"❌ Уведомление для заявки {request_number} не найдено")
            return None, None
    else:
        print(f"❌ Ошибка получения уведомлений: {response.status_code} - {response.text}")
        return None, None

def send_pickup_request_to_placement(operator_token, notification_id):
    """Отправка заявки на размещение"""
    print(f"\n📤 Отправка заявки на размещение через уведомление {notification_id}...")
    
    headers = {"Authorization": f"Bearer {operator_token}"}
    
    response = requests.post(f"{BACKEND_URL}/operator/warehouse-notifications/{notification_id}/send-to-placement", 
                           headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        cargo_id = data.get("cargo_id")
        cargo_number = data.get("cargo_number")
        print(f"✅ Заявка отправлена на размещение успешно")
        print(f"📦 Создан груз: ID={cargo_id}, номер={cargo_number}")
        return cargo_id, cargo_number
    else:
        print(f"❌ Ошибка отправки на размещение: {response.status_code} - {response.text}")
        return None, None

def verify_recipient_data_in_placement(operator_token, cargo_number):
    """Проверка данных получателя в списке размещения"""
    print(f"\n🏭 Проверка данных получателя в списке размещения для груза {cargo_number}...")
    
    headers = {"Authorization": f"Bearer {operator_token}"}
    
    response = requests.get(f"{BACKEND_URL}/operator/cargo/available-for-placement", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        
        # Ищем наш груз
        target_cargo = None
        for item in items:
            if item.get("cargo_number") == cargo_number:
                target_cargo = item
                break
        
        if target_cargo:
            print(f"✅ Груз найден в списке размещения")
            
            # КРИТИЧЕСКАЯ ПРОВЕРКА: данные получателя в грузе
            recipient_name = target_cargo.get("recipient_full_name", "")
            recipient_phone = target_cargo.get("recipient_phone", "")
            recipient_address = target_cargo.get("recipient_address", "")
            
            print(f"📋 ДАННЫЕ ПОЛУЧАТЕЛЯ В ГРУЗЕ:")
            print(f"   - recipient_full_name: '{recipient_name}'")
            print(f"   - recipient_phone: '{recipient_phone}'")
            print(f"   - recipient_address: '{recipient_address}'")
            
            # Проверяем соответствие исходным данным
            expected_name = PICKUP_REQUEST_DATA["recipient_full_name"]
            expected_phone = PICKUP_REQUEST_DATA["recipient_phone"]
            expected_address = PICKUP_REQUEST_DATA["recipient_address"]
            
            if (recipient_name == expected_name and 
                recipient_phone == expected_phone and 
                recipient_address == expected_address):
                print(f"🎉 КРИТИЧЕСКИЙ УСПЕХ: Данные получателя корректно переданы в груз!")
                return True
            else:
                print(f"❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Данные получателя в грузе неверные!")
                print(f"   Ожидалось: {expected_name} / {expected_phone} / {expected_address}")
                print(f"   Получено: {recipient_name} / {recipient_phone} / {recipient_address}")
                return False
        else:
            print(f"❌ Груз {cargo_number} не найден в списке размещения")
            return False
    else:
        print(f"❌ Ошибка получения списка размещения: {response.status_code} - {response.text}")
        return False

def main():
    """Основная функция тестирования"""
    print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ ОТОБРАЖЕНИЯ ИНФОРМАЦИИ О ПОЛУЧАТЕЛЕ ДЛЯ ГРУЗОВ ИЗ ЗАБОРА В TAJLINE.TJ")
    print("=" * 120)
    
    test_results = []
    
    # 1. Авторизация оператора склада
    operator_token, operator_info = authenticate_user(
        WAREHOUSE_OPERATOR["phone"], 
        WAREHOUSE_OPERATOR["password"], 
        "Оператор склада"
    )
    if not operator_token:
        print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как оператор склада")
        return
    test_results.append("✅ Авторизация оператора склада")
    
    # 2. Авторизация курьера
    courier_token, courier_info = authenticate_user(
        COURIER["phone"], 
        COURIER["password"], 
        "Курьер"
    )
    if not courier_token:
        print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как курьер")
        return
    test_results.append("✅ Авторизация курьера")
    
    # 3. Создание заявки на забор с данными получателя
    request_id, request_number = create_pickup_request_with_recipient_data(operator_token)
    if not request_id:
        print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось создать заявку на забор")
        return
    test_results.append("✅ Создание заявки на забор с данными получателя")
    
    # 4. КРИТИЧЕСКАЯ ПРОВЕРКА: данные получателя сохранились
    recipient_data_saved = verify_recipient_data_saved(courier_token, request_id)
    if recipient_data_saved:
        test_results.append("✅ КРИТИЧЕСКИЙ УСПЕХ: Данные получателя сохранены в заявке")
    else:
        test_results.append("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Данные получателя НЕ сохранены")
        print("\n🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА ОБНАРУЖЕНА!")
        print("Endpoint /api/admin/courier/pickup-request НЕ сохраняет поля получателя:")
        print("- recipient_full_name")
        print("- recipient_phone") 
        print("- recipient_address")
        print("\nТребуется исправление в backend коде!")
        return
    
    # 5. Выполнение полного workflow
    workflow_completed = complete_pickup_workflow(courier_token, request_id)
    if workflow_completed:
        test_results.append("✅ Полный workflow заявки выполнен")
    else:
        test_results.append("❌ Ошибка в workflow заявки")
        return
    
    # 6. Проверка уведомления склада
    notification_id, pickup_request_id = check_warehouse_notification_with_recipient_data(operator_token, request_number)
    if notification_id:
        test_results.append("✅ Уведомление склада создано")
    else:
        test_results.append("❌ Уведомление склада не найдено")
        return
    
    # 7. Отправка на размещение
    cargo_id, cargo_number = send_pickup_request_to_placement(operator_token, notification_id)
    if cargo_id:
        test_results.append("✅ Заявка отправлена на размещение")
    else:
        test_results.append("❌ Ошибка отправки на размещение")
        return
    
    # 8. ФИНАЛЬНАЯ ПРОВЕРКА: данные получателя в списке размещения
    recipient_data_in_placement = verify_recipient_data_in_placement(operator_token, cargo_number)
    if recipient_data_in_placement:
        test_results.append("✅ КРИТИЧЕСКИЙ УСПЕХ: Данные получателя в списке размещения")
    else:
        test_results.append("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Данные получателя отсутствуют в размещении")
    
    # Итоговый отчет
    print("\n" + "=" * 120)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
    print("=" * 120)
    
    success_count = len([r for r in test_results if r.startswith("✅")])
    total_count = len(test_results)
    success_rate = (success_count / total_count) * 100
    
    for result in test_results:
        print(result)
    
    print(f"\n📈 SUCCESS RATE: {success_rate:.1f}% ({success_count}/{total_count} тестов пройдены)")
    
    if success_rate == 100:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ ОЖИДАЕМЫЙ РЕЗУЛЬТАТ ДОСТИГНУТ: Полный цикл от создания заявки до отображения в размещении")
        print("✅ Данные получателя (ФИО, телефон, адрес) сохраняются и передаются корректно")
        print("✅ Backend chain работает: создание → send_pickup_request_to_placement → available-for-placement")
    else:
        print(f"\n⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ: {total_count - success_count} из {total_count} тестов не пройдены")
        
        if not recipient_data_saved:
            print("\n🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА:")
            print("Endpoint создания заявки на забор НЕ сохраняет данные получателя!")
            print("Требуется добавить поля recipient_full_name, recipient_phone, recipient_address")
            print("в функцию create_courier_pickup_request")

if __name__ == "__main__":
    main()
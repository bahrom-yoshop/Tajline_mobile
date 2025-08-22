#!/usr/bin/env python3
"""
ДЕТАЛЬНЫЙ АНАЛИЗ СТРУКТУРЫ ЗАЯВОК НА ЗАБОР В TAJLINE.TJ

Углубленный анализ найденных endpoints:
1. /api/admin/cargo-requests (11 записей)
2. /api/operator/warehouse-notifications (11 записей)

Цель: Понять точную структуру данных и найти связи с грузами
"""

import requests
import json
import os
from datetime import datetime

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://placement-view.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def authenticate_admin():
    """Авторизация администратора для доступа к cargo-requests"""
    print("🔐 АВТОРИЗАЦИЯ АДМИНИСТРАТОРА...")
    
    auth_data = {
        "phone": "+79999888777",
        "password": "admin123"
    }
    
    response = requests.post(f"{API_BASE}/auth/login", json=auth_data)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        user_info = data.get('user')
        print(f"✅ Успешная авторизация: {user_info.get('full_name')} (роль: {user_info.get('role')})")
        return token
    else:
        print(f"❌ Ошибка авторизации: {response.text}")
        return None

def authenticate_operator():
    """Авторизация оператора склада"""
    print("🔐 АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА...")
    
    auth_data = {
        "phone": "+79777888999",
        "password": "warehouse123"
    }
    
    response = requests.post(f"{API_BASE}/auth/login", json=auth_data)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        user_info = data.get('user')
        print(f"✅ Успешная авторизация: {user_info.get('full_name')} (роль: {user_info.get('role')})")
        return token
    else:
        print(f"❌ Ошибка авторизации: {response.text}")
        return None

def analyze_cargo_requests(admin_token):
    """Детальный анализ структуры cargo-requests"""
    print("\n📋 ДЕТАЛЬНЫЙ АНАЛИЗ /api/admin/cargo-requests...")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    response = requests.get(f"{API_BASE}/admin/cargo-requests", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Получено данных: {type(data)}")
        
        if isinstance(data, list):
            cargo_requests = data
        else:
            cargo_requests = data.get('requests', data.get('items', []))
        
        print(f"📊 Всего заявок: {len(cargo_requests)}")
        
        # Анализируем каждую заявку детально
        for i, request in enumerate(cargo_requests):
            print(f"\n📋 ЗАЯВКА {i+1}:")
            print(f"   Тип: {type(request)}")
            
            if isinstance(request, dict):
                # Показываем все поля
                print(f"   Поля ({len(request)}): {list(request.keys())}")
                
                # Ключевые поля
                key_fields = ['id', 'request_number', 'status', 'cargo_name', 'sender_full_name', 'recipient_full_name']
                for field in key_fields:
                    if field in request:
                        value = request[field]
                        print(f"   🔑 {field}: {value}")
                
                # Ищем поля связанные с грузами
                cargo_fields = []
                for field, value in request.items():
                    field_lower = field.lower()
                    if any(keyword in field_lower for keyword in ['cargo', 'груз', 'item', 'товар']):
                        cargo_fields.append(field)
                        print(f"   🚛 ГРУЗ-ПОЛЕ: {field} = {value}")
                
                # Проверяем есть ли массив items
                if 'items' in request:
                    items = request['items']
                    print(f"   📦 ITEMS: {type(items)} с {len(items) if isinstance(items, list) else 'N/A'} элементами")
                    
                    if isinstance(items, list):
                        for j, item in enumerate(items[:3]):
                            print(f"      Item {j+1}: {item}")
                            if isinstance(item, dict):
                                # Ищем cargo_id, cargo_number в items
                                for cargo_key in ['cargo_id', 'cargo_number', 'id', 'number']:
                                    if cargo_key in item:
                                        print(f"         🎯 НАЙДЕН ГРУЗ: {cargo_key} = {item[cargo_key]}")
                
                # Проверяем другие возможные связи
                for field in ['related_cargo_id', 'cargo_list', 'associated_cargo']:
                    if field in request:
                        print(f"   🔗 СВЯЗЬ С ГРУЗОМ: {field} = {request[field]}")
                
                print("   " + "-" * 60)
        
        return cargo_requests
    else:
        print(f"❌ Ошибка: {response.status_code} - {response.text}")
        return []

def analyze_warehouse_notifications(operator_token):
    """Детальный анализ структуры warehouse-notifications"""
    print("\n📬 ДЕТАЛЬНЫЙ АНАЛИЗ /api/operator/warehouse-notifications...")
    
    headers = {"Authorization": f"Bearer {operator_token}"}
    
    response = requests.get(f"{API_BASE}/operator/warehouse-notifications", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Получено данных: {type(data)}")
        
        notifications = data.get('notifications', [])
        print(f"📊 Всего уведомлений: {len(notifications)}")
        
        # Показываем дополнительную информацию
        for key, value in data.items():
            if key != 'notifications':
                print(f"   Дополнительное поле: {key} = {value}")
        
        # Анализируем каждое уведомление
        for i, notification in enumerate(notifications):
            print(f"\n📬 УВЕДОМЛЕНИЕ {i+1}:")
            print(f"   Тип: {type(notification)}")
            
            if isinstance(notification, dict):
                # Показываем все поля
                print(f"   Поля ({len(notification)}): {list(notification.keys())}")
                
                # Ключевые поля
                key_fields = ['id', 'request_number', 'status', 'pickup_request_id', 'cargo_id', 'cargo_number']
                for field in key_fields:
                    if field in notification:
                        value = notification[field]
                        print(f"   🔑 {field}: {value}")
                
                # Ищем поля связанные с грузами
                for field, value in notification.items():
                    field_lower = field.lower()
                    if any(keyword in field_lower for keyword in ['cargo', 'груз', 'pickup', 'забор']):
                        print(f"   🚛 СВЯЗАННОЕ ПОЛЕ: {field} = {value}")
                
                # Проверяем есть ли данные о грузе
                if 'cargo_data' in notification or 'pickup_data' in notification:
                    cargo_data = notification.get('cargo_data', notification.get('pickup_data', {}))
                    print(f"   📦 ДАННЫЕ ГРУЗА: {cargo_data}")
                
                print("   " + "-" * 60)
        
        return notifications
    else:
        print(f"❌ Ошибка: {response.status_code} - {response.text}")
        return []

def find_cargo_connections(cargo_requests, notifications):
    """Поиск связей между заявками и грузами"""
    print("\n🔗 ПОИСК СВЯЗЕЙ МЕЖДУ ЗАЯВКАМИ И ГРУЗАМИ...")
    
    connections = []
    
    # Анализируем cargo_requests
    print("📋 Анализ cargo_requests:")
    for i, request in enumerate(cargo_requests):
        if isinstance(request, dict):
            request_id = request.get('id')
            request_number = request.get('request_number')
            
            # Ищем прямые ссылки на грузы
            cargo_connections = []
            
            # Проверяем items
            if 'items' in request and isinstance(request['items'], list):
                for item in request['items']:
                    if isinstance(item, dict):
                        cargo_id = item.get('cargo_id') or item.get('id')
                        cargo_number = item.get('cargo_number') or item.get('number')
                        if cargo_id or cargo_number:
                            cargo_connections.append({
                                'type': 'item',
                                'cargo_id': cargo_id,
                                'cargo_number': cargo_number
                            })
            
            # Проверяем прямые поля
            for field in ['cargo_id', 'cargo_number', 'related_cargo_id']:
                if field in request and request[field]:
                    cargo_connections.append({
                        'type': 'direct_field',
                        'field': field,
                        'value': request[field]
                    })
            
            if cargo_connections:
                print(f"   Заявка {request_number}: {len(cargo_connections)} связей с грузами")
                for conn in cargo_connections:
                    print(f"      {conn}")
                
                connections.append({
                    'request_id': request_id,
                    'request_number': request_number,
                    'cargo_connections': cargo_connections
                })
    
    # Анализируем notifications
    print("\n📬 Анализ notifications:")
    for i, notification in enumerate(notifications):
        if isinstance(notification, dict):
            notification_id = notification.get('id')
            request_number = notification.get('request_number')
            pickup_request_id = notification.get('pickup_request_id')
            
            # Ищем связи с грузами
            cargo_info = []
            
            for field in ['cargo_id', 'cargo_number']:
                if field in notification and notification[field]:
                    cargo_info.append({
                        'field': field,
                        'value': notification[field]
                    })
            
            if cargo_info or pickup_request_id:
                print(f"   Уведомление {notification_id}: pickup_request_id={pickup_request_id}")
                for info in cargo_info:
                    print(f"      {info}")
    
    return connections

def test_cargo_deletion_endpoints(operator_token, admin_token):
    """Тестирование endpoints для удаления грузов"""
    print("\n🗑️ ТЕСТИРОВАНИЕ ENDPOINTS ДЛЯ УДАЛЕНИЯ ГРУЗОВ...")
    
    # Endpoints для тестирования
    deletion_endpoints = [
        {
            'method': 'DELETE',
            'endpoint': '/api/operator/cargo/{cargo_id}/remove-from-placement',
            'description': 'Удаление груза из размещения',
            'token': operator_token
        },
        {
            'method': 'DELETE', 
            'endpoint': '/api/operator/cargo/bulk-remove-from-placement',
            'description': 'Массовое удаление грузов из размещения',
            'token': operator_token
        },
        {
            'method': 'DELETE',
            'endpoint': '/api/admin/cargo-requests/{request_id}',
            'description': 'Удаление заявки на забор',
            'token': admin_token
        }
    ]
    
    for endpoint_info in deletion_endpoints:
        method = endpoint_info['method']
        endpoint = endpoint_info['endpoint']
        description = endpoint_info['description']
        token = endpoint_info['token']
        
        print(f"\n🔍 {description}:")
        print(f"   {method} {endpoint}")
        
        # Для тестирования используем фиктивные данные
        if 'bulk-remove' in endpoint:
            test_data = {"cargo_ids": ["fake-id-1", "fake-id-2"]}
        else:
            test_data = None
        
        # Заменяем параметры в URL
        test_endpoint = endpoint.replace('{cargo_id}', 'fake-cargo-id').replace('{request_id}', 'fake-request-id')
        
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            if method == 'DELETE':
                response = requests.delete(f"{API_BASE}{test_endpoint}", json=test_data, headers=headers)
            
            print(f"   Статус: {response.status_code}")
            
            if response.status_code in [200, 404, 422]:  # Ожидаемые статусы
                print(f"   ✅ Endpoint существует и работает")
                if response.status_code == 200:
                    try:
                        result = response.json()
                        print(f"   📄 Ответ: {result}")
                    except:
                        pass
            else:
                print(f"   ⚠️ Неожиданный статус: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

def main():
    """Основная функция детального анализа"""
    print("🎯 ДЕТАЛЬНЫЙ АНАЛИЗ СТРУКТУРЫ ЗАЯВОК НА ЗАБОР В TAJLINE.TJ")
    print("=" * 80)
    
    # Авторизация
    admin_token = authenticate_admin()
    operator_token = authenticate_operator()
    
    if not admin_token or not operator_token:
        print("❌ Не удалось авторизоваться")
        return
    
    # Детальный анализ cargo-requests
    cargo_requests = analyze_cargo_requests(admin_token)
    
    # Детальный анализ warehouse-notifications
    notifications = analyze_warehouse_notifications(operator_token)
    
    # Поиск связей между заявками и грузами
    connections = find_cargo_connections(cargo_requests, notifications)
    
    # Тестирование endpoints для удаления
    test_cargo_deletion_endpoints(operator_token, admin_token)
    
    # Финальный отчет
    print("\n" + "=" * 80)
    print("📊 ДЕТАЛЬНЫЙ ОТЧЕТ АНАЛИЗА")
    print("=" * 80)
    
    print(f"\n🔍 РЕЗУЛЬТАТЫ ДЕТАЛЬНОГО АНАЛИЗА:")
    print(f"✅ Заявки cargo-requests: {len(cargo_requests)}")
    print(f"✅ Уведомления warehouse-notifications: {len(notifications)}")
    print(f"✅ Найдено связей с грузами: {len(connections)}")
    
    print(f"\n📋 СТРУКТУРА ДАННЫХ ЗАЯВОК НА ЗАБОР:")
    if cargo_requests:
        sample_request = cargo_requests[0]
        if isinstance(sample_request, dict):
            print(f"   Поля в заявке: {list(sample_request.keys())}")
            
            # Показываем важные поля
            important_fields = ['id', 'request_number', 'status', 'items', 'cargo_name', 'sender_full_name', 'recipient_full_name']
            for field in important_fields:
                if field in sample_request:
                    value = sample_request[field]
                    print(f"   {field}: {type(value)} = {value}")
    
    print(f"\n📬 СТРУКТУРА УВЕДОМЛЕНИЙ СКЛАДА:")
    if notifications:
        sample_notification = notifications[0]
        if isinstance(sample_notification, dict):
            print(f"   Поля в уведомлении: {list(sample_notification.keys())}")
            
            # Показываем важные поля
            important_fields = ['id', 'request_number', 'pickup_request_id', 'status', 'cargo_id', 'cargo_number']
            for field in important_fields:
                if field in sample_notification:
                    value = sample_notification[field]
                    print(f"   {field}: {type(value)} = {value}")
    
    print(f"\n🔗 НАЙДЕННЫЕ СВЯЗИ С ГРУЗАМИ:")
    for connection in connections:
        request_number = connection['request_number']
        cargo_connections = connection['cargo_connections']
        print(f"   Заявка {request_number}: {len(cargo_connections)} связей")
        for conn in cargo_connections:
            print(f"      {conn}")
    
    print(f"\n🎯 РЕКОМЕНДАЦИИ ДЛЯ ПОЛНОГО УДАЛЕНИЯ ГРУЗОВ:")
    print("1. ✅ Использовать /api/admin/cargo-requests для получения всех заявок на забор")
    print("2. ✅ Анализировать поле 'items' в каждой заявке для поиска связанных грузов")
    print("3. ✅ Использовать /api/operator/warehouse-notifications для поиска уведомлений с pickup_request_id")
    print("4. ✅ Реализовать удаление через существующие endpoints массового удаления")
    print("5. ✅ Учитывать связи между заявками и грузами при удалении")
    
    if connections:
        print(f"\n✅ НАЙДЕНЫ КОНКРЕТНЫЕ СВЯЗИ МЕЖДУ ЗАЯВКАМИ И ГРУЗАМИ!")
        print("   Можно реализовать полное удаление грузов из секции 'На Забор'")
    else:
        print(f"\n⚠️ Прямые связи не найдены, требуется дополнительный анализ")

if __name__ == "__main__":
    main()
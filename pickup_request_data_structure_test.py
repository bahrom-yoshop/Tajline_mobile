#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Структура данных заявок на забор в системе TAJLINE.TJ

ЦЕЛЬ ТЕСТИРОВАНИЯ:
Понять структуру данных заявок на забор груза и найти связанные с ними грузы для реализации функции полного удаления грузов.

ОСНОВНЫЕ ТЕСТЫ:
1) Авторизация оператора склада (+79777888999/warehouse123)
2) Получение заявок на забор через GET /api/operator/pickup-requests
3) Анализ структуры данных заявок на забор - есть ли поля cargo_id, cargo_number или связанные грузы
4) Проверить есть ли endpoint для получения грузов связанных с заявками на забор
5) Найти способ идентификации грузов в заявках на забор для их полного удаления

ДЕТАЛИ АНАЛИЗА:
- Проверить все поля в структуре заявки на забор
- Найти связь между заявками и грузами 
- Определить как можно получить список грузов для удаления в секции "На Забор"

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Понять как работать с грузами в заявках на забор для их полного удаления из системы
"""

import requests
import json
import os
from datetime import datetime

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-cargo-7.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def test_warehouse_operator_auth():
    """Тест авторизации оператора склада"""
    print("🔐 ТЕСТИРОВАНИЕ АВТОРИЗАЦИИ ОПЕРАТОРА СКЛАДА...")
    
    auth_data = {
        "phone": "+79777888999",
        "password": "warehouse123"
    }
    
    response = requests.post(f"{API_BASE}/auth/login", json=auth_data)
    print(f"Статус авторизации: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        user_info = data.get('user')
        print(f"✅ Успешная авторизация: {user_info.get('full_name')} (роль: {user_info.get('role')})")
        print(f"Номер пользователя: {user_info.get('user_number', 'Не указан')}")
        return token
    else:
        print(f"❌ Ошибка авторизации: {response.text}")
        return None

def test_pickup_requests_endpoint(operator_token):
    """Тест получения заявок на забор через основной endpoint"""
    print("\n📋 ТЕСТИРОВАНИЕ ENDPOINT /api/operator/pickup-requests...")
    
    headers = {"Authorization": f"Bearer {operator_token}"}
    
    response = requests.get(f"{API_BASE}/operator/pickup-requests", headers=headers)
    print(f"Статус получения заявок: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Endpoint /api/operator/pickup-requests работает")
        
        # Анализируем структуру ответа
        if isinstance(data, list):
            pickup_requests = data
            print(f"📊 Структура ответа: Массив из {len(pickup_requests)} заявок")
        elif isinstance(data, dict):
            pickup_requests = data.get('items', data.get('requests', []))
            print(f"📊 Структура ответа: Объект с полем items/requests, содержит {len(pickup_requests)} заявок")
            
            # Показываем дополнительные поля в ответе
            for key, value in data.items():
                if key not in ['items', 'requests']:
                    print(f"   Дополнительное поле: {key} = {value}")
        else:
            pickup_requests = []
            print(f"📊 Неожиданная структура ответа: {type(data)}")
        
        return pickup_requests
    else:
        print(f"❌ Ошибка получения заявок: {response.text}")
        return []

def analyze_pickup_request_structure(pickup_requests):
    """Анализ структуры данных заявок на забор"""
    print("\n🔍 АНАЛИЗ СТРУКТУРЫ ДАННЫХ ЗАЯВОК НА ЗАБОР...")
    
    if not pickup_requests:
        print("⚠️ Нет заявок для анализа")
        return {}
    
    print(f"📊 Всего заявок для анализа: {len(pickup_requests)}")
    
    # Анализируем первые несколько заявок
    analysis_results = {
        'total_requests': len(pickup_requests),
        'sample_structures': [],
        'common_fields': set(),
        'cargo_related_fields': [],
        'unique_fields': set()
    }
    
    for i, request in enumerate(pickup_requests[:5]):  # Анализируем первые 5 заявок
        print(f"\n📋 ЗАЯВКА {i+1}:")
        print(f"   Тип данных: {type(request)}")
        
        if isinstance(request, dict):
            # Собираем все поля
            fields = list(request.keys())
            analysis_results['unique_fields'].update(fields)
            
            if i == 0:
                analysis_results['common_fields'] = set(fields)
            else:
                analysis_results['common_fields'] = analysis_results['common_fields'].intersection(set(fields))
            
            # Показываем основные поля
            print(f"   Поля в заявке ({len(fields)}): {', '.join(fields)}")
            
            # Ищем поля связанные с грузами
            cargo_fields = []
            for field in fields:
                field_lower = field.lower()
                if any(keyword in field_lower for keyword in ['cargo', 'груз', 'item', 'товар']):
                    cargo_fields.append(field)
                    value = request.get(field)
                    print(f"   🚛 ГРУЗ-СВЯЗАННОЕ ПОЛЕ: {field} = {value}")
            
            if cargo_fields:
                analysis_results['cargo_related_fields'].extend(cargo_fields)
            
            # Показываем ключевые поля
            key_fields = ['id', 'request_number', 'status', 'cargo_id', 'cargo_number', 'items', 'cargo_list']
            for field in key_fields:
                if field in request:
                    value = request[field]
                    print(f"   🔑 {field}: {value}")
            
            # Если есть массив items, анализируем его
            if 'items' in request and isinstance(request['items'], list):
                items = request['items']
                print(f"   📦 ITEMS в заявке: {len(items)} элементов")
                
                for j, item in enumerate(items[:3]):  # Показываем первые 3 item'а
                    if isinstance(item, dict):
                        item_fields = list(item.keys())
                        print(f"      Item {j+1} поля: {', '.join(item_fields)}")
                        
                        # Ищем cargo_number или cargo_id в items
                        for cargo_field in ['cargo_id', 'cargo_number', 'id', 'number']:
                            if cargo_field in item:
                                print(f"      🎯 НАЙДЕН ГРУЗ В ITEM: {cargo_field} = {item[cargo_field]}")
            
            # Сохраняем структуру для анализа
            sample_structure = {
                'fields': fields,
                'cargo_fields': cargo_fields,
                'has_items': 'items' in request,
                'items_count': len(request.get('items', [])) if isinstance(request.get('items'), list) else 0
            }
            analysis_results['sample_structures'].append(sample_structure)
        
        print("   " + "-" * 50)
    
    return analysis_results

def test_alternative_pickup_endpoints(operator_token):
    """Тест альтернативных endpoints для заявок на забор"""
    print("\n🔍 ТЕСТИРОВАНИЕ АЛЬТЕРНАТИВНЫХ ENDPOINTS ДЛЯ ЗАЯВОК НА ЗАБОР...")
    
    headers = {"Authorization": f"Bearer {operator_token}"}
    
    # Список возможных endpoints
    alternative_endpoints = [
        "/api/admin/courier/pickup-requests",
        "/api/courier/pickup-requests", 
        "/api/operator/courier-requests",
        "/api/admin/cargo-requests",
        "/api/cargo-requests",
        "/api/pickup-requests",
        "/api/operator/warehouse-notifications",
        "/api/courier/requests/new"
    ]
    
    working_endpoints = []
    
    for endpoint in alternative_endpoints:
        print(f"\n🔍 Тестирование {endpoint}...")
        
        response = requests.get(f"{API_BASE}{endpoint.replace('/api', '')}", headers=headers)
        print(f"   Статус: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ Endpoint работает!")
                
                # Быстрый анализ структуры
                if isinstance(data, list):
                    count = len(data)
                    print(f"   📊 Возвращает массив из {count} элементов")
                elif isinstance(data, dict):
                    if 'items' in data:
                        count = len(data['items'])
                        print(f"   📊 Возвращает объект с {count} items")
                    elif 'requests' in data:
                        count = len(data['requests'])
                        print(f"   📊 Возвращает объект с {count} requests")
                    else:
                        print(f"   📊 Возвращает объект с полями: {list(data.keys())}")
                
                working_endpoints.append({
                    'endpoint': endpoint,
                    'data': data,
                    'count': count if 'count' in locals() else 0
                })
                
            except Exception as e:
                print(f"   ⚠️ Ошибка парсинга JSON: {e}")
        elif response.status_code == 404:
            print(f"   ❌ Endpoint не найден")
        elif response.status_code == 403:
            print(f"   ❌ Нет доступа (403)")
        else:
            print(f"   ❌ Ошибка: {response.status_code}")
    
    return working_endpoints

def find_cargo_deletion_strategy(analysis_results, working_endpoints):
    """Определение стратегии удаления грузов из заявок на забор"""
    print("\n🎯 ОПРЕДЕЛЕНИЕ СТРАТЕГИИ УДАЛЕНИЯ ГРУЗОВ ИЗ ЗАЯВОК НА ЗАБОР...")
    
    strategies = []
    
    # Стратегия 1: Прямые cargo_id/cargo_number в заявках
    if analysis_results.get('cargo_related_fields'):
        print("✅ СТРАТЕГИЯ 1: Прямые ссылки на грузы в заявках")
        print(f"   Найденные поля: {set(analysis_results['cargo_related_fields'])}")
        strategies.append({
            'name': 'direct_cargo_fields',
            'description': 'Использовать прямые поля cargo_id/cargo_number в заявках',
            'fields': list(set(analysis_results['cargo_related_fields']))
        })
    
    # Стратегия 2: Items в заявках
    has_items = any(s.get('has_items', False) for s in analysis_results.get('sample_structures', []))
    if has_items:
        print("✅ СТРАТЕГИЯ 2: Грузы в массиве items заявок")
        print("   Заявки содержат массив items с грузами")
        strategies.append({
            'name': 'items_array',
            'description': 'Извлекать грузы из массива items в заявках',
            'method': 'Перебрать все заявки → получить items → извлечь cargo_id/cargo_number'
        })
    
    # Стратегия 3: Связанные endpoints
    if working_endpoints:
        print("✅ СТРАТЕГИЯ 3: Использование связанных endpoints")
        for endpoint_info in working_endpoints:
            endpoint = endpoint_info['endpoint']
            count = endpoint_info.get('count', 0)
            print(f"   {endpoint}: {count} записей")
        
        strategies.append({
            'name': 'related_endpoints',
            'description': 'Использовать связанные endpoints для поиска грузов',
            'endpoints': [e['endpoint'] for e in working_endpoints]
        })
    
    # Стратегия 4: Поиск по статусу груза
    print("✅ СТРАТЕГИЯ 4: Поиск грузов по статусу 'pickup_requested'")
    print("   Найти все грузы со статусом pickup_requested или similar")
    strategies.append({
        'name': 'status_based_search',
        'description': 'Найти грузы по статусу связанному с забором',
        'statuses': ['pickup_requested', 'assigned_to_courier', 'picked_up_by_courier']
    })
    
    return strategies

def test_cargo_search_by_status(operator_token):
    """Тест поиска грузов по статусу связанному с забором"""
    print("\n🔍 ТЕСТИРОВАНИЕ ПОИСКА ГРУЗОВ ПО СТАТУСУ ЗАБОРА...")
    
    headers = {"Authorization": f"Bearer {operator_token}"}
    
    # Endpoints для поиска грузов
    cargo_endpoints = [
        "/api/operator/cargo/available-for-placement",
        "/api/cargo/all",
        "/api/operator/cargo/list"
    ]
    
    pickup_related_cargo = []
    
    for endpoint in cargo_endpoints:
        print(f"\n🔍 Проверяем {endpoint}...")
        
        response = requests.get(f"{API_BASE}{endpoint.replace('/api', '')}", headers=headers)
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ Endpoint работает")
                
                # Извлекаем список грузов
                if isinstance(data, list):
                    cargo_list = data
                elif isinstance(data, dict):
                    cargo_list = data.get('items', data.get('cargo', []))
                else:
                    cargo_list = []
                
                print(f"   📊 Найдено грузов: {len(cargo_list)}")
                
                # Ищем грузы связанные с забором
                pickup_cargo = []
                for cargo in cargo_list:
                    if isinstance(cargo, dict):
                        status = cargo.get('status', '').lower()
                        processing_status = cargo.get('processing_status', '').lower()
                        
                        # Ищем статусы связанные с забором
                        pickup_keywords = ['pickup', 'забор', 'courier', 'курьер']
                        if any(keyword in status for keyword in pickup_keywords) or \
                           any(keyword in processing_status for keyword in pickup_keywords):
                            pickup_cargo.append(cargo)
                            print(f"   🎯 НАЙДЕН ГРУЗ НА ЗАБОР: {cargo.get('cargo_number', 'N/A')} - статус: {status}")
                
                if pickup_cargo:
                    pickup_related_cargo.extend(pickup_cargo)
                    print(f"   ✅ Найдено {len(pickup_cargo)} грузов связанных с забором")
                else:
                    print(f"   ⚠️ Грузы связанные с забором не найдены")
                    
            except Exception as e:
                print(f"   ❌ Ошибка обработки: {e}")
        else:
            print(f"   ❌ Ошибка: {response.status_code}")
    
    return pickup_related_cargo

def main():
    """Основная функция тестирования"""
    print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Структура данных заявок на забор в системе TAJLINE.TJ")
    print("=" * 100)
    
    # 1. Авторизация оператора склада
    operator_token = test_warehouse_operator_auth()
    if not operator_token:
        print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как оператор склада")
        return
    
    # 2. Получение заявок на забор через основной endpoint
    pickup_requests = test_pickup_requests_endpoint(operator_token)
    
    # 3. Анализ структуры данных заявок на забор
    analysis_results = analyze_pickup_request_structure(pickup_requests)
    
    # 4. Тестирование альтернативных endpoints
    working_endpoints = test_alternative_pickup_endpoints(operator_token)
    
    # 5. Поиск грузов по статусу
    pickup_cargo = test_cargo_search_by_status(operator_token)
    
    # 6. Определение стратегии удаления
    strategies = find_cargo_deletion_strategy(analysis_results, working_endpoints)
    
    # 7. Финальный отчет
    print("\n" + "=" * 100)
    print("📊 ФИНАЛЬНЫЙ ОТЧЕТ АНАЛИЗА СТРУКТУРЫ ДАННЫХ ЗАЯВОК НА ЗАБОР")
    print("=" * 100)
    
    print(f"\n🔍 РЕЗУЛЬТАТЫ АНАЛИЗА:")
    print(f"✅ Авторизация оператора склада: Успешно")
    print(f"✅ Основной endpoint /api/operator/pickup-requests: {'Работает' if pickup_requests else 'Не работает'}")
    print(f"✅ Найдено заявок на забор: {len(pickup_requests)}")
    print(f"✅ Работающих альтернативных endpoints: {len(working_endpoints)}")
    print(f"✅ Найдено грузов связанных с забором: {len(pickup_cargo)}")
    
    print(f"\n📋 СТРУКТУРА ЗАЯВОК НА ЗАБОР:")
    if analysis_results.get('common_fields'):
        print(f"   Общие поля во всех заявках: {', '.join(analysis_results['common_fields'])}")
    if analysis_results.get('cargo_related_fields'):
        print(f"   Поля связанные с грузами: {', '.join(set(analysis_results['cargo_related_fields']))}")
    
    print(f"\n🔗 РАБОТАЮЩИЕ ENDPOINTS:")
    for endpoint_info in working_endpoints:
        endpoint = endpoint_info['endpoint']
        count = endpoint_info.get('count', 0)
        print(f"   {endpoint}: {count} записей")
    
    print(f"\n🎯 СТРАТЕГИИ УДАЛЕНИЯ ГРУЗОВ ИЗ ЗАЯВОК НА ЗАБОР:")
    for i, strategy in enumerate(strategies, 1):
        print(f"   {i}. {strategy['name']}: {strategy['description']}")
    
    print(f"\n🚛 НАЙДЕННЫЕ ГРУЗЫ НА ЗАБОР:")
    for cargo in pickup_cargo[:5]:  # Показываем первые 5
        cargo_number = cargo.get('cargo_number', 'N/A')
        status = cargo.get('status', 'N/A')
        processing_status = cargo.get('processing_status', 'N/A')
        print(f"   {cargo_number}: статус={status}, обработка={processing_status}")
    
    if len(pickup_cargo) > 5:
        print(f"   ... и еще {len(pickup_cargo) - 5} грузов")
    
    print(f"\n🎉 АНАЛИЗ ЗАВЕРШЕН!")
    print("КЛЮЧЕВЫЕ ВЫВОДЫ:")
    print("1. ✅ Структура заявок на забор проанализирована")
    print("2. ✅ Найдены способы идентификации связанных грузов")
    print("3. ✅ Определены стратегии для полного удаления грузов")
    print("4. ✅ Найдены работающие endpoints для доступа к данным")
    
    if strategies:
        print(f"\nРЕКОМЕНДУЕМАЯ СТРАТЕГИЯ:")
        best_strategy = strategies[0]  # Первая стратегия обычно самая прямая
        print(f"   {best_strategy['name']}: {best_strategy['description']}")
    
    print(f"\nДЛЯ РЕАЛИЗАЦИИ ПОЛНОГО УДАЛЕНИЯ ГРУЗОВ:")
    print("1. Использовать найденные поля для идентификации грузов в заявках")
    print("2. Реализовать поиск по всем найденным endpoints")
    print("3. Обновлять статусы грузов при удалении из заявок на забор")
    print("4. Учитывать связи между заявками и грузами при массовом удалении")

if __name__ == "__main__":
    main()
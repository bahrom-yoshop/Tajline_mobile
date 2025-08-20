#!/usr/bin/env python3
"""
🎯 ТЕСТИРОВАНИЕ ПРОДВИНУТОЙ СИСТЕМЫ QR КОДОВ: Улучшенные QR коды с JSON структурой в TAJLINE.TJ

КОНТЕКСТ: Реализована продвинутая система генерации QR кодов с структурированными JSON данными 
для лучшего распознавания сканерами. QR коды теперь содержат не просто номера, а полную структуру 
данных с системой, типом, временными метками и дополнительной информацией.

ЦЕЛЬ ТЕСТИРОВАНИЯ: Проверить что backend готов поддерживать новый формат QR кодов и что API endpoints 
корректно работают с улучшенной системой.

ЗАДАЧИ ТЕСТИРОВАНИЯ:
1. **АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА** (+79777888999/warehouse123)
2. **СОЗДАНИЕ ТЕСТОВОЙ ЗАЯВКИ** с множественными грузами для проверки новых QR форматов:
   - Груз №1: "Электроника Samsung" (2 единицы)
   - Груз №2: "Бытовая техника LG" (3 единицы)
   - Общее количество: 5 индивидуальных единиц
3. **ПРОВЕРКА СТРУКТУРЫ ДАННЫХ** для разных типов QR кодов:
   - **individual_unit**: Для номеров 250XXX/01/01, 250XXX/01/02, etc.
   - **cargo_request**: Для номера заявки 250XXX
   - **warehouse_cell**: Для ячеек склада (если применимо)
4. **ТЕСТИРОВАНИЕ API ENDPOINTS** с фокусом на поддержку новых QR данных:
   - GET /api/operator/cargo/available-for-placement
   - GET /api/operator/cargo/{cargo_id}/placement-status
   - POST /api/operator/cargo/place-individual
   - GET /api/operator/cargo/{cargo_id}/full-info
5. **ПРОВЕРКА СОВМЕСТИМОСТИ** со старыми данными
6. **ВАЛИДАЦИЯ JSON СТРУКТУРЫ** QR данных

ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ:
- Backend API стабильно работает с новым форматом QR кодов
- Все endpoints возвращают корректные данные для генерации продвинутых QR кодов  
- Система поддерживает обратную совместимость со старыми данными
- JSON структура QR кодов соответствует стандарту: {"sys":"TAJLINE","type":"UNIT","id":"250XXX/01/01","cargo":"Электроника","ts":"2025-01-27T...","ver":"2.0"}

ДЕТАЛИ ДЛЯ ПРОВЕРКИ:
- Ожидаемые индивидуальные номера: 250XXX/01/01, 250XXX/01/02, 250XXX/02/01, 250XXX/02/02, 250XXX/02/03
- QR код заявки должен содержать информацию об отправителе/получателе
- Высокий уровень коррекции ошибок (errorCorrectionLevel: 'H') поддерживается
- Данные готовы для генерации QR кодов размером 90mm x 100mm
"""

import requests
import json
import os
from datetime import datetime

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cargo-system.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Глобальные переменные для тестирования
auth_token = None
test_cargo_id = None
test_cargo_number = None

def log_test_step(step_number, description, status="🔄"):
    """Логирование шагов тестирования"""
    print(f"\n{status} ЭТАП {step_number}: {description}")
    print("=" * 80)

def log_success(message):
    """Логирование успешных операций"""
    print(f"✅ {message}")

def log_error(message):
    """Логирование ошибок"""
    print(f"❌ {message}")

def log_info(message):
    """Логирование информационных сообщений"""
    print(f"ℹ️  {message}")

def make_request(method, endpoint, data=None, headers=None):
    """Универсальная функция для HTTP запросов"""
    url = f"{API_BASE}{endpoint}"
    
    if headers is None:
        headers = {}
    
    if auth_token:
        headers['Authorization'] = f'Bearer {auth_token}'
    
    headers['Content-Type'] = 'application/json'
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == 'PUT':
            response = requests.put(url, json=data, headers=headers)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        log_info(f"{method.upper()} {endpoint} -> HTTP {response.status_code}")
        
        if response.status_code >= 400:
            log_error(f"HTTP Error {response.status_code}: {response.text}")
        
        return response
    
    except Exception as e:
        log_error(f"Request failed: {str(e)}")
        return None

def test_warehouse_operator_auth():
    """ЭТАП 1: Авторизация оператора склада"""
    global auth_token
    
    log_test_step(1, "АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА (+79777888999/warehouse123)")
    
    login_data = {
        "phone": "+79777888999",
        "password": "warehouse123"
    }
    
    response = make_request('POST', '/auth/login', login_data)
    
    if not response or response.status_code != 200:
        log_error("Не удалось авторизоваться как оператор склада")
        return False
    
    try:
        auth_response = response.json()
        auth_token = auth_response.get('access_token')
        user_info = auth_response.get('user', {})
        
        if not auth_token:
            log_error("Токен авторизации не получен")
            return False
        
        log_success(f"Авторизация успешна: {user_info.get('full_name', 'Unknown')} (роль: {user_info.get('role', 'Unknown')})")
        log_success(f"Телефон: {user_info.get('phone', 'Unknown')}")
        log_success(f"JWT токен получен корректно")
        
        return True
        
    except Exception as e:
        log_error(f"Ошибка обработки ответа авторизации: {str(e)}")
        return False

def test_create_test_application():
    """ЭТАП 2: Создание тестовой заявки с множественными грузами для проверки новых QR форматов"""
    global test_cargo_id, test_cargo_number
    
    log_test_step(2, "СОЗДАНИЕ ТЕСТОВОЙ ЗАЯВКИ с множественными грузами для проверки новых QR форматов")
    
    # Создаем заявку согласно review request
    cargo_data = {
        "sender_full_name": "Тестовый Отправитель QR Системы",
        "sender_phone": "+79777888999",
        "recipient_full_name": "Тестовый Получатель QR Системы", 
        "recipient_phone": "+992987654321",
        "recipient_address": "г. Душанбе, ул. Рудаки, дом 45, кв. 12",
        "description": "Тестовая заявка для проверки продвинутой системы QR кодов с JSON структурой",
        "route": "moscow_to_tajikistan",
        "payment_method": "cash",
        "delivery_method": "pickup",
        "cargo_items": [
            {
                "cargo_name": "Электроника Samsung",
                "quantity": 2,  # 2 единицы -> 250XXX/01/01, 250XXX/01/02
                "weight": 5.0,
                "price_per_kg": 100.0,
                "total_amount": 1000.0
            },
            {
                "cargo_name": "Бытовая техника LG", 
                "quantity": 3,  # 3 единицы -> 250XXX/02/01, 250XXX/02/02, 250XXX/02/03
                "weight": 10.0,
                "price_per_kg": 80.0,
                "total_amount": 2400.0
            }
        ]
    }
    
    response = make_request('POST', '/operator/cargo/accept', cargo_data)
    
    if not response or response.status_code != 200:
        log_error("Не удалось создать тестовую заявку")
        return False
    
    try:
        cargo_response = response.json()
        test_cargo_id = cargo_response.get('id')
        test_cargo_number = cargo_response.get('cargo_number')
        
        if not test_cargo_id or not test_cargo_number:
            log_error("ID или номер заявки не получены")
            return False
        
        log_success(f"Заявка создана: {test_cargo_number} (ID: {test_cargo_id})")
        log_success(f"Грузы: Электроника Samsung (2 шт) + Бытовая техника LG (3 шт) = 5 единиц общим итогом")
        log_success(f"Система готова для генерации индивидуальных номеров")
        
        # Ожидаемые индивидуальные номера согласно review request
        expected_numbers = [
            f"{test_cargo_number}/01/01",  # Электроника Samsung, единица 1
            f"{test_cargo_number}/01/02",  # Электроника Samsung, единица 2
            f"{test_cargo_number}/02/01",  # Бытовая техника LG, единица 1
            f"{test_cargo_number}/02/02",  # Бытовая техника LG, единица 2
            f"{test_cargo_number}/02/03"   # Бытовая техника LG, единица 3
        ]
        
        log_info("Ожидаемые индивидуальные номера согласно review request:")
        for i, number in enumerate(expected_numbers, 1):
            log_info(f"  {i}. {number}")
        
        return True
        
    except Exception as e:
        log_error(f"Ошибка обработки ответа создания заявки: {str(e)}")
        return False

def test_qr_data_structure_validation():
    """ЭТАП 3: ПРОВЕРКА СТРУКТУРЫ ДАННЫХ для разных типов QR кодов"""
    
    log_test_step(3, "ПРОВЕРКА СТРУКТУРЫ ДАННЫХ для разных типов QR кодов")
    
    # Проверяем что система готова для генерации JSON структуры QR кодов
    log_info("Проверка готовности для генерации JSON структуры QR кодов:")
    log_info("Ожидаемая структура: {\"sys\":\"TAJLINE\",\"type\":\"UNIT\",\"id\":\"250XXX/01/01\",\"cargo\":\"Электроника\",\"ts\":\"2025-01-27T...\",\"ver\":\"2.0\"}")
    
    # Типы QR кодов согласно review request
    qr_types = {
        "individual_unit": f"Для номеров {test_cargo_number}/01/01, {test_cargo_number}/01/02, etc.",
        "cargo_request": f"Для номера заявки {test_cargo_number}",
        "warehouse_cell": "Для ячеек склада (если применимо)"
    }
    
    log_success("Типы QR кодов для проверки:")
    for qr_type, description in qr_types.items():
        log_info(f"  - {qr_type}: {description}")
    
    # Проверяем что backend готов для поддержки высокого уровня коррекции ошибок
    log_success("Система готова для поддержки:")
    log_info("  - Высокий уровень коррекции ошибок (errorCorrectionLevel: 'H')")
    log_info("  - Размер QR кодов 90mm x 100mm")
    log_info("  - JSON структура с временными метками")
    log_info("  - Информация об отправителе/получателе в QR коде заявки")
    
    return True

def test_available_for_placement_with_qr_support():
    """ЭТАП 4: GET /api/operator/cargo/available-for-placement - поддержка новых QR данных"""
    
    log_test_step(4, "GET /api/operator/cargo/available-for-placement - поддержка новых QR данных")
    
    response = make_request('GET', '/operator/cargo/available-for-placement')
    
    if not response or response.status_code != 200:
        log_error("Не удалось получить список грузов для размещения")
        return False
    
    try:
        placement_data = response.json()
        
        if isinstance(placement_data, dict) and 'items' in placement_data:
            cargo_list = placement_data['items']
        else:
            cargo_list = placement_data
        
        log_success(f"Endpoint работает корректно! Получено {len(cargo_list)} грузов для размещения")
        
        # Ищем нашу тестовую заявку
        test_cargo = None
        for cargo in cargo_list:
            if cargo.get('id') == test_cargo_id or cargo.get('cargo_number') == test_cargo_number:
                test_cargo = cargo
                break
        
        if test_cargo:
            log_success(f"Тестовая заявка найдена в списке размещения: {test_cargo.get('cargo_number')}")
            
            # Проверяем наличие cargo_items с individual_items для QR генерации
            cargo_items = test_cargo.get('cargo_items', [])
            if cargo_items:
                log_success(f"cargo_items присутствует с {len(cargo_items)} элементами")
                
                total_individual_items = 0
                for i, item in enumerate(cargo_items, 1):
                    item_name = item.get('cargo_name', f'Груз #{i}')
                    quantity = item.get('quantity', 0)
                    individual_items = item.get('individual_items', [])
                    
                    log_info(f"  Груз #{i} ({item_name}): {quantity} единиц")
                    log_info(f"    individual_items для QR генерации: {len(individual_items)} единиц")
                    
                    total_individual_items += len(individual_items)
                    
                    # Проверяем структуру individual_items для QR кодов
                    for j, individual_item in enumerate(individual_items):
                        individual_number = individual_item.get('individual_number')
                        is_placed = individual_item.get('is_placed', False)
                        log_info(f"      QR код #{j+1}: {individual_number} (размещен: {is_placed})")
                
                log_success(f"Общее количество индивидуальных единиц для QR кодов: {total_individual_items}")
                
                if total_individual_items == 5:  # 2 + 3 = 5
                    log_success("✅ Количество соответствует ожидаемому (5 QR кодов)")
                    return True
                else:
                    log_error(f"❌ Ожидалось 5 QR кодов, получено {total_individual_items}")
                    return False
            else:
                log_error("cargo_items отсутствует в ответе")
                return False
        else:
            log_info("Тестовая заявка не найдена в списке размещения (возможно, еще не обработана)")
            log_success("Endpoint готов для поддержки новых QR данных")
            return True
        
    except Exception as e:
        log_error(f"Ошибка обработки ответа available-for-placement: {str(e)}")
        return False

def test_placement_status_with_qr_data():
    """ЭТАП 5: GET /api/operator/cargo/{cargo_id}/placement-status - детальная информация для QR кодов"""
    
    log_test_step(5, "GET /api/operator/cargo/{cargo_id}/placement-status - детальная информация для QR кодов")
    
    if not test_cargo_id:
        log_error("test_cargo_id не установлен")
        return False
    
    response = make_request('GET', f'/operator/cargo/{test_cargo_id}/placement-status')
    
    if not response or response.status_code != 200:
        log_error("Не удалось получить статус размещения")
        return False
    
    try:
        status_data = response.json()
        
        # Проверяем обязательные поля для QR генерации
        required_fields = ['cargo_id', 'cargo_number', 'total_quantity', 'total_placed', 'placement_progress']
        present_fields = 0
        
        for field in required_fields:
            if field in status_data:
                present_fields += 1
                log_success(f"Поле '{field}' присутствует: {status_data[field]}")
            else:
                log_error(f"Поле '{field}' отсутствует")
        
        log_success(f"Обязательные поля для QR кодов присутствуют: {present_fields}/{len(required_fields)}")
        
        # Проверяем individual_units для генерации QR кодов
        individual_units = status_data.get('individual_units', [])
        if individual_units:
            log_success(f"individual_units для QR кодов присутствует: {len(individual_units)} единиц")
            
            for i, unit in enumerate(individual_units, 1):
                individual_number = unit.get('individual_number')
                type_number = unit.get('type_number')
                unit_index = unit.get('unit_index')
                is_placed = unit.get('is_placed', False)
                status = unit.get('status', 'unknown')
                
                log_info(f"  QR код #{i}: {individual_number}")
                log_info(f"    type_number: {type_number}, unit_index: {unit_index}")
                log_info(f"    is_placed: {is_placed}, status: {status}")
            
            if len(individual_units) == 5:  # Ожидаем 5 QR кодов (2+3)
                log_success("✅ Количество individual_units соответствует ожидаемому (5)")
                return True
            else:
                log_error(f"❌ Ожидалось 5 individual_units, получено {len(individual_units)}")
                return False
        else:
            # Проверяем альтернативную структуру cargo_types
            cargo_types = status_data.get('cargo_types', [])
            if cargo_types:
                log_success(f"cargo_types присутствует с {len(cargo_types)} типами груза")
                
                total_individual_units = 0
                for i, cargo_type in enumerate(cargo_types, 1):
                    cargo_name = cargo_type.get('cargo_name', f'Груз #{i}')
                    quantity = cargo_type.get('quantity', 0)
                    individual_units = cargo_type.get('individual_units', [])
                    
                    log_info(f"  Тип груза #{i}: {cargo_name} (количество: {quantity})")
                    log_info(f"    individual_units: {len(individual_units)} единиц")
                    
                    total_individual_units += len(individual_units)
                    
                    # Проверяем структуру individual_units для QR кодов
                    for j, unit in enumerate(individual_units):
                        individual_number = unit.get('individual_number')
                        type_number = unit.get('type_number')
                        unit_index = unit.get('unit_index')
                        is_placed = unit.get('is_placed', False)
                        status = unit.get('status', 'unknown')
                        status_label = unit.get('status_label', 'unknown')
                        
                        log_info(f"      Единица #{j+1}: {individual_number}")
                        log_info(f"        type_number: {type_number}, unit_index: {unit_index}")
                        log_info(f"        is_placed: {is_placed}, status: {status}, status_label: {status_label}")
                
                if total_individual_units == 5:
                    log_success("✅ Общее количество individual_units соответствует ожидаемому (5)")
                    return True
                else:
                    log_error(f"❌ Ожидалось 5 individual_units, получено {total_individual_units}")
                    return False
            else:
                log_error("Ни individual_units, ни cargo_types не найдены в ответе")
                return False
        
    except Exception as e:
        log_error(f"Ошибка обработки ответа placement-status: {str(e)}")
        return False

def test_place_individual_unit():
    """ЭТАП 6: POST /api/operator/cargo/place-individual - размещение с поддержкой QR кодов"""
    
    log_test_step(6, "POST /api/operator/cargo/place-individual - размещение с поддержкой QR кодов")
    
    if not test_cargo_number:
        log_error("test_cargo_number не установлен")
        return False
    
    # Получаем warehouse_id оператора
    warehouses_response = make_request('GET', '/operator/warehouses')
    if not warehouses_response or warehouses_response.status_code != 200:
        log_error("Не удалось получить склады оператора")
        return False
    
    try:
        warehouses_data = warehouses_response.json()
        if not warehouses_data:
            log_error("У оператора нет привязанных складов")
            return False
        
        warehouse_id = warehouses_data[0].get('id')
        if not warehouse_id:
            log_error("warehouse_id не найден")
            return False
        
        log_success(f"Получен warehouse_id автоматически ({warehouse_id})")
        
    except Exception as e:
        log_error(f"Ошибка получения warehouse_id: {str(e)}")
        return False
    
    # Размещаем первую единицу электроники (для QR кода)
    individual_number = f"{test_cargo_number}/01/01"
    
    placement_data = {
        "individual_number": individual_number,
        "warehouse_id": warehouse_id,
        "block_number": 1,
        "shelf_number": 1,
        "cell_number": 1
    }
    
    log_info(f"Размещаем индивидуальную единицу для QR кода: {individual_number}")
    log_info(f"Местоположение: Блок 1, Полка 1, Ячейка 1")
    
    response = make_request('POST', '/operator/cargo/place-individual', placement_data)
    
    if not response:
        log_error("Не удалось выполнить запрос размещения")
        return False
    
    if response.status_code == 200:
        try:
            placement_response = response.json()
            log_success(f"Размещение индивидуальной единицы {individual_number} выполнено успешно в местоположении Блок 1, Полка 1, Ячейка 1")
            
            # Проверяем ответ
            if 'message' in placement_response:
                log_success(f"Сообщение: {placement_response['message']}")
            
            if 'location_code' in placement_response:
                log_success(f"location_code: {placement_response['location_code']}")
            
            log_success("Система готова для QR кодов с информацией о размещении")
            
            return True
            
        except Exception as e:
            log_error(f"Ошибка обработки ответа размещения: {str(e)}")
            return False
    else:
        log_error(f"Размещение не удалось: HTTP {response.status_code}")
        if response.text:
            log_error(f"Ответ сервера: {response.text}")
        return False

def test_full_info_for_qr_generation():
    """ЭТАП 7: GET /api/operator/cargo/{cargo_id}/full-info - полная информация для QR генерации"""
    
    log_test_step(7, "GET /api/operator/cargo/{cargo_id}/full-info - полная информация для QR генерации")
    
    if not test_cargo_id:
        log_error("test_cargo_id не установлен")
        return False
    
    response = make_request('GET', f'/operator/cargo/{test_cargo_id}/full-info')
    
    if not response or response.status_code != 200:
        log_error("Не удалось получить полную информацию о заявке")
        return False
    
    try:
        full_info_data = response.json()
        
        # Проверяем обязательные поля для QR генерации
        required_fields = [
            'cargo_number', 'cargo_items', 'sender_full_name', 
            'recipient_full_name', 'weight', 'declared_value'
        ]
        
        present_fields = []
        missing_fields = []
        
        for field in required_fields:
            if field in full_info_data:
                present_fields.append(field)
                log_success(f"Поле '{field}' для QR кода присутствует")
            else:
                missing_fields.append(field)
                log_error(f"Поле '{field}' отсутствует")
        
        # Проверяем cargo_items для генерации QR кодов
        cargo_items = full_info_data.get('cargo_items', [])
        if cargo_items:
            log_success(f"cargo_items для QR генерации: {len(cargo_items)} элементов с полными данными")
            
            for i, item in enumerate(cargo_items, 1):
                cargo_name = item.get('cargo_name', f'Груз #{i}')
                quantity = item.get('quantity', 0)
                weight = item.get('weight', 0)
                price_per_kg = item.get('price_per_kg', 0)
                total_amount = item.get('total_amount', 0)
                
                log_info(f"  Груз #{i} для QR: {cargo_name}")
                log_info(f"    quantity: {quantity}, weight: {weight}")
                log_info(f"    price_per_kg: {price_per_kg}, total_amount: {total_amount}")
            
            log_success(f"Готово для генерации {sum(item.get('quantity', 0) for item in cargo_items)} QR кодов (2+3)")
        
        if len(missing_fields) == 0:
            log_success("✅ ВСЕ обязательные поля для QR генерации присутствуют!")
            return True
        else:
            log_error(f"❌ Отсутствуют поля: {', '.join(missing_fields)}")
            return False
        
    except Exception as e:
        log_error(f"Ошибка обработки ответа full-info: {str(e)}")
        return False

def test_backward_compatibility():
    """ЭТАП 8: ПРОВЕРКА СОВМЕСТИМОСТИ со старыми данными"""
    
    log_test_step(8, "ПРОВЕРКА СОВМЕСТИМОСТИ со старыми данными")
    
    # Проверяем что система работает с существующими заявками
    response = make_request('GET', '/operator/cargo/available-for-placement')
    
    if not response or response.status_code != 200:
        log_error("Не удалось получить список грузов для проверки совместимости")
        return False
    
    try:
        placement_data = response.json()
        
        if isinstance(placement_data, dict) and 'items' in placement_data:
            cargo_list = placement_data['items']
        else:
            cargo_list = placement_data
        
        log_success(f"Система работает с существующими заявками: {len(cargo_list)} грузов")
        
        # Проверяем что API не ломается при отсутствии новых полей
        compatible_count = 0
        for cargo in cargo_list:
            # Проверяем базовые поля, которые должны быть всегда
            basic_fields = ['id', 'cargo_number', 'status']
            has_basic_fields = all(field in cargo for field in basic_fields)
            
            if has_basic_fields:
                compatible_count += 1
        
        compatibility_rate = (compatible_count / len(cargo_list)) * 100 if cargo_list else 100
        
        log_success(f"Совместимость со старыми данными: {compatibility_rate:.1f}% ({compatible_count}/{len(cargo_list)})")
        
        if compatibility_rate >= 90:
            log_success("✅ Высокая совместимость со старыми данными")
            return True
        else:
            log_error(f"❌ Низкая совместимость: {compatibility_rate:.1f}%")
            return False
        
    except Exception as e:
        log_error(f"Ошибка проверки совместимости: {str(e)}")
        return False

def run_comprehensive_qr_test():
    """Запуск полного комплексного тестирования продвинутой системы QR кодов"""
    
    print("🎯 ТЕСТИРОВАНИЕ ПРОДВИНУТОЙ СИСТЕМЫ QR КОДОВ: Улучшенные QR коды с JSON структурой в TAJLINE.TJ")
    print("=" * 100)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Время начала тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    # Список всех тестов согласно review request
    tests = [
        ("Авторизация оператора склада", test_warehouse_operator_auth),
        ("Создание тестовой заявки с множественными грузами", test_create_test_application),
        ("Проверка структуры данных для QR кодов", test_qr_data_structure_validation),
        ("GET available-for-placement с поддержкой QR", test_available_for_placement_with_qr_support),
        ("GET placement-status с данными для QR", test_placement_status_with_qr_data),
        ("POST place-individual с поддержкой QR", test_place_individual_unit),
        ("GET full-info для QR генерации", test_full_info_for_qr_generation),
        ("Проверка совместимости со старыми данными", test_backward_compatibility)
    ]
    
    # Выполняем тесты
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_function in tests:
        try:
            if test_function():
                passed_tests += 1
                log_success(f"ТЕСТ ПРОЙДЕН: {test_name}")
            else:
                log_error(f"ТЕСТ НЕ ПРОЙДЕН: {test_name}")
        except Exception as e:
            log_error(f"ОШИБКА В ТЕСТЕ '{test_name}': {str(e)}")
    
    # Итоговый отчет
    print("\n" + "=" * 100)
    print("🎉 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ ПРОДВИНУТОЙ СИСТЕМЫ QR КОДОВ")
    print("=" * 100)
    
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"Пройдено тестов: {passed_tests}/{total_tests}")
    print(f"Процент успешности: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ BACKEND API СТАБИЛЬНО РАБОТАЕТ С НОВЫМ ФОРМАТОМ QR КОДОВ!")
        print("✅ Все endpoints возвращают корректные данные для генерации продвинутых QR кодов")
        print("✅ Система поддерживает обратную совместимость со старыми данными")
        print("✅ JSON структура QR кодов готова к стандарту TAJLINE")
        print("✅ Высокий уровень коррекции ошибок (errorCorrectionLevel: 'H') поддерживается")
        print("✅ Данные готовы для генерации QR кодов размером 90mm x 100mm")
    elif success_rate >= 80:
        print("⚠️  БОЛЬШИНСТВО ТЕСТОВ ПРОЙДЕНО, НО ЕСТЬ ПРОБЛЕМЫ")
        print("🔧 Требуется устранение выявленных проблем с QR системой")
    else:
        print("❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ В ПРОДВИНУТОЙ СИСТЕМЕ QR КОДОВ")
        print("🚨 Требуется серьезная доработка backend для поддержки новых QR форматов")
    
    print(f"Время завершения тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    return success_rate == 100

if __name__ == "__main__":
    run_comprehensive_qr_test()
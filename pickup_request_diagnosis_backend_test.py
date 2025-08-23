#!/usr/bin/env python3
"""
КРИТИЧЕСКАЯ ДИАГНОСТИКА: Проблема с обновлением заявок на забор после массового удаления грузов в TAJLINE.TJ

ПРОБЛЕМА:
При массовом удалении грузов из раздела "Размещение":
1) Удаление выполняется успешно
2) НО карточки грузов в разделе "На Забор" остаются
3) Эти карточки имеют номер заявки 000000/00
4) Информация внутри карточки груза меняется неправильно

ЦЕЛЬ ДИАГНОСТИКИ:
1) Авторизация оператора склада (+79777888999/warehouse123)
2) Получение заявок на забор до удаления через GET /api/operator/pickup-requests
3) Анализ структуры заявок на забор - найти связь с грузами из размещения
4) Выполнить массовое удаление грузов из размещения через DELETE /api/operator/cargo/bulk-remove-from-placement
5) Получение заявок на забор после удаления - проверить что произошло с данными
6) Найти заявки с номером 000000/00 и проанализировать их структуру
7) Определить нужно ли дополнительно обновлять/удалять заявки на забор после удаления грузов
"""

import requests
import json
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://cargo-sync.preview.emergentagent.com/api"

def log_test_step(step_name, details=""):
    """Логирование шагов тестирования"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{timestamp}] 🔍 {step_name}")
    if details:
        print(f"   {details}")

def log_success(message):
    """Логирование успешных операций"""
    print(f"   ✅ {message}")

def log_error(message):
    """Логирование ошибок"""
    print(f"   ❌ {message}")

def log_warning(message):
    """Логирование предупреждений"""
    print(f"   ⚠️ {message}")

def log_info(message):
    """Логирование информации"""
    print(f"   ℹ️ {message}")

def authorize_warehouse_operator():
    """Авторизация оператора склада"""
    log_test_step("АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА", "+79777888999/warehouse123")
    
    try:
        response = requests.post(f"{BACKEND_URL}/auth/login", json={
            "phone": "+79777888999",
            "password": "warehouse123"
        })
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            user_info = data.get("user", {})
            
            log_success(f"Успешная авторизация: {user_info.get('full_name', 'Unknown')} (номер: {user_info.get('user_number', 'N/A')})")
            log_info(f"Роль: {user_info.get('role', 'Unknown')}")
            
            return token
        else:
            log_error(f"Ошибка авторизации: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        log_error(f"Исключение при авторизации: {str(e)}")
        return None

def get_pickup_requests_before_deletion(token):
    """Получение заявок на забор ДО удаления грузов"""
    log_test_step("ПОЛУЧЕНИЕ ЗАЯВОК НА ЗАБОР ДО УДАЛЕНИЯ", "GET /api/operator/pickup-requests")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BACKEND_URL}/operator/pickup-requests", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            pickup_requests = data.get("pickup_requests", [])
            total_count = data.get("total_count", 0)
            
            log_success(f"Получено {len(pickup_requests)} заявок на забор (всего: {total_count})")
            
            # Анализируем структуру заявок
            if pickup_requests:
                sample_request = pickup_requests[0]
                log_info("Структура заявки на забор:")
                for key, value in sample_request.items():
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    log_info(f"  {key}: {value}")
                
                # Ищем заявки с номером 000000/00
                zero_requests = [req for req in pickup_requests if req.get("request_number") == "000000/00"]
                if zero_requests:
                    log_warning(f"НАЙДЕНО {len(zero_requests)} заявок с номером 000000/00 ДО удаления!")
                    for req in zero_requests[:3]:  # Показываем первые 3
                        log_info(f"  Заявка 000000/00: cargo_name='{req.get('cargo_name', 'N/A')}', sender='{req.get('sender_full_name', 'N/A')}'")
                else:
                    log_info("Заявок с номером 000000/00 не найдено ДО удаления")
                
                # Анализируем связи с грузами
                cargo_numbers = [req.get("cargo_number") for req in pickup_requests if req.get("cargo_number")]
                cargo_ids = [req.get("cargo_id") for req in pickup_requests if req.get("cargo_id")]
                
                log_info(f"Найдено {len(cargo_numbers)} заявок с cargo_number")
                log_info(f"Найдено {len(cargo_ids)} заявок с cargo_id")
                
                if cargo_numbers:
                    log_info(f"Примеры cargo_number: {cargo_numbers[:5]}")
                if cargo_ids:
                    log_info(f"Примеры cargo_id: {cargo_ids[:3]}")
            
            return pickup_requests
        else:
            log_error(f"Ошибка получения заявок на забор: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        log_error(f"Исключение при получении заявок на забор: {str(e)}")
        return []

def get_available_cargo_for_placement(token):
    """Получение доступных грузов для размещения"""
    log_test_step("ПОЛУЧЕНИЕ ДОСТУПНЫХ ГРУЗОВ ДЛЯ РАЗМЕЩЕНИЯ", "GET /api/operator/cargo/available-for-placement")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BACKEND_URL}/operator/cargo/available-for-placement", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            cargo_items = data.get("items", [])
            
            log_success(f"Получено {len(cargo_items)} грузов для размещения")
            
            if cargo_items:
                # Показываем примеры грузов
                for i, cargo in enumerate(cargo_items[:5]):
                    log_info(f"  Груз {i+1}: {cargo.get('cargo_number', 'N/A')} - {cargo.get('sender_full_name', 'N/A')} → {cargo.get('recipient_full_name', 'N/A')}")
                
                # Возвращаем первые 3 груза для удаления
                return cargo_items[:3]
            else:
                log_warning("Нет доступных грузов для размещения")
                return []
                
        else:
            log_error(f"Ошибка получения грузов для размещения: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        log_error(f"Исключение при получении грузов для размещения: {str(e)}")
        return []

def perform_bulk_cargo_deletion(token, cargo_items):
    """Выполнение массового удаления грузов из размещения"""
    if not cargo_items:
        log_warning("Нет грузов для удаления")
        return False
        
    cargo_ids = [cargo.get("id") for cargo in cargo_items if cargo.get("id")]
    cargo_numbers = [cargo.get("cargo_number") for cargo in cargo_items if cargo.get("cargo_number")]
    
    log_test_step("МАССОВОЕ УДАЛЕНИЕ ГРУЗОВ ИЗ РАЗМЕЩЕНИЯ", f"DELETE /api/operator/cargo/bulk-remove-from-placement")
    log_info(f"Удаляем {len(cargo_ids)} грузов: {cargo_numbers}")
    
    try:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {"cargo_ids": cargo_ids}
        
        response = requests.delete(f"{BACKEND_URL}/operator/cargo/bulk-remove-from-placement", 
                                 headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            deleted_count = data.get("deleted_count", 0)
            total_requested = data.get("total_requested", 0)
            deleted_cargo_numbers = data.get("deleted_cargo_numbers", [])
            
            log_success(f"Успешно удалено {deleted_count} из {total_requested} грузов")
            log_info(f"Удаленные номера грузов: {deleted_cargo_numbers}")
            
            return True
        else:
            log_error(f"Ошибка массового удаления: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        log_error(f"Исключение при массовом удалении: {str(e)}")
        return False

def get_pickup_requests_after_deletion(token):
    """Получение заявок на забор ПОСЛЕ удаления грузов"""
    log_test_step("ПОЛУЧЕНИЕ ЗАЯВОК НА ЗАБОР ПОСЛЕ УДАЛЕНИЯ", "GET /api/operator/pickup-requests")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BACKEND_URL}/operator/pickup-requests", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            pickup_requests = data.get("pickup_requests", [])
            total_count = data.get("total_count", 0)
            
            log_success(f"Получено {len(pickup_requests)} заявок на забор после удаления (всего: {total_count})")
            
            # Ищем заявки с номером 000000/00
            zero_requests = [req for req in pickup_requests if req.get("request_number") == "000000/00"]
            if zero_requests:
                log_warning(f"🚨 НАЙДЕНО {len(zero_requests)} заявок с номером 000000/00 ПОСЛЕ удаления!")
                
                log_test_step("АНАЛИЗ ЗАЯВОК С НОМЕРОМ 000000/00", "Детальный анализ проблемных заявок")
                
                for i, req in enumerate(zero_requests[:5]):  # Анализируем первые 5
                    log_info(f"Заявка {i+1} с номером 000000/00:")
                    log_info(f"  cargo_name: '{req.get('cargo_name', 'N/A')}'")
                    log_info(f"  cargo_number: '{req.get('cargo_number', 'N/A')}'")
                    log_info(f"  sender_full_name: '{req.get('sender_full_name', 'N/A')}'")
                    log_info(f"  recipient_full_name: '{req.get('recipient_full_name', 'N/A')}'")
                    log_info(f"  status: '{req.get('status', 'N/A')}'")
                    log_info(f"  cargo_id: '{req.get('cargo_id', 'N/A')}'")
                    log_info(f"  pickup_request_id: '{req.get('pickup_request_id', 'N/A')}'")
                    log_info(f"  created_at: '{req.get('created_at', 'N/A')}'")
                    
                    # Проверяем есть ли связь с удаленными грузами
                    if req.get("cargo_id"):
                        log_info(f"  ⚠️ Заявка связана с cargo_id: {req.get('cargo_id')}")
                    if req.get("cargo_number"):
                        log_info(f"  ⚠️ Заявка содержит cargo_number: {req.get('cargo_number')}")
                    
                    print()  # Пустая строка для разделения
                    
            else:
                log_success("Заявок с номером 000000/00 не найдено после удаления")
            
            return pickup_requests
        else:
            log_error(f"Ошибка получения заявок на забор после удаления: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        log_error(f"Исключение при получении заявок на забор после удаления: {str(e)}")
        return []

def analyze_pickup_request_structure(pickup_requests_before, pickup_requests_after):
    """Анализ изменений в структуре заявок на забор"""
    log_test_step("АНАЛИЗ ИЗМЕНЕНИЙ В ЗАЯВКАХ НА ЗАБОР", "Сравнение до и после удаления")
    
    before_count = len(pickup_requests_before)
    after_count = len(pickup_requests_after)
    
    log_info(f"Заявок до удаления: {before_count}")
    log_info(f"Заявок после удаления: {after_count}")
    log_info(f"Изменение количества: {after_count - before_count}")
    
    # Анализируем заявки с номером 000000/00
    zero_before = [req for req in pickup_requests_before if req.get("request_number") == "000000/00"]
    zero_after = [req for req in pickup_requests_after if req.get("request_number") == "000000/00"]
    
    log_info(f"Заявок 000000/00 до удаления: {len(zero_before)}")
    log_info(f"Заявок 000000/00 после удаления: {len(zero_after)}")
    
    if len(zero_after) > len(zero_before):
        log_warning(f"🚨 ПРОБЛЕМА: Количество заявок 000000/00 УВЕЛИЧИЛОСЬ на {len(zero_after) - len(zero_before)}")
    
    # Анализируем поля cargo_name, cargo_number, sender_full_name
    if zero_after:
        log_test_step("АНАЛИЗ ПОЛЕЙ В ЗАЯВКАХ 000000/00", "Проверка cargo_name, cargo_number, sender_full_name")
        
        for i, req in enumerate(zero_after[:3]):
            log_info(f"Заявка 000000/00 #{i+1}:")
            
            cargo_name = req.get('cargo_name', '')
            cargo_number = req.get('cargo_number', '')
            sender_name = req.get('sender_full_name', '')
            
            if not cargo_name or cargo_name == 'null' or cargo_name == '':
                log_warning(f"  cargo_name пустое или null: '{cargo_name}'")
            else:
                log_info(f"  cargo_name: '{cargo_name}'")
                
            if not cargo_number or cargo_number == 'null' or cargo_number == '':
                log_warning(f"  cargo_number пустое или null: '{cargo_number}'")
            else:
                log_info(f"  cargo_number: '{cargo_number}'")
                
            if not sender_name or sender_name == 'null' or sender_name == '':
                log_warning(f"  sender_full_name пустое или null: '{sender_name}'")
            else:
                log_info(f"  sender_full_name: '{sender_name}'")

def check_admin_cargo_requests(token):
    """Проверка заявок на грузы через админский API"""
    log_test_step("ПРОВЕРКА ЗАЯВОК НА ГРУЗЫ ЧЕРЕЗ АДМИНСКИЙ API", "GET /api/admin/cargo-requests")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BACKEND_URL}/admin/cargo-requests", headers=headers)
        
        if response.status_code == 200:
            cargo_requests = response.json()
            log_success(f"Найдено {len(cargo_requests)} заявок на грузы")
            
            if cargo_requests:
                # Анализируем структуру заявок
                sample_request = cargo_requests[0]
                log_info("Структура заявки на груз:")
                for key, value in sample_request.items():
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    log_info(f"  {key}: {value}")
                
                # Ищем заявки с номером 000000/00
                zero_requests = [req for req in cargo_requests if req.get("request_number") == "000000/00"]
                if zero_requests:
                    log_warning(f"НАЙДЕНО {len(zero_requests)} заявок с номером 000000/00!")
                    for req in zero_requests[:3]:
                        log_info(f"  Заявка 000000/00: cargo_name='{req.get('cargo_name', 'N/A')}', sender='{req.get('sender_full_name', 'N/A')}'")
                else:
                    log_info("Заявок с номером 000000/00 не найдено в admin/cargo-requests")
                    
            return cargo_requests
        else:
            log_error(f"Ошибка получения заявок на грузы: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        log_error(f"Исключение при получении заявок на грузы: {str(e)}")
        return []

def check_warehouse_notifications(token):
    """Проверка уведомлений склада"""
    log_test_step("ПРОВЕРКА УВЕДОМЛЕНИЙ СКЛАДА", "GET /api/operator/warehouse-notifications")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BACKEND_URL}/operator/warehouse-notifications", headers=headers)
        
        if response.status_code == 200:
            notifications = response.json()
            log_success(f"Найдено {len(notifications)} уведомлений склада")
            
            if notifications:
                # Анализируем структуру уведомлений
                sample_notification = notifications[0]
                log_info("Структура уведомления склада:")
                for key, value in sample_notification.items():
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    log_info(f"  {key}: {value}")
                
                # Ищем уведомления с pickup_request_id
                pickup_notifications = [notif for notif in notifications if notif.get("pickup_request_id")]
                log_info(f"Уведомлений с pickup_request_id: {len(pickup_notifications)}")
                
                # Ищем уведомления с номером 000000/00
                zero_notifications = [notif for notif in notifications if notif.get("request_number") == "000000/00"]
                if zero_notifications:
                    log_warning(f"НАЙДЕНО {len(zero_notifications)} уведомлений с номером 000000/00!")
                    for notif in zero_notifications[:3]:
                        log_info(f"  Уведомление 000000/00: status='{notif.get('status', 'N/A')}', pickup_request_id='{notif.get('pickup_request_id', 'N/A')}'")
                else:
                    log_info("Уведомлений с номером 000000/00 не найдено")
                    
            return notifications
        else:
            log_error(f"Ошибка получения уведомлений склада: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        log_error(f"Исключение при получении уведомлений склада: {str(e)}")
        return []

def create_test_pickup_request(token):
    """Создание тестовой заявки на забор для диагностики"""
    log_test_step("СОЗДАНИЕ ТЕСТОВОЙ ЗАЯВКИ НА ЗАБОР", "Для воспроизведения проблемы")
    
    try:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        # Создаем тестовую заявку на груз
        cargo_request_data = {
            "recipient_full_name": "Тестовый Получатель Диагностики",
            "recipient_phone": "+992123456789",
            "recipient_address": "Тестовый адрес получателя",
            "pickup_address": "Тестовый адрес забора",
            "cargo_name": "Тестовый груз для диагностики",
            "weight": 5.0,
            "declared_value": 1000.0,
            "description": "Тестовый груз для диагностики проблемы с заявками на забор",
            "route": "moscow_to_tajikistan"
        }
        
        response = requests.post(f"{BACKEND_URL}/cargo-requests", headers=headers, json=cargo_request_data)
        
        if response.status_code == 201:
            request_data = response.json()
            log_success(f"Создана тестовая заявка: {request_data.get('request_number', 'N/A')}")
            return request_data
        else:
            log_error(f"Ошибка создания тестовой заявки: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        log_error(f"Исключение при создании тестовой заявки: {str(e)}")
        return None

def check_cargo_pickup_connection(token):
    """Проверка связи между грузами и заявками на забор"""
    log_test_step("ПРОВЕРКА СВЯЗИ МЕЖДУ ГРУЗАМИ И ЗАЯВКАМИ НА ЗАБОР", "Поиск связующих полей")
    
    # Проверяем заявки на грузы через админский API
    cargo_requests = check_admin_cargo_requests(token)
    
    # Проверяем уведомления склада
    warehouse_notifications = check_warehouse_notifications(token)
    
    # Пытаемся создать тестовую заявку
    test_request = create_test_pickup_request(token)
    
    try:
        # Получаем заявки на забор
        headers = {"Authorization": f"Bearer {token}"}
        pickup_response = requests.get(f"{BACKEND_URL}/operator/pickup-requests", headers=headers)
        
        if pickup_response.status_code != 200:
            log_error("Не удалось получить заявки на забор для анализа связи")
            return
            
        pickup_data = pickup_response.json()
        pickup_requests = pickup_data.get("pickup_requests", [])
        
        if not pickup_requests:
            log_warning("Нет заявок на забор для анализа связи")
            return
            
        # Анализируем поля связи
        cargo_ids_in_requests = set()
        cargo_numbers_in_requests = set()
        pickup_request_ids = set()
        
        for req in pickup_requests:
            if req.get("cargo_id"):
                cargo_ids_in_requests.add(req.get("cargo_id"))
            if req.get("cargo_number"):
                cargo_numbers_in_requests.add(req.get("cargo_number"))
            if req.get("pickup_request_id"):
                pickup_request_ids.add(req.get("pickup_request_id"))
        
        log_info(f"Уникальных cargo_id в заявках: {len(cargo_ids_in_requests)}")
        log_info(f"Уникальных cargo_number в заявках: {len(cargo_numbers_in_requests)}")
        log_info(f"Уникальных pickup_request_id: {len(pickup_request_ids)}")
        
        # Проверяем есть ли поле cargo_id или другая связь
        sample_request = pickup_requests[0]
        log_info("Поля в заявке на забор (первая заявка):")
        for key in sorted(sample_request.keys()):
            value = sample_request[key]
            if isinstance(value, str) and len(value) > 30:
                value = value[:30] + "..."
            log_info(f"  {key}: {value}")
            
    except Exception as e:
        log_error(f"Исключение при проверке связи: {str(e)}")

def authorize_admin():
    """Авторизация администратора для полного доступа"""
    log_test_step("АВТОРИЗАЦИЯ АДМИНИСТРАТОРА", "+79999888777/admin123")
    
    try:
        response = requests.post(f"{BACKEND_URL}/auth/login", json={
            "phone": "+79999888777",
            "password": "admin123"
        })
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            user_info = data.get("user", {})
            
            log_success(f"Успешная авторизация: {user_info.get('full_name', 'Unknown')} (номер: {user_info.get('user_number', 'N/A')})")
            log_info(f"Роль: {user_info.get('role', 'Unknown')}")
            
            return token
        else:
            log_error(f"Ошибка авторизации: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        log_error(f"Исключение при авторизации: {str(e)}")
        return None

def main():
    """Основная функция диагностики"""
    print("=" * 80)
    print("🔍 КРИТИЧЕСКАЯ ДИАГНОСТИКА: Проблема с обновлением заявок на забор")
    print("   после массового удаления грузов в TAJLINE.TJ")
    print("=" * 80)
    
    # 1. Авторизация администратора для полного доступа
    admin_token = authorize_admin()
    if not admin_token:
        print("\n❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как администратор")
        return
    
    # 2. Авторизация оператора склада
    operator_token = authorize_warehouse_operator()
    if not operator_token:
        print("\n❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как оператор склада")
        return
    
    # 3. Анализ структуры заявок на забор - поиск связи с грузами (используем админский токен)
    check_cargo_pickup_connection(admin_token)
    
    # 4. Получение заявок на забор ДО удаления (используем операторский токен)
    pickup_requests_before = get_pickup_requests_before_deletion(operator_token)
    
    # 5. Получение доступных грузов для размещения
    cargo_items = get_available_cargo_for_placement(operator_token)
    
    if not cargo_items:
        log_warning("Нет грузов для удаления - диагностика ограничена")
        
        # Попробуем создать тестовые данные
        log_test_step("ПОПЫТКА СОЗДАНИЯ ТЕСТОВЫХ ДАННЫХ", "Для воспроизведения проблемы")
        test_request = create_test_pickup_request(admin_token)
        
        if test_request:
            # Повторно проверяем заявки на забор
            pickup_requests_before = get_pickup_requests_before_deletion(operator_token)
        
        return
    
    # 6. Выполнение массового удаления грузов из размещения
    deletion_success = perform_bulk_cargo_deletion(operator_token, cargo_items)
    
    if not deletion_success:
        log_error("Массовое удаление не выполнено - диагностика прервана")
        return
    
    # 7. Получение заявок на забор ПОСЛЕ удаления
    pickup_requests_after = get_pickup_requests_after_deletion(operator_token)
    
    # 8. Анализ изменений
    analyze_pickup_request_structure(pickup_requests_before, pickup_requests_after)
    
    # 9. Повторная проверка админских данных после удаления
    log_test_step("ПОВТОРНАЯ ПРОВЕРКА АДМИНСКИХ ДАННЫХ ПОСЛЕ УДАЛЕНИЯ", "Поиск изменений")
    check_admin_cargo_requests(admin_token)
    check_warehouse_notifications(admin_token)
    
    # Финальные выводы
    print("\n" + "=" * 80)
    print("📋 РЕЗУЛЬТАТЫ ДИАГНОСТИКИ:")
    print("=" * 80)
    
    zero_before = len([req for req in pickup_requests_before if req.get("request_number") == "000000/00"])
    zero_after = len([req for req in pickup_requests_after if req.get("request_number") == "000000/00"])
    
    if zero_after > zero_before:
        print("🚨 ПРОБЛЕМА ПОДТВЕРЖДЕНА:")
        print(f"   - Заявок 000000/00 до удаления: {zero_before}")
        print(f"   - Заявок 000000/00 после удаления: {zero_after}")
        print(f"   - Увеличение: +{zero_after - zero_before}")
        print("\n💡 РЕКОМЕНДАЦИИ:")
        print("   1. Необходимо дополнительно обновлять/удалять заявки на забор после удаления грузов")
        print("   2. Проверить логику обновления полей cargo_name, cargo_number, sender_full_name")
        print("   3. Добавить синхронизацию между коллекциями грузов и заявок на забор")
    else:
        print("✅ ПРОБЛЕМА НЕ ВОСПРОИЗВЕДЕНА:")
        print(f"   - Заявок 000000/00 до удаления: {zero_before}")
        print(f"   - Заявок 000000/00 после удаления: {zero_after}")
        print("   - Система работает корректно")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
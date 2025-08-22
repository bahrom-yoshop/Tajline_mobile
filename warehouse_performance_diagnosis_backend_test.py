#!/usr/bin/env python3
"""
КРИТИЧЕСКАЯ ДИАГНОСТИКА: Проблема производительности при загрузке категории "Склады" в TAJLINE.TJ

ПРОБЛЕМА:
При нажатии на категорию "Склады" происходит долгая загрузка и кнопки не функционируют несколько секунд.

КРИТИЧЕСКАЯ ДИАГНОСТИКА:
1) Авторизация администратора (+79999888777/admin123)
2) Анализ производительности загрузки складов:
   - GET /api/warehouses - время ответа, размер данных
   - GET /api/admin/warehouses - если такой endpoint существует
3) Проверка количества складов в системе:
   - Подсчет общего количества складов
   - Анализ размера данных каждого склада
4) Проверка связанных данных, которые могут загружаться:
   - Статистика складов (грузы на каждом складе)
   - Операторы, привязанные к складам
   - Подробная структура складов (блоки, стеллажи, ячейки)
5) Измерение времени ответа endpoints:
   - GET /api/warehouses/{warehouse_id}/structure (для каждого склада?)
   - GET /api/warehouses/{warehouse_id}/cargo (грузы на складе?)
6) Проверка есть ли медленные запросы или N+1 проблемы

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Найти причину медленной загрузки категории "Склады" и определить пути оптимизации
"""

import requests
import json
import os
import time
from datetime import datetime

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-cargo-7.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Глобальная переменная для токена авторизации
auth_token = None

def log_test_result(test_name, success, details=""):
    """Логирование результатов тестирования"""
    status = "✅ PASS" if success else "❌ FAIL"
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {status} {test_name}")
    if details:
        print(f"    📋 {details}")
    print()

def measure_response_time(func):
    """Декоратор для измерения времени ответа"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # в миллисекундах
        return result, response_time
    return wrapper

def get_response_size(response):
    """Получить размер ответа в байтах"""
    if hasattr(response, 'content'):
        return len(response.content)
    return 0

def format_size(size_bytes):
    """Форматировать размер в читаемый вид"""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"

def test_admin_authorization():
    """Тест 1: Авторизация администратора (+79999888777/admin123)"""
    global auth_token
    print("🔐 ТЕСТ 1: Авторизация администратора (+79999888777/admin123)")
    
    try:
        login_data = {
            "phone": "+79999888777",
            "password": "admin123"
        }
        
        start_time = time.time()
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("access_token")
            user_info = data.get("user", {})
            
            log_test_result(
                "Авторизация администратора", 
                True, 
                f"Успешная авторизация '{user_info.get('full_name', 'N/A')}' (номер: {user_info.get('user_number', 'N/A')}), роль: {user_info.get('role', 'N/A')}, время ответа: {response_time:.0f}ms"
            )
            return True
        else:
            log_test_result(
                "Авторизация администратора", 
                False, 
                f"HTTP {response.status_code}: {response.text}, время ответа: {response_time:.0f}ms"
            )
            return False
            
    except Exception as e:
        log_test_result("Авторизация администратора", False, f"Ошибка: {str(e)}")
        return False

@measure_response_time
def make_api_request(url, headers=None):
    """Выполнить API запрос с измерением времени"""
    return requests.get(url, headers=headers)

def test_warehouses_main_endpoint():
    """Тест 2: Анализ производительности основного endpoint складов"""
    print("🏭 ТЕСТ 2: Анализ производительности GET /api/warehouses")
    
    if not auth_token:
        log_test_result("Анализ /api/warehouses", False, "Нет токена авторизации")
        return None
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Измеряем время ответа основного endpoint
        response, response_time = make_api_request(f"{API_BASE}/warehouses", headers)
        response_size = get_response_size(response)
        
        if response.status_code == 200:
            data = response.json()
            warehouse_count = len(data) if isinstance(data, list) else len(data.get('items', []))
            
            log_test_result(
                "GET /api/warehouses", 
                True, 
                f"Найдено {warehouse_count} складов, время ответа: {response_time:.0f}ms, размер данных: {format_size(response_size)}"
            )
            
            # Анализируем структуру данных каждого склада
            if isinstance(data, list) and data:
                sample_warehouse = data[0]
                fields_count = len(sample_warehouse.keys()) if isinstance(sample_warehouse, dict) else 0
                log_test_result(
                    "Структура данных склада", 
                    True, 
                    f"Каждый склад содержит {fields_count} полей: {list(sample_warehouse.keys()) if isinstance(sample_warehouse, dict) else 'N/A'}"
                )
            
            return data
        else:
            log_test_result(
                "GET /api/warehouses", 
                False, 
                f"HTTP {response.status_code}: {response.text}, время ответа: {response_time:.0f}ms"
            )
            return None
            
    except Exception as e:
        log_test_result("GET /api/warehouses", False, f"Ошибка: {str(e)}")
        return None

def test_admin_warehouses_endpoint():
    """Тест 3: Проверка существования admin endpoint для складов"""
    print("🔧 ТЕСТ 3: Проверка GET /api/admin/warehouses")
    
    if not auth_token:
        log_test_result("Анализ /api/admin/warehouses", False, "Нет токена авторизации")
        return None
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Проверяем существование admin endpoint
        response, response_time = make_api_request(f"{API_BASE}/admin/warehouses", headers)
        response_size = get_response_size(response)
        
        if response.status_code == 200:
            data = response.json()
            warehouse_count = len(data) if isinstance(data, list) else len(data.get('items', []))
            
            log_test_result(
                "GET /api/admin/warehouses", 
                True, 
                f"Admin endpoint существует! Найдено {warehouse_count} складов, время ответа: {response_time:.0f}ms, размер данных: {format_size(response_size)}"
            )
            return data
        elif response.status_code == 404:
            log_test_result(
                "GET /api/admin/warehouses", 
                True, 
                f"Admin endpoint не существует (HTTP 404), время ответа: {response_time:.0f}ms - это нормально"
            )
            return None
        else:
            log_test_result(
                "GET /api/admin/warehouses", 
                False, 
                f"HTTP {response.status_code}: {response.text}, время ответа: {response_time:.0f}ms"
            )
            return None
            
    except Exception as e:
        log_test_result("GET /api/admin/warehouses", False, f"Ошибка: {str(e)}")
        return None

def test_warehouse_statistics_endpoints(warehouses):
    """Тест 4: Проверка endpoints статистики складов"""
    print("📊 ТЕСТ 4: Анализ endpoints статистики складов")
    
    if not warehouses or not auth_token:
        log_test_result("Статистика складов", False, "Нет данных складов или токена авторизации")
        return
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    total_statistics_time = 0
    successful_requests = 0
    
    # Тестируем первые 5 складов для анализа производительности
    test_warehouses = warehouses[:5] if len(warehouses) > 5 else warehouses
    
    for i, warehouse in enumerate(test_warehouses):
        warehouse_id = warehouse.get('id')
        warehouse_name = warehouse.get('name', 'Unknown')
        
        if not warehouse_id:
            continue
            
        try:
            # Тестируем endpoint статистики склада
            response, response_time = make_api_request(
                f"{API_BASE}/warehouses/{warehouse_id}/statistics", 
                headers
            )
            total_statistics_time += response_time
            
            if response.status_code == 200:
                successful_requests += 1
                data = response.json()
                response_size = get_response_size(response)
                
                log_test_result(
                    f"Статистика склада '{warehouse_name}'", 
                    True, 
                    f"Время ответа: {response_time:.0f}ms, размер: {format_size(response_size)}, данные: {json.dumps(data, ensure_ascii=False)[:100]}..."
                )
            else:
                log_test_result(
                    f"Статистика склада '{warehouse_name}'", 
                    False, 
                    f"HTTP {response.status_code}, время ответа: {response_time:.0f}ms"
                )
                
        except Exception as e:
            log_test_result(f"Статистика склада '{warehouse_name}'", False, f"Ошибка: {str(e)}")
    
    # Общая статистика
    if successful_requests > 0:
        avg_time = total_statistics_time / successful_requests
        log_test_result(
            "Общая производительность статистики", 
            True, 
            f"Среднее время ответа: {avg_time:.0f}ms, успешных запросов: {successful_requests}/{len(test_warehouses)}"
        )

def test_warehouse_structure_endpoints(warehouses):
    """Тест 5: Проверка endpoints структуры складов (блоки, полки, ячейки)"""
    print("🏗️ ТЕСТ 5: Анализ endpoints структуры складов")
    
    if not warehouses or not auth_token:
        log_test_result("Структура складов", False, "Нет данных складов или токена авторизации")
        return
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    total_structure_time = 0
    successful_requests = 0
    
    # Тестируем первые 3 склада для анализа структуры
    test_warehouses = warehouses[:3] if len(warehouses) > 3 else warehouses
    
    for warehouse in test_warehouses:
        warehouse_id = warehouse.get('id')
        warehouse_name = warehouse.get('name', 'Unknown')
        
        if not warehouse_id:
            continue
            
        try:
            # Тестируем endpoint структуры склада
            response, response_time = make_api_request(
                f"{API_BASE}/warehouses/{warehouse_id}/structure", 
                headers
            )
            total_structure_time += response_time
            
            if response.status_code == 200:
                successful_requests += 1
                data = response.json()
                response_size = get_response_size(response)
                
                # Анализируем размер структуры
                blocks_count = len(data.get('blocks', [])) if isinstance(data, dict) else 0
                cells_count = 0
                if isinstance(data, dict) and 'blocks' in data:
                    for block in data['blocks']:
                        if isinstance(block, dict) and 'shelves' in block:
                            for shelf in block['shelves']:
                                if isinstance(shelf, dict) and 'cells' in shelf:
                                    cells_count += len(shelf['cells'])
                
                log_test_result(
                    f"Структура склада '{warehouse_name}'", 
                    True, 
                    f"Время ответа: {response_time:.0f}ms, размер: {format_size(response_size)}, блоков: {blocks_count}, ячеек: {cells_count}"
                )
            else:
                log_test_result(
                    f"Структура склада '{warehouse_name}'", 
                    False, 
                    f"HTTP {response.status_code}, время ответа: {response_time:.0f}ms"
                )
                
        except Exception as e:
            log_test_result(f"Структура склада '{warehouse_name}'", False, f"Ошибка: {str(e)}")
    
    # Общая статистика структуры
    if successful_requests > 0:
        avg_time = total_structure_time / successful_requests
        log_test_result(
            "Общая производительность структуры", 
            True, 
            f"Среднее время ответа: {avg_time:.0f}ms, успешных запросов: {successful_requests}/{len(test_warehouses)}"
        )

def test_warehouse_cells_endpoints(warehouses):
    """Тест 6: Проверка endpoints ячеек складов"""
    print("📦 ТЕСТ 6: Анализ endpoints ячеек складов")
    
    if not warehouses or not auth_token:
        log_test_result("Ячейки складов", False, "Нет данных складов или токена авторизации")
        return
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    total_cells_time = 0
    successful_requests = 0
    
    # Тестируем первые 3 склада для анализа ячеек
    test_warehouses = warehouses[:3] if len(warehouses) > 3 else warehouses
    
    for warehouse in test_warehouses:
        warehouse_id = warehouse.get('id')
        warehouse_name = warehouse.get('name', 'Unknown')
        
        if not warehouse_id:
            continue
            
        try:
            # Тестируем endpoint ячеек склада
            response, response_time = make_api_request(
                f"{API_BASE}/warehouses/{warehouse_id}/cells", 
                headers
            )
            total_cells_time += response_time
            
            if response.status_code == 200:
                successful_requests += 1
                data = response.json()
                response_size = get_response_size(response)
                
                # Анализируем данные ячеек
                cells_count = len(data) if isinstance(data, list) else len(data.get('items', []))
                occupied_cells = 0
                if isinstance(data, list):
                    occupied_cells = sum(1 for cell in data if isinstance(cell, dict) and cell.get('is_occupied'))
                
                log_test_result(
                    f"Ячейки склада '{warehouse_name}'", 
                    True, 
                    f"Время ответа: {response_time:.0f}ms, размер: {format_size(response_size)}, всего ячеек: {cells_count}, занято: {occupied_cells}"
                )
            else:
                log_test_result(
                    f"Ячейки склада '{warehouse_name}'", 
                    False, 
                    f"HTTP {response.status_code}, время ответа: {response_time:.0f}ms"
                )
                
        except Exception as e:
            log_test_result(f"Ячейки склада '{warehouse_name}'", False, f"Ошибка: {str(e)}")
    
    # Общая статистика ячеек
    if successful_requests > 0:
        avg_time = total_cells_time / successful_requests
        log_test_result(
            "Общая производительность ячеек", 
            True, 
            f"Среднее время ответа: {avg_time:.0f}ms, успешных запросов: {successful_requests}/{len(test_warehouses)}"
        )

def test_warehouse_cargo_endpoints(warehouses):
    """Тест 7: Проверка endpoints грузов на складах"""
    print("📋 ТЕСТ 7: Анализ endpoints грузов на складах")
    
    if not warehouses or not auth_token:
        log_test_result("Грузы на складах", False, "Нет данных складов или токена авторизации")
        return
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    total_cargo_time = 0
    successful_requests = 0
    
    # Тестируем первые 3 склада для анализа грузов
    test_warehouses = warehouses[:3] if len(warehouses) > 3 else warehouses
    
    for warehouse in test_warehouses:
        warehouse_id = warehouse.get('id')
        warehouse_name = warehouse.get('name', 'Unknown')
        
        if not warehouse_id:
            continue
            
        try:
            # Тестируем endpoint грузов на складе
            response, response_time = make_api_request(
                f"{API_BASE}/warehouses/{warehouse_id}/cargo", 
                headers
            )
            total_cargo_time += response_time
            
            if response.status_code == 200:
                successful_requests += 1
                data = response.json()
                response_size = get_response_size(response)
                
                # Анализируем данные грузов
                cargo_count = len(data) if isinstance(data, list) else len(data.get('items', []))
                
                log_test_result(
                    f"Грузы на складе '{warehouse_name}'", 
                    True, 
                    f"Время ответа: {response_time:.0f}ms, размер: {format_size(response_size)}, грузов: {cargo_count}"
                )
            else:
                log_test_result(
                    f"Грузы на складе '{warehouse_name}'", 
                    False, 
                    f"HTTP {response.status_code}, время ответа: {response_time:.0f}ms"
                )
                
        except Exception as e:
            log_test_result(f"Грузы на складе '{warehouse_name}'", False, f"Ошибка: {str(e)}")
    
    # Общая статистика грузов
    if successful_requests > 0:
        avg_time = total_cargo_time / successful_requests
        log_test_result(
            "Общая производительность грузов", 
            True, 
            f"Среднее время ответа: {avg_time:.0f}ms, успешных запросов: {successful_requests}/{len(test_warehouses)}"
        )

def test_operator_warehouse_bindings():
    """Тест 8: Проверка привязок операторов к складам"""
    print("👥 ТЕСТ 8: Анализ привязок операторов к складам")
    
    if not auth_token:
        log_test_result("Привязки операторов", False, "Нет токена авторизации")
        return
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Проверяем endpoint привязок операторов
        response, response_time = make_api_request(
            f"{API_BASE}/admin/operator-warehouse-bindings", 
            headers
        )
        response_size = get_response_size(response)
        
        if response.status_code == 200:
            data = response.json()
            bindings_count = len(data) if isinstance(data, list) else len(data.get('items', []))
            
            log_test_result(
                "Привязки операторов к складам", 
                True, 
                f"Найдено {bindings_count} привязок, время ответа: {response_time:.0f}ms, размер: {format_size(response_size)}"
            )
        else:
            log_test_result(
                "Привязки операторов к складам", 
                False, 
                f"HTTP {response.status_code}, время ответа: {response_time:.0f}ms"
            )
            
    except Exception as e:
        log_test_result("Привязки операторов к складам", False, f"Ошибка: {str(e)}")

def analyze_performance_bottlenecks():
    """Тест 9: Анализ узких мест производительности"""
    print("🔍 ТЕСТ 9: Анализ узких мест производительности")
    
    print("📈 АНАЛИЗ ПРОИЗВОДИТЕЛЬНОСТИ:")
    print("1. Основной endpoint /api/warehouses - базовая загрузка списка складов")
    print("2. Статистика складов - может загружаться для каждого склада отдельно")
    print("3. Структура складов - детальная информация о блоках/полках/ячейках")
    print("4. Ячейки складов - информация о занятости ячеек")
    print("5. Грузы на складах - список грузов для каждого склада")
    print("6. Привязки операторов - информация о том, кто работает на каком складе")
    print()
    
    print("🎯 ВОЗМОЖНЫЕ ПРИЧИНЫ МЕДЛЕННОЙ ЗАГРУЗКИ:")
    print("• N+1 проблема: для каждого склада делается отдельный запрос статистики/структуры")
    print("• Большой объем данных: много ячеек в структуре складов")
    print("• Медленные запросы к базе данных MongoDB")
    print("• Загрузка всех связанных данных сразу (грузы, операторы, статистика)")
    print("• Отсутствие кэширования данных")
    print()
    
    print("💡 РЕКОМЕНДАЦИИ ПО ОПТИМИЗАЦИИ:")
    print("• Использовать пагинацию для списка складов")
    print("• Загружать статистику/структуру только по требованию")
    print("• Добавить кэширование для статических данных")
    print("• Оптимизировать запросы к MongoDB (индексы)")
    print("• Использовать lazy loading для детальной информации")
    print()

def main():
    """Основная функция тестирования"""
    print("=" * 80)
    print("🎯 КРИТИЧЕСКАЯ ДИАГНОСТИКА: Проблема производительности категории 'Склады' в TAJLINE.TJ")
    print("=" * 80)
    print()
    
    # Тест 1: Авторизация администратора
    if not test_admin_authorization():
        print("❌ Не удалось авторизоваться. Прекращаем тестирование.")
        return
    
    # Тест 2: Основной endpoint складов
    warehouses = test_warehouses_main_endpoint()
    
    # Тест 3: Admin endpoint складов
    test_admin_warehouses_endpoint()
    
    if warehouses:
        # Тест 4: Статистика складов
        test_warehouse_statistics_endpoints(warehouses)
        
        # Тест 5: Структура складов
        test_warehouse_structure_endpoints(warehouses)
        
        # Тест 6: Ячейки складов
        test_warehouse_cells_endpoints(warehouses)
        
        # Тест 7: Грузы на складах
        test_warehouse_cargo_endpoints(warehouses)
    
    # Тест 8: Привязки операторов
    test_operator_warehouse_bindings()
    
    # Тест 9: Анализ производительности
    analyze_performance_bottlenecks()
    
    print("=" * 80)
    print("🏁 ДИАГНОСТИКА ПРОИЗВОДИТЕЛЬНОСТИ ЗАВЕРШЕНА")
    print("=" * 80)

if __name__ == "__main__":
    main()
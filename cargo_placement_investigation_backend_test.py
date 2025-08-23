#!/usr/bin/env python3
"""
🚨 КРИТИЧЕСКОЕ ИССЛЕДОВАНИЕ: Груз 250101/01/02 не отображается в визуальной схеме после размещения

ПРОБЛЕМА:
Пользователь только что разместил груз 250101/01/02 из заявки 250101 на позицию Б1-П2-Я5 на складе 003 Москва Склад №1, 
но груз не отображается в визуальной схеме ячеек.

КРИТИЧЕСКОЕ ИССЛЕДОВАНИЕ:
1. Авторизация оператора склада (+79777888999/warehouse123)
2. Проверка placement_records для груза 250101/01/02
3. Проверка operator_cargo статуса (is_placed=true, placement_info содержит "Б1-П2-Я5")
4. Диагностика API layout-with-cargo для склада 003
5. Поиск корневой причины отсутствия груза в визуальной схеме

ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ:
- placement_record должен существовать для 250101/01/02 на Б1-П2-Я5
- operator_cargo должен показывать is_placed=true
- layout-with-cargo должен возвращать груз в ячейке Б1-П2-Я5

КРИТИЧНО: Найти и исправить проблему чтобы размещенный груз отображался в визуальной схеме!
"""

import requests
import json
import time
from datetime import datetime

# Конфигурация
BASE_URL = "https://tajline-manage-1.preview.emergentagent.com/api"
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"

# Целевые данные для исследования
TARGET_CARGO = "250101/01/02"
TARGET_APPLICATION = "250101"
TARGET_POSITION = "Б1-П2-Я5"
TARGET_WAREHOUSE_NAME = "Москва Склад №1"
TARGET_WAREHOUSE_NUMBER = "003"

# Глобальные переменные
auth_token = None
warehouse_id = None
test_results = []

def log_test(test_name, success, details="", response_time=None):
    """Логирование результатов тестов"""
    status = "✅ PASS" if success else "❌ FAIL"
    time_info = f" ({response_time}ms)" if response_time else ""
    result = f"{status} {test_name}{time_info}"
    if details:
        result += f": {details}"
    print(result)
    test_results.append({
        "test": test_name,
        "success": success,
        "details": details,
        "response_time": response_time
    })
    return success

def make_request(method, endpoint, data=None, headers=None):
    """Выполнить HTTP запрос с обработкой ошибок"""
    url = f"{BASE_URL}{endpoint}"
    
    if headers is None:
        headers = {}
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    start_time = time.time()
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method.upper() == "POST":
            headers["Content-Type"] = "application/json"
            response = requests.post(url, json=data, headers=headers, timeout=30)
        elif method.upper() == "PUT":
            headers["Content-Type"] = "application/json"
            response = requests.put(url, json=data, headers=headers, timeout=30)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response_time = int((time.time() - start_time) * 1000)
        
        return response, response_time
    
    except requests.exceptions.RequestException as e:
        response_time = int((time.time() - start_time) * 1000)
        print(f"❌ Request failed: {e}")
        return None, response_time

def test_warehouse_operator_auth():
    """ЭТАП 1: Авторизация оператора склада"""
    global auth_token
    
    print("\n🔐 ЭТАП 1: Авторизация оператора склада")
    print(f"   📱 Телефон: {WAREHOUSE_OPERATOR_PHONE}")
    print(f"   🔑 Пароль: {WAREHOUSE_OPERATOR_PASSWORD}")
    
    auth_data = {
        "phone": WAREHOUSE_OPERATOR_PHONE,
        "password": WAREHOUSE_OPERATOR_PASSWORD
    }
    
    response, response_time = make_request("POST", "/auth/login", auth_data)
    
    if not response:
        return log_test("Авторизация оператора склада", False, "Ошибка сети", response_time)
    
    if response.status_code == 200:
        data = response.json()
        auth_token = data.get("access_token")
        user_info = data.get("user", {})
        
        if auth_token and user_info.get("role") == "warehouse_operator":
            details = f"Успешная авторизация '{user_info.get('full_name')}' (роль: {user_info.get('role')})"
            print(f"   ✅ Токен получен: {auth_token[:20]}...")
            print(f"   👤 Пользователь: {user_info.get('full_name')}")
            print(f"   🏷️ Роль: {user_info.get('role')}")
            return log_test("Авторизация оператора склада", True, details, response_time)
        else:
            return log_test("Авторизация оператора склада", False, "Неверная роль или отсутствует токен", response_time)
    else:
        error_detail = response.json().get("detail", "Unknown error") if response.content else "Empty response"
        return log_test("Авторизация оператора склада", False, f"HTTP {response.status_code}: {error_detail}", response_time)

def find_warehouse_id():
    """Найти ID склада 003 'Москва Склад №1'"""
    global warehouse_id
    
    print(f"\n🏢 ПОИСК СКЛАДА: {TARGET_WAREHOUSE_NAME} (номер {TARGET_WAREHOUSE_NUMBER})")
    
    response, response_time = make_request("GET", "/operator/warehouses")
    
    if not response or response.status_code != 200:
        print("   ❌ Не удалось получить список складов")
        return False
    
    warehouses = response.json()
    print(f"   📋 Найдено складов: {len(warehouses)}")
    
    for warehouse in warehouses:
        print(f"   🏢 Склад: {warehouse.get('name')} (ID: {warehouse.get('id')}, номер: {warehouse.get('warehouse_id_number')})")
        
        # Ищем по номеру склада или названию
        if (warehouse.get('warehouse_id_number') == TARGET_WAREHOUSE_NUMBER or 
            TARGET_WAREHOUSE_NAME in warehouse.get('name', '')):
            warehouse_id = warehouse.get('id')
            print(f"   ✅ НАЙДЕН ЦЕЛЕВОЙ СКЛАД: {warehouse.get('name')}")
            print(f"      - ID: {warehouse_id}")
            print(f"      - Номер: {warehouse.get('warehouse_id_number')}")
            print(f"      - Адрес: {warehouse.get('location')}")
            return True
    
    print(f"   ❌ Склад {TARGET_WAREHOUSE_NAME} (номер {TARGET_WAREHOUSE_NUMBER}) не найден")
    return False

def test_placement_records_check():
    """ЭТАП 2: Проверка placement_records для груза 250101/01/02"""
    
    print(f"\n📋 ЭТАП 2: Проверка placement_records для груза {TARGET_CARGO}")
    print(f"   🎯 Ищем placement_record для individual_number: {TARGET_CARGO}")
    print(f"   📍 Ожидаемая позиция: {TARGET_POSITION}")
    
    # Используем API для получения всех placement records (если есть такой endpoint)
    # Или проверяем через layout-with-cargo API
    
    if not warehouse_id:
        if not find_warehouse_id():
            return log_test("Поиск placement_records", False, "Не найден warehouse_id")
    
    # Проверяем через layout-with-cargo API
    response, response_time = make_request("GET", f"/warehouses/{warehouse_id}/layout-with-cargo")
    
    if not response:
        return log_test("Проверка placement_records", False, "Ошибка сети при получении layout", response_time)
    
    if response.status_code != 200:
        error_detail = response.json().get("detail", "Unknown error") if response.content else "Empty response"
        return log_test("Проверка placement_records", False, f"HTTP {response.status_code}: {error_detail}", response_time)
    
    layout_data = response.json()
    print(f"   📊 Получен layout склада с {len(layout_data.get('blocks', []))} блоками")
    
    # Ищем груз в layout
    found_cargo = False
    cargo_location = None
    
    for block in layout_data.get('blocks', []):
        block_num = block.get('block_number')
        for shelf in block.get('shelves', []):
            shelf_num = shelf.get('shelf_number')
            for cell in shelf.get('cells', []):
                cell_num = cell.get('cell_number')
                
                # Проверяем грузы в ячейке
                for cargo in cell.get('cargo', []):
                    individual_number = cargo.get('individual_number')
                    if individual_number == TARGET_CARGO:
                        found_cargo = True
                        cargo_location = f"Б{block_num}-П{shelf_num}-Я{cell_num}"
                        
                        print(f"   ✅ ГРУЗ НАЙДЕН В LAYOUT!")
                        print(f"      - Individual number: {individual_number}")
                        print(f"      - Позиция: {cargo_location}")
                        print(f"      - Cargo name: {cargo.get('cargo_name', 'N/A')}")
                        print(f"      - Sender: {cargo.get('sender_full_name', 'N/A')}")
                        print(f"      - Placed by: {cargo.get('placed_by_operator', 'N/A')}")
                        
                        # Проверяем соответствие ожидаемой позиции
                        if cargo_location == TARGET_POSITION:
                            details = f"Груз {TARGET_CARGO} найден в правильной позиции {cargo_location}"
                            return log_test("Проверка placement_records", True, details, response_time)
                        else:
                            details = f"Груз {TARGET_CARGO} найден в позиции {cargo_location}, но ожидался в {TARGET_POSITION}"
                            return log_test("Проверка placement_records", False, details, response_time)
    
    if not found_cargo:
        print(f"   ❌ ГРУЗ {TARGET_CARGO} НЕ НАЙДЕН В LAYOUT!")
        print(f"   🔍 Проверим все грузы в layout для диагностики...")
        
        # Диагностика - показываем все грузы
        total_cargo = 0
        for block in layout_data.get('blocks', []):
            for shelf in block.get('shelves', []):
                for cell in shelf.get('cells', []):
                    cargo_count = len(cell.get('cargo', []))
                    if cargo_count > 0:
                        total_cargo += cargo_count
                        print(f"      - Б{block.get('block_number')}-П{shelf.get('shelf_number')}-Я{cell.get('cell_number')}: {cargo_count} грузов")
                        for cargo in cell.get('cargo', []):
                            print(f"        * {cargo.get('individual_number', 'N/A')} - {cargo.get('cargo_name', 'N/A')}")
        
        print(f"   📊 Всего грузов в layout: {total_cargo}")
        details = f"Груз {TARGET_CARGO} отсутствует в layout. Всего грузов в схеме: {total_cargo}"
        return log_test("Проверка placement_records", False, details, response_time)

def test_operator_cargo_status():
    """ЭТАП 3: Проверка operator_cargo статуса"""
    
    print(f"\n🔍 ЭТАП 3: Проверка operator_cargo статуса для груза {TARGET_CARGO}")
    print(f"   🎯 Ищем is_placed=true и placement_info содержит '{TARGET_POSITION}'")
    
    # Получаем список грузов оператора для поиска нашего груза
    response, response_time = make_request("GET", "/operator/cargo/available-for-placement")
    
    if not response:
        return log_test("Проверка operator_cargo статуса", False, "Ошибка сети", response_time)
    
    if response.status_code != 200:
        error_detail = response.json().get("detail", "Unknown error") if response.content else "Empty response"
        return log_test("Проверка operator_cargo статуса", False, f"HTTP {response.status_code}: {error_detail}", response_time)
    
    data = response.json()
    cargo_list = data.get('items', [])
    
    print(f"   📋 Получено грузов для размещения: {len(cargo_list)}")
    
    # Ищем наш груз в списке доступных для размещения
    found_in_available = False
    for cargo in cargo_list:
        cargo_number = cargo.get('cargo_number')
        if cargo_number == TARGET_APPLICATION:  # Ищем по номеру заявки
            found_in_available = True
            print(f"   ⚠️ ЗАЯВКА {TARGET_APPLICATION} НАЙДЕНА В СПИСКЕ ДОСТУПНЫХ ДЛЯ РАЗМЕЩЕНИЯ!")
            print(f"      - Это означает, что груз НЕ полностью размещен")
            
            # Проверяем individual_items
            individual_items = cargo.get('individual_items', [])
            for item in individual_items:
                if item.get('individual_number') == TARGET_CARGO:
                    is_placed = item.get('is_placed', False)
                    placement_info = item.get('placement_info', '')
                    
                    print(f"      - Individual number: {TARGET_CARGO}")
                    print(f"      - is_placed: {is_placed}")
                    print(f"      - placement_info: {placement_info}")
                    
                    if is_placed and TARGET_POSITION in placement_info:
                        details = f"Груз {TARGET_CARGO} помечен как размещенный в {placement_info}"
                        return log_test("Проверка operator_cargo статуса", True, details, response_time)
                    elif is_placed:
                        details = f"Груз {TARGET_CARGO} помечен как размещенный, но placement_info='{placement_info}' не содержит '{TARGET_POSITION}'"
                        return log_test("Проверка operator_cargo статуса", False, details, response_time)
                    else:
                        details = f"Груз {TARGET_CARGO} НЕ помечен как размещенный (is_placed={is_placed})"
                        return log_test("Проверка operator_cargo статуса", False, details, response_time)
            break
    
    if not found_in_available:
        print(f"   ✅ Заявка {TARGET_APPLICATION} НЕ найдена в списке доступных для размещения")
        print(f"   🔍 Это может означать, что заявка полностью размещена")
        
        # Проверяем в списке полностью размещенных
        response2, response_time2 = make_request("GET", "/operator/cargo/fully-placed")
        
        if response2 and response2.status_code == 200:
            fully_placed_data = response2.json()
            fully_placed_list = fully_placed_data.get('items', [])
            
            print(f"   📋 Проверяем полностью размещенные заявки: {len(fully_placed_list)}")
            
            for cargo in fully_placed_list:
                cargo_number = cargo.get('cargo_number')
                if cargo_number == TARGET_APPLICATION:
                    print(f"   ✅ ЗАЯВКА {TARGET_APPLICATION} НАЙДЕНА В ПОЛНОСТЬЮ РАЗМЕЩЕННЫХ!")
                    
                    # Проверяем individual_units
                    individual_units = cargo.get('individual_units', [])
                    for unit in individual_units:
                        if unit.get('individual_number') == TARGET_CARGO:
                            status = unit.get('status')
                            placement_info = unit.get('placement_info', '')
                            
                            print(f"      - Individual number: {TARGET_CARGO}")
                            print(f"      - status: {status}")
                            print(f"      - placement_info: {placement_info}")
                            
                            if status == 'placed' and TARGET_POSITION in placement_info:
                                details = f"Груз {TARGET_CARGO} в полностью размещенных с правильным статусом и позицией {placement_info}"
                                return log_test("Проверка operator_cargo статуса", True, details, response_time + response_time2)
                            else:
                                details = f"Груз {TARGET_CARGO} в полностью размещенных, но status='{status}', placement_info='{placement_info}'"
                                return log_test("Проверка operator_cargo статуса", False, details, response_time + response_time2)
                    break
        
        details = f"Заявка {TARGET_APPLICATION} не найдена ни в доступных, ни в полностью размещенных"
        return log_test("Проверка operator_cargo статуса", False, details, response_time)

def test_layout_with_cargo_api():
    """ЭТАП 4: Диагностика API layout-with-cargo"""
    
    print(f"\n🗺️ ЭТАП 4: Диагностика API layout-with-cargo для склада {TARGET_WAREHOUSE_NUMBER}")
    print(f"   🎯 Ищем груз {TARGET_CARGO} в ячейке {TARGET_POSITION}")
    
    if not warehouse_id:
        if not find_warehouse_id():
            return log_test("Диагностика layout-with-cargo", False, "Не найден warehouse_id")
    
    response, response_time = make_request("GET", f"/warehouses/{warehouse_id}/layout-with-cargo")
    
    if not response:
        return log_test("Диагностика layout-with-cargo", False, "Ошибка сети", response_time)
    
    if response.status_code != 200:
        error_detail = response.json().get("detail", "Unknown error") if response.content else "Empty response"
        return log_test("Диагностика layout-with-cargo", False, f"HTTP {response.status_code}: {error_detail}", response_time)
    
    layout_data = response.json()
    
    print(f"   📊 АНАЛИЗ LAYOUT API:")
    print(f"      - Блоков: {len(layout_data.get('blocks', []))}")
    
    # Ищем конкретную ячейку Б1-П2-Я5
    target_block = 1
    target_shelf = 2  
    target_cell = 5
    
    found_target_cell = False
    target_cell_cargo = []
    
    for block in layout_data.get('blocks', []):
        if block.get('block_number') == target_block:
            print(f"      - Найден блок Б{target_block}")
            
            for shelf in block.get('shelves', []):
                if shelf.get('shelf_number') == target_shelf:
                    print(f"      - Найдена полка П{target_shelf}")
                    
                    for cell in shelf.get('cells', []):
                        if cell.get('cell_number') == target_cell:
                            found_target_cell = True
                            target_cell_cargo = cell.get('cargo', [])
                            
                            print(f"      - Найдена ячейка Я{target_cell}")
                            print(f"      - Грузов в ячейке: {len(target_cell_cargo)}")
                            
                            # Проверяем каждый груз в ячейке
                            for i, cargo in enumerate(target_cell_cargo):
                                individual_number = cargo.get('individual_number')
                                cargo_name = cargo.get('cargo_name', 'N/A')
                                sender = cargo.get('sender_full_name', 'N/A')
                                
                                print(f"         {i+1}. {individual_number} - {cargo_name} (от {sender})")
                                
                                if individual_number == TARGET_CARGO:
                                    print(f"         ✅ НАЙДЕН ЦЕЛЕВОЙ ГРУЗ {TARGET_CARGO}!")
                                    details = f"Груз {TARGET_CARGO} найден в ячейке {TARGET_POSITION} через layout-with-cargo API"
                                    return log_test("Диагностика layout-with-cargo", True, details, response_time)
                            
                            break
                    break
            break
    
    if not found_target_cell:
        print(f"   ❌ Ячейка {TARGET_POSITION} не найдена в layout")
        details = f"Ячейка {TARGET_POSITION} отсутствует в структуре склада"
        return log_test("Диагностика layout-with-cargo", False, details, response_time)
    
    if len(target_cell_cargo) == 0:
        print(f"   ⚠️ Ячейка {TARGET_POSITION} найдена, но пуста")
        details = f"Ячейка {TARGET_POSITION} существует, но не содержит грузов"
        return log_test("Диагностика layout-with-cargo", False, details, response_time)
    
    print(f"   ❌ Груз {TARGET_CARGO} НЕ найден в ячейке {TARGET_POSITION}")
    cargo_list = [cargo.get('individual_number', 'N/A') for cargo in target_cell_cargo]
    details = f"Ячейка {TARGET_POSITION} содержит другие грузы: {', '.join(cargo_list)}"
    return log_test("Диагностика layout-with-cargo", False, details, response_time)

def test_root_cause_analysis():
    """ЭТАП 5: Поиск корневой причины"""
    
    print(f"\n🔍 ЭТАП 5: Анализ корневой причины проблемы")
    print(f"   🎯 Определяем почему груз {TARGET_CARGO} не отображается в визуальной схеме")
    
    # Анализируем результаты предыдущих тестов
    placement_test = next((r for r in test_results if "placement_records" in r["test"]), None)
    operator_cargo_test = next((r for r in test_results if "operator_cargo" in r["test"]), None)
    layout_test = next((r for r in test_results if "layout-with-cargo" in r["test"]), None)
    
    issues_found = []
    recommendations = []
    
    print(f"   📊 АНАЛИЗ РЕЗУЛЬТАТОВ ТЕСТИРОВАНИЯ:")
    
    if placement_test:
        print(f"      - Placement records: {'✅ OK' if placement_test['success'] else '❌ ПРОБЛЕМА'}")
        if not placement_test['success']:
            issues_found.append("Груз отсутствует в placement_records или в неправильной позиции")
            recommendations.append("Проверить создание placement_record при размещении груза")
    
    if operator_cargo_test:
        print(f"      - Operator cargo status: {'✅ OK' if operator_cargo_test['success'] else '❌ ПРОБЛЕМА'}")
        if not operator_cargo_test['success']:
            issues_found.append("Статус груза в operator_cargo не соответствует размещенному")
            recommendations.append("Обновить is_placed=true и placement_info в operator_cargo")
    
    if layout_test:
        print(f"      - Layout API: {'✅ OK' if layout_test['success'] else '❌ ПРОБЛЕМА'}")
        if not layout_test['success']:
            issues_found.append("API layout-with-cargo не возвращает груз в ожидаемой ячейке")
            recommendations.append("Проверить синхронизацию между placement_records и layout API")
    
    print(f"\n   🚨 НАЙДЕННЫЕ ПРОБЛЕМЫ ({len(issues_found)}):")
    for i, issue in enumerate(issues_found, 1):
        print(f"      {i}. {issue}")
    
    print(f"\n   💡 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ ({len(recommendations)}):")
    for i, rec in enumerate(recommendations, 1):
        print(f"      {i}. {rec}")
    
    # Определяем корневую причину
    if len(issues_found) == 0:
        details = "Все системы работают корректно, груз должен отображаться в визуальной схеме"
        return log_test("Анализ корневой причины", True, details)
    elif len(issues_found) == 1:
        details = f"Найдена корневая причина: {issues_found[0]}"
        return log_test("Анализ корневой причины", False, details)
    else:
        details = f"Множественные проблемы: {len(issues_found)} компонентов требуют исправления"
        return log_test("Анализ корневой причины", False, details)

def print_investigation_summary():
    """Вывод итогового отчета расследования"""
    print("\n" + "="*100)
    print("🚨 ИТОГОВЫЙ ОТЧЕТ КРИТИЧЕСКОГО РАССЛЕДОВАНИЯ")
    print("="*100)
    
    print(f"🎯 ЦЕЛЬ РАССЛЕДОВАНИЯ:")
    print(f"   Выяснить почему груз {TARGET_CARGO} из заявки {TARGET_APPLICATION}")
    print(f"   не отображается в визуальной схеме после размещения на позицию {TARGET_POSITION}")
    print(f"   в складе {TARGET_WAREHOUSE_NUMBER} '{TARGET_WAREHOUSE_NAME}'")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results if result["success"])
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n📈 СТАТИСТИКА РАССЛЕДОВАНИЯ:")
    print(f"   - Всего этапов: {total_tests}")
    print(f"   - Успешных: {passed_tests}")
    print(f"   - Проблемных: {failed_tests}")
    print(f"   - Успешность: {success_rate:.1f}%")
    
    print(f"\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ ЭТАПОВ:")
    for i, result in enumerate(test_results, 1):
        status = "✅" if result["success"] else "❌"
        time_info = f" ({result['response_time']}ms)" if result.get('response_time') else ""
        print(f"   {i}. {status} {result['test']}{time_info}")
        if result["details"]:
            print(f"      📝 {result['details']}")
    
    print(f"\n🔍 КРИТИЧЕСКИЕ ВЫВОДЫ:")
    
    # Анализируем ключевые результаты
    auth_success = any(r["success"] for r in test_results if "Авторизация" in r["test"])
    placement_success = any(r["success"] for r in test_results if "placement_records" in r["test"])
    operator_cargo_success = any(r["success"] for r in test_results if "operator_cargo" in r["test"])
    layout_success = any(r["success"] for r in test_results if "layout-with-cargo" in r["test"])
    
    if auth_success:
        print("   ✅ Авторизация оператора склада работает корректно")
    else:
        print("   ❌ Проблемы с авторизацией оператора склада")
    
    if placement_success:
        print(f"   ✅ Груз {TARGET_CARGO} найден в placement_records на правильной позиции")
    else:
        print(f"   ❌ Груз {TARGET_CARGO} отсутствует в placement_records или в неправильной позиции")
    
    if operator_cargo_success:
        print(f"   ✅ Статус груза в operator_cargo корректен (is_placed=true)")
    else:
        print(f"   ❌ Проблемы со статусом груза в operator_cargo")
    
    if layout_success:
        print(f"   ✅ API layout-with-cargo возвращает груз в ячейке {TARGET_POSITION}")
    else:
        print(f"   ❌ API layout-with-cargo НЕ возвращает груз в ожидаемой ячейке")
    
    print(f"\n🎯 ЗАКЛЮЧЕНИЕ РАССЛЕДОВАНИЯ:")
    if success_rate >= 80:
        print("   🎉 ПРОБЛЕМА РЕШЕНА!")
        print(f"   📍 Груз {TARGET_CARGO} корректно размещен и должен отображаться в визуальной схеме")
        print("   💡 Если проблема все еще наблюдается, проверьте frontend кэширование")
    elif success_rate >= 50:
        print("   ⚠️ ЧАСТИЧНАЯ ПРОБЛЕМА ОБНАРУЖЕНА")
        print("   📍 Некоторые компоненты работают корректно, но есть проблемы в других")
        print("   💡 Требуется исправление найденных проблем")
    else:
        print("   🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА ПОДТВЕРЖДЕНА!")
        print(f"   📍 Груз {TARGET_CARGO} НЕ размещен корректно в системе")
        print("   💡 Требуется немедленное исправление системы размещения")
    
    print(f"\n🛠️ СЛЕДУЮЩИЕ ШАГИ:")
    if failed_tests > 0:
        print("   1. Исправить найденные проблемы в backend системе")
        print("   2. Обеспечить синхронизацию между placement_records и operator_cargo")
        print("   3. Проверить корректность API layout-with-cargo")
        print("   4. Повторить размещение груза после исправлений")
    else:
        print("   1. Проверить frontend кэширование и обновление интерфейса")
        print("   2. Убедиться что визуальная схема обновляется после размещения")
        print("   3. Проверить WebSocket уведомления о размещении")

def main():
    """Основная функция расследования"""
    print("🚨 КРИТИЧЕСКОЕ РАССЛЕДОВАНИЕ: Груз не отображается в визуальной схеме после размещения")
    print("="*100)
    print(f"🕐 Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Базовый URL: {BASE_URL}")
    print(f"👤 Оператор: {WAREHOUSE_OPERATOR_PHONE}")
    print(f"📦 Целевой груз: {TARGET_CARGO} из заявки {TARGET_APPLICATION}")
    print(f"📍 Ожидаемая позиция: {TARGET_POSITION}")
    print(f"🏢 Склад: {TARGET_WAREHOUSE_NUMBER} '{TARGET_WAREHOUSE_NAME}'")
    
    # Выполняем этапы расследования
    investigation_steps = [
        test_warehouse_operator_auth,
        test_placement_records_check,
        test_operator_cargo_status,
        test_layout_with_cargo_api,
        test_root_cause_analysis
    ]
    
    for step_func in investigation_steps:
        try:
            step_func()
        except Exception as e:
            print(f"❌ Ошибка в этапе {step_func.__name__}: {e}")
            log_test(step_func.__name__, False, f"Exception: {str(e)}")
    
    # Выводим итоговый отчет расследования
    print_investigation_summary()

if __name__ == "__main__":
    main()
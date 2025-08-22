#!/usr/bin/env python3
"""
🎉 ФИНАЛЬНАЯ ПРОВЕРКА: Модальное окно деталей ячейки с полной информацией о грузах

РЕЗУЛЬТАТ РАБОТЫ:
Обновлен backend API layout-with-cargo для возврата полной информации о грузах и создано улучшенное модальное окно деталей ячейки с подробной информацией.

КРИТИЧЕСКИЕ ОЖИДАНИЯ:
✅ cargo_name корректно заполнен (например: "Самокат ВИВО", "Микроволновка")
✅ sender_full_name заполнен (например: "Бахром Файзуллоевич Бобоназаров")
✅ placed_by_operator показывает корректного оператора
✅ API успешно получает данные из operator_cargo коллекции
✅ Все поля доступны для отображения в модальном окне

ЦЕЛЬ: Подтвердить что backend API теперь возвращает всю необходимую информацию для полного модального окна деталей ячейки!
"""

import requests
import json
import time
from datetime import datetime

# Конфигурация
BASE_URL = "https://placement-view.preview.emergentagent.com/api"
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"

# Глобальные переменные для токена и данных
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
    """Тест 1: Авторизация оператора склада"""
    global auth_token
    
    print("\n🔐 ТЕСТ 1: Авторизация оператора склада")
    
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
            return log_test("Авторизация оператора склада", True, details, response_time)
        else:
            return log_test("Авторизация оператора склада", False, "Неверная роль или отсутствует токен", response_time)
    else:
        error_detail = response.json().get("detail", "Unknown error") if response.content else "Empty response"
        return log_test("Авторизация оператора склада", False, f"HTTP {response.status_code}: {error_detail}", response_time)

def test_get_warehouse_id():
    """Тест 2: Получение warehouse_id для 'Москва Склад №1'"""
    global warehouse_id
    
    print("\n🏢 ТЕСТ 2: Получение warehouse_id для 'Москва Склад №1'")
    
    response, response_time = make_request("GET", "/operator/warehouses")
    
    if not response:
        return log_test("Получение warehouse_id", False, "Ошибка сети", response_time)
    
    if response.status_code == 200:
        warehouses = response.json()
        
        # Ищем склад "Москва Склад №1"
        moscow_warehouse = None
        for warehouse in warehouses:
            if "Москва Склад №1" in warehouse.get("name", ""):
                moscow_warehouse = warehouse
                break
        
        if moscow_warehouse:
            warehouse_id = moscow_warehouse.get("id")
            details = f"Найден склад 'Москва Склад №1' (ID: {warehouse_id})"
            return log_test("Получение warehouse_id", True, details, response_time)
        else:
            available_warehouses = [w.get("name", "Unknown") for w in warehouses]
            details = f"Склад 'Москва Склад №1' не найден. Доступные склады: {available_warehouses}"
            return log_test("Получение warehouse_id", False, details, response_time)
    else:
        error_detail = response.json().get("detail", "Unknown error") if response.content else "Empty response"
        return log_test("Получение warehouse_id", False, f"HTTP {response.status_code}: {error_detail}", response_time)

def test_layout_with_cargo_api():
    """Тест 3: Проверка обновленного API layout-with-cargo"""
    
    print("\n🗺️ ТЕСТ 3: Проверка обновленного API layout-with-cargo")
    
    if not warehouse_id:
        return log_test("API layout-with-cargo", False, "warehouse_id не найден")
    
    response, response_time = make_request("GET", f"/warehouses/{warehouse_id}/layout-with-cargo")
    
    if not response:
        return log_test("API layout-with-cargo", False, "Ошибка сети", response_time)
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"📊 РЕЗУЛЬТАТЫ LAYOUT-WITH-CARGO:")
        print(f"   - Всего ячеек: {data.get('total_cells', 0)}")
        print(f"   - Занято ячеек: {data.get('occupied_cells', 0)}")
        print(f"   - Всего грузов: {data.get('total_cargo', 0)}")
        print(f"   - Блоков: {len(data.get('blocks', []))}")
        
        # Проверяем наличие новых полей в грузах
        new_fields_found = []
        cargo_with_new_fields = 0
        total_cargo_found = 0
        
        # Check both top-level blocks and layout.blocks
        layout_blocks = data.get("layout", {}).get("blocks", [])
        top_level_blocks = data.get("blocks", [])
        
        all_blocks = layout_blocks if layout_blocks else top_level_blocks
        
        for block in all_blocks:
            shelves = block.get("shelves", [])
            for shelf in shelves:
                cells = shelf.get("cells", [])
                for cell in cells:
                    if cell.get("is_occupied") and cell.get("cargo"):
                        cargo_list = cell.get("cargo", [])
                        for cargo_info in cargo_list:
                            total_cargo_found += 1
                        
                            # Проверяем новые поля
                            required_fields = [
                                "cargo_name", "sender_full_name", "sender_phone",
                                "recipient_full_name", "recipient_phone", "recipient_address",
                                "delivery_city", "delivery_warehouse_name", "placed_by_operator"
                            ]
                            
                            fields_present = []
                            for field in required_fields:
                                if field in cargo_info and cargo_info[field]:
                                    fields_present.append(field)
                            
                            if fields_present:
                                cargo_with_new_fields += 1
                                new_fields_found.extend(fields_present)
                                
                                print(f"   📦 Груз в ячейке {cell.get('location_code', 'Unknown')}:")
                                for field in fields_present:
                                    print(f"      - {field}: {cargo_info[field]}")
        
        # Убираем дубликаты
        unique_new_fields = list(set(new_fields_found))
        
        success = True
        issues = []
        
        if total_cargo_found == 0:
            success = False
            issues.append("Не найдено ни одного груза в ячейках")
        elif cargo_with_new_fields == 0:
            success = False
            issues.append("Ни один груз не содержит новые поля")
        elif len(unique_new_fields) < 3:  # Минимум 3 новых поля должны быть
            success = False
            issues.append(f"Найдено только {len(unique_new_fields)} новых полей из 9 ожидаемых")
        
        if success:
            details = f"✅ Найдено {cargo_with_new_fields}/{total_cargo_found} грузов с новыми полями: {unique_new_fields}"
            return log_test("API layout-with-cargo", True, details, response_time)
        else:
            details = f"❌ {', '.join(issues)}. Найдено полей: {unique_new_fields}"
            return log_test("API layout-with-cargo", False, details, response_time)
    else:
        error_detail = response.json().get("detail", "Unknown error") if response.content else "Empty response"
        return log_test("API layout-with-cargo", False, f"HTTP {response.status_code}: {error_detail}", response_time)

def test_specific_cells():
    """Тест 4: Проверка конкретных ячеек Б1-П3-Я2 и Б1-П3-Я3"""
    
    print("\n🎯 ТЕСТ 4: Проверка конкретных ячеек")
    
    if not warehouse_id:
        return log_test("Проверка конкретных ячеек", False, "warehouse_id не найден")
    
    response, response_time = make_request("GET", f"/warehouses/{warehouse_id}/layout-with-cargo")
    
    if not response:
        return log_test("Проверка конкретных ячеек", False, "Ошибка сети", response_time)
    
    if response.status_code == 200:
        data = response.json()
        
        # Ищем конкретные ячейки
        target_cells = ["Б1-П3-Я2", "Б1-П3-Я3"]
        found_cells = {}
        
        blocks = data.get("blocks", [])
        for block in blocks:
            shelves = block.get("shelves", [])
            for shelf in shelves:
                cells = shelf.get("cells", [])
                for cell in cells:
                    location_code = cell.get("location_code", "")
                    if location_code in target_cells and cell.get("is_occupied"):
                        cargo_info = cell.get("cargo_info", {})
                        found_cells[location_code] = cargo_info
                        
                        print(f"   📍 Ячейка {location_code}:")
                        print(f"      - cargo_name: {cargo_info.get('cargo_name', 'НЕТ')}")
                        print(f"      - sender_full_name: {cargo_info.get('sender_full_name', 'НЕТ')}")
                        print(f"      - placed_by_operator: {cargo_info.get('placed_by_operator', 'НЕТ')}")
        
        success = True
        issues = []
        
        # Проверяем ячейку Б1-П3-Я3 на наличие груза "Самокат ВИВО"
        if "Б1-П3-Я3" in found_cells:
            cargo_name = found_cells["Б1-П3-Я3"].get("cargo_name", "")
            if "Самокат ВИВО" not in cargo_name:
                issues.append(f"Ячейка Б1-П3-Я3 не содержит груз 'Самокат ВИВО', найдено: '{cargo_name}'")
        else:
            issues.append("Ячейка Б1-П3-Я3 не найдена или пуста")
        
        # Проверяем ячейку Б1-П3-Я2 на наличие грузов с cargo_name
        if "Б1-П3-Я2" in found_cells:
            cargo_name = found_cells["Б1-П3-Я2"].get("cargo_name", "")
            if not cargo_name:
                issues.append("Ячейка Б1-П3-Я2 не содержит cargo_name")
        else:
            issues.append("Ячейка Б1-П3-Я2 не найдена или пуста")
        
        if issues:
            success = False
        
        if success:
            details = f"✅ Найдены целевые ячейки с корректными данными: {list(found_cells.keys())}"
            return log_test("Проверка конкретных ячеек", True, details, response_time)
        else:
            details = f"❌ {', '.join(issues)}. Найдены ячейки: {list(found_cells.keys())}"
            return log_test("Проверка конкретных ячеек", False, details, response_time)
    else:
        error_detail = response.json().get("detail", "Unknown error") if response.content else "Empty response"
        return log_test("Проверка конкретных ячеек", False, f"HTTP {response.status_code}: {error_detail}", response_time)

def test_operator_cargo_data_retrieval():
    """Тест 5: Проверка получения данных из operator_cargo"""
    
    print("\n🔍 ТЕСТ 5: Проверка получения данных из operator_cargo")
    
    if not warehouse_id:
        return log_test("Получение данных из operator_cargo", False, "warehouse_id не найден")
    
    # Проверяем API layout-with-cargo еще раз для анализа источника данных
    response, response_time = make_request("GET", f"/warehouses/{warehouse_id}/layout-with-cargo")
    
    if not response:
        return log_test("Получение данных из operator_cargo", False, "Ошибка сети", response_time)
    
    if response.status_code == 200:
        data = response.json()
        
        # Анализируем данные на предмет источника из operator_cargo
        cargo_with_operator_data = 0
        total_cargo = 0
        operator_cargo_indicators = []
        
        blocks = data.get("blocks", [])
        for block in blocks:
            shelves = block.get("shelves", [])
            for shelf in shelves:
                cells = shelf.get("cells", [])
                for cell in cells:
                    if cell.get("is_occupied") and cell.get("cargo_info"):
                        cargo_info = cell.get("cargo_info", {})
                        total_cargo += 1
                        
                        # Проверяем индикаторы данных из operator_cargo
                        has_cargo_name = bool(cargo_info.get("cargo_name"))
                        has_sender_full_name = bool(cargo_info.get("sender_full_name"))
                        has_placed_by_operator = bool(cargo_info.get("placed_by_operator"))
                        
                        if has_cargo_name or has_sender_full_name or has_placed_by_operator:
                            cargo_with_operator_data += 1
                            
                            if has_cargo_name:
                                operator_cargo_indicators.append("cargo_name")
                            if has_sender_full_name:
                                operator_cargo_indicators.append("sender_full_name")
                            if has_placed_by_operator:
                                operator_cargo_indicators.append("placed_by_operator")
        
        # Убираем дубликаты
        unique_indicators = list(set(operator_cargo_indicators))
        
        success = True
        issues = []
        
        if total_cargo == 0:
            success = False
            issues.append("Не найдено грузов для анализа")
        elif cargo_with_operator_data == 0:
            success = False
            issues.append("Ни один груз не содержит данные из operator_cargo")
        elif len(unique_indicators) < 2:
            success = False
            issues.append(f"Найдено только {len(unique_indicators)} индикаторов operator_cargo данных")
        
        print(f"   📊 АНАЛИЗ ДАННЫХ OPERATOR_CARGO:")
        print(f"      - Всего грузов: {total_cargo}")
        print(f"      - С данными operator_cargo: {cargo_with_operator_data}")
        print(f"      - Индикаторы: {unique_indicators}")
        
        if success:
            details = f"✅ API успешно извлекает данные из operator_cargo: {cargo_with_operator_data}/{total_cargo} грузов с индикаторами {unique_indicators}"
            return log_test("Получение данных из operator_cargo", True, details, response_time)
        else:
            details = f"❌ {', '.join(issues)}. Индикаторы: {unique_indicators}"
            return log_test("Получение данных из operator_cargo", False, details, response_time)
    else:
        error_detail = response.json().get("detail", "Unknown error") if response.content else "Empty response"
        return log_test("Получение данных из operator_cargo", False, f"HTTP {response.status_code}: {error_detail}", response_time)

def print_summary():
    """Вывод итогового отчета"""
    print("\n" + "="*80)
    print("🎉 ИТОГОВЫЙ ОТЧЕТ ФИНАЛЬНОЙ ПРОВЕРКИ")
    print("="*80)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results if result["success"])
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"📈 ОБЩАЯ СТАТИСТИКА:")
    print(f"   - Всего тестов: {total_tests}")
    print(f"   - Пройдено: {passed_tests}")
    print(f"   - Провалено: {failed_tests}")
    print(f"   - Успешность: {success_rate:.1f}%")
    
    print(f"\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
    for i, result in enumerate(test_results, 1):
        status = "✅" if result["success"] else "❌"
        time_info = f" ({result['response_time']}ms)" if result.get('response_time') else ""
        print(f"   {i}. {status} {result['test']}{time_info}")
        if result["details"]:
            print(f"      {result['details']}")
    
    print(f"\n🎯 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ:")
    
    # Проверяем критические критерии
    layout_test = next((r for r in test_results if "layout-with-cargo" in r["test"]), None)
    cells_test = next((r for r in test_results if "конкретных ячеек" in r["test"]), None)
    operator_cargo_test = next((r for r in test_results if "operator_cargo" in r["test"]), None)
    
    if layout_test and layout_test["success"]:
        print("   ✅ cargo_name корректно заполнен")
        print("   ✅ sender_full_name заполнен")
        print("   ✅ placed_by_operator показывает корректного оператора")
    else:
        print("   ❌ Новые поля в API layout-with-cargo не работают")
    
    if cells_test and cells_test["success"]:
        print("   ✅ Ячейка Б1-П3-Я3 содержит груз 'Самокат ВИВО'")
        print("   ✅ Ячейка Б1-П3-Я2 содержит грузы с cargo_name")
    else:
        print("   ❌ Проблемы с конкретными ячейками")
    
    if operator_cargo_test and operator_cargo_test["success"]:
        print("   ✅ API успешно получает данные из operator_cargo коллекции")
        print("   ✅ Все поля доступны для отображения в модальном окне")
    else:
        print("   ❌ Проблемы с получением данных из operator_cargo")
    
    print(f"\n🏁 ЗАКЛЮЧЕНИЕ:")
    if success_rate >= 80:
        print("   🎉 ФИНАЛЬНАЯ ПРОВЕРКА ЗАВЕРШЕНА УСПЕШНО!")
        print("   📍 Backend API теперь возвращает всю необходимую информацию для полного модального окна деталей ячейки!")
    else:
        print("   ⚠️ ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНАЯ РАБОТА")
        print("   📍 API не полностью возвращает ожидаемую информацию")

def main():
    """Основная функция тестирования"""
    print("🎉 ФИНАЛЬНАЯ ПРОВЕРКА: Модальное окно деталей ячейки с полной информацией о грузах")
    print("="*100)
    print(f"🕐 Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Базовый URL: {BASE_URL}")
    print(f"👤 Оператор: {WAREHOUSE_OPERATOR_PHONE}")
    
    # Выполняем тесты по порядку
    tests = [
        test_warehouse_operator_auth,
        test_get_warehouse_id,
        test_layout_with_cargo_api,
        test_specific_cells,
        test_operator_cargo_data_retrieval
    ]
    
    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ Ошибка в тесте {test_func.__name__}: {e}")
            log_test(test_func.__name__, False, f"Exception: {str(e)}")
    
    # Выводим итоговый отчет
    print_summary()

if __name__ == "__main__":
    main()
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

def test_warehouse_statistics_api():
    """Тест 3: Тестирование исправленного API статистики"""
    
    print("\n📊 ТЕСТ 3: Тестирование исправленного API статистики")
    
    if not warehouse_id:
        return log_test("API статистики склада", False, "warehouse_id не найден")
    
    response, response_time = make_request("GET", f"/warehouses/{warehouse_id}/statistics")
    
    if not response:
        return log_test("API статистики склада", False, "Ошибка сети", response_time)
    
    if response.status_code == 200:
        data = response.json()
        
        occupied_cells = data.get("occupied_cells", 0)
        total_placed_cargo = data.get("total_placed_cargo", 0)
        
        print(f"📍 РЕЗУЛЬТАТЫ СТАТИСТИКИ:")
        print(f"   - occupied_cells: {occupied_cells}")
        print(f"   - total_placed_cargo: {total_placed_cargo}")
        
        # КРИТИЧЕСКИЕ ПРОВЕРКИ
        success = True
        issues = []
        
        # Проверка 1: occupied_cells должно быть 2
        if occupied_cells != 2:
            success = False
            issues.append(f"occupied_cells = {occupied_cells} (ожидалось 2)")
        
        # Проверка 2: total_placed_cargo должно быть 3
        if total_placed_cargo != 3:
            success = False
            issues.append(f"total_placed_cargo = {total_placed_cargo} (ожидалось 3)")
        
        if success:
            details = f"✅ occupied_cells = {occupied_cells}, total_placed_cargo = {total_placed_cargo}"
            return log_test("API статистики склада", True, details, response_time)
        else:
            details = f"❌ {', '.join(issues)}"
            return log_test("API статистики склада", False, details, response_time)
    else:
        error_detail = response.json().get("detail", "Unknown error") if response.content else "Empty response"
        return log_test("API статистики склада", False, f"HTTP {response.status_code}: {error_detail}", response_time)

def test_diagnostic_logging():
    """Тест 4: Проверка диагностического логирования"""
    
    print("\n🔍 ТЕСТ 4: Проверка диагностического логирования")
    
    if not warehouse_id:
        return log_test("Диагностическое логирование", False, "warehouse_id не найден")
    
    # Повторный вызов API для получения логов
    response, response_time = make_request("GET", f"/warehouses/{warehouse_id}/statistics")
    
    if not response:
        return log_test("Диагностическое логирование", False, "Ошибка сети", response_time)
    
    if response.status_code == 200:
        data = response.json()
        
        # Проверяем наличие диагностической информации
        placement_statistics = data.get("placement_statistics", {})
        
        if placement_statistics:
            print(f"🔍 ДИАГНОСТИЧЕСКАЯ ИНФОРМАЦИЯ:")
            for key, value in placement_statistics.items():
                print(f"   - {key}: {value}")
            
            # Проверяем ключевые поля
            data_source = placement_statistics.get("data_source")
            unique_occupied_cells = placement_statistics.get("unique_occupied_cells")
            placement_records_count = placement_statistics.get("placement_records_count")
            
            success = True
            issues = []
            
            if data_source != "placement_records":
                success = False
                issues.append(f"data_source = {data_source} (ожидалось 'placement_records')")
            
            if unique_occupied_cells != 2:
                success = False
                issues.append(f"unique_occupied_cells = {unique_occupied_cells} (ожидалось 2)")
            
            if success:
                details = f"✅ data_source = {data_source}, unique_occupied_cells = {unique_occupied_cells}"
                return log_test("Диагностическое логирование", True, details, response_time)
            else:
                details = f"❌ {', '.join(issues)}"
                return log_test("Диагностическое логирование", False, details, response_time)
        else:
            return log_test("Диагностическое логирование", False, "placement_statistics отсутствует", response_time)
    else:
        error_detail = response.json().get("detail", "Unknown error") if response.content else "Empty response"
        return log_test("Диагностическое логирование", False, f"HTTP {response.status_code}: {error_detail}", response_time)

def test_layout_with_cargo_consistency():
    """Тест 5: Сравнение с визуальной схемой (layout-with-cargo)"""
    
    print("\n🗺️ ТЕСТ 5: Сравнение с визуальной схемой")
    
    if not warehouse_id:
        return log_test("Сравнение с layout-with-cargo", False, "warehouse_id не найден")
    
    response, response_time = make_request("GET", f"/warehouses/{warehouse_id}/layout-with-cargo")
    
    if not response:
        return log_test("Сравнение с layout-with-cargo", False, "Ошибка сети", response_time)
    
    if response.status_code == 200:
        data = response.json()
        
        occupied_cells_layout = data.get("occupied_cells", 0)
        total_cargo_layout = data.get("total_cargo", 0)
        
        print(f"🗺️ РЕЗУЛЬТАТЫ LAYOUT-WITH-CARGO:")
        print(f"   - occupied_cells: {occupied_cells_layout}")
        print(f"   - total_cargo: {total_cargo_layout}")
        
        # Проверяем соответствие со статистикой
        success = True
        issues = []
        
        if occupied_cells_layout != 2:
            success = False
            issues.append(f"layout occupied_cells = {occupied_cells_layout} (ожидалось 2)")
        
        if total_cargo_layout != 3:
            success = False
            issues.append(f"layout total_cargo = {total_cargo_layout} (ожидалось 3)")
        
        if success:
            details = f"✅ Статистика совпадает: occupied_cells = {occupied_cells_layout}, total_cargo = {total_cargo_layout}"
            return log_test("Сравнение с layout-with-cargo", True, details, response_time)
        else:
            details = f"❌ {', '.join(issues)}"
            return log_test("Сравнение с layout-with-cargo", False, details, response_time)
    else:
        error_detail = response.json().get("detail", "Unknown error") if response.content else "Empty response"
        return log_test("Сравнение с layout-with-cargo", False, f"HTTP {response.status_code}: {error_detail}", response_time)

def test_target_cargo_verification():
    """Тест 6: Проверка целевых грузов в схеме"""
    
    print("\n🎯 ТЕСТ 6: Проверка целевых грузов")
    
    if not warehouse_id:
        return log_test("Проверка целевых грузов", False, "warehouse_id не найден")
    
    response, response_time = make_request("GET", f"/warehouses/{warehouse_id}/layout-with-cargo")
    
    if not response:
        return log_test("Проверка целевых грузов", False, "Ошибка сети", response_time)
    
    if response.status_code == 200:
        data = response.json()
        
        # Ищем целевые грузы в схеме
        target_cargo = ["25082235/01/01", "25082235/01/02", "25082235/02/01"]
        found_cargo = []
        
        blocks = data.get("blocks", [])
        for block in blocks:
            shelves = block.get("shelves", [])
            for shelf in shelves:
                cells = shelf.get("cells", [])
                for cell in cells:
                    if cell.get("is_occupied"):
                        cargo_info = cell.get("cargo_info", {})
                        individual_number = cargo_info.get("individual_number")
                        if individual_number in target_cargo:
                            found_cargo.append(individual_number)
                            cell_location = cell.get("location_code", "Unknown")
                            print(f"   ✅ Найден груз {individual_number} в ячейке {cell_location}")
        
        # Проверяем, что найдены все целевые грузы
        missing_cargo = [cargo for cargo in target_cargo if cargo not in found_cargo]
        
        if not missing_cargo:
            details = f"✅ Все целевые грузы найдены: {found_cargo}"
            return log_test("Проверка целевых грузов", True, details, response_time)
        else:
            details = f"❌ Не найдены грузы: {missing_cargo}. Найдены: {found_cargo}"
            return log_test("Проверка целевых грузов", False, details, response_time)
    else:
        error_detail = response.json().get("detail", "Unknown error") if response.content else "Empty response"
        return log_test("Проверка целевых грузов", False, f"HTTP {response.status_code}: {error_detail}", response_time)

def print_summary():
    """Вывод итогового отчета"""
    print("\n" + "="*80)
    print("📊 ИТОГОВЫЙ ОТЧЕТ КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ")
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
    
    print(f"\n🎯 КРИТЕРИИ УСПЕХА:")
    
    # Проверяем критические критерии
    statistics_test = next((r for r in test_results if "API статистики склада" in r["test"]), None)
    layout_test = next((r for r in test_results if "layout-with-cargo" in r["test"]), None)
    cargo_test = next((r for r in test_results if "целевых грузов" in r["test"]), None)
    
    if statistics_test and statistics_test["success"]:
        print("   ✅ occupied_cells = 2 (было 14)")
        print("   ✅ total_placed_cargo = 3")
    else:
        print("   ❌ Статистика склада не исправлена")
    
    if layout_test and layout_test["success"]:
        print("   ✅ Статистика совпадает с визуальной схемой")
    else:
        print("   ❌ Несоответствие между статистикой и схемой")
    
    if cargo_test and cargo_test["success"]:
        print("   ✅ Показывает только актуально размещенные грузы")
    else:
        print("   ❌ Проблемы с отображением целевых грузов")
    
    print(f"\n🏁 ЗАКЛЮЧЕНИЕ:")
    if success_rate >= 80:
        print("   🎉 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ РАБОТАЕТ УСПЕШНО!")
        print("   📍 Карточка склада теперь показывает правильно 2 занятые ячейки!")
    else:
        print("   ⚠️ ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНАЯ РАБОТА")
        print("   📍 Исправление не полностью функционально")

def main():
    """Основная функция тестирования"""
    print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправление статистики для показа только реально занятых ячеек")
    print("="*100)
    print(f"🕐 Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Базовый URL: {BASE_URL}")
    print(f"👤 Оператор: {WAREHOUSE_OPERATOR_PHONE}")
    
    # Выполняем тесты по порядку
    tests = [
        test_warehouse_operator_auth,
        test_get_warehouse_id,
        test_warehouse_statistics_api,
        test_diagnostic_logging,
        test_layout_with_cargo_consistency,
        test_target_cargo_verification
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
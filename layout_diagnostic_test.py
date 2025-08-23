#!/usr/bin/env python3
"""
🔍 ДИАГНОСТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Проблема с отображением размещенных грузов

**ЦЕЛЬ:** Диагностировать проблему с API layout-with-cargo через добавленное логирование

**ТЕСТ:**
1. Авторизоваться как оператор склада (+79777888999/warehouse123)
2. Получить warehouse_id для "Москва Склад №1"
3. Вызвать API `/api/warehouses/{warehouse_id}/layout-with-cargo`
4. Проверить диагностические логи о:
   - Количестве найденных placement_records для склада
   - Общем количестве placement_records в базе
   - Конкретных записях 25082235/01/01 и 25082235/01/02
   - Их warehouse_id и location значениях

**ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:**
- В логах увидим почему API возвращает пустую схему
- Определим есть ли проблема с warehouse_id в placement_records
- Найдем точную причину почему грузы 25082235/01/01 и 25082235/01/02 не отображаются

**КРИТИЧНО:** Получить детальную диагностику через добавленные print логи
"""

import requests
import json
import sys
from datetime import datetime
import time

# Configuration
BACKEND_URL = "https://tajline-manage-1.preview.emergentagent.com/api"
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"

# Test credentials
TEST_CREDENTIALS = {
    "phone": WAREHOUSE_OPERATOR_PHONE,
    "password": WAREHOUSE_OPERATOR_PASSWORD
}

# Global variables
auth_token = None
test_results = []
warehouse_id = None
moscow_warehouse_name = "Москва Склад №1"
target_cargo_numbers = ["25082235/01/01", "25082235/01/02"]  # Целевые грузы для диагностики

def log_test_result(test_name, success, details, response_time_ms=None):
    """Log test result with details"""
    status = "✅ PASSED" if success else "❌ FAILED"
    result = {
        "test": test_name,
        "status": status,
        "success": success,
        "details": details,
        "timestamp": datetime.now().isoformat(),
        "response_time_ms": response_time_ms
    }
    test_results.append(result)
    
    time_info = f" ({response_time_ms}ms)" if response_time_ms else ""
    print(f"{status}: {test_name}{time_info}")
    print(f"   Details: {details}")
    print()

def make_request(method, endpoint, data=None, headers=None):
    """Make HTTP request with error handling and timing"""
    url = f"{BACKEND_URL}{endpoint}"
    
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
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        return response, response_time_ms
    
    except requests.exceptions.RequestException as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        print(f"❌ Request failed: {e}")
        return None, response_time_ms

def test_warehouse_operator_authentication():
    """Test 1: Авторизация оператора склада (+79777888999/warehouse123)"""
    global auth_token
    
    response, response_time = make_request("POST", "/auth/login", TEST_CREDENTIALS)
    
    if not response:
        log_test_result(
            "1. Авторизация оператора склада", 
            False, 
            "Не удалось подключиться к серверу авторизации",
            response_time
        )
        return False
    
    if response.status_code == 200:
        try:
            data = response.json()
            auth_token = data.get("access_token")
            user_info = data.get("user", {})
            
            if auth_token and user_info.get("role") == "warehouse_operator":
                log_test_result(
                    "1. Авторизация оператора склада",
                    True,
                    f"Успешная авторизация '{user_info.get('full_name')}' (роль: {user_info.get('role')}), JWT токен получен корректно",
                    response_time
                )
                return True
            else:
                log_test_result(
                    "1. Авторизация оператора склада",
                    False,
                    f"Неверная роль пользователя: {user_info.get('role')} (ожидалась warehouse_operator)",
                    response_time
                )
                return False
        except Exception as e:
            log_test_result(
                "1. Авторизация оператора склада",
                False,
                f"Ошибка парсинга ответа авторизации: {e}",
                response_time
            )
            return False
    else:
        log_test_result(
            "1. Авторизация оператора склада",
            False,
            f"HTTP {response.status_code}: {response.text}",
            response_time
        )
        return False

def test_get_warehouse_id():
    """Test 2: Получение warehouse_id для "Москва Склад №1" """
    global warehouse_id
    
    response, response_time = make_request("GET", "/operator/warehouses")
    
    if not response:
        log_test_result(
            "2. Получение warehouse_id для Москва Склад №1",
            False,
            "Не удалось подключиться к серверу",
            response_time
        )
        return False
    
    if response.status_code == 200:
        try:
            warehouses = response.json()
            
            if not warehouses:
                log_test_result(
                    "2. Получение warehouse_id для Москва Склад №1",
                    False,
                    "Список складов пуст",
                    response_time
                )
                return False
            
            # Ищем склад "Москва Склад №1"
            moscow_warehouse = None
            for warehouse in warehouses:
                if moscow_warehouse_name in warehouse.get("name", ""):
                    moscow_warehouse = warehouse
                    warehouse_id = warehouse.get("id")
                    break
            
            if moscow_warehouse:
                log_test_result(
                    "2. Получение warehouse_id для Москва Склад №1",
                    True,
                    f"Найден склад 'Москва Склад №1' (ID: {warehouse_id})",
                    response_time
                )
                return True
            else:
                warehouse_names = [w.get("name") for w in warehouses]
                log_test_result(
                    "2. Получение warehouse_id для Москва Склад №1",
                    False,
                    f"Склад '{moscow_warehouse_name}' не найден. Доступные склады: {warehouse_names}",
                    response_time
                )
                return False
                
        except Exception as e:
            log_test_result(
                "2. Получение warehouse_id для Москва Склад №1",
                False,
                f"Ошибка парсинга ответа: {e}",
                response_time
            )
            return False
    else:
        log_test_result(
            "2. Получение warehouse_id для Москва Склад №1",
            False,
            f"HTTP {response.status_code}: {response.text}",
            response_time
        )
        return False

def test_check_placement_records():
    """Test 3: Проверка placement_records для целевых грузов"""
    if not warehouse_id:
        log_test_result(
            "3. Проверка placement_records",
            False,
            "warehouse_id не определен из предыдущего теста",
            0
        )
        return False
    
    # Проверяем placement_records через API individual-units-for-placement
    response, response_time = make_request("GET", "/operator/cargo/individual-units-for-placement")
    
    if not response:
        log_test_result(
            "3. Проверка placement_records",
            False,
            "Не удалось подключиться к серверу",
            response_time
        )
        return False
    
    if response.status_code == 200:
        try:
            data = response.json()
            items = data.get("items", [])
            
            # Ищем целевые грузы
            found_target_cargo = []
            all_cargo = []
            
            for item in items:
                individual_number = item.get("individual_number", "")
                all_cargo.append(individual_number)
                
                if individual_number in target_cargo_numbers:
                    found_target_cargo.append({
                        "individual_number": individual_number,
                        "status": item.get("status", "unknown"),
                        "placement_info": item.get("placement_info", "unknown")
                    })
            
            if found_target_cargo:
                details = f"Найдено {len(found_target_cargo)} из {len(target_cargo_numbers)} целевых единиц: {found_target_cargo}"
            else:
                details = f"Целевые единицы {target_cargo_numbers} НЕ найдены среди {len(items)} единиц"
            
            log_test_result(
                "3. Проверка placement_records",
                len(found_target_cargo) > 0,
                details,
                response_time
            )
            return len(found_target_cargo) > 0
            
        except Exception as e:
            log_test_result(
                "3. Проверка placement_records",
                False,
                f"Ошибка парсинга ответа: {e}",
                response_time
            )
            return False
    else:
        log_test_result(
            "3. Проверка placement_records",
            False,
            f"HTTP {response.status_code}: {response.text}",
            response_time
        )
        return False

def test_layout_with_cargo_diagnostic():
    """Test 4: КРИТИЧЕСКАЯ ПРОБЛЕМА - API layout-with-cargo НЕ РАБОТАЕТ"""
    if not warehouse_id:
        log_test_result(
            "4. API layout-with-cargo диагностика",
            False,
            "warehouse_id не определен из предыдущего теста",
            0
        )
        return False
    
    response, response_time = make_request("GET", f"/warehouses/{warehouse_id}/layout-with-cargo")
    
    if not response:
        log_test_result(
            "4. API layout-with-cargo диагностика",
            False,
            "Не удалось подключиться к серверу",
            response_time
        )
        return False
    
    if response.status_code == 200:
        try:
            layout_data = response.json()
            
            total_cells = layout_data.get("total_cells", 0)
            occupied_cells = layout_data.get("occupied_cells", 0)
            total_cargo = layout_data.get("total_cargo", 0)
            loading_percentage = layout_data.get("occupancy_percentage", 0)
            
            warehouse_info = layout_data.get("warehouse", {})
            layout = warehouse_info.get("layout", {})
            blocks = layout.get("blocks", [])
            
            # Проверяем, есть ли размещенные грузы в схеме
            if occupied_cells == 0 and total_cargo == 0:
                log_test_result(
                    "4. API layout-with-cargo диагностика",
                    False,
                    f"КРИТИЧЕСКАЯ ПРОБЛЕМА - API НЕ РАБОТАЕТ: Всего ячеек: {total_cells}, Занято: {occupied_cells}, Грузов: {total_cargo}, Загрузка: {loading_percentage}%, Блоков: {len(blocks)} - API возвращает пустую схему несмотря на размещенные грузы",
                    response_time
                )
                return False
            else:
                log_test_result(
                    "4. API layout-with-cargo диагностика",
                    True,
                    f"API работает корректно: Всего ячеек: {total_cells}, Занято: {occupied_cells}, Грузов: {total_cargo}, Загрузка: {loading_percentage}%, Блоков: {len(blocks)}",
                    response_time
                )
                return True
            
        except Exception as e:
            log_test_result(
                "4. API layout-with-cargo диагностика",
                False,
                f"Ошибка парсинга ответа: {e}",
                response_time
            )
            return False
    else:
        log_test_result(
            "4. API layout-with-cargo диагностика",
            False,
            f"HTTP {response.status_code}: {response.text}",
            response_time
        )
        return False

def test_target_cargo_in_layout():
    """Test 5: Поиск целевых грузов в схеме склада"""
    if not warehouse_id:
        log_test_result(
            "5. Целевые грузы НЕ найдены в схеме",
            False,
            "warehouse_id не определен из предыдущего теста",
            0
        )
        return False
    
    response, response_time = make_request("GET", f"/warehouses/{warehouse_id}/layout-with-cargo")
    
    if not response or response.status_code != 200:
        log_test_result(
            "5. Целевые грузы НЕ найдены в схеме",
            False,
            "Не удалось получить схему склада",
            response_time
        )
        return False
    
    try:
        layout_data = response.json()
        warehouse_info = layout_data.get("warehouse", {})
        layout = warehouse_info.get("layout", {})
        blocks = layout.get("blocks", [])
        
        # Ищем целевые грузы в схеме
        found_cargo = []
        all_cargo_in_layout = []
        
        for block in blocks:
            shelves = block.get("shelves", [])
            for shelf in shelves:
                cells = shelf.get("cells", [])
                for cell in cells:
                    if cell.get("is_occupied", False):
                        cargo_list = cell.get("cargo", [])
                        location_code = cell.get("location_code", "")
                        
                        if cargo_list:
                            for cargo_info in cargo_list:
                                individual_number = cargo_info.get("individual_number", "")
                                all_cargo_in_layout.append(individual_number)
                                
                                if individual_number in target_cargo_numbers:
                                    found_cargo.append({
                                        "individual_number": individual_number,
                                        "location": location_code,
                                        "cargo_number": cargo_info.get("cargo_number", "")
                                    })
        
        if found_cargo:
            log_test_result(
                "5. Целевые грузы найдены в схеме",
                True,
                f"Найдены целевые грузы: {found_cargo}",
                0
            )
            return True
        else:
            log_test_result(
                "5. Целевые грузы НЕ найдены в схеме",
                False,
                f"Целевые грузы {target_cargo_numbers} НЕ НАЙДЕНЫ - схема показывает {len(all_cargo_in_layout)} занятых ячеек",
                0
            )
            return False
        
    except Exception as e:
        log_test_result(
            "5. Целевые грузы НЕ найдены в схеме",
            False,
            f"Ошибка анализа схемы: {e}",
            0
        )
        return False

def test_data_synchronization_issue():
    """Test 6: Проблема синхронизации данных"""
    # Проверяем синхронизацию между placement_records и схемой склада
    
    # Сначала проверяем individual-units-for-placement
    response1, response_time1 = make_request("GET", "/operator/cargo/individual-units-for-placement")
    
    # Затем проверяем layout-with-cargo
    if warehouse_id:
        response2, response_time2 = make_request("GET", f"/warehouses/{warehouse_id}/layout-with-cargo")
    else:
        response2 = None
        response_time2 = 0
    
    if not response1 or not response2:
        log_test_result(
            "6. Проблема синхронизации данных",
            False,
            "Не удалось получить данные для сравнения",
            response_time1 + response_time2
        )
        return False
    
    try:
        # Анализируем individual-units-for-placement
        units_data = response1.json()
        units_items = units_data.get("items", [])
        
        target_units_in_placement = []
        for item in units_items:
            individual_number = item.get("individual_number", "")
            if individual_number in target_cargo_numbers:
                target_units_in_placement.append({
                    "individual_number": individual_number,
                    "status": item.get("status", "unknown")
                })
        
        # Анализируем layout-with-cargo
        layout_data = response2.json()
        occupied_cells = layout_data.get("occupied_cells", 0)
        
        # Диагностируем проблему
        if target_units_in_placement and occupied_cells == 0:
            log_test_result(
                "6. Проблема синхронизации данных",
                False,
                f"КОРНЕВАЯ ПРИЧИНА ДИАГНОСТИРОВАНА: ✅ {len(target_units_in_placement)} единиц помечены как размещенные в базе данных; ❌ Схема склада показывает {occupied_cells} занятых ячеек; ❌ Целевые грузы НЕ найдены в схеме склада; КОРНЕВАЯ ПРИЧИНА: Проблема с API layout-with-cargo - не показывает размещенные грузы",
                0
            )
            return False
        elif not target_units_in_placement and occupied_cells == 0:
            log_test_result(
                "6. Проблема синхронизации данных",
                False,
                f"Данные синхронизированы, но целевые грузы не размещены: placement_records={len(target_units_in_placement)}, occupied_cells={occupied_cells}",
                0
            )
            return False
        else:
            log_test_result(
                "6. Проблема синхронизации данных",
                True,
                f"Данные синхронизированы корректно: placement_records={len(target_units_in_placement)}, occupied_cells={occupied_cells}",
                0
            )
            return True
        
    except Exception as e:
        log_test_result(
            "6. Проблема синхронизации данных",
            False,
            f"Ошибка анализа синхронизации: {e}",
            0
        )
        return False

def print_diagnostic_summary():
    """Print comprehensive diagnostic summary"""
    print("\n" + "="*80)
    print("🔍 ДИАГНОСТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Проблема с отображением размещенных грузов - РЕЗУЛЬТАТЫ")
    print("="*80)
    
    total_tests = len(test_results)
    passed_tests = len([r for r in test_results if r["success"]])
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n📊 ОБЩАЯ СТАТИСТИКА:")
    print(f"   Всего тестов: {total_tests}")
    print(f"   Пройдено: {passed_tests}")
    print(f"   Провалено: {failed_tests}")
    print(f"   Success Rate: {success_rate:.1f}%")
    
    print(f"\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
    for i, result in enumerate(test_results, 1):
        status_icon = "✅" if result["success"] else "❌"
        time_info = f" ({result['response_time_ms']}ms)" if result.get('response_time_ms') else ""
        print(f"   {i}. {status_icon} {result['test']}{time_info}")
        print(f"      {result['details']}")
    
    print(f"\n🎯 ДИАГНОСТИЧЕСКИЕ ВЫВОДЫ:")
    
    # Анализируем результаты для диагностики
    auth_success = any("Авторизация" in r["test"] and r["success"] for r in test_results)
    warehouse_found = any("warehouse_id" in r["test"] and r["success"] for r in test_results)
    placement_records_found = any("placement_records" in r["test"] and r["success"] for r in test_results)
    layout_api_works = any("layout-with-cargo" in r["test"] and r["success"] for r in test_results)
    cargo_in_layout = any("схеме" in r["test"] and r["success"] for r in test_results)
    sync_issue = any("синхронизации" in r["test"] and not r["success"] for r in test_results)
    
    print(f"   ✅ Авторизация оператора склада: {'РАБОТАЕТ' if auth_success else 'НЕ РАБОТАЕТ'}")
    print(f"   ✅ Получение warehouse_id: {'РАБОТАЕТ' if warehouse_found else 'НЕ РАБОТАЕТ'}")
    print(f"   ✅ Placement records найдены: {'ДА' if placement_records_found else 'НЕТ'}")
    print(f"   ✅ API layout-with-cargo работает: {'ДА' if layout_api_works else 'НЕТ'}")
    print(f"   ✅ Целевые грузы в схеме: {'НАЙДЕНЫ' if cargo_in_layout else 'НЕ НАЙДЕНЫ'}")
    print(f"   ✅ Проблема синхронизации: {'ОБНАРУЖЕНА' if sync_issue else 'НЕ ОБНАРУЖЕНА'}")
    
    print(f"\n🏆 ДИАГНОСТИЧЕСКИЙ РЕЗУЛЬТАТ:")
    if not layout_api_works:
        print("   🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА ПОДТВЕРЖДЕНА!")
        print("   API layout-with-cargo не показывает размещенные грузы в визуальной схеме ячеек.")
        print("   Требуется исправление backend логики для синхронизации с placement_records.")
    elif sync_issue:
        print("   ⚠️ ПРОБЛЕМА СИНХРОНИЗАЦИИ ДАННЫХ!")
        print("   Данные в базе корректны, но API их не отображает.")
    else:
        print("   ✅ ДИАГНОСТИКА ЗАВЕРШЕНА УСПЕШНО!")
        print("   Проблема не воспроизведена или исправлена.")
    
    print("="*80)

def main():
    """Main diagnostic execution"""
    print("🔍 ДИАГНОСТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Проблема с отображением размещенных грузов")
    print("="*80)
    print("Начинаем диагностику проблемы с API layout-with-cargo...")
    print()
    
    # Test 1: Authentication
    if not test_warehouse_operator_authentication():
        print("❌ Критическая ошибка: Не удалось авторизоваться. Остальные тесты невозможны.")
        print_diagnostic_summary()
        return
    
    # Test 2: Get warehouse_id
    if not test_get_warehouse_id():
        print("❌ Критическая ошибка: Не удалось получить warehouse_id. Остальные тесты невозможны.")
        print_diagnostic_summary()
        return
    
    # Test 3: Check placement_records
    test_check_placement_records()
    
    # Test 4: Layout API diagnostic
    test_layout_with_cargo_diagnostic()
    
    # Test 5: Target cargo in layout
    test_target_cargo_in_layout()
    
    # Test 6: Data synchronization issue
    test_data_synchronization_issue()
    
    # Print final diagnostic summary
    print_diagnostic_summary()

if __name__ == "__main__":
    main()
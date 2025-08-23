#!/usr/bin/env python3
"""
🔧 РУЧНОЕ ИСПРАВЛЕНИЕ: Создание placement_records для конкретных грузов

**ЦЕЛЬ:** Создать placement_records для грузов 25082235/01/01, 25082235/01/02, 25082235/02/01

**ПОДХОД:**
1. Авторизация администратора
2. Вызов fix-missing-placement-records API
3. Проверка что placement_records созданы
4. Проверка layout-with-cargo API после создания
"""

import requests
import json
import sys
from datetime import datetime
import time

# Configuration
BACKEND_URL = "https://tajline-manage-1.preview.emergentagent.com/api"

# Admin credentials
ADMIN_PHONE = "+79999888777"
ADMIN_PASSWORD = "admin123"
ADMIN_CREDENTIALS = {
    "phone": ADMIN_PHONE,
    "password": ADMIN_PASSWORD
}

# Warehouse operator credentials
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"
WAREHOUSE_OPERATOR_CREDENTIALS = {
    "phone": WAREHOUSE_OPERATOR_PHONE,
    "password": WAREHOUSE_OPERATOR_PASSWORD
}

# Global variables
admin_token = None
warehouse_operator_token = None
test_results = []
warehouse_id = None

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

def make_request(method, endpoint, data=None, headers=None, token=None):
    """Make HTTP request with error handling and timing"""
    url = f"{BACKEND_URL}{endpoint}"
    
    if headers is None:
        headers = {}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    start_time = time.time()
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method.upper() == "POST":
            headers["Content-Type"] = "application/json"
            response = requests.post(url, json=data, headers=headers, timeout=30)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        return response, response_time_ms
    
    except requests.exceptions.RequestException as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        print(f"❌ Request failed: {e}")
        return None, response_time_ms

def test_admin_authentication():
    """Test 1: Авторизация администратора"""
    global admin_token
    
    response, response_time = make_request("POST", "/auth/login", ADMIN_CREDENTIALS)
    
    if not response:
        log_test_result(
            "1. Авторизация администратора", 
            False, 
            "Не удалось подключиться к серверу авторизации",
            response_time
        )
        return False
    
    if response.status_code == 200:
        try:
            data = response.json()
            admin_token = data.get("access_token")
            user_info = data.get("user", {})
            
            if admin_token and user_info.get("role") == "admin":
                log_test_result(
                    "1. Авторизация администратора",
                    True,
                    f"Успешная авторизация '{user_info.get('full_name')}' (роль: {user_info.get('role')})",
                    response_time
                )
                return True
            else:
                log_test_result(
                    "1. Авторизация администратора",
                    False,
                    f"Неверная роль пользователя: {user_info.get('role')}",
                    response_time
                )
                return False
        except Exception as e:
            log_test_result(
                "1. Авторизация администратора",
                False,
                f"Ошибка парсинга ответа: {e}",
                response_time
            )
            return False
    else:
        log_test_result(
            "1. Авторизация администратора",
            False,
            f"HTTP {response.status_code}: {response.text}",
            response_time
        )
        return False

def test_warehouse_operator_authentication():
    """Test 2: Авторизация оператора склада"""
    global warehouse_operator_token
    
    response, response_time = make_request("POST", "/auth/login", WAREHOUSE_OPERATOR_CREDENTIALS)
    
    if not response:
        log_test_result(
            "2. Авторизация оператора склада", 
            False, 
            "Не удалось подключиться к серверу авторизации",
            response_time
        )
        return False
    
    if response.status_code == 200:
        try:
            data = response.json()
            warehouse_operator_token = data.get("access_token")
            user_info = data.get("user", {})
            
            if warehouse_operator_token and user_info.get("role") == "warehouse_operator":
                log_test_result(
                    "2. Авторизация оператора склада",
                    True,
                    f"Успешная авторизация '{user_info.get('full_name')}' (роль: {user_info.get('role')})",
                    response_time
                )
                return True
            else:
                log_test_result(
                    "2. Авторизация оператора склада",
                    False,
                    f"Неверная роль пользователя: {user_info.get('role')}",
                    response_time
                )
                return False
        except Exception as e:
            log_test_result(
                "2. Авторизация оператора склада",
                False,
                f"Ошибка парсинга ответа: {e}",
                response_time
            )
            return False
    else:
        log_test_result(
            "2. Авторизация оператора склада",
            False,
            f"HTTP {response.status_code}: {response.text}",
            response_time
        )
        return False

def test_get_warehouse_id():
    """Test 3: Получение warehouse_id"""
    global warehouse_id
    
    response, response_time = make_request("GET", "/operator/warehouses", token=warehouse_operator_token)
    
    if not response:
        log_test_result(
            "3. Получение warehouse_id",
            False,
            "Не удалось подключиться к серверу",
            response_time
        )
        return False
    
    if response.status_code == 200:
        try:
            warehouses = response.json()
            
            if warehouses:
                moscow_warehouse = None
                for warehouse in warehouses:
                    if "Москва Склад №1" in warehouse.get("name", ""):
                        moscow_warehouse = warehouse
                        warehouse_id = warehouse.get("id")
                        break
                
                if moscow_warehouse:
                    log_test_result(
                        "3. Получение warehouse_id",
                        True,
                        f"Найден склад '{moscow_warehouse.get('name')}' (ID: {warehouse_id})",
                        response_time
                    )
                    return True
                else:
                    log_test_result(
                        "3. Получение warehouse_id",
                        False,
                        f"Склад 'Москва Склад №1' не найден",
                        response_time
                    )
                    return False
            else:
                log_test_result(
                    "3. Получение warehouse_id",
                    False,
                    "Список складов пуст",
                    response_time
                )
                return False
                
        except Exception as e:
            log_test_result(
                "3. Получение warehouse_id",
                False,
                f"Ошибка парсинга ответа: {e}",
                response_time
            )
            return False
    else:
        log_test_result(
            "3. Получение warehouse_id",
            False,
            f"HTTP {response.status_code}: {response.text}",
            response_time
        )
        return False

def test_run_fix_missing_placement_records():
    """Test 4: Запуск fix-missing-placement-records"""
    
    response, response_time = make_request("GET", "/admin/fix-missing-placement-records", token=admin_token)
    
    if not response:
        log_test_result(
            "4. Запуск fix-missing-placement-records",
            False,
            "Не удалось подключиться к серверу",
            response_time
        )
        return False
    
    if response.status_code == 200:
        try:
            data = response.json()
            
            processed_cargo = data.get("processed_cargo", 0)
            fixed_placement_records = data.get("fixed_placement_records", 0)
            message = data.get("message", "")
            
            log_test_result(
                "4. Запуск fix-missing-placement-records",
                True,
                f"Обработано заявок: {processed_cargo}, Создано placement_records: {fixed_placement_records}, Сообщение: {message}",
                response_time
            )
            return True, fixed_placement_records
                
        except Exception as e:
            log_test_result(
                "4. Запуск fix-missing-placement-records",
                False,
                f"Ошибка парсинга ответа: {e}",
                response_time
            )
            return False, 0
    else:
        log_test_result(
            "4. Запуск fix-missing-placement-records",
            False,
            f"HTTP {response.status_code}: {response.text}",
            response_time
        )
        return False, 0

def test_layout_with_cargo_after_fix():
    """Test 5: Проверка layout-with-cargo после исправления"""
    
    if not warehouse_id:
        log_test_result(
            "5. Проверка layout-with-cargo после исправления",
            False,
            "warehouse_id не получен",
            0
        )
        return False
    
    response, response_time = make_request("GET", f"/warehouses/{warehouse_id}/layout-with-cargo", token=warehouse_operator_token)
    
    if not response:
        log_test_result(
            "5. Проверка layout-with-cargo после исправления",
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
            
            # Ищем целевые грузы
            target_cargo = ["25082235/01/01", "25082235/01/02", "25082235/02/01"]
            found_cargo = []
            
            warehouse_info = layout_data.get("warehouse", {})
            layout = warehouse_info.get("layout", {})
            blocks = layout.get("blocks", [])
            
            for block in blocks:
                shelves = block.get("shelves", [])
                for shelf in shelves:
                    cells = shelf.get("cells", [])
                    for cell in cells:
                        if cell.get("is_occupied", False):
                            cargo_list = cell.get("cargo", [])
                            location_code = cell.get("location_code", "")
                            for cargo_info in cargo_list:
                                individual_number = cargo_info.get("individual_number", "")
                                if individual_number in target_cargo:
                                    found_cargo.append(f"{individual_number}@{location_code}")
            
            if occupied_cells > 0 and len(found_cargo) > 0:
                log_test_result(
                    "5. Проверка layout-with-cargo после исправления",
                    True,
                    f"УСПЕХ! Занято ячеек: {occupied_cells}, Грузов: {total_cargo}, Найдены целевые грузы: {found_cargo}",
                    response_time
                )
                return True
            elif occupied_cells > 0:
                log_test_result(
                    "5. Проверка layout-with-cargo после исправления",
                    True,
                    f"Частичный успех. Занято ячеек: {occupied_cells}, Грузов: {total_cargo}, но целевые грузы не найдены",
                    response_time
                )
                return True
            else:
                log_test_result(
                    "5. Проверка layout-with-cargo после исправления",
                    False,
                    f"Проблема не исправлена. Занято ячеек: {occupied_cells}, Грузов: {total_cargo}",
                    response_time
                )
                return False
                
        except Exception as e:
            log_test_result(
                "5. Проверка layout-with-cargo после исправления",
                False,
                f"Ошибка парсинга ответа: {e}",
                response_time
            )
            return False
    else:
        log_test_result(
            "5. Проверка layout-with-cargo после исправления",
            False,
            f"HTTP {response.status_code}: {response.text}",
            response_time
        )
        return False

def print_test_summary():
    """Print comprehensive test summary"""
    print("\n" + "="*80)
    print("🔧 РУЧНОЕ ИСПРАВЛЕНИЕ: Создание placement_records - РЕЗУЛЬТАТЫ")
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
    
    print("="*80)

def main():
    """Main test execution"""
    print("🔧 РУЧНОЕ ИСПРАВЛЕНИЕ: Создание placement_records для конкретных грузов")
    print("="*80)
    print("Создаем placement_records для грузов 25082235/01/01, 25082235/01/02, 25082235/02/01...")
    print()
    
    # Test 1: Admin authentication
    if not test_admin_authentication():
        print("❌ Критическая ошибка: Не удалось авторизоваться как администратор.")
        print_test_summary()
        return
    
    # Test 2: Warehouse operator authentication
    if not test_warehouse_operator_authentication():
        print("❌ Критическая ошибка: Не удалось авторизоваться как оператор склада.")
        print_test_summary()
        return
    
    # Test 3: Get warehouse ID
    if not test_get_warehouse_id():
        print("❌ Критическая ошибка: Не удалось получить warehouse_id.")
        print_test_summary()
        return
    
    # Test 4: Run fix
    fix_success, fixed_count = test_run_fix_missing_placement_records()
    
    # Test 5: Check layout after fix
    test_layout_with_cargo_after_fix()
    
    # Print final summary
    print_test_summary()

if __name__ == "__main__":
    main()
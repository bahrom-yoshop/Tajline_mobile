#!/usr/bin/env python3
"""
🔍 ДИАГНОСТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Анализ данных placement_records и operator_cargo

**ЦЕЛЬ:** Диагностировать состояние данных для понимания проблемы с отображением грузов

**ТЕСТЫ:**
1. Авторизация оператора склада
2. Проверка данных в operator_cargo для заявки 25082235
3. Проверка placement_records в базе данных
4. Анализ individual_items и их статусов
5. Проверка fully-placed API для сравнения
"""

import requests
import json
import sys
from datetime import datetime
import time

# Configuration
BACKEND_URL = "https://placement-view.preview.emergentagent.com/api"
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"

# Test credentials
WAREHOUSE_OPERATOR_CREDENTIALS = {
    "phone": WAREHOUSE_OPERATOR_PHONE,
    "password": WAREHOUSE_OPERATOR_PASSWORD
}

# Global variables
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

def test_warehouse_operator_authentication():
    """Test 1: Авторизация оператора склада"""
    global warehouse_operator_token
    
    response, response_time = make_request("POST", "/auth/login", WAREHOUSE_OPERATOR_CREDENTIALS)
    
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
            warehouse_operator_token = data.get("access_token")
            user_info = data.get("user", {})
            
            if warehouse_operator_token and user_info.get("role") == "warehouse_operator":
                log_test_result(
                    "1. Авторизация оператора склада",
                    True,
                    f"Успешная авторизация '{user_info.get('full_name')}' (роль: {user_info.get('role')})",
                    response_time
                )
                return True
            else:
                log_test_result(
                    "1. Авторизация оператора склада",
                    False,
                    f"Неверная роль пользователя: {user_info.get('role')}",
                    response_time
                )
                return False
        except Exception as e:
            log_test_result(
                "1. Авторизация оператора склада",
                False,
                f"Ошибка парсинга ответа: {e}",
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
    """Test 2: Получение warehouse_id"""
    global warehouse_id
    
    response, response_time = make_request("GET", "/operator/warehouses", token=warehouse_operator_token)
    
    if not response:
        log_test_result(
            "2. Получение warehouse_id",
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
                        "2. Получение warehouse_id",
                        True,
                        f"Найден склад '{moscow_warehouse.get('name')}' (ID: {warehouse_id})",
                        response_time
                    )
                    return True
                else:
                    log_test_result(
                        "2. Получение warehouse_id",
                        False,
                        f"Склад 'Москва Склад №1' не найден",
                        response_time
                    )
                    return False
            else:
                log_test_result(
                    "2. Получение warehouse_id",
                    False,
                    "Список складов пуст",
                    response_time
                )
                return False
                
        except Exception as e:
            log_test_result(
                "2. Получение warehouse_id",
                False,
                f"Ошибка парсинга ответа: {e}",
                response_time
            )
            return False
    else:
        log_test_result(
            "2. Получение warehouse_id",
            False,
            f"HTTP {response.status_code}: {response.text}",
            response_time
        )
        return False

def test_check_fully_placed_cargo():
    """Test 3: Проверка fully-placed API для поиска заявки 25082235"""
    
    response, response_time = make_request("GET", "/operator/cargo/fully-placed?page=1&per_page=50", token=warehouse_operator_token)
    
    if not response:
        log_test_result(
            "3. Проверка fully-placed API",
            False,
            "Не удалось подключиться к серверу",
            response_time
        )
        return False
    
    if response.status_code == 200:
        try:
            data = response.json()
            items = data.get("items", [])
            
            # Ищем заявку 25082235
            target_cargo = None
            for item in items:
                if item.get("cargo_number", "").startswith("25082235"):
                    target_cargo = item
                    break
            
            if target_cargo:
                individual_units = target_cargo.get("individual_units", [])
                placed_units = [unit for unit in individual_units if unit.get("status") == "placed"]
                
                placed_details = []
                for unit in placed_units:
                    individual_number = unit.get("individual_number", "")
                    placement_info = unit.get("placement_info", "")
                    placed_details.append(f"{individual_number} -> {placement_info}")
                
                log_test_result(
                    "3. Проверка fully-placed API",
                    True,
                    f"Найдена заявка {target_cargo.get('cargo_number')} с {len(placed_units)} размещенными единицами: {placed_details}",
                    response_time
                )
                return True, target_cargo
            else:
                cargo_numbers = [item.get("cargo_number", "") for item in items[:5]]
                log_test_result(
                    "3. Проверка fully-placed API",
                    False,
                    f"Заявка 25082235 не найдена среди {len(items)} полностью размещенных заявок. Примеры: {cargo_numbers}",
                    response_time
                )
                return False, None
                
        except Exception as e:
            log_test_result(
                "3. Проверка fully-placed API",
                False,
                f"Ошибка парсинга ответа: {e}",
                response_time
            )
            return False, None
    else:
        log_test_result(
            "3. Проверка fully-placed API",
            False,
            f"HTTP {response.status_code}: {response.text}",
            response_time
        )
        return False, None

def test_check_individual_units_for_placement():
    """Test 4: Проверка individual-units-for-placement API"""
    
    response, response_time = make_request("GET", "/operator/cargo/individual-units-for-placement?page=1&per_page=50", token=warehouse_operator_token)
    
    if not response:
        log_test_result(
            "4. Проверка individual-units-for-placement API",
            False,
            "Не удалось подключиться к серверу",
            response_time
        )
        return False
    
    if response.status_code == 200:
        try:
            data = response.json()
            items = data.get("items", [])
            
            # Ищем единицы заявки 25082235
            target_units = []
            for item in items:
                individual_number = item.get("individual_number", "")
                if individual_number.startswith("25082235"):
                    target_units.append({
                        "individual_number": individual_number,
                        "status": item.get("status", ""),
                        "is_placed": item.get("is_placed", False),
                        "placement_info": item.get("placement_info", "")
                    })
            
            if target_units:
                log_test_result(
                    "4. Проверка individual-units-for-placement API",
                    True,
                    f"Найдено {len(target_units)} единиц заявки 25082235: {target_units}",
                    response_time
                )
                return True
            else:
                sample_units = [item.get("individual_number", "") for item in items[:5]]
                log_test_result(
                    "4. Проверка individual-units-for-placement API",
                    False,
                    f"Единицы заявки 25082235 не найдены среди {len(items)} единиц для размещения. Примеры: {sample_units}",
                    response_time
                )
                return False
                
        except Exception as e:
            log_test_result(
                "4. Проверка individual-units-for-placement API",
                False,
                f"Ошибка парсинга ответа: {e}",
                response_time
            )
            return False
    else:
        log_test_result(
            "4. Проверка individual-units-for-placement API",
            False,
            f"HTTP {response.status_code}: {response.text}",
            response_time
        )
        return False

def test_layout_with_cargo_diagnosis():
    """Test 5: Диагностика layout-with-cargo API"""
    
    if not warehouse_id:
        log_test_result(
            "5. Диагностика layout-with-cargo API",
            False,
            "warehouse_id не получен",
            0
        )
        return False
    
    response, response_time = make_request("GET", f"/warehouses/{warehouse_id}/layout-with-cargo", token=warehouse_operator_token)
    
    if not response:
        log_test_result(
            "5. Диагностика layout-with-cargo API",
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
            
            # Ищем любые размещенные грузы
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
                                found_cargo.append(f"{individual_number}@{location_code}")
            
            log_test_result(
                "5. Диагностика layout-with-cargo API",
                True,
                f"API работает. Всего ячеек: {total_cells}, Занято: {occupied_cells}, Грузов: {total_cargo}. Найденные грузы: {found_cargo[:10]}{'...' if len(found_cargo) > 10 else ''}",
                response_time
            )
            return True
                
        except Exception as e:
            log_test_result(
                "5. Диагностика layout-with-cargo API",
                False,
                f"Ошибка парсинга ответа: {e}",
                response_time
            )
            return False
    else:
        log_test_result(
            "5. Диагностика layout-with-cargo API",
            False,
            f"HTTP {response.status_code}: {response.text}",
            response_time
        )
        return False

def print_test_summary():
    """Print comprehensive test summary"""
    print("\n" + "="*80)
    print("🔍 ДИАГНОСТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Анализ данных placement_records - РЕЗУЛЬТАТЫ")
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
    print("🔍 ДИАГНОСТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Анализ данных placement_records")
    print("="*80)
    print("Анализируем состояние данных для понимания проблемы с отображением грузов...")
    print()
    
    # Test 1: Authentication
    if not test_warehouse_operator_authentication():
        print("❌ Критическая ошибка: Не удалось авторизоваться.")
        print_test_summary()
        return
    
    # Test 2: Get warehouse ID
    if not test_get_warehouse_id():
        print("❌ Критическая ошибка: Не удалось получить warehouse_id.")
        print_test_summary()
        return
    
    # Test 3: Check fully-placed cargo
    fully_placed_success, target_cargo = test_check_fully_placed_cargo()
    
    # Test 4: Check individual-units-for-placement
    test_check_individual_units_for_placement()
    
    # Test 5: Diagnose layout-with-cargo
    test_layout_with_cargo_diagnosis()
    
    # Print final summary
    print_test_summary()

if __name__ == "__main__":
    main()
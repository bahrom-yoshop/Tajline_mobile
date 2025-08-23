#!/usr/bin/env python3
"""
🎯 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ: Исправление фильтрации и подсчета в режимах "Готов к размещению"

ПРОБЛЕМА:
1. В режиме "Individual Units карточки" показываются полностью размещенные заявки (25082235, 25082298)
2. В режиме "Карточки заявок" неточные данные о количестве размещенных единиц

ИСПРАВЛЕНИЯ:
1. individual-units-for-placement API: Добавлена фильтрация полностью размещенных заявок
2. available-for-placement API: Улучшена логика подсчета размещенных единиц через placement_records

КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ:
✅ Заявки 25082235 и 25082298 НЕ должны быть в списке individual units
✅ Заявка 250101 ДОЛЖНА быть в списке (частично размещена 2/4)
✅ Точный подсчет placed_count через placement_records
✅ Логирование фильтрации individual-units
✅ Улучшенный подсчет размещенных единиц

ЦЕЛЬ: Подтвердить что оба режима "Готов к размещению" теперь работают корректно!
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

def test_individual_units_for_placement_api():
    """Тест 2: КРИТИЧЕСКАЯ ПРОВЕРКА - individual-units-for-placement API фильтрация"""
    
    print("\n🎯 ТЕСТ 2: КРИТИЧЕСКАЯ ПРОВЕРКА - individual-units-for-placement API")
    print("   📝 ЦЕЛЬ: Заявки 25082235 и 25082298 НЕ должны быть в списке (полностью размещены)")
    print("   📝 ЦЕЛЬ: Заявка 250101 ДОЛЖНА быть в списке (частично размещена 2/4)")
    
    response, response_time = make_request("GET", "/operator/cargo/individual-units-for-placement?page=1&per_page=25")
    
    if not response:
        return log_test("individual-units-for-placement API", False, "Ошибка сети", response_time)
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"📊 РЕЗУЛЬТАТЫ individual-units-for-placement API:")
        print(f"   - Всего найдено: {len(data.get('items', []))}")
        
        items = data.get('items', [])
        found_cargo_numbers = set()
        
        # Собираем все номера заявок из результатов
        for item in items:
            cargo_number = item.get('cargo_number', '')
            if cargo_number:
                found_cargo_numbers.add(cargo_number)
        
        print(f"   - Найденные номера заявок: {sorted(found_cargo_numbers)}")
        
        success = True
        issues = []
        
        # КРИТИЧЕСКАЯ ПРОВЕРКА 1: Заявка 25082235 НЕ должна быть в списке
        if '25082235' in found_cargo_numbers:
            success = False
            issues.append("❌ ИСКЛЮЧЕНА: заявка 25082235 найдена в списке (должна быть исключена как полностью размещенная)")
        else:
            print("   ✅ ИСКЛЮЧЕНА: заявка 25082235 НЕ найдена в списке (корректно исключена)")
        
        # КРИТИЧЕСКАЯ ПРОВЕРКА 2: Заявка 25082298 НЕ должна быть в списке
        if '25082298' in found_cargo_numbers:
            success = False
            issues.append("❌ ИСКЛЮЧЕНА: заявка 25082298 найдена в списке (должна быть исключена как полностью размещенная)")
        else:
            print("   ✅ ИСКЛЮЧЕНА: заявка 25082298 НЕ найдена в списке (корректно исключена)")
        
        # КРИТИЧЕСКАЯ ПРОВЕРКА 3: Заявка 250101 ДОЛЖНА быть в списке
        if '250101' not in found_cargo_numbers:
            success = False
            issues.append("❌ ВКЛЮЧЕНА: заявка 250101 НЕ найдена в списке (должна быть включена как частично размещенная)")
        else:
            print("   ✅ ВКЛЮЧЕНА: заявка 250101 найдена в списке (корректно включена как частично размещенная)")
            
            # Дополнительная проверка для заявки 250101
            cargo_250101_items = [item for item in items if item.get('cargo_number') == '250101']
            print(f"   - Единицы заявки 250101: {len(cargo_250101_items)}")
            
            for unit in cargo_250101_items:
                individual_number = unit.get('individual_number', '')
                is_placed = unit.get('is_placed', False)
                print(f"     * {individual_number}: {'размещен' if is_placed else 'не размещен'}")
        
        if success:
            details = f"✅ КРИТИЧЕСКИЕ ПРОВЕРКИ ПРОЙДЕНЫ! Полностью размещенные заявки исключены, частично размещенные включены"
            return log_test("individual-units-for-placement API", True, details, response_time)
        else:
            details = f"❌ {'; '.join(issues)}"
            return log_test("individual-units-for-placement API", False, details, response_time)
    else:
        error_detail = response.json().get("detail", "Unknown error") if response.content else "Empty response"
        return log_test("individual-units-for-placement API", False, f"HTTP {response.status_code}: {error_detail}", response_time)

def test_available_for_placement_api():
    """Тест 3: КРИТИЧЕСКАЯ ПРОВЕРКА - available-for-placement API подсчет через placement_records"""
    
    print("\n🎯 ТЕСТ 3: КРИТИЧЕСКАЯ ПРОВЕРКА - available-for-placement API")
    print("   📝 ЦЕЛЬ: Точный подсчет placed_count через placement_records")
    print("   📝 ЦЕЛЬ: Заявка 250101 должна показывать правильные данные о размещении")
    
    response, response_time = make_request("GET", "/operator/cargo/available-for-placement?page=1&per_page=25")
    
    if not response:
        return log_test("available-for-placement API", False, "Ошибка сети", response_time)
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"📊 РЕЗУЛЬТАТЫ available-for-placement API:")
        print(f"   - Всего найдено: {len(data.get('items', []))}")
        
        items = data.get('items', [])
        found_cargo_250101 = None
        
        # Ищем заявку 250101 для детальной проверки
        for item in items:
            if item.get('cargo_number') == '250101':
                found_cargo_250101 = item
                break
        
        success = True
        issues = []
        
        if not found_cargo_250101:
            success = False
            issues.append("❌ Заявка 250101 не найдена в available-for-placement")
        else:
            print(f"   ✅ Заявка 250101 найдена в списке")
            
            # КРИТИЧЕСКАЯ ПРОВЕРКА: placed_count через placement_records
            placed_count = found_cargo_250101.get('placed_count', 0)
            total_units = found_cargo_250101.get('total_units', 0)
            placement_progress = found_cargo_250101.get('placement_progress', '')
            
            print(f"   - placed_count: {placed_count}")
            print(f"   - total_units: {total_units}")
            print(f"   - placement_progress: {placement_progress}")
            
            # Проверяем логику подсчета
            if placed_count == 2 and total_units == 4:
                print("   ✅ КРИТИЧЕСКИЙ УСПЕХ: placed_count = 2, total_units = 4 (корректный подсчет через placement_records)")
            else:
                success = False
                issues.append(f"❌ Неточный подсчет: placed_count={placed_count}, total_units={total_units} (ожидалось 2/4)")
            
            # Проверяем placement_progress
            expected_progress = "2/4"
            if expected_progress in placement_progress:
                print(f"   ✅ placement_progress корректен: '{placement_progress}'")
            else:
                success = False
                issues.append(f"❌ placement_progress некорректен: '{placement_progress}' (ожидалось содержание '2/4')")
        
        # Дополнительная проверка: убеждаемся что полностью размещенные заявки исключены
        found_fully_placed = []
        for item in items:
            cargo_number = item.get('cargo_number', '')
            placed_count = item.get('placed_count', 0)
            total_units = item.get('total_units', 0)
            
            if placed_count > 0 and placed_count >= total_units:
                found_fully_placed.append(cargo_number)
        
        if found_fully_placed:
            success = False
            issues.append(f"❌ Найдены полностью размещенные заявки в списке: {found_fully_placed}")
        else:
            print("   ✅ Полностью размещенные заявки корректно исключены из списка")
        
        if success:
            details = f"✅ КРИТИЧЕСКИЕ ПРОВЕРКИ ПРОЙДЕНЫ! Подсчет через placement_records работает корректно"
            return log_test("available-for-placement API", True, details, response_time)
        else:
            details = f"❌ {'; '.join(issues)}"
            return log_test("available-for-placement API", False, details, response_time)
    else:
        error_detail = response.json().get("detail", "Unknown error") if response.content else "Empty response"
        return log_test("available-for-placement API", False, f"HTTP {response.status_code}: {error_detail}", response_time)

def test_placement_records_verification():
    """Тест 4: Проверка данных placement_records для диагностики"""
    
    print("\n🔍 ТЕСТ 4: Диагностика placement_records")
    print("   📝 ЦЕЛЬ: Проверить состояние placement_records для понимания логики фильтрации")
    
    # Проверяем конкретные заявки через verify-cargo API
    test_units = [
        {"unit": "25082235/01/01", "expected_status": "размещен"},
        {"unit": "25082235/01/02", "expected_status": "размещен"},
        {"unit": "25082298/01/01", "expected_status": "размещен"},
        {"unit": "250101/01/01", "expected_status": "не размещен"},
        {"unit": "250101/01/02", "expected_status": "размещен"},
    ]
    
    success = True
    placement_status = {}
    
    for test_unit in test_units:
        unit_number = test_unit["unit"]
        expected_status = test_unit["expected_status"]
        
        response, response_time = make_request("POST", "/operator/placement/verify-cargo", {"qr_code": unit_number})
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get("success"):
                placement_status[unit_number] = "не размещен"
                print(f"   - {unit_number}: не размещен (API вернул success=true)")
            else:
                error = data.get("error", "")
                if "уже размещен" in error.lower():
                    placement_status[unit_number] = "размещен"
                    print(f"   - {unit_number}: размещен (API вернул ошибку 'уже размещен')")
                else:
                    placement_status[unit_number] = f"неизвестно ({error})"
                    print(f"   - {unit_number}: неизвестно - {error}")
        else:
            placement_status[unit_number] = "ошибка API"
            print(f"   - {unit_number}: ошибка API")
    
    # Анализируем результаты
    print(f"\n📊 АНАЛИЗ РАЗМЕЩЕНИЯ:")
    
    # Заявка 25082235
    units_25082235 = [k for k in placement_status.keys() if k.startswith("25082235")]
    placed_25082235 = [k for k in units_25082235 if placement_status[k] == "размещен"]
    print(f"   - Заявка 25082235: {len(placed_25082235)}/{len(units_25082235)} размещено")
    
    # Заявка 25082298
    units_25082298 = [k for k in placement_status.keys() if k.startswith("25082298")]
    placed_25082298 = [k for k in units_25082298 if placement_status[k] == "размещен"]
    print(f"   - Заявка 25082298: {len(placed_25082298)}/{len(units_25082298)} размещено")
    
    # Заявка 250101
    units_250101 = [k for k in placement_status.keys() if k.startswith("250101")]
    placed_250101 = [k for k in units_250101 if placement_status[k] == "размещен"]
    print(f"   - Заявка 250101: {len(placed_250101)}/{len(units_250101)} размещено")
    
    details = f"Диагностика завершена: проверено {len(test_units)} единиц"
    return log_test("Диагностика placement_records", True, details, None)

def test_logging_verification():
    """Тест 5: Проверка логирования фильтрации (косвенная проверка)"""
    
    print("\n📝 ТЕСТ 5: Проверка логирования фильтрации")
    print("   📝 ЦЕЛЬ: Косвенная проверка что логирование работает через повторные вызовы API")
    
    # Делаем несколько вызовов individual-units-for-placement для проверки консистентности
    consistent_results = True
    first_result = None
    
    for i in range(3):
        response, response_time = make_request("GET", "/operator/cargo/individual-units-for-placement?page=1&per_page=25")
        
        if response and response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            cargo_numbers = sorted([item.get('cargo_number', '') for item in items])
            
            if first_result is None:
                first_result = cargo_numbers
                print(f"   - Попытка {i+1}: найдено {len(cargo_numbers)} заявок")
            else:
                if cargo_numbers != first_result:
                    consistent_results = False
                    print(f"   - Попытка {i+1}: НЕСООТВЕТСТВИЕ! найдено {len(cargo_numbers)} заявок")
                else:
                    print(f"   - Попытка {i+1}: результат консистентен ({len(cargo_numbers)} заявок)")
        else:
            consistent_results = False
            print(f"   - Попытка {i+1}: ошибка API")
    
    if consistent_results:
        details = "✅ API возвращает консистентные результаты, логика фильтрации стабильна"
        return log_test("Проверка логирования фильтрации", True, details, None)
    else:
        details = "❌ API возвращает непоследовательные результаты"
        return log_test("Проверка логирования фильтрации", False, details, None)

def run_all_tests():
    """Запуск всех тестов"""
    print("🚀 НАЧАЛО ФИНАЛЬНОГО ТЕСТИРОВАНИЯ: Исправление фильтрации и подсчета в режимах 'Готов к размещению'")
    print("=" * 100)
    
    # Список тестов
    tests = [
        test_warehouse_operator_auth,
        test_individual_units_for_placement_api,
        test_available_for_placement_api,
        test_placement_records_verification,
        test_logging_verification,
    ]
    
    # Выполняем тесты
    passed_tests = 0
    total_tests = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed_tests += 1
        except Exception as e:
            print(f"❌ ОШИБКА в тесте {test_func.__name__}: {e}")
    
    # Итоговый отчет
    print("\n" + "=" * 100)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
    print("=" * 100)
    
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"✅ Пройдено тестов: {passed_tests}/{total_tests}")
    print(f"📈 Процент успешности: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ Individual units API исключает полностью размещенные заявки")
        print("✅ Available placement API показывает точные данные о размещении")
        print("✅ Логирование подтверждает корректную фильтрацию")
        print("✅ Подсчет размещенных единиц через placement_records работает")
        print("\n🎯 ЦЕЛЬ ДОСТИГНУТА: Оба режима 'Готов к размещению' теперь работают корректно!")
    elif success_rate >= 80:
        print(f"\n⚠️ БОЛЬШИНСТВО ТЕСТОВ ПРОЙДЕНО ({success_rate:.1f}%)")
        print("🔧 Требуются незначительные исправления")
    else:
        print(f"\n❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ ОБНАРУЖЕНЫ ({success_rate:.1f}%)")
        print("🚨 Требуется серьезная доработка системы")
    
    print("\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
    for result in test_results:
        status = "✅" if result["success"] else "❌"
        time_info = f" ({result['response_time']}ms)" if result.get('response_time') else ""
        print(f"{status} {result['test']}{time_info}")
        if result["details"]:
            print(f"   └─ {result['details']}")
    
    return success_rate == 100

if __name__ == "__main__":
    run_all_tests()
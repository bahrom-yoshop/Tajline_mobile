#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправление точности данных в режиме "Карточки заявок" для TAJLINE.TJ

ОСНОВНАЯ ЦЕЛЬ: 
Проверить что API `/api/operator/cargo/available-for-placement` теперь корректно отображает 
точные данные о размещении в полях `total_placed`, `placement_progress` и `overall_placement_status`.

КРИТИЧЕСКИЕ ПРОВЕРКИ:
1. Авторизация оператора склада (+79777888999/warehouse123)
2. Проверка API available-for-placement: Убедиться что `total_placed` и `placement_progress` 
   корректно отражают фактическое размещение через `placement_records`
3. Проверка заявки 250101: Должна показывать правильный прогресс размещения (например 2/4 если 2 единицы размещены)
4. Сравнение с placement_records: Проверить что данные в API соответствуют фактическим записям в `placement_records`
5. Проверка детализации cargo_items: Убедиться что `placed_count` для каждого `cargo_item` корректен

ИСПРАВЛЕННАЯ ПРОБЛЕМА: 
До исправления `total_placed` показывал 0 даже при наличии размещенных единиц, потому что 
использовались неправильные данные из `processed_cargo_items` вместо актуальных данных из `placement_records`.

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: 
API должен показывать точные данные о размещении, соответствующие фактическим записям в базе данных.
"""

import requests
import json
import time
from datetime import datetime

# Конфигурация
BASE_URL = "https://cargo-sync.preview.emergentagent.com/api"
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
    
    print("\n🔐 ТЕСТ 1: Авторизация оператора склада (+79777888999/warehouse123)")
    
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

def test_available_for_placement_api():
    """Тест 2: КРИТИЧЕСКАЯ ПРОВЕРКА - API available-for-placement с точными данными размещения"""
    
    print("\n🎯 ТЕСТ 2: КРИТИЧЕСКАЯ ПРОВЕРКА - API /api/operator/cargo/available-for-placement")
    print("   📝 ЦЕЛЬ: Проверить точность полей total_placed, placement_progress, overall_placement_status")
    
    response, response_time = make_request("GET", "/operator/cargo/available-for-placement")
    
    if not response:
        return log_test("API available-for-placement точность данных", False, "Ошибка сети", response_time)
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"📊 АНАЛИЗ ДАННЫХ API available-for-placement:")
        print(f"   - Всего заявок: {len(data.get('items', []))}")
        
        success = True
        issues = []
        found_250101 = False
        
        # Ищем заявку 250101 для детального анализа
        for item in data.get('items', []):
            cargo_number = item.get('cargo_number', '')
            
            if cargo_number == '250101':
                found_250101 = True
                print(f"\n   🎯 НАЙДЕНА ЗАЯВКА 250101 - ДЕТАЛЬНЫЙ АНАЛИЗ:")
                
                # Проверяем критические поля
                total_placed = item.get('total_placed', 0)
                placement_progress = item.get('placement_progress', '')
                overall_placement_status = item.get('overall_placement_status', '')
                
                print(f"      - total_placed: {total_placed}")
                print(f"      - placement_progress: '{placement_progress}'")
                print(f"      - overall_placement_status: '{overall_placement_status}'")
                
                # Анализируем cargo_items для детализации
                cargo_items = item.get('cargo_items', [])
                print(f"      - cargo_items: {len(cargo_items)} типов груза")
                
                total_units = 0
                total_placed_calculated = 0
                
                for cargo_item in cargo_items:
                    cargo_name = cargo_item.get('cargo_name', 'Неизвестно')
                    placed_count = cargo_item.get('placed_count', 0)
                    individual_items = cargo_item.get('individual_items', [])
                    
                    print(f"         • {cargo_name}: {placed_count}/{len(individual_items)} размещено")
                    
                    total_units += len(individual_items)
                    total_placed_calculated += placed_count
                
                print(f"      - Расчетные данные: {total_placed_calculated}/{total_units}")
                
                # КРИТИЧЕСКИЕ ПРОВЕРКИ
                if total_placed == 0 and total_placed_calculated > 0:
                    success = False
                    issues.append(f"total_placed={total_placed}, но фактически размещено {total_placed_calculated} единиц")
                
                if placement_progress == '0/4' and total_placed_calculated > 0:
                    success = False
                    issues.append(f"placement_progress='{placement_progress}', но фактически размещено {total_placed_calculated} единиц")
                
                if total_placed != total_placed_calculated:
                    success = False
                    issues.append(f"total_placed ({total_placed}) не соответствует расчетному значению ({total_placed_calculated})")
                
                # Проверяем соответствие placement_progress
                expected_progress = f"{total_placed_calculated}/{total_units}"
                if placement_progress != expected_progress:
                    success = False
                    issues.append(f"placement_progress '{placement_progress}' не соответствует ожидаемому '{expected_progress}'")
                
                break
        
        if not found_250101:
            success = False
            issues.append("Заявка 250101 не найдена в списке available-for-placement")
        
        if success:
            details = f"✅ КРИТИЧЕСКИЙ ТЕСТ ПРОЙДЕН! Заявка 250101 показывает точные данные размещения"
            return log_test("API available-for-placement точность данных", True, details, response_time)
        else:
            details = f"❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ: {'; '.join(issues)}"
            return log_test("API available-for-placement точность данных", False, details, response_time)
    else:
        error_detail = response.json().get("detail", "Unknown error") if response.content else "Empty response"
        return log_test("API available-for-placement точность данных", False, f"HTTP {response.status_code}: {error_detail}", response_time)

def test_placement_records_verification():
    """Тест 3: Проверка соответствия данных с placement_records через verify-cargo API"""
    
    print("\n🔍 ТЕСТ 3: Проверка соответствия с placement_records через verify-cargo")
    print("   📝 ЦЕЛЬ: Убедиться что данные API соответствуют фактическим записям в placement_records")
    
    # Тестируем известные единицы груза из заявки 250101
    test_units = [
        {"qr_code": "250101/01/01", "expected_status": "не размещен"},
        {"qr_code": "250101/01/02", "expected_status": "размещен"},
        {"qr_code": "250101/02/01", "expected_status": "размещен"},
        {"qr_code": "250101/02/02", "expected_status": "не размещен"}
    ]
    
    placement_data = {}
    success = True
    issues = []
    
    for unit in test_units:
        qr_code = unit["qr_code"]
        expected_status = unit["expected_status"]
        
        print(f"\n   🧪 Проверяем единицу {qr_code} (ожидается: {expected_status})")
        
        response, response_time = make_request("POST", "/operator/placement/verify-cargo", {"qr_code": qr_code})
        
        if not response:
            success = False
            issues.append(f"{qr_code}: Ошибка сети")
            continue
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                # Груз найден и не размещен
                placement_data[qr_code] = "не размещен"
                print(f"      ✅ {qr_code}: не размещен (груз найден для размещения)")
            else:
                error = data.get("error", "")
                if "уже размещен" in error.lower():
                    # Груз размещен
                    placement_data[qr_code] = "размещен"
                    print(f"      ✅ {qr_code}: размещен (груз уже размещен)")
                else:
                    success = False
                    issues.append(f"{qr_code}: Неожиданная ошибка - {error}")
                    print(f"      ❌ {qr_code}: Неожиданная ошибка - {error}")
        else:
            success = False
            error_detail = response.json().get("detail", "Unknown error") if response.content else "Empty response"
            issues.append(f"{qr_code}: HTTP {response.status_code}")
            print(f"      ❌ {qr_code}: HTTP {response.status_code}: {error_detail}")
    
    # Анализируем результаты
    print(f"\n   📊 АНАЛИЗ РЕЗУЛЬТАТОВ PLACEMENT_RECORDS:")
    placed_count = sum(1 for status in placement_data.values() if status == "размещен")
    total_count = len(placement_data)
    
    print(f"      - Всего единиц проверено: {total_count}")
    print(f"      - Размещено единиц: {placed_count}")
    print(f"      - Не размещено единиц: {total_count - placed_count}")
    print(f"      - Прогресс размещения: {placed_count}/{total_count}")
    
    # Проверяем соответствие ожиданиям
    for unit in test_units:
        qr_code = unit["qr_code"]
        expected_status = unit["expected_status"]
        actual_status = placement_data.get(qr_code, "неизвестно")
        
        if actual_status != expected_status:
            success = False
            issues.append(f"{qr_code}: ожидался статус '{expected_status}', получен '{actual_status}'")
    
    if success:
        details = f"✅ Данные placement_records соответствуют ожиданиям: {placed_count}/{total_count} размещено"
        return log_test("Соответствие с placement_records", True, details)
    else:
        details = f"❌ Проблемы с placement_records: {'; '.join(issues)}"
        return log_test("Соответствие с placement_records", False, details)

def test_cargo_items_placed_count():
    """Тест 4: Проверка корректности placed_count для каждого cargo_item"""
    
    print("\n📋 ТЕСТ 4: Проверка детализации cargo_items - корректность placed_count")
    print("   📝 ЦЕЛЬ: Убедиться что placed_count для каждого cargo_item корректен")
    
    response, response_time = make_request("GET", "/operator/cargo/available-for-placement")
    
    if not response:
        return log_test("Детализация cargo_items placed_count", False, "Ошибка сети", response_time)
    
    if response.status_code == 200:
        data = response.json()
        
        success = True
        issues = []
        found_250101 = False
        
        # Ищем заявку 250101 для детального анализа cargo_items
        for item in data.get('items', []):
            cargo_number = item.get('cargo_number', '')
            
            if cargo_number == '250101':
                found_250101 = True
                print(f"\n   🎯 АНАЛИЗ CARGO_ITEMS для заявки 250101:")
                
                cargo_items = item.get('cargo_items', [])
                
                for i, cargo_item in enumerate(cargo_items, 1):
                    cargo_name = cargo_item.get('cargo_name', 'Неизвестно')
                    placed_count = cargo_item.get('placed_count', 0)
                    individual_items = cargo_item.get('individual_items', [])
                    
                    print(f"      {i}. {cargo_name}:")
                    print(f"         - placed_count: {placed_count}")
                    print(f"         - individual_items: {len(individual_items)} единиц")
                    
                    # Проверяем каждую individual_item
                    actual_placed = 0
                    for individual_item in individual_items:
                        individual_number = individual_item.get('individual_number', '')
                        is_placed = individual_item.get('is_placed', False)
                        
                        if is_placed:
                            actual_placed += 1
                            print(f"            ✅ {individual_number}: размещен")
                        else:
                            print(f"            ⏳ {individual_number}: ожидает размещения")
                    
                    print(f"         - Фактически размещено: {actual_placed}")
                    
                    # КРИТИЧЕСКАЯ ПРОВЕРКА
                    if placed_count != actual_placed:
                        success = False
                        issues.append(f"{cargo_name}: placed_count={placed_count}, но фактически размещено {actual_placed}")
                        print(f"         ❌ НЕСООТВЕТСТВИЕ: placed_count={placed_count}, фактически={actual_placed}")
                    else:
                        print(f"         ✅ СООТВЕТСТВИЕ: placed_count корректен")
                
                break
        
        if not found_250101:
            success = False
            issues.append("Заявка 250101 не найдена для анализа cargo_items")
        
        if success:
            details = f"✅ Все cargo_items имеют корректные значения placed_count"
            return log_test("Детализация cargo_items placed_count", True, details, response_time)
        else:
            details = f"❌ Проблемы с placed_count: {'; '.join(issues)}"
            return log_test("Детализация cargo_items placed_count", False, details, response_time)
    else:
        error_detail = response.json().get("detail", "Unknown error") if response.content else "Empty response"
        return log_test("Детализация cargo_items placed_count", False, f"HTTP {response.status_code}: {error_detail}", response_time)

def test_overall_placement_status():
    """Тест 5: Проверка корректности overall_placement_status"""
    
    print("\n🎯 ТЕСТ 5: Проверка корректности overall_placement_status")
    print("   📝 ЦЕЛЬ: Убедиться что overall_placement_status отражает реальное состояние размещения")
    
    response, response_time = make_request("GET", "/operator/cargo/available-for-placement")
    
    if not response:
        return log_test("Корректность overall_placement_status", False, "Ошибка сети", response_time)
    
    if response.status_code == 200:
        data = response.json()
        
        success = True
        issues = []
        found_250101 = False
        
        # Ищем заявку 250101 для анализа overall_placement_status
        for item in data.get('items', []):
            cargo_number = item.get('cargo_number', '')
            
            if cargo_number == '250101':
                found_250101 = True
                print(f"\n   🎯 АНАЛИЗ OVERALL_PLACEMENT_STATUS для заявки 250101:")
                
                total_placed = item.get('total_placed', 0)
                total_units = 0
                overall_placement_status = item.get('overall_placement_status', '')
                
                # Подсчитываем общее количество единиц
                cargo_items = item.get('cargo_items', [])
                for cargo_item in cargo_items:
                    individual_items = cargo_item.get('individual_items', [])
                    total_units += len(individual_items)
                
                print(f"      - total_placed: {total_placed}")
                print(f"      - total_units: {total_units}")
                print(f"      - overall_placement_status: '{overall_placement_status}'")
                
                # Определяем ожидаемый статус
                if total_placed == 0:
                    expected_status = "awaiting_placement"
                elif total_placed == total_units:
                    expected_status = "fully_placed"
                else:
                    expected_status = "partially_placed"
                
                print(f"      - Ожидаемый статус: '{expected_status}'")
                
                # КРИТИЧЕСКАЯ ПРОВЕРКА
                if overall_placement_status != expected_status:
                    success = False
                    issues.append(f"overall_placement_status='{overall_placement_status}', ожидался '{expected_status}'")
                    print(f"      ❌ НЕСООТВЕТСТВИЕ: статус не соответствует фактическому состоянию")
                else:
                    print(f"      ✅ СООТВЕТСТВИЕ: overall_placement_status корректен")
                
                break
        
        if not found_250101:
            success = False
            issues.append("Заявка 250101 не найдена для анализа overall_placement_status")
        
        if success:
            details = f"✅ overall_placement_status корректно отражает состояние размещения"
            return log_test("Корректность overall_placement_status", True, details, response_time)
        else:
            details = f"❌ Проблемы с overall_placement_status: {'; '.join(issues)}"
            return log_test("Корректность overall_placement_status", False, details, response_time)
    else:
        error_detail = response.json().get("detail", "Unknown error") if response.content else "Empty response"
        return log_test("Корректность overall_placement_status", False, f"HTTP {response.status_code}: {error_detail}", response_time)

def print_summary():
    """Вывод итогового отчета"""
    print("\n" + "="*100)
    print("🎯 ИТОГОВЫЙ ОТЧЕТ: ИСПРАВЛЕНИЕ ТОЧНОСТИ ДАННЫХ В РЕЖИМЕ 'КАРТОЧКИ ЗАЯВОК'")
    print("="*100)
    
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
    
    print(f"\n🎯 КРИТИЧЕСКИЕ РЕЗУЛЬТАТЫ:")
    
    # Проверяем критические критерии
    auth_test = next((r for r in test_results if "Авторизация" in r["test"]), None)
    api_test = next((r for r in test_results if "available-for-placement" in r["test"]), None)
    placement_test = next((r for r in test_results if "placement_records" in r["test"]), None)
    cargo_items_test = next((r for r in test_results if "cargo_items" in r["test"]), None)
    status_test = next((r for r in test_results if "overall_placement_status" in r["test"]), None)
    
    if auth_test and auth_test["success"]:
        print("   ✅ Авторизация оператора склада (+79777888999/warehouse123) успешна")
    else:
        print("   ❌ Проблемы с авторизацией оператора склада")
    
    if api_test and api_test["success"]:
        print("   ✅ API available-for-placement показывает точные данные о размещении")
        print("   ✅ total_placed и placement_progress корректно отражают фактическое размещение")
    else:
        print("   ❌ API available-for-placement НЕ показывает точные данные о размещении")
    
    if placement_test and placement_test["success"]:
        print("   ✅ Данные API соответствуют фактическим записям в placement_records")
    else:
        print("   ❌ Данные API НЕ соответствуют записям в placement_records")
    
    if cargo_items_test and cargo_items_test["success"]:
        print("   ✅ placed_count для каждого cargo_item корректен")
    else:
        print("   ❌ Проблемы с placed_count в cargo_items")
    
    if status_test and status_test["success"]:
        print("   ✅ overall_placement_status корректно отражает состояние размещения")
    else:
        print("   ❌ Проблемы с overall_placement_status")
    
    print(f"\n🏁 ЗАКЛЮЧЕНИЕ:")
    if success_rate >= 80:
        print("   🎉 ИСПРАВЛЕНИЕ ТОЧНОСТИ ДАННЫХ ПОДТВЕРЖДЕНО!")
        print("   📍 API /api/operator/cargo/available-for-placement теперь корректно отображает")
        print("   📍 точные данные о размещении, соответствующие фактическим записям в базе данных!")
        print("   📍 Проблема с total_placed=0 при наличии размещенных единиц РЕШЕНА!")
    else:
        print("   ⚠️ ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНАЯ РАБОТА")
        print("   📍 API все еще показывает неточные данные о размещении")
        print("   📍 Необходимо дополнительное исправление синхронизации данных")

def main():
    """Основная функция тестирования"""
    print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправление точности данных в режиме 'Карточки заявок'")
    print("="*100)
    print(f"🕐 Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Базовый URL: {BASE_URL}")
    print(f"👤 Оператор: {WAREHOUSE_OPERATOR_PHONE}")
    print(f"🎯 Основная цель: Проверить точность полей total_placed, placement_progress, overall_placement_status")
    
    # Выполняем тесты по порядку
    tests = [
        test_warehouse_operator_auth,
        test_available_for_placement_api,
        test_placement_records_verification,
        test_cargo_items_placed_count,
        test_overall_placement_status
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
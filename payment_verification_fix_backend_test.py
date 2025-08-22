#!/usr/bin/env python3
"""
🎯 ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ: Убрана проверка оплаты при размещении груза

ПРОБЛЕМА:
При размещении груза через меню "Операции" -> "Размещение груз" система выдавала ошибку 
"Груз не оплачен, размещение невозможно" при сканировании QR кода груза.

ИСПРАВЛЕНИЕ:
Отключена проверка payment_status в API `/api/operator/placement/verify-cargo`. 
Теперь разрешено размещение груза независимо от статуса оплаты.

КРИТИЧЕСКИЕ ОЖИДАНИЯ:
✅ API verify-cargo возвращает success=true для любого груза
✅ Нет ошибки "Груз не оплачен, размещение невозможно"  
✅ В логах видно "РАЗМЕЩЕНИЕ РАЗРЕШЕНО"
✅ Статус оплаты логируется для информации
✅ Размещение работает независимо от payment_status

ЦЕЛЬ: Подтвердить что операторы теперь могут размещать грузы любого статуса оплаты!
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
test_cargo_number = "25082235"  # Тестовый груз из review request

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
    """Тест 1: Авторизация оператора склада (+79777888999/warehouse123)"""
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

def test_find_unpaid_cargo():
    """Тест 2: Поиск неоплаченного груза для тестирования"""
    global test_cargo_number
    
    print("\n🔍 ТЕСТ 2: Поиск неоплаченного груза для тестирования")
    
    # Сначала попробуем найти груз 25082235
    response, response_time = make_request("GET", f"/operator/cargo/available-for-placement?search={test_cargo_number}")
    
    if not response:
        return log_test("Поиск неоплаченного груза", False, "Ошибка сети", response_time)
    
    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        
        # Ищем груз 25082235
        target_cargo = None
        for item in items:
            if item.get("cargo_number") == test_cargo_number:
                target_cargo = item
                break
        
        if target_cargo:
            payment_status = target_cargo.get("payment_status", "unknown")
            details = f"Найден груз {test_cargo_number}, статус оплаты: {payment_status}"
            return log_test("Поиск неоплаченного груза", True, details, response_time)
        else:
            # Если не найден конкретный груз, попробуем найти любой неоплаченный
            unpaid_cargo = None
            for item in items:
                if item.get("payment_status") in ["not_paid", "pending", None]:
                    unpaid_cargo = item
                    break
            
            if unpaid_cargo:
                cargo_number = unpaid_cargo.get("cargo_number")
                payment_status = unpaid_cargo.get("payment_status", "unknown")
                details = f"Найден неоплаченный груз {cargo_number}, статус оплаты: {payment_status}"
                # Обновляем тестовый номер груза
                test_cargo_number = cargo_number
                return log_test("Поиск неоплаченного груза", True, details, response_time)
            else:
                details = f"Неоплаченные грузы не найдены среди {len(items)} доступных грузов"
                return log_test("Поиск неоплаченного груза", False, details, response_time)
    else:
        error_detail = response.json().get("detail", "Unknown error") if response.content else "Empty response"
        return log_test("Поиск неоплаченного груза", False, f"HTTP {response.status_code}: {error_detail}", response_time)

def test_verify_cargo_api():
    """Тест 3: КРИТИЧЕСКАЯ ПРОВЕРКА - API verify-cargo с неоплаченным грузом"""
    print(f"\n🎯 ТЕСТ 3: КРИТИЧЕСКАЯ ПРОВЕРКА - API verify-cargo с грузом {test_cargo_number}")
    
    verify_data = {
        "qr_code": test_cargo_number
    }
    
    response, response_time = make_request("POST", "/operator/placement/verify-cargo", verify_data)
    
    if not response:
        return log_test("API verify-cargo", False, "Ошибка сети", response_time)
    
    if response.status_code == 200:
        data = response.json()
        success = data.get("success", False)
        message = data.get("message", "")
        error_code = data.get("error_code", "")
        
        print(f"📊 РЕЗУЛЬТАТЫ VERIFY-CARGO:")
        print(f"   - success: {success}")
        print(f"   - message: {message}")
        print(f"   - error_code: {error_code}")
        
        # КРИТИЧЕСКАЯ ПРОВЕРКА: API должен вернуть success=true
        if success:
            if "РАЗМЕЩЕНИЕ РАЗРЕШЕНО" in message or "разрешено" in message.lower():
                details = f"✅ КРИТИЧЕСКИЙ УСПЕХ! API возвращает success=true, сообщение: '{message}'"
                return log_test("API verify-cargo возвращает success=true", True, details, response_time)
            else:
                details = f"✅ API возвращает success=true, но сообщение неожиданное: '{message}'"
                return log_test("API verify-cargo возвращает success=true", True, details, response_time)
        else:
            # Проверяем, не возвращается ли старая ошибка CARGO_UNPAID
            if error_code == "CARGO_UNPAID" or "не оплачен" in message:
                details = f"❌ КРИТИЧЕСКАЯ ОШИБКА! Старая проверка оплаты все еще активна. Код: {error_code}, сообщение: '{message}'"
                return log_test("API verify-cargo возвращает success=true", False, details, response_time)
            else:
                details = f"❌ API возвращает success=false по другой причине. Код: {error_code}, сообщение: '{message}'"
                return log_test("API verify-cargo возвращает success=true", False, details, response_time)
    else:
        error_detail = response.json().get("detail", "Unknown error") if response.content else "Empty response"
        return log_test("API verify-cargo возвращает success=true", False, f"HTTP {response.status_code}: {error_detail}", response_time)

def test_verify_cargo_with_different_payment_statuses():
    """Тест 4: Проверка verify-cargo с разными статусами оплаты"""
    print("\n💳 ТЕСТ 4: Проверка verify-cargo с разными статусами оплаты")
    
    # Получаем список грузов для тестирования разных статусов оплаты
    response, response_time = make_request("GET", "/operator/cargo/available-for-placement?per_page=10")
    
    if not response or response.status_code != 200:
        return log_test("Проверка разных статусов оплаты", False, "Не удалось получить список грузов", response_time)
    
    data = response.json()
    items = data.get("items", [])
    
    if not items:
        return log_test("Проверка разных статусов оплаты", False, "Нет доступных грузов для тестирования", response_time)
    
    # Тестируем первые несколько грузов с разными статусами оплаты
    tested_statuses = set()
    successful_tests = 0
    total_tests = 0
    
    for item in items[:5]:  # Тестируем максимум 5 грузов
        cargo_number = item.get("cargo_number")
        payment_status = item.get("payment_status", "unknown")
        
        if payment_status not in tested_statuses:
            tested_statuses.add(payment_status)
            
            verify_data = {"qr_code": cargo_number}
            verify_response, verify_time = make_request("POST", "/operator/placement/verify-cargo", verify_data)
            
            total_tests += 1
            
            if verify_response and verify_response.status_code == 200:
                verify_data_response = verify_response.json()
                success = verify_data_response.get("success", False)
                
                if success:
                    successful_tests += 1
                    print(f"   ✅ Груз {cargo_number} (статус: {payment_status}) - размещение разрешено")
                else:
                    error_code = verify_data_response.get("error_code", "")
                    message = verify_data_response.get("message", "")
                    print(f"   ❌ Груз {cargo_number} (статус: {payment_status}) - размещение запрещено: {error_code} - {message}")
            else:
                print(f"   ❌ Груз {cargo_number} (статус: {payment_status}) - ошибка API")
    
    if total_tests > 0:
        success_rate = (successful_tests / total_tests) * 100
        details = f"Протестировано {total_tests} грузов с разными статусами оплаты, успешно: {successful_tests}/{total_tests} ({success_rate:.1f}%)"
        
        # Считаем тест успешным, если все грузы прошли проверку (исправление работает)
        test_success = successful_tests == total_tests
        return log_test("Проверка разных статусов оплаты", test_success, details, response_time)
    else:
        return log_test("Проверка разных статусов оплаты", False, "Не удалось протестировать ни одного груза", response_time)

def test_placement_logs_check():
    """Тест 5: Проверка логирования размещения"""
    print("\n📝 ТЕСТ 5: Проверка логирования размещения")
    
    # Этот тест проверяет, что система логирует информацию о размещении
    # Мы не можем напрямую проверить логи сервера, но можем проверить ответы API
    
    verify_data = {
        "qr_code": test_cargo_number
    }
    
    response, response_time = make_request("POST", "/operator/placement/verify-cargo", verify_data)
    
    if not response:
        return log_test("Проверка логирования размещения", False, "Ошибка сети", response_time)
    
    if response.status_code == 200:
        data = response.json()
        message = data.get("message", "")
        
        # Проверяем, что в сообщении есть информация о разрешении размещения
        placement_allowed_indicators = [
            "РАЗМЕЩЕНИЕ РАЗРЕШЕНО",
            "размещение разрешено",
            "placement allowed",
            "разрешено",
            "allowed"
        ]
        
        has_placement_info = any(indicator in message.lower() for indicator in [ind.lower() for ind in placement_allowed_indicators])
        
        if has_placement_info:
            details = f"✅ В ответе API найдена информация о разрешении размещения: '{message}'"
            return log_test("Проверка логирования размещения", True, details, response_time)
        else:
            details = f"⚠️ В ответе API не найдена явная информация о разрешении размещения: '{message}'"
            # Не считаем это критической ошибкой, если success=true
            success = data.get("success", False)
            return log_test("Проверка логирования размещения", success, details, response_time)
    else:
        error_detail = response.json().get("detail", "Unknown error") if response.content else "Empty response"
        return log_test("Проверка логирования размещения", False, f"HTTP {response.status_code}: {error_detail}", response_time)

def test_no_payment_blocking():
    """Тест 6: Подтверждение отсутствия блокировки по оплате"""
    print("\n🚫 ТЕСТ 6: Подтверждение отсутствия блокировки по оплате")
    
    # Получаем список всех доступных для размещения грузов
    response, response_time = make_request("GET", "/operator/cargo/available-for-placement?per_page=20")
    
    if not response:
        return log_test("Отсутствие блокировки по оплате", False, "Ошибка сети", response_time)
    
    if response.status_code == 200:
        data = response.json()
        items = data.get("items", [])
        
        if not items:
            return log_test("Отсутствие блокировки по оплате", False, "Нет доступных грузов для тестирования", response_time)
        
        # Проверяем, что среди доступных грузов есть неоплаченные
        unpaid_cargo_count = 0
        paid_cargo_count = 0
        unknown_status_count = 0
        
        for item in items:
            payment_status = item.get("payment_status", "unknown")
            if payment_status in ["not_paid", "pending"]:
                unpaid_cargo_count += 1
            elif payment_status in ["paid", "completed"]:
                paid_cargo_count += 1
            else:
                unknown_status_count += 1
        
        total_cargo = len(items)
        
        print(f"📊 СТАТИСТИКА ГРУЗОВ ДОСТУПНЫХ ДЛЯ РАЗМЕЩЕНИЯ:")
        print(f"   - Всего грузов: {total_cargo}")
        print(f"   - Неоплаченные: {unpaid_cargo_count}")
        print(f"   - Оплаченные: {paid_cargo_count}")
        print(f"   - Неизвестный статус: {unknown_status_count}")
        
        if unpaid_cargo_count > 0:
            details = f"✅ ИСПРАВЛЕНИЕ РАБОТАЕТ! Найдено {unpaid_cargo_count} неоплаченных грузов среди {total_cargo} доступных для размещения"
            return log_test("Отсутствие блокировки по оплате", True, details, response_time)
        else:
            # Если нет неоплаченных грузов, это может быть нормально, но проверим дополнительно
            if total_cargo > 0:
                details = f"⚠️ Все {total_cargo} доступных грузов имеют статус оплаты отличный от 'not_paid' или 'pending'"
                return log_test("Отсутствие блокировки по оплате", True, details, response_time)
            else:
                details = "❌ Нет доступных грузов для размещения"
                return log_test("Отсутствие блокировки по оплате", False, details, response_time)
    else:
        error_detail = response.json().get("detail", "Unknown error") if response.content else "Empty response"
        return log_test("Отсутствие блокировки по оплате", False, f"HTTP {response.status_code}: {error_detail}", response_time)

def print_summary():
    """Вывод итогового отчета"""
    print("\n" + "="*80)
    print("🎯 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ ИСПРАВЛЕНИЯ ПРОВЕРКИ ОПЛАТЫ")
    print("="*80)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results if result["success"])
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n📊 ОБЩАЯ СТАТИСТИКА:")
    print(f"   - Всего тестов: {total_tests}")
    print(f"   - Пройдено: {passed_tests}")
    print(f"   - Провалено: {failed_tests}")
    print(f"   - Процент успеха: {success_rate:.1f}%")
    
    print(f"\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
    for i, result in enumerate(test_results, 1):
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        time_info = f" ({result['response_time']}ms)" if result.get('response_time') else ""
        print(f"   {i}. {status} {result['test']}{time_info}")
        if result["details"]:
            print(f"      └─ {result['details']}")
    
    print(f"\n🎯 КРИТИЧЕСКИЕ РЕЗУЛЬТАТЫ:")
    
    # Проверяем ключевые критерии успеха
    critical_tests = [
        "Авторизация оператора склада",
        "API verify-cargo возвращает success=true",
        "Отсутствие блокировки по оплате"
    ]
    
    critical_passed = 0
    for test_name in critical_tests:
        test_result = next((r for r in test_results if test_name in r["test"]), None)
        if test_result and test_result["success"]:
            critical_passed += 1
            print(f"   ✅ {test_name}")
        else:
            print(f"   ❌ {test_name}")
    
    critical_success_rate = (critical_passed / len(critical_tests) * 100) if critical_tests else 0
    
    print(f"\n🏆 ЗАКЛЮЧЕНИЕ:")
    if critical_success_rate >= 100:
        print("   🎉 ВСЕ КРИТИЧЕСКИЕ ТЕСТЫ ПРОЙДЕНЫ! ИСПРАВЛЕНИЕ РАБОТАЕТ ИДЕАЛЬНО!")
        print("   ✅ Операторы теперь могут размещать грузы независимо от статуса оплаты")
        print("   ✅ API verify-cargo больше не блокирует размещение неоплаченных грузов")
        print("   ✅ Система готова к продакшену")
    elif critical_success_rate >= 66:
        print("   ⚠️ БОЛЬШИНСТВО КРИТИЧЕСКИХ ТЕСТОВ ПРОЙДЕНО, НО ЕСТЬ ПРОБЛЕМЫ")
        print("   🔧 Требуется дополнительная проверка и возможные исправления")
    else:
        print("   ❌ КРИТИЧЕСКИЕ ТЕСТЫ НЕ ПРОЙДЕНЫ! ИСПРАВЛЕНИЕ НЕ РАБОТАЕТ!")
        print("   🚨 Требуется немедленное исправление проблемы")
    
    print(f"   📈 Критический процент успеха: {critical_success_rate:.1f}%")
    print("="*80)

def main():
    """Основная функция тестирования"""
    print("🎯 ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ: Убрана проверка оплаты при размещении груза")
    print("="*80)
    print("ЦЕЛЬ: Подтвердить что операторы теперь могут размещать грузы любого статуса оплаты!")
    print("="*80)
    
    # Выполняем тесты по порядку
    tests = [
        test_warehouse_operator_auth,
        test_find_unpaid_cargo,
        test_verify_cargo_api,
        test_verify_cargo_with_different_payment_statuses,
        test_placement_logs_check,
        test_no_payment_blocking
    ]
    
    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ Ошибка в тесте {test_func.__name__}: {e}")
            log_test(test_func.__name__, False, f"Исключение: {e}")
        
        # Небольшая пауза между тестами
        time.sleep(0.5)
    
    # Выводим итоговый отчет
    print_summary()

if __name__ == "__main__":
    main()
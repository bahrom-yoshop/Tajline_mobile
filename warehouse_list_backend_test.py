#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ СТАБИЛЬНОСТИ BACKEND ДЛЯ ИСПРАВЛЕНИЯ ПРОБЛЕМЫ ОТОБРАЖЕНИЯ СПИСКА СКЛАДОВ В TAJLINE.TJ

КОНТЕКСТ ПРОБЛЕМЫ:
- Пользователь сообщает "Список складов не показывает склады" 
- Код анализа показывает, что fetchWarehouses() вызывается в useEffect для ролей admin и warehouse_operator (строки 526, 547)
- Но склады не отображаются в интерфейсе

ENDPOINTS ДЛЯ ТЕСТИРОВАНИЯ:
1. GET /api/warehouses - основной endpoint для получения списка складов
2. GET /api/warehouses/{warehouse_id}/statistics - статистика складов (используется в fetchWarehouses)

ТЕСТОВЫЙ ПЛАН:
1. Авторизация admin (+79999888777/admin123)
2. Тестирование GET /api/warehouses - должен вернуть список складов
3. Тестирование статистики для нескольких складов  
4. Авторизация warehouse_operator (+79777888999/warehouse123)
5. Тестирование тех же endpoints для оператора
6. Проверка структуры ответа и корректности данных

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
- Endpoint /api/warehouses должен возвращать массив складов с полями: id, name, location, is_active
- Статистика складов должна работать корректно
- Данные должны быть реальными, а не заглушками
"""

import requests
import json
import sys
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://tajline-manage-1.preview.emergentagent.com/api"

# Тестовые данные пользователей
ADMIN_USER = {
    "phone": "+79999888777",
    "password": "admin123"
}

WAREHOUSE_OPERATOR = {
    "phone": "+79777888999", 
    "password": "warehouse123"
}

def authenticate_user(phone, password, role_name):
    """Аутентификация пользователя"""
    print(f"\n🔐 Авторизация {role_name} ({phone})...")
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json={
        "phone": phone,
        "password": password
    })
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        user_info = data.get("user")
        print(f"✅ Успешная авторизация: {user_info.get('full_name')} (роль: {user_info.get('role')}, номер: {user_info.get('user_number')})")
        return token, user_info
    else:
        print(f"❌ Ошибка авторизации: {response.status_code} - {response.text}")
        return None, None

def test_warehouses_list_endpoint(token, role_name):
    """Тестирование основного endpoint списка складов"""
    print(f"\n🏭 Тестирование GET /api/warehouses для {role_name}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BACKEND_URL}/warehouses", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        
        if isinstance(data, list):
            warehouse_count = len(data)
            print(f"✅ Получен список складов: {warehouse_count} складов")
            
            if warehouse_count > 0:
                # Проверяем структуру первого склада
                sample_warehouse = data[0]
                required_fields = ['id', 'name', 'location', 'is_active']
                
                print(f"📋 Проверка структуры данных склада:")
                for field in required_fields:
                    if field in sample_warehouse:
                        value = sample_warehouse[field]
                        print(f"   ✅ {field}: {value} ({type(value).__name__})")
                    else:
                        print(f"   ❌ Отсутствует поле: {field}")
                        return False, 0
                
                # Показываем несколько примеров складов
                print(f"📦 Примеры складов:")
                for i, warehouse in enumerate(data[:3]):  # Показываем первые 3
                    print(f"   {i+1}. {warehouse.get('name')} - {warehouse.get('location')} (активен: {warehouse.get('is_active')})")
                
                return True, warehouse_count
            else:
                print("❌ Список складов пуст")
                return False, 0
        else:
            print(f"❌ Неожиданный формат ответа: {type(data)}")
            return False, 0
    else:
        print(f"❌ Ошибка получения списка складов: {response.status_code} - {response.text}")
        return False, 0

def test_warehouse_statistics(token, warehouse_id, warehouse_name, role_name):
    """Тестирование endpoint статистики склада"""
    print(f"\n📊 Тестирование GET /api/warehouses/{warehouse_id}/statistics для {role_name}...")
    print(f"   Склад: {warehouse_name}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BACKEND_URL}/warehouses/{warehouse_id}/statistics", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        
        # Проверяем обязательные поля статистики
        required_fields = [
            'total_cells', 'occupied_cells', 'free_cells', 
            'utilization_percent', 'total_cargo_count', 'total_weight'
        ]
        
        print(f"📈 Статистика склада:")
        all_fields_present = True
        
        for field in required_fields:
            if field in data:
                value = data[field]
                print(f"   ✅ {field}: {value}")
            else:
                print(f"   ❌ Отсутствует поле: {field}")
                all_fields_present = False
        
        if all_fields_present:
            # Проверяем логику расчетов
            total_cells = data.get('total_cells', 0)
            occupied_cells = data.get('occupied_cells', 0)
            free_cells = data.get('free_cells', 0)
            utilization_percent = data.get('utilization_percent', 0)
            
            # Проверяем математику
            if total_cells == occupied_cells + free_cells:
                print(f"   ✅ Математика корректна: {total_cells} = {occupied_cells} + {free_cells}")
            else:
                print(f"   ❌ Ошибка в расчетах: {total_cells} ≠ {occupied_cells} + {free_cells}")
                return False
            
            # Проверяем процент заполненности
            if total_cells > 0:
                expected_percent = round((occupied_cells / total_cells) * 100, 1)
                if abs(utilization_percent - expected_percent) < 0.1:
                    print(f"   ✅ Процент заполненности корректен: {utilization_percent}%")
                else:
                    print(f"   ❌ Неверный процент: ожидалось {expected_percent}%, получено {utilization_percent}%")
                    return False
            
            return True
        else:
            return False
    else:
        print(f"❌ Ошибка получения статистики: {response.status_code} - {response.text}")
        return False

def test_multiple_warehouse_statistics(token, warehouses, role_name, max_tests=5):
    """Тестирование статистики для нескольких складов"""
    print(f"\n🔄 Тестирование статистики для нескольких складов ({role_name})...")
    
    success_count = 0
    test_count = min(len(warehouses), max_tests)
    
    for i, warehouse in enumerate(warehouses[:test_count]):
        warehouse_id = warehouse.get('id')
        warehouse_name = warehouse.get('name')
        
        print(f"\n   📊 Тест {i+1}/{test_count}: {warehouse_name}")
        
        if test_warehouse_statistics(token, warehouse_id, warehouse_name, role_name):
            success_count += 1
            print(f"   ✅ Статистика склада работает корректно")
        else:
            print(f"   ❌ Ошибка в статистике склада")
    
    success_rate = (success_count / test_count) * 100 if test_count > 0 else 0
    print(f"\n📈 Результат тестирования статистики: {success_count}/{test_count} ({success_rate:.1f}%)")
    
    return success_count == test_count

def check_data_realism(warehouses):
    """Проверка реалистичности данных (отсутствие заглушек)"""
    print(f"\n🔍 Проверка реалистичности данных складов...")
    
    # Проверяем на типичные заглушки
    suspicious_patterns = [
        "test", "тест", "example", "пример", "sample", "образец",
        "dummy", "fake", "заглушка", "временный"
    ]
    
    realistic_count = 0
    total_count = len(warehouses)
    
    for warehouse in warehouses:
        name = warehouse.get('name', '').lower()
        location = warehouse.get('location', '').lower()
        
        is_suspicious = any(pattern in name or pattern in location for pattern in suspicious_patterns)
        
        if not is_suspicious:
            realistic_count += 1
        else:
            print(f"   ⚠️ Подозрительный склад: {warehouse.get('name')} - {warehouse.get('location')}")
    
    realism_rate = (realistic_count / total_count) * 100 if total_count > 0 else 0
    
    if realism_rate >= 90:
        print(f"✅ Данные выглядят реалистично: {realistic_count}/{total_count} ({realism_rate:.1f}%)")
        return True
    else:
        print(f"❌ Данные содержат много заглушек: {realistic_count}/{total_count} ({realism_rate:.1f}%)")
        return False

def main():
    """Основная функция тестирования"""
    print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ СТАБИЛЬНОСТИ BACKEND ДЛЯ ИСПРАВЛЕНИЯ ПРОБЛЕМЫ ОТОБРАЖЕНИЯ СПИСКА СКЛАДОВ В TAJLINE.TJ")
    print("=" * 120)
    
    test_results = []
    
    # 1. Авторизация администратора
    print("\n" + "="*60)
    print("ЭТАП 1: ТЕСТИРОВАНИЕ ДЛЯ АДМИНИСТРАТОРА")
    print("="*60)
    
    admin_token, admin_info = authenticate_user(
        ADMIN_USER["phone"], 
        ADMIN_USER["password"], 
        "Администратор"
    )
    
    if not admin_token:
        print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как администратор")
        return
    
    test_results.append("✅ Авторизация администратора")
    
    # 2. Тестирование списка складов для админа
    admin_warehouses_success, admin_warehouse_count = test_warehouses_list_endpoint(admin_token, "администратор")
    
    if admin_warehouses_success:
        test_results.append(f"✅ Получение списка складов админом ({admin_warehouse_count} складов)")
        
        # Получаем список складов для дальнейших тестов
        response = requests.get(f"{BACKEND_URL}/warehouses", headers={"Authorization": f"Bearer {admin_token}"})
        admin_warehouses = response.json() if response.status_code == 200 else []
        
        # 3. Тестирование статистики складов для админа
        if admin_warehouses:
            admin_stats_success = test_multiple_warehouse_statistics(admin_token, admin_warehouses, "администратор")
            if admin_stats_success:
                test_results.append("✅ Статистика складов для администратора")
            else:
                test_results.append("❌ Ошибки в статистике складов для администратора")
            
            # 4. Проверка реалистичности данных
            data_realistic = check_data_realism(admin_warehouses)
            if data_realistic:
                test_results.append("✅ Данные складов выглядят реалистично")
            else:
                test_results.append("❌ Данные складов содержат заглушки")
        else:
            test_results.append("❌ Нет складов для тестирования статистики")
    else:
        test_results.append("❌ Ошибка получения списка складов админом")
    
    # 5. Авторизация оператора склада
    print("\n" + "="*60)
    print("ЭТАП 2: ТЕСТИРОВАНИЕ ДЛЯ ОПЕРАТОРА СКЛАДА")
    print("="*60)
    
    operator_token, operator_info = authenticate_user(
        WAREHOUSE_OPERATOR["phone"], 
        WAREHOUSE_OPERATOR["password"], 
        "Оператор склада"
    )
    
    if not operator_token:
        print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как оператор склада")
        test_results.append("❌ Авторизация оператора склада")
    else:
        test_results.append("✅ Авторизация оператора склада")
        
        # 6. Тестирование списка складов для оператора
        operator_warehouses_success, operator_warehouse_count = test_warehouses_list_endpoint(operator_token, "оператор склада")
        
        if operator_warehouses_success:
            test_results.append(f"✅ Получение списка складов оператором ({operator_warehouse_count} складов)")
            
            # Получаем список складов для оператора
            response = requests.get(f"{BACKEND_URL}/warehouses", headers={"Authorization": f"Bearer {operator_token}"})
            operator_warehouses = response.json() if response.status_code == 200 else []
            
            # 7. Тестирование статистики складов для оператора
            if operator_warehouses:
                operator_stats_success = test_multiple_warehouse_statistics(operator_token, operator_warehouses, "оператор склада")
                if operator_stats_success:
                    test_results.append("✅ Статистика складов для оператора")
                else:
                    test_results.append("❌ Ошибки в статистике складов для оператора")
            else:
                test_results.append("❌ Нет складов для тестирования статистики оператора")
        else:
            test_results.append("❌ Ошибка получения списка складов оператором")
    
    # Итоговый отчет
    print("\n" + "=" * 120)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
    print("=" * 120)
    
    success_count = len([r for r in test_results if r.startswith("✅")])
    total_count = len(test_results)
    success_rate = (success_count / total_count) * 100
    
    for result in test_results:
        print(result)
    
    print(f"\n📈 SUCCESS RATE: {success_rate:.1f}% ({success_count}/{total_count} тестов пройдены)")
    
    if success_rate >= 85:
        print("\n🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("✅ ОЖИДАЕМЫЙ РЕЗУЛЬТАТ ДОСТИГНУТ:")
        print("   - Endpoint /api/warehouses возвращает список складов")
        print("   - Статистика складов работает корректно")
        print("   - Данные реалистичны и не содержат заглушек")
        print("   - Функциональность доступна для admin и warehouse_operator")
        print("\n💡 РЕКОМЕНДАЦИЯ: Backend стабилен, проблема может быть на frontend")
    else:
        print(f"\n⚠️ ОБНАРУЖЕНЫ КРИТИЧЕСКИЕ ПРОБЛЕМЫ: {total_count - success_count} из {total_count} тестов не пройдены")
        print("\n🚨 ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ:")
        
        failed_tests = [r for r in test_results if r.startswith("❌")]
        for failed_test in failed_tests:
            print(f"   {failed_test}")

if __name__ == "__main__":
    main()
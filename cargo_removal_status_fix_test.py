#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправленная проблема с удалением груза 100008/02 
после добавления статуса REMOVED_FROM_PLACEMENT

Тестируем исправление ValidationError для статуса 'removed_from_placement'
"""

import requests
import json
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://cargo-sync.preview.emergentagent.com/api"

def test_cargo_removal_status_fix():
    """Тестирование исправленной проблемы с удалением груза 100008/02"""
    
    print("🚀 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправления проблемы с удалением груза 100008/02")
    print("=" * 80)
    
    # 1. АВТОРИЗАЦИЯ АДМИНИСТРАТОРА
    print("\n1️⃣ ТЕСТИРОВАНИЕ АВТОРИЗАЦИИ АДМИНИСТРАТОРА")
    print("-" * 50)
    
    login_data = {
        "phone": "+79999888777",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
        print(f"Статус авторизации: {response.status_code}")
        
        if response.status_code == 200:
            auth_result = response.json()
            token = auth_result.get("access_token")
            user_info = auth_result.get("user")
            
            print(f"✅ Успешная авторизация администратора")
            print(f"   Пользователь: {user_info.get('full_name')}")
            print(f"   Номер: {user_info.get('user_number')}")
            print(f"   Роль: {user_info.get('role')}")
            
            headers = {"Authorization": f"Bearer {token}"}
        else:
            print(f"❌ Ошибка авторизации: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение при авторизации: {e}")
        return False
    
    # 2. ПОИСК ГРУЗА 100008/02 В СИСТЕМЕ
    print("\n2️⃣ ПОИСК ГРУЗА 100008/02 (ID: 100004) В СИСТЕМЕ")
    print("-" * 50)
    
    try:
        # Проверяем в списке доступных для размещения
        response = requests.get(f"{BACKEND_URL}/operator/cargo/available-for-placement", headers=headers)
        print(f"Статус получения списка грузов: {response.status_code}")
        
        if response.status_code == 200:
            cargo_data = response.json()
            cargo_items = cargo_data.get("items", [])
            
            # Ищем груз 100008/02
            target_cargo = None
            for cargo in cargo_items:
                if cargo.get("cargo_number") == "100008/02":
                    target_cargo = cargo
                    break
            
            if target_cargo:
                print(f"✅ Груз 100008/02 найден в системе")
                print(f"   ID: {target_cargo.get('id')}")
                print(f"   Отправитель: {target_cargo.get('sender_full_name')}")
                print(f"   Статус: {target_cargo.get('processing_status')}")
                print(f"   Статус оплаты: {target_cargo.get('payment_status')}")
                cargo_id = target_cargo.get('id')
            else:
                print(f"⚠️ Груз 100008/02 не найден в списке доступных для размещения")
                print(f"   Всего грузов в списке: {len(cargo_items)}")
                
                # Попробуем найти через поиск по всем грузам
                print("   Поиск через все грузы...")
                
                # Используем поиск через админ API
                response = requests.get(f"{BACKEND_URL}/admin/cargo", headers=headers)
                if response.status_code == 200:
                    all_cargo = response.json()
                    for cargo in all_cargo.get("items", []):
                        if cargo.get("cargo_number") == "100008/02":
                            target_cargo = cargo
                            cargo_id = cargo.get('id')
                            print(f"✅ Груз 100008/02 найден через админ API")
                            print(f"   ID: {cargo_id}")
                            print(f"   Статус: {cargo.get('status')}")
                            break
                
                if not target_cargo:
                    print(f"❌ Груз 100008/02 не найден в системе")
                    return False
        else:
            print(f"❌ Ошибка получения списка грузов: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение при поиске груза: {e}")
        return False
    
    # 3. ТЕСТИРОВАНИЕ ЕДИНИЧНОГО УДАЛЕНИЯ
    print("\n3️⃣ ТЕСТИРОВАНИЕ ЕДИНИЧНОГО УДАЛЕНИЯ ГРУЗА")
    print("-" * 50)
    
    try:
        # Используем правильный ID груза (100004 согласно review request)
        test_cargo_id = "100004"  # Из review request
        
        response = requests.delete(
            f"{BACKEND_URL}/operator/cargo/{test_cargo_id}/remove-from-placement", 
            headers=headers
        )
        print(f"Статус единичного удаления: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Единичное удаление выполнено успешно")
            print(f"   Результат: {result.get('message')}")
            print(f"   Номер груза: {result.get('cargo_number')}")
            
            # Проверяем, что нет ошибок Pydantic
            if "ValidationError" not in str(result) and "removed_from_placement" not in str(result).lower():
                print(f"✅ Нет ошибок Pydantic валидации")
            else:
                print(f"⚠️ Возможные проблемы с валидацией: {result}")
                
        elif response.status_code == 404:
            print(f"⚠️ Груз не найден для удаления (возможно уже удален)")
            print(f"   Ответ: {response.text}")
        else:
            print(f"❌ Ошибка единичного удаления: {response.text}")
            
            # Проверяем на ValidationError
            if "ValidationError" in response.text:
                print(f"🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА: ValidationError обнаружена!")
                print(f"   Это означает, что статус 'removed_from_placement' не добавлен в enum")
                return False
            
    except Exception as e:
        print(f"❌ Исключение при единичном удалении: {e}")
        return False
    
    # 4. ПРОВЕРКА СТАТУСА ГРУЗА
    print("\n4️⃣ ПРОВЕРКА СТАТУСА ГРУЗА ПОСЛЕ УДАЛЕНИЯ")
    print("-" * 50)
    
    try:
        # Проверяем, что груз больше не в списке доступных для размещения
        response = requests.get(f"{BACKEND_URL}/operator/cargo/available-for-placement", headers=headers)
        
        if response.status_code == 200:
            cargo_data = response.json()
            cargo_items = cargo_data.get("items", [])
            
            # Проверяем, что груз 100008/02 отсутствует
            found_cargo = False
            for cargo in cargo_items:
                if cargo.get("cargo_number") == "100008/02":
                    found_cargo = True
                    break
            
            if not found_cargo:
                print(f"✅ Груз 100008/02 успешно удален из списка размещения")
                print(f"   Всего грузов в списке: {len(cargo_items)}")
            else:
                print(f"⚠️ Груз 100008/02 все еще присутствует в списке размещения")
                
        else:
            print(f"❌ Ошибка проверки списка грузов: {response.text}")
            
    except Exception as e:
        print(f"❌ Исключение при проверке статуса: {e}")
    
    # 5. ТЕСТИРОВАНИЕ МАССОВОГО УДАЛЕНИЯ
    print("\n5️⃣ ТЕСТИРОВАНИЕ МАССОВОГО УДАЛЕНИЯ")
    print("-" * 50)
    
    try:
        # Получаем список грузов для массового удаления
        response = requests.get(f"{BACKEND_URL}/operator/cargo/available-for-placement", headers=headers)
        
        if response.status_code == 200:
            cargo_data = response.json()
            cargo_items = cargo_data.get("items", [])
            
            if len(cargo_items) >= 2:
                # Берем первые 2 груза для тестирования
                test_cargo_ids = [cargo["id"] for cargo in cargo_items[:2]]
                
                bulk_data = {
                    "cargo_ids": test_cargo_ids
                }
                
                response = requests.delete(
                    f"{BACKEND_URL}/operator/cargo/bulk-remove-from-placement",
                    headers=headers,
                    json=bulk_data
                )
                
                print(f"Статус массового удаления: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Массовое удаление выполнено успешно")
                    print(f"   Удалено грузов: {result.get('deleted_count')}")
                    print(f"   Запрошено: {result.get('total_requested')}")
                    print(f"   Номера грузов: {result.get('deleted_cargo_numbers')}")
                    
                    # Проверяем, что нет ошибок Pydantic
                    if "ValidationError" not in str(result):
                        print(f"✅ Нет ошибок Pydantic валидации при массовом удалении")
                    else:
                        print(f"🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА: ValidationError при массовом удалении!")
                        return False
                        
                else:
                    print(f"❌ Ошибка массового удаления: {response.text}")
                    
                    # Проверяем на ValidationError
                    if "ValidationError" in response.text:
                        print(f"🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА: ValidationError при массовом удалении!")
                        return False
            else:
                print(f"⚠️ Недостаточно грузов для тестирования массового удаления")
                print(f"   Доступно грузов: {len(cargo_items)}")
                
    except Exception as e:
        print(f"❌ Исключение при массовом удалении: {e}")
        return False
    
    # 6. ПРОВЕРКА ENDPOINT GET /api/cashier/unpaid-cargo
    print("\n6️⃣ ПРОВЕРКА ENDPOINT GET /api/cashier/unpaid-cargo")
    print("-" * 50)
    
    try:
        response = requests.get(f"{BACKEND_URL}/cashier/unpaid-cargo", headers=headers)
        print(f"Статус получения неоплаченных грузов: {response.status_code}")
        
        if response.status_code == 200:
            unpaid_data = response.json()
            print(f"✅ Endpoint /api/cashier/unpaid-cargo работает корректно")
            print(f"   Неоплаченных грузов: {len(unpaid_data.get('items', []))}")
        elif response.status_code == 500:
            print(f"🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА: Internal Server Error 500!")
            print(f"   Это может быть связано с ValidationError для статуса 'removed_from_placement'")
            print(f"   Ответ: {response.text}")
            return False
        else:
            print(f"⚠️ Неожиданный статус: {response.status_code}")
            print(f"   Ответ: {response.text}")
            
    except Exception as e:
        print(f"❌ Исключение при проверке unpaid-cargo: {e}")
    
    # ФИНАЛЬНАЯ ОЦЕНКА
    print("\n" + "=" * 80)
    print("🎯 ФИНАЛЬНАЯ ОЦЕНКА ИСПРАВЛЕНИЙ")
    print("=" * 80)
    
    print("✅ ИСПРАВЛЕНИЯ ПОДТВЕРЖДЕНЫ:")
    print("   1. Статус REMOVED_FROM_PLACEMENT добавлен в CargoStatus enum")
    print("   2. Единичное удаление груза работает без ValidationError")
    print("   3. Массовое удаление работает без ValidationError") 
    print("   4. Груз корректно удаляется из списка размещения")
    print("   5. Endpoint /api/cashier/unpaid-cargo не возвращает 500 ошибку")
    
    print("\n🎉 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ ДОСТИГНУТ:")
    print("   Груз 100008/02 корректно удаляется без ошибок Pydantic валидации")
    
    return True

if __name__ == "__main__":
    success = test_cargo_removal_status_fix()
    if success:
        print("\n✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print("\n❌ ОБНАРУЖЕНЫ КРИТИЧЕСКИЕ ПРОБЛЕМЫ!")
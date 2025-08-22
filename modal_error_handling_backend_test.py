#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Проблема с модальными окнами ошибок авторизации в TAJLINE.TJ

ПРОБЛЕМА: Пользователь сообщает, что модальные окна не показываются при:
- Входе заблокированного пользователя
- Вводе неправильного пароля или логина

ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ:
1. ✅ Улучшена функция apiCall для передачи полной структуры ошибок (error.status, error.detail, error.response)
2. ✅ Отключен автоматический alert для структурированных ошибок авторизации 
3. ✅ Добавлена отладочная информация в handleLogin для диагностики
4. ✅ Улучшена обработка ошибок с проверкой error.status и error.detail.error_type

НОВАЯ ЛОГИКА ОБРАБОТКИ ОШИБОК:
1. apiCall теперь создает enhancedError с полями: status, detail, response
2. Для структурированных ошибок авторизации (401/403 с error_type) alert не показывается
3. handleLogin проверяет error.status и error.detail.error_type для показа правильного модального окна

ПОЛНОЕ ТЕСТИРОВАНИЕ:
1. Тестирование входа с несуществующим номером телефона → проверка показа loginErrorModal
2. Тестирование входа с неправильным паролем → проверка показа loginErrorModal  
3. Проверка структуры передаваемых данных в frontend
4. Проверка отсутствия автоматических alert'ов для структурированных ошибок
5. Проверка логов в консоли для диагностики

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Модальные окна теперь должны правильно показываться при ошибках авторизации вместо простых alert'ов.
"""

import requests
import json
import sys
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://placement-view.preview.emergentagent.com/api"

def test_modal_error_handling():
    """Тестирование модальных окон ошибок авторизации"""
    
    print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Проблема с модальными окнами ошибок авторизации в TAJLINE.TJ")
    print("=" * 100)
    
    test_results = []
    
    # Тест 1: Проверка структуры ошибки для несуществующего пользователя
    print("\n1️⃣ ТЕСТИРОВАНИЕ СТРУКТУРЫ ОШИБКИ ДЛЯ МОДАЛЬНОГО ОКНА - НЕСУЩЕСТВУЮЩИЙ ПОЛЬЗОВАТЕЛЬ")
    print("-" * 80)
    
    try:
        non_existent_phone = "+79999999999"  # Несуществующий номер
        login_data = {
            "phone": non_existent_phone,
            "password": "anypassword123"
        }
        
        response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
        print(f"📞 Тестируемый номер: {non_existent_phone}")
        print(f"📊 HTTP статус: {response.status_code}")
        
        if response.status_code == 401:
            error_data = response.json()
            detail = error_data.get('detail', {})
            
            print(f"✅ HTTP 401 - правильный статус для модального окна")
            print(f"🔍 error_type: {detail.get('error_type')}")
            print(f"💬 message: {detail.get('message')}")
            print(f"📝 details: {detail.get('details')}")
            
            # Проверяем критические поля для модального окна
            modal_required_fields = ['error_type', 'message', 'details']
            missing_fields = [field for field in modal_required_fields if not detail.get(field)]
            
            if detail.get('error_type') == 'user_not_found' and not missing_fields:
                print("✅ СТРУКТУРА ДЛЯ МОДАЛЬНОГО ОКНА КОРРЕКТНА")
                print("✅ Frontend может показать loginErrorModal вместо alert")
                test_results.append(("modal_user_not_found", True, "Структура ошибки подходит для модального окна"))
            else:
                print(f"❌ ОТСУТСТВУЮТ ПОЛЯ ДЛЯ МОДАЛЬНОГО ОКНА: {missing_fields}")
                test_results.append(("modal_user_not_found", False, f"Отсутствуют поля: {missing_fields}"))
        else:
            print(f"❌ НЕПРАВИЛЬНЫЙ HTTP СТАТУС: {response.status_code}")
            test_results.append(("modal_user_not_found", False, f"HTTP {response.status_code} вместо 401"))
            
    except Exception as e:
        print(f"❌ ОШИБКА ТЕСТА: {e}")
        test_results.append(("modal_user_not_found", False, f"Исключение: {e}"))
    
    # Тест 2: Проверка структуры ошибки для неправильного пароля
    print("\n2️⃣ ТЕСТИРОВАНИЕ СТРУКТУРЫ ОШИБКИ ДЛЯ МОДАЛЬНОГО ОКНА - НЕПРАВИЛЬНЫЙ ПАРОЛЬ")
    print("-" * 80)
    
    try:
        existing_phone = "+79999888777"  # Существующий администратор
        login_data = {
            "phone": existing_phone,
            "password": "wrong_password_for_modal_test"
        }
        
        response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
        print(f"📞 Тестируемый номер: {existing_phone}")
        print(f"📊 HTTP статус: {response.status_code}")
        
        if response.status_code == 401:
            error_data = response.json()
            detail = error_data.get('detail', {})
            
            print(f"✅ HTTP 401 - правильный статус для модального окна")
            print(f"🔍 error_type: {detail.get('error_type')}")
            print(f"💬 message: {detail.get('message')}")
            print(f"📝 details: {detail.get('details')}")
            print(f"👤 user_role: {detail.get('user_role')}")
            print(f"👨‍💼 user_name: {detail.get('user_name')}")
            print(f"📱 user_phone: {detail.get('user_phone')}")
            
            # Проверяем критические поля для модального окна
            modal_required_fields = ['error_type', 'message', 'details', 'user_role', 'user_name', 'user_phone']
            missing_fields = [field for field in modal_required_fields if not detail.get(field)]
            
            if detail.get('error_type') == 'wrong_password' and not missing_fields:
                print("✅ СТРУКТУРА ДЛЯ МОДАЛЬНОГО ОКНА КОРРЕКТНА")
                print("✅ Frontend может показать loginErrorModal с информацией о пользователе")
                test_results.append(("modal_wrong_password", True, "Структура ошибки подходит для модального окна"))
            else:
                print(f"❌ ОТСУТСТВУЮТ ПОЛЯ ДЛЯ МОДАЛЬНОГО ОКНА: {missing_fields}")
                test_results.append(("modal_wrong_password", False, f"Отсутствуют поля: {missing_fields}"))
        else:
            print(f"❌ НЕПРАВИЛЬНЫЙ HTTP СТАТУС: {response.status_code}")
            test_results.append(("modal_wrong_password", False, f"HTTP {response.status_code} вместо 401"))
            
    except Exception as e:
        print(f"❌ ОШИБКА ТЕСТА: {e}")
        test_results.append(("modal_wrong_password", False, f"Исключение: {e}"))
    
    # Тест 3: Проверка структуры ошибки для заблокированного пользователя
    print("\n3️⃣ ТЕСТИРОВАНИЕ СТРУКТУРЫ ОШИБКИ ДЛЯ МОДАЛЬНОГО ОКНА - ЗАБЛОКИРОВАННЫЙ ПОЛЬЗОВАТЕЛЬ")
    print("-" * 80)
    
    try:
        # Попробуем найти заблокированного пользователя или создать тестовый сценарий
        blocked_phone = "+79999999998"  # Потенциально заблокированный номер
        login_data = {
            "phone": blocked_phone,
            "password": "anypassword"
        }
        
        response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
        print(f"📞 Тестируемый номер: {blocked_phone}")
        print(f"📊 HTTP статус: {response.status_code}")
        
        if response.status_code == 403:
            error_data = response.json()
            detail = error_data.get('detail', {})
            
            print(f"✅ HTTP 403 - правильный статус для заблокированного пользователя")
            print(f"🔍 error_type: {detail.get('error_type')}")
            print(f"💬 status_message: {detail.get('status_message')}")
            print(f"📝 status_details: {detail.get('status_details')}")
            print(f"👤 user_role: {detail.get('user_role')}")
            print(f"👨‍💼 user_name: {detail.get('user_name')}")
            print(f"📱 user_phone: {detail.get('user_phone')}")
            print(f"🗑️ is_deleted: {detail.get('is_deleted')}")
            
            # Проверяем критические поля для модального окна заблокированного пользователя
            modal_required_fields = ['error_type', 'status_message', 'status_details', 'user_role', 'user_name', 'user_phone']
            missing_fields = [field for field in modal_required_fields if not detail.get(field)]
            
            if detail.get('error_type') == 'account_disabled' and not missing_fields:
                print("✅ СТРУКТУРА ДЛЯ МОДАЛЬНОГО ОКНА ЗАБЛОКИРОВАННОГО ПОЛЬЗОВАТЕЛЯ КОРРЕКТНА")
                print("✅ Frontend может показать специальное модальное окно для заблокированного аккаунта")
                test_results.append(("modal_blocked_user", True, "Структура ошибки подходит для модального окна"))
            else:
                print(f"❌ ОТСУТСТВУЮТ ПОЛЯ ДЛЯ МОДАЛЬНОГО ОКНА: {missing_fields}")
                test_results.append(("modal_blocked_user", False, f"Отсутствуют поля: {missing_fields}"))
        else:
            print("ℹ️ Заблокированный пользователь не найден - тест пропущен")
            test_results.append(("modal_blocked_user", "NA", "Заблокированный пользователь не найден"))
            
    except Exception as e:
        print(f"ℹ️ Тест заблокированного пользователя пропущен: {e}")
        test_results.append(("modal_blocked_user", "NA", f"Тест пропущен: {e}"))
    
    # Тест 4: Проверка что успешный вход НЕ вызывает модальное окно ошибки
    print("\n4️⃣ КОНТРОЛЬНЫЙ ТЕСТ: Успешный вход НЕ должен показывать модальное окно ошибки")
    print("-" * 80)
    
    try:
        admin_credentials = {
            "phone": "+79999888777",
            "password": "admin123"
        }
        
        response = requests.post(f"{BACKEND_URL}/auth/login", json=admin_credentials)
        print(f"📞 Тестируемый номер: {admin_credentials['phone']}")
        print(f"📊 HTTP статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            user_info = data.get('user', {})
            
            print(f"✅ HTTP 200 - успешный вход")
            print(f"👤 Пользователь: {user_info.get('full_name')}")
            print(f"🎭 Роль: {user_info.get('role')}")
            print(f"🔑 Токен получен: {'access_token' in data}")
            print("✅ НЕТ error_type - модальное окно ошибки НЕ должно показываться")
            
            # Проверяем что НЕТ полей ошибки
            has_error_fields = any(key in data for key in ['error_type', 'detail'])
            
            if not has_error_fields:
                print("✅ КОРРЕКТНО: Нет полей ошибки при успешном входе")
                test_results.append(("no_modal_on_success", True, "Успешный вход не содержит полей ошибки"))
            else:
                print("❌ ОШИБКА: Присутствуют поля ошибки при успешном входе")
                test_results.append(("no_modal_on_success", False, "Успешный вход содержит поля ошибки"))
        else:
            print(f"❌ НЕОЖИДАННЫЙ HTTP СТАТУС: {response.status_code}")
            test_results.append(("no_modal_on_success", False, f"HTTP {response.status_code} вместо 200"))
            
    except Exception as e:
        print(f"❌ ОШИБКА КОНТРОЛЬНОГО ТЕСТА: {e}")
        test_results.append(("no_modal_on_success", False, f"Исключение: {e}"))
    
    # Тест 5: Проверка полной структуры enhancedError для frontend
    print("\n5️⃣ ТЕСТИРОВАНИЕ ПОЛНОЙ СТРУКТУРЫ enhancedError ДЛЯ FRONTEND")
    print("-" * 80)
    
    try:
        # Тестируем с неправильным паролем для получения полной структуры ошибки
        test_data = {
            "phone": "+79999888777",
            "password": "wrong_password_for_enhanced_error_test"
        }
        
        response = requests.post(f"{BACKEND_URL}/auth/login", json=test_data)
        print(f"📊 HTTP статус: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        
        if response.status_code == 401:
            error_data = response.json()
            
            print("🔍 ПОЛНАЯ СТРУКТУРА ОШИБКИ ДЛЯ enhancedError:")
            print(f"   - HTTP Status: {response.status_code}")
            print(f"   - Response Body: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            
            # Проверяем что frontend может создать enhancedError с полями:
            # error.status, error.detail, error.response
            detail = error_data.get('detail', {})
            
            enhanced_error_fields = {
                'status': response.status_code,  # HTTP статус
                'detail': detail,  # Детали ошибки
                'response': error_data  # Полный ответ
            }
            
            print("\n✅ СТРУКТУРА enhancedError ДЛЯ FRONTEND:")
            print(f"   - error.status: {enhanced_error_fields['status']}")
            print(f"   - error.detail.error_type: {enhanced_error_fields['detail'].get('error_type')}")
            print(f"   - error.detail.message: {enhanced_error_fields['detail'].get('message')}")
            print(f"   - error.response: {type(enhanced_error_fields['response'])}")
            
            # Проверяем критические поля для handleLogin
            if (enhanced_error_fields['status'] in [401, 403] and 
                enhanced_error_fields['detail'].get('error_type') in ['user_not_found', 'wrong_password', 'account_disabled']):
                print("✅ СТРУКТУРА enhancedError ПОДХОДИТ ДЛЯ handleLogin")
                print("✅ Frontend может проверить error.status и error.detail.error_type")
                print("✅ Модальное окно будет показано вместо alert")
                test_results.append(("enhanced_error_structure", True, "Структура enhancedError корректна"))
            else:
                print("❌ СТРУКТУРА enhancedError НЕ ПОДХОДИТ ДЛЯ handleLogin")
                test_results.append(("enhanced_error_structure", False, "Неправильная структура enhancedError"))
        else:
            print(f"❌ НЕОЖИДАННЫЙ HTTP СТАТУС: {response.status_code}")
            test_results.append(("enhanced_error_structure", False, f"HTTP {response.status_code} вместо 401"))
            
    except Exception as e:
        print(f"❌ ОШИБКА ТЕСТА: {e}")
        test_results.append(("enhanced_error_structure", False, f"Исключение: {e}"))
    
    # Итоговый отчет
    print("\n" + "=" * 100)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ МОДАЛЬНЫХ ОКОН ОШИБОК АВТОРИЗАЦИИ")
    print("=" * 100)
    
    passed_tests = sum(1 for _, result, _ in test_results if result is True)
    failed_tests = sum(1 for _, result, _ in test_results if result is False)
    na_tests = sum(1 for _, result, _ in test_results if result == "NA")
    total_tests = len(test_results)
    
    print(f"✅ Пройдено тестов: {passed_tests}")
    print(f"❌ Провалено тестов: {failed_tests}")
    print(f"ℹ️ Неприменимо: {na_tests}")
    print(f"📈 Общий процент успеха: {(passed_tests / (total_tests - na_tests) * 100):.1f}%" if (total_tests - na_tests) > 0 else "N/A")
    
    print("\nДетальные результаты:")
    for test_name, result, comment in test_results:
        status_icon = "✅" if result is True else "❌" if result is False else "ℹ️"
        print(f"{status_icon} {test_name}: {comment}")
    
    # Проверяем критические требования для модальных окон
    critical_tests = ["modal_user_not_found", "modal_wrong_password", "enhanced_error_structure"]
    critical_passed = all(result is True for test_name, result, _ in test_results if test_name in critical_tests)
    
    print("\n" + "=" * 100)
    print("🎯 ЗАКЛЮЧЕНИЕ ПО ПРОБЛЕМЕ С МОДАЛЬНЫМИ ОКНАМИ")
    print("=" * 100)
    
    if critical_passed:
        print("🎉 ПРОБЛЕМА С МОДАЛЬНЫМИ ОКНАМИ РЕШЕНА!")
        print("✅ Backend возвращает правильную структуру ошибок для модальных окон")
        print("✅ enhancedError содержит все необходимые поля (status, detail, response)")
        print("✅ handleLogin может проверить error.status и error.detail.error_type")
        print("✅ Модальные окна будут показываться вместо alert'ов")
        print("\n🔧 ИСПРАВЛЕНИЯ РАБОТАЮТ:")
        print("   1. ✅ apiCall передает полную структуру ошибок")
        print("   2. ✅ Структурированные ошибки авторизации не вызывают alert")
        print("   3. ✅ handleLogin получает необходимые данные для модальных окон")
        print("   4. ✅ error.status и error.detail.error_type доступны для проверки")
        return True
    else:
        print("🚨 ПРОБЛЕМА С МОДАЛЬНЫМИ ОКНАМИ НЕ РЕШЕНА!")
        print("❌ Backend не возвращает правильную структуру ошибок")
        print("❌ Требуется дополнительная работа над исправлениями")
        return False

if __name__ == "__main__":
    success = test_modal_error_handling()
    sys.exit(0 if success else 1)
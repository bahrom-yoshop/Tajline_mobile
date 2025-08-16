#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Информативные сообщения об ошибках авторизации в TAJLINE.TJ

НОВАЯ ФУНКЦИОНАЛЬНОСТЬ:
1. Backend: Улучшен endpoint /api/auth/login для детальной проверки ошибок авторизации
2. Backend: Разделены ошибки на "пользователь не найден" (HTTP 401, user_not_found) и "неправильный пароль" (HTTP 401, wrong_password)
3. Frontend: Добавлено состояние loginErrorModal и loginErrorData для модального окна ошибок
4. Frontend: Обновлена функция handleLogin для обработки разных типов ошибок авторизации
5. Frontend: Создано красивое модальное окно с информацией об ошибках входа

ТИПЫ ОШИБОК АВТОРИЗАЦИИ:
1. user_not_found - пользователь с номером телефона не найден
2. wrong_password - неправильный пароль для существующего пользователя
3. account_disabled - аккаунт заблокирован/удален (уже было реализовано)

СТРУКТУРА ДАННЫХ ОШИБОК:
- error_type: тип ошибки (user_not_found, wrong_password)
- message: основное сообщение об ошибке
- details: детальное описание и инструкции
- user_role, user_name, user_phone: информация о пользователе (для wrong_password)
- phone_format: подсказка о формате номера телефона
- password_requirements: требования к паролю
- available_actions: список рекомендуемых действий

ТЕСТИРОВАНИЕ:
1. Тестирование входа с несуществующим номером телефона → должна показаться ошибка "user_not_found"
2. Тестирование входа с существующим номером, но неправильным паролем → ошибка "wrong_password"
3. Проверка структуры ответов и всех полей
4. Тестирование для разных ролей пользователей (admin, operator, courier, user)
5. Проверка отображения подсказок и рекомендаций
"""

import requests
import json
import sys
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://550bba2e-5014-4d23-b2e8-7c38c4ea5482.preview.emergentagent.com/api"

def test_login_error_messages():
    """Тестирование информативных сообщений об ошибках авторизации"""
    
    print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Информативные сообщения об ошибках авторизации в TAJLINE.TJ")
    print("=" * 100)
    
    test_results = []
    
    # Тест 1: Вход с несуществующим номером телефона
    print("\n1️⃣ ТЕСТИРОВАНИЕ ОШИБКИ 'user_not_found'")
    print("-" * 50)
    
    try:
        non_existent_phone = "+79999999999"  # Несуществующий номер
        login_data = {
            "phone": non_existent_phone,
            "password": "anypassword123"
        }
        
        response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
        print(f"📞 Тестируемый номер: {non_existent_phone}")
        print(f"🔐 Тестируемый пароль: {login_data['password']}")
        print(f"📊 HTTP статус: {response.status_code}")
        
        if response.status_code == 401:
            error_data = response.json()
            detail = error_data.get('detail', {})
            
            print(f"✅ Правильный HTTP статус: 401 Unauthorized")
            print(f"🔍 Тип ошибки: {detail.get('error_type')}")
            print(f"💬 Сообщение: {detail.get('message')}")
            print(f"📝 Детали: {detail.get('details')}")
            print(f"📱 Формат телефона: {detail.get('phone_format')}")
            print(f"🎯 Доступные действия: {detail.get('available_actions')}")
            
            # Проверяем структуру ответа
            expected_fields = ['error_type', 'message', 'details', 'phone_format', 'available_actions']
            missing_fields = [field for field in expected_fields if field not in detail]
            
            if detail.get('error_type') == 'user_not_found' and not missing_fields:
                print("✅ ТЕСТ ПРОЙДЕН: Ошибка 'user_not_found' работает корректно")
                test_results.append(("user_not_found", True, "Корректная структура ответа и тип ошибки"))
            else:
                print(f"❌ ТЕСТ НЕ ПРОЙДЕН: Неправильный тип ошибки или отсутствуют поля: {missing_fields}")
                test_results.append(("user_not_found", False, f"Отсутствуют поля: {missing_fields}"))
        else:
            print(f"❌ ТЕСТ НЕ ПРОЙДЕН: Неправильный HTTP статус: {response.status_code}")
            test_results.append(("user_not_found", False, f"HTTP {response.status_code} вместо 401"))
            
    except Exception as e:
        print(f"❌ ОШИБКА ТЕСТА: {e}")
        test_results.append(("user_not_found", False, f"Исключение: {e}"))
    
    # Тест 2: Найти существующего пользователя для тестирования wrong_password
    print("\n2️⃣ ПОИСК СУЩЕСТВУЮЩЕГО ПОЛЬЗОВАТЕЛЯ")
    print("-" * 50)
    
    existing_user = None
    test_users = [
        {"phone": "+79999888777", "role": "admin"},
        {"phone": "+79777888999", "role": "warehouse_operator"},
        {"phone": "+79991234567", "role": "courier"},
        {"phone": "+79123456789", "role": "user"}
    ]
    
    for test_user in test_users:
        try:
            # Пробуем войти с заведомо неправильным паролем
            login_data = {
                "phone": test_user["phone"],
                "password": "wrong_password_123"
            }
            
            response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 401:
                error_data = response.json()
                detail = error_data.get('detail', {})
                
                if detail.get('error_type') == 'wrong_password':
                    existing_user = test_user
                    print(f"✅ Найден существующий пользователь: {test_user['phone']} (роль: {test_user['role']})")
                    break
                    
        except Exception as e:
            continue
    
    if not existing_user:
        print("❌ Не найден существующий пользователь для тестирования wrong_password")
        test_results.append(("wrong_password", False, "Не найден существующий пользователь"))
    else:
        # Тест 3: Вход с существующим номером, но неправильным паролем
        print("\n3️⃣ ТЕСТИРОВАНИЕ ОШИБКИ 'wrong_password'")
        print("-" * 50)
        
        try:
            login_data = {
                "phone": existing_user["phone"],
                "password": "definitely_wrong_password_123"
            }
            
            response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
            print(f"📞 Тестируемый номер: {existing_user['phone']}")
            print(f"🔐 Тестируемый пароль: {login_data['password']}")
            print(f"📊 HTTP статус: {response.status_code}")
            
            if response.status_code == 401:
                error_data = response.json()
                detail = error_data.get('detail', {})
                
                print(f"✅ Правильный HTTP статус: 401 Unauthorized")
                print(f"🔍 Тип ошибки: {detail.get('error_type')}")
                print(f"💬 Сообщение: {detail.get('message')}")
                print(f"📝 Детали: {detail.get('details')}")
                print(f"👤 Роль пользователя: {detail.get('user_role')}")
                print(f"👨‍💼 Имя пользователя: {detail.get('user_name')}")
                print(f"📱 Телефон пользователя: {detail.get('user_phone')}")
                print(f"🔒 Требования к паролю: {detail.get('password_requirements')}")
                print(f"🎯 Доступные действия: {detail.get('available_actions')}")
                
                # Проверяем структуру ответа
                expected_fields = ['error_type', 'message', 'details', 'user_role', 'user_name', 'user_phone', 'password_requirements', 'available_actions']
                missing_fields = [field for field in expected_fields if field not in detail]
                
                if detail.get('error_type') == 'wrong_password' and not missing_fields:
                    print("✅ ТЕСТ ПРОЙДЕН: Ошибка 'wrong_password' работает корректно")
                    test_results.append(("wrong_password", True, "Корректная структура ответа и тип ошибки"))
                else:
                    print(f"❌ ТЕСТ НЕ ПРОЙДЕН: Неправильный тип ошибки или отсутствуют поля: {missing_fields}")
                    test_results.append(("wrong_password", False, f"Отсутствуют поля: {missing_fields}"))
            else:
                print(f"❌ ТЕСТ НЕ ПРОЙДЕН: Неправильный HTTP статус: {response.status_code}")
                test_results.append(("wrong_password", False, f"HTTP {response.status_code} вместо 401"))
                
        except Exception as e:
            print(f"❌ ОШИБКА ТЕСТА: {e}")
            test_results.append(("wrong_password", False, f"Исключение: {e}"))
    
    # Тест 4: Проверка успешного входа (для контроля)
    print("\n4️⃣ КОНТРОЛЬНЫЙ ТЕСТ: Успешный вход администратора")
    print("-" * 50)
    
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
            
            print(f"✅ Успешный вход!")
            print(f"👤 Пользователь: {user_info.get('full_name')}")
            print(f"📱 Телефон: {user_info.get('phone')}")
            print(f"🎭 Роль: {user_info.get('role')}")
            print(f"🔑 Токен получен: {'access_token' in data}")
            
            test_results.append(("successful_login", True, "Успешный вход администратора"))
        else:
            print(f"❌ КОНТРОЛЬНЫЙ ТЕСТ НЕ ПРОЙДЕН: HTTP {response.status_code}")
            test_results.append(("successful_login", False, f"HTTP {response.status_code} вместо 200"))
            
    except Exception as e:
        print(f"❌ ОШИБКА КОНТРОЛЬНОГО ТЕСТА: {e}")
        test_results.append(("successful_login", False, f"Исключение: {e}"))
    
    # Тест 5: Проверка account_disabled (если есть заблокированный пользователь)
    print("\n5️⃣ ТЕСТИРОВАНИЕ ОШИБКИ 'account_disabled' (если применимо)")
    print("-" * 50)
    
    try:
        # Пробуем найти неактивного пользователя
        inactive_user_data = {
            "phone": "+79999999998",  # Потенциально неактивный номер
            "password": "anypassword"
        }
        
        response = requests.post(f"{BACKEND_URL}/auth/login", json=inactive_user_data)
        
        if response.status_code == 403:
            error_data = response.json()
            detail = error_data.get('detail', {})
            
            if detail.get('error_type') == 'account_disabled':
                print(f"✅ Найден заблокированный пользователь")
                print(f"🔍 Тип ошибки: {detail.get('error_type')}")
                print(f"💬 Статус сообщение: {detail.get('status_message')}")
                print(f"📝 Детали статуса: {detail.get('status_details')}")
                print(f"👤 Роль: {detail.get('user_role')}")
                print(f"👨‍💼 Имя: {detail.get('user_name')}")
                print(f"📱 Телефон: {detail.get('user_phone')}")
                print(f"🗑️ Удален: {detail.get('is_deleted')}")
                
                test_results.append(("account_disabled", True, "Корректная обработка заблокированного аккаунта"))
            else:
                print("ℹ️ Заблокированный пользователь не найден (это нормально)")
                test_results.append(("account_disabled", "NA", "Заблокированный пользователь не найден"))
        else:
            print("ℹ️ Заблокированный пользователь не найден (это нормально)")
            test_results.append(("account_disabled", "NA", "Заблокированный пользователь не найден"))
            
    except Exception as e:
        print(f"ℹ️ Тест account_disabled пропущен: {e}")
        test_results.append(("account_disabled", "NA", f"Тест пропущен: {e}"))
    
    # Итоговый отчет
    print("\n" + "=" * 100)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
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
    
    # Проверяем критические требования
    critical_tests = ["user_not_found", "wrong_password"]
    critical_passed = all(result is True for test_name, result, _ in test_results if test_name in critical_tests)
    
    if critical_passed:
        print("\n🎉 КРИТИЧЕСКИЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ Информативные сообщения об ошибках авторизации работают корректно")
        print("✅ Структура данных ошибок соответствует требованиям")
        print("✅ Backend готов для интеграции с frontend модальными окнами")
        return True
    else:
        print("\n🚨 КРИТИЧЕСКИЕ ТЕСТЫ НЕ ПРОЙДЕНЫ!")
        print("❌ Требуется исправление информативных сообщений об ошибках авторизации")
        return False

if __name__ == "__main__":
    success = test_login_error_messages()
    sys.exit(0 if success else 1)
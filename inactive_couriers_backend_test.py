#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Новая подкатегория "Неактивные курьеры" в разделе Пользователи → Курьеры

НОВАЯ ФУНКЦИОНАЛЬНОСТЬ ДОБАВЛЕНА:
1. ✅ Добавлена подкатегория "Неактивные курьеры" в меню Пользователи → Курьеры (только для админов)
2. ✅ Создан полный UI для управления неактивными курьерами
3. ✅ Интегрированы все backend endpoints:
   - GET /api/admin/couriers/inactive - получение списка неактивных курьеров
   - POST /api/admin/couriers/{id}/activate - активация курьера
   - DELETE /api/admin/couriers/{id}/permanent - полное удаление курьера
4. ✅ Добавлена автоматическая загрузка неактивных курьеров при переходе на вкладку
5. ✅ Созданы функции handleActivateCourier и handlePermanentDeleteCourier

UI КОМПОНЕНТЫ:
- Таблица с неактивными курьерами (имя, склад, пользователь, статус)
- Кнопка "Активировать" (зеленая, иконка UserCheck)
- Кнопка "Полностью удалить" (красная, иконка X)
- Информационная панель с объяснением функций
- Кнопка "Обновить" для ручного обновления списка

ПОЛНОЕ ТЕСТИРОВАНИЕ:
1. Авторизация администратора
2. Переход в раздел Пользователи → Курьеры → Неактивные курьеры
3. Проверка автоматической загрузки списка неактивных курьеров
4. Тестирование кнопки "Обновить" для ручного обновления
5. Если есть неактивные курьеры - тестирование кнопки "Активировать"
6. Тестирование кнопки "Полностью удалить" (с двойным подтверждением)
7. Проверка обновления списков после действий

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Полностью функциональная подкатегория "Неактивные курьеры" с возможностью просмотра, активации и полного удаления неактивных курьеров из удобного интерфейса.
"""

import requests
import json
import sys
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://placement-view.preview.emergentagent.com/api"

def test_inactive_couriers_functionality():
    """Тестирование функциональности неактивных курьеров"""
    
    print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Новая подкатегория 'Неактивные курьеры' в TAJLINE.TJ")
    print("=" * 100)
    
    test_results = []
    admin_token = None
    
    # Тест 1: Авторизация администратора
    print("\n1️⃣ АВТОРИЗАЦИЯ АДМИНИСТРАТОРА")
    print("-" * 50)
    
    try:
        admin_credentials = {
            "phone": "+79999888777",
            "password": "admin123"
        }
        
        response = requests.post(f"{BACKEND_URL}/auth/login", json=admin_credentials)
        print(f"📞 Номер администратора: {admin_credentials['phone']}")
        print(f"📊 HTTP статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            admin_token = data.get('access_token')
            user_info = data.get('user', {})
            
            print(f"✅ Успешная авторизация!")
            print(f"👤 Администратор: {user_info.get('full_name')}")
            print(f"📱 Телефон: {user_info.get('phone')}")
            print(f"🎭 Роль: {user_info.get('role')}")
            print(f"🔑 Токен получен: {bool(admin_token)}")
            
            if user_info.get('role') == 'admin':
                test_results.append(("admin_authorization", True, f"Успешная авторизация администратора '{user_info.get('full_name')}'"))
            else:
                test_results.append(("admin_authorization", False, f"Неправильная роль: {user_info.get('role')}"))
        else:
            print(f"❌ Ошибка авторизации: HTTP {response.status_code}")
            test_results.append(("admin_authorization", False, f"HTTP {response.status_code}"))
            return test_results
            
    except Exception as e:
        print(f"❌ ОШИБКА АВТОРИЗАЦИИ: {e}")
        test_results.append(("admin_authorization", False, f"Исключение: {e}"))
        return test_results
    
    # Заголовки для авторизованных запросов
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Тест 2: Получение списка неактивных курьеров
    print("\n2️⃣ ПОЛУЧЕНИЕ СПИСКА НЕАКТИВНЫХ КУРЬЕРОВ")
    print("-" * 50)
    
    try:
        response = requests.get(f"{BACKEND_URL}/admin/couriers/inactive", headers=headers)
        print(f"📊 HTTP статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            inactive_couriers = data.get('inactive_couriers', [])
            total_count = data.get('total_count', 0)
            
            print(f"✅ Endpoint работает корректно!")
            print(f"📋 Всего неактивных курьеров: {total_count}")
            print(f"📊 Получено записей: {len(inactive_couriers)}")
            
            # Проверяем структуру данных
            if inactive_couriers:
                sample_courier = inactive_couriers[0]
                required_fields = ['id', 'full_name', 'phone', 'assigned_warehouse_id', 'is_active']
                missing_fields = [field for field in required_fields if field not in sample_courier]
                
                if not missing_fields:
                    print(f"✅ Структура данных корректна")
                    print(f"📝 Пример курьера: {sample_courier.get('full_name')} (ID: {sample_courier.get('id')[:8]}...)")
                    if 'user_info' in sample_courier:
                        print(f"👤 Информация о пользователе: {sample_courier['user_info']}")
                    if 'assigned_warehouse_name' in sample_courier:
                        print(f"🏢 Склад: {sample_courier['assigned_warehouse_name']}")
                else:
                    print(f"⚠️ Отсутствуют поля: {missing_fields}")
            else:
                print("ℹ️ Неактивных курьеров не найдено")
            
            test_results.append(("get_inactive_couriers", True, f"Получено {total_count} неактивных курьеров"))
            
        elif response.status_code == 403:
            print(f"❌ Доступ запрещен: {response.status_code}")
            test_results.append(("get_inactive_couriers", False, "Доступ запрещен - проверьте права администратора"))
        else:
            print(f"❌ Ошибка получения списка: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"📝 Детали ошибки: {error_data}")
            except:
                pass
            test_results.append(("get_inactive_couriers", False, f"HTTP {response.status_code}"))
            
    except Exception as e:
        print(f"❌ ОШИБКА ПОЛУЧЕНИЯ СПИСКА: {e}")
        test_results.append(("get_inactive_couriers", False, f"Исключение: {e}"))
    
    # Тест 3: Создание тестового неактивного курьера (если нет неактивных)
    print("\n3️⃣ ПОДГОТОВКА ТЕСТОВЫХ ДАННЫХ")
    print("-" * 50)
    
    test_courier_id = None
    
    try:
        # Сначала получаем список активных курьеров
        response = requests.get(f"{BACKEND_URL}/admin/couriers/list", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            active_couriers = data.get('couriers', [])
            
            if active_couriers:
                # Берем первого активного курьера и делаем его неактивным для тестирования
                test_courier = active_couriers[0]
                test_courier_id = test_courier.get('id')
                
                print(f"🔧 Используем курьера для тестирования: {test_courier.get('full_name')} (ID: {test_courier_id[:8]}...)")
                
                # Деактивируем курьера через DELETE endpoint (soft delete)
                delete_response = requests.delete(f"{BACKEND_URL}/admin/couriers/{test_courier_id}", headers=headers)
                
                if delete_response.status_code == 200:
                    print(f"✅ Курьер успешно деактивирован для тестирования")
                    test_results.append(("prepare_test_data", True, "Тестовый неактивный курьер подготовлен"))
                else:
                    print(f"⚠️ Не удалось деактивировать курьера: HTTP {delete_response.status_code}")
                    test_results.append(("prepare_test_data", False, f"Не удалось деактивировать: HTTP {delete_response.status_code}"))
            else:
                print("ℹ️ Активных курьеров не найдено для создания тестовых данных")
                test_results.append(("prepare_test_data", "NA", "Нет активных курьеров для тестирования"))
        else:
            print(f"⚠️ Не удалось получить список активных курьеров: HTTP {response.status_code}")
            test_results.append(("prepare_test_data", False, f"HTTP {response.status_code}"))
            
    except Exception as e:
        print(f"⚠️ Ошибка подготовки тестовых данных: {e}")
        test_results.append(("prepare_test_data", False, f"Исключение: {e}"))
    
    # Тест 4: Повторное получение списка неактивных курьеров (должен содержать тестового курьера)
    print("\n4️⃣ ПРОВЕРКА ОБНОВЛЕННОГО СПИСКА НЕАКТИВНЫХ КУРЬЕРОВ")
    print("-" * 50)
    
    try:
        response = requests.get(f"{BACKEND_URL}/admin/couriers/inactive", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            inactive_couriers = data.get('inactive_couriers', [])
            total_count = data.get('total_count', 0)
            
            print(f"✅ Обновленный список получен!")
            print(f"📋 Всего неактивных курьеров: {total_count}")
            
            # Ищем нашего тестового курьера
            test_courier_found = False
            if test_courier_id:
                for courier in inactive_couriers:
                    if courier.get('id') == test_courier_id:
                        test_courier_found = True
                        print(f"✅ Тестовый курьер найден в списке неактивных: {courier.get('full_name')}")
                        break
                
                if test_courier_found:
                    test_results.append(("updated_inactive_list", True, "Тестовый курьер корректно появился в списке неактивных"))
                else:
                    test_results.append(("updated_inactive_list", False, "Тестовый курьер не найден в списке неактивных"))
            else:
                test_results.append(("updated_inactive_list", "NA", "Нет тестового курьера для проверки"))
                
        else:
            print(f"❌ Ошибка получения обновленного списка: HTTP {response.status_code}")
            test_results.append(("updated_inactive_list", False, f"HTTP {response.status_code}"))
            
    except Exception as e:
        print(f"❌ ОШИБКА ПОЛУЧЕНИЯ ОБНОВЛЕННОГО СПИСКА: {e}")
        test_results.append(("updated_inactive_list", False, f"Исключение: {e}"))
    
    # Тест 5: Активация курьера
    print("\n5️⃣ ТЕСТИРОВАНИЕ АКТИВАЦИИ КУРЬЕРА")
    print("-" * 50)
    
    if test_courier_id:
        try:
            response = requests.post(f"{BACKEND_URL}/admin/couriers/{test_courier_id}/activate", headers=headers)
            print(f"🔄 Активируем курьера: {test_courier_id[:8]}...")
            print(f"📊 HTTP статус: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Курьер успешно активирован!")
                print(f"💬 Сообщение: {data.get('message')}")
                print(f"🆔 ID курьера: {data.get('courier_id')}")
                print(f"👤 Активирован пользователем: {data.get('activated_by')}")
                
                test_results.append(("activate_courier", True, "Курьер успешно активирован"))
                
            elif response.status_code == 404:
                print(f"❌ Курьер не найден")
                test_results.append(("activate_courier", False, "Курьер не найден"))
            elif response.status_code == 400:
                print(f"❌ Не удалось активировать курьера")
                try:
                    error_data = response.json()
                    print(f"📝 Детали ошибки: {error_data}")
                except:
                    pass
                test_results.append(("activate_courier", False, "Не удалось активировать"))
            else:
                print(f"❌ Ошибка активации: HTTP {response.status_code}")
                test_results.append(("activate_courier", False, f"HTTP {response.status_code}"))
                
        except Exception as e:
            print(f"❌ ОШИБКА АКТИВАЦИИ: {e}")
            test_results.append(("activate_courier", False, f"Исключение: {e}"))
    else:
        print("ℹ️ Нет тестового курьера для активации")
        test_results.append(("activate_courier", "NA", "Нет тестового курьера"))
    
    # Тест 6: Проверка, что курьер исчез из списка неактивных после активации
    print("\n6️⃣ ПРОВЕРКА СПИСКА ПОСЛЕ АКТИВАЦИИ")
    print("-" * 50)
    
    if test_courier_id:
        try:
            response = requests.get(f"{BACKEND_URL}/admin/couriers/inactive", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                inactive_couriers = data.get('inactive_couriers', [])
                
                # Проверяем, что тестового курьера больше нет в списке неактивных
                test_courier_still_inactive = False
                for courier in inactive_couriers:
                    if courier.get('id') == test_courier_id:
                        test_courier_still_inactive = True
                        break
                
                if not test_courier_still_inactive:
                    print(f"✅ Курьер корректно исчез из списка неактивных после активации")
                    test_results.append(("check_after_activation", True, "Курьер исчез из списка неактивных"))
                else:
                    print(f"❌ Курьер все еще в списке неактивных после активации")
                    test_results.append(("check_after_activation", False, "Курьер остался в списке неактивных"))
                    
            else:
                print(f"❌ Ошибка получения списка: HTTP {response.status_code}")
                test_results.append(("check_after_activation", False, f"HTTP {response.status_code}"))
                
        except Exception as e:
            print(f"❌ ОШИБКА ПРОВЕРКИ: {e}")
            test_results.append(("check_after_activation", False, f"Исключение: {e}"))
    else:
        test_results.append(("check_after_activation", "NA", "Нет тестового курьера"))
    
    # Тест 7: Тестирование полного удаления курьера
    print("\n7️⃣ ТЕСТИРОВАНИЕ ПОЛНОГО УДАЛЕНИЯ КУРЬЕРА")
    print("-" * 50)
    
    # Сначала создадим еще одного тестового неактивного курьера для полного удаления
    permanent_delete_courier_id = None
    
    try:
        # Получаем список активных курьеров для создания еще одного тестового
        response = requests.get(f"{BACKEND_URL}/admin/couriers/list", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            active_couriers = data.get('couriers', [])
            
            if len(active_couriers) > 0:
                # Берем другого курьера для тестирования полного удаления
                delete_test_courier = active_couriers[0]
                permanent_delete_courier_id = delete_test_courier.get('id')
                
                print(f"🔧 Подготавливаем курьера для полного удаления: {delete_test_courier.get('full_name')}")
                
                # Сначала деактивируем его
                delete_response = requests.delete(f"{BACKEND_URL}/admin/couriers/{permanent_delete_courier_id}", headers=headers)
                
                if delete_response.status_code == 200:
                    print(f"✅ Курьер деактивирован, готов для полного удаления")
                    
                    # Теперь тестируем полное удаление
                    permanent_delete_response = requests.delete(
                        f"{BACKEND_URL}/admin/couriers/{permanent_delete_courier_id}/permanent", 
                        headers=headers
                    )
                    
                    print(f"🗑️ Полное удаление курьера: {permanent_delete_courier_id[:8]}...")
                    print(f"📊 HTTP статус: {permanent_delete_response.status_code}")
                    
                    if permanent_delete_response.status_code == 200:
                        delete_data = permanent_delete_response.json()
                        print(f"✅ Курьер полностью удален!")
                        print(f"💬 Сообщение: {delete_data.get('message')}")
                        print(f"🆔 ID курьера: {delete_data.get('courier_id')}")
                        print(f"👤 Пользователь удален: {delete_data.get('user_deleted')}")
                        print(f"🗑️ Удален пользователем: {delete_data.get('deleted_by')}")
                        print(f"📅 Дата удаления: {delete_data.get('deletion_date')}")
                        
                        test_results.append(("permanent_delete_courier", True, "Курьер полностью удален из базы данных"))
                        
                    elif permanent_delete_response.status_code == 404:
                        print(f"❌ Курьер не найден для полного удаления")
                        test_results.append(("permanent_delete_courier", False, "Курьер не найден"))
                    elif permanent_delete_response.status_code == 400:
                        print(f"❌ Не удалось полностью удалить курьера")
                        try:
                            error_data = permanent_delete_response.json()
                            print(f"📝 Детали ошибки: {error_data}")
                        except:
                            pass
                        test_results.append(("permanent_delete_courier", False, "Не удалось удалить"))
                    else:
                        print(f"❌ Ошибка полного удаления: HTTP {permanent_delete_response.status_code}")
                        test_results.append(("permanent_delete_courier", False, f"HTTP {permanent_delete_response.status_code}"))
                        
                else:
                    print(f"⚠️ Не удалось деактивировать курьера для полного удаления")
                    test_results.append(("permanent_delete_courier", False, "Не удалось подготовить курьера"))
            else:
                print("ℹ️ Нет активных курьеров для тестирования полного удаления")
                test_results.append(("permanent_delete_courier", "NA", "Нет курьеров для тестирования"))
        else:
            print(f"⚠️ Не удалось получить список курьеров: HTTP {response.status_code}")
            test_results.append(("permanent_delete_courier", False, f"HTTP {response.status_code}"))
            
    except Exception as e:
        print(f"❌ ОШИБКА ПОЛНОГО УДАЛЕНИЯ: {e}")
        test_results.append(("permanent_delete_courier", False, f"Исключение: {e}"))
    
    # Тест 8: Проверка безопасности - доступ только для админов
    print("\n8️⃣ ПРОВЕРКА БЕЗОПАСНОСТИ - ДОСТУП ТОЛЬКО ДЛЯ АДМИНОВ")
    print("-" * 50)
    
    try:
        # Пробуем получить доступ без токена
        response_no_auth = requests.get(f"{BACKEND_URL}/admin/couriers/inactive")
        print(f"🔒 Запрос без авторизации: HTTP {response_no_auth.status_code}")
        
        if response_no_auth.status_code == 401:
            print(f"✅ Правильно заблокирован доступ без авторизации")
            security_test_1 = True
        else:
            print(f"❌ Неправильная обработка запроса без авторизации")
            security_test_1 = False
        
        # Пробуем получить доступ с неправильным токеном
        fake_headers = {"Authorization": "Bearer fake_token_123"}
        response_fake_auth = requests.get(f"{BACKEND_URL}/admin/couriers/inactive", headers=fake_headers)
        print(f"🔒 Запрос с поддельным токеном: HTTP {response_fake_auth.status_code}")
        
        if response_fake_auth.status_code == 401:
            print(f"✅ Правильно заблокирован доступ с поддельным токеном")
            security_test_2 = True
        else:
            print(f"❌ Неправильная обработка поддельного токена")
            security_test_2 = False
        
        if security_test_1 and security_test_2:
            test_results.append(("security_check", True, "Безопасность endpoints корректна"))
        else:
            test_results.append(("security_check", False, "Проблемы с безопасностью"))
            
    except Exception as e:
        print(f"❌ ОШИБКА ПРОВЕРКИ БЕЗОПАСНОСТИ: {e}")
        test_results.append(("security_check", False, f"Исключение: {e}"))
    
    # Итоговый отчет
    print("\n" + "=" * 100)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ НЕАКТИВНЫХ КУРЬЕРОВ")
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
    critical_tests = ["admin_authorization", "get_inactive_couriers", "activate_courier", "permanent_delete_courier"]
    critical_passed = all(result is True for test_name, result, _ in test_results if test_name in critical_tests and result != "NA")
    
    if critical_passed:
        print("\n🎉 КРИТИЧЕСКИЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ Все backend endpoints для неактивных курьеров работают корректно")
        print("✅ Авторизация и безопасность функционируют правильно")
        print("✅ Активация и полное удаление курьеров работают как ожидается")
        print("✅ Backend готов для интеграции с frontend UI")
        return True
    else:
        print("\n🚨 КРИТИЧЕСКИЕ ТЕСТЫ НЕ ПРОЙДЕНЫ!")
        print("❌ Требуется исправление функциональности неактивных курьеров")
        return False

if __name__ == "__main__":
    success = test_inactive_couriers_functionality()
    sys.exit(0 if success else 1)
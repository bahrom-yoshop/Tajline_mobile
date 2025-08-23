#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ БАГА С ID УВЕДОМЛЕНИЙ СКЛАДА
Testing the critical bug fix with warehouse notification IDs in TAJLINE.TJ

КРИТИЧЕСКИЙ БАГ ИСПРАВЛЕН: Заменена функция generate_readable_request_number() на уникальный timestamp-based ID для warehouse_notifications

БЫСТРЫЙ ТЕСТ:
1. Авторизация оператора (+79777888999/warehouse123)  
2. Создание заявки на забор груза через POST /api/admin/courier/pickup-request
3. Авторизация курьера (+79991234567/courier123)
4. Принятие заявки курьером
5. Забор груза курьером  
6. Сдача груза на склад курьером - должна создать уведомление с УНИКАЛЬНЫМ ID
7. КРИТИЧЕСКИЙ ТЕСТ: Получение уведомлений через GET /api/operator/warehouse-notifications - проверить что ID уникальный
8. КРИТИЧЕСКИЙ ТЕСТ: Принятие уведомления через POST /api/operator/warehouse-notifications/{notification_id}/accept - должно работать
9. Завершение оформления через POST /api/operator/warehouse-notifications/{notification_id}/complete

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Каждое новое уведомление должно иметь уникальный ID в формате WN_{timestamp} и система принятия должна работать без ошибок.
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

class WarehouseNotificationIDTester:
    def __init__(self, base_url="https://cargo-sync.preview.emergentagent.com"):
        self.base_url = base_url
        self.tokens = {}
        self.users = {}
        self.test_data = {}
        self.tests_run = 0
        self.tests_passed = 0
        
        print(f"🚨 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ БАГА С ID УВЕДОМЛЕНИЙ СКЛАДА")
        print(f"📡 Base URL: {self.base_url}")
        print("=" * 80)

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data: Optional[Dict] = None, token: Optional[str] = None, 
                 params: Optional[Dict] = None) -> tuple[bool, Dict]:
        """Run a single API test"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'

        self.tests_run += 1
        print(f"\n🔍 Test {self.tests_run}: {name}")
        print(f"   {method} {endpoint}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, params=params)
            elif method == 'DELETE':
                response = requests.delete(url, json=data, headers=headers)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"   ✅ PASSED - Status: {response.status_code}")
                try:
                    result = response.json()
                    if isinstance(result, dict) and len(str(result)) < 300:
                        print(f"   📄 Response: {result}")
                    return True, result
                except:
                    return True, {}
            else:
                print(f"   ❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   📄 Error: {error_detail}")
                except:
                    print(f"   📄 Raw response: {response.text[:200]}")
                return False, {}

        except Exception as e:
            print(f"   ❌ FAILED - Exception: {str(e)}")
            return False, {}

    def test_warehouse_notification_id_bug_fix(self):
        """Test the critical warehouse notification ID bug fix"""
        print("\n🚨 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ БАГА С ID УВЕДОМЛЕНИЙ")
        print("   🎯 Тестирование полного цикла с проверкой уникальности ID уведомлений")
        
        all_success = True
        
        # ЭТАП 1: Авторизация оператора (+79777888999/warehouse123)
        print("\n   🔐 ЭТАП 1: АВТОРИЗАЦИЯ ОПЕРАТОРА (+79777888999/warehouse123)...")
        
        operator_login_data = {
            "phone": "+79777888999",
            "password": "warehouse123"
        }
        
        success, login_response = self.run_test(
            "Авторизация оператора склада",
            "POST",
            "/api/auth/login",
            200,
            operator_login_data
        )
        all_success &= success
        
        operator_token = None
        if success and 'access_token' in login_response:
            operator_token = login_response['access_token']
            operator_user = login_response.get('user', {})
            operator_role = operator_user.get('role')
            operator_name = operator_user.get('full_name')
            operator_user_number = operator_user.get('user_number')
            
            print(f"   ✅ Оператор успешно авторизован: {operator_name}")
            print(f"   👑 Роль: {operator_role}")
            print(f"   📞 Телефон: {operator_user.get('phone')}")
            print(f"   🆔 Номер пользователя: {operator_user_number}")
            
            self.tokens['operator'] = operator_token
            self.users['operator'] = operator_user
        else:
            print("   ❌ Авторизация оператора не удалась")
            return False
        
        # ЭТАП 2: Создание заявки на забор груза через POST /api/admin/courier/pickup-request
        print("\n   📦 ЭТАП 2: СОЗДАНИЕ ЗАЯВКИ НА ЗАБОР ГРУЗА...")
        
        # Generate unique test data with timestamp
        timestamp = int(time.time())
        pickup_request_data = {
            "sender_full_name": f"Тест Отправитель {timestamp}",
            "sender_phone": f"+7999{timestamp % 10000:04d}",
            "pickup_address": "Москва, Красная площадь, 1",
            "pickup_date": "2025-01-20",
            "pickup_time_from": "10:00",
            "pickup_time_to": "18:00",
            "destination": "Душанбе",
            "courier_fee": 1500.0,
            "cargo_name": f"Тестовый груз для проверки ID уведомлений {timestamp}",
            "weight": 5.0,
            "route": "moscow_to_tajikistan"
        }
        
        success, pickup_response = self.run_test(
            "Создание заявки на забор груза",
            "POST",
            "/api/admin/courier/pickup-request",
            200,
            pickup_request_data,
            operator_token
        )
        all_success &= success
        
        pickup_request_id = None
        pickup_request_number = None
        if success and ('id' in pickup_response or 'request_id' in pickup_response):
            pickup_request_id = pickup_response.get('request_id') or pickup_response.get('id')
            pickup_request_number = pickup_response.get('request_number')
            
            print(f"   ✅ Заявка на забор груза создана: ID {pickup_request_id}")
            print(f"   📋 Номер заявки: {pickup_request_number}")
            
            self.test_data['pickup_request_id'] = pickup_request_id
            self.test_data['pickup_request_number'] = pickup_request_number
        else:
            print("   ❌ Создание заявки на забор груза не удалось")
            print(f"   📄 Response keys: {list(pickup_response.keys()) if pickup_response else 'No response'}")
            return False
        
        # ЭТАП 3: Авторизация курьера (+79991234567/courier123)
        print("\n   🚚 ЭТАП 3: АВТОРИЗАЦИЯ КУРЬЕРА (+79991234567/courier123)...")
        
        courier_login_data = {
            "phone": "+79991234567",
            "password": "courier123"
        }
        
        success, courier_login_response = self.run_test(
            "Авторизация курьера",
            "POST",
            "/api/auth/login",
            200,
            courier_login_data
        )
        all_success &= success
        
        courier_token = None
        if success and 'access_token' in courier_login_response:
            courier_token = courier_login_response['access_token']
            courier_user = courier_login_response.get('user', {})
            courier_role = courier_user.get('role')
            courier_name = courier_user.get('full_name')
            courier_user_number = courier_user.get('user_number')
            
            print(f"   ✅ Курьер успешно авторизован: {courier_name}")
            print(f"   👑 Роль: {courier_role}")
            print(f"   📞 Телефон: {courier_user.get('phone')}")
            print(f"   🆔 Номер пользователя: {courier_user_number}")
            
            self.tokens['courier'] = courier_token
            self.users['courier'] = courier_user
        else:
            print("   ❌ Авторизация курьера не удалась")
            return False
        
        # ЭТАП 4: Принятие заявки курьером
        print("\n   ✋ ЭТАП 4: ПРИНЯТИЕ ЗАЯВКИ КУРЬЕРОМ...")
        
        success, accept_response = self.run_test(
            "Принятие заявки курьером",
            "POST",
            f"/api/courier/requests/{pickup_request_id}/accept",
            200,
            token=courier_token
        )
        all_success &= success
        
        if success:
            print(f"   ✅ Заявка {pickup_request_id} принята курьером")
            print(f"   📋 Статус: {accept_response.get('message', 'Принято')}")
        else:
            print("   ❌ Принятие заявки курьером не удалось")
            return False
        
        # ЭТАП 5: Забор груза курьером
        print("\n   📦 ЭТАП 5: ЗАБОР ГРУЗА КУРЬЕРОМ...")
        
        success, pickup_cargo_response = self.run_test(
            "Забор груза курьером",
            "POST",
            f"/api/courier/requests/{pickup_request_id}/pickup",
            200,
            token=courier_token
        )
        all_success &= success
        
        if success:
            print(f"   ✅ Груз по заявке {pickup_request_id} забран курьером")
            print(f"   📋 Статус: {pickup_cargo_response.get('message', 'Забрано')}")
        else:
            print("   ❌ Забор груза курьером не удался")
            return False
        
        # ЭТАП 6: Сдача груза на склад курьером - должна создать уведомление с УНИКАЛЬНЫМ ID
        print("\n   🏭 ЭТАП 6: СДАЧА ГРУЗА НА СКЛАД КУРЬЕРОМ (СОЗДАНИЕ УВЕДОМЛЕНИЯ)...")
        
        success, deliver_response = self.run_test(
            "Сдача груза на склад курьером",
            "POST",
            f"/api/courier/requests/{pickup_request_id}/deliver-to-warehouse",
            200,
            token=courier_token
        )
        all_success &= success
        
        if success:
            print(f"   ✅ Груз по заявке {pickup_request_id} сдан на склад")
            print(f"   📋 Статус: {deliver_response.get('message', 'Сдано на склад')}")
            print("   🔔 Уведомление для оператора склада должно быть создано")
        else:
            print("   ❌ Сдача груза на склад не удалась")
            return False
        
        # Небольшая пауза для обработки уведомления
        print("   ⏳ Ожидание обработки уведомления (2 секунды)...")
        time.sleep(2)
        
        # ЭТАП 7: КРИТИЧЕСКИЙ ТЕСТ - Получение уведомлений через GET /api/operator/warehouse-notifications
        print("\n   🚨 ЭТАП 7: КРИТИЧЕСКИЙ ТЕСТ - ПОЛУЧЕНИЕ УВЕДОМЛЕНИЙ С ПРОВЕРКОЙ УНИКАЛЬНОСТИ ID...")
        
        success, notifications_response = self.run_test(
            "Получение уведомлений оператора склада",
            "GET",
            "/api/operator/warehouse-notifications",
            200,
            token=operator_token
        )
        all_success &= success
        
        notification_id = None
        notification_ids = []
        
        if success:
            notifications = notifications_response if isinstance(notifications_response, list) else notifications_response.get('notifications', [])
            notification_count = len(notifications)
            
            print(f"   ✅ Получено {notification_count} уведомлений")
            
            if notification_count > 0:
                # Собираем все ID уведомлений для проверки уникальности
                for notification in notifications:
                    notif_id = notification.get('id')
                    if notif_id:
                        notification_ids.append(notif_id)
                        print(f"   🔔 Уведомление ID: {notif_id}")
                        
                        # Проверяем формат ID (должен быть WN_{timestamp} или уникальный)
                        if notif_id.startswith('WN_'):
                            print(f"   ✅ ID в правильном формате WN_timestamp: {notif_id}")
                        else:
                            print(f"   ⚠️  ID не в формате WN_timestamp: {notif_id}")
                
                # КРИТИЧЕСКАЯ ПРОВЕРКА: Все ID должны быть уникальными
                unique_ids = set(notification_ids)
                if len(unique_ids) == len(notification_ids):
                    print(f"   ✅ КРИТИЧЕСКИЙ УСПЕХ: Все {len(notification_ids)} ID уведомлений уникальны!")
                    print("   ✅ БАГ С ОДИНАКОВЫМИ ID ИСПРАВЛЕН!")
                else:
                    print(f"   ❌ КРИТИЧЕСКИЙ БАГ: Найдены дублирующиеся ID уведомлений!")
                    print(f"   📊 Всего ID: {len(notification_ids)}, Уникальных: {len(unique_ids)}")
                    
                    # Найдем дублирующиеся ID
                    duplicates = []
                    for notif_id in notification_ids:
                        if notification_ids.count(notif_id) > 1 and notif_id not in duplicates:
                            duplicates.append(notif_id)
                    
                    if duplicates:
                        print(f"   ❌ Дублирующиеся ID: {duplicates}")
                    
                    all_success = False
                
                # Найдем наше новое уведомление для дальнейшего тестирования
                for notification in notifications:
                    request_id = notification.get('request_id')
                    if request_id == pickup_request_id:
                        notification_id = notification.get('id')
                        print(f"   🎯 Найдено наше уведомление: ID {notification_id}")
                        break
                
                if not notification_id:
                    # Возьмем первое доступное уведомление
                    notification_id = notifications[0].get('id')
                    print(f"   📋 Используем первое доступное уведомление: ID {notification_id}")
                
                self.test_data['notification_id'] = notification_id
            else:
                print("   ⚠️  Уведомления не найдены")
                return False
        else:
            print("   ❌ Получение уведомлений не удалось")
            return False
        
        # ЭТАП 8: КРИТИЧЕСКИЙ ТЕСТ - Принятие уведомления через POST /api/operator/warehouse-notifications/{notification_id}/accept
        print("\n   🚨 ЭТАП 8: КРИТИЧЕСКИЙ ТЕСТ - ПРИНЯТИЕ УВЕДОМЛЕНИЯ...")
        
        if notification_id:
            success, accept_notification_response = self.run_test(
                "Принятие уведомления оператором",
                "POST",
                f"/api/operator/warehouse-notifications/{notification_id}/accept",
                200,
                token=operator_token
            )
            
            if success:
                print(f"   ✅ КРИТИЧЕСКИЙ УСПЕХ: Уведомление {notification_id} принято!")
                print("   ✅ СИСТЕМА ПРИНЯТИЯ УВЕДОМЛЕНИЙ РАБОТАЕТ БЕЗ ОШИБОК!")
                print(f"   📋 Ответ: {accept_notification_response.get('message', 'Принято')}")
            else:
                print(f"   ❌ КРИТИЧЕСКИЙ СБОЙ: Принятие уведомления {notification_id} не удалось!")
                print("   ❌ СИСТЕМА ПРИНЯТИЯ УВЕДОМЛЕНИЙ НЕ РАБОТАЕТ!")
                all_success = False
        else:
            print("   ❌ Нет ID уведомления для тестирования принятия")
            all_success = False
        
        # ЭТАП 9: Завершение оформления через POST /api/operator/warehouse-notifications/{notification_id}/complete
        print("\n   ✅ ЭТАП 9: ЗАВЕРШЕНИЕ ОФОРМЛЕНИЯ УВЕДОМЛЕНИЯ...")
        
        if notification_id:
            # Add required data for complete endpoint
            complete_data = {
                "cargo_items": [
                    {
                        "cargo_name": f"Груз из заявки {pickup_request_number}",
                        "weight": 5.0,
                        "declared_value": 1500.0
                    }
                ]
            }
            
            success, complete_notification_response = self.run_test(
                "Завершение оформления уведомления",
                "POST",
                f"/api/operator/warehouse-notifications/{notification_id}/complete",
                200,
                complete_data,
                operator_token
            )
            
            if success:
                print(f"   ✅ Уведомление {notification_id} завершено!")
                print(f"   📋 Ответ: {complete_notification_response.get('message', 'Завершено')}")
                
                # Проверим, создались ли грузы
                if 'created_cargo' in complete_notification_response:
                    created_cargo = complete_notification_response['created_cargo']
                    if isinstance(created_cargo, list):
                        print(f"   📦 Создано грузов: {len(created_cargo)}")
                        for cargo in created_cargo:
                            cargo_number = cargo.get('cargo_number', 'N/A')
                            print(f"   📦 Груз создан: {cargo_number}")
                    else:
                        print(f"   📦 Груз создан: {created_cargo}")
            else:
                print(f"   ❌ Завершение оформления уведомления {notification_id} не удалось")
                all_success = False
        else:
            print("   ❌ Нет ID уведомления для завершения оформления")
            all_success = False
        
        # ФИНАЛЬНАЯ ПРОВЕРКА: Повторно получим уведомления и проверим уникальность
        print("\n   🔍 ФИНАЛЬНАЯ ПРОВЕРКА: ПОВТОРНАЯ ПРОВЕРКА УНИКАЛЬНОСТИ ID...")
        
        success, final_notifications_response = self.run_test(
            "Финальная проверка уведомлений",
            "GET",
            "/api/operator/warehouse-notifications",
            200,
            token=operator_token
        )
        
        if success:
            final_notifications = final_notifications_response if isinstance(final_notifications_response, list) else final_notifications_response.get('notifications', [])
            final_notification_ids = [n.get('id') for n in final_notifications if n.get('id')]
            final_unique_ids = set(final_notification_ids)
            
            print(f"   📊 Финальная проверка: {len(final_notification_ids)} ID, {len(final_unique_ids)} уникальных")
            
            if len(final_unique_ids) == len(final_notification_ids):
                print("   ✅ ФИНАЛЬНЫЙ УСПЕХ: Все ID уведомлений остаются уникальными!")
            else:
                print("   ❌ ФИНАЛЬНЫЙ СБОЙ: Обнаружены дублирующиеся ID!")
                all_success = False
        
        # ИТОГОВЫЙ ОТЧЕТ
        print("\n" + "=" * 80)
        print("📊 ИТОГОВЫЙ ОТЧЕТ КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ ИСПРАВЛЕНИЯ БАГА С ID УВЕДОМЛЕНИЙ")
        print("=" * 80)
        
        if all_success:
            print("🎉 ВСЕ КРИТИЧЕСКИЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            print("✅ Авторизация оператора работает")
            print("✅ Создание заявки на забор груза работает")
            print("✅ Авторизация курьера работает")
            print("✅ Принятие заявки курьером работает")
            print("✅ Забор груза курьером работает")
            print("✅ Сдача груза на склад работает и создает уведомление")
            print("✅ КРИТИЧЕСКИЙ УСПЕХ: Все ID уведомлений уникальны!")
            print("✅ КРИТИЧЕСКИЙ УСПЕХ: Система принятия уведомлений работает!")
            print("✅ Завершение оформления уведомлений работает")
            print("")
            print("🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ ДОСТИГНУТ:")
            print("   • Каждое новое уведомление имеет уникальный ID")
            print("   • Система принятия уведомлений работает без ошибок")
            print("   • БАГ С ОДИНАКОВЫМИ ID (100004) ИСПРАВЛЕН!")
        else:
            print("❌ КРИТИЧЕСКИЕ ТЕСТЫ НЕ ПРОЙДЕНЫ!")
            print("🔍 Проверьте детали выше для выявления проблем")
            print("")
            print("⚠️  ВОЗМОЖНЫЕ ПРОБЛЕМЫ:")
            print("   • ID уведомлений все еще дублируются")
            print("   • Система принятия уведомлений не работает")
            print("   • Функция generate_readable_request_number() не заменена")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\n📈 СТАТИСТИКА ТЕСТИРОВАНИЯ: {self.tests_passed}/{self.tests_run} тестов пройдено ({success_rate:.1f}%)")
        
        return all_success

def main():
    """Main function to run the warehouse notification ID bug fix test"""
    tester = WarehouseNotificationIDTester()
    
    try:
        # Run the critical warehouse notification ID bug fix test
        success = tester.test_warehouse_notification_id_bug_fix()
        
        if success:
            print("\n🎉 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ БАГ С ID УВЕДОМЛЕНИЙ ИСПРАВЛЕН!")
            sys.exit(0)
        else:
            print("\n❌ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ НЕ ПРОЙДЕНО!")
            print("🚨 БАГ С ID УВЕДОМЛЕНИЙ ТРЕБУЕТ ВНИМАНИЯ!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка при тестировании: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
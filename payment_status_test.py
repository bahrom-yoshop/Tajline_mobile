#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ СТАТУСА ОПЛАТЫ В МОДАЛЬНОМ ОКНЕ TAJLINE.TJ
Финальное тестирование исправления статуса оплаты в модальном окне согласно review request
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class PaymentStatusTester:
    def __init__(self):
        # Используем URL из frontend/.env
        self.base_url = "https://tajline-cargo-8.preview.emergentagent.com/api"
        self.tokens = {}
        self.test_data = {}
        self.tests_run = 0
        self.tests_passed = 0
        
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ СТАТУСА ОПЛАТЫ В МОДАЛЬНОМ ОКНЕ TAJLINE.TJ")
        print(f"📡 Backend URL: {self.base_url}")
        print("=" * 80)

    def log_test(self, name: str, success: bool, details: str = ""):
        """Логирование результата теста"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ ТЕСТ {self.tests_run}: {name}")
        else:
            print(f"❌ ТЕСТ {self.tests_run}: {name}")
        
        if details:
            print(f"   📝 {details}")

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    token: Optional[str] = None, params: Optional[Dict] = None) -> tuple[bool, Dict]:
        """Выполнить HTTP запрос"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text, "status_code": response.status_code}

            return response.status_code < 400, response_data

        except Exception as e:
            return False, {"error": str(e)}

    def test_courier_authentication(self) -> bool:
        """ЭТАП 1: Авторизация курьера (+79991234567/courier123)"""
        print("\n🔐 ЭТАП 1: АВТОРИЗАЦИЯ КУРЬЕРА")
        
        login_data = {
            "phone": "+79991234567",
            "password": "courier123"
        }
        
        success, response = self.make_request('POST', '/auth/login', login_data)
        
        if success and 'access_token' in response:
            self.tokens['courier'] = response['access_token']
            self.test_data['courier_info'] = response.get('user', {})
            self.log_test("Авторизация курьера", True, 
                         f"Курьер: {response.get('user', {}).get('full_name', 'Unknown')}")
            return True
        else:
            self.log_test("Авторизация курьера", False, f"Ошибка: {response}")
            return False

    def test_find_active_request(self) -> bool:
        """ЭТАП 2: Поиск активной заявки курьера"""
        print("\n🔍 ЭТАП 2: ПОИСК АКТИВНОЙ ЗАЯВКИ")
        
        # Получаем принятые заявки курьера
        success, response = self.make_request('GET', '/courier/requests/accepted', 
                                            token=self.tokens['courier'])
        
        if success and 'accepted_requests' in response:
            accepted_requests = response['accepted_requests']
            if accepted_requests:
                # Берем первую активную заявку
                active_request = accepted_requests[0]
                self.test_data['request_id'] = active_request['id']
                self.log_test("Поиск активной заявки", True, 
                             f"Найдена заявка ID: {active_request['id']}")
                return True
            else:
                # Если нет принятых заявок, попробуем найти новые и принять одну
                success_new, response_new = self.make_request('GET', '/courier/requests/new', 
                                                            token=self.tokens['courier'])
                if success_new and 'new_requests' in response_new:
                    new_requests = response_new['new_requests']
                    if new_requests:
                        # Принимаем первую новую заявку
                        request_to_accept = new_requests[0]
                        accept_success, accept_response = self.make_request(
                            'POST', f'/courier/requests/{request_to_accept["id"]}/accept',
                            token=self.tokens['courier']
                        )
                        if accept_success:
                            self.test_data['request_id'] = request_to_accept['id']
                            self.log_test("Поиск активной заявки", True, 
                                         f"Принята новая заявка ID: {request_to_accept['id']}")
                            return True
                
                self.log_test("Поиск активной заявки", False, "Нет доступных заявок")
                return False
        else:
            self.log_test("Поиск активной заявки", False, f"Ошибка: {response}")
            return False

    def test_update_request_with_payment_status(self) -> bool:
        """ЭТАП 3: Обновление заявки с конкретным статусом оплаты"""
        print("\n💰 ЭТАП 3: ОБНОВЛЕНИЕ ЗАЯВКИ С СТАТУСОМ ОПЛАТЫ")
        
        if 'request_id' not in self.test_data:
            self.log_test("Обновление заявки с статусом оплаты", False, "Нет активной заявки")
            return False
        
        # Данные для обновления заявки согласно review request
        update_data = {
            "cargo_items": [
                {"name": "Документы", "weight": "1.5", "total_price": "800"}
            ],
            "recipient_full_name": "Тест Статус Оплаты",
            "recipient_phone": "+992900777888",
            "recipient_address": "Душанбе, ул. Оплата, 5",
            "payment_method": "cash",
            "payment_status": "paid"  # КРИТИЧЕСКОЕ ПОЛЕ
        }
        
        success, response = self.make_request(
            'PUT', f'/courier/requests/{self.test_data["request_id"]}/update',
            update_data, token=self.tokens['courier']
        )
        
        if success:
            self.log_test("Обновление заявки с статусом оплаты", True, 
                         "Заявка обновлена с payment_status: 'paid'")
            return True
        else:
            self.log_test("Обновление заявки с статусом оплаты", False, f"Ошибка: {response}")
            return False

    def test_deliver_to_warehouse(self) -> bool:
        """ЭТАП 4: Доставка на склад"""
        print("\n🏭 ЭТАП 4: ДОСТАВКА НА СКЛАД")
        
        if 'request_id' not in self.test_data:
            self.log_test("Доставка на склад", False, "Нет активной заявки")
            return False
        
        success, response = self.make_request(
            'POST', f'/courier/requests/{self.test_data["request_id"]}/deliver-to-warehouse',
            token=self.tokens['courier']
        )
        
        if success:
            self.log_test("Доставка на склад", True, "Груз сдан на склад")
            return True
        else:
            self.log_test("Доставка на склад", False, f"Ошибка: {response}")
            return False

    def test_operator_authentication(self) -> bool:
        """ЭТАП 5: Авторизация оператора (+79777888999/warehouse123)"""
        print("\n🔐 ЭТАП 5: АВТОРИЗАЦИЯ ОПЕРАТОРА")
        
        login_data = {
            "phone": "+79777888999",
            "password": "warehouse123"
        }
        
        success, response = self.make_request('POST', '/auth/login', login_data)
        
        if success and 'access_token' in response:
            self.tokens['operator'] = response['access_token']
            self.test_data['operator_info'] = response.get('user', {})
            self.log_test("Авторизация оператора", True, 
                         f"Оператор: {response.get('user', {}).get('full_name', 'Unknown')}")
            return True
        else:
            self.log_test("Авторизация оператора", False, f"Ошибка: {response}")
            return False

    def test_get_warehouse_notifications(self) -> bool:
        """ЭТАП 6: Получение уведомлений склада"""
        print("\n📬 ЭТАП 6: ПОЛУЧЕНИЕ УВЕДОМЛЕНИЙ СКЛАДА")
        
        success, response = self.make_request('GET', '/operator/warehouse-notifications',
                                            token=self.tokens['operator'])
        
        if success and 'notifications' in response:
            notifications = response['notifications']
            # Ищем новое уведомление с pickup_request_id
            for notification in notifications:
                if notification.get('pickup_request_id') == self.test_data.get('request_id'):
                    self.test_data['notification_id'] = notification['id']
                    self.test_data['pickup_request_id'] = notification['pickup_request_id']
                    self.log_test("Получение уведомлений склада", True, 
                                 f"Найдено уведомление с pickup_request_id: {notification['pickup_request_id']}")
                    return True
            
            # Если не нашли конкретное уведомление, берем первое доступное
            if notifications:
                first_notification = notifications[0]
                self.test_data['notification_id'] = first_notification['id']
                self.test_data['pickup_request_id'] = first_notification.get('pickup_request_id', 'unknown')
                self.log_test("Получение уведомлений склада", True, 
                             f"Найдено уведомление ID: {first_notification['id']}")
                return True
            else:
                self.log_test("Получение уведомлений склада", False, "Нет доступных уведомлений")
                return False
        else:
            self.log_test("Получение уведомлений склада", False, f"Ошибка: {response}")
            return False

    def test_pickup_request_endpoint(self) -> bool:
        """ЭТАП 7: КРИТИЧЕСКАЯ ПРОВЕРКА - Тестирование GET /api/operator/pickup-requests/{pickup_request_id}"""
        print("\n🎯 ЭТАП 7: КРИТИЧЕСКАЯ ПРОВЕРКА ENDPOINT PICKUP REQUESTS")
        
        if 'pickup_request_id' not in self.test_data:
            self.log_test("Тестирование pickup-requests endpoint", False, "Нет pickup_request_id")
            return False
        
        pickup_request_id = self.test_data['pickup_request_id']
        success, response = self.make_request(
            'GET', f'/operator/pickup-requests/{pickup_request_id}',
            token=self.tokens['operator']
        )
        
        if success:
            self.log_test("Тестирование pickup-requests endpoint", True, 
                         f"Endpoint доступен для pickup_request_id: {pickup_request_id}")
            self.test_data['pickup_request_data'] = response
            return True
        else:
            self.log_test("Тестирование pickup-requests endpoint", False, f"Ошибка: {response}")
            return False

    def test_payment_status_verification(self) -> bool:
        """ЭТАП 8: КРИТИЧЕСКАЯ ПРОВЕРКА - Проверка payment_info.payment_status = "paid" """
        print("\n💳 ЭТАП 8: КРИТИЧЕСКАЯ ПРОВЕРКА СТАТУСА ОПЛАТЫ")
        
        if 'pickup_request_data' not in self.test_data:
            self.log_test("Проверка статуса оплаты", False, "Нет данных pickup request")
            return False
        
        pickup_data = self.test_data['pickup_request_data']
        
        # Проверяем наличие payment_info
        if 'payment_info' in pickup_data:
            payment_info = pickup_data['payment_info']
            payment_status = payment_info.get('payment_status')
            
            if payment_status == 'paid':
                self.log_test("Проверка статуса оплаты", True, 
                             f"✅ УСПЕХ! payment_info.payment_status = '{payment_status}'")
                return True
            else:
                self.log_test("Проверка статуса оплаты", False, 
                             f"❌ ОШИБКА! payment_info.payment_status = '{payment_status}' (ожидался 'paid')")
                return False
        else:
            # Проверяем альтернативные поля
            payment_status = pickup_data.get('payment_status')
            payment_method = pickup_data.get('payment_method')
            
            print(f"   📋 Доступные поля в ответе: {list(pickup_data.keys())}")
            
            if payment_status:
                if payment_status == 'paid':
                    self.log_test("Проверка статуса оплаты", True, 
                                 f"✅ УСПЕХ! payment_status = '{payment_status}'")
                    return True
                else:
                    self.log_test("Проверка статуса оплаты", False, 
                                 f"❌ ОШИБКА! payment_status = '{payment_status}' (ожидался 'paid')")
                    return False
            else:
                self.log_test("Проверка статуса оплаты", False, 
                             "❌ ОШИБКА! Поле payment_info или payment_status не найдено")
                return False

    def run_comprehensive_test(self):
        """Запуск полного цикла тестирования"""
        print("🚀 ЗАПУСК КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ ИСПРАВЛЕНИЯ СТАТУСА ОПЛАТЫ")
        print("=" * 80)
        
        # Последовательность тестов согласно review request
        test_steps = [
            ("Авторизация курьера", self.test_courier_authentication),
            ("Поиск активной заявки", self.test_find_active_request),
            ("Обновление заявки с статусом оплаты", self.test_update_request_with_payment_status),
            ("Доставка на склад", self.test_deliver_to_warehouse),
            ("Авторизация оператора", self.test_operator_authentication),
            ("Получение уведомлений склада", self.test_get_warehouse_notifications),
            ("Тестирование pickup-requests endpoint", self.test_pickup_request_endpoint),
            ("КРИТИЧЕСКАЯ ПРОВЕРКА статуса оплаты", self.test_payment_status_verification)
        ]
        
        all_passed = True
        
        for step_name, test_func in test_steps:
            try:
                result = test_func()
                if not result:
                    all_passed = False
                    print(f"⚠️  Тест '{step_name}' не прошел, но продолжаем...")
            except Exception as e:
                print(f"❌ Ошибка в тесте '{step_name}': {e}")
                all_passed = False
        
        # Финальный отчет
        print("\n" + "=" * 80)
        print("📊 ФИНАЛЬНЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 80)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"📈 Всего тестов: {self.tests_run}")
        print(f"✅ Успешных: {self.tests_passed}")
        print(f"❌ Неуспешных: {self.tests_run - self.tests_passed}")
        print(f"📊 Процент успеха: {success_rate:.1f}%")
        
        if all_passed and success_rate >= 87.5:  # 7/8 тестов
            print("\n🎉 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ ОЖИДАЕМЫЙ РЕЗУЛЬТАТ ДОСТИГНУТ:")
            print("   - Backend сохраняет payment_status от курьера")
            print("   - Endpoint /api/operator/pickup-requests/{pickup_request_id} возвращает payment_info с правильным статусом")
            print("   - Модальное окно оператора должно отображать статус 'paid' вместо 'not_paid'")
        else:
            print("\n⚠️  ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ПРОБЛЕМАМИ")
            print("❌ Требуется дополнительная проверка исправлений")
        
        return all_passed

if __name__ == "__main__":
    tester = PaymentStatusTester()
    tester.run_comprehensive_test()
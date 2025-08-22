#!/usr/bin/env python3
"""
КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ ПРОБЛЕМЫ СО СТАТУСОМ ОПЛАТЫ В ЗАЯВКЕ НА ЗАБОР ГРУЗА TAJLINE.TJ

ПОЛНЫЙ WORKFLOW ДЛЯ ДИАГНОСТИКИ:
1. Авторизация оператора (+79777888999/warehouse123)
2. Создание заявки на забор груза оператором
3. Авторизация курьера (+79991234567/courier123)
4. Принятие заявки курьером
5. Забор груза курьером с установкой статуса оплаты
6. Сдача груза на склад курьером (создание уведомления)
7. Получение уведомлений оператором
8. Анализ endpoint /api/operator/pickup-requests/{pickup_request_id}
9. Проверка сохранения payment_status в базе данных
10. Анализ modal_data.payment_info

ЦЕЛЬ: Создать полный цикл и проследить где теряется информация о статусе оплаты
"""

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class ComprehensivePaymentStatusTester:
    def __init__(self, base_url="https://tajline-cargo-7.preview.emergentagent.com"):
        self.base_url = base_url
        self.tokens = {}
        self.users = {}
        self.test_data = {}
        self.tests_run = 0
        self.tests_passed = 0
        
        print(f"🔍 TAJLINE.TJ COMPREHENSIVE PAYMENT STATUS TESTING")
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

    def test_full_payment_status_workflow(self):
        """Test full payment status workflow from creation to operator modal"""
        print("\n🎯 ПОЛНЫЙ WORKFLOW ТЕСТИРОВАНИЯ СТАТУСА ОПЛАТЫ")
        print("   📋 Создание полного цикла для диагностики проблемы со статусом оплаты")
        
        workflow_results = {}
        
        # ЭТАП 1: АВТОРИЗАЦИЯ ОПЕРАТОРА
        print("\n   🔐 ЭТАП 1: АВТОРИЗАЦИЯ ОПЕРАТОРА (+79777888999/warehouse123)...")
        
        operator_login_data = {
            "phone": "+79777888999",
            "password": "warehouse123"
        }
        
        success, login_response = self.run_test(
            "Operator Authentication",
            "POST",
            "/api/auth/login",
            200,
            operator_login_data
        )
        
        if not success or 'access_token' not in login_response:
            print("   ❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как оператор")
            return False
        
        operator_token = login_response['access_token']
        operator_user = login_response.get('user', {})
        
        print(f"   ✅ Авторизация оператора: {operator_user.get('full_name')}")
        print(f"   👑 Роль: {operator_user.get('role')}")
        
        self.tokens['operator'] = operator_token
        self.users['operator'] = operator_user
        workflow_results['operator_auth'] = True
        
        # ЭТАП 2: СОЗДАНИЕ ЗАЯВКИ НА ЗАБОР ГРУЗА ОПЕРАТОРОМ
        print("\n   📝 ЭТАП 2: СОЗДАНИЕ ЗАЯВКИ НА ЗАБОР ГРУЗА ОПЕРАТОРОМ...")
        
        # Генерируем уникальные данные для тестирования
        timestamp = datetime.now().strftime("%H%M%S")
        pickup_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        pickup_request_data = {
            "sender_full_name": f"Тест Отправитель Статус Оплаты {timestamp}",
            "sender_phone": f"+7999{timestamp}",
            "pickup_address": f"Москва, ул. Тестовая Статус Оплаты, {timestamp}",
            "pickup_date": pickup_date,
            "pickup_time_from": "10:00",
            "pickup_time_to": "18:00",
            "route": "moscow_to_tajikistan",
            "courier_fee": 500.0,
            "destination": "Душанбе, ул. Получателя, 1",
            "cargo_description": f"Тестовый груз для проверки статуса оплаты {timestamp}",
            "estimated_weight": 5.0
        }
        
        success, pickup_response = self.run_test(
            "Create Pickup Request by Operator",
            "POST",
            "/api/admin/courier/pickup-request",
            200,
            pickup_request_data,
            operator_token
        )
        
        if not success or 'id' not in pickup_response:
            print("   ❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось создать заявку на забор груза")
            return False
        
        pickup_request_id = pickup_response['id']
        pickup_request_number = pickup_response.get('request_number', pickup_request_id)
        
        print(f"   ✅ Заявка на забор груза создана: {pickup_request_number}")
        print(f"   🆔 ID заявки: {pickup_request_id}")
        
        self.test_data['pickup_request_id'] = pickup_request_id
        self.test_data['pickup_request_number'] = pickup_request_number
        workflow_results['pickup_request_created'] = True
        
        # ЭТАП 3: АВТОРИЗАЦИЯ КУРЬЕРА
        print("\n   🚚 ЭТАП 3: АВТОРИЗАЦИЯ КУРЬЕРА (+79991234567/courier123)...")
        
        courier_login_data = {
            "phone": "+79991234567",
            "password": "courier123"
        }
        
        success, courier_login_response = self.run_test(
            "Courier Authentication",
            "POST",
            "/api/auth/login",
            200,
            courier_login_data
        )
        
        if not success or 'access_token' not in courier_login_response:
            print("   ❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как курьер")
            return False
        
        courier_token = courier_login_response['access_token']
        courier_user = courier_login_response.get('user', {})
        
        print(f"   ✅ Авторизация курьера: {courier_user.get('full_name')}")
        print(f"   👑 Роль: {courier_user.get('role')}")
        
        self.tokens['courier'] = courier_token
        self.users['courier'] = courier_user
        workflow_results['courier_auth'] = True
        
        # ЭТАП 4: ПРИНЯТИЕ ЗАЯВКИ КУРЬЕРОМ
        print("\n   ✅ ЭТАП 4: ПРИНЯТИЕ ЗАЯВКИ КУРЬЕРОМ...")
        
        success, accept_response = self.run_test(
            "Accept Pickup Request by Courier",
            "POST",
            f"/api/courier/requests/{pickup_request_id}/accept",
            200,
            token=courier_token
        )
        
        if not success:
            print("   ❌ КРИТИЧЕСКАЯ ОШИБКА: Курьер не смог принять заявку")
            return False
        
        print(f"   ✅ Заявка принята курьером: {accept_response.get('message', 'Success')}")
        workflow_results['request_accepted'] = True
        
        # ЭТАП 5: ЗАБОР ГРУЗА КУРЬЕРОМ С УСТАНОВКОЙ СТАТУСА ОПЛАТЫ
        print("\n   💰 ЭТАП 5: ЗАБОР ГРУЗА КУРЬЕРОМ С УСТАНОВКОЙ СТАТУСА ОПЛАТЫ...")
        
        # Сначала выполним pickup
        success, pickup_cargo_response = self.run_test(
            "Pickup Cargo by Courier",
            "POST",
            f"/api/courier/requests/{pickup_request_id}/pickup",
            200,
            token=courier_token
        )
        
        if not success:
            print("   ❌ КРИТИЧЕСКАЯ ОШИБКА: Курьер не смог забрать груз")
            return False
        
        print(f"   ✅ Груз забран курьером: {pickup_cargo_response.get('message', 'Success')}")
        
        # Теперь попробуем обновить заявку с информацией об оплате
        payment_update_data = {
            "cargo_items": [
                {
                    "name": f"Тестовый груз статус оплаты {timestamp}",
                    "weight": "5.0",
                    "total_price": "2500"
                }
            ],
            "recipient_full_name": f"Получатель Тест {timestamp}",
            "recipient_phone": f"+992999{timestamp}",
            "recipient_address": "Душанбе, ул. Получателя, 1",
            "delivery_method": "pickup",
            "payment_method": "cash",
            "payment_status": "paid",  # КРИТИЧЕСКИ ВАЖНО: устанавливаем статус оплаты
            "payment_amount": 2500.0,
            "courier_notes": f"Оплата получена наличными {timestamp}"
        }
        
        success, update_response = self.run_test(
            "Update Request with Payment Status by Courier",
            "PUT",
            f"/api/courier/requests/{pickup_request_id}/update",
            200,
            payment_update_data,
            courier_token
        )
        
        if success:
            print("   ✅ Заявка обновлена курьером с информацией об оплате")
            print(f"   💰 Статус оплаты установлен: paid")
            print(f"   💳 Способ оплаты: cash")
            print(f"   💵 Сумма: 2500.0")
            workflow_results['payment_status_set'] = True
        else:
            print("   ❌ ОШИБКА: Не удалось обновить заявку с информацией об оплате")
            workflow_results['payment_status_set'] = False
        
        # ЭТАП 6: СДАЧА ГРУЗА НА СКЛАД КУРЬЕРОМ (СОЗДАНИЕ УВЕДОМЛЕНИЯ)
        print("\n   🏭 ЭТАП 6: СДАЧА ГРУЗА НА СКЛАД КУРЬЕРОМ...")
        
        success, deliver_response = self.run_test(
            "Deliver Cargo to Warehouse by Courier",
            "POST",
            f"/api/courier/requests/{pickup_request_id}/deliver-to-warehouse",
            200,
            token=courier_token
        )
        
        if not success:
            print("   ❌ КРИТИЧЕСКАЯ ОШИБКА: Курьер не смог сдать груз на склад")
            return False
        
        print(f"   ✅ Груз сдан на склад: {deliver_response.get('message', 'Success')}")
        
        # Получаем notification_id из ответа
        notification_id = deliver_response.get('notification_id')
        if notification_id:
            print(f"   📬 Создано уведомление: {notification_id}")
            self.test_data['notification_id'] = notification_id
        
        workflow_results['cargo_delivered'] = True
        
        # ЭТАП 7: ПОЛУЧЕНИЕ УВЕДОМЛЕНИЙ ОПЕРАТОРОМ
        print("\n   📬 ЭТАП 7: ПОЛУЧЕНИЕ УВЕДОМЛЕНИЙ ОПЕРАТОРОМ...")
        
        success, notifications_response = self.run_test(
            "Get Warehouse Notifications by Operator",
            "GET",
            "/api/operator/warehouse-notifications",
            200,
            token=operator_token
        )
        
        if not success:
            print("   ❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить уведомления")
            return False
        
        notifications = notifications_response if isinstance(notifications_response, list) else []
        print(f"   ✅ Получено {len(notifications)} уведомлений")
        
        # Найдем наше уведомление
        our_notification = None
        for notification in notifications:
            if notification.get('pickup_request_id') == pickup_request_id:
                our_notification = notification
                break
        
        if our_notification:
            print(f"   ✅ Найдено наше уведомление: {our_notification.get('id')}")
            print(f"   📋 Статус уведомления: {our_notification.get('status')}")
            
            # Проверим есть ли информация об оплате в уведомлении
            payment_fields_in_notification = {}
            for key, value in our_notification.items():
                if 'payment' in key.lower() or 'pay' in key.lower():
                    payment_fields_in_notification[key] = value
                    print(f"   💰 {key}: {value}")
            
            if payment_fields_in_notification:
                print("   ✅ Информация об оплате найдена в уведомлении")
                workflow_results['payment_in_notification'] = True
            else:
                print("   ❌ ПРОБЛЕМА: Информация об оплате НЕ найдена в уведомлении")
                workflow_results['payment_in_notification'] = False
            
            self.test_data['notification'] = our_notification
        else:
            print("   ❌ КРИТИЧЕСКАЯ ОШИБКА: Наше уведомление не найдено")
            workflow_results['notification_found'] = False
            return False
        
        workflow_results['notification_found'] = True
        
        # ЭТАП 8: АНАЛИЗ ENDPOINT /api/operator/pickup-requests/{pickup_request_id}
        print("\n   🎯 ЭТАП 8: АНАЛИЗ ENDPOINT /api/operator/pickup-requests/{pickup_request_id}...")
        
        success, pickup_request_details = self.run_test(
            f"Get Pickup Request Details ({pickup_request_id})",
            "GET",
            f"/api/operator/pickup-requests/{pickup_request_id}",
            200,
            token=operator_token
        )
        
        if success:
            print("   ✅ Endpoint /api/operator/pickup-requests/{pickup_request_id} работает")
            
            # КРИТИЧЕСКИЙ АНАЛИЗ ПОЛЕЙ ОПЛАТЫ
            print("\n   🔍 КРИТИЧЕСКИЙ АНАЛИЗ ПОЛЕЙ ОПЛАТЫ:")
            
            # Проверка payment_status
            payment_status = pickup_request_details.get('payment_status')
            print(f"   ❓ Есть ли поле payment_status? {payment_status is not None}")
            if payment_status is not None:
                print(f"   💰 Значение payment_status: {payment_status}")
                if payment_status == 'paid':
                    print("   ✅ Статус оплаты корректный (paid)")
                    workflow_results['correct_payment_status'] = True
                else:
                    print(f"   ❌ ПРОБЛЕМА: Неожиданный статус оплаты: {payment_status}")
                    workflow_results['correct_payment_status'] = False
            else:
                print("   ❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Поле payment_status ОТСУТСТВУЕТ")
                workflow_results['has_payment_status'] = False
            
            # Проверка payment_method
            payment_method = pickup_request_details.get('payment_method')
            print(f"   ❓ Есть ли поле payment_method? {payment_method is not None}")
            if payment_method is not None:
                print(f"   💳 Значение payment_method: {payment_method}")
                if payment_method == 'cash':
                    print("   ✅ Способ оплаты корректный (cash)")
                    workflow_results['correct_payment_method'] = True
                else:
                    print(f"   ❌ ПРОБЛЕМА: Неожиданный способ оплаты: {payment_method}")
                    workflow_results['correct_payment_method'] = False
            else:
                print("   ❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Поле payment_method ОТСУТСТВУЕТ")
                workflow_results['has_payment_method'] = False
            
            # Проверка modal_data
            modal_data = pickup_request_details.get('modal_data', {})
            print(f"   ❓ Есть ли modal_data? {bool(modal_data)}")
            if modal_data:
                print(f"   📋 Ключи modal_data: {list(modal_data.keys())}")
                
                # Проверка payment_info в modal_data
                payment_info = modal_data.get('payment_info')
                print(f"   ❓ Есть ли modal_data.payment_info? {payment_info is not None}")
                if payment_info:
                    print(f"   📊 modal_data.payment_info: {payment_info}")
                    
                    if isinstance(payment_info, dict) and 'payment_status' in payment_info:
                        modal_payment_status = payment_info['payment_status']
                        print(f"   ✅ modal_data.payment_info.payment_status: {modal_payment_status}")
                        workflow_results['modal_payment_status'] = True
                    else:
                        print("   ❌ ПРОБЛЕМА: modal_data.payment_info НЕ содержит payment_status")
                        workflow_results['modal_payment_status'] = False
                else:
                    print("   ❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: modal_data.payment_info ОТСУТСТВУЕТ")
                    workflow_results['has_modal_payment_info'] = False
            else:
                print("   ❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: modal_data ОТСУТСТВУЕТ")
                workflow_results['has_modal_data'] = False
            
            # Поиск всех полей связанных с оплатой
            print("\n   🔍 ВСЕ ПОЛЯ СВЯЗАННЫЕ С ОПЛАТОЙ:")
            payment_related_fields = {}
            for key, value in pickup_request_details.items():
                if 'payment' in key.lower() or 'pay' in key.lower():
                    payment_related_fields[key] = value
                    print(f"   💰 {key}: {value}")
            
            if not payment_related_fields:
                print("   ❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: НЕ НАЙДЕНО полей связанных с оплатой")
                workflow_results['has_any_payment_fields'] = False
            else:
                print(f"   ✅ Найдено {len(payment_related_fields)} полей связанных с оплатой")
                workflow_results['has_any_payment_fields'] = True
            
            workflow_results['pickup_request_analysis'] = {
                'endpoint_works': True,
                'payment_fields_found': payment_related_fields,
                'has_payment_status': payment_status is not None,
                'payment_status_value': payment_status,
                'has_payment_method': payment_method is not None,
                'payment_method_value': payment_method,
                'has_modal_data': bool(modal_data),
                'has_modal_payment_info': payment_info is not None if modal_data else False
            }
            
        else:
            print("   ❌ КРИТИЧЕСКАЯ ОШИБКА: Endpoint /api/operator/pickup-requests/{pickup_request_id} не работает")
            workflow_results['pickup_request_analysis'] = {'endpoint_works': False}
            return False
        
        # ЭТАП 9: ПРОВЕРКА СОХРАНЕНИЯ В БАЗЕ ДАННЫХ (через API)
        print("\n   💾 ЭТАП 9: ПРОВЕРКА СОХРАНЕНИЯ В БАЗЕ ДАННЫХ...")
        
        # Проверим через API курьера - сохранилась ли информация об оплате
        success, courier_history = self.run_test(
            "Check Courier Request History for Payment Info",
            "GET",
            "/api/courier/requests/history",
            200,
            token=courier_token
        )
        
        if success:
            history_items = courier_history.get('items', []) if isinstance(courier_history, dict) else courier_history if isinstance(courier_history, list) else []
            
            # Найдем нашу заявку в истории
            our_request_in_history = None
            for item in history_items:
                if item.get('id') == pickup_request_id:
                    our_request_in_history = item
                    break
            
            if our_request_in_history:
                print("   ✅ Наша заявка найдена в истории курьера")
                
                # Проверим сохранилась ли информация об оплате
                history_payment_fields = {}
                for key, value in our_request_in_history.items():
                    if 'payment' in key.lower() or 'pay' in key.lower():
                        history_payment_fields[key] = value
                        print(f"   💰 История - {key}: {value}")
                
                if history_payment_fields:
                    print("   ✅ Информация об оплате сохранена в истории курьера")
                    workflow_results['payment_saved_in_db'] = True
                else:
                    print("   ❌ ПРОБЛЕМА: Информация об оплате НЕ сохранена в истории курьера")
                    workflow_results['payment_saved_in_db'] = False
            else:
                print("   ❌ ПРОБЛЕМА: Наша заявка НЕ найдена в истории курьера")
                workflow_results['request_in_history'] = False
        else:
            print("   ❌ Не удалось получить историю курьера")
        
        return workflow_results

    def analyze_workflow_results(self, results):
        """Analyze workflow results and provide detailed diagnosis"""
        print("\n" + "="*80)
        print("📊 ДЕТАЛЬНЫЙ АНАЛИЗ РЕЗУЛЬТАТОВ WORKFLOW")
        print("="*80)
        
        # Подсчет успешных этапов
        successful_stages = 0
        total_stages = 0
        
        stages = [
            ('operator_auth', 'Авторизация оператора'),
            ('pickup_request_created', 'Создание заявки на забор груза'),
            ('courier_auth', 'Авторизация курьера'),
            ('request_accepted', 'Принятие заявки курьером'),
            ('payment_status_set', 'Установка статуса оплаты курьером'),
            ('cargo_delivered', 'Сдача груза на склад'),
            ('notification_found', 'Создание уведомления оператору'),
            ('payment_in_notification', 'Информация об оплате в уведомлении'),
        ]
        
        print("\n🔍 АНАЛИЗ ЭТАПОВ WORKFLOW:")
        for stage_key, stage_name in stages:
            total_stages += 1
            if results.get(stage_key, False):
                successful_stages += 1
                print(f"   ✅ {stage_name}")
            else:
                print(f"   ❌ {stage_name}")
        
        workflow_success_rate = (successful_stages / total_stages * 100) if total_stages > 0 else 0
        print(f"\n📈 Успешность workflow: {successful_stages}/{total_stages} ({workflow_success_rate:.1f}%)")
        
        # Анализ критических проблем
        print("\n🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ:")
        
        problems_found = []
        
        # Проверка endpoint анализа
        pickup_analysis = results.get('pickup_request_analysis', {})
        if pickup_analysis.get('endpoint_works', False):
            print("   ✅ Endpoint /api/operator/pickup-requests/{id} работает")
            
            if not pickup_analysis.get('has_payment_status', False):
                problems_found.append("❌ Поле payment_status ОТСУТСТВУЕТ в endpoint")
            
            if not pickup_analysis.get('has_payment_method', False):
                problems_found.append("❌ Поле payment_method ОТСУТСТВУЕТ в endpoint")
            
            if not pickup_analysis.get('has_modal_data', False):
                problems_found.append("❌ modal_data ОТСУТСТВУЕТ в endpoint")
            
            if not pickup_analysis.get('has_modal_payment_info', False):
                problems_found.append("❌ modal_data.payment_info ОТСУТСТВУЕТ в endpoint")
        else:
            problems_found.append("❌ Endpoint /api/operator/pickup-requests/{id} НЕ РАБОТАЕТ")
        
        # Проверка сохранения данных
        if not results.get('payment_status_set', False):
            problems_found.append("❌ Курьер НЕ СМОГ установить статус оплаты")
        
        if not results.get('payment_in_notification', False):
            problems_found.append("❌ Информация об оплате НЕ передается в уведомления")
        
        if not results.get('payment_saved_in_db', False):
            problems_found.append("❌ Информация об оплате НЕ сохраняется в базе данных")
        
        # Вывод проблем
        if problems_found:
            print(f"   Найдено {len(problems_found)} критических проблем:")
            for i, problem in enumerate(problems_found, 1):
                print(f"   {i}. {problem}")
        else:
            print("   ✅ Критические проблемы не обнаружены")
        
        # Рекомендации по исправлению
        print("\n💡 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ:")
        
        recommendations = []
        
        if not pickup_analysis.get('has_payment_status', False):
            recommendations.append("Добавить поле payment_status в endpoint /api/operator/pickup-requests/{id}")
        
        if not pickup_analysis.get('has_payment_method', False):
            recommendations.append("Добавить поле payment_method в endpoint /api/operator/pickup-requests/{id}")
        
        if not pickup_analysis.get('has_modal_payment_info', False):
            recommendations.append("Добавить payment_info в modal_data для модального окна оператора")
        
        if not results.get('payment_in_notification', False):
            recommendations.append("Обеспечить передачу информации об оплате в уведомления склада")
        
        if not results.get('payment_saved_in_db', False):
            recommendations.append("Исправить сохранение информации об оплате в базе данных")
        
        recommendations.append("Проверить workflow передачи данных от курьера к оператору")
        recommendations.append("Добавить валидацию сохранения payment_status при обновлении заявки курьером")
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        else:
            print("   ✅ Дополнительные рекомендации не требуются")
        
        # Итоговая оценка
        print("\n🎯 ИТОГОВАЯ ОЦЕНКА:")
        
        if workflow_success_rate >= 80 and len(problems_found) == 0:
            print("   🎉 ОТЛИЧНО: Система работает корректно, проблемы со статусом оплаты не обнаружены")
            return True
        elif workflow_success_rate >= 60 and len(problems_found) <= 2:
            print("   ⚠️  УДОВЛЕТВОРИТЕЛЬНО: Система работает, но есть минорные проблемы")
            return True
        else:
            print("   ❌ НЕУДОВЛЕТВОРИТЕЛЬНО: Обнаружены критические проблемы со статусом оплаты")
            print("   🔧 ТРЕБУЕТСЯ НЕМЕДЛЕННОЕ ИСПРАВЛЕНИЕ")
            return False

    def run_comprehensive_test(self):
        """Run comprehensive payment status test"""
        print("🚀 ЗАПУСК КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ СТАТУСА ОПЛАТЫ")
        
        try:
            results = self.test_full_payment_status_workflow()
            
            if results:
                success = self.analyze_workflow_results(results)
                
                print(f"\n📊 СТАТИСТИКА ТЕСТИРОВАНИЯ:")
                print(f"   Всего тестов: {self.tests_run}")
                print(f"   Успешных: {self.tests_passed}")
                print(f"   Процент успеха: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
                
                return success
            else:
                print("❌ Комплексное тестирование не удалось завершить")
                return False
                
        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА в комплексном тестировании: {str(e)}")
            return False

if __name__ == "__main__":
    tester = ComprehensivePaymentStatusTester()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО")
        print("📋 Проверьте результаты выше для понимания состояния системы статуса оплаты")
    else:
        print("\n❌ КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ ВЫЯВИЛО КРИТИЧЕСКИЕ ПРОБЛЕМЫ")
        print("🔍 Проверьте анализ выше для диагностики и исправления проблем")
    
    sys.exit(0 if success else 1)
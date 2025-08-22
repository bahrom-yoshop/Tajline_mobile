#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ПРОБЛЕМЫ СО СТАТУСОМ ОПЛАТЫ В ЗАЯВКЕ НА ЗАБОР ГРУЗА TAJLINE.TJ

ДИАГНОСТИКА ПРОБЛЕМЫ СТАТУСА ОПЛАТЫ:
1. Авторизация оператора (+79777888999/warehouse123)
2. Получить уведомления: GET /api/operator/warehouse-notifications
3. Найти уведомление с pickup_request_id
4. Протестировать GET /api/operator/pickup-requests/{pickup_request_id} и проанализировать:
   - Есть ли поле payment_status в response?
   - Какое значение payment_status (paid, not_paid, partially_paid)?
   - Сохраняется ли статус оплаты который выбирал курьер?
   - Есть ли поле payment_method в данных?

ДОПОЛНИТЕЛЬНАЯ ДИАГНОСТИКА:
5. Найти заявку курьера где был установлен статус оплаты
6. Проверить прямо в базе данных - сохраняется ли payment_status от курьера
7. Проверить что modal_data.payment_info содержит payment_status

КЛЮЧЕВЫЕ ВОПРОСЫ:
- Сохраняет ли backend payment_status когда курьер обновляет заявку?
- Передается ли payment_status в endpoint /api/operator/pickup-requests/{pickup_request_id}?
- Правильно ли структурированы данные payment_info в modal_data?
- Отображается ли статус оплаты в payment_info секции?

ЦЕЛЬ: Понять почему статус оплаты курьера не отображается в модальном окне оператора и где теряются эти данные.
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class PaymentStatusInvestigationTester:
    def __init__(self, base_url="https://tajline-cargo-7.preview.emergentagent.com"):
        self.base_url = base_url
        self.tokens = {}
        self.users = {}
        self.tests_run = 0
        self.tests_passed = 0
        
        print(f"🔍 TAJLINE.TJ PAYMENT STATUS INVESTIGATION")
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

    def investigate_payment_status_issue(self):
        """Investigate payment status issue in pickup requests according to review request"""
        print("\n🎯 КРИТИЧЕСКОЕ РАССЛЕДОВАНИЕ ПРОБЛЕМЫ СО СТАТУСОМ ОПЛАТЫ В ЗАЯВКЕ НА ЗАБОР ГРУЗА")
        print("   📋 Исследование проблемы со статусом оплаты в заявке на забор груза TAJLINE.TJ")
        
        all_success = True
        investigation_results = {}
        
        # ЭТАП 1: АВТОРИЗАЦИЯ ОПЕРАТОРА (+79777888999/warehouse123)
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
        operator_role = operator_user.get('role')
        operator_name = operator_user.get('full_name')
        
        print(f"   ✅ Авторизация успешна: {operator_name}")
        print(f"   👑 Роль: {operator_role}")
        print(f"   📞 Телефон: {operator_user.get('phone')}")
        
        investigation_results['operator_auth'] = {
            'success': True,
            'operator_name': operator_name,
            'operator_role': operator_role
        }
        
        # ЭТАП 2: ПОЛУЧИТЬ УВЕДОМЛЕНИЯ: GET /api/operator/warehouse-notifications
        print("\n   📬 ЭТАП 2: ПОЛУЧИТЬ УВЕДОМЛЕНИЯ СКЛАДА...")
        
        success, notifications_response = self.run_test(
            "Get Warehouse Notifications",
            "GET",
            "/api/operator/warehouse-notifications",
            200,
            token=operator_token
        )
        
        if not success:
            print("   ❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить уведомления склада")
            return False
        
        notifications = notifications_response if isinstance(notifications_response, list) else []
        notification_count = len(notifications)
        
        print(f"   ✅ Получено {notification_count} уведомлений склада")
        
        investigation_results['notifications'] = {
            'total_count': notification_count,
            'notifications': notifications
        }
        
        # ЭТАП 3: НАЙТИ УВЕДОМЛЕНИЕ С pickup_request_id
        print("\n   🔍 ЭТАП 3: ПОИСК УВЕДОМЛЕНИЯ С pickup_request_id...")
        
        pickup_notifications = []
        for notification in notifications:
            if 'pickup_request_id' in notification and notification.get('pickup_request_id'):
                pickup_notifications.append(notification)
                print(f"   📋 Найдено уведомление с pickup_request_id: {notification.get('pickup_request_id')}")
                print(f"      - ID уведомления: {notification.get('id')}")
                print(f"      - Статус: {notification.get('status')}")
                print(f"      - Сообщение: {notification.get('message', '')[:100]}...")
        
        if not pickup_notifications:
            print("   ⚠️  НЕ НАЙДЕНО уведомлений с pickup_request_id")
            print("   ℹ️  Это может означать что:")
            print("      1) Нет активных заявок на забор груза")
            print("      2) Курьеры еще не сдали грузы на склад")
            print("      3) Уведомления уже обработаны")
            
            # Попробуем найти любые уведомления для анализа
            if notifications:
                sample_notification = notifications[0]
                print(f"   📋 Пример уведомления для анализа структуры:")
                print(f"      - ID: {sample_notification.get('id')}")
                print(f"      - Тип: {sample_notification.get('type', 'unknown')}")
                print(f"      - Статус: {sample_notification.get('status')}")
                
                # Проверим есть ли поля связанные с оплатой
                payment_fields = ['payment_status', 'payment_method', 'payment_info']
                found_payment_fields = []
                for field in payment_fields:
                    if field in sample_notification:
                        found_payment_fields.append(field)
                        print(f"      - {field}: {sample_notification.get(field)}")
                
                if found_payment_fields:
                    print(f"   ✅ Найдены поля оплаты в уведомлении: {found_payment_fields}")
                else:
                    print("   ❌ НЕ НАЙДЕНЫ поля оплаты в уведомлении")
        else:
            print(f"   ✅ Найдено {len(pickup_notifications)} уведомлений с pickup_request_id")
        
        investigation_results['pickup_notifications'] = pickup_notifications
        
        # ЭТАП 4: ПРОТЕСТИРОВАТЬ GET /api/operator/pickup-requests/{pickup_request_id}
        print("\n   🎯 ЭТАП 4: АНАЛИЗ ENDPOINT /api/operator/pickup-requests/{pickup_request_id}...")
        
        pickup_request_analysis = []
        
        if pickup_notifications:
            for notification in pickup_notifications[:3]:  # Анализируем первые 3 уведомления
                pickup_request_id = notification.get('pickup_request_id')
                print(f"\n   📋 Анализ заявки на забор груза: {pickup_request_id}")
                
                success, pickup_request_response = self.run_test(
                    f"Get Pickup Request Details ({pickup_request_id})",
                    "GET",
                    f"/api/operator/pickup-requests/{pickup_request_id}",
                    200,
                    token=operator_token
                )
                
                if success:
                    print("   ✅ Endpoint /api/operator/pickup-requests/{pickup_request_id} работает")
                    
                    # КРИТИЧЕСКИЙ АНАЛИЗ: Есть ли поле payment_status в response?
                    payment_status = pickup_request_response.get('payment_status')
                    payment_method = pickup_request_response.get('payment_method')
                    payment_info = pickup_request_response.get('payment_info')
                    modal_data = pickup_request_response.get('modal_data', {})
                    
                    analysis = {
                        'pickup_request_id': pickup_request_id,
                        'endpoint_works': True,
                        'has_payment_status': payment_status is not None,
                        'payment_status_value': payment_status,
                        'has_payment_method': payment_method is not None,
                        'payment_method_value': payment_method,
                        'has_payment_info': payment_info is not None,
                        'payment_info_value': payment_info,
                        'has_modal_data': bool(modal_data),
                        'modal_data_keys': list(modal_data.keys()) if modal_data else []
                    }
                    
                    print(f"   🔍 КРИТИЧЕСКИЙ АНАЛИЗ ЗАЯВКИ {pickup_request_id}:")
                    print(f"      ❓ Есть ли поле payment_status? {analysis['has_payment_status']}")
                    if analysis['has_payment_status']:
                        print(f"      💰 Значение payment_status: {analysis['payment_status_value']}")
                    else:
                        print("      ❌ ПРОБЛЕМА: Поле payment_status ОТСУТСТВУЕТ в ответе")
                    
                    print(f"      ❓ Есть ли поле payment_method? {analysis['has_payment_method']}")
                    if analysis['has_payment_method']:
                        print(f"      💳 Значение payment_method: {analysis['payment_method_value']}")
                    else:
                        print("      ❌ ПРОБЛЕМА: Поле payment_method ОТСУТСТВУЕТ в ответе")
                    
                    print(f"      ❓ Есть ли поле payment_info? {analysis['has_payment_info']}")
                    if analysis['has_payment_info']:
                        print(f"      📊 Значение payment_info: {analysis['payment_info_value']}")
                    else:
                        print("      ❌ ПРОБЛЕМА: Поле payment_info ОТСУТСТВУЕТ в ответе")
                    
                    print(f"      ❓ Есть ли modal_data? {analysis['has_modal_data']}")
                    if analysis['has_modal_data']:
                        print(f"      📋 Ключи modal_data: {analysis['modal_data_keys']}")
                        
                        # Проверим modal_data.payment_info
                        modal_payment_info = modal_data.get('payment_info')
                        if modal_payment_info:
                            print(f"      ✅ modal_data.payment_info найден: {modal_payment_info}")
                            
                            # Проверим содержит ли payment_status
                            if isinstance(modal_payment_info, dict) and 'payment_status' in modal_payment_info:
                                print(f"      ✅ modal_data.payment_info содержит payment_status: {modal_payment_info['payment_status']}")
                                analysis['modal_payment_info_has_status'] = True
                                analysis['modal_payment_status'] = modal_payment_info['payment_status']
                            else:
                                print("      ❌ ПРОБЛЕМА: modal_data.payment_info НЕ содержит payment_status")
                                analysis['modal_payment_info_has_status'] = False
                        else:
                            print("      ❌ ПРОБЛЕМА: modal_data.payment_info ОТСУТСТВУЕТ")
                            analysis['modal_payment_info_has_status'] = False
                    else:
                        print("      ❌ ПРОБЛЕМА: modal_data ОТСУТСТВУЕТ в ответе")
                    
                    # Проверим все поля ответа для поиска информации об оплате
                    print(f"      🔍 Все поля в ответе: {list(pickup_request_response.keys())}")
                    
                    # Поиск полей содержащих 'payment' или 'pay'
                    payment_related_fields = []
                    for key in pickup_request_response.keys():
                        if 'payment' in key.lower() or 'pay' in key.lower():
                            payment_related_fields.append(key)
                            print(f"      💰 Поле связанное с оплатой: {key} = {pickup_request_response[key]}")
                    
                    analysis['payment_related_fields'] = payment_related_fields
                    
                    pickup_request_analysis.append(analysis)
                    
                else:
                    print(f"   ❌ ОШИБКА: Endpoint /api/operator/pickup-requests/{pickup_request_id} не работает")
                    pickup_request_analysis.append({
                        'pickup_request_id': pickup_request_id,
                        'endpoint_works': False,
                        'error': 'Endpoint failed'
                    })
        else:
            print("   ⚠️  Нет pickup_request_id для анализа endpoint")
        
        investigation_results['pickup_request_analysis'] = pickup_request_analysis
        
        # ЭТАП 5: НАЙТИ ЗАЯВКУ КУРЬЕРА ГДЕ БЫЛ УСТАНОВЛЕН СТАТУС ОПЛАТЫ
        print("\n   🚚 ЭТАП 5: ПОИСК ЗАЯВОК КУРЬЕРА СО СТАТУСОМ ОПЛАТЫ...")
        
        # Попробуем авторизоваться как курьер для проверки
        courier_login_data = {
            "phone": "+79991234567",
            "password": "courier123"
        }
        
        success, courier_login_response = self.run_test(
            "Courier Authentication for Investigation",
            "POST",
            "/api/auth/login",
            200,
            courier_login_data
        )
        
        if success and 'access_token' in courier_login_response:
            courier_token = courier_login_response['access_token']
            courier_user = courier_login_response.get('user', {})
            
            print(f"   ✅ Авторизация курьера: {courier_user.get('full_name')}")
            
            # Получим заявки курьера для анализа
            success, courier_requests = self.run_test(
                "Get Courier Requests History",
                "GET",
                "/api/courier/requests/history",
                200,
                token=courier_token
            )
            
            if success:
                requests_list = courier_requests.get('items', []) if isinstance(courier_requests, dict) else courier_requests if isinstance(courier_requests, list) else []
                print(f"   📋 Найдено {len(requests_list)} заявок в истории курьера")
                
                # Анализируем заявки на наличие информации об оплате
                courier_payment_analysis = []
                for request in requests_list[:3]:  # Анализируем первые 3 заявки
                    request_id = request.get('id')
                    request_type = request.get('request_type', 'unknown')
                    
                    print(f"   🔍 Анализ заявки курьера: {request_id} (тип: {request_type})")
                    
                    # Поиск полей оплаты в заявке курьера
                    payment_fields_found = {}
                    for key, value in request.items():
                        if 'payment' in key.lower() or 'pay' in key.lower():
                            payment_fields_found[key] = value
                            print(f"      💰 {key}: {value}")
                    
                    courier_payment_analysis.append({
                        'request_id': request_id,
                        'request_type': request_type,
                        'payment_fields': payment_fields_found
                    })
                
                investigation_results['courier_payment_analysis'] = courier_payment_analysis
                
                if not any(analysis['payment_fields'] for analysis in courier_payment_analysis):
                    print("   ❌ ПРОБЛЕМА: НЕ НАЙДЕНЫ поля оплаты в заявках курьера")
                else:
                    print("   ✅ Найдены поля оплаты в заявках курьера")
            else:
                print("   ❌ Не удалось получить историю заявок курьера")
        else:
            print("   ❌ Не удалось авторизоваться как курьер для анализа")
        
        # ЭТАП 6: ОБЩИЙ АНАЛИЗ И ВЫВОДЫ
        print("\n   📊 ЭТАП 6: ОБЩИЙ АНАЛИЗ И ВЫВОДЫ...")
        
        # Подсчет проблем
        problems_found = []
        
        # Проверка 1: Есть ли payment_status в pickup requests
        if pickup_request_analysis:
            requests_without_payment_status = [r for r in pickup_request_analysis if not r.get('has_payment_status', False)]
            if requests_without_payment_status:
                problems_found.append(f"❌ {len(requests_without_payment_status)} заявок БЕЗ поля payment_status")
            
            requests_without_payment_method = [r for r in pickup_request_analysis if not r.get('has_payment_method', False)]
            if requests_without_payment_method:
                problems_found.append(f"❌ {len(requests_without_payment_method)} заявок БЕЗ поля payment_method")
            
            requests_without_modal_payment_info = [r for r in pickup_request_analysis if not r.get('modal_payment_info_has_status', False)]
            if requests_without_modal_payment_info:
                problems_found.append(f"❌ {len(requests_without_modal_payment_info)} заявок БЕЗ modal_data.payment_info.payment_status")
        
        # Вывод результатов
        print("\n   🎯 РЕЗУЛЬТАТЫ РАССЛЕДОВАНИЯ:")
        
        if problems_found:
            print("   ❌ НАЙДЕНЫ КРИТИЧЕСКИЕ ПРОБЛЕМЫ:")
            for problem in problems_found:
                print(f"      {problem}")
        else:
            print("   ✅ Критические проблемы не обнаружены")
        
        # Рекомендации
        print("\n   💡 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ:")
        
        if pickup_request_analysis:
            missing_payment_status = any(not r.get('has_payment_status', False) for r in pickup_request_analysis)
            missing_payment_method = any(not r.get('has_payment_method', False) for r in pickup_request_analysis)
            missing_modal_payment_info = any(not r.get('modal_payment_info_has_status', False) for r in pickup_request_analysis)
            
            if missing_payment_status:
                print("   🔧 1. Добавить поле payment_status в endpoint /api/operator/pickup-requests/{pickup_request_id}")
            
            if missing_payment_method:
                print("   🔧 2. Добавить поле payment_method в endpoint /api/operator/pickup-requests/{pickup_request_id}")
            
            if missing_modal_payment_info:
                print("   🔧 3. Добавить payment_status в modal_data.payment_info для модального окна")
            
            print("   🔧 4. Убедиться что статус оплаты от курьера сохраняется в базе данных")
            print("   🔧 5. Проверить что данные передаются из courier_requests в pickup_requests")
        else:
            print("   🔧 1. Создать тестовые заявки на забор груза для диагностики")
            print("   🔧 2. Убедиться что курьеры могут устанавливать статус оплаты")
            print("   🔧 3. Проверить workflow от курьера до оператора")
        
        investigation_results['problems_found'] = problems_found
        investigation_results['recommendations'] = [
            "Добавить поля payment_status и payment_method в endpoint pickup-requests",
            "Обеспечить сохранение статуса оплаты от курьера",
            "Добавить payment_info в modal_data для модального окна",
            "Проверить workflow передачи данных от курьера к оператору"
        ]
        
        return investigation_results

    def run_full_investigation(self):
        """Run full payment status investigation"""
        print("🚀 ЗАПУСК ПОЛНОГО РАССЛЕДОВАНИЯ ПРОБЛЕМЫ СО СТАТУСОМ ОПЛАТЫ")
        
        try:
            results = self.investigate_payment_status_issue()
            
            print("\n" + "="*80)
            print("📋 ИТОГОВЫЙ ОТЧЕТ РАССЛЕДОВАНИЯ")
            print("="*80)
            
            if results:
                # Operator authentication
                if results.get('operator_auth', {}).get('success'):
                    print("✅ Авторизация оператора: УСПЕШНО")
                else:
                    print("❌ Авторизация оператора: НЕУДАЧНО")
                
                # Notifications analysis
                notification_count = results.get('notifications', {}).get('total_count', 0)
                pickup_notification_count = len(results.get('pickup_notifications', []))
                print(f"📬 Уведомления склада: {notification_count} всего, {pickup_notification_count} с pickup_request_id")
                
                # Pickup request analysis
                pickup_analysis = results.get('pickup_request_analysis', [])
                if pickup_analysis:
                    working_endpoints = len([r for r in pickup_analysis if r.get('endpoint_works')])
                    with_payment_status = len([r for r in pickup_analysis if r.get('has_payment_status')])
                    with_payment_method = len([r for r in pickup_analysis if r.get('has_payment_method')])
                    with_modal_payment_info = len([r for r in pickup_analysis if r.get('modal_payment_info_has_status')])
                    
                    print(f"🎯 Анализ pickup requests: {working_endpoints}/{len(pickup_analysis)} endpoints работают")
                    print(f"💰 С payment_status: {with_payment_status}/{len(pickup_analysis)}")
                    print(f"💳 С payment_method: {with_payment_method}/{len(pickup_analysis)}")
                    print(f"📋 С modal payment_info: {with_modal_payment_info}/{len(pickup_analysis)}")
                else:
                    print("⚠️  Pickup requests не найдены для анализа")
                
                # Problems summary
                problems = results.get('problems_found', [])
                if problems:
                    print(f"\n❌ НАЙДЕНО {len(problems)} КРИТИЧЕСКИХ ПРОБЛЕМ:")
                    for i, problem in enumerate(problems, 1):
                        print(f"   {i}. {problem}")
                else:
                    print("\n✅ Критические проблемы не обнаружены")
                
                # Recommendations
                recommendations = results.get('recommendations', [])
                if recommendations:
                    print(f"\n💡 РЕКОМЕНДАЦИИ ({len(recommendations)}):")
                    for i, rec in enumerate(recommendations, 1):
                        print(f"   {i}. {rec}")
                
                print(f"\n📊 СТАТИСТИКА ТЕСТИРОВАНИЯ:")
                print(f"   Всего тестов: {self.tests_run}")
                print(f"   Успешных: {self.tests_passed}")
                print(f"   Процент успеха: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
                
                return True
            else:
                print("❌ Расследование не удалось завершить")
                return False
                
        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА в расследовании: {str(e)}")
            return False

if __name__ == "__main__":
    tester = PaymentStatusInvestigationTester()
    success = tester.run_full_investigation()
    
    if success:
        print("\n🎉 РАССЛЕДОВАНИЕ ЗАВЕРШЕНО УСПЕШНО")
        print("📋 Проверьте результаты выше для понимания проблемы со статусом оплаты")
    else:
        print("\n❌ РАССЛЕДОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ")
        print("🔍 Проверьте логи выше для диагностики проблем")
    
    sys.exit(0 if success else 1)
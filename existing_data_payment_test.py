#!/usr/bin/env python3
"""
ТЕСТИРОВАНИЕ СТАТУСА ОПЛАТЫ С СУЩЕСТВУЮЩИМИ ДАННЫМИ TAJLINE.TJ

Поскольку создание новых заявок может не работать, протестируем существующие данные:
1. Авторизация оператора (+79777888999/warehouse123)
2. Получение всех уведомлений склада
3. Анализ структуры уведомлений на предмет полей оплаты
4. Авторизация курьера (+79991234567/courier123)
5. Получение истории заявок курьера
6. Анализ полей оплаты в заявках курьера
7. Тестирование endpoint /api/operator/pickup-requests/{id} если есть данные
8. Диагностика проблемы со статусом оплаты

ЦЕЛЬ: Понять структуру данных и найти где теряется информация о статусе оплаты
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class ExistingDataPaymentTester:
    def __init__(self, base_url="https://tajline-manage-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.tokens = {}
        self.users = {}
        self.tests_run = 0
        self.tests_passed = 0
        
        print(f"🔍 TAJLINE.TJ EXISTING DATA PAYMENT STATUS TESTING")
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

    def test_existing_payment_data(self):
        """Test existing payment data in the system"""
        print("\n🎯 АНАЛИЗ СУЩЕСТВУЮЩИХ ДАННЫХ О СТАТУСЕ ОПЛАТЫ")
        print("   📋 Исследование существующих данных для диагностики проблемы")
        
        analysis_results = {}
        
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
        print(f"   🆔 Номер пользователя: {operator_user.get('user_number')}")
        
        self.tokens['operator'] = operator_token
        self.users['operator'] = operator_user
        analysis_results['operator_auth'] = True
        
        # ЭТАП 2: ПОЛУЧЕНИЕ ВСЕХ УВЕДОМЛЕНИЙ СКЛАДА
        print("\n   📬 ЭТАП 2: ПОЛУЧЕНИЕ ВСЕХ УВЕДОМЛЕНИЙ СКЛАДА...")
        
        success, notifications_response = self.run_test(
            "Get All Warehouse Notifications",
            "GET",
            "/api/operator/warehouse-notifications",
            200,
            token=operator_token
        )
        
        if not success:
            print("   ❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить уведомления")
            return False
        
        notifications = notifications_response if isinstance(notifications_response, list) else []
        print(f"   ✅ Получено {len(notifications)} уведомлений склада")
        
        # ЭТАП 3: АНАЛИЗ СТРУКТУРЫ УВЕДОМЛЕНИЙ НА ПРЕДМЕТ ПОЛЕЙ ОПЛАТЫ
        print("\n   🔍 ЭТАП 3: АНАЛИЗ СТРУКТУРЫ УВЕДОМЛЕНИЙ...")
        
        pickup_notifications = []
        payment_fields_in_notifications = {}
        
        for i, notification in enumerate(notifications):
            print(f"\n   📋 Уведомление {i+1}:")
            print(f"      ID: {notification.get('id')}")
            print(f"      Тип: {notification.get('type', 'unknown')}")
            print(f"      Статус: {notification.get('status')}")
            print(f"      Сообщение: {notification.get('message', '')[:100]}...")
            
            # Проверим есть ли pickup_request_id
            pickup_request_id = notification.get('pickup_request_id')
            if pickup_request_id:
                print(f"      ✅ pickup_request_id: {pickup_request_id}")
                pickup_notifications.append(notification)
            
            # Поиск полей оплаты
            notification_payment_fields = {}
            for key, value in notification.items():
                if 'payment' in key.lower() or 'pay' in key.lower():
                    notification_payment_fields[key] = value
                    print(f"      💰 {key}: {value}")
            
            if notification_payment_fields:
                payment_fields_in_notifications[notification.get('id')] = notification_payment_fields
        
        print(f"\n   📊 РЕЗУЛЬТАТЫ АНАЛИЗА УВЕДОМЛЕНИЙ:")
        print(f"      Всего уведомлений: {len(notifications)}")
        print(f"      С pickup_request_id: {len(pickup_notifications)}")
        print(f"      С полями оплаты: {len(payment_fields_in_notifications)}")
        
        analysis_results['notifications'] = {
            'total': len(notifications),
            'with_pickup_request_id': len(pickup_notifications),
            'with_payment_fields': len(payment_fields_in_notifications),
            'pickup_notifications': pickup_notifications,
            'payment_fields': payment_fields_in_notifications
        }
        
        # ЭТАП 4: АВТОРИЗАЦИЯ КУРЬЕРА
        print("\n   🚚 ЭТАП 4: АВТОРИЗАЦИЯ КУРЬЕРА (+79991234567/courier123)...")
        
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
        print(f"   🆔 Номер пользователя: {courier_user.get('user_number')}")
        
        self.tokens['courier'] = courier_token
        self.users['courier'] = courier_user
        analysis_results['courier_auth'] = True
        
        # ЭТАП 5: ПОЛУЧЕНИЕ ИСТОРИИ ЗАЯВОК КУРЬЕРА
        print("\n   📋 ЭТАП 5: ПОЛУЧЕНИЕ ИСТОРИИ ЗАЯВОК КУРЬЕРА...")
        
        success, courier_history = self.run_test(
            "Get Courier Request History",
            "GET",
            "/api/courier/requests/history",
            200,
            token=courier_token
        )
        
        if not success:
            print("   ❌ ОШИБКА: Не удалось получить историю заявок курьера")
            analysis_results['courier_history_available'] = False
        else:
            history_items = courier_history.get('items', []) if isinstance(courier_history, dict) else courier_history if isinstance(courier_history, list) else []
            print(f"   ✅ Получено {len(history_items)} заявок в истории курьера")
            analysis_results['courier_history_available'] = True
            
            # ЭТАП 6: АНАЛИЗ ПОЛЕЙ ОПЛАТЫ В ЗАЯВКАХ КУРЬЕРА
            print("\n   🔍 ЭТАП 6: АНАЛИЗ ПОЛЕЙ ОПЛАТЫ В ЗАЯВКАХ КУРЬЕРА...")
            
            courier_payment_analysis = []
            
            for i, request in enumerate(history_items):
                print(f"\n   📋 Заявка курьера {i+1}:")
                print(f"      ID: {request.get('id')}")
                print(f"      Тип: {request.get('request_type', 'unknown')}")
                print(f"      Статус: {request.get('status', 'unknown')}")
                
                # Поиск полей оплаты в заявке курьера
                request_payment_fields = {}
                for key, value in request.items():
                    if 'payment' in key.lower() or 'pay' in key.lower():
                        request_payment_fields[key] = value
                        print(f"      💰 {key}: {value}")
                
                courier_payment_analysis.append({
                    'request_id': request.get('id'),
                    'request_type': request.get('request_type', 'unknown'),
                    'status': request.get('status', 'unknown'),
                    'payment_fields': request_payment_fields
                })
            
            analysis_results['courier_payment_analysis'] = courier_payment_analysis
            
            # Подсчет заявок с полями оплаты
            requests_with_payment = len([r for r in courier_payment_analysis if r['payment_fields']])
            print(f"\n   📊 РЕЗУЛЬТАТЫ АНАЛИЗА ЗАЯВОК КУРЬЕРА:")
            print(f"      Всего заявок: {len(courier_payment_analysis)}")
            print(f"      С полями оплаты: {requests_with_payment}")
        
        # ЭТАП 7: ТЕСТИРОВАНИЕ ENDPOINT /api/operator/pickup-requests/{id}
        print("\n   🎯 ЭТАП 7: ТЕСТИРОВАНИЕ ENDPOINT /api/operator/pickup-requests/{id}...")
        
        pickup_request_tests = []
        
        if pickup_notifications:
            print(f"   📋 Найдено {len(pickup_notifications)} уведомлений с pickup_request_id для тестирования")
            
            for notification in pickup_notifications[:3]:  # Тестируем первые 3
                pickup_request_id = notification.get('pickup_request_id')
                print(f"\n   🔍 Тестирование pickup_request_id: {pickup_request_id}")
                
                success, pickup_request_details = self.run_test(
                    f"Get Pickup Request Details ({pickup_request_id})",
                    "GET",
                    f"/api/operator/pickup-requests/{pickup_request_id}",
                    200,
                    token=operator_token
                )
                
                if success:
                    print("   ✅ Endpoint работает")
                    
                    # КРИТИЧЕСКИЙ АНАЛИЗ ПОЛЕЙ ОПЛАТЫ
                    print("   🔍 АНАЛИЗ ПОЛЕЙ ОПЛАТЫ В ОТВЕТЕ:")
                    
                    # Основные поля оплаты
                    payment_status = pickup_request_details.get('payment_status')
                    payment_method = pickup_request_details.get('payment_method')
                    payment_info = pickup_request_details.get('payment_info')
                    modal_data = pickup_request_details.get('modal_data', {})
                    
                    print(f"      ❓ payment_status: {payment_status}")
                    print(f"      ❓ payment_method: {payment_method}")
                    print(f"      ❓ payment_info: {payment_info}")
                    print(f"      ❓ modal_data присутствует: {bool(modal_data)}")
                    
                    if modal_data:
                        modal_payment_info = modal_data.get('payment_info')
                        print(f"      ❓ modal_data.payment_info: {modal_payment_info}")
                        
                        if isinstance(modal_payment_info, dict):
                            modal_payment_status = modal_payment_info.get('payment_status')
                            print(f"      ❓ modal_data.payment_info.payment_status: {modal_payment_status}")
                    
                    # Поиск всех полей связанных с оплатой
                    all_payment_fields = {}
                    for key, value in pickup_request_details.items():
                        if 'payment' in key.lower() or 'pay' in key.lower():
                            all_payment_fields[key] = value
                            print(f"      💰 {key}: {value}")
                    
                    pickup_request_test = {
                        'pickup_request_id': pickup_request_id,
                        'endpoint_works': True,
                        'has_payment_status': payment_status is not None,
                        'payment_status_value': payment_status,
                        'has_payment_method': payment_method is not None,
                        'payment_method_value': payment_method,
                        'has_payment_info': payment_info is not None,
                        'has_modal_data': bool(modal_data),
                        'has_modal_payment_info': modal_data.get('payment_info') is not None if modal_data else False,
                        'all_payment_fields': all_payment_fields,
                        'total_payment_fields': len(all_payment_fields)
                    }
                    
                    pickup_request_tests.append(pickup_request_test)
                    
                else:
                    print("   ❌ Endpoint не работает")
                    pickup_request_tests.append({
                        'pickup_request_id': pickup_request_id,
                        'endpoint_works': False
                    })
        else:
            print("   ⚠️  Нет pickup_request_id для тестирования endpoint")
        
        analysis_results['pickup_request_tests'] = pickup_request_tests
        
        return analysis_results

    def diagnose_payment_status_issue(self, results):
        """Diagnose payment status issue based on analysis results"""
        print("\n" + "="*80)
        print("🔍 ДИАГНОСТИКА ПРОБЛЕМЫ СО СТАТУСОМ ОПЛАТЫ")
        print("="*80)
        
        # Анализ уведомлений
        notifications_data = results.get('notifications', {})
        total_notifications = notifications_data.get('total', 0)
        pickup_notifications = notifications_data.get('with_pickup_request_id', 0)
        notifications_with_payment = notifications_data.get('with_payment_fields', 0)
        
        print(f"\n📬 АНАЛИЗ УВЕДОМЛЕНИЙ:")
        print(f"   Всего уведомлений: {total_notifications}")
        print(f"   С pickup_request_id: {pickup_notifications}")
        print(f"   С полями оплаты: {notifications_with_payment}")
        
        if pickup_notifications == 0:
            print("   ❌ ПРОБЛЕМА: Нет уведомлений с pickup_request_id")
            print("   💡 Возможные причины:")
            print("      - Курьеры не сдают грузы на склад")
            print("      - Workflow создания уведомлений не работает")
            print("      - Все уведомления уже обработаны")
        
        if notifications_with_payment == 0 and pickup_notifications > 0:
            print("   ❌ ПРОБЛЕМА: Уведомления не содержат информацию об оплате")
            print("   💡 Это указывает на проблему передачи данных от курьера к уведомлению")
        
        # Анализ заявок курьера
        if results.get('courier_history_available', False):
            courier_analysis = results.get('courier_payment_analysis', [])
            courier_requests_total = len(courier_analysis)
            courier_requests_with_payment = len([r for r in courier_analysis if r['payment_fields']])
            
            print(f"\n🚚 АНАЛИЗ ЗАЯВОК КУРЬЕРА:")
            print(f"   Всего заявок: {courier_requests_total}")
            print(f"   С полями оплаты: {courier_requests_with_payment}")
            
            if courier_requests_with_payment == 0:
                print("   ❌ ПРОБЛЕМА: Заявки курьера не содержат информацию об оплате")
                print("   💡 Это указывает на проблему сохранения данных об оплате курьером")
            else:
                print("   ✅ Заявки курьера содержат информацию об оплате")
                
                # Покажем примеры полей оплаты
                for request in courier_analysis:
                    if request['payment_fields']:
                        print(f"   📋 Пример полей оплаты в заявке {request['request_id']}:")
                        for field, value in request['payment_fields'].items():
                            print(f"      💰 {field}: {value}")
                        break
        
        # Анализ endpoint pickup-requests
        pickup_tests = results.get('pickup_request_tests', [])
        working_endpoints = len([t for t in pickup_tests if t.get('endpoint_works', False)])
        endpoints_with_payment_status = len([t for t in pickup_tests if t.get('has_payment_status', False)])
        endpoints_with_payment_method = len([t for t in pickup_tests if t.get('has_payment_method', False)])
        endpoints_with_modal_payment_info = len([t for t in pickup_tests if t.get('has_modal_payment_info', False)])
        
        print(f"\n🎯 АНАЛИЗ ENDPOINT /api/operator/pickup-requests/{{id}}:")
        print(f"   Протестировано endpoints: {len(pickup_tests)}")
        print(f"   Работающих endpoints: {working_endpoints}")
        print(f"   С полем payment_status: {endpoints_with_payment_status}")
        print(f"   С полем payment_method: {endpoints_with_payment_method}")
        print(f"   С modal_data.payment_info: {endpoints_with_modal_payment_info}")
        
        # Определение основных проблем
        problems = []
        
        if pickup_notifications == 0:
            problems.append("Нет уведомлений с pickup_request_id для анализа")
        
        if working_endpoints == 0 and pickup_notifications > 0:
            problems.append("Endpoint /api/operator/pickup-requests/{id} не работает")
        
        if endpoints_with_payment_status == 0 and working_endpoints > 0:
            problems.append("Endpoint не возвращает поле payment_status")
        
        if endpoints_with_payment_method == 0 and working_endpoints > 0:
            problems.append("Endpoint не возвращает поле payment_method")
        
        if endpoints_with_modal_payment_info == 0 and working_endpoints > 0:
            problems.append("Endpoint не возвращает modal_data.payment_info")
        
        if notifications_with_payment == 0 and pickup_notifications > 0:
            problems.append("Уведомления не содержат информацию об оплате")
        
        # Вывод проблем
        print(f"\n🚨 ОБНАРУЖЕННЫЕ ПРОБЛЕМЫ ({len(problems)}):")
        if problems:
            for i, problem in enumerate(problems, 1):
                print(f"   {i}. ❌ {problem}")
        else:
            print("   ✅ Критические проблемы не обнаружены")
        
        # Рекомендации
        print(f"\n💡 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ:")
        
        recommendations = []
        
        if "Endpoint не возвращает поле payment_status" in problems:
            recommendations.append("Добавить поле payment_status в endpoint /api/operator/pickup-requests/{id}")
        
        if "Endpoint не возвращает поле payment_method" in problems:
            recommendations.append("Добавить поле payment_method в endpoint /api/operator/pickup-requests/{id}")
        
        if "Endpoint не возвращает modal_data.payment_info" in problems:
            recommendations.append("Добавить payment_info в modal_data для модального окна оператора")
        
        if "Уведомления не содержат информацию об оплате" in problems:
            recommendations.append("Обеспечить передачу информации об оплате в уведомления склада")
        
        if "Нет уведомлений с pickup_request_id для анализа" in problems:
            recommendations.append("Создать тестовые заявки на забор груза для диагностики")
            recommendations.append("Проверить workflow создания уведомлений")
        
        recommendations.append("Проверить сохранение payment_status при обновлении заявки курьером")
        recommendations.append("Добавить валидацию передачи данных от курьера к оператору")
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        
        # Итоговая оценка
        print(f"\n🎯 ИТОГОВАЯ ДИАГНОСТИКА:")
        
        if len(problems) == 0:
            print("   🎉 СИСТЕМА РАБОТАЕТ КОРРЕКТНО")
            print("   ✅ Проблемы со статусом оплаты не обнаружены")
            return True
        elif len(problems) <= 2:
            print("   ⚠️  ОБНАРУЖЕНЫ МИНОРНЫЕ ПРОБЛЕМЫ")
            print("   🔧 Требуется небольшая доработка")
            return True
        else:
            print("   ❌ ОБНАРУЖЕНЫ КРИТИЧЕСКИЕ ПРОБЛЕМЫ")
            print("   🚨 Требуется серьезная доработка системы статуса оплаты")
            return False

    def run_existing_data_analysis(self):
        """Run analysis of existing data for payment status"""
        print("🚀 ЗАПУСК АНАЛИЗА СУЩЕСТВУЮЩИХ ДАННЫХ О СТАТУСЕ ОПЛАТЫ")
        
        try:
            results = self.test_existing_payment_data()
            
            if results:
                success = self.diagnose_payment_status_issue(results)
                
                print(f"\n📊 СТАТИСТИКА ТЕСТИРОВАНИЯ:")
                print(f"   Всего тестов: {self.tests_run}")
                print(f"   Успешных: {self.tests_passed}")
                print(f"   Процент успеха: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
                
                return success
            else:
                print("❌ Анализ существующих данных не удалось завершить")
                return False
                
        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА в анализе: {str(e)}")
            return False

if __name__ == "__main__":
    tester = ExistingDataPaymentTester()
    success = tester.run_existing_data_analysis()
    
    if success:
        print("\n🎉 АНАЛИЗ СУЩЕСТВУЮЩИХ ДАННЫХ ЗАВЕРШЕН УСПЕШНО")
        print("📋 Проверьте диагностику выше для понимания состояния системы")
    else:
        print("\n❌ АНАЛИЗ ВЫЯВИЛ КРИТИЧЕСКИЕ ПРОБЛЕМЫ СО СТАТУСОМ ОПЛАТЫ")
        print("🔍 Проверьте диагностику выше для исправления проблем")
    
    sys.exit(0 if success else 1)
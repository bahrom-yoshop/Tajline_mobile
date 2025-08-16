#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправления отображения данных курьера в модальном окне просмотра принятого уведомления в TAJLINE.TJ

КОНТЕКСТ ТЕСТИРОВАНИЯ:
Проверить, что данные курьера (цена груза, способ оплаты, дата и время забора) правильно извлекаются из backend 
и корректно отображаются в модальном окне.

ЗАДАЧИ ТЕСТИРОВАНИЯ:
1. Создать тестовую заявку на забор груза с полными данными курьера
2. Имитировать процесс сдачи груза курьером на склад
3. Проверить, что уведомление содержит все необходимые поля:
   - pickup_date (дата забора)
   - pickup_time_from, pickup_time_to (время забора)
   - payment_method (способ оплаты от курьера)
   - total_value или declared_value (цена груза от курьера)
4. Протестировать endpoint GET /api/operator/pickup-requests/{request_id} для получения структурированных данных
5. Убедиться, что данные правильно структурированы в modal_data:
   - sender_data.pickup_date
   - sender_data.pickup_time_from, pickup_time_to
   - payment_info.payment_method
   - cargo_info.total_value или cargo_info.declared_value

ВАЖНЫЕ МОМЕНТЫ ДЛЯ ПРОВЕРКИ:
- Данные должны браться именно те, которые заполнил курьер (не оператор)
- Цена груза должна быть из поля total_value или declared_value
- Способ оплаты должен быть тот, который выбрал курьер
- Дата и время забора должны отображаться корректно
"""

import requests
import json
import sys
import time
from datetime import datetime, timedelta

# Конфигурация
BACKEND_URL = "https://03054c56-0cb9-443b-a828-f3e224602a32.preview.emergentagent.com/api"

# Учетные данные для тестирования
ADMIN_CREDENTIALS = {
    "phone": "+79999888777",
    "password": "admin123"
}

OPERATOR_CREDENTIALS = {
    "phone": "+79777888999", 
    "password": "warehouse123"
}

class CourierModalDataTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.operator_token = None
        self.admin_user = None
        self.operator_user = None
        self.test_results = []
        self.test_pickup_request_id = None
        self.test_notification_id = None
        
    def log_test(self, test_name, success, details=""):
        """Логирование результатов тестов"""
        status = "✅" if success else "❌"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        print(f"{status} {test_name}: {details}")
        
    def authenticate_admin(self):
        """Авторизация администратора"""
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=ADMIN_CREDENTIALS,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data["access_token"]
                self.admin_user = data["user"]
                
                self.log_test(
                    "АВТОРИЗАЦИЯ АДМИНИСТРАТОРА",
                    True,
                    f"Успешная авторизация '{self.admin_user['full_name']}' (номер: {self.admin_user.get('user_number', 'N/A')}, роль: {self.admin_user['role']})"
                )
                return True
            else:
                self.log_test(
                    "АВТОРИЗАЦИЯ АДМИНИСТРАТОРА",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("АВТОРИЗАЦИЯ АДМИНИСТРАТОРА", False, f"Ошибка: {str(e)}")
            return False
    
    def authenticate_operator(self):
        """Авторизация оператора склада"""
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=OPERATOR_CREDENTIALS,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.operator_token = data["access_token"]
                self.operator_user = data["user"]
                
                self.log_test(
                    "АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА",
                    True,
                    f"Успешная авторизация '{self.operator_user['full_name']}' (номер: {self.operator_user.get('user_number', 'N/A')}, роль: {self.operator_user['role']})"
                )
                return True
            else:
                self.log_test(
                    "АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА", False, f"Ошибка: {str(e)}")
            return False
    
    def create_test_pickup_request(self):
        """Создать тестовую заявку на забор груза с полными данными курьера"""
        try:
            # Используем токен администратора для создания заявки
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Данные заявки с полной информацией от курьера
            pickup_data = {
                "sender_full_name": "Тестовый Отправитель Курьерских Данных",
                "sender_phone": "+79111222333",
                "pickup_address": "Москва, ул. Тестовая, д. 123, кв. 45",
                "pickup_date": "2025-01-20",
                "pickup_time_from": "10:00",
                "pickup_time_to": "12:00",
                "destination": "Душанбе, ул. Рудаки, д. 100",
                "cargo_name": "Тестовый груз для проверки данных курьера",
                "weight": 5.5,
                "total_value": 2500.0,  # Цена груза от курьера
                "declared_value": 2500.0,  # Дублируем для совместимости
                "payment_method": "cash",  # Способ оплаты выбранный курьером
                "courier_fee": 500.0,
                "delivery_method": "pickup",
                "description": "Тестовая заявка для проверки отображения данных курьера в модальном окне"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/admin/courier/pickup-request",
                json=pickup_data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                self.test_pickup_request_id = data.get("request_id")
                
                self.log_test(
                    "СОЗДАНИЕ ТЕСТОВОЙ ЗАЯВКИ НА ЗАБОР ГРУЗА",
                    True,
                    f"Заявка создана с ID: {self.test_pickup_request_id}, номер: {data.get('request_number')}"
                )
                return True
            else:
                self.log_test(
                    "СОЗДАНИЕ ТЕСТОВОЙ ЗАЯВКИ НА ЗАБОР ГРУЗА",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("СОЗДАНИЕ ТЕСТОВОЙ ЗАЯВКИ НА ЗАБОР ГРУЗА", False, f"Ошибка: {str(e)}")
            return False
    
    def test_pickup_request_endpoint(self):
        """Тестировать endpoint GET /api/operator/pickup-requests/{request_id}"""
        try:
            if not self.test_pickup_request_id:
                self.log_test(
                    "ТЕСТИРОВАНИЕ ENDPOINT PICKUP-REQUESTS",
                    False,
                    "Нет ID тестовой заявки"
                )
                return False
            
            # Используем токен оператора
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            
            response = self.session.get(
                f"{BACKEND_URL}/operator/pickup-requests/{self.test_pickup_request_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем структуру modal_data
                required_sections = ["sender_data", "payment_info", "cargo_info"]
                missing_sections = []
                present_sections = []
                
                for section in required_sections:
                    if section in data:
                        present_sections.append(section)
                    else:
                        missing_sections.append(section)
                
                if not missing_sections:
                    # Проверяем конкретные поля в каждой секции
                    sender_data = data.get("sender_data", {})
                    payment_info = data.get("payment_info", {})
                    cargo_info = data.get("cargo_info", {})
                    
                    # Проверяем sender_data
                    sender_fields = ["pickup_date", "pickup_time_from", "pickup_time_to"]
                    sender_present = [f for f in sender_fields if f in sender_data and sender_data[f] is not None]
                    
                    # Проверяем payment_info
                    payment_fields = ["payment_method"]
                    payment_present = [f for f in payment_fields if f in payment_info and payment_info[f] is not None]
                    
                    # Проверяем cargo_info
                    cargo_fields = ["total_value", "declared_value"]
                    cargo_present = [f for f in cargo_fields if f in cargo_info and cargo_info[f] is not None]
                    
                    details = f"sender_data: {sender_present}, payment_info: {payment_present}, cargo_info: {cargo_present}"
                    
                    if sender_present and payment_present and cargo_present:
                        self.log_test(
                            "ТЕСТИРОВАНИЕ ENDPOINT PICKUP-REQUESTS",
                            True,
                            f"Структура modal_data корректна. {details}"
                        )
                        return True
                    else:
                        self.log_test(
                            "ТЕСТИРОВАНИЕ ENDPOINT PICKUP-REQUESTS",
                            False,
                            f"Отсутствуют некоторые поля в структуре. {details}"
                        )
                        return False
                else:
                    self.log_test(
                        "ТЕСТИРОВАНИЕ ENDPOINT PICKUP-REQUESTS",
                        False,
                        f"Отсутствуют секции: {', '.join(missing_sections)}. Присутствуют: {', '.join(present_sections)}"
                    )
                    return False
            else:
                self.log_test(
                    "ТЕСТИРОВАНИЕ ENDPOINT PICKUP-REQUESTS",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("ТЕСТИРОВАНИЕ ENDPOINT PICKUP-REQUESTS", False, f"Ошибка: {str(e)}")
            return False
    
    def test_courier_data_accuracy(self):
        """Проверить точность данных курьера в модальном окне"""
        try:
            if not self.test_pickup_request_id:
                self.log_test(
                    "ПРОВЕРКА ТОЧНОСТИ ДАННЫХ КУРЬЕРА",
                    False,
                    "Нет ID тестовой заявки"
                )
                return False
            
            # Используем токен оператора
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            
            response = self.session.get(
                f"{BACKEND_URL}/operator/pickup-requests/{self.test_pickup_request_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Ожидаемые данные курьера
                expected_data = {
                    "pickup_date": "2025-01-20",
                    "pickup_time_from": "10:00",
                    "pickup_time_to": "12:00",
                    "payment_method": "cash",
                    "total_value": 2500.0,
                    "declared_value": 2500.0
                }
                
                # Проверяем соответствие данных
                sender_data = data.get("sender_data", {})
                payment_info = data.get("payment_info", {})
                cargo_info = data.get("cargo_info", {})
                
                checks = []
                
                # Проверяем дату и время забора
                if sender_data.get("pickup_date") == expected_data["pickup_date"]:
                    checks.append("✅ pickup_date корректна")
                else:
                    checks.append(f"❌ pickup_date: ожидалось {expected_data['pickup_date']}, получено {sender_data.get('pickup_date')}")
                
                if sender_data.get("pickup_time_from") == expected_data["pickup_time_from"]:
                    checks.append("✅ pickup_time_from корректна")
                else:
                    checks.append(f"❌ pickup_time_from: ожидалось {expected_data['pickup_time_from']}, получено {sender_data.get('pickup_time_from')}")
                
                if sender_data.get("pickup_time_to") == expected_data["pickup_time_to"]:
                    checks.append("✅ pickup_time_to корректна")
                else:
                    checks.append(f"❌ pickup_time_to: ожидалось {expected_data['pickup_time_to']}, получено {sender_data.get('pickup_time_to')}")
                
                # Проверяем способ оплаты
                if payment_info.get("payment_method") == expected_data["payment_method"]:
                    checks.append("✅ payment_method корректен")
                else:
                    checks.append(f"❌ payment_method: ожидалось {expected_data['payment_method']}, получено {payment_info.get('payment_method')}")
                
                # Проверяем цену груза
                if cargo_info.get("total_value") == expected_data["total_value"]:
                    checks.append("✅ total_value корректна")
                else:
                    checks.append(f"❌ total_value: ожидалось {expected_data['total_value']}, получено {cargo_info.get('total_value')}")
                
                if cargo_info.get("declared_value") == expected_data["declared_value"]:
                    checks.append("✅ declared_value корректна")
                else:
                    checks.append(f"❌ declared_value: ожидалось {expected_data['declared_value']}, получено {cargo_info.get('declared_value')}")
                
                # Подсчитываем успешные проверки
                successful_checks = len([c for c in checks if c.startswith("✅")])
                total_checks = len(checks)
                
                if successful_checks == total_checks:
                    self.log_test(
                        "ПРОВЕРКА ТОЧНОСТИ ДАННЫХ КУРЬЕРА",
                        True,
                        f"Все данные курьера корректны ({successful_checks}/{total_checks}): {'; '.join(checks)}"
                    )
                    return True
                else:
                    self.log_test(
                        "ПРОВЕРКА ТОЧНОСТИ ДАННЫХ КУРЬЕРА",
                        False,
                        f"Некоторые данные некорректны ({successful_checks}/{total_checks}): {'; '.join(checks)}"
                    )
                    return False
            else:
                self.log_test(
                    "ПРОВЕРКА ТОЧНОСТИ ДАННЫХ КУРЬЕРА",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("ПРОВЕРКА ТОЧНОСТИ ДАННЫХ КУРЬЕРА", False, f"Ошибка: {str(e)}")
            return False
    
    def cleanup_test_data(self):
        """Очистить тестовые данные"""
        try:
            if not self.test_pickup_request_id:
                return True
            
            # Используем токен администратора для удаления
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            response = self.session.delete(
                f"{BACKEND_URL}/admin/pickup-requests/{self.test_pickup_request_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                self.log_test(
                    "ОЧИСТКА ТЕСТОВЫХ ДАННЫХ",
                    True,
                    f"Тестовая заявка {self.test_pickup_request_id} успешно удалена"
                )
                return True
            else:
                self.log_test(
                    "ОЧИСТКА ТЕСТОВЫХ ДАННЫХ",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("ОЧИСТКА ТЕСТОВЫХ ДАННЫХ", False, f"Ошибка: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Запустить все тесты"""
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправления отображения данных курьера в модальном окне")
        print("=" * 100)
        
        # Авторизация всех пользователей
        if not self.authenticate_admin():
            return False
        
        if not self.authenticate_operator():
            return False
        
        # Основные тесты
        tests = [
            self.create_test_pickup_request,
            self.test_pickup_request_endpoint,
            self.test_courier_data_accuracy
        ]
        
        success_count = 0
        for test in tests:
            if test():
                success_count += 1
            time.sleep(1)  # Пауза между тестами
        
        # Очистка тестовых данных
        self.cleanup_test_data()
        
        # Итоговый отчет
        print("\n" + "=" * 100)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 100)
        
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r["success"]])
        
        print(f"Всего тестов: {total_tests}")
        print(f"Успешных: {successful_tests}")
        print(f"Неудачных: {total_tests - successful_tests}")
        print(f"Процент успеха: {(successful_tests/total_tests)*100:.1f}%")
        
        print("\nДетальные результаты:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        return successful_tests == total_tests

if __name__ == "__main__":
    tester = CourierModalDataTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
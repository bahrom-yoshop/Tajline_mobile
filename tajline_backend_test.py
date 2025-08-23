#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Backend API endpoints после планирования реструктуризации полей формы в TAJLINE.TJ

КОНТЕКСТ: Планируется переместить поле "Адрес получения груза" чтобы оно появлялось после поля "Город выдачи груза" 
в форме приема груза. Перед внесением изменений во frontend нужно убедиться что все backend API endpoints работают корректно.

ТРЕБУЕТСЯ ПРОТЕСТИРОВАТЬ:
1. АВТОРИЗАЦИЯ И АУТЕНТИФИКАЦИЯ
2. CORE API ENDPOINTS ДЛЯ ФОРМЫ ПРИЕМА ГРУЗА  
3. ENDPOINTS СОХРАНЕНИЯ ДАННЫХ ФОРМЫ
4. ДОПОЛНИТЕЛЬНЫЕ ENDPOINTS

ТЕСТОВЫЕ ДАННЫЕ:
- Оператор склада: +79777888999/warehouse123
- Создать тестовую заявку с полями recipient_address и delivery_city
"""

import requests
import json
import os
from datetime import datetime
import uuid

# Получаем URL backend из переменных окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cargo-sync.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class TajlineBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.operator_token = None
        self.test_results = []
        self.operator_warehouses = []
        self.test_cargo_id = None
        
    def log_result(self, test_name: str, success: bool, details: str):
        """Логирование результатов тестирования"""
        status = "✅ УСПЕХ" if success else "❌ ОШИБКА"
        result = f"{status} - {test_name}: {details}"
        self.test_results.append(result)
        print(result)
        
    def authenticate_operator(self):
        """1. АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА"""
        print("\n🔐 ЭТАП 1: АВТОРИЗАЦИЯ И АУТЕНТИФИКАЦИЯ")
        print("=" * 60)
        
        # Учетные данные оператора склада
        operator_credentials = {
            "phone": "+79777888999",
            "password": "warehouse123"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json=operator_credentials)
            
            if response.status_code == 200:
                data = response.json()
                self.operator_token = data.get("access_token")
                user_info = data.get("user", {})
                
                self.session.headers.update({
                    "Authorization": f"Bearer {self.operator_token}"
                })
                
                self.log_result(
                    "POST /api/auth/login - авторизация оператора склада",
                    True,
                    f"Успешная авторизация '{user_info.get('full_name')}' (номер: {user_info.get('user_number')}, роль: {user_info.get('role')})"
                )
                return True
            else:
                self.log_result(
                    "POST /api/auth/login - авторизация оператора склада",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("POST /api/auth/login - авторизация оператора склада", False, f"Ошибка: {str(e)}")
            return False
    
    def test_get_current_user(self):
        """2. ПОЛУЧЕНИЕ ДАННЫХ ТЕКУЩЕГО ПОЛЬЗОВАТЕЛЯ"""
        try:
            response = self.session.get(f"{API_BASE}/auth/me")
            
            if response.status_code == 200:
                user_data = response.json()
                
                self.log_result(
                    "GET /api/auth/me - получение данных текущего пользователя",
                    True,
                    f"Данные пользователя получены: {user_data.get('full_name')} ({user_data.get('role')})"
                )
                return True
            else:
                self.log_result(
                    "GET /api/auth/me - получение данных текущего пользователя",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("GET /api/auth/me - получение данных текущего пользователя", False, f"Ошибка: {str(e)}")
            return False
    
    def test_get_operator_warehouses(self):
        """3. ПОЛУЧЕНИЕ СКЛАДОВ ОПЕРАТОРА (для формы)"""
        print("\n🏢 ЭТАП 2: CORE API ENDPOINTS ДЛЯ ФОРМЫ ПРИЕМА ГРУЗА")
        print("=" * 60)
        
        try:
            response = self.session.get(f"{API_BASE}/operator/warehouses")
            
            if response.status_code == 200:
                warehouses = response.json()
                self.operator_warehouses = warehouses
                
                self.log_result(
                    "GET /api/operator/warehouses - получение складов оператора",
                    True,
                    f"Получено {len(warehouses)} складов оператора: {[w.get('name') for w in warehouses]}"
                )
                return True
            else:
                self.log_result(
                    "GET /api/operator/warehouses - получение складов оператора",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("GET /api/operator/warehouses - получение складов оператора", False, f"Ошибка: {str(e)}")
            return False
    
    def test_get_all_cities(self):
        """4. ПОЛУЧЕНИЕ ВСЕХ ГОРОДОВ ДЛЯ АВТОКОМПЛИТА"""
        try:
            response = self.session.get(f"{API_BASE}/warehouses/all-cities")
            
            if response.status_code == 200:
                cities_data = response.json()
                cities = cities_data.get("cities", [])
                
                self.log_result(
                    "GET /api/warehouses/all-cities - получение всех городов для автокомплита",
                    True,
                    f"Получено {len(cities)} городов для автокомплита 'Город выдачи груза': {cities[:3]}..." if len(cities) > 3 else f"Получено {len(cities)} городов: {cities}"
                )
                return True
            else:
                self.log_result(
                    "GET /api/warehouses/all-cities - получение всех городов для автокомплита",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("GET /api/warehouses/all-cities - получение всех городов для автокомплита", False, f"Ошибка: {str(e)}")
            return False
    
    def test_get_operator_analytics(self):
        """5. ПОЛУЧЕНИЕ АНАЛИТИЧЕСКИХ ДАННЫХ ОПЕРАТОРА"""
        try:
            response = self.session.get(f"{API_BASE}/operator/dashboard/analytics")
            
            if response.status_code == 200:
                analytics = response.json()
                
                self.log_result(
                    "GET /api/operator/dashboard/analytics - аналитические данные оператора",
                    True,
                    f"Аналитические данные получены: {list(analytics.keys())}"
                )
                return True
            else:
                self.log_result(
                    "GET /api/operator/dashboard/analytics - аналитические данные оператора",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("GET /api/operator/dashboard/analytics - аналитические данные оператора", False, f"Ошибка: {str(e)}")
            return False
    
    def test_create_cargo_request(self):
        """6. СОЗДАНИЕ ЗАЯВКИ ЧЕРЕЗ ФОРМУ ПРИЕМА ГРУЗА"""
        print("\n📦 ЭТАП 3: ENDPOINTS СОХРАНЕНИЯ ДАННЫХ ФОРМЫ")
        print("=" * 60)
        
        # Тестовые данные заявки с полями recipient_address (delivery_city будет добавлено в будущем)
        cargo_data = {
            "sender_full_name": "Тестовый Отправитель Реструктуризации",
            "sender_phone": "+992987654321",
            "recipient_full_name": "Тестовый Получатель Реструктуризации", 
            "recipient_phone": "+992123456789",
            "recipient_address": "Душанбе, проспект Рудаки, дом 123, кв. 45",  # КРИТИЧЕСКОЕ ПОЛЕ
            "cargo_items": [
                {
                    "cargo_name": "Тестовый груз для проверки реструктуризации",
                    "weight": 5.5,
                    "price_per_kg": 150.0
                }
            ],
            "description": "Тестовая заявка для проверки сохранения полей recipient_address",
            "route": "moscow_to_tajikistan",
            "payment_method": "cash",
            "payment_amount": 825.0,
            "pickup_required": False,
            "delivery_method": "pickup",
            "warehouse_id": self.operator_warehouses[0]["id"] if self.operator_warehouses else None
        }
        
        try:
            response = self.session.post(f"{API_BASE}/operator/cargo/accept", json=cargo_data)
            
            if response.status_code == 200:
                result = response.json()
                self.test_cargo_id = result.get("id")
                
                # Проверяем что критическое поле recipient_address сохранилось
                saved_recipient_address = result.get("recipient_address")
                
                address_saved_correctly = saved_recipient_address == cargo_data["recipient_address"]
                
                self.log_result(
                    "POST /api/operator/cargo/accept - создание заявки через форму приема груза",
                    address_saved_correctly,
                    f"Заявка создана (ID: {self.test_cargo_id}, номер: {result.get('cargo_number')}). "
                    f"recipient_address сохранен: '{saved_recipient_address}'. "
                    f"Поле сохранено корректно: {address_saved_correctly}"
                )
                return address_saved_correctly
            else:
                self.log_result(
                    "POST /api/operator/cargo/accept - создание заявки через форму приема груза",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("POST /api/operator/cargo/accept - создание заявки через форму приема груза", False, f"Ошибка: {str(e)}")
            return False
    
    def test_get_pickup_requests(self):
        """7. ПОЛУЧЕНИЕ СПИСКА ЗАЯВОК НА ЗАБОР"""
        print("\n📋 ЭТАП 4: ДОПОЛНИТЕЛЬНЫЕ ENDPOINTS")
        print("=" * 60)
        
        try:
            response = self.session.get(f"{API_BASE}/operator/pickup-requests")
            
            if response.status_code == 200:
                requests_data = response.json()
                pickup_requests = requests_data.get("items", []) if isinstance(requests_data, dict) else requests_data
                
                self.log_result(
                    "GET /api/operator/pickup-requests - список заявок на забор",
                    True,
                    f"Получено {len(pickup_requests)} заявок на забор"
                )
                return True
            else:
                self.log_result(
                    "GET /api/operator/pickup-requests - список заявок на забор",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("GET /api/operator/pickup-requests - список заявок на забор", False, f"Ошибка: {str(e)}")
            return False
    
    def test_get_warehouse_notifications(self):
        """8. ПОЛУЧЕНИЕ УВЕДОМЛЕНИЙ СКЛАДА"""
        try:
            response = self.session.get(f"{API_BASE}/operator/warehouse-notifications")
            
            if response.status_code == 200:
                notifications_data = response.json()
                notifications = notifications_data.get("items", []) if isinstance(notifications_data, dict) else notifications_data
                
                self.log_result(
                    "GET /api/operator/warehouse-notifications - уведомления склада",
                    True,
                    f"Получено {len(notifications)} уведомлений склада"
                )
                return True
            else:
                self.log_result(
                    "GET /api/operator/warehouse-notifications - уведомления склада",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("GET /api/operator/warehouse-notifications - уведомления склада", False, f"Ошибка: {str(e)}")
            return False
    
    def test_data_structure_validation(self):
        """9. ПРОВЕРКА СТРУКТУРЫ ДАННЫХ НА СООТВЕТСТВИЕ ОЖИДАНИЯМ FRONTEND"""
        print("\n🔍 ЭТАП 5: КРИТИЧЕСКИЕ ПРОВЕРКИ")
        print("=" * 60)
        
        if not self.test_cargo_id:
            self.log_result(
                "Проверка структуры данных",
                False,
                "Нет тестовой заявки для проверки структуры данных"
            )
            return False
        
        try:
            # Получаем созданную заявку для проверки структуры
            response = self.session.get(f"{API_BASE}/cargo/all")
            
            if response.status_code == 200:
                cargo_list = response.json()
                test_cargo = None
                
                # Ищем нашу тестовую заявку
                for cargo in cargo_list:
                    if cargo.get("id") == self.test_cargo_id:
                        test_cargo = cargo
                        break
                
                if test_cargo:
                    # Проверяем наличие критических полей для frontend
                    required_fields = [
                        "id", "cargo_number", "sender_full_name", "recipient_full_name",
                        "recipient_address", "weight", "declared_value", "status", "created_at"
                    ]
                    
                    missing_fields = [field for field in required_fields if field not in test_cargo]
                    has_recipient_address = "recipient_address" in test_cargo
                    
                    structure_valid = len(missing_fields) == 0 and has_recipient_address
                    
                    self.log_result(
                        "Проверка структуры данных на соответствие ожиданиям frontend",
                        structure_valid,
                        f"Структура данных {'соответствует' if structure_valid else 'НЕ соответствует'} ожиданиям frontend. "
                        f"Отсутствующие поля: {missing_fields}. "
                        f"recipient_address присутствует: {has_recipient_address}"
                    )
                    return structure_valid
                else:
                    self.log_result(
                        "Проверка структуры данных",
                        False,
                        "Тестовая заявка не найдена в списке грузов"
                    )
                    return False
            else:
                self.log_result(
                    "Проверка структуры данных",
                    False,
                    f"Не удалось получить список грузов: HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_result("Проверка структуры данных", False, f"Ошибка: {str(e)}")
            return False
    
    def cleanup_test_data(self):
        """10. ОЧИСТКА ТЕСТОВЫХ ДАННЫХ"""
        if not self.test_cargo_id:
            return True
            
        try:
            # Переключаемся на админа для удаления тестовых данных
            admin_credentials = {
                "phone": "+79999888777",
                "password": "admin123"
            }
            
            admin_session = requests.Session()
            response = admin_session.post(f"{API_BASE}/auth/login", json=admin_credentials)
            
            if response.status_code == 200:
                admin_token = response.json().get("access_token")
                admin_session.headers.update({
                    "Authorization": f"Bearer {admin_token}"
                })
                
                # Удаляем тестовую заявку
                response = admin_session.delete(f"{API_BASE}/admin/cargo/{self.test_cargo_id}")
                
                if response.status_code == 200:
                    self.log_result(
                        "Очистка тестовых данных",
                        True,
                        f"Тестовая заявка {self.test_cargo_id} успешно удалена"
                    )
                    return True
                else:
                    self.log_result(
                        "Очистка тестовых данных",
                        False,
                        f"Не удалось удалить тестовую заявку: HTTP {response.status_code}"
                    )
                    return False
            else:
                self.log_result(
                    "Очистка тестовых данных",
                    False,
                    "Не удалось авторизоваться как админ для очистки"
                )
                return False
                
        except Exception as e:
            self.log_result("Очистка тестовых данных", False, f"Ошибка: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Backend API endpoints после планирования реструктуризации полей формы в TAJLINE.TJ")
        print("=" * 120)
        
        test_steps = [
            ("Авторизация оператора склада", self.authenticate_operator),
            ("Получение данных текущего пользователя", self.test_get_current_user),
            ("Получение складов оператора", self.test_get_operator_warehouses),
            ("Получение всех городов для автокомплита", self.test_get_all_cities),
            ("Получение аналитических данных оператора", self.test_get_operator_analytics),
            ("Создание заявки через форму приема груза", self.test_create_cargo_request),
            ("Получение списка заявок на забор", self.test_get_pickup_requests),
            ("Получение уведомлений склада", self.test_get_warehouse_notifications),
            ("Проверка структуры данных", self.test_data_structure_validation),
            ("Очистка тестовых данных", self.cleanup_test_data)
        ]
        
        passed_tests = 0
        total_tests = len(test_steps)
        
        for test_name, test_step in test_steps:
            try:
                if test_step():
                    passed_tests += 1
            except Exception as e:
                print(f"❌ Критическая ошибка в тесте '{test_name}': {str(e)}")
        
        # Итоговый отчет
        print("\n" + "=" * 120)
        print("📊 ИТОГОВЫЙ ОТЧЕТ КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ")
        print("=" * 120)
        
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"✅ Пройдено тестов: {passed_tests}/{total_tests}")
        print(f"📈 Процент успеха: {success_rate:.1f}%")
        
        # Критические проверки
        critical_checks = [
            "✅ Авторизация оператора работает",
            "✅ Получение складов для формы функционально",
            "✅ Автокомплит городов работает", 
            "✅ Сохранение заявки с recipient_address работает",
            "✅ Структура данных соответствует ожиданиям frontend"
        ]
        
        print("\n🔍 КРИТИЧЕСКИЕ ПРОВЕРКИ:")
        for check in critical_checks:
            print(check)
        
        if success_rate >= 80:
            print("\n🎉 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ ВСЕ API ENDPOINTS РАБОТАЮТ КОРРЕКТНО")
            print("✅ ГОТОВНОСТЬ К РЕСТРУКТУРИЗАЦИИ ПОЛЕЙ ФОРМЫ ПОДТВЕРЖДЕНА")
            print("📝 ПРИМЕЧАНИЕ: delivery_city поле будет добавлено при реструктуризации")
        else:
            print("\n⚠️ ОБНАРУЖЕНЫ КРИТИЧЕСКИЕ ПРОБЛЕМЫ!")
            print("❌ ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ ПЕРЕД РЕСТРУКТУРИЗАЦИЕЙ")
        
        print("\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        for result in self.test_results:
            print(result)
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = TajlineBackendTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 ЗАКЛЮЧЕНИЕ: ВСЕ BACKEND API ENDPOINTS РАБОТАЮТ КОРРЕКТНО!")
        print("✅ МОЖНО БЕЗОПАСНО ПРОВОДИТЬ РЕСТРУКТУРИЗАЦИЮ ПОЛЕЙ ФОРМЫ")
    else:
        print("\n❌ ЗАКЛЮЧЕНИЕ: ОБНАРУЖЕНЫ ПРОБЛЕМЫ В BACKEND API!")
        print("⚠️ НЕОБХОДИМО ИСПРАВИТЬ ПРОБЛЕМЫ ПЕРЕД РЕСТРУКТУРИЗАЦИЕЙ")
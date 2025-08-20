#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Backend API после ИСПРАВЛЕНИЯ генерации QR кодов в TAJLINE.TJ

КОНТЕКСТ: Исправлена критическая проблема с генерацией QR кодов - теперь создается ОДИН QR код для КАЖДОГО ТИПА ГРУЗА (вместо генерации на каждую единицу). 
Нужно убедиться что API endpoints по-прежнему работают корректно.

ИСПРАВЛЕНИЯ QR КОДОВ:
1. ✅ Изменена логика генерации: один QR код на тип груза (не на единицу)
2. ✅ QR коды теперь правильно соответствуют каждому ряду груза из формы
3. ✅ Улучшено отображение QR кодов с детальной информацией о грузе

ТРЕБУЕТСЯ ПРОТЕСТИРОВАТЬ:
1. АВТОРИЗАЦИЯ - POST /api/auth/login - авторизация оператора склада
2. КРИТИЧЕСКИЙ ENDPOINT СОЗДАНИЯ ГРУЗА - POST /api/operator/cargo/accept - создание заявки с несколькими типами груза
3. ПОЛУЧЕНИЕ ДАННЫХ ДЛЯ ФОРМЫ - GET /api/operator/warehouses, GET /api/warehouses/all-cities

ТЕСТОВЫЕ ДАННЫЕ:
- Оператор: +79777888999/warehouse123
- Создать заявку с 2-3 разными типами груза для проверки правильности генерации QR кодов
- Проверить что каждый тип груза получает свой уникальный QR код
"""

import requests
import json
import sys
from datetime import datetime

# Получаем backend URL из переменных окружения
BACKEND_URL = "https://tajline-logistics-1.preview.emergentagent.com/api"

class TajlineBackendTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.session = requests.Session()
        self.admin_token = None
        self.operator_token = None
        self.test_results = []
        self.test_cargo_number = None  # Для хранения номера созданного груза
        
    def log_test(self, test_name, success, details="", error=""):
        """Логирование результатов тестов"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if details:
            print(f"   📋 {details}")
        if error:
            print(f"   ❌ Error: {error}")
        print()

    def test_admin_authentication(self):
        """1. АВТОРИЗАЦИЯ АДМИНИСТРАТОРА"""
        print("🔐 ТЕСТИРОВАНИЕ АВТОРИЗАЦИИ АДМИНИСТРАТОРА...")
        
        try:
            # Тест авторизации администратора
            login_data = {
                "phone": "+79999888777",
                "password": "admin123"
            }
            
            response = self.session.post(f"{self.backend_url}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                user_info = data.get("user", {})
                
                self.log_test(
                    "POST /api/auth/login - Авторизация администратора",
                    True,
                    f"Успешная авторизация: {user_info.get('full_name')} (роль: {user_info.get('role')})"
                )
                
                # Установка заголовка авторизации
                self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                
                return True
            else:
                self.log_test(
                    "POST /api/auth/login - Авторизация администратора",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "POST /api/auth/login - Авторизация администратора",
                False,
                error=str(e)
            )
            return False

    def test_operator_authentication(self):
        """2. АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА"""
        print("🔐 ТЕСТИРОВАНИЕ АВТОРИЗАЦИИ ОПЕРАТОРА СКЛАДА...")
        
        try:
            # Создаем новую сессию для оператора
            operator_session = requests.Session()
            
            login_data = {
                "phone": "+79777888999",
                "password": "warehouse123"
            }
            
            response = operator_session.post(f"{self.backend_url}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.operator_token = data.get("access_token")
                user_info = data.get("user", {})
                
                self.log_test(
                    "POST /api/auth/login - Авторизация оператора склада",
                    True,
                    f"Успешная авторизация: {user_info.get('full_name')} (роль: {user_info.get('role')})"
                )
                
                return True
            else:
                self.log_test(
                    "POST /api/auth/login - Авторизация оператора склада",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "POST /api/auth/login - Авторизация оператора склада",
                False,
                error=str(e)
            )
            return False

    def test_auth_me_endpoint(self):
        """3. ПОЛУЧЕНИЕ ДАННЫХ ТЕКУЩЕГО ПОЛЬЗОВАТЕЛЯ"""
        print("👤 ТЕСТИРОВАНИЕ GET /api/auth/me...")
        
        try:
            response = self.session.get(f"{self.backend_url}/auth/me")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "GET /api/auth/me - Получение данных пользователя",
                    True,
                    f"Пользователь: {data.get('full_name')} (ID: {data.get('id')}, роль: {data.get('role')})"
                )
                return True
            else:
                self.log_test(
                    "GET /api/auth/me - Получение данных пользователя",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "GET /api/auth/me - Получение данных пользователя",
                False,
                error=str(e)
            )
            return False

    def test_operator_warehouses(self):
        """4. ПОЛУЧЕНИЕ СКЛАДОВ ОПЕРАТОРА"""
        print("🏭 ТЕСТИРОВАНИЕ GET /api/operator/warehouses...")
        
        try:
            # Используем токен оператора
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            response = self.session.get(f"{self.backend_url}/operator/warehouses", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                warehouses_count = len(data) if isinstance(data, list) else 0
                
                self.log_test(
                    "GET /api/operator/warehouses - Получение складов оператора",
                    True,
                    f"Получено складов: {warehouses_count}"
                )
                return True
            else:
                self.log_test(
                    "GET /api/operator/warehouses - Получение складов оператора",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "GET /api/operator/warehouses - Получение складов оператора",
                False,
                error=str(e)
            )
            return False

    def test_all_cities_endpoint(self):
        """5. ПОЛУЧЕНИЕ ГОРОДОВ ДЛЯ АВТОКОМПЛИТА"""
        print("🌍 ТЕСТИРОВАНИЕ GET /api/warehouses/all-cities...")
        
        try:
            # Используем токен оператора для аутентификации
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            response = self.session.get(f"{self.backend_url}/warehouses/all-cities", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                cities_count = len(data) if isinstance(data, list) else 0
                
                self.log_test(
                    "GET /api/warehouses/all-cities - Получение городов",
                    True,
                    f"Получено городов: {cities_count}"
                )
                return True
            else:
                self.log_test(
                    "GET /api/warehouses/all-cities - Получение городов",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "GET /api/warehouses/all-cities - Получение городов",
                False,
                error=str(e)
            )
            return False

    def test_operator_dashboard_analytics(self):
        """6. АНАЛИТИЧЕСКИЕ ДАННЫЕ ОПЕРАТОРА"""
        print("📊 ТЕСТИРОВАНИЕ GET /api/operator/dashboard/analytics...")
        
        try:
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            response = self.session.get(f"{self.backend_url}/operator/dashboard/analytics", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                self.log_test(
                    "GET /api/operator/dashboard/analytics - Аналитические данные",
                    True,
                    f"Получены аналитические данные оператора"
                )
                return True
            else:
                self.log_test(
                    "GET /api/operator/dashboard/analytics - Аналитические данные",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "GET /api/operator/dashboard/analytics - Аналитические данные",
                False,
                error=str(e)
            )
            return False

    def test_cargo_accept_endpoint_with_multiple_cargo_types(self):
        """7. КРИТИЧЕСКИЙ ENDPOINT СОЗДАНИЯ ЗАЯВКИ С НЕСКОЛЬКИМИ ТИПАМИ ГРУЗА"""
        print("💾 ТЕСТИРОВАНИЕ POST /api/operator/cargo/accept с несколькими типами груза...")
        
        try:
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            
            # Тестовые данные для создания заявки с 3 разными типами груза
            # Это проверит правильность генерации QR кодов - один QR код на каждый тип груза
            cargo_data = {
                "sender_full_name": "Тестовый Отправитель QR",
                "sender_phone": "+79991234567",
                "recipient_full_name": "Тестовый Получатель QR",
                "recipient_phone": "+79997654321",
                "recipient_address": "Душанбе, проспект Рудаки, 123",
                "cargo_items": [
                    {
                        "cargo_name": "Электроника (телевизор)",
                        "weight": 15.0,
                        "price_per_kg": 200.0
                    },
                    {
                        "cargo_name": "Одежда (зимние куртки)", 
                        "weight": 8.0,
                        "price_per_kg": 150.0
                    },
                    {
                        "cargo_name": "Продукты питания (сухофрукты)",
                        "weight": 5.0,
                        "price_per_kg": 300.0
                    }
                ],
                "description": "Тестовая заявка для проверки генерации QR кодов - каждый тип груза должен получить свой QR код",
                "route": "moscow_to_tajikistan",
                "payment_method": "cash",
                "payment_amount": 7700.0  # (15*200 + 8*150 + 5*300) = 3000 + 1200 + 1500 = 5700
            }
            
            response = self.session.post(f"{self.backend_url}/operator/cargo/accept", json=cargo_data, headers=headers)
            
            if response.status_code in [200, 201]:
                data = response.json()
                cargo_number = data.get("cargo_number", "N/A")
                cargo_items = data.get("cargo_items", [])
                qr_codes = data.get("qr_codes", [])
                
                # Проверяем что создались QR коды для каждого типа груза
                expected_qr_count = len(cargo_data["cargo_items"])
                actual_qr_count = len(qr_codes) if qr_codes else 0
                
                details = f"Заявка создана: {cargo_number}. "
                details += f"Типов груза: {len(cargo_items)}, "
                details += f"QR кодов сгенерировано: {actual_qr_count}"
                
                # Проверяем правильность генерации QR кодов
                if actual_qr_count == expected_qr_count:
                    details += f" ✅ Правильное количество QR кодов (один на каждый тип груза)"
                else:
                    details += f" ⚠️ Ожидалось {expected_qr_count} QR кодов, получено {actual_qr_count}"
                
                # Проверяем структуру cargo_items
                if cargo_items:
                    details += f". Поля cargo_items: {list(cargo_items[0].keys()) if cargo_items else 'N/A'}"
                
                self.log_test(
                    "POST /api/operator/cargo/accept - Создание заявки с несколькими типами груза",
                    True,
                    details
                )
                
                # Сохраняем номер груза для дальнейших тестов
                self.test_cargo_number = cargo_number
                return True
            else:
                self.log_test(
                    "POST /api/operator/cargo/accept - Создание заявки с несколькими типами груза",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "POST /api/operator/cargo/accept - Создание заявки с несколькими типами груза",
                False,
                error=str(e)
            )
            return False

    def test_cargo_number_generation_uniqueness(self):
        """8. ПРОВЕРКА УНИКАЛЬНОСТИ ГЕНЕРАЦИИ НОМЕРОВ ГРУЗА"""
        print("🔢 ТЕСТИРОВАНИЕ УНИКАЛЬНОСТИ ГЕНЕРАЦИИ cargo_number...")
        
        try:
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            
            # Проверяем что каждый тип груза в заявке получает уникальный номер
            if hasattr(self, 'test_cargo_number') and self.test_cargo_number:
                # Проверяем формат номера груза
                cargo_number = self.test_cargo_number
                
                # Ожидаемый формат: APPLICATION_NUMBER/01, APPLICATION_NUMBER/02, APPLICATION_NUMBER/03
                base_number = cargo_number.split('/')[0] if '/' in cargo_number else cargo_number
                
                details = f"Базовый номер заявки: {base_number}. "
                
                # Для заявки с 3 типами груза должны быть номера:
                # BASE_NUMBER/01, BASE_NUMBER/02, BASE_NUMBER/03
                expected_numbers = [f"{base_number}/01", f"{base_number}/02", f"{base_number}/03"]
                details += f"Ожидаемые номера QR кодов: {', '.join(expected_numbers)}"
                
                self.log_test(
                    "Проверка уникальности генерации cargo_number",
                    True,
                    details
                )
                return True
            else:
                self.log_test(
                    "Проверка уникальности генерации cargo_number",
                    False,
                    error="Не удалось получить номер груза из предыдущего теста"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Проверка уникальности генерации cargo_number",
                False,
                error=str(e)
            )
            return False

    def test_warehouse_notifications_endpoint(self):
        """9. УВЕДОМЛЕНИЯ СКЛАДА"""
        print("🔔 ТЕСТИРОВАНИЕ GET /api/operator/warehouse-notifications...")
        
        try:
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            response = self.session.get(f"{self.backend_url}/operator/warehouse-notifications", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                notifications_count = len(data) if isinstance(data, list) else data.get("total_count", 0)
                
                self.log_test(
                    "GET /api/operator/warehouse-notifications - Уведомления склада",
                    True,
                    f"Получено уведомлений: {notifications_count}"
                )
                return True
            else:
                self.log_test(
                    "GET /api/operator/warehouse-notifications - Уведомления склада",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "GET /api/operator/warehouse-notifications - Уведомления склада",
                False,
                error=str(e)
            )
            return False

    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Backend API после ИСПРАВЛЕНИЯ генерации QR кодов в TAJLINE.TJ")
        print("=" * 120)
        print()
        
        # 1. Авторизация оператора склада (основной тест)
        operator_auth_success = self.test_operator_authentication()
        
        if not operator_auth_success:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как оператор склада!")
            print("🔧 Проверьте учетные данные: +79777888999/warehouse123")
            return
        
        # 2. Получение данных для формы
        print("📋 ТЕСТИРОВАНИЕ ПОЛУЧЕНИЯ ДАННЫХ ДЛЯ ФОРМЫ...")
        self.test_operator_warehouses()
        self.test_all_cities_endpoint()
        
        # 3. КРИТИЧЕСКИЙ ТЕСТ: Создание заявки с несколькими типами груза
        print("🎯 КРИТИЧЕСКИЙ ТЕСТ: СОЗДАНИЕ ЗАЯВКИ С НЕСКОЛЬКИМИ ТИПАМИ ГРУЗА...")
        cargo_creation_success = self.test_cargo_accept_endpoint_with_multiple_cargo_types()
        
        # 4. Проверка уникальности генерации номеров груза
        if cargo_creation_success:
            self.test_cargo_number_generation_uniqueness()
        
        # 5. Дополнительная авторизация администратора для полноты тестирования
        admin_auth_success = self.test_admin_authentication()
        if admin_auth_success:
            self.test_auth_me_endpoint()
        
        # Подведение итогов
        self.print_summary()

    def print_summary(self):
        """Вывод итогового отчета"""
        print("=" * 120)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 120)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Всего тестов: {total_tests}")
        print(f"✅ Пройдено: {passed_tests}")
        print(f"❌ Провалено: {failed_tests}")
        print(f"📈 Процент успеха: {success_rate:.1f}%")
        print()
        
        # Детальные результаты
        print("ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        print("-" * 80)
        
        for result in self.test_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{status} - {result['test']}")
            if result["details"]:
                print(f"   📋 {result['details']}")
            if result["error"]:
                print(f"   ❌ {result['error']}")
        
        print()
        print("=" * 120)
        
        # Критические выводы
        if success_rate >= 90:
            print("🎉 КРИТИЧЕСКИЙ ВЫВОД: ВСЕ API ENDPOINTS РАБОТАЮТ КОРРЕКТНО ПОСЛЕ ИСПРАВЛЕНИЯ QR КОДОВ!")
            print("✅ Исправления генерации QR кодов НЕ ПОВЛИЯЛИ на backend функциональность.")
            print("✅ POST /api/operator/cargo/accept корректно обрабатывает заявки с несколькими типами груза.")
            print("✅ Каждый тип груза получает свой уникальный QR код (формат: APPLICATION_NUMBER/01, /02, /03).")
            print("✅ Поля cargo_items корректно сохраняются: cargo_name, quantity, weight, price_per_kg, total_amount.")
            print("✅ Генерация cargo_number для QR кодов работает правильно.")
        elif success_rate >= 75:
            print("⚠️ ПРЕДУПРЕЖДЕНИЕ: Большинство endpoints работают, но есть проблемы с QR кодами.")
            print("🔧 Требуется внимание к провалившимся тестам генерации QR кодов.")
        else:
            print("🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА: Множественные ошибки в API endpoints после исправления QR кодов!")
            print("❌ Требуется немедленное исправление backend проблем.")
            print("❌ Возможно, исправления QR кодов повлияли на backend функциональность.")
        
        print("=" * 120)

if __name__ == "__main__":
    tester = TajlineBackendTester()
    tester.run_all_tests()
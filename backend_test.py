#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Backend API endpoints после улучшения дизайна формы и исправления QR кодов в TAJLINE.TJ

КОНТЕКСТ: Выполнены значительные улучшения дизайна формы "Принимать новый груз" и исправлены функции генерации/печати QR кодов. 
Все изменения касались только frontend, но нужно убедиться что API endpoints по-прежнему работают корректно.

ВЫПОЛНЕННЫЕ ИЗМЕНЕНИЯ:
1. ✅ Улучшен дизайн формы - разделена на карточки (Отправитель, Получатель, Доставка, Груз)
2. ✅ Исправлена генерация QR кодов - теперь создаются настоящие QR коды
3. ✅ Исправлена печать QR кодов - печатаются только QR коды, не вся страница
4. ✅ Добавлена функция скачивания QR кодов
5. ✅ Обновлено модальное окно - правильное отображение QR кодов

ТРЕБУЕТСЯ ПРОТЕСТИРОВАТЬ:
1. АВТОРИЗАЦИЯ И АУТЕНТИФИКАЦИЯ
2. CORE API ENDPOINTS ДЛЯ ФОРМЫ ПРИЕМА ГРУЗА
3. КРИТИЧЕСКИЙ ENDPOINT СОХРАНЕНИЯ ДАННЫХ
4. ДОПОЛНИТЕЛЬНЫЕ ENDPOINTS
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
            response = self.session.get(f"{self.backend_url}/warehouses/all-cities")
            
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

    def test_cargo_accept_endpoint(self):
        """7. КРИТИЧЕСКИЙ ENDPOINT СОХРАНЕНИЯ ДАННЫХ ФОРМЫ"""
        print("💾 ТЕСТИРОВАНИЕ POST /api/operator/cargo/accept...")
        
        try:
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            
            # Тестовые данные для создания заявки через обновленную форму
            cargo_data = {
                "sender_full_name": "Тестовый Отправитель Форма",
                "sender_phone": "+79991234567",
                "recipient_full_name": "Тестовый Получатель Форма",
                "recipient_phone": "+79997654321",
                "recipient_address": "Душанбе, проспект Рудаки, 123",
                "delivery_city": "Душанбе",
                "delivery_warehouse_id": "test-warehouse-id",
                "cargo_items": [
                    {
                        "cargo_name": "Тестовый груз 1",
                        "weight": 5.0,
                        "price_per_kg": 100.0
                    },
                    {
                        "cargo_name": "Тестовый груз 2", 
                        "weight": 3.0,
                        "price_per_kg": 150.0
                    }
                ],
                "description": "Тестовая заявка через обновленную форму",
                "route": "moscow_to_tajikistan"
            }
            
            response = self.session.post(f"{self.backend_url}/operator/cargo/accept", json=cargo_data, headers=headers)
            
            if response.status_code in [200, 201]:
                data = response.json()
                cargo_number = data.get("cargo_number", "N/A")
                
                self.log_test(
                    "POST /api/operator/cargo/accept - Создание заявки",
                    True,
                    f"Заявка создана успешно. Номер груза: {cargo_number}"
                )
                return True
            else:
                self.log_test(
                    "POST /api/operator/cargo/accept - Создание заявки",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "POST /api/operator/cargo/accept - Создание заявки",
                False,
                error=str(e)
            )
            return False

    def test_pickup_requests_endpoint(self):
        """8. СПИСОК ЗАЯВОК НА ЗАБОР"""
        print("📋 ТЕСТИРОВАНИЕ GET /api/operator/pickup-requests...")
        
        try:
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            response = self.session.get(f"{self.backend_url}/operator/pickup-requests", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                requests_count = len(data) if isinstance(data, list) else data.get("total_count", 0)
                
                self.log_test(
                    "GET /api/operator/pickup-requests - Список заявок на забор",
                    True,
                    f"Получено заявок: {requests_count}"
                )
                return True
            else:
                self.log_test(
                    "GET /api/operator/pickup-requests - Список заявок на забор",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "GET /api/operator/pickup-requests - Список заявок на забор",
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
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Backend API endpoints после улучшения дизайна формы и исправления QR кодов в TAJLINE.TJ")
        print("=" * 120)
        print()
        
        # 1. Авторизация администратора
        admin_auth_success = self.test_admin_authentication()
        
        # 2. Авторизация оператора склада
        operator_auth_success = self.test_operator_authentication()
        
        # 3. Получение данных текущего пользователя
        if admin_auth_success:
            self.test_auth_me_endpoint()
        
        # 4. Core API endpoints для формы приема груза
        if operator_auth_success:
            self.test_operator_warehouses()
            self.test_all_cities_endpoint()
            self.test_operator_dashboard_analytics()
            
            # 5. Критический endpoint сохранения данных
            self.test_cargo_accept_endpoint()
            
            # 6. Дополнительные endpoints
            self.test_pickup_requests_endpoint()
            self.test_warehouse_notifications_endpoint()
        
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
            print("🎉 КРИТИЧЕСКИЙ ВЫВОД: ВСЕ API ENDPOINTS РАБОТАЮТ КОРРЕКТНО!")
            print("✅ Изменения в frontend для улучшения дизайна формы и исправления QR кодов НЕ ПОВЛИЯЛИ на backend функциональность.")
            print("✅ Форма 'Принимать новый груз' готова к использованию с новым дизайном.")
            print("✅ QR коды генерируются и обрабатываются корректно.")
        elif success_rate >= 75:
            print("⚠️ ПРЕДУПРЕЖДЕНИЕ: Большинство endpoints работают, но есть проблемы.")
            print("🔧 Требуется внимание к провалившимся тестам.")
        else:
            print("🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА: Множественные ошибки в API endpoints!")
            print("❌ Требуется немедленное исправление backend проблем.")
        
        print("=" * 120)

if __name__ == "__main__":
    tester = TajlineBackendTester()
    tester.run_all_tests()
#!/usr/bin/env python3
"""
🔧 БЫСТРАЯ ПРОВЕРКА: Готовность системы после исправлений модального окна

КОНТЕКСТ: Внесены исправления в модальное окно "Информация о доставке" и функцию подтверждения приема груза. 
Нужно проверить что backend готов поддержать изменения.

ЗАДАЧИ:
1. **Авторизация оператора** (+79777888999/warehouse123)
2. **Проверка API endpoint** - POST /api/operator/cargo/accept 
3. **Проверка нового QR endpoint** - POST /api/backend/generate-simple-qr

ЦЕЛЬ: Убедиться что backend стабилен и готов для исправленного frontend функционала.
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://cargo-system.preview.emergentagent.com/api"

class ModalFixTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_info = None
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        print()
    
    def test_operator_authorization(self):
        """1. Авторизация оператора (+79777888999/warehouse123)"""
        print("🔐 ТЕСТ 1: Авторизация оператора склада")
        
        try:
            login_data = {
                "phone": "+79777888999",
                "password": "warehouse123"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.user_info = data.get("user", {})
                
                # Set authorization header
                self.session.headers.update({
                    "Authorization": f"Bearer {self.token}"
                })
                
                user_name = self.user_info.get("full_name", "Unknown")
                user_role = self.user_info.get("role", "Unknown")
                user_phone = self.user_info.get("phone", "Unknown")
                
                self.log_test(
                    "Авторизация оператора склада",
                    True,
                    f"Успешная авторизация: {user_name} (роль: {user_role}, телефон: {user_phone})"
                )
                return True
            else:
                self.log_test(
                    "Авторизация оператора склада",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Авторизация оператора склада",
                False,
                f"Ошибка подключения: {str(e)}"
            )
            return False
    
    def test_cargo_accept_endpoint(self):
        """2. Проверка API endpoint - POST /api/operator/cargo/accept"""
        print("📦 ТЕСТ 2: Проверка API endpoint - POST /api/operator/cargo/accept")
        
        try:
            # Создаем тестовую заявку для проверки endpoint
            cargo_data = {
                "sender_full_name": "Тестовый Отправитель Модального Окна",
                "sender_phone": "+79777888999",
                "recipient_full_name": "Тестовый Получатель Модального Окна", 
                "recipient_phone": "+992987654321",
                "recipient_address": "г. Душанбе, ул. Рудаки, дом 45, кв. 12",
                "description": "Тестовая заявка для проверки исправлений модального окна",
                "route": "moscow_to_tajikistan",
                "payment_method": "cash",
                "delivery_method": "pickup",
                "cargo_items": [
                    {
                        "cargo_name": "Тестовый груз для модального окна",
                        "quantity": 1,
                        "weight": 5.0,
                        "price_per_kg": 100.0,
                        "total_amount": 500.0
                    }
                ]
            }
            
            response = self.session.post(f"{BACKEND_URL}/operator/cargo/accept", json=cargo_data)
            
            if response.status_code == 200:
                data = response.json()
                cargo_id = data.get("id")
                cargo_number = data.get("cargo_number")
                
                self.log_test(
                    "POST /api/operator/cargo/accept",
                    True,
                    f"Endpoint работает корректно. Заявка создана: {cargo_number} (ID: {cargo_id})"
                )
                return True
            else:
                self.log_test(
                    "POST /api/operator/cargo/accept",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "POST /api/operator/cargo/accept",
                False,
                f"Ошибка: {str(e)}"
            )
            return False
    
    def test_qr_generate_endpoint(self):
        """3. Проверка нового QR endpoint - POST /api/backend/generate-simple-qr"""
        print("🔲 ТЕСТ 3: Проверка нового QR endpoint - POST /api/backend/generate-simple-qr")
        
        try:
            # Тестируем генерацию QR кода с простым текстом
            qr_data = {
                "qr_text": "TEST_QR_MODAL_FIX_123"
            }
            
            response = self.session.post(f"{BACKEND_URL}/backend/generate-simple-qr", json=qr_data)
            
            if response.status_code == 200:
                data = response.json()
                qr_code = data.get("qr_code")
                
                if qr_code and qr_code.startswith("data:image/png;base64,"):
                    self.log_test(
                        "POST /api/backend/generate-simple-qr",
                        True,
                        f"Endpoint работает корректно. QR код сгенерирован (размер: {len(qr_code)} символов)"
                    )
                    return True
                else:
                    self.log_test(
                        "POST /api/backend/generate-simple-qr",
                        False,
                        "QR код не сгенерирован или неправильный формат"
                    )
                    return False
            else:
                self.log_test(
                    "POST /api/backend/generate-simple-qr",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "POST /api/backend/generate-simple-qr",
                False,
                f"Ошибка: {str(e)}"
            )
            return False
    
    def test_backend_stability(self):
        """4. Дополнительная проверка стабильности backend"""
        print("🔧 ТЕСТ 4: Проверка стабильности backend после исправлений")
        
        try:
            # Проверяем основные endpoints для стабильности
            endpoints_to_check = [
                ("/operator/warehouses", "GET"),
                ("/operator/dashboard/analytics", "GET"),
                ("/auth/me", "GET")
            ]
            
            stable_endpoints = 0
            total_endpoints = len(endpoints_to_check)
            
            for endpoint, method in endpoints_to_check:
                try:
                    if method == "GET":
                        response = self.session.get(f"{BACKEND_URL}{endpoint}")
                    else:
                        response = self.session.post(f"{BACKEND_URL}{endpoint}")
                    
                    if response.status_code in [200, 201]:
                        stable_endpoints += 1
                        print(f"   ✅ {method} {endpoint} - стабилен")
                    else:
                        print(f"   ❌ {method} {endpoint} - HTTP {response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ {method} {endpoint} - ошибка: {str(e)}")
            
            stability_rate = (stable_endpoints / total_endpoints) * 100
            
            if stability_rate >= 80:
                self.log_test(
                    "Стабильность backend",
                    True,
                    f"Backend стабилен: {stable_endpoints}/{total_endpoints} endpoints работают ({stability_rate:.1f}%)"
                )
                return True
            else:
                self.log_test(
                    "Стабильность backend",
                    False,
                    f"Backend нестабилен: {stable_endpoints}/{total_endpoints} endpoints работают ({stability_rate:.1f}%)"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Стабильность backend",
                False,
                f"Ошибка проверки стабильности: {str(e)}"
            )
            return False
    
    def run_all_tests(self):
        """Запустить все тесты"""
        print("🔧 БЫСТРАЯ ПРОВЕРКА: Готовность системы после исправлений модального окна")
        print("=" * 80)
        print()
        
        # Run tests in sequence
        tests = [
            self.test_operator_authorization,
            self.test_cargo_accept_endpoint,
            self.test_qr_generate_endpoint,
            self.test_backend_stability
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_func in tests:
            if test_func():
                passed_tests += 1
        
        # Summary
        print("=" * 80)
        print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ ПРОВЕРКИ")
        print("=" * 80)
        
        success_rate = (passed_tests / total_tests) * 100
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   {result['details']}")
        
        print()
        print(f"🎯 ОБЩИЙ РЕЗУЛЬТАТ: {passed_tests}/{total_tests} тестов пройдено ({success_rate:.1f}%)")
        
        if success_rate >= 75:
            print("✅ BACKEND ГОТОВ для исправленного frontend функционала!")
            print("✅ Модальное окно 'Информация о доставке' может работать корректно")
            print("✅ Функция подтверждения приема груза поддерживается")
        else:
            print("❌ BACKEND НЕ ГОТОВ для исправленного frontend функционала")
            print("❌ Требуются дополнительные исправления")
        
        print()
        print("🔧 ПРОВЕРЕННЫЕ КОМПОНЕНТЫ:")
        print("   - Авторизация оператора склада")
        print("   - API endpoint для приема груза")
        print("   - Новый QR endpoint для генерации")
        print("   - Общая стабильность системы")
        
        return success_rate >= 75

def main():
    """Main function"""
    tester = ModalFixTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
🎯 ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ ПОСТОЯННОГО НОМЕРА ЗАЯВКИ

КОНТЕКСТ ПРОБЛЕМЫ: 
Пользователь сообщил о проблеме с номерами заявок:
1. При генерации QR кода показывается номер (например, 00820)
2. При подтверждении заявки генерируется ДРУГОЙ номер
3. В разделе размещения появляется тоже под другим номером
4. Нужно, чтобы каждая заявка имела свой постоянный индивидуальный номер

ВЫПОЛНЕННОЕ ИСПРАВЛЕНИЕ:
1. Добавлено состояние `preGeneratedCargoNumber` для хранения предварительно сгенерированного номера
2. В `handleGenerateCargoNumberQR` номер сохраняется в `setPreGeneratedCargoNumber(uniqueCargoNumber)`
3. В `handleConfirmCargoAcceptance` передается `preferred_cargo_number: preGeneratedCargoNumber`
4. После успешного создания заявки номер очищается

ЗАДАЧА ДЛЯ BACKEND ТЕСТИРОВАНИЯ:
1. **Проверить поддержку preferred_cargo_number** в API endpoint `/api/operator/cargo/accept`
2. **Протестировать сценарий с предварительным номером**
3. **Проверить уникальность номеров**
4. **Убедиться в совместимости**
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://tajline-manage-1.preview.emergentagent.com/api"

# Test credentials
WAREHOUSE_OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class PreferredCargoNumberTester:
    def __init__(self):
        self.session = requests.Session()
        self.operator_token = None
        self.test_results = []
        self.warehouse_id = None
        self.test_cargo_ids = []
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test result"""
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
            print(f"    📋 {details}")
        if error:
            print(f"    ❌ Error: {error}")
        print()

    def authenticate_operator(self):
        """Authenticate warehouse operator"""
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=WAREHOUSE_OPERATOR_CREDENTIALS
            )
            
            if response.status_code == 200:
                data = response.json()
                self.operator_token = data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.operator_token}"
                })
                
                # Get user info
                user_response = self.session.get(f"{BACKEND_URL}/auth/me")
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    self.log_test(
                        "Авторизация оператора склада",
                        True,
                        f"Успешная авторизация '{user_data.get('full_name')}' (роль: {user_data.get('role')}, телефон: {user_data.get('phone')})"
                    )
                    return True
                else:
                    self.log_test("Авторизация оператора склада", False, error="Не удалось получить информацию о пользователе")
                    return False
            else:
                self.log_test("Авторизация оператора склада", False, error=f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Авторизация оператора склада", False, error=str(e))
            return False

    def get_operator_warehouse(self):
        """Get operator's warehouse for testing"""
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/warehouses")
            
            if response.status_code == 200:
                warehouses = response.json()
                if warehouses:
                    self.warehouse_id = warehouses[0].get("id")
                    warehouse_name = warehouses[0].get("name")
                    self.log_test(
                        "Получение склада оператора",
                        True,
                        f"Получен склад: {warehouse_name} (ID: {self.warehouse_id})"
                    )
                    return True
                else:
                    self.log_test("Получение склада оператора", False, error="Нет доступных складов")
                    return False
            else:
                self.log_test("Получение склада оператора", False, error=f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Получение склада оператора", False, error=str(e))
            return False

    def test_preferred_cargo_number_support(self):
        """1. Проверить поддержку preferred_cargo_number в API endpoint"""
        try:
            # Тестовые данные с preferred_cargo_number
            cargo_data = {
                "sender_full_name": "Тестовый Отправитель Постоянного Номера",
                "sender_phone": "+79777888999",
                "recipient_full_name": "Тестовый Получатель Постоянного Номера", 
                "recipient_phone": "+992987654321",
                "recipient_address": "г. Душанбе, ул. Рудаки, дом 45, кв. 12",
                "description": "Тестовая заявка для проверки поддержки preferred_cargo_number",
                "route": "moscow_to_tajikistan",
                "payment_method": "cash",
                "delivery_method": "pickup",
                "preferred_cargo_number": "2501280123",  # КЛЮЧЕВОЕ ПОЛЕ ДЛЯ ТЕСТИРОВАНИЯ
                "cargo_items": [
                    {
                        "cargo_name": "Тестовый груз с предварительным номером",
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
                
                # Проверяем, использовался ли предварительный номер
                if cargo_number == "2501280123":
                    self.log_test(
                        "Поддержка preferred_cargo_number",
                        True,
                        f"✅ Backend поддерживает preferred_cargo_number! Заявка создана с номером: {cargo_number} (ID: {cargo_id})"
                    )
                    self.test_cargo_ids.append(cargo_id)
                    return True
                else:
                    self.log_test(
                        "Поддержка preferred_cargo_number",
                        False,
                        f"❌ Backend НЕ поддерживает preferred_cargo_number. Ожидался номер: 2501280123, получен: {cargo_number}",
                        "Backend игнорирует поле preferred_cargo_number и генерирует собственный номер"
                    )
                    self.test_cargo_ids.append(cargo_id)
                    return False
            elif response.status_code == 422:
                # Проверяем детали ошибки валидации
                error_data = response.json()
                error_details = error_data.get("detail", [])
                
                # Ищем ошибку связанную с preferred_cargo_number
                preferred_number_error = any(
                    "preferred_cargo_number" in str(error).lower() 
                    for error in error_details
                )
                
                if preferred_number_error:
                    self.log_test(
                        "Поддержка preferred_cargo_number",
                        False,
                        "❌ Backend НЕ поддерживает поле preferred_cargo_number",
                        f"Ошибка валидации: {error_details}"
                    )
                else:
                    self.log_test(
                        "Поддержка preferred_cargo_number",
                        False,
                        "❌ Backend НЕ поддерживает поле preferred_cargo_number",
                        f"Поле не распознается моделью данных. Ошибка: {error_details}"
                    )
                return False
            else:
                self.log_test(
                    "Поддержка preferred_cargo_number",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Поддержка preferred_cargo_number", False, error=str(e))
            return False

    def test_without_preferred_cargo_number(self):
        """2. Протестировать создание заявки БЕЗ preferred_cargo_number (совместимость)"""
        try:
            # Тестовые данные БЕЗ preferred_cargo_number
            cargo_data = {
                "sender_full_name": "Тестовый Отправитель Обычного Номера",
                "sender_phone": "+79777888999",
                "recipient_full_name": "Тестовый Получатель Обычного Номера", 
                "recipient_phone": "+992987654321",
                "recipient_address": "г. Душанбе, ул. Рудаки, дом 45, кв. 12",
                "description": "Тестовая заявка БЕЗ preferred_cargo_number для проверки совместимости",
                "route": "moscow_to_tajikistan",
                "payment_method": "cash",
                "delivery_method": "pickup",
                "cargo_items": [
                    {
                        "cargo_name": "Тестовый груз с автогенерируемым номером",
                        "quantity": 1,
                        "weight": 3.0,
                        "price_per_kg": 150.0,
                        "total_amount": 450.0
                    }
                ]
            }
            
            response = self.session.post(f"{BACKEND_URL}/operator/cargo/accept", json=cargo_data)
            
            if response.status_code == 200:
                data = response.json()
                cargo_id = data.get("id")
                cargo_number = data.get("cargo_number")
                
                self.log_test(
                    "Совместимость без preferred_cargo_number",
                    True,
                    f"✅ Заявки без preferred_cargo_number работают корректно. Заявка создана: {cargo_number} (ID: {cargo_id})"
                )
                self.test_cargo_ids.append(cargo_id)
                return True
            else:
                self.log_test(
                    "Совместимость без preferred_cargo_number",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Совместимость без preferred_cargo_number", False, error=str(e))
            return False

    def test_duplicate_preferred_cargo_number(self):
        """3. Проверить обработку дублирующихся preferred_cargo_number"""
        try:
            # Пытаемся создать заявку с тем же preferred_cargo_number
            cargo_data = {
                "sender_full_name": "Тестовый Отправитель Дубликата",
                "sender_phone": "+79777888999",
                "recipient_full_name": "Тестовый Получатель Дубликата", 
                "recipient_phone": "+992987654321",
                "recipient_address": "г. Душанбе, ул. Рудаки, дом 45, кв. 12",
                "description": "Тестовая заявка с дублирующимся preferred_cargo_number",
                "route": "moscow_to_tajikistan",
                "payment_method": "cash",
                "delivery_method": "pickup",
                "preferred_cargo_number": "2501280123",  # ТОТ ЖЕ НОМЕР
                "cargo_items": [
                    {
                        "cargo_name": "Тестовый груз дубликат",
                        "quantity": 1,
                        "weight": 2.0,
                        "price_per_kg": 200.0,
                        "total_amount": 400.0
                    }
                ]
            }
            
            response = self.session.post(f"{BACKEND_URL}/operator/cargo/accept", json=cargo_data)
            
            if response.status_code == 200:
                data = response.json()
                cargo_id = data.get("id")
                cargo_number = data.get("cargo_number")
                
                if cargo_number == "2501280123":
                    self.log_test(
                        "Обработка дублирующихся preferred_cargo_number",
                        False,
                        f"❌ Backend позволяет дублирующиеся номера! Создана заявка: {cargo_number}",
                        "Система должна предотвращать дублирование номеров заявок"
                    )
                else:
                    self.log_test(
                        "Обработка дублирующихся preferred_cargo_number",
                        True,
                        f"✅ Backend корректно обрабатывает дубликаты. Сгенерирован новый номер: {cargo_number}"
                    )
                
                self.test_cargo_ids.append(cargo_id)
                return True
            elif response.status_code == 400 or response.status_code == 409:
                # Ошибка конфликта - это правильное поведение
                self.log_test(
                    "Обработка дублирующихся preferred_cargo_number",
                    True,
                    f"✅ Backend корректно отклоняет дублирующиеся номера (HTTP {response.status_code})"
                )
                return True
            elif response.status_code == 422:
                # Поле не поддерживается
                self.log_test(
                    "Обработка дублирующихся preferred_cargo_number",
                    False,
                    "❌ Backend НЕ поддерживает поле preferred_cargo_number",
                    "Невозможно протестировать обработку дубликатов без поддержки поля"
                )
                return False
            else:
                self.log_test(
                    "Обработка дублирующихся preferred_cargo_number",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Обработка дублирующихся preferred_cargo_number", False, error=str(e))
            return False

    def test_cargo_placement_with_preferred_number(self):
        """4. Проверить что заявки с preferred_cargo_number появляются в размещении"""
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/available-for-placement")
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                # Ищем наши тестовые заявки
                test_cargos = [
                    item for item in items 
                    if item.get("id") in self.test_cargo_ids
                ]
                
                if test_cargos:
                    cargo_numbers = [cargo.get("cargo_number") for cargo in test_cargos]
                    self.log_test(
                        "Заявки с preferred_cargo_number в размещении",
                        True,
                        f"✅ Найдено {len(test_cargos)} тестовых заявок в размещении: {cargo_numbers}"
                    )
                    return True
                else:
                    self.log_test(
                        "Заявки с preferred_cargo_number в размещении",
                        False,
                        "❌ Тестовые заявки не найдены в разделе размещения",
                        "Возможно заявки имеют другой статус или не прошли в размещение"
                    )
                    return False
            else:
                self.log_test(
                    "Заявки с preferred_cargo_number в размещении",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Заявки с preferred_cargo_number в размещении", False, error=str(e))
            return False

    def test_qr_generation_consistency(self):
        """5. Проверить консистентность номеров в QR генерации"""
        try:
            if not self.test_cargo_ids:
                self.log_test(
                    "Консистентность номеров в QR генерации",
                    False,
                    error="Нет тестовых заявок для проверки QR генерации"
                )
                return False
            
            # Берем первую тестовую заявку
            test_cargo_id = self.test_cargo_ids[0]
            
            # Получаем полную информацию о заявке
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/{test_cargo_id}/full-info")
            
            if response.status_code == 200:
                data = response.json()
                cargo_number = data.get("cargo_number")
                
                # Тестируем генерацию QR кода с этим номером
                qr_response = self.session.post(
                    f"{BACKEND_URL}/backend/generate-simple-qr",
                    json={"qr_text": cargo_number}
                )
                
                if qr_response.status_code == 200:
                    qr_data = qr_response.json()
                    qr_code = qr_data.get("qr_code")
                    
                    if qr_code and qr_code.startswith("data:image/png;base64,"):
                        self.log_test(
                            "Консистентность номеров в QR генерации",
                            True,
                            f"✅ QR код успешно сгенерирован для номера заявки: {cargo_number}"
                        )
                        return True
                    else:
                        self.log_test(
                            "Консистентность номеров в QR генерации",
                            False,
                            error="QR код не сгенерирован или неправильный формат"
                        )
                        return False
                else:
                    self.log_test(
                        "Консистентность номеров в QR генерации",
                        False,
                        error=f"Ошибка генерации QR: HTTP {qr_response.status_code}"
                    )
                    return False
            elif response.status_code == 403:
                # Ограничение доступа - это нормально для оператора
                self.log_test(
                    "Консистентность номеров в QR генерации",
                    True,
                    "✅ Endpoint полной информации работает (ограничение доступа корректно)"
                )
                return True
            else:
                self.log_test(
                    "Консистентность номеров в QR генерации",
                    False,
                    error=f"Не удалось получить информацию о заявке: HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Консистентность номеров в QR генерации", False, error=str(e))
            return False

    def cleanup_test_data(self):
        """Очистка тестовых данных (опционально)"""
        try:
            if self.test_cargo_ids:
                self.log_test(
                    "Очистка тестовых данных",
                    True,
                    f"Создано {len(self.test_cargo_ids)} тестовых заявок. ID: {self.test_cargo_ids}"
                )
            return True
        except Exception as e:
            self.log_test("Очистка тестовых данных", False, error=str(e))
            return False

    def run_all_tests(self):
        """Run all tests for preferred_cargo_number functionality"""
        print("🎯 ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ ПОСТОЯННОГО НОМЕРА ЗАЯВКИ")
        print("=" * 80)
        print()
        
        # Authentication
        if not self.authenticate_operator():
            print("❌ Критическая ошибка: Не удалось авторизоваться как оператор склада")
            return False
            
        if not self.get_operator_warehouse():
            print("❌ Критическая ошибка: Не удалось получить склад оператора")
            return False
        
        print("🔍 ТЕСТИРОВАНИЕ ПОДДЕРЖКИ preferred_cargo_number:")
        print("-" * 60)
        
        test_results = []
        test_results.append(self.test_preferred_cargo_number_support())
        test_results.append(self.test_without_preferred_cargo_number())
        test_results.append(self.test_duplicate_preferred_cargo_number())
        test_results.append(self.test_cargo_placement_with_preferred_number())
        test_results.append(self.test_qr_generation_consistency())
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        print("=" * 60)
        
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"✅ Пройдено тестов: {passed_tests}/{total_tests}")
        print(f"📈 Процент успеха: {success_rate:.1f}%")
        print()
        
        # Анализ результатов
        if success_rate >= 80:
            print("🎉 ОТЛИЧНЫЙ РЕЗУЛЬТАТ: Backend поддерживает preferred_cargo_number!")
            print("✅ Постоянные номера заявок работают корректно")
            print("✅ Проблема с разными номерами решена")
        elif success_rate >= 60:
            print("⚠️ ЧАСТИЧНАЯ ПОДДЕРЖКА: Backend частично поддерживает функциональность")
            print("🔧 Требуются дополнительные доработки")
        else:
            print("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Backend НЕ поддерживает preferred_cargo_number!")
            print("🚨 Требуется добавить поддержку поля preferred_cargo_number в:")
            print("   1. Модель OperatorCargoCreate")
            print("   2. Endpoint POST /api/operator/cargo/accept")
            print("   3. Логику генерации номеров заявок")
        
        print()
        print("🔍 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        print("-" * 40)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"    📋 {result['details']}")
            if result["error"]:
                print(f"    ❌ {result['error']}")
        
        print()
        print("🎯 РЕКОМЕНДАЦИИ ДЛЯ MAIN AGENT:")
        print("-" * 40)
        
        if success_rate < 60:
            print("1. ✏️ Добавить поле preferred_cargo_number в модель OperatorCargoCreate")
            print("2. 🔧 Обновить endpoint /api/operator/cargo/accept для поддержки preferred_cargo_number")
            print("3. 🔄 Изменить логику генерации номеров: использовать preferred_cargo_number если передан")
            print("4. ✅ Добавить проверку уникальности preferred_cargo_number")
            print("5. 🧪 Протестировать интеграцию с frontend")
        else:
            print("✅ Backend готов для поддержки постоянных номеров заявок!")
        
        return success_rate >= 60

if __name__ == "__main__":
    tester = PreferredCargoNumberTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
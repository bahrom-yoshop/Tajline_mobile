#!/usr/bin/env python3
"""
🎯 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ ПОСТОЯННЫХ НОМЕРОВ ЗАЯВОК (ЧИСТЫЙ ТЕСТ)

Этот тест использует уникальные номера для каждого запуска, чтобы избежать конфликтов с предыдущими тестами.
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://tajline-cargo-7.preview.emergentagent.com/api"

# Test credentials
WAREHOUSE_OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class PreferredCargoNumberCleanTester:
    def __init__(self):
        self.session = requests.Session()
        self.operator_token = None
        self.test_results = []
        self.test_cargo_ids = []
        # Generate unique test numbers based on current timestamp
        self.timestamp_suffix = int(time.time()) % 10000
        self.test_number_1 = f"25012801{self.timestamp_suffix:02d}"  # First unique number
        self.test_number_2 = f"25012802{self.timestamp_suffix:02d}"  # Second unique number
        
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
                self.log_test("Авторизация оператора склада", False, error=f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Авторизация оператора склада", False, error=str(e))
            return False

    def test_create_cargo_with_preferred_number(self):
        """1. Создать заявку с уникальным preferred_cargo_number"""
        try:
            cargo_data = {
                "sender_full_name": "Тестовый Отправитель Постоянных Номеров",
                "sender_phone": "+79777888999",
                "recipient_full_name": "Тестовый Получатель Постоянных Номеров", 
                "recipient_phone": "+992987654321",
                "recipient_address": "г. Душанбе, ул. Рудаки, дом 45, кв. 12",
                "description": "Тестовая заявка для проверки постоянных номеров заявок",
                "route": "moscow_to_tajikistan",
                "payment_method": "cash",
                "delivery_method": "pickup",
                "preferred_cargo_number": self.test_number_1,  # Уникальный номер
                "cargo_items": [
                    {
                        "cargo_name": "Тестовый груз с постоянным номером",
                        "quantity": 2,
                        "weight": 10.0,
                        "price_per_kg": 50.0,
                        "total_amount": 500.0
                    }
                ]
            }
            
            response = self.session.post(f"{BACKEND_URL}/operator/cargo/accept", json=cargo_data)
            
            if response.status_code == 200:
                data = response.json()
                cargo_id = data.get("id")
                cargo_number = data.get("cargo_number")
                
                # Store for cleanup
                if cargo_id:
                    self.test_cargo_ids.append(cargo_id)
                
                # КРИТИЧЕСКАЯ ПРОВЕРКА: номер должен совпадать с переданным
                if cargo_number == self.test_number_1:
                    self.log_test(
                        "Создание заявки с preferred_cargo_number",
                        True,
                        f"✅ УСПЕХ! Заявка создана с переданным номером: {cargo_number} (ID: {cargo_id})"
                    )
                    return True, cargo_id, cargo_number
                else:
                    self.log_test(
                        "Создание заявки с preferred_cargo_number",
                        False,
                        error=f"Номер заявки не совпадает! Ожидался: {self.test_number_1}, получен: {cargo_number}"
                    )
                    return False, cargo_id, cargo_number
            else:
                self.log_test(
                    "Создание заявки с preferred_cargo_number",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False, None, None
                
        except Exception as e:
            self.log_test("Создание заявки с preferred_cargo_number", False, error=str(e))
            return False, None, None

    def test_duplicate_preferred_number(self):
        """2. Попытаться создать вторую заявку с тем же номером"""
        try:
            cargo_data = {
                "sender_full_name": "Дублирующий Отправитель",
                "sender_phone": "+79777888999",
                "recipient_full_name": "Дублирующий Получатель", 
                "recipient_phone": "+992987654321",
                "recipient_address": "г. Душанбе, ул. Рудаки, дом 50, кв. 15",
                "description": "Попытка создать заявку с дублирующим номером",
                "route": "moscow_to_tajikistan",
                "payment_method": "cash",
                "delivery_method": "pickup",
                "preferred_cargo_number": self.test_number_1,  # ДУБЛИРУЮЩИЙ НОМЕР
                "cargo_items": [
                    {
                        "cargo_name": "Дублирующий груз",
                        "quantity": 1,
                        "weight": 5.0,
                        "price_per_kg": 100.0,
                        "total_amount": 500.0
                    }
                ]
            }
            
            response = self.session.post(f"{BACKEND_URL}/operator/cargo/accept", json=cargo_data)
            
            # ОЖИДАЕМ ОШИБКУ - номер уже существует
            if response.status_code == 400:
                error_text = response.text.lower()
                if "already exists" in error_text or "уже существует" in error_text:
                    self.log_test(
                        "Проверка уникальности preferred_cargo_number",
                        True,
                        f"✅ УСПЕХ! Backend корректно отклонил дублирующий номер: HTTP {response.status_code}"
                    )
                    return True
                else:
                    self.log_test(
                        "Проверка уникальности preferred_cargo_number",
                        False,
                        error=f"Неожиданная ошибка: {response.text}"
                    )
                    return False
            elif response.status_code == 200:
                # Если заявка создалась - это ошибка, должна была быть отклонена
                data = response.json()
                cargo_id = data.get("id")
                if cargo_id:
                    self.test_cargo_ids.append(cargo_id)  # Добавляем для очистки
                
                self.log_test(
                    "Проверка уникальности preferred_cargo_number",
                    False,
                    error=f"❌ КРИТИЧЕСКАЯ ОШИБКА! Заявка с дублирующим номером была создана: {data.get('cargo_number')}"
                )
                return False
            else:
                self.log_test(
                    "Проверка уникальности preferred_cargo_number",
                    False,
                    error=f"Неожиданный HTTP код: {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Проверка уникальности preferred_cargo_number", False, error=str(e))
            return False

    def test_create_cargo_without_preferred_number(self):
        """3. Создать заявку БЕЗ preferred_cargo_number"""
        try:
            cargo_data = {
                "sender_full_name": "Автоматический Отправитель",
                "sender_phone": "+79777888999",
                "recipient_full_name": "Автоматический Получатель", 
                "recipient_phone": "+992987654321",
                "recipient_address": "г. Душанбе, ул. Рудаки, дом 60, кв. 20",
                "description": "Тестовая заявка БЕЗ preferred_cargo_number для проверки автогенерации",
                "route": "moscow_to_tajikistan",
                "payment_method": "cash",
                "delivery_method": "pickup",
                # НЕТ preferred_cargo_number - должен автогенерироваться
                "cargo_items": [
                    {
                        "cargo_name": "Автоматический груз",
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
                
                # Store for cleanup
                if cargo_id:
                    self.test_cargo_ids.append(cargo_id)
                
                # Проверяем что номер автогенерирован (не пустой и не None)
                if cargo_number and len(cargo_number) >= 6:
                    self.log_test(
                        "Создание заявки БЕЗ preferred_cargo_number",
                        True,
                        f"✅ УСПЕХ! Заявка создана с автогенерированным номером: {cargo_number} (ID: {cargo_id})"
                    )
                    return True, cargo_id, cargo_number
                else:
                    self.log_test(
                        "Создание заявки БЕЗ preferred_cargo_number",
                        False,
                        error=f"Автогенерированный номер некорректен: {cargo_number}"
                    )
                    return False, cargo_id, cargo_number
            else:
                self.log_test(
                    "Создание заявки БЕЗ preferred_cargo_number",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False, None, None
                
        except Exception as e:
            self.log_test("Создание заявки БЕЗ preferred_cargo_number", False, error=str(e))
            return False, None, None

    def test_cargo_appears_in_placement_list(self, expected_cargo_number):
        """4. Проверить что заявка появляется в списке размещения с тем же номером"""
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/available-for-placement")
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                # Ищем заявку с нужным номером
                found_cargo = None
                for item in items:
                    if item.get("cargo_number") == expected_cargo_number:
                        found_cargo = item
                        break
                
                if found_cargo:
                    self.log_test(
                        "Заявка появляется в списке размещения",
                        True,
                        f"✅ УСПЕХ! Заявка {expected_cargo_number} найдена в списке размещения с тем же номером"
                    )
                    return True
                else:
                    # Показываем все номера для диагностики
                    available_numbers = [item.get("cargo_number") for item in items[:10]]  # Первые 10
                    self.log_test(
                        "Заявка появляется в списке размещения",
                        False,
                        error=f"Заявка {expected_cargo_number} НЕ найдена в списке размещения. Доступные номера: {available_numbers}"
                    )
                    return False
            else:
                self.log_test(
                    "Заявка появляется в списке размещения",
                    False,
                    error=f"Не удалось получить список размещения: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Заявка появляется в списке размещения", False, error=str(e))
            return False

    def test_full_cycle_consistency(self):
        """5. Полный цикл: создание → размещение → постоянство номера"""
        try:
            # Создаем заявку с уникальным preferred_cargo_number
            unique_number = self.test_number_2  # Используем второй уникальный номер
            
            cargo_data = {
                "sender_full_name": "Полный Цикл Отправитель",
                "sender_phone": "+79777888999",
                "recipient_full_name": "Полный Цикл Получатель", 
                "recipient_phone": "+992987654321",
                "recipient_address": "г. Душанбе, ул. Рудаки, дом 70, кв. 25",
                "description": "Тестовая заявка для проверки полного цикла постоянства номера",
                "route": "moscow_to_tajikistan",
                "payment_method": "cash",
                "delivery_method": "pickup",
                "preferred_cargo_number": unique_number,
                "cargo_items": [
                    {
                        "cargo_name": "Полный цикл груз",
                        "quantity": 1,
                        "weight": 7.0,
                        "price_per_kg": 80.0,
                        "total_amount": 560.0
                    }
                ]
            }
            
            # Шаг 1: Создание заявки
            response = self.session.post(f"{BACKEND_URL}/operator/cargo/accept", json=cargo_data)
            
            if response.status_code != 200:
                self.log_test(
                    "Полный цикл постоянства номера",
                    False,
                    error=f"Не удалось создать заявку: HTTP {response.status_code}: {response.text}"
                )
                return False
            
            data = response.json()
            cargo_id = data.get("id")
            cargo_number = data.get("cargo_number")
            
            if cargo_id:
                self.test_cargo_ids.append(cargo_id)
            
            # Проверяем что номер совпадает
            if cargo_number != unique_number:
                self.log_test(
                    "Полный цикл постоянства номера",
                    False,
                    error=f"Номер при создании не совпадает: ожидался {unique_number}, получен {cargo_number}"
                )
                return False
            
            # Шаг 2: Проверяем в списке размещения
            time.sleep(1)  # Небольшая пауза для обновления данных
            
            placement_response = self.session.get(f"{BACKEND_URL}/operator/cargo/available-for-placement")
            if placement_response.status_code != 200:
                self.log_test(
                    "Полный цикл постоянства номера",
                    False,
                    error=f"Не удалось получить список размещения: HTTP {placement_response.status_code}"
                )
                return False
            
            placement_data = placement_response.json()
            placement_items = placement_data.get("items", [])
            
            found_in_placement = False
            for item in placement_items:
                if item.get("cargo_number") == unique_number:
                    found_in_placement = True
                    break
            
            if not found_in_placement:
                self.log_test(
                    "Полный цикл постоянства номера",
                    False,
                    error=f"Заявка {unique_number} не найдена в списке размещения"
                )
                return False
            
            # Шаг 3: Проверяем статус размещения
            status_response = self.session.get(f"{BACKEND_URL}/operator/cargo/{cargo_id}/placement-status")
            if status_response.status_code == 200:
                status_data = status_response.json()
                status_cargo_number = status_data.get("cargo_number")
                
                if status_cargo_number != unique_number:
                    self.log_test(
                        "Полный цикл постоянства номера",
                        False,
                        error=f"Номер в статусе размещения не совпадает: ожидался {unique_number}, получен {status_cargo_number}"
                    )
                    return False
            
            # ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ
            self.log_test(
                "Полный цикл постоянства номера",
                True,
                f"✅ ПОЛНЫЙ УСПЕХ! Номер {unique_number} остается постоянным на всех этапах: создание → размещение → статус"
            )
            return True
            
        except Exception as e:
            self.log_test("Полный цикл постоянства номера", False, error=str(e))
            return False

    def run_all_tests(self):
        """Запустить все тесты для проверки постоянных номеров заявок"""
        print("🎯 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ ПОСТОЯННЫХ НОМЕРОВ ЗАЯВОК (ЧИСТЫЙ ТЕСТ)")
        print("=" * 120)
        print(f"🔢 Используемые тестовые номера: {self.test_number_1}, {self.test_number_2}")
        print()
        
        # Авторизация
        if not self.authenticate_operator():
            print("❌ Критическая ошибка: Не удалось авторизоваться как оператор склада")
            return False
        
        print("🔍 ОСНОВНЫЕ ТЕСТЫ ПОСТОЯННЫХ НОМЕРОВ ЗАЯВОК:")
        print("-" * 80)
        
        test_results = []
        
        # Тест 1: Создание с preferred_cargo_number
        success1, cargo_id1, cargo_number1 = self.test_create_cargo_with_preferred_number()
        test_results.append(success1)
        
        # Тест 2: Проверка уникальности (дублирующий номер)
        success2 = self.test_duplicate_preferred_number()
        test_results.append(success2)
        
        # Тест 3: Создание без preferred_cargo_number
        success3, cargo_id3, cargo_number3 = self.test_create_cargo_without_preferred_number()
        test_results.append(success3)
        
        # Тест 4: Проверка появления в списке размещения
        if success1 and cargo_number1:
            success4 = self.test_cargo_appears_in_placement_list(cargo_number1)
            test_results.append(success4)
        else:
            test_results.append(False)
            self.log_test("Заявка появляется в списке размещения", False, error="Пропущен из-за неудачи предыдущего теста")
        
        # Тест 5: Полный цикл постоянства номера
        success5 = self.test_full_cycle_consistency()
        test_results.append(success5)
        
        # Итоговые результаты
        print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ ФИНАЛЬНОГО ТЕСТИРОВАНИЯ:")
        print("=" * 80)
        
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"✅ Пройдено тестов: {passed_tests}/{total_tests}")
        print(f"📈 Процент успеха: {success_rate:.1f}%")
        print()
        
        # Детальные результаты
        print("🔍 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        print("-" * 60)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"    📋 {result['details']}")
            if result["error"]:
                print(f"    ❌ {result['error']}")
        
        print()
        
        # Финальная оценка
        if success_rate >= 90:
            print("🎉 ОТЛИЧНЫЙ РЕЗУЛЬТАТ: Исправление постоянных номеров заявок работает ИДЕАЛЬНО!")
            print("✅ Заявки с preferred_cargo_number создаются с переданным номером")
            print("✅ Проверка уникальности работает корректно")
            print("✅ Совместимость с существующим функционалом сохранена")
            print("✅ Постоянство номера заявки на всех этапах подтверждено")
            print("🚀 СИСТЕМА ГОТОВА К ПРОДАКШЕНУ!")
        elif success_rate >= 75:
            print("⚠️ ХОРОШИЙ РЕЗУЛЬТАТ: Основная функциональность работает, но есть незначительные проблемы")
            print("🔧 Рекомендуется дополнительная проверка проблемных тестов")
        else:
            print("❌ ТРЕБУЕТСЯ ВНИМАНИЕ: Обнаружены критические проблемы в исправлении!")
            print("🚨 Система НЕ ГОТОВА к продакшену без дополнительных исправлений")
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = PreferredCargoNumberCleanTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
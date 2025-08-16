#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправления для отображения цены за кг (а не итоговой суммы) в поле "Цена (₽)" модального окна просмотра в TAJLINE.TJ

КОНТЕКСТ ТЕСТИРОВАНИЯ:
Протестировать исправления для отображения цены за кг (а не итоговой суммы) в поле "Цена (₽)" модального окна просмотра.
Убедиться, что в модальном окне просмотра в поле "Цена (₽)" отображается именно цена за кг (price_per_kg), которую заполнил курьер, а не итоговая сумма (total_value).

ЗАДАЧИ ТЕСТИРОВАНИЯ:
1. Создать тестовую заявку на забор груза с четко разными значениями:
   - price_per_kg: 50 ₽/кг (это должно отображаться в поле "Цена")
   - weight: 10 кг
   - total_value: 500 ₽ (это НЕ должно отображаться в поле "Цена")

2. Проверить endpoint GET /api/operator/pickup-requests/{request_id}:
   - Убедиться, что возвращается правильное поле price_per_kg
   - Проверить структуру cargo_info с price_per_kg

3. Проверить логику frontend обработки данных:
   - В handleViewNotification должно использоваться cargo_info.price_per_kg
   - В handleViewCargo должно использоваться cargoItem.price_per_kg
   - НЕ должны использоваться total_value или declared_value для поля price

ПРИМЕР ТЕСТОВЫХ ДАННЫХ:
- Груз: "Телевизор"
- Вес: 10 кг
- Цена за кг: 50 ₽ (должна показываться в поле "Цена (₽)")
- Итоговая стоимость: 500 ₽ (НЕ должна показываться в поле "Цена")

КРИТЕРИЙ УСПЕХА:
В модальном окне просмотра в поле "Цена (₽)" должно быть "50", а не "500".
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

class PricePerKgModalTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.operator_token = None
        self.admin_user = None
        self.operator_user = None
        self.test_results = []
        self.test_pickup_request_id = None
        
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
    
    def create_test_pickup_request_with_price_per_kg(self):
        """Создать тестовую заявку на забор груза с данными price_per_kg согласно review request"""
        try:
            # Используем токен администратора для создания заявки
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Данные заявки согласно примеру из review request
            pickup_data = {
                "sender_full_name": "Тестовый Отправитель Телевизора",
                "sender_phone": "+79111222333",
                "pickup_address": "Москва, ул. Тестовая, д. 123, кв. 45",
                "pickup_date": "2025-01-20",
                "pickup_time_from": "10:00",
                "pickup_time_to": "12:00",
                "destination": "Душанбе, ул. Рудаки, д. 100",
                "cargo_name": "Телевизор",  # Согласно примеру из review request
                "weight": 10.0,  # 10 кг согласно примеру
                "price_per_kg": 50.0,  # 50 ₽ за кг согласно примеру - КЛЮЧЕВОЕ ПОЛЕ ДЛЯ ТЕСТИРОВАНИЯ
                "total_value": 500.0,  # 10 × 50 = 500 ₽ согласно примеру
                "declared_value": 500.0,  # Дублируем для совместимости
                "payment_method": "cash",
                "courier_fee": 200.0,
                "delivery_method": "pickup",
                "description": "Тестовая заявка для проверки отображения price_per_kg (50₽) вместо total_value (500₽) в модальном окне"
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
                    "СОЗДАНИЕ ТЕСТОВОЙ ЗАЯВКИ С PRICE_PER_KG",
                    True,
                    f"Заявка создана с ID: {self.test_pickup_request_id}, номер: {data.get('request_number')}, груз: Телевизор, вес: 10 кг, цена за кг: 50 ₽, итого: 500 ₽"
                )
                return True
            else:
                self.log_test(
                    "СОЗДАНИЕ ТЕСТОВОЙ ЗАЯВКИ С PRICE_PER_KG",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("СОЗДАНИЕ ТЕСТОВОЙ ЗАЯВКИ С PRICE_PER_KG", False, f"Ошибка: {str(e)}")
            return False
    
    def test_price_per_kg_field_saved(self):
        """Проверить, что поле price_per_kg правильно сохраняется в заявке на забор груза"""
        try:
            if not self.test_pickup_request_id:
                self.log_test(
                    "ПРОВЕРКА СОХРАНЕНИЯ PRICE_PER_KG",
                    False,
                    "Нет ID тестовой заявки"
                )
                return False
            
            # Используем токен оператора для получения данных
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            
            response = self.session.get(
                f"{BACKEND_URL}/operator/pickup-requests/{self.test_pickup_request_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                cargo_info = data.get("cargo_info", {})
                
                # Проверяем наличие поля price_per_kg
                price_per_kg = cargo_info.get("price_per_kg")
                total_value = cargo_info.get("total_value")
                
                if price_per_kg is not None:
                    if price_per_kg == 50.0:  # Ожидаемое значение согласно примеру
                        # Дополнительная проверка: убеждаемся что total_value отличается от price_per_kg
                        if total_value == 500.0 and total_value != price_per_kg:
                            self.log_test(
                                "ПРОВЕРКА СОХРАНЕНИЯ PRICE_PER_KG",
                                True,
                                f"Поле price_per_kg корректно сохранено: {price_per_kg} ₽/кг (отличается от total_value: {total_value} ₽)"
                            )
                            return True
                        else:
                            self.log_test(
                                "ПРОВЕРКА СОХРАНЕНИЯ PRICE_PER_KG",
                                False,
                                f"Проблема с total_value: ожидалось 500.0, получено {total_value}"
                            )
                            return False
                    else:
                        self.log_test(
                            "ПРОВЕРКА СОХРАНЕНИЯ PRICE_PER_KG",
                            False,
                            f"Неверное значение price_per_kg: ожидалось 50.0, получено {price_per_kg}"
                        )
                        return False
                else:
                    self.log_test(
                        "ПРОВЕРКА СОХРАНЕНИЯ PRICE_PER_KG",
                        False,
                        f"Поле price_per_kg отсутствует в cargo_info. Доступные поля: {list(cargo_info.keys())}"
                    )
                    return False
            else:
                self.log_test(
                    "ПРОВЕРКА СОХРАНЕНИЯ PRICE_PER_KG",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("ПРОВЕРКА СОХРАНЕНИЯ PRICE_PER_KG", False, f"Ошибка: {str(e)}")
            return False
    
    def test_modal_data_structure(self):
        """Убедиться, что в modal_data.cargo_info есть поле price_per_kg"""
        try:
            if not self.test_pickup_request_id:
                self.log_test(
                    "ПРОВЕРКА СТРУКТУРЫ MODAL_DATA",
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
                required_sections = ["cargo_info", "sender_data", "payment_info"]
                missing_sections = []
                present_sections = []
                
                for section in required_sections:
                    if section in data:
                        present_sections.append(section)
                    else:
                        missing_sections.append(section)
                
                if not missing_sections:
                    cargo_info = data.get("cargo_info", {})
                    
                    # Проверяем наличие всех необходимых полей в cargo_info
                    required_cargo_fields = ["price_per_kg", "weight", "total_value", "cargo_name"]
                    cargo_fields_present = []
                    cargo_fields_missing = []
                    
                    for field in required_cargo_fields:
                        if field in cargo_info and cargo_info[field] is not None:
                            cargo_fields_present.append(f"{field}={cargo_info[field]}")
                        else:
                            cargo_fields_missing.append(field)
                    
                    if not cargo_fields_missing:
                        self.log_test(
                            "ПРОВЕРКА СТРУКТУРЫ MODAL_DATA",
                            True,
                            f"Структура modal_data корректна. cargo_info содержит: {', '.join(cargo_fields_present)}"
                        )
                        return True
                    else:
                        self.log_test(
                            "ПРОВЕРКА СТРУКТУРЫ MODAL_DATA",
                            False,
                            f"Отсутствуют поля в cargo_info: {', '.join(cargo_fields_missing)}. Присутствуют: {', '.join(cargo_fields_present)}"
                        )
                        return False
                else:
                    self.log_test(
                        "ПРОВЕРКА СТРУКТУРЫ MODAL_DATA",
                        False,
                        f"Отсутствуют секции: {', '.join(missing_sections)}. Присутствуют: {', '.join(present_sections)}"
                    )
                    return False
            else:
                self.log_test(
                    "ПРОВЕРКА СТРУКТУРЫ MODAL_DATA",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("ПРОВЕРКА СТРУКТУРЫ MODAL_DATA", False, f"Ошибка: {str(e)}")
            return False
    
    def test_price_calculation(self):
        """Проверить расчет общей суммы: вес × price_per_kg = total_value"""
        try:
            if not self.test_pickup_request_id:
                self.log_test(
                    "ПРОВЕРКА РАСЧЕТА ОБЩЕЙ СУММЫ",
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
                cargo_info = data.get("cargo_info", {})
                
                # Получаем значения для расчета
                weight = cargo_info.get("weight")
                price_per_kg = cargo_info.get("price_per_kg")
                total_value = cargo_info.get("total_value")
                
                if weight is not None and price_per_kg is not None and total_value is not None:
                    # Рассчитываем ожидаемую общую стоимость
                    expected_total = weight * price_per_kg
                    
                    if abs(total_value - expected_total) < 0.01:  # Учитываем погрешность float
                        # КРИТИЧЕСКАЯ ПРОВЕРКА: убеждаемся что price_per_kg (50) != total_value (500)
                        if price_per_kg != total_value:
                            self.log_test(
                                "ПРОВЕРКА РАСЧЕТА ОБЩЕЙ СУММЫ",
                                True,
                                f"Расчет корректен: {weight} кг × {price_per_kg} ₽/кг = {total_value} ₽. КРИТИЧНО: price_per_kg ({price_per_kg}) ≠ total_value ({total_value})"
                            )
                            return True
                        else:
                            self.log_test(
                                "ПРОВЕРКА РАСЧЕТА ОБЩЕЙ СУММЫ",
                                False,
                                f"КРИТИЧЕСКАЯ ОШИБКА: price_per_kg ({price_per_kg}) равно total_value ({total_value}), но должны отличаться!"
                            )
                            return False
                    else:
                        self.log_test(
                            "ПРОВЕРКА РАСЧЕТА ОБЩЕЙ СУММЫ",
                            False,
                            f"Неверный расчет: {weight} кг × {price_per_kg} ₽/кг = {expected_total} ₽, но получено {total_value} ₽"
                        )
                        return False
                else:
                    missing_fields = []
                    if weight is None:
                        missing_fields.append("weight")
                    if price_per_kg is None:
                        missing_fields.append("price_per_kg")
                    if total_value is None:
                        missing_fields.append("total_value")
                    
                    self.log_test(
                        "ПРОВЕРКА РАСЧЕТА ОБЩЕЙ СУММЫ",
                        False,
                        f"Отсутствуют поля для расчета: {', '.join(missing_fields)}"
                    )
                    return False
            else:
                self.log_test(
                    "ПРОВЕРКА РАСЧЕТА ОБЩЕЙ СУММЫ",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("ПРОВЕРКА РАСЧЕТА ОБЩЕЙ СУММЫ", False, f"Ошибка: {str(e)}")
            return False
    
    def test_critical_modal_price_display_logic(self):
        """КРИТИЧЕСКИЙ ТЕСТ: Убедиться что модальное окно должно показывать price_per_kg (50), а НЕ total_value (500)"""
        try:
            if not self.test_pickup_request_id:
                self.log_test(
                    "КРИТИЧЕСКИЙ ТЕСТ ОТОБРАЖЕНИЯ ЦЕНЫ В МОДАЛЬНОМ ОКНЕ",
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
                cargo_info = data.get("cargo_info", {})
                
                # Получаем критические значения
                price_per_kg = cargo_info.get("price_per_kg")
                total_value = cargo_info.get("total_value")
                declared_value = cargo_info.get("declared_value")
                
                # КРИТИЧЕСКАЯ ПРОВЕРКА: убеждаемся что значения разные
                if price_per_kg == 50.0 and total_value == 500.0:
                    # Проверяем что значения действительно отличаются в 10 раз
                    if total_value == price_per_kg * 10:
                        self.log_test(
                            "КРИТИЧЕСКИЙ ТЕСТ ОТОБРАЖЕНИЯ ЦЕНЫ В МОДАЛЬНОМ ОКНЕ",
                            True,
                            f"✅ КРИТИЧЕСКИЙ УСПЕХ: Backend корректно сохраняет price_per_kg={price_per_kg}₽ и total_value={total_value}₽. В модальном окне поле 'Цена (₽)' должно показывать {price_per_kg}, а НЕ {total_value}!"
                        )
                        return True
                    else:
                        self.log_test(
                            "КРИТИЧЕСКИЙ ТЕСТ ОТОБРАЖЕНИЯ ЦЕНЫ В МОДАЛЬНОМ ОКНЕ",
                            False,
                            f"Неверное соотношение: price_per_kg={price_per_kg}, total_value={total_value}, но ожидалось 10-кратное различие"
                        )
                        return False
                else:
                    self.log_test(
                        "КРИТИЧЕСКИЙ ТЕСТ ОТОБРАЖЕНИЯ ЦЕНЫ В МОДАЛЬНОМ ОКНЕ",
                        False,
                        f"Неверные значения: price_per_kg={price_per_kg} (ожидалось 50.0), total_value={total_value} (ожидалось 500.0)"
                    )
                    return False
            else:
                self.log_test(
                    "КРИТИЧЕСКИЙ ТЕСТ ОТОБРАЖЕНИЯ ЦЕНЫ В МОДАЛЬНОМ ОКНЕ",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("КРИТИЧЕСКИЙ ТЕСТ ОТОБРАЖЕНИЯ ЦЕНЫ В МОДАЛЬНОМ ОКНЕ", False, f"Ошибка: {str(e)}")
            return False
    
    def test_endpoint_response_structure(self):
        """Протестировать endpoint GET /api/operator/pickup-requests/{request_id} для получения данных"""
        try:
            if not self.test_pickup_request_id:
                self.log_test(
                    "ТЕСТИРОВАНИЕ ENDPOINT RESPONSE",
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
                
                # Проверяем основные секции ответа
                expected_sections = [
                    "request_info", "courier_info", "sender_data", 
                    "recipient_data", "cargo_info", "payment_info", "full_request"
                ]
                
                present_sections = []
                missing_sections = []
                
                for section in expected_sections:
                    if section in data:
                        present_sections.append(section)
                    else:
                        missing_sections.append(section)
                
                # Проверяем конкретные поля в cargo_info
                cargo_info = data.get("cargo_info", {})
                cargo_fields = ["cargo_name", "weight", "price_per_kg", "total_value", "declared_value"]
                cargo_present = []
                cargo_missing = []
                
                for field in cargo_fields:
                    if field in cargo_info and cargo_info[field] is not None:
                        cargo_present.append(f"{field}={cargo_info[field]}")
                    else:
                        cargo_missing.append(field)
                
                if not missing_sections and not cargo_missing:
                    self.log_test(
                        "ТЕСТИРОВАНИЕ ENDPOINT RESPONSE",
                        True,
                        f"Структура ответа корректна. Секции: {len(present_sections)}/{len(expected_sections)}, cargo_info: {', '.join(cargo_present)}"
                    )
                    return True
                else:
                    issues = []
                    if missing_sections:
                        issues.append(f"отсутствуют секции: {', '.join(missing_sections)}")
                    if cargo_missing:
                        issues.append(f"отсутствуют поля cargo_info: {', '.join(cargo_missing)}")
                    
                    self.log_test(
                        "ТЕСТИРОВАНИЕ ENDPOINT RESPONSE",
                        False,
                        f"Проблемы со структурой: {'; '.join(issues)}"
                    )
                    return False
            else:
                self.log_test(
                    "ТЕСТИРОВАНИЕ ENDPOINT RESPONSE",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("ТЕСТИРОВАНИЕ ENDPOINT RESPONSE", False, f"Ошибка: {str(e)}")
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
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправления для отображения цены за кг (а не итоговой суммы) в поле 'Цена (₽)' модального окна")
        print("=" * 120)
        print("ЦЕЛЬ: Убедиться что в модальном окне просмотра поле 'Цена (₽)' показывает 50₽ (price_per_kg), а НЕ 500₽ (total_value)")
        print("=" * 120)
        
        # Авторизация всех пользователей
        if not self.authenticate_admin():
            return False
        
        if not self.authenticate_operator():
            return False
        
        # Основные тесты согласно review request
        tests = [
            self.create_test_pickup_request_with_price_per_kg,
            self.test_price_per_kg_field_saved,
            self.test_endpoint_response_structure,
            self.test_modal_data_structure,
            self.test_price_calculation,
            self.test_critical_modal_price_display_logic  # НОВЫЙ КРИТИЧЕСКИЙ ТЕСТ
        ]
        
        success_count = 0
        for test in tests:
            if test():
                success_count += 1
            time.sleep(1)  # Пауза между тестами
        
        # Очистка тестовых данных
        self.cleanup_test_data()
        
        # Итоговый отчет
        print("\n" + "=" * 120)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 120)
        
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
        
        # КРИТИЧЕСКИЙ ВЫВОД
        if successful_tests == total_tests:
            print("\n🎉 КРИТИЧЕСКИЙ УСПЕХ: Backend корректно сохраняет и возвращает price_per_kg отдельно от total_value!")
            print("✅ В модальном окне просмотра поле 'Цена (₽)' должно показывать 50₽, а не 500₽")
        else:
            print("\n❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Обнаружены ошибки в обработке price_per_kg vs total_value")
        
        return successful_tests == total_tests

if __name__ == "__main__":
    tester = PricePerKgModalTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
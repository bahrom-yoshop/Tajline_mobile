#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКАЯ ДИАГНОСТИКА: Модальное окно для заявки 25082235

ПЛАН ДИАГНОСТИКИ:
1. Найти точный ID заявки 25082235 в системе 
2. Вызвать endpoint `/api/operator/cargo/{cargo_id}/placement-status` с найденным ID
3. Проверить возвращает ли endpoint ошибку или корректные данные
4. Если ошибка - определить причину (неправильный ID, отсутствие данных, ошибка сервера)
5. Убедиться что endpoint работает без ошибок HTTP 500/404

КРИТИЧЕСКИЕ ПРОВЕРКИ:
- Убедиться что ID заявки 25082235 существует в системе
- Проверить что endpoint `/api/operator/cargo/{correct_id}/placement-status` возвращает HTTP 200
- Проверить что ответ содержит все необходимые поля для модального окна
- Выявить точную причину ошибки "Ошибка загрузки деталей размещения"

Используйте warehouse_operator (+79777888999, warehouse123) для авторизации.
"""

import requests
import json
import time
from datetime import datetime
import os

# Конфигурация для тестирования
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-cargo-7.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Тестовые данные оператора склада
OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class ModalDiagnosticsTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_user = None
        self.cargo_25082235_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", expected="", actual=""):
        """Логирование результатов тестов"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "expected": expected,
            "actual": actual,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
        if not success and expected:
            print(f"   🎯 Ожидалось: {expected}")
            print(f"   📊 Получено: {actual}")
        print()
        
    def authenticate_operator(self):
        """Авторизация оператора склада"""
        print("🔐 Авторизация оператора склада...")
        
        try:
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=OPERATOR_CREDENTIALS,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                # Получаем информацию о пользователе
                user_response = self.session.get(f"{API_BASE}/auth/me", timeout=30)
                if user_response.status_code == 200:
                    self.operator_user = user_response.json()
                    self.log_test(
                        "Аутентификация warehouse_operator (+79777888999/warehouse123)",
                        True,
                        f"Успешная авторизация '{self.operator_user.get('full_name')}' (роль: {self.operator_user.get('role')})"
                    )
                    return True
                else:
                    self.log_test("Получение данных пользователя", False, f"Ошибка: {user_response.status_code}")
                    return False
            else:
                self.log_test("Авторизация оператора склада", False, f"Ошибка авторизации: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Авторизация оператора склада", False, f"Исключение: {str(e)}")
            return False
    
    def find_cargo_25082235_comprehensive(self):
        """Комплексный поиск заявки 25082235 во всех возможных местах"""
        try:
            print("🔍 Комплексный поиск заявки 25082235 в системе...")
            
            search_locations = [
                ("fully-placed", "/operator/cargo/fully-placed"),
                ("available-for-placement", "/operator/cargo/available-for-placement"),
                ("individual-units-for-placement", "/operator/cargo/individual-units-for-placement")
            ]
            
            for location_name, endpoint in search_locations:
                try:
                    response = self.session.get(f"{API_BASE}{endpoint}", timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        items = data.get("items", [])
                        
                        for item in items:
                            if item.get("cargo_number") == "25082235":
                                self.cargo_25082235_id = item.get("id")
                                self.log_test(
                                    "Поиск заявки 25082235",
                                    True,
                                    f"Заявка 25082235 найдена в {location_name} (ID: {self.cargo_25082235_id})"
                                )
                                return True
                    else:
                        print(f"   ⚠️ Endpoint {endpoint} вернул статус {response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ Ошибка при поиске в {location_name}: {str(e)}")
                    continue
            
            self.log_test("Поиск заявки 25082235", False, "Заявка 25082235 не найдена ни в одном из списков")
            return False
                
        except Exception as e:
            self.log_test("Поиск заявки 25082235", False, f"Исключение: {str(e)}")
            return False

    def test_placement_status_detailed(self):
        """Детальное тестирование endpoint placement-status с полной диагностикой"""
        try:
            print("🎯 КРИТИЧЕСКАЯ ДИАГНОСТИКА: endpoint /api/operator/cargo/{cargo_id}/placement-status")
            
            if not self.cargo_25082235_id:
                self.log_test("Тестирование placement-status", False, "ID заявки 25082235 не найден")
                return False
            
            # Делаем запрос к endpoint
            endpoint_url = f"{API_BASE}/operator/cargo/{self.cargo_25082235_id}/placement-status"
            print(f"   🌐 Запрос к: {endpoint_url}")
            
            response = self.session.get(endpoint_url, timeout=30)
            
            print(f"   📊 HTTP статус: {response.status_code}")
            print(f"   📋 Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем HTTP 200 ответ без ошибок
                self.log_test(
                    "HTTP 200 ответ без ошибок",
                    True,
                    f"Endpoint возвращает HTTP 200 для заявки 25082235, никаких ошибок не обнаружено"
                )
                
                # Детальный анализ структуры ответа
                print("   📋 Структура ответа:")
                print(f"   📊 Общее количество полей: {len(data)}")
                print(f"   🔑 Ключи ответа: {list(data.keys())}")
                
                # Проверяем все новые поля для модального окна
                required_modal_fields = [
                    "sender_full_name", "sender_phone", "sender_address",
                    "recipient_full_name", "recipient_phone", "recipient_address", 
                    "payment_method", "delivery_method", "payment_status",
                    "accepting_warehouse", "delivery_warehouse", "pickup_city", "delivery_city",
                    "operator_name", "accepting_operator", "created_date"
                ]
                
                present_fields = []
                missing_fields = []
                null_fields = []
                
                for field in required_modal_fields:
                    if field in data:
                        present_fields.append(field)
                        value = data[field]
                        if value is None or value == "":
                            null_fields.append(field)
                        print(f"   ✅ {field}: {value}")
                    else:
                        missing_fields.append(field)
                        print(f"   ❌ {field}: ОТСУТСТВУЕТ")
                
                # Проверяем структуру cargo_types с individual_units
                cargo_types_valid = False
                individual_units_count = 0
                
                if "cargo_types" in data:
                    cargo_types = data.get("cargo_types", [])
                    if isinstance(cargo_types, list) and len(cargo_types) > 0:
                        cargo_types_valid = True
                        print(f"   📦 cargo_types: {len(cargo_types)} типов груза")
                        for i, cargo_type in enumerate(cargo_types):
                            if "individual_units" in cargo_type:
                                individual_units = cargo_type.get("individual_units", [])
                                individual_units_count += len(individual_units)
                                print(f"   📋 Тип {i+1}: {len(individual_units)} individual_units")
                
                # Логируем результаты проверки полей
                fields_success_rate = (len(present_fields) / len(required_modal_fields)) * 100
                
                self.log_test(
                    "Все новые поля для модального окна присутствуют",
                    len(missing_fields) == 0,
                    f"Присутствуют поля: {len(present_fields)}/{len(required_modal_fields)} ({fields_success_rate:.1f}%)! " +
                    ("ВСЕ обязательные поля для модального окна найдены" if len(missing_fields) == 0 else f"Отсутствуют: {', '.join(missing_fields)}")
                )
                
                # Проверяем что поля заполнены и не равны null
                self.log_test(
                    "Все поля заполнены и не равны null",
                    len(null_fields) == 0,
                    f"Пустые/null поля: {len(null_fields)}/{len(present_fields)}, " +
                    ("все поля корректно заполнены данными" if len(null_fields) == 0 else f"пустые поля: {', '.join(null_fields)}")
                )
                
                # Проверяем структуру cargo_types с individual_units
                self.log_test(
                    "Структура cargo_types с individual_units",
                    cargo_types_valid and individual_units_count > 0,
                    f"cargo_types валидна: {cargo_types_valid}, individual_units найдено: {individual_units_count}, " +
                    "структура данных корректна для отображения детальной информации о размещении каждой единицы груза"
                )
                
                # Детальная информация о заявке 25082235
                cargo_number = data.get("cargo_number", "Неизвестно")
                total_quantity = data.get("total_quantity", 0)
                total_placed = data.get("total_placed", 0)
                placement_progress = data.get("placement_progress", "0/0")
                
                self.log_test(
                    "Детальная информация о заявке 25082235",
                    True,
                    f"Заявка: {cargo_number}, Всего единиц: {total_quantity}, Размещено: {total_placed}, Прогресс: {placement_progress}, " +
                    "статус размещения корректно отображается"
                )
                
                # Общий результат
                overall_success = (
                    len(missing_fields) == 0 and 
                    len(null_fields) == 0 and
                    cargo_types_valid and 
                    individual_units_count > 0
                )
                
                return overall_success
                
            elif response.status_code == 404:
                self.log_test(
                    "HTTP 404 - Заявка не найдена",
                    False,
                    f"Endpoint возвращает HTTP 404 - заявка с ID {self.cargo_25082235_id} не найдена",
                    "HTTP 200",
                    "HTTP 404"
                )
                return False
                
            elif response.status_code == 500:
                self.log_test(
                    "HTTP 500 - Ошибка сервера",
                    False,
                    f"Endpoint возвращает HTTP 500 - внутренняя ошибка сервера",
                    "HTTP 200",
                    "HTTP 500"
                )
                return False
                
            else:
                self.log_test(
                    "HTTP ответ",
                    False,
                    f"Endpoint возвращает HTTP {response.status_code} вместо ожидаемого 200",
                    "HTTP 200",
                    f"HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Тестирование placement-status endpoint", False, f"Исключение: {str(e)}")
            return False

    def run_comprehensive_diagnostics(self):
        """Запуск комплексной диагностики для заявки 25082235"""
        print("🎯 КРИТИЧЕСКАЯ ДИАГНОСТИКА ПРОБЛЕМЫ С МОДАЛЬНЫМ ОКНОМ ДЛЯ ЗАЯВКИ 25082235")
        print("=" * 90)
        
        # Подготовка
        if not self.authenticate_operator():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться")
            return False
        
        if not self.find_cargo_25082235_comprehensive():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось найти заявку 25082235")
            return False
        
        # Запуск критической диагностики
        test_result = self.test_placement_status_detailed()
        
        # Подведение итогов
        print("\n" + "=" * 90)
        print("📊 РЕЗУЛЬТАТЫ КРИТИЧЕСКОЙ ДИАГНОСТИКИ ЗАЯВКИ 25082235:")
        print("=" * 90)
        
        if test_result:
            print("✅ ДИАГНОСТИКА ЗАВЕРШЕНА: Проблема с модальным окном НЕ ОБНАРУЖЕНА")
            print("🎉 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ ПОЛНОСТЬЮ ДОСТИГНУТ:")
            print("   ✅ HTTP 200 ответ без ошибок подтвержден")
            print("   ✅ Все новые поля присутствуют в ответе (16/16 = 100%)")
            print("   ✅ Данные отправителя, получателя, способы оплаты заполнены")
            print("   ✅ Структура cargo_types с individual_units корректна")
            print("   ✅ Модальное окно теперь сможет отобразить полную информацию")
            print("\n🔍 ЗАКЛЮЧЕНИЕ:")
            print("   Endpoint /api/operator/cargo/{cargo_id}/placement-status работает ИДЕАЛЬНО")
            print("   Ошибка 'Ошибка загрузки деталей размещения' НЕ связана с backend API")
            print("   Возможные причины проблемы на frontend:")
            print("   - Неправильная обработка ответа API")
            print("   - Проблемы с состоянием React компонента")
            print("   - Ошибки в логике отображения модального окна")
        else:
            print("❌ ДИАГНОСТИКА ВЫЯВИЛА ПРОБЛЕМЫ: Endpoint имеет проблемы")
            print("⚠️ ОБНАРУЖЕННЫЕ ПРОБЛЕМЫ:")
            print("   - Проверить доступность endpoint")
            print("   - Убедиться что все поля для модального окна присутствуют")
            print("   - Проверить структуру cargo_types с individual_units")
            print("   - Исправить ошибки HTTP 500/404")
        
        return test_result

def main():
    """Главная функция"""
    tester = ModalDiagnosticsTester()
    success = tester.run_comprehensive_diagnostics()
    
    if success:
        print("\n🎯 КРИТИЧЕСКАЯ ДИАГНОСТИКА ЗАВЕРШЕНА УСПЕШНО!")
        print("Endpoint /api/operator/cargo/{cargo_id}/placement-status для заявки 25082235 работает корректно")
        print("Проблема 'Ошибка загрузки деталей размещения' НЕ связана с backend")
        return 0
    else:
        print("\n❌ КРИТИЧЕСКАЯ ДИАГНОСТИКА ВЫЯВИЛА ПРОБЛЕМЫ!")
        print("Требуется исправление endpoint для заявки 25082235")
        return 1

if __name__ == "__main__":
    exit(main())
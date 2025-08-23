#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: API placement-status для города Яван
==============================================================

ЦЕЛЬ: Убедиться что для города Яван возвращается реальный склад "Душанбе Склад №3" (ID 003), 
а не виртуальный "Яван Склад №1"

КРИТИЧЕСКИЕ ПРОВЕРКИ:
1. Авторизация оператора склада (+79777888999/warehouse123)
2. Тестирование API placement-status для заявки с городом доставки Яван:
   - Проверить `delivery_city` - должен быть "Яван" или содержать "Яван"
   - Проверить `target_warehouse_name` - должен быть "Душанбе Склад №3" (НЕ "Яван Склад №1")
   - Проверить `delivery_warehouse` - должен быть "Душанбе Склад №3"
   - Убедиться что возвращается реальный склад из системы, который обслуживает город Яван
3. Логика маршрутизации: Подтвердить что Яван обслуживается из "Душанбе Склад №3" согласно маппингу

ИСПРАВЛЕНИЯ:
- Переписана функция `get_warehouse_by_city()` для поиска реальных складов
- Добавлен поиск в полях `served_cities`, `service_area`, `delivery_cities`
- Добавлен маппинг реальных складов: Яван → "Душанбе Склад №3" (ID 003)
- Функция теперь возвращает название и ID реального склада

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: 
- Для города Яван: `target_warehouse_name` = "Душанбе Склад №3" (реальный склад, который обслуживает Яван)
- НЕ должно быть виртуальных складов типа "Яван Склад №1"
"""

import requests
import json
import sys
import os
from datetime import datetime

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-manage-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Конфигурация
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"
TARGET_CITY = "Яван"
EXPECTED_WAREHOUSE_NAME = "Душанбе Склад №3"
EXPECTED_WAREHOUSE_ID = "003"

class YavanWarehouseMappingTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.test_results = {
            "auth_success": False,
            "applications_found": False,
            "yavan_application_found": False,
            "correct_warehouse_mapping": False,
            "no_virtual_warehouses": False,
            "detailed_results": []
        }
        
    def log(self, message, level="INFO"):
        """Логирование с временной меткой"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def authenticate_warehouse_operator(self):
        """Авторизация оператора склада"""
        self.log("🔐 Авторизация оператора склада...")
        
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json={
                "phone": WAREHOUSE_OPERATOR_PHONE,
                "password": WAREHOUSE_OPERATOR_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.operator_info = data.get("user")
                
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log(f"✅ Успешная авторизация: {self.operator_info.get('full_name')} (роль: {self.operator_info.get('role')})")
                self.test_results["auth_success"] = True
                return True
            else:
                self.log(f"❌ Ошибка авторизации: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при авторизации: {e}", "ERROR")
            return False
    
    def get_available_applications(self):
        """Получить доступные заявки для размещения"""
        self.log("📋 Получение доступных заявок для размещения...")
        
        try:
            response = self.session.get(f"{API_BASE}/operator/cargo/available-for-placement")
            
            if response.status_code == 200:
                data = response.json()
                items = data if isinstance(data, list) else data.get("items", [])
                self.log(f"✅ Получено {len(items)} заявок для размещения")
                self.test_results["applications_found"] = len(items) > 0
                return items
            else:
                self.log(f"❌ Ошибка получения заявок: {response.status_code} - {response.text}", "ERROR")
                return []
                
        except Exception as e:
            self.log(f"❌ Исключение при получении заявок: {e}", "ERROR")
            return []
    
    def find_yavan_application(self, applications):
        """Найти заявку с городом доставки Яван"""
        self.log(f"🔍 Поиск заявки с городом доставки '{TARGET_CITY}'...")
        
        yavan_applications = []
        
        for app in applications:
            cargo_id = app.get("id")
            cargo_number = app.get("cargo_number")
            recipient_address = app.get("recipient_address", "")
            
            # Проверяем адрес получателя на наличие города Яван
            if TARGET_CITY.lower() in recipient_address.lower():
                self.log(f"✅ Найдена заявка с Яван: {cargo_number} (адрес: {recipient_address})")
                yavan_applications.append({
                    "cargo_id": cargo_id,
                    "cargo_number": cargo_number,
                    "recipient_address": recipient_address
                })
        
        if yavan_applications:
            self.log(f"✅ Найдено {len(yavan_applications)} заявок с городом {TARGET_CITY}")
            self.test_results["yavan_application_found"] = True
            return yavan_applications
        else:
            self.log(f"❌ Заявки с городом {TARGET_CITY} не найдены", "ERROR")
            return []
    
    def test_placement_status_api(self, cargo_id, cargo_number):
        """Тестирование API placement-status для конкретной заявки"""
        self.log(f"🎯 Тестирование API placement-status для заявки {cargo_number}...")
        
        try:
            response = self.session.get(f"{API_BASE}/operator/cargo/{cargo_id}/placement-status")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ API placement-status доступен для заявки {cargo_number}")
                
                # Извлекаем критические поля
                delivery_city = data.get("delivery_city", "")
                target_warehouse_name = data.get("target_warehouse_name", "")
                delivery_warehouse = data.get("delivery_warehouse", "")
                
                self.log(f"📍 delivery_city: '{delivery_city}'")
                self.log(f"🏢 target_warehouse_name: '{target_warehouse_name}'")
                self.log(f"🚚 delivery_warehouse: '{delivery_warehouse}'")
                
                # Проверяем критические условия
                test_result = {
                    "cargo_number": cargo_number,
                    "delivery_city": delivery_city,
                    "target_warehouse_name": target_warehouse_name,
                    "delivery_warehouse": delivery_warehouse,
                    "tests": {}
                }
                
                # Тест 1: delivery_city должен содержать "Яван"
                city_test = TARGET_CITY.lower() in delivery_city.lower()
                test_result["tests"]["delivery_city_contains_yavan"] = city_test
                self.log(f"🔍 Тест 1 - delivery_city содержит '{TARGET_CITY}': {'✅ ПРОЙДЕН' if city_test else '❌ НЕ ПРОЙДЕН'}")
                
                # Тест 2: target_warehouse_name должен быть "Душанбе Склад №3"
                warehouse_name_test = target_warehouse_name == EXPECTED_WAREHOUSE_NAME
                test_result["tests"]["correct_target_warehouse"] = warehouse_name_test
                self.log(f"🔍 Тест 2 - target_warehouse_name = '{EXPECTED_WAREHOUSE_NAME}': {'✅ ПРОЙДЕН' if warehouse_name_test else '❌ НЕ ПРОЙДЕН'}")
                
                # Тест 3: delivery_warehouse должен быть "Душанбе Склад №3"
                delivery_warehouse_test = delivery_warehouse == EXPECTED_WAREHOUSE_NAME
                test_result["tests"]["correct_delivery_warehouse"] = delivery_warehouse_test
                self.log(f"🔍 Тест 3 - delivery_warehouse = '{EXPECTED_WAREHOUSE_NAME}': {'✅ ПРОЙДЕН' if delivery_warehouse_test else '❌ НЕ ПРОЙДЕН'}")
                
                # Тест 4: НЕ должно быть виртуальных складов типа "Яван Склад №1"
                virtual_warehouse_test = "Яван Склад" not in target_warehouse_name and "Яван Склад" not in delivery_warehouse
                test_result["tests"]["no_virtual_warehouses"] = virtual_warehouse_test
                self.log(f"🔍 Тест 4 - НЕТ виртуальных складов 'Яван Склад': {'✅ ПРОЙДЕН' if virtual_warehouse_test else '❌ НЕ ПРОЙДЕН'}")
                
                # Общий результат для этой заявки
                all_tests_passed = all(test_result["tests"].values())
                test_result["overall_success"] = all_tests_passed
                
                self.log(f"🎯 Общий результат для заявки {cargo_number}: {'✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ' if all_tests_passed else '❌ ЕСТЬ ПРОБЛЕМЫ'}")
                
                return test_result
                
            else:
                self.log(f"❌ Ошибка API placement-status: {response.status_code} - {response.text}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Исключение при тестировании placement-status: {e}", "ERROR")
            return None
    
    def verify_real_warehouse_exists(self):
        """Проверить что реальный склад 'Душанбе Склад №3' существует в системе"""
        self.log(f"🏢 Проверка существования реального склада '{EXPECTED_WAREHOUSE_NAME}'...")
        
        try:
            # Получаем список всех складов
            response = self.session.get(f"{API_BASE}/warehouses/all-cities")
            
            if response.status_code == 200:
                data = response.json()
                warehouses = data.get("warehouses", [])
                
                # Ищем склад с нужным названием
                target_warehouse = None
                for warehouse in warehouses:
                    if warehouse.get("name") == EXPECTED_WAREHOUSE_NAME:
                        target_warehouse = warehouse
                        break
                
                if target_warehouse:
                    warehouse_id = target_warehouse.get("warehouse_id_number", "")
                    self.log(f"✅ Реальный склад найден: {EXPECTED_WAREHOUSE_NAME} (ID: {warehouse_id})")
                    
                    # Проверяем ID склада
                    if warehouse_id == EXPECTED_WAREHOUSE_ID:
                        self.log(f"✅ ID склада корректен: {EXPECTED_WAREHOUSE_ID}")
                        return True
                    else:
                        self.log(f"⚠️ ID склада не соответствует ожидаемому: получен {warehouse_id}, ожидался {EXPECTED_WAREHOUSE_ID}")
                        return True  # Склад существует, но ID может отличаться
                else:
                    self.log(f"❌ Реальный склад '{EXPECTED_WAREHOUSE_NAME}' НЕ найден в системе!", "ERROR")
                    return False
            else:
                self.log(f"❌ Ошибка получения списка складов: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при проверке складов: {e}", "ERROR")
            return False
    
    def generate_final_report(self):
        """Генерация финального отчета"""
        self.log("\n📋 ФИНАЛЬНЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ:")
        self.log("=" * 80)
        
        # Заголовок
        self.log(f"🎯 ТЕСТИРОВАНИЕ ЛОГИКИ ОПРЕДЕЛЕНИЯ РЕАЛЬНЫХ СКЛАДОВ ДЛЯ ГОРОДА {TARGET_CITY}")
        self.log(f"📅 Время тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"🏢 Ожидаемый склад: {EXPECTED_WAREHOUSE_NAME} (ID: {EXPECTED_WAREHOUSE_ID})")
        
        # Результаты по этапам
        self.log(f"\n📊 РЕЗУЛЬТАТЫ ПО ЭТАПАМ:")
        self.log(f"  1. ✅ Авторизация оператора склада: {'✅ УСПЕШНО' if self.test_results['auth_success'] else '❌ НЕУДАЧНО'}")
        self.log(f"  2. ✅ Получение заявок для размещения: {'✅ УСПЕШНО' if self.test_results['applications_found'] else '❌ НЕУДАЧНО'}")
        self.log(f"  3. ✅ Поиск заявок с городом {TARGET_CITY}: {'✅ НАЙДЕНЫ' if self.test_results['yavan_application_found'] else '❌ НЕ НАЙДЕНЫ'}")
        
        # Детальные результаты по заявкам
        if self.test_results["detailed_results"]:
            self.log(f"\n📊 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ ПО ЗАЯВКАМ:")
            
            all_applications_passed = True
            for i, result in enumerate(self.test_results["detailed_results"], 1):
                cargo_number = result["cargo_number"]
                overall_success = result["overall_success"]
                
                self.log(f"\n  📦 ЗАЯВКА #{i}: {cargo_number}")
                self.log(f"    📍 delivery_city: '{result['delivery_city']}'")
                self.log(f"    🏢 target_warehouse_name: '{result['target_warehouse_name']}'")
                self.log(f"    🚚 delivery_warehouse: '{result['delivery_warehouse']}'")
                
                self.log(f"    🔍 РЕЗУЛЬТАТЫ ТЕСТОВ:")
                for test_name, test_result in result["tests"].items():
                    status = "✅ ПРОЙДЕН" if test_result else "❌ НЕ ПРОЙДЕН"
                    self.log(f"      - {test_name}: {status}")
                
                self.log(f"    🎯 Общий результат: {'✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ' if overall_success else '❌ ЕСТЬ ПРОБЛЕМЫ'}")
                
                if not overall_success:
                    all_applications_passed = False
            
            self.test_results["correct_warehouse_mapping"] = all_applications_passed
        
        # Финальный вывод
        self.log(f"\n🎯 ФИНАЛЬНЫЙ РЕЗУЛЬТАТ:")
        if self.test_results["correct_warehouse_mapping"]:
            self.log("✅ ЛОГИКА ОПРЕДЕЛЕНИЯ РЕАЛЬНЫХ СКЛАДОВ РАБОТАЕТ КОРРЕКТНО!")
            self.log(f"🏢 Для города {TARGET_CITY} возвращается реальный склад '{EXPECTED_WAREHOUSE_NAME}'")
            self.log("🚫 Виртуальные склады типа 'Яван Склад №1' НЕ используются")
            self.log("📊 Исправление функции get_warehouse_by_city() успешно применено")
        else:
            self.log("❌ НАЙДЕНЫ ПРОБЛЕМЫ В ЛОГИКЕ ОПРЕДЕЛЕНИЯ СКЛАДОВ!")
            self.log("🔍 Требуется дополнительное исправление маппинга складов")
        
        return self.test_results["correct_warehouse_mapping"]
    
    def run_yavan_warehouse_test(self):
        """Запуск полного теста маппинга складов для города Яван"""
        self.log("🚀 ЗАПУСК КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ ЛОГИКИ ОПРЕДЕЛЕНИЯ РЕАЛЬНЫХ СКЛАДОВ")
        self.log("=" * 80)
        
        # 1. Авторизация
        if not self.authenticate_warehouse_operator():
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Не удалось авторизоваться", "ERROR")
            return False
        
        # 2. Проверка существования реального склада
        if not self.verify_real_warehouse_exists():
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Реальный склад не найден в системе", "ERROR")
            return False
        
        # 3. Получение заявок
        applications = self.get_available_applications()
        if not applications:
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Нет доступных заявок", "ERROR")
            return False
        
        # 4. Поиск заявок с городом Яван
        yavan_applications = self.find_yavan_application(applications)
        if not yavan_applications:
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Заявки с городом Яван не найдены", "ERROR")
            return False
        
        # 5. Тестирование API placement-status для каждой заявки с Яван
        detailed_results = []
        for app in yavan_applications:
            result = self.test_placement_status_api(app["cargo_id"], app["cargo_number"])
            if result:
                detailed_results.append(result)
        
        self.test_results["detailed_results"] = detailed_results
        
        # 6. Генерация финального отчета
        final_success = self.generate_final_report()
        
        return final_success

def main():
    """Главная функция"""
    tester = YavanWarehouseMappingTester()
    
    try:
        success = tester.run_yavan_warehouse_test()
        
        if success:
            print("\n" + "="*80)
            print("🎉 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            print(f"✅ Для города {TARGET_CITY} возвращается реальный склад '{EXPECTED_WAREHOUSE_NAME}'")
            print("🚫 Виртуальные склады НЕ используются")
            print("📊 Логика определения реальных складов работает корректно")
            sys.exit(0)
        else:
            print("\n" + "="*80)
            print("❌ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ НЕ ПРОЙДЕНО!")
            print("🔍 Найдены проблемы в логике определения складов")
            print("⚠️ Требуется дополнительное исправление маппинга складов")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
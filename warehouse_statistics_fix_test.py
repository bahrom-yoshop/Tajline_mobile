#!/usr/bin/env python3
"""
🔧 ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ: API статистики склада
Проверка исправления проблемы с отображением занятых ячеек в карточке склада
"""

import requests
import json
import sys
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://tajline-manage-1.preview.emergentagent.com/api"
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"
TARGET_WAREHOUSE_NAME = "Москва Склад №1"

class WarehouseStatisticsTest:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.warehouse_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", expected="", actual=""):
        """Логирование результатов тестов"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "expected": expected,
            "actual": actual,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   📝 {details}")
        if not success and expected and actual:
            print(f"   🎯 Expected: {expected}")
            print(f"   📊 Actual: {actual}")
        print()

    def authenticate_warehouse_operator(self):
        """1. Авторизация оператора склада"""
        print("🔐 STEP 1: Авторизация оператора склада")
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "phone": WAREHOUSE_OPERATOR_PHONE,
                "password": WAREHOUSE_OPERATOR_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                user_info = data.get("user", {})
                
                self.session.headers.update({
                    "Authorization": f"Bearer {self.token}"
                })
                
                self.log_test(
                    "Авторизация оператора склада",
                    True,
                    f"Успешная авторизация '{user_info.get('full_name')}' (роль: {user_info.get('role')})"
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

    def get_warehouse_id(self):
        """2. Получение warehouse_id для "Москва Склад №1" """
        print("🏢 STEP 2: Получение warehouse_id для 'Москва Склад №1'")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/warehouses")
            
            if response.status_code == 200:
                warehouses = response.json()
                
                for warehouse in warehouses:
                    if warehouse.get("name") == TARGET_WAREHOUSE_NAME:
                        self.warehouse_id = warehouse.get("id")
                        self.log_test(
                            "Получение warehouse_id",
                            True,
                            f"Найден склад '{TARGET_WAREHOUSE_NAME}' (ID: {self.warehouse_id})"
                        )
                        return True
                
                self.log_test(
                    "Получение warehouse_id",
                    False,
                    f"Склад '{TARGET_WAREHOUSE_NAME}' не найден среди {len(warehouses)} складов"
                )
                return False
            else:
                self.log_test(
                    "Получение warehouse_id",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Получение warehouse_id",
                False,
                f"Ошибка запроса: {str(e)}"
            )
            return False

    def test_warehouse_statistics_api(self):
        """3. Тестирование исправленного API статистики склада"""
        print("📊 STEP 3: Тестирование исправленного API статистики")
        
        if not self.warehouse_id:
            self.log_test(
                "API статистики склада",
                False,
                "warehouse_id не найден"
            )
            return False
            
        try:
            response = self.session.get(f"{BACKEND_URL}/warehouses/{self.warehouse_id}/statistics")
            
            if response.status_code == 200:
                stats = response.json()
                print(f"📋 Полученная статистика: {json.dumps(stats, indent=2, ensure_ascii=False)}")
                
                # КРИТИЧЕСКИЕ ПРОВЕРКИ
                success = True
                details = []
                
                # 1. occupied_cells должно быть 2 (не 10!)
                occupied_cells = stats.get("occupied_cells", 0)
                if occupied_cells == 2:
                    details.append(f"✅ occupied_cells = {occupied_cells} (исправлено с 10)")
                else:
                    details.append(f"❌ occupied_cells = {occupied_cells} (ожидалось 2)")
                    success = False
                
                # 2. total_placed_cargo должно быть 3
                total_placed_cargo = stats.get("total_placed_cargo", 0)
                if total_placed_cargo == 3:
                    details.append(f"✅ total_placed_cargo = {total_placed_cargo}")
                else:
                    details.append(f"❌ total_placed_cargo = {total_placed_cargo} (ожидалось 3)")
                    success = False
                
                # 3. placement_statistics проверки
                placement_stats = stats.get("placement_statistics", {})
                unique_occupied_cells = placement_stats.get("unique_occupied_cells", 0)
                placement_records_count = placement_stats.get("placement_records_count", 0)
                
                if unique_occupied_cells == 2:
                    details.append(f"✅ placement_statistics.unique_occupied_cells = {unique_occupied_cells}")
                else:
                    details.append(f"❌ placement_statistics.unique_occupied_cells = {unique_occupied_cells} (ожидалось 2)")
                    success = False
                
                if placement_records_count == 3:
                    details.append(f"✅ placement_statistics.placement_records_count = {placement_records_count}")
                else:
                    details.append(f"❌ placement_statistics.placement_records_count = {placement_records_count} (ожидалось 3)")
                    success = False
                
                # 4. data_source должен быть "placement_records"
                data_source = stats.get("data_source", "")
                if data_source == "placement_records":
                    details.append(f"✅ data_source = '{data_source}'")
                else:
                    details.append(f"❌ data_source = '{data_source}' (ожидалось 'placement_records')")
                    success = False
                
                self.log_test(
                    "API статистики склада - критические проверки",
                    success,
                    "; ".join(details)
                )
                
                return success
            else:
                self.log_test(
                    "API статистики склада",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "API статистики склада",
                False,
                f"Ошибка запроса: {str(e)}"
            )
            return False

    def check_diagnostic_logging(self):
        """4. Проверка логирования диагностики (через повторный запрос)"""
        print("🔍 STEP 4: Проверка диагностического логирования")
        
        if not self.warehouse_id:
            self.log_test(
                "Диагностическое логирование",
                False,
                "warehouse_id не найден"
            )
            return False
            
        try:
            # Делаем повторный запрос для активации логирования
            response = self.session.get(f"{BACKEND_URL}/warehouses/{self.warehouse_id}/statistics")
            
            if response.status_code == 200:
                stats = response.json()
                
                # Проверяем наличие диагностической информации
                diagnostic_info = []
                
                if "placement_statistics" in stats:
                    placement_stats = stats["placement_statistics"]
                    diagnostic_info.append(f"📦 placement_records найдено: {placement_stats.get('placement_records_count', 0)}")
                    diagnostic_info.append(f"📍 Уникальных занятых ячеек: {placement_stats.get('unique_occupied_cells', 0)}")
                    diagnostic_info.append(f"🏷️ Размещенных грузов: {stats.get('total_placed_cargo', 0)}")
                
                if diagnostic_info:
                    self.log_test(
                        "Диагностическое логирование",
                        True,
                        f"Диагностическая информация получена: {'; '.join(diagnostic_info)}"
                    )
                    return True
                else:
                    self.log_test(
                        "Диагностическое логирование",
                        False,
                        "Диагностическая информация не найдена в ответе API"
                    )
                    return False
            else:
                self.log_test(
                    "Диагностическое логирование",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Диагностическое логирование",
                False,
                f"Ошибка запроса: {str(e)}"
            )
            return False

    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 НАЧАЛО ТЕСТИРОВАНИЯ ИСПРАВЛЕНИЯ API СТАТИСТИКИ СКЛАДА")
        print("=" * 80)
        
        # Выполняем тесты по порядку
        tests_passed = 0
        total_tests = 4
        
        if self.authenticate_warehouse_operator():
            tests_passed += 1
            
            if self.get_warehouse_id():
                tests_passed += 1
                
                if self.test_warehouse_statistics_api():
                    tests_passed += 1
                    
                if self.check_diagnostic_logging():
                    tests_passed += 1
        
        # Итоговый отчет
        print("=" * 80)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 80)
        
        success_rate = (tests_passed / total_tests) * 100
        
        print(f"✅ Пройдено тестов: {tests_passed}/{total_tests}")
        print(f"📈 Процент успеха: {success_rate:.1f}%")
        
        if tests_passed == total_tests:
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            print("✅ ИСПРАВЛЕНИЕ API СТАТИСТИКИ СКЛАДА РАБОТАЕТ КОРРЕКТНО")
            print("✅ occupied_cells = 2 (исправлено с 10)")
            print("✅ Использование placement_records как источника данных")
            print("✅ Правильная статистика для карточки склада")
        else:
            print("❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
            print("🔧 ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНОЕ ИСПРАВЛЕНИЕ")
        
        print("\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        for result in self.test_results:
            print(f"{result['status']}: {result['test']}")
            if result['details']:
                print(f"   📝 {result['details']}")
        
        return tests_passed == total_tests

if __name__ == "__main__":
    tester = WarehouseStatisticsTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
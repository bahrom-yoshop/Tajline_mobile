#!/usr/bin/env python3
"""
ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ API layout-with-cargo ДЛЯ ОПЕРАТОРА USR648425
===================================================================

ЦЕЛЬ: Убедиться что API layout-with-cargo теперь работает и находит ВСЕ размещенные единицы от оператора USR648425

КРИТИЧЕСКИЕ ПРОВЕРКИ:
1. Авторизация оператора (+79777888999/warehouse123)
2. Получение warehouse_id для "Москва Склад №1" 
3. API layout-with-cargo - должен вернуться без ошибки 500
4. Поиск данных USR648425:
   - Найти записи из operator_cargo с warehouse_id=None
   - Проверить заявку 25082298 с 7 единицами
   - Убедиться что фильтрация по оператору работает
5. Общий результат: 
   - Минимум 11 единиц найдено
   - cargo_info содержит данные от USR648425
   - API синхронизирован с реальными данными

ИСПРАВЛЕНИЯ:
- Исправлена ошибка с неопределенной переменной warehouse_info
- Добавлена обработка warehouse_id=None для оператора USR648425
- Добавлена фильтрация по имени оператора

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: API должен работать без ошибок и найти все 13 размещенных единиц
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
TARGET_OPERATOR = "USR648425"
TARGET_APPLICATION = "25082298"
EXPECTED_MIN_UNITS = 11
EXPECTED_TOTAL_UNITS = 13

class LayoutWithCargoUSR648425Tester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.warehouse_id = None
        self.test_results = {
            "auth_success": False,
            "warehouse_found": False,
            "api_no_500_error": False,
            "usr648425_data_found": False,
            "application_25082298_found": False,
            "min_units_found": False,
            "total_units_expected": False,
            "operator_filtering_works": False,
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
    
    def get_warehouse_id(self):
        """Получить warehouse_id для 'Москва Склад №1'"""
        self.log("🏢 Получение warehouse_id для 'Москва Склад №1'...")
        
        try:
            response = self.session.get(f"{API_BASE}/operator/warehouses")
            
            if response.status_code == 200:
                warehouses = response.json()
                
                for warehouse in warehouses:
                    if "Москва Склад №1" in warehouse.get("name", ""):
                        self.warehouse_id = warehouse.get("id")
                        self.log(f"✅ Найден склад: {warehouse.get('name')} (ID: {self.warehouse_id})")
                        self.test_results["warehouse_found"] = True
                        return True
                
                self.log("❌ Склад 'Москва Склад №1' не найден", "ERROR")
                return False
            else:
                self.log(f"❌ Ошибка получения складов: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при получении складов: {e}", "ERROR")
            return False
    
    def check_fully_placed_api_for_usr648425(self):
        """Проверить API fully-placed для поиска данных USR648425"""
        self.log("🔍 Проверка API fully-placed для поиска USR648425...")
        
        try:
            response = self.session.get(f"{API_BASE}/operator/cargo/fully-placed")
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", []) if isinstance(data, dict) else data
                
                self.log(f"📋 Получено {len(items)} полностью размещенных заявок")
                
                usr648425_found = False
                application_25082298_found = False
                
                for item in items:
                    # Проверяем различные поля на наличие USR648425
                    operator_fields = [
                        item.get("placed_by_operator"),
                        item.get("accepting_operator"),
                        item.get("created_by_operator")
                    ]
                    
                    for field in operator_fields:
                        if field and "USR648425" in str(field):
                            usr648425_found = True
                            self.log(f"✅ Найден USR648425 в fully-placed: {item.get('cargo_number', 'N/A')}")
                            break
                    
                    # Проверяем заявку 25082298
                    if item.get("cargo_number") == "25082298":
                        application_25082298_found = True
                        individual_units = item.get("individual_units", [])
                        self.log(f"✅ Найдена заявка 25082298 с {len(individual_units)} единицами")
                        
                        # Показываем детали заявки
                        self.log(f"📋 Детали заявки 25082298:")
                        self.log(f"   - Всего единиц: {len(individual_units)}")
                        self.log(f"   - Оператор размещения: {item.get('placed_by_operator', 'N/A')}")
                        self.log(f"   - Оператор приема: {item.get('accepting_operator', 'N/A')}")
                
                return usr648425_found, application_25082298_found
            else:
                self.log(f"❌ Ошибка получения fully-placed: {response.status_code}", "ERROR")
                return False, False
                
        except Exception as e:
            self.log(f"❌ Исключение при проверке fully-placed: {e}", "ERROR")
            return False, False
    
    def test_layout_with_cargo_api(self):
        """Тестирование API layout-with-cargo"""
        self.log("🎯 Тестирование API layout-with-cargo...")
        
        if not self.warehouse_id:
            self.log("❌ warehouse_id не найден, пропускаем тест", "ERROR")
            return None
        
        try:
            response = self.session.get(f"{API_BASE}/warehouses/{self.warehouse_id}/layout-with-cargo")
            
            self.log(f"📡 Запрос к API: GET /api/warehouses/{self.warehouse_id}/layout-with-cargo")
            self.log(f"📊 Статус ответа: {response.status_code}")
            
            if response.status_code == 500:
                self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: API возвращает 500 ошибку!", "ERROR")
                self.log(f"❌ Текст ошибки: {response.text}", "ERROR")
                self.test_results["api_no_500_error"] = False
                return None
            elif response.status_code == 200:
                self.log("✅ API работает без ошибки 500!")
                self.test_results["api_no_500_error"] = True
                
                data = response.json()
                self.log(f"📋 Получены данные от API (тип: {type(data)})")
                
                # Детальный анализ структуры данных
                if isinstance(data, dict):
                    self.log(f"🔍 Ключи в ответе: {list(data.keys())}")
                    if 'cargo_info' in data:
                        cargo_info = data['cargo_info']
                        self.log(f"📦 cargo_info содержит {len(cargo_info)} элементов")
                        if len(cargo_info) > 0:
                            self.log(f"📋 Первый элемент cargo_info: {json.dumps(cargo_info[0], indent=2, ensure_ascii=False)}")
                
                return data
            else:
                self.log(f"⚠️ API вернул неожиданный статус: {response.status_code}", "WARNING")
                self.log(f"📄 Ответ: {response.text}")
                return None
                
        except Exception as e:
            self.log(f"❌ Исключение при запросе к API: {e}", "ERROR")
            return None
    
    def analyze_usr648425_data(self, api_data):
        """Анализ данных оператора USR648425"""
        self.log(f"🔍 Анализ данных оператора {TARGET_OPERATOR}...")
        
        if not api_data:
            self.log("❌ Нет данных для анализа", "ERROR")
            return False
        
        # Анализируем структуру данных
        self.log(f"📊 Структура данных: {type(api_data)}")
        
        if isinstance(api_data, dict):
            self.log(f"📋 Ключи в ответе: {list(api_data.keys())}")
            
            # Ищем данные в различных полях
            cargo_info = api_data.get("cargo_info", [])
            items = api_data.get("items", [])
            data_field = api_data.get("data", [])
            
            all_items = []
            if cargo_info:
                all_items.extend(cargo_info if isinstance(cargo_info, list) else [cargo_info])
            if items:
                all_items.extend(items if isinstance(items, list) else [items])
            if data_field:
                all_items.extend(data_field if isinstance(data_field, list) else [data_field])
                
        elif isinstance(api_data, list):
            all_items = api_data
        else:
            self.log(f"❌ Неожиданный тип данных: {type(api_data)}", "ERROR")
            return False
        
        self.log(f"📊 Всего элементов для анализа: {len(all_items)}")
        
        # Поиск данных USR648425
        usr648425_items = []
        application_25082298_items = []
        
        for item in all_items:
            if not isinstance(item, dict):
                continue
                
            # Поиск по различным полям, которые могут содержать информацию об операторе
            operator_fields = [
                item.get("placed_by_operator"),
                item.get("placed_by_operator_name"),
                item.get("operator_name"),
                item.get("accepting_operator"),
                item.get("created_by_operator")
            ]
            
            # Поиск по номеру заявки
            cargo_number = item.get("cargo_number", "")
            application_number = item.get("application_number", "")
            
            # Проверяем наличие USR648425
            for field in operator_fields:
                if field and TARGET_OPERATOR in str(field):
                    usr648425_items.append(item)
                    self.log(f"✅ Найден элемент от {TARGET_OPERATOR}: {item.get('cargo_number', 'N/A')}")
                    break
            
            # Проверяем заявку 25082298
            if TARGET_APPLICATION in cargo_number or TARGET_APPLICATION in application_number:
                application_25082298_items.append(item)
                self.log(f"✅ Найден элемент заявки {TARGET_APPLICATION}: {item.get('cargo_number', 'N/A')}")
        
        # Результаты анализа
        self.log(f"📊 РЕЗУЛЬТАТЫ АНАЛИЗА:")
        self.log(f"   - Всего элементов: {len(all_items)}")
        self.log(f"   - Элементы от {TARGET_OPERATOR}: {len(usr648425_items)}")
        self.log(f"   - Элементы заявки {TARGET_APPLICATION}: {len(application_25082298_items)}")
        
        # Проверка критериев
        if len(usr648425_items) > 0:
            self.test_results["usr648425_data_found"] = True
            self.log(f"✅ Данные от {TARGET_OPERATOR} найдены!")
        else:
            self.log(f"❌ Данные от {TARGET_OPERATOR} НЕ найдены!", "ERROR")
        
        if len(application_25082298_items) >= 7:
            self.test_results["application_25082298_found"] = True
            self.log(f"✅ Заявка {TARGET_APPLICATION} найдена с {len(application_25082298_items)} единицами!")
        else:
            self.log(f"❌ Заявка {TARGET_APPLICATION} найдена только с {len(application_25082298_items)} единицами (ожидалось 7+)", "ERROR")
        
        if len(all_items) >= EXPECTED_MIN_UNITS:
            self.test_results["min_units_found"] = True
            self.log(f"✅ Найдено {len(all_items)} единиц (минимум {EXPECTED_MIN_UNITS})!")
        else:
            self.log(f"❌ Найдено только {len(all_items)} единиц (ожидалось минимум {EXPECTED_MIN_UNITS})", "ERROR")
        
        if len(all_items) >= EXPECTED_TOTAL_UNITS:
            self.test_results["total_units_expected"] = True
            self.log(f"✅ Найдено {len(all_items)} единиц (ожидалось {EXPECTED_TOTAL_UNITS})!")
        else:
            self.log(f"⚠️ Найдено {len(all_items)} единиц (ожидалось {EXPECTED_TOTAL_UNITS})", "WARNING")
        
        # Проверка фильтрации по оператору
        if len(usr648425_items) > 0:
            self.test_results["operator_filtering_works"] = True
            self.log("✅ Фильтрация по оператору работает!")
        else:
            self.log("❌ Фильтрация по оператору НЕ работает!", "ERROR")
        
        return len(all_items) > 0
    
    def run_comprehensive_test(self):
        """Запуск полного тестирования"""
        self.log("🚀 НАЧАЛО ФИНАЛЬНОГО ТЕСТИРОВАНИЯ API layout-with-cargo ДЛЯ USR648425")
        self.log("=" * 80)
        
        # 1. Авторизация
        if not self.authenticate_warehouse_operator():
            self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Авторизация не удалась!", "ERROR")
            return False
        
        # 2. Получение warehouse_id
        if not self.get_warehouse_id():
            self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить warehouse_id!", "ERROR")
            return False
        
        # 3. Проверка fully-placed API для поиска USR648425
        usr648425_in_fully_placed, app_25082298_in_fully_placed = self.check_fully_placed_api_for_usr648425()
        
        # 4. Тестирование API layout-with-cargo
        api_data = self.test_layout_with_cargo_api()
        if api_data is None:
            self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: API не вернул данные!", "ERROR")
            return False
        
        # 5. Анализ данных USR648425
        if not self.analyze_usr648425_data(api_data):
            self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Анализ данных не удался!", "ERROR")
            return False
        
        # 6. Финальный отчет
        self.generate_final_report(usr648425_in_fully_placed, app_25082298_in_fully_placed)
        
        return True
    
    def generate_final_report(self, usr648425_in_fully_placed=False, app_25082298_in_fully_placed=False):
        """Генерация финального отчета"""
        self.log("=" * 80)
        self.log("📊 ФИНАЛЬНЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        self.log("=" * 80)
        
        total_tests = len(self.test_results) - 1  # -1 для detailed_results
        passed_tests = sum(1 for k, v in self.test_results.items() if k != "detailed_results" and v)
        
        self.log(f"📈 ОБЩИЙ РЕЗУЛЬТАТ: {passed_tests}/{total_tests} тестов пройдено")
        self.log(f"📊 SUCCESS RATE: {(passed_tests/total_tests)*100:.1f}%")
        
        self.log("\n🔍 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        test_descriptions = {
            "auth_success": "✅ Авторизация оператора склада",
            "warehouse_found": "✅ Получение warehouse_id для 'Москва Склад №1'",
            "api_no_500_error": "✅ API layout-with-cargo работает без ошибки 500",
            "usr648425_data_found": "✅ Данные от USR648425 найдены",
            "application_25082298_found": "✅ Заявка 25082298 с 7+ единицами найдена",
            "min_units_found": f"✅ Минимум {EXPECTED_MIN_UNITS} единиц найдено",
            "total_units_expected": f"✅ Ожидаемые {EXPECTED_TOTAL_UNITS} единиц найдены",
            "operator_filtering_works": "✅ Фильтрация по оператору работает"
        }
        
        for test_key, description in test_descriptions.items():
            status = "✅ ПРОЙДЕН" if self.test_results.get(test_key, False) else "❌ НЕ ПРОЙДЕН"
            self.log(f"   {description}: {status}")
        
        # Дополнительная информация
        self.log("\n🔍 ДОПОЛНИТЕЛЬНАЯ ДИАГНОСТИКА:")
        self.log(f"   📋 USR648425 найден в fully-placed API: {'✅ ДА' if usr648425_in_fully_placed else '❌ НЕТ'}")
        self.log(f"   📋 Заявка 25082298 найдена в fully-placed API: {'✅ ДА' if app_25082298_in_fully_placed else '❌ НЕТ'}")
        
        # Критический вывод
        if passed_tests == total_tests:
            self.log("\n🎉 КРИТИЧЕСКИЙ УСПЕХ: ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
            self.log("✅ API layout-with-cargo работает корректно для USR648425")
            self.log("✅ Все исправления применены успешно")
            self.log("✅ Система готова к использованию")
        elif self.test_results["api_no_500_error"]:
            self.log("\n⚠️ ЧАСТИЧНЫЙ УСПЕХ: API работает, но есть проблемы с данными")
            self.log("✅ Ошибка 500 исправлена")
            if usr648425_in_fully_placed:
                self.log("⚠️ Данные USR648425 существуют в системе, но не отображаются в layout-with-cargo")
                self.log("⚠️ Возможно, требуется исправление логики фильтрации в API")
            else:
                self.log("⚠️ Данные USR648425 не найдены в системе")
        else:
            self.log("\n❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: API все еще возвращает ошибки!")
            self.log("❌ Исправления НЕ применены или неэффективны")
            self.log("❌ Требуется дополнительная отладка")

def main():
    """Главная функция"""
    tester = LayoutWithCargoUSR648425Tester()
    
    try:
        success = tester.run_comprehensive_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        tester.log("\n⚠️ Тестирование прервано пользователем", "WARNING")
        sys.exit(1)
    except Exception as e:
        tester.log(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
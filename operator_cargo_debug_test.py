#!/usr/bin/env python3
"""
КРИТИЧЕСКАЯ ОТЛАДКА: Прямая проверка коллекции operator_cargo для оператора USR648425
===================================================================================

ЦЕЛЬ: Понять почему исправленный API НЕ находит данные в operator_cargo с оператором USR648425

КРИТИЧЕСКИЕ ПРОВЕРКИ:
1. Авторизация оператора (+79777888999/warehouse123)
2. Проверка GET /api/debug/operator-cargo или прямой доступ к данным
3. Поиск оператора USR648425:
   - Найти ВСЕ записи operator_cargo с operator_name или placed_by содержащим "USR648425" или "Юлдашев"
   - Проверить структуру данных: cargo_items.individual_items.is_placed
   - Проверить warehouse_id в найденных записях
4. Диагностика проблемы:
   - Почему API layout-with-cargo не находит эти данные
   - Правильно ли работает фильтр по warehouse_id
   - Корректно ли парсится коллекция operator_cargo

ВАЖНО: Пользователь показал скриншот где заявка 25082298 имеет 7 размещенных единиц 
оператором "Юлдашев Жасурбек Бахтиёрович". Эти данные должны быть в operator_cargo.

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Найти точную причину почему operator_cargo данные не обрабатываются API
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
TARGET_OPERATOR_NAME = "Юлдашев"

class OperatorCargoDebugTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.test_results = {
            "auth_success": False,
            "debug_api_accessible": False,
            "operator_cargo_found": False,
            "target_application_found": False,
            "individual_items_structure": False,
            "warehouse_id_check": False,
            "api_layout_diagnosis": False
        }
        self.found_records = []
        self.diagnosis_results = {}

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def authenticate_operator(self):
        """Авторизация оператора склада"""
        try:
            self.log("🔐 Авторизация оператора склада...")
            
            auth_data = {
                "phone": WAREHOUSE_OPERATOR_PHONE,
                "password": WAREHOUSE_OPERATOR_PASSWORD
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=auth_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                
                # Получаем информацию о пользователе
                user_response = self.session.get(f"{API_BASE}/auth/me")
                if user_response.status_code == 200:
                    self.operator_info = user_response.json()
                    self.log(f"✅ Успешная авторизация: {self.operator_info.get('full_name')} (роль: {self.operator_info.get('role')})")
                    self.test_results["auth_success"] = True
                    return True
                else:
                    self.log(f"❌ Ошибка получения информации о пользователе: {user_response.status_code}")
                    return False
            else:
                self.log(f"❌ Ошибка авторизации: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при авторизации: {e}", "ERROR")
            return False

    def check_debug_api(self):
        """Проверка доступности debug API для operator_cargo"""
        try:
            self.log("🔍 Проверка debug API для operator_cargo...")
            
            # Пробуем различные debug endpoints
            debug_endpoints = [
                "/debug/operator-cargo",
                "/operator/debug/operator-cargo", 
                "/admin/debug/operator-cargo",
                "/debug/collections/operator_cargo"
            ]
            
            for endpoint in debug_endpoints:
                try:
                    response = self.session.get(f"{API_BASE}{endpoint}")
                    self.log(f"🔍 Проверка {endpoint}: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        self.log(f"✅ Debug API доступен: {endpoint}")
                        self.log(f"📊 Найдено записей: {len(data) if isinstance(data, list) else 'неизвестно'}")
                        self.test_results["debug_api_accessible"] = True
                        return data
                    elif response.status_code == 404:
                        continue
                    else:
                        self.log(f"⚠️ {endpoint} вернул: {response.status_code}")
                        
                except Exception as e:
                    self.log(f"⚠️ Ошибка при проверке {endpoint}: {e}")
                    continue
            
            self.log("❌ Ни один debug API не доступен")
            return None
            
        except Exception as e:
            self.log(f"❌ Исключение при проверке debug API: {e}", "ERROR")
            return None

    def search_operator_cargo_direct(self):
        """Прямой поиск в operator_cargo через доступные API"""
        try:
            self.log(f"🔍 Поиск оператора {TARGET_OPERATOR} в operator_cargo...")
            
            # Пробуем различные API endpoints для поиска
            search_endpoints = [
                "/operator/cargo/all",
                "/operator/cargo/list", 
                "/admin/cargo/all",
                "/cargo/search",
                "/operator/cargo/individual-units-for-placement"
            ]
            
            for endpoint in search_endpoints:
                try:
                    # Пробуем с различными параметрами
                    params_list = [
                        {},
                        {"page": 1, "per_page": 100},
                        {"search": TARGET_OPERATOR},
                        {"search": TARGET_OPERATOR_NAME},
                        {"operator": TARGET_OPERATOR}
                    ]
                    
                    for params in params_list:
                        response = self.session.get(f"{API_BASE}{endpoint}", params=params)
                        
                        if response.status_code == 200:
                            data = response.json()
                            self.log(f"✅ Успешный запрос к {endpoint} с параметрами {params}")
                            
                            # Анализируем структуру ответа
                            if isinstance(data, dict):
                                if "items" in data:
                                    items = data["items"]
                                    self.log(f"📊 Найдено записей: {len(items)}")
                                    self.analyze_cargo_records(items, endpoint)
                                elif "cargo" in data:
                                    items = data["cargo"]
                                    self.log(f"📊 Найдено записей: {len(items)}")
                                    self.analyze_cargo_records(items, endpoint)
                                else:
                                    self.log(f"📊 Структура ответа: {list(data.keys())}")
                            elif isinstance(data, list):
                                self.log(f"📊 Найдено записей: {len(data)}")
                                self.analyze_cargo_records(data, endpoint)
                            
                            break  # Если нашли рабочий endpoint, переходим к следующему
                        elif response.status_code == 404:
                            continue
                        else:
                            self.log(f"⚠️ {endpoint} вернул: {response.status_code}")
                            
                except Exception as e:
                    self.log(f"⚠️ Ошибка при запросе {endpoint}: {e}")
                    continue
                    
        except Exception as e:
            self.log(f"❌ Исключение при поиске operator_cargo: {e}", "ERROR")

    def analyze_cargo_records(self, records, source_endpoint):
        """Анализ найденных записей на предмет оператора USR648425"""
        try:
            self.log(f"🔍 Анализ {len(records)} записей из {source_endpoint}...")
            
            target_records = []
            
            for record in records:
                # Поиск по различным полям
                found_operator = False
                found_fields = []
                
                # Проверяем различные поля на наличие целевого оператора
                fields_to_check = [
                    "operator_name", "placed_by", "created_by_operator", 
                    "accepting_operator", "placing_operator", "operator_id",
                    "created_by", "updated_by"
                ]
                
                for field in fields_to_check:
                    if field in record:
                        value = str(record[field]).lower()
                        if TARGET_OPERATOR.lower() in value or TARGET_OPERATOR_NAME.lower() in value:
                            found_operator = True
                            found_fields.append(f"{field}: {record[field]}")
                
                # Также проверяем вложенные структуры
                if "cargo_items" in record:
                    for cargo_item in record["cargo_items"]:
                        if "individual_items" in cargo_item:
                            for individual_item in cargo_item["individual_items"]:
                                for field in ["placed_by", "operator_name", "operator_id"]:
                                    if field in individual_item:
                                        value = str(individual_item[field]).lower()
                                        if TARGET_OPERATOR.lower() in value or TARGET_OPERATOR_NAME.lower() in value:
                                            found_operator = True
                                            found_fields.append(f"cargo_items.individual_items.{field}: {individual_item[field]}")
                
                if found_operator:
                    target_records.append({
                        "record": record,
                        "found_fields": found_fields,
                        "source": source_endpoint
                    })
                    
                    # Проверяем заявку 25082298
                    cargo_number = record.get("cargo_number", "")
                    if TARGET_APPLICATION in cargo_number:
                        self.log(f"🎯 НАЙДЕНА ЦЕЛЕВАЯ ЗАЯВКА {TARGET_APPLICATION}!")
                        self.test_results["target_application_found"] = True
            
            if target_records:
                self.log(f"✅ Найдено {len(target_records)} записей с оператором {TARGET_OPERATOR}")
                self.found_records.extend(target_records)
                self.test_results["operator_cargo_found"] = True
                
                # Детальный анализ найденных записей
                self.analyze_found_records(target_records)
            else:
                self.log(f"❌ Записи с оператором {TARGET_OPERATOR} не найдены в {source_endpoint}")
                
        except Exception as e:
            self.log(f"❌ Исключение при анализе записей: {e}", "ERROR")

    def analyze_found_records(self, records):
        """Детальный анализ найденных записей"""
        try:
            self.log("🔍 ДЕТАЛЬНЫЙ АНАЛИЗ НАЙДЕННЫХ ЗАПИСЕЙ:")
            
            for i, record_data in enumerate(records, 1):
                record = record_data["record"]
                found_fields = record_data["found_fields"]
                source = record_data["source"]
                
                self.log(f"\n📋 ЗАПИСЬ #{i} (источник: {source}):")
                self.log(f"   Номер заявки: {record.get('cargo_number', 'неизвестно')}")
                self.log(f"   Найденные поля: {', '.join(found_fields)}")
                self.log(f"   warehouse_id: {record.get('warehouse_id', 'не указан')}")
                
                # Анализ структуры cargo_items
                if "cargo_items" in record:
                    self.log(f"   📦 Количество cargo_items: {len(record['cargo_items'])}")
                    
                    total_individual_items = 0
                    placed_individual_items = 0
                    
                    for j, cargo_item in enumerate(record["cargo_items"], 1):
                        self.log(f"      Cargo Item #{j}: {cargo_item.get('cargo_name', 'без названия')}")
                        
                        if "individual_items" in cargo_item:
                            individual_items = cargo_item["individual_items"]
                            total_individual_items += len(individual_items)
                            
                            placed_count = sum(1 for item in individual_items if item.get("is_placed", False))
                            placed_individual_items += placed_count
                            
                            self.log(f"         Individual items: {len(individual_items)} (размещено: {placed_count})")
                            
                            # Проверяем структуру individual_items
                            if individual_items:
                                sample_item = individual_items[0]
                                self.log(f"         Структура individual_item: {list(sample_item.keys())}")
                                
                                if "is_placed" in sample_item:
                                    self.test_results["individual_items_structure"] = True
                        else:
                            self.log(f"         ❌ individual_items отсутствует!")
                    
                    self.log(f"   📊 ИТОГО: {total_individual_items} единиц, размещено: {placed_individual_items}")
                    
                    # Проверяем warehouse_id
                    warehouse_id = record.get("warehouse_id")
                    if warehouse_id:
                        self.log(f"   🏢 warehouse_id: {warehouse_id}")
                        self.test_results["warehouse_id_check"] = True
                    else:
                        self.log(f"   ❌ warehouse_id отсутствует!")
                else:
                    self.log(f"   ❌ cargo_items отсутствует!")
                    
        except Exception as e:
            self.log(f"❌ Исключение при детальном анализе: {e}", "ERROR")

    def diagnose_layout_with_cargo_api(self):
        """Диагностика API layout-with-cargo"""
        try:
            self.log("🔍 ДИАГНОСТИКА API layout-with-cargo...")
            
            # Получаем информацию о складе оператора
            warehouses_response = self.session.get(f"{API_BASE}/operator/warehouses")
            if warehouses_response.status_code != 200:
                self.log(f"❌ Не удалось получить склады оператора: {warehouses_response.status_code}")
                return
            
            warehouses = warehouses_response.json()
            if not warehouses:
                self.log("❌ У оператора нет привязанных складов")
                return
            
            warehouse = warehouses[0]
            warehouse_id = warehouse["id"]
            self.log(f"🏢 Тестируем склад: {warehouse['name']} (ID: {warehouse_id})")
            
            # Тестируем API layout-with-cargo
            layout_response = self.session.get(f"{API_BASE}/warehouses/{warehouse_id}/layout-with-cargo")
            
            if layout_response.status_code == 200:
                layout_data = layout_response.json()
                self.log(f"✅ API layout-with-cargo доступен")
                
                # Анализируем cargo_info
                if "cargo_info" in layout_data:
                    cargo_info = layout_data["cargo_info"]
                    self.log(f"📊 Найдено единиц в cargo_info: {len(cargo_info)}")
                    
                    # Ищем данные оператора USR648425
                    usr648425_units = []
                    for unit in cargo_info:
                        placed_by = unit.get("placed_by", "")
                        if TARGET_OPERATOR in placed_by or TARGET_OPERATOR_NAME.lower() in placed_by.lower():
                            usr648425_units.append(unit)
                    
                    if usr648425_units:
                        self.log(f"✅ Найдено {len(usr648425_units)} единиц от оператора {TARGET_OPERATOR}")
                        self.test_results["api_layout_diagnosis"] = True
                        
                        # Анализируем найденные единицы
                        for unit in usr648425_units[:3]:  # Показываем первые 3
                            self.log(f"   📦 {unit.get('cargo_number', 'неизвестно')}: {unit.get('cargo_name', 'без названия')}")
                            self.log(f"      Размещен: {unit.get('placed_by', 'неизвестно')}")
                            self.log(f"      Ячейка: {unit.get('cell_location', 'неизвестно')}")
                    else:
                        self.log(f"❌ Данные оператора {TARGET_OPERATOR} НЕ найдены в cargo_info")
                        self.log("🔍 Возможные причины:")
                        self.log("   1. Данные находятся только в operator_cargo, но не обрабатываются API")
                        self.log("   2. warehouse_id в operator_cargo не соответствует складу оператора")
                        self.log("   3. Структура individual_items не соответствует ожидаемой")
                        self.log("   4. Фильтр по is_placed не работает корректно")
                        
                        # Дополнительная диагностика
                        self.additional_diagnosis(warehouse_id)
                else:
                    self.log("❌ cargo_info отсутствует в ответе API")
            else:
                self.log(f"❌ API layout-with-cargo недоступен: {layout_response.status_code}")
                
        except Exception as e:
            self.log(f"❌ Исключение при диагностике API: {e}", "ERROR")

    def additional_diagnosis(self, warehouse_id):
        """Дополнительная диагностика проблемы"""
        try:
            self.log("🔍 ДОПОЛНИТЕЛЬНАЯ ДИАГНОСТИКА:")
            
            # Проверяем, есть ли записи в operator_cargo с правильным warehouse_id
            if self.found_records:
                self.log(f"📋 Анализ warehouse_id в найденных записях:")
                
                for record_data in self.found_records:
                    record = record_data["record"]
                    record_warehouse_id = record.get("warehouse_id")
                    cargo_number = record.get("cargo_number", "неизвестно")
                    
                    self.log(f"   Заявка {cargo_number}: warehouse_id = {record_warehouse_id}")
                    
                    if record_warehouse_id == warehouse_id:
                        self.log(f"   ✅ warehouse_id совпадает с текущим складом")
                    elif record_warehouse_id is None:
                        self.log(f"   ❌ warehouse_id отсутствует (None)")
                    else:
                        self.log(f"   ❌ warehouse_id не совпадает (ожидается: {warehouse_id})")
            
            # Проверяем placement_records
            self.log("🔍 Проверка placement_records...")
            try:
                # Пробуем найти placement_records через различные API
                placement_endpoints = [
                    f"/warehouses/{warehouse_id}/placement-records",
                    f"/operator/placement-records",
                    f"/debug/placement-records"
                ]
                
                for endpoint in placement_endpoints:
                    try:
                        response = self.session.get(f"{API_BASE}{endpoint}")
                        if response.status_code == 200:
                            data = response.json()
                            self.log(f"✅ Найдены placement_records через {endpoint}")
                            
                            if isinstance(data, list):
                                usr_records = [r for r in data if TARGET_OPERATOR in str(r.get("placed_by", ""))]
                                self.log(f"📊 Записи от {TARGET_OPERATOR}: {len(usr_records)}")
                            break
                    except:
                        continue
            except:
                self.log("⚠️ Не удалось проверить placement_records")
                
        except Exception as e:
            self.log(f"❌ Исключение при дополнительной диагностике: {e}", "ERROR")

    def run_comprehensive_test(self):
        """Запуск полного теста"""
        self.log("🚀 НАЧАЛО КРИТИЧЕСКОЙ ОТЛАДКИ operator_cargo для USR648425")
        self.log("=" * 80)
        
        # 1. Авторизация
        if not self.authenticate_operator():
            self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться")
            return False
        
        # 2. Проверка debug API
        debug_data = self.check_debug_api()
        
        # 3. Поиск operator_cargo
        self.search_operator_cargo_direct()
        
        # 4. Диагностика layout-with-cargo API
        self.diagnose_layout_with_cargo_api()
        
        # 5. Итоговый отчет
        self.generate_final_report()
        
        return True

    def generate_final_report(self):
        """Генерация итогового отчета"""
        self.log("\n" + "=" * 80)
        self.log("📊 ИТОГОВЫЙ ОТЧЕТ КРИТИЧЕСКОЙ ОТЛАДКИ")
        self.log("=" * 80)
        
        # Статистика тестов
        passed_tests = sum(1 for result in self.test_results.values() if result)
        total_tests = len(self.test_results)
        success_rate = (passed_tests / total_tests) * 100
        
        self.log(f"📈 SUCCESS RATE: {success_rate:.1f}% ({passed_tests}/{total_tests} тестов пройдены)")
        
        # Детальные результаты
        self.log("\n🔍 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        for test_name, result in self.test_results.items():
            status = "✅" if result else "❌"
            self.log(f"   {status} {test_name}: {'ПРОЙДЕН' if result else 'НЕ ПРОЙДЕН'}")
        
        # Найденные записи
        if self.found_records:
            self.log(f"\n📋 НАЙДЕНО ЗАПИСЕЙ С ОПЕРАТОРОМ {TARGET_OPERATOR}: {len(self.found_records)}")
            
            target_app_found = any(
                TARGET_APPLICATION in record_data["record"].get("cargo_number", "")
                for record_data in self.found_records
            )
            
            if target_app_found:
                self.log(f"🎯 ЦЕЛЕВАЯ ЗАЯВКА {TARGET_APPLICATION} НАЙДЕНА!")
            else:
                self.log(f"❌ ЦЕЛЕВАЯ ЗАЯВКА {TARGET_APPLICATION} НЕ НАЙДЕНА")
        else:
            self.log(f"\n❌ ЗАПИСИ С ОПЕРАТОРОМ {TARGET_OPERATOR} НЕ НАЙДЕНЫ")
        
        # Диагноз проблемы
        self.log("\n🔍 ДИАГНОЗ ПРОБЛЕМЫ:")
        
        if not self.test_results["operator_cargo_found"]:
            self.log("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Данные оператора USR648425 не найдены в operator_cargo")
            self.log("   Возможные причины:")
            self.log("   1. Данные не были сохранены в operator_cargo коллекцию")
            self.log("   2. Поля operator_name/placed_by содержат другие значения")
            self.log("   3. API не предоставляет доступ к operator_cargo данным")
        elif not self.test_results["target_application_found"]:
            self.log("❌ ПРОБЛЕМА: Заявка 25082298 не найдена среди записей оператора")
            self.log("   Возможные причины:")
            self.log("   1. Заявка имеет другой номер")
            self.log("   2. Заявка не привязана к оператору USR648425")
        elif not self.test_results["individual_items_structure"]:
            self.log("❌ ПРОБЛЕМА: Структура individual_items некорректна")
            self.log("   Возможные причины:")
            self.log("   1. individual_items не содержат поле is_placed")
            self.log("   2. Структура данных не соответствует ожидаемой")
        elif not self.test_results["warehouse_id_check"]:
            self.log("❌ ПРОБЛЕМА: warehouse_id отсутствует в записях")
            self.log("   Возможные причины:")
            self.log("   1. warehouse_id не был установлен при создании записи")
            self.log("   2. Записи созданы до внедрения warehouse_id")
        elif not self.test_results["api_layout_diagnosis"]:
            self.log("❌ ПРОБЛЕМА: API layout-with-cargo не обрабатывает данные operator_cargo")
            self.log("   Возможные причины:")
            self.log("   1. API ищет только в placement_records, игнорируя operator_cargo")
            self.log("   2. Фильтр по warehouse_id не работает с operator_cargo")
            self.log("   3. Логика объединения данных из двух источников не реализована")
        else:
            self.log("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ: Данные найдены и структура корректна")
        
        # Рекомендации
        self.log("\n💡 РЕКОМЕНДАЦИИ:")
        if not self.test_results["operator_cargo_found"]:
            self.log("1. Проверить наличие данных в MongoDB коллекции operator_cargo")
            self.log("2. Убедиться что поля operator_name/placed_by содержат 'USR648425' или 'Юлдашев'")
            self.log("3. Создать debug endpoint для прямого доступа к operator_cargo")
        else:
            self.log("1. Реализовать поиск в operator_cargo коллекции в API layout-with-cargo")
            self.log("2. Добавить логику объединения данных из placement_records и operator_cargo")
            self.log("3. Убедиться что warehouse_id корректно фильтрует записи")
            self.log("4. Создать синтетические placement_records из operator_cargo данных")
        
        self.log("\n" + "=" * 80)
        self.log("🏁 КРИТИЧЕСКАЯ ОТЛАДКА ЗАВЕРШЕНА")
        self.log("=" * 80)

def main():
    """Главная функция"""
    tester = OperatorCargoDebugTester()
    
    try:
        success = tester.run_comprehensive_test()
        
        if success:
            print("\n✅ Тест завершен успешно")
            return 0
        else:
            print("\n❌ Тест завершен с ошибками")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Тест прерван пользователем")
        return 1
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
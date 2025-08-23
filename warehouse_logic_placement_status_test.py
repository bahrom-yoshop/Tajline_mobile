#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: ИСПРАВЛЕННАЯ ЛОГИКА ОПРЕДЕЛЕНИЯ СКЛАДОВ В API placement-status
=======================================================================================

ЦЕЛЬ: Убедиться что склад выдачи груза теперь правильно определяется по городу доставки

КРИТИЧЕСКИЕ ПРОВЕРКИ:
1. Авторизация оператора склада (+79777888999/warehouse123)
2. Тестирование API placement-status для любой доступной заявки:
   - Проверить source_warehouse_name - должен быть склад приёма (Москва)
   - Проверить target_warehouse_name - должен соответствовать городу доставки
   - Проверить delivery_warehouse - должен быть складом в городе доставки, НЕ складом приёма
   - Проверить соответствие: если delivery_city = "Яван", то target_warehouse_name должен быть "Яван Склад №1"
3. Логика определения складов: Убедиться что разные города дают разные склады выдачи

ИСПРАВЛЕНИЯ:
- Добавлена функция get_warehouse_by_city() для умного определения складов
- Маппинг популярных таджикских городов на склады
- Fallback логика для неизвестных городов

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: 
- Склад приёма: "Москва Центральный" (корректно)
- Склад выдачи: соответствует городу доставки (например, "Яван Склад №1" для города Яван)
"""

import requests
import json
import sys
import os
from datetime import datetime

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cargo-sync.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Конфигурация
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"

class WarehouseLogicTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.test_results = {
            "auth_success": False,
            "api_accessible": False,
            "applications_found": False,
            "warehouse_logic_correct": False,
            "total_tests": 0,
            "passed_tests": 0,
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
                self.test_results["api_accessible"] = True
                self.test_results["applications_found"] = len(items) > 0
                return items
            else:
                self.log(f"❌ Ошибка получения заявок: {response.status_code} - {response.text}", "ERROR")
                return []
                
        except Exception as e:
            self.log(f"❌ Исключение при запросе: {e}", "ERROR")
            return []
    
    def test_placement_status_api(self, cargo_id, cargo_number):
        """Тестирование API placement-status для конкретной заявки"""
        self.log(f"🎯 Тестирование API placement-status для заявки {cargo_number}...")
        
        try:
            response = self.session.get(f"{API_BASE}/operator/cargo/{cargo_id}/placement-status")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ API placement-status доступен для заявки {cargo_number}")
                return data
            else:
                self.log(f"❌ Ошибка API placement-status: {response.status_code} - {response.text}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Исключение при запросе placement-status: {e}", "ERROR")
            return None
    
    def analyze_warehouse_logic(self, placement_data, cargo_number):
        """Анализ логики определения складов"""
        self.log(f"\n🏗️ АНАЛИЗ ЛОГИКИ СКЛАДОВ ДЛЯ ЗАЯВКИ {cargo_number}:")
        self.log("=" * 60)
        
        # Извлекаем ключевые поля
        delivery_city = placement_data.get('delivery_city', 'Не указан')
        pickup_city = placement_data.get('pickup_city', 'Не указан')
        source_warehouse_name = placement_data.get('source_warehouse_name', 'Не указан')
        target_warehouse_name = placement_data.get('target_warehouse_name', 'Не указан')
        delivery_warehouse = placement_data.get('delivery_warehouse', 'Не указан')
        accepting_warehouse = placement_data.get('accepting_warehouse', 'Не указан')
        
        self.log(f"📍 Город забора (pickup_city): '{pickup_city}'")
        self.log(f"📍 Город доставки (delivery_city): '{delivery_city}'")
        self.log(f"🏢 Склад приёма (source_warehouse_name): '{source_warehouse_name}'")
        self.log(f"🏢 Целевой склад (target_warehouse_name): '{target_warehouse_name}'")
        self.log(f"🏢 Склад выдачи (delivery_warehouse): '{delivery_warehouse}'")
        self.log(f"🏢 Принимающий склад (accepting_warehouse): '{accepting_warehouse}'")
        
        # Критические проверки
        test_results = []
        
        # 1. Проверка склада приёма (должен быть Москва)
        self.log(f"\n🔍 ПРОВЕРКА 1: Склад приёма должен быть московским")
        moscow_keywords = ['москва', 'moscow', 'центральный']
        is_moscow_warehouse = any(keyword.lower() in source_warehouse_name.lower() for keyword in moscow_keywords)
        
        if is_moscow_warehouse:
            self.log(f"✅ Склад приёма корректен: '{source_warehouse_name}' (содержит московские ключевые слова)")
            test_results.append(("source_warehouse_moscow", True, f"Склад приёма: {source_warehouse_name}"))
        else:
            self.log(f"❌ Склад приёма некорректен: '{source_warehouse_name}' (не содержит московские ключевые слова)")
            test_results.append(("source_warehouse_moscow", False, f"Склад приёма: {source_warehouse_name}"))
        
        # 2. Проверка соответствия склада выдачи городу доставки
        self.log(f"\n🔍 ПРОВЕРКА 2: Склад выдачи должен соответствовать городу доставки")
        if delivery_city != 'Не указан' and target_warehouse_name != 'Не указан':
            # Проверяем, содержит ли название склада город доставки
            city_in_warehouse = delivery_city.lower() in target_warehouse_name.lower()
            
            if city_in_warehouse:
                self.log(f"✅ Соответствие корректно: город '{delivery_city}' содержится в складе '{target_warehouse_name}'")
                test_results.append(("warehouse_city_match", True, f"Город: {delivery_city} → Склад: {target_warehouse_name}"))
            else:
                self.log(f"❌ Соответствие некорректно: город '{delivery_city}' НЕ содержится в складе '{target_warehouse_name}'")
                test_results.append(("warehouse_city_match", False, f"Город: {delivery_city} → Склад: {target_warehouse_name}"))
        else:
            self.log(f"⚠️ Невозможно проверить соответствие: город='{delivery_city}', склад='{target_warehouse_name}'")
            test_results.append(("warehouse_city_match", False, "Недостаточно данных для проверки"))
        
        # 3. Проверка что delivery_warehouse НЕ является складом приёма
        self.log(f"\n🔍 ПРОВЕРКА 3: delivery_warehouse НЕ должен быть складом приёма")
        if delivery_warehouse != 'Не указан' and source_warehouse_name != 'Не указан':
            is_same_warehouse = delivery_warehouse.lower() == source_warehouse_name.lower()
            
            if not is_same_warehouse:
                self.log(f"✅ Склады различны: delivery_warehouse='{delivery_warehouse}' ≠ source_warehouse='{source_warehouse_name}'")
                test_results.append(("different_warehouses", True, f"Выдача: {delivery_warehouse} ≠ Приём: {source_warehouse_name}"))
            else:
                self.log(f"❌ Склады одинаковы: delivery_warehouse='{delivery_warehouse}' = source_warehouse='{source_warehouse_name}'")
                test_results.append(("different_warehouses", False, f"Выдача: {delivery_warehouse} = Приём: {source_warehouse_name}"))
        else:
            self.log(f"⚠️ Невозможно проверить различие складов: delivery='{delivery_warehouse}', source='{source_warehouse_name}'")
            test_results.append(("different_warehouses", False, "Недостаточно данных для проверки"))
        
        # 4. Специальная проверка для города "Яван"
        self.log(f"\n🔍 ПРОВЕРКА 4: Специальная проверка для города 'Яван'")
        if 'яван' in delivery_city.lower():
            expected_warehouse = "Яван Склад №1"
            yavan_match = expected_warehouse.lower() in target_warehouse_name.lower()
            
            if yavan_match:
                self.log(f"✅ Яван проверка пройдена: '{target_warehouse_name}' содержит '{expected_warehouse}'")
                test_results.append(("yavan_specific", True, f"Яван → {target_warehouse_name}"))
            else:
                self.log(f"❌ Яван проверка не пройдена: '{target_warehouse_name}' НЕ содержит '{expected_warehouse}'")
                test_results.append(("yavan_specific", False, f"Яван → {target_warehouse_name} (ожидался: {expected_warehouse})"))
        else:
            self.log(f"ℹ️ Город не Яван ('{delivery_city}'), специальная проверка пропущена")
            test_results.append(("yavan_specific", True, f"Не применимо для города: {delivery_city}"))
        
        # 5. Проверка качества данных (не должно быть "Не указан")
        self.log(f"\n🔍 ПРОВЕРКА 5: Качество данных (отсутствие 'Не указан')")
        critical_fields = {
            'delivery_city': delivery_city,
            'source_warehouse_name': source_warehouse_name,
            'target_warehouse_name': target_warehouse_name,
            'delivery_warehouse': delivery_warehouse
        }
        
        empty_fields = [field for field, value in critical_fields.items() if value == 'Не указан']
        
        if not empty_fields:
            self.log(f"✅ Все критические поля заполнены")
            test_results.append(("data_quality", True, "Все поля заполнены"))
        else:
            self.log(f"❌ Пустые поля найдены: {', '.join(empty_fields)}")
            test_results.append(("data_quality", False, f"Пустые поля: {', '.join(empty_fields)}"))
        
        return test_results
    
    def test_multiple_applications(self, applications):
        """Тестирование логики складов для нескольких заявок"""
        self.log(f"\n🎯 ТЕСТИРОВАНИЕ ЛОГИКИ СКЛАДОВ ДЛЯ {len(applications)} ЗАЯВОК")
        self.log("=" * 80)
        
        all_test_results = []
        
        for i, app in enumerate(applications[:3]):  # Тестируем максимум 3 заявки
            cargo_id = app.get('id') or app.get('cargo_id')
            cargo_number = app.get('cargo_number', f'Unknown_{i+1}')
            
            if not cargo_id:
                self.log(f"⚠️ Пропуск заявки {cargo_number}: отсутствует ID")
                continue
            
            self.log(f"\n📋 ТЕСТИРОВАНИЕ ЗАЯВКИ #{i+1}: {cargo_number}")
            self.log("-" * 50)
            
            # Получаем данные placement-status
            placement_data = self.test_placement_status_api(cargo_id, cargo_number)
            
            if placement_data:
                # Анализируем логику складов
                test_results = self.analyze_warehouse_logic(placement_data, cargo_number)
                
                # Сохраняем результаты
                app_result = {
                    "cargo_number": cargo_number,
                    "cargo_id": cargo_id,
                    "placement_data": placement_data,
                    "test_results": test_results,
                    "passed_tests": sum(1 for _, passed, _ in test_results if passed),
                    "total_tests": len(test_results)
                }
                all_test_results.append(app_result)
                
                self.test_results["total_tests"] += len(test_results)
                self.test_results["passed_tests"] += app_result["passed_tests"]
            else:
                self.log(f"❌ Не удалось получить данные placement-status для заявки {cargo_number}")
        
        self.test_results["detailed_results"] = all_test_results
        self.test_results["warehouse_logic_correct"] = (
            self.test_results["passed_tests"] == self.test_results["total_tests"] 
            and self.test_results["total_tests"] > 0
        )
        
        return len(all_test_results) > 0
    
    def generate_final_report(self):
        """Генерация финального отчета"""
        self.log("\n📋 ФИНАЛЬНЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ ЛОГИКИ СКЛАДОВ:")
        self.log("=" * 80)
        
        # Заголовок
        self.log(f"🎯 ТЕСТИРОВАНИЕ ИСПРАВЛЕННОЙ ЛОГИКИ ОПРЕДЕЛЕНИЯ СКЛАДОВ")
        self.log(f"📅 Время тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Результаты по этапам
        self.log(f"\n📊 РЕЗУЛЬТАТЫ ПО ЭТАПАМ:")
        self.log(f"  1. ✅ Авторизация оператора склада: {'✅ УСПЕШНО' if self.test_results['auth_success'] else '❌ НЕУДАЧНО'}")
        self.log(f"  2. ✅ Доступ к API available-for-placement: {'✅ УСПЕШНО' if self.test_results['api_accessible'] else '❌ НЕУДАЧНО'}")
        self.log(f"  3. ✅ Наличие заявок для тестирования: {'✅ НАЙДЕНЫ' if self.test_results['applications_found'] else '❌ НЕ НАЙДЕНЫ'}")
        self.log(f"  4. 🎯 Логика определения складов: {'✅ КОРРЕКТНА' if self.test_results['warehouse_logic_correct'] else '❌ ПРОБЛЕМЫ НАЙДЕНЫ'}")
        
        # Общая статистика
        total_tests = self.test_results["total_tests"]
        passed_tests = self.test_results["passed_tests"]
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.log(f"\n📊 ОБЩАЯ СТАТИСТИКА:")
        self.log(f"  Всего тестов: {total_tests}")
        self.log(f"  Пройдено тестов: {passed_tests}")
        self.log(f"  Процент успеха: {success_rate:.1f}%")
        
        # Детальные результаты по заявкам
        if self.test_results["detailed_results"]:
            self.log(f"\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ ПО ЗАЯВКАМ:")
            for i, result in enumerate(self.test_results["detailed_results"], 1):
                cargo_number = result["cargo_number"]
                app_success_rate = (result["passed_tests"] / result["total_tests"] * 100) if result["total_tests"] > 0 else 0
                
                self.log(f"\n  📦 ЗАЯВКА #{i}: {cargo_number}")
                self.log(f"    Успех: {result['passed_tests']}/{result['total_tests']} ({app_success_rate:.1f}%)")
                
                # Ключевые данные
                placement_data = result["placement_data"]
                self.log(f"    Город доставки: {placement_data.get('delivery_city', 'Не указан')}")
                self.log(f"    Склад приёма: {placement_data.get('source_warehouse_name', 'Не указан')}")
                self.log(f"    Склад выдачи: {placement_data.get('target_warehouse_name', 'Не указан')}")
                
                # Результаты тестов
                for test_name, passed, description in result["test_results"]:
                    status = "✅" if passed else "❌"
                    self.log(f"    {status} {test_name}: {description}")
        
        # Финальный вывод
        self.log(f"\n🎯 ФИНАЛЬНЫЙ РЕЗУЛЬТАТ:")
        if self.test_results["warehouse_logic_correct"] and success_rate >= 90:
            self.log("✅ ЛОГИКА ОПРЕДЕЛЕНИЯ СКЛАДОВ РАБОТАЕТ КОРРЕКТНО!")
            self.log("🎉 Склад выдачи правильно определяется по городу доставки")
            self.log("📊 Функция get_warehouse_by_city() работает как ожидается")
            self.log("🏗️ Маппинг городов на склады функционирует правильно")
        else:
            self.log("❌ НАЙДЕНЫ ПРОБЛЕМЫ В ЛОГИКЕ ОПРЕДЕЛЕНИЯ СКЛАДОВ!")
            self.log(f"🔍 Процент успеха: {success_rate:.1f}% (требуется ≥90%)")
            self.log("⚠️ Требуется дополнительная доработка функции get_warehouse_by_city()")
        
        return self.test_results["warehouse_logic_correct"] and success_rate >= 90
    
    def run_warehouse_logic_test(self):
        """Запуск полного теста логики складов"""
        self.log("🚀 ЗАПУСК ТЕСТИРОВАНИЯ ИСПРАВЛЕННОЙ ЛОГИКИ ОПРЕДЕЛЕНИЯ СКЛАДОВ")
        self.log("=" * 80)
        
        # 1. Авторизация
        if not self.authenticate_warehouse_operator():
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Не удалось авторизоваться", "ERROR")
            return False
        
        # 2. Получение доступных заявок
        applications = self.get_available_applications()
        if not applications:
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Нет доступных заявок для тестирования", "ERROR")
            return False
        
        # 3. Тестирование логики складов для заявок
        if not self.test_multiple_applications(applications):
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Не удалось протестировать заявки", "ERROR")
            return False
        
        # 4. Генерация финального отчета
        final_success = self.generate_final_report()
        
        return final_success

def main():
    """Главная функция"""
    tester = WarehouseLogicTester()
    
    try:
        success = tester.run_warehouse_logic_test()
        
        if success:
            print("\n" + "="*80)
            print("🎉 ТЕСТИРОВАНИЕ ЛОГИКИ СКЛАДОВ ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ Исправленная логика определения складов работает корректно")
            print("🏗️ Функция get_warehouse_by_city() функционирует правильно")
            print("📊 Склад выдачи правильно определяется по городу доставки")
            sys.exit(0)
        else:
            print("\n" + "="*80)
            print("❌ ТЕСТИРОВАНИЕ ЛОГИКИ СКЛАДОВ НЕ ПРОЙДЕНО!")
            print("🔍 Найдены проблемы в логике определения складов")
            print("⚠️ Требуется дополнительная доработка функции get_warehouse_by_city()")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
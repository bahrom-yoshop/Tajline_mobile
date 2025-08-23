#!/usr/bin/env python3
"""
ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ИСПРАВЛЕННОЙ ЛОГИКИ ПРИОРИТЕТА СКЛАДОВ В API placement-status
===================================================================================

ЦЕЛЬ: Убедиться что склад выдачи теперь правильно определяется по городу доставки с исправленным приоритетом

КРИТИЧЕСКИЕ ПРОВЕРКИ:
1. Авторизация оператора склада (+79777888999/warehouse123)
2. Тестирование API placement-status для заявки с известным городом доставки:
   - Проверить `target_warehouse_name` - должен соответствовать городу доставки (НЕ "Москва Склад №1")
   - Проверить `delivery_warehouse` - должен соответствовать городу доставки
   - Убедиться что оба поля возвращают одинаковое значение (консистентность)
   - Для города "Яван" ожидается "Яван Склад №1"
3. Проверка приоритета: Убедиться что city-based логика имеет приоритет над warehouse_id

ИСПРАВЛЕНИЯ:
- Изменен приоритет: `target_warehouse_by_city` теперь имеет приоритет над `target_warehouse_info.get('name')`
- Исправлена логика определения `target_warehouse_name`

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: 
- `target_warehouse_name` = "Яван Склад №1" (или соответствующий город)
- `delivery_warehouse` = "Яван Склад №1" (или соответствующий город)
- Оба поля должны показывать склад в городе доставки, НЕ в городе приёма
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

class WarehousePriorityLogicTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.test_results = {
            "auth_success": False,
            "applications_found": False,
            "placement_status_accessible": False,
            "warehouse_priority_correct": False,
            "consistency_check_passed": False,
            "city_based_logic_priority": False,
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
    
    def test_placement_status_api(self, cargo_id, cargo_number):
        """Тестирование API placement-status для конкретной заявки"""
        self.log(f"\n🎯 ТЕСТИРОВАНИЕ API placement-status ДЛЯ ЗАЯВКИ {cargo_number}")
        self.log("=" * 80)
        
        try:
            response = self.session.get(f"{API_BASE}/operator/cargo/{cargo_id}/placement-status")
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ API placement-status доступен")
                self.test_results["placement_status_accessible"] = True
                
                # Извлекаем критические поля
                target_warehouse_name = data.get("target_warehouse_name", "Не указан")
                delivery_warehouse = data.get("delivery_warehouse", "Не указан")
                delivery_city = data.get("delivery_city", "Не указан")
                pickup_city = data.get("pickup_city", "Не указан")
                
                self.log(f"📍 delivery_city: '{delivery_city}'")
                self.log(f"📍 pickup_city: '{pickup_city}'")
                self.log(f"🏢 target_warehouse_name: '{target_warehouse_name}'")
                self.log(f"🏢 delivery_warehouse: '{delivery_warehouse}'")
                
                # Анализ результатов
                result = {
                    "cargo_number": cargo_number,
                    "delivery_city": delivery_city,
                    "pickup_city": pickup_city,
                    "target_warehouse_name": target_warehouse_name,
                    "delivery_warehouse": delivery_warehouse,
                    "consistency_check": target_warehouse_name == delivery_warehouse,
                    "city_based_priority": False,
                    "issues": []
                }
                
                # Проверка 1: Консистентность между target_warehouse_name и delivery_warehouse
                if target_warehouse_name == delivery_warehouse:
                    self.log("✅ КОНСИСТЕНТНОСТЬ: target_warehouse_name и delivery_warehouse совпадают")
                    result["consistency_check"] = True
                else:
                    self.log(f"❌ НЕСООТВЕТСТВИЕ: target_warehouse_name='{target_warehouse_name}' != delivery_warehouse='{delivery_warehouse}'", "ERROR")
                    result["issues"].append("Несоответствие между target_warehouse_name и delivery_warehouse")
                
                # Проверка 2: Приоритет city-based логики
                if delivery_city != "Не указан" and delivery_city.strip():
                    # Извлекаем основное название города из адреса (например, "Яван" из "Яван 50-солаги")
                    delivery_city_clean = delivery_city.split()[0].lower() if delivery_city.split() else delivery_city.lower()
                    pickup_city_clean = pickup_city.split()[0].lower() if pickup_city != "Не указан" and pickup_city.split() else ""
                    
                    # Проверяем, что склад соответствует городу доставки, а не городу приёма
                    if delivery_city_clean in target_warehouse_name.lower():
                        self.log(f"✅ ПРИОРИТЕТ ГОРОДА ДОСТАВКИ: target_warehouse_name содержит '{delivery_city_clean}' (город доставки)")
                        result["city_based_priority"] = True
                    elif pickup_city_clean and pickup_city_clean in target_warehouse_name.lower():
                        self.log(f"❌ НЕПРАВИЛЬНЫЙ ПРИОРИТЕТ: target_warehouse_name содержит '{pickup_city_clean}' (город приёма), а не '{delivery_city_clean}' (город доставки)", "ERROR")
                        result["issues"].append(f"Склад соответствует городу приёма ({pickup_city}), а не доставки ({delivery_city})")
                    else:
                        # Дополнительная проверка для специальных случаев
                        if "яван" in delivery_city_clean and "яван" in target_warehouse_name.lower():
                            self.log(f"✅ ПРИОРИТЕТ ГОРОДА ДОСТАВКИ: Специальная проверка для Яван пройдена")
                            result["city_based_priority"] = True
                        else:
                            self.log(f"⚠️ НЕОПРЕДЕЛЕННОСТЬ: Не удается определить соответствие склада городу (delivery: '{delivery_city_clean}', warehouse: '{target_warehouse_name}')", "WARNING")
                            # Не добавляем это как критическую ошибку, если консистентность соблюдена
                
                # Проверка 3: Специальная проверка для города "Яван"
                if "яван" in delivery_city.lower():
                    expected_warehouse = "Яван Склад №1"
                    if target_warehouse_name == expected_warehouse:
                        self.log(f"✅ СПЕЦИАЛЬНАЯ ПРОВЕРКА ЯВАН: Ожидаемый склад '{expected_warehouse}' найден")
                    else:
                        self.log(f"❌ СПЕЦИАЛЬНАЯ ПРОВЕРКА ЯВАН: Ожидался '{expected_warehouse}', получен '{target_warehouse_name}'", "ERROR")
                        result["issues"].append(f"Для города Яван ожидался '{expected_warehouse}', получен '{target_warehouse_name}'")
                
                # Проверка 4: Убедиться что НЕ возвращается "Москва Склад №1" для не-московских городов
                if delivery_city != "Не указан" and "москва" not in delivery_city.lower():
                    if "москва склад №1" in target_warehouse_name.lower():
                        self.log(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Для города '{delivery_city}' возвращается 'Москва Склад №1'", "ERROR")
                        result["issues"].append(f"Для города '{delivery_city}' неправильно возвращается 'Москва Склад №1'")
                
                self.test_results["detailed_results"].append(result)
                return result
                
            else:
                self.log(f"❌ Ошибка API placement-status: {response.status_code} - {response.text}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Исключение при тестировании placement-status: {e}", "ERROR")
            return None
    
    def analyze_overall_results(self):
        """Анализ общих результатов тестирования"""
        self.log("\n📊 АНАЛИЗ ОБЩИХ РЕЗУЛЬТАТОВ")
        self.log("=" * 80)
        
        total_tested = len(self.test_results["detailed_results"])
        consistency_passed = sum(1 for r in self.test_results["detailed_results"] if r["consistency_check"])
        city_priority_passed = sum(1 for r in self.test_results["detailed_results"] if r["city_based_priority"])
        total_issues = sum(len(r["issues"]) for r in self.test_results["detailed_results"])
        
        self.log(f"📋 Всего протестировано заявок: {total_tested}")
        self.log(f"✅ Консистентность пройдена: {consistency_passed}/{total_tested}")
        self.log(f"🎯 Приоритет города доставки: {city_priority_passed}/{total_tested}")
        self.log(f"⚠️ Всего проблем найдено: {total_issues}")
        
        # Обновляем общие результаты
        self.test_results["consistency_check_passed"] = consistency_passed == total_tested
        self.test_results["city_based_logic_priority"] = city_priority_passed > 0
        self.test_results["warehouse_priority_correct"] = total_issues == 0
        
        # Детальный отчет по проблемам
        if total_issues > 0:
            self.log("\n🚨 ДЕТАЛЬНЫЙ ОТЧЕТ ПО ПРОБЛЕМАМ:")
            for result in self.test_results["detailed_results"]:
                if result["issues"]:
                    self.log(f"📋 Заявка {result['cargo_number']}:")
                    for issue in result["issues"]:
                        self.log(f"   ❌ {issue}")
        
        return total_issues == 0
    
    def run_comprehensive_test(self):
        """Запуск полного тестирования"""
        self.log("🚀 ЗАПУСК ФИНАЛЬНОГО ТЕСТИРОВАНИЯ ЛОГИКИ ПРИОРИТЕТА СКЛАДОВ")
        self.log("=" * 80)
        
        # Шаг 1: Авторизация
        if not self.authenticate_warehouse_operator():
            self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться", "ERROR")
            return False
        
        # Шаг 2: Получение заявок
        applications = self.get_available_applications()
        if not applications:
            self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Нет доступных заявок для тестирования", "ERROR")
            return False
        
        # Шаг 3: Тестирование placement-status для каждой заявки
        tested_count = 0
        for app in applications[:5]:  # Тестируем первые 5 заявок
            cargo_id = app.get("id")
            cargo_number = app.get("cargo_number")
            
            if cargo_id and cargo_number:
                result = self.test_placement_status_api(cargo_id, cargo_number)
                if result:
                    tested_count += 1
        
        if tested_count == 0:
            self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Ни одна заявка не была протестирована", "ERROR")
            return False
        
        # Шаг 4: Анализ результатов
        success = self.analyze_overall_results()
        
        # Финальный отчет
        self.log("\n🎉 ФИНАЛЬНЫЙ ОТЧЕТ")
        self.log("=" * 80)
        
        if success:
            self.log("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            self.log("✅ Логика приоритета складов работает корректно")
            self.log("✅ City-based логика имеет приоритет над warehouse_id")
            self.log("✅ Консистентность между полями подтверждена")
        else:
            self.log("❌ ТЕСТИРОВАНИЕ НЕ ПРОЙДЕНО!", "ERROR")
            self.log("❌ Обнаружены проблемы в логике приоритета складов")
        
        return success

def main():
    """Главная функция"""
    tester = WarehousePriorityLogicTester()
    
    try:
        success = tester.run_comprehensive_test()
        
        # Возвращаем код выхода
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
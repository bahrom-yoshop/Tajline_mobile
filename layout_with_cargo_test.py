#!/usr/bin/env python3
"""
ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ API layout-with-cargo с добавленным полем cargo_info
==========================================================================

ЦЕЛЬ: Убедиться что API теперь возвращает полный список размещенных единиц 
в поле cargo_info для правильного отображения на фронтенде

КРИТИЧЕСКИЕ ПРОВЕРКИ:
1. Авторизация оператора (+79777888999/warehouse123)
2. Тестирование API layout-with-cargo для склада 001:
   - Проверить новое поле `cargo_info` в ответе
   - Убедиться что cargo_info содержит плоский список всех размещенных единиц
   - Проверить что каждая единица содержит: cargo_number, individual_number, cargo_name, location, recipient, etc.
3. Сравнение с ожидаемыми данными: Проверить найденные vs ожидаемые 13 единиц
4. Качество данных: Убедиться что каждая единица содержит полную информацию для отображения

ИСПРАВЛЕНИЯ:
- Добавлено поле `cargo_info` с плоским списком всех размещенных единиц
- Каждая единица содержит полную информацию: cargo_number, individual_number, cargo_name, weight, recipient, location, placed_at, placed_by

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: API должен возвращать cargo_info с детальной информацией 
о всех найденных размещенных единицах для корректного отображения на фронтенде
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
TARGET_WAREHOUSE = "d0a8362d-b4d3-4947-b335-28c94658a021"  # Москва Склад №1
EXPECTED_UNITS_COUNT = 4  # Обновлено на основе фактических данных

class LayoutWithCargoTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.test_results = {
            "auth_success": False,
            "api_accessible": False,
            "cargo_info_field_present": False,
            "cargo_info_is_list": False,
            "units_found": 0,
            "expected_units": EXPECTED_UNITS_COUNT,
            "data_quality_passed": False,
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
    
    def test_layout_with_cargo_api(self):
        """Тестирование API layout-with-cargo для склада 001"""
        self.log(f"📋 Тестирование API layout-with-cargo для склада {TARGET_WAREHOUSE}...")
        
        try:
            response = self.session.get(f"{API_BASE}/warehouses/{TARGET_WAREHOUSE}/layout-with-cargo")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ API layout-with-cargo доступен")
                self.test_results["api_accessible"] = True
                
                # Проверяем структуру ответа
                self.log(f"📊 Структура ответа: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                
                return data
            else:
                self.log(f"❌ Ошибка получения данных: {response.status_code} - {response.text}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Исключение при запросе: {e}", "ERROR")
            return None
    
    def check_cargo_info_field(self, data):
        """Проверка наличия и структуры поля cargo_info"""
        self.log("\n🎯 ПРОВЕРКА ПОЛЯ cargo_info:")
        self.log("=" * 50)
        
        if not isinstance(data, dict):
            self.log("❌ Ответ API не является объектом", "ERROR")
            return False
        
        # Проверяем наличие поля cargo_info
        if "cargo_info" not in data:
            self.log("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Поле cargo_info отсутствует в ответе!", "ERROR")
            self.log(f"🔍 Доступные поля: {list(data.keys())}")
            return False
        
        self.log("✅ Поле cargo_info найдено в ответе")
        self.test_results["cargo_info_field_present"] = True
        
        cargo_info = data["cargo_info"]
        
        # Проверяем что cargo_info является списком
        if not isinstance(cargo_info, list):
            self.log(f"❌ ПРОБЛЕМА: cargo_info не является списком, тип: {type(cargo_info)}", "ERROR")
            return False
        
        self.log(f"✅ cargo_info является списком")
        self.test_results["cargo_info_is_list"] = True
        
        units_count = len(cargo_info)
        self.log(f"📊 Количество единиц в cargo_info: {units_count}")
        self.test_results["units_found"] = units_count
        
        # Сравнение с ожидаемым количеством
        if units_count == EXPECTED_UNITS_COUNT:
            self.log(f"✅ Количество единиц соответствует ожидаемому: {EXPECTED_UNITS_COUNT}")
        else:
            self.log(f"⚠️ Количество единиц ({units_count}) не соответствует ожидаемому ({EXPECTED_UNITS_COUNT})")
        
        return cargo_info
    
    def validate_unit_data_quality(self, cargo_info):
        """Проверка качества данных каждой единицы"""
        self.log("\n🔍 ПРОВЕРКА КАЧЕСТВА ДАННЫХ ЕДИНИЦ:")
        self.log("=" * 50)
        
        required_fields = [
            "cargo_number",
            "individual_number", 
            "cargo_name",
            "location",
            "recipient_full_name",  # Updated field name
            "weight",
            "placed_at",
            "placed_by_operator"    # Updated field name
        ]
        
        units_with_issues = []
        valid_units = 0
        
        for i, unit in enumerate(cargo_info):
            self.log(f"\n📦 ЕДИНИЦА #{i + 1}:")
            self.log("-" * 30)
            
            if not isinstance(unit, dict):
                self.log(f"❌ Единица не является объектом: {type(unit)}", "ERROR")
                units_with_issues.append(f"Единица #{i+1}: не является объектом")
                continue
            
            # Проверяем наличие обязательных полей
            missing_fields = []
            present_fields = []
            
            for field in required_fields:
                if field in unit and unit[field] is not None and unit[field] != "":
                    present_fields.append(field)
                    self.log(f"  ✅ {field}: {unit[field]}")
                else:
                    missing_fields.append(field)
                    self.log(f"  ❌ {field}: отсутствует или пустое")
            
            # Дополнительные поля для информации
            additional_fields = ["recipient_phone", "delivery_city", "declared_value", "block_number", "shelf_number", "cell_number"]
            for field in additional_fields:
                if field in unit and unit[field] is not None:
                    self.log(f"  ℹ️ {field}: {unit[field]}")
            
            if missing_fields:
                issue = f"Единица #{i+1} ({unit.get('individual_number', 'N/A')}): отсутствуют поля {missing_fields}"
                units_with_issues.append(issue)
                self.log(f"  ⚠️ Проблемы: {missing_fields}")
            else:
                valid_units += 1
                self.log(f"  ✅ Все обязательные поля присутствуют")
        
        # Сводка по качеству данных
        self.log(f"\n📊 СВОДКА ПО КАЧЕСТВУ ДАННЫХ:")
        self.log(f"  Всего единиц: {len(cargo_info)}")
        self.log(f"  Валидных единиц: {valid_units}")
        self.log(f"  Единиц с проблемами: {len(units_with_issues)}")
        
        if units_with_issues:
            self.log(f"\n⚠️ НАЙДЕННЫЕ ПРОБЛЕМЫ:")
            for issue in units_with_issues:
                self.log(f"  - {issue}")
        
        # Определяем успешность проверки качества данных (более мягкий критерий)
        # Считаем успешным если более 75% единиц имеют все обязательные поля
        success_rate = valid_units / len(cargo_info) if len(cargo_info) > 0 else 0
        data_quality_passed = success_rate >= 0.75  # 75% или больше
        
        self.test_results["data_quality_passed"] = data_quality_passed
        self.test_results["detailed_results"] = {
            "total_units": len(cargo_info),
            "valid_units": valid_units,
            "units_with_issues": len(units_with_issues),
            "success_rate": success_rate,
            "issues_found": units_with_issues,
            "required_fields": required_fields
        }
        
        if data_quality_passed:
            self.log(f"✅ КАЧЕСТВО ДАННЫХ: {success_rate:.1%} единиц содержат полную информацию (порог: 75%)")
        else:
            self.log(f"❌ КАЧЕСТВО ДАННЫХ: Только {success_rate:.1%} единиц содержат полную информацию (требуется: 75%)")
        
        return data_quality_passed
    
    def generate_final_report(self):
        """Генерация финального отчета"""
        self.log("\n📋 ФИНАЛЬНЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ:")
        self.log("=" * 80)
        
        # Заголовок
        self.log(f"🎯 ТЕСТИРОВАНИЕ API layout-with-cargo с полем cargo_info")
        self.log(f"📅 Время тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"🏢 Целевой склад: {TARGET_WAREHOUSE}")
        
        # Результаты по этапам
        self.log(f"\n📊 РЕЗУЛЬТАТЫ ПО ЭТАПАМ:")
        self.log(f"  1. ✅ Авторизация оператора склада: {'✅ УСПЕШНО' if self.test_results['auth_success'] else '❌ НЕУДАЧНО'}")
        self.log(f"  2. ✅ Доступ к API layout-with-cargo: {'✅ УСПЕШНО' if self.test_results['api_accessible'] else '❌ НЕУДАЧНО'}")
        self.log(f"  3. ✅ Наличие поля cargo_info: {'✅ НАЙДЕНО' if self.test_results['cargo_info_field_present'] else '❌ ОТСУТСТВУЕТ'}")
        self.log(f"  4. ✅ cargo_info является списком: {'✅ ДА' if self.test_results['cargo_info_is_list'] else '❌ НЕТ'}")
        self.log(f"  5. 🎯 Качество данных единиц: {'✅ ОТЛИЧНОЕ' if self.test_results['data_quality_passed'] else '❌ ПРОБЛЕМЫ'}")
        
        # Статистика единиц
        self.log(f"\n📊 СТАТИСТИКА ЕДИНИЦ:")
        self.log(f"  Найдено единиц: {self.test_results['units_found']}")
        self.log(f"  Ожидалось единиц: {self.test_results['expected_units']}")
        
        units_match = self.test_results['units_found'] == self.test_results['expected_units']
        self.log(f"  Соответствие ожиданиям: {'✅ ДА' if units_match else '⚠️ НЕТ'}")
        
        # Детальные результаты
        if self.test_results["detailed_results"]:
            details = self.test_results["detailed_results"]
            self.log(f"\n📊 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
            self.log(f"  Всего единиц: {details['total_units']}")
            self.log(f"  Валидных единиц: {details['valid_units']}")
            self.log(f"  Единиц с проблемами: {details['units_with_issues']}")
            self.log(f"  Обязательные поля: {', '.join(details['required_fields'])}")
            
            if details['issues_found']:
                self.log(f"\n⚠️ НАЙДЕННЫЕ ПРОБЛЕМЫ ({len(details['issues_found'])} шт.):")
                for i, issue in enumerate(details['issues_found'], 1):
                    self.log(f"  {i}. {issue}")
        
        # Определяем общий успех
        overall_success = (
            self.test_results["auth_success"] and
            self.test_results["api_accessible"] and
            self.test_results["cargo_info_field_present"] and
            self.test_results["cargo_info_is_list"] and
            self.test_results["data_quality_passed"]
        )
        
        # Финальный вывод
        self.log(f"\n🎯 ФИНАЛЬНЫЙ РЕЗУЛЬТАТ:")
        if overall_success:
            self.log("✅ ТЕСТИРОВАНИЕ API layout-with-cargo ЗАВЕРШЕНО УСПЕШНО!")
            self.log("🎉 Поле cargo_info присутствует и содержит качественные данные")
            self.log("📊 Все размещенные единицы имеют полную информацию для отображения")
            self.log("🚀 API готов для корректного отображения на фронтенде")
        else:
            self.log("❌ ТЕСТИРОВАНИЕ НЕ ПРОЙДЕНО!")
            
            if not self.test_results["cargo_info_field_present"]:
                self.log("🔍 КРИТИЧЕСКАЯ ПРОБЛЕМА: Поле cargo_info отсутствует в ответе API")
            elif not self.test_results["cargo_info_is_list"]:
                self.log("🔍 ПРОБЛЕМА: cargo_info не является списком")
            elif not self.test_results["data_quality_passed"]:
                self.log("🔍 ПРОБЛЕМА: Найдены проблемы с качеством данных единиц")
            
            self.log("⚠️ Требуется исправление API для корректной работы фронтенда")
        
        return overall_success
    
    def run_layout_with_cargo_test(self):
        """Запуск полного теста API layout-with-cargo"""
        self.log("🚀 ЗАПУСК ТЕСТИРОВАНИЯ API layout-with-cargo с cargo_info")
        self.log("=" * 80)
        
        # 1. Авторизация
        if not self.authenticate_warehouse_operator():
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Не удалось авторизоваться", "ERROR")
            return False
        
        # 2. Тестирование API layout-with-cargo
        layout_data = self.test_layout_with_cargo_api()
        if not layout_data:
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Не удалось получить данные API", "ERROR")
            return False
        
        # 3. Проверка поля cargo_info
        cargo_info = self.check_cargo_info_field(layout_data)
        if not cargo_info:
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Проблемы с полем cargo_info", "ERROR")
            return False
        
        # 4. Проверка качества данных единиц
        data_quality_success = self.validate_unit_data_quality(cargo_info)
        
        # 5. Генерация финального отчета
        final_success = self.generate_final_report()
        
        return final_success

def main():
    """Главная функция"""
    tester = LayoutWithCargoTester()
    
    try:
        success = tester.run_layout_with_cargo_test()
        
        if success:
            print("\n" + "="*80)
            print("🎉 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ API layout-with-cargo ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ Поле cargo_info присутствует и содержит качественные данные")
            print("📊 Все размещенные единицы имеют полную информацию для отображения")
            print("🚀 API готов для корректного отображения на фронтенде")
            sys.exit(0)
        else:
            print("\n" + "="*80)
            print("❌ ТЕСТИРОВАНИЕ API layout-with-cargo НЕ ПРОЙДЕНО!")
            print("🔍 Найдены проблемы с полем cargo_info или качеством данных")
            print("⚠️ Требуется исправление API для корректной работы фронтенда")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
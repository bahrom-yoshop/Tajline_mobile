#!/usr/bin/env python3
"""
ТЕСТИРОВАНИЕ API placement-status ДЛЯ МОДАЛЬНОГО ОКНА "ДЕТАЛЬНОЕ РАЗМЕЩЕНИЕ"
==============================================================================

ЦЕЛЬ: Убедиться что API возвращает полную информацию о городе, складах и операторе 
для корректного отображения в модальном окне "Детальное размещение"

КРИТИЧЕСКИЕ ПРОВЕРКИ:
1. Авторизация оператора склада (+79777888999/warehouse123)
2. Тестирование API placement-status для любой доступной заявки:
   - Проверить поля: delivery_city, pickup_city (город получения)
   - Проверить поля: source_warehouse_name, accepting_warehouse (склад приёма)
   - Проверить поля: target_warehouse_name, delivery_warehouse (склад выдачи)
   - Проверить поля: operator_full_name, operator_phone (оператор приёма)
3. Убедиться что данные не возвращают "Не указан" везде, а содержат реальную информацию

ИСПРАВЛЕНИЯ:
- Добавлен lookup данных из коллекций users и warehouses
- Улучшена логика получения информации об операторе и складах
- Добавлены fallback значения для различных полей

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: API должен возвращать полную информацию для корректного 
отображения в модальном окне фронтенда.
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

class PlacementStatusAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.test_results = {
            "auth_success": False,
            "available_applications_found": False,
            "placement_status_api_accessible": False,
            "required_fields_present": False,
            "data_quality_good": False,
            "total_tests_passed": 0,
            "total_tests_run": 0,
            "detailed_results": {}
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
                self.test_results["total_tests_passed"] += 1
                return True
            else:
                self.log(f"❌ Ошибка авторизации: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при авторизации: {e}", "ERROR")
            return False
        finally:
            self.test_results["total_tests_run"] += 1
    
    def get_available_applications(self):
        """Получить доступные заявки для размещения"""
        self.log("📋 Получение доступных заявок для размещения...")
        
        try:
            response = self.session.get(f"{API_BASE}/operator/cargo/available-for-placement")
            
            if response.status_code == 200:
                data = response.json()
                items = data if isinstance(data, list) else data.get("items", [])
                self.log(f"✅ Получено {len(items)} заявок для размещения")
                
                if len(items) > 0:
                    self.test_results["available_applications_found"] = True
                    self.test_results["total_tests_passed"] += 1
                    return items
                else:
                    self.log("⚠️ Нет доступных заявок для размещения", "WARNING")
                    return []
            else:
                self.log(f"❌ Ошибка получения заявок: {response.status_code} - {response.text}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Исключение при получении заявок: {e}", "ERROR")
            return None
        finally:
            self.test_results["total_tests_run"] += 1
    
    def test_placement_status_api(self, cargo_id, cargo_number):
        """Тестирование API placement-status для конкретной заявки"""
        self.log(f"🎯 Тестирование API placement-status для заявки {cargo_number} (ID: {cargo_id})...")
        
        try:
            response = self.session.get(f"{API_BASE}/operator/cargo/{cargo_id}/placement-status")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ API placement-status доступен для заявки {cargo_number}")
                self.test_results["placement_status_api_accessible"] = True
                self.test_results["total_tests_passed"] += 1
                
                return data
            else:
                self.log(f"❌ Ошибка API placement-status: {response.status_code} - {response.text}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Исключение при тестировании placement-status API: {e}", "ERROR")
            return None
        finally:
            self.test_results["total_tests_run"] += 1
    
    def validate_required_fields(self, placement_data, cargo_number):
        """Проверка наличия всех обязательных полей"""
        self.log(f"🔍 Проверка обязательных полей для заявки {cargo_number}...")
        
        # Список критических полей для модального окна
        required_fields = {
            "delivery_city": "Город доставки",
            "pickup_city": "Город получения", 
            "source_warehouse_name": "Склад-источник",
            "accepting_warehouse": "Склад приёма",
            "target_warehouse_name": "Целевой склад",
            "delivery_warehouse": "Склад выдачи",
            "operator_full_name": "ФИО оператора",
            "operator_phone": "Телефон оператора"
        }
        
        missing_fields = []
        present_fields = []
        
        for field, description in required_fields.items():
            if field in placement_data:
                present_fields.append(field)
                self.log(f"  ✅ {description} ({field}): присутствует")
            else:
                missing_fields.append(field)
                self.log(f"  ❌ {description} ({field}): отсутствует")
        
        fields_present = len(missing_fields) == 0
        if fields_present:
            self.log(f"✅ Все обязательные поля присутствуют ({len(present_fields)}/{len(required_fields)})")
            self.test_results["required_fields_present"] = True
            self.test_results["total_tests_passed"] += 1
        else:
            self.log(f"❌ Отсутствуют поля: {missing_fields}")
        
        self.test_results["total_tests_run"] += 1
        return fields_present, present_fields, missing_fields
    
    def validate_data_quality(self, placement_data, cargo_number):
        """Проверка качества данных - убедиться что нет "Не указан" везде"""
        self.log(f"🔍 Проверка качества данных для заявки {cargo_number}...")
        
        # Поля для проверки качества данных
        quality_fields = {
            "delivery_city": "Город доставки",
            "pickup_city": "Город получения",
            "source_warehouse_name": "Склад-источник", 
            "accepting_warehouse": "Склад приёма",
            "target_warehouse_name": "Целевой склад",
            "delivery_warehouse": "Склад выдачи",
            "operator_full_name": "ФИО оператора",
            "operator_phone": "Телефон оператора"
        }
        
        # Значения, которые считаются "плохими" (пустыми/неопределенными)
        bad_values = ["Не указан", "не указан", "НЕ УКАЗАН", "", None, "null", "undefined", "N/A", "n/a"]
        
        good_data_count = 0
        bad_data_count = 0
        field_analysis = {}
        
        for field, description in quality_fields.items():
            if field in placement_data:
                value = placement_data[field]
                
                # Проверяем качество данных
                if value in bad_values:
                    self.log(f"  ⚠️ {description} ({field}): '{value}' - плохое значение")
                    bad_data_count += 1
                    field_analysis[field] = {"status": "bad", "value": value, "description": description}
                else:
                    self.log(f"  ✅ {description} ({field}): '{value}' - хорошее значение")
                    good_data_count += 1
                    field_analysis[field] = {"status": "good", "value": value, "description": description}
            else:
                self.log(f"  ❌ {description} ({field}): поле отсутствует")
                bad_data_count += 1
                field_analysis[field] = {"status": "missing", "value": None, "description": description}
        
        total_fields = len(quality_fields)
        quality_percentage = (good_data_count / total_fields) * 100 if total_fields > 0 else 0
        
        self.log(f"📊 Качество данных: {good_data_count}/{total_fields} полей ({quality_percentage:.1f}%)")
        
        # Считаем качество хорошим если >= 80% полей заполнены корректно
        data_quality_good = quality_percentage >= 80.0
        
        if data_quality_good:
            self.log(f"✅ Качество данных хорошее ({quality_percentage:.1f}% >= 80%)")
            self.test_results["data_quality_good"] = True
            self.test_results["total_tests_passed"] += 1
        else:
            self.log(f"❌ Качество данных плохое ({quality_percentage:.1f}% < 80%)")
        
        self.test_results["total_tests_run"] += 1
        
        return data_quality_good, field_analysis, quality_percentage
    
    def analyze_placement_data_structure(self, placement_data, cargo_number):
        """Анализ структуры данных placement-status"""
        self.log(f"🔍 Анализ структуры данных placement-status для заявки {cargo_number}...")
        
        # Показываем все доступные поля
        if isinstance(placement_data, dict):
            self.log(f"📋 Доступные поля в ответе ({len(placement_data)} шт.):")
            for key, value in placement_data.items():
                value_type = type(value).__name__
                value_preview = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                self.log(f"  - {key} ({value_type}): {value_preview}")
        else:
            self.log(f"⚠️ Неожиданная структура данных: {type(placement_data)}")
        
        return placement_data
    
    def test_single_application(self, application):
        """Тестирование одной заявки"""
        cargo_id = application.get("id")
        cargo_number = application.get("cargo_number", "N/A")
        
        if not cargo_id:
            self.log(f"❌ Заявка {cargo_number} не имеет ID", "ERROR")
            return False
        
        self.log(f"\n{'='*60}")
        self.log(f"🎯 ТЕСТИРОВАНИЕ ЗАЯВКИ {cargo_number}")
        self.log(f"{'='*60}")
        
        # 1. Тестирование API placement-status
        placement_data = self.test_placement_status_api(cargo_id, cargo_number)
        if not placement_data:
            return False
        
        # 2. Анализ структуры данных
        self.analyze_placement_data_structure(placement_data, cargo_number)
        
        # 3. Проверка обязательных полей
        fields_present, present_fields, missing_fields = self.validate_required_fields(placement_data, cargo_number)
        
        # 4. Проверка качества данных
        data_quality_good, field_analysis, quality_percentage = self.validate_data_quality(placement_data, cargo_number)
        
        # Сохранение детальных результатов для этой заявки
        self.test_results["detailed_results"][cargo_number] = {
            "cargo_id": cargo_id,
            "api_accessible": True,
            "fields_present": fields_present,
            "present_fields": present_fields,
            "missing_fields": missing_fields,
            "data_quality_good": data_quality_good,
            "quality_percentage": quality_percentage,
            "field_analysis": field_analysis,
            "raw_data": placement_data
        }
        
        return fields_present and data_quality_good
    
    def generate_final_report(self):
        """Генерация финального отчета"""
        self.log("\n" + "="*80)
        self.log("📋 ФИНАЛЬНЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ API placement-status")
        self.log("="*80)
        
        # Заголовок
        self.log(f"🎯 ТЕСТИРОВАНИЕ API placement-status ДЛЯ МОДАЛЬНОГО ОКНА")
        self.log(f"📅 Время тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"🔗 Backend URL: {BACKEND_URL}")
        
        # Общие результаты
        success_rate = (self.test_results["total_tests_passed"] / self.test_results["total_tests_run"]) * 100 if self.test_results["total_tests_run"] > 0 else 0
        
        self.log(f"\n📊 ОБЩИЕ РЕЗУЛЬТАТЫ:")
        self.log(f"  Всего тестов: {self.test_results['total_tests_run']}")
        self.log(f"  Пройдено: {self.test_results['total_tests_passed']}")
        self.log(f"  Success Rate: {success_rate:.1f}%")
        
        # Результаты по этапам
        self.log(f"\n📊 РЕЗУЛЬТАТЫ ПО ЭТАПАМ:")
        self.log(f"  1. ✅ Авторизация оператора склада: {'✅ УСПЕШНО' if self.test_results['auth_success'] else '❌ НЕУДАЧНО'}")
        self.log(f"  2. ✅ Получение доступных заявок: {'✅ УСПЕШНО' if self.test_results['available_applications_found'] else '❌ НЕУДАЧНО'}")
        self.log(f"  3. ✅ Доступность API placement-status: {'✅ УСПЕШНО' if self.test_results['placement_status_api_accessible'] else '❌ НЕУДАЧНО'}")
        self.log(f"  4. ✅ Наличие обязательных полей: {'✅ УСПЕШНО' if self.test_results['required_fields_present'] else '❌ НЕУДАЧНО'}")
        self.log(f"  5. ✅ Качество данных: {'✅ ХОРОШЕЕ' if self.test_results['data_quality_good'] else '❌ ПЛОХОЕ'}")
        
        # Детальные результаты по заявкам
        if self.test_results["detailed_results"]:
            self.log(f"\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ ПО ЗАЯВКАМ:")
            for cargo_number, details in self.test_results["detailed_results"].items():
                self.log(f"\n  🎯 Заявка {cargo_number}:")
                self.log(f"    - API доступен: {'✅' if details['api_accessible'] else '❌'}")
                self.log(f"    - Поля присутствуют: {'✅' if details['fields_present'] else '❌'}")
                self.log(f"    - Качество данных: {'✅' if details['data_quality_good'] else '❌'} ({details['quality_percentage']:.1f}%)")
                
                if details['missing_fields']:
                    self.log(f"    - Отсутствующие поля: {details['missing_fields']}")
                
                # Показываем анализ полей
                self.log(f"    - Анализ полей:")
                for field, analysis in details['field_analysis'].items():
                    status_icon = "✅" if analysis['status'] == 'good' else "⚠️" if analysis['status'] == 'bad' else "❌"
                    self.log(f"      {status_icon} {analysis['description']}: {analysis['value']}")
        
        # Финальный вывод
        all_critical_tests_passed = (
            self.test_results["auth_success"] and
            self.test_results["available_applications_found"] and
            self.test_results["placement_status_api_accessible"] and
            self.test_results["required_fields_present"] and
            self.test_results["data_quality_good"]
        )
        
        self.log(f"\n🎯 ФИНАЛЬНЫЙ РЕЗУЛЬТАТ:")
        if all_critical_tests_passed:
            self.log("✅ ВСЕ КРИТИЧЕСКИЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            self.log("🎉 API placement-status возвращает полную информацию для модального окна")
            self.log("📊 Данные содержат реальную информацию, а не 'Не указан'")
            self.log("🏗️ Lookup данных из коллекций users и warehouses работает корректно")
        else:
            self.log("❌ КРИТИЧЕСКИЕ ТЕСТЫ НЕ ПРОЙДЕНЫ!")
            self.log("🔍 Требуется дополнительная доработка API placement-status")
            if not self.test_results["required_fields_present"]:
                self.log("⚠️ Отсутствуют обязательные поля для модального окна")
            if not self.test_results["data_quality_good"]:
                self.log("⚠️ Качество данных недостаточное - много 'Не указан' значений")
        
        return all_critical_tests_passed
    
    def run_placement_status_test(self):
        """Запуск полного теста API placement-status"""
        self.log("🚀 ЗАПУСК ТЕСТИРОВАНИЯ API placement-status")
        self.log("="*80)
        
        # 1. Авторизация
        if not self.authenticate_warehouse_operator():
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Не удалось авторизоваться", "ERROR")
            return False
        
        # 2. Получение доступных заявок
        applications = self.get_available_applications()
        if not applications:
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Нет доступных заявок", "ERROR")
            return False
        
        if len(applications) == 0:
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Список заявок пуст", "ERROR")
            return False
        
        # 3. Тестирование первой доступной заявки
        self.log(f"🎯 Выбрана первая доступная заявка из {len(applications)} для тестирования")
        first_application = applications[0]
        
        success = self.test_single_application(first_application)
        
        # 4. Генерация финального отчета
        final_success = self.generate_final_report()
        
        return final_success

def main():
    """Главная функция"""
    tester = PlacementStatusAPITester()
    
    try:
        success = tester.run_placement_status_test()
        
        if success:
            print("\n" + "="*80)
            print("🎉 ТЕСТИРОВАНИЕ API placement-status ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ API возвращает полную информацию для модального окна")
            print("📊 Данные содержат реальную информацию о городах, складах и операторах")
            print("🏗️ Lookup данных из коллекций users и warehouses работает корректно")
            sys.exit(0)
        else:
            print("\n" + "="*80)
            print("❌ ТЕСТИРОВАНИЕ API placement-status НЕ ПРОЙДЕНО!")
            print("🔍 API не возвращает достаточно информации для модального окна")
            print("⚠️ Требуется доработка lookup данных и fallback значений")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
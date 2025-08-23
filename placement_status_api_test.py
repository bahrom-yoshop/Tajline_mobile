#!/usr/bin/env python3
"""
ПОВТОРНОЕ ТЕСТИРОВАНИЕ УЛУЧШЕННОГО API placement-status
======================================================

ЦЕЛЬ: Проверить что после улучшений API возвращает качественные данные для модального окна

КРИТИЧЕСКИЕ ПРОВЕРКИ:
1. Авторизация оператора склада (+79777888999/warehouse123)
2. Тестирование API placement-status для любой доступной заявки:
   - Проверить delivery_city, pickup_city - должны содержать реальные города (не "Не указан")
   - Проверить source_warehouse_name, accepting_warehouse - должны содержать названия складов
   - Проверить target_warehouse_name, delivery_warehouse - должны содержать названия складов выдачи
   - Проверить operator_full_name, operator_phone - должны содержать информацию об операторе
3. Качество данных: Убедиться что минимум 75% полей содержат реальную информацию (не "Не указан")

УЛУЧШЕНИЯ:
- Парсинг городов из адресов sender_address и recipient_address
- Использование данных текущего оператора для заполнения operator_full_name
- Fallback значения по умолчанию: Москва (приём), Душанбе (выдача)
- Lookup данных из коллекций users и warehouses

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Значительное улучшение качества данных для корректного отображения в модальном окне.
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

class PlacementStatusAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.test_results = {
            "auth_success": False,
            "applications_found": False,
            "api_accessible": False,
            "data_quality_good": False,
            "quality_percentage": 0.0,
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
        self.log(f"🎯 Тестирование API placement-status для заявки {cargo_number}...")
        
        try:
            response = self.session.get(f"{API_BASE}/operator/cargo/{cargo_id}/placement-status")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ API placement-status доступен и возвращает данные ({len(data)} полей)")
                self.test_results["api_accessible"] = True
                return data
            else:
                self.log(f"❌ Ошибка API placement-status: {response.status_code} - {response.text}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Исключение при тестировании API: {e}", "ERROR")
            return None
    
    def analyze_data_quality(self, placement_data, cargo_number):
        """Анализ качества данных в ответе API"""
        self.log(f"\n🔍 АНАЛИЗ КАЧЕСТВА ДАННЫХ ДЛЯ ЗАЯВКИ {cargo_number}:")
        self.log("=" * 60)
        
        # Критические поля для проверки
        critical_fields = {
            "delivery_city": "Город выдачи",
            "pickup_city": "Город приёма", 
            "source_warehouse_name": "Название склада приёма",
            "accepting_warehouse": "Принимающий склад",
            "target_warehouse_name": "Название целевого склада",
            "delivery_warehouse": "Склад выдачи",
            "operator_full_name": "ФИО оператора",
            "operator_phone": "Телефон оператора"
        }
        
        quality_results = {}
        good_fields = 0
        total_fields = len(critical_fields)
        
        self.log("📊 ПРОВЕРКА КРИТИЧЕСКИХ ПОЛЕЙ:")
        
        for field, description in critical_fields.items():
            value = placement_data.get(field, "")
            is_good = value and value != "Не указан" and value != "Неизвестно" and value != "Неизвестный оператор"
            
            if is_good:
                good_fields += 1
                status = "✅"
                quality_results[field] = {"value": value, "quality": "good"}
            else:
                status = "⚠️"
                quality_results[field] = {"value": value, "quality": "poor"}
            
            self.log(f"  {status} {description}: '{value}'")
        
        # Расчет процента качества
        quality_percentage = (good_fields / total_fields) * 100
        
        self.log(f"\n📈 РЕЗУЛЬТАТЫ АНАЛИЗА КАЧЕСТВА:")
        self.log(f"  Хорошие поля: {good_fields}/{total_fields}")
        self.log(f"  Процент качества: {quality_percentage:.1f}%")
        self.log(f"  Требуемый минимум: 75.0%")
        
        quality_good = quality_percentage >= 75.0
        
        if quality_good:
            self.log(f"  ✅ КАЧЕСТВО ДАННЫХ СООТВЕТСТВУЕТ ТРЕБОВАНИЯМ!")
        else:
            self.log(f"  ❌ КАЧЕСТВО ДАННЫХ НЕДОСТАТОЧНОЕ!")
        
        return {
            "quality_percentage": quality_percentage,
            "good_fields": good_fields,
            "total_fields": total_fields,
            "quality_good": quality_good,
            "field_analysis": quality_results
        }
    
    def check_data_improvements(self, placement_data):
        """Проверка улучшений в данных"""
        self.log(f"\n🔧 ПРОВЕРКА УЛУЧШЕНИЙ В ДАННЫХ:")
        self.log("-" * 40)
        
        improvements_found = []
        
        # Проверка парсинга городов из адресов
        sender_address = placement_data.get("sender_address", "")
        recipient_address = placement_data.get("recipient_address", "")
        pickup_city = placement_data.get("pickup_city", "")
        delivery_city = placement_data.get("delivery_city", "")
        
        if sender_address and pickup_city != "Не указан":
            improvements_found.append("✅ Парсинг города из sender_address работает")
            self.log(f"  ✅ Город приёма определён из адреса: '{pickup_city}' (из '{sender_address}')")
        
        if recipient_address and delivery_city != "Не указан":
            improvements_found.append("✅ Парсинг города из recipient_address работает")
            self.log(f"  ✅ Город выдачи определён из адреса: '{delivery_city}' (из '{recipient_address}')")
        
        # Проверка использования данных оператора
        operator_full_name = placement_data.get("operator_full_name", "")
        operator_phone = placement_data.get("operator_phone", "")
        
        if operator_full_name and operator_full_name != "Неизвестный оператор":
            improvements_found.append("✅ Данные оператора используются корректно")
            self.log(f"  ✅ ФИО оператора заполнено: '{operator_full_name}'")
        
        if operator_phone and operator_phone != "Не указан":
            improvements_found.append("✅ Телефон оператора заполнен")
            self.log(f"  ✅ Телефон оператора заполнен: '{operator_phone}'")
        
        # Проверка fallback значений
        if pickup_city == "Москва" or delivery_city == "Душанбе":
            improvements_found.append("✅ Fallback значения применяются")
            self.log(f"  ✅ Fallback значения: pickup_city='{pickup_city}', delivery_city='{delivery_city}'")
        
        # Проверка lookup данных складов
        source_warehouse = placement_data.get("source_warehouse_name", "")
        target_warehouse = placement_data.get("target_warehouse_name", "")
        
        if source_warehouse and source_warehouse != "Не указан":
            improvements_found.append("✅ Lookup данных складов работает")
            self.log(f"  ✅ Склад приёма найден: '{source_warehouse}'")
        
        if target_warehouse and target_warehouse != "Не указан":
            self.log(f"  ✅ Целевой склад найден: '{target_warehouse}'")
        
        self.log(f"\n📊 НАЙДЕНО УЛУЧШЕНИЙ: {len(improvements_found)}")
        for improvement in improvements_found:
            self.log(f"  {improvement}")
        
        return improvements_found
    
    def generate_final_report(self, cargo_number, quality_analysis, improvements):
        """Генерация финального отчета"""
        self.log("\n📋 ФИНАЛЬНЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ API placement-status:")
        self.log("=" * 80)
        
        # Заголовок
        self.log(f"🎯 ПОВТОРНОЕ ТЕСТИРОВАНИЕ УЛУЧШЕННОГО API placement-status")
        self.log(f"📅 Время тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"🎯 Тестируемая заявка: {cargo_number}")
        
        # Результаты по этапам
        self.log(f"\n📊 РЕЗУЛЬТАТЫ ПО ЭТАПАМ:")
        self.log(f"  1. ✅ Авторизация оператора склада: {'✅ УСПЕШНО' if self.test_results['auth_success'] else '❌ НЕУДАЧНО'}")
        self.log(f"  2. ✅ Получение доступных заявок: {'✅ УСПЕШНО' if self.test_results['applications_found'] else '❌ НЕУДАЧНО'}")
        self.log(f"  3. ✅ Доступность API placement-status: {'✅ УСПЕШНО' if self.test_results['api_accessible'] else '❌ НЕУДАЧНО'}")
        self.log(f"  4. 🎯 Качество данных (≥75%): {'✅ СООТВЕТСТВУЕТ' if self.test_results['data_quality_good'] else '❌ НЕДОСТАТОЧНО'}")
        
        # Детальные результаты качества
        if quality_analysis:
            self.log(f"\n📊 ДЕТАЛЬНЫЙ АНАЛИЗ КАЧЕСТВА ДАННЫХ:")
            self.log(f"  Процент качества: {quality_analysis['quality_percentage']:.1f}%")
            self.log(f"  Хорошие поля: {quality_analysis['good_fields']}/{quality_analysis['total_fields']}")
            self.log(f"  Требуемый минимум: 75.0%")
            
            # Анализ по полям
            self.log(f"\n📋 АНАЛИЗ ПО ПОЛЯМ:")
            for field, analysis in quality_analysis['field_analysis'].items():
                status = "✅" if analysis['quality'] == 'good' else "⚠️"
                self.log(f"  {status} {field}: '{analysis['value']}'")
        
        # Найденные улучшения
        if improvements:
            self.log(f"\n🔧 НАЙДЕННЫЕ УЛУЧШЕНИЯ ({len(improvements)} шт.):")
            for improvement in improvements:
                self.log(f"  {improvement}")
        
        # Финальный вывод
        self.log(f"\n🎯 ФИНАЛЬНЫЙ РЕЗУЛЬТАТ:")
        if self.test_results["data_quality_good"]:
            self.log("✅ API placement-status ВОЗВРАЩАЕТ КАЧЕСТВЕННЫЕ ДАННЫЕ!")
            self.log("🎉 Улучшения успешно применены и работают корректно")
            self.log("📊 Качество данных соответствует требованиям (≥75%)")
            self.log("🎯 Модальное окно будет отображать корректную информацию")
        else:
            self.log("❌ КАЧЕСТВО ДАННЫХ API placement-status НЕДОСТАТОЧНОЕ!")
            self.log(f"🔍 Текущее качество: {self.test_results['quality_percentage']:.1f}% (требуется ≥75%)")
            self.log("⚠️ Требуется дополнительная доработка lookup логики")
        
        return self.test_results["data_quality_good"]
    
    def run_placement_status_test(self):
        """Запуск полного теста API placement-status"""
        self.log("🚀 ЗАПУСК ПОВТОРНОГО ТЕСТИРОВАНИЯ УЛУЧШЕННОГО API placement-status")
        self.log("=" * 80)
        
        # 1. Авторизация
        if not self.authenticate_warehouse_operator():
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Не удалось авторизоваться", "ERROR")
            return False
        
        # 2. Получение доступных заявок
        applications = self.get_available_applications()
        if not applications:
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Нет доступных заявок", "ERROR")
            return False
        
        # 3. Выбираем первую доступную заявку для тестирования
        test_application = applications[0]
        cargo_id = test_application.get("id")
        cargo_number = test_application.get("cargo_number")
        
        if not cargo_id or not cargo_number:
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Некорректные данные заявки", "ERROR")
            return False
        
        self.log(f"🎯 Выбрана заявка для тестирования: {cargo_number} (ID: {cargo_id})")
        
        # 4. Тестирование API placement-status
        placement_data = self.test_placement_status_api(cargo_id, cargo_number)
        if not placement_data:
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: API placement-status недоступен", "ERROR")
            return False
        
        # 5. Анализ качества данных
        quality_analysis = self.analyze_data_quality(placement_data, cargo_number)
        self.test_results["data_quality_good"] = quality_analysis["quality_good"]
        self.test_results["quality_percentage"] = quality_analysis["quality_percentage"]
        self.test_results["detailed_results"] = quality_analysis
        
        # 6. Проверка улучшений
        improvements = self.check_data_improvements(placement_data)
        
        # 7. Генерация финального отчета
        final_success = self.generate_final_report(cargo_number, quality_analysis, improvements)
        
        return final_success

def main():
    """Главная функция"""
    tester = PlacementStatusAPITester()
    
    try:
        success = tester.run_placement_status_test()
        
        if success:
            print("\n" + "="*80)
            print("🎉 ПОВТОРНОЕ ТЕСТИРОВАНИЕ API placement-status ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ API возвращает качественные данные для модального окна")
            print("📊 Качество данных соответствует требованиям (≥75%)")
            print("🎯 Улучшения успешно применены и работают корректно")
            sys.exit(0)
        else:
            print("\n" + "="*80)
            print("❌ ПОВТОРНОЕ ТЕСТИРОВАНИЕ API placement-status НЕ ПРОЙДЕНО!")
            print("🔍 Качество данных недостаточное для корректного отображения")
            print("⚠️ Требуется дополнительная доработка lookup логики")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
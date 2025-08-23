#!/usr/bin/env python3
"""
КРИТИЧЕСКАЯ ДИАГНОСТИКА API layout-with-cargo: Почему не находит 4 размещенных единицы
====================================================================================

НАЙДЕННЫЕ ДАННЫЕ ИЗ ПРЕДЫДУЩЕЙ ДИАГНОСТИКИ:
- В placement_records найдено 4 записи для склада 001 (d0a8362d-b4d3-4947-b335-28c94658a021)
- Заявка 250101: 1 единица (250101/01/02 в Б1-П2-Я5)
- Заявка 25082235: 3 единицы (25082235/01/02, 25082235/02/01, 25082235/01/01)
- Заявка 25082298: 0 единиц (НЕ НАЙДЕНА)

ЦЕЛЬ: Понять почему API layout-with-cargo возвращает 0 записей вместо 4 найденных

КРИТИЧЕСКИЕ ПРОВЕРКИ:
1. Тестирование API layout-with-cargo для склада 001
2. Анализ логики поиска в API
3. Сравнение данных из placement_records с ответом API
4. Поиск проблем в фильтрации или обработке данных
"""

import requests
import json
import sys
import os
from datetime import datetime
from pymongo import MongoClient

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cargo-sync.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# MongoDB конфигурация
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'cargo_transport')

# Конфигурация
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"

# Данные из предыдущей диагностики
MOSCOW_WAREHOUSE_ID = "d0a8362d-b4d3-4947-b335-28c94658a021"
MOSCOW_WAREHOUSE_NAME = "Москва Склад №1"
MOSCOW_WAREHOUSE_NUMBER = "001"

FOUND_PLACEMENT_RECORDS = [
    {"cargo_number": "250101", "individual_number": "250101/01/02", "location": "Б1-П2-Я5"},
    {"cargo_number": "25082235", "individual_number": "25082235/01/02", "location": "Б1-П3-Я2"},
    {"cargo_number": "25082235", "individual_number": "25082235/02/01", "location": "Б1-П3-Я2"},
    {"cargo_number": "25082235", "individual_number": "25082235/01/01", "location": "Б1-П3-Я3"}
]

class LayoutWithCargoAPIDiagnosticTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.mongo_client = None
        self.db = None
        self.test_results = {
            "auth_success": False,
            "api_response_received": False,
            "api_cargo_count": 0,
            "expected_cargo_count": 4,
            "placement_records_in_db": 0,
            "api_vs_db_mismatch": False,
            "critical_issues": []
        }
        
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
                    self.test_results["auth_success"] = True
                    self.log(f"✅ Успешная авторизация: {self.operator_info.get('full_name')} (роль: {self.operator_info.get('role')})")
                    return True
                else:
                    self.log(f"❌ Ошибка получения информации о пользователе: {user_response.status_code}")
                    return False
            else:
                self.log(f"❌ Ошибка авторизации: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при авторизации: {str(e)}", "ERROR")
            return False
    
    def connect_to_mongodb(self):
        """Подключение к MongoDB"""
        try:
            self.log("🔌 Подключение к MongoDB...")
            
            self.mongo_client = MongoClient(MONGO_URL)
            self.db = self.mongo_client[DB_NAME]
            
            # Проверяем подключение
            self.mongo_client.admin.command('ping')
            self.log("✅ Успешное подключение к MongoDB")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Ошибка подключения к MongoDB: {str(e)}", "ERROR")
            return False
    
    def verify_placement_records_in_db(self):
        """Проверка placement_records в базе данных"""
        try:
            self.log("🔍 Проверка placement_records в базе данных...")
            
            placement_collection = self.db['placement_records']
            
            # Поиск записей для склада 001
            moscow_records = list(placement_collection.find({
                "warehouse_id": MOSCOW_WAREHOUSE_ID
            }))
            
            self.test_results["placement_records_in_db"] = len(moscow_records)
            self.log(f"📊 Найдено {len(moscow_records)} placement_records для склада 001 в базе данных")
            
            for record in moscow_records:
                cargo_number = record.get('cargo_number', 'N/A')
                individual_number = record.get('individual_number', 'N/A')
                location = record.get('location', 'N/A')
                placed_at = record.get('placed_at', 'N/A')
                placed_by = record.get('placed_by', 'N/A')
                
                self.log(f"   - {cargo_number}/{individual_number} в {location} (размещен: {placed_at}, кем: {placed_by})")
            
            return moscow_records
            
        except Exception as e:
            self.log(f"❌ Ошибка проверки placement_records: {str(e)}", "ERROR")
            return []
    
    def test_layout_with_cargo_api(self):
        """Тестирование API layout-with-cargo"""
        try:
            self.log("🧪 ТЕСТИРОВАНИЕ API layout-with-cargo...")
            self.log(f"📍 Склад: {MOSCOW_WAREHOUSE_NAME} (ID: {MOSCOW_WAREHOUSE_ID})")
            
            # Вызов API
            api_url = f"{API_BASE}/warehouses/{MOSCOW_WAREHOUSE_ID}/layout-with-cargo"
            self.log(f"🌐 URL: {api_url}")
            
            response = self.session.get(api_url)
            
            if response.status_code == 200:
                self.test_results["api_response_received"] = True
                data = response.json()
                
                self.log("✅ API ответил успешно")
                self.log(f"📋 Структура ответа: {list(data.keys())}")
                
                # Анализ cargo_info
                cargo_info = data.get('cargo_info', [])
                self.test_results["api_cargo_count"] = len(cargo_info)
                
                self.log(f"📦 API вернул {len(cargo_info)} записей cargo_info")
                
                if len(cargo_info) == 0:
                    self.log("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: API возвращает пустой cargo_info")
                    self.test_results["critical_issues"].append("API layout-with-cargo возвращает пустой cargo_info")
                else:
                    self.log("✅ API возвращает данные в cargo_info:")
                    for i, cargo in enumerate(cargo_info):
                        cargo_number = cargo.get('cargo_number', 'N/A')
                        individual_number = cargo.get('individual_number', 'N/A')
                        location = cargo.get('location', 'N/A')
                        self.log(f"   {i+1}. {cargo_number}/{individual_number} в {location}")
                
                # Анализ других полей
                layout_structure = data.get('layout_structure', {})
                warehouse_info = data.get('warehouse_info', {})
                
                self.log(f"🏗️ Layout structure: {len(layout_structure.get('blocks', []))} блоков")
                self.log(f"🏢 Warehouse info: {warehouse_info.get('name', 'N/A')}")
                
                return data
                
            else:
                self.log(f"❌ Ошибка API: {response.status_code}")
                self.log(f"❌ Ответ: {response.text}")
                self.test_results["critical_issues"].append(f"API layout-with-cargo вернул ошибку {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"❌ Ошибка тестирования API: {str(e)}", "ERROR")
            return None
    
    def analyze_api_logic_issue(self, placement_records):
        """Анализ проблемы в логике API"""
        try:
            self.log("\n🔍 АНАЛИЗ ПРОБЛЕМЫ В ЛОГИКЕ API...")
            
            # Сравнение данных
            db_count = len(placement_records)
            api_count = self.test_results["api_cargo_count"]
            
            self.log(f"📊 База данных: {db_count} записей")
            self.log(f"📊 API ответ: {api_count} записей")
            
            if db_count > api_count:
                self.test_results["api_vs_db_mismatch"] = True
                self.log(f"❌ НЕСООТВЕТСТВИЕ: API возвращает меньше записей чем в базе данных")
                self.test_results["critical_issues"].append(f"API возвращает {api_count} записей, а в БД {db_count}")
                
                # Анализ возможных причин
                self.log("\n🔍 ВОЗМОЖНЫЕ ПРИЧИНЫ ПРОБЛЕМЫ:")
                
                # 1. Проблема с фильтрацией по warehouse_id
                self.log("1. 🔧 Проверка фильтрации по warehouse_id:")
                self.log(f"   - Ожидаемый warehouse_id: {MOSCOW_WAREHOUSE_ID}")
                self.log(f"   - Возможно API ищет по другому полю (warehouse_id_number: {MOSCOW_WAREHOUSE_NUMBER})")
                
                # 2. Проблема с JOIN операциями
                self.log("2. 🔧 Проблема с JOIN операциями:")
                self.log("   - API может не находить связанные данные из других коллекций")
                self.log("   - Проверить связи между placement_records и cargo/operator_cargo")
                
                # 3. Проблема с форматом данных
                self.log("3. 🔧 Проблема с форматом данных:")
                self.log("   - Формат location: Б1-П2-Я5 (найден в БД)")
                self.log("   - API может ожидать другой формат")
                
                # 4. Проблема с активностью записей
                self.log("4. 🔧 Проблема с фильтрацией активных записей:")
                self.log("   - API может фильтровать по статусу или флагам активности")
                
            elif db_count == api_count:
                self.log("✅ Количество записей совпадает")
            else:
                self.log("⚠️ API возвращает больше записей чем в БД (возможно из других источников)")
                
        except Exception as e:
            self.log(f"❌ Ошибка анализа логики API: {str(e)}", "ERROR")
    
    def test_alternative_warehouse_search(self):
        """Тестирование поиска по альтернативным критериям"""
        try:
            self.log("\n🔍 ТЕСТИРОВАНИЕ АЛЬТЕРНАТИВНЫХ КРИТЕРИЕВ ПОИСКА...")
            
            # Тест 1: Поиск по warehouse_id_number
            self.log("1. 🧪 Тест поиска по warehouse_id_number...")
            
            placement_collection = self.db['placement_records']
            
            # Поиск записей с warehouse_id_number
            records_by_number = list(placement_collection.find({
                "warehouse_id_number": MOSCOW_WAREHOUSE_NUMBER
            }))
            
            self.log(f"   📊 Найдено {len(records_by_number)} записей по warehouse_id_number = '{MOSCOW_WAREHOUSE_NUMBER}'")
            
            # Тест 2: Поиск по названию склада
            self.log("2. 🧪 Тест поиска по названию склада...")
            
            records_by_name = list(placement_collection.find({
                "warehouse_name": {"$regex": "Москва", "$options": "i"}
            }))
            
            self.log(f"   📊 Найдено {len(records_by_name)} записей по названию склада содержащему 'Москва'")
            
            # Тест 3: Поиск всех записей и анализ warehouse_id
            self.log("3. 🧪 Анализ всех warehouse_id в placement_records...")
            
            all_records = list(placement_collection.find({}))
            warehouse_ids = set()
            
            for record in all_records:
                warehouse_id = record.get('warehouse_id')
                if warehouse_id:
                    warehouse_ids.add(warehouse_id)
            
            self.log(f"   📊 Найдено {len(warehouse_ids)} уникальных warehouse_id:")
            for wid in warehouse_ids:
                count = placement_collection.count_documents({"warehouse_id": wid})
                self.log(f"      - {wid}: {count} записей")
                
                # Проверяем, это ли наш склад
                if wid == MOSCOW_WAREHOUSE_ID:
                    self.log(f"      ✅ ЭТО НАШ СКЛАД 001!")
                    
        except Exception as e:
            self.log(f"❌ Ошибка тестирования альтернативного поиска: {str(e)}", "ERROR")
    
    def run_comprehensive_diagnosis(self):
        """Запуск полной диагностики API"""
        try:
            self.log("🚀 ЗАПУСК ДИАГНОСТИКИ API layout-with-cargo")
            self.log("=" * 80)
            
            # 1. Авторизация
            if not self.authenticate_operator():
                self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться")
                return False
            
            # 2. Подключение к MongoDB
            if not self.connect_to_mongodb():
                self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось подключиться к MongoDB")
                return False
            
            # 3. Проверка placement_records в БД
            placement_records = self.verify_placement_records_in_db()
            
            # 4. Тестирование API layout-with-cargo
            api_response = self.test_layout_with_cargo_api()
            
            # 5. Анализ проблемы в логике API
            self.analyze_api_logic_issue(placement_records)
            
            # 6. Тестирование альтернативных критериев поиска
            self.test_alternative_warehouse_search()
            
            # 7. Финальный отчет
            self.generate_final_report()
            
            return True
            
        except Exception as e:
            self.log(f"❌ КРИТИЧЕСКАЯ ОШИБКА диагностики: {str(e)}", "ERROR")
            return False
        finally:
            if self.mongo_client:
                self.mongo_client.close()
    
    def generate_final_report(self):
        """Генерация финального отчета диагностики"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 ФИНАЛЬНЫЙ ОТЧЕТ ДИАГНОСТИКИ API layout-with-cargo")
            self.log("=" * 80)
            
            # Статистика
            self.log(f"✅ Авторизация: {'УСПЕШНО' if self.test_results['auth_success'] else 'ОШИБКА'}")
            self.log(f"✅ API ответ получен: {'ДА' if self.test_results['api_response_received'] else 'НЕТ'}")
            self.log(f"📊 Записей в БД: {self.test_results['placement_records_in_db']}")
            self.log(f"📊 Записей в API: {self.test_results['api_cargo_count']}")
            self.log(f"📊 Ожидалось: {self.test_results['expected_cargo_count']}")
            
            # Проблема
            if self.test_results["api_vs_db_mismatch"]:
                self.log(f"\n❌ КРИТИЧЕСКАЯ ПРОБЛЕМА ПОДТВЕРЖДЕНА:")
                self.log(f"   API layout-with-cargo возвращает {self.test_results['api_cargo_count']} записей")
                self.log(f"   В базе данных найдено {self.test_results['placement_records_in_db']} записей")
                self.log(f"   Пользователь ожидал {self.test_results['expected_cargo_count']} записей")
            
            # Критические проблемы
            if self.test_results["critical_issues"]:
                self.log(f"\n🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ ({len(self.test_results['critical_issues'])}):")
                for issue in self.test_results["critical_issues"]:
                    self.log(f"❌ {issue}")
            
            # Рекомендации по исправлению
            self.log(f"\n💡 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ:")
            
            if self.test_results["api_cargo_count"] == 0 and self.test_results["placement_records_in_db"] > 0:
                self.log("🔧 1. КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: API не находит записи из placement_records")
                self.log("🔧 2. Проверить логику JOIN между placement_records и другими коллекциями")
                self.log("🔧 3. Убедиться что API правильно фильтрует по warehouse_id")
                self.log("🔧 4. Проверить формат данных в placement_records")
                self.log("🔧 5. Добавить логирование в API для отладки")
            
            # Успешность диагностики
            if self.test_results["api_cargo_count"] == self.test_results["expected_cargo_count"]:
                success_rate = 100.0
                self.log(f"\n📊 УСПЕШНОСТЬ: {success_rate}% - ВСЕ ЗАПИСИ НАЙДЕНЫ")
            else:
                success_rate = (self.test_results["api_cargo_count"] / self.test_results["expected_cargo_count"]) * 100
                self.log(f"\n📊 УСПЕШНОСТЬ: {success_rate:.1f}% - ПРОБЛЕМА ПОДТВЕРЖДЕНА")
            
            # Следующие шаги
            self.log(f"\n🎯 СЛЕДУЮЩИЕ ШАГИ:")
            self.log("1. Исправить логику API layout-with-cargo")
            self.log("2. Добавить поддержку поиска по всем форматам warehouse_id")
            self.log("3. Протестировать исправления")
            self.log("4. Убедиться что все 13 ожидаемых единиц найдены")
                
        except Exception as e:
            self.log(f"❌ Ошибка генерации отчета: {str(e)}", "ERROR")

def main():
    """Главная функция"""
    print("🚀 ДИАГНОСТИКА API layout-with-cargo: Поиск причины проблемы")
    print("=" * 80)
    
    tester = LayoutWithCargoAPIDiagnosticTester()
    
    try:
        success = tester.run_comprehensive_diagnosis()
        
        if success:
            print("\n✅ ДИАГНОСТИКА ЗАВЕРШЕНА")
        else:
            print("\n❌ ДИАГНОСТИКА ЗАВЕРШЕНА С ОШИБКАМИ")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ ДИАГНОСТИКА ПРЕРВАНА ПОЛЬЗОВАТЕЛЕМ")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
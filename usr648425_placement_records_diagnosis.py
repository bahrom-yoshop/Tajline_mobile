#!/usr/bin/env python3
"""
КРИТИЧЕСКАЯ ДИАГНОСТИКА: Поиск всех 13 placement_records размещенных оператором USR648425
========================================================================================

ЦЕЛЬ: Найти ВСЕ 13 placement_records, которые были размещены оператором USR648425, 
но не отображаются в API

КРИТИЧЕСКИЕ ПРОВЕРКИ:
1. Авторизация оператора (+79777888999/warehouse123)
2. Поиск по оператору USR648425:
   - Найти все placement_records с placed_by_operator = "USR648425"
   - Найти все placement_records с placed_by = "USR648425"
   - Проанализировать какие warehouse_id используются для этого оператора
3. Поиск по заявкам:
   - 25082298 (ожидается 7 единиц)
   - 250101 (ожидается 2 единицы)  
   - 25082235 (ожидается 4 единицы)
4. Анализ проблемы фильтрации: Почему API находит только 4 из 13 записей
5. Проверка других коллекций: operator_cargo, cargo - возможно данные там

ПРОБЛЕМА: Пользователь подтверждает что оператор USR648425 размещал все 13 единиц, 
но API находит только 4

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Найти все 13 placement_records и определить почему API их не находит 
при фильтрации по warehouse_id
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

# Конфигурация
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"
TARGET_OPERATOR = "USR648425"
EXPECTED_APPLICATIONS = {
    "25082298": 7,  # ожидается 7 единиц
    "250101": 2,    # ожидается 2 единицы
    "25082235": 4   # ожидается 4 единицы
}

class USR648425PlacementDiagnostic:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.mongo_client = None
        self.db = None
        self.test_results = {
            "auth_success": False,
            "mongo_connection": False,
            "placement_records_found": 0,
            "expected_total": 13,
            "applications_analysis": {},
            "warehouse_analysis": {},
            "api_filtering_issue": None,
            "missing_records": []
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
    
    def connect_to_mongodb(self):
        """Подключение к MongoDB для прямого анализа данных"""
        self.log("🔌 Подключение к MongoDB...")
        
        try:
            # Используем локальное подключение к MongoDB
            MONGO_URL = "mongodb://localhost:27017"
            DB_NAME = "cargo_transport"
            
            self.mongo_client = MongoClient(MONGO_URL)
            self.db = self.mongo_client[DB_NAME]
            
            # Проверяем подключение
            collections = self.db.list_collection_names()
            self.log(f"✅ Подключение к MongoDB успешно. Найдено {len(collections)} коллекций")
            self.test_results["mongo_connection"] = True
            return True
            
        except Exception as e:
            self.log(f"❌ Ошибка подключения к MongoDB: {e}", "ERROR")
            return False
    
    def search_placement_records_by_operator(self):
        """Поиск всех placement_records размещенных оператором USR648425"""
        self.log(f"🔍 Поиск placement_records для оператора {TARGET_OPERATOR}...")
        
        try:
            # Поиск по различным полям оператора
            search_queries = [
                {"placed_by_operator": TARGET_OPERATOR},
                {"placed_by": TARGET_OPERATOR},
                {"operator_id": TARGET_OPERATOR},
                {"placed_by_operator_id": TARGET_OPERATOR}
            ]
            
            all_records = []
            unique_records = set()
            
            for query in search_queries:
                self.log(f"  🔍 Поиск по запросу: {query}")
                records = list(self.db.placement_records.find(query, {"_id": 0}))
                
                for record in records:
                    record_id = record.get("id", "unknown")
                    if record_id not in unique_records:
                        unique_records.add(record_id)
                        all_records.append(record)
                
                self.log(f"    Найдено записей: {len(records)}")
            
            self.log(f"✅ Всего уникальных placement_records найдено: {len(all_records)}")
            self.test_results["placement_records_found"] = len(all_records)
            
            # Анализ найденных записей
            if all_records:
                self.log("\n📋 ДЕТАЛЬНЫЙ АНАЛИЗ НАЙДЕННЫХ PLACEMENT_RECORDS:")
                self.log("=" * 80)
                
                warehouse_stats = {}
                application_stats = {}
                
                for i, record in enumerate(all_records, 1):
                    cargo_number = record.get("cargo_number", "N/A")
                    individual_number = record.get("individual_number", "N/A")
                    warehouse_id = record.get("warehouse_id", "N/A")
                    placed_at = record.get("placed_at", "N/A")
                    location = record.get("location", "N/A")
                    
                    self.log(f"  {i}. Заявка: {cargo_number}, Единица: {individual_number}")
                    self.log(f"     Склад: {warehouse_id}, Размещено: {placed_at}")
                    self.log(f"     Местоположение: {location}")
                    
                    # Статистика по складам
                    if warehouse_id not in warehouse_stats:
                        warehouse_stats[warehouse_id] = 0
                    warehouse_stats[warehouse_id] += 1
                    
                    # Статистика по заявкам
                    if cargo_number not in application_stats:
                        application_stats[cargo_number] = 0
                    application_stats[cargo_number] += 1
                
                self.test_results["warehouse_analysis"] = warehouse_stats
                self.test_results["applications_analysis"] = application_stats
                
                self.log(f"\n📊 СТАТИСТИКА ПО СКЛАДАМ:")
                for warehouse_id, count in warehouse_stats.items():
                    self.log(f"  Склад {warehouse_id}: {count} единиц")
                
                self.log(f"\n📊 СТАТИСТИКА ПО ЗАЯВКАМ:")
                for app_number, count in application_stats.items():
                    expected = EXPECTED_APPLICATIONS.get(app_number, "неизвестно")
                    status = "✅" if expected != "неизвестно" and count == expected else "⚠️"
                    self.log(f"  {status} Заявка {app_number}: {count} единиц (ожидалось: {expected})")
            
            return all_records
            
        except Exception as e:
            self.log(f"❌ Ошибка поиска placement_records: {e}", "ERROR")
            return []
    
    def search_by_specific_applications(self):
        """Поиск по конкретным заявкам"""
        self.log(f"\n🎯 ПОИСК ПО КОНКРЕТНЫМ ЗАЯВКАМ:")
        self.log("=" * 50)
        
        try:
            total_found = 0
            missing_applications = []
            
            for app_number, expected_count in EXPECTED_APPLICATIONS.items():
                self.log(f"\n🔍 Поиск заявки {app_number} (ожидается {expected_count} единиц)...")
                
                # Поиск в placement_records
                placement_records = list(self.db.placement_records.find({
                    "cargo_number": app_number,
                    "$or": [
                        {"placed_by_operator": TARGET_OPERATOR},
                        {"placed_by": TARGET_OPERATOR},
                        {"operator_id": TARGET_OPERATOR},
                        {"placed_by_operator_id": TARGET_OPERATOR}
                    ]
                }, {"_id": 0}))
                
                found_count = len(placement_records)
                total_found += found_count
                
                if found_count > 0:
                    self.log(f"  ✅ Найдено {found_count} единиц в placement_records")
                    for record in placement_records:
                        individual_number = record.get("individual_number", "N/A")
                        warehouse_id = record.get("warehouse_id", "N/A")
                        location = record.get("location", "N/A")
                        self.log(f"    - {individual_number} (склад: {warehouse_id}, место: {location})")
                else:
                    self.log(f"  ❌ НЕ найдено единиц в placement_records")
                
                # Проверка в других коллекциях
                self.log(f"  🔍 Проверка в коллекции operator_cargo...")
                operator_cargo = self.db.operator_cargo.find_one({"cargo_number": app_number})
                if operator_cargo:
                    individual_items = operator_cargo.get("individual_items", [])
                    placed_items = [item for item in individual_items if item.get("is_placed", False)]
                    self.log(f"    operator_cargo: {len(individual_items)} единиц, {len(placed_items)} размещено")
                else:
                    self.log(f"    operator_cargo: заявка НЕ найдена")
                
                self.log(f"  🔍 Проверка в коллекции cargo...")
                cargo = self.db.cargo.find_one({"cargo_number": app_number})
                if cargo:
                    individual_items = cargo.get("individual_items", [])
                    placed_items = [item for item in individual_items if item.get("is_placed", False)]
                    self.log(f"    cargo: {len(individual_items)} единиц, {len(placed_items)} размещено")
                else:
                    self.log(f"    cargo: заявка НЕ найдена")
                
                # Анализ расхождений
                if found_count != expected_count:
                    missing_count = expected_count - found_count
                    missing_applications.append({
                        "application": app_number,
                        "expected": expected_count,
                        "found": found_count,
                        "missing": missing_count
                    })
                    self.log(f"  ⚠️ РАСХОЖДЕНИЕ: ожидалось {expected_count}, найдено {found_count}, недостает {missing_count}")
            
            self.test_results["missing_records"] = missing_applications
            
            self.log(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
            self.log(f"  Всего найдено единиц: {total_found}")
            self.log(f"  Ожидалось единиц: {sum(EXPECTED_APPLICATIONS.values())}")
            self.log(f"  Недостает единиц: {sum(EXPECTED_APPLICATIONS.values()) - total_found}")
            
            return total_found
            
        except Exception as e:
            self.log(f"❌ Ошибка поиска по заявкам: {e}", "ERROR")
            return 0
    
    def analyze_api_filtering_issue(self):
        """Анализ проблемы фильтрации API"""
        self.log(f"\n🔍 АНАЛИЗ ПРОБЛЕМЫ ФИЛЬТРАЦИИ API:")
        self.log("=" * 50)
        
        try:
            # Получаем данные через API layout-with-cargo
            self.log("📡 Запрос к API /api/operator/warehouses/layout-with-cargo...")
            
            # Сначала получаем склады оператора
            warehouses_response = self.session.get(f"{API_BASE}/operator/warehouses")
            if warehouses_response.status_code != 200:
                self.log(f"❌ Ошибка получения складов: {warehouses_response.status_code}")
                return
            
            warehouses = warehouses_response.json()
            self.log(f"✅ Получено складов оператора: {len(warehouses)}")
            
            api_found_total = 0
            
            for warehouse in warehouses:
                warehouse_id = warehouse.get("id")
                warehouse_name = warehouse.get("name", "N/A")
                
                self.log(f"\n🏢 Проверка склада: {warehouse_name} (ID: {warehouse_id})")
                
                # Запрос к layout-with-cargo для этого склада
                layout_response = self.session.get(f"{API_BASE}/operator/warehouses/{warehouse_id}/layout-with-cargo")
                
                if layout_response.status_code == 200:
                    layout_data = layout_response.json()
                    
                    # Подсчет грузов в layout
                    cargo_count = 0
                    usr648425_count = 0
                    
                    if "layout" in layout_data:
                        layout = layout_data["layout"]
                        if "blocks" in layout:
                            for block in layout["blocks"]:
                                if "shelves" in block:
                                    for shelf in block["shelves"]:
                                        if "cells" in shelf:
                                            for cell in shelf["cells"]:
                                                if "cargo" in cell and cell["cargo"]:
                                                    for cargo in cell["cargo"]:
                                                        cargo_count += 1
                                                        placed_by = cargo.get("placed_by_operator", "")
                                                        if placed_by == TARGET_OPERATOR:
                                                            usr648425_count += 1
                    
                    self.log(f"  📊 Всего грузов в layout: {cargo_count}")
                    self.log(f"  🎯 Грузов размещенных {TARGET_OPERATOR}: {usr648425_count}")
                    api_found_total += usr648425_count
                    
                    # Проверка cargo_info если есть
                    if "cargo_info" in layout_data:
                        cargo_info = layout_data["cargo_info"]
                        cargo_info_count = len(cargo_info) if isinstance(cargo_info, list) else 0
                        usr648425_cargo_info = 0
                        
                        if isinstance(cargo_info, list):
                            for cargo in cargo_info:
                                placed_by = cargo.get("placed_by_operator", "")
                                if placed_by == TARGET_OPERATOR:
                                    usr648425_cargo_info += 1
                        
                        self.log(f"  📋 cargo_info записей: {cargo_info_count}")
                        self.log(f"  🎯 cargo_info для {TARGET_OPERATOR}: {usr648425_cargo_info}")
                else:
                    self.log(f"  ❌ Ошибка получения layout: {layout_response.status_code}")
            
            self.log(f"\n📊 СРАВНЕНИЕ API И БАЗЫ ДАННЫХ:")
            self.log(f"  API находит грузов {TARGET_OPERATOR}: {api_found_total}")
            self.log(f"  База данных содержит: {self.test_results['placement_records_found']}")
            self.log(f"  Ожидается всего: {self.test_results['expected_total']}")
            
            if api_found_total < self.test_results['placement_records_found']:
                self.test_results["api_filtering_issue"] = f"API фильтрация неполная: API находит {api_found_total}, а в БД {self.test_results['placement_records_found']}"
                self.log(f"  ⚠️ ПРОБЛЕМА: API фильтрация неполная!")
                self.log(f"     API не показывает {self.test_results['placement_records_found'] - api_found_total} записей")
            elif api_found_total == self.test_results['placement_records_found']:
                self.test_results["api_filtering_issue"] = "API фильтрация корректна, но данных меньше ожидаемого"
                self.log(f"  ✅ API фильтрация корректна")
                self.log(f"  ⚠️ Но общее количество меньше ожидаемого")
            
        except Exception as e:
            self.log(f"❌ Ошибка анализа API: {e}", "ERROR")
    
    def generate_comprehensive_report(self):
        """Генерация комплексного отчета диагностики"""
        self.log("\n📋 КОМПЛЕКСНЫЙ ОТЧЕТ ДИАГНОСТИКИ:")
        self.log("=" * 80)
        
        # Заголовок
        self.log(f"🎯 КРИТИЧЕСКАЯ ДИАГНОСТИКА: Поиск placement_records оператора {TARGET_OPERATOR}")
        self.log(f"📅 Время диагностики: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Основные результаты
        self.log(f"\n📊 ОСНОВНЫЕ РЕЗУЛЬТАТЫ:")
        self.log(f"  ✅ Авторизация: {'УСПЕШНО' if self.test_results['auth_success'] else 'НЕУДАЧНО'}")
        self.log(f"  ✅ Подключение к MongoDB: {'УСПЕШНО' if self.test_results['mongo_connection'] else 'НЕУДАЧНО'}")
        self.log(f"  📊 Найдено placement_records: {self.test_results['placement_records_found']}")
        self.log(f"  🎯 Ожидалось всего: {self.test_results['expected_total']}")
        self.log(f"  ⚠️ Недостает записей: {self.test_results['expected_total'] - self.test_results['placement_records_found']}")
        
        # Анализ по складам
        if self.test_results["warehouse_analysis"]:
            self.log(f"\n🏢 АНАЛИЗ ПО СКЛАДАМ:")
            for warehouse_id, count in self.test_results["warehouse_analysis"].items():
                self.log(f"  Склад {warehouse_id}: {count} единиц")
        
        # Анализ по заявкам
        if self.test_results["applications_analysis"]:
            self.log(f"\n📋 АНАЛИЗ ПО ЗАЯВКАМ:")
            for app_number, found_count in self.test_results["applications_analysis"].items():
                expected = EXPECTED_APPLICATIONS.get(app_number, "неизвестно")
                status = "✅" if expected != "неизвестно" and found_count == expected else "⚠️"
                self.log(f"  {status} Заявка {app_number}: найдено {found_count}, ожидалось {expected}")
        
        # Недостающие записи
        if self.test_results["missing_records"]:
            self.log(f"\n⚠️ НЕДОСТАЮЩИЕ ЗАПИСИ:")
            for missing in self.test_results["missing_records"]:
                self.log(f"  Заявка {missing['application']}: недостает {missing['missing']} единиц")
        
        # Проблема API фильтрации
        if self.test_results["api_filtering_issue"]:
            self.log(f"\n🔍 ПРОБЛЕМА API ФИЛЬТРАЦИИ:")
            self.log(f"  {self.test_results['api_filtering_issue']}")
        
        # Финальные выводы
        self.log(f"\n🎯 ФИНАЛЬНЫЕ ВЫВОДЫ:")
        
        if self.test_results['placement_records_found'] == self.test_results['expected_total']:
            self.log("✅ ВСЕ 13 PLACEMENT_RECORDS НАЙДЕНЫ!")
            self.log("🎉 Проблема может быть в API фильтрации, а не в отсутствии данных")
        elif self.test_results['placement_records_found'] > 0:
            missing = self.test_results['expected_total'] - self.test_results['placement_records_found']
            self.log(f"⚠️ НАЙДЕНО ТОЛЬКО {self.test_results['placement_records_found']} ИЗ {self.test_results['expected_total']} ЗАПИСЕЙ")
            self.log(f"❌ НЕДОСТАЕТ {missing} PLACEMENT_RECORDS")
            self.log("🔍 Возможные причины:")
            self.log("   1. Записи были удалены из базы данных")
            self.log("   2. Записи сохранены с другим operator_id")
            self.log("   3. Записи находятся в другой коллекции")
            self.log("   4. Проблема с полями placed_by_operator/placed_by")
        else:
            self.log("❌ НИ ОДНОЙ ЗАПИСИ НЕ НАЙДЕНО!")
            self.log("🔍 Критическая проблема: все данные отсутствуют или поля неправильные")
        
        return self.test_results['placement_records_found'] >= 4  # Минимум то что API находит
    
    def run_comprehensive_diagnosis(self):
        """Запуск комплексной диагностики"""
        self.log("🚀 ЗАПУСК КРИТИЧЕСКОЙ ДИАГНОСТИКИ USR648425 PLACEMENT_RECORDS")
        self.log("=" * 80)
        
        # 1. Авторизация
        if not self.authenticate_warehouse_operator():
            self.log("❌ ДИАГНОСТИКА ПРЕРВАНА: Не удалось авторизоваться", "ERROR")
            return False
        
        # 2. Подключение к MongoDB
        if not self.connect_to_mongodb():
            self.log("❌ ДИАГНОСТИКА ПРЕРВАНА: Не удалось подключиться к MongoDB", "ERROR")
            return False
        
        # 3. Поиск placement_records по оператору
        placement_records = self.search_placement_records_by_operator()
        
        # 4. Поиск по конкретным заявкам
        found_by_applications = self.search_by_specific_applications()
        
        # 5. Анализ проблемы API фильтрации
        self.analyze_api_filtering_issue()
        
        # 6. Генерация комплексного отчета
        success = self.generate_comprehensive_report()
        
        return success

def main():
    """Главная функция"""
    diagnostic = USR648425PlacementDiagnostic()
    
    try:
        success = diagnostic.run_comprehensive_diagnosis()
        
        if success:
            print("\n" + "="*80)
            print("🎉 КРИТИЧЕСКАЯ ДИАГНОСТИКА ЗАВЕРШЕНА!")
            print(f"✅ Найдено placement_records: {diagnostic.test_results['placement_records_found']}")
            print("📊 Детальный анализ проблемы выполнен")
            print("🔍 Смотрите отчет выше для понимания причин расхождений")
            sys.exit(0)
        else:
            print("\n" + "="*80)
            print("❌ КРИТИЧЕСКАЯ ДИАГНОСТИКА ВЫЯВИЛА ПРОБЛЕМЫ!")
            print("🔍 Не все ожидаемые placement_records найдены")
            print("⚠️ Требуется дополнительное расследование")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Диагностика прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
ПРЯМАЯ ДИАГНОСТИКА БАЗЫ ДАННЫХ: Поиск placement_records в MongoDB
================================================================

ЦЕЛЬ: Прямой доступ к MongoDB для поиска placement_records и анализа проблемы

КРИТИЧЕСКИЕ ПРОВЕРКИ:
1. Подключение к MongoDB
2. Поиск коллекций с placement данными
3. Анализ всех записей размещения
4. Поиск записей для заявок: 25082298, 250101, 25082235
5. Анализ warehouse_id паттернов
6. Поиск склада 001/Москва
"""

import requests
import json
import sys
import os
from datetime import datetime
from pymongo import MongoClient
from collections import defaultdict

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-manage-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# MongoDB конфигурация
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'cargo_transport')

# Конфигурация
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"
TARGET_APPLICATIONS = ["25082298", "250101", "25082235"]
EXPECTED_UNITS = {"25082298": 7, "250101": 2, "25082235": 4}
TOTAL_EXPECTED = 13

class DirectDatabaseDiagnosticTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.mongo_client = None
        self.db = None
        self.test_results = {
            "auth_success": False,
            "mongo_connection": False,
            "collections_found": [],
            "placement_records_found": 0,
            "target_applications_found": {},
            "warehouse_001_records": 0,
            "warehouse_patterns": {},
            "location_formats": set(),
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
            self.log(f"📍 MongoDB URL: {MONGO_URL}")
            self.log(f"📍 Database: {DB_NAME}")
            
            self.mongo_client = MongoClient(MONGO_URL)
            self.db = self.mongo_client[DB_NAME]
            
            # Проверяем подключение
            self.mongo_client.admin.command('ping')
            self.test_results["mongo_connection"] = True
            self.log("✅ Успешное подключение к MongoDB")
            
            # Получаем список коллекций
            collections = self.db.list_collection_names()
            self.test_results["collections_found"] = collections
            self.log(f"📋 Найдено {len(collections)} коллекций: {collections}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Ошибка подключения к MongoDB: {str(e)}", "ERROR")
            return False
    
    def search_placement_collections(self):
        """Поиск коллекций с данными о размещении"""
        try:
            self.log("\n🔍 ПОИСК КОЛЛЕКЦИЙ С ДАННЫМИ О РАЗМЕЩЕНИИ...")
            
            placement_collections = []
            
            # Список возможных коллекций с данными о размещении
            possible_collections = [
                'placement_records',
                'cargo_placement',
                'warehouse_placements',
                'individual_placements',
                'cargo',
                'operator_cargo',
                'warehouse_cells'
            ]
            
            for collection_name in possible_collections:
                if collection_name in self.test_results["collections_found"]:
                    collection = self.db[collection_name]
                    count = collection.count_documents({})
                    self.log(f"✅ Коллекция {collection_name}: {count} документов")
                    placement_collections.append((collection_name, count))
                else:
                    self.log(f"❌ Коллекция {collection_name}: не найдена")
            
            return placement_collections
            
        except Exception as e:
            self.log(f"❌ Ошибка поиска коллекций размещения: {str(e)}", "ERROR")
            return []
    
    def analyze_cargo_collections(self):
        """Анализ коллекций cargo и operator_cargo для поиска размещенных грузов"""
        try:
            self.log("\n📦 АНАЛИЗ КОЛЛЕКЦИЙ CARGO...")
            
            all_placement_data = []
            
            # Анализ коллекции cargo
            if 'cargo' in self.test_results["collections_found"]:
                cargo_collection = self.db['cargo']
                cargo_count = cargo_collection.count_documents({})
                self.log(f"📋 Коллекция cargo: {cargo_count} документов")
                
                # Поиск грузов с данными о размещении
                placed_cargo = list(cargo_collection.find({
                    "$or": [
                        {"status": "placed_in_warehouse"},
                        {"warehouse_id": {"$exists": True, "$ne": None}},
                        {"block_number": {"$exists": True}},
                        {"individual_items.is_placed": True}
                    ]
                }))
                
                self.log(f"🎯 Найдено {len(placed_cargo)} размещенных грузов в коллекции cargo")
                
                for cargo in placed_cargo:
                    cargo_number = cargo.get('cargo_number', '')
                    individual_items = cargo.get('individual_items', [])
                    
                    for item in individual_items:
                        if item.get('is_placed', False):
                            placement_data = {
                                'source': 'cargo',
                                'cargo_number': cargo_number,
                                'individual_number': item.get('individual_number', ''),
                                'warehouse_id': cargo.get('warehouse_id'),
                                'location': item.get('placement_info', ''),
                                'is_placed': item.get('is_placed', False),
                                'placed_at': item.get('placed_at'),
                                'placed_by': item.get('placed_by')
                            }
                            all_placement_data.append(placement_data)
            
            # Анализ коллекции operator_cargo
            if 'operator_cargo' in self.test_results["collections_found"]:
                operator_cargo_collection = self.db['operator_cargo']
                operator_cargo_count = operator_cargo_collection.count_documents({})
                self.log(f"📋 Коллекция operator_cargo: {operator_cargo_count} документов")
                
                # Поиск грузов с данными о размещении
                placed_operator_cargo = list(operator_cargo_collection.find({
                    "$or": [
                        {"status": "placed_in_warehouse"},
                        {"warehouse_id": {"$exists": True, "$ne": None}},
                        {"block_number": {"$exists": True}},
                        {"individual_items.is_placed": True}
                    ]
                }))
                
                self.log(f"🎯 Найдено {len(placed_operator_cargo)} размещенных грузов в коллекции operator_cargo")
                
                for cargo in placed_operator_cargo:
                    cargo_number = cargo.get('cargo_number', '')
                    individual_items = cargo.get('individual_items', [])
                    
                    for item in individual_items:
                        if item.get('is_placed', False):
                            placement_data = {
                                'source': 'operator_cargo',
                                'cargo_number': cargo_number,
                                'individual_number': item.get('individual_number', ''),
                                'warehouse_id': cargo.get('warehouse_id'),
                                'location': item.get('placement_info', ''),
                                'is_placed': item.get('is_placed', False),
                                'placed_at': item.get('placed_at'),
                                'placed_by': item.get('placed_by')
                            }
                            all_placement_data.append(placement_data)
            
            self.test_results["placement_records_found"] = len(all_placement_data)
            self.log(f"📊 ВСЕГО НАЙДЕНО {len(all_placement_data)} ЗАПИСЕЙ О РАЗМЕЩЕНИИ")
            
            return all_placement_data
            
        except Exception as e:
            self.log(f"❌ Ошибка анализа коллекций cargo: {str(e)}", "ERROR")
            return []
    
    def search_placement_records_collection(self):
        """Поиск в коллекции placement_records"""
        try:
            self.log("\n🔍 ПОИСК В КОЛЛЕКЦИИ placement_records...")
            
            if 'placement_records' not in self.test_results["collections_found"]:
                self.log("❌ Коллекция placement_records не найдена")
                return []
            
            placement_collection = self.db['placement_records']
            all_records = list(placement_collection.find({}))
            
            self.log(f"📋 Найдено {len(all_records)} записей в placement_records")
            
            placement_data = []
            for record in all_records:
                placement_data.append({
                    'source': 'placement_records',
                    'cargo_number': record.get('cargo_number', ''),
                    'individual_number': record.get('individual_number', ''),
                    'warehouse_id': record.get('warehouse_id'),
                    'location': record.get('location', ''),
                    'placed_at': record.get('placed_at'),
                    'placed_by': record.get('placed_by')
                })
            
            return placement_data
            
        except Exception as e:
            self.log(f"❌ Ошибка поиска в placement_records: {str(e)}", "ERROR")
            return []
    
    def analyze_warehouses(self):
        """Анализ складов для поиска склада 001"""
        try:
            self.log("\n🏢 АНАЛИЗ СКЛАДОВ...")
            
            if 'warehouses' not in self.test_results["collections_found"]:
                self.log("❌ Коллекция warehouses не найдена")
                return {}
            
            warehouses_collection = self.db['warehouses']
            all_warehouses = list(warehouses_collection.find({}))
            
            self.log(f"📋 Найдено {len(all_warehouses)} складов")
            
            warehouse_info = {}
            moscow_warehouse = None
            
            for warehouse in all_warehouses:
                warehouse_id = warehouse.get('id', '')
                warehouse_name = warehouse.get('name', '')
                warehouse_id_number = warehouse.get('warehouse_id_number', '')
                location = warehouse.get('location', '')
                
                warehouse_info[warehouse_id] = {
                    'name': warehouse_name,
                    'id_number': warehouse_id_number,
                    'location': location
                }
                
                self.log(f"🏢 Склад: {warehouse_name} (ID: {warehouse_id}, Номер: {warehouse_id_number}, Локация: {location})")
                
                # Поиск склада 001 или Москва
                if (warehouse_id_number == '001' or 
                    'москва' in warehouse_name.lower() or 
                    'москва' in location.lower()):
                    moscow_warehouse = warehouse
                    self.log(f"🎯 НАЙДЕН СКЛАД 001/МОСКВА: {warehouse_name}")
            
            return warehouse_info, moscow_warehouse
            
        except Exception as e:
            self.log(f"❌ Ошибка анализа складов: {str(e)}", "ERROR")
            return {}, None
    
    def analyze_placement_data(self, placement_data):
        """Анализ данных о размещении"""
        try:
            self.log(f"\n🔍 АНАЛИЗ {len(placement_data)} ЗАПИСЕЙ О РАЗМЕЩЕНИИ...")
            
            # Статистика по заявкам
            application_stats = defaultdict(list)
            warehouse_stats = defaultdict(int)
            location_formats = set()
            
            for record in placement_data:
                cargo_number = record.get('cargo_number', '')
                warehouse_id = record.get('warehouse_id', '')
                location = record.get('location', '')
                
                # Анализ заявок
                if cargo_number:
                    application_stats[cargo_number].append(record)
                
                # Анализ складов
                if warehouse_id:
                    warehouse_stats[warehouse_id] += 1
                
                # Анализ форматов местоположения
                if location:
                    location_formats.add(location)
            
            # Анализ целевых заявок
            self.log("\n🎯 АНАЛИЗ ЦЕЛЕВЫХ ЗАЯВОК:")
            for app_number in TARGET_APPLICATIONS:
                found_records = application_stats.get(app_number, [])
                expected_count = EXPECTED_UNITS.get(app_number, 0)
                
                self.test_results["target_applications_found"][app_number] = len(found_records)
                
                if found_records:
                    self.log(f"✅ Заявка {app_number}: найдено {len(found_records)} записей (ожидалось {expected_count})")
                    for record in found_records:
                        self.log(f"   - {record.get('individual_number', 'N/A')} в {record.get('location', 'N/A')} (источник: {record.get('source', 'N/A')})")
                else:
                    self.log(f"❌ Заявка {app_number}: НЕ НАЙДЕНА (ожидалось {expected_count} записей)")
                    self.test_results["critical_issues"].append(f"Заявка {app_number} не найдена в базе данных")
            
            # Анализ складов
            self.log(f"\n🏢 АНАЛИЗ СКЛАДОВ ({len(warehouse_stats)} складов):")
            for warehouse_id, count in warehouse_stats.items():
                self.log(f"📦 Склад {warehouse_id}: {count} записей")
            
            # Анализ форматов местоположения
            self.log(f"\n📍 НАЙДЕНО {len(location_formats)} УНИКАЛЬНЫХ ФОРМАТОВ МЕСТОПОЛОЖЕНИЯ:")
            for location in sorted(location_formats):
                self.log(f"   - {location}")
                self.test_results["location_formats"].add(location)
            
            self.test_results["warehouse_patterns"] = dict(warehouse_stats)
            
            return application_stats, warehouse_stats, location_formats
            
        except Exception as e:
            self.log(f"❌ Ошибка анализа данных размещения: {str(e)}", "ERROR")
            return {}, {}, set()
    
    def run_comprehensive_diagnosis(self):
        """Запуск полной диагностики"""
        try:
            self.log("🚀 ЗАПУСК ПРЯМОЙ ДИАГНОСТИКИ БАЗЫ ДАННЫХ")
            self.log("=" * 80)
            
            # 1. Авторизация
            if not self.authenticate_operator():
                self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться")
                return False
            
            # 2. Подключение к MongoDB
            if not self.connect_to_mongodb():
                self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось подключиться к MongoDB")
                return False
            
            # 3. Поиск коллекций с данными о размещении
            placement_collections = self.search_placement_collections()
            
            # 4. Анализ складов
            warehouse_info, moscow_warehouse = self.analyze_warehouses()
            
            # 5. Поиск данных о размещении в разных коллекциях
            placement_data = []
            
            # Поиск в коллекции placement_records
            placement_records_data = self.search_placement_records_collection()
            placement_data.extend(placement_records_data)
            
            # Поиск в коллекциях cargo
            cargo_placement_data = self.analyze_cargo_collections()
            placement_data.extend(cargo_placement_data)
            
            # 6. Анализ найденных данных
            if placement_data:
                app_stats, warehouse_stats, location_formats = self.analyze_placement_data(placement_data)
            else:
                self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Не найдено данных о размещении")
            
            # 7. Финальный отчет
            self.generate_final_report(moscow_warehouse)
            
            return True
            
        except Exception as e:
            self.log(f"❌ КРИТИЧЕСКАЯ ОШИБКА диагностики: {str(e)}", "ERROR")
            return False
        finally:
            if self.mongo_client:
                self.mongo_client.close()
    
    def generate_final_report(self, moscow_warehouse=None):
        """Генерация финального отчета диагностики"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 ФИНАЛЬНЫЙ ОТЧЕТ ПРЯМОЙ ДИАГНОСТИКИ БАЗЫ ДАННЫХ")
            self.log("=" * 80)
            
            # Статистика подключения
            self.log(f"✅ Авторизация: {'УСПЕШНО' if self.test_results['auth_success'] else 'ОШИБКА'}")
            self.log(f"✅ MongoDB подключение: {'УСПЕШНО' if self.test_results['mongo_connection'] else 'ОШИБКА'}")
            self.log(f"📋 Коллекций найдено: {len(self.test_results['collections_found'])}")
            self.log(f"📊 Записей о размещении найдено: {self.test_results['placement_records_found']}")
            
            # Информация о складе 001
            if moscow_warehouse:
                self.log(f"\n🎯 СКЛАД 001/МОСКВА НАЙДЕН:")
                self.log(f"   - Название: {moscow_warehouse.get('name', 'N/A')}")
                self.log(f"   - ID: {moscow_warehouse.get('id', 'N/A')}")
                self.log(f"   - Номер: {moscow_warehouse.get('warehouse_id_number', 'N/A')}")
                self.log(f"   - Локация: {moscow_warehouse.get('location', 'N/A')}")
            else:
                self.log(f"\n❌ СКЛАД 001/МОСКВА НЕ НАЙДЕН")
                self.test_results["critical_issues"].append("Склад 001/Москва не найден в базе данных")
            
            # Целевые заявки
            self.log(f"\n🎯 ЦЕЛЕВЫЕ ЗАЯВКИ:")
            total_found = 0
            for app_number, expected in EXPECTED_UNITS.items():
                found = self.test_results["target_applications_found"].get(app_number, 0)
                total_found += found
                status = "✅" if found == expected else "❌"
                self.log(f"{status} {app_number}: найдено {found} из {expected} ожидаемых")
            
            self.log(f"\n📈 ОБЩИЙ ИТОГ: найдено {total_found} из {TOTAL_EXPECTED} ожидаемых единиц")
            
            # Критические проблемы
            if self.test_results["critical_issues"]:
                self.log(f"\n🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ ({len(self.test_results['critical_issues'])}):")
                for issue in self.test_results["critical_issues"]:
                    self.log(f"❌ {issue}")
            
            # Форматы местоположения
            if self.test_results["location_formats"]:
                self.log(f"\n📍 НАЙДЕННЫЕ ФОРМАТЫ МЕСТОПОЛОЖЕНИЯ ({len(self.test_results['location_formats'])}):")
                for location_format in sorted(self.test_results["location_formats"]):
                    self.log(f"   - {location_format}")
            
            # Рекомендации
            self.log(f"\n💡 РЕКОМЕНДАЦИИ:")
            if total_found == 0:
                self.log("🔧 1. КРИТИЧЕСКАЯ ПРОБЛЕМА: Нет записей о размещении в базе данных")
                self.log("🔧 2. Проверить процесс размещения грузов - записи не сохраняются")
                self.log("🔧 3. Проверить API endpoints для размещения грузов")
            elif total_found < TOTAL_EXPECTED:
                self.log("🔧 1. Частичная потеря данных о размещении")
                self.log("🔧 2. Проверить синхронизацию между frontend и backend")
                self.log("🔧 3. Восстановить недостающие записи")
            
            if not moscow_warehouse:
                self.log("🔧 4. Создать или исправить склад 001/Москва в базе данных")
            
            # Успешность диагностики
            success_rate = (total_found / TOTAL_EXPECTED) * 100 if TOTAL_EXPECTED > 0 else 0
            self.log(f"\n📊 УСПЕШНОСТЬ ДИАГНОСТИКИ: {success_rate:.1f}%")
            
            if success_rate == 0:
                self.log("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: ПОЛНАЯ ПОТЕРЯ ДАННЫХ!")
            elif success_rate < 50:
                self.log("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА ПОДТВЕРЖДЕНА!")
            elif success_rate < 100:
                self.log("⚠️ ЧАСТИЧНАЯ ПРОБЛЕМА ОБНАРУЖЕНА")
            else:
                self.log("✅ ВСЕ ЗАПИСИ НАЙДЕНЫ УСПЕШНО")
                
        except Exception as e:
            self.log(f"❌ Ошибка генерации отчета: {str(e)}", "ERROR")

def main():
    """Главная функция"""
    print("🚀 ПРЯМАЯ ДИАГНОСТИКА БАЗЫ ДАННЫХ: Поиск 13 недостающих единиц склада 001")
    print("=" * 80)
    
    tester = DirectDatabaseDiagnosticTester()
    
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
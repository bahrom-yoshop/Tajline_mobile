#!/usr/bin/env python3
"""
РАСШИРЕННЫЙ ПОИСК ВСЕХ ДАННЫХ СВЯЗАННЫХ С ОПЕРАТОРОМ USR648425
==============================================================

ЦЕЛЬ: Найти ВСЕ упоминания USR648425 во всех коллекциях и полях базы данных

СТРАТЕГИЯ ПОИСКА:
1. Поиск по всем коллекциям MongoDB
2. Поиск по всем возможным полям с "USR648425"
3. Поиск заявок 25082298, 250101, 25082235 во всех коллекциях
4. Анализ структуры данных для понимания где могут храниться placement_records
5. Поиск по частичным совпадениям и вариациям имени оператора
"""

import requests
import json
import sys
import os
from datetime import datetime
from pymongo import MongoClient
import re

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-manage-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Конфигурация
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"
TARGET_OPERATOR = "USR648425"
TARGET_APPLICATIONS = ["25082298", "250101", "25082235"]

class ComprehensiveUSR648425Search:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.mongo_client = None
        self.db = None
        self.search_results = {
            "collections_searched": 0,
            "operator_mentions": {},
            "application_mentions": {},
            "placement_data_found": [],
            "potential_matches": []
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
            self.search_results["collections_searched"] = len(collections)
            return True
            
        except Exception as e:
            self.log(f"❌ Ошибка подключения к MongoDB: {e}", "ERROR")
            return False
    
    def search_all_collections_for_operator(self):
        """Поиск USR648425 во всех коллекциях"""
        self.log(f"🔍 ПОИСК {TARGET_OPERATOR} ВО ВСЕХ КОЛЛЕКЦИЯХ...")
        self.log("=" * 60)
        
        try:
            collections = self.db.list_collection_names()
            
            for collection_name in collections:
                self.log(f"\n📂 Поиск в коллекции: {collection_name}")
                collection = self.db[collection_name]
                
                # Различные варианты поиска оператора
                search_patterns = [
                    {"$text": {"$search": TARGET_OPERATOR}},  # Текстовый поиск
                    {"$or": [
                        {field: TARGET_OPERATOR} for field in [
                            "placed_by_operator", "placed_by", "operator_id", 
                            "placed_by_operator_id", "created_by", "updated_by",
                            "user_id", "operator", "placed_by_user", "accepting_operator"
                        ]
                    ]},
                    {"$or": [
                        {field: {"$regex": TARGET_OPERATOR, "$options": "i"}} for field in [
                            "placed_by_operator", "placed_by", "operator_id", 
                            "placed_by_operator_id", "created_by", "updated_by",
                            "user_id", "operator", "placed_by_user", "accepting_operator"
                        ]
                    ]}
                ]
                
                total_found = 0
                
                for i, pattern in enumerate(search_patterns):
                    try:
                        if i == 0:  # Текстовый поиск может не работать без индекса
                            try:
                                results = list(collection.find(pattern).limit(10))
                            except:
                                continue
                        else:
                            results = list(collection.find(pattern).limit(10))
                        
                        if results:
                            total_found += len(results)
                            self.log(f"  ✅ Найдено {len(results)} записей (паттерн {i+1})")
                            
                            # Сохраняем первые несколько результатов для анализа
                            for result in results[:3]:
                                self.search_results["operator_mentions"][collection_name] = self.search_results["operator_mentions"].get(collection_name, [])
                                self.search_results["operator_mentions"][collection_name].append({
                                    "pattern": i+1,
                                    "sample_data": {k: v for k, v in result.items() if k != "_id"}
                                })
                    except Exception as e:
                        continue
                
                if total_found == 0:
                    self.log(f"  ❌ Не найдено записей с {TARGET_OPERATOR}")
                else:
                    self.log(f"  🎯 ВСЕГО найдено: {total_found} записей")
                    
        except Exception as e:
            self.log(f"❌ Ошибка поиска по коллекциям: {e}", "ERROR")
    
    def search_applications_in_all_collections(self):
        """Поиск заявок во всех коллекциях"""
        self.log(f"\n🔍 ПОИСК ЗАЯВОК ВО ВСЕХ КОЛЛЕКЦИЯХ...")
        self.log("=" * 60)
        
        try:
            collections = self.db.list_collection_names()
            
            for app_number in TARGET_APPLICATIONS:
                self.log(f"\n📋 Поиск заявки {app_number}:")
                
                for collection_name in collections:
                    collection = self.db[collection_name]
                    
                    # Поиск по различным полям номера заявки
                    search_patterns = [
                        {"cargo_number": app_number},
                        {"application_number": app_number},
                        {"request_number": app_number},
                        {"number": app_number},
                        {"id": app_number}
                    ]
                    
                    found_in_collection = False
                    
                    for pattern in search_patterns:
                        try:
                            results = list(collection.find(pattern).limit(5))
                            if results:
                                found_in_collection = True
                                self.log(f"  ✅ {collection_name}: {len(results)} записей")
                                
                                # Сохраняем данные для анализа
                                self.search_results["application_mentions"][app_number] = self.search_results["application_mentions"].get(app_number, {})
                                self.search_results["application_mentions"][app_number][collection_name] = {
                                    "count": len(results),
                                    "sample": results[0] if results else None
                                }
                                
                                # Проверяем есть ли данные о размещении в этих записях
                                for result in results:
                                    placement_fields = [
                                        "placement_records", "individual_items", "placed_items",
                                        "is_placed", "placement_info", "placed_by_operator"
                                    ]
                                    
                                    for field in placement_fields:
                                        if field in result and result[field]:
                                            self.search_results["placement_data_found"].append({
                                                "application": app_number,
                                                "collection": collection_name,
                                                "field": field,
                                                "data": result[field]
                                            })
                                break
                        except Exception as e:
                            continue
                    
                    if not found_in_collection:
                        # Попробуем поиск по regex для частичных совпадений
                        try:
                            regex_results = list(collection.find({
                                "$or": [
                                    {"cargo_number": {"$regex": app_number}},
                                    {"application_number": {"$regex": app_number}},
                                    {"request_number": {"$regex": app_number}}
                                ]
                            }).limit(3))
                            
                            if regex_results:
                                self.log(f"  🔍 {collection_name}: {len(regex_results)} частичных совпадений")
                        except:
                            pass
                            
        except Exception as e:
            self.log(f"❌ Ошибка поиска заявок: {e}", "ERROR")
    
    def analyze_placement_data_structure(self):
        """Анализ структуры данных размещения"""
        self.log(f"\n🔍 АНАЛИЗ СТРУКТУРЫ ДАННЫХ РАЗМЕЩЕНИЯ...")
        self.log("=" * 60)
        
        try:
            # Проверяем коллекции которые могут содержать данные размещения
            placement_collections = [
                "placement_records", "operator_cargo", "cargo", 
                "warehouse_cells", "individual_items", "cargo_placement"
            ]
            
            for collection_name in placement_collections:
                if collection_name in self.db.list_collection_names():
                    collection = self.db[collection_name]
                    
                    # Получаем несколько записей для анализа структуры
                    sample_records = list(collection.find().limit(3))
                    total_count = collection.count_documents({})
                    
                    self.log(f"\n📂 Коллекция {collection_name}:")
                    self.log(f"  📊 Всего записей: {total_count}")
                    
                    if sample_records:
                        self.log(f"  🔍 Структура данных:")
                        sample = sample_records[0]
                        for key, value in sample.items():
                            if key != "_id":
                                value_type = type(value).__name__
                                if isinstance(value, list) and value:
                                    value_preview = f"[{len(value)} элементов, первый: {type(value[0]).__name__}]"
                                elif isinstance(value, dict):
                                    value_preview = f"{{dict с {len(value)} ключами}}"
                                else:
                                    value_preview = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                                
                                self.log(f"    {key}: {value_type} = {value_preview}")
                        
                        # Поиск полей связанных с операторами
                        operator_fields = []
                        for key in sample.keys():
                            if any(op_word in key.lower() for op_word in ["operator", "placed", "user", "by"]):
                                operator_fields.append(key)
                        
                        if operator_fields:
                            self.log(f"  🎯 Поля операторов: {operator_fields}")
                    else:
                        self.log(f"  ❌ Коллекция пустая")
                else:
                    self.log(f"❌ Коллекция {collection_name} не существует")
                    
        except Exception as e:
            self.log(f"❌ Ошибка анализа структуры: {e}", "ERROR")
    
    def search_for_similar_operators(self):
        """Поиск похожих операторов"""
        self.log(f"\n🔍 ПОИСК ПОХОЖИХ ОПЕРАТОРОВ...")
        self.log("=" * 60)
        
        try:
            # Поиск операторов с похожими номерами
            collections_to_search = ["users", "placement_records", "operator_cargo", "cargo"]
            
            for collection_name in collections_to_search:
                if collection_name in self.db.list_collection_names():
                    collection = self.db[collection_name]
                    
                    # Поиск операторов начинающихся с USR
                    usr_operators = list(collection.find({
                        "$or": [
                            {"user_number": {"$regex": "^USR"}},
                            {"operator_id": {"$regex": "^USR"}},
                            {"placed_by_operator": {"$regex": "^USR"}},
                            {"placed_by": {"$regex": "^USR"}}
                        ]
                    }).limit(10))
                    
                    if usr_operators:
                        self.log(f"\n📂 {collection_name}: найдено {len(usr_operators)} USR операторов")
                        
                        unique_operators = set()
                        for record in usr_operators:
                            for field in ["user_number", "operator_id", "placed_by_operator", "placed_by"]:
                                if field in record and record[field] and record[field].startswith("USR"):
                                    unique_operators.add(record[field])
                        
                        self.log(f"  🎯 Уникальные USR операторы: {sorted(unique_operators)}")
                        
                        # Проверяем есть ли близкие к USR648425
                        for operator in unique_operators:
                            if "648" in operator or operator.endswith("425"):
                                self.log(f"  ⚠️ ПОТЕНЦИАЛЬНОЕ СОВПАДЕНИЕ: {operator}")
                                self.search_results["potential_matches"].append({
                                    "collection": collection_name,
                                    "operator": operator,
                                    "reason": "Содержит 648 или заканчивается на 425"
                                })
                                
        except Exception as e:
            self.log(f"❌ Ошибка поиска похожих операторов: {e}", "ERROR")
    
    def generate_comprehensive_report(self):
        """Генерация комплексного отчета"""
        self.log("\n📋 КОМПЛЕКСНЫЙ ОТЧЕТ РАСШИРЕННОГО ПОИСКА:")
        self.log("=" * 80)
        
        # Заголовок
        self.log(f"🎯 РАСШИРЕННЫЙ ПОИСК ДАННЫХ ОПЕРАТОРА {TARGET_OPERATOR}")
        self.log(f"📅 Время поиска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Статистика поиска
        self.log(f"\n📊 СТАТИСТИКА ПОИСКА:")
        self.log(f"  Коллекций проверено: {self.search_results['collections_searched']}")
        self.log(f"  Упоминаний оператора найдено: {len(self.search_results['operator_mentions'])}")
        self.log(f"  Заявок найдено: {len(self.search_results['application_mentions'])}")
        self.log(f"  Данных размещения найдено: {len(self.search_results['placement_data_found'])}")
        self.log(f"  Потенциальных совпадений: {len(self.search_results['potential_matches'])}")
        
        # Упоминания оператора
        if self.search_results["operator_mentions"]:
            self.log(f"\n🎯 НАЙДЕННЫЕ УПОМИНАНИЯ ОПЕРАТОРА {TARGET_OPERATOR}:")
            for collection, mentions in self.search_results["operator_mentions"].items():
                self.log(f"  📂 {collection}: {len(mentions)} упоминаний")
                for mention in mentions[:2]:  # Показываем первые 2
                    self.log(f"    - Паттерн {mention['pattern']}: {list(mention['sample_data'].keys())}")
        
        # Найденные заявки
        if self.search_results["application_mentions"]:
            self.log(f"\n📋 НАЙДЕННЫЕ ЗАЯВКИ:")
            for app_number, collections in self.search_results["application_mentions"].items():
                self.log(f"  📋 Заявка {app_number}:")
                for collection, data in collections.items():
                    self.log(f"    📂 {collection}: {data['count']} записей")
        
        # Данные размещения
        if self.search_results["placement_data_found"]:
            self.log(f"\n🎯 НАЙДЕННЫЕ ДАННЫЕ РАЗМЕЩЕНИЯ:")
            for placement in self.search_results["placement_data_found"]:
                self.log(f"  📋 Заявка {placement['application']} в {placement['collection']}")
                self.log(f"    Поле: {placement['field']}")
                if isinstance(placement['data'], list):
                    self.log(f"    Данные: список из {len(placement['data'])} элементов")
                else:
                    self.log(f"    Данные: {str(placement['data'])[:100]}...")
        
        # Потенциальные совпадения
        if self.search_results["potential_matches"]:
            self.log(f"\n⚠️ ПОТЕНЦИАЛЬНЫЕ СОВПАДЕНИЯ:")
            for match in self.search_results["potential_matches"]:
                self.log(f"  🔍 {match['operator']} в {match['collection']}")
                self.log(f"    Причина: {match['reason']}")
        
        # Финальные выводы
        self.log(f"\n🎯 ФИНАЛЬНЫЕ ВЫВОДЫ:")
        
        if self.search_results["operator_mentions"]:
            self.log("✅ НАЙДЕНЫ УПОМИНАНИЯ ОПЕРАТОРА USR648425!")
            self.log("🔍 Данные существуют, но возможно в неожиданных местах")
        elif self.search_results["potential_matches"]:
            self.log("⚠️ НАЙДЕНЫ ПОХОЖИЕ ОПЕРАТОРЫ!")
            self.log("🔍 Возможно номер оператора записан с ошибкой")
        else:
            self.log("❌ ОПЕРАТОР USR648425 НЕ НАЙДЕН НИГДЕ!")
            self.log("🔍 Возможные причины:")
            self.log("   1. Данные были удалены")
            self.log("   2. Номер оператора записан по-другому")
            self.log("   3. Данные находятся в другой базе данных")
            self.log("   4. Пользователь ошибся в номере оператора")
        
        if self.search_results["application_mentions"]:
            self.log(f"\n✅ ЗАЯВКИ НАЙДЕНЫ В БАЗЕ ДАННЫХ!")
            self.log("🔍 Заявки существуют, но возможно не связаны с USR648425")
        else:
            self.log(f"\n❌ ЗАЯВКИ НЕ НАЙДЕНЫ В БАЗЕ ДАННЫХ!")
            self.log("🔍 Критическая проблема: заявки отсутствуют полностью")
        
        return len(self.search_results["operator_mentions"]) > 0 or len(self.search_results["potential_matches"]) > 0
    
    def run_comprehensive_search(self):
        """Запуск комплексного поиска"""
        self.log("🚀 ЗАПУСК РАСШИРЕННОГО ПОИСКА USR648425")
        self.log("=" * 80)
        
        # 1. Авторизация
        if not self.authenticate_warehouse_operator():
            self.log("❌ ПОИСК ПРЕРВАН: Не удалось авторизоваться", "ERROR")
            return False
        
        # 2. Подключение к MongoDB
        if not self.connect_to_mongodb():
            self.log("❌ ПОИСК ПРЕРВАН: Не удалось подключиться к MongoDB", "ERROR")
            return False
        
        # 3. Поиск оператора во всех коллекциях
        self.search_all_collections_for_operator()
        
        # 4. Поиск заявок во всех коллекциях
        self.search_applications_in_all_collections()
        
        # 5. Анализ структуры данных размещения
        self.analyze_placement_data_structure()
        
        # 6. Поиск похожих операторов
        self.search_for_similar_operators()
        
        # 7. Генерация комплексного отчета
        success = self.generate_comprehensive_report()
        
        return success

def main():
    """Главная функция"""
    search = ComprehensiveUSR648425Search()
    
    try:
        success = search.run_comprehensive_search()
        
        if success:
            print("\n" + "="*80)
            print("🎉 РАСШИРЕННЫЙ ПОИСК ЗАВЕРШЕН!")
            print("✅ Найдены данные связанные с USR648425 или похожими операторами")
            print("📊 Смотрите детальный отчет выше")
            sys.exit(0)
        else:
            print("\n" + "="*80)
            print("❌ РАСШИРЕННЫЙ ПОИСК НЕ ДАЛ РЕЗУЛЬТАТОВ!")
            print("🔍 Оператор USR648425 и связанные данные не найдены")
            print("⚠️ Возможно данные отсутствуют или номер оператора неверный")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Поиск прерван пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
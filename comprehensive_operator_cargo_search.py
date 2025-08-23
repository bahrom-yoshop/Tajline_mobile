#!/usr/bin/env python3
"""
РАСШИРЕННЫЙ ПОИСК ДАННЫХ ОПЕРАТОРА USR648425 В СИСТЕМЕ
====================================================

ЦЕЛЬ: Найти данные оператора USR648425 через все доступные API endpoints
и понять где хранятся данные о размещенных им 7 единицах заявки 25082298

СТРАТЕГИЯ ПОИСКА:
1. Проверить все доступные API endpoints
2. Поиск по различным критериям (номер оператора, имя, заявка)
3. Анализ структуры данных во всех найденных записях
4. Проверка как admin, так и operator доступов
"""

import requests
import json
import sys
import os
from datetime import datetime

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-manage-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Конфигурация поиска
SEARCH_TERMS = [
    "USR648425",
    "Юлдашев", 
    "Жасурбек",
    "Бахтиёрович",
    "25082298"
]

class ComprehensiveOperatorSearch:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.admin_token = None
        self.admin_info = None
        self.found_data = []
        self.api_endpoints_tested = []

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def authenticate_operator(self):
        """Авторизация как оператор склада"""
        try:
            self.log("🔐 Авторизация как оператор склада...")
            
            auth_data = {
                "phone": "+79777888999",
                "password": "warehouse123"
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=auth_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                
                user_response = self.session.get(f"{API_BASE}/auth/me")
                if user_response.status_code == 200:
                    self.operator_info = user_response.json()
                    self.log(f"✅ Авторизация оператора: {self.operator_info.get('full_name')}")
                    return True
            
            self.log(f"❌ Ошибка авторизации оператора: {response.status_code}")
            return False
                
        except Exception as e:
            self.log(f"❌ Исключение при авторизации оператора: {e}", "ERROR")
            return False

    def authenticate_admin(self):
        """Попытка авторизации как администратор"""
        try:
            self.log("🔐 Попытка авторизации как администратор...")
            
            # Пробуем стандартные admin credentials
            admin_credentials = [
                {"phone": "+992000000001", "password": "admin123"},
                {"phone": "+992000000000", "password": "admin123"},
                {"phone": "admin", "password": "admin123"},
                {"phone": "+79999999999", "password": "admin123"}
            ]
            
            for creds in admin_credentials:
                try:
                    response = requests.post(f"{API_BASE}/auth/login", json=creds)
                    if response.status_code == 200:
                        data = response.json()
                        admin_token = data.get("access_token")
                        
                        # Проверяем роль
                        admin_session = requests.Session()
                        admin_session.headers.update({"Authorization": f"Bearer {admin_token}"})
                        user_response = admin_session.get(f"{API_BASE}/auth/me")
                        
                        if user_response.status_code == 200:
                            user_data = user_response.json()
                            if user_data.get("role") == "admin":
                                self.admin_token = admin_token
                                self.admin_info = user_data
                                self.log(f"✅ Авторизация администратора: {user_data.get('full_name')}")
                                return admin_session
                except:
                    continue
            
            self.log("❌ Не удалось авторизоваться как администратор")
            return None
                
        except Exception as e:
            self.log(f"❌ Исключение при авторизации администратора: {e}", "ERROR")
            return None

    def test_all_endpoints(self, session, role_name):
        """Тестирование всех возможных endpoints"""
        self.log(f"🔍 Тестирование endpoints как {role_name}...")
        
        # Список всех возможных endpoints для поиска данных
        endpoints_to_test = [
            # Operator endpoints
            "/operator/cargo/list",
            "/operator/cargo/all", 
            "/operator/cargo/available-for-placement",
            "/operator/cargo/individual-units-for-placement",
            "/operator/cargo/fully-placed",
            "/operator/placement-progress",
            "/operator/warehouses",
            
            # Admin endpoints (если доступны)
            "/admin/cargo/list",
            "/admin/cargo/all",
            "/admin/users/list",
            "/admin/operators/list",
            
            # General cargo endpoints
            "/cargo/search",
            "/cargo/list",
            "/cargo/all",
            
            # Warehouse endpoints
            "/warehouses/list",
            "/warehouses/all-cities",
            
            # Debug endpoints
            "/debug/operator-cargo",
            "/debug/placement-records",
            "/debug/cargo",
            "/debug/collections",
            
            # Search endpoints
            "/search/advanced",
            "/search/cargo",
            "/search/users"
        ]
        
        found_endpoints = []
        
        for endpoint in endpoints_to_test:
            try:
                # Тестируем без параметров
                response = session.get(f"{API_BASE}{endpoint}")
                status = response.status_code
                
                endpoint_info = {
                    "endpoint": endpoint,
                    "status": status,
                    "role": role_name,
                    "accessible": status in [200, 201],
                    "data": None
                }
                
                if status == 200:
                    try:
                        data = response.json()
                        endpoint_info["data"] = data
                        found_endpoints.append(endpoint_info)
                        
                        # Анализируем данные на предмет поисковых терминов
                        self.analyze_data_for_search_terms(data, endpoint, role_name)
                        
                        self.log(f"✅ {endpoint}: {status} - данных: {self.count_records(data)}")
                    except:
                        self.log(f"⚠️ {endpoint}: {status} - не JSON")
                elif status == 404:
                    self.log(f"❌ {endpoint}: не найден")
                elif status == 403:
                    self.log(f"🔒 {endpoint}: доступ запрещен")
                elif status == 405:
                    self.log(f"⚠️ {endpoint}: метод не поддерживается")
                else:
                    self.log(f"⚠️ {endpoint}: {status}")
                
                self.api_endpoints_tested.append(endpoint_info)
                
            except Exception as e:
                self.log(f"❌ Ошибка при тестировании {endpoint}: {e}")
        
        return found_endpoints

    def count_records(self, data):
        """Подсчет количества записей в данных"""
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            if "items" in data:
                return len(data["items"])
            elif "cargo" in data:
                return len(data["cargo"])
            elif "users" in data:
                return len(data["users"])
            elif "warehouses" in data:
                return len(data["warehouses"])
            else:
                return len(data)
        return 0

    def analyze_data_for_search_terms(self, data, endpoint, role):
        """Анализ данных на предмет поисковых терминов"""
        try:
            found_matches = []
            
            def search_in_object(obj, path=""):
                matches = []
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_path = f"{path}.{key}" if path else key
                        
                        # Проверяем значение на наличие поисковых терминов
                        if isinstance(value, str):
                            for term in SEARCH_TERMS:
                                if term.lower() in value.lower():
                                    matches.append({
                                        "path": current_path,
                                        "value": value,
                                        "term": term
                                    })
                        
                        # Рекурсивно ищем в вложенных объектах
                        matches.extend(search_in_object(value, current_path))
                        
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        current_path = f"{path}[{i}]" if path else f"[{i}]"
                        matches.extend(search_in_object(item, current_path))
                
                return matches
            
            # Ищем в данных
            matches = search_in_object(data)
            
            if matches:
                self.log(f"🎯 НАЙДЕНЫ СОВПАДЕНИЯ в {endpoint} ({role}):")
                for match in matches[:5]:  # Показываем первые 5 совпадений
                    self.log(f"   {match['path']}: {match['value']} (термин: {match['term']})")
                
                # Сохраняем найденные данные
                self.found_data.append({
                    "endpoint": endpoint,
                    "role": role,
                    "matches": matches,
                    "data": data
                })
                
                if len(matches) > 5:
                    self.log(f"   ... и еще {len(matches) - 5} совпадений")
                    
        except Exception as e:
            self.log(f"❌ Ошибка при анализе данных из {endpoint}: {e}")

    def search_with_parameters(self, session, role_name):
        """Поиск с различными параметрами"""
        self.log(f"🔍 Поиск с параметрами как {role_name}...")
        
        # Endpoints которые поддерживают параметры поиска
        search_endpoints = [
            "/operator/cargo/list",
            "/operator/cargo/available-for-placement",
            "/operator/cargo/individual-units-for-placement",
            "/admin/cargo/list",
            "/cargo/search"
        ]
        
        # Различные параметры для поиска
        search_params = [
            {"search": "USR648425"},
            {"search": "Юлдашев"},
            {"search": "25082298"},
            {"operator": "USR648425"},
            {"operator_name": "Юлдашев"},
            {"cargo_number": "25082298"},
            {"placed_by": "USR648425"},
            {"page": 1, "per_page": 100},
            {"page": 1, "per_page": 100, "search": "USR648425"}
        ]
        
        for endpoint in search_endpoints:
            for params in search_params:
                try:
                    response = session.get(f"{API_BASE}{endpoint}", params=params)
                    
                    if response.status_code == 200:
                        data = response.json()
                        record_count = self.count_records(data)
                        
                        if record_count > 0:
                            self.log(f"✅ {endpoint} с {params}: найдено {record_count} записей")
                            self.analyze_data_for_search_terms(data, f"{endpoint}?{params}", role_name)
                        else:
                            self.log(f"⚪ {endpoint} с {params}: 0 записей")
                    
                except Exception as e:
                    continue

    def detailed_analysis_of_found_data(self):
        """Детальный анализ найденных данных"""
        if not self.found_data:
            self.log("❌ Данные для анализа не найдены")
            return
        
        self.log("🔍 ДЕТАЛЬНЫЙ АНАЛИЗ НАЙДЕННЫХ ДАННЫХ:")
        self.log("=" * 60)
        
        for i, found_item in enumerate(self.found_data, 1):
            self.log(f"\n📋 ИСТОЧНИК #{i}: {found_item['endpoint']} ({found_item['role']})")
            self.log(f"   Совпадений: {len(found_item['matches'])}")
            
            # Анализируем структуру данных
            data = found_item['data']
            
            if isinstance(data, dict) and "items" in data:
                items = data["items"]
            elif isinstance(data, list):
                items = data
            else:
                items = [data]
            
            # Ищем записи с нашими терминами
            relevant_records = []
            for item in items:
                if self.contains_search_terms(item):
                    relevant_records.append(item)
            
            self.log(f"   Релевантных записей: {len(relevant_records)}")
            
            # Анализируем каждую релевантную запись
            for j, record in enumerate(relevant_records[:3], 1):  # Показываем первые 3
                self.log(f"\n   📦 ЗАПИСЬ #{j}:")
                self.analyze_single_record(record, "      ")

    def contains_search_terms(self, obj):
        """Проверяет, содержит ли объект поисковые термины"""
        obj_str = json.dumps(obj, default=str).lower()
        return any(term.lower() in obj_str for term in SEARCH_TERMS)

    def analyze_single_record(self, record, indent=""):
        """Анализ одной записи"""
        try:
            # Основная информация
            cargo_number = record.get("cargo_number", "неизвестно")
            self.log(f"{indent}Номер заявки: {cargo_number}")
            
            # Информация об операторе
            operator_fields = ["operator_name", "placed_by", "created_by_operator", "accepting_operator", "placing_operator"]
            for field in operator_fields:
                if field in record and record[field]:
                    self.log(f"{indent}{field}: {record[field]}")
            
            # warehouse_id
            if "warehouse_id" in record:
                self.log(f"{indent}warehouse_id: {record['warehouse_id']}")
            
            # Анализ cargo_items
            if "cargo_items" in record:
                cargo_items = record["cargo_items"]
                self.log(f"{indent}cargo_items: {len(cargo_items)} шт.")
                
                total_individual = 0
                total_placed = 0
                
                for k, cargo_item in enumerate(cargo_items, 1):
                    cargo_name = cargo_item.get("cargo_name", f"Груз #{k}")
                    self.log(f"{indent}  {k}. {cargo_name}")
                    
                    if "individual_items" in cargo_item:
                        individual_items = cargo_item["individual_items"]
                        placed_count = sum(1 for item in individual_items if item.get("is_placed", False))
                        
                        total_individual += len(individual_items)
                        total_placed += placed_count
                        
                        self.log(f"{indent}     individual_items: {len(individual_items)} (размещено: {placed_count})")
                        
                        # Проверяем структуру individual_items
                        if individual_items:
                            sample = individual_items[0]
                            fields = list(sample.keys())
                            self.log(f"{indent}     поля: {', '.join(fields[:5])}{'...' if len(fields) > 5 else ''}")
                
                self.log(f"{indent}ИТОГО: {total_individual} единиц, размещено: {total_placed}")
            
            # Дополнительные поля
            additional_fields = ["status", "created_at", "updated_at", "payment_status"]
            for field in additional_fields:
                if field in record and record[field]:
                    self.log(f"{indent}{field}: {record[field]}")
                    
        except Exception as e:
            self.log(f"{indent}❌ Ошибка анализа записи: {e}")

    def generate_comprehensive_report(self):
        """Генерация комплексного отчета"""
        self.log("\n" + "=" * 80)
        self.log("📊 КОМПЛЕКСНЫЙ ОТЧЕТ ПОИСКА ОПЕРАТОРА USR648425")
        self.log("=" * 80)
        
        # Статистика endpoints
        total_endpoints = len(self.api_endpoints_tested)
        accessible_endpoints = len([e for e in self.api_endpoints_tested if e["accessible"]])
        
        self.log(f"📈 СТАТИСТИКА API:")
        self.log(f"   Протестировано endpoints: {total_endpoints}")
        self.log(f"   Доступных endpoints: {accessible_endpoints}")
        self.log(f"   Найдено данных в: {len(self.found_data)} endpoints")
        
        # Доступные endpoints
        if accessible_endpoints > 0:
            self.log(f"\n✅ ДОСТУПНЫЕ ENDPOINTS:")
            for endpoint_info in self.api_endpoints_tested:
                if endpoint_info["accessible"]:
                    data_count = self.count_records(endpoint_info.get("data", {}))
                    self.log(f"   {endpoint_info['endpoint']} ({endpoint_info['role']}): {data_count} записей")
        
        # Найденные совпадения
        if self.found_data:
            self.log(f"\n🎯 НАЙДЕННЫЕ СОВПАДЕНИЯ:")
            total_matches = sum(len(item["matches"]) for item in self.found_data)
            self.log(f"   Всего совпадений: {total_matches}")
            
            for item in self.found_data:
                self.log(f"   {item['endpoint']} ({item['role']}): {len(item['matches'])} совпадений")
        else:
            self.log(f"\n❌ СОВПАДЕНИЯ НЕ НАЙДЕНЫ")
        
        # Выводы и рекомендации
        self.log(f"\n🔍 ВЫВОДЫ:")
        
        if not self.found_data:
            self.log("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Данные оператора USR648425 не найдены ни в одном API")
            self.log("   Возможные причины:")
            self.log("   1. Данные хранятся в MongoDB, но не доступны через API")
            self.log("   2. Поля содержат другие значения (не USR648425 или Юлдашев)")
            self.log("   3. Данные были удалены или перемещены")
            self.log("   4. API не предоставляет доступ к operator_cargo коллекции")
        else:
            self.log("✅ Данные найдены! Анализируем структуру...")
            
            # Проверяем, найдена ли заявка 25082298
            found_target_app = False
            for item in self.found_data:
                for match in item["matches"]:
                    if "25082298" in match["value"]:
                        found_target_app = True
                        break
            
            if found_target_app:
                self.log("🎯 ЦЕЛЕВАЯ ЗАЯВКА 25082298 НАЙДЕНА!")
            else:
                self.log("❌ Целевая заявка 25082298 не найдена среди совпадений")
        
        self.log(f"\n💡 РЕКОМЕНДАЦИИ:")
        if not self.found_data:
            self.log("1. Создать debug endpoint для прямого доступа к MongoDB")
            self.log("2. Проверить содержимое operator_cargo коллекции в базе данных")
            self.log("3. Убедиться что данные не были потеряны при миграции")
        else:
            self.log("1. Проанализировать найденные данные на предмет структуры")
            self.log("2. Убедиться что API layout-with-cargo использует правильные источники")
            self.log("3. Проверить логику фильтрации по warehouse_id")
        
        self.log("\n" + "=" * 80)

    def run_comprehensive_search(self):
        """Запуск комплексного поиска"""
        self.log("🚀 НАЧАЛО КОМПЛЕКСНОГО ПОИСКА ОПЕРАТОРА USR648425")
        self.log("=" * 80)
        
        # 1. Авторизация как оператор
        if not self.authenticate_operator():
            self.log("❌ Не удалось авторизоваться как оператор")
            return False
        
        # 2. Тестирование endpoints как оператор
        self.test_all_endpoints(self.session, "operator")
        self.search_with_parameters(self.session, "operator")
        
        # 3. Попытка авторизации как администратор
        admin_session = self.authenticate_admin()
        if admin_session:
            self.test_all_endpoints(admin_session, "admin")
            self.search_with_parameters(admin_session, "admin")
        
        # 4. Детальный анализ найденных данных
        self.detailed_analysis_of_found_data()
        
        # 5. Генерация отчета
        self.generate_comprehensive_report()
        
        return True

def main():
    """Главная функция"""
    searcher = ComprehensiveOperatorSearch()
    
    try:
        success = searcher.run_comprehensive_search()
        
        if success:
            print("\n✅ Комплексный поиск завершен")
            return 0
        else:
            print("\n❌ Комплексный поиск завершен с ошибками")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Поиск прерван пользователем")
        return 1
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
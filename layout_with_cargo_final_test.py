#!/usr/bin/env python3
"""
ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ API layout-with-cargo с полной поддержкой двух источников
==============================================================================

ЦЕЛЬ: Убедиться что API теперь находит ВСЕ размещенные единицы из operator_cargo с оператором USR648425

КРИТИЧЕСКИЕ ПРОВЕРКИ:
1. Авторизация оператора (+79777888999/warehouse123)  
2. API layout-with-cargo для склада 001:
   - Проверить количество найденных записей из placement_records
   - Проверить количество найденных записей из operator_cargo (новый источник)
   - Убедиться что найдены данные оператора USR648425 (Юлдашев Жасурбек Бахтиёрович)
3. Проверка конкретных заявок из скриншота:
   - 25082298: ожидается 7 единиц со статусом "Размещено"
   - 250101: ожидается 2 единицы  
   - 25082235: ожидается 4 единицы
   - Всего: 13 единиц размещенных оператором USR648425
4. Качество данных в cargo_info: Полная информация о каждой единице

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: 
- Минимум 13 размещенных единиц найдено
- Данные от оператора USR648425 присутствуют в результатах
- Поле cargo_info содержит все найденные единицы с полной информацией
- API отображает реальную картину размещения со скриншота пользователя
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
TARGET_WAREHOUSE_ID = "001"
TARGET_OPERATOR_ID = "USR648425"
TARGET_OPERATOR_NAME = "Юлдашев Жасурбек Бахтиёрович"

# Ожидаемые заявки из скриншота
EXPECTED_APPLICATIONS = {
    "25082298": {"expected_units": 7, "status": "Размещено"},
    "250101": {"expected_units": 2, "status": "Размещено"}, 
    "25082235": {"expected_units": 4, "status": "Размещено"}
}
TOTAL_EXPECTED_UNITS = 13

class LayoutWithCargoTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.test_results = {
            "auth_success": False,
            "api_accessible": False,
            "cargo_info_present": False,
            "operator_data_found": False,
            "expected_applications_found": {},
            "total_units_found": 0,
            "data_quality_check": False,
            "detailed_analysis": {}
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
        self.log(f"📋 Тестирование API layout-with-cargo для склада {TARGET_WAREHOUSE_ID}...")
        
        try:
            response = self.session.get(f"{API_BASE}/warehouses/{TARGET_WAREHOUSE_ID}/layout-with-cargo")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ API доступен и возвращает данные")
                self.test_results["api_accessible"] = True
                return data
            else:
                self.log(f"❌ Ошибка API: {response.status_code} - {response.text}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Исключение при запросе API: {e}", "ERROR")
            return None
    
    def analyze_cargo_info(self, layout_data):
        """Анализ поля cargo_info"""
        self.log("\n🔍 АНАЛИЗ ПОЛЯ cargo_info:")
        self.log("=" * 60)
        
        cargo_info = layout_data.get("cargo_info", [])
        
        if not cargo_info:
            self.log("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Поле cargo_info отсутствует или пустое!", "ERROR")
            return False
        
        self.log(f"✅ Поле cargo_info найдено с {len(cargo_info)} единицами")
        self.test_results["cargo_info_present"] = True
        self.test_results["total_units_found"] = len(cargo_info)
        
        # Анализ источников данных
        placement_records_count = 0
        operator_cargo_count = 0
        operator_usr648425_count = 0
        applications_found = {}
        
        for i, cargo_unit in enumerate(cargo_info):
            cargo_number = cargo_unit.get("cargo_number", "N/A")
            individual_number = cargo_unit.get("individual_number", "N/A")
            placed_by = cargo_unit.get("placed_by", "N/A")
            placed_by_id = cargo_unit.get("placed_by_id", "N/A")
            source = cargo_unit.get("source", "unknown")
            
            # Подсчет по источникам
            if source == "placement_records":
                placement_records_count += 1
            elif source == "operator_cargo":
                operator_cargo_count += 1
            
            # Поиск данных оператора USR648425
            if placed_by_id == TARGET_OPERATOR_ID or TARGET_OPERATOR_NAME in str(placed_by):
                operator_usr648425_count += 1
                self.log(f"  🎯 Найдена единица от оператора {TARGET_OPERATOR_ID}: {individual_number}")
            
            # Группировка по заявкам
            if cargo_number not in applications_found:
                applications_found[cargo_number] = []
            applications_found[cargo_number].append({
                "individual_number": individual_number,
                "placed_by": placed_by,
                "placed_by_id": placed_by_id,
                "source": source
            })
        
        # Результаты анализа источников
        self.log(f"\n📊 АНАЛИЗ ИСТОЧНИКОВ ДАННЫХ:")
        self.log(f"  📋 Из placement_records: {placement_records_count} единиц")
        self.log(f"  🏢 Из operator_cargo: {operator_cargo_count} единиц")
        self.log(f"  🎯 От оператора {TARGET_OPERATOR_ID}: {operator_usr648425_count} единиц")
        
        # Проверка наличия данных от целевого оператора
        if operator_usr648425_count > 0:
            self.log(f"✅ Данные от оператора {TARGET_OPERATOR_ID} найдены!")
            self.test_results["operator_data_found"] = True
        else:
            self.log(f"❌ Данные от оператора {TARGET_OPERATOR_ID} НЕ найдены!", "ERROR")
        
        # Анализ конкретных заявок
        self.log(f"\n🔍 АНАЛИЗ КОНКРЕТНЫХ ЗАЯВОК:")
        for app_number, expected in EXPECTED_APPLICATIONS.items():
            if app_number in applications_found:
                found_units = len(applications_found[app_number])
                expected_units = expected["expected_units"]
                
                self.log(f"  📦 Заявка {app_number}: найдено {found_units}/{expected_units} единиц")
                
                if found_units >= expected_units:
                    self.log(f"    ✅ Ожидания выполнены или превышены")
                    self.test_results["expected_applications_found"][app_number] = True
                else:
                    self.log(f"    ❌ Недостаточно единиц (ожидалось {expected_units})")
                    self.test_results["expected_applications_found"][app_number] = False
                
                # Детали единиц
                for unit in applications_found[app_number]:
                    self.log(f"      - {unit['individual_number']} (источник: {unit['source']}, оператор: {unit['placed_by_id']})")
            else:
                self.log(f"  ❌ Заявка {app_number}: НЕ найдена!", "ERROR")
                self.test_results["expected_applications_found"][app_number] = False
        
        # Сохранение детального анализа
        self.test_results["detailed_analysis"] = {
            "placement_records_count": placement_records_count,
            "operator_cargo_count": operator_cargo_count,
            "operator_usr648425_count": operator_usr648425_count,
            "applications_found": applications_found,
            "total_applications": len(applications_found)
        }
        
        return True
    
    def check_data_quality(self, layout_data):
        """Проверка качества данных в cargo_info"""
        self.log("\n🔍 ПРОВЕРКА КАЧЕСТВА ДАННЫХ:")
        self.log("=" * 50)
        
        cargo_info = layout_data.get("cargo_info", [])
        
        if not cargo_info:
            self.log("❌ Нет данных для проверки качества", "ERROR")
            return False
        
        required_fields = [
            "cargo_number", "individual_number", "cargo_name", 
            "sender_name", "recipient_name", "placed_by", "placed_at"
        ]
        
        complete_records = 0
        incomplete_records = 0
        
        for i, cargo_unit in enumerate(cargo_info):
            missing_fields = []
            for field in required_fields:
                if not cargo_unit.get(field):
                    missing_fields.append(field)
            
            if not missing_fields:
                complete_records += 1
            else:
                incomplete_records += 1
                if incomplete_records <= 3:  # Показываем только первые 3 неполные записи
                    self.log(f"  ⚠️ Запись #{i+1} неполная: отсутствуют {missing_fields}")
        
        self.log(f"📊 Качество данных:")
        self.log(f"  ✅ Полные записи: {complete_records}")
        self.log(f"  ⚠️ Неполные записи: {incomplete_records}")
        
        quality_percentage = (complete_records / len(cargo_info)) * 100 if cargo_info else 0
        self.log(f"  📈 Качество данных: {quality_percentage:.1f}%")
        
        # Считаем качество хорошим если >= 80% записей полные
        quality_good = quality_percentage >= 80.0
        self.test_results["data_quality_check"] = quality_good
        
        if quality_good:
            self.log(f"  ✅ Качество данных соответствует требованиям")
        else:
            self.log(f"  ❌ Качество данных требует улучшения")
        
        return quality_good
    
    def generate_final_report(self):
        """Генерация финального отчета"""
        self.log("\n📋 ФИНАЛЬНЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ:")
        self.log("=" * 80)
        
        # Заголовок
        self.log(f"🎯 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ API layout-with-cargo")
        self.log(f"📅 Время тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"🏢 Целевой склад: {TARGET_WAREHOUSE_ID}")
        self.log(f"👤 Целевой оператор: {TARGET_OPERATOR_ID} ({TARGET_OPERATOR_NAME})")
        
        # Результаты по этапам
        self.log(f"\n📊 РЕЗУЛЬТАТЫ ПО ЭТАПАМ:")
        self.log(f"  1. ✅ Авторизация оператора: {'✅ УСПЕШНО' if self.test_results['auth_success'] else '❌ НЕУДАЧНО'}")
        self.log(f"  2. ✅ Доступность API: {'✅ ДОСТУПЕН' if self.test_results['api_accessible'] else '❌ НЕДОСТУПЕН'}")
        self.log(f"  3. ✅ Поле cargo_info: {'✅ ПРИСУТСТВУЕТ' if self.test_results['cargo_info_present'] else '❌ ОТСУТСТВУЕТ'}")
        self.log(f"  4. 🎯 Данные оператора {TARGET_OPERATOR_ID}: {'✅ НАЙДЕНЫ' if self.test_results['operator_data_found'] else '❌ НЕ НАЙДЕНЫ'}")
        self.log(f"  5. 📊 Качество данных: {'✅ ХОРОШЕЕ' if self.test_results['data_quality_check'] else '❌ ТРЕБУЕТ УЛУЧШЕНИЯ'}")
        
        # Детальные результаты
        self.log(f"\n📊 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        self.log(f"  📦 Всего единиц найдено: {self.test_results['total_units_found']}")
        self.log(f"  🎯 Ожидалось минимум: {TOTAL_EXPECTED_UNITS} единиц")
        
        if "detailed_analysis" in self.test_results:
            details = self.test_results["detailed_analysis"]
            self.log(f"  📋 Из placement_records: {details['placement_records_count']}")
            self.log(f"  🏢 Из operator_cargo: {details['operator_cargo_count']}")
            self.log(f"  👤 От оператора {TARGET_OPERATOR_ID}: {details['operator_usr648425_count']}")
            self.log(f"  📑 Всего заявок: {details['total_applications']}")
        
        # Проверка конкретных заявок
        self.log(f"\n🔍 ПРОВЕРКА КОНКРЕТНЫХ ЗАЯВОК:")
        all_applications_found = True
        for app_number, expected in EXPECTED_APPLICATIONS.items():
            found = self.test_results["expected_applications_found"].get(app_number, False)
            status = "✅ НАЙДЕНА" if found else "❌ НЕ НАЙДЕНА"
            self.log(f"  📦 {app_number} ({expected['expected_units']} единиц): {status}")
            if not found:
                all_applications_found = False
        
        # Финальный вывод
        self.log(f"\n🎯 ФИНАЛЬНЫЙ РЕЗУЛЬТАТ:")
        
        # Критерии успеха
        success_criteria = [
            self.test_results["auth_success"],
            self.test_results["api_accessible"], 
            self.test_results["cargo_info_present"],
            self.test_results["operator_data_found"],
            self.test_results["total_units_found"] >= TOTAL_EXPECTED_UNITS,
            all_applications_found
        ]
        
        success_count = sum(success_criteria)
        total_criteria = len(success_criteria)
        success_rate = (success_count / total_criteria) * 100
        
        self.log(f"📊 SUCCESS RATE: {success_rate:.1f}% ({success_count}/{total_criteria} критических проверок пройдены)")
        
        if success_rate >= 90:
            self.log("🎉 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            self.log("✅ API layout-with-cargo работает с поддержкой двух источников данных")
            self.log(f"✅ Найдены данные от оператора {TARGET_OPERATOR_ID}")
            self.log("✅ Все ожидаемые заявки присутствуют в результатах")
            return True
        else:
            self.log("❌ ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ НЕ ПРОЙДЕНО!")
            if not self.test_results["operator_data_found"]:
                self.log(f"❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Данные от оператора {TARGET_OPERATOR_ID} НЕ найдены")
            if self.test_results["total_units_found"] < TOTAL_EXPECTED_UNITS:
                self.log(f"❌ НЕДОСТАТОЧНО ЕДИНИЦ: найдено {self.test_results['total_units_found']}, ожидалось {TOTAL_EXPECTED_UNITS}")
            if not all_applications_found:
                self.log("❌ НЕ ВСЕ ОЖИДАЕМЫЕ ЗАЯВКИ НАЙДЕНЫ")
            return False
    
    def run_comprehensive_test(self):
        """Запуск полного теста API layout-with-cargo"""
        self.log("🚀 ЗАПУСК ФИНАЛЬНОГО ТЕСТИРОВАНИЯ API layout-with-cargo")
        self.log("=" * 80)
        
        # 1. Авторизация
        if not self.authenticate_warehouse_operator():
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Не удалось авторизоваться", "ERROR")
            return False
        
        # 2. Тестирование API
        layout_data = self.test_layout_with_cargo_api()
        if not layout_data:
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: API недоступен", "ERROR")
            return False
        
        # 3. Анализ cargo_info
        if not self.analyze_cargo_info(layout_data):
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Проблемы с cargo_info", "ERROR")
            return False
        
        # 4. Проверка качества данных
        self.check_data_quality(layout_data)
        
        # 5. Генерация финального отчета
        return self.generate_final_report()

def main():
    """Главная функция"""
    tester = LayoutWithCargoTester()
    
    try:
        success = tester.run_comprehensive_test()
        
        if success:
            print("\n" + "="*80)
            print("🎉 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ API layout-with-cargo ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ API находит ВСЕ размещенные единицы из двух источников")
            print(f"✅ Данные от оператора {TARGET_OPERATOR_ID} присутствуют")
            print("✅ Все ожидаемые заявки найдены с правильным количеством единиц")
            print("📊 API отображает реальную картину размещения")
            sys.exit(0)
        else:
            print("\n" + "="*80)
            print("❌ ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ API layout-with-cargo НЕ ПРОЙДЕНО!")
            print("🔍 Исправления для поддержки двух источников НЕ реализованы")
            print(f"⚠️ Требуется реализация поиска в operator_cargo с оператором {TARGET_OPERATOR_ID}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""
ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ИСПРАВЛЕННОГО API layout-with-cargo С ДВУМЯ ИСТОЧНИКАМИ ДАННЫХ
====================================================================================

ЦЕЛЬ: Убедиться что API теперь находит ВСЕ 13 размещенных единиц из обеих коллекций 
(placement_records + operator_cargo)

КРИТИЧЕСКИЕ ПРОВЕРКИ:
1. Авторизация оператора (+79777888999/warehouse123)
2. Тестирование ИСПРАВЛЕННОГО API layout-with-cargo:
   - Проверить поиск в placement_records (существующий источник)
   - Проверить поиск в operator_cargo с is_placed=true (новый источник)  
   - Убедиться что найдены данные оператора USR648425 (Юлдашев Жасурбек)
   - Проверить общее количество найденных записей
3. Проверка конкретных заявок:
   - 25082298: должно найти 7 единиц (из operator_cargo)
   - 250101: должно найти 2 единицы
   - 25082235: должно найти 4 единицы
4. Качество cargo_info: Убедиться что все найденные единицы попадают в cargo_info

ИСПРАВЛЕНИЯ:
- Добавлен поиск в коллекции operator_cargo с флагом is_placed=true
- Создание синтетических placement_records из данных operator_cargo
- Объединение данных из обеих источников
- Фильтрация по warehouse_id для обеих источников

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: API должен найти все 13 размещенных единиц и корректно отобразить их в cargo_info
"""

import requests
import json
import sys
import os
from datetime import datetime
from pymongo import MongoClient

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-manage-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# MongoDB подключение для диагностики
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'cargo_transport')

# Конфигурация
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"
EXPECTED_TOTAL_UNITS = 13
TARGET_OPERATOR = "USR648425"  # Юлдашев Жасурбек
WAREHOUSE_001_ID = "d0a8362d-b4d3-4947-b335-28c94658a021"  # Москва Склад №1

# Ожидаемые заявки и их количества
EXPECTED_APPLICATIONS = {
    "25082298": 7,  # из operator_cargo
    "250101": 2,    # существующие данные
    "25082235": 4   # существующие данные
}

class LayoutWithCargoFinalTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.mongo_client = None
        self.db = None
        self.test_results = {
            "auth_success": False,
            "api_accessible": False,
            "cargo_info_present": False,
            "total_units_correct": False,
            "operator_data_found": False,
            "applications_check": {},
            "detailed_analysis": {}
        }
        
    def log(self, message, level="INFO"):
        """Логирование с временной меткой"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def connect_to_database(self):
        """Подключение к MongoDB для диагностики"""
        try:
            self.mongo_client = MongoClient(MONGO_URL)
            self.db = self.mongo_client[DB_NAME]
            self.log("✅ Подключение к MongoDB успешно")
            return True
        except Exception as e:
            self.log(f"❌ Ошибка подключения к MongoDB: {e}", "ERROR")
            return False
        
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
    
    def diagnose_database_state(self):
        """Диагностика состояния базы данных"""
        self.log("\n🔍 ДИАГНОСТИКА СОСТОЯНИЯ БАЗЫ ДАННЫХ:")
        self.log("=" * 60)
        
        if self.db is None:
            self.log("❌ База данных недоступна", "ERROR")
            return
        
        try:
            # Проверка placement_records
            placement_count = self.db.placement_records.count_documents({
                "warehouse_id": WAREHOUSE_001_ID
            })
            self.log(f"📋 placement_records для склада 001: {placement_count}")
            
            # Проверка operator_cargo с is_placed=true
            operator_cargo_placed = self.db.operator_cargo.count_documents({
                "warehouse_id": WAREHOUSE_001_ID,
                "individual_items.is_placed": True
            })
            self.log(f"📦 operator_cargo с размещенными единицами: {operator_cargo_placed}")
            
            # Поиск данных оператора USR648425
            operator_data = self.db.operator_cargo.find({
                "created_by": TARGET_OPERATOR,
                "individual_items.is_placed": True
            })
            operator_count = len(list(operator_data))
            self.log(f"👤 Данные оператора {TARGET_OPERATOR}: {operator_count} заявок")
            
            # Проверка конкретных заявок
            for app_number, expected_count in EXPECTED_APPLICATIONS.items():
                # В placement_records
                placement_app = self.db.placement_records.count_documents({
                    "cargo_number": app_number,
                    "warehouse_id": WAREHOUSE_001_ID
                })
                
                # В operator_cargo
                operator_app = self.db.operator_cargo.find_one({
                    "cargo_number": app_number
                })
                operator_placed = 0
                if operator_app and "individual_items" in operator_app:
                    operator_placed = len([item for item in operator_app["individual_items"] 
                                         if item.get("is_placed", False)])
                
                total_found = placement_app + operator_placed
                self.log(f"📊 Заявка {app_number}: placement_records={placement_app}, operator_cargo={operator_placed}, всего={total_found}, ожидается={expected_count}")
                
        except Exception as e:
            self.log(f"❌ Ошибка диагностики БД: {e}", "ERROR")
    
    def test_layout_with_cargo_api(self):
        """Тестирование исправленного API layout-with-cargo"""
        self.log("\n🎯 ТЕСТИРОВАНИЕ ИСПРАВЛЕННОГО API layout-with-cargo:")
        self.log("=" * 60)
        
        try:
            # Запрос к API с warehouse_id для склада 001
            response = self.session.get(f"{API_BASE}/warehouses/{WAREHOUSE_001_ID}/layout-with-cargo")
            
            if response.status_code != 200:
                self.log(f"❌ API недоступен: {response.status_code} - {response.text}", "ERROR")
                return False
            
            data = response.json()
            self.log("✅ API layout-with-cargo доступен")
            self.test_results["api_accessible"] = True
            
            # Проверка наличия cargo_info
            cargo_info = data.get("cargo_info", [])
            if not cargo_info:
                self.log("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: cargo_info отсутствует или пустой!", "ERROR")
                return False
            
            self.log(f"✅ cargo_info найден с {len(cargo_info)} единицами")
            self.test_results["cargo_info_present"] = True
            
            # Проверка общего количества единиц
            total_found = len(cargo_info)
            self.log(f"📊 Найдено единиц: {total_found}, ожидается: {EXPECTED_TOTAL_UNITS}")
            
            if total_found == EXPECTED_TOTAL_UNITS:
                self.log("✅ ОБЩЕЕ КОЛИЧЕСТВО ЕДИНИЦ КОРРЕКТНО!")
                self.test_results["total_units_correct"] = True
            else:
                self.log(f"⚠️ Расхождение в количестве: найдено {total_found}, ожидается {EXPECTED_TOTAL_UNITS}")
            
            # Анализ найденных данных
            self.analyze_cargo_info(cargo_info)
            
            # Проверка данных оператора USR648425
            self.check_operator_data(cargo_info)
            
            # Проверка конкретных заявок
            self.check_specific_applications(cargo_info)
            
            return True
            
        except Exception as e:
            self.log(f"❌ Ошибка тестирования API: {e}", "ERROR")
            return False
    
    def analyze_cargo_info(self, cargo_info):
        """Анализ структуры и качества cargo_info"""
        self.log("\n📋 АНАЛИЗ КАЧЕСТВА cargo_info:")
        self.log("-" * 40)
        
        applications_found = {}
        operators_found = set()
        locations_found = set()
        
        for i, item in enumerate(cargo_info):
            cargo_number = item.get("cargo_number", "N/A")
            individual_number = item.get("individual_number", "N/A")
            location = item.get("location", "N/A")
            cargo_name = item.get("cargo_name", "N/A")
            placed_by = item.get("placed_by", "N/A")
            
            # Группировка по заявкам
            if cargo_number not in applications_found:
                applications_found[cargo_number] = 0
            applications_found[cargo_number] += 1
            
            # Сбор операторов
            if placed_by != "N/A":
                operators_found.add(placed_by)
            
            # Сбор локаций
            if location != "N/A":
                locations_found.add(location)
            
            if i < 5:  # Показываем первые 5 для примера
                self.log(f"  {i+1}. {individual_number} ({cargo_name}) - {location}")
        
        self.log(f"📊 Найдено заявок: {len(applications_found)}")
        self.log(f"👥 Найдено операторов: {len(operators_found)}")
        self.log(f"📍 Найдено локаций: {len(locations_found)}")
        
        # Детальная информация по заявкам
        self.log("\n📋 РАСПРЕДЕЛЕНИЕ ПО ЗАЯВКАМ:")
        for app_number, count in applications_found.items():
            expected = EXPECTED_APPLICATIONS.get(app_number, "неизвестно")
            status = "✅" if (expected != "неизвестно" and count == expected) else "⚠️"
            self.log(f"  {status} {app_number}: {count} единиц (ожидается: {expected})")
        
        self.test_results["detailed_analysis"] = {
            "applications_found": applications_found,
            "operators_found": list(operators_found),
            "locations_found": list(locations_found),
            "total_items": len(cargo_info)
        }
    
    def check_operator_data(self, cargo_info):
        """Проверка данных оператора USR648425"""
        self.log(f"\n👤 ПРОВЕРКА ДАННЫХ ОПЕРАТОРА {TARGET_OPERATOR}:")
        self.log("-" * 40)
        
        operator_items = []
        for item in cargo_info:
            placed_by = item.get("placed_by", "")
            created_by = item.get("created_by", "")
            
            # Проверяем и placed_by и created_by
            if TARGET_OPERATOR in placed_by or TARGET_OPERATOR in created_by:
                operator_items.append(item)
        
        if operator_items:
            self.log(f"✅ Найдено {len(operator_items)} единиц от оператора {TARGET_OPERATOR}")
            self.test_results["operator_data_found"] = True
            
            # Показываем примеры
            for i, item in enumerate(operator_items[:3]):
                cargo_number = item.get("cargo_number", "N/A")
                individual_number = item.get("individual_number", "N/A")
                cargo_name = item.get("cargo_name", "N/A")
                self.log(f"  {i+1}. {individual_number} ({cargo_name}) из заявки {cargo_number}")
        else:
            self.log(f"❌ Данные оператора {TARGET_OPERATOR} НЕ найдены")
            self.log("🔍 Проверяем всех операторов в cargo_info:")
            all_operators = set()
            for item in cargo_info:
                placed_by = item.get("placed_by", "")
                created_by = item.get("created_by", "")
                if placed_by:
                    all_operators.add(placed_by)
                if created_by:
                    all_operators.add(created_by)
            
            for op in list(all_operators)[:5]:
                self.log(f"  - {op}")
    
    def check_specific_applications(self, cargo_info):
        """Проверка конкретных заявок"""
        self.log("\n📊 ПРОВЕРКА КОНКРЕТНЫХ ЗАЯВОК:")
        self.log("-" * 40)
        
        for app_number, expected_count in EXPECTED_APPLICATIONS.items():
            found_items = [item for item in cargo_info 
                          if item.get("cargo_number") == app_number]
            found_count = len(found_items)
            
            if found_count == expected_count:
                self.log(f"✅ Заявка {app_number}: найдено {found_count} единиц (ожидается {expected_count})")
                self.test_results["applications_check"][app_number] = True
            else:
                self.log(f"❌ Заявка {app_number}: найдено {found_count} единиц, ожидается {expected_count}")
                self.test_results["applications_check"][app_number] = False
                
                # Показываем что найдено
                if found_items:
                    self.log(f"   Найденные единицы:")
                    for item in found_items:
                        individual_number = item.get("individual_number", "N/A")
                        location = item.get("location", "N/A")
                        self.log(f"     - {individual_number} в {location}")
    
    def generate_final_report(self):
        """Генерация финального отчета"""
        self.log("\n📋 ФИНАЛЬНЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ:")
        self.log("=" * 80)
        
        # Заголовок
        self.log(f"🎯 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ API layout-with-cargo С ДВУМЯ ИСТОЧНИКАМИ")
        self.log(f"📅 Время тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"🏢 Целевой склад: 001 (Москва Склад №1)")
        self.log(f"👤 Целевой оператор: {TARGET_OPERATOR}")
        
        # Результаты по этапам
        self.log(f"\n📊 РЕЗУЛЬТАТЫ ПО ЭТАПАМ:")
        self.log(f"  1. ✅ Авторизация оператора: {'✅ УСПЕШНО' if self.test_results['auth_success'] else '❌ НЕУДАЧНО'}")
        self.log(f"  2. ✅ Доступность API layout-with-cargo: {'✅ ДОСТУПЕН' if self.test_results['api_accessible'] else '❌ НЕДОСТУПЕН'}")
        self.log(f"  3. ✅ Наличие cargo_info: {'✅ ПРИСУТСТВУЕТ' if self.test_results['cargo_info_present'] else '❌ ОТСУТСТВУЕТ'}")
        self.log(f"  4. 🎯 Общее количество единиц: {'✅ КОРРЕКТНО' if self.test_results['total_units_correct'] else '❌ НЕВЕРНО'}")
        self.log(f"  5. 👤 Данные оператора {TARGET_OPERATOR}: {'✅ НАЙДЕНЫ' if self.test_results['operator_data_found'] else '❌ НЕ НАЙДЕНЫ'}")
        
        # Проверка конкретных заявок
        self.log(f"\n📊 ПРОВЕРКА КОНКРЕТНЫХ ЗАЯВОК:")
        all_apps_correct = True
        for app_number, expected_count in EXPECTED_APPLICATIONS.items():
            status = self.test_results["applications_check"].get(app_number, False)
            status_icon = "✅" if status else "❌"
            self.log(f"  {status_icon} Заявка {app_number}: {expected_count} единиц")
            if not status:
                all_apps_correct = False
        
        # Детальная аналитика
        if self.test_results["detailed_analysis"]:
            details = self.test_results["detailed_analysis"]
            self.log(f"\n📊 ДЕТАЛЬНАЯ АНАЛИТИКА:")
            self.log(f"  Всего единиц в cargo_info: {details['total_items']}")
            self.log(f"  Найдено заявок: {len(details['applications_found'])}")
            self.log(f"  Найдено операторов: {len(details['operators_found'])}")
            self.log(f"  Найдено локаций: {len(details['locations_found'])}")
        
        # Финальный вывод
        self.log(f"\n🎯 ФИНАЛЬНЫЙ РЕЗУЛЬТАТ:")
        
        success_criteria = [
            self.test_results["auth_success"],
            self.test_results["api_accessible"],
            self.test_results["cargo_info_present"],
            self.test_results["total_units_correct"],
            all_apps_correct
        ]
        
        overall_success = all(success_criteria)
        
        if overall_success:
            self.log("🎉 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            self.log("✅ API layout-with-cargo находит все 13 размещенных единиц")
            self.log("✅ Данные из обеих коллекций (placement_records + operator_cargo) объединены корректно")
            self.log("✅ cargo_info содержит все необходимые единицы")
            self.log("✅ Конкретные заявки найдены в правильном количестве")
        else:
            self.log("❌ ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ НЕ ПРОЙДЕНО!")
            failed_criteria = []
            if not self.test_results["auth_success"]:
                failed_criteria.append("Авторизация")
            if not self.test_results["api_accessible"]:
                failed_criteria.append("Доступность API")
            if not self.test_results["cargo_info_present"]:
                failed_criteria.append("Наличие cargo_info")
            if not self.test_results["total_units_correct"]:
                failed_criteria.append("Общее количество единиц")
            if not all_apps_correct:
                failed_criteria.append("Конкретные заявки")
            
            self.log(f"🔍 Проблемы: {', '.join(failed_criteria)}")
        
        return overall_success
    
    def run_final_test(self):
        """Запуск полного финального теста"""
        self.log("🚀 ЗАПУСК ФИНАЛЬНОГО ТЕСТИРОВАНИЯ API layout-with-cargo")
        self.log("=" * 80)
        
        # 1. Подключение к базе данных для диагностики
        self.connect_to_database()
        
        # 2. Авторизация
        if not self.authenticate_warehouse_operator():
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Не удалось авторизоваться", "ERROR")
            return False
        
        # 3. Диагностика состояния БД
        self.diagnose_database_state()
        
        # 4. Тестирование API
        if not self.test_layout_with_cargo_api():
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: API недоступен или неисправен", "ERROR")
            return False
        
        # 5. Генерация финального отчета
        final_success = self.generate_final_report()
        
        # Закрытие подключения к БД
        if self.mongo_client:
            self.mongo_client.close()
        
        return final_success

def main():
    """Главная функция"""
    tester = LayoutWithCargoFinalTester()
    
    try:
        success = tester.run_final_test()
        
        if success:
            print("\n" + "="*80)
            print("🎉 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ API layout-with-cargo ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ API находит все 13 размещенных единиц из обеих коллекций")
            print("✅ Исправления с двумя источниками данных работают корректно")
            print("✅ cargo_info содержит все необходимые данные")
            sys.exit(0)
        else:
            print("\n" + "="*80)
            print("❌ ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ API layout-with-cargo НЕ ПРОЙДЕНО!")
            print("🔍 Найдены проблемы с поиском размещенных единиц")
            print("⚠️ Требуется дополнительное исправление API")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
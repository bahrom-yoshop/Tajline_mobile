#!/usr/bin/env python3
"""
КРИТИЧЕСКАЯ ДИАГНОСТИКА: Полный анализ склада 001 и placement_records
====================================================================

ЦЕЛЬ: Найти склад 001 любым способом и проанализировать все placement_records

ПРОБЛЕМА: API layout-with-cargo находит только 4 из 13 размещенных единиц для склада 001

СТРАТЕГИЯ ПОИСКА СКЛАДА 001:
1. По warehouse_id_number = "001"
2. По названию содержащему "001" 
3. По любому складу оператора (если только один)
4. Прямой поиск в базе всех складов

ДЕТАЛЬНАЯ ДИАГНОСТИКА:
1. Авторизация оператора (+79777888999/warehouse123)
2. Поиск склада 001 всеми возможными способами
3. Анализ placement_records для найденного склада
4. Сравнение с ожидаемыми данными (13 единиц из 3 заявок)
5. Диагностика причин расхождений
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
TARGET_WAREHOUSE = "001"
EXPECTED_APPLICATIONS = ["25082298", "250101", "25082235"]
EXPECTED_TOTAL_UNITS = 13
EXPECTED_UNITS_PER_APP = {"25082298": 7, "250101": 2, "25082235": 4}

class ComprehensiveWarehouse001Diagnoser:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.warehouse_001_info = None
        self.all_warehouses = []
        self.test_results = {
            "auth_success": False,
            "warehouse_found": False,
            "warehouse_search_method": None,
            "api_accessible": False,
            "placement_records_found": 0,
            "expected_records": EXPECTED_TOTAL_UNITS,
            "missing_records": 0,
            "applications_analysis": {},
            "critical_issues": [],
            "warehouse_details": {}
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
    
    def get_all_warehouses_info(self):
        """Получить информацию о всех доступных складах"""
        self.log("🏢 Получение информации о всех складах...")
        
        try:
            # Получаем склады оператора
            response = self.session.get(f"{API_BASE}/operator/warehouses")
            
            if response.status_code == 200:
                operator_warehouses = response.json()
                self.log(f"📋 Склады оператора: {len(operator_warehouses)}")
                
                for i, warehouse in enumerate(operator_warehouses):
                    self.log(f"  Склад #{i+1}:")
                    self.log(f"    ID: {warehouse.get('id', 'N/A')}")
                    self.log(f"    Номер: {warehouse.get('warehouse_id_number', 'НЕТ')}")
                    self.log(f"    Название: {warehouse.get('name', 'N/A')}")
                    self.log(f"    Местоположение: {warehouse.get('location', 'N/A')}")
                
                self.all_warehouses.extend(operator_warehouses)
            else:
                self.log(f"⚠️ Не удалось получить склады оператора: {response.status_code}", "WARNING")
            
            # Попробуем получить все склады системы (если есть доступ)
            try:
                response = self.session.get(f"{API_BASE}/warehouses/all-cities")
                if response.status_code == 200:
                    all_warehouses = response.json()
                    self.log(f"📋 Все склады системы: {len(all_warehouses)}")
                    
                    # Добавляем склады, которых нет в списке оператора
                    existing_ids = {w.get('id') for w in self.all_warehouses}
                    for warehouse in all_warehouses:
                        if warehouse.get('id') not in existing_ids:
                            self.all_warehouses.append(warehouse)
                            self.log(f"  Дополнительный склад: {warehouse.get('name', 'N/A')} (ID: {warehouse.get('id', 'N/A')})")
            except:
                self.log("⚠️ Не удалось получить все склады системы", "WARNING")
            
            return len(self.all_warehouses) > 0
                
        except Exception as e:
            self.log(f"❌ Исключение при получении складов: {e}", "ERROR")
            return False
    
    def find_warehouse_001_comprehensive(self):
        """Комплексный поиск склада 001 всеми возможными способами"""
        self.log("🔍 КОМПЛЕКСНЫЙ ПОИСК СКЛАДА 001:")
        self.log("=" * 60)
        
        if not self.all_warehouses:
            self.log("❌ Нет доступных складов для поиска", "ERROR")
            return False
        
        # Метод 1: По warehouse_id_number = "001"
        self.log("🔍 Метод 1: Поиск по warehouse_id_number = '001'")
        for warehouse in self.all_warehouses:
            warehouse_id_number = warehouse.get("warehouse_id_number", "")
            if warehouse_id_number == TARGET_WAREHOUSE:
                self.warehouse_001_info = warehouse
                self.test_results["warehouse_search_method"] = "warehouse_id_number"
                self.log(f"✅ Склад найден по warehouse_id_number!")
                self.log_warehouse_details(warehouse)
                self.test_results["warehouse_found"] = True
                return True
        
        self.log("❌ Склад не найден по warehouse_id_number")
        
        # Метод 2: По названию содержащему "001"
        self.log("\n🔍 Метод 2: Поиск по названию содержащему '001'")
        for warehouse in self.all_warehouses:
            warehouse_name = warehouse.get("name", "").lower()
            if "001" in warehouse_name:
                self.warehouse_001_info = warehouse
                self.test_results["warehouse_search_method"] = "name_contains_001"
                self.log(f"✅ Склад найден по названию!")
                self.log_warehouse_details(warehouse)
                self.test_results["warehouse_found"] = True
                return True
        
        self.log("❌ Склад не найден по названию")
        
        # Метод 3: Если у оператора только один склад - используем его
        operator_warehouses = [w for w in self.all_warehouses if w.get('is_operator_warehouse', True)]
        if len(operator_warehouses) == 1:
            self.log("\n🔍 Метод 3: Единственный склад оператора")
            warehouse = operator_warehouses[0]
            self.warehouse_001_info = warehouse
            self.test_results["warehouse_search_method"] = "single_operator_warehouse"
            self.log(f"✅ Используем единственный склад оператора!")
            self.log_warehouse_details(warehouse)
            self.test_results["warehouse_found"] = True
            return True
        
        # Метод 4: Поиск по местоположению "Москва"
        self.log("\n🔍 Метод 4: Поиск по местоположению 'Москва'")
        for warehouse in self.all_warehouses:
            location = warehouse.get("location", "").lower()
            if "москва" in location:
                self.warehouse_001_info = warehouse
                self.test_results["warehouse_search_method"] = "moscow_location"
                self.log(f"✅ Склад найден по местоположению Москва!")
                self.log_warehouse_details(warehouse)
                self.test_results["warehouse_found"] = True
                return True
        
        self.log("❌ Склад 001 не найден ни одним методом", "ERROR")
        return False
    
    def log_warehouse_details(self, warehouse):
        """Логирование деталей склада"""
        details = {
            "id": warehouse.get("id", "N/A"),
            "warehouse_id_number": warehouse.get("warehouse_id_number", "НЕТ"),
            "name": warehouse.get("name", "N/A"),
            "location": warehouse.get("location", "N/A"),
            "address": warehouse.get("address", "N/A"),
            "is_active": warehouse.get("is_active", "N/A")
        }
        
        self.log(f"📋 Детали найденного склада:")
        for key, value in details.items():
            self.log(f"   {key}: {value}")
        
        self.test_results["warehouse_details"] = details
    
    def test_layout_with_cargo_api(self):
        """Тестирование API layout-with-cargo для найденного склада"""
        self.log("\n🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: API layout-with-cargo")
        self.log("=" * 80)
        
        if not self.warehouse_001_info:
            self.log("❌ Склад не найден, невозможно протестировать API", "ERROR")
            return False
        
        warehouse_id = self.warehouse_001_info["id"]
        
        try:
            # Запрос к API layout-with-cargo
            self.log(f"📡 Запрос к /api/operator/warehouses/{warehouse_id}/layout-with-cargo")
            response = self.session.get(f"{API_BASE}/operator/warehouses/{warehouse_id}/layout-with-cargo")
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ API layout-with-cargo доступен")
                self.test_results["api_accessible"] = True
                
                # Анализ структуры ответа
                self.log("\n📊 АНАЛИЗ СТРУКТУРЫ ОТВЕТА:")
                self.log(f"Тип данных: {type(data)}")
                
                if isinstance(data, dict):
                    self.log(f"Ключи ответа: {list(data.keys())}")
                    
                    # Ищем информацию о размещенных грузах
                    cargo_info = data.get("cargo_info", [])
                    occupied_cells = data.get("occupied_cells", 0)
                    layout_data = data.get("layout", {})
                    
                    self.log(f"📦 cargo_info: {len(cargo_info)} записей")
                    self.log(f"🏠 occupied_cells: {occupied_cells}")
                    self.log(f"🗺️ layout данные: {type(layout_data)}")
                    
                    # КРИТИЧЕСКАЯ ПРОВЕРКА: Анализ cargo_info
                    self.analyze_cargo_info(cargo_info)
                    
                    # Сохраняем количество найденных записей
                    self.test_results["placement_records_found"] = len(cargo_info)
                    self.test_results["missing_records"] = EXPECTED_TOTAL_UNITS - len(cargo_info)
                    
                    return True
                else:
                    self.log(f"⚠️ Неожиданная структура ответа: {type(data)}", "WARNING")
                    return False
            else:
                self.log(f"❌ Ошибка API: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при тестировании API: {e}", "ERROR")
            return False
    
    def analyze_cargo_info(self, cargo_info):
        """Детальный анализ cargo_info из API ответа"""
        self.log("\n🔍 ДЕТАЛЬНЫЙ АНАЛИЗ CARGO_INFO:")
        self.log("-" * 60)
        
        if not cargo_info:
            self.log("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: cargo_info пустой!", "ERROR")
            self.test_results["critical_issues"].append("cargo_info пустой - API не находит размещенные грузы")
            return
        
        # Группируем по номерам заявок
        applications_found = {}
        
        for i, cargo in enumerate(cargo_info):
            cargo_number = cargo.get("cargo_number", "N/A")
            individual_number = cargo.get("individual_number", "N/A")
            cargo_name = cargo.get("cargo_name", "N/A")
            placement_location = cargo.get("placement_location", "N/A")
            
            self.log(f"📦 Груз #{i+1}:")
            self.log(f"   Номер заявки: {cargo_number}")
            self.log(f"   Individual номер: {individual_number}")
            self.log(f"   Название: {cargo_name}")
            self.log(f"   Местоположение: {placement_location}")
            
            # Группируем по заявкам
            if cargo_number not in applications_found:
                applications_found[cargo_number] = []
            applications_found[cargo_number].append(cargo)
        
        # Анализ найденных заявок
        self.log(f"\n📊 АНАЛИЗ ПО ЗАЯВКАМ:")
        self.log(f"Найдено заявок: {len(applications_found)}")
        
        for app_number, cargos in applications_found.items():
            expected_count = EXPECTED_UNITS_PER_APP.get(app_number, 0)
            found_count = len(cargos)
            
            self.log(f"📋 Заявка {app_number}:")
            self.log(f"   Найдено единиц: {found_count}")
            self.log(f"   Ожидалось единиц: {expected_count}")
            
            if expected_count > 0:
                if found_count == expected_count:
                    self.log(f"   ✅ Количество совпадает")
                else:
                    self.log(f"   ❌ РАСХОЖДЕНИЕ: не хватает {expected_count - found_count} единиц")
                    self.test_results["critical_issues"].append(
                        f"Заявка {app_number}: найдено {found_count} из {expected_count} единиц"
                    )
            else:
                self.log(f"   ⚠️ Неожиданная заявка (не в списке ожидаемых)")
        
        # Проверка ожидаемых заявок
        self.log(f"\n🎯 ПРОВЕРКА ОЖИДАЕМЫХ ЗАЯВОК:")
        for expected_app in EXPECTED_APPLICATIONS:
            if expected_app in applications_found:
                found_count = len(applications_found[expected_app])
                expected_count = EXPECTED_UNITS_PER_APP[expected_app]
                self.log(f"✅ Заявка {expected_app}: найдена ({found_count}/{expected_count})")
            else:
                self.log(f"❌ Заявка {expected_app}: НЕ НАЙДЕНА!")
                self.test_results["critical_issues"].append(f"Заявка {expected_app} полностью отсутствует в API ответе")
        
        # Сохраняем анализ
        self.test_results["applications_analysis"] = {
            app: len(cargos) for app, cargos in applications_found.items()
        }
    
    def test_placement_progress_api(self):
        """Дополнительная проверка через API placement-progress"""
        self.log("\n🔄 ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: API placement-progress")
        self.log("-" * 60)
        
        try:
            response = self.session.get(f"{API_BASE}/operator/placement-progress")
            
            if response.status_code == 200:
                data = response.json()
                
                total_units = data.get("total_units", 0)
                placed_units = data.get("placed_units", 0)
                pending_units = data.get("pending_units", 0)
                progress_percentage = data.get("progress_percentage", 0)
                
                self.log(f"📊 Общая статистика размещения:")
                self.log(f"   Всего единиц: {total_units}")
                self.log(f"   Размещено единиц: {placed_units}")
                self.log(f"   Ожидает размещения: {pending_units}")
                self.log(f"   Прогресс: {progress_percentage}%")
                
                # Сравнение с layout-with-cargo
                layout_found = self.test_results["placement_records_found"]
                self.log(f"\n🔍 СРАВНЕНИЕ С layout-with-cargo:")
                self.log(f"   placement-progress placed_units: {placed_units}")
                self.log(f"   layout-with-cargo найдено: {layout_found}")
                
                if placed_units == layout_found:
                    self.log(f"   ✅ Данные синхронизированы")
                else:
                    self.log(f"   ❌ РАСХОЖДЕНИЕ: {abs(placed_units - layout_found)} единиц")
                    self.test_results["critical_issues"].append(
                        f"Расхождение между placement-progress ({placed_units}) и layout-with-cargo ({layout_found})"
                    )
                
                return True
            else:
                self.log(f"❌ Ошибка API placement-progress: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при проверке placement-progress: {e}", "ERROR")
            return False
    
    def generate_comprehensive_report(self):
        """Генерация комплексного диагностического отчета"""
        self.log("\n📋 КОМПЛЕКСНЫЙ ДИАГНОСТИЧЕСКИЙ ОТЧЕТ:")
        self.log("=" * 80)
        
        # Заголовок
        self.log(f"🎯 КРИТИЧЕСКАЯ ДИАГНОСТИКА: Склад 001 и API layout-with-cargo")
        self.log(f"📅 Время диагностики: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"🏢 Целевой склад: {TARGET_WAREHOUSE}")
        
        # Результаты по этапам
        self.log(f"\n📊 РЕЗУЛЬТАТЫ ДИАГНОСТИКИ:")
        self.log(f"  1. ✅ Авторизация оператора: {'✅ УСПЕШНО' if self.test_results['auth_success'] else '❌ НЕУДАЧНО'}")
        self.log(f"  2. ✅ Поиск склада 001: {'✅ НАЙДЕН' if self.test_results['warehouse_found'] else '❌ НЕ НАЙДЕН'}")
        
        if self.test_results['warehouse_found']:
            method = self.test_results['warehouse_search_method']
            self.log(f"     Метод поиска: {method}")
            
            if self.test_results['warehouse_details']:
                details = self.test_results['warehouse_details']
                self.log(f"     ID склада: {details.get('id', 'N/A')}")
                self.log(f"     Номер склада: {details.get('warehouse_id_number', 'НЕТ')}")
                self.log(f"     Название: {details.get('name', 'N/A')}")
        
        self.log(f"  3. ✅ Доступ к API layout-with-cargo: {'✅ ДОСТУПЕН' if self.test_results['api_accessible'] else '❌ НЕДОСТУПЕН'}")
        
        # Критические данные
        found_records = self.test_results["placement_records_found"]
        expected_records = self.test_results["expected_records"]
        missing_records = self.test_results["missing_records"]
        
        self.log(f"\n🎯 КРИТИЧЕСКИЕ ДАННЫЕ:")
        self.log(f"  Ожидалось записей: {expected_records}")
        self.log(f"  Найдено записей: {found_records}")
        self.log(f"  Отсутствует записей: {missing_records}")
        
        if missing_records > 0:
            self.log(f"  ❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: API пропускает {missing_records} из {expected_records} записей!")
        else:
            self.log(f"  ✅ Все записи найдены")
        
        # Анализ по заявкам
        if self.test_results["applications_analysis"]:
            self.log(f"\n📋 АНАЛИЗ ПО ЗАЯВКАМ:")
            for app_number, found_count in self.test_results["applications_analysis"].items():
                expected_count = EXPECTED_UNITS_PER_APP.get(app_number, 0)
                if expected_count > 0:
                    status = "✅" if found_count == expected_count else "❌"
                    self.log(f"  {status} Заявка {app_number}: {found_count}/{expected_count}")
                else:
                    self.log(f"  ⚠️ Заявка {app_number}: {found_count} (неожиданная)")
        
        # Критические проблемы
        if self.test_results["critical_issues"]:
            self.log(f"\n⚠️ КРИТИЧЕСКИЕ ПРОБЛЕМЫ ({len(self.test_results['critical_issues'])} шт.):")
            for i, issue in enumerate(self.test_results["critical_issues"], 1):
                self.log(f"  {i}. {issue}")
        
        # Финальный вывод
        self.log(f"\n🎯 ДИАГНОЗ:")
        if missing_records == 0 and not self.test_results["critical_issues"]:
            self.log("✅ API layout-with-cargo работает корректно")
            self.log("📊 Все ожидаемые записи найдены")
        else:
            self.log("❌ ОБНАРУЖЕНЫ КРИТИЧЕСКИЕ ПРОБЛЕМЫ!")
            self.log(f"🔍 API layout-with-cargo находит только {found_records} из {expected_records} записей")
            self.log("⚠️ Требуется исправление логики поиска placement_records")
            
            # Рекомендации
            self.log(f"\n💡 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ:")
            self.log("  1. Проверить логику поиска placement_records в API")
            self.log("  2. Убедиться что поиск работает по всем вариантам warehouse_id")
            self.log("  3. Проверить фильтрацию записей в базе данных")
            self.log("  4. Добавить логирование для диагностики пропущенных записей")
            
            if not self.test_results["warehouse_found"]:
                self.log("  5. КРИТИЧНО: Исправить идентификацию склада 001")
                self.log("     - Добавить warehouse_id_number = '001' в базу данных")
                self.log("     - Или обновить логику поиска склада в API")
        
        return missing_records == 0 and not self.test_results["critical_issues"]
    
    def run_comprehensive_diagnosis(self):
        """Запуск комплексной диагностики"""
        self.log("🚀 ЗАПУСК КОМПЛЕКСНОЙ ДИАГНОСТИКИ СКЛАДА 001")
        self.log("=" * 80)
        
        # 1. Авторизация
        if not self.authenticate_warehouse_operator():
            self.log("❌ ДИАГНОСТИКА ПРЕРВАНА: Не удалось авторизоваться", "ERROR")
            return False
        
        # 2. Получение информации о всех складах
        if not self.get_all_warehouses_info():
            self.log("❌ ДИАГНОСТИКА ПРЕРВАНА: Не удалось получить информацию о складах", "ERROR")
            return False
        
        # 3. Комплексный поиск склада 001
        if not self.find_warehouse_001_comprehensive():
            self.log("❌ ДИАГНОСТИКА ПРЕРВАНА: Склад 001 не найден", "ERROR")
            return False
        
        # 4. Тестирование API layout-with-cargo
        if not self.test_layout_with_cargo_api():
            self.log("❌ ДИАГНОСТИКА ПРЕРВАНА: API недоступен", "ERROR")
            return False
        
        # 5. Дополнительная проверка через placement-progress
        self.test_placement_progress_api()
        
        # 6. Генерация комплексного диагностического отчета
        diagnosis_success = self.generate_comprehensive_report()
        
        return diagnosis_success

def main():
    """Главная функция"""
    diagnoser = ComprehensiveWarehouse001Diagnoser()
    
    try:
        success = diagnoser.run_comprehensive_diagnosis()
        
        if success:
            print("\n" + "="*80)
            print("✅ КОМПЛЕКСНАЯ ДИАГНОСТИКА ЗАВЕРШЕНА: ПРОБЛЕМ НЕ ОБНАРУЖЕНО")
            print("📊 API layout-with-cargo работает корректно")
            print("🎯 Все ожидаемые записи найдены")
            sys.exit(0)
        else:
            print("\n" + "="*80)
            print("❌ КОМПЛЕКСНАЯ ДИАГНОСТИКА ЗАВЕРШЕНА: КРИТИЧЕСКИЕ ПРОБЛЕМЫ ОБНАРУЖЕНЫ!")
            print("🔍 API layout-with-cargo находит не все размещенные единицы")
            print("⚠️ Требуется исправление логики поиска placement_records")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Диагностика прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
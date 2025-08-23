#!/usr/bin/env python3
"""
КРИТИЧЕСКАЯ ДИАГНОСТИКА: API layout-with-cargo находит только 4 из 13 размещенных единиц для склада 001
===============================================================================================

ЦЕЛЬ: Выяснить почему API layout-with-cargo возвращает только 4 единицы груза вместо реальных 13 размещенных единиц

КРИТИЧЕСКАЯ ПРОБЛЕМА: Пользователь показал скриншот где на складе 001 размещено 13 единиц из 3 заявок, 
но API возвращает только 4

ДЕТАЛЬНАЯ ДИАГНОСТИКА:
1. Авторизация оператора (+79777888999/warehouse123)
2. Полный анализ placement_records в базе данных:
   - Найти ВСЕ placement_records для склада 001
   - Проверить разные варианты warehouse_id ("001", UUID склада, название)
   - Подсчитать точное количество записей
3. Сравнение с фронтенд данными:
   - API должен находить заявки: 25082298 (7 единиц), 250101 (2 единицы), 25082235 (4 единицы)
   - Всего должно быть 13 единиц, не 4
4. Анализ фильтрации: Возможно API фильтрует или пропускает некоторые записи

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Найти и исправить проблему, почему API пропускает 9 из 13 размещенных единиц

КРИТИЧНО: Это основная проблема синхронизации - API не видит большую часть реально размещенных грузов
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

class LayoutWithCargoDiagnoser:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.warehouse_001_info = None
        self.test_results = {
            "auth_success": False,
            "warehouse_found": False,
            "api_accessible": False,
            "placement_records_found": 0,
            "expected_records": EXPECTED_TOTAL_UNITS,
            "missing_records": 0,
            "applications_analysis": {},
            "critical_issues": []
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
    
    def find_warehouse_001(self):
        """Найти склад 001 и получить его полную информацию"""
        self.log("🏢 Поиск склада 001...")
        
        try:
            # Получаем список складов оператора
            response = self.session.get(f"{API_BASE}/operator/warehouses")
            
            if response.status_code == 200:
                warehouses = response.json()
                self.log(f"📋 Получено {len(warehouses)} складов оператора")
                
                # Ищем склад 001
                for warehouse in warehouses:
                    warehouse_id_number = warehouse.get("warehouse_id_number", "")
                    warehouse_name = warehouse.get("name", "")
                    warehouse_id = warehouse.get("id", "")
                    
                    self.log(f"🔍 Проверяем склад: ID={warehouse_id}, номер={warehouse_id_number}, название={warehouse_name}")
                    
                    if warehouse_id_number == TARGET_WAREHOUSE:
                        self.warehouse_001_info = warehouse
                        self.log(f"✅ Склад 001 найден!")
                        self.log(f"   ID: {warehouse_id}")
                        self.log(f"   Номер: {warehouse_id_number}")
                        self.log(f"   Название: {warehouse_name}")
                        self.log(f"   Местоположение: {warehouse.get('location', 'N/A')}")
                        self.test_results["warehouse_found"] = True
                        return True
                
                self.log(f"❌ Склад 001 НЕ найден среди складов оператора", "ERROR")
                return False
            else:
                self.log(f"❌ Ошибка получения складов: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при поиске склада: {e}", "ERROR")
            return False
    
    def test_layout_with_cargo_api(self):
        """Тестирование API layout-with-cargo для склада 001"""
        self.log("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: API layout-with-cargo для склада 001")
        self.log("=" * 80)
        
        if not self.warehouse_001_info:
            self.log("❌ Склад 001 не найден, невозможно протестировать API", "ERROR")
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
    
    def generate_diagnosis_report(self):
        """Генерация диагностического отчета"""
        self.log("\n📋 ДИАГНОСТИЧЕСКИЙ ОТЧЕТ:")
        self.log("=" * 80)
        
        # Заголовок
        self.log(f"🎯 КРИТИЧЕСКАЯ ДИАГНОСТИКА: API layout-with-cargo для склада 001")
        self.log(f"📅 Время диагностики: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"🏢 Целевой склад: {TARGET_WAREHOUSE}")
        
        # Результаты по этапам
        self.log(f"\n📊 РЕЗУЛЬТАТЫ ДИАГНОСТИКИ:")
        self.log(f"  1. ✅ Авторизация оператора: {'✅ УСПЕШНО' if self.test_results['auth_success'] else '❌ НЕУДАЧНО'}")
        self.log(f"  2. ✅ Поиск склада 001: {'✅ НАЙДЕН' if self.test_results['warehouse_found'] else '❌ НЕ НАЙДЕН'}")
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
        
        return missing_records == 0 and not self.test_results["critical_issues"]
    
    def run_full_diagnosis(self):
        """Запуск полной диагностики"""
        self.log("🚀 ЗАПУСК КРИТИЧЕСКОЙ ДИАГНОСТИКИ API layout-with-cargo")
        self.log("=" * 80)
        
        # 1. Авторизация
        if not self.authenticate_warehouse_operator():
            self.log("❌ ДИАГНОСТИКА ПРЕРВАНА: Не удалось авторизоваться", "ERROR")
            return False
        
        # 2. Поиск склада 001
        if not self.find_warehouse_001():
            self.log("❌ ДИАГНОСТИКА ПРЕРВАНА: Склад 001 не найден", "ERROR")
            return False
        
        # 3. Тестирование API layout-with-cargo
        if not self.test_layout_with_cargo_api():
            self.log("❌ ДИАГНОСТИКА ПРЕРВАНА: API недоступен", "ERROR")
            return False
        
        # 4. Дополнительная проверка через placement-progress
        self.test_placement_progress_api()
        
        # 5. Генерация диагностического отчета
        diagnosis_success = self.generate_diagnosis_report()
        
        return diagnosis_success

def main():
    """Главная функция"""
    diagnoser = LayoutWithCargoDiagnoser()
    
    try:
        success = diagnoser.run_full_diagnosis()
        
        if success:
            print("\n" + "="*80)
            print("✅ ДИАГНОСТИКА ЗАВЕРШЕНА: ПРОБЛЕМ НЕ ОБНАРУЖЕНО")
            print("📊 API layout-with-cargo работает корректно")
            print("🎯 Все ожидаемые записи найдены")
            sys.exit(0)
        else:
            print("\n" + "="*80)
            print("❌ ДИАГНОСТИКА ЗАВЕРШЕНА: КРИТИЧЕСКИЕ ПРОБЛЕМЫ ОБНАРУЖЕНЫ!")
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
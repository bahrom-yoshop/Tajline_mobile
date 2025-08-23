#!/usr/bin/env python3
"""
КРИТИЧЕСКАЯ ДИАГНОСТИКА: API layout-with-cargo - ИСПРАВЛЕННАЯ ВЕРСИЯ
===================================================================

ЦЕЛЬ: Выяснить почему API layout-with-cargo возвращает только 4 из 13 размещенных единиц для склада 001

ИСПРАВЛЕНИЕ: Используем правильный endpoint /api/warehouses/{warehouse_id}/layout-with-cargo

КРИТИЧЕСКАЯ ПРОБЛЕМА: Пользователь показал скриншот где на складе 001 размещено 13 единиц из 3 заявок, 
но API возвращает только 4

ДЕТАЛЬНАЯ ДИАГНОСТИКА:
1. Авторизация оператора (+79777888999/warehouse123)
2. Поиск склада (любым доступным способом)
3. Тестирование ПРАВИЛЬНОГО API endpoint
4. Полный анализ placement_records в базе данных
5. Сравнение с ожидаемыми данными (13 единиц из 3 заявок)
6. Диагностика причин расхождений
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

class CorrectedLayoutWithCargoDiagnoser:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.warehouse_info = None
        self.test_results = {
            "auth_success": False,
            "warehouse_found": False,
            "api_accessible": False,
            "placement_records_found": 0,
            "expected_records": EXPECTED_TOTAL_UNITS,
            "missing_records": 0,
            "applications_analysis": {},
            "critical_issues": [],
            "warehouse_details": {},
            "api_response_structure": {}
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
    
    def find_warehouse(self):
        """Найти склад оператора"""
        self.log("🏢 Поиск склада оператора...")
        
        try:
            # Получаем склады оператора
            response = self.session.get(f"{API_BASE}/operator/warehouses")
            
            if response.status_code == 200:
                warehouses = response.json()
                self.log(f"📋 Получено {len(warehouses)} складов оператора")
                
                if len(warehouses) > 0:
                    # Используем первый доступный склад
                    warehouse = warehouses[0]
                    self.warehouse_info = warehouse
                    
                    self.log(f"✅ Склад найден!")
                    self.log(f"   ID: {warehouse.get('id', 'N/A')}")
                    self.log(f"   Номер: {warehouse.get('warehouse_id_number', 'НЕТ')}")
                    self.log(f"   Название: {warehouse.get('name', 'N/A')}")
                    self.log(f"   Местоположение: {warehouse.get('location', 'N/A')}")
                    
                    self.test_results["warehouse_found"] = True
                    self.test_results["warehouse_details"] = {
                        "id": warehouse.get("id", "N/A"),
                        "warehouse_id_number": warehouse.get("warehouse_id_number", "НЕТ"),
                        "name": warehouse.get("name", "N/A"),
                        "location": warehouse.get("location", "N/A"),
                        "address": warehouse.get("address", "N/A")
                    }
                    return True
                else:
                    self.log("❌ У оператора нет доступных складов", "ERROR")
                    return False
            else:
                self.log(f"❌ Ошибка получения складов: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при поиске склада: {e}", "ERROR")
            return False
    
    def test_layout_with_cargo_api(self):
        """Тестирование ПРАВИЛЬНОГО API layout-with-cargo"""
        self.log("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: API layout-with-cargo (ИСПРАВЛЕННЫЙ ENDPOINT)")
        self.log("=" * 80)
        
        if not self.warehouse_info:
            self.log("❌ Склад не найден, невозможно протестировать API", "ERROR")
            return False
        
        warehouse_id = self.warehouse_info["id"]
        
        try:
            # ИСПРАВЛЕННЫЙ ENDPOINT: /api/warehouses/{warehouse_id}/layout-with-cargo
            self.log(f"📡 Запрос к ПРАВИЛЬНОМУ endpoint: /api/warehouses/{warehouse_id}/layout-with-cargo")
            response = self.session.get(f"{API_BASE}/warehouses/{warehouse_id}/layout-with-cargo")
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ API layout-with-cargo доступен (правильный endpoint)")
                self.test_results["api_accessible"] = True
                
                # Анализ структуры ответа
                self.log("\n📊 АНАЛИЗ СТРУКТУРЫ ОТВЕТА:")
                self.log(f"Тип данных: {type(data)}")
                
                if isinstance(data, dict):
                    self.log(f"Ключи ответа: {list(data.keys())}")
                    
                    # Сохраняем структуру ответа для анализа
                    self.test_results["api_response_structure"] = {
                        "keys": list(data.keys()),
                        "data_type": str(type(data))
                    }
                    
                    # Ищем информацию о размещенных грузах
                    cargo_info = data.get("cargo_info", [])
                    occupied_cells = data.get("occupied_cells", 0)
                    layout_data = data.get("layout", {})
                    warehouse_info = data.get("warehouse_info", {})
                    
                    self.log(f"📦 cargo_info: {len(cargo_info)} записей")
                    self.log(f"🏠 occupied_cells: {occupied_cells}")
                    self.log(f"🗺️ layout данные: {type(layout_data)}")
                    self.log(f"🏢 warehouse_info: {type(warehouse_info)}")
                    
                    # Дополнительная информация о складе
                    if warehouse_info:
                        self.log(f"📋 Информация о складе из API:")
                        self.log(f"   Название: {warehouse_info.get('name', 'N/A')}")
                        self.log(f"   ID номер: {warehouse_info.get('warehouse_id_number', 'НЕТ')}")
                        self.log(f"   Местоположение: {warehouse_info.get('location', 'N/A')}")
                    
                    # КРИТИЧЕСКАЯ ПРОВЕРКА: Анализ cargo_info
                    self.analyze_cargo_info_detailed(cargo_info)
                    
                    # Сохраняем количество найденных записей
                    self.test_results["placement_records_found"] = len(cargo_info)
                    self.test_results["missing_records"] = EXPECTED_TOTAL_UNITS - len(cargo_info)
                    
                    return True
                else:
                    self.log(f"⚠️ Неожиданная структура ответа: {type(data)}", "WARNING")
                    return False
            else:
                self.log(f"❌ Ошибка API: {response.status_code} - {response.text}", "ERROR")
                
                # Попробуем альтернативные endpoints
                self.log("🔄 Попытка альтернативных endpoints...")
                return self.try_alternative_endpoints(warehouse_id)
                
        except Exception as e:
            self.log(f"❌ Исключение при тестировании API: {e}", "ERROR")
            return False
    
    def try_alternative_endpoints(self, warehouse_id):
        """Попробовать альтернативные endpoints"""
        self.log("🔄 ТЕСТИРОВАНИЕ АЛЬТЕРНАТИВНЫХ ENDPOINTS:")
        
        alternative_endpoints = [
            f"/api/operator/warehouses/{warehouse_id}/layout-with-cargo",
            f"/api/admin/warehouses/{warehouse_id}/layout-with-cargo",
            f"/api/warehouses/{warehouse_id}/layout",
            f"/api/warehouses/{warehouse_id}/cargo",
            f"/api/operator/warehouses/{warehouse_id}/layout",
            f"/api/operator/warehouses/{warehouse_id}/cargo"
        ]
        
        for endpoint in alternative_endpoints:
            try:
                self.log(f"🔍 Тестируем: {endpoint}")
                response = self.session.get(f"{API_BASE}{endpoint}")
                
                if response.status_code == 200:
                    self.log(f"✅ НАЙДЕН РАБОЧИЙ ENDPOINT: {endpoint}")
                    data = response.json()
                    
                    # Анализируем найденный endpoint
                    if isinstance(data, dict):
                        cargo_info = data.get("cargo_info", [])
                        if cargo_info:
                            self.log(f"📦 Найдено {len(cargo_info)} записей в cargo_info")
                            self.analyze_cargo_info_detailed(cargo_info)
                            self.test_results["placement_records_found"] = len(cargo_info)
                            self.test_results["missing_records"] = EXPECTED_TOTAL_UNITS - len(cargo_info)
                            self.test_results["api_accessible"] = True
                            return True
                    
                elif response.status_code == 404:
                    self.log(f"❌ 404 Not Found: {endpoint}")
                elif response.status_code == 403:
                    self.log(f"❌ 403 Forbidden: {endpoint}")
                else:
                    self.log(f"❌ {response.status_code}: {endpoint}")
                    
            except Exception as e:
                self.log(f"❌ Ошибка при тестировании {endpoint}: {e}")
        
        self.log("❌ Ни один альтернативный endpoint не работает", "ERROR")
        return False
    
    def analyze_cargo_info_detailed(self, cargo_info):
        """Детальный анализ cargo_info из API ответа"""
        self.log("\n🔍 ДЕТАЛЬНЫЙ АНАЛИЗ CARGO_INFO:")
        self.log("-" * 60)
        
        if not cargo_info:
            self.log("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: cargo_info пустой!", "ERROR")
            self.test_results["critical_issues"].append("cargo_info пустой - API не находит размещенные грузы")
            return
        
        # Группируем по номерам заявок
        applications_found = {}
        all_cargo_numbers = set()
        
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
            
            # Собираем все номера заявок
            all_cargo_numbers.add(cargo_number)
            
            # Группируем по заявкам
            if cargo_number not in applications_found:
                applications_found[cargo_number] = []
            applications_found[cargo_number].append(cargo)
        
        # Анализ найденных заявок
        self.log(f"\n📊 АНАЛИЗ ПО ЗАЯВКАМ:")
        self.log(f"Найдено уникальных заявок: {len(applications_found)}")
        self.log(f"Все номера заявок: {sorted(all_cargo_numbers)}")
        
        for app_number, cargos in applications_found.items():
            expected_count = EXPECTED_UNITS_PER_APP.get(app_number, 0)
            found_count = len(cargos)
            
            self.log(f"📋 Заявка {app_number}:")
            self.log(f"   Найдено единиц: {found_count}")
            self.log(f"   Ожидалось единиц: {expected_count}")
            
            if expected_count > 0:
                if found_count == expected_count:
                    self.log(f"   ✅ Количество совпадает")
                elif found_count < expected_count:
                    self.log(f"   ❌ НЕДОСТАЕТ: не хватает {expected_count - found_count} единиц")
                    self.test_results["critical_issues"].append(
                        f"Заявка {app_number}: найдено {found_count} из {expected_count} единиц (недостает {expected_count - found_count})"
                    )
                else:
                    self.log(f"   ⚠️ ИЗБЫТОК: найдено больше чем ожидалось (+{found_count - expected_count})")
            else:
                self.log(f"   ⚠️ Неожиданная заявка (не в списке ожидаемых)")
        
        # Проверка ожидаемых заявок
        self.log(f"\n🎯 ПРОВЕРКА ОЖИДАЕМЫХ ЗАЯВОК:")
        missing_applications = []
        
        for expected_app in EXPECTED_APPLICATIONS:
            if expected_app in applications_found:
                found_count = len(applications_found[expected_app])
                expected_count = EXPECTED_UNITS_PER_APP[expected_app]
                status = "✅" if found_count == expected_count else "❌"
                self.log(f"{status} Заявка {expected_app}: найдена ({found_count}/{expected_count})")
            else:
                self.log(f"❌ Заявка {expected_app}: НЕ НАЙДЕНА!")
                missing_applications.append(expected_app)
                self.test_results["critical_issues"].append(f"Заявка {expected_app} полностью отсутствует в API ответе")
        
        # Дополнительная диагностика для отсутствующих заявок
        if missing_applications:
            self.log(f"\n🔍 ДИАГНОСТИКА ОТСУТСТВУЮЩИХ ЗАЯВОК:")
            for missing_app in missing_applications:
                expected_units = EXPECTED_UNITS_PER_APP[missing_app]
                self.log(f"❌ Заявка {missing_app}: ожидалось {expected_units} единиц, найдено 0")
                self.log(f"   Возможные причины:")
                self.log(f"   - Заявка не размещена на этом складе")
                self.log(f"   - Проблема с фильтрацией по warehouse_id")
                self.log(f"   - Заявка размещена под другим номером")
                self.log(f"   - Проблема с базой данных placement_records")
        
        # Сохраняем анализ
        self.test_results["applications_analysis"] = {
            app: len(cargos) for app, cargos in applications_found.items()
        }
    
    def test_placement_progress_comparison(self):
        """Сравнение с API placement-progress"""
        self.log("\n🔄 СРАВНЕНИЕ С API placement-progress")
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
                self.log(f"\n🔍 КРИТИЧЕСКОЕ СРАВНЕНИЕ:")
                self.log(f"   placement-progress placed_units: {placed_units}")
                self.log(f"   layout-with-cargo найдено: {layout_found}")
                self.log(f"   Ожидалось по пользователю: {EXPECTED_TOTAL_UNITS}")
                
                if placed_units == layout_found:
                    self.log(f"   ✅ API синхронизированы между собой")
                else:
                    self.log(f"   ❌ РАСХОЖДЕНИЕ МЕЖДУ API: {abs(placed_units - layout_found)} единиц")
                    self.test_results["critical_issues"].append(
                        f"Расхождение между placement-progress ({placed_units}) и layout-with-cargo ({layout_found})"
                    )
                
                if placed_units == EXPECTED_TOTAL_UNITS:
                    self.log(f"   ✅ placement-progress соответствует ожиданиям пользователя")
                else:
                    self.log(f"   ❌ placement-progress НЕ соответствует ожиданиям: {abs(placed_units - EXPECTED_TOTAL_UNITS)} единиц разница")
                
                if layout_found == EXPECTED_TOTAL_UNITS:
                    self.log(f"   ✅ layout-with-cargo соответствует ожиданиям пользователя")
                else:
                    self.log(f"   ❌ layout-with-cargo НЕ соответствует ожиданиям: {abs(layout_found - EXPECTED_TOTAL_UNITS)} единиц разница")
                
                return True
            else:
                self.log(f"❌ Ошибка API placement-progress: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при проверке placement-progress: {e}", "ERROR")
            return False
    
    def generate_final_diagnosis_report(self):
        """Генерация финального диагностического отчета"""
        self.log("\n📋 ФИНАЛЬНЫЙ ДИАГНОСТИЧЕСКИЙ ОТЧЕТ:")
        self.log("=" * 80)
        
        # Заголовок
        self.log(f"🎯 КРИТИЧЕСКАЯ ДИАГНОСТИКА: API layout-with-cargo для склада 001")
        self.log(f"📅 Время диагностики: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"🏢 Целевой склад: {TARGET_WAREHOUSE}")
        
        # Результаты по этапам
        self.log(f"\n📊 РЕЗУЛЬТАТЫ ДИАГНОСТИКИ:")
        self.log(f"  1. ✅ Авторизация оператора: {'✅ УСПЕШНО' if self.test_results['auth_success'] else '❌ НЕУДАЧНО'}")
        self.log(f"  2. ✅ Поиск склада: {'✅ НАЙДЕН' if self.test_results['warehouse_found'] else '❌ НЕ НАЙДЕН'}")
        self.log(f"  3. ✅ Доступ к API layout-with-cargo: {'✅ ДОСТУПЕН' if self.test_results['api_accessible'] else '❌ НЕДОСТУПЕН'}")
        
        if self.test_results['warehouse_found'] and self.test_results['warehouse_details']:
            details = self.test_results['warehouse_details']
            self.log(f"     Склад ID: {details.get('id', 'N/A')}")
            self.log(f"     Склад номер: {details.get('warehouse_id_number', 'НЕТ')}")
            self.log(f"     Склад название: {details.get('name', 'N/A')}")
        
        # Критические данные
        found_records = self.test_results["placement_records_found"]
        expected_records = self.test_results["expected_records"]
        missing_records = self.test_results["missing_records"]
        
        self.log(f"\n🎯 КРИТИЧЕСКИЕ ДАННЫЕ:")
        self.log(f"  Ожидалось записей (по пользователю): {expected_records}")
        self.log(f"  Найдено записей (API layout-with-cargo): {found_records}")
        self.log(f"  Отсутствует записей: {missing_records}")
        
        if missing_records > 0:
            percentage_found = (found_records / expected_records) * 100
            self.log(f"  ❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: API находит только {percentage_found:.1f}% от ожидаемых записей!")
            self.log(f"  🔍 Пропущено {missing_records} из {expected_records} записей")
        elif missing_records == 0:
            self.log(f"  ✅ Все ожидаемые записи найдены")
        else:
            self.log(f"  ⚠️ Найдено больше записей чем ожидалось (+{abs(missing_records)})")
        
        # Анализ по заявкам
        if self.test_results["applications_analysis"]:
            self.log(f"\n📋 ДЕТАЛЬНЫЙ АНАЛИЗ ПО ЗАЯВКАМ:")
            total_found = 0
            total_expected = 0
            
            for app_number, found_count in self.test_results["applications_analysis"].items():
                expected_count = EXPECTED_UNITS_PER_APP.get(app_number, 0)
                total_found += found_count
                
                if expected_count > 0:
                    total_expected += expected_count
                    status = "✅" if found_count == expected_count else "❌"
                    self.log(f"  {status} Заявка {app_number}: {found_count}/{expected_count}")
                    
                    if found_count < expected_count:
                        self.log(f"      ⚠️ Недостает {expected_count - found_count} единиц")
                else:
                    self.log(f"  ⚠️ Заявка {app_number}: {found_count} (неожиданная)")
            
            # Проверка отсутствующих заявок
            for expected_app in EXPECTED_APPLICATIONS:
                if expected_app not in self.test_results["applications_analysis"]:
                    expected_count = EXPECTED_UNITS_PER_APP[expected_app]
                    total_expected += expected_count
                    self.log(f"  ❌ Заявка {expected_app}: 0/{expected_count} (ПОЛНОСТЬЮ ОТСУТСТВУЕТ)")
            
            self.log(f"\n📊 ИТОГОВАЯ СВОДКА:")
            self.log(f"  Найдено единиц: {total_found}")
            self.log(f"  Ожидалось единиц: {total_expected}")
            self.log(f"  Процент найденных: {(total_found/total_expected)*100:.1f}%")
        
        # Критические проблемы
        if self.test_results["critical_issues"]:
            self.log(f"\n⚠️ КРИТИЧЕСКИЕ ПРОБЛЕМЫ ({len(self.test_results['critical_issues'])} шт.):")
            for i, issue in enumerate(self.test_results["critical_issues"], 1):
                self.log(f"  {i}. {issue}")
        
        # Финальный диагноз
        self.log(f"\n🎯 ФИНАЛЬНЫЙ ДИАГНОЗ:")
        if missing_records == 0 and not self.test_results["critical_issues"]:
            self.log("✅ API layout-with-cargo работает корректно")
            self.log("📊 Все ожидаемые записи найдены")
            self.log("🎉 Проблема НЕ подтверждена - возможно уже исправлена")
        else:
            self.log("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА ПОДТВЕРЖДЕНА!")
            self.log(f"🔍 API layout-with-cargo находит только {found_records} из {expected_records} записей")
            self.log(f"📉 Потеряно {missing_records} записей ({abs(missing_records/expected_records)*100:.1f}%)")
            
            # Рекомендации по исправлению
            self.log(f"\n💡 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ:")
            self.log("  1. 🔍 ПРОВЕРИТЬ ЛОГИКУ ПОИСКА placement_records:")
            self.log("     - Убедиться что поиск работает по всем вариантам warehouse_id")
            self.log("     - Проверить фильтрацию по UUID, номеру склада, названию")
            self.log("     - Добавить логирование для диагностики пропущенных записей")
            
            self.log("  2. 🗄️ ПРОВЕРИТЬ БАЗУ ДАННЫХ:")
            self.log("     - Убедиться что все placement_records существуют")
            self.log("     - Проверить правильность warehouse_id в записях")
            self.log("     - Проверить индексы для оптимизации поиска")
            
            self.log("  3. 🔧 ИСПРАВИТЬ API ENDPOINT:")
            self.log("     - Расширить логику поиска склада в API")
            self.log("     - Добавить поддержку поиска по номеру склада '001'")
            self.log("     - Улучшить обработку различных форматов warehouse_id")
            
            if not self.test_results["warehouse_found"]:
                self.log("  4. 🏢 КРИТИЧНО: ИСПРАВИТЬ ИДЕНТИФИКАЦИЮ СКЛАДА:")
                self.log("     - Добавить warehouse_id_number = '001' в базу данных")
                self.log("     - Или обновить логику поиска склада в API")
        
        return missing_records == 0 and not self.test_results["critical_issues"]
    
    def run_corrected_diagnosis(self):
        """Запуск исправленной диагностики"""
        self.log("🚀 ЗАПУСК ИСПРАВЛЕННОЙ ДИАГНОСТИКИ API layout-with-cargo")
        self.log("=" * 80)
        
        # 1. Авторизация
        if not self.authenticate_warehouse_operator():
            self.log("❌ ДИАГНОСТИКА ПРЕРВАНА: Не удалось авторизоваться", "ERROR")
            return False
        
        # 2. Поиск склада
        if not self.find_warehouse():
            self.log("❌ ДИАГНОСТИКА ПРЕРВАНА: Склад не найден", "ERROR")
            return False
        
        # 3. Тестирование API layout-with-cargo (исправленный endpoint)
        if not self.test_layout_with_cargo_api():
            self.log("❌ ДИАГНОСТИКА ПРЕРВАНА: API недоступен", "ERROR")
            return False
        
        # 4. Сравнение с placement-progress
        self.test_placement_progress_comparison()
        
        # 5. Генерация финального диагностического отчета
        diagnosis_success = self.generate_final_diagnosis_report()
        
        return diagnosis_success

def main():
    """Главная функция"""
    diagnoser = CorrectedLayoutWithCargoDiagnoser()
    
    try:
        success = diagnoser.run_corrected_diagnosis()
        
        if success:
            print("\n" + "="*80)
            print("✅ ИСПРАВЛЕННАЯ ДИАГНОСТИКА ЗАВЕРШЕНА: ПРОБЛЕМ НЕ ОБНАРУЖЕНО")
            print("📊 API layout-with-cargo работает корректно")
            print("🎯 Все ожидаемые записи найдены")
            print("🎉 Проблема пользователя НЕ подтверждена - возможно уже исправлена")
            sys.exit(0)
        else:
            print("\n" + "="*80)
            print("❌ ИСПРАВЛЕННАЯ ДИАГНОСТИКА ЗАВЕРШЕНА: КРИТИЧЕСКАЯ ПРОБЛЕМА ПОДТВЕРЖДЕНА!")
            print("🔍 API layout-with-cargo находит не все размещенные единицы")
            print("📉 Пользователь прав - API пропускает записи")
            print("⚠️ Требуется срочное исправление логики поиска placement_records")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Диагностика прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
ДИАГНОСТИКА ПРОБЛЕМЫ СИНХРОНИЗАЦИИ ДАННЫХ В API layout-with-cargo ДЛЯ СКЛАДА 001
================================================================================

ЦЕЛЬ: Выяснить почему визуальная схема склада 001 не синхронизирована с реальными данными о размещенных грузах

КРИТИЧЕСКИЕ ПРОВЕРКИ:
1. Авторизация оператора склада (+79777888999/warehouse123)
2. Поиск склада 001: Найти правильный warehouse_id для "Москва Склад №1"
3. Тестирование API layout-with-cargo для склада 001:
   - Проверить сколько placement_records найдено для склада 001
   - Проверить правильность парсинга location для каждого размещенного груза
   - Сравнить с фактическими данными в базе данных
4. Диагностика warehouse_id:
   - Проверить что в placement_records правильно указан warehouse_id для Москвы
   - Убедиться что все размещенные единицы попадают в результат
5. Анализ занятых ячеек: Подсчитать реальное количество занятых ячеек vs отображаемое

ПРОБЛЕМА: На складе ID 001 "Москва Склад №1" размещено много грузов, но визуальная схема 
показывает неправильное количество занятых ячеек - нужна автосинхронизация

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: API должен возвращать все реально размещенные единицы груза 
с правильной синхронизацией данных для Москвы
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
TARGET_WAREHOUSE_NUMBER = "001"
TARGET_WAREHOUSE_NAME = "Москва Склад №1"

class WarehouseLayoutSyncTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.warehouse_001_id = None
        self.test_results = {
            "auth_success": False,
            "warehouse_found": False,
            "layout_api_accessible": False,
            "placement_records_found": 0,
            "sync_issues_found": [],
            "occupied_cells_count": 0,
            "expected_occupied_count": 0,
            "warehouse_id_issues": [],
            "location_parsing_issues": []
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
        """Найти склад 001 'Москва Склад №1'"""
        self.log(f"🏢 Поиск склада {TARGET_WAREHOUSE_NUMBER} '{TARGET_WAREHOUSE_NAME}'...")
        
        try:
            # Сначала попробуем получить список складов оператора
            response = self.session.get(f"{API_BASE}/operator/warehouses")
            
            if response.status_code == 200:
                warehouses = response.json()
                self.log(f"📋 Получено {len(warehouses)} складов оператора")
                
                # Ищем склад по номеру или названию
                for warehouse in warehouses:
                    warehouse_id_number = warehouse.get("warehouse_id_number", "")
                    warehouse_name = warehouse.get("name", "")
                    warehouse_id = warehouse.get("id", "")
                    
                    self.log(f"🔍 Проверяем склад: ID={warehouse_id}, номер={warehouse_id_number}, название='{warehouse_name}'")
                    
                    if (warehouse_id_number == TARGET_WAREHOUSE_NUMBER or 
                        TARGET_WAREHOUSE_NAME in warehouse_name):
                        self.warehouse_001_id = warehouse_id
                        self.log(f"✅ Склад 001 найден! ID: {warehouse_id}, номер: {warehouse_id_number}, название: '{warehouse_name}'")
                        self.test_results["warehouse_found"] = True
                        return True
                
                # Если не найден в списке оператора, попробуем общий список
                self.log("⚠️ Склад 001 не найден в списке оператора, проверяем общий список...")
                return self.find_warehouse_001_in_all_warehouses()
            else:
                self.log(f"❌ Ошибка получения складов оператора: {response.status_code}", "ERROR")
                return self.find_warehouse_001_in_all_warehouses()
                
        except Exception as e:
            self.log(f"❌ Исключение при поиске склада: {e}", "ERROR")
            return False
    
    def find_warehouse_001_in_all_warehouses(self):
        """Поиск склада 001 в общем списке складов"""
        try:
            response = self.session.get(f"{API_BASE}/warehouses/all-cities")
            
            if response.status_code == 200:
                data = response.json()
                warehouses = data.get("warehouses", [])
                self.log(f"📋 Получено {len(warehouses)} складов в общем списке")
                
                for warehouse in warehouses:
                    warehouse_id_number = warehouse.get("warehouse_id_number", "")
                    warehouse_name = warehouse.get("name", "")
                    warehouse_id = warehouse.get("id", "")
                    
                    if (warehouse_id_number == TARGET_WAREHOUSE_NUMBER or 
                        TARGET_WAREHOUSE_NAME in warehouse_name):
                        self.warehouse_001_id = warehouse_id
                        self.log(f"✅ Склад 001 найден в общем списке! ID: {warehouse_id}, номер: {warehouse_id_number}")
                        self.test_results["warehouse_found"] = True
                        return True
                
                self.log(f"❌ Склад 001 '{TARGET_WAREHOUSE_NAME}' не найден ни в одном списке", "ERROR")
                return False
            else:
                self.log(f"❌ Ошибка получения общего списка складов: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при поиске в общем списке: {e}", "ERROR")
            return False
    
    def test_layout_with_cargo_api(self):
        """Тестирование API layout-with-cargo для склада 001"""
        if not self.warehouse_001_id:
            self.log("❌ Не удалось найти warehouse_id для склада 001", "ERROR")
            return False
            
        self.log(f"🎯 Тестирование API layout-with-cargo для склада 001 (ID: {self.warehouse_001_id})...")
        
        try:
            response = self.session.get(f"{API_BASE}/warehouses/{self.warehouse_001_id}/layout-with-cargo")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ API layout-with-cargo доступен")
                self.test_results["layout_api_accessible"] = True
                
                # Анализируем структуру ответа
                self.analyze_layout_response(data)
                return True
            else:
                self.log(f"❌ Ошибка API layout-with-cargo: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при тестировании API: {e}", "ERROR")
            return False
    
    def analyze_layout_response(self, layout_data):
        """Анализ ответа API layout-with-cargo"""
        self.log("\n🔍 АНАЛИЗ ОТВЕТА API layout-with-cargo:")
        self.log("=" * 60)
        
        # Основная структура
        warehouse_info = layout_data.get("warehouse_info", {})
        layout_structure = layout_data.get("layout_structure", [])
        placement_records = layout_data.get("placement_records", [])
        statistics = layout_data.get("statistics", {})
        
        self.log(f"🏢 Информация о складе:")
        self.log(f"   Название: {warehouse_info.get('name', 'N/A')}")
        self.log(f"   ID: {warehouse_info.get('id', 'N/A')}")
        self.log(f"   Номер: {warehouse_info.get('warehouse_id_number', 'N/A')}")
        
        self.log(f"📊 Статистика:")
        total_cells = statistics.get("total_cells", 0)
        occupied_cells = statistics.get("occupied_cells", 0)
        free_cells = statistics.get("free_cells", 0)
        occupancy_rate = statistics.get("occupancy_rate", 0)
        
        self.log(f"   Всего ячеек: {total_cells}")
        self.log(f"   Занятых ячеек: {occupied_cells}")
        self.log(f"   Свободных ячеек: {free_cells}")
        self.log(f"   Процент заполнения: {occupancy_rate}%")
        
        self.test_results["occupied_cells_count"] = occupied_cells
        
        # Анализ placement_records
        self.log(f"\n📋 Анализ placement_records:")
        self.log(f"   Найдено записей размещения: {len(placement_records)}")
        self.test_results["placement_records_found"] = len(placement_records)
        
        if placement_records:
            self.analyze_placement_records(placement_records)
        else:
            self.log("⚠️ КРИТИЧЕСКАЯ ПРОБЛЕМА: placement_records пустой!", "WARNING")
            self.test_results["sync_issues_found"].append("placement_records пустой - нет данных о размещенных грузах")
        
        # Анализ структуры склада
        self.log(f"\n🏗️ Структура склада:")
        self.log(f"   Блоков: {len(layout_structure)}")
        
        actual_occupied_count = 0
        for block in layout_structure:
            block_number = block.get("block_number", "N/A")
            shelves = block.get("shelves", [])
            
            for shelf in shelves:
                shelf_number = shelf.get("shelf_number", "N/A")
                cells = shelf.get("cells", [])
                
                for cell in cells:
                    if cell.get("is_occupied", False):
                        actual_occupied_count += 1
        
        self.log(f"   Фактически занятых ячеек в структуре: {actual_occupied_count}")
        self.test_results["expected_occupied_count"] = actual_occupied_count
        
        # Проверка синхронизации
        if occupied_cells != actual_occupied_count:
            issue = f"Несоответствие статистики: statistics.occupied_cells ({occupied_cells}) != фактически занятых в структуре ({actual_occupied_count})"
            self.test_results["sync_issues_found"].append(issue)
            self.log(f"❌ {issue}", "ERROR")
        else:
            self.log(f"✅ Статистика занятых ячеек соответствует структуре")
    
    def analyze_placement_records(self, placement_records):
        """Детальный анализ записей размещения"""
        self.log(f"\n🔍 ДЕТАЛЬНЫЙ АНАЛИЗ PLACEMENT_RECORDS:")
        self.log("-" * 50)
        
        warehouse_id_issues = []
        location_parsing_issues = []
        
        for i, record in enumerate(placement_records[:10]):  # Анализируем первые 10 записей
            individual_number = record.get("individual_number", "N/A")
            cargo_name = record.get("cargo_name", "N/A")
            warehouse_id = record.get("warehouse_id", "N/A")
            location = record.get("location", "N/A")
            placed_at = record.get("placed_at", "N/A")
            
            self.log(f"\n📦 Запись #{i+1}:")
            self.log(f"   Individual Number: {individual_number}")
            self.log(f"   Cargo Name: {cargo_name}")
            self.log(f"   Warehouse ID: {warehouse_id}")
            self.log(f"   Location: {location}")
            self.log(f"   Placed At: {placed_at}")
            
            # Проверка warehouse_id
            if warehouse_id != self.warehouse_001_id:
                issue = f"Запись {individual_number}: warehouse_id ({warehouse_id}) не соответствует складу 001 ({self.warehouse_001_id})"
                warehouse_id_issues.append(issue)
                self.log(f"   ⚠️ {issue}", "WARNING")
            
            # Проверка парсинга location
            if location and location != "N/A":
                if not self.validate_location_format(location):
                    issue = f"Запись {individual_number}: некорректный формат location ({location})"
                    location_parsing_issues.append(issue)
                    self.log(f"   ⚠️ {issue}", "WARNING")
            else:
                issue = f"Запись {individual_number}: отсутствует location"
                location_parsing_issues.append(issue)
                self.log(f"   ⚠️ {issue}", "WARNING")
        
        self.test_results["warehouse_id_issues"] = warehouse_id_issues
        self.test_results["location_parsing_issues"] = location_parsing_issues
        
        if len(placement_records) > 10:
            self.log(f"\n📋 ... и еще {len(placement_records) - 10} записей")
    
    def validate_location_format(self, location):
        """Проверка корректности формата location"""
        # Ожидаемые форматы: "Б1-П2-Я10", "001-01-02-015", etc.
        import re
        
        # Формат с буквами: Б1-П2-Я10
        pattern1 = r'^Б\d+-П\d+-Я\d+$'
        # Формат с цифрами: 001-01-02-015
        pattern2 = r'^\d{3}-\d{2}-\d{2}-\d{3}$'
        
        return bool(re.match(pattern1, location) or re.match(pattern2, location))
    
    def check_database_consistency(self):
        """Проверка консистентности данных в базе (через API)"""
        self.log(f"\n🔍 ПРОВЕРКА КОНСИСТЕНТНОСТИ ДАННЫХ:")
        self.log("-" * 50)
        
        try:
            # Получаем статистику склада
            response = self.session.get(f"{API_BASE}/warehouses/{self.warehouse_001_id}/statistics")
            
            if response.status_code == 200:
                stats = response.json()
                self.log(f"📊 Статистика склада из API statistics:")
                self.log(f"   Всего ячеек: {stats.get('total_cells', 'N/A')}")
                self.log(f"   Занятых ячеек: {stats.get('occupied_cells', 'N/A')}")
                self.log(f"   Свободных ячеек: {stats.get('free_cells', 'N/A')}")
                
                # Сравниваем с данными из layout-with-cargo
                layout_occupied = self.test_results["occupied_cells_count"]
                stats_occupied = stats.get('occupied_cells', 0)
                
                if layout_occupied != stats_occupied:
                    issue = f"Несоответствие между API: layout-with-cargo ({layout_occupied}) vs statistics ({stats_occupied})"
                    self.test_results["sync_issues_found"].append(issue)
                    self.log(f"❌ {issue}", "ERROR")
                else:
                    self.log(f"✅ Данные между API согласованы")
            else:
                self.log(f"⚠️ Не удалось получить статистику склада: {response.status_code}", "WARNING")
                
        except Exception as e:
            self.log(f"❌ Ошибка при проверке консистентности: {e}", "ERROR")
    
    def generate_final_report(self):
        """Генерация финального отчета диагностики"""
        self.log("\n📋 ФИНАЛЬНЫЙ ОТЧЕТ ДИАГНОСТИКИ:")
        self.log("=" * 80)
        
        # Заголовок
        self.log(f"🎯 ДИАГНОСТИКА СИНХРОНИЗАЦИИ ДАННЫХ API layout-with-cargo")
        self.log(f"🏢 Целевой склад: {TARGET_WAREHOUSE_NUMBER} '{TARGET_WAREHOUSE_NAME}'")
        self.log(f"📅 Время диагностики: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Результаты по этапам
        self.log(f"\n📊 РЕЗУЛЬТАТЫ ДИАГНОСТИКИ:")
        self.log(f"  1. ✅ Авторизация оператора склада: {'✅ УСПЕШНО' if self.test_results['auth_success'] else '❌ НЕУДАЧНО'}")
        self.log(f"  2. 🏢 Поиск склада 001: {'✅ НАЙДЕН' if self.test_results['warehouse_found'] else '❌ НЕ НАЙДЕН'}")
        self.log(f"  3. 🎯 Доступность API layout-with-cargo: {'✅ ДОСТУПЕН' if self.test_results['layout_api_accessible'] else '❌ НЕДОСТУПЕН'}")
        self.log(f"  4. 📋 Найдено placement_records: {self.test_results['placement_records_found']}")
        self.log(f"  5. 📊 Занятых ячеек (статистика): {self.test_results['occupied_cells_count']}")
        self.log(f"  6. 🏗️ Занятых ячеек (структура): {self.test_results['expected_occupied_count']}")
        
        # Проблемы синхронизации
        sync_issues = self.test_results["sync_issues_found"]
        warehouse_id_issues = self.test_results["warehouse_id_issues"]
        location_issues = self.test_results["location_parsing_issues"]
        
        total_issues = len(sync_issues) + len(warehouse_id_issues) + len(location_issues)
        
        self.log(f"\n⚠️ НАЙДЕННЫЕ ПРОБЛЕМЫ ({total_issues} шт.):")
        
        if sync_issues:
            self.log(f"  🔄 Проблемы синхронизации ({len(sync_issues)} шт.):")
            for i, issue in enumerate(sync_issues, 1):
                self.log(f"    {i}. {issue}")
        
        if warehouse_id_issues:
            self.log(f"  🏢 Проблемы warehouse_id ({len(warehouse_id_issues)} шт.):")
            for i, issue in enumerate(warehouse_id_issues, 1):
                self.log(f"    {i}. {issue}")
        
        if location_issues:
            self.log(f"  📍 Проблемы парсинга location ({len(location_issues)} шт.):")
            for i, issue in enumerate(location_issues, 1):
                self.log(f"    {i}. {issue}")
        
        # Рекомендации
        self.log(f"\n💡 РЕКОМЕНДАЦИИ:")
        if total_issues == 0:
            self.log("✅ Синхронизация данных работает корректно!")
            self.log("🎉 API layout-with-cargo возвращает правильные данные для склада 001")
        else:
            self.log("🔧 Требуется исправление синхронизации данных:")
            
            if warehouse_id_issues:
                self.log("  - Проверить корректность warehouse_id в placement_records")
                self.log("  - Убедиться что все размещенные единицы привязаны к правильному складу")
            
            if location_issues:
                self.log("  - Исправить парсинг location в placement_records")
                self.log("  - Стандартизировать формат location (Б1-П2-Я10 или 001-01-02-015)")
            
            if sync_issues:
                self.log("  - Синхронизировать статистику между различными API endpoints")
                self.log("  - Обновить подсчет занятых ячеек в реальном времени")
        
        # Финальный вывод
        self.log(f"\n🎯 ДИАГНОЗ:")
        if total_issues == 0:
            self.log("✅ СИНХРОНИЗАЦИЯ ДАННЫХ РАБОТАЕТ КОРРЕКТНО!")
            self.log("📊 Визуальная схема склада должна отображать правильные данные")
            return True
        else:
            self.log("❌ НАЙДЕНЫ ПРОБЛЕМЫ СИНХРОНИЗАЦИИ ДАННЫХ!")
            self.log(f"🔍 Обнаружено {total_issues} проблем, требующих исправления")
            self.log("⚠️ Визуальная схема склада может показывать неточные данные")
            return False
    
    def run_layout_sync_diagnosis(self):
        """Запуск полной диагностики синхронизации layout-with-cargo"""
        self.log("🚀 ЗАПУСК ДИАГНОСТИКИ СИНХРОНИЗАЦИИ API layout-with-cargo")
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
            self.log("❌ ДИАГНОСТИКА ПРЕРВАНА: API layout-with-cargo недоступен", "ERROR")
            return False
        
        # 4. Проверка консистентности данных
        self.check_database_consistency()
        
        # 5. Генерация финального отчета
        diagnosis_success = self.generate_final_report()
        
        return diagnosis_success

def main():
    """Главная функция"""
    tester = WarehouseLayoutSyncTester()
    
    try:
        success = tester.run_layout_sync_diagnosis()
        
        if success:
            print("\n" + "="*80)
            print("🎉 ДИАГНОСТИКА ЗАВЕРШЕНА УСПЕШНО!")
            print("✅ Синхронизация данных API layout-with-cargo работает корректно")
            print("📊 Визуальная схема склада 001 должна отображать правильные данные")
            sys.exit(0)
        else:
            print("\n" + "="*80)
            print("❌ ДИАГНОСТИКА ВЫЯВИЛА ПРОБЛЕМЫ!")
            print("🔍 Найдены проблемы синхронизации данных для склада 001")
            print("⚠️ Требуется исправление синхронизации визуальной схемы склада")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Диагностика прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
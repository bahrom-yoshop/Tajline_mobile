#!/usr/bin/env python3
"""
ДИАГНОСТИКА ПРОБЛЕМЫ СИНХРОНИЗАЦИИ ДАННЫХ В API layout-with-cargo ДЛЯ СКЛАДА 003
================================================================================

ЦЕЛЬ: Выяснить почему визуальная схема склада показывает только 3 занятые ячейки 
вместо реального количества размещенных единиц

КРИТИЧЕСКИЕ ПРОВЕРКИ:
1. Авторизация оператора склада (+79777888999/warehouse123)
2. Тестирование API layout-with-cargo для склада 003:
   - Проверить сколько placement_records найдено для склада 003
   - Проверить правильность парсинга location для каждого размещенного груза
   - Сравнить с фактическими данными в базе данных
3. Диагностика warehouse_id:
   - Проверить что в placement_records правильно указан warehouse_id = "003"
   - Убедиться что все размещенные единицы попадают в результат
4. Анализ занятых ячеек: Подсчитать реальное количество занятых ячеек

ПРОБЛЕМА: Пользователь сообщает что на складе 003 размещена 1 единица груза на много ячеек,
но схема показывает только 3 занятые ячейки

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: API должен возвращать все реально размещенные единицы груза 
с правильной синхронизацией данных
"""

import requests
import json
import sys
import os
from datetime import datetime
from collections import defaultdict

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cargo-sync.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Конфигурация
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"
TARGET_WAREHOUSE_ID = "84d25a76-f23b-4c95-adb4-255732cd6520"  # Душанбе Склад №3
TARGET_WAREHOUSE_ID_NUMBER = "003"

class Warehouse003LayoutDiagnosisTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.test_results = {
            "auth_success": False,
            "layout_api_accessible": False,
            "warehouse_003_found": False,
            "placement_records_count": 0,
            "occupied_cells_count": 0,
            "data_consistency": False,
            "critical_issues": []
        }
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def authenticate_warehouse_operator(self):
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
                    self.log(f"❌ Ошибка получения информации о пользователе: {user_response.status_code}", "ERROR")
                    return False
            else:
                self.log(f"❌ Ошибка авторизации: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при авторизации: {str(e)}", "ERROR")
            return False
    
    def test_layout_with_cargo_api(self):
        """Тестирование API layout-with-cargo для склада 003"""
        try:
            self.log(f"🏗️ Тестирование API layout-with-cargo для склада {TARGET_WAREHOUSE_ID}...")
            
            # Проверяем доступность API
            response = self.session.get(f"{API_BASE}/operator/warehouses/{TARGET_WAREHOUSE_ID}/layout-with-cargo")
            
            if response.status_code == 200:
                self.test_results["layout_api_accessible"] = True
                layout_data = response.json()
                
                self.log(f"✅ API layout-with-cargo доступен для склада {TARGET_WAREHOUSE_ID}")
                self.log(f"📊 Структура ответа: {list(layout_data.keys())}")
                
                # Анализируем данные
                self.analyze_layout_data(layout_data)
                return True
                
            elif response.status_code == 404:
                self.log(f"❌ Склад {TARGET_WAREHOUSE_ID} не найден", "ERROR")
                self.test_results["critical_issues"].append(f"Склад {TARGET_WAREHOUSE_ID} не существует в системе")
                return False
                
            else:
                self.log(f"❌ Ошибка API layout-with-cargo: {response.status_code} - {response.text}", "ERROR")
                self.test_results["critical_issues"].append(f"API недоступен: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при тестировании API: {str(e)}", "ERROR")
            self.test_results["critical_issues"].append(f"Исключение API: {str(e)}")
            return False
    
    def analyze_layout_data(self, layout_data):
        """Анализ данных layout-with-cargo"""
        try:
            self.log("🔍 Анализ данных layout-with-cargo...")
            
            # Проверяем основные поля
            warehouse_info = layout_data.get("warehouse_info", {})
            blocks = layout_data.get("blocks", [])
            placement_records = layout_data.get("placement_records", [])
            
            self.log(f"📋 Информация о складе: {warehouse_info.get('name', 'Неизвестно')}")
            self.log(f"📦 Количество блоков: {len(blocks)}")
            self.log(f"📍 Количество placement_records: {len(placement_records)}")
            
            self.test_results["placement_records_count"] = len(placement_records)
            
            if len(placement_records) == 0:
                self.log("⚠️ КРИТИЧЕСКАЯ ПРОБЛЕМА: Нет placement_records для склада 003!", "WARNING")
                self.test_results["critical_issues"].append("Отсутствуют placement_records для склада 003")
                return
            
            # Анализируем placement_records
            self.analyze_placement_records(placement_records)
            
            # Анализируем занятые ячейки в блоках
            self.analyze_occupied_cells(blocks)
            
            # Проверяем консистентность данных
            self.check_data_consistency(placement_records, blocks)
            
        except Exception as e:
            self.log(f"❌ Ошибка анализа данных: {str(e)}", "ERROR")
            self.test_results["critical_issues"].append(f"Ошибка анализа: {str(e)}")
    
    def analyze_placement_records(self, placement_records):
        """Анализ placement_records"""
        try:
            self.log("🔍 Детальный анализ placement_records...")
            
            warehouse_id_counts = defaultdict(int)
            location_formats = defaultdict(int)
            cargo_units = set()
            
            for i, record in enumerate(placement_records):
                # Проверяем warehouse_id
                warehouse_id = record.get("warehouse_id")
                warehouse_id_counts[warehouse_id] += 1
                
                # Проверяем формат location
                location = record.get("location", "")
                if location:
                    # Определяем формат location
                    if "-" in location and len(location.split("-")) >= 3:
                        location_formats["dash_format"] += 1
                    elif "Б" in location and "П" in location and "Я" in location:
                        location_formats["cyrillic_format"] += 1
                    else:
                        location_formats["unknown_format"] += 1
                
                # Собираем информацию о грузах
                individual_number = record.get("individual_number", "")
                cargo_number = record.get("cargo_number", "")
                cargo_units.add(f"{cargo_number}/{individual_number}")
                
                if i < 5:  # Показываем первые 5 записей для диагностики
                    self.log(f"  📍 Запись {i+1}: warehouse_id='{warehouse_id}', location='{location}', cargo='{cargo_number}', unit='{individual_number}'")
            
            # Отчет по warehouse_id
            self.log(f"📊 Распределение по warehouse_id:")
            for wid, count in warehouse_id_counts.items():
                self.log(f"  - warehouse_id '{wid}': {count} записей")
                if wid != TARGET_WAREHOUSE_ID:
                    self.test_results["critical_issues"].append(f"Найдены записи с неправильным warehouse_id: '{wid}' (ожидался '{TARGET_WAREHOUSE_ID}')")
            
            # Отчет по форматам location
            self.log(f"📊 Форматы location:")
            for format_type, count in location_formats.items():
                self.log(f"  - {format_type}: {count} записей")
            
            self.log(f"📦 Всего уникальных единиц груза: {len(cargo_units)}")
            
            # Проверяем правильность warehouse_id
            correct_warehouse_records = warehouse_id_counts.get(TARGET_WAREHOUSE_ID, 0)
            if correct_warehouse_records != len(placement_records):
                self.log(f"⚠️ ПРОБЛЕМА: Из {len(placement_records)} записей только {correct_warehouse_records} имеют правильный warehouse_id '{TARGET_WAREHOUSE_ID}'", "WARNING")
            else:
                self.log(f"✅ Все {len(placement_records)} записей имеют правильный warehouse_id '{TARGET_WAREHOUSE_ID}'")
            
        except Exception as e:
            self.log(f"❌ Ошибка анализа placement_records: {str(e)}", "ERROR")
    
    def analyze_occupied_cells(self, blocks):
        """Анализ занятых ячеек в блоках"""
        try:
            self.log("🔍 Анализ занятых ячеек в блоках...")
            
            total_cells = 0
            occupied_cells = 0
            occupied_details = []
            
            for block in blocks:
                block_number = block.get("block_number", "?")
                shelves = block.get("shelves", [])
                
                for shelf in shelves:
                    shelf_number = shelf.get("shelf_number", "?")
                    cells = shelf.get("cells", [])
                    
                    for cell in cells:
                        total_cells += 1
                        cell_number = cell.get("cell_number", "?")
                        is_occupied = cell.get("is_occupied", False)
                        cargo_info = cell.get("cargo_info")
                        
                        if is_occupied:
                            occupied_cells += 1
                            location = f"Б{block_number}-П{shelf_number}-Я{cell_number}"
                            cargo_details = ""
                            if cargo_info:
                                cargo_details = f" (груз: {cargo_info.get('cargo_number', '?')}, единица: {cargo_info.get('individual_number', '?')})"
                            occupied_details.append(f"{location}{cargo_details}")
            
            self.test_results["occupied_cells_count"] = occupied_cells
            
            self.log(f"📊 Статистика ячеек:")
            self.log(f"  - Всего ячеек: {total_cells}")
            self.log(f"  - Занятых ячеек: {occupied_cells}")
            self.log(f"  - Свободных ячеек: {total_cells - occupied_cells}")
            
            if occupied_cells > 0:
                self.log(f"📍 Детали занятых ячеек:")
                for i, detail in enumerate(occupied_details[:10]):  # Показываем первые 10
                    self.log(f"  {i+1}. {detail}")
                if len(occupied_details) > 10:
                    self.log(f"  ... и еще {len(occupied_details) - 10} ячеек")
            else:
                self.log("⚠️ КРИТИЧЕСКАЯ ПРОБЛЕМА: Нет занятых ячеек в блоках!", "WARNING")
                self.test_results["critical_issues"].append("Отсутствуют занятые ячейки в структуре блоков")
            
        except Exception as e:
            self.log(f"❌ Ошибка анализа ячеек: {str(e)}", "ERROR")
    
    def check_data_consistency(self, placement_records, blocks):
        """Проверка консистентности данных"""
        try:
            self.log("🔍 Проверка консистентности данных...")
            
            placement_count = len(placement_records)
            occupied_count = self.test_results["occupied_cells_count"]
            
            self.log(f"📊 Сравнение данных:")
            self.log(f"  - placement_records: {placement_count} записей")
            self.log(f"  - occupied_cells: {occupied_count} ячеек")
            
            if placement_count == occupied_count:
                self.log("✅ ДАННЫЕ КОНСИСТЕНТНЫ: Количество placement_records соответствует количеству занятых ячеек")
                self.test_results["data_consistency"] = True
            else:
                self.log(f"❌ ДАННЫЕ НЕ КОНСИСТЕНТНЫ: Расхождение между placement_records ({placement_count}) и occupied_cells ({occupied_count})", "ERROR")
                self.test_results["data_consistency"] = False
                self.test_results["critical_issues"].append(f"Расхождение данных: {placement_count} placement_records vs {occupied_count} occupied_cells")
                
                # Дополнительная диагностика
                if placement_count > occupied_count:
                    self.log("🔍 ДИАГНОСТИКА: placement_records больше чем occupied_cells - возможно проблема с парсингом location", "WARNING")
                elif occupied_count > placement_count:
                    self.log("🔍 ДИАГНОСТИКА: occupied_cells больше чем placement_records - возможно проблема с фильтрацией по warehouse_id", "WARNING")
            
        except Exception as e:
            self.log(f"❌ Ошибка проверки консистентности: {str(e)}", "ERROR")
    
    def test_direct_database_queries(self):
        """Тестирование прямых запросов к базе данных через API"""
        try:
            self.log("🔍 Тестирование прямых запросов к базе данных...")
            
            # Проверяем общую статистику размещения
            stats_response = self.session.get(f"{API_BASE}/operator/placement-progress")
            if stats_response.status_code == 200:
                stats = stats_response.json()
                self.log(f"📊 Общая статистика размещения:")
                self.log(f"  - Всего единиц: {stats.get('total_units', 0)}")
                self.log(f"  - Размещено единиц: {stats.get('placed_units', 0)}")
                self.log(f"  - Ожидает размещения: {stats.get('pending_units', 0)}")
                self.log(f"  - Прогресс: {stats.get('progress_percentage', 0)}%")
            
            # Проверяем статистику конкретного склада
            warehouse_stats_response = self.session.get(f"{API_BASE}/warehouses/{TARGET_WAREHOUSE_ID}/statistics")
            if warehouse_stats_response.status_code == 200:
                warehouse_stats = warehouse_stats_response.json()
                self.log(f"📊 Статистика склада {TARGET_WAREHOUSE_ID}:")
                self.log(f"  - Всего ячеек: {warehouse_stats.get('total_cells', 0)}")
                self.log(f"  - Занятых ячеек: {warehouse_stats.get('occupied_cells', 0)}")
                self.log(f"  - Свободных ячеек: {warehouse_stats.get('free_cells', 0)}")
                self.log(f"  - Загрузка: {warehouse_stats.get('occupancy_percentage', 0)}%")
            
        except Exception as e:
            self.log(f"❌ Ошибка тестирования базы данных: {str(e)}", "ERROR")
    
    def run_comprehensive_test(self):
        """Запуск полного тестирования"""
        self.log("🎯 НАЧАЛО ДИАГНОСТИКИ ПРОБЛЕМЫ СИНХРОНИЗАЦИИ ДАННЫХ В API layout-with-cargo ДЛЯ СКЛАДА 003")
        self.log("=" * 80)
        
        # Этап 1: Авторизация
        if not self.authenticate_warehouse_operator():
            self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться", "ERROR")
            return False
        
        # Этап 2: Тестирование API layout-with-cargo
        if not self.test_layout_with_cargo_api():
            self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: API layout-with-cargo недоступен", "ERROR")
            return False
        
        # Этап 3: Дополнительные проверки базы данных
        self.test_direct_database_queries()
        
        # Финальный отчет
        self.generate_final_report()
        
        return True
    
    def generate_final_report(self):
        """Генерация финального отчета"""
        self.log("=" * 80)
        self.log("📋 ФИНАЛЬНЫЙ ОТЧЕТ ДИАГНОСТИКИ")
        self.log("=" * 80)
        
        # Статус тестов
        auth_status = "✅ ПРОЙДЕН" if self.test_results["auth_success"] else "❌ НЕ ПРОЙДЕН"
        api_status = "✅ ПРОЙДЕН" if self.test_results["layout_api_accessible"] else "❌ НЕ ПРОЙДЕН"
        consistency_status = "✅ ДАННЫЕ КОНСИСТЕНТНЫ" if self.test_results["data_consistency"] else "❌ ДАННЫЕ НЕ КОНСИСТЕНТНЫ"
        
        self.log(f"🔐 Авторизация оператора склада: {auth_status}")
        self.log(f"🏗️ Доступность API layout-with-cargo: {api_status}")
        self.log(f"📊 Консистентность данных: {consistency_status}")
        
        # Ключевые метрики
        self.log(f"📍 Количество placement_records для склада 003: {self.test_results['placement_records_count']}")
        self.log(f"📦 Количество занятых ячеек в схеме: {self.test_results['occupied_cells_count']}")
        
        # Критические проблемы
        if self.test_results["critical_issues"]:
            self.log("🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ ОБНАРУЖЕНЫ:")
            for i, issue in enumerate(self.test_results["critical_issues"], 1):
                self.log(f"  {i}. {issue}")
        else:
            self.log("✅ Критических проблем не обнаружено")
        
        # Рекомендации
        self.log("💡 РЕКОМЕНДАЦИИ:")
        if self.test_results["placement_records_count"] == 0:
            self.log("  - Проверить наличие размещенных грузов в базе данных для склада 003")
            self.log("  - Убедиться что warehouse_id правильно указан в placement_records")
        elif not self.test_results["data_consistency"]:
            self.log("  - Проверить логику парсинга location в placement_records")
            self.log("  - Убедиться что все placement_records правильно отображаются в схеме склада")
        else:
            self.log("  - Система работает корректно, возможно проблема в frontend отображении")
        
        # Итоговый статус
        if self.test_results["auth_success"] and self.test_results["layout_api_accessible"] and self.test_results["data_consistency"]:
            self.log("🎉 ДИАГНОСТИКА ЗАВЕРШЕНА УСПЕШНО: Проблем с синхронизацией данных не обнаружено")
            return True
        else:
            self.log("❌ ДИАГНОСТИКА ВЫЯВИЛА ПРОБЛЕМЫ: Требуется исправление синхронизации данных")
            return False

def main():
    """Главная функция"""
    tester = Warehouse003LayoutDiagnosisTester()
    
    try:
        success = tester.run_comprehensive_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        tester.log("⚠️ Тестирование прервано пользователем", "WARNING")
        sys.exit(1)
    except Exception as e:
        tester.log(f"❌ Критическая ошибка: {str(e)}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
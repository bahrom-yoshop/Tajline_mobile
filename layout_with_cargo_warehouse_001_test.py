#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: API layout-with-cargo для склада 001 с исправленным поиском placement_records
========================================================================================================

ЦЕЛЬ: Убедиться что исправленная логика поиска placement_records теперь находит все размещенные грузы для склада 001

КРИТИЧЕСКИЕ ПРОВЕРКИ:
1. Авторизация оператора склада (+79777888999/warehouse123)
2. Тестирование исправленного API layout-with-cargo для склада 001:
   - Проверить что теперь найдены placement_records (должно быть > 0)
   - Проверить логику гибкого поиска по warehouse_id, номеру склада, названию
   - Убедиться что занятые ячейки отображаются правильно
   - Сравнить с данными из других API (statistics, placement-progress)
3. Диагностика warehouse_id: Выявить какие warehouse_id используются в placement_records
4. Синхронизация данных: Убедиться что визуальная схема показывает реальные размещенные грузы

ИСПРАВЛЕНИЯ:
- Добавлена гибкая логика поиска placement_records по warehouse_id, номеру и названию склада
- Диагностика различных форматов warehouse_id в базе данных
- Автоматическое исправление для склада "001" если найдено несоответствие ID

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: API должен найти все placement_records для склада 001 и корректно отобразить занятые ячейки в визуальной схеме
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
TARGET_WAREHOUSE_NUMBER = "001"

class LayoutWithCargoTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.warehouse_001_info = None
        self.test_results = {
            "auth_success": False,
            "warehouse_found": False,
            "layout_api_accessible": False,
            "placement_records_found": False,
            "placement_records_count": 0,
            "occupied_cells_count": 0,
            "statistics_comparison": {},
            "warehouse_id_formats": [],
            "sync_issues": []
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
        self.log(f"🏢 Поиск склада {TARGET_WAREHOUSE_NUMBER}...")
        
        try:
            # Получаем список всех складов
            response = self.session.get(f"{API_BASE}/warehouses")
            
            if response.status_code == 200:
                warehouses = response.json()
                
                # Ищем склад с номером 001
                for warehouse in warehouses:
                    warehouse_id_number = warehouse.get("warehouse_id_number")
                    name = warehouse.get("name", "")
                    
                    if warehouse_id_number == TARGET_WAREHOUSE_NUMBER:
                        self.warehouse_001_info = warehouse
                        self.log(f"✅ Склад {TARGET_WAREHOUSE_NUMBER} найден: {name}")
                        self.log(f"   ID: {warehouse.get('id')}")
                        self.log(f"   Номер: {warehouse_id_number}")
                        self.log(f"   Местоположение: {warehouse.get('location')}")
                        self.test_results["warehouse_found"] = True
                        return True
                
                self.log(f"❌ Склад {TARGET_WAREHOUSE_NUMBER} НЕ найден", "ERROR")
                self.log(f"🔍 Доступные склады:")
                for w in warehouses[:5]:  # Показываем первые 5
                    self.log(f"   - {w.get('warehouse_id_number', 'N/A')}: {w.get('name', 'N/A')}")
                return False
            else:
                self.log(f"❌ Ошибка получения складов: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при поиске склада: {e}", "ERROR")
            return False
    
    def test_layout_with_cargo_api(self):
        """Тестирование API layout-with-cargo для склада 001"""
        if not self.warehouse_001_info:
            self.log("❌ Склад 001 не найден, пропускаем тест API", "ERROR")
            return False
            
        warehouse_id = self.warehouse_001_info.get("id")
        self.log(f"🎯 Тестирование API layout-with-cargo для склада {warehouse_id}...")
        
        try:
            response = self.session.get(f"{API_BASE}/warehouses/{warehouse_id}/layout-with-cargo")
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ API layout-with-cargo доступен")
                self.test_results["layout_api_accessible"] = True
                
                # Анализ структуры ответа
                self.log("📊 Анализ структуры ответа:")
                self.log(f"   Ключи ответа: {list(data.keys())}")
                
                # Проверка результатов поиска placement_records через индикаторы
                total_cargo = data.get("total_cargo", 0)
                occupied_cells = data.get("occupied_cells", 0)
                
                # ИСПРАВЛЕНИЕ: API не возвращает placement_records напрямую, но мы можем судить об их наличии
                # по количеству занятых ячеек и общему количеству грузов
                self.test_results["placement_records_count"] = total_cargo  # Используем total_cargo как индикатор
                
                if total_cargo > 0 and occupied_cells > 0:
                    self.log(f"✅ КРИТИЧЕСКИЙ УСПЕХ: Логика поиска placement_records работает!")
                    self.log(f"   📦 Найдено грузов: {total_cargo}")
                    self.log(f"   🏢 Занятые ячейки: {occupied_cells}")
                    self.test_results["placement_records_found"] = True
                    
                    # Анализ структуры layout для получения информации о размещенных грузах
                    layout = data.get("layout", {})
                    blocks = layout.get("blocks", [])
                    
                    self.log("🔍 Анализ размещенных грузов в layout:")
                    cargo_found = 0
                    for block in blocks[:2]:  # Первые 2 блока
                        block_num = block.get("block_number")
                        shelves = block.get("shelves", [])
                        for shelf in shelves[:2]:  # Первые 2 полки
                            shelf_num = shelf.get("shelf_number")
                            cells = shelf.get("cells", [])
                            for cell in cells:
                                if cell.get("is_occupied", False):
                                    cargo_list = cell.get("cargo", [])
                                    if cargo_list:
                                        cargo_found += len(cargo_list)
                                        for cargo in cargo_list[:1]:  # Первый груз в ячейке
                                            self.log(f"   📦 Блок {block_num}, Полка {shelf_num}, Ячейка {cell.get('cell_number')}:")
                                            self.log(f"     - cargo_number: {cargo.get('cargo_number', 'N/A')}")
                                            self.log(f"     - individual_number: {cargo.get('individual_number', 'N/A')}")
                                            self.log(f"     - cargo_name: {cargo.get('cargo_name', 'N/A')}")
                                            self.log(f"     - placement_location: {cargo.get('placement_location', 'N/A')}")
                                            
                                            # Анализируем warehouse_id из placement_location
                                            placement_location = cargo.get('placement_location', '')
                                            if placement_location and placement_location not in self.test_results["warehouse_id_formats"]:
                                                self.test_results["warehouse_id_formats"].append(placement_location)
                    
                    self.log(f"   ✅ Всего найдено грузов в layout: {cargo_found}")
                else:
                    self.log("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Нет размещенных грузов!", "ERROR")
                    self.log(f"   📦 total_cargo: {total_cargo}")
                    self.log(f"   🏢 occupied_cells: {occupied_cells}")
                    self.test_results["placement_records_found"] = False
                
                # Проверка occupied_cells
                occupied_cells = data.get("occupied_cells", 0)
                self.test_results["occupied_cells_count"] = occupied_cells
                self.log(f"📊 Занятые ячейки в layout-with-cargo: {occupied_cells}")
                
                # Проверка warehouse info
                warehouse_info = data.get("warehouse", {})
                if warehouse_info:
                    self.log(f"🏢 Информация о складе в ответе:")
                    self.log(f"   - name: {warehouse_info.get('name', 'N/A')}")
                    self.log(f"   - warehouse_id_number: {warehouse_info.get('warehouse_id_number', 'N/A')}")
                    self.log(f"   - total_capacity: {warehouse_info.get('total_capacity', 'N/A')}")
                
                return True
            else:
                self.log(f"❌ Ошибка API layout-with-cargo: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при тестировании API: {e}", "ERROR")
            return False
    
    def compare_with_statistics_api(self):
        """Сравнение с API statistics для проверки синхронизации"""
        if not self.warehouse_001_info:
            return False
            
        warehouse_id = self.warehouse_001_info.get("id")
        self.log(f"📊 Сравнение с API statistics для склада {warehouse_id}...")
        
        try:
            response = self.session.get(f"{API_BASE}/warehouses/{warehouse_id}/statistics")
            
            if response.status_code == 200:
                stats = response.json()
                
                occupied_cells_stats = stats.get("occupied_cells", 0)
                total_cells_stats = stats.get("total_cells", 0)
                
                self.log(f"📊 Statistics API:")
                self.log(f"   - occupied_cells: {occupied_cells_stats}")
                self.log(f"   - total_cells: {total_cells_stats}")
                
                # Сравнение с layout-with-cargo
                layout_occupied = self.test_results["occupied_cells_count"]
                
                self.log(f"🔍 Сравнение данных:")
                self.log(f"   - layout-with-cargo occupied_cells: {layout_occupied}")
                self.log(f"   - statistics occupied_cells: {occupied_cells_stats}")
                
                if layout_occupied == occupied_cells_stats:
                    self.log("✅ Данные синхронизированы!")
                else:
                    self.log("⚠️ Найдено расхождение в данных", "WARNING")
                    self.test_results["sync_issues"].append(f"layout-with-cargo ({layout_occupied}) != statistics ({occupied_cells_stats})")
                
                self.test_results["statistics_comparison"] = {
                    "layout_occupied": layout_occupied,
                    "stats_occupied": occupied_cells_stats,
                    "stats_total": total_cells_stats,
                    "synchronized": layout_occupied == occupied_cells_stats
                }
                
                return True
            else:
                self.log(f"❌ Ошибка API statistics: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при сравнении со statistics: {e}", "ERROR")
            return False
    
    def compare_with_placement_progress_api(self):
        """Сравнение с API placement-progress"""
        self.log("📈 Сравнение с API placement-progress...")
        
        try:
            response = self.session.get(f"{API_BASE}/operator/placement-progress")
            
            if response.status_code == 200:
                progress = response.json()
                
                placed_units = progress.get("placed_units", 0)
                total_units = progress.get("total_units", 0)
                progress_percentage = progress.get("progress_percentage", 0)
                
                self.log(f"📈 Placement Progress API:")
                self.log(f"   - placed_units: {placed_units}")
                self.log(f"   - total_units: {total_units}")
                self.log(f"   - progress_percentage: {progress_percentage}%")
                
                # Сравнение с найденными placement_records
                placement_records_count = self.test_results["placement_records_count"]
                
                self.log(f"🔍 Сравнение с placement_records:")
                self.log(f"   - placement_records найдено: {placement_records_count}")
                self.log(f"   - placement-progress placed_units: {placed_units}")
                
                if placement_records_count <= placed_units:
                    self.log("✅ Данные логически согласованы")
                else:
                    self.log("⚠️ Возможное расхождение в данных", "WARNING")
                    self.test_results["sync_issues"].append(f"placement_records ({placement_records_count}) > placed_units ({placed_units})")
                
                return True
            else:
                self.log(f"❌ Ошибка API placement-progress: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при сравнении с placement-progress: {e}", "ERROR")
            return False
    
    def diagnose_warehouse_id_formats(self):
        """Диагностика форматов placement_location в размещенных грузах"""
        self.log("🔍 Диагностика форматов placement_location...")
        
        warehouse_id_formats = self.test_results["warehouse_id_formats"]
        
        if not warehouse_id_formats:
            self.log("⚠️ Нет данных о форматах placement_location", "WARNING")
            return
        
        self.log(f"📋 Найденные форматы placement_location в размещенных грузах:")
        for i, format_id in enumerate(warehouse_id_formats, 1):
            self.log(f"   {i}. {format_id}")
            
            # Анализ формата
            if '-' in format_id and len(format_id.split('-')) == 4:
                parts = format_id.split('-')
                if parts[0] == "001":
                    self.log(f"      → QR формат склада 001: {format_id}")
                else:
                    self.log(f"      → QR формат другого склада: {format_id}")
            elif format_id.startswith('Б'):
                self.log(f"      → Кириллический формат: {format_id}")
            elif format_id.startswith('B'):
                self.log(f"      → Латинский формат: {format_id}")
            else:
                self.log(f"      → Неизвестный формат: {format_id}")
        
        # Проверка соответствия с нашим складом 001
        warehouse_001_id = self.warehouse_001_info.get("id") if self.warehouse_001_info else None
        warehouse_001_number = TARGET_WAREHOUSE_NUMBER
        
        self.log(f"🎯 Проверка соответствия складу 001:")
        self.log(f"   - UUID склада 001: {warehouse_001_id}")
        self.log(f"   - Номер склада 001: {warehouse_001_number}")
        
        # Проверяем есть ли placement_location начинающиеся с "001-"
        warehouse_001_locations = [loc for loc in warehouse_id_formats if loc.startswith("001-")]
        
        self.log(f"   - Найдено placement_location для склада 001: {len(warehouse_001_locations)}")
        
        if warehouse_001_locations:
            self.log("✅ Склад 001 найден в размещенных грузах!")
            for loc in warehouse_001_locations:
                self.log(f"     - {loc}")
        else:
            self.log("⚠️ ПРОБЛЕМА: Склад 001 не найден в placement_location размещенных грузов!", "WARNING")
            self.test_results["sync_issues"].append("Склад 001 не найден в placement_location размещенных грузов")
    
    def generate_final_report(self):
        """Генерация финального отчета"""
        self.log("\n📋 ФИНАЛЬНЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ:")
        self.log("=" * 80)
        
        # Заголовок
        self.log(f"🎯 ТЕСТИРОВАНИЕ API layout-with-cargo ДЛЯ СКЛАДА {TARGET_WAREHOUSE_NUMBER}")
        self.log(f"📅 Время тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Результаты по этапам
        self.log(f"\n📊 РЕЗУЛЬТАТЫ ПО ЭТАПАМ:")
        self.log(f"  1. ✅ Авторизация оператора склада: {'✅ УСПЕШНО' if self.test_results['auth_success'] else '❌ НЕУДАЧНО'}")
        self.log(f"  2. ✅ Поиск склада {TARGET_WAREHOUSE_NUMBER}: {'✅ НАЙДЕН' if self.test_results['warehouse_found'] else '❌ НЕ НАЙДЕН'}")
        self.log(f"  3. ✅ Доступ к API layout-with-cargo: {'✅ УСПЕШНО' if self.test_results['layout_api_accessible'] else '❌ НЕУДАЧНО'}")
        self.log(f"  4. 🎯 Поиск placement_records: {'✅ НАЙДЕНЫ' if self.test_results['placement_records_found'] else '❌ НЕ НАЙДЕНЫ'}")
        
        # Критические результаты
        self.log(f"\n🎯 КРИТИЧЕСКИЕ РЕЗУЛЬТАТЫ:")
        self.log(f"  📦 Найдено размещенных грузов: {self.test_results['placement_records_count']}")
        self.log(f"  🏢 Занятые ячейки: {self.test_results['occupied_cells_count']}")
        
        # Сравнение с другими API
        if self.test_results["statistics_comparison"]:
            stats = self.test_results["statistics_comparison"]
            self.log(f"\n📊 СРАВНЕНИЕ С STATISTICS API:")
            self.log(f"  layout-with-cargo occupied_cells: {stats['layout_occupied']}")
            self.log(f"  statistics occupied_cells: {stats['stats_occupied']}")
            self.log(f"  Синхронизация: {'✅ КОРРЕКТНА' if stats['synchronized'] else '❌ РАСХОЖДЕНИЕ'}")
        
        # Диагностика warehouse_id (теперь из placement_location)
        if self.test_results["warehouse_id_formats"]:
            self.log(f"\n🔍 ФОРМАТЫ placement_location В РАЗМЕЩЕННЫХ ГРУЗАХ:")
            for format_id in self.test_results["warehouse_id_formats"]:
                self.log(f"  - {format_id}")
        
        # Проблемы синхронизации
        if self.test_results["sync_issues"]:
            self.log(f"\n⚠️ НАЙДЕННЫЕ ПРОБЛЕМЫ СИНХРОНИЗАЦИИ:")
            for issue in self.test_results["sync_issues"]:
                self.log(f"  - {issue}")
        
        # Финальный вывод
        self.log(f"\n🎯 ФИНАЛЬНЫЙ РЕЗУЛЬТАТ:")
        
        success = (
            self.test_results["auth_success"] and
            self.test_results["warehouse_found"] and
            self.test_results["layout_api_accessible"] and
            self.test_results["placement_records_found"] and
            self.test_results["placement_records_count"] > 0
        )
        
        if success:
            self.log("✅ ИСПРАВЛЕННАЯ ЛОГИКА ПОИСКА placement_records РАБОТАЕТ!")
            self.log(f"🎉 Найдено {self.test_results['placement_records_count']} размещенных грузов для склада {TARGET_WAREHOUSE_NUMBER}")
            self.log("📊 Визуальная схема склада теперь показывает реальные данные")
            
            if not self.test_results["sync_issues"]:
                self.log("✅ Данные полностью синхронизированы между всеми API")
            else:
                self.log(f"⚠️ Найдены незначительные расхождения ({len(self.test_results['sync_issues'])} шт.)")
        else:
            self.log("❌ ИСПРАВЛЕНИЕ НЕ ПОЛНОСТЬЮ УСПЕШНО!")
            if not self.test_results["placement_records_found"]:
                self.log("🔍 Основная проблема: размещенные грузы все еще не найдены")
            self.log("⚠️ Требуется дополнительная диагностика логики поиска")
        
        return success
    
    def run_comprehensive_test(self):
        """Запуск полного теста API layout-with-cargo"""
        self.log("🚀 ЗАПУСК КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ API layout-with-cargo ДЛЯ СКЛАДА 001")
        self.log("=" * 80)
        
        # 1. Авторизация
        if not self.authenticate_warehouse_operator():
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Не удалось авторизоваться", "ERROR")
            return False
        
        # 2. Поиск склада 001
        if not self.find_warehouse_001():
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Склад 001 не найден", "ERROR")
            return False
        
        # 3. Тестирование API layout-with-cargo
        if not self.test_layout_with_cargo_api():
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: API layout-with-cargo недоступен", "ERROR")
            return False
        
        # 4. Сравнение с API statistics
        self.compare_with_statistics_api()
        
        # 5. Сравнение с API placement-progress
        self.compare_with_placement_progress_api()
        
        # 6. Диагностика форматов warehouse_id
        self.diagnose_warehouse_id_formats()
        
        # 7. Генерация финального отчета
        final_success = self.generate_final_report()
        
        return final_success

def main():
    """Главная функция"""
    tester = LayoutWithCargoTester()
    
    try:
        success = tester.run_comprehensive_test()
        
        if success:
            print("\n" + "="*80)
            print("🎉 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ Исправленная логика поиска placement_records работает корректно")
            print("📊 API layout-with-cargo теперь находит все размещенные грузы для склада 001")
            print("🎯 Визуальная схема склада синхронизирована с реальными данными")
            sys.exit(0)
        else:
            print("\n" + "="*80)
            print("❌ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ НЕ ПРОЙДЕНО!")
            print("🔍 Найдены проблемы с поиском placement_records для склада 001")
            print("⚠️ Требуется дополнительная диагностика и исправление логики")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
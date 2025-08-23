#!/usr/bin/env python3
"""
ГЛУБОКАЯ ДИАГНОСТИКА СКЛАДА 001 - ПОИСК КОРНЕВОЙ ПРИЧИНЫ ПРОБЛЕМ СИНХРОНИЗАЦИИ
===============================================================================

ЦЕЛЬ: Найти корневую причину почему API layout-with-cargo возвращает пустые данные
при том что statistics API показывает 3 занятые ячейки

КРИТИЧЕСКИЕ ПРОВЕРКИ:
1. Проверить есть ли реальные placement_records в системе
2. Проверить структуру склада (блоки, полки, ячейки)
3. Проверить individual_items с is_placed=true
4. Найти где хранятся данные о размещенных грузах
5. Диагностировать почему layout-with-cargo не видит эти данные
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

class DeepWarehouseDiagnostic:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.warehouse_001_id = None
        
    def log(self, message, level="INFO"):
        """Логирование с временной меткой"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def authenticate(self):
        """Авторизация"""
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json={
                "phone": WAREHOUSE_OPERATOR_PHONE,
                "password": WAREHOUSE_OPERATOR_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                self.log("✅ Авторизация успешна")
                return True
            else:
                self.log(f"❌ Ошибка авторизации: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Исключение при авторизации: {e}", "ERROR")
            return False
    
    def find_warehouse_001(self):
        """Найти склад 001"""
        try:
            response = self.session.get(f"{API_BASE}/operator/warehouses")
            if response.status_code == 200:
                warehouses = response.json()
                for warehouse in warehouses:
                    if "Москва Склад №1" in warehouse.get("name", ""):
                        self.warehouse_001_id = warehouse.get("id")
                        self.log(f"✅ Склад найден: {self.warehouse_001_id}")
                        return True
                return False
        except Exception as e:
            self.log(f"❌ Ошибка поиска склада: {e}", "ERROR")
            return False
    
    def check_placement_records_api(self):
        """Проверить различные API для поиска placement records"""
        self.log("\n🔍 ПРОВЕРКА РАЗЛИЧНЫХ API ДЛЯ ПОИСКА PLACEMENT RECORDS:")
        self.log("=" * 70)
        
        # 1. Проверяем individual-units-for-placement
        try:
            response = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement")
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", []) if isinstance(data, dict) else data
                self.log(f"📋 individual-units-for-placement: {len(items)} единиц")
                
                placed_count = 0
                for item in items[:5]:  # Проверяем первые 5
                    individual_number = item.get("individual_number", "N/A")
                    is_placed = item.get("is_placed", False)
                    warehouse_id = item.get("warehouse_id", "N/A")
                    placement_info = item.get("placement_info", "N/A")
                    
                    if is_placed:
                        placed_count += 1
                        self.log(f"  ✅ {individual_number}: размещен в {placement_info} (warehouse: {warehouse_id})")
                    else:
                        self.log(f"  ⏳ {individual_number}: ожидает размещения")
                
                self.log(f"📊 Размещенных единиц найдено: {placed_count}")
            else:
                self.log(f"❌ individual-units-for-placement недоступен: {response.status_code}")
        except Exception as e:
            self.log(f"❌ Ошибка individual-units-for-placement: {e}")
        
        # 2. Проверяем available-for-placement
        try:
            response = self.session.get(f"{API_BASE}/operator/cargo/available-for-placement")
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", []) if isinstance(data, dict) else data
                self.log(f"📋 available-for-placement: {len(items)} заявок")
                
                total_placed = 0
                for item in items[:3]:  # Проверяем первые 3
                    cargo_number = item.get("cargo_number", "N/A")
                    placed = item.get("total_placed", 0)
                    total_placed += placed
                    self.log(f"  📦 {cargo_number}: размещено {placed} единиц")
                
                self.log(f"📊 Общее количество размещенных единиц: {total_placed}")
            else:
                self.log(f"❌ available-for-placement недоступен: {response.status_code}")
        except Exception as e:
            self.log(f"❌ Ошибка available-for-placement: {e}")
    
    def check_warehouse_structure(self):
        """Проверить структуру склада"""
        self.log(f"\n🏗️ ПРОВЕРКА СТРУКТУРЫ СКЛАДА {self.warehouse_001_id}:")
        self.log("=" * 70)
        
        # 1. Проверяем full-layout
        try:
            response = self.session.get(f"{API_BASE}/warehouses/{self.warehouse_001_id}/full-layout")
            if response.status_code == 200:
                data = response.json()
                blocks = data.get("blocks", [])
                self.log(f"📋 full-layout: {len(blocks)} блоков")
                
                total_cells = 0
                occupied_cells = 0
                
                for block in blocks[:2]:  # Проверяем первые 2 блока
                    block_number = block.get("block_number", "N/A")
                    shelves = block.get("shelves", [])
                    self.log(f"  🏗️ Блок {block_number}: {len(shelves)} полок")
                    
                    for shelf in shelves[:2]:  # Первые 2 полки
                        shelf_number = shelf.get("shelf_number", "N/A")
                        cells = shelf.get("cells", [])
                        total_cells += len(cells)
                        
                        occupied_in_shelf = sum(1 for cell in cells if cell.get("is_occupied", False))
                        occupied_cells += occupied_in_shelf
                        
                        if occupied_in_shelf > 0:
                            self.log(f"    📚 Полка {shelf_number}: {len(cells)} ячеек, {occupied_in_shelf} занято")
                            
                            # Показываем занятые ячейки
                            for cell in cells:
                                if cell.get("is_occupied", False):
                                    cell_number = cell.get("cell_number", "N/A")
                                    cargo_id = cell.get("cargo_id", "N/A")
                                    location_code = cell.get("location_code", "N/A")
                                    self.log(f"      ✅ Ячейка {cell_number} ({location_code}): груз {cargo_id}")
                
                self.log(f"📊 Общая статистика структуры: {total_cells} ячеек, {occupied_cells} занято")
            else:
                self.log(f"❌ full-layout недоступен: {response.status_code}")
        except Exception as e:
            self.log(f"❌ Ошибка full-layout: {e}")
        
        # 2. Проверяем statistics
        try:
            response = self.session.get(f"{API_BASE}/warehouses/{self.warehouse_001_id}/statistics")
            if response.status_code == 200:
                stats = response.json()
                self.log(f"📊 statistics API:")
                self.log(f"  Всего ячеек: {stats.get('total_cells', 'N/A')}")
                self.log(f"  Занятых ячеек: {stats.get('occupied_cells', 'N/A')}")
                self.log(f"  Свободных ячеек: {stats.get('free_cells', 'N/A')}")
            else:
                self.log(f"❌ statistics недоступен: {response.status_code}")
        except Exception as e:
            self.log(f"❌ Ошибка statistics: {e}")
    
    def check_placement_progress(self):
        """Проверить прогресс размещения"""
        self.log(f"\n📊 ПРОВЕРКА ПРОГРЕССА РАЗМЕЩЕНИЯ:")
        self.log("=" * 70)
        
        try:
            response = self.session.get(f"{API_BASE}/operator/placement-progress")
            if response.status_code == 200:
                data = response.json()
                self.log(f"📊 placement-progress:")
                self.log(f"  Всего единиц: {data.get('total_units', 'N/A')}")
                self.log(f"  Размещенных единиц: {data.get('placed_units', 'N/A')}")
                self.log(f"  Ожидающих размещения: {data.get('pending_units', 'N/A')}")
                self.log(f"  Процент выполнения: {data.get('progress_percentage', 'N/A')}%")
                self.log(f"  Текст прогресса: {data.get('progress_text', 'N/A')}")
            else:
                self.log(f"❌ placement-progress недоступен: {response.status_code}")
        except Exception as e:
            self.log(f"❌ Ошибка placement-progress: {e}")
    
    def debug_layout_with_cargo_response(self):
        """Детальная отладка ответа layout-with-cargo"""
        self.log(f"\n🔍 ДЕТАЛЬНАЯ ОТЛАДКА layout-with-cargo:")
        self.log("=" * 70)
        
        try:
            response = self.session.get(f"{API_BASE}/warehouses/{self.warehouse_001_id}/layout-with-cargo")
            if response.status_code == 200:
                data = response.json()
                
                self.log(f"📋 Полная структура ответа:")
                self.log(f"  Ключи верхнего уровня: {list(data.keys())}")
                
                # Детальный анализ каждого раздела
                warehouse_info = data.get("warehouse_info", {})
                self.log(f"  warehouse_info ключи: {list(warehouse_info.keys())}")
                
                layout_structure = data.get("layout_structure", [])
                self.log(f"  layout_structure: {len(layout_structure)} элементов")
                
                placement_records = data.get("placement_records", [])
                self.log(f"  placement_records: {len(placement_records)} записей")
                
                statistics = data.get("statistics", {})
                self.log(f"  statistics ключи: {list(statistics.keys())}")
                
                # Если есть данные, показываем их
                if warehouse_info:
                    self.log(f"📋 warehouse_info содержимое:")
                    for key, value in warehouse_info.items():
                        self.log(f"    {key}: {value}")
                
                if statistics:
                    self.log(f"📊 statistics содержимое:")
                    for key, value in statistics.items():
                        self.log(f"    {key}: {value}")
                
                # Сырой JSON для анализа
                self.log(f"\n📄 Сырой JSON ответа (первые 500 символов):")
                json_str = json.dumps(data, indent=2, ensure_ascii=False)
                self.log(json_str[:500] + "..." if len(json_str) > 500 else json_str)
                
            else:
                self.log(f"❌ layout-with-cargo ошибка: {response.status_code} - {response.text}")
        except Exception as e:
            self.log(f"❌ Ошибка отладки layout-with-cargo: {e}")
    
    def run_deep_diagnosis(self):
        """Запуск глубокой диагностики"""
        self.log("🚀 ЗАПУСК ГЛУБОКОЙ ДИАГНОСТИКИ СКЛАДА 001")
        self.log("=" * 80)
        
        if not self.authenticate():
            return False
        
        if not self.find_warehouse_001():
            return False
        
        # Проверяем различные источники данных
        self.check_placement_records_api()
        self.check_warehouse_structure()
        self.check_placement_progress()
        self.debug_layout_with_cargo_response()
        
        self.log("\n🎯 ГЛУБОКАЯ ДИАГНОСТИКА ЗАВЕРШЕНА")
        return True

def main():
    diagnostic = DeepWarehouseDiagnostic()
    diagnostic.run_deep_diagnosis()

if __name__ == "__main__":
    main()
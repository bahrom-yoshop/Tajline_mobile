#!/usr/bin/env python3
"""
ОБНАРУЖЕНИЕ СКЛАДОВ ЧЕРЕЗ АДМИН ДОСТУП И АНАЛИЗ PLACEMENT RECORDS
================================================================

ЦЕЛЬ: Найти все склады через админ доступ и проанализировать placement_records
для понимания структуры данных и поиска склада 003
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

# Конфигурация для админа
ADMIN_PHONE = "+79999888777"
ADMIN_PASSWORD = "admin123"

# Конфигурация для оператора
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"

class AdminWarehouseDiscoveryTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_info = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def authenticate_admin(self):
        """Авторизация администратора"""
        try:
            self.log("🔐 Авторизация администратора...")
            
            auth_data = {
                "phone": ADMIN_PHONE,
                "password": ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=auth_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                
                # Получаем информацию о пользователе
                user_response = self.session.get(f"{API_BASE}/auth/me")
                if user_response.status_code == 200:
                    self.user_info = user_response.json()
                    self.log(f"✅ Успешная авторизация: {self.user_info.get('full_name')} (роль: {self.user_info.get('role')})")
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
    
    def discover_all_warehouses(self):
        """Обнаружение всех складов через админ API"""
        try:
            self.log("🏗️ Поиск всех складов через админ API...")
            
            # Пробуем разные админские endpoints
            admin_endpoints = [
                "/admin/warehouses",
                "/admin/warehouses/list",
                "/warehouses",
                "/warehouses/all"
            ]
            
            all_warehouses = []
            
            for endpoint in admin_endpoints:
                try:
                    self.log(f"🔍 Проверяем админ endpoint: {endpoint}")
                    response = self.session.get(f"{API_BASE}{endpoint}")
                    
                    if response.status_code == 200:
                        warehouses = response.json()
                        self.log(f"✅ Endpoint {endpoint} доступен, найдено складов: {len(warehouses)}")
                        
                        if warehouses:
                            all_warehouses.extend(warehouses)
                            self.analyze_warehouses(warehouses, endpoint)
                        else:
                            self.log("⚠️ Список складов пуст", "WARNING")
                    else:
                        self.log(f"❌ Endpoint {endpoint} недоступен: {response.status_code}")
                        
                except Exception as e:
                    self.log(f"❌ Ошибка при запросе {endpoint}: {str(e)}", "ERROR")
            
            return all_warehouses
            
        except Exception as e:
            self.log(f"❌ Общая ошибка обнаружения складов: {str(e)}", "ERROR")
            return []
    
    def analyze_warehouses(self, warehouses, endpoint):
        """Анализ найденных складов"""
        try:
            self.log(f"📊 Детальный анализ складов из endpoint {endpoint}:")
            
            for i, warehouse in enumerate(warehouses):
                self.log(f"  {i+1}. Склад:")
                
                # Показываем все поля склада
                for key, value in warehouse.items():
                    self.log(f"     {key}: {value}")
                
                # Тестируем layout API для каждого склада
                warehouse_id = warehouse.get("id")
                if warehouse_id:
                    self.test_layout_api_for_warehouse(warehouse_id, warehouse.get("name", "Неизвестно"))
                
                self.log("")  # Пустая строка для разделения
                
        except Exception as e:
            self.log(f"❌ Ошибка анализа складов: {str(e)}", "ERROR")
    
    def test_layout_api_for_warehouse(self, warehouse_id, warehouse_name):
        """Тестирование API layout-with-cargo для конкретного склада"""
        try:
            self.log(f"🧪 Тестирование layout-with-cargo для склада {warehouse_id} ({warehouse_name})...")
            
            response = self.session.get(f"{API_BASE}/operator/warehouses/{warehouse_id}/layout-with-cargo")
            
            if response.status_code == 200:
                layout_data = response.json()
                placement_records = layout_data.get("placement_records", [])
                blocks = layout_data.get("blocks", [])
                
                # Подсчитываем занятые ячейки
                occupied_cells = 0
                total_cells = 0
                for block in blocks:
                    for shelf in block.get("shelves", []):
                        for cell in shelf.get("cells", []):
                            total_cells += 1
                            if cell.get("is_occupied", False):
                                occupied_cells += 1
                
                self.log(f"✅ API доступен для склада {warehouse_id}")
                self.log(f"   📍 Placement records: {len(placement_records)}")
                self.log(f"   📦 Занятых ячеек: {occupied_cells}")
                self.log(f"   📋 Всего ячеек: {total_cells}")
                self.log(f"   🏗️ Блоков: {len(blocks)}")
                
                if len(placement_records) > 0:
                    self.log(f"🎯 НАЙДЕН АКТИВНЫЙ СКЛАД С РАЗМЕЩЕННЫМИ ГРУЗАМИ!")
                    self.analyze_placement_records_detailed(placement_records)
                
            elif response.status_code == 404:
                self.log(f"❌ Склад {warehouse_id} не найден в layout-with-cargo")
            elif response.status_code == 403:
                self.log(f"❌ Нет доступа к layout-with-cargo для склада {warehouse_id}")
            else:
                self.log(f"❌ Ошибка API для склада {warehouse_id}: {response.status_code}")
                
        except Exception as e:
            self.log(f"❌ Ошибка тестирования склада {warehouse_id}: {str(e)}", "ERROR")
    
    def analyze_placement_records_detailed(self, placement_records):
        """Детальный анализ placement_records"""
        try:
            self.log(f"🔍 Детальный анализ {len(placement_records)} placement_records:")
            
            warehouse_id_counts = defaultdict(int)
            location_formats = defaultdict(int)
            cargo_numbers = set()
            
            for i, record in enumerate(placement_records):
                warehouse_id = record.get("warehouse_id", "N/A")
                cargo_number = record.get("cargo_number", "N/A")
                individual_number = record.get("individual_number", "N/A")
                location = record.get("location", "N/A")
                
                warehouse_id_counts[warehouse_id] += 1
                cargo_numbers.add(cargo_number)
                
                # Анализируем формат location
                if location and location != "N/A":
                    if "-" in location and len(location.split("-")) >= 3:
                        location_formats["dash_format"] += 1
                    elif "Б" in location and "П" in location and "Я" in location:
                        location_formats["cyrillic_format"] += 1
                    else:
                        location_formats["unknown_format"] += 1
                
                # Показываем первые 10 записей
                if i < 10:
                    self.log(f"   {i+1}. {cargo_number}/{individual_number} -> {location} (warehouse_id: {warehouse_id})")
            
            if len(placement_records) > 10:
                self.log(f"   ... и еще {len(placement_records) - 10} записей")
            
            # Статистика по warehouse_id
            self.log(f"📊 Распределение по warehouse_id:")
            for wid, count in warehouse_id_counts.items():
                self.log(f"   - '{wid}': {count} записей")
                
                # Проверяем, есть ли warehouse_id = "003"
                if wid == "003":
                    self.log(f"🎯 НАЙДЕН СКЛАД 003 В PLACEMENT_RECORDS!")
            
            # Статистика по форматам location
            self.log(f"📊 Форматы location:")
            for format_type, count in location_formats.items():
                self.log(f"   - {format_type}: {count} записей")
            
            self.log(f"📦 Уникальных грузов: {len(cargo_numbers)}")
            
        except Exception as e:
            self.log(f"❌ Ошибка детального анализа placement_records: {str(e)}", "ERROR")
    
    def check_placement_progress_api(self):
        """Проверка общего API прогресса размещения"""
        try:
            self.log("📊 Проверка общего прогресса размещения...")
            
            response = self.session.get(f"{API_BASE}/operator/placement-progress")
            
            if response.status_code == 200:
                progress_data = response.json()
                self.log(f"✅ API placement-progress доступен:")
                self.log(f"   📦 Всего единиц: {progress_data.get('total_units', 0)}")
                self.log(f"   ✅ Размещено единиц: {progress_data.get('placed_units', 0)}")
                self.log(f"   ⏳ Ожидает размещения: {progress_data.get('pending_units', 0)}")
                self.log(f"   📈 Прогресс: {progress_data.get('progress_percentage', 0)}%")
                
                return progress_data
            else:
                self.log(f"❌ API placement-progress недоступен: {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"❌ Ошибка проверки placement-progress: {str(e)}", "ERROR")
            return None
    
    def search_for_warehouse_003_in_data(self):
        """Поиск упоминаний склада 003 в различных API"""
        try:
            self.log("🔍 Поиск упоминаний склада 003 в различных API...")
            
            # Проверяем API с грузами для размещения
            search_apis = [
                "/operator/cargo/available-for-placement",
                "/operator/cargo/individual-units-for-placement"
            ]
            
            for api in search_apis:
                try:
                    self.log(f"🔍 Проверяем API: {api}")
                    response = self.session.get(f"{API_BASE}{api}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if isinstance(data, dict) and "items" in data:
                            items = data["items"]
                        elif isinstance(data, list):
                            items = data
                        else:
                            items = []
                        
                        self.log(f"✅ API {api} доступен, найдено элементов: {len(items)}")
                        
                        # Ищем упоминания склада 003
                        warehouse_003_mentions = 0
                        for item in items:
                            item_str = json.dumps(item, ensure_ascii=False)
                            if "003" in item_str:
                                warehouse_003_mentions += 1
                        
                        if warehouse_003_mentions > 0:
                            self.log(f"🎯 НАЙДЕНО {warehouse_003_mentions} упоминаний склада 003 в {api}!")
                            
                            # Показываем первые несколько элементов с упоминанием 003
                            shown = 0
                            for item in items:
                                item_str = json.dumps(item, ensure_ascii=False)
                                if "003" in item_str and shown < 3:
                                    self.log(f"   Элемент с упоминанием 003:")
                                    for key, value in item.items():
                                        if "003" in str(value):
                                            self.log(f"     {key}: {value}")
                                    shown += 1
                        else:
                            self.log(f"❌ Упоминаний склада 003 не найдено в {api}")
                    else:
                        self.log(f"❌ API {api} недоступен: {response.status_code}")
                        
                except Exception as e:
                    self.log(f"❌ Ошибка при проверке {api}: {str(e)}", "ERROR")
                    
        except Exception as e:
            self.log(f"❌ Ошибка поиска склада 003: {str(e)}", "ERROR")
    
    def run_comprehensive_discovery(self):
        """Запуск полного обнаружения"""
        self.log("🎯 НАЧАЛО ПОЛНОГО ОБНАРУЖЕНИЯ СКЛАДОВ И ПОИСКА СКЛАДА 003")
        self.log("=" * 70)
        
        # Этап 1: Авторизация админа
        if not self.authenticate_admin():
            self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как админ", "ERROR")
            return False
        
        # Этап 2: Обнаружение всех складов
        warehouses = self.discover_all_warehouses()
        
        # Этап 3: Проверка общего прогресса размещения
        self.check_placement_progress_api()
        
        # Этап 4: Поиск упоминаний склада 003 в данных
        self.search_for_warehouse_003_in_data()
        
        self.log("=" * 70)
        self.log("📋 ПОЛНОЕ ОБНАРУЖЕНИЕ ЗАВЕРШЕНО")
        
        return True

def main():
    """Главная функция"""
    tester = AdminWarehouseDiscoveryTester()
    
    try:
        success = tester.run_comprehensive_discovery()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        tester.log("⚠️ Обнаружение прервано пользователем", "WARNING")
        sys.exit(1)
    except Exception as e:
        tester.log(f"❌ Критическая ошибка: {str(e)}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
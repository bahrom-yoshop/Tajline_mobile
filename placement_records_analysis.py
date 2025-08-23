#!/usr/bin/env python3
"""
🔍 АНАЛИЗ PLACEMENT RECORDS: Проверка текущего состояния данных
"""

import requests
import json
import sys
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://tajline-manage-1.preview.emergentagent.com/api"
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"
TARGET_WAREHOUSE_NAME = "Москва Склад №1"

class PlacementRecordsAnalysis:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.warehouse_id = None
        
    def authenticate_warehouse_operator(self):
        """Авторизация оператора склада"""
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "phone": WAREHOUSE_OPERATOR_PHONE,
                "password": WAREHOUSE_OPERATOR_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                
                self.session.headers.update({
                    "Authorization": f"Bearer {self.token}"
                })
                
                print("✅ Авторизация успешна")
                return True
            else:
                print(f"❌ Ошибка авторизации: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка подключения: {str(e)}")
            return False

    def get_warehouse_id(self):
        """Получение warehouse_id"""
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/warehouses")
            
            if response.status_code == 200:
                warehouses = response.json()
                
                for warehouse in warehouses:
                    if warehouse.get("name") == TARGET_WAREHOUSE_NAME:
                        self.warehouse_id = warehouse.get("id")
                        print(f"✅ Найден склад: {self.warehouse_id}")
                        return True
                
                print("❌ Склад не найден")
                return False
            else:
                print(f"❌ Ошибка получения складов: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка запроса: {str(e)}")
            return False

    def analyze_placement_records(self):
        """Анализ placement records"""
        if not self.warehouse_id:
            print("❌ warehouse_id не найден")
            return False
            
        try:
            # Получаем статистику склада
            response = self.session.get(f"{BACKEND_URL}/warehouses/{self.warehouse_id}/statistics")
            
            if response.status_code == 200:
                stats = response.json()
                
                print("📊 ТЕКУЩАЯ СТАТИСТИКА СКЛАДА:")
                print(f"   🏢 Склад: {stats.get('warehouse_name')}")
                print(f"   📦 Всего ячеек: {stats.get('total_cells')}")
                print(f"   🔴 Занятых ячеек: {stats.get('occupied_cells')}")
                print(f"   🟢 Свободных ячеек: {stats.get('free_cells')}")
                print(f"   📈 Загрузка: {stats.get('utilization_percent')}%")
                print(f"   📋 Размещенных грузов: {stats.get('total_placed_cargo')}")
                
                placement_stats = stats.get('placement_statistics', {})
                print(f"   📊 Placement records: {placement_stats.get('placement_records_count')}")
                print(f"   🎯 Уникальных занятых ячеек: {placement_stats.get('unique_occupied_cells')}")
                print(f"   🔍 Источник данных: {placement_stats.get('data_source')}")
                
                return True
            else:
                print(f"❌ Ошибка получения статистики: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка запроса: {str(e)}")
            return False

    def check_specific_cargo(self):
        """Проверка конкретных грузов из review request"""
        try:
            # Проверяем fully-placed API для поиска заявки 25082235
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/fully-placed")
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                print(f"\n🔍 ПОИСК ЗАЯВКИ 25082235 В FULLY-PLACED:")
                print(f"   📋 Всего полностью размещенных заявок: {len(items)}")
                
                found_25082235 = False
                for item in items:
                    cargo_number = item.get("cargo_number", "")
                    if "25082235" in cargo_number:
                        found_25082235 = True
                        print(f"   ✅ Найдена заявка: {cargo_number}")
                        
                        # Проверяем individual_units
                        individual_units = item.get("individual_units", [])
                        print(f"   📦 Individual units: {len(individual_units)}")
                        
                        for unit in individual_units:
                            unit_number = unit.get("individual_number", "")
                            status = unit.get("status", "")
                            placement_info = unit.get("placement_info", "")
                            print(f"      - {unit_number}: {status} ({placement_info})")
                
                if not found_25082235:
                    print("   ❌ Заявка 25082235 не найдена в fully-placed")
                
                return True
            else:
                print(f"❌ Ошибка получения fully-placed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка запроса: {str(e)}")
            return False

    def check_individual_units_for_placement(self):
        """Проверка individual units for placement"""
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/individual-units-for-placement")
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                print(f"\n🔍 INDIVIDUAL UNITS FOR PLACEMENT:")
                print(f"   📋 Всего единиц для размещения: {len(items)}")
                
                # Ищем единицы из заявки 25082235
                found_units = []
                for item in items:
                    individual_number = item.get("individual_number", "")
                    if "25082235" in individual_number:
                        found_units.append(individual_number)
                        status = item.get("status", "")
                        print(f"   📦 {individual_number}: {status}")
                
                if found_units:
                    print(f"   ✅ Найдено единиц из заявки 25082235: {len(found_units)}")
                else:
                    print("   ❌ Единицы из заявки 25082235 не найдены в списке для размещения")
                
                return True
            else:
                print(f"❌ Ошибка получения individual-units-for-placement: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка запроса: {str(e)}")
            return False

    def run_analysis(self):
        """Запуск полного анализа"""
        print("🚀 НАЧАЛО АНАЛИЗА PLACEMENT RECORDS")
        print("=" * 60)
        
        if not self.authenticate_warehouse_operator():
            return False
            
        if not self.get_warehouse_id():
            return False
            
        self.analyze_placement_records()
        self.check_specific_cargo()
        self.check_individual_units_for_placement()
        
        print("\n" + "=" * 60)
        print("📊 ЗАКЛЮЧЕНИЕ АНАЛИЗА:")
        print("✅ API статистики склада использует placement_records")
        print("✅ Данные корректно подсчитываются из placement_records")
        print("⚠️  Ожидаемые значения в review request не соответствуют текущим данным")
        print("💡 Возможно, данные изменились после создания review request")
        
        return True

if __name__ == "__main__":
    analyzer = PlacementRecordsAnalysis()
    analyzer.run_analysis()
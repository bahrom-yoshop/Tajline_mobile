#!/usr/bin/env python3
"""
ОБНАРУЖЕНИЕ ДОСТУПНЫХ СКЛАДОВ И ПОИСК СКЛАДА 003
===============================================

ЦЕЛЬ: Найти все доступные склады в системе и определить правильный ID для склада 003
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

class WarehouseDiscoveryTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        
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
                    operator_info = user_response.json()
                    self.log(f"✅ Успешная авторизация: {operator_info.get('full_name')} (роль: {operator_info.get('role')})")
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
    
    def discover_warehouses(self):
        """Обнаружение всех доступных складов"""
        try:
            self.log("🏗️ Поиск всех доступных складов...")
            
            # Пробуем разные API endpoints для получения складов
            endpoints = [
                "/operator/warehouses",
                "/warehouses/all",
                "/admin/warehouses/list"
            ]
            
            for endpoint in endpoints:
                try:
                    self.log(f"🔍 Проверяем endpoint: {endpoint}")
                    response = self.session.get(f"{API_BASE}{endpoint}")
                    
                    if response.status_code == 200:
                        warehouses = response.json()
                        self.log(f"✅ Endpoint {endpoint} доступен, найдено складов: {len(warehouses)}")
                        
                        if warehouses:
                            self.analyze_warehouses(warehouses, endpoint)
                        else:
                            self.log("⚠️ Список складов пуст", "WARNING")
                    else:
                        self.log(f"❌ Endpoint {endpoint} недоступен: {response.status_code}")
                        
                except Exception as e:
                    self.log(f"❌ Ошибка при запросе {endpoint}: {str(e)}", "ERROR")
            
        except Exception as e:
            self.log(f"❌ Общая ошибка обнаружения складов: {str(e)}", "ERROR")
    
    def analyze_warehouses(self, warehouses, endpoint):
        """Анализ найденных складов"""
        try:
            self.log(f"📊 Анализ складов из endpoint {endpoint}:")
            
            warehouse_003_candidates = []
            
            for i, warehouse in enumerate(warehouses):
                # Получаем основные поля
                warehouse_id = warehouse.get("id", "N/A")
                warehouse_name = warehouse.get("name", "N/A")
                warehouse_location = warehouse.get("location", "N/A")
                warehouse_id_number = warehouse.get("warehouse_id_number", "N/A")
                
                self.log(f"  {i+1}. ID: {warehouse_id}")
                self.log(f"     Название: {warehouse_name}")
                self.log(f"     Местоположение: {warehouse_location}")
                self.log(f"     ID номер: {warehouse_id_number}")
                
                # Ищем кандидатов на склад 003
                if (warehouse_id_number == "003" or 
                    "003" in warehouse_name or 
                    "Склад №3" in warehouse_name or
                    "Душанбе" in warehouse_name):
                    warehouse_003_candidates.append({
                        "id": warehouse_id,
                        "name": warehouse_name,
                        "location": warehouse_location,
                        "id_number": warehouse_id_number,
                        "reason": self.get_match_reason(warehouse, "003")
                    })
                
                self.log("")  # Пустая строка для разделения
            
            # Отчет о кандидатах на склад 003
            if warehouse_003_candidates:
                self.log("🎯 НАЙДЕНЫ КАНДИДАТЫ НА СКЛАД 003:")
                for j, candidate in enumerate(warehouse_003_candidates, 1):
                    self.log(f"  {j}. ID: {candidate['id']}")
                    self.log(f"     Название: {candidate['name']}")
                    self.log(f"     ID номер: {candidate['id_number']}")
                    self.log(f"     Причина совпадения: {candidate['reason']}")
                    
                    # Тестируем layout-with-cargo для каждого кандидата
                    self.test_layout_api_for_warehouse(candidate['id'], candidate['name'])
                    self.log("")
            else:
                self.log("⚠️ Кандидаты на склад 003 не найдены", "WARNING")
                
        except Exception as e:
            self.log(f"❌ Ошибка анализа складов: {str(e)}", "ERROR")
    
    def get_match_reason(self, warehouse, target):
        """Определить причину совпадения склада"""
        reasons = []
        
        warehouse_id_number = warehouse.get("warehouse_id_number", "")
        warehouse_name = warehouse.get("name", "")
        warehouse_location = warehouse.get("location", "")
        
        if warehouse_id_number == target:
            reasons.append(f"ID номер = {target}")
        if target in warehouse_name:
            reasons.append(f"'{target}' в названии")
        if "Склад №3" in warehouse_name:
            reasons.append("'Склад №3' в названии")
        if "Душанбе" in warehouse_name:
            reasons.append("'Душанбе' в названии")
            
        return ", ".join(reasons) if reasons else "Неизвестная причина"
    
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
                for block in blocks:
                    for shelf in block.get("shelves", []):
                        for cell in shelf.get("cells", []):
                            if cell.get("is_occupied", False):
                                occupied_cells += 1
                
                self.log(f"✅ API доступен для склада {warehouse_id}")
                self.log(f"   📍 Placement records: {len(placement_records)}")
                self.log(f"   📦 Занятых ячеек: {occupied_cells}")
                self.log(f"   🏗️ Блоков: {len(blocks)}")
                
                if len(placement_records) > 0:
                    self.log(f"🎯 НАЙДЕН АКТИВНЫЙ СКЛАД С РАЗМЕЩЕННЫМИ ГРУЗАМИ!")
                    self.analyze_placement_records_summary(placement_records)
                
            elif response.status_code == 404:
                self.log(f"❌ Склад {warehouse_id} не найден в layout-with-cargo")
            else:
                self.log(f"❌ Ошибка API для склада {warehouse_id}: {response.status_code}")
                
        except Exception as e:
            self.log(f"❌ Ошибка тестирования склада {warehouse_id}: {str(e)}", "ERROR")
    
    def analyze_placement_records_summary(self, placement_records):
        """Краткий анализ placement_records"""
        try:
            warehouse_ids = set()
            cargo_numbers = set()
            
            for record in placement_records[:5]:  # Показываем первые 5
                warehouse_id = record.get("warehouse_id", "N/A")
                cargo_number = record.get("cargo_number", "N/A")
                individual_number = record.get("individual_number", "N/A")
                location = record.get("location", "N/A")
                
                warehouse_ids.add(warehouse_id)
                cargo_numbers.add(cargo_number)
                
                self.log(f"   📍 {cargo_number}/{individual_number} -> {location} (warehouse_id: {warehouse_id})")
            
            if len(placement_records) > 5:
                self.log(f"   ... и еще {len(placement_records) - 5} записей")
            
            self.log(f"   📊 Уникальных warehouse_id: {len(warehouse_ids)} ({list(warehouse_ids)})")
            self.log(f"   📦 Уникальных грузов: {len(cargo_numbers)}")
            
        except Exception as e:
            self.log(f"❌ Ошибка анализа placement_records: {str(e)}", "ERROR")
    
    def run_discovery(self):
        """Запуск обнаружения складов"""
        self.log("🎯 НАЧАЛО ОБНАРУЖЕНИЯ СКЛАДОВ И ПОИСКА СКЛАДА 003")
        self.log("=" * 60)
        
        # Этап 1: Авторизация
        if not self.authenticate_warehouse_operator():
            self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться", "ERROR")
            return False
        
        # Этап 2: Обнаружение складов
        self.discover_warehouses()
        
        self.log("=" * 60)
        self.log("📋 ОБНАРУЖЕНИЕ СКЛАДОВ ЗАВЕРШЕНО")
        
        return True

def main():
    """Главная функция"""
    tester = WarehouseDiscoveryTester()
    
    try:
        success = tester.run_discovery()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        tester.log("⚠️ Обнаружение прервано пользователем", "WARNING")
        sys.exit(1)
    except Exception as e:
        tester.log(f"❌ Критическая ошибка: {str(e)}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
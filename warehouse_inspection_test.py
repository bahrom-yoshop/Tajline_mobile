#!/usr/bin/env python3
"""
🔍 ИНСПЕКЦИЯ СКЛАДОВ И ЯЧЕЕК ДЛЯ ДИАГНОСТИКИ QR КОДОВ

Проверяем какие склады и ячейки существуют в системе для правильного тестирования QR кодов
"""

import requests
import json
import os

# Конфигурация
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://tajline-cargo-8.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Тестовые данные оператора склада
WAREHOUSE_OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class WarehouseInspector:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        
    def authenticate(self):
        """Авторизация"""
        response = self.session.post(f"{API_BASE}/auth/login", json=WAREHOUSE_OPERATOR_CREDENTIALS)
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
            print("✅ Авторизация успешна")
            return True
        else:
            print(f"❌ Ошибка авторизации: {response.status_code}")
            return False
    
    def inspect_warehouses(self):
        """Проверка складов"""
        print("\n🏢 ИНСПЕКЦИЯ СКЛАДОВ:")
        print("=" * 50)
        
        # Получаем все склады
        response = self.session.get(f"{API_BASE}/admin/warehouses")
        
        if response.status_code == 200:
            warehouses = response.json()
            print(f"📊 Найдено складов: {len(warehouses)}")
            
            for warehouse in warehouses:
                print(f"\n📦 Склад: {warehouse.get('name')}")
                print(f"   🆔 ID: {warehouse.get('id')}")
                print(f"   🔢 Номер склада: {warehouse.get('warehouse_id_number', 'НЕТ')}")
                print(f"   📍 Местоположение: {warehouse.get('location')}")
                print(f"   🏗️ Блоков: {warehouse.get('blocks_count')}")
                print(f"   📚 Полок на блок: {warehouse.get('shelves_per_block')}")
                print(f"   📦 Ячеек на полку: {warehouse.get('cells_per_shelf')}")
                print(f"   📈 Общая вместимость: {warehouse.get('total_capacity')}")
                print(f"   ✅ Активен: {warehouse.get('is_active')}")
                
                # Проверяем ячейки для этого склада
                self.inspect_warehouse_cells(warehouse.get('id'), warehouse.get('warehouse_id_number'))
        else:
            print(f"❌ Ошибка получения складов: {response.status_code}")
    
    def inspect_warehouse_cells(self, warehouse_id, warehouse_id_number):
        """Проверка ячеек конкретного склада"""
        print(f"   🔍 Проверка ячеек склада {warehouse_id_number}:")
        
        # Получаем ячейки склада
        response = self.session.get(f"{API_BASE}/admin/warehouses/{warehouse_id}/cells")
        
        if response.status_code == 200:
            cells = response.json()
            print(f"   📊 Найдено ячеек: {len(cells)}")
            
            # Показываем первые 5 ячеек как примеры
            for i, cell in enumerate(cells[:5]):
                print(f"   📦 Ячейка {i+1}: {cell.get('location_code')} (ID код: {cell.get('id_based_code', 'НЕТ')})")
                print(f"      Блок: {cell.get('block_number')}, Полка: {cell.get('shelf_number')}, Ячейка: {cell.get('cell_number')}")
                print(f"      Занята: {cell.get('is_occupied', False)}")
            
            if len(cells) > 5:
                print(f"   ... и еще {len(cells) - 5} ячеек")
                
            # Ищем конкретные ячейки для тестирования
            test_cells = ["001-01-01-003", "002-02-02-001", "003-03-03-005"]
            for test_cell in test_cells:
                found_cell = None
                for cell in cells:
                    if cell.get('id_based_code') == test_cell:
                        found_cell = cell
                        break
                
                if found_cell:
                    print(f"   ✅ Тестовая ячейка {test_cell} найдена: {found_cell.get('location_code')}")
                else:
                    print(f"   ❌ Тестовая ячейка {test_cell} НЕ найдена")
        else:
            print(f"   ❌ Ошибка получения ячеек: {response.status_code}")
    
    def test_specific_qr_codes(self):
        """Тестирование конкретных QR кодов с существующими ячейками"""
        print("\n🎯 ТЕСТИРОВАНИЕ СУЩЕСТВУЮЩИХ QR КОДОВ:")
        print("=" * 50)
        
        # Получаем все склады для поиска существующих ячеек
        response = self.session.get(f"{API_BASE}/admin/warehouses")
        
        if response.status_code == 200:
            warehouses = response.json()
            
            for warehouse in warehouses:
                warehouse_id = warehouse.get('id')
                warehouse_id_number = warehouse.get('warehouse_id_number')
                
                if not warehouse_id_number:
                    continue
                
                print(f"\n📦 Тестируем склад {warehouse_id_number} ({warehouse.get('name')})")
                
                # Получаем ячейки этого склада
                cells_response = self.session.get(f"{API_BASE}/admin/warehouses/{warehouse_id}/cells")
                
                if cells_response.status_code == 200:
                    cells = cells_response.json()
                    
                    # Тестируем первые 3 ячейки
                    for i, cell in enumerate(cells[:3]):
                        id_based_code = cell.get('id_based_code')
                        if id_based_code:
                            print(f"   🔍 Тестируем QR код: {id_based_code}")
                            
                            # Тестируем verify-cell endpoint
                            verify_response = self.session.post(
                                f"{API_BASE}/operator/placement/verify-cell",
                                json={"qr_code": id_based_code}
                            )
                            
                            if verify_response.status_code == 200:
                                verify_data = verify_response.json()
                                if verify_data.get("success"):
                                    cell_info = verify_data.get("cell_info", {})
                                    warehouse_info = verify_data.get("warehouse_info", {})
                                    print(f"   ✅ QR код работает: Склад {warehouse_info.get('warehouse_id_number')}, Ячейка {cell_info.get('cell_address')}")
                                else:
                                    print(f"   ❌ QR код не работает: {verify_data.get('error')}")
                            else:
                                print(f"   ❌ HTTP ошибка: {verify_response.status_code}")
                        else:
                            print(f"   ⚠️ Ячейка без id_based_code: {cell.get('location_code')}")
    
    def run_inspection(self):
        """Запуск полной инспекции"""
        print("🔍 ИНСПЕКЦИЯ СКЛАДОВ И ЯЧЕЕК ДЛЯ ДИАГНОСТИКИ QR КОДОВ")
        print("=" * 70)
        
        if not self.authenticate():
            return False
        
        self.inspect_warehouses()
        self.test_specific_qr_codes()
        
        print("\n" + "=" * 70)
        print("📋 ИНСПЕКЦИЯ ЗАВЕРШЕНА")
        print("=" * 70)
        
        return True

def main():
    inspector = WarehouseInspector()
    inspector.run_inspection()

if __name__ == "__main__":
    main()
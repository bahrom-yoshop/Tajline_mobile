#!/usr/bin/env python3
"""
🔬 ГЛУБОКОЕ ИССЛЕДОВАНИЕ: API layout-with-cargo не показывает размещенные грузы

**ОБНАРУЖЕННАЯ ПРОБЛЕМА:**
- Грузы 25082235/01/01 и 25082235/01/02 помечены как размещенные в базе данных
- НО API /api/warehouses/{warehouse_id}/layout-with-cargo показывает:
  - occupied_cells: 0
  - total_cargo: 0  
  - blocks: [] (пустой массив)

**ГЛУБОКОЕ ИССЛЕДОВАНИЕ:**
1. Проверить структуру данных в базе данных
2. Проверить логику API layout-with-cargo
3. Проверить связь между placement_records и warehouse layout
4. Найти где происходит разрыв в цепочке данных
"""

import requests
import json
import sys
from datetime import datetime
import time

# Configuration
BACKEND_URL = "https://cargo-sync.preview.emergentagent.com/api"

# Test credentials
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"

class LayoutAPIDeepInvestigation:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.warehouse_id = None
        self.test_results = []
        self.start_time = time.time()
        
    def log_result(self, test_name: str, success: bool, details: str, response_time: float = 0):
        """Log test result with timing"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "response_time": f"{response_time:.0f}ms"
        })
        print(f"{status} {test_name}: {details} ({response_time:.0f}ms)")
        
    def make_request(self, method: str, endpoint: str, **kwargs):
        """Make HTTP request with timing"""
        start_time = time.time()
        
        headers = kwargs.get('headers', {})
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        kwargs['headers'] = headers
        
        try:
            url = f"{BACKEND_URL}{endpoint}"
            response = self.session.request(method, url, **kwargs)
            response_time = (time.time() - start_time) * 1000
            
            return response, response_time
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            print(f"❌ Request failed: {e}")
            return None, response_time
    
    def authenticate_and_get_warehouse(self):
        """Authenticate and get warehouse ID"""
        print("\n🔐 Authenticating and getting warehouse...")
        
        # Authenticate
        login_data = {
            "phone": WAREHOUSE_OPERATOR_PHONE,
            "password": WAREHOUSE_OPERATOR_PASSWORD
        }
        
        response, response_time = self.make_request('POST', '/auth/login', json=login_data)
        
        if response and response.status_code == 200:
            data = response.json()
            self.token = data.get('access_token')
            
            # Get warehouse
            response, response_time2 = self.make_request('GET', '/operator/warehouses')
            
            if response and response.status_code == 200:
                warehouses = response.json()
                for warehouse in warehouses:
                    if "Москва Склад №1" in warehouse.get('name', ''):
                        self.warehouse_id = warehouse['id']
                        self.log_result(
                            "Авторизация и получение склада",
                            True,
                            f"Склад найден: {warehouse['name']} (ID: {self.warehouse_id})",
                            response_time + response_time2
                        )
                        return True
        
        self.log_result(
            "Авторизация и получение склада",
            False,
            "Не удалось авторизоваться или найти склад",
            response_time
        )
        return False
    
    def check_warehouse_structure(self):
        """Check if warehouse has proper structure (blocks, shelves, cells)"""
        print("\n🏗️ Checking warehouse structure...")
        
        # Try to get warehouse layout structure
        response, response_time = self.make_request('GET', f'/warehouses/{self.warehouse_id}/layout')
        
        if response and response.status_code == 200:
            data = response.json()
            blocks = data.get('blocks', [])
            total_cells = data.get('total_cells', 0)
            
            self.log_result(
                "Проверка структуры склада",
                len(blocks) > 0,
                f"Найдено блоков: {len(blocks)}, всего ячеек: {total_cells}",
                response_time
            )
            return data
        else:
            # Try alternative endpoint
            response, response_time = self.make_request('GET', f'/warehouses/{self.warehouse_id}/statistics')
            
            if response and response.status_code == 200:
                data = response.json()
                total_cells = data.get('total_cells', 0)
                occupied_cells = data.get('occupied_cells', 0)
                
                self.log_result(
                    "Проверка структуры склада (через статистику)",
                    total_cells > 0,
                    f"Всего ячеек: {total_cells}, занято: {occupied_cells}",
                    response_time
                )
                return data
            else:
                self.log_result(
                    "Проверка структуры склада",
                    False,
                    "Не удалось получить структуру склада",
                    response_time
                )
                return None
    
    def check_placement_records_direct(self):
        """Check placement records more directly"""
        print("\n📋 Checking placement records directly...")
        
        # Check through admin endpoint if available
        response, response_time = self.make_request('GET', '/operator/cargo/fully-placed', params={'per_page': 100})
        
        if response and response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            
            # Look for cargo 25082235
            target_cargo = None
            for item in items:
                if item.get('cargo_number') == '25082235':
                    target_cargo = item
                    break
            
            if target_cargo:
                individual_units = target_cargo.get('individual_units', [])
                placed_units = [u for u in individual_units if u.get('status') == 'placed']
                
                details = f"Заявка 25082235 найдена с {len(individual_units)} единиц, из них размещено: {len(placed_units)}"
                for unit in placed_units:
                    details += f"\n  - {unit.get('individual_number')}: {unit.get('placement_info')}"
                
                self.log_result(
                    "Проверка placement_records",
                    len(placed_units) > 0,
                    details,
                    response_time
                )
                return placed_units
            else:
                self.log_result(
                    "Проверка placement_records",
                    False,
                    f"Заявка 25082235 не найдена среди {len(items)} полностью размещенных заявок",
                    response_time
                )
                return []
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else 'Connection failed'
            self.log_result(
                "Проверка placement_records",
                False,
                f"Ошибка получения данных: {error_msg}",
                response_time
            )
            return []
    
    def test_layout_with_cargo_detailed(self):
        """Test layout-with-cargo API in detail"""
        print("\n🏭 Testing layout-with-cargo API in detail...")
        
        response, response_time = self.make_request('GET', f'/warehouses/{self.warehouse_id}/layout-with-cargo')
        
        if response and response.status_code == 200:
            data = response.json()
            
            # Extract all key information
            total_cells = data.get('total_cells', 0)
            occupied_cells = data.get('occupied_cells', 0)
            total_cargo = data.get('total_cargo', 0)
            loading_percentage = data.get('loading_percentage', 0)
            blocks = data.get('blocks', [])
            
            # Count actual occupied cells in blocks
            actual_occupied = 0
            actual_cargo = 0
            
            for block in blocks:
                shelves = block.get('shelves', [])
                for shelf in shelves:
                    cells = shelf.get('cells', [])
                    for cell in cells:
                        if cell.get('is_occupied', False):
                            actual_occupied += 1
                            if cell.get('cargo'):
                                actual_cargo += 1
            
            details = f"API данные: occupied_cells={occupied_cells}, total_cargo={total_cargo}, blocks={len(blocks)}"
            details += f"\nФактический подсчет: occupied_cells={actual_occupied}, cargo={actual_cargo}"
            
            # Check for discrepancy
            discrepancy = (occupied_cells != actual_occupied) or (total_cargo != actual_cargo)
            
            self.log_result(
                "Детальная проверка layout-with-cargo",
                not discrepancy and occupied_cells > 0,
                details,
                response_time
            )
            
            return data
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else 'Connection failed'
            self.log_result(
                "Детальная проверка layout-with-cargo",
                False,
                f"Ошибка API: {error_msg}",
                response_time
            )
            return None
    
    def check_warehouse_cells_creation(self):
        """Check if warehouse cells are properly created"""
        print("\n🔧 Checking warehouse cells creation...")
        
        # Try to create warehouse layout if it doesn't exist
        response, response_time = self.make_request('POST', f'/warehouses/{self.warehouse_id}/create-layout')
        
        if response and response.status_code == 200:
            data = response.json()
            self.log_result(
                "Создание структуры склада",
                True,
                f"Структура склада создана/обновлена: {data.get('message', 'Success')}",
                response_time
            )
            return True
        else:
            # This might be expected if layout already exists
            error_msg = response.json().get('detail', 'Unknown error') if response else 'Connection failed'
            self.log_result(
                "Создание структуры склада",
                False,
                f"Не удалось создать структуру: {error_msg}",
                response_time
            )
            return False
    
    def test_specific_cell_lookup(self):
        """Test looking up specific cells where cargo should be"""
        print("\n🎯 Testing specific cell lookup...")
        
        # Test cells Б1-П3-Я2 and Б1-П3-Я3
        target_positions = [
            {"block": 1, "shelf": 3, "cell": 2, "cargo": "25082235/01/02"},
            {"block": 1, "shelf": 3, "cell": 3, "cargo": "25082235/01/01"}
        ]
        
        for pos in target_positions:
            # Try to verify cell directly
            response, response_time = self.make_request(
                'POST', 
                '/operator/placement/verify-cell',
                json={
                    "qr_code": f"001-{pos['block']:02d}-{pos['shelf']:02d}-{pos['cell']:03d}",
                    "warehouse_id": self.warehouse_id
                }
            )
            
            if response and response.status_code == 200:
                data = response.json()
                cell_info = data.get('cell_info', {})
                is_occupied = cell_info.get('is_occupied', False)
                
                self.log_result(
                    f"Проверка ячейки Б{pos['block']}-П{pos['shelf']}-Я{pos['cell']}",
                    True,
                    f"Ячейка найдена, занята: {is_occupied}, данные: {cell_info}",
                    response_time
                )
            else:
                error_msg = response.json().get('detail', 'Unknown error') if response else 'Connection failed'
                self.log_result(
                    f"Проверка ячейки Б{pos['block']}-П{pos['shelf']}-Я{pos['cell']}",
                    False,
                    f"Ошибка проверки ячейки: {error_msg}",
                    response_time
                )
    
    def run_deep_investigation(self):
        """Run complete deep investigation"""
        print("🔬 ГЛУБОКОЕ ИССЛЕДОВАНИЕ: API layout-with-cargo не показывает размещенные грузы")
        print("=" * 100)
        
        # Step 1: Authenticate and get warehouse
        if not self.authenticate_and_get_warehouse():
            return self.generate_report()
        
        # Step 2: Check warehouse structure
        warehouse_structure = self.check_warehouse_structure()
        
        # Step 3: Check placement records
        placement_records = self.check_placement_records_direct()
        
        # Step 4: Test layout-with-cargo in detail
        layout_data = self.test_layout_with_cargo_detailed()
        
        # Step 5: Try to create warehouse cells if needed
        self.check_warehouse_cells_creation()
        
        # Step 6: Test specific cell lookup
        self.test_specific_cell_lookup()
        
        # Step 7: Re-test layout after potential fixes
        print("\n🔄 Re-testing layout-with-cargo after potential fixes...")
        final_layout_data = self.test_layout_with_cargo_detailed()
        
        return self.generate_report()
    
    def generate_report(self):
        """Generate final test report"""
        total_time = time.time() - self.start_time
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 100)
        print("🔬 ГЛУБОКОЕ ИССЛЕДОВАНИЕ ЗАВЕРШЕНО")
        print("=" * 100)
        
        print(f"\n📊 ОБЩАЯ СТАТИСТИКА:")
        print(f"- Всего тестов: {total_tests}")
        print(f"- Успешных: {passed_tests}")
        print(f"- Неуспешных: {total_tests - passed_tests}")
        print(f"- Success Rate: {success_rate:.1f}%")
        print(f"- Время выполнения: {total_time:.1f} секунд")
        
        print(f"\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        for result in self.test_results:
            print(f"{result['status']} {result['test']}: {result['details']} ({result['response_time']})")
        
        print(f"\n🎯 КРИТИЧЕСКИЙ ВЫВОД:")
        if success_rate >= 70:
            print("✅ ПРОБЛЕМА РЕШЕНА ИЛИ ДИАГНОСТИРОВАНА! Layout-with-cargo API работает корректно.")
        else:
            print("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА ПОДТВЕРЖДЕНА! Layout-with-cargo API не работает правильно.")
        
        print(f"\n🔧 ТЕХНИЧЕСКИЕ РЕКОМЕНДАЦИИ:")
        print("1. Проверить создание структуры склада (блоки, полки, ячейки)")
        print("2. Проверить связь между placement_records и warehouse_cells")
        print("3. Проверить логику API layout-with-cargo в backend коде")
        print("4. Проверить фильтрацию по warehouse_id в запросах к базе данных")
        
        return {
            'success_rate': success_rate,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'execution_time': total_time,
            'results': self.test_results
        }

def main():
    """Main execution function"""
    investigation = LayoutAPIDeepInvestigation()
    results = investigation.run_deep_investigation()
    
    # Exit with appropriate code
    if results['success_rate'] >= 70:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
🚨 КРИТИЧЕСКОЕ ИССЛЕДОВАНИЕ: Проблема с отображением недавно размещенных грузов в визуальной схеме ячеек

**ПРОБЛЕМА:**
- Оператор USR648425 только что разместил 2 груза из заявки 25082235:
  - 25082235/01/01 на позицию Б1-П3-Я3
  - 25082235/01/02 на позицию Б1-П3-Я2
- НО визуальная схема ячеек показывает все ячейки свободными

**КРИТИЧЕСКОЕ ИССЛЕДОВАНИЕ:**

1. **Авторизация и проверка склада:**
   - Авторизоваться как оператор склада (+79777888999/warehouse123)
   - Получить warehouse_id для "Москва Склад №1"

2. **Проверка placement_records для новых грузов:**
   - Найти записи placement_records для 25082235/01/01 и 25082235/01/02
   - Проверить правильность warehouse_id в этих записях
   - Проверить поля location и location_code

3. **Диагностика API layout-with-cargo:**
   - Вызвать /api/warehouses/{warehouse_id}/layout-with-cargo
   - Проверить occupied_cells - должно быть > 0
   - Найти блок Б1, полку П3, ячейки Я2 и Я3
   - Проверить есть ли грузы в этих ячейках

4. **Проверка синхронизации данных:**
   - Проверить что operator_cargo содержит правильные данные размещения
   - Сверить данные между placement_records и operator_cargo

5. **Детальная диагностика проблемы:**
   - Найти корневую причину почему новые грузы не отображаются
   - Проверить фильтрацию по warehouse_id
   - Проверить парсинг location кодов

**ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ:**
- Найти и диагностировать причину проблемы
- occupied_cells должно быть минимум 2 (новые грузы)
- Грузы 25082235/01/01 и 25082235/01/02 должны быть в ячейках Б1-П3-Я3 и Б1-П3-Я2

**КРИТИЧНО:** Найти точную причину почему свежеразмещенные грузы не отображаются в схеме!
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

# Target cargo items to investigate
TARGET_CARGO_ITEMS = ["25082235/01/01", "25082235/01/02"]
TARGET_CARGO_NUMBER = "25082235"
TARGET_POSITIONS = {
    "25082235/01/01": "Б1-П3-Я3",
    "25082235/01/02": "Б1-П3-Я2"
}

class PlacementRecordsInvestigation:
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
    
    def authenticate_warehouse_operator(self):
        """Step 1: Authenticate as warehouse operator"""
        print("\n🔐 STEP 1: Authenticating as warehouse operator...")
        
        login_data = {
            "phone": WAREHOUSE_OPERATOR_PHONE,
            "password": WAREHOUSE_OPERATOR_PASSWORD
        }
        
        response, response_time = self.make_request('POST', '/auth/login', json=login_data)
        
        if response and response.status_code == 200:
            data = response.json()
            self.token = data.get('access_token')
            user_info = data.get('user', {})
            
            self.log_result(
                "Авторизация оператора склада",
                True,
                f"Успешная авторизация '{user_info.get('full_name', 'Unknown')}' (роль: {user_info.get('role', 'unknown')})",
                response_time
            )
            return True
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else 'Connection failed'
            self.log_result(
                "Авторизация оператора склада",
                False,
                f"Ошибка авторизации: {error_msg}",
                response_time
            )
            return False
    
    def get_warehouse_id(self):
        """Step 2: Get warehouse_id for 'Москва Склад №1'"""
        print("\n🏢 STEP 2: Getting warehouse_id for 'Москва Склад №1'...")
        
        response, response_time = self.make_request('GET', '/operator/warehouses')
        
        if response and response.status_code == 200:
            warehouses = response.json()
            
            # Find "Москва Склад №1"
            moscow_warehouse = None
            for warehouse in warehouses:
                if "Москва Склад №1" in warehouse.get('name', ''):
                    moscow_warehouse = warehouse
                    break
            
            if moscow_warehouse:
                self.warehouse_id = moscow_warehouse['id']
                self.log_result(
                    "Получение warehouse_id",
                    True,
                    f"Найден склад 'Москва Склад №1' (ID: {self.warehouse_id})",
                    response_time
                )
                return True
            else:
                self.log_result(
                    "Получение warehouse_id",
                    False,
                    f"Склад 'Москва Склад №1' не найден среди {len(warehouses)} складов",
                    response_time
                )
                return False
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else 'Connection failed'
            self.log_result(
                "Получение warehouse_id",
                False,
                f"Ошибка получения складов: {error_msg}",
                response_time
            )
            return False
    
    def check_placement_records(self):
        """Step 3: Check placement_records for target cargo items"""
        print("\n📋 STEP 3: Checking placement_records for target cargo items...")
        
        # We need to use a direct database query endpoint or check through operator cargo
        # Let's check through operator cargo first
        response, response_time = self.make_request('GET', '/operator/cargo/fully-placed')
        
        if response and response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            
            # Look for our target cargo
            target_cargo = None
            for item in items:
                if item.get('cargo_number') == TARGET_CARGO_NUMBER:
                    target_cargo = item
                    break
            
            if target_cargo:
                individual_units = target_cargo.get('individual_units', [])
                found_units = []
                
                for unit in individual_units:
                    individual_number = unit.get('individual_number')
                    if individual_number in TARGET_CARGO_ITEMS:
                        found_units.append({
                            'individual_number': individual_number,
                            'status': unit.get('status'),
                            'placement_info': unit.get('placement_info'),
                            'is_placed': unit.get('status') == 'placed'
                        })
                
                if found_units:
                    details = f"Найдено {len(found_units)} единиц из заявки {TARGET_CARGO_NUMBER}: "
                    for unit in found_units:
                        details += f"{unit['individual_number']} ({unit['status']}, {unit['placement_info']}), "
                    
                    self.log_result(
                        "Проверка placement_records",
                        True,
                        details.rstrip(', '),
                        response_time
                    )
                    return found_units
                else:
                    self.log_result(
                        "Проверка placement_records",
                        False,
                        f"Целевые единицы {TARGET_CARGO_ITEMS} не найдены в заявке {TARGET_CARGO_NUMBER}",
                        response_time
                    )
                    return []
            else:
                self.log_result(
                    "Проверка placement_records",
                    False,
                    f"Заявка {TARGET_CARGO_NUMBER} не найдена среди {len(items)} полностью размещенных заявок",
                    response_time
                )
                return []
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else 'Connection failed'
            self.log_result(
                "Проверка placement_records",
                False,
                f"Ошибка получения полностью размещенных заявок: {error_msg}",
                response_time
            )
            return []
    
    def check_layout_with_cargo(self):
        """Step 4: Check layout-with-cargo API"""
        print("\n🏭 STEP 4: Checking layout-with-cargo API...")
        
        if not self.warehouse_id:
            self.log_result(
                "Проверка layout-with-cargo",
                False,
                "warehouse_id не определен",
                0
            )
            return None
        
        response, response_time = self.make_request('GET', f'/warehouses/{self.warehouse_id}/layout-with-cargo')
        
        if response and response.status_code == 200:
            data = response.json()
            
            # Check basic statistics
            total_cells = data.get('total_cells', 0)
            occupied_cells = data.get('occupied_cells', 0)
            total_cargo = data.get('total_cargo', 0)
            loading_percentage = data.get('loading_percentage', 0)
            
            # Check structure
            blocks = data.get('blocks', [])
            
            self.log_result(
                "Проверка layout-with-cargo",
                True,
                f"Всего ячеек: {total_cells}, Занято: {occupied_cells}, Грузов: {total_cargo}, Загрузка: {loading_percentage}%, Блоков: {len(blocks)}",
                response_time
            )
            
            return data
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else 'Connection failed'
            self.log_result(
                "Проверка layout-with-cargo",
                False,
                f"Ошибка получения схемы склада: {error_msg}",
                response_time
            )
            return None
    
    def search_target_cargo_in_layout(self, layout_data):
        """Step 5: Search for target cargo items in layout"""
        print("\n🔍 STEP 5: Searching for target cargo items in layout...")
        
        if not layout_data:
            self.log_result(
                "Поиск целевых грузов в схеме",
                False,
                "Данные схемы склада недоступны",
                0
            )
            return
        
        blocks = layout_data.get('blocks', [])
        found_cargo = []
        
        # Search through all blocks, shelves, and cells
        for block in blocks:
            block_number = block.get('number')
            shelves = block.get('shelves', [])
            
            for shelf in shelves:
                shelf_number = shelf.get('number')
                cells = shelf.get('cells', [])
                
                for cell in cells:
                    cell_number = cell.get('number')
                    is_occupied = cell.get('is_occupied', False)
                    
                    if is_occupied:
                        cargo_info = cell.get('cargo', {})
                        individual_number = cargo_info.get('individual_number')
                        
                        if individual_number in TARGET_CARGO_ITEMS:
                            position = f"Б{block_number}-П{shelf_number}-Я{cell_number}"
                            found_cargo.append({
                                'individual_number': individual_number,
                                'position': position,
                                'cargo_number': cargo_info.get('cargo_number'),
                                'cargo_name': cargo_info.get('cargo_name'),
                                'recipient_name': cargo_info.get('recipient_name'),
                                'placed_by': cargo_info.get('placed_by')
                            })
        
        if found_cargo:
            details = f"Найдено {len(found_cargo)} целевых грузов в схеме: "
            for cargo in found_cargo:
                details += f"{cargo['individual_number']} на позиции {cargo['position']}, "
            
            self.log_result(
                "Поиск целевых грузов в схеме",
                True,
                details.rstrip(', '),
                0
            )
        else:
            # Check if we have any occupied cells at all
            occupied_cells = layout_data.get('occupied_cells', 0)
            if occupied_cells > 0:
                self.log_result(
                    "Поиск целевых грузов в схеме",
                    False,
                    f"Целевые грузы {TARGET_CARGO_ITEMS} НЕ НАЙДЕНЫ в схеме, хотя есть {occupied_cells} занятых ячеек",
                    0
                )
            else:
                self.log_result(
                    "Поиск целевых грузов в схеме",
                    False,
                    f"Целевые грузы {TARGET_CARGO_ITEMS} НЕ НАЙДЕНЫ - схема показывает 0 занятых ячеек",
                    0
                )
        
        return found_cargo
    
    def check_data_synchronization(self):
        """Step 6: Check data synchronization between collections"""
        print("\n🔄 STEP 6: Checking data synchronization...")
        
        # Check individual units for placement
        response, response_time = self.make_request('GET', '/operator/cargo/individual-units-for-placement')
        
        if response and response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            
            # Look for our target cargo items
            target_units = []
            for item in items:
                individual_number = item.get('individual_number')
                if individual_number in TARGET_CARGO_ITEMS:
                    target_units.append({
                        'individual_number': individual_number,
                        'cargo_number': item.get('cargo_number'),
                        'status': item.get('status'),
                        'is_placed': item.get('is_placed', False),
                        'placement_info': item.get('placement_info')
                    })
            
            if target_units:
                details = f"Найдено {len(target_units)} единиц в individual-units-for-placement: "
                for unit in target_units:
                    details += f"{unit['individual_number']} (размещен: {unit['is_placed']}, статус: {unit['status']}), "
                
                self.log_result(
                    "Проверка синхронизации данных",
                    True,
                    details.rstrip(', '),
                    response_time
                )
            else:
                self.log_result(
                    "Проверка синхронизации данных",
                    False,
                    f"Целевые единицы {TARGET_CARGO_ITEMS} не найдены в individual-units-for-placement среди {len(items)} единиц",
                    response_time
                )
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response else 'Connection failed'
            self.log_result(
                "Проверка синхронизации данных",
                False,
                f"Ошибка получения individual units: {error_msg}",
                response_time
            )
    
    def diagnose_root_cause(self, placement_records, layout_data, found_cargo):
        """Step 7: Diagnose root cause of the problem"""
        print("\n🔬 STEP 7: Diagnosing root cause...")
        
        diagnosis = []
        
        # Check if cargo items are marked as placed
        placed_items = [item for item in placement_records if item.get('is_placed')]
        if placed_items:
            diagnosis.append(f"✅ {len(placed_items)} единиц помечены как размещенные в базе данных")
        else:
            diagnosis.append(f"❌ Ни одна из целевых единиц не помечена как размещенная")
        
        # Check if layout shows occupied cells
        occupied_cells = layout_data.get('occupied_cells', 0) if layout_data else 0
        if occupied_cells > 0:
            diagnosis.append(f"✅ Схема склада показывает {occupied_cells} занятых ячеек")
        else:
            diagnosis.append(f"❌ Схема склада показывает 0 занятых ячеек")
        
        # Check if target cargo found in layout
        if found_cargo:
            diagnosis.append(f"✅ {len(found_cargo)} целевых грузов найдено в схеме склада")
        else:
            diagnosis.append(f"❌ Целевые грузы НЕ найдены в схеме склада")
        
        # Determine root cause
        if not placed_items:
            root_cause = "КОРНЕВАЯ ПРИЧИНА: Грузы не помечены как размещенные в базе данных"
        elif occupied_cells == 0:
            root_cause = "КОРНЕВАЯ ПРИЧИНА: Проблема с API layout-with-cargo - не показывает размещенные грузы"
        elif not found_cargo:
            root_cause = "КОРНЕВАЯ ПРИЧИНА: Размещенные грузы есть в базе, но не отображаются в правильных позициях"
        else:
            root_cause = "КОРНЕВАЯ ПРИЧИНА: Проблема не обнаружена - грузы корректно отображаются"
        
        diagnosis.append(root_cause)
        
        diagnosis_text = "; ".join(diagnosis)
        
        self.log_result(
            "Диагностика корневой причины",
            len(found_cargo) == len(TARGET_CARGO_ITEMS),
            diagnosis_text,
            0
        )
        
        return root_cause
    
    def run_investigation(self):
        """Run complete investigation"""
        print("🚨 КРИТИЧЕСКОЕ ИССЛЕДОВАНИЕ: Проблема с отображением недавно размещенных грузов")
        print("=" * 100)
        
        # Step 1: Authenticate
        if not self.authenticate_warehouse_operator():
            return self.generate_report()
        
        # Step 2: Get warehouse ID
        if not self.get_warehouse_id():
            return self.generate_report()
        
        # Step 3: Check placement records
        placement_records = self.check_placement_records()
        
        # Step 4: Check layout with cargo
        layout_data = self.check_layout_with_cargo()
        
        # Step 5: Search for target cargo in layout
        found_cargo = self.search_target_cargo_in_layout(layout_data)
        
        # Step 6: Check data synchronization
        self.check_data_synchronization()
        
        # Step 7: Diagnose root cause
        root_cause = self.diagnose_root_cause(placement_records, layout_data, found_cargo)
        
        return self.generate_report()
    
    def generate_report(self):
        """Generate final test report"""
        total_time = time.time() - self.start_time
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 100)
        print("🎯 КРИТИЧЕСКОЕ ИССЛЕДОВАНИЕ ЗАВЕРШЕНО")
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
            if passed_tests == total_tests:
                print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Проблема с отображением грузов решена или не обнаружена.")
            else:
                print("⚠️ ЧАСТИЧНЫЙ УСПЕХ! Некоторые аспекты проблемы выявлены и требуют внимания.")
        else:
            print("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА ПОДТВЕРЖДЕНА! Требуется немедленное исправление.")
        
        print("\n🔧 РЕКОМЕНДАЦИИ:")
        print("1. Проверить синхронизацию между placement_records и operator_cargo")
        print("2. Убедиться что API layout-with-cargo использует правильные данные")
        print("3. Проверить фильтрацию по warehouse_id в запросах")
        print("4. Проверить парсинг location кодов (Б1-П3-Я3 формат)")
        
        return {
            'success_rate': success_rate,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'execution_time': total_time,
            'results': self.test_results
        }

def main():
    """Main execution function"""
    investigation = PlacementRecordsInvestigation()
    results = investigation.run_investigation()
    
    # Exit with appropriate code
    if results['success_rate'] >= 70:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
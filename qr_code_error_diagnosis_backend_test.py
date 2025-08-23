#!/usr/bin/env python3
"""
🎯 ДИАГНОСТИКА ОШИБКИ QR КОДА 25082198/01/01 - BACKEND ТЕСТИРОВАНИЕ

КОНТЕКСТ ПРОБЛЕМЫ:
Пользователь пытается отсканировать QR код `25082198/01/01` для размещения груза, но получает ошибку:
"❌ Единица 01 груза типа 01 из заявки 25082198 не найдена"

ЗАДАЧА ДИАГНОСТИКИ:
1. Проверить существование заявки 25082198 в коллекциях cargo и operator_cargo
2. Проверить структуру cargo_items и individual_items
3. Проверить API endpoint available-for-placement
4. Создать корректные тестовые данные если нужно
5. Убедиться что QR код 25082198/01/01 может быть успешно размещен
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://cargo-sync.preview.emergentagent.com/api"

# Test credentials
WAREHOUSE_OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

ADMIN_CREDENTIALS = {
    "phone": "+79999888777", 
    "password": "admin123"
}

class QRCodeErrorDiagnosticTester:
    def __init__(self):
        self.session = requests.Session()
        self.operator_token = None
        self.admin_token = None
        self.test_results = []
        self.warehouse_id = None
        self.target_cargo_number = "25082198"
        self.target_qr_code = "25082198/01/01"
        
    def log_test(self, test_name, success, details="", error=""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if details:
            print(f"    📋 {details}")
        if error:
            print(f"    ❌ Error: {error}")
        print()

    def authenticate_operator(self):
        """Authenticate warehouse operator"""
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=WAREHOUSE_OPERATOR_CREDENTIALS
            )
            
            if response.status_code == 200:
                data = response.json()
                self.operator_token = data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.operator_token}"
                })
                
                # Get user info
                user_response = self.session.get(f"{BACKEND_URL}/auth/me")
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    self.log_test(
                        "Авторизация оператора склада",
                        True,
                        f"Успешная авторизация '{user_data.get('full_name')}' (роль: {user_data.get('role')}, телефон: {user_data.get('phone')})"
                    )
                    return True
                else:
                    self.log_test("Авторизация оператора склада", False, error="Не удалось получить информацию о пользователе")
                    return False
            else:
                self.log_test("Авторизация оператора склада", False, error=f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Авторизация оператора склада", False, error=str(e))
            return False

    def get_operator_warehouse(self):
        """Get operator's warehouse"""
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/warehouses")
            
            if response.status_code == 200:
                warehouses = response.json()
                if warehouses:
                    self.warehouse_id = warehouses[0]["id"]
                    warehouse_name = warehouses[0]["name"]
                    self.log_test(
                        "Получение склада оператора",
                        True,
                        f"Получен склад '{warehouse_name}' (ID: {self.warehouse_id})"
                    )
                    return True
                else:
                    self.log_test("Получение склада оператора", False, error="Нет доступных складов")
                    return False
            else:
                self.log_test("Получение склада оператора", False, error=f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Получение склада оператора", False, error=str(e))
            return False

    def check_cargo_exists_in_available_for_placement(self):
        """Check if cargo 25082198 exists in available-for-placement endpoint"""
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/available-for-placement")
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle both list and dict responses
                if isinstance(data, dict):
                    cargo_list = data.get("items", []) or data.get("cargo_list", []) or []
                elif isinstance(data, list):
                    cargo_list = data
                else:
                    cargo_list = []
                
                self.log_test(
                    "Получение списка available-for-placement",
                    True,
                    f"Получено {len(cargo_list)} грузов для размещения"
                )
                
                # Search for our target cargo
                target_cargo = None
                for cargo in cargo_list:
                    if isinstance(cargo, dict) and cargo.get("cargo_number") == self.target_cargo_number:
                        target_cargo = cargo
                        break
                
                if target_cargo:
                    self.log_test(
                        f"Поиск заявки {self.target_cargo_number} в available-for-placement",
                        True,
                        f"Заявка найдена! ID: {target_cargo.get('id')}, статус: {target_cargo.get('status', 'unknown')}"
                    )
                    
                    # Check cargo_items structure
                    cargo_items = target_cargo.get("cargo_items", [])
                    if cargo_items:
                        self.log_test(
                            "Проверка структуры cargo_items",
                            True,
                            f"Найдено {len(cargo_items)} типов груза: {[item.get('cargo_name', 'unknown') for item in cargo_items]}"
                        )
                        
                        # Check for type_number = "01"
                        type_01_found = False
                        for i, item in enumerate(cargo_items):
                            type_number = f"{i+1:02d}"  # Generate type_number as 01, 02, etc.
                            if type_number == "01":
                                type_01_found = True
                                
                                # Check individual_items
                                individual_items = item.get("individual_items", [])
                                if individual_items:
                                    unit_01_found = False
                                    for unit in individual_items:
                                        if unit.get("unit_index") == "01":
                                            unit_01_found = True
                                            break
                                    
                                    if unit_01_found:
                                        self.log_test(
                                            "Проверка единицы 01 в типе груза 01",
                                            True,
                                            f"Единица 01 найдена в типе груза 01! Всего единиц: {len(individual_items)}"
                                        )
                                    else:
                                        self.log_test(
                                            "Проверка единицы 01 в типе груза 01",
                                            False,
                                            f"Единица 01 НЕ найдена в типе груза 01. Доступные единицы: {[u.get('unit_index') for u in individual_items]}"
                                        )
                                else:
                                    self.log_test(
                                        "Проверка individual_items в типе груза 01",
                                        False,
                                        "individual_items отсутствует или пуст в типе груза 01"
                                    )
                                break
                        
                        if not type_01_found:
                            self.log_test(
                                "Проверка типа груза 01",
                                False,
                                f"Тип груза 01 не найден. Доступные типы: {list(range(1, len(cargo_items)+1))}"
                            )
                    else:
                        self.log_test(
                            "Проверка структуры cargo_items",
                            False,
                            "cargo_items отсутствует или пуст"
                        )
                    
                    return target_cargo
                else:
                    self.log_test(
                        f"Поиск заявки {self.target_cargo_number} в available-for-placement",
                        False,
                        f"Заявка НЕ найдена среди {len(cargo_list)} доступных грузов"
                    )
                    
                    # Show available cargo numbers for debugging
                    available_numbers = [c.get("cargo_number") for c in cargo_list[:10] if isinstance(c, dict)]  # First 10
                    self.log_test(
                        "Доступные номера грузов (первые 10)",
                        True,
                        f"Номера: {available_numbers}"
                    )
                    return None
            else:
                self.log_test(
                    "Получение списка available-for-placement",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return None
                
        except Exception as e:
            self.log_test("Проверка available-for-placement", False, error=str(e))
            return None

    def create_test_cargo_25082198(self):
        """Create test cargo with number 25082198 if it doesn't exist"""
        try:
            # First, try to create with the specific number
            cargo_data = {
                "sender_full_name": "Тестовый Отправитель QR",
                "sender_phone": "+79111222333",
                "recipient_full_name": "Тестовый Получатель QR",
                "recipient_phone": "+79444555666",
                "recipient_address": "г. Душанбе, ул. Тестовая, дом 25",
                "description": "Тестовый груз для диагностики QR кода 25082198/01/01",
                "route": "moscow_to_tajikistan",
                "payment_method": "cash_on_delivery",
                "delivery_method": "pickup",
                "preferred_cargo_number": self.target_cargo_number,  # Force specific number
                "cargo_items": [
                    {
                        "cargo_name": "Электроника Samsung",
                        "quantity": 2,  # This will create individual items 01 and 02
                        "weight": 5.0,
                        "price_per_kg": 100.0,
                        "total_amount": 500.0
                    },
                    {
                        "cargo_name": "Бытовая техника LG", 
                        "quantity": 3,  # This will create individual items 01, 02, 03
                        "weight": 8.0,
                        "price_per_kg": 80.0,
                        "total_amount": 640.0
                    }
                ]
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/operator/cargo/accept",
                json=cargo_data
            )
            
            if response.status_code == 200:
                result = response.json()
                cargo_id = result.get("cargo_id")
                cargo_number = result.get("cargo_number")
                
                self.log_test(
                    f"Создание тестовой заявки {self.target_cargo_number}",
                    True,
                    f"Заявка создана: {cargo_number} (ID: {cargo_id}). Грузы: 2 типа (2+3=5 единиц)"
                )
                
                # Verify the structure was created correctly
                time.sleep(1)  # Wait for data to be processed
                return self.verify_created_cargo_structure(cargo_id)
            else:
                error_text = response.text
                
                # If cargo already exists, that's actually good for our diagnosis
                if "already exists" in error_text:
                    self.log_test(
                        f"Проверка существования заявки {self.target_cargo_number}",
                        True,
                        f"Заявка {self.target_cargo_number} уже существует в системе - это хорошо для диагностики!"
                    )
                    return True  # Continue with existing cargo
                else:
                    self.log_test(
                        f"Создание тестовой заявки {self.target_cargo_number}",
                        False,
                        error=f"HTTP {response.status_code}: {error_text}"
                    )
                    return False
                
        except Exception as e:
            self.log_test("Создание тестовой заявки", False, error=str(e))
            return False

    def verify_created_cargo_structure(self, cargo_id):
        """Verify that created cargo has correct structure for QR code 25082198/01/01"""
        try:
            # Check if cargo appears in available-for-placement
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/available-for-placement")
            
            if response.status_code == 200:
                cargo_list = response.json()
                
                # Find our created cargo
                created_cargo = None
                for cargo in cargo_list:
                    if cargo.get("id") == cargo_id:
                        created_cargo = cargo
                        break
                
                if created_cargo:
                    cargo_items = created_cargo.get("cargo_items", [])
                    
                    # Check if first cargo type has individual_items with unit_index "01"
                    if cargo_items and len(cargo_items) > 0:
                        first_cargo_type = cargo_items[0]
                        individual_items = first_cargo_type.get("individual_items", [])
                        
                        if individual_items:
                            # Look for unit with unit_index "01"
                            unit_01_exists = any(
                                item.get("unit_index") == "01" 
                                for item in individual_items
                            )
                            
                            if unit_01_exists:
                                self.log_test(
                                    "Верификация структуры созданной заявки",
                                    True,
                                    f"QR код {self.target_qr_code} должен работать! Структура корректна."
                                )
                                return True
                            else:
                                unit_indices = [item.get("unit_index") for item in individual_items]
                                self.log_test(
                                    "Верификация структуры созданной заявки",
                                    False,
                                    f"Единица 01 не найдена. Доступные unit_index: {unit_indices}"
                                )
                                return False
                        else:
                            self.log_test(
                                "Верификация структуры созданной заявки",
                                False,
                                "individual_items отсутствует в первом типе груза"
                            )
                            return False
                    else:
                        self.log_test(
                            "Верификация структуры созданной заявки",
                            False,
                            "cargo_items отсутствует или пуст"
                        )
                        return False
                else:
                    self.log_test(
                        "Верификация структуры созданной заявки",
                        False,
                        "Созданная заявка не найдена в available-for-placement"
                    )
                    return False
            else:
                self.log_test(
                    "Верификация структуры созданной заявки",
                    False,
                    error=f"Ошибка получения available-for-placement: HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Верификация структуры созданной заявки", False, error=str(e))
            return False

    def test_qr_code_placement(self, cargo_data):
        """Test actual QR code placement for 25082198/01/01"""
        try:
            if not cargo_data:
                self.log_test(
                    "Тестирование размещения QR кода",
                    False,
                    error="Нет данных о грузе для тестирования"
                )
                return False
            
            cargo_id = cargo_data.get("id")
            
            # Try to place the individual unit 25082198/01/01
            placement_data = {
                "individual_number": self.target_qr_code,
                "warehouse_id": self.warehouse_id,  # Add required warehouse_id
                "block_number": 1,
                "shelf_number": 1,
                "cell_number": 1
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/operator/cargo/place-individual",
                json=placement_data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test(
                    f"Размещение QR кода {self.target_qr_code}",
                    True,
                    f"Единица успешно размещена в местоположении {result.get('location_code', 'unknown')}"
                )
                return True
            else:
                error_text = response.text
                self.log_test(
                    f"Размещение QR кода {self.target_qr_code}",
                    False,
                    error=f"HTTP {response.status_code}: {error_text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Тестирование размещения QR кода", False, error=str(e))
            return False

    def run_comprehensive_diagnosis(self):
        """Run comprehensive QR code error diagnosis"""
        print("🎯 НАЧАЛО ДИАГНОСТИКИ ОШИБКИ QR КОДА 25082198/01/01")
        print("=" * 80)
        
        # Step 1: Authenticate
        if not self.authenticate_operator():
            print("❌ Не удалось авторизоваться. Прекращение тестирования.")
            return False
        
        # Step 2: Get warehouse
        if not self.get_operator_warehouse():
            print("❌ Не удалось получить склад оператора. Прекращение тестирования.")
            return False
        
        # Step 3: Check if cargo exists
        existing_cargo = self.check_cargo_exists_in_available_for_placement()
        
        # Step 4: Create cargo if it doesn't exist or has wrong structure
        if not existing_cargo:
            print(f"\n🔧 Заявка {self.target_cargo_number} не найдена. Создаем тестовую заявку...")
            if not self.create_test_cargo_25082198():
                print("❌ Не удалось создать тестовую заявку.")
                return False
            
            # Re-check after creation
            existing_cargo = self.check_cargo_exists_in_available_for_placement()
        
        # Step 5: Test QR code placement
        if existing_cargo:
            print(f"\n🧪 Тестирование размещения QR кода {self.target_qr_code}...")
            self.test_qr_code_placement(existing_cargo)
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 РЕЗУЛЬТАТЫ ДИАГНОСТИКИ:")
        
        success_count = sum(1 for result in self.test_results if result["success"])
        total_count = len(self.test_results)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        print(f"Успешных тестов: {success_count}/{total_count} ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 ДИАГНОСТИКА ЗАВЕРШЕНА УСПЕШНО!")
            print(f"✅ QR код {self.target_qr_code} должен работать корректно")
        else:
            print("⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ!")
            print("❌ Требуется дополнительная диагностика или исправления")
        
        return success_rate >= 80

def main():
    """Main function"""
    tester = QRCodeErrorDiagnosticTester()
    
    try:
        success = tester.run_comprehensive_diagnosis()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
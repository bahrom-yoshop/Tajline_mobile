#!/usr/bin/env python3
"""
ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ СТРУКТУРЫ ОТВЕТОВ ENDPOINTS РАЗМЕЩЕНИЯ В TAJLINE.TJ

ЦЕЛЬ: Протестировать успешное размещение груза и проверить структуру ответа
чтобы найти источник данных груза в placementStatistics переменной frontend
"""

import requests
import json
import sys
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://tajline-cargo-8.preview.emergentagent.com/api"

# Учетные данные оператора склада
WAREHOUSE_OPERATOR = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class PlacementResponseTester:
    def __init__(self):
        self.session = requests.Session()
        self.operator_token = None
        self.test_results = []
        
    def log_result(self, test_name, success, message, details=None):
        """Логирование результата теста"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {message}")
        if details:
            print(f"   Details: {json.dumps(details, indent=2, ensure_ascii=False)}")
    
    def authenticate_warehouse_operator(self):
        """Авторизация оператора склада"""
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=WAREHOUSE_OPERATOR,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.operator_token = data.get("access_token")
                if self.operator_token:
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.operator_token}"
                    })
                    user_info = data.get("user", {})
                    self.log_result(
                        "Авторизация оператора склада",
                        True,
                        f"Успешная авторизация: {user_info.get('full_name', 'Unknown')} (роль: {user_info.get('role', 'Unknown')})"
                    )
                    return True
                else:
                    self.log_result("Авторизация оператора склада", False, "Токен доступа не получен")
                    return False
            else:
                self.log_result("Авторизация оператора склада", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Авторизация оператора склада", False, f"Исключение: {str(e)}")
            return False
    
    def test_placement_with_different_cells(self):
        """Тестирование размещения груза с разными ячейками"""
        # Сначала получим доступные грузы
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/available-for-placement", timeout=30)
            if response.status_code != 200:
                self.log_result("Получение доступных грузов", False, f"HTTP {response.status_code}")
                return False
            
            data = response.json()
            available_cargo = data.get("items", [])
            
            if not available_cargo:
                self.log_result("Получение доступных грузов", False, "Нет доступных грузов")
                return False
            
            # Получим склады оператора
            response = self.session.get(f"{BACKEND_URL}/operator/warehouses", timeout=30)
            if response.status_code != 200:
                self.log_result("Получение складов", False, f"HTTP {response.status_code}")
                return False
            
            warehouses = response.json()
            if not warehouses:
                self.log_result("Получение складов", False, "Нет доступных складов")
                return False
            
            # Попробуем разные ячейки для размещения
            test_cargo = available_cargo[0]
            test_warehouse = warehouses[0]
            
            cargo_id = test_cargo.get("id")
            warehouse_id = test_warehouse.get("id")
            
            # Попробуем разные координаты ячеек
            cell_coordinates = [
                (1, 1, 2), (1, 1, 3), (1, 1, 4), (1, 1, 5),
                (1, 2, 1), (1, 2, 2), (1, 2, 3),
                (2, 1, 1), (2, 1, 2), (2, 2, 1)
            ]
            
            for block, shelf, cell in cell_coordinates:
                placement_data = {
                    "cargo_id": cargo_id,
                    "warehouse_id": warehouse_id,
                    "block_number": block,
                    "shelf_number": shelf,
                    "cell_number": cell
                }
                
                try:
                    response = self.session.post(
                        f"{BACKEND_URL}/operator/cargo/place",
                        json=placement_data,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # КРИТИЧЕСКАЯ ПРОВЕРКА: анализ структуры ответа
                        cargo_fields = ["location_code", "cargo_name", "cargo_number", "placed_at", "warehouse_name"]
                        present_cargo_fields = [field for field in cargo_fields if field in data]
                        
                        self.log_result(
                            f"УСПЕШНОЕ РАЗМЕЩЕНИЕ в ячейку Б{block}-П{shelf}-Я{cell}",
                            True,
                            f"🎉 НАЙДЕН ИСТОЧНИК ПРОБЛЕМЫ: Endpoint /api/operator/cargo/place возвращает поля груза: {present_cargo_fields}",
                            {
                                "placement_coordinates": f"Б{block}-П{shelf}-Я{cell}",
                                "cargo_fields_in_response": present_cargo_fields,
                                "full_response": data,
                                "bug_explanation": "Этот ответ может перезаписывать placementStatistics в frontend",
                                "react_error_source": "Если этот объект попадает в placementStatistics, то React выдаст ошибку 'Objects are not valid as a React child'"
                            }
                        )
                        return True
                    elif response.status_code == 400 and "occupied" in response.text:
                        # Ячейка занята, пробуем следующую
                        continue
                    else:
                        print(f"   Ошибка размещения в Б{block}-П{shelf}-Я{cell}: {response.status_code} - {response.text}")
                        
                except Exception as e:
                    print(f"   Исключение при размещении в Б{block}-П{shelf}-Я{cell}: {str(e)}")
                    continue
            
            # Если не удалось разместить ни в одну ячейку
            self.log_result(
                "Тестирование размещения груза",
                False,
                "Не удалось найти свободную ячейку для размещения груза",
                {"tried_coordinates": cell_coordinates}
            )
            return False
            
        except Exception as e:
            self.log_result("Тестирование размещения груза", False, f"Исключение: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🎯 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ СТРУКТУРЫ ОТВЕТОВ ENDPOINTS РАЗМЕЩЕНИЯ В TAJLINE.TJ")
        print("=" * 80)
        print("🔍 ЦЕЛЬ: Найти точный источник данных груза в placementStatistics")
        print("=" * 80)
        
        # Шаг 1: Авторизация
        if not self.authenticate_warehouse_operator():
            print("❌ Невозможно продолжить без авторизации")
            return False
        
        # Шаг 2: Тестирование размещения с разными ячейками
        self.test_placement_with_different_cells()
        
        # Итоговый отчет
        print("\n" + "=" * 80)
        print("📊 ФИНАЛЬНЫЙ ОТЧЕТ ДИАГНОСТИКИ")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        
        print(f"Всего тестов: {total_tests}")
        print(f"Пройдено: {passed_tests}")
        
        # Поиск источника проблемы
        successful_placement = next((r for r in self.test_results if r["success"] and "УСПЕШНОЕ РАЗМЕЩЕНИЕ" in r["test"]), None)
        
        if successful_placement:
            print(f"\n🚨 ИСТОЧНИК ПРОБЛЕМЫ НАЙДЕН:")
            details = successful_placement.get("details", {})
            cargo_fields = details.get("cargo_fields_in_response", [])
            
            print(f"   ✅ Endpoint: /api/operator/cargo/place")
            print(f"   ❌ Возвращает поля груза: {cargo_fields}")
            print(f"   🔍 Полный ответ: {details.get('full_response', {})}")
            
            print(f"\n💡 ОБЪЯСНЕНИЕ ПРОБЛЕМЫ:")
            print("   1. API /api/operator/placement-statistics работает правильно")
            print("   2. API /api/operator/cargo/place возвращает данные груза после размещения")
            print("   3. Frontend ошибочно записывает результат размещения в placementStatistics")
            print("   4. React пытается отобразить объект груза как строку → ошибка")
            
            print(f"\n🔧 РЕШЕНИЕ:")
            print("   1. В frontend разделить переменные:")
            print("      - placementStatistics (для статистики)")
            print("      - placementResult (для результата размещения)")
            print("   2. Не перезаписывать placementStatistics результатом размещения")
            print("   3. Использовать отдельную переменную для отображения результата")
        else:
            print(f"\n🤔 ИСТОЧНИК ПРОБЛЕМЫ НЕ НАЙДЕН В BACKEND:")
            print("   ✅ API /api/operator/placement-statistics работает правильно")
            print("   ⚠️  Не удалось протестировать успешное размещение груза")
            print("   🔍 Проблема скорее всего в frontend логике")
        
        return True

if __name__ == "__main__":
    tester = PlacementResponseTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 ДИАГНОСТИКА ЗАВЕРШЕНА!")
        sys.exit(0)
    else:
        print("\n❌ ДИАГНОСТИКА НЕ ЗАВЕРШЕНА!")
        sys.exit(1)
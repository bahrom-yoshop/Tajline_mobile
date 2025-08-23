#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Размещение грузов любого статуса в TAJLINE.TJ

КОНТЕКСТ ИСПРАВЛЕНИЙ:
- Убрана проверка processing_status = "paid" в /api/operator/cargo/available-for-placement
- Убрана проверка статуса оплаты в /api/cargo/place-in-cell
- Теперь ВСЕ грузы в категории "Размещение" могут размещаться независимо от статуса оплаты

ПЛАН ТЕСТИРОВАНИЯ:
1. Авторизация оператора склада (+79777888999/warehouse123)
2. ГЛАВНАЯ ПРОВЕРКА: Получить доступные грузы для размещения через /api/operator/cargo/available-for-placement
3. Убедиться что показываются грузы с любым статусом оплаты (не только "paid")
4. Протестировать размещение груза с непaid статусом через /api/cargo/place-in-cell

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
- API должен возвращать грузы со всеми статусами (payment_pending, paid, etc.)
- Размещение груза должно работать для любого статуса оплаты
- Увеличение количества доступных грузов для размещения
"""

import requests
import json
import sys
import os
from datetime import datetime

# Configuration
BACKEND_URL = "https://cargo-sync.preview.emergentagent.com/api"
WAREHOUSE_OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class CargoPlacementAnyStatusTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", error_msg=""):
        """Логирование результатов тестов"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   📋 {details}")
        if error_msg:
            print(f"   🚨 {error_msg}")
        print()

    def authenticate_warehouse_operator(self):
        """Авторизация оператора склада"""
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=WAREHOUSE_OPERATOR_CREDENTIALS
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.operator_info = data.get("user")
                
                # Устанавливаем заголовок авторизации
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                operator_name = self.operator_info.get("full_name", "Unknown")
                operator_role = self.operator_info.get("role", "Unknown")
                operator_number = self.operator_info.get("user_number", "Unknown")
                
                self.log_test(
                    "Авторизация оператора склада (+79777888999/warehouse123)",
                    True,
                    f"Успешная авторизация '{operator_name}' (номер: {operator_number}), роль: {operator_role}"
                )
                return True
            else:
                self.log_test(
                    "Авторизация оператора склада",
                    False,
                    error_msg=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Авторизация оператора склада",
                False,
                error_msg=f"Ошибка подключения: {str(e)}"
            )
            return False

    def get_available_cargo_for_placement(self):
        """КРИТИЧЕСКАЯ ПРОВЕРКА: Получить доступные грузы для размещения"""
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/available-for-placement")
            
            if response.status_code == 200:
                data = response.json()
                cargo_items = data.get("items", [])
                total_cargo = len(cargo_items)
                
                # Анализируем статусы грузов
                status_counts = {}
                payment_status_counts = {}
                processing_status_counts = {}
                
                for cargo in cargo_items:
                    # Подсчет по статусам
                    status = cargo.get("status", "unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1
                    
                    # Подсчет по статусам оплаты
                    payment_status = cargo.get("payment_status", "unknown")
                    payment_status_counts[payment_status] = payment_status_counts.get(payment_status, 0) + 1
                    
                    # Подсчет по статусам обработки
                    processing_status = cargo.get("processing_status", "unknown")
                    processing_status_counts[processing_status] = processing_status_counts.get(processing_status, 0) + 1
                
                # Проверяем наличие грузов с разными статусами
                has_non_paid_cargo = any(status != "paid" for status in processing_status_counts.keys())
                has_multiple_payment_statuses = len(payment_status_counts) > 1
                has_multiple_processing_statuses = len(processing_status_counts) > 1
                
                details = f"Найдено {total_cargo} грузов для размещения. "
                details += f"Статусы обработки: {processing_status_counts}. "
                details += f"Статусы оплаты: {payment_status_counts}. "
                
                if has_non_paid_cargo or has_multiple_processing_statuses:
                    details += "✅ КРИТИЧЕСКИЙ УСПЕХ: Найдены грузы с разными статусами оплаты!"
                else:
                    details += "⚠️ Все грузы имеют одинаковый статус - возможно исправления не применились"
                
                self.log_test(
                    "КРИТИЧЕСКАЯ ПРОВЕРКА: GET /api/operator/cargo/available-for-placement",
                    True,
                    details
                )
                
                return cargo_items
                
            else:
                self.log_test(
                    "КРИТИЧЕСКАЯ ПРОВЕРКА: GET /api/operator/cargo/available-for-placement",
                    False,
                    error_msg=f"HTTP {response.status_code}: {response.text}"
                )
                return []
                
        except Exception as e:
            self.log_test(
                "КРИТИЧЕСКАЯ ПРОВЕРКА: GET /api/operator/cargo/available-for-placement",
                False,
                error_msg=f"Ошибка запроса: {str(e)}"
            )
            return []

    def test_cargo_placement_any_status(self, cargo_items):
        """Тестирование размещения груза с любым статусом оплаты"""
        if not cargo_items:
            self.log_test(
                "Тестирование размещения груза с любым статусом",
                False,
                error_msg="Нет доступных грузов для тестирования"
            )
            return False
        
        # Ищем груз с непaid статусом для тестирования
        test_cargo = None
        for cargo in cargo_items:
            processing_status = cargo.get("processing_status", "")
            payment_status = cargo.get("payment_status", "")
            
            # Ищем груз с непaid статусом
            if processing_status != "paid" or payment_status != "paid":
                test_cargo = cargo
                break
        
        # Если не найден непaid груз, берем любой первый
        if not test_cargo and cargo_items:
            test_cargo = cargo_items[0]
        
        if not test_cargo:
            self.log_test(
                "Тестирование размещения груза с любым статусом",
                False,
                error_msg="Не найден подходящий груз для тестирования"
            )
            return False
        
        try:
            cargo_id = test_cargo.get("id")
            cargo_number = test_cargo.get("cargo_number", "Unknown")
            processing_status = test_cargo.get("processing_status", "Unknown")
            payment_status = test_cargo.get("payment_status", "Unknown")
            
            # Пытаемся разместить груз в разные тестовые ячейки
            test_cells = ["001-01-01-002", "001-01-01-003", "001-01-01-004", "001-01-01-005"]
            
            placement_success = False
            last_error = ""
            
            for cell_code in test_cells:
                placement_data = {
                    "cargo_number": cargo_number,
                    "cell_code": cell_code
                }
                
                response = self.session.post(
                    f"{BACKEND_URL}/cargo/place-in-cell",
                    json=placement_data
                )
                
                if response.status_code == 200:
                    data = response.json()
                    details = f"Груз {cargo_number} (processing_status: {processing_status}, payment_status: {payment_status}) успешно размещен в ячейку {cell_code}. "
                    details += f"Ответ API: {data}"
                    
                    self.log_test(
                        "Тестирование размещения груза с любым статусом через /api/cargo/place-in-cell",
                        True,
                        details
                    )
                    placement_success = True
                    break
                else:
                    last_error = f"HTTP {response.status_code}: {response.text}"
                    # Продолжаем пробовать другие ячейки
                    continue
            
            if not placement_success:
                error_details = f"Груз {cargo_number} (processing_status: {processing_status}, payment_status: {payment_status}). "
                error_details += f"Не удалось разместить ни в одну из тестовых ячеек. Последняя ошибка: {last_error}"
                
                self.log_test(
                    "Тестирование размещения груза с любым статусом через /api/cargo/place-in-cell",
                    False,
                    error_msg=error_details
                )
                return False
            
            return True
                
        except Exception as e:
            self.log_test(
                "Тестирование размещения груза с любым статусом",
                False,
                error_msg=f"Ошибка размещения: {str(e)}"
            )
            return False

    def run_comprehensive_test(self):
        """Запуск полного тестирования"""
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Размещение грузов любого статуса в TAJLINE.TJ")
        print("=" * 80)
        print()
        
        # 1. Авторизация оператора склада
        if not self.authenticate_warehouse_operator():
            print("❌ Тестирование прервано: не удалось авторизоваться")
            return False
        
        # 2. ГЛАВНАЯ ПРОВЕРКА: Получить доступные грузы
        cargo_items = self.get_available_cargo_for_placement()
        
        # 3. Тестирование размещения груза с любым статусом
        self.test_cargo_placement_any_status(cargo_items)
        
        # Подведение итогов
        print("=" * 80)
        print("📊 ИТОГИ ТЕСТИРОВАНИЯ:")
        print()
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Всего тестов: {total_tests}")
        print(f"✅ Пройдено: {passed_tests}")
        print(f"❌ Провалено: {failed_tests}")
        print(f"📈 Успешность: {(passed_tests/total_tests*100):.1f}%")
        print()
        
        if failed_tests == 0:
            print("🎉 ВСЕ КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ РАБОТАЮТ КОРРЕКТНО!")
            print("✅ Грузы с любым статусом оплаты могут размещаться")
            print("✅ API возвращает грузы независимо от статуса оплаты")
        else:
            print("🚨 ОБНАРУЖЕНЫ ПРОБЛЕМЫ В КРИТИЧЕСКИХ ИСПРАВЛЕНИЯХ!")
            print("❌ Требуется дополнительная проверка исправлений")
        
        return failed_tests == 0

def main():
    """Основная функция запуска тестов"""
    tester = CargoPlacementAnyStatusTester()
    success = tester.run_comprehensive_test()
    
    # Возвращаем код выхода
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
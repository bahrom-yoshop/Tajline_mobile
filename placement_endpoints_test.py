#!/usr/bin/env python3
"""
ДОПОЛНИТЕЛЬНОЕ ТЕСТИРОВАНИЕ ENDPOINTS РАЗМЕЩЕНИЯ ГРУЗА В TAJLINE.TJ

ЦЕЛЬ: Проверить все endpoints связанные с размещением груза, чтобы найти
источник неправильных данных в placementStatistics переменной frontend

ENDPOINTS ДЛЯ ПРОВЕРКИ:
1. /api/operator/placement-statistics - уже проверен, работает правильно
2. /api/operator/cargo/place - размещение груза оператором
3. /api/cargo/place-in-cell - размещение груза в ячейку
4. /api/operator/cargo/available-for-placement - список грузов для размещения

ПОДОЗРЕНИЕ: Один из endpoints размещения возвращает данные груза вместо статистики,
и frontend ошибочно записывает это в переменную placementStatistics
"""

import requests
import json
import sys
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://cargo-sync.preview.emergentagent.com/api"

# Учетные данные оператора склада
WAREHOUSE_OPERATOR = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class PlacementEndpointsTester:
    def __init__(self):
        self.session = requests.Session()
        self.operator_token = None
        self.test_results = []
        self.available_cargo = []
        self.operator_warehouses = []
        
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
        if details and not success:
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
    
    def get_operator_warehouses(self):
        """Получить склады оператора"""
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/warehouses", timeout=30)
            
            if response.status_code == 200:
                self.operator_warehouses = response.json()
                warehouse_count = len(self.operator_warehouses)
                self.log_result(
                    "Получение складов оператора",
                    True,
                    f"Найдено {warehouse_count} складов оператора"
                )
                return True
            else:
                self.log_result("Получение складов оператора", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Получение складов оператора", False, f"Исключение: {str(e)}")
            return False
    
    def get_available_cargo_for_placement(self):
        """Получить доступные грузы для размещения"""
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/available-for-placement", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                self.available_cargo = data.get("items", []) if isinstance(data, dict) else data
                cargo_count = len(self.available_cargo)
                self.log_result(
                    "Получение доступных грузов для размещения",
                    True,
                    f"Найдено {cargo_count} грузов для размещения"
                )
                return True
            else:
                self.log_result("Получение доступных грузов для размещения", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Получение доступных грузов для размещения", False, f"Исключение: {str(e)}")
            return False
    
    def test_operator_cargo_place_endpoint(self):
        """Тестирование endpoint /api/operator/cargo/place"""
        if not self.available_cargo or not self.operator_warehouses:
            self.log_result(
                "Тест /api/operator/cargo/place",
                False,
                "Нет доступных грузов или складов для тестирования"
            )
            return False
        
        # Берем первый доступный груз и склад
        test_cargo = self.available_cargo[0]
        test_warehouse = self.operator_warehouses[0]
        
        cargo_id = test_cargo.get("id")
        warehouse_id = test_warehouse.get("id")
        
        if not cargo_id or not warehouse_id:
            self.log_result(
                "Тест /api/operator/cargo/place",
                False,
                "Отсутствуют ID груза или склада"
            )
            return False
        
        # Данные для размещения груза
        placement_data = {
            "cargo_id": cargo_id,
            "warehouse_id": warehouse_id,
            "block_number": 1,
            "shelf_number": 1,
            "cell_number": 1
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/operator/cargo/place",
                json=placement_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # КРИТИЧЕСКАЯ ПРОВЕРКА: что возвращает этот endpoint
                # Проверяем наличие полей груза (которые могут попасть в placementStatistics)
                cargo_fields = ["location_code", "cargo_name", "cargo_number", "placed_at", "warehouse_name"]
                present_cargo_fields = [field for field in cargo_fields if field in data]
                
                # Проверяем наличие полей статистики
                stats_fields = ["today_placements", "session_placements", "recent_placements"]
                present_stats_fields = [field for field in stats_fields if field in data]
                
                if present_cargo_fields:
                    self.log_result(
                        "Тест /api/operator/cargo/place - ПОДОЗРИТЕЛЬНЫЙ ENDPOINT",
                        False,
                        f"🚨 НАЙДЕН ИСТОЧНИК ПРОБЛЕМЫ: Endpoint возвращает поля груза: {present_cargo_fields}",
                        {
                            "cargo_fields_found": present_cargo_fields,
                            "stats_fields_found": present_stats_fields,
                            "full_response": data,
                            "potential_bug_source": True,
                            "explanation": "Этот endpoint может перезаписывать placementStatistics в frontend"
                        }
                    )
                    return False
                else:
                    self.log_result(
                        "Тест /api/operator/cargo/place",
                        True,
                        f"Endpoint не возвращает поля груза, структура ответа корректна",
                        {
                            "response_fields": list(data.keys()),
                            "full_response": data
                        }
                    )
                    return True
            else:
                self.log_result(
                    "Тест /api/operator/cargo/place",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"placement_data": placement_data}
                )
                return False
                
        except Exception as e:
            self.log_result("Тест /api/operator/cargo/place", False, f"Исключение: {str(e)}")
            return False
    
    def test_cargo_place_in_cell_endpoint(self):
        """Тестирование endpoint /api/cargo/place-in-cell"""
        if not self.available_cargo:
            self.log_result(
                "Тест /api/cargo/place-in-cell",
                False,
                "Нет доступных грузов для тестирования"
            )
            return False
        
        # Берем первый доступный груз
        test_cargo = self.available_cargo[0]
        cargo_number = test_cargo.get("cargo_number")
        
        if not cargo_number:
            self.log_result(
                "Тест /api/cargo/place-in-cell",
                False,
                "Отсутствует номер груза"
            )
            return False
        
        # Данные для размещения груза в ячейку (используем ID-based формат)
        placement_data = {
            "cargo_number": cargo_number,
            "cell_code": "001-01-01-001"  # ID-based формат
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/cargo/place-in-cell",
                json=placement_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # КРИТИЧЕСКАЯ ПРОВЕРКА: что возвращает этот endpoint
                cargo_fields = ["location_code", "cargo_name", "cargo_number", "placed_at", "warehouse_name"]
                present_cargo_fields = [field for field in cargo_fields if field in data]
                
                stats_fields = ["today_placements", "session_placements", "recent_placements"]
                present_stats_fields = [field for field in stats_fields if field in data]
                
                if present_cargo_fields:
                    self.log_result(
                        "Тест /api/cargo/place-in-cell - ПОДОЗРИТЕЛЬНЫЙ ENDPOINT",
                        False,
                        f"🚨 НАЙДЕН ИСТОЧНИК ПРОБЛЕМЫ: Endpoint возвращает поля груза: {present_cargo_fields}",
                        {
                            "cargo_fields_found": present_cargo_fields,
                            "stats_fields_found": present_stats_fields,
                            "full_response": data,
                            "potential_bug_source": True,
                            "explanation": "Этот endpoint может перезаписывать placementStatistics в frontend"
                        }
                    )
                    return False
                else:
                    self.log_result(
                        "Тест /api/cargo/place-in-cell",
                        True,
                        f"Endpoint не возвращает поля груза, структура ответа корректна",
                        {
                            "response_fields": list(data.keys()),
                            "full_response": data
                        }
                    )
                    return True
            else:
                # Может быть ошибка из-за занятой ячейки или другой причины
                self.log_result(
                    "Тест /api/cargo/place-in-cell",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"placement_data": placement_data, "note": "Возможно ячейка занята или груз уже размещен"}
                )
                return False
                
        except Exception as e:
            self.log_result("Тест /api/cargo/place-in-cell", False, f"Исключение: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Запуск всех тестов для поиска источника проблемы placementStatistics"""
        print("🔍 ДОПОЛНИТЕЛЬНОЕ ТЕСТИРОВАНИЕ ENDPOINTS РАЗМЕЩЕНИЯ ГРУЗА В TAJLINE.TJ")
        print("=" * 80)
        print("🎯 ЦЕЛЬ: Найти endpoint который возвращает данные груза вместо статистики")
        print("🚨 ПРОБЛЕМА: placementStatistics содержит {location_code, cargo_name, ...}")
        print("=" * 80)
        
        # Шаг 1: Авторизация
        if not self.authenticate_warehouse_operator():
            print("❌ Невозможно продолжить без авторизации")
            return False
        
        # Шаг 2: Получить склады оператора
        if not self.get_operator_warehouses():
            print("❌ Невозможно получить склады оператора")
            return False
        
        # Шаг 3: Получить доступные грузы
        if not self.get_available_cargo_for_placement():
            print("❌ Невозможно получить доступные грузы")
            return False
        
        # Шаг 4: Тестировать endpoints размещения
        print(f"\n🧪 ТЕСТИРОВАНИЕ ENDPOINTS РАЗМЕЩЕНИЯ...")
        
        # Тест 1: /api/operator/cargo/place
        print(f"\n1️⃣ Тестирование /api/operator/cargo/place...")
        self.test_operator_cargo_place_endpoint()
        
        # Тест 2: /api/cargo/place-in-cell
        print(f"\n2️⃣ Тестирование /api/cargo/place-in-cell...")
        self.test_cargo_place_in_cell_endpoint()
        
        # Итоговый отчет
        print("\n" + "=" * 80)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ПОИСКА ИСТОЧНИКА ПРОБЛЕМЫ")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Всего тестов: {total_tests}")
        print(f"Пройдено: {passed_tests}")
        print(f"Провалено: {failed_tests}")
        print(f"Процент успеха: {success_rate:.1f}%")
        
        # Поиск подозрительных endpoints
        suspicious_endpoints = [
            result for result in self.test_results 
            if not result["success"] and result.get("details", {}).get("potential_bug_source")
        ]
        
        print(f"\n🔍 РЕЗУЛЬТАТЫ ПОИСКА ИСТОЧНИКА ПРОБЛЕМЫ:")
        
        if suspicious_endpoints:
            print(f"   🚨 НАЙДЕНЫ ПОДОЗРИТЕЛЬНЫЕ ENDPOINTS: {len(suspicious_endpoints)}")
            for result in suspicious_endpoints:
                print(f"   ❌ {result['test']}: {result['message']}")
                details = result.get("details", {})
                if "cargo_fields_found" in details:
                    print(f"      Поля груза: {details['cargo_fields_found']}")
            
            print(f"\n💡 РЕКОМЕНДАЦИИ:")
            print("   1. Проверить frontend код где вызываются найденные endpoints")
            print("   2. Убедиться что результат не записывается в placementStatistics")
            print("   3. Разделить переменные для статистики и результата размещения")
        else:
            print("   ✅ Подозрительные endpoints НЕ НАЙДЕНЫ")
            print("   🤔 Проблема может быть в frontend логике")
            print(f"\n💡 РЕКОМЕНДАЦИИ:")
            print("   1. Проверить frontend код где используется placementStatistics")
            print("   2. Найти место где переменная перезаписывается")
            print("   3. Проверить обработчики событий размещения груза")
        
        return success_rate >= 50.0  # Более мягкий критерий, так как ошибки размещения ожидаемы

if __name__ == "__main__":
    tester = PlacementEndpointsTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
        sys.exit(0)
    else:
        print("\n🔍 ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНАЯ ДИАГНОСТИКА!")
        sys.exit(1)
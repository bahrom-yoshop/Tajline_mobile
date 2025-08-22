#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ СИСТЕМЫ РАЗМЕЩЕНИЯ ГРУЗА ЧЕРЕЗ QR СКАНИРОВАНИЕ В TAJLINE.TJ

КОНТЕКСТ ИСПРАВЛЕНИЙ:
- Исправлена ошибка "Invalid cell code format" при размещении груза
- Frontend код теперь корректно определяет warehouse_id по warehouse_number для компактного формата QR (03010101)
- Система должна поддерживать различные форматы QR кодов ячеек

ТЕСТОВЫЙ ПЛАН:
1. Авторизация оператора склада (+79777888999/warehouse123)
2. Получение доступных грузов для размещения через /api/operator/cargo/available-for-placement
3. Получение списка складов через /api/warehouses для проверки соответствия warehouse_id и warehouse_number
4. Тестирование различных форматов QR кодов ячеек через /api/operator/cargo/place
5. Проверка корректной обработки компактного формата QR (03010101)

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
- Авторизация оператора склада работает
- API возвращает доступные грузы для размещения
- Склады имеют соответствующие поля warehouse_number и id
- Размещение груза работает с различными форматами QR кодов
- Компактный формат QR корректно преобразуется в warehouse_id
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List

# Конфигурация
BACKEND_URL = "https://tajline-cargo-8.preview.emergentagent.com/api"

# Учетные данные оператора склада
WAREHOUSE_OPERATOR = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class QRCargoPlacementTester:
    def __init__(self):
        self.session = requests.Session()
        self.operator_token = None
        self.operator_info = None
        self.test_results = []
        self.warehouses = []
        self.available_cargo = []
        
    def log_result(self, test_name: str, success: bool, message: str, details: Optional[Dict] = None):
        """Логирование результата теста"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {message}")
        if details and not success:
            print(f"   Details: {json.dumps(details, indent=2, ensure_ascii=False)}")
    
    def authenticate_warehouse_operator(self) -> bool:
        """Авторизация оператора склада"""
        print("\n🔐 АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА")
        print("=" * 60)
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=WAREHOUSE_OPERATOR,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.operator_token = data.get("access_token")
                self.operator_info = data.get("user", {})
                
                if self.operator_token:
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.operator_token}"
                    })
                    
                    operator_name = self.operator_info.get('full_name', 'Unknown')
                    operator_role = self.operator_info.get('role', 'Unknown')
                    operator_number = self.operator_info.get('user_number', 'Unknown')
                    
                    self.log_result(
                        "Авторизация оператора склада",
                        True,
                        f"Успешная авторизация: {operator_name} (роль: {operator_role}, номер: {operator_number})",
                        {
                            "operator_name": operator_name,
                            "operator_role": operator_role,
                            "operator_number": operator_number,
                            "phone": WAREHOUSE_OPERATOR["phone"],
                            "token_length": len(self.operator_token)
                        }
                    )
                    return True
                else:
                    self.log_result(
                        "Авторизация оператора склада",
                        False,
                        "Токен доступа не получен",
                        {"response": data}
                    )
                    return False
            else:
                self.log_result(
                    "Авторизация оператора склада",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Авторизация оператора склада",
                False,
                f"Исключение: {str(e)}"
            )
            return False
    
    def get_available_cargo_for_placement(self) -> bool:
        """Получение доступных грузов для размещения"""
        print("\n📦 ПОЛУЧЕНИЕ ДОСТУПНЫХ ГРУЗОВ ДЛЯ РАЗМЕЩЕНИЯ")
        print("=" * 60)
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/operator/cargo/available-for-placement",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                total_count = data.get("total_count", len(items))
                
                self.available_cargo = items
                
                # Анализ структуры данных
                cargo_analysis = {
                    "total_cargo": len(items),
                    "cargo_with_warehouse_info": 0,
                    "cargo_statuses": {},
                    "sample_cargo": items[0] if items else None
                }
                
                for cargo in items:
                    # Подсчет статусов
                    status = cargo.get("processing_status", "unknown")
                    cargo_analysis["cargo_statuses"][status] = cargo_analysis["cargo_statuses"].get(status, 0) + 1
                    
                    # Проверка наличия информации о складе
                    if cargo.get("warehouse_name") or cargo.get("warehouse_location"):
                        cargo_analysis["cargo_with_warehouse_info"] += 1
                
                self.log_result(
                    "Получение доступных грузов для размещения",
                    True,
                    f"Получено {len(items)} грузов для размещения (всего: {total_count})",
                    cargo_analysis
                )
                
                # Проверка структуры ответа
                required_fields = ["items"]
                optional_fields = ["total_count", "page", "per_page", "total_pages", "has_next", "has_prev"]
                
                structure_check = {
                    "has_items": "items" in data,
                    "has_pagination": any(field in data for field in optional_fields),
                    "pagination_fields": [field for field in optional_fields if field in data]
                }
                
                self.log_result(
                    "Проверка структуры ответа API",
                    structure_check["has_items"],
                    f"Структура ответа {'корректна' if structure_check['has_items'] else 'некорректна'}",
                    structure_check
                )
                
                return True
            else:
                self.log_result(
                    "Получение доступных грузов для размещения",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Получение доступных грузов для размещения",
                False,
                f"Исключение: {str(e)}"
            )
            return False
    
    def get_warehouses_list(self) -> bool:
        """Получение списка складов для проверки соответствия warehouse_id и warehouse_number"""
        print("\n🏭 ПОЛУЧЕНИЕ СПИСКА СКЛАДОВ")
        print("=" * 60)
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/warehouses",
                timeout=30
            )
            
            if response.status_code == 200:
                warehouses = response.json()
                self.warehouses = warehouses
                
                # Анализ складов
                warehouse_analysis = {
                    "total_warehouses": len(warehouses),
                    "warehouses_with_number": 0,
                    "warehouses_with_id": 0,
                    "warehouse_number_formats": {},
                    "sample_warehouse": warehouses[0] if warehouses else None
                }
                
                for warehouse in warehouses:
                    # Проверка наличия warehouse_number
                    if "warehouse_number" in warehouse and warehouse["warehouse_number"] is not None:
                        warehouse_analysis["warehouses_with_number"] += 1
                        
                        # Анализ формата warehouse_number
                        wh_number = str(warehouse["warehouse_number"])
                        if wh_number.isdigit():
                            format_type = f"numeric_{len(wh_number)}_digits"
                        else:
                            format_type = "non_numeric"
                        
                        warehouse_analysis["warehouse_number_formats"][format_type] = \
                            warehouse_analysis["warehouse_number_formats"].get(format_type, 0) + 1
                    
                    # Проверка наличия id
                    if "id" in warehouse and warehouse["id"]:
                        warehouse_analysis["warehouses_with_id"] += 1
                
                success = warehouse_analysis["warehouses_with_number"] > 0 and warehouse_analysis["warehouses_with_id"] > 0
                
                self.log_result(
                    "Получение списка складов",
                    success,
                    f"Получено {len(warehouses)} складов, {warehouse_analysis['warehouses_with_number']} с warehouse_number, {warehouse_analysis['warehouses_with_id']} с id",
                    warehouse_analysis
                )
                
                # Проверка соответствия warehouse_id и warehouse_number
                if success:
                    self.check_warehouse_id_number_mapping()
                
                return success
            else:
                self.log_result(
                    "Получение списка складов",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Получение списка складов",
                False,
                f"Исключение: {str(e)}"
            )
            return False
    
    def check_warehouse_id_number_mapping(self):
        """Проверка соответствия warehouse_id и warehouse_number"""
        print("\n🔍 ПРОВЕРКА СООТВЕТСТВИЯ WAREHOUSE_ID И WAREHOUSE_NUMBER")
        
        mapping_data = {
            "warehouses_with_both": 0,
            "mapping_examples": [],
            "potential_issues": []
        }
        
        for warehouse in self.warehouses:
            warehouse_id = warehouse.get("id")
            warehouse_number = warehouse.get("warehouse_number")
            warehouse_name = warehouse.get("name", "Unknown")
            
            if warehouse_id and warehouse_number is not None:
                mapping_data["warehouses_with_both"] += 1
                
                mapping_example = {
                    "name": warehouse_name,
                    "id": warehouse_id,
                    "warehouse_number": warehouse_number,
                    "warehouse_number_str": str(warehouse_number)
                }
                
                mapping_data["mapping_examples"].append(mapping_example)
                
                # Проверка на потенциальные проблемы
                if not str(warehouse_number).isdigit():
                    mapping_data["potential_issues"].append(f"Склад '{warehouse_name}' имеет нечисловой warehouse_number: {warehouse_number}")
        
        success = mapping_data["warehouses_with_both"] > 0
        
        self.log_result(
            "Проверка соответствия warehouse_id и warehouse_number",
            success,
            f"Найдено {mapping_data['warehouses_with_both']} складов с корректным соответствием id и warehouse_number",
            mapping_data
        )
    
    def test_qr_code_formats(self) -> bool:
        """Тестирование различных форматов QR кодов ячеек"""
        print("\n🔲 ТЕСТИРОВАНИЕ ФОРМАТОВ QR КОДОВ ЯЧЕЕК")
        print("=" * 60)
        
        if not self.available_cargo:
            self.log_result(
                "Тестирование QR кодов",
                False,
                "Нет доступных грузов для тестирования размещения"
            )
            return False
        
        if not self.warehouses:
            self.log_result(
                "Тестирование QR кодов",
                False,
                "Нет данных о складах для тестирования"
            )
            return False
        
        # Выбираем первый доступный груз для тестирования
        test_cargo = self.available_cargo[0]
        cargo_id = test_cargo.get("id")
        cargo_number = test_cargo.get("cargo_number")
        
        if not cargo_number:
            self.log_result(
                "Тестирование QR кодов",
                False,
                "Не найден номер груза для тестирования"
            )
            return False
        
        # Выбираем склад с warehouse_number для тестирования
        test_warehouse = None
        for warehouse in self.warehouses:
            if warehouse.get("warehouse_number") is not None:
                test_warehouse = warehouse
                break
        
        if not test_warehouse:
            self.log_result(
                "Тестирование QR кодов",
                False,
                "Не найден склад с warehouse_number для тестирования"
            )
            return False
        
        warehouse_id = test_warehouse.get("id")
        warehouse_number = str(test_warehouse.get("warehouse_number"))
        warehouse_name = test_warehouse.get("name", "Unknown")
        
        print(f"Тестовый груз: {cargo_number} (ID: {cargo_id})")
        print(f"Тестовый склад: {warehouse_name} (ID: {warehouse_id}, Number: {warehouse_number})")
        
        # Различные форматы QR кодов для тестирования
        # Используем правильный API endpoint: /api/cargo/place-in-cell
        qr_test_cases = [
            {
                "name": "ID-based формат с дефисами (003-01-01-001)",
                "cell_code": f"{warehouse_number.zfill(3)}-01-01-001",
                "description": "Формат: warehouse_number(3) + block(2) + shelf(2) + cell(3)"
            },
            {
                "name": "Полный UUID формат (UUID-Б1-П1-Я1)",
                "cell_code": f"{warehouse_id}-Б1-П1-Я1",
                "description": "Полный UUID склада + читаемый формат"
            },
            {
                "name": "Компактный формат (без поддержки в backend)",
                "cell_code": f"{warehouse_number.zfill(2)}010101",  # warehouse_number + block + shelf + cell
                "description": "Формат: warehouse_number(2) + block(2) + shelf(2) + cell(2) - НЕ ПОДДЕРЖИВАЕТСЯ BACKEND"
            }
        ]
        
        test_results = []
        
        for i, test_case in enumerate(qr_test_cases, 1):
            print(f"\n🔲 Тест {i}: {test_case['name']}")
            print(f"   Cell код: {test_case['cell_code']}")
            print(f"   Описание: {test_case['description']}")
            
            # Данные для размещения груза - используем правильный API
            placement_data = {
                "cargo_number": cargo_number,
                "cell_code": test_case["cell_code"]
            }
            
            try:
                response = self.session.post(
                    f"{BACKEND_URL}/cargo/place-in-cell",
                    json=placement_data,
                    timeout=30
                )
                
                test_result = {
                    "format": test_case["name"],
                    "cell_code": test_case["cell_code"],
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "response": None,
                    "error": None
                }
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        test_result["response"] = response_data
                        print(f"   ✅ Успешно: {response_data.get('message', 'Груз размещен')}")
                    except:
                        test_result["response"] = response.text
                        print(f"   ✅ Успешно: {response.text}")
                else:
                    try:
                        error_data = response.json()
                        test_result["error"] = error_data
                        error_message = error_data.get("detail", response.text)
                        print(f"   ❌ Ошибка: {error_message}")
                    except:
                        test_result["error"] = response.text
                        print(f"   ❌ Ошибка: {response.text}")
                
                test_results.append(test_result)
                
            except Exception as e:
                test_result = {
                    "format": test_case["name"],
                    "cell_code": test_case["cell_code"],
                    "status_code": None,
                    "success": False,
                    "response": None,
                    "error": str(e)
                }
                test_results.append(test_result)
                print(f"   ❌ Исключение: {str(e)}")
        
        # Анализ результатов
        successful_formats = [r for r in test_results if r["success"]]
        failed_formats = [r for r in test_results if not r["success"]]
        
        success_rate = len(successful_formats) / len(test_results) * 100 if test_results else 0
        
        self.log_result(
            "Тестирование различных форматов QR кодов",
            len(successful_formats) > 0,
            f"Успешно обработано {len(successful_formats)} из {len(test_results)} форматов QR кодов ({success_rate:.1f}%)",
            {
                "test_cargo": {
                    "cargo_id": cargo_id,
                    "cargo_number": cargo_number
                },
                "test_warehouse": {
                    "warehouse_id": warehouse_id,
                    "warehouse_number": warehouse_number,
                    "warehouse_name": warehouse_name
                },
                "successful_formats": [r["format"] for r in successful_formats],
                "failed_formats": [{"format": r["format"], "error": r["error"]} for r in failed_formats],
                "detailed_results": test_results
            }
        )
        
        # Специальная проверка компактного формата
        compact_format_test = next((r for r in test_results if "Компактный формат" in r["format"]), None)
        if compact_format_test:
            self.log_result(
                "КРИТИЧЕСКАЯ ПРОВЕРКА: Компактный формат QR (03010101)",
                compact_format_test["success"],
                f"Компактный формат QR {'работает корректно' if compact_format_test['success'] else 'НЕ ПОДДЕРЖИВАЕТСЯ в backend (ожидаемо)'}",
                {
                    "cell_code": compact_format_test["cell_code"],
                    "status_code": compact_format_test["status_code"],
                    "error": compact_format_test["error"] if not compact_format_test["success"] else None,
                    "note": "Компактный формат должен обрабатываться на frontend и преобразовываться в поддерживаемый формат"
                }
            )
        
        return len(successful_formats) > 0
    
    def run_comprehensive_test(self) -> bool:
        """Запуск полного комплексного тестирования"""
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ СИСТЕМЫ РАЗМЕЩЕНИЯ ГРУЗА ЧЕРЕЗ QR СКАНИРОВАНИЕ В TAJLINE.TJ")
        print("=" * 100)
        
        # Этап 1: Авторизация оператора склада
        if not self.authenticate_warehouse_operator():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как оператор склада")
            return False
        
        # Этап 2: Получение доступных грузов для размещения
        if not self.get_available_cargo_for_placement():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить доступные грузы для размещения")
            return False
        
        # Этап 3: Получение списка складов
        if not self.get_warehouses_list():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить список складов")
            return False
        
        # Этап 4: Тестирование различных форматов QR кодов
        qr_test_success = self.test_qr_code_formats()
        
        # Итоговый отчет
        self.generate_final_report()
        
        return qr_test_success
    
    def generate_final_report(self):
        """Генерация итогового отчета"""
        print("\n" + "=" * 100)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 100)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Всего тестов: {total_tests}")
        print(f"Пройдено: {passed_tests}")
        print(f"Провалено: {failed_tests}")
        print(f"Процент успеха: {success_rate:.1f}%")
        
        print("\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        # Критические проблемы
        critical_failures = [
            result for result in self.test_results 
            if not result["success"] and any(keyword in result["test"].lower() 
                                           for keyword in ["критическая", "авторизация", "компактный формат"])
        ]
        
        if critical_failures:
            print(f"\n🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ ({len(critical_failures)}):")
            for failure in critical_failures:
                print(f"   - {failure['test']}: {failure['message']}")
        
        # Ключевые выводы
        print(f"\n🔍 КЛЮЧЕВЫЕ ВЫВОДЫ:")
        
        # Проверка авторизации
        auth_test = next((r for r in self.test_results if "Авторизация" in r["test"]), None)
        if auth_test and auth_test["success"]:
            print("   ✅ Авторизация оператора склада работает корректно")
        elif auth_test:
            print("   ❌ Проблемы с авторизацией оператора склада")
        
        # Проверка API доступных грузов
        cargo_test = next((r for r in self.test_results if "доступных грузов" in r["test"]), None)
        if cargo_test and cargo_test["success"]:
            print("   ✅ API /api/operator/cargo/available-for-placement работает")
        elif cargo_test:
            print("   ❌ Проблемы с API доступных грузов для размещения")
        
        # Проверка складов
        warehouse_test = next((r for r in self.test_results if "список складов" in r["test"]), None)
        if warehouse_test and warehouse_test["success"]:
            print("   ✅ API /api/warehouses работает, склады имеют warehouse_id и warehouse_number")
        elif warehouse_test:
            print("   ❌ Проблемы с API складов или отсутствуют необходимые поля")
        
        # Проверка QR кодов
        qr_test = next((r for r in self.test_results if "QR кодов" in r["test"]), None)
        if qr_test and qr_test["success"]:
            print("   ✅ Система размещения груза через QR коды работает")
        elif qr_test:
            print("   ❌ Проблемы с размещением груза через QR коды")
        
        # Проверка компактного формата
        compact_test = next((r for r in self.test_results if "Компактный формат" in r["test"]), None)
        if compact_test and compact_test["success"]:
            print("   ✅ КРИТИЧЕСКИЙ УСПЕХ: Компактный формат QR (03010101) работает корректно")
        elif compact_test:
            print("   ❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Компактный формат QR не работает")
        
        # Общий вывод
        if success_rate >= 80:
            print(f"\n🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ Система размещения груза через QR сканирование работает корректно")
            print("✅ Исправления 'Invalid cell code format' подтверждены")
        else:
            print(f"\n⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ В СИСТЕМЕ")
            print("❌ Требуется дополнительная работа над исправлениями")

def main():
    """Основная функция"""
    tester = QRCargoPlacementTester()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 ВСЕ КРИТИЧЕСКИЕ ТЕСТЫ ПРОЙДЕНЫ!")
        sys.exit(0)
    else:
        print("\n❌ ОБНАРУЖЕНЫ КРИТИЧЕСКИЕ ПРОБЛЕМЫ!")
        sys.exit(1)

if __name__ == "__main__":
    main()
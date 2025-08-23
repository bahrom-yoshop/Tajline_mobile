#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: ЭТАП 2 - API endpoints для размещения грузов на транспорт
===================================================================================

ЦЕЛЬ ТЕСТИРОВАНИЯ: Проверить все новые API endpoints этапа 2 системы "Размещение грузов на транспорт" - 
сканирование транспорта, сканирование грузов, управление сессиями загрузки.

КРИТИЧЕСКИЕ ENDPOINTS ДЛЯ ТЕСТИРОВАНИЯ:
1. POST /api/logistics/cargo-to-transport/scan-transport - Сканирование QR кода транспорта и создание сессии
2. POST /api/logistics/cargo-to-transport/scan-cargo - Сканирование QR кода груза для размещения на транспорт  
3. GET /api/logistics/cargo-to-transport/session - Получение текущей активной сессии размещения
4. DELETE /api/logistics/cargo-to-transport/session - Завершение сессии размещения

ДЕТАЛЬНЫЕ ТРЕБОВАНИЯ:
1. Авторизация: Использовать warehouse_operator (+79777888999/warehouse123)
2. Сканирование транспорта: 
   - Принимать QR коды в формате TRANSPORT_{transport_number}_{timestamp}
   - Создавать сессию размещения в коллекции transport_loading_sessions
   - Обновлять статус транспорта на "loading"
   - Возвращать session_id и данные транспорта
3. Сканирование грузов:
   - Принимать различные форматы QR грузов (TAJLINE|INDIVIDUAL|..., простые номера)
   - Проверять что груз размещен на складе (placement_records)
   - Добавлять груз в сессию (loaded_cargo массив)
   - Обновлять статус груза на "loaded_on_transport"
4. Управление сессиями:
   - Получение активной сессии по operator_id или session_id
   - Завершение сессии с обновлением статуса транспорта
   - Корректная обработка количества загруженных грузов

ТЕСТОВЫЕ СЦЕНАРИИ:
Сценарий 1: Полный workflow размещения
Сценарий 2: Обработка ошибок
Сценарий 3: Управление сессиями

ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ:
- ✅ Все endpoints доступны и работают корректно
- ✅ Сессии создаются и управляются правильно
- ✅ Статусы транспортов и грузов обновляются корректно
- ✅ База данных transport_loading_sessions функционирует
- ✅ Обработка ошибок работает (404, 400 коды)
- ✅ Возвращаются правильные данные о сессиях и грузах
"""

import requests
import json
import sys
import os
from datetime import datetime
import time
import uuid

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cargo-sync.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Конфигурация тестирования
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"

# Тестовые данные
TEST_TRANSPORT_NUMBER = "001АА01"
TEST_CARGO_NUMBERS = ["250101", "TAJLINE|INDIVIDUAL|250101/01/01|1234567890"]
INVALID_TRANSPORT_QR = "INVALID_QR_CODE"
INVALID_CARGO_QR = "NONEXISTENT_CARGO"

class CargoToTransportStage2Tester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.current_session_id = None
        self.test_results = {
            "auth_success": False,
            "scan_transport_success": False,
            "scan_cargo_success": False,
            "get_session_success": False,
            "delete_session_success": False,
            "error_handling_success": False,
            "session_management_success": False,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "detailed_results": []
        }
        
    def log(self, message, level="INFO"):
        """Логирование с временной меткой"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def add_test_result(self, test_name, success, details="", response_time=None):
        """Добавить результат теста"""
        self.test_results["total_tests"] += 1
        if success:
            self.test_results["passed_tests"] += 1
            status = "✅ ПРОЙДЕН"
        else:
            self.test_results["failed_tests"] += 1
            status = "❌ ПРОВАЛЕН"
            
        result = {
            "test_name": test_name,
            "status": status,
            "success": success,
            "details": details,
            "response_time": f"{response_time}ms" if response_time else "N/A"
        }
        self.test_results["detailed_results"].append(result)
        
        self.log(f"{status}: {test_name} ({result['response_time']}) - {details}")
        
    def authenticate_warehouse_operator(self):
        """Авторизация оператора склада"""
        self.log("🔐 Авторизация оператора склада...")
        
        try:
            start_time = time.time()
            response = self.session.post(f"{API_BASE}/auth/login", json={
                "phone": WAREHOUSE_OPERATOR_PHONE,
                "password": WAREHOUSE_OPERATOR_PASSWORD
            })
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.operator_info = data.get("user")
                
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                details = f"Успешная авторизация '{self.operator_info.get('full_name')}' (роль: {self.operator_info.get('role')})"
                self.add_test_result("Авторизация оператора склада", True, details, response_time)
                self.test_results["auth_success"] = True
                return True
            else:
                details = f"Ошибка авторизации: {response.status_code} - {response.text}"
                self.add_test_result("Авторизация оператора склада", False, details, response_time)
                return False
                
        except Exception as e:
            details = f"Исключение при авторизации: {e}"
            self.add_test_result("Авторизация оператора склада", False, details)
            return False
    
    def test_scan_transport_endpoint(self):
        """Тестирование POST /api/logistics/cargo-to-transport/scan-transport"""
        self.log("\n🚛 Тестирование сканирования транспорта...")
        
        # Генерируем QR код транспорта в правильном формате
        timestamp = int(time.time())
        transport_qr = f"TRANSPORT_{TEST_TRANSPORT_NUMBER}_{timestamp}"
        
        try:
            start_time = time.time()
            response = self.session.post(f"{API_BASE}/logistics/cargo-to-transport/scan-transport", json={
                "qr_code": transport_qr
            })
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем обязательные поля в ответе
                required_fields = ["session_id", "transport_id", "transport_number", "status"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.current_session_id = data.get("session_id")
                    details = f"Сессия создана: {self.current_session_id}, транспорт: {data.get('transport_number')}, статус: {data.get('status')}"
                    self.add_test_result("Сканирование транспорта (создание сессии)", True, details, response_time)
                    self.test_results["scan_transport_success"] = True
                    return True
                else:
                    details = f"Отсутствуют обязательные поля: {missing_fields}"
                    self.add_test_result("Сканирование транспорта (создание сессии)", False, details, response_time)
                    return False
            else:
                details = f"Ошибка HTTP {response.status_code}: {response.text}"
                self.add_test_result("Сканирование транспорта (создание сессии)", False, details, response_time)
                return False
                
        except Exception as e:
            details = f"Исключение: {e}"
            self.add_test_result("Сканирование транспорта (создание сессии)", False, details)
            return False
    
    def test_scan_cargo_endpoint(self):
        """Тестирование POST /api/logistics/cargo-to-transport/scan-cargo"""
        self.log("\n📦 Тестирование сканирования грузов...")
        
        if not self.current_session_id:
            self.add_test_result("Сканирование груза", False, "Нет активной сессии для тестирования")
            return False
        
        success_count = 0
        total_cargo_tests = len(TEST_CARGO_NUMBERS)
        
        for i, cargo_qr in enumerate(TEST_CARGO_NUMBERS):
            self.log(f"📋 Тестирование груза {i+1}/{total_cargo_tests}: {cargo_qr}")
            
            try:
                start_time = time.time()
                response = self.session.post(f"{API_BASE}/logistics/cargo-to-transport/scan-cargo", json={
                    "qr_code": cargo_qr,
                    "session_id": self.current_session_id
                })
                response_time = int((time.time() - start_time) * 1000)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Проверяем обязательные поля
                    required_fields = ["success", "cargo_info", "session_info"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields and data.get("success"):
                        cargo_info = data.get("cargo_info", {})
                        session_info = data.get("session_info", {})
                        
                        details = f"Груз добавлен: {cargo_info.get('cargo_number', 'N/A')}, статус: {cargo_info.get('status', 'N/A')}, загружено в сессию: {session_info.get('loaded_cargo_count', 0)}"
                        self.add_test_result(f"Сканирование груза #{i+1}", True, details, response_time)
                        success_count += 1
                    else:
                        details = f"Неуспешный ответ или отсутствуют поля: {missing_fields}"
                        self.add_test_result(f"Сканирование груза #{i+1}", False, details, response_time)
                else:
                    details = f"Ошибка HTTP {response.status_code}: {response.text}"
                    self.add_test_result(f"Сканирование груза #{i+1}", False, details, response_time)
                    
            except Exception as e:
                details = f"Исключение: {e}"
                self.add_test_result(f"Сканирование груза #{i+1}", False, details)
        
        # Общий результат сканирования грузов
        if success_count > 0:
            self.test_results["scan_cargo_success"] = True
            return True
        else:
            return False
    
    def test_get_session_endpoint(self):
        """Тестирование GET /api/logistics/cargo-to-transport/session"""
        self.log("\n📋 Тестирование получения активной сессии...")
        
        try:
            start_time = time.time()
            response = self.session.get(f"{API_BASE}/logistics/cargo-to-transport/session")
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем структуру ответа
                required_fields = ["session_id", "transport_info", "loaded_cargo", "session_status"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    transport_info = data.get("transport_info", {})
                    loaded_cargo = data.get("loaded_cargo", [])
                    
                    details = f"Активная сессия: {data.get('session_id')}, транспорт: {transport_info.get('transport_number', 'N/A')}, загружено грузов: {len(loaded_cargo)}, статус: {data.get('session_status')}"
                    self.add_test_result("Получение активной сессии", True, details, response_time)
                    self.test_results["get_session_success"] = True
                    return True
                else:
                    details = f"Отсутствуют обязательные поля: {missing_fields}"
                    self.add_test_result("Получение активной сессии", False, details, response_time)
                    return False
            else:
                details = f"Ошибка HTTP {response.status_code}: {response.text}"
                self.add_test_result("Получение активной сессии", False, details, response_time)
                return False
                
        except Exception as e:
            details = f"Исключение: {e}"
            self.add_test_result("Получение активной сессии", False, details)
            return False
    
    def test_delete_session_endpoint(self):
        """Тестирование DELETE /api/logistics/cargo-to-transport/session"""
        self.log("\n🔚 Тестирование завершения сессии...")
        
        if not self.current_session_id:
            self.add_test_result("Завершение сессии", False, "Нет активной сессии для завершения")
            return False
        
        try:
            start_time = time.time()
            response = self.session.delete(f"{API_BASE}/logistics/cargo-to-transport/session", json={
                "session_id": self.current_session_id
            })
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем результат завершения
                if data.get("success"):
                    session_summary = data.get("session_summary", {})
                    details = f"Сессия завершена: {self.current_session_id}, загружено грузов: {session_summary.get('total_loaded_cargo', 0)}, статус транспорта: {session_summary.get('transport_status', 'N/A')}"
                    self.add_test_result("Завершение сессии", True, details, response_time)
                    self.test_results["delete_session_success"] = True
                    self.current_session_id = None  # Сбрасываем ID сессии
                    return True
                else:
                    details = f"Неуспешное завершение сессии: {data.get('message', 'Неизвестная ошибка')}"
                    self.add_test_result("Завершение сессии", False, details, response_time)
                    return False
            else:
                details = f"Ошибка HTTP {response.status_code}: {response.text}"
                self.add_test_result("Завершение сессии", False, details, response_time)
                return False
                
        except Exception as e:
            details = f"Исключение: {e}"
            self.add_test_result("Завершение сессии", False, details)
            return False
    
    def test_error_handling(self):
        """Тестирование обработки ошибок"""
        self.log("\n⚠️ Тестирование обработки ошибок...")
        
        error_tests = [
            {
                "name": "Сканирование недопустимого QR транспорта",
                "endpoint": f"{API_BASE}/logistics/cargo-to-transport/scan-transport",
                "method": "POST",
                "data": {"qr_code": INVALID_TRANSPORT_QR},
                "expected_status": [400, 404]
            },
            {
                "name": "Сканирование груза без активной сессии",
                "endpoint": f"{API_BASE}/logistics/cargo-to-transport/scan-cargo",
                "method": "POST", 
                "data": {"qr_code": "250101", "session_id": "nonexistent_session"},
                "expected_status": [400, 404]
            },
            {
                "name": "Сканирование несуществующего груза",
                "endpoint": f"{API_BASE}/logistics/cargo-to-transport/scan-cargo",
                "method": "POST",
                "data": {"qr_code": INVALID_CARGO_QR, "session_id": str(uuid.uuid4())},
                "expected_status": [400, 404]
            }
        ]
        
        error_success_count = 0
        
        for test in error_tests:
            try:
                start_time = time.time()
                
                if test["method"] == "POST":
                    response = self.session.post(test["endpoint"], json=test["data"])
                elif test["method"] == "GET":
                    response = self.session.get(test["endpoint"])
                elif test["method"] == "DELETE":
                    response = self.session.delete(test["endpoint"], json=test["data"])
                    
                response_time = int((time.time() - start_time) * 1000)
                
                if response.status_code in test["expected_status"]:
                    details = f"Корректная обработка ошибки: HTTP {response.status_code}"
                    self.add_test_result(test["name"], True, details, response_time)
                    error_success_count += 1
                else:
                    details = f"Неожиданный статус: HTTP {response.status_code} (ожидался {test['expected_status']})"
                    self.add_test_result(test["name"], False, details, response_time)
                    
            except Exception as e:
                details = f"Исключение: {e}"
                self.add_test_result(test["name"], False, details)
        
        if error_success_count >= len(error_tests) * 0.7:  # 70% успешности для обработки ошибок
            self.test_results["error_handling_success"] = True
            return True
        else:
            return False
    
    def test_session_management(self):
        """Тестирование управления сессиями"""
        self.log("\n🔄 Тестирование управления сессиями...")
        
        # Тест 1: Создание множественных сессий (должно возвращать существующую)
        self.log("📋 Тест: Создание множественных сессий...")
        
        timestamp = int(time.time())
        transport_qr = f"TRANSPORT_{TEST_TRANSPORT_NUMBER}_{timestamp}"
        
        try:
            # Первая сессия
            response1 = self.session.post(f"{API_BASE}/logistics/cargo-to-transport/scan-transport", json={
                "qr_code": transport_qr
            })
            
            # Вторая попытка создания сессии
            response2 = self.session.post(f"{API_BASE}/logistics/cargo-to-transport/scan-transport", json={
                "qr_code": transport_qr
            })
            
            if response1.status_code == 200 and response2.status_code == 200:
                data1 = response1.json()
                data2 = response2.json()
                
                session_id1 = data1.get("session_id")
                session_id2 = data2.get("session_id")
                
                if session_id1 == session_id2:
                    details = f"Корректно возвращена существующая сессия: {session_id1}"
                    self.add_test_result("Управление множественными сессиями", True, details)
                    self.current_session_id = session_id1
                    session_mgmt_success = True
                else:
                    details = f"Созданы разные сессии: {session_id1} vs {session_id2}"
                    self.add_test_result("Управление множественными сессиями", False, details)
                    session_mgmt_success = False
            else:
                details = f"Ошибки при создании сессий: {response1.status_code}, {response2.status_code}"
                self.add_test_result("Управление множественными сессиями", False, details)
                session_mgmt_success = False
                
        except Exception as e:
            details = f"Исключение: {e}"
            self.add_test_result("Управление множественными сессиями", False, details)
            session_mgmt_success = False
        
        # Тест 2: Получение сессии по ID
        if self.current_session_id:
            try:
                response = self.session.get(f"{API_BASE}/logistics/cargo-to-transport/session", params={
                    "session_id": self.current_session_id
                })
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("session_id") == self.current_session_id:
                        details = f"Сессия найдена по ID: {self.current_session_id}"
                        self.add_test_result("Получение сессии по ID", True, details)
                    else:
                        details = f"Неверная сессия возвращена: {data.get('session_id')}"
                        self.add_test_result("Получение сессии по ID", False, details)
                        session_mgmt_success = False
                else:
                    details = f"Ошибка получения сессии: HTTP {response.status_code}"
                    self.add_test_result("Получение сессии по ID", False, details)
                    session_mgmt_success = False
                    
            except Exception as e:
                details = f"Исключение: {e}"
                self.add_test_result("Получение сессии по ID", False, details)
                session_mgmt_success = False
        
        if session_mgmt_success:
            self.test_results["session_management_success"] = True
            return True
        else:
            return False
    
    def run_comprehensive_test(self):
        """Запуск полного комплексного тестирования"""
        self.log("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: ЭТАП 2 - API endpoints для размещения грузов на транспорт")
        self.log("=" * 100)
        
        # Этап 1: Авторизация
        if not self.authenticate_warehouse_operator():
            self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться. Тестирование прервано.", "ERROR")
            return False
        
        # Этап 2: Тестирование основных endpoints
        self.log("\n🔥 ЭТАП 2: ТЕСТИРОВАНИЕ ОСНОВНЫХ ENDPOINTS")
        self.log("-" * 60)
        
        # Сценарий 1: Полный workflow размещения
        self.log("\n📋 СЦЕНАРИЙ 1: ПОЛНЫЙ WORKFLOW РАЗМЕЩЕНИЯ")
        self.test_scan_transport_endpoint()
        self.test_scan_cargo_endpoint()
        self.test_get_session_endpoint()
        self.test_delete_session_endpoint()
        
        # Сценарий 2: Обработка ошибок
        self.log("\n📋 СЦЕНАРИЙ 2: ОБРАБОТКА ОШИБОК")
        self.test_error_handling()
        
        # Сценарий 3: Управление сессиями
        self.log("\n📋 СЦЕНАРИЙ 3: УПРАВЛЕНИЕ СЕССИЯМИ")
        self.test_session_management()
        
        # Финальная очистка (завершение любых оставшихся сессий)
        if self.current_session_id:
            self.test_delete_session_endpoint()
        
        return True
    
    def print_final_report(self):
        """Вывод финального отчета"""
        self.log("\n" + "=" * 100)
        self.log("🎉 ФИНАЛЬНЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        self.log("=" * 100)
        
        # Общая статистика
        total_tests = self.test_results["total_tests"]
        passed_tests = self.test_results["passed_tests"]
        failed_tests = self.test_results["failed_tests"]
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.log(f"📊 ОБЩАЯ СТАТИСТИКА:")
        self.log(f"   Всего тестов: {total_tests}")
        self.log(f"   Пройдено: {passed_tests}")
        self.log(f"   Провалено: {failed_tests}")
        self.log(f"   Успешность: {success_rate:.1f}%")
        
        # Статус основных функций
        self.log(f"\n🎯 СТАТУС ОСНОВНЫХ ФУНКЦИЙ:")
        functions = [
            ("Авторизация оператора склада", self.test_results["auth_success"]),
            ("Сканирование транспорта", self.test_results["scan_transport_success"]),
            ("Сканирование грузов", self.test_results["scan_cargo_success"]),
            ("Получение активной сессии", self.test_results["get_session_success"]),
            ("Завершение сессии", self.test_results["delete_session_success"]),
            ("Обработка ошибок", self.test_results["error_handling_success"]),
            ("Управление сессиями", self.test_results["session_management_success"])
        ]
        
        for func_name, success in functions:
            status = "✅" if success else "❌"
            self.log(f"   {status} {func_name}")
        
        # Детальные результаты
        self.log(f"\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ ТЕСТОВ:")
        for result in self.test_results["detailed_results"]:
            self.log(f"   {result['status']}: {result['test_name']} ({result['response_time']})")
            if result['details']:
                self.log(f"      └─ {result['details']}")
        
        # Итоговый вердикт
        self.log(f"\n🏆 ИТОГОВЫЙ ВЕРДИКТ:")
        if success_rate >= 90:
            self.log("✅ ОТЛИЧНО! Все критические функции работают корректно.")
            self.log("🚀 СИСТЕМА ГОТОВА К ПРОДАКШЕНУ!")
        elif success_rate >= 70:
            self.log("⚠️ ХОРОШО! Основные функции работают, но есть проблемы.")
            self.log("🔧 ТРЕБУЮТСЯ НЕЗНАЧИТЕЛЬНЫЕ ИСПРАВЛЕНИЯ.")
        else:
            self.log("❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ! Система не готова к использованию.")
            self.log("🚨 ТРЕБУЕТСЯ СЕРЬЕЗНАЯ ДОРАБОТКА!")
        
        self.log("=" * 100)
        
        return success_rate >= 70

def main():
    """Главная функция запуска тестирования"""
    print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: ЭТАП 2 - API endpoints для размещения грузов на транспорт")
    print("Дата:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("Backend URL:", BACKEND_URL)
    print()
    
    tester = CargoToTransportStage2Tester()
    
    try:
        # Запуск комплексного тестирования
        success = tester.run_comprehensive_test()
        
        if success:
            # Вывод финального отчета
            overall_success = tester.print_final_report()
            
            # Возврат кода выхода
            sys.exit(0 if overall_success else 1)
        else:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Тестирование не удалось запустить")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"❌ НЕОЖИДАННАЯ ОШИБКА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
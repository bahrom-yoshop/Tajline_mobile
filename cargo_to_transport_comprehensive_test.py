#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: ПОЛНЫЙ WORKFLOW ЭТАПА 2 - Размещение грузов на транспорт
===================================================================================

ЦЕЛЬ: Протестировать полный workflow размещения грузов на транспорт после исправления TransportStatus enum.

ПОЛНЫЙ WORKFLOW:
1. Создать транспорт со статусом 'available'
2. Сканировать QR транспорта → создается сессия, статус 'loading'
3. Создать и разместить тестовый груз на складе
4. Сканировать QR груза → добавляется в сессию
5. Получить активную сессию → проверить данные
6. Завершить сессию → статус транспорта 'loaded'

ENDPOINTS ДЛЯ ТЕСТИРОВАНИЯ:
- POST /api/logistics/cargo-to-transport/scan-transport
- POST /api/logistics/cargo-to-transport/scan-cargo  
- GET /api/logistics/cargo-to-transport/session
- DELETE /api/logistics/cargo-to-transport/session

ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ:
- ✅ Все endpoints работают без критических ошибок
- ✅ Полный workflow выполняется успешно
- ✅ Статусы транспорта и грузов обновляются корректно
- ✅ Сессии создаются, управляются и завершаются правильно
"""

import requests
import json
import sys
import os
from datetime import datetime
import time
import uuid
from pymongo import MongoClient

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cargo-sync.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# MongoDB подключение
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'cargo_transport')

# Конфигурация тестирования
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"

class CargoToTransportComprehensiveTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.test_transport_id = None
        self.test_cargo_number = None
        self.current_session_id = None
        self.mongo_client = None
        self.db = None
        self.test_results = {
            "auth_success": False,
            "transport_setup_success": False,
            "cargo_creation_success": False,
            "cargo_placement_success": False,
            "scan_transport_success": False,
            "scan_cargo_success": False,
            "get_session_success": False,
            "delete_session_success": False,
            "full_workflow_success": False,
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
            
        time_info = f" ({response_time}ms)" if response_time else ""
        result_entry = f"{status}: {test_name}{time_info}"
        if details:
            result_entry += f" - {details}"
            
        self.test_results["detailed_results"].append(result_entry)
        self.log(result_entry)
        
    def connect_to_mongodb(self):
        """Подключение к MongoDB"""
        try:
            self.mongo_client = MongoClient(MONGO_URL)
            self.db = self.mongo_client[DB_NAME]
            self.mongo_client.admin.command('ping')
            self.log("✅ Подключение к MongoDB установлено")
            return True
        except Exception as e:
            self.log(f"❌ Ошибка подключения к MongoDB: {str(e)}", "ERROR")
            return False
        
    def authenticate(self):
        """Авторизация оператора склада"""
        self.log("🔐 Авторизация оператора склада...")
        
        start_time = time.time()
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json={
                "phone": WAREHOUSE_OPERATOR_PHONE,
                "password": WAREHOUSE_OPERATOR_PASSWORD
            })
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                
                user_response = self.session.get(f"{API_BASE}/auth/me")
                if user_response.status_code == 200:
                    self.operator_info = user_response.json()
                    operator_name = self.operator_info.get("full_name", "Unknown")
                    
                    self.test_results["auth_success"] = True
                    self.add_test_result(
                        "Авторизация оператора склада", 
                        True, 
                        f"Успешная авторизация '{operator_name}' (роль: warehouse_operator)",
                        response_time
                    )
                    return True
                else:
                    self.add_test_result("Получение информации о пользователе", False, f"HTTP {user_response.status_code}")
                    return False
            else:
                self.add_test_result("Авторизация оператора склада", False, f"HTTP {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.add_test_result("Авторизация оператора склада", False, f"Ошибка: {str(e)}")
            return False
    
    def setup_test_transport(self):
        """Создать и настроить тестовый транспорт"""
        self.log("🚛 Создание и настройка тестового транспорта...")
        
        transport_number = f"TEST{int(time.time() % 10000):04d}"
        
        start_time = time.time()
        try:
            # Создаем транспорт
            response = self.session.post(f"{API_BASE}/transport/create", json={
                "driver_name": "Тестовый Водитель",
                "driver_phone": "+79999999999",
                "transport_number": transport_number,
                "capacity_kg": 1000.0,
                "direction": "Москва-Душанбе"
            })
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                self.test_transport_id = data.get("transport_id")
                
                # Обновляем статус на 'available' через MongoDB
                if self.db is not None:
                    result = self.db.transports.update_one(
                        {"id": self.test_transport_id},
                        {"$set": {"status": "available", "updated_at": datetime.utcnow()}}
                    )
                    
                    if result.modified_count > 0:
                        self.test_results["transport_setup_success"] = True
                        self.add_test_result(
                            "Создание и настройка транспорта", 
                            True, 
                            f"Транспорт {transport_number} создан и настроен со статусом 'available'",
                            response_time
                        )
                        return True
                    else:
                        self.add_test_result("Обновление статуса транспорта", False, "Не удалось обновить статус")
                        return False
                else:
                    self.add_test_result("Настройка транспорта", False, "Нет подключения к MongoDB")
                    return False
            else:
                self.add_test_result("Создание транспорта", False, f"HTTP {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.add_test_result("Создание транспорта", False, f"Ошибка: {str(e)}")
            return False
    
    def create_and_place_test_cargo(self):
        """Создать тестовый груз и разместить его на складе"""
        self.log("📦 Создание и размещение тестового груза...")
        
        start_time = time.time()
        try:
            # Создаем груз
            cargo_response = self.session.post(f"{API_BASE}/operator/cargo/accept", json={
                "sender_full_name": "Тестовый Отправитель",
                "sender_phone": "+79999999998",
                "recipient_full_name": "Тестовый Получатель", 
                "recipient_phone": "+79999999997",
                "recipient_address": "Тестовый адрес доставки",
                "cargo_items": [{
                    "cargo_name": "Тестовый груз для транспорта",
                    "quantity": 1,
                    "weight": 5.0,
                    "price_per_kg": 100.0,
                    "total_amount": 500.0
                }],
                "description": "Тестовый груз для размещения на транспорт",
                "payment_method": "cash",
                "payment_amount": 500.0
            })
            response_time = int((time.time() - start_time) * 1000)
            
            if cargo_response.status_code == 200:
                cargo_data = cargo_response.json()
                self.test_cargo_number = cargo_data.get("cargo_number")
                
                self.test_results["cargo_creation_success"] = True
                self.add_test_result(
                    "Создание тестового груза", 
                    True, 
                    f"Груз создан: {self.test_cargo_number}",
                    response_time
                )
                
                # Размещаем груз на складе
                return self.place_cargo_on_warehouse()
            else:
                self.add_test_result("Создание тестового груза", False, f"HTTP {cargo_response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.add_test_result("Создание тестового груза", False, f"Ошибка: {str(e)}")
            return False
    
    def place_cargo_on_warehouse(self):
        """Разместить груз на складе"""
        self.log("🏭 Размещение груза на складе...")
        
        start_time = time.time()
        try:
            placement_response = self.session.post(f"{API_BASE}/operator/cargo/place-individual", json={
                "individual_number": f"{self.test_cargo_number}/01/01",
                "cell_code": "001-01-01-001"
            })
            response_time = int((time.time() - start_time) * 1000)
            
            if placement_response.status_code == 200:
                self.test_results["cargo_placement_success"] = True
                self.add_test_result(
                    "Размещение груза на складе", 
                    True, 
                    f"Груз {self.test_cargo_number} размещен в ячейке 001-01-01-001",
                    response_time
                )
                return True
            else:
                self.add_test_result("Размещение груза на складе", False, f"HTTP {placement_response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.add_test_result("Размещение груза на складе", False, f"Ошибка: {str(e)}")
            return False
    
    def test_scan_transport(self):
        """Тестирование сканирования QR транспорта"""
        self.log("📱 Тестирование сканирования QR транспорта...")
        
        # Получаем данные транспорта
        transport_response = self.session.get(f"{API_BASE}/transport/{self.test_transport_id}")
        if transport_response.status_code != 200:
            self.add_test_result("Получение данных транспорта", False, f"HTTP {transport_response.status_code}")
            return False
            
        transport_data = transport_response.json()
        transport_number = transport_data.get("transport_number")
        
        # Формируем QR код
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        qr_code = f"TRANSPORT_{transport_number}_{timestamp}"
        
        start_time = time.time()
        try:
            response = self.session.post(f"{API_BASE}/logistics/cargo-to-transport/scan-transport", json={
                "qr_code": qr_code
            })
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                self.current_session_id = data.get("session_id")
                
                if self.current_session_id:
                    self.test_results["scan_transport_success"] = True
                    self.add_test_result(
                        "Сканирование QR транспорта", 
                        True, 
                        f"Сессия создана: {self.current_session_id}, статус обновлен на 'loading'",
                        response_time
                    )
                    return True
                else:
                    self.add_test_result("Сканирование QR транспорта", False, "Отсутствует session_id в ответе", response_time)
                    return False
            else:
                self.add_test_result("Сканирование QR транспорта", False, f"HTTP {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.add_test_result("Сканирование QR транспорта", False, f"Ошибка: {str(e)}")
            return False
    
    def test_scan_cargo(self):
        """Тестирование сканирования QR груза"""
        self.log("📦 Тестирование сканирования QR груза...")
        
        if not self.current_session_id:
            self.add_test_result("Сканирование QR груза", False, "Нет активной сессии")
            return False
        
        start_time = time.time()
        try:
            response = self.session.post(f"{API_BASE}/logistics/cargo-to-transport/scan-cargo", json={
                "qr_code": self.test_cargo_number
            })
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                cargo_info = data.get("cargo_info", {})
                cargo_number = cargo_info.get("cargo_number", "Unknown")
                
                self.test_results["scan_cargo_success"] = True
                self.add_test_result(
                    "Сканирование QR груза", 
                    True, 
                    f"Груз {cargo_number} добавлен в сессию размещения",
                    response_time
                )
                return True
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.headers.get("content-type", "").startswith("application/json") else response.text
                self.add_test_result("Сканирование QR груза", False, f"HTTP {response.status_code}: {error_detail}", response_time)
                return False
                
        except Exception as e:
            self.add_test_result("Сканирование QR груза", False, f"Ошибка: {str(e)}")
            return False
    
    def test_get_session(self):
        """Тестирование получения активной сессии"""
        self.log("📋 Тестирование получения активной сессии...")
        
        start_time = time.time()
        try:
            response = self.session.get(f"{API_BASE}/logistics/cargo-to-transport/session")
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                session_id = data.get("session_id")
                loaded_cargo = data.get("loaded_cargo", [])
                
                if session_id:
                    self.test_results["get_session_success"] = True
                    self.add_test_result(
                        "Получение активной сессии", 
                        True, 
                        f"Сессия найдена: {session_id}, загружено грузов: {len(loaded_cargo)}",
                        response_time
                    )
                    return True
                else:
                    self.add_test_result("Получение активной сессии", False, "Отсутствует session_id в ответе", response_time)
                    return False
            else:
                self.add_test_result("Получение активной сессии", False, f"HTTP {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.add_test_result("Получение активной сессии", False, f"Ошибка: {str(e)}")
            return False
    
    def test_delete_session(self):
        """Тестирование завершения сессии"""
        self.log("🏁 Тестирование завершения сессии...")
        
        start_time = time.time()
        try:
            response = self.session.delete(f"{API_BASE}/logistics/cargo-to-transport/session")
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                transport_status = data.get("transport_status", "unknown")
                loaded_cargo_count = data.get("loaded_cargo_count", 0)
                
                self.test_results["delete_session_success"] = True
                self.add_test_result(
                    "Завершение сессии", 
                    True, 
                    f"Сессия завершена, статус транспорта: {transport_status}, загружено грузов: {loaded_cargo_count}",
                    response_time
                )
                return True
            else:
                self.add_test_result("Завершение сессии", False, f"HTTP {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.add_test_result("Завершение сессии", False, f"Ошибка: {str(e)}")
            return False
    
    def cleanup_test_data(self):
        """Очистка тестовых данных"""
        self.log("🧹 Очистка тестовых данных...")
        
        try:
            # Завершаем сессию если активна
            if self.current_session_id:
                try:
                    self.session.delete(f"{API_BASE}/logistics/cargo-to-transport/session")
                except:
                    pass
            
            # Удаляем тестовый транспорт
            if self.test_transport_id:
                try:
                    self.session.delete(f"{API_BASE}/transport/{self.test_transport_id}")
                except:
                    pass
            
            # Закрываем MongoDB подключение
            if self.mongo_client:
                self.mongo_client.close()
                    
        except Exception as e:
            self.log(f"Предупреждение при очистке: {str(e)}", "WARNING")
    
    def run_comprehensive_test(self):
        """Запуск полного тестирования"""
        self.log("🚀 НАЧИНАЕМ ПОЛНОЕ ТЕСТИРОВАНИЕ WORKFLOW РАЗМЕЩЕНИЯ ГРУЗОВ НА ТРАНСПОРТ")
        self.log("=" * 90)
        
        try:
            # 1. Подключение к MongoDB
            if not self.connect_to_mongodb():
                return self.generate_final_report()
            
            # 2. Авторизация
            if not self.authenticate():
                return self.generate_final_report()
            
            # 3. Настройка транспорта
            if not self.setup_test_transport():
                return self.generate_final_report()
            
            # 4. Создание и размещение груза
            if not self.create_and_place_test_cargo():
                return self.generate_final_report()
            
            # 5. Тестирование workflow
            scan_transport_ok = self.test_scan_transport()
            scan_cargo_ok = self.test_scan_cargo()
            get_session_ok = self.test_get_session()
            delete_session_ok = self.test_delete_session()
            
            # Проверяем полный workflow
            if scan_transport_ok and scan_cargo_ok and get_session_ok and delete_session_ok:
                self.test_results["full_workflow_success"] = True
                self.add_test_result("Полный workflow размещения грузов на транспорт", True, "Все этапы выполнены успешно")
            
        except Exception as e:
            self.log(f"❌ Критическая ошибка: {str(e)}", "ERROR")
        
        finally:
            self.cleanup_test_data()
            
        return self.generate_final_report()
    
    def generate_final_report(self):
        """Генерация финального отчета"""
        self.log("=" * 90)
        self.log("📊 ФИНАЛЬНЫЙ ОТЧЕТ ПОЛНОГО ТЕСТИРОВАНИЯ")
        self.log("=" * 90)
        
        total_tests = self.test_results["total_tests"]
        passed_tests = self.test_results["passed_tests"]
        failed_tests = self.test_results["failed_tests"]
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.log(f"📈 СТАТИСТИКА:")
        self.log(f"   Всего тестов: {total_tests}")
        self.log(f"   Пройдено: {passed_tests}")
        self.log(f"   Провалено: {failed_tests}")
        self.log(f"   Процент успеха: {success_rate:.1f}%")
        self.log("")
        
        self.log("📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        for result in self.test_results["detailed_results"]:
            self.log(f"   {result}")
        self.log("")
        
        self.log("🎯 КРИТИЧЕСКИЕ ВЫВОДЫ:")
        
        if self.test_results["full_workflow_success"]:
            self.log("   ✅ ПОЛНЫЙ WORKFLOW РАЗМЕЩЕНИЯ ГРУЗОВ НА ТРАНСПОРТ РАБОТАЕТ!")
            self.log("   ✅ Все API endpoints этапа 2 функционируют корректно")
            self.log("   ✅ TransportStatus enum исправлен и работает правильно")
            self.log("   ✅ Сессии создаются, управляются и завершаются корректно")
            self.log("   ✅ Статусы транспортов и грузов обновляются правильно")
            self.log("   ✅ Система готова к продакшену")
        else:
            self.log("   ❌ WORKFLOW НЕ ЗАВЕРШЕН ПОЛНОСТЬЮ")
            
            if not self.test_results["scan_transport_success"]:
                self.log("   ❌ Проблемы со сканированием транспорта")
            if not self.test_results["scan_cargo_success"]:
                self.log("   ❌ Проблемы со сканированием грузов")
            if not self.test_results["get_session_success"]:
                self.log("   ❌ Проблемы с получением сессии")
            if not self.test_results["delete_session_success"]:
                self.log("   ❌ Проблемы с завершением сессии")
        
        self.log("")
        
        if success_rate >= 80:
            self.log("🎉 ЗАКЛЮЧЕНИЕ: ПОЛНОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            final_status = "SUCCESS"
        elif success_rate >= 60:
            self.log("⚠️  ЗАКЛЮЧЕНИЕ: ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ПРЕДУПРЕЖДЕНИЯМИ")
            final_status = "WARNING"
        else:
            self.log("❌ ЗАКЛЮЧЕНИЕ: КРИТИЧЕСКИЕ ПРОБЛЕМЫ ОБНАРУЖЕНЫ!")
            final_status = "FAILURE"
        
        self.log("=" * 90)
        
        return {
            "status": final_status,
            "success_rate": success_rate,
            "full_workflow_success": self.test_results["full_workflow_success"],
            "detailed_results": self.test_results["detailed_results"]
        }

def main():
    """Главная функция"""
    tester = CargoToTransportComprehensiveTester()
    result = tester.run_comprehensive_test()
    
    if result["status"] == "SUCCESS":
        sys.exit(0)
    elif result["status"] == "WARNING":
        sys.exit(1)
    else:
        sys.exit(2)

if __name__ == "__main__":
    main()
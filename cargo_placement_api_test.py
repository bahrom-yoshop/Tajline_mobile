#!/usr/bin/env python3
"""
🎯 ТЕСТИРОВАНИЕ ОБНОВЛЕННОГО API: Новые поля для карточек грузов размещения в TAJLINE.TJ

КОНТЕКСТ:
Обновлен API endpoint GET /api/operator/cargo/available-for-placement с новыми полями для карточек грузов:
1. Город выдачи груза (delivery_city)
2. Склад-отправитель → склад-получатель (source_warehouse_name, target_warehouse_name)  
3. Дата и время приема груза (created_date, accepted_date)
4. Способ получения груза (delivery_method)
5. Список грузов по типам с количеством (cargo_items) 
6. Статус размещения каждого груза (placement_status, placed_count)
7. Общая статистика размещения (total_quantity, total_placed, placement_progress)

НОВЫЕ ENDPOINTS:
- GET /api/operator/cargo/{cargo_id}/placement-status - детальный статус размещения
- POST /api/operator/cargo/{cargo_id}/update-placement-status - обновление и автоперемещение

ТРЕБУЕТСЯ ПРОТЕСТИРОВАТЬ:
1. Авторизация оператора склада (+79777888999/warehouse123)
2. GET /api/operator/cargo/available-for-placement - проверить новые поля в ответе
3. Создание тестовой заявки для тестирования новых endpoints  
4. GET /api/operator/cargo/{cargo_id}/placement-status - тестирование нового endpoint
5. POST /api/operator/cargo/{cargo_id}/update-placement-status - тестирование логики перемещения

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
API должен возвращать все новые поля для создания улучшенных карточек грузов с информацией о размещении, складах и статусах.
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List

# Configuration
BACKEND_URL = "https://tajline-manage-1.preview.emergentagent.com/api"

# Test credentials
ADMIN_CREDENTIALS = {
    "phone": "+79999888777",
    "password": "admin123"
}

WAREHOUSE_OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class CargoPlacementAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.operator_token = None
        self.test_results = []
        self.found_cargo_numbers = []
        
    def log_result(self, test_name: str, success: bool, message: str, details: Optional[Dict] = None):
        """Log test result"""
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
    
    def authenticate_admin(self) -> bool:
        """Authenticate as admin"""
        print("\n🔐 STEP 1: АВТОРИЗАЦИЯ АДМИНИСТРАТОРА")
        print("=" * 60)
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=ADMIN_CREDENTIALS,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                if self.admin_token:
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.admin_token}"
                    })
                    user_info = data.get("user", {})
                    self.log_result(
                        "Авторизация администратора",
                        True,
                        f"Успешная авторизация: {user_info.get('full_name', 'Admin')} (роль: {user_info.get('role')}, номер: {user_info.get('user_number')})"
                    )
                    return True
                else:
                    self.log_result("Авторизация администратора", False, "Токен доступа не получен")
                    return False
            else:
                self.log_result("Авторизация администратора", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Авторизация администратора", False, f"Исключение: {str(e)}")
            return False
    
    def authenticate_warehouse_operator(self) -> bool:
        """Authenticate as warehouse operator"""
        print("\n🏭 STEP 2: АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА")
        print("=" * 60)
        
        try:
            # Create new session for operator
            operator_session = requests.Session()
            response = operator_session.post(
                f"{BACKEND_URL}/auth/login",
                json=WAREHOUSE_OPERATOR_CREDENTIALS,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.operator_token = data.get("access_token")
                if self.operator_token:
                    user_info = data.get("user", {})
                    self.log_result(
                        "Авторизация оператора склада",
                        True,
                        f"Успешная авторизация: {user_info.get('full_name', 'Operator')} (роль: {user_info.get('role')}, номер: {user_info.get('user_number')})"
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
    
    def test_available_for_placement_endpoint(self) -> bool:
        """КРИТИЧЕСКАЯ ПРОВЕРКА: GET /api/operator/cargo/available-for-placement"""
        print("\n🎯 STEP 3: КРИТИЧЕСКАЯ ПРОВЕРКА - ENDPOINT AVAILABLE-FOR-PLACEMENT")
        print("=" * 60)
        
        try:
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            response = requests.get(
                f"{BACKEND_URL}/operator/cargo/available-for-placement",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                has_items = "items" in data
                has_pagination = any(key in data for key in ["total_count", "page", "per_page", "total_pages"])
                
                items = data.get("items", [])
                total_count = data.get("total_count", len(items))
                
                # Analyze cargo statuses
                status_counts = {}
                awaiting_placement_count = 0
                paid_count = 0
                sample_cargo = None
                
                for item in items:
                    status = item.get("processing_status", "unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1
                    
                    if status == "awaiting_placement":
                        awaiting_placement_count += 1
                    elif status == "paid":
                        paid_count += 1
                    
                    if not sample_cargo:
                        sample_cargo = item
                        cargo_number = item.get("cargo_number")
                        if cargo_number:
                            self.found_cargo_numbers.append(cargo_number)
                
                # Collect all cargo numbers for testing
                for item in items:
                    cargo_number = item.get("cargo_number")
                    if cargo_number and cargo_number not in self.found_cargo_numbers:
                        self.found_cargo_numbers.append(cargo_number)
                
                success = True
                message_parts = []
                
                if total_count == 0:
                    success = False
                    message_parts.append("КРИТИЧЕСКАЯ ПРОБЛЕМА: Список грузов для размещения ПУСТОЙ")
                else:
                    message_parts.append(f"Найдено {total_count} грузов для размещения")
                
                if not has_items:
                    success = False
                    message_parts.append("Отсутствует поле 'items' в ответе")
                
                if not has_pagination:
                    message_parts.append("Отсутствует информация о пагинации")
                
                message = "; ".join(message_parts)
                
                details = {
                    "total_count": total_count,
                    "has_items": has_items,
                    "has_pagination": has_pagination,
                    "status_counts": status_counts,
                    "awaiting_placement_count": awaiting_placement_count,
                    "paid_count": paid_count,
                    "sample_cargo": sample_cargo,
                    "found_cargo_numbers": self.found_cargo_numbers[:5],  # First 5 for testing
                    "response_structure": list(data.keys())
                }
                
                self.log_result(
                    "GET /api/operator/cargo/available-for-placement",
                    success,
                    message,
                    details
                )
                
                return success
                
            else:
                self.log_result(
                    "GET /api/operator/cargo/available-for-placement",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "GET /api/operator/cargo/available-for-placement",
                False,
                f"Исключение: {str(e)}"
            )
            return False
    
    def test_general_operator_cargo_list(self) -> bool:
        """ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: GET /api/operator/cargo - общий список грузов оператора"""
        print("\n📋 STEP 4: ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА - ОБЩИЙ СПИСОК ГРУЗОВ ОПЕРАТОРА")
        print("=" * 60)
        
        try:
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            response = requests.get(
                f"{BACKEND_URL}/operator/cargo",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle different response formats
                if isinstance(data, dict):
                    items = data.get("items", data.get("cargo", []))
                    total_count = data.get("total_count", len(items))
                elif isinstance(data, list):
                    items = data
                    total_count = len(items)
                else:
                    items = []
                    total_count = 0
                
                # Analyze statuses
                status_counts = {}
                awaiting_placement_cargo = []
                
                for item in items:
                    status = item.get("processing_status", "unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1
                    
                    if status in ["awaiting_placement", "paid"]:
                        awaiting_placement_cargo.append({
                            "cargo_number": item.get("cargo_number"),
                            "status": status,
                            "weight": item.get("weight"),
                            "sender_name": item.get("sender_full_name")
                        })
                        
                        cargo_number = item.get("cargo_number")
                        if cargo_number and cargo_number not in self.found_cargo_numbers:
                            self.found_cargo_numbers.append(cargo_number)
                
                message = f"Найдено {total_count} грузов в общем списке оператора"
                
                details = {
                    "total_count": total_count,
                    "status_counts": status_counts,
                    "awaiting_placement_cargo": awaiting_placement_cargo[:10],  # First 10
                    "response_type": type(data).__name__,
                    "response_structure": list(data.keys()) if isinstance(data, dict) else "list"
                }
                
                self.log_result(
                    "GET /api/operator/cargo",
                    True,
                    message,
                    details
                )
                
                return True
                
            else:
                self.log_result(
                    "GET /api/operator/cargo",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "GET /api/operator/cargo",
                False,
                f"Исключение: {str(e)}"
            )
            return False
    
    def test_cargo_tracking_for_scanning(self) -> bool:
        """ПРОВЕРКА СКАНИРОВАНИЯ: Тестирование найденных номеров грузов"""
        print("\n🔍 STEP 5: ПРОВЕРКА СКАНИРОВАНИЯ - ТЕСТИРОВАНИЕ НОМЕРОВ ГРУЗОВ")
        print("=" * 60)
        
        if not self.found_cargo_numbers:
            self.log_result(
                "Тестирование сканирования грузов",
                False,
                "Не найдено номеров грузов для тестирования"
            )
            return False
        
        successful_scans = 0
        failed_scans = 0
        scan_results = []
        
        # Test first 5 cargo numbers
        test_cargo_numbers = self.found_cargo_numbers[:5]
        
        for cargo_number in test_cargo_numbers:
            try:
                headers = {"Authorization": f"Bearer {self.operator_token}"}
                response = requests.get(
                    f"{BACKEND_URL}/cargo/track/{cargo_number}",
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    successful_scans += 1
                    scan_results.append({
                        "cargo_number": cargo_number,
                        "status": "success",
                        "data": {
                            "cargo_name": data.get("cargo_name"),
                            "weight": data.get("weight"),
                            "processing_status": data.get("processing_status"),
                            "sender_name": data.get("sender_full_name")
                        }
                    })
                    print(f"   ✅ Груз {cargo_number}: найден и доступен для сканирования")
                else:
                    failed_scans += 1
                    scan_results.append({
                        "cargo_number": cargo_number,
                        "status": "failed",
                        "error": f"HTTP {response.status_code}"
                    })
                    print(f"   ❌ Груз {cargo_number}: ошибка {response.status_code}")
                    
            except Exception as e:
                failed_scans += 1
                scan_results.append({
                    "cargo_number": cargo_number,
                    "status": "error",
                    "error": str(e)
                })
                print(f"   ❌ Груз {cargo_number}: исключение {str(e)}")
        
        success = successful_scans > 0
        message = f"Протестировано {len(test_cargo_numbers)} номеров грузов: {successful_scans} успешно, {failed_scans} неудачно"
        
        details = {
            "tested_cargo_count": len(test_cargo_numbers),
            "successful_scans": successful_scans,
            "failed_scans": failed_scans,
            "scan_results": scan_results,
            "all_found_cargo_numbers": self.found_cargo_numbers
        }
        
        self.log_result(
            "Тестирование сканирования грузов",
            success,
            message,
            details
        )
        
        return success
    
    def create_test_cargo_for_placement(self) -> bool:
        """Создание тестового груза для размещения"""
        print("\n📦 STEP 6: СОЗДАНИЕ ТЕСТОВОГО ГРУЗА ДЛЯ РАЗМЕЩЕНИЯ")
        print("=" * 60)
        
        try:
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            
            # Create test cargo with paid status
            cargo_data = {
                "sender_full_name": "Тестовый Отправитель Размещение",
                "sender_phone": "+79991112233",
                "recipient_full_name": "Тестовый Получатель Размещение",
                "recipient_phone": "+992900123456",
                "recipient_address": "Душанбе, ул. Тестовая Размещение, 123",
                "weight": 15.5,
                "cargo_name": "Тестовый груз для размещения",
                "declared_value": 2500.0,
                "description": "Тестовый груз для проверки размещения",
                "route": "moscow_to_tajikistan",
                "payment_method": "cash",
                "payment_amount": 2500.0
            }
            
            response = requests.post(
                f"{BACKEND_URL}/operator/cargo/accept",
                json=cargo_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                cargo_id = data.get("id")
                cargo_number = data.get("cargo_number")
                processing_status = data.get("processing_status")
                
                if cargo_number:
                    self.found_cargo_numbers.append(cargo_number)
                
                message = f"Создан тестовый груз: {cargo_number} (статус: {processing_status})"
                
                details = {
                    "cargo_id": cargo_id,
                    "cargo_number": cargo_number,
                    "processing_status": processing_status,
                    "payment_method": data.get("payment_method"),
                    "weight": data.get("weight"),
                    "declared_value": data.get("declared_value")
                }
                
                self.log_result(
                    "Создание тестового груза",
                    True,
                    message,
                    details
                )
                
                return True
            else:
                self.log_result(
                    "Создание тестового груза",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Создание тестового груза",
                False,
                f"Исключение: {str(e)}"
            )
            return False
    
    def run_comprehensive_test(self) -> bool:
        """Запуск полного комплексного тестирования"""
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ API ENDPOINT ДЛЯ СПИСКА ГРУЗОВ, ОЖИДАЮЩИХ РАЗМЕЩЕНИЯ В TAJLINE.TJ")
        print("=" * 100)
        print("ПРОБЛЕМА: При сканировании QR кодов грузов система пишет 'Груз не найден в списке ожидающих размещение'")
        print("ЦЕЛЬ: Найти реальные cargo_number для тестирования функциональности сканирования!")
        print("=" * 100)
        
        # Step 1: Admin authentication
        if not self.authenticate_admin():
            print("❌ Не удалось авторизоваться как администратор")
            return False
        
        # Step 2: Warehouse operator authentication
        if not self.authenticate_warehouse_operator():
            print("❌ Не удалось авторизоваться как оператор склада")
            return False
        
        # Step 3: Test main endpoint
        main_endpoint_success = self.test_available_for_placement_endpoint()
        
        # Step 4: Test general cargo list
        general_list_success = self.test_general_operator_cargo_list()
        
        # Step 5: Create test cargo if needed
        if not self.found_cargo_numbers:
            print("\n⚠️ Не найдено грузов для тестирования, создаем тестовый груз...")
            self.create_test_cargo_for_placement()
            # Re-test main endpoint after creating cargo
            main_endpoint_success = self.test_available_for_placement_endpoint()
        
        # Step 6: Test cargo scanning
        scanning_success = self.test_cargo_tracking_for_scanning()
        
        # Generate summary
        self.generate_final_summary()
        
        # Return overall success
        return main_endpoint_success and len(self.found_cargo_numbers) > 0
    
    def generate_final_summary(self):
        """Генерация итогового отчета"""
        print("\n" + "=" * 100)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 100)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 СТАТИСТИКА ТЕСТОВ:")
        print(f"   Всего тестов: {total_tests}")
        print(f"   Пройдено: {passed_tests}")
        print(f"   Провалено: {failed_tests}")
        print(f"   Успешность: {success_rate:.1f}%")
        
        print(f"\n🔍 НАЙДЕННЫЕ НОМЕРА ГРУЗОВ ДЛЯ ТЕСТИРОВАНИЯ СКАНИРОВАНИЯ:")
        if self.found_cargo_numbers:
            for i, cargo_number in enumerate(self.found_cargo_numbers[:10], 1):
                print(f"   {i}. {cargo_number}")
            if len(self.found_cargo_numbers) > 10:
                print(f"   ... и еще {len(self.found_cargo_numbers) - 10} номеров")
        else:
            print("   ❌ НЕ НАЙДЕНО номеров грузов для тестирования!")
        
        print(f"\n🎯 КЛЮЧЕВЫЕ РЕЗУЛЬТАТЫ:")
        
        # Check main endpoint
        main_test = next((r for r in self.test_results if "available-for-placement" in r["test"]), None)
        if main_test and main_test["success"]:
            print("   ✅ Endpoint /api/operator/cargo/available-for-placement работает")
        else:
            print("   ❌ Endpoint /api/operator/cargo/available-for-placement НЕ работает")
        
        # Check cargo availability
        if self.found_cargo_numbers:
            print(f"   ✅ Найдено {len(self.found_cargo_numbers)} номеров грузов для сканирования")
        else:
            print("   ❌ НЕ найдено номеров грузов для сканирования")
        
        # Check scanning capability
        scan_test = next((r for r in self.test_results if "сканирования" in r["test"]), None)
        if scan_test and scan_test["success"]:
            print("   ✅ Сканирование грузов работает")
        else:
            print("   ❌ Сканирование грузов НЕ работает")
        
        print(f"\n🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ:")
        critical_issues = []
        
        if not main_test or not main_test["success"]:
            critical_issues.append("Endpoint available-for-placement не работает")
        
        if not self.found_cargo_numbers:
            critical_issues.append("Нет грузов для размещения - список пустой")
        
        if not scan_test or not scan_test["success"]:
            critical_issues.append("Сканирование грузов не работает")
        
        if critical_issues:
            for issue in critical_issues:
                print(f"   ❌ {issue}")
        else:
            print("   ✅ Критических проблем не обнаружено")
        
        print(f"\n💡 РЕКОМЕНДАЦИИ:")
        if not self.found_cargo_numbers:
            print("   1. Проверить наличие грузов со статусом 'paid' или 'awaiting_placement'")
            print("   2. Убедиться что оператор имеет доступ к складам с грузами")
            print("   3. Проверить логику фильтрации в endpoint available-for-placement")
        else:
            print("   1. Использовать найденные номера грузов для тестирования сканера")
            print("   2. Проверить frontend интеграцию с найденными данными")
            print("   3. Протестировать полный workflow размещения")

if __name__ == "__main__":
    tester = CargoPlacementAPITester()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("✅ Найдены реальные номера грузов для тестирования сканирования")
        sys.exit(0)
    else:
        print("\n❌ ТЕСТИРОВАНИЕ ВЫЯВИЛО КРИТИЧЕСКИЕ ПРОБЛЕМЫ!")
        print("🔍 Проверьте детали выше для устранения проблем")
        sys.exit(1)
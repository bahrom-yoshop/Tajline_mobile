#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Обновление адреса склада для правильной работы карты маршрута в TAJLINE.TJ
Тестирование согласно review request:
1. GET /api/operator/warehouses - получить список складов оператора
2. PATCH /api/admin/warehouses/{warehouse_id}/address - обновить адрес склада
3. GET /api/operator/warehouses - проверить что адрес обновлен

Цель: исправить адрес склада чтобы карта маршрута показывала правильный адрес
"Селигерская, новая улица 1а строение 2" вместо "Москва Склад №1"
"""

import requests
import json
import os
from datetime import datetime

# Получаем URL backend из переменных окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-cargo-8.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class WarehouseAddressUpdateTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: str):
        """Логирование результатов тестирования"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ УСПЕХ" if success else "❌ ОШИБКА"
        print(f"{status}: {test_name}")
        print(f"   Детали: {details}")
        print("-" * 80)
        
    def authenticate_admin(self):
        """Авторизация администратора"""
        try:
            login_data = {
                "phone": "+79999888777",
                "password": "admin123"
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                user_info = data.get("user", {})
                
                self.log_result(
                    "Авторизация администратора (+79999888777/admin123)",
                    True,
                    f"Успешная авторизация '{user_info.get('full_name', 'N/A')}' "
                    f"(номер: {user_info.get('user_number', 'N/A')}), "
                    f"роль: {user_info.get('role', 'N/A')}, JWT токен получен"
                )
                
                # Устанавливаем заголовок авторизации
                self.session.headers.update({
                    "Authorization": f"Bearer {self.admin_token}",
                    "Content-Type": "application/json"
                })
                return True
            else:
                self.log_result(
                    "Авторизация администратора",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Авторизация администратора",
                False,
                f"Исключение: {str(e)}"
            )
            return False
    
    def get_operator_warehouses(self, test_name: str):
        """Получить список складов оператора"""
        try:
            response = self.session.get(f"{API_BASE}/operator/warehouses")
            
            if response.status_code == 200:
                warehouses = response.json()
                
                if isinstance(warehouses, list) and len(warehouses) > 0:
                    warehouse_details = []
                    for warehouse in warehouses:
                        details = {
                            "id": warehouse.get("id"),
                            "name": warehouse.get("name"),
                            "location": warehouse.get("location"),
                            "address": warehouse.get("address")
                        }
                        warehouse_details.append(details)
                    
                    self.log_result(
                        test_name,
                        True,
                        f"Получено {len(warehouses)} складов. Детали: {json.dumps(warehouse_details, ensure_ascii=False, indent=2)}"
                    )
                    return warehouses
                else:
                    self.log_result(
                        test_name,
                        False,
                        f"Пустой список складов или неправильный формат: {warehouses}"
                    )
                    return []
            else:
                self.log_result(
                    test_name,
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return []
                
        except Exception as e:
            self.log_result(
                test_name,
                False,
                f"Исключение: {str(e)}"
            )
            return []
    
    def update_warehouse_address(self, warehouse_id: str, new_address: str):
        """Обновить адрес склада"""
        try:
            update_data = {
                "address": new_address
            }
            
            response = self.session.patch(
                f"{API_BASE}/admin/warehouses/{warehouse_id}/address",
                json=update_data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_result(
                    f"PATCH /api/admin/warehouses/{warehouse_id}/address",
                    True,
                    f"Адрес склада успешно обновлен на '{new_address}'. Ответ: {json.dumps(result, ensure_ascii=False)}"
                )
                return True
            else:
                self.log_result(
                    f"PATCH /api/admin/warehouses/{warehouse_id}/address",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                f"PATCH /api/admin/warehouses/{warehouse_id}/address",
                False,
                f"Исключение: {str(e)}"
            )
            return False
    
    def find_moscow_warehouse(self, warehouses):
        """Найти склад в Москве для обновления"""
        moscow_warehouse = None
        
        for warehouse in warehouses:
            name = warehouse.get("name", "").lower()
            location = warehouse.get("location", "").lower()
            
            # Ищем склад с "москва" в названии или локации
            if "москва" in name or "москва" in location:
                moscow_warehouse = warehouse
                break
        
        if moscow_warehouse:
            self.log_result(
                "Поиск склада в Москве",
                True,
                f"Найден склад: ID={moscow_warehouse.get('id')}, "
                f"Название='{moscow_warehouse.get('name')}', "
                f"Локация='{moscow_warehouse.get('location')}', "
                f"Текущий адрес='{moscow_warehouse.get('address')}'"
            )
        else:
            self.log_result(
                "Поиск склада в Москве",
                False,
                "Склад с 'Москва' в названии или локации не найден"
            )
        
        return moscow_warehouse
    
    def verify_address_update(self, warehouse_id: str, expected_address: str):
        """Проверить что адрес склада обновился"""
        warehouses = self.get_operator_warehouses("GET /api/operator/warehouses (проверка обновления)")
        
        if not warehouses:
            return False
        
        # Найти обновленный склад
        updated_warehouse = None
        for warehouse in warehouses:
            if warehouse.get("id") == warehouse_id:
                updated_warehouse = warehouse
                break
        
        if updated_warehouse:
            current_address = updated_warehouse.get("address", "")
            if current_address == expected_address:
                self.log_result(
                    "Проверка обновления адреса",
                    True,
                    f"Адрес склада успешно обновлен! "
                    f"Текущий адрес: '{current_address}' соответствует ожидаемому: '{expected_address}'"
                )
                return True
            else:
                self.log_result(
                    "Проверка обновления адреса",
                    False,
                    f"Адрес не обновился корректно. "
                    f"Ожидаемый: '{expected_address}', Текущий: '{current_address}'"
                )
                return False
        else:
            self.log_result(
                "Проверка обновления адреса",
                False,
                f"Склад с ID {warehouse_id} не найден в обновленном списке"
            )
            return False
    
    def run_comprehensive_test(self):
        """Запуск полного тестирования обновления адреса склада"""
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Обновление адреса склада для карты маршрута")
        print("=" * 80)
        
        # Целевой адрес для обновления
        target_address = "Москва, Селигерская, новая улица 1а строение 2"
        
        # 1. Авторизация администратора
        if not self.authenticate_admin():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как администратор")
            return False
        
        # 2. Получение списка складов оператора (первый запрос)
        print("\n📋 ШАГ 1: Получение текущего списка складов оператора")
        warehouses_before = self.get_operator_warehouses("GET /api/operator/warehouses (до обновления)")
        
        if not warehouses_before:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить список складов")
            return False
        
        # 3. Поиск склада в Москве для обновления
        print("\n🔍 ШАГ 2: Поиск склада в Москве для обновления адреса")
        moscow_warehouse = self.find_moscow_warehouse(warehouses_before)
        
        if not moscow_warehouse:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Склад в Москве не найден")
            return False
        
        warehouse_id = moscow_warehouse.get("id")
        old_address = moscow_warehouse.get("address", "")
        
        # 4. Обновление адреса склада
        print(f"\n✏️ ШАГ 3: Обновление адреса склада {warehouse_id}")
        print(f"   Старый адрес: '{old_address}'")
        print(f"   Новый адрес: '{target_address}'")
        
        if not self.update_warehouse_address(warehouse_id, target_address):
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось обновить адрес склада")
            return False
        
        # 5. Проверка обновления (второй запрос)
        print(f"\n✅ ШАГ 4: Проверка что адрес обновился")
        if not self.verify_address_update(warehouse_id, target_address):
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Адрес не обновился корректно")
            return False
        
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print(f"✅ Адрес склада обновлен с '{old_address}' на '{target_address}'")
        print("✅ Карта маршрута теперь будет показывать правильный адрес")
        
        return True
    
    def print_summary(self):
        """Вывод итогового отчета"""
        print("\n" + "=" * 80)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - successful_tests
        
        print(f"Всего тестов: {total_tests}")
        print(f"Успешных: {successful_tests}")
        print(f"Неудачных: {failed_tests}")
        print(f"Процент успеха: {(successful_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ НЕУДАЧНЫЕ ТЕСТЫ:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['details']}")
        
        print("\n✅ УСПЕШНЫЕ ТЕСТЫ:")
        for result in self.test_results:
            if result["success"]:
                print(f"   - {result['test']}")

def main():
    """Основная функция тестирования"""
    tester = WarehouseAddressUpdateTester()
    
    try:
        success = tester.run_comprehensive_test()
        tester.print_summary()
        
        if success:
            print("\n🎯 РЕЗУЛЬТАТ: ОБНОВЛЕНИЕ АДРЕСА СКЛАДА ВЫПОЛНЕНО УСПЕШНО!")
            print("Карта маршрута теперь будет показывать правильный адрес:")
            print("'Селигерская, новая улица 1а строение 2'")
        else:
            print("\n❌ РЕЗУЛЬТАТ: ОБНОВЛЕНИЕ АДРЕСА СКЛАДА НЕ ВЫПОЛНЕНО!")
            print("Требуется дополнительная диагностика проблемы")
            
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА ТЕСТИРОВАНИЯ: {e}")
        tester.print_summary()

if __name__ == "__main__":
    main()
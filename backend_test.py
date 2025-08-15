#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправление адреса склада в TAJLINE.TJ
Тестирование исправления адреса склада на правильный согласно review request.

ЗАДАЧА:
1. GET /api/operator/warehouses - получить текущие данные склада
2. PATCH /api/admin/warehouses/{warehouse_id}/address - обновить адрес склада на ПРАВИЛЬНЫЙ
3. GET /api/operator/warehouses - проверить что адрес обновлен на правильный

ПРАВИЛЬНЫЙ АДРЕС: "Москва, новая улица 1а строение 2" (БЕЗ слова "Селигерская")
АВТОРИЗАЦИЯ: phone: "+79999888777", password: "admin123"
"""

import requests
import json
import sys
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://tajline-ops.preview.emergentagent.com/api"
ADMIN_PHONE = "+79999888777"
ADMIN_PASSWORD = "admin123"
CORRECT_ADDRESS = "Москва, новая улица 1а строение 2"

class WarehouseAddressTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        
    def log_result(self, test_name, success, details):
        """Логирование результатов тестирования"""
        status = "✅ УСПЕХ" if success else "❌ ОШИБКА"
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        print(f"   Детали: {details}")
        print()
        
    def authenticate_admin(self):
        """Авторизация администратора"""
        try:
            print("🔐 АВТОРИЗАЦИЯ АДМИНИСТРАТОРА...")
            
            auth_data = {
                "phone": ADMIN_PHONE,
                "password": ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=auth_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                user_info = data.get("user", {})
                
                self.session.headers.update({
                    "Authorization": f"Bearer {self.admin_token}"
                })
                
                self.log_result(
                    "Авторизация администратора",
                    True,
                    f"Успешная авторизация '{user_info.get('full_name', 'N/A')}' (номер: {user_info.get('user_number', 'N/A')}), роль: {user_info.get('role', 'N/A')}"
                )
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
    
    def get_current_warehouses(self):
        """Получить текущие данные складов"""
        try:
            print("📦 ПОЛУЧЕНИЕ ТЕКУЩИХ ДАННЫХ СКЛАДОВ...")
            
            response = self.session.get(f"{BACKEND_URL}/operator/warehouses")
            
            if response.status_code == 200:
                warehouses = response.json()
                
                if warehouses:
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
                        "Получение текущих данных складов",
                        True,
                        f"Найдено {len(warehouses)} складов. Детали: {json.dumps(warehouse_details, ensure_ascii=False, indent=2)}"
                    )
                    return warehouses
                else:
                    self.log_result(
                        "Получение текущих данных складов",
                        False,
                        "Список складов пуст"
                    )
                    return []
            else:
                self.log_result(
                    "Получение текущих данных складов",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return []
                
        except Exception as e:
            self.log_result(
                "Получение текущих данных складов",
                False,
                f"Исключение: {str(e)}"
            )
            return []
    
    def find_moscow_warehouse(self, warehouses):
        """Найти московский склад для обновления адреса"""
        try:
            print("🔍 ПОИСК МОСКОВСКОГО СКЛАДА...")
            
            moscow_warehouses = []
            for warehouse in warehouses:
                location = warehouse.get("location", "").lower()
                name = warehouse.get("name", "").lower()
                
                if "москва" in location or "москва" in name:
                    moscow_warehouses.append(warehouse)
            
            if moscow_warehouses:
                # Берем первый найденный московский склад
                target_warehouse = moscow_warehouses[0]
                
                self.log_result(
                    "Поиск московского склада",
                    True,
                    f"Найден московский склад: '{target_warehouse.get('name')}' (ID: {target_warehouse.get('id')}), текущий адрес: '{target_warehouse.get('address', target_warehouse.get('location'))}'"
                )
                return target_warehouse
            else:
                self.log_result(
                    "Поиск московского склада",
                    False,
                    "Московский склад не найден в списке"
                )
                return None
                
        except Exception as e:
            self.log_result(
                "Поиск московского склада",
                False,
                f"Исключение: {str(e)}"
            )
            return None
    
    def update_warehouse_address(self, warehouse_id):
        """Обновить адрес склада на правильный"""
        try:
            print("🏠 ОБНОВЛЕНИЕ АДРЕСА СКЛАДА НА ПРАВИЛЬНЫЙ...")
            
            address_data = {
                "address": CORRECT_ADDRESS
            }
            
            response = self.session.patch(
                f"{BACKEND_URL}/admin/warehouses/{warehouse_id}/address",
                json=address_data
            )
            
            if response.status_code == 200:
                data = response.json()
                
                self.log_result(
                    "Обновление адреса склада",
                    True,
                    f"Адрес склада успешно обновлен на '{CORRECT_ADDRESS}'. Ответ сервера: {json.dumps(data, ensure_ascii=False)}"
                )
                return True
            else:
                self.log_result(
                    "Обновление адреса склада",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Обновление адреса склада",
                False,
                f"Исключение: {str(e)}"
            )
            return False
    
    def verify_address_update(self, warehouse_id):
        """Проверить что адрес обновлен правильно"""
        try:
            print("✅ ПРОВЕРКА ОБНОВЛЕНИЯ АДРЕСА...")
            
            response = self.session.get(f"{BACKEND_URL}/operator/warehouses")
            
            if response.status_code == 200:
                warehouses = response.json()
                
                # Найти обновленный склад
                updated_warehouse = None
                for warehouse in warehouses:
                    if warehouse.get("id") == warehouse_id:
                        updated_warehouse = warehouse
                        break
                
                if updated_warehouse:
                    current_address = updated_warehouse.get("address")
                    
                    if current_address == CORRECT_ADDRESS:
                        self.log_result(
                            "Проверка обновления адреса",
                            True,
                            f"✅ АДРЕС УСПЕШНО ОБНОВЛЕН! Текущий адрес: '{current_address}' соответствует правильному адресу: '{CORRECT_ADDRESS}'"
                        )
                        return True
                    else:
                        self.log_result(
                            "Проверка обновления адреса",
                            False,
                            f"❌ АДРЕС НЕ СООТВЕТСТВУЕТ! Текущий адрес: '{current_address}', ожидаемый: '{CORRECT_ADDRESS}'"
                        )
                        return False
                else:
                    self.log_result(
                        "Проверка обновления адреса",
                        False,
                        f"Склад с ID {warehouse_id} не найден после обновления"
                    )
                    return False
            else:
                self.log_result(
                    "Проверка обновления адреса",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Проверка обновления адреса",
                False,
                f"Исключение: {str(e)}"
            )
            return False
    
    def check_address_correctness(self, warehouses):
        """Дополнительная проверка правильности адресов"""
        try:
            print("🔍 ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА ПРАВИЛЬНОСТИ АДРЕСОВ...")
            
            issues_found = []
            correct_addresses = []
            
            for warehouse in warehouses:
                name = warehouse.get("name", "")
                address = warehouse.get("address", warehouse.get("location", ""))
                
                if "москва" in name.lower() or "москва" in address.lower():
                    if "селигерская" in address.lower():
                        issues_found.append({
                            "warehouse": name,
                            "id": warehouse.get("id"),
                            "current_address": address,
                            "issue": "Содержит слово 'Селигерская' - должно быть исправлено"
                        })
                    elif address == CORRECT_ADDRESS:
                        correct_addresses.append({
                            "warehouse": name,
                            "id": warehouse.get("id"),
                            "address": address
                        })
            
            if issues_found:
                self.log_result(
                    "Проверка правильности адресов",
                    False,
                    f"Найдены проблемы с адресами: {json.dumps(issues_found, ensure_ascii=False, indent=2)}"
                )
                return False, issues_found
            else:
                self.log_result(
                    "Проверка правильности адресов",
                    True,
                    f"Все московские склады имеют правильные адреса: {json.dumps(correct_addresses, ensure_ascii=False, indent=2)}"
                )
                return True, correct_addresses
                
        except Exception as e:
            self.log_result(
                "Проверка правильности адресов",
                False,
                f"Исключение: {str(e)}"
            )
            return False, []
    
    def run_comprehensive_test(self):
        """Запустить полное тестирование исправления адреса склада"""
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: ИСПРАВЛЕНИЕ АДРЕСА СКЛАДА В TAJLINE.TJ")
        print("=" * 80)
        print(f"Правильный адрес: '{CORRECT_ADDRESS}'")
        print(f"Авторизация: {ADMIN_PHONE}")
        print("=" * 80)
        print()
        
        # 1. Авторизация администратора
        if not self.authenticate_admin():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как администратор")
            return False
        
        # 2. Получение текущих данных складов
        warehouses = self.get_current_warehouses()
        if not warehouses:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить данные складов")
            return False
        
        # 3. Дополнительная проверка правильности адресов (до обновления)
        print("📋 ПРОВЕРКА АДРЕСОВ ДО ОБНОВЛЕНИЯ:")
        is_correct_before, details_before = self.check_address_correctness(warehouses)
        
        # 4. Поиск московского склада
        moscow_warehouse = self.find_moscow_warehouse(warehouses)
        if not moscow_warehouse:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Московский склад не найден")
            return False
        
        warehouse_id = moscow_warehouse.get("id")
        current_address = moscow_warehouse.get("address", moscow_warehouse.get("location"))
        
        # 5. Проверка, нужно ли обновление
        if current_address == CORRECT_ADDRESS:
            print(f"✅ АДРЕС УЖЕ ПРАВИЛЬНЫЙ: '{current_address}'")
            self.log_result(
                "Проверка необходимости обновления",
                True,
                f"Адрес склада уже соответствует правильному: '{CORRECT_ADDRESS}'"
            )
        else:
            print(f"🔄 ТРЕБУЕТСЯ ОБНОВЛЕНИЕ: '{current_address}' → '{CORRECT_ADDRESS}'")
            
            # 6. Обновление адреса склада
            if not self.update_warehouse_address(warehouse_id):
                print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось обновить адрес склада")
                return False
            
            # 7. Проверка обновления
            if not self.verify_address_update(warehouse_id):
                print("❌ КРИТИЧЕСКАЯ ОШИБКА: Адрес не был обновлен правильно")
                return False
        
        # 8. Финальная проверка всех адресов
        print("📋 ФИНАЛЬНАЯ ПРОВЕРКА АДРЕСОВ:")
        final_warehouses = self.get_current_warehouses()
        if final_warehouses:
            is_correct_after, details_after = self.check_address_correctness(final_warehouses)
            
            if is_correct_after:
                print("🎉 ВСЕ АДРЕСА ПРАВИЛЬНЫЕ!")
            else:
                print("⚠️ НАЙДЕНЫ ПРОБЛЕМЫ С АДРЕСАМИ")
        
        return True
    
    def print_summary(self):
        """Вывести итоговый отчет"""
        print("\n" + "=" * 80)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - successful_tests
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Всего тестов: {total_tests}")
        print(f"Успешных: {successful_tests}")
        print(f"Неудачных: {failed_tests}")
        print(f"Процент успеха: {success_rate:.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ НЕУДАЧНЫЕ ТЕСТЫ:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['details']}")
            print()
        
        if successful_tests == total_tests:
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            print(f"✅ АДРЕС СКЛАДА ИСПРАВЛЕН НА ПРАВИЛЬНЫЙ: '{CORRECT_ADDRESS}'")
        else:
            print("⚠️ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
        
        print("=" * 80)

def main():
    """Основная функция"""
    tester = WarehouseAddressTester()
    
    try:
        success = tester.run_comprehensive_test()
        tester.print_summary()
        
        if success:
            print("\n✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО")
            sys.exit(0)
        else:
            print("\n❌ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ ТЕСТИРОВАНИЕ ПРЕРВАНО ПОЛЬЗОВАТЕЛЕМ")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
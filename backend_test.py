#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Новые API эндпоинты для управления городами складов в TAJLINE.TJ

КОНТЕКСТ: Добавлены новые эндпоинты для управления списком городов доставки для каждого склада.
Необходимо протестировать все 4 новых эндпоинта.

НОВЫЕ ЭНДПОИНТЫ ДЛЯ ТЕСТИРОВАНИЯ:
1. GET /api/warehouses/{warehouse_id}/cities - получить список городов склада
2. POST /api/warehouses/{warehouse_id}/cities - добавить один город к складу
3. POST /api/warehouses/{warehouse_id}/cities/bulk - массовое добавление городов
4. DELETE /api/warehouses/{warehouse_id}/cities - удалить город из склада
"""

import requests
import json
import os
from datetime import datetime

# Получаем URL backend из переменных окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cargo-tracker-31.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class WarehouseCityTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_warehouse_id = None
        self.test_warehouse_name = None
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: str):
        """Логирование результатов тестирования"""
        status = "✅ УСПЕХ" if success else "❌ ОШИБКА"
        result = f"{status} - {test_name}: {details}"
        self.test_results.append(result)
        print(result)
        
    def authenticate_admin(self):
        """Авторизация администратора для доступа к эндпоинтам"""
        print("\n🔐 ЭТАП 1: Авторизация администратора")
        
        # Учетные данные администратора
        admin_credentials = {
            "phone": "+79999888777",
            "password": "admin123"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json=admin_credentials)
            
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
                    f"Успешная авторизация '{user_info.get('full_name')}' (роль: {user_info.get('role')})"
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
            self.log_result("Авторизация администратора", False, f"Ошибка: {str(e)}")
            return False
    
    def get_warehouse_for_testing(self):
        """Получить список складов и выбрать один для тестирования"""
        print("\n🏢 ЭТАП 2: Получение списка складов")
        
        try:
            response = self.session.get(f"{API_BASE}/warehouses")
            
            if response.status_code == 200:
                warehouses = response.json()
                
                if warehouses:
                    # Выбираем первый склад для тестирования
                    test_warehouse = warehouses[0]
                    self.test_warehouse_id = test_warehouse.get("id")
                    self.test_warehouse_name = test_warehouse.get("name")
                    
                    self.log_result(
                        "Получение списка складов",
                        True,
                        f"Найдено {len(warehouses)} складов. Выбран для тестирования: '{self.test_warehouse_name}' (ID: {self.test_warehouse_id})"
                    )
                    return True
                else:
                    self.log_result("Получение списка складов", False, "Список складов пуст")
                    return False
            else:
                self.log_result(
                    "Получение списка складов",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Получение списка складов", False, f"Ошибка: {str(e)}")
            return False
    
    def test_get_warehouse_cities_initial(self):
        """Тест GET /api/warehouses/{warehouse_id}/cities (должен возвращать пустой список изначально)"""
        print("\n📋 ЭТАП 3: Тестирование GET cities (начальное состояние)")
        
        try:
            response = self.session.get(f"{API_BASE}/warehouses/{self.test_warehouse_id}/cities")
            
            if response.status_code == 200:
                data = response.json()
                cities = data.get("cities", [])
                cities_count = data.get("cities_count", 0)
                
                self.log_result(
                    "GET warehouse cities (начальное)",
                    True,
                    f"Склад '{data.get('warehouse_name')}' имеет {cities_count} городов: {cities}"
                )
                return True
            else:
                self.log_result(
                    "GET warehouse cities (начальное)",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("GET warehouse cities (начальное)", False, f"Ошибка: {str(e)}")
            return False
    
    def test_add_single_city(self):
        """Тест POST /api/warehouses/{warehouse_id}/cities - добавить тестовый город "Душанбе" """
        print("\n➕ ЭТАП 4: Тестирование POST single city - добавление 'Душанбе'")
        
        city_data = {
            "city_name": "Душанбе"
        }
        
        try:
            response = self.session.post(
                f"{API_BASE}/warehouses/{self.test_warehouse_id}/cities",
                json=city_data
            )
            
            if response.status_code == 200:
                data = response.json()
                
                self.log_result(
                    "POST single city (Душанбе)",
                    True,
                    f"{data.get('message')}. Всего городов: {data.get('total_cities')}"
                )
                return True
            else:
                self.log_result(
                    "POST single city (Душанбе)",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("POST single city (Душанбе)", False, f"Ошибка: {str(e)}")
            return False
    
    def test_add_bulk_cities(self):
        """Тест POST /api/warehouses/{warehouse_id}/cities/bulk - массово добавить ["Худжанд", "Куляб", "Курган-Тюбе"]"""
        print("\n📦 ЭТАП 5: Тестирование POST bulk cities - массовое добавление")
        
        cities_data = {
            "city_names": ["Худжанд", "Куляб", "Курган-Тюбе"]
        }
        
        try:
            response = self.session.post(
                f"{API_BASE}/warehouses/{self.test_warehouse_id}/cities/bulk",
                json=cities_data
            )
            
            if response.status_code == 200:
                data = response.json()
                
                self.log_result(
                    "POST bulk cities",
                    True,
                    f"{data.get('message')}. Добавлено: {data.get('added_count')} городов {data.get('added_cities')}. Пропущено: {data.get('skipped_count')} городов {data.get('skipped_cities')}. Всего: {data.get('total_cities')}"
                )
                return True
            else:
                self.log_result(
                    "POST bulk cities",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("POST bulk cities", False, f"Ошибка: {str(e)}")
            return False
    
    def test_get_warehouse_cities_after_additions(self):
        """Тест GET /api/warehouses/{warehouse_id}/cities снова - должен показать все добавленные города"""
        print("\n📋 ЭТАП 6: Тестирование GET cities (после добавлений)")
        
        try:
            response = self.session.get(f"{API_BASE}/warehouses/{self.test_warehouse_id}/cities")
            
            if response.status_code == 200:
                data = response.json()
                cities = data.get("cities", [])
                cities_count = data.get("cities_count", 0)
                
                expected_cities = ["Душанбе", "Худжанд", "Куляб", "Курган-Тюбе"]
                all_cities_present = all(city in cities for city in expected_cities)
                
                self.log_result(
                    "GET warehouse cities (после добавлений)",
                    all_cities_present,
                    f"Склад '{data.get('warehouse_name')}' имеет {cities_count} городов: {cities}. Все ожидаемые города присутствуют: {all_cities_present}"
                )
                return all_cities_present
            else:
                self.log_result(
                    "GET warehouse cities (после добавлений)",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("GET warehouse cities (после добавлений)", False, f"Ошибка: {str(e)}")
            return False
    
    def test_delete_city(self):
        """Тест DELETE /api/warehouses/{warehouse_id}/cities - удалить один город "Куляб" """
        print("\n🗑️ ЭТАП 7: Тестирование DELETE city - удаление 'Куляб'")
        
        city_data = {
            "city_name": "Куляб"
        }
        
        try:
            response = self.session.delete(
                f"{API_BASE}/warehouses/{self.test_warehouse_id}/cities",
                json=city_data
            )
            
            if response.status_code == 200:
                data = response.json()
                
                self.log_result(
                    "DELETE city (Куляб)",
                    True,
                    f"{data.get('message')}. Всего городов: {data.get('total_cities')}"
                )
                return True
            else:
                self.log_result(
                    "DELETE city (Куляб)",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("DELETE city (Куляб)", False, f"Ошибка: {str(e)}")
            return False
    
    def test_get_warehouse_cities_final(self):
        """Финальная проверка GET /api/warehouses/{warehouse_id}/cities - должен показать города без "Куляб" """
        print("\n🏁 ЭТАП 8: Финальная проверка GET cities (без 'Куляб')")
        
        try:
            response = self.session.get(f"{API_BASE}/warehouses/{self.test_warehouse_id}/cities")
            
            if response.status_code == 200:
                data = response.json()
                cities = data.get("cities", [])
                cities_count = data.get("cities_count", 0)
                
                expected_cities = ["Душанбе", "Худжанд", "Курган-Тюбе"]
                kulyab_absent = "Куляб" not in cities
                expected_cities_present = all(city in cities for city in expected_cities)
                
                success = kulyab_absent and expected_cities_present
                
                self.log_result(
                    "GET warehouse cities (финальная проверка)",
                    success,
                    f"Склад '{data.get('warehouse_name')}' имеет {cities_count} городов: {cities}. 'Куляб' отсутствует: {kulyab_absent}. Остальные города присутствуют: {expected_cities_present}"
                )
                return success
            else:
                self.log_result(
                    "GET warehouse cities (финальная проверка)",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("GET warehouse cities (финальная проверка)", False, f"Ошибка: {str(e)}")
            return False
    
    def test_security_validations(self):
        """Проверки безопасности - только администраторы и операторы складов должны иметь доступ"""
        print("\n🔒 ЭТАП 9: Проверки безопасности")
        
        # Тест без авторизации
        temp_session = requests.Session()
        
        try:
            response = temp_session.get(f"{API_BASE}/warehouses/{self.test_warehouse_id}/cities")
            
            if response.status_code == 403:
                self.log_result(
                    "Проверка безопасности (без авторизации)",
                    True,
                    "Доступ корректно заблокирован для неавторизованных пользователей"
                )
                return True
            else:
                self.log_result(
                    "Проверка безопасности (без авторизации)",
                    False,
                    f"Ожидался HTTP 403, получен HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_result("Проверка безопасности (без авторизации)", False, f"Ошибка: {str(e)}")
            return False
    
    def test_data_validation(self):
        """Валидация данных (пустые города, дубликаты и т.д.)"""
        print("\n✅ ЭТАП 10: Валидация данных")
        
        # Тест добавления пустого города
        try:
            empty_city_data = {"city_name": ""}
            response = self.session.post(
                f"{API_BASE}/warehouses/{self.test_warehouse_id}/cities",
                json=empty_city_data
            )
            
            if response.status_code == 422:  # Validation error
                self.log_result(
                    "Валидация данных (пустой город)",
                    True,
                    "Пустой город корректно отклонен"
                )
            else:
                self.log_result(
                    "Валидация данных (пустой город)",
                    False,
                    f"Ожидался HTTP 422, получен HTTP {response.status_code}"
                )
            
            # Тест добавления дубликата
            duplicate_city_data = {"city_name": "Душанбе"}  # Уже добавлен ранее
            response = self.session.post(
                f"{API_BASE}/warehouses/{self.test_warehouse_id}/cities",
                json=duplicate_city_data
            )
            
            if response.status_code == 400:  # Bad request for duplicate
                self.log_result(
                    "Валидация данных (дубликат города)",
                    True,
                    "Дубликат города корректно отклонен"
                )
                return True
            else:
                self.log_result(
                    "Валидация данных (дубликат города)",
                    False,
                    f"Ожидался HTTP 400, получен HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Валидация данных", False, f"Ошибка: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Новые API эндпоинты для управления городами складов в TAJLINE.TJ")
        print("=" * 100)
        
        test_steps = [
            self.authenticate_admin,
            self.get_warehouse_for_testing,
            self.test_get_warehouse_cities_initial,
            self.test_add_single_city,
            self.test_add_bulk_cities,
            self.test_get_warehouse_cities_after_additions,
            self.test_delete_city,
            self.test_get_warehouse_cities_final,
            self.test_security_validations,
            self.test_data_validation
        ]
        
        passed_tests = 0
        total_tests = len(test_steps)
        
        for test_step in test_steps:
            try:
                if test_step():
                    passed_tests += 1
            except Exception as e:
                print(f"❌ Критическая ошибка в тесте {test_step.__name__}: {str(e)}")
        
        # Итоговый отчет
        print("\n" + "=" * 100)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 100)
        
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"✅ Пройдено тестов: {passed_tests}/{total_tests}")
        print(f"📈 Процент успеха: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        else:
            print("⚠️ ОБНАРУЖЕНЫ КРИТИЧЕСКИЕ ПРОБЛЕМЫ!")
        
        print("\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        for result in self.test_results:
            print(result)
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = WarehouseCityTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 ВСЕ НОВЫЕ ЭНДПОИНТЫ ДЛЯ УПРАВЛЕНИЯ ГОРОДАМИ СКЛАДОВ РАБОТАЮТ КОРРЕКТНО!")
    else:
        print("\n❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ В НОВЫХ ЭНДПОИНТАХ!")
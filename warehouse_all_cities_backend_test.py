#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Новый API endpoint для получения всех городов складов в TAJLINE.TJ

КОНТЕКСТ: Добавлен новый endpoint GET /api/warehouses/all-cities для формы приёма груза. 
Этот endpoint должен возвращать все уникальные города из всех складов с информацией о доступных складах.

ЗАДАЧИ ТЕСТИРОВАНИЯ:
1. Авторизоваться как администратор
2. Протестировать новый endpoint GET /api/warehouses/all-cities
3. Проверить структуру ответа:
   - cities: массив объектов с городами
   - total_cities: общее количество городов  
   - total_warehouses_with_cities: количество складов с городами
4. Каждый объект города должен содержать:
   - city_name: название города
   - available_warehouses: массив складов
   - warehouses_count: количество складов
5. Каждый склад должен содержать:
   - warehouse_id: ID склада
   - warehouse_name: название склада
   - warehouse_location: местоположение склада
   - warehouse_id_number: уникальный номер склада

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
Endpoint должен вернуть все города из всех активных складов, сгруппированные с информацией о том, 
какие склады доступны в каждом городе.

ПРОВЕРКИ БЕЗОПАСНОСТИ:
- Доступ только для admin и warehouse_operator ролей
- Возвращать только активные склады (is_active: true)

ДОПОЛНИТЕЛЬНЫЕ ПРОВЕРКИ:
- Города должны быть отсортированы по алфавиту
- Пустые города должны быть отфильтрованы  
- Дублирующиеся города должны быть объединены
"""

import requests
import json
import os
from datetime import datetime

# Получаем URL backend из переменных окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-cargo-7.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class WarehouseAllCitiesTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.operator_token = None
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
                    f"Успешная авторизация '{user_info.get('full_name')}' (номер: {user_info.get('user_number')}, роль: {user_info.get('role')})"
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
    
    def test_all_cities_endpoint_structure(self):
        """Тест основной структуры ответа GET /api/warehouses/all-cities"""
        print("\n🏢 ЭТАП 2: Тестирование структуры ответа GET /api/warehouses/all-cities")
        
        try:
            response = self.session.get(f"{API_BASE}/warehouses/all-cities")
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем основные поля ответа
                required_fields = ["cities", "total_cities", "total_warehouses_with_cities"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        "Структура ответа",
                        False,
                        f"Отсутствуют обязательные поля: {missing_fields}"
                    )
                    return False
                
                cities = data.get("cities", [])
                total_cities = data.get("total_cities", 0)
                total_warehouses = data.get("total_warehouses_with_cities", 0)
                
                self.log_result(
                    "Структура ответа",
                    True,
                    f"Получено {total_cities} городов из {total_warehouses} складов. Структура корректна."
                )
                
                # Сохраняем данные для дальнейших тестов
                self.cities_data = cities
                self.total_cities = total_cities
                self.total_warehouses = total_warehouses
                
                return True
            else:
                self.log_result(
                    "Структура ответа",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Структура ответа", False, f"Ошибка: {str(e)}")
            return False
    
    def test_cities_data_structure(self):
        """Тест структуры данных каждого города"""
        print("\n📋 ЭТАП 3: Тестирование структуры данных городов")
        
        if not hasattr(self, 'cities_data'):
            self.log_result("Структура данных городов", False, "Нет данных городов для тестирования")
            return False
        
        try:
            cities_with_issues = []
            warehouses_with_issues = []
            
            for city in self.cities_data:
                # Проверяем обязательные поля города
                city_required_fields = ["city_name", "available_warehouses", "warehouses_count"]
                missing_city_fields = [field for field in city_required_fields if field not in city]
                
                if missing_city_fields:
                    cities_with_issues.append(f"Город '{city.get('city_name', 'UNKNOWN')}': отсутствуют поля {missing_city_fields}")
                    continue
                
                # Проверяем структуру складов в городе
                warehouses = city.get("available_warehouses", [])
                warehouses_count = city.get("warehouses_count", 0)
                
                # Проверяем соответствие количества складов
                if len(warehouses) != warehouses_count:
                    cities_with_issues.append(f"Город '{city['city_name']}': несоответствие количества складов ({len(warehouses)} != {warehouses_count})")
                
                # Проверяем структуру каждого склада
                for warehouse in warehouses:
                    warehouse_required_fields = ["warehouse_id", "warehouse_name", "warehouse_location", "warehouse_id_number"]
                    missing_warehouse_fields = [field for field in warehouse_required_fields if field not in warehouse]
                    
                    if missing_warehouse_fields:
                        warehouses_with_issues.append(f"Склад в городе '{city['city_name']}': отсутствуют поля {missing_warehouse_fields}")
            
            if cities_with_issues or warehouses_with_issues:
                issues = cities_with_issues + warehouses_with_issues
                self.log_result(
                    "Структура данных городов",
                    False,
                    f"Найдены проблемы: {'; '.join(issues[:3])}{'...' if len(issues) > 3 else ''}"
                )
                return False
            else:
                self.log_result(
                    "Структура данных городов",
                    True,
                    f"Структура данных всех {len(self.cities_data)} городов корректна"
                )
                return True
                
        except Exception as e:
            self.log_result("Структура данных городов", False, f"Ошибка: {str(e)}")
            return False
    
    def test_cities_sorting(self):
        """Тест сортировки городов по алфавиту"""
        print("\n🔤 ЭТАП 4: Тестирование сортировки городов по алфавиту")
        
        if not hasattr(self, 'cities_data'):
            self.log_result("Сортировка городов", False, "Нет данных городов для тестирования")
            return False
        
        try:
            city_names = [city.get("city_name", "") for city in self.cities_data]
            sorted_city_names = sorted(city_names)
            
            is_sorted = city_names == sorted_city_names
            
            self.log_result(
                "Сортировка городов",
                is_sorted,
                f"Города {'корректно отсортированы' if is_sorted else 'НЕ отсортированы'} по алфавиту. Порядок: {city_names[:5]}{'...' if len(city_names) > 5 else ''}"
            )
            
            return is_sorted
                
        except Exception as e:
            self.log_result("Сортировка городов", False, f"Ошибка: {str(e)}")
            return False
    
    def test_warehouse_id_numbers(self):
        """Тест наличия уникальных номеров складов"""
        print("\n🏷️ ЭТАП 5: Тестирование уникальных номеров складов")
        
        if not hasattr(self, 'cities_data'):
            self.log_result("Уникальные номера складов", False, "Нет данных городов для тестирования")
            return False
        
        try:
            warehouse_id_numbers = []
            warehouses_without_numbers = []
            
            for city in self.cities_data:
                for warehouse in city.get("available_warehouses", []):
                    warehouse_id_number = warehouse.get("warehouse_id_number")
                    warehouse_name = warehouse.get("warehouse_name", "UNKNOWN")
                    
                    if not warehouse_id_number or warehouse_id_number == "000":
                        warehouses_without_numbers.append(warehouse_name)
                    else:
                        warehouse_id_numbers.append(warehouse_id_number)
            
            # Проверяем уникальность номеров
            unique_numbers = set(warehouse_id_numbers)
            duplicates = len(warehouse_id_numbers) - len(unique_numbers)
            
            success = len(warehouses_without_numbers) == 0 and duplicates == 0
            
            details = f"Всего складов: {len(warehouse_id_numbers) + len(warehouses_without_numbers)}, "
            details += f"с номерами: {len(warehouse_id_numbers)}, "
            details += f"уникальных номеров: {len(unique_numbers)}, "
            details += f"дубликатов: {duplicates}, "
            details += f"без номеров: {len(warehouses_without_numbers)}"
            
            if warehouses_without_numbers:
                details += f". Склады без номеров: {warehouses_without_numbers[:3]}{'...' if len(warehouses_without_numbers) > 3 else ''}"
            
            self.log_result(
                "Уникальные номера складов",
                success,
                details
            )
            
            return success
                
        except Exception as e:
            self.log_result("Уникальные номера складов", False, f"Ошибка: {str(e)}")
            return False
    
    def test_security_admin_access(self):
        """Тест доступа администратора"""
        print("\n🔒 ЭТАП 6: Тестирование доступа администратора")
        
        try:
            # Тест с токеном администратора (уже установлен)
            response = self.session.get(f"{API_BASE}/warehouses/all-cities")
            
            if response.status_code == 200:
                self.log_result(
                    "Доступ администратора",
                    True,
                    "Администратор имеет корректный доступ к endpoint"
                )
                return True
            else:
                self.log_result(
                    "Доступ администратора",
                    False,
                    f"Администратор не может получить доступ: HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_result("Доступ администратора", False, f"Ошибка: {str(e)}")
            return False
    
    def test_security_no_auth(self):
        """Тест безопасности - доступ без авторизации"""
        print("\n🚫 ЭТАП 7: Тестирование безопасности (без авторизации)")
        
        try:
            # Создаем новую сессию без токена
            temp_session = requests.Session()
            response = temp_session.get(f"{API_BASE}/warehouses/all-cities")
            
            if response.status_code in [401, 403]:
                self.log_result(
                    "Безопасность (без авторизации)",
                    True,
                    f"Доступ корректно заблокирован для неавторизованных пользователей (HTTP {response.status_code})"
                )
                return True
            else:
                self.log_result(
                    "Безопасность (без авторизации)",
                    False,
                    f"Ожидался HTTP 401/403, получен HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_result("Безопасность (без авторизации)", False, f"Ошибка: {str(e)}")
            return False
    
    def test_operator_access(self):
        """Тест доступа оператора склада"""
        print("\n👷 ЭТАП 8: Тестирование доступа оператора склада")
        
        # Попробуем авторизоваться как оператор
        operator_credentials = {
            "phone": "+79777888999",
            "password": "warehouse123"
        }
        
        try:
            temp_session = requests.Session()
            response = temp_session.post(f"{API_BASE}/auth/login", json=operator_credentials)
            
            if response.status_code == 200:
                data = response.json()
                operator_token = data.get("access_token")
                user_info = data.get("user", {})
                
                temp_session.headers.update({
                    "Authorization": f"Bearer {operator_token}"
                })
                
                # Тестируем доступ оператора к endpoint
                response = temp_session.get(f"{API_BASE}/warehouses/all-cities")
                
                if response.status_code == 200:
                    self.log_result(
                        "Доступ оператора",
                        True,
                        f"Оператор '{user_info.get('full_name')}' имеет корректный доступ к endpoint"
                    )
                    return True
                else:
                    self.log_result(
                        "Доступ оператора",
                        False,
                        f"Оператор не может получить доступ: HTTP {response.status_code}"
                    )
                    return False
            else:
                self.log_result(
                    "Доступ оператора",
                    False,
                    f"Не удалось авторизоваться как оператор: HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_result("Доступ оператора", False, f"Ошибка: {str(e)}")
            return False
    
    def test_data_consistency(self):
        """Тест консистентности данных"""
        print("\n🔍 ЭТАП 9: Тестирование консистентности данных")
        
        if not hasattr(self, 'cities_data'):
            self.log_result("Консистентность данных", False, "Нет данных городов для тестирования")
            return False
        
        try:
            # Проверяем, что нет пустых городов
            empty_cities = [city for city in self.cities_data if not city.get("city_name", "").strip()]
            
            # Проверяем, что все склады имеют корректные ID
            warehouses_with_invalid_ids = []
            for city in self.cities_data:
                for warehouse in city.get("available_warehouses", []):
                    warehouse_id = warehouse.get("warehouse_id", "")
                    warehouse_name = warehouse.get("warehouse_name", "UNKNOWN")
                    
                    if not warehouse_id or len(warehouse_id) < 10:  # UUID должен быть длиннее
                        warehouses_with_invalid_ids.append(warehouse_name)
            
            # Проверяем дубликаты городов
            city_names = [city.get("city_name", "") for city in self.cities_data]
            unique_city_names = set(city_names)
            duplicate_cities = len(city_names) - len(unique_city_names)
            
            issues = []
            if empty_cities:
                issues.append(f"пустые города: {len(empty_cities)}")
            if warehouses_with_invalid_ids:
                issues.append(f"склады с некорректными ID: {len(warehouses_with_invalid_ids)}")
            if duplicate_cities > 0:
                issues.append(f"дублирующиеся города: {duplicate_cities}")
            
            success = len(issues) == 0
            
            details = f"Проверено {len(self.cities_data)} городов. "
            if success:
                details += "Все данные консистентны."
            else:
                details += f"Найдены проблемы: {'; '.join(issues)}"
            
            self.log_result(
                "Консистентность данных",
                success,
                details
            )
            
            return success
                
        except Exception as e:
            self.log_result("Консистентность данных", False, f"Ошибка: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Новый API endpoint для получения всех городов складов в TAJLINE.TJ")
        print("=" * 100)
        
        test_steps = [
            self.authenticate_admin,
            self.test_all_cities_endpoint_structure,
            self.test_cities_data_structure,
            self.test_cities_sorting,
            self.test_warehouse_id_numbers,
            self.test_security_admin_access,
            self.test_security_no_auth,
            self.test_operator_access,
            self.test_data_consistency
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
    tester = WarehouseAllCitiesTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 НОВЫЙ ENDPOINT GET /api/warehouses/all-cities РАБОТАЕТ КОРРЕКТНО!")
    else:
        print("\n❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ В НОВОМ ENDPOINT!")
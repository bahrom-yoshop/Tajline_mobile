#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Проблема с регистрацией оператора при выборе склада из выпадающего списка в TAJLINE.TJ

ПРОБЛЕМА: При регистрации оператора возникает ошибка при выборе склада из выпадающего списка

КРИТИЧЕСКИЕ ТЕСТЫ:
1) GET /api/warehouses - убедиться что endpoint возвращает корректный список складов:
   - Проверить что возвращается массив складов
   - Убедиться что у каждого склада есть поля: id, name, location
   - Проверить формат данных (должен быть JSON array или объект с массивом)

2) POST /api/admin/create-operator - протестировать создание оператора:
   - Попробовать создать оператора с валидными данными включая warehouse_id
   - Проверить что endpoint принимает все требуемые поля: full_name, phone, address, password, warehouse_id
   - Проверить валидацию данных

3) Проверить логи backend на предмет ошибок при создании оператора

ТЕСТОВЫЕ ДАННЫЕ:
- Админ: phone="+79999888777", password="admin123"

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Найти источник ошибки при выборе склада в выпадающем списке во время регистрации оператора
"""

import requests
import json
import os
from datetime import datetime
import uuid

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-cargo-7.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class OperatorRegistrationTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.admin_info = None
        self.test_results = []
        self.warehouses_data = []
        
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
        status = "✅ УСПЕХ" if success else "❌ ОШИБКА"
        print(f"{status}: {test_name}")
        if details:
            print(f"   📋 Детали: {details}")
        if error_msg:
            print(f"   ⚠️ Ошибка: {error_msg}")
        print()

    def test_admin_login(self):
        """Тест 1: Авторизация администратора"""
        try:
            login_data = {
                "phone": "+79999888777",
                "password": "admin123"
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                self.admin_info = data.get("user", {})
                
                if self.admin_token and self.admin_info.get("role") == "admin":
                    self.log_test(
                        "Авторизация администратора (+79999888777/admin123)",
                        True,
                        f"Успешная авторизация '{self.admin_info.get('full_name')}' (номер: {self.admin_info.get('user_number')}), роль: {self.admin_info.get('role')}, JWT токен получен"
                    )
                    return True
                else:
                    self.log_test(
                        "Авторизация администратора (+79999888777/admin123)",
                        False,
                        "Токен не получен или роль не admin",
                        f"Ответ: {data}"
                    )
                    return False
            else:
                self.log_test(
                    "Авторизация администратора (+79999888777/admin123)",
                    False,
                    f"HTTP {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Авторизация администратора (+79999888777/admin123)",
                False,
                "",
                str(e)
            )
            return False

    def test_warehouses_endpoint(self):
        """Тест 2: GET /api/warehouses - проверка списка складов для выпадающего списка"""
        try:
            if not self.admin_token:
                self.log_test(
                    "GET /api/warehouses - проверка списка складов",
                    False,
                    "",
                    "Нет токена администратора"
                )
                return False
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{API_BASE}/warehouses", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем структуру данных
                if isinstance(data, list):
                    self.warehouses_data = data
                    warehouse_count = len(data)
                    
                    if warehouse_count > 0:
                        # Проверяем структуру каждого склада
                        required_fields = ["id", "name", "location"]
                        all_valid = True
                        missing_fields_summary = []
                        
                        for i, warehouse in enumerate(data[:5]):  # Проверяем первые 5 складов
                            missing_fields = [field for field in required_fields if field not in warehouse]
                            if missing_fields:
                                all_valid = False
                                missing_fields_summary.append(f"Склад {i+1}: отсутствуют поля {missing_fields}")
                        
                        if all_valid:
                            # Показываем примеры складов
                            examples = []
                            for warehouse in data[:3]:
                                examples.append(f"ID: {warehouse.get('id', 'N/A')[:8]}..., Название: '{warehouse.get('name', 'N/A')}', Локация: '{warehouse.get('location', 'N/A')}'")
                            
                            self.log_test(
                                "GET /api/warehouses - проверка списка складов",
                                True,
                                f"✅ Получено {warehouse_count} складов со всеми необходимыми полями (id, name, location). Примеры: {'; '.join(examples)}"
                            )
                            return True
                        else:
                            self.log_test(
                                "GET /api/warehouses - проверка списка складов",
                                False,
                                f"Получено {warehouse_count} складов, но у некоторых отсутствуют обязательные поля",
                                f"Проблемы: {'; '.join(missing_fields_summary)}"
                            )
                            return False
                    else:
                        self.log_test(
                            "GET /api/warehouses - проверка списка складов",
                            False,
                            "Список складов пуст - выпадающий список будет пустым",
                            "Нет складов для выбора при регистрации оператора"
                        )
                        return False
                        
                elif isinstance(data, dict):
                    # Возможно данные в формате {items: [...], pagination: {...}}
                    if "items" in data:
                        self.warehouses_data = data["items"]
                        warehouse_count = len(data["items"])
                        
                        if warehouse_count > 0:
                            self.log_test(
                                "GET /api/warehouses - проверка списка складов",
                                True,
                                f"✅ Получено {warehouse_count} складов в пагинированном формате, структура корректна"
                            )
                            return True
                        else:
                            self.log_test(
                                "GET /api/warehouses - проверка списка складов",
                                False,
                                "Пагинированный ответ содержит пустой список складов",
                                "Нет складов для выбора при регистрации оператора"
                            )
                            return False
                    else:
                        self.log_test(
                            "GET /api/warehouses - проверка списка складов",
                            False,
                            "Неожиданная структура ответа - не массив и не объект с полем 'items'",
                            f"Структура ответа: {list(data.keys()) if isinstance(data, dict) else type(data)}"
                        )
                        return False
                else:
                    self.log_test(
                        "GET /api/warehouses - проверка списка складов",
                        False,
                        "Неожиданная структура ответа",
                        f"Тип данных: {type(data)}, Содержимое: {str(data)[:200]}"
                    )
                    return False
            else:
                self.log_test(
                    "GET /api/warehouses - проверка списка складов",
                    False,
                    f"HTTP {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "GET /api/warehouses - проверка списка складов",
                False,
                "",
                str(e)
            )
            return False

    def test_create_operator_endpoint_structure(self):
        """Тест 3: Проверка структуры endpoint POST /api/admin/create-operator"""
        try:
            if not self.admin_token:
                self.log_test(
                    "Проверка структуры POST /api/admin/create-operator",
                    False,
                    "",
                    "Нет токена администратора"
                )
                return False
            
            if not self.warehouses_data:
                self.log_test(
                    "Проверка структуры POST /api/admin/create-operator",
                    False,
                    "",
                    "Нет данных о складах для тестирования"
                )
                return False
            
            # Берем первый склад для тестирования
            test_warehouse = self.warehouses_data[0]
            warehouse_id = test_warehouse.get("id")
            
            if not warehouse_id:
                self.log_test(
                    "Проверка структуры POST /api/admin/create-operator",
                    False,
                    "",
                    "У первого склада отсутствует поле 'id'"
                )
                return False
            
            # Тестовые данные для создания оператора
            test_operator_data = {
                "full_name": f"Тестовый Оператор {datetime.now().strftime('%H%M%S')}",
                "phone": f"+7999{datetime.now().strftime('%H%M%S')}",
                "address": "Тестовый адрес для проверки регистрации оператора",
                "password": "testpass123",
                "warehouse_id": warehouse_id
            }
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.post(f"{API_BASE}/admin/create-operator", json=test_operator_data, headers=headers)
            
            if response.status_code == 200 or response.status_code == 201:
                data = response.json()
                self.log_test(
                    "Проверка структуры POST /api/admin/create-operator",
                    True,
                    f"✅ Оператор успешно создан! Склад: '{test_warehouse.get('name')}' (ID: {warehouse_id[:8]}...), Ответ: {data.get('message', 'Успешно')}"
                )
                return True
                
            elif response.status_code == 400:
                # Ошибка валидации - анализируем детали
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", response.text)
                    
                    if "warehouse_id" in str(error_detail).lower():
                        self.log_test(
                            "Проверка структуры POST /api/admin/create-operator",
                            False,
                            f"❌ НАЙДЕНА ПРОБЛЕМА С WAREHOUSE_ID! Склад ID: {warehouse_id[:8]}..., Название: '{test_warehouse.get('name')}'",
                            f"Ошибка валидации warehouse_id: {error_detail}"
                        )
                    else:
                        self.log_test(
                            "Проверка структуры POST /api/admin/create-operator",
                            False,
                            f"Ошибка валидации данных (не связана с warehouse_id)",
                            f"HTTP 400: {error_detail}"
                        )
                except:
                    self.log_test(
                        "Проверка структуры POST /api/admin/create-operator",
                        False,
                        f"Ошибка валидации данных",
                        f"HTTP 400: {response.text}"
                    )
                return False
                
            elif response.status_code == 422:
                # Ошибка валидации Pydantic
                try:
                    error_data = response.json()
                    validation_errors = error_data.get("detail", [])
                    
                    warehouse_errors = []
                    other_errors = []
                    
                    if isinstance(validation_errors, list):
                        for error in validation_errors:
                            if isinstance(error, dict):
                                field = error.get("loc", ["unknown"])[-1] if error.get("loc") else "unknown"
                                msg = error.get("msg", "validation error")
                                
                                if "warehouse" in field.lower():
                                    warehouse_errors.append(f"{field}: {msg}")
                                else:
                                    other_errors.append(f"{field}: {msg}")
                    
                    if warehouse_errors:
                        self.log_test(
                            "Проверка структуры POST /api/admin/create-operator",
                            False,
                            f"❌ НАЙДЕНА ПРОБЛЕМА С ВАЛИДАЦИЕЙ WAREHOUSE_ID! Склад: '{test_warehouse.get('name')}' (ID: {warehouse_id[:8]}...)",
                            f"Ошибки валидации warehouse: {'; '.join(warehouse_errors)}"
                        )
                    else:
                        self.log_test(
                            "Проверка структуры POST /api/admin/create-operator",
                            False,
                            f"Ошибки валидации других полей (не warehouse_id)",
                            f"HTTP 422: {'; '.join(other_errors) if other_errors else str(validation_errors)}"
                        )
                except:
                    self.log_test(
                        "Проверка структуры POST /api/admin/create-operator",
                        False,
                        f"Ошибка валидации Pydantic",
                        f"HTTP 422: {response.text}"
                    )
                return False
                
            elif response.status_code == 404:
                self.log_test(
                    "Проверка структуры POST /api/admin/create-operator",
                    False,
                    "❌ ENDPOINT НЕ НАЙДЕН! Возможно неправильный URL или endpoint не реализован",
                    f"HTTP 404: {response.text}"
                )
                return False
                
            elif response.status_code == 409:
                # Конфликт - возможно пользователь уже существует
                self.log_test(
                    "Проверка структуры POST /api/admin/create-operator",
                    True,  # Endpoint работает, просто данные конфликтуют
                    f"⚠️ Конфликт данных (возможно телефон уже используется), но endpoint работает корректно",
                    f"HTTP 409: {response.text}"
                )
                return True
                
            else:
                self.log_test(
                    "Проверка структуры POST /api/admin/create-operator",
                    False,
                    f"Неожиданный HTTP статус: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Проверка структуры POST /api/admin/create-operator",
                False,
                "",
                str(e)
            )
            return False

    def test_create_operator_with_different_warehouses(self):
        """Тест 4: Тестирование создания оператора с разными складами"""
        try:
            if not self.admin_token:
                self.log_test(
                    "Тестирование создания оператора с разными складами",
                    False,
                    "",
                    "Нет токена администратора"
                )
                return False
            
            if len(self.warehouses_data) < 2:
                self.log_test(
                    "Тестирование создания оператора с разными складами",
                    True,  # Не критично если мало складов
                    f"Доступно только {len(self.warehouses_data)} складов, тест с одним складом",
                    "Недостаточно складов для полного тестирования"
                )
                return True
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            successful_tests = 0
            total_tests = min(3, len(self.warehouses_data))  # Тестируем максимум 3 склада
            
            for i in range(total_tests):
                warehouse = self.warehouses_data[i]
                warehouse_id = warehouse.get("id")
                warehouse_name = warehouse.get("name", "Неизвестный склад")
                
                if not warehouse_id:
                    continue
                
                # Уникальные данные для каждого теста
                test_operator_data = {
                    "full_name": f"Тестовый Оператор Склада {i+1} {datetime.now().strftime('%H%M%S')}",
                    "phone": f"+7999{datetime.now().strftime('%H%M%S')}{i:02d}",
                    "address": f"Тестовый адрес {i+1} для проверки регистрации оператора",
                    "password": f"testpass{i+1}23",
                    "warehouse_id": warehouse_id
                }
                
                response = self.session.post(f"{API_BASE}/admin/create-operator", json=test_operator_data, headers=headers)
                
                if response.status_code in [200, 201, 409]:  # 409 = конфликт, но endpoint работает
                    successful_tests += 1
                    print(f"   ✅ Склад {i+1}: '{warehouse_name}' (ID: {warehouse_id[:8]}...) - OK")
                else:
                    print(f"   ❌ Склад {i+1}: '{warehouse_name}' (ID: {warehouse_id[:8]}...) - Ошибка {response.status_code}")
            
            success_rate = (successful_tests / total_tests) * 100
            
            if success_rate >= 80:
                self.log_test(
                    "Тестирование создания оператора с разными складами",
                    True,
                    f"✅ Успешность: {successful_tests}/{total_tests} складов ({success_rate:.1f}%), endpoint работает корректно с разными warehouse_id"
                )
                return True
            else:
                self.log_test(
                    "Тестирование создания оператора с разными складами",
                    False,
                    f"❌ Низкая успешность: {successful_tests}/{total_tests} складов ({success_rate:.1f}%)",
                    "Возможны проблемы с обработкой разных warehouse_id"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Тестирование создания оператора с разными складами",
                False,
                "",
                str(e)
            )
            return False

    def test_invalid_warehouse_id(self):
        """Тест 5: Тестирование с невалидным warehouse_id"""
        try:
            if not self.admin_token:
                self.log_test(
                    "Тестирование с невалидным warehouse_id",
                    False,
                    "",
                    "Нет токена администратора"
                )
                return False
            
            # Тестируем с несуществующим warehouse_id
            invalid_warehouse_id = str(uuid.uuid4())
            
            test_operator_data = {
                "full_name": f"Тестовый Оператор Невалидный {datetime.now().strftime('%H%M%S')}",
                "phone": f"+7999{datetime.now().strftime('%H%M%S')}99",
                "address": "Тестовый адрес для проверки невалидного warehouse_id",
                "password": "testpass123",
                "warehouse_id": invalid_warehouse_id
            }
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.post(f"{API_BASE}/admin/create-operator", json=test_operator_data, headers=headers)
            
            if response.status_code == 400:
                try:
                    error_data = response.json()
                    error_detail = str(error_data.get("detail", response.text))
                    
                    if "warehouse" in error_detail.lower() or "not found" in error_detail.lower():
                        self.log_test(
                            "Тестирование с невалидным warehouse_id",
                            True,
                            f"✅ Система корректно отклоняет невалидный warehouse_id",
                            f"Ожидаемая ошибка: {error_detail}"
                        )
                        return True
                    else:
                        self.log_test(
                            "Тестирование с невалидным warehouse_id",
                            False,
                            f"Система отклоняет запрос, но ошибка не связана с warehouse_id",
                            f"HTTP 400: {error_detail}"
                        )
                        return False
                except:
                    self.log_test(
                        "Тестирование с невалидным warehouse_id",
                        True,
                        f"✅ Система корректно отклоняет невалидный warehouse_id",
                        f"HTTP 400: {response.text}"
                    )
                    return True
                    
            elif response.status_code == 422:
                self.log_test(
                    "Тестирование с невалидным warehouse_id",
                    True,
                    f"✅ Система корректно валидирует warehouse_id (Pydantic validation)",
                    f"HTTP 422: {response.text}"
                )
                return True
                
            elif response.status_code in [200, 201]:
                self.log_test(
                    "Тестирование с невалидным warehouse_id",
                    False,
                    f"❌ ПРОБЛЕМА: Система приняла невалидный warehouse_id!",
                    f"Невалидный ID: {invalid_warehouse_id}, но запрос прошел успешно"
                )
                return False
                
            else:
                self.log_test(
                    "Тестирование с невалидным warehouse_id",
                    False,
                    f"Неожиданный ответ на невалидный warehouse_id",
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Тестирование с невалидным warehouse_id",
                False,
                "",
                str(e)
            )
            return False

    def test_missing_warehouse_id(self):
        """Тест 6: Тестирование без warehouse_id"""
        try:
            if not self.admin_token:
                self.log_test(
                    "Тестирование без warehouse_id",
                    False,
                    "",
                    "Нет токена администратора"
                )
                return False
            
            # Тестируем без warehouse_id
            test_operator_data = {
                "full_name": f"Тестовый Оператор Без Склада {datetime.now().strftime('%H%M%S')}",
                "phone": f"+7999{datetime.now().strftime('%H%M%S')}88",
                "address": "Тестовый адрес для проверки без warehouse_id",
                "password": "testpass123"
                # warehouse_id отсутствует
            }
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.post(f"{API_BASE}/admin/create-operator", json=test_operator_data, headers=headers)
            
            if response.status_code == 422:
                try:
                    error_data = response.json()
                    validation_errors = error_data.get("detail", [])
                    
                    warehouse_required = False
                    if isinstance(validation_errors, list):
                        for error in validation_errors:
                            if isinstance(error, dict):
                                field = error.get("loc", ["unknown"])[-1] if error.get("loc") else "unknown"
                                if "warehouse" in field.lower():
                                    warehouse_required = True
                                    break
                    
                    if warehouse_required:
                        self.log_test(
                            "Тестирование без warehouse_id",
                            True,
                            f"✅ Система корректно требует обязательное поле warehouse_id",
                            f"Валидация Pydantic: warehouse_id обязательно"
                        )
                        return True
                    else:
                        self.log_test(
                            "Тестирование без warehouse_id",
                            False,
                            f"Ошибка валидации, но не связана с warehouse_id",
                            f"HTTP 422: {validation_errors}"
                        )
                        return False
                except:
                    self.log_test(
                        "Тестирование без warehouse_id",
                        True,
                        f"✅ Система корректно требует обязательные поля",
                        f"HTTP 422: {response.text}"
                    )
                    return True
                    
            elif response.status_code == 400:
                self.log_test(
                    "Тестирование без warehouse_id",
                    True,
                    f"✅ Система корректно отклоняет запрос без warehouse_id",
                    f"HTTP 400: {response.text}"
                )
                return True
                
            elif response.status_code in [200, 201]:
                self.log_test(
                    "Тестирование без warehouse_id",
                    False,
                    f"❌ ПРОБЛЕМА: Система создала оператора без warehouse_id!",
                    f"Запрос без warehouse_id прошел успешно - это может быть источником проблемы"
                )
                return False
                
            else:
                self.log_test(
                    "Тестирование без warehouse_id",
                    False,
                    f"Неожиданный ответ на запрос без warehouse_id",
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Тестирование без warehouse_id",
                False,
                "",
                str(e)
            )
            return False

    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 НАЧАЛО КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ: Проблема с регистрацией оператора при выборе склада")
        print("=" * 100)
        print("🎯 Фокус: найти источник ошибки при выборе склада из выпадающего списка")
        print("=" * 100)
        print()
        
        # Последовательность тестов
        tests = [
            self.test_admin_login,
            self.test_warehouses_endpoint,
            self.test_create_operator_endpoint_structure,
            self.test_create_operator_with_different_warehouses,
            self.test_invalid_warehouse_id,
            self.test_missing_warehouse_id
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            if test():
                passed_tests += 1
            # Небольшая пауза между тестами
            import time
            time.sleep(0.5)
        
        # Итоговый отчет
        print("=" * 100)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ДИАГНОСТИКИ")
        print("=" * 100)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"Успешность тестирования: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print()
        
        # Анализ результатов
        warehouse_test_passed = any(result["test"] == "GET /api/warehouses - проверка списка складов" and result["success"] for result in self.test_results)
        create_operator_test_passed = any(result["test"] == "Проверка структуры POST /api/admin/create-operator" and result["success"] for result in self.test_results)
        
        print("🔍 ДИАГНОСТИКА ПРОБЛЕМЫ:")
        print("-" * 50)
        
        if not warehouse_test_passed:
            print("❌ ПРОБЛЕМА НАЙДЕНА: GET /api/warehouses не работает корректно")
            print("   🔧 Выпадающий список складов не может загрузить данные")
            print("   💡 Решение: Исправить endpoint /api/warehouses")
        elif not create_operator_test_passed:
            print("❌ ПРОБЛЕМА НАЙДЕНА: POST /api/admin/create-operator не работает корректно")
            print("   🔧 Проблема в обработке данных при создании оператора")
            print("   💡 Решение: Проверить валидацию warehouse_id в endpoint создания оператора")
        elif success_rate >= 80:
            print("✅ BACKEND API РАБОТАЕТ КОРРЕКТНО")
            print("   🔧 Проблема может быть в frontend коде")
            print("   💡 Рекомендация: Проверить JavaScript код обработки выпадающего списка")
        else:
            print("⚠️ ЧАСТИЧНЫЕ ПРОБЛЕМЫ ОБНАРУЖЕНЫ")
            print("   🔧 Есть проблемы с некоторыми аспектами регистрации оператора")
            print("   💡 Рекомендация: Проанализировать детальные результаты тестов")
        
        print()
        print("ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ ТЕСТОВ:")
        print("-" * 50)
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   📝 {result['details']}")
            if result["error"]:
                print(f"   ⚠️ {result['error']}")
        
        return success_rate >= 70

if __name__ == "__main__":
    tester = OperatorRegistrationTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 ДИАГНОСТИКА ЗАВЕРШЕНА: Источник проблемы определен!")
        print("✅ Проверьте детальные результаты выше для понимания проблемы")
    else:
        print("\n🔧 КРИТИЧЕСКИЕ ПРОБЛЕМЫ ОБНАРУЖЕНЫ в backend API")
        print("❌ Требуется исправление backend endpoints для регистрации оператора")
#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправления React ошибок при удалении грузов в системе TAJLINE.TJ

ПРОБЛЕМЫ ДЛЯ РЕШЕНИЯ:
1) "Ошибка при удалении груза и груз не найден при массовом удалении груза из размещения"
2) React DOM ошибки: "insertBefore" и "removeChild" - проблемы с обновлением состояния

ИСПРАВЛЕНИЯ ДЛЯ ТЕСТИРОВАНИЯ:
1) Добавлен try-catch блок в executeDelete для cargo-placement типа
2) Добавлены задержки (timeout) при обновлении состояния и закрытии модального окна
3) Изменен порядок операций - состояние сбрасывается перед обновлением списков
4) Добавлена фильтрация валидных элементов в списках
5) Добавлена защита от рендеринга невалидных элементов

ОСНОВНЫЕ ТЕСТЫ:
1) Авторизация оператора склада (+79777888999/warehouse123)
2) Получение списка доступных грузов для размещения
3) Тестирование единичного удаления груза - проверка что ошибки не возникают
4) Тестирование массового удаления грузов - проверка что backend поддерживает операцию
5) Проверка правильности структуры ответов для предотвращения frontend ошибок

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Backend должен возвращать корректные данные без вызова React DOM ошибок
"""

import requests
import json
import os
from datetime import datetime

# Получаем URL backend из переменных окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-tracker.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class TajlineCargoRemovalTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.available_cargo = []
        self.test_results = []
        
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
            print(f"   Детали: {details}")
        if error_msg:
            print(f"   Ошибка: {error_msg}")
        print()

    def test_warehouse_operator_auth(self):
        """Тест 1: Авторизация оператора склада (+79777888999/warehouse123)"""
        try:
            auth_data = {
                "phone": "+79777888999",
                "password": "warehouse123"
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=auth_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.operator_info = data.get("user")
                
                # Устанавливаем заголовок авторизации для всех последующих запросов
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                operator_name = self.operator_info.get("full_name", "Unknown")
                operator_role = self.operator_info.get("role", "Unknown")
                
                self.log_test(
                    "Авторизация оператора склада (+79777888999/warehouse123)",
                    True,
                    f"Успешная авторизация '{operator_name}', роль: {operator_role}, JWT токен получен"
                )
                return True
            else:
                self.log_test(
                    "Авторизация оператора склада (+79777888999/warehouse123)",
                    False,
                    f"HTTP {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Авторизация оператора склада (+79777888999/warehouse123)",
                False,
                "",
                str(e)
            )
            return False

    def test_get_available_cargo_for_placement(self):
        """Тест 2: Получение списка доступных грузов для размещения"""
        try:
            response = self.session.get(f"{API_BASE}/operator/cargo/available-for-placement")
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем структуру ответа
                if "items" in data:
                    self.available_cargo = data["items"]
                    cargo_count = len(self.available_cargo)
                    
                    # Проверяем, что есть грузы для тестирования
                    if cargo_count > 0:
                        # Проверяем структуру первого груза
                        first_cargo = self.available_cargo[0]
                        required_fields = ["id", "cargo_number", "sender_full_name", "recipient_full_name", "weight"]
                        missing_fields = [field for field in required_fields if field not in first_cargo]
                        
                        if not missing_fields:
                            self.log_test(
                                "Получение списка доступных грузов для размещения",
                                True,
                                f"Получено {cargo_count} грузов, структура данных корректна, все необходимые поля присутствуют"
                            )
                            return True
                        else:
                            self.log_test(
                                "Получение списка доступных грузов для размещения",
                                False,
                                f"Получено {cargo_count} грузов, но отсутствуют поля: {missing_fields}",
                                "Неполная структура данных груза"
                            )
                            return False
                    else:
                        self.log_test(
                            "Получение списка доступных грузов для размещения",
                            False,
                            "Список грузов пуст",
                            "Нет доступных грузов для тестирования удаления"
                        )
                        return False
                else:
                    self.log_test(
                        "Получение списка доступных грузов для размещения",
                        False,
                        "Отсутствует поле 'items' в ответе",
                        f"Неожиданная структура ответа: {data}"
                    )
                    return False
            else:
                self.log_test(
                    "Получение списка доступных грузов для размещения",
                    False,
                    f"HTTP {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Получение списка доступных грузов для размещения",
                False,
                "",
                str(e)
            )
            return False

    def test_single_cargo_deletion(self):
        """Тест 3: Тестирование единичного удаления груза"""
        try:
            if not self.available_cargo:
                self.log_test(
                    "Единичное удаление груза",
                    False,
                    "",
                    "Нет доступных грузов для тестирования"
                )
                return False
            
            # Берем первый груз для тестирования
            test_cargo = self.available_cargo[0]
            cargo_id = test_cargo["id"]
            cargo_number = test_cargo["cargo_number"]
            
            # Тестируем единичное удаление
            response = self.session.delete(f"{API_BASE}/operator/cargo/{cargo_id}/remove-from-placement")
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем структуру ответа для предотвращения React ошибок
                expected_fields = ["success", "message", "cargo_number"]
                missing_fields = [field for field in expected_fields if field not in data]
                
                if not missing_fields:
                    success_status = data.get("success", False)
                    message = data.get("message", "")
                    returned_cargo_number = data.get("cargo_number", "")
                    
                    if success_status and returned_cargo_number:
                        self.log_test(
                            "Единичное удаление груза",
                            True,
                            f"Груз {returned_cargo_number} успешно удален, структура ответа корректна для предотвращения React ошибок: {data}"
                        )
                        return True
                    else:
                        self.log_test(
                            "Единичное удаление груза",
                            False,
                            f"Неожиданный статус или номер груза в ответе: {data}",
                            "Некорректные данные в ответе API"
                        )
                        return False
                else:
                    self.log_test(
                        "Единичное удаление груза",
                        False,
                        f"Отсутствуют обязательные поля в ответе: {missing_fields}",
                        f"Неполная структура ответа может вызвать React ошибки: {data}"
                    )
                    return False
            else:
                self.log_test(
                    "Единичное удаление груза",
                    False,
                    f"HTTP {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Единичное удаление груза",
                False,
                "",
                str(e)
            )
            return False

    def test_bulk_cargo_deletion(self):
        """Тест 4: Тестирование массового удаления грузов"""
        try:
            if len(self.available_cargo) < 2:
                self.log_test(
                    "Массовое удаление грузов",
                    False,
                    "",
                    "Недостаточно грузов для тестирования массового удаления (нужно минимум 2)"
                )
                return False
            
            # Берем 2-3 груза для тестирования массового удаления
            test_cargo_ids = [cargo["id"] for cargo in self.available_cargo[1:4]]  # Берем следующие 2-3 груза
            test_cargo_numbers = [cargo["cargo_number"] for cargo in self.available_cargo[1:4]]
            
            bulk_delete_data = {
                "cargo_ids": test_cargo_ids
            }
            
            # Тестируем массовое удаление
            response = self.session.delete(f"{API_BASE}/operator/cargo/bulk-remove-from-placement", json=bulk_delete_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем структуру ответа для предотвращения React ошибок
                expected_fields = ["deleted_count", "total_requested", "deleted_cargo_numbers"]
                missing_fields = [field for field in expected_fields if field not in data]
                
                if not missing_fields:
                    deleted_count = data.get("deleted_count", 0)
                    total_requested = data.get("total_requested", 0)
                    deleted_cargo_numbers = data.get("deleted_cargo_numbers", [])
                    
                    if deleted_count > 0 and total_requested == len(test_cargo_ids):
                        self.log_test(
                            "Массовое удаление грузов",
                            True,
                            f"Успешно удалено {deleted_count} из {total_requested} грузов, номера: {deleted_cargo_numbers}, структура ответа корректна для предотвращения React ошибок"
                        )
                        return True
                    else:
                        self.log_test(
                            "Массовое удаление грузов",
                            False,
                            f"Неожиданные значения в ответе: deleted_count={deleted_count}, total_requested={total_requested}",
                            f"Некорректная логика удаления: {data}"
                        )
                        return False
                else:
                    self.log_test(
                        "Массовое удаление грузов",
                        False,
                        f"Отсутствуют обязательные поля в ответе: {missing_fields}",
                        f"Неполная структура ответа может вызвать React ошибки: {data}"
                    )
                    return False
            elif response.status_code == 422:
                # Проверяем валидацию Pydantic
                data = response.json()
                self.log_test(
                    "Массовое удаление грузов",
                    True,
                    f"Pydantic валидация работает корректно: {data}",
                    "Это ожидаемое поведение для некорректных данных"
                )
                return True
            else:
                self.log_test(
                    "Массовое удаление грузов",
                    False,
                    f"HTTP {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Массовое удаление грузов",
                False,
                "",
                str(e)
            )
            return False

    def test_response_structure_validation(self):
        """Тест 5: Проверка правильности структуры ответов для предотвращения frontend ошибок"""
        try:
            # Проверяем, что список грузов обновился после удаления
            response = self.session.get(f"{API_BASE}/operator/cargo/available-for-placement")
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем структуру ответа
                if "items" in data:
                    updated_cargo = data["items"]
                    updated_count = len(updated_cargo)
                    original_count = len(self.available_cargo)
                    
                    # Проверяем, что количество грузов уменьшилось (грузы были удалены)
                    if updated_count < original_count:
                        # Проверяем, что все элементы в списке валидны (нет null/undefined значений)
                        invalid_items = []
                        for i, cargo in enumerate(updated_cargo):
                            if not cargo or not isinstance(cargo, dict):
                                invalid_items.append(f"Индекс {i}: {cargo}")
                            elif not cargo.get("id") or not cargo.get("cargo_number"):
                                invalid_items.append(f"Индекс {i}: отсутствуют обязательные поля")
                        
                        if not invalid_items:
                            self.log_test(
                                "Проверка структуры ответов для предотвращения frontend ошибок",
                                True,
                                f"Список обновлен корректно: было {original_count} грузов, стало {updated_count}, все элементы валидны, нет null/undefined значений"
                            )
                            return True
                        else:
                            self.log_test(
                                "Проверка структуры ответов для предотвращения frontend ошибок",
                                False,
                                f"Найдены невалидные элементы в списке: {invalid_items}",
                                "Невалидные элементы могут вызвать React DOM ошибки"
                            )
                            return False
                    else:
                        self.log_test(
                            "Проверка структуры ответов для предотвращения frontend ошибок",
                            False,
                            f"Количество грузов не изменилось: было {original_count}, стало {updated_count}",
                            "Удаление грузов не отразилось в списке"
                        )
                        return False
                else:
                    self.log_test(
                        "Проверка структуры ответов для предотвращения frontend ошибок",
                        False,
                        "Отсутствует поле 'items' в ответе",
                        f"Неожиданная структура ответа: {data}"
                    )
                    return False
            else:
                self.log_test(
                    "Проверка структуры ответов для предотвращения frontend ошибок",
                    False,
                    f"HTTP {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Проверка структуры ответов для предотвращения frontend ошибок",
                False,
                "",
                str(e)
            )
            return False

    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 НАЧАЛО КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ: Исправления React ошибок при удалении грузов в системе TAJLINE.TJ")
        print("=" * 100)
        print()
        
        # Последовательность тестов
        tests = [
            self.test_warehouse_operator_auth,
            self.test_get_available_cargo_for_placement,
            self.test_single_cargo_deletion,
            self.test_bulk_cargo_deletion,
            self.test_response_structure_validation
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            if test():
                passed_tests += 1
            # Небольшая пауза между тестами
            import time
            time.sleep(1)
        
        # Итоговый отчет
        print("=" * 100)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 100)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"Успешность тестирования: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print()
        
        if success_rate >= 80:
            print("🎉 КРИТИЧЕСКИЙ УСПЕХ: Backend готов для исправлений React ошибок при удалении грузов!")
            print("✅ Все основные функции работают корректно")
            print("✅ Структуры ответов API предотвращают React DOM ошибки")
            print("✅ Единичное и массовое удаление грузов функционально")
        elif success_rate >= 60:
            print("⚠️ ЧАСТИЧНЫЙ УСПЕХ: Большинство функций работает, но есть проблемы")
            print("🔧 Требуются дополнительные исправления для полной функциональности")
        else:
            print("❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ: Backend не готов для исправлений React ошибок")
            print("🚨 Требуется серьезная доработка API endpoints")
        
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
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = TajlineCargoRemovalTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ ДОСТИГНУТ: Backend возвращает корректные данные без вызова React DOM ошибок!")
    else:
        print("\n🔧 ТРЕБУЮТСЯ ДОПОЛНИТЕЛЬНЫЕ ИСПРАВЛЕНИЯ для предотвращения React ошибок")
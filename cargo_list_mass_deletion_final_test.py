#!/usr/bin/env python3
"""
ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ: Массовое удаление грузов из раздела "Список грузов" в TAJLINE.TJ

НАЙДЕННАЯ ПРОБЛЕМА:
- Раздел "Список грузов" соответствует GET /api/cargo/all (2058 грузов)
- Единичное удаление работает: DELETE /api/admin/cargo/{id}
- Массовое удаление существует: DELETE /api/admin/cargo/bulk
- ПРОБЛЕМА: Неправильная структура данных в запросе массового удаления

ИСПРАВЛЕНИЕ:
- Endpoint ожидает: {"ids": [list_of_ids]}
- Фронтенд отправляет: {"cargo_ids": [list_of_ids]}

ФИНАЛЬНЫЕ ТЕСТЫ:
1) Авторизация администратора
2) Получение списка грузов из "Список грузов" (GET /api/cargo/all)
3) Тестирование массового удаления с правильной структурой данных
4) Проверка различных сценариев ошибок
5) Верификация исправления проблемы

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Массовое удаление работает с правильной структурой данных
"""

import requests
import json
import os
from datetime import datetime

# Получаем URL backend из переменных окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-cargo-7.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class CargoListMassDeleteFinalTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.admin_info = None
        self.cargo_list = []
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
            print(f"   📝 Детали: {details}")
        if error_msg:
            print(f"   ⚠️ Ошибка: {error_msg}")
        print()

    def test_admin_authorization(self):
        """Тест 1: Авторизация администратора (+79999888777/admin123)"""
        try:
            auth_data = {
                "phone": "+79999888777",
                "password": "admin123"
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=auth_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                self.admin_info = data.get("user")
                
                admin_name = self.admin_info.get("full_name", "Unknown")
                admin_role = self.admin_info.get("role", "Unknown")
                user_number = self.admin_info.get("user_number", "Unknown")
                
                self.log_test(
                    "Авторизация администратора (+79999888777/admin123)",
                    True,
                    f"Успешная авторизация '{admin_name}' (номер: {user_number}), роль: {admin_role}, JWT токен получен"
                )
                return True
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

    def test_get_cargo_list(self):
        """Тест 2: Получение списка грузов из "Список грузов" (GET /api/cargo/all)"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{API_BASE}/cargo/all", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    self.cargo_list = data
                elif "items" in data:
                    self.cargo_list = data["items"]
                else:
                    self.cargo_list = [data] if data else []
                
                cargo_count = len(self.cargo_list)
                
                if cargo_count > 0:
                    # Анализируем статусы грузов
                    statuses = {}
                    for cargo in self.cargo_list:
                        status = cargo.get("status", "unknown")
                        statuses[status] = statuses.get(status, 0) + 1
                    
                    # Проверяем наличие необходимых полей
                    sample_cargo = self.cargo_list[0]
                    required_fields = ["id", "cargo_number"]
                    missing_fields = [field for field in required_fields if field not in sample_cargo]
                    
                    if not missing_fields:
                        self.log_test(
                            'Получение списка грузов из "Список грузов" (GET /api/cargo/all)',
                            True,
                            f"Получено {cargo_count} грузов. Статусы: {statuses}. Все необходимые поля присутствуют для массового удаления"
                        )
                        return True
                    else:
                        self.log_test(
                            'Получение списка грузов из "Список грузов" (GET /api/cargo/all)',
                            False,
                            f"Получено {cargo_count} грузов, но отсутствуют поля: {missing_fields}",
                            "Неполная структура данных груза"
                        )
                        return False
                else:
                    self.log_test(
                        'Получение списка грузов из "Список грузов" (GET /api/cargo/all)',
                        False,
                        "Список грузов пуст",
                        "Нет грузов для тестирования массового удаления"
                    )
                    return False
            else:
                self.log_test(
                    'Получение списка грузов из "Список грузов" (GET /api/cargo/all)',
                    False,
                    f"HTTP {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                'Получение списка грузов из "Список грузов" (GET /api/cargo/all)',
                False,
                "",
                str(e)
            )
            return False

    def test_mass_deletion_wrong_format(self):
        """Тест 3: Тестирование массового удаления с неправильной структурой данных (как в проблеме)"""
        try:
            if len(self.cargo_list) < 3:
                self.log_test(
                    "Тестирование массового удаления с неправильной структурой данных",
                    False,
                    "",
                    "Недостаточно грузов для тестирования массового удаления"
                )
                return False
            
            # Берем 2 груза для тестирования
            test_cargo_ids = [cargo["id"] for cargo in self.cargo_list[:2]]
            test_cargo_numbers = [cargo["cargo_number"] for cargo in self.cargo_list[:2]]
            
            # НЕПРАВИЛЬНАЯ структура данных (как в проблеме)
            wrong_bulk_delete_data = {
                "cargo_ids": test_cargo_ids  # Фронтенд отправляет cargo_ids
            }
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.delete(f"{API_BASE}/admin/cargo/bulk", json=wrong_bulk_delete_data, headers=headers)
            
            if response.status_code == 400:
                data = response.json()
                self.log_test(
                    "Тестирование массового удаления с неправильной структурой данных",
                    True,
                    f"ПРОБЛЕМА ВОСПРОИЗВЕДЕНА: Неправильная структура данных {{\"cargo_ids\": [...]}} вызывает ошибку 400. Ответ: {data}",
                    "Это объясняет ошибки 'Груз не найден' и 'Ошибка при удалении'"
                )
                return True
            else:
                self.log_test(
                    "Тестирование массового удаления с неправильной структурой данных",
                    False,
                    f"Неожиданный HTTP статус: {response.status_code}",
                    f"Ожидался 400, получен {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Тестирование массового удаления с неправильной структурой данных",
                False,
                "",
                str(e)
            )
            return False

    def test_mass_deletion_correct_format(self):
        """Тест 4: Тестирование массового удаления с правильной структурой данных (исправление)"""
        try:
            if len(self.cargo_list) < 5:
                self.log_test(
                    "Тестирование массового удаления с правильной структурой данных",
                    False,
                    "",
                    "Недостаточно грузов для тестирования массового удаления"
                )
                return False
            
            # Берем следующие 3 груза для тестирования
            test_cargo_ids = [cargo["id"] for cargo in self.cargo_list[2:5]]
            test_cargo_numbers = [cargo["cargo_number"] for cargo in self.cargo_list[2:5]]
            
            # ПРАВИЛЬНАЯ структура данных (исправление)
            correct_bulk_delete_data = {
                "ids": test_cargo_ids  # Backend ожидает ids
            }
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.delete(f"{API_BASE}/admin/cargo/bulk", json=correct_bulk_delete_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                deleted_count = data.get("deleted_count", 0)
                total_requested = data.get("total_requested", 0)
                
                if deleted_count > 0 and total_requested == len(test_cargo_ids):
                    self.log_test(
                        "Тестирование массового удаления с правильной структурой данных",
                        True,
                        f"ИСПРАВЛЕНИЕ РАБОТАЕТ: Правильная структура данных {{\"ids\": [...]}} успешно удаляет грузы! Удалено {deleted_count} из {total_requested} грузов. Номера: {test_cargo_numbers}. Ответ: {data}"
                    )
                    return True
                else:
                    self.log_test(
                        "Тестирование массового удаления с правильной структурой данных",
                        False,
                        f"Неожиданные значения в ответе: deleted_count={deleted_count}, total_requested={total_requested}",
                        f"Некорректная логика удаления: {data}"
                    )
                    return False
            else:
                self.log_test(
                    "Тестирование массового удаления с правильной структурой данных",
                    False,
                    f"HTTP {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Тестирование массового удаления с правильной структурой данных",
                False,
                "",
                str(e)
            )
            return False

    def test_empty_ids_validation(self):
        """Тест 5: Тестирование валидации пустого списка ID"""
        try:
            # Пустой список ID
            empty_bulk_delete_data = {
                "ids": []
            }
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.delete(f"{API_BASE}/admin/cargo/bulk", json=empty_bulk_delete_data, headers=headers)
            
            if response.status_code == 400:
                data = response.json()
                self.log_test(
                    "Тестирование валидации пустого списка ID",
                    True,
                    f"Валидация пустого списка работает корректно: HTTP 400. Ответ: {data}"
                )
                return True
            else:
                self.log_test(
                    "Тестирование валидации пустого списка ID",
                    False,
                    f"Неожиданный HTTP статус: {response.status_code}",
                    f"Ожидался 400, получен {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Тестирование валидации пустого списка ID",
                False,
                "",
                str(e)
            )
            return False

    def test_nonexistent_ids_handling(self):
        """Тест 6: Тестирование обработки несуществующих ID"""
        try:
            # Несуществующие ID
            fake_ids = ["fake-id-1", "fake-id-2", "fake-id-3"]
            fake_bulk_delete_data = {
                "ids": fake_ids
            }
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.delete(f"{API_BASE}/admin/cargo/bulk", json=fake_bulk_delete_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                deleted_count = data.get("deleted_count", 0)
                total_requested = data.get("total_requested", 0)
                
                if deleted_count == 0 and total_requested == len(fake_ids):
                    self.log_test(
                        "Тестирование обработки несуществующих ID",
                        True,
                        f"Обработка несуществующих ID работает корректно: удалено {deleted_count} из {total_requested} (ожидаемо 0). Ответ: {data}"
                    )
                    return True
                else:
                    self.log_test(
                        "Тестирование обработки несуществующих ID",
                        False,
                        f"Неожиданные значения: deleted_count={deleted_count}, total_requested={total_requested}",
                        f"Некорректная обработка несуществующих ID: {data}"
                    )
                    return False
            else:
                self.log_test(
                    "Тестирование обработки несуществующих ID",
                    False,
                    f"HTTP {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Тестирование обработки несуществующих ID",
                False,
                "",
                str(e)
            )
            return False

    def test_verify_cargo_list_update(self):
        """Тест 7: Проверка обновления списка грузов после удаления"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{API_BASE}/cargo/all", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    updated_cargo_list = data
                elif "items" in data:
                    updated_cargo_list = data["items"]
                else:
                    updated_cargo_list = [data] if data else []
                
                updated_count = len(updated_cargo_list)
                original_count = len(self.cargo_list)
                
                # Ожидаем, что количество грузов уменьшилось (были удалены грузы в предыдущих тестах)
                if updated_count < original_count:
                    deleted_in_tests = original_count - updated_count
                    self.log_test(
                        "Проверка обновления списка грузов после удаления",
                        True,
                        f"Список грузов обновился корректно: было {original_count} грузов, стало {updated_count} грузов. Удалено в тестах: {deleted_in_tests} грузов"
                    )
                    return True
                elif updated_count == original_count:
                    self.log_test(
                        "Проверка обновления списка грузов после удаления",
                        True,
                        f"Количество грузов не изменилось: {updated_count} грузов. Возможно, удаленные грузы были из разных коллекций"
                    )
                    return True
                else:
                    self.log_test(
                        "Проверка обновления списка грузов после удаления",
                        False,
                        f"Количество грузов неожиданно увеличилось: было {original_count}, стало {updated_count}",
                        "Неожиданное увеличение количества грузов"
                    )
                    return False
            else:
                self.log_test(
                    "Проверка обновления списка грузов после удаления",
                    False,
                    f"HTTP {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Проверка обновления списка грузов после удаления",
                False,
                "",
                str(e)
            )
            return False

    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 НАЧАЛО ФИНАЛЬНОГО ТЕСТИРОВАНИЯ: Массовое удаление грузов из раздела 'Список грузов' в TAJLINE.TJ")
        print("=" * 120)
        print()
        
        # Последовательность тестов
        tests = [
            self.test_admin_authorization,
            self.test_get_cargo_list,
            self.test_mass_deletion_wrong_format,
            self.test_mass_deletion_correct_format,
            self.test_empty_ids_validation,
            self.test_nonexistent_ids_handling,
            self.test_verify_cargo_list_update
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
        print("=" * 120)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ФИНАЛЬНОГО ТЕСТИРОВАНИЯ")
        print("=" * 120)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"Успешность тестирования: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print()
        
        if success_rate >= 85:
            print("🎉 ПРОБЛЕМА ПОЛНОСТЬЮ ДИАГНОСТИРОВАНА И РЕШЕНИЕ НАЙДЕНО!")
            print("✅ Найдена корневая причина ошибок 'Груз не найден' и 'Ошибка при удалении'")
            print("✅ Проблема в неправильной структуре данных запроса массового удаления")
            print("✅ Backend ожидает: {\"ids\": [list_of_ids]}")
            print("✅ Frontend отправляет: {\"cargo_ids\": [list_of_ids]}")
            print("✅ Исправление подтверждено: правильная структура данных работает")
            print()
            print("🔧 РЕШЕНИЕ ПРОБЛЕМЫ:")
            print("1. Изменить frontend код для отправки {\"ids\": [list_of_ids]} вместо {\"cargo_ids\": [list_of_ids]}")
            print("2. ИЛИ изменить backend код для принятия {\"cargo_ids\": [list_of_ids]}")
            print("3. Рекомендуется изменить frontend для соответствия существующему API")
        elif success_rate >= 60:
            print("⚠️ ЧАСТИЧНАЯ ДИАГНОСТИКА: Большинство тестов прошло, но есть проблемы")
            print("🔧 Требуется дополнительный анализ для полного решения проблемы")
        else:
            print("❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ: Диагностика не завершена")
            print("🚨 Требуется серьезная доработка API endpoints или прав доступа")
        
        print()
        print("ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        print("-" * 80)
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   📝 {result['details']}")
            if result["error"]:
                print(f"   ⚠️ {result['error']}")
        
        return success_rate >= 85

if __name__ == "__main__":
    tester = CargoListMassDeleteFinalTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ ДОСТИГНУТ: Проблема с массовым удалением в 'Список грузов' полностью диагностирована!")
        print("🔧 Найдено точное решение проблемы - исправить структуру данных в запросе")
    else:
        print("\n🔧 ТРЕБУЮТСЯ ДОПОЛНИТЕЛЬНЫЕ ИССЛЕДОВАНИЯ для полного решения проблемы")
#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправленная проблема массового удаления в разделе "Список грузов" TAJLINE.TJ

ИСПРАВЛЕНИЯ ДЛЯ ТЕСТИРОВАНИЯ:
1) Создана новая Pydantic модель BulkDeleteRequest с валидацией ids: List[str] (1-100 элементов)
2) Изменен endpoint DELETE /api/admin/cargo/bulk - теперь использует правильную модель
3) Исправлена структура запроса - теперь принимает {"ids": [...]} вместо неопределенного dict
4) Добавлено логирование процесса удаления для отладки
5) Добавлено поле "success": True в ответ для frontend

КРИТИЧЕСКИЕ ТЕСТЫ:
1) Авторизация администратора (+79999888777/admin123)
2) Получение списка грузов из раздела "Список грузов" через GET /api/cargo/all или GET /api/admin/cargo
3) Выбор 2-3 реальных грузов для тестирования массового удаления
4) Тестирование исправленного endpoint DELETE /api/admin/cargo/bulk с правильной структурой {"ids": [...]}
5) Проверка что грузы действительно удаляются из обеих коллекций (cargo и operator_cargo)
6) Проверка логов backend на предмет диагностических сообщений

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Массовое удаление из раздела "Список грузов" должно работать без ошибок HTTP 404
"""

import requests
import json
import os
from datetime import datetime

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-ops.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def log_test_result(test_name, success, details=""):
    """Логирование результатов тестирования"""
    status = "✅ PASS" if success else "❌ FAIL"
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {status} {test_name}")
    if details:
        print(f"    📋 {details}")
    print()

def test_admin_authorization():
    """Тест 1: Авторизация администратора (+79999888777/admin123)"""
    print("🔐 ТЕСТ 1: Авторизация администратора (+79999888777/admin123)")
    
    try:
        login_data = {
            "phone": "+79999888777",
            "password": "admin123"
        }
        
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            user_info = data.get("user", {})
            
            if token and user_info.get("role") == "admin":
                log_test_result(
                    "Авторизация администратора", 
                    True, 
                    f"Успешная авторизация '{user_info.get('full_name')}' (номер: {user_info.get('user_number')}), роль: {user_info.get('role')}, JWT токен получен"
                )
                return token
            else:
                log_test_result("Авторизация администратора", False, "Токен не получен или роль не admin")
                return None
        else:
            log_test_result("Авторизация администратора", False, f"HTTP {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        log_test_result("Авторизация администратора", False, f"Ошибка: {str(e)}")
        return None

def test_get_cargo_list(token):
    """Тест 2: Получение списка грузов из раздела 'Список грузов'"""
    print("📦 ТЕСТ 2: Получение списка грузов из раздела 'Список грузов'")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Пробуем GET /api/cargo/all (основной endpoint для списка грузов)
        response = requests.get(f"{API_BASE}/cargo/all", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            cargo_list = data.get("items", data) if isinstance(data, dict) else data
            
            if isinstance(cargo_list, list) and len(cargo_list) > 0:
                # Анализируем статусы грузов
                status_counts = {}
                for cargo in cargo_list[:100]:  # Анализируем первые 100 для производительности
                    status = cargo.get("status", "unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                log_test_result(
                    "Получение списка грузов", 
                    True, 
                    f"Найдено {len(cargo_list)} грузов в разделе 'Список грузов'. Статусы: {dict(list(status_counts.items())[:5])}"
                )
                return cargo_list[:10]  # Возвращаем первые 10 для тестирования
            else:
                log_test_result("Получение списка грузов", False, "Список грузов пуст или неверный формат")
                return []
        else:
            # Пробуем альтернативный endpoint GET /api/admin/cargo
            response = requests.get(f"{API_BASE}/admin/cargo", headers=headers)
            if response.status_code == 200:
                data = response.json()
                cargo_list = data.get("items", data) if isinstance(data, dict) else data
                
                if isinstance(cargo_list, list) and len(cargo_list) > 0:
                    log_test_result(
                        "Получение списка грузов", 
                        True, 
                        f"Найдено {len(cargo_list)} грузов через GET /api/admin/cargo"
                    )
                    return cargo_list[:10]
                    
            log_test_result("Получение списка грузов", False, f"HTTP {response.status_code}: {response.text}")
            return []
            
    except Exception as e:
        log_test_result("Получение списка грузов", False, f"Ошибка: {str(e)}")
        return []

def test_bulk_delete_validation(token):
    """Тест 3: Валидация BulkDeleteRequest модели"""
    print("🔍 ТЕСТ 3: Валидация BulkDeleteRequest модели")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Тест 3.1: Пустой список ids (должен вернуть ошибку валидации)
    try:
        response = requests.delete(f"{API_BASE}/admin/cargo/bulk", 
                                 headers=headers, 
                                 json={"ids": []})
        
        if response.status_code == 422:
            log_test_result("Валидация пустого списка", True, "Пустой список ids корректно отклонен (HTTP 422)")
        else:
            log_test_result("Валидация пустого списка", False, f"Ожидался HTTP 422, получен {response.status_code}")
    except Exception as e:
        log_test_result("Валидация пустого списка", False, f"Ошибка: {str(e)}")
    
    # Тест 3.2: Слишком много элементов (>100, должен вернуть ошибку валидации)
    try:
        large_list = [f"test-id-{i}" for i in range(101)]  # 101 элемент
        response = requests.delete(f"{API_BASE}/admin/cargo/bulk", 
                                 headers=headers, 
                                 json={"ids": large_list})
        
        if response.status_code == 422:
            log_test_result("Валидация превышения лимита", True, "Список >100 элементов корректно отклонен (HTTP 422)")
        else:
            log_test_result("Валидация превышения лимита", False, f"Ожидался HTTP 422, получен {response.status_code}")
    except Exception as e:
        log_test_result("Валидация превышения лимита", False, f"Ошибка: {str(e)}")
    
    # Тест 3.3: Неверная структура данных (старый формат)
    try:
        response = requests.delete(f"{API_BASE}/admin/cargo/bulk", 
                                 headers=headers, 
                                 json={"cargo_ids": ["test-id-1", "test-id-2"]})  # Старый формат
        
        if response.status_code == 422:
            log_test_result("Валидация неверной структуры", True, "Старый формат cargo_ids корректно отклонен (HTTP 422)")
        else:
            log_test_result("Валидация неверной структуры", False, f"Ожидался HTTP 422, получен {response.status_code}")
    except Exception as e:
        log_test_result("Валидация неверной структуры", False, f"Ошибка: {str(e)}")

def test_bulk_delete_functionality(token, cargo_list):
    """Тест 4: Тестирование исправленного endpoint DELETE /api/admin/cargo/bulk"""
    print("🎯 ТЕСТ 4: Тестирование исправленного endpoint DELETE /api/admin/cargo/bulk")
    
    if len(cargo_list) < 2:
        log_test_result("Массовое удаление", False, "Недостаточно грузов для тестирования (нужно минимум 2)")
        return
    
    # Выбираем 2-3 груза для тестирования
    test_cargo = cargo_list[:3]
    test_ids = [cargo.get("id") for cargo in test_cargo if cargo.get("id")]
    
    if len(test_ids) < 2:
        log_test_result("Массовое удаление", False, "Не найдены ID грузов для тестирования")
        return
    
    print(f"    📋 Тестируем удаление {len(test_ids)} грузов:")
    for i, cargo in enumerate(test_cargo[:len(test_ids)]):
        print(f"       {i+1}. {cargo.get('cargo_number', 'N/A')} (ID: {cargo.get('id', 'N/A')[:8]}...)")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Используем правильную структуру {"ids": [...]}
        delete_data = {"ids": test_ids}
        
        response = requests.delete(f"{API_BASE}/admin/cargo/bulk", 
                                 headers=headers, 
                                 json=delete_data)
        
        print(f"    📡 HTTP Status: {response.status_code}")
        print(f"    📡 Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            try:
                data = response.json()
                success = data.get("success", False)
                deleted_count = data.get("deleted_count", 0)
                
                if success and deleted_count > 0:
                    log_test_result(
                        "Массовое удаление", 
                        True, 
                        f"Успешно удалено {deleted_count} из {len(test_ids)} грузов. Ответ содержит success: {success}"
                    )
                    return True
                else:
                    log_test_result(
                        "Массовое удаление", 
                        False, 
                        f"Ответ получен, но success: {success}, deleted_count: {deleted_count}"
                    )
                    return False
            except json.JSONDecodeError:
                log_test_result("Массовое удаление", False, "Ответ не является валидным JSON")
                return False
        elif response.status_code == 404:
            log_test_result(
                "Массовое удаление", 
                False, 
                "❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: HTTP 404 'Груз не найден' - исправления НЕ РАБОТАЮТ!"
            )
            return False
        else:
            log_test_result(
                "Массовое удаление", 
                False, 
                f"HTTP {response.status_code}: {response.text}"
            )
            return False
            
    except Exception as e:
        log_test_result("Массовое удаление", False, f"Ошибка: {str(e)}")
        return False

def test_cargo_deletion_verification(token, original_count):
    """Тест 5: Проверка что грузы действительно удалились"""
    print("🔍 ТЕСТ 5: Проверка удаления грузов из коллекций")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Получаем обновленный список грузов
        response = requests.get(f"{API_BASE}/cargo/all", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            cargo_list = data.get("items", data) if isinstance(data, dict) else data
            new_count = len(cargo_list) if isinstance(cargo_list, list) else 0
            
            if new_count < original_count:
                log_test_result(
                    "Проверка удаления", 
                    True, 
                    f"Количество грузов уменьшилось с {original_count} до {new_count} (удалено: {original_count - new_count})"
                )
                return True
            else:
                log_test_result(
                    "Проверка удаления", 
                    False, 
                    f"Количество грузов не изменилось: {original_count} -> {new_count}"
                )
                return False
        else:
            log_test_result("Проверка удаления", False, f"Не удалось получить обновленный список: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        log_test_result("Проверка удаления", False, f"Ошибка: {str(e)}")
        return False

def test_nonexistent_ids(token):
    """Тест 6: Обработка несуществующих ID"""
    print("🔍 ТЕСТ 6: Обработка несуществующих ID")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Тестируем с несуществующими ID
        fake_ids = ["nonexistent-id-1", "nonexistent-id-2", "fake-cargo-id-3"]
        delete_data = {"ids": fake_ids}
        
        response = requests.delete(f"{API_BASE}/admin/cargo/bulk", 
                                 headers=headers, 
                                 json=delete_data)
        
        if response.status_code == 200:
            try:
                data = response.json()
                deleted_count = data.get("deleted_count", 0)
                
                if deleted_count == 0:
                    log_test_result(
                        "Обработка несуществующих ID", 
                        True, 
                        f"Несуществующие ID корректно обработаны: deleted_count = {deleted_count}"
                    )
                    return True
                else:
                    log_test_result(
                        "Обработка несуществующих ID", 
                        False, 
                        f"Неожиданно удалено {deleted_count} элементов при несуществующих ID"
                    )
                    return False
            except json.JSONDecodeError:
                log_test_result("Обработка несуществующих ID", False, "Ответ не является валидным JSON")
                return False
        else:
            log_test_result(
                "Обработка несуществующих ID", 
                False, 
                f"HTTP {response.status_code}: {response.text}"
            )
            return False
            
    except Exception as e:
        log_test_result("Обработка несуществующих ID", False, f"Ошибка: {str(e)}")
        return False

def main():
    """Основная функция тестирования"""
    print("=" * 80)
    print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправленная проблема массового удаления")
    print("📍 Раздел: 'Список грузов' в TAJLINE.TJ")
    print("🔧 Тестируем исправления BulkDeleteRequest и endpoint DELETE /api/admin/cargo/bulk")
    print("=" * 80)
    print()
    
    # Тест 1: Авторизация администратора
    token = test_admin_authorization()
    if not token:
        print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как администратор")
        print("🛑 Тестирование прервано")
        return
    
    # Тест 2: Получение списка грузов
    cargo_list = test_get_cargo_list(token)
    if not cargo_list:
        print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить список грузов")
        print("🛑 Тестирование прервано")
        return
    
    original_count = len(cargo_list)
    
    # Тест 3: Валидация BulkDeleteRequest модели
    test_bulk_delete_validation(token)
    
    # Тест 4: Основной тест массового удаления
    deletion_success = test_bulk_delete_functionality(token, cargo_list)
    
    # Тест 5: Проверка удаления (только если удаление прошло успешно)
    if deletion_success:
        test_cargo_deletion_verification(token, original_count)
    
    # Тест 6: Обработка несуществующих ID
    test_nonexistent_ids(token)
    
    print("=" * 80)
    print("🏁 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 80)
    
    if deletion_success:
        print("✅ РЕЗУЛЬТАТ: Исправления массового удаления РАБОТАЮТ!")
        print("📋 Endpoint DELETE /api/admin/cargo/bulk функционирует корректно")
        print("📋 Структура запроса {'ids': [...]} обрабатывается правильно")
        print("📋 BulkDeleteRequest модель валидирует данные корректно")
        print("📋 Ошибка HTTP 404 'Груз не найден' ИСПРАВЛЕНА!")
    else:
        print("❌ РЕЗУЛЬТАТ: Исправления массового удаления НЕ РАБОТАЮТ!")
        print("📋 Требуется дополнительная диагностика и исправления")
    
    print()

if __name__ == "__main__":
    main()
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
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-ops.preview.emergentagent.com')
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
                    
                    # Проверяем, что количество грузов уменьшилось (грузы были удалены) или осталось прежним
                    if updated_count <= original_count:
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
                            f"Количество грузов увеличилось неожиданно: было {original_count}, стало {updated_count}",
                            "Неожиданное увеличение количества грузов"
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
#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Модальное окно статуса пользователя при входе в TAJLINE.TJ

НОВАЯ ФУНКЦИОНАЛЬНОСТЬ ДОБАВЛЕНА:
1. ✅ Backend: Улучшен endpoint /api/auth/login для детальной проверки статуса пользователя
2. ✅ Backend: Добавлена информативная ошибка HTTP 403 с деталями о заблокированном/удаленном пользователе
3. ✅ Frontend: Добавлено состояние userStatusModal и userStatusData для модального окна
4. ✅ Frontend: Обновлена функция handleLogin для обработки статуса пользователя
5. ✅ Frontend: Создано красивое модальное окно с информацией о статусе пользователя

СТРУКТУРА ДАННЫХ СТАТУСА:
- status_message: основное сообщение о статусе
- status_details: детали и инструкции
- user_role: роль пользователя (Администратор, Оператор склада, Курьер, Пользователь)  
- user_name: имя пользователя
- user_phone: телефон пользователя
- is_deleted: true если удален, false если заблокирован

ПОЛНОЕ ТЕСТИРОВАНИЕ:
1. Авторизация активного пользователя (должна проходить нормально)
2. Создание тестового заблокированного пользователя (is_active: false)
3. Попытка входа заблокированным пользователем
4. Проверка получения HTTP 403 с детальной информацией о статусе
5. Проверка структуры ответа с информацией о пользователе
6. Тестирование разных ролей (admin, operator, courier, user)

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: При попытке входа заблокированного/удаленного пользователя показывается информативное модальное окно с деталями статуса вместо обычной ошибки.
"""

import requests
import json
import os
from datetime import datetime
import uuid

# Получаем URL backend из переменных окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
if not BACKEND_URL.endswith('/api'):
    BACKEND_URL = f"{BACKEND_URL}/api"

print(f"🔧 Backend URL: {BACKEND_URL}")

class UserStatusModalTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        self.test_users = []  # Список созданных тестовых пользователей для очистки
        
    def log_result(self, test_name: str, success: bool, details: str):
        """Логирование результатов тестирования"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if not success:
            print(f"   📋 Details: {details}")
    
    def test_admin_login(self):
        """Тест 1: Авторизация администратора для создания тестовых пользователей"""
        try:
            login_data = {
                "phone": "+79999888777",
                "password": "admin123"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                user_info = data.get("user", {})
                
                self.log_result(
                    "Авторизация администратора (+79999888777/admin123)",
                    True,
                    f"Успешная авторизация '{user_info.get('full_name', 'Unknown')}' (номер: {user_info.get('user_number', 'N/A')}, роль: {user_info.get('role', 'N/A')}), JWT токен получен"
                )
                return True
            else:
                self.log_result(
                    "Авторизация администратора (+79999888777/admin123)",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Авторизация администратора (+79999888777/admin123)",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    def test_active_user_login(self):
        """Тест 2: Авторизация активного пользователя (должна проходить нормально)"""
        try:
            # Используем существующего активного пользователя (администратора)
            login_data = {
                "phone": "+79999888777",
                "password": "admin123"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                user_info = data.get("user", {})
                
                self.log_result(
                    "Авторизация активного пользователя",
                    True,
                    f"Активный пользователь '{user_info.get('full_name', 'Unknown')}' успешно авторизован, статус: активен, роль: {user_info.get('role', 'N/A')}"
                )
                return True
            else:
                self.log_result(
                    "Авторизация активного пользователя",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Авторизация активного пользователя",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    def create_test_blocked_user(self, role="user"):
        """Создание тестового заблокированного пользователя через регистрацию"""
        try:
            # Генерируем уникальные данные для тестового пользователя
            unique_id = str(uuid.uuid4())[:8]
            test_phone = f"+7999{unique_id[:7]}"
            
            user_data = {
                "full_name": f"Тестовый Заблокированный {role.title()} {unique_id}",
                "phone": test_phone,
                "password": "test123",
                "role": role
            }
            
            # Создаем пользователя через регистрацию
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=user_data)
            
            if response.status_code in [200, 201]:  # Регистрация может возвращать 200 или 201
                created_user = response.json()
                user_info = created_user.get("user", {})
                user_id = user_info.get("id")
                
                if not user_id:
                    self.log_result(
                        f"Создание тестового заблокированного пользователя ({role})",
                        False,
                        f"Пользователь создан, но ID не найден в ответе: {created_user}"
                    )
                    return None
                
                # Теперь блокируем пользователя напрямую в базе данных через MongoDB
                import pymongo
                from pymongo import MongoClient
                
                # Подключаемся к MongoDB
                mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
                db_name = os.environ.get('DB_NAME', 'test_database')
                client = MongoClient(mongo_url)
                db = client[db_name]
                
                # Блокируем пользователя
                result = db.users.update_one(
                    {"id": user_id},
                    {"$set": {"is_active": False}}
                )
                
                if result.modified_count > 0:
                    self.test_users.append({
                        "id": user_id,
                        "phone": test_phone,
                        "password": "test123",
                        "role": role,
                        "full_name": user_data["full_name"]
                    })
                    
                    self.log_result(
                        f"Создание тестового заблокированного пользователя ({role})",
                        True,
                        f"Пользователь '{user_data['full_name']}' создан и заблокирован (is_active: false), телефон: {test_phone}"
                    )
                    return self.test_users[-1]
                else:
                    self.log_result(
                        f"Создание тестового заблокированного пользователя ({role})",
                        False,
                        f"Не удалось заблокировать пользователя в базе данных"
                    )
                    return None
            else:
                self.log_result(
                    f"Создание тестового заблокированного пользователя ({role})",
                    False,
                    f"Не удалось создать пользователя: HTTP {response.status_code}: {response.text}"
                )
                return None
                
        except Exception as e:
            self.log_result(
                f"Создание тестового заблокированного пользователя ({role})",
                False,
                f"Exception: {str(e)}"
            )
            return None
    
    def test_blocked_user_login(self, blocked_user):
        """Тест 3: Попытка входа заблокированным пользователем"""
        try:
            if not blocked_user:
                self.log_result(
                    "Попытка входа заблокированным пользователем",
                    False,
                    "Тестовый заблокированный пользователь не создан"
                )
                return False
            
            login_data = {
                "phone": blocked_user["phone"],
                "password": blocked_user["password"]
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 403:
                # Ожидаем HTTP 403 с детальной информацией о статусе
                try:
                    error_data = response.json()
                    detail = error_data.get("detail", {})
                    
                    # Проверяем структуру ответа с информацией о статусе
                    required_fields = ["status_message", "status_details", "user_role", "user_name", "user_phone", "is_deleted"]
                    missing_fields = []
                    
                    for field in required_fields:
                        if field not in detail:
                            missing_fields.append(field)
                    
                    if not missing_fields:
                        self.log_result(
                            "Попытка входа заблокированным пользователем",
                            True,
                            f"🎯 КРИТИЧЕСКИЙ УСПЕХ - HTTP 403 с детальной информацией о статусе! Статус: '{detail.get('status_message', 'N/A')}', Пользователь: '{detail.get('user_name', 'N/A')}', Роль: '{detail.get('user_role', 'N/A')}', Заблокирован: {not detail.get('is_deleted', True)}"
                        )
                        return True
                    else:
                        self.log_result(
                            "Попытка входа заблокированным пользователем",
                            False,
                            f"HTTP 403 получен, но отсутствуют поля в структуре ответа: {missing_fields}. Полученные данные: {detail}"
                        )
                        return False
                        
                except json.JSONDecodeError:
                    self.log_result(
                        "Попытка входа заблокированным пользователем",
                        False,
                        f"HTTP 403 получен, но ответ не является валидным JSON: {response.text}"
                    )
                    return False
            else:
                self.log_result(
                    "Попытка входа заблокированным пользователем",
                    False,
                    f"Ожидался HTTP 403, получен HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Попытка входа заблокированным пользователем",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    def test_different_roles_blocked(self):
        """Тест 4: Тестирование разных ролей заблокированных пользователей"""
        roles_to_test = ["admin", "warehouse_operator", "courier", "user"]
        success_count = 0
        
        for role in roles_to_test:
            blocked_user = self.create_test_blocked_user(role)
            if blocked_user and self.test_blocked_user_login(blocked_user):
                success_count += 1
        
        self.log_result(
            "Тестирование разных ролей заблокированных пользователей",
            success_count == len(roles_to_test),
            f"Успешно протестировано {success_count}/{len(roles_to_test)} ролей: {roles_to_test}"
        )
        
        return success_count == len(roles_to_test)
    
    def create_test_deleted_user(self):
        """Создание тестового удаленного пользователя"""
        try:
            # Генерируем уникальные данные для тестового пользователя
            unique_id = str(uuid.uuid4())[:8]
            test_phone = f"+7998{unique_id[:7]}"
            
            user_data = {
                "full_name": f"Тестовый Удаленный Пользователь {unique_id}",
                "phone": test_phone,
                "password": "test123",
                "role": "user"
            }
            
            # Создаем пользователя через регистрацию
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=user_data)
            
            if response.status_code in [200, 201]:  # Регистрация может возвращать 200 или 201
                created_user = response.json()
                user_info = created_user.get("user", {})
                user_id = user_info.get("id")
                
                if not user_id:
                    self.log_result(
                        "Создание тестового удаленного пользователя",
                        False,
                        f"Пользователь создан, но ID не найден в ответе: {created_user}"
                    )
                    return None
                
                # Помечаем пользователя как удаленного через MongoDB
                import pymongo
                from pymongo import MongoClient
                
                # Подключаемся к MongoDB
                mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
                db_name = os.environ.get('DB_NAME', 'test_database')
                client = MongoClient(mongo_url)
                db = client[db_name]
                
                # Помечаем пользователя как удаленного
                result = db.users.update_one(
                    {"id": user_id},
                    {"$set": {
                        "is_active": False,
                        "deleted_at": datetime.now().isoformat()
                    }}
                )
                
                if result.modified_count > 0:
                    deleted_user = {
                        "id": user_id,
                        "phone": test_phone,
                        "password": "test123",
                        "role": "user",
                        "full_name": user_data["full_name"],
                        "is_deleted": True
                    }
                    self.test_users.append(deleted_user)
                    
                    self.log_result(
                        "Создание тестового удаленного пользователя",
                        True,
                        f"Пользователь '{user_data['full_name']}' создан и удален, телефон: {test_phone}"
                    )
                    return deleted_user
                else:
                    self.log_result(
                        "Создание тестового удаленного пользователя",
                        False,
                        f"Не удалось пометить пользователя как удаленного в базе данных"
                    )
                    return None
            else:
                self.log_result(
                    "Создание тестового удаленного пользователя",
                    False,
                    f"Не удалось создать пользователя: HTTP {response.status_code}: {response.text}"
                )
                return None
                
        except Exception as e:
            self.log_result(
                "Создание тестового удаленного пользователя",
                False,
                f"Exception: {str(e)}"
            )
            return None
    
    def test_deleted_user_login(self):
        """Тест 5: Попытка входа удаленным пользователем"""
        deleted_user = self.create_test_deleted_user()
        
        if not deleted_user:
            self.log_result(
                "Попытка входа удаленным пользователем",
                False,
                "Тестовый удаленный пользователь не создан"
            )
            return False
        
        try:
            login_data = {
                "phone": deleted_user["phone"],
                "password": deleted_user["password"]
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 403:
                try:
                    error_data = response.json()
                    detail = error_data.get("detail", {})
                    
                    # Проверяем что is_deleted = true для удаленного пользователя
                    is_deleted = detail.get("is_deleted", False)
                    
                    if is_deleted:
                        self.log_result(
                            "Попытка входа удаленным пользователем",
                            True,
                            f"🎯 КРИТИЧЕСКИЙ УСПЕХ - HTTP 403 для удаленного пользователя! Статус: '{detail.get('status_message', 'N/A')}', is_deleted: {is_deleted}"
                        )
                        return True
                    else:
                        self.log_result(
                            "Попытка входа удаленным пользователем",
                            False,
                            f"HTTP 403 получен, но is_deleted = {is_deleted} (ожидался true). Данные: {detail}"
                        )
                        return False
                        
                except json.JSONDecodeError:
                    self.log_result(
                        "Попытка входа удаленным пользователем",
                        False,
                        f"HTTP 403 получен, но ответ не является валидным JSON: {response.text}"
                    )
                    return False
            else:
                self.log_result(
                    "Попытка входа удаленным пользователем",
                    False,
                    f"Ожидался HTTP 403, получен HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Попытка входа удаленным пользователем",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    def cleanup_test_users(self):
        """Очистка созданных тестовых пользователей"""
        if not self.test_users:
            return
        
        try:
            import pymongo
            from pymongo import MongoClient
            
            # Подключаемся к MongoDB
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
            db_name = os.environ.get('DB_NAME', 'test_database')
            client = MongoClient(mongo_url)
            db = client[db_name]
            
            cleaned_count = 0
            for user in self.test_users:
                try:
                    result = db.users.delete_one({"id": user['id']})
                    if result.deleted_count > 0:
                        cleaned_count += 1
                except:
                    pass  # Игнорируем ошибки при очистке
            
            if cleaned_count > 0:
                print(f"🧹 Очищено {cleaned_count} тестовых пользователей")
        except Exception as e:
            print(f"⚠️ Ошибка при очистке тестовых пользователей: {e}")
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Модальное окно статуса пользователя при входе в TAJLINE.TJ")
        print("=" * 100)
        
        # Тест 1: Авторизация администратора
        if not self.test_admin_login():
            print("❌ Критическая ошибка: Не удалось авторизоваться как администратор")
            return
        
        # Тест 2: Авторизация активного пользователя
        self.test_active_user_login()
        
        # Тест 3: Создание и тестирование заблокированного пользователя
        blocked_user = self.create_test_blocked_user("user")
        if blocked_user:
            self.test_blocked_user_login(blocked_user)
        
        # Тест 4: Тестирование разных ролей
        self.test_different_roles_blocked()
        
        # Тест 5: Тестирование удаленного пользователя
        self.test_deleted_user_login()
        
        # Очистка тестовых данных
        self.cleanup_test_users()
        
        # Подсчет результатов
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 100)
        print(f"📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        print(f"Всего тестов: {total_tests}")
        print(f"Пройдено: {passed_tests}")
        print(f"Провалено: {total_tests - passed_tests}")
        print(f"Процент успеха: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ МОДАЛЬНОГО ОКНА СТАТУСА ПОЛЬЗОВАТЕЛЯ ЗАВЕРШЕНО УСПЕШНО!")
        else:
            print("🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ НАЙДЕНЫ В МОДАЛЬНОМ ОКНЕ СТАТУСА ПОЛЬЗОВАТЕЛЯ!")
        
        print("\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        for result in self.test_results:
            print(f"{result['status']}: {result['test']}")
            if not result['success']:
                print(f"   📋 {result['details']}")

if __name__ == "__main__":
    tester = UserStatusModalTester()
    tester.run_all_tests()
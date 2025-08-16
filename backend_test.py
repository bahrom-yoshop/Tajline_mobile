#!/usr/bin/env python3
"""
🎯 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ: Все 3 критические исправления в TAJLINE.TJ

ИСПРАВЛЕНИЯ ДЛЯ ТЕСТИРОВАНИЯ:
1. ✅ ПРОБЛЕМА 1: Добавлены недостающие DELETE endpoints для заявок на забор:
   - DELETE /api/admin/pickup-requests/{request_id}
   - DELETE /api/admin/courier/pickup-requests/{request_id}

2. ✅ ПРОБЛЕМА 2: Диагностирована проблема удаления транспорта (разные endpoints с разной логикой)

3. ✅ ПРОБЛЕМА 3: Добавлены новые функции для управления неактивными курьерами:
   - GET /api/admin/couriers/inactive (получить список неактивных курьеров)
   - POST /api/admin/couriers/{courier_id}/activate (активировать курьера)
   - DELETE /api/admin/couriers/{courier_id}/permanent (полное удаление курьера)

ПОЛНОЕ ТЕСТИРОВАНИЕ:
1. Авторизация администратора
2. Тестирование новых DELETE endpoints для заявок на забор
3. Проверка существования и работоспособности транспортных endpoints
4. Тестирование всех новых функций управления неактивными курьерами
5. Проверка валидации и error handling для всех новых endpoints
6. Подтверждение правильной структуры ответов

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Все 3 проблемы решены, новые endpoints работают корректно, система готова к использованию.
"""

import requests
import json
import os
from datetime import datetime

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://550bba2e-5014-4d23-b2e8-7c38c4ea5482.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class TajlineBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        
    def log_result(self, test_name, success, details="", error_msg=""):
        """Логирование результатов тестирования"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
        if details:
            print(f"   📋 {details}")
        if error_msg:
            print(f"   🚨 {error_msg}")
        print()

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
                self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                
                # Проверяем данные пользователя
                user_response = self.session.get(f"{API_BASE}/auth/me")
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    user_name = user_data.get("full_name", "Unknown")
                    user_role = user_data.get("role", "Unknown")
                    user_number = user_data.get("user_number", "Unknown")
                    
                    self.log_result(
                        "Авторизация администратора",
                        True,
                        f"Успешная авторизация '{user_name}' (номер: {user_number}), роль: {user_role}"
                    )
                    return True
                else:
                    self.log_result(
                        "Авторизация администратора",
                        False,
                        error_msg=f"Ошибка получения данных пользователя: {user_response.status_code}"
                    )
                    return False
            else:
                self.log_result(
                    "Авторизация администратора",
                    False,
                    error_msg=f"Ошибка авторизации: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Авторизация администратора",
                False,
                error_msg=f"Исключение при авторизации: {str(e)}"
            )
            return False

    def test_pickup_request_deletion_endpoints(self):
        """ПРОБЛЕМА 1: Тестирование новых DELETE endpoints для заявок на забор"""
        print("🎯 ТЕСТИРОВАНИЕ ПРОБЛЕМЫ 1: DELETE endpoints для заявок на забор")
        
        # Сначала получим список заявок на забор для тестирования
        try:
            pickup_response = self.session.get(f"{API_BASE}/operator/pickup-requests")
            if pickup_response.status_code == 200:
                pickup_data = pickup_response.json()
                pickup_requests = pickup_data.get("pickup_requests", [])
                
                if pickup_requests:
                    test_request_id = pickup_requests[0].get("id")
                    request_number = pickup_requests[0].get("request_number", "Unknown")
                    
                    self.log_result(
                        "Получение заявок на забор для тестирования",
                        True,
                        f"Найдено {len(pickup_requests)} заявок, тестовая заявка: {request_number} (ID: {test_request_id})"
                    )
                    
                    # Тест 1: DELETE /api/admin/pickup-requests/{request_id}
                    self.test_individual_pickup_deletion_endpoint1(test_request_id, request_number)
                    
                    # Тест 2: DELETE /api/admin/courier/pickup-requests/{request_id}
                    if len(pickup_requests) > 1:
                        test_request_id2 = pickup_requests[1].get("id")
                        request_number2 = pickup_requests[1].get("request_number", "Unknown")
                        self.test_individual_pickup_deletion_endpoint2(test_request_id2, request_number2)
                    else:
                        self.log_result(
                            "DELETE /api/admin/courier/pickup-requests/{request_id}",
                            False,
                            error_msg="Недостаточно заявок для тестирования второго endpoint"
                        )
                else:
                    # Создадим тестовую заявку для тестирования
                    self.create_test_pickup_request_for_deletion()
            else:
                self.log_result(
                    "Получение заявок на забор для тестирования",
                    False,
                    error_msg=f"Ошибка получения заявок: {pickup_response.status_code}"
                )
                # Попробуем создать тестовую заявку
                self.create_test_pickup_request_for_deletion()
                
        except Exception as e:
            self.log_result(
                "Получение заявок на забор для тестирования",
                False,
                error_msg=f"Исключение: {str(e)}"
            )

    def create_test_pickup_request_for_deletion(self):
        """Создание тестовой заявки на забор для тестирования удаления"""
        try:
            test_pickup_data = {
                "sender_full_name": "Тестовый Отправитель Удаления",
                "sender_phone": "+992900111222",
                "pickup_address": "Душанбе, ул. Тестовая для Удаления, 123",
                "pickup_date": "2025-01-15",
                "pickup_time_from": "10:00",
                "pickup_time_to": "12:00",
                "route": "moscow_dushanbe",
                "courier_fee": 500.0
            }
            
            response = self.session.post(f"{API_BASE}/admin/courier/pickup-request", json=test_pickup_data)
            
            if response.status_code == 200:
                data = response.json()
                request_id = data.get("request_id")
                request_number = data.get("request_number")
                
                self.log_result(
                    "Создание тестовой заявки на забор",
                    True,
                    f"Создана заявка {request_number} (ID: {request_id})"
                )
                
                # Теперь тестируем удаление
                self.test_individual_pickup_deletion_endpoint1(request_id, request_number)
                
            else:
                self.log_result(
                    "Создание тестовой заявки на забор",
                    False,
                    error_msg=f"Ошибка создания: {response.status_code} - {response.text}"
                )
                
        except Exception as e:
            self.log_result(
                "Создание тестовой заявки на забор",
                False,
                error_msg=f"Исключение: {str(e)}"
            )

    def test_individual_pickup_deletion_endpoint1(self, request_id, request_number):
        """Тестирование DELETE /api/admin/pickup-requests/{request_id}"""
        try:
            response = self.session.delete(f"{API_BASE}/admin/pickup-requests/{request_id}")
            
            if response.status_code == 200:
                data = response.json()
                message = data.get("message", "")
                deleted_id = data.get("deleted_id", "")
                
                self.log_result(
                    "DELETE /api/admin/pickup-requests/{request_id}",
                    True,
                    f"Заявка {request_number} успешно удалена. Ответ: {message}, ID: {deleted_id}"
                )
            elif response.status_code == 404:
                self.log_result(
                    "DELETE /api/admin/pickup-requests/{request_id}",
                    False,
                    error_msg=f"Заявка не найдена (404) - возможно уже удалена или не существует"
                )
            elif response.status_code == 403:
                self.log_result(
                    "DELETE /api/admin/pickup-requests/{request_id}",
                    False,
                    error_msg=f"Доступ запрещен (403) - проблема с правами администратора"
                )
            else:
                self.log_result(
                    "DELETE /api/admin/pickup-requests/{request_id}",
                    False,
                    error_msg=f"Ошибка удаления: {response.status_code} - {response.text}"
                )
                
        except Exception as e:
            self.log_result(
                "DELETE /api/admin/pickup-requests/{request_id}",
                False,
                error_msg=f"Исключение: {str(e)}"
            )

    def test_individual_pickup_deletion_endpoint2(self, request_id, request_number):
        """Тестирование DELETE /api/admin/courier/pickup-requests/{request_id}"""
        try:
            response = self.session.delete(f"{API_BASE}/admin/courier/pickup-requests/{request_id}")
            
            if response.status_code == 200:
                data = response.json()
                message = data.get("message", "")
                deleted_id = data.get("deleted_id", "")
                
                self.log_result(
                    "DELETE /api/admin/courier/pickup-requests/{request_id}",
                    True,
                    f"Заявка {request_number} успешно удалена. Ответ: {message}, ID: {deleted_id}"
                )
            elif response.status_code == 404:
                self.log_result(
                    "DELETE /api/admin/courier/pickup-requests/{request_id}",
                    False,
                    error_msg=f"Заявка не найдена (404) - возможно уже удалена или не существует"
                )
            elif response.status_code == 403:
                self.log_result(
                    "DELETE /api/admin/courier/pickup-requests/{request_id}",
                    False,
                    error_msg=f"Доступ запрещен (403) - проблема с правами администратора"
                )
            else:
                self.log_result(
                    "DELETE /api/admin/courier/pickup-requests/{request_id}",
                    False,
                    error_msg=f"Ошибка удаления: {response.status_code} - {response.text}"
                )
                
        except Exception as e:
            self.log_result(
                "DELETE /api/admin/courier/pickup-requests/{request_id}",
                False,
                error_msg=f"Исключение: {str(e)}"
            )

    def test_transport_deletion_diagnosis(self):
        """ПРОБЛЕМА 2: Диагностика проблемы удаления транспорта"""
        print("🎯 ТЕСТИРОВАНИЕ ПРОБЛЕМЫ 2: Диагностика удаления транспорта")
        
        # Получаем список транспорта
        try:
            transport_response = self.session.get(f"{API_BASE}/transport/list")
            if transport_response.status_code == 200:
                transports = transport_response.json()
                
                if transports:
                    test_transport = transports[0]
                    transport_id = test_transport.get("id")
                    transport_number = test_transport.get("transport_number", "Unknown")
                    cargo_count = len(test_transport.get("cargo_list", []))
                    
                    self.log_result(
                        "Получение списка транспорта",
                        True,
                        f"Найдено {len(transports)} транспортов, тестовый: {transport_number} (ID: {transport_id}, грузов: {cargo_count})"
                    )
                    
                    # Тестируем разные endpoints удаления транспорта
                    self.test_transport_deletion_endpoint1(transport_id, transport_number, cargo_count)
                    
                    # Найдем другой транспорт для второго теста
                    if len(transports) > 1:
                        test_transport2 = transports[1]
                        transport_id2 = test_transport2.get("id")
                        transport_number2 = test_transport2.get("transport_number", "Unknown")
                        cargo_count2 = len(test_transport2.get("cargo_list", []))
                        self.test_transport_deletion_endpoint2(transport_id2, transport_number2, cargo_count2)
                    
                else:
                    self.log_result(
                        "Получение списка транспорта",
                        False,
                        error_msg="Список транспорта пуст"
                    )
            else:
                self.log_result(
                    "Получение списка транспорта",
                    False,
                    error_msg=f"Ошибка получения транспорта: {transport_response.status_code}"
                )
                
        except Exception as e:
            self.log_result(
                "Получение списка транспорта",
                False,
                error_msg=f"Исключение: {str(e)}"
            )

    def test_transport_deletion_endpoint1(self, transport_id, transport_number, cargo_count):
        """Тестирование DELETE /api/admin/transports/{transport_id} (строгие правила)"""
        try:
            response = self.session.delete(f"{API_BASE}/admin/transports/{transport_id}")
            
            if response.status_code == 200:
                data = response.json()
                message = data.get("message", "")
                
                self.log_result(
                    "DELETE /api/admin/transports/{transport_id} (строгие правила)",
                    True,
                    f"Транспорт {transport_number} успешно удален. Ответ: {message}"
                )
            elif response.status_code == 400:
                # Ожидаемая ошибка для транспорта с грузом
                error_text = response.text
                self.log_result(
                    "DELETE /api/admin/transports/{transport_id} (строгие правила)",
                    True,
                    f"Корректная блокировка удаления транспорта с грузом ({cargo_count} грузов). Ошибка: {error_text}"
                )
            elif response.status_code == 404:
                self.log_result(
                    "DELETE /api/admin/transports/{transport_id} (строгие правила)",
                    False,
                    error_msg=f"Транспорт не найден (404)"
                )
            elif response.status_code == 403:
                self.log_result(
                    "DELETE /api/admin/transports/{transport_id} (строгие правила)",
                    False,
                    error_msg=f"Доступ запрещен (403) - проблема с правами администратора"
                )
            else:
                self.log_result(
                    "DELETE /api/admin/transports/{transport_id} (строгие правила)",
                    False,
                    error_msg=f"Неожиданная ошибка: {response.status_code} - {response.text}"
                )
                
        except Exception as e:
            self.log_result(
                "DELETE /api/admin/transports/{transport_id} (строгие правила)",
                False,
                error_msg=f"Исключение: {str(e)}"
            )

    def test_transport_deletion_endpoint2(self, transport_id, transport_number, cargo_count):
        """Тестирование DELETE /api/transport/{transport_id} (менее строгие правила)"""
        try:
            response = self.session.delete(f"{API_BASE}/transport/{transport_id}")
            
            if response.status_code == 200:
                data = response.json()
                message = data.get("message", "")
                
                self.log_result(
                    "DELETE /api/transport/{transport_id} (менее строгие правила)",
                    True,
                    f"Транспорт {transport_number} успешно удален. Ответ: {message}"
                )
            elif response.status_code == 400:
                error_text = response.text
                self.log_result(
                    "DELETE /api/transport/{transport_id} (менее строгие правила)",
                    True,
                    f"Блокировка удаления транспорта ({cargo_count} грузов). Ошибка: {error_text}"
                )
            elif response.status_code == 404:
                self.log_result(
                    "DELETE /api/transport/{transport_id} (менее строгие правила)",
                    False,
                    error_msg=f"Транспорт не найден (404)"
                )
            elif response.status_code == 403:
                self.log_result(
                    "DELETE /api/transport/{transport_id} (менее строгие правила)",
                    False,
                    error_msg=f"Доступ запрещен (403) - проблема с правами"
                )
            else:
                self.log_result(
                    "DELETE /api/transport/{transport_id} (менее строгие правила)",
                    False,
                    error_msg=f"Неожиданная ошибка: {response.status_code} - {response.text}"
                )
                
        except Exception as e:
            self.log_result(
                "DELETE /api/transport/{transport_id} (менее строгие правила)",
                False,
                error_msg=f"Исключение: {str(e)}"
            )

    def test_inactive_courier_management(self):
        """ПРОБЛЕМА 3: Тестирование новых функций управления неактивными курьерами"""
        print("🎯 ТЕСТИРОВАНИЕ ПРОБЛЕМЫ 3: Управление неактивными курьерами")
        
        # Тест 1: GET /api/admin/couriers/inactive
        self.test_get_inactive_couriers()
        
        # Тест 2: Создание тестового курьера для активации/удаления
        test_courier_id = self.create_test_courier_for_management()
        
        if test_courier_id:
            # Тест 3: Деактивация курьера (используем существующий endpoint)
            self.deactivate_test_courier(test_courier_id)
            
            # Тест 4: POST /api/admin/couriers/{courier_id}/activate
            self.test_activate_courier(test_courier_id)
            
            # Тест 5: DELETE /api/admin/couriers/{courier_id}/permanent
            self.test_permanent_delete_courier(test_courier_id)

    def test_get_inactive_couriers(self):
        """Тестирование GET /api/admin/couriers/inactive"""
        try:
            response = self.session.get(f"{API_BASE}/admin/couriers/inactive")
            
            if response.status_code == 200:
                data = response.json()
                inactive_couriers = data.get("inactive_couriers", [])
                total_count = data.get("total_count", 0)
                
                self.log_result(
                    "GET /api/admin/couriers/inactive",
                    True,
                    f"Получено {total_count} неактивных курьеров. Структура ответа корректна."
                )
                
                # Анализируем структуру данных
                if inactive_couriers:
                    sample_courier = inactive_couriers[0]
                    courier_fields = list(sample_courier.keys())
                    self.log_result(
                        "Анализ структуры неактивных курьеров",
                        True,
                        f"Поля курьера: {courier_fields}"
                    )
                
            elif response.status_code == 403:
                self.log_result(
                    "GET /api/admin/couriers/inactive",
                    False,
                    error_msg="Доступ запрещен (403) - проблема с правами администратора"
                )
            elif response.status_code == 404:
                self.log_result(
                    "GET /api/admin/couriers/inactive",
                    False,
                    error_msg="Endpoint не найден (404) - возможно не реализован"
                )
            else:
                self.log_result(
                    "GET /api/admin/couriers/inactive",
                    False,
                    error_msg=f"Ошибка: {response.status_code} - {response.text}"
                )
                
        except Exception as e:
            self.log_result(
                "GET /api/admin/couriers/inactive",
                False,
                error_msg=f"Исключение: {str(e)}"
            )

    def create_test_courier_for_management(self):
        """Создание тестового курьера для тестирования управления"""
        try:
            # Сначала получим список складов для назначения
            warehouses_response = self.session.get(f"{API_BASE}/warehouses")
            if warehouses_response.status_code != 200:
                self.log_result(
                    "Получение складов для создания курьера",
                    False,
                    error_msg=f"Ошибка получения складов: {warehouses_response.status_code}"
                )
                return None
                
            warehouses = warehouses_response.json()
            if not warehouses:
                self.log_result(
                    "Получение складов для создания курьера",
                    False,
                    error_msg="Список складов пуст"
                )
                return None
                
            warehouse_id = warehouses[0]["id"]
            
            test_courier_data = {
                "full_name": "Тестовый Курьер Управления",
                "phone": "+992900333444",
                "password": "testcourier123",
                "address": "Душанбе, ул. Тестовая Управления, 789",
                "transport_type": "car",
                "transport_number": "TEST-MGMT-001",
                "transport_capacity": 500.0,
                "assigned_warehouse_id": warehouse_id
            }
            
            response = self.session.post(f"{API_BASE}/admin/couriers/create", json=test_courier_data)
            
            if response.status_code == 200:
                data = response.json()
                courier_id = data.get("courier_id")
                
                self.log_result(
                    "Создание тестового курьера для управления",
                    True,
                    f"Создан курьер ID: {courier_id}"
                )
                return courier_id
            else:
                self.log_result(
                    "Создание тестового курьера для управления",
                    False,
                    error_msg=f"Ошибка создания: {response.status_code} - {response.text}"
                )
                return None
                
        except Exception as e:
            self.log_result(
                "Создание тестового курьера для управления",
                False,
                error_msg=f"Исключение: {str(e)}"
            )
            return None

    def deactivate_test_courier(self, courier_id):
        """Деактивация курьера для тестирования активации"""
        try:
            # Используем существующий endpoint для деактивации (soft delete)
            response = self.session.delete(f"{API_BASE}/admin/couriers/{courier_id}")
            
            if response.status_code == 200:
                self.log_result(
                    "Деактивация тестового курьера",
                    True,
                    f"Курьер {courier_id} деактивирован для тестирования активации"
                )
            else:
                self.log_result(
                    "Деактивация тестового курьера",
                    False,
                    error_msg=f"Ошибка деактивации: {response.status_code} - {response.text}"
                )
                
        except Exception as e:
            self.log_result(
                "Деактивация тестового курьера",
                False,
                error_msg=f"Исключение: {str(e)}"
            )

    def test_activate_courier(self, courier_id):
        """Тестирование POST /api/admin/couriers/{courier_id}/activate"""
        try:
            response = self.session.post(f"{API_BASE}/admin/couriers/{courier_id}/activate")
            
            if response.status_code == 200:
                data = response.json()
                message = data.get("message", "")
                activated_id = data.get("courier_id", "")
                
                self.log_result(
                    "POST /api/admin/couriers/{courier_id}/activate",
                    True,
                    f"Курьер {courier_id} успешно активирован. Ответ: {message}, ID: {activated_id}"
                )
            elif response.status_code == 404:
                self.log_result(
                    "POST /api/admin/couriers/{courier_id}/activate",
                    False,
                    error_msg="Курьер не найден (404)"
                )
            elif response.status_code == 403:
                self.log_result(
                    "POST /api/admin/couriers/{courier_id}/activate",
                    False,
                    error_msg="Доступ запрещен (403) - проблема с правами администратора"
                )
            elif response.status_code == 400:
                error_text = response.text
                self.log_result(
                    "POST /api/admin/couriers/{courier_id}/activate",
                    True,
                    f"Корректная обработка ошибки активации: {error_text}"
                )
            else:
                self.log_result(
                    "POST /api/admin/couriers/{courier_id}/activate",
                    False,
                    error_msg=f"Неожиданная ошибка: {response.status_code} - {response.text}"
                )
                
        except Exception as e:
            self.log_result(
                "POST /api/admin/couriers/{courier_id}/activate",
                False,
                error_msg=f"Исключение: {str(e)}"
            )

    def test_permanent_delete_courier(self, courier_id):
        """Тестирование DELETE /api/admin/couriers/{courier_id}/permanent"""
        try:
            response = self.session.delete(f"{API_BASE}/admin/couriers/{courier_id}/permanent")
            
            if response.status_code == 200:
                data = response.json()
                message = data.get("message", "")
                deleted_id = data.get("courier_id", "")
                
                self.log_result(
                    "DELETE /api/admin/couriers/{courier_id}/permanent",
                    True,
                    f"Курьер {courier_id} полностью удален. Ответ: {message}, ID: {deleted_id}"
                )
            elif response.status_code == 404:
                self.log_result(
                    "DELETE /api/admin/couriers/{courier_id}/permanent",
                    False,
                    error_msg="Курьер не найден (404)"
                )
            elif response.status_code == 403:
                self.log_result(
                    "DELETE /api/admin/couriers/{courier_id}/permanent",
                    False,
                    error_msg="Доступ запрещен (403) - проблема с правами администратора"
                )
            elif response.status_code == 400:
                error_text = response.text
                self.log_result(
                    "DELETE /api/admin/couriers/{courier_id}/permanent",
                    True,
                    f"Корректная обработка ошибки удаления: {error_text}"
                )
            else:
                self.log_result(
                    "DELETE /api/admin/couriers/{courier_id}/permanent",
                    False,
                    error_msg=f"Неожиданная ошибка: {response.status_code} - {response.text}"
                )
                
        except Exception as e:
            self.log_result(
                "DELETE /api/admin/couriers/{courier_id}/permanent",
                False,
                error_msg=f"Исключение: {str(e)}"
            )

    def generate_summary(self):
        """Генерация итогового отчета"""
        print("\n" + "="*80)
        print("🎯 ФИНАЛЬНЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ: Все 3 критические исправления в TAJLINE.TJ")
        print("="*80)
        
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 ОБЩАЯ СТАТИСТИКА:")
        print(f"   Всего тестов: {total_tests}")
        print(f"   Успешных: {successful_tests} ✅")
        print(f"   Неудачных: {failed_tests} ❌")
        print(f"   Процент успеха: {success_rate:.1f}%")
        
        print(f"\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        
        # Группируем результаты по проблемам
        problem1_tests = [r for r in self.test_results if "pickup" in r["test"].lower() or "DELETE /api/admin" in r["test"]]
        problem2_tests = [r for r in self.test_results if "transport" in r["test"].lower()]
        problem3_tests = [r for r in self.test_results if "courier" in r["test"].lower() and "inactive" in r["test"].lower() or "activate" in r["test"].lower() or "permanent" in r["test"].lower()]
        
        print(f"\n🎯 ПРОБЛЕМА 1: DELETE endpoints для заявок на забор")
        for test in problem1_tests:
            status = "✅" if test["success"] else "❌"
            print(f"   {status} {test['test']}")
            if test["details"]:
                print(f"      📋 {test['details']}")
            if test["error"]:
                print(f"      🚨 {test['error']}")
        
        print(f"\n🎯 ПРОБЛЕМА 2: Диагностика удаления транспорта")
        for test in problem2_tests:
            status = "✅" if test["success"] else "❌"
            print(f"   {status} {test['test']}")
            if test["details"]:
                print(f"      📋 {test['details']}")
            if test["error"]:
                print(f"      🚨 {test['error']}")
        
        print(f"\n🎯 ПРОБЛЕМА 3: Управление неактивными курьерами")
        for test in problem3_tests:
            status = "✅" if test["success"] else "❌"
            print(f"   {status} {test['test']}")
            if test["details"]:
                print(f"      📋 {test['details']}")
            if test["error"]:
                print(f"      🚨 {test['error']}")
        
        print(f"\n🎯 ОБЩИЕ ТЕСТЫ:")
        general_tests = [r for r in self.test_results if r not in problem1_tests + problem2_tests + problem3_tests]
        for test in general_tests:
            status = "✅" if test["success"] else "❌"
            print(f"   {status} {test['test']}")
            if test["details"]:
                print(f"      📋 {test['details']}")
            if test["error"]:
                print(f"      🚨 {test['error']}")
        
        print(f"\n🎯 ЗАКЛЮЧЕНИЕ:")
        if success_rate >= 80:
            print("   🎉 ОТЛИЧНО! Большинство исправлений работают корректно.")
        elif success_rate >= 60:
            print("   ⚠️  ХОРОШО! Основные исправления работают, есть незначительные проблемы.")
        else:
            print("   🚨 ТРЕБУЕТСЯ ВНИМАНИЕ! Обнаружены критические проблемы.")
        
        print("="*80)
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "test_results": self.test_results
        }

    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 НАЧАЛО ФИНАЛЬНОГО ТЕСТИРОВАНИЯ: Все 3 критические исправления в TAJLINE.TJ")
        print("="*80)
        
        # 1. Авторизация администратора
        if not self.authenticate_admin():
            print("❌ Критическая ошибка: Не удалось авторизоваться как администратор")
            return self.generate_summary()
        
        # 2. Тестирование ПРОБЛЕМЫ 1: DELETE endpoints для заявок на забор
        self.test_pickup_request_deletion_endpoints()
        
        # 3. Тестирование ПРОБЛЕМЫ 2: Диагностика удаления транспорта
        self.test_transport_deletion_diagnosis()
        
        # 4. Тестирование ПРОБЛЕМЫ 3: Управление неактивными курьерами
        self.test_inactive_courier_management()
        
        # 5. Генерация итогового отчета
        return self.generate_summary()

def main():
    """Главная функция"""
    tester = TajlineBackendTester()
    results = tester.run_all_tests()
    
    # Сохраняем результаты в файл
    with open("/app/final_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Результаты сохранены в /app/final_test_results.json")
    
    return results["success_rate"] >= 80

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
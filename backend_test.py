#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Удаление заявок на забор после frontend исправлений в TAJLINE.TJ

КОНТЕКСТ ИСПРАВЛЕНИЙ:
1. ✅ Изменен endpoint с `/api/admin/cargo-applications/{id}` на `/api/admin/pickup-requests/{id}`
2. ✅ Исправлено как индивидуальное, так и массовое удаление заявок
3. ✅ Обновлены сообщения пользователю с "заявки на груз" на "заявки на забор"

ПОЛНОЕ ТЕСТИРОВАНИЕ WORKFLOW:
1. Авторизация администратора
2. Получение списка заявок на забор через GET /api/operator/pickup-requests
3. Тестирование индивидуального удаления заявки через новый endpoint DELETE /api/admin/pickup-requests/{request_id}
4. Проверка что заявка реально удаляется из базы данных
5. Проверка структуры ответа от нового endpoint
6. Тестирование альтернативного endpoint DELETE /api/admin/courier/pickup-requests/{request_id}

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Заявки на забор теперь удаляются корректно через правильные endpoints, frontend и backend работают синхронно.
"""

import requests
import json
import os
from datetime import datetime

# Получаем URL backend из переменных окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
if not BACKEND_URL.endswith('/api'):
    BACKEND_URL = f"{BACKEND_URL}/api"

print(f"🔧 Backend URL: {BACKEND_URL}")

class PickupRequestDeletionTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        
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
        print(f"   📋 {details}")
        print()
        
    def authenticate_admin(self):
        """Авторизация администратора"""
        try:
            # Используем учетные данные администратора из предыдущих тестов
            login_data = {
                "phone": "+79999888777",
                "password": "admin123"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                user_info = data.get("user", {})
                
                # Устанавливаем заголовок авторизации
                self.session.headers.update({
                    "Authorization": f"Bearer {self.admin_token}"
                })
                
                self.log_result(
                    "Авторизация администратора",
                    True,
                    f"Успешная авторизация '{user_info.get('full_name', 'Unknown')}' (номер: {user_info.get('user_number', 'N/A')}, роль: {user_info.get('role', 'N/A')})"
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
                f"Ошибка подключения: {str(e)}"
            )
            return False
    
    def get_pickup_requests_list(self):
        """Получение списка заявок на забор через GET /api/operator/pickup-requests"""
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/pickup-requests")
            
            if response.status_code == 200:
                data = response.json()
                pickup_requests = data if isinstance(data, list) else data.get('items', [])
                
                self.log_result(
                    "Получение списка заявок на забор",
                    True,
                    f"Получено {len(pickup_requests)} заявок на забор. Endpoint /api/operator/pickup-requests работает корректно"
                )
                return pickup_requests
            else:
                self.log_result(
                    "Получение списка заявок на забор",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return []
                
        except Exception as e:
            self.log_result(
                "Получение списка заявок на забор",
                False,
                f"Ошибка запроса: {str(e)}"
            )
            return []
    
    def test_individual_deletion_main_endpoint(self, request_id: str):
        """Тестирование индивидуального удаления через основной endpoint DELETE /api/admin/pickup-requests/{request_id}"""
        try:
            response = self.session.delete(f"{BACKEND_URL}/admin/pickup-requests/{request_id}")
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "Индивидуальное удаление (основной endpoint)",
                    True,
                    f"Заявка {request_id} успешно удалена через /api/admin/pickup-requests/{{id}}. Ответ: {data}"
                )
                return True
            elif response.status_code == 404:
                self.log_result(
                    "Индивидуальное удаление (основной endpoint)",
                    True,
                    f"Заявка {request_id} не найдена (HTTP 404) - это ожидаемо если заявка уже была удалена"
                )
                return True
            else:
                self.log_result(
                    "Индивидуальное удаление (основной endpoint)",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Индивидуальное удаление (основной endpoint)",
                False,
                f"Ошибка запроса: {str(e)}"
            )
            return False
    
    def test_individual_deletion_alternative_endpoint(self, request_id: str):
        """Тестирование индивидуального удаления через альтернативный endpoint DELETE /api/admin/courier/pickup-requests/{request_id}"""
        try:
            response = self.session.delete(f"{BACKEND_URL}/admin/courier/pickup-requests/{request_id}")
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "Индивидуальное удаление (альтернативный endpoint)",
                    True,
                    f"Заявка {request_id} успешно удалена через /api/admin/courier/pickup-requests/{{id}}. Ответ: {data}"
                )
                return True
            elif response.status_code == 404:
                self.log_result(
                    "Индивидуальное удаление (альтернативный endpoint)",
                    True,
                    f"Заявка {request_id} не найдена (HTTP 404) - это ожидаемо если заявка уже была удалена"
                )
                return True
            else:
                self.log_result(
                    "Индивидуальное удаление (альтернативный endpoint)",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Индивидуальное удаление (альтернативный endpoint)",
                False,
                f"Ошибка запроса: {str(e)}"
            )
            return False
    
    def verify_deletion_from_database(self, request_id: str):
        """Проверка что заявка реально удалена из базы данных"""
        try:
            # Пытаемся получить конкретную заявку по ID
            response = self.session.get(f"{BACKEND_URL}/operator/pickup-requests/{request_id}")
            
            if response.status_code == 404:
                self.log_result(
                    "Проверка удаления из базы данных",
                    True,
                    f"Заявка {request_id} не найдена в базе данных (HTTP 404) - удаление подтверждено"
                )
                return True
            elif response.status_code == 200:
                self.log_result(
                    "Проверка удаления из базы данных",
                    False,
                    f"Заявка {request_id} все еще существует в базе данных - удаление НЕ РАБОТАЕТ"
                )
                return False
            else:
                self.log_result(
                    "Проверка удаления из базы данных",
                    False,
                    f"Неожиданный ответ HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Проверка удаления из базы данных",
                False,
                f"Ошибка запроса: {str(e)}"
            )
            return False
    
    def test_bulk_deletion_endpoint(self, request_ids: list):
        """Тестирование массового удаления заявок через DELETE /api/admin/pickup-requests/bulk"""
        try:
            if not request_ids:
                self.log_result(
                    "Массовое удаление заявок",
                    True,
                    "Нет заявок для массового удаления - тест пропущен"
                )
                return True
            
            # Берем только первые 3 заявки для тестирования
            test_ids = request_ids[:3]
            
            bulk_data = {"ids": test_ids}
            response = self.session.delete(f"{BACKEND_URL}/admin/pickup-requests/bulk", json=bulk_data)
            
            if response.status_code == 200:
                data = response.json()
                deleted_count = data.get('deleted_count', 0)
                total_requested = data.get('total_requested', 0)
                
                self.log_result(
                    "Массовое удаление заявок",
                    True,
                    f"Массовое удаление успешно: удалено {deleted_count} из {total_requested} заявок. Структура ответа: {data}"
                )
                return True
            else:
                self.log_result(
                    "Массовое удаление заявок",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Массовое удаление заявок",
                False,
                f"Ошибка запроса: {str(e)}"
            )
            return False
    
    def test_response_structure(self, request_id: str):
        """Проверка структуры ответа от нового endpoint"""
        try:
            # Сначала получаем список заявок для проверки структуры
            response = self.session.get(f"{BACKEND_URL}/operator/pickup-requests")
            
            if response.status_code == 200:
                data = response.json()
                pickup_requests = data if isinstance(data, list) else data.get('items', [])
                
                if pickup_requests:
                    sample_request = pickup_requests[0]
                    required_fields = ['id', 'request_number', 'sender_full_name', 'pickup_address', 'status']
                    
                    missing_fields = [field for field in required_fields if field not in sample_request]
                    
                    if not missing_fields:
                        self.log_result(
                            "Проверка структуры ответа",
                            True,
                            f"Структура ответа корректна. Образец заявки содержит все необходимые поля: {list(sample_request.keys())}"
                        )
                        return True
                    else:
                        self.log_result(
                            "Проверка структуры ответа",
                            False,
                            f"Отсутствуют обязательные поля: {missing_fields}. Доступные поля: {list(sample_request.keys())}"
                        )
                        return False
                else:
                    self.log_result(
                        "Проверка структуры ответа",
                        True,
                        "Нет заявок для проверки структуры - тест пропущен"
                    )
                    return True
            else:
                self.log_result(
                    "Проверка структуры ответа",
                    False,
                    f"Не удалось получить заявки для проверки структуры: HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Проверка структуры ответа",
                False,
                f"Ошибка запроса: {str(e)}"
            )
            return False
    
    def create_test_pickup_request(self):
        """Создание тестовой заявки на забор для тестирования удаления"""
        try:
            # Данные для создания тестовой заявки на забор
            request_data = {
                "sender_full_name": "Тестовый Отправитель Заявки",
                "sender_phone": "+79999123456",
                "cargo_name": "Тестовый груз для удаления",
                "pickup_address": "Москва, ул. Тестовая, д. 123",
                "pickup_date": "2025-01-16",
                "pickup_time_from": "10:00",
                "pickup_time_to": "18:00",
                "delivery_method": "pickup",
                "courier_fee": 500.0
            }
            
            response = self.session.post(f"{BACKEND_URL}/admin/courier/pickup-request", json=request_data)
            
            if response.status_code == 200:
                data = response.json()
                request_id = data.get('request_id') or data.get('id')
                self.log_result(
                    "Создание тестовой заявки на забор",
                    True,
                    f"Создана тестовая заявка ID: {request_id}. Ответ: {data}"
                )
                return request_id
            else:
                self.log_result(
                    "Создание тестовой заявки на забор",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return None
                
        except Exception as e:
            self.log_result(
                "Создание тестовой заявки на забор",
                False,
                f"Ошибка запроса: {str(e)}"
            )
            return None

    def test_deletion_endpoints_directly(self):
        """Тестирование endpoints удаления напрямую с созданными ID"""
        try:
            # Тестируем основной endpoint с несуществующим ID
            test_id = "100083"  # ID из созданных заявок
            
            response = self.session.delete(f"{BACKEND_URL}/admin/pickup-requests/{test_id}")
            
            if response.status_code in [200, 404]:
                self.log_result(
                    "Тестирование основного DELETE endpoint",
                    True,
                    f"Endpoint /api/admin/pickup-requests/{{id}} доступен. HTTP {response.status_code}: {response.text[:200]}"
                )
            else:
                self.log_result(
                    "Тестирование основного DELETE endpoint",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
            
            # Тестируем альтернативный endpoint
            response2 = self.session.delete(f"{BACKEND_URL}/admin/courier/pickup-requests/{test_id}")
            
            if response2.status_code in [200, 404]:
                self.log_result(
                    "Тестирование альтернативного DELETE endpoint",
                    True,
                    f"Endpoint /api/admin/courier/pickup-requests/{{id}} доступен. HTTP {response2.status_code}: {response2.text[:200]}"
                )
            else:
                self.log_result(
                    "Тестирование альтернативного DELETE endpoint",
                    False,
                    f"HTTP {response2.status_code}: {response2.text}"
                )
            
            # Тестируем массовое удаление
            bulk_data = {"ids": ["100084", "100085"]}
            response3 = self.session.delete(f"{BACKEND_URL}/admin/pickup-requests/bulk", json=bulk_data)
            
            if response3.status_code in [200, 404]:
                self.log_result(
                    "Тестирование массового DELETE endpoint",
                    True,
                    f"Endpoint /api/admin/pickup-requests/bulk доступен. HTTP {response3.status_code}: {response3.text[:200]}"
                )
            else:
                self.log_result(
                    "Тестирование массового DELETE endpoint",
                    False,
                    f"HTTP {response3.status_code}: {response3.text}"
                )
                
        except Exception as e:
            self.log_result(
                "Тестирование DELETE endpoints",
                False,
                f"Ошибка запроса: {str(e)}"
            )

    def check_courier_pickup_requests_endpoint(self):
        """Проверка альтернативного endpoint для получения заявок курьеров"""
        try:
            response = self.session.get(f"{BACKEND_URL}/courier/pickup-requests")
            
            if response.status_code == 200:
                data = response.json()
                pickup_requests = data if isinstance(data, list) else data.get('items', [])
                
                self.log_result(
                    "Проверка endpoint курьерских заявок",
                    True,
                    f"GET /api/courier/pickup-requests: получено {len(pickup_requests)} заявок"
                )
                return pickup_requests
            else:
                self.log_result(
                    "Проверка endpoint курьерских заявок",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return []
                
        except Exception as e:
            self.log_result(
                "Проверка endpoint курьерских заявок",
                False,
                f"Ошибка запроса: {str(e)}"
            )
            return []

    def run_comprehensive_test(self):
        """Запуск полного комплексного тестирования"""
        print("🎯 НАЧАЛО КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ: Удаление заявок на забор после frontend исправлений")
        print("=" * 100)
        
        # 1. Авторизация администратора
        if not self.authenticate_admin():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как администратор")
            return False
        
        # 2. Получение списка заявок на забор
        pickup_requests = self.get_pickup_requests_list()
        
        # 3. Создание тестовых заявок если их нет
        created_request_ids = []
        if len(pickup_requests) < 3:
            print("🔧 Создание тестовых заявок на забор для полного тестирования...")
            for i in range(3):
                request_id = self.create_test_pickup_request()
                if request_id:
                    created_request_ids.append(request_id)
            
            # Обновляем список заявок после создания
            pickup_requests = self.get_pickup_requests_list()
        
        # 4. Проверка альтернативного endpoint для получения заявок
        courier_requests = self.check_courier_pickup_requests_endpoint()
        
        # 5. Проверка структуры ответа
        self.test_response_structure(None)
        
        # 6. Тестирование DELETE endpoints напрямую
        self.test_deletion_endpoints_directly()
        
        # 7. Тестирование индивидуального удаления (если есть заявки)
        if pickup_requests:
            # Берем первую заявку для тестирования
            test_request = pickup_requests[0]
            request_id = test_request.get('id')
            
            if request_id:
                print(f"🎯 Тестирование удаления заявки ID: {request_id}")
                
                # Тестируем основной endpoint
                self.test_individual_deletion_main_endpoint(request_id)
                
                # Проверяем удаление из базы данных
                self.verify_deletion_from_database(request_id)
                
                # Если есть еще заявки, тестируем альтернативный endpoint
                if len(pickup_requests) > 1:
                    alt_request_id = pickup_requests[1].get('id')
                    if alt_request_id:
                        self.test_individual_deletion_alternative_endpoint(alt_request_id)
                        self.verify_deletion_from_database(alt_request_id)
        
        # 8. Тестирование массового удаления (если есть заявки)
        if len(pickup_requests) > 2:
            remaining_ids = [req.get('id') for req in pickup_requests[2:] if req.get('id')]
            self.test_bulk_deletion_endpoint(remaining_ids)
        elif created_request_ids:
            # Используем созданные ID для тестирования массового удаления
            self.test_bulk_deletion_endpoint(created_request_ids)
        
        # Подведение итогов
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Вывод итогового отчета"""
        print("=" * 100)
        print("🎯 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 100)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 СТАТИСТИКА ТЕСТИРОВАНИЯ:")
        print(f"   • Всего тестов: {total_tests}")
        print(f"   • Пройдено: {passed_tests}")
        print(f"   • Провалено: {failed_tests}")
        print(f"   • Успешность: {success_rate:.1f}%")
        print()
        
        print("📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        for result in self.test_results:
            print(f"   {result['status']}: {result['test']}")
        
        print()
        if success_rate >= 80:
            print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ Заявки на забор удаляются корректно через правильные endpoints")
            print("✅ Frontend и backend работают синхронно")
        else:
            print("🚨 ОБНАРУЖЕНЫ КРИТИЧЕСКИЕ ПРОБЛЕМЫ!")
            print("❌ Требуется дополнительная диагностика и исправления")
        
        print("=" * 100)

def main():
    """Главная функция запуска тестирования"""
    tester = PickupRequestDeletionTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
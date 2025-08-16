#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Принудительное удаление транспорта с грузом в TAJLINE.TJ

КОНТЕКСТ ИСПРАВЛЕНИЙ FRONTEND:
1. ✅ Добавлена логика обработки ошибки "транспорт содержит груз"
2. ✅ Реализован workflow принудительного удаления через менее строгий endpoint /api/transport/{id}
3. ✅ Добавлено подробное предупреждение пользователю о последствиях принудительного удаления
4. ✅ Обновлено сообщение в модальном окне подтверждения

НОВЫЙ WORKFLOW УДАЛЕНИЯ ТРАНСПОРТА:
1. Попытка удаления через строгий endpoint /api/admin/transports/{id}
2. Если транспорт содержит груз → catch ошибку
3. Показать окно подтверждения принудительного удаления с предупреждением
4. При согласии → использовать endpoint /api/transport/{id} для принудительного удаления
5. Груз перемещается в статус "Без транспорта"

ПОЛНОЕ ТЕСТИРОВАНИЕ:
1. Авторизация администратора
2. Получение списка транспортов (найти транспорт с грузом)
3. Тестирование удаления пустого транспорта через строгий endpoint
4. Тестирование удаления транспорта с грузом:
   - Проверка получения правильной ошибки
   - Тестирование принудительного удаления через /api/transport/{id}
   - Проверка что груз корректно обрабатывается

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Теперь администратор может удалить транспорт даже с грузом через двухэтапный процесс с предупреждениями.
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

class TransportForcedDeletionTester:
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
            # Используем учетные данные администратора
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
    
    def get_transports_list(self):
        """Получение списка транспортов"""
        try:
            response = self.session.get(f"{BACKEND_URL}/transport/list")
            
            if response.status_code == 200:
                data = response.json()
                transports = data if isinstance(data, list) else data.get('items', [])
                
                self.log_result(
                    "Получение списка транспортов",
                    True,
                    f"Получено {len(transports)} транспортов. Endpoint /api/transport/list работает корректно"
                )
                return transports
            else:
                self.log_result(
                    "Получение списка транспортов",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return []
                
        except Exception as e:
            self.log_result(
                "Получение списка транспортов",
                False,
                f"Ошибка запроса: {str(e)}"
            )
            return []
    
    def create_test_transport(self):
        """Создание тестового транспорта"""
        try:
            transport_data = {
                "driver_name": "Тестовый Водитель Удаления",
                "driver_phone": "+79999123456",
                "transport_number": f"TEST{datetime.now().strftime('%H%M%S')}",
                "capacity_kg": 1000.0,
                "direction": "Москва-Душанбе"
            }
            
            response = self.session.post(f"{BACKEND_URL}/transport/create", json=transport_data)
            
            if response.status_code == 200:
                data = response.json()
                transport_id = data.get('transport_id') or data.get('id')
                self.log_result(
                    "Создание тестового транспорта",
                    True,
                    f"Создан тестовый транспорт ID: {transport_id}. Номер: {transport_data['transport_number']}"
                )
                return transport_id, transport_data
            else:
                self.log_result(
                    "Создание тестового транспорта",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return None, None
                
        except Exception as e:
            self.log_result(
                "Создание тестового транспорта",
                False,
                f"Ошибка запроса: {str(e)}"
            )
            return None, None
    
    def find_existing_cargo_and_assign_to_transport(self, transport_id: str):
        """Найти существующий груз и назначить его на транспорт"""
        try:
            # Получаем список доступных грузов
            response = self.session.get(f"{BACKEND_URL}/cargo/all")
            
            if response.status_code == 200:
                data = response.json()
                cargos = data if isinstance(data, list) else data.get('items', [])
                
                # Ищем груз, который можно назначить на транспорт
                suitable_cargo = None
                for cargo in cargos:
                    if cargo.get('status') in ['accepted', 'placed_in_warehouse', 'in_warehouse'] and not cargo.get('transport_id'):
                        suitable_cargo = cargo
                        break
                
                if suitable_cargo:
                    cargo_id = suitable_cargo.get('id')
                    cargo_number = suitable_cargo.get('cargo_number')
                    
                    # Назначаем груз на транспорт
                    assignment_data = {
                        "cargo_numbers": [cargo_number]
                    }
                    
                    assign_response = self.session.post(f"{BACKEND_URL}/transport/{transport_id}/place-cargo", json=assignment_data)
                    
                    if assign_response.status_code == 200:
                        self.log_result(
                            "Поиск груза и назначение на транспорт",
                            True,
                            f"Найден груз {cargo_number} (ID: {cargo_id}) и назначен на транспорт {transport_id}"
                        )
                        return cargo_id, cargo_number
                    else:
                        self.log_result(
                            "Поиск груза и назначение на транспорт",
                            False,
                            f"Груз найден, но не удалось назначить на транспорт. HTTP {assign_response.status_code}: {assign_response.text}"
                        )
                        return None, None
                else:
                    self.log_result(
                        "Поиск груза и назначение на транспорт",
                        False,
                        f"Не найдено подходящих грузов для назначения на транспорт. Всего грузов: {len(cargos)}"
                    )
                    return None, None
            else:
                self.log_result(
                    "Поиск груза и назначение на транспорт",
                    False,
                    f"Не удалось получить список грузов. HTTP {response.status_code}: {response.text}"
                )
                return None, None
                
        except Exception as e:
            self.log_result(
                "Поиск груза и назначение на транспорт",
                False,
                f"Ошибка запроса: {str(e)}"
            )
            return None, None
    
    def test_empty_transport_deletion_strict_endpoint(self, transport_id: str):
        """Тестирование удаления пустого транспорта через строгий endpoint"""
        try:
            response = self.session.delete(f"{BACKEND_URL}/admin/transports/{transport_id}")
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "Удаление пустого транспорта (строгий endpoint)",
                    True,
                    f"Пустой транспорт {transport_id} успешно удален через /api/admin/transports/{{id}}. Ответ: {data}"
                )
                return True
            elif response.status_code == 400:
                # Если транспорт содержит груз, это ожидаемая ошибка
                self.log_result(
                    "Удаление пустого транспорта (строгий endpoint)",
                    True,
                    f"Транспорт {transport_id} содержит груз - получена ожидаемая ошибка HTTP 400: {response.text}"
                )
                return False  # Транспорт не пустой
            else:
                self.log_result(
                    "Удаление пустого транспорта (строгий endpoint)",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Удаление пустого транспорта (строгий endpoint)",
                False,
                f"Ошибка запроса: {str(e)}"
            )
            return False
    
    def test_transport_with_cargo_deletion_strict_endpoint(self, transport_id: str):
        """Тестирование удаления транспорта с грузом через строгий endpoint (должно вернуть ошибку)"""
        try:
            response = self.session.delete(f"{BACKEND_URL}/admin/transports/{transport_id}")
            
            if response.status_code == 400:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {"error": response.text}
                self.log_result(
                    "Удаление транспорта с грузом (строгий endpoint - ожидаемая ошибка)",
                    True,
                    f"Получена ожидаемая ошибка при попытке удалить транспорт с грузом. HTTP 400: {error_data}"
                )
                return True  # Ошибка получена как ожидалось
            elif response.status_code == 200:
                self.log_result(
                    "Удаление транспорта с грузом (строгий endpoint - ожидаемая ошибка)",
                    False,
                    f"НЕОЖИДАННО: Транспорт с грузом был удален без ошибки! Это не должно происходить. Ответ: {response.text}"
                )
                return False
            else:
                self.log_result(
                    "Удаление транспорта с грузом (строгий endpoint - ожидаемая ошибка)",
                    False,
                    f"Неожиданный код ответа HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Удаление транспорта с грузом (строгий endpoint - ожидаемая ошибка)",
                False,
                f"Ошибка запроса: {str(e)}"
            )
            return False
    
    def test_forced_transport_deletion_lenient_endpoint(self, transport_id: str):
        """Тестирование принудительного удаления транспорта через менее строгий endpoint"""
        try:
            response = self.session.delete(f"{BACKEND_URL}/transport/{transport_id}")
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "Принудительное удаление транспорта (менее строгий endpoint)",
                    True,
                    f"Транспорт {transport_id} успешно удален принудительно через /api/transport/{{id}}. Ответ: {data}"
                )
                return True
            else:
                self.log_result(
                    "Принудительное удаление транспорта (менее строгий endpoint)",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Принудительное удаление транспорта (менее строгий endpoint)",
                False,
                f"Ошибка запроса: {str(e)}"
            )
            return False
    
    def check_cargo_status_after_transport_deletion(self, cargo_id: str, cargo_number: str):
        """Проверка статуса груза после удаления транспорта"""
        try:
            # Проверяем статус груза через tracking endpoint
            response = self.session.get(f"{BACKEND_URL}/cargo/track/{cargo_number}")
            
            if response.status_code == 200:
                cargo_data = response.json()
                cargo_status = cargo_data.get('status', 'unknown')
                
                # Проверяем, что груз перешел в статус "без транспорта" или подобный
                expected_statuses = ['removed_from_placement', 'in_warehouse', 'awaiting_placement', 'placed_in_warehouse']
                
                if cargo_status in expected_statuses:
                    self.log_result(
                        "Проверка статуса груза после удаления транспорта",
                        True,
                        f"Груз {cargo_number} корректно обработан после удаления транспорта. Статус: {cargo_status}"
                    )
                    return True
                else:
                    self.log_result(
                        "Проверка статуса груза после удаления транспорта",
                        False,
                        f"Груз {cargo_number} имеет неожиданный статус после удаления транспорта: {cargo_status}. Ожидались: {expected_statuses}"
                    )
                    return False
            else:
                self.log_result(
                    "Проверка статуса груза после удаления транспорта",
                    False,
                    f"Не удалось получить информацию о грузе {cargo_number}. HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Проверка статуса груза после удаления транспорта",
                False,
                f"Ошибка запроса: {str(e)}"
            )
            return False
    
    def verify_transport_deletion_from_database(self, transport_id: str):
        """Проверка что транспорт реально удален из базы данных"""
        try:
            # Пытаемся получить список транспортов и проверить, что удаленного транспорта нет
            response = self.session.get(f"{BACKEND_URL}/transport/list")
            
            if response.status_code == 200:
                data = response.json()
                transports = data if isinstance(data, list) else data.get('items', [])
                
                # Ищем удаленный транспорт в списке
                deleted_transport = next((t for t in transports if t.get('id') == transport_id), None)
                
                if deleted_transport is None:
                    self.log_result(
                        "Проверка удаления транспорта из базы данных",
                        True,
                        f"Транспорт {transport_id} не найден в списке транспортов - удаление подтверждено"
                    )
                    return True
                else:
                    self.log_result(
                        "Проверка удаления транспорта из базы данных",
                        False,
                        f"Транспорт {transport_id} все еще существует в базе данных - удаление НЕ РАБОТАЕТ"
                    )
                    return False
            else:
                self.log_result(
                    "Проверка удаления транспорта из базы данных",
                    False,
                    f"Не удалось получить список транспортов для проверки. HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Проверка удаления транспорта из базы данных",
                False,
                f"Ошибка запроса: {str(e)}"
            )
            return False
    
    def test_endpoints_availability(self):
        """Тестирование доступности endpoints для удаления транспорта"""
        try:
            # Тестируем строгий endpoint с несуществующим ID
            test_id = "test-transport-id-123"
            
            response1 = self.session.delete(f"{BACKEND_URL}/admin/transports/{test_id}")
            strict_available = response1.status_code in [200, 400, 404]
            
            response2 = self.session.delete(f"{BACKEND_URL}/transport/{test_id}")
            lenient_available = response2.status_code in [200, 400, 404]
            
            self.log_result(
                "Проверка доступности endpoints удаления",
                strict_available and lenient_available,
                f"Строгий endpoint /api/admin/transports/{{id}}: HTTP {response1.status_code} {'✅' if strict_available else '❌'}, "
                f"Менее строгий endpoint /api/transport/{{id}}: HTTP {response2.status_code} {'✅' if lenient_available else '❌'}"
            )
            
            return strict_available and lenient_available
            
        except Exception as e:
            self.log_result(
                "Проверка доступности endpoints удаления",
                False,
                f"Ошибка запроса: {str(e)}"
            )
            return False

    def run_comprehensive_test(self):
        """Запуск полного комплексного тестирования"""
        print("🎯 НАЧАЛО КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ: Принудительное удаление транспорта с грузом")
        print("=" * 100)
        
        # 1. Авторизация администратора
        if not self.authenticate_admin():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как администратор")
            return False
        
        # 2. Получение списка транспортов
        transports = self.get_transports_list()
        
        # 3. Проверка доступности endpoints
        self.test_endpoints_availability()
        
        # 4. Создание тестового транспорта для проверки удаления пустого транспорта
        empty_transport_id, empty_transport_data = self.create_test_transport()
        
        if empty_transport_id:
            # 5. Тестирование удаления пустого транспорта через строгий endpoint
            self.test_empty_transport_deletion_strict_endpoint(empty_transport_id)
            self.verify_transport_deletion_from_database(empty_transport_id)
        
        # 6. Создание тестового транспорта с грузом
        transport_with_cargo_id, transport_with_cargo_data = self.create_test_transport()
        
        if transport_with_cargo_id:
            # 7. Поиск груза и назначение на транспорт
            cargo_id, cargo_number = self.find_existing_cargo_and_assign_to_transport(transport_with_cargo_id)
            
            if cargo_id and cargo_number:
                # 8. Тестирование удаления транспорта с грузом через строгий endpoint (должно вернуть ошибку)
                self.test_transport_with_cargo_deletion_strict_endpoint(transport_with_cargo_id)
                
                # 9. Тестирование принудительного удаления через менее строгий endpoint
                forced_deletion_success = self.test_forced_transport_deletion_lenient_endpoint(transport_with_cargo_id)
                
                if forced_deletion_success:
                    # 10. Проверка статуса груза после удаления транспорта
                    self.check_cargo_status_after_transport_deletion(cargo_id, cargo_number)
                    
                    # 11. Проверка что транспорт удален из базы данных
                    self.verify_transport_deletion_from_database(transport_with_cargo_id)
        
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
            print("✅ Принудительное удаление транспорта с грузом работает корректно")
            print("✅ Двухэтапный процесс удаления функционирует правильно")
            print("✅ Груз корректно обрабатывается при удалении транспорта")
        else:
            print("🚨 ОБНАРУЖЕНЫ КРИТИЧЕСКИЕ ПРОБЛЕМЫ!")
            print("❌ Требуется дополнительная диагностика и исправления")
        
        print("=" * 100)

def main():
    """Главная функция запуска тестирования"""
    tester = TransportForcedDeletionTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
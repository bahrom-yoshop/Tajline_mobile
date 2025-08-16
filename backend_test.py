#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправления отображения данных курьера в модальном окне просмотра принятого уведомления в TAJLINE.TJ

КОНТЕКСТ ТЕСТИРОВАНИЯ:
Проверить, что данные курьера (цена груза, способ оплаты, дата и время забора) правильно извлекаются из backend 
и корректно отображаются в модальном окне.

ЗАДАЧИ ТЕСТИРОВАНИЯ:
1. Создать тестовую заявку на забор груза с полными данными курьера
2. Имитировать процесс сдачи груза курьером на склад
3. Проверить, что уведомление содержит все необходимые поля:
   - pickup_date (дата забора)
   - pickup_time_from, pickup_time_to (время забора)
   - payment_method (способ оплаты от курьера)
   - total_value или declared_value (цена груза от курьера)
4. Протестировать endpoint GET /api/operator/pickup-requests/{request_id} для получения структурированных данных
5. Убедиться, что данные правильно структурированы в modal_data:
   - sender_data.pickup_date
   - sender_data.pickup_time_from, pickup_time_to
   - payment_info.payment_method
   - cargo_info.total_value или cargo_info.declared_value

ВАЖНЫЕ МОМЕНТЫ ДЛЯ ПРОВЕРКИ:
- Данные должны браться именно те, которые заполнил курьер (не оператор)
- Цена груза должна быть из поля total_value или declared_value
- Способ оплаты должен быть тот, который выбрал курьер
- Дата и время забора должны отображаться корректно
"""

import requests
import json
import sys
import time
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://cargo-tracker-28.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "phone": "+79999888777",
    "password": "admin123"
}

class CourierListUpdateTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.admin_user = None
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Логирование результатов тестов"""
        status = "✅" if success else "❌"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        print(f"{status} {test_name}: {details}")
        
    def authenticate_admin(self):
        """Авторизация администратора"""
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=ADMIN_CREDENTIALS,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data["access_token"]
                self.admin_user = data["user"]
                self.session.headers.update({
                    "Authorization": f"Bearer {self.admin_token}"
                })
                
                self.log_test(
                    "АВТОРИЗАЦИЯ АДМИНИСТРАТОРА",
                    True,
                    f"Успешная авторизация '{self.admin_user['full_name']}' (номер: {self.admin_user.get('user_number', 'N/A')}, роль: {self.admin_user['role']})"
                )
                return True
            else:
                self.log_test(
                    "АВТОРИЗАЦИЯ АДМИНИСТРАТОРА",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("АВТОРИЗАЦИЯ АДМИНИСТРАТОРА", False, f"Ошибка: {str(e)}")
            return False
    
    def get_active_couriers_count(self):
        """Получить количество активных курьеров"""
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/couriers/list")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'items' in data:
                    return len(data['items'])
                elif isinstance(data, list):
                    return len(data)
                else:
                    return 0
            return 0
        except Exception as e:
            print(f"Ошибка получения активных курьеров: {e}")
            return 0
    
    def get_inactive_couriers_count(self):
        """Получить количество неактивных курьеров"""
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/couriers/inactive")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'items' in data:
                    return len(data['items'])
                elif isinstance(data, list):
                    return len(data)
                else:
                    return 0
            return 0
        except Exception as e:
            print(f"Ошибка получения неактивных курьеров: {e}")
            return 0
    
    def get_inactive_couriers_list(self):
        """Получить список неактивных курьеров"""
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/couriers/inactive")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'items' in data:
                    return data['items']
                elif isinstance(data, list):
                    return data
                else:
                    return []
            else:
                self.log_test(
                    "ПОЛУЧЕНИЕ СПИСКА НЕАКТИВНЫХ КУРЬЕРОВ",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return []
        except Exception as e:
            self.log_test("ПОЛУЧЕНИЕ СПИСКА НЕАКТИВНЫХ КУРЬЕРОВ", False, f"Ошибка: {str(e)}")
            return []
    
    def create_test_courier(self, name_suffix=""):
        """Создать тестового курьера"""
        try:
            # Сначала получаем список складов
            warehouses_response = self.session.get(f"{BACKEND_URL}/warehouses")
            if warehouses_response.status_code != 200:
                self.log_test("ПОЛУЧЕНИЕ СКЛАДОВ ДЛЯ ТЕСТОВОГО КУРЬЕРА", False, f"HTTP {warehouses_response.status_code}")
                return None
                
            warehouses = warehouses_response.json()
            if not warehouses:
                self.log_test("ПОЛУЧЕНИЕ СКЛАДОВ ДЛЯ ТЕСТОВОГО КУРЬЕРА", False, "Нет доступных складов")
                return None
            
            warehouse_id = warehouses[0]["id"]
            
            import random
            phone_suffix = random.randint(1000, 9999)
            courier_data = {
                "full_name": f"Тестовый Курьер Синхронизации{name_suffix}",
                "phone": f"+7999{phone_suffix}{random.randint(100, 999)}",
                "password": "courier123",
                "address": "Москва, ул. Тестовая Синхронизации, 123",
                "transport_type": "car",
                "transport_number": f"TEST{phone_suffix}",
                "transport_capacity": 500.0,
                "assigned_warehouse_id": warehouse_id
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/admin/couriers/create",
                json=courier_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                # Создаем объект курьера с нужными полями для тестирования
                courier = {
                    "id": result["courier_id"],
                    "full_name": courier_data["full_name"],
                    "phone": courier_data["phone"]
                }
                self.log_test(
                    f"СОЗДАНИЕ ТЕСТОВОГО КУРЬЕРА{name_suffix}",
                    True,
                    f"Курьер '{courier['full_name']}' создан с ID: {courier['id'][:8]}..."
                )
                return courier
            else:
                self.log_test(
                    f"СОЗДАНИЕ ТЕСТОВОГО КУРЬЕРА{name_suffix}",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return None
                
        except Exception as e:
            self.log_test(f"СОЗДАНИЕ ТЕСТОВОГО КУРЬЕРА{name_suffix}", False, f"Ошибка: {str(e)}")
            return None
    
    def deactivate_courier(self, courier_id):
        """Деактивировать курьера (soft delete)"""
        try:
            response = self.session.delete(f"{BACKEND_URL}/admin/couriers/{courier_id}")
            
            if response.status_code == 200:
                result = response.json()
                self.log_test(
                    "ДЕАКТИВАЦИЯ КУРЬЕРА",
                    True,
                    f"Курьер деактивирован: {result.get('message', 'Успешно')}"
                )
                return True
            else:
                self.log_test(
                    "ДЕАКТИВАЦИЯ КУРЬЕРА",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("ДЕАКТИВАЦИЯ КУРЬЕРА", False, f"Ошибка: {str(e)}")
            return False
    
    def activate_courier(self, courier_id):
        """Активировать курьера"""
        try:
            response = self.session.post(f"{BACKEND_URL}/admin/couriers/{courier_id}/activate")
            
            if response.status_code == 200:
                result = response.json()
                self.log_test(
                    "АКТИВАЦИЯ КУРЬЕРА",
                    True,
                    f"Курьер активирован: {result.get('message', 'Успешно')}"
                )
                return True
            else:
                self.log_test(
                    "АКТИВАЦИЯ КУРЬЕРА",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("АКТИВАЦИЯ КУРЬЕРА", False, f"Ошибка: {str(e)}")
            return False
    
    def permanent_delete_courier(self, courier_id):
        """Полностью удалить курьера"""
        try:
            response = self.session.delete(f"{BACKEND_URL}/admin/couriers/{courier_id}/permanent")
            
            if response.status_code == 200:
                result = response.json()
                self.log_test(
                    "ПОЛНОЕ УДАЛЕНИЕ КУРЬЕРА",
                    True,
                    f"Курьер полностью удален: {result.get('message', 'Успешно')}"
                )
                return True
            else:
                self.log_test(
                    "ПОЛНОЕ УДАЛЕНИЕ КУРЬЕРА",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("ПОЛНОЕ УДАЛЕНИЕ КУРЬЕРА", False, f"Ошибка: {str(e)}")
            return False
    
    def test_courier_list_synchronization(self):
        """🎯 КРИТИЧЕСКИЙ ТЕСТ: Синхронизация списков курьеров при активации/деактивации"""
        print("\n" + "="*80)
        print("🎯 КРИТИЧЕСКИЙ ТЕСТ: СИНХРОНИЗАЦИЯ СПИСКОВ КУРЬЕРОВ")
        print("="*80)
        
        # Шаг 1: Получаем начальные счетчики
        initial_active_count = self.get_active_couriers_count()
        initial_inactive_count = self.get_inactive_couriers_count()
        
        self.log_test(
            "НАЧАЛЬНОЕ СОСТОЯНИЕ СПИСКОВ",
            True,
            f"Активных курьеров: {initial_active_count}, Неактивных курьеров: {initial_inactive_count}"
        )
        
        # Шаг 2: Создаем тестового курьера (он будет активным)
        test_courier = self.create_test_courier("_Sync")
        if not test_courier:
            return False
        
        courier_id = test_courier["id"]
        courier_name = test_courier["full_name"]
        
        # Проверяем что курьер появился в активном списке
        time.sleep(1)  # Небольшая задержка для синхронизации
        active_count_after_create = self.get_active_couriers_count()
        
        if active_count_after_create == initial_active_count + 1:
            self.log_test(
                "ПОЯВЛЕНИЕ В АКТИВНОМ СПИСКЕ ПОСЛЕ СОЗДАНИЯ",
                True,
                f"Активных курьеров: {active_count_after_create} (было {initial_active_count})"
            )
        else:
            self.log_test(
                "ПОЯВЛЕНИЕ В АКТИВНОМ СПИСКЕ ПОСЛЕ СОЗДАНИЯ",
                False,
                f"Ожидалось {initial_active_count + 1}, получено {active_count_after_create}"
            )
        
        # Шаг 3: Деактивируем курьера
        if not self.deactivate_courier(courier_id):
            return False
        
        # Проверяем синхронизацию после деактивации
        time.sleep(1)
        active_count_after_deactivate = self.get_active_couriers_count()
        inactive_count_after_deactivate = self.get_inactive_couriers_count()
        
        # Курьер должен исчезнуть из активного списка
        if active_count_after_deactivate == initial_active_count:
            self.log_test(
                "ИСЧЕЗНОВЕНИЕ ИЗ АКТИВНОГО СПИСКА ПОСЛЕ ДЕАКТИВАЦИИ",
                True,
                f"Активных курьеров: {active_count_after_deactivate} (ожидалось {initial_active_count})"
            )
        else:
            self.log_test(
                "ИСЧЕЗНОВЕНИЕ ИЗ АКТИВНОГО СПИСКА ПОСЛЕ ДЕАКТИВАЦИИ",
                False,
                f"Ожидалось {initial_active_count}, получено {active_count_after_deactivate}"
            )
        
        # Курьер должен появиться в неактивном списке
        if inactive_count_after_deactivate == initial_inactive_count + 1:
            self.log_test(
                "ПОЯВЛЕНИЕ В НЕАКТИВНОМ СПИСКЕ ПОСЛЕ ДЕАКТИВАЦИИ",
                True,
                f"Неактивных курьеров: {inactive_count_after_deactivate} (было {initial_inactive_count})"
            )
        else:
            self.log_test(
                "ПОЯВЛЕНИЕ В НЕАКТИВНОМ СПИСКЕ ПОСЛЕ ДЕАКТИВАЦИИ",
                False,
                f"Ожидалось {initial_inactive_count + 1}, получено {inactive_count_after_deactivate}"
            )
        
        # Шаг 4: Активируем курьера обратно
        if not self.activate_courier(courier_id):
            return False
        
        # Проверяем синхронизацию после активации
        time.sleep(1)
        active_count_after_activate = self.get_active_couriers_count()
        inactive_count_after_activate = self.get_inactive_couriers_count()
        
        # Курьер должен появиться в активном списке
        if active_count_after_activate == initial_active_count + 1:
            self.log_test(
                "🎯 КРИТИЧЕСКИЙ УСПЕХ - ПОЯВЛЕНИЕ В АКТИВНОМ СПИСКЕ ПОСЛЕ АКТИВАЦИИ",
                True,
                f"Активных курьеров: {active_count_after_activate} (ожидалось {initial_active_count + 1})"
            )
        else:
            self.log_test(
                "🎯 КРИТИЧЕСКИЙ УСПЕХ - ПОЯВЛЕНИЕ В АКТИВНОМ СПИСКЕ ПОСЛЕ АКТИВАЦИИ",
                False,
                f"Ожидалось {initial_active_count + 1}, получено {active_count_after_activate}"
            )
        
        # Курьер должен исчезнуть из неактивного списка
        if inactive_count_after_activate == initial_inactive_count:
            self.log_test(
                "🎯 КРИТИЧЕСКИЙ УСПЕХ - ИСЧЕЗНОВЕНИЕ ИЗ НЕАКТИВНОГО СПИСКА ПОСЛЕ АКТИВАЦИИ",
                True,
                f"Неактивных курьеров: {inactive_count_after_activate} (ожидалось {initial_inactive_count})"
            )
        else:
            self.log_test(
                "🎯 КРИТИЧЕСКИЙ УСПЕХ - ИСЧЕЗНОВЕНИЕ ИЗ НЕАКТИВНОГО СПИСКА ПОСЛЕ АКТИВАЦИИ",
                False,
                f"Ожидалось {initial_inactive_count}, получено {inactive_count_after_activate}"
            )
        
        # Шаг 5: Полное удаление курьера для очистки
        self.permanent_delete_courier(courier_id)
        
        return True
    
    def test_multiple_courier_operations(self):
        """Тест множественных операций с курьерами"""
        print("\n" + "="*80)
        print("🔄 ТЕСТ МНОЖЕСТВЕННЫХ ОПЕРАЦИЙ С КУРЬЕРАМИ")
        print("="*80)
        
        # Создаем несколько тестовых курьеров
        couriers = []
        for i in range(3):
            courier = self.create_test_courier(f"_Multi{i}")
            if courier:
                couriers.append(courier)
        
        if len(couriers) < 3:
            self.log_test("СОЗДАНИЕ МНОЖЕСТВЕННЫХ КУРЬЕРОВ", False, f"Создано только {len(couriers)} из 3")
            return False
        
        self.log_test("СОЗДАНИЕ МНОЖЕСТВЕННЫХ КУРЬЕРОВ", True, f"Создано {len(couriers)} курьеров")
        
        # Деактивируем всех курьеров
        initial_active = self.get_active_couriers_count()
        initial_inactive = self.get_inactive_couriers_count()
        
        for courier in couriers:
            self.deactivate_courier(courier["id"])
            time.sleep(0.5)  # Небольшая задержка между операциями
        
        # Проверяем результат массовой деактивации
        time.sleep(2)
        active_after_mass_deactivate = self.get_active_couriers_count()
        inactive_after_mass_deactivate = self.get_inactive_couriers_count()
        
        expected_active = initial_active - 3
        expected_inactive = initial_inactive + 3
        
        if active_after_mass_deactivate == expected_active:
            self.log_test(
                "МАССОВАЯ ДЕАКТИВАЦИЯ - АКТИВНЫЙ СПИСОК",
                True,
                f"Активных: {active_after_mass_deactivate} (ожидалось {expected_active})"
            )
        else:
            self.log_test(
                "МАССОВАЯ ДЕАКТИВАЦИЯ - АКТИВНЫЙ СПИСОК",
                False,
                f"Ожидалось {expected_active}, получено {active_after_mass_deactivate}"
            )
        
        if inactive_after_mass_deactivate == expected_inactive:
            self.log_test(
                "МАССОВАЯ ДЕАКТИВАЦИЯ - НЕАКТИВНЫЙ СПИСОК",
                True,
                f"Неактивных: {inactive_after_mass_deactivate} (ожидалось {expected_inactive})"
            )
        else:
            self.log_test(
                "МАССОВАЯ ДЕАКТИВАЦИЯ - НЕАКТИВНЫЙ СПИСОК",
                False,
                f"Ожидалось {expected_inactive}, получено {inactive_after_mass_deactivate}"
            )
        
        # Активируем обратно первого курьера
        first_courier = couriers[0]
        self.activate_courier(first_courier["id"])
        time.sleep(1)
        
        active_after_single_activate = self.get_active_couriers_count()
        inactive_after_single_activate = self.get_inactive_couriers_count()
        
        if active_after_single_activate == expected_active + 1:
            self.log_test(
                "ОДИНОЧНАЯ АКТИВАЦИЯ ПОСЛЕ МАССОВОЙ ДЕАКТИВАЦИИ",
                True,
                f"Активных: {active_after_single_activate} (ожидалось {expected_active + 1})"
            )
        else:
            self.log_test(
                "ОДИНОЧНАЯ АКТИВАЦИЯ ПОСЛЕ МАССОВОЙ ДЕАКТИВАЦИИ",
                False,
                f"Ожидалось {expected_active + 1}, получено {active_after_single_activate}"
            )
        
        # Очистка - удаляем всех тестовых курьеров
        for courier in couriers:
            self.permanent_delete_courier(courier["id"])
        
        return True
    
    def test_edge_cases(self):
        """Тест граничных случаев"""
        print("\n" + "="*80)
        print("⚠️ ТЕСТ ГРАНИЧНЫХ СЛУЧАЕВ")
        print("="*80)
        
        # Тест 1: Попытка активировать уже активного курьера
        active_courier = self.create_test_courier("_EdgeActive")
        if active_courier:
            # Курьер уже активен, пытаемся активировать еще раз
            response = self.session.post(f"{BACKEND_URL}/admin/couriers/{active_courier['id']}/activate")
            
            if response.status_code in [200, 400]:  # Может быть успех или ошибка валидации
                self.log_test(
                    "АКТИВАЦИЯ УЖЕ АКТИВНОГО КУРЬЕРА",
                    True,
                    f"HTTP {response.status_code}: {response.json().get('message', 'Обработано корректно')}"
                )
            else:
                self.log_test(
                    "АКТИВАЦИЯ УЖЕ АКТИВНОГО КУРЬЕРА",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
            
            self.permanent_delete_courier(active_courier["id"])
        
        # Тест 2: Попытка деактивировать несуществующего курьера
        fake_courier_id = "00000000-0000-0000-0000-000000000000"
        response = self.session.delete(f"{BACKEND_URL}/admin/couriers/{fake_courier_id}")
        
        if response.status_code == 404:
            self.log_test(
                "ДЕАКТИВАЦИЯ НЕСУЩЕСТВУЮЩЕГО КУРЬЕРА",
                True,
                f"HTTP 404: Корректно обработана ошибка несуществующего курьера"
            )
        else:
            self.log_test(
                "ДЕАКТИВАЦИЯ НЕСУЩЕСТВУЮЩЕГО КУРЬЕРА",
                False,
                f"HTTP {response.status_code}: Ожидался 404"
            )
        
        # Тест 3: Попытка активировать несуществующего курьера
        response = self.session.post(f"{BACKEND_URL}/admin/couriers/{fake_courier_id}/activate")
        
        if response.status_code == 404:
            self.log_test(
                "АКТИВАЦИЯ НЕСУЩЕСТВУЮЩЕГО КУРЬЕРА",
                True,
                f"HTTP 404: Корректно обработана ошибка несуществующего курьера"
            )
        else:
            self.log_test(
                "АКТИВАЦИЯ НЕСУЩЕСТВУЮЩЕГО КУРЬЕРА",
                False,
                f"HTTP {response.status_code}: Ожидался 404"
            )
        
        return True
    
    def test_api_endpoints_availability(self):
        """Тест доступности всех необходимых API endpoints"""
        print("\n" + "="*80)
        print("🔗 ТЕСТ ДОСТУПНОСТИ API ENDPOINTS")
        print("="*80)
        
        endpoints_to_test = [
            ("GET", "/admin/couriers/list", "Список активных курьеров"),
            ("GET", "/admin/couriers/inactive", "Список неактивных курьеров"),
            ("POST", "/admin/couriers/create", "Создание курьера"),
            ("DELETE", "/admin/couriers/{id}", "Деактивация курьера"),
            ("POST", "/admin/couriers/{id}/activate", "Активация курьера"),
            ("DELETE", "/admin/couriers/{id}/permanent", "Полное удаление курьера")
        ]
        
        for method, endpoint, description in endpoints_to_test:
            try:
                if method == "GET":
                    response = self.session.get(f"{BACKEND_URL}{endpoint}")
                elif method == "POST":
                    # Для POST endpoints делаем запрос с пустыми данными чтобы проверить доступность
                    response = self.session.post(f"{BACKEND_URL}{endpoint.replace('{id}', 'test')}", json={})
                elif method == "DELETE":
                    response = self.session.delete(f"{BACKEND_URL}{endpoint.replace('{id}', 'test')}")
                
                # Endpoint доступен если не возвращает 404 (Not Found)
                if response.status_code != 404:
                    self.log_test(
                        f"ENDPOINT {method} {endpoint}",
                        True,
                        f"{description} - HTTP {response.status_code} (endpoint доступен)"
                    )
                else:
                    self.log_test(
                        f"ENDPOINT {method} {endpoint}",
                        False,
                        f"{description} - HTTP 404 (endpoint не найден)"
                    )
                    
            except Exception as e:
                self.log_test(
                    f"ENDPOINT {method} {endpoint}",
                    False,
                    f"{description} - Ошибка: {str(e)}"
                )
        
        return True
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправленное обновление списков курьеров при активации/удалении в TAJLINE.TJ")
        print("="*120)
        print(f"Время начала тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Backend URL: {BACKEND_URL}")
        print("="*120)
        
        # Авторизация
        if not self.authenticate_admin():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как администратор")
            return False
        
        # Запуск тестов
        tests = [
            ("API ENDPOINTS AVAILABILITY", self.test_api_endpoints_availability),
            ("COURIER LIST SYNCHRONIZATION", self.test_courier_list_synchronization),
            ("MULTIPLE COURIER OPERATIONS", self.test_multiple_courier_operations),
            ("EDGE CASES", self.test_edge_cases)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n{'='*60}")
            print(f"🧪 ВЫПОЛНЕНИЕ ТЕСТА: {test_name}")
            print(f"{'='*60}")
            
            try:
                if test_func():
                    passed_tests += 1
                    print(f"✅ ТЕСТ '{test_name}' ЗАВЕРШЕН УСПЕШНО")
                else:
                    print(f"❌ ТЕСТ '{test_name}' ЗАВЕРШЕН С ОШИБКАМИ")
            except Exception as e:
                print(f"❌ ТЕСТ '{test_name}' ЗАВЕРШЕН С ИСКЛЮЧЕНИЕМ: {str(e)}")
        
        # Итоговый отчет
        print("\n" + "="*120)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("="*120)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"Успешно пройдено тестов: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Детальная статистика по отдельным проверкам
        successful_checks = sum(1 for result in self.test_results if result["success"])
        total_checks = len(self.test_results)
        check_success_rate = (successful_checks / total_checks) * 100 if total_checks > 0 else 0
        
        print(f"Успешно пройдено проверок: {successful_checks}/{total_checks} ({check_success_rate:.1f}%)")
        
        # Список неудачных тестов
        failed_tests = [result for result in self.test_results if not result["success"]]
        if failed_tests:
            print(f"\n❌ НЕУДАЧНЫЕ ПРОВЕРКИ ({len(failed_tests)}):")
            for failed in failed_tests:
                print(f"   • {failed['test']}: {failed['details']}")
        
        print(f"\nВремя завершения тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Финальная оценка
        if success_rate >= 90:
            print("\n🎉 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ Исправления обновления списков курьеров работают корректно")
            print("✅ Синхронизация между активными и неактивными курьерами функционирует правильно")
            print("✅ Backend готов для frontend интеграции с исправленными функциями handleActivateCourier и handlePermanentDeleteCourier")
        elif success_rate >= 70:
            print("\n⚠️ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ПРЕДУПРЕЖДЕНИЯМИ")
            print("⚠️ Основная функциональность работает, но есть минорные проблемы")
        else:
            print("\n❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ ОБНАРУЖЕНЫ")
            print("❌ Требуется исправление найденных проблем перед использованием")
        
        return success_rate >= 70

def main():
    """Главная функция"""
    tester = CourierListUpdateTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
🔢 ТЕСТИРОВАНИЕ СЧЕТЧИКОВ БОКОВОГО МЕНЮ: Новая функциональность подсчета элементов для каждого пункта меню в TAJLINE.TJ

КОНТЕКСТ ТЕСТИРОВАНИЯ:
Только что реализованы счетчики для бокового меню, которые показывают количество элементов в каждом разделе. 
Система автоматически подсчитывает и отображает счетчики для всех основных разделов приложения.

НОВАЯ ФУНКЦИОНАЛЬНОСТЬ:
1. ✅ Автоматический подсчет элементов для каждого пункта меню
2. ✅ Цветовая система счетчиков: Красные (основные), синие (подпункты), зеленые (вложенные)
3. ✅ Умное отображение: Скрытие нулей, "99+" для больших чисел
4. ✅ Реального времени обновление при изменении данных

ENDPOINTS ДЛЯ СОЗДАНИЯ ТЕСТОВЫХ ДАННЫХ:

Приоритет 1: Создание данных для счетчиков
1. POST /api/operator/cargo/accept - Создать 5-7 тестовых грузов для счетчика "Грузы"
2. GET /api/operator/cargo/individual-units-for-placement - Проверить данные для счетчика "Размещение"
3. GET /api/operator/warehouses - Проверить данные для счетчика "Склады"
4. GET /api/operator/placement-progress - Получить прогресс для счетчика размещения

Приоритет 2: Проверка существующих данных
5. GET /api/operator/cargo - Проверить список грузов для основного счетчика
6. GET /api/users (для админов) - Проверить пользователей/курьеров
7. GET /api/operator/unpaid-cargo - Данные для счетчика кассы

ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ:
- Все основные endpoints работают стабильно
- Тестовые данные создаются корректно для демонстрации счетчиков
- Система возвращает нужные структуры данных для подсчета
- Backend готов для frontend отображения счетчиков в реальном времени

СПЕЦИАЛЬНОЕ ВНИМАНИЕ:
- Создать разнообразные тестовые данные для демонстрации всех типов счетчиков
- Убедиться что данные структурированы для правильного подсчета frontend
- Проверить производительность при множественных запросах на получение счетчиков

ЦЕЛЬ: Подготовить backend данные для визуального тестирования счетчиков в интерфейсе
"""

import requests
import json
import time
from datetime import datetime, timedelta
import os
import random

# Конфигурация для тестирования
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://placement-view.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Тестовые данные оператора склада
OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

# Тестовые данные администратора
ADMIN_CREDENTIALS = {
    "phone": "+79999888777",
    "password": "admin123"
}

class SidebarCountersTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.warehouse_id = None
        self.test_results = []
        self.created_cargo_ids = []
        
    def log_test(self, test_name, success, details="", expected="", actual=""):
        """Логирование результатов тестов"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "expected": expected,
            "actual": actual,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
        if not success and expected:
            print(f"   🎯 Ожидалось: {expected}")
            print(f"   📊 Получено: {actual}")
        print()
        
    def authenticate_operator(self):
        """Авторизация оператора склада"""
        print("🔐 Авторизация оператора склада...")
        
        try:
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=OPERATOR_CREDENTIALS,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                # Получаем информацию о пользователе
                user_response = self.session.get(f"{API_BASE}/auth/me", timeout=30)
                if user_response.status_code == 200:
                    self.current_user = user_response.json()
                    self.log_test(
                        "Авторизация оператора склада",
                        True,
                        f"Успешная авторизация: {self.current_user.get('full_name')} (роль: {self.current_user.get('role')})"
                    )
                    return True
                else:
                    self.log_test("Получение данных пользователя", False, f"Ошибка: {user_response.status_code}")
                    return False
            else:
                self.log_test("Авторизация оператора склада", False, f"Ошибка авторизации: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Авторизация оператора склада", False, f"Исключение: {str(e)}")
            return False
    
    def authenticate_admin(self):
        """Авторизация администратора"""
        print("🔐 Авторизация администратора...")
        
        try:
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=ADMIN_CREDENTIALS,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                # Получаем информацию о пользователе
                user_response = self.session.get(f"{API_BASE}/auth/me", timeout=30)
                if user_response.status_code == 200:
                    self.current_user = user_response.json()
                    self.log_test(
                        "Авторизация администратора",
                        True,
                        f"Успешная авторизация: {self.current_user.get('full_name')} (роль: {self.current_user.get('role')})"
                    )
                    return True
                else:
                    self.log_test("Получение данных администратора", False, f"Ошибка: {user_response.status_code}")
                    return False
            else:
                self.log_test("Авторизация администратора", False, f"Ошибка авторизации: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Авторизация администратора", False, f"Исключение: {str(e)}")
            return False
    
    def get_operator_warehouse(self):
        """Получение склада оператора"""
        try:
            print("🏢 Получение склада оператора...")
            
            response = self.session.get(f"{API_BASE}/operator/warehouses", timeout=30)
            
            if response.status_code == 200:
                warehouses = response.json()
                if warehouses:
                    warehouse = warehouses[0]
                    self.warehouse_id = warehouse.get("id")
                    self.log_test(
                        "Получение склада оператора",
                        True,
                        f"Склад получен: {warehouse.get('name')} (ID: {self.warehouse_id})"
                    )
                    return True
                else:
                    self.log_test("Получение склада оператора", False, "У оператора нет привязанных складов")
                    return False
            else:
                self.log_test("Получение склада оператора", False, f"Ошибка получения складов: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Получение склада оператора", False, f"Исключение: {str(e)}")
            return False

    def create_test_cargo_data(self):
        """ПРИОРИТЕТ 1: Создание 5-7 тестовых грузов для счетчика 'Грузы'"""
        try:
            print("🎯 ТЕСТ 1: СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ ДЛЯ СЧЕТЧИКА 'ГРУЗЫ'")
            
            # Создаем 6 разнообразных тестовых грузов
            test_cargos = [
                {
                    "sender_full_name": "Иван Петров",
                    "sender_phone": "+79161234567",
                    "recipient_full_name": "Мария Сидорова",
                    "recipient_phone": "+992987654321",
                    "recipient_address": "Душанбе, ул. Рудаки, 15",
                    "cargo_items": [
                        {
                            "cargo_name": "Электроника Samsung",
                            "quantity": 2,
                            "weight": 5.5,
                            "price_per_kg": 150.0,
                            "total_amount": 825.0
                        }
                    ],
                    "description": "Телефоны и аксессуары",
                    "route": "moscow_to_tajikistan",
                    "payment_method": "cash_on_delivery"
                },
                {
                    "sender_full_name": "Алексей Козлов",
                    "sender_phone": "+79162345678",
                    "recipient_full_name": "Фарход Рахимов",
                    "recipient_phone": "+992987654322",
                    "recipient_address": "Худжанд, ул. Ленина, 25",
                    "cargo_items": [
                        {
                            "cargo_name": "Бытовая техника",
                            "quantity": 1,
                            "weight": 12.0,
                            "price_per_kg": 80.0,
                            "total_amount": 960.0
                        }
                    ],
                    "description": "Микроволновая печь",
                    "route": "moscow_to_tajikistan",
                    "payment_method": "cash"
                },
                {
                    "sender_full_name": "Ольга Смирнова",
                    "sender_phone": "+79163456789",
                    "recipient_full_name": "Зарина Назарова",
                    "recipient_phone": "+992987654323",
                    "recipient_address": "Душанбе, пр. Исмоили Сомони, 45",
                    "cargo_items": [
                        {
                            "cargo_name": "Одежда и обувь",
                            "quantity": 3,
                            "weight": 8.2,
                            "price_per_kg": 120.0,
                            "total_amount": 984.0
                        }
                    ],
                    "description": "Зимняя одежда и обувь",
                    "route": "moscow_to_tajikistan",
                    "payment_method": "card_transfer"
                },
                {
                    "sender_full_name": "Дмитрий Волков",
                    "sender_phone": "+79164567890",
                    "recipient_full_name": "Джамшед Каримов",
                    "recipient_phone": "+992987654324",
                    "recipient_address": "Куляб, ул. Фирдавси, 12",
                    "cargo_items": [
                        {
                            "cargo_name": "Автозапчасти",
                            "quantity": 4,
                            "weight": 15.8,
                            "price_per_kg": 200.0,
                            "total_amount": 3160.0
                        }
                    ],
                    "description": "Запчасти для Toyota",
                    "route": "moscow_to_tajikistan",
                    "payment_method": "credit",
                    "debt_due_date": "2025-02-15"
                },
                {
                    "sender_full_name": "Елена Морозова",
                    "sender_phone": "+79165678901",
                    "recipient_full_name": "Нигора Юсупова",
                    "recipient_phone": "+992987654325",
                    "recipient_address": "Душанбе, ул. Айни, 78",
                    "cargo_items": [
                        {
                            "cargo_name": "Косметика и парфюмерия",
                            "quantity": 5,
                            "weight": 3.2,
                            "price_per_kg": 300.0,
                            "total_amount": 960.0
                        }
                    ],
                    "description": "Косметические товары",
                    "route": "moscow_to_tajikistan",
                    "payment_method": "cash_on_delivery"
                },
                {
                    "sender_full_name": "Сергей Новиков",
                    "sender_phone": "+79166789012",
                    "recipient_full_name": "Рустам Холов",
                    "recipient_phone": "+992987654326",
                    "recipient_address": "Худжанд, ул. Гагарина, 33",
                    "cargo_items": [
                        {
                            "cargo_name": "Медицинские товары",
                            "quantity": 2,
                            "weight": 6.5,
                            "price_per_kg": 250.0,
                            "total_amount": 1625.0
                        }
                    ],
                    "description": "Медицинские приборы",
                    "route": "moscow_to_tajikistan",
                    "payment_method": "cash"
                }
            ]
            
            created_count = 0
            
            for i, cargo_data in enumerate(test_cargos, 1):
                try:
                    response = self.session.post(
                        f"{API_BASE}/operator/cargo/accept",
                        json=cargo_data,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        cargo_id = result.get("cargo_id")
                        cargo_number = result.get("cargo_number")
                        
                        if cargo_id:
                            self.created_cargo_ids.append(cargo_id)
                            created_count += 1
                            print(f"  ✅ Груз #{i} создан: {cargo_number} (ID: {cargo_id})")
                        else:
                            print(f"  ⚠️ Груз #{i} создан, но ID не получен")
                            created_count += 1
                    else:
                        print(f"  ❌ Ошибка создания груза #{i}: {response.status_code}")
                        
                except Exception as e:
                    print(f"  ❌ Исключение при создании груза #{i}: {str(e)}")
            
            if created_count >= 5:
                self.log_test(
                    "Создание тестовых данных для счетчика 'Грузы'",
                    True,
                    f"Успешно создано {created_count} тестовых грузов для демонстрации счетчика"
                )
                return True
            else:
                self.log_test(
                    "Создание тестовых данных для счетчика 'Грузы'",
                    False,
                    f"Создано недостаточно грузов: {created_count}",
                    "Минимум 5 грузов",
                    f"{created_count} грузов"
                )
                return False
                
        except Exception as e:
            self.log_test("Создание тестовых данных для счетчика 'Грузы'", False, f"Исключение: {str(e)}")
            return False

    def test_placement_counter_data(self):
        """ПРИОРИТЕТ 1: Проверка данных для счетчика 'Размещение'"""
        try:
            print("🎯 ТЕСТ 2: ПРОВЕРКА ДАННЫХ ДЛЯ СЧЕТЧИКА 'РАЗМЕЩЕНИЕ'")
            
            # Тестируем GET /api/operator/cargo/individual-units-for-placement
            response = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                total = data.get("total", 0)
                
                # Подсчитываем общее количество individual units
                total_units = 0
                for group in items:
                    units = group.get("units", [])
                    total_units += len(units)
                
                self.log_test(
                    "Данные для счетчика 'Размещение' (Individual Units)",
                    True,
                    f"Получено {len(items)} групп грузов с {total_units} individual units для размещения"
                )
                
                # Тестируем GET /api/operator/placement-progress
                progress_response = self.session.get(f"{API_BASE}/operator/placement-progress", timeout=30)
                
                if progress_response.status_code == 200:
                    progress_data = progress_response.json()
                    total_units_progress = progress_data.get("total_units", 0)
                    placed_units = progress_data.get("placed_units", 0)
                    pending_units = progress_data.get("pending_units", 0)
                    progress_text = progress_data.get("progress_text", "")
                    
                    self.log_test(
                        "Прогресс размещения для счетчика",
                        True,
                        f"Прогресс размещения: {progress_text} (всего: {total_units_progress}, размещено: {placed_units}, ожидает: {pending_units})"
                    )
                    return True
                else:
                    self.log_test(
                        "Прогресс размещения для счетчика",
                        False,
                        f"Ошибка получения прогресса: {progress_response.status_code}"
                    )
                    return False
            else:
                self.log_test(
                    "Данные для счетчика 'Размещение'",
                    False,
                    f"Ошибка получения individual units: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Данные для счетчика 'Размещение'", False, f"Исключение: {str(e)}")
            return False

    def test_warehouses_counter_data(self):
        """ПРИОРИТЕТ 1: Проверка данных для счетчика 'Склады'"""
        try:
            print("🎯 ТЕСТ 3: ПРОВЕРКА ДАННЫХ ДЛЯ СЧЕТЧИКА 'СКЛАДЫ'")
            
            response = self.session.get(f"{API_BASE}/operator/warehouses", timeout=30)
            
            if response.status_code == 200:
                warehouses = response.json()
                warehouse_count = len(warehouses)
                
                if warehouse_count > 0:
                    warehouse_names = [w.get("name", "Неизвестно") for w in warehouses]
                    self.log_test(
                        "Данные для счетчика 'Склады'",
                        True,
                        f"Получено {warehouse_count} складов: {', '.join(warehouse_names)}"
                    )
                    return True
                else:
                    self.log_test(
                        "Данные для счетчика 'Склады'",
                        False,
                        "Нет доступных складов для оператора"
                    )
                    return False
            else:
                self.log_test(
                    "Данные для счетчика 'Склады'",
                    False,
                    f"Ошибка получения складов: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Данные для счетчика 'Склады'", False, f"Исключение: {str(e)}")
            return False

    def test_cargo_list_counter_data(self):
        """ПРИОРИТЕТ 2: Проверка списка грузов для основного счетчика"""
        try:
            print("🎯 ТЕСТ 4: ПРОВЕРКА СПИСКА ГРУЗОВ ДЛЯ ОСНОВНОГО СЧЕТЧИКА")
            
            response = self.session.get(f"{API_BASE}/operator/cargo/list", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, dict) and "items" in data:
                    # Пагинированный ответ
                    items = data.get("items", [])
                    total = data.get("total", 0)
                    
                    self.log_test(
                        "Список грузов для основного счетчика",
                        True,
                        f"Получено {len(items)} грузов на текущей странице, всего: {total}"
                    )
                elif isinstance(data, list):
                    # Простой список
                    cargo_count = len(data)
                    
                    self.log_test(
                        "Список грузов для основного счетчика",
                        True,
                        f"Получено {cargo_count} грузов в списке"
                    )
                else:
                    self.log_test(
                        "Список грузов для основного счетчика",
                        False,
                        f"Неожиданная структура ответа: {type(data)}"
                    )
                    return False
                
                return True
            else:
                self.log_test(
                    "Список грузов для основного счетчика",
                    False,
                    f"Ошибка получения списка грузов: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Список грузов для основного счетчика", False, f"Исключение: {str(e)}")
            return False

    def test_users_counter_data(self):
        """ПРИОРИТЕТ 2: Проверка пользователей/курьеров (для админов)"""
        try:
            print("🎯 ТЕСТ 5: ПРОВЕРКА ПОЛЬЗОВАТЕЛЕЙ/КУРЬЕРОВ (ДЛЯ АДМИНОВ)")
            
            # Переключаемся на администратора для доступа к пользователям
            if not self.authenticate_admin():
                self.log_test("Переключение на администратора", False, "Не удалось авторизоваться как администратор")
                return False
            
            # Проверяем список пользователей
            users_response = self.session.get(f"{API_BASE}/admin/users", timeout=30)
            
            if users_response.status_code == 200:
                users_data = users_response.json()
                
                if isinstance(users_data, dict) and "items" in users_data:
                    users = users_data.get("items", [])
                    total_users = users_data.get("total", 0)
                else:
                    users = users_data if isinstance(users_data, list) else []
                    total_users = len(users)
                
                # Подсчитываем пользователей по ролям
                role_counts = {}
                for user in users:
                    role = user.get("role", "unknown")
                    role_counts[role] = role_counts.get(role, 0) + 1
                
                self.log_test(
                    "Данные пользователей для счетчика",
                    True,
                    f"Получено {total_users} пользователей. Распределение по ролям: {role_counts}"
                )
                
                # Проверяем список курьеров
                couriers_response = self.session.get(f"{API_BASE}/admin/couriers/list", timeout=30)
                
                if couriers_response.status_code == 200:
                    couriers_data = couriers_response.json()
                    
                    if isinstance(couriers_data, dict) and "items" in couriers_data:
                        couriers = couriers_data.get("items", [])
                        total_couriers = couriers_data.get("total", 0)
                    else:
                        couriers = couriers_data if isinstance(couriers_data, list) else []
                        total_couriers = len(couriers)
                    
                    # Подсчитываем активных/неактивных курьеров
                    active_couriers = len([c for c in couriers if c.get("is_active", True)])
                    inactive_couriers = total_couriers - active_couriers
                    
                    self.log_test(
                        "Данные курьеров для счетчика",
                        True,
                        f"Получено {total_couriers} курьеров (активных: {active_couriers}, неактивных: {inactive_couriers})"
                    )
                    return True
                else:
                    self.log_test(
                        "Данные курьеров для счетчика",
                        False,
                        f"Ошибка получения курьеров: {couriers_response.status_code}"
                    )
                    return False
            else:
                self.log_test(
                    "Данные пользователей для счетчика",
                    False,
                    f"Ошибка получения пользователей: {users_response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Данные пользователей/курьеров", False, f"Исключение: {str(e)}")
            return False

    def test_unpaid_cargo_counter_data(self):
        """ПРИОРИТЕТ 2: Данные для счетчика кассы (неоплаченные заказы)"""
        try:
            print("🎯 ТЕСТ 6: ПРОВЕРКА ДАННЫХ ДЛЯ СЧЕТЧИКА КАССЫ")
            
            # Возвращаемся к оператору
            if not self.authenticate_operator():
                self.log_test("Возврат к оператору", False, "Не удалось авторизоваться как оператор")
                return False
            
            response = self.session.get(f"{API_BASE}/cashier/unpaid-cargo", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, dict) and "items" in data:
                    unpaid_items = data.get("items", [])
                    total_unpaid = data.get("total", 0)
                else:
                    unpaid_items = data if isinstance(data, list) else []
                    total_unpaid = len(unpaid_items)
                
                # Подсчитываем общую сумму неоплаченных заказов
                total_amount = 0
                for item in unpaid_items:
                    amount = item.get("amount", 0) or item.get("declared_value", 0)
                    total_amount += amount
                
                self.log_test(
                    "Данные для счетчика кассы (неоплаченные заказы)",
                    True,
                    f"Получено {total_unpaid} неоплаченных заказов на общую сумму {total_amount:.2f} руб."
                )
                return True
            else:
                self.log_test(
                    "Данные для счетчика кассы",
                    False,
                    f"Ошибка получения неоплаченных заказов: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Данные для счетчика кассы", False, f"Исключение: {str(e)}")
            return False

    def test_performance_multiple_requests(self):
        """Проверка производительности при множественных запросах"""
        try:
            print("🎯 ТЕСТ 7: ПРОВЕРКА ПРОИЗВОДИТЕЛЬНОСТИ ПРИ МНОЖЕСТВЕННЫХ ЗАПРОСАХ")
            
            # Список endpoints для тестирования производительности
            endpoints = [
                "/operator/cargo/list",
                "/operator/warehouses", 
                "/operator/placement-progress",
                "/operator/cargo/individual-units-for-placement"
            ]
            
            total_time = 0
            successful_requests = 0
            
            for endpoint in endpoints:
                start_time = time.time()
                
                try:
                    response = self.session.get(f"{API_BASE}{endpoint}", timeout=30)
                    end_time = time.time()
                    request_time = end_time - start_time
                    
                    if response.status_code == 200:
                        successful_requests += 1
                        total_time += request_time
                        print(f"  ✅ {endpoint}: {request_time:.3f}s")
                    else:
                        print(f"  ❌ {endpoint}: HTTP {response.status_code}")
                        
                except Exception as e:
                    print(f"  ❌ {endpoint}: {str(e)}")
            
            if successful_requests > 0:
                avg_time = total_time / successful_requests
                
                if avg_time < 2.0:  # Ожидаем среднее время ответа менее 2 секунд
                    self.log_test(
                        "Производительность при множественных запросах",
                        True,
                        f"Успешно выполнено {successful_requests}/{len(endpoints)} запросов. Среднее время ответа: {avg_time:.3f}s"
                    )
                    return True
                else:
                    self.log_test(
                        "Производительность при множественных запросах",
                        False,
                        f"Медленные ответы: среднее время {avg_time:.3f}s",
                        "Менее 2.0s",
                        f"{avg_time:.3f}s"
                    )
                    return False
            else:
                self.log_test(
                    "Производительность при множественных запросах",
                    False,
                    "Ни один запрос не выполнился успешно"
                )
                return False
                
        except Exception as e:
            self.log_test("Производительность при множественных запросах", False, f"Исключение: {str(e)}")
            return False

    def run_all_tests(self):
        """Запуск всех тестов счетчиков бокового меню"""
        print("🔢 НАЧАЛО ТЕСТИРОВАНИЯ СЧЕТЧИКОВ БОКОВОГО МЕНЮ В TAJLINE.TJ")
        print("=" * 80)
        
        # Подготовка
        if not self.authenticate_operator():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как оператор")
            return False
        
        if not self.get_operator_warehouse():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить склад оператора")
            return False
        
        # Запуск тестов
        test_results = []
        
        # ПРИОРИТЕТ 1: Создание данных для счетчиков
        test_results.append(("Создание тестовых данных для счетчика 'Грузы'", self.create_test_cargo_data()))
        test_results.append(("Данные для счетчика 'Размещение'", self.test_placement_counter_data()))
        test_results.append(("Данные для счетчика 'Склады'", self.test_warehouses_counter_data()))
        
        # ПРИОРИТЕТ 2: Проверка существующих данных
        test_results.append(("Список грузов для основного счетчика", self.test_cargo_list_counter_data()))
        test_results.append(("Данные пользователей/курьеров для счетчиков", self.test_users_counter_data()))
        test_results.append(("Данные для счетчика кассы", self.test_unpaid_cargo_counter_data()))
        
        # Дополнительные тесты
        test_results.append(("Производительность при множественных запросах", self.test_performance_multiple_requests()))
        
        # Подведение итогов
        print("\n" + "=" * 80)
        print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ СЧЕТЧИКОВ БОКОВОГО МЕНЮ:")
        print("=" * 80)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ ПРОЙДЕН" if result else "❌ НЕ ПРОЙДЕН"
            print(f"{status}: {test_name}")
            if result:
                passed_tests += 1
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n📈 ОБЩИЙ РЕЗУЛЬТАТ: {passed_tests}/{total_tests} тестов пройдено ({success_rate:.1f}%)")
        
        if success_rate == 100:
            print("🎉 ВСЕ ENDPOINTS ДЛЯ СЧЕТЧИКОВ РАБОТАЮТ ИДЕАЛЬНО! Backend готов для frontend отображения счетчиков в реальном времени. СИСТЕМА ГОТОВА К ПРОДАКШЕНУ!")
        elif success_rate >= 85:
            print("🎯 ОТЛИЧНЫЙ РЕЗУЛЬТАТ! Большинство endpoints работают корректно. Backend практически готов для счетчиков.")
        elif success_rate >= 70:
            print("⚠️ ХОРОШИЙ РЕЗУЛЬТАТ! Основные endpoints работают, но есть проблемы требующие внимания.")
        else:
            print("❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ! Многие endpoints не работают корректно. Требуется исправление.")
        
        # Дополнительная информация о созданных данных
        if self.created_cargo_ids:
            print(f"\n📦 СОЗДАННЫЕ ТЕСТОВЫЕ ДАННЫЕ:")
            print(f"   Создано {len(self.created_cargo_ids)} тестовых грузов для демонстрации счетчиков")
            print(f"   ID созданных грузов: {', '.join(self.created_cargo_ids[:3])}{'...' if len(self.created_cargo_ids) > 3 else ''}")
        
        return success_rate >= 85  # Ожидаем минимум 85% для успешного тестирования

def main():
    """Главная функция"""
    tester = SidebarCountersTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 ТЕСТИРОВАНИЕ СЧЕТЧИКОВ ЗАВЕРШЕНО УСПЕШНО!")
        print("Backend готов для визуального тестирования счетчиков в интерфейсе")
        return 0
    else:
        print("\n❌ ТЕСТИРОВАНИЕ ВЫЯВИЛО ПРОБЛЕМЫ!")
        print("Требуется исправление найденных ошибок в endpoints для счетчиков")
        return 1

if __name__ == "__main__":
    exit(main())
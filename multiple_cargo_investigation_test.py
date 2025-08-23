#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ПРОБЛЕМЫ ОТОБРАЖЕНИЯ ВЕСОВ И ЦЕН ДЛЯ МНОЖЕСТВЕННЫХ ГРУЗОВ В TAJLINE.TJ

Исследование проблемы отображения весов и цен для множественных грузов в TAJLINE.TJ:

ДИАГНОСТИКА ПРОБЛЕМЫ С МНОЖЕСТВЕННЫМИ ГРУЗАМИ:
1. Авторизация оператора (+79777888999/warehouse123)
2. Получить уведомления: GET /api/operator/warehouse-notifications
3. Найти уведомление с множественными грузами и получить pickup_request_id
4. Протестировать GET /api/operator/pickup-requests/{pickup_request_id} и проанализировать:
   - Структуру cargo_info
   - Есть ли массив cargo_items с отдельными грузами?
   - Как сохраняются индивидуальные веса и цены для каждого груза?
   - Или все объединяется в cargo_name и общие weight/total_value?

ДОПОЛНИТЕЛЬНАЯ ДИАГНОСТИКА:
5. Создать тестовую заявку где курьер заполняет НЕСКОЛЬКО грузов с разными весами и ценами:
   - Груз 1: "Холодильник" - 50 кг - 15000 ₽
   - Груз 2: "Кондиционер" - 25 кг - 10000 ₽
6. Проверить как эти данные сохраняются в базе данных
7. Проверить что возвращает endpoint modal_data

ЦЕЛЬ: Понять почему индивидуальные веса и цены каждого груза не сохраняются/не отображаются корректно в модальном окне.

КРИТИЧЕСКИЕ ВОПРОСЫ:
- Сохраняет ли backend отдельные cargo_items или объединяет их?
- Как курьер заполняет несколько грузов с индивидуальными параметрами?
- Правильно ли передаются данные от курьера к оператору?
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://tajline-manage-1.preview.emergentagent.com/api"

class MultipleCargoInvestigationTester:
    def __init__(self):
        self.session = requests.Session()
        self.operator_token = None
        self.courier_token = None
        self.admin_token = None
        
    def authenticate_operator(self):
        """Авторизация оператора склада"""
        print("🔐 ЭТАП 1: АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА (+79777888999/warehouse123)")
        
        login_data = {
            "phone": "+79777888999",
            "password": "warehouse123"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.operator_token = data.get("access_token")
                user_info = data.get("user", {})
                print(f"   ✅ Успешная авторизация: {user_info.get('full_name', 'Unknown')}")
                print(f"   Роль: {user_info.get('role', 'Unknown')}")
                print(f"   Номер пользователя: {user_info.get('user_number', 'Unknown')}")
                return True
            else:
                print(f"   ❌ Ошибка авторизации: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Исключение при авторизации: {e}")
            return False
    
    def authenticate_courier(self):
        """Авторизация курьера"""
        print("🔐 ЭТАП 2: АВТОРИЗАЦИЯ КУРЬЕРА (+79991234567/courier123)")
        
        login_data = {
            "phone": "+79991234567",
            "password": "courier123"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.courier_token = data.get("access_token")
                user_info = data.get("user", {})
                print(f"   ✅ Успешная авторизация: {user_info.get('full_name', 'Unknown')}")
                print(f"   Роль: {user_info.get('role', 'Unknown')}")
                print(f"   Номер пользователя: {user_info.get('user_number', 'Unknown')}")
                return True
            else:
                print(f"   ❌ Ошибка авторизации: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Исключение при авторизации: {e}")
            return False
    
    def get_warehouse_notifications(self):
        """Получить уведомления склада"""
        print("📋 ЭТАП 3: ПОЛУЧЕНИЕ УВЕДОМЛЕНИЙ СКЛАДА")
        
        if not self.operator_token:
            print("   ❌ Нет токена оператора")
            return []
        
        headers = {"Authorization": f"Bearer {self.operator_token}"}
        
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/warehouse-notifications", headers=headers)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                notifications = data.get("notifications", [])
                print(f"   ✅ Найдено уведомлений: {len(notifications)}")
                
                # Ищем уведомления с pickup_request_id
                pickup_notifications = []
                for notification in notifications:
                    if notification.get("pickup_request_id"):
                        pickup_notifications.append(notification)
                        print(f"   📦 Уведомление с pickup_request_id: {notification.get('pickup_request_id')}")
                        print(f"      ID: {notification.get('id')}")
                        print(f"      Статус: {notification.get('status')}")
                        print(f"      Сообщение: {notification.get('message', '')[:100]}...")
                
                return pickup_notifications
            else:
                print(f"   ❌ Ошибка получения уведомлений: {response.text}")
                return []
                
        except Exception as e:
            print(f"   ❌ Исключение при получении уведомлений: {e}")
            return []
    
    def investigate_pickup_request(self, pickup_request_id):
        """Исследовать структуру заявки на забор груза"""
        print(f"🔍 ЭТАП 4: ИССЛЕДОВАНИЕ ЗАЯВКИ НА ЗАБОР ГРУЗА {pickup_request_id}")
        
        if not self.operator_token:
            print("   ❌ Нет токена оператора")
            return None
        
        headers = {"Authorization": f"Bearer {self.operator_token}"}
        
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/pickup-requests/{pickup_request_id}", headers=headers)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("   ✅ Структура заявки получена:")
                
                # Анализируем структуру cargo_info
                cargo_info = data.get("cargo_info", {})
                print(f"   📦 CARGO_INFO структура:")
                print(f"      Тип: {type(cargo_info)}")
                print(f"      Ключи: {list(cargo_info.keys()) if isinstance(cargo_info, dict) else 'Не словарь'}")
                
                # Проверяем наличие cargo_items
                cargo_items = cargo_info.get("cargo_items", []) if isinstance(cargo_info, dict) else []
                print(f"   📋 CARGO_ITEMS:")
                print(f"      Найдено элементов: {len(cargo_items)}")
                
                if cargo_items:
                    print("   🔍 ДЕТАЛЬНЫЙ АНАЛИЗ CARGO_ITEMS:")
                    for i, item in enumerate(cargo_items, 1):
                        print(f"      Груз {i}:")
                        print(f"         Название: {item.get('name', 'Не указано')}")
                        print(f"         Вес: {item.get('weight', 'Не указано')}")
                        print(f"         Цена: {item.get('price', 'Не указано')}")
                        print(f"         Общая стоимость: {item.get('total_price', 'Не указано')}")
                        print(f"         Все поля: {list(item.keys())}")
                else:
                    print("   ⚠️ CARGO_ITEMS пуст или отсутствует")
                    
                    # Проверяем общие поля
                    print("   🔍 ПРОВЕРКА ОБЩИХ ПОЛЕЙ:")
                    print(f"      cargo_name: {cargo_info.get('cargo_name', 'Отсутствует')}")
                    print(f"      weight: {cargo_info.get('weight', 'Отсутствует')}")
                    print(f"      total_value: {cargo_info.get('total_value', 'Отсутствует')}")
                    print(f"      declared_value: {cargo_info.get('declared_value', 'Отсутствует')}")
                
                # Полная структура данных
                print("   📄 ПОЛНАЯ СТРУКТУРА ОТВЕТА:")
                print(json.dumps(data, indent=2, ensure_ascii=False)[:2000] + "..." if len(str(data)) > 2000 else json.dumps(data, indent=2, ensure_ascii=False))
                
                return data
            else:
                print(f"   ❌ Ошибка получения заявки: {response.text}")
                return None
                
        except Exception as e:
            print(f"   ❌ Исключение при получении заявки: {e}")
            return None
    
    def create_test_pickup_request_with_multiple_cargo(self):
        """Создать тестовую заявку с множественными грузами"""
        print("🚚 ЭТАП 5: СОЗДАНИЕ ТЕСТОВОЙ ЗАЯВКИ С МНОЖЕСТВЕННЫМИ ГРУЗАМИ")
        
        if not self.operator_token:
            print("   ❌ Нет токена оператора")
            return None
        
        headers = {"Authorization": f"Bearer {self.operator_token}"}
        
        # Данные для создания заявки с множественными грузами
        pickup_request_data = {
            "sender_full_name": "Тестовый Отправитель Множественных Грузов",
            "sender_phone": "+79998887766",
            "pickup_address": "Москва, ул. Тестовая Множественная, 123",
            "pickup_date": "2025-01-20",
            "pickup_time_from": "10:00",
            "pickup_time_to": "18:00",
            "route": "moscow_to_tajikistan",
            "courier_fee": 500.0,
            "destination": "Душанбе",
            # КРИТИЧЕСКИ ВАЖНО: Множественные грузы с индивидуальными весами и ценами
            "cargo_items": [
                {
                    "name": "Холодильник",
                    "weight": 50.0,
                    "price": 15000.0,
                    "description": "Холодильник Samsung двухкамерный"
                },
                {
                    "name": "Кондиционер", 
                    "weight": 25.0,
                    "price": 10000.0,
                    "description": "Кондиционер LG настенный"
                }
            ],
            "total_weight": 75.0,
            "total_value": 25000.0,
            "description": "Тестовая заявка для исследования множественных грузов"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/admin/courier/pickup-request", json=pickup_request_data, headers=headers)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                request_id = data.get("request_id")
                request_number = data.get("request_number")
                print(f"   ✅ Заявка создана успешно:")
                print(f"      ID: {request_id}")
                print(f"      Номер: {request_number}")
                print(f"      Множественные грузы:")
                print(f"         1. Холодильник - 50 кг - 15000 ₽")
                print(f"         2. Кондиционер - 25 кг - 10000 ₽")
                print(f"      Общий вес: 75 кг")
                print(f"      Общая стоимость: 25000 ₽")
                
                return request_id
            else:
                print(f"   ❌ Ошибка создания заявки: {response.text}")
                return None
                
        except Exception as e:
            print(f"   ❌ Исключение при создании заявки: {e}")
            return None
    
    def simulate_courier_workflow_with_multiple_cargo(self, request_id):
        """Симулировать workflow курьера с множественными грузами"""
        print(f"👨‍💼 ЭТАП 6: СИМУЛЯЦИЯ WORKFLOW КУРЬЕРА С МНОЖЕСТВЕННЫМИ ГРУЗАМИ")
        
        if not self.courier_token or not request_id:
            print("   ❌ Нет токена курьера или ID заявки")
            return False
        
        headers = {"Authorization": f"Bearer {self.courier_token}"}
        
        # 1. Принять заявку
        print("   📝 Принятие заявки курьером...")
        try:
            response = self.session.post(f"{BACKEND_URL}/courier/requests/{request_id}/accept", headers=headers)
            print(f"      Status: {response.status_code}")
            
            if response.status_code == 200:
                print("      ✅ Заявка принята курьером")
            else:
                print(f"      ❌ Ошибка принятия заявки: {response.text}")
                return False
        except Exception as e:
            print(f"      ❌ Исключение при принятии заявки: {e}")
            return False
        
        # 2. Забрать груз
        print("   📦 Забор груза курьером...")
        try:
            response = self.session.post(f"{BACKEND_URL}/courier/requests/{request_id}/pickup", headers=headers)
            print(f"      Status: {response.status_code}")
            
            if response.status_code == 200:
                print("      ✅ Груз забран курьером")
            else:
                print(f"      ❌ Ошибка забора груза: {response.text}")
                return False
        except Exception as e:
            print(f"      ❌ Исключение при заборе груза: {e}")
            return False
        
        # 3. Сдать груз на склад
        print("   🏢 Сдача груза на склад...")
        try:
            response = self.session.post(f"{BACKEND_URL}/courier/requests/{request_id}/deliver-to-warehouse", headers=headers)
            print(f"      Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                notification_id = data.get("notification_id")
                print(f"      ✅ Груз сдан на склад")
                print(f"      Создано уведомление: {notification_id}")
                return notification_id
            else:
                print(f"      ❌ Ошибка сдачи груза: {response.text}")
                return False
        except Exception as e:
            print(f"      ❌ Исключение при сдаче груза: {e}")
            return False
    
    def investigate_notification_modal_data(self, notification_id):
        """Исследовать данные модального окна уведомления"""
        print(f"🔍 ЭТАП 7: ИССЛЕДОВАНИЕ ДАННЫХ МОДАЛЬНОГО ОКНА УВЕДОМЛЕНИЯ {notification_id}")
        
        if not self.operator_token:
            print("   ❌ Нет токена оператора")
            return None
        
        headers = {"Authorization": f"Bearer {self.operator_token}"}
        
        # Получаем детальную информацию уведомления
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/warehouse-notifications", headers=headers)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                notifications = data.get("notifications", [])
                
                # Ищем наше уведомление
                target_notification = None
                for notification in notifications:
                    if notification.get("id") == notification_id:
                        target_notification = notification
                        break
                
                if target_notification:
                    print("   ✅ Уведомление найдено:")
                    print(f"      ID: {target_notification.get('id')}")
                    print(f"      Статус: {target_notification.get('status')}")
                    print(f"      pickup_request_id: {target_notification.get('pickup_request_id')}")
                    
                    # Исследуем структуру cargo_info в уведомлении
                    cargo_info = target_notification.get("cargo_info", {})
                    print(f"   📦 CARGO_INFO В УВЕДОМЛЕНИИ:")
                    print(f"      Тип: {type(cargo_info)}")
                    
                    if isinstance(cargo_info, dict):
                        print(f"      Ключи: {list(cargo_info.keys())}")
                        
                        # Проверяем cargo_items
                        cargo_items = cargo_info.get("cargo_items", [])
                        print(f"   📋 CARGO_ITEMS В УВЕДОМЛЕНИИ:")
                        print(f"      Количество элементов: {len(cargo_items)}")
                        
                        if cargo_items:
                            print("   🔍 ДЕТАЛЬНЫЙ АНАЛИЗ CARGO_ITEMS В УВЕДОМЛЕНИИ:")
                            for i, item in enumerate(cargo_items, 1):
                                print(f"      Груз {i}:")
                                print(f"         Название: {item.get('name', 'Не указано')}")
                                print(f"         Вес: {item.get('weight', 'Не указано')}")
                                print(f"         Цена: {item.get('price', 'Не указано')}")
                                print(f"         Все поля: {list(item.keys())}")
                        else:
                            print("   ⚠️ CARGO_ITEMS в уведомлении пуст")
                            print("   🔍 ПРОВЕРКА ОБЪЕДИНЕННЫХ ПОЛЕЙ:")
                            print(f"      cargo_name: {cargo_info.get('cargo_name', 'Отсутствует')}")
                            print(f"      weight: {cargo_info.get('weight', 'Отсутствует')}")
                            print(f"      total_value: {cargo_info.get('total_value', 'Отсутствует')}")
                    
                    # Полная структура уведомления
                    print("   📄 ПОЛНАЯ СТРУКТУРА УВЕДОМЛЕНИЯ:")
                    print(json.dumps(target_notification, indent=2, ensure_ascii=False)[:1500] + "..." if len(str(target_notification)) > 1500 else json.dumps(target_notification, indent=2, ensure_ascii=False))
                    
                    return target_notification
                else:
                    print(f"   ❌ Уведомление {notification_id} не найдено")
                    return None
            else:
                print(f"   ❌ Ошибка получения уведомлений: {response.text}")
                return None
                
        except Exception as e:
            print(f"   ❌ Исключение при получении уведомлений: {e}")
            return None
    
    def test_modal_acceptance_with_multiple_cargo(self, notification_id):
        """Тестировать принятие модального окна с множественными грузами"""
        print(f"✅ ЭТАП 8: ТЕСТИРОВАНИЕ ПРИНЯТИЯ МОДАЛЬНОГО ОКНА С МНОЖЕСТВЕННЫМИ ГРУЗАМИ")
        
        if not self.operator_token:
            print("   ❌ Нет токена оператора")
            return False
        
        headers = {"Authorization": f"Bearer {self.operator_token}"}
        
        # 1. Принять уведомление
        print("   📝 Принятие уведомления...")
        try:
            response = self.session.post(f"{BACKEND_URL}/operator/warehouse-notifications/{notification_id}/accept", headers=headers)
            print(f"      Status: {response.status_code}")
            
            if response.status_code == 200:
                print("      ✅ Уведомление принято")
            else:
                print(f"      ❌ Ошибка принятия уведомления: {response.text}")
                return False
        except Exception as e:
            print(f"      ❌ Исключение при принятии уведомления: {e}")
            return False
        
        # 2. Завершить оформление с множественными грузами
        print("   📋 Завершение оформления с множественными грузами...")
        
        completion_data = {
            "sender_full_name": "Тестовый Отправитель Множественных Грузов",
            "cargo_items": [
                {
                    "name": "Холодильник",
                    "weight": "50.0",
                    "price": "15000"
                },
                {
                    "name": "Кондиционер",
                    "weight": "25.0", 
                    "price": "10000"
                }
            ],
            "payment_method": "cash",
            "delivery_method": "pickup"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/operator/warehouse-notifications/{notification_id}/complete", 
                                       json=completion_data, headers=headers)
            print(f"      Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                cargo_number = data.get("cargo_number")
                print(f"      ✅ Оформление завершено")
                print(f"      Номер груза: {cargo_number}")
                
                # Проверяем как сохранились множественные грузы
                return cargo_number
            else:
                print(f"      ❌ Ошибка завершения оформления: {response.text}")
                return False
        except Exception as e:
            print(f"      ❌ Исключение при завершении оформления: {e}")
            return False
    
    def investigate_final_cargo_structure(self, cargo_number):
        """Исследовать финальную структуру созданного груза"""
        print(f"🔍 ЭТАП 9: ИССЛЕДОВАНИЕ ФИНАЛЬНОЙ СТРУКТУРЫ ГРУЗА {cargo_number}")
        
        if not self.operator_token:
            print("   ❌ Нет токена оператора")
            return None
        
        headers = {"Authorization": f"Bearer {self.operator_token}"}
        
        try:
            response = self.session.get(f"{BACKEND_URL}/cargo/track/{cargo_number}", headers=headers)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("   ✅ Структура финального груза:")
                print(f"      Номер груза: {data.get('cargo_number')}")
                print(f"      Название груза: {data.get('cargo_name', 'Не указано')}")
                print(f"      Вес: {data.get('weight', 'Не указано')}")
                print(f"      Объявленная стоимость: {data.get('declared_value', 'Не указано')}")
                print(f"      Описание: {data.get('description', 'Не указано')}")
                
                # Проверяем наличие cargo_items в финальном грузе
                cargo_items = data.get("cargo_items", [])
                print(f"   📋 CARGO_ITEMS В ФИНАЛЬНОМ ГРУЗЕ:")
                print(f"      Количество элементов: {len(cargo_items)}")
                
                if cargo_items:
                    print("   🔍 ДЕТАЛЬНЫЙ АНАЛИЗ CARGO_ITEMS В ФИНАЛЬНОМ ГРУЗЕ:")
                    for i, item in enumerate(cargo_items, 1):
                        print(f"      Груз {i}:")
                        print(f"         Название: {item.get('name', 'Не указано')}")
                        print(f"         Вес: {item.get('weight', 'Не указано')}")
                        print(f"         Цена: {item.get('price', 'Не указано')}")
                        print(f"         Все поля: {list(item.keys())}")
                else:
                    print("   ⚠️ CARGO_ITEMS в финальном грузе отсутствует")
                    print("   🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА: Индивидуальные веса и цены грузов НЕ СОХРАНИЛИСЬ!")
                
                # Полная структура груза
                print("   📄 ПОЛНАЯ СТРУКТУРА ФИНАЛЬНОГО ГРУЗА:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                return data
            else:
                print(f"   ❌ Ошибка получения груза: {response.text}")
                return None
                
        except Exception as e:
            print(f"   ❌ Исключение при получении груза: {e}")
            return None
    
    def run_comprehensive_investigation(self):
        """Запустить комплексное исследование проблемы множественных грузов"""
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ПРОБЛЕМЫ ОТОБРАЖЕНИЯ ВЕСОВ И ЦЕН ДЛЯ МНОЖЕСТВЕННЫХ ГРУЗОВ В TAJLINE.TJ")
        print("=" * 100)
        
        # Этап 1: Авторизация оператора
        if not self.authenticate_operator():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как оператор")
            return False
        
        # Этап 2: Авторизация курьера
        if not self.authenticate_courier():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как курьер")
            return False
        
        # Этап 3: Получение существующих уведомлений
        existing_notifications = self.get_warehouse_notifications()
        
        # Этап 4: Исследование существующих заявок (если есть)
        if existing_notifications:
            print("🔍 ИССЛЕДОВАНИЕ СУЩЕСТВУЮЩИХ УВЕДОМЛЕНИЙ С PICKUP_REQUEST_ID:")
            for notification in existing_notifications[:2]:  # Исследуем первые 2
                pickup_request_id = notification.get("pickup_request_id")
                if pickup_request_id:
                    self.investigate_pickup_request(pickup_request_id)
        
        # Этап 5: Создание тестовой заявки с множественными грузами
        test_request_id = self.create_test_pickup_request_with_multiple_cargo()
        if not test_request_id:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось создать тестовую заявку")
            return False
        
        # Этап 6: Симуляция workflow курьера
        notification_id = self.simulate_courier_workflow_with_multiple_cargo(test_request_id)
        if not notification_id:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось завершить workflow курьера")
            return False
        
        # Этап 7: Исследование данных модального окна
        notification_data = self.investigate_notification_modal_data(notification_id)
        if not notification_data:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить данные уведомления")
            return False
        
        # Этап 8: Тестирование принятия модального окна
        cargo_number = self.test_modal_acceptance_with_multiple_cargo(notification_id)
        if not cargo_number:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось завершить оформление груза")
            return False
        
        # Этап 9: Исследование финальной структуры груза
        final_cargo_data = self.investigate_final_cargo_structure(cargo_number)
        if not final_cargo_data:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить финальную структуру груза")
            return False
        
        # Финальный анализ
        self.generate_final_analysis_report(final_cargo_data)
        
        return True
    
    def generate_final_analysis_report(self, final_cargo_data):
        """Генерировать финальный отчет анализа"""
        print("\n" + "=" * 100)
        print("📊 ФИНАЛЬНЫЙ ОТЧЕТ АНАЛИЗА ПРОБЛЕМЫ МНОЖЕСТВЕННЫХ ГРУЗОВ")
        print("=" * 100)
        
        # Проверяем наличие cargo_items в финальном грузе
        cargo_items = final_cargo_data.get("cargo_items", [])
        
        if cargo_items and len(cargo_items) > 1:
            print("✅ ПОЛОЖИТЕЛЬНЫЙ РЕЗУЛЬТАТ:")
            print("   Индивидуальные веса и цены грузов СОХРАНЯЮТСЯ корректно")
            print(f"   Найдено {len(cargo_items)} отдельных грузов:")
            for i, item in enumerate(cargo_items, 1):
                print(f"      {i}. {item.get('name', 'Без названия')} - {item.get('weight', 'Без веса')} кг - {item.get('price', 'Без цены')} ₽")
        else:
            print("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА ОБНАРУЖЕНА:")
            print("   Индивидуальные веса и цены грузов НЕ СОХРАНЯЮТСЯ!")
            print("   Возможные причины:")
            print("   1. Backend объединяет множественные грузы в один cargo_name")
            print("   2. Структура cargo_items не передается корректно")
            print("   3. Модальное окно не отображает индивидуальные параметры")
            
            # Анализируем что сохранилось вместо этого
            print("\n   Что сохранилось вместо множественных грузов:")
            print(f"      cargo_name: {final_cargo_data.get('cargo_name', 'Отсутствует')}")
            print(f"      weight: {final_cargo_data.get('weight', 'Отсутствует')}")
            print(f"      declared_value: {final_cargo_data.get('declared_value', 'Отсутствует')}")
        
        print("\n🎯 КЛЮЧЕВЫЕ ВЫВОДЫ:")
        print("1. Структура cargo_items должна сохраняться на всех этапах workflow")
        print("2. Модальное окно должно отображать каждый груз отдельно с индивидуальными параметрами")
        print("3. Backend должен поддерживать массив cargo_items, а не объединять в общие поля")
        print("4. Frontend должен корректно отображать множественные грузы в модальном окне")
        
        print("\n" + "=" * 100)

def main():
    """Главная функция тестирования"""
    tester = MultipleCargoInvestigationTester()
    
    try:
        success = tester.run_comprehensive_investigation()
        
        if success:
            print("\n🎉 КОМПЛЕКСНОЕ ИССЛЕДОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            sys.exit(0)
        else:
            print("\n❌ ИССЛЕДОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
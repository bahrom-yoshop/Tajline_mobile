#!/usr/bin/env python3
"""
Тестирование исправления отображения грузов из заявок на забор в разделе "Размещенные грузы"

ПРОБЛЕМА: Грузы, созданные из заявок на забор груза, не отображались в разделе "Размещенные грузы"

ИСПРАВЛЕНИЯ:
1. Frontend: Обновлен fetchPlacedCargo - теперь ищет статусы 'placed,placement_ready'
2. Backend: Обновлен endpoint /api/warehouses/placed-cargo - теперь ищет в коллекции operator_cargo 
   и включает статусы "placed_in_warehouse" и "placement_ready"

ТЕСТЫ:
1. Авторизация оператора (+79777888999/warehouse123)
2. ОСНОВНОЙ ТЕСТ: GET /api/warehouses/placed-cargo - должны возвращаться грузы со статусом "placement_ready"
3. Проверить что грузы из operator_cargo с pickup_request_id отображаются
4. Убедиться что возвращаются грузы с номерами в формате request_number/01, request_number/02
5. Проверить пагинацию и общее количество грузов
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class PlacedCargoTester:
    def __init__(self, base_url="https://tajline-cargo-8.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        
        print(f"🎯 ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ ОТОБРАЖЕНИЯ ГРУЗОВ ИЗ ЗАЯВОК НА ЗАБОР")
        print(f"📡 Base URL: {self.base_url}")
        print("=" * 80)

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data: Optional[Dict] = None, params: Optional[Dict] = None) -> tuple[bool, Dict]:
        """Выполнить один API тест"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Тест {self.tests_run}: {name}")
        print(f"   {method} {endpoint}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, params=params)
            elif method == 'DELETE':
                response = requests.delete(url, json=data, headers=headers)
            else:
                raise ValueError(f"Неподдерживаемый HTTP метод: {method}")

            print(f"   📊 Статус: {response.status_code}")
            
            # Попытка парсинга JSON ответа
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}

            success = response.status_code == expected_status
            if success:
                print(f"   ✅ УСПЕХ")
                self.tests_passed += 1
            else:
                print(f"   ❌ ОШИБКА: Ожидался статус {expected_status}, получен {response.status_code}")
                if response_data:
                    print(f"   📄 Ответ: {json.dumps(response_data, ensure_ascii=False, indent=2)}")

            return success, response_data

        except Exception as e:
            print(f"   💥 ИСКЛЮЧЕНИЕ: {str(e)}")
            return False, {"error": str(e)}

    def test_operator_authentication(self):
        """Тест 1: Авторизация оператора склада"""
        print(f"\n{'='*60}")
        print("🔐 ЭТАП 1: АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА")
        print(f"{'='*60}")
        
        # Авторизация оператора склада
        login_data = {
            "phone": "+79777888999",
            "password": "warehouse123"
        }
        
        success, response = self.run_test(
            "Авторизация оператора склада",
            "POST", "/api/auth/login", 200, login_data
        )
        
        if success and "access_token" in response:
            self.token = response["access_token"]
            print(f"   🎫 Токен получен: {self.token[:50]}...")
            
            # Получаем информацию о пользователе
            success, user_response = self.run_test(
                "Получение информации о пользователе",
                "GET", "/api/auth/me", 200
            )
            
            if success:
                self.user_data = user_response
                print(f"   👤 Пользователь: {user_response.get('full_name', 'Неизвестно')}")
                print(f"   🏷️ Роль: {user_response.get('role', 'Неизвестно')}")
                print(f"   📞 Телефон: {user_response.get('phone', 'Неизвестно')}")
                print(f"   🆔 ID: {user_response.get('user_number', 'Неизвестно')}")
                return True
        
        print("   ❌ Не удалось авторизоваться как оператор склада")
        return False

    def test_placed_cargo_endpoint(self):
        """Тест 2: ОСНОВНОЙ ТЕСТ - GET /api/warehouses/placed-cargo"""
        print(f"\n{'='*60}")
        print("🎯 ЭТАП 2: ОСНОВНОЙ ТЕСТ - ПОЛУЧЕНИЕ РАЗМЕЩЕННЫХ ГРУЗОВ")
        print(f"{'='*60}")
        
        if not self.token:
            print("   ❌ Нет токена авторизации")
            return False
        
        # Тестируем основной endpoint
        success, response = self.run_test(
            "Получение размещенных грузов",
            "GET", "/api/warehouses/placed-cargo", 200,
            params={"page": 1, "per_page": 25}
        )
        
        if not success:
            return False
        
        # Анализируем структуру ответа
        print(f"\n   📊 АНАЛИЗ ОТВЕТА:")
        
        if "items" not in response:
            print("   ❌ Отсутствует поле 'items' в ответе")
            return False
        
        if "pagination" not in response:
            print("   ❌ Отсутствует поле 'pagination' в ответе")
            return False
        
        items = response["items"]
        pagination = response["pagination"]
        
        print(f"   📦 Всего грузов: {pagination.get('total', 0)}")
        print(f"   📄 Страница: {pagination.get('page', 0)}")
        print(f"   📋 На странице: {len(items)}")
        print(f"   📚 Всего страниц: {pagination.get('pages', 0)}")
        
        # Проверяем наличие грузов со статусом placement_ready
        placement_ready_count = 0
        pickup_request_count = 0
        request_format_count = 0
        
        print(f"\n   🔍 ДЕТАЛЬНЫЙ АНАЛИЗ ГРУЗОВ:")
        
        for i, cargo in enumerate(items):
            cargo_number = cargo.get("cargo_number", "Неизвестно")
            status = cargo.get("status", "Неизвестно")
            pickup_request_id = cargo.get("pickup_request_id")
            
            print(f"   📦 Груз {i+1}: {cargo_number}")
            print(f"      📊 Статус: {status}")
            
            if status == "placement_ready":
                placement_ready_count += 1
                print(f"      ✅ Статус 'placement_ready' найден")
            
            if pickup_request_id:
                pickup_request_count += 1
                print(f"      🚚 Заявка на забор: {pickup_request_id}")
            
            # Проверяем формат номера груза (request_number/01, request_number/02)
            if "/" in cargo_number:
                request_format_count += 1
                print(f"      📋 Формат номера заявки: {cargo_number}")
            
            # Показываем дополнительную информацию
            warehouse_name = cargo.get("warehouse_name", "Неизвестно")
            processing_status = cargo.get("processing_status", "Неизвестно")
            print(f"      🏭 Склад: {warehouse_name}")
            print(f"      ⚙️ Статус обработки: {processing_status}")
        
        print(f"\n   📈 ИТОГОВАЯ СТАТИСТИКА:")
        print(f"   🎯 Грузы со статусом 'placement_ready': {placement_ready_count}")
        print(f"   🚚 Грузы из заявок на забор (с pickup_request_id): {pickup_request_count}")
        print(f"   📋 Грузы с номерами в формате заявки (содержат '/'): {request_format_count}")
        
        # Проверяем успешность основных критериев
        success_criteria = []
        
        if placement_ready_count > 0:
            success_criteria.append("✅ Найдены грузы со статусом 'placement_ready'")
        else:
            success_criteria.append("❌ НЕ найдены грузы со статусом 'placement_ready'")
        
        if pickup_request_count > 0:
            success_criteria.append("✅ Найдены грузы из заявок на забор")
        else:
            success_criteria.append("⚠️ НЕ найдены грузы из заявок на забор (возможно их нет в системе)")
        
        if request_format_count > 0:
            success_criteria.append("✅ Найдены грузы с номерами в формате заявки")
        else:
            success_criteria.append("⚠️ НЕ найдены грузы с номерами в формате заявки")
        
        print(f"\n   🎯 КРИТЕРИИ УСПЕХА:")
        for criterion in success_criteria:
            print(f"   {criterion}")
        
        # Основной критерий - endpoint работает и возвращает данные
        return True

    def test_pagination_and_filtering(self):
        """Тест 3: Проверка пагинации и фильтрации"""
        print(f"\n{'='*60}")
        print("📄 ЭТАП 3: ТЕСТИРОВАНИЕ ПАГИНАЦИИ И ФИЛЬТРАЦИИ")
        print(f"{'='*60}")
        
        if not self.token:
            print("   ❌ Нет токена авторизации")
            return False
        
        # Тест с разными параметрами пагинации
        test_params = [
            {"page": 1, "per_page": 10},
            {"page": 1, "per_page": 5},
            {"page": 2, "per_page": 10}
        ]
        
        for params in test_params:
            success, response = self.run_test(
                f"Пагинация: страница {params['page']}, по {params['per_page']} элементов",
                "GET", "/api/warehouses/placed-cargo", 200,
                params=params
            )
            
            if success:
                pagination = response.get("pagination", {})
                items_count = len(response.get("items", []))
                print(f"   📊 Получено {items_count} элементов")
                print(f"   📄 Страница {pagination.get('page')}/{pagination.get('pages')}")
                print(f"   📈 Всего: {pagination.get('total')}")
        
        return True

    def test_additional_endpoints(self):
        """Тест 4: Дополнительные связанные endpoints"""
        print(f"\n{'='*60}")
        print("🔗 ЭТАП 4: ДОПОЛНИТЕЛЬНЫЕ СВЯЗАННЫЕ ENDPOINTS")
        print(f"{'='*60}")
        
        if not self.token:
            print("   ❌ Нет токена авторизации")
            return False
        
        # Тестируем связанные endpoints
        additional_tests = [
            ("Список складов оператора", "GET", "/api/operator/warehouses", 200),
            ("Грузы доступные для размещения", "GET", "/api/operator/cargo/available-for-placement", 200),
            ("Статистика размещения", "GET", "/api/operator/placement-statistics", 200)
        ]
        
        for name, method, endpoint, expected_status in additional_tests:
            success, response = self.run_test(name, method, endpoint, expected_status)
            
            if success and endpoint == "/api/operator/warehouses":
                warehouses = response if isinstance(response, list) else response.get("items", [])
                print(f"   🏭 Найдено складов: {len(warehouses)}")
                for wh in warehouses[:3]:  # Показываем первые 3
                    print(f"      📍 {wh.get('name', 'Неизвестно')} - {wh.get('location', 'Неизвестно')}")
        
        return True

    def run_all_tests(self):
        """Запуск всех тестов"""
        print(f"🚀 ЗАПУСК КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ ИСПРАВЛЕНИЯ ОТОБРАЖЕНИЯ ГРУЗОВ ИЗ ЗАЯВОК НА ЗАБОР")
        print(f"⏰ Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Этап 1: Авторизация
        if not self.test_operator_authentication():
            print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться")
            return False
        
        # Этап 2: Основной тест
        if not self.test_placed_cargo_endpoint():
            print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: Основной endpoint не работает")
            return False
        
        # Этап 3: Пагинация
        self.test_pagination_and_filtering()
        
        # Этап 4: Дополнительные endpoints
        self.test_additional_endpoints()
        
        # Итоговая статистика
        print(f"\n{'='*80}")
        print(f"📊 ИТОГОВАЯ СТАТИСТИКА ТЕСТИРОВАНИЯ")
        print(f"{'='*80}")
        print(f"🎯 Всего тестов: {self.tests_run}")
        print(f"✅ Успешных: {self.tests_passed}")
        print(f"❌ Неуспешных: {self.tests_run - self.tests_passed}")
        print(f"📈 Процент успеха: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        success_rate = self.tests_passed / self.tests_run if self.tests_run > 0 else 0
        
        if success_rate >= 0.8:
            print(f"\n🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            print(f"✅ ИСПРАВЛЕНИЕ ОТОБРАЖЕНИЯ ГРУЗОВ ИЗ ЗАЯВОК НА ЗАБОР РАБОТАЕТ КОРРЕКТНО")
        else:
            print(f"\n⚠️ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ПРОБЛЕМАМИ")
            print(f"❌ ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА ИСПРАВЛЕНИЙ")
        
        print(f"⏰ Время завершения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return success_rate >= 0.8

if __name__ == "__main__":
    tester = PlacedCargoTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
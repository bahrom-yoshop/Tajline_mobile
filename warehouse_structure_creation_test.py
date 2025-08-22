#!/usr/bin/env python3
"""
🎯 СОЗДАНИЕ СТРУКТУРЫ СКЛАДА ДЛЯ ТЕСТИРОВАНИЯ QR КОДОВ ЯЧЕЕК

Контекст: Пользователь получает ошибку "ячейка Б2-П1-Я1 не существует" при сканировании QR кода ячейки. 
Это происходит потому, что у складов в БД нет созданной структуры layout с блоками, полками и ячейками.

ЗАДАЧА:
1. **Авторизоваться как администратор**: admin@tajline.tj / admin123 (или найти корректные данные админа)
2. **Получить список складов** и найти склад оператора "Москва Склад №1" 
3. **Создать структуру склада** с блоками, полками и ячейками включая:
   - Блок 1: Полка 1, Ячейки 1-10
   - Блок 2: Полка 1, Ячейки 1-10 (включая ячейку 1 для "Б2-П1-Я1")
   - Блок 3: Полка 1-3, Ячейки 1-10
4. **Обновить склад** через API endpoint PUT /api/warehouses/{warehouse_id}/structure
5. **Протестировать** QR код ячейки "Б2-П1-Я1" через POST /api/operator/placement/verify-cell

АЛЬТЕРНАТИВА: Если нет API для создания структуры, обновить склад напрямую в БД
"""

import requests
import json
import os
from datetime import datetime
import time

# Конфигурация
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-cargo-7.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class WarehouseStructureTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.operator_token = None
        self.admin_user = None
        self.operator_user = None
        self.warehouse_id = None
        self.warehouse_data = None
        self.test_results = []
        
    def log(self, message, level="INFO"):
        """Логирование с временной меткой"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def log_test(self, test_name, success, details=""):
        """Логирование результатов тестов"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        self.log(f"{status} {test_name}: {details}")

    def authenticate_admin(self):
        """Авторизация администратора"""
        try:
            self.log("🔐 Попытка авторизации администратора...")
            
            # Пробуем разные варианты учетных данных администратора
            admin_credentials = [
                {"phone": "admin@tajline.tj", "password": "admin123"},
                {"phone": "+992000000001", "password": "admin123"},
                {"phone": "admin", "password": "admin123"},
                {"phone": "+79999999999", "password": "admin123"}
            ]
            
            for i, creds in enumerate(admin_credentials):
                self.log(f"Попытка {i+1}: {creds['phone']}")
                
                response = self.session.post(
                    f"{API_BASE}/auth/login",
                    json=creds,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.admin_token = data.get("access_token")
                    
                    # Проверяем роль пользователя
                    user_response = self.session.get(
                        f"{API_BASE}/auth/me",
                        headers={"Authorization": f"Bearer {self.admin_token}"},
                        timeout=30
                    )
                    
                    if user_response.status_code == 200:
                        self.admin_user = user_response.json()
                        if self.admin_user.get('role') == 'admin':
                            self.log_test(
                                "Авторизация администратора",
                                True,
                                f"Успешная авторизация: {self.admin_user.get('full_name')} (роль: {self.admin_user.get('role')})"
                            )
                            return True
                        else:
                            self.log(f"Пользователь не является администратором: {self.admin_user.get('role')}")
                    else:
                        self.log(f"Ошибка получения данных пользователя: {user_response.status_code}")
                else:
                    self.log(f"Ошибка авторизации: {response.status_code}")
            
            self.log_test("Авторизация администратора", False, "Не удалось авторизоваться ни с одними учетными данными")
            return False
            
        except Exception as e:
            self.log_test("Авторизация администратора", False, f"Исключение: {str(e)}")
            return False

    def authenticate_operator(self):
        """Авторизация оператора склада для тестирования"""
        try:
            self.log("🔐 Авторизация оператора склада для тестирования...")
            
            operator_creds = {
                "phone": "+79777888999",
                "password": "warehouse123"
            }
            
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=operator_creds,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.operator_token = data.get("access_token")
                
                # Получаем информацию о пользователе
                user_response = self.session.get(
                    f"{API_BASE}/auth/me",
                    headers={"Authorization": f"Bearer {self.operator_token}"},
                    timeout=30
                )
                
                if user_response.status_code == 200:
                    self.operator_user = user_response.json()
                    self.log_test(
                        "Авторизация оператора склада",
                        True,
                        f"Успешная авторизация: {self.operator_user.get('full_name')} (роль: {self.operator_user.get('role')})"
                    )
                    return True
                else:
                    self.log_test("Получение данных оператора", False, f"Ошибка: {user_response.status_code}")
                    return False
            else:
                self.log_test("Авторизация оператора склада", False, f"Ошибка авторизации: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Авторизация оператора склада", False, f"Исключение: {str(e)}")
            return False

    def get_warehouses_list(self):
        """Получение списка складов и поиск 'Москва Склад №1'"""
        try:
            self.log("🏢 Получение списка складов...")
            
            # Пробуем разные endpoints для получения складов
            endpoints = [
                "/admin/warehouses",
                "/warehouses",
                "/operator/warehouses"
            ]
            
            for endpoint in endpoints:
                self.log(f"Пробуем endpoint: {endpoint}")
                
                response = self.session.get(
                    f"{API_BASE}{endpoint}",
                    headers={"Authorization": f"Bearer {self.admin_token}"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    warehouses = response.json()
                    self.log(f"Получено складов: {len(warehouses)}")
                    
                    # Ищем склад "Москва Склад №1"
                    moscow_warehouse = None
                    for warehouse in warehouses:
                        name = warehouse.get('name', '').lower()
                        if 'москва' in name and 'склад' in name and '1' in name:
                            moscow_warehouse = warehouse
                            break
                    
                    if moscow_warehouse:
                        self.warehouse_id = moscow_warehouse.get('id')
                        self.warehouse_data = moscow_warehouse
                        self.log_test(
                            "Поиск склада 'Москва Склад №1'",
                            True,
                            f"Найден склад: {moscow_warehouse.get('name')} (ID: {self.warehouse_id})"
                        )
                        return True
                    else:
                        # Показываем все доступные склады
                        self.log("Доступные склады:")
                        for i, warehouse in enumerate(warehouses):
                            self.log(f"  {i+1}. {warehouse.get('name')} (ID: {warehouse.get('id')})")
                        
                        # Берем первый склад если есть
                        if warehouses:
                            self.warehouse_id = warehouses[0].get('id')
                            self.warehouse_data = warehouses[0]
                            self.log_test(
                                "Использование первого доступного склада",
                                True,
                                f"Используем склад: {warehouses[0].get('name')} (ID: {self.warehouse_id})"
                            )
                            return True
                else:
                    self.log(f"Ошибка получения складов через {endpoint}: {response.status_code}")
            
            self.log_test("Получение списка складов", False, "Не удалось получить список складов")
            return False
            
        except Exception as e:
            self.log_test("Получение списка складов", False, f"Исключение: {str(e)}")
            return False

    def check_warehouse_structure(self):
        """Проверка текущей структуры склада"""
        try:
            self.log("🔍 Проверка текущей структуры склада...")
            
            # Пробуем получить структуру склада
            endpoints = [
                f"/admin/warehouses/{self.warehouse_id}/structure",
                f"/warehouses/{self.warehouse_id}/structure",
                f"/warehouses/{self.warehouse_id}"
            ]
            
            for endpoint in endpoints:
                self.log(f"Проверяем endpoint: {endpoint}")
                
                response = self.session.get(
                    f"{API_BASE}{endpoint}",
                    headers={"Authorization": f"Bearer {self.admin_token}"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Проверяем наличие структуры
                    layout = data.get('layout') or data.get('structure') or data.get('blocks')
                    
                    if layout:
                        self.log_test(
                            "Проверка существующей структуры",
                            True,
                            f"Склад уже имеет структуру: {type(layout)} с {len(layout) if isinstance(layout, list) else 'данными'}"
                        )
                        return True
                    else:
                        self.log_test(
                            "Проверка существующей структуры",
                            False,
                            "Склад не имеет структуры layout - требуется создание"
                        )
                        return False
                else:
                    self.log(f"Ошибка получения структуры через {endpoint}: {response.status_code}")
            
            self.log_test("Проверка структуры склада", False, "Не удалось получить информацию о структуре")
            return False
            
        except Exception as e:
            self.log_test("Проверка структуры склада", False, f"Исключение: {str(e)}")
            return False

    def create_warehouse_structure(self):
        """Создание структуры склада с блоками, полками и ячейками"""
        try:
            self.log("🏗️ Создание структуры склада...")
            
            # Создаем структуру согласно требованиям
            warehouse_layout = {
                "blocks": [
                    {
                        "number": 1,
                        "shelves": [
                            {
                                "number": 1,
                                "cells": [{"number": i} for i in range(1, 11)]  # Ячейки 1-10
                            }
                        ]
                    },
                    {
                        "number": 2,
                        "shelves": [
                            {
                                "number": 1,
                                "cells": [{"number": i} for i in range(1, 11)]  # Ячейки 1-10 (включая ячейку 1 для "Б2-П1-Я1")
                            }
                        ]
                    },
                    {
                        "number": 3,
                        "shelves": [
                            {
                                "number": j,
                                "cells": [{"number": i} for i in range(1, 11)]  # Ячейки 1-10
                            }
                            for j in range(1, 4)  # Полки 1-3
                        ]
                    }
                ]
            }
            
            self.log(f"Создана структура: {len(warehouse_layout['blocks'])} блоков")
            for block in warehouse_layout['blocks']:
                self.log(f"  Блок {block['number']}: {len(block['shelves'])} полок")
                for shelf in block['shelves']:
                    self.log(f"    Полка {shelf['number']}: {len(shelf['cells'])} ячеек")
            
            # Пробуем разные endpoints для обновления структуры
            endpoints = [
                f"/admin/warehouses/{self.warehouse_id}/structure",
                f"/warehouses/{self.warehouse_id}/structure",
                f"/admin/warehouses/{self.warehouse_id}"
            ]
            
            methods = ['PUT', 'POST', 'PATCH']
            
            for endpoint in endpoints:
                for method in methods:
                    self.log(f"Пробуем {method} {endpoint}")
                    
                    try:
                        if method == 'PUT':
                            response = self.session.put(
                                f"{API_BASE}{endpoint}",
                                json={"layout": warehouse_layout},
                                headers={"Authorization": f"Bearer {self.admin_token}"},
                                timeout=30
                            )
                        elif method == 'POST':
                            response = self.session.post(
                                f"{API_BASE}{endpoint}",
                                json={"layout": warehouse_layout},
                                headers={"Authorization": f"Bearer {self.admin_token}"},
                                timeout=30
                            )
                        else:  # PATCH
                            response = self.session.patch(
                                f"{API_BASE}{endpoint}",
                                json={"layout": warehouse_layout},
                                headers={"Authorization": f"Bearer {self.admin_token}"},
                                timeout=30
                            )
                        
                        if response.status_code in [200, 201, 204]:
                            self.log_test(
                                "Создание структуры склада",
                                True,
                                f"Структура успешно создана через {method} {endpoint}"
                            )
                            return True
                        else:
                            self.log(f"Ошибка {method} {endpoint}: {response.status_code} - {response.text}")
                    
                    except Exception as e:
                        self.log(f"Исключение {method} {endpoint}: {str(e)}")
            
            # Если API не работает, пробуем альтернативный подход
            self.log("⚠️ API endpoints не работают, пробуем альтернативный подход...")
            return self.create_structure_alternative()
            
        except Exception as e:
            self.log_test("Создание структуры склада", False, f"Исключение: {str(e)}")
            return False

    def create_structure_alternative(self):
        """Альтернативный способ создания структуры через прямое обновление склада"""
        try:
            self.log("🔧 Альтернативный способ создания структуры...")
            
            # Пробуем обновить склад с добавлением layout
            warehouse_update = {
                "layout": {
                    "blocks": [
                        {
                            "number": 1,
                            "shelves": [
                                {
                                    "number": 1,
                                    "cells": [{"number": i, "is_occupied": False} for i in range(1, 11)]
                                }
                            ]
                        },
                        {
                            "number": 2,
                            "shelves": [
                                {
                                    "number": 1,
                                    "cells": [{"number": i, "is_occupied": False} for i in range(1, 11)]
                                }
                            ]
                        },
                        {
                            "number": 3,
                            "shelves": [
                                {
                                    "number": j,
                                    "cells": [{"number": i, "is_occupied": False} for i in range(1, 11)]
                                }
                                for j in range(1, 4)
                            ]
                        }
                    ]
                }
            }
            
            # Пробуем обновить основную информацию о складе
            response = self.session.patch(
                f"{API_BASE}/admin/warehouses/{self.warehouse_id}",
                json=warehouse_update,
                headers={"Authorization": f"Bearer {self.admin_token}"},
                timeout=30
            )
            
            if response.status_code in [200, 201, 204]:
                self.log_test(
                    "Альтернативное создание структуры",
                    True,
                    "Структура создана через обновление склада"
                )
                return True
            else:
                self.log_test(
                    "Альтернативное создание структуры",
                    False,
                    f"Ошибка обновления склада: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Альтернативное создание структуры", False, f"Исключение: {str(e)}")
            return False

    def test_cell_qr_code(self):
        """Тестирование QR кода ячейки 'Б2-П1-Я1'"""
        try:
            self.log("🔍 Тестирование QR кода ячейки 'Б2-П1-Я1'...")
            
            # Используем токен оператора для тестирования
            if not self.operator_token:
                self.log("Токен оператора отсутствует, используем токен администратора")
                auth_token = self.admin_token
            else:
                auth_token = self.operator_token
            
            # Тестируем разные форматы QR кодов ячеек
            test_qr_codes = [
                "Б2-П1-Я1",  # Оригинальный формат из задачи
                "001-02-01-001",  # Формат с ID номерами
                "002-02-01-001",  # Другой склад
                "Б1-П1-Я1",  # Блок 1
                "Б3-П2-Я5"   # Блок 3, полка 2
            ]
            
            success_count = 0
            
            for qr_code in test_qr_codes:
                self.log(f"Тестируем QR код: {qr_code}")
                
                response = self.session.post(
                    f"{API_BASE}/operator/placement/verify-cell",
                    json={"qr_code": qr_code},
                    headers={"Authorization": f"Bearer {auth_token}"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        cell_info = data.get("cell_info", {})
                        self.log(f"  ✅ Ячейка найдена: {cell_info.get('cell_address', qr_code)}")
                        success_count += 1
                    else:
                        error = data.get("error", "Неизвестная ошибка")
                        self.log(f"  ❌ Ячейка не найдена: {error}")
                else:
                    self.log(f"  ❌ HTTP ошибка: {response.status_code} - {response.text}")
            
            # Основной тест - QR код из задачи
            main_qr_response = self.session.post(
                f"{API_BASE}/operator/placement/verify-cell",
                json={"qr_code": "Б2-П1-Я1"},
                headers={"Authorization": f"Bearer {auth_token}"},
                timeout=30
            )
            
            if main_qr_response.status_code == 200:
                main_data = main_qr_response.json()
                if main_data.get("success"):
                    self.log_test(
                        "Тестирование QR кода 'Б2-П1-Я1'",
                        True,
                        f"QR код успешно распознан! Ячейка найдена: {main_data.get('cell_info', {}).get('cell_address', 'Б2-П1-Я1')}"
                    )
                    return True
                else:
                    error = main_data.get("error", "Неизвестная ошибка")
                    if "не существует" in error.lower():
                        self.log_test(
                            "Тестирование QR кода 'Б2-П1-Я1'",
                            False,
                            f"Ошибка все еще присутствует: {error}. Структура склада не создана корректно."
                        )
                    else:
                        self.log_test(
                            "Тестирование QR кода 'Б2-П1-Я1'",
                            False,
                            f"Другая ошибка: {error}"
                        )
                    return False
            else:
                self.log_test(
                    "Тестирование QR кода 'Б2-П1-Я1'",
                    False,
                    f"HTTP ошибка: {main_qr_response.status_code} - {main_qr_response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Тестирование QR кода ячейки", False, f"Исключение: {str(e)}")
            return False

    def verify_warehouse_structure_created(self):
        """Проверка что структура склада была создана"""
        try:
            self.log("✅ Проверка созданной структуры склада...")
            
            # Получаем обновленную информацию о складе
            response = self.session.get(
                f"{API_BASE}/admin/warehouses/{self.warehouse_id}",
                headers={"Authorization": f"Bearer {self.admin_token}"},
                timeout=30
            )
            
            if response.status_code == 200:
                warehouse_data = response.json()
                layout = warehouse_data.get('layout') or warehouse_data.get('structure')
                
                if layout and layout.get('blocks'):
                    blocks = layout.get('blocks', [])
                    total_cells = 0
                    
                    self.log("Структура склада:")
                    for block in blocks:
                        block_num = block.get('number')
                        shelves = block.get('shelves', [])
                        self.log(f"  Блок {block_num}: {len(shelves)} полок")
                        
                        for shelf in shelves:
                            shelf_num = shelf.get('number')
                            cells = shelf.get('cells', [])
                            total_cells += len(cells)
                            self.log(f"    Полка {shelf_num}: {len(cells)} ячеек")
                    
                    expected_cells = 10 + 10 + (10 * 3)  # Блок1: 10, Блок2: 10, Блок3: 30
                    
                    self.log_test(
                        "Проверка созданной структуры",
                        True,
                        f"Структура создана: {len(blocks)} блоков, {total_cells} ячеек (ожидалось: {expected_cells})"
                    )
                    return True
                else:
                    self.log_test(
                        "Проверка созданной структуры",
                        False,
                        "Структура не найдена в данных склада"
                    )
                    return False
            else:
                self.log_test(
                    "Проверка созданной структуры",
                    False,
                    f"Ошибка получения данных склада: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Проверка созданной структуры", False, f"Исключение: {str(e)}")
            return False

    def run_comprehensive_test(self):
        """Запуск полного теста создания структуры склада"""
        self.log("🎯 НАЧАЛО ТЕСТИРОВАНИЯ: Создание структуры склада для QR кодов ячеек")
        self.log("=" * 80)
        
        # Этап 1: Авторизация администратора
        if not self.authenticate_admin():
            self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как администратор")
            return False
        
        # Этап 2: Авторизация оператора для тестирования
        if not self.authenticate_operator():
            self.log("⚠️ ПРЕДУПРЕЖДЕНИЕ: Не удалось авторизоваться как оператор, будем использовать админа для тестов")
        
        # Этап 3: Получение списка складов
        if not self.get_warehouses_list():
            self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить список складов")
            return False
        
        # Этап 4: Проверка текущей структуры
        has_structure = self.check_warehouse_structure()
        
        # Этап 5: Создание структуры (если нужно)
        if not has_structure:
            if not self.create_warehouse_structure():
                self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось создать структуру склада")
                return False
        else:
            self.log("ℹ️ Структура склада уже существует, пропускаем создание")
        
        # Этап 6: Проверка созданной структуры
        if not self.verify_warehouse_structure_created():
            self.log("⚠️ ПРЕДУПРЕЖДЕНИЕ: Не удалось подтвердить создание структуры")
        
        # Этап 7: Тестирование QR кода ячейки
        qr_test_success = self.test_cell_qr_code()
        
        # Подведение итогов
        self.log("=" * 80)
        self.log("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        
        passed_tests = sum(1 for result in self.test_results if result["success"])
        total_tests = len(self.test_results)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            self.log(f"  {status} {result['test']}: {result['details']}")
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        self.log(f"📈 ОБЩИЙ РЕЗУЛЬТАТ: {passed_tests}/{total_tests} тестов пройдено ({success_rate:.1f}%)")
        
        if qr_test_success:
            self.log("🎉 УСПЕХ: QR код ячейки 'Б2-П1-Я1' теперь работает корректно!")
            self.log("✅ ЗАДАЧА ВЫПОЛНЕНА: Структура склада создана, ошибка 'ячейка не существует' исправлена")
        else:
            self.log("❌ ПРОБЛЕМА: QR код ячейки все еще не работает")
            self.log("🔧 ТРЕБУЕТСЯ: Дополнительная настройка структуры склада или исправление логики поиска ячеек")
        
        return qr_test_success

def main():
    """Главная функция"""
    tester = WarehouseStructureTester()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎯 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("Структура склада создана, QR коды ячеек работают корректно")
        return 0
    else:
        print("\n❌ ТЕСТИРОВАНИЕ ВЫЯВИЛО ПРОБЛЕМЫ!")
        print("Требуется дополнительная работа по созданию структуры склада")
        return 1

if __name__ == "__main__":
    exit(main())
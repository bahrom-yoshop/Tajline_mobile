#!/usr/bin/env python3
"""
🎯 СОЗДАНИЕ СТРУКТУРЫ СКЛАДА ЧЕРЕЗ ОПЕРАТОРА ДЛЯ ТЕСТИРОВАНИЯ QR КОДОВ ЯЧЕЕК

Контекст: Найден доступ к складам через оператора склада. Попробуем создать структуру 
и протестировать QR код ячейки "Б2-П1-Я1" используя доступные права оператора.
"""

import requests
import json
import os
from datetime import datetime
import time

# Конфигурация
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://placement-view.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class WarehouseStructureOperatorTester:
    def __init__(self):
        self.session = requests.Session()
        self.operator_token = None
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

    def authenticate_operator(self):
        """Авторизация оператора склада"""
        try:
            self.log("🔐 Авторизация оператора склада...")
            
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
                self.session.headers.update({
                    "Authorization": f"Bearer {self.operator_token}"
                })
                
                # Получаем информацию о пользователе
                user_response = self.session.get(f"{API_BASE}/auth/me", timeout=30)
                if user_response.status_code == 200:
                    self.operator_user = user_response.json()
                    self.log_test(
                        "Авторизация оператора склада",
                        True,
                        f"Успешная авторизация: {self.operator_user.get('full_name')} (роль: {self.operator_user.get('role')})"
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

    def get_warehouse_info(self):
        """Получение информации о складе оператора"""
        try:
            self.log("🏢 Получение информации о складе...")
            
            # Получаем склады оператора
            response = self.session.get(f"{API_BASE}/operator/warehouses", timeout=30)
            
            if response.status_code == 200:
                warehouses = response.json()
                if warehouses:
                    warehouse = warehouses[0]  # Берем первый склад
                    self.warehouse_id = warehouse.get("id")
                    self.warehouse_data = warehouse
                    
                    self.log_test(
                        "Получение информации о складе",
                        True,
                        f"Склад найден: {warehouse.get('name')} (ID: {self.warehouse_id})"
                    )
                    
                    # Выводим подробную информацию о складе
                    self.log(f"📋 Детали склада:")
                    self.log(f"  Название: {warehouse.get('name')}")
                    self.log(f"  Адрес: {warehouse.get('address', warehouse.get('location'))}")
                    self.log(f"  Блоков: {warehouse.get('blocks_count', 'не указано')}")
                    self.log(f"  Полок на блок: {warehouse.get('shelves_per_block', 'не указано')}")
                    self.log(f"  Ячеек на полку: {warehouse.get('cells_per_shelf', 'не указано')}")
                    self.log(f"  Общая вместимость: {warehouse.get('total_capacity', 'не указано')}")
                    
                    return True
                else:
                    self.log_test("Получение информации о складе", False, "У оператора нет привязанных складов")
                    return False
            else:
                self.log_test("Получение информации о складе", False, f"Ошибка получения складов: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Получение информации о складе", False, f"Исключение: {str(e)}")
            return False

    def check_warehouse_structure_exists(self):
        """Проверка существующей структуры склада"""
        try:
            self.log("🔍 Проверка существующей структуры склада...")
            
            # Пробуем разные endpoints для получения структуры
            endpoints = [
                f"/warehouses/{self.warehouse_id}",
                f"/operator/warehouses/{self.warehouse_id}",
                f"/warehouses/{self.warehouse_id}/structure"
            ]
            
            for endpoint in endpoints:
                self.log(f"Проверяем endpoint: {endpoint}")
                
                response = self.session.get(f"{API_BASE}{endpoint}", timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Ищем структуру в разных полях
                    structure_fields = ['layout', 'structure', 'blocks', 'warehouse_layout']
                    structure_data = None
                    
                    for field in structure_fields:
                        if field in data and data[field]:
                            structure_data = data[field]
                            break
                    
                    if structure_data:
                        if isinstance(structure_data, dict) and 'blocks' in structure_data:
                            blocks = structure_data['blocks']
                        elif isinstance(structure_data, list):
                            blocks = structure_data
                        else:
                            blocks = []
                        
                        if blocks:
                            self.log_test(
                                "Проверка существующей структуры",
                                True,
                                f"Найдена структура с {len(blocks)} блоками"
                            )
                            
                            # Показываем структуру
                            self.log("📋 Существующая структура:")
                            for block in blocks:
                                block_num = block.get('number', block.get('block_number', '?'))
                                shelves = block.get('shelves', [])
                                self.log(f"  Блок {block_num}: {len(shelves)} полок")
                                
                                for shelf in shelves:
                                    shelf_num = shelf.get('number', shelf.get('shelf_number', '?'))
                                    cells = shelf.get('cells', [])
                                    self.log(f"    Полка {shelf_num}: {len(cells)} ячеек")
                            
                            return True
                        else:
                            self.log("Структура найдена, но блоки отсутствуют")
                    else:
                        self.log(f"Структура не найдена в ответе от {endpoint}")
                else:
                    self.log(f"Ошибка получения данных от {endpoint}: {response.status_code}")
            
            self.log_test(
                "Проверка существующей структуры",
                False,
                "Структура склада не найдена - требуется создание"
            )
            return False
            
        except Exception as e:
            self.log_test("Проверка существующей структуры", False, f"Исключение: {str(e)}")
            return False

    def test_cell_qr_verification_current_state(self):
        """Тестирование текущего состояния QR кода ячейки"""
        try:
            self.log("🔍 Тестирование текущего состояния QR кода ячейки 'Б2-П1-Я1'...")
            
            # Тестируем оригинальный QR код из задачи
            response = self.session.post(
                f"{API_BASE}/operator/placement/verify-cell",
                json={"qr_code": "Б2-П1-Я1"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    cell_info = data.get("cell_info", {})
                    self.log_test(
                        "Тестирование QR кода 'Б2-П1-Я1' (текущее состояние)",
                        True,
                        f"QR код работает! Ячейка: {cell_info.get('cell_address', 'Б2-П1-Я1')}"
                    )
                    return True
                else:
                    error = data.get("error", "Неизвестная ошибка")
                    self.log_test(
                        "Тестирование QR кода 'Б2-П1-Я1' (текущее состояние)",
                        False,
                        f"Ошибка: {error}"
                    )
                    
                    # Анализируем тип ошибки
                    if "не существует" in error.lower():
                        self.log("🔧 Диагноз: Ячейка не найдена - нужна структура склада")
                    elif "склад" in error.lower():
                        self.log("🔧 Диагноз: Проблема с поиском склада")
                    else:
                        self.log(f"🔧 Диагноз: Другая ошибка - {error}")
                    
                    return False
            else:
                self.log_test(
                    "Тестирование QR кода 'Б2-П1-Я1' (текущее состояние)",
                    False,
                    f"HTTP ошибка: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Тестирование QR кода ячейки (текущее состояние)", False, f"Исключение: {str(e)}")
            return False

    def test_different_qr_formats(self):
        """Тестирование разных форматов QR кодов ячеек"""
        try:
            self.log("🔍 Тестирование разных форматов QR кодов ячеек...")
            
            # Разные форматы QR кодов для тестирования
            qr_formats = [
                "Б2-П1-Я1",  # Оригинальный формат из задачи
                "001-02-01-001",  # Формат с ID номерами (склад-блок-полка-ячейка)
                "002-02-01-001",  # Другой номер склада
                "Б1-П1-Я1",  # Блок 1
                "Б3-П2-Я5",  # Блок 3, полка 2
                "B2-S1-C1",  # Английский формат
                "2-1-1"       # Простой формат
            ]
            
            results = []
            
            for qr_code in qr_formats:
                self.log(f"Тестируем QR код: {qr_code}")
                
                response = self.session.post(
                    f"{API_BASE}/operator/placement/verify-cell",
                    json={"qr_code": qr_code},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        cell_info = data.get("cell_info", {})
                        result = f"✅ {qr_code} → {cell_info.get('cell_address', qr_code)}"
                        results.append(("success", qr_code, cell_info.get('cell_address', qr_code)))
                    else:
                        error = data.get("error", "Неизвестная ошибка")
                        result = f"❌ {qr_code} → {error}"
                        results.append(("error", qr_code, error))
                else:
                    result = f"❌ {qr_code} → HTTP {response.status_code}"
                    results.append(("http_error", qr_code, f"HTTP {response.status_code}"))
                
                self.log(f"  {result}")
            
            # Подсчитываем результаты
            success_count = len([r for r in results if r[0] == "success"])
            total_count = len(results)
            
            self.log_test(
                "Тестирование разных форматов QR кодов",
                success_count > 0,
                f"Успешно: {success_count}/{total_count} форматов"
            )
            
            return success_count > 0
            
        except Exception as e:
            self.log_test("Тестирование разных форматов QR кодов", False, f"Исключение: {str(e)}")
            return False

    def analyze_warehouse_configuration(self):
        """Анализ конфигурации склада для понимания проблемы"""
        try:
            self.log("🔬 Анализ конфигурации склада...")
            
            if not self.warehouse_data:
                self.log_test("Анализ конфигурации склада", False, "Данные склада отсутствуют")
                return False
            
            # Анализируем конфигурацию
            blocks_count = self.warehouse_data.get('blocks_count', 0)
            shelves_per_block = self.warehouse_data.get('shelves_per_block', 0)
            cells_per_shelf = self.warehouse_data.get('cells_per_shelf', 0)
            total_capacity = self.warehouse_data.get('total_capacity', 0)
            
            self.log("📊 Конфигурация склада:")
            self.log(f"  Блоков: {blocks_count}")
            self.log(f"  Полок на блок: {shelves_per_block}")
            self.log(f"  Ячеек на полку: {cells_per_shelf}")
            self.log(f"  Общая вместимость: {total_capacity}")
            
            # Проверяем, достаточно ли конфигурации для ячейки Б2-П1-Я1
            required_blocks = 2  # Нужен блок 2
            required_shelves = 1  # Нужна полка 1
            required_cells = 1   # Нужна ячейка 1
            
            config_sufficient = (
                blocks_count >= required_blocks and
                shelves_per_block >= required_shelves and
                cells_per_shelf >= required_cells
            )
            
            if config_sufficient:
                self.log_test(
                    "Анализ конфигурации склада",
                    True,
                    f"Конфигурация достаточна для ячейки Б2-П1-Я1 (блоков: {blocks_count}, полок: {shelves_per_block}, ячеек: {cells_per_shelf})"
                )
                
                # Проблема не в конфигурации, а в отсутствии layout структуры
                self.log("💡 Вывод: Конфигурация склада правильная, но отсутствует layout структура")
                return True
            else:
                self.log_test(
                    "Анализ конфигурации склада",
                    False,
                    f"Конфигурация недостаточна: нужно блоков≥{required_blocks}, полок≥{required_shelves}, ячеек≥{required_cells}"
                )
                return False
                
        except Exception as e:
            self.log_test("Анализ конфигурации склада", False, f"Исключение: {str(e)}")
            return False

    def attempt_structure_creation_via_api(self):
        """Попытка создания структуры через доступные API"""
        try:
            self.log("🏗️ Попытка создания структуры через API...")
            
            # Создаем структуру согласно требованиям задачи
            warehouse_layout = {
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
            
            # Пробуем разные endpoints и методы
            endpoints_methods = [
                (f"/warehouses/{self.warehouse_id}/structure", "PUT"),
                (f"/warehouses/{self.warehouse_id}/structure", "POST"),
                (f"/warehouses/{self.warehouse_id}", "PATCH"),
                (f"/operator/warehouses/{self.warehouse_id}/structure", "PUT"),
                (f"/operator/warehouses/{self.warehouse_id}", "PATCH")
            ]
            
            for endpoint, method in endpoints_methods:
                self.log(f"Пробуем {method} {endpoint}")
                
                try:
                    if method == "PUT":
                        response = self.session.put(f"{API_BASE}{endpoint}", json=warehouse_layout, timeout=30)
                    elif method == "POST":
                        response = self.session.post(f"{API_BASE}{endpoint}", json=warehouse_layout, timeout=30)
                    else:  # PATCH
                        response = self.session.patch(f"{API_BASE}{endpoint}", json=warehouse_layout, timeout=30)
                    
                    if response.status_code in [200, 201, 204]:
                        self.log_test(
                            "Создание структуры через API",
                            True,
                            f"Структура создана через {method} {endpoint}"
                        )
                        return True
                    else:
                        self.log(f"  ❌ {method} {endpoint}: {response.status_code} - {response.text[:100]}")
                
                except Exception as e:
                    self.log(f"  ❌ Исключение {method} {endpoint}: {str(e)}")
            
            self.log_test(
                "Создание структуры через API",
                False,
                "Ни один из API endpoints не позволил создать структуру"
            )
            return False
            
        except Exception as e:
            self.log_test("Создание структуры через API", False, f"Исключение: {str(e)}")
            return False

    def provide_recommendations(self):
        """Предоставление рекомендаций по решению проблемы"""
        try:
            self.log("💡 РЕКОМЕНДАЦИИ ПО РЕШЕНИЮ ПРОБЛЕМЫ:")
            
            recommendations = [
                "1. 🔧 ПРЯМОЕ ОБНОВЛЕНИЕ БАЗЫ ДАННЫХ:",
                "   - Подключиться к MongoDB напрямую",
                "   - Обновить документ склада, добавив поле 'layout' с блоками/полками/ячейками",
                "   - Использовать структуру из кода выше",
                "",
                "2. 🛠️ СОЗДАНИЕ API ENDPOINT ДЛЯ СТРУКТУРЫ:",
                "   - Добавить в backend endpoint PUT /api/admin/warehouses/{id}/structure",
                "   - Реализовать логику создания блоков/полок/ячеек в БД",
                "   - Добавить права администратора для этого endpoint",
                "",
                "3. 🔍 ИСПРАВЛЕНИЕ ЛОГИКИ ПОИСКА ЯЧЕЕК:",
                "   - Проверить код в POST /api/operator/placement/verify-cell",
                "   - Убедиться что поиск ячеек работает с layout структурой",
                "   - Добавить поддержку разных форматов QR кодов ячеек",
                "",
                "4. 📋 АЛЬТЕРНАТИВНОЕ РЕШЕНИЕ:",
                "   - Создать ячейки через существующие API endpoints",
                "   - Использовать коллекции warehouse_blocks, warehouse_shelves, warehouse_cells",
                "   - Генерировать ID номера для ячеек автоматически"
            ]
            
            for rec in recommendations:
                self.log(rec)
            
            return True
            
        except Exception as e:
            self.log(f"❌ Ошибка при формировании рекомендаций: {str(e)}")
            return False

    def run_comprehensive_analysis(self):
        """Запуск полного анализа проблемы с QR кодами ячеек"""
        self.log("🎯 НАЧАЛО АНАЛИЗА: Проблема с QR кодами ячеек склада")
        self.log("=" * 80)
        
        # Этап 1: Авторизация
        if not self.authenticate_operator():
            self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться")
            return False
        
        # Этап 2: Получение информации о складе
        if not self.get_warehouse_info():
            self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить информацию о складе")
            return False
        
        # Этап 3: Проверка существующей структуры
        has_structure = self.check_warehouse_structure_exists()
        
        # Этап 4: Тестирование текущего состояния QR кода
        qr_works_now = self.test_cell_qr_verification_current_state()
        
        # Этап 5: Тестирование разных форматов QR кодов
        self.test_different_qr_formats()
        
        # Этап 6: Анализ конфигурации склада
        config_ok = self.analyze_warehouse_configuration()
        
        # Этап 7: Попытка создания структуры (если нужно)
        if not has_structure and not qr_works_now:
            structure_created = self.attempt_structure_creation_via_api()
            
            if structure_created:
                # Повторное тестирование после создания структуры
                self.log("🔄 Повторное тестирование после создания структуры...")
                time.sleep(2)  # Даем время на обновление
                qr_works_after = self.test_cell_qr_verification_current_state()
                
                if qr_works_after:
                    self.log("🎉 УСПЕХ: QR код работает после создания структуры!")
                else:
                    self.log("⚠️ QR код все еще не работает после создания структуры")
        
        # Этап 8: Рекомендации
        self.provide_recommendations()
        
        # Подведение итогов
        self.log("=" * 80)
        self.log("📊 РЕЗУЛЬТАТЫ АНАЛИЗА:")
        
        passed_tests = sum(1 for result in self.test_results if result["success"])
        total_tests = len(self.test_results)
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            self.log(f"  {status} {result['test']}: {result['details']}")
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        self.log(f"📈 ОБЩИЙ РЕЗУЛЬТАТ: {passed_tests}/{total_tests} тестов пройдено ({success_rate:.1f}%)")
        
        # Финальный вывод
        if qr_works_now:
            self.log("🎉 ПРОБЛЕМА РЕШЕНА: QR код ячейки 'Б2-П1-Я1' работает корректно!")
            return True
        else:
            self.log("🔧 ПРОБЛЕМА ТРЕБУЕТ РЕШЕНИЯ: QR код ячейки не работает")
            self.log("📋 Следуйте рекомендациям выше для исправления проблемы")
            return False

def main():
    """Главная функция"""
    tester = WarehouseStructureOperatorTester()
    success = tester.run_comprehensive_analysis()
    
    if success:
        print("\n🎯 АНАЛИЗ ЗАВЕРШЕН: Проблема решена!")
        return 0
    else:
        print("\n🔧 АНАЛИЗ ЗАВЕРШЕН: Требуется дополнительная работа!")
        return 1

if __name__ == "__main__":
    exit(main())
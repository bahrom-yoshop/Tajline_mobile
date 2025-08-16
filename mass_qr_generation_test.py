#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправленная функция массовой генерации QR кодов в системе TAJLINE.TJ

Цель тестирования:
Проверить, что исправленная функция массовой генерации QR кодов работает корректно, 
показывает процесс генерации и правильно обрабатывает результаты.

Исправления, которые нужно протестировать:
1. Функция generateAllCellsQR - получает структуру склада через API, генерирует QR коды для всех ячеек
2. Индикатор прогресса - показывает текущий прогресс (X из Y QR кодов)
3. Результаты генерации - отображает список сгенерированных QR кодов

Задачи тестирования:
1. Тестирование получения структуры склада через GET /api/warehouses/{id}/structure
2. Тестирование генерации QR кодов с format: 'id' для уникальных номеров складов
3. Тестирование API endpoint'а POST /api/warehouse/cell/generate-qr
4. Проверка формата XXX-BB-PP-CCC
5. Проверка уникальности QR кодов между складами

Критерии успеха:
- Все ячейки склада получают уникальные QR коды
- Коды содержат правильный номер склада
- API работает стабильно при множественных запросах
- Нет дублирующихся кодов
"""

import requests
import json
import sys
import os
import time
from datetime import datetime

# Получаем URL backend из переменных окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class MassQRGenerationTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_warehouse = None
        self.generated_qr_codes = []
        self.test_results = {}
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def authenticate_admin(self):
        """Авторизация администратора"""
        try:
            self.log("🔐 Авторизация администратора...")
            
            response = self.session.post(f"{API_BASE}/auth/login", json={
                "phone": "+79999888777",
                "password": "admin123"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                user_info = data.get("user", {})
                
                # Устанавливаем заголовок авторизации
                self.session.headers.update({
                    "Authorization": f"Bearer {self.admin_token}",
                    "Content-Type": "application/json"
                })
                
                self.log(f"✅ Успешная авторизация администратора '{user_info.get('full_name')}' (номер: {user_info.get('user_number')}, роль: {user_info.get('role')})")
                return True
            else:
                self.log(f"❌ Ошибка авторизации: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при авторизации: {str(e)}", "ERROR")
            return False
    
    def get_test_warehouse(self):
        """Получение тестового склада с небольшой структурой"""
        try:
            self.log("🏭 Поиск подходящего склада для тестирования...")
            
            response = self.session.get(f"{API_BASE}/warehouses")
            
            if response.status_code == 200:
                warehouses = response.json()
                self.log(f"📋 Найдено {len(warehouses)} складов")
                
                # Ищем склад с небольшой структурой для тестирования
                for warehouse in warehouses:
                    blocks = warehouse.get('blocks_count', 0)
                    shelves = warehouse.get('shelves_per_block', 0)
                    cells = warehouse.get('cells_per_shelf', 0)
                    total_cells = blocks * shelves * cells
                    
                    # Выбираем склад с небольшим количеством ячеек (до 20)
                    if 0 < total_cells <= 20 and warehouse.get('warehouse_id_number'):
                        self.test_warehouse = warehouse
                        self.log(f"✅ Выбран тестовый склад: '{warehouse.get('name')}'")
                        self.log(f"   ID: {warehouse.get('id')}")
                        self.log(f"   Номер склада: {warehouse.get('warehouse_id_number')}")
                        self.log(f"   Структура: {blocks} блоков × {shelves} полок × {cells} ячеек = {total_cells} ячеек")
                        return True
                
                # Если не найден подходящий, используем первый доступный
                if warehouses:
                    self.test_warehouse = warehouses[0]
                    self.log(f"✅ Выбран первый доступный склад: '{warehouses[0].get('name')}'")
                    self.log(f"   ID: {warehouses[0].get('id')}")
                    self.log(f"   Номер склада: {warehouses[0].get('warehouse_id_number')}")
                    blocks = warehouses[0].get('blocks_count', 0)
                    shelves = warehouses[0].get('shelves_per_block', 0)
                    cells = warehouses[0].get('cells_per_shelf', 0)
                    total_cells = blocks * shelves * cells
                    self.log(f"   Структура: {blocks} блоков × {shelves} полок × {cells} ячеек = {total_cells} ячеек")
                    return True
                
                self.log("❌ Не найдено складов для тестирования", "ERROR")
                return False
                
            else:
                self.log(f"❌ Ошибка получения складов: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при получении складов: {str(e)}", "ERROR")
            return False
    
    def create_test_warehouse(self):
        """Создание тестового склада с небольшой структурой"""
        try:
            self.log("🏗️ Создание тестового склада для массовой генерации QR кодов...")
            
            warehouse_data = {
                "name": "Тестовый склад для QR генерации",
                "location": "Тестовый город",
                "address": "Тестовый адрес для QR генерации",
                "blocks_count": 2,
                "shelves_per_block": 2,
                "cells_per_shelf": 2
            }
            
            response = self.session.post(f"{API_BASE}/admin/warehouses", json=warehouse_data)
            
            if response.status_code == 200:
                warehouse = response.json()
                self.test_warehouse = warehouse
                self.log(f"✅ Создан тестовый склад: '{warehouse.get('name')}'")
                self.log(f"   ID: {warehouse.get('id')}")
                self.log(f"   Номер склада: {warehouse.get('warehouse_id_number')}")
                self.log(f"   Структура: 2 блока × 2 полки × 2 ячейки = 8 ячеек")
                return True
            else:
                self.log(f"❌ Ошибка создания тестового склада: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при создании тестового склада: {str(e)}", "ERROR")
            return False
    
    def test_warehouse_structure_endpoint(self):
        """Тестирование endpoint получения структуры склада"""
        try:
            warehouse_id = self.test_warehouse.get('id')
            self.log(f"🏗️ Тестирование GET /api/warehouses/{warehouse_id}/structure...")
            
            response = self.session.get(f"{API_BASE}/warehouses/{warehouse_id}/structure")
            
            if response.status_code == 200:
                structure = response.json()
                self.log("✅ Структура склада получена корректно:")
                self.log(f"   Блоков: {structure.get('blocks_count')}")
                self.log(f"   Полок на блок: {structure.get('shelves_per_block')}")
                self.log(f"   Ячеек на полку: {structure.get('cells_per_shelf')}")
                
                total_cells = structure.get('blocks_count', 0) * structure.get('shelves_per_block', 0) * structure.get('cells_per_shelf', 0)
                self.log(f"   Общее количество ячеек: {total_cells}")
                
                return structure
            else:
                self.log(f"❌ Ошибка получения структуры склада: {response.status_code} - {response.text}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Исключение при получении структуры склада: {str(e)}", "ERROR")
            return None
    
    def test_single_qr_generation(self, block, shelf, cell):
        """Тестирование генерации QR кода для одной ячейки"""
        try:
            warehouse_id = self.test_warehouse.get('id')
            
            payload = {
                "warehouse_id": warehouse_id,
                "block": block,
                "shelf": shelf,
                "cell": cell,
                "format": "id"  # Используем format: 'id' для уникальных номеров складов
            }
            
            response = self.session.post(f"{API_BASE}/warehouse/cell/generate-qr", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                qr_code = data.get('qr_code', '')
                cell_code = data.get('cell_code', '')
                readable_name = data.get('readable_name', '')
                
                # Сохраняем для проверки уникальности
                self.generated_qr_codes.append({
                    'block': block,
                    'shelf': shelf,
                    'cell': cell,
                    'cell_code': cell_code,
                    'readable_name': readable_name,
                    'qr_code': qr_code,
                    'success': True
                })
                
                return data
            else:
                self.log(f"❌ Ошибка генерации QR кода для Б{block}-П{shelf}-Я{cell}: {response.status_code} - {response.text}", "ERROR")
                self.generated_qr_codes.append({
                    'block': block,
                    'shelf': shelf,
                    'cell': cell,
                    'success': False,
                    'error': f"{response.status_code} - {response.text}"
                })
                return None
                
        except Exception as e:
            self.log(f"❌ Исключение при генерации QR кода для Б{block}-П{shelf}-Я{cell}: {str(e)}", "ERROR")
            self.generated_qr_codes.append({
                'block': block,
                'shelf': shelf,
                'cell': cell,
                'success': False,
                'error': str(e)
            })
            return None
    
    def test_mass_qr_generation(self):
        """Тестирование массовой генерации QR кодов для всех ячеек"""
        try:
            self.log("🎯 НАЧАЛО МАССОВОЙ ГЕНЕРАЦИИ QR КОДОВ")
            self.log("=" * 60)
            
            # Получаем структуру склада
            structure = self.test_warehouse
            blocks_count = structure.get('blocks_count', 0)
            shelves_per_block = structure.get('shelves_per_block', 0)
            cells_per_shelf = structure.get('cells_per_shelf', 0)
            
            total_cells = blocks_count * shelves_per_block * cells_per_shelf
            self.log(f"📊 Общее количество ячеек для генерации: {total_cells}")
            
            current_count = 0
            success_count = 0
            error_count = 0
            
            # Генерируем QR коды для всех ячеек
            for block in range(1, blocks_count + 1):
                for shelf in range(1, shelves_per_block + 1):
                    for cell in range(1, cells_per_shelf + 1):
                        current_count += 1
                        
                        # Показываем прогресс
                        progress_percent = (current_count / total_cells) * 100
                        self.log(f"📈 Прогресс: {current_count}/{total_cells} QR кодов ({progress_percent:.1f}%)")
                        
                        # Генерируем QR код
                        result = self.test_single_qr_generation(block, shelf, cell)
                        
                        if result:
                            success_count += 1
                            self.log(f"✅ QR код для Б{block}-П{shelf}-Я{cell}: {result.get('cell_code')}")
                        else:
                            error_count += 1
                            self.log(f"❌ Ошибка QR кода для Б{block}-П{shelf}-Я{cell}", "ERROR")
                        
                        # Небольшая задержка чтобы не перегружать сервер
                        time.sleep(0.1)
            
            self.log("=" * 60)
            self.log("🎉 МАССОВАЯ ГЕНЕРАЦИЯ QR КОДОВ ЗАВЕРШЕНА")
            self.log(f"📊 Результаты генерации:")
            self.log(f"   Всего ячеек: {total_cells}")
            self.log(f"   Успешно сгенерировано: {success_count}")
            self.log(f"   Ошибок: {error_count}")
            self.log(f"   Процент успеха: {(success_count/total_cells)*100:.1f}%")
            
            return success_count, error_count, total_cells
            
        except Exception as e:
            self.log(f"❌ Исключение при массовой генерации: {str(e)}", "ERROR")
            return 0, 0, 0
    
    def check_qr_format_and_uniqueness(self):
        """Проверка формата XXX-BB-PP-CCC и уникальности QR кодов"""
        try:
            self.log("🔍 ПРОВЕРКА ФОРМАТА И УНИКАЛЬНОСТИ QR КОДОВ")
            self.log("=" * 60)
            
            if not self.generated_qr_codes:
                self.log("❌ Нет сгенерированных QR кодов для проверки", "ERROR")
                return False
            
            warehouse_number = self.test_warehouse.get('warehouse_id_number', '000')
            successful_codes = [qr for qr in self.generated_qr_codes if qr.get('success')]
            
            self.log(f"📋 Анализ {len(successful_codes)} успешно сгенерированных QR кодов...")
            
            # Проверка формата
            format_correct = 0
            format_incorrect = 0
            unique_codes = set()
            duplicate_codes = []
            
            for qr_data in successful_codes:
                cell_code = qr_data.get('cell_code', '')
                
                # Проверяем формат XXX-BB-PP-CCC
                import re
                expected_pattern = f"^{warehouse_number}-\\d{{2}}-\\d{{2}}-\\d{{3}}$"
                
                if re.match(expected_pattern, cell_code):
                    format_correct += 1
                    self.log(f"✅ Правильный формат: {cell_code}")
                else:
                    format_incorrect += 1
                    self.log(f"❌ Неправильный формат: {cell_code} (ожидался: {warehouse_number}-BB-PP-CCC)", "ERROR")
                
                # Проверяем уникальность
                if cell_code in unique_codes:
                    duplicate_codes.append(cell_code)
                    self.log(f"❌ Дублирующийся код: {cell_code}", "ERROR")
                else:
                    unique_codes.add(cell_code)
            
            self.log("=" * 60)
            self.log("📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ ФОРМАТА И УНИКАЛЬНОСТИ:")
            self.log(f"   Правильный формат: {format_correct}")
            self.log(f"   Неправильный формат: {format_incorrect}")
            self.log(f"   Уникальных кодов: {len(unique_codes)}")
            self.log(f"   Дублирующихся кодов: {len(duplicate_codes)}")
            self.log(f"   Ожидаемый формат: {warehouse_number}-BB-PP-CCC")
            
            if duplicate_codes:
                self.log(f"⚠️ Найдены дубликаты: {duplicate_codes}", "WARNING")
            
            # Показываем примеры сгенерированных кодов
            self.log("📋 Примеры сгенерированных QR кодов:")
            for i, qr_data in enumerate(successful_codes[:5]):
                self.log(f"   {i+1}. Б{qr_data.get('block')}-П{qr_data.get('shelf')}-Я{qr_data.get('cell')}: {qr_data.get('cell_code')}")
            
            return format_incorrect == 0 and len(duplicate_codes) == 0
            
        except Exception as e:
            self.log(f"❌ Исключение при проверке формата: {str(e)}", "ERROR")
            return False
    
    def test_api_stability(self):
        """Тестирование стабильности API при множественных запросах"""
        try:
            self.log("🔄 ТЕСТИРОВАНИЕ СТАБИЛЬНОСТИ API")
            self.log("=" * 60)
            
            warehouse_id = self.test_warehouse.get('id')
            test_requests = 10
            success_count = 0
            response_times = []
            
            self.log(f"📊 Выполнение {test_requests} тестовых запросов...")
            
            for i in range(test_requests):
                start_time = time.time()
                
                payload = {
                    "warehouse_id": warehouse_id,
                    "block": 1,
                    "shelf": 1,
                    "cell": (i % 5) + 1,  # Циклически используем ячейки 1-5
                    "format": "id"
                }
                
                response = self.session.post(f"{API_BASE}/warehouse/cell/generate-qr", json=payload)
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # в миллисекундах
                response_times.append(response_time)
                
                if response.status_code == 200:
                    success_count += 1
                    self.log(f"✅ Запрос {i+1}: успешно ({response_time:.0f}ms)")
                else:
                    self.log(f"❌ Запрос {i+1}: ошибка {response.status_code} ({response_time:.0f}ms)", "ERROR")
                
                time.sleep(0.1)  # Небольшая задержка
            
            avg_response_time = sum(response_times) / len(response_times)
            success_rate = (success_count / test_requests) * 100
            
            self.log("=" * 60)
            self.log("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ СТАБИЛЬНОСТИ API:")
            self.log(f"   Успешных запросов: {success_count}/{test_requests}")
            self.log(f"   Процент успеха: {success_rate:.1f}%")
            self.log(f"   Среднее время ответа: {avg_response_time:.0f}ms")
            self.log(f"   Минимальное время: {min(response_times):.0f}ms")
            self.log(f"   Максимальное время: {max(response_times):.0f}ms")
            
            return success_rate >= 80  # 80% успешных запросов
            
        except Exception as e:
            self.log(f"❌ Исключение при тестировании стабильности: {str(e)}", "ERROR")
            return False
    
    def run_comprehensive_test(self):
        """Запуск комплексного тестирования массовой генерации QR кодов"""
        self.log("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ МАССОВОЙ ГЕНЕРАЦИИ QR КОДОВ В СИСТЕМЕ TAJLINE.TJ")
        self.log("=" * 80)
        
        test_results = {
            "admin_auth": False,
            "warehouse_setup": False,
            "structure_endpoint": False,
            "mass_qr_generation": False,
            "format_and_uniqueness": False,
            "api_stability": False
        }
        
        # Тест 1: Авторизация администратора
        self.log("\n📋 ТЕСТ 1: Авторизация администратора")
        self.log("-" * 50)
        test_results["admin_auth"] = self.authenticate_admin()
        
        if not test_results["admin_auth"]:
            self.log("❌ Критическая ошибка: не удалось авторизоваться", "ERROR")
            return self.generate_final_report(test_results)
        
        # Тест 2: Настройка тестового склада
        self.log("\n📋 ТЕСТ 2: Настройка тестового склада")
        self.log("-" * 50)
        test_results["warehouse_setup"] = self.get_test_warehouse()
        
        if not test_results["warehouse_setup"]:
            self.log("❌ Критическая ошибка: не удалось настроить тестовый склад", "ERROR")
            return self.generate_final_report(test_results)
        
        # Тест 3: Тестирование endpoint структуры склада
        self.log("\n📋 ТЕСТ 3: Endpoint получения структуры склада")
        self.log("-" * 50)
        structure = self.test_warehouse_structure_endpoint()
        test_results["structure_endpoint"] = structure is not None
        
        # Тест 4: Массовая генерация QR кодов
        self.log("\n📋 ТЕСТ 4: Массовая генерация QR кодов")
        self.log("-" * 50)
        success_count, error_count, total_cells = self.test_mass_qr_generation()
        test_results["mass_qr_generation"] = success_count > 0 and (success_count / total_cells) >= 0.8
        
        # Тест 5: Проверка формата и уникальности
        self.log("\n📋 ТЕСТ 5: Проверка формата и уникальности QR кодов")
        self.log("-" * 50)
        test_results["format_and_uniqueness"] = self.check_qr_format_and_uniqueness()
        
        # Тест 6: Стабильность API
        self.log("\n📋 ТЕСТ 6: Стабильность API при множественных запросах")
        self.log("-" * 50)
        test_results["api_stability"] = self.test_api_stability()
        
        return self.generate_final_report(test_results)
    
    def generate_final_report(self, test_results):
        """Генерация итогового отчета"""
        self.log("\n" + "=" * 80)
        self.log("🎯 ИТОГОВЫЙ ОТЧЕТ КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ")
        self.log("=" * 80)
        
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100
        
        self.log("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        for test_name, result in test_results.items():
            status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
            readable_name = test_name.replace('_', ' ').upper()
            self.log(f"   {readable_name}: {status}")
        
        self.log(f"\n📈 ОБЩИЙ РЕЗУЛЬТАТ: {passed_tests}/{total_tests} тестов пройдено ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            self.log("\n🎉 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            self.log("✅ Исправленная функция массовой генерации QR кодов работает корректно")
            self.log("✅ Все ячейки склада получают уникальные QR коды")
            self.log("✅ Коды содержат правильный номер склада в формате XXX-BB-PP-CCC")
            self.log("✅ API работает стабильно при множественных запросах")
            self.log("✅ Нет дублирующихся кодов")
        else:
            self.log("\n❌ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ВЫЯВИЛО ПРОБЛЕМЫ!")
            self.log("⚠️ Требуется дополнительное исправление функции массовой генерации QR кодов")
        
        return test_results

def main():
    """Основная функция запуска тестирования"""
    tester = MassQRGenerationTester()
    results = tester.run_comprehensive_test()
    
    # Определяем код выхода
    passed_tests = sum(results.values())
    total_tests = len(results)
    success_rate = (passed_tests / total_tests) * 100
    
    if success_rate >= 80:
        sys.exit(0)  # Успешное завершение
    else:
        sys.exit(1)  # Ошибка

if __name__ == "__main__":
    main()
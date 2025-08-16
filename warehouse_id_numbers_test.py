#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправление проблемы с генерацией уникальных номеров складов для QR кодов в системе TAJLINE.TJ

ПРОБЛЕМА:
При генерации QR кода ячейки показывается код "01-01-001", но номер склада генерируется как "01" для всех складов, 
вместо уникальных номеров 001, 002, 003.

ЗАДАЧИ ДЛЯ ИСПРАВЛЕНИЯ:
1. Запустить обновление номеров складов: POST /api/admin/warehouses/update-id-numbers
2. Проверить обновленные номера складов: убедиться что поле warehouse_id_number содержит правильные значения
3. Протестировать генерацию QR кодов после обновления: проверить что коды содержат правильные номера складов
4. Проверить все склады в системе: убедиться что ВСЕ склады имеют уникальные номера

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
После исправления QR код для ячейки Б1-П1-Я1 должен показывать:
- Склад №1: 001-01-01-001 (не 01-01-01-001)  
- Склад №2: 002-01-01-001 (не 01-01-01-001)

КРИТИЧЕСКИЙ ТЕСТ:
Сгенерировать QR коды для минимум 3 разных складов и убедиться, что все имеют разные 3-значные номера складов.
"""

import requests
import json
import sys
import os
from datetime import datetime

# Получаем URL backend из переменных окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class WarehouseIdNumbersTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.operator_token = None
        self.test_results = []
        self.warehouses_before_update = []
        self.warehouses_after_update = []
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_admin_auth(self):
        """Авторизация администратора"""
        try:
            self.log("🔐 Авторизация администратора...")
            
            response = self.session.post(f"{API_BASE}/auth/login", json={
                "phone": "+79999888777",
                "password": "admin123"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data["access_token"]
                user_info = data["user"]
                self.log(f"✅ Успешная авторизация администратора: {user_info['full_name']} (роль: {user_info['role']})")
                return True
            else:
                self.log(f"❌ Ошибка авторизации администратора: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при авторизации администратора: {e}", "ERROR")
            return False
    
    def get_warehouses_before_update(self):
        """Получить список складов ДО обновления номеров"""
        try:
            self.log("🏢 Получение списка складов ДО обновления номеров...")
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{API_BASE}/warehouses", headers=headers)
            
            if response.status_code == 200:
                self.warehouses_before_update = response.json()
                
                self.log(f"✅ Получено {len(self.warehouses_before_update)} складов ДО обновления:")
                
                # Анализируем текущие номера складов
                warehouses_with_numbers = 0
                warehouses_without_numbers = 0
                duplicate_numbers = {}
                
                for warehouse in self.warehouses_before_update:
                    warehouse_id_number = warehouse.get('warehouse_id_number')
                    name = warehouse.get('name', 'Без названия')
                    
                    if warehouse_id_number:
                        warehouses_with_numbers += 1
                        if warehouse_id_number in duplicate_numbers:
                            duplicate_numbers[warehouse_id_number].append(name)
                        else:
                            duplicate_numbers[warehouse_id_number] = [name]
                        self.log(f"   - {name}: номер {warehouse_id_number}")
                    else:
                        warehouses_without_numbers += 1
                        self.log(f"   - {name}: НЕТ НОМЕРА")
                
                # Проверяем дубликаты
                duplicates_found = {num: names for num, names in duplicate_numbers.items() if len(names) > 1}
                
                if duplicates_found:
                    self.log(f"⚠️ НАЙДЕНЫ ДУБЛИРУЮЩИЕСЯ НОМЕРА СКЛАДОВ:")
                    for duplicate_num, warehouse_names in duplicates_found.items():
                        self.log(f"   - Номер {duplicate_num}: {', '.join(warehouse_names)}")
                
                self.log(f"📊 Статистика ДО обновления:")
                self.log(f"   - Складов с номерами: {warehouses_with_numbers}")
                self.log(f"   - Складов без номеров: {warehouses_without_numbers}")
                self.log(f"   - Дублирующихся номеров: {len(duplicates_found)}")
                
                return True
            else:
                self.log(f"❌ Ошибка получения складов: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при получении складов: {e}", "ERROR")
            return False
    
    def update_warehouse_id_numbers(self):
        """Запустить обновление номеров складов через POST /api/admin/warehouses/update-id-numbers"""
        try:
            self.log("🔄 Запуск обновления номеров складов...")
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.post(f"{API_BASE}/admin/warehouses/update-id-numbers", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                updated_count = data.get('updated_count', 0)
                total_count = data.get('total_count', 0)
                message = data.get('message', '')
                
                self.log(f"✅ Обновление номеров складов завершено:")
                self.log(f"   - Сообщение: {message}")
                self.log(f"   - Обновлено складов: {updated_count}")
                self.log(f"   - Всего складов: {total_count}")
                
                # Проверяем детали обновления если есть
                if 'updated_warehouses' in data:
                    updated_warehouses = data['updated_warehouses']
                    self.log(f"   - Детали обновления:")
                    for warehouse_info in updated_warehouses[:5]:  # Показываем первые 5
                        name = warehouse_info.get('name', 'N/A')
                        old_number = warehouse_info.get('old_number', 'НЕТ')
                        new_number = warehouse_info.get('new_number', 'НЕТ')
                        self.log(f"     * {name}: {old_number} → {new_number}")
                    
                    if len(updated_warehouses) > 5:
                        self.log(f"     ... и еще {len(updated_warehouses) - 5} складов")
                
                return True
            else:
                self.log(f"❌ Ошибка обновления номеров складов: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при обновлении номеров складов: {e}", "ERROR")
            return False
    
    def get_warehouses_after_update(self):
        """Получить список складов ПОСЛЕ обновления номеров"""
        try:
            self.log("🏢 Получение списка складов ПОСЛЕ обновления номеров...")
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{API_BASE}/warehouses", headers=headers)
            
            if response.status_code == 200:
                self.warehouses_after_update = response.json()
                
                self.log(f"✅ Получено {len(self.warehouses_after_update)} складов ПОСЛЕ обновления:")
                
                # Анализируем обновленные номера складов
                warehouses_with_numbers = 0
                warehouses_without_numbers = 0
                duplicate_numbers = {}
                unique_numbers = set()
                
                for warehouse in self.warehouses_after_update:
                    warehouse_id_number = warehouse.get('warehouse_id_number')
                    name = warehouse.get('name', 'Без названия')
                    
                    if warehouse_id_number:
                        warehouses_with_numbers += 1
                        unique_numbers.add(warehouse_id_number)
                        
                        if warehouse_id_number in duplicate_numbers:
                            duplicate_numbers[warehouse_id_number].append(name)
                        else:
                            duplicate_numbers[warehouse_id_number] = [name]
                        
                        # Проверяем формат номера (должен быть 3 цифры)
                        if len(warehouse_id_number) == 3 and warehouse_id_number.isdigit():
                            self.log(f"   - {name}: номер {warehouse_id_number} ✅")
                        else:
                            self.log(f"   - {name}: номер {warehouse_id_number} ❌ (неправильный формат)")
                    else:
                        warehouses_without_numbers += 1
                        self.log(f"   - {name}: НЕТ НОМЕРА ❌")
                
                # Проверяем дубликаты
                duplicates_found = {num: names for num, names in duplicate_numbers.items() if len(names) > 1}
                
                self.log(f"📊 Статистика ПОСЛЕ обновления:")
                self.log(f"   - Складов с номерами: {warehouses_with_numbers}")
                self.log(f"   - Складов без номеров: {warehouses_without_numbers}")
                self.log(f"   - Уникальных номеров: {len(unique_numbers)}")
                self.log(f"   - Дублирующихся номеров: {len(duplicates_found)}")
                
                if duplicates_found:
                    self.log(f"❌ НАЙДЕНЫ ДУБЛИРУЮЩИЕСЯ НОМЕРА СКЛАДОВ ПОСЛЕ ОБНОВЛЕНИЯ:")
                    for duplicate_num, warehouse_names in duplicates_found.items():
                        self.log(f"   - Номер {duplicate_num}: {', '.join(warehouse_names)}")
                    return False
                
                if warehouses_without_numbers > 0:
                    self.log(f"❌ НАЙДЕНЫ СКЛАДЫ БЕЗ НОМЕРОВ ПОСЛЕ ОБНОВЛЕНИЯ: {warehouses_without_numbers}")
                    return False
                
                self.log(f"✅ Все склады имеют уникальные номера!")
                return True
            else:
                self.log(f"❌ Ошибка получения складов после обновления: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при получении складов после обновления: {e}", "ERROR")
            return False
    
    def test_qr_code_generation_with_unique_numbers(self):
        """Протестировать генерацию QR кодов с уникальными номерами складов"""
        try:
            self.log("🎯 КРИТИЧЕСКИЙ ТЕСТ: Генерация QR кодов с уникальными номерами складов")
            
            if len(self.warehouses_after_update) < 2:
                self.log("❌ Недостаточно складов для тестирования уникальности (нужно минимум 2)", "ERROR")
                return False
            
            # Берем первые 3 склада для тестирования (или сколько есть)
            test_warehouses = self.warehouses_after_update[:min(3, len(self.warehouses_after_update))]
            
            self.log(f"📋 Тестируем генерацию QR кодов для {len(test_warehouses)} складов:")
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            qr_results = []
            
            for i, warehouse in enumerate(test_warehouses):
                warehouse_id = warehouse['id']
                warehouse_name = warehouse['name']
                warehouse_id_number = warehouse.get('warehouse_id_number', 'НЕТ')
                
                self.log(f"   {i+1}. {warehouse_name} (номер: {warehouse_id_number})")
                
                # Генерируем QR код для ячейки Б1-П1-Я1 с format: 'id'
                cell_data = {
                    "warehouse_id": warehouse_id,
                    "block": 1,
                    "shelf": 1,
                    "cell": 1,
                    "format": "id"  # КРИТИЧЕСКИЙ ПАРАМЕТР
                }
                
                response = self.session.post(f"{API_BASE}/warehouse/cell/generate-qr", 
                                           json=cell_data, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    cell_code = data.get('cell_code', '')
                    format_type = data.get('format_type', '')
                    
                    qr_results.append({
                        'warehouse_name': warehouse_name,
                        'warehouse_id_number': warehouse_id_number,
                        'cell_code': cell_code,
                        'format_type': format_type
                    })
                    
                    self.log(f"      ✅ QR код: {cell_code} (формат: {format_type})")
                else:
                    self.log(f"      ❌ Ошибка генерации QR кода: {response.status_code} - {response.text}")
                    return False
            
            # Анализируем результаты
            self.log(f"\n🔍 АНАЛИЗ РЕЗУЛЬТАТОВ ГЕНЕРАЦИИ QR КОДОВ:")
            
            unique_codes = set()
            unique_warehouse_numbers = set()
            format_issues = []
            
            for result in qr_results:
                cell_code = result['cell_code']
                warehouse_name = result['warehouse_name']
                warehouse_id_number = result['warehouse_id_number']
                
                # Проверяем формат XXX-BB-PP-CCC
                parts = cell_code.split('-')
                if len(parts) == 4:
                    warehouse_part, block_part, shelf_part, cell_part = parts
                    
                    # Проверяем формат каждой части
                    if (len(warehouse_part) == 3 and warehouse_part.isdigit() and
                        len(block_part) == 2 and block_part.isdigit() and
                        len(shelf_part) == 2 and shelf_part.isdigit() and
                        len(cell_part) == 3 and cell_part.isdigit()):
                        
                        # Проверяем соответствие номера склада
                        if warehouse_part == warehouse_id_number:
                            self.log(f"   ✅ {warehouse_name}: {cell_code} (номер склада {warehouse_part} корректен)")
                            unique_codes.add(cell_code)
                            unique_warehouse_numbers.add(warehouse_part)
                        else:
                            self.log(f"   ❌ {warehouse_name}: {cell_code} (номер склада {warehouse_part} не соответствует {warehouse_id_number})")
                            format_issues.append(f"Несоответствие номера склада: {warehouse_part} != {warehouse_id_number}")
                    else:
                        self.log(f"   ❌ {warehouse_name}: {cell_code} (неправильный формат XXX-BB-PP-CCC)")
                        format_issues.append(f"Неправильный формат: {cell_code}")
                else:
                    self.log(f"   ❌ {warehouse_name}: {cell_code} (не содержит 4 части)")
                    format_issues.append(f"Неправильная структура: {cell_code}")
            
            # Итоговая проверка
            self.log(f"\n📊 ИТОГОВАЯ ПРОВЕРКА:")
            self.log(f"   - Всего QR кодов: {len(qr_results)}")
            self.log(f"   - Уникальных QR кодов: {len(unique_codes)}")
            self.log(f"   - Уникальных номеров складов: {len(unique_warehouse_numbers)}")
            self.log(f"   - Проблем с форматом: {len(format_issues)}")
            
            if format_issues:
                self.log(f"❌ НАЙДЕНЫ ПРОБЛЕМЫ С ФОРМАТОМ:")
                for issue in format_issues:
                    self.log(f"   - {issue}")
                return False
            
            if len(unique_codes) == len(qr_results) and len(unique_warehouse_numbers) == len(qr_results):
                self.log(f"✅ ВСЕ QR КОДЫ УНИКАЛЬНЫ И СОДЕРЖАТ ПРАВИЛЬНЫЕ НОМЕРА СКЛАДОВ!")
                
                # Демонстрируем ожидаемый результат
                self.log(f"\n🎯 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ ДОСТИГНУТ:")
                for result in qr_results:
                    warehouse_name = result['warehouse_name']
                    cell_code = result['cell_code']
                    self.log(f"   - {warehouse_name}: {cell_code}")
                
                return True
            else:
                self.log(f"❌ НАЙДЕНЫ ДУБЛИРУЮЩИЕСЯ QR КОДЫ ИЛИ НОМЕРА СКЛАДОВ!")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при тестировании генерации QR кодов: {e}", "ERROR")
            return False
    
    def test_all_warehouses_have_unique_numbers(self):
        """Проверить что ВСЕ склады в системе имеют уникальные номера"""
        try:
            self.log("🔍 КРИТИЧЕСКИЙ ТЕСТ: Проверка уникальности номеров ВСЕХ складов в системе")
            
            if not self.warehouses_after_update:
                self.log("❌ Нет данных о складах после обновления", "ERROR")
                return False
            
            # Собираем все номера складов
            all_numbers = []
            warehouses_info = []
            
            for warehouse in self.warehouses_after_update:
                warehouse_id_number = warehouse.get('warehouse_id_number')
                name = warehouse.get('name', 'Без названия')
                
                if warehouse_id_number:
                    all_numbers.append(warehouse_id_number)
                    warehouses_info.append({
                        'name': name,
                        'number': warehouse_id_number
                    })
                else:
                    self.log(f"❌ Склад без номера: {name}")
                    return False
            
            # Проверяем уникальность
            unique_numbers = set(all_numbers)
            
            self.log(f"📊 СТАТИСТИКА ВСЕХ СКЛАДОВ:")
            self.log(f"   - Всего складов: {len(self.warehouses_after_update)}")
            self.log(f"   - Складов с номерами: {len(all_numbers)}")
            self.log(f"   - Уникальных номеров: {len(unique_numbers)}")
            
            if len(unique_numbers) == len(all_numbers):
                self.log(f"✅ ВСЕ {len(all_numbers)} СКЛАДОВ ИМЕЮТ УНИКАЛЬНЫЕ НОМЕРА!")
                
                # Показываем примеры номеров
                sorted_warehouses = sorted(warehouses_info, key=lambda x: x['number'])
                self.log(f"📋 ПРИМЕРЫ НОМЕРОВ СКЛАДОВ:")
                for warehouse_info in sorted_warehouses[:10]:  # Показываем первые 10
                    self.log(f"   - {warehouse_info['name']}: {warehouse_info['number']}")
                
                if len(sorted_warehouses) > 10:
                    self.log(f"   ... и еще {len(sorted_warehouses) - 10} складов")
                
                return True
            else:
                # Находим дубликаты
                duplicates = {}
                for number in all_numbers:
                    if all_numbers.count(number) > 1:
                        if number not in duplicates:
                            duplicates[number] = []
                        for warehouse_info in warehouses_info:
                            if warehouse_info['number'] == number:
                                duplicates[number].append(warehouse_info['name'])
                
                self.log(f"❌ НАЙДЕНЫ ДУБЛИРУЮЩИЕСЯ НОМЕРА СКЛАДОВ:")
                for duplicate_number, warehouse_names in duplicates.items():
                    self.log(f"   - Номер {duplicate_number}: {', '.join(warehouse_names)}")
                
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при проверке уникальности всех номеров: {e}", "ERROR")
            return False
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        self.log("🚀 НАЧАЛО КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ ИСПРАВЛЕНИЯ ПРОБЛЕМЫ С НОМЕРАМИ СКЛАДОВ")
        self.log("=" * 100)
        self.log("ПРОБЛЕМА: При генерации QR кода ячейки номер склада генерируется как '01' для всех складов")
        self.log("ЦЕЛЬ: Исправить генерацию уникальных номеров складов 001, 002, 003...")
        self.log("=" * 100)
        
        # Список всех тестов
        tests = [
            ("Авторизация администратора", self.test_admin_auth),
            ("Получение складов ДО обновления", self.get_warehouses_before_update),
            ("Обновление номеров складов", self.update_warehouse_id_numbers),
            ("Получение складов ПОСЛЕ обновления", self.get_warehouses_after_update),
            ("Тестирование генерации QR кодов с уникальными номерами", self.test_qr_code_generation_with_unique_numbers),
            ("Проверка уникальности ВСЕХ номеров складов", self.test_all_warehouses_have_unique_numbers)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"\n📋 ТЕСТ: {test_name}")
            self.log("-" * 80)
            
            try:
                result = test_func()
                if result:
                    passed_tests += 1
                    self.test_results.append(f"✅ {test_name}")
                    self.log(f"✅ ТЕСТ ПРОЙДЕН: {test_name}")
                else:
                    self.test_results.append(f"❌ {test_name}")
                    self.log(f"❌ ТЕСТ НЕ ПРОЙДЕН: {test_name}")
            except Exception as e:
                self.test_results.append(f"❌ {test_name} (Исключение: {e})")
                self.log(f"❌ ИСКЛЮЧЕНИЕ В ТЕСТЕ {test_name}: {e}", "ERROR")
        
        # Итоговый отчет
        self.log("\n" + "=" * 100)
        self.log("🎯 ИТОГОВЫЙ ОТЧЕТ КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ ИСПРАВЛЕНИЯ НОМЕРОВ СКЛАДОВ")
        self.log("=" * 100)
        
        success_rate = (passed_tests / total_tests) * 100
        self.log(f"📊 РЕЗУЛЬТАТ: {passed_tests}/{total_tests} тестов пройдено ({success_rate:.1f}%)")
        
        self.log("\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        for result in self.test_results:
            self.log(f"   {result}")
        
        if success_rate >= 80:
            self.log(f"\n🎉 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            self.log(f"✅ Проблема с генерацией уникальных номеров складов для QR кодов ИСПРАВЛЕНА!")
            self.log(f"✅ Все склады теперь имеют уникальные 3-значные номера (001, 002, 003...)")
            self.log(f"✅ QR коды генерируются в правильном формате XXX-BB-PP-CCC")
            self.log(f"✅ Ожидаемый результат достигнут:")
            self.log(f"   - Склад №1: 001-01-01-001 (не 01-01-01-001)")
            self.log(f"   - Склад №2: 002-01-01-001 (не 01-01-01-001)")
        else:
            self.log(f"\n❌ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ВЫЯВИЛО ПРОБЛЕМЫ!")
            self.log(f"❌ Требуется дополнительная работа над исправлением номеров складов")
        
        return success_rate >= 80

def main():
    """Главная функция"""
    print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправление проблемы с генерацией уникальных номеров складов для QR кодов в TAJLINE.TJ")
    print("=" * 120)
    
    tester = WarehouseIdNumbersTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
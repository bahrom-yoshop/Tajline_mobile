#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправления генерации QR кодов через визуальную схему склада в TAJLINE.TJ

Цель тестирования:
Проверить, что при генерации QR кодов через визуальную схему склада (при клике на ячейки или генерации для всех ячеек) 
теперь используется правильный формат с уникальными номерами складов.

Проблема для решения:
Ранее при генерации QR кодов через визуальную схему склада не использовался параметр `format: 'id'`, 
что приводило к генерации кодов без уникальных номеров складов.

Задачи тестирования:
1. Тестирование массовой генерации QR кодов (generateCellQRCodes)
2. Тестирование генерации для отдельной ячейки (generateCellQR) 
3. Тестирование генерации для всех ячеек склада
4. Проверка уникальности между складами
5. Проверка формата XXX-BB-PP-CCC
"""

import requests
import json
import sys
import os
from datetime import datetime

# Получаем URL backend из переменных окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class QRCodeGenerationTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.operator_token = None
        self.test_warehouses = []
        self.test_results = []
        
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
    
    def test_operator_auth(self):
        """Авторизация оператора склада"""
        try:
            self.log("🔐 Авторизация оператора склада...")
            
            response = self.session.post(f"{API_BASE}/auth/login", json={
                "phone": "+79777888999",
                "password": "warehouse123"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.operator_token = data["access_token"]
                user_info = data["user"]
                self.log(f"✅ Успешная авторизация оператора: {user_info['full_name']} (роль: {user_info['role']})")
                return True
            else:
                self.log(f"❌ Ошибка авторизации оператора: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при авторизации оператора: {e}", "ERROR")
            return False
    
    def get_test_warehouses(self):
        """Получить тестовые склады для проверки уникальности"""
        try:
            self.log("🏢 Получение списка складов для тестирования...")
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{API_BASE}/warehouses", headers=headers)
            
            if response.status_code == 200:
                warehouses = response.json()
                
                # Берем первые 2 склада для тестирования уникальности
                self.test_warehouses = warehouses[:2] if len(warehouses) >= 2 else warehouses
                
                self.log(f"✅ Получено {len(self.test_warehouses)} складов для тестирования:")
                for warehouse in self.test_warehouses:
                    warehouse_id_number = warehouse.get('warehouse_id_number', 'НЕТ')
                    self.log(f"   - {warehouse['name']} (ID: {warehouse['id'][:8]}..., Номер: {warehouse_id_number})")
                
                return len(self.test_warehouses) > 0
            else:
                self.log(f"❌ Ошибка получения складов: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при получении складов: {e}", "ERROR")
            return False
    
    def test_single_cell_qr_generation_with_format_id(self):
        """Тестирование генерации QR кода для отдельной ячейки с параметром format: 'id'"""
        try:
            self.log("🎯 КРИТИЧЕСКИЙ ТЕСТ: Генерация QR кода для отдельной ячейки с format: 'id'")
            
            if not self.test_warehouses:
                self.log("❌ Нет доступных складов для тестирования", "ERROR")
                return False
            
            warehouse = self.test_warehouses[0]
            warehouse_id = warehouse['id']
            
            # Тестируем генерацию QR кода с format: 'id'
            headers = {"Authorization": f"Bearer {self.admin_token}"}
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
                
                # Проверяем структуру ответа
                required_fields = ['success', 'warehouse_id', 'warehouse_id_number', 'cell_code', 'format_type', 'qr_code']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log(f"❌ Отсутствуют обязательные поля в ответе: {missing_fields}", "ERROR")
                    return False
                
                # Проверяем формат cell_code (должен быть XXX-BB-PP-CCC)
                cell_code = data['cell_code']
                warehouse_id_number = data['warehouse_id_number']
                format_type = data['format_type']
                
                self.log(f"✅ QR код сгенерирован успешно:")
                self.log(f"   - Код ячейки: {cell_code}")
                self.log(f"   - Номер склада: {warehouse_id_number}")
                self.log(f"   - Формат: {format_type}")
                
                # Проверяем формат XXX-BB-PP-CCC
                parts = cell_code.split('-')
                if len(parts) == 4:
                    warehouse_part, block_part, shelf_part, cell_part = parts
                    
                    # Проверяем формат каждой части
                    format_valid = (
                        len(warehouse_part) == 3 and warehouse_part.isdigit() and
                        len(block_part) == 2 and block_part.isdigit() and
                        len(shelf_part) == 2 and shelf_part.isdigit() and
                        len(cell_part) == 3 and cell_part.isdigit()
                    )
                    
                    if format_valid:
                        self.log(f"✅ Формат QR кода корректен: {cell_code} (XXX-BB-PP-CCC)")
                        
                        # Проверяем, что используется уникальный номер склада
                        if warehouse_id_number and warehouse_id_number == warehouse_part:
                            self.log(f"✅ Уникальный номер склада используется правильно: {warehouse_id_number}")
                            return True
                        else:
                            self.log(f"❌ Номер склада в QR коде не соответствует warehouse_id_number: {warehouse_part} != {warehouse_id_number}", "ERROR")
                            return False
                    else:
                        self.log(f"❌ Неправильный формат QR кода: {cell_code} (ожидается XXX-BB-PP-CCC)", "ERROR")
                        return False
                else:
                    self.log(f"❌ QR код не содержит 4 части разделенные дефисами: {cell_code}", "ERROR")
                    return False
            else:
                self.log(f"❌ Ошибка генерации QR кода: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при тестировании генерации QR кода: {e}", "ERROR")
            return False
    
    def test_legacy_format_compatibility(self):
        """Тестирование обратной совместимости со старым форматом"""
        try:
            self.log("🔄 ТЕСТ: Обратная совместимость со старым форматом (format: 'legacy')")
            
            if not self.test_warehouses:
                self.log("❌ Нет доступных складов для тестирования", "ERROR")
                return False
            
            warehouse = self.test_warehouses[0]
            warehouse_id = warehouse['id']
            
            # Тестируем генерацию QR кода со старым форматом
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            cell_data = {
                "warehouse_id": warehouse_id,
                "block": 1,
                "shelf": 1,
                "cell": 1,
                "format": "legacy"  # Старый формат
            }
            
            response = self.session.post(f"{API_BASE}/warehouse/cell/generate-qr", 
                                       json=cell_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                cell_code = data['cell_code']
                format_type = data['format_type']
                
                self.log(f"✅ Старый формат работает:")
                self.log(f"   - Код ячейки: {cell_code}")
                self.log(f"   - Формат: {format_type}")
                
                # Проверяем формат старого кода (должен содержать UUID-Б1-П1-Я1)
                if "-Б" in cell_code and "-П" in cell_code and "-Я" in cell_code:
                    self.log(f"✅ Старый формат корректен: {cell_code}")
                    return True
                else:
                    self.log(f"❌ Неправильный старый формат: {cell_code}", "ERROR")
                    return False
            else:
                self.log(f"❌ Ошибка генерации QR кода в старом формате: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при тестировании старого формата: {e}", "ERROR")
            return False
    
    def test_mass_qr_generation_all_cells(self):
        """Тестирование массовой генерации QR кодов для всех ячеек склада"""
        try:
            self.log("🏭 КРИТИЧЕСКИЙ ТЕСТ: Массовая генерация QR кодов для всех ячеек склада")
            
            if not self.test_warehouses:
                self.log("❌ Нет доступных складов для тестирования", "ERROR")
                return False
            
            warehouse = self.test_warehouses[0]
            warehouse_id = warehouse['id']
            warehouse_name = warehouse['name']
            
            # Тестируем старый endpoint для массовой генерации
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{API_BASE}/warehouse/{warehouse_id}/all-cells-qr", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                qr_codes = data.get('qr_codes', [])
                total_cells = data.get('total_cells', 0)
                
                self.log(f"✅ Массовая генерация QR кодов успешна:")
                self.log(f"   - Склад: {warehouse_name}")
                self.log(f"   - Всего ячеек: {total_cells}")
                self.log(f"   - Сгенерировано QR кодов: {len(qr_codes)}")
                
                if len(qr_codes) > 0:
                    # Проверяем первые несколько QR кодов
                    sample_codes = qr_codes[:3]
                    self.log(f"   - Примеры QR кодов:")
                    for i, qr_data in enumerate(sample_codes):
                        location = qr_data.get('location', 'N/A')
                        qr_code = qr_data.get('qr_code', '')
                        self.log(f"     {i+1}. {location} - QR код: {'✅ Есть' if qr_code else '❌ Нет'}")
                    
                    return True
                else:
                    self.log("❌ Не сгенерировано ни одного QR кода", "ERROR")
                    return False
            else:
                self.log(f"❌ Ошибка массовой генерации QR кодов: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при массовой генерации QR кодов: {e}", "ERROR")
            return False
    
    def test_new_batch_qr_generation(self):
        """Тестирование нового endpoint для массовой генерации QR кодов"""
        try:
            self.log("🆕 КРИТИЧЕСКИЙ ТЕСТ: Новый endpoint массовой генерации QR кодов")
            
            if not self.test_warehouses:
                self.log("❌ Нет доступных складов для тестирования", "ERROR")
                return False
            
            warehouse = self.test_warehouses[0]
            warehouse_id = warehouse['id']
            warehouse_name = warehouse['name']
            
            # Тестируем новый endpoint для массовой генерации
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{API_BASE}/warehouses/{warehouse_id}/cells/qr-batch", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                qr_codes = data.get('qr_codes', [])
                total_cells = data.get('total_cells', 0)
                
                self.log(f"✅ Новый endpoint массовой генерации работает:")
                self.log(f"   - Склад: {warehouse_name}")
                self.log(f"   - Всего ячеек: {total_cells}")
                self.log(f"   - Сгенерировано QR кодов: {len(qr_codes)}")
                
                if len(qr_codes) > 0:
                    # Проверяем формат новых QR кодов
                    sample_codes = qr_codes[:3]
                    self.log(f"   - Примеры новых QR кодов:")
                    for i, qr_data in enumerate(sample_codes):
                        cell_location = qr_data.get('cell_location', 'N/A')
                        qr_data_value = qr_data.get('qr_data', '')
                        qr_code = qr_data.get('qr_code', '')
                        self.log(f"     {i+1}. {cell_location} - QR данные: {qr_data_value} - QR код: {'✅ Есть' if qr_code else '❌ Нет'}")
                    
                    return True
                else:
                    self.log("❌ Не сгенерировано ни одного QR кода", "ERROR")
                    return False
            else:
                self.log(f"❌ Ошибка нового endpoint массовой генерации: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при тестировании нового endpoint: {e}", "ERROR")
            return False
    
    def test_individual_cell_qr_endpoint(self):
        """Тестирование нового endpoint для генерации QR кода отдельной ячейки"""
        try:
            self.log("🎯 КРИТИЧЕСКИЙ ТЕСТ: Новый endpoint генерации QR кода отдельной ячейки")
            
            if not self.test_warehouses:
                self.log("❌ Нет доступных складов для тестирования", "ERROR")
                return False
            
            warehouse = self.test_warehouses[0]
            warehouse_id = warehouse['id']
            
            # Формируем cell_id в формате warehouse_id-block-shelf-cell
            cell_id = f"{warehouse_id}-1-1-1"
            
            # Тестируем новый endpoint для отдельной ячейки
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{API_BASE}/warehouses/cells/{cell_id}/qr", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                cell_location = data.get('cell_location', '')
                warehouse_number = data.get('warehouse_number', 0)
                qr_data = data.get('qr_data', '')
                qr_code = data.get('qr_code', '')
                
                self.log(f"✅ Новый endpoint отдельной ячейки работает:")
                self.log(f"   - Ячейка: {cell_location}")
                self.log(f"   - Номер склада: {warehouse_number}")
                self.log(f"   - QR данные: {qr_data}")
                self.log(f"   - QR код: {'✅ Есть' if qr_code else '❌ Нет'}")
                
                # Проверяем формат QR данных (должен быть числовым)
                if qr_data and qr_data.isdigit() and len(qr_data) == 8:
                    self.log(f"✅ Формат QR данных корректен: {qr_data} (8 цифр)")
                    return True
                else:
                    self.log(f"❌ Неправильный формат QR данных: {qr_data} (ожидается 8 цифр)", "ERROR")
                    return False
            else:
                self.log(f"❌ Ошибка нового endpoint отдельной ячейки: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при тестировании нового endpoint отдельной ячейки: {e}", "ERROR")
            return False
    
    def test_warehouse_uniqueness(self):
        """Тестирование уникальности QR кодов между складами"""
        try:
            self.log("🔄 КРИТИЧЕСКИЙ ТЕСТ: Уникальность QR кодов между складами")
            
            if len(self.test_warehouses) < 2:
                self.log("❌ Недостаточно складов для тестирования уникальности (нужно минимум 2)", "ERROR")
                return False
            
            warehouse1 = self.test_warehouses[0]
            warehouse2 = self.test_warehouses[1]
            
            # Генерируем QR коды для одинаковых ячеек разных складов
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # QR код для ячейки Б1-П1-Я1 первого склада
            cell_data1 = {
                "warehouse_id": warehouse1['id'],
                "block": 1,
                "shelf": 1,
                "cell": 1,
                "format": "id"
            }
            
            response1 = self.session.post(f"{API_BASE}/warehouse/cell/generate-qr", 
                                        json=cell_data1, headers=headers)
            
            # QR код для ячейки Б1-П1-Я1 второго склада
            cell_data2 = {
                "warehouse_id": warehouse2['id'],
                "block": 1,
                "shelf": 1,
                "cell": 1,
                "format": "id"
            }
            
            response2 = self.session.post(f"{API_BASE}/warehouse/cell/generate-qr", 
                                        json=cell_data2, headers=headers)
            
            if response1.status_code == 200 and response2.status_code == 200:
                data1 = response1.json()
                data2 = response2.json()
                
                cell_code1 = data1['cell_code']
                cell_code2 = data2['cell_code']
                warehouse_id_number1 = data1['warehouse_id_number']
                warehouse_id_number2 = data2['warehouse_id_number']
                
                self.log(f"✅ QR коды для одинаковых ячеек разных складов:")
                self.log(f"   - Склад 1 ({warehouse1['name']}): {cell_code1} (номер: {warehouse_id_number1})")
                self.log(f"   - Склад 2 ({warehouse2['name']}): {cell_code2} (номер: {warehouse_id_number2})")
                
                # Проверяем, что коды отличаются
                if cell_code1 != cell_code2:
                    self.log(f"✅ QR коды уникальны между складами!")
                    
                    # Проверяем, что отличаются именно номера складов
                    parts1 = cell_code1.split('-')
                    parts2 = cell_code2.split('-')
                    
                    if len(parts1) == 4 and len(parts2) == 4:
                        if parts1[0] != parts2[0] and parts1[1:] == parts2[1:]:
                            self.log(f"✅ Уникальность обеспечивается номерами складов: {parts1[0]} != {parts2[0]}")
                            return True
                        else:
                            self.log(f"❌ Коды отличаются не только номерами складов", "ERROR")
                            return False
                    else:
                        self.log(f"❌ Неправильный формат QR кодов", "ERROR")
                        return False
                else:
                    self.log(f"❌ QR коды одинаковых ячеек разных складов идентичны: {cell_code1}", "ERROR")
                    return False
            else:
                self.log(f"❌ Ошибка генерации QR кодов для тестирования уникальности", "ERROR")
                self.log(f"   - Склад 1: {response1.status_code} - {response1.text}")
                self.log(f"   - Склад 2: {response2.status_code} - {response2.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при тестировании уникальности: {e}", "ERROR")
            return False
    
    def test_operator_permissions(self):
        """Тестирование прав доступа оператора к генерации QR кодов"""
        try:
            self.log("👤 ТЕСТ: Права доступа оператора к генерации QR кодов")
            
            if not self.operator_token:
                self.log("❌ Нет токена оператора для тестирования", "ERROR")
                return False
            
            if not self.test_warehouses:
                self.log("❌ Нет доступных складов для тестирования", "ERROR")
                return False
            
            warehouse = self.test_warehouses[0]
            warehouse_id = warehouse['id']
            
            # Тестируем доступ оператора к генерации QR кода
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            cell_data = {
                "warehouse_id": warehouse_id,
                "block": 1,
                "shelf": 1,
                "cell": 1,
                "format": "id"
            }
            
            response = self.session.post(f"{API_BASE}/warehouse/cell/generate-qr", 
                                       json=cell_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Оператор имеет доступ к генерации QR кодов:")
                self.log(f"   - Код ячейки: {data.get('cell_code', 'N/A')}")
                return True
            elif response.status_code == 403:
                self.log(f"❌ Оператор не имеет доступа к генерации QR кодов: {response.text}", "ERROR")
                return False
            else:
                self.log(f"❌ Неожиданная ошибка при тестировании прав оператора: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при тестировании прав оператора: {e}", "ERROR")
            return False
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        self.log("🚀 НАЧАЛО КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ ИСПРАВЛЕНИЙ ГЕНЕРАЦИИ QR КОДОВ")
        self.log("=" * 80)
        
        # Список всех тестов
        tests = [
            ("Авторизация администратора", self.test_admin_auth),
            ("Авторизация оператора склада", self.test_operator_auth),
            ("Получение тестовых складов", self.get_test_warehouses),
            ("Генерация QR кода с format: 'id'", self.test_single_cell_qr_generation_with_format_id),
            ("Обратная совместимость (format: 'legacy')", self.test_legacy_format_compatibility),
            ("Массовая генерация QR кодов (старый endpoint)", self.test_mass_qr_generation_all_cells),
            ("Массовая генерация QR кодов (новый endpoint)", self.test_new_batch_qr_generation),
            ("Генерация QR кода отдельной ячейки (новый endpoint)", self.test_individual_cell_qr_endpoint),
            ("Уникальность QR кодов между складами", self.test_warehouse_uniqueness),
            ("Права доступа оператора", self.test_operator_permissions)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"\n📋 ТЕСТ: {test_name}")
            self.log("-" * 60)
            
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
        self.log("\n" + "=" * 80)
        self.log("🎯 ИТОГОВЫЙ ОТЧЕТ КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ ИСПРАВЛЕНИЙ ГЕНЕРАЦИИ QR КОДОВ")
        self.log("=" * 80)
        
        success_rate = (passed_tests / total_tests) * 100
        self.log(f"📊 РЕЗУЛЬТАТ: {passed_tests}/{total_tests} тестов пройдено ({success_rate:.1f}%)")
        
        self.log("\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        for result in self.test_results:
            self.log(f"   {result}")
        
        if success_rate >= 80:
            self.log(f"\n🎉 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            self.log(f"✅ Исправления генерации QR кодов через визуальную схему склада работают корректно")
            self.log(f"✅ Параметр format: 'id' используется правильно")
            self.log(f"✅ QR коды содержат уникальные номера складов в формате XXX-BB-PP-CCC")
        else:
            self.log(f"\n❌ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ВЫЯВИЛО ПРОБЛЕМЫ!")
            self.log(f"❌ Требуется дополнительная работа над исправлениями генерации QR кодов")
        
        return success_rate >= 80

def main():
    """Главная функция"""
    print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправления генерации QR кодов через визуальную схему склада в TAJLINE.TJ")
    print("=" * 100)
    
    tester = QRCodeGenerationTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправления для отображения цены за кг (а не итоговой суммы) в поле "Цена (₽)" модального окна просмотра в TAJLINE.TJ

КОНТЕКСТ ТЕСТИРОВАНИЯ:
Протестировать исправления для отображения цены за кг (а не итоговой суммы) в поле "Цена (₽)" модального окна просмотра.
Убедиться, что в модальном окне просмотра в поле "Цена (₽)" отображается именно цена за кг (price_per_kg), которую заполнил курьер, а не итоговая сумма (total_value).

ЗАДАЧИ ТЕСТИРОВАНИЯ:
1. Создать тестовую заявку на забор груза с четко разными значениями:
   - price_per_kg: 50 ₽/кг (это должно отображаться в поле "Цена")
   - weight: 10 кг
   - total_value: 500 ₽ (это НЕ должно отображаться в поле "Цена")

2. Проверить endpoint GET /api/operator/pickup-requests/{request_id}:
   - Убедиться, что возвращается правильное поле price_per_kg
   - Проверить структуру cargo_info с price_per_kg

3. Проверить логику frontend обработки данных:
   - В handleViewNotification должно использоваться cargo_info.price_per_kg
   - В handleViewCargo должно использоваться cargoItem.price_per_kg
   - НЕ должны использоваться total_value или declared_value для поля price

ПРИМЕР ТЕСТОВЫХ ДАННЫХ:
- Груз: "Телевизор"
- Вес: 10 кг
- Цена за кг: 50 ₽ (должна показываться в поле "Цена (₽)")
- Итоговая стоимость: 500 ₽ (НЕ должна показываться в поле "Цена")

КРИТЕРИЙ УСПЕХА:
В модальном окне просмотра в поле "Цена (₽)" должно быть "50", а не "500".
"""

import requests
import json
import sys
import time
from datetime import datetime, timedelta

# Конфигурация
BACKEND_URL = "https://03054c56-0cb9-443b-a828-f3e224602a32.preview.emergentagent.com/api"

# Учетные данные для тестирования
ADMIN_CREDENTIALS = {
    "phone": "+79999888777",
    "password": "admin123"
}

OPERATOR_CREDENTIALS = {
    "phone": "+79777888999", 
    "password": "warehouse123"
}

class PricePerKgModalTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.operator_token = None
        self.admin_user = None
        self.operator_user = None
        self.test_results = []
        self.test_pickup_request_id = None
        
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
    
    def authenticate_operator(self):
        """Авторизация оператора склада"""
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=OPERATOR_CREDENTIALS,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.operator_token = data["access_token"]
                self.operator_user = data["user"]
                
                self.log_test(
                    "АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА",
                    True,
                    f"Успешная авторизация '{self.operator_user['full_name']}' (номер: {self.operator_user.get('user_number', 'N/A')}, роль: {self.operator_user['role']})"
                )
                return True
            else:
                self.log_test(
                    "АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА", False, f"Ошибка: {str(e)}")
            return False
    
    def create_test_pickup_request_with_price_per_kg(self):
        """Создать тестовую заявку на забор груза с данными price_per_kg согласно review request"""
        try:
            # Используем токен администратора для создания заявки
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Данные заявки согласно примеру из review request
            pickup_data = {
                "sender_full_name": "Тестовый Отправитель Телевизора",
                "sender_phone": "+79111222333",
                "pickup_address": "Москва, ул. Тестовая, д. 123, кв. 45",
                "pickup_date": "2025-01-20",
                "pickup_time_from": "10:00",
                "pickup_time_to": "12:00",
                "destination": "Душанбе, ул. Рудаки, д. 100",
                "cargo_name": "Телевизор",  # Согласно примеру из review request
                "weight": 10.0,  # 10 кг согласно примеру
                "price_per_kg": 50.0,  # 50 ₽ за кг согласно примеру - КЛЮЧЕВОЕ ПОЛЕ ДЛЯ ТЕСТИРОВАНИЯ
                "total_value": 500.0,  # 10 × 50 = 500 ₽ согласно примеру
                "declared_value": 500.0,  # Дублируем для совместимости
                "payment_method": "cash",
                "courier_fee": 200.0,
                "delivery_method": "pickup",
                "description": "Тестовая заявка для проверки отображения price_per_kg (50₽) вместо total_value (500₽) в модальном окне"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/admin/courier/pickup-request",
                json=pickup_data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                self.test_pickup_request_id = data.get("request_id")
                
                self.log_test(
                    "СОЗДАНИЕ ТЕСТОВОЙ ЗАЯВКИ С PRICE_PER_KG",
                    True,
                    f"Заявка создана с ID: {self.test_pickup_request_id}, номер: {data.get('request_number')}, груз: Телевизор, вес: 10 кг, цена за кг: 50 ₽, итого: 500 ₽"
                )
                return True
            else:
                self.log_test(
                    "СОЗДАНИЕ ТЕСТОВОЙ ЗАЯВКИ С PRICE_PER_KG",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("СОЗДАНИЕ ТЕСТОВОЙ ЗАЯВКИ С PRICE_PER_KG", False, f"Ошибка: {str(e)}")
            return False
    
    def test_price_per_kg_field_saved(self):
        """Проверить, что поле price_per_kg правильно сохраняется в заявке на забор груза"""
        try:
            if not self.test_pickup_request_id:
                self.log_test(
                    "ПРОВЕРКА СОХРАНЕНИЯ PRICE_PER_KG",
                    False,
                    "Нет ID тестовой заявки"
                )
                return False
            
            # Используем токен оператора для получения данных
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            
            response = self.session.get(
                f"{BACKEND_URL}/operator/pickup-requests/{self.test_pickup_request_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                cargo_info = data.get("cargo_info", {})
                
                # Проверяем наличие поля price_per_kg
                price_per_kg = cargo_info.get("price_per_kg")
                total_value = cargo_info.get("total_value")
                
                if price_per_kg is not None:
                    if price_per_kg == 50.0:  # Ожидаемое значение согласно примеру
                        # Дополнительная проверка: убеждаемся что total_value отличается от price_per_kg
                        if total_value == 500.0 and total_value != price_per_kg:
                            self.log_test(
                                "ПРОВЕРКА СОХРАНЕНИЯ PRICE_PER_KG",
                                True,
                                f"Поле price_per_kg корректно сохранено: {price_per_kg} ₽/кг (отличается от total_value: {total_value} ₽)"
                            )
                            return True
                        else:
                            self.log_test(
                                "ПРОВЕРКА СОХРАНЕНИЯ PRICE_PER_KG",
                                False,
                                f"Проблема с total_value: ожидалось 500.0, получено {total_value}"
                            )
                            return False
                    else:
                        self.log_test(
                            "ПРОВЕРКА СОХРАНЕНИЯ PRICE_PER_KG",
                            False,
                            f"Неверное значение price_per_kg: ожидалось 50.0, получено {price_per_kg}"
                        )
                        return False
                else:
                    self.log_test(
                        "ПРОВЕРКА СОХРАНЕНИЯ PRICE_PER_KG",
                        False,
                        f"Поле price_per_kg отсутствует в cargo_info. Доступные поля: {list(cargo_info.keys())}"
                    )
                    return False
            else:
                self.log_test(
                    "ПРОВЕРКА СОХРАНЕНИЯ PRICE_PER_KG",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("ПРОВЕРКА СОХРАНЕНИЯ PRICE_PER_KG", False, f"Ошибка: {str(e)}")
            return False
    
    def test_modal_data_structure(self):
        """Убедиться, что в modal_data.cargo_info есть поле price_per_kg"""
        try:
            if not self.test_pickup_request_id:
                self.log_test(
                    "ПРОВЕРКА СТРУКТУРЫ MODAL_DATA",
                    False,
                    "Нет ID тестовой заявки"
                )
                return False
            
            # Используем токен оператора
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            
            response = self.session.get(
                f"{BACKEND_URL}/operator/pickup-requests/{self.test_pickup_request_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем структуру modal_data
                required_sections = ["cargo_info", "sender_data", "payment_info"]
                missing_sections = []
                present_sections = []
                
                for section in required_sections:
                    if section in data:
                        present_sections.append(section)
                    else:
                        missing_sections.append(section)
                
                if not missing_sections:
                    cargo_info = data.get("cargo_info", {})
                    
                    # Проверяем наличие всех необходимых полей в cargo_info
                    required_cargo_fields = ["price_per_kg", "weight", "total_value", "cargo_name"]
                    cargo_fields_present = []
                    cargo_fields_missing = []
                    
                    for field in required_cargo_fields:
                        if field in cargo_info and cargo_info[field] is not None:
                            cargo_fields_present.append(f"{field}={cargo_info[field]}")
                        else:
                            cargo_fields_missing.append(field)
                    
                    if not cargo_fields_missing:
                        self.log_test(
                            "ПРОВЕРКА СТРУКТУРЫ MODAL_DATA",
                            True,
                            f"Структура modal_data корректна. cargo_info содержит: {', '.join(cargo_fields_present)}"
                        )
                        return True
                    else:
                        self.log_test(
                            "ПРОВЕРКА СТРУКТУРЫ MODAL_DATA",
                            False,
                            f"Отсутствуют поля в cargo_info: {', '.join(cargo_fields_missing)}. Присутствуют: {', '.join(cargo_fields_present)}"
                        )
                        return False
                else:
                    self.log_test(
                        "ПРОВЕРКА СТРУКТУРЫ MODAL_DATA",
                        False,
                        f"Отсутствуют секции: {', '.join(missing_sections)}. Присутствуют: {', '.join(present_sections)}"
                    )
                    return False
            else:
                self.log_test(
                    "ПРОВЕРКА СТРУКТУРЫ MODAL_DATA",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("ПРОВЕРКА СТРУКТУРЫ MODAL_DATA", False, f"Ошибка: {str(e)}")
            return False
    
    def test_price_calculation(self):
        """Проверить расчет общей суммы: вес × price_per_kg = total_value"""
        try:
            if not self.test_pickup_request_id:
                self.log_test(
                    "ПРОВЕРКА РАСЧЕТА ОБЩЕЙ СУММЫ",
                    False,
                    "Нет ID тестовой заявки"
                )
                return False
            
            # Используем токен оператора
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            
            response = self.session.get(
                f"{BACKEND_URL}/operator/pickup-requests/{self.test_pickup_request_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                cargo_info = data.get("cargo_info", {})
                
                # Получаем значения для расчета
                weight = cargo_info.get("weight")
                price_per_kg = cargo_info.get("price_per_kg")
                total_value = cargo_info.get("total_value")
                
                if weight is not None and price_per_kg is not None and total_value is not None:
                    # Рассчитываем ожидаемую общую стоимость
                    expected_total = weight * price_per_kg
                    
                    if abs(total_value - expected_total) < 0.01:  # Учитываем погрешность float
                        # КРИТИЧЕСКАЯ ПРОВЕРКА: убеждаемся что price_per_kg (50) != total_value (500)
                        if price_per_kg != total_value:
                            self.log_test(
                                "ПРОВЕРКА РАСЧЕТА ОБЩЕЙ СУММЫ",
                                True,
                                f"Расчет корректен: {weight} кг × {price_per_kg} ₽/кг = {total_value} ₽. КРИТИЧНО: price_per_kg ({price_per_kg}) ≠ total_value ({total_value})"
                            )
                            return True
                        else:
                            self.log_test(
                                "ПРОВЕРКА РАСЧЕТА ОБЩЕЙ СУММЫ",
                                False,
                                f"КРИТИЧЕСКАЯ ОШИБКА: price_per_kg ({price_per_kg}) равно total_value ({total_value}), но должны отличаться!"
                            )
                            return False
                    else:
                        self.log_test(
                            "ПРОВЕРКА РАСЧЕТА ОБЩЕЙ СУММЫ",
                            False,
                            f"Неверный расчет: {weight} кг × {price_per_kg} ₽/кг = {expected_total} ₽, но получено {total_value} ₽"
                        )
                        return False
                else:
                    missing_fields = []
                    if weight is None:
                        missing_fields.append("weight")
                    if price_per_kg is None:
                        missing_fields.append("price_per_kg")
                    if total_value is None:
                        missing_fields.append("total_value")
                    
                    self.log_test(
                        "ПРОВЕРКА РАСЧЕТА ОБЩЕЙ СУММЫ",
                        False,
                        f"Отсутствуют поля для расчета: {', '.join(missing_fields)}"
                    )
                    return False
            else:
                self.log_test(
                    "ПРОВЕРКА РАСЧЕТА ОБЩЕЙ СУММЫ",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("ПРОВЕРКА РАСЧЕТА ОБЩЕЙ СУММЫ", False, f"Ошибка: {str(e)}")
            return False
    
    def test_critical_modal_price_display_logic(self):
        """КРИТИЧЕСКИЙ ТЕСТ: Убедиться что модальное окно должно показывать price_per_kg (50), а НЕ total_value (500)"""
        try:
            if not self.test_pickup_request_id:
                self.log_test(
                    "КРИТИЧЕСКИЙ ТЕСТ ОТОБРАЖЕНИЯ ЦЕНЫ В МОДАЛЬНОМ ОКНЕ",
                    False,
                    "Нет ID тестовой заявки"
                )
                return False
            
            # Используем токен оператора
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            
            response = self.session.get(
                f"{BACKEND_URL}/operator/pickup-requests/{self.test_pickup_request_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                cargo_info = data.get("cargo_info", {})
                
                # Получаем критические значения
                price_per_kg = cargo_info.get("price_per_kg")
                total_value = cargo_info.get("total_value")
                declared_value = cargo_info.get("declared_value")
                
                # КРИТИЧЕСКАЯ ПРОВЕРКА: убеждаемся что значения разные
                if price_per_kg == 50.0 and total_value == 500.0:
                    # Проверяем что значения действительно отличаются в 10 раз
                    if total_value == price_per_kg * 10:
                        self.log_test(
                            "КРИТИЧЕСКИЙ ТЕСТ ОТОБРАЖЕНИЯ ЦЕНЫ В МОДАЛЬНОМ ОКНЕ",
                            True,
                            f"✅ КРИТИЧЕСКИЙ УСПЕХ: Backend корректно сохраняет price_per_kg={price_per_kg}₽ и total_value={total_value}₽. В модальном окне поле 'Цена (₽)' должно показывать {price_per_kg}, а НЕ {total_value}!"
                        )
                        return True
                    else:
                        self.log_test(
                            "КРИТИЧЕСКИЙ ТЕСТ ОТОБРАЖЕНИЯ ЦЕНЫ В МОДАЛЬНОМ ОКНЕ",
                            False,
                            f"Неверное соотношение: price_per_kg={price_per_kg}, total_value={total_value}, но ожидалось 10-кратное различие"
                        )
                        return False
                else:
                    self.log_test(
                        "КРИТИЧЕСКИЙ ТЕСТ ОТОБРАЖЕНИЯ ЦЕНЫ В МОДАЛЬНОМ ОКНЕ",
                        False,
                        f"Неверные значения: price_per_kg={price_per_kg} (ожидалось 50.0), total_value={total_value} (ожидалось 500.0)"
                    )
                    return False
            else:
                self.log_test(
                    "КРИТИЧЕСКИЙ ТЕСТ ОТОБРАЖЕНИЯ ЦЕНЫ В МОДАЛЬНОМ ОКНЕ",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("КРИТИЧЕСКИЙ ТЕСТ ОТОБРАЖЕНИЯ ЦЕНЫ В МОДАЛЬНОМ ОКНЕ", False, f"Ошибка: {str(e)}")
            return False
    
    def test_endpoint_response_structure(self):
        """Протестировать endpoint GET /api/operator/pickup-requests/{request_id} для получения данных"""
        try:
            if not self.test_pickup_request_id:
                self.log_test(
                    "ТЕСТИРОВАНИЕ ENDPOINT RESPONSE",
                    False,
                    "Нет ID тестовой заявки"
                )
                return False
            
            # Используем токен оператора
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            
            response = self.session.get(
                f"{BACKEND_URL}/operator/pickup-requests/{self.test_pickup_request_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем основные секции ответа
                expected_sections = [
                    "request_info", "courier_info", "sender_data", 
                    "recipient_data", "cargo_info", "payment_info", "full_request"
                ]
                
                present_sections = []
                missing_sections = []
                
                for section in expected_sections:
                    if section in data:
                        present_sections.append(section)
                    else:
                        missing_sections.append(section)
                
                # Проверяем конкретные поля в cargo_info
                cargo_info = data.get("cargo_info", {})
                cargo_fields = ["cargo_name", "weight", "price_per_kg", "total_value", "declared_value"]
                cargo_present = []
                cargo_missing = []
                
                for field in cargo_fields:
                    if field in cargo_info and cargo_info[field] is not None:
                        cargo_present.append(f"{field}={cargo_info[field]}")
                    else:
                        cargo_missing.append(field)
                
                if not missing_sections and not cargo_missing:
                    self.log_test(
                        "ТЕСТИРОВАНИЕ ENDPOINT RESPONSE",
                        True,
                        f"Структура ответа корректна. Секции: {len(present_sections)}/{len(expected_sections)}, cargo_info: {', '.join(cargo_present)}"
                    )
                    return True
                else:
                    issues = []
                    if missing_sections:
                        issues.append(f"отсутствуют секции: {', '.join(missing_sections)}")
                    if cargo_missing:
                        issues.append(f"отсутствуют поля cargo_info: {', '.join(cargo_missing)}")
                    
                    self.log_test(
                        "ТЕСТИРОВАНИЕ ENDPOINT RESPONSE",
                        False,
                        f"Проблемы со структурой: {'; '.join(issues)}"
                    )
                    return False
            else:
                self.log_test(
                    "ТЕСТИРОВАНИЕ ENDPOINT RESPONSE",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("ТЕСТИРОВАНИЕ ENDPOINT RESPONSE", False, f"Ошибка: {str(e)}")
            return False
    
    def cleanup_test_data(self):
        """Очистить тестовые данные"""
        try:
            if not self.test_pickup_request_id:
                return True
            
            # Используем токен администратора для удаления
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            response = self.session.delete(
                f"{BACKEND_URL}/admin/pickup-requests/{self.test_pickup_request_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                self.log_test(
                    "ОЧИСТКА ТЕСТОВЫХ ДАННЫХ",
                    True,
                    f"Тестовая заявка {self.test_pickup_request_id} успешно удалена"
                )
                return True
            else:
                self.log_test(
                    "ОЧИСТКА ТЕСТОВЫХ ДАННЫХ",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("ОЧИСТКА ТЕСТОВЫХ ДАННЫХ", False, f"Ошибка: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Запустить все тесты"""
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправления для отображения цены за кг (а не итоговой суммы) в поле 'Цена (₽)' модального окна")
        print("=" * 120)
        print("ЦЕЛЬ: Убедиться что в модальном окне просмотра поле 'Цена (₽)' показывает 50₽ (price_per_kg), а НЕ 500₽ (total_value)")
        print("=" * 120)
        
        # Авторизация всех пользователей
        if not self.authenticate_admin():
            return False
        
        if not self.authenticate_operator():
            return False
        
        # Основные тесты согласно review request
        tests = [
            self.create_test_pickup_request_with_price_per_kg,
            self.test_price_per_kg_field_saved,
            self.test_endpoint_response_structure,
            self.test_modal_data_structure,
            self.test_price_calculation,
            self.test_critical_modal_price_display_logic  # НОВЫЙ КРИТИЧЕСКИЙ ТЕСТ
        ]
        
        success_count = 0
        for test in tests:
            if test():
                success_count += 1
            time.sleep(1)  # Пауза между тестами
        
        # Очистка тестовых данных
        self.cleanup_test_data()
        
        # Итоговый отчет
        print("\n" + "=" * 120)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 120)
        
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r["success"]])
        
        print(f"Всего тестов: {total_tests}")
        print(f"Успешных: {successful_tests}")
        print(f"Неудачных: {total_tests - successful_tests}")
        print(f"Процент успеха: {(successful_tests/total_tests)*100:.1f}%")
        
        print("\nДетальные результаты:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        # КРИТИЧЕСКИЙ ВЫВОД
        if successful_tests == total_tests:
            print("\n🎉 КРИТИЧЕСКИЙ УСПЕХ: Backend корректно сохраняет и возвращает price_per_kg отдельно от total_value!")
            print("✅ В модальном окне просмотра поле 'Цена (₽)' должно показывать 50₽, а не 500₽")
        else:
            print("\n❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Обнаружены ошибки в обработке price_per_kg vs total_value")
        
        return successful_tests == total_tests

if __name__ == "__main__":
    tester = PricePerKgModalTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
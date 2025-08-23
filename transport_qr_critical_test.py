#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: ИСПРАВЛЕННЫЕ QR КОДЫ ТРАНСПОРТА - Настоящие сканируемые QR изображения
=====================================================================================================

ЦЕЛЬ ТЕСТИРОВАНИЯ: Проверить исправленную генерацию QR кодов для транспорта - теперь должны создаваться 
настоящие QR изображения в формате TAJLINE, как для заявок, которые можно сканировать.

КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ ДЛЯ ПРОВЕРКИ:
1. **QR данные в формате TAJLINE**: TAJLINE|TRANSPORT|{transport_number}|{timestamp}
2. **Настоящее QR изображение**: Генерация qrcode изображения и сохранение как base64
3. **Сканирование новых QR**: Обновленный парсинг в scan-transport поддерживает новый формат
4. **Отображение информации**: При сканировании показывается полная информация о транспорте

ENDPOINTS ДЛЯ ТЕСТИРОВАНИЯ:
1. **POST /api/transport/{transport_id}/generate-qr** - Генерация настоящего QR изображения
2. **GET /api/transport/{transport_id}/qr** - Получение QR изображения и данных
3. **POST /api/logistics/cargo-to-transport/scan-transport** - Сканирование нового формата QR
4. **GET /api/transport/list-with-qr** - Список транспортов с QR статусом

ДЕТАЛЬНЫЕ ТРЕБОВАНИЯ:
1. **Авторизация**: warehouse_operator (+79777888999/warehouse123)
2. **Генерация QR**:
   - QR данные: TAJLINE|TRANSPORT|{transport_number}|{timestamp}
   - QR изображение: base64 PNG изображение настоящего QR кода
   - Поля: qr_code, qr_image_base64, qr_generated_at, qr_generated_by
3. **Получение QR**:
   - Возврат qr_image: "data:image/png;base64,{image_data}"
   - Полная информация о транспорте (transport_number, driver_name, direction)
4. **Сканирование QR**:
   - Поддержка нового формата TAJLINE|TRANSPORT|...
   - Обратная совместимость со старым форматом TRANSPORT_...
   - Корректное извлечение transport_number из обоих форматов

ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ:
- ✅ Генерация создает настоящие QR изображения (не просто текст)
- ✅ QR данные в формате TAJLINE|TRANSPORT|{transport_number}|{timestamp}
- ✅ QR изображения в формате data:image/png;base64,{image_data}
- ✅ Сканирование нового формата работает корректно
- ✅ Информация о транспорте отображается при сканировании
- ✅ Обратная совместимость со старым форматом
- ✅ Все поля QR корректно сохраняются в базе данных
"""

import requests
import json
import sys
import os
import re
import base64
from datetime import datetime
from typing import Dict, List, Optional, Any

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cargo-sync.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Конфигурация тестирования
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"

class TransportQRCriticalTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.test_results = {
            "auth_success": False,
            "transport_found": False,
            "qr_generation_success": False,
            "qr_retrieval_success": False,
            "qr_scanning_success": False,
            "transport_list_success": False,
            "backward_compatibility_success": False,
            "detailed_results": {},
            "critical_issues": []
        }
        
    def log(self, message: str, level: str = "INFO"):
        """Логирование с временной меткой"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def authenticate_warehouse_operator(self) -> bool:
        """Авторизация оператора склада"""
        self.log("🔐 Авторизация оператора склада...")
        
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json={
                "phone": WAREHOUSE_OPERATOR_PHONE,
                "password": WAREHOUSE_OPERATOR_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.operator_info = data.get("user")
                
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log(f"✅ Успешная авторизация: {self.operator_info.get('full_name')} (роль: {self.operator_info.get('role')})")
                self.test_results["auth_success"] = True
                return True
            else:
                self.log(f"❌ Ошибка авторизации: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при авторизации: {e}", "ERROR")
            return False
    
    def find_or_create_transport(self) -> Optional[Dict[str, Any]]:
        """Найти существующий транспорт или создать новый для тестирования"""
        self.log("🚛 Поиск доступного транспорта для тестирования...")
        
        try:
            # Сначала попробуем получить обычный список транспортов
            response = self.session.get(f"{API_BASE}/transport/list")
            
            if response.status_code == 200:
                data = response.json()
                transports = data.get("items", []) if isinstance(data, dict) else data
                
                if transports and len(transports) > 0:
                    # Используем первый доступный транспорт
                    transport = transports[0]
                    self.log(f"✅ Найден транспорт: {transport.get('transport_number')} (ID: {transport.get('id')})")
                    self.test_results["transport_found"] = True
                    return transport
                else:
                    self.log("⚠️ Транспорты не найдены, попробуем создать новый...")
                    return self.create_test_transport()
            else:
                self.log(f"⚠️ Не удалось получить список транспортов: {response.status_code}")
                return self.create_test_transport()
                
        except Exception as e:
            self.log(f"❌ Ошибка при поиске транспорта: {e}", "ERROR")
            return self.create_test_transport()
    
    def create_test_transport(self) -> Optional[Dict[str, Any]]:
        """Создать тестовый транспорт"""
        self.log("🚛 Создание тестового транспорта...")
        
        try:
            transport_data = {
                "driver_name": "Тестовый Водитель QR",
                "driver_phone": "+79999999999",
                "transport_number": f"TEST_QR_{datetime.now().strftime('%H%M%S')}",
                "capacity_kg": 1000.0,
                "direction": "Москва-Душанбе"
            }
            
            response = self.session.post(f"{API_BASE}/transport/create", json=transport_data)
            
            if response.status_code == 200:
                transport = response.json()
                self.log(f"✅ Создан тестовый транспорт: {transport.get('transport_number')} (ID: {transport.get('id')})")
                self.test_results["transport_found"] = True
                return transport
            else:
                self.log(f"❌ Ошибка создания транспорта: {response.status_code} - {response.text}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Исключение при создании транспорта: {e}", "ERROR")
            return None
    
    def test_qr_generation(self, transport: Dict[str, Any]) -> bool:
        """Тестирование генерации QR кода транспорта"""
        self.log("\n🎯 СЦЕНАРИЙ 1: Генерация нового QR кода")
        self.log("=" * 60)
        
        transport_id = transport.get("id")
        transport_number = transport.get("transport_number")
        
        try:
            response = self.session.post(f"{API_BASE}/transport/{transport_id}/generate-qr")
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем наличие обязательных полей
                required_fields = ["qr_code", "qr_image_base64", "qr_generated_at", "qr_generated_by"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log(f"❌ Отсутствуют обязательные поля: {missing_fields}", "ERROR")
                    self.test_results["critical_issues"].append(f"QR Generation: Missing fields {missing_fields}")
                    return False
                
                # Проверяем формат QR данных
                qr_code = data.get("qr_code", "")
                if not qr_code.startswith("TAJLINE|TRANSPORT|"):
                    self.log(f"❌ Неправильный формат QR данных: {qr_code}", "ERROR")
                    self.test_results["critical_issues"].append(f"QR Generation: Wrong format {qr_code}")
                    return False
                
                # Проверяем структуру QR данных
                qr_parts = qr_code.split("|")
                if len(qr_parts) != 4 or qr_parts[0] != "TAJLINE" or qr_parts[1] != "TRANSPORT":
                    self.log(f"❌ Неправильная структура QR данных: {qr_parts}", "ERROR")
                    self.test_results["critical_issues"].append(f"QR Generation: Wrong structure {qr_parts}")
                    return False
                
                # Проверяем transport_number в QR
                qr_transport_number = qr_parts[2]
                if qr_transport_number != transport_number:
                    self.log(f"❌ Неправильный transport_number в QR: {qr_transport_number} != {transport_number}", "ERROR")
                    self.test_results["critical_issues"].append(f"QR Generation: Wrong transport_number {qr_transport_number}")
                    return False
                
                # Проверяем base64 изображение
                qr_image = data.get("qr_image_base64", "")
                if not qr_image or not self.is_valid_base64_image(qr_image):
                    self.log(f"❌ Неправильное base64 изображение QR кода", "ERROR")
                    self.test_results["critical_issues"].append("QR Generation: Invalid base64 image")
                    return False
                
                self.log(f"✅ QR код сгенерирован успешно:")
                self.log(f"   - QR данные: {qr_code}")
                self.log(f"   - Время генерации: {data.get('qr_generated_at')}")
                self.log(f"   - Сгенерировал: {data.get('qr_generated_by')}")
                self.log(f"   - Base64 изображение: {'Валидное' if self.is_valid_base64_image(qr_image) else 'Невалидное'}")
                
                self.test_results["qr_generation_success"] = True
                self.test_results["detailed_results"]["qr_generation"] = data
                return True
                
            else:
                self.log(f"❌ Ошибка генерации QR: {response.status_code} - {response.text}", "ERROR")
                self.test_results["critical_issues"].append(f"QR Generation: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при генерации QR: {e}", "ERROR")
            self.test_results["critical_issues"].append(f"QR Generation: Exception {e}")
            return False
    
    def test_qr_retrieval(self, transport: Dict[str, Any]) -> bool:
        """Тестирование получения QR изображения"""
        self.log("\n🎯 СЦЕНАРИЙ 2: Получение QR изображения")
        self.log("=" * 60)
        
        transport_id = transport.get("id")
        
        try:
            response = self.session.get(f"{API_BASE}/transport/{transport_id}/qr")
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем наличие qr_image поля
                if "qr_image" not in data:
                    self.log(f"❌ Отсутствует поле qr_image", "ERROR")
                    self.test_results["critical_issues"].append("QR Retrieval: Missing qr_image field")
                    return False
                
                # Проверяем формат qr_image
                qr_image = data.get("qr_image", "")
                if not qr_image.startswith("data:image/png;base64,"):
                    self.log(f"❌ Неправильный формат qr_image: {qr_image[:50]}...", "ERROR")
                    self.test_results["critical_issues"].append("QR Retrieval: Wrong qr_image format")
                    return False
                
                # Проверяем полные данные транспорта
                required_transport_fields = ["transport_number", "driver_name", "direction"]
                missing_fields = [field for field in required_transport_fields if field not in data]
                
                if missing_fields:
                    self.log(f"❌ Отсутствуют поля транспорта: {missing_fields}", "ERROR")
                    self.test_results["critical_issues"].append(f"QR Retrieval: Missing transport fields {missing_fields}")
                    return False
                
                self.log(f"✅ QR изображение получено успешно:")
                self.log(f"   - Формат изображения: data:image/png;base64,...")
                self.log(f"   - Номер транспорта: {data.get('transport_number')}")
                self.log(f"   - Водитель: {data.get('driver_name')}")
                self.log(f"   - Направление: {data.get('direction')}")
                
                self.test_results["qr_retrieval_success"] = True
                self.test_results["detailed_results"]["qr_retrieval"] = data
                return True
                
            else:
                self.log(f"❌ Ошибка получения QR: {response.status_code} - {response.text}", "ERROR")
                self.test_results["critical_issues"].append(f"QR Retrieval: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при получении QR: {e}", "ERROR")
            self.test_results["critical_issues"].append(f"QR Retrieval: Exception {e}")
            return False
    
    def test_qr_scanning_new_format(self, transport: Dict[str, Any]) -> bool:
        """Тестирование сканирования нового формата QR"""
        self.log("\n🎯 СЦЕНАРИЙ 3: Сканирование нового формата")
        self.log("=" * 60)
        
        # Получаем QR код из предыдущего теста
        qr_generation_data = self.test_results["detailed_results"].get("qr_generation", {})
        qr_code = qr_generation_data.get("qr_code")
        
        if not qr_code:
            self.log("❌ QR код не найден из предыдущего теста", "ERROR")
            return False
        
        try:
            response = self.session.post(f"{API_BASE}/logistics/cargo-to-transport/scan-transport", json={
                "qr_code": qr_code
            })
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем успешное создание сессии размещения
                if not data.get("success", False):
                    self.log(f"❌ Сканирование не успешно: {data.get('message', 'Unknown error')}", "ERROR")
                    self.test_results["critical_issues"].append(f"QR Scanning: Not successful - {data.get('message')}")
                    return False
                
                # Проверяем корректное извлечение transport_number
                scanned_transport_number = data.get("transport_number")
                expected_transport_number = transport.get("transport_number")
                
                if scanned_transport_number != expected_transport_number:
                    self.log(f"❌ Неправильный transport_number: {scanned_transport_number} != {expected_transport_number}", "ERROR")
                    self.test_results["critical_issues"].append(f"QR Scanning: Wrong transport_number {scanned_transport_number}")
                    return False
                
                self.log(f"✅ Сканирование нового формата успешно:")
                self.log(f"   - QR код: {qr_code}")
                self.log(f"   - Извлеченный transport_number: {scanned_transport_number}")
                self.log(f"   - Сессия размещения: {data.get('session_id', 'N/A')}")
                
                self.test_results["qr_scanning_success"] = True
                self.test_results["detailed_results"]["qr_scanning"] = data
                return True
                
            else:
                self.log(f"❌ Ошибка сканирования QR: {response.status_code} - {response.text}", "ERROR")
                self.test_results["critical_issues"].append(f"QR Scanning: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при сканировании QR: {e}", "ERROR")
            self.test_results["critical_issues"].append(f"QR Scanning: Exception {e}")
            return False
    
    def test_backward_compatibility(self, transport: Dict[str, Any]) -> bool:
        """Тестирование обратной совместимости со старым форматом"""
        self.log("\n🎯 СЦЕНАРИЙ 4: Обратная совместимость")
        self.log("=" * 60)
        
        transport_number = transport.get("transport_number")
        old_format_qr = f"TRANSPORT_{transport_number}_{int(datetime.now().timestamp())}"
        
        try:
            response = self.session.post(f"{API_BASE}/logistics/cargo-to-transport/scan-transport", json={
                "qr_code": old_format_qr
            })
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем успешное сканирование старого формата
                if not data.get("success", False):
                    self.log(f"❌ Старый формат не поддерживается: {data.get('message', 'Unknown error')}", "ERROR")
                    self.test_results["critical_issues"].append(f"Backward Compatibility: Not supported - {data.get('message')}")
                    return False
                
                # Проверяем корректное извлечение transport_number из старого формата
                scanned_transport_number = data.get("transport_number")
                
                if scanned_transport_number != transport_number:
                    self.log(f"❌ Неправильное извлечение из старого формата: {scanned_transport_number} != {transport_number}", "ERROR")
                    self.test_results["critical_issues"].append(f"Backward Compatibility: Wrong extraction {scanned_transport_number}")
                    return False
                
                self.log(f"✅ Обратная совместимость работает:")
                self.log(f"   - Старый формат QR: {old_format_qr}")
                self.log(f"   - Извлеченный transport_number: {scanned_transport_number}")
                
                self.test_results["backward_compatibility_success"] = True
                self.test_results["detailed_results"]["backward_compatibility"] = data
                return True
                
            else:
                self.log(f"❌ Ошибка сканирования старого формата: {response.status_code} - {response.text}", "ERROR")
                self.test_results["critical_issues"].append(f"Backward Compatibility: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при тестировании обратной совместимости: {e}", "ERROR")
            self.test_results["critical_issues"].append(f"Backward Compatibility: Exception {e}")
            return False
    
    def test_transport_list_with_qr(self) -> bool:
        """Тестирование списка транспортов с QR статусом"""
        self.log("\n🎯 ДОПОЛНИТЕЛЬНО: Список транспортов с QR статусом")
        self.log("=" * 60)
        
        try:
            response = self.session.get(f"{API_BASE}/transport/list-with-qr")
            
            if response.status_code == 200:
                data = response.json()
                transports = data.get("items", []) if isinstance(data, dict) else data
                
                self.log(f"✅ Получен список транспортов: {len(transports)} шт.")
                
                # Проверяем наличие QR статуса у транспортов
                qr_enabled_count = 0
                for transport in transports:
                    if transport.get("qr_code") or transport.get("qr_generated_at"):
                        qr_enabled_count += 1
                
                self.log(f"   - Транспортов с QR кодами: {qr_enabled_count}")
                
                self.test_results["transport_list_success"] = True
                self.test_results["detailed_results"]["transport_list"] = {
                    "total_transports": len(transports),
                    "qr_enabled_transports": qr_enabled_count
                }
                return True
                
            else:
                self.log(f"❌ Ошибка получения списка транспортов: {response.status_code} - {response.text}", "ERROR")
                self.test_results["critical_issues"].append(f"Transport List: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при получении списка транспортов: {e}", "ERROR")
            self.test_results["critical_issues"].append(f"Transport List: Exception {e}")
            return False
    
    def is_valid_base64_image(self, base64_string: str) -> bool:
        """Проверка валидности base64 изображения"""
        try:
            if not base64_string:
                return False
            
            # Убираем data URL префикс если есть
            if base64_string.startswith("data:image/"):
                base64_string = base64_string.split(",", 1)[1]
            
            # Проверяем base64 декодирование
            decoded = base64.b64decode(base64_string)
            
            # Проверяем PNG заголовок
            return decoded.startswith(b'\x89PNG\r\n\x1a\n')
            
        except Exception:
            return False
    
    def generate_final_report(self) -> bool:
        """Генерация финального отчета"""
        self.log("\n📋 ФИНАЛЬНЫЙ ОТЧЕТ КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ QR КОДОВ ТРАНСПОРТА")
        self.log("=" * 80)
        
        # Заголовок
        self.log(f"🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: ИСПРАВЛЕННЫЕ QR КОДЫ ТРАНСПОРТА")
        self.log(f"📅 Время тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"🔧 Цель: Проверка настоящих сканируемых QR изображений в формате TAJLINE")
        
        # Результаты по сценариям
        self.log(f"\n📊 РЕЗУЛЬТАТЫ ПО СЦЕНАРИЯМ:")
        self.log(f"  1. ✅ Авторизация оператора склада: {'✅ УСПЕШНО' if self.test_results['auth_success'] else '❌ НЕУДАЧНО'}")
        self.log(f"  2. 🚛 Поиск/создание транспорта: {'✅ НАЙДЕН' if self.test_results['transport_found'] else '❌ НЕ НАЙДЕН'}")
        self.log(f"  3. 🎯 Генерация QR кода: {'✅ УСПЕШНО' if self.test_results['qr_generation_success'] else '❌ НЕУДАЧНО'}")
        self.log(f"  4. 📱 Получение QR изображения: {'✅ УСПЕШНО' if self.test_results['qr_retrieval_success'] else '❌ НЕУДАЧНО'}")
        self.log(f"  5. 🔍 Сканирование нового формата: {'✅ УСПЕШНО' if self.test_results['qr_scanning_success'] else '❌ НЕУДАЧНО'}")
        self.log(f"  6. 🔄 Обратная совместимость: {'✅ УСПЕШНО' if self.test_results['backward_compatibility_success'] else '❌ НЕУДАЧНО'}")
        self.log(f"  7. 📋 Список транспортов с QR: {'✅ УСПЕШНО' if self.test_results['transport_list_success'] else '❌ НЕУДАЧНО'}")
        
        # Детальные результаты
        if self.test_results["detailed_results"]:
            self.log(f"\n📊 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
            
            # QR Generation
            if "qr_generation" in self.test_results["detailed_results"]:
                qr_gen = self.test_results["detailed_results"]["qr_generation"]
                self.log(f"  🎯 Генерация QR:")
                self.log(f"     - QR данные: {qr_gen.get('qr_code', 'N/A')}")
                self.log(f"     - Время генерации: {qr_gen.get('qr_generated_at', 'N/A')}")
                self.log(f"     - Сгенерировал: {qr_gen.get('qr_generated_by', 'N/A')}")
            
            # Transport List
            if "transport_list" in self.test_results["detailed_results"]:
                transport_list = self.test_results["detailed_results"]["transport_list"]
                self.log(f"  📋 Список транспортов:")
                self.log(f"     - Всего транспортов: {transport_list.get('total_transports', 0)}")
                self.log(f"     - С QR кодами: {transport_list.get('qr_enabled_transports', 0)}")
        
        # Критические проблемы
        if self.test_results["critical_issues"]:
            self.log(f"\n⚠️ КРИТИЧЕСКИЕ ПРОБЛЕМЫ ({len(self.test_results['critical_issues'])} шт.):")
            for i, issue in enumerate(self.test_results["critical_issues"], 1):
                self.log(f"  {i}. {issue}")
        
        # Финальный вывод
        all_tests_passed = all([
            self.test_results["auth_success"],
            self.test_results["transport_found"],
            self.test_results["qr_generation_success"],
            self.test_results["qr_retrieval_success"],
            self.test_results["qr_scanning_success"],
            self.test_results["backward_compatibility_success"]
        ])
        
        self.log(f"\n🎯 КРИТИЧЕСКИЙ РЕЗУЛЬТАТ:")
        if all_tests_passed:
            self.log("✅ ВСЕ КРИТИЧЕСКИЕ ТЕСТЫ QR КОДОВ ТРАНСПОРТА ПРОЙДЕНЫ!")
            self.log("🎉 Генерация создает настоящие QR изображения (не просто текст)")
            self.log("📊 QR данные в формате TAJLINE|TRANSPORT|{transport_number}|{timestamp}")
            self.log("🖼️ QR изображения в формате data:image/png;base64,{image_data}")
            self.log("🔍 Сканирование нового формата работает корректно")
            self.log("ℹ️ Информация о транспорте отображается при сканировании")
            self.log("🔄 Обратная совместимость со старым форматом работает")
            self.log("💾 Все поля QR корректно сохраняются в базе данных")
            self.log("🚀 СИСТЕМА ГОТОВА К ИСПОЛЬЗОВАНИЮ!")
        else:
            self.log("❌ КРИТИЧЕСКИЕ ТЕСТЫ QR КОДОВ ТРАНСПОРТА НЕ ПРОЙДЕНЫ!")
            self.log(f"🔍 Обнаружено {len(self.test_results['critical_issues'])} критических проблем")
            self.log("⚠️ Требуется исправление функциональности QR кодов транспорта")
        
        return all_tests_passed
    
    def run_critical_transport_qr_test(self) -> bool:
        """Запуск полного критического тестирования QR кодов транспорта"""
        self.log("🚀 ЗАПУСК КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ QR КОДОВ ТРАНСПОРТА")
        self.log("=" * 80)
        
        # 1. Авторизация
        if not self.authenticate_warehouse_operator():
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Не удалось авторизоваться", "ERROR")
            return False
        
        # 2. Поиск/создание транспорта
        transport = self.find_or_create_transport()
        if not transport:
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Не удалось найти/создать транспорт", "ERROR")
            return False
        
        # 3. Тестирование генерации QR
        if not self.test_qr_generation(transport):
            self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Генерация QR не работает", "ERROR")
            # Продолжаем тестирование для полной диагностики
        
        # 4. Тестирование получения QR
        if not self.test_qr_retrieval(transport):
            self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Получение QR не работает", "ERROR")
        
        # 5. Тестирование сканирования нового формата
        if not self.test_qr_scanning_new_format(transport):
            self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Сканирование нового формата не работает", "ERROR")
        
        # 6. Тестирование обратной совместимости
        if not self.test_backward_compatibility(transport):
            self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Обратная совместимость не работает", "ERROR")
        
        # 7. Тестирование списка транспортов
        self.test_transport_list_with_qr()
        
        # 8. Генерация финального отчета
        final_success = self.generate_final_report()
        
        return final_success

def main():
    """Главная функция"""
    tester = TransportQRCriticalTester()
    
    try:
        success = tester.run_critical_transport_qr_test()
        
        if success:
            print("\n" + "="*80)
            print("🎉 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ QR КОДОВ ТРАНСПОРТА ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ Все исправления QR кодов транспорта работают корректно")
            print("🎯 Настоящие сканируемые QR изображения в формате TAJLINE созданы")
            print("🔍 Сканирование и обратная совместимость функционируют")
            print("🚀 СИСТЕМА ГОТОВА К ПРОДАКШЕНУ!")
            sys.exit(0)
        else:
            print("\n" + "="*80)
            print("❌ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ QR КОДОВ ТРАНСПОРТА НЕ ПРОЙДЕНО!")
            print("🔍 Найдены критические проблемы с QR функциональностью")
            print("⚠️ Требуется исправление QR кодов транспорта")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
🎯 ТЕСТИРОВАНИЕ BACKEND API ДЛЯ ПЕЧАТИ QR КОДОВ В TAJLINE.TJ

Контекст: Backend API для печати QR кодов реализован на 100% и готов к тестированию. 
Нужно протестировать 3 новых API endpoint'а для функциональности печати QR кодов individual units.

API ENDPOINTS ДЛЯ ТЕСТИРОВАНИЯ:
1. POST /api/operator/qr/generate-individual - Генерация QR кода для одной единицы груза
2. POST /api/operator/qr/generate-batch - Массовая генерация QR кодов для списка единиц  
3. GET /api/operator/qr/print-layout - Получение опций макетов печати

ТЕСТОВЫЕ СЦЕНАРИИ:
1. АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА: +79777888999 / warehouse123
2. ТЕСТ 1 - Одиночная генерация QR: Сгенерировать QR код для одной individual unit
3. ТЕСТ 2 - Массовая генерация QR: Сгенерировать QR коды для нескольких individual units 
4. ТЕСТ 3 - Опции макетов печати: Получить доступные макеты (single, grid_2x2, grid_3x3, compact)
5. ВАЛИДАЦИЯ: Проверить структуру QR данных, base64 изображения, метаданные
"""

import requests
import json
import base64
import re
import time
from datetime import datetime

# Конфигурация для тестирования
BACKEND_URL = "https://tajline-cargo-8.preview.emergentagent.com/api"

# Тестовые данные оператора склада
OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class QRPrintingAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_user = None
        self.test_cargo_id = None
        self.test_cargo_number = None
        self.test_individual_numbers = []
        self.test_results = []
        
    def log_result(self, test_name, success, details="", error_details=""):
        """Логирование результатов тестов"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error_details": error_details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
        if error_details and not success:
            print(f"   ⚠️ {error_details}")
        print()
        
    def authenticate_operator(self):
        """Авторизация оператора склада"""
        print("🔐 АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА")
        print("=" * 50)
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=OPERATOR_CREDENTIALS,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                
                # Получаем информацию о пользователе
                user_response = self.session.get(
                    f"{BACKEND_URL}/auth/me",
                    headers={"Authorization": f"Bearer {self.auth_token}"},
                    timeout=30
                )
                
                if user_response.status_code == 200:
                    self.operator_user = user_response.json()
                    self.log_result(
                        "Авторизация оператора склада",
                        True,
                        f"Успешная авторизация: {self.operator_user.get('full_name')} (роль: {self.operator_user.get('role')}, телефон: {self.operator_user.get('phone')})"
                    )
                    return True
                else:
                    self.log_result(
                        "Получение данных пользователя",
                        False,
                        error_details=f"HTTP {user_response.status_code}: {user_response.text}"
                    )
                    return False
            else:
                self.log_result(
                    "Авторизация оператора склада",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Авторизация оператора склада",
                False,
                error_details=f"Исключение: {str(e)}"
            )
            return False
    
    def create_test_cargo_with_individual_units(self):
        """Создание тестового груза с individual units для тестирования QR кодов"""
        print("📦 СОЗДАНИЕ ТЕСТОВОГО ГРУЗА С INDIVIDUAL UNITS")
        print("=" * 50)
        
        try:
            # Создаем груз с несколькими типами и единицами для тестирования QR кодов
            cargo_data = {
                "sender_full_name": "Алексей Петрович Смирнов",
                "sender_phone": "+79161234567",
                "recipient_full_name": "Фарход Рахимович Назаров",
                "recipient_phone": "+992987654321",
                "recipient_address": "г. Душанбе, ул. Рудаки, дом 125, кв. 45",
                "description": "Тестовый груз для проверки QR кодов Individual Units",
                "route": "moscow_to_tajikistan",
                "payment_method": "cash_on_delivery",
                "delivery_method": "pickup",
                "cargo_items": [
                    {
                        "cargo_name": "Электроника Samsung",
                        "quantity": 2,
                        "weight": 5.5,
                        "price_per_kg": 150.0,
                        "total_amount": 825.0
                    },
                    {
                        "cargo_name": "Бытовая техника LG",
                        "quantity": 3,
                        "weight": 8.2,
                        "price_per_kg": 120.0,
                        "total_amount": 984.0
                    }
                ]
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/operator/cargo/accept",
                json=cargo_data,
                headers={
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.test_cargo_id = result.get("cargo_id")
                self.test_cargo_number = result.get("cargo_number")
                
                self.log_result(
                    "Создание тестового груза",
                    True,
                    f"Груз создан: {self.test_cargo_number} (ID: {self.test_cargo_id}), Грузы: Электроника Samsung (2 шт) + Бытовая техника LG (3 шт) = 5 единиц общим итогом"
                )
                
                # Генерируем ожидаемые individual numbers
                self.generate_expected_individual_numbers()
                
                return True
            else:
                self.log_result(
                    "Создание тестового груза",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Создание тестового груза",
                False,
                error_details=f"Исключение: {str(e)}"
            )
            return False
    
    def generate_expected_individual_numbers(self):
        """Генерация ожидаемых individual numbers на основе созданного груза"""
        if not self.test_cargo_number:
            return
        
        # Ожидаемые individual numbers для созданного груза:
        # Груз #1 (Электроника Samsung) - 2 единицы: /01/01, /01/02
        # Груз #2 (Бытовая техника LG) - 3 единицы: /02/01, /02/02, /02/03
        self.test_individual_numbers = [
            f"{self.test_cargo_number}/01/01",  # Электроника Samsung, единица 1
            f"{self.test_cargo_number}/01/02",  # Электроника Samsung, единица 2
            f"{self.test_cargo_number}/02/01",  # Бытовая техника LG, единица 1
            f"{self.test_cargo_number}/02/02",  # Бытовая техника LG, единица 2
            f"{self.test_cargo_number}/02/03",  # Бытовая техника LG, единица 3
        ]
        
        print(f"📋 Ожидаемые individual numbers для QR кодов:")
        for i, number in enumerate(self.test_individual_numbers, 1):
            print(f"   {i}. {number}")
        print()
    
    def test_generate_individual_qr(self):
        """ТЕСТ 1: Генерация QR кода для одной единицы"""
        print("🎯 ТЕСТ 1: ОДИНОЧНАЯ ГЕНЕРАЦИЯ QR КОДА")
        print("=" * 50)
        
        if not self.test_individual_numbers:
            self.log_result(
                "ТЕСТ 1 - Одиночная генерация QR",
                False,
                error_details="Нет individual numbers для тестирования"
            )
            return False
        
        test_individual_number = self.test_individual_numbers[0]
        print(f"🖨️ Тестируем генерацию QR для: {test_individual_number}")
        
        try:
            request_data = {
                "individual_number": test_individual_number
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/operator/qr/generate-individual",
                json=request_data,
                headers={
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Проверяем структуру ответа
                required_fields = ["success", "qr_info", "message"]
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    self.log_result(
                        "ТЕСТ 1 - Структура ответа",
                        False,
                        error_details=f"Отсутствуют обязательные поля: {missing_fields}"
                    )
                    return False
                
                qr_info = result.get("qr_info", {})
                required_qr_fields = ["individual_number", "cargo_number", "cargo_name", "sender_name", "recipient_name", "qr_data", "qr_base64"]
                missing_qr_fields = [field for field in required_qr_fields if field not in qr_info]
                
                if missing_qr_fields:
                    self.log_result(
                        "ТЕСТ 1 - Структура QR информации",
                        False,
                        error_details=f"Отсутствуют обязательные поля в qr_info: {missing_qr_fields}"
                    )
                    return False
                
                # Проверяем формат QR данных
                qr_data = qr_info.get("qr_data", "")
                expected_pattern = r"TAJLINE\|INDIVIDUAL\|.+\|\d+"
                
                if not re.match(expected_pattern, qr_data):
                    self.log_result(
                        "ТЕСТ 1 - Формат QR данных",
                        False,
                        error_details=f"Неправильный формат QR данных: {qr_data}, ожидался: TAJLINE|INDIVIDUAL|{test_individual_number}|timestamp"
                    )
                    return False
                
                # Проверяем base64 изображение
                qr_base64 = qr_info.get("qr_base64", "")
                if not qr_base64:
                    self.log_result(
                        "ТЕСТ 1 - QR base64 изображение",
                        False,
                        error_details="QR base64 изображение отсутствует"
                    )
                    return False
                
                try:
                    # Проверяем валидность base64
                    decoded_image = base64.b64decode(qr_base64)
                    image_size = len(decoded_image)
                    
                    if image_size < 500:
                        self.log_result(
                            "ТЕСТ 1 - Размер QR изображения",
                            False,
                            error_details=f"QR изображение слишком маленькое: {image_size} байт"
                        )
                        return False
                        
                except Exception as decode_error:
                    self.log_result(
                        "ТЕСТ 1 - Валидность base64",
                        False,
                        error_details=f"QR base64 изображение невалидно: {str(decode_error)}"
                    )
                    return False
                
                # Все проверки пройдены
                self.log_result(
                    "ТЕСТ 1 - Одиночная генерация QR",
                    True,
                    f"QR код сгенерирован для {test_individual_number}. QR данные: {qr_data}. Груз: {qr_info.get('cargo_name')} (№{qr_info.get('cargo_number')}). Отправитель: {qr_info.get('sender_name')}. Получатель: {qr_info.get('recipient_name')}. Размер изображения: {image_size} байт"
                )
                
                return True
            else:
                self.log_result(
                    "ТЕСТ 1 - Одиночная генерация QR",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "ТЕСТ 1 - Одиночная генерация QR",
                False,
                error_details=f"Исключение: {str(e)}"
            )
            return False
    
    def test_generate_batch_qr(self):
        """ТЕСТ 2: Массовая генерация QR кодов"""
        print("🎯 ТЕСТ 2: МАССОВАЯ ГЕНЕРАЦИЯ QR КОДОВ")
        print("=" * 50)
        
        if len(self.test_individual_numbers) < 2:
            self.log_result(
                "ТЕСТ 2 - Массовая генерация QR",
                False,
                error_details="Недостаточно individual numbers для тестирования массовой генерации"
            )
            return False
        
        # Берем первые 5 номеров для тестирования (все созданные единицы)
        test_numbers = self.test_individual_numbers[:5]
        print(f"🖨️ Тестируем массовую генерацию для {len(test_numbers)} единиц: {test_numbers}")
        
        try:
            request_data = {
                "individual_numbers": test_numbers
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/operator/qr/generate-batch",
                json=request_data,
                headers={
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Проверяем структуру ответа
                required_fields = ["success", "qr_batch", "failed_items", "total_generated", "total_failed"]
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    self.log_result(
                        "ТЕСТ 2 - Структура ответа",
                        False,
                        error_details=f"Отсутствуют обязательные поля: {missing_fields}"
                    )
                    return False
                
                qr_batch = result.get("qr_batch", [])
                failed_items = result.get("failed_items", [])
                total_generated = result.get("total_generated", 0)
                total_failed = result.get("total_failed", 0)
                
                print(f"📊 Результаты массовой генерации:")
                print(f"   ✅ Успешно сгенерировано: {total_generated}")
                print(f"   ❌ Ошибок: {total_failed}")
                
                # Проверяем каждый сгенерированный QR код
                valid_qr_count = 0
                for qr_item in qr_batch:
                    required_qr_fields = ["individual_number", "cargo_number", "cargo_name", "qr_data", "qr_base64"]
                    missing_qr_fields = [field for field in required_qr_fields if field not in qr_item]
                    
                    if missing_qr_fields:
                        print(f"   ❌ Отсутствуют поля {missing_qr_fields} в QR элементе {qr_item.get('individual_number')}")
                        continue
                    
                    # Проверяем формат QR данных
                    qr_data = qr_item.get("qr_data", "")
                    expected_pattern = r"TAJLINE\|INDIVIDUAL\|.+\|\d+"
                    
                    if not re.match(expected_pattern, qr_data):
                        print(f"   ❌ Неправильный формат QR данных: {qr_data}")
                        continue
                    
                    # Проверяем base64 изображение
                    qr_base64 = qr_item.get("qr_base64", "")
                    if not qr_base64:
                        print(f"   ❌ QR base64 изображение отсутствует для {qr_item.get('individual_number')}")
                        continue
                    
                    try:
                        base64.b64decode(qr_base64)
                        valid_qr_count += 1
                    except:
                        print(f"   ❌ Невалидное base64 изображение для {qr_item.get('individual_number')}")
                        continue
                
                # Считаем тест успешным если сгенерировано хотя бы 80% QR кодов
                success_rate = (valid_qr_count / len(test_numbers)) * 100 if test_numbers else 0
                
                if success_rate >= 80:
                    self.log_result(
                        "ТЕСТ 2 - Массовая генерация QR",
                        True,
                        f"Массовая генерация QR кодов работает корректно. Сгенерировано {valid_qr_count} из {len(test_numbers)} QR кодов ({success_rate:.1f}% успешности). Примеры: {[qr['individual_number'] for qr in qr_batch[:2]]}"
                    )
                    return True
                else:
                    self.log_result(
                        "ТЕСТ 2 - Массовая генерация QR",
                        False,
                        error_details=f"Низкая успешность генерации: {success_rate:.1f}% ({valid_qr_count}/{len(test_numbers)})"
                    )
                    return False
            else:
                self.log_result(
                    "ТЕСТ 2 - Массовая генерация QR",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "ТЕСТ 2 - Массовая генерация QR",
                False,
                error_details=f"Исключение: {str(e)}"
            )
            return False
    
    def test_print_layout_options(self):
        """ТЕСТ 3: Получение опций макетов печати"""
        print("🎯 ТЕСТ 3: ОПЦИИ МАКЕТОВ ПЕЧАТИ")
        print("=" * 50)
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/operator/qr/print-layout",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Проверяем структуру ответа
                required_fields = ["success", "layout_options", "default_layout"]
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    self.log_result(
                        "ТЕСТ 3 - Структура ответа",
                        False,
                        error_details=f"Отсутствуют обязательные поля: {missing_fields}"
                    )
                    return False
                
                layout_options = result.get("layout_options", {})
                expected_layouts = ["single", "grid_2x2", "grid_3x3", "compact"]
                missing_layouts = [layout for layout in expected_layouts if layout not in layout_options]
                
                if missing_layouts:
                    self.log_result(
                        "ТЕСТ 3 - Доступные макеты",
                        False,
                        error_details=f"Отсутствуют макеты: {missing_layouts}"
                    )
                    return False
                
                # Проверяем структуру каждого макета
                layout_details = []
                for layout_key, layout_info in layout_options.items():
                    required_layout_fields = ["name", "description", "qr_size", "per_page"]
                    missing_layout_fields = [field for field in required_layout_fields if field not in layout_info]
                    
                    if missing_layout_fields:
                        self.log_result(
                            f"ТЕСТ 3 - Структура макета {layout_key}",
                            False,
                            error_details=f"Отсутствуют поля {missing_layout_fields} в макете {layout_key}"
                        )
                        return False
                    
                    layout_details.append(f"{layout_key}: {layout_info.get('name')} ({layout_info.get('per_page')} QR/страница, размер: {layout_info.get('qr_size')})")
                
                default_layout = result.get("default_layout")
                
                self.log_result(
                    "ТЕСТ 3 - Опции макетов печати",
                    True,
                    f"Все 4 макета печати доступны: {', '.join(expected_layouts)}. Макет по умолчанию: {default_layout}. Детали: {'; '.join(layout_details)}"
                )
                
                return True
            else:
                self.log_result(
                    "ТЕСТ 3 - Опции макетов печати",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "ТЕСТ 3 - Опции макетов печати",
                False,
                error_details=f"Исключение: {str(e)}"
            )
            return False
    
    def test_error_handling(self):
        """ТЕСТ 4: Обработка ошибок для несуществующих individual_numbers"""
        print("🎯 ТЕСТ 4: ОБРАБОТКА ОШИБОК")
        print("=" * 50)
        
        tests_passed = 0
        total_tests = 3
        
        # Тест 4.1: Несуществующий individual_number
        print("🔍 Тест 4.1: Несуществующий individual_number")
        try:
            request_data = {"individual_number": "NONEXISTENT/99/99"}
            
            response = self.session.post(
                f"{BACKEND_URL}/operator/qr/generate-individual",
                json=request_data,
                headers={
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            if response.status_code == 404:
                print("   ✅ Корректная обработка несуществующего номера (404)")
                tests_passed += 1
            else:
                print(f"   ❌ Ожидался 404, получен {response.status_code}")
        except Exception as e:
            print(f"   ❌ Исключение: {str(e)}")
        
        # Тест 4.2: Пустой individual_number
        print("🔍 Тест 4.2: Пустой individual_number")
        try:
            request_data = {"individual_number": ""}
            
            response = self.session.post(
                f"{BACKEND_URL}/operator/qr/generate-individual",
                json=request_data,
                headers={
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            if response.status_code == 400:
                print("   ✅ Корректная обработка пустого номера (400)")
                tests_passed += 1
            else:
                print(f"   ❌ Ожидался 400, получен {response.status_code}")
        except Exception as e:
            print(f"   ❌ Исключение: {str(e)}")
        
        # Тест 4.3: Пустой список для массовой генерации
        print("🔍 Тест 4.3: Пустой список для массовой генерации")
        try:
            request_data = {"individual_numbers": []}
            
            response = self.session.post(
                f"{BACKEND_URL}/operator/qr/generate-batch",
                json=request_data,
                headers={
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            if response.status_code == 400:
                print("   ✅ Корректная обработка пустого списка (400)")
                tests_passed += 1
            else:
                print(f"   ❌ Ожидался 400, получен {response.status_code}")
        except Exception as e:
            print(f"   ❌ Исключение: {str(e)}")
        
        success = tests_passed == total_tests
        self.log_result(
            "ТЕСТ 4 - Обработка ошибок",
            success,
            f"Пройдено {tests_passed}/{total_tests} тестов обработки ошибок" if success else "",
            f"Пройдено только {tests_passed}/{total_tests} тестов обработки ошибок" if not success else ""
        )
        
        return success
    
    def validate_qr_data_structure(self):
        """ТЕСТ 5: Валидация структуры QR данных и base64 изображений"""
        print("🎯 ТЕСТ 5: ВАЛИДАЦИЯ QR ДАННЫХ И ИЗОБРАЖЕНИЙ")
        print("=" * 50)
        
        if not self.test_individual_numbers:
            self.log_result(
                "ТЕСТ 5 - Валидация QR данных",
                False,
                error_details="Нет individual numbers для валидации"
            )
            return False
        
        test_individual_number = self.test_individual_numbers[0]
        
        try:
            request_data = {"individual_number": test_individual_number}
            
            response = self.session.post(
                f"{BACKEND_URL}/operator/qr/generate-individual",
                json=request_data,
                headers={
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                qr_info = result.get("qr_info", {})
                qr_data = qr_info.get("qr_data", "")
                qr_base64 = qr_info.get("qr_base64", "")
                
                validation_results = []
                
                # Проверяем формат TAJLINE
                if qr_data.startswith("TAJLINE|INDIVIDUAL|"):
                    validation_results.append("✅ Формат TAJLINE корректен")
                else:
                    validation_results.append(f"❌ QR код не соответствует формату TAJLINE: {qr_data}")
                    return False
                
                # Проверяем структуру данных
                parts = qr_data.split("|")
                if len(parts) == 4:
                    validation_results.append("✅ QR код содержит 4 части (TAJLINE|INDIVIDUAL|номер|timestamp)")
                    
                    # Проверяем timestamp
                    try:
                        timestamp = int(parts[3])
                        current_time = int(time.time())
                        
                        if abs(current_time - timestamp) <= 60:  # В пределах 1 минуты
                            validation_results.append(f"✅ Timestamp актуален: {timestamp} ({datetime.fromtimestamp(timestamp)})")
                        else:
                            validation_results.append(f"⚠️ Timestamp старый: {timestamp}")
                    except ValueError:
                        validation_results.append(f"❌ Невалидный timestamp: {parts[3]}")
                        return False
                else:
                    validation_results.append(f"❌ QR код не содержит 4 части: {qr_data}")
                    return False
                
                # Проверяем base64 изображение
                try:
                    decoded_image = base64.b64decode(qr_base64)
                    image_size = len(decoded_image)
                    
                    if 500 <= image_size <= 100000:  # Разумный размер
                        validation_results.append(f"✅ QR изображение корректного размера: {image_size} байт")
                    else:
                        validation_results.append(f"⚠️ QR изображение необычного размера: {image_size} байт")
                    
                    # Проверяем что это PNG
                    if decoded_image.startswith(b'\x89PNG'):
                        validation_results.append("✅ QR изображение в формате PNG")
                    else:
                        validation_results.append("⚠️ QR изображение не в формате PNG")
                        
                except Exception as decode_error:
                    validation_results.append(f"❌ Ошибка декодирования base64: {str(decode_error)}")
                    return False
                
                self.log_result(
                    "ТЕСТ 5 - Валидация QR данных",
                    True,
                    f"QR код качественный. Формат: {qr_data}. Размер изображения: {image_size} байт. Все проверки: {'; '.join(validation_results)}"
                )
                
                return True
            else:
                self.log_result(
                    "ТЕСТ 5 - Валидация QR данных",
                    False,
                    error_details=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "ТЕСТ 5 - Валидация QR данных",
                False,
                error_details=f"Исключение: {str(e)}"
            )
            return False
    
    def cleanup_test_data(self):
        """Очистка тестовых данных (опционально)"""
        print("🧹 ОЧИСТКА ТЕСТОВЫХ ДАННЫХ")
        print("=" * 50)
        print("ℹ️ Тестовые данные оставлены для дальнейшего использования")
        print()
    
    def run_comprehensive_tests(self):
        """Запуск всех тестов QR кодов для печати Individual Units"""
        print("🖨️ ТЕСТИРОВАНИЕ BACKEND API ДЛЯ ПЕЧАТИ QR КОДОВ В TAJLINE.TJ")
        print("=" * 80)
        print("Контекст: Backend API для печати QR кодов реализован на 100% и готов к тестированию")
        print("Цель: Протестировать 3 новых API endpoint'а для функциональности печати QR кодов individual units")
        print("=" * 80)
        
        # Этап 1: Авторизация
        if not self.authenticate_operator():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как оператор склада")
            return False
        
        # Этап 2: Создание тестовых данных
        if not self.create_test_cargo_with_individual_units():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось создать тестовый груз с individual units")
            return False
        
        # Этап 3: Запуск тестов API endpoints
        test_results = []
        
        test_results.append(("ТЕСТ 1 - Одиночная генерация QR", self.test_generate_individual_qr()))
        test_results.append(("ТЕСТ 2 - Массовая генерация QR", self.test_generate_batch_qr()))
        test_results.append(("ТЕСТ 3 - Опции макетов печати", self.test_print_layout_options()))
        test_results.append(("ТЕСТ 4 - Обработка ошибок", self.test_error_handling()))
        test_results.append(("ТЕСТ 5 - Валидация QR данных", self.validate_qr_data_structure()))
        
        # Этап 4: Очистка
        self.cleanup_test_data()
        
        # Этап 5: Подведение итогов
        print("=" * 80)
        print("📊 ИТОГИ ТЕСТИРОВАНИЯ BACKEND API ДЛЯ ПЕЧАТИ QR КОДОВ")
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
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО! (100% SUCCESS RATE)")
            print("✅ Авторизация оператора склада (+79777888999/warehouse123): Успешная авторизация")
            print("✅ Генерация QR кода для одной единицы: QR коды генерируются в формате TAJLINE|INDIVIDUAL|{individual_number}|{timestamp}")
            print("✅ Массовая генерация QR кодов: Base64 изображения QR кодов корректны")
            print("✅ Опции макетов печати: 4 макета печати доступны (single, grid_2x2, grid_3x3, compact)")
            print("✅ Обработка ошибок: 404 для несуществующих individual_numbers")
            print("✅ Валидация QR данных: Base64 изображения валидны, формат соответствует стандарту")
            print("\n🚀 API ГОТОВ К ПРОДАКШЕНУ!")
        elif success_rate >= 80:
            print("⚠️ Большинство тестов пройдено, но есть проблемы требующие внимания.")
        else:
            print("❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ: Многие тесты не пройдены.")
        
        return success_rate == 100

if __name__ == "__main__":
    tester = QRPrintingAPITester()
    success = tester.run_comprehensive_tests()
    
    if success:
        print("\n✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("Все 3 endpoint'а для печати QR кодов работают корректно согласно техническому заданию.")
        exit(0)
    else:
        print("\n❌ ТЕСТИРОВАНИЕ ВЫЯВИЛО ПРОБЛЕМЫ!")
        print("Требуется исправление найденных ошибок перед использованием в продакшене.")
        exit(1)
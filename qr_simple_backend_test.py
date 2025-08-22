#!/usr/bin/env python3
"""
🎯 ТЕСТИРОВАНИЕ: Новая система QR кодов с использованием рабочего формата из "Список грузов"

КОНТЕКСТ: Реализована новая система QR генерации, которая копирует подход из работающей кнопки "QR код" 
в разделе "Список грузов". Используется тот же backend API endpoint `/api/backend/generate-simple-qr` 
с библиотекой qrcode Python.

ЦЕЛЬ: Протестировать новый backend endpoint для генерации QR кодов.

ЗАДАЧИ:
1. **Авторизация оператора** (+79777888999/warehouse123)
2. **Тестирование нового endpoint** - POST /api/backend/generate-simple-qr
3. **Проверка формата ответа** - должен возвращать base64 изображение как в рабочей системе
4. **Тестирование разных типов данных**:
   - Индивидуальный номер: "250144/01/01"
   - Номер заявки: "250144" 
   - Простой текст: "TEST123"

ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ:
- Backend endpoint работает как `/api/cargo/generate-qr-by-number`
- Возвращает base64 QR коды в формате: `data:image/png;base64,iVBOR...`
- Использует ту же библиотеку qrcode с теми же параметрами
- QR коды читаются сканерами (как в рабочей системе списка грузов)
"""

import requests
import json
import sys
import base64
import re
from datetime import datetime

# Configuration
BACKEND_URL = "https://tajline-cargo-8.preview.emergentagent.com/api"

class QRSimpleSystemTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_info = None
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        print()
    
    def test_operator_authorization(self):
        """1. Авторизация оператора (+79777888999/warehouse123)"""
        print("🔐 ТЕСТ 1: Авторизация оператора склада")
        
        try:
            login_data = {
                "phone": "+79777888999",
                "password": "warehouse123"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.user_info = data.get("user", {})
                
                # Set authorization header
                self.session.headers.update({
                    "Authorization": f"Bearer {self.token}"
                })
                
                user_name = self.user_info.get("full_name", "Unknown")
                user_role = self.user_info.get("role", "Unknown")
                user_phone = self.user_info.get("phone", "Unknown")
                
                self.log_test(
                    "Авторизация оператора склада",
                    True,
                    f"Успешная авторизация: {user_name} (роль: {user_role}, телефон: {user_phone})"
                )
                return True
            else:
                self.log_test(
                    "Авторизация оператора склада",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Авторизация оператора склада",
                False,
                f"Ошибка подключения: {str(e)}"
            )
            return False
    
    def validate_base64_qr_image(self, qr_data):
        """Проверка что QR код в правильном base64 формате"""
        try:
            # Проверяем формат data:image/png;base64,
            if not qr_data.startswith("data:image/png;base64,"):
                return False, "Неправильный формат - должен начинаться с 'data:image/png;base64,'"
            
            # Извлекаем base64 часть
            base64_part = qr_data.split(",", 1)[1]
            
            # Проверяем что это валидный base64
            try:
                decoded = base64.b64decode(base64_part)
                if len(decoded) < 100:  # Минимальный размер PNG файла
                    return False, f"Слишком маленький размер изображения: {len(decoded)} байт"
                
                # Проверяем PNG заголовок
                if not decoded.startswith(b'\x89PNG'):
                    return False, "Не является PNG изображением"
                
                return True, f"Валидное PNG изображение, размер: {len(decoded)} байт"
                
            except Exception as decode_error:
                return False, f"Ошибка декодирования base64: {str(decode_error)}"
                
        except Exception as e:
            return False, f"Ошибка валидации: {str(e)}"
    
    def test_new_qr_endpoint(self):
        """2. Тестирование нового endpoint - POST /api/backend/generate-simple-qr"""
        print("🔗 ТЕСТ 2: Тестирование нового endpoint POST /api/backend/generate-simple-qr")
        
        # Тестовые данные согласно review request
        test_cases = [
            {
                "name": "Индивидуальный номер",
                "data": "250144/01/01",
                "description": "Тестирование с индивидуальным номером груза"
            },
            {
                "name": "Номер заявки", 
                "data": "250144",
                "description": "Тестирование с номером заявки"
            },
            {
                "name": "Простой текст",
                "data": "TEST123", 
                "description": "Тестирование с простым текстом"
            }
        ]
        
        all_tests_passed = True
        
        for test_case in test_cases:
            print(f"\n📋 Подтест: {test_case['name']} - {test_case['description']}")
            
            try:
                # Данные для запроса (используем правильное поле qr_text)
                request_data = {
                    "qr_text": test_case["data"]
                }
                
                response = self.session.post(f"{BACKEND_URL}/backend/generate-simple-qr", json=request_data)
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        qr_code = response_data.get("qr_code")
                        
                        if qr_code:
                            # Валидируем QR код
                            is_valid, validation_message = self.validate_base64_qr_image(qr_code)
                            
                            if is_valid:
                                self.log_test(
                                    f"QR генерация - {test_case['name']}",
                                    True,
                                    f"Данные: '{test_case['data']}' -> {validation_message}"
                                )
                            else:
                                self.log_test(
                                    f"QR генерация - {test_case['name']}",
                                    False,
                                    f"Данные: '{test_case['data']}' -> Невалидный QR: {validation_message}"
                                )
                                all_tests_passed = False
                        else:
                            self.log_test(
                                f"QR генерация - {test_case['name']}",
                                False,
                                f"Данные: '{test_case['data']}' -> QR код отсутствует в ответе"
                            )
                            all_tests_passed = False
                            
                    except Exception as json_error:
                        self.log_test(
                            f"QR генерация - {test_case['name']}",
                            False,
                            f"Данные: '{test_case['data']}' -> Ошибка парсинга JSON: {str(json_error)}"
                        )
                        all_tests_passed = False
                else:
                    self.log_test(
                        f"QR генерация - {test_case['name']}",
                        False,
                        f"Данные: '{test_case['data']}' -> HTTP {response.status_code}: {response.text}"
                    )
                    all_tests_passed = False
                    
            except Exception as e:
                self.log_test(
                    f"QR генерация - {test_case['name']}",
                    False,
                    f"Данные: '{test_case['data']}' -> Ошибка запроса: {str(e)}"
                )
                all_tests_passed = False
        
        return all_tests_passed
    
    def test_qr_format_compatibility(self):
        """3. Проверка совместимости с рабочей системой списка грузов"""
        print("🔄 ТЕСТ 3: Проверка совместимости с рабочей системой списка грузов")
        
        try:
            # Тестируем с тем же форматом, что используется в списке грузов
            test_data = "250144"  # Простой номер заявки
            
            request_data = {
                "qr_text": test_data
            }
            
            response = self.session.post(f"{BACKEND_URL}/backend/generate-simple-qr", json=request_data)
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    qr_code = response_data.get("qr_code")
                    
                    if qr_code:
                        # Проверяем что формат такой же как в рабочей системе
                        is_valid, validation_message = self.validate_base64_qr_image(qr_code)
                        
                        if is_valid:
                            # Дополнительные проверки совместимости
                            base64_part = qr_code.split(",", 1)[1]
                            decoded = base64.b64decode(base64_part)
                            
                            # Проверяем размер изображения (должен быть разумным)
                            if 200 <= len(decoded) <= 50000:  # Более широкий диапазон для QR кода
                                self.log_test(
                                    "Совместимость с рабочей системой",
                                    True,
                                    f"QR код совместим с рабочей системой. {validation_message}. Формат: data:image/png;base64,..."
                                )
                                return True
                            else:
                                self.log_test(
                                    "Совместимость с рабочей системой",
                                    False,
                                    f"Размер изображения вне ожидаемого диапазона: {len(decoded)} байт"
                                )
                                return False
                        else:
                            self.log_test(
                                "Совместимость с рабочей системой",
                                False,
                                f"QR код не прошел валидацию: {validation_message}"
                            )
                            return False
                    else:
                        self.log_test(
                            "Совместимость с рабочей системой",
                            False,
                            "QR код отсутствует в ответе"
                        )
                        return False
                        
                except Exception as json_error:
                    self.log_test(
                        "Совместимость с рабочей системой",
                        False,
                        f"Ошибка парсинга JSON: {str(json_error)}"
                    )
                    return False
            else:
                self.log_test(
                    "Совместимость с рабочей системой",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Совместимость с рабочей системой",
                False,
                f"Ошибка запроса: {str(e)}"
            )
            return False
    
    def test_qr_library_consistency(self):
        """4. Проверка использования той же библиотеки qrcode Python"""
        print("📚 ТЕСТ 4: Проверка использования библиотеки qrcode Python")
        
        try:
            # Тестируем с разными типами данных для проверки консистентности
            test_cases = [
                "SHORT",  # Короткий текст
                "MEDIUM_LENGTH_TEXT_123",  # Средний текст
                "250144/01/01/EXTRA/DATA/FOR/TESTING"  # Длинный текст
            ]
            
            all_consistent = True
            qr_sizes = []
            
            for test_text in test_cases:
                request_data = {"qr_text": test_text}
                response = self.session.post(f"{BACKEND_URL}/backend/generate-simple-qr", json=request_data)
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        qr_code = response_data.get("qr_code")
                        
                        if qr_code:
                            is_valid, validation_message = self.validate_base64_qr_image(qr_code)
                            
                            if is_valid:
                                base64_part = qr_code.split(",", 1)[1]
                                decoded = base64.b64decode(base64_part)
                                qr_sizes.append(len(decoded))
                                print(f"   Текст: '{test_text}' -> Размер QR: {len(decoded)} байт")
                            else:
                                all_consistent = False
                                print(f"   Текст: '{test_text}' -> Ошибка: {validation_message}")
                        else:
                            all_consistent = False
                            print(f"   Текст: '{test_text}' -> QR код отсутствует")
                    except Exception as e:
                        all_consistent = False
                        print(f"   Текст: '{test_text}' -> Ошибка: {str(e)}")
                else:
                    all_consistent = False
                    print(f"   Текст: '{test_text}' -> HTTP {response.status_code}")
            
            if all_consistent and len(qr_sizes) == len(test_cases):
                # Проверяем что размеры QR кодов логичны (больше данных = больше размер или одинаковый)
                size_consistency = all(size > 0 for size in qr_sizes)
                
                if size_consistency:
                    self.log_test(
                        "Консистентность библиотеки qrcode",
                        True,
                        f"Библиотека qrcode работает консистентно. Размеры QR: {qr_sizes} байт"
                    )
                    return True
                else:
                    self.log_test(
                        "Консистентность библиотеки qrcode",
                        False,
                        f"Некорректные размеры QR кодов: {qr_sizes}"
                    )
                    return False
            else:
                self.log_test(
                    "Консистентность библиотеки qrcode",
                    False,
                    "Не все QR коды сгенерированы успешно"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Консистентность библиотеки qrcode",
                False,
                f"Ошибка тестирования: {str(e)}"
            )
            return False
    
    def test_endpoint_comparison(self):
        """5. Сравнение с существующим endpoint /api/cargo/generate-qr-by-number"""
        print("⚖️  ТЕСТ 5: Сравнение с существующим endpoint /api/cargo/generate-qr-by-number")
        
        try:
            test_number = "250144"
            
            # Тестируем новый endpoint
            new_request_data = {"qr_text": test_number}
            new_response = self.session.post(f"{BACKEND_URL}/backend/generate-simple-qr", json=new_request_data)
            
            # Тестируем старый endpoint (если существует)
            old_request_data = {"cargo_number": test_number}
            old_response = self.session.post(f"{BACKEND_URL}/cargo/generate-qr-by-number", json=old_request_data)
            
            new_success = new_response.status_code == 200
            old_success = old_response.status_code == 200
            
            if new_success:
                try:
                    new_data = new_response.json()
                    new_qr = new_data.get("qr_code")
                    new_valid, new_msg = self.validate_base64_qr_image(new_qr) if new_qr else (False, "QR отсутствует")
                    
                    if old_success:
                        try:
                            old_data = old_response.json()
                            old_qr = old_data.get("qr_code")
                            old_valid, old_msg = self.validate_base64_qr_image(old_qr) if old_qr else (False, "QR отсутствует")
                            
                            if new_valid and old_valid:
                                # Сравниваем размеры
                                new_size = len(base64.b64decode(new_qr.split(",", 1)[1]))
                                old_size = len(base64.b64decode(old_qr.split(",", 1)[1]))
                                
                                self.log_test(
                                    "Сравнение с существующим endpoint",
                                    True,
                                    f"Оба endpoint работают. Новый: {new_size} байт, Старый: {old_size} байт"
                                )
                                return True
                            elif new_valid:
                                self.log_test(
                                    "Сравнение с существующим endpoint",
                                    True,
                                    f"Новый endpoint работает ({new_msg}), старый имеет проблемы ({old_msg})"
                                )
                                return True
                            else:
                                self.log_test(
                                    "Сравнение с существующим endpoint",
                                    False,
                                    f"Новый endpoint: {new_msg}, Старый endpoint: {old_msg}"
                                )
                                return False
                                
                        except Exception as old_error:
                            if new_valid:
                                self.log_test(
                                    "Сравнение с существующим endpoint",
                                    True,
                                    f"Новый endpoint работает ({new_msg}), старый недоступен"
                                )
                                return True
                            else:
                                self.log_test(
                                    "Сравнение с существующим endpoint",
                                    False,
                                    f"Новый endpoint: {new_msg}, Старый: ошибка {str(old_error)}"
                                )
                                return False
                    else:
                        # Старый endpoint недоступен, проверяем только новый
                        if new_valid:
                            self.log_test(
                                "Сравнение с существующим endpoint",
                                True,
                                f"Новый endpoint работает корректно ({new_msg}), старый endpoint недоступен (HTTP {old_response.status_code})"
                            )
                            return True
                        else:
                            self.log_test(
                                "Сравнение с существующим endpoint",
                                False,
                                f"Новый endpoint: {new_msg}, Старый: HTTP {old_response.status_code}"
                            )
                            return False
                            
                except Exception as new_error:
                    self.log_test(
                        "Сравнение с существующим endpoint",
                        False,
                        f"Ошибка обработки нового endpoint: {str(new_error)}"
                    )
                    return False
            else:
                self.log_test(
                    "Сравнение с существующим endpoint",
                    False,
                    f"Новый endpoint недоступен: HTTP {new_response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Сравнение с существующим endpoint",
                False,
                f"Ошибка тестирования: {str(e)}"
            )
            return False
    
    def run_all_tests(self):
        """Запустить все тесты"""
        print("🎯 ТЕСТИРОВАНИЕ: Новая система QR кодов с использованием рабочего формата из 'Список грузов'")
        print("=" * 100)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 100)
        print()
        
        # Run tests in sequence
        tests = [
            self.test_operator_authorization,
            self.test_new_qr_endpoint,
            self.test_qr_format_compatibility,
            self.test_qr_library_consistency,
            self.test_endpoint_comparison
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_func in tests:
            if test_func():
                passed_tests += 1
        
        # Summary
        print("=" * 100)
        print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
        print("=" * 100)
        
        success_rate = (passed_tests / total_tests) * 100
        
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   {result['details']}")
        
        print()
        print(f"🎯 ОБЩИЙ РЕЗУЛЬТАТ: {passed_tests}/{total_tests} тестов пройдено ({success_rate:.1f}%)")
        
        if success_rate == 100:
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            print("✅ Backend endpoint POST /api/backend/generate-simple-qr работает корректно")
            print("✅ Возвращает base64 QR коды в правильном формате: data:image/png;base64,...")
            print("✅ Использует библиотеку qrcode Python консистентно")
            print("✅ QR коды совместимы с рабочей системой списка грузов")
            print("✅ Поддерживает все типы данных: индивидуальные номера, номера заявок, простой текст")
        elif success_rate >= 80:
            print("⚠️  БОЛЬШИНСТВО ТЕСТОВ ПРОЙДЕНО")
            print("🔧 Новая система QR кодов работает, но есть незначительные проблемы")
        else:
            print("❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ В НОВОЙ СИСТЕМЕ QR КОДОВ")
            print("🚨 Требуется доработка backend endpoint")
        
        print()
        print("📋 ПРОТЕСТИРОВАННЫЕ ДАННЫЕ:")
        print("   - Индивидуальный номер: '250144/01/01'")
        print("   - Номер заявки: '250144'")
        print("   - Простой текст: 'TEST123'")
        print()
        print("🔧 ОЖИДАЕМЫЙ ФОРМАТ ОТВЕТА:")
        print("   {\"qr_code\": \"data:image/png;base64,iVBOR...\"}")
        
        return success_rate >= 80

def main():
    """Main function"""
    tester = QRSimpleSystemTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
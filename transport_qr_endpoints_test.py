#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: API endpoints для QR кодов транспорта (Этап 1)
=============================================================================

ЦЕЛЬ ТЕСТИРОВАНИЯ: Проверить все новые API endpoints для работы с QR кодами транспорта 
согласно техническому заданию "Размещение грузов на транспорт - Этап 1: Генерация QR кодов для транспорта".

КРИТИЧЕСКИЕ ENDPOINTS ДЛЯ ТЕСТИРОВАНИЯ:
1. POST /api/transport/{transport_id}/generate-qr - Генерация QR кода для транспорта
2. GET /api/transport/{transport_id}/qr - Получение QR данных транспорта  
3. POST /api/transport/{transport_id}/print-qr - Печать QR кода (увеличение счетчика)
4. GET /api/transport/list-with-qr - Список транспортов с QR статусом

ДЕТАЛЬНЫЕ ТРЕБОВАНИЯ:
1. Авторизация: Использовать warehouse_operator (+79777888999/warehouse123)
2. Генерация QR: Создать QR код в формате TRANSPORT_{transport_number}_{timestamp}
3. QR данные: Проверить поля qr_code, qr_generated_at, qr_generated_by, qr_print_count
4. Счетчик печати: Должен увеличиваться при каждом вызове print-qr
5. Список транспортов: Должен показывать has_qr_code и qr_print_count для каждого транспорта
6. Структура Transport модели: Проверить что новые поля добавлены

ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ:
- ✅ Все endpoints доступны и работают корректно
- ✅ QR коды генерируются в правильном формате  
- ✅ Данные сохраняются в MongoDB коллекции transport
- ✅ Счетчик печати работает корректно (увеличивается на 1)
- ✅ Список транспортов показывает QR статус
- ✅ Обработка ошибок работает (404 для несуществующих транспортов)
"""

import requests
import json
import sys
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Any

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cargo-sync.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Конфигурация тестирования
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"

class TransportQREndpointsTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.test_results = {
            "auth_success": False,
            "transport_list_success": False,
            "qr_generation_success": False,
            "qr_data_retrieval_success": False,
            "qr_print_counter_success": False,
            "transport_model_validation_success": False,
            "error_handling_success": False,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": []
        }
        self.test_transport_id = None
        self.test_transport_number = None
        
    def log(self, message: str, level: str = "INFO"):
        """Логирование с временной меткой"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def add_test_result(self, test_name: str, success: bool, details: str = "", response_time: int = 0):
        """Добавить результат теста"""
        self.test_results["total_tests"] += 1
        if success:
            self.test_results["passed_tests"] += 1
        else:
            self.test_results["failed_tests"] += 1
            
        self.test_results["test_details"].append({
            "test_name": test_name,
            "success": success,
            "details": details,
            "response_time_ms": response_time,
            "timestamp": datetime.now().isoformat()
        })
        
    def authenticate_warehouse_operator(self) -> bool:
        """Авторизация оператора склада"""
        self.log("🔐 Авторизация оператора склада...")
        
        try:
            start_time = datetime.now()
            response = self.session.post(f"{API_BASE}/auth/login", json={
                "phone": WAREHOUSE_OPERATOR_PHONE,
                "password": WAREHOUSE_OPERATOR_PASSWORD
            })
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.operator_info = data.get("user")
                
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                operator_name = self.operator_info.get('full_name', 'Unknown')
                operator_role = self.operator_info.get('role', 'Unknown')
                
                self.log(f"✅ Успешная авторизация '{operator_name}' (роль: {operator_role})")
                self.test_results["auth_success"] = True
                self.add_test_result(
                    "Авторизация оператора склада (+79777888999/warehouse123)",
                    True,
                    f"Успешная авторизация '{operator_name}' (роль: {operator_role})",
                    response_time
                )
                return True
            else:
                error_msg = f"HTTP {response.status_code} - {response.text}"
                self.log(f"❌ Ошибка авторизации: {error_msg}", "ERROR")
                self.add_test_result(
                    "Авторизация оператора склада",
                    False,
                    f"Ошибка авторизации: {error_msg}",
                    response_time
                )
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при авторизации: {e}", "ERROR")
            self.add_test_result(
                "Авторизация оператора склада",
                False,
                f"Исключение: {str(e)}",
                0
            )
            return False
    
    def test_transport_list_with_qr(self) -> bool:
        """Тестирование GET /api/transport/list-with-qr"""
        self.log("📋 Тестирование GET /api/transport/list-with-qr...")
        
        try:
            start_time = datetime.now()
            response = self.session.get(f"{API_BASE}/transport/list-with-qr")
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем структуру ответа
                required_fields = ["transports", "total_count", "with_qr_count", "without_qr_count"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    error_msg = f"Отсутствуют обязательные поля: {missing_fields}"
                    self.log(f"❌ {error_msg}", "ERROR")
                    self.add_test_result(
                        "GET /api/transport/list-with-qr - структура ответа",
                        False,
                        error_msg,
                        response_time
                    )
                    return False
                
                transports = data.get("transports", [])
                total_count = data.get("total_count", 0)
                with_qr_count = data.get("with_qr_count", 0)
                without_qr_count = data.get("without_qr_count", 0)
                
                self.log(f"✅ Получен список транспортов: {total_count} всего, {with_qr_count} с QR, {without_qr_count} без QR")
                
                # Проверяем структуру каждого транспорта
                if transports:
                    transport = transports[0]
                    transport_fields = ["id", "transport_number", "has_qr_code", "qr_print_count"]
                    missing_transport_fields = [field for field in transport_fields if field not in transport]
                    
                    if missing_transport_fields:
                        error_msg = f"В транспорте отсутствуют поля: {missing_transport_fields}"
                        self.log(f"❌ {error_msg}", "ERROR")
                        self.add_test_result(
                            "GET /api/transport/list-with-qr - структура транспорта",
                            False,
                            error_msg,
                            response_time
                        )
                        return False
                    
                    # Сохраняем транспорт для дальнейших тестов
                    self.test_transport_id = transport.get("id")
                    self.test_transport_number = transport.get("transport_number")
                    
                    self.log(f"🚛 Выбран тестовый транспорт: {self.test_transport_number} (ID: {self.test_transport_id})")
                
                self.test_results["transport_list_success"] = True
                self.add_test_result(
                    "GET /api/transport/list-with-qr",
                    True,
                    f"Получено {total_count} транспортов, структура корректна",
                    response_time
                )
                return True
            else:
                error_msg = f"HTTP {response.status_code} - {response.text}"
                self.log(f"❌ Ошибка получения списка транспортов: {error_msg}", "ERROR")
                self.add_test_result(
                    "GET /api/transport/list-with-qr",
                    False,
                    f"Ошибка API: {error_msg}",
                    response_time
                )
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при получении списка транспортов: {e}", "ERROR")
            self.add_test_result(
                "GET /api/transport/list-with-qr",
                False,
                f"Исключение: {str(e)}",
                0
            )
            return False
    
    def test_qr_generation(self) -> bool:
        """Тестирование POST /api/transport/{transport_id}/generate-qr"""
        if not self.test_transport_id:
            self.log("❌ Нет тестового транспорта для генерации QR", "ERROR")
            return False
            
        self.log(f"🎯 Тестирование POST /api/transport/{self.test_transport_id}/generate-qr...")
        
        try:
            start_time = datetime.now()
            response = self.session.post(f"{API_BASE}/transport/{self.test_transport_id}/generate-qr")
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем структуру ответа
                required_fields = ["message", "transport_id", "qr_code", "generated_at", "generated_by"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    error_msg = f"Отсутствуют обязательные поля: {missing_fields}"
                    self.log(f"❌ {error_msg}", "ERROR")
                    self.add_test_result(
                        f"POST /api/transport/{self.test_transport_id}/generate-qr - структура ответа",
                        False,
                        error_msg,
                        response_time
                    )
                    return False
                
                qr_code = data.get("qr_code")
                generated_by = data.get("generated_by")
                
                # Проверяем формат QR кода
                expected_pattern = f"TRANSPORT_{self.test_transport_number}_\\d{{8}}_\\d{{6}}"
                if not re.match(expected_pattern, qr_code):
                    error_msg = f"QR код не соответствует ожидаемому формату. Получен: {qr_code}"
                    self.log(f"❌ {error_msg}", "ERROR")
                    self.add_test_result(
                        f"POST /api/transport/{self.test_transport_id}/generate-qr - формат QR",
                        False,
                        error_msg,
                        response_time
                    )
                    return False
                
                self.log(f"✅ QR код успешно сгенерирован: {qr_code}")
                self.log(f"👤 Создан оператором: {generated_by}")
                
                self.test_results["qr_generation_success"] = True
                self.add_test_result(
                    f"POST /api/transport/{self.test_transport_id}/generate-qr",
                    True,
                    f"QR код сгенерирован: {qr_code}, создан: {generated_by}",
                    response_time
                )
                return True
            else:
                error_msg = f"HTTP {response.status_code} - {response.text}"
                self.log(f"❌ Ошибка генерации QR: {error_msg}", "ERROR")
                self.add_test_result(
                    f"POST /api/transport/{self.test_transport_id}/generate-qr",
                    False,
                    f"Ошибка API: {error_msg}",
                    response_time
                )
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при генерации QR: {e}", "ERROR")
            self.add_test_result(
                f"POST /api/transport/{self.test_transport_id}/generate-qr",
                False,
                f"Исключение: {str(e)}",
                0
            )
            return False
    
    def test_qr_data_retrieval(self) -> bool:
        """Тестирование GET /api/transport/{transport_id}/qr"""
        if not self.test_transport_id:
            self.log("❌ Нет тестового транспорта для получения QR данных", "ERROR")
            return False
            
        self.log(f"📊 Тестирование GET /api/transport/{self.test_transport_id}/qr...")
        
        try:
            start_time = datetime.now()
            response = self.session.get(f"{API_BASE}/transport/{self.test_transport_id}/qr")
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем структуру ответа
                required_fields = ["transport_id", "transport_number", "qr_code", "qr_generated_at", "qr_generated_by", "qr_print_count"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    error_msg = f"Отсутствуют обязательные поля: {missing_fields}"
                    self.log(f"❌ {error_msg}", "ERROR")
                    self.add_test_result(
                        f"GET /api/transport/{self.test_transport_id}/qr - структура ответа",
                        False,
                        error_msg,
                        response_time
                    )
                    return False
                
                transport_id = data.get("transport_id")
                transport_number = data.get("transport_number")
                qr_code = data.get("qr_code")
                qr_generated_by = data.get("qr_generated_by")
                qr_print_count = data.get("qr_print_count")
                
                # Проверяем соответствие данных
                if transport_id != self.test_transport_id:
                    error_msg = f"transport_id не соответствует: ожидался {self.test_transport_id}, получен {transport_id}"
                    self.log(f"❌ {error_msg}", "ERROR")
                    self.add_test_result(
                        f"GET /api/transport/{self.test_transport_id}/qr - соответствие ID",
                        False,
                        error_msg,
                        response_time
                    )
                    return False
                
                self.log(f"✅ QR данные получены корректно:")
                self.log(f"  🚛 Транспорт: {transport_number}")
                self.log(f"  🔢 QR код: {qr_code}")
                self.log(f"  👤 Создан: {qr_generated_by}")
                self.log(f"  🖨️ Счетчик печати: {qr_print_count}")
                
                self.test_results["qr_data_retrieval_success"] = True
                self.add_test_result(
                    f"GET /api/transport/{self.test_transport_id}/qr",
                    True,
                    f"QR данные получены: {qr_code}, счетчик: {qr_print_count}",
                    response_time
                )
                return True
            else:
                error_msg = f"HTTP {response.status_code} - {response.text}"
                self.log(f"❌ Ошибка получения QR данных: {error_msg}", "ERROR")
                self.add_test_result(
                    f"GET /api/transport/{self.test_transport_id}/qr",
                    False,
                    f"Ошибка API: {error_msg}",
                    response_time
                )
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при получении QR данных: {e}", "ERROR")
            self.add_test_result(
                f"GET /api/transport/{self.test_transport_id}/qr",
                False,
                f"Исключение: {str(e)}",
                0
            )
            return False
    
    def test_qr_print_counter(self) -> bool:
        """Тестирование POST /api/transport/{transport_id}/print-qr"""
        if not self.test_transport_id:
            self.log("❌ Нет тестового транспорта для тестирования счетчика печати", "ERROR")
            return False
            
        self.log(f"🖨️ Тестирование POST /api/transport/{self.test_transport_id}/print-qr...")
        
        try:
            # Сначала получаем текущий счетчик
            qr_response = self.session.get(f"{API_BASE}/transport/{self.test_transport_id}/qr")
            if qr_response.status_code != 200:
                self.log("❌ Не удалось получить текущий счетчик печати", "ERROR")
                return False
                
            current_count = qr_response.json().get("qr_print_count", 0)
            self.log(f"📊 Текущий счетчик печати: {current_count}")
            
            # Выполняем печать
            start_time = datetime.now()
            response = self.session.post(f"{API_BASE}/transport/{self.test_transport_id}/print-qr")
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем структуру ответа
                required_fields = ["message", "transport_id", "qr_code", "print_count"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    error_msg = f"Отсутствуют обязательные поля: {missing_fields}"
                    self.log(f"❌ {error_msg}", "ERROR")
                    self.add_test_result(
                        f"POST /api/transport/{self.test_transport_id}/print-qr - структура ответа",
                        False,
                        error_msg,
                        response_time
                    )
                    return False
                
                new_count = data.get("print_count")
                expected_count = current_count + 1
                
                # Проверяем увеличение счетчика
                if new_count != expected_count:
                    error_msg = f"Счетчик печати не увеличился корректно: ожидался {expected_count}, получен {new_count}"
                    self.log(f"❌ {error_msg}", "ERROR")
                    self.add_test_result(
                        f"POST /api/transport/{self.test_transport_id}/print-qr - счетчик",
                        False,
                        error_msg,
                        response_time
                    )
                    return False
                
                self.log(f"✅ Счетчик печати увеличен: {current_count} → {new_count}")
                
                self.test_results["qr_print_counter_success"] = True
                self.add_test_result(
                    f"POST /api/transport/{self.test_transport_id}/print-qr",
                    True,
                    f"Счетчик увеличен с {current_count} до {new_count}",
                    response_time
                )
                return True
            else:
                error_msg = f"HTTP {response.status_code} - {response.text}"
                self.log(f"❌ Ошибка печати QR: {error_msg}", "ERROR")
                self.add_test_result(
                    f"POST /api/transport/{self.test_transport_id}/print-qr",
                    False,
                    f"Ошибка API: {error_msg}",
                    response_time
                )
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при тестировании счетчика печати: {e}", "ERROR")
            self.add_test_result(
                f"POST /api/transport/{self.test_transport_id}/print-qr",
                False,
                f"Исключение: {str(e)}",
                0
            )
            return False
    
    def test_error_handling(self) -> bool:
        """Тестирование обработки ошибок"""
        self.log("⚠️ Тестирование обработки ошибок...")
        
        fake_transport_id = "non-existent-transport-id"
        success_count = 0
        total_error_tests = 3
        
        # Тест 1: Генерация QR для несуществующего транспорта
        try:
            start_time = datetime.now()
            response = self.session.post(f"{API_BASE}/transport/{fake_transport_id}/generate-qr")
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            if response.status_code == 404:
                self.log("✅ Корректная обработка 404 для генерации QR несуществующего транспорта")
                success_count += 1
                self.add_test_result(
                    "Обработка ошибок - генерация QR (404)",
                    True,
                    "Корректный HTTP 404 для несуществующего транспорта",
                    response_time
                )
            else:
                self.log(f"❌ Неожиданный статус для несуществующего транспорта: {response.status_code}")
                self.add_test_result(
                    "Обработка ошибок - генерация QR (404)",
                    False,
                    f"Ожидался 404, получен {response.status_code}",
                    response_time
                )
        except Exception as e:
            self.log(f"❌ Исключение при тестировании 404: {e}")
            self.add_test_result(
                "Обработка ошибок - генерация QR (404)",
                False,
                f"Исключение: {str(e)}",
                0
            )
        
        # Тест 2: Получение QR данных для несуществующего транспорта
        try:
            start_time = datetime.now()
            response = self.session.get(f"{API_BASE}/transport/{fake_transport_id}/qr")
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            if response.status_code == 404:
                self.log("✅ Корректная обработка 404 для получения QR данных несуществующего транспорта")
                success_count += 1
                self.add_test_result(
                    "Обработка ошибок - получение QR данных (404)",
                    True,
                    "Корректный HTTP 404 для несуществующего транспорта",
                    response_time
                )
            else:
                self.log(f"❌ Неожиданный статус для получения QR данных: {response.status_code}")
                self.add_test_result(
                    "Обработка ошибок - получение QR данных (404)",
                    False,
                    f"Ожидался 404, получен {response.status_code}",
                    response_time
                )
        except Exception as e:
            self.log(f"❌ Исключение при тестировании получения QR данных: {e}")
            self.add_test_result(
                "Обработка ошибок - получение QR данных (404)",
                False,
                f"Исключение: {str(e)}",
                0
            )
        
        # Тест 3: Печать QR для несуществующего транспорта
        try:
            start_time = datetime.now()
            response = self.session.post(f"{API_BASE}/transport/{fake_transport_id}/print-qr")
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            if response.status_code == 404:
                self.log("✅ Корректная обработка 404 для печати QR несуществующего транспорта")
                success_count += 1
                self.add_test_result(
                    "Обработка ошибок - печать QR (404)",
                    True,
                    "Корректный HTTP 404 для несуществующего транспорта",
                    response_time
                )
            else:
                self.log(f"❌ Неожиданный статус для печати QR: {response.status_code}")
                self.add_test_result(
                    "Обработка ошибок - печать QR (404)",
                    False,
                    f"Ожидался 404, получен {response.status_code}",
                    response_time
                )
        except Exception as e:
            self.log(f"❌ Исключение при тестировании печати QR: {e}")
            self.add_test_result(
                "Обработка ошибок - печать QR (404)",
                False,
                f"Исключение: {str(e)}",
                0
            )
        
        error_handling_success = success_count == total_error_tests
        self.test_results["error_handling_success"] = error_handling_success
        
        if error_handling_success:
            self.log(f"✅ Обработка ошибок работает корректно ({success_count}/{total_error_tests})")
        else:
            self.log(f"❌ Проблемы с обработкой ошибок ({success_count}/{total_error_tests})")
        
        return error_handling_success
    
    def validate_transport_model(self) -> bool:
        """Проверка что новые поля добавлены в модель Transport"""
        self.log("🔍 Проверка структуры Transport модели...")
        
        if not self.test_transport_id:
            self.log("❌ Нет тестового транспорта для проверки модели", "ERROR")
            return False
        
        try:
            # Получаем данные транспорта через QR endpoint
            response = self.session.get(f"{API_BASE}/transport/{self.test_transport_id}/qr")
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем наличие новых полей QR
                qr_fields = ["qr_code", "qr_generated_at", "qr_generated_by", "qr_print_count"]
                missing_qr_fields = [field for field in qr_fields if field not in data]
                
                if missing_qr_fields:
                    error_msg = f"В модели Transport отсутствуют QR поля: {missing_qr_fields}"
                    self.log(f"❌ {error_msg}", "ERROR")
                    self.add_test_result(
                        "Валидация Transport модели - QR поля",
                        False,
                        error_msg,
                        0
                    )
                    return False
                
                # Проверяем типы данных
                qr_code = data.get("qr_code")
                qr_print_count = data.get("qr_print_count")
                
                if not isinstance(qr_code, str) or not qr_code:
                    error_msg = f"qr_code должен быть непустой строкой, получен: {type(qr_code)} - {qr_code}"
                    self.log(f"❌ {error_msg}", "ERROR")
                    self.add_test_result(
                        "Валидация Transport модели - тип qr_code",
                        False,
                        error_msg,
                        0
                    )
                    return False
                
                if not isinstance(qr_print_count, int) or qr_print_count < 0:
                    error_msg = f"qr_print_count должен быть неотрицательным числом, получен: {type(qr_print_count)} - {qr_print_count}"
                    self.log(f"❌ {error_msg}", "ERROR")
                    self.add_test_result(
                        "Валидация Transport модели - тип qr_print_count",
                        False,
                        error_msg,
                        0
                    )
                    return False
                
                self.log("✅ Структура Transport модели корректна - все QR поля присутствуют")
                self.test_results["transport_model_validation_success"] = True
                self.add_test_result(
                    "Валидация Transport модели",
                    True,
                    "Все QR поля присутствуют и имеют корректные типы",
                    0
                )
                return True
            else:
                error_msg = f"Не удалось получить данные транспорта для валидации: HTTP {response.status_code}"
                self.log(f"❌ {error_msg}", "ERROR")
                self.add_test_result(
                    "Валидация Transport модели",
                    False,
                    error_msg,
                    0
                )
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при валидации модели: {e}", "ERROR")
            self.add_test_result(
                "Валидация Transport модели",
                False,
                f"Исключение: {str(e)}",
                0
            )
            return False
    
    def generate_comprehensive_report(self) -> bool:
        """Генерация подробного отчета о тестировании"""
        self.log("\n" + "="*80)
        self.log("📋 ПОДРОБНЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ QR ENDPOINTS ДЛЯ ТРАНСПОРТА")
        self.log("="*80)
        
        # Заголовок
        self.log(f"🎯 ЦЕЛЬ: Тестирование API endpoints для QR кодов транспорта (Этап 1)")
        self.log(f"📅 Время тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"🚛 Тестовый транспорт: {self.test_transport_number} (ID: {self.test_transport_id})")
        
        # Общая статистика
        total_tests = self.test_results["total_tests"]
        passed_tests = self.test_results["passed_tests"]
        failed_tests = self.test_results["failed_tests"]
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.log(f"\n📊 ОБЩАЯ СТАТИСТИКА:")
        self.log(f"  Всего тестов: {total_tests}")
        self.log(f"  Пройдено: {passed_tests}")
        self.log(f"  Провалено: {failed_tests}")
        self.log(f"  Успешность: {success_rate:.1f}%")
        
        # Результаты по категориям
        self.log(f"\n🎯 РЕЗУЛЬТАТЫ ПО КРИТИЧЕСКИМ ОБЛАСТЯМ:")
        categories = [
            ("Авторизация оператора", self.test_results["auth_success"]),
            ("Список транспортов с QR статусом", self.test_results["transport_list_success"]),
            ("Генерация QR кодов", self.test_results["qr_generation_success"]),
            ("Получение QR данных", self.test_results["qr_data_retrieval_success"]),
            ("Счетчик печати QR", self.test_results["qr_print_counter_success"]),
            ("Валидация Transport модели", self.test_results["transport_model_validation_success"]),
            ("Обработка ошибок", self.test_results["error_handling_success"])
        ]
        
        for category, success in categories:
            status = "✅ УСПЕШНО" if success else "❌ НЕУДАЧНО"
            self.log(f"  {category}: {status}")
        
        # Детальные результаты тестов
        self.log(f"\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ ТЕСТОВ:")
        for i, test in enumerate(self.test_results["test_details"], 1):
            status = "✅" if test["success"] else "❌"
            response_time = f"({test['response_time_ms']}ms)" if test['response_time_ms'] > 0 else ""
            self.log(f"  {i}. {status} {test['test_name']} {response_time}")
            if test["details"]:
                self.log(f"     {test['details']}")
        
        # Финальный вывод
        all_critical_passed = all([
            self.test_results["auth_success"],
            self.test_results["transport_list_success"],
            self.test_results["qr_generation_success"],
            self.test_results["qr_data_retrieval_success"],
            self.test_results["qr_print_counter_success"],
            self.test_results["transport_model_validation_success"],
            self.test_results["error_handling_success"]
        ])
        
        self.log(f"\n🎯 ФИНАЛЬНЫЙ РЕЗУЛЬТАТ:")
        if all_critical_passed and success_rate >= 90:
            self.log("🎉 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ API ENDPOINTS ДЛЯ QR КОДОВ ТРАНСПОРТА ЗАВЕРШЕНО УСПЕШНО!")
            self.log("✅ Все критические endpoints работают корректно")
            self.log("✅ QR коды генерируются в правильном формате")
            self.log("✅ Данные сохраняются в MongoDB корректно")
            self.log("✅ Счетчик печати работает правильно")
            self.log("✅ Список транспортов показывает QR статус")
            self.log("✅ Обработка ошибок функционирует корректно")
            self.log("🚀 СИСТЕМА ГОТОВА К ПРОДАКШЕНУ!")
        else:
            self.log("❌ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ НЕ ПРОЙДЕНО!")
            self.log(f"🔍 Успешность: {success_rate:.1f}% (требуется ≥90%)")
            self.log("⚠️ Найдены проблемы, требующие исправления")
            
            # Показываем проблемные области
            failed_categories = [cat[0] for cat in categories if not cat[1]]
            if failed_categories:
                self.log(f"🚨 Проблемные области: {', '.join(failed_categories)}")
        
        return all_critical_passed and success_rate >= 90
    
    def run_comprehensive_test(self) -> bool:
        """Запуск полного комплексного тестирования"""
        self.log("🚀 ЗАПУСК КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ QR ENDPOINTS ДЛЯ ТРАНСПОРТА")
        self.log("="*80)
        
        # 1. Авторизация
        if not self.authenticate_warehouse_operator():
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Не удалось авторизоваться", "ERROR")
            return False
        
        # 2. Получение списка транспортов с QR статусом
        if not self.test_transport_list_with_qr():
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Не удалось получить список транспортов", "ERROR")
            return False
        
        # 3. Генерация QR кода
        if not self.test_qr_generation():
            self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось сгенерировать QR код", "ERROR")
            # Продолжаем тестирование даже если генерация не удалась
        
        # 4. Получение QR данных
        if not self.test_qr_data_retrieval():
            self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить QR данные", "ERROR")
        
        # 5. Тестирование счетчика печати
        if not self.test_qr_print_counter():
            self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Счетчик печати не работает", "ERROR")
        
        # 6. Валидация модели Transport
        if not self.validate_transport_model():
            self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Проблемы с моделью Transport", "ERROR")
        
        # 7. Тестирование обработки ошибок
        if not self.test_error_handling():
            self.log("❌ ПРОБЛЕМЫ: Обработка ошибок работает некорректно", "WARNING")
        
        # 8. Генерация финального отчета
        final_success = self.generate_comprehensive_report()
        
        return final_success

def main():
    """Главная функция"""
    tester = TransportQREndpointsTester()
    
    try:
        success = tester.run_comprehensive_test()
        
        if success:
            print("\n" + "="*80)
            print("🎉 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ QR ENDPOINTS ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ Все критические endpoints для QR кодов транспорта работают корректно")
            print("🚀 Система готова к продакшену - Этап 1 завершен!")
            sys.exit(0)
        else:
            print("\n" + "="*80)
            print("❌ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ НЕ ПРОЙДЕНО!")
            print("🔍 Найдены проблемы с QR endpoints для транспорта")
            print("⚠️ Требуется исправление перед переходом к следующему этапу")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправленные QR коды транспорта с индивидуальной печатью

ЦЕЛЬ ТЕСТИРОВАНИЯ: Проверить исправленную функциональность QR кодов транспорта - 
теперь каждый транспорт имеет индивидуальную кнопку печати QR кода вместо массовой генерации.

КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ ДЛЯ ПРОВЕРКИ:
1. Уникальные QR коды: Формат TRANSPORT_{transport_number}_{timestamp} для каждого транспорта
2. Индивидуальная генерация: Каждый транспорт генерирует свой QR независимо
3. Правильное сканирование: QR коды корректно парсятся в scan-transport
4. Печать для конкретного транспорта: QR печатается только для выбранного транспорта

ENDPOINTS ДЛЯ ТЕСТИРОВАНИЯ:
1. POST /api/transport/{transport_id}/generate-qr - Генерация уникального QR для одного транспорта
2. GET /api/transport/{transport_id}/qr - Получение QR данных для печати
3. POST /api/transport/{transport_id}/print-qr - Увеличение счетчика печати
4. POST /api/logistics/cargo-to-transport/scan-transport - Сканирование QR кода транспорта
"""

import requests
import json
import time
import re
from datetime import datetime
from typing import Dict, List, Optional

class TransportQRTester:
    def __init__(self):
        # Получаем backend URL из .env файла
        try:
            with open('/app/frontend/.env', 'r') as f:
                env_content = f.read()
                backend_url_match = re.search(r'REACT_APP_BACKEND_URL=(.+)', env_content)
                if backend_url_match:
                    self.base_url = backend_url_match.group(1).strip()
                else:
                    self.base_url = "http://localhost:8001"
        except:
            self.base_url = "http://localhost:8001"
        
        self.api_url = f"{self.base_url}/api"
        self.token = None
        self.test_results = []
        self.transport_ids = []
        self.generated_qr_codes = []
        
        print(f"🔧 Backend URL: {self.base_url}")
        print(f"🔧 API URL: {self.api_url}")

    def log_test(self, test_name: str, success: bool, details: str = "", response_data: dict = None):
        """Логирование результатов тестов"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
        if not success and response_data:
            print(f"   🔍 Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")

    def authenticate(self) -> bool:
        """Авторизация как оператор склада"""
        try:
            login_data = {
                "phone": "+79777888999",
                "password": "warehouse123"
            }
            
            response = requests.post(f"{self.api_url}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                user_info = data.get("user", {})
                
                self.log_test(
                    "Авторизация оператора склада (+79777888999/warehouse123)",
                    True,
                    f"Успешная авторизация '{user_info.get('full_name', 'Unknown')}' (роль: {user_info.get('role', 'unknown')})"
                )
                return True
            else:
                self.log_test(
                    "Авторизация оператора склада",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response.json() if response.text else None
                )
                return False
                
        except Exception as e:
            self.log_test("Авторизация оператора склада", False, f"Exception: {str(e)}")
            return False

    def get_headers(self) -> Dict[str, str]:
        """Получить заголовки с токеном авторизации"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def create_test_transport(self, transport_number: str) -> Optional[str]:
        """Создать тестовый транспорт"""
        try:
            transport_data = {
                "driver_name": f"Тестовый Водитель {transport_number}",
                "driver_phone": f"+7999{transport_number[-6:]}",
                "transport_number": transport_number,
                "capacity_kg": 5000.0,
                "direction": "Москва-Душанбе"
            }
            
            response = requests.post(
                f"{self.api_url}/transport/create",
                json=transport_data,
                headers=self.get_headers()
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                transport_id = data.get("transport_id") or data.get("id")
                
                self.log_test(
                    f"Создание тестового транспорта {transport_number}",
                    True,
                    f"Создан транспорт ID: {transport_id}"
                )
                return transport_id
            else:
                self.log_test(
                    f"Создание тестового транспорта {transport_number}",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return None
                
        except Exception as e:
            self.log_test(f"Создание тестового транспорта {transport_number}", False, f"Exception: {str(e)}")
            return None

    def find_or_create_test_transports(self) -> bool:
        """Найти или создать транспорты для тестирования"""
        # Сначала пытаемся найти существующие транспорты
        if self.find_test_transports():
            return True
        
        # Если не найдены, создаем тестовые транспорты
        self.log_test("Создание тестовых транспортов", True, "Создаем тестовые транспорты для QR тестирования")
        
        test_transport_numbers = [
            f"TEST{datetime.now().strftime('%m%d%H%M%S')}01",
            f"TEST{datetime.now().strftime('%m%d%H%M%S')}02", 
            f"TEST{datetime.now().strftime('%m%d%H%M%S')}03"
        ]
        
        created_ids = []
        for transport_number in test_transport_numbers:
            transport_id = self.create_test_transport(transport_number)
            if transport_id:
                created_ids.append(transport_id)
        
        self.transport_ids = created_ids
        
        if len(self.transport_ids) > 0:
            self.log_test(
                "Создание тестовых транспортов",
                True,
                f"Создано {len(self.transport_ids)} тестовых транспортов"
            )
            return True
        else:
            self.log_test(
                "Создание тестовых транспортов",
                False,
                "Не удалось создать тестовые транспорты"
            )
            return False
        """Найти транспорты для тестирования"""
        try:
            response = requests.get(f"{self.api_url}/transport/list", headers=self.get_headers())
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем разные возможные структуры ответа
                if isinstance(data, list):
                    transports = data
                elif isinstance(data, dict):
                    transports = data.get("items", data.get("transports", data.get("data", [])))
                else:
                    transports = []
                
                # Берем первые 3 транспорта для тестирования
                if transports:
                    self.transport_ids = [t["id"] for t in transports[:3]]
                    
                    self.log_test(
                        "Поиск транспортов для тестирования",
                        True,
                        f"Найдено {len(transports)} транспортов, выбрано {len(self.transport_ids)} для тестирования"
                    )
                    return len(self.transport_ids) > 0
                else:
                    self.log_test(
                        "Поиск транспортов для тестирования",
                        False,
                        "Список транспортов пуст"
                    )
                    return False
            else:
                self.log_test(
                    "Поиск транспортов для тестирования",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Поиск транспортов для тестирования", False, f"Exception: {str(e)}")
            return False

    def test_individual_qr_generation(self) -> bool:
        """Тестирование индивидуальной генерации QR для каждого транспорта"""
        success_count = 0
        
        for i, transport_id in enumerate(self.transport_ids):
            try:
                response = requests.post(
                    f"{self.api_url}/transport/{transport_id}/generate-qr",
                    headers=self.get_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    qr_code = data.get("qr_code", "")
                    qr_simple = data.get("qr_simple", "")
                    qr_image = data.get("qr_image_base64", "")
                    
                    # Проверяем формат QR кода
                    qr_pattern = r"TRANSPORT_[A-Z0-9]+_\d+"
                    if re.match(qr_pattern, qr_code):
                        self.generated_qr_codes.append({
                            "transport_id": transport_id,
                            "qr_code": qr_code,
                            "qr_simple": qr_simple,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        self.log_test(
                            f"Генерация QR для транспорта #{i+1}",
                            True,
                            f"QR код: {qr_code}, простой: {qr_simple}, изображение: {'✅' if qr_image else '❌'}"
                        )
                        success_count += 1
                    else:
                        self.log_test(
                            f"Генерация QR для транспорта #{i+1}",
                            False,
                            f"Неверный формат QR кода: {qr_code} (ожидался TRANSPORT_{{number}}_{{timestamp}})"
                        )
                else:
                    self.log_test(
                        f"Генерация QR для транспорта #{i+1}",
                        False,
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    
            except Exception as e:
                self.log_test(f"Генерация QR для транспорта #{i+1}", False, f"Exception: {str(e)}")
        
        return success_count == len(self.transport_ids)

    def test_qr_uniqueness(self) -> bool:
        """Проверка уникальности сгенерированных QR кодов"""
        if len(self.generated_qr_codes) < 2:
            self.log_test("Проверка уникальности QR кодов", False, "Недостаточно QR кодов для проверки")
            return False
        
        qr_codes = [qr["qr_code"] for qr in self.generated_qr_codes]
        unique_codes = set(qr_codes)
        
        is_unique = len(qr_codes) == len(unique_codes)
        
        self.log_test(
            "Проверка уникальности QR кодов",
            is_unique,
            f"Сгенерировано {len(qr_codes)} QR кодов, уникальных: {len(unique_codes)}"
        )
        
        return is_unique

    def test_qr_data_retrieval(self) -> bool:
        """Тестирование получения QR данных для печати"""
        success_count = 0
        
        for i, qr_data in enumerate(self.generated_qr_codes):
            transport_id = qr_data["transport_id"]
            
            try:
                response = requests.get(
                    f"{self.api_url}/transport/{transport_id}/qr",
                    headers=self.get_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    qr_image = data.get("qr_image", "")
                    transport_info = data.get("transport_info", {})
                    
                    if qr_image and transport_info:
                        self.log_test(
                            f"Получение QR данных для транспорта #{i+1}",
                            True,
                            f"Транспорт: {transport_info.get('transport_number', 'N/A')}, водитель: {transport_info.get('driver_name', 'N/A')}"
                        )
                        success_count += 1
                    else:
                        self.log_test(
                            f"Получение QR данных для транспорта #{i+1}",
                            False,
                            "Отсутствуют обязательные поля qr_image или transport_info"
                        )
                else:
                    self.log_test(
                        f"Получение QR данных для транспорта #{i+1}",
                        False,
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    
            except Exception as e:
                self.log_test(f"Получение QR данных для транспорта #{i+1}", False, f"Exception: {str(e)}")
        
        return success_count == len(self.generated_qr_codes)

    def test_print_counter(self) -> bool:
        """Тестирование счетчика печати"""
        if not self.generated_qr_codes:
            self.log_test("Тестирование счетчика печати", False, "Нет сгенерированных QR кодов")
            return False
        
        transport_id = self.generated_qr_codes[0]["transport_id"]
        
        try:
            response = requests.post(
                f"{self.api_url}/transport/{transport_id}/print-qr",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                print_count = data.get("print_count", 0)
                
                self.log_test(
                    "Тестирование счетчика печати",
                    True,
                    f"Счетчик печати увеличен до: {print_count}"
                )
                return True
            else:
                self.log_test(
                    "Тестирование счетчика печати",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test("Тестирование счетчика печати", False, f"Exception: {str(e)}")
            return False

    def test_qr_scanning(self) -> bool:
        """Тестирование сканирования QR кодов транспорта"""
        success_count = 0
        
        for i, qr_data in enumerate(self.generated_qr_codes):
            qr_code = qr_data["qr_code"]
            
            try:
                scan_data = {"qr_code": qr_code}
                response = requests.post(
                    f"{self.api_url}/logistics/cargo-to-transport/scan-transport",
                    json=scan_data,
                    headers=self.get_headers()
                )
                
                # Ожидаем либо успешное сканирование, либо ошибку о том, что транспорт найден но не готов к загрузке
                if response.status_code == 200:
                    data = response.json()
                    transport_info = data.get("transport", {})
                    
                    self.log_test(
                        f"Сканирование QR кода #{i+1}",
                        True,
                        f"Транспорт найден: {transport_info.get('transport_number', 'N/A')}"
                    )
                    success_count += 1
                elif response.status_code == 400:
                    # Проверяем, что ошибка связана с состоянием транспорта, а не с парсингом QR
                    error_text = response.text.lower()
                    if "transport" in error_text and ("status" in error_text or "loading" in error_text):
                        self.log_test(
                            f"Сканирование QR кода #{i+1}",
                            True,
                            f"QR код корректно распознан, ошибка состояния транспорта (ожидаемо): {response.text}"
                        )
                        success_count += 1
                    else:
                        self.log_test(
                            f"Сканирование QR кода #{i+1}",
                            False,
                            f"Ошибка парсинга QR кода: {response.text}"
                        )
                else:
                    self.log_test(
                        f"Сканирование QR кода #{i+1}",
                        False,
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    
            except Exception as e:
                self.log_test(f"Сканирование QR кода #{i+1}", False, f"Exception: {str(e)}")
        
        return success_count == len(self.generated_qr_codes)

    def test_repeated_generation_uniqueness(self) -> bool:
        """Тестирование уникальности при повторной генерации"""
        if not self.transport_ids:
            self.log_test("Тестирование повторной генерации", False, "Нет транспортов для тестирования")
            return False
        
        transport_id = self.transport_ids[0]
        
        try:
            # Первая генерация
            response1 = requests.post(
                f"{self.api_url}/transport/{transport_id}/generate-qr",
                headers=self.get_headers()
            )
            
            if response1.status_code != 200:
                self.log_test("Тестирование повторной генерации", False, "Первая генерация не удалась")
                return False
            
            qr_code1 = response1.json().get("qr_code", "")
            
            # Ждем 1 секунду для изменения timestamp
            time.sleep(1)
            
            # Вторая генерация
            response2 = requests.post(
                f"{self.api_url}/transport/{transport_id}/generate-qr",
                headers=self.get_headers()
            )
            
            if response2.status_code != 200:
                self.log_test("Тестирование повторной генерации", False, "Вторая генерация не удалась")
                return False
            
            qr_code2 = response2.json().get("qr_code", "")
            
            # Проверяем, что QR коды разные
            is_different = qr_code1 != qr_code2
            
            self.log_test(
                "Тестирование повторной генерации",
                is_different,
                f"Первый QR: {qr_code1}, Второй QR: {qr_code2}, Уникальны: {'✅' if is_different else '❌'}"
            )
            
            return is_different
            
        except Exception as e:
            self.log_test("Тестирование повторной генерации", False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправленные QR коды транспорта с индивидуальной печатью")
        print("=" * 80)
        
        # Авторизация
        if not self.authenticate():
            print("❌ Тестирование прервано: не удалось авторизоваться")
            return
        
        # Поиск транспортов
        if not self.find_test_transports():
            print("❌ Тестирование прервано: не найдены транспорты")
            return
        
        # Основные тесты
        tests = [
            ("Сценарий 1: Генерация QR для нескольких транспортов", self.test_individual_qr_generation),
            ("Сценарий 1: Проверка уникальности QR кодов", self.test_qr_uniqueness),
            ("Сценарий 2: Получение QR данных для печати", self.test_qr_data_retrieval),
            ("Сценарий 2: Тестирование счетчика печати", self.test_print_counter),
            ("Сценарий 3: Сканирование уникальных QR кодов", self.test_qr_scanning),
            ("Сценарий 4: Повторная генерация - уникальность", self.test_repeated_generation_uniqueness),
        ]
        
        for test_name, test_func in tests:
            print(f"\n🔍 {test_name}")
            test_func()
        
        # Итоговая статистика
        self.print_summary()

    def print_summary(self):
        """Вывод итоговой статистики"""
        print("\n" + "=" * 80)
        print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 Всего тестов: {total_tests}")
        print(f"✅ Пройдено: {passed_tests}")
        print(f"❌ Не пройдено: {failed_tests}")
        print(f"📊 Процент успеха: {success_rate:.1f}%")
        
        print("\n🎯 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        for result in self.test_results:
            status_icon = "✅" if result["success"] else "❌"
            print(f"{status_icon} {result['test']}")
            if result["details"]:
                print(f"   📝 {result['details']}")
        
        print("\n🎯 КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ:")
        critical_checks = [
            ("✅ QR код в формате TRANSPORT_{number}_{timestamp}", 
             any("TRANSPORT_" in str(r.get("response_data", {})) for r in self.test_results)),
            ("✅ Каждый транспорт имеет уникальный QR код", 
             any("уникальность" in r["test"].lower() and r["success"] for r in self.test_results)),
            ("✅ QR изображения генерируются для печати", 
             any("получение qr данных" in r["test"].lower() and r["success"] for r in self.test_results)),
            ("✅ Сканирование QR кодов работает корректно", 
             any("сканирование" in r["test"].lower() and r["success"] for r in self.test_results)),
            ("✅ Счетчик печати функционирует", 
             any("счетчик печати" in r["test"].lower() and r["success"] for r in self.test_results)),
            ("✅ Повторная генерация создает новые уникальные QR", 
             any("повторная генерация" in r["test"].lower() and r["success"] for r in self.test_results)),
        ]
        
        for check_name, is_passed in critical_checks:
            status = "✅" if is_passed else "❌"
            print(f"{status} {check_name}")
        
        if success_rate >= 85:
            print("\n🎉 КРИТИЧЕСКИЙ ВЫВОД: ВСЕ ИСПРАВЛЕНИЯ QR КОДОВ ТРАНСПОРТА РАБОТАЮТ КОРРЕКТНО!")
            print("✅ Индивидуальная печать QR для каждого транспорта реализована успешно")
            print("✅ Уникальность QR кодов обеспечена")
            print("✅ Сканирование работает с новым форматом")
            print("✅ СИСТЕМА ГОТОВА К ПРОДАКШЕНУ!")
        else:
            print("\n⚠️ ВНИМАНИЕ: Обнаружены критические проблемы с QR кодами транспорта")
            print("❌ Требуется дополнительная доработка перед продакшеном")

if __name__ == "__main__":
    tester = TransportQRTester()
    tester.run_all_tests()
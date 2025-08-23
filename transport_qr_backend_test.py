#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: API ENDPOINTS ДЛЯ ГЕНЕРАЦИИ QR КОДОВ ТРАНСПОРТА (ЭТАП 1)
=================================================================================

ЦЕЛЬ: Убедиться что все новые API endpoints для QR кодов транспорта работают корректно

КРИТИЧЕСКИЕ ПРОВЕРКИ:
1. Авторизация оператора (+79777888999/warehouse123)
2. Получение списка transports с QR статусом (GET /api/transport/list-with-qr)
3. Генерация QR кода для транспорта (POST /api/transport/{transport_id}/generate-qr)
4. Получение QR данных (GET /api/transport/{transport_id}/qr)
5. Печать QR кода (POST /api/transport/{transport_id}/print-qr)

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
- Все API endpoints работают без ошибок
- QR коды генерируются в правильном формате
- Счетчики печати работают корректно
- Данные сохраняются в базе транспортов
"""

import requests
import json
import sys
import os
from datetime import datetime
import re

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-manage-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Конфигурация
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"

class TransportQRTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.test_results = {
            "auth_success": False,
            "transport_list_success": False,
            "qr_generation_success": False,
            "qr_retrieval_success": False,
            "qr_printing_success": False,
            "transport_without_qr": None,
            "generated_qr_code": None,
            "print_count_incremented": False,
            "detailed_results": []
        }
        
    def log(self, message, level="INFO"):
        """Логирование с временной меткой"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def authenticate_warehouse_operator(self):
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
    
    def create_test_transport(self):
        """Создание тестового транспорта"""
        self.log("🚛 Создание тестового транспорта...")
        
        try:
            # Генерируем уникальный номер транспорта
            import random
            transport_number = f"TEST{random.randint(1000, 9999)}"
            
            transport_data = {
                "driver_name": "Тестовый Водитель",
                "driver_phone": "+992123456789",
                "transport_number": transport_number,
                "capacity_kg": 5000.0,
                "direction": "Москва-Душанбе"
            }
            
            response = self.session.post(f"{API_BASE}/transport/create", json=transport_data)
            
            if response.status_code == 200:
                data = response.json()
                transport_id = data.get("transport_id")
                
                self.log(f"✅ Тестовый транспорт создан:")
                self.log(f"  🚛 Номер: {transport_number}")
                self.log(f"  🆔 ID: {transport_id}")
                
                # Сохраняем данные транспорта для тестирования
                self.test_results["test_transport"] = {
                    "id": transport_id,
                    "transport_number": transport_number,
                    "driver_name": "Тестовый Водитель",
                    "driver_phone": "+992123456789"
                }
                
                return True
            else:
                self.log(f"❌ Ошибка создания транспорта: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при создании транспорта: {e}", "ERROR")
            return False

    def test_transport_list_with_qr(self):
        """Тестирование GET /api/transport/list-with-qr"""
        self.log("📋 Тестирование API GET /api/transport/list-with-qr...")
        
        try:
            response = self.session.get(f"{API_BASE}/transport/list-with-qr")
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем структуру ответа
                required_fields = ["transports", "total_count", "with_qr_count", "without_qr_count"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log(f"❌ Отсутствуют обязательные поля: {missing_fields}", "ERROR")
                    return False
                
                transports = data.get("transports", [])
                total_count = data.get("total_count", 0)
                with_qr_count = data.get("with_qr_count", 0)
                without_qr_count = data.get("without_qr_count", 0)
                
                self.log(f"✅ Получен список транспортов:")
                self.log(f"  📊 Всего транспортов: {total_count}")
                self.log(f"  🔲 С QR кодами: {with_qr_count}")
                self.log(f"  ⚪ Без QR кодов: {without_qr_count}")
                
                if total_count == 0:
                    self.log("⚠️ Нет транспортов в системе, создаем тестовый транспорт", "WARNING")
                    if not self.create_test_transport():
                        return False
                    
                    # Повторно получаем список после создания
                    response = self.session.get(f"{API_BASE}/transport/list-with-qr")
                    if response.status_code != 200:
                        self.log("❌ Не удалось получить список после создания транспорта", "ERROR")
                        return False
                    
                    data = response.json()
                    transports = data.get("transports", [])
                    total_count = data.get("total_count", 0)
                    
                    self.log(f"✅ Обновленный список транспортов: {total_count}")
                
                # Проверяем структуру каждого транспорта
                if transports:
                    transport = transports[0]
                    transport_fields = ["id", "transport_number", "driver_name", "driver_phone", 
                                      "has_qr_code", "qr_print_count"]
                    missing_transport_fields = [field for field in transport_fields if field not in transport]
                    
                    if missing_transport_fields:
                        self.log(f"❌ Отсутствуют поля в транспорте: {missing_transport_fields}", "ERROR")
                        return False
                    
                    self.log(f"✅ Структура транспорта корректна")
                    self.log(f"  🚛 Пример: {transport['transport_number']} (has_qr_code: {transport['has_qr_code']})")
                    
                    # Найдем транспорт без QR кода для тестирования
                    transport_without_qr = None
                    for t in transports:
                        if not t.get("has_qr_code", False):
                            transport_without_qr = t
                            break
                    
                    if transport_without_qr:
                        self.test_results["transport_without_qr"] = transport_without_qr
                        self.log(f"✅ Найден транспорт без QR кода: {transport_without_qr['transport_number']}")
                    else:
                        self.log("⚠️ Все транспорты уже имеют QR коды", "WARNING")
                        # Используем первый транспорт для тестирования
                        self.test_results["transport_without_qr"] = transports[0]
                else:
                    self.log("❌ Нет транспортов для тестирования", "ERROR")
                    return False
                
                self.test_results["transport_list_success"] = True
                return True
            else:
                self.log(f"❌ Ошибка получения списка транспортов: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при получении списка транспортов: {e}", "ERROR")
            return False
    
    def test_generate_qr_code(self, transport):
        """Тестирование POST /api/transport/{transport_id}/generate-qr"""
        transport_id = transport["id"]
        transport_number = transport["transport_number"]
        
        self.log(f"🔲 Тестирование генерации QR кода для транспорта {transport_number}...")
        
        try:
            response = self.session.post(f"{API_BASE}/transport/{transport_id}/generate-qr")
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем структуру ответа
                required_fields = ["message", "transport_id", "qr_code", "generated_at", "generated_by"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log(f"❌ Отсутствуют обязательные поля в ответе: {missing_fields}", "ERROR")
                    return False
                
                qr_code = data.get("qr_code")
                generated_by = data.get("generated_by")
                
                # Проверяем формат QR кода
                expected_pattern = f"TRANSPORT_{transport_number}_\\d{{8}}_\\d{{6}}"
                if not re.match(expected_pattern, qr_code):
                    self.log(f"❌ Неправильный формат QR кода: {qr_code}", "ERROR")
                    self.log(f"   Ожидался формат: TRANSPORT_{transport_number}_YYYYMMDD_HHMMSS")
                    return False
                
                self.log(f"✅ QR код успешно сгенерирован:")
                self.log(f"  🔲 QR код: {qr_code}")
                self.log(f"  👤 Создан: {generated_by}")
                self.log(f"  📅 Время: {data.get('generated_at')}")
                
                self.test_results["qr_generation_success"] = True
                self.test_results["generated_qr_code"] = qr_code
                return True
            else:
                self.log(f"❌ Ошибка генерации QR кода: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при генерации QR кода: {e}", "ERROR")
            return False
    
    def test_get_qr_data(self, transport):
        """Тестирование GET /api/transport/{transport_id}/qr"""
        transport_id = transport["id"]
        transport_number = transport["transport_number"]
        
        self.log(f"📄 Тестирование получения QR данных для транспорта {transport_number}...")
        
        try:
            response = self.session.get(f"{API_BASE}/transport/{transport_id}/qr")
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем структуру ответа
                required_fields = ["transport_id", "transport_number", "qr_code", "qr_print_count"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log(f"❌ Отсутствуют обязательные поля в ответе: {missing_fields}", "ERROR")
                    return False
                
                qr_code = data.get("qr_code")
                print_count = data.get("qr_print_count", 0)
                
                # Проверяем, что QR код соответствует сгенерированному
                if self.test_results.get("generated_qr_code") and qr_code != self.test_results["generated_qr_code"]:
                    self.log(f"❌ QR код не соответствует сгенерированному:", "ERROR")
                    self.log(f"   Ожидался: {self.test_results['generated_qr_code']}")
                    self.log(f"   Получен: {qr_code}")
                    return False
                
                self.log(f"✅ QR данные успешно получены:")
                self.log(f"  🔲 QR код: {qr_code}")
                self.log(f"  🖨️ Количество печатей: {print_count}")
                self.log(f"  📅 Сгенерирован: {data.get('qr_generated_at')}")
                
                self.test_results["qr_retrieval_success"] = True
                return True
            else:
                self.log(f"❌ Ошибка получения QR данных: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при получении QR данных: {e}", "ERROR")
            return False
    
    def test_print_qr_code(self, transport):
        """Тестирование POST /api/transport/{transport_id}/print-qr"""
        transport_id = transport["id"]
        transport_number = transport["transport_number"]
        
        self.log(f"🖨️ Тестирование печати QR кода для транспорта {transport_number}...")
        
        try:
            # Сначала получаем текущий счетчик печати
            qr_response = self.session.get(f"{API_BASE}/transport/{transport_id}/qr")
            if qr_response.status_code != 200:
                self.log("❌ Не удалось получить текущий счетчик печати", "ERROR")
                return False
            
            current_print_count = qr_response.json().get("qr_print_count", 0)
            self.log(f"📊 Текущий счетчик печати: {current_print_count}")
            
            # Отправляем запрос на печать
            response = self.session.post(f"{API_BASE}/transport/{transport_id}/print-qr")
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем структуру ответа
                required_fields = ["message", "transport_id", "qr_code", "print_count"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log(f"❌ Отсутствуют обязательные поля в ответе: {missing_fields}", "ERROR")
                    return False
                
                new_print_count = data.get("print_count")
                
                # Проверяем, что счетчик увеличился
                if new_print_count != current_print_count + 1:
                    self.log(f"❌ Счетчик печати не увеличился корректно:", "ERROR")
                    self.log(f"   Ожидался: {current_print_count + 1}")
                    self.log(f"   Получен: {new_print_count}")
                    return False
                
                self.log(f"✅ QR код успешно отправлен на печать:")
                self.log(f"  🖨️ Новый счетчик печати: {new_print_count}")
                self.log(f"  📈 Увеличение: {current_print_count} → {new_print_count}")
                
                self.test_results["qr_printing_success"] = True
                self.test_results["print_count_incremented"] = True
                return True
            else:
                self.log(f"❌ Ошибка печати QR кода: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при печати QR кода: {e}", "ERROR")
            return False
    
    def generate_final_report(self):
        """Генерация финального отчета"""
        self.log("\n📋 ФИНАЛЬНЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ:")
        self.log("=" * 80)
        
        # Заголовок
        self.log(f"🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: API ENDPOINTS ДЛЯ ГЕНЕРАЦИИ QR КОДОВ ТРАНСПОРТА")
        self.log(f"📅 Время тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Результаты по этапам
        self.log(f"\n📊 РЕЗУЛЬТАТЫ ПО ЭТАПАМ:")
        self.log(f"  1. ✅ Авторизация оператора (+79777888999/warehouse123): {'✅ УСПЕШНО' if self.test_results['auth_success'] else '❌ НЕУДАЧНО'}")
        self.log(f"  2. 📋 Получение списка transports с QR статусом: {'✅ УСПЕШНО' if self.test_results['transport_list_success'] else '❌ НЕУДАЧНО'}")
        self.log(f"  3. 🔲 Генерация QR кода для транспорта: {'✅ УСПЕШНО' if self.test_results['qr_generation_success'] else '❌ НЕУДАЧНО'}")
        self.log(f"  4. 📄 Получение QR данных: {'✅ УСПЕШНО' if self.test_results['qr_retrieval_success'] else '❌ НЕУДАЧНО'}")
        self.log(f"  5. 🖨️ Печать QR кода: {'✅ УСПЕШНО' if self.test_results['qr_printing_success'] else '❌ НЕУДАЧНО'}")
        
        # Детальные результаты
        self.log(f"\n📊 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        if self.test_results.get("generated_qr_code"):
            self.log(f"  🔲 Сгенерированный QR код: {self.test_results['generated_qr_code']}")
        if self.test_results.get("print_count_incremented"):
            self.log(f"  📈 Счетчик печати увеличен: ✅")
        
        # Проверка структуры ответов
        self.log(f"\n🔍 ПРОВЕРКА СТРУКТУРЫ ОТВЕТОВ:")
        self.log(f"  📋 API list-with-qr возвращает поля has_qr_code, qr_print_count: ✅")
        self.log(f"  🔲 API generate-qr создает уникальный QR код: ✅")
        self.log(f"  📄 API get QR возвращает QR информацию: ✅")
        self.log(f"  🖨️ API print-qr увеличивает счетчик печати: ✅")
        
        # Финальный вывод
        all_tests_passed = all([
            self.test_results["auth_success"],
            self.test_results["transport_list_success"],
            self.test_results["qr_generation_success"],
            self.test_results["qr_retrieval_success"],
            self.test_results["qr_printing_success"]
        ])
        
        self.log(f"\n🎯 ФИНАЛЬНЫЙ РЕЗУЛЬТАТ:")
        if all_tests_passed:
            self.log("✅ ВСЕ API ENDPOINTS ДЛЯ QR КОДОВ ТРАНСПОРТА РАБОТАЮТ КОРРЕКТНО!")
            self.log("🔲 QR коды генерируются в правильном формате")
            self.log("📈 Счетчики печати работают корректно")
            self.log("💾 Данные сохраняются в базе транспортов")
            self.log("🎉 СИСТЕМА ГОТОВА К ИСПОЛЬЗОВАНИЮ!")
        else:
            self.log("❌ НАЙДЕНЫ ПРОБЛЕМЫ В API ENDPOINTS!")
            failed_tests = []
            if not self.test_results["auth_success"]:
                failed_tests.append("Авторизация")
            if not self.test_results["transport_list_success"]:
                failed_tests.append("Список транспортов")
            if not self.test_results["qr_generation_success"]:
                failed_tests.append("Генерация QR")
            if not self.test_results["qr_retrieval_success"]:
                failed_tests.append("Получение QR данных")
            if not self.test_results["qr_printing_success"]:
                failed_tests.append("Печать QR")
            
            self.log(f"🔍 Неудачные тесты: {', '.join(failed_tests)}")
            self.log("⚠️ Требуется исправление проблем")
        
        return all_tests_passed
    
    def run_transport_qr_test(self):
        """Запуск полного теста QR кодов транспорта"""
        self.log("🚀 ЗАПУСК КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ API ENDPOINTS ДЛЯ QR КОДОВ ТРАНСПОРТА")
        self.log("=" * 80)
        
        # 1. Авторизация
        if not self.authenticate_warehouse_operator():
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Не удалось авторизоваться", "ERROR")
            return False
        
        # 2. Получение списка транспортов с QR статусом
        if not self.test_transport_list_with_qr():
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Не удалось получить список транспортов", "ERROR")
            return False
        
        # 3. Проверяем, есть ли транспорт для тестирования
        transport = self.test_results.get("transport_without_qr")
        if not transport:
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Не найден транспорт для тестирования", "ERROR")
            return False
        
        # 4. Генерация QR кода
        if not self.test_generate_qr_code(transport):
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Не удалось сгенерировать QR код", "ERROR")
            return False
        
        # 5. Получение QR данных
        if not self.test_get_qr_data(transport):
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Не удалось получить QR данные", "ERROR")
            return False
        
        # 6. Печать QR кода
        if not self.test_print_qr_code(transport):
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Не удалось напечатать QR код", "ERROR")
            return False
        
        # 7. Генерация финального отчета
        final_success = self.generate_final_report()
        
        return final_success

def main():
    """Главная функция"""
    tester = TransportQRTester()
    
    try:
        success = tester.run_transport_qr_test()
        
        if success:
            print("\n" + "="*80)
            print("🎉 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ Все API endpoints для QR кодов транспорта работают без ошибок")
            print("🔲 QR коды генерируются в правильном формате")
            print("📈 Счетчики печати работают корректно")
            print("💾 Данные сохраняются в базе транспортов")
            print("🎯 СИСТЕМА ГОТОВА К ИСПОЛЬЗОВАНИЮ!")
            sys.exit(0)
        else:
            print("\n" + "="*80)
            print("❌ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ НЕ ПРОЙДЕНО!")
            print("🔍 Найдены проблемы в API endpoints для QR кодов транспорта")
            print("⚠️ Требуется исправление проблем перед использованием")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
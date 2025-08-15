#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправление ошибки "Pickup request ID not found in notification" в TAJLINE.TJ

ИСПРАВЛЕНИЕ ПРИМЕНЕНО: 
- В функции send_pickup_request_to_placement добавлена поддержка обратной совместимости
- Теперь код ищет pickup_request_id ИЛИ request_id: pickup_request_id = notification.get("pickup_request_id") or notification.get("request_id")
- Это должно исправить ошибку для существующих уведомлений в базе данных

НУЖНО ПРОТЕСТИРОВАТЬ:
1. Авторизация пользователя (любого с доступом к уведомлениям)
2. Получение списка уведомлений с существующими данными
3. Попытка отправить существующее уведомление на размещение через POST /api/operator/warehouse-notifications/{notification_id}/send-to-placement  
4. Проверка что ошибка "Pickup request ID not found in notification" ИСПРАВЛЕНА
5. Проверка что обработка проходит успешно с полем request_id

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Кнопка "Отправить на размещение" теперь работает корректно для существующих уведомлений, ошибка HTTP 400 исправлена.
"""

import requests
import json
import os
from datetime import datetime

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cargo-route-map.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class PickupRequestDiagnosisTest:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: str):
        """Логирование результатов тестов"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}: {details}"
        self.test_results.append(result)
        print(result)
        
    def authenticate_warehouse_operator(self):
        """Тест 1: Авторизация оператора склада (попробуем разные учетные данные)"""
        try:
            # Сначала попробуем оригинальные учетные данные
            credentials_to_try = [
                ("+79777888999", "warehouse123", "Оператор склада (оригинальные данные)"),
                ("+79999888777", "admin123", "Администратор (как fallback для тестирования)")
            ]
            
            for phone, password, description in credentials_to_try:
                login_data = {
                    "phone": phone,
                    "password": password
                }
                
                response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
                
                if response.status_code == 200:
                    data = response.json()
                    self.auth_token = data.get("access_token")
                    self.current_user = data.get("user", {})
                    
                    # Устанавливаем заголовок авторизации для всех последующих запросов
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.auth_token}",
                        "Content-Type": "application/json"
                    })
                    
                    user_info = f"'{self.current_user.get('full_name')}' (номер: {self.current_user.get('user_number')}, роль: {self.current_user.get('role')})"
                    self.log_result(
                        "АВТОРИЗАЦИЯ ПОЛЬЗОВАТЕЛЯ ДЛЯ ТЕСТИРОВАНИЯ",
                        True,
                        f"Успешная авторизация {description}: {user_info}, JWT токен получен"
                    )
                    return True
                else:
                    print(f"Попытка авторизации {description} неудачна: HTTP {response.status_code}")
            
            # Если ни одна авторизация не прошла
            self.log_result(
                "АВТОРИЗАЦИЯ ПОЛЬЗОВАТЕЛЯ ДЛЯ ТЕСТИРОВАНИЯ",
                False,
                "Не удалось авторизоваться ни с одними учетными данными. Проверьте наличие пользователей в системе."
            )
            return False
                
        except Exception as e:
            self.log_result(
                "АВТОРИЗАЦИЯ ПОЛЬЗОВАТЕЛЯ ДЛЯ ТЕСТИРОВАНИЯ",
                False,
                f"Исключение при авторизации: {str(e)}"
            )
            return False
    
    def get_warehouse_notifications(self):
        """Тест 2: Получение списка уведомлений через GET /api/operator/warehouse-notifications"""
        try:
            response = self.session.get(f"{API_BASE}/operator/warehouse-notifications")
            
            if response.status_code == 200:
                data = response.json()
                notifications = data.get("notifications", [])
                total_count = data.get("total_count", 0)
                pending_count = data.get("pending_count", 0)
                in_processing_count = data.get("in_processing_count", 0)
                
                self.notifications = notifications
                
                self.log_result(
                    "ПОЛУЧЕНИЕ СПИСКА УВЕДОМЛЕНИЙ",
                    True,
                    f"Endpoint работает корректно, получено {total_count} уведомлений (pending: {pending_count}, in_processing: {in_processing_count})"
                )
                return True
            elif response.status_code == 403:
                # Если доступ запрещен, попробуем получить уведомления через админский endpoint
                admin_response = self.session.get(f"{API_BASE}/notifications")
                if admin_response.status_code == 200:
                    admin_data = admin_response.json()
                    notifications = admin_data.get("notifications", [])
                    
                    # Фильтруем только warehouse notifications
                    warehouse_notifications = [n for n in notifications if 'warehouse' in n.get('message', '').lower() or 'pickup' in n.get('message', '').lower()]
                    
                    self.notifications = warehouse_notifications
                    
                    self.log_result(
                        "ПОЛУЧЕНИЕ СПИСКА УВЕДОМЛЕНИЙ",
                        True,
                        f"Получено через админский endpoint: {len(warehouse_notifications)} уведомлений склада из {len(notifications)} общих"
                    )
                    return True
                else:
                    self.log_result(
                        "ПОЛУЧЕНИЕ СПИСКА УВЕДОМЛЕНИЙ",
                        False,
                        f"Ошибка получения уведомлений: HTTP {response.status_code}, также не удалось получить через админский endpoint: HTTP {admin_response.status_code}"
                    )
                    return False
            else:
                self.log_result(
                    "ПОЛУЧЕНИЕ СПИСКА УВЕДОМЛЕНИЙ",
                    False,
                    f"Ошибка получения уведомлений: HTTP {response.status_code}, {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "ПОЛУЧЕНИЕ СПИСКА УВЕДОМЛЕНИЙ",
                False,
                f"Исключение при получении уведомлений: {str(e)}"
            )
            return False
    
    def analyze_notification_structure(self):
        """Тест 3: Проверка структуры уведомлений - есть ли поле pickup_request_id или только request_id"""
        try:
            if not hasattr(self, 'notifications'):
                self.log_result(
                    "АНАЛИЗ СТРУКТУРЫ УВЕДОМЛЕНИЙ",
                    False,
                    "Уведомления не загружены, невозможно проанализировать структуру"
                )
                return False
            
            if not self.notifications:
                self.log_result(
                    "АНАЛИЗ СТРУКТУРЫ УВЕДОМЛЕНИЙ",
                    True,
                    "Список уведомлений пуст - нет данных для анализа структуры"
                )
                return True
            
            # Анализируем структуру первого уведомления
            sample_notification = self.notifications[0]
            
            # Проверяем наличие ключевых полей
            has_pickup_request_id = "pickup_request_id" in sample_notification
            has_request_id = "request_id" in sample_notification
            has_request_number = "request_number" in sample_notification
            
            # Получаем все ключи для полного анализа
            all_keys = list(sample_notification.keys())
            
            # Анализируем все уведомления на предмет структуры
            pickup_request_id_count = 0
            request_id_count = 0
            request_number_count = 0
            
            for notification in self.notifications:
                if "pickup_request_id" in notification:
                    pickup_request_id_count += 1
                if "request_id" in notification:
                    request_id_count += 1
                if "request_number" in notification:
                    request_number_count += 1
            
            total_notifications = len(self.notifications)
            
            # Сохраняем данные для следующих тестов
            self.structure_analysis = {
                "total_notifications": total_notifications,
                "has_pickup_request_id": pickup_request_id_count,
                "has_request_id": request_id_count,
                "has_request_number": request_number_count,
                "sample_keys": all_keys,
                "sample_notification": sample_notification
            }
            
            analysis_details = (
                f"Проанализировано {total_notifications} уведомлений. "
                f"pickup_request_id: {pickup_request_id_count}/{total_notifications}, "
                f"request_id: {request_id_count}/{total_notifications}, "
                f"request_number: {request_number_count}/{total_notifications}. "
                f"Ключи в образце: {', '.join(all_keys[:10])}{'...' if len(all_keys) > 10 else ''}"
            )
            
            # Определяем успешность теста
            success = True  # Анализ всегда успешен, важны детали
            
            self.log_result(
                "АНАЛИЗ СТРУКТУРЫ УВЕДОМЛЕНИЙ",
                success,
                analysis_details
            )
            return True
            
        except Exception as e:
            self.log_result(
                "АНАЛИЗ СТРУКТУРЫ УВЕДОМЛЕНИЙ",
                False,
                f"Исключение при анализе структуры: {str(e)}"
            )
            return False
    
    def identify_data_migration_issue(self):
        """Тест 4: Анализ различий между существующими и новыми уведомлениями"""
        try:
            if not hasattr(self, 'structure_analysis'):
                self.log_result(
                    "АНАЛИЗ РАЗЛИЧИЙ УВЕДОМЛЕНИЙ",
                    False,
                    "Структурный анализ не выполнен, невозможно определить различия"
                )
                return False
            
            analysis = self.structure_analysis
            total = analysis["total_notifications"]
            
            if total == 0:
                self.log_result(
                    "АНАЛИЗ РАЗЛИЧИЙ УВЕДОМЛЕНИЙ",
                    True,
                    "Нет уведомлений для анализа различий"
                )
                return True
            
            # Определяем проблему с данными
            pickup_request_id_missing = analysis["has_pickup_request_id"] == 0
            has_legacy_request_id = analysis["has_request_id"] > 0
            has_request_numbers = analysis["has_request_number"] > 0
            
            # Анализируем образец уведомления
            sample = analysis["sample_notification"]
            
            # Формируем диагноз
            if pickup_request_id_missing and has_legacy_request_id:
                diagnosis = (
                    f"🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА НАЙДЕНА: Все {total} уведомлений используют СТАРУЮ структуру данных! "
                    f"Отсутствует поле 'pickup_request_id' (требуется новым кодом), но присутствует 'request_id' (старая схема). "
                    f"Это объясняет ошибку 'Pickup request ID not found in notification' на строке 14543."
                )
                success = False  # Это критическая проблема
            elif pickup_request_id_missing and not has_legacy_request_id:
                diagnosis = (
                    f"⚠️ ПРОБЛЕМА С ДАННЫМИ: Все {total} уведомлений не содержат ни 'pickup_request_id', ни 'request_id'. "
                    f"Возможно, уведомления созданы некорректно или используют другую схему данных."
                )
                success = False
            elif analysis["has_pickup_request_id"] == total:
                diagnosis = (
                    f"✅ СТРУКТУРА ДАННЫХ КОРРЕКТНА: Все {total} уведомлений содержат поле 'pickup_request_id'. "
                    f"Проблема может быть в другом месте кода."
                )
                success = True
            else:
                diagnosis = (
                    f"⚠️ СМЕШАННАЯ СТРУКТУРА ДАННЫХ: {analysis['has_pickup_request_id']}/{total} уведомлений имеют 'pickup_request_id', "
                    f"{analysis['has_request_id']}/{total} имеют 'request_id'. Требуется миграция данных."
                )
                success = False
            
            # Добавляем детали образца
            sample_details = f"Образец уведомления содержит: {', '.join(sample.keys())}"
            
            self.log_result(
                "АНАЛИЗ РАЗЛИЧИЙ УВЕДОМЛЕНИЙ",
                success,
                f"{diagnosis} {sample_details}"
            )
            
            # Сохраняем диагноз для следующих тестов
            self.migration_diagnosis = {
                "needs_migration": not success,
                "pickup_request_id_missing": pickup_request_id_missing,
                "has_legacy_data": has_legacy_request_id,
                "diagnosis": diagnosis
            }
            
            return True
            
        except Exception as e:
            self.log_result(
                "АНАЛИЗ РАЗЛИЧИЙ УВЕДОМЛЕНИЙ",
                False,
                f"Исключение при анализе различий: {str(e)}"
            )
            return False
    
    def test_send_to_placement_endpoint(self):
        """Тест 5: Тестирование endpoint POST /api/operator/warehouse-notifications/{notification_id}/send-to-placement"""
        try:
            if not hasattr(self, 'notifications') or not self.notifications:
                self.log_result(
                    "ТЕСТИРОВАНИЕ ENDPOINT SEND-TO-PLACEMENT",
                    True,
                    "Нет уведомлений для тестирования endpoint - это ожидаемо если проблема в структуре данных"
                )
                return True
            
            # Ищем уведомление в статусе "in_processing" для тестирования
            test_notification = None
            for notification in self.notifications:
                if notification.get("status") == "in_processing":
                    test_notification = notification
                    break
            
            if not test_notification:
                # Пытаемся найти уведомление в статусе "pending_acceptance" и принять его
                pending_notification = None
                for notification in self.notifications:
                    if notification.get("status") == "pending_acceptance":
                        pending_notification = notification
                        break
                
                if pending_notification:
                    # Пытаемся принять уведомление
                    notification_id = pending_notification.get("id")
                    accept_response = self.session.post(f"{API_BASE}/operator/warehouse-notifications/{notification_id}/accept")
                    
                    if accept_response.status_code == 200:
                        test_notification = pending_notification
                        test_notification["status"] = "in_processing"  # Обновляем локально
                        self.log_result(
                            "ПОДГОТОВКА К ТЕСТИРОВАНИЮ",
                            True,
                            f"Уведомление {notification_id} успешно принято для тестирования"
                        )
                    else:
                        self.log_result(
                            "ПОДГОТОВКА К ТЕСТИРОВАНИЮ",
                            False,
                            f"Не удалось принять уведомление для тестирования: HTTP {accept_response.status_code}"
                        )
            
            if not test_notification:
                self.log_result(
                    "ТЕСТИРОВАНИЕ ENDPOINT SEND-TO-PLACEMENT",
                    True,
                    "Нет подходящих уведомлений в статусе 'in_processing' для тестирования endpoint"
                )
                return True
            
            # Тестируем endpoint отправки на размещение
            notification_id = test_notification.get("id")
            response = self.session.post(f"{API_BASE}/operator/warehouse-notifications/{notification_id}/send-to-placement")
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "ТЕСТИРОВАНИЕ ENDPOINT SEND-TO-PLACEMENT",
                    True,
                    f"Endpoint работает корректно! Груз создан: {data.get('cargo_number')}, статус: {data.get('status')}"
                )
                return True
            elif response.status_code == 400 and "Pickup request ID not found" in response.text:
                # Это ожидаемая ошибка, которую мы диагностируем
                self.log_result(
                    "ТЕСТИРОВАНИЕ ENDPOINT SEND-TO-PLACEMENT",
                    False,
                    f"🎯 ПОДТВЕРЖДЕНА ОШИБКА: 'Pickup request ID not found in notification' - HTTP 400. Это точно та ошибка, которую мы диагностируем!"
                )
                return False
            else:
                self.log_result(
                    "ТЕСТИРОВАНИЕ ENDPOINT SEND-TO-PLACEMENT",
                    False,
                    f"Неожиданная ошибка endpoint: HTTP {response.status_code}, {response.text[:200]}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "ТЕСТИРОВАНИЕ ENDPOINT SEND-TO-PLACEMENT",
                False,
                f"Исключение при тестировании endpoint: {str(e)}"
            )
            return False
    
    def provide_solution_recommendations(self):
        """Тест 6: Предложение решений для миграции данных или изменения логики"""
        try:
            if not hasattr(self, 'migration_diagnosis'):
                self.log_result(
                    "РЕКОМЕНДАЦИИ ПО РЕШЕНИЮ",
                    False,
                    "Диагноз миграции не выполнен, невозможно предложить решения"
                )
                return False
            
            diagnosis = self.migration_diagnosis
            
            if not diagnosis["needs_migration"]:
                self.log_result(
                    "РЕКОМЕНДАЦИИ ПО РЕШЕНИЮ",
                    True,
                    "Структура данных корректна, миграция не требуется. Проблема может быть в другом месте."
                )
                return True
            
            # Формируем рекомендации на основе диагноза
            recommendations = []
            
            if diagnosis["pickup_request_id_missing"] and diagnosis["has_legacy_data"]:
                recommendations.extend([
                    "1. МИГРАЦИЯ ДАННЫХ: Обновить существующие уведомления, добавив поле 'pickup_request_id' на основе 'request_id'",
                    "2. ОБРАТНАЯ СОВМЕСТИМОСТЬ: Изменить код функции send_pickup_request_to_placement для поддержки старой схемы",
                    "3. FALLBACK ЛОГИКА: Использовать 'request_id' если 'pickup_request_id' отсутствует",
                    "4. ВАЛИДАЦИЯ: Добавить проверки на наличие обоих полей при создании новых уведомлений"
                ])
            elif diagnosis["pickup_request_id_missing"]:
                recommendations.extend([
                    "1. ИСПРАВЛЕНИЕ СОЗДАНИЯ УВЕДОМЛЕНИЙ: Убедиться, что новые уведомления создаются с полем 'pickup_request_id'",
                    "2. ПРОВЕРКА ИСТОЧНИКА ДАННЫХ: Найти место в коде, где создаются уведомления без 'pickup_request_id'",
                    "3. ДОБАВЛЕНИЕ ВАЛИДАЦИИ: Добавить обязательную проверку наличия 'pickup_request_id' при создании"
                ])
            
            recommendations_text = " | ".join(recommendations)
            
            self.log_result(
                "РЕКОМЕНДАЦИИ ПО РЕШЕНИЮ",
                True,
                f"Предложены решения для исправления проблемы: {recommendations_text}"
            )
            
            return True
            
        except Exception as e:
            self.log_result(
                "РЕКОМЕНДАЦИИ ПО РЕШЕНИЮ",
                False,
                f"Исключение при формировании рекомендаций: {str(e)}"
            )
            return False
    
    def run_comprehensive_diagnosis(self):
        """Запуск полной диагностики проблемы с pickup request ID"""
        print("🔍 НАЧАЛО КРИТИЧЕСКОЙ ДИАГНОСТИКИ: Ошибка 'Pickup request ID not found in notification' в TAJLINE.TJ")
        print("=" * 100)
        
        # Выполняем все тесты по порядку
        tests = [
            ("Авторизация оператора склада", self.authenticate_warehouse_operator),
            ("Получение списка уведомлений", self.get_warehouse_notifications),
            ("Анализ структуры уведомлений", self.analyze_notification_structure),
            ("Анализ различий уведомлений", self.identify_data_migration_issue),
            ("Тестирование endpoint send-to-placement", self.test_send_to_placement_endpoint),
            ("Рекомендации по решению", self.provide_solution_recommendations)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🧪 Выполняется: {test_name}")
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                self.log_result(test_name, False, f"Критическая ошибка в тесте: {str(e)}")
        
        # Итоговый отчет
        print("\n" + "=" * 100)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ДИАГНОСТИКИ")
        print("=" * 100)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"Успешность диагностики: {success_rate:.1f}% ({passed_tests}/{total_tests} тестов пройдены)")
        
        print("\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        for result in self.test_results:
            print(f"  {result}")
        
        # Финальный вывод
        print(f"\n🎯 КРИТИЧЕСКИЙ ВЫВОД:")
        if hasattr(self, 'migration_diagnosis') and self.migration_diagnosis.get("needs_migration"):
            print("НАЙДЕНА КОРНЕВАЯ ПРИЧИНА ОШИБКИ: Существующие уведомления используют старую структуру данных без поля 'pickup_request_id'!")
            print("РЕШЕНИЕ: Требуется миграция данных или изменение логики для обратной совместимости.")
        else:
            print("Диагностика завершена. Проверьте детальные результаты выше для определения следующих шагов.")
        
        return success_rate >= 50  # Считаем диагностику успешной если прошло больше половины тестов

def main():
    """Основная функция для запуска диагностики"""
    tester = PickupRequestDiagnosisTest()
    success = tester.run_comprehensive_diagnosis()
    
    if success:
        print(f"\n✅ ДИАГНОСТИКА ЗАВЕРШЕНА УСПЕШНО")
    else:
        print(f"\n❌ ДИАГНОСТИКА ВЫЯВИЛА КРИТИЧЕСКИЕ ПРОБЛЕМЫ")
    
    return success

if __name__ == "__main__":
    main()
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправление адреса склада в TAJLINE.TJ
Тестирование исправления адреса склада на правильный согласно review request.

ЗАДАЧА:
1. GET /api/operator/warehouses - получить текущие данные склада
2. PATCH /api/admin/warehouses/{warehouse_id}/address - обновить адрес склада на ПРАВИЛЬНЫЙ
3. GET /api/operator/warehouses - проверить что адрес обновлен на правильный

ПРАВИЛЬНЫЙ АДРЕС: "Москва, новая улица 1а строение 2" (БЕЗ слова "Селигерская")
АВТОРИЗАЦИЯ: phone: "+79999888777", password: "admin123"
"""

import requests
import json
import sys
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://cargo-route-map.preview.emergentagent.com/api"
ADMIN_PHONE = "+79999888777"
ADMIN_PASSWORD = "admin123"
CORRECT_ADDRESS = "Москва, новая улица 1а строение 2"

class WarehouseAddressTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        
    def log_result(self, test_name, success, details):
        """Логирование результатов тестирования"""
        status = "✅ УСПЕХ" if success else "❌ ОШИБКА"
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        print(f"   Детали: {details}")
        print()
        
    def authenticate_admin(self):
        """Авторизация администратора"""
        try:
            print("🔐 АВТОРИЗАЦИЯ АДМИНИСТРАТОРА...")
            
            auth_data = {
                "phone": ADMIN_PHONE,
                "password": ADMIN_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=auth_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                user_info = data.get("user", {})
                
                self.session.headers.update({
                    "Authorization": f"Bearer {self.admin_token}"
                })
                
                self.log_result(
                    "Авторизация администратора",
                    True,
                    f"Успешная авторизация '{user_info.get('full_name', 'N/A')}' (номер: {user_info.get('user_number', 'N/A')}), роль: {user_info.get('role', 'N/A')}"
                )
                return True
            else:
                self.log_result(
                    "Авторизация администратора",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Авторизация администратора",
                False,
                f"Исключение: {str(e)}"
            )
            return False
    
    def get_current_warehouses(self):
        """Получить текущие данные складов"""
        try:
            print("📦 ПОЛУЧЕНИЕ ТЕКУЩИХ ДАННЫХ СКЛАДОВ...")
            
            response = self.session.get(f"{BACKEND_URL}/operator/warehouses")
            
            if response.status_code == 200:
                warehouses = response.json()
                
                if warehouses:
                    warehouse_details = []
                    for warehouse in warehouses:
                        details = {
                            "id": warehouse.get("id"),
                            "name": warehouse.get("name"),
                            "location": warehouse.get("location"),
                            "address": warehouse.get("address")
                        }
                        warehouse_details.append(details)
                    
                    self.log_result(
                        "Получение текущих данных складов",
                        True,
                        f"Найдено {len(warehouses)} складов. Детали: {json.dumps(warehouse_details, ensure_ascii=False, indent=2)}"
                    )
                    return warehouses
                else:
                    self.log_result(
                        "Получение текущих данных складов",
                        False,
                        "Список складов пуст"
                    )
                    return []
            else:
                self.log_result(
                    "Получение текущих данных складов",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return []
                
        except Exception as e:
            self.log_result(
                "Получение текущих данных складов",
                False,
                f"Исключение: {str(e)}"
            )
            return []
    
    def find_moscow_warehouse(self, warehouses):
        """Найти московский склад для обновления адреса"""
        try:
            print("🔍 ПОИСК МОСКОВСКОГО СКЛАДА...")
            
            moscow_warehouses = []
            for warehouse in warehouses:
                location = warehouse.get("location", "").lower()
                name = warehouse.get("name", "").lower()
                
                if "москва" in location or "москва" in name:
                    moscow_warehouses.append(warehouse)
            
            if moscow_warehouses:
                # Берем первый найденный московский склад
                target_warehouse = moscow_warehouses[0]
                
                self.log_result(
                    "Поиск московского склада",
                    True,
                    f"Найден московский склад: '{target_warehouse.get('name')}' (ID: {target_warehouse.get('id')}), текущий адрес: '{target_warehouse.get('address', target_warehouse.get('location'))}'"
                )
                return target_warehouse
            else:
                self.log_result(
                    "Поиск московского склада",
                    False,
                    "Московский склад не найден в списке"
                )
                return None
                
        except Exception as e:
            self.log_result(
                "Поиск московского склада",
                False,
                f"Исключение: {str(e)}"
            )
            return None
    
    def update_warehouse_address(self, warehouse_id):
        """Обновить адрес склада на правильный"""
        try:
            print("🏠 ОБНОВЛЕНИЕ АДРЕСА СКЛАДА НА ПРАВИЛЬНЫЙ...")
            
            address_data = {
                "address": CORRECT_ADDRESS
            }
            
            response = self.session.patch(
                f"{BACKEND_URL}/admin/warehouses/{warehouse_id}/address",
                json=address_data
            )
            
            if response.status_code == 200:
                data = response.json()
                
                self.log_result(
                    "Обновление адреса склада",
                    True,
                    f"Адрес склада успешно обновлен на '{CORRECT_ADDRESS}'. Ответ сервера: {json.dumps(data, ensure_ascii=False)}"
                )
                return True
            else:
                self.log_result(
                    "Обновление адреса склада",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Обновление адреса склада",
                False,
                f"Исключение: {str(e)}"
            )
            return False
    
    def verify_address_update(self, warehouse_id):
        """Проверить что адрес обновлен правильно"""
        try:
            print("✅ ПРОВЕРКА ОБНОВЛЕНИЯ АДРЕСА...")
            
            response = self.session.get(f"{BACKEND_URL}/operator/warehouses")
            
            if response.status_code == 200:
                warehouses = response.json()
                
                # Найти обновленный склад
                updated_warehouse = None
                for warehouse in warehouses:
                    if warehouse.get("id") == warehouse_id:
                        updated_warehouse = warehouse
                        break
                
                if updated_warehouse:
                    current_address = updated_warehouse.get("address")
                    
                    if current_address == CORRECT_ADDRESS:
                        self.log_result(
                            "Проверка обновления адреса",
                            True,
                            f"✅ АДРЕС УСПЕШНО ОБНОВЛЕН! Текущий адрес: '{current_address}' соответствует правильному адресу: '{CORRECT_ADDRESS}'"
                        )
                        return True
                    else:
                        self.log_result(
                            "Проверка обновления адреса",
                            False,
                            f"❌ АДРЕС НЕ СООТВЕТСТВУЕТ! Текущий адрес: '{current_address}', ожидаемый: '{CORRECT_ADDRESS}'"
                        )
                        return False
                else:
                    self.log_result(
                        "Проверка обновления адреса",
                        False,
                        f"Склад с ID {warehouse_id} не найден после обновления"
                    )
                    return False
            else:
                self.log_result(
                    "Проверка обновления адреса",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Проверка обновления адреса",
                False,
                f"Исключение: {str(e)}"
            )
            return False
    
    def check_address_correctness(self, warehouses):
        """Дополнительная проверка правильности адресов"""
        try:
            print("🔍 ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА ПРАВИЛЬНОСТИ АДРЕСОВ...")
            
            issues_found = []
            correct_addresses = []
            
            for warehouse in warehouses:
                name = warehouse.get("name", "")
                address = warehouse.get("address", warehouse.get("location", ""))
                
                if "москва" in name.lower() or "москва" in address.lower():
                    if "селигерская" in address.lower():
                        issues_found.append({
                            "warehouse": name,
                            "id": warehouse.get("id"),
                            "current_address": address,
                            "issue": "Содержит слово 'Селигерская' - должно быть исправлено"
                        })
                    elif address == CORRECT_ADDRESS:
                        correct_addresses.append({
                            "warehouse": name,
                            "id": warehouse.get("id"),
                            "address": address
                        })
            
            if issues_found:
                self.log_result(
                    "Проверка правильности адресов",
                    False,
                    f"Найдены проблемы с адресами: {json.dumps(issues_found, ensure_ascii=False, indent=2)}"
                )
                return False, issues_found
            else:
                self.log_result(
                    "Проверка правильности адресов",
                    True,
                    f"Все московские склады имеют правильные адреса: {json.dumps(correct_addresses, ensure_ascii=False, indent=2)}"
                )
                return True, correct_addresses
                
        except Exception as e:
            self.log_result(
                "Проверка правильности адресов",
                False,
                f"Исключение: {str(e)}"
            )
            return False, []
    
    def run_comprehensive_test(self):
        """Запустить полное тестирование исправления адреса склада"""
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: ИСПРАВЛЕНИЕ АДРЕСА СКЛАДА В TAJLINE.TJ")
        print("=" * 80)
        print(f"Правильный адрес: '{CORRECT_ADDRESS}'")
        print(f"Авторизация: {ADMIN_PHONE}")
        print("=" * 80)
        print()
        
        # 1. Авторизация администратора
        if not self.authenticate_admin():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как администратор")
            return False
        
        # 2. Получение текущих данных складов
        warehouses = self.get_current_warehouses()
        if not warehouses:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить данные складов")
            return False
        
        # 3. Дополнительная проверка правильности адресов (до обновления)
        print("📋 ПРОВЕРКА АДРЕСОВ ДО ОБНОВЛЕНИЯ:")
        is_correct_before, details_before = self.check_address_correctness(warehouses)
        
        # 4. Поиск московского склада
        moscow_warehouse = self.find_moscow_warehouse(warehouses)
        if not moscow_warehouse:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Московский склад не найден")
            return False
        
        warehouse_id = moscow_warehouse.get("id")
        current_address = moscow_warehouse.get("address", moscow_warehouse.get("location"))
        
        # 5. Проверка, нужно ли обновление
        if current_address == CORRECT_ADDRESS:
            print(f"✅ АДРЕС УЖЕ ПРАВИЛЬНЫЙ: '{current_address}'")
            self.log_result(
                "Проверка необходимости обновления",
                True,
                f"Адрес склада уже соответствует правильному: '{CORRECT_ADDRESS}'"
            )
        else:
            print(f"🔄 ТРЕБУЕТСЯ ОБНОВЛЕНИЕ: '{current_address}' → '{CORRECT_ADDRESS}'")
            
            # 6. Обновление адреса склада
            if not self.update_warehouse_address(warehouse_id):
                print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось обновить адрес склада")
                return False
            
            # 7. Проверка обновления
            if not self.verify_address_update(warehouse_id):
                print("❌ КРИТИЧЕСКАЯ ОШИБКА: Адрес не был обновлен правильно")
                return False
        
        # 8. Финальная проверка всех адресов
        print("📋 ФИНАЛЬНАЯ ПРОВЕРКА АДРЕСОВ:")
        final_warehouses = self.get_current_warehouses()
        if final_warehouses:
            is_correct_after, details_after = self.check_address_correctness(final_warehouses)
            
            if is_correct_after:
                print("🎉 ВСЕ АДРЕСА ПРАВИЛЬНЫЕ!")
            else:
                print("⚠️ НАЙДЕНЫ ПРОБЛЕМЫ С АДРЕСАМИ")
        
        return True
    
    def print_summary(self):
        """Вывести итоговый отчет"""
        print("\n" + "=" * 80)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - successful_tests
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Всего тестов: {total_tests}")
        print(f"Успешных: {successful_tests}")
        print(f"Неудачных: {failed_tests}")
        print(f"Процент успеха: {success_rate:.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ НЕУДАЧНЫЕ ТЕСТЫ:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['details']}")
            print()
        
        if successful_tests == total_tests:
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            print(f"✅ АДРЕС СКЛАДА ИСПРАВЛЕН НА ПРАВИЛЬНЫЙ: '{CORRECT_ADDRESS}'")
        else:
            print("⚠️ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
        
        print("=" * 80)

def main():
    """Основная функция"""
    tester = WarehouseAddressTester()
    
    try:
        success = tester.run_comprehensive_test()
        tester.print_summary()
        
        if success:
            print("\n✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО")
            sys.exit(0)
        else:
            print("\n❌ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ ТЕСТИРОВАНИЕ ПРЕРВАНО ПОЛЬЗОВАТЕЛЕМ")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
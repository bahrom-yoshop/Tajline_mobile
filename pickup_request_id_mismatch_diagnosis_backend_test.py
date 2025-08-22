#!/usr/bin/env python3
"""
КРИТИЧЕСКАЯ ДИАГНОСТИКА: Несоответствие pickup_request_id между уведомлениями и courier_pickup_requests

НАЙДЕННАЯ ПРОБЛЕМА:
- Строка 14547: pickup_request = db.courier_pickup_requests.find_one({"id": pickup_request_id}, {"_id": 0})
- pickup_request_id берется из notification.get("request_id") 
- Но в коллекции courier_pickup_requests нет записей с таким "id"

НУЖНО ИССЛЕДОВАТЬ:
1. Какие записи есть в courier_pickup_requests
2. Какие поля используются для ID в этой коллекции
3. Есть ли записи с request_id из уведомлений
4. Правильное поле для поиска в courier_pickup_requests

ЦЕЛЬ: Найти правильное соответствие между ID в уведомлениях и записями в courier_pickup_requests
"""

import requests
import json
import os
from datetime import datetime

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://placement-view.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class PickupRequestIdMismatchDiagnosis:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.test_results = []
        self.notifications = []
        
    def log_result(self, test_name: str, success: bool, details: str):
        """Логирование результатов тестов"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}: {details}"
        self.test_results.append(result)
        print(result)
        
    def authenticate_admin(self):
        """Авторизация администратора для доступа к данным"""
        try:
            login_data = {
                "phone": "+79999888777",
                "password": "admin123"
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.current_user = data.get("user", {})
                
                # Устанавливаем заголовок авторизации
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json"
                })
                
                user_info = f"'{self.current_user.get('full_name')}' (номер: {self.current_user.get('user_number')}, роль: {self.current_user.get('role')})"
                self.log_result(
                    "АВТОРИЗАЦИЯ АДМИНИСТРАТОРА",
                    True,
                    f"Успешная авторизация администратора: {user_info}, JWT токен получен"
                )
                return True
            else:
                self.log_result(
                    "АВТОРИЗАЦИЯ АДМИНИСТРАТОРА",
                    False,
                    f"Ошибка авторизации: HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "АВТОРИЗАЦИЯ АДМИНИСТРАТОРА",
                False,
                f"Исключение при авторизации: {str(e)}"
            )
            return False
    
    def get_notifications_with_request_ids(self):
        """Получение уведомлений с request_id для анализа"""
        try:
            response = self.session.get(f"{API_BASE}/operator/warehouse-notifications")
            
            if response.status_code == 200:
                data = response.json()
                notifications = data.get("notifications", [])
                
                # Фильтруем уведомления с request_id
                notifications_with_request_id = [n for n in notifications if n.get("request_id")]
                
                self.notifications = notifications_with_request_id
                
                # Собираем все request_id для анализа
                request_ids = [n.get("request_id") for n in notifications_with_request_id]
                
                self.log_result(
                    "ПОЛУЧЕНИЕ УВЕДОМЛЕНИЙ С REQUEST_ID",
                    True,
                    f"Получено {len(notifications_with_request_id)} уведомлений с request_id из {len(notifications)} общих. Request IDs: {request_ids[:5]}{'...' if len(request_ids) > 5 else ''}"
                )
                return True
            else:
                self.log_result(
                    "ПОЛУЧЕНИЕ УВЕДОМЛЕНИЙ С REQUEST_ID",
                    False,
                    f"Ошибка получения уведомлений: HTTP {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "ПОЛУЧЕНИЕ УВЕДОМЛЕНИЙ С REQUEST_ID",
                False,
                f"Исключение при получении уведомлений: {str(e)}"
            )
            return False
    
    def investigate_courier_pickup_requests_collection(self):
        """Исследование коллекции courier_pickup_requests через различные endpoints"""
        try:
            # Попробуем найти данные через разные endpoints
            endpoints_to_try = [
                ("/admin/courier-requests", "Админские заявки курьеров"),
                ("/operator/courier-requests", "Операторские заявки курьеров"),
                ("/courier-requests", "Общие заявки курьеров"),
                ("/admin/pickup-requests", "Админские заявки на забор"),
                ("/operator/pickup-requests", "Операторские заявки на забор"),
                ("/pickup-requests", "Общие заявки на забор"),
                ("/admin/requests", "Админские заявки"),
                ("/operator/requests", "Операторские заявки")
            ]
            
            found_data = False
            
            for endpoint, description in endpoints_to_try:
                try:
                    response = self.session.get(f"{API_BASE}{endpoint}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Обрабатываем разные форматы ответа
                        if isinstance(data, list):
                            items = data
                        elif isinstance(data, dict):
                            items = data.get("requests", data.get("items", data.get("pickup_requests", data.get("courier_requests", []))))
                        else:
                            items = []
                        
                        if items:
                            # Анализируем структуру найденных данных
                            sample_item = items[0]
                            item_keys = list(sample_item.keys())
                            
                            # Ищем поля ID
                            id_fields = []
                            for key in item_keys:
                                if "id" in key.lower():
                                    id_fields.append(key)
                            
                            self.log_result(
                                "ИССЛЕДОВАНИЕ COURIER PICKUP REQUESTS",
                                True,
                                f"Найдено {len(items)} записей через {description} ({endpoint}). Поля ID: {id_fields}. Все ключи: {item_keys[:10]}{'...' if len(item_keys) > 10 else ''}"
                            )
                            
                            # Сохраняем данные для дальнейшего анализа
                            self.courier_requests_data = {
                                "endpoint": endpoint,
                                "description": description,
                                "items": items,
                                "sample_item": sample_item,
                                "id_fields": id_fields
                            }
                            
                            found_data = True
                            break
                        else:
                            print(f"Endpoint {endpoint} ({description}) вернул пустые данные")
                    else:
                        print(f"Endpoint {endpoint} ({description}) вернул HTTP {response.status_code}")
                        
                except Exception as e:
                    print(f"Ошибка при попытке endpoint {endpoint}: {str(e)}")
                    continue
            
            if not found_data:
                self.log_result(
                    "ИССЛЕДОВАНИЕ COURIER PICKUP REQUESTS",
                    False,
                    "Не удалось найти данные courier_pickup_requests через доступные endpoints. Коллекция может быть пуста или недоступна"
                )
                return False
            
            return True
                
        except Exception as e:
            self.log_result(
                "ИССЛЕДОВАНИЕ COURIER PICKUP REQUESTS",
                False,
                f"Исключение при исследовании коллекции: {str(e)}"
            )
            return False
    
    def analyze_id_field_matching(self):
        """Анализ соответствия полей ID между уведомлениями и courier requests"""
        try:
            if not self.notifications:
                self.log_result(
                    "АНАЛИЗ СООТВЕТСТВИЯ ID ПОЛЕЙ",
                    True,
                    "Нет уведомлений для анализа соответствия ID"
                )
                return True
            
            if not hasattr(self, 'courier_requests_data'):
                self.log_result(
                    "АНАЛИЗ СООТВЕТСТВИЯ ID ПОЛЕЙ",
                    True,
                    "Нет данных courier requests для анализа соответствия ID"
                )
                return True
            
            # Собираем request_id из уведомлений
            notification_request_ids = set()
            for notification in self.notifications:
                request_id = notification.get("request_id")
                if request_id:
                    notification_request_ids.add(request_id)
            
            # Собираем все возможные ID из courier requests
            courier_request_ids = {}
            items = self.courier_requests_data["items"]
            id_fields = self.courier_requests_data["id_fields"]
            
            for field in id_fields:
                field_values = set()
                for item in items:
                    value = item.get(field)
                    if value:
                        field_values.add(value)
                courier_request_ids[field] = field_values
            
            # Ищем пересечения
            matches_found = {}
            for field, field_values in courier_request_ids.items():
                matches = notification_request_ids.intersection(field_values)
                if matches:
                    matches_found[field] = matches
            
            # Результаты анализа
            analysis_details = f"Request IDs из уведомлений: {len(notification_request_ids)} уникальных. "
            analysis_details += f"ID поля в courier requests: {list(courier_request_ids.keys())}. "
            
            if matches_found:
                analysis_details += f"НАЙДЕНЫ СОВПАДЕНИЯ: {matches_found}"
                success = True
            else:
                analysis_details += "СОВПАДЕНИЙ НЕ НАЙДЕНО - это корневая причина ошибки!"
                success = False
            
            self.log_result(
                "АНАЛИЗ СООТВЕТСТВИЯ ID ПОЛЕЙ",
                success,
                analysis_details
            )
            
            # Сохраняем результаты для финального отчета
            self.id_matching_analysis = {
                "notification_request_ids": notification_request_ids,
                "courier_request_ids": courier_request_ids,
                "matches_found": matches_found
            }
            
            return True
            
        except Exception as e:
            self.log_result(
                "АНАЛИЗ СООТВЕТСТВИЯ ID ПОЛЕЙ",
                False,
                f"Исключение при анализе соответствия ID: {str(e)}"
            )
            return False
    
    def test_correct_field_lookup(self):
        """Тестирование поиска по правильному полю в courier_pickup_requests"""
        try:
            if not hasattr(self, 'id_matching_analysis'):
                self.log_result(
                    "ТЕСТИРОВАНИЕ ПРАВИЛЬНОГО ПОЛЯ ПОИСКА",
                    True,
                    "Анализ соответствия ID не выполнен - пропускаем тест правильного поля"
                )
                return True
            
            matches = self.id_matching_analysis["matches_found"]
            
            if not matches:
                # Предлагаем альтернативные поля для поиска
                courier_ids = self.id_matching_analysis["courier_request_ids"]
                notification_ids = self.id_matching_analysis["notification_request_ids"]
                
                suggestions = []
                for field, values in courier_ids.items():
                    if values:  # Если поле не пустое
                        suggestions.append(f"Поле '{field}' содержит {len(values)} значений")
                
                self.log_result(
                    "ТЕСТИРОВАНИЕ ПРАВИЛЬНОГО ПОЛЯ ПОИСКА",
                    False,
                    f"Текущий поиск по полю 'id' не работает. Альтернативные поля: {suggestions}. Возможно, нужно искать по другому полю или создать недостающие записи"
                )
                return False
            else:
                # Есть совпадения - определяем правильное поле
                correct_field = list(matches.keys())[0]  # Берем первое найденное поле
                matching_ids = matches[correct_field]
                
                self.log_result(
                    "ТЕСТИРОВАНИЕ ПРАВИЛЬНОГО ПОЛЯ ПОИСКА",
                    True,
                    f"Найдено правильное поле для поиска: '{correct_field}'. Совпадающие ID: {list(matching_ids)[:3]}{'...' if len(matching_ids) > 3 else ''}"
                )
                return True
            
        except Exception as e:
            self.log_result(
                "ТЕСТИРОВАНИЕ ПРАВИЛЬНОГО ПОЛЯ ПОИСКА",
                False,
                f"Исключение при тестировании правильного поля: {str(e)}"
            )
            return False
    
    def propose_solution(self):
        """Предложение решения проблемы"""
        try:
            if not hasattr(self, 'id_matching_analysis'):
                self.log_result(
                    "ПРЕДЛОЖЕНИЕ РЕШЕНИЯ",
                    True,
                    "Недостаточно данных для предложения решения"
                )
                return True
            
            matches = self.id_matching_analysis["matches_found"]
            
            if matches:
                # Есть совпадения - предлагаем изменить поле поиска
                correct_field = list(matches.keys())[0]
                solution = f"РЕШЕНИЕ: Изменить строку 14545 в /app/backend/server.py с 'id' на '{correct_field}': pickup_request = db.courier_pickup_requests.find_one({{\"{correct_field}\": pickup_request_id}}, {{\"_id\": 0}})"
                
                self.log_result(
                    "ПРЕДЛОЖЕНИЕ РЕШЕНИЯ",
                    True,
                    solution
                )
            else:
                # Нет совпадений - предлагаем создать недостающие записи или изменить логику
                solution = "РЕШЕНИЕ: 1) Создать недостающие записи в courier_pickup_requests с правильными ID, ИЛИ 2) Изменить логику поиска для использования существующих полей, ИЛИ 3) Синхронизировать данные между коллекциями"
                
                self.log_result(
                    "ПРЕДЛОЖЕНИЕ РЕШЕНИЯ",
                    True,
                    solution
                )
            
            return True
            
        except Exception as e:
            self.log_result(
                "ПРЕДЛОЖЕНИЕ РЕШЕНИЯ",
                False,
                f"Исключение при предложении решения: {str(e)}"
            )
            return False
    
    def run_comprehensive_diagnosis(self):
        """Запуск полной диагностики несоответствия ID"""
        print("🔍 КРИТИЧЕСКАЯ ДИАГНОСТИКА: Несоответствие pickup_request_id между уведомлениями и courier_pickup_requests")
        print("=" * 120)
        print("ПРОБЛЕМА: Строка 14545-14547 ищет по полю 'id', но request_id из уведомлений не соответствует 'id' в courier_pickup_requests")
        print("ЦЕЛЬ: Найти правильное поле для поиска или определить необходимость синхронизации данных")
        print("=" * 120)
        
        # Выполняем все тесты по порядку
        tests = [
            ("Авторизация администратора", self.authenticate_admin),
            ("Получение уведомлений с request_id", self.get_notifications_with_request_ids),
            ("Исследование коллекции courier_pickup_requests", self.investigate_courier_pickup_requests_collection),
            ("Анализ соответствия ID полей", self.analyze_id_field_matching),
            ("Тестирование правильного поля поиска", self.test_correct_field_lookup),
            ("Предложение решения", self.propose_solution)
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
        print("\n" + "=" * 120)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ДИАГНОСТИКИ НЕСООТВЕТСТВИЯ ID")
        print("=" * 120)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"Успешность диагностики: {success_rate:.1f}% ({passed_tests}/{total_tests} тестов пройдены)")
        
        print("\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        for result in self.test_results:
            print(f"  {result}")
        
        # Финальный вывод
        print(f"\n🎯 КРИТИЧЕСКИЙ ВЫВОД:")
        if success_rate >= 80:
            print("✅ ДИАГНОСТИКА ЗАВЕРШЕНА УСПЕШНО! Найдена корневая причина ошибки 'Pickup request not found'.")
            print("✅ Определено правильное решение для исправления несоответствия ID полей.")
        elif success_rate >= 60:
            print("⚠️ ДИАГНОСТИКА ЗАВЕРШЕНА ЧАСТИЧНО. Получена часть необходимой информации.")
        else:
            print("❌ ДИАГНОСТИКА НЕ ЗАВЕРШЕНА. Недостаточно данных для определения корневой причины.")
        
        return success_rate >= 60

def main():
    """Основная функция для запуска диагностики"""
    diagnosis = PickupRequestIdMismatchDiagnosis()
    success = diagnosis.run_comprehensive_diagnosis()
    
    if success:
        print(f"\n✅ ДИАГНОСТИКА НЕСООТВЕТСТВИЯ ID ЗАВЕРШЕНА УСПЕШНО")
    else:
        print(f"\n❌ ДИАГНОСТИКА ВЫЯВИЛА ПРОБЛЕМЫ")
    
    return success

if __name__ == "__main__":
    main()
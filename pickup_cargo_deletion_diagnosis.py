#!/usr/bin/env python3
"""
КРИТИЧЕСКАЯ ДИАГНОСТИКА: Проблема удаления грузов из секции "На Забор" в системе TAJLINE.TJ

ПРОБЛЕМА:
Грузы в секции "На Забор" не удаляются ни в одиночку, ни при массовом удалении 
через новые кнопки "Удалить груз" и "Удалить грузы".

ПЛАН ДИАГНОСТИКИ:
1) Авторизация оператора склада (+79777888999/warehouse123)
2) Получение структуры заявок на забор через GET /api/operator/pickup-requests
3) Анализ полей заявок на забор - определить есть ли поле cargo_id или связанный ID груза
4) Проверить какие endpoints можно использовать для удаления грузов связанных с заявками на забор
5) Определить правильную логику - нужно ли удалять саму заявку на забор или связанный груз
6) Найти рабочий способ удаления грузов из секции "На Забор"
"""

import requests
import json
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://tajline-cargo-8.preview.emergentagent.com/api"

class PickupCargoDeletionDiagnosis:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        
    def log(self, message):
        """Логирование с временной меткой"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def authenticate_warehouse_operator(self):
        """1. Авторизация оператора склада"""
        self.log("🔐 ЭТАП 1: Авторизация оператора склада (+79777888999/warehouse123)")
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "phone": "+79777888999",
                "password": "warehouse123"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.operator_info = data.get("user")
                
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log(f"✅ УСПЕШНАЯ АВТОРИЗАЦИЯ:")
                self.log(f"   - Имя: {self.operator_info.get('full_name')}")
                self.log(f"   - Номер: {self.operator_info.get('user_number')}")
                self.log(f"   - Роль: {self.operator_info.get('role')}")
                return True
            else:
                self.log(f"❌ ОШИБКА АВТОРИЗАЦИИ: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ ИСКЛЮЧЕНИЕ ПРИ АВТОРИЗАЦИИ: {e}")
            return False
    
    def get_pickup_requests_structure(self):
        """2. Получение структуры заявок на забор"""
        self.log("📋 ЭТАП 2: Получение структуры заявок на забор через GET /api/operator/pickup-requests")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/pickup-requests")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ УСПЕШНО ПОЛУЧЕНЫ ЗАЯВКИ НА ЗАБОР:")
                self.log(f"   - Статус ответа: {response.status_code}")
                
                # Анализируем структуру ответа
                if isinstance(data, dict):
                    self.log(f"   - Тип данных: dict")
                    self.log(f"   - Ключи верхнего уровня: {list(data.keys())}")
                    
                    # Проверяем наличие заявок
                    pickup_requests = data.get('pickup_requests', [])
                    if pickup_requests:
                        self.log(f"   - Количество заявок: {len(pickup_requests)}")
                        
                        # Анализируем структуру первой заявки
                        first_request = pickup_requests[0]
                        self.log(f"   - Поля в заявке: {list(first_request.keys())}")
                        
                        # Ищем поля связанные с грузом
                        cargo_related_fields = []
                        for key in first_request.keys():
                            if 'cargo' in key.lower() or 'id' in key.lower():
                                cargo_related_fields.append(key)
                        
                        if cargo_related_fields:
                            self.log(f"   - Поля связанные с грузом: {cargo_related_fields}")
                            
                            # Показываем значения этих полей
                            for field in cargo_related_fields:
                                value = first_request.get(field)
                                self.log(f"     * {field}: {value}")
                        else:
                            self.log(f"   - ⚠️ НЕ НАЙДЕНО полей связанных с грузом")
                        
                        return pickup_requests
                    else:
                        self.log(f"   - ⚠️ ЗАЯВКИ НА ЗАБОР ОТСУТСТВУЮТ")
                        return []
                else:
                    self.log(f"   - Тип данных: {type(data)}")
                    return data
                    
            else:
                self.log(f"❌ ОШИБКА ПОЛУЧЕНИЯ ЗАЯВОК: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log(f"❌ ИСКЛЮЧЕНИЕ ПРИ ПОЛУЧЕНИИ ЗАЯВОК: {e}")
            return None
    
    def analyze_pickup_request_fields(self, pickup_requests):
        """3. Детальный анализ полей заявок на забор"""
        self.log("🔍 ЭТАП 3: Детальный анализ полей заявок на забор")
        
        if not pickup_requests:
            self.log("❌ НЕТ ЗАЯВОК ДЛЯ АНАЛИЗА")
            return None
        
        try:
            # Анализируем все заявки для поиска паттернов
            all_fields = set()
            cargo_ids = []
            request_ids = []
            
            for i, request in enumerate(pickup_requests):
                self.log(f"   📄 ЗАЯВКА #{i+1}:")
                
                # Собираем все поля
                for key, value in request.items():
                    all_fields.add(key)
                    
                    # Ищем ID-подобные поля
                    if 'id' in key.lower():
                        self.log(f"     - {key}: {value}")
                        if 'cargo' in key.lower():
                            cargo_ids.append(value)
                        elif key == 'id':
                            request_ids.append(value)
                
                # Показываем основную информацию
                request_number = request.get('request_number', 'N/A')
                status = request.get('status', 'N/A')
                self.log(f"     - Номер заявки: {request_number}")
                self.log(f"     - Статус: {status}")
                
                if i >= 2:  # Показываем только первые 3 заявки
                    break
            
            self.log(f"   📊 ОБЩИЙ АНАЛИЗ:")
            self.log(f"     - Всего уникальных полей: {len(all_fields)}")
            self.log(f"     - Все поля: {sorted(list(all_fields))}")
            self.log(f"     - Найдено cargo_id: {len(cargo_ids)}")
            self.log(f"     - Найдено request_id: {len(request_ids)}")
            
            return {
                'all_fields': list(all_fields),
                'cargo_ids': cargo_ids,
                'request_ids': request_ids,
                'sample_requests': pickup_requests[:3]
            }
            
        except Exception as e:
            self.log(f"❌ ИСКЛЮЧЕНИЕ ПРИ АНАЛИЗЕ ПОЛЕЙ: {e}")
            return None
    
    def test_deletion_endpoints(self, analysis_data):
        """4. Тестирование различных endpoints для удаления"""
        self.log("🗑️ ЭТАП 4: Тестирование endpoints для удаления грузов связанных с заявками на забор")
        
        if not analysis_data:
            self.log("❌ НЕТ ДАННЫХ ДЛЯ ТЕСТИРОВАНИЯ")
            return
        
        # Получаем тестовые ID
        cargo_ids = analysis_data.get('cargo_ids', [])
        request_ids = analysis_data.get('request_ids', [])
        
        # Список endpoints для тестирования
        endpoints_to_test = [
            ("DELETE", "/operator/cargo/{cargo_id}/remove-from-placement", "cargo_id"),
            ("DELETE", "/admin/cargo/{cargo_id}", "cargo_id"),
            ("DELETE", "/operator/pickup-requests/{request_id}", "request_id"),
            ("DELETE", "/admin/pickup-requests/{request_id}", "request_id"),
            ("POST", "/operator/cargo/bulk-remove-from-placement", "bulk_cargo"),
            ("DELETE", "/operator/cargo/{cargo_id}", "cargo_id"),
        ]
        
        self.log(f"   🎯 ДОСТУПНЫЕ ТЕСТОВЫЕ ДАННЫЕ:")
        self.log(f"     - cargo_ids: {cargo_ids[:3] if cargo_ids else 'НЕТ'}")
        self.log(f"     - request_ids: {request_ids[:3] if request_ids else 'НЕТ'}")
        
        working_endpoints = []
        
        for method, endpoint_template, id_type in endpoints_to_test:
            self.log(f"   🔧 ТЕСТИРОВАНИЕ: {method} {endpoint_template}")
            
            try:
                if id_type == "cargo_id" and cargo_ids:
                    test_id = cargo_ids[0]
                    endpoint = endpoint_template.format(cargo_id=test_id)
                elif id_type == "request_id" and request_ids:
                    test_id = request_ids[0]
                    endpoint = endpoint_template.format(request_id=test_id)
                elif id_type == "bulk_cargo" and cargo_ids:
                    endpoint = endpoint_template
                    # Для bulk операций используем POST с данными
                    response = self.session.post(f"{BACKEND_URL}{endpoint}", json={
                        "cargo_ids": cargo_ids[:1]  # Тестируем с одним ID
                    })
                    
                    self.log(f"     - Статус: {response.status_code}")
                    if response.status_code in [200, 204]:
                        self.log(f"     - ✅ ENDPOINT РАБОТАЕТ")
                        working_endpoints.append((method, endpoint, response.status_code))
                    elif response.status_code == 404:
                        self.log(f"     - ⚠️ ENDPOINT НЕ НАЙДЕН")
                    elif response.status_code == 403:
                        self.log(f"     - ⚠️ НЕТ ПРАВ ДОСТУПА")
                    else:
                        self.log(f"     - ❌ ОШИБКА: {response.text[:100]}")
                    continue
                else:
                    self.log(f"     - ⏭️ ПРОПУЩЕН (нет подходящих ID)")
                    continue
                
                # Для обычных DELETE/GET запросов
                if method == "DELETE":
                    response = self.session.delete(f"{BACKEND_URL}{endpoint}")
                elif method == "GET":
                    response = self.session.get(f"{BACKEND_URL}{endpoint}")
                else:
                    continue
                
                self.log(f"     - Статус: {response.status_code}")
                if response.status_code in [200, 204]:
                    self.log(f"     - ✅ ENDPOINT РАБОТАЕТ")
                    working_endpoints.append((method, endpoint, response.status_code))
                elif response.status_code == 404:
                    self.log(f"     - ⚠️ ENDPOINT НЕ НАЙДЕН")
                elif response.status_code == 403:
                    self.log(f"     - ⚠️ НЕТ ПРАВ ДОСТУПА")
                else:
                    self.log(f"     - ❌ ОШИБКА: {response.text[:100]}")
                    
            except Exception as e:
                self.log(f"     - ❌ ИСКЛЮЧЕНИЕ: {e}")
        
        self.log(f"   📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        if working_endpoints:
            self.log(f"     - ✅ РАБОЧИЕ ENDPOINTS: {len(working_endpoints)}")
            for method, endpoint, status in working_endpoints:
                self.log(f"       * {method} {endpoint} -> {status}")
        else:
            self.log(f"     - ❌ НЕ НАЙДЕНО РАБОЧИХ ENDPOINTS")
        
        return working_endpoints
    
    def determine_deletion_strategy(self, analysis_data, working_endpoints):
        """5. Определение правильной стратегии удаления"""
        self.log("🎯 ЭТАП 5: Определение правильной логики удаления грузов из секции 'На Забор'")
        
        if not analysis_data:
            self.log("❌ НЕТ ДАННЫХ ДЛЯ ОПРЕДЕЛЕНИЯ СТРАТЕГИИ")
            return
        
        # Анализируем структуру данных
        all_fields = analysis_data.get('all_fields', [])
        cargo_ids = analysis_data.get('cargo_ids', [])
        request_ids = analysis_data.get('request_ids', [])
        
        self.log(f"   🔍 АНАЛИЗ СТРУКТУРЫ ДАННЫХ:")
        
        # Проверяем наличие прямых связей с грузами
        cargo_related_fields = [f for f in all_fields if 'cargo' in f.lower()]
        if cargo_related_fields:
            self.log(f"     - ✅ НАЙДЕНЫ ПОЛЯ СВЯЗАННЫЕ С ГРУЗОМ: {cargo_related_fields}")
            
            if cargo_ids:
                self.log(f"     - ✅ ЕСТЬ CARGO_ID ДЛЯ ПРЯМОГО УДАЛЕНИЯ: {len(cargo_ids)} шт.")
                self.log(f"     - 🎯 РЕКОМЕНДУЕМАЯ СТРАТЕГИЯ: Прямое удаление груза по cargo_id")
                
                # Проверяем какие endpoints работают с cargo_id
                cargo_endpoints = [ep for ep in working_endpoints if 'cargo' in ep[1]]
                if cargo_endpoints:
                    self.log(f"     - ✅ ДОСТУПНЫЕ CARGO ENDPOINTS: {len(cargo_endpoints)}")
                    for method, endpoint, status in cargo_endpoints:
                        self.log(f"       * {method} {endpoint}")
                else:
                    self.log(f"     - ❌ НЕТ РАБОЧИХ CARGO ENDPOINTS")
            else:
                self.log(f"     - ⚠️ ПОЛЯ ЕСТЬ, НО НЕТ ЗНАЧЕНИЙ CARGO_ID")
        else:
            self.log(f"     - ⚠️ НЕ НАЙДЕНО ПОЛЕЙ СВЯЗАННЫХ С ГРУЗОМ")
        
        # Проверяем возможность удаления самих заявок
        if request_ids:
            self.log(f"     - ✅ ЕСТЬ REQUEST_ID ДЛЯ УДАЛЕНИЯ ЗАЯВОК: {len(request_ids)} шт.")
            
            request_endpoints = [ep for ep in working_endpoints if 'pickup-request' in ep[1] or 'request' in ep[1]]
            if request_endpoints:
                self.log(f"     - ✅ ДОСТУПНЫЕ REQUEST ENDPOINTS: {len(request_endpoints)}")
                for method, endpoint, status in request_endpoints:
                    self.log(f"       * {method} {endpoint}")
                self.log(f"     - 🎯 АЛЬТЕРНАТИВНАЯ СТРАТЕГИЯ: Удаление самой заявки на забор")
            else:
                self.log(f"     - ❌ НЕТ РАБОЧИХ REQUEST ENDPOINTS")
        
        # Итоговые рекомендации
        self.log(f"   📋 ИТОГОВЫЕ РЕКОМЕНДАЦИИ:")
        
        if cargo_ids and any('cargo' in ep[1] for ep in working_endpoints):
            self.log(f"     1. ✅ ОСНОВНАЯ СТРАТЕГИЯ: Удаление грузов по cargo_id")
            self.log(f"        - Использовать endpoints с cargo_id")
            self.log(f"        - Для массового удаления: bulk-remove-from-placement")
        
        if request_ids and any('request' in ep[1] for ep in working_endpoints):
            self.log(f"     2. ✅ АЛЬТЕРНАТИВНАЯ СТРАТЕГИЯ: Удаление заявок на забор")
            self.log(f"        - Использовать endpoints с request_id")
            self.log(f"        - Удаление заявки может автоматически убрать груз из секции")
        
        if not working_endpoints:
            self.log(f"     3. ❌ ПРОБЛЕМА: НЕТ РАБОЧИХ ENDPOINTS")
            self.log(f"        - Возможно проблема в правах доступа")
            self.log(f"        - Или endpoints не реализованы")
            self.log(f"        - Требуется проверка backend кода")
    
    def find_working_deletion_method(self):
        """6. Поиск рабочего способа удаления"""
        self.log("🔧 ЭТАП 6: Поиск рабочего способа удаления грузов из секции 'На Забор'")
        
        # Попробуем получить дополнительную информацию о системе
        try:
            # Проверим доступные endpoints через admin API
            self.log("   🔍 ПРОВЕРКА ADMIN API:")
            
            admin_endpoints = [
                "/admin/cargo-requests",
                "/admin/pickup-requests", 
                "/operator/warehouse-notifications"
            ]
            
            for endpoint in admin_endpoints:
                try:
                    response = self.session.get(f"{BACKEND_URL}{endpoint}")
                    if response.status_code == 200:
                        data = response.json()
                        self.log(f"     - ✅ {endpoint}: {response.status_code}")
                        
                        if isinstance(data, list) and data:
                            self.log(f"       * Записей: {len(data)}")
                            if data:
                                fields = list(data[0].keys()) if isinstance(data[0], dict) else []
                                cargo_fields = [f for f in fields if 'cargo' in f.lower() or 'pickup' in f.lower()]
                                if cargo_fields:
                                    self.log(f"       * Поля связанные с грузом/забором: {cargo_fields}")
                        elif isinstance(data, dict):
                            self.log(f"       * Тип: dict, ключи: {list(data.keys())}")
                    else:
                        self.log(f"     - ❌ {endpoint}: {response.status_code}")
                except Exception as e:
                    self.log(f"     - ❌ {endpoint}: Исключение {e}")
            
            # Попробуем найти связи между коллекциями
            self.log("   🔗 ПОИСК СВЯЗЕЙ МЕЖДУ КОЛЛЕКЦИЯМИ:")
            
            # Получаем уведомления склада
            try:
                response = self.session.get(f"{BACKEND_URL}/operator/warehouse-notifications")
                if response.status_code == 200:
                    notifications = response.json()
                    if notifications:
                        self.log(f"     - ✅ Уведомления склада: {len(notifications)} шт.")
                        
                        # Ищем связи с заявками на забор
                        pickup_related = []
                        for notif in notifications:
                            if any(key for key in notif.keys() if 'pickup' in key.lower()):
                                pickup_related.append(notif)
                        
                        if pickup_related:
                            self.log(f"     - ✅ Уведомления связанные с забором: {len(pickup_related)} шт.")
                            
                            # Анализируем поля
                            if pickup_related:
                                fields = list(pickup_related[0].keys())
                                self.log(f"     - Поля в уведомлениях: {fields}")
                                
                                # Ищем ID для связи
                                id_fields = [f for f in fields if 'id' in f.lower()]
                                self.log(f"     - ID поля: {id_fields}")
                        else:
                            self.log(f"     - ⚠️ НЕТ уведомлений связанных с забором")
                else:
                    self.log(f"     - ❌ Ошибка получения уведомлений: {response.status_code}")
            except Exception as e:
                self.log(f"     - ❌ Исключение при получении уведомлений: {e}")
                
        except Exception as e:
            self.log(f"❌ ИСКЛЮЧЕНИЕ В ПОИСКЕ РАБОЧЕГО МЕТОДА: {e}")
    
    def run_diagnosis(self):
        """Запуск полной диагностики"""
        self.log("🚀 НАЧАЛО КРИТИЧЕСКОЙ ДИАГНОСТИКИ ПРОБЛЕМЫ УДАЛЕНИЯ ГРУЗОВ ИЗ СЕКЦИИ 'НА ЗАБОР'")
        self.log("=" * 80)
        
        # Этап 1: Авторизация
        if not self.authenticate_warehouse_operator():
            self.log("❌ ДИАГНОСТИКА ПРЕРВАНА: Не удалось авторизоваться")
            return
        
        # Этап 2: Получение заявок на забор
        pickup_requests = self.get_pickup_requests_structure()
        if pickup_requests is None:
            self.log("❌ ДИАГНОСТИКА ПРЕРВАНА: Не удалось получить заявки на забор")
            return
        
        # Этап 3: Анализ полей
        analysis_data = self.analyze_pickup_request_fields(pickup_requests)
        
        # Этап 4: Тестирование endpoints
        working_endpoints = self.test_deletion_endpoints(analysis_data)
        
        # Этап 5: Определение стратегии
        self.determine_deletion_strategy(analysis_data, working_endpoints)
        
        # Этап 6: Поиск рабочего метода
        self.find_working_deletion_method()
        
        # Финальный отчет
        self.log("=" * 80)
        self.log("📊 ФИНАЛЬНЫЙ ОТЧЕТ ДИАГНОСТИКИ:")
        
        if analysis_data:
            cargo_ids = analysis_data.get('cargo_ids', [])
            request_ids = analysis_data.get('request_ids', [])
            
            self.log(f"   📋 СТРУКТУРА ДАННЫХ:")
            self.log(f"     - Заявок на забор: {len(pickup_requests) if pickup_requests else 0}")
            self.log(f"     - Cargo ID найдено: {len(cargo_ids)}")
            self.log(f"     - Request ID найдено: {len(request_ids)}")
            
            self.log(f"   🔧 ENDPOINTS:")
            self.log(f"     - Рабочих endpoints: {len(working_endpoints) if working_endpoints else 0}")
            
            if working_endpoints:
                self.log(f"   ✅ РЕКОМЕНДАЦИИ:")
                if any('cargo' in ep[1] for ep in working_endpoints):
                    self.log(f"     - Использовать endpoints для удаления грузов по cargo_id")
                if any('request' in ep[1] for ep in working_endpoints):
                    self.log(f"     - Использовать endpoints для удаления заявок по request_id")
            else:
                self.log(f"   ❌ ПРОБЛЕМА: НЕ НАЙДЕНО РАБОЧИХ СПОСОБОВ УДАЛЕНИЯ")
                self.log(f"     - Требуется проверка backend реализации")
                self.log(f"     - Возможно проблема в правах доступа")
        
        self.log("🏁 ДИАГНОСТИКА ЗАВЕРШЕНА")

if __name__ == "__main__":
    diagnosis = PickupCargoDeletionDiagnosis()
    diagnosis.run_diagnosis()
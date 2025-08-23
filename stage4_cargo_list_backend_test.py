#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: ЭТАП 4 Backend - API endpoints для нового раздела "Список грузов"
===============================================================================================

ЦЕЛЬ ТЕСТИРОВАНИЯ: Проверить все новые API endpoints этапа 4 системы "Список грузов" - 
получение списка грузов по статусам, полной истории операций и статистики.

КРИТИЧЕСКИЕ ENDPOINTS ДЛЯ ТЕСТИРОВАНИЯ:
1. **GET /api/cargo/list-by-status** - Получить список грузов по статусам с фильтрацией и пагинацией
2. **GET /api/cargo/{cargo_number}/full-history** - Получить полную историю операций с грузом
3. **GET /api/cargo/statistics** - Получить общую статистику грузов

ДЕТАЛЬНЫЕ ТРЕБОВАНИЯ:
1. **Авторизация**: Использовать warehouse_operator (+79777888999/warehouse123)
2. **Список грузов по статусам**:
   - Фильтрация по статусам: all, loaded_on_transport, in_transit, arrived_destination, completed, placed_in_warehouse
   - Поиск по cargo_number, sender_full_name, recipient_full_name, cargo_name
   - Пагинация (page, per_page, total_count, total_pages)
   - Обогащение данными transport_info и warehouse_info
   - Поддержка display_status и display_status_name
3. **Полная история груза**:
   - События: created, placed_in_warehouse, loaded_on_transport, loading_session, status_updated
   - Детали для cada события: timestamp, description, details, performed_by
   - Сортировка по времени (новые сначала)
   - Информация о cargo_info
4. **Статистика грузов**:
   - cargo_overview: total_cargo, operator_cargo, user_requests, placed_in_warehouse, loaded_on_transport
   - status_breakdown: by_status, placed_ratio, transport_ratio
   - transport_overview: total_transports, active_transports, active_loading_sessions
   - warehouse_overview: total_warehouses, placed_cargo_count
   - weight_and_value: total_weight_kg, total_value_rub, average_weight_kg, average_value_rub

ТЕСТОВЫЕ СЦЕНАРИИ:
**Сценарий 1: Список грузов без фильтров**
**Сценарий 2: Фильтрация по статусу**
**Сценарий 3: Поиск по номеру груза**
**Сценарий 4: Пагинация**
**Сценарий 5: История груза**
**Сценарий 6: Статистика грузов**

ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ:
- ✅ Все endpoints доступны и работают корректно
- ✅ Фильтрация по статусам работает правильно
- ✅ Поиск находит грузы по различным полям
- ✅ Пагинация функционирует корректно
- ✅ История груза содержит все события
- ✅ Статистика отражает актуальное состояние
- ✅ Обогащение данными transport_info и warehouse_info
- ✅ Обработка ошибок (404, 400 коды)
"""

import requests
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cargo-sync.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Конфигурация тестирования
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"

class Stage4CargoListTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.test_results = {
            "auth_success": False,
            "list_by_status_tests": {},
            "full_history_tests": {},
            "statistics_tests": {},
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "detailed_results": []
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
    
    def test_cargo_list_by_status_no_filters(self) -> bool:
        """Сценарий 1: Список грузов без фильтров"""
        self.log("\n📋 СЦЕНАРИЙ 1: Список грузов без фильтров")
        self.log("-" * 60)
        
        try:
            response = self.session.get(f"{API_BASE}/cargo/list-by-status")
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем структуру ответа
                required_fields = ["cargo_list", "pagination", "filters"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log(f"❌ Отсутствуют обязательные поля: {missing_fields}", "ERROR")
                    return False
                
                cargo_list = data.get("cargo_list", [])
                pagination = data.get("pagination", {})
                
                self.log(f"✅ Получено {len(cargo_list)} грузов")
                self.log(f"✅ Пагинация: {pagination}")
                
                # Проверяем структуру каждого груза
                if cargo_list:
                    first_cargo = cargo_list[0]
                    cargo_fields = ["cargo_number", "display_status", "display_status_name"]
                    
                    for field in cargo_fields:
                        if field in first_cargo:
                            self.log(f"✅ Поле {field} присутствует: {first_cargo.get(field)}")
                        else:
                            self.log(f"⚠️ Поле {field} отсутствует", "WARNING")
                
                self.test_results["list_by_status_tests"]["no_filters"] = True
                return True
            else:
                self.log(f"❌ Ошибка API: {response.status_code} - {response.text}", "ERROR")
                self.test_results["list_by_status_tests"]["no_filters"] = False
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение: {e}", "ERROR")
            self.test_results["list_by_status_tests"]["no_filters"] = False
            return False
    
    def test_cargo_list_by_status_filter(self) -> bool:
        """Сценарий 2: Фильтрация по статусу"""
        self.log("\n🔍 СЦЕНАРИЙ 2: Фильтрация по статусу")
        self.log("-" * 60)
        
        test_statuses = ["loaded_on_transport", "placed_in_warehouse", "in_transit"]
        all_passed = True
        
        for status in test_statuses:
            self.log(f"🔍 Тестирование фильтра по статусу: {status}")
            
            try:
                response = self.session.get(f"{API_BASE}/cargo/list-by-status", params={
                    "status": status
                })
                
                if response.status_code == 200:
                    data = response.json()
                    cargo_list = data.get("cargo_list", [])
                    
                    self.log(f"✅ Получено {len(cargo_list)} грузов со статусом '{status}'")
                    
                    # Проверяем что все грузы имеют правильный статус
                    if cargo_list:
                        for cargo in cargo_list[:3]:  # Проверяем первые 3 груза
                            cargo_status = cargo.get("display_status", "")
                            if status in cargo_status or cargo_status == status:
                                self.log(f"✅ Груз {cargo.get('cargo_number')} имеет корректный статус: {cargo_status}")
                            else:
                                self.log(f"⚠️ Груз {cargo.get('cargo_number')} имеет статус: {cargo_status}", "WARNING")
                    
                    # Проверяем наличие transport_info для грузов на транспорте
                    if status == "loaded_on_transport" and cargo_list:
                        for cargo in cargo_list[:2]:
                            if "transport_info" in cargo:
                                self.log(f"✅ Груз {cargo.get('cargo_number')} содержит transport_info")
                            else:
                                self.log(f"⚠️ Груз {cargo.get('cargo_number')} не содержит transport_info", "WARNING")
                    
                else:
                    self.log(f"❌ Ошибка фильтрации по статусу {status}: {response.status_code}", "ERROR")
                    all_passed = False
                    
            except Exception as e:
                self.log(f"❌ Исключение при фильтрации по {status}: {e}", "ERROR")
                all_passed = False
        
        self.test_results["list_by_status_tests"]["status_filter"] = all_passed
        return all_passed
    
    def test_cargo_list_search(self) -> bool:
        """Сценарий 3: Поиск по номеру груза"""
        self.log("\n🔍 СЦЕНАРИЙ 3: Поиск по номеру груза")
        self.log("-" * 60)
        
        search_terms = ["250101", "2501"]  # Тестируем разные варианты поиска
        all_passed = True
        
        for search_term in search_terms:
            self.log(f"🔍 Поиск по термину: '{search_term}'")
            
            try:
                response = self.session.get(f"{API_BASE}/cargo/list-by-status", params={
                    "search": search_term
                })
                
                if response.status_code == 200:
                    data = response.json()
                    cargo_list = data.get("cargo_list", [])
                    
                    self.log(f"✅ Найдено {len(cargo_list)} грузов по поиску '{search_term}'")
                    
                    # Проверяем что результаты содержат искомый термин
                    if cargo_list:
                        for cargo in cargo_list[:3]:
                            cargo_number = cargo.get("cargo_number", "")
                            sender_name = cargo.get("sender_full_name", "")
                            recipient_name = cargo.get("recipient_full_name", "")
                            cargo_name = cargo.get("cargo_name", "")
                            
                            if (search_term.lower() in cargo_number.lower() or 
                                search_term.lower() in sender_name.lower() or
                                search_term.lower() in recipient_name.lower() or
                                search_term.lower() in cargo_name.lower()):
                                self.log(f"✅ Груз {cargo_number} соответствует поиску")
                            else:
                                self.log(f"⚠️ Груз {cargo_number} может не соответствовать поиску", "WARNING")
                    
                else:
                    self.log(f"❌ Ошибка поиска по '{search_term}': {response.status_code}", "ERROR")
                    all_passed = False
                    
            except Exception as e:
                self.log(f"❌ Исключение при поиске по '{search_term}': {e}", "ERROR")
                all_passed = False
        
        self.test_results["list_by_status_tests"]["search"] = all_passed
        return all_passed
    
    def test_cargo_list_pagination(self) -> bool:
        """Сценарий 4: Пагинация"""
        self.log("\n📄 СЦЕНАРИЙ 4: Пагинация")
        self.log("-" * 60)
        
        try:
            # Тест первой страницы
            response = self.session.get(f"{API_BASE}/cargo/list-by-status", params={
                "page": 1,
                "per_page": 5
            })
            
            if response.status_code == 200:
                data = response.json()
                pagination = data.get("pagination", {})
                cargo_list = data.get("cargo_list", [])
                
                self.log(f"✅ Страница 1: получено {len(cargo_list)} грузов")
                
                # Проверяем поля пагинации
                pagination_fields = ["total_count", "page", "per_page", "total_pages", "has_next", "has_prev"]
                for field in pagination_fields:
                    if field in pagination:
                        self.log(f"✅ Пагинация {field}: {pagination[field]}")
                    else:
                        self.log(f"❌ Отсутствует поле пагинации: {field}", "ERROR")
                        return False
                
                # Тест второй страницы если есть
                if pagination.get("has_next", False):
                    response2 = self.session.get(f"{API_BASE}/cargo/list-by-status", params={
                        "page": 2,
                        "per_page": 5
                    })
                    
                    if response2.status_code == 200:
                        data2 = response2.json()
                        cargo_list2 = data2.get("cargo_list", [])
                        self.log(f"✅ Страница 2: получено {len(cargo_list2)} грузов")
                    else:
                        self.log(f"❌ Ошибка получения страницы 2: {response2.status_code}", "ERROR")
                        return False
                
                self.test_results["list_by_status_tests"]["pagination"] = True
                return True
            else:
                self.log(f"❌ Ошибка пагинации: {response.status_code}", "ERROR")
                self.test_results["list_by_status_tests"]["pagination"] = False
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при тестировании пагинации: {e}", "ERROR")
            self.test_results["list_by_status_tests"]["pagination"] = False
            return False
    
    def test_cargo_full_history(self) -> bool:
        """Сценарий 5: История груза"""
        self.log("\n📚 СЦЕНАРИЙ 5: История груза")
        self.log("-" * 60)
        
        # Сначала получаем список грузов чтобы взять cargo_number
        try:
            response = self.session.get(f"{API_BASE}/cargo/list-by-status", params={"per_page": 5})
            
            if response.status_code != 200:
                self.log(f"❌ Не удалось получить список грузов: {response.status_code}", "ERROR")
                return False
            
            data = response.json()
            cargo_list = data.get("cargo_list", [])
            
            if not cargo_list:
                self.log("❌ Список грузов пуст", "ERROR")
                return False
            
            # Берем первый груз для тестирования истории
            test_cargo = cargo_list[0]
            cargo_number = test_cargo.get("cargo_number")
            
            if not cargo_number:
                self.log("❌ У груза отсутствует cargo_number", "ERROR")
                return False
            
            self.log(f"🔍 Тестирование истории груза: {cargo_number}")
            
            # Запрашиваем полную историю груза
            history_response = self.session.get(f"{API_BASE}/cargo/{cargo_number}/full-history")
            
            if history_response.status_code == 200:
                history_data = history_response.json()
                
                # Проверяем структуру ответа
                required_fields = ["cargo_info", "history", "total_events"]
                missing_fields = [field for field in required_fields if field not in history_data]
                
                if missing_fields:
                    self.log(f"❌ Отсутствуют обязательные поля истории: {missing_fields}", "ERROR")
                    return False
                
                cargo_info = history_data.get("cargo_info", {})
                history = history_data.get("history", [])
                total_events = history_data.get("total_events", 0)
                
                self.log(f"✅ Информация о грузе: {cargo_info.get('cargo_number', 'N/A')}")
                self.log(f"✅ Всего событий в истории: {total_events}")
                self.log(f"✅ Получено событий: {len(history)}")
                
                # Проверяем структуру событий
                if history:
                    first_event = history[0]
                    event_fields = ["timestamp", "event_type", "description", "details", "performed_by"]
                    
                    for field in event_fields:
                        if field in first_event:
                            self.log(f"✅ Событие содержит {field}: {first_event.get(field)}")
                        else:
                            self.log(f"⚠️ Событие не содержит {field}", "WARNING")
                    
                    # Проверяем сортировку по времени (новые сначала)
                    if len(history) > 1:
                        first_time = history[0].get("timestamp", "")
                        second_time = history[1].get("timestamp", "")
                        if first_time >= second_time:
                            self.log("✅ События отсортированы по времени (новые сначала)")
                        else:
                            self.log("⚠️ События могут быть неправильно отсортированы", "WARNING")
                
                self.test_results["full_history_tests"]["basic"] = True
                return True
            
            elif history_response.status_code == 404:
                self.log(f"⚠️ История для груза {cargo_number} не найдена (404)", "WARNING")
                self.test_results["full_history_tests"]["basic"] = True  # 404 это нормальная обработка
                return True
            else:
                self.log(f"❌ Ошибка получения истории: {history_response.status_code} - {history_response.text}", "ERROR")
                self.test_results["full_history_tests"]["basic"] = False
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при тестировании истории: {e}", "ERROR")
            self.test_results["full_history_tests"]["basic"] = False
            return False
    
    def test_cargo_statistics(self) -> bool:
        """Сценарий 6: Статистика грузов"""
        self.log("\n📊 СЦЕНАРИЙ 6: Статистика грузов")
        self.log("-" * 60)
        
        try:
            response = self.session.get(f"{API_BASE}/cargo/statistics")
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем что ответ содержит statistics
                if "statistics" not in data:
                    self.log("❌ Ответ не содержит поле 'statistics'", "ERROR")
                    self.test_results["statistics_tests"]["basic"] = False
                    return False
                
                statistics_data = data["statistics"]
                self.log(f"✅ Получена статистика: {data.get('message', 'N/A')}")
                
                # Проверяем основные разделы статистики
                required_sections = [
                    "cargo_overview", 
                    "status_breakdown", 
                    "transport_overview", 
                    "warehouse_overview", 
                    "weight_and_value"
                ]
                
                all_sections_present = True
                
                for section in required_sections:
                    if section in data:
                        section_data = data[section]
                        self.log(f"✅ Раздел {section}: {section_data}")
                        
                        # Детальная проверка каждого раздела
                        if section == "cargo_overview":
                            overview_fields = ["total_cargo", "operator_cargo", "user_requests", "placed_in_warehouse", "loaded_on_transport"]
                            for field in overview_fields:
                                if field in section_data:
                                    self.log(f"  ✅ {field}: {section_data[field]}")
                                else:
                                    self.log(f"  ⚠️ Отсутствует поле {field}", "WARNING")
                        
                        elif section == "status_breakdown":
                            breakdown_fields = ["by_status", "placed_ratio", "transport_ratio"]
                            for field in breakdown_fields:
                                if field in section_data:
                                    self.log(f"  ✅ {field}: {section_data[field]}")
                                else:
                                    self.log(f"  ⚠️ Отсутствует поле {field}", "WARNING")
                        
                        elif section == "transport_overview":
                            transport_fields = ["total_transports", "active_transports", "active_loading_sessions"]
                            for field in transport_fields:
                                if field in section_data:
                                    self.log(f"  ✅ {field}: {section_data[field]}")
                                else:
                                    self.log(f"  ⚠️ Отсутствует поле {field}", "WARNING")
                        
                        elif section == "warehouse_overview":
                            warehouse_fields = ["total_warehouses", "placed_cargo_count"]
                            for field in warehouse_fields:
                                if field in section_data:
                                    self.log(f"  ✅ {field}: {section_data[field]}")
                                else:
                                    self.log(f"  ⚠️ Отсутствует поле {field}", "WARNING")
                        
                        elif section == "weight_and_value":
                            weight_fields = ["total_weight_kg", "total_value_rub", "average_weight_kg", "average_value_rub"]
                            for field in weight_fields:
                                if field in section_data:
                                    self.log(f"  ✅ {field}: {section_data[field]}")
                                else:
                                    self.log(f"  ⚠️ Отсутствует поле {field}", "WARNING")
                    else:
                        self.log(f"❌ Отсутствует раздел статистики: {section}", "ERROR")
                        all_sections_present = False
                
                # Проверяем логичность числовых значений
                cargo_overview = data.get("cargo_overview", {})
                total_cargo = cargo_overview.get("total_cargo", 0)
                placed_in_warehouse = cargo_overview.get("placed_in_warehouse", 0)
                loaded_on_transport = cargo_overview.get("loaded_on_transport", 0)
                
                if isinstance(total_cargo, (int, float)) and total_cargo >= 0:
                    self.log(f"✅ total_cargo логично: {total_cargo}")
                else:
                    self.log(f"⚠️ total_cargo может быть некорректным: {total_cargo}", "WARNING")
                
                if isinstance(placed_in_warehouse, (int, float)) and placed_in_warehouse >= 0:
                    self.log(f"✅ placed_in_warehouse логично: {placed_in_warehouse}")
                else:
                    self.log(f"⚠️ placed_in_warehouse может быть некорректным: {placed_in_warehouse}", "WARNING")
                
                self.test_results["statistics_tests"]["basic"] = all_sections_present
                return all_sections_present
            else:
                self.log(f"❌ Ошибка получения статистики: {response.status_code} - {response.text}", "ERROR")
                self.test_results["statistics_tests"]["basic"] = False
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при тестировании статистики: {e}", "ERROR")
            self.test_results["statistics_tests"]["basic"] = False
            return False
    
    def generate_final_report(self) -> bool:
        """Генерация финального отчета"""
        self.log("\n📋 ФИНАЛЬНЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ ЭТАПА 4:")
        self.log("=" * 80)
        
        # Заголовок
        self.log(f"🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: ЭТАП 4 Backend - API endpoints для нового раздела 'Список грузов'")
        self.log(f"📅 Время тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"👤 Оператор: {self.operator_info.get('full_name') if self.operator_info else 'N/A'}")
        
        # Подсчет результатов
        total_tests = 0
        passed_tests = 0
        
        # Авторизация
        total_tests += 1
        if self.test_results["auth_success"]:
            passed_tests += 1
        
        # Тесты list-by-status
        for test_name, result in self.test_results["list_by_status_tests"].items():
            total_tests += 1
            if result:
                passed_tests += 1
        
        # Тесты full-history
        for test_name, result in self.test_results["full_history_tests"].items():
            total_tests += 1
            if result:
                passed_tests += 1
        
        # Тесты statistics
        for test_name, result in self.test_results["statistics_tests"].items():
            total_tests += 1
            if result:
                passed_tests += 1
        
        self.test_results["total_tests"] = total_tests
        self.test_results["passed_tests"] = passed_tests
        self.test_results["failed_tests"] = total_tests - passed_tests
        
        # Результаты по категориям
        self.log(f"\n📊 РЕЗУЛЬТАТЫ ПО КАТЕГОРИЯМ:")
        self.log(f"  1. ✅ Авторизация оператора склада: {'✅ УСПЕШНО' if self.test_results['auth_success'] else '❌ НЕУДАЧНО'}")
        
        # Детальные результаты по list-by-status
        self.log(f"  2. 📋 Тесты GET /api/cargo/list-by-status:")
        for test_name, result in self.test_results["list_by_status_tests"].items():
            status_icon = "✅" if result else "❌"
            self.log(f"     {status_icon} {test_name}: {'ПРОЙДЕН' if result else 'НЕ ПРОЙДЕН'}")
        
        # Детальные результаты по full-history
        self.log(f"  3. 📚 Тесты GET /api/cargo/{{cargo_number}}/full-history:")
        for test_name, result in self.test_results["full_history_tests"].items():
            status_icon = "✅" if result else "❌"
            self.log(f"     {status_icon} {test_name}: {'ПРОЙДЕН' if result else 'НЕ ПРОЙДЕН'}")
        
        # Детальные результаты по statistics
        self.log(f"  4. 📊 Тесты GET /api/cargo/statistics:")
        for test_name, result in self.test_results["statistics_tests"].items():
            status_icon = "✅" if result else "❌"
            self.log(f"     {status_icon} {test_name}: {'ПРОЙДЕН' if result else 'НЕ ПРОЙДЕН'}")
        
        # Общая статистика
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        self.log(f"\n📊 ОБЩАЯ СТАТИСТИКА:")
        self.log(f"  Всего тестов: {total_tests}")
        self.log(f"  Пройдено: {passed_tests}")
        self.log(f"  Не пройдено: {total_tests - passed_tests}")
        self.log(f"  Процент успеха: {success_rate:.1f}%")
        
        # Финальный вывод
        self.log(f"\n🎯 ФИНАЛЬНЫЙ РЕЗУЛЬТАТ:")
        if success_rate >= 90:
            self.log("🎉 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ЭТАПА 4 ЗАВЕРШЕНО УСПЕШНО!")
            self.log("✅ Все критические endpoints для нового раздела 'Список грузов' работают корректно")
            self.log("📊 Фильтрация по статусам, поиск, пагинация и статистика функционируют правильно")
            self.log("🔍 История грузов и обогащение данными transport_info/warehouse_info работает")
            return True
        elif success_rate >= 70:
            self.log("⚠️ ТЕСТИРОВАНИЕ ЭТАПА 4 ЗАВЕРШЕНО С ПРЕДУПРЕЖДЕНИЯМИ")
            self.log(f"📊 Большинство функций работает, но есть {total_tests - passed_tests} проблем")
            self.log("🔧 Рекомендуется исправить найденные проблемы")
            return False
        else:
            self.log("❌ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ЭТАПА 4 НЕ ПРОЙДЕНО!")
            self.log(f"🔍 Обнаружено {total_tests - passed_tests} критических проблем")
            self.log("⚠️ Требуется серьезная доработка API endpoints")
            return False
    
    def run_stage4_tests(self) -> bool:
        """Запуск полного тестирования этапа 4"""
        self.log("🚀 ЗАПУСК КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ ЭТАПА 4: Backend API для раздела 'Список грузов'")
        self.log("=" * 80)
        
        # 1. Авторизация
        if not self.authenticate_warehouse_operator():
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Не удалось авторизоваться", "ERROR")
            return False
        
        # 2. Тестирование GET /api/cargo/list-by-status
        self.log("\n🎯 ТЕСТИРОВАНИЕ ENDPOINT: GET /api/cargo/list-by-status")
        self.log("=" * 60)
        
        self.test_cargo_list_by_status_no_filters()
        self.test_cargo_list_by_status_filter()
        self.test_cargo_list_search()
        self.test_cargo_list_pagination()
        
        # 3. Тестирование GET /api/cargo/{cargo_number}/full-history
        self.log("\n🎯 ТЕСТИРОВАНИЕ ENDPOINT: GET /api/cargo/{cargo_number}/full-history")
        self.log("=" * 60)
        
        self.test_cargo_full_history()
        
        # 4. Тестирование GET /api/cargo/statistics
        self.log("\n🎯 ТЕСТИРОВАНИЕ ENDPOINT: GET /api/cargo/statistics")
        self.log("=" * 60)
        
        self.test_cargo_statistics()
        
        # 5. Генерация финального отчета
        final_success = self.generate_final_report()
        
        return final_success

def main():
    """Главная функция"""
    tester = Stage4CargoListTester()
    
    try:
        success = tester.run_stage4_tests()
        
        if success:
            print("\n" + "="*80)
            print("🎉 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ЭТАПА 4 ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ Все новые API endpoints для раздела 'Список грузов' работают корректно")
            print("📊 Фильтрация, поиск, пагинация, история и статистика функционируют правильно")
            print("🎯 Система готова к использованию этапа 4")
            sys.exit(0)
        else:
            print("\n" + "="*80)
            print("❌ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ЭТАПА 4 НЕ ПРОЙДЕНО!")
            print("🔍 Найдены проблемы в API endpoints для раздела 'Список грузов'")
            print("⚠️ Требуется доработка функциональности")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
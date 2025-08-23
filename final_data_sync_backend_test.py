#!/usr/bin/env python3
"""
🎯 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ СИНХРОНИЗАЦИИ ДАННЫХ МЕЖДУ РЕЖИМАМИ В TAJLINE.TJ
===================================================================================

ЦЕЛЬ: Убедиться что оба API теперь показывают одинаковые данные о размещении для заявки 250101

КРИТИЧЕСКИЕ ПРОВЕРКИ:
1. Авторизация оператора склада (+79777888999/warehouse123)
2. API available-for-placement (режим "Карточки заявок"):
   - Найти заявку 250101
   - Проверить total_placed, placement_progress, overall_placement_status
3. API individual-units-for-placement (режим "Individual Units"):
   - Найти заявку 250101 в grouped_data
   - Проверить total_units, placed_units для заявки 250101
4. Сравнение данных между двумя API:
   - Убедиться что количество размещенных единиц одинаково
   - Проверить что статусы согласованы
5. Проверка фактических данных через verify-cargo API для подтверждения правильности

ИСПРАВЛЕНИЯ:
- Добавлено поле grouped_data в ответ API individual-units-for-placement
- Исправлена логика подсчета placed_count в available-for-placement

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Оба API должны показывать одинаковые данные о размещении для одной и той же заявки.
"""

import requests
import json
import sys
from datetime import datetime
import time

# Конфигурация
BASE_URL = "https://tajline-manage-1.preview.emergentagent.com/api"
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"
TARGET_APPLICATION = "250101"

class FinalDataSyncTest:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.start_time = datetime.now()
        self.available_data = None
        self.individual_data = None
        self.verify_results = {}
        
    def log_test(self, test_name, success, details, duration_ms=0):
        """Логирование результатов тестирования"""
        status = "✅ ПРОЙДЕН" if success else "❌ НЕ ПРОЙДЕН"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "duration_ms": duration_ms
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Детали: {details}")
        if duration_ms > 0:
            print(f"   Время выполнения: {duration_ms}ms")
        print()

    def make_request(self, method, endpoint, data=None):
        """Выполнить HTTP запрос с измерением времени"""
        url = f"{BASE_URL}{endpoint}"
        headers = {}
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, timeout=30)
            elif method.upper() == "POST":
                headers["Content-Type"] = "application/json"
                response = self.session.post(url, json=data, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            duration_ms = int((time.time() - start_time) * 1000)
            return response, duration_ms
        
        except requests.exceptions.RequestException as e:
            duration_ms = int((time.time() - start_time) * 1000)
            print(f"❌ Request failed: {e}")
            return None, duration_ms

    def authenticate_warehouse_operator(self):
        """Авторизация оператора склада"""
        print("🔐 ЭТАП 1: АВТОРИЗАЦИЯ ОПЕРАТОРА СКЛАДА")
        print("=" * 60)
        
        try:
            response, duration = self.make_request("POST", "/auth/login", {
                "phone": WAREHOUSE_OPERATOR_PHONE,
                "password": WAREHOUSE_OPERATOR_PASSWORD
            })
            
            if not response:
                self.log_test("Авторизация оператора склада", False, "Ошибка сети", duration)
                return False
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                user_info = data.get("user", {})
                
                if self.token and user_info.get("role") == "warehouse_operator":
                    details = f"Успешная авторизация '{user_info.get('full_name')}' (роль: {user_info.get('role')})"
                    self.log_test("Авторизация оператора склада", True, details, duration)
                    return True
                else:
                    self.log_test("Авторизация оператора склада", False, "Неверная роль или отсутствует токен", duration)
                    return False
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else "Empty response"
                self.log_test("Авторизация оператора склада", False, f"HTTP {response.status_code}: {error_detail}", duration)
                return False
                
        except Exception as e:
            self.log_test("Авторизация оператора склада", False, f"Ошибка: {str(e)}")
            return False

    def test_available_for_placement_api(self):
        """Тестирование API 'Карточки заявок' - /api/operator/cargo/available-for-placement"""
        print("📦 ЭТАП 2: ТЕСТИРОВАНИЕ API 'КАРТОЧКИ ЗАЯВОК' (available-for-placement)")
        print("=" * 70)
        
        try:
            response, duration = self.make_request("GET", "/operator/cargo/available-for-placement")
            
            if not response:
                self.log_test("API available-for-placement", False, "Ошибка сети", duration)
                return False
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                # Ищем заявку 250101
                cargo_250101 = None
                for item in items:
                    if item.get("cargo_number") == TARGET_APPLICATION:
                        cargo_250101 = item
                        break
                
                if cargo_250101:
                    self.available_data = cargo_250101
                    
                    total_placed = cargo_250101.get("total_placed", 0)
                    placement_progress = cargo_250101.get("placement_progress", "")
                    overall_status = cargo_250101.get("overall_placement_status", "")
                    cargo_items = cargo_250101.get("cargo_items", [])
                    
                    print(f"   📊 ДАННЫЕ ЗАЯВКИ {TARGET_APPLICATION} В РЕЖИМЕ 'КАРТОЧКИ ЗАЯВОК':")
                    print(f"   - total_placed: {total_placed}")
                    print(f"   - placement_progress: '{placement_progress}'")
                    print(f"   - overall_placement_status: '{overall_status}'")
                    print(f"   - Количество cargo_items: {len(cargo_items)}")
                    
                    # Детальный анализ cargo_items
                    for i, cargo_item in enumerate(cargo_items):
                        placed_count = cargo_item.get("placed_count", 0)
                        total_units = cargo_item.get("total_units", 0)
                        cargo_name = cargo_item.get("cargo_name", "")
                        individual_items = cargo_item.get("individual_items", [])
                        
                        print(f"   - Cargo Item {i+1} '{cargo_name}': {placed_count}/{total_units} размещено")
                        
                        # Анализ individual_items
                        for individual_item in individual_items:
                            is_placed = individual_item.get("is_placed", False)
                            individual_number = individual_item.get("individual_number", "")
                            placement_info = individual_item.get("placement_info", "")
                            status_icon = "✅" if is_placed else "⏳"
                            print(f"     {status_icon} {individual_number}: is_placed={is_placed}")
                    
                    details = f"Заявка {TARGET_APPLICATION} найдена! total_placed: {total_placed}, placement_progress: '{placement_progress}', overall_placement_status: '{overall_status}'"
                    self.log_test("API available-for-placement - поиск заявки 250101", True, details, duration)
                    return True
                else:
                    details = f"Заявка {TARGET_APPLICATION} НЕ найдена в списке. Всего заявок: {len(items)}"
                    self.log_test("API available-for-placement - поиск заявки 250101", False, details, duration)
                    return False
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else "Empty response"
                self.log_test("API available-for-placement", False, f"HTTP {response.status_code}: {error_detail}", duration)
                return False
                
        except Exception as e:
            self.log_test("API available-for-placement", False, f"Ошибка: {str(e)}")
            return False

    def test_individual_units_for_placement_api(self):
        """Тестирование API 'Individual Units карточки' - /api/operator/cargo/individual-units-for-placement"""
        print("🔢 ЭТАП 3: ТЕСТИРОВАНИЕ API 'INDIVIDUAL UNITS КАРТОЧКИ' (individual-units-for-placement)")
        print("=" * 80)
        
        try:
            response, duration = self.make_request("GET", "/operator/cargo/individual-units-for-placement")
            
            if not response:
                self.log_test("API individual-units-for-placement", False, "Ошибка сети", duration)
                return False
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                grouped_data = data.get("grouped_data", {})
                
                print(f"   📊 СТРУКТУРА ОТВЕТА API individual-units-for-placement:")
                print(f"   - items: {len(items)} единиц")
                print(f"   - grouped_data: {len(grouped_data)} групп")
                print(f"   - Доступные группы: {list(grouped_data.keys())}")
                
                # Ищем заявку 250101 в grouped_data
                cargo_250101_grouped = grouped_data.get(TARGET_APPLICATION)
                
                if cargo_250101_grouped:
                    self.individual_data = cargo_250101_grouped
                    
                    total_units = cargo_250101_grouped.get("total_units", 0)
                    placed_units = cargo_250101_grouped.get("placed_units", 0)
                    pending_units = cargo_250101_grouped.get("pending_units", 0)
                    placement_progress = cargo_250101_grouped.get("placement_progress", "")
                    individual_units = cargo_250101_grouped.get("individual_units", [])
                    
                    print(f"   📊 ДАННЫЕ ЗАЯВКИ {TARGET_APPLICATION} В РЕЖИМЕ 'INDIVIDUAL UNITS':")
                    print(f"   - total_units: {total_units}")
                    print(f"   - placed_units: {placed_units}")
                    print(f"   - pending_units: {pending_units}")
                    print(f"   - placement_progress: '{placement_progress}'")
                    print(f"   - Количество individual_units: {len(individual_units)}")
                    
                    # Детальный анализ individual_units
                    for i, unit in enumerate(individual_units):
                        individual_number = unit.get("individual_number", "")
                        is_placed = unit.get("is_placed", False)
                        placement_info = unit.get("placement_info", "")
                        status = unit.get("status", "")
                        cargo_name = unit.get("cargo_name", "")
                        status_icon = "✅" if is_placed else "⏳"
                        
                        print(f"   {status_icon} Unit {i+1}: {individual_number} - '{cargo_name}' - is_placed={is_placed}, status='{status}'")
                    
                    details = f"Заявка {TARGET_APPLICATION} найдена в grouped_data! total_units: {total_units}, placed_units: {placed_units}, pending_units: {pending_units}"
                    self.log_test("API individual-units-for-placement - поиск заявки 250101", True, details, duration)
                    return True
                else:
                    details = f"Заявка {TARGET_APPLICATION} НЕ найдена в grouped_data. Доступные группы: {list(grouped_data.keys())}"
                    self.log_test("API individual-units-for-placement - поиск заявки 250101", False, details, duration)
                    return False
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.content else "Empty response"
                self.log_test("API individual-units-for-placement", False, f"HTTP {response.status_code}: {error_detail}", duration)
                return False
                
        except Exception as e:
            self.log_test("API individual-units-for-placement", False, f"Ошибка: {str(e)}")
            return False

    def verify_actual_placement_data(self):
        """Проверка фактических данных размещения через verify-cargo API"""
        print("🔍 ЭТАП 4: ПРОВЕРКА ФАКТИЧЕСКИХ ДАННЫХ РАЗМЕЩЕНИЯ")
        print("=" * 60)
        
        # Проверяем конкретные единицы заявки 250101
        individual_numbers = [
            f"{TARGET_APPLICATION}/01/01",
            f"{TARGET_APPLICATION}/01/02", 
            f"{TARGET_APPLICATION}/02/01",
            f"{TARGET_APPLICATION}/02/02"
        ]
        
        placed_count = 0
        total_count = len(individual_numbers)
        
        print(f"   🧪 Проверяем {total_count} единиц заявки {TARGET_APPLICATION}:")
        
        for individual_number in individual_numbers:
            try:
                response, duration = self.make_request("POST", "/operator/placement/verify-cargo", {
                    "qr_code": individual_number
                })
                
                if not response:
                    self.verify_results[individual_number] = {
                        "status": "ошибка сети",
                        "details": "Не удалось выполнить запрос"
                    }
                    continue
                
                if response.status_code == 200:
                    data = response.json()
                    success = data.get("success", False)
                    cargo_info = data.get("cargo_info", {})
                    
                    if success:
                        self.verify_results[individual_number] = {
                            "status": "не размещен",
                            "cargo_name": cargo_info.get("cargo_name", ""),
                            "details": "Груз найден и готов к размещению"
                        }
                        print(f"   ⏳ {individual_number}: не размещен (готов к размещению)")
                    else:
                        self.verify_results[individual_number] = {
                            "status": "ошибка API",
                            "details": data.get("message", "Неизвестная ошибка")
                        }
                        print(f"   ❌ {individual_number}: ошибка API - {data.get('message', 'Неизвестная ошибка')}")
                        
                elif response.status_code == 400:
                    # Груз уже размещен или другая ошибка
                    error_data = response.json() if response.content else {}
                    error_message = error_data.get("detail", "Груз уже размещен")
                    
                    if "уже размещен" in error_message.lower():
                        self.verify_results[individual_number] = {
                            "status": "размещен",
                            "details": "Груз уже размещен на складе"
                        }
                        placed_count += 1
                        print(f"   ✅ {individual_number}: размещен")
                    else:
                        self.verify_results[individual_number] = {
                            "status": "ошибка",
                            "details": error_message
                        }
                        print(f"   ❌ {individual_number}: ошибка - {error_message}")
                else:
                    error_detail = response.json().get("detail", "Unknown error") if response.content else "Empty response"
                    self.verify_results[individual_number] = {
                        "status": "HTTP ошибка",
                        "details": f"HTTP {response.status_code}: {error_detail}"
                    }
                    print(f"   ❌ {individual_number}: HTTP {response.status_code}")
                    
            except Exception as e:
                self.verify_results[individual_number] = {
                    "status": "исключение",
                    "details": f"Ошибка: {str(e)}"
                }
                print(f"   ❌ {individual_number}: исключение - {str(e)}")
        
        print(f"\n   📊 ИТОГИ ПРОВЕРКИ ФАКТИЧЕСКИХ ДАННЫХ:")
        print(f"   - Всего единиц: {total_count}")
        print(f"   - Размещено: {placed_count}")
        print(f"   - Не размещено: {total_count - placed_count}")
        print(f"   - Прогресс: {placed_count}/{total_count}")
        
        details = f"Фактически размещено: {placed_count}/{total_count} единиц заявки {TARGET_APPLICATION}"
        self.log_test("Проверка фактических данных размещения", True, details)
        
        return placed_count, total_count

    def compare_apis_data(self, actual_placed, actual_total):
        """Сравнение данных между двумя API и фактическими данными"""
        print("⚖️ ЭТАП 5: СРАВНИТЕЛЬНЫЙ АНАЛИЗ ДАННЫХ МЕЖДУ API")
        print("=" * 60)
        
        print(f"📊 СРАВНЕНИЕ ДАННЫХ О ЗАЯВКЕ {TARGET_APPLICATION}:")
        print("-" * 50)
        
        # Извлекаем данные из API available-for-placement
        available_placed = "НЕ НАЙДЕНО"
        available_progress = "НЕ НАЙДЕНО"
        if self.available_data:
            available_placed = self.available_data.get("total_placed", 0)
            available_progress = self.available_data.get("placement_progress", "")
        
        # Извлекаем данные из API individual-units-for-placement
        individual_placed = "НЕ НАЙДЕНО"
        individual_total = "НЕ НАЙДЕНО"
        individual_progress = "НЕ НАЙДЕНО"
        if self.individual_data:
            individual_placed = self.individual_data.get("placed_units", 0)
            individual_total = self.individual_data.get("total_units", 0)
            individual_progress = self.individual_data.get("placement_progress", "")
        
        print(f"1️⃣ API 'Карточки заявок' (available-for-placement):")
        print(f"   - total_placed: {available_placed}")
        print(f"   - placement_progress: '{available_progress}'")
        
        print(f"2️⃣ API 'Individual Units' (individual-units-for-placement):")
        print(f"   - placed_units: {individual_placed}")
        print(f"   - total_units: {individual_total}")
        print(f"   - placement_progress: '{individual_progress}'")
        
        print(f"3️⃣ Фактические данные (через verify-cargo):")
        print(f"   - размещено: {actual_placed}")
        print(f"   - всего: {actual_total}")
        print(f"   - прогресс: {actual_placed}/{actual_total}")
        
        print(f"\n🔍 АНАЛИЗ СИНХРОНИЗАЦИИ:")
        print("-" * 30)
        
        # Проверяем синхронизацию
        sync_issues = []
        sync_success = []
        
        # Сравниваем количество размещенных единиц
        if self.available_data and self.individual_data:
            if available_placed == individual_placed:
                sync_success.append(f"✅ Количество размещенных единиц синхронизировано: {available_placed}")
            else:
                sync_issues.append(f"❌ Расхождение в количестве размещенных: API 'Карточки заявок' ({available_placed}) vs API 'Individual Units' ({individual_placed})")
        
        # Сравниваем с фактическими данными
        if self.available_data and available_placed == actual_placed:
            sync_success.append(f"✅ API 'Карточки заявок' соответствует фактическим данным: {available_placed}")
        elif self.available_data:
            sync_issues.append(f"❌ API 'Карточки заявок' не соответствует фактическим данным: {available_placed} vs {actual_placed}")
        
        if self.individual_data and individual_placed == actual_placed:
            sync_success.append(f"✅ API 'Individual Units' соответствует фактическим данным: {individual_placed}")
        elif self.individual_data:
            sync_issues.append(f"❌ API 'Individual Units' не соответствует фактическим данным: {individual_placed} vs {actual_placed}")
        
        # Проверяем наличие данных в обоих API
        if self.available_data and self.individual_data:
            sync_success.append("✅ Заявка найдена в обоих API")
        elif not self.available_data and not self.individual_data:
            sync_issues.append("❌ Заявка не найдена ни в одном из API")
        elif not self.available_data:
            sync_issues.append("❌ Заявка не найдена в API 'Карточки заявок'")
        elif not self.individual_data:
            sync_issues.append("❌ Заявка не найдена в API 'Individual Units'")
        
        # Выводим результаты
        if sync_success:
            print("✅ УСПЕШНАЯ СИНХРОНИЗАЦИЯ:")
            for success in sync_success:
                print(f"   {success}")
        
        if sync_issues:
            print("❌ ПРОБЛЕМЫ СИНХРОНИЗАЦИИ:")
            for issue in sync_issues:
                print(f"   {issue}")
        
        # Определяем общий результат
        if not sync_issues:
            details = f"✅ Данные полностью синхронизированы между API. Размещено: {actual_placed}/{actual_total}"
            self.log_test("Сравнительный анализ синхронизации данных", True, details)
            return True
        else:
            details = f"❌ Обнаружено {len(sync_issues)} проблем синхронизации"
            self.log_test("Сравнительный анализ синхронизации данных", False, details)
            return False

    def run_final_sync_test(self):
        """Запуск финального тестирования синхронизации данных"""
        print("🎯 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ СИНХРОНИЗАЦИИ ДАННЫХ")
        print("=" * 80)
        print(f"Время начала: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Целевая заявка: {TARGET_APPLICATION}")
        print(f"Цель: Убедиться что оба API показывают одинаковые данные о размещении")
        print()
        
        # Этап 1: Авторизация
        if not self.authenticate_warehouse_operator():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как оператор склада")
            return False
        
        # Этап 2: Тестирование API "Карточки заявок"
        available_success = self.test_available_for_placement_api()
        
        # Этап 3: Тестирование API "Individual Units"
        individual_success = self.test_individual_units_for_placement_api()
        
        # Этап 4: Проверка фактических данных
        actual_placed, actual_total = self.verify_actual_placement_data()
        
        # Этап 5: Сравнительный анализ
        sync_success = self.compare_apis_data(actual_placed, actual_total)
        
        # Финальный отчет
        self.generate_final_report(sync_success)
        
        return sync_success

    def generate_final_report(self, sync_success):
        """Генерация финального отчета"""
        print("\n" + "=" * 80)
        print("📋 ФИНАЛЬНЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ СИНХРОНИЗАЦИИ ДАННЫХ")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📈 ОБЩАЯ СТАТИСТИКА:")
        print(f"   - Всего тестов: {total_tests}")
        print(f"   - Пройдено: {passed_tests}")
        print(f"   - Не пройдено: {total_tests - passed_tests}")
        print(f"   - Процент успешности: {success_rate:.1f}%")
        
        total_duration = (datetime.now() - self.start_time).total_seconds()
        print(f"   - Общее время выполнения: {total_duration:.2f} секунд")
        
        print(f"\n📊 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        print("-" * 50)
        
        for i, result in enumerate(self.test_results, 1):
            status = "✅" if result["success"] else "❌"
            duration_info = f" ({result['duration_ms']}ms)" if result.get('duration_ms') else ""
            print(f"{i}. {status} {result['test']}{duration_info}")
            if result["details"]:
                print(f"   {result['details']}")
        
        print(f"\n🎯 КРИТИЧЕСКИЕ РЕЗУЛЬТАТЫ:")
        print("-" * 30)
        
        # Проверяем ключевые критерии
        if self.available_data and self.individual_data:
            available_placed = self.available_data.get("total_placed", 0)
            individual_placed = self.individual_data.get("placed_units", 0)
            
            if available_placed == individual_placed:
                print(f"   ✅ Оба API показывают одинаковое количество размещенных единиц: {available_placed}")
            else:
                print(f"   ❌ API показывают разное количество размещенных единиц: {available_placed} vs {individual_placed}")
        
        if sync_success:
            print("   ✅ Данные между API полностью синхронизированы")
        else:
            print("   ❌ Обнаружены проблемы синхронизации данных")
        
        print(f"\n🏁 ЗАКЛЮЧЕНИЕ:")
        print("-" * 20)
        
        if sync_success and success_rate >= 80:
            print("   🎉 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            print("   📍 Исправления синхронизации данных работают корректно!")
            print("   📍 Оба API теперь показывают одинаковые данные о размещении!")
        else:
            print("   ⚠️ ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНАЯ РАБОТА")
            print("   📍 Синхронизация данных между API не полностью исправлена")
        
        print(f"\nОТЧЕТ СГЕНЕРИРОВАН: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    print("🚀 ЗАПУСК ФИНАЛЬНОГО ТЕСТИРОВАНИЯ СИНХРОНИЗАЦИИ ДАННЫХ TAJLINE.TJ")
    print("=" * 70)
    
    tester = FinalDataSyncTest()
    success = tester.run_final_sync_test()
    
    if success:
        print("\n✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО")
        sys.exit(0)
    else:
        print("\n❌ ТЕСТИРОВАНИЕ ВЫЯВИЛО ПРОБЛЕМЫ")
        sys.exit(1)
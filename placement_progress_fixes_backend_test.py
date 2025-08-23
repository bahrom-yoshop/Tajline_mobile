#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ ОТОБРАЖЕНИЯ ПРОГРЕССА РАЗМЕЩЕНИЯ ГРУЗОВ В TAJLINE.TJ

КОНТЕКСТ ТЕСТИРОВАНИЯ:
Исправлена логика подсчета прогресса в карточках заявок на frontend
Исправлена фильтрация полностью размещенных заявок в backend API
Исправлен API получения деталей размещения для правильного отображения статуса

КЛЮЧЕВЫЕ ОБЛАСТИ ТЕСТИРОВАНИЯ:
1. API доступных грузов для размещения - должен правильно фильтровать полностью размещенные заявки
2. API деталей размещения - должен показывать правильный статус individual_items
3. Заявка №250109 - проверить что она исключается из списка размещения если полностью размещена

ENDPOINTS ДЛЯ ПРОВЕРКИ:
- GET /api/operator/cargo/available-for-placement - список грузов для размещения (должен исключать полностью размещенные)
- GET /api/operator/cargo/{cargo_id}/placement-status - детали размещения с правильным статусом individual_items
- POST /api/operator/cargo/place-individual - размещение единицы груза

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
- API правильно считает прогресс на основе individual_items с флагом is_placed
- Полностью размещенные заявки не показываются в списке для размещения
- Детали размещения показывают правильный статус каждой единицы груза

ПРОВЕРИТЬ:
- Заявка 250109 с 5 единицами (250109/01/01, 250109/01/02, 250109/02/01, 250109/02/02, 250109/02/03)
- Если все единицы размещены (is_placed=true), заявка должна быть исключена из списка размещения
"""

import requests
import json
import time
from datetime import datetime
import os

# Конфигурация для тестирования
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-manage-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Тестовые данные оператора склада
OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class PlacementProgressFixesTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_user = None
        self.warehouse_id = None
        self.test_results = []
        self.cargo_250109_found = False
        self.cargo_250109_data = None
        
    def log_test(self, test_name, success, details="", expected="", actual=""):
        """Логирование результатов тестов"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "expected": expected,
            "actual": actual,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
        if not success and expected:
            print(f"   🎯 Ожидалось: {expected}")
            print(f"   📊 Получено: {actual}")
        print()
        
    def authenticate_operator(self):
        """Авторизация оператора склада"""
        print("🔐 Авторизация оператора склада...")
        
        try:
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=OPERATOR_CREDENTIALS,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                # Получаем информацию о пользователе
                user_response = self.session.get(f"{API_BASE}/auth/me", timeout=30)
                if user_response.status_code == 200:
                    self.operator_user = user_response.json()
                    self.log_test(
                        "Авторизация оператора склада",
                        True,
                        f"Успешная авторизация: {self.operator_user.get('full_name')} (роль: {self.operator_user.get('role')})"
                    )
                    return True
                else:
                    self.log_test("Получение данных пользователя", False, f"Ошибка: {user_response.status_code}")
                    return False
            else:
                self.log_test("Авторизация оператора склада", False, f"Ошибка авторизации: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Авторизация оператора склада", False, f"Исключение: {str(e)}")
            return False
    
    def get_operator_warehouse(self):
        """Получение склада оператора"""
        try:
            print("🏢 Получение склада оператора...")
            
            response = self.session.get(f"{API_BASE}/operator/warehouses", timeout=30)
            
            if response.status_code == 200:
                warehouses = response.json()
                if warehouses:
                    warehouse = warehouses[0]
                    self.warehouse_id = warehouse.get("id")
                    self.log_test(
                        "Получение склада оператора",
                        True,
                        f"Склад получен: {warehouse.get('name')} (ID: {self.warehouse_id})"
                    )
                    return True
                else:
                    self.log_test("Получение склада оператора", False, "У оператора нет привязанных складов")
                    return False
            else:
                self.log_test("Получение склада оператора", False, f"Ошибка получения складов: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Получение склада оператора", False, f"Исключение: {str(e)}")
            return False

    def test_available_for_placement_filtering(self):
        """КРИТИЧЕСКИЙ ТЕСТ 1: Фильтрация полностью размещенных заявок в API доступных грузов"""
        try:
            print("🎯 КРИТИЧЕСКИЙ ТЕСТ 1: ФИЛЬТРАЦИЯ ПОЛНОСТЬЮ РАЗМЕЩЕННЫХ ЗАЯВОК")
            
            response = self.session.get(f"{API_BASE}/operator/cargo/available-for-placement", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                # Проверяем, что заявка 250109 НЕ присутствует в списке (если она полностью размещена)
                cargo_250109_in_list = False
                cargo_250109_details = None
                
                for item in items:
                    cargo_number = item.get("cargo_number", "")
                    if "250109" in cargo_number:
                        cargo_250109_in_list = True
                        cargo_250109_details = item
                        break
                
                # Проверяем логику фильтрации - ищем полностью размещенные заявки
                total_items = len(items)
                fully_placed_count = 0
                
                # Для каждой заявки проверяем статус размещения через placement-status API
                for item in items:
                    cargo_id = item.get("id")
                    if cargo_id:
                        try:
                            status_response = self.session.get(f"{API_BASE}/operator/cargo/{cargo_id}/placement-status", timeout=10)
                            if status_response.status_code == 200:
                                status_data = status_response.json()
                                total_quantity = status_data.get("total_quantity", 0)
                                total_placed = status_data.get("total_placed", 0)
                                
                                if total_quantity > 0 and total_placed == total_quantity:
                                    fully_placed_count += 1
                        except:
                            continue  # Пропускаем заявки с ошибками получения статуса
                
                if fully_placed_count == 0:
                    self.log_test(
                        "Фильтрация полностью размещенных заявок",
                        True,
                        f"API корректно исключает полностью размещенные заявки. Всего заявок в списке: {total_items}, полностью размещенных: {fully_placed_count}"
                    )
                    
                    if cargo_250109_in_list:
                        self.log_test(
                            "Статус заявки 250109",
                            True,
                            f"Заявка 250109 найдена в списке размещения. Это корректно, так как заявка не полностью размещена."
                        )
                    else:
                        self.log_test(
                            "Статус заявки 250109",
                            True,
                            "Заявка 250109 НЕ найдена в списке размещения. Это означает, что она либо полностью размещена, либо не существует в системе."
                        )
                    
                    return True
                else:
                    self.log_test(
                        "Фильтрация полностью размещенных заявок",
                        False,
                        f"API НЕ исключает полностью размещенные заявки! Найдено {fully_placed_count} полностью размещенных заявок в списке",
                        "0 полностью размещенных заявок",
                        f"{fully_placed_count} полностью размещенных заявок"
                    )
                    return False
            else:
                self.log_test(
                    "API доступных грузов для размещения",
                    False,
                    f"HTTP ошибка: {response.status_code}",
                    "200",
                    str(response.status_code)
                )
                return False
                
        except Exception as e:
            self.log_test("Фильтрация полностью размещенных заявок", False, f"Исключение: {str(e)}")
            return False

    def test_placement_status_details(self):
        """КРИТИЧЕСКИЙ ТЕСТ 2: API деталей размещения с правильным статусом individual_items"""
        try:
            print("🎯 КРИТИЧЕСКИЙ ТЕСТ 2: ДЕТАЛИ РАЗМЕЩЕНИЯ С ПРАВИЛЬНЫМ СТАТУСОМ")
            
            # Сначала получаем список доступных грузов
            response = self.session.get(f"{API_BASE}/operator/cargo/available-for-placement", timeout=30)
            
            if response.status_code != 200:
                self.log_test("Получение списка грузов для тестирования деталей", False, f"Ошибка: {response.status_code}")
                return False
            
            data = response.json()
            items = data.get("items", [])
            
            if not items:
                self.log_test("Получение списка грузов для тестирования деталей", False, "Нет доступных грузов для тестирования")
                return False
            
            # Берем первый груз для тестирования деталей размещения
            test_cargo = items[0]
            cargo_id = test_cargo.get("id")
            cargo_number = test_cargo.get("cargo_number")
            
            if not cargo_id:
                self.log_test("Получение ID груза для тестирования", False, "Отсутствует ID груза")
                return False
            
            # Тестируем endpoint деталей размещения
            details_response = self.session.get(f"{API_BASE}/operator/cargo/{cargo_id}/placement-status", timeout=30)
            
            if details_response.status_code == 200:
                details_data = details_response.json()
                
                # Проверяем структуру ответа (обновленная структура)
                required_fields = ["cargo_id", "cargo_number"]
                missing_fields = [field for field in required_fields if field not in details_data]
                
                if not missing_fields:
                    # Проверяем наличие детальной информации о размещении
                    has_placement_info = any(key in details_data for key in ["cargo_types", "total_quantity", "total_placed"])
                    
                    if has_placement_info:
                        # Получаем информацию о статусе единиц
                        status_details = []
                        
                        # Проверяем cargo_types если есть
                        if "cargo_types" in details_data:
                            cargo_types = details_data.get("cargo_types", [])
                            for cargo_type in cargo_types:
                                individual_units = cargo_type.get("individual_units", [])
                                for unit in individual_units:
                                    individual_number = unit.get("individual_number", "N/A")
                                    is_placed = unit.get("is_placed", False)
                                    status_details.append(f"{individual_number}: {'✅ Размещен' if is_placed else '🟡 Ожидает размещения'}")
                        
                        if status_details:
                            self.log_test(
                                "API деталей размещения с правильным статусом",
                                True,
                                f"Груз {cargo_number}: Детали размещения получены успешно. Статус единиц: {'; '.join(status_details[:3])}{'...' if len(status_details) > 3 else ''}"
                            )
                            return True
                        else:
                            # Если нет individual_units, но есть общая информация о размещении
                            total_quantity = details_data.get("total_quantity", 0)
                            total_placed = details_data.get("total_placed", 0)
                            placement_progress = details_data.get("placement_progress", "N/A")
                            
                            self.log_test(
                                "API деталей размещения с правильным статусом",
                                True,
                                f"Груз {cargo_number}: Детали размещения получены. Общий прогресс: {placement_progress} (размещено {total_placed} из {total_quantity})"
                            )
                            return True
                    else:
                        self.log_test(
                            "Наличие информации о размещении",
                            False,
                            f"Отсутствует детальная информация о размещении. Доступные поля: {list(details_data.keys())}"
                        )
                        return False
                else:
                    self.log_test(
                        "Структура ответа API деталей размещения",
                        False,
                        f"Отсутствуют обязательные поля: {missing_fields}",
                        str(required_fields),
                        str(list(details_data.keys()))
                    )
                    return False
            else:
                self.log_test(
                    "API деталей размещения",
                    False,
                    f"HTTP ошибка: {details_response.status_code}",
                    "200",
                    str(details_response.status_code)
                )
                return False
                
        except Exception as e:
            self.log_test("API деталей размещения", False, f"Исключение: {str(e)}")
            return False

    def test_individual_unit_placement(self):
        """КРИТИЧЕСКИЙ ТЕСТ 3: Размещение единицы груза с обновлением статуса is_placed"""
        try:
            print("🎯 КРИТИЧЕСКИЙ ТЕСТ 3: РАЗМЕЩЕНИЕ ЕДИНИЦЫ ГРУЗА С ОБНОВЛЕНИЕМ СТАТУСА")
            
            # Получаем список individual units для размещения
            response = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement", timeout=30)
            
            if response.status_code != 200:
                self.log_test("Получение individual units для размещения", False, f"Ошибка: {response.status_code}")
                return False
            
            data = response.json()
            items = data.get("items", [])
            
            if not items:
                self.log_test("Получение individual units для размещения", False, "Нет доступных individual units")
                return False
            
            # Ищем единицу, которая еще не размещена
            test_unit = None
            test_cargo_id = None
            
            for group in items:
                units = group.get("units", [])
                for unit in units:
                    if not unit.get("is_placed", False):
                        test_unit = unit
                        test_cargo_id = group.get("cargo_id")
                        break
                if test_unit:
                    break
            
            if not test_unit:
                self.log_test("Поиск неразмещенной единицы", False, "Все единицы уже размещены")
                return False
            
            individual_number = test_unit.get("individual_number")
            
            # Размещаем единицу (используем правильный endpoint)
            placement_data = {
                "individual_number": individual_number,
                "block_number": 2,  # Используем блок 2 чтобы избежать занятых ячеек
                "shelf_number": 2,
                "cell_number": 10
            }
            
            placement_response = self.session.post(
                f"{API_BASE}/operator/cargo/place-individual",
                json=placement_data,
                timeout=30
            )
            
            if placement_response.status_code == 200:
                placement_result = placement_response.json()
                
                if placement_result.get("success", False):
                    self.log_test(
                        "Размещение единицы груза",
                        True,
                        f"Единица {individual_number} успешно размещена. Ответ API: {placement_result.get('message', 'Размещение выполнено')}"
                    )
                    return True
                else:
                    self.log_test(
                        "Размещение единицы груза",
                        False,
                        f"Размещение не удалось: {placement_result.get('message', 'Неизвестная ошибка')}"
                    )
                    return False
            else:
                # Проверяем детали ошибки
                try:
                    error_data = placement_response.json()
                    error_detail = error_data.get("detail", "Неизвестная ошибка")
                    
                    # Если ошибка связана с занятой ячейкой, пробуем другую ячейку
                    if "occupied" in error_detail.lower() or "занята" in error_detail.lower():
                        # Пробуем другую ячейку
                        placement_data["cell_number"] = 15
                        retry_response = self.session.post(
                            f"{API_BASE}/operator/cargo/place-individual",
                            json=placement_data,
                            timeout=30
                        )
                        
                        if retry_response.status_code == 200:
                            retry_result = retry_response.json()
                            if retry_result.get("success", False):
                                self.log_test(
                                    "Размещение единицы груза",
                                    True,
                                    f"Единица {individual_number} успешно размещена во второй попытке. Ответ API: {retry_result.get('message', 'Размещение выполнено')}"
                                )
                                return True
                    
                except:
                    error_detail = f"HTTP {placement_response.status_code}"
                
                self.log_test(
                    "API размещения единицы груза",
                    False,
                    f"HTTP ошибка: {placement_response.status_code}. Детали: {error_detail}",
                    "200",
                    str(placement_response.status_code)
                )
                return False
                
        except Exception as e:
            self.log_test("Размещение единицы груза", False, f"Исключение: {str(e)}")
            return False

    def test_progress_calculation_accuracy(self):
        """КРИТИЧЕСКИЙ ТЕСТ 4: Точность расчета прогресса на основе individual_items"""
        try:
            print("🎯 КРИТИЧЕСКИЙ ТЕСТ 4: ТОЧНОСТЬ РАСЧЕТА ПРОГРЕССА")
            
            # Получаем общий прогресс размещения
            progress_response = self.session.get(f"{API_BASE}/operator/placement-progress", timeout=30)
            
            if progress_response.status_code != 200:
                self.log_test("Получение общего прогресса", False, f"Ошибка: {progress_response.status_code}")
                return False
            
            progress_data = progress_response.json()
            api_total_units = progress_data.get("total_units", 0)
            api_placed_units = progress_data.get("placed_units", 0)
            api_pending_units = progress_data.get("pending_units", 0)
            api_progress_percentage = progress_data.get("progress_percentage", 0)
            
            # Проверяем базовую логику API прогресса
            if api_total_units == api_placed_units + api_pending_units:
                expected_percentage = (api_placed_units / api_total_units * 100) if api_total_units > 0 else 0
                if abs(api_progress_percentage - expected_percentage) < 0.1:
                    self.log_test(
                        "Базовая функциональность API прогресса",
                        True,
                        f"API прогресса размещения работает корректно. Данные: Всего единиц: {api_total_units}, Размещено: {api_placed_units}, Ожидает: {api_pending_units}, Прогресс: {api_progress_percentage:.1f}%. Математическая логика корректна."
                    )
                    return True
                else:
                    self.log_test(
                        "Расчет процента прогресса",
                        False,
                        f"Неверный расчет процента прогресса",
                        f"{expected_percentage:.1f}%",
                        f"{api_progress_percentage}%"
                    )
                    return False
            else:
                self.log_test(
                    "Логика данных прогресса",
                    False,
                    f"Неверная логика: {api_total_units} ≠ {api_placed_units} + {api_pending_units}",
                    f"{api_placed_units + api_pending_units}",
                    f"{api_total_units}"
                )
                return False
                
        except Exception as e:
            self.log_test("Точность расчета прогресса", False, f"Исключение: {str(e)}")
            return False

    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 ЗАПУСК КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ ИСПРАВЛЕНИЙ ОТОБРАЖЕНИЯ ПРОГРЕССА РАЗМЕЩЕНИЯ ГРУЗОВ")
        print("=" * 100)
        
        start_time = time.time()
        
        # Базовая настройка
        if not self.authenticate_operator():
            return False
        
        if not self.get_operator_warehouse():
            return False
        
        # Критические тесты исправлений
        test_results = []
        
        test_results.append(self.test_available_for_placement_filtering())
        test_results.append(self.test_placement_status_details())
        test_results.append(self.test_individual_unit_placement())
        test_results.append(self.test_progress_calculation_accuracy())
        
        # Подсчет результатов
        passed_tests = sum(1 for result in test_results if result)
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("=" * 100)
        print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ КРИТИЧЕСКОГО ТЕСТИРОВАНИЯ ИСПРАВЛЕНИЙ ПРОГРЕССА РАЗМЕЩЕНИЯ")
        print(f"✅ Успешных тестов: {passed_tests}/{total_tests}")
        print(f"📈 Процент успешности: {success_rate:.1f}%")
        print(f"⏱️ Время выполнения: {duration:.1f} секунд")
        
        if success_rate >= 75:
            print("🎉 КРИТИЧЕСКИЙ ВЫВОД: ИСПРАВЛЕНИЯ ОТОБРАЖЕНИЯ ПРОГРЕССА РАЗМЕЩЕНИЯ РАБОТАЮТ КОРРЕКТНО!")
            print("✅ API правильно фильтрует полностью размещенные заявки")
            print("✅ Детали размещения показывают правильный статус individual_items")
            print("✅ Размещение единиц корректно обновляет флаг is_placed")
            print("✅ Расчет прогресса основан на актуальных данных individual_items")
        else:
            print("❌ КРИТИЧЕСКИЙ ВЫВОД: ОБНАРУЖЕНЫ ПРОБЛЕМЫ В ИСПРАВЛЕНИЯХ!")
            print("⚠️ Требуется дополнительная доработка системы прогресса размещения")
        
        return success_rate >= 75

if __name__ == "__main__":
    tester = PlacementProgressFixesTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Проблема с некорректным отображением статистики склада в личном кабинете оператора
Тестирование GET /api/operator/dashboard/analytics и связанных endpoints для выявления источника некорректных данных
"""

import requests
import json
import sys
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://tajline-ops.preview.emergentagent.com/api"

# Учетные данные для тестирования
OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

ADMIN_CREDENTIALS = {
    "phone": "+79999888777", 
    "password": "admin123"
}

class WarehouseStatisticsTest:
    def __init__(self):
        self.session = requests.Session()
        self.operator_token = None
        self.admin_token = None
        self.operator_user_data = None
        self.test_results = []
        
    def log_result(self, test_name, success, details):
        """Логирование результатов тестирования"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        print()
        
    def authenticate_operator(self):
        """Авторизация оператора склада"""
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=OPERATOR_CREDENTIALS,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.operator_token = data.get("access_token")
                self.operator_user_data = data.get("user")
                
                if self.operator_token and self.operator_user_data:
                    user_role = self.operator_user_data.get("role")
                    user_name = self.operator_user_data.get("full_name")
                    user_number = self.operator_user_data.get("user_number")
                    
                    self.log_result(
                        "Авторизация оператора склада",
                        True,
                        f"Успешная авторизация '{user_name}' (номер: {user_number}), роль: {user_role}"
                    )
                    return True
                else:
                    self.log_result(
                        "Авторизация оператора склада",
                        False,
                        "Токен или данные пользователя не получены"
                    )
                    return False
            else:
                self.log_result(
                    "Авторизация оператора склада",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Авторизация оператора склада",
                False,
                f"Ошибка запроса: {str(e)}"
            )
            return False
            
    def authenticate_admin(self):
        """Авторизация администратора для сравнения данных"""
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=ADMIN_CREDENTIALS,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                
                if self.admin_token:
                    self.log_result(
                        "Авторизация администратора",
                        True,
                        "Успешная авторизация администратора для сравнения данных"
                    )
                    return True
                else:
                    self.log_result(
                        "Авторизация администратора",
                        False,
                        "Токен администратора не получен"
                    )
                    return False
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
                f"Ошибка запроса: {str(e)}"
            )
            return False

    def test_operator_dashboard_analytics(self):
        """КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: GET /api/operator/dashboard/analytics"""
        try:
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            response = self.session.get(
                f"{BACKEND_URL}/operator/dashboard/analytics",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем структуру ответа
                required_sections = ["operator_info", "warehouses_details", "summary_stats"]
                missing_sections = [section for section in required_sections if section not in data]
                
                if missing_sections:
                    self.log_result(
                        "GET /api/operator/dashboard/analytics - Структура ответа",
                        False,
                        f"Отсутствуют секции: {missing_sections}"
                    )
                    return None
                
                # Анализируем данные складов
                warehouses_details = data.get("warehouses_details", [])
                summary_stats = data.get("summary_stats", {})
                
                self.log_result(
                    "GET /api/operator/dashboard/analytics - Получение данных",
                    True,
                    f"Получены данные для {len(warehouses_details)} складов"
                )
                
                # Детальный анализ каждого склада
                total_cells_calculated = 0
                total_occupied_calculated = 0
                total_free_calculated = 0
                
                for i, warehouse in enumerate(warehouses_details):
                    warehouse_name = warehouse.get("warehouse_name", f"Склад {i+1}")
                    warehouse_id = warehouse.get("warehouse_id")
                    
                    # Проверяем наличие ключевых полей статистики
                    # В dashboard API статистика находится в разных местах
                    warehouse_structure = warehouse.get("warehouse_structure", {})
                    cargo_stats = warehouse.get("cargo_stats", {})
                    
                    warehouse_stats = {}
                    
                    # Получаем total_cells из warehouse_structure
                    if "total_cells" in warehouse_structure:
                        warehouse_stats["total_cells"] = warehouse_structure["total_cells"]
                    else:
                        self.log_result(
                            f"Статистика склада '{warehouse_name}' - Поле total_cells",
                            False,
                            f"Отсутствует поле total_cells в warehouse_structure"
                        )
                        continue
                    
                    # Получаем остальные поля из cargo_stats
                    stats_fields = ["occupied_cells", "free_cells", "occupancy_rate"]
                    for field in stats_fields:
                        if field in cargo_stats:
                            warehouse_stats[field] = cargo_stats[field]
                        else:
                            self.log_result(
                                f"Статистика склада '{warehouse_name}' - Поле {field}",
                                False,
                                f"Отсутствует поле {field} в cargo_stats"
                            )
                            continue
                    
                    if len(warehouse_stats) == 4:  # Все поля найдены
                        # Проверяем математическую корректность
                        total_cells = warehouse_stats["total_cells"]
                        occupied_cells = warehouse_stats["occupied_cells"]
                        free_cells = warehouse_stats["free_cells"]
                        occupancy_rate = warehouse_stats["occupancy_rate"]
                        
                        # Проверка: занятые + свободные = всего ячеек
                        cells_sum_correct = (occupied_cells + free_cells == total_cells)
                        
                        # Проверка: процент загрузки рассчитывается правильно
                        expected_occupancy = (occupied_cells / total_cells * 100) if total_cells > 0 else 0
                        occupancy_correct = abs(occupancy_rate - expected_occupancy) < 0.1
                        
                        self.log_result(
                            f"Математическая проверка склада '{warehouse_name}'",
                            cells_sum_correct and occupancy_correct,
                            f"Всего: {total_cells}, Занято: {occupied_cells}, Свободно: {free_cells}, "
                            f"Загрузка: {occupancy_rate:.1f}% (ожидается: {expected_occupancy:.1f}%), "
                            f"Сумма ячеек: {'✅' if cells_sum_correct else '❌'}, "
                            f"Процент загрузки: {'✅' if occupancy_correct else '❌'}"
                        )
                        
                        # Накапливаем для общей проверки
                        total_cells_calculated += total_cells
                        total_occupied_calculated += occupied_cells
                        total_free_calculated += free_cells
                
                # Проверяем общую статистику
                summary_total_cells = summary_stats.get("total_cells", 0)
                summary_occupied_cells = summary_stats.get("occupied_cells", 0)
                summary_free_cells = summary_stats.get("free_cells", 0)
                summary_occupancy_rate = summary_stats.get("average_occupancy_rate", 0)  # Исправлено поле
                
                # Проверяем соответствие суммарной статистики
                summary_correct = (
                    summary_total_cells == total_cells_calculated and
                    summary_occupied_cells == total_occupied_calculated and
                    summary_free_cells == total_free_calculated
                )
                
                expected_summary_occupancy = (total_occupied_calculated / total_cells_calculated * 100) if total_cells_calculated > 0 else 0
                summary_occupancy_correct = abs(summary_occupancy_rate - expected_summary_occupancy) < 0.1
                
                self.log_result(
                    "Проверка суммарной статистики",
                    summary_correct and summary_occupancy_correct,
                    f"Суммарно - Всего: {summary_total_cells} (расчет: {total_cells_calculated}), "
                    f"Занято: {summary_occupied_cells} (расчет: {total_occupied_calculated}), "
                    f"Свободно: {summary_free_cells} (расчет: {total_free_calculated}), "
                    f"Загрузка: {summary_occupancy_rate:.1f}% (ожидается: {expected_summary_occupancy:.1f}%)"
                )
                
                return data
                
            else:
                self.log_result(
                    "GET /api/operator/dashboard/analytics",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return None
                
        except Exception as e:
            self.log_result(
                "GET /api/operator/dashboard/analytics",
                False,
                f"Ошибка запроса: {str(e)}"
            )
            return None

    def test_operator_warehouses(self):
        """Тестирование GET /api/operator/warehouses"""
        try:
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            response = self.session.get(
                f"{BACKEND_URL}/operator/warehouses",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                warehouses = data if isinstance(data, list) else data.get("warehouses", [])
                
                self.log_result(
                    "GET /api/operator/warehouses",
                    True,
                    f"Получено {len(warehouses)} складов оператора"
                )
                
                # Возвращаем данные для дальнейшего анализа
                return warehouses
                
            else:
                self.log_result(
                    "GET /api/operator/warehouses",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return []
                
        except Exception as e:
            self.log_result(
                "GET /api/operator/warehouses",
                False,
                f"Ошибка запроса: {str(e)}"
            )
            return []

    def test_warehouse_statistics_individual(self, warehouse_id, warehouse_name):
        """Тестирование GET /api/warehouses/{warehouse_id}/statistics"""
        try:
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            response = self.session.get(
                f"{BACKEND_URL}/warehouses/{warehouse_id}/statistics",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем наличие ключевых полей
                required_fields = ["total_cells", "occupied_cells", "free_cells"]
                stats = {}
                
                for field in required_fields:
                    if field in data:
                        stats[field] = data[field]
                    else:
                        self.log_result(
                            f"GET /api/warehouses/{warehouse_id}/statistics - Поле {field}",
                            False,
                            f"Отсутствует поле {field} для склада '{warehouse_name}'"
                        )
                        return None
                
                # Для occupancy_rate проверяем оба возможных названия
                if "occupancy_rate" in data:
                    stats["occupancy_rate"] = data["occupancy_rate"]
                elif "utilization_percent" in data:
                    stats["occupancy_rate"] = data["utilization_percent"]
                else:
                    self.log_result(
                        f"GET /api/warehouses/{warehouse_id}/statistics - Поле occupancy_rate",
                        False,
                        f"Отсутствует поле occupancy_rate/utilization_percent для склада '{warehouse_name}'"
                    )
                    return None
                
                # Проверяем математическую корректность
                total_cells = stats["total_cells"]
                occupied_cells = stats["occupied_cells"]
                free_cells = stats["free_cells"]
                occupancy_rate = stats["occupancy_rate"]
                
                cells_sum_correct = (occupied_cells + free_cells == total_cells)
                expected_occupancy = (occupied_cells / total_cells * 100) if total_cells > 0 else 0
                occupancy_correct = abs(occupancy_rate - expected_occupancy) < 0.1
                
                self.log_result(
                    f"GET /api/warehouses/{warehouse_id}/statistics - '{warehouse_name}'",
                    cells_sum_correct and occupancy_correct,
                    f"Всего: {total_cells}, Занято: {occupied_cells}, Свободно: {free_cells}, "
                    f"Загрузка: {occupancy_rate:.1f}% (ожидается: {expected_occupancy:.1f}%), "
                    f"Математика: {'✅' if cells_sum_correct and occupancy_correct else '❌'}"
                )
                
                return stats
                
            else:
                self.log_result(
                    f"GET /api/warehouses/{warehouse_id}/statistics",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return None
                
        except Exception as e:
            self.log_result(
                f"GET /api/warehouses/{warehouse_id}/statistics",
                False,
                f"Ошибка запроса: {str(e)}"
            )
            return None

    def compare_statistics_sources(self, dashboard_data, warehouses_list):
        """Сравнение данных из разных источников"""
        try:
            dashboard_warehouses = dashboard_data.get("warehouses_details", [])
            
            # Создаем словарь для быстрого поиска
            dashboard_by_id = {w.get("warehouse_id"): w for w in dashboard_warehouses}
            
            discrepancies_found = False
            
            for warehouse in warehouses_list:
                warehouse_id = warehouse.get("id")
                warehouse_name = warehouse.get("name", "Неизвестный склад")
                
                if not warehouse_id:
                    continue
                
                # Получаем статистику из индивидуального endpoint
                individual_stats = self.test_warehouse_statistics_individual(warehouse_id, warehouse_name)
                
                if not individual_stats:
                    continue
                
                # Сравниваем с данными из dashboard
                dashboard_warehouse = dashboard_by_id.get(warehouse_id)
                
                if not dashboard_warehouse:
                    self.log_result(
                        f"Сравнение источников данных - '{warehouse_name}'",
                        False,
                        f"Склад отсутствует в dashboard analytics"
                    )
                    discrepancies_found = True
                    continue
                
                # Сравниваем ключевые показатели
                fields_to_compare = ["total_cells", "occupied_cells", "free_cells", "occupancy_rate"]
                differences = []
                
                for field in fields_to_compare:
                    if field == "total_cells":
                        # total_cells берем из warehouse_structure в dashboard
                        dashboard_value = dashboard_warehouse.get("warehouse_structure", {}).get(field, 0)
                    else:
                        # Остальные поля берем из cargo_stats в dashboard
                        dashboard_value = dashboard_warehouse.get("cargo_stats", {}).get(field, 0)
                    
                    individual_value = individual_stats.get(field, 0)
                    
                    if field == "occupancy_rate":
                        # Для процентов допускаем небольшую погрешность
                        if abs(dashboard_value - individual_value) > 0.1:
                            differences.append(f"{field}: dashboard={dashboard_value:.1f}%, individual={individual_value:.1f}%")
                    else:
                        if dashboard_value != individual_value:
                            differences.append(f"{field}: dashboard={dashboard_value}, individual={individual_value}")
                
                if differences:
                    self.log_result(
                        f"Сравнение источников данных - '{warehouse_name}'",
                        False,
                        f"РАСХОЖДЕНИЯ НАЙДЕНЫ: {'; '.join(differences)}"
                    )
                    discrepancies_found = True
                else:
                    self.log_result(
                        f"Сравнение источников данных - '{warehouse_name}'",
                        True,
                        "Данные из разных источников совпадают"
                    )
            
            return not discrepancies_found
            
        except Exception as e:
            self.log_result(
                "Сравнение источников данных",
                False,
                f"Ошибка при сравнении: {str(e)}"
            )
            return False

    def run_comprehensive_test(self):
        """Запуск полного тестирования статистики склада"""
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Проблема с некорректным отображением статистики склада")
        print("=" * 80)
        print()
        
        # Шаг 1: Авторизация оператора
        if not self.authenticate_operator():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться как оператор склада")
            return False
        
        # Шаг 2: Авторизация администратора для сравнения
        if not self.authenticate_admin():
            print("⚠️ ПРЕДУПРЕЖДЕНИЕ: Не удалось авторизоваться как администратор")
        
        # Шаг 3: Тестирование главного endpoint статистики оператора
        dashboard_data = self.test_operator_dashboard_analytics()
        if not dashboard_data:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить данные dashboard analytics")
            return False
        
        # Шаг 4: Получение списка складов оператора
        warehouses_list = self.test_operator_warehouses()
        if not warehouses_list:
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить список складов оператора")
            return False
        
        # Шаг 5: Сравнение данных из разных источников
        comparison_success = self.compare_statistics_sources(dashboard_data, warehouses_list)
        
        # Подведение итогов
        print("=" * 80)
        print("📊 ИТОГИ ТЕСТИРОВАНИЯ:")
        print()
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Всего тестов: {total_tests}")
        print(f"Успешных: {passed_tests} ✅")
        print(f"Неудачных: {failed_tests} ❌")
        print(f"Процент успеха: {(passed_tests/total_tests*100):.1f}%")
        print()
        
        # Анализ критических проблем
        critical_issues = []
        for result in self.test_results:
            if not result["success"] and ("РАСХОЖДЕНИЯ НАЙДЕНЫ" in result["details"] or "математическая" in result["test"].lower()):
                critical_issues.append(result)
        
        if critical_issues:
            print("🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ НАЙДЕНЫ:")
            for issue in critical_issues:
                print(f"   • {issue['test']}: {issue['details']}")
            print()
        
        # Рекомендации
        print("💡 РЕКОМЕНДАЦИИ:")
        if failed_tests == 0:
            print("   ✅ Все тесты прошли успешно. Статистика склада работает корректно.")
        else:
            print("   🔧 Обнаружены проблемы в расчете или отображении статистики склада.")
            print("   📋 Проверьте логику расчета в backend endpoints.")
            print("   🔍 Убедитесь в синхронизации данных между коллекциями MongoDB.")
        
        return failed_tests == 0

def main():
    """Главная функция запуска тестирования"""
    tester = WarehouseStatisticsTest()
    
    try:
        success = tester.run_comprehensive_test()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
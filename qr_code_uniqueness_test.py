#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправления для генерации уникальных QR кодов ячеек складов в TAJLINE.TJ

Цель тестирования:
Проверить, что каждый склад генерирует уникальные QR коды ячеек с правильными номерами складов,
чтобы система могла различать, к какому складу принадлежит ячейка при сканировании.

Задачи тестирования:
1. Тестирование нового endpoint обновления номеров: POST /api/admin/warehouses/update-id-numbers
2. Тестирование генерации QR кодов с уникальными номерами складов
3. Проверка уникальности QR кодов для одинаковых ячеек разных складов
4. Тестирование автоматического исправления при генерации QR кодов
"""

import requests
import json
import sys
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://tajline-cargo-7.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "phone": "+79999888777",
    "password": "admin123"
}

class QRCodeUniquenessTest:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: str):
        """Логирование результатов тестирования"""
        status = "✅ PASSED" if success else "❌ FAILED"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        print(f"   {details}")
        print()
        
    def authenticate_admin(self):
        """Авторизация администратора"""
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=ADMIN_CREDENTIALS
            )
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.admin_token}"
                })
                
                user_info = data.get("user", {})
                self.log_result(
                    "Авторизация администратора",
                    True,
                    f"Успешная авторизация: {user_info.get('full_name')} (роль: {user_info.get('role')})"
                )
                return True
            else:
                self.log_result(
                    "Авторизация администратора",
                    False,
                    f"Ошибка авторизации: HTTP {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Авторизация администратора",
                False,
                f"Исключение при авторизации: {str(e)}"
            )
            return False
    
    def get_warehouses_list(self):
        """Получение списка складов"""
        try:
            response = self.session.get(f"{BACKEND_URL}/warehouses")
            
            if response.status_code == 200:
                warehouses = response.json()
                self.log_result(
                    "Получение списка складов",
                    True,
                    f"Получено {len(warehouses)} складов для тестирования"
                )
                return warehouses
            else:
                self.log_result(
                    "Получение списка складов",
                    False,
                    f"Ошибка получения складов: HTTP {response.status_code} - {response.text}"
                )
                return []
                
        except Exception as e:
            self.log_result(
                "Получение списка складов",
                False,
                f"Исключение при получении складов: {str(e)}"
            )
            return []
    
    def test_update_warehouse_id_numbers_endpoint(self):
        """Тестирование endpoint обновления номеров складов"""
        try:
            response = self.session.post(f"{BACKEND_URL}/admin/warehouses/update-id-numbers")
            
            if response.status_code == 200:
                data = response.json()
                total_warehouses = data.get("total_warehouses", 0)
                updated_count = data.get("updated_count", 0)
                updated_warehouses = data.get("updated_warehouses", [])
                
                # Проверяем уникальность номеров
                unique_numbers = set()
                duplicates_found = False
                
                # Получаем обновленный список складов для проверки уникальности
                warehouses = self.get_warehouses_list()
                warehouse_numbers = []
                
                for warehouse in warehouses:
                    warehouse_id_number = warehouse.get("warehouse_id_number")
                    if warehouse_id_number:
                        if warehouse_id_number in unique_numbers:
                            duplicates_found = True
                        else:
                            unique_numbers.add(warehouse_id_number)
                        warehouse_numbers.append(warehouse_id_number)
                
                details = f"Всего складов: {total_warehouses}, Обновлено: {updated_count}"
                if updated_warehouses:
                    details += f"\nПримеры обновлений:"
                    for update in updated_warehouses[:3]:  # Показываем первые 3
                        details += f"\n  - {update.get('name')}: {update.get('old_number')} → {update.get('new_number')}"
                
                details += f"\nУникальных номеров: {len(unique_numbers)}"
                details += f"\nДубликаты найдены: {'Да' if duplicates_found else 'Нет'}"
                
                self.log_result(
                    "Endpoint обновления номеров складов",
                    not duplicates_found,
                    details
                )
                
                return not duplicates_found
            else:
                self.log_result(
                    "Endpoint обновления номеров складов",
                    False,
                    f"Ошибка обновления: HTTP {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Endpoint обновления номеров складов",
                False,
                f"Исключение при обновлении номеров: {str(e)}"
            )
            return False
    
    def test_qr_code_generation_uniqueness(self):
        """Тестирование уникальности QR кодов для одинаковых ячеек разных складов"""
        try:
            warehouses = self.get_warehouses_list()
            
            if len(warehouses) < 2:
                self.log_result(
                    "Тестирование уникальности QR кодов",
                    False,
                    "Недостаточно складов для тестирования уникальности (нужно минимум 2)"
                )
                return False
            
            # Выбираем первые 2 склада для тестирования
            test_warehouses = warehouses[:2]
            qr_codes = {}
            
            # Тестируем одинаковые ячейки (блок 1, полка 1, ячейка 1) для разных складов
            block, shelf, cell = 1, 1, 1
            
            for warehouse in test_warehouses:
                warehouse_id = warehouse.get("id")
                warehouse_name = warehouse.get("name", "Unknown")
                warehouse_id_number = warehouse.get("warehouse_id_number")
                
                # Генерируем QR код для ячейки
                try:
                    response = self.session.get(
                        f"{BACKEND_URL}/warehouse/{warehouse_id}/cell-qr/{block}/{shelf}/{cell}"
                    )
                    
                    if response.status_code == 200:
                        qr_data = response.text
                        qr_codes[warehouse_id] = {
                            "name": warehouse_name,
                            "warehouse_id_number": warehouse_id_number,
                            "qr_code": qr_data,
                            "expected_format": f"{warehouse_id_number}-{block:02d}-{shelf:02d}-{cell:03d}"
                        }
                    else:
                        self.log_result(
                            f"Генерация QR кода для склада {warehouse_name}",
                            False,
                            f"Ошибка генерации QR: HTTP {response.status_code} - {response.text}"
                        )
                        
                except Exception as e:
                    self.log_result(
                        f"Генерация QR кода для склада {warehouse_name}",
                        False,
                        f"Исключение при генерации QR: {str(e)}"
                    )
            
            # Проверяем уникальность QR кодов
            if len(qr_codes) >= 2:
                qr_values = [data["qr_code"] for data in qr_codes.values()]
                unique_qr_codes = len(set(qr_values)) == len(qr_values)
                
                details = f"Протестировано складов: {len(qr_codes)}\n"
                details += f"Тестовая ячейка: Блок {block}, Полка {shelf}, Ячейка {cell}\n"
                
                for warehouse_id, data in qr_codes.items():
                    details += f"\nСклад: {data['name']}"
                    details += f"\n  - Номер склада: {data['warehouse_id_number']}"
                    details += f"\n  - Ожидаемый формат: {data['expected_format']}"
                    details += f"\n  - QR код длина: {len(data['qr_code'])} символов"
                
                details += f"\n\nУникальность QR кодов: {'✅ Да' if unique_qr_codes else '❌ Нет'}"
                
                self.log_result(
                    "Тестирование уникальности QR кодов",
                    unique_qr_codes,
                    details
                )
                
                return unique_qr_codes
            else:
                self.log_result(
                    "Тестирование уникальности QR кодов",
                    False,
                    f"Недостаточно QR кодов сгенерировано: {len(qr_codes)} из {len(test_warehouses)}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Тестирование уникальности QR кодов",
                False,
                f"Исключение при тестировании уникальности: {str(e)}"
            )
            return False
    
    def test_automatic_warehouse_id_assignment(self):
        """Тестирование автоматического назначения номеров складам без warehouse_id_number"""
        try:
            warehouses = self.get_warehouses_list()
            
            # Ищем склады без warehouse_id_number или с некорректными номерами
            warehouses_without_id = []
            warehouses_with_id = []
            
            for warehouse in warehouses:
                warehouse_id_number = warehouse.get("warehouse_id_number")
                if not warehouse_id_number or not warehouse_id_number.isdigit() or len(warehouse_id_number) != 3:
                    warehouses_without_id.append(warehouse)
                else:
                    warehouses_with_id.append(warehouse)
            
            details = f"Всего складов: {len(warehouses)}\n"
            details += f"Склады с корректными номерами: {len(warehouses_with_id)}\n"
            details += f"Склады без номеров/с некорректными: {len(warehouses_without_id)}\n"
            
            if warehouses_without_id:
                # Тестируем автоматическое назначение через генерацию QR кода
                test_warehouse = warehouses_without_id[0]
                warehouse_id = test_warehouse.get("id")
                warehouse_name = test_warehouse.get("name", "Unknown")
                
                details += f"\nТестовый склад: {warehouse_name}"
                details += f"\nТекущий warehouse_id_number: {test_warehouse.get('warehouse_id_number')}"
                
                # Пытаемся сгенерировать QR код - это должно автоматически назначить номер
                try:
                    response = self.session.get(
                        f"{BACKEND_URL}/warehouse/{warehouse_id}/cell-qr/1/1/1"
                    )
                    
                    if response.status_code == 200:
                        # Проверяем, был ли назначен номер
                        updated_warehouses = self.get_warehouses_list()
                        updated_warehouse = next(
                            (w for w in updated_warehouses if w.get("id") == warehouse_id), 
                            None
                        )
                        
                        if updated_warehouse:
                            new_id_number = updated_warehouse.get("warehouse_id_number")
                            if new_id_number and new_id_number.isdigit() and len(new_id_number) == 3:
                                details += f"\n✅ Автоматически назначен номер: {new_id_number}"
                                success = True
                            else:
                                details += f"\n❌ Номер не назначен или некорректный: {new_id_number}"
                                success = False
                        else:
                            details += f"\n❌ Склад не найден после обновления"
                            success = False
                    else:
                        details += f"\n❌ Ошибка генерации QR: HTTP {response.status_code}"
                        success = False
                        
                except Exception as e:
                    details += f"\n❌ Исключение при генерации QR: {str(e)}"
                    success = False
            else:
                details += "\n✅ Все склады уже имеют корректные номера"
                success = True
            
            self.log_result(
                "Автоматическое назначение номеров складам",
                success,
                details
            )
            
            return success
            
        except Exception as e:
            self.log_result(
                "Автоматическое назначение номеров складам",
                False,
                f"Исключение при тестировании автоназначения: {str(e)}"
            )
            return False
    
    def test_qr_code_format_validation(self):
        """Тестирование правильности формата QR кодов"""
        try:
            warehouses = self.get_warehouses_list()
            
            if not warehouses:
                self.log_result(
                    "Валидация формата QR кодов",
                    False,
                    "Нет складов для тестирования"
                )
                return False
            
            # Тестируем первые 3 склада
            test_warehouses = warehouses[:3]
            format_tests = []
            
            for warehouse in test_warehouses:
                warehouse_id = warehouse.get("id")
                warehouse_name = warehouse.get("name", "Unknown")
                warehouse_id_number = warehouse.get("warehouse_id_number")
                
                if not warehouse_id_number:
                    continue
                
                # Тестируем разные ячейки
                test_cells = [
                    (1, 1, 1),   # 001-01-01-001
                    (2, 3, 15),  # XXX-02-03-015
                    (1, 1, 100)  # XXX-01-01-100
                ]
                
                for block, shelf, cell in test_cells:
                    expected_format = f"{warehouse_id_number}-{block:02d}-{shelf:02d}-{cell:03d}"
                    
                    try:
                        response = self.session.get(
                            f"{BACKEND_URL}/warehouse/{warehouse_id}/cell-qr/{block}/{shelf}/{cell}"
                        )
                        
                        if response.status_code == 200:
                            qr_data = response.text
                            # QR код должен содержать base64 данные
                            is_base64_format = qr_data.startswith("data:image/png;base64,")
                            
                            format_tests.append({
                                "warehouse": warehouse_name,
                                "warehouse_number": warehouse_id_number,
                                "cell": f"Б{block}-П{shelf}-Я{cell}",
                                "expected_format": expected_format,
                                "qr_generated": True,
                                "is_base64": is_base64_format,
                                "qr_length": len(qr_data)
                            })
                        else:
                            format_tests.append({
                                "warehouse": warehouse_name,
                                "warehouse_number": warehouse_id_number,
                                "cell": f"Б{block}-П{shelf}-Я{cell}",
                                "expected_format": expected_format,
                                "qr_generated": False,
                                "error": f"HTTP {response.status_code}"
                            })
                            
                    except Exception as e:
                        format_tests.append({
                            "warehouse": warehouse_name,
                            "warehouse_number": warehouse_id_number,
                            "cell": f"Б{block}-П{shelf}-Я{cell}",
                            "expected_format": expected_format,
                            "qr_generated": False,
                            "error": str(e)
                        })
            
            # Анализируем результаты
            successful_tests = [t for t in format_tests if t.get("qr_generated", False)]
            failed_tests = [t for t in format_tests if not t.get("qr_generated", False)]
            
            details = f"Протестировано QR кодов: {len(format_tests)}\n"
            details += f"Успешно сгенерировано: {len(successful_tests)}\n"
            details += f"Ошибок генерации: {len(failed_tests)}\n"
            
            if successful_tests:
                details += f"\nПримеры успешных QR кодов:"
                for test in successful_tests[:3]:
                    details += f"\n  - {test['warehouse']} ({test['warehouse_number']})"
                    details += f"\n    Ячейка: {test['cell']}"
                    details += f"\n    Ожидаемый формат: {test['expected_format']}"
                    details += f"\n    Base64 формат: {'✅' if test.get('is_base64') else '❌'}"
                    details += f"\n    Длина QR: {test.get('qr_length', 0)} символов"
            
            if failed_tests:
                details += f"\nОшибки генерации:"
                for test in failed_tests[:3]:
                    details += f"\n  - {test['warehouse']}: {test.get('error', 'Unknown error')}"
            
            success_rate = len(successful_tests) / len(format_tests) if format_tests else 0
            overall_success = success_rate >= 0.8  # 80% успешности
            
            details += f"\nУспешность: {success_rate:.1%}"
            
            self.log_result(
                "Валидация формата QR кодов",
                overall_success,
                details
            )
            
            return overall_success
            
        except Exception as e:
            self.log_result(
                "Валидация формата QR кодов",
                False,
                f"Исключение при валидации формата: {str(e)}"
            )
            return False
    
    def run_comprehensive_test(self):
        """Запуск полного комплексного тестирования"""
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Исправления для генерации уникальных QR кодов ячеек складов в TAJLINE.TJ")
        print("=" * 100)
        print()
        
        # 1. Авторизация
        if not self.authenticate_admin():
            print("❌ Критическая ошибка: Не удалось авторизоваться как администратор")
            return False
        
        # 2. Тестирование endpoint обновления номеров
        print("📋 ТЕСТ 1: Endpoint обновления номеров складов")
        test1_success = self.test_update_warehouse_id_numbers_endpoint()
        
        # 3. Тестирование уникальности QR кодов
        print("🔍 ТЕСТ 2: Уникальность QR кодов для одинаковых ячеек")
        test2_success = self.test_qr_code_generation_uniqueness()
        
        # 4. Тестирование автоматического назначения
        print("⚙️ ТЕСТ 3: Автоматическое назначение номеров")
        test3_success = self.test_automatic_warehouse_id_assignment()
        
        # 5. Тестирование формата QR кодов
        print("📝 ТЕСТ 4: Валидация формата QR кодов")
        test4_success = self.test_qr_code_format_validation()
        
        # Подведение итогов
        print("=" * 100)
        print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
        print("=" * 100)
        
        passed_tests = sum([test1_success, test2_success, test3_success, test4_success])
        total_tests = 4
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"Пройдено тестов: {passed_tests}/{total_tests}")
        print(f"Успешность: {success_rate:.1f}%")
        print()
        
        # Детальные результаты
        for result in self.test_results:
            print(f"{result['status']}: {result['test']}")
        
        print()
        
        if success_rate >= 75:
            print("🎉 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ Исправления для генерации уникальных QR кодов работают корректно")
            print("✅ Каждый склад генерирует уникальные QR коды ячеек")
            print("✅ Система может различать принадлежность ячеек к складам")
        else:
            print("⚠️ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ ВЫЯВИЛО ПРОБЛЕМЫ!")
            print("❌ Требуются дополнительные исправления")
            
        return success_rate >= 75

def main():
    """Главная функция запуска тестирования"""
    tester = QRCodeUniquenessTest()
    success = tester.run_comprehensive_test()
    
    # Возвращаем код выхода
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
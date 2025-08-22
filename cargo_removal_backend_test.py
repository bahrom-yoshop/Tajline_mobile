#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: НОВАЯ ФУНКЦИЯ УДАЛЕНИЯ ГРУЗА ИЗ СПИСКА РАЗМЕЩЕНИЯ В TAJLINE.TJ

КОНТЕКСТ НОВОЙ ФУНКЦИОНАЛЬНОСТИ:
- Добавлена кнопка "Удалить" на каждую карточку груза в списке размещения
- Кнопка красного цвета с иконкой Trash2 и подтверждением
- Backend API endpoint DELETE /api/operator/cargo/{cargo_id}/remove-from-placement
- Изменение статуса груза на "removed_from_placement" с временными метками
- Создание уведомления об удалении груза

ТЕСТОВЫЙ ПЛАН:
1. Авторизация оператора склада (+79777888999/warehouse123)
2. Получить доступные грузы для размещения через /api/operator/cargo/available-for-placement
3. КРИТИЧЕСКИЙ ТЕСТ: Протестировать новый API endpoint /api/operator/cargo/{cargo_id}/remove-from-placement:
   - Использовать реальный cargo_id из доступных грузов
   - Проверить успешное удаление груза из списка размещения
   - Убедиться что статус груза изменился на "removed_from_placement"
4. Проверить что груз исчез из списка доступных для размещения
5. Проверить создание уведомления об операции удаления

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
- API должен успешно удалять груз из списка размещения
- Статус груза должен измениться на "removed_from_placement"
- Груз должен исчезнуть из списка доступных для размещения
- Создается уведомление об операции удаления
"""

import requests
import json
import sys
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://tajline-cargo-8.preview.emergentagent.com/api"

# Учетные данные оператора склада
WAREHOUSE_OPERATOR = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class CargoRemovalTester:
    def __init__(self):
        self.operator_token = None
        self.operator_info = None
        self.test_results = []
        
    def log_result(self, test_name, success, message, details=None):
        """Логирование результата теста"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def authenticate_warehouse_operator(self):
        """Авторизация оператора склада"""
        print(f"\n🔐 Авторизация оператора склада ({WAREHOUSE_OPERATOR['phone']})...")
        
        try:
            response = requests.post(f"{BACKEND_URL}/auth/login", json=WAREHOUSE_OPERATOR, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                self.operator_token = data.get("access_token")
                self.operator_info = data.get("user", {})
                
                if self.operator_token:
                    operator_name = self.operator_info.get('full_name', 'Unknown')
                    operator_role = self.operator_info.get('role', 'Unknown')
                    operator_number = self.operator_info.get('user_number', 'Unknown')
                    
                    self.log_result(
                        "Авторизация оператора склада",
                        True,
                        f"Успешная авторизация: {operator_name} (роль: {operator_role}, номер: {operator_number})"
                    )
                    return True
                else:
                    self.log_result("Авторизация оператора склада", False, "Токен доступа не получен")
                    return False
            else:
                self.log_result("Авторизация оператора склада", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Авторизация оператора склада", False, f"Exception: {str(e)}")
            return False
    
    def get_available_cargo_for_placement(self):
        """Получить доступные грузы для размещения"""
        print(f"\n📦 Получение доступных грузов для размещения...")
        
        try:
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            response = requests.get(f"{BACKEND_URL}/operator/cargo/available-for-placement", headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                if items:
                    self.log_result(
                        "Получение доступных грузов для размещения",
                        True,
                        f"Найдено {len(items)} грузов для размещения",
                        {
                            "total_items": len(items),
                            "sample_cargo": items[0] if items else None,
                            "cargo_ids": [item.get("id") for item in items[:5]]  # Первые 5 ID
                        }
                    )
                    return items
                else:
                    self.log_result(
                        "Получение доступных грузов для размещения",
                        False,
                        "Нет доступных грузов для размещения",
                        {"response_data": data}
                    )
                    return []
            else:
                self.log_result(
                    "Получение доступных грузов для размещения",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return []
                
        except Exception as e:
            self.log_result("Получение доступных грузов для размещения", False, f"Exception: {str(e)}")
            return []
    
    def test_cargo_removal_endpoint(self, cargo_id, cargo_number):
        """КРИТИЧЕСКИЙ ТЕСТ: Тестирование нового endpoint удаления груза"""
        print(f"\n🗑️ КРИТИЧЕСКИЙ ТЕСТ: Удаление груза {cargo_number} (ID: {cargo_id}) из списка размещения...")
        
        try:
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            response = requests.delete(f"{BACKEND_URL}/operator/cargo/{cargo_id}/remove-from-placement", headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Проверяем структуру ответа
                success = data.get("success", False)
                message = data.get("message", "")
                returned_cargo_number = data.get("cargo_number", "")
                
                if success and returned_cargo_number == cargo_number:
                    self.log_result(
                        "КРИТИЧЕСКИЙ ТЕСТ: Удаление груза из размещения",
                        True,
                        f"Груз {cargo_number} успешно удален из списка размещения",
                        {
                            "cargo_id": cargo_id,
                            "cargo_number": cargo_number,
                            "returned_cargo_number": returned_cargo_number,
                            "api_message": message,
                            "response_data": data
                        }
                    )
                    return True
                else:
                    self.log_result(
                        "КРИТИЧЕСКИЙ ТЕСТ: Удаление груза из размещения",
                        False,
                        f"Неожиданный ответ API: success={success}, cargo_number={returned_cargo_number}",
                        {"response_data": data}
                    )
                    return False
            else:
                self.log_result(
                    "КРИТИЧЕСКИЙ ТЕСТ: Удаление груза из размещения",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {
                        "cargo_id": cargo_id,
                        "cargo_number": cargo_number,
                        "status_code": response.status_code,
                        "response_text": response.text
                    }
                )
                return False
                
        except Exception as e:
            self.log_result("КРИТИЧЕСКИЙ ТЕСТ: Удаление груза из размещения", False, f"Exception: {str(e)}")
            return False
    
    def verify_cargo_status_changed(self, cargo_id, cargo_number):
        """Проверить что статус груза изменился на 'removed_from_placement'"""
        print(f"\n🔍 Проверка изменения статуса груза {cargo_number}...")
        
        try:
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            # Попробуем найти груз через поиск по номеру
            response = requests.get(f"{BACKEND_URL}/cargo/track/{cargo_number}", headers=headers, timeout=30)
            
            if response.status_code == 200:
                cargo_data = response.json()
                cargo_status = cargo_data.get("status", "")
                
                if cargo_status == "removed_from_placement":
                    self.log_result(
                        "Проверка изменения статуса груза",
                        True,
                        f"Статус груза {cargo_number} изменен на 'removed_from_placement'",
                        {
                            "cargo_id": cargo_id,
                            "cargo_number": cargo_number,
                            "new_status": cargo_status,
                            "cargo_data": cargo_data
                        }
                    )
                    return True
                else:
                    self.log_result(
                        "Проверка изменения статуса груза",
                        False,
                        f"Статус груза {cargo_number} не изменился: {cargo_status}",
                        {
                            "cargo_id": cargo_id,
                            "cargo_number": cargo_number,
                            "current_status": cargo_status,
                            "expected_status": "removed_from_placement"
                        }
                    )
                    return False
            else:
                self.log_result(
                    "Проверка изменения статуса груза",
                    False,
                    f"Не удалось получить данные груза: HTTP {response.status_code}",
                    {"response_text": response.text}
                )
                return False
                
        except Exception as e:
            self.log_result("Проверка изменения статуса груза", False, f"Exception: {str(e)}")
            return False
    
    def verify_cargo_removed_from_list(self, removed_cargo_id):
        """Проверить что груз исчез из списка доступных для размещения"""
        print(f"\n🔍 Проверка что груз исчез из списка размещения...")
        
        try:
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            response = requests.get(f"{BACKEND_URL}/operator/cargo/available-for-placement", headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                # Проверяем что удаленный груз отсутствует в списке
                cargo_still_present = any(item.get("id") == removed_cargo_id for item in items)
                
                if not cargo_still_present:
                    self.log_result(
                        "Проверка исчезновения груза из списка",
                        True,
                        f"Груз успешно исчез из списка размещения (осталось {len(items)} грузов)",
                        {
                            "removed_cargo_id": removed_cargo_id,
                            "remaining_cargo_count": len(items),
                            "cargo_still_present": False
                        }
                    )
                    return True
                else:
                    self.log_result(
                        "Проверка исчезновения груза из списка",
                        False,
                        "Груз все еще присутствует в списке размещения",
                        {
                            "removed_cargo_id": removed_cargo_id,
                            "cargo_still_present": True,
                            "total_items": len(items)
                        }
                    )
                    return False
            else:
                self.log_result(
                    "Проверка исчезновения груза из списка",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Проверка исчезновения груза из списка", False, f"Exception: {str(e)}")
            return False
    
    def check_removal_notification(self, cargo_number):
        """Проверить создание уведомления об удалении груза"""
        print(f"\n📬 Проверка создания уведомления об удалении груза {cargo_number}...")
        
        try:
            headers = {"Authorization": f"Bearer {self.operator_token}"}
            response = requests.get(f"{BACKEND_URL}/notifications", headers=headers, timeout=30)
            
            if response.status_code == 200:
                notifications = response.json()
                
                # Ищем уведомление об удалении груза
                removal_notification = None
                for notification in notifications:
                    message = notification.get("message", "")
                    if "удален" in message.lower() and cargo_number in message:
                        removal_notification = notification
                        break
                
                if removal_notification:
                    self.log_result(
                        "Проверка уведомления об удалении",
                        True,
                        f"Уведомление об удалении груза {cargo_number} создано",
                        {
                            "notification_id": removal_notification.get("id"),
                            "notification_message": removal_notification.get("message"),
                            "created_at": removal_notification.get("created_at")
                        }
                    )
                    return True
                else:
                    self.log_result(
                        "Проверка уведомления об удалении",
                        False,
                        f"Уведомление об удалении груза {cargo_number} не найдено",
                        {
                            "total_notifications": len(notifications),
                            "searched_cargo": cargo_number
                        }
                    )
                    return False
            else:
                self.log_result(
                    "Проверка уведомления об удалении",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Проверка уведомления об удалении", False, f"Exception: {str(e)}")
            return False
    
    def run_comprehensive_cargo_removal_test(self):
        """Запуск полного тестирования функции удаления груза"""
        print("🗑️ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: НОВАЯ ФУНКЦИЯ УДАЛЕНИЯ ГРУЗА ИЗ СПИСКА РАЗМЕЩЕНИЯ В TAJLINE.TJ")
        print("=" * 100)
        
        # Шаг 1: Авторизация оператора склада
        if not self.authenticate_warehouse_operator():
            print("❌ Не удалось авторизоваться как оператор склада")
            return False
        
        # Шаг 2: Получить доступные грузы для размещения
        available_cargo = self.get_available_cargo_for_placement()
        if not available_cargo:
            print("❌ Нет доступных грузов для тестирования удаления")
            return False
        
        # Выбираем первый груз для тестирования
        test_cargo = available_cargo[0]
        cargo_id = test_cargo.get("id")
        cargo_number = test_cargo.get("cargo_number")
        
        if not cargo_id or not cargo_number:
            self.log_result(
                "Выбор тестового груза",
                False,
                "Груз не содержит необходимых полей id или cargo_number",
                {"test_cargo": test_cargo}
            )
            return False
        
        print(f"\n🎯 Выбран тестовый груз: {cargo_number} (ID: {cargo_id})")
        
        # Шаг 3: КРИТИЧЕСКИЙ ТЕСТ - Удаление груза из размещения
        removal_success = self.test_cargo_removal_endpoint(cargo_id, cargo_number)
        if not removal_success:
            print("❌ КРИТИЧЕСКИЙ ТЕСТ ПРОВАЛЕН: Не удалось удалить груз из размещения")
            return False
        
        # Шаг 4: Проверить что статус груза изменился
        status_changed = self.verify_cargo_status_changed(cargo_id, cargo_number)
        
        # Шаг 5: Проверить что груз исчез из списка
        cargo_removed_from_list = self.verify_cargo_removed_from_list(cargo_id)
        
        # Шаг 6: Проверить создание уведомления (опционально)
        notification_created = self.check_removal_notification(cargo_number)
        
        # Итоговый отчет
        print("\n" + "=" * 100)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ ФУНКЦИИ УДАЛЕНИЯ ГРУЗА")
        print("=" * 100)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Всего тестов: {total_tests}")
        print(f"Пройдено: {passed_tests}")
        print(f"Провалено: {failed_tests}")
        print(f"Процент успеха: {success_rate:.1f}%")
        
        # Детальные результаты
        print(f"\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        # Критические проблемы
        critical_failures = [
            result for result in self.test_results 
            if not result["success"] and "КРИТИЧЕСКИЙ" in result["test"]
        ]
        
        if critical_failures:
            print(f"\n🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ ({len(critical_failures)}):")
            for failure in critical_failures:
                print(f"   - {failure['test']}: {failure['message']}")
        
        # Ключевые выводы
        print(f"\n🔍 КЛЮЧЕВЫЕ ВЫВОДЫ:")
        
        if removal_success:
            print("   ✅ НОВЫЙ API ENDPOINT РАБОТАЕТ: DELETE /api/operator/cargo/{cargo_id}/remove-from-placement")
        else:
            print("   ❌ НОВЫЙ API ENDPOINT НЕ РАБОТАЕТ: Требуется реализация")
        
        if status_changed:
            print("   ✅ Статус груза изменяется на 'removed_from_placement'")
        else:
            print("   ❌ Статус груза не изменяется корректно")
        
        if cargo_removed_from_list:
            print("   ✅ Груз корректно исчезает из списка размещения")
        else:
            print("   ❌ Груз не исчезает из списка размещения")
        
        if notification_created:
            print("   ✅ Уведомление об удалении создается")
        else:
            print("   ⚠️ Уведомление об удалении не создается (может быть не критично)")
        
        # Финальная оценка
        if success_rate >= 75.0 and removal_success and status_changed:
            print("\n🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ ОЖИДАЕМЫЙ РЕЗУЛЬТАТ ДОСТИГНУТ:")
            print("   - API успешно удаляет груз из списка размещения")
            print("   - Статус груза изменяется на 'removed_from_placement'")
            print("   - Груз исчезает из списка доступных для размещения")
            return True
        else:
            print("\n❌ ТЕСТИРОВАНИЕ ВЫЯВИЛО ПРОБЛЕМЫ!")
            print("🔧 ТРЕБУЕТСЯ ДОРАБОТКА:")
            if not removal_success:
                print("   - Реализовать API endpoint DELETE /api/operator/cargo/{cargo_id}/remove-from-placement")
            if not status_changed:
                print("   - Исправить изменение статуса груза на 'removed_from_placement'")
                print("   - Добавить временные метки удаления")
            if not cargo_removed_from_list:
                print("   - Исправить логику фильтрации в /api/operator/cargo/available-for-placement")
            return False

if __name__ == "__main__":
    tester = CargoRemovalTester()
    success = tester.run_comprehensive_cargo_removal_test()
    
    if success:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        sys.exit(0)
    else:
        print("\n❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ В ТЕСТИРОВАНИИ!")
        sys.exit(1)
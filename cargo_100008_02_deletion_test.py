#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Удаление конкретного груза 100008/02 (ID: 100004) в TAJLINE.TJ

Найден груз 100008/02 с ID: 100004 в коллекции размещения.
Проведем детальное тестирование всех способов удаления этого конкретного груза.
"""

import requests
import json
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://tajline-manage-1.preview.emergentagent.com/api"

# Учетные данные администратора
ADMIN_CREDENTIALS = {
    "phone": "+79999888777",
    "password": "admin123"
}

class SpecificCargoDeletionTest:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.target_cargo_number = "100008/02"
        self.target_cargo_id = "100004"
        self.cargo_data = None
        
    def authenticate_admin(self):
        """Авторизация администратора"""
        print("🔐 Авторизация администратора...")
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=ADMIN_CREDENTIALS,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                user_info = data.get("user", {})
                
                print(f"✅ Успешная авторизация: {user_info.get('full_name', 'N/A')} ({user_info.get('role', 'N/A')})")
                
                # Устанавливаем токен для всех последующих запросов
                self.session.headers.update({
                    "Authorization": f"Bearer {self.admin_token}"
                })
                
                return True
            else:
                print(f"❌ Ошибка авторизации: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение при авторизации: {e}")
            return False
    
    def get_detailed_cargo_info(self):
        """Получение детальной информации о грузе 100008/02"""
        print(f"\n📋 Получение детальной информации о грузе {self.target_cargo_number}...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/operator/cargo/available-for-placement",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                cargo_items = data.get('items', [])
                
                # Ищем наш груз
                target_cargo = None
                for cargo in cargo_items:
                    if cargo.get('cargo_number') == self.target_cargo_number:
                        target_cargo = cargo
                        break
                
                if target_cargo:
                    self.cargo_data = target_cargo
                    
                    print(f"🎯 ДЕТАЛЬНАЯ ИНФОРМАЦИЯ О ГРУЗЕ {self.target_cargo_number}:")
                    print(f"=" * 60)
                    for key, value in target_cargo.items():
                        print(f"   {key}: {value}")
                    print(f"=" * 60)
                    
                    return True
                else:
                    print(f"❌ Груз {self.target_cargo_number} не найден в списке размещения")
                    return False
            else:
                print(f"❌ Ошибка получения списка грузов: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение при получении информации о грузе: {e}")
            return False
    
    def test_single_cargo_deletion(self):
        """Тестирование единичного удаления груза"""
        print(f"\n🗑️ Тестирование единичного удаления груза {self.target_cargo_number}...")
        
        # Метод 1: DELETE /api/operator/cargo/{cargo_id}/remove-from-placement
        print(f"\n🔄 Метод 1: DELETE /api/operator/cargo/{self.target_cargo_id}/remove-from-placement")
        try:
            response = self.session.delete(
                f"{BACKEND_URL}/operator/cargo/{self.target_cargo_id}/remove-from-placement",
                timeout=10
            )
            
            print(f"   Статус: {response.status_code}")
            print(f"   Ответ: {response.text}")
            
            if response.status_code == 200:
                print(f"   ✅ Успешное удаление методом 1!")
                return True
            else:
                print(f"   ❌ Ошибка удаления методом 1")
                
        except Exception as e:
            print(f"   ❌ Исключение в методе 1: {e}")
        
        # Метод 2: DELETE /api/admin/cargo/{cargo_id}
        print(f"\n🔄 Метод 2: DELETE /api/admin/cargo/{self.target_cargo_id}")
        try:
            response = self.session.delete(
                f"{BACKEND_URL}/admin/cargo/{self.target_cargo_id}",
                timeout=10
            )
            
            print(f"   Статус: {response.status_code}")
            print(f"   Ответ: {response.text}")
            
            if response.status_code == 200:
                print(f"   ✅ Успешное удаление методом 2!")
                return True
            else:
                print(f"   ❌ Ошибка удаления методом 2")
                
        except Exception as e:
            print(f"   ❌ Исключение в методе 2: {e}")
        
        # Метод 3: DELETE /api/cargo/{cargo_id}
        print(f"\n🔄 Метод 3: DELETE /api/cargo/{self.target_cargo_id}")
        try:
            response = self.session.delete(
                f"{BACKEND_URL}/cargo/{self.target_cargo_id}",
                timeout=10
            )
            
            print(f"   Статус: {response.status_code}")
            print(f"   Ответ: {response.text}")
            
            if response.status_code == 200:
                print(f"   ✅ Успешное удаление методом 3!")
                return True
            else:
                print(f"   ❌ Ошибка удаления методом 3")
                
        except Exception as e:
            print(f"   ❌ Исключение в методе 3: {e}")
        
        return False
    
    def test_bulk_cargo_deletion(self):
        """Тестирование массового удаления груза"""
        print(f"\n🗑️ Тестирование массового удаления груза {self.target_cargo_number}...")
        
        # Метод 1: POST /api/operator/cargo/bulk-remove-from-placement
        print(f"\n🔄 Метод 1: POST /api/operator/cargo/bulk-remove-from-placement")
        try:
            payload = {
                "cargo_ids": [self.target_cargo_id]
            }
            
            response = self.session.delete(
                f"{BACKEND_URL}/operator/cargo/bulk-remove-from-placement",
                json=payload,
                timeout=10
            )
            
            print(f"   Статус: {response.status_code}")
            print(f"   Ответ: {response.text}")
            
            if response.status_code == 200:
                print(f"   ✅ Успешное массовое удаление!")
                return True
            else:
                print(f"   ❌ Ошибка массового удаления")
                
        except Exception as e:
            print(f"   ❌ Исключение при массовом удалении: {e}")
        
        return False
    
    def test_cargo_status_change(self):
        """Тестирование изменения статуса груза"""
        print(f"\n🔄 Тестирование изменения статуса груза {self.target_cargo_number}...")
        
        # Попробуем изменить статус груза
        status_endpoints = [
            f"/admin/cargo/{self.target_cargo_id}/status",
            f"/operator/cargo/{self.target_cargo_id}/status",
            f"/cargo/{self.target_cargo_id}/status"
        ]
        
        new_statuses = ["removed", "deleted", "cancelled", "completed"]
        
        for endpoint in status_endpoints:
            for status in new_statuses:
                print(f"\n🔄 Попытка изменения статуса на '{status}' через {endpoint}")
                try:
                    payload = {"status": status}
                    
                    response = self.session.put(
                        f"{BACKEND_URL}{endpoint}",
                        json=payload,
                        timeout=10
                    )
                    
                    print(f"   Статус: {response.status_code}")
                    print(f"   Ответ: {response.text}")
                    
                    if response.status_code == 200:
                        print(f"   ✅ Успешное изменение статуса на '{status}'!")
                        return True
                        
                except Exception as e:
                    print(f"   ❌ Исключение: {e}")
        
        return False
    
    def verify_cargo_removal(self):
        """Проверка удаления груза из системы"""
        print(f"\n✅ Проверка удаления груза {self.target_cargo_number}...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/operator/cargo/available-for-placement",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                cargo_items = data.get('items', [])
                
                # Ищем наш груз
                found = False
                for cargo in cargo_items:
                    if cargo.get('cargo_number') == self.target_cargo_number:
                        found = True
                        break
                
                if found:
                    print(f"❌ Груз {self.target_cargo_number} ВСЕ ЕЩЕ ПРИСУТСТВУЕТ в списке размещения!")
                    return False
                else:
                    print(f"✅ Груз {self.target_cargo_number} успешно удален из списка размещения!")
                    return True
            else:
                print(f"❌ Ошибка проверки: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение при проверке: {e}")
            return False
    
    def analyze_cargo_dependencies(self):
        """Анализ зависимостей груза, которые могут блокировать удаление"""
        print(f"\n🔗 Анализ зависимостей груза {self.target_cargo_number}...")
        
        if not self.cargo_data:
            print("⚠️ Нет данных о грузе для анализа")
            return
        
        print(f"🔍 Анализ полей груза на предмет блокирующих зависимостей:")
        
        # Проверяем критические поля
        critical_fields = [
            'status', 'processing_status', 'payment_status',
            'warehouse_id', 'block_number', 'shelf_number', 'cell_number',
            'assigned_courier_id', 'transport_id', 'placed_by_operator_id'
        ]
        
        blocking_factors = []
        
        for field in critical_fields:
            value = self.cargo_data.get(field)
            if value and value != 'N/A' and value != '':
                print(f"   ⚠️ {field}: {value} (может блокировать удаление)")
                blocking_factors.append(f"{field}={value}")
            else:
                print(f"   ✅ {field}: {value or 'не установлено'}")
        
        if blocking_factors:
            print(f"\n🚨 НАЙДЕНЫ ПОТЕНЦИАЛЬНЫЕ БЛОКИРУЮЩИЕ ФАКТОРЫ:")
            for factor in blocking_factors:
                print(f"   - {factor}")
            
            print(f"\n💡 РЕКОМЕНДАЦИИ:")
            print(f"   1. Проверить, не размещен ли груз в ячейке склада")
            print(f"   2. Проверить, не назначен ли груз курьеру")
            print(f"   3. Проверить, не загружен ли груз в транспорт")
            print(f"   4. Проверить статус оплаты и обработки")
        else:
            print(f"\n✅ Блокирующих факторов не найдено")
    
    def run_comprehensive_deletion_test(self):
        """Запуск комплексного тестирования удаления груза 100008/02"""
        print("=" * 80)
        print("🎯 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Удаление груза 100008/02")
        print("=" * 80)
        
        # Шаг 1: Авторизация
        if not self.authenticate_admin():
            print("\n❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться")
            return False
        
        # Шаг 2: Получение детальной информации о грузе
        if not self.get_detailed_cargo_info():
            print("\n❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить информацию о грузе")
            return False
        
        # Шаг 3: Анализ зависимостей
        self.analyze_cargo_dependencies()
        
        # Шаг 4: Тестирование единичного удаления
        single_deletion_success = self.test_single_cargo_deletion()
        
        if single_deletion_success:
            # Проверяем удаление
            if self.verify_cargo_removal():
                print(f"\n🎉 УСПЕХ: Груз {self.target_cargo_number} успешно удален единичным способом!")
                return True
        
        # Шаг 5: Тестирование массового удаления
        bulk_deletion_success = self.test_bulk_cargo_deletion()
        
        if bulk_deletion_success:
            # Проверяем удаление
            if self.verify_cargo_removal():
                print(f"\n🎉 УСПЕХ: Груз {self.target_cargo_number} успешно удален массовым способом!")
                return True
        
        # Шаг 6: Тестирование изменения статуса
        status_change_success = self.test_cargo_status_change()
        
        if status_change_success:
            # Проверяем удаление
            if self.verify_cargo_removal():
                print(f"\n🎉 УСПЕХ: Груз {self.target_cargo_number} успешно удален через изменение статуса!")
                return True
        
        # Финальная проверка
        print(f"\n" + "=" * 80)
        print(f"🎯 ФИНАЛЬНЫЙ РЕЗУЛЬТАТ ТЕСТИРОВАНИЯ")
        print(f"=" * 80)
        
        if not self.verify_cargo_removal():
            print(f"❌ ПРОБЛЕМА ПОДТВЕРЖДЕНА: Груз {self.target_cargo_number} НЕ УДАЛЯЕТСЯ!")
            print(f"\n🔍 ДИАГНОСТИРОВАННЫЕ ПРОБЛЕМЫ:")
            print(f"   1. Единичное удаление не работает")
            print(f"   2. Массовое удаление не работает") 
            print(f"   3. Изменение статуса не работает")
            
            print(f"\n💡 РЕКОМЕНДУЕМЫЕ РЕШЕНИЯ:")
            print(f"   1. Проверить backend код для endpoint'ов удаления")
            print(f"   2. Проверить права доступа администратора")
            print(f"   3. Проверить блокирующие зависимости в базе данных")
            print(f"   4. Проверить логи backend сервера")
            
            return False
        else:
            print(f"✅ Груз {self.target_cargo_number} успешно удален!")
            return True

def main():
    """Главная функция для запуска тестирования удаления"""
    test = SpecificCargoDeletionTest()
    
    try:
        success = test.run_comprehensive_deletion_test()
        
        if success:
            print("\n🎉 Тестирование удаления завершено успешно!")
        else:
            print("\n❌ Тестирование удаления выявило проблемы!")
            
    except KeyboardInterrupt:
        print("\n⚠️ Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка тестирования: {e}")

if __name__ == "__main__":
    main()
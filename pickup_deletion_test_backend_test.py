#!/usr/bin/env python3
"""
ФИНАЛЬНАЯ ДИАГНОСТИКА: Создание заявок на забор для тестирования массового удаления
"""

import requests
import json
import sys
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://tajline-cargo-8.preview.emergentagent.com/api"
ADMIN_PHONE = "+79999888777"
ADMIN_PASSWORD = "admin123"

class PickupRequestCreationTest:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        
    def authenticate_admin(self):
        """Авторизация администратора"""
        login_data = {
            "phone": ADMIN_PHONE,
            "password": ADMIN_PASSWORD
        }
        
        response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            self.admin_token = data.get("access_token")
            self.session.headers.update({
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            })
            print(f"✅ Авторизация успешна: {data.get('user', {}).get('full_name')}")
            return True
        else:
            print(f"❌ Ошибка авторизации: {response.text}")
            return False
    
    def create_test_cargo_requests(self):
        """Создание тестовых заявок на груз для генерации заявок на забор"""
        print("\n📦 СОЗДАНИЕ ТЕСТОВЫХ ЗАЯВОК НА ГРУЗ...")
        
        test_requests = [
            {
                "recipient_full_name": "Тестовый Получатель 1",
                "recipient_phone": "+992123456789",
                "recipient_address": "Душанбе, ул. Тестовая 1",
                "pickup_address": "Москва, ул. Тестовая 1",
                "cargo_name": "Тестовый груз для забора 1",
                "weight": 5.0,
                "declared_value": 1000.0,
                "description": "Тестовый груз для проверки массового удаления заявок на забор",
                "route": "moscow_to_tajikistan"
            },
            {
                "recipient_full_name": "Тестовый Получатель 2", 
                "recipient_phone": "+992123456790",
                "recipient_address": "Душанбе, ул. Тестовая 2",
                "pickup_address": "Москва, ул. Тестовая 2",
                "cargo_name": "Тестовый груз для забора 2",
                "weight": 3.0,
                "declared_value": 500.0,
                "description": "Тестовый груз для проверки массового удаления заявок на забор",
                "route": "moscow_to_tajikistan"
            },
            {
                "recipient_full_name": "Тестовый Получатель 3",
                "recipient_phone": "+992123456791", 
                "recipient_address": "Душанбе, ул. Тестовая 3",
                "pickup_address": "Москва, ул. Тестовая 3",
                "cargo_name": "Тестовый груз для забора 3",
                "weight": 7.0,
                "declared_value": 1500.0,
                "description": "Тестовый груз для проверки массового удаления заявок на забор",
                "route": "moscow_to_tajikistan"
            }
        ]
        
        created_requests = []
        
        for i, request_data in enumerate(test_requests):
            print(f"\n   📦 Создание заявки {i+1}...")
            
            try:
                response = self.session.post(f"{BACKEND_URL}/cargo-requests", json=request_data)
                print(f"      POST /api/cargo-requests - Status: {response.status_code}")
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    created_requests.append(data)
                    print(f"      ✅ Заявка создана: {data.get('request_number', 'unknown')}")
                    print(f"         ID: {data.get('id')}")
                    print(f"         Груз: {data.get('cargo_name')}")
                else:
                    print(f"      ❌ Ошибка создания заявки: {response.text}")
                    
            except Exception as e:
                print(f"      ❌ Исключение при создании заявки: {e}")
        
        print(f"\n   📊 Создано заявок: {len(created_requests)}/{len(test_requests)}")
        return created_requests
    
    def check_pickup_requests_after_creation(self):
        """Проверка заявок на забор после создания заявок на груз"""
        print(f"\n🔍 ПРОВЕРКА ЗАЯВОК НА ЗАБОР ПОСЛЕ СОЗДАНИЯ...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/pickup-requests")
            print(f"   GET /api/operator/pickup-requests - Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                pickup_requests = data.get("pickup_requests", [])
                total_count = data.get("total_count", 0)
                
                print(f"   📋 Всего заявок на забор: {total_count}")
                print(f"   📋 Активных заявок: {len(pickup_requests)}")
                
                if pickup_requests:
                    print("   📋 Заявки на забор:")
                    for i, req in enumerate(pickup_requests):
                        print(f"      {i+1}. ID: {req.get('id')}")
                        print(f"         Номер: {req.get('request_number')}")
                        print(f"         Статус: {req.get('status')}")
                        print(f"         Груз: {req.get('cargo_name', 'unknown')}")
                
                return pickup_requests, total_count
            else:
                print(f"   ❌ Ошибка получения заявок на забор: {response.text}")
                return [], 0
                
        except Exception as e:
            print(f"   ❌ Исключение при получении заявок на забор: {e}")
            return [], 0
    
    def test_bulk_deletion_of_pickup_requests(self, pickup_requests):
        """Тестирование массового удаления заявок на забор"""
        print(f"\n🗑️ ТЕСТИРОВАНИЕ МАССОВОГО УДАЛЕНИЯ ЗАЯВОК НА ЗАБОР...")
        
        if not pickup_requests:
            print("   ⚠️ Нет заявок на забор для тестирования")
            return False
        
        # Берем все доступные заявки для тестирования
        test_requests = pickup_requests[:3]  # Максимум 3 для тестирования
        print(f"   📋 Выбрано {len(test_requests)} заявок для массового удаления")
        
        # Показываем что будем удалять
        print(f"   📋 Заявки для удаления:")
        for i, req in enumerate(test_requests):
            print(f"      {i+1}. {req.get('request_number')} (ID: {req.get('id')})")
        
        # Пробуем массовое удаление через разные endpoints
        deletion_endpoints = [
            "/admin/cargo-applications/bulk-delete",
            "/operator/pickup-requests/bulk-delete", 
            "/admin/pickup-requests/bulk-delete"
        ]
        
        request_ids = [req.get("id") for req in test_requests]
        
        successful_deletions = 0
        
        for endpoint in deletion_endpoints:
            print(f"\n   🗑️ Попытка массового удаления через {endpoint}...")
            
            try:
                # Пробуем разные форматы payload
                payloads_to_try = [
                    {"request_ids": request_ids},
                    {"ids": request_ids},
                    {"pickup_request_ids": request_ids},
                    {"cargo_application_ids": request_ids}
                ]
                
                for payload in payloads_to_try:
                    try:
                        response = self.session.delete(f"{BACKEND_URL}{endpoint}", json=payload)
                        print(f"      DELETE {endpoint} (payload: {list(payload.keys())[0]}) - Status: {response.status_code}")
                        
                        if response.status_code in [200, 204]:
                            print(f"      ✅ Массовое удаление успешно!")
                            print(f"      📄 Ответ: {response.text}")
                            successful_deletions += len(request_ids)
                            break
                        else:
                            print(f"      ❌ Ошибка: {response.text}")
                            
                    except Exception as e:
                        print(f"      ❌ Исключение: {e}")
                
                if successful_deletions > 0:
                    break
                    
            except Exception as e:
                print(f"   ❌ Общее исключение для {endpoint}: {e}")
        
        # Если массовое удаление не сработало, пробуем по одной
        if successful_deletions == 0:
            print(f"\n   🗑️ Массовое удаление не сработало, пробуем удалять по одной...")
            
            for i, request in enumerate(test_requests):
                request_id = request.get("id")
                request_number = request.get("request_number")
                
                print(f"\n      🗑️ Удаление заявки {i+1}: {request_number}")
                
                # Пробуем разные endpoints для единичного удаления
                single_deletion_endpoints = [
                    f"/admin/cargo-applications/{request_id}",
                    f"/operator/pickup-requests/{request_id}",
                    f"/admin/pickup-requests/{request_id}"
                ]
                
                deleted = False
                for endpoint in single_deletion_endpoints:
                    try:
                        response = self.session.delete(f"{BACKEND_URL}{endpoint}")
                        print(f"         DELETE {endpoint} - Status: {response.status_code}")
                        
                        if response.status_code in [200, 204]:
                            print(f"         ✅ Заявка удалена!")
                            successful_deletions += 1
                            deleted = True
                            break
                        else:
                            print(f"         ❌ Ошибка: {response.text}")
                            
                    except Exception as e:
                        print(f"         ❌ Исключение: {e}")
                
                if not deleted:
                    print(f"         ❌ Не удалось удалить заявку {request_number}")
        
        # Проверяем результат
        print(f"\n   📊 РЕЗУЛЬТАТ МАССОВОГО УДАЛЕНИЯ:")
        print(f"   ✅ Успешно удалено: {successful_deletions}/{len(test_requests)}")
        
        if successful_deletions > 0:
            # Проверяем, действительно ли заявки удалились
            print(f"\n   🔍 ПРОВЕРКА ФАКТИЧЕСКОГО УДАЛЕНИЯ...")
            pickup_requests_after, total_after = self.check_pickup_requests_after_creation()
            
            print(f"   📊 Заявок было: {len(pickup_requests)}")
            print(f"   📊 Заявок стало: {total_after}")
            print(f"   📊 Ожидаемая разница: {successful_deletions}")
            print(f"   📊 Фактическая разница: {len(pickup_requests) - total_after}")
            
            if len(pickup_requests) - total_after >= successful_deletions:
                print(f"   ✅ МАССОВОЕ УДАЛЕНИЕ РАБОТАЕТ!")
                return True
            else:
                print(f"   ❌ ПРОБЛЕМА: Заявки не удалились полностью")
                return False
        else:
            print(f"   ❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: НИ ОДНА ЗАЯВКА НЕ БЫЛА УДАЛЕНА!")
            return False
    
    def run_pickup_deletion_test(self):
        """Запуск полного теста удаления заявок на забор"""
        print("=" * 80)
        print("🧪 ТЕСТ МАССОВОГО УДАЛЕНИЯ ЗАЯВОК НА ЗАБОР")
        print("=" * 80)
        
        # Авторизация
        if not self.authenticate_admin():
            return False
        
        # Проверяем текущее состояние
        initial_pickup_requests, initial_count = self.check_pickup_requests_after_creation()
        print(f"📊 Начальное количество заявок на забор: {initial_count}")
        
        # Создаем тестовые заявки на груз (которые должны генерировать заявки на забор)
        created_requests = self.create_test_cargo_requests()
        
        # Проверяем, появились ли заявки на забор
        pickup_requests_after_creation, count_after_creation = self.check_pickup_requests_after_creation()
        
        if count_after_creation > initial_count:
            print(f"✅ Заявки на забор появились: {count_after_creation - initial_count} новых")
            
            # Тестируем массовое удаление
            deletion_success = self.test_bulk_deletion_of_pickup_requests(pickup_requests_after_creation)
            
            # Итоговый отчет
            print(f"\n" + "=" * 80)
            print("📊 ИТОГОВЫЙ ОТЧЕТ")
            print("=" * 80)
            
            print(f"📦 Создано заявок на груз: {len(created_requests)}")
            print(f"📋 Появилось заявок на забор: {count_after_creation - initial_count}")
            
            if deletion_success:
                print(f"✅ МАССОВОЕ УДАЛЕНИЕ ЗАЯВОК НА ЗАБОР: РАБОТАЕТ")
            else:
                print(f"❌ МАССОВОЕ УДАЛЕНИЕ ЗАЯВОК НА ЗАБОР: НЕ РАБОТАЕТ")
            
            return deletion_success
            
        else:
            print(f"⚠️ Заявки на забор не появились после создания заявок на груз")
            print(f"   Это может означать что:")
            print(f"   1. Заявки на забор создаются по другой логике")
            print(f"   2. Требуется дополнительный шаг для активации заявок на забор")
            print(f"   3. Заявки на забор создаются автоматически при других условиях")
            
            return False

def main():
    test = PickupRequestCreationTest()
    
    try:
        success = test.run_pickup_deletion_test()
        
        if success:
            print(f"\n✅ Тест завершен успешно")
            sys.exit(0)
        else:
            print(f"\n❌ Тест завершен с проблемами")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Критическая ошибка теста: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
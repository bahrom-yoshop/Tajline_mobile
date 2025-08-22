#!/usr/bin/env python3
"""
ФИНАЛЬНОЕ РЕШЕНИЕ: Тестирование правильных endpoints для удаления грузов из секции "На Забор"

Найденные правильные endpoints:
1. DELETE /api/admin/pickup-requests/bulk - массовое удаление заявок на забор
2. DELETE /api/admin/cargo-applications/{request_id} - удаление заявки на груз
3. DELETE /api/admin/cargo-applications/bulk - массовое удаление заявок на груз
4. DELETE /api/operator/cargo/{cargo_id}/remove-from-placement - удаление груза из размещения
5. DELETE /api/operator/cargo/bulk-remove-from-placement - массовое удаление грузов из размещения
"""

import requests
import json
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://tajline-cargo-7.preview.emergentagent.com/api"

class FinalPickupDeletionTest:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        
    def log(self, message):
        """Логирование с временной меткой"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def authenticate_warehouse_operator(self):
        """Авторизация оператора склада"""
        self.log("🔐 Авторизация оператора склада (+79777888999/warehouse123)")
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "phone": "+79777888999",
                "password": "warehouse123"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log(f"✅ Успешная авторизация: {data.get('user', {}).get('full_name')}")
                return True
            else:
                self.log(f"❌ Ошибка авторизации: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при авторизации: {e}")
            return False
    
    def get_pickup_data(self):
        """Получение данных для тестирования удаления"""
        self.log("📋 ПОЛУЧЕНИЕ ДАННЫХ ДЛЯ ТЕСТИРОВАНИЯ УДАЛЕНИЯ")
        
        data = {
            'cargo_requests': [],
            'pickup_requests': [],
            'notifications': [],
            'available_cargo': []
        }
        
        # 1. Заявки на грузы (cargo-requests)
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/cargo-requests")
            if response.status_code == 200:
                data['cargo_requests'] = response.json()
                self.log(f"   ✅ Заявки на грузы: {len(data['cargo_requests'])}")
            else:
                self.log(f"   ❌ Ошибка получения заявок на грузы: {response.status_code}")
        except Exception as e:
            self.log(f"   ❌ Исключение при получении заявок на грузы: {e}")
        
        # 2. Заявки на забор (pickup-requests)
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/pickup-requests")
            if response.status_code == 200:
                pickup_data = response.json()
                data['pickup_requests'] = pickup_data.get('pickup_requests', [])
                self.log(f"   ✅ Заявки на забор: {len(data['pickup_requests'])}")
            else:
                self.log(f"   ❌ Ошибка получения заявок на забор: {response.status_code}")
        except Exception as e:
            self.log(f"   ❌ Исключение при получении заявок на забор: {e}")
        
        # 3. Уведомления склада
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/warehouse-notifications")
            if response.status_code == 200:
                notif_data = response.json()
                data['notifications'] = notif_data.get('notifications', [])
                self.log(f"   ✅ Уведомления склада: {len(data['notifications'])}")
            else:
                self.log(f"   ❌ Ошибка получения уведомлений: {response.status_code}")
        except Exception as e:
            self.log(f"   ❌ Исключение при получении уведомлений: {e}")
        
        # 4. Доступные грузы для размещения
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/available-for-placement")
            if response.status_code == 200:
                cargo_data = response.json()
                data['available_cargo'] = cargo_data.get('items', [])
                self.log(f"   ✅ Доступные грузы: {len(data['available_cargo'])}")
            else:
                self.log(f"   ❌ Ошибка получения доступных грузов: {response.status_code}")
        except Exception as e:
            self.log(f"   ❌ Исключение при получении доступных грузов: {e}")
        
        return data
    
    def test_cargo_applications_deletion(self, cargo_requests):
        """Тестирование удаления заявок на груз"""
        self.log("🗑️ ТЕСТИРОВАНИЕ УДАЛЕНИЯ ЗАЯВОК НА ГРУЗ")
        
        if not cargo_requests:
            self.log("   ❌ Нет заявок на груз для тестирования")
            return False
        
        # Тестируем единичное удаление
        test_request = cargo_requests[0]
        request_id = test_request.get('id')
        
        self.log(f"   🎯 Тестовая заявка:")
        self.log(f"     - ID: {request_id}")
        self.log(f"     - Номер: {test_request.get('request_number')}")
        self.log(f"     - Груз: {test_request.get('cargo_name')}")
        
        try:
            self.log(f"   🔧 ТЕСТИРУЕМ: DELETE /admin/cargo-applications/{request_id}")
            response = self.session.delete(f"{BACKEND_URL}/admin/cargo-applications/{request_id}")
            
            self.log(f"     - Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                self.log(f"     - ✅ УСПЕШНОЕ УДАЛЕНИЕ ЗАЯВКИ НА ГРУЗ!")
                self.log(f"     - Ответ: {response.text}")
                return True
            elif response.status_code == 404:
                self.log(f"     - ❌ ЗАЯВКА НЕ НАЙДЕНА")
            elif response.status_code == 403:
                self.log(f"     - ❌ НЕТ ПРАВ ДОСТУПА")
            else:
                self.log(f"     - ❌ ОШИБКА: {response.text}")
                
        except Exception as e:
            self.log(f"     - ❌ ИСКЛЮЧЕНИЕ: {e}")
        
        return False
    
    def test_bulk_cargo_applications_deletion(self, cargo_requests):
        """Тестирование массового удаления заявок на груз"""
        self.log("📦 ТЕСТИРОВАНИЕ МАССОВОГО УДАЛЕНИЯ ЗАЯВОК НА ГРУЗ")
        
        if len(cargo_requests) < 2:
            self.log("   ❌ Недостаточно заявок для массового удаления")
            return False
        
        # Берем первые 2 заявки для тестирования
        test_ids = [req['id'] for req in cargo_requests[:2]]
        
        self.log(f"   🎯 Тестовые заявки: {len(test_ids)} шт.")
        for i, req_id in enumerate(test_ids):
            request = cargo_requests[i]
            self.log(f"     {i+1}. {request.get('request_number')} - {request.get('cargo_name')}")
        
        try:
            self.log(f"   🔧 ТЕСТИРУЕМ: DELETE /admin/cargo-applications/bulk")
            response = self.session.delete(f"{BACKEND_URL}/admin/cargo-applications/bulk", json={
                "request_ids": test_ids
            })
            
            self.log(f"     - Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                self.log(f"     - ✅ УСПЕШНОЕ МАССОВОЕ УДАЛЕНИЕ ЗАЯВОК!")
                self.log(f"     - Ответ: {response.text}")
                return True
            elif response.status_code == 404:
                self.log(f"     - ❌ ENDPOINT НЕ НАЙДЕН")
            elif response.status_code == 403:
                self.log(f"     - ❌ НЕТ ПРАВ ДОСТУПА")
            else:
                self.log(f"     - ❌ ОШИБКА: {response.text}")
                
        except Exception as e:
            self.log(f"     - ❌ ИСКЛЮЧЕНИЕ: {e}")
        
        return False
    
    def test_pickup_requests_bulk_deletion(self, notifications):
        """Тестирование массового удаления заявок на забор"""
        self.log("🚚 ТЕСТИРОВАНИЕ МАССОВОГО УДАЛЕНИЯ ЗАЯВОК НА ЗАБОР")
        
        if not notifications:
            self.log("   ❌ Нет уведомлений с pickup_request_id")
            return False
        
        # Извлекаем pickup_request_id из уведомлений
        pickup_request_ids = []
        for notif in notifications:
            pickup_id = notif.get('pickup_request_id')
            if pickup_id and pickup_id not in pickup_request_ids:
                pickup_request_ids.append(pickup_id)
        
        if not pickup_request_ids:
            self.log("   ❌ Не найдено pickup_request_id в уведомлениях")
            return False
        
        # Берем первые 2 ID для тестирования
        test_ids = pickup_request_ids[:2]
        
        self.log(f"   🎯 Тестовые pickup_request_id: {test_ids}")
        
        try:
            self.log(f"   🔧 ТЕСТИРУЕМ: DELETE /admin/pickup-requests/bulk")
            response = self.session.delete(f"{BACKEND_URL}/admin/pickup-requests/bulk", json={
                "request_ids": test_ids
            })
            
            self.log(f"     - Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                self.log(f"     - ✅ УСПЕШНОЕ МАССОВОЕ УДАЛЕНИЕ ЗАЯВОК НА ЗАБОР!")
                self.log(f"     - Ответ: {response.text}")
                return True
            elif response.status_code == 404:
                self.log(f"     - ❌ ENDPOINT НЕ НАЙДЕН")
            elif response.status_code == 403:
                self.log(f"     - ❌ НЕТ ПРАВ ДОСТУПА")
            else:
                self.log(f"     - ❌ ОШИБКА: {response.text}")
                
        except Exception as e:
            self.log(f"     - ❌ ИСКЛЮЧЕНИЕ: {e}")
        
        return False
    
    def test_cargo_removal_from_placement(self, available_cargo):
        """Тестирование удаления грузов из размещения"""
        self.log("📦 ТЕСТИРОВАНИЕ УДАЛЕНИЯ ГРУЗОВ ИЗ РАЗМЕЩЕНИЯ")
        
        if not available_cargo:
            self.log("   ❌ Нет доступных грузов для тестирования")
            return False
        
        # Тестируем единичное удаление
        test_cargo = available_cargo[0]
        cargo_id = test_cargo.get('id')
        
        self.log(f"   🎯 Тестовый груз:")
        self.log(f"     - ID: {cargo_id}")
        self.log(f"     - Номер: {test_cargo.get('cargo_number')}")
        self.log(f"     - Отправитель: {test_cargo.get('sender_full_name')}")
        
        try:
            self.log(f"   🔧 ТЕСТИРУЕМ: DELETE /operator/cargo/{cargo_id}/remove-from-placement")
            response = self.session.delete(f"{BACKEND_URL}/operator/cargo/{cargo_id}/remove-from-placement")
            
            self.log(f"     - Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                self.log(f"     - ✅ УСПЕШНОЕ УДАЛЕНИЕ ГРУЗА ИЗ РАЗМЕЩЕНИЯ!")
                self.log(f"     - Ответ: {response.text}")
                return True
            elif response.status_code == 404:
                self.log(f"     - ❌ ГРУЗ НЕ НАЙДЕН")
            elif response.status_code == 403:
                self.log(f"     - ❌ НЕТ ПРАВ ДОСТУПА")
            else:
                self.log(f"     - ❌ ОШИБКА: {response.text}")
                
        except Exception as e:
            self.log(f"     - ❌ ИСКЛЮЧЕНИЕ: {e}")
        
        return False
    
    def test_bulk_cargo_removal_from_placement(self, available_cargo):
        """Тестирование массового удаления грузов из размещения"""
        self.log("📦 ТЕСТИРОВАНИЕ МАССОВОГО УДАЛЕНИЯ ГРУЗОВ ИЗ РАЗМЕЩЕНИЯ")
        
        if len(available_cargo) < 2:
            self.log("   ❌ Недостаточно грузов для массового удаления")
            return False
        
        # Берем первые 2 груза для тестирования
        test_cargo_ids = [cargo['id'] for cargo in available_cargo[:2]]
        
        self.log(f"   🎯 Тестовые грузы: {len(test_cargo_ids)} шт.")
        for i, cargo_id in enumerate(test_cargo_ids):
            cargo = available_cargo[i]
            self.log(f"     {i+1}. {cargo.get('cargo_number')} - {cargo.get('sender_full_name')}")
        
        try:
            self.log(f"   🔧 ТЕСТИРУЕМ: DELETE /operator/cargo/bulk-remove-from-placement")
            response = self.session.delete(f"{BACKEND_URL}/operator/cargo/bulk-remove-from-placement", json={
                "cargo_ids": test_cargo_ids
            })
            
            self.log(f"     - Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                self.log(f"     - ✅ УСПЕШНОЕ МАССОВОЕ УДАЛЕНИЕ ГРУЗОВ ИЗ РАЗМЕЩЕНИЯ!")
                self.log(f"     - Ответ: {response.text}")
                return True
            elif response.status_code == 404:
                self.log(f"     - ❌ ENDPOINT НЕ НАЙДЕН")
            elif response.status_code == 403:
                self.log(f"     - ❌ НЕТ ПРАВ ДОСТУПА")
            else:
                self.log(f"     - ❌ ОШИБКА: {response.text}")
                
        except Exception as e:
            self.log(f"     - ❌ ИСКЛЮЧЕНИЕ: {e}")
        
        return False
    
    def run_final_test(self):
        """Запуск финального тестирования с правильными endpoints"""
        self.log("🚀 НАЧАЛО ФИНАЛЬНОГО ТЕСТИРОВАНИЯ УДАЛЕНИЯ ГРУЗОВ ИЗ СЕКЦИИ 'НА ЗАБОР'")
        self.log("🎯 ИСПОЛЬЗУЕМ ПРАВИЛЬНЫЕ ENDPOINTS ИЗ BACKEND КОДА")
        self.log("=" * 80)
        
        # Авторизация
        if not self.authenticate_warehouse_operator():
            return
        
        # Получение данных
        data = self.get_pickup_data()
        
        # Результаты тестирования
        results = {
            'cargo_applications_single': False,
            'cargo_applications_bulk': False,
            'pickup_requests_bulk': False,
            'cargo_removal_single': False,
            'cargo_removal_bulk': False
        }
        
        # Тестирование различных подходов
        if data['cargo_requests']:
            results['cargo_applications_single'] = self.test_cargo_applications_deletion(data['cargo_requests'])
            results['cargo_applications_bulk'] = self.test_bulk_cargo_applications_deletion(data['cargo_requests'])
        
        if data['notifications']:
            results['pickup_requests_bulk'] = self.test_pickup_requests_bulk_deletion(data['notifications'])
        
        if data['available_cargo']:
            results['cargo_removal_single'] = self.test_cargo_removal_from_placement(data['available_cargo'])
            results['cargo_removal_bulk'] = self.test_bulk_cargo_removal_from_placement(data['available_cargo'])
        
        # Финальный отчет
        self.log("=" * 80)
        self.log("📊 ФИНАЛЬНЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ ПРАВИЛЬНЫХ ENDPOINTS:")
        
        working_methods = []
        for method, success in results.items():
            status = "✅ РАБОТАЕТ" if success else "❌ НЕ РАБОТАЕТ"
            self.log(f"   {method}: {status}")
            if success:
                working_methods.append(method)
        
        self.log(f"   📈 ИТОГО РАБОЧИХ МЕТОДОВ: {len(working_methods)}")
        
        if working_methods:
            self.log("   🎯 НАЙДЕННЫЕ РАБОЧИЕ СПОСОБЫ УДАЛЕНИЯ ГРУЗОВ ИЗ СЕКЦИИ 'НА ЗАБОР':")
            
            if 'cargo_applications_single' in working_methods:
                self.log("     1. ✅ ЕДИНИЧНОЕ УДАЛЕНИЕ ЗАЯВОК НА ГРУЗ:")
                self.log("        - Endpoint: DELETE /admin/cargo-applications/{request_id}")
                self.log("        - Удаляет заявку на груз, что убирает груз из секции 'На Забор'")
            
            if 'cargo_applications_bulk' in working_methods:
                self.log("     2. ✅ МАССОВОЕ УДАЛЕНИЕ ЗАЯВОК НА ГРУЗ:")
                self.log("        - Endpoint: DELETE /admin/cargo-applications/bulk")
                self.log("        - Массовое удаление заявок на груз")
            
            if 'pickup_requests_bulk' in working_methods:
                self.log("     3. ✅ МАССОВОЕ УДАЛЕНИЕ ЗАЯВОК НА ЗАБОР:")
                self.log("        - Endpoint: DELETE /admin/pickup-requests/bulk")
                self.log("        - Прямое удаление заявок на забор")
            
            if 'cargo_removal_single' in working_methods:
                self.log("     4. ✅ ЕДИНИЧНОЕ УДАЛЕНИЕ ГРУЗОВ ИЗ РАЗМЕЩЕНИЯ:")
                self.log("        - Endpoint: DELETE /operator/cargo/{cargo_id}/remove-from-placement")
                self.log("        - Удаляет груз из списка размещения")
            
            if 'cargo_removal_bulk' in working_methods:
                self.log("     5. ✅ МАССОВОЕ УДАЛЕНИЕ ГРУЗОВ ИЗ РАЗМЕЩЕНИЯ:")
                self.log("        - Endpoint: DELETE /operator/cargo/bulk-remove-from-placement")
                self.log("        - Массовое удаление грузов из размещения")
        else:
            self.log("   ❌ НЕ НАЙДЕНО РАБОЧИХ МЕТОДОВ УДАЛЕНИЯ")
            self.log("   💡 ВОЗМОЖНЫЕ ПРИЧИНЫ:")
            self.log("     - Проблема с правами доступа (нужна роль admin для некоторых endpoints)")
            self.log("     - Неправильная структура данных в запросах")
            self.log("     - Endpoints требуют специальной авторизации")
        
        self.log("🏁 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        
        return working_methods

if __name__ == "__main__":
    test = FinalPickupDeletionTest()
    working_methods = test.run_final_test()
    
    if working_methods:
        print("\n🎉 РЕШЕНИЕ НАЙДЕНО!")
        print("Рабочие способы удаления грузов из секции 'На Забор':")
        for method in working_methods:
            print(f"  - {method}")
    else:
        print("\n❌ РЕШЕНИЕ НЕ НАЙДЕНО")
        print("Требуется дополнительное исследование backend кода")
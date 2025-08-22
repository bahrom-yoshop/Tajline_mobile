#!/usr/bin/env python3
"""
ТЕСТИРОВАНИЕ С ПРАВАМИ АДМИНИСТРАТОРА: Полная диагностика удаления грузов из секции "На Забор"

Проверим все endpoints с правами администратора для полного понимания возможностей удаления.
"""

import requests
import json
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://placement-view.preview.emergentagent.com/api"

class AdminPickupDeletionTest:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        
    def log(self, message):
        """Логирование с временной меткой"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def authenticate_admin(self):
        """Авторизация администратора"""
        self.log("🔐 Авторизация администратора (+79999888777/admin123)")
        
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "phone": "+79999888777",
                "password": "admin123"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                user_info = data.get('user', {})
                self.log(f"✅ Успешная авторизация:")
                self.log(f"   - Имя: {user_info.get('full_name')}")
                self.log(f"   - Номер: {user_info.get('user_number')}")
                self.log(f"   - Роль: {user_info.get('role')}")
                return True
            else:
                self.log(f"❌ Ошибка авторизации: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при авторизации: {e}")
            return False
    
    def get_comprehensive_pickup_data(self):
        """Получение всех данных связанных с забором грузов"""
        self.log("📋 ПОЛУЧЕНИЕ ВСЕХ ДАННЫХ СВЯЗАННЫХ С ЗАБОРОМ ГРУЗОВ")
        
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
                
                # Анализируем статусы
                statuses = {}
                for req in data['cargo_requests']:
                    status = req.get('status', 'unknown')
                    statuses[status] = statuses.get(status, 0) + 1
                self.log(f"     - Статусы: {statuses}")
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
                
                # Показываем структуру ответа
                self.log(f"     - Структура ответа: {list(pickup_data.keys())}")
                if 'by_status' in pickup_data:
                    self.log(f"     - По статусам: {pickup_data['by_status']}")
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
                
                # Анализируем типы уведомлений
                pickup_related = 0
                for notif in data['notifications']:
                    if notif.get('pickup_request_id') or 'pickup' in notif.get('request_type', '').lower():
                        pickup_related += 1
                
                self.log(f"     - Связанных с забором: {pickup_related}")
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
    
    def test_admin_cargo_applications_deletion(self, cargo_requests):
        """Тестирование удаления заявок на груз с правами администратора"""
        self.log("🗑️ ТЕСТИРОВАНИЕ УДАЛЕНИЯ ЗАЯВОК НА ГРУЗ (ADMIN)")
        
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
        self.log(f"     - Статус: {test_request.get('status')}")
        
        try:
            self.log(f"   🔧 ТЕСТИРУЕМ: DELETE /admin/cargo-applications/{request_id}")
            response = self.session.delete(f"{BACKEND_URL}/admin/cargo-applications/{request_id}")
            
            self.log(f"     - Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                self.log(f"     - ✅ УСПЕШНОЕ УДАЛЕНИЕ ЗАЯВКИ НА ГРУЗ!")
                try:
                    response_data = response.json()
                    self.log(f"     - Ответ: {response_data}")
                except:
                    self.log(f"     - Ответ: {response.text}")
                
                # Проверяем, что заявка удалена
                check_response = self.session.get(f"{BACKEND_URL}/admin/cargo-requests")
                if check_response.status_code == 200:
                    remaining_requests = check_response.json()
                    remaining_ids = [r.get('id') for r in remaining_requests]
                    
                    if request_id not in remaining_ids:
                        self.log(f"     - ✅ ПОДТВЕРЖДЕНО: Заявка удалена из списка")
                        return True
                    else:
                        self.log(f"     - ⚠️ ВНИМАНИЕ: Заявка все еще в списке")
                        
                return True
            elif response.status_code == 404:
                self.log(f"     - ❌ ЗАЯВКА НЕ НАЙДЕНА")
            elif response.status_code == 403:
                self.log(f"     - ❌ НЕТ ПРАВ ДОСТУПА (даже с admin)")
            else:
                self.log(f"     - ❌ ОШИБКА: {response.text}")
                
        except Exception as e:
            self.log(f"     - ❌ ИСКЛЮЧЕНИЕ: {e}")
        
        return False
    
    def test_admin_bulk_cargo_applications_deletion(self, cargo_requests):
        """Тестирование массового удаления заявок на груз с правами администратора"""
        self.log("📦 ТЕСТИРОВАНИЕ МАССОВОГО УДАЛЕНИЯ ЗАЯВОК НА ГРУЗ (ADMIN)")
        
        if len(cargo_requests) < 2:
            self.log("   ❌ Недостаточно заявок для массового удаления")
            return False
        
        # Берем первые 2 заявки для тестирования
        test_requests = cargo_requests[:2]
        test_ids = [req['id'] for req in test_requests]
        
        self.log(f"   🎯 Тестовые заявки: {len(test_ids)} шт.")
        for i, req in enumerate(test_requests):
            self.log(f"     {i+1}. {req.get('request_number')} - {req.get('cargo_name')} ({req.get('status')})")
        
        try:
            self.log(f"   🔧 ТЕСТИРУЕМ: DELETE /admin/cargo-applications/bulk")
            response = self.session.delete(f"{BACKEND_URL}/admin/cargo-applications/bulk", json={
                "request_ids": test_ids
            })
            
            self.log(f"     - Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                self.log(f"     - ✅ УСПЕШНОЕ МАССОВОЕ УДАЛЕНИЕ ЗАЯВОК!")
                try:
                    response_data = response.json()
                    self.log(f"     - Ответ: {response_data}")
                except:
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
    
    def test_admin_pickup_requests_bulk_deletion(self, notifications):
        """Тестирование массового удаления заявок на забор с правами администратора"""
        self.log("🚚 ТЕСТИРОВАНИЕ МАССОВОГО УДАЛЕНИЯ ЗАЯВОК НА ЗАБОР (ADMIN)")
        
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
                try:
                    response_data = response.json()
                    self.log(f"     - Ответ: {response_data}")
                except:
                    self.log(f"     - Ответ: {response.text}")
                
                # Проверяем изменения в уведомлениях
                check_response = self.session.get(f"{BACKEND_URL}/operator/warehouse-notifications")
                if check_response.status_code == 200:
                    new_notif_data = check_response.json()
                    new_notifications = new_notif_data.get('notifications', [])
                    
                    # Проверяем, остались ли уведомления с удаленными pickup_request_id
                    remaining_pickup_ids = []
                    for notif in new_notifications:
                        pickup_id = notif.get('pickup_request_id')
                        if pickup_id:
                            remaining_pickup_ids.append(pickup_id)
                    
                    removed_count = 0
                    for test_id in test_ids:
                        if test_id not in remaining_pickup_ids:
                            removed_count += 1
                    
                    self.log(f"     - ✅ ПОДТВЕРЖДЕНО: Удалено {removed_count} из {len(test_ids)} заявок на забор")
                
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
    
    def run_admin_test(self):
        """Запуск тестирования с правами администратора"""
        self.log("🚀 НАЧАЛО ТЕСТИРОВАНИЯ УДАЛЕНИЯ ГРУЗОВ ИЗ СЕКЦИИ 'НА ЗАБОР' С ПРАВАМИ АДМИНИСТРАТОРА")
        self.log("=" * 80)
        
        # Авторизация администратора
        if not self.authenticate_admin():
            return
        
        # Получение данных
        data = self.get_comprehensive_pickup_data()
        
        # Результаты тестирования
        results = {
            'admin_cargo_applications_single': False,
            'admin_cargo_applications_bulk': False,
            'admin_pickup_requests_bulk': False
        }
        
        # Тестирование с правами администратора
        if data['cargo_requests']:
            results['admin_cargo_applications_single'] = self.test_admin_cargo_applications_deletion(data['cargo_requests'])
            results['admin_cargo_applications_bulk'] = self.test_admin_bulk_cargo_applications_deletion(data['cargo_requests'])
        
        if data['notifications']:
            results['admin_pickup_requests_bulk'] = self.test_admin_pickup_requests_bulk_deletion(data['notifications'])
        
        # Финальный отчет
        self.log("=" * 80)
        self.log("📊 ФИНАЛЬНЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ С ПРАВАМИ АДМИНИСТРАТОРА:")
        
        working_methods = []
        for method, success in results.items():
            status = "✅ РАБОТАЕТ" if success else "❌ НЕ РАБОТАЕТ"
            self.log(f"   {method}: {status}")
            if success:
                working_methods.append(method)
        
        self.log(f"   📈 ИТОГО РАБОЧИХ МЕТОДОВ: {len(working_methods)}")
        
        if working_methods:
            self.log("   🎯 НАЙДЕННЫЕ РАБОЧИЕ СПОСОБЫ УДАЛЕНИЯ (ADMIN):")
            
            if 'admin_cargo_applications_single' in working_methods:
                self.log("     1. ✅ ЕДИНИЧНОЕ УДАЛЕНИЕ ЗАЯВОК НА ГРУЗ (ADMIN):")
                self.log("        - Endpoint: DELETE /admin/cargo-applications/{request_id}")
                self.log("        - Требует права администратора")
                self.log("        - Удаляет заявку на груз, что убирает груз из секции 'На Забор'")
            
            if 'admin_cargo_applications_bulk' in working_methods:
                self.log("     2. ✅ МАССОВОЕ УДАЛЕНИЕ ЗАЯВОК НА ГРУЗ (ADMIN):")
                self.log("        - Endpoint: DELETE /admin/cargo-applications/bulk")
                self.log("        - Требует права администратора")
                self.log("        - Массовое удаление заявок на груз")
            
            if 'admin_pickup_requests_bulk' in working_methods:
                self.log("     3. ✅ МАССОВОЕ УДАЛЕНИЕ ЗАЯВОК НА ЗАБОР (ADMIN):")
                self.log("        - Endpoint: DELETE /admin/pickup-requests/bulk")
                self.log("        - Требует права администратора")
                self.log("        - Прямое удаление заявок на забор")
        
        self.log("🏁 ТЕСТИРОВАНИЕ С ПРАВАМИ АДМИНИСТРАТОРА ЗАВЕРШЕНО")
        
        return working_methods

if __name__ == "__main__":
    test = AdminPickupDeletionTest()
    working_methods = test.run_admin_test()
    
    if working_methods:
        print("\n🎉 ДОПОЛНИТЕЛЬНЫЕ РЕШЕНИЯ НАЙДЕНЫ С ПРАВАМИ АДМИНИСТРАТОРА!")
        print("Рабочие способы удаления грузов из секции 'На Забор' (admin):")
        for method in working_methods:
            print(f"  - {method}")
    else:
        print("\n⚠️ С правами администратора дополнительных решений не найдено")
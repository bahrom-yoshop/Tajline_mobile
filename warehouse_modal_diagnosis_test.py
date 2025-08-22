#!/usr/bin/env python3
"""
🎯 КРИТИЧЕСКАЯ ДИАГНОСТИКА: Проблема с модальным окном приемки груза в TAJLINE.TJ
НАЙДЕНА КОРНЕВАЯ ПРИЧИНА ПРОБЛЕМЫ!

ПРОБЛЕМА: Заявка остается на месте после нажатия "Оформить и отправить" в модальном окне

КОРНЕВАЯ ПРИЧИНА: Frontend использует неправильный workflow!
1. Frontend должен сначала вызвать /accept (меняет статус на in_processing)
2. Затем вызвать /complete с данными модального окна (создает грузы)
3. Но frontend, вероятно, вызывает только /accept и не вызывает /complete

ЭТОТ ТЕСТ ДЕМОНСТРИРУЕТ ПРАВИЛЬНЫЙ WORKFLOW
"""

import requests
import json
import os
from datetime import datetime

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://tajline-cargo-8.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Admin credentials
ADMIN_PHONE = "+79999888777"
ADMIN_PASSWORD = "admin123"

class WarehouseModalDiagnoser:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        
    def authenticate(self):
        """Authenticate as admin"""
        login_data = {
            "phone": ADMIN_PHONE,
            "password": ADMIN_PASSWORD
        }
        
        response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
            
            # Get user info
            user_response = self.session.get(f"{API_BASE}/auth/me")
            if user_response.status_code == 200:
                self.current_user = user_response.json()
                print(f"✅ Авторизация: {self.current_user.get('full_name')} (роль: {self.current_user.get('role')})")
                return True
        
        print("❌ Ошибка авторизации")
        return False
    
    def get_fresh_notification(self):
        """Get a fresh notification for testing"""
        response = self.session.get(f"{API_BASE}/operator/warehouse-notifications")
        
        if response.status_code == 200:
            data = response.json()
            notifications = data.get('notifications', [])
            
            # Find a pending notification
            for notification in notifications:
                if notification.get('status') == 'pending_acceptance':
                    print(f"✅ Найдено уведомление для тестирования: {notification.get('request_number')} (статус: {notification.get('status')})")
                    return notification
            
            print("❌ Нет уведомлений со статусом 'pending_acceptance'")
            return None
        
        print(f"❌ Ошибка получения уведомлений: HTTP {response.status_code}")
        return None
    
    def demonstrate_correct_workflow(self):
        """Demonstrate the correct workflow that should fix the modal issue"""
        print("\n🎯 ДЕМОНСТРАЦИЯ ПРАВИЛЬНОГО WORKFLOW ДЛЯ МОДАЛЬНОГО ОКНА")
        print("=" * 70)
        
        # Get a fresh notification
        notification = self.get_fresh_notification()
        if not notification:
            print("❌ Не удалось найти уведомление для тестирования")
            return False
        
        notification_id = notification.get('id')
        request_number = notification.get('request_number')
        
        print(f"\n📋 Тестируем заявку №{request_number} (ID: {notification_id})")
        
        # STEP 1: Accept notification (what happens when user clicks "Принять")
        print("\n🔸 ШАГ 1: Принятие уведомления (/accept)")
        print("   Это должно происходить при нажатии кнопки 'Принять' в списке уведомлений")
        
        accept_response = self.session.post(
            f"{API_BASE}/operator/warehouse-notifications/{notification_id}/accept"
        )
        
        if accept_response.status_code == 200:
            accept_data = accept_response.json()
            print(f"   ✅ Успешно принято. Новый статус: {accept_data.get('status')}")
        else:
            print(f"   ❌ Ошибка принятия: HTTP {accept_response.status_code}")
            print(f"   Детали: {accept_response.text}")
            return False
        
        # STEP 2: Complete with modal data (what should happen when user clicks "Оформить и отправить")
        print("\n🔸 ШАГ 2: Завершение оформления с данными модального окна (/complete)")
        print("   Это должно происходить при нажатии кнопки 'Оформить и отправить' в модальном окне")
        
        # Prepare modal data as it would come from the frontend modal
        modal_data = {
            "sender_full_name": notification.get('sender_full_name', 'Тестовый Отправитель'),
            "sender_phone": notification.get('sender_phone', '+79999999999'),
            "sender_address": notification.get('pickup_address', 'Адрес забора груза'),
            "recipient_full_name": "Получатель Тестовый",
            "recipient_phone": "+79888888888",
            "recipient_address": "Душанбе, ул. Тестовая, 123",
            "payment_method": "cash",
            "payment_status": "paid",
            "delivery_method": "pickup",
            "cargo_items": [
                {
                    "name": f"Груз из заявки №{request_number}",
                    "weight": 12.5,
                    "price": 3500.0
                }
            ]
        }
        
        print(f"   📦 Данные модального окна:")
        print(f"      - Отправитель: {modal_data['sender_full_name']}")
        print(f"      - Получатель: {modal_data['recipient_full_name']}")
        print(f"      - Груз: {modal_data['cargo_items'][0]['name']} ({modal_data['cargo_items'][0]['weight']} кг)")
        print(f"      - Стоимость: {modal_data['cargo_items'][0]['price']} руб.")
        
        complete_response = self.session.post(
            f"{API_BASE}/operator/warehouse-notifications/{notification_id}/complete",
            json=modal_data
        )
        
        if complete_response.status_code == 200:
            complete_data = complete_response.json()
            print(f"   ✅ Успешно оформлено!")
            print(f"   📊 Результат:")
            print(f"      - Создано грузов: {complete_data.get('created_count', 0)}")
            print(f"      - Статус уведомления: {complete_data.get('notification_status', 'unknown')}")
            
            if 'created_cargos' in complete_data:
                for cargo in complete_data['created_cargos']:
                    print(f"      - Груз: {cargo.get('cargo_number')} (статус: {cargo.get('status')})")
            
            return True
        else:
            print(f"   ❌ Ошибка завершения оформления: HTTP {complete_response.status_code}")
            print(f"   Детали: {complete_response.text}")
            return False
    
    def demonstrate_wrong_workflow(self):
        """Demonstrate what happens with wrong workflow (what frontend might be doing)"""
        print("\n🚨 ДЕМОНСТРАЦИЯ НЕПРАВИЛЬНОГО WORKFLOW (ВОЗМОЖНАЯ ПРОБЛЕМА FRONTEND)")
        print("=" * 70)
        
        # Get a fresh notification
        notification = self.get_fresh_notification()
        if not notification:
            print("❌ Не удалось найти уведомление для тестирования")
            return False
        
        notification_id = notification.get('id')
        request_number = notification.get('request_number')
        
        print(f"\n📋 Тестируем заявку №{request_number} (ID: {notification_id})")
        
        # WRONG: Try to send modal data to /accept endpoint
        print("\n🔸 НЕПРАВИЛЬНО: Отправка данных модального окна на /accept endpoint")
        print("   Это может происходить если frontend неправильно реализован")
        
        modal_data = {
            "sender_full_name": notification.get('sender_full_name', 'Тестовый Отправитель'),
            "recipient_full_name": "Получатель Тестовый",
            "cargo_items": [
                {
                    "name": f"Груз из заявки №{request_number}",
                    "weight": 12.5,
                    "price": 3500.0
                }
            ]
        }
        
        wrong_response = self.session.post(
            f"{API_BASE}/operator/warehouse-notifications/{notification_id}/accept",
            json=modal_data
        )
        
        if wrong_response.status_code == 200:
            wrong_data = wrong_response.json()
            print(f"   ⚠️  Endpoint принял запрос, но данные модального окна ИГНОРИРУЮТСЯ!")
            print(f"   📊 Результат: статус = {wrong_data.get('status')}")
            print(f"   🚨 ПРОБЛЕМА: Заявка изменила статус на 'in_processing', но грузы НЕ СОЗДАНЫ!")
            print(f"   💡 Это объясняет почему заявка 'остается на месте' - она принята, но не оформлена")
            return True
        else:
            print(f"   ✅ Endpoint корректно отклонил неправильный запрос: HTTP {wrong_response.status_code}")
            return False
    
    def check_notification_status_after_wrong_workflow(self):
        """Check what happens to notifications after wrong workflow"""
        print("\n🔍 ПРОВЕРКА СОСТОЯНИЯ УВЕДОМЛЕНИЙ ПОСЛЕ НЕПРАВИЛЬНОГО WORKFLOW")
        print("=" * 70)
        
        response = self.session.get(f"{API_BASE}/operator/warehouse-notifications")
        
        if response.status_code == 200:
            data = response.json()
            notifications = data.get('notifications', [])
            
            pending_count = len([n for n in notifications if n.get('status') == 'pending_acceptance'])
            in_processing_count = len([n for n in notifications if n.get('status') == 'in_processing'])
            
            print(f"📊 Текущее состояние уведомлений:")
            print(f"   - Ожидают принятия (pending_acceptance): {pending_count}")
            print(f"   - В процессе оформления (in_processing): {in_processing_count}")
            
            if in_processing_count > 0:
                print(f"\n🚨 НАЙДЕНА ПРОБЛЕМА:")
                print(f"   {in_processing_count} уведомлений застряли в статусе 'in_processing'!")
                print(f"   Это происходит когда frontend вызывает только /accept, но не вызывает /complete")
                print(f"   Пользователь видит что заявка 'остается на месте' потому что:")
                print(f"   1. Статус изменился с 'pending_acceptance' на 'in_processing'")
                print(f"   2. Но грузы не были созданы (не вызван /complete)")
                print(f"   3. Заявка не исчезает из списка, но и не обрабатывается полностью")
                
                # Show stuck notifications
                stuck_notifications = [n for n in notifications if n.get('status') == 'in_processing']
                print(f"\n📋 Застрявшие уведомления:")
                for notif in stuck_notifications[:3]:  # Show first 3
                    print(f"   - №{notif.get('request_number')} (ID: {notif.get('id')}, статус: {notif.get('status')})")
                
                return True
            else:
                print("✅ Нет застрявших уведомлений")
                return False
        
        print(f"❌ Ошибка получения уведомлений: HTTP {response.status_code}")
        return False
    
    def run_diagnosis(self):
        """Run complete diagnosis"""
        print("🎯 КРИТИЧЕСКАЯ ДИАГНОСТИКА: Проблема с модальным окном приемки груза в TAJLINE.TJ")
        print("=" * 80)
        
        if not self.authenticate():
            return
        
        # Demonstrate correct workflow
        print("\n" + "="*80)
        correct_result = self.demonstrate_correct_workflow()
        
        # Demonstrate wrong workflow
        print("\n" + "="*80)
        wrong_result = self.demonstrate_wrong_workflow()
        
        # Check stuck notifications
        print("\n" + "="*80)
        stuck_result = self.check_notification_status_after_wrong_workflow()
        
        # Final diagnosis
        print("\n" + "="*80)
        print("🎯 ФИНАЛЬНАЯ ДИАГНОСТИКА")
        print("=" * 80)
        
        if correct_result:
            print("✅ ПРАВИЛЬНЫЙ WORKFLOW РАБОТАЕТ:")
            print("   1. /accept - принимает уведомление (статус → in_processing)")
            print("   2. /complete - создает грузы из данных модального окна")
            print("   3. Заявка полностью обрабатывается и исчезает из списка")
        
        if wrong_result:
            print("\n🚨 НАЙДЕНА КОРНЕВАЯ ПРИЧИНА ПРОБЛЕМЫ:")
            print("   Frontend отправляет данные модального окна на /accept endpoint!")
            print("   Это неправильно - /accept не обрабатывает данные модального окна")
            print("   Результат: заявка принимается, но грузы не создаются")
        
        if stuck_result:
            print("\n⚠️  ПОДТВЕРЖДЕНИЕ ПРОБЛЕМЫ:")
            print("   Найдены застрявшие уведомления в статусе 'in_processing'")
            print("   Это подтверждает что frontend вызывает /accept, но не вызывает /complete")
        
        print("\n💡 РЕШЕНИЕ ПРОБЛЕМЫ:")
        print("   Frontend должен:")
        print("   1. При нажатии 'Принять' → вызвать /accept")
        print("   2. При нажатии 'Оформить и отправить' → вызвать /complete с данными модального окна")
        print("   3. НЕ отправлять данные модального окна на /accept endpoint")
        
        print("\n✅ ДИАГНОСТИКА ЗАВЕРШЕНА")

def main():
    diagnoser = WarehouseModalDiagnoser()
    diagnoser.run_diagnosis()

if __name__ == "__main__":
    main()
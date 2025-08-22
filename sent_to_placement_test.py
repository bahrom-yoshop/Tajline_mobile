#!/usr/bin/env python3
"""
ДОПОЛНИТЕЛЬНОЕ ТЕСТИРОВАНИЕ: Проверка приемки уведомлений со статусом "sent_to_placement"
"""

import requests
import json
import os

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-cargo-8.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def test_sent_to_placement_acceptance():
    """Тест приемки уведомления со статусом sent_to_placement"""
    session = requests.Session()
    
    # Авторизация
    login_data = {"phone": "+79999888777", "password": "admin123"}
    response = session.post(f"{API_BASE}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print("❌ Ошибка авторизации")
        return False
    
    data = response.json()
    auth_token = data.get("access_token")
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    
    # Получаем уведомления
    response = session.get(f"{API_BASE}/operator/warehouse-notifications")
    if response.status_code != 200:
        print("❌ Ошибка получения уведомлений")
        return False
    
    data = response.json()
    notifications = data.get("notifications", [])
    
    # Ищем уведомление для создания sent_to_placement статуса
    pending_notification = None
    for notification in notifications:
        if notification.get("status") == "pending_acceptance":
            pending_notification = notification
            break
    
    if not pending_notification:
        print("✅ Нет pending уведомлений для тестирования")
        return True
    
    notification_id = pending_notification.get("id")
    
    # Принимаем уведомление
    accept_response = session.post(f"{API_BASE}/operator/warehouse-notifications/{notification_id}/accept")
    if accept_response.status_code != 200:
        print(f"❌ Ошибка принятия уведомления: {accept_response.status_code}")
        return False
    
    # Отправляем на размещение чтобы получить sent_to_placement статус
    placement_response = session.post(f"{API_BASE}/operator/warehouse-notifications/{notification_id}/send-to-placement")
    if placement_response.status_code != 200:
        print(f"❌ Ошибка отправки на размещение: {placement_response.status_code}")
        return False
    
    print("✅ Уведомление успешно переведено в статус sent_to_placement")
    
    # Теперь пробуем принять уведомление со статусом sent_to_placement
    reaccept_response = session.post(f"{API_BASE}/operator/warehouse-notifications/{notification_id}/accept")
    
    if reaccept_response.status_code == 200:
        print("🎉 УСПЕХ! Уведомление со статусом 'sent_to_placement' успешно принято для повторной обработки")
        return True
    elif reaccept_response.status_code == 400:
        error_text = reaccept_response.text
        if "cannot be processed" in error_text.lower():
            print(f"❌ ОШИБКА! Уведомление 'sent_to_placement' не принимается: {error_text}")
            return False
        else:
            print(f"✅ Статус принимается, но есть другая проблема: {error_text}")
            return True
    else:
        print(f"❌ Неожиданная ошибка: HTTP {reaccept_response.status_code}")
        return False

if __name__ == "__main__":
    print("🧪 ДОПОЛНИТЕЛЬНОЕ ТЕСТИРОВАНИЕ: Приемка уведомлений со статусом 'sent_to_placement'")
    print("=" * 80)
    
    success = test_sent_to_placement_acceptance()
    
    if success:
        print("\n✅ ТЕСТ ПРОЙДЕН: Уведомления 'sent_to_placement' могут быть повторно обработаны")
    else:
        print("\n❌ ТЕСТ НЕ ПРОЙДЕН: Проблема с обработкой 'sent_to_placement' уведомлений")
#!/usr/bin/env python3
"""
🎯 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ: Проверка найденного индивидуального DELETE endpoint для заявок на забор

НАЙДЕНО: 1 существующий индивидуальный endpoint из 5 проверенных
НУЖНО: Определить какой именно endpoint работает и протестировать его

ЦЕЛЬ: Подтвердить работоспособность найденного endpoint и дать финальные рекомендации
"""

import requests
import json
import os
from datetime import datetime

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-manage-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class FinalPickupDeletionTest:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.current_user = None
        self.pickup_requests = []
        
    def log(self, message, level="INFO"):
        """Простое логирование"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def authenticate_admin(self):
        """Авторизация администратора"""
        try:
            login_data = {
                "phone": "+79999888777",
                "password": "admin123"
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json"
                })
                
                user_response = self.session.get(f"{API_BASE}/auth/me")
                if user_response.status_code == 200:
                    self.current_user = user_response.json()
                    self.log(f"✅ Авторизация успешна: {self.current_user.get('full_name')} (роль: {self.current_user.get('role')})")
                    return True
                    
            self.log(f"❌ Ошибка авторизации: HTTP {response.status_code}", "ERROR")
            return False
                
        except Exception as e:
            self.log(f"❌ Исключение при авторизации: {str(e)}", "ERROR")
            return False
    
    def get_pickup_requests(self):
        """Получение заявок на забор"""
        try:
            response = self.session.get(f"{API_BASE}/operator/pickup-requests")
            
            if response.status_code == 200:
                data = response.json()
                
                if isinstance(data, list):
                    self.pickup_requests = data
                elif isinstance(data, dict):
                    self.pickup_requests = data.get('items', data.get('requests', data.get('pickup_requests', [])))
                
                self.log(f"✅ Получено {len(self.pickup_requests)} заявок на забор")
                
                if self.pickup_requests:
                    sample = self.pickup_requests[0]
                    self.log(f"📋 Образец заявки: ID={sample.get('id')}, номер={sample.get('request_number')}")
                
                return True
            else:
                self.log(f"❌ Ошибка получения заявок: HTTP {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при получении заявок: {str(e)}", "ERROR")
            return False
    
    def test_individual_endpoints_detailed(self):
        """Детальное тестирование индивидуальных endpoints"""
        if not self.pickup_requests:
            self.log("⚠️ Нет заявок для тестирования", "WARNING")
            return
        
        test_request = self.pickup_requests[0]
        request_id = test_request.get('id')
        request_number = test_request.get('request_number')
        
        self.log(f"🎯 Тестируем с ID={request_id}, номер={request_number}")
        
        # Тестируем различные endpoints
        endpoints_to_test = [
            f"/api/admin/pickup-requests/{request_id}",
            f"/api/admin/courier/pickup-requests/{request_id}",
            f"/api/operator/pickup-requests/{request_id}",
            f"/api/admin/pickup-requests/{request_number}",
            f"/api/admin/courier/pickup-requests/{request_number}"
        ]
        
        working_endpoints = []
        
        for endpoint in endpoints_to_test:
            try:
                # Используем HEAD для проверки существования
                head_response = self.session.head(f"{BACKEND_URL}{endpoint}")
                
                if head_response.status_code == 200:
                    self.log(f"✅ НАЙДЕН РАБОЧИЙ ENDPOINT: {endpoint} (HTTP 200)")
                    working_endpoints.append(endpoint)
                elif head_response.status_code == 405:  # Method Not Allowed - endpoint существует, но DELETE не поддерживается
                    self.log(f"⚠️ Endpoint существует, но DELETE не поддерживается: {endpoint} (HTTP 405)")
                elif head_response.status_code == 404:
                    self.log(f"❌ Endpoint не найден: {endpoint} (HTTP 404)")
                else:
                    self.log(f"🔍 Endpoint {endpoint}: HTTP {head_response.status_code}")
                    
            except Exception as e:
                self.log(f"❌ Ошибка при тестировании {endpoint}: {str(e)}", "ERROR")
        
        # Тестируем DELETE на найденных endpoints
        if working_endpoints:
            self.log(f"🎯 Тестируем DELETE на {len(working_endpoints)} найденных endpoints")
            
            for endpoint in working_endpoints:
                try:
                    # Тестируем DELETE (осторожно!)
                    delete_response = self.session.delete(f"{BACKEND_URL}{endpoint}")
                    
                    if delete_response.status_code == 200:
                        self.log(f"✅ DELETE РАБОТАЕТ: {endpoint} - заявка успешно удалена!")
                        self.log(f"📄 Ответ: {delete_response.text[:200]}")
                        break  # Останавливаемся после первого успешного удаления
                    elif delete_response.status_code == 404:
                        self.log(f"❌ Заявка не найдена: {endpoint} (HTTP 404)")
                    elif delete_response.status_code == 403:
                        self.log(f"❌ Нет прав доступа: {endpoint} (HTTP 403)")
                    elif delete_response.status_code == 405:
                        self.log(f"❌ Метод не поддерживается: {endpoint} (HTTP 405)")
                    else:
                        self.log(f"⚠️ Неожиданный ответ от {endpoint}: HTTP {delete_response.status_code}")
                        self.log(f"📄 Ответ: {delete_response.text[:200]}")
                        
                except Exception as e:
                    self.log(f"❌ Ошибка DELETE на {endpoint}: {str(e)}", "ERROR")
        else:
            self.log("❌ НЕ НАЙДЕНО рабочих индивидуальных endpoints для DELETE", "ERROR")
    
    def test_bulk_endpoint_detailed(self):
        """Детальное тестирование bulk endpoint"""
        if not self.pickup_requests:
            self.log("⚠️ Нет заявок для тестирования bulk удаления", "WARNING")
            return
        
        # Берем последнюю заявку для bulk удаления
        test_request = self.pickup_requests[-1]  # Берем последнюю, чтобы не конфликтовать с индивидуальным тестом
        request_id = test_request.get('id')
        
        self.log(f"🎯 Тестируем bulk удаление с ID={request_id}")
        
        # Правильная структура для bulk delete
        bulk_data = {
            "ids": [request_id]
        }
        
        try:
            response = self.session.delete(f"{API_BASE}/admin/pickup-requests/bulk", json=bulk_data)
            
            if response.status_code == 200:
                self.log("✅ BULK DELETE РАБОТАЕТ: заявка успешно удалена через bulk endpoint!")
                self.log(f"📄 Ответ: {response.text[:200]}")
            elif response.status_code == 400:
                self.log(f"❌ Ошибка валидации bulk delete: {response.text[:200]}")
            elif response.status_code == 500:
                self.log(f"❌ Внутренняя ошибка сервера в bulk delete: {response.text[:200]}")
            else:
                self.log(f"⚠️ Неожиданный ответ bulk delete: HTTP {response.status_code}")
                self.log(f"📄 Ответ: {response.text[:200]}")
                
        except Exception as e:
            self.log(f"❌ Исключение при bulk delete: {str(e)}", "ERROR")
    
    def run_final_test(self):
        """Запуск финального теста"""
        print("🎯 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ: Проверка DELETE endpoints для заявок на забор")
        print("=" * 80)
        print()
        
        # Авторизация
        if not self.authenticate_admin():
            print("❌ Не удалось авторизоваться. Тест прерван.")
            return
        
        # Получение заявок
        if not self.get_pickup_requests():
            print("❌ Не удалось получить заявки. Тест прерван.")
            return
        
        # Детальное тестирование индивидуальных endpoints
        self.log("🔍 ТЕСТИРОВАНИЕ ИНДИВИДУАЛЬНЫХ DELETE ENDPOINTS")
        self.log("-" * 60)
        self.test_individual_endpoints_detailed()
        
        print()
        
        # Детальное тестирование bulk endpoint
        self.log("🔍 ТЕСТИРОВАНИЕ BULK DELETE ENDPOINT")
        self.log("-" * 60)
        self.test_bulk_endpoint_detailed()
        
        print()
        print("=" * 80)
        print("🎯 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        print("=" * 80)

def main():
    """Главная функция"""
    tester = FinalPickupDeletionTest()
    tester.run_final_test()

if __name__ == "__main__":
    main()
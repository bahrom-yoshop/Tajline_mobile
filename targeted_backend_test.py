#!/usr/bin/env python3
"""
🎯 ЦЕЛЕВОЕ ТЕСТИРОВАНИЕ BACKEND API: Проверка конкретных endpoints после системы нумерации разработчика
"""

import requests
import json
import time
from datetime import datetime
import os

# Конфигурация для тестирования
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://placement-manager.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Тестовые данные оператора склада
OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class TargetedBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_user = None
        self.warehouse_id = None
        
    def authenticate(self):
        """Авторизация оператора склада"""
        print("🔐 Авторизация оператора склада...")
        
        try:
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=OPERATOR_CREDENTIALS,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                # Получаем информацию о пользователе
                user_response = self.session.get(f"{API_BASE}/auth/me", timeout=30)
                if user_response.status_code == 200:
                    self.operator_user = user_response.json()
                    print(f"✅ Авторизация успешна: {self.operator_user.get('full_name')} (роль: {self.operator_user.get('role')})")
                    return True
                else:
                    print(f"❌ Ошибка получения данных пользователя: {user_response.status_code}")
                    return False
            else:
                print(f"❌ Ошибка авторизации: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение при авторизации: {str(e)}")
            return False
    
    def get_warehouse(self):
        """Получение склада оператора"""
        try:
            response = self.session.get(f"{API_BASE}/operator/warehouses", timeout=30)
            
            if response.status_code == 200:
                warehouses = response.json()
                if warehouses:
                    warehouse = warehouses[0]
                    self.warehouse_id = warehouse.get("id")
                    print(f"✅ Склад получен: {warehouse.get('name')} (ID: {self.warehouse_id})")
                    return True
                else:
                    print("❌ У оператора нет привязанных складов")
                    return False
            else:
                print(f"❌ Ошибка получения складов: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение при получении склада: {str(e)}")
            return False
    
    def test_specific_endpoints(self):
        """Тестирование конкретных endpoints"""
        print("\n🎯 ТЕСТИРОВАНИЕ КОНКРЕТНЫХ ENDPOINTS:")
        print("=" * 60)
        
        endpoints_to_test = [
            ("GET", "/api/operator/placement-progress", None),
            ("GET", "/api/operator/cargo/available-for-placement", None),
            ("GET", "/api/operator/cargo/individual-units-for-placement", None),
            ("POST", "/api/operator/qr/generate-individual", {"individual_number": "250101/01/01"}),
            ("GET", "/api/operator/qr/print-layout", None),
            ("POST", "/api/operator/placement/verify-cell", {"qr_code": "001-01-01-001"}),
        ]
        
        for method, endpoint, payload in endpoints_to_test:
            print(f"\n📋 Тестирование: {method} {endpoint}")
            
            try:
                if method == "GET":
                    response = self.session.get(f"{API_BASE.replace('/api', '')}{endpoint}", timeout=30)
                elif method == "POST":
                    response = self.session.post(
                        f"{API_BASE.replace('/api', '')}{endpoint}",
                        json=payload,
                        timeout=30
                    )
                
                print(f"   📊 Статус: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"   ✅ Успешный ответ (размер: {len(str(data))} символов)")
                        
                        # Показываем ключи ответа для диагностики
                        if isinstance(data, dict):
                            keys = list(data.keys())[:5]  # Первые 5 ключей
                            print(f"   📝 Ключи ответа: {keys}")
                        elif isinstance(data, list):
                            print(f"   📝 Массив из {len(data)} элементов")
                            
                    except json.JSONDecodeError:
                        print(f"   ⚠️ Ответ не является JSON")
                elif response.status_code == 404:
                    print(f"   ❌ Endpoint не найден")
                elif response.status_code == 400:
                    print(f"   ❌ Неверный запрос")
                    try:
                        error_data = response.json()
                        print(f"   📝 Ошибка: {error_data}")
                    except:
                        print(f"   📝 Текст ошибки: {response.text[:200]}")
                else:
                    print(f"   ❌ Неожиданный статус: {response.status_code}")
                    print(f"   📝 Ответ: {response.text[:200]}")
                    
            except Exception as e:
                print(f"   ❌ Исключение: {str(e)}")
    
    def run_test(self):
        """Запуск целевого тестирования"""
        print("🎯 ЦЕЛЕВОЕ ТЕСТИРОВАНИЕ BACKEND API")
        print("=" * 60)
        
        if not self.authenticate():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться")
            return False
        
        if not self.get_warehouse():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить склад оператора")
            return False
        
        self.test_specific_endpoints()
        
        print("\n🎯 ЦЕЛЕВОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        return True

def main():
    """Главная функция"""
    tester = TargetedBackendTester()
    tester.run_test()
    return 0

if __name__ == "__main__":
    exit(main())
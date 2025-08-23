#!/usr/bin/env python3
"""
ДИАГНОСТИКА ДАННЫХ ДЛЯ API placement-status
==========================================

Цель: Проанализировать доступные данные в базе для улучшения API placement-status
"""

import requests
import json
import sys
import os
from datetime import datetime

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cargo-sync.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Конфигурация
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"

class PlacementStatusDiagnoser:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        
    def log(self, message, level="INFO"):
        """Логирование с временной меткой"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def authenticate_warehouse_operator(self):
        """Авторизация оператора склада"""
        self.log("🔐 Авторизация оператора склада...")
        
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json={
                "phone": WAREHOUSE_OPERATOR_PHONE,
                "password": WAREHOUSE_OPERATOR_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.operator_info = data.get("user")
                
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log(f"✅ Успешная авторизация: {self.operator_info.get('full_name')} (роль: {self.operator_info.get('role')})")
                return True
            else:
                self.log(f"❌ Ошибка авторизации: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при авторизации: {e}", "ERROR")
            return False
    
    def get_warehouses_data(self):
        """Получить данные о складах"""
        self.log("🏢 Получение данных о складах...")
        
        try:
            response = self.session.get(f"{API_BASE}/operator/warehouses")
            
            if response.status_code == 200:
                warehouses = response.json()
                self.log(f"✅ Получено {len(warehouses)} складов")
                
                for warehouse in warehouses:
                    self.log(f"  📦 Склад: {warehouse.get('name')} (ID: {warehouse.get('id')})")
                    self.log(f"      - Местоположение: {warehouse.get('location')}")
                    self.log(f"      - Адрес: {warehouse.get('address')}")
                    
                return warehouses
            else:
                self.log(f"❌ Ошибка получения складов: {response.status_code} - {response.text}", "ERROR")
                return []
                
        except Exception as e:
            self.log(f"❌ Исключение при получении складов: {e}", "ERROR")
            return []
    
    def get_all_cities(self):
        """Получить все города"""
        self.log("🌍 Получение списка городов...")
        
        try:
            response = self.session.get(f"{API_BASE}/warehouses/all-cities")
            
            if response.status_code == 200:
                cities = response.json()
                self.log(f"✅ Получено {len(cities)} городов: {cities}")
                return cities
            else:
                self.log(f"❌ Ошибка получения городов: {response.status_code} - {response.text}", "ERROR")
                return []
                
        except Exception as e:
            self.log(f"❌ Исключение при получении городов: {e}", "ERROR")
            return []
    
    def analyze_cargo_data(self, cargo_id):
        """Анализ данных конкретной заявки"""
        self.log(f"🔍 Анализ данных заявки {cargo_id}...")
        
        try:
            response = self.session.get(f"{API_BASE}/operator/cargo/{cargo_id}/placement-status")
            
            if response.status_code == 200:
                data = response.json()
                
                self.log("📋 АНАЛИЗ ПОЛЕЙ ЗАЯВКИ:")
                self.log("=" * 50)
                
                # Анализируем каждое поле
                fields_to_analyze = [
                    'sender_full_name', 'sender_phone', 'sender_address',
                    'recipient_full_name', 'recipient_phone', 'recipient_address',
                    'pickup_city', 'delivery_city',
                    'source_warehouse_name', 'target_warehouse_name',
                    'accepting_warehouse', 'delivery_warehouse',
                    'operator_full_name', 'operator_phone'
                ]
                
                for field in fields_to_analyze:
                    value = data.get(field, 'ОТСУТСТВУЕТ')
                    status = "✅" if value not in ['Не указан', 'ОТСУТСТВУЕТ', None, ''] else "❌"
                    self.log(f"  {status} {field}: {value}")
                
                return data
            else:
                self.log(f"❌ Ошибка получения данных заявки: {response.status_code} - {response.text}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Исключение при анализе заявки: {e}", "ERROR")
            return None
    
    def suggest_improvements(self, cargo_data, warehouses, cities):
        """Предложить улучшения для API"""
        self.log("\n🔧 ПРЕДЛОЖЕНИЯ ПО УЛУЧШЕНИЮ API placement-status:")
        self.log("=" * 60)
        
        # Анализ городов
        if cargo_data.get('pickup_city') == 'Не указан':
            self.log("1. 🌍 ГОРОДА:")
            self.log("   - pickup_city не заполнен")
            self.log("   - Можно использовать sender_address для определения города")
            self.log("   - Доступные города в системе:", cities[:5] if cities else "Нет данных")
        
        # Анализ складов
        if cargo_data.get('source_warehouse_name') == 'Не указан':
            self.log("2. 🏢 СКЛАДЫ:")
            self.log("   - source_warehouse_name не заполнен")
            self.log("   - Можно использовать warehouse_id оператора")
            if warehouses:
                self.log(f"   - Доступные склады: {[w.get('name') for w in warehouses]}")
        
        # Анализ операторов
        if cargo_data.get('operator_full_name') == 'Неизвестный оператор':
            self.log("3. 👤 ОПЕРАТОРЫ:")
            self.log("   - operator_full_name не заполнен корректно")
            self.log("   - Можно использовать данные текущего авторизованного оператора")
            self.log(f"   - Текущий оператор: {self.operator_info.get('full_name')} ({self.operator_info.get('phone')})")
        
        # Предложения по улучшению
        self.log("\n💡 КОНКРЕТНЫЕ ПРЕДЛОЖЕНИЯ:")
        self.log("1. Использовать warehouse_id текущего оператора для source_warehouse_name")
        self.log("2. Парсить города из sender_address и recipient_address")
        self.log("3. Использовать данные авторизованного оператора для operator_full_name и operator_phone")
        self.log("4. Добавить fallback значения на основе маршрута (route)")
        self.log("5. Использовать lookup в коллекциях users и warehouses более эффективно")
    
    def run_diagnosis(self):
        """Запуск полной диагностики"""
        self.log("🚀 ЗАПУСК ДИАГНОСТИКИ ДАННЫХ ДЛЯ placement-status API")
        self.log("=" * 70)
        
        # 1. Авторизация
        if not self.authenticate_warehouse_operator():
            return False
        
        # 2. Получение данных о складах
        warehouses = self.get_warehouses_data()
        
        # 3. Получение городов
        cities = self.get_all_cities()
        
        # 4. Получение доступных заявок
        try:
            response = self.session.get(f"{API_BASE}/operator/cargo/available-for-placement")
            if response.status_code == 200:
                applications = response.json()
                items = applications if isinstance(applications, list) else applications.get("items", [])
                
                if items:
                    first_app = items[0]
                    cargo_id = first_app.get("id")
                    
                    # 5. Анализ данных заявки
                    cargo_data = self.analyze_cargo_data(cargo_id)
                    
                    if cargo_data:
                        # 6. Предложения по улучшению
                        self.suggest_improvements(cargo_data, warehouses, cities)
                        
                        return True
                else:
                    self.log("❌ Нет доступных заявок для анализа")
                    return False
            else:
                self.log(f"❌ Ошибка получения заявок: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Ошибка при получении заявок: {e}")
            return False

def main():
    """Главная функция"""
    diagnoser = PlacementStatusDiagnoser()
    
    try:
        success = diagnoser.run_diagnosis()
        
        if success:
            print("\n" + "="*70)
            print("✅ ДИАГНОСТИКА ЗАВЕРШЕНА УСПЕШНО!")
            print("📊 Проанализированы доступные данные и предложены улучшения")
        else:
            print("\n" + "="*70)
            print("❌ ДИАГНОСТИКА НЕ ЗАВЕРШЕНА!")
            print("🔍 Не удалось получить достаточно данных для анализа")
            
    except KeyboardInterrupt:
        print("\n⏹️ Диагностика прервана пользователем")
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")

if __name__ == "__main__":
    main()
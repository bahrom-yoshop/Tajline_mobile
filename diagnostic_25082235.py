#!/usr/bin/env python3
"""
🔍 ДИАГНОСТИКА: Проверка данных заявки 25082235 в базе данных

Этот скрипт проверяет:
1. Существование заявки 25082235 в коллекциях cargo и operator_cargo
2. Структуру individual_items и их поля placed_by/placed_by_operator
3. Записи в placement_records для этой заявки
4. Логику определения placing_operator в endpoint
"""

import requests
import json
import time
from datetime import datetime
import os
from pymongo import MongoClient

# Конфигурация для тестирования
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://placement-view.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# MongoDB подключение
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'cargo_transport')
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Тестовые данные оператора склада
OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class Diagnostic25082235:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        
    def authenticate_operator(self):
        """Авторизация оператора склада"""
        print("🔐 Авторизация для API тестов...")
        
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
                print("✅ Авторизация успешна")
                return True
            else:
                print(f"❌ Ошибка авторизации: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение при авторизации: {str(e)}")
            return False

    def check_database_data(self):
        """Проверка данных в базе данных"""
        print("\n🔍 ДИАГНОСТИКА БАЗЫ ДАННЫХ:")
        print("=" * 60)
        
        # Проверяем коллекцию operator_cargo
        print("📋 Поиск в коллекции operator_cargo...")
        operator_cargo = db.operator_cargo.find_one({"cargo_number": "25082235"})
        
        if operator_cargo:
            print("✅ Заявка найдена в operator_cargo")
            print(f"   📦 ID: {operator_cargo.get('id')}")
            print(f"   📋 Номер: {operator_cargo.get('cargo_number')}")
            print(f"   📊 Статус: {operator_cargo.get('status')}")
            
            cargo_items = operator_cargo.get('cargo_items', [])
            print(f"   📦 Количество cargo_items: {len(cargo_items)}")
            
            for i, item in enumerate(cargo_items):
                print(f"   📦 Cargo Item {i+1}:")
                print(f"      🏷️ Название: {item.get('cargo_name', 'N/A')}")
                print(f"      🔢 Количество: {item.get('quantity', 'N/A')}")
                
                individual_items = item.get('individual_items', [])
                print(f"      📋 Individual items: {len(individual_items)}")
                
                for j, individual in enumerate(individual_items):
                    print(f"         📦 Unit {j+1}:")
                    print(f"            🔢 Номер: {individual.get('individual_number', 'N/A')}")
                    print(f"            ✅ Размещен: {individual.get('is_placed', False)}")
                    print(f"            📍 Место: {individual.get('placement_info', 'N/A')}")
                    print(f"            👤 placed_by: {individual.get('placed_by', 'НЕТ ПОЛЯ')}")
                    print(f"            👤 placed_by_operator: {individual.get('placed_by_operator', 'НЕТ ПОЛЯ')}")
                    print(f"            📅 placed_at: {individual.get('placed_at', 'N/A')}")
                    print(f"            🏢 warehouse_name: {individual.get('warehouse_name', 'N/A')}")
        else:
            print("❌ Заявка НЕ найдена в operator_cargo")
        
        # Проверяем коллекцию cargo
        print("\n📋 Поиск в коллекции cargo...")
        cargo = db.cargo.find_one({"cargo_number": "25082235"})
        
        if cargo:
            print("✅ Заявка найдена в cargo")
            print(f"   📦 ID: {cargo.get('id')}")
            print(f"   📋 Номер: {cargo.get('cargo_number')}")
            print(f"   📊 Статус: {cargo.get('status')}")
        else:
            print("❌ Заявка НЕ найдена в cargo")
        
        # Проверяем placement_records
        print("\n📋 Поиск в коллекции placement_records...")
        placement_records = list(db.placement_records.find({"cargo_number": "25082235"}))
        
        if placement_records:
            print(f"✅ Найдено {len(placement_records)} записей размещения")
            for i, record in enumerate(placement_records):
                print(f"   📦 Запись {i+1}:")
                print(f"      🔢 Individual number: {record.get('individual_number', 'N/A')}")
                print(f"      📍 Место: {record.get('location_code', 'N/A')}")
                print(f"      👤 placed_by_operator: {record.get('placed_by_operator', 'N/A')}")
                print(f"      📅 placed_at: {record.get('placed_at', 'N/A')}")
                print(f"      🏢 warehouse_name: {record.get('warehouse_name', 'N/A')}")
        else:
            print("❌ Записи размещения НЕ найдены в placement_records")
        
        return operator_cargo, cargo, placement_records

    def test_api_response(self):
        """Тестирование API ответа"""
        print("\n🔍 ДИАГНОСТИКА API ОТВЕТА:")
        print("=" * 60)
        
        try:
            response = self.session.get(f"{API_BASE}/operator/cargo/fully-placed", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                # Ищем заявку 25082235
                target_cargo = None
                for item in items:
                    if item.get("cargo_number") == "25082235":
                        target_cargo = item
                        break
                
                if target_cargo:
                    print("✅ Заявка найдена в API ответе")
                    print(f"   📋 Номер: {target_cargo.get('cargo_number')}")
                    print(f"   👤 placing_operator: '{target_cargo.get('placing_operator')}'")
                    print(f"   📊 Статус: {target_cargo.get('status')}")
                    print(f"   📦 Всего единиц: {target_cargo.get('total_units')}")
                    print(f"   ✅ Размещено единиц: {target_cargo.get('placed_units')}")
                    
                    individual_units = target_cargo.get("individual_units", [])
                    print(f"   📋 Individual units в API: {len(individual_units)}")
                    
                    for i, unit in enumerate(individual_units):
                        print(f"      📦 Unit {i+1}:")
                        print(f"         🔢 Номер: {unit.get('individual_number', 'N/A')}")
                        print(f"         ✅ Размещен: {unit.get('is_placed', False)}")
                        print(f"         👤 placed_by: '{unit.get('placed_by', 'НЕТ ПОЛЯ')}'")
                        print(f"         📍 Место: {unit.get('placement_info', 'N/A')}")
                    
                    return target_cargo
                else:
                    print("❌ Заявка НЕ найдена в API ответе")
                    return None
            else:
                print(f"❌ Ошибка API: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Исключение при тестировании API: {str(e)}")
            return None

    def suggest_fix(self, operator_cargo, placement_records):
        """Предложение исправления"""
        print("\n🔧 ПРЕДЛОЖЕНИЯ ПО ИСПРАВЛЕНИЮ:")
        print("=" * 60)
        
        if placement_records:
            # Есть записи в placement_records с операторами
            operators = [record.get('placed_by_operator') for record in placement_records if record.get('placed_by_operator')]
            if operators:
                print(f"✅ В placement_records найдены операторы: {set(operators)}")
                print("💡 РЕШЕНИЕ 1: Обновить individual_items в основном документе из placement_records")
                
                # Предлагаем скрипт обновления
                print("\n📝 Скрипт обновления MongoDB:")
                for record in placement_records:
                    individual_number = record.get('individual_number')
                    operator = record.get('placed_by_operator')
                    if individual_number and operator:
                        print(f"""
db.operator_cargo.updateOne(
    {{"cargo_number": "25082235", "cargo_items.individual_items.individual_number": "{individual_number}"}},
    {{"$set": {{
        "cargo_items.$[cargo_item].individual_items.$[individual_item].placed_by_operator": "{operator}",
        "cargo_items.$[cargo_item].individual_items.$[individual_item].placed_at": new Date("{record.get('placed_at', '')}"),
        "cargo_items.$[cargo_item].individual_items.$[individual_item].warehouse_name": "{record.get('warehouse_name', '')}"
    }}}},
    {{arrayFilters: [
        {{"cargo_item.individual_items.individual_number": "{individual_number}"}},
        {{"individual_item.individual_number": "{individual_number}"}}
    ]}}
)""")
        
        if operator_cargo:
            print("\n💡 РЕШЕНИЕ 2: Проверить логику в endpoint fully-placed")
            print("   - Убедиться что поиск идет по правильному полю (placed_by_operator)")
            print("   - Проверить что данные синхронизированы между коллекциями")

    def run_full_diagnostic(self):
        """Запуск полной диагностики"""
        print("🔍 ПОЛНАЯ ДИАГНОСТИКА ЗАЯВКИ 25082235")
        print("=" * 80)
        
        # Авторизация для API тестов
        if not self.authenticate_operator():
            print("❌ Не удалось авторизоваться для API тестов")
            return False
        
        # Проверка данных в БД
        operator_cargo, cargo, placement_records = self.check_database_data()
        
        # Проверка API ответа
        api_cargo = self.test_api_response()
        
        # Предложения по исправлению
        self.suggest_fix(operator_cargo, placement_records)
        
        print("\n🎯 ДИАГНОСТИКА ЗАВЕРШЕНА!")
        return True

def main():
    """Главная функция"""
    diagnostic = Diagnostic25082235()
    diagnostic.run_full_diagnostic()
    return 0

if __name__ == "__main__":
    exit(main())
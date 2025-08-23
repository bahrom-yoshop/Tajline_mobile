#!/usr/bin/env python3
"""
БЫСТРАЯ ПРОВЕРКА API available-for-placement для заявки 250101
=============================================================

ЦЕЛЬ: Убедиться что backend API возвращает правильные данные для заявки 250101

ПРОВЕРКИ:
1. Авторизация оператора склада (+79777888999/warehouse123)
2. Запрос к `/api/operator/cargo/available-for-placement`
3. Найти заявку 250101 в ответе
4. Проверить поля:
   - `total_placed` (должно быть 2)
   - `placement_progress` (должно быть '2/4')
   - `overall_placement_status`

ВАЖНО: Пользователь видит в интерфейсе 1/4 вместо ожидаемых 2/4. 
Нужно подтвердить что backend возвращает правильные данные.
"""

import requests
import json
import sys
import os
from datetime import datetime

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-manage-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def test_warehouse_operator_auth():
    """Тест авторизации оператора склада"""
    print("🔐 Тестирование авторизации оператора склада...")
    
    login_data = {
        "phone": "+79777888999",
        "password": "warehouse123"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            user_info = data.get("user", {})
            
            print(f"✅ Авторизация успешна: {user_info.get('full_name')} (роль: {user_info.get('role')})")
            return token
        else:
            print(f"❌ Ошибка авторизации: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Исключение при авторизации: {e}")
        return None

def test_available_for_placement_api(token):
    """Тест API available-for-placement для поиска заявки 250101"""
    print("\n📦 Тестирование API available-for-placement...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_BASE}/operator/cargo/available-for-placement", 
                              headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            
            print(f"✅ API доступен, получено {len(items)} заявок")
            
            # Ищем заявку 250101
            target_cargo = None
            for item in items:
                cargo_number = item.get("cargo_number", "")
                if cargo_number == "250101":
                    target_cargo = item
                    break
            
            if target_cargo:
                print(f"\n🎯 ЗАЯВКА 250101 НАЙДЕНА!")
                
                # Проверяем ключевые поля
                total_placed = target_cargo.get("total_placed")
                placement_progress = target_cargo.get("placement_progress")
                overall_placement_status = target_cargo.get("overall_placement_status")
                
                print(f"📊 ДАННЫЕ ЗАЯВКИ 250101:")
                print(f"   • total_placed: {total_placed}")
                print(f"   • placement_progress: '{placement_progress}'")
                print(f"   • overall_placement_status: '{overall_placement_status}'")
                
                # Детальный анализ cargo_items если есть
                cargo_items = target_cargo.get("cargo_items", [])
                if cargo_items:
                    print(f"\n📋 ДЕТАЛЬНЫЙ АНАЛИЗ CARGO ITEMS ({len(cargo_items)} шт.):")
                    for i, item in enumerate(cargo_items, 1):
                        cargo_name = item.get("cargo_name", "Неизвестно")
                        placed_count = item.get("placed_count", 0)
                        total_count = item.get("total_count", 0)
                        individual_items = item.get("individual_items", [])
                        
                        print(f"   Cargo Item {i}: '{cargo_name}' - {placed_count}/{total_count} размещено")
                        
                        # Анализ individual_items
                        if individual_items:
                            for j, ind_item in enumerate(individual_items, 1):
                                individual_number = ind_item.get("individual_number", "")
                                is_placed = ind_item.get("is_placed", False)
                                status = "✅ размещен" if is_placed else "⏳ ожидает"
                                print(f"     - {individual_number}: {status}")
                
                # Проверяем соответствие ожиданиям
                print(f"\n🔍 ПРОВЕРКА СООТВЕТСТВИЯ ОЖИДАНИЯМ:")
                if total_placed == 2:
                    print(f"✅ total_placed = 2 (соответствует ожиданию)")
                else:
                    print(f"❌ total_placed = {total_placed} (ожидалось: 2)")
                
                if placement_progress == "2/4":
                    print(f"✅ placement_progress = '2/4' (соответствует ожиданию)")
                else:
                    print(f"❌ placement_progress = '{placement_progress}' (ожидалось: '2/4')")
                
                return True
            else:
                print(f"❌ ЗАЯВКА 250101 НЕ НАЙДЕНА в списке доступных для размещения")
                
                # Показываем доступные заявки для отладки
                print(f"\n📋 ДОСТУПНЫЕ ЗАЯВКИ ({len(items)} шт.):")
                for item in items[:10]:  # Показываем первые 10
                    cargo_number = item.get("cargo_number", "")
                    total_placed = item.get("total_placed", 0)
                    placement_progress = item.get("placement_progress", "")
                    print(f"   • {cargo_number}: {placement_progress}")
                
                return False
                
        else:
            print(f"❌ Ошибка API: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Исключение при запросе API: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 БЫСТРАЯ ПРОВЕРКА API available-for-placement для заявки 250101")
    print("=" * 70)
    
    # Шаг 1: Авторизация
    token = test_warehouse_operator_auth()
    if not token:
        print("\n❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Не удалось авторизоваться")
        sys.exit(1)
    
    # Шаг 2: Проверка API
    success = test_available_for_placement_api(token)
    
    # Итоговый результат
    print("\n" + "=" * 70)
    if success:
        print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print("✅ Backend API возвращает данные для заявки 250101")
        print("📊 Проверьте выше соответствие данных ожиданиям")
    else:
        print("❌ ТЕСТИРОВАНИЕ НЕ ПРОЙДЕНО!")
        print("🔍 Заявка 250101 не найдена или API недоступен")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
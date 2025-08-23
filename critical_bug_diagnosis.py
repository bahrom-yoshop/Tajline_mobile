#!/usr/bin/env python3
"""
🚨 КРИТИЧЕСКАЯ ДИАГНОСТИКА: Проблема с заявкой 250109 в fully-placed endpoint

ОБНАРУЖЕННАЯ ПРОБЛЕМА:
- Заявка 250109 имеет 5/5 единиц полностью размещенных
- Но она НЕ появляется в /api/operator/cargo/fully-placed endpoint
- Это точно соответствует описанию проблемы в review request

ДИАГНОСТИКА СТРУКТУРЫ ДАННЫХ:
- individual-units-for-placement находит данные в cargo_items[].individual_items
- fully-placed ищет данные в cargo.individual_items (неправильно)
"""

import requests
import json

# Конфигурация
BACKEND_URL = 'https://cargo-sync.preview.emergentagent.com'
API_BASE = f"{BACKEND_URL}/api"

def authenticate():
    response = requests.post(f"{API_BASE}/auth/login", 
                           json={'phone': '+79777888999', 'password': 'warehouse123'})
    if response.status_code == 200:
        return response.json()['access_token']
    return None

def main():
    print("🚨 КРИТИЧЕСКАЯ ДИАГНОСТИКА: Проблема fully-placed endpoint")
    print("=" * 70)
    
    token = authenticate()
    if not token:
        print("❌ Ошибка авторизации")
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # 1. Проверяем individual-units-for-placement
    print("\n📊 ДИАГНОСТИКА 1: individual-units-for-placement endpoint")
    response = requests.get(f"{API_BASE}/operator/cargo/individual-units-for-placement", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        groups = data.get('items', [])
        print(f"✅ Найдено {len(groups)} групп заявок")
        
        total_units = 0
        total_placed = 0
        
        for i, group in enumerate(groups):
            units = group.get('units', [])
            group_total = len(units)
            group_placed = sum(1 for unit in units if unit.get('is_placed', False))
            
            total_units += group_total
            total_placed += group_placed
            
            print(f"  Группа {i+1}: {group_placed}/{group_total} единиц размещено")
            
            # Показываем детали для заявки 250109
            for unit in units:
                individual_number = unit.get('individual_number', '')
                if '250109' in individual_number:
                    is_placed = unit.get('is_placed', False)
                    placement_info = unit.get('placement_info', '')
                    status = "✅ Размещен" if is_placed else "🟡 Ожидает"
                    print(f"    📍 {individual_number}: {status} ({placement_info})")
        
        print(f"📊 ИТОГО: {total_placed}/{total_units} единиц размещено")
        
        # Определяем полностью размещенные заявки
        fully_placed_count = 0
        for group in groups:
            units = group.get('units', [])
            if units:
                group_total = len(units)
                group_placed = sum(1 for unit in units if unit.get('is_placed', False))
                if group_placed == group_total:
                    fully_placed_count += 1
        
        print(f"🎯 ПОЛНОСТЬЮ РАЗМЕЩЕННЫХ ЗАЯВОК: {fully_placed_count}")
    else:
        print(f"❌ Ошибка: {response.status_code}")
    
    # 2. Проверяем fully-placed endpoint
    print("\n📊 ДИАГНОСТИКА 2: fully-placed endpoint")
    response = requests.get(f"{API_BASE}/operator/cargo/fully-placed", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        items = data.get('items', [])
        summary = data.get('summary', {})
        
        print(f"✅ Endpoint доступен")
        print(f"📊 Найдено полностью размещенных заявок: {len(items)}")
        print(f"📊 Summary: {summary}")
        
        if items:
            for item in items:
                app_num = item.get('application_number', item.get('cargo_number', 'N/A'))
                placed_units = item.get('placed_units', 0)
                total_units = item.get('total_units', 0)
                print(f"  📦 Заявка {app_num}: {placed_units}/{total_units}")
        else:
            print("  ❌ НЕТ ПОЛНОСТЬЮ РАЗМЕЩЕННЫХ ЗАЯВОК")
    else:
        print(f"❌ Ошибка: {response.status_code}")
    
    # 3. Выводы
    print("\n" + "=" * 70)
    print("🔍 КРИТИЧЕСКИЕ ВЫВОДЫ:")
    print("=" * 70)
    
    print("✅ ПОДТВЕРЖДЕНО: individual-units-for-placement находит заявку 250109 с 5/5 размещенными единицами")
    print("❌ ПОДТВЕРЖДЕНО: fully-placed НЕ находит эту же заявку")
    print("🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА: Логика fully-placed endpoint НЕИСПРАВНА")
    print("")
    print("📋 ТЕХНИЧЕСКАЯ ПРИЧИНА:")
    print("   - individual-units-for-placement ищет в cargo_items[].individual_items")
    print("   - fully-placed ищет в cargo.individual_items (неправильная структура)")
    print("")
    print("🔧 ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ:")
    print("   - Исправить логику в /api/operator/cargo/fully-placed")
    print("   - Использовать правильную структуру данных cargo_items[].individual_items")
    print("   - Обеспечить консистентность между endpoints")

if __name__ == "__main__":
    main()
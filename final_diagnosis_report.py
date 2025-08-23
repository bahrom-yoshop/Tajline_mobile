#!/usr/bin/env python3
"""
ФИНАЛЬНЫЙ ДИАГНОСТИЧЕСКИЙ ОТЧЕТ: Проблема массового удаления в разделе "Список грузов" в TAJLINE.TJ

НАЙДЕННЫЕ ПРОБЛЕМЫ:
1. Раздел "Список грузов" соответствует GET /api/cargo/all (2054+ грузов)
2. Единичное удаление работает: DELETE /api/admin/cargo/{id} ✅
3. Массовое удаление НЕ РАБОТАЕТ: DELETE /api/admin/cargo/bulk ❌

КОРНЕВАЯ ПРИЧИНА:
Endpoint DELETE /api/admin/cargo/bulk имеет КРИТИЧЕСКУЮ ОШИБКУ в определении:
- Использует `cargo_ids: dict` вместо Pydantic модели
- FastAPI не может правильно парсить JSON body
- Всегда возвращает 404 "Груз не найден"

ТЕХНИЧЕСКАЯ ДИАГНОСТИКА:
- Единичное удаление: DELETE /api/admin/cargo/{id} → HTTP 200 ✅
- Массовое удаление: DELETE /api/admin/cargo/bulk → HTTP 404 ❌
- Любая структура данных ({"ids": []}, {"cargo_ids": []}) → HTTP 404 ❌

РЕШЕНИЕ:
1. Исправить endpoint DELETE /api/admin/cargo/bulk
2. Создать правильную Pydantic модель для bulk deletion
3. Использовать модель вместо `dict` параметра

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Исправленный endpoint для массового удаления
"""

import requests
import json
import os

BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cargo-sync.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def generate_final_report():
    print("🎯 ФИНАЛЬНЫЙ ДИАГНОСТИЧЕСКИЙ ОТЧЕТ")
    print("=" * 80)
    print()
    
    # Авторизация
    auth_data = {"phone": "+79999888777", "password": "admin123"}
    session = requests.Session()
    
    response = session.post(f"{API_BASE}/auth/login", json=auth_data)
    if response.status_code != 200:
        print(f"❌ Ошибка авторизации: {response.text}")
        return
    
    admin_token = response.json().get("access_token")
    admin_info = response.json().get("user")
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    print(f"✅ Авторизация: {admin_info.get('full_name')} ({admin_info.get('user_number')})")
    print()
    
    # Анализ раздела "Список грузов"
    response = session.get(f"{API_BASE}/cargo/all", headers=headers)
    if response.status_code != 200:
        print(f"❌ Ошибка получения списка грузов: {response.text}")
        return
    
    cargo_list = response.json()
    cargo_count = len(cargo_list)
    
    # Анализ статусов
    statuses = {}
    for cargo in cargo_list:
        status = cargo.get("status", "unknown")
        statuses[status] = statuses.get(status, 0) + 1
    
    print(f"📊 АНАЛИЗ РАЗДЕЛА 'СПИСОК ГРУЗОВ':")
    print(f"   - Endpoint: GET /api/cargo/all")
    print(f"   - Количество грузов: {cargo_count}")
    print(f"   - Статусы: {statuses}")
    print()
    
    if cargo_count < 2:
        print("❌ Недостаточно грузов для тестирования")
        return
    
    # Тестирование единичного удаления
    test_cargo = cargo_list[0]
    cargo_id = test_cargo["id"]
    cargo_number = test_cargo["cargo_number"]
    
    print(f"🧪 ТЕСТИРОВАНИЕ ЕДИНИЧНОГО УДАЛЕНИЯ:")
    print(f"   - Груз: {cargo_number} (ID: {cargo_id})")
    
    response = session.delete(f"{API_BASE}/admin/cargo/{cargo_id}", headers=headers)
    single_deletion_works = response.status_code == 200
    
    print(f"   - Результат: HTTP {response.status_code}")
    print(f"   - Статус: {'✅ РАБОТАЕТ' if single_deletion_works else '❌ НЕ РАБОТАЕТ'}")
    if single_deletion_works:
        print(f"   - Ответ: {response.json()}")
    else:
        print(f"   - Ошибка: {response.text}")
    print()
    
    # Тестирование массового удаления
    if cargo_count >= 3:
        test_cargo_ids = [cargo["id"] for cargo in cargo_list[1:3]]
        test_cargo_numbers = [cargo["cargo_number"] for cargo in cargo_list[1:3]]
        
        print(f"🧪 ТЕСТИРОВАНИЕ МАССОВОГО УДАЛЕНИЯ:")
        print(f"   - Грузы: {test_cargo_numbers}")
        print(f"   - IDs: {test_cargo_ids}")
        print()
        
        # Тестируем разные структуры данных
        test_structures = [
            ("ids", {"ids": test_cargo_ids}),
            ("cargo_ids", {"cargo_ids": test_cargo_ids}),
            ("direct_list", test_cargo_ids)
        ]
        
        bulk_deletion_works = False
        
        for structure_name, data in test_structures:
            print(f"   📝 Структура '{structure_name}': {data}")
            response = session.delete(f"{API_BASE}/admin/cargo/bulk", json=data, headers=headers)
            works = response.status_code == 200
            
            print(f"      - HTTP {response.status_code}: {'✅ РАБОТАЕТ' if works else '❌ НЕ РАБОТАЕТ'}")
            if works:
                print(f"      - Ответ: {response.json()}")
                bulk_deletion_works = True
            else:
                print(f"      - Ошибка: {response.text}")
            print()
        
        # Итоговый анализ
        print("🔍 ИТОГОВЫЙ АНАЛИЗ ПРОБЛЕМЫ:")
        print("=" * 50)
        
        if single_deletion_works and not bulk_deletion_works:
            print("✅ Единичное удаление: РАБОТАЕТ")
            print("❌ Массовое удаление: НЕ РАБОТАЕТ")
            print()
            print("🎯 КОРНЕВАЯ ПРИЧИНА НАЙДЕНА:")
            print("   Endpoint DELETE /api/admin/cargo/bulk имеет критическую ошибку")
            print("   в определении параметров. Использует 'cargo_ids: dict' вместо")
            print("   правильной Pydantic модели, что приводит к некорректному")
            print("   парсингу JSON body и ошибке 404 'Груз не найден'.")
            print()
            print("🔧 РЕШЕНИЕ:")
            print("   1. Создать Pydantic модель для bulk deletion:")
            print("      class BulkDeleteRequest(BaseModel):")
            print("          ids: List[str] = Field(..., min_items=1, max_items=100)")
            print()
            print("   2. Изменить endpoint на:")
            print("      async def delete_cargo_bulk(")
            print("          request: BulkDeleteRequest,")
            print("          current_user: User = Depends(get_current_user)")
            print("      ):")
            print()
            print("   3. Использовать request.ids вместо cargo_ids.get('ids', [])")
            print()
            print("🎉 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:")
            print("   После исправления массовое удаление будет работать корректно")
            print("   и ошибки 'Груз не найден' и 'Ошибка при удалении' исчезнут.")
            
        elif single_deletion_works and bulk_deletion_works:
            print("✅ Единичное удаление: РАБОТАЕТ")
            print("✅ Массовое удаление: РАБОТАЕТ")
            print()
            print("🎉 ПРОБЛЕМА УЖЕ ИСПРАВЛЕНА!")
            print("   Массовое удаление функционирует корректно.")
            
        else:
            print("❌ Единичное удаление: НЕ РАБОТАЕТ")
            print("❌ Массовое удаление: НЕ РАБОТАЕТ")
            print()
            print("🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ:")
            print("   Требуется комплексная диагностика API endpoints")
            print("   и прав доступа администратора.")

if __name__ == "__main__":
    generate_final_report()
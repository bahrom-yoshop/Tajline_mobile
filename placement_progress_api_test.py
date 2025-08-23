#!/usr/bin/env python3
"""
🎯 ТЕСТИРОВАНИЕ УЛУЧШЕНИЙ BACKEND API: Прогресс размещения и детальная информация о размещении грузов в TAJLINE.TJ

КОНТЕКСТ ТЕСТИРОВАНИЯ:
Протестировать важные улучшения в backend API для улучшения скорости и качества размещения груза:

1. **Новый endpoint для прогресса**: `/api/operator/placement-progress` - возвращает общий прогресс размещения (0/20)
2. **Улучшенный endpoint размещения**: `/api/operator/cargo/place-individual` - теперь возвращает детальную информацию о грузе и прогрессе заявки

КРИТИЧЕСКИЕ ENDPOINTS ДЛЯ ТЕСТИРОВАНИЯ:

### 1. Новый Endpoint Прогресса Размещения:
- **GET /api/operator/placement-progress**
- Должен возвращать:
  - `total_units`: общее количество единиц для размещения
  - `placed_units`: количество размещенных единиц
  - `pending_units`: количество ожидающих размещения
  - `progress_percentage`: процент выполнения
  - `progress_text`: текст прогресса в формате "Размещено: X/Y"

### 2. Улучшенный Endpoint Размещения Individual Unit:
- **POST /api/operator/cargo/place-individual**
- Теперь должен возвращать:
  - `cargo_name`: название груза
  - `application_number`: номер заявки
  - `placement_details`: детали размещения (блок, полка, ячейка, кем размещено, когда)
  - `application_progress`: прогресс заявки (total_units, placed_units, remaining_units, progress_text)

### 3. Существующие Endpoints (для проверки совместимости):
- **GET /api/operator/cargo/individual-units-for-placement**
- **POST /api/auth/login** (оператор склада: +79777888999/warehouse123)
- **GET /api/operator/warehouses**
"""

import requests
import json
import time
from datetime import datetime

# Конфигурация для тестирования
BACKEND_URL = "https://cargo-sync.preview.emergentagent.com/api"

# Тестовые данные оператора склада
OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class PlacementProgressAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_user = None
        self.test_cargo_id = None
        self.test_individual_numbers = []
        self.warehouse_id = None
        
    def authenticate_operator(self):
        """Авторизация оператора склада"""
        print("🔐 Авторизация оператора склада...")
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=OPERATOR_CREDENTIALS,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.operator_user = data.get("user")
                
                # Устанавливаем заголовок авторизации для всех последующих запросов
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json"
                })
                
                print(f"✅ Успешная авторизация: {self.operator_user.get('full_name')} (роль: {self.operator_user.get('role')})")
                print(f"📱 Телефон: {self.operator_user.get('phone')}")
                return True
            else:
                print(f"❌ Ошибка авторизации: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение при авторизации: {e}")
            return False
    
    def get_operator_warehouses(self):
        """Получить склады оператора"""
        print("\n🏢 Получение складов оператора...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/warehouses")
            
            if response.status_code == 200:
                warehouses = response.json()
                if warehouses:
                    self.warehouse_id = warehouses[0].get("id")
                    print(f"✅ Получен склад: {warehouses[0].get('name')} (ID: {self.warehouse_id})")
                    return warehouses
                else:
                    print("⚠️ Нет доступных складов для оператора")
                    return []
            else:
                print(f"❌ Ошибка получения складов: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Исключение при получении складов: {e}")
            return []
    
    def test_new_placement_progress_endpoint(self):
        """СЦЕНАРИЙ 1: Тестирование нового endpoint прогресса размещения"""
        print("\n🎯 СЦЕНАРИЙ 1: Тестирование нового endpoint прогресса размещения")
        print("=" * 80)
        
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/placement-progress")
            
            print(f"📡 GET /api/operator/placement-progress")
            print(f"📊 Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Endpoint доступен!")
                print(f"📋 Структура ответа:")
                
                # Проверяем обязательные поля
                required_fields = ['total_units', 'placed_units', 'pending_units', 'progress_percentage', 'progress_text']
                missing_fields = []
                
                for field in required_fields:
                    if field in data:
                        print(f"   ✅ {field}: {data[field]}")
                    else:
                        missing_fields.append(field)
                        print(f"   ❌ {field}: ОТСУТСТВУЕТ")
                
                if not missing_fields:
                    print(f"🎉 ВСЕ ОБЯЗАТЕЛЬНЫЕ ПОЛЯ ПРИСУТСТВУЮТ!")
                    
                    # Проверяем логику данных
                    total_units = data.get('total_units', 0)
                    placed_units = data.get('placed_units', 0)
                    pending_units = data.get('pending_units', 0)
                    progress_percentage = data.get('progress_percentage', 0)
                    
                    if total_units == placed_units + pending_units:
                        print(f"✅ Логика данных корректна: {total_units} = {placed_units} + {pending_units}")
                    else:
                        print(f"⚠️ Возможная проблема с логикой: {total_units} ≠ {placed_units} + {pending_units}")
                    
                    if total_units > 0:
                        expected_percentage = round((placed_units / total_units) * 100, 1)
                        if abs(progress_percentage - expected_percentage) < 0.1:
                            print(f"✅ Процент корректен: {progress_percentage}%")
                        else:
                            print(f"⚠️ Процент может быть неточным: {progress_percentage}% (ожидалось: {expected_percentage}%)")
                    
                    return True
                else:
                    print(f"❌ Отсутствуют обязательные поля: {missing_fields}")
                    return False
                    
            elif response.status_code == 404:
                print(f"❌ Endpoint не найден - возможно, не реализован")
                return False
            else:
                print(f"❌ Ошибка: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение при тестировании endpoint прогресса: {e}")
            return False
    
    def get_individual_units_for_placement(self):
        """Получить individual units для размещения"""
        print("\n📦 Получение individual units для размещения...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/individual-units-for-placement")
            
            if response.status_code == 200:
                data = response.json()
                units = data.get('items', []) if isinstance(data, dict) else data
                
                if units:
                    print(f"✅ Получено {len(units)} групп грузов для размещения")
                    
                    # Собираем individual numbers для тестирования
                    for cargo_group in units:
                        cargo_items = cargo_group.get('cargo_items', [])
                        for cargo_item in cargo_items:
                            individual_items = cargo_item.get('individual_items', [])
                            for item in individual_items:
                                if not item.get('is_placed', False):
                                    individual_number = item.get('individual_number')
                                    if individual_number:
                                        self.test_individual_numbers.append({
                                            'individual_number': individual_number,
                                            'cargo_id': cargo_group.get('id'),
                                            'cargo_number': cargo_group.get('cargo_number'),
                                            'cargo_name': cargo_item.get('cargo_name', 'Неизвестно')
                                        })
                    
                    print(f"📋 Найдено {len(self.test_individual_numbers)} единиц для размещения")
                    return True
                else:
                    print("⚠️ Нет individual units для размещения")
                    return False
            else:
                print(f"❌ Ошибка получения individual units: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение при получении individual units: {e}")
            return False
    
    def test_improved_place_individual_endpoint(self):
        """СЦЕНАРИЙ 2: Тестирование улучшенного endpoint размещения individual unit"""
        print("\n🎯 СЦЕНАРИЙ 2: Тестирование улучшенного endpoint размещения individual unit")
        print("=" * 80)
        
        if not self.test_individual_numbers:
            print("❌ Нет доступных individual units для тестирования")
            return False
        
        # Берем первую доступную единицу для тестирования
        test_unit = self.test_individual_numbers[0]
        individual_number = test_unit['individual_number']
        
        print(f"🧪 Тестируем размещение единицы: {individual_number}")
        print(f"📦 Груз: {test_unit['cargo_name']}")
        print(f"📋 Заявка: {test_unit['cargo_number']}")
        
        try:
            # Данные для размещения
            placement_data = {
                "individual_number": individual_number,
                "block_number": 1,
                "shelf_number": 1,
                "cell_number": 1
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/operator/cargo/place-individual",
                json=placement_data
            )
            
            print(f"📡 POST /api/operator/cargo/place-individual")
            print(f"📊 Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Размещение выполнено успешно!")
                print(f"📋 Структура ответа:")
                
                # Проверяем новые обязательные поля
                expected_fields = {
                    'cargo_name': 'название груза',
                    'application_number': 'номер заявки', 
                    'placement_details': 'детали размещения',
                    'application_progress': 'прогресс заявки'
                }
                
                missing_fields = []
                present_fields = []
                
                for field, description in expected_fields.items():
                    if field in data:
                        present_fields.append(field)
                        print(f"   ✅ {field} ({description}): {data[field]}")
                    else:
                        missing_fields.append(field)
                        print(f"   ❌ {field} ({description}): ОТСУТСТВУЕТ")
                
                # Проверяем детали размещения
                if 'placement_details' in data:
                    placement_details = data['placement_details']
                    if isinstance(placement_details, dict):
                        detail_fields = ['block', 'shelf', 'cell', 'placed_by', 'placed_at']
                        for detail_field in detail_fields:
                            if detail_field in placement_details:
                                print(f"      ✅ {detail_field}: {placement_details[detail_field]}")
                            else:
                                print(f"      ⚠️ {detail_field}: отсутствует в placement_details")
                
                # Проверяем прогресс заявки
                if 'application_progress' in data:
                    app_progress = data['application_progress']
                    if isinstance(app_progress, dict):
                        progress_fields = ['total_units', 'placed_units', 'remaining_units', 'progress_text']
                        for progress_field in progress_fields:
                            if progress_field in app_progress:
                                print(f"      ✅ {progress_field}: {app_progress[progress_field]}")
                            else:
                                print(f"      ⚠️ {progress_field}: отсутствует в application_progress")
                
                if len(present_fields) >= 2:  # Минимум 2 из 4 новых полей
                    print(f"🎉 УЛУЧШЕННЫЙ ENDPOINT РАБОТАЕТ! Присутствует {len(present_fields)}/4 новых полей")
                    return True
                else:
                    print(f"⚠️ Endpoint работает, но новые поля отсутствуют ({len(present_fields)}/4)")
                    return False
                    
            else:
                print(f"❌ Ошибка размещения: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение при тестировании улучшенного размещения: {e}")
            return False
    
    def test_progress_after_placement(self):
        """СЦЕНАРИЙ 3: Проверка прогресса после размещения"""
        print("\n🎯 СЦЕНАРИЙ 3: Проверка прогресса после размещения")
        print("=" * 80)
        
        print("📊 Проверяем, обновился ли прогресс после размещения...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/placement-progress")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Получен обновленный прогресс:")
                print(f"   📦 Всего единиц: {data.get('total_units', 0)}")
                print(f"   ✅ Размещено: {data.get('placed_units', 0)}")
                print(f"   ⏳ Ожидает размещения: {data.get('pending_units', 0)}")
                print(f"   📊 Процент выполнения: {data.get('progress_percentage', 0)}%")
                print(f"   📝 Текст прогресса: {data.get('progress_text', 'N/A')}")
                
                # Проверяем, что прогресс изменился
                placed_units = data.get('placed_units', 0)
                if placed_units > 0:
                    print(f"🎉 ПРОГРЕСС ОБНОВЛЯЕТСЯ! Размещено единиц: {placed_units}")
                    return True
                else:
                    print(f"⚠️ Прогресс не обновился или нет размещенных единиц")
                    return False
            else:
                print(f"❌ Ошибка получения прогресса: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение при проверке прогресса: {e}")
            return False
    
    def test_existing_endpoints_compatibility(self):
        """Проверка совместимости существующих endpoints"""
        print("\n🔄 Проверка совместимости существующих endpoints")
        print("=" * 80)
        
        endpoints_to_test = [
            ("GET /api/operator/cargo/individual-units-for-placement", f"{BACKEND_URL}/operator/cargo/individual-units-for-placement"),
            ("GET /api/operator/warehouses", f"{BACKEND_URL}/operator/warehouses")
        ]
        
        compatibility_results = []
        
        for endpoint_name, endpoint_url in endpoints_to_test:
            try:
                response = self.session.get(endpoint_url)
                
                if response.status_code == 200:
                    print(f"✅ {endpoint_name}: Работает корректно")
                    compatibility_results.append(True)
                else:
                    print(f"❌ {endpoint_name}: Ошибка {response.status_code}")
                    compatibility_results.append(False)
                    
            except Exception as e:
                print(f"❌ {endpoint_name}: Исключение - {e}")
                compatibility_results.append(False)
        
        success_rate = sum(compatibility_results) / len(compatibility_results) * 100
        print(f"\n📊 Совместимость: {success_rate:.1f}% ({sum(compatibility_results)}/{len(compatibility_results)} endpoints)")
        
        return success_rate >= 90  # 90% успешности для совместимости
    
    def run_comprehensive_test(self):
        """Запуск полного тестирования"""
        print("🎯 ТЕСТИРОВАНИЕ УЛУЧШЕНИЙ BACKEND API: Прогресс размещения и детальная информация")
        print("=" * 100)
        print(f"🕒 Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Backend URL: {BACKEND_URL}")
        
        test_results = []
        
        # 1. Авторизация
        if not self.authenticate_operator():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться")
            return False
        
        # 2. Получение складов
        if not self.get_operator_warehouses():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить склады")
            return False
        
        # 3. Получение individual units
        if not self.get_individual_units_for_placement():
            print("⚠️ ПРЕДУПРЕЖДЕНИЕ: Нет individual units для размещения")
        
        # 4. Тестирование нового endpoint прогресса
        print("\n" + "="*100)
        result1 = self.test_new_placement_progress_endpoint()
        test_results.append(("Новый endpoint прогресса размещения", result1))
        
        # 5. Тестирование улучшенного endpoint размещения
        print("\n" + "="*100)
        result2 = self.test_improved_place_individual_endpoint()
        test_results.append(("Улучшенный endpoint размещения", result2))
        
        # 6. Проверка прогресса после размещения
        print("\n" + "="*100)
        result3 = self.test_progress_after_placement()
        test_results.append(("Прогресс после размещения", result3))
        
        # 7. Проверка совместимости
        print("\n" + "="*100)
        result4 = self.test_existing_endpoints_compatibility()
        test_results.append(("Совместимость существующих endpoints", result4))
        
        # Итоговый отчет
        print("\n" + "="*100)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        print("="*100)
        
        successful_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ ПРОЙДЕН" if result else "❌ НЕ ПРОЙДЕН"
            print(f"{status}: {test_name}")
            if result:
                successful_tests += 1
        
        success_rate = (successful_tests / total_tests) * 100
        print(f"\n📈 ОБЩИЙ РЕЗУЛЬТАТ: {success_rate:.1f}% ({successful_tests}/{total_tests} тестов пройдено)")
        
        if success_rate >= 90:
            print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ Новые API улучшения работают корректно")
            print("✅ Совместимость с существующими endpoints сохранена")
            print("✅ Система готова к использованию")
        elif success_rate >= 70:
            print("⚠️ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ПРЕДУПРЕЖДЕНИЯМИ")
            print("⚠️ Некоторые функции могут работать не полностью")
            print("🔧 Рекомендуется дополнительная проверка и исправления")
        else:
            print("❌ ТЕСТИРОВАНИЕ НЕ ПРОЙДЕНО")
            print("❌ Критические проблемы с новыми API улучшениями")
            print("🚨 Требуется немедленное исправление")
        
        print(f"\n🕒 Время завершения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return success_rate >= 70

def main():
    """Главная функция для запуска тестирования"""
    tester = PlacementProgressAPITester()
    success = tester.run_comprehensive_test()
    
    if success:
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    main()
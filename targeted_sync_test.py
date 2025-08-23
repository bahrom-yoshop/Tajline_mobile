#!/usr/bin/env python3
"""
🎯 ЦЕЛЕВОЕ ТЕСТИРОВАНИЕ: Исследование проблемы синхронизации данных и заявки 250109
"""

import requests
import json
import time
from datetime import datetime
import os
import random

# Конфигурация для тестирования
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-manage-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Тестовые данные оператора склада
OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class TargetedSyncTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_user = None
        self.warehouse_id = None
        
    def authenticate_operator(self):
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
                return False
                
        except Exception as e:
            print(f"❌ Исключение при авторизации: {str(e)}")
            return False
    
    def get_operator_warehouse(self):
        """Получение склада оператора"""
        try:
            print("🏢 Получение склада оператора...")
            
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

    def investigate_application_250109(self):
        """Исследование заявки 250109"""
        print("\n🔍 ИССЛЕДОВАНИЕ ЗАЯВКИ 250109")
        print("=" * 50)
        
        # Проверяем в available-for-placement
        print("📋 Поиск в available-for-placement...")
        available_response = self.session.get(f"{API_BASE}/operator/cargo/available-for-placement", timeout=30)
        
        found_in_available = False
        if available_response.status_code == 200:
            available_data = available_response.json()
            available_items = available_data.get("items", [])
            
            for item in available_items:
                if item.get("cargo_number") == "250109":
                    found_in_available = True
                    print(f"✅ Заявка 250109 найдена в available-for-placement")
                    
                    # Анализируем состояние individual_items
                    cargo_items = item.get("cargo_items", [])
                    print(f"   📦 Количество типов груза: {len(cargo_items)}")
                    
                    total_units = 0
                    placed_units = 0
                    
                    for i, cargo_item in enumerate(cargo_items):
                        individual_items = cargo_item.get("individual_items", [])
                        cargo_total = len(individual_items)
                        cargo_placed = sum(1 for unit in individual_items if unit.get("is_placed", False))
                        
                        total_units += cargo_total
                        placed_units += cargo_placed
                        
                        print(f"   📦 Тип груза {i+1}: {cargo_placed}/{cargo_total} размещено")
                        
                        # Показываем детали первых нескольких единиц
                        for j, unit in enumerate(individual_items[:3]):
                            individual_number = unit.get("individual_number", "N/A")
                            is_placed = unit.get("is_placed", False)
                            print(f"     📋 Единица {j+1}: {individual_number} - размещена: {is_placed}")
                    
                    print(f"   📊 ИТОГО: {placed_units}/{total_units} единиц размещено")
                    break
        else:
            print(f"❌ Ошибка получения available-for-placement: {available_response.status_code}")
        
        # Проверяем в fully-placed
        print("\n📋 Поиск в fully-placed...")
        fully_placed_response = self.session.get(f"{API_BASE}/operator/cargo/fully-placed", timeout=30)
        
        found_in_fully_placed = False
        if fully_placed_response.status_code == 200:
            fully_placed_data = fully_placed_response.json()
            fully_placed_items = fully_placed_data.get("items", [])
            
            for item in fully_placed_items:
                if item.get("cargo_number") == "250109":
                    found_in_fully_placed = True
                    print(f"✅ Заявка 250109 найдена в fully-placed")
                    break
        else:
            print(f"❌ Ошибка получения fully-placed: {fully_placed_response.status_code}")
        
        # Результат исследования
        print(f"\n📊 РЕЗУЛЬТАТ ИССЛЕДОВАНИЯ ЗАЯВКИ 250109:")
        print(f"   Available-for-placement: {'✅ Найдена' if found_in_available else '❌ Не найдена'}")
        print(f"   Fully-placed: {'✅ Найдена' if found_in_fully_placed else '❌ Не найдена'}")
        
        if found_in_available and found_in_fully_placed:
            print("   ⚠️ ПРОБЛЕМА: Заявка найдена в ОБОИХ списках!")
        elif not found_in_available and not found_in_fully_placed:
            print("   ⚠️ ПРОБЛЕМА: Заявка НЕ найдена ни в одном списке!")
        elif found_in_available:
            print("   ✅ Заявка корректно находится в available-for-placement")
        else:
            print("   ✅ Заявка корректно находится в fully-placed")

    def test_placement_with_random_cells(self):
        """Тестирование размещения с случайными ячейками"""
        print("\n🎯 ТЕСТИРОВАНИЕ РАЗМЕЩЕНИЯ С СЛУЧАЙНЫМИ ЯЧЕЙКАМИ")
        print("=" * 50)
        
        # Получаем список заявок для размещения
        available_response = self.session.get(f"{API_BASE}/operator/cargo/available-for-placement", timeout=30)
        
        if available_response.status_code != 200:
            print(f"❌ Ошибка получения заявок: {available_response.status_code}")
            return False
        
        available_data = available_response.json()
        available_items = available_data.get("items", [])
        
        if not available_items:
            print("❌ Нет заявок для размещения")
            return False
        
        # Берем первую заявку
        first_cargo = available_items[0]
        cargo_number = first_cargo.get("cargo_number")
        print(f"📦 Тестируем заявку: {cargo_number}")
        
        # Получаем первую единицу для размещения
        cargo_items = first_cargo.get("cargo_items", [])
        if not cargo_items:
            print("❌ Нет cargo_items")
            return False
        
        individual_items = cargo_items[0].get("individual_items", [])
        if not individual_items:
            print("❌ Нет individual_items")
            return False
        
        # Ищем не размещенную единицу
        test_unit = None
        for unit in individual_items:
            if not unit.get("is_placed", False):
                test_unit = unit
                break
        
        if not test_unit:
            print("❌ Все единицы уже размещены")
            return False
        
        individual_number = test_unit.get("individual_number")
        print(f"📋 Размещаем единицу: {individual_number}")
        
        # Пробуем разные случайные ячейки
        for attempt in range(10):
            block = random.randint(1, 4)
            shelf = random.randint(1, 4)
            cell = random.randint(1, 50)
            
            print(f"   Попытка {attempt + 1}: Блок {block}, Полка {shelf}, Ячейка {cell}")
            
            placement_data = {
                "individual_number": individual_number,
                "block_number": block,
                "shelf_number": shelf,
                "cell_number": cell
            }
            
            place_response = self.session.post(
                f"{API_BASE}/operator/cargo/place-individual",
                json=placement_data,
                timeout=30
            )
            
            if place_response.status_code == 200:
                place_data = place_response.json()
                print(f"   ✅ УСПЕШНО! Единица размещена: {place_data.get('message', 'Успешно')}")
                
                # Проверяем синхронизацию данных
                time.sleep(2)
                
                # Получаем обновленные данные
                updated_response = self.session.get(f"{API_BASE}/operator/cargo/available-for-placement", timeout=30)
                
                if updated_response.status_code == 200:
                    updated_data = updated_response.json()
                    updated_items = updated_data.get("items", [])
                    
                    # Ищем обновленную заявку
                    updated_cargo = None
                    for item in updated_items:
                        if item.get("cargo_number") == cargo_number:
                            updated_cargo = item
                            break
                    
                    if updated_cargo:
                        # Проверяем обновленное состояние
                        updated_cargo_items = updated_cargo.get("cargo_items", [])
                        if updated_cargo_items:
                            updated_individual_items = updated_cargo_items[0].get("individual_items", [])
                            
                            updated_unit = None
                            for unit in updated_individual_items:
                                if unit.get("individual_number") == individual_number:
                                    updated_unit = unit
                                    break
                            
                            if updated_unit:
                                is_placed_after = updated_unit.get("is_placed", False)
                                print(f"   📊 Синхронизация: is_placed = {is_placed_after}")
                                
                                if is_placed_after:
                                    print("   ✅ СИНХРОНИЗАЦИЯ РАБОТАЕТ! individual_items.is_placed обновлен корректно")
                                    return True
                                else:
                                    print("   ❌ СИНХРОНИЗАЦИЯ НЕ РАБОТАЕТ! individual_items.is_placed не обновлен")
                                    return False
                            else:
                                print("   ❌ Размещенная единица не найдена в обновленных данных")
                        else:
                            print("   ❌ Отсутствуют cargo_items в обновленных данных")
                    else:
                        print("   📋 Заявка исчезла из available-for-placement - возможно перемещена в fully-placed")
                        
                        # Проверяем fully-placed
                        fully_placed_response = self.session.get(f"{API_BASE}/operator/cargo/fully-placed", timeout=30)
                        if fully_placed_response.status_code == 200:
                            fully_placed_data = fully_placed_response.json()
                            fully_placed_items = fully_placed_data.get("items", [])
                            
                            found_in_fully_placed = False
                            for item in fully_placed_items:
                                if item.get("cargo_number") == cargo_number:
                                    found_in_fully_placed = True
                                    break
                            
                            if found_in_fully_placed:
                                print("   ✅ ОТЛИЧНО! Заявка корректно перемещена в fully-placed")
                                return True
                            else:
                                print("   ❌ Заявка не найдена в fully-placed")
                                return False
                        else:
                            print(f"   ❌ Ошибка получения fully-placed: {fully_placed_response.status_code}")
                            return False
                else:
                    print(f"   ❌ Ошибка получения обновленных данных: {updated_response.status_code}")
                    return False
                    
            elif place_response.status_code == 400:
                try:
                    error_data = place_response.json()
                    error_detail = error_data.get("detail", "Неизвестная ошибка")
                    print(f"   ❌ Ячейка занята или недоступна: {error_detail}")
                except:
                    print(f"   ❌ Ошибка 400: {place_response.text}")
            else:
                print(f"   ❌ Ошибка размещения: {place_response.status_code}")
        
        print("❌ Не удалось найти свободную ячейку после 10 попыток")
        return False

    def check_placement_records_vs_individual_items(self):
        """Проверка соответствия между placement_records и individual_items"""
        print("\n🔍 ПРОВЕРКА СООТВЕТСТВИЯ PLACEMENT_RECORDS И INDIVIDUAL_ITEMS")
        print("=" * 60)
        
        # Получаем статистику размещения
        progress_response = self.session.get(f"{API_BASE}/operator/placement-progress", timeout=30)
        
        if progress_response.status_code == 200:
            progress_data = progress_response.json()
            total_units = progress_data.get("total_units", 0)
            placed_units = progress_data.get("placed_units", 0)
            pending_units = progress_data.get("pending_units", 0)
            
            print(f"📊 Статистика размещения:")
            print(f"   Всего единиц: {total_units}")
            print(f"   Размещено: {placed_units}")
            print(f"   Ожидает размещения: {pending_units}")
            print(f"   Прогресс: {progress_data.get('progress_percentage', 0):.1f}%")
            
            # Проверяем математическую корректность
            if total_units == placed_units + pending_units:
                print("   ✅ Математика корректна")
            else:
                print(f"   ❌ Математическая ошибка: {total_units} ≠ {placed_units} + {pending_units}")
        else:
            print(f"❌ Ошибка получения статистики размещения: {progress_response.status_code}")
        
        # Получаем заявки для размещения и анализируем их
        available_response = self.session.get(f"{API_BASE}/operator/cargo/available-for-placement", timeout=30)
        
        if available_response.status_code == 200:
            available_data = available_response.json()
            available_items = available_data.get("items", [])
            
            print(f"\n📋 Анализ заявок в available-for-placement ({len(available_items)} заявок):")
            
            total_individual_units = 0
            total_placed_individual_units = 0
            
            for i, item in enumerate(available_items[:5]):  # Анализируем первые 5 заявок
                cargo_number = item.get("cargo_number")
                cargo_items = item.get("cargo_items", [])
                
                cargo_total = 0
                cargo_placed = 0
                
                for cargo_item in cargo_items:
                    individual_items = cargo_item.get("individual_items", [])
                    cargo_total += len(individual_items)
                    cargo_placed += sum(1 for unit in individual_items if unit.get("is_placed", False))
                
                total_individual_units += cargo_total
                total_placed_individual_units += cargo_placed
                
                print(f"   {i+1}. {cargo_number}: {cargo_placed}/{cargo_total} размещено")
            
            print(f"\n📊 Итого по individual_items в available-for-placement:")
            print(f"   Всего единиц: {total_individual_units}")
            print(f"   Размещено: {total_placed_individual_units}")
            print(f"   Не размещено: {total_individual_units - total_placed_individual_units}")
        else:
            print(f"❌ Ошибка получения available-for-placement: {available_response.status_code}")

    def run_investigation(self):
        """Запуск полного исследования"""
        print("🔍 НАЧАЛО ЦЕЛЕВОГО ИССЛЕДОВАНИЯ СИНХРОНИЗАЦИИ ДАННЫХ")
        print("=" * 70)
        
        # Подготовка
        if not self.authenticate_operator():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться")
            return False
        
        if not self.get_operator_warehouse():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить склад оператора")
            return False
        
        # Исследования
        self.investigate_application_250109()
        self.check_placement_records_vs_individual_items()
        placement_success = self.test_placement_with_random_cells()
        
        print("\n" + "=" * 70)
        print("📊 РЕЗУЛЬТАТЫ ИССЛЕДОВАНИЯ:")
        print("=" * 70)
        
        if placement_success:
            print("✅ СИНХРОНИЗАЦИЯ ДАННЫХ РАБОТАЕТ КОРРЕКТНО!")
            print("   Размещение единиц обновляет individual_items.is_placed")
            print("   Заявки корректно перемещаются между списками")
        else:
            print("❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ С СИНХРОНИЗАЦИЕЙ!")
            print("   Требуется дополнительная диагностика и исправления")
        
        return placement_success

def main():
    """Главная функция"""
    tester = TargetedSyncTester()
    success = tester.run_investigation()
    
    if success:
        print("\n🎯 ИССЛЕДОВАНИЕ ЗАВЕРШЕНО: СИНХРОНИЗАЦИЯ РАБОТАЕТ!")
        return 0
    else:
        print("\n❌ ИССЛЕДОВАНИЕ ВЫЯВИЛО ПРОБЛЕМЫ С СИНХРОНИЗАЦИЕЙ!")
        return 1

if __name__ == "__main__":
    exit(main())
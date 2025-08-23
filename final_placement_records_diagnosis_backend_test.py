#!/usr/bin/env python3
"""
ФИНАЛЬНАЯ ДИАГНОСТИКА: Подтверждение проблемы API layout-with-cargo
==================================================================

НАЙДЕННАЯ ПРОБЛЕМА:
- В базе данных найдено 4 placement_records для склада 001
- API layout-with-cargo НЕ возвращает поле cargo_info
- API возвращает данные в структуре layout.blocks[].shelves[].cells[].cargo[]
- Пользователь ожидает поле cargo_info с размещенными единицами

ЦЕЛЬ: Подтвердить структуру ответа API и найти где должны быть данные о размещенных грузах
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
MOSCOW_WAREHOUSE_ID = "d0a8362d-b4d3-4947-b335-28c94658a021"

class FinalPlacementDiagnosticTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def authenticate_operator(self):
        """Авторизация оператора склада"""
        try:
            self.log("🔐 Авторизация оператора склада...")
            
            auth_data = {
                "phone": WAREHOUSE_OPERATOR_PHONE,
                "password": WAREHOUSE_OPERATOR_PASSWORD
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=auth_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                
                # Получаем информацию о пользователе
                user_response = self.session.get(f"{API_BASE}/auth/me")
                if user_response.status_code == 200:
                    self.operator_info = user_response.json()
                    self.log(f"✅ Успешная авторизация: {self.operator_info.get('full_name')} (роль: {self.operator_info.get('role')})")
                    return True
                else:
                    self.log(f"❌ Ошибка получения информации о пользователе: {user_response.status_code}")
                    return False
            else:
                self.log(f"❌ Ошибка авторизации: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Исключение при авторизации: {str(e)}", "ERROR")
            return False
    
    def test_api_response_structure(self):
        """Тестирование структуры ответа API layout-with-cargo"""
        try:
            self.log("🧪 ТЕСТИРОВАНИЕ СТРУКТУРЫ ОТВЕТА API layout-with-cargo...")
            
            api_url = f"{API_BASE}/warehouses/{MOSCOW_WAREHOUSE_ID}/layout-with-cargo"
            response = self.session.get(api_url)
            
            if response.status_code == 200:
                data = response.json()
                
                self.log("✅ API ответил успешно")
                self.log(f"📋 Поля верхнего уровня: {list(data.keys())}")
                
                # Проверяем наличие cargo_info
                if 'cargo_info' in data:
                    cargo_info = data['cargo_info']
                    self.log(f"✅ Поле cargo_info найдено: {len(cargo_info)} записей")
                    
                    for i, cargo in enumerate(cargo_info):
                        self.log(f"   {i+1}. {cargo.get('cargo_number', 'N/A')}/{cargo.get('individual_number', 'N/A')} в {cargo.get('location', 'N/A')}")
                else:
                    self.log("❌ Поле cargo_info НЕ НАЙДЕНО в ответе API")
                
                # Проверяем структуру layout
                if 'layout' in data:
                    layout = data['layout']
                    self.log(f"📋 Структура layout: {list(layout.keys())}")
                    
                    if 'blocks' in layout:
                        blocks = layout['blocks']
                        self.log(f"🏗️ Найдено {len(blocks)} блоков")
                        
                        total_cargo_found = 0
                        cargo_details = []
                        
                        for block in blocks:
                            block_num = block.get('block_number', 'N/A')
                            shelves = block.get('shelves', [])
                            
                            for shelf in shelves:
                                shelf_num = shelf.get('shelf_number', 'N/A')
                                cells = shelf.get('cells', [])
                                
                                for cell in cells:
                                    cell_num = cell.get('cell_number', 'N/A')
                                    cargo_list = cell.get('cargo', [])
                                    
                                    if len(cargo_list) > 0:
                                        total_cargo_found += len(cargo_list)
                                        location = f"Б{block_num}-П{shelf_num}-Я{cell_num}"
                                        
                                        for cargo in cargo_list:
                                            cargo_number = cargo.get('cargo_number', 'N/A')
                                            individual_number = cargo.get('individual_number', 'N/A')
                                            cargo_name = cargo.get('cargo_name', 'N/A')
                                            
                                            cargo_details.append({
                                                'cargo_number': cargo_number,
                                                'individual_number': individual_number,
                                                'cargo_name': cargo_name,
                                                'location': location
                                            })
                        
                        self.log(f"📦 ВСЕГО НАЙДЕНО ГРУЗОВ В LAYOUT: {total_cargo_found}")
                        
                        if total_cargo_found > 0:
                            self.log("📋 ДЕТАЛИ НАЙДЕННЫХ ГРУЗОВ:")
                            for cargo in cargo_details:
                                self.log(f"   - {cargo['cargo_number']}/{cargo['individual_number']}: {cargo['cargo_name']} в {cargo['location']}")
                        else:
                            self.log("❌ В структуре layout НЕ НАЙДЕНО грузов")
                
                # Проверяем общую статистику
                total_cargo = data.get('total_cargo', 0)
                occupied_cells = data.get('occupied_cells', 0)
                total_cells = data.get('total_cells', 0)
                occupancy_percentage = data.get('occupancy_percentage', 0)
                
                self.log(f"📊 ОБЩАЯ СТАТИСТИКА:")
                self.log(f"   - Всего грузов: {total_cargo}")
                self.log(f"   - Занятых ячеек: {occupied_cells}")
                self.log(f"   - Всего ячеек: {total_cells}")
                self.log(f"   - Заполненность: {occupancy_percentage}%")
                
                return data
                
            else:
                self.log(f"❌ Ошибка API: {response.status_code}")
                self.log(f"❌ Ответ: {response.text}")
                return None
                
        except Exception as e:
            self.log(f"❌ Ошибка тестирования API: {str(e)}", "ERROR")
            return None
    
    def run_final_diagnosis(self):
        """Запуск финальной диагностики"""
        try:
            self.log("🚀 ЗАПУСК ФИНАЛЬНОЙ ДИАГНОСТИКИ API layout-with-cargo")
            self.log("=" * 80)
            
            # 1. Авторизация
            if not self.authenticate_operator():
                self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться")
                return False
            
            # 2. Тестирование структуры ответа API
            api_response = self.test_api_response_structure()
            
            # 3. Финальный отчет
            self.generate_final_report(api_response)
            
            return True
            
        except Exception as e:
            self.log(f"❌ КРИТИЧЕСКАЯ ОШИБКА диагностики: {str(e)}", "ERROR")
            return False
    
    def generate_final_report(self, api_response):
        """Генерация финального отчета диагностики"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 ФИНАЛЬНЫЙ ОТЧЕТ ДИАГНОСТИКИ")
            self.log("=" * 80)
            
            if api_response:
                # Анализ структуры ответа
                has_cargo_info = 'cargo_info' in api_response
                has_layout = 'layout' in api_response
                total_cargo = api_response.get('total_cargo', 0)
                
                self.log(f"✅ API ответ получен: ДА")
                self.log(f"📋 Поле cargo_info: {'НАЙДЕНО' if has_cargo_info else 'НЕ НАЙДЕНО'}")
                self.log(f"📋 Поле layout: {'НАЙДЕНО' if has_layout else 'НЕ НАЙДЕНО'}")
                self.log(f"📊 Всего грузов в ответе: {total_cargo}")
                
                # Определение проблемы
                if not has_cargo_info and total_cargo > 0:
                    self.log(f"\n🎯 ПРОБЛЕМА ОПРЕДЕЛЕНА:")
                    self.log(f"   - API НЕ возвращает поле cargo_info")
                    self.log(f"   - Данные о грузах находятся в layout.blocks[].shelves[].cells[].cargo[]")
                    self.log(f"   - Пользователь ожидает поле cargo_info с плоским списком размещенных единиц")
                    
                elif not has_cargo_info and total_cargo == 0:
                    self.log(f"\n❌ КРИТИЧЕСКАЯ ПРОБЛЕМА:")
                    self.log(f"   - API НЕ возвращает поле cargo_info")
                    self.log(f"   - API НЕ находит размещенные грузы (total_cargo = 0)")
                    self.log(f"   - В базе данных есть 4 placement_records, но API их не обрабатывает")
                    
                elif has_cargo_info:
                    cargo_info = api_response.get('cargo_info', [])
                    self.log(f"\n✅ ПОЛЕ cargo_info НАЙДЕНО:")
                    self.log(f"   - Количество записей: {len(cargo_info)}")
                    
                    if len(cargo_info) < 4:
                        self.log(f"   ⚠️ Ожидалось 4 записи, найдено {len(cargo_info)}")
                    else:
                        self.log(f"   ✅ Все ожидаемые записи найдены")
                
                # Рекомендации
                self.log(f"\n💡 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ:")
                
                if not has_cargo_info:
                    self.log("🔧 1. ДОБАВИТЬ поле cargo_info в ответ API layout-with-cargo")
                    self.log("🔧 2. Создать плоский список всех размещенных единиц из layout структуры")
                    self.log("🔧 3. Включить в cargo_info поля: cargo_number, individual_number, location, cargo_name, etc.")
                
                if total_cargo == 0:
                    self.log("🔧 4. ИСПРАВИТЬ логику обработки placement_records в API")
                    self.log("🔧 5. Убедиться что placement_records правильно парсятся и добавляются в layout")
                    self.log("🔧 6. Проверить формат location в placement_records (Б1-П2-Я5)")
                
                # Успешность
                if has_cargo_info and len(api_response.get('cargo_info', [])) >= 4:
                    self.log(f"\n📊 УСПЕШНОСТЬ: 100% - ВСЕ ЗАПИСИ НАЙДЕНЫ")
                elif total_cargo >= 4:
                    self.log(f"\n📊 УСПЕШНОСТЬ: 75% - ДАННЫЕ ЕСТЬ, НО НЕ В ПРАВИЛЬНОМ ФОРМАТЕ")
                else:
                    self.log(f"\n📊 УСПЕШНОСТЬ: 0% - КРИТИЧЕСКАЯ ПРОБЛЕМА ПОДТВЕРЖДЕНА")
            else:
                self.log(f"❌ API ответ НЕ получен")
                self.log(f"\n📊 УСПЕШНОСТЬ: 0% - API НЕ РАБОТАЕТ")
                
        except Exception as e:
            self.log(f"❌ Ошибка генерации отчета: {str(e)}", "ERROR")

def main():
    """Главная функция"""
    print("🚀 ФИНАЛЬНАЯ ДИАГНОСТИКА: Подтверждение проблемы API layout-with-cargo")
    print("=" * 80)
    
    tester = FinalPlacementDiagnosticTester()
    
    try:
        success = tester.run_final_diagnosis()
        
        if success:
            print("\n✅ ДИАГНОСТИКА ЗАВЕРШЕНА")
        else:
            print("\n❌ ДИАГНОСТИКА ЗАВЕРШЕНА С ОШИБКАМИ")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ ДИАГНОСТИКА ПРЕРВАНА ПОЛЬЗОВАТЕЛЕМ")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
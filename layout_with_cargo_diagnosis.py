#!/usr/bin/env python3
"""
ДИАГНОСТИКА API layout-with-cargo: Почему не находит данные USR648425
====================================================================

НАЙДЕННЫЕ ДАННЫЕ:
- Заявка 25082298: 7 единиц размещено оператором "Юлдашев Жасурбек Бахтиёрович"
- Заявка 250101: 1 единица размещена тем же оператором
- Данные найдены в /operator/cargo/fully-placed

ПРОБЛЕМА: API layout-with-cargo возвращает только 4 единицы, не включая данные USR648425

ЦЕЛЬ: Понять почему layout-with-cargo не обрабатывает данные из operator_cargo коллекции
"""

import requests
import json
import sys
import os
from datetime import datetime

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cargo-sync.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class LayoutWithCargoDebugger:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.warehouse_id = None
        self.warehouse_info = None

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def authenticate_operator(self):
        """Авторизация оператора склада"""
        try:
            self.log("🔐 Авторизация оператора склада...")
            
            auth_data = {
                "phone": "+79777888999",
                "password": "warehouse123"
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=auth_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                
                user_response = self.session.get(f"{API_BASE}/auth/me")
                if user_response.status_code == 200:
                    self.operator_info = user_response.json()
                    self.log(f"✅ Авторизация: {self.operator_info.get('full_name')} (роль: {self.operator_info.get('role')})")
                    return True
            
            return False
                
        except Exception as e:
            self.log(f"❌ Ошибка авторизации: {e}", "ERROR")
            return False

    def get_warehouse_info(self):
        """Получение информации о складе оператора"""
        try:
            self.log("🏢 Получение информации о складе...")
            
            response = self.session.get(f"{API_BASE}/operator/warehouses")
            if response.status_code == 200:
                warehouses = response.json()
                if warehouses:
                    self.warehouse_info = warehouses[0]
                    self.warehouse_id = self.warehouse_info["id"]
                    self.log(f"✅ Склад: {self.warehouse_info['name']} (ID: {self.warehouse_id})")
                    return True
            
            self.log("❌ Не удалось получить информацию о складе")
            return False
            
        except Exception as e:
            self.log(f"❌ Ошибка получения склада: {e}", "ERROR")
            return False

    def analyze_fully_placed_data(self):
        """Анализ данных из fully-placed API"""
        try:
            self.log("🔍 АНАЛИЗ ДАННЫХ ИЗ fully-placed API...")
            
            response = self.session.get(f"{API_BASE}/operator/cargo/fully-placed")
            if response.status_code != 200:
                self.log(f"❌ Ошибка получения fully-placed: {response.status_code}")
                return None
            
            data = response.json()
            items = data.get("items", [])
            
            self.log(f"📊 Найдено полностью размещенных заявок: {len(items)}")
            
            # Ищем заявку 25082298
            target_application = None
            for item in items:
                if "25082298" in item.get("cargo_number", ""):
                    target_application = item
                    break
            
            if target_application:
                self.log("🎯 НАЙДЕНА ЦЕЛЕВАЯ ЗАЯВКА 25082298:")
                self.log(f"   Номер: {target_application.get('cargo_number')}")
                self.log(f"   Размещающий оператор: {target_application.get('placing_operator')}")
                self.log(f"   warehouse_id: {target_application.get('warehouse_id', 'НЕ УКАЗАН')}")
                
                # Анализ individual_units
                individual_units = target_application.get("individual_units", [])
                self.log(f"   Individual units: {len(individual_units)}")
                
                placed_units = []
                for unit in individual_units:
                    if unit.get("status") == "placed":
                        placed_units.append(unit)
                        self.log(f"      ✅ {unit.get('individual_number')}: {unit.get('placement_info')}")
                
                self.log(f"   📊 ИТОГО РАЗМЕЩЕНО: {len(placed_units)} единиц")
                
                return {
                    "application": target_application,
                    "placed_units": placed_units,
                    "warehouse_id": target_application.get("warehouse_id")
                }
            else:
                self.log("❌ Заявка 25082298 не найдена в fully-placed")
                return None
                
        except Exception as e:
            self.log(f"❌ Ошибка анализа fully-placed: {e}", "ERROR")
            return None

    def test_layout_with_cargo_api(self):
        """Тестирование API layout-with-cargo"""
        try:
            self.log("🔍 ТЕСТИРОВАНИЕ API layout-with-cargo...")
            
            if not self.warehouse_id:
                self.log("❌ warehouse_id не определен")
                return None
            
            response = self.session.get(f"{API_BASE}/warehouses/{self.warehouse_id}/layout-with-cargo")
            
            if response.status_code != 200:
                self.log(f"❌ Ошибка API layout-with-cargo: {response.status_code}")
                return None
            
            data = response.json()
            self.log("✅ API layout-with-cargo доступен")
            
            # Анализ cargo_info
            cargo_info = data.get("cargo_info", [])
            self.log(f"📊 Найдено единиц в cargo_info: {len(cargo_info)}")
            
            # Поиск данных USR648425
            usr_units = []
            for unit in cargo_info:
                placed_by = unit.get("placed_by", "")
                if "Юлдашев" in placed_by or "USR648425" in placed_by:
                    usr_units.append(unit)
            
            self.log(f"🔍 Единиц от USR648425/Юлдашев: {len(usr_units)}")
            
            if usr_units:
                self.log("✅ НАЙДЕНЫ ЕДИНИЦЫ ОТ USR648425:")
                for unit in usr_units[:5]:  # Показываем первые 5
                    self.log(f"   📦 {unit.get('cargo_number')}: {unit.get('cargo_name')}")
                    self.log(f"      Размещен: {unit.get('placed_by')}")
                    self.log(f"      Ячейка: {unit.get('cell_location')}")
            else:
                self.log("❌ ЕДИНИЦЫ ОТ USR648425 НЕ НАЙДЕНЫ в cargo_info")
            
            # Анализ источников данных
            self.analyze_cargo_info_sources(cargo_info)
            
            return {
                "cargo_info": cargo_info,
                "usr_units": usr_units,
                "total_units": len(cargo_info)
            }
            
        except Exception as e:
            self.log(f"❌ Ошибка тестирования layout-with-cargo: {e}", "ERROR")
            return None

    def analyze_cargo_info_sources(self, cargo_info):
        """Анализ источников данных в cargo_info"""
        try:
            self.log("🔍 АНАЛИЗ ИСТОЧНИКОВ ДАННЫХ В cargo_info:")
            
            # Группируем по источникам данных
            sources = {}
            
            for unit in cargo_info:
                # Определяем источник по структуре данных
                if "placement_record_id" in unit:
                    source = "placement_records"
                elif "operator_cargo_id" in unit:
                    source = "operator_cargo"
                elif unit.get("placed_by"):
                    # Если есть placed_by, скорее всего из placement_records
                    source = "placement_records"
                else:
                    source = "unknown"
                
                if source not in sources:
                    sources[source] = []
                sources[source].append(unit)
            
            self.log(f"📊 ИСТОЧНИКИ ДАННЫХ:")
            for source, units in sources.items():
                self.log(f"   {source}: {len(units)} единиц")
                
                # Показываем примеры
                if units:
                    sample = units[0]
                    fields = list(sample.keys())
                    self.log(f"      Поля: {', '.join(fields[:8])}{'...' if len(fields) > 8 else ''}")
            
            # Проверяем, есть ли данные из operator_cargo
            if "operator_cargo" not in sources and "placement_records" in sources:
                self.log("❌ ПРОБЛЕМА: Данные только из placement_records, operator_cargo не обрабатывается!")
            elif "operator_cargo" in sources:
                self.log("✅ Данные из operator_cargo найдены")
            else:
                self.log("⚠️ Источник данных неопределен")
                
        except Exception as e:
            self.log(f"❌ Ошибка анализа источников: {e}", "ERROR")

    def compare_data_sources(self, fully_placed_data, layout_data):
        """Сравнение данных из разных источников"""
        try:
            self.log("🔍 СРАВНЕНИЕ ДАННЫХ ИЗ РАЗНЫХ ИСТОЧНИКОВ:")
            
            if not fully_placed_data or not layout_data:
                self.log("❌ Недостаточно данных для сравнения")
                return
            
            # Данные из fully-placed
            fully_placed_units = len(fully_placed_data["placed_units"])
            fully_placed_warehouse_id = fully_placed_data["warehouse_id"]
            
            # Данные из layout-with-cargo
            layout_units = layout_data["total_units"]
            layout_usr_units = len(layout_data["usr_units"])
            
            self.log(f"📊 СРАВНЕНИЕ:")
            self.log(f"   fully-placed: {fully_placed_units} единиц от USR648425")
            self.log(f"   layout-with-cargo: {layout_usr_units} единиц от USR648425")
            self.log(f"   layout-with-cargo всего: {layout_units} единиц")
            
            # Анализ warehouse_id
            self.log(f"🏢 WAREHOUSE_ID:")
            self.log(f"   fully-placed данные: {fully_placed_warehouse_id}")
            self.log(f"   текущий склад оператора: {self.warehouse_id}")
            
            if fully_placed_warehouse_id != self.warehouse_id:
                self.log("❌ ПРОБЛЕМА: warehouse_id в fully-placed не совпадает с текущим складом!")
                self.log("   Это может быть причиной почему layout-with-cargo не находит данные")
            else:
                self.log("✅ warehouse_id совпадает")
            
            # Выводы
            if fully_placed_units > layout_usr_units:
                self.log("❌ ПРОБЛЕМА: layout-with-cargo находит меньше единиц чем fully-placed")
                self.log("   Возможные причины:")
                self.log("   1. API layout-with-cargo не ищет в operator_cargo коллекции")
                self.log("   2. Фильтр по warehouse_id исключает данные из operator_cargo")
                self.log("   3. Структура данных в operator_cargo не соответствует ожидаемой")
            else:
                self.log("✅ Количество единиц соответствует ожиданиям")
                
        except Exception as e:
            self.log(f"❌ Ошибка сравнения данных: {e}", "ERROR")

    def test_placement_records_api(self):
        """Тестирование placement_records API"""
        try:
            self.log("🔍 ТЕСТИРОВАНИЕ placement_records...")
            
            # Пробуем различные endpoints для placement_records
            endpoints = [
                f"/warehouses/{self.warehouse_id}/placement-records",
                "/operator/placement-records",
                "/placement-records"
            ]
            
            for endpoint in endpoints:
                try:
                    response = self.session.get(f"{API_BASE}{endpoint}")
                    if response.status_code == 200:
                        data = response.json()
                        self.log(f"✅ {endpoint}: найдено {len(data) if isinstance(data, list) else 'неизвестно'} записей")
                        
                        # Ищем записи USR648425
                        if isinstance(data, list):
                            usr_records = [r for r in data if "Юлдашев" in str(r.get("placed_by", ""))]
                            self.log(f"   Записи от USR648425: {len(usr_records)}")
                        
                        return data
                    else:
                        self.log(f"⚠️ {endpoint}: {response.status_code}")
                except:
                    continue
            
            self.log("❌ placement_records API недоступен")
            return None
            
        except Exception as e:
            self.log(f"❌ Ошибка тестирования placement_records: {e}", "ERROR")
            return None

    def generate_diagnosis_report(self, fully_placed_data, layout_data):
        """Генерация диагностического отчета"""
        self.log("\n" + "=" * 80)
        self.log("📊 ДИАГНОСТИЧЕСКИЙ ОТЧЕТ API layout-with-cargo")
        self.log("=" * 80)
        
        # Основные выводы
        if fully_placed_data and layout_data:
            fully_placed_units = len(fully_placed_data["placed_units"])
            layout_usr_units = len(layout_data["usr_units"])
            
            self.log(f"🎯 КЛЮЧЕВЫЕ НАХОДКИ:")
            self.log(f"   ✅ Заявка 25082298 найдена в fully-placed API")
            self.log(f"   ✅ Оператор 'Юлдашев Жасурбек Бахтиёрович' подтвержден")
            self.log(f"   📊 fully-placed показывает: {fully_placed_units} размещенных единиц")
            self.log(f"   📊 layout-with-cargo показывает: {layout_usr_units} единиц от USR648425")
            
            if fully_placed_units > layout_usr_units:
                self.log(f"\n❌ КРИТИЧЕСКАЯ ПРОБЛЕМА ПОДТВЕРЖДЕНА:")
                self.log(f"   API layout-with-cargo НЕ находит все данные оператора USR648425")
                self.log(f"   Недостает: {fully_placed_units - layout_usr_units} единиц")
                
                # Анализ warehouse_id
                fully_placed_warehouse_id = fully_placed_data.get("warehouse_id")
                if fully_placed_warehouse_id != self.warehouse_id:
                    self.log(f"\n🔍 КОРНЕВАЯ ПРИЧИНА:")
                    self.log(f"   warehouse_id в данных: {fully_placed_warehouse_id}")
                    self.log(f"   warehouse_id оператора: {self.warehouse_id}")
                    self.log(f"   ❌ НЕСООТВЕТСТВИЕ warehouse_id!")
                    self.log(f"   API layout-with-cargo фильтрует по warehouse_id оператора")
                    self.log(f"   но данные в operator_cargo имеют другой/отсутствующий warehouse_id")
                else:
                    self.log(f"\n🔍 ДРУГИЕ ВОЗМОЖНЫЕ ПРИЧИНЫ:")
                    self.log(f"   1. API layout-with-cargo не ищет в operator_cargo коллекции")
                    self.log(f"   2. Логика объединения данных из двух источников не реализована")
                    self.log(f"   3. Структура individual_items в operator_cargo отличается")
            else:
                self.log(f"\n✅ ПРОБЛЕМА НЕ ПОДТВЕРЖДЕНА:")
                self.log(f"   layout-with-cargo находит все ожидаемые данные")
        else:
            self.log(f"❌ НЕДОСТАТОЧНО ДАННЫХ ДЛЯ ДИАГНОСТИКИ")
        
        # Рекомендации
        self.log(f"\n💡 РЕКОМЕНДАЦИИ ДЛЯ ИСПРАВЛЕНИЯ:")
        self.log(f"1. Проверить логику API layout-with-cargo:")
        self.log(f"   - Убедиться что ищет в обеих коллекциях (placement_records + operator_cargo)")
        self.log(f"   - Проверить фильтрацию по warehouse_id")
        self.log(f"2. Исправить warehouse_id в operator_cargo записях:")
        self.log(f"   - Установить правильный warehouse_id для записей USR648425")
        self.log(f"   - Или изменить логику фильтрации")
        self.log(f"3. Реализовать объединение данных из двух источников:")
        self.log(f"   - placement_records (текущий источник)")
        self.log(f"   - operator_cargo с is_placed=true (отсутствующий источник)")
        
        self.log("\n" + "=" * 80)

    def run_comprehensive_diagnosis(self):
        """Запуск комплексной диагностики"""
        self.log("🚀 НАЧАЛО ДИАГНОСТИКИ API layout-with-cargo")
        self.log("=" * 80)
        
        # 1. Авторизация
        if not self.authenticate_operator():
            return False
        
        # 2. Получение информации о складе
        if not self.get_warehouse_info():
            return False
        
        # 3. Анализ данных fully-placed
        fully_placed_data = self.analyze_fully_placed_data()
        
        # 4. Тестирование layout-with-cargo
        layout_data = self.test_layout_with_cargo_api()
        
        # 5. Тестирование placement_records
        self.test_placement_records_api()
        
        # 6. Сравнение данных
        self.compare_data_sources(fully_placed_data, layout_data)
        
        # 7. Генерация отчета
        self.generate_diagnosis_report(fully_placed_data, layout_data)
        
        return True

def main():
    """Главная функция"""
    debugger = LayoutWithCargoDebugger()
    
    try:
        success = debugger.run_comprehensive_diagnosis()
        
        if success:
            print("\n✅ Диагностика завершена")
            return 0
        else:
            print("\n❌ Диагностика завершена с ошибками")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Диагностика прервана пользователем")
        return 1
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
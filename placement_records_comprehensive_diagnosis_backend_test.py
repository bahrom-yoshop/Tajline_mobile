#!/usr/bin/env python3
"""
КРИТИЧЕСКАЯ ДИАГНОСТИКА: Полный анализ placement_records для поиска 13 недостающих единиц склада 001
=====================================================================================================

ЦЕЛЬ: Найти и исправить проблему, почему API layout-with-cargo не находит 13 размещенных единиц для склада 001

КРИТИЧЕСКАЯ ДИАГНОСТИКА:
1. Авторизация оператора (+79777888999/warehouse123)
2. Полный анализ placement_records:
   - Проанализировать ВСЕ placement_records в системе
   - Найти записи для заявок: 25082298 (7 единиц), 250101 (2 единицы), 25082235 (4 единиц)
   - Выявить какие warehouse_id используются в реальных данных
   - Определить формат location (Б1-П1-Я7, 001-01-02-002, etc.)
3. Поиск записей для Москвы/001: Найти все записи, связанные со складом 001
4. Исправление логики поиска: Применить правильную логику поиска по найденным паттернам

ПРОБЛЕМА: API возвращает 0 записей вместо ожидаемых 13 размещенных единиц. 
Пользователь видит на фронтенде, но API не находит в базе.

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: 
- Найти все 13 placement_records для склада 001
- Определить правильный warehouse_id для поиска
- Исправить логику синхронизации между фронтендом и API
"""

import requests
import json
import sys
import os
from datetime import datetime
from collections import defaultdict

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-manage-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Конфигурация
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"
TARGET_APPLICATIONS = ["25082298", "250101", "25082235"]
EXPECTED_UNITS = {"25082298": 7, "250101": 2, "25082235": 4}
TOTAL_EXPECTED = 13

class PlacementRecordsDiagnosticTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.test_results = {
            "auth_success": False,
            "placement_records_found": 0,
            "target_applications_found": {},
            "warehouse_001_records": 0,
            "warehouse_patterns": {},
            "location_formats": set(),
            "critical_issues": []
        }
        
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
                    self.test_results["auth_success"] = True
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
    
    def get_all_placement_records(self):
        """Получить ВСЕ placement_records из системы для анализа"""
        try:
            self.log("📊 Получение всех placement_records из системы...")
            
            # Попробуем несколько возможных endpoints
            endpoints_to_try = [
                "/operator/placement-records/all",
                "/admin/placement-records/all", 
                "/placement-records",
                "/operator/placement-progress",
                "/warehouses/placement-records"
            ]
            
            all_records = []
            
            for endpoint in endpoints_to_try:
                try:
                    response = self.session.get(f"{API_BASE}{endpoint}")
                    if response.status_code == 200:
                        data = response.json()
                        self.log(f"✅ Endpoint {endpoint} доступен")
                        
                        # Извлекаем записи в зависимости от структуры ответа
                        if isinstance(data, list):
                            all_records.extend(data)
                        elif isinstance(data, dict):
                            if 'placement_records' in data:
                                all_records.extend(data['placement_records'])
                            elif 'records' in data:
                                all_records.extend(data['records'])
                            elif 'items' in data:
                                all_records.extend(data['items'])
                        
                        self.log(f"📋 Найдено {len(all_records)} записей через {endpoint}")
                        break
                        
                except Exception as e:
                    self.log(f"⚠️ Endpoint {endpoint} недоступен: {str(e)}")
                    continue
            
            if not all_records:
                self.log("❌ Не удалось получить placement_records через стандартные endpoints")
                # Попробуем альтернативный подход через MongoDB API
                return self.get_placement_records_alternative()
            
            self.test_results["placement_records_found"] = len(all_records)
            return all_records
            
        except Exception as e:
            self.log(f"❌ Ошибка получения placement_records: {str(e)}", "ERROR")
            return []
    
    def get_placement_records_alternative(self):
        """Альтернативный способ получения placement_records через другие API"""
        try:
            self.log("🔄 Попытка получить placement_records через альтернативные методы...")
            
            # Попробуем через API layout-with-cargo для всех складов
            warehouses_response = self.session.get(f"{API_BASE}/operator/warehouses")
            if warehouses_response.status_code != 200:
                self.log("❌ Не удалось получить список складов")
                return []
            
            warehouses = warehouses_response.json()
            all_records = []
            
            for warehouse in warehouses:
                warehouse_id = warehouse.get('id')
                warehouse_name = warehouse.get('name', 'Unknown')
                
                try:
                    layout_response = self.session.get(f"{API_BASE}/warehouses/{warehouse_id}/layout-with-cargo")
                    if layout_response.status_code == 200:
                        layout_data = layout_response.json()
                        cargo_info = layout_data.get('cargo_info', [])
                        
                        self.log(f"📦 Склад {warehouse_name}: найдено {len(cargo_info)} размещенных грузов")
                        
                        # Преобразуем cargo_info в формат placement_records
                        for cargo in cargo_info:
                            record = {
                                'warehouse_id': warehouse_id,
                                'warehouse_name': warehouse_name,
                                'cargo_number': cargo.get('cargo_number'),
                                'individual_number': cargo.get('individual_number'),
                                'location': cargo.get('location'),
                                'placed_at': cargo.get('placed_at'),
                                'placed_by': cargo.get('placed_by')
                            }
                            all_records.append(record)
                            
                except Exception as e:
                    self.log(f"⚠️ Ошибка получения layout для склада {warehouse_name}: {str(e)}")
                    continue
            
            self.test_results["placement_records_found"] = len(all_records)
            self.log(f"📊 Всего найдено {len(all_records)} placement records через альтернативный метод")
            return all_records
            
        except Exception as e:
            self.log(f"❌ Ошибка альтернативного получения placement_records: {str(e)}", "ERROR")
            return []
    
    def analyze_placement_records(self, records):
        """Анализ всех placement_records для поиска паттернов"""
        try:
            self.log("🔍 Анализ placement_records...")
            
            # Статистика по заявкам
            application_stats = defaultdict(list)
            warehouse_stats = defaultdict(int)
            location_formats = set()
            warehouse_patterns = defaultdict(set)
            
            for record in records:
                cargo_number = record.get('cargo_number', '')
                individual_number = record.get('individual_number', '')
                warehouse_id = record.get('warehouse_id', '')
                warehouse_name = record.get('warehouse_name', '')
                location = record.get('location', '')
                
                # Анализ заявок
                if cargo_number:
                    application_stats[cargo_number].append(record)
                
                # Анализ складов
                if warehouse_id:
                    warehouse_stats[warehouse_id] += 1
                    warehouse_patterns[warehouse_id].add(warehouse_name)
                
                # Анализ форматов местоположения
                if location:
                    location_formats.add(location)
                    
                    # Определяем тип формата
                    if '-' in location and len(location.split('-')) == 4:
                        # Формат 001-01-02-002
                        self.log(f"📍 Найден формат ID: {location}")
                    elif 'Б' in location and 'П' in location and 'Я' in location:
                        # Формат Б1-П1-Я7
                        self.log(f"📍 Найден формат Б-П-Я: {location}")
            
            # Анализ целевых заявок
            self.log("\n🎯 АНАЛИЗ ЦЕЛЕВЫХ ЗАЯВОК:")
            for app_number in TARGET_APPLICATIONS:
                found_records = application_stats.get(app_number, [])
                expected_count = EXPECTED_UNITS.get(app_number, 0)
                
                self.test_results["target_applications_found"][app_number] = len(found_records)
                
                if found_records:
                    self.log(f"✅ Заявка {app_number}: найдено {len(found_records)} записей (ожидалось {expected_count})")
                    for record in found_records:
                        self.log(f"   - {record.get('individual_number', 'N/A')} в {record.get('location', 'N/A')} (склад: {record.get('warehouse_name', 'N/A')})")
                else:
                    self.log(f"❌ Заявка {app_number}: НЕ НАЙДЕНА (ожидалось {expected_count} записей)")
                    self.test_results["critical_issues"].append(f"Заявка {app_number} не найдена в placement_records")
            
            # Анализ складов
            self.log("\n🏢 АНАЛИЗ СКЛАДОВ:")
            for warehouse_id, count in warehouse_stats.items():
                warehouse_names = list(warehouse_patterns[warehouse_id])
                self.log(f"📦 Склад {warehouse_id}: {count} записей, названия: {warehouse_names}")
                
                # Поиск склада 001
                if any('001' in str(warehouse_id) or 'Москва' in name for name in warehouse_names):
                    self.test_results["warehouse_001_records"] = count
                    self.log(f"🎯 НАЙДЕН СКЛАД 001/МОСКВА: {count} записей")
            
            # Анализ форматов местоположения
            self.log(f"\n📍 НАЙДЕНО {len(location_formats)} УНИКАЛЬНЫХ ФОРМАТОВ МЕСТОПОЛОЖЕНИЯ:")
            for location in sorted(location_formats):
                self.log(f"   - {location}")
                self.test_results["location_formats"].add(location)
            
            self.test_results["warehouse_patterns"] = dict(warehouse_patterns)
            
            return application_stats, warehouse_stats, location_formats
            
        except Exception as e:
            self.log(f"❌ Ошибка анализа placement_records: {str(e)}", "ERROR")
            return {}, {}, set()
    
    def search_warehouse_001_records(self, records):
        """Поиск всех записей, связанных со складом 001/Москва"""
        try:
            self.log("\n🔍 ПОИСК ЗАПИСЕЙ ДЛЯ СКЛАДА 001/МОСКВА...")
            
            moscow_keywords = ['москва', 'moscow', '001']
            found_records = []
            
            for record in records:
                warehouse_id = str(record.get('warehouse_id', '')).lower()
                warehouse_name = str(record.get('warehouse_name', '')).lower()
                location = str(record.get('location', '')).lower()
                
                # Поиск по различным критериям
                if any(keyword in warehouse_id or keyword in warehouse_name or keyword in location 
                       for keyword in moscow_keywords):
                    found_records.append(record)
            
            self.log(f"🎯 НАЙДЕНО {len(found_records)} ЗАПИСЕЙ ДЛЯ СКЛАДА 001/МОСКВА:")
            
            for record in found_records:
                cargo_number = record.get('cargo_number', 'N/A')
                individual_number = record.get('individual_number', 'N/A')
                location = record.get('location', 'N/A')
                warehouse_name = record.get('warehouse_name', 'N/A')
                
                self.log(f"   - {cargo_number}/{individual_number} в {location} (склад: {warehouse_name})")
            
            return found_records
            
        except Exception as e:
            self.log(f"❌ Ошибка поиска записей склада 001: {str(e)}", "ERROR")
            return []
    
    def test_layout_with_cargo_api(self):
        """Тестирование API layout-with-cargo для поиска проблемы"""
        try:
            self.log("\n🧪 ТЕСТИРОВАНИЕ API layout-with-cargo...")
            
            # Получаем список складов
            warehouses_response = self.session.get(f"{API_BASE}/operator/warehouses")
            if warehouses_response.status_code != 200:
                self.log("❌ Не удалось получить список складов")
                return
            
            warehouses = warehouses_response.json()
            
            for warehouse in warehouses:
                warehouse_id = warehouse.get('id')
                warehouse_name = warehouse.get('name', 'Unknown')
                warehouse_id_number = warehouse.get('warehouse_id_number', 'N/A')
                
                self.log(f"\n📦 Тестирование склада: {warehouse_name} (ID: {warehouse_id}, Номер: {warehouse_id_number})")
                
                try:
                    layout_response = self.session.get(f"{API_BASE}/warehouses/{warehouse_id}/layout-with-cargo")
                    
                    if layout_response.status_code == 200:
                        layout_data = layout_response.json()
                        cargo_info = layout_data.get('cargo_info', [])
                        
                        self.log(f"✅ API ответил: найдено {len(cargo_info)} размещенных грузов")
                        
                        # Проверяем наличие целевых заявок
                        target_found = {}
                        for cargo in cargo_info:
                            cargo_number = cargo.get('cargo_number', '')
                            if cargo_number in TARGET_APPLICATIONS:
                                if cargo_number not in target_found:
                                    target_found[cargo_number] = []
                                target_found[cargo_number].append(cargo)
                        
                        if target_found:
                            self.log(f"🎯 НАЙДЕНЫ ЦЕЛЕВЫЕ ЗАЯВКИ в складе {warehouse_name}:")
                            for app_number, cargos in target_found.items():
                                self.log(f"   - {app_number}: {len(cargos)} единиц")
                        
                        # Если это склад с номером 001 или Москва
                        if ('001' in str(warehouse_id_number) or 'москва' in warehouse_name.lower()):
                            self.log(f"🎯 ЭТО СКЛАД 001/МОСКВА! Найдено {len(cargo_info)} записей")
                            if len(cargo_info) == 0:
                                self.test_results["critical_issues"].append(f"API layout-with-cargo возвращает 0 записей для склада 001/Москва")
                    else:
                        self.log(f"❌ Ошибка API: {layout_response.status_code}")
                        
                except Exception as e:
                    self.log(f"❌ Ошибка тестирования склада {warehouse_name}: {str(e)}")
                    continue
                    
        except Exception as e:
            self.log(f"❌ Ошибка тестирования layout-with-cargo API: {str(e)}", "ERROR")
    
    def run_comprehensive_diagnosis(self):
        """Запуск полной диагностики"""
        try:
            self.log("🚀 ЗАПУСК КРИТИЧЕСКОЙ ДИАГНОСТИКИ PLACEMENT RECORDS")
            self.log("=" * 80)
            
            # 1. Авторизация
            if not self.authenticate_operator():
                self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось авторизоваться")
                return False
            
            # 2. Получение всех placement_records
            all_records = self.get_all_placement_records()
            if not all_records:
                self.log("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить placement_records")
                return False
            
            # 3. Анализ записей
            app_stats, warehouse_stats, location_formats = self.analyze_placement_records(all_records)
            
            # 4. Поиск записей склада 001
            moscow_records = self.search_warehouse_001_records(all_records)
            
            # 5. Тестирование API layout-with-cargo
            self.test_layout_with_cargo_api()
            
            # 6. Финальный отчет
            self.generate_final_report()
            
            return True
            
        except Exception as e:
            self.log(f"❌ КРИТИЧЕСКАЯ ОШИБКА диагностики: {str(e)}", "ERROR")
            return False
    
    def generate_final_report(self):
        """Генерация финального отчета диагностики"""
        try:
            self.log("\n" + "=" * 80)
            self.log("📊 ФИНАЛЬНЫЙ ОТЧЕТ ДИАГНОСТИКИ")
            self.log("=" * 80)
            
            # Статистика
            self.log(f"✅ Авторизация: {'УСПЕШНО' if self.test_results['auth_success'] else 'ОШИБКА'}")
            self.log(f"📊 Всего placement_records найдено: {self.test_results['placement_records_found']}")
            self.log(f"🏢 Записей для склада 001: {self.test_results['warehouse_001_records']}")
            
            # Целевые заявки
            self.log(f"\n🎯 ЦЕЛЕВЫЕ ЗАЯВКИ:")
            total_found = 0
            for app_number, expected in EXPECTED_UNITS.items():
                found = self.test_results["target_applications_found"].get(app_number, 0)
                total_found += found
                status = "✅" if found == expected else "❌"
                self.log(f"{status} {app_number}: найдено {found} из {expected} ожидаемых")
            
            self.log(f"\n📈 ОБЩИЙ ИТОГ: найдено {total_found} из {TOTAL_EXPECTED} ожидаемых единиц")
            
            # Критические проблемы
            if self.test_results["critical_issues"]:
                self.log(f"\n🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ ({len(self.test_results['critical_issues'])}):")
                for issue in self.test_results["critical_issues"]:
                    self.log(f"❌ {issue}")
            
            # Форматы местоположения
            if self.test_results["location_formats"]:
                self.log(f"\n📍 НАЙДЕННЫЕ ФОРМАТЫ МЕСТОПОЛОЖЕНИЯ ({len(self.test_results['location_formats'])}):")
                for location_format in sorted(self.test_results["location_formats"]):
                    self.log(f"   - {location_format}")
            
            # Рекомендации
            self.log(f"\n💡 РЕКОМЕНДАЦИИ:")
            if total_found < TOTAL_EXPECTED:
                self.log("🔧 1. Проверить логику поиска placement_records в API")
                self.log("🔧 2. Убедиться что все placement_records сохраняются правильно")
                self.log("🔧 3. Проверить фильтрацию по warehouse_id в базе данных")
            
            if self.test_results['warehouse_001_records'] == 0:
                self.log("🔧 4. Исправить идентификацию склада 001 в системе")
                self.log("🔧 5. Добавить поддержку поиска по номеру склада '001'")
            
            # Успешность диагностики
            success_rate = (total_found / TOTAL_EXPECTED) * 100 if TOTAL_EXPECTED > 0 else 0
            self.log(f"\n📊 УСПЕШНОСТЬ ДИАГНОСТИКИ: {success_rate:.1f}%")
            
            if success_rate < 50:
                self.log("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА ПОДТВЕРЖДЕНА!")
            elif success_rate < 100:
                self.log("⚠️ ЧАСТИЧНАЯ ПРОБЛЕМА ОБНАРУЖЕНА")
            else:
                self.log("✅ ВСЕ ЗАПИСИ НАЙДЕНЫ УСПЕШНО")
                
        except Exception as e:
            self.log(f"❌ Ошибка генерации отчета: {str(e)}", "ERROR")

def main():
    """Главная функция"""
    print("🚀 КРИТИЧЕСКАЯ ДИАГНОСТИКА: Поиск 13 недостающих единиц склада 001")
    print("=" * 80)
    
    tester = PlacementRecordsDiagnosticTester()
    
    try:
        success = tester.run_comprehensive_diagnosis()
        
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
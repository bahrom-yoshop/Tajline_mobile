#!/usr/bin/env python3
"""
ДЕТАЛЬНЫЙ АНАЛИЗ ДАННЫХ individual_items ДЛЯ ЗАЯВКИ 250101
==========================================================

ЦЕЛЬ: Проанализировать структуру данных `individual_items` в ответе API available-for-placement для заявки 250101

ДЕТАЛЬНЫЕ ПРОВЕРКИ:
1. Авторизация оператора склада (+79777888999/warehouse123)
2. Запрос к `/api/operator/cargo/available-for-placement`
3. Найти заявку 250101
4. ДЕТАЛЬНО проанализировать каждый cargo_item:
   - Поля `placed_count` и `quantity` для каждого cargo_item
   - Структуру и содержимое массива `individual_items` для каждого cargo_item
   - Значения `is_placed` для каждого individual_item
   - Соответствие между `placed_count` и количеством individual_items с `is_placed: true`

КРИТИЧЕСКАЯ ПРОВЕРКА: Frontend подсчитывает прогресс на основе 
`individual_items.filter(unit => unit.is_placed === true).length`, 
поэтому нужно убедиться что в `individual_items` правильно установлены флаги `is_placed`.

ПРОБЛЕМА: Backend возвращает `total_placed=2`, но frontend показывает 1/4, 
что означает проблему в данных `individual_items`.
"""

import requests
import json
import sys
from datetime import datetime

# Конфигурация
BACKEND_URL = "https://tajline-manage-1.preview.emergentagent.com/api"
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"
TARGET_APPLICATION = "250101"

class DetailedIndividualItemsAnalyzer:
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
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
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
    
    def get_available_for_placement(self):
        """Получить данные available-for-placement"""
        self.log("📋 Запрос к /api/operator/cargo/available-for-placement...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/available-for-placement")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Получено {len(data)} заявок для размещения")
                return data
            else:
                self.log(f"❌ Ошибка получения данных: {response.status_code} - {response.text}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Исключение при запросе: {e}", "ERROR")
            return None
    
    def find_application_250101(self, applications):
        """Найти заявку 250101 в списке"""
        self.log(f"🔍 Поиск заявки {TARGET_APPLICATION}...")
        
        for app in applications:
            if app.get("cargo_number") == TARGET_APPLICATION:
                self.log(f"✅ Заявка {TARGET_APPLICATION} найдена!")
                return app
        
        self.log(f"❌ Заявка {TARGET_APPLICATION} НЕ найдена в списке", "ERROR")
        return None
    
    def analyze_application_overview(self, application):
        """Анализ общих данных заявки"""
        self.log("📊 АНАЛИЗ ОБЩИХ ДАННЫХ ЗАЯВКИ 250101:")
        self.log("=" * 60)
        
        # Основные поля
        cargo_number = application.get("cargo_number")
        total_placed = application.get("total_placed", 0)
        placement_progress = application.get("placement_progress", "N/A")
        overall_status = application.get("overall_placement_status", "N/A")
        
        self.log(f"📋 Номер заявки: {cargo_number}")
        self.log(f"📊 total_placed: {total_placed}")
        self.log(f"📈 placement_progress: {placement_progress}")
        self.log(f"🎯 overall_placement_status: {overall_status}")
        
        # Анализ cargo_items
        cargo_items = application.get("cargo_items", [])
        self.log(f"📦 Количество cargo_items: {len(cargo_items)}")
        
        return {
            "cargo_number": cargo_number,
            "total_placed": total_placed,
            "placement_progress": placement_progress,
            "overall_status": overall_status,
            "cargo_items_count": len(cargo_items)
        }
    
    def analyze_cargo_item_detailed(self, cargo_item, item_index):
        """Детальный анализ одного cargo_item"""
        self.log(f"\n🔍 ДЕТАЛЬНЫЙ АНАЛИЗ CARGO_ITEM #{item_index + 1}:")
        self.log("-" * 50)
        
        # Основные поля cargo_item
        cargo_name = cargo_item.get("cargo_name", "N/A")
        quantity = cargo_item.get("quantity", 0)
        placed_count = cargo_item.get("placed_count", 0)
        
        self.log(f"📦 Название груза: {cargo_name}")
        self.log(f"🔢 quantity: {quantity}")
        self.log(f"✅ placed_count: {placed_count}")
        
        # Анализ individual_items
        individual_items = cargo_item.get("individual_items", [])
        self.log(f"📋 Количество individual_items: {len(individual_items)}")
        
        if not individual_items:
            self.log("⚠️ ПРОБЛЕМА: individual_items пустой!", "WARNING")
            return {
                "cargo_name": cargo_name,
                "quantity": quantity,
                "placed_count": placed_count,
                "individual_items_count": 0,
                "placed_items_count": 0,
                "consistency_check": False,
                "issues": ["individual_items пустой"]
            }
        
        # Детальный анализ каждого individual_item
        placed_items_count = 0
        issues = []
        
        self.log("\n📋 АНАЛИЗ КАЖДОГО INDIVIDUAL_ITEM:")
        for i, item in enumerate(individual_items):
            individual_number = item.get("individual_number", "N/A")
            is_placed = item.get("is_placed", False)
            placement_info = item.get("placement_info", "N/A")
            
            status_icon = "✅" if is_placed else "⏳"
            self.log(f"  {status_icon} {individual_number}: is_placed={is_placed}, placement_info='{placement_info}'")
            
            if is_placed:
                placed_items_count += 1
        
        # Проверка консистентности
        consistency_check = (placed_count == placed_items_count)
        
        self.log(f"\n🔍 ПРОВЕРКА КОНСИСТЕНТНОСТИ:")
        self.log(f"  placed_count (из cargo_item): {placed_count}")
        self.log(f"  Фактически размещенных (is_placed=true): {placed_items_count}")
        self.log(f"  Консистентность: {'✅ ДА' if consistency_check else '❌ НЕТ'}")
        
        if not consistency_check:
            issues.append(f"placed_count ({placed_count}) != фактически размещенных ({placed_items_count})")
        
        return {
            "cargo_name": cargo_name,
            "quantity": quantity,
            "placed_count": placed_count,
            "individual_items_count": len(individual_items),
            "placed_items_count": placed_items_count,
            "consistency_check": consistency_check,
            "issues": issues,
            "individual_items_details": [
                {
                    "individual_number": item.get("individual_number"),
                    "is_placed": item.get("is_placed", False),
                    "placement_info": item.get("placement_info")
                }
                for item in individual_items
            ]
        }
    
    def analyze_frontend_calculation(self, application):
        """Анализ того, как frontend будет подсчитывать прогресс"""
        self.log("\n🖥️ АНАЛИЗ РАСЧЕТА FRONTEND:")
        self.log("=" * 60)
        
        cargo_items = application.get("cargo_items", [])
        
        # Симуляция frontend расчета
        total_individual_items = 0
        total_placed_frontend = 0
        
        for cargo_item in cargo_items:
            individual_items = cargo_item.get("individual_items", [])
            total_individual_items += len(individual_items)
            
            # Frontend логика: individual_items.filter(unit => unit.is_placed === true).length
            placed_in_this_item = sum(1 for item in individual_items if item.get("is_placed") == True)
            total_placed_frontend += placed_in_this_item
        
        self.log(f"📊 Общее количество individual_items: {total_individual_items}")
        self.log(f"✅ Frontend подсчет размещенных: {total_placed_frontend}")
        self.log(f"📈 Frontend прогресс: {total_placed_frontend}/{total_individual_items}")
        
        # Сравнение с backend данными
        backend_total_placed = application.get("total_placed", 0)
        backend_progress = application.get("placement_progress", "N/A")
        
        self.log(f"\n🔍 СРАВНЕНИЕ BACKEND vs FRONTEND:")
        self.log(f"  Backend total_placed: {backend_total_placed}")
        self.log(f"  Frontend расчет: {total_placed_frontend}")
        self.log(f"  Backend progress: {backend_progress}")
        self.log(f"  Frontend progress: {total_placed_frontend}/{total_individual_items}")
        
        consistency = (backend_total_placed == total_placed_frontend)
        self.log(f"  Консистентность: {'✅ ДА' if consistency else '❌ НЕТ'}")
        
        return {
            "total_individual_items": total_individual_items,
            "frontend_placed_count": total_placed_frontend,
            "backend_placed_count": backend_total_placed,
            "frontend_progress": f"{total_placed_frontend}/{total_individual_items}",
            "backend_progress": backend_progress,
            "consistency": consistency
        }
    
    def generate_detailed_report(self, application, cargo_items_analysis, frontend_analysis):
        """Генерация детального отчета"""
        self.log("\n📋 ДЕТАЛЬНЫЙ ОТЧЕТ АНАЛИЗА:")
        self.log("=" * 80)
        
        # Заголовок
        self.log(f"🎯 ЗАЯВКА: {application.get('cargo_number')}")
        self.log(f"📅 Время анализа: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Общие данные
        self.log(f"\n📊 ОБЩИЕ ДАННЫЕ:")
        self.log(f"  total_placed (backend): {application.get('total_placed')}")
        self.log(f"  placement_progress (backend): {application.get('placement_progress')}")
        self.log(f"  overall_placement_status: {application.get('overall_placement_status')}")
        
        # Анализ по cargo_items
        self.log(f"\n📦 АНАЛИЗ CARGO_ITEMS ({len(cargo_items_analysis)} шт.):")
        for i, analysis in enumerate(cargo_items_analysis):
            self.log(f"  Cargo Item #{i+1}: {analysis['cargo_name']}")
            self.log(f"    quantity: {analysis['quantity']}")
            self.log(f"    placed_count: {analysis['placed_count']}")
            self.log(f"    individual_items: {analysis['individual_items_count']}")
            self.log(f"    фактически размещено: {analysis['placed_items_count']}")
            self.log(f"    консистентность: {'✅' if analysis['consistency_check'] else '❌'}")
            
            if analysis['issues']:
                self.log(f"    ⚠️ Проблемы: {', '.join(analysis['issues'])}")
        
        # Frontend анализ
        self.log(f"\n🖥️ FRONTEND АНАЛИЗ:")
        self.log(f"  Общее количество individual_items: {frontend_analysis['total_individual_items']}")
        self.log(f"  Frontend подсчет размещенных: {frontend_analysis['frontend_placed_count']}")
        self.log(f"  Backend подсчет размещенных: {frontend_analysis['backend_placed_count']}")
        self.log(f"  Frontend прогресс: {frontend_analysis['frontend_progress']}")
        self.log(f"  Backend прогресс: {frontend_analysis['backend_progress']}")
        self.log(f"  Консистентность: {'✅' if frontend_analysis['consistency'] else '❌'}")
        
        # Выводы
        self.log(f"\n🎯 КРИТИЧЕСКИЕ ВЫВОДЫ:")
        
        if frontend_analysis['consistency']:
            self.log("✅ ДАННЫЕ КОНСИСТЕНТНЫ: Backend и Frontend показывают одинаковые результаты")
        else:
            self.log("❌ НАЙДЕНА ПРОБЛЕМА: Расхождение между Backend и Frontend данными")
            self.log(f"   Backend возвращает: {frontend_analysis['backend_placed_count']} размещенных")
            self.log(f"   Frontend подсчитает: {frontend_analysis['frontend_placed_count']} размещенных")
            self.log("   Это объясняет почему пользователь видит разные данные!")
        
        # Проблемы в cargo_items
        total_issues = sum(len(analysis['issues']) for analysis in cargo_items_analysis)
        if total_issues > 0:
            self.log(f"⚠️ НАЙДЕНО {total_issues} ПРОБЛЕМ В CARGO_ITEMS:")
            for i, analysis in enumerate(cargo_items_analysis):
                if analysis['issues']:
                    self.log(f"   Cargo Item #{i+1} ({analysis['cargo_name']}): {', '.join(analysis['issues'])}")
        
        return {
            "application_number": application.get('cargo_number'),
            "analysis_timestamp": datetime.now().isoformat(),
            "backend_data": {
                "total_placed": application.get('total_placed'),
                "placement_progress": application.get('placement_progress'),
                "overall_status": application.get('overall_placement_status')
            },
            "cargo_items_analysis": cargo_items_analysis,
            "frontend_analysis": frontend_analysis,
            "critical_issues_found": not frontend_analysis['consistency'] or total_issues > 0,
            "total_issues": total_issues
        }
    
    def run_detailed_analysis(self):
        """Запуск детального анализа"""
        self.log("🚀 ЗАПУСК ДЕТАЛЬНОГО АНАЛИЗА individual_items ДЛЯ ЗАЯВКИ 250101")
        self.log("=" * 80)
        
        # 1. Авторизация
        if not self.authenticate_warehouse_operator():
            return False
        
        # 2. Получение данных available-for-placement
        applications = self.get_available_for_placement()
        if not applications:
            return False
        
        # 3. Поиск заявки 250101
        application = self.find_application_250101(applications)
        if not application:
            return False
        
        # 4. Анализ общих данных заявки
        overview = self.analyze_application_overview(application)
        
        # 5. Детальный анализ каждого cargo_item
        cargo_items = application.get("cargo_items", [])
        cargo_items_analysis = []
        
        for i, cargo_item in enumerate(cargo_items):
            analysis = self.analyze_cargo_item_detailed(cargo_item, i)
            cargo_items_analysis.append(analysis)
        
        # 6. Анализ frontend расчета
        frontend_analysis = self.analyze_frontend_calculation(application)
        
        # 7. Генерация детального отчета
        report = self.generate_detailed_report(application, cargo_items_analysis, frontend_analysis)
        
        # 8. Финальные выводы
        self.log("\n🎉 АНАЛИЗ ЗАВЕРШЕН!")
        if report['critical_issues_found']:
            self.log("❌ НАЙДЕНЫ КРИТИЧЕСКИЕ ПРОБЛЕМЫ В ДАННЫХ!")
            return False
        else:
            self.log("✅ ДАННЫЕ КОРРЕКТНЫ, ПРОБЛЕМ НЕ ОБНАРУЖЕНО")
            return True

def main():
    """Главная функция"""
    analyzer = DetailedIndividualItemsAnalyzer()
    
    try:
        success = analyzer.run_detailed_analysis()
        
        if success:
            print("\n" + "="*80)
            print("✅ ДЕТАЛЬНЫЙ АНАЛИЗ ЗАВЕРШЕН УСПЕШНО")
            print("📋 Все данные individual_items корректны")
            print("🎯 Проблема НЕ в структуре данных backend")
            sys.exit(0)
        else:
            print("\n" + "="*80)
            print("❌ ОБНАРУЖЕНЫ КРИТИЧЕСКИЕ ПРОБЛЕМЫ")
            print("🔍 Требуется исправление данных individual_items")
            print("⚠️ Проблема в синхронизации backend данных")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Анализ прерван пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
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
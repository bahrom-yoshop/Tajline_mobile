#!/usr/bin/env python3
"""
ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ СИНХРОНИЗАЦИИ placed_count С is_placed ФЛАГАМИ
====================================================================

ЦЕЛЬ: Убедиться что после исправления backend возвращает консистентные данные 
где `placed_count` соответствует количеству `individual_items` с `is_placed=true`

КРИТИЧЕСКИЕ ПРОВЕРКИ:
1. Авторизация оператора склада (+79777888999/warehouse123)
2. Запрос к `/api/operator/cargo/available-for-placement`
3. Найти заявку 250101
4. ГЛАВНАЯ ПРОВЕРКА: Для каждого cargo_item проверить:
   - `placed_count` должен равняться `individual_items.filter(item => item.is_placed === true).length`
   - Больше не должно быть расхождений между backend подсчетом и frontend подсчетом
5. Убедиться что `total_placed` для всей заявки соответствует фактическому количеству размещенных единиц

ИСПРАВЛЕНИЕ: Добавлена логика синхронизации, которая автоматически исправляет 
`placed_count` на основе фактических `is_placed` флагов в `individual_items`.

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: 
- Консистентные данные между `placed_count` и `individual_items`
- Frontend и backend должны показывать одинаковый прогресс размещения
- Логи должны показать исправления если были расхождения
"""

import requests
import json
import sys
import os
from datetime import datetime

# Получаем URL backend из переменной окружения
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-manage-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Конфигурация
WAREHOUSE_OPERATOR_PHONE = "+79777888999"
WAREHOUSE_OPERATOR_PASSWORD = "warehouse123"
TARGET_APPLICATION = "250101"

class PlacedCountSynchronizationTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_info = None
        self.test_results = {
            "auth_success": False,
            "api_accessible": False,
            "application_found": False,
            "synchronization_correct": False,
            "total_issues_found": 0,
            "detailed_results": []
        }
        
    def log(self, message, level="INFO"):
        """Логирование с временной меткой"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def authenticate_warehouse_operator(self):
        """Авторизация оператора склада"""
        self.log("🔐 Авторизация оператора склада...")
        
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json={
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
                self.test_results["auth_success"] = True
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
            response = self.session.get(f"{API_BASE}/operator/cargo/available-for-placement")
            
            if response.status_code == 200:
                data = response.json()
                items = data if isinstance(data, list) else data.get("items", [])
                self.log(f"✅ Получено {len(items)} заявок для размещения")
                self.test_results["api_accessible"] = True
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
        
        # Проверяем структуру ответа
        if isinstance(applications, dict):
            # Если это объект с полями, ищем в items или аналогичном поле
            if 'items' in applications:
                applications = applications['items']
            elif 'data' in applications:
                applications = applications['data']
            else:
                # Если это единичный объект, проверяем его
                if applications.get("cargo_number") == TARGET_APPLICATION:
                    self.log(f"✅ Заявка {TARGET_APPLICATION} найдена!")
                    self.test_results["application_found"] = True
                    return applications
                else:
                    self.log(f"❌ Заявка {TARGET_APPLICATION} НЕ найдена", "ERROR")
                    return None
        
        # Если это список
        if isinstance(applications, list):
            for app in applications:
                if isinstance(app, dict) and app.get("cargo_number") == TARGET_APPLICATION:
                    self.log(f"✅ Заявка {TARGET_APPLICATION} найдена!")
                    self.test_results["application_found"] = True
                    return app
        
        self.log(f"❌ Заявка {TARGET_APPLICATION} НЕ найдена в списке", "ERROR")
        self.log(f"🔍 Структура ответа: {type(applications)}")
        if isinstance(applications, list) and len(applications) > 0:
            self.log(f"🔍 Первый элемент: {type(applications[0])}")
            if isinstance(applications[0], dict):
                self.log(f"🔍 Ключи первого элемента: {list(applications[0].keys())}")
        return None
    
    def test_placed_count_synchronization(self, application):
        """Главная проверка синхронизации placed_count с is_placed флагами"""
        self.log("\n🎯 ГЛАВНАЯ ПРОВЕРКА: СИНХРОНИЗАЦИЯ placed_count С is_placed ФЛАГАМИ")
        self.log("=" * 80)
        
        # Основные поля заявки
        cargo_number = application.get("cargo_number")
        total_placed = application.get("total_placed", 0)
        placement_progress = application.get("placement_progress", "N/A")
        overall_status = application.get("overall_placement_status", "N/A")
        
        self.log(f"📋 Заявка: {cargo_number}")
        self.log(f"📊 Backend total_placed: {total_placed}")
        self.log(f"📈 Backend placement_progress: {placement_progress}")
        self.log(f"🎯 Backend overall_placement_status: {overall_status}")
        
        # Анализ cargo_items
        cargo_items = application.get("cargo_items", [])
        self.log(f"📦 Количество cargo_items: {len(cargo_items)}")
        
        if not cargo_items:
            self.log("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: cargo_items пустой!", "ERROR")
            return False
        
        # Детальная проверка каждого cargo_item
        total_frontend_placed = 0
        total_individual_items = 0
        issues_found = []
        
        for i, cargo_item in enumerate(cargo_items):
            self.log(f"\n🔍 ПРОВЕРКА CARGO_ITEM #{i + 1}:")
            self.log("-" * 50)
            
            cargo_name = cargo_item.get("cargo_name", "N/A")
            quantity = cargo_item.get("quantity", 0)
            placed_count = cargo_item.get("placed_count", 0)
            individual_items = cargo_item.get("individual_items", [])
            
            self.log(f"📦 Название груза: {cargo_name}")
            self.log(f"🔢 quantity: {quantity}")
            self.log(f"✅ placed_count (backend): {placed_count}")
            self.log(f"📋 individual_items: {len(individual_items)}")
            
            if not individual_items:
                self.log("⚠️ ПРОБЛЕМА: individual_items пустой!", "WARNING")
                issues_found.append(f"Cargo Item #{i+1} ({cargo_name}): individual_items пустой")
                continue
            
            # Подсчет фактически размещенных единиц (frontend логика)
            frontend_placed_count = 0
            total_individual_items += len(individual_items)
            
            self.log("\n📋 АНАЛИЗ КАЖДОГО INDIVIDUAL_ITEM:")
            for j, item in enumerate(individual_items):
                individual_number = item.get("individual_number", "N/A")
                is_placed = item.get("is_placed", False)
                placement_info = item.get("placement_info", "N/A")
                
                status_icon = "✅" if is_placed else "⏳"
                self.log(f"  {status_icon} {individual_number}: is_placed={is_placed}")
                
                if is_placed:
                    frontend_placed_count += 1
            
            total_frontend_placed += frontend_placed_count
            
            # КРИТИЧЕСКАЯ ПРОВЕРКА СИНХРОНИЗАЦИИ
            self.log(f"\n🎯 ПРОВЕРКА СИНХРОНИЗАЦИИ:")
            self.log(f"  Backend placed_count: {placed_count}")
            self.log(f"  Frontend подсчет (is_placed=true): {frontend_placed_count}")
            
            if placed_count == frontend_placed_count:
                self.log(f"  ✅ СИНХРОНИЗАЦИЯ КОРРЕКТНА")
            else:
                self.log(f"  ❌ РАСХОЖДЕНИЕ НАЙДЕНО!")
                issue = f"Cargo Item #{i+1} ({cargo_name}): placed_count ({placed_count}) != фактически размещенных ({frontend_placed_count})"
                issues_found.append(issue)
                self.log(f"     {issue}")
        
        # Общая проверка total_placed
        self.log(f"\n🔍 ОБЩАЯ ПРОВЕРКА total_placed:")
        self.log(f"  Backend total_placed: {total_placed}")
        self.log(f"  Frontend общий подсчет: {total_frontend_placed}")
        self.log(f"  Общее количество individual_items: {total_individual_items}")
        
        total_placed_correct = (total_placed == total_frontend_placed)
        if total_placed_correct:
            self.log(f"  ✅ ОБЩАЯ СИНХРОНИЗАЦИЯ КОРРЕКТНА")
        else:
            self.log(f"  ❌ ОБЩЕЕ РАСХОЖДЕНИЕ НАЙДЕНО!")
            issues_found.append(f"Общее расхождение: total_placed ({total_placed}) != frontend подсчет ({total_frontend_placed})")
        
        # Сохранение результатов
        self.test_results["total_issues_found"] = len(issues_found)
        self.test_results["synchronization_correct"] = (len(issues_found) == 0)
        self.test_results["detailed_results"] = {
            "backend_total_placed": total_placed,
            "frontend_total_placed": total_frontend_placed,
            "total_individual_items": total_individual_items,
            "backend_progress": placement_progress,
            "frontend_progress": f"{total_frontend_placed}/{total_individual_items}",
            "issues_found": issues_found
        }
        
        return len(issues_found) == 0
    
    def generate_final_report(self):
        """Генерация финального отчета"""
        self.log("\n📋 ФИНАЛЬНЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ:")
        self.log("=" * 80)
        
        # Заголовок
        self.log(f"🎯 ТЕСТИРОВАНИЕ СИНХРОНИЗАЦИИ placed_count С is_placed ФЛАГАМИ")
        self.log(f"📅 Время тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"🎯 Целевая заявка: {TARGET_APPLICATION}")
        
        # Результаты по этапам
        self.log(f"\n📊 РЕЗУЛЬТАТЫ ПО ЭТАПАМ:")
        self.log(f"  1. ✅ Авторизация оператора склада: {'✅ УСПЕШНО' if self.test_results['auth_success'] else '❌ НЕУДАЧНО'}")
        self.log(f"  2. ✅ Доступ к API available-for-placement: {'✅ УСПЕШНО' if self.test_results['api_accessible'] else '❌ НЕУДАЧНО'}")
        self.log(f"  3. ✅ Поиск заявки {TARGET_APPLICATION}: {'✅ НАЙДЕНА' if self.test_results['application_found'] else '❌ НЕ НАЙДЕНА'}")
        self.log(f"  4. 🎯 Синхронизация placed_count: {'✅ КОРРЕКТНА' if self.test_results['synchronization_correct'] else '❌ ПРОБЛЕМЫ НАЙДЕНЫ'}")
        
        # Детальные результаты
        if self.test_results["detailed_results"]:
            details = self.test_results["detailed_results"]
            self.log(f"\n📊 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
            self.log(f"  Backend total_placed: {details['backend_total_placed']}")
            self.log(f"  Frontend подсчет: {details['frontend_total_placed']}")
            self.log(f"  Общее количество individual_items: {details['total_individual_items']}")
            self.log(f"  Backend progress: {details['backend_progress']}")
            self.log(f"  Frontend progress: {details['frontend_progress']}")
            
            if details['issues_found']:
                self.log(f"\n⚠️ НАЙДЕННЫЕ ПРОБЛЕМЫ ({len(details['issues_found'])} шт.):")
                for i, issue in enumerate(details['issues_found'], 1):
                    self.log(f"  {i}. {issue}")
        
        # Финальный вывод
        self.log(f"\n🎯 ФИНАЛЬНЫЙ РЕЗУЛЬТАТ:")
        if self.test_results["synchronization_correct"]:
            self.log("✅ СИНХРОНИЗАЦИЯ placed_count С is_placed ФЛАГАМИ РАБОТАЕТ КОРРЕКТНО!")
            self.log("🎉 Backend и Frontend показывают консистентные данные")
            self.log("📊 Исправление синхронизации успешно применено")
        else:
            self.log("❌ НАЙДЕНЫ ПРОБЛЕМЫ СИНХРОНИЗАЦИИ!")
            self.log(f"🔍 Обнаружено {self.test_results['total_issues_found']} проблем")
            self.log("⚠️ Требуется дополнительное исправление логики синхронизации")
        
        return self.test_results["synchronization_correct"]
    
    def run_synchronization_test(self):
        """Запуск полного теста синхронизации"""
        self.log("🚀 ЗАПУСК ФИНАЛЬНОГО ТЕСТИРОВАНИЯ СИНХРОНИЗАЦИИ placed_count")
        self.log("=" * 80)
        
        # 1. Авторизация
        if not self.authenticate_warehouse_operator():
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Не удалось авторизоваться", "ERROR")
            return False
        
        # 2. Получение данных available-for-placement
        applications = self.get_available_for_placement()
        if not applications:
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Не удалось получить данные API", "ERROR")
            return False
        
        # 3. Поиск заявки 250101
        application = self.find_application_250101(applications)
        if not application:
            self.log("❌ ТЕСТИРОВАНИЕ ПРЕРВАНО: Заявка 250101 не найдена", "ERROR")
            return False
        
        # 4. Главная проверка синхронизации
        synchronization_success = self.test_placed_count_synchronization(application)
        
        # 5. Генерация финального отчета
        final_success = self.generate_final_report()
        
        return final_success

def main():
    """Главная функция"""
    tester = PlacedCountSynchronizationTester()
    
    try:
        success = tester.run_synchronization_test()
        
        if success:
            print("\n" + "="*80)
            print("🎉 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            print("✅ Синхронизация placed_count с is_placed флагами работает корректно")
            print("📊 Backend и Frontend показывают консистентные данные")
            print("🎯 Исправление синхронизации успешно применено")
            sys.exit(0)
        else:
            print("\n" + "="*80)
            print("❌ ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ НЕ ПРОЙДЕНО!")
            print("🔍 Найдены проблемы синхронизации placed_count с is_placed флагами")
            print("⚠️ Требуется дополнительное исправление логики синхронизации")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
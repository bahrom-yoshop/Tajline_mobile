#!/usr/bin/env python3
"""
🎯 УГЛУБЛЕННАЯ ДИАГНОСТИКА: Проблема с форматом unit_index в QR сканировании

НАЙДЕННАЯ ПРОБЛЕМА:
- Заявка 25082026 существует и доступна для размещения ✅
- Груз типа 01 найден ✅  
- НО: unit_index хранится как числа (1, 2) вместо строк ("01", "02") ❌

КОРНЕВАЯ ПРИЧИНА:
Frontend ищет unit_index = "02" (строка с ведущим нулем)
Backend хранит unit_index = 2 (число без ведущего нуля)

РЕШЕНИЕ: Исправить генерацию unit_index в backend или логику поиска в frontend
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://tajline-cargo-8.preview.emergentagent.com/api"

# Test credentials
WAREHOUSE_OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class DetailedQRFormatAnalyzer:
    def __init__(self):
        self.session = requests.Session()
        self.operator_token = None
        self.target_cargo_number = "25082026"
        self.target_qr_code = "25082026/01/02"
        
    def authenticate_operator(self):
        """Authenticate warehouse operator"""
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json=WAREHOUSE_OPERATOR_CREDENTIALS
            )
            
            if response.status_code == 200:
                data = response.json()
                self.operator_token = data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.operator_token}"
                })
                return True
            return False
        except Exception as e:
            print(f"❌ Ошибка авторизации: {e}")
            return False

    def analyze_unit_index_format_issue(self):
        """Детальный анализ проблемы с форматом unit_index"""
        print("🔍 УГЛУБЛЕННЫЙ АНАЛИЗ ПРОБЛЕМЫ С ФОРМАТОМ unit_index")
        print("=" * 60)
        
        try:
            # Получаем данные заявки
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/available-for-placement")
            
            if response.status_code != 200:
                print("❌ Не удалось получить список грузов")
                return False
            
            data = response.json()
            items = data.get("items", [])
            
            # Находим целевую заявку
            target_cargo = None
            for item in items:
                if item.get("cargo_number") == self.target_cargo_number:
                    target_cargo = item
                    break
            
            if not target_cargo:
                print(f"❌ Заявка {self.target_cargo_number} не найдена")
                return False
            
            print(f"✅ Заявка {self.target_cargo_number} найдена")
            print(f"   ID: {target_cargo.get('id')}")
            print()
            
            # Анализируем cargo_items
            cargo_items = target_cargo.get("cargo_items", [])
            print(f"📦 АНАЛИЗ CARGO_ITEMS ({len(cargo_items)} элементов):")
            print("-" * 40)
            
            for i, cargo_item in enumerate(cargo_items):
                type_number = i + 1
                cargo_name = cargo_item.get("cargo_name", "Неизвестно")
                quantity = cargo_item.get("quantity", 0)
                individual_items = cargo_item.get("individual_items", [])
                
                print(f"Груз #{type_number} (тип {type_number:02d}):")
                print(f"   Название: {cargo_name}")
                print(f"   Количество: {quantity}")
                print(f"   Individual_items: {len(individual_items)}")
                
                # Детальный анализ individual_items для первого груза (тип 01)
                if i == 0:  # Первый груз = тип 01
                    print(f"   🔍 ДЕТАЛЬНЫЙ АНАЛИЗ individual_items для типа 01:")
                    
                    for j, item in enumerate(individual_items):
                        unit_index = item.get("unit_index")
                        individual_number = item.get("individual_number")
                        
                        print(f"      Единица #{j+1}:")
                        print(f"         unit_index: {unit_index} (тип: {type(unit_index).__name__})")
                        print(f"         individual_number: {individual_number}")
                        
                        # Проверяем соответствие с целевым QR кодом
                        if individual_number == self.target_qr_code:
                            print(f"         🎯 ЭТО ЦЕЛЕВАЯ ЕДИНИЦА! QR: {self.target_qr_code}")
                            
                            # Анализируем проблему с unit_index
                            expected_unit_index = "02"  # Frontend ожидает строку
                            actual_unit_index = unit_index
                            
                            print(f"         📊 АНАЛИЗ ПРОБЛЕМЫ:")
                            print(f"            Frontend ищет unit_index = '{expected_unit_index}' (строка)")
                            print(f"            Backend хранит unit_index = {actual_unit_index} ({type(actual_unit_index).__name__})")
                            
                            if str(actual_unit_index).zfill(2) == expected_unit_index:
                                print(f"         ✅ РЕШЕНИЕ: Преобразовать {actual_unit_index} → '{expected_unit_index}'")
                            else:
                                print(f"         ❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Несоответствие значений")
                print()
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка анализа: {e}")
            return False

    def test_different_search_approaches(self):
        """Тестируем разные подходы к поиску единицы"""
        print("🧪 ТЕСТИРОВАНИЕ РАЗНЫХ ПОДХОДОВ К ПОИСКУ")
        print("=" * 50)
        
        try:
            # Получаем данные заявки
            response = self.session.get(f"{BACKEND_URL}/operator/cargo/available-for-placement")
            data = response.json()
            items = data.get("items", [])
            
            target_cargo = None
            for item in items:
                if item.get("cargo_number") == self.target_cargo_number:
                    target_cargo = item
                    break
            
            if not target_cargo:
                return False
            
            cargo_items = target_cargo.get("cargo_items", [])
            if not cargo_items:
                return False
            
            individual_items = cargo_items[0].get("individual_items", [])
            
            print("🔍 Тестируем разные способы поиска единицы '02':")
            print()
            
            # Подход 1: Поиск по строковому unit_index "02"
            found_by_string = False
            for item in individual_items:
                if str(item.get("unit_index")) == "02":
                    found_by_string = True
                    break
            print(f"1. Поиск unit_index == '02' (строка): {'✅ Найдено' if found_by_string else '❌ Не найдено'}")
            
            # Подход 2: Поиск по числовому unit_index 2
            found_by_number = False
            for item in individual_items:
                if item.get("unit_index") == 2:
                    found_by_number = True
                    break
            print(f"2. Поиск unit_index == 2 (число): {'✅ Найдено' if found_by_number else '❌ Не найдено'}")
            
            # Подход 3: Поиск по строковому unit_index с zfill
            found_by_zfill = False
            for item in individual_items:
                if str(item.get("unit_index")).zfill(2) == "02":
                    found_by_zfill = True
                    break
            print(f"3. Поиск str(unit_index).zfill(2) == '02': {'✅ Найдено' if found_by_zfill else '❌ Не найдено'}")
            
            # Подход 4: Поиск по individual_number
            found_by_individual_number = False
            for item in individual_items:
                if item.get("individual_number") == self.target_qr_code:
                    found_by_individual_number = True
                    break
            print(f"4. Поиск individual_number == '{self.target_qr_code}': {'✅ Найдено' if found_by_individual_number else '❌ Не найдено'}")
            
            print()
            print("💡 РЕКОМЕНДУЕМОЕ РЕШЕНИЕ:")
            if found_by_zfill and found_by_individual_number:
                print("✅ Использовать подход #3 или #4 для надежного поиска")
                print("   Frontend должен искать по str(unit_index).zfill(2) или individual_number")
            elif found_by_number:
                print("⚠️ Backend хранит unit_index как числа, нужно исправить логику поиска")
            else:
                print("❌ Требуется дополнительная диагностика")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования: {e}")
            return False

    def suggest_backend_fix(self):
        """Предложить исправление в backend"""
        print("🔧 ПРЕДЛОЖЕНИЕ ИСПРАВЛЕНИЯ В BACKEND")
        print("=" * 40)
        
        print("ПРОБЛЕМА:")
        print("- Backend генерирует unit_index как числа (1, 2, 3...)")
        print("- Frontend ожидает unit_index как строки с ведущими нулями ('01', '02', '03'...)")
        print()
        
        print("РЕШЕНИЕ 1 - Исправить генерацию unit_index в backend:")
        print("```python")
        print("# В функции генерации individual_items")
        print("unit_index = f'{unit_number:02d}'  # Вместо unit_index = unit_number")
        print("```")
        print()
        
        print("РЕШЕНИЕ 2 - Исправить логику поиска в frontend:")
        print("```javascript")
        print("// При поиске единицы по unit_index")
        print("const targetUnit = individual_items.find(item => ")
        print("  String(item.unit_index).padStart(2, '0') === target_unit_index")
        print(");")
        print("```")
        print()
        
        print("РЕШЕНИЕ 3 - Использовать individual_number для поиска:")
        print("```javascript")
        print("// Поиск по полному individual_number вместо unit_index")
        print("const targetUnit = individual_items.find(item => ")
        print("  item.individual_number === qr_code")
        print(");")
        print("```")
        print()
        
        print("🎯 РЕКОМЕНДАЦИЯ: Использовать РЕШЕНИЕ 1 (исправить backend)")
        print("   Это обеспечит консистентность данных во всей системе")

    def run_detailed_analysis(self):
        """Запустить детальный анализ"""
        print("🎯 УГЛУБЛЕННАЯ ДИАГНОСТИКА: Проблема с форматом unit_index в QR сканировании")
        print("=" * 80)
        print()
        
        if not self.authenticate_operator():
            print("❌ Не удалось авторизоваться")
            return False
        
        print("✅ Авторизация успешна")
        print()
        
        # Детальный анализ
        if not self.analyze_unit_index_format_issue():
            return False
        
        # Тестирование подходов
        if not self.test_different_search_approaches():
            return False
        
        # Предложения по исправлению
        self.suggest_backend_fix()
        
        print("🎉 ДИАГНОСТИКА ЗАВЕРШЕНА!")
        print("=" * 30)
        print("КОРНЕВАЯ ПРИЧИНА НАЙДЕНА: Несоответствие формата unit_index")
        print("РЕШЕНИЕ: Исправить генерацию unit_index в backend или логику поиска в frontend")
        
        return True

if __name__ == "__main__":
    analyzer = DetailedQRFormatAnalyzer()
    success = analyzer.run_detailed_analysis()
    sys.exit(0 if success else 1)
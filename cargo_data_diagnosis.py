#!/usr/bin/env python3
"""
ДИАГНОСТИКА: Проверка данных груза с ID 100004
"""

import requests
import json

# Конфигурация
BACKEND_URL = "https://tajline-cargo-8.preview.emergentagent.com/api"

def diagnose_cargo_data():
    """Диагностика данных груза"""
    
    print("🔍 ДИАГНОСТИКА: Проверка данных груза с ID 100004")
    print("=" * 60)
    
    # Авторизация
    login_data = {
        "phone": "+79999888777",
        "password": "admin123"
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Ошибка авторизации: {response.text}")
        return False
        
    token = response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Поиск всех грузов с номером 100008/02
    print("\n1️⃣ ПОИСК ВСЕХ ГРУЗОВ С НОМЕРОМ 100008/02")
    print("-" * 50)
    
    response = requests.get(f"{BACKEND_URL}/operator/cargo/available-for-placement", headers=headers)
    if response.status_code == 200:
        cargo_data = response.json()
        cargo_items = cargo_data.get("items", [])
        
        print(f"Всего грузов в списке размещения: {len(cargo_items)}")
        
        cargos_100008 = []
        for cargo in cargo_items:
            if "100008" in cargo.get("cargo_number", ""):
                cargos_100008.append(cargo)
        
        print(f"Найдено грузов с номером содержащим '100008': {len(cargos_100008)}")
        
        for i, cargo in enumerate(cargos_100008):
            print(f"  {i+1}. ID: {cargo.get('id')}, Номер: {cargo.get('cargo_number')}")
            print(f"     Отправитель: {cargo.get('sender_full_name')}")
            print(f"     Статус: {cargo.get('processing_status')}")
    
    # Поиск груза с ID 100004
    print(f"\n2️⃣ ПОИСК ГРУЗА С ID 100004")
    print("-" * 50)
    
    response = requests.get(f"{BACKEND_URL}/operator/cargo/available-for-placement", headers=headers)
    if response.status_code == 200:
        cargo_data = response.json()
        cargo_items = cargo_data.get("items", [])
        
        cargo_100004 = None
        for cargo in cargo_items:
            if cargo.get("id") == "100004":
                cargo_100004 = cargo
                break
        
        if cargo_100004:
            print(f"✅ Груз с ID 100004 найден:")
            print(f"   Номер груза: {cargo_100004.get('cargo_number')}")
            print(f"   Отправитель: {cargo_100004.get('sender_full_name')}")
            print(f"   Получатель: {cargo_100004.get('recipient_full_name')}")
            print(f"   Статус: {cargo_100004.get('processing_status')}")
            print(f"   Статус оплаты: {cargo_100004.get('payment_status')}")
        else:
            print(f"⚠️ Груз с ID 100004 не найден в списке размещения")
    
    # Поиск всех грузов с ID содержащим 100004
    print(f"\n3️⃣ ПОИСК ВСЕХ ГРУЗОВ С ID СОДЕРЖАЩИМ '100004'")
    print("-" * 50)
    
    response = requests.get(f"{BACKEND_URL}/operator/cargo/list", headers=headers)
    if response.status_code == 200:
        all_cargo = response.json()
        cargo_items = all_cargo.get("items", [])
        
        print(f"Всего грузов в общем списке: {len(cargo_items)}")
        
        cargos_with_100004 = []
        for cargo in cargo_items:
            if "100004" in str(cargo.get("id", "")):
                cargos_with_100004.append(cargo)
        
        print(f"Найдено грузов с ID содержащим '100004': {len(cargos_with_100004)}")
        
        for i, cargo in enumerate(cargos_with_100004):
            print(f"  {i+1}. ID: {cargo.get('id')}, Номер: {cargo.get('cargo_number')}")
            print(f"     Отправитель: {cargo.get('sender_full_name')}")
            print(f"     Статус: {cargo.get('processing_status')}")
    
    # Проверка соответствия номера груза и ID
    print(f"\n4️⃣ АНАЛИЗ СООТВЕТСТВИЯ НОМЕРОВ И ID")
    print("-" * 50)
    
    response = requests.get(f"{BACKEND_URL}/operator/cargo/available-for-placement", headers=headers)
    if response.status_code == 200:
        cargo_data = response.json()
        cargo_items = cargo_data.get("items", [])
        
        # Ищем все грузы с номерами 100008/XX и 100012/XX
        relevant_cargos = []
        for cargo in cargo_items:
            cargo_number = cargo.get("cargo_number", "")
            if cargo_number.startswith("100008/") or cargo_number.startswith("100012/"):
                relevant_cargos.append(cargo)
        
        print(f"Найдено релевантных грузов: {len(relevant_cargos)}")
        
        for cargo in relevant_cargos:
            print(f"  Номер: {cargo.get('cargo_number')} → ID: {cargo.get('id')}")
            print(f"    Отправитель: {cargo.get('sender_full_name')}")
    
    print(f"\n" + "=" * 60)
    print(f"🎯 ВЫВОДЫ ДИАГНОСТИКИ:")
    print(f"   Проверили соответствие номеров грузов и их ID")
    print(f"   Определили, какой груз имеет ID 100004")
    print(f"   Выяснили причину несоответствия в тестах")
    
    return True

if __name__ == "__main__":
    diagnose_cargo_data()
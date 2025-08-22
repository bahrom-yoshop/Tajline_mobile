#!/usr/bin/env python3
"""
🎯 СПЕЦИАЛЬНЫЙ ТЕСТ: QR код 25082026/01/02

КОНТЕКСТ: Проверить конкретный QR код 25082026/01/02 упомянутый в review request
"""

import requests
import json

# Configuration
BACKEND_URL = "https://tajline-cargo-7.preview.emergentagent.com/api"

# Test credentials
WAREHOUSE_OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

def test_specific_qr_code():
    """Тест конкретного QR кода 25082026/01/02"""
    session = requests.Session()
    
    # Authenticate
    response = session.post(f"{BACKEND_URL}/auth/login", json=WAREHOUSE_OPERATOR_CREDENTIALS)
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        print("✅ Авторизация успешна")
    else:
        print("❌ Ошибка авторизации")
        return
    
    # Get warehouse ID
    warehouses_response = session.get(f"{BACKEND_URL}/operator/warehouses")
    if warehouses_response.status_code == 200:
        warehouses = warehouses_response.json()
        if warehouses:
            warehouse_id = warehouses[0].get("id")
            print(f"✅ Получен warehouse_id: {warehouse_id}")
        else:
            print("❌ Нет доступных складов")
            return
    else:
        print("❌ Ошибка получения складов")
        return
    
    # Test the specific QR code mentioned in review request
    test_qr_code = "25082026/01/02"
    
    placement_data = {
        "individual_number": test_qr_code,
        "warehouse_id": warehouse_id,
        "block_number": 1,
        "shelf_number": 1,
        "cell_number": 1
    }
    
    print(f"\n🔍 Тестирование QR кода: {test_qr_code}")
    
    response = session.post(f"{BACKEND_URL}/operator/cargo/place-individual", json=placement_data)
    
    print(f"HTTP Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ QR код успешно размещен!")
    elif response.status_code == 404:
        print("⚠️ QR код не найден (но формат распознается)")
    else:
        print("❌ Ошибка обработки QR кода")

if __name__ == "__main__":
    test_specific_qr_code()
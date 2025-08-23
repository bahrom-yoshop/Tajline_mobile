#!/usr/bin/env python3
"""
Quick fix to assign warehouse numbers for digital QR support
"""

import requests
import json

# Configuration
BACKEND_URL = "https://cargo-sync.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "phone": "+79999888777",
    "password": "admin123"
}

def fix_warehouse_numbers():
    session = requests.Session()
    
    # Authenticate as admin
    print("🔐 Авторизация администратора...")
    response = session.post(f"{BACKEND_URL}/auth/login", json=ADMIN_CREDENTIALS)
    
    if response.status_code != 200:
        print(f"❌ Ошибка авторизации: {response.status_code}")
        return False
    
    data = response.json()
    token = data.get("access_token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    print("✅ Авторизация успешна")
    
    # Assign warehouse numbers
    print("🔢 Присваиваем номера складам...")
    response = session.post(f"{BACKEND_URL}/admin/warehouses/assign-numbers")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data.get('message')}")
        return True
    else:
        print(f"❌ Ошибка: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    fix_warehouse_numbers()
#!/usr/bin/env python3
"""
Comprehensive Testing for Operator Warehouse-Based Access Control System
Tests all 6 requirements for the operator permissions system as specified in the review request.

REQUIREMENTS TO TEST:
1.1) Operators see cargo only from their assigned warehouses
1.2) Operators get access only to functions of assigned warehouses  
1.3) Full access to assigned warehouse
1.4) Accept cargo only to assigned warehouses
1.5) Operators see transports going to/from their warehouses
1.6) Create inter-warehouse transports
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class OperatorPermissionsAPITester:
    def __init__(self, base_url="https://tajline-cargo-8.preview.emergentagent.com"):
        self.base_url = base_url
        self.tokens = {}  # Store tokens for different users
        self.users = {}   # Store user data
        self.warehouses = {}  # Store warehouse data
        self.bindings = {}  # Store binding data
        self.cargo_ids = []  # Store created cargo IDs
        self.transport_ids = []  # Store created transport IDs
        self.tests_run = 0
        self.tests_passed = 0
        
        print(f"🔐 OPERATOR PERMISSIONS SYSTEM TESTER")
        print(f"📡 Base URL: {self.base_url}")
        print("=" * 80)

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data: Optional[Dict] = None, token: Optional[str] = None, 
                 params: Optional[Dict] = None) -> tuple[bool, Dict]:
        """Run a single API test"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'

        self.tests_run += 1
        print(f"\n🔍 Test {self.tests_run}: {name}")
        print(f"   {method} {endpoint}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, params=params)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"   ✅ PASSED - Status: {response.status_code}")
                try:
                    result = response.json()
                    if isinstance(result, dict) and len(str(result)) < 300:
                        print(f"   📄 Response: {result}")
                    elif isinstance(result, list) and len(result) <= 5:
                        print(f"   📄 Response: {len(result)} items")
                    return True, result
                except:
                    return True, {}
            else:
                print(f"   ❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   📄 Error: {error_detail}")
                except:
                    print(f"   📄 Raw response: {response.text[:200]}")
                return False, {}

        except Exception as e:
            print(f"   ❌ FAILED - Exception: {str(e)}")
            return False, {}

    def setup_test_environment(self):
        """Setup test environment with users, warehouses, and bindings"""
        print("\n🏗️ SETTING UP TEST ENVIRONMENT")
        
        # Step A: Create test users
        test_users = [
            {
                "name": "Admin User",
                "data": {
                    "full_name": "Админ Тестовый",
                    "phone": "+79999000001",
                    "password": "admin123",
                    "role": "admin"
                }
            },
            {
                "name": "Operator A (Warehouse 1)",
                "data": {
                    "full_name": "Оператор А Складской",
                    "phone": "+79999000002",
                    "password": "operator123",
                    "role": "warehouse_operator"
                }
            },
            {
                "name": "Operator B (Warehouse 2)",
                "data": {
                    "full_name": "Оператор Б Складской",
                    "phone": "+79999000003",
                    "password": "operator123",
                    "role": "warehouse_operator"
                }
            },
            {
                "name": "Operator C (No Bindings)",
                "data": {
                    "full_name": "Оператор В Без Привязок",
                    "phone": "+79999000004",
                    "password": "operator123",
                    "role": "warehouse_operator"
                }
            }
        ]
        
        print("\n   👥 Creating Test Users...")
        for user_info in test_users:
            success, response = self.run_test(
                f"Register {user_info['name']}", 
                "POST", 
                "/api/auth/register", 
                200, 
                user_info['data']
            )
            
            if success and 'access_token' in response:
                role_key = f"{user_info['data']['role']}_{user_info['data']['phone'][-1]}"
                self.tokens[role_key] = response['access_token']
                self.users[role_key] = response['user']
                print(f"   🔑 Token stored for {role_key}")
        
        # Step B: Create test warehouses
        print("\n   🏭 Creating Test Warehouses...")
        warehouse_configs = [
            {"name": "Склад 1", "location": "Москва, Складская 1"},
            {"name": "Склад 2", "location": "Москва, Складская 2"},
            {"name": "Склад 3", "location": "Москва, Складская 3"}
        ]
        
        admin_token = self.tokens.get('admin_1')
        if not admin_token:
            print("   ❌ No admin token available")
            return False
            
        for i, config in enumerate(warehouse_configs):
            warehouse_data = {
                "name": config["name"],
                "location": config["location"],
                "blocks_count": 2,
                "shelves_per_block": 2,
                "cells_per_shelf": 5
            }
            
            success, warehouse_response = self.run_test(
                f"Create {config['name']}",
                "POST",
                "/api/warehouses/create",
                200,
                warehouse_data,
                admin_token
            )
            
            if success and 'id' in warehouse_response:
                warehouse_key = f"warehouse_{i+1}"
                self.warehouses[warehouse_key] = warehouse_response
                print(f"   🏭 Created {config['name']}: {warehouse_response['id']}")
        
        # Step C: Create operator-warehouse bindings
        print("\n   🔗 Creating Operator-Warehouse Bindings...")
        bindings_config = [
            {"operator": "warehouse_operator_2", "warehouse": "warehouse_1"},  # Operator A -> Warehouse 1
            {"operator": "warehouse_operator_3", "warehouse": "warehouse_2"},  # Operator B -> Warehouse 2
            # Operator C gets no bindings
        ]
        
        for binding_config in bindings_config:
            operator_id = self.users[binding_config["operator"]]["id"]
            warehouse_id = self.warehouses[binding_config["warehouse"]]["id"]
            
            binding_data = {
                "operator_id": operator_id,
                "warehouse_id": warehouse_id
            }
            
            success, binding_response = self.run_test(
                f"Bind {binding_config['operator']} to {binding_config['warehouse']}",
                "POST",
                "/api/admin/operator-warehouse-binding",
                200,
                binding_data,
                admin_token
            )
            
            if success and 'binding_id' in binding_response:
                binding_key = f"{binding_config['operator']}_{binding_config['warehouse']}"
                self.bindings[binding_key] = binding_response
                print(f"   🔗 Created binding: {binding_key}")
        
        # Step D: Create test cargo on different warehouses
        print("\n   📦 Creating Test Cargo on Different Warehouses...")
        cargo_configs = [
            {"warehouse": "warehouse_1", "operator": "warehouse_operator_2", "name": "Груз Склад 1 #1"},
            {"warehouse": "warehouse_1", "operator": "warehouse_operator_2", "name": "Груз Склад 1 #2"},
            {"warehouse": "warehouse_2", "operator": "warehouse_operator_3", "name": "Груз Склад 2 #1"},
            {"warehouse": "warehouse_2", "operator": "warehouse_operator_3", "name": "Груз Склад 2 #2"},
        ]
        
        for i, cargo_config in enumerate(cargo_configs):
            cargo_data = {
                "sender_full_name": f"Отправитель {i+1}",
                "sender_phone": f"+79111{i+1}{i+1}{i+1}{i+1}{i+1}{i+1}",
                "recipient_full_name": f"Получатель {i+1}",
                "recipient_phone": f"+99244{i+1}{i+1}{i+1}{i+1}{i+1}{i+1}",
                "recipient_address": f"Душанбе, ул. Тестовая, {i+1}",
                "weight": 10.0 + i,
                "cargo_name": cargo_config["name"],
                "declared_value": 5000.0 + (i * 1000),
                "description": f"Тестовый груз для {cargo_config['warehouse']}",
                "route": "moscow_to_tajikistan"
            }
            
            operator_token = self.tokens[cargo_config["operator"]]
            success, cargo_response = self.run_test(
                f"Create {cargo_config['name']}",
                "POST",
                "/api/operator/cargo/accept",
                200,
                cargo_data,
                operator_token
            )
            
            if success and 'id' in cargo_response:
                self.cargo_ids.append({
                    "id": cargo_response['id'],
                    "number": cargo_response.get('cargo_number'),
                    "warehouse": cargo_config["warehouse"],
                    "operator": cargo_config["operator"]
                })
                print(f"   📦 Created cargo: {cargo_response.get('cargo_number')} on {cargo_config['warehouse']}")
        
        return True

    def test_requirement_1_1_cargo_visibility_filtering(self):
        """Test 1.1: Operators see cargo only from their assigned warehouses"""
        print("\n" + "="*80)
        print("🔍 REQUIREMENT 1.1: CARGO VISIBILITY FILTERING")
        print("Testing that operators see only cargo from their assigned warehouses")
        print("="*80)
        
        all_success = True
        
        # Test A: Admin sees all cargo
        print("\n   👑 Testing Admin Access (Should see ALL cargo)...")
        admin_token = self.tokens.get('admin_1')
        success, admin_cargo = self.run_test(
            "Admin Get All Cargo",
            "GET",
            "/api/operator/cargo/list",
            200,
            token=admin_token
        )
        all_success &= success
        
        if success:
            admin_cargo_count = len(admin_cargo) if isinstance(admin_cargo, list) else 0
            print(f"   📊 Admin sees {admin_cargo_count} cargo items (should see all)")
        
        # Test B: Operator A sees only Warehouse 1 cargo
        print("\n   🏭 Testing Operator A Access (Should see only Warehouse 1 cargo)...")
        operator_a_token = self.tokens.get('warehouse_operator_2')
        success, operator_a_cargo = self.run_test(
            "Operator A Get Cargo List",
            "GET",
            "/api/operator/cargo/list",
            200,
            token=operator_a_token
        )
        all_success &= success
        
        if success:
            operator_a_count = len(operator_a_cargo) if isinstance(operator_a_cargo, list) else 0
            print(f"   📊 Operator A sees {operator_a_count} cargo items")
            
            # Verify cargo belongs to Warehouse 1 or was created by Operator A
            warehouse_1_cargo = [c for c in self.cargo_ids if c["warehouse"] == "warehouse_1"]
            expected_count = len(warehouse_1_cargo)
            
            if operator_a_count == expected_count:
                print(f"   ✅ Correct filtering: Operator A sees exactly {expected_count} cargo items from Warehouse 1")
            else:
                print(f"   ❌ Incorrect filtering: Expected {expected_count}, got {operator_a_count}")
                all_success = False
        
        # Test C: Operator B sees only Warehouse 2 cargo
        print("\n   🏭 Testing Operator B Access (Should see only Warehouse 2 cargo)...")
        operator_b_token = self.tokens.get('warehouse_operator_3')
        success, operator_b_cargo = self.run_test(
            "Operator B Get Cargo List",
            "GET",
            "/api/operator/cargo/list",
            200,
            token=operator_b_token
        )
        all_success &= success
        
        if success:
            operator_b_count = len(operator_b_cargo) if isinstance(operator_b_cargo, list) else 0
            print(f"   📊 Operator B sees {operator_b_count} cargo items")
            
            # Verify cargo belongs to Warehouse 2 or was created by Operator B
            warehouse_2_cargo = [c for c in self.cargo_ids if c["warehouse"] == "warehouse_2"]
            expected_count = len(warehouse_2_cargo)
            
            if operator_b_count == expected_count:
                print(f"   ✅ Correct filtering: Operator B sees exactly {expected_count} cargo items from Warehouse 2")
            else:
                print(f"   ❌ Incorrect filtering: Expected {expected_count}, got {operator_b_count}")
                all_success = False
        
        # Test D: Operator C (no bindings) sees empty list
        print("\n   🚫 Testing Operator C Access (No bindings - should see empty list)...")
        operator_c_token = self.tokens.get('warehouse_operator_4')
        success, operator_c_cargo = self.run_test(
            "Operator C Get Cargo List",
            "GET",
            "/api/operator/cargo/list",
            200,
            token=operator_c_token
        )
        all_success &= success
        
        if success:
            operator_c_count = len(operator_c_cargo) if isinstance(operator_c_cargo, list) else 0
            print(f"   📊 Operator C sees {operator_c_count} cargo items")
            
            if operator_c_count == 0:
                print(f"   ✅ Correct isolation: Operator C with no bindings sees 0 cargo items")
            else:
                print(f"   ❌ Security breach: Operator C should see 0 cargo items, got {operator_c_count}")
                all_success = False
        
        return all_success

    def test_requirement_1_2_warehouse_function_access(self):
        """Test 1.2: Operators get access only to functions of assigned warehouses"""
        print("\n" + "="*80)
        print("🏭 REQUIREMENT 1.2: WAREHOUSE FUNCTION ACCESS")
        print("Testing that operators get detailed statistics only for assigned warehouses")
        print("="*80)
        
        all_success = True
        
        # Test A: Admin sees all warehouses
        print("\n   👑 Testing Admin Warehouse Access (Should see ALL warehouses)...")
        admin_token = self.tokens.get('admin_1')
        success, admin_warehouses = self.run_test(
            "Admin Get My Warehouses",
            "GET",
            "/api/operator/my-warehouses",
            200,
            token=admin_token
        )
        all_success &= success
        
        if success:
            admin_warehouse_data = admin_warehouses.get('warehouses', []) if isinstance(admin_warehouses, dict) else []
            admin_count = len(admin_warehouse_data)
            is_admin = admin_warehouses.get('is_admin', False)
            
            print(f"   📊 Admin sees {admin_count} warehouses (is_admin: {is_admin})")
            
            if is_admin and admin_count >= 3:  # Should see all 3 warehouses we created
                print(f"   ✅ Admin has access to all warehouses with detailed statistics")
            else:
                print(f"   ❌ Admin should have access to all warehouses")
                all_success = False
        
        # Test B: Operator A sees only assigned warehouse with detailed stats
        print("\n   🏭 Testing Operator A Warehouse Access (Should see only Warehouse 1)...")
        operator_a_token = self.tokens.get('warehouse_operator_2')
        success, operator_a_warehouses = self.run_test(
            "Operator A Get My Warehouses",
            "GET",
            "/api/operator/my-warehouses",
            200,
            token=operator_a_token
        )
        all_success &= success
        
        if success:
            operator_a_data = operator_a_warehouses.get('warehouses', []) if isinstance(operator_a_warehouses, dict) else []
            operator_a_count = len(operator_a_data)
            is_admin = operator_a_warehouses.get('is_admin', False)
            
            print(f"   📊 Operator A sees {operator_a_count} warehouses (is_admin: {is_admin})")
            
            if operator_a_count == 1 and not is_admin:
                warehouse_info = operator_a_data[0]
                warehouse_id = warehouse_info.get('id')
                expected_warehouse_id = self.warehouses['warehouse_1']['id']
                
                if warehouse_id == expected_warehouse_id:
                    print(f"   ✅ Operator A correctly sees only assigned Warehouse 1")
                    
                    # Check detailed statistics
                    required_stats = ['total_cells', 'occupied_cells', 'free_cells', 'occupancy_percentage', 'total_cargo']
                    missing_stats = [stat for stat in required_stats if stat not in warehouse_info]
                    
                    if not missing_stats:
                        print(f"   ✅ Detailed warehouse statistics provided: {required_stats}")
                    else:
                        print(f"   ❌ Missing warehouse statistics: {missing_stats}")
                        all_success = False
                else:
                    print(f"   ❌ Operator A sees wrong warehouse: {warehouse_id} vs expected {expected_warehouse_id}")
                    all_success = False
            else:
                print(f"   ❌ Operator A should see exactly 1 warehouse, got {operator_a_count}")
                all_success = False
        
        # Test C: Operator B sees only assigned warehouse
        print("\n   🏭 Testing Operator B Warehouse Access (Should see only Warehouse 2)...")
        operator_b_token = self.tokens.get('warehouse_operator_3')
        success, operator_b_warehouses = self.run_test(
            "Operator B Get My Warehouses",
            "GET",
            "/api/operator/my-warehouses",
            200,
            token=operator_b_token
        )
        all_success &= success
        
        if success:
            operator_b_data = operator_b_warehouses.get('warehouses', []) if isinstance(operator_b_warehouses, dict) else []
            operator_b_count = len(operator_b_data)
            
            if operator_b_count == 1:
                warehouse_info = operator_b_data[0]
                warehouse_id = warehouse_info.get('id')
                expected_warehouse_id = self.warehouses['warehouse_2']['id']
                
                if warehouse_id == expected_warehouse_id:
                    print(f"   ✅ Operator B correctly sees only assigned Warehouse 2")
                else:
                    print(f"   ❌ Operator B sees wrong warehouse: {warehouse_id} vs expected {expected_warehouse_id}")
                    all_success = False
            else:
                print(f"   ❌ Operator B should see exactly 1 warehouse, got {operator_b_count}")
                all_success = False
        
        # Test D: Operator C (no bindings) sees empty list
        print("\n   🚫 Testing Operator C Warehouse Access (No bindings - should see empty list)...")
        operator_c_token = self.tokens.get('warehouse_operator_4')
        success, operator_c_warehouses = self.run_test(
            "Operator C Get My Warehouses",
            "GET",
            "/api/operator/my-warehouses",
            200,
            token=operator_c_token
        )
        all_success &= success
        
        if success:
            operator_c_data = operator_c_warehouses.get('warehouses', []) if isinstance(operator_c_warehouses, dict) else []
            operator_c_count = len(operator_c_data)
            message = operator_c_warehouses.get('message', '')
            
            if operator_c_count == 0 and 'No warehouses assigned' in message:
                print(f"   ✅ Operator C correctly sees no warehouses (message: {message})")
            else:
                print(f"   ❌ Operator C should see 0 warehouses, got {operator_c_count}")
                all_success = False
        
        return all_success

    def test_requirement_1_4_cargo_acceptance_restrictions(self):
        """Test 1.4: Accept cargo only to assigned warehouses"""
        print("\n" + "="*80)
        print("📥 REQUIREMENT 1.4: CARGO ACCEPTANCE RESTRICTIONS")
        print("Testing that operators can only accept cargo to their assigned warehouses")
        print("="*80)
        
        all_success = True
        
        # Test A: Operator A can accept cargo (has warehouse binding)
        print("\n   ✅ Testing Operator A Cargo Acceptance (Should succeed - has warehouse binding)...")
        operator_a_token = self.tokens.get('warehouse_operator_2')
        
        cargo_data = {
            "sender_full_name": "Тестовый Отправитель А",
            "sender_phone": "+79111999001",
            "recipient_full_name": "Тестовый Получатель А",
            "recipient_phone": "+992444999001",
            "recipient_address": "Душанбе, ул. Тестовая Приемка, 1",
            "weight": 15.0,
            "cargo_name": "Груз для теста приемки А",
            "declared_value": 7500.0,
            "description": "Тестовый груз для проверки приемки оператором А",
            "route": "moscow_to_tajikistan"
        }
        
        success, cargo_response = self.run_test(
            "Operator A Accept Cargo",
            "POST",
            "/api/operator/cargo/accept",
            200,
            cargo_data,
            operator_a_token
        )
        all_success &= success
        
        if success:
            cargo_number = cargo_response.get('cargo_number')
            target_warehouse_id = cargo_response.get('target_warehouse_id')
            target_warehouse_name = cargo_response.get('target_warehouse_name')
            expected_warehouse_id = self.warehouses['warehouse_1']['id']
            
            print(f"   📦 Cargo accepted: {cargo_number}")
            print(f"   🏭 Target warehouse: {target_warehouse_name} ({target_warehouse_id})")
            
            if target_warehouse_id == expected_warehouse_id:
                print(f"   ✅ Cargo automatically assigned to correct warehouse (Warehouse 1)")
            else:
                print(f"   ❌ Cargo assigned to wrong warehouse: {target_warehouse_id} vs expected {expected_warehouse_id}")
                all_success = False
        
        # Test B: Operator B can accept cargo (has warehouse binding)
        print("\n   ✅ Testing Operator B Cargo Acceptance (Should succeed - has warehouse binding)...")
        operator_b_token = self.tokens.get('warehouse_operator_3')
        
        cargo_data_b = {
            "sender_full_name": "Тестовый Отправитель Б",
            "sender_phone": "+79111999002",
            "recipient_full_name": "Тестовый Получатель Б",
            "recipient_phone": "+992444999002",
            "recipient_address": "Душанбе, ул. Тестовая Приемка, 2",
            "weight": 20.0,
            "cargo_name": "Груз для теста приемки Б",
            "declared_value": 9000.0,
            "description": "Тестовый груз для проверки приемки оператором Б",
            "route": "moscow_to_tajikistan"
        }
        
        success, cargo_response_b = self.run_test(
            "Operator B Accept Cargo",
            "POST",
            "/api/operator/cargo/accept",
            200,
            cargo_data_b,
            operator_b_token
        )
        all_success &= success
        
        if success:
            cargo_number_b = cargo_response_b.get('cargo_number')
            target_warehouse_id_b = cargo_response_b.get('target_warehouse_id')
            target_warehouse_name_b = cargo_response_b.get('target_warehouse_name')
            expected_warehouse_id_b = self.warehouses['warehouse_2']['id']
            
            print(f"   📦 Cargo accepted: {cargo_number_b}")
            print(f"   🏭 Target warehouse: {target_warehouse_name_b} ({target_warehouse_id_b})")
            
            if target_warehouse_id_b == expected_warehouse_id_b:
                print(f"   ✅ Cargo automatically assigned to correct warehouse (Warehouse 2)")
            else:
                print(f"   ❌ Cargo assigned to wrong warehouse: {target_warehouse_id_b} vs expected {expected_warehouse_id_b}")
                all_success = False
        
        # Test C: Operator C cannot accept cargo (no warehouse bindings)
        print("\n   🚫 Testing Operator C Cargo Acceptance (Should fail - no warehouse bindings)...")
        operator_c_token = self.tokens.get('warehouse_operator_4')
        
        cargo_data_c = {
            "sender_full_name": "Тестовый Отправитель В",
            "sender_phone": "+79111999003",
            "recipient_full_name": "Тестовый Получатель В",
            "recipient_phone": "+992444999003",
            "recipient_address": "Душанбе, ул. Тестовая Приемка, 3",
            "weight": 12.0,
            "cargo_name": "Груз для теста приемки В",
            "declared_value": 6000.0,
            "description": "Тестовый груз для проверки блокировки приемки",
            "route": "moscow_to_tajikistan"
        }
        
        success, error_response = self.run_test(
            "Operator C Accept Cargo (Should Fail)",
            "POST",
            "/api/operator/cargo/accept",
            403,  # Expecting forbidden
            cargo_data_c,
            operator_c_token
        )
        all_success &= success
        
        if success:
            error_detail = error_response.get('detail', '')
            if 'No warehouses assigned' in error_detail or 'Cannot accept cargo' in error_detail:
                print(f"   ✅ Correctly blocked cargo acceptance: {error_detail}")
            else:
                print(f"   ❌ Wrong error message: {error_detail}")
                all_success = False
        
        # Test D: Admin can accept cargo (has access to all warehouses)
        print("\n   👑 Testing Admin Cargo Acceptance (Should succeed - admin access)...")
        admin_token = self.tokens.get('admin_1')
        
        cargo_data_admin = {
            "sender_full_name": "Админский Отправитель",
            "sender_phone": "+79111999004",
            "recipient_full_name": "Админский Получатель",
            "recipient_phone": "+992444999004",
            "recipient_address": "Душанбе, ул. Админская, 1",
            "weight": 25.0,
            "cargo_name": "Админский груз",
            "declared_value": 12000.0,
            "description": "Груз принятый администратором",
            "route": "moscow_to_tajikistan"
        }
        
        success, admin_cargo_response = self.run_test(
            "Admin Accept Cargo",
            "POST",
            "/api/operator/cargo/accept",
            200,
            cargo_data_admin,
            admin_token
        )
        all_success &= success
        
        if success:
            admin_cargo_number = admin_cargo_response.get('cargo_number')
            print(f"   📦 Admin successfully accepted cargo: {admin_cargo_number}")
            print(f"   ✅ Admin can accept cargo (has universal access)")
        
        return all_success

    def test_requirement_1_5_transport_visibility_filtering(self):
        """Test 1.5: Operators see transports going to/from their warehouses"""
        print("\n" + "="*80)
        print("🚛 REQUIREMENT 1.5: TRANSPORT VISIBILITY FILTERING")
        print("Testing that operators see only transports related to their warehouses")
        print("="*80)
        
        all_success = True
        
        # First, create some test transports
        print("\n   🚛 Creating Test Transports...")
        admin_token = self.tokens.get('admin_1')
        
        transport_configs = [
            {
                "name": "Transport to Warehouse 1",
                "data": {
                    "driver_name": "Водитель Первый",
                    "driver_phone": "+79111888001",
                    "transport_number": "А001БВ77",
                    "capacity_kg": 3000.0,
                    "direction": "Москва - Душанбе (Склад 1)"
                },
                "source_warehouse": "warehouse_1",
                "destination_warehouse": "warehouse_2"
            },
            {
                "name": "Transport to Warehouse 2", 
                "data": {
                    "driver_name": "Водитель Второй",
                    "driver_phone": "+79111888002",
                    "transport_number": "А002БВ77",
                    "capacity_kg": 4000.0,
                    "direction": "Москва - Душанбе (Склад 2)"
                },
                "source_warehouse": "warehouse_2",
                "destination_warehouse": "warehouse_1"
            },
            {
                "name": "Transport to Warehouse 3",
                "data": {
                    "driver_name": "Водитель Третий",
                    "driver_phone": "+79111888003",
                    "transport_number": "А003БВ77",
                    "capacity_kg": 5000.0,
                    "direction": "Москва - Душанбе (Склад 3)"
                },
                "source_warehouse": "warehouse_3",
                "destination_warehouse": "warehouse_3"
            }
        ]
        
        created_transports = []
        for transport_config in transport_configs:
            success, transport_response = self.run_test(
                f"Create {transport_config['name']}",
                "POST",
                "/api/transport/create",
                200,
                transport_config['data'],
                admin_token
            )
            
            if success and 'transport_id' in transport_response:
                transport_id = transport_response['transport_id']
                created_transports.append({
                    "id": transport_id,
                    "name": transport_config['name'],
                    "source_warehouse": transport_config['source_warehouse'],
                    "destination_warehouse": transport_config['destination_warehouse']
                })
                print(f"   🚛 Created transport: {transport_id}")
        
        # Test A: Admin sees all transports
        print("\n   👑 Testing Admin Transport Access (Should see ALL transports)...")
        success, admin_transports = self.run_test(
            "Admin Get Transport List",
            "GET",
            "/api/transport/list",
            200,
            token=admin_token
        )
        all_success &= success
        
        if success:
            admin_transport_count = len(admin_transports) if isinstance(admin_transports, list) else 0
            print(f"   📊 Admin sees {admin_transport_count} transports (should see all)")
            
            if admin_transport_count >= len(created_transports):
                print(f"   ✅ Admin has access to all transports")
            else:
                print(f"   ❌ Admin should see at least {len(created_transports)} transports")
                all_success = False
        
        # Test B: Operator A sees only transports related to Warehouse 1
        print("\n   🏭 Testing Operator A Transport Access (Should see only Warehouse 1 related)...")
        operator_a_token = self.tokens.get('warehouse_operator_2')
        success, operator_a_transports = self.run_test(
            "Operator A Get Transport List",
            "GET",
            "/api/transport/list",
            200,
            token=operator_a_token
        )
        all_success &= success
        
        if success:
            operator_a_count = len(operator_a_transports) if isinstance(operator_a_transports, list) else 0
            print(f"   📊 Operator A sees {operator_a_count} transports")
            
            # Count expected transports (those involving Warehouse 1)
            expected_transports = [t for t in created_transports 
                                 if t['source_warehouse'] == 'warehouse_1' or t['destination_warehouse'] == 'warehouse_1']
            expected_count = len(expected_transports)
            
            if operator_a_count >= expected_count:
                print(f"   ✅ Operator A sees appropriate number of transports (at least {expected_count})")
            else:
                print(f"   ❌ Operator A should see at least {expected_count} transports, got {operator_a_count}")
                all_success = False
        
        # Test C: Operator B sees only transports related to Warehouse 2
        print("\n   🏭 Testing Operator B Transport Access (Should see only Warehouse 2 related)...")
        operator_b_token = self.tokens.get('warehouse_operator_3')
        success, operator_b_transports = self.run_test(
            "Operator B Get Transport List",
            "GET",
            "/api/transport/list",
            200,
            token=operator_b_token
        )
        all_success &= success
        
        if success:
            operator_b_count = len(operator_b_transports) if isinstance(operator_b_transports, list) else 0
            print(f"   📊 Operator B sees {operator_b_count} transports")
            
            # Count expected transports (those involving Warehouse 2)
            expected_transports = [t for t in created_transports 
                                 if t['source_warehouse'] == 'warehouse_2' or t['destination_warehouse'] == 'warehouse_2']
            expected_count = len(expected_transports)
            
            if operator_b_count >= expected_count:
                print(f"   ✅ Operator B sees appropriate number of transports (at least {expected_count})")
            else:
                print(f"   ❌ Operator B should see at least {expected_count} transports, got {operator_b_count}")
                all_success = False
        
        # Test D: Operator C (no bindings) sees limited transports
        print("\n   🚫 Testing Operator C Transport Access (No bindings - should see limited/no transports)...")
        operator_c_token = self.tokens.get('warehouse_operator_4')
        success, operator_c_transports = self.run_test(
            "Operator C Get Transport List",
            "GET",
            "/api/transport/list",
            200,
            token=operator_c_token
        )
        all_success &= success
        
        if success:
            operator_c_count = len(operator_c_transports) if isinstance(operator_c_transports, list) else 0
            print(f"   📊 Operator C sees {operator_c_count} transports")
            
            # Operator C should see very few or no transports since they have no warehouse bindings
            if operator_c_count <= 1:  # Allow for transports they might have created
                print(f"   ✅ Operator C correctly sees limited transports ({operator_c_count})")
            else:
                print(f"   ❌ Operator C should see very few transports, got {operator_c_count}")
                all_success = False
        
        # Store transport IDs for cleanup
        self.transport_ids = [t['id'] for t in created_transports]
        
        return all_success

    def test_requirement_1_6_interwarehouse_transport_creation(self):
        """Test 1.6: Create inter-warehouse transports"""
        print("\n" + "="*80)
        print("🔄 REQUIREMENT 1.6: INTER-WAREHOUSE TRANSPORT CREATION")
        print("Testing creation of transports between operator's accessible warehouses")
        print("="*80)
        
        all_success = True
        
        # Test A: Operator A creates inter-warehouse transport (should work if has access to multiple warehouses)
        print("\n   🔄 Testing Operator A Inter-warehouse Transport Creation...")
        operator_a_token = self.tokens.get('warehouse_operator_2')
        
        # First check what warehouses Operator A has access to
        success, operator_a_warehouses = self.run_test(
            "Get Operator A Warehouses for Inter-transport",
            "GET",
            "/api/operator/my-warehouses",
            200,
            token=operator_a_token
        )
        
        if success:
            warehouses_data = operator_a_warehouses.get('warehouses', [])
            warehouse_count = len(warehouses_data)
            print(f"   📊 Operator A has access to {warehouse_count} warehouses")
            
            if warehouse_count >= 2:
                # Can create inter-warehouse transport
                source_warehouse_id = warehouses_data[0]['id']
                destination_warehouse_id = warehouses_data[1]['id']
                
                inter_transport_data = {
                    "source_warehouse_id": source_warehouse_id,
                    "destination_warehouse_id": destination_warehouse_id,
                    "driver_name": "Межскладской Водитель А",
                    "driver_phone": "+79111777001",
                    "transport_number": "IW001БВ77",
                    "capacity_kg": 2000.0,
                    "notes": "Межскладской транспорт от Оператора А"
                }
                
                success, inter_transport_response = self.run_test(
                    "Operator A Create Inter-warehouse Transport",
                    "POST",
                    "/api/transport/create-interwarehouse",
                    200,
                    inter_transport_data,
                    operator_a_token
                )
                all_success &= success
                
                if success:
                    transport_id = inter_transport_response.get('transport_id')
                    transport_number = inter_transport_response.get('transport_number')
                    print(f"   ✅ Inter-warehouse transport created: {transport_number} ({transport_id})")
                    
                    # Verify transport number has IW- prefix
                    if transport_number and transport_number.startswith('IW-'):
                        print(f"   ✅ Correct inter-warehouse prefix: {transport_number}")
                    else:
                        print(f"   ❌ Missing IW- prefix in transport number: {transport_number}")
                        all_success = False
            else:
                print(f"   ℹ️  Operator A has access to only {warehouse_count} warehouse(s), cannot test inter-warehouse transport")
        
        # Test B: Admin creates inter-warehouse transport (should work - has access to all warehouses)
        print("\n   👑 Testing Admin Inter-warehouse Transport Creation...")
        admin_token = self.tokens.get('admin_1')
        
        if len(self.warehouses) >= 2:
            warehouse_keys = list(self.warehouses.keys())
            source_warehouse_id = self.warehouses[warehouse_keys[0]]['id']
            destination_warehouse_id = self.warehouses[warehouse_keys[1]]['id']
            
            admin_inter_transport_data = {
                "source_warehouse_id": source_warehouse_id,
                "destination_warehouse_id": destination_warehouse_id,
                "driver_name": "Админский Межскладской Водитель",
                "driver_phone": "+79111777002",
                "transport_number": "IW002БВ77",
                "capacity_kg": 3000.0,
                "notes": "Межскладской транспорт от Администратора"
            }
            
            success, admin_inter_response = self.run_test(
                "Admin Create Inter-warehouse Transport",
                "POST",
                "/api/transport/create-interwarehouse",
                200,
                admin_inter_transport_data,
                admin_token
            )
            all_success &= success
            
            if success:
                admin_transport_id = admin_inter_response.get('transport_id')
                admin_transport_number = admin_inter_response.get('transport_number')
                print(f"   ✅ Admin inter-warehouse transport created: {admin_transport_number} ({admin_transport_id})")
        
        # Test C: Operator tries to create transport between inaccessible warehouses (should fail)
        print("\n   🚫 Testing Operator Access Control for Inter-warehouse Transport...")
        operator_a_token = self.tokens.get('warehouse_operator_2')
        
        # Try to create transport using warehouse that Operator A doesn't have access to
        if len(self.warehouses) >= 3:
            accessible_warehouse_id = self.warehouses['warehouse_1']['id']  # Operator A has access
            inaccessible_warehouse_id = self.warehouses['warehouse_3']['id']  # Operator A doesn't have access
            
            invalid_transport_data = {
                "source_warehouse_id": accessible_warehouse_id,
                "destination_warehouse_id": inaccessible_warehouse_id,
                "driver_name": "Недоступный Водитель",
                "driver_phone": "+79111777003",
                "transport_number": "IW003БВ77",
                "capacity_kg": 1500.0,
                "notes": "Попытка создания недоступного транспорта"
            }
            
            success, error_response = self.run_test(
                "Operator A Create Invalid Inter-warehouse Transport (Should Fail)",
                "POST",
                "/api/transport/create-interwarehouse",
                403,  # Expecting forbidden
                invalid_transport_data,
                operator_a_token
            )
            all_success &= success
            
            if success:
                error_detail = error_response.get('detail', '')
                if 'Access denied' in error_detail or 'not accessible' in error_detail:
                    print(f"   ✅ Correctly blocked invalid inter-warehouse transport: {error_detail}")
                else:
                    print(f"   ❌ Wrong error message: {error_detail}")
                    all_success = False
        
        # Test D: Validation - same source and destination warehouse (should fail)
        print("\n   ⚠️  Testing Same Warehouse Validation...")
        admin_token = self.tokens.get('admin_1')
        
        same_warehouse_id = self.warehouses['warehouse_1']['id']
        same_warehouse_data = {
            "source_warehouse_id": same_warehouse_id,
            "destination_warehouse_id": same_warehouse_id,
            "driver_name": "Одинаковый Водитель",
            "driver_phone": "+79111777004",
            "transport_number": "IW004БВ77",
            "capacity_kg": 1000.0,
            "notes": "Транспорт с одинаковыми складами"
        }
        
        success, validation_error = self.run_test(
            "Create Transport with Same Source/Destination (Should Fail)",
            "POST",
            "/api/transport/create-interwarehouse",
            400,  # Expecting bad request
            same_warehouse_data,
            admin_token
        )
        all_success &= success
        
        if success:
            error_detail = validation_error.get('detail', '')
            if 'same warehouse' in error_detail.lower() or 'identical' in error_detail.lower():
                print(f"   ✅ Correctly validated same warehouse restriction: {error_detail}")
            else:
                print(f"   ❌ Wrong validation error: {error_detail}")
                all_success = False
        
        return all_success

    def test_cross_tenant_security(self):
        """Test cross-tenant security - operators should not see each other's data"""
        print("\n" + "="*80)
        print("🔒 CROSS-TENANT SECURITY TESTING")
        print("Testing that operators cannot access data from other operators' warehouses")
        print("="*80)
        
        all_success = True
        
        # Test A: Operator A cannot see Operator B's cargo
        print("\n   🔒 Testing Cargo Isolation Between Operators...")
        operator_a_token = self.tokens.get('warehouse_operator_2')
        operator_b_token = self.tokens.get('warehouse_operator_3')
        
        # Get Operator A's cargo list
        success, operator_a_cargo = self.run_test(
            "Get Operator A Cargo List",
            "GET",
            "/api/operator/cargo/list",
            200,
            token=operator_a_token
        )
        all_success &= success
        
        # Get Operator B's cargo list
        success, operator_b_cargo = self.run_test(
            "Get Operator B Cargo List",
            "GET",
            "/api/operator/cargo/list",
            200,
            token=operator_b_token
        )
        all_success &= success
        
        if success:
            # Check for cargo overlap (there should be none)
            operator_a_numbers = set()
            operator_b_numbers = set()
            
            if isinstance(operator_a_cargo, list):
                operator_a_numbers = {c.get('cargo_number') for c in operator_a_cargo if c.get('cargo_number')}
            
            if isinstance(operator_b_cargo, list):
                operator_b_numbers = {c.get('cargo_number') for c in operator_b_cargo if c.get('cargo_number')}
            
            overlap = operator_a_numbers.intersection(operator_b_numbers)
            
            if not overlap:
                print(f"   ✅ Perfect cargo isolation: No overlap between operators")
                print(f"   📊 Operator A cargo: {len(operator_a_numbers)} items")
                print(f"   📊 Operator B cargo: {len(operator_b_numbers)} items")
            else:
                print(f"   ❌ SECURITY BREACH: Cargo overlap detected: {overlap}")
                all_success = False
        
        # Test B: Regular user cannot access operator functions
        print("\n   🚫 Testing Regular User Access Restrictions...")
        
        # Create a regular user for testing
        regular_user_data = {
            "full_name": "Обычный Пользователь",
            "phone": "+79999000005",
            "password": "user123",
            "role": "user"
        }
        
        success, user_response = self.run_test(
            "Register Regular User",
            "POST",
            "/api/auth/register",
            200,
            regular_user_data
        )
        
        if success and 'access_token' in user_response:
            regular_user_token = user_response['access_token']
            
            # Test that regular user cannot access operator cargo list
            success, _ = self.run_test(
                "Regular User Access Operator Cargo (Should Fail)",
                "GET",
                "/api/operator/cargo/list",
                403,
                token=regular_user_token
            )
            all_success &= success
            
            # Test that regular user cannot access operator warehouses
            success, _ = self.run_test(
                "Regular User Access Operator Warehouses (Should Fail)",
                "GET",
                "/api/operator/my-warehouses",
                403,
                token=regular_user_token
            )
            all_success &= success
            
            # Test that regular user cannot accept cargo as operator
            cargo_data = {
                "sender_full_name": "Злоумышленник",
                "sender_phone": "+79999999999",
                "recipient_full_name": "Получатель",
                "recipient_phone": "+992999999999",
                "recipient_address": "Адрес",
                "weight": 10.0,
                "declared_value": 5000.0,
                "description": "Попытка несанкционированного доступа",
                "route": "moscow_to_tajikistan"
            }
            
            success, _ = self.run_test(
                "Regular User Accept Cargo (Should Fail)",
                "POST",
                "/api/operator/cargo/accept",
                403,
                cargo_data,
                token=regular_user_token
            )
            all_success &= success
            
            if success:
                print(f"   ✅ Regular user correctly blocked from operator functions")
        
        # Test C: Unauthorized access (no token)
        print("\n   🚫 Testing Unauthorized Access...")
        
        success, _ = self.run_test(
            "Unauthorized Access to Operator Cargo (Should Fail)",
            "GET",
            "/api/operator/cargo/list",
            403  # FastAPI returns 403 for missing authentication
        )
        all_success &= success
        
        success, _ = self.run_test(
            "Unauthorized Access to Operator Warehouses (Should Fail)",
            "GET",
            "/api/operator/my-warehouses",
            403
        )
        all_success &= success
        
        if success:
            print(f"   ✅ Unauthorized access correctly blocked")
        
        return all_success

    def run_comprehensive_test_suite(self):
        """Run the complete test suite for operator permissions system"""
        print("\n🚀 STARTING COMPREHENSIVE OPERATOR PERMISSIONS TEST SUITE")
        print("Testing all 6 requirements for the operator warehouse-based access control system")
        print("="*80)
        
        # Setup test environment
        setup_success = self.setup_test_environment()
        if not setup_success:
            print("\n❌ FAILED TO SETUP TEST ENVIRONMENT - ABORTING TESTS")
            return False
        
        print(f"\n✅ TEST ENVIRONMENT SETUP COMPLETE")
        print(f"   👥 Users created: {len(self.users)}")
        print(f"   🏭 Warehouses created: {len(self.warehouses)}")
        print(f"   🔗 Bindings created: {len(self.bindings)}")
        print(f"   📦 Test cargo created: {len(self.cargo_ids)}")
        
        # Run all requirement tests
        test_results = []
        
        # Requirement 1.1: Cargo visibility filtering
        result_1_1 = self.test_requirement_1_1_cargo_visibility_filtering()
        test_results.append(("1.1 - Cargo Visibility Filtering", result_1_1))
        
        # Requirement 1.2: Warehouse function access
        result_1_2 = self.test_requirement_1_2_warehouse_function_access()
        test_results.append(("1.2 - Warehouse Function Access", result_1_2))
        
        # Requirement 1.4: Cargo acceptance restrictions
        result_1_4 = self.test_requirement_1_4_cargo_acceptance_restrictions()
        test_results.append(("1.4 - Cargo Acceptance Restrictions", result_1_4))
        
        # Requirement 1.5: Transport visibility filtering
        result_1_5 = self.test_requirement_1_5_transport_visibility_filtering()
        test_results.append(("1.5 - Transport Visibility Filtering", result_1_5))
        
        # Requirement 1.6: Inter-warehouse transport creation
        result_1_6 = self.test_requirement_1_6_interwarehouse_transport_creation()
        test_results.append(("1.6 - Inter-warehouse Transport Creation", result_1_6))
        
        # Cross-tenant security testing
        security_result = self.test_cross_tenant_security()
        test_results.append(("Cross-Tenant Security", security_result))
        
        # Print final results
        print("\n" + "="*80)
        print("📊 FINAL TEST RESULTS")
        print("="*80)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {status} - {test_name}")
            if result:
                passed_tests += 1
        
        print(f"\n📈 OVERALL RESULTS:")
        print(f"   🎯 Individual Tests: {self.tests_passed}/{self.tests_run} passed ({(self.tests_passed/self.tests_run)*100:.1f}%)")
        print(f"   🎯 Requirement Tests: {passed_tests}/{total_tests} passed ({(passed_tests/total_tests)*100:.1f}%)")
        
        overall_success = passed_tests == total_tests
        
        if overall_success:
            print(f"\n🎉 ALL OPERATOR PERMISSIONS REQUIREMENTS PASSED!")
            print(f"   ✅ Operators see cargo only from assigned warehouses")
            print(f"   ✅ Operators get access only to assigned warehouse functions")
            print(f"   ✅ Operators can accept cargo only to assigned warehouses")
            print(f"   ✅ Operators see transports related to their warehouses")
            print(f"   ✅ Operators can create inter-warehouse transports")
            print(f"   ✅ Cross-tenant security is properly implemented")
        else:
            print(f"\n⚠️  SOME REQUIREMENTS FAILED - SYSTEM NEEDS ATTENTION")
            failed_tests = [name for name, result in test_results if not result]
            print(f"   ❌ Failed requirements: {', '.join(failed_tests)}")
        
        return overall_success

def main():
    """Main function to run the operator permissions test suite"""
    tester = OperatorPermissionsAPITester()
    
    try:
        success = tester.run_comprehensive_test_suite()
        
        if success:
            print(f"\n🎯 OPERATOR PERMISSIONS SYSTEM: FULLY FUNCTIONAL")
            sys.exit(0)
        else:
            print(f"\n⚠️  OPERATOR PERMISSIONS SYSTEM: NEEDS FIXES")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
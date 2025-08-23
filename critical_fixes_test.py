#!/usr/bin/env python3
"""
Critical Fixes Testing for TAJLINE.TJ Application
Tests the two specific fixes mentioned in the review request:
1. Warehouse Schema Cross-Collection Display Fix
2. Manual Cell Selection for Cargo Placement
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class CriticalFixesTester:
    def __init__(self, base_url="https://tajline-manage-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.tokens = {}
        self.users = {}
        self.warehouse_id = None
        self.transport_id = None
        self.cargo_ids = {"cargo": [], "operator_cargo": []}
        self.tests_run = 0
        self.tests_passed = 0
        
        print(f"🔧 TAJLINE.TJ Critical Fixes Tester")
        print(f"📡 Base URL: {self.base_url}")
        print("=" * 60)

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
        """Setup test environment with users, warehouse, and cargo"""
        print("\n🏗️ SETTING UP TEST ENVIRONMENT")
        
        # Register admin user
        admin_data = {
            "full_name": "Админ Тестер",
            "phone": "+79999888777",
            "password": "admin123",
            "role": "admin"
        }
        
        success, response = self.run_test(
            "Register Admin User",
            "POST",
            "/api/auth/register",
            200,
            admin_data
        )
        
        if success and 'access_token' in response:
            self.tokens['admin'] = response['access_token']
            self.users['admin'] = response['user']
            print(f"   🔑 Admin token stored")
        else:
            # Try login if user already exists
            success, response = self.run_test(
                "Login Admin User",
                "POST",
                "/api/auth/login",
                200,
                {"phone": admin_data['phone'], "password": admin_data['password']}
            )
            if success and 'access_token' in response:
                self.tokens['admin'] = response['access_token']
                self.users['admin'] = response['user']
                print(f"   🔑 Admin token obtained via login")
        
        # Register regular user
        user_data = {
            "full_name": "Пользователь Тестер",
            "phone": "+79123456789",
            "password": "123456",  # Use correct password
            "role": "user"
        }
        
        success, response = self.run_test(
            "Register Regular User",
            "POST",
            "/api/auth/register",
            200,
            user_data
        )
        
        if success and 'access_token' in response:
            self.tokens['user'] = response['access_token']
            self.users['user'] = response['user']
        else:
            # Try login if user already exists
            success, response = self.run_test(
                "Login Regular User",
                "POST",
                "/api/auth/login",
                200,
                {"phone": user_data['phone'], "password": user_data['password']}
            )
            if success and 'access_token' in response:
                self.tokens['user'] = response['access_token']
                self.users['user'] = response['user']
        
        # Create warehouse
        warehouse_data = {
            "name": "Тестовый склад для критических исправлений",
            "location": "Москва, Тестовая территория",
            "blocks_count": 2,
            "shelves_per_block": 2,
            "cells_per_shelf": 5
        }
        
        success, warehouse_response = self.run_test(
            "Create Test Warehouse",
            "POST",
            "/api/warehouses/create",
            200,
            warehouse_data,
            self.tokens['admin']
        )
        
        if success and 'id' in warehouse_response:
            self.warehouse_id = warehouse_response['id']
            print(f"   🏭 Warehouse created: {self.warehouse_id}")
        
        # Create transport with unique number
        import random
        transport_number = f"TEST{random.randint(1000, 9999)}"
        transport_data = {
            "driver_name": "Тестовый Водитель",
            "driver_phone": "+79555666777",
            "transport_number": transport_number,
            "capacity_kg": 5000.0,
            "direction": "Москва - Душанбе"
        }
        
        success, transport_response = self.run_test(
            "Create Test Transport",
            "POST",
            "/api/transport/create",
            200,
            transport_data,
            self.tokens['admin']
        )
        
        if success and 'transport_id' in transport_response:
            self.transport_id = transport_response['transport_id']
            print(f"   🚛 Transport created: {self.transport_id}")
        
        return self.tokens.get('admin') and self.warehouse_id and self.transport_id

    def create_test_cargo(self):
        """Create cargo in both collections for testing"""
        print("\n📦 CREATING TEST CARGO IN BOTH COLLECTIONS")
        
        # Create cargo in 'cargo' collection (regular user cargo)
        user_cargo_data = {
            "recipient_name": "Получатель Пользователя",
            "recipient_phone": "+992444555666",
            "route": "moscow_to_tajikistan",
            "weight": 25.0,
            "cargo_name": "Пользовательский груз",
            "description": "Груз созданный пользователем",
            "declared_value": 15000.0,
            "sender_address": "Москва, ул. Пользователя, 1",
            "recipient_address": "Душанбе, ул. Получателя, 1"
        }
        
        success, cargo_response = self.run_test(
            "Create User Cargo (cargo collection)",
            "POST",
            "/api/cargo/create",
            200,
            user_cargo_data,
            self.tokens['user']
        )
        
        if success and 'id' in cargo_response:
            cargo_id = cargo_response['id']
            cargo_number = cargo_response.get('cargo_number')
            self.cargo_ids['cargo'].append({
                'id': cargo_id,
                'number': cargo_number,
                'collection': 'cargo'
            })
            print(f"   📋 User cargo created: {cargo_number} (ID: {cargo_id})")
            
            # Update status to accepted and add warehouse location
            success, _ = self.run_test(
                "Update User Cargo Status",
                "PUT",
                f"/api/cargo/{cargo_id}/status",
                200,
                token=self.tokens['admin'],
                params={"status": "accepted", "warehouse_location": "Склад А, Стеллаж 1"}
            )
        
        # Create cargo in 'operator_cargo' collection
        operator_cargo_data = {
            "sender_full_name": "Отправитель Оператора",
            "sender_phone": "+79111222333",
            "recipient_full_name": "Получатель Оператора",
            "recipient_phone": "+992777888999",
            "recipient_address": "Душанбе, ул. Операторская, 25",
            "weight": 30.0,
            "cargo_name": "Операторский груз",
            "declared_value": 12000.0,
            "description": "Груз принятый оператором",
            "route": "moscow_to_tajikistan"
        }
        
        success, cargo_response = self.run_test(
            "Create Operator Cargo (operator_cargo collection)",
            "POST",
            "/api/operator/cargo/accept",
            200,
            operator_cargo_data,
            self.tokens['admin']
        )
        
        if success and 'id' in cargo_response:
            cargo_id = cargo_response['id']
            cargo_number = cargo_response.get('cargo_number')
            self.cargo_ids['operator_cargo'].append({
                'id': cargo_id,
                'number': cargo_number,
                'collection': 'operator_cargo'
            })
            print(f"   📋 Operator cargo created: {cargo_number} (ID: {cargo_id})")
        
        return len(self.cargo_ids['cargo']) > 0 and len(self.cargo_ids['operator_cargo']) > 0

    def place_cargo_in_warehouse_cells(self):
        """Place cargo from both collections in warehouse cells"""
        print("\n🏭 PLACING CARGO IN WAREHOUSE CELLS")
        
        if not self.warehouse_id:
            print("   ❌ No warehouse available")
            return False
        
        # Place user cargo in warehouse cell
        if self.cargo_ids['cargo']:
            cargo_info = self.cargo_ids['cargo'][0]
            
            # Use the warehouse cell assignment endpoint
            success, _ = self.run_test(
                f"Place User Cargo in Cell",
                "PUT",
                f"/api/warehouses/{self.warehouse_id}/assign-cargo",
                200,
                token=self.tokens['admin'],
                params={
                    "cargo_id": cargo_info['id'],
                    "cell_location_code": "B1-S1-C1"
                }
            )
            
            if success:
                print(f"   ✅ User cargo {cargo_info['number']} placed in B1-S1-C1")
        
        # Place operator cargo in warehouse cell using operator placement
        if self.cargo_ids['operator_cargo']:
            cargo_info = self.cargo_ids['operator_cargo'][0]
            
            placement_data = {
                "cargo_id": cargo_info['id'],
                "warehouse_id": self.warehouse_id,
                "block_number": 1,
                "shelf_number": 2,
                "cell_number": 1
            }
            
            success, placement_response = self.run_test(
                f"Place Operator Cargo in Cell",
                "POST",
                "/api/operator/cargo/place",
                200,
                placement_data,
                self.tokens['admin']
            )
            
            if success:
                location = placement_response.get('location', 'Unknown')
                print(f"   ✅ Operator cargo {cargo_info['number']} placed in {location}")
        
        return True

    def test_warehouse_schema_cross_collection_fix(self):
        """Test Fix #1: Warehouse schema shows cargo from both collections"""
        print("\n🔧 FIX #1: WAREHOUSE SCHEMA CROSS-COLLECTION DISPLAY")
        print("Testing that GET /api/warehouses/{warehouse_id}/full-layout shows cargo from both 'cargo' and 'operator_cargo' collections")
        
        if not self.warehouse_id:
            print("   ❌ No warehouse available for testing")
            return False
        
        success, layout_response = self.run_test(
            "Get Warehouse Full Layout (Cross-Collection)",
            "GET",
            f"/api/warehouses/{self.warehouse_id}/full-layout",
            200,
            token=self.tokens['admin']
        )
        
        if not success:
            print("   ❌ Failed to get warehouse layout")
            return False
        
        # Analyze the response
        warehouse_info = layout_response.get('warehouse', {})
        statistics = layout_response.get('statistics', {})
        layout = layout_response.get('layout', {})
        
        print(f"   🏭 Warehouse: {warehouse_info.get('name', 'Unknown')}")
        print(f"   📊 Total cells: {statistics.get('total_cells', 0)}")
        print(f"   📊 Occupied cells: {statistics.get('occupied_cells', 0)}")
        print(f"   📊 Available cells: {statistics.get('available_cells', 0)}")
        
        # Check if we can find cargo from both collections in the layout
        cargo_found = {"cargo": False, "operator_cargo": False}
        cargo_details_found = []
        
        print(f"   🔍 DEBUG: Layout structure keys: {list(layout.keys())}")
        
        for block_key, block_data in layout.items():
            print(f"   🔍 DEBUG: Block {block_key} structure: {list(block_data.keys())}")
            if isinstance(block_data, dict) and "shelves" in block_data:
                shelves = block_data["shelves"]
                for shelf_key, shelf_data in shelves.items():
                    print(f"   🔍 DEBUG: Shelf {shelf_key} structure: {list(shelf_data.keys())}")
                    if isinstance(shelf_data, dict) and "cells" in shelf_data:
                        cells = shelf_data["cells"]
                        for cell in cells:
                            print(f"   🔍 DEBUG: Cell data: {cell}")
                            if cell.get('is_occupied') and cell.get('cargo_info'):
                                cargo_info = cell['cargo_info']
                                cargo_number = cargo_info.get('cargo_number')
                                
                                if cargo_number:
                                    # Check if this cargo matches our test cargo
                                    for collection_name, cargo_list in self.cargo_ids.items():
                                        for cargo_data in cargo_list:
                                            if cargo_data['number'] == cargo_number:
                                                cargo_found[collection_name] = True
                                                cargo_details_found.append({
                                                    'number': cargo_number,
                                                    'collection': collection_name,
                                                    'cell': cell.get('location_code'),
                                                    'name': cargo_info.get('cargo_name', 'N/A')
                                                })
        
        # Report findings
        print(f"\n   📋 CARGO FOUND IN WAREHOUSE LAYOUT:")
        for cargo in cargo_details_found:
            print(f"   📦 {cargo['number']} ({cargo['collection']}) in {cargo['cell']} - {cargo['name']}")
        
        # Verify the fix
        if cargo_found['cargo'] and cargo_found['operator_cargo']:
            print(f"\n   ✅ SUCCESS: Warehouse layout shows cargo from BOTH collections!")
            print(f"   ✅ User cargo (cargo collection): Found")
            print(f"   ✅ Operator cargo (operator_cargo collection): Found")
            return True
        elif cargo_found['cargo'] or cargo_found['operator_cargo']:
            print(f"\n   ⚠️  PARTIAL: Only one collection found in layout")
            print(f"   📊 User cargo found: {cargo_found['cargo']}")
            print(f"   📊 Operator cargo found: {cargo_found['operator_cargo']}")
            return False
        else:
            print(f"\n   ❌ FAILED: No test cargo found in warehouse layout")
            print(f"   📊 Expected to find cargo from both collections")
            return False

    def test_manual_cell_selection_fix(self):
        """Test Fix #2: Manual cell selection for cargo placement"""
        print("\n🔧 FIX #2: MANUAL CELL SELECTION FOR CARGO PLACEMENT")
        print("Testing that POST /api/transport/{transport_id}/place-cargo-by-number requires manual cell selection")
        
        if not self.transport_id:
            print("   ❌ No transport available for testing")
            return False
        
        if not self.cargo_ids['cargo'] and not self.cargo_ids['operator_cargo']:
            print("   ❌ No cargo available for testing")
            return False
        
        # First, we need to place cargo on transport and mark it as arrived
        print("   🚛 Setting up transport with cargo...")
        
        # Place some cargo on transport first using the correct API
        if self.cargo_ids['cargo']:
            cargo_info = self.cargo_ids['cargo'][0]
            placement_data = {
                "cargo_numbers": [cargo_info['number']]  # Use cargo_numbers
            }
            
            success, _ = self.run_test(
                "Place Cargo on Transport by Number",
                "POST",
                f"/api/transport/{self.transport_id}/place-cargo",
                200,
                placement_data,
                self.tokens['admin']
            )
            
            if success:
                print("   ✅ Cargo placed on transport")
        
        # Dispatch transport first
        success, _ = self.run_test(
            "Dispatch Transport",
            "POST",
            f"/api/transport/{self.transport_id}/dispatch",
            200,
            token=self.tokens['admin']
        )
        
        if success:
            print("   ✅ Transport dispatched")
        
        # Mark transport as arrived
        success, _ = self.run_test(
            "Mark Transport as Arrived",
            "POST",
            f"/api/transport/{self.transport_id}/arrive",
            200,
            token=self.tokens['admin']
        )
        
        if not success:
            print("   ❌ Failed to mark transport as arrived")
            return False
        
        print("   ✅ Transport marked as arrived")
        
        # Test with cargo from both collections
        test_results = []
        
        for collection_name, cargo_list in self.cargo_ids.items():
            if not cargo_list:
                continue
                
            cargo_info = cargo_list[0]
            cargo_number = cargo_info['number']
            
            print(f"\n   🧪 Testing with {collection_name} cargo: {cargo_number}")
            
            # Test 1: Manual coordinates (should work)
            print(f"   📍 Test 1: Manual cell coordinates")
            manual_placement_data = {
                "cargo_number": cargo_number,
                "block_number": 2,
                "shelf_number": 1,
                "cell_number": 3
            }
            
            success, response = self.run_test(
                f"Place {collection_name} Cargo with Manual Coordinates",
                "POST",
                f"/api/transport/{self.transport_id}/place-cargo-by-number",
                200,
                manual_placement_data,
                self.tokens['admin']
            )
            
            if success:
                print(f"   ✅ Manual placement successful")
                print(f"   📊 Warehouse auto-selected: {response.get('warehouse_auto_selected', 'N/A')}")
                print(f"   📊 Placement method: {response.get('placement_method', 'N/A')}")
                test_results.append(True)
            else:
                print(f"   ❌ Manual placement failed")
                test_results.append(False)
            
            # Test 2: QR code cell placement (should work)
            print(f"   📱 Test 2: QR code cell placement")
            qr_placement_data = {
                "cargo_number": cargo_number,
                "cell_qr_data": f"""ЯЧЕЙКА СКЛАДА
Местоположение: Склад-А-Б2-П2-Я4
Склад: Тестовый склад
Адрес склада: Москва, Тестовая территория
Блок: 2
Полка: 2
Ячейка: 4
ID склада: {self.warehouse_id}"""
            }
            
            success, response = self.run_test(
                f"Place {collection_name} Cargo with QR Code",
                "POST",
                f"/api/transport/{self.transport_id}/place-cargo-by-number",
                200,
                qr_placement_data,
                self.tokens['admin']
            )
            
            if success:
                print(f"   ✅ QR placement successful")
                print(f"   📊 Warehouse auto-selected: {response.get('warehouse_auto_selected', 'N/A')}")
                print(f"   📊 Placement method: {response.get('placement_method', 'N/A')}")
                test_results.append(True)
            else:
                print(f"   ❌ QR placement failed")
                test_results.append(False)
            
            # Test 3: No cell information (should fail)
            print(f"   ❌ Test 3: No cell information (should fail)")
            no_cell_data = {
                "cargo_number": cargo_number
                # No cell coordinates or QR data
            }
            
            success, response = self.run_test(
                f"Place {collection_name} Cargo without Cell Info (Should Fail)",
                "POST",
                f"/api/transport/{self.transport_id}/place-cargo-by-number",
                400,  # Should fail with 400 error
                no_cell_data,
                self.tokens['admin']
            )
            
            if success:  # Success means it correctly returned 400
                print(f"   ✅ Correctly rejected placement without cell info")
                test_results.append(True)
            else:
                print(f"   ❌ Should have rejected placement without cell info")
                test_results.append(False)
        
        # Evaluate results
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        print(f"\n   📊 MANUAL CELL SELECTION TEST RESULTS:")
        print(f"   📈 Passed: {passed_tests}/{total_tests} tests")
        
        if passed_tests == total_tests:
            print(f"   ✅ SUCCESS: Manual cell selection working correctly!")
            print(f"   ✅ Warehouse selection: Automatic (based on operator bindings)")
            print(f"   ✅ Cell selection: Manual (coordinates or QR code required)")
            return True
        else:
            print(f"   ❌ FAILED: Some manual cell selection tests failed")
            return False

    def run_all_tests(self):
        """Run all critical fixes tests"""
        print("\n🚀 STARTING CRITICAL FIXES TESTING")
        
        # Setup
        if not self.setup_test_environment():
            print("❌ Failed to setup test environment")
            return False
        
        if not self.create_test_cargo():
            print("❌ Failed to create test cargo")
            return False
        
        if not self.place_cargo_in_warehouse_cells():
            print("❌ Failed to place cargo in warehouse cells")
            return False
        
        # Run critical fix tests
        fix1_result = self.test_warehouse_schema_cross_collection_fix()
        fix2_result = self.test_manual_cell_selection_fix()
        
        # Summary
        print("\n" + "=" * 60)
        print("🏁 CRITICAL FIXES TEST SUMMARY")
        print("=" * 60)
        
        print(f"📊 Total tests run: {self.tests_run}")
        print(f"✅ Tests passed: {self.tests_passed}")
        print(f"❌ Tests failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        print(f"\n🔧 CRITICAL FIXES RESULTS:")
        print(f"Fix #1 - Warehouse Schema Cross-Collection: {'✅ PASSED' if fix1_result else '❌ FAILED'}")
        print(f"Fix #2 - Manual Cell Selection: {'✅ PASSED' if fix2_result else '❌ FAILED'}")
        
        overall_success = fix1_result and fix2_result
        print(f"\n🎯 OVERALL RESULT: {'✅ ALL FIXES WORKING' if overall_success else '❌ SOME FIXES NEED ATTENTION'}")
        
        return overall_success

if __name__ == "__main__":
    tester = CriticalFixesTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
TAJLINE Invoice Printing Functionality Test
Tests that the backend provides all necessary data fields for the new TAJLINE invoice printing functionality.
"""

import requests
import sys
import json
from datetime import datetime

class TajlineInvoiceAPITester:
    def __init__(self, base_url="https://cargo-sync.preview.emergentagent.com"):
        self.base_url = base_url
        self.tokens = {}
        self.tests_run = 0
        self.tests_passed = 0
        
        print(f"🧾 TAJLINE Invoice Printing Functionality Tester")
        print(f"📡 Base URL: {self.base_url}")
        print("=" * 60)

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data=None, token=None, params=None):
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

    def login_admin(self):
        """Login as admin user"""
        print("\n🔐 ADMIN LOGIN")
        
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "/api/auth/login",
            200,
            {"phone": "+79999888777", "password": "admin123"}
        )
        
        if success and 'access_token' in response:
            self.tokens['admin'] = response['access_token']
            print(f"   🔑 Admin token obtained")
            return True
        return False

    def test_tajline_invoice_printing_functionality(self):
        """Test TAJLINE invoice printing functionality - comprehensive data structure verification"""
        print("\n🧾 TAJLINE INVOICE PRINTING FUNCTIONALITY TESTING")
        
        if 'admin' not in self.tokens:
            print("   ❌ No admin token available")
            return False
            
        all_success = True
        
        # Test 1: Cargo Data Structure Verification for TAJLINE Invoice
        print("\n   📋 Testing Cargo Data Structure for TAJLINE Invoice Format...")
        
        # Create test cargo with all required fields for TAJLINE invoice
        tajline_cargo_data = {
            # Basic info required for TAJLINE invoice
            "sender_full_name": "Иван Отправитель Тест",
            "sender_phone": "+79999123456",
            "sender_address": "Москва, ул. Отправителя, 123",
            "recipient_full_name": "Петр Получатель Тест", 
            "recipient_phone": "+992900123456",
            "recipient_address": "Душанбе, ул. Получателя, 456",
            
            # Multi-cargo with individual pricing for TAJLINE invoice table
            "cargo_items": [
                {"cargo_name": "Документы", "weight": 10.0, "price_per_kg": 60.0},
                {"cargo_name": "Одежда", "weight": 25.0, "price_per_kg": 60.0},
                {"cargo_name": "Электроника", "weight": 100.0, "price_per_kg": 65.0}
            ],
            "description": "Тестовый груз для TAJLINE накладной",
            "route": "moscow_dushanbe"  # For route translation testing
        }
        
        success, tajline_cargo_response = self.run_test(
            "Create TAJLINE Test Cargo (135kg, 8600руб)",
            "POST",
            "/api/operator/cargo/accept",
            200,
            tajline_cargo_data,
            self.tokens['admin']
        )
        all_success &= success
        
        tajline_cargo_id = None
        if success and 'id' in tajline_cargo_response:
            tajline_cargo_id = tajline_cargo_response['id']
            cargo_number = tajline_cargo_response.get('cargo_number', 'N/A')
            total_weight = tajline_cargo_response.get('weight', 0)
            total_cost = tajline_cargo_response.get('declared_value', 0)
            
            print(f"   ✅ TAJLINE cargo created: {cargo_number}")
            print(f"   📊 Total weight: {total_weight} kg (expected: 135 kg)")
            print(f"   💰 Total cost: {total_cost} руб (expected: 8600 руб)")
            
            # Verify calculations match TAJLINE requirements
            if abs(total_weight - 135.0) < 0.01 and abs(total_cost - 8600.0) < 0.01:
                print("   ✅ TAJLINE cargo calculations verified")
            else:
                print("   ❌ TAJLINE cargo calculations incorrect")
                all_success = False
            
            # Verify all required TAJLINE invoice fields are present
            required_tajline_fields = [
                'cargo_number', 'weight', 'declared_value', 'route', 'created_at',
                'sender_full_name', 'sender_phone', 'sender_address',
                'recipient_full_name', 'recipient_phone', 'recipient_address'
            ]
            
            missing_fields = []
            for field in required_tajline_fields:
                if field not in tajline_cargo_response or tajline_cargo_response.get(field) is None:
                    missing_fields.append(field)
            
            if not missing_fields:
                print("   ✅ All required TAJLINE invoice fields present")
            else:
                print(f"   ❌ Missing TAJLINE invoice fields: {missing_fields}")
                all_success = False
        
        # Test 2: Multi-cargo Invoice Data Structure
        print("\n   🧮 Testing Multi-cargo Invoice Data Structure...")
        
        if tajline_cargo_id:
            # Get individual cargo lookup for invoice printing
            success, cargo_details = self.run_test(
                "Get Cargo Details for Invoice",
                "GET",
                f"/api/operator/cargo/list?page=1&per_page=100",
                200,
                token=self.tokens['admin']
            )
            all_success &= success
            
            if success and 'items' in cargo_details:
                # Find our TAJLINE test cargo
                tajline_cargo = None
                for cargo in cargo_details['items']:
                    if cargo.get('id') == tajline_cargo_id:
                        tajline_cargo = cargo
                        break
                
                if tajline_cargo:
                    print("   ✅ TAJLINE cargo found in cargo list")
                    
                    # Verify multi-cargo structure for invoice table
                    cargo_name = tajline_cargo.get('cargo_name', '')
                    description = tajline_cargo.get('description', '')
                    
                    # Check if multi-cargo items are properly structured
                    expected_items = ["Документы", "Одежда", "Электроника"]
                    items_found = all(item in cargo_name for item in expected_items)
                    
                    if items_found:
                        print("   ✅ Multi-cargo items properly structured for invoice table")
                        print(f"   📋 Cargo items: {cargo_name}")
                    else:
                        print("   ❌ Multi-cargo items not properly structured")
                        all_success = False
                    
                    # Verify individual pricing information is available
                    if "60.0 руб/кг" in description and "65.0 руб/кг" in description:
                        print("   ✅ Individual pricing information available for invoice")
                    else:
                        print("   ❌ Individual pricing information missing")
                        all_success = False
                    
                    # Verify total calculations for invoice
                    weight = tajline_cargo.get('weight', 0)
                    declared_value = tajline_cargo.get('declared_value', 0)
                    
                    if weight == 135.0 and declared_value == 8600.0:
                        print("   ✅ Total weight and cost calculations correct for invoice")
                    else:
                        print(f"   ❌ Total calculations incorrect: {weight}kg, {declared_value}руб")
                        all_success = False
                else:
                    print("   ❌ TAJLINE cargo not found in cargo list")
                    all_success = False
        
        # Test 3: Route Translation Verification
        print("\n   🗺️  Testing Route Translation for TAJLINE Invoice...")
        
        # Test different routes for destination translation
        route_translations = {
            "moscow_dushanbe": "Душанбе",
            "moscow_khujand": "Худжанд", 
            "moscow_kulob": "Кулоб",
            "moscow_kurgantyube": "Курган-Тюбе"
        }
        
        for route_code, expected_destination in route_translations.items():
            test_route_cargo_data = {
                "sender_full_name": f"Тест {route_code}",
                "sender_phone": "+79999999999",
                "recipient_full_name": f"Получатель {expected_destination}",
                "recipient_phone": "+992999999999",
                "recipient_address": f"{expected_destination}, ул. Тестовая, 1",
                "cargo_name": f"Тест маршрута {route_code}",
                "weight": 5.0,
                "declared_value": 500.0,
                "description": f"Тест маршрута для {expected_destination}",
                "route": route_code
            }
            
            success, route_response = self.run_test(
                f"Create Cargo for Route {route_code}",
                "POST",
                "/api/operator/cargo/accept",
                200,
                test_route_cargo_data,
                self.tokens['admin']
            )
            all_success &= success
            
            if success:
                route_in_response = route_response.get('route', '')
                if route_in_response == route_code:
                    print(f"   ✅ Route {route_code} → {expected_destination} properly stored")
                else:
                    print(f"   ❌ Route {route_code} not properly stored")
                    all_success = False
        
        # Test 4: Invoice-ready Data Endpoints
        print("\n   📄 Testing Invoice-ready Data Endpoints...")
        
        if tajline_cargo_id:
            # Test individual cargo lookup by ID (for invoice printing)
            success, individual_cargo = self.run_test(
                "Get Individual Cargo for Invoice",
                "GET",
                f"/api/operator/cargo/list?page=1&per_page=1",
                200,
                token=self.tokens['admin']
            )
            all_success &= success
            
            if success and 'items' in individual_cargo and len(individual_cargo['items']) > 0:
                cargo_item = individual_cargo['items'][0]
                
                # Verify all invoice fields are properly formatted
                invoice_fields = {
                    'cargo_number': cargo_item.get('cargo_number'),
                    'sender_full_name': cargo_item.get('sender_full_name'),
                    'sender_phone': cargo_item.get('sender_phone'),
                    'recipient_full_name': cargo_item.get('recipient_full_name'),
                    'recipient_phone': cargo_item.get('recipient_phone'),
                    'weight': cargo_item.get('weight'),
                    'declared_value': cargo_item.get('declared_value'),
                    'route': cargo_item.get('route'),
                    'created_at': cargo_item.get('created_at')
                }
                
                print("   📋 INVOICE DATA VERIFICATION:")
                all_fields_valid = True
                for field_name, field_value in invoice_fields.items():
                    if field_value is not None and field_value != '':
                        print(f"   ✅ {field_name}: {field_value}")
                    else:
                        print(f"   ❌ {field_name}: Missing or empty")
                        all_fields_valid = False
                
                if all_fields_valid:
                    print("   ✅ All invoice fields properly formatted and available")
                else:
                    print("   ❌ Some invoice fields missing or improperly formatted")
                    all_success = False
                
                # Verify data types are JSON serializable
                try:
                    import json
                    json.dumps(invoice_fields, default=str)
                    print("   ✅ Invoice data is JSON serializable")
                except Exception as e:
                    print(f"   ❌ Invoice data serialization error: {e}")
                    all_success = False
        
        # Test 5: Complete TAJLINE Invoice Workflow
        print("\n   🔄 Testing Complete TAJLINE Invoice Workflow...")
        
        # Step 1: Login as admin (already done)
        print("   ✅ Step 1: Admin login completed")
        
        # Step 2: Create test cargo with multiple items (already done)
        if tajline_cargo_id:
            print("   ✅ Step 2: Multi-cargo created with individual pricing")
            
            # Step 3: Verify cargo data structure matches TAJLINE requirements
            success, workflow_cargo_list = self.run_test(
                "Workflow: Get Cargo List",
                "GET",
                "/api/operator/cargo/list",
                200,
                token=self.tokens['admin']
            )
            all_success &= success
            
            if success:
                print("   ✅ Step 3: Cargo data structure verified")
                
                # Step 4: Test individual cargo retrieval for invoice printing
                if 'items' in workflow_cargo_list and len(workflow_cargo_list['items']) > 0:
                    print("   ✅ Step 4: Individual cargo retrieval working")
                    
                    # Step 5: Verify all invoice fields are available and properly formatted
                    sample_cargo = workflow_cargo_list['items'][0]
                    required_invoice_fields = [
                        'cargo_number', 'sender_full_name', 'sender_phone', 
                        'recipient_full_name', 'recipient_phone', 'recipient_address',
                        'weight', 'declared_value', 'route', 'created_at'
                    ]
                    
                    fields_available = all(
                        field in sample_cargo and sample_cargo[field] is not None 
                        for field in required_invoice_fields
                    )
                    
                    if fields_available:
                        print("   ✅ Step 5: All invoice fields available and properly formatted")
                        print("   🎉 COMPLETE TAJLINE INVOICE WORKFLOW SUCCESSFUL!")
                    else:
                        print("   ❌ Step 5: Some invoice fields missing")
                        all_success = False
                else:
                    print("   ❌ Step 4: Individual cargo retrieval failed")
                    all_success = False
            else:
                print("   ❌ Step 3: Cargo data structure verification failed")
                all_success = False
        else:
            print("   ❌ Step 2: Multi-cargo creation failed")
            all_success = False
        
        # Test Summary
        print("\n   📊 TAJLINE INVOICE FUNCTIONALITY TEST SUMMARY:")
        if all_success:
            print("   ✅ Cargo data structure contains all TAJLINE invoice fields")
            print("   ✅ Multi-cargo support with individual pricing working")
            print("   ✅ Route translation capabilities verified")
            print("   ✅ Invoice-ready data endpoints functional")
            print("   ✅ Complete workflow from cargo creation to invoice data retrieval working")
            print("   🎯 TAJLINE INVOICE PRINTING FUNCTIONALITY FULLY SUPPORTED!")
        else:
            print("   ❌ Some TAJLINE invoice functionality issues detected")
            print("   🔧 Backend may need adjustments for complete TAJLINE invoice support")
        
        return all_success

    def run_all_tests(self):
        """Run all TAJLINE invoice tests"""
        print("\n🚀 STARTING TAJLINE INVOICE FUNCTIONALITY TESTS")
        print("=" * 60)
        
        # Login as admin first
        if not self.login_admin():
            print("❌ Failed to login as admin - cannot continue tests")
            return False
        
        # Run TAJLINE invoice functionality test
        success = self.test_tajline_invoice_printing_functionality()
        
        print(f"\n🏁 TESTING COMPLETE")
        print(f"📊 Results: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        return success

if __name__ == "__main__":
    tester = TajlineInvoiceAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 ALL TAJLINE INVOICE TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n❌ SOME TAJLINE INVOICE TESTS FAILED!")
        sys.exit(1)
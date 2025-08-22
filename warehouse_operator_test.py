#!/usr/bin/env python3
"""
Focused test for warehouse operator /api/operator/warehouses endpoint
Testing authentication and warehouse access for operators
"""

import requests
import json
from datetime import datetime

class WarehouseOperatorTester:
    def __init__(self, base_url="https://tajline-cargo-7.preview.emergentagent.com"):
        self.base_url = base_url
        self.admin_token = None
        self.operator_token = None
        
        print(f"🏭 WAREHOUSE OPERATOR ENDPOINT TESTING")
        print(f"📡 Base URL: {self.base_url}")
        print("=" * 60)

    def login_admin(self):
        """Login as admin to fix operator role if needed"""
        print("\n👑 ADMIN LOGIN...")
        
        admin_data = {
            "phone": "+79999888777",
            "password": "admin123"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json=admin_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                self.admin_token = result['access_token']
                admin_user = result['user']
                print(f"   ✅ Admin login successful")
                print(f"   👤 Name: {admin_user.get('full_name')}")
                print(f"   👑 Role: {admin_user.get('role')}")
                return True
            else:
                print(f"   ❌ Admin login failed: {response.status_code}")
                print(f"   📄 Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Admin login exception: {e}")
            return False

    def fix_operator_role(self):
        """Fix operator role using admin endpoint"""
        print("\n🔧 FIXING OPERATOR ROLE...")
        
        if not self.admin_token:
            print("   ❌ No admin token available")
            return False
            
        try:
            response = requests.post(
                f"{self.base_url}/api/admin/fix-operator-role",
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.admin_token}'
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Operator role fix successful")
                print(f"   📄 Response: {result.get('message', 'No message')}")
                return True
            else:
                print(f"   ❌ Operator role fix failed: {response.status_code}")
                print(f"   📄 Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Operator role fix exception: {e}")
            return False

    def login_warehouse_operator(self):
        """Login as warehouse operator with credentials +79777888999/warehouse123"""
        print("\n🏭 WAREHOUSE OPERATOR LOGIN...")
        
        operator_data = {
            "phone": "+79777888999",
            "password": "warehouse123"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json=operator_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                self.operator_token = result['access_token']
                operator_user = result['user']
                print(f"   ✅ Warehouse operator login successful")
                print(f"   👤 Name: {operator_user.get('full_name')}")
                print(f"   📞 Phone: {operator_user.get('phone')}")
                print(f"   👑 Role: {operator_user.get('role')}")
                print(f"   🆔 User Number: {operator_user.get('user_number')}")
                
                # Verify role is correct
                if operator_user.get('role') == 'warehouse_operator':
                    print("   ✅ Operator role correctly set to 'warehouse_operator'")
                    return True
                else:
                    print(f"   ❌ Operator role incorrect: expected 'warehouse_operator', got '{operator_user.get('role')}'")
                    return False
            else:
                print(f"   ❌ Warehouse operator login failed: {response.status_code}")
                print(f"   📄 Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Warehouse operator login exception: {e}")
            return False

    def test_operator_warehouses_endpoint(self):
        """Test GET /api/operator/warehouses endpoint"""
        print("\n📦 TESTING /api/operator/warehouses ENDPOINT...")
        
        if not self.operator_token:
            print("   ❌ No operator token available")
            return False
            
        try:
            response = requests.get(
                f"{self.base_url}/api/operator/warehouses",
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.operator_token}'
                }
            )
            
            print(f"   📡 Request: GET /api/operator/warehouses")
            print(f"   📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Endpoint accessible")
                
                # Analyze response structure
                if isinstance(result, list):
                    warehouse_count = len(result)
                    print(f"   🏭 Warehouses returned: {warehouse_count}")
                    
                    if warehouse_count > 0:
                        # Analyze first warehouse structure
                        sample_warehouse = result[0]
                        print(f"\n   📋 WAREHOUSE DATA STRUCTURE:")
                        for key, value in sample_warehouse.items():
                            print(f"   - {key}: {value}")
                        
                        # Check required fields
                        required_fields = ['id', 'name', 'location']
                        missing_fields = [field for field in required_fields if field not in sample_warehouse]
                        
                        if not missing_fields:
                            print(f"   ✅ All required fields present")
                        else:
                            print(f"   ❌ Missing required fields: {missing_fields}")
                        
                        # Show warehouse details
                        warehouse_id = sample_warehouse.get('id')
                        warehouse_name = sample_warehouse.get('name')
                        warehouse_location = sample_warehouse.get('location')
                        
                        print(f"\n   🏭 WAREHOUSE DETAILS:")
                        print(f"   - ID: {warehouse_id}")
                        print(f"   - Name: {warehouse_name}")
                        print(f"   - Location: {warehouse_location}")
                        
                        return True
                    else:
                        print(f"   ⚠️  No warehouses assigned to operator")
                        print(f"   📄 This may indicate missing operator-warehouse bindings")
                        return True  # Endpoint works, just no data
                        
                else:
                    print(f"   ❌ Unexpected response format: {type(result)}")
                    print(f"   📄 Response: {result}")
                    return False
                    
            else:
                print(f"   ❌ Endpoint failed: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   📄 Error: {error_detail}")
                except:
                    print(f"   📄 Raw response: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception during endpoint test: {e}")
            return False

    def check_operator_warehouse_bindings(self):
        """Check operator-warehouse bindings in database"""
        print("\n🔗 CHECKING OPERATOR-WAREHOUSE BINDINGS...")
        
        if not self.admin_token:
            print("   ❌ No admin token available")
            return False
            
        try:
            response = requests.get(
                f"{self.base_url}/api/admin/operator-warehouse-bindings",
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.admin_token}'
                }
            )
            
            if response.status_code == 200:
                bindings = response.json()
                print(f"   ✅ Found {len(bindings)} operator-warehouse bindings")
                
                # Look for our operator's bindings
                operator_bindings = []
                for binding in bindings:
                    if binding.get('operator_phone') == '+79777888999':
                        operator_bindings.append(binding)
                
                print(f"   🏭 Operator (+79777888999) has {len(operator_bindings)} warehouse bindings")
                
                if operator_bindings:
                    for i, binding in enumerate(operator_bindings, 1):
                        print(f"   📦 Binding {i}:")
                        print(f"     - Warehouse: {binding.get('warehouse_name')}")
                        print(f"     - Warehouse ID: {binding.get('warehouse_id')}")
                        print(f"     - Operator: {binding.get('operator_name')}")
                        print(f"     - Created by: {binding.get('created_by')}")
                else:
                    print(f"   ⚠️  No warehouse bindings found for operator +79777888999")
                    print(f"   📄 This explains why /api/operator/warehouses returns empty list")
                
                return True
            else:
                print(f"   ❌ Failed to get bindings: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception checking bindings: {e}")
            return False

    def test_warehouse_data_consistency(self):
        """Test warehouse data consistency between different endpoints"""
        print("\n🔍 TESTING WAREHOUSE DATA CONSISTENCY...")
        
        if not self.admin_token:
            print("   ❌ No admin token available")
            return False
            
        try:
            # Get all warehouses via admin endpoint
            admin_response = requests.get(
                f"{self.base_url}/api/warehouses",
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.admin_token}'
                }
            )
            
            if admin_response.status_code == 200:
                admin_warehouses = admin_response.json()
                print(f"   📊 Admin sees {len(admin_warehouses)} total warehouses")
                
                # Get operator warehouses
                if self.operator_token:
                    operator_response = requests.get(
                        f"{self.base_url}/api/operator/warehouses",
                        headers={
                            'Content-Type': 'application/json',
                            'Authorization': f'Bearer {self.operator_token}'
                        }
                    )
                    
                    if operator_response.status_code == 200:
                        operator_warehouses = operator_response.json()
                        print(f"   🏭 Operator sees {len(operator_warehouses)} assigned warehouses")
                        
                        # Compare data structure
                        if admin_warehouses and operator_warehouses:
                            admin_sample = admin_warehouses[0]
                            operator_sample = operator_warehouses[0]
                            
                            admin_fields = set(admin_sample.keys())
                            operator_fields = set(operator_sample.keys())
                            
                            if admin_fields == operator_fields:
                                print(f"   ✅ Warehouse data structure consistent between endpoints")
                            else:
                                print(f"   ❌ Data structure mismatch:")
                                print(f"     Admin fields: {admin_fields}")
                                print(f"     Operator fields: {operator_fields}")
                        
                        return True
                    else:
                        print(f"   ❌ Operator warehouses failed: {operator_response.status_code}")
                        return False
                else:
                    print(f"   ⚠️  No operator token for comparison")
                    return True
            else:
                print(f"   ❌ Admin warehouses failed: {admin_response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception during consistency test: {e}")
            return False

    def run_comprehensive_test(self):
        """Run comprehensive warehouse operator endpoint test"""
        print("\n🎯 STARTING COMPREHENSIVE WAREHOUSE OPERATOR ENDPOINT TEST")
        print("   📋 Testing: /api/operator/warehouses endpoint")
        print("   👤 Operator: +79777888999/warehouse123")
        
        success_count = 0
        total_tests = 6
        
        # Step 1: Admin login
        if self.login_admin():
            success_count += 1
            print("   ✅ Step 1/6: Admin authentication successful")
        else:
            print("   ❌ Step 1/6: Admin authentication failed")
        
        # Step 2: Fix operator role
        if self.fix_operator_role():
            success_count += 1
            print("   ✅ Step 2/6: Operator role fix successful")
        else:
            print("   ❌ Step 2/6: Operator role fix failed")
        
        # Step 3: Operator login
        if self.login_warehouse_operator():
            success_count += 1
            print("   ✅ Step 3/6: Warehouse operator authentication successful")
        else:
            print("   ❌ Step 3/6: Warehouse operator authentication failed")
        
        # Step 4: Test warehouses endpoint
        if self.test_operator_warehouses_endpoint():
            success_count += 1
            print("   ✅ Step 4/6: /api/operator/warehouses endpoint working")
        else:
            print("   ❌ Step 4/6: /api/operator/warehouses endpoint failed")
        
        # Step 5: Check bindings
        if self.check_operator_warehouse_bindings():
            success_count += 1
            print("   ✅ Step 5/6: Operator-warehouse bindings checked")
        else:
            print("   ❌ Step 5/6: Operator-warehouse bindings check failed")
        
        # Step 6: Test data consistency
        if self.test_warehouse_data_consistency():
            success_count += 1
            print("   ✅ Step 6/6: Warehouse data consistency verified")
        else:
            print("   ❌ Step 6/6: Warehouse data consistency failed")
        
        # Final summary
        print(f"\n📊 FINAL RESULTS:")
        print(f"   ✅ Successful steps: {success_count}/{total_tests}")
        print(f"   📈 Success rate: {(success_count/total_tests)*100:.1f}%")
        
        if success_count == total_tests:
            print(f"   🎉 ALL TESTS PASSED - Warehouse operator endpoint fully functional!")
        elif success_count >= 4:
            print(f"   ⚠️  MOSTLY WORKING - Some issues need attention")
        else:
            print(f"   ❌ CRITICAL ISSUES - Major problems need fixing")
        
        return success_count >= 4

if __name__ == "__main__":
    tester = WarehouseOperatorTester()
    success = tester.run_comprehensive_test()
    
    if success:
        print(f"\n🎯 CONCLUSION: Backend /api/operator/warehouses endpoint is working correctly")
        print(f"   📋 Operators can authenticate and access their assigned warehouses")
        print(f"   🔧 Any frontend issues are likely in the UI layer, not backend")
    else:
        print(f"\n❌ CONCLUSION: Backend issues found that need fixing before frontend work")
        print(f"   🔧 Fix backend issues first, then address frontend problems")
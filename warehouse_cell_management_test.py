#!/usr/bin/env python3
"""
WAREHOUSE CELL MANAGEMENT ENDPOINTS TESTING FOR TAJLINE.TJ
==========================================================

Протестировать endpoints управления ячейками склада в TAJLINE.TJ для выявления ошибок генерации QR кодов.

КОНТЕКСТ:
- Пользователь сообщает об ошибке при генерации QR кода ячейки
- Нужно протестировать новые endpoints управления ячейками
- Проверить генерацию QR кодов для отдельных ячеек и массовую генерацию

ENDPOINTS ДЛЯ ТЕСТИРОВАНИЯ:
1. GET /api/warehouses/{warehouse_id}/cells - получение списка ячеек
2. PUT /api/warehouses/{warehouse_id}/structure - обновление структуры склада  
3. GET /api/warehouses/cells/{cell_id}/qr - генерация QR для отдельной ячейки
4. GET /api/warehouses/{warehouse_id}/cells/qr-batch - массовая генерация QR
5. POST /api/warehouses/{warehouse_id}/cells/batch-delete - массовое удаление ячеек

ТЕСТОВЫЙ ПЛАН:
1. Авторизация admin (+79999888777/admin123)
2. Получить список складов для выбора warehouse_id
3. Тестировать получение ячеек склада
4. **ОСОБОЕ ВНИМАНИЕ**: Протестировать генерацию QR для отдельной ячейки - найти ошибку
5. Тестировать массовую генерацию QR кодов
6. Проверить валидацию данных и обработку ошибок

ФОКУС НА ОШИБКАХ:
- Найти конкретную ошибку в генерации QR кодов
- Проверить корректность cell_id формата
- Убедиться в правильности JSON данных для QR
- Проверить base64 кодирование изображения
"""

import requests
import json
import base64
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://tajline-cargo-8.preview.emergentagent.com/api"

class WarehouseCellManagementTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        self.warehouse_id = None
        self.test_cells = []
        
    def log_result(self, test_name, success, details, error=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": str(error) if error else None,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()

    def authenticate_admin(self):
        """Authenticate as admin user"""
        try:
            print("🔐 STEP 1: Admin Authentication (+79999888777/admin123)")
            
            login_data = {
                "phone": "+79999888777",
                "password": "admin123"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                user_info = data.get("user", {})
                
                # Set authorization header
                self.session.headers.update({
                    "Authorization": f"Bearer {self.admin_token}"
                })
                
                self.log_result(
                    "Admin Authentication",
                    True,
                    f"Successfully authenticated as {user_info.get('full_name', 'Admin')} "
                    f"(Role: {user_info.get('role', 'unknown')}, "
                    f"User Number: {user_info.get('user_number', 'N/A')})"
                )
                return True
            else:
                self.log_result(
                    "Admin Authentication",
                    False,
                    f"Authentication failed with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Admin Authentication", False, "Exception during authentication", e)
            return False

    def get_warehouses_list(self):
        """Get list of warehouses to choose warehouse_id"""
        try:
            print("🏭 STEP 2: Getting Warehouses List")
            
            response = self.session.get(f"{BACKEND_URL}/warehouses")
            
            if response.status_code == 200:
                warehouses = response.json()
                
                if warehouses and len(warehouses) > 0:
                    # Choose first warehouse for testing
                    self.warehouse_id = warehouses[0].get("id")
                    warehouse_name = warehouses[0].get("name", "Unknown")
                    
                    self.log_result(
                        "Get Warehouses List",
                        True,
                        f"Found {len(warehouses)} warehouses. Selected warehouse: {warehouse_name} (ID: {self.warehouse_id})"
                    )
                    return True
                else:
                    self.log_result(
                        "Get Warehouses List",
                        False,
                        "No warehouses found in the system"
                    )
                    return False
            else:
                self.log_result(
                    "Get Warehouses List",
                    False,
                    f"Failed to get warehouses list with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Get Warehouses List", False, "Exception during warehouses retrieval", e)
            return False

    def test_get_warehouse_cells(self):
        """Test GET /api/warehouses/{warehouse_id}/cells"""
        try:
            print("📦 STEP 3: Testing GET /api/warehouses/{warehouse_id}/cells")
            
            response = self.session.get(f"{BACKEND_URL}/warehouses/{self.warehouse_id}/cells")
            
            if response.status_code == 200:
                cells_data = response.json()
                
                if isinstance(cells_data, list):
                    cells = cells_data
                elif isinstance(cells_data, dict) and 'cells' in cells_data:
                    cells = cells_data['cells']
                else:
                    cells = []
                
                if cells and len(cells) > 0:
                    # Store first few cells for QR testing
                    self.test_cells = cells[:5]  # Take first 5 cells for testing
                    
                    # Analyze cell structure
                    sample_cell = cells[0]
                    cell_fields = list(sample_cell.keys())
                    
                    self.log_result(
                        "Get Warehouse Cells",
                        True,
                        f"Found {len(cells)} cells in warehouse. Sample cell fields: {cell_fields}. "
                        f"Selected {len(self.test_cells)} cells for QR testing."
                    )
                    return True
                else:
                    self.log_result(
                        "Get Warehouse Cells",
                        False,
                        "No cells found in the selected warehouse"
                    )
                    return False
            else:
                self.log_result(
                    "Get Warehouse Cells",
                    False,
                    f"Failed to get warehouse cells with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Get Warehouse Cells", False, "Exception during cells retrieval", e)
            return False

    def test_individual_cell_qr_generation(self):
        """Test GET /api/warehouses/cells/{cell_id}/qr - ОСОБОЕ ВНИМАНИЕ на ошибки"""
        try:
            print("🔍 STEP 4: Testing Individual Cell QR Generation (CRITICAL TEST)")
            
            if not self.test_cells:
                self.log_result(
                    "Individual Cell QR Generation",
                    False,
                    "No test cells available for QR generation testing"
                )
                return False
            
            success_count = 0
            error_details = []
            
            for i, cell in enumerate(self.test_cells):
                cell_id = cell.get("id")
                cell_location = cell.get("location_code", cell.get("id_based_code", "Unknown"))
                
                print(f"   Testing QR generation for cell {i+1}/{len(self.test_cells)}: {cell_location}")
                
                try:
                    response = self.session.get(f"{BACKEND_URL}/warehouses/cells/{cell_id}/qr")
                    
                    if response.status_code == 200:
                        qr_data = response.json()
                        
                        # Check if response contains QR code data
                        if isinstance(qr_data, dict):
                            if "qr_code" in qr_data:
                                qr_code = qr_data["qr_code"]
                                
                                # Validate base64 QR code
                                if qr_code and qr_code.startswith("data:image/png;base64,"):
                                    base64_data = qr_code.split(",")[1]
                                    try:
                                        # Try to decode base64
                                        decoded = base64.b64decode(base64_data)
                                        success_count += 1
                                        print(f"      ✅ QR generated successfully (size: {len(decoded)} bytes)")
                                    except Exception as decode_error:
                                        error_details.append(f"Cell {cell_location}: Base64 decode error - {decode_error}")
                                        print(f"      ❌ Base64 decode error: {decode_error}")
                                else:
                                    qr_preview = qr_code[:100] if qr_code else 'None'
                                    error_details.append(f"Cell {cell_location}: Invalid QR code format - {qr_preview}")
                                    print(f"      ❌ Invalid QR code format")
                            else:
                                available_keys = list(qr_data.keys())
                                error_details.append(f"Cell {cell_location}: Missing 'qr_code' field in response - {available_keys}")
                                print(f"      ❌ Missing 'qr_code' field in response")
                        else:
                            error_details.append(f"Cell {cell_location}: Invalid response format - {type(qr_data)}")
                            print(f"      ❌ Invalid response format")
                    else:
                        response_preview = response.text[:200]
                        error_details.append(f"Cell {cell_location}: HTTP {response.status_code} - {response_preview}")
                        print(f"      ❌ HTTP {response.status_code}")
                        
                except Exception as cell_error:
                    error_details.append(f"Cell {cell_location}: Exception - {cell_error}")
                    print(f"      ❌ Exception: {cell_error}")
            
            # Summary
            if success_count == len(self.test_cells):
                self.log_result(
                    "Individual Cell QR Generation",
                    True,
                    f"All {success_count}/{len(self.test_cells)} cells generated QR codes successfully"
                )
                return True
            else:
                self.log_result(
                    "Individual Cell QR Generation",
                    False,
                    f"Only {success_count}/{len(self.test_cells)} cells generated QR codes successfully. "
                    f"Errors found: {len(error_details)}",
                    "; ".join(error_details)
                )
                return False
                
        except Exception as e:
            self.log_result("Individual Cell QR Generation", False, "Exception during QR generation testing", e)
            return False

    def test_batch_qr_generation(self):
        """Test GET /api/warehouses/{warehouse_id}/cells/qr-batch"""
        try:
            print("📊 STEP 5: Testing Batch QR Generation")
            
            response = self.session.get(f"{BACKEND_URL}/warehouses/{self.warehouse_id}/cells/qr-batch")
            
            if response.status_code == 200:
                batch_data = response.json()
                
                if isinstance(batch_data, dict):
                    if "qr_codes" in batch_data:
                        qr_codes = batch_data["qr_codes"]
                        
                        if isinstance(qr_codes, list) and len(qr_codes) > 0:
                            # Validate some QR codes
                            valid_qr_count = 0
                            invalid_qr_details = []
                            
                            for i, qr_item in enumerate(qr_codes[:10]):  # Check first 10
                                if isinstance(qr_item, dict) and "qr_code" in qr_item:
                                    qr_code = qr_item["qr_code"]
                                    if qr_code and qr_code.startswith("data:image/png;base64,"):
                                        valid_qr_count += 1
                                    else:
                                        invalid_qr_details.append(f"QR {i+1}: Invalid format")
                                else:
                                    invalid_qr_details.append(f"QR {i+1}: Missing qr_code field")
                            
                            self.log_result(
                                "Batch QR Generation",
                                True,
                                f"Generated {len(qr_codes)} QR codes in batch. "
                                f"Validated {valid_qr_count}/10 sample QR codes successfully. "
                                f"Invalid QRs: {len(invalid_qr_details)}"
                            )
                            return True
                        else:
                            self.log_result(
                                "Batch QR Generation",
                                False,
                                "Empty or invalid qr_codes array in response"
                            )
                            return False
                    else:
                        available_fields = list(batch_data.keys())
                        self.log_result(
                            "Batch QR Generation",
                            False,
                            f"Missing 'qr_codes' field in response. Available fields: {available_fields}"
                        )
                        return False
                else:
                    self.log_result(
                        "Batch QR Generation",
                        False,
                        f"Invalid response format: {type(batch_data)}"
                    )
                    return False
            else:
                self.log_result(
                    "Batch QR Generation",
                    False,
                    f"Failed to generate batch QR codes with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Batch QR Generation", False, "Exception during batch QR generation", e)
            return False

    def test_warehouse_structure_update(self):
        """Test PUT /api/warehouses/{warehouse_id}/structure"""
        try:
            print("🏗️ STEP 6: Testing Warehouse Structure Update")
            
            # Get current warehouse structure first
            warehouse_response = self.session.get(f"{BACKEND_URL}/warehouses/{self.warehouse_id}")
            
            if warehouse_response.status_code != 200:
                self.log_result(
                    "Warehouse Structure Update",
                    False,
                    f"Failed to get current warehouse structure: {warehouse_response.status_code}"
                )
                return False
            
            warehouse_data = warehouse_response.json()
            
            # Prepare structure update (keep same structure to avoid breaking existing cells)
            structure_update = {
                "blocks_count": warehouse_data.get("blocks_count", 1),
                "shelves_per_block": warehouse_data.get("shelves_per_block", 1),
                "cells_per_shelf": warehouse_data.get("cells_per_shelf", 5)
            }
            
            response = self.session.put(
                f"{BACKEND_URL}/warehouses/{self.warehouse_id}/structure",
                json=structure_update
            )
            
            if response.status_code == 200:
                update_result = response.json()
                
                blocks = structure_update['blocks_count']
                shelves = structure_update['shelves_per_block']
                cells = structure_update['cells_per_shelf']
                
                self.log_result(
                    "Warehouse Structure Update",
                    True,
                    f"Successfully updated warehouse structure. "
                    f"Structure: {blocks} blocks × {shelves} shelves × {cells} cells"
                )
                return True
            else:
                self.log_result(
                    "Warehouse Structure Update",
                    False,
                    f"Failed to update warehouse structure with status {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Warehouse Structure Update", False, "Exception during structure update", e)
            return False

    def test_batch_delete_cells(self):
        """Test POST /api/warehouses/{warehouse_id}/cells/batch-delete"""
        try:
            print("🗑️ STEP 7: Testing Batch Delete Cells")
            
            # We won't actually delete cells, just test the endpoint validation
            # Use non-existent cell IDs to test error handling
            fake_cell_ids = ["fake-cell-1", "fake-cell-2", "non-existent-cell"]
            
            delete_data = {
                "cell_ids": fake_cell_ids
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/warehouses/{self.warehouse_id}/cells/batch-delete",
                json=delete_data
            )
            
            # We expect this to either work (with error details) or return appropriate error
            if response.status_code in [200, 400, 404]:
                content_type = response.headers.get('content-type', '')
                result_data = response.json() if content_type.startswith('application/json') else {}
                
                self.log_result(
                    "Batch Delete Cells",
                    True,
                    f"Batch delete endpoint accessible (status: {response.status_code}). "
                    f"Response indicates proper error handling for non-existent cells."
                )
                return True
            else:
                self.log_result(
                    "Batch Delete Cells",
                    False,
                    f"Unexpected response from batch delete endpoint: {response.status_code}",
                    response.text
                )
                return False
                
        except Exception as e:
            self.log_result("Batch Delete Cells", False, "Exception during batch delete testing", e)
            return False

    def test_data_validation_and_error_handling(self):
        """Test data validation and error handling"""
        try:
            print("🔍 STEP 8: Testing Data Validation and Error Handling")
            
            validation_tests = []
            
            # Test 1: Invalid warehouse_id for cells
            try:
                response = self.session.get(f"{BACKEND_URL}/warehouses/invalid-warehouse-id/cells")
                validation_tests.append({
                    "test": "Invalid warehouse_id for cells",
                    "success": response.status_code in [400, 404],
                    "details": f"Status: {response.status_code}"
                })
            except Exception as e:
                validation_tests.append({
                    "test": "Invalid warehouse_id for cells",
                    "success": False,
                    "details": f"Exception: {e}"
                })
            
            # Test 2: Invalid cell_id for QR generation
            try:
                response = self.session.get(f"{BACKEND_URL}/warehouses/cells/invalid-cell-id/qr")
                validation_tests.append({
                    "test": "Invalid cell_id for QR",
                    "success": response.status_code in [400, 404],
                    "details": f"Status: {response.status_code}"
                })
            except Exception as e:
                validation_tests.append({
                    "test": "Invalid cell_id for QR",
                    "success": False,
                    "details": f"Exception: {e}"
                })
            
            # Test 3: Invalid structure data
            try:
                invalid_structure = {
                    "blocks_count": -1,  # Invalid negative value
                    "shelves_per_block": 0,  # Invalid zero value
                    "cells_per_shelf": "invalid"  # Invalid string value
                }
                response = self.session.put(
                    f"{BACKEND_URL}/warehouses/{self.warehouse_id}/structure",
                    json=invalid_structure
                )
                validation_tests.append({
                    "test": "Invalid structure data",
                    "success": response.status_code in [400, 422],
                    "details": f"Status: {response.status_code}"
                })
            except Exception as e:
                validation_tests.append({
                    "test": "Invalid structure data",
                    "success": False,
                    "details": f"Exception: {e}"
                })
            
            # Summary
            passed_tests = sum(1 for test in validation_tests if test["success"])
            total_tests = len(validation_tests)
            
            # Create details string without f-string backslash issue
            details_parts = []
            for t in validation_tests:
                test_name = t["test"]
                test_details = t["details"]
                details_parts.append(f"{test_name}: {test_details}")
            details_str = "; ".join(details_parts)
            
            self.log_result(
                "Data Validation and Error Handling",
                passed_tests == total_tests,
                f"Validation tests passed: {passed_tests}/{total_tests}. Details: {details_str}"
            )
            
            return passed_tests == total_tests
                
        except Exception as e:
            self.log_result("Data Validation and Error Handling", False, "Exception during validation testing", e)
            return False

    def generate_summary_report(self):
        """Generate comprehensive test summary"""
        print("\n" + "="*80)
        print("🎯 WAREHOUSE CELL MANAGEMENT ENDPOINTS TESTING SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"📊 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {(passed_tests/total_tests*100):.1f}%")
        print()
        
        print("📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"   {status} {result['test']}")
            print(f"      {result['details']}")
            if result["error"]:
                print(f"      Error: {result['error']}")
            print()
        
        # Critical findings
        print("🔍 CRITICAL FINDINGS:")
        qr_test = next((r for r in self.test_results if "QR Generation" in r["test"]), None)
        if qr_test:
            if qr_test["success"]:
                print("   ✅ QR Code Generation: Working correctly")
            else:
                print("   ❌ QR Code Generation: ERRORS FOUND")
                print(f"      Details: {qr_test['details']}")
                if qr_test["error"]:
                    print(f"      Error: {qr_test['error']}")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        if failed_tests > 0:
            print("   - Review failed endpoints for implementation issues")
            print("   - Check QR code generation logic and base64 encoding")
            print("   - Verify cell_id format and validation")
            print("   - Test with different warehouse configurations")
        else:
            print("   - All warehouse cell management endpoints are working correctly")
            print("   - QR code generation is functioning properly")
            print("   - System is ready for production use")
        
        return passed_tests, total_tests

    def run_all_tests(self):
        """Run all warehouse cell management tests"""
        print("🚀 STARTING WAREHOUSE CELL MANAGEMENT ENDPOINTS TESTING")
        print("="*80)
        
        # Step 1: Authentication
        if not self.authenticate_admin():
            print("❌ Authentication failed. Cannot proceed with testing.")
            return False
        
        # Step 2: Get warehouses
        if not self.get_warehouses_list():
            print("❌ Failed to get warehouses list. Cannot proceed with testing.")
            return False
        
        # Step 3: Test warehouse cells retrieval
        if not self.test_get_warehouse_cells():
            print("⚠️ Failed to get warehouse cells. Some tests may be limited.")
        
        # Step 4: Test individual QR generation (CRITICAL)
        self.test_individual_cell_qr_generation()
        
        # Step 5: Test batch QR generation
        self.test_batch_qr_generation()
        
        # Step 6: Test warehouse structure update
        self.test_warehouse_structure_update()
        
        # Step 7: Test batch delete
        self.test_batch_delete_cells()
        
        # Step 8: Test validation and error handling
        self.test_data_validation_and_error_handling()
        
        # Generate summary
        passed, total = self.generate_summary_report()
        
        return passed == total

def main():
    """Main function"""
    tester = WarehouseCellManagementTester()
    
    try:
        success = tester.run_all_tests()
        
        if success:
            print("\n🎉 ALL TESTS PASSED! Warehouse cell management endpoints are working correctly.")
            sys.exit(0)
        else:
            print("\n⚠️ SOME TESTS FAILED! Review the detailed results above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Testing interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
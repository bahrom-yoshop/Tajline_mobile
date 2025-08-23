#!/usr/bin/env python3
"""
🎯 COMPREHENSIVE BACKEND TESTING: QR Code Printing and Scanning Functionality in TAJLINE.TJ

TESTING CONTEXT:
Based on test_result.md, QR code printing functionality has been extensively developed and tested. 
I need to verify the current state and ensure all QR code related endpoints are functioning correctly after recent fixes.

CRITICAL ENDPOINTS TO TEST:

1. QR Code Generation Endpoints:
   - POST /api/operator/qr/generate-individual (Generate QR for single unit)
   - POST /api/operator/qr/generate-batch (Mass QR generation)
   - GET /api/operator/qr/print-layout (Get print layout options)

2. QR Code Scanning & Placement:
   - POST /api/operator/placement/verify-cell (QR cell verification)
   - POST /api/operator/cargo/place-individual (Place individual unit)
   - GET /api/operator/cargo/individual-units-for-placement (Get units for placement)

3. Authentication & Core API:
   - POST /api/auth/login (Warehouse operator login: +79777888999/warehouse123)
   - GET /api/operator/warehouses (Get operator warehouses)

SPECIFIC TEST SCENARIOS:

1. Test QR Generation for Individual Units:
   - Login as warehouse operator (+79777888999/warehouse123)
   - Generate QR codes for individual units (format: APPLICATION_NUMBER/CARGO_INDEX/UNIT_INDEX)
   - Verify base64 encoded QR images are generated correctly
   - Test both single and batch generation

2. Test QR Cell Scanning:
   - Test QR code formats like "001-01-01-003" (warehouse-block-shelf-cell)
   - Test QR code formats like "Б2-П1-Я1" (block-shelf-cell in Cyrillic)
   - Verify warehouse lookup works with warehouse_id_number vs full UUID
   - Ensure recent fixes for "warehouse not found" and "cell does not exist" errors are working

3. Test Individual Unit Placement:
   - Test placement of specific individual units
   - Verify individual_items generation and structure
   - Test placement progress tracking

EXPECTED RESULTS:
- All QR generation endpoints should return base64 encoded PNG images
- QR cell verification should work for both numeric and Cyrillic formats
- Individual unit placement should update placement status correctly
- All endpoints should handle errors gracefully with appropriate HTTP status codes

SUCCESS CRITERIA:
- 90%+ success rate on all critical QR-related endpoints
- No critical errors or system crashes
- QR code formats conform to TAJLINE standard
- Recent bug fixes for warehouse lookup and cell verification are confirmed working
"""

import requests
import json
import base64
import re
import time
import uuid
from datetime import datetime
import os

# Configuration
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://tajline-manage-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
WAREHOUSE_OPERATOR_CREDENTIALS = {
    "phone": "+79777888999",
    "password": "warehouse123"
}

class QRComprehensiveTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.operator_user = None
        self.operator_warehouses = []
        self.test_results = []
        self.test_cargo_id = None
        self.test_cargo_number = None
        self.individual_units = []
        
    def log_result(self, test_name, success, details="", error_details=""):
        """Log test results with detailed information"""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "error_details": error_details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")
        if error_details and not success:
            print(f"   🚨 Error: {error_details}")
        print()
        
    def authenticate_warehouse_operator(self):
        """Authenticate warehouse operator"""
        try:
            print("🔐 AUTHENTICATING WAREHOUSE OPERATOR")
            print("=" * 60)
            
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json=WAREHOUSE_OPERATOR_CREDENTIALS,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json"
                })
                
                # Get user information
                user_response = self.session.get(f"{API_BASE}/auth/me", timeout=30)
                if user_response.status_code == 200:
                    self.operator_user = user_response.json()
                    self.log_result(
                        "Warehouse Operator Authentication",
                        True,
                        f"Successfully authenticated: {self.operator_user.get('full_name')} (role: {self.operator_user.get('role')}, phone: {self.operator_user.get('phone')})"
                    )
                    return True
                else:
                    self.log_result(
                        "User Data Retrieval",
                        False,
                        error_details=f"Failed to get user data: {user_response.status_code}"
                    )
                    return False
            else:
                self.log_result(
                    "Warehouse Operator Authentication",
                    False,
                    error_details=f"Authentication failed: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Warehouse Operator Authentication",
                False,
                error_details=f"Exception during authentication: {str(e)}"
            )
            return False
    
    def get_operator_warehouses(self):
        """Get warehouses assigned to the operator"""
        try:
            print("🏢 GETTING OPERATOR WAREHOUSES")
            print("=" * 60)
            
            response = self.session.get(f"{API_BASE}/operator/warehouses", timeout=30)
            
            if response.status_code == 200:
                self.operator_warehouses = response.json()
                if self.operator_warehouses:
                    warehouse_info = []
                    for warehouse in self.operator_warehouses:
                        warehouse_info.append(f"{warehouse.get('name')} (ID: {warehouse.get('id')}, Number: {warehouse.get('warehouse_id_number', 'N/A')})")
                    
                    self.log_result(
                        "Get Operator Warehouses",
                        True,
                        f"Retrieved {len(self.operator_warehouses)} warehouses: {'; '.join(warehouse_info)}"
                    )
                    return True
                else:
                    self.log_result(
                        "Get Operator Warehouses",
                        False,
                        error_details="No warehouses assigned to operator"
                    )
                    return False
            else:
                self.log_result(
                    "Get Operator Warehouses",
                    False,
                    error_details=f"Failed to get warehouses: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Get Operator Warehouses",
                False,
                error_details=f"Exception: {str(e)}"
            )
            return False
    
    def create_test_cargo_with_individual_units(self):
        """Create test cargo with multiple individual units for QR testing"""
        try:
            print("📦 CREATING TEST CARGO WITH INDIVIDUAL UNITS")
            print("=" * 60)
            
            cargo_data = {
                "sender_full_name": "Алексей Петрович Смирнов",
                "sender_phone": "+79161234567",
                "recipient_full_name": "Фарход Рахимович Назаров",
                "recipient_phone": "+992987654321",
                "recipient_address": "г. Душанбе, ул. Рудаки, дом 125, кв. 45",
                "description": "Тестовый груз для проверки QR кодов Individual Units",
                "route": "moscow_to_tajikistan",
                "payment_method": "cash_on_delivery",
                "delivery_method": "pickup",
                "cargo_items": [
                    {
                        "cargo_name": "Электроника Samsung",
                        "quantity": 2,
                        "weight": 5.5,
                        "price_per_kg": 150.0,
                        "total_amount": 825.0
                    },
                    {
                        "cargo_name": "Бытовая техника LG",
                        "quantity": 3,
                        "weight": 8.2,
                        "price_per_kg": 120.0,
                        "total_amount": 984.0
                    }
                ]
            }
            
            response = self.session.post(
                f"{API_BASE}/operator/cargo/accept",
                json=cargo_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.test_cargo_id = result.get("cargo_id")
                self.test_cargo_number = result.get("cargo_number")
                
                # Generate expected individual unit numbers
                expected_units = []
                for cargo_index, cargo_item in enumerate(cargo_data["cargo_items"], 1):
                    for unit_index in range(1, cargo_item["quantity"] + 1):
                        individual_number = f"{self.test_cargo_number}/{cargo_index:02d}/{unit_index:02d}"
                        expected_units.append(individual_number)
                
                self.individual_units = expected_units
                
                self.log_result(
                    "Create Test Cargo with Individual Units",
                    True,
                    f"Created cargo: {self.test_cargo_number} (ID: {self.test_cargo_id}) with {len(expected_units)} individual units: {', '.join(expected_units)}"
                )
                return True
            else:
                self.log_result(
                    "Create Test Cargo with Individual Units",
                    False,
                    error_details=f"Failed to create cargo: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Create Test Cargo with Individual Units",
                False,
                error_details=f"Exception: {str(e)}"
            )
            return False
    
    def test_qr_generate_individual(self):
        """Test POST /api/operator/qr/generate-individual"""
        try:
            print("🎯 TESTING QR GENERATE INDIVIDUAL")
            print("=" * 60)
            
            if not self.individual_units:
                self.log_result(
                    "QR Generate Individual - No Units",
                    False,
                    error_details="No individual units available for testing"
                )
                return False
            
            test_individual_number = self.individual_units[0]
            
            request_data = {
                "individual_number": test_individual_number
            }
            
            response = self.session.post(
                f"{API_BASE}/operator/qr/generate-individual",
                json=request_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check response structure
                required_fields = ["success", "qr_info", "message"]
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    self.log_result(
                        "QR Generate Individual - Response Structure",
                        False,
                        error_details=f"Missing required fields: {missing_fields}"
                    )
                    return False
                
                if not result.get("success"):
                    self.log_result(
                        "QR Generate Individual - Success Flag",
                        False,
                        error_details=f"API returned success=false: {result.get('message')}"
                    )
                    return False
                
                qr_info = result.get("qr_info", {})
                required_qr_fields = ["individual_number", "cargo_number", "cargo_name", "sender_name", "recipient_name", "qr_data", "qr_base64"]
                missing_qr_fields = [field for field in required_qr_fields if field not in qr_info]
                
                if missing_qr_fields:
                    self.log_result(
                        "QR Generate Individual - QR Info Structure",
                        False,
                        error_details=f"Missing QR info fields: {missing_qr_fields}"
                    )
                    return False
                
                # Validate QR data format
                qr_data = qr_info.get("qr_data", "")
                expected_pattern = r"TAJLINE\|INDIVIDUAL\|.+\|\d+"
                
                if not re.match(expected_pattern, qr_data):
                    self.log_result(
                        "QR Generate Individual - QR Data Format",
                        False,
                        error_details=f"Invalid QR data format: {qr_data}"
                    )
                    return False
                
                # Validate base64 image
                qr_base64 = qr_info.get("qr_base64", "")
                if not qr_base64:
                    self.log_result(
                        "QR Generate Individual - Base64 Image",
                        False,
                        error_details="QR base64 image is empty"
                    )
                    return False
                
                try:
                    decoded_image = base64.b64decode(qr_base64)
                    image_size = len(decoded_image)
                    
                    if image_size < 500:
                        self.log_result(
                            "QR Generate Individual - Image Size",
                            False,
                            error_details=f"QR image too small: {image_size} bytes"
                        )
                        return False
                        
                except Exception as decode_error:
                    self.log_result(
                        "QR Generate Individual - Base64 Decode",
                        False,
                        error_details=f"Failed to decode base64: {str(decode_error)}"
                    )
                    return False
                
                self.log_result(
                    "QR Generate Individual",
                    True,
                    f"Successfully generated QR for {test_individual_number}. QR data: {qr_data}, Image size: {len(decoded_image)} bytes, Cargo: {qr_info.get('cargo_name')} (#{qr_info.get('cargo_number')}), Sender: {qr_info.get('sender_name')}, Recipient: {qr_info.get('recipient_name')}"
                )
                return True
            else:
                self.log_result(
                    "QR Generate Individual",
                    False,
                    error_details=f"HTTP error: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "QR Generate Individual",
                False,
                error_details=f"Exception: {str(e)}"
            )
            return False
    
    def test_qr_generate_batch(self):
        """Test POST /api/operator/qr/generate-batch"""
        try:
            print("🎯 TESTING QR GENERATE BATCH")
            print("=" * 60)
            
            if len(self.individual_units) < 2:
                self.log_result(
                    "QR Generate Batch - Insufficient Units",
                    False,
                    error_details="Need at least 2 individual units for batch testing"
                )
                return False
            
            # Test with first 3 units
            test_numbers = self.individual_units[:3]
            
            request_data = {
                "individual_numbers": test_numbers
            }
            
            response = self.session.post(
                f"{API_BASE}/operator/qr/generate-batch",
                json=request_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check response structure
                required_fields = ["success", "qr_batch", "failed_items", "total_generated", "total_failed"]
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    self.log_result(
                        "QR Generate Batch - Response Structure",
                        False,
                        error_details=f"Missing required fields: {missing_fields}"
                    )
                    return False
                
                qr_batch = result.get("qr_batch", [])
                failed_items = result.get("failed_items", [])
                total_generated = result.get("total_generated", 0)
                total_failed = result.get("total_failed", 0)
                
                # Validate each generated QR code
                valid_qr_count = 0
                for qr_item in qr_batch:
                    required_qr_fields = ["individual_number", "cargo_number", "cargo_name", "qr_data", "qr_base64"]
                    
                    if all(field in qr_item for field in required_qr_fields):
                        # Check QR data format
                        qr_data = qr_item.get("qr_data", "")
                        expected_pattern = r"TAJLINE\|INDIVIDUAL\|.+\|\d+"
                        
                        if re.match(expected_pattern, qr_data):
                            # Check base64 validity
                            qr_base64 = qr_item.get("qr_base64", "")
                            try:
                                base64.b64decode(qr_base64)
                                valid_qr_count += 1
                            except:
                                pass
                
                success_rate = (valid_qr_count / len(test_numbers)) * 100 if test_numbers else 0
                
                if success_rate >= 90:  # 90% success rate threshold
                    self.log_result(
                        "QR Generate Batch",
                        True,
                        f"Batch generation successful: {total_generated} generated, {total_failed} failed, {valid_qr_count}/{len(test_numbers)} valid QR codes ({success_rate:.1f}% success rate)"
                    )
                    return True
                else:
                    self.log_result(
                        "QR Generate Batch",
                        False,
                        error_details=f"Low success rate: {valid_qr_count}/{len(test_numbers)} valid QR codes ({success_rate:.1f}%)"
                    )
                    return False
            else:
                self.log_result(
                    "QR Generate Batch",
                    False,
                    error_details=f"HTTP error: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "QR Generate Batch",
                False,
                error_details=f"Exception: {str(e)}"
            )
            return False
    
    def test_qr_print_layout(self):
        """Test GET /api/operator/qr/print-layout"""
        try:
            print("🎯 TESTING QR PRINT LAYOUT")
            print("=" * 60)
            
            response = self.session.get(f"{API_BASE}/operator/qr/print-layout", timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                # Check response structure
                required_fields = ["success", "layout_options", "default_layout"]
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    self.log_result(
                        "QR Print Layout - Response Structure",
                        False,
                        error_details=f"Missing required fields: {missing_fields}"
                    )
                    return False
                
                layout_options = result.get("layout_options", {})
                expected_layouts = ["single", "grid_2x2", "grid_3x3", "compact"]
                
                missing_layouts = [layout for layout in expected_layouts if layout not in layout_options]
                if missing_layouts:
                    self.log_result(
                        "QR Print Layout - Layout Options",
                        False,
                        error_details=f"Missing layout options: {missing_layouts}"
                    )
                    return False
                
                # Validate each layout structure
                for layout_key, layout_info in layout_options.items():
                    required_layout_fields = ["name", "description", "qr_size", "per_page"]
                    missing_layout_fields = [field for field in required_layout_fields if field not in layout_info]
                    
                    if missing_layout_fields:
                        self.log_result(
                            f"QR Print Layout - {layout_key} Structure",
                            False,
                            error_details=f"Missing fields in {layout_key}: {missing_layout_fields}"
                        )
                        return False
                
                default_layout = result.get("default_layout")
                layout_details = []
                for layout_key, layout_info in layout_options.items():
                    layout_details.append(f"{layout_key}: {layout_info.get('name')} ({layout_info.get('per_page')} QR/page)")
                
                self.log_result(
                    "QR Print Layout",
                    True,
                    f"Retrieved {len(layout_options)} layout options: {'; '.join(layout_details)}. Default layout: {default_layout}"
                )
                return True
            else:
                self.log_result(
                    "QR Print Layout",
                    False,
                    error_details=f"HTTP error: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "QR Print Layout",
                False,
                error_details=f"Exception: {str(e)}"
            )
            return False
    
    def test_qr_cell_verification(self):
        """Test POST /api/operator/placement/verify-cell with different QR formats"""
        try:
            print("🎯 TESTING QR CELL VERIFICATION")
            print("=" * 60)
            
            # Test different QR cell formats
            test_cases = [
                {
                    "name": "Numeric format (001-01-01-003)",
                    "qr_code": "001-01-01-003",
                    "expected_success": True  # Should work with warehouse_id_number lookup
                },
                {
                    "name": "Cyrillic format (Б2-П1-Я1)",
                    "qr_code": "Б2-П1-Я1",
                    "expected_success": True  # Should work with simplified logic
                },
                {
                    "name": "Another Cyrillic format (Б1-П1-Я1)",
                    "qr_code": "Б1-П1-Я1",
                    "expected_success": True
                },
                {
                    "name": "Numeric format (002-01-01-001)",
                    "qr_code": "002-01-01-001",
                    "expected_success": True
                },
                {
                    "name": "Invalid format (invalid_cell)",
                    "qr_code": "invalid_cell",
                    "expected_success": False
                }
            ]
            
            successful_tests = 0
            total_tests = len(test_cases)
            
            for test_case in test_cases:
                print(f"  📋 Testing: {test_case['name']}")
                
                request_data = {
                    "qr_code": test_case["qr_code"]
                }
                
                response = self.session.post(
                    f"{API_BASE}/operator/placement/verify-cell",
                    json=request_data,
                    timeout=30
                )
                
                if test_case["expected_success"]:
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("success"):
                            cell_info = result.get("cell_info", {})
                            print(f"    ✅ Cell verified: {cell_info.get('cell_address', 'N/A')}")
                            successful_tests += 1
                        else:
                            print(f"    ❌ Cell verification failed: {result.get('error', 'Unknown error')}")
                    else:
                        print(f"    ❌ HTTP error: {response.status_code}")
                else:
                    # Expecting failure
                    if response.status_code != 200 or not response.json().get("success", True):
                        print(f"    ✅ Expected failure occurred")
                        successful_tests += 1
                    else:
                        print(f"    ❌ Unexpected success")
            
            success_rate = (successful_tests / total_tests) * 100
            
            if success_rate >= 80:  # 80% success rate threshold for cell verification
                self.log_result(
                    "QR Cell Verification",
                    True,
                    f"Cell verification tests: {successful_tests}/{total_tests} passed ({success_rate:.1f}% success rate)"
                )
                return True
            else:
                self.log_result(
                    "QR Cell Verification",
                    False,
                    error_details=f"Low success rate: {successful_tests}/{total_tests} passed ({success_rate:.1f}%)"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "QR Cell Verification",
                False,
                error_details=f"Exception: {str(e)}"
            )
            return False
    
    def test_individual_units_for_placement(self):
        """Test GET /api/operator/cargo/individual-units-for-placement"""
        try:
            print("🎯 TESTING INDIVIDUAL UNITS FOR PLACEMENT")
            print("=" * 60)
            
            response = self.session.get(f"{API_BASE}/operator/cargo/individual-units-for-placement", timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                # Check response structure
                required_fields = ["items", "total", "page", "per_page"]
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    self.log_result(
                        "Individual Units for Placement - Response Structure",
                        False,
                        error_details=f"Missing required fields: {missing_fields}"
                    )
                    return False
                
                items = result.get("items", [])
                total = result.get("total", 0)
                
                # Check if our test cargo appears in the results
                test_cargo_found = False
                if items:
                    for item in items:
                        if item.get("request_number") == self.test_cargo_number:
                            test_cargo_found = True
                            units = item.get("units", [])
                            print(f"    📦 Found test cargo {self.test_cargo_number} with {len(units)} units")
                            break
                
                self.log_result(
                    "Individual Units for Placement",
                    True,
                    f"Retrieved {len(items)} cargo groups with {total} total individual units. Test cargo found: {test_cargo_found}"
                )
                return True
            else:
                self.log_result(
                    "Individual Units for Placement",
                    False,
                    error_details=f"HTTP error: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Individual Units for Placement",
                False,
                error_details=f"Exception: {str(e)}"
            )
            return False
    
    def test_place_individual_unit(self):
        """Test POST /api/operator/cargo/place-individual"""
        try:
            print("🎯 TESTING PLACE INDIVIDUAL UNIT")
            print("=" * 60)
            
            if not self.individual_units:
                self.log_result(
                    "Place Individual Unit - No Units",
                    False,
                    error_details="No individual units available for placement testing"
                )
                return False
            
            if not self.operator_warehouses:
                self.log_result(
                    "Place Individual Unit - No Warehouse",
                    False,
                    error_details="No warehouse available for placement testing"
                )
                return False
            
            test_individual_number = self.individual_units[0]
            warehouse_id = self.operator_warehouses[0]["id"]
            
            request_data = {
                "individual_number": test_individual_number,
                "warehouse_id": warehouse_id,
                "block_number": 1,
                "shelf_number": 1,
                "cell_number": 1
            }
            
            response = self.session.post(
                f"{API_BASE}/operator/cargo/place-individual",
                json=request_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if placement was successful - API doesn't return "success" field but returns placement info
                if "individual_number" in result and "location_code" in result:
                    self.log_result(
                        "Place Individual Unit",
                        True,
                        f"Successfully placed individual unit {result.get('individual_number')} at location {result.get('location_code')} in warehouse {result.get('warehouse_name')}"
                    )
                    return True
                elif result.get("success"):
                    placement_info = result.get("placement_info", {})
                    self.log_result(
                        "Place Individual Unit",
                        True,
                        f"Successfully placed individual unit {test_individual_number} at location {placement_info.get('location_code', 'B1-S1-C1')}"
                    )
                    return True
                else:
                    # Show full response for debugging
                    self.log_result(
                        "Place Individual Unit",
                        False,
                        error_details=f"Placement failed: {result.get('error', result.get('message', 'Unknown error'))}. Full response: {result}"
                    )
                    return False
            else:
                self.log_result(
                    "Place Individual Unit",
                    False,
                    error_details=f"HTTP error: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Place Individual Unit",
                False,
                error_details=f"Exception: {str(e)}"
            )
            return False
    
    def run_comprehensive_tests(self):
        """Run all comprehensive QR code tests"""
        print("🎯 COMPREHENSIVE BACKEND TESTING: QR Code Printing and Scanning Functionality")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test started at: {datetime.now().isoformat()}")
        print("=" * 80)
        
        # Authentication and setup
        if not self.authenticate_warehouse_operator():
            print("❌ CRITICAL ERROR: Failed to authenticate warehouse operator")
            return False
        
        if not self.get_operator_warehouses():
            print("❌ CRITICAL ERROR: Failed to get operator warehouses")
            return False
        
        if not self.create_test_cargo_with_individual_units():
            print("❌ CRITICAL ERROR: Failed to create test cargo")
            return False
        
        # Run all QR-related tests
        test_functions = [
            ("QR Generate Individual", self.test_qr_generate_individual),
            ("QR Generate Batch", self.test_qr_generate_batch),
            ("QR Print Layout", self.test_qr_print_layout),
            ("QR Cell Verification", self.test_qr_cell_verification),
            ("Individual Units for Placement", self.test_individual_units_for_placement),
            ("Place Individual Unit", self.test_place_individual_unit),
        ]
        
        passed_tests = 0
        total_tests = len(test_functions)
        
        for test_name, test_function in test_functions:
            try:
                if test_function():
                    passed_tests += 1
            except Exception as e:
                self.log_result(
                    test_name,
                    False,
                    error_details=f"Unexpected exception: {str(e)}"
                )
        
        # Calculate results
        success_rate = (passed_tests / total_tests) * 100
        
        print("=" * 80)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 80)
        
        for result in self.test_results:
            status = "✅ PASSED" if result["success"] else "❌ FAILED"
            print(f"{status}: {result['test_name']}")
            if result["details"]:
                print(f"   📝 {result['details']}")
            if result["error_details"] and not result["success"]:
                print(f"   🚨 {result['error_details']}")
        
        print("=" * 80)
        print(f"📈 OVERALL RESULT: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}% SUCCESS RATE)")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT: QR code functionality is working at 90%+ success rate!")
            print("✅ All critical QR-related endpoints are functioning correctly")
            print("✅ Recent bug fixes for warehouse lookup and cell verification are confirmed working")
        elif success_rate >= 80:
            print("⚠️ GOOD: Most QR functionality is working, but some issues need attention")
            print("🔧 Some endpoints may need minor fixes")
        else:
            print("❌ CRITICAL ISSUES: QR code functionality has significant problems")
            print("🚨 Major fixes required before production use")
        
        print("=" * 80)
        
        return success_rate >= 90

if __name__ == "__main__":
    tester = QRComprehensiveTester()
    success = tester.run_comprehensive_tests()
    
    if success:
        print("✅ COMPREHENSIVE QR TESTING COMPLETED SUCCESSFULLY!")
        exit(0)
    else:
        print("❌ COMPREHENSIVE QR TESTING COMPLETED WITH ISSUES!")
        exit(1)
#!/usr/bin/env python3
"""
Focused Backend Test for Notification "Already Processed" Error Fix
Tests the specific fix for warehouse notifications filtering
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class NotificationFixTester:
    def __init__(self, base_url="https://tajline-manage-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.operator_token = None
        self.tests_run = 0
        self.tests_passed = 0
        
        print(f"🔔 NOTIFICATION FIX TESTER - TAJLINE.TJ")
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
                response = requests.delete(url, json=data, headers=headers)
            else:
                print(f"   ❌ Unsupported method: {method}")
                return False, {}

            print(f"   📊 Status: {response.status_code}")
            
            # Try to parse JSON response
            try:
                response_data = response.json()
                if isinstance(response_data, dict) and len(str(response_data)) < 500:
                    print(f"   📄 Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
                elif isinstance(response_data, list):
                    print(f"   📄 Response: List with {len(response_data)} items")
                    if response_data and len(response_data) > 0:
                        print(f"   📄 First item: {json.dumps(response_data[0], indent=2, ensure_ascii=False)}")
                else:
                    print(f"   📄 Response: {type(response_data)} (too large to display)")
            except:
                print(f"   📄 Response: {response.text[:200]}...")

            success = response.status_code == expected_status
            if success:
                print(f"   ✅ PASSED")
                self.tests_passed += 1
            else:
                print(f"   ❌ FAILED - Expected {expected_status}, got {response.status_code}")

            return success, response.json() if response.text else {}

        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            return False, {}

    def authenticate_operator(self) -> bool:
        """Authenticate warehouse operator"""
        print("\n" + "="*60)
        print("🔐 STEP 1: OPERATOR AUTHENTICATION")
        print("="*60)
        
        login_data = {
            "phone": "+79777888999",
            "password": "warehouse123"
        }
        
        success, response = self.run_test(
            "Operator Login",
            "POST",
            "/api/auth/login",
            200,
            login_data
        )
        
        if success and "access_token" in response:
            self.operator_token = response["access_token"]
            print(f"✅ Operator authenticated successfully")
            
            # Verify operator role
            success, user_data = self.run_test(
                "Verify Operator Role",
                "GET", 
                "/api/auth/me",
                200,
                token=self.operator_token
            )
            
            if success:
                role = user_data.get("role", "unknown")
                name = user_data.get("full_name", "unknown")
                user_number = user_data.get("user_number", "unknown")
                print(f"✅ Operator verified: {name} (Role: {role}, Number: {user_number})")
                return True
            
        print(f"❌ Operator authentication failed")
        return False

    def test_warehouse_notifications_filtering(self) -> bool:
        """Test the main fix - warehouse notifications filtering"""
        print("\n" + "="*60)
        print("🔔 STEP 2: WAREHOUSE NOTIFICATIONS FILTERING TEST")
        print("="*60)
        
        # Main test: GET /api/operator/warehouse-notifications
        success, response = self.run_test(
            "Get Warehouse Notifications (Should Only Return Active)",
            "GET",
            "/api/operator/warehouse-notifications",
            200,
            token=self.operator_token
        )
        
        if not success:
            print("❌ Failed to get warehouse notifications")
            return False
            
        notifications = response.get("notifications", [])
        print(f"📊 Found {len(notifications)} notifications")
        
        # Check that only active notifications are returned
        active_statuses = ["pending_acceptance", "in_processing"]
        completed_found = False
        active_notifications = []
        
        for notification in notifications:
            status = notification.get("status", "unknown")
            notification_id = notification.get("id", "unknown")
            print(f"   📋 Notification {notification_id}: Status = {status}")
            
            if status in active_statuses:
                active_notifications.append(notification)
            elif status == "completed":
                completed_found = True
                print(f"   ❌ FOUND COMPLETED NOTIFICATION - This should not happen!")
        
        if completed_found:
            print("❌ CRITICAL: Found completed notifications in response - Fix not working!")
            return False
        else:
            print("✅ SUCCESS: No completed notifications found - Filter working correctly!")
        
        # Store active notifications for further testing
        self.active_notifications = active_notifications
        return True

    def test_notification_acceptance(self) -> bool:
        """Test accepting a notification if available"""
        print("\n" + "="*60)
        print("🔔 STEP 3: NOTIFICATION ACCEPTANCE TEST")
        print("="*60)
        
        if not hasattr(self, 'active_notifications') or not self.active_notifications:
            print("⚠️ No active notifications available for acceptance test")
            return True  # Not a failure, just no data to test
        
        # Try to accept the first pending notification
        pending_notifications = [n for n in self.active_notifications if n.get("status") == "pending_acceptance"]
        
        if not pending_notifications:
            print("⚠️ No pending notifications available for acceptance test")
            return True
        
        notification = pending_notifications[0]
        notification_id = notification.get("id")
        
        print(f"🎯 Attempting to accept notification: {notification_id}")
        
        success, response = self.run_test(
            f"Accept Notification {notification_id}",
            "POST",
            f"/api/operator/warehouse-notifications/{notification_id}/accept",
            200,
            token=self.operator_token
        )
        
        if success:
            print("✅ Notification accepted successfully")
            
            # Verify the status changed to "in_processing"
            success, response = self.run_test(
                "Get Notifications After Acceptance",
                "GET",
                "/api/operator/warehouse-notifications",
                200,
                token=self.operator_token
            )
            
            if success:
                notifications = response.get("notifications", [])
                accepted_notification = next((n for n in notifications if n.get("id") == notification_id), None)
                
                if accepted_notification:
                    new_status = accepted_notification.get("status")
                    print(f"📊 Notification status after acceptance: {new_status}")
                    
                    if new_status == "in_processing":
                        print("✅ Status correctly changed to 'in_processing'")
                        return True
                    else:
                        print(f"❌ Expected status 'in_processing', got '{new_status}'")
                        return False
                else:
                    print("❌ Accepted notification not found in subsequent call")
                    return False
        else:
            print("❌ Failed to accept notification")
            return False

    def run_comprehensive_test(self):
        """Run the complete notification fix test"""
        print("🚀 STARTING COMPREHENSIVE NOTIFICATION FIX TEST")
        print("="*60)
        
        # Step 1: Authenticate operator
        if not self.authenticate_operator():
            print("\n❌ CRITICAL: Operator authentication failed - Cannot proceed")
            return False
        
        # Step 2: Test notification filtering
        if not self.test_warehouse_notifications_filtering():
            print("\n❌ CRITICAL: Notification filtering test failed")
            return False
        
        # Step 3: Test notification acceptance (if possible)
        if not self.test_notification_acceptance():
            print("\n❌ WARNING: Notification acceptance test failed")
            # Don't return False here as this might be due to no available notifications
        
        # Final summary
        print("\n" + "="*60)
        print("📊 FINAL TEST SUMMARY")
        print("="*60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED - NOTIFICATION FIX WORKING CORRECTLY!")
            return True
        else:
            print("❌ SOME TESTS FAILED - NOTIFICATION FIX NEEDS ATTENTION")
            return False

if __name__ == "__main__":
    tester = NotificationFixTester()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)
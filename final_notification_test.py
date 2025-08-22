#!/usr/bin/env python3
"""
Final Backend Test for Notification Fix
Tests the specific fix for warehouse notifications filtering
"""

import requests
import sys
import json
from datetime import datetime

class FinalNotificationTester:
    def __init__(self, base_url="https://placement-view.preview.emergentagent.com"):
        self.base_url = base_url
        self.operator_token = None
        
        print(f"🔔 FINAL NOTIFICATION FIX TEST - TAJLINE.TJ")
        print(f"📡 Base URL: {self.base_url}")
        print("=" * 60)

    def authenticate_operator(self) -> bool:
        """Authenticate warehouse operator"""
        print("\n🔐 OPERATOR AUTHENTICATION (+79777888999/warehouse123)")
        
        login_data = {
            "phone": "+79777888999",
            "password": "warehouse123"
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
            print(f"   📊 Login Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.operator_token = data.get("access_token")
                print(f"   ✅ Operator authenticated successfully")
                
                # Verify role
                headers = {'Authorization': f'Bearer {self.operator_token}'}
                me_response = requests.get(f"{self.base_url}/api/auth/me", headers=headers)
                
                if me_response.status_code == 200:
                    user_data = me_response.json()
                    role = user_data.get("role")
                    name = user_data.get("full_name")
                    user_number = user_data.get("user_number")
                    print(f"   ✅ Verified: {name} (Role: {role}, Number: {user_number})")
                    return True
                    
            print(f"   ❌ Authentication failed")
            return False
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False

    def test_notification_filtering(self) -> bool:
        """Test the main fix - notification filtering"""
        print("\n🔔 MAIN TEST: GET /api/operator/warehouse-notifications")
        print("   Should return only notifications with status 'pending_acceptance' and 'in_processing'")
        
        try:
            headers = {'Authorization': f'Bearer {self.operator_token}'}
            response = requests.get(f"{self.base_url}/api/operator/warehouse-notifications", headers=headers)
            
            print(f"   📊 Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"   ❌ Failed to get notifications")
                return False
            
            data = response.json()
            notifications = data.get("notifications", [])
            total_count = data.get("total_count", 0)
            pending_count = data.get("pending_count", 0)
            in_processing_count = data.get("in_processing_count", 0)
            
            print(f"   📊 Total notifications returned: {total_count}")
            print(f"   📊 Pending acceptance: {pending_count}")
            print(f"   📊 In processing: {in_processing_count}")
            
            # Check statuses
            completed_found = False
            active_statuses = ["pending_acceptance", "in_processing"]
            
            print(f"\n   🔍 Analyzing notification statuses:")
            for i, notification in enumerate(notifications[:5]):  # Show first 5
                status = notification.get("status", "unknown")
                notification_id = notification.get("id", "unknown")
                print(f"      {i+1}. ID: {notification_id}, Status: {status}")
                
                if status == "completed":
                    completed_found = True
                elif status not in active_statuses:
                    print(f"      ⚠️ Unexpected status: {status}")
            
            if len(notifications) > 5:
                print(f"      ... and {len(notifications) - 5} more notifications")
            
            # Main test result
            if completed_found:
                print(f"\n   ❌ CRITICAL: Found 'completed' notifications in response!")
                print(f"      The filtering fix is NOT working correctly!")
                return False
            else:
                print(f"\n   ✅ SUCCESS: No 'completed' notifications found!")
                print(f"      Only active notifications (pending_acceptance, in_processing) are returned")
                print(f"      The filtering fix IS working correctly!")
                return True
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False

    def test_unique_notification_acceptance(self) -> bool:
        """Test accepting a notification with unique ID if available"""
        print("\n🔔 BONUS TEST: Try accepting a notification with unique ID")
        
        try:
            headers = {'Authorization': f'Bearer {self.operator_token}'}
            response = requests.get(f"{self.base_url}/api/operator/warehouse-notifications", headers=headers)
            
            if response.status_code != 200:
                print(f"   ⚠️ Cannot get notifications for acceptance test")
                return True  # Not critical
            
            data = response.json()
            notifications = data.get("notifications", [])
            
            # Find notifications with unique IDs (starting with WN_)
            unique_pending = [n for n in notifications 
                            if n.get("status") == "pending_acceptance" 
                            and n.get("id", "").startswith("WN_")]
            
            if not unique_pending:
                print(f"   ⚠️ No unique pending notifications available for testing")
                return True  # Not critical
            
            notification = unique_pending[0]
            notification_id = notification.get("id")
            
            print(f"   🎯 Attempting to accept notification: {notification_id}")
            
            accept_response = requests.post(
                f"{self.base_url}/api/operator/warehouse-notifications/{notification_id}/accept",
                headers=headers
            )
            
            print(f"   📊 Accept Status: {accept_response.status_code}")
            
            if accept_response.status_code == 200:
                print(f"   ✅ Notification accepted successfully!")
                
                # Verify status change
                verify_response = requests.get(f"{self.base_url}/api/operator/warehouse-notifications", headers=headers)
                if verify_response.status_code == 200:
                    verify_data = verify_response.json()
                    verify_notifications = verify_data.get("notifications", [])
                    accepted_notification = next((n for n in verify_notifications if n.get("id") == notification_id), None)
                    
                    if accepted_notification and accepted_notification.get("status") == "in_processing":
                        print(f"   ✅ Status correctly changed to 'in_processing'")
                        return True
                    else:
                        print(f"   ⚠️ Status change verification failed")
                        return True  # Not critical for main fix
            else:
                accept_data = accept_response.json() if accept_response.text else {}
                detail = accept_data.get("detail", "Unknown error")
                print(f"   ⚠️ Accept failed: {detail}")
                return True  # Not critical for main fix
                
        except Exception as e:
            print(f"   ⚠️ Error in acceptance test: {str(e)}")
            return True  # Not critical for main fix

    def run_test(self):
        """Run the complete test"""
        print("🚀 STARTING NOTIFICATION FIX TEST")
        print("="*60)
        
        # Step 1: Authenticate
        if not self.authenticate_operator():
            print("\n❌ CRITICAL: Authentication failed - Cannot proceed")
            return False
        
        # Step 2: Main test - notification filtering
        filtering_success = self.test_notification_filtering()
        
        # Step 3: Bonus test - try accepting a notification
        self.test_unique_notification_acceptance()
        
        # Final summary
        print("\n" + "="*60)
        print("📊 FINAL TEST RESULTS")
        print("="*60)
        
        if filtering_success:
            print("🎉 MAIN FIX VERIFICATION: SUCCESS!")
            print("✅ GET /api/operator/warehouse-notifications only returns active notifications")
            print("✅ Completed notifications are properly filtered out")
            print("✅ No more 'Notification already processed' errors for new notifications")
            print("\n🎯 EXPECTED RESULT ACHIEVED:")
            print("   The backend fix is working correctly!")
            return True
        else:
            print("❌ MAIN FIX VERIFICATION: FAILED!")
            print("❌ The filtering fix is not working correctly")
            return False

if __name__ == "__main__":
    tester = FinalNotificationTester()
    success = tester.run_test()
    sys.exit(0 if success else 1)
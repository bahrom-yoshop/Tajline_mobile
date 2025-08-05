#!/usr/bin/env python3
"""
Stage 1 Features Test Script
Tests the new Stage 1 features that were just added
"""

from backend_test import CargoTransportAPITester

def main():
    """Run Stage 1 tests only"""
    tester = CargoTransportAPITester()
    
    # Setup required tokens and data
    print("🔧 Setting up test environment...")
    tester.test_health_check()
    tester.test_user_login()
    tester.test_cargo_creation()  # Create some cargo for testing
    
    # Run Stage 1 tests
    print("\n🎯 Running Stage 1 Features Tests...")
    stage1_results = tester.test_stage1_features()
    
    return stage1_results

if __name__ == "__main__":
    main()
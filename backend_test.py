#!/usr/bin/env python3
"""
Comprehensive Backend API Testing Suite
Tests duplicate phone number validation in parties API endpoints
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://ledger-view-issue.preview.emergentagent.com/api"
USERNAME = "admin"
PASSWORD = "admin123"

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", response_data=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if response_data and not success:
            print(f"   Response: {response_data}")
        print()
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
    
    def authenticate(self):
        """Authenticate and get JWT token"""
        print("🔐 Authenticating...")
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json={
                "username": USERNAME,
                "password": PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log_test("Authentication", True, f"Logged in as {USERNAME}")
                return True
            else:
                self.log_test("Authentication", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_duplicate_phone_validation(self):
        """Test all duplicate phone number validation scenarios"""
        print("📱 Testing Duplicate Phone Number Validation...")
        
        # Store party IDs for cleanup
        created_parties = []
        
        try:
            # Test 1: Create Party with Phone (Baseline)
            print("\n1️⃣ BASELINE - Create Party with Phone")
            party_a_data = {
                "name": "Test Party A",
                "phone": "12345678",
                "party_type": "customer"
            }
            
            response = self.session.post(f"{BASE_URL}/parties", json=party_a_data)
            if response.status_code in [200, 201]:
                party_a = response.json()
                party_a_id = party_a.get("id")
                created_parties.append(party_a_id)
                self.log_test("Create Party A with phone 12345678", True, 
                            f"Party created with ID: {party_a_id}")
            else:
                self.log_test("Create Party A with phone 12345678", False, 
                            f"Status: {response.status_code}", response.text)
                return
            
            # Test 2: Duplicate Phone Test (Create) - Should Fail
            print("\n2️⃣ DUPLICATE PHONE TEST (Create)")
            party_b_data = {
                "name": "Test Party B", 
                "phone": "12345678",
                "party_type": "customer"
            }
            
            response = self.session.post(f"{BASE_URL}/parties", json=party_b_data)
            if response.status_code == 400:
                error_msg = response.json().get("detail", "")
                if "Test Party A" in error_msg and "12345678" in error_msg:
                    self.log_test("Duplicate phone validation (CREATE)", True, 
                                f"Correctly blocked duplicate phone. Error: {error_msg}")
                else:
                    self.log_test("Duplicate phone validation (CREATE)", False, 
                                f"Error message doesn't include existing party name: {error_msg}")
            else:
                self.log_test("Duplicate phone validation (CREATE)", False, 
                            f"Expected 400 error, got {response.status_code}", response.text)
            
            # Test 3: Unique Phone Test - Should Succeed
            print("\n3️⃣ UNIQUE PHONE TEST")
            party_c_data = {
                "name": "Test Party C",
                "phone": "87654321", 
                "party_type": "customer"
            }
            
            response = self.session.post(f"{BASE_URL}/parties", json=party_c_data)
            if response.status_code in [200, 201]:
                party_c = response.json()
                party_c_id = party_c.get("id")
                created_parties.append(party_c_id)
                self.log_test("Create Party C with unique phone 87654321", True,
                            f"Party created with ID: {party_c_id}")
            else:
                self.log_test("Create Party C with unique phone 87654321", False,
                            f"Status: {response.status_code}", response.text)
                return
            
            # Test 4: Duplicate Name with Unique Phone - Should Succeed
            print("\n4️⃣ DUPLICATE NAME WITH UNIQUE PHONE (Should Succeed)")
            party_d_data = {
                "name": "Test Party A",  # Same name as Party A
                "phone": "99999999",     # Different phone
                "party_type": "vendor"
            }
            
            response = self.session.post(f"{BASE_URL}/parties", json=party_d_data)
            if response.status_code in [200, 201]:
                party_d = response.json()
                party_d_id = party_d.get("id")
                created_parties.append(party_d_id)
                self.log_test("Duplicate name with unique phone", True,
                            f"Correctly allowed duplicate name. Party ID: {party_d_id}")
            else:
                self.log_test("Duplicate name with unique phone", False,
                            f"Status: {response.status_code}", response.text)
            
            # Test 5: Update with Duplicate Phone - Should Fail
            print("\n5️⃣ UPDATE WITH DUPLICATE PHONE (Should Fail)")
            update_data = {"phone": "12345678"}  # Try to use Party A's phone
            
            response = self.session.patch(f"{BASE_URL}/parties/{party_c_id}", json=update_data)
            if response.status_code == 400:
                error_msg = response.json().get("detail", "")
                if "Test Party A" in error_msg and "12345678" in error_msg:
                    self.log_test("Duplicate phone validation (UPDATE)", True,
                                f"Correctly blocked duplicate phone update. Error: {error_msg}")
                else:
                    self.log_test("Duplicate phone validation (UPDATE)", False,
                                f"Error message doesn't include existing party name: {error_msg}")
            else:
                self.log_test("Duplicate phone validation (UPDATE)", False,
                            f"Expected 400 error, got {response.status_code}", response.text)
            
            # Test 6: Update with Unique Phone - Should Succeed
            print("\n6️⃣ UPDATE WITH UNIQUE PHONE (Should Succeed)")
            update_data = {"phone": "11111111"}
            
            response = self.session.patch(f"{BASE_URL}/parties/{party_c_id}", json=update_data)
            if response.status_code == 200:
                updated_party = response.json()
                if updated_party.get("phone") == "11111111":
                    self.log_test("Update with unique phone", True,
                                f"Phone successfully updated to 11111111")
                else:
                    self.log_test("Update with unique phone", False,
                                f"Phone not updated correctly: {updated_party.get('phone')}")
            else:
                self.log_test("Update with unique phone", False,
                            f"Status: {response.status_code}", response.text)
            
            # Test 7: Update Same Phone - Should Succeed
            print("\n7️⃣ UPDATE SAME PHONE (Should Succeed)")
            update_data = {"phone": "11111111"}  # Same phone as current
            
            response = self.session.patch(f"{BASE_URL}/parties/{party_c_id}", json=update_data)
            if response.status_code == 200:
                self.log_test("Update to same phone number", True,
                            "Correctly allowed updating to own phone number")
            else:
                self.log_test("Update to same phone number", False,
                            f"Status: {response.status_code}", response.text)
            
            # Test 8: Empty Phone Test - Should Succeed
            print("\n8️⃣ EMPTY PHONE TEST")
            party_e_data = {
                "name": "Party No Phone 1",
                "phone": "",
                "party_type": "customer"
            }
            
            response = self.session.post(f"{BASE_URL}/parties", json=party_e_data)
            if response.status_code in [200, 201]:
                party_e = response.json()
                party_e_id = party_e.get("id")
                created_parties.append(party_e_id)
                
                # Create second party with empty phone
                party_f_data = {
                    "name": "Party No Phone 2",
                    "phone": "",
                    "party_type": "customer"
                }
                
                response2 = self.session.post(f"{BASE_URL}/parties", json=party_f_data)
                if response2.status_code in [200, 201]:
                    party_f = response2.json()
                    party_f_id = party_f.get("id")
                    created_parties.append(party_f_id)
                    self.log_test("Multiple parties with empty phone", True,
                                "Both parties with empty phone created successfully")
                else:
                    self.log_test("Multiple parties with empty phone", False,
                                f"Second party creation failed: {response2.status_code}", response2.text)
            else:
                self.log_test("Multiple parties with empty phone", False,
                            f"First party creation failed: {response.status_code}", response.text)
            
            # Test 9: NULL Phone Test - Should Succeed
            print("\n9️⃣ NULL PHONE TEST")
            party_g_data = {
                "name": "Party Null Phone",
                "party_type": "customer"
                # No phone field provided (null)
            }
            
            response = self.session.post(f"{BASE_URL}/parties", json=party_g_data)
            if response.status_code in [200, 201]:
                party_g = response.json()
                party_g_id = party_g.get("id")
                created_parties.append(party_g_id)
                self.log_test("Party with null phone", True,
                            f"Party with null phone created successfully. ID: {party_g_id}")
            else:
                self.log_test("Party with null phone", False,
                            f"Status: {response.status_code}", response.text)
            
            # Test 10: Error Message Validation
            print("\n🔟 ERROR MESSAGE VALIDATION")
            # Try creating another duplicate to verify error message format
            test_duplicate_data = {
                "name": "Another Test Party",
                "phone": "12345678",  # Party A's phone
                "party_type": "vendor"
            }
            
            response = self.session.post(f"{BASE_URL}/parties", json=test_duplicate_data)
            if response.status_code == 400:
                error_detail = response.json().get("detail", "")
                
                # Check error message components
                has_phone = "12345678" in error_detail
                has_party_name = "Test Party A" in error_detail
                has_clear_message = "already registered" in error_detail.lower()
                
                if has_phone and has_party_name and has_clear_message:
                    self.log_test("Error message validation", True,
                                f"Error message contains all required elements: {error_detail}")
                else:
                    self.log_test("Error message validation", False,
                                f"Error message missing elements. Phone: {has_phone}, Name: {has_party_name}, Clear: {has_clear_message}. Message: {error_detail}")
            else:
                self.log_test("Error message validation", False,
                            f"Expected 400 error, got {response.status_code}", response.text)
            
        finally:
            # Cleanup: Delete created parties
            print("\n🧹 CLEANUP - Deleting test parties...")
            for party_id in created_parties:
                try:
                    response = self.session.delete(f"{BASE_URL}/parties/{party_id}")
                    if response.status_code in [200, 204]:
                        print(f"   ✅ Deleted party {party_id}")
                    else:
                        print(f"   ⚠️ Failed to delete party {party_id}: {response.status_code}")
                except Exception as e:
                    print(f"   ⚠️ Exception deleting party {party_id}: {str(e)}")
    
    def run_all_tests(self):
        """Run all test scenarios"""
        print("🚀 Starting Comprehensive Backend API Testing")
        print("=" * 60)
        
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run duplicate phone validation tests
        self.test_duplicate_phone_validation()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = APITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
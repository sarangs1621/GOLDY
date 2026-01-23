#!/usr/bin/env python3
"""
Comprehensive Backend API Testing Suite for Party Ledger Functionality
Tests the specific issues reported by user:
1. "View Ledger in Parties not working" 
2. "Failed to update parties"
3. "Failed to load party details"

Focus: Verify backend API endpoints are working correctly with proper response structures
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://party-details-debug.preview.emergentagent.com/api"
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
    
    def test_party_ledger_endpoints(self):
        """Test Party Ledger endpoints as requested in review"""
        print("📋 Testing Party Ledger Endpoints...")
        
        # First, get a list of existing parties to test with
        print("\n1️⃣ GETTING EXISTING PARTIES")
        response = self.session.get(f"{BASE_URL}/parties?page=1&per_page=10")
        
        if response.status_code != 200:
            self.log_test("Get parties for testing", False, 
                        f"Status: {response.status_code}", response.text)
            return
        
        parties_data = response.json()
        if not parties_data.get("items"):
            # Create a test party if none exist
            print("   No existing parties found. Creating test party...")
            test_party_data = {
                "name": "Ledger Test Party 2025",
                "phone": "99887766",
                "party_type": "customer",
                "address": "Test Address for Ledger Testing"
            }
            
            create_response = self.session.post(f"{BASE_URL}/parties", json=test_party_data)
            if create_response.status_code in [200, 201]:
                test_party = create_response.json()
                party_id = test_party.get("id")
                self.log_test("Create test party for ledger testing", True, 
                            f"Created party with ID: {party_id}")
            else:
                self.log_test("Create test party for ledger testing", False, 
                            f"Status: {create_response.status_code}", create_response.text)
                return
        else:
            # Use first existing party
            party_id = parties_data["items"][0]["id"]
            party_name = parties_data["items"][0]["name"]
            self.log_test("Get existing party for testing", True, 
                        f"Using party: {party_name} (ID: {party_id})")
        
        # Test 1: GET /api/parties/{party_id}/summary
        print(f"\n2️⃣ TESTING GET /api/parties/{party_id}/summary")
        response = self.session.get(f"{BASE_URL}/parties/{party_id}/summary")
        
        if response.status_code == 200:
            summary_data = response.json()
            
            # Verify response structure
            required_sections = ["party", "gold", "money"]
            missing_sections = [section for section in required_sections if section not in summary_data]
            
            if not missing_sections:
                # Verify party section
                party_section = summary_data.get("party", {})
                party_fields = ["id", "name", "phone", "address", "party_type", "notes", "created_at"]
                party_missing = [field for field in party_fields if field not in party_section]
                
                # Verify gold section
                gold_section = summary_data.get("gold", {})
                gold_fields = ["gold_due_from_party", "gold_due_to_party", "net_gold_balance", "total_entries"]
                gold_missing = [field for field in gold_fields if field not in gold_section]
                
                # Verify money section
                money_section = summary_data.get("money", {})
                money_fields = ["money_due_from_party", "money_due_to_party", "net_money_balance", "total_invoices", "total_transactions"]
                money_missing = [field for field in money_fields if field not in money_section]
                
                if not party_missing and not gold_missing and not money_missing:
                    self.log_test("Party summary endpoint structure", True, 
                                f"All required fields present. Gold balance: {gold_section.get('net_gold_balance')}g, Money balance: {money_section.get('net_money_balance')} OMR")
                else:
                    missing_details = []
                    if party_missing:
                        missing_details.append(f"Party fields: {party_missing}")
                    if gold_missing:
                        missing_details.append(f"Gold fields: {gold_missing}")
                    if money_missing:
                        missing_details.append(f"Money fields: {money_missing}")
                    
                    self.log_test("Party summary endpoint structure", False, 
                                f"Missing fields - {', '.join(missing_details)}")
            else:
                self.log_test("Party summary endpoint structure", False, 
                            f"Missing sections: {missing_sections}", summary_data)
        else:
            self.log_test("Party summary endpoint", False, 
                        f"Status: {response.status_code}", response.text)
        
        # Test 2: GET /api/gold-ledger?party_id={party_id}
        print(f"\n3️⃣ TESTING GET /api/gold-ledger?party_id={party_id}")
        response = self.session.get(f"{BASE_URL}/gold-ledger?party_id={party_id}")
        
        if response.status_code == 200:
            gold_ledger_data = response.json()
            
            # Verify pagination structure
            if "items" in gold_ledger_data and "pagination" in gold_ledger_data:
                items = gold_ledger_data.get("items", [])
                pagination = gold_ledger_data.get("pagination", {})
                
                # Verify pagination fields
                pagination_fields = ["total_count", "page", "per_page", "total_pages", "has_next", "has_prev"]
                pagination_missing = [field for field in pagination_fields if field not in pagination]
                
                if not pagination_missing:
                    # Verify items structure if any exist
                    if items:
                        first_item = items[0]
                        item_fields = ["id", "party_id", "date", "type", "weight_grams", "purity_entered", "purpose", "notes"]
                        item_missing = [field for field in item_fields if field not in first_item]
                        
                        if not item_missing:
                            self.log_test("Gold ledger pagination structure", True, 
                                        f"Correct structure with {len(items)} entries. First entry: {first_item.get('type')} {first_item.get('weight_grams')}g")
                        else:
                            self.log_test("Gold ledger pagination structure", False, 
                                        f"Items missing fields: {item_missing}")
                    else:
                        self.log_test("Gold ledger pagination structure", True, 
                                    f"Correct pagination structure with {pagination.get('total_count', 0)} total entries (empty result is valid)")
                else:
                    self.log_test("Gold ledger pagination structure", False, 
                                f"Pagination missing fields: {pagination_missing}")
            else:
                self.log_test("Gold ledger pagination structure", False, 
                            "Response missing 'items' or 'pagination' fields", gold_ledger_data)
        else:
            self.log_test("Gold ledger endpoint", False, 
                        f"Status: {response.status_code}", response.text)
        
        # Test 3: GET /api/parties/{party_id}/ledger
        print(f"\n4️⃣ TESTING GET /api/parties/{party_id}/ledger")
        response = self.session.get(f"{BASE_URL}/parties/{party_id}/ledger")
        
        if response.status_code == 200:
            ledger_data = response.json()
            
            # Verify response structure
            required_fields = ["invoices", "transactions", "outstanding"]
            missing_fields = [field for field in required_fields if field not in ledger_data]
            
            if not missing_fields:
                invoices = ledger_data.get("invoices", [])
                transactions = ledger_data.get("transactions", [])
                outstanding = ledger_data.get("outstanding", 0)
                
                self.log_test("Party ledger endpoint structure", True, 
                            f"Correct structure with {len(invoices)} invoices, {len(transactions)} transactions, outstanding: {outstanding} OMR")
            else:
                self.log_test("Party ledger endpoint structure", False, 
                            f"Missing fields: {missing_fields}", ledger_data)
        else:
            self.log_test("Party ledger endpoint", False, 
                        f"Status: {response.status_code}", response.text)
        
        # Test 4: Test pagination parameters on gold-ledger
        print(f"\n5️⃣ TESTING GOLD LEDGER PAGINATION PARAMETERS")
        
        # Test different page sizes
        for per_page in [25, 50, 100]:
            response = self.session.get(f"{BASE_URL}/gold-ledger?party_id={party_id}&page=1&per_page={per_page}")
            
            if response.status_code == 200:
                data = response.json()
                pagination = data.get("pagination", {})
                
                if pagination.get("per_page") == per_page:
                    self.log_test(f"Gold ledger pagination per_page={per_page}", True, 
                                f"Correct per_page value returned: {pagination.get('per_page')}")
                else:
                    self.log_test(f"Gold ledger pagination per_page={per_page}", False, 
                                f"Expected per_page={per_page}, got {pagination.get('per_page')}")
            else:
                self.log_test(f"Gold ledger pagination per_page={per_page}", False, 
                            f"Status: {response.status_code}")
        
        # Test 5: Create test gold ledger entry to verify data flow
        print(f"\n6️⃣ TESTING GOLD LEDGER ENTRY CREATION AND RETRIEVAL")
        
        # Create a test gold ledger entry
        test_entry_data = {
            "party_id": party_id,
            "type": "IN",
            "weight_grams": 25.750,
            "purity_entered": 916,
            "purpose": "job_work",
            "notes": "Test entry for ledger verification"
        }
        
        create_response = self.session.post(f"{BASE_URL}/gold-ledger", json=test_entry_data)
        
        if create_response.status_code in [200, 201]:
            created_entry = create_response.json()
            entry_id = created_entry.get("id")
            
            self.log_test("Create test gold ledger entry", True, 
                        f"Created entry with ID: {entry_id}, Weight: {created_entry.get('weight_grams')}g")
            
            # Now test retrieval with the new entry
            response = self.session.get(f"{BASE_URL}/gold-ledger?party_id={party_id}")
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                # Look for our test entry
                test_entry_found = any(item.get("id") == entry_id for item in items)
                
                if test_entry_found:
                    self.log_test("Retrieve created gold ledger entry", True, 
                                f"Test entry found in gold ledger results")
                    
                    # Test the updated summary
                    summary_response = self.session.get(f"{BASE_URL}/parties/{party_id}/summary")
                    if summary_response.status_code == 200:
                        summary_data = summary_response.json()
                        gold_section = summary_data.get("gold", {})
                        
                        if gold_section.get("total_entries", 0) > 0:
                            self.log_test("Party summary reflects gold ledger entry", True, 
                                        f"Gold summary shows {gold_section.get('total_entries')} entries, balance: {gold_section.get('net_gold_balance')}g")
                        else:
                            self.log_test("Party summary reflects gold ledger entry", False, 
                                        "Gold summary shows 0 entries despite creating one")
                else:
                    self.log_test("Retrieve created gold ledger entry", False, 
                                "Test entry not found in gold ledger results")
            
            # Cleanup: Delete the test entry
            delete_response = self.session.delete(f"{BASE_URL}/gold-ledger/{entry_id}")
            if delete_response.status_code in [200, 204]:
                print(f"   ✅ Cleaned up test gold ledger entry {entry_id}")
            else:
                print(f"   ⚠️ Failed to cleanup test entry {entry_id}")
                
        else:
            self.log_test("Create test gold ledger entry", False, 
                        f"Status: {create_response.status_code}", create_response.text)
    
    def run_all_tests(self):
        """Run all test scenarios"""
        print("🚀 Starting Party Ledger Backend API Testing")
        print("=" * 60)
        
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run party ledger tests
        self.test_party_ledger_endpoints()
        
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
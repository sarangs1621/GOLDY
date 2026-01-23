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
BASE_URL = "https://invoice-details-2.preview.emergentagent.com/api"
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
    
    def test_party_crud_operations(self):
        """Test Party CRUD operations to verify 'Failed to update parties' and 'Failed to load party details' issues"""
        print("🔧 Testing Party CRUD Operations...")
        
        # Test 1: GET /api/parties - List all parties
        print("\n1️⃣ TESTING GET /api/parties - List all parties")
        response = self.session.get(f"{BASE_URL}/parties?page=1&per_page=50")
        
        if response.status_code == 200:
            parties_data = response.json()
            
            # Verify pagination structure
            if "items" in parties_data and "pagination" in parties_data:
                items = parties_data.get("items", [])
                pagination = parties_data.get("pagination", {})
                
                # Verify pagination fields
                pagination_fields = ["total_count", "page", "per_page", "total_pages", "has_next", "has_prev"]
                pagination_missing = [field for field in pagination_fields if field not in pagination]
                
                if not pagination_missing:
                    self.log_test("GET /api/parties - Pagination structure", True, 
                                f"Found {len(items)} parties with correct pagination structure")
                    
                    # Store first party for later tests if available
                    self.existing_party_id = items[0]["id"] if items else None
                    
                    # Verify party fields if parties exist
                    if items:
                        first_party = items[0]
                        required_fields = ["id", "name", "phone", "party_type", "created_at"]
                        missing_fields = [field for field in required_fields if field not in first_party]
                        
                        if not missing_fields:
                            self.log_test("GET /api/parties - Party fields structure", True, 
                                        f"All required fields present in party objects")
                        else:
                            self.log_test("GET /api/parties - Party fields structure", False, 
                                        f"Missing fields: {missing_fields}")
                else:
                    self.log_test("GET /api/parties - Pagination structure", False, 
                                f"Missing pagination fields: {pagination_missing}")
            else:
                self.log_test("GET /api/parties - Response structure", False, 
                            "Missing 'items' or 'pagination' in response", parties_data)
        else:
            self.log_test("GET /api/parties", False, 
                        f"Status: {response.status_code}", response.text)
            return
        
        # Test 2: Create new party
        print("\n2️⃣ TESTING POST /api/parties - Create new party")
        test_party_data = {
            "name": "Test Party API Check",
            "phone": "+968 9999 5555",
            "party_type": "customer",
            "address": "Test Address for API Verification",
            "notes": "Created for party ledger testing"
        }
        
        create_response = self.session.post(f"{BASE_URL}/parties", json=test_party_data)
        
        if create_response.status_code in [200, 201]:
            created_party = create_response.json()
            self.test_party_id = created_party.get("id")
            
            # Verify created party structure
            if self.test_party_id and created_party.get("name") == test_party_data["name"]:
                self.log_test("POST /api/parties - Create party", True, 
                            f"Created party with ID: {self.test_party_id}")
            else:
                self.log_test("POST /api/parties - Create party", False, 
                            "Created party missing ID or incorrect data", created_party)
                return
        else:
            self.log_test("POST /api/parties - Create party", False, 
                        f"Status: {create_response.status_code}", create_response.text)
            return
        
        # Test 3: GET /api/parties/{party_id} - Get single party details
        print(f"\n3️⃣ TESTING GET /api/parties/{self.test_party_id} - Get party details")
        response = self.session.get(f"{BASE_URL}/parties/{self.test_party_id}")
        
        if response.status_code == 200:
            party_details = response.json()
            
            # Verify party details structure
            required_fields = ["id", "name", "phone", "party_type", "address", "notes", "created_at"]
            missing_fields = [field for field in required_fields if field not in party_details]
            
            if not missing_fields:
                self.log_test("GET /api/parties/{id} - Party details", True, 
                            f"All required fields present. Party: {party_details.get('name')}")
            else:
                self.log_test("GET /api/parties/{id} - Party details", False, 
                            f"Missing fields: {missing_fields}")
        else:
            self.log_test("GET /api/parties/{id} - Party details", False, 
                        f"Status: {response.status_code}", response.text)
        
        # Test 4: PATCH /api/parties/{party_id} - Update party
        print(f"\n4️⃣ TESTING PATCH /api/parties/{self.test_party_id} - Update party")
        update_data = {
            "name": "Updated Test Party",
            "notes": "Updated for testing party update functionality"
        }
        
        update_response = self.session.patch(f"{BASE_URL}/parties/{self.test_party_id}", json=update_data)
        
        if update_response.status_code == 200:
            updated_party = update_response.json()
            
            # Verify update was applied
            if updated_party.get("name") == update_data["name"]:
                self.log_test("PATCH /api/parties/{id} - Update party", True, 
                            f"Party updated successfully. New name: {updated_party.get('name')}")
            else:
                self.log_test("PATCH /api/parties/{id} - Update party", False, 
                            f"Update not applied correctly. Expected: {update_data['name']}, Got: {updated_party.get('name')}")
        else:
            self.log_test("PATCH /api/parties/{id} - Update party", False, 
                        f"Status: {update_response.status_code}", update_response.text)
    
    def test_party_ledger_endpoints(self):
        """Test Party Ledger endpoints to verify 'View Ledger in Parties not working' issue"""
        print("📋 Testing Party Ledger Endpoints...")
        
        if not hasattr(self, 'test_party_id') or not self.test_party_id:
            self.log_test("Party Ledger Tests", False, "No test party available for ledger testing")
            return
        
        # Test 1: GET /api/parties/{party_id}/summary - Party Summary
        print(f"\n1️⃣ TESTING GET /api/parties/{self.test_party_id}/summary - Party Summary")
        response = self.session.get(f"{BASE_URL}/parties/{self.test_party_id}/summary")
        
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
                    self.log_test("GET /api/parties/{id}/summary - Complete structure", True, 
                                f"All sections and fields present. Gold: {gold_section.get('net_gold_balance')}g, Money: {money_section.get('net_money_balance')} OMR")
                else:
                    missing_details = []
                    if party_missing:
                        missing_details.append(f"Party: {party_missing}")
                    if gold_missing:
                        missing_details.append(f"Gold: {gold_missing}")
                    if money_missing:
                        missing_details.append(f"Money: {money_missing}")
                    
                    self.log_test("GET /api/parties/{id}/summary - Complete structure", False, 
                                f"Missing fields - {', '.join(missing_details)}")
            else:
                self.log_test("GET /api/parties/{id}/summary - Response structure", False, 
                            f"Missing sections: {missing_sections}", summary_data)
        else:
            self.log_test("GET /api/parties/{id}/summary", False, 
                        f"Status: {response.status_code}", response.text)
        
        # Test 2: GET /api/gold-ledger?party_id={party_id} - Gold Ledger (CRITICAL - This was the main fix)
        print(f"\n2️⃣ TESTING GET /api/gold-ledger?party_id={self.test_party_id} - Gold Ledger (CRITICAL FIX)")
        response = self.session.get(f"{BASE_URL}/gold-ledger?party_id={self.test_party_id}")
        
        if response.status_code == 200:
            gold_ledger_data = response.json()
            
            # CRITICAL: Verify pagination structure {items: [], pagination: {}}
            if "items" in gold_ledger_data and "pagination" in gold_ledger_data:
                items = gold_ledger_data.get("items", [])
                pagination = gold_ledger_data.get("pagination", {})
                
                # Verify pagination fields
                pagination_fields = ["total_count", "page", "per_page", "total_pages", "has_next", "has_prev"]
                pagination_missing = [field for field in pagination_fields if field not in pagination]
                
                if not pagination_missing:
                    # Verify items is an array (not an object)
                    if isinstance(items, list):
                        self.log_test("GET /api/gold-ledger - PAGINATION STRUCTURE (CRITICAL FIX)", True, 
                                    f"✅ CORRECT: Returns {{items: [], pagination: {{}}}} structure with {len(items)} entries")
                        
                        # Test different page sizes
                        for per_page in [25, 50, 100]:
                            page_response = self.session.get(f"{BASE_URL}/gold-ledger?party_id={self.test_party_id}&page=1&per_page={per_page}")
                            if page_response.status_code == 200:
                                page_data = page_response.json()
                                if page_data.get("pagination", {}).get("per_page") == per_page:
                                    self.log_test(f"Gold ledger pagination per_page={per_page}", True, 
                                                f"Correct per_page value: {per_page}")
                                else:
                                    self.log_test(f"Gold ledger pagination per_page={per_page}", False, 
                                                f"Expected {per_page}, got {page_data.get('pagination', {}).get('per_page')}")
                    else:
                        self.log_test("GET /api/gold-ledger - PAGINATION STRUCTURE (CRITICAL FIX)", False, 
                                    f"❌ INCORRECT: items is not an array, it's {type(items)}")
                else:
                    self.log_test("GET /api/gold-ledger - PAGINATION STRUCTURE (CRITICAL FIX)", False, 
                                f"❌ Missing pagination fields: {pagination_missing}")
            else:
                self.log_test("GET /api/gold-ledger - PAGINATION STRUCTURE (CRITICAL FIX)", False, 
                            f"❌ INCORRECT: Missing 'items' or 'pagination' fields. This was the main issue!", gold_ledger_data)
        else:
            self.log_test("GET /api/gold-ledger", False, 
                        f"Status: {response.status_code}", response.text)
        
        # Test 3: GET /api/parties/{party_id}/ledger - Money Ledger
        print(f"\n3️⃣ TESTING GET /api/parties/{self.test_party_id}/ledger - Money Ledger")
        response = self.session.get(f"{BASE_URL}/parties/{self.test_party_id}/ledger")
        
        if response.status_code == 200:
            ledger_data = response.json()
            
            # Verify response structure
            required_fields = ["invoices", "transactions", "outstanding"]
            missing_fields = [field for field in required_fields if field not in ledger_data]
            
            if not missing_fields:
                invoices = ledger_data.get("invoices", [])
                transactions = ledger_data.get("transactions", [])
                outstanding = ledger_data.get("outstanding", 0)
                
                # Verify invoices and transactions are arrays
                if isinstance(invoices, list) and isinstance(transactions, list):
                    self.log_test("GET /api/parties/{id}/ledger - Money Ledger structure", True, 
                                f"Complete structure: {len(invoices)} invoices, {len(transactions)} transactions, outstanding: {outstanding} OMR")
                else:
                    self.log_test("GET /api/parties/{id}/ledger - Money Ledger structure", False, 
                                f"Invoices or transactions not arrays. Invoices: {type(invoices)}, Transactions: {type(transactions)}")
            else:
                self.log_test("GET /api/parties/{id}/ledger - Money Ledger structure", False, 
                            f"Missing fields: {missing_fields}", ledger_data)
        else:
            self.log_test("GET /api/parties/{id}/ledger", False, 
                        f"Status: {response.status_code}", response.text)
    
    def test_with_actual_data(self):
        """Test with actual ledger entries to verify data flow"""
        print("📊 Testing with Actual Data - Create ledger entries and verify")
        
        if not hasattr(self, 'test_party_id') or not self.test_party_id:
            self.log_test("Data Flow Tests", False, "No test party available for data testing")
            return
        
        # Test 1: Create gold ledger IN entry
        print(f"\n1️⃣ CREATING GOLD LEDGER IN ENTRY for party {self.test_party_id}")
        gold_entry_data = {
            "party_id": self.test_party_id,
            "type": "IN",
            "weight_grams": 25.500,
            "purity_entered": 916,
            "purpose": "job_work",
            "notes": "Test gold deposit for ledger verification"
        }
        
        create_response = self.session.post(f"{BASE_URL}/gold-ledger", json=gold_entry_data)
        
        if create_response.status_code in [200, 201]:
            created_entry = create_response.json()
            self.test_gold_entry_id = created_entry.get("id")
            
            self.log_test("Create gold ledger IN entry", True, 
                        f"Created entry ID: {self.test_gold_entry_id}, Weight: {created_entry.get('weight_grams')}g")
            
            # Test 2: Verify gold ledger shows the entry
            print(f"\n2️⃣ VERIFYING GOLD LEDGER SHOWS THE ENTRY")
            response = self.session.get(f"{BASE_URL}/gold-ledger?party_id={self.test_party_id}")
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                # Look for our test entry
                test_entry_found = any(item.get("id") == self.test_gold_entry_id for item in items)
                
                if test_entry_found and len(items) >= 1:
                    found_entry = next(item for item in items if item.get("id") == self.test_gold_entry_id)
                    self.log_test("Gold ledger shows created entry", True, 
                                f"Entry found: {found_entry.get('type')} {found_entry.get('weight_grams')}g")
                else:
                    self.log_test("Gold ledger shows created entry", False, 
                                f"Entry not found in {len(items)} items")
            
            # Test 3: Verify party summary reflects the gold entry
            print(f"\n3️⃣ VERIFYING PARTY SUMMARY REFLECTS GOLD ENTRY")
            summary_response = self.session.get(f"{BASE_URL}/parties/{self.test_party_id}/summary")
            
            if summary_response.status_code == 200:
                summary_data = summary_response.json()
                gold_section = summary_data.get("gold", {})
                
                expected_gold_due = 25.500
                actual_gold_due = gold_section.get("gold_due_from_party", 0)
                total_entries = gold_section.get("total_entries", 0)
                
                if total_entries >= 1 and abs(actual_gold_due - expected_gold_due) < 0.001:
                    self.log_test("Party summary reflects gold entry", True, 
                                f"Gold due from party: {actual_gold_due}g, Total entries: {total_entries}")
                else:
                    self.log_test("Party summary reflects gold entry", False, 
                                f"Expected gold_due_from_party: {expected_gold_due}g, got: {actual_gold_due}g, entries: {total_entries}")
        else:
            self.log_test("Create gold ledger IN entry", False, 
                        f"Status: {create_response.status_code}", create_response.text)
    
    def cleanup_test_data(self):
        """Clean up test data created during testing"""
        print("🧹 Cleaning up test data...")
        
        # Delete test gold ledger entry
        if hasattr(self, 'test_gold_entry_id') and self.test_gold_entry_id:
            delete_response = self.session.delete(f"{BASE_URL}/gold-ledger/{self.test_gold_entry_id}")
            if delete_response.status_code in [200, 204]:
                print(f"   ✅ Deleted test gold ledger entry {self.test_gold_entry_id}")
            else:
                print(f"   ⚠️ Failed to delete gold ledger entry {self.test_gold_entry_id}")
        
        # Delete test party
        if hasattr(self, 'test_party_id') and self.test_party_id:
            delete_response = self.session.delete(f"{BASE_URL}/parties/{self.test_party_id}")
            if delete_response.status_code in [200, 204]:
                print(f"   ✅ Deleted test party {self.test_party_id}")
            else:
                print(f"   ⚠️ Failed to delete test party {self.test_party_id}")
    
    def run_all_tests(self):
        """Run all test scenarios for Party Ledger functionality"""
        print("🚀 Starting Party Ledger Backend API Testing")
        print("🎯 Focus: Verify 'View Ledger in Parties', 'Failed to update parties', 'Failed to load party details' issues")
        print("=" * 80)
        
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        try:
            # Test 1: Party CRUD Operations
            self.test_party_crud_operations()
            
            # Test 2: Party Ledger Endpoints  
            self.test_party_ledger_endpoints()
            
            # Test 3: Test with actual data
            self.test_with_actual_data()
            
        finally:
            # Always cleanup
            self.cleanup_test_data()
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Categorize results
        critical_tests = [r for r in self.test_results if "CRITICAL" in r["test"]]
        crud_tests = [r for r in self.test_results if any(op in r["test"] for op in ["GET /api/parties", "POST /api/parties", "PATCH /api/parties"])]
        ledger_tests = [r for r in self.test_results if "ledger" in r["test"].lower()]
        
        print(f"\n📋 TEST CATEGORIES:")
        print(f"   🔥 Critical Tests (Pagination Fix): {sum(1 for t in critical_tests if t['success'])}/{len(critical_tests)} passed")
        print(f"   🔧 Party CRUD Tests: {sum(1 for t in crud_tests if t['success'])}/{len(crud_tests)} passed")  
        print(f"   📊 Ledger Tests: {sum(1 for t in ledger_tests if t['success'])}/{len(ledger_tests)} passed")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS ({failed_tests}):")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}")
                    if result['details']:
                        print(f"     └─ {result['details']}")
        
        print(f"\n🎯 USER ISSUES STATUS:")
        
        # Check specific issues
        pagination_fixed = any("PAGINATION STRUCTURE (CRITICAL FIX)" in r["test"] and r["success"] for r in self.test_results)
        party_update_working = any("PATCH /api/parties" in r["test"] and r["success"] for r in self.test_results)
        party_details_working = any("GET /api/parties/{id} - Party details" in r["test"] and r["success"] for r in self.test_results)
        
        print(f"   1. 'View Ledger in Parties not working': {'✅ RESOLVED' if pagination_fixed else '❌ STILL FAILING'}")
        print(f"   2. 'Failed to update parties': {'✅ RESOLVED' if party_update_working else '❌ STILL FAILING'}")
        print(f"   3. 'Failed to load party details': {'✅ RESOLVED' if party_details_working else '❌ STILL FAILING'}")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = APITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
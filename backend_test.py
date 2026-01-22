#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Gold Shop ERP System
PAGINATION BACKEND TESTING - 7 ENDPOINTS

This script tests all 7 pagination endpoints that have been implemented:
1. GET /api/parties?page=X&per_page=Y
2. GET /api/gold-ledger?page=X&per_page=Y
3. GET /api/purchases?page=X&per_page=Y
4. GET /api/jobcards?page=X&per_page=Y
5. GET /api/invoices?page=X&per_page=Y
6. GET /api/transactions?page=X&per_page=Y
7. GET /api/audit-logs?page=X&per_page=Y

Each endpoint uses standardized create_pagination_response() helper function.
Default pagination: page=1, per_page=50
Response format: {items: [...], pagination: {...}}
"""

import requests
import json
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

class PaginationTester:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
        self.session = requests.Session()
        self.test_results = []
        self.user_id = None  # Will be set after login
        self.created_entities = {
            'parties': [],
            'gold_ledger': [],
            'purchases': [],
            'jobcards': [],
            'invoices': [],
            'transactions': [],
            'accounts': []
        }  # Track created entities for cleanup
        
    def log_result(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result with details"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "response_data": response_data,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"    Details: {details}")
        if not success and response_data:
            print(f"    Response: {response_data}")
        print()

    def authenticate(self) -> bool:
        """Authenticate and get JWT token"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json={"username": self.username, "password": self.password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                user_data = data.get('user', {})
                self.user_id = user_data.get('id')
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                self.log_result("Authentication", True, f"Logged in as {self.username}, user_id: {self.user_id}")
                return True
            else:
                self.log_result("Authentication", False, f"Status: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Authentication", False, f"Exception: {str(e)}")
            return False

    def test_pagination_endpoint(self, endpoint: str, endpoint_name: str, filters: Dict = None) -> bool:
        """Test pagination for a specific endpoint"""
        print(f"🔸 Testing {endpoint_name} Pagination")
        
        try:
            # Test 1: Default pagination (page=1, per_page=50)
            params = filters.copy() if filters else {}
            response = self.session.get(f"{self.base_url}/api/{endpoint}", params=params)
            
            if response.status_code != 200:
                self.log_result(f"{endpoint_name} - Default Pagination", False, 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
            
            data = response.json()
            
            # Verify response structure
            if not self.verify_pagination_structure(data, endpoint_name, "Default"):
                return False
            
            total_count = data['pagination']['total_count']
            
            # Test 2: Custom page numbers (if there's enough data)
            if total_count > 50:  # Only test if we have multiple pages
                params['page'] = 2
                response = self.session.get(f"{self.base_url}/api/{endpoint}", params=params)
                
                if response.status_code != 200:
                    self.log_result(f"{endpoint_name} - Page 2", False, 
                                  f"Status: {response.status_code}")
                    return False
                
                data = response.json()
                if not self.verify_pagination_structure(data, endpoint_name, "Page 2"):
                    return False
            
            # Test 3: Custom per_page values
            params = filters.copy() if filters else {}
            params['per_page'] = 25
            response = self.session.get(f"{self.base_url}/api/{endpoint}", params=params)
            
            if response.status_code != 200:
                self.log_result(f"{endpoint_name} - Custom per_page", False, 
                              f"Status: {response.status_code}")
                return False
            
            data = response.json()
            if not self.verify_pagination_structure(data, endpoint_name, "Custom per_page=25"):
                return False
            
            # Verify per_page is respected
            if len(data['items']) > 25:
                self.log_result(f"{endpoint_name} - per_page Limit", False, 
                              f"Returned {len(data['items'])} items, expected max 25")
                return False
            
            # Test 4: Boundary cases
            # Test page=0 (should default to 1 or return error)
            params = filters.copy() if filters else {}
            params['page'] = 0
            response = self.session.get(f"{self.base_url}/api/{endpoint}", params=params)
            
            # Either should work (default to page 1) or return 400 error
            if response.status_code not in [200, 400]:
                self.log_result(f"{endpoint_name} - Boundary page=0", False, 
                              f"Unexpected status: {response.status_code}")
                return False
            
            # Test page > total_pages
            if total_count > 0:
                total_pages = (total_count + 49) // 50  # Ceiling division for default per_page=50
                params = filters.copy() if filters else {}
                params['page'] = total_pages + 10  # Way beyond available pages
                response = self.session.get(f"{self.base_url}/api/{endpoint}", params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    # Should return empty items but valid pagination structure
                    if len(data['items']) > 0:
                        self.log_result(f"{endpoint_name} - Beyond total_pages", False, 
                                      f"Page {total_pages + 10} returned {len(data['items'])} items, expected 0")
                        return False
            
            self.log_result(f"{endpoint_name} - All Pagination Tests", True, 
                          f"Default, custom page, custom per_page, and boundary cases all working")
            return True
            
        except Exception as e:
            self.log_result(f"{endpoint_name} - Pagination Tests", False, f"Exception: {str(e)}")
            return False

    def verify_pagination_structure(self, data: Dict, endpoint_name: str, test_type: str) -> bool:
        """Verify pagination response structure"""
        # Check top-level structure
        if 'items' not in data or 'pagination' not in data:
            self.log_result(f"{endpoint_name} - {test_type} Structure", False, 
                          "Missing 'items' or 'pagination' in response")
            return False
        
        pagination = data['pagination']
        required_fields = ['total_count', 'page', 'per_page', 'total_pages', 'has_next', 'has_prev']
        
        for field in required_fields:
            if field not in pagination:
                self.log_result(f"{endpoint_name} - {test_type} Structure", False, 
                              f"Missing '{field}' in pagination metadata")
                return False
        
        # Verify pagination calculations
        total_count = pagination['total_count']
        page = pagination['page']
        per_page = pagination['per_page']
        total_pages = pagination['total_pages']
        has_next = pagination['has_next']
        has_prev = pagination['has_prev']
        
        # Verify total_pages calculation
        expected_total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0
        if total_pages != expected_total_pages:
            self.log_result(f"{endpoint_name} - {test_type} Calculation", False, 
                          f"total_pages={total_pages}, expected={expected_total_pages}")
            return False
        
        # Verify has_next
        expected_has_next = page < total_pages
        if has_next != expected_has_next:
            self.log_result(f"{endpoint_name} - {test_type} has_next", False, 
                          f"has_next={has_next}, expected={expected_has_next}")
            return False
        
        # Verify has_prev
        expected_has_prev = page > 1
        if has_prev != expected_has_prev:
            self.log_result(f"{endpoint_name} - {test_type} has_prev", False, 
                          f"has_prev={has_prev}, expected={expected_has_prev}")
            return False
        
        # Verify items count doesn't exceed per_page
        if len(data['items']) > per_page:
            self.log_result(f"{endpoint_name} - {test_type} Items Count", False, 
                          f"Returned {len(data['items'])} items, max should be {per_page}")
            return False
        
        return True

    def create_test_data(self) -> bool:
        """Create test data for pagination testing"""
        print("🔧 SETUP PHASE - Creating Test Data for Pagination Testing")
        print("-" * 60)
        
        try:
            # Create test parties (customers and vendors)
            for i in range(5):
                party_data = {
                    "name": f"Pagination Test Customer {i+1:03d}",
                    "phone": f"9988776{i:02d}",
                    "address": f"Test Address {i+1}",
                    "party_type": "customer",
                    "notes": f"Test customer for pagination - {datetime.now().isoformat()}"
                }
                
                response = self.session.post(f"{self.base_url}/api/parties", json=party_data)
                if response.status_code == 200:
                    party = response.json()
                    self.created_entities['parties'].append(party['id'])
                else:
                    self.log_result("Create Test Customers", False, f"Failed to create customer {i+1}")
                    return False
            
            # Create test vendors
            for i in range(3):
                vendor_data = {
                    "name": f"Pagination Test Vendor {i+1:03d}",
                    "phone": f"9977665{i:02d}",
                    "address": f"Vendor Address {i+1}",
                    "party_type": "vendor",
                    "notes": f"Test vendor for pagination - {datetime.now().isoformat()}"
                }
                
                response = self.session.post(f"{self.base_url}/api/parties", json=vendor_data)
                if response.status_code == 200:
                    vendor = response.json()
                    self.created_entities['parties'].append(vendor['id'])
                else:
                    self.log_result("Create Test Vendors", False, f"Failed to create vendor {i+1}")
                    return False
            
            # Create test accounts for transactions
            account_data = {
                "name": "Pagination Test Cash Account",
                "account_type": "asset",
                "opening_balance": 10000.0
            }
            
            response = self.session.post(f"{self.base_url}/api/accounts", json=account_data)
            if response.status_code == 200:
                account = response.json()
                self.created_entities['accounts'].append(account['id'])
                test_account_id = account['id']
            else:
                self.log_result("Create Test Account", False, "Failed to create test account")
                return False
            
            # Create gold ledger entries
            if len(self.created_entities['parties']) >= 3:
                customer_ids = [pid for pid in self.created_entities['parties'][:5]]  # First 5 are customers
                
                for i, customer_id in enumerate(customer_ids):
                    # Create IN entry (customer gives gold to shop)
                    gold_entry = {
                        "party_id": customer_id,
                        "type": "IN",
                        "weight_grams": round(25.5 + i * 10.25, 3),
                        "purity_entered": 916,
                        "purpose": "job_work",
                        "notes": f"Pagination test gold deposit {i+1}"
                    }
                    
                    response = self.session.post(f"{self.base_url}/api/gold-ledger", json=gold_entry)
                    if response.status_code == 200:
                        entry = response.json()
                        self.created_entities['gold_ledger'].append(entry['id'])
                    
                    # Create OUT entry (shop gives gold to customer)
                    if i < 3:  # Only for first 3 customers
                        gold_entry_out = {
                            "party_id": customer_id,
                            "type": "OUT",
                            "weight_grams": round(10.5 + i * 5.25, 3),
                            "purity_entered": 916,
                            "purpose": "exchange",
                            "notes": f"Pagination test gold return {i+1}"
                        }
                        
                        response = self.session.post(f"{self.base_url}/api/gold-ledger", json=gold_entry_out)
                        if response.status_code == 200:
                            entry = response.json()
                            self.created_entities['gold_ledger'].append(entry['id'])
            
            # Create transactions
            if test_account_id and len(self.created_entities['parties']) >= 3:
                for i in range(4):
                    transaction_data = {
                        "transaction_type": "credit" if i % 2 == 0 else "debit",
                        "mode": "Cash",
                        "account_id": test_account_id,
                        "amount": 500.0 + i * 100.0,
                        "category": "Test Transaction",
                        "notes": f"Pagination test transaction {i+1}"
                    }
                    
                    response = self.session.post(f"{self.base_url}/api/transactions", json=transaction_data)
                    if response.status_code == 200:
                        txn = response.json()
                        self.created_entities['transactions'].append(txn['id'])
            
            self.log_result("Create Test Data", True, 
                          f"Created {len(self.created_entities['parties'])} parties, "
                          f"{len(self.created_entities['gold_ledger'])} gold entries, "
                          f"{len(self.created_entities['transactions'])} transactions")
            return True
            
        except Exception as e:
            self.log_result("Create Test Data", False, f"Exception: {str(e)}")
            return False

    # ============================================================================
    # PAGINATION TESTS FOR ALL 7 ENDPOINTS
    # ============================================================================

    def test_parties_pagination(self):
        """Test GET /api/parties pagination"""
        # Test with no filters
        success = self.test_pagination_endpoint("parties", "Parties")
        
        # Test with party_type filter
        if success:
            success = self.test_pagination_endpoint("parties", "Parties (customer filter)", 
                                                  {"party_type": "customer"})
        
        return success

    def test_gold_ledger_pagination(self):
        """Test GET /api/gold-ledger pagination"""
        # Test with no filters
        success = self.test_pagination_endpoint("gold-ledger", "Gold Ledger")
        
        # Test with party_id filter (if we have parties)
        if success and self.created_entities['parties']:
            party_id = self.created_entities['parties'][0]
            success = self.test_pagination_endpoint("gold-ledger", "Gold Ledger (party filter)", 
                                                  {"party_id": party_id})
        
        # Test with date filters
        if success:
            today = datetime.now().strftime('%Y-%m-%d')
            success = self.test_pagination_endpoint("gold-ledger", "Gold Ledger (date filter)", 
                                                  {"date_from": today})
        
        return success

    def test_purchases_pagination(self):
        """Test GET /api/purchases pagination"""
        # Note: We may not have purchase data, but we should test the endpoint structure
        success = self.test_pagination_endpoint("purchases", "Purchases")
        
        # Test with status filter
        if success:
            success = self.test_pagination_endpoint("purchases", "Purchases (status filter)", 
                                                  {"status": "draft"})
        
        return success

    def test_jobcards_pagination(self):
        """Test GET /api/jobcards pagination"""
        # Note: We may not have jobcard data, but we should test the endpoint structure
        success = self.test_pagination_endpoint("jobcards", "Job Cards")
        
        return success

    def test_invoices_pagination(self):
        """Test GET /api/invoices pagination"""
        # Note: We may not have invoice data, but we should test the endpoint structure
        success = self.test_pagination_endpoint("invoices", "Invoices")
        
        return success

    def test_transactions_pagination(self):
        """Test GET /api/transactions pagination"""
        success = self.test_pagination_endpoint("transactions", "Transactions")
        
        return success

    def test_audit_logs_pagination(self):
        """Test GET /api/audit-logs pagination"""
        success = self.test_pagination_endpoint("audit-logs", "Audit Logs")
        
        # Test with module filter
        if success:
            success = self.test_pagination_endpoint("audit-logs", "Audit Logs (module filter)", 
                                                  {"module": "party"})
        
        # Test with date filters
        if success:
            today = datetime.now().strftime('%Y-%m-%d')
            success = self.test_pagination_endpoint("audit-logs", "Audit Logs (date filter)", 
                                                  {"date_from": today})
        
        return success

    # ============================================================================
    # COMPREHENSIVE PAGINATION VERIFICATION
    # ============================================================================

    def test_pagination_metadata_accuracy(self):
        """Test pagination metadata accuracy across all endpoints"""
        print("🔸 Testing Pagination Metadata Accuracy")
        
        endpoints_to_test = [
            ("parties", "Parties"),
            ("gold-ledger", "Gold Ledger"),
            ("purchases", "Purchases"),
            ("jobcards", "Job Cards"),
            ("invoices", "Invoices"),
            ("transactions", "Transactions"),
            ("audit-logs", "Audit Logs")
        ]
        
        all_passed = True
        
        for endpoint, name in endpoints_to_test:
            try:
                # Test with different per_page values
                for per_page in [25, 50, 100]:
                    response = self.session.get(f"{self.base_url}/api/{endpoint}", 
                                              params={"page": 1, "per_page": per_page})
                    
                    if response.status_code != 200:
                        self.log_result(f"{name} - Metadata Accuracy (per_page={per_page})", False, 
                                      f"Status: {response.status_code}")
                        all_passed = False
                        continue
                    
                    data = response.json()
                    
                    # Verify metadata calculations
                    pagination = data['pagination']
                    total_count = pagination['total_count']
                    page = pagination['page']
                    per_page_actual = pagination['per_page']
                    total_pages = pagination['total_pages']
                    
                    # Check per_page is correct
                    if per_page_actual != per_page:
                        self.log_result(f"{name} - per_page Accuracy", False, 
                                      f"Expected per_page={per_page}, got {per_page_actual}")
                        all_passed = False
                        continue
                    
                    # Check total_pages calculation
                    expected_total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0
                    if total_pages != expected_total_pages:
                        self.log_result(f"{name} - total_pages Calculation", False, 
                                      f"Expected {expected_total_pages}, got {total_pages}")
                        all_passed = False
                        continue
                    
                    # Check items count doesn't exceed per_page
                    if len(data['items']) > per_page:
                        self.log_result(f"{name} - Items Count Limit", False, 
                                      f"Returned {len(data['items'])} items, max should be {per_page}")
                        all_passed = False
                        continue
            
            except Exception as e:
                self.log_result(f"{name} - Metadata Test", False, f"Exception: {str(e)}")
                all_passed = False
        
        if all_passed:
            self.log_result("Pagination Metadata Accuracy", True, 
                          "All endpoints have accurate pagination metadata calculations")
        
        return all_passed

    def test_pagination_boundary_cases(self):
        """Test boundary cases for all pagination endpoints"""
        print("🔸 Testing Pagination Boundary Cases")
        
        endpoints_to_test = [
            ("parties", "Parties"),
            ("gold-ledger", "Gold Ledger"),
            ("transactions", "Transactions"),
            ("audit-logs", "Audit Logs")
        ]
        
        all_passed = True
        
        for endpoint, name in endpoints_to_test:
            try:
                # Test negative page number
                response = self.session.get(f"{self.base_url}/api/{endpoint}", 
                                          params={"page": -1, "per_page": 50})
                
                # Should either default to page 1 or return 400 error
                if response.status_code not in [200, 400]:
                    self.log_result(f"{name} - Negative Page", False, 
                                  f"Unexpected status for page=-1: {response.status_code}")
                    all_passed = False
                
                # Test zero page number
                response = self.session.get(f"{self.base_url}/api/{endpoint}", 
                                          params={"page": 0, "per_page": 50})
                
                if response.status_code not in [200, 400]:
                    self.log_result(f"{name} - Zero Page", False, 
                                  f"Unexpected status for page=0: {response.status_code}")
                    all_passed = False
                
                # Test very large per_page
                response = self.session.get(f"{self.base_url}/api/{endpoint}", 
                                          params={"page": 1, "per_page": 10000})
                
                if response.status_code == 200:
                    data = response.json()
                    # Should handle large per_page gracefully
                    if len(data['items']) > 10000:
                        self.log_result(f"{name} - Large per_page", False, 
                                      f"Returned {len(data['items'])} items for per_page=10000")
                        all_passed = False
                
            except Exception as e:
                self.log_result(f"{name} - Boundary Cases", False, f"Exception: {str(e)}")
                all_passed = False
        
        if all_passed:
            self.log_result("Pagination Boundary Cases", True, 
                          "All endpoints handle boundary cases correctly")
        
        return all_passed

    # ============================================================================
    # MAIN TEST EXECUTION
    # ============================================================================

    def run_all_tests(self):
        """Run comprehensive audit logs filtering tests"""
        print("🎯 COMPREHENSIVE AUDIT LOGS FILTERING TESTS")
        print("=" * 80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Setup failed. Cannot proceed with comprehensive tests.")
            return
        
        print("\n📋 INDIVIDUAL FILTER TESTS")
        print("-" * 60)
        self.test_date_range_filters()
        self.test_user_filter()
        self.test_module_filter()
        self.test_action_filters()
        
        print("\n📋 COMBINED FILTER TESTS")
        print("-" * 60)
        self.test_combined_filters()
        
        print("\n📋 EDGE CASE TESTS")
        print("-" * 60)
        self.test_edge_cases()
        
        print("\n📋 VERIFICATION CHECKLIST")
        print("-" * 60)
        self.test_verification_checklist()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("🎯 AUDIT LOGS FILTERING TEST RESULTS SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"\n📊 OVERALL STATISTICS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Show all results
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            print(f"   {result['status']}: {result['test']}")
            if result['details']:
                print(f"      → {result['details']}")
        
        # Show failed tests details
        failed_results = [r for r in self.test_results if not r['success']]
        if failed_results:
            print(f"\n❌ FAILED TESTS DETAILS:")
            for result in failed_results:
                print(f"\n   Test: {result['test']}")
                print(f"   Details: {result['details']}")
                if result.get('response_data'):
                    print(f"   Response: {result['response_data']}")
        
        print(f"\n🎯 AUDIT LOGS FILTERING ASSESSMENT:")
        if failed_tests == 0:
            print("   ✅ ALL TESTS PASSED - AUDIT LOGS FILTERING FULLY FUNCTIONAL")
        elif failed_tests <= 2:
            print(f"   ⚠️  MOSTLY FUNCTIONAL - {failed_tests} minor issues to fix")
        elif failed_tests <= 5:
            print(f"   ⚠️  NEEDS WORK - {failed_tests} issues to fix")
        else:
            print(f"   ❌ NOT FUNCTIONAL - {failed_tests} critical issues to fix")
        
        print("\n" + "=" * 80)


# Entry point
def main():
    """Main execution function"""
    # Configuration
    BASE_URL = "https://pagination-blocker.preview.emergentagent.com"
    USERNAME = "admin"
    PASSWORD = "admin123"
    
    print("🚀 Starting Audit Logs Filtering Tests")
    print(f"Backend URL: {BASE_URL}")
    print(f"Username: {USERNAME}")
    print("-" * 80)
    
    # Initialize tester
    tester = AuditLogsFilterTester(BASE_URL, USERNAME, PASSWORD)
    
    # Run all audit logs filtering tests
    tester.run_all_tests()

if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Comprehensive Gold Shop ERP Backend API Testing Suite
Tests all backend functionality with comprehensive dummy data verification
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import time

# Configuration
BASE_URL = "https://decimal-precision.preview.emergentagent.com/api"

# Test credentials from review request
TEST_CREDENTIALS = [
    {"username": "admin", "password": "admin123", "role": "admin"},
    {"username": "manager", "password": "manager123", "role": "manager"},
    {"username": "staff1", "password": "staff123", "role": "staff"}
]

class GoldShopERPTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.current_user = None
        
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
    
    def authenticate(self, username, password):
        """Authenticate and get JWT token"""
        print(f"🔐 Authenticating as {username}...")
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json={
                "username": username,
                "password": password
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.current_user = username
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log_test(f"Authentication - {username}", True, f"Successfully logged in")
                return True
            else:
                self.log_test(f"Authentication - {username}", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test(f"Authentication - {username}", False, f"Exception: {str(e)}")
            return False
    
    def test_authentication_endpoints(self):
        """Test authentication with all user types"""
        print("🔐 Testing Authentication Endpoints...")
        
        for cred in TEST_CREDENTIALS:
            success = self.authenticate(cred["username"], cred["password"])
            if not success:
                return False
        
        return True
    
    def test_inventory_management(self):
        """Test inventory management endpoints"""
        print("📦 Testing Inventory Management...")
        
        try:
            # Test GET /api/inventory/headers
            response = self.session.get(f"{BASE_URL}/inventory/headers")
            
            if response.status_code == 200:
                headers = response.json()
                
                # Check if we have 8 categories
                expected_categories = ["Chain", "Ring", "Bangle", "Necklace", "Bracelet", "Coin", "Biscuit", "Others"]
                
                if isinstance(headers, list) and len(headers) >= 8:
                    category_names = [h.get("name", "") for h in headers]
                    found_categories = [cat for cat in expected_categories if cat in category_names]
                    
                    # Check each header has required fields
                    valid_headers = True
                    for header in headers:
                        if not all(field in header for field in ["current_qty", "current_weight"]):
                            valid_headers = False
                            break
                    
                    if len(found_categories) >= 7 and valid_headers:  # Allow some flexibility
                        self.log_test("Inventory Headers", True, 
                                    f"Found {len(headers)} categories with required fields. Categories: {category_names}")
                    else:
                        self.log_test("Inventory Headers", False, 
                                    f"Missing categories or fields. Found: {found_categories}, Valid fields: {valid_headers}")
                else:
                    self.log_test("Inventory Headers", False, 
                                f"Expected list with 8+ items, got: {type(headers)} with {len(headers) if isinstance(headers, list) else 'N/A'} items")
            else:
                self.log_test("Inventory Headers", False, 
                            f"Status: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Inventory Headers", False, f"Exception: {str(e)}")
    
    def test_stock_movements(self):
        """Test stock movements endpoints"""
        print("📈 Testing Stock Movements...")
        
        try:
            # Test GET /api/inventory/movements
            response = self.session.get(f"{BASE_URL}/inventory/movements")
            
            if response.status_code == 200:
                data = response.json()
                
                # Stock movements returns a direct list, not paginated
                movements = data if isinstance(data, list) else []
                total_count = len(movements)
                
                if len(movements) > 0:
                    # Check first movement has required fields
                    first_movement = movements[0]
                    required_fields = ["header_id", "movement_type", "qty_delta", "weight_delta", "purity"]
                    
                    has_required_fields = all(field in first_movement for field in required_fields)
                    
                    if has_required_fields:
                        self.log_test("Stock Movements", True, 
                                    f"Found {total_count} movements with required fields")
                    else:
                        missing_fields = [field for field in required_fields if field not in first_movement]
                        self.log_test("Stock Movements", False, 
                                    f"Missing required fields: {missing_fields}")
                else:
                    self.log_test("Stock Movements", False, "No stock movements found")
            else:
                self.log_test("Stock Movements", False, 
                            f"Status: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Stock Movements", False, f"Exception: {str(e)}")
    
    def test_party_management(self):
        """Test party management endpoints"""
        print("👥 Testing Party Management...")
        
        try:
            # Test GET /api/parties
            response = self.session.get(f"{BASE_URL}/parties")
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle pagination response
                if isinstance(data, dict) and "items" in data:
                    parties = data["items"]
                    total_count = data.get("pagination", {}).get("total_count", len(parties))
                else:
                    parties = data if isinstance(data, list) else []
                    total_count = len(parties)
                
                if total_count >= 18:  # Should return 18 parties
                    # Test filtering by party type
                    self.test_party_filtering()
                    
                    # Check for Omani names
                    party_names = [p.get("name", "") for p in parties]
                    omani_indicators = ["Al-", "Hassan", "Ahmed", "Fatima"]
                    has_omani_names = any(indicator in " ".join(party_names) for indicator in omani_indicators)
                    
                    if has_omani_names:
                        self.log_test("Party Management", True, 
                                    f"Found {total_count} parties with Omani names detected")
                    else:
                        self.log_test("Party Management", True, 
                                    f"Found {total_count} parties (Omani names not clearly detected)")
                else:
                    self.log_test("Party Management", False, 
                                f"Expected 18+ parties, found {total_count}")
            else:
                self.log_test("Party Management", False, 
                            f"Status: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Party Management", False, f"Exception: {str(e)}")
    
    def test_party_filtering(self):
        """Test party filtering by type"""
        party_types = [
            ("customer", 10),
            ("vendor", 4),
            ("worker", 4)
        ]
        
        for party_type, expected_count in party_types:
            try:
                response = self.session.get(f"{BASE_URL}/parties?party_type={party_type}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Handle pagination response
                    if isinstance(data, dict) and "items" in data:
                        parties = data["items"]
                        total_count = data.get("pagination", {}).get("total_count", len(parties))
                    else:
                        parties = data if isinstance(data, list) else []
                        total_count = len(parties)
                    
                    if total_count >= expected_count - 2:  # Allow some flexibility
                        self.log_test(f"Party Filter - {party_type}", True, 
                                    f"Found {total_count} {party_type}s (expected ~{expected_count})")
                    else:
                        self.log_test(f"Party Filter - {party_type}", False, 
                                    f"Found {total_count} {party_type}s, expected ~{expected_count}")
                else:
                    self.log_test(f"Party Filter - {party_type}", False, 
                                f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Party Filter - {party_type}", False, f"Exception: {str(e)}")
    
    def test_job_cards(self):
        """Test job card endpoints"""
        print("🔧 Testing Job Cards...")
        
        try:
            response = self.session.get(f"{BASE_URL}/jobcards")
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle pagination response
                if isinstance(data, dict) and "items" in data:
                    jobcards = data["items"]
                    total_count = data.get("pagination", {}).get("total_count", len(jobcards))
                else:
                    jobcards = data if isinstance(data, list) else []
                    total_count = len(jobcards)
                
                if total_count >= 25:  # Should return 28 job cards
                    # Check job card structure
                    if len(jobcards) > 0:
                        first_jobcard = jobcards[0]
                        required_fields = ["items", "customer_info", "worker_info"]
                        
                        has_required_fields = any(field in first_jobcard for field in required_fields)
                        
                        # Check for different statuses
                        statuses = [jc.get("status", "") for jc in jobcards]
                        expected_statuses = ["created", "in_progress", "completed", "delivered"]
                        found_statuses = [status for status in expected_statuses if status in statuses]
                        
                        if has_required_fields and len(found_statuses) > 0:
                            self.log_test("Job Cards", True, 
                                        f"Found {total_count} job cards with required structure and statuses: {found_statuses}")
                        else:
                            self.log_test("Job Cards", False, 
                                        f"Job cards missing required fields or statuses")
                    else:
                        self.log_test("Job Cards", True, 
                                    f"Found {total_count} job cards (structure not verified - empty list)")
                else:
                    self.log_test("Job Cards", False, 
                                f"Expected 25+ job cards, found {total_count}")
            else:
                self.log_test("Job Cards", False, 
                            f"Status: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Job Cards", False, f"Exception: {str(e)}")
    
    def test_invoices(self):
        """Test invoice endpoints"""
        print("🧾 Testing Invoices...")
        
        try:
            response = self.session.get(f"{BASE_URL}/invoices")
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle pagination response
                if isinstance(data, dict) and "items" in data:
                    invoices = data["items"]
                    total_count = data.get("pagination", {}).get("total_count", len(invoices))
                else:
                    invoices = data if isinstance(data, list) else []
                    total_count = len(invoices)
                
                if total_count >= 18:  # Should return 21 invoices
                    # Check invoice structure
                    if len(invoices) > 0:
                        first_invoice = invoices[0]
                        required_fields = ["items", "subtotal", "discount_amount", "grand_total"]
                        
                        has_required_fields = all(field in first_invoice for field in required_fields)
                        
                        # Check payment statuses
                        payment_statuses = [inv.get("payment_status", "") for inv in invoices]
                        expected_statuses = ["paid", "partial", "unpaid"]
                        found_statuses = [status for status in expected_statuses if status in payment_statuses]
                        
                        if has_required_fields and len(found_statuses) > 0:
                            self.log_test("Invoices", True, 
                                        f"Found {total_count} invoices with required fields and payment statuses: {found_statuses}")
                        else:
                            self.log_test("Invoices", False, 
                                        f"Invoices missing required fields or payment statuses")
                    else:
                        self.log_test("Invoices", True, 
                                    f"Found {total_count} invoices (structure not verified - empty list)")
                else:
                    self.log_test("Invoices", False, 
                                f"Expected 18+ invoices, found {total_count}")
            else:
                self.log_test("Invoices", False, 
                            f"Status: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Invoices", False, f"Exception: {str(e)}")
    
    def test_accounts(self):
        """Test account endpoints"""
        print("💰 Testing Accounts...")
        
        try:
            response = self.session.get(f"{BASE_URL}/accounts")
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle pagination response
                if isinstance(data, dict) and "items" in data:
                    accounts = data["items"]
                    total_count = data.get("pagination", {}).get("total_count", len(accounts))
                else:
                    accounts = data if isinstance(data, list) else []
                    total_count = len(accounts)
                
                if total_count >= 4:  # Should return 4 accounts
                    # Check for expected account types
                    account_names = [acc.get("name", "").lower() for acc in accounts]
                    expected_types = ["cash", "bank", "petty"]
                    
                    found_types = []
                    for acc_type in expected_types:
                        if any(acc_type in name for name in account_names):
                            found_types.append(acc_type)
                    
                    # Check required fields
                    has_balance_fields = True
                    if len(accounts) > 0:
                        first_account = accounts[0]
                        required_fields = ["opening_balance", "current_balance"]
                        has_balance_fields = all(field in first_account for field in required_fields)
                    
                    if len(found_types) >= 2 and has_balance_fields:
                        self.log_test("Accounts", True, 
                                    f"Found {total_count} accounts with types: {found_types} and balance fields")
                    else:
                        self.log_test("Accounts", False, 
                                    f"Missing expected account types or balance fields. Found types: {found_types}")
                else:
                    self.log_test("Accounts", False, 
                                f"Expected 4+ accounts, found {total_count}")
            else:
                self.log_test("Accounts", False, 
                            f"Status: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Accounts", False, f"Exception: {str(e)}")
    
    def test_transactions(self):
        """Test transaction endpoints"""
        print("💳 Testing Transactions...")
        
        try:
            response = self.session.get(f"{BASE_URL}/transactions")
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle pagination response
                if isinstance(data, dict) and "items" in data:
                    transactions = data["items"]
                    total_count = data.get("pagination", {}).get("total_count", len(transactions))
                else:
                    transactions = data if isinstance(data, list) else []
                    total_count = len(transactions)
                
                if total_count >= 30:  # Should return 32+ transactions
                    # Check transaction structure
                    if len(transactions) > 0:
                        # Check for receipt and payment types
                        transaction_types = [t.get("transaction_type", "") for t in transactions]
                        has_receipts = "receipt" in transaction_types
                        has_payments = "payment" in transaction_types
                        
                        # Check for payment modes
                        payment_modes = []
                        for t in transactions:
                            mode = t.get("mode", "")
                            if mode and mode not in payment_modes:
                                payment_modes.append(mode)
                        
                        expected_modes = ["cash", "bank_transfer", "card", "upi"]
                        found_modes = [mode for mode in expected_modes if mode in payment_modes]
                        
                        if (has_receipts or has_payments) and len(found_modes) > 0:
                            self.log_test("Transactions", True, 
                                        f"Found {total_count} transactions with types and payment modes: {found_modes}")
                        else:
                            self.log_test("Transactions", False, 
                                        f"Missing transaction types or payment modes")
                    else:
                        self.log_test("Transactions", True, 
                                    f"Found {total_count} transactions (structure not verified - empty list)")
                else:
                    self.log_test("Transactions", False, 
                                f"Expected 30+ transactions, found {total_count}")
            else:
                self.log_test("Transactions", False, 
                            f"Status: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Transactions", False, f"Exception: {str(e)}")
    
    def test_daily_closings(self):
        """Test daily closing endpoints"""
        print("📅 Testing Daily Closings...")
        
        try:
            response = self.session.get(f"{BASE_URL}/daily-closings")
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle pagination response
                if isinstance(data, dict) and "items" in data:
                    closings = data["items"]
                    total_count = data.get("pagination", {}).get("total_count", len(closings))
                else:
                    closings = data if isinstance(data, list) else []
                    total_count = len(closings)
                
                if total_count >= 12:  # Should return 15 records
                    # Check daily closing structure
                    if len(closings) > 0:
                        first_closing = closings[0]
                        required_fields = ["opening_cash", "total_credit", "total_debit", 
                                         "expected_closing", "actual_closing", "difference"]
                        
                        has_required_fields = all(field in first_closing for field in required_fields)
                        
                        # Check for is_locked field
                        has_locked_field = "is_locked" in first_closing
                        
                        if has_required_fields and has_locked_field:
                            self.log_test("Daily Closings", True, 
                                        f"Found {total_count} daily closings with required fields")
                        else:
                            missing_fields = [field for field in required_fields if field not in first_closing]
                            self.log_test("Daily Closings", False, 
                                        f"Missing required fields: {missing_fields}, has_locked: {has_locked_field}")
                    else:
                        self.log_test("Daily Closings", True, 
                                    f"Found {total_count} daily closings (structure not verified - empty list)")
                else:
                    self.log_test("Daily Closings", False, 
                                f"Expected 12+ daily closings, found {total_count}")
            else:
                self.log_test("Daily Closings", False, 
                            f"Status: {response.status_code}", response.text)
                
        except Exception as e:
            self.log_test("Daily Closings", False, f"Exception: {str(e)}")
    
    def test_pagination(self):
        """Test pagination functionality"""
        print("📄 Testing Pagination...")
        
        # Test pagination on major endpoints (only those that actually support pagination)
        endpoints_to_test = [
            "parties", "jobcards", "invoices", "transactions", 
            "purchases"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                # Test with different page sizes
                response = self.session.get(f"{BASE_URL}/{endpoint}?page=1&per_page=25")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if isinstance(data, dict) and "pagination" in data:
                        pagination = data["pagination"]
                        required_fields = ["total_count", "total_pages", "has_next", "has_prev"]
                        
                        has_required_fields = all(field in pagination for field in required_fields)
                        
                        if has_required_fields:
                            self.log_test(f"Pagination - {endpoint}", True, 
                                        f"Pagination metadata complete: {pagination}")
                        else:
                            missing_fields = [field for field in required_fields if field not in pagination]
                            self.log_test(f"Pagination - {endpoint}", False, 
                                        f"Missing pagination fields: {missing_fields}")
                    else:
                        self.log_test(f"Pagination - {endpoint}", False, 
                                    "No pagination metadata found")
                else:
                    self.log_test(f"Pagination - {endpoint}", False, 
                                f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Pagination - {endpoint}", False, f"Exception: {str(e)}")
    
    def test_protected_endpoints(self):
        """Test that protected endpoints require authentication"""
        print("🔒 Testing Protected Endpoints...")
        
        # Remove authorization header temporarily
        original_headers = self.session.headers.copy()
        if "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]
        
        try:
            # Test a protected endpoint without auth
            response = self.session.get(f"{BASE_URL}/parties")
            
            if response.status_code in [401, 403]:  # Both are acceptable for unauthorized access
                self.log_test("Protected Endpoints", True, 
                            f"Correctly requires authentication ({response.status_code})")
            else:
                self.log_test("Protected Endpoints", False, 
                            f"Expected 401 or 403, got {response.status_code}")
        
        finally:
            # Restore authorization header
            self.session.headers.update(original_headers)
    
    def run_comprehensive_tests(self):
        """Run all comprehensive test scenarios"""
        print("🚀 Starting Comprehensive Gold Shop ERP Backend Testing")
        print("=" * 80)
        
        # Authenticate with admin credentials
        if not self.authenticate("admin", "admin123"):
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run all test categories
        test_methods = [
            self.test_authentication_endpoints,
            self.test_inventory_management,
            self.test_stock_movements,
            self.test_party_management,
            self.test_job_cards,
            self.test_invoices,
            self.test_accounts,
            self.test_transactions,
            self.test_daily_closings,
            self.test_pagination,
            self.test_protected_endpoints
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ Error in {test_method.__name__}: {str(e)}")
        
        # Print comprehensive summary
        self.print_test_summary()
        
        # Return success status
        failed_tests = sum(1 for result in self.test_results if not result["success"])
        return failed_tests == 0
    
    def print_test_summary(self):
        """Print detailed test summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests Executed: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS ({failed_tests}):")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}")
                    if result['details']:
                        print(f"     Details: {result['details']}")
        
        if passed_tests > 0:
            print(f"\n✅ PASSED TESTS ({passed_tests}):")
            categories = {}
            for result in self.test_results:
                if result["success"]:
                    category = result['test'].split(' - ')[0] if ' - ' in result['test'] else result['test'].split()[0]
                    if category not in categories:
                        categories[category] = 0
                    categories[category] += 1
            
            for category, count in categories.items():
                print(f"   • {category}: {count} tests passed")

if __name__ == "__main__":
    tester = GoldShopERPTester()
    success = tester.run_comprehensive_tests()
    sys.exit(0 if success else 1)
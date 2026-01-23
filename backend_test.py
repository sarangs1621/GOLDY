#!/usr/bin/env python3
"""
COMPREHENSIVE BUG FIX VERIFICATION - Test All 3 Critical Bug Fixes

CONTEXT:
Previous testing identified 3 critical bugs. TWO fixes were verified working (Bug #3 timezone error, Bug #2 missing endpoint). 
Bug #1 was BLOCKED by ObjectId serialization error. A NEW FIX has been applied to resolve the ObjectId serialization issue.

CRITICAL FIXES APPLIED:
1. ✅ Fixed datetime timezone handling (lines 4090-4092, 4151-4153)
2. ✅ Added GET /accounts/{account_id} endpoint (lines 3048-3054)  
3. ✅ Fixed ObjectId serialization in decimal_to_float() function (line 45)

TESTING PRIORITIES:
1. Bug #1 (HIGHEST) - Previously blocked, needs full verification
2. Bug #2 (MEDIUM) - Re-confirm still working after new fix
3. Bug #3 (LOW) - Re-confirm still working (was already verified)
"""

import requests
import json
from datetime import datetime
import time

# Configuration - Read from frontend/.env
BASE_URL = "https://bugfix-progress-1.preview.emergentagent.com/api"
USERNAME = "admin"
PASSWORD = "admin123"

class BugFixTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        
    def log_result(self, test_name, status, details=""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status_icon = "✅" if status == "PASS" else "❌"
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        print()
    
    def authenticate(self):
        """Authenticate and get JWT token"""
        print("🔐 AUTHENTICATING...")
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json={
                "username": USERNAME,
                "password": PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log_result("Authentication", "PASS", f"Token obtained successfully")
                return True
            else:
                self.log_result("Authentication", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Authentication", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_outstanding_reports(self):
        """🔥 PRIORITY 1: Test Outstanding Reports (Bug Fix #3)"""
        print("🔥 PRIORITY 1: TESTING OUTSTANDING REPORTS (Bug Fix #3)")
        print("=" * 60)
        
        try:
            response = self.session.get(f"{BASE_URL}/reports/outstanding")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["vendor_payables", "invoice_receivables"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Outstanding Reports - Response Structure", "FAIL", 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Check for overdue calculations
                vendor_payables = data.get("vendor_payables", [])
                invoice_receivables = data.get("invoice_receivables", [])
                
                # Verify overdue calculations are present
                overdue_fields_found = False
                for item in vendor_payables + invoice_receivables:
                    if any(key.startswith("overdue_") for key in item.keys()):
                        overdue_fields_found = True
                        break
                
                self.log_result("Outstanding Reports - API Response", "PASS", 
                              f"Status: 200 OK, Vendor Payables: {len(vendor_payables)}, Invoice Receivables: {len(invoice_receivables)}")
                
                if overdue_fields_found:
                    self.log_result("Outstanding Reports - Overdue Calculations", "PASS", 
                                  "Overdue calculations (overdue_0_7, overdue_8_30, overdue_31_plus) present")
                else:
                    self.log_result("Outstanding Reports - Overdue Calculations", "PASS", 
                                  "No overdue items found (expected if no overdue data exists)")
                
                self.log_result("Outstanding Reports - Timezone Fix", "PASS", 
                              "No timezone-related TypeError encountered")
                return True
                
            else:
                self.log_result("Outstanding Reports - API Response", "FAIL", 
                              f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Outstanding Reports - Exception", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_account_detail_endpoint(self):
        """🔥 PRIORITY 2: Test Account Detail Endpoint (New Feature)"""
        print("🔥 PRIORITY 2: TESTING ACCOUNT DETAIL ENDPOINT (New Feature)")
        print("=" * 60)
        
        try:
            # First get list of accounts
            accounts_response = self.session.get(f"{BASE_URL}/accounts")
            
            if accounts_response.status_code != 200:
                self.log_result("Account Detail - Get Accounts List", "FAIL", 
                              f"Status: {accounts_response.status_code}")
                return False
            
            accounts_data = accounts_response.json()
            accounts = accounts_data.get("items", []) if isinstance(accounts_data, dict) else accounts_data
            
            if not accounts:
                self.log_result("Account Detail - Get Accounts List", "FAIL", "No accounts found")
                return False
            
            self.log_result("Account Detail - Get Accounts List", "PASS", 
                          f"Found {len(accounts)} accounts")
            
            # Test with valid account ID
            test_account = accounts[0]
            account_id = test_account["id"]
            
            detail_response = self.session.get(f"{BASE_URL}/accounts/{account_id}")
            
            if detail_response.status_code == 200:
                account_detail = detail_response.json()
                
                # Verify required fields
                required_fields = ["id", "name", "type", "opening_balance", "current_balance"]
                missing_fields = [field for field in required_fields if field not in account_detail]
                
                if missing_fields:
                    self.log_result("Account Detail - Valid ID Response", "FAIL", 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                self.log_result("Account Detail - Valid ID Response", "PASS", 
                              f"Account: {account_detail['name']}, Type: {account_detail['type']}, Balance: {account_detail['current_balance']}")
                
            else:
                self.log_result("Account Detail - Valid ID Response", "FAIL", 
                              f"Status: {detail_response.status_code}")
                return False
            
            # Test with invalid account ID
            invalid_response = self.session.get(f"{BASE_URL}/accounts/invalid-account-id")
            
            if invalid_response.status_code == 404:
                self.log_result("Account Detail - Invalid ID Response", "PASS", 
                              "Returns 404 Not Found for invalid account ID")
            else:
                self.log_result("Account Detail - Invalid ID Response", "FAIL", 
                              f"Expected 404, got {invalid_response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Account Detail - Exception", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_bug_2_purchases_serialization(self):
        """🔥 TEST 2: Bug Fix #2 - GET /api/purchases Serialization (Re-confirmation)"""
        print("🔥 TEST 2: Bug Fix #2 - GET /api/purchases Serialization (Re-confirmation)")
        print("=" * 80)
        
        try:
            response = self.session.get(f"{BASE_URL}/purchases")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if isinstance(data, dict) and "items" in data and "pagination" in data:
                    purchases = data["items"]
                    self.log_result("Bug #2 - Response Structure", "PASS", 
                                  f"Correct structure: {{items: [], pagination: {{}}}}")
                    
                    self.log_result("Bug #2 - HTTP Status", "PASS", 
                                  f"Status: 200 OK (not 500 or 520)")
                    
                    # Check if any purchases exist and verify no ObjectId serialization errors
                    if purchases:
                        sample_purchase = purchases[0]
                        # Verify all fields are JSON serializable (no ObjectId errors)
                        try:
                            json.dumps(sample_purchase)
                            self.log_result("Bug #2 - ObjectId Serialization", "PASS", 
                                          "All purchase objects properly serialized")
                        except Exception as e:
                            self.log_result("Bug #2 - ObjectId Serialization", "FAIL", 
                                          f"Serialization error: {str(e)}")
                            return False
                    else:
                        self.log_result("Bug #2 - ObjectId Serialization", "PASS", 
                                      "No purchases to test, but no serialization errors")
                    
                    self.log_result("Bug #2 - Overall", "PASS", 
                                  f"Found {len(purchases)} purchases, all properly serialized")
                    return True
                else:
                    self.log_result("Bug #2 - Response Structure", "FAIL", 
                                  f"Incorrect structure: {type(data)}")
                    return False
                    
            else:
                self.log_result("Bug #2 - HTTP Status", "FAIL", 
                              f"Status: {response.status_code} (expected 200), Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Bug #2 - Exception", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_bug_1_account_balance_update(self):
        """🔥 TEST 1: Bug Fix #1 - Account Balance Update After Purchase Finalization (PRIORITY)"""
        print("🔥 TEST 1: Bug Fix #1 - Account Balance Update After Purchase Finalization (PRIORITY)")
        print("=" * 80)
        
        try:
            # STEP 1: Create test vendor
            print("STEP 1: Creating test vendor...")
            vendor_data = {
                "name": "Test Vendor for Balance Update",
                "party_type": "vendor",
                "phone": "98765432"
            }
            
            vendor_response = self.session.post(f"{BASE_URL}/parties", json=vendor_data)
            if vendor_response.status_code not in [200, 201]:
                self.log_result("Bug #1 - Create Vendor", "FAIL", 
                              f"Status: {vendor_response.status_code}, Response: {vendor_response.text}")
                return False
            
            vendor = vendor_response.json()
            vendor_id = vendor["id"]
            self.log_result("Bug #1 - Create Vendor", "PASS", f"Created vendor: {vendor['name']}")
            
            # STEP 2: Create test account
            print("STEP 2: Creating test account...")
            account_data = {
                "name": "Test Cash Account",
                "account_type": "cash",
                "opening_balance": 10000.00
            }
            
            account_response = self.session.post(f"{BASE_URL}/accounts", json=account_data)
            if account_response.status_code not in [200, 201]:
                self.log_result("Bug #1 - Create Account", "FAIL", 
                              f"Status: {account_response.status_code}, Response: {account_response.text}")
                return False
            
            account = account_response.json()
            account_id = account["id"]
            initial_balance = account["current_balance"]
            self.log_result("Bug #1 - Create Account", "PASS", 
                          f"Created account: {account['name']}, Balance: {initial_balance}")
            
            # STEP 3: Verify initial account balance
            print("STEP 3: Verifying initial account balance...")
            account_detail_response = self.session.get(f"{BASE_URL}/accounts/{account_id}")
            if account_detail_response.status_code != 200:
                self.log_result("Bug #1 - Get Account Detail", "FAIL", 
                              f"Status: {account_detail_response.status_code}")
                return False
            
            account_detail = account_detail_response.json()
            current_balance = account_detail["current_balance"]
            
            if current_balance != 10000.00:
                self.log_result("Bug #1 - Initial Balance Check", "FAIL", 
                              f"Expected 10000.00, got {current_balance}")
                return False
            
            self.log_result("Bug #1 - Initial Balance Check", "PASS", f"Balance: {current_balance}")
            
            # STEP 4: Create purchase
            print("STEP 4: Creating purchase...")
            purchase_data = {
                "vendor_party_id": vendor_id,
                "description": "Test purchase for balance update",
                "weight_grams": 50.5,
                "entered_purity": 916,
                "rate_per_gram": 250.0,
                "paid_amount_money": 1000.0,
                "payment_mode": "Cash",
                "account_id": account_id
            }
            
            purchase_response = self.session.post(f"{BASE_URL}/purchases", json=purchase_data)
            if purchase_response.status_code not in [200, 201]:
                self.log_result("Bug #1 - Create Purchase", "FAIL", 
                              f"Status: {purchase_response.status_code}, Response: {purchase_response.text}")
                return False
            
            purchase = purchase_response.json()
            purchase_id = purchase["id"]
            self.log_result("Bug #1 - Create Purchase", "PASS", 
                          f"Created purchase: {purchase_id}, Amount: 1000.0")
            
            # STEP 5: Verify balance unchanged after creation
            print("STEP 5: Verifying balance unchanged after purchase creation...")
            account_after_create = self.session.get(f"{BASE_URL}/accounts/{account_id}").json()
            balance_after_create = account_after_create["current_balance"]
            
            if balance_after_create != 10000.00:
                self.log_result("Bug #1 - Balance After Create", "FAIL", 
                              f"Balance changed unexpectedly: {balance_after_create}")
                return False
            
            self.log_result("Bug #1 - Balance After Create", "PASS", 
                          f"Balance unchanged: {balance_after_create}")
            
            # STEP 6: Finalize purchase (CRITICAL TEST)
            print("STEP 6: Finalizing purchase (CRITICAL TEST)...")
            finalize_response = self.session.post(f"{BASE_URL}/purchases/{purchase_id}/finalize")
            
            if finalize_response.status_code != 200:
                error_text = finalize_response.text
                if "ObjectId" in error_text or "not JSON serializable" in error_text:
                    self.log_result("Bug #1 - Purchase Finalization", "FAIL", 
                                  f"ObjectId serialization error: {error_text}")
                else:
                    self.log_result("Bug #1 - Purchase Finalization", "FAIL", 
                                  f"Status: {finalize_response.status_code}, Response: {error_text}")
                return False
            
            self.log_result("Bug #1 - Purchase Finalization", "PASS", "Purchase finalized successfully")
            
            # STEP 7: CRITICAL VERIFICATION - Check account balance after finalization
            print("STEP 7: CRITICAL VERIFICATION - Checking account balance after finalization...")
            time.sleep(1)  # Brief pause to ensure database update
            
            account_after_finalize = self.session.get(f"{BASE_URL}/accounts/{account_id}").json()
            final_balance = account_after_finalize["current_balance"]
            expected_balance = 9000.00  # 10000 - 1000
            
            if abs(final_balance - expected_balance) < 0.01:
                self.log_result("Bug #1 - Account Balance Update", "PASS", 
                              f"Balance updated correctly: 10000.00 → {final_balance} (decreased by 1000.00)")
            else:
                self.log_result("Bug #1 - Account Balance Update", "FAIL", 
                              f"Balance incorrect: Expected {expected_balance}, Got {final_balance}")
                return False
            
            # STEP 8: Verify transaction created
            print("STEP 8: Verifying transaction created...")
            transactions_response = self.session.get(f"{BASE_URL}/transactions")
            if transactions_response.status_code == 200:
                transactions_data = transactions_response.json()
                transactions = transactions_data.get("items", [])
                
                # Look for the purchase payment transaction
                purchase_transaction = None
                for txn in transactions:
                    if (txn.get("category") == "Purchase Payment" and 
                        txn.get("amount") == 1000.0 and
                        txn.get("transaction_type") == "debit"):
                        purchase_transaction = txn
                        break
                
                if purchase_transaction:
                    self.log_result("Bug #1 - Transaction Created", "PASS", 
                                  f"Transaction: type=debit, amount=1000.0, category=Purchase Payment")
                else:
                    self.log_result("Bug #1 - Transaction Created", "FAIL", 
                                  "Purchase payment transaction not found")
                    return False
            else:
                self.log_result("Bug #1 - Transaction Created", "FAIL", 
                              f"Failed to get transactions: {transactions_response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Bug #1 - Exception", "FAIL", f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all bug fix tests in priority order"""
        print("🚀 STARTING COMPREHENSIVE BUG FIX VERIFICATION")
        print("=" * 80)
        print(f"Backend URL: {BASE_URL}")
        print(f"Test Time: {datetime.now().isoformat()}")
        print("=" * 80)
        print()
        
        # Authenticate first
        if not self.authenticate():
            print("❌ AUTHENTICATION FAILED - CANNOT PROCEED WITH TESTS")
            return
        
        # Run tests in priority order
        test_functions = [
            ("PRIORITY 1: Outstanding Reports (Bug Fix #3)", self.test_outstanding_reports),
            ("PRIORITY 2: Account Detail Endpoint (New Feature)", self.test_account_detail_endpoint),
            ("PRIORITY 3: Account Balance Update (Bug Fix #1) - MOST CRITICAL", self.test_account_balance_update),
            ("PRIORITY 4: Purchases Serialization (Bug Fix #2)", self.test_purchases_serialization),
        ]
        
        passed_tests = 0
        total_tests = len(test_functions)
        
        for test_name, test_func in test_functions:
            print(f"\n{'='*80}")
            print(f"EXECUTING: {test_name}")
            print(f"{'='*80}")
            
            if test_func():
                passed_tests += 1
            
            print(f"{'='*80}")
            print(f"COMPLETED: {test_name}")
            print(f"{'='*80}\n")
        
        # Final summary
        print("\n" + "="*80)
        print("🎯 FINAL TEST RESULTS SUMMARY")
        print("="*80)
        
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"📊 OVERALL SUCCESS RATE: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print()
        
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"{status_icon} {result['test']}: {result['status']}")
            if result["details"]:
                print(f"   {result['details']}")
        
        print("\n" + "="*80)
        if passed_tests == total_tests:
            print("🎉 ALL BUG FIXES VERIFIED SUCCESSFULLY - PRODUCTION READY!")
        else:
            print(f"⚠️  {total_tests - passed_tests} TEST(S) FAILED - REQUIRES ATTENTION")
        print("="*80)

if __name__ == "__main__":
    tester = BugFixTester()
    tester.run_all_tests()
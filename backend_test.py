#!/usr/bin/env python3
"""
Backend Testing Script for Critical API Fixes - Purchases and Transactions

CRITICAL FIXES TO VERIFY:
1. ✅ Purchases API - Changed from accepting Purchase model to accepting dictionary
2. ✅ Transactions API - Validated it's working correctly (requires account setup first)

TEST OBJECTIVES:
1. Verify Purchases API accepts dictionary payload (not Purchase model object)
2. Test all purchase scenarios with proper validation and error handling
3. Verify Transactions API works when valid account_id is provided
4. Test transaction creation with proper account balance updates
5. Validate numeric field precision (weights: 3 decimals, amounts: 2 decimals)
6. Test error handling for invalid data
"""

import requests
import json
import sys
from datetime import datetime
import uuid
import time

# Configuration
BASE_URL = "https://fortress-api-1.preview.emergentagent.com/api"
USERNAME = "admin"
PASSWORD = "admin123"

class CriticalAPIFixesTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.test_vendor_id = None
        self.test_account_id = None
        
    def log_result(self, test_name, status, details):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,  # "PASS", "FAIL", "ERROR"
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_symbol} {test_name}: {details}")
        
    def authenticate(self):
        """Authenticate and get JWT token"""
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json={
                "username": USERNAME,
                "password": PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log_result("Authentication", "PASS", f"Successfully authenticated as {USERNAME}")
                return True
            else:
                self.log_result("Authentication", "FAIL", f"Failed to authenticate: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Authentication", "ERROR", f"Authentication error: {str(e)}")
            return False
    
    def setup_test_data(self):
        """Create test vendor and account for testing"""
        print("\n" + "="*80)
        print("SETUP PHASE - Creating Test Data")
        print("="*80)
        
        # Create test vendor
        try:
            import random
            unique_suffix = f"{datetime.now().strftime('%H%M%S')}{random.randint(100, 999)}"
            
            vendor_data = {
                "name": f"Test Vendor Gold Supplier {unique_suffix}",
                "party_type": "vendor",
                "phone": f"99887{unique_suffix}",
                "address": "Test Address for API Testing",
                "notes": "Created for testing purchases API fixes"
            }
            
            response = self.session.post(f"{BASE_URL}/parties", json=vendor_data)
            if response.status_code == 200:
                vendor = response.json()
                self.test_vendor_id = vendor["id"]
                self.log_result("Setup - Vendor Creation", "PASS", f"Created test vendor: {vendor['name']} (ID: {self.test_vendor_id})")
            else:
                self.log_result("Setup - Vendor Creation", "FAIL", f"Failed to create vendor: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Setup - Vendor Creation", "ERROR", f"Error creating vendor: {str(e)}")
            return False
        
        # Create test account
        try:
            account_data = {
                "name": f"Test Cash Account {unique_suffix}",
                "account_type": "cash",
                "opening_balance": 10000.0,
                "notes": "Created for testing transactions API"
            }
            
            response = self.session.post(f"{BASE_URL}/accounts", json=account_data)
            if response.status_code == 200:
                account = response.json()
                self.test_account_id = account["id"]
                self.log_result("Setup - Account Creation", "PASS", f"Created test account: {account['name']} (ID: {self.test_account_id})")
                return True
            else:
                self.log_result("Setup - Account Creation", "FAIL", f"Failed to create account: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Setup - Account Creation", "ERROR", f"Error creating account: {str(e)}")
            return False
    
    def test_purchases_api_dictionary_payload(self):
        """
        CRITICAL TEST: Verify Purchases API accepts dictionary payload (not Purchase model)
        This was the main fix - endpoint should accept dict instead of Purchase model object
        """
        print("\n" + "="*80)
        print("PURCHASES API TESTING - Dictionary Payload Acceptance")
        print("="*80)
        
        # Test Case 1: Create Purchase Without Payment
        try:
            purchase_data = {
                "vendor_party_id": self.test_vendor_id,
                "description": "Test Gold Purchase 24K",
                "weight_grams": 150.500,
                "entered_purity": 999,
                "rate_per_gram": 58.75,
                "amount_total": 8841.69,
                "paid_amount_money": 0,
                "date": "2024-01-24T10:00:00Z"
            }
            
            response = self.session.post(f"{BASE_URL}/purchases", json=purchase_data)
            if response.status_code == 200:
                purchase = response.json()
                # Verify the purchase was created correctly
                if (purchase.get("status") == "draft" and 
                    abs(purchase.get("weight_grams", 0) - 150.500) < 0.001 and
                    abs(purchase.get("amount_total", 0) - 8841.69) < 0.01):
                    self.log_result("Purchases API - Dictionary Payload (No Payment)", "PASS", 
                                  f"Purchase created successfully with ID: {purchase.get('id')}, Status: {purchase.get('status')}")
                else:
                    self.log_result("Purchases API - Dictionary Payload (No Payment)", "FAIL", 
                                  f"Purchase created but data validation failed: {purchase}")
            else:
                self.log_result("Purchases API - Dictionary Payload (No Payment)", "FAIL", 
                              f"Failed to create purchase: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Purchases API - Dictionary Payload (No Payment)", "ERROR", f"Error: {str(e)}")
        
        # Test Case 2: Create Purchase With Payment
        try:
            purchase_data = {
                "vendor_party_id": self.test_vendor_id,
                "description": "Gold Purchase with Advance Payment",
                "weight_grams": 100.250,
                "entered_purity": 916,
                "rate_per_gram": 55.50,
                "amount_total": 5563.88,
                "paid_amount_money": 2000.00,
                "account_id": self.test_account_id,
                "payment_mode": "cash",
                "date": "2024-01-24T11:00:00Z"
            }
            
            response = self.session.post(f"{BASE_URL}/purchases", json=purchase_data)
            if response.status_code == 200:
                purchase = response.json()
                expected_balance = 5563.88 - 2000.00  # 3563.88
                actual_balance = purchase.get("balance_due_money", 0)
                
                if abs(actual_balance - expected_balance) < 0.01:
                    self.log_result("Purchases API - Dictionary Payload (With Payment)", "PASS", 
                                  f"Purchase with payment created correctly. Balance due: {actual_balance} OMR")
                else:
                    self.log_result("Purchases API - Dictionary Payload (With Payment)", "FAIL", 
                                  f"Balance calculation incorrect: {actual_balance}, expected: {expected_balance}")
            else:
                self.log_result("Purchases API - Dictionary Payload (With Payment)", "FAIL", 
                              f"Failed to create purchase with payment: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Purchases API - Dictionary Payload (With Payment)", "ERROR", f"Error: {str(e)}")
        
        # Test Case 3: Create Purchase With Gold Settlement
        try:
            purchase_data = {
                "vendor_party_id": self.test_vendor_id,
                "description": "Purchase with Gold Exchange",
                "weight_grams": 200.750,
                "entered_purity": 995,
                "rate_per_gram": 57.25,
                "amount_total": 11492.94,
                "paid_amount_money": 0,
                "advance_in_gold_grams": 50.500,
                "exchange_in_gold_grams": 25.250,
                "date": "2024-01-24T12:00:00Z"
            }
            
            response = self.session.post(f"{BASE_URL}/purchases", json=purchase_data)
            if response.status_code == 200:
                purchase = response.json()
                # Verify gold fields are rounded to 3 decimals
                advance_gold = purchase.get("advance_in_gold_grams", 0)
                exchange_gold = purchase.get("exchange_in_gold_grams", 0)
                
                if (abs(advance_gold - 50.500) < 0.001 and 
                    abs(exchange_gold - 25.250) < 0.001):
                    self.log_result("Purchases API - Dictionary Payload (Gold Settlement)", "PASS", 
                                  f"Purchase with gold settlement created. Advance: {advance_gold}g, Exchange: {exchange_gold}g")
                else:
                    self.log_result("Purchases API - Dictionary Payload (Gold Settlement)", "FAIL", 
                                  f"Gold field precision incorrect: Advance: {advance_gold}, Exchange: {exchange_gold}")
            else:
                self.log_result("Purchases API - Dictionary Payload (Gold Settlement)", "FAIL", 
                              f"Failed to create purchase with gold settlement: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Purchases API - Dictionary Payload (Gold Settlement)", "ERROR", f"Error: {str(e)}")
    
    def test_purchases_api_error_handling(self):
        """Test error handling for purchases API"""
        print("\n" + "="*80)
        print("PURCHASES API - Error Handling Tests")
        print("="*80)
        
        # Test Case 4: Invalid Vendor
        try:
            purchase_data = {
                "vendor_party_id": "fake-vendor-123",
                "description": "Test Purchase",
                "weight_grams": 100.0,
                "entered_purity": 999,
                "rate_per_gram": 55.00,
                "amount_total": 5500.00,
                "paid_amount_money": 0,
                "date": "2024-01-24T10:00:00Z"
            }
            
            response = self.session.post(f"{BASE_URL}/purchases", json=purchase_data)
            if response.status_code == 404 and "Vendor not found" in response.text:
                self.log_result("Purchases API - Invalid Vendor Error", "PASS", 
                              f"Correctly returned 404 for invalid vendor: {response.text}")
            else:
                self.log_result("Purchases API - Invalid Vendor Error", "FAIL", 
                              f"Unexpected response for invalid vendor: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Purchases API - Invalid Vendor Error", "ERROR", f"Error: {str(e)}")
        
        # Test Case 5: Payment Without Account
        try:
            purchase_data = {
                "vendor_party_id": self.test_vendor_id,
                "description": "Test Purchase",
                "weight_grams": 100.0,
                "entered_purity": 999,
                "rate_per_gram": 55.00,
                "amount_total": 5500.00,
                "paid_amount_money": 1000.00,  # Payment without account_id
                "date": "2024-01-24T10:00:00Z"
            }
            
            response = self.session.post(f"{BASE_URL}/purchases", json=purchase_data)
            if response.status_code == 400 and "account_id is required" in response.text:
                self.log_result("Purchases API - Payment Without Account Error", "PASS", 
                              f"Correctly returned 400 for payment without account: {response.text}")
            else:
                self.log_result("Purchases API - Payment Without Account Error", "FAIL", 
                              f"Unexpected response for payment without account: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Purchases API - Payment Without Account Error", "ERROR", f"Error: {str(e)}")
    
    def test_transactions_api_with_proper_setup(self):
        """
        CRITICAL TEST: Verify Transactions API works with proper account setup
        This validates the dependency requirement is working correctly
        """
        print("\n" + "="*80)
        print("TRANSACTIONS API TESTING - With Proper Account Setup")
        print("="*80)
        
        # Get initial account balance
        try:
            response = self.session.get(f"{BASE_URL}/accounts/{self.test_account_id}")
            if response.status_code == 200:
                account = response.json()
                initial_balance = account.get("current_balance", 0)
                self.log_result("Transactions API - Initial Balance Check", "PASS", 
                              f"Account initial balance: {initial_balance} OMR")
            else:
                self.log_result("Transactions API - Initial Balance Check", "FAIL", 
                              f"Failed to get account: {response.status_code}")
                return
        except Exception as e:
            self.log_result("Transactions API - Initial Balance Check", "ERROR", f"Error: {str(e)}")
            return
        
        # Test Case 1: Create Credit Transaction
        try:
            transaction_data = {
                "account_id": self.test_account_id,
                "transaction_type": "credit",
                "mode": "cash",
                "amount": 5000.00,
                "category": "sales",
                "notes": "Test sales transaction"
            }
            
            response = self.session.post(f"{BASE_URL}/transactions", json=transaction_data)
            if response.status_code == 200:
                transaction = response.json()
                self.log_result("Transactions API - Credit Transaction", "PASS", 
                              f"Credit transaction created: {transaction.get('id')}, Amount: {transaction.get('amount')} OMR")
                
                # Verify account balance updated
                time.sleep(1)  # Brief delay for database update
                response = self.session.get(f"{BASE_URL}/accounts/{self.test_account_id}")
                if response.status_code == 200:
                    account = response.json()
                    new_balance = account.get("current_balance", 0)
                    expected_balance = initial_balance + 5000.00
                    
                    if abs(new_balance - expected_balance) < 0.01:
                        self.log_result("Transactions API - Credit Balance Update", "PASS", 
                                      f"Account balance correctly updated: {new_balance} OMR (expected: {expected_balance})")
                        initial_balance = new_balance  # Update for next test
                    else:
                        self.log_result("Transactions API - Credit Balance Update", "FAIL", 
                                      f"Balance update incorrect: {new_balance}, expected: {expected_balance}")
            else:
                self.log_result("Transactions API - Credit Transaction", "FAIL", 
                              f"Failed to create credit transaction: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Transactions API - Credit Transaction", "ERROR", f"Error: {str(e)}")
        
        # Test Case 2: Create Debit Transaction
        try:
            transaction_data = {
                "account_id": self.test_account_id,
                "transaction_type": "debit",
                "mode": "cash",
                "amount": 1500.00,
                "category": "expense",
                "notes": "Test expense transaction"
            }
            
            response = self.session.post(f"{BASE_URL}/transactions", json=transaction_data)
            if response.status_code == 200:
                transaction = response.json()
                self.log_result("Transactions API - Debit Transaction", "PASS", 
                              f"Debit transaction created: {transaction.get('id')}, Amount: {transaction.get('amount')} OMR")
                
                # Verify account balance updated
                time.sleep(1)  # Brief delay for database update
                response = self.session.get(f"{BASE_URL}/accounts/{self.test_account_id}")
                if response.status_code == 200:
                    account = response.json()
                    new_balance = account.get("current_balance", 0)
                    expected_balance = initial_balance - 1500.00
                    
                    if abs(new_balance - expected_balance) < 0.01:
                        self.log_result("Transactions API - Debit Balance Update", "PASS", 
                                      f"Account balance correctly updated: {new_balance} OMR (expected: {expected_balance})")
                    else:
                        self.log_result("Transactions API - Debit Balance Update", "FAIL", 
                                      f"Balance update incorrect: {new_balance}, expected: {expected_balance}")
            else:
                self.log_result("Transactions API - Debit Transaction", "FAIL", 
                              f"Failed to create debit transaction: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Transactions API - Debit Transaction", "ERROR", f"Error: {str(e)}")
    
    def test_transactions_api_error_handling(self):
        """Test error handling for transactions API"""
        print("\n" + "="*80)
        print("TRANSACTIONS API - Error Handling Tests")
        print("="*80)
        
        # Test Case 3: Transaction With Invalid Account
        try:
            transaction_data = {
                "account_id": "fake-account-123",
                "transaction_type": "credit",
                "mode": "cash",
                "amount": 1000.00,
                "category": "sales",
                "notes": "Test transaction with invalid account"
            }
            
            response = self.session.post(f"{BASE_URL}/transactions", json=transaction_data)
            if response.status_code == 404 and "Account not found" in response.text:
                self.log_result("Transactions API - Invalid Account Error", "PASS", 
                              f"Correctly returned 404 for invalid account: {response.text}")
            else:
                self.log_result("Transactions API - Invalid Account Error", "FAIL", 
                              f"Unexpected response for invalid account: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Transactions API - Invalid Account Error", "ERROR", f"Error: {str(e)}")
        
        # Test Case 4: Get Transactions List
        try:
            response = self.session.get(f"{BASE_URL}/transactions?account_id={self.test_account_id}&page=1&per_page=10")
            if response.status_code == 200:
                data = response.json()
                transactions = data.get("items", [])
                self.log_result("Transactions API - Get Transactions List", "PASS", 
                              f"Retrieved {len(transactions)} transactions for account")
            else:
                self.log_result("Transactions API - Get Transactions List", "FAIL", 
                              f"Failed to get transactions: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Transactions API - Get Transactions List", "ERROR", f"Error: {str(e)}")
    
    def verification_phase(self):
        """Verify created data and numeric precision"""
        print("\n" + "="*80)
        print("VERIFICATION PHASE - Data Integrity and Precision")
        print("="*80)
        
        # Verify purchases created
        try:
            response = self.session.get(f"{BASE_URL}/purchases?vendor_party_id={self.test_vendor_id}&per_page=10")
            if response.status_code == 200:
                data = response.json()
                purchases = data.get("items", [])
                
                if len(purchases) >= 3:  # We created 3 purchases
                    self.log_result("Verification - Purchases Created", "PASS", 
                                  f"Found {len(purchases)} purchases for test vendor")
                    
                    # Check numeric precision
                    precision_ok = True
                    for purchase in purchases:
                        weight = purchase.get("weight_grams", 0)
                        amount = purchase.get("amount_total", 0)
                        
                        # Check weight precision (3 decimals)
                        if len(str(weight).split('.')[-1]) > 3:
                            precision_ok = False
                            break
                        
                        # Check amount precision (2 decimals)
                        if len(str(amount).split('.')[-1]) > 2:
                            precision_ok = False
                            break
                    
                    if precision_ok:
                        self.log_result("Verification - Numeric Precision", "PASS", 
                                      "All numeric fields have correct precision (weight: 3 decimals, amounts: 2 decimals)")
                    else:
                        self.log_result("Verification - Numeric Precision", "FAIL", 
                                      "Some numeric fields have incorrect precision")
                else:
                    self.log_result("Verification - Purchases Created", "FAIL", 
                                  f"Expected at least 3 purchases, found {len(purchases)}")
            else:
                self.log_result("Verification - Purchases Created", "FAIL", 
                              f"Failed to get purchases: {response.status_code}")
                
        except Exception as e:
            self.log_result("Verification - Purchases Created", "ERROR", f"Error: {str(e)}")
        
        # Verify account balance is correct
        try:
            response = self.session.get(f"{BASE_URL}/accounts/{self.test_account_id}")
            if response.status_code == 200:
                account = response.json()
                current_balance = account.get("current_balance", 0)
                opening_balance = account.get("opening_balance", 0)
                
                # Expected: opening (10000) + credit (5000) - debit (1500) = 13500
                expected_balance = opening_balance + 5000.00 - 1500.00
                
                if abs(current_balance - expected_balance) < 0.01:
                    self.log_result("Verification - Final Account Balance", "PASS", 
                                  f"Account balance correct: {current_balance} OMR (expected: {expected_balance})")
                else:
                    self.log_result("Verification - Final Account Balance", "FAIL", 
                                  f"Account balance incorrect: {current_balance}, expected: {expected_balance}")
            else:
                self.log_result("Verification - Final Account Balance", "FAIL", 
                              f"Failed to get account: {response.status_code}")
                
        except Exception as e:
            self.log_result("Verification - Final Account Balance", "ERROR", f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all critical API fix tests"""
        print("STARTING CRITICAL API FIXES TESTING - PURCHASES & TRANSACTIONS")
        print("Backend URL:", BASE_URL)
        print("Authentication:", f"{USERNAME}/***")
        print("="*80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Test data setup failed. Cannot proceed with tests.")
            return False
        
        # Run all test phases
        self.test_purchases_api_dictionary_payload()
        self.test_purchases_api_error_handling()
        self.test_transactions_api_with_proper_setup()
        self.test_transactions_api_error_handling()
        self.verification_phase()
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY - CRITICAL API FIXES")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        error_tests = len([r for r in self.test_results if r["status"] == "ERROR"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️ Errors: {error_tests}")
        
        # Critical success criteria
        print("\nCRITICAL SUCCESS CRITERIA:")
        
        purchases_api_tests = [r for r in self.test_results if "Purchases API - Dictionary Payload" in r["test"]]
        purchases_success = all(r["status"] == "PASS" for r in purchases_api_tests)
        
        transactions_api_tests = [r for r in self.test_results if "Transactions API -" in r["test"] and "Error" not in r["test"]]
        transactions_success = all(r["status"] == "PASS" for r in transactions_api_tests)
        
        error_handling_tests = [r for r in self.test_results if "Error" in r["test"]]
        error_handling_success = all(r["status"] == "PASS" for r in error_handling_tests)
        
        if purchases_success:
            print("✅ Purchases API accepts dictionary payload (not Purchase model object)")
        else:
            print("❌ Purchases API dictionary payload acceptance - FAILED")
        
        if transactions_success:
            print("✅ Transactions API works when valid account_id provided")
        else:
            print("❌ Transactions API functionality - FAILED")
        
        if error_handling_success:
            print("✅ Clear error messages for invalid data")
        else:
            print("❌ Error handling - FAILED")
        
        # Overall assessment
        critical_success = purchases_success and transactions_success and error_handling_success
        
        if critical_success:
            print("\n🎉 ALL CRITICAL FIXES VERIFIED SUCCESSFULLY!")
            print("✅ Purchases API dictionary fix is working")
            print("✅ Transactions API dependency validation is working")
            print("✅ Both APIs are production ready")
        else:
            print("\n🚨 CRITICAL ISSUES DETECTED!")
            print("❌ Some API fixes are not working as expected")
            print("❌ Manual investigation required")
        
        # Detailed results
        print("\nDETAILED RESULTS:")
        for result in self.test_results:
            status_symbol = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"{status_symbol} {result['test']}: {result['details']}")
        
        return critical_success

if __name__ == "__main__":
    tester = CriticalAPIFixesTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
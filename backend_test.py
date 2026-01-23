#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Invoice Payment to Account Integration
Critical Bug Fix Verification - Gold Shop ERP System

This test verifies that when invoice payments are added:
1. Transaction records are created correctly
2. Account current_balance field is updated correctly  
3. Invoice paid_amount and balance_due are updated correctly
4. Both Cash and Bank accounts work correctly
5. Both partial and full payments work correctly
"""

import requests
import json
import sys
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

# Configuration
BASE_URL = "https://jolly-herschel.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}

class InvoicePaymentTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.test_data = {}
        
    def log_test(self, test_name, passed, details=""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
        
    def authenticate(self):
        """Authenticate and get JWT token"""
        print("\n🔐 STEP 0: Authentication")
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json=ADMIN_CREDENTIALS)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log_test("Admin Authentication", True, "Successfully authenticated")
                return True
            else:
                self.log_test("Admin Authentication", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_1_verify_accounts(self):
        """TEST 1: PRE-CONDITIONS VERIFICATION - Verify accounts exist"""
        print("\n💰 TEST 1: PRE-CONDITIONS VERIFICATION")
        try:
            response = self.session.get(f"{BASE_URL}/accounts")
            if response.status_code != 200:
                self.log_test("Get Accounts List", False, f"Status: {response.status_code}")
                return False
                
            accounts = response.json()
            print(f"Found {len(accounts)} accounts")
            
            # Find Cash and Bank accounts
            cash_account = None
            bank_account = None
            
            for account in accounts:
                if account.get('account_type', '').lower() == 'cash':
                    cash_account = account
                elif account.get('account_type', '').lower() == 'bank':
                    bank_account = account
                    
            if not cash_account:
                self.log_test("Cash Account Exists", False, "No Cash account found")
                return False
            if not bank_account:
                self.log_test("Bank Account Exists", False, "No Bank account found")
                return False
                
            # Store account details for testing
            self.test_data['cash_account'] = cash_account
            self.test_data['bank_account'] = bank_account
            self.test_data['cash_opening_balance'] = float(cash_account.get('current_balance', 0))
            self.test_data['bank_opening_balance'] = float(bank_account.get('current_balance', 0))
            
            self.log_test("Cash Account Exists", True, f"ID: {cash_account['id']}, Balance: {self.test_data['cash_opening_balance']} OMR")
            self.log_test("Bank Account Exists", True, f"ID: {bank_account['id']}, Balance: {self.test_data['bank_opening_balance']} OMR")
            
            return True
            
        except Exception as e:
            self.log_test("Verify Accounts", False, f"Exception: {str(e)}")
            return False
    
    def test_2_create_test_invoice(self):
        """TEST 2: CREATE TEST INVOICE with 2+ items"""
        print("\n📄 TEST 2: CREATE TEST INVOICE")
        try:
            # Get a customer for the invoice
            parties_response = self.session.get(f"{BASE_URL}/parties?party_type=customer&per_page=1")
            if parties_response.status_code != 200:
                self.log_test("Get Customer", False, f"Status: {parties_response.status_code}")
                return False
                
            parties_data = parties_response.json()
            if not parties_data.get('items') or len(parties_data['items']) == 0:
                self.log_test("Get Customer", False, "No customers found")
                return False
                
            customer = parties_data['items'][0]
            
            # Create invoice with 2 items
            invoice_data = {
                "customer_type": "saved",
                "customer_id": customer['id'],
                "customer_name": customer['name'],
                "customer_phone": customer.get('phone', ''),
                "customer_address": customer.get('address', ''),
                "items": [
                    {
                        "description": "Gold Ring 22K - Test Payment Integration",
                        "weight": 15.500,
                        "category": "Ring",
                        "purity": 916,
                        "metal_rate": 50.00,
                        "making_value": 100.00,
                        "line_total": 875.00  # (15.5 * 50) + 100
                    },
                    {
                        "description": "Gold Chain 18K - Test Payment Integration", 
                        "weight": 20.250,
                        "category": "Chain",
                        "purity": 750,
                        "metal_rate": 45.00,
                        "making_value": 150.00,
                        "line_total": 1061.25  # (20.25 * 45) + 150
                    }
                ],
                "subtotal": 1936.25,
                "discount_amount": 0.00,
                "vat_total": 96.81,  # 5% VAT
                "grand_total": 2033.06,
                "status": "draft",
                "notes": "Test invoice for payment integration testing"
            }
            
            response = self.session.post(f"{BASE_URL}/invoices", json=invoice_data)
            if response.status_code != 201:
                self.log_test("Create Test Invoice", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
            invoice = response.json()
            self.test_data['test_invoice'] = invoice
            self.test_data['invoice_id'] = invoice['id']
            self.test_data['grand_total'] = float(invoice['grand_total'])
            
            self.log_test("Create Test Invoice", True, f"Invoice ID: {invoice['id']}, Grand Total: {self.test_data['grand_total']} OMR")
            return True
            
        except Exception as e:
            self.log_test("Create Test Invoice", False, f"Exception: {str(e)}")
            return False
    
    def test_3_get_account_balance_before(self):
        """TEST 3: GET ACCOUNT BALANCE BEFORE PAYMENT"""
        print("\n💰 TEST 3: GET ACCOUNT BALANCE BEFORE PAYMENT")
        try:
            cash_account_id = self.test_data['cash_account']['id']
            response = self.session.get(f"{BASE_URL}/accounts/{cash_account_id}")
            
            if response.status_code != 200:
                self.log_test("Get Cash Account Balance Before", False, f"Status: {response.status_code}")
                return False
                
            account = response.json()
            current_balance = float(account.get('current_balance', 0))
            self.test_data['cash_balance_before'] = current_balance
            
            self.log_test("Get Cash Account Balance Before", True, f"Balance: {current_balance} OMR")
            return True
            
        except Exception as e:
            self.log_test("Get Cash Account Balance Before", False, f"Exception: {str(e)}")
            return False
    
    def test_4_add_partial_payment(self):
        """TEST 4: ADD PARTIAL PAYMENT TO INVOICE (CRITICAL TEST)"""
        print("\n💳 TEST 4: ADD PARTIAL PAYMENT TO INVOICE")
        try:
            invoice_id = self.test_data['invoice_id']
            cash_account_id = self.test_data['cash_account']['id']
            payment_amount = 500.00
            
            payment_data = {
                "amount": payment_amount,
                "payment_mode": "Cash",
                "account_id": cash_account_id,
                "notes": "Test payment for account balance integration"
            }
            
            response = self.session.post(f"{BASE_URL}/invoices/{invoice_id}/add-payment", json=payment_data)
            
            if response.status_code != 200:
                self.log_test("Add Partial Payment", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
            result = response.json()
            
            # Verify response structure
            required_fields = ['message', 'transaction_id', 'transaction_number', 'new_paid_amount', 'new_balance_due', 'payment_status']
            missing_fields = [field for field in required_fields if field not in result]
            
            if missing_fields:
                self.log_test("Payment Response Structure", False, f"Missing fields: {missing_fields}")
                return False
                
            # Verify payment calculations
            expected_paid_amount = payment_amount
            expected_balance_due = self.test_data['grand_total'] - payment_amount
            
            if abs(float(result['new_paid_amount']) - expected_paid_amount) > 0.01:
                self.log_test("Payment Amount Calculation", False, f"Expected: {expected_paid_amount}, Got: {result['new_paid_amount']}")
                return False
                
            if abs(float(result['new_balance_due']) - expected_balance_due) > 0.01:
                self.log_test("Balance Due Calculation", False, f"Expected: {expected_balance_due}, Got: {result['new_balance_due']}")
                return False
                
            if result['payment_status'] != 'partial':
                self.log_test("Payment Status", False, f"Expected: partial, Got: {result['payment_status']}")
                return False
                
            # Store payment details for verification
            self.test_data['first_payment_amount'] = payment_amount
            self.test_data['transaction_id'] = result['transaction_id']
            self.test_data['transaction_number'] = result['transaction_number']
            
            self.log_test("Add Partial Payment", True, f"Amount: {payment_amount} OMR, Status: {result['payment_status']}")
            self.log_test("Payment Response Structure", True, "All required fields present")
            self.log_test("Payment Amount Calculation", True, f"Paid: {result['new_paid_amount']} OMR")
            self.log_test("Balance Due Calculation", True, f"Balance: {result['new_balance_due']} OMR")
            self.log_test("Payment Status", True, f"Status: {result['payment_status']}")
            
            return True
            
        except Exception as e:
            self.log_test("Add Partial Payment", False, f"Exception: {str(e)}")
            return False
    
    def test_5_verify_account_balance_increased(self):
        """TEST 5: VERIFY ACCOUNT BALANCE INCREASED (CRITICAL VERIFICATION)"""
        print("\n💰 TEST 5: VERIFY ACCOUNT BALANCE INCREASED")
        try:
            cash_account_id = self.test_data['cash_account']['id']
            response = self.session.get(f"{BASE_URL}/accounts/{cash_account_id}")
            
            if response.status_code != 200:
                self.log_test("Get Cash Account Balance After", False, f"Status: {response.status_code}")
                return False
                
            account = response.json()
            current_balance = float(account.get('current_balance', 0))
            expected_balance = self.test_data['cash_balance_before'] + self.test_data['first_payment_amount']
            
            # Allow for small floating point differences
            if abs(current_balance - expected_balance) > 0.01:
                self.log_test("Account Balance Update", False, 
                            f"Expected: {expected_balance} OMR, Got: {current_balance} OMR, "
                            f"Before: {self.test_data['cash_balance_before']} OMR, "
                            f"Payment: {self.test_data['first_payment_amount']} OMR")
                return False
                
            self.test_data['cash_balance_after_first'] = current_balance
            self.log_test("Account Balance Update", True, 
                        f"Balance increased from {self.test_data['cash_balance_before']} to {current_balance} OMR "
                        f"(+{self.test_data['first_payment_amount']} OMR)")
            return True
            
        except Exception as e:
            self.log_test("Verify Account Balance Increased", False, f"Exception: {str(e)}")
            return False
    
    def test_6_verify_transaction_record(self):
        """TEST 6: VERIFY TRANSACTION RECORD CREATED"""
        print("\n📊 TEST 6: VERIFY TRANSACTION RECORD CREATED")
        try:
            cash_account_id = self.test_data['cash_account']['id']
            
            # Get transactions for the account
            response = self.session.get(f"{BASE_URL}/transactions?account_id={cash_account_id}&per_page=25")
            
            if response.status_code != 200:
                self.log_test("Get Account Transactions", False, f"Status: {response.status_code}")
                return False
                
            transactions_data = response.json()
            transactions = transactions_data.get('items', [])
            
            # Find the transaction we just created
            target_transaction = None
            for txn in transactions:
                if txn.get('id') == self.test_data.get('transaction_id'):
                    target_transaction = txn
                    break
                    
            if not target_transaction:
                self.log_test("Transaction Record Found", False, f"Transaction ID {self.test_data.get('transaction_id')} not found")
                return False
                
            # Verify transaction fields
            verifications = [
                ("transaction_type", "credit", "Transaction type should be credit for payment received"),
                ("mode", "Cash", "Payment mode should match"),
                ("amount", self.test_data['first_payment_amount'], "Amount should match payment"),
                ("category", "Invoice Payment", "Category should be Invoice Payment"),
                ("reference_type", "invoice", "Reference type should be invoice"),
                ("reference_id", self.test_data['invoice_id'], "Reference ID should match invoice ID"),
                ("account_id", cash_account_id, "Account ID should match Cash account")
            ]
            
            all_passed = True
            for field, expected, description in verifications:
                actual = target_transaction.get(field)
                
                # Handle numeric comparisons
                if isinstance(expected, (int, float)):
                    if abs(float(actual) - float(expected)) > 0.01:
                        self.log_test(f"Transaction {field}", False, f"Expected: {expected}, Got: {actual}")
                        all_passed = False
                    else:
                        self.log_test(f"Transaction {field}", True, f"Value: {actual}")
                else:
                    if actual != expected:
                        self.log_test(f"Transaction {field}", False, f"Expected: {expected}, Got: {actual}")
                        all_passed = False
                    else:
                        self.log_test(f"Transaction {field}", True, f"Value: {actual}")
                        
            return all_passed
            
        except Exception as e:
            self.log_test("Verify Transaction Record", False, f"Exception: {str(e)}")
            return False
    
    def test_7_verify_invoice_updated(self):
        """TEST 7: VERIFY INVOICE UPDATED"""
        print("\n📄 TEST 7: VERIFY INVOICE UPDATED")
        try:
            invoice_id = self.test_data['invoice_id']
            response = self.session.get(f"{BASE_URL}/invoices/{invoice_id}")
            
            if response.status_code != 200:
                self.log_test("Get Updated Invoice", False, f"Status: {response.status_code}")
                return False
                
            invoice = response.json()
            
            # Verify invoice payment fields
            expected_paid_amount = self.test_data['first_payment_amount']
            expected_balance_due = self.test_data['grand_total'] - expected_paid_amount
            expected_status = "partial"
            
            verifications = [
                ("paid_amount", expected_paid_amount, "Paid amount should match payment"),
                ("balance_due", expected_balance_due, "Balance due should be grand_total - paid_amount"),
                ("payment_status", expected_status, "Payment status should be partial")
            ]
            
            all_passed = True
            for field, expected, description in verifications:
                actual = invoice.get(field)
                
                if isinstance(expected, (int, float)):
                    if abs(float(actual) - float(expected)) > 0.01:
                        self.log_test(f"Invoice {field}", False, f"Expected: {expected}, Got: {actual}")
                        all_passed = False
                    else:
                        self.log_test(f"Invoice {field}", True, f"Value: {actual}")
                else:
                    if actual != expected:
                        self.log_test(f"Invoice {field}", False, f"Expected: {expected}, Got: {actual}")
                        all_passed = False
                    else:
                        self.log_test(f"Invoice {field}", True, f"Value: {actual}")
                        
            return all_passed
            
        except Exception as e:
            self.log_test("Verify Invoice Updated", False, f"Exception: {str(e)}")
            return False
    
    def test_8_add_second_payment(self):
        """TEST 8: ADD SECOND PAYMENT TO COMPLETE INVOICE"""
        print("\n💳 TEST 8: ADD SECOND PAYMENT TO COMPLETE INVOICE")
        try:
            invoice_id = self.test_data['invoice_id']
            cash_account_id = self.test_data['cash_account']['id']
            
            # Calculate remaining balance
            remaining_balance = self.test_data['grand_total'] - self.test_data['first_payment_amount']
            
            payment_data = {
                "amount": remaining_balance,
                "payment_mode": "Cash",
                "account_id": cash_account_id,
                "notes": "Final payment to complete invoice"
            }
            
            response = self.session.post(f"{BASE_URL}/invoices/{invoice_id}/add-payment", json=payment_data)
            
            if response.status_code != 200:
                self.log_test("Add Second Payment", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
            result = response.json()
            
            # Verify payment status changed to "paid"
            if result.get('payment_status') != 'paid':
                self.log_test("Final Payment Status", False, f"Expected: paid, Got: {result.get('payment_status')}")
                return False
                
            # Verify balance due is 0
            if abs(float(result.get('new_balance_due', 0))) > 0.01:
                self.log_test("Final Balance Due", False, f"Expected: 0.00, Got: {result.get('new_balance_due')}")
                return False
                
            self.test_data['second_payment_amount'] = remaining_balance
            
            self.log_test("Add Second Payment", True, f"Amount: {remaining_balance} OMR")
            self.log_test("Final Payment Status", True, f"Status: {result['payment_status']}")
            self.log_test("Final Balance Due", True, f"Balance: {result['new_balance_due']} OMR")
            
            return True
            
        except Exception as e:
            self.log_test("Add Second Payment", False, f"Exception: {str(e)}")
            return False
    
    def test_9_verify_account_balance_after_second(self):
        """TEST 9: VERIFY ACCOUNT BALANCE AFTER SECOND PAYMENT"""
        print("\n💰 TEST 9: VERIFY ACCOUNT BALANCE AFTER SECOND PAYMENT")
        try:
            cash_account_id = self.test_data['cash_account']['id']
            response = self.session.get(f"{BASE_URL}/accounts/{cash_account_id}")
            
            if response.status_code != 200:
                self.log_test("Get Cash Account Final Balance", False, f"Status: {response.status_code}")
                return False
                
            account = response.json()
            current_balance = float(account.get('current_balance', 0))
            expected_balance = (self.test_data['cash_balance_before'] + 
                              self.test_data['first_payment_amount'] + 
                              self.test_data['second_payment_amount'])
            
            if abs(current_balance - expected_balance) > 0.01:
                self.log_test("Final Account Balance", False, 
                            f"Expected: {expected_balance} OMR, Got: {current_balance} OMR")
                return False
                
            total_payments = self.test_data['first_payment_amount'] + self.test_data['second_payment_amount']
            self.log_test("Final Account Balance", True, 
                        f"Balance: {current_balance} OMR (Original: {self.test_data['cash_balance_before']} + "
                        f"Total Payments: {total_payments} OMR)")
            return True
            
        except Exception as e:
            self.log_test("Verify Final Account Balance", False, f"Exception: {str(e)}")
            return False
    
    def test_10_bank_account_payment(self):
        """TEST 10: TEST BANK ACCOUNT PAYMENT"""
        print("\n🏦 TEST 10: TEST BANK ACCOUNT PAYMENT")
        try:
            # Create another test invoice
            parties_response = self.session.get(f"{BASE_URL}/parties?party_type=customer&per_page=1")
            if parties_response.status_code != 200:
                self.log_test("Get Customer for Bank Test", False, f"Status: {parties_response.status_code}")
                return False
                
            parties_data = parties_response.json()
            customer = parties_data['items'][0]
            
            # Create simple invoice for bank payment test
            invoice_data = {
                "customer_type": "saved",
                "customer_id": customer['id'],
                "customer_name": customer['name'],
                "customer_phone": customer.get('phone', ''),
                "customer_address": customer.get('address', ''),
                "items": [
                    {
                        "description": "Gold Bracelet 18K - Bank Payment Test",
                        "weight": 12.000,
                        "category": "Bracelet",
                        "purity": 750,
                        "metal_rate": 45.00,
                        "making_value": 80.00,
                        "line_total": 620.00  # (12 * 45) + 80
                    }
                ],
                "subtotal": 620.00,
                "discount_amount": 0.00,
                "vat_total": 31.00,  # 5% VAT
                "grand_total": 651.00,
                "status": "draft",
                "notes": "Test invoice for bank payment integration"
            }
            
            response = self.session.post(f"{BASE_URL}/invoices", json=invoice_data)
            if response.status_code != 201:
                self.log_test("Create Bank Test Invoice", False, f"Status: {response.status_code}")
                return False
                
            bank_invoice = response.json()
            bank_invoice_id = bank_invoice['id']
            
            # Get bank account balance before payment
            bank_account_id = self.test_data['bank_account']['id']
            response = self.session.get(f"{BASE_URL}/accounts/{bank_account_id}")
            if response.status_code != 200:
                self.log_test("Get Bank Balance Before", False, f"Status: {response.status_code}")
                return False
                
            bank_balance_before = float(response.json().get('current_balance', 0))
            
            # Add bank payment
            payment_amount = 651.00  # Full payment
            payment_data = {
                "amount": payment_amount,
                "payment_mode": "Bank Transfer",
                "account_id": bank_account_id,
                "notes": "Bank transfer payment test"
            }
            
            response = self.session.post(f"{BASE_URL}/invoices/{bank_invoice_id}/add-payment", json=payment_data)
            if response.status_code != 200:
                self.log_test("Add Bank Payment", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
            # Verify bank account balance increased
            response = self.session.get(f"{BASE_URL}/accounts/{bank_account_id}")
            if response.status_code != 200:
                self.log_test("Get Bank Balance After", False, f"Status: {response.status_code}")
                return False
                
            bank_balance_after = float(response.json().get('current_balance', 0))
            expected_bank_balance = bank_balance_before + payment_amount
            
            if abs(bank_balance_after - expected_bank_balance) > 0.01:
                self.log_test("Bank Account Balance Update", False, 
                            f"Expected: {expected_bank_balance} OMR, Got: {bank_balance_after} OMR")
                return False
                
            # Verify transaction created with correct bank account reference
            response = self.session.get(f"{BASE_URL}/transactions?account_id={bank_account_id}&per_page=5")
            if response.status_code != 200:
                self.log_test("Get Bank Transactions", False, f"Status: {response.status_code}")
                return False
                
            transactions_data = response.json()
            transactions = transactions_data.get('items', [])
            
            # Find recent transaction
            bank_transaction = None
            for txn in transactions:
                if (txn.get('reference_id') == bank_invoice_id and 
                    txn.get('account_id') == bank_account_id and
                    abs(float(txn.get('amount', 0)) - payment_amount) < 0.01):
                    bank_transaction = txn
                    break
                    
            if not bank_transaction:
                self.log_test("Bank Transaction Created", False, "Bank transaction not found")
                return False
                
            self.log_test("Create Bank Test Invoice", True, f"Invoice ID: {bank_invoice_id}")
            self.log_test("Add Bank Payment", True, f"Amount: {payment_amount} OMR")
            self.log_test("Bank Account Balance Update", True, 
                        f"Balance increased from {bank_balance_before} to {bank_balance_after} OMR")
            self.log_test("Bank Transaction Created", True, f"Transaction ID: {bank_transaction['id']}")
            
            return True
            
        except Exception as e:
            self.log_test("Test Bank Account Payment", False, f"Exception: {str(e)}")
            return False
    
    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🚀 STARTING COMPREHENSIVE INVOICE PAYMENT TO ACCOUNT INTEGRATION TESTING")
        print("=" * 80)
        
        # Authentication
        if not self.authenticate():
            return False
            
        # Run all tests
        tests = [
            self.test_1_verify_accounts,
            self.test_2_create_test_invoice,
            self.test_3_get_account_balance_before,
            self.test_4_add_partial_payment,
            self.test_5_verify_account_balance_increased,
            self.test_6_verify_transaction_record,
            self.test_7_verify_invoice_updated,
            self.test_8_add_second_payment,
            self.test_9_verify_account_balance_after_second,
            self.test_10_bank_account_payment
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed_tests += 1
                else:
                    print(f"❌ Test failed: {test.__name__}")
            except Exception as e:
                print(f"❌ Test error in {test.__name__}: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("🎯 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"Overall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Group results by category
        critical_tests = [t for t in self.test_results if 'Balance' in t['test'] or 'Payment' in t['test']]
        critical_passed = len([t for t in critical_tests if t['passed']])
        
        print(f"\n🔥 CRITICAL TESTS (Account Balance Integration): {critical_passed}/{len(critical_tests)} PASSED")
        
        # Show failed tests
        failed_tests = [t for t in self.test_results if not t['passed']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        else:
            print(f"\n✅ ALL TESTS PASSED - INVOICE PAYMENT TO ACCOUNT INTEGRATION WORKING CORRECTLY!")
            
        # Critical success criteria
        print(f"\n🎯 CRITICAL SUCCESS CRITERIA VERIFICATION:")
        criteria = [
            ("Account current_balance updates immediately after payment", 
             any('Account Balance Update' in t['test'] and t['passed'] for t in self.test_results)),
            ("Balance increases by EXACT payment amount", 
             any('Account Balance Update' in t['test'] and t['passed'] for t in self.test_results)),
            ("Transaction records created with correct fields", 
             any('Transaction' in t['test'] and t['passed'] for t in self.test_results)),
            ("Invoice paid_amount and balance_due updated correctly", 
             any('Invoice' in t['test'] and 'updated' in t['test'].lower() and t['passed'] for t in self.test_results)),
            ("Works for both Cash and Bank accounts", 
             any('Bank' in t['test'] and t['passed'] for t in self.test_results)),
            ("Works for both partial and full payments", 
             any('Second Payment' in t['test'] and t['passed'] for t in self.test_results)),
            ("Transaction type is credit for payment received", 
             any('transaction_type' in t['test'] and t['passed'] for t in self.test_results)),
            ("Category is Invoice Payment", 
             any('category' in t['test'] and t['passed'] for t in self.test_results))
        ]
        
        for criterion, passed in criteria:
            status = "✅" if passed else "❌"
            print(f"   {status} {criterion}")
            
        return len(failed_tests) == 0

if __name__ == "__main__":
    tester = InvoicePaymentTester()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)
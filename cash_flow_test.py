#!/usr/bin/env python3
"""
Cash Flow Dashboard Calculation Testing
Testing the critical fixes for transaction directions and net flow formula

CRITICAL REQUIREMENTS TO TEST:
1. Transaction Directions:
   - Invoice payment → DEBIT (money IN to cash/bank)
   - Purchase payment → CREDIT (money OUT from cash/bank)
   - Sales return refund → CREDIT (money OUT to customer)
   - Purchase return refund → DEBIT (money IN from vendor)

2. Net Flow Formula:
   - Net Flow = Total Debit - Total Credit (for asset accounts like cash/bank)

3. Cash/Bank Summary Calculations:
   - cash_summary.net = cash_debit - cash_credit
   - bank_summary.net = bank_debit - bank_credit

TEST SCENARIOS:
✅ PHASE 1: ACCOUNT SETUP
✅ PHASE 2: INVOICE PAYMENT TESTING (DEBIT)
✅ PHASE 3: PURCHASE PAYMENT TESTING (CREDIT)
✅ PHASE 4: NET FLOW FORMULA VERIFICATION
✅ PHASE 5: TRANSACTION DIRECTIONS VERIFICATION
"""

import requests
import json
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal

# Configuration - Use environment variable for backend URL
import os
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ledger-correction.preview.emergentagent.com') + '/api'
HEADERS = {"Content-Type": "application/json"}

class CashFlowTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.auth_token = None
        self.csrf_token = None
        self.test_data = {}
        self.test_results = []
        
    def log_result(self, test_name, success, details="", error=""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    Details: {details}")
        if error:
            print(f"    Error: {error}")
        print()

    def authenticate(self):
        """Authenticate with admin user"""
        try:
            # Login with admin credentials
            login_data = {
                "username": "admin",
                "password": "Admin123!@#$%"
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.csrf_token = data.get("csrf_token")
                
                # Update session headers
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}",
                    "X-CSRF-Token": self.csrf_token
                })
                
                self.log_result("Authentication", True, "Successfully authenticated as admin")
                return True
            else:
                self.log_result("Authentication", False, "", f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, "", f"Authentication error: {str(e)}")
            return False

    def test_phase1_account_setup(self):
        """PHASE 1: Create Cash Account"""
        print("=" * 80)
        print("PHASE 1: ACCOUNT SETUP")
        print("=" * 80)
        
        try:
            # Create cash account with opening balance 0
            account_data = {
                "name": "Main Cash",
                "account_type": "cash",
                "opening_balance": 0
            }
            
            response = self.session.post(f"{BASE_URL}/accounts", json=account_data)
            if response.status_code == 201:
                self.test_data["cash_account"] = response.json()
                self.log_result("Create Cash Account", True, 
                              f"Created cash account: {self.test_data['cash_account']['name']} "
                              f"(ID: {self.test_data['cash_account']['id'][:8]}...)")
                return True
            else:
                self.log_result("Create Cash Account", False, "", 
                              f"Failed to create cash account: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Create Cash Account", False, "", f"Error: {str(e)}")
            return False

    def setup_test_entities(self):
        """Setup required entities for testing"""
        try:
            # Create customer party
            customer_data = {
                "name": "Test Customer",
                "phone": "+968-9876-5432",
                "address": "123 Test Street, Muscat",
                "party_type": "customer",
                "notes": "Test customer for cash flow testing"
            }
            response = self.session.post(f"{BASE_URL}/parties", json=customer_data)
            if response.status_code == 201:
                self.test_data["customer"] = response.json()
                self.log_result("Setup Customer", True, f"Created customer: {self.test_data['customer']['name']}")
            else:
                self.log_result("Setup Customer", False, "", f"Failed to create customer: {response.text}")
                return False

            # Create vendor party
            vendor_data = {
                "name": "Test Vendor",
                "phone": "+968-1234-5678",
                "address": "456 Vendor Street, Muscat",
                "party_type": "vendor",
                "notes": "Test vendor for cash flow testing"
            }
            response = self.session.post(f"{BASE_URL}/parties", json=vendor_data)
            if response.status_code == 201:
                self.test_data["vendor"] = response.json()
                self.log_result("Setup Vendor", True, f"Created vendor: {self.test_data['vendor']['name']}")
            else:
                self.log_result("Setup Vendor", False, "", f"Failed to create vendor: {response.text}")
                return False

            # Create inventory category
            category_data = {
                "name": "Gold Chains Test",
                "current_qty": 100.0,
                "current_weight": 1000.0
            }
            response = self.session.post(f"{BASE_URL}/inventory/headers", json=category_data)
            if response.status_code == 201:
                self.test_data["category"] = response.json()
                self.log_result("Setup Inventory", True, f"Created category: {self.test_data['category']['name']}")
            else:
                self.log_result("Setup Inventory", False, "", f"Failed to create category: {response.text}")
                return False

            return True
            
        except Exception as e:
            self.log_result("Setup Test Entities", False, "", f"Error: {str(e)}")
            return False

    def test_phase2_invoice_payment(self):
        """PHASE 2: Create Invoice Payment (Money IN) - Should be DEBIT"""
        print("=" * 80)
        print("PHASE 2: INVOICE PAYMENT TESTING (MONEY IN = DEBIT)")
        print("=" * 80)
        
        try:
            # Create invoice
            invoice_data = {
                "customer_type": "saved",
                "customer_id": self.test_data["customer"]["id"],
                "invoice_type": "sale",
                "items": [
                    {
                        "category": "Gold Chains Test",
                        "description": "22K Gold Chain - 50g",
                        "qty": 1,
                        "gross_weight": 50.0,
                        "stone_weight": 0.0,
                        "net_gold_weight": 50.0,
                        "weight": 50.0,
                        "purity": 916,
                        "metal_rate": 200.0,
                        "gold_value": 10000.0,
                        "making_charge_type": "per_gram",
                        "making_value": 1000.0,
                        "stone_charges": 0.0,
                        "wastage_charges": 500.0,
                        "item_discount": 0.0,
                        "vat_percent": 5.0,
                        "vat_amount": 575.0,
                        "line_total": 12075.0
                    }
                ],
                "subtotal": 11500.0,
                "discount_amount": 0.0,
                "tax_type": "cgst_sgst",
                "gst_percent": 5.0,
                "cgst_total": 287.5,
                "sgst_total": 287.5,
                "igst_total": 0.0,
                "vat_total": 575.0,
                "grand_total": 12075.0,
                "paid_amount": 0.0,
                "balance_due": 12075.0
            }
            
            response = self.session.post(f"{BASE_URL}/invoices", json=invoice_data)
            if response.status_code == 201:
                invoice = response.json()
                
                # Finalize the invoice
                finalize_response = self.session.post(f"{BASE_URL}/invoices/{invoice['id']}/finalize")
                if finalize_response.status_code == 200:
                    self.test_data["invoice"] = finalize_response.json()
                    self.log_result("Create Invoice", True, 
                                  f"Created and finalized invoice: {self.test_data['invoice']['invoice_number']} "
                                  f"(Total: {self.test_data['invoice']['grand_total']} OMR)")
                    
                    # Add payment to invoice (Money IN = DEBIT)
                    payment_data = {
                        "amount": 5000.0,
                        "payment_mode": "Cash",
                        "account_id": self.test_data["cash_account"]["id"],
                        "notes": "Partial payment for invoice"
                    }
                    
                    payment_response = self.session.post(f"{BASE_URL}/invoices/{invoice['id']}/add-payment", json=payment_data)
                    if payment_response.status_code == 200:
                        updated_invoice = payment_response.json()
                        self.test_data["invoice_payment"] = payment_data
                        self.log_result("Add Invoice Payment", True, 
                                      f"Added payment of {payment_data['amount']} OMR to invoice "
                                      f"(Balance due: {updated_invoice.get('balance_due', 'N/A')} OMR)")
                        return True
                    else:
                        self.log_result("Add Invoice Payment", False, "", 
                                      f"Failed to add payment: {payment_response.status_code} - {payment_response.text}")
                        return False
                else:
                    self.log_result("Create Invoice", False, "", 
                                  f"Failed to finalize invoice: {finalize_response.status_code} - {finalize_response.text}")
                    return False
            else:
                self.log_result("Create Invoice", False, "", 
                              f"Failed to create invoice: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Invoice Payment Test", False, "", f"Error: {str(e)}")
            return False

    def test_phase3_purchase_payment(self):
        """PHASE 3: Create Purchase Payment (Money OUT) - Should be CREDIT"""
        print("=" * 80)
        print("PHASE 3: PURCHASE PAYMENT TESTING (MONEY OUT = CREDIT)")
        print("=" * 80)
        
        try:
            # Create purchase with payment
            purchase_data = {
                "vendor_party_id": self.test_data["vendor"]["id"],
                "description": "Gold Purchase - 100g at 916 purity",
                "weight_grams": 100.0,
                "entered_purity": 916,
                "valuation_purity_fixed": 916,
                "rate_per_gram": 180.0,
                "amount_total": 18000.0,
                "paid_amount_money": 3000.0,  # Partial payment
                "balance_due_money": 15000.0,
                "payment_mode": "Cash",
                "account_id": self.test_data["cash_account"]["id"]
            }
            
            response = self.session.post(f"{BASE_URL}/purchases", json=purchase_data)
            if response.status_code == 201:
                purchase = response.json()
                
                # Finalize the purchase
                finalize_response = self.session.post(f"{BASE_URL}/purchases/{purchase['id']}/finalize")
                if finalize_response.status_code == 200:
                    self.test_data["purchase"] = finalize_response.json()
                    self.log_result("Create Purchase with Payment", True, 
                                  f"Created and finalized purchase with payment of {purchase_data['paid_amount_money']} OMR "
                                  f"(Total: {self.test_data['purchase']['amount_total']} OMR, "
                                  f"Balance due: {self.test_data['purchase']['balance_due_money']} OMR)")
                    return True
                else:
                    self.log_result("Create Purchase with Payment", False, "", 
                                  f"Failed to finalize purchase: {finalize_response.status_code} - {finalize_response.text}")
                    return False
            else:
                self.log_result("Create Purchase with Payment", False, "", 
                              f"Failed to create purchase: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Purchase Payment Test", False, "", f"Error: {str(e)}")
            return False

    def test_phase4_net_flow_verification(self):
        """PHASE 4: Verify Net Flow Formula and Transaction Summary"""
        print("=" * 80)
        print("PHASE 4: NET FLOW FORMULA VERIFICATION")
        print("=" * 80)
        
        try:
            # Get transactions summary
            response = self.session.get(f"{BASE_URL}/transactions/summary")
            if response.status_code == 200:
                summary = response.json()
                
                # Extract key values
                total_debit = summary.get('total_debit', 0)
                total_credit = summary.get('total_credit', 0)
                net_flow = summary.get('net_flow', 0)
                
                # Calculate expected net flow: debit - credit (for asset accounts)
                expected_net_flow = total_debit - total_credit
                
                self.log_result("Get Transactions Summary", True, 
                              f"Retrieved summary - Total Debit: {total_debit} OMR, "
                              f"Total Credit: {total_credit} OMR, Net Flow: {net_flow} OMR")
                
                # Verify net flow formula
                if abs(net_flow - expected_net_flow) < 0.01:  # Allow for rounding
                    self.log_result("Net Flow Formula Verification", True, 
                                  f"Net Flow formula correct: {net_flow} = {total_debit} - {total_credit}")
                else:
                    self.log_result("Net Flow Formula Verification", False, "", 
                                  f"Net Flow formula incorrect: Expected {expected_net_flow}, Got {net_flow}")
                
                # Verify cash summary if available
                cash_summary = summary.get('cash_summary', {})
                if cash_summary:
                    cash_debit = cash_summary.get('debit', 0)
                    cash_credit = cash_summary.get('credit', 0)
                    cash_net = cash_summary.get('net', 0)
                    expected_cash_net = cash_debit - cash_credit
                    
                    if abs(cash_net - expected_cash_net) < 0.01:
                        self.log_result("Cash Summary Net Calculation", True, 
                                      f"Cash net correct: {cash_net} = {cash_debit} - {cash_credit}")
                    else:
                        self.log_result("Cash Summary Net Calculation", False, "", 
                                      f"Cash net incorrect: Expected {expected_cash_net}, Got {cash_net}")
                
                # Verify bank summary if available
                bank_summary = summary.get('bank_summary', {})
                if bank_summary:
                    bank_debit = bank_summary.get('debit', 0)
                    bank_credit = bank_summary.get('credit', 0)
                    bank_net = bank_summary.get('net', 0)
                    expected_bank_net = bank_debit - bank_credit
                    
                    if abs(bank_net - expected_bank_net) < 0.01:
                        self.log_result("Bank Summary Net Calculation", True, 
                                      f"Bank net correct: {bank_net} = {bank_debit} - {bank_credit}")
                    else:
                        self.log_result("Bank Summary Net Calculation", False, "", 
                                      f"Bank net incorrect: Expected {expected_bank_net}, Got {bank_net}")
                
                return True
            else:
                self.log_result("Get Transactions Summary", False, "", 
                              f"Failed to get summary: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Net Flow Verification", False, "", f"Error: {str(e)}")
            return False

    def test_phase5_transaction_directions(self):
        """PHASE 5: Verify Transaction Directions"""
        print("=" * 80)
        print("PHASE 5: TRANSACTION DIRECTIONS VERIFICATION")
        print("=" * 80)
        
        try:
            # Get all transactions
            response = self.session.get(f"{BASE_URL}/transactions")
            if response.status_code == 200:
                transactions = response.json()
                
                # Find our test transactions
                invoice_payment_transaction = None
                purchase_payment_transaction = None
                
                for transaction in transactions:
                    if transaction.get('account_id') == self.test_data["cash_account"]["id"]:
                        if transaction.get('reference_type') == 'invoice':
                            invoice_payment_transaction = transaction
                        elif transaction.get('reference_type') == 'purchase':
                            purchase_payment_transaction = transaction
                
                # Verify invoice payment transaction (Money IN = DEBIT)
                if invoice_payment_transaction:
                    if invoice_payment_transaction.get('transaction_type') == 'debit':
                        self.log_result("Invoice Payment Direction", True, 
                                      f"Invoice payment correctly recorded as DEBIT (money IN): "
                                      f"{invoice_payment_transaction.get('amount')} OMR")
                    else:
                        self.log_result("Invoice Payment Direction", False, "", 
                                      f"Invoice payment should be DEBIT but got: {invoice_payment_transaction.get('transaction_type')}")
                else:
                    self.log_result("Invoice Payment Direction", False, "", 
                                  "Invoice payment transaction not found")
                
                # Verify purchase payment transaction (Money OUT = CREDIT)
                if purchase_payment_transaction:
                    if purchase_payment_transaction.get('transaction_type') == 'credit':
                        self.log_result("Purchase Payment Direction", True, 
                                      f"Purchase payment correctly recorded as CREDIT (money OUT): "
                                      f"{purchase_payment_transaction.get('amount')} OMR")
                    else:
                        self.log_result("Purchase Payment Direction", False, "", 
                                      f"Purchase payment should be CREDIT but got: {purchase_payment_transaction.get('transaction_type')}")
                else:
                    self.log_result("Purchase Payment Direction", False, "", 
                                  "Purchase payment transaction not found")
                
                return True
            else:
                self.log_result("Get Transactions", False, "", 
                              f"Failed to get transactions: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Transaction Directions Verification", False, "", f"Error: {str(e)}")
            return False

    def run_comprehensive_test(self):
        """Run all test phases"""
        print("🚀 STARTING CASH FLOW DASHBOARD CALCULATION TESTING")
        print("=" * 80)
        
        # Authenticate
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with testing.")
            return False
        
        # Setup test entities
        if not self.setup_test_entities():
            print("❌ Test entities setup failed. Cannot proceed with testing.")
            return False
        
        # Phase 1: Account Setup
        if not self.test_phase1_account_setup():
            print("❌ Account setup failed. Cannot proceed with testing.")
            return False
        
        # Phase 2: Invoice Payment Testing
        if not self.test_phase2_invoice_payment():
            print("❌ Invoice payment test failed. Continuing with other tests.")
        
        # Phase 3: Purchase Payment Testing
        if not self.test_phase3_purchase_payment():
            print("❌ Purchase payment test failed. Continuing with other tests.")
        
        # Phase 4: Net Flow Verification
        self.test_phase4_net_flow_verification()
        
        # Phase 5: Transaction Directions Verification
        self.test_phase5_transaction_directions()
        
        # Print summary
        self.print_summary()
        
        return True

    def print_summary(self):
        """Print test results summary"""
        print("=" * 80)
        print("🎯 CASH FLOW DASHBOARD TESTING SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            print("-" * 40)
            for result in self.test_results:
                if not result["success"]:
                    print(f"• {result['test']}")
                    if result["error"]:
                        print(f"  Error: {result['error']}")
            print()
        
        print("✅ PASSED TESTS:")
        print("-" * 40)
        for result in self.test_results:
            if result["success"]:
                print(f"• {result['test']}")
        
        print("=" * 80)
        print("🏁 CASH FLOW TESTING COMPLETE")
        print("=" * 80)

if __name__ == "__main__":
    tester = CashFlowTester()
    tester.run_comprehensive_test()
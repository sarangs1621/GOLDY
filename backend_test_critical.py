import requests
import sys
import json
from datetime import datetime

class GoldShopERPTester:
    def __init__(self, base_url="https://decimal-precision.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None
        self.created_resources = {
            'headers': [],
            'parties': [],
            'accounts': [],
            'jobcards': [],
            'invoices': []
        }

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {method} {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_login(self):
        """Test login with admin credentials"""
        # First try to register admin user if it doesn't exist
        register_success, register_response = self.run_test(
            "Register Admin User",
            "POST",
            "auth/register",
            200,
            data={
                "username": "admin",
                "password": "admin123",
                "email": "admin@goldshop.com",
                "full_name": "System Administrator",
                "role": "admin"
            }
        )
        
        # Try to login (whether registration succeeded or failed due to existing user)
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            print(f"   Token obtained: {self.token[:20]}...")
            return True
        return False

    def test_critical_invoice_finalization_stock_deduction(self):
        """
        PRIORITY 1: INVOICE FINALIZATION & STOCK DEDUCTION (MOST CRITICAL)
        Test the core business logic that ensures financial integrity
        """
        print("\n🔥 CRITICAL PRIORITY TESTING - INVOICE FINALIZATION & STOCK DEDUCTION")
        
        # Step 1: Create test inventory category
        inventory_data = {
            "name": "Gold 22K Test"
        }
        
        success, inventory = self.run_test(
            "Create Test Inventory Category",
            "POST",
            "inventory/headers",
            200,
            data=inventory_data
        )
        
        if not success or not inventory.get('id'):
            return False
        
        inventory_id = inventory['id']
        print(f"✅ Created inventory: {inventory['name']}")
        
        # Add initial stock to inventory
        stock_data = {
            "movement_type": "Stock IN",
            "header_id": inventory_id,
            "description": "Initial stock for testing",
            "qty_delta": 5,
            "weight_delta": 500.0,
            "purity": 916,
            "notes": "Test stock"
        }
        
        success, stock_movement = self.run_test(
            "Add Initial Stock",
            "POST",
            "inventory/movements",
            200,
            data=stock_data
        )
        
        if not success:
            return False
        
        print(f"✅ Added initial stock: 5 qty, 500.0g")
        
        # Step 2: Create test customer
        customer_data = {
            "name": "Test Customer Invoice",
            "party_type": "customer",
            "phone": "99887766"
        }
        
        success, customer = self.run_test(
            "Create Test Customer",
            "POST",
            "parties",
            200,
            data=customer_data
        )
        
        if not success or not customer.get('id'):
            return False
        
        customer_id = customer['id']
        print(f"✅ Created customer: {customer['name']}")
        
        # Step 3: Create test job card
        jobcard_data = {
            "card_type": "individual",
            "customer_type": "saved",
            "customer_id": customer_id,
            "customer_name": customer['name'],
            "items": [{
                "category": "Gold 22K Test",
                "description": "Gold Chain",
                "qty": 1,
                "weight_in": 50.0,
                "weight_out": 50.0,
                "purity": 916,
                "work_type": "polish"
            }]
        }
        
        success, jobcard = self.run_test(
            "Create Test Job Card",
            "POST",
            "jobcards",
            200,
            data=jobcard_data
        )
        
        if not success or not jobcard.get('id'):
            return False
        
        jobcard_id = jobcard['id']
        print(f"✅ Created job card: {jobcard['job_card_number']}")
        
        # Step 4: Convert job card to DRAFT invoice
        invoice_conversion_data = {
            "customer_type": "saved",
            "metal_rate": 20.0,
            "vat_percent": 5
        }
        
        success, invoice = self.run_test(
            "Convert Job Card to DRAFT Invoice",
            "POST",
            f"jobcards/{jobcard_id}/convert-to-invoice",
            200,
            data=invoice_conversion_data
        )
        
        if not success or not invoice.get('id'):
            return False
        
        invoice_id = invoice['id']
        
        # CRITICAL CHECK: Verify invoice is in draft status
        if invoice.get('status') != 'draft':
            print(f"❌ CRITICAL: Invoice should be in 'draft' status, got: {invoice.get('status')}")
            return False
        
        print(f"✅ CRITICAL: Invoice created in draft status: {invoice.get('status')}")
        
        # CRITICAL CHECK: Stock should NOT be deducted yet
        success, inventory_after_draft = self.run_test(
            "Check Inventory After Draft Creation (Should NOT be deducted)",
            "GET",
            "inventory/stock-totals",
            200
        )
        
        if not success:
            return False
        
        # Find our test inventory
        test_inventory = None
        for inv in inventory_after_draft:
            if inv.get('header_id') == inventory_id:
                test_inventory = inv
                break
        
        if not test_inventory:
            print(f"❌ Test inventory not found")
            return False
        
        if test_inventory.get('total_qty') != 5 or test_inventory.get('total_weight') != 500.0:
            print(f"❌ CRITICAL: Stock should NOT be deducted for draft invoice. Expected: 5 qty, 500.0g. Got: {test_inventory.get('total_qty')} qty, {test_inventory.get('total_weight')}g")
            return False
        
        print(f"✅ CRITICAL: Stock NOT deducted for draft invoice (total_qty: {test_inventory.get('total_qty')}, total_weight: {test_inventory.get('total_weight')}g)")
        
        # Step 5: FINALIZE the invoice
        success, finalized_response = self.run_test(
            "FINALIZE Invoice (Stock Should Be Deducted)",
            "POST",
            f"invoices/{invoice_id}/finalize",
            200
        )
        
        if not success:
            return False
        
        # CRITICAL CHECK: Response should confirm finalization
        success, updated_invoice = self.run_test(
            "Get Updated Invoice Status",
            "GET",
            f"invoices/{invoice_id}",
            200
        )
        
        if not success:
            return False
        
        if updated_invoice.get('status') != 'finalized':
            print(f"❌ CRITICAL: Invoice status should be 'finalized', got: {updated_invoice.get('status')}")
            return False
        
        print(f"✅ CRITICAL: Invoice finalized successfully")
        
        # CRITICAL CHECK: Stock movements should be created with negative values
        success, stock_movements = self.run_test(
            "Check Stock Movements After Finalization",
            "GET",
            "inventory/movements",
            200
        )
        
        if not success:
            return False
        
        # Find movements for this invoice
        invoice_movements = [
            m for m in stock_movements 
            if m.get('reference_type') == 'invoice' and m.get('reference_id') == invoice_id
        ]
        
        if not invoice_movements:
            print(f"❌ CRITICAL: No stock movements found for finalized invoice")
            return False
        
        # Verify movements have negative values (Stock OUT)
        for movement in invoice_movements:
            if movement.get('movement_type') != 'Stock OUT':
                print(f"❌ CRITICAL: Movement should be 'Stock OUT', got: {movement.get('movement_type')}")
                return False
            
            if movement.get('qty_delta', 0) >= 0 or movement.get('weight_delta', 0) >= 0:
                print(f"❌ CRITICAL: Stock movements should have NEGATIVE values. Got qty_delta: {movement.get('qty_delta')}, weight_delta: {movement.get('weight_delta')}")
                return False
        
        print(f"✅ CRITICAL: Stock movements created with negative values (Stock OUT)")
        
        # CRITICAL CHECK: Verify stock was actually deducted from inventory
        success, inventory_after_finalize = self.run_test(
            "Check Inventory After Finalization (Should Be Deducted)",
            "GET",
            "inventory/stock-totals",
            200
        )
        
        if not success:
            return False
        
        # Find our test inventory again
        test_inventory_final = None
        for inv in inventory_after_finalize:
            if inv.get('header_id') == inventory_id:
                test_inventory_final = inv
                break
        
        if not test_inventory_final:
            print(f"❌ Test inventory not found after finalization")
            return False
        
        expected_qty = 4  # 5 - 1 = 4
        expected_weight = 450.0  # 500.0 - 50.0 = 450.0
        
        if test_inventory_final.get('total_qty') != expected_qty or test_inventory_final.get('total_weight') != expected_weight:
            print(f"❌ CRITICAL: Stock should be deducted after finalization. Expected: {expected_qty} qty, {expected_weight}g. Got: {test_inventory_final.get('total_qty')} qty, {test_inventory_final.get('total_weight')}g")
            return False
        
        print(f"✅ CRITICAL: Stock deducted correctly (total_qty: {test_inventory_final.get('total_qty')}, total_weight: {test_inventory_final.get('total_weight')}g)")
        
        # CRITICAL CHECK: Job card should be locked
        success, locked_jobcard = self.run_test(
            "Check Job Card Locking After Finalization",
            "GET",
            f"jobcards/{jobcard_id}",
            200
        )
        
        if not success:
            return False
        
        if not locked_jobcard.get('locked'):
            print(f"❌ CRITICAL: Job card should be locked after invoice finalization")
            return False
        
        print(f"✅ CRITICAL: Job card locked after finalization (locked: {locked_jobcard.get('locked')})")
        
        # Step 6: Test immutability - Try to edit finalized invoice
        success, edit_error = self.run_test(
            "Try to Edit Finalized Invoice (Should Fail)",
            "PATCH",
            f"invoices/{invoice_id}",
            400,  # Expecting 400 error
            data={"notes": "Attempting to edit finalized invoice"}
        )
        
        if not success:
            print(f"❌ CRITICAL: Finalized invoice should reject edit attempts with 400 error")
            return False
        
        print(f"✅ CRITICAL: Finalized invoice correctly rejects edit attempts")
        
        # Step 7: Test re-finalization prevention
        success, refinalize_error = self.run_test(
            "Try to Re-finalize Invoice (Should Fail)",
            "POST",
            f"invoices/{invoice_id}/finalize",
            400,  # Expecting 400 error
        )
        
        if not success:
            print(f"❌ CRITICAL: Already finalized invoice should reject re-finalization with 400 error")
            return False
        
        print(f"✅ CRITICAL: Invoice correctly prevents re-finalization")
        
        # Store data for payment tests
        self.critical_test_data = {
            'customer_id': customer_id,
            'invoice_id': invoice_id,
            'grand_total': updated_invoice.get('grand_total', 0)
        }
        
        print(f"🎉 CRITICAL PRIORITY 1 TESTS PASSED - Invoice finalization & stock deduction working correctly!")
        return True

    def test_critical_payment_tracking(self):
        """
        PRIORITY 2: PAYMENT TRACKING (CRITICAL)
        Test payment processing and balance tracking
        """
        print("\n🔥 CRITICAL PRIORITY TESTING - PAYMENT TRACKING")
        
        if not hasattr(self, 'critical_test_data'):
            print("❌ Critical test data not available, run invoice finalization test first")
            return False
        
        invoice_id = self.critical_test_data['invoice_id']
        grand_total = self.critical_test_data['grand_total']
        
        print(f"   Testing payments for invoice with grand_total: {grand_total}")
        
        # Create cash account for payments
        cash_account_data = {
            "name": "Test Cash Account",
            "account_type": "cash",
            "opening_balance": 10000.0
        }
        
        success, cash_account = self.run_test(
            "Create Cash Account for Payments",
            "POST",
            "accounts",
            200,
            data=cash_account_data
        )
        
        if not success or not cash_account.get('id'):
            return False
        
        cash_account_id = cash_account['id']
        
        # Create bank account for payments
        bank_account_data = {
            "name": "Test Bank Account",
            "account_type": "bank",
            "opening_balance": 20000.0
        }
        
        success, bank_account = self.run_test(
            "Create Bank Account for Payments",
            "POST",
            "accounts",
            200,
            data=bank_account_data
        )
        
        if not success or not bank_account.get('id'):
            return False
        
        bank_account_id = bank_account['id']
        
        # Step 8: Add Cash payment (50% of grand_total)
        partial_amount = round(grand_total * 0.5, 2)
        
        payment_data_1 = {
            "payment_mode": "Cash",
            "amount": partial_amount,
            "account_id": cash_account_id
        }
        
        success, payment_response_1 = self.run_test(
            "Add Cash Payment (50% of total)",
            "POST",
            f"invoices/{invoice_id}/add-payment",
            200,
            data=payment_data_1
        )
        
        if not success:
            return False
        
        # CRITICAL CHECK: Response should show correct payment tracking
        new_paid_amount = payment_response_1.get('new_paid_amount', 0)
        new_balance_due = payment_response_1.get('new_balance_due', 0)
        payment_status = payment_response_1.get('payment_status', '')
        
        if abs(new_paid_amount - partial_amount) > 0.01:
            print(f"❌ CRITICAL: new_paid_amount should be {partial_amount}, got: {new_paid_amount}")
            return False
        
        expected_balance = round(grand_total - partial_amount, 2)
        if abs(new_balance_due - expected_balance) > 0.01:
            print(f"❌ CRITICAL: new_balance_due should be {expected_balance}, got: {new_balance_due}")
            return False
        
        if payment_status != 'partial':
            print(f"❌ CRITICAL: payment_status should be 'partial', got: {payment_status}")
            return False
        
        transaction_id_1 = payment_response_1.get('transaction_id')
        if not transaction_id_1:
            print(f"❌ CRITICAL: transaction_id should be created")
            return False
        
        print(f"✅ CRITICAL: Cash payment processed correctly (paid: {new_paid_amount}, balance: {new_balance_due}, status: {payment_status})")
        
        # Step 9: Add Bank Transfer payment to complete
        remaining_amount = new_balance_due
        
        payment_data_2 = {
            "payment_mode": "Bank Transfer",
            "amount": remaining_amount,
            "account_id": bank_account_id
        }
        
        success, payment_response_2 = self.run_test(
            "Add Bank Transfer Payment (Complete Payment)",
            "POST",
            f"invoices/{invoice_id}/add-payment",
            200,
            data=payment_data_2
        )
        
        if not success:
            return False
        
        # CRITICAL CHECK: Response should show payment completion
        final_paid_amount = payment_response_2.get('new_paid_amount', 0)
        final_balance_due = payment_response_2.get('new_balance_due', 0)
        final_payment_status = payment_response_2.get('payment_status', '')
        
        if abs(final_paid_amount - grand_total) > 0.01:
            print(f"❌ CRITICAL: final paid amount should equal grand_total {grand_total}, got: {final_paid_amount}")
            return False
        
        if final_balance_due > 0.01:
            print(f"❌ CRITICAL: final balance_due should be ~0, got: {final_balance_due}")
            return False
        
        if final_payment_status != 'paid':
            print(f"❌ CRITICAL: final payment_status should be 'paid', got: {final_payment_status}")
            return False
        
        transaction_id_2 = payment_response_2.get('transaction_id')
        if not transaction_id_2:
            print(f"❌ CRITICAL: second transaction_id should be created")
            return False
        
        print(f"✅ CRITICAL: Final payment processed correctly (total paid: {final_paid_amount}, balance: {final_balance_due}, status: {final_payment_status})")
        
        print(f"🎉 CRITICAL PRIORITY 2 TESTS PASSED - Payment tracking working correctly!")
        return True

    def test_critical_walk_in_vs_saved_customer(self):
        """
        PRIORITY 3: WALK-IN VS SAVED CUSTOMER
        Test different customer handling workflows
        """
        print("\n🔥 CRITICAL PRIORITY TESTING - WALK-IN VS SAVED CUSTOMER")
        
        # Step 10: Create walk-in job card
        walk_in_jobcard_data = {
            "card_type": "individual",
            "customer_type": "walk_in",
            "walk_in_name": "Walk-in Customer Test",
            "walk_in_phone": "88776655",
            "items": [{
                "category": "Gold 22K Test",
                "description": "Walk-in Gold Ring",
                "qty": 1,
                "weight_in": 30.0,
                "weight_out": 30.0,
                "purity": 916,
                "work_type": "polish"
            }]
        }
        
        success, walk_in_jobcard = self.run_test(
            "Create Walk-in Job Card",
            "POST",
            "jobcards",
            200,
            data=walk_in_jobcard_data
        )
        
        if not success or not walk_in_jobcard.get('id'):
            return False
        
        walk_in_jobcard_id = walk_in_jobcard['id']
        print(f"✅ Created walk-in job card: {walk_in_jobcard['job_card_number']}")
        
        # Convert to walk-in invoice
        walk_in_conversion_data = {
            "customer_type": "walk_in",
            "customer_name": "Walk-in Customer Test",
            "customer_phone": "88776655",
            "metal_rate": 20.0,
            "vat_percent": 5
        }
        
        success, walk_in_invoice = self.run_test(
            "Convert to Walk-in Invoice",
            "POST",
            f"jobcards/{walk_in_jobcard_id}/convert-to-invoice",
            200,
            data=walk_in_conversion_data
        )
        
        if not success or not walk_in_invoice.get('id'):
            return False
        
        walk_in_invoice_id = walk_in_invoice['id']
        
        # CRITICAL CHECK: Walk-in invoice should have correct customer handling
        if walk_in_invoice.get('customer_id'):
            print(f"❌ CRITICAL: Walk-in invoice should NOT have customer_id, got: {walk_in_invoice.get('customer_id')}")
            return False
        
        if walk_in_invoice.get('customer_type') != 'walk_in':
            print(f"❌ CRITICAL: Invoice customer_type should be 'walk_in', got: {walk_in_invoice.get('customer_type')}")
            return False
        
        if walk_in_invoice.get('walk_in_name') != "Walk-in Customer Test":
            print(f"❌ CRITICAL: Walk-in name mismatch, expected 'Walk-in Customer Test', got: {walk_in_invoice.get('walk_in_name')}")
            return False
        
        print(f"✅ CRITICAL: Walk-in invoice created correctly (customer_id: {walk_in_invoice.get('customer_id')}, customer_type: {walk_in_invoice.get('customer_type')})")
        
        # Step 11: Finalize walk-in invoice
        success, finalized_walk_in = self.run_test(
            "Finalize Walk-in Invoice",
            "POST",
            f"invoices/{walk_in_invoice_id}/finalize",
            200
        )
        
        if not success:
            return False
        
        # Get updated invoice status
        success, updated_walk_in_invoice = self.run_test(
            "Get Updated Walk-in Invoice Status",
            "GET",
            f"invoices/{walk_in_invoice_id}",
            200
        )
        
        if not success:
            return False
        
        # CRITICAL CHECK: Should work correctly
        if updated_walk_in_invoice.get('status') != 'finalized':
            print(f"❌ CRITICAL: Walk-in invoice should be finalized, got: {updated_walk_in_invoice.get('status')}")
            return False
        
        print(f"✅ CRITICAL: Walk-in invoice finalized successfully")
        
        # CRITICAL CHECK: Stock should be deducted
        success, movements_walk_in = self.run_test(
            "Check Stock Movements for Walk-in Invoice",
            "GET",
            "inventory/movements",
            200
        )
        
        if not success:
            return False
        
        walk_in_movements = [
            m for m in movements_walk_in 
            if m.get('reference_type') == 'invoice' and m.get('reference_id') == walk_in_invoice_id
        ]
        
        if not walk_in_movements:
            print(f"❌ CRITICAL: Stock movements should be created for walk-in invoice")
            return False
        
        print(f"✅ CRITICAL: Stock deducted for walk-in invoice ({len(walk_in_movements)} movements)")
        
        # CRITICAL CHECK: Transaction created but party_id should be null/empty
        success, transactions = self.run_test(
            "Check Transactions for Walk-in Invoice",
            "GET",
            "transactions",
            200
        )
        
        if not success:
            return False
        
        walk_in_invoice_number = updated_walk_in_invoice.get('invoice_number', '')
        walk_in_transaction = None
        for txn in transactions:
            if (txn.get('category') == 'Sales Invoice' and
                walk_in_invoice_number in txn.get('notes', '')):
                walk_in_transaction = txn
                break
        
        if not walk_in_transaction:
            print(f"❌ CRITICAL: Transaction should be created for walk-in invoice")
            return False
        
        if walk_in_transaction.get('party_id'):
            print(f"❌ CRITICAL: Walk-in transaction should NOT have party_id, got: {walk_in_transaction.get('party_id')}")
            return False
        
        print(f"✅ CRITICAL: Walk-in transaction created without party_id")
        
        # Step 12: Add payment to walk-in invoice
        # Create cash account if not exists
        cash_account_data = {
            "name": "Walk-in Cash Account",
            "account_type": "cash",
            "opening_balance": 5000.0
        }
        
        success, walk_in_cash_account = self.run_test(
            "Create Cash Account for Walk-in Payment",
            "POST",
            "accounts",
            200,
            data=cash_account_data
        )
        
        if not success:
            return False
        
        walk_in_payment_data = {
            "payment_mode": "Cash",
            "amount": updated_walk_in_invoice.get('grand_total', 0),
            "account_id": walk_in_cash_account['id']
        }
        
        success, walk_in_payment_response = self.run_test(
            "Add Payment to Walk-in Invoice",
            "POST",
            f"invoices/{walk_in_invoice_id}/add-payment",
            200,
            data=walk_in_payment_data
        )
        
        if not success:
            return False
        
        # CRITICAL CHECK: Should work correctly
        if walk_in_payment_response.get('payment_status') != 'paid':
            print(f"❌ CRITICAL: Walk-in invoice should be fully paid, got status: {walk_in_payment_response.get('payment_status')}")
            return False
        
        print(f"✅ CRITICAL: Walk-in payment processed successfully")
        
        # CRITICAL CHECK: Payment transaction created without party_id
        payment_transaction_id = walk_in_payment_response.get('transaction_id')
        if not payment_transaction_id:
            print(f"❌ CRITICAL: Payment transaction should be created")
            return False
        
        # Get the payment transaction
        success, updated_transactions = self.run_test(
            "Get Updated Transactions",
            "GET",
            "transactions",
            200
        )
        
        if not success:
            return False
        
        payment_transaction = None
        for txn in updated_transactions:
            if txn.get('id') == payment_transaction_id:
                payment_transaction = txn
                break
        
        if not payment_transaction:
            print(f"❌ CRITICAL: Payment transaction not found")
            return False
        
        if payment_transaction.get('party_id'):
            print(f"❌ CRITICAL: Walk-in payment transaction should NOT have party_id, got: {payment_transaction.get('party_id')}")
            return False
        
        print(f"✅ CRITICAL: Walk-in payment transaction created without party_id")
        
        print(f"🎉 CRITICAL PRIORITY 3 TESTS PASSED - Walk-in vs saved customer handling working correctly!")
        return True

    def run_all_tests(self):
        """Run all critical tests in sequence"""
        print("🚀 Starting Gold Shop ERP CRITICAL Backend API Tests...")
        print(f"   Base URL: {self.base_url}")
        
        # Authentication tests
        if not self.test_login():
            print("❌ Login failed - stopping tests")
            return False
        
        # CRITICAL PRIORITY TESTS (as requested in review)
        critical_tests = [
            self.test_critical_invoice_finalization_stock_deduction,
            self.test_critical_payment_tracking,
            self.test_critical_walk_in_vs_saved_customer
        ]
        
        print("\n" + "="*80)
        print("🔥 RUNNING CRITICAL PRIORITY TESTS FOR GOLD SHOP ERP")
        print("="*80)
        
        critical_passed = 0
        for test_method in critical_tests:
            try:
                if test_method():
                    critical_passed += 1
                    print(f"✅ CRITICAL TEST PASSED: {test_method.__name__}")
                else:
                    print(f"❌ CRITICAL TEST FAILED: {test_method.__name__}")
            except Exception as e:
                print(f"❌ CRITICAL TEST ERROR in {test_method.__name__}: {str(e)}")
        
        print(f"\n🎯 CRITICAL TESTS SUMMARY: {critical_passed}/{len(critical_tests)} PASSED")
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        print(f"   CRITICAL TESTS: {critical_passed}/{len(critical_tests)} PASSED")
        
        return critical_passed == len(critical_tests)

def main():
    tester = GoldShopERPTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

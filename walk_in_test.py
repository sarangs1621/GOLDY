import requests
import sys
import json
from datetime import datetime
import re

class WalkInInvoiceTransactionTester:
    def __init__(self, base_url="https://decimal-precision.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None

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

    def test_auth_me(self):
        """Test getting current user info"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        return success and response.get('username') == 'admin'

    def test_walk_in_invoice_transaction_creation(self):
        """🔥 CRITICAL FIX VERIFICATION - Walk-in Invoice Transaction Creation"""
        print("\n🔥 TESTING WALK-IN INVOICE TRANSACTION CREATION FIX")
        
        # Step 1: Create a walk-in job card with at least 1 item
        jobcard_data = {
            "card_type": "individual",
            "customer_type": "walk_in",
            "walk_in_name": "John Walk-in Customer",
            "walk_in_phone": "+968 9999 1234",
            "delivery_date": "2025-01-20",
            "notes": "Walk-in job card for transaction creation test",
            "items": [{
                "category": "Ring",
                "description": "Gold ring for walk-in customer",
                "qty": 1,
                "weight_in": 10.500,
                "weight_out": 10.200,
                "purity": 916,
                "work_type": "polish",
                "remarks": "Polish and clean",
                "making_charge_type": "flat",
                "making_charge_value": 15.0,
                "vat_percent": 5.0
            }]
        }
        
        success, jobcard = self.run_test(
            "Create Walk-in Job Card",
            "POST",
            "jobcards",
            200,
            data=jobcard_data
        )
        
        if not success or not jobcard.get('id'):
            print("❌ Failed to create walk-in job card")
            return False
        
        jobcard_id = jobcard['id']
        print(f"✅ Walk-in job card created: {jobcard_id}")
        
        # Step 2: Convert to walk-in invoice
        invoice_conversion_data = {
            "customer_type": "walk_in",
            "walk_in_name": "John Walk-in Customer",
            "walk_in_phone": "+968 9999 1234"
        }
        
        success, invoice = self.run_test(
            "Convert Walk-in Job Card to Invoice",
            "POST",
            f"jobcards/{jobcard_id}/convert-to-invoice",
            200,
            data=invoice_conversion_data
        )
        
        if not success or not invoice.get('id'):
            print("❌ Failed to convert walk-in job card to invoice")
            return False
        
        invoice_id = invoice['id']
        grand_total = invoice.get('grand_total', 0)
        print(f"✅ Walk-in invoice created: {invoice_id}, grand_total: {grand_total}")
        
        # Verify invoice has walk-in customer details
        if invoice.get('customer_type') != 'walk_in':
            print(f"❌ Invoice customer_type should be 'walk_in', got: {invoice.get('customer_type')}")
            return False
        
        if invoice.get('walk_in_name') != 'John Walk-in Customer':
            print(f"❌ Invoice walk_in_name mismatch")
            return False
        
        if invoice.get('walk_in_phone') != '+968 9999 1234':
            print(f"❌ Invoice walk_in_phone mismatch")
            return False
        
        print(f"✅ Walk-in invoice has correct customer details")
        
        # Step 3: Finalize the walk-in invoice
        success, finalized_invoice = self.run_test(
            "Finalize Walk-in Invoice",
            "POST",
            f"invoices/{invoice_id}/finalize",
            200
        )
        
        if not success:
            print("❌ Failed to finalize walk-in invoice")
            return False
        
        print(f"✅ Walk-in invoice finalized successfully")
        
        # Step 4: 🔥 CRITICAL CHECK - Query transactions collection for transaction record
        success, transactions = self.run_test(
            "Get All Transactions (Find Walk-in Transaction)",
            "GET",
            "transactions",
            200
        )
        
        if not success:
            print("❌ Failed to get transactions")
            return False
        
        # Find the transaction record for this walk-in invoice
        walk_in_transaction = None
        for txn in transactions:
            if (txn.get('reference_type') == 'invoice' and 
                txn.get('reference_id') == invoice_id and
                txn.get('category') == 'Sales Invoice'):
                walk_in_transaction = txn
                break
        
        if not walk_in_transaction:
            print(f"❌ CRITICAL FAILURE: No transaction record found for walk-in invoice {invoice_id}")
            print(f"   Expected: reference_type='invoice', reference_id='{invoice_id}', category='Sales Invoice'")
            return False
        
        print(f"✅ CRITICAL SUCCESS: Transaction record found for walk-in invoice!")
        
        # Verify transaction record has correct fields for walk-in
        verification_results = []
        
        # Check reference_type = "invoice"
        if walk_in_transaction.get('reference_type') != 'invoice':
            print(f"❌ reference_type should be 'invoice', got: {walk_in_transaction.get('reference_type')}")
            verification_results.append(False)
        else:
            print(f"✅ reference_type correct: {walk_in_transaction.get('reference_type')}")
            verification_results.append(True)
        
        # Check reference_id = invoice_id
        if walk_in_transaction.get('reference_id') != invoice_id:
            print(f"❌ reference_id should be '{invoice_id}', got: {walk_in_transaction.get('reference_id')}")
            verification_results.append(False)
        else:
            print(f"✅ reference_id correct: {walk_in_transaction.get('reference_id')}")
            verification_results.append(True)
        
        # Check category = "Sales Invoice"
        if walk_in_transaction.get('category') != 'Sales Invoice':
            print(f"❌ category should be 'Sales Invoice', got: {walk_in_transaction.get('category')}")
            verification_results.append(False)
        else:
            print(f"✅ category correct: {walk_in_transaction.get('category')}")
            verification_results.append(True)
        
        # Check mode = "invoice"
        if walk_in_transaction.get('mode') != 'invoice':
            print(f"❌ mode should be 'invoice', got: {walk_in_transaction.get('mode')}")
            verification_results.append(False)
        else:
            print(f"✅ mode correct: {walk_in_transaction.get('mode')}")
            verification_results.append(True)
        
        # Check party_id = None (for walk-in)
        if walk_in_transaction.get('party_id') is not None:
            print(f"❌ party_id should be None for walk-in, got: {walk_in_transaction.get('party_id')}")
            verification_results.append(False)
        else:
            print(f"✅ party_id correct (None for walk-in): {walk_in_transaction.get('party_id')}")
            verification_results.append(True)
        
        # Check party_name = None (for walk-in)
        if walk_in_transaction.get('party_name') is not None:
            print(f"❌ party_name should be None for walk-in, got: {walk_in_transaction.get('party_name')}")
            verification_results.append(False)
        else:
            print(f"✅ party_name correct (None for walk-in): {walk_in_transaction.get('party_name')}")
            verification_results.append(True)
        
        # Check notes containing walk_in_name and walk_in_phone
        notes = walk_in_transaction.get('notes', '')
        if 'John Walk-in Customer' not in notes:
            print(f"❌ notes should contain walk_in_name 'John Walk-in Customer', got: {notes}")
            verification_results.append(False)
        else:
            print(f"✅ notes contain walk_in_name")
            verification_results.append(True)
        
        if '+968 9999 1234' not in notes:
            print(f"❌ notes should contain walk_in_phone '+968 9999 1234', got: {notes}")
            verification_results.append(False)
        else:
            print(f"✅ notes contain walk_in_phone")
            verification_results.append(True)
        
        # Check amount = invoice grand_total
        if abs(walk_in_transaction.get('amount', 0) - grand_total) > 0.01:
            print(f"❌ amount should be {grand_total}, got: {walk_in_transaction.get('amount')}")
            verification_results.append(False)
        else:
            print(f"✅ amount correct: {walk_in_transaction.get('amount')}")
            verification_results.append(True)
        
        # Check transaction_number format: TXN-YYYY-NNNN
        txn_number = walk_in_transaction.get('transaction_number', '')
        if not re.match(r'^TXN-\d{4}-\d{4}$', txn_number):
            print(f"❌ transaction_number format incorrect: {txn_number}")
            verification_results.append(False)
        else:
            print(f"✅ transaction_number format correct: {txn_number}")
            verification_results.append(True)
        
        # Final verification
        all_checks_passed = all(verification_results)
        
        if all_checks_passed:
            print(f"\n🎉 CRITICAL FIX VERIFICATION SUCCESSFUL!")
            print(f"   ✅ Transaction record CREATED for walk-in invoice finalization")
            print(f"   ✅ Transaction has correct fields for walk-in (party_id=None, notes with customer info)")
            print(f"   ✅ Transaction number auto-generated correctly: {txn_number}")
            print(f"   ✅ Amount matches invoice grand_total: {grand_total}")
            print(f"   ✅ All walk-in transaction creation requirements met")
        else:
            print(f"\n❌ CRITICAL FIX VERIFICATION FAILED!")
            print(f"   Some transaction record fields are incorrect")
        
        return all_checks_passed

    def run_test_suite(self):
        """Run the focused walk-in invoice transaction creation test"""
        print("🚀 Starting Walk-in Invoice Transaction Creation Test")
        print(f"   Base URL: {self.base_url}")
        
        # Authentication tests
        if not self.test_login():
            print("❌ Login failed - stopping tests")
            return
        
        if not self.test_auth_me():
            print("❌ Auth verification failed")
            return
        
        # 🔥 CRITICAL FIX VERIFICATION - Walk-in Invoice Transaction Creation
        print("\n" + "="*80)
        print("🔥 CRITICAL FIX VERIFICATION - WALK-IN INVOICE TRANSACTION CREATION")
        print("="*80)
        
        if not self.test_walk_in_invoice_transaction_creation():
            print("❌ CRITICAL: Walk-in invoice transaction creation test FAILED")
        else:
            print("✅ CRITICAL: Walk-in invoice transaction creation test PASSED")
        
        print("="*80)
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")

if __name__ == "__main__":
    tester = WalkInInvoiceTransactionTester()
    tester.run_test_suite()
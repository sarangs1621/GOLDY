#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class FinalizationTester:
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

    def test_transaction_type_fix(self):
        """Test that service invoices create debit transactions"""
        print("\n🔥 TESTING TRANSACTION TYPE FIX")
        
        # Create customer
        customer_data = {
            "name": f"Transaction Type Test {datetime.now().strftime('%H%M%S')}",
            "phone": "+968 7777 8888",
            "address": "Transaction Type Test Address",
            "party_type": "customer"
        }
        
        success, customer = self.run_test(
            "Create Customer for Transaction Type Test",
            "POST",
            "parties",
            200,
            data=customer_data
        )
        
        if not success:
            return False
        
        # Create job card
        jobcard_data = {
            "card_type": "individual",
            "customer_id": customer['id'],
            "customer_name": customer['name'],
            "delivery_date": "2025-01-25",
            "items": [{
                "category": "Ring",
                "description": "Test ring for transaction type",
                "qty": 1,
                "weight_in": 10.0,
                "weight_out": 9.8,
                "purity": 916,
                "work_type": "polish"
            }]
        }
        
        success, jobcard = self.run_test(
            "Create Job Card for Transaction Type Test",
            "POST",
            "jobcards",
            200,
            data=jobcard_data
        )
        
        if not success:
            return False
        
        # Convert to invoice (will be service type)
        success, invoice = self.run_test(
            "Convert Job Card to Invoice (Service Type)",
            "POST",
            f"jobcards/{jobcard['id']}/convert-to-invoice",
            200
        )
        
        if not success:
            return False
        
        print(f"   Invoice type: {invoice.get('invoice_type')}")
        
        # Finalize invoice
        success, finalized = self.run_test(
            "Finalize Service Invoice",
            "POST",
            f"invoices/{invoice['id']}/finalize",
            200
        )
        
        if not success:
            return False
        
        # Check transaction type
        success, transactions = self.run_test(
            "Get Transactions to Check Type",
            "GET",
            "transactions",
            200
        )
        
        if not success:
            return False
        
        # Find the transaction for this invoice
        invoice_number = invoice.get('invoice_number')
        ledger_entry = None
        for txn in transactions:
            if (txn.get('party_id') == customer['id'] and 
                invoice_number in txn.get('notes', '')):
                ledger_entry = txn
                break
        
        if not ledger_entry:
            print(f"❌ No transaction found for service invoice")
            return False
        
        transaction_type = ledger_entry.get('transaction_type')
        print(f"   Transaction type: {transaction_type}")
        
        if transaction_type != 'debit':
            print(f"❌ Service invoice should create debit transaction, got: {transaction_type}")
            return False
        
        print(f"✅ Service invoice correctly created debit transaction")
        return True

    def test_sales_account_creation(self):
        """Test Sales account creation with proper fields"""
        print("\n🔥 TESTING SALES ACCOUNT CREATION FIX")
        
        # Try to get accounts (this should work now)
        success, accounts = self.run_test(
            "Get All Accounts (Should Work Now)",
            "GET",
            "accounts",
            200
        )
        
        if not success:
            return False
        
        print(f"✅ Accounts endpoint working correctly")
        
        # Check if Sales account exists and has proper fields
        sales_account = None
        for account in accounts:
            if account.get('name') == 'Sales':
                sales_account = account
                break
        
        if sales_account:
            print(f"✅ Sales account exists with proper fields:")
            print(f"   - ID: {sales_account.get('id')}")
            print(f"   - Name: {sales_account.get('name')}")
            print(f"   - Type: {sales_account.get('account_type')}")
            print(f"   - Created By: {sales_account.get('created_by')}")
            
            if not sales_account.get('created_by'):
                print(f"❌ Sales account missing created_by field")
                return False
        else:
            print(f"ℹ️  Sales account doesn't exist yet, will be created on next invoice finalization")
        
        return True

    def run_tests(self):
        """Run the specific finalization fix tests"""
        print("🚀 Testing Enhanced Invoice Finalization Fixes")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)

        if not self.test_login():
            print("❌ Login failed")
            return False

        results = {
            "Transaction Type Fix": self.test_transaction_type_fix(),
            "Sales Account Creation Fix": self.test_sales_account_creation()
        }

        print("\n" + "=" * 60)
        print("📊 FIX TEST RESULTS")
        print("=" * 60)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:<30} {status}")

        print(f"\n📈 Overall: {self.tests_passed}/{self.tests_run} tests passed")
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"🎯 Success Rate: {success_rate:.1f}%")

        return all(results.values())

def main():
    tester = FinalizationTester()
    success = tester.run_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
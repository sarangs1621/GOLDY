import requests
import sys
import json
from datetime import datetime

class Module4PurchasePaymentTester:
    def __init__(self, base_url="https://decimal-precision.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None
        self.test_data = {
            'vendor_id': None,
            'account_id': None,
            'purchases': []
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

    def setup_authentication(self):
        """Setup admin authentication"""
        print("\n🔐 SETTING UP AUTHENTICATION")
        
        # Try to register admin user if it doesn't exist
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

    def setup_test_data(self):
        """Create vendor party and account for testing"""
        print("\n🏗️ SETTING UP TEST DATA")
        
        # Create vendor party
        vendor_data = {
            "name": f"Test Vendor {datetime.now().strftime('%H%M%S')}",
            "phone": "+968 9999 1111",
            "address": "Test Vendor Address",
            "party_type": "vendor",
            "notes": "Vendor for MODULE 4 purchase testing"
        }
        
        success, vendor = self.run_test(
            "Create Test Vendor Party",
            "POST",
            "parties",
            200,
            data=vendor_data
        )
        
        if not success or not vendor.get('id'):
            return False
        
        self.test_data['vendor_id'] = vendor['id']
        print(f"   Vendor created: {vendor['name']} (ID: {vendor['id']})")
        
        # Create test account for payments
        account_data = {
            "name": f"Test Cash Account {datetime.now().strftime('%H%M%S')}",
            "account_type": "cash",
            "opening_balance": 10000.00
        }
        
        success, account = self.run_test(
            "Create Test Account",
            "POST",
            "accounts",
            200,
            data=account_data
        )
        
        if not success or not account.get('id'):
            return False
        
        self.test_data['account_id'] = account['id']
        print(f"   Account created: {account['name']} (ID: {account['id']})")
        
        return True

    def test_1_create_draft_purchase_with_payment_fields(self):
        """TEST 1: Create Draft Purchase with Payment Fields"""
        print("\n📝 TEST 1: Create Draft Purchase with Payment Fields")
        
        purchase_data = {
            "vendor_party_id": self.test_data['vendor_id'],
            "description": "Test purchase with payment",
            "weight_grams": 100.456,
            "entered_purity": 999,
            "rate_per_gram": 50.75,
            "amount_total": 5098.14,  # 100.456 * 50.75
            "paid_amount_money": 3000.00,
            "payment_mode": "Cash",
            "account_id": self.test_data['account_id']
        }
        
        success, purchase = self.run_test(
            "Create Draft Purchase with Payment",
            "POST",
            "purchases",
            200,
            data=purchase_data
        )
        
        if not success:
            return False
        
        # Verify balance_due_money auto-calculated
        expected_balance = 5098.14 - 3000.00  # 2098.14
        actual_balance = purchase.get('balance_due_money', 0)
        
        if abs(actual_balance - expected_balance) > 0.01:
            print(f"❌ Balance due calculation error: expected {expected_balance}, got {actual_balance}")
            return False
        
        # Verify precision (3 decimals gold, 2 decimals money)
        if purchase.get('weight_grams') != 100.456:
            print(f"❌ Weight precision error: expected 100.456, got {purchase.get('weight_grams')}")
            return False
        
        if purchase.get('amount_total') != 5098.14:
            print(f"❌ Amount precision error: expected 5098.14, got {purchase.get('amount_total')}")
            return False
        
        print(f"✅ Purchase created with correct balance_due_money: {actual_balance}")
        print(f"✅ Precision maintained: weight={purchase.get('weight_grams')}, amount={purchase.get('amount_total')}")
        
        self.test_data['purchases'].append(purchase['id'])
        return True

    def test_2_create_draft_purchase_with_gold_settlement(self):
        """TEST 2: Create Draft Purchase with Gold Settlement"""
        print("\n🥇 TEST 2: Create Draft Purchase with Gold Settlement")
        
        purchase_data = {
            "vendor_party_id": self.test_data['vendor_id'],
            "description": "Test purchase with gold settlement",
            "weight_grams": 75.125,
            "entered_purity": 995,
            "rate_per_gram": 48.50,
            "amount_total": 3643.56,
            "paid_amount_money": 0.00,
            "advance_in_gold_grams": 25.500,
            "exchange_in_gold_grams": 10.250
        }
        
        success, purchase = self.run_test(
            "Create Draft Purchase with Gold Settlement",
            "POST",
            "purchases",
            200,
            data=purchase_data
        )
        
        if not success:
            return False
        
        # Verify balance_due_money = amount_total (no payment)
        if purchase.get('balance_due_money') != 3643.56:
            print(f"❌ Balance due should equal amount_total: expected 3643.56, got {purchase.get('balance_due_money')}")
            return False
        
        # Verify gold values have 3 decimal precision
        if purchase.get('advance_in_gold_grams') != 25.500:
            print(f"❌ Advance gold precision error: expected 25.500, got {purchase.get('advance_in_gold_grams')}")
            return False
        
        if purchase.get('exchange_in_gold_grams') != 10.250:
            print(f"❌ Exchange gold precision error: expected 10.250, got {purchase.get('exchange_in_gold_grams')}")
            return False
        
        print(f"✅ Gold settlement purchase created with 3-decimal precision")
        print(f"   Advance gold: {purchase.get('advance_in_gold_grams')}g")
        print(f"   Exchange gold: {purchase.get('exchange_in_gold_grams')}g")
        
        self.test_data['purchases'].append(purchase['id'])
        return True

    def test_3_edit_draft_purchase_balance_recalculation(self):
        """TEST 3: Edit Draft Purchase - Verify Balance Recalculation"""
        print("\n✏️ TEST 3: Edit Draft Purchase - Balance Recalculation")
        
        if not self.test_data['purchases']:
            print("❌ No purchases available for editing")
            return False
        
        purchase_id = self.test_data['purchases'][0]
        
        # Update paid_amount_money
        update_data = {
            "paid_amount_money": 4000.00
        }
        
        success, updated_purchase = self.run_test(
            "Update Purchase Payment Amount",
            "PATCH",
            f"purchases/{purchase_id}",
            200,
            data=update_data
        )
        
        if not success:
            return False
        
        # Verify balance recalculated: 5098.14 - 4000.00 = 1098.14
        expected_balance = 5098.14 - 4000.00
        actual_balance = updated_purchase.get('balance_due_money', 0)
        
        if abs(actual_balance - expected_balance) > 0.01:
            print(f"❌ Balance recalculation error: expected {expected_balance}, got {actual_balance}")
            return False
        
        print(f"✅ Balance recalculated correctly: {actual_balance}")
        return True

    def test_4_finalize_purchase_full_payment(self):
        """TEST 4: Finalize Purchase with ONLY Payment (Full Payment)"""
        print("\n💰 TEST 4: Finalize Purchase with Full Payment")
        
        # Create purchase with full payment
        purchase_data = {
            "vendor_party_id": self.test_data['vendor_id'],
            "description": "Full payment purchase test",
            "weight_grams": 50.000,
            "entered_purity": 916,
            "rate_per_gram": 20.00,
            "amount_total": 1000.00,
            "paid_amount_money": 1000.00,
            "payment_mode": "Bank Transfer",
            "account_id": self.test_data['account_id']
        }
        
        success, purchase = self.run_test(
            "Create Purchase for Full Payment Test",
            "POST",
            "purchases",
            200,
            data=purchase_data
        )
        
        if not success:
            return False
        
        purchase_id = purchase['id']
        
        # Finalize the purchase
        success, finalized_response = self.run_test(
            "Finalize Purchase with Full Payment",
            "POST",
            f"purchases/{purchase_id}/finalize",
            200
        )
        
        if not success:
            return False
        
        # Verify response includes correct IDs and amounts
        if not finalized_response.get('stock_movement_id'):
            print(f"❌ Missing stock_movement_id in response")
            return False
        
        if not finalized_response.get('payment_transaction_id'):
            print(f"❌ Missing payment_transaction_id in response")
            return False
        
        if finalized_response.get('vendor_payable_transaction_id'):
            print(f"❌ Should not have vendor_payable_transaction_id for full payment")
            return False
        
        if finalized_response.get('paid_amount') != 1000.00:
            print(f"❌ Paid amount mismatch: expected 1000.00, got {finalized_response.get('paid_amount')}")
            return False
        
        if finalized_response.get('balance_due') != 0.00:
            print(f"❌ Balance due should be 0.00, got {finalized_response.get('balance_due')}")
            return False
        
        print(f"✅ Full payment finalization successful:")
        print(f"   Stock Movement ID: {finalized_response.get('stock_movement_id')}")
        print(f"   Payment Transaction ID: {finalized_response.get('payment_transaction_id')}")
        print(f"   Paid Amount: {finalized_response.get('paid_amount')}")
        print(f"   Balance Due: {finalized_response.get('balance_due')}")
        
        return True

    def test_5_finalize_purchase_partial_payment(self):
        """TEST 5: Finalize Purchase with Partial Payment"""
        print("\n💸 TEST 5: Finalize Purchase with Partial Payment")
        
        # Create purchase with partial payment
        purchase_data = {
            "vendor_party_id": self.test_data['vendor_id'],
            "description": "Partial payment purchase test",
            "weight_grams": 75.000,
            "entered_purity": 916,
            "rate_per_gram": 20.00,
            "amount_total": 1500.00,
            "paid_amount_money": 900.00,
            "payment_mode": "Cash",
            "account_id": self.test_data['account_id']
        }
        
        success, purchase = self.run_test(
            "Create Purchase for Partial Payment Test",
            "POST",
            "purchases",
            200,
            data=purchase_data
        )
        
        if not success:
            return False
        
        purchase_id = purchase['id']
        
        # Finalize the purchase
        success, finalized_response = self.run_test(
            "Finalize Purchase with Partial Payment",
            "POST",
            f"purchases/{purchase_id}/finalize",
            200
        )
        
        if not success:
            return False
        
        # Verify creates both DEBIT and CREDIT transactions
        if not finalized_response.get('payment_transaction_id'):
            print(f"❌ Missing payment_transaction_id for partial payment")
            return False
        
        if not finalized_response.get('vendor_payable_transaction_id'):
            print(f"❌ Missing vendor_payable_transaction_id for partial payment")
            return False
        
        if finalized_response.get('paid_amount') != 900.00:
            print(f"❌ Paid amount mismatch: expected 900.00, got {finalized_response.get('paid_amount')}")
            return False
        
        if finalized_response.get('balance_due') != 600.00:
            print(f"❌ Balance due mismatch: expected 600.00, got {finalized_response.get('balance_due')}")
            return False
        
        print(f"✅ Partial payment finalization successful:")
        print(f"   Payment Transaction ID: {finalized_response.get('payment_transaction_id')}")
        print(f"   Vendor Payable Transaction ID: {finalized_response.get('vendor_payable_transaction_id')}")
        print(f"   Paid Amount: {finalized_response.get('paid_amount')}")
        print(f"   Balance Due: {finalized_response.get('balance_due')}")
        
        return True

    def test_6_finalize_purchase_advance_gold_settlement(self):
        """TEST 6: Finalize Purchase with Advance Gold Settlement"""
        print("\n🥇 TEST 6: Finalize Purchase with Advance Gold Settlement")
        
        # Create purchase with advance gold
        purchase_data = {
            "vendor_party_id": self.test_data['vendor_id'],
            "description": "Advance gold settlement test",
            "weight_grams": 100.000,
            "entered_purity": 916,
            "rate_per_gram": 20.00,
            "amount_total": 2000.00,
            "paid_amount_money": 0.00,
            "advance_in_gold_grams": 50.125
        }
        
        success, purchase = self.run_test(
            "Create Purchase for Advance Gold Test",
            "POST",
            "purchases",
            200,
            data=purchase_data
        )
        
        if not success:
            return False
        
        purchase_id = purchase['id']
        
        # Finalize the purchase
        success, finalized_response = self.run_test(
            "Finalize Purchase with Advance Gold",
            "POST",
            f"purchases/{purchase_id}/finalize",
            200
        )
        
        if not success:
            return False
        
        # Verify creates GoldLedgerEntry OUT and vendor payable
        if not finalized_response.get('advance_gold_ledger_id'):
            print(f"❌ Missing advance_gold_ledger_id")
            return False
        
        if not finalized_response.get('vendor_payable_transaction_id'):
            print(f"❌ Missing vendor_payable_transaction_id")
            return False
        
        if finalized_response.get('payment_transaction_id'):
            print(f"❌ Should not have payment_transaction_id (no payment)")
            return False
        
        if finalized_response.get('balance_due') != 2000.00:
            print(f"❌ Balance due should be full amount: expected 2000.00, got {finalized_response.get('balance_due')}")
            return False
        
        # Verify GoldLedgerEntry was created correctly
        success, gold_entries = self.run_test(
            "Get Gold Ledger Entries",
            "GET",
            "gold-ledger",
            200,
            params={"party_id": self.test_data['vendor_id']}
        )
        
        if not success:
            return False
        
        # Find the advance gold entry
        advance_entry = None
        for entry in gold_entries:
            if (entry.get('reference_id') == purchase_id and 
                entry.get('purpose') == 'advance_gold' and
                entry.get('type') == 'OUT'):
                advance_entry = entry
                break
        
        if not advance_entry:
            print(f"❌ Advance gold ledger entry not found")
            return False
        
        if advance_entry.get('weight_grams') != 50.125:
            print(f"❌ Advance gold weight mismatch: expected 50.125, got {advance_entry.get('weight_grams')}")
            return False
        
        print(f"✅ Advance gold settlement successful:")
        print(f"   Advance Gold Ledger ID: {finalized_response.get('advance_gold_ledger_id')}")
        print(f"   Gold Entry Type: {advance_entry.get('type')} (shop gives to vendor)")
        print(f"   Gold Weight: {advance_entry.get('weight_grams')}g")
        print(f"   Balance Due: {finalized_response.get('balance_due')}")
        
        return True

    def test_7_finalize_purchase_exchange_gold(self):
        """TEST 7: Finalize Purchase with Exchange Gold"""
        print("\n🔄 TEST 7: Finalize Purchase with Exchange Gold")
        
        # Create purchase with exchange gold
        purchase_data = {
            "vendor_party_id": self.test_data['vendor_id'],
            "description": "Exchange gold settlement test",
            "weight_grams": 90.000,
            "entered_purity": 916,
            "rate_per_gram": 20.00,
            "amount_total": 1800.00,
            "paid_amount_money": 0.00,
            "exchange_in_gold_grams": 35.750
        }
        
        success, purchase = self.run_test(
            "Create Purchase for Exchange Gold Test",
            "POST",
            "purchases",
            200,
            data=purchase_data
        )
        
        if not success:
            return False
        
        purchase_id = purchase['id']
        
        # Finalize the purchase
        success, finalized_response = self.run_test(
            "Finalize Purchase with Exchange Gold",
            "POST",
            f"purchases/{purchase_id}/finalize",
            200
        )
        
        if not success:
            return False
        
        # Verify creates GoldLedgerEntry IN
        if not finalized_response.get('exchange_gold_ledger_id'):
            print(f"❌ Missing exchange_gold_ledger_id")
            return False
        
        # Verify GoldLedgerEntry was created correctly
        success, gold_entries = self.run_test(
            "Get Gold Ledger Entries for Exchange",
            "GET",
            "gold-ledger",
            200,
            params={"party_id": self.test_data['vendor_id']}
        )
        
        if not success:
            return False
        
        # Find the exchange gold entry
        exchange_entry = None
        for entry in gold_entries:
            if (entry.get('reference_id') == purchase_id and 
                entry.get('purpose') == 'exchange' and
                entry.get('type') == 'IN'):
                exchange_entry = entry
                break
        
        if not exchange_entry:
            print(f"❌ Exchange gold ledger entry not found")
            return False
        
        if exchange_entry.get('weight_grams') != 35.750:
            print(f"❌ Exchange gold weight mismatch: expected 35.750, got {exchange_entry.get('weight_grams')}")
            return False
        
        print(f"✅ Exchange gold settlement successful:")
        print(f"   Exchange Gold Ledger ID: {finalized_response.get('exchange_gold_ledger_id')}")
        print(f"   Gold Entry Type: {exchange_entry.get('type')} (shop receives from vendor)")
        print(f"   Gold Weight: {exchange_entry.get('weight_grams')}g")
        
        return True

    def test_8_finalize_mixed_settlement(self):
        """TEST 8: Finalize with MIXED Settlement (Most Complex)"""
        print("\n🎯 TEST 8: Finalize with Mixed Settlement (Payment + Gold)")
        
        # Create purchase with mixed settlement
        purchase_data = {
            "vendor_party_id": self.test_data['vendor_id'],
            "description": "Mixed settlement test - payment + gold",
            "weight_grams": 250.000,
            "entered_purity": 916,
            "rate_per_gram": 20.00,
            "amount_total": 5000.00,
            "paid_amount_money": 2500.00,
            "payment_mode": "Card",
            "account_id": self.test_data['account_id'],
            "advance_in_gold_grams": 30.125,
            "exchange_in_gold_grams": 15.500
        }
        
        success, purchase = self.run_test(
            "Create Purchase for Mixed Settlement Test",
            "POST",
            "purchases",
            200,
            data=purchase_data
        )
        
        if not success:
            return False
        
        purchase_id = purchase['id']
        
        # Finalize the purchase
        success, finalized_response = self.run_test(
            "Finalize Purchase with Mixed Settlement",
            "POST",
            f"purchases/{purchase_id}/finalize",
            200
        )
        
        if not success:
            return False
        
        # Verify ALL IDs are present
        required_ids = [
            'stock_movement_id',
            'payment_transaction_id',
            'advance_gold_ledger_id',
            'exchange_gold_ledger_id',
            'vendor_payable_transaction_id'
        ]
        
        for id_field in required_ids:
            if not finalized_response.get(id_field):
                print(f"❌ Missing {id_field} in mixed settlement response")
                return False
        
        # Verify amounts
        if finalized_response.get('paid_amount') != 2500.00:
            print(f"❌ Paid amount mismatch: expected 2500.00, got {finalized_response.get('paid_amount')}")
            return False
        
        if finalized_response.get('balance_due') != 2500.00:
            print(f"❌ Balance due mismatch: expected 2500.00, got {finalized_response.get('balance_due')}")
            return False
        
        print(f"✅ Mixed settlement finalization successful:")
        print(f"   Stock Movement ID: {finalized_response.get('stock_movement_id')}")
        print(f"   Payment Transaction ID: {finalized_response.get('payment_transaction_id')}")
        print(f"   Advance Gold Ledger ID: {finalized_response.get('advance_gold_ledger_id')}")
        print(f"   Exchange Gold Ledger ID: {finalized_response.get('exchange_gold_ledger_id')}")
        print(f"   Vendor Payable Transaction ID: {finalized_response.get('vendor_payable_transaction_id')}")
        print(f"   Paid Amount: {finalized_response.get('paid_amount')}")
        print(f"   Balance Due: {finalized_response.get('balance_due')}")
        
        return True

    def test_9_precision_validation(self):
        """TEST 9: Precision Validation"""
        print("\n🔢 TEST 9: Precision Validation")
        
        # Create purchase with precise values
        purchase_data = {
            "vendor_party_id": self.test_data['vendor_id'],
            "description": "Precision validation test",
            "weight_grams": 123.456789,  # Should round to 123.457
            "entered_purity": 916,
            "rate_per_gram": 45.678901,  # Should round to 45.68
            "amount_total": 5643.210987,  # Should round to 5643.21
            "paid_amount_money": 2000.999,  # Should round to 2001.00
            "advance_in_gold_grams": 25.123456789,  # Should round to 25.123
            "exchange_in_gold_grams": 15.987654321  # Should round to 15.988
        }
        
        success, purchase = self.run_test(
            "Create Purchase for Precision Test",
            "POST",
            "purchases",
            200,
            data=purchase_data
        )
        
        if not success:
            return False
        
        # Verify gold values: exactly 3 decimals
        if purchase.get('weight_grams') != 123.457:
            print(f"❌ Weight precision error: expected 123.457, got {purchase.get('weight_grams')}")
            return False
        
        if purchase.get('advance_in_gold_grams') != 25.123:
            print(f"❌ Advance gold precision error: expected 25.123, got {purchase.get('advance_in_gold_grams')}")
            return False
        
        if purchase.get('exchange_in_gold_grams') != 15.988:
            print(f"❌ Exchange gold precision error: expected 15.988, got {purchase.get('exchange_in_gold_grams')}")
            return False
        
        # Verify money values: exactly 2 decimals
        if purchase.get('rate_per_gram') != 45.68:
            print(f"❌ Rate precision error: expected 45.68, got {purchase.get('rate_per_gram')}")
            return False
        
        if purchase.get('amount_total') != 5643.21:
            print(f"❌ Amount precision error: expected 5643.21, got {purchase.get('amount_total')}")
            return False
        
        if purchase.get('paid_amount_money') != 2001.00:
            print(f"❌ Paid amount precision error: expected 2001.00, got {purchase.get('paid_amount_money')}")
            return False
        
        print(f"✅ All precision validations passed:")
        print(f"   Gold values (3 decimals): weight={purchase.get('weight_grams')}, advance={purchase.get('advance_in_gold_grams')}, exchange={purchase.get('exchange_in_gold_grams')}")
        print(f"   Money values (2 decimals): rate={purchase.get('rate_per_gram')}, amount={purchase.get('amount_total')}, paid={purchase.get('paid_amount_money')}")
        
        return True

    def test_10_account_validation(self):
        """TEST 10: Account Validation"""
        print("\n🏦 TEST 10: Account Validation")
        
        # Test 1: Payment without account_id (should fail)
        purchase_data_no_account = {
            "vendor_party_id": self.test_data['vendor_id'],
            "description": "Test purchase without account",
            "weight_grams": 50.000,
            "entered_purity": 916,
            "rate_per_gram": 20.00,
            "amount_total": 1000.00,
            "paid_amount_money": 500.00,
            "payment_mode": "Cash"
            # Missing account_id
        }
        
        success, error_response = self.run_test(
            "Create Purchase Without Account (Should Fail)",
            "POST",
            "purchases",
            400,  # Expecting 400 error
            data=purchase_data_no_account
        )
        
        if not success:
            print(f"❌ Expected 400 error for missing account_id")
            return False
        
        # Verify error message
        error_str = str(error_response).lower()
        if 'account_id' not in error_str or 'required' not in error_str:
            print(f"❌ Error message should mention account_id requirement")
            return False
        
        print(f"✅ Correctly rejected purchase without account_id")
        
        # Test 2: Invalid account_id (should fail)
        purchase_data_invalid_account = {
            "vendor_party_id": self.test_data['vendor_id'],
            "description": "Test purchase with invalid account",
            "weight_grams": 50.000,
            "entered_purity": 916,
            "rate_per_gram": 20.00,
            "amount_total": 1000.00,
            "paid_amount_money": 500.00,
            "payment_mode": "Cash",
            "account_id": "invalid-account-id-12345"
        }
        
        success, error_response = self.run_test(
            "Create Purchase with Invalid Account (Should Fail)",
            "POST",
            "purchases",
            404,  # Expecting 404 error
            data=purchase_data_invalid_account
        )
        
        if not success:
            print(f"❌ Expected 404 error for invalid account_id")
            return False
        
        # Verify error message
        error_str = str(error_response).lower()
        if 'account' not in error_str or 'not found' not in error_str:
            print(f"❌ Error message should mention account not found")
            return False
        
        print(f"✅ Correctly rejected purchase with invalid account_id")
        
        return True

    def run_all_tests(self):
        """Run all MODULE 4 tests"""
        print("🚀 STARTING MODULE 4/10 - Purchase Payments + Gold Settlement Options TESTING")
        print("=" * 80)
        
        # Setup
        if not self.setup_authentication():
            print("❌ Authentication setup failed")
            return False
        
        if not self.setup_test_data():
            print("❌ Test data setup failed")
            return False
        
        # Run all tests
        tests = [
            self.test_1_create_draft_purchase_with_payment_fields,
            self.test_2_create_draft_purchase_with_gold_settlement,
            self.test_3_edit_draft_purchase_balance_recalculation,
            self.test_4_finalize_purchase_full_payment,
            self.test_5_finalize_purchase_partial_payment,
            self.test_6_finalize_purchase_advance_gold_settlement,
            self.test_7_finalize_purchase_exchange_gold,
            self.test_8_finalize_mixed_settlement,
            self.test_9_precision_validation,
            self.test_10_account_validation
        ]
        
        passed_tests = 0
        for test in tests:
            try:
                if test():
                    passed_tests += 1
                else:
                    print(f"❌ Test {test.__name__} failed")
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {str(e)}")
        
        # Summary
        print("\n" + "=" * 80)
        print(f"📊 MODULE 4 TEST SUMMARY")
        print(f"Total Tests: {len(tests)}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {len(tests) - passed_tests}")
        print(f"Success Rate: {(passed_tests / len(tests)) * 100:.1f}%")
        
        if passed_tests == len(tests):
            print("🎉 ALL MODULE 4 TESTS PASSED!")
            return True
        else:
            print("⚠️ Some tests failed - see details above")
            return False

if __name__ == "__main__":
    tester = Module4PurchasePaymentTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
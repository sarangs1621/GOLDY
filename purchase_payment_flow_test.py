#!/usr/bin/env python3
"""
COMPREHENSIVE PURCHASE PAYMENT FLOW TESTING

TEST OBJECTIVE: Verify that Purchase payment lifecycle works correctly end-to-end

CRITICAL BUSINESS RULES TO VERIFY:
1. Purchase lifecycle: Draft → Partially Paid → Paid → Locked
2. Locking only happens when balance_due == 0
3. Edit allowed when locked = False
4. Add payment endpoint works correctly

TEST SCENARIOS:
1. Create Draft Purchase (Unpaid)
2. Create Partially Paid Purchase
3. Add Payment to Draft Purchase
4. Complete Payment - Auto Lock
5. Edit Unlocked Purchase
6. Block Edit on Locked Purchase
7. Block Add Payment to Locked Purchase
"""

import requests
import json
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal

class PurchasePaymentFlowTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.csrf_token = None
        self.test_data = {}
        self.test_results = []
        
        # Get backend URL from environment
        try:
            with open('/app/frontend/.env', 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        backend_url = line.split('=', 1)[1].strip()
                        self.base_url = f"{backend_url}/api"
                        break
                else:
                    self.base_url = "https://payment-flow-repair-5.preview.emergentagent.com/api"
        except:
            self.base_url = "https://payment-flow-repair-5.preview.emergentagent.com/api"
        
        self.session.headers.update({"Content-Type": "application/json"})
        
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
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            response = self.session.post(f"{self.base_url}/auth/login", json=login_data)
            
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

    def setup_test_data(self):
        """Create test data: vendor party and account"""
        try:
            # Create vendor party with unique data
            timestamp = int(time.time())
            vendor_data = {
                "name": f"Test Gold Vendor {timestamp}",
                "phone": f"+968-{timestamp % 10000:04d}-{timestamp % 10000:04d}",
                "address": f"{timestamp} Gold Street, Muscat",
                "party_type": "vendor",
                "notes": "Test vendor for purchase payment flow testing"
            }
            response = self.session.post(f"{self.base_url}/parties", json=vendor_data)
            if response.status_code in [200, 201]:
                self.test_data["vendor"] = response.json()
                self.log_result("Setup - Vendor Party", True, f"Created vendor: {self.test_data['vendor']['name']}")
            else:
                self.log_result("Setup - Vendor Party", False, "", f"Failed to create vendor: {response.status_code} - {response.text}")
                return False

            # Create cash account for payments with unique name
            account_data = {
                "name": f"Test Cash Account {timestamp}",
                "account_type": "asset",
                "opening_balance": 50000.0
            }
            response = self.session.post(f"{self.base_url}/accounts", json=account_data)
            if response.status_code == 201:
                self.test_data["account"] = response.json()
                self.log_result("Setup - Cash Account", True, f"Created account: {self.test_data['account']['name']}")
            else:
                self.log_result("Setup - Cash Account", False, "", f"Failed to create account: {response.status_code} - {response.text}")
                return False

            return True
            
        except Exception as e:
            self.log_result("Setup Test Data", False, "", f"Setup error: {str(e)}")
            return False

    def test_scenario_1_draft_purchase(self):
        """SCENARIO 1: Create Draft Purchase (Unpaid)"""
        print("=" * 80)
        print("SCENARIO 1: Create Draft Purchase (Unpaid)")
        print("=" * 80)
        
        try:
            purchase_data = {
                "vendor_party_id": self.test_data["vendor"]["id"],
                "date": "2024-01-15",
                "description": "Gold Purchase - 100.5g at 916 purity",
                "weight_grams": 100.5,
                "entered_purity": 916,
                "rate_per_gram": 50.00,
                "amount_total": 5025.00,
                "paid_amount_money": 0.0,  # UNPAID
                "balance_due_money": 5025.00
            }
            
            response = self.session.post(f"{self.base_url}/purchases", json=purchase_data)
            
            if response.status_code == 201:
                purchase = response.json()
                self.test_data["draft_purchase"] = purchase
                
                # Verify response
                expected_status = "Draft"
                expected_locked = False
                expected_balance = 5025.00
                
                actual_status = purchase.get("status")
                actual_locked = purchase.get("locked", True)  # Default to True to catch failures
                actual_balance = purchase.get("balance_due_money", 0)
                
                if (actual_status == expected_status and 
                    actual_locked == expected_locked and 
                    abs(actual_balance - expected_balance) < 0.01):
                    
                    self.log_result("SCENARIO 1 - Draft Purchase Creation", True, 
                                  f"✅ Status: {actual_status}, Locked: {actual_locked}, Balance: {actual_balance} OMR")
                else:
                    self.log_result("SCENARIO 1 - Draft Purchase Creation", False, "", 
                                  f"❌ Expected: Status='{expected_status}', Locked={expected_locked}, Balance={expected_balance} OMR. "
                                  f"Got: Status='{actual_status}', Locked={actual_locked}, Balance={actual_balance} OMR")
            else:
                self.log_result("SCENARIO 1 - Draft Purchase Creation", False, "", 
                              f"Failed to create draft purchase: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("SCENARIO 1 - Draft Purchase Creation", False, "", f"Error: {str(e)}")

    def test_scenario_2_partially_paid_purchase(self):
        """SCENARIO 2: Create Partially Paid Purchase"""
        print("=" * 80)
        print("SCENARIO 2: Create Partially Paid Purchase")
        print("=" * 80)
        
        try:
            purchase_data = {
                "vendor_party_id": self.test_data["vendor"]["id"],
                "date": "2024-01-15",
                "description": "Gold Purchase - 80g at 916 purity",
                "weight_grams": 80.0,
                "entered_purity": 916,
                "rate_per_gram": 55.00,
                "amount_total": 4400.00,
                "paid_amount_money": 2200.00,  # 50% paid
                "balance_due_money": 2200.00,
                "payment_mode": "Cash",
                "account_id": self.test_data["account"]["id"]
            }
            
            response = self.session.post(f"{self.base_url}/purchases", json=purchase_data)
            
            if response.status_code == 201:
                purchase = response.json()
                self.test_data["partial_purchase"] = purchase
                
                # Verify response
                expected_status = "Partially Paid"
                expected_locked = False
                expected_balance = 2200.00
                
                actual_status = purchase.get("status")
                actual_locked = purchase.get("locked", True)
                actual_balance = purchase.get("balance_due_money", 0)
                
                if (actual_status == expected_status and 
                    actual_locked == expected_locked and 
                    abs(actual_balance - expected_balance) < 0.01):
                    
                    self.log_result("SCENARIO 2 - Partially Paid Purchase", True, 
                                  f"✅ Status: {actual_status}, Locked: {actual_locked}, Balance: {actual_balance} OMR")
                else:
                    self.log_result("SCENARIO 2 - Partially Paid Purchase", False, "", 
                                  f"❌ Expected: Status='{expected_status}', Locked={expected_locked}, Balance={expected_balance} OMR. "
                                  f"Got: Status='{actual_status}', Locked={actual_locked}, Balance={actual_balance} OMR")
            else:
                self.log_result("SCENARIO 2 - Partially Paid Purchase", False, "", 
                              f"Failed to create partially paid purchase: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("SCENARIO 2 - Partially Paid Purchase", False, "", f"Error: {str(e)}")

    def test_scenario_3_add_payment_to_draft(self):
        """SCENARIO 3: Add Payment to Draft Purchase"""
        print("=" * 80)
        print("SCENARIO 3: Add Payment to Draft Purchase")
        print("=" * 80)
        
        if "draft_purchase" not in self.test_data:
            self.log_result("SCENARIO 3 - Add Payment to Draft", False, "", "Draft purchase not available from Scenario 1")
            return
        
        try:
            purchase_id = self.test_data["draft_purchase"]["id"]
            payment_data = {
                "payment_amount": 2512.50,  # 50% of 5025.00
                "payment_mode": "Cash",
                "account_id": self.test_data["account"]["id"],
                "notes": "Partial payment on draft purchase"
            }
            
            response = self.session.post(f"{self.base_url}/purchases/{purchase_id}/add-payment", json=payment_data)
            
            if response.status_code == 200:
                updated_purchase = response.json()
                
                # Verify response
                expected_status = "Partially Paid"
                expected_locked = False
                expected_balance = 2512.50  # 5025.00 - 2512.50
                
                actual_status = updated_purchase.get("status")
                actual_locked = updated_purchase.get("locked", True)
                actual_balance = updated_purchase.get("balance_due_money", 0)
                transaction_number = updated_purchase.get("transaction_number")
                
                if (actual_status == expected_status and 
                    actual_locked == expected_locked and 
                    abs(actual_balance - expected_balance) < 0.01 and
                    transaction_number):
                    
                    self.log_result("SCENARIO 3 - Add Payment to Draft", True, 
                                  f"✅ Status: {actual_status}, Locked: {actual_locked}, Balance: {actual_balance} OMR, Transaction: {transaction_number}")
                    
                    # Store updated purchase for next test
                    self.test_data["draft_purchase"] = updated_purchase
                else:
                    self.log_result("SCENARIO 3 - Add Payment to Draft", False, "", 
                                  f"❌ Expected: Status='{expected_status}', Locked={expected_locked}, Balance={expected_balance} OMR. "
                                  f"Got: Status='{actual_status}', Locked={actual_locked}, Balance={actual_balance} OMR, Transaction: {transaction_number}")
            else:
                self.log_result("SCENARIO 3 - Add Payment to Draft", False, "", 
                              f"Failed to add payment: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("SCENARIO 3 - Add Payment to Draft", False, "", f"Error: {str(e)}")

    def test_scenario_4_complete_payment_auto_lock(self):
        """SCENARIO 4: Complete Payment - Auto Lock"""
        print("=" * 80)
        print("SCENARIO 4: Complete Payment - Auto Lock")
        print("=" * 80)
        
        if "draft_purchase" not in self.test_data:
            self.log_result("SCENARIO 4 - Complete Payment Auto Lock", False, "", "Partially paid purchase not available from Scenario 3")
            return
        
        try:
            purchase_id = self.test_data["draft_purchase"]["id"]
            remaining_balance = self.test_data["draft_purchase"]["balance_due_money"]
            
            payment_data = {
                "payment_amount": remaining_balance,  # Pay remaining balance
                "payment_mode": "Cash",
                "account_id": self.test_data["account"]["id"],
                "notes": "Final payment to complete purchase"
            }
            
            response = self.session.post(f"{self.base_url}/purchases/{purchase_id}/add-payment", json=payment_data)
            
            if response.status_code == 200:
                updated_purchase = response.json()
                
                # Verify response
                expected_status = "Paid"
                expected_locked = True  # Should auto-lock when balance_due = 0
                expected_balance = 0.0
                
                actual_status = updated_purchase.get("status")
                actual_locked = updated_purchase.get("locked", False)
                actual_balance = updated_purchase.get("balance_due_money", 999)
                locked_at = updated_purchase.get("locked_at")
                
                if (actual_status == expected_status and 
                    actual_locked == expected_locked and 
                    abs(actual_balance - expected_balance) < 0.01 and
                    locked_at):
                    
                    self.log_result("SCENARIO 4 - Complete Payment Auto Lock", True, 
                                  f"✅ Status: {actual_status}, Locked: {actual_locked}, Balance: {actual_balance} OMR, Locked At: {locked_at}")
                    
                    # Store locked purchase for next tests
                    self.test_data["locked_purchase"] = updated_purchase
                else:
                    self.log_result("SCENARIO 4 - Complete Payment Auto Lock", False, "", 
                                  f"❌ Expected: Status='{expected_status}', Locked={expected_locked}, Balance={expected_balance} OMR. "
                                  f"Got: Status='{actual_status}', Locked={actual_locked}, Balance={actual_balance} OMR, Locked At: {locked_at}")
            else:
                self.log_result("SCENARIO 4 - Complete Payment Auto Lock", False, "", 
                              f"Failed to complete payment: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("SCENARIO 4 - Complete Payment Auto Lock", False, "", f"Error: {str(e)}")

    def test_scenario_5_edit_unlocked_purchase(self):
        """SCENARIO 5: Edit Unlocked Purchase"""
        print("=" * 80)
        print("SCENARIO 5: Edit Unlocked Purchase")
        print("=" * 80)
        
        if "partial_purchase" not in self.test_data:
            self.log_result("SCENARIO 5 - Edit Unlocked Purchase", False, "", "Unlocked purchase not available from Scenario 2")
            return
        
        try:
            purchase_id = self.test_data["partial_purchase"]["id"]
            update_data = {
                "description": "Updated Gold Purchase - 80g at 916 purity (EDITED)"
            }
            
            response = self.session.patch(f"{self.base_url}/purchases/{purchase_id}", json=update_data)
            
            if response.status_code == 200:
                updated_purchase = response.json()
                
                # Verify the description was updated
                actual_description = updated_purchase.get("description", "")
                expected_text = "(EDITED)"
                
                if expected_text in actual_description:
                    self.log_result("SCENARIO 5 - Edit Unlocked Purchase", True, 
                                  f"✅ Successfully edited unlocked purchase. New description: {actual_description}")
                else:
                    self.log_result("SCENARIO 5 - Edit Unlocked Purchase", False, "", 
                                  f"❌ Description not updated correctly. Got: {actual_description}")
            else:
                self.log_result("SCENARIO 5 - Edit Unlocked Purchase", False, "", 
                              f"Failed to edit unlocked purchase: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("SCENARIO 5 - Edit Unlocked Purchase", False, "", f"Error: {str(e)}")

    def test_scenario_6_block_edit_locked_purchase(self):
        """SCENARIO 6: Block Edit on Locked Purchase"""
        print("=" * 80)
        print("SCENARIO 6: Block Edit on Locked Purchase")
        print("=" * 80)
        
        if "locked_purchase" not in self.test_data:
            self.log_result("SCENARIO 6 - Block Edit Locked Purchase", False, "", "Locked purchase not available from Scenario 4")
            return
        
        try:
            purchase_id = self.test_data["locked_purchase"]["id"]
            update_data = {
                "description": "This edit should be blocked"
            }
            
            response = self.session.patch(f"{self.base_url}/purchases/{purchase_id}", json=update_data)
            
            if response.status_code == 400:
                error_message = response.text.lower()
                if "locked" in error_message:
                    self.log_result("SCENARIO 6 - Block Edit Locked Purchase", True, 
                                  f"✅ Correctly blocked edit on locked purchase. Error: {response.text}")
                else:
                    self.log_result("SCENARIO 6 - Block Edit Locked Purchase", False, "", 
                                  f"❌ Got 400 error but wrong message. Expected 'locked' in error. Got: {response.text}")
            else:
                self.log_result("SCENARIO 6 - Block Edit Locked Purchase", False, "", 
                              f"❌ Should have blocked edit with HTTP 400 but got: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("SCENARIO 6 - Block Edit Locked Purchase", False, "", f"Error: {str(e)}")

    def test_scenario_7_block_payment_locked_purchase(self):
        """SCENARIO 7: Block Add Payment to Locked Purchase"""
        print("=" * 80)
        print("SCENARIO 7: Block Add Payment to Locked Purchase")
        print("=" * 80)
        
        if "locked_purchase" not in self.test_data:
            self.log_result("SCENARIO 7 - Block Payment Locked Purchase", False, "", "Locked purchase not available from Scenario 4")
            return
        
        try:
            purchase_id = self.test_data["locked_purchase"]["id"]
            payment_data = {
                "payment_amount": 100.00,
                "payment_mode": "Cash",
                "account_id": self.test_data["account"]["id"],
                "notes": "This payment should be blocked"
            }
            
            response = self.session.post(f"{self.base_url}/purchases/{purchase_id}/add-payment", json=payment_data)
            
            if response.status_code == 400:
                error_message = response.text.lower()
                if "locked" in error_message:
                    self.log_result("SCENARIO 7 - Block Payment Locked Purchase", True, 
                                  f"✅ Correctly blocked payment on locked purchase. Error: {response.text}")
                else:
                    self.log_result("SCENARIO 7 - Block Payment Locked Purchase", False, "", 
                                  f"❌ Got 400 error but wrong message. Expected 'locked' in error. Got: {response.text}")
            else:
                self.log_result("SCENARIO 7 - Block Payment Locked Purchase", False, "", 
                              f"❌ Should have blocked payment with HTTP 400 but got: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("SCENARIO 7 - Block Payment Locked Purchase", False, "", f"Error: {str(e)}")

    def test_error_cases(self):
        """Test error cases"""
        print("=" * 80)
        print("ERROR CASES TESTING")
        print("=" * 80)
        
        # Test: Pay more than balance_due
        if "partial_purchase" in self.test_data:
            try:
                purchase_id = self.test_data["partial_purchase"]["id"]
                balance_due = self.test_data["partial_purchase"]["balance_due_money"]
                
                payment_data = {
                    "payment_amount": balance_due + 1000.00,  # Overpayment
                    "payment_mode": "Cash",
                    "account_id": self.test_data["account"]["id"],
                    "notes": "Overpayment test"
                }
                
                response = self.session.post(f"{self.base_url}/purchases/{purchase_id}/add-payment", json=payment_data)
                
                if response.status_code == 400:
                    self.log_result("Error Case - Overpayment", True, 
                                  f"✅ Correctly blocked overpayment. Error: {response.text}")
                else:
                    self.log_result("Error Case - Overpayment", False, "", 
                                  f"❌ Should have blocked overpayment but got: {response.status_code} - {response.text}")
            except Exception as e:
                self.log_result("Error Case - Overpayment", False, "", f"Error: {str(e)}")
        
        # Test: Add payment without account_id
        if "partial_purchase" in self.test_data:
            try:
                purchase_id = self.test_data["partial_purchase"]["id"]
                
                payment_data = {
                    "payment_amount": 100.00,
                    "payment_mode": "Cash",
                    # Missing account_id
                    "notes": "Missing account test"
                }
                
                response = self.session.post(f"{self.base_url}/purchases/{purchase_id}/add-payment", json=payment_data)
                
                if response.status_code == 400:
                    self.log_result("Error Case - Missing Account", True, 
                                  f"✅ Correctly blocked payment without account. Error: {response.text}")
                else:
                    self.log_result("Error Case - Missing Account", False, "", 
                                  f"❌ Should have blocked payment without account but got: {response.status_code} - {response.text}")
            except Exception as e:
                self.log_result("Error Case - Missing Account", False, "", f"Error: {str(e)}")
        
        # Test: Invalid purchase_id
        try:
            invalid_id = str(uuid.uuid4())
            payment_data = {
                "payment_amount": 100.00,
                "payment_mode": "Cash",
                "account_id": self.test_data["account"]["id"],
                "notes": "Invalid purchase ID test"
            }
            
            response = self.session.post(f"{self.base_url}/purchases/{invalid_id}/add-payment", json=payment_data)
            
            if response.status_code == 404:
                self.log_result("Error Case - Invalid Purchase ID", True, 
                              f"✅ Correctly returned 404 for invalid purchase ID")
            else:
                self.log_result("Error Case - Invalid Purchase ID", False, "", 
                              f"❌ Should have returned 404 but got: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_result("Error Case - Invalid Purchase ID", False, "", f"Error: {str(e)}")

    def run_comprehensive_test(self):
        """Run all test scenarios"""
        print("🚀 STARTING COMPREHENSIVE PURCHASE PAYMENT FLOW TESTING")
        print("=" * 80)
        
        # Authenticate
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with testing.")
            return False
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Test data setup failed. Cannot proceed with testing.")
            return False
        
        # Run all scenarios
        self.test_scenario_1_draft_purchase()
        self.test_scenario_2_partially_paid_purchase()
        self.test_scenario_3_add_payment_to_draft()
        self.test_scenario_4_complete_payment_auto_lock()
        self.test_scenario_5_edit_unlocked_purchase()
        self.test_scenario_6_block_edit_locked_purchase()
        self.test_scenario_7_block_payment_locked_purchase()
        self.test_error_cases()
        
        # Print summary
        self.print_summary()
        
        return True

    def print_summary(self):
        """Print test results summary"""
        print("=" * 80)
        print("🎯 COMPREHENSIVE PURCHASE PAYMENT FLOW TESTING SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "No tests run")
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
        print("🏁 TESTING COMPLETE")
        print("=" * 80)

if __name__ == "__main__":
    tester = PurchasePaymentFlowTester()
    tester.run_comprehensive_test()
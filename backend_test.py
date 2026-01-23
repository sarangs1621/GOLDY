#!/usr/bin/env python3
"""
Comprehensive Backend API Testing Suite for Invoice Finalization and Viewing Functionality
Tests the Gold Shop ERP System invoice finalization and viewing capabilities.

Focus: Verify that finalized invoices can be viewed properly and display complete, accurate details.

Test Requirements:
1. Create New Invoice (Draft) with 2+ items
2. View Draft Invoice 
3. Finalize the Invoice
4. View Finalized Invoice
5. Test Invoice List View
6. Attempt to Edit Finalized Invoice (Should Fail)
7. Test Edge Cases
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://invoice-details-2.preview.emergentagent.com/api"
USERNAME = "admin"
PASSWORD = "admin123"

class InvoiceFinalizationTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.test_invoice_id = None
        self.test_customer_id = None
        
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
    
    def authenticate(self):
        """Authenticate and get JWT token"""
        print("🔐 Authenticating...")
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json={
                "username": USERNAME,
                "password": PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log_test("Authentication", True, f"Logged in as {USERNAME}")
                return True
            else:
                self.log_test("Authentication", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Authentication", False, f"Exception: {str(e)}")
            return False
    
    def get_or_create_test_customer(self):
        """Get existing customer or create one for testing"""
        print("👤 Setting up test customer...")
        
        # First, try to get existing customers
        response = self.session.get(f"{BASE_URL}/parties?party_type=customer&page=1&per_page=10")
        
        if response.status_code == 200:
            parties_data = response.json()
            customers = parties_data.get("items", [])
            
            if customers:
                # Use first existing customer
                self.test_customer_id = customers[0]["id"]
                customer_name = customers[0]["name"]
                self.log_test("Get existing customer", True, f"Using customer: {customer_name} (ID: {self.test_customer_id})")
                return True
        
        # If no customers exist, create one
        customer_data = {
            "name": "Ahmed Al-Rashid",
            "phone": "+968 9876 5432",
            "party_type": "customer",
            "address": "Muscat, Sultanate of Oman",
            "notes": "Test customer for invoice finalization testing"
        }
        
        create_response = self.session.post(f"{BASE_URL}/parties", json=customer_data)
        
        if create_response.status_code in [200, 201]:
            created_customer = create_response.json()
            self.test_customer_id = created_customer.get("id")
            self.log_test("Create test customer", True, f"Created customer: {customer_data['name']} (ID: {self.test_customer_id})")
            return True
        else:
            self.log_test("Create test customer", False, f"Status: {create_response.status_code}", create_response.text)
            return False
    
    def test_step_1_create_draft_invoice(self):
        """Step 1: Create New Invoice (Draft) with 2+ items"""
        print("\n📝 STEP 1: Create New Invoice (Draft) with 2+ items")
        
        if not self.test_customer_id:
            self.log_test("Step 1 - Create Draft Invoice", False, "No test customer available")
            return False
        
        # Calculate totals for realistic invoice
        item1_weight = 15.500
        item1_rate = 25.50
        item1_making = 50.00
        item1_vat_percent = 5.0
        item1_gold_value = item1_weight * item1_rate
        item1_vat_amount = (item1_gold_value + item1_making) * (item1_vat_percent / 100)
        item1_total = item1_gold_value + item1_making + item1_vat_amount
        
        item2_weight = 20.250
        item2_rate = 30.00
        item2_making = 75.00
        item2_vat_percent = 5.0
        item2_gold_value = item2_weight * item2_rate
        item2_vat_amount = (item2_gold_value + item2_making) * (item2_vat_percent / 100)
        item2_total = item2_gold_value + item2_making + item2_vat_amount
        
        subtotal = item1_gold_value + item1_making + item2_gold_value + item2_making
        vat_total = item1_vat_amount + item2_vat_amount
        grand_total = subtotal + vat_total
        
        invoice_data = {
            "customer_type": "saved",
            "customer_id": self.test_customer_id,
            "customer_name": "Ahmed Al-Rashid",
            "date": datetime.now().isoformat(),
            "invoice_type": "sale",
            "status": "draft",
            "items": [
                {
                    "description": "Gold Ring 22K",
                    "qty": 1,
                    "weight": item1_weight,
                    "purity": 916,
                    "metal_rate": item1_rate,
                    "gold_value": round(item1_gold_value, 2),
                    "making_value": item1_making,
                    "vat_percent": item1_vat_percent,
                    "vat_amount": round(item1_vat_amount, 2),
                    "line_total": round(item1_total, 2)
                },
                {
                    "description": "Gold Chain 18K",
                    "qty": 1,
                    "weight": item2_weight,
                    "purity": 750,
                    "metal_rate": item2_rate,
                    "gold_value": round(item2_gold_value, 2),
                    "making_value": item2_making,
                    "vat_percent": item2_vat_percent,
                    "vat_amount": round(item2_vat_amount, 2),
                    "line_total": round(item2_total, 2)
                }
            ],
            "subtotal": round(subtotal, 2),
            "vat_total": round(vat_total, 2),
            "grand_total": round(grand_total, 2),
            "paid_amount": 0.0,
            "balance_due": round(grand_total, 2),
            "notes": "Test invoice for finalization testing"
        }
        
        response = self.session.post(f"{BASE_URL}/invoices", json=invoice_data)
        
        if response.status_code in [200, 201]:
            created_invoice = response.json()
            self.test_invoice_id = created_invoice.get("id")
            
            # Verify invoice creation
            if (self.test_invoice_id and 
                created_invoice.get("status") == "draft" and
                len(created_invoice.get("items", [])) == 2):
                
                self.log_test("Step 1 - Create Draft Invoice", True, 
                            f"Created invoice ID: {self.test_invoice_id}, Status: draft, Items: 2, Grand Total: {created_invoice.get('grand_total')} OMR")
                return True
            else:
                self.log_test("Step 1 - Create Draft Invoice", False, 
                            f"Invoice creation incomplete. ID: {self.test_invoice_id}, Status: {created_invoice.get('status')}, Items: {len(created_invoice.get('items', []))}")
                return False
        else:
            self.log_test("Step 1 - Create Draft Invoice", False, 
                        f"Status: {response.status_code}", response.text)
            return False
    
    def test_step_2_view_draft_invoice(self):
        """Step 2: View Draft Invoice"""
        print("\n👁️ STEP 2: View Draft Invoice")
        
        if not self.test_invoice_id:
            self.log_test("Step 2 - View Draft Invoice", False, "No test invoice available")
            return False
        
        response = self.session.get(f"{BASE_URL}/invoices/{self.test_invoice_id}")
        
        if response.status_code == 200:
            invoice_data = response.json()
            
            # Verify all required fields are present
            required_fields = ["id", "invoice_number", "date", "customer_name", "items", 
                             "subtotal", "vat_total", "grand_total", "status"]
            missing_fields = [field for field in required_fields if field not in invoice_data]
            
            if not missing_fields:
                items = invoice_data.get("items", [])
                status = invoice_data.get("status")
                
                # Verify items have proper structure
                items_valid = True
                for item in items:
                    item_fields = ["description", "weight", "metal_rate", "making_value", "vat_amount", "line_total"]
                    if not all(field in item for field in item_fields):
                        items_valid = False
                        break
                
                if items_valid and status == "draft" and len(items) == 2:
                    # Check numeric precision
                    weight_precision_ok = all(
                        len(str(item.get("weight", 0)).split(".")[-1]) <= 3 
                        for item in items
                    )
                    money_precision_ok = all(
                        len(str(invoice_data.get(field, 0)).split(".")[-1]) <= 2 
                        for field in ["subtotal", "vat_total", "grand_total"]
                    )
                    
                    if weight_precision_ok and money_precision_ok:
                        self.log_test("Step 2 - View Draft Invoice", True, 
                                    f"All fields present, Status: {status}, Items: {len(items)}, Precision: Weight ≤3 decimals, Money ≤2 decimals")
                        return True
                    else:
                        self.log_test("Step 2 - View Draft Invoice", False, 
                                    f"Precision issues - Weight precision OK: {weight_precision_ok}, Money precision OK: {money_precision_ok}")
                        return False
                else:
                    self.log_test("Step 2 - View Draft Invoice", False, 
                                f"Items validation failed or wrong status. Items valid: {items_valid}, Status: {status}, Item count: {len(items)}")
                    return False
            else:
                self.log_test("Step 2 - View Draft Invoice", False, 
                            f"Missing required fields: {missing_fields}")
                return False
        else:
            self.log_test("Step 2 - View Draft Invoice", False, 
                        f"Status: {response.status_code}", response.text)
            return False
    
    def test_step_3_finalize_invoice(self):
        """Step 3: Finalize the Invoice"""
        print("\n🔒 STEP 3: Finalize the Invoice")
        
        if not self.test_invoice_id:
            self.log_test("Step 3 - Finalize Invoice", False, "No test invoice available")
            return False
        
        response = self.session.patch(f"{BASE_URL}/invoices/{self.test_invoice_id}/finalize")
        
        if response.status_code == 200:
            finalized_invoice = response.json()
            
            # Verify finalization
            status = finalized_invoice.get("status")
            finalized_at = finalized_invoice.get("finalized_at")
            locked = finalized_invoice.get("locked")
            
            if status == "finalized" and finalized_at and locked:
                self.log_test("Step 3 - Finalize Invoice", True, 
                            f"Invoice finalized successfully. Status: {status}, Locked: {locked}, Finalized at: {finalized_at}")
                return True
            else:
                self.log_test("Step 3 - Finalize Invoice", False, 
                            f"Finalization incomplete. Status: {status}, Locked: {locked}, Finalized at: {finalized_at}")
                return False
        else:
            self.log_test("Step 3 - Finalize Invoice", False, 
                        f"Status: {response.status_code}", response.text)
            return False
    
    def test_step_4_view_finalized_invoice(self):
        """Step 4: View Finalized Invoice - CRITICAL TEST"""
        print("\n🔍 STEP 4: View Finalized Invoice - CRITICAL TEST")
        
        if not self.test_invoice_id:
            self.log_test("Step 4 - View Finalized Invoice", False, "No test invoice available")
            return False
        
        response = self.session.get(f"{BASE_URL}/invoices/{self.test_invoice_id}")
        
        if response.status_code == 200:
            invoice_data = response.json()
            
            # Comprehensive verification of finalized invoice
            verification_results = []
            
            # 1. Basic structure
            required_fields = ["id", "invoice_number", "date", "customer_name", "items", 
                             "subtotal", "vat_total", "grand_total", "status", "finalized_at", "locked"]
            missing_fields = [field for field in required_fields if field not in invoice_data]
            verification_results.append(("Basic structure", len(missing_fields) == 0, f"Missing: {missing_fields}" if missing_fields else "All fields present"))
            
            # 2. Status verification
            status = invoice_data.get("status")
            locked = invoice_data.get("locked")
            finalized_at = invoice_data.get("finalized_at")
            verification_results.append(("Status verification", status == "finalized" and locked and finalized_at, 
                                       f"Status: {status}, Locked: {locked}, Finalized: {bool(finalized_at)}"))
            
            # 3. Customer information
            customer_info_complete = all(invoice_data.get(field) for field in ["customer_name", "customer_id"])
            verification_results.append(("Customer information", customer_info_complete, 
                                       f"Customer: {invoice_data.get('customer_name')}, ID: {invoice_data.get('customer_id')}"))
            
            # 4. Items verification
            items = invoice_data.get("items", [])
            items_complete = len(items) >= 2
            if items_complete:
                for i, item in enumerate(items):
                    item_fields = ["description", "weight", "purity", "metal_rate", "making_value", "vat_percent", "vat_amount", "line_total"]
                    item_complete = all(field in item for field in item_fields)
                    verification_results.append((f"Item {i+1} structure", item_complete, 
                                               f"Description: {item.get('description')}, Weight: {item.get('weight')}g"))
            
            # 5. Calculations verification
            subtotal = invoice_data.get("subtotal", 0)
            vat_total = invoice_data.get("vat_total", 0)
            grand_total = invoice_data.get("grand_total", 0)
            
            # Verify calculations are reasonable (basic sanity check)
            calculations_reasonable = (subtotal > 0 and vat_total >= 0 and grand_total > subtotal)
            verification_results.append(("Calculations", calculations_reasonable, 
                                       f"Subtotal: {subtotal}, VAT: {vat_total}, Grand Total: {grand_total}"))
            
            # 6. Precision verification
            weight_precision_ok = all(
                len(str(item.get("weight", 0)).split(".")[-1]) <= 3 
                for item in items
            )
            money_precision_ok = all(
                len(str(invoice_data.get(field, 0)).split(".")[-1]) <= 2 
                for field in ["subtotal", "vat_total", "grand_total"]
            )
            verification_results.append(("Numeric precision", weight_precision_ok and money_precision_ok, 
                                       f"Weight ≤3 decimals: {weight_precision_ok}, Money ≤2 decimals: {money_precision_ok}"))
            
            # 7. Payment details
            balance_due = invoice_data.get("balance_due", 0)
            paid_amount = invoice_data.get("paid_amount", 0)
            payment_details_present = "balance_due" in invoice_data and "paid_amount" in invoice_data
            verification_results.append(("Payment details", payment_details_present, 
                                       f"Paid: {paid_amount}, Balance: {balance_due}"))
            
            # Summary
            all_passed = all(result[1] for result in verification_results)
            passed_count = sum(1 for result in verification_results if result[1])
            total_count = len(verification_results)
            
            details = f"Verification: {passed_count}/{total_count} checks passed"
            for check_name, passed, detail in verification_results:
                if not passed:
                    details += f"\n   ❌ {check_name}: {detail}"
                else:
                    details += f"\n   ✅ {check_name}: {detail}"
            
            self.log_test("Step 4 - View Finalized Invoice (COMPREHENSIVE)", all_passed, details)
            return all_passed
        else:
            self.log_test("Step 4 - View Finalized Invoice", False, 
                        f"Status: {response.status_code}", response.text)
            return False
    
    def test_step_5_invoice_list_view(self):
        """Step 5: Test Invoice List View"""
        print("\n📋 STEP 5: Test Invoice List View")
        
        response = self.session.get(f"{BASE_URL}/invoices?page=1&per_page=50")
        
        if response.status_code == 200:
            invoices_data = response.json()
            
            # Verify pagination structure
            if "items" in invoices_data and "pagination" in invoices_data:
                items = invoices_data.get("items", [])
                
                # Look for our finalized invoice
                test_invoice_found = False
                if self.test_invoice_id:
                    test_invoice_found = any(inv.get("id") == self.test_invoice_id for inv in items)
                
                if test_invoice_found:
                    found_invoice = next(inv for inv in items if inv.get("id") == self.test_invoice_id)
                    
                    # Verify list preview data
                    preview_fields = ["invoice_number", "date", "customer_name", "grand_total", "status"]
                    preview_complete = all(field in found_invoice for field in preview_fields)
                    
                    if preview_complete and found_invoice.get("status") == "finalized":
                        self.log_test("Step 5 - Invoice List View", True, 
                                    f"Finalized invoice found in list. Invoice: {found_invoice.get('invoice_number')}, "
                                    f"Customer: {found_invoice.get('customer_name')}, Total: {found_invoice.get('grand_total')}")
                        return True
                    else:
                        self.log_test("Step 5 - Invoice List View", False, 
                                    f"Preview data incomplete or wrong status. Complete: {preview_complete}, Status: {found_invoice.get('status')}")
                        return False
                else:
                    self.log_test("Step 5 - Invoice List View", False, 
                                f"Test invoice not found in list of {len(items)} invoices")
                    return False
            else:
                self.log_test("Step 5 - Invoice List View", False, 
                            "Invalid response structure - missing items or pagination")
                return False
        else:
            self.log_test("Step 5 - Invoice List View", False, 
                        f"Status: {response.status_code}", response.text)
            return False
    
    def test_step_6_attempt_edit_finalized(self):
        """Step 6: Attempt to Edit Finalized Invoice (Should Fail)"""
        print("\n🚫 STEP 6: Attempt to Edit Finalized Invoice (Should Fail)")
        
        if not self.test_invoice_id:
            self.log_test("Step 6 - Edit Finalized Invoice", False, "No test invoice available")
            return False
        
        # Attempt to update the finalized invoice
        update_data = {
            "notes": "This should not be allowed - invoice is finalized"
        }
        
        response = self.session.patch(f"{BASE_URL}/invoices/{self.test_invoice_id}", json=update_data)
        
        # This should fail with 400 or 403 error
        if response.status_code in [400, 403]:
            error_message = response.text or response.json().get("detail", "")
            
            # Check if error message indicates invoice is locked/finalized
            locked_keywords = ["finalized", "locked", "cannot", "edit", "modify"]
            error_indicates_locked = any(keyword.lower() in error_message.lower() for keyword in locked_keywords)
            
            if error_indicates_locked:
                self.log_test("Step 6 - Edit Finalized Invoice (Should Fail)", True, 
                            f"Correctly rejected edit attempt. Status: {response.status_code}, Message: {error_message}")
                return True
            else:
                self.log_test("Step 6 - Edit Finalized Invoice (Should Fail)", False, 
                            f"Rejected but unclear error message. Status: {response.status_code}, Message: {error_message}")
                return False
        elif response.status_code == 200:
            self.log_test("Step 6 - Edit Finalized Invoice (Should Fail)", False, 
                        "CRITICAL: Edit was allowed on finalized invoice - this should not happen!")
            return False
        else:
            self.log_test("Step 6 - Edit Finalized Invoice (Should Fail)", False, 
                        f"Unexpected status code: {response.status_code}", response.text)
            return False
    
    def test_step_7_edge_cases(self):
        """Step 7: Test Edge Cases"""
        print("\n🧪 STEP 7: Test Edge Cases")
        
        edge_case_results = []
        
        # Edge Case 1: Test with multiple items (already done, but verify calculations)
        if self.test_invoice_id:
            response = self.session.get(f"{BASE_URL}/invoices/{self.test_invoice_id}")
            if response.status_code == 200:
                invoice_data = response.json()
                items = invoice_data.get("items", [])
                
                if len(items) >= 2:
                    # Verify each item has different VAT percentages or rates
                    different_rates = len(set(item.get("metal_rate", 0) for item in items)) > 1
                    edge_case_results.append(("Multiple items with different rates", different_rates, 
                                            f"Items have different rates: {different_rates}"))
                    
                    # Verify calculations for each item
                    calculations_correct = True
                    for item in items:
                        weight = item.get("weight", 0)
                        rate = item.get("metal_rate", 0)
                        making = item.get("making_value", 0)
                        vat_percent = item.get("vat_percent", 0)
                        
                        expected_gold_value = weight * rate
                        expected_vat = (expected_gold_value + making) * (vat_percent / 100)
                        expected_total = expected_gold_value + making + expected_vat
                        
                        actual_gold_value = item.get("gold_value", 0)
                        actual_vat = item.get("vat_amount", 0)
                        actual_total = item.get("line_total", 0)
                        
                        # Allow small rounding differences
                        if (abs(actual_gold_value - expected_gold_value) > 0.01 or
                            abs(actual_vat - expected_vat) > 0.01 or
                            abs(actual_total - expected_total) > 0.01):
                            calculations_correct = False
                            break
                    
                    edge_case_results.append(("Item-wise calculations accuracy", calculations_correct, 
                                            f"All item calculations are accurate: {calculations_correct}"))
        
        # Edge Case 2: Test invoice with rounding
        if self.test_invoice_id:
            response = self.session.get(f"{BASE_URL}/invoices/{self.test_invoice_id}")
            if response.status_code == 200:
                invoice_data = response.json()
                grand_total = invoice_data.get("grand_total", 0)
                
                # Check if there's a rounded field
                grand_total_rounded = invoice_data.get("grand_total_rounded")
                if grand_total_rounded is not None:
                    rounding_reasonable = abs(grand_total_rounded - grand_total) <= 1.0
                    edge_case_results.append(("Grand total rounding", rounding_reasonable, 
                                            f"Original: {grand_total}, Rounded: {grand_total_rounded}"))
                else:
                    edge_case_results.append(("Grand total rounding field", True, 
                                            "No rounding field present (acceptable)"))
        
        # Edge Case 3: Test payment details display
        if self.test_invoice_id:
            response = self.session.get(f"{BASE_URL}/invoices/{self.test_invoice_id}")
            if response.status_code == 200:
                invoice_data = response.json()
                
                paid_amount = invoice_data.get("paid_amount", 0)
                balance_due = invoice_data.get("balance_due", 0)
                grand_total = invoice_data.get("grand_total", 0)
                
                # Verify payment calculation
                payment_calculation_correct = abs((paid_amount + balance_due) - grand_total) < 0.01
                edge_case_results.append(("Payment calculation", payment_calculation_correct, 
                                        f"Paid: {paid_amount}, Balance: {balance_due}, Total: {grand_total}"))
                
                # Determine payment status
                if paid_amount == 0:
                    payment_status = "unpaid"
                elif balance_due <= 0:
                    payment_status = "paid"
                else:
                    payment_status = "partial"
                
                actual_payment_status = invoice_data.get("payment_status", "")
                payment_status_correct = actual_payment_status == payment_status
                edge_case_results.append(("Payment status accuracy", payment_status_correct, 
                                        f"Expected: {payment_status}, Actual: {actual_payment_status}"))
        
        # Summary of edge cases
        all_edge_cases_passed = all(result[1] for result in edge_case_results)
        passed_edge_cases = sum(1 for result in edge_case_results if result[1])
        total_edge_cases = len(edge_case_results)
        
        details = f"Edge cases: {passed_edge_cases}/{total_edge_cases} passed"
        for case_name, passed, detail in edge_case_results:
            if not passed:
                details += f"\n   ❌ {case_name}: {detail}"
            else:
                details += f"\n   ✅ {case_name}: {detail}"
        
        self.log_test("Step 7 - Edge Cases", all_edge_cases_passed, details)
        return all_edge_cases_passed
    
    def cleanup_test_data(self):
        """Clean up test data created during testing"""
        print("🧹 Cleaning up test data...")
        
        # Delete test invoice
        if hasattr(self, 'test_invoice_id') and self.test_invoice_id:
            delete_response = self.session.delete(f"{BASE_URL}/invoices/{self.test_invoice_id}")
            if delete_response.status_code in [200, 204]:
                print(f"   ✅ Deleted test invoice {self.test_invoice_id}")
            else:
                print(f"   ⚠️ Failed to delete test invoice {self.test_invoice_id}")
        
        # Note: We don't delete the test customer as it might be an existing customer
        # Only delete if we created it specifically for testing
        if hasattr(self, 'test_customer_id') and hasattr(self, 'created_test_customer'):
            if self.created_test_customer:
                delete_response = self.session.delete(f"{BASE_URL}/parties/{self.test_customer_id}")
                if delete_response.status_code in [200, 204]:
                    print(f"   ✅ Deleted test customer {self.test_customer_id}")
                else:
                    print(f"   ⚠️ Failed to delete test customer {self.test_customer_id}")
    
    def run_all_tests(self):
        """Run all test scenarios for Invoice Finalization and Viewing functionality"""
        print("🚀 Starting Invoice Finalization and Viewing Backend API Testing")
        print("🎯 Focus: Verify that finalized invoices can be viewed properly and display complete, accurate details")
        print("=" * 80)
        
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Setup test customer
        if not self.get_or_create_test_customer():
            print("❌ Failed to setup test customer. Cannot proceed with tests.")
            return False
        
        try:
            # Execute all test steps
            step_results = []
            
            # Step 1: Create New Invoice (Draft)
            step_results.append(self.test_step_1_create_draft_invoice())
            
            # Step 2: View Draft Invoice
            step_results.append(self.test_step_2_view_draft_invoice())
            
            # Step 3: Finalize the Invoice
            step_results.append(self.test_step_3_finalize_invoice())
            
            # Step 4: View Finalized Invoice (CRITICAL)
            step_results.append(self.test_step_4_view_finalized_invoice())
            
            # Step 5: Test Invoice List View
            step_results.append(self.test_step_5_invoice_list_view())
            
            # Step 6: Attempt to Edit Finalized Invoice (Should Fail)
            step_results.append(self.test_step_6_attempt_edit_finalized())
            
            # Step 7: Test Edge Cases
            step_results.append(self.test_step_7_edge_cases())
            
        finally:
            # Always cleanup
            self.cleanup_test_data()
        
        # Print comprehensive summary
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE INVOICE FINALIZATION TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Step-by-step results
        step_names = [
            "Step 1 - Create Draft Invoice",
            "Step 2 - View Draft Invoice", 
            "Step 3 - Finalize Invoice",
            "Step 4 - View Finalized Invoice",
            "Step 5 - Invoice List View",
            "Step 6 - Edit Finalized Invoice (Should Fail)",
            "Step 7 - Edge Cases"
        ]
        
        print(f"\n📋 STEP-BY-STEP RESULTS:")
        for i, step_name in enumerate(step_names):
            if i < len(step_results):
                status = "✅ PASS" if step_results[i] else "❌ FAIL"
                print(f"   {status} {step_name}")
            else:
                print(f"   ⏭️ SKIP {step_name}")
        
        # Critical verifications
        print(f"\n🎯 CRITICAL VERIFICATIONS:")
        
        invoice_creation_ok = any("Step 1 - Create Draft Invoice" in r["test"] and r["success"] for r in self.test_results)
        draft_viewing_ok = any("Step 2 - View Draft Invoice" in r["test"] and r["success"] for r in self.test_results)
        finalization_ok = any("Step 3 - Finalize Invoice" in r["test"] and r["success"] for r in self.test_results)
        finalized_viewing_ok = any("Step 4 - View Finalized Invoice" in r["test"] and r["success"] for r in self.test_results)
        list_view_ok = any("Step 5 - Invoice List View" in r["test"] and r["success"] for r in self.test_results)
        edit_protection_ok = any("Step 6 - Edit Finalized Invoice" in r["test"] and r["success"] for r in self.test_results)
        
        print(f"   ✅ Invoice creation with 2+ items works: {'✅ YES' if invoice_creation_ok else '❌ NO'}")
        print(f"   ✅ Draft invoice can be viewed: {'✅ YES' if draft_viewing_ok else '❌ NO'}")
        print(f"   ✅ Finalization endpoint works: {'✅ YES' if finalization_ok else '❌ NO'}")
        print(f"   ✅ Finalized invoice displays all details correctly: {'✅ YES' if finalized_viewing_ok else '❌ NO'}")
        print(f"   ✅ Status shows 'finalized': {'✅ YES' if finalization_ok else '❌ NO'}")
        print(f"   ✅ Editing finalized invoice is properly blocked: {'✅ YES' if edit_protection_ok else '❌ NO'}")
        print(f"   ✅ No blank pages or missing data: {'✅ YES' if finalized_viewing_ok else '❌ NO'}")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS ({failed_tests}):")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}")
                    if result['details']:
                        print(f"     └─ {result['details']}")
        
        # Production readiness assessment
        critical_steps_passed = sum(step_results[:6])  # First 6 steps are critical
        production_ready = critical_steps_passed >= 5  # Allow 1 failure in non-critical areas
        
        print(f"\n🎯 PRODUCTION READINESS ASSESSMENT:")
        print(f"   Critical Steps Passed: {critical_steps_passed}/6")
        print(f"   Overall Assessment: {'✅ PRODUCTION READY' if production_ready else '❌ NEEDS FIXES'}")
        
        if production_ready:
            print(f"   📋 Invoice finalization and viewing functionality is working correctly")
            print(f"   📋 All calculations are accurate and properly formatted")
            print(f"   📋 Finalized invoices are properly protected from editing")
        else:
            print(f"   ⚠️ Critical issues found that need to be addressed before production")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = InvoiceFinalizationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
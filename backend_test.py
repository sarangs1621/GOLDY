#!/usr/bin/env python3
"""
Backend Testing Script for Invoice Workflow Critical Issues
Testing 4 specific issues identified in the review request:
1. Making Charges Calculation Bug in Job Card to Invoice Conversion
2. Invoice Field Naming Consistency
3. Stock OUT Movement Verification
4. Customer Outstanding Balance Calculation
"""

import requests
import json
import sys
from datetime import datetime
import uuid

# Configuration
BASE_URL = "https://charge-calc-fix.preview.emergentagent.com/api"
USERNAME = "admin"
PASSWORD = "admin123"

class InvoiceWorkflowTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        
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
    
    def get_test_customer(self):
        """Get a test customer for invoice creation"""
        try:
            response = self.session.get(f"{BASE_URL}/parties?party_type=customer&per_page=1")
            if response.status_code == 200:
                customers = response.json().get("items", [])
                if customers:
                    return customers[0]
            return None
        except Exception as e:
            print(f"Error getting test customer: {e}")
            return None
    
    def get_test_worker(self):
        """Get a test worker for job card creation"""
        try:
            response = self.session.get(f"{BASE_URL}/parties?party_type=worker&per_page=1")
            if response.status_code == 200:
                workers = response.json().get("items", [])
                if workers:
                    return workers[0]
            return None
        except Exception as e:
            print(f"Error getting test worker: {e}")
            return None
    
    def test_issue_1_making_charges_calculation(self):
        """
        HIGH PRIORITY ISSUE #1: Making Charges Calculation Bug in Job Card to Invoice Conversion
        Test that job card making charges (100 OMR flat) are properly transferred to invoice items
        """
        print("\n" + "="*80)
        print("TESTING ISSUE #1: Making Charges Calculation Bug")
        print("="*80)
        
        try:
            # Get test customer and worker
            customer = self.get_test_customer()
            worker = self.get_test_worker()
            
            if not customer or not worker:
                self.log_result("Issue #1 - Setup", "FAIL", "Could not find test customer or worker")
                return
            
            # Step 1: Create a job card with specific making charges
            jobcard_data = {
                "customer_type": "saved",
                "customer_id": customer["id"],
                "customer_name": customer["name"],
                "worker_id": worker["id"],
                "worker_name": worker["name"],
                "delivery_date": "2024-12-31",
                "notes": "Test job card for making charges verification",
                "gold_rate_at_jobcard": 25.0,
                "items": [
                    {
                        "category": "Ring",
                        "description": "Test Ring for Making Charges",
                        "qty": 1,
                        "weight_in": 10.0,
                        "weight_out": 10.0,
                        "purity": 916,
                        "work_type": "New Making",
                        "making_charge_type": "flat",
                        "making_charge_value": 100.0,  # 100 OMR flat charge
                        "vat_percent": 5.0,
                        "remarks": "Test item with 100 OMR flat making charge"
                    }
                ]
            }
            
            # Create job card
            response = self.session.post(f"{BASE_URL}/jobcards", json=jobcard_data)
            if response.status_code != 200:
                self.log_result("Issue #1 - Job Card Creation", "FAIL", f"Failed to create job card: {response.status_code} - {response.text}")
                return
            
            jobcard = response.json()
            jobcard_id = jobcard["id"]
            self.log_result("Issue #1 - Job Card Creation", "PASS", f"Created job card {jobcard_id} with 100 OMR flat making charge")
            
            # Step 2: Convert job card to invoice
            conversion_data = {
                "customer_type": "saved",
                "customer_id": customer["id"],
                "customer_name": customer["name"],
                "metal_rate": 25.0
            }
            
            response = self.session.post(f"{BASE_URL}/jobcards/{jobcard_id}/convert-to-invoice", json=conversion_data)
            if response.status_code != 200:
                self.log_result("Issue #1 - Job Card Conversion", "FAIL", f"Failed to convert job card: {response.status_code} - {response.text}")
                return
            
            invoice = response.json()
            invoice_id = invoice["id"]
            self.log_result("Issue #1 - Job Card Conversion", "PASS", f"Converted job card to invoice {invoice_id}")
            
            # Step 3: Verify making charge value in invoice
            if not invoice.get("items"):
                self.log_result("Issue #1 - Invoice Items", "FAIL", "Invoice has no items")
                return
            
            first_item = invoice["items"][0]
            making_value = first_item.get("making_value", 0)
            
            # The critical test: making_value should be 100.0, not 5.0
            if making_value == 100.0:
                self.log_result("Issue #1 - Making Charges Calculation", "PASS", f"Making charge correctly transferred: {making_value} OMR (expected 100.0)")
            elif making_value == 5.0:
                self.log_result("Issue #1 - Making Charges Calculation", "FAIL", f"BUG CONFIRMED: Making charge shows {making_value} OMR instead of expected 100.0 OMR")
            else:
                self.log_result("Issue #1 - Making Charges Calculation", "FAIL", f"Unexpected making charge value: {making_value} OMR (expected 100.0)")
            
            # Additional verification: Check if making_charge_value from job card is being used
            print(f"   Job Card Item Making Charge: {jobcard['items'][0].get('making_charge_value')} OMR ({jobcard['items'][0].get('making_charge_type')})")
            print(f"   Invoice Item Making Value: {making_value} OMR")
            
        except Exception as e:
            self.log_result("Issue #1 - Making Charges Calculation", "ERROR", f"Test error: {str(e)}")
    
    def test_issue_2_field_naming_consistency(self):
        """
        MEDIUM PRIORITY ISSUE #2: Invoice Field Naming Consistency
        Verify that invoice items use consistent field names (gold_value, making_value)
        """
        print("\n" + "="*80)
        print("TESTING ISSUE #2: Invoice Field Naming Consistency")
        print("="*80)
        
        try:
            # Get any existing invoice
            response = self.session.get(f"{BASE_URL}/invoices?per_page=1")
            if response.status_code != 200:
                self.log_result("Issue #2 - Get Invoice", "FAIL", f"Failed to get invoices: {response.status_code}")
                return
            
            invoices = response.json().get("items", [])
            if not invoices:
                self.log_result("Issue #2 - Get Invoice", "FAIL", "No invoices found for testing")
                return
            
            invoice = invoices[0]
            invoice_id = invoice["id"]
            
            # Get detailed invoice
            response = self.session.get(f"{BASE_URL}/invoices/{invoice_id}")
            if response.status_code != 200:
                self.log_result("Issue #2 - Get Invoice Details", "FAIL", f"Failed to get invoice details: {response.status_code}")
                return
            
            invoice_detail = response.json()
            items = invoice_detail.get("items", [])
            
            if not items:
                self.log_result("Issue #2 - Invoice Items", "FAIL", "Invoice has no items to check field names")
                return
            
            first_item = items[0]
            
            # Check for correct field names
            has_gold_value = "gold_value" in first_item
            has_making_value = "making_value" in first_item
            
            # Check for incorrect field names
            has_metal_value = "metal_value" in first_item
            has_making_charges = "making_charges" in first_item
            
            field_issues = []
            
            if not has_gold_value:
                field_issues.append("Missing 'gold_value' field")
            if not has_making_value:
                field_issues.append("Missing 'making_value' field")
            if has_metal_value:
                field_issues.append("Found incorrect 'metal_value' field (should be 'gold_value')")
            if has_making_charges:
                field_issues.append("Found incorrect 'making_charges' field (should be 'making_value')")
            
            if field_issues:
                self.log_result("Issue #2 - Field Naming Consistency", "FAIL", f"Field naming issues: {', '.join(field_issues)}")
            else:
                self.log_result("Issue #2 - Field Naming Consistency", "PASS", "All field names are consistent (gold_value, making_value)")
            
            # Log the actual field structure for verification
            print(f"   Invoice Item Fields: {list(first_item.keys())}")
            
        except Exception as e:
            self.log_result("Issue #2 - Field Naming Consistency", "ERROR", f"Test error: {str(e)}")
    
    def test_issue_3_stock_out_movements(self):
        """
        MEDIUM PRIORITY ISSUE #3: Stock OUT Movement Verification
        Confirm Stock OUT movements are created during invoice finalization
        """
        print("\n" + "="*80)
        print("TESTING ISSUE #3: Stock OUT Movement Verification")
        print("="*80)
        
        try:
            # Get test customer
            customer = self.get_test_customer()
            if not customer:
                self.log_result("Issue #3 - Setup", "FAIL", "Could not find test customer")
                return
            
            # Step 1: Create a draft invoice with inventory items
            invoice_data = {
                "customer_type": "saved",
                "customer_id": customer["id"],
                "customer_name": customer["name"],
                "invoice_date": datetime.now().strftime("%Y-%m-%d"),
                "notes": "Test invoice for stock movement verification",
                "items": [
                    {
                        "category": "Ring",  # Inventory category
                        "description": "Test Ring for Stock Movement",
                        "qty": 1,
                        "weight": 5.0,
                        "purity": 916,
                        "metal_rate": 25.0,
                        "gold_value": 125.0,
                        "making_value": 50.0,
                        "vat_percent": 5.0,
                        "vat_amount": 8.75,
                        "line_total": 183.75
                    }
                ],
                "subtotal": 175.0,
                "discount_percent": 0,
                "discount_amount": 0,
                "vat_amount": 8.75,
                "grand_total": 183.75,
                "paid_amount": 0,
                "balance_due": 183.75,
                "payment_status": "unpaid"
            }
            
            # Create invoice
            response = self.session.post(f"{BASE_URL}/invoices", json=invoice_data)
            if response.status_code != 200:
                self.log_result("Issue #3 - Invoice Creation", "FAIL", f"Failed to create invoice: {response.status_code} - {response.text}")
                return
            
            invoice = response.json()
            invoice_id = invoice["id"]
            self.log_result("Issue #3 - Invoice Creation", "PASS", f"Created draft invoice {invoice_id}")
            
            # Step 2: Get current inventory stock for Ring category
            response = self.session.get(f"{BASE_URL}/inventory/headers")
            if response.status_code != 200:
                self.log_result("Issue #3 - Get Inventory", "FAIL", f"Failed to get inventory: {response.status_code}")
                return
            
            headers = response.json()
            if isinstance(headers, dict) and "items" in headers:
                headers = headers["items"]
            
            ring_header = None
            for header in headers:
                if header.get("name") == "Ring":
                    ring_header = header
                    break
            
            if not ring_header:
                self.log_result("Issue #3 - Ring Inventory", "FAIL", "Ring inventory category not found")
                return
            
            initial_qty = ring_header.get("current_qty", 0)
            initial_weight = ring_header.get("current_weight", 0)
            print(f"   Initial Ring Stock: {initial_qty} qty, {initial_weight}g weight")
            
            # Step 3: Get current movement count
            response = self.session.get(f"{BASE_URL}/inventory/movements")
            if response.status_code != 200:
                self.log_result("Issue #3 - Get Movements", "FAIL", f"Failed to get movements: {response.status_code}")
                return
            
            movements_data = response.json()
            if isinstance(movements_data, dict) and "items" in movements_data:
                initial_movement_count = len(movements_data["items"])
            else:
                initial_movement_count = len(movements_data) if isinstance(movements_data, list) else 0
            
            # Step 4: Finalize the invoice
            response = self.session.post(f"{BASE_URL}/invoices/{invoice_id}/finalize")
            if response.status_code != 200:
                self.log_result("Issue #3 - Invoice Finalization", "FAIL", f"Failed to finalize invoice: {response.status_code} - {response.text}")
                return
            
            self.log_result("Issue #3 - Invoice Finalization", "PASS", f"Successfully finalized invoice {invoice_id}")
            
            # Step 5: Verify Stock OUT movement was created
            response = self.session.get(f"{BASE_URL}/inventory/movements")
            if response.status_code != 200:
                self.log_result("Issue #3 - Get Updated Movements", "FAIL", f"Failed to get updated movements: {response.status_code}")
                return
            
            movements = response.json()
            if isinstance(movements, dict) and "items" in movements:
                movements = movements["items"]
            new_movement_count = len(movements)
            
            # Look for the Stock OUT movement for our invoice
            stock_out_movement = None
            for movement in movements:
                if (movement.get("movement_type") == "Stock OUT" and 
                    movement.get("reference_type") == "invoice" and 
                    movement.get("reference_id") == invoice_id):
                    stock_out_movement = movement
                    break
            
            if stock_out_movement:
                qty_delta = stock_out_movement.get("qty_delta", 0)
                weight_delta = stock_out_movement.get("weight_delta", 0)
                
                if qty_delta == -1 and weight_delta == -5.0:
                    self.log_result("Issue #3 - Stock OUT Movement", "PASS", f"Stock OUT movement created correctly: qty_delta={qty_delta}, weight_delta={weight_delta}")
                else:
                    self.log_result("Issue #3 - Stock OUT Movement", "FAIL", f"Stock OUT movement has incorrect deltas: qty_delta={qty_delta}, weight_delta={weight_delta}")
            else:
                self.log_result("Issue #3 - Stock OUT Movement", "FAIL", "No Stock OUT movement found for the finalized invoice")
            
            # Step 6: Verify inventory stock decreased
            response = self.session.get(f"{BASE_URL}/inventory/headers")
            if response.status_code == 200:
                headers = response.json()
                if isinstance(headers, dict) and "items" in headers:
                    headers = headers["items"]
                    
                for header in headers:
                    if header.get("name") == "Ring":
                        final_qty = header.get("current_qty", 0)
                        final_weight = header.get("current_weight", 0)
                        
                        qty_decrease = initial_qty - final_qty
                        weight_decrease = initial_weight - final_weight
                        
                        print(f"   Final Ring Stock: {final_qty} qty, {final_weight}g weight")
                        print(f"   Stock Decrease: {qty_decrease} qty, {weight_decrease}g weight")
                        
                        if qty_decrease == 1 and abs(weight_decrease - 5.0) < 0.001:
                            self.log_result("Issue #3 - Inventory Update", "PASS", f"Inventory correctly decreased by {qty_decrease} qty, {weight_decrease}g")
                        else:
                            self.log_result("Issue #3 - Inventory Update", "FAIL", f"Inventory decrease incorrect: {qty_decrease} qty, {weight_decrease}g")
                        break
            
        except Exception as e:
            self.log_result("Issue #3 - Stock OUT Movement Verification", "ERROR", f"Test error: {str(e)}")
    
    def test_issue_4_customer_outstanding_balance(self):
        """
        MEDIUM PRIORITY ISSUE #4: Customer Outstanding Balance Calculation
        Verify discrepancy between party summary and invoice balance totals
        """
        print("\n" + "="*80)
        print("TESTING ISSUE #4: Customer Outstanding Balance Calculation")
        print("="*80)
        
        try:
            # Get test customer
            customer = self.get_test_customer()
            if not customer:
                self.log_result("Issue #4 - Setup", "FAIL", "Could not find test customer")
                return
            
            customer_id = customer["id"]
            
            # Step 1: Create a finalized invoice with partial payment
            invoice_data = {
                "customer_type": "saved",
                "customer_id": customer_id,
                "customer_name": customer["name"],
                "invoice_date": datetime.now().strftime("%Y-%m-%d"),
                "notes": "Test invoice for outstanding balance verification",
                "items": [
                    {
                        "category": "Chain",
                        "description": "Test Chain for Balance Verification",
                        "qty": 1,
                        "weight": 10.0,
                        "purity": 916,
                        "metal_rate": 25.0,
                        "gold_value": 250.0,
                        "making_value": 100.0,
                        "vat_percent": 5.0,
                        "vat_amount": 17.5,
                        "line_total": 367.5
                    }
                ],
                "subtotal": 350.0,
                "discount_percent": 0,
                "discount_amount": 0,
                "vat_amount": 17.5,
                "grand_total": 367.5,
                "paid_amount": 200.0,  # Partial payment
                "balance_due": 167.5,  # Should be auto-calculated
                "payment_status": "partial"
            }
            
            # Create invoice
            response = self.session.post(f"{BASE_URL}/invoices", json=invoice_data)
            if response.status_code != 200:
                self.log_result("Issue #4 - Invoice Creation", "FAIL", f"Failed to create invoice: {response.status_code} - {response.text}")
                return
            
            invoice = response.json()
            invoice_id = invoice["id"]
            
            # Finalize the invoice
            response = self.session.post(f"{BASE_URL}/invoices/{invoice_id}/finalize")
            if response.status_code != 200:
                self.log_result("Issue #4 - Invoice Finalization", "FAIL", f"Failed to finalize invoice: {response.status_code} - {response.text}")
                return
            
            self.log_result("Issue #4 - Invoice Setup", "PASS", f"Created and finalized invoice {invoice_id} with 167.5 OMR balance due")
            
            # Step 2: Get party summary
            response = self.session.get(f"{BASE_URL}/parties/{customer_id}/summary")
            if response.status_code != 200:
                self.log_result("Issue #4 - Party Summary", "FAIL", f"Failed to get party summary: {response.status_code}")
                return
            
            party_summary = response.json()
            money_due_from_party = party_summary.get("money", {}).get("money_due_from_party", 0)
            
            # Step 3: Get all invoices for this customer and calculate total balance_due
            response = self.session.get(f"{BASE_URL}/invoices?customer_id={customer_id}")
            if response.status_code != 200:
                self.log_result("Issue #4 - Customer Invoices", "FAIL", f"Failed to get customer invoices: {response.status_code}")
                return
            
            invoices = response.json().get("items", [])
            total_balance_due = sum(inv.get("balance_due", 0) for inv in invoices if inv.get("status") == "finalized")
            
            print(f"   Party Summary money_due_from_party: {money_due_from_party} OMR")
            print(f"   Sum of invoice balance_due amounts: {total_balance_due} OMR")
            
            # Step 4: Verify the calculation matches
            if abs(money_due_from_party - total_balance_due) < 0.01:  # Allow for small floating point differences
                self.log_result("Issue #4 - Outstanding Balance Calculation", "PASS", f"Party outstanding balance matches invoice totals: {money_due_from_party} OMR")
            else:
                self.log_result("Issue #4 - Outstanding Balance Calculation", "FAIL", f"DISCREPANCY: Party summary shows {money_due_from_party} OMR but invoice totals are {total_balance_due} OMR")
            
            # Additional verification: Check transaction records
            response = self.session.get(f"{BASE_URL}/transactions?party_id={customer_id}")
            if response.status_code == 200:
                transactions = response.json().get("items", [])
                print(f"   Customer has {len(transactions)} transaction records")
                
                # Check if transactions are affecting the calculation
                credit_transactions = [t for t in transactions if t.get("transaction_type") == "credit"]
                debit_transactions = [t for t in transactions if t.get("transaction_type") == "debit"]
                
                print(f"   Credit transactions: {len(credit_transactions)}")
                print(f"   Debit transactions: {len(debit_transactions)}")
            
        except Exception as e:
            self.log_result("Issue #4 - Customer Outstanding Balance", "ERROR", f"Test error: {str(e)}")
    
    def run_all_tests(self):
        """Run all critical issue tests"""
        print("STARTING INVOICE WORKFLOW CRITICAL ISSUES TESTING")
        print("Backend URL:", BASE_URL)
        print("Authentication:", f"{USERNAME}/***")
        print("="*80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run all tests
        self.test_issue_1_making_charges_calculation()
        self.test_issue_2_field_naming_consistency()
        self.test_issue_3_stock_out_movements()
        self.test_issue_4_customer_outstanding_balance()
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        error_tests = len([r for r in self.test_results if r["status"] == "ERROR"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️ Errors: {error_tests}")
        
        # Detailed results
        print("\nDETAILED RESULTS:")
        for result in self.test_results:
            status_symbol = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"{status_symbol} {result['test']}: {result['details']}")
        
        return failed_tests == 0 and error_tests == 0

if __name__ == "__main__":
    tester = InvoiceWorkflowTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
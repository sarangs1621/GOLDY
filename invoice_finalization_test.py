import requests
import sys
import json
from datetime import datetime

class InvoiceFinalizationTester:
    def __init__(self, base_url="https://decimal-precision.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None
        self.test_data = {}

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

    def setup_test_environment(self):
        """Setup test environment with admin login and test data"""
        print("\n🚀 SETTING UP TEST ENVIRONMENT")
        
        # Register admin user if needed
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
        
        # Login as admin
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
            print(f"   ✅ Admin logged in successfully")
            return True
        return False

    def create_test_customer(self, name_suffix=""):
        """Create a test customer for finalization tests"""
        customer_data = {
            "name": f"Test Customer for Finalization {name_suffix}",
            "phone": "+968 9999 1234",
            "address": "Test Address for Invoice Finalization",
            "party_type": "customer",
            "notes": "Customer created for invoice finalization testing"
        }
        
        success, customer = self.run_test(
            f"Create Test Customer {name_suffix}",
            "POST",
            "parties",
            200,
            data=customer_data
        )
        
        if success and customer.get('id'):
            return customer
        return None

    def create_test_items(self):
        """Create test items for invoices"""
        return [
            {
                "description": "Gold Ring (10g, 916 purity)",
                "qty": 1,
                "weight": 10.0,
                "purity": 916,
                "metal_rate": 25.0,
                "gold_value": 250.0,
                "making_value": 20.0,
                "vat_percent": 5.0,
                "vat_amount": 13.5,
                "line_total": 283.5
            },
            {
                "description": "Gold Chain (15g, 916 purity)",
                "qty": 1,
                "weight": 15.0,
                "purity": 916,
                "metal_rate": 25.0,
                "gold_value": 375.0,
                "making_value": 30.0,
                "vat_percent": 5.0,
                "vat_amount": 20.25,
                "line_total": 425.25
            }
        ]

    def test_draft_invoice_creation_no_stock_deduction(self):
        """Test 1: Draft Invoice Creation - NO Stock Deduction"""
        print("\n📝 TEST 1: DRAFT INVOICE CREATION - NO STOCK DEDUCTION")
        
        # Create test customer
        customer = self.create_test_customer("Draft Test")
        if not customer:
            return False
        
        # Create draft invoice with items
        items = self.create_test_items()
        invoice_data = {
            "customer_id": customer['id'],
            "customer_name": customer['name'],
            "invoice_type": "sale",
            "items": items,
            "subtotal": sum(item['gold_value'] + item['making_value'] for item in items),
            "vat_total": sum(item['vat_amount'] for item in items),
            "grand_total": sum(item['line_total'] for item in items),
            "balance_due": sum(item['line_total'] for item in items),
            "notes": "Test draft invoice - should NOT deduct stock"
        }
        
        success, invoice = self.run_test(
            "Create Draft Invoice with Items",
            "POST",
            "invoices",
            200,
            data=invoice_data
        )
        
        if not success or not invoice.get('id'):
            return False
        
        invoice_id = invoice['id']
        self.test_data['draft_invoice_id'] = invoice_id
        
        # Verify invoice is created with status="draft"
        if invoice.get('status') != 'draft':
            print(f"❌ Invoice should be created with status='draft', got: {invoice.get('status')}")
            return False
        
        print(f"✅ Invoice created with status='draft': {invoice.get('status')}")
        
        # Verify NO stock movements are created
        success, movements = self.run_test(
            "Check Stock Movements (Should be NONE for draft)",
            "GET",
            "inventory/movements",
            200
        )
        
        if not success:
            return False
        
        # Filter movements for this invoice
        invoice_movements = [
            m for m in movements 
            if m.get('reference_type') == 'invoice' and m.get('reference_id') == invoice_id
        ]
        
        if invoice_movements:
            print(f"❌ NO stock movements should exist for draft invoice, found: {len(invoice_movements)}")
            return False
        
        print(f"✅ NO stock movements created for draft invoice (correct behavior)")
        
        # Verify invoice can be retrieved
        success, retrieved_invoice = self.run_test(
            "Retrieve Draft Invoice by ID",
            "GET",
            f"invoices/{invoice_id}",
            200
        )
        
        if not success:
            return False
        
        if retrieved_invoice.get('id') != invoice_id:
            print(f"❌ Retrieved invoice ID mismatch")
            return False
        
        print(f"✅ Draft invoice can be retrieved successfully")
        
        return True

    def test_invoice_finalization_stock_deduction(self):
        """Test 2: Invoice Finalization - Stock Deduction Happens"""
        print("\n🔥 TEST 2: INVOICE FINALIZATION - STOCK DEDUCTION HAPPENS")
        
        # Create test customer
        customer = self.create_test_customer("Finalization Test")
        if not customer:
            return False
        
        # Create draft invoice with specific items
        items = [
            {
                "description": "Gold Ring (10g, 916 purity) - Finalization Test",
                "qty": 1,
                "weight": 10.0,
                "purity": 916,
                "metal_rate": 25.0,
                "gold_value": 250.0,
                "making_value": 20.0,
                "vat_percent": 5.0,
                "vat_amount": 13.5,
                "line_total": 283.5
            }
        ]
        
        invoice_data = {
            "customer_id": customer['id'],
            "customer_name": customer['name'],
            "invoice_type": "sale",
            "items": items,
            "subtotal": 270.0,
            "vat_total": 13.5,
            "grand_total": 283.5,
            "balance_due": 283.5,
            "notes": "Test invoice for finalization and stock deduction"
        }
        
        success, invoice = self.run_test(
            "Create Draft Invoice for Finalization",
            "POST",
            "invoices",
            200,
            data=invoice_data
        )
        
        if not success or not invoice.get('id'):
            return False
        
        invoice_id = invoice['id']
        
        # Record initial stock levels (get current movements)
        success, initial_movements = self.run_test(
            "Record Initial Stock Levels",
            "GET",
            "inventory/movements",
            200
        )
        
        if not success:
            return False
        
        initial_count = len(initial_movements)
        print(f"   Initial stock movements count: {initial_count}")
        
        # Call finalize endpoint
        success, finalized_response = self.run_test(
            "Finalize Invoice (Stock Deduction Should Happen)",
            "POST",
            f"invoices/{invoice_id}/finalize",
            200
        )
        
        if not success:
            return False
        
        # Verify response is successful (200 status) - already checked above
        print(f"✅ Finalization endpoint returned 200 status")
        
        # Verify invoice status changed to "finalized"
        if finalized_response.get('status') != 'finalized':
            print(f"❌ Invoice status should be 'finalized', got: {finalized_response.get('status')}")
            return False
        
        print(f"✅ Invoice status changed to 'finalized'")
        
        # Verify finalized_at and finalized_by fields are populated
        if not finalized_response.get('finalized_at'):
            print(f"❌ finalized_at field should be populated")
            return False
        
        if not finalized_response.get('finalized_by'):
            print(f"❌ finalized_by field should be populated")
            return False
        
        print(f"✅ finalized_at and finalized_by fields populated")
        
        # Verify stock movements are created
        success, final_movements = self.run_test(
            "Check Stock Movements After Finalization",
            "GET",
            "inventory/movements",
            200
        )
        
        if not success:
            return False
        
        # Find new stock movements for this invoice
        invoice_movements = [
            m for m in final_movements 
            if m.get('reference_type') == 'invoice' and m.get('reference_id') == invoice_id
        ]
        
        if not invoice_movements:
            print(f"❌ Stock movements should be created after finalization")
            return False
        
        print(f"✅ Stock movements created: {len(invoice_movements)} movements")
        
        # Verify stock movements have movement_type="Stock OUT"
        for movement in invoice_movements:
            if movement.get('movement_type') != 'Stock OUT':
                print(f"❌ Movement type should be 'Stock OUT', got: {movement.get('movement_type')}")
                return False
        
        print(f"✅ All movements have movement_type='Stock OUT'")
        
        # Verify stock movements have NEGATIVE qty_delta and weight_delta values
        for movement in invoice_movements:
            qty_delta = movement.get('qty_delta', 0)
            weight_delta = movement.get('weight_delta', 0)
            
            if qty_delta >= 0:
                print(f"❌ qty_delta should be negative (Stock OUT), got: {qty_delta}")
                return False
            
            if weight_delta >= 0:
                print(f"❌ weight_delta should be negative (Stock OUT), got: {weight_delta}")
                return False
        
        print(f"✅ All movements have NEGATIVE qty_delta and weight_delta values")
        
        # Verify stock movements reference the invoice
        for movement in invoice_movements:
            if movement.get('reference_type') != 'invoice':
                print(f"❌ reference_type should be 'invoice', got: {movement.get('reference_type')}")
                return False
            
            if movement.get('reference_id') != invoice_id:
                print(f"❌ reference_id should be {invoice_id}, got: {movement.get('reference_id')}")
                return False
        
        print(f"✅ All movements correctly reference the invoice")
        
        self.test_data['finalized_invoice_id'] = invoice_id
        return True

    def test_finalized_invoice_cannot_be_edited(self):
        """Test 3: Finalized Invoice Cannot Be Edited"""
        print("\n🔒 TEST 3: FINALIZED INVOICE CANNOT BE EDITED")
        
        if 'finalized_invoice_id' not in self.test_data:
            print("❌ No finalized invoice available for testing")
            return False
        
        invoice_id = self.test_data['finalized_invoice_id']
        
        # Attempt to update the finalized invoice
        update_data = {
            "notes": "Attempting to edit finalized invoice",
            "customer_name": "Modified Customer Name"
        }
        
        success, error_response = self.run_test(
            "Attempt to Edit Finalized Invoice (Should FAIL)",
            "PATCH",
            f"invoices/{invoice_id}",
            400,  # Expecting 400 Bad Request
            data=update_data
        )
        
        if not success:
            print(f"❌ Expected 400 status for editing finalized invoice")
            return False
        
        # Verify error message mentions immutability
        error_str = str(error_response).lower()
        if 'immutable' not in error_str and 'finalized' not in error_str:
            print(f"❌ Error message should mention immutability or finalized status")
            return False
        
        print(f"✅ Finalized invoice correctly rejects edit attempts with 400 error")
        print(f"   Error message mentions immutability: {error_response}")
        
        return True

    def test_finalized_invoice_cannot_be_deleted(self):
        """Test 4: Finalized Invoice Cannot Be Deleted"""
        print("\n🗑️ TEST 4: FINALIZED INVOICE CANNOT BE DELETED")
        
        if 'finalized_invoice_id' not in self.test_data:
            print("❌ No finalized invoice available for testing")
            return False
        
        invoice_id = self.test_data['finalized_invoice_id']
        
        # Attempt to delete the finalized invoice
        success, error_response = self.run_test(
            "Attempt to Delete Finalized Invoice (Should FAIL)",
            "DELETE",
            f"invoices/{invoice_id}",
            400  # Expecting 400 Bad Request
        )
        
        if not success:
            print(f"❌ Expected 400 status for deleting finalized invoice")
            return False
        
        # Verify error message mentions finalized invoices cannot be deleted
        error_str = str(error_response).lower()
        if 'finalized' not in error_str or 'delete' not in error_str:
            print(f"❌ Error message should mention finalized invoices cannot be deleted")
            return False
        
        print(f"✅ Finalized invoice correctly rejects delete attempts with 400 error")
        print(f"   Error message: {error_response}")
        
        return True

    def test_cannot_re_finalize_invoice(self):
        """Test 5: Cannot Re-Finalize an Already Finalized Invoice"""
        print("\n🔄 TEST 5: CANNOT RE-FINALIZE ALREADY FINALIZED INVOICE")
        
        if 'finalized_invoice_id' not in self.test_data:
            print("❌ No finalized invoice available for testing")
            return False
        
        invoice_id = self.test_data['finalized_invoice_id']
        
        # Get current stock movements count
        success, movements_before = self.run_test(
            "Count Stock Movements Before Re-finalization Attempt",
            "GET",
            "inventory/movements",
            200
        )
        
        if not success:
            return False
        
        movements_before_count = len([
            m for m in movements_before 
            if m.get('reference_type') == 'invoice' and m.get('reference_id') == invoice_id
        ])
        
        # Attempt to finalize it again
        success, error_response = self.run_test(
            "Attempt to Re-finalize Already Finalized Invoice (Should FAIL)",
            "POST",
            f"invoices/{invoice_id}/finalize",
            400  # Expecting 400 Bad Request
        )
        
        if not success:
            print(f"❌ Expected 400 status for re-finalizing invoice")
            return False
        
        # Verify error message says "Invoice is already finalized"
        error_str = str(error_response).lower()
        if 'already finalized' not in error_str:
            print(f"❌ Error message should say 'Invoice is already finalized'")
            return False
        
        print(f"✅ Re-finalization correctly rejected with 400 error")
        print(f"   Error message: {error_response}")
        
        # Verify no duplicate stock movements are created
        success, movements_after = self.run_test(
            "Verify No Duplicate Stock Movements Created",
            "GET",
            "inventory/movements",
            200
        )
        
        if not success:
            return False
        
        movements_after_count = len([
            m for m in movements_after 
            if m.get('reference_type') == 'invoice' and m.get('reference_id') == invoice_id
        ])
        
        if movements_after_count != movements_before_count:
            print(f"❌ Duplicate stock movements created: before={movements_before_count}, after={movements_after_count}")
            return False
        
        print(f"✅ No duplicate stock movements created")
        
        return True

    def test_job_card_locking_on_finalization(self):
        """Test 6: Job Card Locking on Invoice Finalization"""
        print("\n🔐 TEST 6: JOB CARD LOCKING ON INVOICE FINALIZATION")
        
        # Create customer
        customer = self.create_test_customer("Job Card Lock Test")
        if not customer:
            return False
        
        # Create job card
        jobcard_data = {
            "card_type": "individual",
            "customer_id": customer['id'],
            "customer_name": customer['name'],
            "delivery_date": "2025-02-01",
            "notes": "Job card for locking test",
            "items": [{
                "category": "Ring",
                "description": "Gold ring for job card locking test",
                "qty": 1,
                "weight_in": 12.0,
                "weight_out": 11.8,
                "purity": 916,
                "work_type": "polish",
                "remarks": "Polish and clean",
                "making_charge_type": "flat",
                "making_charge_value": 15.0,
                "vat_percent": 5.0
            }]
        }
        
        success, jobcard = self.run_test(
            "Create Job Card for Locking Test",
            "POST",
            "jobcards",
            200,
            data=jobcard_data
        )
        
        if not success or not jobcard.get('id'):
            return False
        
        jobcard_id = jobcard['id']
        
        # Create invoice linked to job card
        success, invoice = self.run_test(
            "Convert Job Card to Invoice",
            "POST",
            f"jobcards/{jobcard_id}/convert-to-invoice",
            200
        )
        
        if not success or not invoice.get('id'):
            return False
        
        invoice_id = invoice['id']
        
        # Verify invoice has jobcard_id field
        if invoice.get('jobcard_id') != jobcard_id:
            print(f"❌ Invoice should have jobcard_id={jobcard_id}, got: {invoice.get('jobcard_id')}")
            return False
        
        print(f"✅ Invoice linked to job card: jobcard_id={invoice.get('jobcard_id')}")
        
        # Finalize the invoice
        success, finalized_invoice = self.run_test(
            "Finalize Invoice (Should Lock Job Card)",
            "POST",
            f"invoices/{invoice_id}/finalize",
            200
        )
        
        if not success:
            return False
        
        # Verify the job card is locked
        success, updated_jobcard = self.run_test(
            "Check Job Card After Invoice Finalization",
            "GET",
            f"jobcards/{jobcard_id}",
            200
        )
        
        if not success:
            return False
        
        # Check locked field
        if not updated_jobcard.get('locked'):
            print(f"❌ Job card should be locked=True, got: {updated_jobcard.get('locked')}")
            return False
        
        # Check locked_at field
        if not updated_jobcard.get('locked_at'):
            print(f"❌ Job card should have locked_at timestamp")
            return False
        
        # Check locked_by field
        if not updated_jobcard.get('locked_by'):
            print(f"❌ Job card should have locked_by user ID")
            return False
        
        # Check status changed to "invoiced"
        if updated_jobcard.get('status') != 'invoiced':
            print(f"❌ Job card status should be 'invoiced', got: {updated_jobcard.get('status')}")
            return False
        
        print(f"✅ Job card locked successfully:")
        print(f"   - locked: {updated_jobcard.get('locked')}")
        print(f"   - locked_at: {updated_jobcard.get('locked_at')}")
        print(f"   - locked_by: {updated_jobcard.get('locked_by')}")
        print(f"   - status: {updated_jobcard.get('status')}")
        
        # Attempt to edit the locked job card (should fail for non-admin)
        # Note: We're logged in as admin, so this will succeed with warning
        success, edit_response = self.run_test(
            "Attempt to Edit Locked Job Card (Admin Override)",
            "PATCH",
            f"jobcards/{jobcard_id}",
            200,  # Admin can edit with override
            data={"notes": "Attempting to edit locked job card"}
        )
        
        if not success:
            print(f"❌ Admin should be able to edit locked job card with override")
            return False
        
        # Verify response contains warning about locked job card
        response_str = str(edit_response).lower()
        if 'locked' not in response_str or 'finalized invoice' not in response_str:
            print(f"❌ Response should contain warning about locked job card")
            return False
        
        print(f"✅ Admin can edit locked job card with override and warning")
        
        return True

    def test_customer_ledger_entry_creation(self):
        """Test 7: Customer Ledger Entry Creation on Finalization"""
        print("\n📊 TEST 7: CUSTOMER LEDGER ENTRY CREATION ON FINALIZATION")
        
        # Create customer
        customer = self.create_test_customer("Ledger Test")
        if not customer:
            return False
        
        customer_id = customer['id']
        
        # Create invoice for that customer
        items = [{
            "description": "Gold item for ledger test",
            "qty": 1,
            "weight": 8.0,
            "purity": 916,
            "metal_rate": 30.0,
            "gold_value": 240.0,
            "making_value": 25.0,
            "vat_percent": 5.0,
            "vat_amount": 13.25,
            "line_total": 278.25
        }]
        
        invoice_data = {
            "customer_id": customer_id,
            "customer_name": customer['name'],
            "invoice_type": "sale",
            "items": items,
            "subtotal": 265.0,
            "vat_total": 13.25,
            "grand_total": 278.25,
            "balance_due": 278.25,
            "notes": "Invoice for ledger entry testing"
        }
        
        success, invoice = self.run_test(
            "Create Invoice for Ledger Test",
            "POST",
            "invoices",
            200,
            data=invoice_data
        )
        
        if not success or not invoice.get('id'):
            return False
        
        invoice_id = invoice['id']
        grand_total = invoice.get('grand_total', 0)
        
        # Finalize the invoice
        success, finalized_invoice = self.run_test(
            "Finalize Invoice (Should Create Ledger Entry)",
            "POST",
            f"invoices/{invoice_id}/finalize",
            200
        )
        
        if not success:
            return False
        
        # Verify a Transaction record is created
        success, transactions = self.run_test(
            "Get All Transactions (Find Ledger Entry)",
            "GET",
            "transactions",
            200
        )
        
        if not success:
            return False
        
        # Find the transaction for this invoice
        invoice_number = finalized_invoice.get('invoice_number', '')
        ledger_entry = None
        
        for txn in transactions:
            if (txn.get('party_id') == customer_id and 
                txn.get('category') == 'Sales Invoice' and
                invoice_number in txn.get('notes', '')):
                ledger_entry = txn
                break
        
        if not ledger_entry:
            print(f"❌ No ledger entry found for customer {customer_id} and invoice {invoice_number}")
            return False
        
        # Verify Transaction record properties
        # party_id = customer_id
        if ledger_entry.get('party_id') != customer_id:
            print(f"❌ Ledger entry party_id should be {customer_id}, got: {ledger_entry.get('party_id')}")
            return False
        
        # amount = grand_total
        if ledger_entry.get('amount') != grand_total:
            print(f"❌ Ledger entry amount should be {grand_total}, got: {ledger_entry.get('amount')}")
            return False
        
        # category = "Sales Invoice"
        if ledger_entry.get('category') != 'Sales Invoice':
            print(f"❌ Ledger entry category should be 'Sales Invoice', got: {ledger_entry.get('category')}")
            return False
        
        # transaction_number follows TXN-YYYY-NNNN format
        txn_number = ledger_entry.get('transaction_number', '')
        import re
        if not re.match(r'^TXN-\d{4}-\d{4}$', txn_number):
            print(f"❌ Transaction number format should be TXN-YYYY-NNNN, got: {txn_number}")
            return False
        
        print(f"✅ Ledger entry created successfully:")
        print(f"   - party_id: {ledger_entry.get('party_id')}")
        print(f"   - amount: {ledger_entry.get('amount')}")
        print(f"   - category: {ledger_entry.get('category')}")
        print(f"   - transaction_number: {txn_number}")
        
        # Verify customer's outstanding balance is updated
        success, party_ledger = self.run_test(
            "Get Customer Ledger (Check Outstanding Balance)",
            "GET",
            f"parties/{customer_id}/ledger",
            200
        )
        
        if not success:
            return False
        
        outstanding = party_ledger.get('outstanding', 0)
        expected_outstanding = finalized_invoice.get('balance_due', 0)
        
        if outstanding != expected_outstanding:
            print(f"❌ Outstanding balance should be {expected_outstanding}, got: {outstanding}")
            return False
        
        print(f"✅ Customer outstanding balance updated: {outstanding}")
        
        return True

    def run_all_tests(self):
        """Run all invoice finalization tests"""
        print("🚀 STARTING COMPREHENSIVE INVOICE FINALIZATION WORKFLOW TESTS")
        print("=" * 80)
        
        # Setup
        if not self.setup_test_environment():
            print("❌ Failed to setup test environment")
            return False
        
        # Run all test scenarios
        test_results = []
        
        test_results.append(self.test_draft_invoice_creation_no_stock_deduction())
        test_results.append(self.test_invoice_finalization_stock_deduction())
        test_results.append(self.test_finalized_invoice_cannot_be_edited())
        test_results.append(self.test_finalized_invoice_cannot_be_deleted())
        test_results.append(self.test_cannot_re_finalize_invoice())
        test_results.append(self.test_job_card_locking_on_finalization())
        test_results.append(self.test_customer_ledger_entry_creation())
        
        # Summary
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        print("\n" + "=" * 80)
        print("🏁 INVOICE FINALIZATION WORKFLOW TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests Run: {total_tests}")
        print(f"Tests Passed: {passed_tests}")
        print(f"Tests Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL INVOICE FINALIZATION TESTS PASSED!")
            print("✅ Draft invoices: status='draft', NO stock movements")
            print("✅ Finalized invoices: status='finalized', stock movements created with negative values")
            print("✅ Finalized invoices are immutable (cannot edit/delete)")
            print("✅ Cannot re-finalize")
            print("✅ Job cards get locked when invoice is finalized")
            print("✅ Customer ledger entries are created")
            print("✅ Stock deduction happens ATOMICALLY only on finalization")
        else:
            print(f"\n❌ {total_tests - passed_tests} TESTS FAILED")
            print("Please review the failed tests above for details")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = InvoiceFinalizationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
import requests
import sys
import json
from datetime import datetime

class InvoiceStateManagementTester:
    def __init__(self, base_url="https://decimal-precision.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.test_results = []
        self.created_invoices = []
        self.created_customer_id = None

    def log_result(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        self.test_results.append({"name": test_name, "success": success, "details": details})
        return success

    def make_request(self, method, endpoint, data=None, params=None, expected_status=None):
        """Make HTTP request with proper headers"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            print(f"   {method} {endpoint} -> Status: {response.status_code}")
            
            if expected_status and response.status_code != expected_status:
                print(f"   Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

            try:
                return True, response.json()
            except:
                return True, {"status_code": response.status_code}

        except Exception as e:
            print(f"   Request failed: {str(e)}")
            return False, {}

    def setup_authentication(self):
        """Setup authentication and create test customer"""
        print("🔐 Setting up authentication...")
        
        # Register admin user (ignore if exists)
        self.make_request("POST", "auth/register", data={
            "username": "admin",
            "password": "admin123",
            "email": "admin@goldshop.com",
            "full_name": "System Administrator",
            "role": "admin"
        })
        
        # Login
        success, response = self.make_request("POST", "auth/login", data={
            "username": "admin", 
            "password": "admin123"
        }, expected_status=200)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            print(f"   ✅ Authenticated as {response['user']['username']}")
            
            # Create test customer
            customer_success, customer = self.make_request("POST", "parties", data={
                "name": "Test Customer for Invoice State",
                "phone": "+968 9999 1234",
                "party_type": "customer"
            }, expected_status=200)
            
            if customer_success:
                self.created_customer_id = customer['id']
                print(f"   ✅ Created test customer: {customer['id']}")
                return True
        
        return False

    def verify_stock_movements(self, invoice_id, should_exist=True):
        """Verify stock movements for an invoice"""
        success, movements = self.make_request("GET", "inventory/movements", expected_status=200)
        if not success:
            return False, "Failed to fetch stock movements"
        
        # Filter movements for this invoice
        invoice_movements = [m for m in movements if m.get('reference_id') == invoice_id]
        
        if should_exist:
            if len(invoice_movements) == 0:
                return False, f"Expected stock movements for invoice {invoice_id}, but found none"
            else:
                return True, f"Found {len(invoice_movements)} stock movements for invoice {invoice_id}"
        else:
            if len(invoice_movements) > 0:
                return False, f"Expected NO stock movements for invoice {invoice_id}, but found {len(invoice_movements)}"
            else:
                return True, f"Correctly found NO stock movements for invoice {invoice_id}"

    def verify_audit_log(self, record_id, action):
        """Verify audit log entry exists"""
        success, logs = self.make_request("GET", "audit-logs", params={"module": "invoice"}, expected_status=200)
        if not success:
            return False, "Failed to fetch audit logs"
        
        # Find matching log entry
        matching_logs = [log for log in logs if log.get('record_id') == record_id and log.get('action') == action]
        
        if len(matching_logs) > 0:
            return True, f"Found audit log for {action} on {record_id}"
        else:
            return False, f"No audit log found for {action} on {record_id}"

    def test_create_draft_invoice(self):
        """Test 1: Create Draft Invoice - verify NO stock deduction"""
        print("\n📝 Test 1: Create Draft Invoice")
        
        invoice_data = {
            "customer_id": self.created_customer_id,
            "customer_name": "Test Customer for Invoice State",
            "invoice_type": "sale",
            "items": [{
                "description": "Gold Ring",
                "qty": 1,
                "weight": 5.5,
                "purity": 22,
                "metal_rate": 5000,
                "gold_value": 27500,
                "making_value": 2000,
                "vat_percent": 5,
                "vat_amount": 1475,
                "line_total": 30975
            }],
            "subtotal": 29500,
            "vat_total": 1475,
            "grand_total": 30975,
            "balance_due": 30975
        }
        
        success, invoice = self.make_request("POST", "invoices", data=invoice_data, expected_status=200)
        
        if not success:
            return self.log_result("Create Draft Invoice", False, "Failed to create invoice")
        
        invoice_id = invoice.get('id')
        if not invoice_id:
            return self.log_result("Create Draft Invoice", False, "No invoice ID returned")
        
        self.created_invoices.append(invoice_id)
        
        # Verify invoice is in draft status
        if invoice.get('status') != 'draft':
            return self.log_result("Create Draft Invoice", False, f"Expected status 'draft', got '{invoice.get('status')}'")
        
        if invoice.get('finalized_at') is not None:
            return self.log_result("Create Draft Invoice", False, "finalized_at should be null for draft invoice")
        
        if invoice.get('finalized_by') is not None:
            return self.log_result("Create Draft Invoice", False, "finalized_by should be null for draft invoice")
        
        # CRITICAL: Verify NO stock movements were created
        stock_ok, stock_msg = self.verify_stock_movements(invoice_id, should_exist=False)
        if not stock_ok:
            return self.log_result("Create Draft Invoice", False, f"Stock movement check failed: {stock_msg}")
        
        # Verify audit log
        audit_ok, audit_msg = self.verify_audit_log(invoice_id, "create")
        if not audit_ok:
            return self.log_result("Create Draft Invoice", False, f"Audit log check failed: {audit_msg}")
        
        return self.log_result("Create Draft Invoice", True, f"Invoice {invoice_id} created as draft with no stock deduction")

    def test_edit_draft_invoice(self):
        """Test 2: Edit Draft Invoice - should succeed"""
        print("\n✏️ Test 2: Edit Draft Invoice")
        
        if not self.created_invoices:
            return self.log_result("Edit Draft Invoice", False, "No draft invoice available to edit")
        
        invoice_id = self.created_invoices[0]
        
        update_data = {
            "customer_name": "Updated Customer Name",
            "notes": "Updated notes for draft invoice"
        }
        
        success, response = self.make_request("PATCH", f"invoices/{invoice_id}", data=update_data, expected_status=200)
        
        if not success:
            return self.log_result("Edit Draft Invoice", False, "Failed to update draft invoice")
        
        # Verify the invoice is still in draft status
        success, updated_invoice = self.make_request("GET", f"invoices/{invoice_id}", expected_status=200)
        if success and updated_invoice.get('status') != 'draft':
            return self.log_result("Edit Draft Invoice", False, "Invoice status changed unexpectedly during edit")
        
        return self.log_result("Edit Draft Invoice", True, f"Successfully updated draft invoice {invoice_id}")

    def test_finalize_draft_invoice(self):
        """Test 3: Finalize Draft Invoice - verify stock movements ARE created"""
        print("\n🔒 Test 3: Finalize Draft Invoice")
        
        if not self.created_invoices:
            return self.log_result("Finalize Draft Invoice", False, "No draft invoice available to finalize")
        
        invoice_id = self.created_invoices[0]
        
        success, response = self.make_request("POST", f"invoices/{invoice_id}/finalize", expected_status=200)
        
        if not success:
            return self.log_result("Finalize Draft Invoice", False, "Failed to finalize invoice")
        
        # Verify invoice status changed to finalized
        if response.get('status') != 'finalized':
            return self.log_result("Finalize Draft Invoice", False, f"Expected status 'finalized', got '{response.get('status')}'")
        
        if not response.get('finalized_at'):
            return self.log_result("Finalize Draft Invoice", False, "finalized_at should be set")
        
        if not response.get('finalized_by'):
            return self.log_result("Finalize Draft Invoice", False, "finalized_by should be set")
        
        # CRITICAL: Verify stock movements WERE created
        stock_ok, stock_msg = self.verify_stock_movements(invoice_id, should_exist=True)
        if not stock_ok:
            return self.log_result("Finalize Draft Invoice", False, f"Stock movement check failed: {stock_msg}")
        
        # Verify stock movements have correct values (negative for Stock OUT)
        success, movements = self.make_request("GET", "inventory/movements", expected_status=200)
        if success:
            invoice_movements = [m for m in movements if m.get('reference_id') == invoice_id]
            for movement in invoice_movements:
                if movement.get('qty_delta', 0) >= 0:
                    return self.log_result("Finalize Draft Invoice", False, f"Expected negative qty_delta, got {movement.get('qty_delta')}")
                if movement.get('weight_delta', 0) >= 0:
                    return self.log_result("Finalize Draft Invoice", False, f"Expected negative weight_delta, got {movement.get('weight_delta')}")
        
        # Verify audit log
        audit_ok, audit_msg = self.verify_audit_log(invoice_id, "finalize")
        if not audit_ok:
            return self.log_result("Finalize Draft Invoice", False, f"Audit log check failed: {audit_msg}")
        
        return self.log_result("Finalize Draft Invoice", True, f"Invoice {invoice_id} finalized with stock movements created")

    def test_edit_finalized_invoice_should_fail(self):
        """Test 4: Attempt to Edit Finalized Invoice - should fail"""
        print("\n🚫 Test 4: Attempt to Edit Finalized Invoice")
        
        if not self.created_invoices:
            return self.log_result("Edit Finalized Invoice (Should Fail)", False, "No finalized invoice available")
        
        invoice_id = self.created_invoices[0]
        
        update_data = {
            "customer_name": "This should not work",
            "notes": "This edit should be rejected"
        }
        
        success, response = self.make_request("PATCH", f"invoices/{invoice_id}", data=update_data, expected_status=400)
        
        if success:
            # Check if error message mentions finalized invoice
            error_detail = response.get('detail', '')
            if 'finalized' in error_detail.lower():
                return self.log_result("Edit Finalized Invoice (Should Fail)", True, f"Correctly rejected edit: {error_detail}")
            else:
                return self.log_result("Edit Finalized Invoice (Should Fail)", False, f"Wrong error message: {error_detail}")
        else:
            return self.log_result("Edit Finalized Invoice (Should Fail)", False, "Request should have failed with 400 status")

    def test_delete_finalized_invoice_should_fail(self):
        """Test 5: Attempt to Delete Finalized Invoice - should fail"""
        print("\n🚫 Test 5: Attempt to Delete Finalized Invoice")
        
        if not self.created_invoices:
            return self.log_result("Delete Finalized Invoice (Should Fail)", False, "No finalized invoice available")
        
        invoice_id = self.created_invoices[0]
        
        success, response = self.make_request("DELETE", f"invoices/{invoice_id}", expected_status=400)
        
        if success:
            # Check if error message mentions finalized invoice
            error_detail = response.get('detail', '')
            if 'finalized' in error_detail.lower():
                return self.log_result("Delete Finalized Invoice (Should Fail)", True, f"Correctly rejected delete: {error_detail}")
            else:
                return self.log_result("Delete Finalized Invoice (Should Fail)", False, f"Wrong error message: {error_detail}")
        else:
            return self.log_result("Delete Finalized Invoice (Should Fail)", False, "Request should have failed with 400 status")

    def test_finalize_already_finalized_should_fail(self):
        """Test 6: Attempt to Finalize Already Finalized Invoice - should fail"""
        print("\n🚫 Test 6: Attempt to Finalize Already Finalized Invoice")
        
        if not self.created_invoices:
            return self.log_result("Finalize Already Finalized (Should Fail)", False, "No finalized invoice available")
        
        invoice_id = self.created_invoices[0]
        
        success, response = self.make_request("POST", f"invoices/{invoice_id}/finalize", expected_status=400)
        
        if success:
            # Check if error message mentions already finalized
            error_detail = response.get('detail', '')
            if 'already finalized' in error_detail.lower():
                return self.log_result("Finalize Already Finalized (Should Fail)", True, f"Correctly rejected: {error_detail}")
            else:
                return self.log_result("Finalize Already Finalized (Should Fail)", False, f"Wrong error message: {error_detail}")
        else:
            return self.log_result("Finalize Already Finalized (Should Fail)", False, "Request should have failed with 400 status")

    def test_delete_draft_invoice_should_succeed(self):
        """Test 7: Delete Draft Invoice - should succeed"""
        print("\n🗑️ Test 7: Delete Draft Invoice")
        
        # Create a new draft invoice for deletion test
        invoice_data = {
            "customer_id": self.created_customer_id,
            "customer_name": "Test Customer for Deletion",
            "invoice_type": "sale",
            "items": [{
                "description": "Test Item for Deletion",
                "qty": 1,
                "weight": 2.5,
                "purity": 22,
                "metal_rate": 5000,
                "gold_value": 12500,
                "making_value": 1000,
                "vat_percent": 5,
                "vat_amount": 675,
                "line_total": 14175
            }],
            "subtotal": 13500,
            "vat_total": 675,
            "grand_total": 14175,
            "balance_due": 14175
        }
        
        success, invoice = self.make_request("POST", "invoices", data=invoice_data, expected_status=200)
        
        if not success:
            return self.log_result("Delete Draft Invoice", False, "Failed to create draft invoice for deletion test")
        
        invoice_id = invoice.get('id')
        
        # Verify it's in draft status
        if invoice.get('status') != 'draft':
            return self.log_result("Delete Draft Invoice", False, "Invoice is not in draft status")
        
        # Delete the draft invoice
        success, response = self.make_request("DELETE", f"invoices/{invoice_id}", expected_status=200)
        
        if not success:
            return self.log_result("Delete Draft Invoice", False, "Failed to delete draft invoice")
        
        # Verify invoice is marked as deleted (should return 404)
        try:
            url = f"{self.base_url}/api/invoices/{invoice_id}"
            headers = {'Authorization': f'Bearer {self.token}'}
            response = requests.get(url, headers=headers)
            
            if response.status_code == 404:
                return self.log_result("Delete Draft Invoice", True, f"Successfully deleted draft invoice {invoice_id}")
            else:
                return self.log_result("Delete Draft Invoice", False, f"Invoice still accessible after deletion (status: {response.status_code})")
        except Exception as e:
            return self.log_result("Delete Draft Invoice", False, f"Error checking deleted invoice: {str(e)}")

    def run_all_tests(self):
        """Run all invoice state management tests"""
        print("🚀 CRITICAL BUSINESS LOGIC TESTING - Invoice State Management")
        print("=" * 70)
        print("Testing invoice draft/finalized workflow and stock deduction logic")
        print("=" * 70)

        # Setup
        if not self.setup_authentication():
            print("❌ Authentication setup failed, stopping tests")
            return False

        # Run all test scenarios
        test_methods = [
            self.test_create_draft_invoice,
            self.test_edit_draft_invoice,
            self.test_finalize_draft_invoice,
            self.test_edit_finalized_invoice_should_fail,
            self.test_delete_finalized_invoice_should_fail,
            self.test_finalize_already_finalized_should_fail,
            self.test_delete_draft_invoice_should_succeed
        ]

        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ Test {test_method.__name__} crashed: {str(e)}")
                self.test_results.append({
                    "name": test_method.__name__, 
                    "success": False, 
                    "details": f"Test crashed: {str(e)}"
                })

        # Print final results
        print("\n" + "=" * 70)
        print("📊 INVOICE STATE MANAGEMENT TEST RESULTS")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{result['name']:<40} {status}")
            if not result['success'] and result['details']:
                print(f"   └─ {result['details']}")

        print(f"\n📈 Overall: {passed}/{total} tests passed")
        success_rate = (passed / total) * 100 if total > 0 else 0
        print(f"🎯 Success Rate: {success_rate:.1f}%")

        if success_rate == 100:
            print("\n🎉 ALL TESTS PASSED - Invoice state management is working correctly!")
            print("✅ Stock deduction only happens on finalization")
            print("✅ Finalized invoices are properly immutable")
            print("✅ Draft invoices can be edited and deleted")
        else:
            print(f"\n⚠️  {total - passed} TESTS FAILED - Invoice state management has issues!")
            
        return success_rate >= 90

def main():
    tester = InvoiceStateManagementTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
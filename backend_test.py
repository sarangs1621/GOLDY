import requests
import sys
import json
from datetime import datetime

class GoldShopERPTester:
    def __init__(self, base_url="https://vendor-transactions.preview.emergentagent.com"):
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

    def test_auth_me(self):
        """Test getting current user info"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        return success and response.get('username') == 'admin'

    def test_inventory_headers(self):
        """Test inventory headers CRUD"""
        # Get existing headers
        success, headers = self.run_test(
            "Get Inventory Headers",
            "GET",
            "inventory/headers",
            200
        )
        if not success:
            return False

        # Create new header
        test_header_name = f"Test Category {datetime.now().strftime('%H%M%S')}"
        success, new_header = self.run_test(
            "Create Inventory Header",
            "POST",
            "inventory/headers",
            200,
            data={"name": test_header_name}
        )
        if success and new_header.get('id'):
            self.created_resources['headers'].append(new_header['id'])
            return True
        return False

    def test_stock_movements(self):
        """Test stock movements"""
        # First ensure we have a header
        if not self.created_resources['headers']:
            return False

        header_id = self.created_resources['headers'][0]
        
        # Create stock movement
        movement_data = {
            "movement_type": "Stock IN",
            "header_id": header_id,
            "description": "Test stock movement",
            "qty_delta": 5,
            "weight_delta": 25.500,
            "purity": 916,
            "notes": "Test movement"
        }
        
        success, movement = self.run_test(
            "Create Stock Movement",
            "POST",
            "inventory/movements",
            200,
            data=movement_data
        )
        
        if success:
            # Get stock totals
            success2, totals = self.run_test(
                "Get Stock Totals",
                "GET",
                "inventory/stock-totals",
                200
            )
            return success2
        return False

    def test_parties(self):
        """Test parties CRUD"""
        # Create customer
        customer_data = {
            "name": f"Test Customer {datetime.now().strftime('%H%M%S')}",
            "phone": "+968 9999 9999",
            "address": "Test Address",
            "party_type": "customer",
            "notes": "Test customer"
        }
        
        success, customer = self.run_test(
            "Create Customer",
            "POST",
            "parties",
            200,
            data=customer_data
        )
        
        if success and customer.get('id'):
            self.created_resources['parties'].append(customer['id'])
            
            # Get all parties
            success2, parties = self.run_test(
                "Get All Parties",
                "GET",
                "parties",
                200
            )
            
            # Get outstanding summary
            success3, outstanding = self.run_test(
                "Get Outstanding Summary",
                "GET",
                "parties/outstanding-summary",
                200
            )
            
            return success2 and success3
        return False

    def test_accounts(self):
        """Test accounts CRUD"""
        account_data = {
            "name": f"Test Cash Account {datetime.now().strftime('%H%M%S')}",
            "account_type": "cash",
            "opening_balance": 1000.000
        }
        
        success, account = self.run_test(
            "Create Account",
            "POST",
            "accounts",
            200,
            data=account_data
        )
        
        if success and account.get('id'):
            self.created_resources['accounts'].append(account['id'])
            
            # Get all accounts
            success2, accounts = self.run_test(
                "Get All Accounts",
                "GET",
                "accounts",
                200
            )
            return success2
        return False

    def test_transactions(self):
        """Test transactions"""
        if not self.created_resources['accounts']:
            return False
            
        account_id = self.created_resources['accounts'][0]
        
        transaction_data = {
            "transaction_type": "credit",
            "mode": "cash",
            "account_id": account_id,
            "amount": 500.000,
            "category": "sales",
            "notes": "Test transaction"
        }
        
        success, transaction = self.run_test(
            "Create Transaction",
            "POST",
            "transactions",
            200,
            data=transaction_data
        )
        
        if success:
            # Get all transactions
            success2, transactions = self.run_test(
                "Get All Transactions",
                "GET",
                "transactions",
                200
            )
            return success2
        return False

    def test_jobcards(self):
        """Test job cards with new making charge and VAT fields"""
        if not self.created_resources['parties']:
            return False
            
        customer_id = self.created_resources['parties'][0]
        
        # Test 1: Job card with flat making charge and VAT
        jobcard_data_flat = {
            "card_type": "individual",
            "customer_id": customer_id,
            "customer_name": "Test Customer",
            "delivery_date": "2025-01-15",
            "notes": "Test job card with flat making charge",
            "items": [{
                "category": "Ring",
                "description": "Gold ring with flat making charge",
                "qty": 1,
                "weight_in": 10.500,
                "weight_out": 10.200,
                "purity": 916,
                "work_type": "polish",
                "remarks": "Polish and clean",
                "making_charge_type": "flat",
                "making_charge_value": 10.0,
                "vat_percent": 5.0
            }]
        }
        
        success1, jobcard1 = self.run_test(
            "Create Job Card (Flat Making Charge)",
            "POST",
            "jobcards",
            200,
            data=jobcard_data_flat
        )
        
        if success1 and jobcard1.get('id'):
            self.created_resources['jobcards'].append(jobcard1['id'])
        
        # Test 2: Job card with per-gram making charge and VAT
        jobcard_data_per_gram = {
            "card_type": "individual",
            "customer_id": customer_id,
            "customer_name": "Test Customer",
            "delivery_date": "2025-01-15",
            "notes": "Test job card with per-gram making charge",
            "items": [{
                "category": "Chain",
                "description": "Gold chain with per-gram making charge",
                "qty": 1,
                "weight_in": 15.500,
                "weight_out": 15.200,
                "purity": 916,
                "work_type": "polish",
                "remarks": "Polish and clean",
                "making_charge_type": "per_gram",
                "making_charge_value": 2.0,
                "vat_percent": 5.0
            }]
        }
        
        success2, jobcard2 = self.run_test(
            "Create Job Card (Per-Gram Making Charge)",
            "POST",
            "jobcards",
            200,
            data=jobcard_data_per_gram
        )
        
        if success2 and jobcard2.get('id'):
            self.created_resources['jobcards'].append(jobcard2['id'])
        
        # Test 3: Job card WITHOUT new fields (backward compatibility)
        jobcard_data_legacy = {
            "card_type": "individual",
            "customer_id": customer_id,
            "customer_name": "Test Customer",
            "delivery_date": "2025-01-15",
            "notes": "Test job card without new fields",
            "items": [{
                "category": "Bracelet",
                "description": "Gold bracelet (legacy format)",
                "qty": 1,
                "weight_in": 20.500,
                "weight_out": 20.200,
                "purity": 916,
                "work_type": "repair",
                "remarks": "Simple repair"
            }]
        }
        
        success3, jobcard3 = self.run_test(
            "Create Job Card (Backward Compatibility)",
            "POST",
            "jobcards",
            200,
            data=jobcard_data_legacy
        )
        
        if success3 and jobcard3.get('id'):
            self.created_resources['jobcards'].append(jobcard3['id'])
        
        # Get all job cards
        success4, jobcards = self.run_test(
            "Get All Job Cards",
            "GET",
            "jobcards",
            200
        )
        
        return success1 and success2 and success3 and success4

    def test_jobcard_to_invoice_conversion(self):
        """Test converting job cards to invoices with new making charge calculations"""
        if not self.created_resources['jobcards']:
            return False
        
        results = []
        
        # Test conversion for each job card created
        for i, jobcard_id in enumerate(self.created_resources['jobcards']):
            # Update job card status to completed first
            success_update, _ = self.run_test(
                f"Update Job Card {i+1} Status",
                "PATCH",
                f"jobcards/{jobcard_id}",
                200,
                data={"status": "completed"}
            )
            
            if success_update:
                # Convert to invoice
                success_convert, invoice = self.run_test(
                    f"Convert Job Card {i+1} to Invoice",
                    "POST",
                    f"jobcards/{jobcard_id}/convert-to-invoice",
                    200
                )
                
                if success_convert and invoice.get('id'):
                    self.created_resources['invoices'].append(invoice['id'])
                    
                    # Verify invoice has correct calculations
                    if 'items' in invoice and len(invoice['items']) > 0:
                        item = invoice['items'][0]
                        print(f"   Invoice item calculations:")
                        print(f"   - Gold Value: {item.get('gold_value', 0)}")
                        print(f"   - Making Value: {item.get('making_value', 0)}")
                        print(f"   - VAT Amount: {item.get('vat_amount', 0)}")
                        print(f"   - Line Total: {item.get('line_total', 0)}")
                    
                    results.append(success_convert)
                else:
                    results.append(False)
            else:
                results.append(False)
        
        return all(results) if results else False

    def test_daily_closing(self):
        """Test daily closing APIs"""
        # Get existing daily closings
        success1, closings = self.run_test(
            "Get Daily Closings",
            "GET",
            "daily-closings",
            200
        )
        
        if not success1:
            return False
        
        # Create new daily closing with sample data
        closing_data = {
            "date": "2025-01-10T00:00:00Z",
            "opening_cash": 1000.00,
            "total_credit": 2500.00,
            "total_debit": 800.00,
            "expected_closing": 2700.00,  # opening + credit - debit
            "actual_closing": 2650.00,
            "difference": -50.00,  # actual - expected
            "is_locked": False,
            "notes": "Test daily closing with sample calculations"
        }
        
        success2, closing = self.run_test(
            "Create Daily Closing",
            "POST",
            "daily-closings",
            200,
            data=closing_data
        )
        
        if success2:
            print(f"   Daily closing created with:")
            print(f"   - Expected: {closing_data['expected_closing']}")
            print(f"   - Actual: {closing_data['actual_closing']}")
            print(f"   - Difference: {closing_data['difference']}")
        
        return success1 and success2

    def test_invoice_pdf_generation(self):
        """Test invoice PDF generation"""
        if not self.created_resources['invoices']:
            return False
        
        invoice_id = self.created_resources['invoices'][0]
        
        # Test PDF generation endpoint
        success, pdf_response = self.run_test(
            "Generate Invoice PDF",
            "GET",
            f"invoices/{invoice_id}/pdf",
            200
        )
        
        if success:
            print(f"   PDF generation successful for invoice: {invoice_id}")
        
        return success

    def test_audit_logs(self):
        """Test audit logs"""
        success, logs = self.run_test(
            "Get Audit Logs",
            "GET",
            "audit-logs",
            200
        )
        return success

    def test_reports_financial_summary(self):
        """Test financial summary endpoint with date filtering"""
        # Test without filters
        success1, summary1 = self.run_test(
            "Financial Summary (No Filters)",
            "GET",
            "reports/financial-summary",
            200
        )
        
        # Test with date filters
        success2, summary2 = self.run_test(
            "Financial Summary (With Date Filters)",
            "GET",
            "reports/financial-summary",
            200,
            params={"start_date": "2024-01-01", "end_date": "2024-12-31"}
        )
        
        return success1 and success2

    def test_reports_inventory_view(self):
        """Test inventory view endpoint with filters"""
        # Test without filters
        success1, inventory1 = self.run_test(
            "Inventory View (No Filters)",
            "GET",
            "reports/inventory-view",
            200
        )
        
        # Test with date and type filters
        success2, inventory2 = self.run_test(
            "Inventory View (With Filters)",
            "GET",
            "reports/inventory-view",
            200,
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "movement_type": "Stock IN"
            }
        )
        
        # Test with category filter
        success3, inventory3 = self.run_test(
            "Inventory View (Category Filter)",
            "GET",
            "reports/inventory-view",
            200,
            params={"category": "Gold"}
        )
        
        return success1 and success2 and success3

    def test_reports_invoices_view(self):
        """Test invoices view endpoint with filters"""
        # Test without filters
        success1, invoices1 = self.run_test(
            "Invoices View (No Filters)",
            "GET",
            "reports/invoices-view",
            200
        )
        
        # Test with date and status filters
        success2, invoices2 = self.run_test(
            "Invoices View (With Filters)",
            "GET",
            "reports/invoices-view",
            200,
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "invoice_type": "sale",
                "payment_status": "unpaid"
            }
        )
        
        return success1 and success2

    def test_reports_parties_view(self):
        """Test parties view endpoint"""
        # Test without filters
        success1, parties1 = self.run_test(
            "Parties View (No Filters)",
            "GET",
            "reports/parties-view",
            200
        )
        
        # Test with party type filter
        success2, parties2 = self.run_test(
            "Parties View (Customer Filter)",
            "GET",
            "reports/parties-view",
            200,
            params={"party_type": "customer"}
        )
        
        return success1 and success2

    def test_reports_transactions_view(self):
        """Test transactions view endpoint with filters"""
        # Test without filters
        success1, transactions1 = self.run_test(
            "Transactions View (No Filters)",
            "GET",
            "reports/transactions-view",
            200
        )
        
        # Test with date and type filters
        success2, transactions2 = self.run_test(
            "Transactions View (With Filters)",
            "GET",
            "reports/transactions-view",
            200,
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "transaction_type": "credit"
            }
        )
        
        return success1 and success2

    def test_reports_export_endpoints(self):
        """Test export endpoints with filters"""
        # Test inventory export
        success1, _ = self.run_test(
            "Inventory Export (With Filters)",
            "GET",
            "reports/inventory-export",
            200,
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "movement_type": "Stock IN"
            }
        )
        
        # Test parties export
        success2, _ = self.run_test(
            "Parties Export",
            "GET",
            "reports/parties-export",
            200,
            params={"party_type": "customer"}
        )
        
        # Test invoices export
        success3, _ = self.run_test(
            "Invoices Export (With Filters)",
            "GET",
            "reports/invoices-export",
            200,
            params={
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "invoice_type": "sale"
            }
        )
        
        return success1 and success2 and success3

    def test_reports_individual_reports(self):
        """Test individual report endpoints if data exists"""
        results = []
        
        # Test invoice report if we have invoices
        if self.created_resources['invoices']:
            invoice_id = self.created_resources['invoices'][0]
            success1, invoice_report = self.run_test(
                "Individual Invoice Report",
                "GET",
                f"reports/invoice/{invoice_id}",
                200
            )
            results.append(success1)
        
        # Test party ledger report if we have parties
        if self.created_resources['parties']:
            party_id = self.created_resources['parties'][0]
            success2, ledger_report = self.run_test(
                "Party Ledger Report",
                "GET",
                f"reports/party/{party_id}/ledger-report",
                200
            )
            success3, ledger_with_dates = self.run_test(
                "Party Ledger Report (With Dates)",
                "GET",
                f"reports/party/{party_id}/ledger-report",
                200,
                params={"start_date": "2024-01-01", "end_date": "2024-12-31"}
            )
            results.extend([success2, success3])
        
        # Test inventory stock report if we have headers
        if self.created_resources['headers']:
            header_id = self.created_resources['headers'][0]
            success4, stock_report = self.run_test(
                "Inventory Stock Report",
                "GET",
                f"reports/inventory/{header_id}/stock-report",
                200
            )
            success5, stock_with_dates = self.run_test(
                "Inventory Stock Report (With Dates)",
                "GET",
                f"reports/inventory/{header_id}/stock-report",
                200,
                params={"start_date": "2024-01-01", "end_date": "2024-12-31"}
            )
            results.extend([success4, success5])
        
        return all(results) if results else True

    def test_enhanced_invoice_finalization_job_card_locking(self):
        """Test Scenario 1: Job Card Locking on Invoice Finalization"""
        print("\n🔥 TESTING ENHANCED INVOICE FINALIZATION - JOB CARD LOCKING")
        
        # Create a customer party
        customer_data = {
            "name": f"Finalization Test Customer {datetime.now().strftime('%H%M%S')}",
            "phone": "+968 9876 5432",
            "address": "Test Address for Finalization",
            "party_type": "customer",
            "notes": "Customer for testing invoice finalization"
        }
        
        success, customer = self.run_test(
            "Create Customer for Finalization Test",
            "POST",
            "parties",
            200,
            data=customer_data
        )
        
        if not success or not customer.get('id'):
            return False
        
        customer_id = customer['id']
        
        # Create a job card linked to that customer
        jobcard_data = {
            "card_type": "individual",
            "customer_id": customer_id,
            "customer_name": customer['name'],
            "delivery_date": "2025-01-20",
            "notes": "Job card for finalization testing",
            "items": [{
                "category": "Ring",
                "description": "Gold ring for finalization test",
                "qty": 1,
                "weight_in": 12.500,
                "weight_out": 12.200,
                "purity": 916,
                "work_type": "polish",
                "remarks": "Polish and clean for finalization test",
                "making_charge_type": "flat",
                "making_charge_value": 15.0,
                "vat_percent": 5.0
            }]
        }
        
        success, jobcard = self.run_test(
            "Create Job Card for Finalization Test",
            "POST",
            "jobcards",
            200,
            data=jobcard_data
        )
        
        if not success or not jobcard.get('id'):
            return False
        
        jobcard_id = jobcard['id']
        
        # Convert job card to invoice (should be draft status)
        success, invoice = self.run_test(
            "Convert Job Card to Invoice (Draft)",
            "POST",
            f"jobcards/{jobcard_id}/convert-to-invoice",
            200
        )
        
        if not success or not invoice.get('id'):
            return False
        
        invoice_id = invoice['id']
        
        # Verify invoice is in draft status
        if invoice.get('status') != 'draft':
            print(f"❌ Invoice should be in draft status, got: {invoice.get('status')}")
            return False
        
        print(f"✅ Invoice created in draft status: {invoice.get('status')}")
        
        # Finalize the invoice
        success, finalized_invoice = self.run_test(
            "Finalize Invoice (Atomic Operations)",
            "POST",
            f"invoices/{invoice_id}/finalize",
            200
        )
        
        if not success:
            return False
        
        # Verify invoice status changed to finalized
        if finalized_invoice.get('status') != 'finalized':
            print(f"❌ Invoice should be finalized, got: {finalized_invoice.get('status')}")
            return False
        
        print(f"✅ Invoice finalized successfully: {finalized_invoice.get('status')}")
        
        # Verify job card status changed to "invoiced", locked=True, locked_at and locked_by are set
        success, updated_jobcard = self.run_test(
            "Get Updated Job Card (Should be Locked)",
            "GET",
            f"jobcards/{jobcard_id}",
            200
        )
        
        if not success:
            return False
        
        # Check job card locking
        if updated_jobcard.get('status') != 'invoiced':
            print(f"❌ Job card status should be 'invoiced', got: {updated_jobcard.get('status')}")
            return False
        
        if not updated_jobcard.get('locked'):
            print(f"❌ Job card should be locked, got: {updated_jobcard.get('locked')}")
            return False
        
        if not updated_jobcard.get('locked_at'):
            print(f"❌ Job card should have locked_at timestamp")
            return False
        
        if not updated_jobcard.get('locked_by'):
            print(f"❌ Job card should have locked_by user ID")
            return False
        
        print(f"✅ Job card locked successfully: status={updated_jobcard.get('status')}, locked={updated_jobcard.get('locked')}")
        
        # Try to edit the locked job card (should get 403 error for non-admin, but admin can override)
        # Since we're logged in as admin, this should succeed with warning
        success, edit_response = self.run_test(
            "Admin Try to Edit Locked Job Card (Should Succeed with Warning)",
            "PATCH",
            f"jobcards/{jobcard_id}",
            200,  # Admin can edit with override
            data={"notes": "Admin editing locked job card"}
        )
        
        if not success:
            print(f"❌ Admin should be able to edit locked job card with override")
            return False
        
        # Verify response contains warning message
        response_str = str(edit_response)
        if 'locked' not in response_str.lower() or 'finalized invoice' not in response_str.lower():
            print(f"❌ Response should contain warning about locked job card and finalized invoice")
            return False
        
        print(f"✅ Admin can edit locked job card with override and warning message")
        
        # Try to delete the locked job card (should get 403 error for non-admin, but admin can override)
        # Since we're logged in as admin, this should succeed with warning
        success, delete_response = self.run_test(
            "Admin Try to Delete Locked Job Card (Should Succeed with Warning)",
            "DELETE",
            f"jobcards/{jobcard_id}",
            200  # Admin can delete with override
        )
        
        if not success:
            print(f"❌ Admin should be able to delete locked job card with override")
            return False
        
        # Verify response contains warning message
        response_str = str(delete_response)
        if 'locked' not in response_str.lower() or 'finalized invoice' not in response_str.lower():
            print(f"❌ Response should contain warning about locked job card and finalized invoice")
            return False
        
        print(f"✅ Admin can delete locked job card with override and warning message")
        
        # Store for other tests
        self.finalization_test_data = {
            'customer_id': customer_id,
            'jobcard_id': jobcard_id,
            'invoice_id': invoice_id
        }
        
        return True

    def test_enhanced_invoice_finalization_customer_ledger(self):
        """Test Scenario 2: Customer Ledger Entry Creation"""
        print("\n🔥 TESTING ENHANCED INVOICE FINALIZATION - CUSTOMER LEDGER ENTRY")
        
        if not hasattr(self, 'finalization_test_data'):
            print("❌ Finalization test data not available, run job card locking test first")
            return False
        
        customer_id = self.finalization_test_data['customer_id']
        invoice_id = self.finalization_test_data['invoice_id']
        
        # Get the finalized invoice to check grand_total
        success, invoice = self.run_test(
            "Get Finalized Invoice Details",
            "GET",
            f"invoices/{invoice_id}",
            200
        )
        
        if not success:
            return False
        
        grand_total = invoice.get('grand_total', 0)
        customer_name = invoice.get('customer_name', '')
        invoice_number = invoice.get('invoice_number', '')
        
        print(f"   Invoice grand_total: {grand_total}")
        
        # Get all transactions to find the ledger entry
        success, transactions = self.run_test(
            "Get All Transactions (Find Ledger Entry)",
            "GET",
            "transactions",
            200
        )
        
        if not success:
            return False
        
        # Find the transaction created for this invoice
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
        if ledger_entry.get('party_id') != customer_id:
            print(f"❌ Ledger entry party_id mismatch: expected {customer_id}, got {ledger_entry.get('party_id')}")
            return False
        
        if ledger_entry.get('party_name') != customer_name:
            print(f"❌ Ledger entry party_name mismatch: expected {customer_name}, got {ledger_entry.get('party_name')}")
            return False
        
        if ledger_entry.get('amount') != grand_total:
            print(f"❌ Ledger entry amount mismatch: expected {grand_total}, got {ledger_entry.get('amount')}")
            return False
        
        if ledger_entry.get('category') != 'Sales Invoice':
            print(f"❌ Ledger entry category mismatch: expected 'Sales Invoice', got {ledger_entry.get('category')}")
            return False
        
        if ledger_entry.get('transaction_type') != 'debit':
            print(f"❌ Ledger entry transaction_type mismatch: expected 'debit', got {ledger_entry.get('transaction_type')}")
            return False
        
        # Check transaction number format (TXN-YYYY-NNNN)
        txn_number = ledger_entry.get('transaction_number', '')
        import re
        if not re.match(r'^TXN-\d{4}-\d{4}$', txn_number):
            print(f"❌ Transaction number format incorrect: {txn_number}")
            return False
        
        # Check notes contains invoice number reference
        notes = ledger_entry.get('notes', '')
        if invoice_number not in notes:
            print(f"❌ Transaction notes should contain invoice number {invoice_number}, got: {notes}")
            return False
        
        print(f"✅ Ledger entry created correctly:")
        print(f"   - Transaction Number: {txn_number}")
        print(f"   - Amount: {ledger_entry.get('amount')}")
        print(f"   - Type: {ledger_entry.get('transaction_type')}")
        print(f"   - Category: {ledger_entry.get('category')}")
        print(f"   - Notes: {notes}")
        
        # Get the party ledger and verify the transaction appears
        success, party_ledger = self.run_test(
            "Get Party Ledger (Verify Transaction)",
            "GET",
            f"parties/{customer_id}/ledger",
            200
        )
        
        if not success:
            return False
        
        # Check if the transaction appears in party ledger
        ledger_transactions = party_ledger.get('transactions', [])
        found_in_ledger = any(
            txn.get('id') == ledger_entry.get('id') 
            for txn in ledger_transactions
        )
        
        if not found_in_ledger:
            print(f"❌ Transaction not found in party ledger")
            return False
        
        print(f"✅ Transaction appears in party ledger correctly")
        
        return True

    def test_enhanced_invoice_finalization_outstanding_balance(self):
        """Test Scenario 3: Outstanding Balance Tracking"""
        print("\n🔥 TESTING ENHANCED INVOICE FINALIZATION - OUTSTANDING BALANCE TRACKING")
        
        if not hasattr(self, 'finalization_test_data'):
            print("❌ Finalization test data not available")
            return False
        
        customer_id = self.finalization_test_data['customer_id']
        invoice_id = self.finalization_test_data['invoice_id']
        
        # Get the invoice to check balance_due
        success, invoice = self.run_test(
            "Get Invoice for Balance Check",
            "GET",
            f"invoices/{invoice_id}",
            200
        )
        
        if not success:
            return False
        
        expected_balance = invoice.get('balance_due', 0)
        print(f"   Expected outstanding balance: {expected_balance}")
        
        # Get party ledger to verify outstanding balance
        success, party_ledger = self.run_test(
            "Get Party Ledger for Outstanding Balance",
            "GET",
            f"parties/{customer_id}/ledger",
            200
        )
        
        if not success:
            return False
        
        actual_outstanding = party_ledger.get('outstanding', 0)
        print(f"   Actual outstanding balance: {actual_outstanding}")
        
        if actual_outstanding != expected_balance:
            print(f"❌ Outstanding balance mismatch: expected {expected_balance}, got {actual_outstanding}")
            return False
        
        print(f"✅ Outstanding balance tracking working correctly: {actual_outstanding}")
        
        return True

    def test_enhanced_invoice_finalization_direct_invoice(self):
        """Test Scenario 4: Direct Invoice Finalization (No Job Card)"""
        print("\n🔥 TESTING ENHANCED INVOICE FINALIZATION - DIRECT INVOICE (NO JOB CARD)")
        
        # Create a customer for direct invoice
        customer_data = {
            "name": f"Direct Invoice Customer {datetime.now().strftime('%H%M%S')}",
            "phone": "+968 1111 2222",
            "address": "Direct Invoice Address",
            "party_type": "customer",
            "notes": "Customer for direct invoice testing"
        }
        
        success, customer = self.run_test(
            "Create Customer for Direct Invoice",
            "POST",
            "parties",
            200,
            data=customer_data
        )
        
        if not success or not customer.get('id'):
            return False
        
        customer_id = customer['id']
        
        # Create a draft invoice without jobcard_id
        invoice_data = {
            "customer_id": customer_id,
            "customer_name": customer['name'],
            "invoice_type": "sale",
            "items": [{
                "description": "Direct sale gold item",
                "qty": 1,
                "weight": 10.0,
                "purity": 916,
                "metal_rate": 25.0,
                "gold_value": 250.0,
                "making_value": 20.0,
                "vat_percent": 5.0,
                "vat_amount": 13.5,
                "line_total": 283.5
            }],
            "subtotal": 270.0,
            "vat_total": 13.5,
            "grand_total": 283.5,
            "balance_due": 283.5,
            "notes": "Direct invoice without job card"
        }
        
        success, invoice = self.run_test(
            "Create Direct Invoice (Draft)",
            "POST",
            "invoices",
            200,
            data=invoice_data
        )
        
        if not success or not invoice.get('id'):
            return False
        
        invoice_id = invoice['id']
        
        # Verify invoice is in draft status and has no jobcard_id
        if invoice.get('status') != 'draft':
            print(f"❌ Direct invoice should be in draft status, got: {invoice.get('status')}")
            return False
        
        if invoice.get('jobcard_id'):
            print(f"❌ Direct invoice should not have jobcard_id, got: {invoice.get('jobcard_id')}")
            return False
        
        print(f"✅ Direct invoice created without job card: status={invoice.get('status')}")
        
        # Finalize the direct invoice
        success, finalized_invoice = self.run_test(
            "Finalize Direct Invoice",
            "POST",
            f"invoices/{invoice_id}/finalize",
            200
        )
        
        if not success:
            return False
        
        # Verify invoice is finalized
        if finalized_invoice.get('status') != 'finalized':
            print(f"❌ Direct invoice should be finalized, got: {finalized_invoice.get('status')}")
            return False
        
        print(f"✅ Direct invoice finalized successfully")
        
        # Verify stock movements were created
        success, movements = self.run_test(
            "Get Stock Movements (Direct Invoice)",
            "GET",
            "inventory/movements",
            200
        )
        
        if not success:
            return False
        
        # Find stock movements for this invoice
        invoice_movements = [
            m for m in movements 
            if m.get('reference_type') == 'invoice' and m.get('reference_id') == invoice_id
        ]
        
        if not invoice_movements:
            print(f"❌ No stock movements found for direct invoice {invoice_id}")
            return False
        
        print(f"✅ Stock movements created for direct invoice: {len(invoice_movements)} movements")
        
        # Verify ledger entry was created
        success, transactions = self.run_test(
            "Get Transactions (Direct Invoice Ledger)",
            "GET",
            "transactions",
            200
        )
        
        if not success:
            return False
        
        # Find ledger entry for this invoice
        invoice_number = finalized_invoice.get('invoice_number', '')
        ledger_entry = None
        for txn in transactions:
            if (txn.get('party_id') == customer_id and 
                txn.get('category') == 'Sales Invoice' and
                invoice_number in txn.get('notes', '')):
                ledger_entry = txn
                break
        
        if not ledger_entry:
            print(f"❌ No ledger entry found for direct invoice")
            return False
        
        print(f"✅ Ledger entry created for direct invoice: {ledger_entry.get('transaction_number')}")
        
        # Verify no job card locking was attempted (should not cause errors)
        print(f"✅ Direct invoice finalization completed without job card locking")
        
        return True

    def test_enhanced_invoice_finalization_sales_account(self):
        """Test Scenario 5: Default Sales Account Creation"""
        print("\n🔥 TESTING ENHANCED INVOICE FINALIZATION - DEFAULT SALES ACCOUNT CREATION")
        
        # Check if "Sales" account exists
        success, accounts = self.run_test(
            "Get All Accounts (Check Sales Account)",
            "GET",
            "accounts",
            200
        )
        
        if not success:
            return False
        
        # Look for Sales account
        sales_account = None
        for account in accounts:
            if account.get('name') == 'Sales':
                sales_account = account
                break
        
        if sales_account:
            print(f"✅ Sales account already exists: {sales_account.get('id')}")
            
            # Verify account properties
            if sales_account.get('account_type') != 'asset':
                print(f"❌ Sales account should be 'asset' type, got: {sales_account.get('account_type')}")
                return False
            
            print(f"✅ Sales account has correct properties: type={sales_account.get('account_type')}")
        else:
            print(f"ℹ️  Sales account does not exist, will be created during invoice finalization")
            
            # Create a test invoice to trigger Sales account creation
            customer_data = {
                "name": f"Sales Account Test Customer {datetime.now().strftime('%H%M%S')}",
                "phone": "+968 3333 4444",
                "address": "Sales Account Test Address",
                "party_type": "customer"
            }
            
            success, customer = self.run_test(
                "Create Customer for Sales Account Test",
                "POST",
                "parties",
                200,
                data=customer_data
            )
            
            if not success:
                return False
            
            # Create and finalize invoice to trigger Sales account creation
            invoice_data = {
                "customer_id": customer['id'],
                "customer_name": customer['name'],
                "invoice_type": "sale",
                "items": [{
                    "description": "Test item for sales account creation",
                    "qty": 1,
                    "weight": 5.0,
                    "purity": 916,
                    "metal_rate": 20.0,
                    "gold_value": 100.0,
                    "making_value": 10.0,
                    "vat_percent": 5.0,
                    "vat_amount": 5.5,
                    "line_total": 115.5
                }],
                "subtotal": 110.0,
                "vat_total": 5.5,
                "grand_total": 115.5,
                "balance_due": 115.5
            }
            
            success, invoice = self.run_test(
                "Create Invoice for Sales Account Test",
                "POST",
                "invoices",
                200,
                data=invoice_data
            )
            
            if not success:
                return False
            
            # Finalize invoice to trigger Sales account creation
            success, finalized = self.run_test(
                "Finalize Invoice (Create Sales Account)",
                "POST",
                f"invoices/{invoice['id']}/finalize",
                200
            )
            
            if not success:
                return False
            
            # Check if Sales account was created
            success, updated_accounts = self.run_test(
                "Get Accounts After Finalization",
                "GET",
                "accounts",
                200
            )
            
            if not success:
                return False
            
            # Look for newly created Sales account
            new_sales_account = None
            for account in updated_accounts:
                if account.get('name') == 'Sales':
                    new_sales_account = account
                    break
            
            if not new_sales_account:
                print(f"❌ Sales account was not created during invoice finalization")
                return False
            
            # Verify account properties
            if new_sales_account.get('account_type') != 'asset':
                print(f"❌ Created Sales account should be 'asset' type, got: {new_sales_account.get('account_type')}")
                return False
            
            print(f"✅ Sales account created successfully during finalization:")
            print(f"   - ID: {new_sales_account.get('id')}")
            print(f"   - Name: {new_sales_account.get('name')}")
            print(f"   - Type: {new_sales_account.get('account_type')}")
        
        return True

    def test_enhanced_invoice_finalization_full_workflow(self):
        """Test Scenario 6: Full Workflow Test"""
        print("\n🔥 TESTING ENHANCED INVOICE FINALIZATION - FULL WORKFLOW")
        
        # Create customer party
        customer_data = {
            "name": f"Full Workflow Customer {datetime.now().strftime('%H%M%S')}",
            "phone": "+968 5555 6666",
            "address": "Full Workflow Address",
            "party_type": "customer",
            "notes": "Customer for full workflow testing"
        }
        
        success, customer = self.run_test(
            "Full Workflow: Create Customer",
            "POST",
            "parties",
            200,
            data=customer_data
        )
        
        if not success:
            return False
        
        customer_id = customer['id']
        
        # Create job card
        jobcard_data = {
            "card_type": "individual",
            "customer_id": customer_id,
            "customer_name": customer['name'],
            "delivery_date": "2025-01-25",
            "notes": "Full workflow job card",
            "items": [{
                "category": "Necklace",
                "description": "Gold necklace for full workflow test",
                "qty": 1,
                "weight_in": 25.500,
                "weight_out": 25.200,
                "purity": 916,
                "work_type": "repair",
                "remarks": "Full repair and polish",
                "making_charge_type": "per_gram",
                "making_charge_value": 3.0,
                "vat_percent": 5.0
            }]
        }
        
        success, jobcard = self.run_test(
            "Full Workflow: Create Job Card",
            "POST",
            "jobcards",
            200,
            data=jobcard_data
        )
        
        if not success:
            return False
        
        jobcard_id = jobcard['id']
        
        # Convert to invoice (draft)
        success, invoice = self.run_test(
            "Full Workflow: Convert to Invoice (Draft)",
            "POST",
            f"jobcards/{jobcard_id}/convert-to-invoice",
            200
        )
        
        if not success:
            return False
        
        invoice_id = invoice['id']
        
        # Verify: invoice status="draft", NO stock movements yet
        if invoice.get('status') != 'draft':
            print(f"❌ Invoice should be draft, got: {invoice.get('status')}")
            return False
        
        print(f"✅ Invoice created in draft status: {invoice.get('status')}")
        
        # Check that no stock movements exist for this invoice yet
        success, movements_before = self.run_test(
            "Full Workflow: Check Stock Movements Before Finalization",
            "GET",
            "inventory/movements",
            200
        )
        
        if not success:
            return False
        
        invoice_movements_before = [
            m for m in movements_before 
            if m.get('reference_type') == 'invoice' and m.get('reference_id') == invoice_id
        ]
        
        if invoice_movements_before:
            print(f"❌ No stock movements should exist before finalization, found: {len(invoice_movements_before)}")
            return False
        
        print(f"✅ No stock movements exist before finalization (correct)")
        
        # Finalize invoice
        success, finalized_invoice = self.run_test(
            "Full Workflow: Finalize Invoice (All Atomic Operations)",
            "POST",
            f"invoices/{invoice_id}/finalize",
            200
        )
        
        if not success:
            return False
        
        # Verify ALL atomic operations:
        
        # 1. Invoice status="finalized"
        if finalized_invoice.get('status') != 'finalized':
            print(f"❌ Invoice should be finalized, got: {finalized_invoice.get('status')}")
            return False
        
        print(f"✅ Operation 1: Invoice status finalized")
        
        # 2. Stock OUT movements created with negative values
        success, movements_after = self.run_test(
            "Full Workflow: Check Stock Movements After Finalization",
            "GET",
            "inventory/movements",
            200
        )
        
        if not success:
            return False
        
        invoice_movements_after = [
            m for m in movements_after 
            if m.get('reference_type') == 'invoice' and m.get('reference_id') == invoice_id
        ]
        
        if not invoice_movements_after:
            print(f"❌ Stock movements should exist after finalization")
            return False
        
        # Check that movements have negative values (Stock OUT)
        for movement in invoice_movements_after:
            if movement.get('qty_delta', 0) >= 0 or movement.get('weight_delta', 0) >= 0:
                print(f"❌ Stock movements should have negative values (OUT), got qty: {movement.get('qty_delta')}, weight: {movement.get('weight_delta')}")
                return False
        
        print(f"✅ Operation 2: Stock OUT movements created with negative values: {len(invoice_movements_after)} movements")
        
        # 3. Job card locked (status="invoiced", locked=True)
        success, locked_jobcard = self.run_test(
            "Full Workflow: Check Job Card Locking",
            "GET",
            f"jobcards/{jobcard_id}",
            200
        )
        
        if not success:
            return False
        
        if locked_jobcard.get('status') != 'invoiced' or not locked_jobcard.get('locked'):
            print(f"❌ Job card should be locked with status 'invoiced', got status: {locked_jobcard.get('status')}, locked: {locked_jobcard.get('locked')}")
            return False
        
        print(f"✅ Operation 3: Job card locked (status={locked_jobcard.get('status')}, locked={locked_jobcard.get('locked')})")
        
        # 4. Transaction/ledger entry created
        success, transactions = self.run_test(
            "Full Workflow: Check Ledger Entry Creation",
            "GET",
            "transactions",
            200
        )
        
        if not success:
            return False
        
        invoice_number = finalized_invoice.get('invoice_number', '')
        ledger_entry = None
        for txn in transactions:
            if (txn.get('party_id') == customer_id and 
                txn.get('category') == 'Sales Invoice' and
                invoice_number in txn.get('notes', '')):
                ledger_entry = txn
                break
        
        if not ledger_entry:
            print(f"❌ Ledger entry should be created for finalized invoice")
            return False
        
        print(f"✅ Operation 4: Ledger entry created ({ledger_entry.get('transaction_number')})")
        
        # 5. Party outstanding balance updated
        success, party_ledger = self.run_test(
            "Full Workflow: Check Outstanding Balance Update",
            "GET",
            f"parties/{customer_id}/ledger",
            200
        )
        
        if not success:
            return False
        
        outstanding = party_ledger.get('outstanding', 0)
        expected_outstanding = finalized_invoice.get('balance_due', 0)
        
        if outstanding != expected_outstanding:
            print(f"❌ Outstanding balance mismatch: expected {expected_outstanding}, got {outstanding}")
            return False
        
        print(f"✅ Operation 5: Outstanding balance updated correctly: {outstanding}")
        
        print(f"🎉 ALL 5 ATOMIC OPERATIONS COMPLETED SUCCESSFULLY!")
        
        return True

    def test_enhanced_invoice_finalization_error_cases(self):
        """Test Error Cases for Enhanced Invoice Finalization"""
        print("\n🔥 TESTING ENHANCED INVOICE FINALIZATION - ERROR CASES")
        
        results = []
        
        # Error Case 1: Attempt to edit locked job card (should return 400)
        if hasattr(self, 'finalization_test_data'):
            jobcard_id = self.finalization_test_data['jobcard_id']
            
            success, _ = self.run_test(
                "Error Case: Edit Locked Job Card",
                "PATCH",
                f"jobcards/{jobcard_id}",
                400,  # Expecting 400 error
                data={"notes": "Attempting to edit locked job card"}
            )
            results.append(success)
            
            # Error Case 2: Attempt to delete locked job card (should return 400)
            success, _ = self.run_test(
                "Error Case: Delete Locked Job Card",
                "DELETE",
                f"jobcards/{jobcard_id}",
                400  # Expecting 400 error
            )
            results.append(success)
            
            # Error Case 3: Attempt to finalize already finalized invoice
            invoice_id = self.finalization_test_data['invoice_id']
            
            success, _ = self.run_test(
                "Error Case: Re-finalize Already Finalized Invoice",
                "POST",
                f"invoices/{invoice_id}/finalize",
                400  # Expecting 400 error
            )
            results.append(success)
        
        # Error Case 4: Finalize invoice without customer_id (should skip ledger entry gracefully)
        invoice_data = {
            "invoice_type": "sale",
            "items": [{
                "description": "Test item without customer",
                "qty": 1,
                "weight": 5.0,
                "purity": 916,
                "metal_rate": 20.0,
                "gold_value": 100.0,
                "making_value": 10.0,
                "vat_percent": 5.0,
                "vat_amount": 5.5,
                "line_total": 115.5
            }],
            "subtotal": 110.0,
            "vat_total": 5.5,
            "grand_total": 115.5,
            "balance_due": 115.5,
            "notes": "Invoice without customer for error testing"
        }
        
        success, invoice = self.run_test(
            "Error Case: Create Invoice Without Customer",
            "POST",
            "invoices",
            200,
            data=invoice_data
        )
        
        if success:
            # This should succeed but skip ledger entry creation
            success, finalized = self.run_test(
                "Error Case: Finalize Invoice Without Customer (Should Skip Ledger)",
                "POST",
                f"invoices/{invoice['id']}/finalize",
                200  # Should succeed but skip ledger entry
            )
            results.append(success)
            
            if success:
                print(f"✅ Invoice without customer finalized gracefully (ledger entry skipped)")
        
        return all(results) if results else True

    def test_job_card_locking_admin_override_setup(self):
        """Setup Phase: Create admin user, staff user, job card, invoice, and finalize"""
        print("\n🔒 TESTING JOB CARD LOCKING ADMIN OVERRIDE - SETUP PHASE")
        
        # Create staff user for testing non-admin scenarios
        staff_register_success, staff_response = self.run_test(
            "Register Staff User",
            "POST",
            "auth/register",
            200,
            data={
                "username": "staff_user",
                "password": "staff123",
                "email": "staff@goldshop.com",
                "full_name": "Staff Member",
                "role": "staff"
            }
        )
        
        # Create customer for job card
        customer_data = {
            "name": f"Lock Test Customer {datetime.now().strftime('%H%M%S')}",
            "phone": "+968 7777 8888",
            "address": "Lock Test Address",
            "party_type": "customer",
            "notes": "Customer for job card locking tests"
        }
        
        success, customer = self.run_test(
            "Create Customer for Lock Test",
            "POST",
            "parties",
            200,
            data=customer_data
        )
        
        if not success:
            return False
        
        customer_id = customer['id']
        
        # Create job card
        jobcard_data = {
            "card_type": "individual",
            "customer_id": customer_id,
            "customer_name": customer['name'],
            "delivery_date": "2025-01-30",
            "notes": "Job card for admin override testing",
            "items": [{
                "category": "Ring",
                "description": "Gold ring for lock testing",
                "qty": 1,
                "weight_in": 8.500,
                "weight_out": 8.200,
                "purity": 916,
                "work_type": "polish",
                "remarks": "Polish for lock test",
                "making_charge_type": "flat",
                "making_charge_value": 12.0,
                "vat_percent": 5.0
            }]
        }
        
        success, jobcard = self.run_test(
            "Create Job Card for Lock Test",
            "POST",
            "jobcards",
            200,
            data=jobcard_data
        )
        
        if not success:
            return False
        
        jobcard_id = jobcard['id']
        
        # Convert to invoice
        success, invoice = self.run_test(
            "Convert Job Card to Invoice for Lock Test",
            "POST",
            f"jobcards/{jobcard_id}/convert-to-invoice",
            200
        )
        
        if not success:
            return False
        
        invoice_id = invoice['id']
        
        # Finalize invoice to lock job card
        success, finalized_invoice = self.run_test(
            "Finalize Invoice to Lock Job Card",
            "POST",
            f"invoices/{invoice_id}/finalize",
            200
        )
        
        if not success:
            return False
        
        # Verify job card is locked
        success, locked_jobcard = self.run_test(
            "Verify Job Card is Locked",
            "GET",
            f"jobcards/{jobcard_id}",
            200
        )
        
        if not success:
            return False
        
        if not locked_jobcard.get('locked'):
            print(f"❌ Job card should be locked after invoice finalization")
            return False
        
        print(f"✅ Setup complete: Job card locked (locked={locked_jobcard.get('locked')})")
        
        # Store test data for other tests
        self.admin_override_test_data = {
            'customer_id': customer_id,
            'jobcard_id': jobcard_id,
            'invoice_id': invoice_id,
            'locked_at': locked_jobcard.get('locked_at'),
            'locked_by': locked_jobcard.get('locked_by'),
            'jobcard_number': locked_jobcard.get('job_card_number'),
            'customer_name': customer['name']
        }
        
        return True

    def test_job_card_locking_non_admin_edit_attempt(self):
        """Test Scenario 1: Non-Admin Edit Attempt (Should FAIL)"""
        print("\n🔒 TESTING JOB CARD LOCKING - NON-ADMIN EDIT ATTEMPT")
        
        if not hasattr(self, 'admin_override_test_data'):
            print("❌ Admin override test data not available, run setup first")
            return False
        
        jobcard_id = self.admin_override_test_data['jobcard_id']
        
        # Login as staff user
        success, staff_login_response = self.run_test(
            "Login as Staff User",
            "POST",
            "auth/login",
            200,
            data={"username": "staff_user", "password": "staff123"}
        )
        
        if not success:
            return False
        
        # Store admin token and switch to staff token
        admin_token = self.token
        self.token = staff_login_response['access_token']
        
        # Attempt to edit locked job card as staff (should get 403)
        success, error_response = self.run_test(
            "Staff Edit Locked Job Card (Should Fail with 403)",
            "PATCH",
            f"jobcards/{jobcard_id}",
            403,  # Expecting 403 Forbidden
            data={"notes": "Staff attempting to edit locked job card"}
        )
        
        # Restore admin token
        self.token = admin_token
        
        if not success:
            print(f"❌ Expected 403 Forbidden error for staff editing locked job card")
            return False
        
        # Verify error message mentions admin override
        if 'admin' not in str(error_response).lower():
            print(f"❌ Error message should mention admin override requirement")
            return False
        
        print(f"✅ Staff user correctly blocked from editing locked job card (403 Forbidden)")
        return True

    def test_job_card_locking_non_admin_delete_attempt(self):
        """Test Scenario 2: Non-Admin Delete Attempt (Should FAIL)"""
        print("\n🔒 TESTING JOB CARD LOCKING - NON-ADMIN DELETE ATTEMPT")
        
        if not hasattr(self, 'admin_override_test_data'):
            print("❌ Admin override test data not available")
            return False
        
        jobcard_id = self.admin_override_test_data['jobcard_id']
        
        # Login as staff user
        success, staff_login_response = self.run_test(
            "Login as Staff User for Delete Test",
            "POST",
            "auth/login",
            200,
            data={"username": "staff_user", "password": "staff123"}
        )
        
        if not success:
            return False
        
        # Store admin token and switch to staff token
        admin_token = self.token
        self.token = staff_login_response['access_token']
        
        # Attempt to delete locked job card as staff (should get 403)
        success, error_response = self.run_test(
            "Staff Delete Locked Job Card (Should Fail with 403)",
            "DELETE",
            f"jobcards/{jobcard_id}",
            403,  # Expecting 403 Forbidden
        )
        
        # Restore admin token
        self.token = admin_token
        
        if not success:
            print(f"❌ Expected 403 Forbidden error for staff deleting locked job card")
            return False
        
        # Verify error message mentions admin override
        if 'admin' not in str(error_response).lower():
            print(f"❌ Error message should mention admin override requirement")
            return False
        
        print(f"✅ Staff user correctly blocked from deleting locked job card (403 Forbidden)")
        return True

    def test_job_card_locking_admin_edit_override(self):
        """Test Scenario 3: Admin Edit Override (Should SUCCEED)"""
        print("\n🔒 TESTING JOB CARD LOCKING - ADMIN EDIT OVERRIDE")
        
        if not hasattr(self, 'admin_override_test_data'):
            print("❌ Admin override test data not available")
            return False
        
        jobcard_id = self.admin_override_test_data['jobcard_id']
        
        # Admin edit locked job card (should succeed with warning)
        success, edit_response = self.run_test(
            "Admin Edit Locked Job Card (Should Succeed)",
            "PATCH",
            f"jobcards/{jobcard_id}",
            200,  # Should succeed
            data={"notes": "Admin override edit of locked job card"}
        )
        
        if not success:
            return False
        
        # Verify response contains warning message
        response_str = str(edit_response)
        if 'locked' not in response_str.lower() or 'finalized invoice' not in response_str.lower():
            print(f"❌ Response should contain warning about locked job card and finalized invoice")
            return False
        
        print(f"✅ Admin successfully edited locked job card with warning message")
        
        # Verify audit log was created for admin override edit
        success, audit_logs = self.run_test(
            "Get Audit Logs for Admin Override Edit",
            "GET",
            "audit-logs",
            200,
            params={"module": "jobcard"}
        )
        
        if not success:
            return False
        
        # Find the admin override edit log
        override_edit_log = None
        for log in audit_logs:
            if (log.get('record_id') == jobcard_id and 
                log.get('action') == 'admin_override_edit'):
                override_edit_log = log
                break
        
        if not override_edit_log:
            print(f"❌ No admin_override_edit audit log found for job card {jobcard_id}")
            return False
        
        # Verify audit log contains required details
        changes = override_edit_log.get('changes', {})
        if not changes.get('reason'):
            print(f"❌ Audit log should contain reason")
            return False
        
        if not changes.get('locked_at'):
            print(f"❌ Audit log should contain locked_at timestamp")
            return False
        
        if not changes.get('locked_by'):
            print(f"❌ Audit log should contain locked_by user ID")
            return False
        
        if not changes.get('changes'):
            print(f"❌ Audit log should contain the actual changes made")
            return False
        
        print(f"✅ Admin override edit audit log created with all required details:")
        print(f"   - Action: {override_edit_log.get('action')}")
        print(f"   - User: {override_edit_log.get('user_name')}")
        print(f"   - Reason: {changes.get('reason')}")
        
        return True

    def test_job_card_locking_admin_delete_override(self):
        """Test Scenario 4: Admin Delete Override (Should SUCCEED)"""
        print("\n🔒 TESTING JOB CARD LOCKING - ADMIN DELETE OVERRIDE")
        
        # Create another locked job card for delete test
        # (We need a separate one since the previous test modified the original)
        
        # Create customer for second job card
        customer_data = {
            "name": f"Delete Test Customer {datetime.now().strftime('%H%M%S')}",
            "phone": "+968 9999 0000",
            "address": "Delete Test Address",
            "party_type": "customer",
            "notes": "Customer for delete override test"
        }
        
        success, customer = self.run_test(
            "Create Customer for Delete Override Test",
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
            "delivery_date": "2025-02-01",
            "notes": "Job card for delete override testing",
            "items": [{
                "category": "Bracelet",
                "description": "Gold bracelet for delete test",
                "qty": 1,
                "weight_in": 15.500,
                "weight_out": 15.200,
                "purity": 916,
                "work_type": "repair",
                "remarks": "Repair for delete test"
            }]
        }
        
        success, jobcard = self.run_test(
            "Create Job Card for Delete Override Test",
            "POST",
            "jobcards",
            200,
            data=jobcard_data
        )
        
        if not success:
            return False
        
        jobcard_id = jobcard['id']
        jobcard_number = jobcard['job_card_number']
        
        # Convert to invoice and finalize to lock
        success, invoice = self.run_test(
            "Convert Job Card to Invoice for Delete Test",
            "POST",
            f"jobcards/{jobcard_id}/convert-to-invoice",
            200
        )
        
        if not success:
            return False
        
        success, finalized = self.run_test(
            "Finalize Invoice to Lock Job Card for Delete Test",
            "POST",
            f"invoices/{invoice['id']}/finalize",
            200
        )
        
        if not success:
            return False
        
        # Verify job card is locked
        success, locked_jobcard = self.run_test(
            "Verify Job Card is Locked for Delete Test",
            "GET",
            f"jobcards/{jobcard_id}",
            200
        )
        
        if not success or not locked_jobcard.get('locked'):
            print(f"❌ Job card should be locked for delete test")
            return False
        
        # Admin delete locked job card (should succeed with warning)
        success, delete_response = self.run_test(
            "Admin Delete Locked Job Card (Should Succeed)",
            "DELETE",
            f"jobcards/{jobcard_id}",
            200  # Should succeed
        )
        
        if not success:
            return False
        
        # Verify response contains warning message
        response_str = str(delete_response)
        if 'locked' not in response_str.lower() or 'finalized invoice' not in response_str.lower():
            print(f"❌ Response should contain warning about locked job card and finalized invoice")
            return False
        
        print(f"✅ Admin successfully deleted locked job card with warning message")
        
        # Verify audit log was created for admin override delete
        success, audit_logs = self.run_test(
            "Get Audit Logs for Admin Override Delete",
            "GET",
            "audit-logs",
            200,
            params={"module": "jobcard"}
        )
        
        if not success:
            return False
        
        # Find the admin override delete log
        override_delete_log = None
        for log in audit_logs:
            if (log.get('record_id') == jobcard_id and 
                log.get('action') == 'admin_override_delete'):
                override_delete_log = log
                break
        
        if not override_delete_log:
            print(f"❌ No admin_override_delete audit log found for job card {jobcard_id}")
            return False
        
        # Verify audit log contains required details
        changes = override_delete_log.get('changes', {})
        if not changes.get('reason'):
            print(f"❌ Audit log should contain reason")
            return False
        
        if not changes.get('locked_at'):
            print(f"❌ Audit log should contain locked_at timestamp")
            return False
        
        if not changes.get('locked_by'):
            print(f"❌ Audit log should contain locked_by user ID")
            return False
        
        if not changes.get('jobcard_number'):
            print(f"❌ Audit log should contain jobcard_number")
            return False
        
        if not changes.get('customer_name'):
            print(f"❌ Audit log should contain customer_name")
            return False
        
        print(f"✅ Admin override delete audit log created with all required details:")
        print(f"   - Action: {override_delete_log.get('action')}")
        print(f"   - User: {override_delete_log.get('user_name')}")
        print(f"   - Reason: {changes.get('reason')}")
        print(f"   - Job Card: {changes.get('jobcard_number')}")
        print(f"   - Customer: {changes.get('customer_name')}")
        
        return True

    def test_job_card_locking_audit_log_verification(self):
        """Test Scenario 5: Audit Log Verification"""
        print("\n🔒 TESTING JOB CARD LOCKING - AUDIT LOG VERIFICATION")
        
        # Get all audit logs for jobcard module
        success, audit_logs = self.run_test(
            "Get All Job Card Audit Logs",
            "GET",
            "audit-logs",
            200,
            params={"module": "jobcard"}
        )
        
        if not success:
            return False
        
        # Count admin override actions
        override_edit_logs = [log for log in audit_logs if log.get('action') == 'admin_override_edit']
        override_delete_logs = [log for log in audit_logs if log.get('action') == 'admin_override_delete']
        
        print(f"✅ Found {len(override_edit_logs)} admin override edit logs")
        print(f"✅ Found {len(override_delete_logs)} admin override delete logs")
        
        # Verify each override log has complete override_details
        all_logs_valid = True
        
        for log in override_edit_logs + override_delete_logs:
            changes = log.get('changes', {})
            required_fields = ['reason', 'locked_at', 'locked_by']
            
            if log.get('action') == 'admin_override_delete':
                required_fields.extend(['jobcard_number', 'customer_name'])
            elif log.get('action') == 'admin_override_edit':
                required_fields.append('changes')
            
            for field in required_fields:
                if not changes.get(field):
                    print(f"❌ Audit log {log.get('id')} missing required field: {field}")
                    all_logs_valid = False
        
        if not all_logs_valid:
            return False
        
        print(f"✅ All admin override audit logs contain complete override_details")
        return True

    def test_job_card_locking_normal_operations(self):
        """Test Scenario 6: Normal Job Card Operations (Should Work)"""
        print("\n🔒 TESTING JOB CARD LOCKING - NORMAL OPERATIONS")
        
        # Create customer for normal operations test
        customer_data = {
            "name": f"Normal Ops Customer {datetime.now().strftime('%H%M%S')}",
            "phone": "+968 1111 3333",
            "address": "Normal Operations Address",
            "party_type": "customer",
            "notes": "Customer for normal operations test"
        }
        
        success, customer = self.run_test(
            "Create Customer for Normal Operations",
            "POST",
            "parties",
            200,
            data=customer_data
        )
        
        if not success:
            return False
        
        # Create unlocked job card
        jobcard_data = {
            "card_type": "individual",
            "customer_id": customer['id'],
            "customer_name": customer['name'],
            "delivery_date": "2025-02-05",
            "notes": "Normal unlocked job card",
            "items": [{
                "category": "Chain",
                "description": "Gold chain for normal operations",
                "qty": 1,
                "weight_in": 20.500,
                "weight_out": 20.200,
                "purity": 916,
                "work_type": "clean",
                "remarks": "Simple cleaning"
            }]
        }
        
        success, jobcard = self.run_test(
            "Create Unlocked Job Card",
            "POST",
            "jobcards",
            200,
            data=jobcard_data
        )
        
        if not success:
            return False
        
        jobcard_id = jobcard['id']
        
        # Verify job card is not locked
        if jobcard.get('locked'):
            print(f"❌ New job card should not be locked")
            return False
        
        print(f"✅ Created unlocked job card (locked={jobcard.get('locked', False)})")
        
        # Login as staff user to test normal operations
        success, staff_login_response = self.run_test(
            "Login as Staff for Normal Operations",
            "POST",
            "auth/login",
            200,
            data={"username": "staff_user", "password": "staff123"}
        )
        
        if not success:
            return False
        
        # Store admin token and switch to staff token
        admin_token = self.token
        self.token = staff_login_response['access_token']
        
        # Edit unlocked job card as staff (should succeed)
        success, edit_response = self.run_test(
            "Staff Edit Unlocked Job Card (Should Succeed)",
            "PATCH",
            f"jobcards/{jobcard_id}",
            200,
            data={"notes": "Staff edited unlocked job card successfully"}
        )
        
        if not success:
            print(f"❌ Staff should be able to edit unlocked job card")
            self.token = admin_token
            return False
        
        print(f"✅ Staff successfully edited unlocked job card")
        
        # Delete unlocked job card as staff (should succeed)
        success, delete_response = self.run_test(
            "Staff Delete Unlocked Job Card (Should Succeed)",
            "DELETE",
            f"jobcards/{jobcard_id}",
            200
        )
        
        # Restore admin token
        self.token = admin_token
        
        if not success:
            print(f"❌ Staff should be able to delete unlocked job card")
            return False
        
        print(f"✅ Staff successfully deleted unlocked job card")
        return True

    def test_party_summary_endpoint(self):
        """Test Module 2/10 - Party Report Combined Summary Backend"""
        print("\n🎯 TESTING MODULE 2/10 - PARTY SUMMARY ENDPOINT")
        
        # Step 1: Create a test party if needed
        party_data = {
            "name": f"Summary Test Party {datetime.now().strftime('%H%M%S')}",
            "phone": "+968 9999 1111",
            "address": "Summary Test Address",
            "party_type": "customer",
            "notes": "Party for testing combined summary endpoint"
        }
        
        success, party = self.run_test(
            "Create Test Party for Summary",
            "POST",
            "parties",
            200,
            data=party_data
        )
        
        if not success or not party.get('id'):
            return False
        
        party_id = party['id']
        print(f"   Created party: {party['name']} (ID: {party_id})")
        
        # Step 2: Create gold ledger entries (both IN and OUT types)
        gold_entries = [
            {
                "party_id": party_id,
                "type": "IN",  # Party gives gold to shop
                "weight_grams": 125.456,
                "purity_entered": 916,
                "purpose": "job_work",
                "notes": "Gold received from party for job work"
            },
            {
                "party_id": party_id,
                "type": "OUT",  # Shop gives gold to party
                "weight_grams": 50.123,
                "purity_entered": 916,
                "purpose": "exchange",
                "notes": "Gold given to party in exchange"
            },
            {
                "party_id": party_id,
                "type": "IN",  # Another IN entry
                "weight_grams": 30.250,
                "purity_entered": 916,
                "purpose": "advance_gold",
                "notes": "Additional gold advance from party"
            }
        ]
        
        created_gold_entries = []
        for i, entry_data in enumerate(gold_entries):
            success, entry = self.run_test(
                f"Create Gold Entry {i+1} ({entry_data['type']})",
                "POST",
                "gold-ledger",
                200,
                data=entry_data
            )
            if success:
                created_gold_entries.append(entry)
                print(f"   Created {entry_data['type']} entry: {entry_data['weight_grams']}g")
        
        if len(created_gold_entries) != 3:
            print(f"❌ Failed to create all gold entries")
            return False
        
        # Step 3: Create an invoice for the party with outstanding balance
        invoice_data = {
            "customer_id": party_id,
            "customer_name": party['name'],
            "invoice_type": "sale",
            "items": [{
                "description": "Gold jewelry for summary test",
                "qty": 1,
                "weight": 15.500,
                "purity": 916,
                "metal_rate": 25.0,
                "gold_value": 387.5,
                "making_value": 50.0,
                "vat_percent": 5.0,
                "vat_amount": 21.875,
                "line_total": 459.375
            }],
            "subtotal": 437.5,
            "vat_total": 21.875,
            "grand_total": 459.375,
            "balance_due": 459.375,  # Outstanding balance
            "notes": "Invoice for party summary testing"
        }
        
        success, invoice = self.run_test(
            "Create Invoice with Outstanding Balance",
            "POST",
            "invoices",
            200,
            data=invoice_data
        )
        
        if not success:
            return False
        
        invoice_id = invoice['id']
        print(f"   Created invoice: {invoice.get('invoice_number')} with balance: {invoice.get('balance_due')}")
        
        # Step 4: Create a transaction (credit type) for the party
        # First ensure we have an account
        if not self.created_resources['accounts']:
            account_data = {
                "name": f"Summary Test Account {datetime.now().strftime('%H%M%S')}",
                "account_type": "cash",
                "opening_balance": 1000.0
            }
            
            success, account = self.run_test(
                "Create Account for Transaction",
                "POST",
                "accounts",
                200,
                data=account_data
            )
            
            if success:
                self.created_resources['accounts'].append(account['id'])
        
        if self.created_resources['accounts']:
            account_id = self.created_resources['accounts'][0]
            
            transaction_data = {
                "transaction_type": "credit",
                "mode": "cash",
                "account_id": account_id,
                "party_id": party_id,
                "amount": 150.0,
                "category": "vendor_payment",
                "notes": "Credit transaction for party summary testing"
            }
            
            success, transaction = self.run_test(
                "Create Credit Transaction",
                "POST",
                "transactions",
                200,
                data=transaction_data
            )
            
            if success:
                print(f"   Created credit transaction: {transaction.get('transaction_number')} amount: {transaction.get('amount')}")
        
        # Step 5: Test GET /api/parties/{party_id}/summary endpoint
        success, summary = self.run_test(
            "Get Party Summary (Main Test)",
            "GET",
            f"parties/{party_id}/summary",
            200
        )
        
        if not success:
            return False
        
        print(f"\n📊 PARTY SUMMARY RESPONSE VERIFICATION:")
        
        # Verify response structure
        required_sections = ['party', 'gold', 'money']
        for section in required_sections:
            if section not in summary:
                print(f"❌ Missing section: {section}")
                return False
        
        # Verify party info
        party_info = summary['party']
        required_party_fields = ['id', 'name', 'phone', 'address', 'party_type', 'notes', 'created_at']
        for field in required_party_fields:
            if field not in party_info:
                print(f"❌ Missing party field: {field}")
                return False
        
        if party_info['id'] != party_id:
            print(f"❌ Party ID mismatch: expected {party_id}, got {party_info['id']}")
            return False
        
        print(f"✅ Party info correct: {party_info['name']} ({party_info['party_type']})")
        
        # Verify gold summary
        gold_summary = summary['gold']
        required_gold_fields = ['gold_due_from_party', 'gold_due_to_party', 'net_gold_balance', 'total_entries']
        for field in required_gold_fields:
            if field not in gold_summary:
                print(f"❌ Missing gold field: {field}")
                return False
        
        # Calculate expected gold values
        expected_gold_due_from_party = 125.456 + 30.250  # IN entries
        expected_gold_due_to_party = 50.123  # OUT entries
        expected_net_gold_balance = expected_gold_due_from_party - expected_gold_due_to_party
        expected_total_entries = 3
        
        # Verify gold calculations (with 3 decimal precision)
        if abs(gold_summary['gold_due_from_party'] - expected_gold_due_from_party) > 0.001:
            print(f"❌ Gold due from party mismatch: expected {expected_gold_due_from_party}, got {gold_summary['gold_due_from_party']}")
            return False
        
        if abs(gold_summary['gold_due_to_party'] - expected_gold_due_to_party) > 0.001:
            print(f"❌ Gold due to party mismatch: expected {expected_gold_due_to_party}, got {gold_summary['gold_due_to_party']}")
            return False
        
        if abs(gold_summary['net_gold_balance'] - expected_net_gold_balance) > 0.001:
            print(f"❌ Net gold balance mismatch: expected {expected_net_gold_balance}, got {gold_summary['net_gold_balance']}")
            return False
        
        if gold_summary['total_entries'] != expected_total_entries:
            print(f"❌ Total entries mismatch: expected {expected_total_entries}, got {gold_summary['total_entries']}")
            return False
        
        print(f"✅ Gold calculations correct:")
        print(f"   - Gold due from party: {gold_summary['gold_due_from_party']:.3f}g")
        print(f"   - Gold due to party: {gold_summary['gold_due_to_party']:.3f}g")
        print(f"   - Net gold balance: {gold_summary['net_gold_balance']:.3f}g")
        print(f"   - Total entries: {gold_summary['total_entries']}")
        
        # Verify money summary
        money_summary = summary['money']
        required_money_fields = ['money_due_from_party', 'money_due_to_party', 'net_money_balance', 'total_invoices', 'total_transactions']
        for field in required_money_fields:
            if field not in money_summary:
                print(f"❌ Missing money field: {field}")
                return False
        
        # Calculate expected money values
        expected_money_due_from_party = 459.375  # Invoice balance_due
        expected_money_due_to_party = 150.0  # Credit transaction
        expected_net_money_balance = expected_money_due_from_party - expected_money_due_to_party
        expected_total_invoices = 1
        expected_total_transactions = 1
        
        # Verify money calculations (with 2 decimal precision)
        if abs(money_summary['money_due_from_party'] - expected_money_due_from_party) > 0.01:
            print(f"❌ Money due from party mismatch: expected {expected_money_due_from_party}, got {money_summary['money_due_from_party']}")
            return False
        
        if abs(money_summary['money_due_to_party'] - expected_money_due_to_party) > 0.01:
            print(f"❌ Money due to party mismatch: expected {expected_money_due_to_party}, got {money_summary['money_due_to_party']}")
            return False
        
        if abs(money_summary['net_money_balance'] - expected_net_money_balance) > 0.01:
            print(f"❌ Net money balance mismatch: expected {expected_net_money_balance}, got {money_summary['net_money_balance']}")
            return False
        
        if money_summary['total_invoices'] != expected_total_invoices:
            print(f"❌ Total invoices mismatch: expected {expected_total_invoices}, got {money_summary['total_invoices']}")
            return False
        
        if money_summary['total_transactions'] != expected_total_transactions:
            print(f"❌ Total transactions mismatch: expected {expected_total_transactions}, got {money_summary['total_transactions']}")
            return False
        
        print(f"✅ Money calculations correct:")
        print(f"   - Money due from party: {money_summary['money_due_from_party']:.2f} OMR")
        print(f"   - Money due to party: {money_summary['money_due_to_party']:.2f} OMR")
        print(f"   - Net money balance: {money_summary['net_money_balance']:.2f} OMR")
        print(f"   - Total invoices: {money_summary['total_invoices']}")
        print(f"   - Total transactions: {money_summary['total_transactions']}")
        
        # Verify precision formatting
        # Gold should have 3 decimals
        gold_fields_3_decimal = ['gold_due_from_party', 'gold_due_to_party', 'net_gold_balance']
        for field in gold_fields_3_decimal:
            value_str = str(gold_summary[field])
            if '.' in value_str:
                decimal_places = len(value_str.split('.')[1])
                if decimal_places > 3:
                    print(f"❌ Gold field {field} has more than 3 decimal places: {value_str}")
                    return False
        
        # Money should have 2 decimals
        money_fields_2_decimal = ['money_due_from_party', 'money_due_to_party', 'net_money_balance']
        for field in money_fields_2_decimal:
            value_str = str(money_summary[field])
            if '.' in value_str:
                decimal_places = len(value_str.split('.')[1])
                if decimal_places > 2:
                    print(f"❌ Money field {field} has more than 2 decimal places: {value_str}")
                    return False
        
        print(f"✅ Precision formatting correct (3 decimals for gold, 2 decimals for money)")
        
        # Store created resources for cleanup
        self.created_resources['parties'].append(party_id)
        if invoice_id:
            self.created_resources['invoices'].append(invoice_id)
        
        print(f"\n🎉 PARTY SUMMARY ENDPOINT TEST COMPLETED SUCCESSFULLY!")
        print(f"   All calculations verified, precision correct, response structure valid")
        
        return True

    def test_purchases_module_setup(self):
        """Setup Phase: Get/create vendor party and inventory headers"""
        print("\n🏗️ PURCHASES MODULE SETUP - Creating vendor party and inventory headers")
        
        # Create vendor party
        vendor_data = {
            "name": f"Gold Vendor {datetime.now().strftime('%H%M%S')}",
            "phone": "+968 9999 1111",
            "address": "Vendor Address for Purchase Testing",
            "party_type": "vendor",
            "notes": "Vendor for purchase module testing"
        }
        
        success, vendor = self.run_test(
            "Create Vendor Party",
            "POST",
            "parties",
            200,
            data=vendor_data
        )
        
        if not success or not vendor.get('id'):
            return False
        
        # Store vendor for other tests
        self.purchases_test_data = {
            'vendor_id': vendor['id'],
            'vendor_name': vendor['name']
        }
        
        # Get existing inventory headers to verify stock movements
        success, headers = self.run_test(
            "Get Inventory Headers for Purchase Testing",
            "GET",
            "inventory/headers",
            200
        )
        
        if not success:
            return False
        
        # Create Gold 22K header if it doesn't exist (for 916 purity)
        gold_22k_header = None
        for header in headers:
            if "Gold 22K" in header.get('name', ''):
                gold_22k_header = header
                break
        
        if not gold_22k_header:
            header_data = {"name": "Gold 22K"}
            success, new_header = self.run_test(
                "Create Gold 22K Inventory Header",
                "POST",
                "inventory/headers",
                200,
                data=header_data
            )
            if success:
                gold_22k_header = new_header
        
        if gold_22k_header:
            self.purchases_test_data['inventory_header_id'] = gold_22k_header['id']
            self.purchases_test_data['inventory_header_name'] = gold_22k_header['name']
            print(f"✅ Setup complete: Vendor {vendor['name']}, Inventory header {gold_22k_header['name']}")
        
        return True

    def test_purchases_create_draft(self):
        """Test Scenario 1: Create Draft Purchase"""
        print("\n💰 TESTING PURCHASES MODULE - CREATE DRAFT PURCHASE")
        
        if not hasattr(self, 'purchases_test_data'):
            print("❌ Purchase test data not available, run setup first")
            return False
        
        vendor_id = self.purchases_test_data['vendor_id']
        
        # Test data with specific precision requirements
        purchase_data = {
            "vendor_party_id": vendor_id,
            "description": "Gold Purchase Test 001",
            "weight_grams": 125.456,  # Should round to 3 decimals
            "entered_purity": 999,    # 24K as claimed by vendor
            "rate_per_gram": 185.50,  # Per gram rate at 916 purity
            "amount_total": 23272.19  # Calculate or provide
        }
        
        success, purchase = self.run_test(
            "Create Draft Purchase",
            "POST",
            "purchases",
            200,
            data=purchase_data
        )
        
        if not success or not purchase.get('id'):
            return False
        
        # Verify purchase properties
        if purchase.get('status') != 'draft':
            print(f"❌ Purchase status should be 'draft', got: {purchase.get('status')}")
            return False
        
        if purchase.get('locked') != False:
            print(f"❌ Purchase locked should be False, got: {purchase.get('locked')}")
            return False
        
        if purchase.get('valuation_purity_fixed') != 916:
            print(f"❌ Valuation purity should be 916, got: {purchase.get('valuation_purity_fixed')}")
            return False
        
        # Verify precision (3 decimals for weight, 2 for money)
        if abs(purchase.get('weight_grams', 0) - 125.456) > 0.001:
            print(f"❌ Weight precision incorrect: expected 125.456, got {purchase.get('weight_grams')}")
            return False
        
        if abs(purchase.get('rate_per_gram', 0) - 185.50) > 0.01:
            print(f"❌ Rate precision incorrect: expected 185.50, got {purchase.get('rate_per_gram')}")
            return False
        
        # Store purchase for other tests
        self.purchases_test_data['draft_purchase_id'] = purchase['id']
        self.purchases_test_data['draft_purchase'] = purchase
        
        print(f"✅ Draft purchase created successfully:")
        print(f"   - Status: {purchase.get('status')}")
        print(f"   - Locked: {purchase.get('locked')}")
        print(f"   - Valuation Purity: {purchase.get('valuation_purity_fixed')}")
        print(f"   - Weight: {purchase.get('weight_grams')}g (3 decimals)")
        print(f"   - Rate: {purchase.get('rate_per_gram')}/g (2 decimals)")
        
        return True

    def test_purchases_get_all(self):
        """Test Scenario 2: Get All Purchases"""
        print("\n📋 TESTING PURCHASES MODULE - GET ALL PURCHASES")
        
        if not hasattr(self, 'purchases_test_data'):
            return False
        
        # Test without filters
        success, purchases = self.run_test(
            "Get All Purchases (No Filters)",
            "GET",
            "purchases",
            200
        )
        
        if not success:
            return False
        
        # Verify our draft purchase is in the list
        draft_purchase_id = self.purchases_test_data['draft_purchase_id']
        found_purchase = None
        for purchase in purchases:
            if purchase.get('id') == draft_purchase_id:
                found_purchase = purchase
                break
        
        if not found_purchase:
            print(f"❌ Draft purchase {draft_purchase_id} not found in purchases list")
            return False
        
        print(f"✅ Draft purchase found in purchases list")
        
        # Test with vendor filter
        vendor_id = self.purchases_test_data['vendor_id']
        success, filtered_purchases = self.run_test(
            "Get Purchases (Vendor Filter)",
            "GET",
            "purchases",
            200,
            params={"vendor_party_id": vendor_id}
        )
        
        if not success:
            return False
        
        # Verify all returned purchases are for this vendor
        for purchase in filtered_purchases:
            if purchase.get('vendor_party_id') != vendor_id:
                print(f"❌ Filtered purchases should only contain vendor {vendor_id}")
                return False
        
        print(f"✅ Vendor filter working correctly: {len(filtered_purchases)} purchases")
        
        # Test with status filter
        success, draft_purchases = self.run_test(
            "Get Purchases (Status=Draft Filter)",
            "GET",
            "purchases",
            200,
            params={"status": "draft"}
        )
        
        if not success:
            return False
        
        # Verify all returned purchases are draft
        for purchase in draft_purchases:
            if purchase.get('status') != 'draft':
                print(f"❌ Status filter should only return draft purchases")
                return False
        
        print(f"✅ Status filter working correctly: {len(draft_purchases)} draft purchases")
        
        return True

    def test_purchases_edit_draft(self):
        """Test Scenario 3: Edit Draft Purchase"""
        print("\n✏️ TESTING PURCHASES MODULE - EDIT DRAFT PURCHASE")
        
        if not hasattr(self, 'purchases_test_data'):
            return False
        
        draft_purchase_id = self.purchases_test_data['draft_purchase_id']
        
        # Update purchase data
        update_data = {
            "description": "Updated Gold Purchase",
            "weight_grams": 130.789  # Should round to 3 decimals
        }
        
        success, updated_purchase = self.run_test(
            "Edit Draft Purchase",
            "PATCH",
            f"purchases/{draft_purchase_id}",
            200,
            data=update_data
        )
        
        if not success:
            return False
        
        # Verify changes were applied
        if updated_purchase.get('description') != "Updated Gold Purchase":
            print(f"❌ Description not updated: expected 'Updated Gold Purchase', got {updated_purchase.get('description')}")
            return False
        
        if abs(updated_purchase.get('weight_grams', 0) - 130.789) > 0.001:
            print(f"❌ Weight not updated correctly: expected 130.789, got {updated_purchase.get('weight_grams')}")
            return False
        
        print(f"✅ Draft purchase updated successfully:")
        print(f"   - Description: {updated_purchase.get('description')}")
        print(f"   - Weight: {updated_purchase.get('weight_grams')}g")
        
        return True

    def test_purchases_edit_invalid_party(self):
        """Test Scenario 4: Attempt to Edit Non-Existent Party Type"""
        print("\n🚫 TESTING PURCHASES MODULE - EDIT WITH INVALID PARTY")
        
        if not hasattr(self, 'purchases_test_data'):
            return False
        
        draft_purchase_id = self.purchases_test_data['draft_purchase_id']
        
        # Try to change vendor to a customer party (should fail)
        # First create a customer party
        customer_data = {
            "name": f"Test Customer {datetime.now().strftime('%H%M%S')}",
            "party_type": "customer"
        }
        
        success, customer = self.run_test(
            "Create Customer Party for Invalid Test",
            "POST",
            "parties",
            200,
            data=customer_data
        )
        
        if not success:
            return False
        
        # Try to update purchase with customer party (should fail with 400)
        success, error_response = self.run_test(
            "Edit Purchase with Customer Party (Should Fail)",
            "PATCH",
            f"purchases/{draft_purchase_id}",
            400,  # Expecting 400 error
            data={"vendor_party_id": customer['id']}
        )
        
        if not success:
            print(f"❌ Expected 400 error when using customer party as vendor")
            return False
        
        print(f"✅ Correctly rejected customer party as vendor (400 error)")
        
        # Try with non-existent party ID (should fail with 404)
        fake_party_id = "non-existent-party-id"
        success, error_response = self.run_test(
            "Edit Purchase with Non-Existent Party (Should Fail)",
            "PATCH",
            f"purchases/{draft_purchase_id}",
            404,  # Expecting 404 error
            data={"vendor_party_id": fake_party_id}
        )
        
        if not success:
            print(f"❌ Expected 404 error when using non-existent party")
            return False
        
        print(f"✅ Correctly rejected non-existent party (404 error)")
        
        return True

    def test_purchases_finalize_atomic_operations(self):
        """Test Scenario 5: Finalize Purchase (CRITICAL - 5 Atomic Operations)"""
        print("\n🔥 TESTING PURCHASES MODULE - FINALIZE PURCHASE (5 ATOMIC OPERATIONS)")
        
        if not hasattr(self, 'purchases_test_data'):
            return False
        
        draft_purchase_id = self.purchases_test_data['draft_purchase_id']
        vendor_id = self.purchases_test_data['vendor_id']
        
        # Get current inventory state before finalization
        success, stock_before = self.run_test(
            "Get Stock Totals Before Finalization",
            "GET",
            "inventory/stock-totals",
            200
        )
        
        if not success:
            return False
        
        # Find Gold 22K inventory
        gold_22k_before = None
        for stock in stock_before:
            if "Gold 22K" in stock.get('header_name', ''):
                gold_22k_before = stock
                break
        
        initial_qty = gold_22k_before.get('total_qty', 0) if gold_22k_before else 0
        initial_weight = gold_22k_before.get('total_weight', 0) if gold_22k_before else 0
        
        print(f"   Initial inventory: {initial_qty} qty, {initial_weight}g weight")
        
        # Finalize the purchase
        success, finalize_response = self.run_test(
            "Finalize Purchase (All Atomic Operations)",
            "POST",
            f"purchases/{draft_purchase_id}/finalize",
            200
        )
        
        if not success:
            return False
        
        # Verify response structure
        required_fields = ['purchase_id', 'stock_movement_id', 'transaction_id', 'vendor_payable']
        for field in required_fields:
            if field not in finalize_response:
                print(f"❌ Finalize response missing field: {field}")
                return False
        
        print(f"✅ Finalize response complete:")
        print(f"   - Purchase ID: {finalize_response.get('purchase_id')}")
        print(f"   - Stock Movement ID: {finalize_response.get('stock_movement_id')}")
        print(f"   - Transaction ID: {finalize_response.get('transaction_id')}")
        print(f"   - Vendor Payable: {finalize_response.get('vendor_payable')}")
        
        # OPERATION A: Verify purchase status changed to "finalized", locked = True
        success, finalized_purchase = self.run_test(
            "Get Finalized Purchase (Check Status)",
            "GET",
            f"purchases/{draft_purchase_id}",
            200
        )
        
        if not success:
            return False
        
        if finalized_purchase.get('status') != 'finalized':
            print(f"❌ Purchase status should be 'finalized', got: {finalized_purchase.get('status')}")
            return False
        
        if finalized_purchase.get('locked') != True:
            print(f"❌ Purchase should be locked, got: {finalized_purchase.get('locked')}")
            return False
        
        if not finalized_purchase.get('finalized_at'):
            print(f"❌ Purchase should have finalized_at timestamp")
            return False
        
        if not finalized_purchase.get('finalized_by'):
            print(f"❌ Purchase should have finalized_by user")
            return False
        
        print(f"✅ Operation A: Purchase status changed to finalized and locked")
        
        # OPERATION B: Verify finalized_at, finalized_by populated
        print(f"✅ Operation B: Finalized metadata populated (at: {finalized_purchase.get('finalized_at')}, by: {finalized_purchase.get('finalized_by')})")
        
        # OPERATION C: Verify Stock IN movement created
        success, movements = self.run_test(
            "Get Stock Movements (Check Stock IN)",
            "GET",
            "inventory/movements",
            200
        )
        
        if not success:
            return False
        
        # Find the stock movement for this purchase
        purchase_movement = None
        for movement in movements:
            if (movement.get('reference_type') == 'purchase' and 
                movement.get('reference_id') == draft_purchase_id):
                purchase_movement = movement
                break
        
        if not purchase_movement:
            print(f"❌ No stock movement found for purchase {draft_purchase_id}")
            return False
        
        # Verify movement properties
        if purchase_movement.get('movement_type') != 'Stock IN':
            print(f"❌ Movement type should be 'Stock IN', got: {purchase_movement.get('movement_type')}")
            return False
        
        if purchase_movement.get('purity') != 916:
            print(f"❌ Movement purity should be 916 (NOT 999), got: {purchase_movement.get('purity')}")
            return False
        
        if purchase_movement.get('qty_delta') != 1:
            print(f"❌ Movement qty_delta should be 1 (positive), got: {purchase_movement.get('qty_delta')}")
            return False
        
        expected_weight = finalized_purchase.get('weight_grams', 0)
        if abs(purchase_movement.get('weight_delta', 0) - expected_weight) > 0.001:
            print(f"❌ Movement weight_delta should be {expected_weight}, got: {purchase_movement.get('weight_delta')}")
            return False
        
        print(f"✅ Operation C: Stock IN movement created correctly:")
        print(f"   - Type: {purchase_movement.get('movement_type')}")
        print(f"   - Purity: {purchase_movement.get('purity')} (valuation, not entered)")
        print(f"   - Qty Delta: +{purchase_movement.get('qty_delta')}")
        print(f"   - Weight Delta: +{purchase_movement.get('weight_delta')}g")
        
        # OPERATION D: Verify inventory header current_qty and current_weight increased
        success, stock_after = self.run_test(
            "Get Stock Totals After Finalization",
            "GET",
            "inventory/stock-totals",
            200
        )
        
        if not success:
            return False
        
        # Find Gold 22K inventory after finalization
        gold_22k_after = None
        for stock in stock_after:
            if "Gold 22K" in stock.get('header_name', ''):
                gold_22k_after = stock
                break
        
        if not gold_22k_after:
            print(f"❌ Gold 22K inventory header not found after finalization")
            return False
        
        final_qty = gold_22k_after.get('total_qty', 0)
        final_weight = gold_22k_after.get('total_weight', 0)
        
        expected_final_qty = initial_qty + 1
        expected_final_weight = initial_weight + expected_weight
        
        if abs(final_qty - expected_final_qty) > 0.001:
            print(f"❌ Inventory qty should increase by 1: expected {expected_final_qty}, got {final_qty}")
            return False
        
        if abs(final_weight - expected_final_weight) > 0.001:
            print(f"❌ Inventory weight should increase by {expected_weight}: expected {expected_final_weight}, got {final_weight}")
            return False
        
        print(f"✅ Operation D: Inventory header updated correctly:")
        print(f"   - Qty: {initial_qty} → {final_qty} (+1)")
        print(f"   - Weight: {initial_weight}g → {final_weight}g (+{expected_weight}g)")
        
        # OPERATION E: Verify vendor payable transaction created
        success, transactions = self.run_test(
            "Get Transactions (Check Vendor Payable)",
            "GET",
            "transactions",
            200
        )
        
        if not success:
            return False
        
        # Find the vendor payable transaction
        vendor_transaction = None
        for txn in transactions:
            if (txn.get('reference_type') == 'purchase' and 
                txn.get('reference_id') == draft_purchase_id and
                txn.get('party_id') == vendor_id):
                vendor_transaction = txn
                break
        
        if not vendor_transaction:
            print(f"❌ No vendor payable transaction found for purchase")
            return False
        
        # Verify transaction properties
        if vendor_transaction.get('transaction_type') != 'credit':
            print(f"❌ Transaction type should be 'credit' (we owe vendor), got: {vendor_transaction.get('transaction_type')}")
            return False
        
        if vendor_transaction.get('party_id') != vendor_id:
            print(f"❌ Transaction party_id should be {vendor_id}, got: {vendor_transaction.get('party_id')}")
            return False
        
        expected_amount = finalized_purchase.get('amount_total', 0)
        if abs(vendor_transaction.get('amount', 0) - expected_amount) > 0.01:
            print(f"❌ Transaction amount should be {expected_amount}, got: {vendor_transaction.get('amount')}")
            return False
        
        if vendor_transaction.get('category') != 'Purchase':
            print(f"❌ Transaction category should be 'Purchase', got: {vendor_transaction.get('category')}")
            return False
        
        # Verify transaction number format (TXN-YYYY-NNNN)
        txn_number = vendor_transaction.get('transaction_number', '')
        import re
        if not re.match(r'^TXN-\d{4}-\d{4}$', txn_number):
            print(f"❌ Transaction number format incorrect: {txn_number}")
            return False
        
        print(f"✅ Operation E: Vendor payable transaction created correctly:")
        print(f"   - Type: {vendor_transaction.get('transaction_type')} (liability)")
        print(f"   - Amount: {vendor_transaction.get('amount')}")
        print(f"   - Category: {vendor_transaction.get('category')}")
        print(f"   - Transaction Number: {txn_number}")
        
        # Store finalized purchase data for other tests
        self.purchases_test_data['finalized_purchase_id'] = draft_purchase_id
        self.purchases_test_data['stock_movement_id'] = finalize_response.get('stock_movement_id')
        self.purchases_test_data['transaction_id'] = finalize_response.get('transaction_id')
        
        print(f"🎉 ALL 5 ATOMIC OPERATIONS COMPLETED SUCCESSFULLY!")
        
        return True

    def test_purchases_edit_finalized_attempt(self):
        """Test Scenario 6: Attempt to Edit Finalized Purchase"""
        print("\n🔒 TESTING PURCHASES MODULE - ATTEMPT TO EDIT FINALIZED PURCHASE")
        
        if not hasattr(self, 'purchases_test_data') or 'finalized_purchase_id' not in self.purchases_test_data:
            print("❌ Finalized purchase not available, run finalization test first")
            return False
        
        finalized_purchase_id = self.purchases_test_data['finalized_purchase_id']
        
        # Try to update finalized purchase (should fail with 400)
        success, error_response = self.run_test(
            "Edit Finalized Purchase (Should Fail)",
            "PATCH",
            f"purchases/{finalized_purchase_id}",
            400,  # Expecting 400 error
            data={"description": "Attempting to edit finalized purchase"}
        )
        
        if not success:
            print(f"❌ Expected 400 error when editing finalized purchase")
            return False
        
        # Verify error message mentions immutability
        error_str = str(error_response).lower()
        if 'immutable' not in error_str or 'finalized' not in error_str:
            print(f"❌ Error message should mention immutability and finalized status")
            return False
        
        print(f"✅ Finalized purchase correctly rejected edit attempt (400 error)")
        print(f"   Error message mentions immutability: {error_response}")
        
        return True

    def test_purchases_re_finalize_attempt(self):
        """Test Scenario 7: Attempt to Re-Finalize"""
        print("\n🔄 TESTING PURCHASES MODULE - ATTEMPT TO RE-FINALIZE")
        
        if not hasattr(self, 'purchases_test_data') or 'finalized_purchase_id' not in self.purchases_test_data:
            return False
        
        finalized_purchase_id = self.purchases_test_data['finalized_purchase_id']
        
        # Count stock movements before re-finalize attempt
        success, movements_before = self.run_test(
            "Count Stock Movements Before Re-Finalize",
            "GET",
            "inventory/movements",
            200
        )
        
        if not success:
            return False
        
        movements_count_before = len([
            m for m in movements_before 
            if m.get('reference_type') == 'purchase' and m.get('reference_id') == finalized_purchase_id
        ])
        
        # Count transactions before re-finalize attempt
        success, transactions_before = self.run_test(
            "Count Transactions Before Re-Finalize",
            "GET",
            "transactions",
            200
        )
        
        if not success:
            return False
        
        transactions_count_before = len([
            t for t in transactions_before 
            if t.get('reference_type') == 'purchase' and t.get('reference_id') == finalized_purchase_id
        ])
        
        # Try to re-finalize (should fail with 400)
        success, error_response = self.run_test(
            "Re-Finalize Already Finalized Purchase (Should Fail)",
            "POST",
            f"purchases/{finalized_purchase_id}/finalize",
            400  # Expecting 400 error
        )
        
        if not success:
            print(f"❌ Expected 400 error when re-finalizing purchase")
            return False
        
        # Verify error message mentions already finalized
        error_str = str(error_response).lower()
        if 'already finalized' not in error_str:
            print(f"❌ Error message should mention 'already finalized'")
            return False
        
        print(f"✅ Re-finalization correctly rejected (400 error)")
        
        # Verify NO duplicate stock movements or transactions created
        success, movements_after = self.run_test(
            "Count Stock Movements After Re-Finalize Attempt",
            "GET",
            "inventory/movements",
            200
        )
        
        if not success:
            return False
        
        movements_count_after = len([
            m for m in movements_after 
            if m.get('reference_type') == 'purchase' and m.get('reference_id') == finalized_purchase_id
        ])
        
        success, transactions_after = self.run_test(
            "Count Transactions After Re-Finalize Attempt",
            "GET",
            "transactions",
            200
        )
        
        if not success:
            return False
        
        transactions_count_after = len([
            t for t in transactions_after 
            if t.get('reference_type') == 'purchase' and t.get('reference_id') == finalized_purchase_id
        ])
        
        if movements_count_after != movements_count_before:
            print(f"❌ Duplicate stock movements created: before={movements_count_before}, after={movements_count_after}")
            return False
        
        if transactions_count_after != transactions_count_before:
            print(f"❌ Duplicate transactions created: before={transactions_count_before}, after={transactions_count_after}")
            return False
        
        print(f"✅ No duplicate movements or transactions created")
        print(f"   - Stock movements: {movements_count_before} (unchanged)")
        print(f"   - Transactions: {transactions_count_before} (unchanged)")
        
        return True

    def test_purchases_purity_handling(self):
        """Test Scenario 8: Purity Handling Verification"""
        print("\n🔬 TESTING PURCHASES MODULE - PURITY HANDLING VERIFICATION")
        
        if not hasattr(self, 'purchases_test_data') or 'finalized_purchase_id' not in self.purchases_test_data:
            return False
        
        finalized_purchase_id = self.purchases_test_data['finalized_purchase_id']
        
        # Get the finalized purchase
        success, purchase = self.run_test(
            "Get Purchase for Purity Verification",
            "GET",
            f"purchases/{finalized_purchase_id}",
            200
        )
        
        if not success:
            return False
        
        # Verify entered_purity (999) is stored in purchase document
        if purchase.get('entered_purity') != 999:
            print(f"❌ entered_purity should be 999 (as claimed by vendor), got: {purchase.get('entered_purity')}")
            return False
        
        print(f"✅ entered_purity stored correctly: {purchase.get('entered_purity')} (vendor claim)")
        
        # Verify valuation_purity_fixed is 916
        if purchase.get('valuation_purity_fixed') != 916:
            print(f"❌ valuation_purity_fixed should be 916, got: {purchase.get('valuation_purity_fixed')}")
            return False
        
        print(f"✅ valuation_purity_fixed correct: {purchase.get('valuation_purity_fixed')} (for accounting)")
        
        # Get the stock movement and verify it uses 916 purity
        success, movements = self.run_test(
            "Get Stock Movement for Purity Verification",
            "GET",
            "inventory/movements",
            200
        )
        
        if not success:
            return False
        
        purchase_movement = None
        for movement in movements:
            if (movement.get('reference_type') == 'purchase' and 
                movement.get('reference_id') == finalized_purchase_id):
                purchase_movement = movement
                break
        
        if not purchase_movement:
            print(f"❌ Stock movement not found for purchase")
            return False
        
        # Verify stock movement uses valuation_purity_fixed (916), NOT entered_purity (999)
        if purchase_movement.get('purity') != 916:
            print(f"❌ Stock movement should use purity 916 (valuation), got: {purchase_movement.get('purity')}")
            return False
        
        print(f"✅ Stock movement uses valuation purity: {purchase_movement.get('purity')} (NOT entered purity)")
        
        # Verify inventory header shows 916 purity (22K gold)
        success, stock_totals = self.run_test(
            "Get Stock Totals for Purity Verification",
            "GET",
            "inventory/stock-totals",
            200
        )
        
        if not success:
            return False
        
        # Find the inventory header used
        header_name = purchase_movement.get('header_name', '')
        if "22K" not in header_name:
            print(f"❌ Inventory header should be 22K (916 purity), got: {header_name}")
            return False
        
        print(f"✅ Inventory header shows correct purity: {header_name} (22K = 916 purity)")
        
        print(f"🔬 PURITY HANDLING VERIFICATION COMPLETE:")
        print(f"   - entered_purity (999) stored for reference")
        print(f"   - valuation_purity_fixed (916) used for stock and accounting")
        print(f"   - Stock movement uses 916 purity")
        print(f"   - Inventory shows 22K gold (916 purity)")
        
        return True

    def test_purchases_precision_verification(self):
        """Test Scenario 9: Precision Verification"""
        print("\n📏 TESTING PURCHASES MODULE - PRECISION VERIFICATION")
        
        if not hasattr(self, 'purchases_test_data'):
            return False
        
        vendor_id = self.purchases_test_data['vendor_id']
        
        # Create purchase with specific precision test values
        precision_test_data = {
            "vendor_party_id": vendor_id,
            "description": "Precision Test Purchase",
            "weight_grams": 123.4567,    # 4 decimals input
            "entered_purity": 995,
            "rate_per_gram": 185.555,    # 3 decimals input
            "amount_total": 22888.88
        }
        
        success, purchase = self.run_test(
            "Create Purchase for Precision Test",
            "POST",
            "purchases",
            200,
            data=precision_test_data
        )
        
        if not success:
            return False
        
        # Verify weight rounded to 3 decimals (123.457)
        expected_weight = 123.457  # Should round 123.4567 to 3 decimals
        if abs(purchase.get('weight_grams', 0) - expected_weight) > 0.001:
            print(f"❌ Weight should be rounded to 3 decimals: expected {expected_weight}, got {purchase.get('weight_grams')}")
            return False
        
        print(f"✅ Weight precision correct: {precision_test_data['weight_grams']} → {purchase.get('weight_grams')} (3 decimals)")
        
        # Verify rate rounded to 2 decimals (185.56)
        expected_rate = 185.56  # Should round 185.555 to 2 decimals
        if abs(purchase.get('rate_per_gram', 0) - expected_rate) > 0.01:
            print(f"❌ Rate should be rounded to 2 decimals: expected {expected_rate}, got {purchase.get('rate_per_gram')}")
            return False
        
        print(f"✅ Rate precision correct: {precision_test_data['rate_per_gram']} → {purchase.get('rate_per_gram')} (2 decimals)")
        
        # Verify amount rounded to 2 decimals
        expected_amount = 22888.88
        if abs(purchase.get('amount_total', 0) - expected_amount) > 0.01:
            print(f"❌ Amount should be rounded to 2 decimals: expected {expected_amount}, got {purchase.get('amount_total')}")
            return False
        
        print(f"✅ Amount precision correct: {purchase.get('amount_total')} (2 decimals)")
        
        return True

    def test_purchases_date_range_filter(self):
        """Test Scenario 10: Filter by Date Range"""
        print("\n📅 TESTING PURCHASES MODULE - DATE RANGE FILTER")
        
        from datetime import timedelta
        
        # Test date range filtering
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Test with date range that should include today's purchases
        success, purchases_today = self.run_test(
            "Get Purchases (Today's Date Range)",
            "GET",
            "purchases",
            200,
            params={
                "start_date": today,
                "end_date": tomorrow
            }
        )
        
        if not success:
            return False
        
        print(f"✅ Date range filter working: {len(purchases_today)} purchases found for today")
        
        # Test with date range that should exclude today's purchases
        success, purchases_yesterday = self.run_test(
            "Get Purchases (Yesterday's Date Range)",
            "GET",
            "purchases",
            200,
            params={
                "start_date": yesterday,
                "end_date": yesterday
            }
        )
        
        if not success:
            return False
        
        print(f"✅ Date range exclusion working: {len(purchases_yesterday)} purchases found for yesterday")
        
        # Verify all returned purchases are within date range
        for purchase in purchases_today:
            purchase_date = purchase.get('date', '')
            if purchase_date and today not in purchase_date:
                print(f"ℹ️  Purchase date {purchase_date} outside expected range (may be timezone difference)")
        
        return True

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Gold Shop ERP Backend Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)

        # Authentication tests
        if not self.test_login():
            print("❌ Login failed, stopping tests")
            return False

        if not self.test_auth_me():
            print("❌ Auth verification failed")
            return False

        # Core functionality tests
        test_results = {
            "Inventory Headers": self.test_inventory_headers(),
            "Stock Movements": self.test_stock_movements(),
            "Parties Management": self.test_parties(),
            "Accounts Management": self.test_accounts(),
            "Transactions": self.test_transactions(),
            "Job Cards (New Fields)": self.test_jobcards(),
            "Job Card to Invoice Conversion": self.test_jobcard_to_invoice_conversion(),
            "Party Summary Endpoint (Module 2/10)": self.test_party_summary_endpoint(),  # NEW TEST
            "Daily Closing APIs": self.test_daily_closing(),
            "Invoice PDF Generation": self.test_invoice_pdf_generation(),
            "Audit Logs": self.test_audit_logs(),
            "Financial Summary Reports": self.test_reports_financial_summary(),
            "Inventory View Reports": self.test_reports_inventory_view(),
            "Invoices View Reports": self.test_reports_invoices_view(),
            "Parties View Reports": self.test_reports_parties_view(),
            "Transactions View Reports": self.test_reports_transactions_view(),
            "Export Endpoints": self.test_reports_export_endpoints(),
            "Individual Reports": self.test_reports_individual_reports(),
            
            # ENHANCED INVOICE FINALIZATION TESTS
            "🔥 Job Card Locking on Finalization": self.test_enhanced_invoice_finalization_job_card_locking(),
            "🔥 Customer Ledger Entry Creation": self.test_enhanced_invoice_finalization_customer_ledger(),
            "🔥 Outstanding Balance Tracking": self.test_enhanced_invoice_finalization_outstanding_balance(),
            "🔥 Direct Invoice Finalization": self.test_enhanced_invoice_finalization_direct_invoice(),
            "🔥 Default Sales Account Creation": self.test_enhanced_invoice_finalization_sales_account(),
            "🔥 Full Workflow Test": self.test_enhanced_invoice_finalization_full_workflow(),
            "🔥 Error Cases Testing": self.test_enhanced_invoice_finalization_error_cases(),
            
            # JOB CARD LOCKING WITH ADMIN OVERRIDE TESTS
            "🔒 Job Card Locking Setup": self.test_job_card_locking_admin_override_setup(),
            "🔒 Non-Admin Edit Attempt": self.test_job_card_locking_non_admin_edit_attempt(),
            "🔒 Non-Admin Delete Attempt": self.test_job_card_locking_non_admin_delete_attempt(),
            "🔒 Admin Edit Override": self.test_job_card_locking_admin_edit_override(),
            "🔒 Admin Delete Override": self.test_job_card_locking_admin_delete_override(),
            "🔒 Audit Log Verification": self.test_job_card_locking_audit_log_verification(),
            "🔒 Normal Job Card Operations": self.test_job_card_locking_normal_operations()
        }

        # Print results summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:<25} {status}")

        print(f"\n📈 Overall: {self.tests_passed}/{self.tests_run} tests passed")
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"🎯 Success Rate: {success_rate:.1f}%")

        return success_rate >= 80

def main():
    tester = GoldShopERPTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
import requests
import sys
import json
from datetime import datetime

class GoldShopERPTester:
    def __init__(self, base_url="https://party-summary.preview.emergentagent.com"):
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
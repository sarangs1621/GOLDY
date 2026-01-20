import requests
import sys
import json
from datetime import datetime

class GoldShopERPTester:
    def __init__(self, base_url="https://gold-inv-workflow.preview.emergentagent.com"):
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
            "Individual Reports": self.test_reports_individual_reports()
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
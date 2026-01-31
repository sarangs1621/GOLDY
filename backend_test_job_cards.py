#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Gold Shop ERP - Job Card Enhancements
Testing Job Card Enhancements Backend Implementation
"""

import requests
import json
import uuid
from datetime import datetime, timezone
import time

# Configuration
BACKEND_URL = "https://feature-unlock-2.preview.emergentagent.com/api"
TEST_USER = {
    "username": "admin_netflow_test",
    "password": "TestAdmin@123"  # Test admin user for net flow testing
}

class JobCardEnhancementsTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.csrf_token = None
        self.test_results = []
        
    def log_result(self, test_name, success, details, response_data=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {details}")
        
    def authenticate(self):
        """Authenticate and get tokens"""
        try:
            # Login
            login_data = {
                "username": TEST_USER["username"],
                "password": TEST_USER["password"]
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.csrf_token = data.get("csrf_token")
                
                # Set headers for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}",
                    "X-CSRF-Token": self.csrf_token
                })
                
                self.log_result("Authentication", True, f"Successfully authenticated as {TEST_USER['username']}")
                return True
            else:
                self.log_result("Authentication", False, f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def test_job_card_enhancements(self):
        """Test Job Card Enhancements Backend Implementation"""
        print("\n" + "="*60)
        print("TESTING JOB CARD ENHANCEMENTS BACKEND IMPLEMENTATION")
        print("="*60)
        
        # Test 1: GET Individual Job Card Endpoint (NEW - Just Added)
        self.test_get_individual_job_card_endpoint()
        
        # Test 2: Customer Oman ID Everywhere
        self.test_customer_oman_id_workflow()
        
        # Test 3: Per-Inch Making Charge
        self.test_per_inch_making_charge()
        
        # Test 4: Work Types CRUD (Quick Verification)
        self.test_work_types_crud()
    
    def test_get_individual_job_card_endpoint(self):
        """Test GET /api/jobcards/{jobcard_id} endpoint (NEW - Just Added)"""
        print("\n--- Testing GET Individual Job Card Endpoint ---")
        
        try:
            # First create a test job card
            job_card_id = self.create_test_job_card_with_customer_oman_id()
            
            if not job_card_id:
                self.log_result("GET Individual Job Card - Setup", False, "Failed to create test job card")
                return
            
            # Test GET /api/jobcards/{jobcard_id}
            response = self.session.get(f"{BACKEND_URL}/jobcards/{job_card_id}")
            
            if response.status_code == 200:
                job_card_data = response.json()
                
                # Verify required fields are present
                required_fields = ['id', 'job_card_number', 'status', 'customer_type', 'items', 'created_at']
                missing_fields = [field for field in required_fields if field not in job_card_data]
                
                if not missing_fields:
                    # Verify authentication is required (this should work since we're authenticated)
                    job_card_number = job_card_data.get('job_card_number')
                    items_count = len(job_card_data.get('items', []))
                    
                    self.log_result(
                        "GET Individual Job Card Endpoint", 
                        True, 
                        f"Successfully retrieved job card {job_card_number} with {items_count} items",
                        {
                            "job_card_id": job_card_id,
                            "job_card_number": job_card_number,
                            "status": job_card_data.get('status'),
                            "items_count": items_count
                        }
                    )
                    
                    # Test with non-existent job card (should return 404)
                    self.test_get_nonexistent_job_card()
                    
                else:
                    self.log_result("GET Individual Job Card Endpoint", False, f"Missing required fields: {missing_fields}")
            else:
                self.log_result("GET Individual Job Card Endpoint", False, f"Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("GET Individual Job Card Endpoint", False, f"Error: {str(e)}")
    
    def test_get_nonexistent_job_card(self):
        """Test GET /api/jobcards/{jobcard_id} with non-existent ID (should return 404)"""
        try:
            fake_id = str(uuid.uuid4())
            response = self.session.get(f"{BACKEND_URL}/jobcards/{fake_id}")
            
            if response.status_code == 404:
                self.log_result(
                    "GET Individual Job Card - 404 Test", 
                    True, 
                    "Correctly returned 404 for non-existent job card"
                )
            else:
                self.log_result(
                    "GET Individual Job Card - 404 Test", 
                    False, 
                    f"Expected 404 but got: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("GET Individual Job Card - 404 Test", False, f"Error: {str(e)}")
    
    def test_customer_oman_id_workflow(self):
        """Test Customer Oman ID field throughout job card to invoice workflow"""
        print("\n--- Testing Customer Oman ID Workflow ---")
        
        try:
            # Step 1: Create job card with customer_oman_id
            job_card_id = self.create_test_job_card_with_customer_oman_id()
            
            if not job_card_id:
                self.log_result("Customer Oman ID Workflow - Setup", False, "Failed to create job card with Oman ID")
                return
            
            # Step 2: Retrieve job card and verify customer_oman_id is stored
            response = self.session.get(f"{BACKEND_URL}/jobcards/{job_card_id}")
            
            if response.status_code == 200:
                job_card_data = response.json()
                stored_oman_id = job_card_data.get('customer_oman_id')
                
                if stored_oman_id == "12345678":  # Our test Oman ID
                    self.log_result(
                        "Customer Oman ID - Job Card Storage", 
                        True, 
                        f"Job card correctly stores customer_oman_id: {stored_oman_id}"
                    )
                    
                    # Step 3: Convert job card to invoice
                    invoice_id = self.convert_job_card_to_invoice(job_card_id)
                    
                    if invoice_id:
                        # Step 4: Verify customer_oman_id is carried forward to invoice
                        self.verify_oman_id_in_invoice(invoice_id, stored_oman_id)
                    
                else:
                    self.log_result("Customer Oman ID - Job Card Storage", False, f"Expected Oman ID '12345678' but got: {stored_oman_id}")
            else:
                self.log_result("Customer Oman ID - Job Card Retrieval", False, f"Failed to retrieve job card: {response.status_code}")
                
        except Exception as e:
            self.log_result("Customer Oman ID Workflow", False, f"Error: {str(e)}")
    
    def create_test_job_card_with_customer_oman_id(self):
        """Create a test job card with customer_oman_id field"""
        try:
            # Get or create a customer
            customer_id = self.get_or_create_test_customer()
            if not customer_id:
                return None
            
            # Get or create a worker
            worker_id = self.get_or_create_test_worker()
            
            job_card_data = {
                "customer_type": "saved",
                "customer_id": customer_id,
                "customer_oman_id": "12345678",  # Test Oman ID
                "worker_id": worker_id,
                "delivery_date": "2024-12-31",
                "items": [
                    {
                        "category": "Rings",
                        "description": "Gold Ring 22K - Customer Oman ID Test",
                        "qty": 1,
                        "weight_in": 5.250,
                        "weight_out": 5.150,
                        "purity": 916,
                        "work_type": "Polish",
                        "making_charge_type": "per_gram",
                        "making_charge_value": 25.00,
                        "remarks": "Test job card with customer Oman ID"
                    }
                ],
                "notes": "Test job card for customer Oman ID workflow testing"
            }
            
            response = self.session.post(f"{BACKEND_URL}/jobcards", json=job_card_data)
            
            if response.status_code == 201:
                job_card = response.json()
                job_card_id = job_card.get("id")
                job_card_number = job_card.get("job_card_number")
                
                self.log_result(
                    "Create Job Card with Oman ID", 
                    True, 
                    f"Created job card {job_card_number} with customer_oman_id: 12345678",
                    {"job_card_id": job_card_id, "job_card_number": job_card_number}
                )
                return job_card_id
            else:
                self.log_result("Create Job Card with Oman ID", False, f"Failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Create Job Card with Oman ID", False, f"Error: {str(e)}")
            return None
    
    def get_or_create_test_customer(self):
        """Get existing customer or create one for testing"""
        try:
            # Try to get existing customers
            response = self.session.get(f"{BACKEND_URL}/parties?party_type=customer")
            
            if response.status_code == 200:
                customers = response.json()
                if isinstance(customers, dict) and 'items' in customers:
                    customers = customers['items']
                
                if customers:
                    customer_id = customers[0].get('id')
                    self.log_result("Get Test Customer", True, f"Using existing customer: {customers[0].get('name')}")
                    return customer_id
            
            # Create new customer
            customer_data = {
                "name": "Ahmed Al-Rashid",
                "phone": "+968 9876 5432",
                "address": "Muscat, Sultanate of Oman",
                "party_type": "customer",
                "notes": "Test customer for job card testing"
            }
            
            response = self.session.post(f"{BACKEND_URL}/parties", json=customer_data)
            
            if response.status_code == 201:
                customer = response.json()
                customer_id = customer.get("id")
                self.log_result("Create Test Customer", True, f"Created test customer: {customer.get('name')}")
                return customer_id
            else:
                self.log_result("Create Test Customer", False, f"Failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Get/Create Test Customer", False, f"Error: {str(e)}")
            return None
    
    def get_or_create_test_worker(self):
        """Get existing worker or create one for testing"""
        try:
            # Try to get existing workers
            response = self.session.get(f"{BACKEND_URL}/workers")
            
            if response.status_code == 200:
                workers = response.json()
                if isinstance(workers, dict) and 'items' in workers:
                    workers = workers['items']
                
                if workers:
                    worker_id = workers[0].get('id')
                    self.log_result("Get Test Worker", True, f"Using existing worker: {workers[0].get('name')}")
                    return worker_id
            
            # Create new worker
            worker_data = {
                "name": "Ahmed Al-Saidi",
                "phone": "+968 9123 4567",
                "role": "Goldsmith",
                "active": True
            }
            
            response = self.session.post(f"{BACKEND_URL}/workers", json=worker_data)
            
            if response.status_code == 201:
                worker = response.json()
                worker_id = worker.get("id")
                self.log_result("Create Test Worker", True, f"Created test worker: {worker.get('name')}")
                return worker_id
            else:
                self.log_result("Create Test Worker", False, f"Failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Get/Create Test Worker", False, f"Error: {str(e)}")
            return None
    
    def convert_job_card_to_invoice(self, job_card_id):
        """Convert job card to invoice"""
        try:
            response = self.session.post(f"{BACKEND_URL}/jobcards/{job_card_id}/convert-to-invoice")
            
            if response.status_code == 200:
                result = response.json()
                invoice_id = result.get("invoice_id")
                invoice_number = result.get("invoice_number")
                
                self.log_result(
                    "Convert Job Card to Invoice", 
                    True, 
                    f"Successfully converted job card to invoice {invoice_number}",
                    {"invoice_id": invoice_id, "invoice_number": invoice_number}
                )
                return invoice_id
            else:
                self.log_result("Convert Job Card to Invoice", False, f"Failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Convert Job Card to Invoice", False, f"Error: {str(e)}")
            return None
    
    def verify_oman_id_in_invoice(self, invoice_id, expected_oman_id):
        """Verify customer_oman_id is carried forward to invoice"""
        try:
            response = self.session.get(f"{BACKEND_URL}/invoices/{invoice_id}")
            
            if response.status_code == 200:
                invoice_data = response.json()
                invoice_oman_id = invoice_data.get('customer_oman_id')
                
                if invoice_oman_id == expected_oman_id:
                    self.log_result(
                        "Customer Oman ID - Invoice Carryover", 
                        True, 
                        f"Invoice correctly carries forward customer_oman_id: {invoice_oman_id}"
                    )
                else:
                    self.log_result(
                        "Customer Oman ID - Invoice Carryover", 
                        False, 
                        f"Expected Oman ID '{expected_oman_id}' but invoice has: {invoice_oman_id}"
                    )
            else:
                self.log_result("Customer Oman ID - Invoice Verification", False, f"Failed to retrieve invoice: {response.status_code}")
                
        except Exception as e:
            self.log_result("Customer Oman ID - Invoice Verification", False, f"Error: {str(e)}")
    
    def test_per_inch_making_charge(self):
        """Test per-inch making charge calculation"""
        print("\n--- Testing Per-Inch Making Charge ---")
        
        try:
            # Step 1: Create job card with making_charge_type='per_inch'
            job_card_id = self.create_job_card_with_per_inch_charge()
            
            if not job_card_id:
                self.log_result("Per-Inch Making Charge - Setup", False, "Failed to create job card with per-inch charge")
                return
            
            # Step 2: Retrieve job card and verify fields are stored correctly
            response = self.session.get(f"{BACKEND_URL}/jobcards/{job_card_id}")
            
            if response.status_code == 200:
                job_card_data = response.json()
                items = job_card_data.get('items', [])
                
                if items:
                    item = items[0]
                    making_charge_type = item.get('making_charge_type')
                    making_charge_value = item.get('making_charge_value')
                    inches = item.get('inches')
                    
                    if making_charge_type == 'per_inch' and making_charge_value == 50.0 and inches == 8.5:
                        self.log_result(
                            "Per-Inch Making Charge - Job Card Storage", 
                            True, 
                            f"Job card correctly stores per-inch fields: type={making_charge_type}, value={making_charge_value}, inches={inches}"
                        )
                        
                        # Step 3: Convert to invoice and verify calculation
                        invoice_id = self.convert_job_card_to_invoice(job_card_id)
                        
                        if invoice_id:
                            self.verify_per_inch_calculation_in_invoice(invoice_id, making_charge_value, inches)
                    else:
                        self.log_result(
                            "Per-Inch Making Charge - Job Card Storage", 
                            False, 
                            f"Incorrect per-inch fields: type={making_charge_type}, value={making_charge_value}, inches={inches}"
                        )
                else:
                    self.log_result("Per-Inch Making Charge - Job Card Items", False, "No items found in job card")
            else:
                self.log_result("Per-Inch Making Charge - Job Card Retrieval", False, f"Failed to retrieve job card: {response.status_code}")
                
        except Exception as e:
            self.log_result("Per-Inch Making Charge", False, f"Error: {str(e)}")
    
    def create_job_card_with_per_inch_charge(self):
        """Create job card with per-inch making charge"""
        try:
            # Get or create a customer
            customer_id = self.get_or_create_test_customer()
            if not customer_id:
                return None
            
            # Get or create a worker
            worker_id = self.get_or_create_test_worker()
            
            job_card_data = {
                "customer_type": "saved",
                "customer_id": customer_id,
                "customer_oman_id": "87654321",  # Different Oman ID for this test
                "worker_id": worker_id,
                "delivery_date": "2024-12-31",
                "items": [
                    {
                        "category": "Chains",
                        "description": "Gold Chain 22K - Per Inch Charge Test",
                        "qty": 1,
                        "weight_in": 12.500,
                        "weight_out": 12.350,
                        "purity": 916,
                        "work_type": "Custom",
                        "making_charge_type": "per_inch",  # Per-inch charge
                        "making_charge_value": 50.00,     # 50 OMR per inch
                        "inches": 8.5,                    # 8.5 inches
                        "remarks": "Test per-inch making charge calculation"
                    }
                ],
                "notes": "Test job card for per-inch making charge testing"
            }
            
            response = self.session.post(f"{BACKEND_URL}/jobcards", json=job_card_data)
            
            if response.status_code == 201:
                job_card = response.json()
                job_card_id = job_card.get("id")
                job_card_number = job_card.get("job_card_number")
                
                self.log_result(
                    "Create Job Card with Per-Inch Charge", 
                    True, 
                    f"Created job card {job_card_number} with per-inch making charge (50 OMR × 8.5 inches = 425 OMR)",
                    {"job_card_id": job_card_id, "job_card_number": job_card_number}
                )
                return job_card_id
            else:
                self.log_result("Create Job Card with Per-Inch Charge", False, f"Failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Create Job Card with Per-Inch Charge", False, f"Error: {str(e)}")
            return None
    
    def verify_per_inch_calculation_in_invoice(self, invoice_id, making_charge_value, inches):
        """Verify per-inch making charge calculation in invoice"""
        try:
            response = self.session.get(f"{BACKEND_URL}/invoices/{invoice_id}")
            
            if response.status_code == 200:
                invoice_data = response.json()
                items = invoice_data.get('items', [])
                
                if items:
                    item = items[0]
                    making_charge_type = item.get('making_charge_type')
                    making_value = item.get('making_value')
                    item_inches = item.get('inches')
                    
                    # Expected calculation: making_charge_value * inches = 50.0 * 8.5 = 425.0
                    expected_making_value = making_charge_value * inches
                    
                    if (making_charge_type == 'per_inch' and 
                        abs(making_value - expected_making_value) < 0.01 and 
                        item_inches == inches):
                        
                        self.log_result(
                            "Per-Inch Making Charge - Invoice Calculation", 
                            True, 
                            f"Invoice correctly calculates per-inch making charge: {making_charge_value} × {inches} = {making_value} OMR"
                        )
                    else:
                        self.log_result(
                            "Per-Inch Making Charge - Invoice Calculation", 
                            False, 
                            f"Incorrect calculation: expected {expected_making_value}, got {making_value} (type: {making_charge_type}, inches: {item_inches})"
                        )
                else:
                    self.log_result("Per-Inch Making Charge - Invoice Items", False, "No items found in invoice")
            else:
                self.log_result("Per-Inch Making Charge - Invoice Retrieval", False, f"Failed to retrieve invoice: {response.status_code}")
                
        except Exception as e:
            self.log_result("Per-Inch Making Charge - Invoice Verification", False, f"Error: {str(e)}")
    
    def test_work_types_crud(self):
        """Test Work Types CRUD operations (Quick Verification)"""
        print("\n--- Testing Work Types CRUD (Quick Verification) ---")
        
        try:
            # Test 1: Create work type
            work_type_id = self.create_test_work_type()
            
            if work_type_id:
                # Test 2: Read work types
                self.test_read_work_types()
                
                # Test 3: Update work type
                self.test_update_work_type(work_type_id)
                
                # Test 4: Test duplicate prevention
                self.test_work_type_duplicate_prevention()
                
                # Test 5: Delete work type
                self.test_delete_work_type(work_type_id)
        
        except Exception as e:
            self.log_result("Work Types CRUD", False, f"Error: {str(e)}")
    
    def create_test_work_type(self):
        """Create a test work type"""
        try:
            work_type_data = {
                "name": f"Test Work Type {uuid.uuid4().hex[:8]}",
                "description": "Test work type for CRUD verification",
                "is_active": True
            }
            
            response = self.session.post(f"{BACKEND_URL}/work-types", json=work_type_data)
            
            if response.status_code == 201:
                work_type = response.json()
                work_type_id = work_type.get("id")
                work_type_name = work_type.get("name")
                
                self.log_result(
                    "Work Types - Create", 
                    True, 
                    f"Created work type: {work_type_name}",
                    {"work_type_id": work_type_id, "name": work_type_name}
                )
                return work_type_id
            else:
                self.log_result("Work Types - Create", False, f"Failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Work Types - Create", False, f"Error: {str(e)}")
            return None
    
    def test_read_work_types(self):
        """Test reading work types"""
        try:
            response = self.session.get(f"{BACKEND_URL}/work-types")
            
            if response.status_code == 200:
                work_types = response.json()
                if isinstance(work_types, dict) and 'items' in work_types:
                    work_types = work_types['items']
                
                work_types_count = len(work_types) if isinstance(work_types, list) else 0
                
                self.log_result(
                    "Work Types - Read", 
                    True, 
                    f"Retrieved {work_types_count} work types",
                    {"count": work_types_count}
                )
            else:
                self.log_result("Work Types - Read", False, f"Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Work Types - Read", False, f"Error: {str(e)}")
    
    def test_update_work_type(self, work_type_id):
        """Test updating work type"""
        try:
            update_data = {
                "name": f"Updated Test Work Type {uuid.uuid4().hex[:8]}",
                "description": "Updated description for test work type",
                "is_active": True
            }
            
            response = self.session.patch(f"{BACKEND_URL}/work-types/{work_type_id}", json=update_data)
            
            if response.status_code == 200:
                updated_work_type = response.json()
                updated_name = updated_work_type.get("name")
                
                self.log_result(
                    "Work Types - Update", 
                    True, 
                    f"Updated work type: {updated_name}",
                    {"updated_name": updated_name}
                )
            else:
                self.log_result("Work Types - Update", False, f"Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Work Types - Update", False, f"Error: {str(e)}")
    
    def test_work_type_duplicate_prevention(self):
        """Test work type duplicate name prevention"""
        try:
            # Create first work type
            work_type_data = {
                "name": "Duplicate Test Work Type",
                "description": "First work type",
                "is_active": True
            }
            
            response1 = self.session.post(f"{BACKEND_URL}/work-types", json=work_type_data)
            
            if response1.status_code == 201:
                # Try to create duplicate
                response2 = self.session.post(f"{BACKEND_URL}/work-types", json=work_type_data)
                
                if response2.status_code == 400:
                    error_message = response2.json().get('detail', response2.text)
                    self.log_result(
                        "Work Types - Duplicate Prevention", 
                        True, 
                        f"Correctly prevented duplicate work type: {error_message}"
                    )
                else:
                    self.log_result(
                        "Work Types - Duplicate Prevention", 
                        False, 
                        f"Should have prevented duplicate but got: {response2.status_code}"
                    )
            else:
                self.log_result("Work Types - Duplicate Prevention Setup", False, f"Failed to create first work type: {response1.status_code}")
                
        except Exception as e:
            self.log_result("Work Types - Duplicate Prevention", False, f"Error: {str(e)}")
    
    def test_delete_work_type(self, work_type_id):
        """Test deleting work type"""
        try:
            response = self.session.delete(f"{BACKEND_URL}/work-types/{work_type_id}")
            
            if response.status_code == 200:
                self.log_result(
                    "Work Types - Delete", 
                    True, 
                    "Successfully deleted work type"
                )
            else:
                self.log_result("Work Types - Delete", False, f"Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Work Types - Delete", False, f"Error: {str(e)}")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("JOB CARD ENHANCEMENTS TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print(f"\nFAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"❌ {result['test']}: {result['details']}")
        
        print(f"\nDetailed results saved to job_card_test_results.json")
        
        # Save detailed results
        with open('/app/job_card_test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)

    def run_all_tests(self):
        """Run all job card enhancement tests"""
        print("🚀 Starting Job Card Enhancements Backend Testing")
        print("="*80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Test Job Card Enhancements (Primary Focus)
        self.test_job_card_enhancements()
        
        # Print final summary
        self.print_summary()

def main():
    """Main function to run all tests"""
    tester = JobCardEnhancementsTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
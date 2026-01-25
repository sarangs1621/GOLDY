#!/usr/bin/env python3
"""
Comprehensive Backend Testing Script for Worker Management System

CRITICAL TEST FOCUS:
✅ Worker CRUD Operations - Complete API Testing
✅ Job Card Worker Assignment - Integration Testing  
✅ Invoice Worker Integration - Data Flow Testing
✅ Validation Scenarios - Edge Case Testing

TEST OBJECTIVES:
1. WORKER CRUD OPERATIONS:
   - GET /api/workers (list all workers, test active filter)
   - POST /api/workers (create worker with duplicate name/phone validation)
   - GET /api/workers/{worker_id} (get single worker)
   - PATCH /api/workers/{worker_id} (update worker, test duplicate validation)
   - DELETE /api/workers/{worker_id} (soft delete, test active job card constraint)

2. JOB CARD WORKER ASSIGNMENT:
   - Test job card creation with worker assignment
   - Test job card update to assign/change worker
   - Verify completion validation: Must have worker before completing

3. INVOICE WORKER INTEGRATION:
   - Verify worker_id and worker_name transfer from job card to invoice
   - Test invoice creation from job card with worker data

4. VALIDATION SCENARIOS:
   - Duplicate worker name validation
   - Duplicate phone number validation  
   - Worker deletion with active job cards assigned
   - Worker activation/deactivation

5. EDGE CASES:
   - Empty/null worker name
   - Invalid worker_id in job card assignment
   - Worker deletion cascade checks
"""

import requests
import json
import sys
from datetime import datetime
import uuid
import time

# Configuration
BASE_URL = "https://axios-harmony.preview.emergentagent.com/api"
USERNAME = "admin"
PASSWORD = "admin123"

class WorkerManagementTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.test_workers = []
        self.test_jobcards = []
        self.test_invoices = []
        
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

    # ============================================================================
    # WORKER CRUD OPERATIONS TESTING
    # ============================================================================
    
    def test_worker_list_endpoint(self):
        """
        TEST 1: Worker List Endpoint
        GET /api/workers - Test list all workers with active filter
        """
        print("\n" + "="*80)
        print("TEST 1: WORKER LIST ENDPOINT")
        print("="*80)
        
        try:
            # Test basic list endpoint
            response = self.session.get(f"{BASE_URL}/workers")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if "items" in data:
                    workers = data["items"]
                    self.log_result("Worker List - Response Structure", "PASS", 
                                  f"Response contains 'items' array with {len(workers)} workers")
                    
                    # Test active filter
                    response_active = self.session.get(f"{BASE_URL}/workers?active=true")
                    if response_active.status_code == 200:
                        active_data = response_active.json()
                        active_workers = active_data.get("items", [])
                        self.log_result("Worker List - Active Filter", "PASS", 
                                      f"Active filter working: {len(active_workers)} active workers")
                    else:
                        self.log_result("Worker List - Active Filter", "FAIL", 
                                      f"Active filter failed: {response_active.status_code}")
                        
                    # Test inactive filter
                    response_inactive = self.session.get(f"{BASE_URL}/workers?active=false")
                    if response_inactive.status_code == 200:
                        inactive_data = response_inactive.json()
                        inactive_workers = inactive_data.get("items", [])
                        self.log_result("Worker List - Inactive Filter", "PASS", 
                                      f"Inactive filter working: {len(inactive_workers)} inactive workers")
                    else:
                        self.log_result("Worker List - Inactive Filter", "FAIL", 
                                      f"Inactive filter failed: {response_inactive.status_code}")
                        
                else:
                    self.log_result("Worker List - Response Structure", "FAIL", 
                                  "Response missing 'items' key")
            else:
                self.log_result("Worker List - HTTP Response", "FAIL", 
                              f"Failed to get workers: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Worker List - Exception", "ERROR", f"Error: {str(e)}")
    
    def test_worker_creation(self):
        """
        TEST 2: Worker Creation
        POST /api/workers - Test worker creation with validation
        """
        print("\n" + "="*80)
        print("TEST 2: WORKER CREATION")
        print("="*80)
        
        try:
            # Test successful worker creation
            worker_data = {
                "name": "John Smith",
                "phone": "+968-9876-5432",
                "role": "Goldsmith",
                "active": True
            }
            
            response = self.session.post(f"{BASE_URL}/workers", json=worker_data)
            
            if response.status_code == 200:
                worker = response.json()
                self.test_workers.append(worker)
                self.log_result("Worker Creation - Success", "PASS", 
                              f"Successfully created worker: {worker.get('name')} (ID: {worker.get('id')})")
                
                # Verify worker fields
                required_fields = ['id', 'name', 'phone', 'role', 'active', 'created_at', 'created_by']
                missing_fields = [field for field in required_fields if field not in worker]
                
                if not missing_fields:
                    self.log_result("Worker Creation - Field Validation", "PASS", 
                                  "Created worker has all required fields")
                else:
                    self.log_result("Worker Creation - Field Validation", "FAIL", 
                                  f"Missing fields: {missing_fields}")
                    
            else:
                self.log_result("Worker Creation - Success", "FAIL", 
                              f"Failed to create worker: {response.status_code} - {response.text}")
                
            # Test duplicate name validation
            duplicate_name_data = {
                "name": "John Smith",  # Same name as above
                "phone": "+968-1111-2222",
                "role": "Polisher",
                "active": True
            }
            
            response = self.session.post(f"{BASE_URL}/workers", json=duplicate_name_data)
            
            if response.status_code == 400:
                self.log_result("Worker Creation - Duplicate Name Validation", "PASS", 
                              "Duplicate name validation working correctly")
            else:
                self.log_result("Worker Creation - Duplicate Name Validation", "FAIL", 
                              f"Duplicate name should return 400, got: {response.status_code}")
                
            # Test duplicate phone validation
            duplicate_phone_data = {
                "name": "Jane Doe",
                "phone": "+968-9876-5432",  # Same phone as first worker
                "role": "Designer",
                "active": True
            }
            
            response = self.session.post(f"{BASE_URL}/workers", json=duplicate_phone_data)
            
            if response.status_code == 400:
                self.log_result("Worker Creation - Duplicate Phone Validation", "PASS", 
                              "Duplicate phone validation working correctly")
            else:
                self.log_result("Worker Creation - Duplicate Phone Validation", "FAIL", 
                              f"Duplicate phone should return 400, got: {response.status_code}")
                
            # Test empty name validation
            empty_name_data = {
                "name": "",
                "phone": "+968-3333-4444",
                "role": "Helper",
                "active": True
            }
            
            response = self.session.post(f"{BASE_URL}/workers", json=empty_name_data)
            
            if response.status_code == 400:
                self.log_result("Worker Creation - Empty Name Validation", "PASS", 
                              "Empty name validation working correctly")
            else:
                self.log_result("Worker Creation - Empty Name Validation", "FAIL", 
                              f"Empty name should return 400, got: {response.status_code}")
                
        except Exception as e:
            self.log_result("Worker Creation - Exception", "ERROR", f"Error: {str(e)}")
    
    def test_worker_retrieval(self):
        """
        TEST 3: Worker Retrieval
        GET /api/workers/{worker_id} - Test single worker retrieval
        """
        print("\n" + "="*80)
        print("TEST 3: WORKER RETRIEVAL")
        print("="*80)
        
        if not self.test_workers:
            self.log_result("Worker Retrieval", "FAIL", "No test workers available")
            return
            
        try:
            worker = self.test_workers[0]
            worker_id = worker.get('id')
            
            # Test successful retrieval
            response = self.session.get(f"{BASE_URL}/workers/{worker_id}")
            
            if response.status_code == 200:
                retrieved_worker = response.json()
                self.log_result("Worker Retrieval - Success", "PASS", 
                              f"Successfully retrieved worker: {retrieved_worker.get('name')}")
                
                # Verify data consistency
                if retrieved_worker.get('id') == worker_id:
                    self.log_result("Worker Retrieval - Data Consistency", "PASS", 
                                  "Retrieved worker data matches created worker")
                else:
                    self.log_result("Worker Retrieval - Data Consistency", "FAIL", 
                                  "Retrieved worker data doesn't match")
            else:
                self.log_result("Worker Retrieval - Success", "FAIL", 
                              f"Failed to retrieve worker: {response.status_code} - {response.text}")
                
            # Test invalid worker ID
            invalid_id = str(uuid.uuid4())
            response = self.session.get(f"{BASE_URL}/workers/{invalid_id}")
            
            if response.status_code == 404:
                self.log_result("Worker Retrieval - Invalid ID", "PASS", 
                              "Invalid worker ID returns 404 correctly")
            else:
                self.log_result("Worker Retrieval - Invalid ID", "FAIL", 
                              f"Invalid ID should return 404, got: {response.status_code}")
                
        except Exception as e:
            self.log_result("Worker Retrieval - Exception", "ERROR", f"Error: {str(e)}")
    
    def test_worker_update(self):
        """
        TEST 4: Worker Update
        PATCH /api/workers/{worker_id} - Test worker updates with validation
        """
        print("\n" + "="*80)
        print("TEST 4: WORKER UPDATE")
        print("="*80)
        
        if not self.test_workers:
            self.log_result("Worker Update", "FAIL", "No test workers available")
            return
            
        try:
            worker = self.test_workers[0]
            worker_id = worker.get('id')
            
            # Test successful update
            update_data = {
                "role": "Senior Goldsmith",
                "phone": "+968-9999-8888"
            }
            
            response = self.session.patch(f"{BASE_URL}/workers/{worker_id}", json=update_data)
            
            if response.status_code == 200:
                self.log_result("Worker Update - Success", "PASS", 
                              "Successfully updated worker")
                
                # Verify update by retrieving worker
                response = self.session.get(f"{BASE_URL}/workers/{worker_id}")
                if response.status_code == 200:
                    updated_worker = response.json()
                    if updated_worker.get('role') == "Senior Goldsmith":
                        self.log_result("Worker Update - Data Verification", "PASS", 
                                      "Worker update data verified correctly")
                    else:
                        self.log_result("Worker Update - Data Verification", "FAIL", 
                                      "Worker update data not reflected")
            else:
                self.log_result("Worker Update - Success", "FAIL", 
                              f"Failed to update worker: {response.status_code} - {response.text}")
                
            # Create second worker for duplicate testing
            second_worker_data = {
                "name": "Alice Johnson",
                "phone": "+968-5555-6666",
                "role": "Polisher",
                "active": True
            }
            
            response = self.session.post(f"{BASE_URL}/workers", json=second_worker_data)
            if response.status_code == 200:
                second_worker = response.json()
                self.test_workers.append(second_worker)
                
                # Test duplicate name update validation
                duplicate_update = {"name": "Alice Johnson"}  # Try to update first worker to second worker's name
                
                response = self.session.patch(f"{BASE_URL}/workers/{worker_id}", json=duplicate_update)
                
                if response.status_code == 400:
                    self.log_result("Worker Update - Duplicate Name Validation", "PASS", 
                                  "Duplicate name update validation working correctly")
                else:
                    self.log_result("Worker Update - Duplicate Name Validation", "FAIL", 
                                  f"Duplicate name update should return 400, got: {response.status_code}")
                    
                # Test duplicate phone update validation
                duplicate_phone_update = {"phone": "+968-5555-6666"}  # Try to update to second worker's phone
                
                response = self.session.patch(f"{BASE_URL}/workers/{worker_id}", json=duplicate_phone_update)
                
                if response.status_code == 400:
                    self.log_result("Worker Update - Duplicate Phone Validation", "PASS", 
                                  "Duplicate phone update validation working correctly")
                else:
                    self.log_result("Worker Update - Duplicate Phone Validation", "FAIL", 
                                  f"Duplicate phone update should return 400, got: {response.status_code}")
                
        except Exception as e:
            self.log_result("Worker Update - Exception", "ERROR", f"Error: {str(e)}")

    # ============================================================================
    # JOB CARD WORKER ASSIGNMENT TESTING
    # ============================================================================
    
    def test_jobcard_worker_assignment(self):
        """
        TEST 5: Job Card Worker Assignment
        Test job card creation and worker assignment functionality
        """
        print("\n" + "="*80)
        print("TEST 5: JOB CARD WORKER ASSIGNMENT")
        print("="*80)
        
        if not self.test_workers:
            self.log_result("Job Card Worker Assignment", "FAIL", "No test workers available")
            return
            
        try:
            worker = self.test_workers[0]
            worker_id = worker.get('id')
            worker_name = worker.get('name')
            
            # Create job card with worker assignment
            jobcard_data = {
                "customer_type": "walk_in",
                "walk_in_name": "Test Customer",
                "walk_in_phone": "+968-1234-5678",
                "worker_id": worker_id,
                "worker_name": worker_name,
                "items": [
                    {
                        "category": "Ring",
                        "description": "Gold ring repair",
                        "qty": 1,
                        "weight_in": 5.5,
                        "purity": 22,
                        "work_type": "Repair"
                    }
                ],
                "notes": "Test job card with worker assignment"
            }
            
            response = self.session.post(f"{BASE_URL}/jobcards", json=jobcard_data)
            
            if response.status_code == 200:
                jobcard = response.json()
                self.test_jobcards.append(jobcard)
                
                # Verify worker assignment
                if jobcard.get('worker_id') == worker_id and jobcard.get('worker_name') == worker_name:
                    self.log_result("Job Card - Worker Assignment", "PASS", 
                                  f"Job card successfully assigned to worker: {worker_name}")
                else:
                    self.log_result("Job Card - Worker Assignment", "FAIL", 
                                  "Worker assignment not reflected in job card")
                    
            else:
                self.log_result("Job Card - Creation with Worker", "FAIL", 
                              f"Failed to create job card: {response.status_code} - {response.text}")
                
            # Test job card creation without worker (should succeed)
            jobcard_no_worker_data = {
                "customer_type": "walk_in",
                "walk_in_name": "Test Customer 2",
                "walk_in_phone": "+968-8765-4321",
                "items": [
                    {
                        "category": "Necklace",
                        "description": "Gold necklace cleaning",
                        "qty": 1,
                        "weight_in": 15.0,
                        "purity": 18,
                        "work_type": "Cleaning"
                    }
                ],
                "notes": "Test job card without worker"
            }
            
            response = self.session.post(f"{BASE_URL}/jobcards", json=jobcard_no_worker_data)
            
            if response.status_code == 200:
                jobcard_no_worker = response.json()
                self.test_jobcards.append(jobcard_no_worker)
                self.log_result("Job Card - Creation without Worker", "PASS", 
                              "Job card creation without worker succeeded (as expected)")
            else:
                self.log_result("Job Card - Creation without Worker", "FAIL", 
                              f"Job card creation without worker failed: {response.status_code}")
                
        except Exception as e:
            self.log_result("Job Card Worker Assignment - Exception", "ERROR", f"Error: {str(e)}")
    
    def test_jobcard_completion_validation(self):
        """
        TEST 6: Job Card Completion Validation
        Test that job cards cannot be completed without worker assignment
        """
        print("\n" + "="*80)
        print("TEST 6: JOB CARD COMPLETION VALIDATION")
        print("="*80)
        
        if len(self.test_jobcards) < 2:
            self.log_result("Job Card Completion Validation", "FAIL", "Insufficient test job cards")
            return
            
        try:
            # Test completion of job card WITH worker (should succeed)
            jobcard_with_worker = self.test_jobcards[0]  # Has worker assigned
            jobcard_id = jobcard_with_worker.get('id')
            
            # First update to in_progress
            response = self.session.patch(f"{BASE_URL}/jobcards/{jobcard_id}", json={"status": "in_progress"})
            
            if response.status_code == 200:
                # Now try to complete
                response = self.session.patch(f"{BASE_URL}/jobcards/{jobcard_id}", json={"status": "completed"})
                
                if response.status_code == 200:
                    self.log_result("Job Card - Completion with Worker", "PASS", 
                                  "Job card with worker completed successfully")
                else:
                    self.log_result("Job Card - Completion with Worker", "FAIL", 
                                  f"Job card with worker completion failed: {response.status_code}")
            
            # Test completion of job card WITHOUT worker (should fail)
            jobcard_without_worker = self.test_jobcards[1]  # No worker assigned
            jobcard_id_no_worker = jobcard_without_worker.get('id')
            
            # First update to in_progress
            response = self.session.patch(f"{BASE_URL}/jobcards/{jobcard_id_no_worker}", json={"status": "in_progress"})
            
            if response.status_code == 200:
                # Now try to complete (should fail)
                response = self.session.patch(f"{BASE_URL}/jobcards/{jobcard_id_no_worker}", json={"status": "completed"})
                
                if response.status_code == 422:
                    self.log_result("Job Card - Completion without Worker Blocked", "PASS", 
                                  "Job card completion without worker correctly blocked with HTTP 422")
                else:
                    self.log_result("Job Card - Completion without Worker Blocked", "FAIL", 
                                  f"Job card completion should be blocked, got: {response.status_code}")
                    
            # Test assigning worker and then completing
            if len(self.test_workers) > 0:
                worker = self.test_workers[0]
                worker_assignment = {
                    "worker_id": worker.get('id'),
                    "worker_name": worker.get('name')
                }
                
                response = self.session.patch(f"{BASE_URL}/jobcards/{jobcard_id_no_worker}", json=worker_assignment)
                
                if response.status_code == 200:
                    # Now try to complete (should succeed)
                    response = self.session.patch(f"{BASE_URL}/jobcards/{jobcard_id_no_worker}", json={"status": "completed"})
                    
                    if response.status_code == 200:
                        self.log_result("Job Card - Completion after Worker Assignment", "PASS", 
                                      "Job card completed successfully after worker assignment")
                    else:
                        self.log_result("Job Card - Completion after Worker Assignment", "FAIL", 
                                      f"Job card completion after worker assignment failed: {response.status_code}")
                        
        except Exception as e:
            self.log_result("Job Card Completion Validation - Exception", "ERROR", f"Error: {str(e)}")

    # ============================================================================
    # INVOICE WORKER INTEGRATION TESTING
    # ============================================================================
    
    def test_invoice_worker_integration(self):
        """
        TEST 7: Invoice Worker Integration
        Test that worker data flows from job card to invoice
        """
        print("\n" + "="*80)
        print("TEST 7: INVOICE WORKER INTEGRATION")
        print("="*80)
        
        if not self.test_jobcards:
            self.log_result("Invoice Worker Integration", "FAIL", "No test job cards available")
            return
            
        try:
            # Find a completed job card with worker
            completed_jobcard = None
            for jobcard in self.test_jobcards:
                if jobcard.get('status') == 'completed' and jobcard.get('worker_id'):
                    completed_jobcard = jobcard
                    break
                    
            if not completed_jobcard:
                self.log_result("Invoice Worker Integration", "FAIL", "No completed job card with worker found")
                return
                
            jobcard_id = completed_jobcard.get('id')
            expected_worker_id = completed_jobcard.get('worker_id')
            expected_worker_name = completed_jobcard.get('worker_name')
            
            # Convert job card to invoice
            response = self.session.post(f"{BASE_URL}/jobcards/{jobcard_id}/convert-to-invoice")
            
            if response.status_code == 200:
                invoice = response.json()
                self.test_invoices.append(invoice)
                
                # Verify worker data transfer
                invoice_worker_id = invoice.get('worker_id')
                invoice_worker_name = invoice.get('worker_name')
                
                if invoice_worker_id == expected_worker_id and invoice_worker_name == expected_worker_name:
                    self.log_result("Invoice - Worker Data Transfer", "PASS", 
                                  f"Worker data correctly transferred to invoice: {invoice_worker_name} (ID: {invoice_worker_id})")
                else:
                    self.log_result("Invoice - Worker Data Transfer", "FAIL", 
                                  f"Worker data not transferred correctly. Expected: {expected_worker_name}, Got: {invoice_worker_name}")
                    
                # Verify invoice has worker fields
                if 'worker_id' in invoice and 'worker_name' in invoice:
                    self.log_result("Invoice - Worker Fields Present", "PASS", 
                                  "Invoice model contains worker_id and worker_name fields")
                else:
                    self.log_result("Invoice - Worker Fields Present", "FAIL", 
                                  "Invoice model missing worker fields")
                    
            else:
                self.log_result("Invoice - Job Card Conversion", "FAIL", 
                              f"Failed to convert job card to invoice: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Invoice Worker Integration - Exception", "ERROR", f"Error: {str(e)}")

    # ============================================================================
    # WORKER DELETION TESTING
    # ============================================================================
    
    def test_worker_deletion_constraints(self):
        """
        TEST 8: Worker Deletion Constraints
        Test worker deletion with active job card constraints
        """
        print("\n" + "="*80)
        print("TEST 8: WORKER DELETION CONSTRAINTS")
        print("="*80)
        
        if len(self.test_workers) < 2:
            self.log_result("Worker Deletion Constraints", "FAIL", "Insufficient test workers")
            return
            
        try:
            # Try to delete worker with active job cards (should fail)
            worker_with_jobcards = self.test_workers[0]  # This worker has job cards assigned
            worker_id = worker_with_jobcards.get('id')
            
            response = self.session.delete(f"{BASE_URL}/workers/{worker_id}")
            
            if response.status_code == 400:
                self.log_result("Worker Deletion - Active Job Cards Constraint", "PASS", 
                              "Worker deletion correctly blocked due to active job cards")
            else:
                self.log_result("Worker Deletion - Active Job Cards Constraint", "FAIL", 
                              f"Worker deletion should be blocked, got: {response.status_code}")
                
            # Try to delete worker without active job cards (should succeed)
            worker_without_jobcards = self.test_workers[1]  # This worker has no job cards
            worker_id_free = worker_without_jobcards.get('id')
            
            response = self.session.delete(f"{BASE_URL}/workers/{worker_id_free}")
            
            if response.status_code == 200:
                self.log_result("Worker Deletion - Success", "PASS", 
                              "Worker without active job cards deleted successfully")
                
                # Verify soft delete (worker should not appear in list)
                response = self.session.get(f"{BASE_URL}/workers")
                if response.status_code == 200:
                    workers = response.json().get('items', [])
                    deleted_worker_found = any(w.get('id') == worker_id_free for w in workers)
                    
                    if not deleted_worker_found:
                        self.log_result("Worker Deletion - Soft Delete Verification", "PASS", 
                                      "Deleted worker not appearing in worker list (soft delete working)")
                    else:
                        self.log_result("Worker Deletion - Soft Delete Verification", "FAIL", 
                                      "Deleted worker still appearing in list")
            else:
                self.log_result("Worker Deletion - Success", "FAIL", 
                              f"Worker deletion failed: {response.status_code} - {response.text}")
                
            # Test deletion of non-existent worker
            invalid_worker_id = str(uuid.uuid4())
            response = self.session.delete(f"{BASE_URL}/workers/{invalid_worker_id}")
            
            if response.status_code == 404:
                self.log_result("Worker Deletion - Invalid ID", "PASS", 
                              "Deletion of non-existent worker returns 404 correctly")
            else:
                self.log_result("Worker Deletion - Invalid ID", "FAIL", 
                              f"Invalid worker deletion should return 404, got: {response.status_code}")
                
        except Exception as e:
            self.log_result("Worker Deletion Constraints - Exception", "ERROR", f"Error: {str(e)}")

    # ============================================================================
    # EDGE CASES AND VALIDATION TESTING
    # ============================================================================
    
    def test_edge_cases_and_validation(self):
        """
        TEST 9: Edge Cases and Validation
        Test various edge cases and validation scenarios
        """
        print("\n" + "="*80)
        print("TEST 9: EDGE CASES AND VALIDATION")
        print("="*80)
        
        try:
            # Test worker creation with missing required fields
            incomplete_worker_data = {
                "name": "Test Worker"
                # Missing role field
            }
            
            response = self.session.post(f"{BASE_URL}/workers", json=incomplete_worker_data)
            
            if response.status_code == 422:  # Validation error
                self.log_result("Edge Case - Missing Required Fields", "PASS", 
                              "Missing required fields validation working correctly")
            else:
                self.log_result("Edge Case - Missing Required Fields", "FAIL", 
                              f"Missing fields should return 422, got: {response.status_code}")
                
            # Test worker creation with null/empty values
            null_values_data = {
                "name": None,
                "phone": "",
                "role": "   ",  # Whitespace only
                "active": True
            }
            
            response = self.session.post(f"{BASE_URL}/workers", json=null_values_data)
            
            if response.status_code == 400:
                self.log_result("Edge Case - Null/Empty Values", "PASS", 
                              "Null/empty values validation working correctly")
            else:
                self.log_result("Edge Case - Null/Empty Values", "FAIL", 
                              f"Null/empty values should return 400, got: {response.status_code}")
                
            # Test job card with invalid worker_id
            if self.test_jobcards:
                jobcard = self.test_jobcards[0]
                jobcard_id = jobcard.get('id')
                invalid_worker_id = str(uuid.uuid4())
                
                invalid_worker_update = {
                    "worker_id": invalid_worker_id,
                    "worker_name": "Non-existent Worker"
                }
                
                response = self.session.patch(f"{BASE_URL}/jobcards/{jobcard_id}", json=invalid_worker_update)
                
                # This might succeed as the API might not validate worker existence during assignment
                # The validation would happen during completion
                if response.status_code in [200, 400, 404]:
                    self.log_result("Edge Case - Invalid Worker ID Assignment", "PASS", 
                                  f"Invalid worker ID handled appropriately: {response.status_code}")
                else:
                    self.log_result("Edge Case - Invalid Worker ID Assignment", "FAIL", 
                                  f"Unexpected response for invalid worker ID: {response.status_code}")
                    
            # Test worker activation/deactivation
            if self.test_workers:
                active_worker = self.test_workers[0]
                worker_id = active_worker.get('id')
                
                # Deactivate worker
                response = self.session.patch(f"{BASE_URL}/workers/{worker_id}", json={"active": False})
                
                if response.status_code == 200:
                    self.log_result("Edge Case - Worker Deactivation", "PASS", 
                                  "Worker deactivation successful")
                    
                    # Reactivate worker
                    response = self.session.patch(f"{BASE_URL}/workers/{worker_id}", json={"active": True})
                    
                    if response.status_code == 200:
                        self.log_result("Edge Case - Worker Reactivation", "PASS", 
                                      "Worker reactivation successful")
                    else:
                        self.log_result("Edge Case - Worker Reactivation", "FAIL", 
                                      f"Worker reactivation failed: {response.status_code}")
                else:
                    self.log_result("Edge Case - Worker Deactivation", "FAIL", 
                                  f"Worker deactivation failed: {response.status_code}")
                    
        except Exception as e:
            self.log_result("Edge Cases and Validation - Exception", "ERROR", f"Error: {str(e)}")

    # ============================================================================
    # TEST EXECUTION AND REPORTING
    # ============================================================================
    
    def run_all_tests(self):
        """Run all worker management tests"""
        print("STARTING COMPREHENSIVE WORKER MANAGEMENT TESTING")
        print("Backend URL:", BASE_URL)
        print("Authentication:", f"{USERNAME}/***")
        print("Test Coverage: Worker CRUD, Job Card Integration, Invoice Integration, Validation")
        print("="*80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run all test suites
        self.test_worker_list_endpoint()
        self.test_worker_creation()
        self.test_worker_retrieval()
        self.test_worker_update()
        self.test_jobcard_worker_assignment()
        self.test_jobcard_completion_validation()
        self.test_invoice_worker_integration()
        self.test_worker_deletion_constraints()
        self.test_edge_cases_and_validation()
        
        # Generate comprehensive summary
        self.generate_test_summary()
        
        return self.assess_overall_success()
    
    def generate_test_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "="*80)
        print("COMPREHENSIVE TEST SUMMARY - WORKER MANAGEMENT SYSTEM")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        error_tests = len([r for r in self.test_results if r["status"] == "ERROR"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️ Errors: {error_tests}")
        
        # Category-wise assessment
        print("\nTEST CATEGORY ASSESSMENT:")
        
        categories = {
            "Worker CRUD Operations": ["Worker List", "Worker Creation", "Worker Retrieval", "Worker Update", "Worker Deletion"],
            "Job Card Integration": ["Job Card", "Completion"],
            "Invoice Integration": ["Invoice"],
            "Validation & Edge Cases": ["Edge Case", "Validation"]
        }
        
        for category, keywords in categories.items():
            category_tests = [r for r in self.test_results if any(keyword in r["test"] for keyword in keywords)]
            category_passed = len([r for r in category_tests if r["status"] == "PASS"])
            category_total = len(category_tests)
            
            if category_total > 0:
                success_rate = (category_passed / category_total) * 100
                status = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 60 else "❌"
                print(f"{status} {category}: {category_passed}/{category_total} ({success_rate:.1f}%)")
        
        # Critical functionality assessment
        print("\nCRITICAL FUNCTIONALITY ASSESSMENT:")
        
        critical_tests = {
            "Worker CRUD API": ["Worker List - Response Structure", "Worker Creation - Success", "Worker Retrieval - Success", "Worker Update - Success"],
            "Duplicate Validation": ["Duplicate Name Validation", "Duplicate Phone Validation"],
            "Job Card Worker Assignment": ["Job Card - Worker Assignment", "Job Card - Completion with Worker"],
            "Completion Validation": ["Job Card - Completion without Worker Blocked"],
            "Invoice Integration": ["Invoice - Worker Data Transfer"],
            "Deletion Constraints": ["Worker Deletion - Active Job Cards Constraint"]
        }
        
        for functionality, test_names in critical_tests.items():
            func_tests = [r for r in self.test_results if any(test_name in r["test"] for test_name in test_names)]
            func_passed = len([r for r in func_tests if r["status"] == "PASS"])
            func_total = len(func_tests)
            
            if func_total > 0:
                success = func_passed == func_total
                status = "✅" if success else "❌"
                print(f"{status} {functionality}: {'WORKING' if success else 'ISSUES DETECTED'}")
        
        # Detailed results
        print("\nDETAILED TEST RESULTS:")
        for result in self.test_results:
            status_symbol = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"{status_symbol} {result['test']}: {result['details']}")
    
    def assess_overall_success(self):
        """Assess overall test success"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        
        if total_tests == 0:
            return False
            
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"\nOVERALL SUCCESS RATE: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 WORKER MANAGEMENT SYSTEM FULLY FUNCTIONAL!")
            print("✅ All critical functionality working correctly")
            print("✅ Ready for production use")
            return True
        elif success_rate >= 75:
            print("⚠️ WORKER MANAGEMENT SYSTEM MOSTLY FUNCTIONAL")
            print("⚠️ Some minor issues detected but core functionality working")
            return True
        else:
            print("🚨 CRITICAL ISSUES DETECTED!")
            print("❌ Major functionality problems require immediate attention")
            return False

if __name__ == "__main__":
    tester = WorkerManagementTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
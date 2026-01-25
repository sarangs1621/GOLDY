#!/usr/bin/env python3
"""
Focused Worker Management Testing - Critical Functionality Only

This script focuses on testing the core worker management functionality
that was requested in the review, with proper error handling and debugging.
"""

import requests
import json
import sys
from datetime import datetime
import uuid

# Configuration
BASE_URL = "https://worker-class-error.preview.emergentagent.com/api"
USERNAME = "admin"
PASSWORD = "admin123"

class FocusedWorkerTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.created_workers = []
        self.created_jobcards = []
        
    def log_result(self, test_name, status, details):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
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

    def test_worker_crud_operations(self):
        """Test core worker CRUD operations"""
        print("\n" + "="*80)
        print("TESTING WORKER CRUD OPERATIONS")
        print("="*80)
        
        # 1. Test Worker Creation
        try:
            worker_data = {
                "name": "Ahmed Al-Rashid",
                "phone": "+968-9123-4567",
                "role": "Senior Goldsmith",
                "active": True
            }
            
            response = self.session.post(f"{BASE_URL}/workers", json=worker_data)
            
            if response.status_code == 200:
                worker = response.json()
                self.created_workers.append(worker)
                self.log_result("Worker Creation", "PASS", 
                              f"Created worker: {worker.get('name')} (ID: {worker.get('id')})")
            else:
                self.log_result("Worker Creation", "FAIL", 
                              f"Failed to create worker: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Worker Creation", "ERROR", f"Error: {str(e)}")
            return False
        
        # 2. Test Worker List
        try:
            response = self.session.get(f"{BASE_URL}/workers")
            
            if response.status_code == 200:
                data = response.json()
                workers = data.get("items", [])
                self.log_result("Worker List", "PASS", 
                              f"Retrieved {len(workers)} workers")
            else:
                self.log_result("Worker List", "FAIL", 
                              f"Failed to list workers: {response.status_code}")
                
        except Exception as e:
            self.log_result("Worker List", "ERROR", f"Error: {str(e)}")
        
        # 3. Test Worker Retrieval
        if self.created_workers:
            try:
                worker_id = self.created_workers[0].get('id')
                response = self.session.get(f"{BASE_URL}/workers/{worker_id}")
                
                if response.status_code == 200:
                    worker = response.json()
                    self.log_result("Worker Retrieval", "PASS", 
                                  f"Retrieved worker: {worker.get('name')}")
                else:
                    self.log_result("Worker Retrieval", "FAIL", 
                                  f"Failed to retrieve worker: {response.status_code}")
                    
            except Exception as e:
                self.log_result("Worker Retrieval", "ERROR", f"Error: {str(e)}")
        
        # 4. Test Worker Update
        if self.created_workers:
            try:
                worker_id = self.created_workers[0].get('id')
                update_data = {"role": "Master Goldsmith"}
                
                response = self.session.patch(f"{BASE_URL}/workers/{worker_id}", json=update_data)
                
                if response.status_code == 200:
                    self.log_result("Worker Update", "PASS", 
                                  "Successfully updated worker role")
                else:
                    self.log_result("Worker Update", "FAIL", 
                                  f"Failed to update worker: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.log_result("Worker Update", "ERROR", f"Error: {str(e)}")
        
        return True

    def test_worker_validation(self):
        """Test worker validation scenarios"""
        print("\n" + "="*80)
        print("TESTING WORKER VALIDATION")
        print("="*80)
        
        # Test duplicate name validation
        if self.created_workers:
            try:
                duplicate_data = {
                    "name": self.created_workers[0].get('name'),  # Same name
                    "phone": "+968-8888-9999",
                    "role": "Polisher",
                    "active": True
                }
                
                response = self.session.post(f"{BASE_URL}/workers", json=duplicate_data)
                
                if response.status_code == 400:
                    self.log_result("Duplicate Name Validation", "PASS", 
                                  "Duplicate name correctly rejected")
                else:
                    self.log_result("Duplicate Name Validation", "FAIL", 
                                  f"Duplicate name should be rejected, got: {response.status_code}")
                    
            except Exception as e:
                self.log_result("Duplicate Name Validation", "ERROR", f"Error: {str(e)}")
        
        # Test duplicate phone validation
        if self.created_workers:
            try:
                duplicate_phone_data = {
                    "name": "Different Worker",
                    "phone": self.created_workers[0].get('phone'),  # Same phone
                    "role": "Designer",
                    "active": True
                }
                
                response = self.session.post(f"{BASE_URL}/workers", json=duplicate_phone_data)
                
                if response.status_code == 400:
                    self.log_result("Duplicate Phone Validation", "PASS", 
                                  "Duplicate phone correctly rejected")
                else:
                    self.log_result("Duplicate Phone Validation", "FAIL", 
                                  f"Duplicate phone should be rejected, got: {response.status_code}")
                    
            except Exception as e:
                self.log_result("Duplicate Phone Validation", "ERROR", f"Error: {str(e)}")

    def test_jobcard_worker_integration(self):
        """Test job card worker integration"""
        print("\n" + "="*80)
        print("TESTING JOB CARD WORKER INTEGRATION")
        print("="*80)
        
        if not self.created_workers:
            self.log_result("Job Card Worker Integration", "FAIL", "No workers available for testing")
            return
        
        worker = self.created_workers[0]
        worker_id = worker.get('id')
        worker_name = worker.get('name')
        
        # Test job card creation with worker
        try:
            jobcard_data = {
                "customer_type": "walk_in",
                "walk_in_name": "Fatima Al-Zahra",
                "walk_in_phone": "+968-7777-8888",
                "worker_id": worker_id,
                "worker_name": worker_name,
                "items": [
                    {
                        "category": "Gold Rings",  # Using the category we created
                        "description": "Ring resizing and polishing",
                        "qty": 1,
                        "weight_in": 8.5,
                        "purity": 22,
                        "work_type": "Repair"
                    }
                ],
                "notes": "Customer wants ring resized from 7 to 8"
            }
            
            response = self.session.post(f"{BASE_URL}/jobcards", json=jobcard_data)
            
            if response.status_code == 200:
                jobcard = response.json()
                self.created_jobcards.append(jobcard)
                
                # Verify worker assignment
                if jobcard.get('worker_id') == worker_id:
                    self.log_result("Job Card Worker Assignment", "PASS", 
                                  f"Job card successfully assigned to worker: {worker_name}")
                else:
                    self.log_result("Job Card Worker Assignment", "FAIL", 
                                  "Worker assignment not reflected in job card")
            else:
                self.log_result("Job Card Creation with Worker", "FAIL", 
                              f"Failed to create job card: {response.status_code} - {response.text}")
                # Let's debug this
                print(f"DEBUG: Job card creation failed. Response: {response.text}")
                
        except Exception as e:
            self.log_result("Job Card Creation with Worker", "ERROR", f"Error: {str(e)}")
        
        # Test job card creation without worker
        try:
            jobcard_no_worker_data = {
                "customer_type": "walk_in",
                "walk_in_name": "Omar Al-Balushi",
                "walk_in_phone": "+968-6666-7777",
                "items": [
                    {
                        "category": "Gold Chains",
                        "description": "Chain repair",
                        "qty": 1,
                        "weight_in": 12.0,
                        "purity": 18,
                        "work_type": "Repair"
                    }
                ],
                "notes": "Chain link broken"
            }
            
            response = self.session.post(f"{BASE_URL}/jobcards", json=jobcard_no_worker_data)
            
            if response.status_code == 200:
                jobcard = response.json()
                self.created_jobcards.append(jobcard)
                self.log_result("Job Card Creation without Worker", "PASS", 
                              "Job card created without worker (as expected)")
            else:
                self.log_result("Job Card Creation without Worker", "FAIL", 
                              f"Job card creation without worker failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Job Card Creation without Worker", "ERROR", f"Error: {str(e)}")

    def test_jobcard_completion_validation(self):
        """Test job card completion validation"""
        print("\n" + "="*80)
        print("TESTING JOB CARD COMPLETION VALIDATION")
        print("="*80)
        
        if len(self.created_jobcards) < 2:
            self.log_result("Job Card Completion Validation", "FAIL", "Insufficient job cards for testing")
            return
        
        # Test completion without worker (should fail)
        try:
            jobcard_no_worker = None
            for jc in self.created_jobcards:
                if not jc.get('worker_id'):
                    jobcard_no_worker = jc
                    break
            
            if jobcard_no_worker:
                jobcard_id = jobcard_no_worker.get('id')
                
                # Try to complete directly (should fail)
                response = self.session.patch(f"{BASE_URL}/jobcards/{jobcard_id}", 
                                            json={"status": "completed"})
                
                if response.status_code == 422:
                    self.log_result("Completion Validation - No Worker", "PASS", 
                                  "Job card completion correctly blocked without worker (HTTP 422)")
                else:
                    self.log_result("Completion Validation - No Worker", "FAIL", 
                                  f"Expected HTTP 422, got: {response.status_code}")
            else:
                self.log_result("Completion Validation - No Worker", "FAIL", 
                              "No job card without worker found for testing")
                
        except Exception as e:
            self.log_result("Completion Validation - No Worker", "ERROR", f"Error: {str(e)}")
        
        # Test completion with worker (should succeed)
        try:
            jobcard_with_worker = None
            for jc in self.created_jobcards:
                if jc.get('worker_id'):
                    jobcard_with_worker = jc
                    break
            
            if jobcard_with_worker:
                jobcard_id = jobcard_with_worker.get('id')
                
                # First set to in_progress
                response = self.session.patch(f"{BASE_URL}/jobcards/{jobcard_id}", 
                                            json={"status": "in_progress"})
                
                if response.status_code == 200:
                    # Now complete it
                    response = self.session.patch(f"{BASE_URL}/jobcards/{jobcard_id}", 
                                                json={"status": "completed"})
                    
                    if response.status_code == 200:
                        self.log_result("Completion Validation - With Worker", "PASS", 
                                      "Job card with worker completed successfully")
                    else:
                        self.log_result("Completion Validation - With Worker", "FAIL", 
                                      f"Job card completion failed: {response.status_code} - {response.text}")
                else:
                    self.log_result("Completion Validation - With Worker", "FAIL", 
                                  f"Failed to set job card to in_progress: {response.status_code}")
            else:
                self.log_result("Completion Validation - With Worker", "FAIL", 
                              "No job card with worker found for testing")
                
        except Exception as e:
            self.log_result("Completion Validation - With Worker", "ERROR", f"Error: {str(e)}")

    def test_invoice_worker_integration(self):
        """Test invoice worker integration"""
        print("\n" + "="*80)
        print("TESTING INVOICE WORKER INTEGRATION")
        print("="*80)
        
        # Find a completed job card with worker
        completed_jobcard = None
        for jc in self.created_jobcards:
            if jc.get('status') == 'completed' and jc.get('worker_id'):
                completed_jobcard = jc
                break
        
        if not completed_jobcard:
            self.log_result("Invoice Worker Integration", "FAIL", 
                          "No completed job card with worker available")
            return
        
        try:
            jobcard_id = completed_jobcard.get('id')
            expected_worker_id = completed_jobcard.get('worker_id')
            expected_worker_name = completed_jobcard.get('worker_name')
            
            # Convert job card to invoice
            response = self.session.post(f"{BASE_URL}/jobcards/{jobcard_id}/convert-to-invoice")
            
            if response.status_code == 200:
                invoice = response.json()
                
                # Verify worker data transfer
                invoice_worker_id = invoice.get('worker_id')
                invoice_worker_name = invoice.get('worker_name')
                
                if invoice_worker_id == expected_worker_id and invoice_worker_name == expected_worker_name:
                    self.log_result("Invoice Worker Data Transfer", "PASS", 
                                  f"Worker data correctly transferred: {invoice_worker_name}")
                else:
                    self.log_result("Invoice Worker Data Transfer", "FAIL", 
                                  f"Worker data not transferred correctly")
            else:
                self.log_result("Invoice Worker Integration", "FAIL", 
                              f"Failed to convert job card to invoice: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Invoice Worker Integration", "ERROR", f"Error: {str(e)}")

    def test_worker_deletion_constraints(self):
        """Test worker deletion constraints"""
        print("\n" + "="*80)
        print("TESTING WORKER DELETION CONSTRAINTS")
        print("="*80)
        
        if not self.created_workers:
            self.log_result("Worker Deletion Constraints", "FAIL", "No workers available for testing")
            return
        
        # Create a worker without job cards for deletion testing
        try:
            deletable_worker_data = {
                "name": "Temporary Worker",
                "phone": "+968-0000-1111",
                "role": "Helper",
                "active": True
            }
            
            response = self.session.post(f"{BASE_URL}/workers", json=deletable_worker_data)
            
            if response.status_code == 200:
                deletable_worker = response.json()
                worker_id = deletable_worker.get('id')
                
                # Try to delete this worker (should succeed)
                response = self.session.delete(f"{BASE_URL}/workers/{worker_id}")
                
                if response.status_code == 200:
                    self.log_result("Worker Deletion - No Job Cards", "PASS", 
                                  "Worker without job cards deleted successfully")
                else:
                    self.log_result("Worker Deletion - No Job Cards", "FAIL", 
                                  f"Worker deletion failed: {response.status_code} - {response.text}")
            else:
                self.log_result("Worker Deletion - Setup", "FAIL", 
                              f"Failed to create deletable worker: {response.status_code}")
                
        except Exception as e:
            self.log_result("Worker Deletion - No Job Cards", "ERROR", f"Error: {str(e)}")
        
        # Try to delete worker with job cards (should fail)
        try:
            worker_with_jobcards = None
            for worker in self.created_workers:
                # Check if this worker has job cards
                worker_id = worker.get('id')
                has_jobcards = any(jc.get('worker_id') == worker_id for jc in self.created_jobcards)
                if has_jobcards:
                    worker_with_jobcards = worker
                    break
            
            if worker_with_jobcards:
                worker_id = worker_with_jobcards.get('id')
                response = self.session.delete(f"{BASE_URL}/workers/{worker_id}")
                
                if response.status_code == 400:
                    self.log_result("Worker Deletion - With Job Cards", "PASS", 
                                  "Worker deletion correctly blocked due to active job cards")
                else:
                    self.log_result("Worker Deletion - With Job Cards", "FAIL", 
                                  f"Expected HTTP 400, got: {response.status_code}")
            else:
                self.log_result("Worker Deletion - With Job Cards", "FAIL", 
                              "No worker with job cards found for testing")
                
        except Exception as e:
            self.log_result("Worker Deletion - With Job Cards", "ERROR", f"Error: {str(e)}")

    def run_focused_tests(self):
        """Run focused worker management tests"""
        print("STARTING FOCUSED WORKER MANAGEMENT TESTING")
        print("Backend URL:", BASE_URL)
        print("Focus: Core Worker CRUD + Job Card Integration + Invoice Integration")
        print("="*80)
        
        # Authenticate
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run focused test suites
        success = True
        
        if not self.test_worker_crud_operations():
            success = False
        
        self.test_worker_validation()
        self.test_jobcard_worker_integration()
        self.test_jobcard_completion_validation()
        self.test_invoice_worker_integration()
        self.test_worker_deletion_constraints()
        
        # Generate summary
        self.generate_summary()
        
        return success
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "="*80)
        print("FOCUSED WORKER MANAGEMENT TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        error_tests = len([r for r in self.test_results if r["status"] == "ERROR"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️ Errors: {error_tests}")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        # Critical functionality assessment
        print("\nCRITICAL FUNCTIONALITY STATUS:")
        
        critical_functions = {
            "Worker CRUD Operations": ["Worker Creation", "Worker List", "Worker Retrieval", "Worker Update"],
            "Worker Validation": ["Duplicate Name Validation", "Duplicate Phone Validation"],
            "Job Card Integration": ["Job Card Worker Assignment", "Job Card Creation"],
            "Completion Validation": ["Completion Validation"],
            "Invoice Integration": ["Invoice Worker Data Transfer"],
            "Deletion Constraints": ["Worker Deletion"]
        }
        
        for function, keywords in critical_functions.items():
            func_tests = [r for r in self.test_results if any(keyword in r["test"] for keyword in keywords)]
            func_passed = len([r for r in func_tests if r["status"] == "PASS"])
            func_total = len(func_tests)
            
            if func_total > 0:
                func_success = func_passed == func_total
                status = "✅" if func_success else "❌"
                print(f"{status} {function}: {'WORKING' if func_success else 'ISSUES DETECTED'}")
        
        # Detailed results
        print("\nDETAILED RESULTS:")
        for result in self.test_results:
            status_symbol = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"{status_symbol} {result['test']}: {result['details']}")
        
        # Overall assessment
        if success_rate >= 85:
            print(f"\n🎉 WORKER MANAGEMENT SYSTEM CORE FUNCTIONALITY WORKING!")
            print("✅ Critical worker operations are functional")
            return True
        else:
            print(f"\n🚨 CRITICAL ISSUES DETECTED!")
            print("❌ Core functionality has significant problems")
            return False

if __name__ == "__main__":
    tester = FocusedWorkerTester()
    success = tester.run_focused_tests()
    sys.exit(0 if success else 1)
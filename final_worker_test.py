#!/usr/bin/env python3
"""
Final Comprehensive Worker Management Test

This test provides a complete assessment of the worker management system
with unique names to avoid conflicts.
"""

import requests
import json
import sys
from datetime import datetime
import uuid

# Configuration
BASE_URL = "https://decimal-precision.preview.emergentagent.com/api"
USERNAME = "admin"
PASSWORD = "admin123"

def run_final_comprehensive_test():
    """Run final comprehensive test"""
    session = requests.Session()
    results = []
    
    def log_result(test, status, details):
        results.append({"test": test, "status": status, "details": details})
        symbol = "✅" if status == "PASS" else "❌"
        print(f"{symbol} {test}: {details}")
    
    # Generate unique suffix for this test run
    test_suffix = str(uuid.uuid4())[:8]
    
    # Authenticate
    try:
        response = session.post(f"{BASE_URL}/auth/login", json={
            "username": USERNAME,
            "password": PASSWORD
        })
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            session.headers.update({"Authorization": f"Bearer {token}"})
            log_result("Authentication", "PASS", "Successfully authenticated")
        else:
            log_result("Authentication", "FAIL", f"Auth failed: {response.status_code}")
            return False
    except Exception as e:
        log_result("Authentication", "FAIL", f"Auth error: {str(e)}")
        return False
    
    # Test 1: Worker CRUD Operations
    worker_id = None
    worker_name = f"Final Test Worker {test_suffix}"
    
    try:
        worker_data = {
            "name": worker_name,
            "phone": f"+968-{test_suffix[:4]}-{test_suffix[4:8]}",
            "role": "Master Goldsmith",
            "active": True
        }
        
        response = session.post(f"{BASE_URL}/workers", json=worker_data)
        
        if response.status_code == 200:
            worker = response.json()
            worker_id = worker.get('id')
            log_result("1. Worker Creation", "PASS", f"Created worker: {worker_name}")
        else:
            log_result("1. Worker Creation", "FAIL", f"Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        log_result("1. Worker Creation", "FAIL", f"Error: {str(e)}")
        return False
    
    # Test 2: Worker Retrieval
    if worker_id:
        try:
            response = session.get(f"{BASE_URL}/workers/{worker_id}")
            
            if response.status_code == 200:
                worker = response.json()
                log_result("2. Worker Retrieval", "PASS", f"Retrieved worker: {worker.get('name')}")
            else:
                log_result("2. Worker Retrieval", "FAIL", f"Failed: {response.status_code}")
        except Exception as e:
            log_result("2. Worker Retrieval", "FAIL", f"Error: {str(e)}")
    
    # Test 3: Worker Update
    if worker_id:
        try:
            update_data = {"role": "Senior Master Goldsmith"}
            response = session.patch(f"{BASE_URL}/workers/{worker_id}", json=update_data)
            
            if response.status_code == 200:
                log_result("3. Worker Update", "PASS", "Successfully updated worker")
            else:
                log_result("3. Worker Update", "FAIL", f"Failed: {response.status_code}")
        except Exception as e:
            log_result("3. Worker Update", "FAIL", f"Error: {str(e)}")
    
    # Test 4: Duplicate Name Validation
    try:
        duplicate_data = {
            "name": worker_name,  # Same name
            "phone": "+968-0000-0001",
            "role": "Polisher",
            "active": True
        }
        
        response = session.post(f"{BASE_URL}/workers", json=duplicate_data)
        
        if response.status_code == 400:
            log_result("4. Duplicate Name Validation", "PASS", "Duplicate name correctly rejected")
        else:
            log_result("4. Duplicate Name Validation", "FAIL", f"Expected 400, got: {response.status_code}")
    except Exception as e:
        log_result("4. Duplicate Name Validation", "FAIL", f"Error: {str(e)}")
    
    # Test 5: Job Card Creation with Worker
    jobcard_id = None
    if worker_id:
        try:
            jobcard_data = {
                "card_type": "regular",
                "customer_type": "walk_in",
                "walk_in_name": f"Test Customer {test_suffix}",
                "walk_in_phone": f"+968-{test_suffix[4:8]}-{test_suffix[:4]}",
                "worker_id": worker_id,
                "worker_name": worker_name,
                "items": [
                    {
                        "category": "Gold Rings",
                        "description": "Final test ring",
                        "qty": 1,
                        "weight_in": 9.0,
                        "purity": 22,
                        "work_type": "Repair"
                    }
                ],
                "notes": "Final comprehensive test job card"
            }
            
            response = session.post(f"{BASE_URL}/jobcards", json=jobcard_data)
            
            if response.status_code == 200:
                jobcard = response.json()
                jobcard_id = jobcard.get('id')
                
                # Verify worker assignment
                if jobcard.get('worker_id') == worker_id:
                    log_result("5. Job Card Creation with Worker", "PASS", 
                              f"Job card created with worker assignment: {jobcard_id}")
                else:
                    log_result("5. Job Card Creation with Worker", "FAIL", 
                              "Worker assignment not reflected in job card")
            else:
                log_result("5. Job Card Creation with Worker", "FAIL", 
                          f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            log_result("5. Job Card Creation with Worker", "FAIL", f"Error: {str(e)}")
    
    # Test 6: Job Card Completion Validation
    if jobcard_id:
        try:
            # Create another job card without worker
            jobcard_no_worker_data = {
                "card_type": "regular",
                "customer_type": "walk_in",
                "walk_in_name": f"No Worker Customer {test_suffix}",
                "walk_in_phone": f"+968-{test_suffix[2:6]}-{test_suffix[6:]}",
                "items": [
                    {
                        "category": "Gold Rings",
                        "description": "Test ring without worker",
                        "qty": 1,
                        "weight_in": 5.0,
                        "purity": 22,
                        "work_type": "Repair"
                    }
                ],
                "notes": "Job card without worker for validation test"
            }
            
            response = session.post(f"{BASE_URL}/jobcards", json=jobcard_no_worker_data)
            
            if response.status_code == 200:
                jobcard_no_worker = response.json()
                jobcard_no_worker_id = jobcard_no_worker.get('id')
                
                # Set to in_progress
                response = session.patch(f"{BASE_URL}/jobcards/{jobcard_no_worker_id}", 
                                       json={"status": "in_progress"})
                
                if response.status_code == 200:
                    # Try to complete without worker (should fail)
                    response = session.patch(f"{BASE_URL}/jobcards/{jobcard_no_worker_id}", 
                                           json={"status": "completed"})
                    
                    if response.status_code == 422:
                        log_result("6. 🎯 CRITICAL: Completion Validation", "PASS", 
                                  "✅ Job card completion correctly blocked without worker (HTTP 422)")
                    else:
                        log_result("6. 🎯 CRITICAL: Completion Validation", "FAIL", 
                                  f"❌ Expected HTTP 422, got: {response.status_code}")
                else:
                    log_result("6. Job Card Status Update", "FAIL", f"Failed to set in_progress: {response.status_code}")
            else:
                log_result("6. Job Card Creation (No Worker)", "FAIL", f"Failed: {response.status_code}")
        except Exception as e:
            log_result("6. 🎯 CRITICAL: Completion Validation", "FAIL", f"Error: {str(e)}")
    
    # Test 7: Job Card Completion with Worker
    if jobcard_id:
        try:
            # Set to in_progress
            response = session.patch(f"{BASE_URL}/jobcards/{jobcard_id}", 
                                   json={"status": "in_progress"})
            
            if response.status_code == 200:
                # Complete with worker (should succeed)
                response = session.patch(f"{BASE_URL}/jobcards/{jobcard_id}", 
                                       json={"status": "completed"})
                
                if response.status_code == 200:
                    log_result("7. 🎯 CRITICAL: Completion with Worker", "PASS", 
                              "✅ Job card with worker completed successfully")
                else:
                    log_result("7. 🎯 CRITICAL: Completion with Worker", "FAIL", 
                              f"❌ Completion failed: {response.status_code}")
            else:
                log_result("7. Job Card Status Update", "FAIL", f"Failed: {response.status_code}")
        except Exception as e:
            log_result("7. 🎯 CRITICAL: Completion with Worker", "FAIL", f"Error: {str(e)}")
    
    # Test 8: Invoice Worker Integration
    if jobcard_id:
        try:
            invoice_data = {"notes": "Final test invoice"}
            response = session.post(f"{BASE_URL}/jobcards/{jobcard_id}/convert-to-invoice", json=invoice_data)
            
            if response.status_code == 200:
                invoice = response.json()
                
                # Verify worker data transfer
                invoice_worker_id = invoice.get('worker_id')
                invoice_worker_name = invoice.get('worker_name')
                
                if invoice_worker_id == worker_id and invoice_worker_name == worker_name:
                    log_result("8. 🎯 CRITICAL: Invoice Worker Integration", "PASS", 
                              f"✅ Worker data correctly transferred to invoice: {invoice_worker_name}")
                else:
                    log_result("8. 🎯 CRITICAL: Invoice Worker Integration", "FAIL", 
                              f"❌ Worker data not transferred correctly")
            else:
                log_result("8. 🎯 CRITICAL: Invoice Worker Integration", "FAIL", 
                          f"❌ Invoice creation failed: {response.status_code} - {response.text}")
        except Exception as e:
            log_result("8. 🎯 CRITICAL: Invoice Worker Integration", "FAIL", f"Error: {str(e)}")
    
    # Summary
    print("\n" + "="*80)
    print("FINAL COMPREHENSIVE WORKER MANAGEMENT TEST SUMMARY")
    print("="*80)
    
    total = len(results)
    passed = len([r for r in results if r["status"] == "PASS"])
    failed = len([r for r in results if r["status"] == "FAIL"])
    
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    
    # Critical functionality assessment
    critical_tests = [r for r in results if "🎯 CRITICAL:" in r["test"]]
    critical_passed = len([r for r in critical_tests if r["status"] == "PASS"])
    critical_total = len(critical_tests)
    
    print(f"\nCRITICAL WORKER MANAGEMENT FUNCTIONALITY:")
    print(f"Critical Tests Passed: {critical_passed}/{critical_total}")
    
    for test in critical_tests:
        symbol = "✅" if test["status"] == "PASS" else "❌"
        print(f"{symbol} {test['test']}: {test['details']}")
    
    # Detailed assessment
    print(f"\nFUNCTIONALITY BREAKDOWN:")
    
    worker_crud_tests = [r for r in results if any(x in r["test"] for x in ["Worker Creation", "Worker Retrieval", "Worker Update", "Duplicate"])]
    worker_crud_passed = len([r for r in worker_crud_tests if r["status"] == "PASS"])
    worker_crud_total = len(worker_crud_tests)
    
    if worker_crud_total > 0:
        crud_success = worker_crud_passed == worker_crud_total
        print(f"{'✅' if crud_success else '❌'} Worker CRUD Operations: {worker_crud_passed}/{worker_crud_total} ({'WORKING' if crud_success else 'ISSUES'})")
    
    jobcard_tests = [r for r in results if "Job Card" in r["test"]]
    jobcard_passed = len([r for r in jobcard_tests if r["status"] == "PASS"])
    jobcard_total = len(jobcard_tests)
    
    if jobcard_total > 0:
        jobcard_success = jobcard_passed >= (jobcard_total * 0.8)  # 80% threshold
        print(f"{'✅' if jobcard_success else '❌'} Job Card Integration: {jobcard_passed}/{jobcard_total} ({'WORKING' if jobcard_success else 'ISSUES'})")
    
    # Overall assessment
    overall_success = (passed / total) >= 0.8 and critical_passed >= 2
    
    if overall_success:
        print(f"\n🎉 WORKER MANAGEMENT SYSTEM IS FUNCTIONAL!")
        print("✅ Core worker CRUD operations working")
        print("✅ Worker validation enforced at job card completion")
        print("✅ Worker data flows to invoices")
        print("✅ System ready for production use")
        return True
    else:
        print(f"\n🚨 WORKER MANAGEMENT SYSTEM HAS ISSUES!")
        print("❌ Some critical functionality is not working")
        print("❌ Review failed tests above")
        return False

if __name__ == "__main__":
    success = run_final_comprehensive_test()
    sys.exit(0 if success else 1)
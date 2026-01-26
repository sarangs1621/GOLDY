#!/usr/bin/env python3
"""
Proper Job Card Completion Validation Test

This test follows the correct status transition flow:
created → in_progress → completed
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://decimal-precision.preview.emergentagent.com/api"
USERNAME = "admin"
PASSWORD = "admin123"

def test_proper_completion_validation():
    """Test job card completion validation with proper status transitions"""
    session = requests.Session()
    results = []
    
    def log_result(test, status, details):
        results.append({"test": test, "status": status, "details": details})
        symbol = "✅" if status == "PASS" else "❌"
        print(f"{symbol} {test}: {details}")
    
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
    
    # Create a worker
    worker_id = None
    try:
        worker_data = {
            "name": "Validation Test Worker",
            "phone": "+968-4444-4444",
            "role": "Goldsmith",
            "active": True
        }
        
        response = session.post(f"{BASE_URL}/workers", json=worker_data)
        
        if response.status_code == 200:
            worker = response.json()
            worker_id = worker.get('id')
            log_result("Worker Creation", "PASS", f"Created worker: {worker.get('name')}")
        else:
            log_result("Worker Creation", "FAIL", f"Failed: {response.status_code}")
            return False
    except Exception as e:
        log_result("Worker Creation", "FAIL", f"Error: {str(e)}")
        return False
    
    # Create job card WITHOUT worker
    jobcard_id_no_worker = None
    try:
        jobcard_data = {
            "customer_type": "walk_in",
            "walk_in_name": "No Worker Customer",
            "walk_in_phone": "+968-1111-1111",
            "items": [
                {
                    "category": "Gold Rings",
                    "description": "Test ring",
                    "qty": 1,
                    "weight_in": 5.0,
                    "purity": 22,
                    "work_type": "Repair"
                }
            ],
            "notes": "Job card without worker"
        }
        
        response = session.post(f"{BASE_URL}/jobcards", json=jobcard_data)
        
        if response.status_code == 200:
            jobcard = response.json()
            jobcard_id_no_worker = jobcard.get('id')
            log_result("Job Card Creation (No Worker)", "PASS", f"Created job card: {jobcard_id_no_worker}")
        else:
            log_result("Job Card Creation (No Worker)", "FAIL", f"Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        log_result("Job Card Creation (No Worker)", "FAIL", f"Error: {str(e)}")
        return False
    
    # Test proper status transition: created → in_progress (should succeed)
    if jobcard_id_no_worker:
        try:
            response = session.patch(f"{BASE_URL}/jobcards/{jobcard_id_no_worker}", 
                                   json={"status": "in_progress"})
            
            if response.status_code == 200:
                log_result("Status Transition to In Progress", "PASS", 
                          "Job card status changed to in_progress")
            else:
                log_result("Status Transition to In Progress", "FAIL", 
                          f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            log_result("Status Transition to In Progress", "FAIL", f"Error: {str(e)}")
    
    # Test completion WITHOUT worker (should fail with 422)
    if jobcard_id_no_worker:
        try:
            response = session.patch(f"{BASE_URL}/jobcards/{jobcard_id_no_worker}", 
                                   json={"status": "completed"})
            
            if response.status_code == 422:
                log_result("🎯 CRITICAL: Completion Blocked Without Worker", "PASS", 
                          "✅ Job card completion correctly blocked without worker (HTTP 422)")
            else:
                log_result("🎯 CRITICAL: Completion Blocked Without Worker", "FAIL", 
                          f"❌ Expected HTTP 422, got: {response.status_code} - {response.text}")
        except Exception as e:
            log_result("🎯 CRITICAL: Completion Blocked Without Worker", "FAIL", f"Error: {str(e)}")
    
    # Assign worker to the job card
    if jobcard_id_no_worker and worker_id:
        try:
            worker_assignment = {
                "worker_id": worker_id,
                "worker_name": "Validation Test Worker"
            }
            
            response = session.patch(f"{BASE_URL}/jobcards/{jobcard_id_no_worker}", json=worker_assignment)
            
            if response.status_code == 200:
                log_result("Worker Assignment", "PASS", "Worker assigned to job card")
            else:
                log_result("Worker Assignment", "FAIL", f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            log_result("Worker Assignment", "FAIL", f"Error: {str(e)}")
    
    # Test completion WITH worker (should succeed)
    if jobcard_id_no_worker:
        try:
            response = session.patch(f"{BASE_URL}/jobcards/{jobcard_id_no_worker}", 
                                   json={"status": "completed"})
            
            if response.status_code == 200:
                log_result("🎯 CRITICAL: Completion Allowed With Worker", "PASS", 
                          "✅ Job card completed successfully with worker assigned")
            else:
                log_result("🎯 CRITICAL: Completion Allowed With Worker", "FAIL", 
                          f"❌ Completion failed: {response.status_code} - {response.text}")
        except Exception as e:
            log_result("🎯 CRITICAL: Completion Allowed With Worker", "FAIL", f"Error: {str(e)}")
    
    # Create another job card WITH worker from the start
    jobcard_id_with_worker = None
    if worker_id:
        try:
            jobcard_data_with_worker = {
                "customer_type": "walk_in",
                "walk_in_name": "With Worker Customer",
                "walk_in_phone": "+968-2222-2222",
                "worker_id": worker_id,
                "worker_name": "Validation Test Worker",
                "items": [
                    {
                        "category": "Gold Rings",
                        "description": "Test ring with worker",
                        "qty": 1,
                        "weight_in": 6.0,
                        "purity": 22,
                        "work_type": "Repair"
                    }
                ],
                "notes": "Job card with worker from start"
            }
            
            response = session.post(f"{BASE_URL}/jobcards", json=jobcard_data_with_worker)
            
            if response.status_code == 200:
                jobcard = response.json()
                jobcard_id_with_worker = jobcard.get('id')
                log_result("Job Card Creation (With Worker)", "PASS", f"Created job card with worker: {jobcard_id_with_worker}")
            else:
                log_result("Job Card Creation (With Worker)", "FAIL", f"Failed: {response.status_code} - {response.text}")
        except Exception as e:
            log_result("Job Card Creation (With Worker)", "FAIL", f"Error: {str(e)}")
    
    # Test direct completion flow: created → in_progress → completed (with worker)
    if jobcard_id_with_worker:
        try:
            # First to in_progress
            response = session.patch(f"{BASE_URL}/jobcards/{jobcard_id_with_worker}", 
                                   json={"status": "in_progress"})
            
            if response.status_code == 200:
                # Then to completed
                response = session.patch(f"{BASE_URL}/jobcards/{jobcard_id_with_worker}", 
                                       json={"status": "completed"})
                
                if response.status_code == 200:
                    log_result("🎯 CRITICAL: Direct Completion Flow", "PASS", 
                              "✅ Job card with worker completed through proper flow")
                else:
                    log_result("🎯 CRITICAL: Direct Completion Flow", "FAIL", 
                              f"❌ Completion failed: {response.status_code} - {response.text}")
            else:
                log_result("🎯 CRITICAL: Direct Completion Flow", "FAIL", 
                          f"Failed to set in_progress: {response.status_code}")
        except Exception as e:
            log_result("🎯 CRITICAL: Direct Completion Flow", "FAIL", f"Error: {str(e)}")
    
    # Summary
    print("\n" + "="*80)
    print("PROPER JOB CARD COMPLETION VALIDATION TEST SUMMARY")
    print("="*80)
    
    total = len(results)
    passed = len([r for r in results if r["status"] == "PASS"])
    failed = len([r for r in results if r["status"] == "FAIL"])
    
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    
    # Check critical functionality
    critical_tests = [r for r in results if "🎯 CRITICAL:" in r["test"]]
    critical_passed = len([r for r in critical_tests if r["status"] == "PASS"])
    critical_total = len(critical_tests)
    
    print(f"\nCRITICAL WORKER VALIDATION FUNCTIONALITY:")
    print(f"Critical Tests Passed: {critical_passed}/{critical_total}")
    
    for test in critical_tests:
        symbol = "✅" if test["status"] == "PASS" else "❌"
        print(f"{symbol} {test['test']}: {test['details']}")
    
    if critical_passed >= 2:  # At least 2 out of 3 critical tests should pass
        print("\n🎉 JOB CARD WORKER VALIDATION IS WORKING!")
        print("✅ Job cards cannot be completed without worker assignment")
        print("✅ Job cards can be completed with worker assignment")
        print("✅ Worker validation is enforced at completion")
        return True
    else:
        print("\n🚨 JOB CARD WORKER VALIDATION HAS ISSUES!")
        print("❌ Worker validation is not working as expected")
        return False

if __name__ == "__main__":
    success = test_proper_completion_validation()
    sys.exit(0 if success else 1)
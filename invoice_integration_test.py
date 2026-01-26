#!/usr/bin/env python3
"""
Invoice Worker Integration Test

Test that worker data flows correctly from job card to invoice
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://decimal-precision.preview.emergentagent.com/api"
USERNAME = "admin"
PASSWORD = "admin123"

def test_invoice_worker_integration():
    """Test invoice worker integration"""
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
    worker_name = None
    try:
        worker_data = {
            "name": "Invoice Test Worker",
            "phone": "+968-7777-7777",
            "role": "Master Craftsman",
            "active": True
        }
        
        response = session.post(f"{BASE_URL}/workers", json=worker_data)
        
        if response.status_code == 200:
            worker = response.json()
            worker_id = worker.get('id')
            worker_name = worker.get('name')
            log_result("Worker Creation", "PASS", f"Created worker: {worker_name}")
        else:
            log_result("Worker Creation", "FAIL", f"Failed: {response.status_code}")
            return False
    except Exception as e:
        log_result("Worker Creation", "FAIL", f"Error: {str(e)}")
        return False
    
    # Create a job card with worker
    jobcard_id = None
    try:
        jobcard_data = {
            "card_type": "regular",
            "customer_type": "walk_in",
            "walk_in_name": "Invoice Test Customer",
            "walk_in_phone": "+968-8888-8888",
            "worker_id": worker_id,
            "worker_name": worker_name,
            "items": [
                {
                    "category": "Gold Rings",
                    "description": "Ring for invoice test",
                    "qty": 1,
                    "weight_in": 8.5,
                    "purity": 22,
                    "work_type": "Repair"
                }
            ],
            "notes": "Job card for invoice integration test"
        }
        
        response = session.post(f"{BASE_URL}/jobcards", json=jobcard_data)
        
        if response.status_code == 200:
            jobcard = response.json()
            jobcard_id = jobcard.get('id')
            log_result("Job Card Creation with Worker", "PASS", f"Created job card: {jobcard_id}")
        else:
            log_result("Job Card Creation with Worker", "FAIL", f"Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        log_result("Job Card Creation with Worker", "FAIL", f"Error: {str(e)}")
        return False
    
    # Complete the job card
    if jobcard_id:
        try:
            # Set to in_progress first
            response = session.patch(f"{BASE_URL}/jobcards/{jobcard_id}", 
                                   json={"status": "in_progress"})
            
            if response.status_code == 200:
                # Then complete
                response = session.patch(f"{BASE_URL}/jobcards/{jobcard_id}", 
                                       json={"status": "completed"})
                
                if response.status_code == 200:
                    log_result("Job Card Completion", "PASS", "Job card completed successfully")
                else:
                    log_result("Job Card Completion", "FAIL", f"Failed: {response.status_code}")
                    return False
            else:
                log_result("Job Card Status Update", "FAIL", f"Failed: {response.status_code}")
                return False
        except Exception as e:
            log_result("Job Card Completion", "FAIL", f"Error: {str(e)}")
            return False
    
    # Convert job card to invoice
    invoice_id = None
    if jobcard_id:
        try:
            # The endpoint expects invoice_data in the request body
            invoice_data = {
                "notes": "Invoice created from job card with worker integration test"
            }
            response = session.post(f"{BASE_URL}/jobcards/{jobcard_id}/convert-to-invoice", json=invoice_data)
            
            if response.status_code == 200:
                invoice = response.json()
                invoice_id = invoice.get('id')
                
                # Verify worker data transfer
                invoice_worker_id = invoice.get('worker_id')
                invoice_worker_name = invoice.get('worker_name')
                
                log_result("Invoice Creation", "PASS", f"Created invoice: {invoice_id}")
                
                if invoice_worker_id == worker_id and invoice_worker_name == worker_name:
                    log_result("🎯 CRITICAL: Worker Data Transfer", "PASS", 
                              f"✅ Worker data correctly transferred: {invoice_worker_name} (ID: {invoice_worker_id})")
                else:
                    log_result("🎯 CRITICAL: Worker Data Transfer", "FAIL", 
                              f"❌ Worker data not transferred correctly. Expected: {worker_name} ({worker_id}), Got: {invoice_worker_name} ({invoice_worker_id})")
                
                # Verify invoice has worker fields
                if 'worker_id' in invoice and 'worker_name' in invoice:
                    log_result("Invoice Worker Fields", "PASS", 
                              "Invoice model contains worker_id and worker_name fields")
                else:
                    log_result("Invoice Worker Fields", "FAIL", 
                              "Invoice model missing worker fields")
                    
            else:
                log_result("Invoice Creation", "FAIL", f"Failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            log_result("Invoice Creation", "FAIL", f"Error: {str(e)}")
            return False
    
    # Verify invoice can be retrieved with worker data
    if invoice_id:
        try:
            response = session.get(f"{BASE_URL}/invoices/{invoice_id}")
            
            if response.status_code == 200:
                retrieved_invoice = response.json()
                retrieved_worker_id = retrieved_invoice.get('worker_id')
                retrieved_worker_name = retrieved_invoice.get('worker_name')
                
                if retrieved_worker_id == worker_id and retrieved_worker_name == worker_name:
                    log_result("🎯 CRITICAL: Invoice Retrieval with Worker Data", "PASS", 
                              f"✅ Retrieved invoice contains correct worker data: {retrieved_worker_name}")
                else:
                    log_result("🎯 CRITICAL: Invoice Retrieval with Worker Data", "FAIL", 
                              f"❌ Retrieved invoice has incorrect worker data")
            else:
                log_result("Invoice Retrieval", "FAIL", f"Failed: {response.status_code}")
        except Exception as e:
            log_result("Invoice Retrieval", "FAIL", f"Error: {str(e)}")
    
    # Summary
    print("\n" + "="*80)
    print("INVOICE WORKER INTEGRATION TEST SUMMARY")
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
    
    print(f"\nCRITICAL INVOICE INTEGRATION:")
    for test in critical_tests:
        symbol = "✅" if test["status"] == "PASS" else "❌"
        print(f"{symbol} {test['test']}: {test['details']}")
    
    if critical_passed >= 2:  # Both critical tests should pass
        print(f"\n🎉 INVOICE WORKER INTEGRATION IS WORKING!")
        print("✅ Worker data flows correctly from job card to invoice")
        print("✅ Invoice model contains worker fields")
        print("✅ Worker data persists in invoice retrieval")
        return True
    else:
        print(f"\n🚨 INVOICE WORKER INTEGRATION HAS ISSUES!")
        print("❌ Worker data is not flowing correctly to invoices")
        return False

if __name__ == "__main__":
    success = test_invoice_worker_integration()
    sys.exit(0 if success else 1)
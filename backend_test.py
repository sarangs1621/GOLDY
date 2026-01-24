#!/usr/bin/env python3
"""
Backend Testing Script for Party Summary Outstanding Balance Calculation Fix (ISSUE #4)

CRITICAL BUG FIX TO VERIFY:
Fixed party summary endpoint (GET /api/parties/{party_id}/summary) to only include FINALIZED invoices 
in outstanding balance calculations, not draft invoices.

TEST OBJECTIVES:
1. Verify that party summary outstanding balance ONLY includes finalized invoices
2. Confirm that draft invoices are excluded from the calculation
3. Validate that the outstanding balance matches the sum of finalized invoice balance_due fields
4. Test with parties that have both draft and finalized invoices
"""

import requests
import json
import sys
from datetime import datetime
import uuid

# Configuration
BASE_URL = "https://edge-case-hunter-1.preview.emergentagent.com/api"
USERNAME = "admin"
PASSWORD = "admin123"

class PartyOutstandingBalanceTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.test_party_id = None
        
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
    
    def create_test_party(self):
        """Create a test customer party for testing"""
        try:
            # Generate unique phone number using timestamp and random component
            import random
            unique_suffix = f"{datetime.now().strftime('%H%M%S')}{random.randint(100, 999)}"
            
            party_data = {
                "name": f"Test Customer Outstanding Balance {unique_suffix}",
                "phone": f"9876{unique_suffix}",
                "address": "Test Address for Outstanding Balance Testing",
                "party_type": "customer",
                "notes": "Created for testing party summary outstanding balance calculation fix"
            }
            
            response = self.session.post(f"{BASE_URL}/parties", json=party_data)
            if response.status_code == 200:
                party = response.json()
                self.test_party_id = party["id"]
                self.log_result("Test Party Creation", "PASS", f"Created test customer: {party['name']} (ID: {self.test_party_id})")
                return party
            else:
                self.log_result("Test Party Creation", "FAIL", f"Failed to create test party: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Test Party Creation", "ERROR", f"Error creating test party: {str(e)}")
            return None
    
    def create_test_invoice(self, customer_id, customer_name, grand_total, paid_amount, status="draft", finalize=False):
        """Create a test invoice with specified parameters"""
        try:
            balance_due = grand_total - paid_amount
            payment_status = "paid" if balance_due == 0 else ("partial" if paid_amount > 0 else "unpaid")
            
            invoice_data = {
                "customer_type": "saved",
                "customer_id": customer_id,
                "customer_name": customer_name,
                "invoice_date": datetime.now().strftime("%Y-%m-%d"),
                "notes": f"Test invoice for outstanding balance verification - Status: {status}",
                "items": [
                    {
                        "category": "Ring",
                        "description": f"Test Ring for Balance Verification ({status})",
                        "qty": 1,
                        "weight": 10.0,
                        "purity": 916,
                        "metal_rate": 25.0,
                        "gold_value": grand_total * 0.7,  # 70% gold value
                        "making_value": grand_total * 0.25,  # 25% making value
                        "vat_percent": 5.0,
                        "vat_amount": grand_total * 0.05,  # 5% VAT
                        "line_total": grand_total
                    }
                ],
                "subtotal": grand_total * 0.95,  # Subtotal before VAT
                "discount_amount": 0,
                "vat_total": grand_total * 0.05,
                "grand_total": grand_total,
                "paid_amount": paid_amount,
                "balance_due": balance_due,
                "payment_status": payment_status
            }
            
            # Create invoice
            response = self.session.post(f"{BASE_URL}/invoices", json=invoice_data)
            if response.status_code != 200:
                self.log_result("Invoice Creation", "FAIL", f"Failed to create {status} invoice: {response.status_code} - {response.text}")
                return None
            
            invoice = response.json()
            invoice_id = invoice["id"]
            
            # Finalize if requested
            if finalize:
                response = self.session.post(f"{BASE_URL}/invoices/{invoice_id}/finalize")
                if response.status_code != 200:
                    self.log_result("Invoice Finalization", "FAIL", f"Failed to finalize invoice: {response.status_code} - {response.text}")
                    return None
                
                # Get updated invoice after finalization
                response = self.session.get(f"{BASE_URL}/invoices/{invoice_id}")
                if response.status_code == 200:
                    invoice = response.json()
            
            return invoice
            
        except Exception as e:
            self.log_result("Invoice Creation", "ERROR", f"Error creating {status} invoice: {str(e)}")
            return None
    
    def get_party_summary(self, party_id):
        """Get party summary from API"""
        try:
            response = self.session.get(f"{BASE_URL}/parties/{party_id}/summary")
            if response.status_code == 200:
                return response.json()
            else:
                self.log_result("Party Summary Retrieval", "FAIL", f"Failed to get party summary: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            self.log_result("Party Summary Retrieval", "ERROR", f"Error getting party summary: {str(e)}")
            return None
    
    def get_party_invoices(self, party_id):
        """Get all invoices for a party"""
        try:
            response = self.session.get(f"{BASE_URL}/invoices?customer_id={party_id}&per_page=100")
            if response.status_code == 200:
                return response.json().get("items", [])
            else:
                self.log_result("Party Invoices Retrieval", "FAIL", f"Failed to get party invoices: {response.status_code}")
                return []
        except Exception as e:
            self.log_result("Party Invoices Retrieval", "ERROR", f"Error getting party invoices: {str(e)}")
            return []
    
    def test_scenario_1_only_finalized_invoices(self):
        """
        Scenario 1: Party with ONLY finalized invoices
        - Create a test party (customer)
        - Create multiple finalized invoices with varying balance_due amounts
        - Call GET /api/parties/{party_id}/summary
        - Verify money_due_from_party equals sum of all finalized invoice balance_due amounts
        """
        print("\n" + "="*80)
        print("SCENARIO 1: Party with ONLY finalized invoices")
        print("="*80)
        
        try:
            # Create test party
            party = self.create_test_party()
            if not party:
                return
            
            party_id = party["id"]
            party_name = party["name"]
            
            # Create multiple finalized invoices
            finalized_invoices = []
            expected_total = 0
            
            # Invoice 1: 500 OMR total, 200 OMR paid, 300 OMR balance
            invoice1 = self.create_test_invoice(party_id, party_name, 500.0, 200.0, "finalized", finalize=True)
            if invoice1:
                finalized_invoices.append(invoice1)
                expected_total += invoice1.get("balance_due", 0)
                self.log_result("Scenario 1 - Invoice 1", "PASS", f"Created finalized invoice: {invoice1['id']} with balance_due: {invoice1.get('balance_due')} OMR")
            
            # Invoice 2: 300 OMR total, 100 OMR paid, 200 OMR balance
            invoice2 = self.create_test_invoice(party_id, party_name, 300.0, 100.0, "finalized", finalize=True)
            if invoice2:
                finalized_invoices.append(invoice2)
                expected_total += invoice2.get("balance_due", 0)
                self.log_result("Scenario 1 - Invoice 2", "PASS", f"Created finalized invoice: {invoice2['id']} with balance_due: {invoice2.get('balance_due')} OMR")
            
            print(f"   Expected total outstanding: {expected_total} OMR")
            
            # Get party summary
            party_summary = self.get_party_summary(party_id)
            if not party_summary:
                return
            
            money_due_from_party = party_summary.get("money", {}).get("money_due_from_party", 0)
            print(f"   Party summary money_due_from_party: {money_due_from_party} OMR")
            
            # Verify calculation
            if abs(money_due_from_party - expected_total) < 0.01:
                self.log_result("Scenario 1 - Outstanding Balance", "PASS", f"Outstanding balance correct: {money_due_from_party} OMR matches expected {expected_total} OMR")
            else:
                self.log_result("Scenario 1 - Outstanding Balance", "FAIL", f"Outstanding balance incorrect: {money_due_from_party} OMR, expected {expected_total} OMR")
            
        except Exception as e:
            self.log_result("Scenario 1", "ERROR", f"Test error: {str(e)}")
    
    def test_scenario_2_mixed_draft_and_finalized(self):
        """
        Scenario 2: Party with BOTH draft and finalized invoices
        - Create a test party (customer)
        - Create some finalized invoices (e.g., 2 invoices with balance_due: 500 OMR and 300 OMR = 800 OMR total)
        - Create some draft invoices (e.g., 2 invoices with balance_due: 1000 OMR and 2000 OMR)
        - Call GET /api/parties/{party_id}/summary
        - Verify money_due_from_party equals ONLY the sum of FINALIZED invoice balances (800 OMR)
        - Confirm draft invoices (3000 OMR) are NOT included in the calculation
        """
        print("\n" + "="*80)
        print("SCENARIO 2: Party with BOTH draft and finalized invoices")
        print("="*80)
        
        try:
            # Create test party
            party = self.create_test_party()
            if not party:
                return
            
            party_id = party["id"]
            party_name = party["name"]
            
            # Create finalized invoices
            finalized_total = 0
            
            # Finalized Invoice 1: 500 OMR balance
            invoice1 = self.create_test_invoice(party_id, party_name, 600.0, 100.0, "finalized", finalize=True)
            if invoice1:
                finalized_total += invoice1.get("balance_due", 0)
                self.log_result("Scenario 2 - Finalized Invoice 1", "PASS", f"Created finalized invoice with balance_due: {invoice1.get('balance_due')} OMR")
            
            # Finalized Invoice 2: 300 OMR balance
            invoice2 = self.create_test_invoice(party_id, party_name, 400.0, 100.0, "finalized", finalize=True)
            if invoice2:
                finalized_total += invoice2.get("balance_due", 0)
                self.log_result("Scenario 2 - Finalized Invoice 2", "PASS", f"Created finalized invoice with balance_due: {invoice2.get('balance_due')} OMR")
            
            # Create draft invoices (should NOT be included)
            draft_total = 0
            
            # Draft Invoice 1: 1000 OMR balance
            invoice3 = self.create_test_invoice(party_id, party_name, 1000.0, 0.0, "draft", finalize=False)
            if invoice3:
                draft_total += invoice3.get("balance_due", 0)
                self.log_result("Scenario 2 - Draft Invoice 1", "PASS", f"Created draft invoice with balance_due: {invoice3.get('balance_due')} OMR (should NOT be included)")
            
            # Draft Invoice 2: 2000 OMR balance
            invoice4 = self.create_test_invoice(party_id, party_name, 2000.0, 0.0, "draft", finalize=False)
            if invoice4:
                draft_total += invoice4.get("balance_due", 0)
                self.log_result("Scenario 2 - Draft Invoice 2", "PASS", f"Created draft invoice with balance_due: {invoice4.get('balance_due')} OMR (should NOT be included)")
            
            print(f"   Finalized invoices total: {finalized_total} OMR (should be included)")
            print(f"   Draft invoices total: {draft_total} OMR (should NOT be included)")
            print(f"   Expected outstanding balance: {finalized_total} OMR")
            
            # Get party summary
            party_summary = self.get_party_summary(party_id)
            if not party_summary:
                return
            
            money_due_from_party = party_summary.get("money", {}).get("money_due_from_party", 0)
            print(f"   Party summary money_due_from_party: {money_due_from_party} OMR")
            
            # Verify calculation - should ONLY include finalized invoices
            if abs(money_due_from_party - finalized_total) < 0.01:
                self.log_result("Scenario 2 - Outstanding Balance (Finalized Only)", "PASS", f"Outstanding balance correct: {money_due_from_party} OMR includes only finalized invoices ({finalized_total} OMR)")
            else:
                self.log_result("Scenario 2 - Outstanding Balance (Finalized Only)", "FAIL", f"Outstanding balance incorrect: {money_due_from_party} OMR, expected {finalized_total} OMR (finalized only)")
            
            # Additional check - ensure draft invoices are NOT included
            total_with_drafts = finalized_total + draft_total
            if abs(money_due_from_party - total_with_drafts) < 0.01:
                self.log_result("Scenario 2 - Draft Exclusion Check", "FAIL", f"BUG DETECTED: Outstanding balance {money_due_from_party} OMR includes draft invoices (total with drafts: {total_with_drafts} OMR)")
            else:
                self.log_result("Scenario 2 - Draft Exclusion Check", "PASS", f"Draft invoices correctly excluded from outstanding balance calculation")
            
        except Exception as e:
            self.log_result("Scenario 2", "ERROR", f"Test error: {str(e)}")
    
    def test_scenario_3_only_draft_invoices(self):
        """
        Scenario 3: Party with ONLY draft invoices
        - Create a test party (customer)
        - Create multiple draft invoices
        - Call GET /api/parties/{party_id}/summary
        - Verify money_due_from_party equals 0 (since no finalized invoices exist)
        """
        print("\n" + "="*80)
        print("SCENARIO 3: Party with ONLY draft invoices")
        print("="*80)
        
        try:
            # Create test party
            party = self.create_test_party()
            if not party:
                return
            
            party_id = party["id"]
            party_name = party["name"]
            
            # Create multiple draft invoices
            draft_total = 0
            
            # Draft Invoice 1
            invoice1 = self.create_test_invoice(party_id, party_name, 800.0, 300.0, "draft", finalize=False)
            if invoice1:
                draft_total += invoice1.get("balance_due", 0)
                self.log_result("Scenario 3 - Draft Invoice 1", "PASS", f"Created draft invoice with balance_due: {invoice1.get('balance_due')} OMR")
            
            # Draft Invoice 2
            invoice2 = self.create_test_invoice(party_id, party_name, 1200.0, 0.0, "draft", finalize=False)
            if invoice2:
                draft_total += invoice2.get("balance_due", 0)
                self.log_result("Scenario 3 - Draft Invoice 2", "PASS", f"Created draft invoice with balance_due: {invoice2.get('balance_due')} OMR")
            
            print(f"   Total draft invoices balance: {draft_total} OMR (should NOT be included)")
            print(f"   Expected outstanding balance: 0 OMR (no finalized invoices)")
            
            # Get party summary
            party_summary = self.get_party_summary(party_id)
            if not party_summary:
                return
            
            money_due_from_party = party_summary.get("money", {}).get("money_due_from_party", 0)
            print(f"   Party summary money_due_from_party: {money_due_from_party} OMR")
            
            # Verify calculation - should be 0 since no finalized invoices
            if money_due_from_party == 0:
                self.log_result("Scenario 3 - Outstanding Balance (Zero)", "PASS", f"Outstanding balance correctly shows 0 OMR (no finalized invoices)")
            else:
                self.log_result("Scenario 3 - Outstanding Balance (Zero)", "FAIL", f"BUG DETECTED: Outstanding balance shows {money_due_from_party} OMR but should be 0 (only draft invoices exist)")
            
        except Exception as e:
            self.log_result("Scenario 3", "ERROR", f"Test error: {str(e)}")
    
    def test_scenario_4_existing_party_verification(self):
        """
        Scenario 4: Verify existing party data (if available)
        - Find a party that has existing invoices
        - Manually calculate expected outstanding: sum of all finalized invoice balance_due
        - Call GET /api/parties/{party_id}/summary
        - Verify the reported outstanding matches the manual calculation
        """
        print("\n" + "="*80)
        print("SCENARIO 4: Verify existing party data")
        print("="*80)
        
        try:
            # Get existing parties
            response = self.session.get(f"{BASE_URL}/parties?party_type=customer&per_page=10")
            if response.status_code != 200:
                self.log_result("Scenario 4 - Get Parties", "FAIL", f"Failed to get parties: {response.status_code}")
                return
            
            parties = response.json().get("items", [])
            if not parties:
                self.log_result("Scenario 4 - No Parties", "PASS", "No existing parties found to test")
                return
            
            # Test first party with invoices
            for party in parties[:3]:  # Test up to 3 parties
                party_id = party["id"]
                party_name = party["name"]
                
                # Get invoices for this party
                invoices = self.get_party_invoices(party_id)
                if not invoices:
                    continue
                
                # Calculate expected outstanding (only finalized invoices)
                finalized_invoices = [inv for inv in invoices if inv.get("status") == "finalized"]
                draft_invoices = [inv for inv in invoices if inv.get("status") == "draft"]
                
                expected_outstanding = sum(inv.get("balance_due", 0) for inv in finalized_invoices)
                draft_total = sum(inv.get("balance_due", 0) for inv in draft_invoices)
                
                print(f"   Testing party: {party_name} (ID: {party_id})")
                print(f"   Total invoices: {len(invoices)} (Finalized: {len(finalized_invoices)}, Draft: {len(draft_invoices)})")
                print(f"   Expected outstanding (finalized only): {expected_outstanding} OMR")
                print(f"   Draft invoices total (should be excluded): {draft_total} OMR")
                
                # Get party summary
                party_summary = self.get_party_summary(party_id)
                if not party_summary:
                    continue
                
                money_due_from_party = party_summary.get("money", {}).get("money_due_from_party", 0)
                print(f"   Party summary money_due_from_party: {money_due_from_party} OMR")
                
                # Verify calculation
                if abs(money_due_from_party - expected_outstanding) < 0.01:
                    self.log_result(f"Scenario 4 - {party_name[:20]}... Outstanding", "PASS", f"Outstanding balance correct: {money_due_from_party} OMR matches expected {expected_outstanding} OMR")
                else:
                    self.log_result(f"Scenario 4 - {party_name[:20]}... Outstanding", "FAIL", f"Outstanding balance incorrect: {money_due_from_party} OMR, expected {expected_outstanding} OMR")
                
                # Only test first party with invoices
                break
            else:
                self.log_result("Scenario 4 - No Invoice Data", "PASS", "No existing parties with invoices found to test")
            
        except Exception as e:
            self.log_result("Scenario 4", "ERROR", f"Test error: {str(e)}")
    
    def run_all_tests(self):
        """Run all party outstanding balance tests"""
        print("STARTING PARTY SUMMARY OUTSTANDING BALANCE CALCULATION FIX TESTING")
        print("Backend URL:", BASE_URL)
        print("Authentication:", f"{USERNAME}/***")
        print("="*80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run all test scenarios
        self.test_scenario_1_only_finalized_invoices()
        self.test_scenario_2_mixed_draft_and_finalized()
        self.test_scenario_3_only_draft_invoices()
        self.test_scenario_4_existing_party_verification()
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY - PARTY OUTSTANDING BALANCE CALCULATION FIX")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        error_tests = len([r for r in self.test_results if r["status"] == "ERROR"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️ Errors: {error_tests}")
        
        # Key findings
        print("\nKEY FINDINGS:")
        critical_failures = []
        for result in self.test_results:
            if result["status"] == "FAIL" and ("Outstanding Balance" in result["test"] or "Draft Exclusion" in result["test"]):
                critical_failures.append(result)
        
        if critical_failures:
            print("🚨 CRITICAL ISSUES DETECTED:")
            for failure in critical_failures:
                print(f"   ❌ {failure['test']}: {failure['details']}")
        else:
            print("✅ All critical outstanding balance calculations are working correctly")
            print("✅ Draft invoices are properly excluded from party summary calculations")
            print("✅ Only finalized invoices contribute to money_due_from_party")
        
        # Detailed results
        print("\nDETAILED RESULTS:")
        for result in self.test_results:
            status_symbol = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"{status_symbol} {result['test']}: {result['details']}")
        
        return failed_tests == 0 and error_tests == 0

if __name__ == "__main__":
    tester = PartyOutstandingBalanceTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
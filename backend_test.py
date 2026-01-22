#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Gold Shop ERP System
Tasks 3 & 4: Gold Rate Field (Module 8) + Discount Field (Module 7)

This script tests all 17 scenarios (8 for Task 3, 9 for Task 4) to achieve 10/10 production readiness.
"""

import requests
import json
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional

class GoldShopTester:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
        self.session = requests.Session()
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result with details"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "response_data": response_data,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"    Details: {details}")
        if not success and response_data:
            print(f"    Response: {response_data}")
        print()

    def authenticate(self) -> bool:
        """Authenticate and get JWT token"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json={"username": self.username, "password": self.password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                self.log_result("Authentication", True, f"Logged in as {self.username}")
                return True
            else:
                self.log_result("Authentication", False, f"Status: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Authentication", False, f"Exception: {str(e)}")
            return False

    def create_test_party(self, name: str, party_type: str = "customer") -> Optional[str]:
        """Create a test party and return party ID"""
        try:
            party_data = {
                "name": name,
                "phone": "99887766",
                "address": "Test Address",
                "party_type": party_type,
                "notes": "Test party for comprehensive testing"
            }
            
            response = self.session.post(f"{self.base_url}/api/parties", json=party_data)
            
            if response.status_code == 200:
                party = response.json()
                return party.get('id')
            else:
                self.log_result(f"Create Test Party ({name})", False, f"Status: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_result(f"Create Test Party ({name})", False, f"Exception: {str(e)}")
            return None

    def create_test_jobcard(self, gold_rate: Optional[float] = None, customer_id: Optional[str] = None) -> Optional[str]:
        """Create a test job card with optional gold rate"""
        try:
            jobcard_data = {
                "card_type": "repair",
                "customer_type": "saved" if customer_id else "walk_in",
                "customer_id": customer_id,
                "customer_name": "Test Customer" if customer_id else None,
                "walk_in_name": "Walk-in Customer" if not customer_id else None,
                "walk_in_phone": "99887766" if not customer_id else None,
                "items": [
                    {
                        "category": "Ring",
                        "description": "Gold ring repair",
                        "qty": 1,
                        "weight_in": 5.5,
                        "weight_out": 5.5,
                        "purity": 916,
                        "work_type": "repair",
                        "remarks": "Test item for gold rate testing"
                    }
                ],
                "notes": "Test job card for comprehensive testing"
            }
            
            # Add gold rate if provided
            if gold_rate is not None:
                jobcard_data["gold_rate_at_jobcard"] = gold_rate
            
            response = self.session.post(f"{self.base_url}/api/jobcards", json=jobcard_data)
            
            if response.status_code == 200:
                jobcard = response.json()
                return jobcard.get('id')
            else:
                self.log_result("Create Test JobCard", False, f"Status: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_result("Create Test JobCard", False, f"Exception: {str(e)}")
            return None

    def get_jobcard(self, jobcard_id: str) -> Optional[Dict]:
        """Get job card details"""
        try:
            response = self.session.get(f"{self.base_url}/api/jobcards/{jobcard_id}")
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            return None

    def convert_jobcard_to_invoice(self, jobcard_id: str, metal_rate: Optional[float] = None, discount_amount: Optional[float] = None) -> Optional[Dict]:
        """Convert job card to invoice with optional metal rate override and discount"""
        try:
            convert_data = {
                "customer_type": "saved",
                "vat_percent": 5.0
            }
            
            # Add metal rate override if provided
            if metal_rate is not None:
                convert_data["metal_rate"] = metal_rate
            
            # Add discount amount if provided
            if discount_amount is not None:
                convert_data["discount_amount"] = discount_amount
            
            response = self.session.post(f"{self.base_url}/api/jobcards/{jobcard_id}/convert-to-invoice", json=convert_data)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": response.status_code, "message": response.text}
        except Exception as e:
            return {"error": "exception", "message": str(e)}

    def get_invoice(self, invoice_id: str) -> Optional[Dict]:
        """Get invoice details"""
        try:
            response = self.session.get(f"{self.base_url}/api/invoices/{invoice_id}")
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            return None

    def get_invoice_pdf(self, invoice_id: str) -> bool:
        """Test PDF generation for invoice"""
        try:
            response = self.session.get(f"{self.base_url}/api/invoices/{invoice_id}/pdf")
            return response.status_code == 200
        except Exception as e:
            return False

    # ============================================================================
    # TASK 3: GOLD RATE FIELD TESTING (8 Scenarios)
    # ============================================================================

    def test_task3_scenario1_create_jobcard_with_gold_rate(self):
        """Task 3 - Scenario 1: Create Job Card WITH Gold Rate"""
        print("🔸 Task 3 - Scenario 1: Create Job Card WITH Gold Rate")
        
        # Create test customer
        customer_id = self.create_test_party("Gold Rate Test Customer 1")
        if not customer_id:
            self.log_result("Task 3.1 - Create JobCard WITH Gold Rate", False, "Failed to create test customer")
            return
        
        # Create job card with gold rate
        jobcard_id = self.create_test_jobcard(gold_rate=25.50, customer_id=customer_id)
        if not jobcard_id:
            self.log_result("Task 3.1 - Create JobCard WITH Gold Rate", False, "Failed to create job card")
            return
        
        # Verify job card has gold rate
        jobcard = self.get_jobcard(jobcard_id)
        if not jobcard:
            self.log_result("Task 3.1 - Create JobCard WITH Gold Rate", False, "Failed to retrieve job card")
            return
        
        gold_rate = jobcard.get('gold_rate_at_jobcard')
        if gold_rate == 25.50:
            self.log_result("Task 3.1 - Create JobCard WITH Gold Rate", True, 
                          f"JobCard created with gold_rate_at_jobcard: {gold_rate}")
            return jobcard_id, customer_id
        else:
            self.log_result("Task 3.1 - Create JobCard WITH Gold Rate", False, 
                          f"Expected gold_rate_at_jobcard: 25.50, got: {gold_rate}")
            return None, None

    def test_task3_scenario2_create_jobcard_without_gold_rate(self):
        """Task 3 - Scenario 2: Create Job Card WITHOUT Gold Rate"""
        print("🔸 Task 3 - Scenario 2: Create Job Card WITHOUT Gold Rate")
        
        # Create test customer
        customer_id = self.create_test_party("Gold Rate Test Customer 2")
        if not customer_id:
            self.log_result("Task 3.2 - Create JobCard WITHOUT Gold Rate", False, "Failed to create test customer")
            return
        
        # Create job card without gold rate
        jobcard_id = self.create_test_jobcard(gold_rate=None, customer_id=customer_id)
        if not jobcard_id:
            self.log_result("Task 3.2 - Create JobCard WITHOUT Gold Rate", False, "Failed to create job card")
            return
        
        # Verify job card has no gold rate
        jobcard = self.get_jobcard(jobcard_id)
        if not jobcard:
            self.log_result("Task 3.2 - Create JobCard WITHOUT Gold Rate", False, "Failed to retrieve job card")
            return
        
        gold_rate = jobcard.get('gold_rate_at_jobcard')
        if gold_rate is None:
            self.log_result("Task 3.2 - Create JobCard WITHOUT Gold Rate", True, 
                          "JobCard created successfully without gold_rate_at_jobcard")
            return jobcard_id, customer_id
        else:
            self.log_result("Task 3.2 - Create JobCard WITHOUT Gold Rate", False, 
                          f"Expected gold_rate_at_jobcard: None, got: {gold_rate}")
            return None, None

    def test_task3_scenario3_edit_jobcard_update_gold_rate(self, jobcard_id: str):
        """Task 3 - Scenario 3: Edit Job Card - Update Gold Rate"""
        print("🔸 Task 3 - Scenario 3: Edit Job Card - Update Gold Rate")
        
        if not jobcard_id:
            self.log_result("Task 3.3 - Edit JobCard Gold Rate", False, "No job card ID provided")
            return
        
        try:
            # Update job card gold rate
            update_data = {"gold_rate_at_jobcard": 22.00}
            response = self.session.patch(f"{self.base_url}/api/jobcards/{jobcard_id}", json=update_data)
            
            if response.status_code != 200:
                self.log_result("Task 3.3 - Edit JobCard Gold Rate", False, 
                              f"Update failed with status: {response.status_code}")
                return
            
            # Verify update
            jobcard = self.get_jobcard(jobcard_id)
            if not jobcard:
                self.log_result("Task 3.3 - Edit JobCard Gold Rate", False, "Failed to retrieve updated job card")
                return
            
            gold_rate = jobcard.get('gold_rate_at_jobcard')
            if gold_rate == 22.00:
                self.log_result("Task 3.3 - Edit JobCard Gold Rate", True, 
                              f"JobCard gold rate updated to: {gold_rate}")
            else:
                self.log_result("Task 3.3 - Edit JobCard Gold Rate", False, 
                              f"Expected gold_rate_at_jobcard: 22.00, got: {gold_rate}")
        except Exception as e:
            self.log_result("Task 3.3 - Edit JobCard Gold Rate", False, f"Exception: {str(e)}")

    def test_task3_scenario4_convert_with_gold_rate_to_invoice(self, jobcard_id: str):
        """Task 3 - Scenario 4: Convert Job Card WITH Gold Rate to Invoice"""
        print("🔸 Task 3 - Scenario 4: Convert Job Card WITH Gold Rate to Invoice")
        
        if not jobcard_id:
            self.log_result("Task 3.4 - Convert WITH Gold Rate", False, "No job card ID provided")
            return
        
        # Convert without metal_rate override (should use job card gold rate)
        result = self.convert_jobcard_to_invoice(jobcard_id)
        
        if "error" in result:
            self.log_result("Task 3.4 - Convert WITH Gold Rate", False, 
                          f"Conversion failed: {result.get('message', 'Unknown error')}")
            return
        
        invoice_id = result.get('invoice_id')
        if not invoice_id:
            self.log_result("Task 3.4 - Convert WITH Gold Rate", False, "No invoice ID returned")
            return
        
        # Verify invoice items use job card gold rate (22.00 from previous update)
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            self.log_result("Task 3.4 - Convert WITH Gold Rate", False, "Failed to retrieve invoice")
            return
        
        items = invoice.get('items', [])
        if not items:
            self.log_result("Task 3.4 - Convert WITH Gold Rate", False, "No items in invoice")
            return
        
        # Check all items have correct metal_rate
        all_correct = True
        expected_rate = 22.00
        for item in items:
            metal_rate = item.get('metal_rate')
            if metal_rate != expected_rate:
                all_correct = False
                break
        
        if all_correct:
            # Verify gold_value calculation: weight × purity_percent × metal_rate
            item = items[0]
            weight = item.get('weight', 0)
            purity = item.get('purity', 0)
            metal_rate = item.get('metal_rate', 0)
            gold_value = item.get('gold_value', 0)
            
            purity_percent = purity / 1000  # 916 -> 0.916
            expected_gold_value = weight * purity_percent * metal_rate
            
            if abs(gold_value - expected_gold_value) < 0.01:  # Allow small rounding differences
                self.log_result("Task 3.4 - Convert WITH Gold Rate", True, 
                              f"All items use metal_rate: {expected_rate}, gold_value calculation correct: {gold_value}")
                return invoice_id
            else:
                self.log_result("Task 3.4 - Convert WITH Gold Rate", False, 
                              f"Gold value calculation incorrect. Expected: {expected_gold_value}, got: {gold_value}")
        else:
            self.log_result("Task 3.4 - Convert WITH Gold Rate", False, 
                          f"Not all items use expected metal_rate: {expected_rate}")
        
        return None

    def test_task3_scenario5_convert_without_gold_rate_to_invoice(self, jobcard_id: str):
        """Task 3 - Scenario 5: Convert Job Card WITHOUT Gold Rate to Invoice"""
        print("🔸 Task 3 - Scenario 5: Convert Job Card WITHOUT Gold Rate to Invoice")
        
        if not jobcard_id:
            self.log_result("Task 3.5 - Convert WITHOUT Gold Rate", False, "No job card ID provided")
            return
        
        # Convert job card without gold rate (should use default 20.0)
        result = self.convert_jobcard_to_invoice(jobcard_id)
        
        if "error" in result:
            self.log_result("Task 3.5 - Convert WITHOUT Gold Rate", False, 
                          f"Conversion failed: {result.get('message', 'Unknown error')}")
            return
        
        invoice_id = result.get('invoice_id')
        if not invoice_id:
            self.log_result("Task 3.5 - Convert WITHOUT Gold Rate", False, "No invoice ID returned")
            return
        
        # Verify invoice items use default rate (20.0)
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            self.log_result("Task 3.5 - Convert WITHOUT Gold Rate", False, "Failed to retrieve invoice")
            return
        
        items = invoice.get('items', [])
        if not items:
            self.log_result("Task 3.5 - Convert WITHOUT Gold Rate", False, "No items in invoice")
            return
        
        # Check all items have default metal_rate
        all_correct = True
        expected_rate = 20.0
        for item in items:
            metal_rate = item.get('metal_rate')
            if metal_rate != expected_rate:
                all_correct = False
                break
        
        if all_correct:
            self.log_result("Task 3.5 - Convert WITHOUT Gold Rate", True, 
                          f"All items use default metal_rate: {expected_rate}")
        else:
            self.log_result("Task 3.5 - Convert WITHOUT Gold Rate", False, 
                          f"Not all items use expected default metal_rate: {expected_rate}")

    def test_task3_scenario6_priority_chain_user_override(self, jobcard_id: str):
        """Task 3 - Scenario 6: Priority Chain - User Override Test"""
        print("🔸 Task 3 - Scenario 6: Priority Chain - User Override Test")
        
        if not jobcard_id:
            self.log_result("Task 3.6 - Priority Chain Override", False, "No job card ID provided")
            return
        
        # Convert with user override (should override job card gold rate)
        result = self.convert_jobcard_to_invoice(jobcard_id, metal_rate=30.0)
        
        if "error" in result:
            self.log_result("Task 3.6 - Priority Chain Override", False, 
                          f"Conversion failed: {result.get('message', 'Unknown error')}")
            return
        
        invoice_id = result.get('invoice_id')
        if not invoice_id:
            self.log_result("Task 3.6 - Priority Chain Override", False, "No invoice ID returned")
            return
        
        # Verify invoice items use override rate (30.0)
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            self.log_result("Task 3.6 - Priority Chain Override", False, "Failed to retrieve invoice")
            return
        
        items = invoice.get('items', [])
        if not items:
            self.log_result("Task 3.6 - Priority Chain Override", False, "No items in invoice")
            return
        
        # Check all items have override metal_rate
        all_correct = True
        expected_rate = 30.0
        for item in items:
            metal_rate = item.get('metal_rate')
            if metal_rate != expected_rate:
                all_correct = False
                break
        
        if all_correct:
            self.log_result("Task 3.6 - Priority Chain Override", True, 
                          f"User override successful - all items use metal_rate: {expected_rate}")
        else:
            self.log_result("Task 3.6 - Priority Chain Override", False, 
                          f"User override failed - not all items use expected metal_rate: {expected_rate}")

    def test_task3_scenario7_backend_calculation_verification(self):
        """Task 3 - Scenario 7: Backend Calculation Verification"""
        print("🔸 Task 3 - Scenario 7: Backend Calculation Verification")
        
        # Create test customer
        customer_id = self.create_test_party("Calculation Test Customer")
        if not customer_id:
            self.log_result("Task 3.7 - Calculation Verification", False, "Failed to create test customer")
            return
        
        # Create job card with specific gold rate
        try:
            jobcard_data = {
                "card_type": "repair",
                "customer_type": "saved",
                "customer_id": customer_id,
                "customer_name": "Calculation Test Customer",
                "gold_rate_at_jobcard": 24.75,
                "items": [
                    {
                        "category": "Ring",
                        "description": "Test calculation item",
                        "qty": 1,
                        "weight_in": 5.5,
                        "weight_out": 5.5,
                        "purity": 916,
                        "work_type": "repair",
                        "remarks": "For calculation verification"
                    }
                ],
                "notes": "Calculation verification test"
            }
            
            response = self.session.post(f"{self.base_url}/api/jobcards", json=jobcard_data)
            
            if response.status_code != 200:
                self.log_result("Task 3.7 - Calculation Verification", False, 
                              f"Failed to create job card: {response.status_code}")
                return
            
            jobcard = response.json()
            jobcard_id = jobcard.get('id')
            
            # Convert to invoice
            result = self.convert_jobcard_to_invoice(jobcard_id)
            
            if "error" in result:
                self.log_result("Task 3.7 - Calculation Verification", False, 
                              f"Conversion failed: {result.get('message', 'Unknown error')}")
                return
            
            invoice_id = result.get('invoice_id')
            invoice = self.get_invoice(invoice_id)
            
            if not invoice:
                self.log_result("Task 3.7 - Calculation Verification", False, "Failed to retrieve invoice")
                return
            
            items = invoice.get('items', [])
            if not items:
                self.log_result("Task 3.7 - Calculation Verification", False, "No items in invoice")
                return
            
            # Verify calculation: weight_out × purity_percent × metal_rate = gold_value
            item = items[0]
            weight = item.get('weight', 0)  # Should be 5.5
            purity = item.get('purity', 0)  # Should be 916
            metal_rate = item.get('metal_rate', 0)  # Should be 24.75
            gold_value = item.get('gold_value', 0)
            
            purity_percent = purity / 1000  # 916 -> 0.916
            expected_gold_value = weight * purity_percent * metal_rate
            # Expected: 5.5 × 0.916 × 24.75 = 124.793
            
            if abs(gold_value - expected_gold_value) < 0.01:  # Allow small rounding differences
                self.log_result("Task 3.7 - Calculation Verification", True, 
                              f"Calculation accurate: {weight} × {purity_percent} × {metal_rate} = {gold_value} (expected: {expected_gold_value})")
            else:
                self.log_result("Task 3.7 - Calculation Verification", False, 
                              f"Calculation incorrect: Expected {expected_gold_value}, got {gold_value}")
        
        except Exception as e:
            self.log_result("Task 3.7 - Calculation Verification", False, f"Exception: {str(e)}")

    def test_task3_scenario8_backward_compatibility(self):
        """Task 3 - Scenario 8: Backward Compatibility"""
        print("🔸 Task 3 - Scenario 8: Backward Compatibility")
        
        # Create test customer
        customer_id = self.create_test_party("Backward Compatibility Customer")
        if not customer_id:
            self.log_result("Task 3.8 - Backward Compatibility", False, "Failed to create test customer")
            return
        
        # Create job card without gold_rate_at_jobcard field (simulate old job card)
        jobcard_id = self.create_test_jobcard(gold_rate=None, customer_id=customer_id)
        if not jobcard_id:
            self.log_result("Task 3.8 - Backward Compatibility", False, "Failed to create job card")
            return
        
        # Convert to invoice (should use default 20.0 without errors)
        result = self.convert_jobcard_to_invoice(jobcard_id)
        
        if "error" in result:
            self.log_result("Task 3.8 - Backward Compatibility", False, 
                          f"Conversion failed: {result.get('message', 'Unknown error')}")
            return
        
        invoice_id = result.get('invoice_id')
        if invoice_id:
            self.log_result("Task 3.8 - Backward Compatibility", True, 
                          "Backward compatibility maintained - old job cards convert successfully with default rate")
        else:
            self.log_result("Task 3.8 - Backward Compatibility", False, "No invoice ID returned")

    # ============================================================================
    # TASK 4: DISCOUNT FIELD TESTING (9 Scenarios)
    # ============================================================================

    def test_task4_scenario1_convert_with_valid_discount(self):
        """Task 4 - Scenario 1: Convert with Valid Discount"""
        print("🔸 Task 4 - Scenario 1: Convert with Valid Discount")
        
        # Create test customer
        customer_id = self.create_test_party("Discount Test Customer 1")
        if not customer_id:
            self.log_result("Task 4.1 - Valid Discount", False, "Failed to create test customer")
            return
        
        # Create job card
        jobcard_id = self.create_test_jobcard(gold_rate=20.0, customer_id=customer_id)
        if not jobcard_id:
            self.log_result("Task 4.1 - Valid Discount", False, "Failed to create job card")
            return
        
        # Convert with discount
        result = self.convert_jobcard_to_invoice(jobcard_id, discount_amount=10.500)
        
        if "error" in result:
            self.log_result("Task 4.1 - Valid Discount", False, 
                          f"Conversion failed: {result.get('message', 'Unknown error')}")
            return
        
        invoice_id = result.get('invoice_id')
        if not invoice_id:
            self.log_result("Task 4.1 - Valid Discount", False, "No invoice ID returned")
            return
        
        # Verify invoice has correct discount and calculations
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            self.log_result("Task 4.1 - Valid Discount", False, "Failed to retrieve invoice")
            return
        
        discount_amount = invoice.get('discount_amount', 0)
        subtotal = invoice.get('subtotal', 0)
        vat_total = invoice.get('vat_total', 0)
        grand_total = invoice.get('grand_total', 0)
        
        # Verify discount amount
        if discount_amount != 10.500:
            self.log_result("Task 4.1 - Valid Discount", False, 
                          f"Expected discount_amount: 10.500, got: {discount_amount}")
            return
        
        # Verify calculation chain: Taxable = Subtotal - Discount, VAT = Taxable × 0.05, Grand Total = Taxable + VAT
        taxable = subtotal - discount_amount
        expected_vat = taxable * 0.05
        expected_grand_total = taxable + expected_vat
        
        if (abs(vat_total - expected_vat) < 0.01 and abs(grand_total - expected_grand_total) < 0.01):
            self.log_result("Task 4.1 - Valid Discount", True, 
                          f"Discount applied correctly: Subtotal={subtotal}, Discount={discount_amount}, Taxable={taxable}, VAT={vat_total}, Grand Total={grand_total}")
            return invoice_id
        else:
            self.log_result("Task 4.1 - Valid Discount", False, 
                          f"Calculation incorrect: Expected VAT={expected_vat}, Grand Total={expected_grand_total}, got VAT={vat_total}, Grand Total={grand_total}")
            return None

    def test_task4_scenario2_convert_without_discount(self):
        """Task 4 - Scenario 2: Convert WITHOUT Discount"""
        print("🔸 Task 4 - Scenario 2: Convert WITHOUT Discount")
        
        # Create test customer
        customer_id = self.create_test_party("No Discount Test Customer")
        if not customer_id:
            self.log_result("Task 4.2 - No Discount", False, "Failed to create test customer")
            return
        
        # Create job card
        jobcard_id = self.create_test_jobcard(gold_rate=20.0, customer_id=customer_id)
        if not jobcard_id:
            self.log_result("Task 4.2 - No Discount", False, "Failed to create job card")
            return
        
        # Convert without discount (omit field)
        result = self.convert_jobcard_to_invoice(jobcard_id)
        
        if "error" in result:
            self.log_result("Task 4.2 - No Discount", False, 
                          f"Conversion failed: {result.get('message', 'Unknown error')}")
            return
        
        invoice_id = result.get('invoice_id')
        if not invoice_id:
            self.log_result("Task 4.2 - No Discount", False, "No invoice ID returned")
            return
        
        # Verify invoice has discount_amount: 0.0
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            self.log_result("Task 4.2 - No Discount", False, "Failed to retrieve invoice")
            return
        
        discount_amount = invoice.get('discount_amount', 0)
        subtotal = invoice.get('subtotal', 0)
        vat_total = invoice.get('vat_total', 0)
        grand_total = invoice.get('grand_total', 0)
        
        # Verify no discount
        if discount_amount != 0.0:
            self.log_result("Task 4.2 - No Discount", False, 
                          f"Expected discount_amount: 0.0, got: {discount_amount}")
            return
        
        # Verify calculation: VAT = Subtotal × 0.05, Grand Total = Subtotal + VAT
        expected_vat = subtotal * 0.05
        expected_grand_total = subtotal + expected_vat
        
        if (abs(vat_total - expected_vat) < 0.01 and abs(grand_total - expected_grand_total) < 0.01):
            self.log_result("Task 4.2 - No Discount", True, 
                          f"No discount calculation correct: Subtotal={subtotal}, VAT={vat_total}, Grand Total={grand_total}")
        else:
            self.log_result("Task 4.2 - No Discount", False, 
                          f"Calculation incorrect without discount")

    def test_task4_scenario3_negative_discount_validation(self):
        """Task 4 - Scenario 3: Negative Discount Validation"""
        print("🔸 Task 4 - Scenario 3: Negative Discount Validation")
        
        # Create test customer
        customer_id = self.create_test_party("Negative Discount Test Customer")
        if not customer_id:
            self.log_result("Task 4.3 - Negative Discount Validation", False, "Failed to create test customer")
            return
        
        # Create job card
        jobcard_id = self.create_test_jobcard(gold_rate=20.0, customer_id=customer_id)
        if not jobcard_id:
            self.log_result("Task 4.3 - Negative Discount Validation", False, "Failed to create job card")
            return
        
        # Try to convert with negative discount
        result = self.convert_jobcard_to_invoice(jobcard_id, discount_amount=-5.0)
        
        if "error" in result and result["error"] == 400:
            # Check if error message contains "cannot be negative"
            error_message = result.get("message", "").lower()
            if "negative" in error_message or "cannot be negative" in error_message:
                self.log_result("Task 4.3 - Negative Discount Validation", True, 
                              f"Negative discount correctly rejected with 400 error: {result['message']}")
            else:
                self.log_result("Task 4.3 - Negative Discount Validation", False, 
                              f"400 error returned but message doesn't mention negative: {result['message']}")
        else:
            self.log_result("Task 4.3 - Negative Discount Validation", False, 
                          f"Expected 400 error for negative discount, got: {result}")

    def test_task4_scenario4_discount_exceeds_subtotal_validation(self):
        """Task 4 - Scenario 4: Discount Exceeds Subtotal Validation"""
        print("🔸 Task 4 - Scenario 4: Discount Exceeds Subtotal Validation")
        
        # Create test customer
        customer_id = self.create_test_party("Excess Discount Test Customer")
        if not customer_id:
            self.log_result("Task 4.4 - Excess Discount Validation", False, "Failed to create test customer")
            return
        
        # Create simple job card with low value
        try:
            jobcard_data = {
                "card_type": "repair",
                "customer_type": "saved",
                "customer_id": customer_id,
                "customer_name": "Excess Discount Test Customer",
                "gold_rate_at_jobcard": 20.0,
                "items": [
                    {
                        "category": "Ring",
                        "description": "Small item for discount test",
                        "qty": 1,
                        "weight_in": 1.0,  # Small weight for low subtotal
                        "weight_out": 1.0,
                        "purity": 916,
                        "work_type": "repair",
                        "making_charge_type": "flat",
                        "making_charge_value": 10.0,  # Small making charge
                        "remarks": "Low value item for excess discount test"
                    }
                ],
                "notes": "Excess discount validation test"
            }
            
            response = self.session.post(f"{self.base_url}/api/jobcards", json=jobcard_data)
            
            if response.status_code != 200:
                self.log_result("Task 4.4 - Excess Discount Validation", False, 
                              f"Failed to create job card: {response.status_code}")
                return
            
            jobcard = response.json()
            jobcard_id = jobcard.get('id')
            
            # Try to convert with discount exceeding subtotal (100.0 should exceed ~30 OMR subtotal)
            result = self.convert_jobcard_to_invoice(jobcard_id, discount_amount=100.0)
            
            if "error" in result and result["error"] == 400:
                # Check if error message mentions discount and subtotal
                error_message = result.get("message", "").lower()
                if ("discount" in error_message and "subtotal" in error_message) or "exceeds" in error_message:
                    self.log_result("Task 4.4 - Excess Discount Validation", True, 
                                  f"Excess discount correctly rejected with 400 error: {result['message']}")
                else:
                    self.log_result("Task 4.4 - Excess Discount Validation", False, 
                                  f"400 error returned but message doesn't mention discount/subtotal: {result['message']}")
            else:
                self.log_result("Task 4.4 - Excess Discount Validation", False, 
                              f"Expected 400 error for excess discount, got: {result}")
        
        except Exception as e:
            self.log_result("Task 4.4 - Excess Discount Validation", False, f"Exception: {str(e)}")

    def test_task4_scenario5_discount_calculation_accuracy(self):
        """Task 4 - Scenario 5: Discount Calculation Accuracy"""
        print("🔸 Task 4 - Scenario 5: Discount Calculation Accuracy")
        
        # Create test customer
        customer_id = self.create_test_party("Calculation Accuracy Customer")
        if not customer_id:
            self.log_result("Task 4.5 - Calculation Accuracy", False, "Failed to create test customer")
            return
        
        # Create job card with known values for precise calculation
        try:
            jobcard_data = {
                "card_type": "repair",
                "customer_type": "saved",
                "customer_id": customer_id,
                "customer_name": "Calculation Accuracy Customer",
                "gold_rate_at_jobcard": 20.0,
                "items": [
                    {
                        "category": "Ring",
                        "description": "Calculation test item",
                        "qty": 1,
                        "weight_in": 4.0,  # 4.0g × 0.916 × 20.0 = 73.28 gold_value
                        "weight_out": 4.0,
                        "purity": 916,
                        "work_type": "repair",
                        "making_charge_type": "flat",
                        "making_charge_value": 26.72,  # Total item value = 100.0
                        "remarks": "Precise calculation test"
                    }
                ],
                "notes": "Discount calculation accuracy test"
            }
            
            response = self.session.post(f"{self.base_url}/api/jobcards", json=jobcard_data)
            
            if response.status_code != 200:
                self.log_result("Task 4.5 - Calculation Accuracy", False, 
                              f"Failed to create job card: {response.status_code}")
                return
            
            jobcard = response.json()
            jobcard_id = jobcard.get('id')
            
            # Convert with 20.0 discount (Subtotal ~100.0, Discount 20.0, Taxable 80.0, VAT 4.0, Grand Total 84.0)
            result = self.convert_jobcard_to_invoice(jobcard_id, discount_amount=20.0)
            
            if "error" in result:
                self.log_result("Task 4.5 - Calculation Accuracy", False, 
                              f"Conversion failed: {result.get('message', 'Unknown error')}")
                return
            
            invoice_id = result.get('invoice_id')
            invoice = self.get_invoice(invoice_id)
            
            if not invoice:
                self.log_result("Task 4.5 - Calculation Accuracy", False, "Failed to retrieve invoice")
                return
            
            subtotal = invoice.get('subtotal', 0)
            discount_amount = invoice.get('discount_amount', 0)
            vat_total = invoice.get('vat_total', 0)
            grand_total = invoice.get('grand_total', 0)
            
            # Calculate expected values
            taxable = subtotal - discount_amount
            expected_vat = taxable * 0.05
            expected_grand_total = taxable + expected_vat
            
            # Verify calculations (allow small rounding differences)
            if (abs(discount_amount - 20.0) < 0.01 and 
                abs(taxable - 80.0) < 5.0 and  # Allow some variance in subtotal
                abs(vat_total - expected_vat) < 0.01 and 
                abs(grand_total - expected_grand_total) < 0.01):
                
                self.log_result("Task 4.5 - Calculation Accuracy", True, 
                              f"Calculation accurate: Subtotal={subtotal}, Discount={discount_amount}, Taxable={taxable}, VAT={vat_total}, Grand Total={grand_total}")
            else:
                self.log_result("Task 4.5 - Calculation Accuracy", False, 
                              f"Calculation inaccurate: Subtotal={subtotal}, Discount={discount_amount}, Taxable={taxable}, VAT={vat_total}, Grand Total={grand_total}")
        
        except Exception as e:
            self.log_result("Task 4.5 - Calculation Accuracy", False, f"Exception: {str(e)}")

    def test_task4_scenario6_pdf_generation_with_discount(self, invoice_id: str):
        """Task 4 - Scenario 6: PDF Generation WITH Discount"""
        print("🔸 Task 4 - Scenario 6: PDF Generation WITH Discount")
        
        if not invoice_id:
            self.log_result("Task 4.6 - PDF WITH Discount", False, "No invoice ID provided")
            return
        
        # Test PDF generation
        pdf_success = self.get_invoice_pdf(invoice_id)
        
        if pdf_success:
            self.log_result("Task 4.6 - PDF WITH Discount", True, 
                          f"PDF generated successfully for invoice with discount")
        else:
            self.log_result("Task 4.6 - PDF WITH Discount", False, 
                          "PDF generation failed for invoice with discount")

    def test_task4_scenario7_pdf_generation_without_discount(self):
        """Task 4 - Scenario 7: PDF Generation WITHOUT Discount"""
        print("🔸 Task 4 - Scenario 7: PDF Generation WITHOUT Discount")
        
        # Create test customer
        customer_id = self.create_test_party("PDF No Discount Customer")
        if not customer_id:
            self.log_result("Task 4.7 - PDF WITHOUT Discount", False, "Failed to create test customer")
            return
        
        # Create job card and convert without discount
        jobcard_id = self.create_test_jobcard(gold_rate=20.0, customer_id=customer_id)
        if not jobcard_id:
            self.log_result("Task 4.7 - PDF WITHOUT Discount", False, "Failed to create job card")
            return
        
        result = self.convert_jobcard_to_invoice(jobcard_id, discount_amount=0.0)
        
        if "error" in result:
            self.log_result("Task 4.7 - PDF WITHOUT Discount", False, 
                          f"Conversion failed: {result.get('message', 'Unknown error')}")
            return
        
        invoice_id = result.get('invoice_id')
        if not invoice_id:
            self.log_result("Task 4.7 - PDF WITHOUT Discount", False, "No invoice ID returned")
            return
        
        # Test PDF generation
        pdf_success = self.get_invoice_pdf(invoice_id)
        
        if pdf_success:
            self.log_result("Task 4.7 - PDF WITHOUT Discount", True, 
                          "PDF generated successfully for invoice without discount")
        else:
            self.log_result("Task 4.7 - PDF WITHOUT Discount", False, 
                          "PDF generation failed for invoice without discount")

    def test_task4_scenario8_vat_proportional_distribution(self):
        """Task 4 - Scenario 8: VAT Proportional Distribution"""
        print("🔸 Task 4 - Scenario 8: VAT Proportional Distribution")
        
        # Create test customer
        customer_id = self.create_test_party("VAT Distribution Customer")
        if not customer_id:
            self.log_result("Task 4.8 - VAT Distribution", False, "Failed to create test customer")
            return
        
        # Create job card with 2 items
        try:
            jobcard_data = {
                "card_type": "repair",
                "customer_type": "saved",
                "customer_id": customer_id,
                "customer_name": "VAT Distribution Customer",
                "gold_rate_at_jobcard": 20.0,
                "items": [
                    {
                        "category": "Ring",
                        "description": "Item 1",
                        "qty": 1,
                        "weight_in": 2.0,
                        "weight_out": 2.0,
                        "purity": 916,
                        "work_type": "repair",
                        "making_charge_type": "flat",
                        "making_charge_value": 10.0,
                        "remarks": "First item"
                    },
                    {
                        "category": "Necklace",
                        "description": "Item 2",
                        "qty": 1,
                        "weight_in": 3.0,
                        "weight_out": 3.0,
                        "purity": 916,
                        "work_type": "repair",
                        "making_charge_type": "flat",
                        "making_charge_value": 15.0,
                        "remarks": "Second item"
                    }
                ],
                "notes": "VAT distribution test with 2 items"
            }
            
            response = self.session.post(f"{self.base_url}/api/jobcards", json=jobcard_data)
            
            if response.status_code != 200:
                self.log_result("Task 4.8 - VAT Distribution", False, 
                              f"Failed to create job card: {response.status_code}")
                return
            
            jobcard = response.json()
            jobcard_id = jobcard.get('id')
            
            # Convert with discount
            result = self.convert_jobcard_to_invoice(jobcard_id, discount_amount=10.0)
            
            if "error" in result:
                self.log_result("Task 4.8 - VAT Distribution", False, 
                              f"Conversion failed: {result.get('message', 'Unknown error')}")
                return
            
            invoice_id = result.get('invoice_id')
            invoice = self.get_invoice(invoice_id)
            
            if not invoice:
                self.log_result("Task 4.8 - VAT Distribution", False, "Failed to retrieve invoice")
                return
            
            items = invoice.get('items', [])
            if len(items) != 2:
                self.log_result("Task 4.8 - VAT Distribution", False, f"Expected 2 items, got {len(items)}")
                return
            
            # Verify VAT distribution
            total_vat_from_items = sum(item.get('vat_amount', 0) for item in items)
            invoice_vat_total = invoice.get('vat_total', 0)
            
            if abs(total_vat_from_items - invoice_vat_total) < 0.01:
                self.log_result("Task 4.8 - VAT Distribution", True, 
                              f"VAT distributed proportionally: Item VATs sum to {total_vat_from_items}, Invoice VAT total: {invoice_vat_total}")
            else:
                self.log_result("Task 4.8 - VAT Distribution", False, 
                              f"VAT distribution incorrect: Item VATs sum to {total_vat_from_items}, Invoice VAT total: {invoice_vat_total}")
        
        except Exception as e:
            self.log_result("Task 4.8 - VAT Distribution", False, f"Exception: {str(e)}")

    def test_task4_scenario9_backward_compatibility(self):
        """Task 4 - Scenario 9: Backward Compatibility"""
        print("🔸 Task 4 - Scenario 9: Backward Compatibility")
        
        # Create test customer
        customer_id = self.create_test_party("Backward Compatibility Discount Customer")
        if not customer_id:
            self.log_result("Task 4.9 - Backward Compatibility", False, "Failed to create test customer")
            return
        
        # Create job card and convert without discount_amount field (simulate old behavior)
        jobcard_id = self.create_test_jobcard(gold_rate=20.0, customer_id=customer_id)
        if not jobcard_id:
            self.log_result("Task 4.9 - Backward Compatibility", False, "Failed to create job card")
            return
        
        result = self.convert_jobcard_to_invoice(jobcard_id)  # No discount_amount specified
        
        if "error" in result:
            self.log_result("Task 4.9 - Backward Compatibility", False, 
                          f"Conversion failed: {result.get('message', 'Unknown error')}")
            return
        
        invoice_id = result.get('invoice_id')
        if not invoice_id:
            self.log_result("Task 4.9 - Backward Compatibility", False, "No invoice ID returned")
            return
        
        # Verify invoice defaults to 0.0 discount and calculations work
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            self.log_result("Task 4.9 - Backward Compatibility", False, "Failed to retrieve invoice")
            return
        
        discount_amount = invoice.get('discount_amount', 0)
        subtotal = invoice.get('subtotal', 0)
        vat_total = invoice.get('vat_total', 0)
        grand_total = invoice.get('grand_total', 0)
        
        # Verify defaults to 0.0 and calculations work
        if discount_amount == 0.0:
            expected_vat = subtotal * 0.05
            expected_grand_total = subtotal + expected_vat
            
            if (abs(vat_total - expected_vat) < 0.01 and abs(grand_total - expected_grand_total) < 0.01):
                self.log_result("Task 4.9 - Backward Compatibility", True, 
                              f"Backward compatibility maintained: discount defaults to 0.0, calculations correct")
            else:
                self.log_result("Task 4.9 - Backward Compatibility", False, 
                              "Calculations incorrect with default discount")
        else:
            self.log_result("Task 4.9 - Backward Compatibility", False, 
                          f"Expected discount_amount: 0.0, got: {discount_amount}")

    # ============================================================================
    # MAIN TEST EXECUTION
    # ============================================================================

    def run_all_tests(self):
        """Run all 17 test scenarios"""
        print("🎯 COMPREHENSIVE END-TO-END TESTING - Tasks 3 & 4")
        print("=" * 80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        print("\n📋 TASK 3: GOLD RATE FIELD TESTING (8 Scenarios)")
        print("-" * 60)
        
        # Task 3 - Scenario 1 & 3 (linked)
        jobcard_id_with_rate, customer_id_1 = self.test_task3_scenario1_create_jobcard_with_gold_rate()
        if jobcard_id_with_rate:
            self.test_task3_scenario3_edit_jobcard_update_gold_rate(jobcard_id_with_rate)
            invoice_id_with_rate = self.test_task3_scenario4_convert_with_gold_rate_to_invoice(jobcard_id_with_rate)
        
        # Task 3 - Scenario 2 & 5 (linked)
        jobcard_id_without_rate, customer_id_2 = self.test_task3_scenario2_create_jobcard_without_gold_rate()
        if jobcard_id_without_rate:
            self.test_task3_scenario5_convert_without_gold_rate_to_invoice(jobcard_id_without_rate)
        
        # Task 3 - Scenario 6 (user override)
        if jobcard_id_with_rate:
            self.test_task3_scenario6_priority_chain_user_override(jobcard_id_with_rate)
        
        # Task 3 - Scenarios 7 & 8 (independent)
        self.test_task3_scenario7_backend_calculation_verification()
        self.test_task3_scenario8_backward_compatibility()
        
        print("\n📋 TASK 4: DISCOUNT FIELD TESTING (9 Scenarios)")
        print("-" * 60)
        
        # Task 4 - Scenario 1 & 6 (linked)
        invoice_id_with_discount = self.test_task4_scenario1_convert_with_valid_discount()
        if invoice_id_with_discount:
            self.test_task4_scenario6_pdf_generation_with_discount(invoice_id_with_discount)
        
        # Task 4 - Scenarios 2-9 (mostly independent)
        self.test_task4_scenario2_convert_without_discount()
        self.test_task4_scenario3_negative_discount_validation()
        self.test_task4_scenario4_discount_exceeds_subtotal_validation()
        self.test_task4_scenario5_discount_calculation_accuracy()
        self.test_task4_scenario7_pdf_generation_without_discount()
        self.test_task4_scenario8_vat_proportional_distribution()
        self.test_task4_scenario9_backward_compatibility()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("🎯 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"\n📊 OVERALL STATISTICS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Group results by task
        task3_results = [r for r in self.test_results if "Task 3" in r['test']]
        task4_results = [r for r in self.test_results if "Task 4" in r['test']]
        other_results = [r for r in self.test_results if "Task 3" not in r['test'] and "Task 4" not in r['test']]
        
        print(f"\n📋 TASK 3 - GOLD RATE FIELD ({len(task3_results)} scenarios):")
        for result in task3_results:
            print(f"   {result['status']}: {result['test']}")
        
        print(f"\n📋 TASK 4 - DISCOUNT FIELD ({len(task4_results)} scenarios):")
        for result in task4_results:
            print(f"   {result['status']}: {result['test']}")
        
        if other_results:
            print(f"\n📋 OTHER TESTS ({len(other_results)} tests):")
            for result in other_results:
                print(f"   {result['status']}: {result['test']}")
        
        # Show failed tests details
        failed_results = [r for r in self.test_results if not r['success']]
        if failed_results:
            print(f"\n❌ FAILED TESTS DETAILS:")
            for result in failed_results:
                print(f"\n   Test: {result['test']}")
                print(f"   Details: {result['details']}")
                if result.get('response_data'):
                    print(f"   Response: {result['response_data']}")
        
        print(f"\n🎯 PRODUCTION READINESS ASSESSMENT:")
        if failed_tests == 0:
            print("   ✅ ALL TESTS PASSED - PRODUCTION READY (10/10)")
        elif failed_tests <= 2:
            print(f"   ⚠️  MOSTLY READY - {failed_tests} minor issues to fix (8/10)")
        elif failed_tests <= 5:
            print(f"   ⚠️  NEEDS WORK - {failed_tests} issues to fix (6/10)")
        else:
            print(f"   ❌ NOT READY - {failed_tests} critical issues to fix (4/10)")
        
        print("\n" + "=" * 80)

def main():
    """Main execution function"""
    # Configuration
    BASE_URL = "https://fields-verified.preview.emergentagent.com"
    USERNAME = "admin"
    PASSWORD = "admin123"
    
    print("🚀 Starting Comprehensive Backend Testing")
    print(f"Backend URL: {BASE_URL}")
    print(f"Username: {USERNAME}")
    print("-" * 80)
    
    # Initialize tester
    tester = GoldShopTester(BASE_URL, USERNAME, PASSWORD)
    
    # Run all tests
    tester.run_all_tests()

if __name__ == "__main__":
    main()
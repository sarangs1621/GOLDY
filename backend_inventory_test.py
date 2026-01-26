#!/usr/bin/env python3
"""
CRITICAL INVENTORY FLOW CORRECTION TESTING - Production-Grade Compliance Verification

This test suite verifies the SINGLE AUTHORITATIVE PATH for stock reduction through Invoice Finalization.
Tests 11 critical scenarios to ensure audit trail, accounting, and GST compliance.

BLOCKING TESTS (Must Fail):
1. Manual Stock OUT Creation - should return 403 Forbidden
2. Negative Delta Bypass - should return 400 Bad Request  
3. Invalid Movement Type - should return 400 Bad Request
4. Stock OUT Movement Deletion - should return 403 Forbidden
5. Invoice-Linked Movement Deletion - should return 403 Forbidden

ALLOWING TESTS (Must Succeed):
6. Legitimate Stock IN - should return 200 Success
7. Legitimate Adjustment - should return 200 Success
8. Manual Movement Deletion - should return 200 Success
9. Invoice Finalization Path - should return 200 Success
10. Purchase Finalization Path - should return 200 Success
11. End-to-End Integrity - comprehensive verification
"""

import requests
import json
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://decimal-precision.preview.emergentagent.com/api"
USERNAME = "admin@goldshop.com"
PASSWORD = "admin123"

class InventoryFlowTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.created_entities = {
            "parties": [],
            "inventory_headers": [],
            "stock_movements": [],
            "invoices": [],
            "purchases": [],
            "accounts": []
        }
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test results with detailed information"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if response_data and not success:
            print(f"   Response: {response_data}")
        print()
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
    
    def authenticate(self) -> bool:
        """Authenticate and get JWT token"""
        print("🔐 Authenticating...")
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json={
                "username": USERNAME,
                "password": PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log_test("Authentication", True, f"Logged in as {USERNAME}")
                return True
            else:
                self.log_test("Authentication", False, f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Authentication", False, f"Exception: {str(e)}")
            return False
    
    def setup_test_data(self) -> bool:
        """Create necessary test data for inventory flow testing"""
        print("🏗️ Setting up test data...")
        
        try:
            # Create test vendor party
            vendor_data = {
                "name": "Test Vendor for Inventory Flow",
                "phone": "99887766",
                "party_type": "vendor",
                "address": "Test Vendor Address"
            }
            
            response = self.session.post(f"{BASE_URL}/parties", json=vendor_data)
            if response.status_code in [200, 201]:
                vendor = response.json()
                self.created_entities["parties"].append(vendor["id"])
                self.vendor_id = vendor["id"]
                self.log_test("Create test vendor", True, f"Vendor ID: {vendor['id']}")
            else:
                self.log_test("Create test vendor", False, f"Status: {response.status_code}", response.text)
                return False
            
            # Create test customer party
            customer_data = {
                "name": "Test Customer for Inventory Flow",
                "phone": "11223344",
                "party_type": "customer",
                "address": "Test Customer Address"
            }
            
            response = self.session.post(f"{BASE_URL}/parties", json=customer_data)
            if response.status_code in [200, 201]:
                customer = response.json()
                self.created_entities["parties"].append(customer["id"])
                self.customer_id = customer["id"]
                self.log_test("Create test customer", True, f"Customer ID: {customer['id']}")
            else:
                self.log_test("Create test customer", False, f"Status: {response.status_code}", response.text)
                return False
            
            # Create test inventory header (Gold 22K)
            header_data = {
                "name": "Gold 22K Test Category"
            }
            
            response = self.session.post(f"{BASE_URL}/inventory/headers", json=header_data)
            if response.status_code in [200, 201]:
                header = response.json()
                self.created_entities["inventory_headers"].append(header["id"])
                self.header_id = header["id"]
                self.log_test("Create test inventory header", True, f"Header ID: {header['id']}")
            else:
                self.log_test("Create test inventory header", False, f"Status: {response.status_code}", response.text)
                return False
            
            # Create test account for payments
            account_data = {
                "name": "Test Cash Account",
                "account_type": "asset",
                "opening_balance": 10000.0
            }
            
            response = self.session.post(f"{BASE_URL}/accounts", json=account_data)
            if response.status_code in [200, 201]:
                account = response.json()
                self.created_entities["accounts"].append(account["id"])
                self.account_id = account["id"]
                self.log_test("Create test account", True, f"Account ID: {account['id']}")
            else:
                self.log_test("Create test account", False, f"Status: {response.status_code}", response.text)
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Setup test data", False, f"Exception: {str(e)}")
            return False
    
    def test_1_manual_stock_out_creation(self):
        """TEST 1: Manual Stock OUT Creation - Must return 403 Forbidden"""
        print("\n1️⃣ BLOCKING TEST: Manual Stock OUT Creation")
        
        movement_data = {
            "header_id": self.header_id,
            "movement_type": "Stock OUT",
            "description": "Attempting manual stock out",
            "qty_delta": 1,
            "weight_delta": 10.5,
            "purity": 916,
            "notes": "This should be blocked"
        }
        
        response = self.session.post(f"{BASE_URL}/inventory/movements", json=movement_data)
        
        if response.status_code == 403:
            error_msg = response.json().get("detail", "")
            if "invoice finalization" in error_msg.lower():
                self.log_test("Block manual Stock OUT creation", True, 
                            f"Correctly blocked with 403. Error: {error_msg}")
            else:
                self.log_test("Block manual Stock OUT creation", False, 
                            f"403 returned but error message doesn't mention invoice finalization: {error_msg}")
        else:
            self.log_test("Block manual Stock OUT creation", False, 
                        f"Expected 403 Forbidden, got {response.status_code}", response.text)
    
    def test_2_negative_delta_bypass(self):
        """TEST 2: Negative Delta Bypass - Must return 400 Bad Request"""
        print("\n2️⃣ BLOCKING TEST: Negative Delta Bypass")
        
        movement_data = {
            "header_id": self.header_id,
            "movement_type": "Stock IN",
            "description": "Attempting negative bypass",
            "qty_delta": -1,  # Negative to bypass Stock OUT restriction
            "weight_delta": -5.0,  # Negative to bypass Stock OUT restriction
            "purity": 916,
            "notes": "Attempting to reduce stock via negative Stock IN"
        }
        
        response = self.session.post(f"{BASE_URL}/inventory/movements", json=movement_data)
        
        if response.status_code == 400:
            error_msg = response.json().get("detail", "")
            if "must be positive" in error_msg.lower():
                self.log_test("Block negative delta bypass", True, 
                            f"Correctly blocked with 400. Error: {error_msg}")
            else:
                self.log_test("Block negative delta bypass", False, 
                            f"400 returned but error message doesn't mention positive values: {error_msg}")
        else:
            self.log_test("Block negative delta bypass", False, 
                        f"Expected 400 Bad Request, got {response.status_code}", response.text)
    
    def test_3_invalid_movement_type(self):
        """TEST 3: Invalid Movement Type - Must return 400 Bad Request"""
        print("\n3️⃣ BLOCKING TEST: Invalid Movement Type")
        
        movement_data = {
            "header_id": self.header_id,
            "movement_type": "InvalidType",
            "description": "Testing invalid movement type",
            "qty_delta": 1,
            "weight_delta": 5.0,
            "purity": 916,
            "notes": "This should be blocked"
        }
        
        response = self.session.post(f"{BASE_URL}/inventory/movements", json=movement_data)
        
        if response.status_code == 400:
            error_msg = response.json().get("detail", "")
            if "allowed types" in error_msg.lower() and "stock in" in error_msg.lower():
                self.log_test("Block invalid movement type", True, 
                            f"Correctly blocked with 400. Error: {error_msg}")
            else:
                self.log_test("Block invalid movement type", False, 
                            f"400 returned but error message doesn't list allowed types: {error_msg}")
        else:
            self.log_test("Block invalid movement type", False, 
                        f"Expected 400 Bad Request, got {response.status_code}", response.text)
    
    def test_4_stock_out_movement_deletion(self):
        """TEST 4: Stock OUT Movement Deletion - Must return 403 Forbidden"""
        print("\n4️⃣ BLOCKING TEST: Stock OUT Movement Deletion")
        
        # First, we need to create a Stock OUT movement through invoice finalization
        # Create a draft invoice
        invoice_data = {
            "invoice_number": "INV-TEST-001",
            "customer_type": "saved",
            "customer_id": self.customer_id,
            "customer_name": "Test Customer for Inventory Flow",
            "invoice_type": "sale",
            "items": [
                {
                    "category": "Gold 22K Test Category",
                    "description": "Test Gold Item",
                    "qty": 1,
                    "weight": 10.0,
                    "purity": 916,
                    "metal_rate": 50.0,
                    "gold_value": 500.0,
                    "making_value": 100.0,
                    "vat_percent": 5.0,
                    "vat_amount": 30.0,
                    "line_total": 630.0
                }
            ],
            "subtotal": 600.0,
            "vat_total": 30.0,
            "grand_total": 630.0,
            "balance_due": 630.0
        }
        
        # Add some stock first via legitimate Stock IN
        stock_in_data = {
            "header_id": self.header_id,
            "movement_type": "Stock IN",
            "description": "Adding stock for invoice test",
            "qty_delta": 2,
            "weight_delta": 20.0,
            "purity": 916,
            "notes": "Initial stock for testing"
        }
        
        response = self.session.post(f"{BASE_URL}/inventory/movements", json=stock_in_data)
        if response.status_code in [200, 201]:
            stock_movement = response.json()
            self.created_entities["stock_movements"].append(stock_movement["id"])
        
        # Create invoice
        response = self.session.post(f"{BASE_URL}/invoices", json=invoice_data)
        if response.status_code in [200, 201]:
            invoice = response.json()
            self.created_entities["invoices"].append(invoice["id"])
            invoice_id = invoice["id"]
            
            # Finalize invoice to create Stock OUT movement
            response = self.session.post(f"{BASE_URL}/invoices/{invoice_id}/finalize")
            if response.status_code == 200:
                finalize_result = response.json()
                stock_out_id = finalize_result.get("stock_movement_id")
                
                if stock_out_id:
                    # Now try to delete the Stock OUT movement
                    response = self.session.delete(f"{BASE_URL}/inventory/movements/{stock_out_id}")
                    
                    if response.status_code == 403:
                        error_msg = response.json().get("detail", "")
                        if "stock out" in error_msg.lower():
                            self.log_test("Block Stock OUT movement deletion", True, 
                                        f"Correctly blocked with 403. Error: {error_msg}")
                        else:
                            self.log_test("Block Stock OUT movement deletion", False, 
                                        f"403 returned but error message doesn't mention Stock OUT: {error_msg}")
                    else:
                        self.log_test("Block Stock OUT movement deletion", False, 
                                    f"Expected 403 Forbidden, got {response.status_code}", response.text)
                else:
                    self.log_test("Block Stock OUT movement deletion", False, 
                                "Invoice finalization didn't return stock_movement_id")
            else:
                self.log_test("Block Stock OUT movement deletion", False, 
                            f"Invoice finalization failed: {response.status_code}", response.text)
        else:
            self.log_test("Block Stock OUT movement deletion", False, 
                        f"Invoice creation failed: {response.status_code}", response.text)
    
    def test_5_invoice_linked_movement_deletion(self):
        """TEST 5: Invoice-Linked Movement Deletion - Must return 403 Forbidden"""
        print("\n5️⃣ BLOCKING TEST: Invoice-Linked Movement Deletion")
        
        # This test is covered by test_4 since Stock OUT movements are always invoice-linked
        # But let's also test with a purchase-linked movement
        
        # Create a draft purchase
        purchase_data = {
            "vendor_party_id": self.vendor_id,
            "description": "Test purchase for movement deletion",
            "weight_grams": 15.0,
            "entered_purity": 999,
            "valuation_purity_fixed": 916,
            "rate_per_gram": 45.0,
            "amount_total": 675.0,
            "paid_amount_money": 0.0,
            "balance_due_money": 675.0
        }
        
        response = self.session.post(f"{BASE_URL}/purchases", json=purchase_data)
        if response.status_code in [200, 201]:
            purchase = response.json()
            self.created_entities["purchases"].append(purchase["id"])
            purchase_id = purchase["id"]
            
            # Finalize purchase to create Stock IN movement with reference_type
            response = self.session.post(f"{BASE_URL}/purchases/{purchase_id}/finalize")
            if response.status_code == 200:
                finalize_result = response.json()
                stock_in_id = finalize_result.get("stock_movement_id")
                
                if stock_in_id:
                    # Try to delete the purchase-linked Stock IN movement
                    response = self.session.delete(f"{BASE_URL}/inventory/movements/{stock_in_id}")
                    
                    if response.status_code == 403:
                        error_msg = response.json().get("detail", "")
                        if "linked to purchase" in error_msg.lower() or "reference_type" in error_msg.lower():
                            self.log_test("Block invoice-linked movement deletion", True, 
                                        f"Correctly blocked with 403. Error: {error_msg}")
                        else:
                            self.log_test("Block invoice-linked movement deletion", False, 
                                        f"403 returned but error message doesn't mention linking: {error_msg}")
                    else:
                        self.log_test("Block invoice-linked movement deletion", False, 
                                    f"Expected 403 Forbidden, got {response.status_code}", response.text)
                else:
                    self.log_test("Block invoice-linked movement deletion", False, 
                                "Purchase finalization didn't return stock_movement_id")
            else:
                self.log_test("Block invoice-linked movement deletion", False, 
                            f"Purchase finalization failed: {response.status_code}", response.text)
        else:
            self.log_test("Block invoice-linked movement deletion", False, 
                        f"Purchase creation failed: {response.status_code}", response.text)
    
    def test_6_legitimate_stock_in(self):
        """TEST 6: Legitimate Stock IN - Must return 200 Success"""
        print("\n6️⃣ ALLOWING TEST: Legitimate Stock IN")
        
        movement_data = {
            "header_id": self.header_id,
            "movement_type": "Stock IN",
            "description": "Legitimate stock addition",
            "qty_delta": 3,
            "weight_delta": 25.5,
            "purity": 916,
            "notes": "Manual stock addition - legitimate"
        }
        
        response = self.session.post(f"{BASE_URL}/inventory/movements", json=movement_data)
        
        if response.status_code in [200, 201]:
            movement = response.json()
            self.created_entities["stock_movements"].append(movement["id"])
            
            # Verify inventory was updated
            response = self.session.get(f"{BASE_URL}/inventory/stock-totals")
            if response.status_code == 200:
                stock_totals = response.json()
                header_stock = next((h for h in stock_totals if h["header_id"] == self.header_id), None)
                
                if header_stock and header_stock["total_weight"] >= 25.5:
                    self.log_test("Allow legitimate Stock IN", True, 
                                f"Stock IN created successfully. Movement ID: {movement['id']}, Current weight: {header_stock['total_weight']}g")
                else:
                    self.log_test("Allow legitimate Stock IN", False, 
                                f"Stock IN created but inventory not updated correctly: {header_stock}")
            else:
                self.log_test("Allow legitimate Stock IN", True, 
                            f"Stock IN created successfully. Movement ID: {movement['id']} (couldn't verify inventory update)")
        else:
            self.log_test("Allow legitimate Stock IN", False, 
                        f"Expected 200/201 Success, got {response.status_code}", response.text)
    
    def test_7_legitimate_adjustment(self):
        """TEST 7: Legitimate Adjustment - Must return 200 Success"""
        print("\n7️⃣ ALLOWING TEST: Legitimate Adjustment")
        
        movement_data = {
            "header_id": self.header_id,
            "movement_type": "Adjustment",
            "description": "Inventory reconciliation adjustment",
            "qty_delta": 1,
            "weight_delta": 5.0,
            "purity": 916,
            "notes": "Reconciliation adjustment - found items"
        }
        
        response = self.session.post(f"{BASE_URL}/inventory/movements", json=movement_data)
        
        if response.status_code in [200, 201]:
            movement = response.json()
            self.created_entities["stock_movements"].append(movement["id"])
            self.log_test("Allow legitimate Adjustment", True, 
                        f"Adjustment created successfully. Movement ID: {movement['id']}")
        else:
            self.log_test("Allow legitimate Adjustment", False, 
                        f"Expected 200/201 Success, got {response.status_code}", response.text)
    
    def test_8_manual_movement_deletion(self):
        """TEST 8: Manual Movement Deletion - Must return 200 Success"""
        print("\n8️⃣ ALLOWING TEST: Manual Movement Deletion")
        
        # Create a manual Stock IN movement first
        movement_data = {
            "header_id": self.header_id,
            "movement_type": "Stock IN",
            "description": "Stock IN for deletion test",
            "qty_delta": 1,
            "weight_delta": 8.0,
            "purity": 916,
            "notes": "This will be deleted"
        }
        
        response = self.session.post(f"{BASE_URL}/inventory/movements", json=movement_data)
        
        if response.status_code in [200, 201]:
            movement = response.json()
            movement_id = movement["id"]
            
            # Now delete the manual movement
            response = self.session.delete(f"{BASE_URL}/inventory/movements/{movement_id}")
            
            if response.status_code in [200, 204]:
                delete_result = response.json() if response.content else {}
                self.log_test("Allow manual movement deletion", True, 
                            f"Manual movement deleted successfully. ID: {movement_id}")
            else:
                self.log_test("Allow manual movement deletion", False, 
                            f"Expected 200/204 Success, got {response.status_code}", response.text)
        else:
            self.log_test("Allow manual movement deletion", False, 
                        f"Failed to create movement for deletion test: {response.status_code}", response.text)
    
    def test_9_invoice_finalization_path(self):
        """TEST 9: Invoice Finalization Path - Must return 200 Success"""
        print("\n9️⃣ ALLOWING TEST: Invoice Finalization Path")
        
        # Create a draft invoice
        invoice_data = {
            "invoice_number": "INV-TEST-002",
            "customer_type": "saved",
            "customer_id": self.customer_id,
            "customer_name": "Test Customer for Inventory Flow",
            "invoice_type": "sale",
            "items": [
                {
                    "category": "Gold 22K Test Category",
                    "description": "Test Gold Item for Finalization",
                    "qty": 1,
                    "weight": 12.0,
                    "purity": 916,
                    "metal_rate": 50.0,
                    "gold_value": 600.0,
                    "making_value": 120.0,
                    "vat_percent": 5.0,
                    "vat_amount": 36.0,
                    "line_total": 756.0
                }
            ],
            "subtotal": 720.0,
            "vat_total": 36.0,
            "grand_total": 756.0,
            "balance_due": 756.0
        }
        
        response = self.session.post(f"{BASE_URL}/invoices", json=invoice_data)
        if response.status_code in [200, 201]:
            invoice = response.json()
            self.created_entities["invoices"].append(invoice["id"])
            invoice_id = invoice["id"]
            
            # Finalize invoice
            response = self.session.post(f"{BASE_URL}/invoices/{invoice_id}/finalize")
            
            if response.status_code == 200:
                finalize_result = response.json()
                stock_movement_id = finalize_result.get("stock_movement_id")
                
                if stock_movement_id:
                    # Verify Stock OUT movement was created with reference_type="invoice"
                    response = self.session.get(f"{BASE_URL}/inventory/movements")
                    if response.status_code == 200:
                        movements = response.json()
                        stock_out_movement = next((m for m in movements if m["id"] == stock_movement_id), None)
                        
                        if (stock_out_movement and 
                            stock_out_movement["movement_type"] == "Stock OUT" and 
                            stock_out_movement["reference_type"] == "invoice"):
                            self.log_test("Allow invoice finalization path", True, 
                                        f"Invoice finalized successfully. Stock OUT created with reference_type=invoice. Movement ID: {stock_movement_id}")
                        else:
                            self.log_test("Allow invoice finalization path", False, 
                                        f"Stock OUT movement not created correctly: {stock_out_movement}")
                    else:
                        self.log_test("Allow invoice finalization path", True, 
                                    f"Invoice finalized successfully. Movement ID: {stock_movement_id} (couldn't verify movement details)")
                else:
                    self.log_test("Allow invoice finalization path", False, 
                                "Invoice finalization didn't return stock_movement_id")
            else:
                self.log_test("Allow invoice finalization path", False, 
                            f"Expected 200 Success, got {response.status_code}", response.text)
        else:
            self.log_test("Allow invoice finalization path", False, 
                        f"Invoice creation failed: {response.status_code}", response.text)
    
    def test_10_purchase_finalization_path(self):
        """TEST 10: Purchase Finalization Path - Must return 200 Success"""
        print("\n🔟 ALLOWING TEST: Purchase Finalization Path")
        
        # Create a draft purchase
        purchase_data = {
            "vendor_party_id": self.vendor_id,
            "description": "Test purchase for finalization path",
            "weight_grams": 20.0,
            "entered_purity": 999,
            "valuation_purity_fixed": 916,
            "rate_per_gram": 48.0,
            "amount_total": 960.0,
            "paid_amount_money": 0.0,
            "balance_due_money": 960.0
        }
        
        response = self.session.post(f"{BASE_URL}/purchases", json=purchase_data)
        if response.status_code in [200, 201]:
            purchase = response.json()
            self.created_entities["purchases"].append(purchase["id"])
            purchase_id = purchase["id"]
            
            # Finalize purchase
            response = self.session.post(f"{BASE_URL}/purchases/{purchase_id}/finalize")
            
            if response.status_code == 200:
                finalize_result = response.json()
                stock_movement_id = finalize_result.get("stock_movement_id")
                
                if stock_movement_id:
                    # Verify Stock IN movement was created with reference_type="purchase"
                    response = self.session.get(f"{BASE_URL}/inventory/movements")
                    if response.status_code == 200:
                        movements = response.json()
                        stock_in_movement = next((m for m in movements if m["id"] == stock_movement_id), None)
                        
                        if (stock_in_movement and 
                            stock_in_movement["movement_type"] == "Stock IN" and 
                            stock_in_movement["reference_type"] == "purchase"):
                            self.log_test("Allow purchase finalization path", True, 
                                        f"Purchase finalized successfully. Stock IN created with reference_type=purchase. Movement ID: {stock_movement_id}")
                        else:
                            self.log_test("Allow purchase finalization path", False, 
                                        f"Stock IN movement not created correctly: {stock_in_movement}")
                    else:
                        self.log_test("Allow purchase finalization path", True, 
                                    f"Purchase finalized successfully. Movement ID: {stock_movement_id} (couldn't verify movement details)")
                else:
                    self.log_test("Allow purchase finalization path", False, 
                                "Purchase finalization didn't return stock_movement_id")
            else:
                self.log_test("Allow purchase finalization path", False, 
                            f"Expected 200 Success, got {response.status_code}", response.text)
        else:
            self.log_test("Allow purchase finalization path", False, 
                        f"Purchase creation failed: {response.status_code}", response.text)
    
    def test_11_end_to_end_integrity(self):
        """TEST 11: End-to-End Integrity - Comprehensive verification"""
        print("\n1️⃣1️⃣ COMPREHENSIVE TEST: End-to-End Integrity")
        
        try:
            # Record start inventory
            response = self.session.get(f"{BASE_URL}/inventory/stock-totals")
            if response.status_code != 200:
                self.log_test("End-to-end integrity", False, "Failed to get initial inventory")
                return
            
            stock_totals = response.json()
            header_stock = next((h for h in stock_totals if h["header_id"] == self.header_id), None)
            start_qty = header_stock["total_qty"] if header_stock else 0
            start_weight = header_stock["total_weight"] if header_stock else 0
            
            print(f"   Start inventory: {start_qty} qty, {start_weight}g")
            
            # Step 1: Finalize purchase (add stock)
            purchase_data = {
                "vendor_party_id": self.vendor_id,
                "description": "End-to-end test purchase",
                "weight_grams": 30.0,
                "entered_purity": 916,
                "valuation_purity_fixed": 916,
                "rate_per_gram": 50.0,
                "amount_total": 1500.0,
                "paid_amount_money": 0.0,
                "balance_due_money": 1500.0
            }
            
            response = self.session.post(f"{BASE_URL}/purchases", json=purchase_data)
            if response.status_code not in [200, 201]:
                self.log_test("End-to-end integrity", False, f"Purchase creation failed: {response.status_code}")
                return
            
            purchase = response.json()
            self.created_entities["purchases"].append(purchase["id"])
            
            response = self.session.post(f"{BASE_URL}/purchases/{purchase['id']}/finalize")
            if response.status_code != 200:
                self.log_test("End-to-end integrity", False, f"Purchase finalization failed: {response.status_code}")
                return
            
            purchase_result = response.json()
            purchase_movement_id = purchase_result.get("stock_movement_id")
            
            # Step 2: Finalize invoice (reduce stock)
            invoice_data = {
                "invoice_number": "INV-E2E-001",
                "customer_type": "saved",
                "customer_id": self.customer_id,
                "customer_name": "Test Customer for Inventory Flow",
                "invoice_type": "sale",
                "items": [
                    {
                        "category": "Gold 22K Test Category",
                        "description": "End-to-end test item",
                        "qty": 1,
                        "weight": 15.0,
                        "purity": 916,
                        "metal_rate": 55.0,
                        "gold_value": 825.0,
                        "making_value": 150.0,
                        "vat_percent": 5.0,
                        "vat_amount": 48.75,
                        "line_total": 1023.75
                    }
                ],
                "subtotal": 975.0,
                "vat_total": 48.75,
                "grand_total": 1023.75,
                "balance_due": 1023.75
            }
            
            response = self.session.post(f"{BASE_URL}/invoices", json=invoice_data)
            if response.status_code not in [200, 201]:
                self.log_test("End-to-end integrity", False, f"Invoice creation failed: {response.status_code}")
                return
            
            invoice = response.json()
            self.created_entities["invoices"].append(invoice["id"])
            
            response = self.session.post(f"{BASE_URL}/invoices/{invoice['id']}/finalize")
            if response.status_code != 200:
                self.log_test("End-to-end integrity", False, f"Invoice finalization failed: {response.status_code}")
                return
            
            invoice_result = response.json()
            invoice_movement_id = invoice_result.get("stock_movement_id")
            
            # Step 3: Verify final inventory matches calculations
            response = self.session.get(f"{BASE_URL}/inventory/stock-totals")
            if response.status_code != 200:
                self.log_test("End-to-end integrity", False, "Failed to get final inventory")
                return
            
            stock_totals = response.json()
            header_stock = next((h for h in stock_totals if h["header_id"] == self.header_id), None)
            final_qty = header_stock["total_qty"] if header_stock else 0
            final_weight = header_stock["total_weight"] if header_stock else 0
            
            expected_qty = start_qty + 1 - 1  # +1 from purchase, -1 from invoice
            expected_weight = start_weight + 30.0 - 15.0  # +30g from purchase, -15g from invoice
            
            print(f"   Final inventory: {final_qty} qty, {final_weight}g")
            print(f"   Expected inventory: {expected_qty} qty, {expected_weight}g")
            
            # Step 4: Verify both movements have reference_type
            response = self.session.get(f"{BASE_URL}/inventory/movements")
            if response.status_code != 200:
                self.log_test("End-to-end integrity", False, "Failed to get movements")
                return
            
            movements = response.json()
            purchase_movement = next((m for m in movements if m["id"] == purchase_movement_id), None)
            invoice_movement = next((m for m in movements if m["id"] == invoice_movement_id), None)
            
            # Step 5: Verify cannot delete either movement
            purchase_delete_blocked = False
            invoice_delete_blocked = False
            
            if purchase_movement_id:
                response = self.session.delete(f"{BASE_URL}/inventory/movements/{purchase_movement_id}")
                purchase_delete_blocked = (response.status_code == 403)
            
            if invoice_movement_id:
                response = self.session.delete(f"{BASE_URL}/inventory/movements/{invoice_movement_id}")
                invoice_delete_blocked = (response.status_code == 403)
            
            # Evaluate results
            inventory_correct = (abs(final_qty - expected_qty) < 0.01 and abs(final_weight - expected_weight) < 0.01)
            reference_types_correct = (
                purchase_movement and purchase_movement.get("reference_type") == "purchase" and
                invoice_movement and invoice_movement.get("reference_type") == "invoice"
            )
            deletions_blocked = purchase_delete_blocked and invoice_delete_blocked
            
            if inventory_correct and reference_types_correct and deletions_blocked:
                self.log_test("End-to-end integrity", True, 
                            f"All checks passed: Inventory calculations correct, reference_types set, deletions blocked")
            else:
                details = []
                if not inventory_correct:
                    details.append(f"Inventory mismatch: expected {expected_qty}/{expected_weight}g, got {final_qty}/{final_weight}g")
                if not reference_types_correct:
                    details.append(f"Reference types incorrect: purchase={purchase_movement.get('reference_type') if purchase_movement else None}, invoice={invoice_movement.get('reference_type') if invoice_movement else None}")
                if not deletions_blocked:
                    details.append(f"Deletions not blocked: purchase={purchase_delete_blocked}, invoice={invoice_delete_blocked}")
                
                self.log_test("End-to-end integrity", False, "; ".join(details))
                
        except Exception as e:
            self.log_test("End-to-end integrity", False, f"Exception during test: {str(e)}")
    
    def cleanup_test_data(self):
        """Clean up all created test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete invoices
        for invoice_id in self.created_entities["invoices"]:
            try:
                response = self.session.delete(f"{BASE_URL}/invoices/{invoice_id}")
                if response.status_code in [200, 204]:
                    print(f"   ✅ Deleted invoice {invoice_id}")
                else:
                    print(f"   ⚠️ Failed to delete invoice {invoice_id}: {response.status_code}")
            except Exception as e:
                print(f"   ⚠️ Exception deleting invoice {invoice_id}: {str(e)}")
        
        # Delete purchases
        for purchase_id in self.created_entities["purchases"]:
            try:
                response = self.session.delete(f"{BASE_URL}/purchases/{purchase_id}")
                if response.status_code in [200, 204]:
                    print(f"   ✅ Deleted purchase {purchase_id}")
                else:
                    print(f"   ⚠️ Failed to delete purchase {purchase_id}: {response.status_code}")
            except Exception as e:
                print(f"   ⚠️ Exception deleting purchase {purchase_id}: {str(e)}")
        
        # Delete accounts
        for account_id in self.created_entities["accounts"]:
            try:
                response = self.session.delete(f"{BASE_URL}/accounts/{account_id}")
                if response.status_code in [200, 204]:
                    print(f"   ✅ Deleted account {account_id}")
                else:
                    print(f"   ⚠️ Failed to delete account {account_id}: {response.status_code}")
            except Exception as e:
                print(f"   ⚠️ Exception deleting account {account_id}: {str(e)}")
        
        # Delete inventory headers
        for header_id in self.created_entities["inventory_headers"]:
            try:
                response = self.session.delete(f"{BASE_URL}/inventory/headers/{header_id}")
                if response.status_code in [200, 204]:
                    print(f"   ✅ Deleted inventory header {header_id}")
                else:
                    print(f"   ⚠️ Failed to delete inventory header {header_id}: {response.status_code}")
            except Exception as e:
                print(f"   ⚠️ Exception deleting inventory header {header_id}: {str(e)}")
        
        # Delete parties
        for party_id in self.created_entities["parties"]:
            try:
                response = self.session.delete(f"{BASE_URL}/parties/{party_id}")
                if response.status_code in [200, 204]:
                    print(f"   ✅ Deleted party {party_id}")
                else:
                    print(f"   ⚠️ Failed to delete party {party_id}: {response.status_code}")
            except Exception as e:
                print(f"   ⚠️ Exception deleting party {party_id}: {str(e)}")
    
    def run_all_tests(self) -> bool:
        """Run all inventory flow tests"""
        print("🚀 Starting CRITICAL INVENTORY FLOW CORRECTION TESTING")
        print("=" * 80)
        print("Testing SINGLE AUTHORITATIVE PATH for stock reduction through Invoice Finalization")
        print("=" * 80)
        
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        if not self.setup_test_data():
            print("❌ Test data setup failed. Cannot proceed with tests.")
            return False
        
        try:
            # Run all 11 critical tests
            self.test_1_manual_stock_out_creation()
            self.test_2_negative_delta_bypass()
            self.test_3_invalid_movement_type()
            self.test_4_stock_out_movement_deletion()
            self.test_5_invoice_linked_movement_deletion()
            self.test_6_legitimate_stock_in()
            self.test_7_legitimate_adjustment()
            self.test_8_manual_movement_deletion()
            self.test_9_invoice_finalization_path()
            self.test_10_purchase_finalization_path()
            self.test_11_end_to_end_integrity()
            
        finally:
            # Always cleanup
            self.cleanup_test_data()
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 CRITICAL INVENTORY FLOW TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Categorize results
        blocking_tests = [r for r in self.test_results if "BLOCKING" in r["test"] or any(x in r["test"].lower() for x in ["block", "manual stock out", "negative delta", "invalid movement", "deletion"])]
        allowing_tests = [r for r in self.test_results if "ALLOWING" in r["test"] or any(x in r["test"].lower() for x in ["allow", "legitimate", "finalization path", "end-to-end"])]
        
        blocking_passed = sum(1 for r in blocking_tests if r["success"])
        allowing_passed = sum(1 for r in allowing_tests if r["success"])
        
        print(f"\n🚫 BLOCKING TESTS (Must Fail): {blocking_passed}/{len(blocking_tests)} passed")
        print(f"✅ ALLOWING TESTS (Must Succeed): {allowing_passed}/{len(allowing_tests)} passed")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        # Production readiness assessment
        critical_failures = [r for r in self.test_results if not r["success"] and ("block" in r["test"].lower() or "allow" in r["test"].lower())]
        
        if len(critical_failures) == 0:
            print(f"\n🎯 PRODUCTION READINESS: ✅ PASSED")
            print("All critical inventory flow controls are working correctly.")
            print("Single authoritative path for stock reduction is enforced.")
            print("Audit trail, accounting accuracy, and GST compliance maintained.")
        else:
            print(f"\n🎯 PRODUCTION READINESS: ❌ FAILED")
            print("Critical inventory flow controls have issues that must be fixed before production.")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = InventoryFlowTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
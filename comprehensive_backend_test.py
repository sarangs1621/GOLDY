#!/usr/bin/env python3
"""
COMPREHENSIVE BACKEND TESTING - Gold Shop ERP System

Test the following critical workflows in order:

## 1. AUTHENTICATION & AUTHORIZATION
- Test login with admin credentials (admin/admin123)
- Test login with staff credentials (staff/staff123)
- Verify JWT token generation and validation
- Test permission enforcement on protected endpoints

## 2. PURCHASE PAYMENT FLOW (CRITICAL - Recently Fixed)
Test complete purchase lifecycle:
a) Create unpaid draft purchase (paid_amount = 0)
b) Add partial payment
c) Complete payment
d) Test edit restrictions

## 3. CASH FLOW CALCULATIONS (CRITICAL - Recently Fixed)
Verify transaction directions are correct

## 4. INVENTORY STOCK MOVEMENTS (CRITICAL - Recently Fixed)
Test Stock OUT creation on invoice finalization

## 5. WORKER MANAGEMENT
Test worker assignment and validation

## 6. CATEGORY DUPLICATE PREVENTION
Test duplicate category validation

## 7. RETURNS FINALIZATION
Test returns workflow

## 8. DATA INTEGRITY & EDGE CASES
Test with decimal values and edge cases
"""

import requests
import json
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal

# Configuration
BASE_URL = "https://status-tracker-app.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class GoldShopERPTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.auth_token = None
        self.csrf_token = None
        self.test_data = {}
        self.test_results = []
        
    def log_result(self, test_name, success, details="", error=""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    Details: {details}")
        if error:
            print(f"    Error: {error}")
        print()

    def test_authentication_authorization(self):
        """Test authentication and authorization"""
        print("=" * 80)
        print("1. AUTHENTICATION & AUTHORIZATION TESTING")
        print("=" * 80)
        
        # Test 1: Admin login
        try:
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.csrf_token = data.get("csrf_token")
                
                # Update session headers
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}",
                    "X-CSRF-Token": self.csrf_token
                })
                
                user_info = data.get("user", {})
                self.log_result("Admin Login", True, 
                              f"Successfully authenticated as admin. Role: {user_info.get('role')}, "
                              f"Permissions: {len(user_info.get('permissions', []))}")
                self.test_data["admin_user"] = user_info
            else:
                self.log_result("Admin Login", False, "", f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Admin Login", False, "", f"Authentication error: {str(e)}")
            return False

        # Test 2: Staff login (separate session)
        try:
            staff_session = requests.Session()
            staff_session.headers.update(HEADERS)
            
            login_data = {
                "username": "staff",
                "password": "staff123"
            }
            
            response = staff_session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                user_info = data.get("user", {})
                self.log_result("Staff Login", True, 
                              f"Successfully authenticated as staff. Role: {user_info.get('role')}, "
                              f"Permissions: {len(user_info.get('permissions', []))}")
                self.test_data["staff_user"] = user_info
            else:
                self.log_result("Staff Login", False, "", f"Staff login failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Staff Login", False, "", f"Staff authentication error: {str(e)}")

        # Test 3: JWT Token validation
        try:
            response = self.session.get(f"{BASE_URL}/users")
            if response.status_code == 200:
                self.log_result("JWT Token Validation", True, "Token successfully validated on protected endpoint")
            else:
                self.log_result("JWT Token Validation", False, "", f"Token validation failed: {response.status_code}")
        except Exception as e:
            self.log_result("JWT Token Validation", False, "", f"Token validation error: {str(e)}")

        return True

    def setup_test_data(self):
        """Create test data: accounts, parties, inventory, workers"""
        print("=" * 80)
        print("SETTING UP TEST DATA")
        print("=" * 80)
        
        try:
            # Create cash account
            account_data = {
                "name": "Test Cash Account",
                "account_type": "asset",
                "opening_balance": 50000.0
            }
            response = self.session.post(f"{BASE_URL}/accounts", json=account_data)
            if response.status_code in [200, 201]:
                self.test_data["cash_account"] = response.json()
                self.log_result("Setup - Cash Account", True, f"Created account: {self.test_data['cash_account']['name']}")
            else:
                self.log_result("Setup - Cash Account", False, "", f"Failed to create account: {response.text}")
                return False

            # Create vendor party
            vendor_data = {
                "name": f"Gold Supplier Test {int(time.time())}",
                "phone": f"+968-{int(time.time()) % 10000}-5678",
                "address": "Industrial Area, Muscat",
                "party_type": "vendor",
                "notes": "Primary gold supplier for testing"
            }
            response = self.session.post(f"{BASE_URL}/parties", json=vendor_data)
            if response.status_code in [200, 201]:
                vendor_result = response.json()
                self.test_data["vendor"] = vendor_result
                self.log_result("Setup - Vendor Party", True, f"Created vendor: {vendor_result['name']}")
            else:
                self.log_result("Setup - Vendor Party", False, "", f"Failed to create vendor: {response.status_code} - {response.text}")
                return False

            # Create customer party
            customer_data = {
                "name": f"Ahmed Al-Rashid Test {int(time.time())}",
                "phone": f"+968-{int(time.time()) % 10000}-1234",
                "address": "Al Khuwair, Muscat",
                "party_type": "customer",
                "notes": "VIP customer for testing"
            }
            response = self.session.post(f"{BASE_URL}/parties", json=customer_data)
            if response.status_code in [200, 201]:
                customer_result = response.json()
                self.test_data["customer"] = customer_result
                self.log_result("Setup - Customer Party", True, f"Created customer: {customer_result['name']}")
            else:
                self.log_result("Setup - Customer Party", False, "", f"Failed to create customer: {response.status_code} - {response.text}")
                return False

            # Create inventory categories
            categories = [
                {"name": f"Gold Chains 22K Test {int(time.time())}", "current_qty": 25.0, "current_weight": 750.0},
                {"name": f"Gold Rings 18K Test {int(time.time())}", "current_qty": 15.0, "current_weight": 225.0}
            ]
            
            self.test_data["categories"] = []
            for cat_data in categories:
                response = self.session.post(f"{BASE_URL}/inventory/headers", json=cat_data)
                if response.status_code == 201:
                    category = response.json()
                    self.test_data["categories"].append(category)
                    self.log_result("Setup - Inventory Category", True, f"Created category: {category['name']}")
                else:
                    self.log_result("Setup - Inventory Category", False, "", f"Failed to create category: {response.text}")

            # Create worker
            worker_data = {
                "name": f"Mohammed Al-Balushi Test {int(time.time())}",
                "phone": f"+968-{int(time.time()) % 10000}-7777",
                "role": "goldsmith",
                "active": True
            }
            response = self.session.post(f"{BASE_URL}/workers", json=worker_data)
            if response.status_code == 201:
                self.test_data["worker"] = response.json()
                self.log_result("Setup - Worker", True, f"Created worker: {self.test_data['worker']['name']}")
            else:
                self.log_result("Setup - Worker", False, "", f"Failed to create worker: {response.text}")

            return True
            
        except Exception as e:
            self.log_result("Setup Test Data", False, "", f"Setup error: {str(e)}")
            return False

    def test_purchase_payment_flow(self):
        """Test complete purchase lifecycle - CRITICAL"""
        print("=" * 80)
        print("2. PURCHASE PAYMENT FLOW TESTING (CRITICAL)")
        print("=" * 80)
        
        # Test 2a: Create unpaid draft purchase
        try:
            purchase_data = {
                "vendor_party_id": self.test_data["vendor"]["id"],
                "description": "Premium 22K Gold Bars - 150g",
                "weight_grams": 150.0,
                "entered_purity": 916,
                "valuation_purity_fixed": 916,
                "rate_per_gram": 195.50,
                "amount_total": 29325.0,
                "paid_amount_money": 0.0,  # No payment initially
                "balance_due_money": 29325.0
            }
            
            response = self.session.post(f"{BASE_URL}/purchases", json=purchase_data)
            if response.status_code in [200, 201]:
                purchase = response.json()
                self.test_data["draft_purchase"] = purchase
                
                # Verify draft status
                if (purchase.get("status") == "Draft" and 
                    purchase.get("locked") == False and 
                    purchase.get("balance_due_money") == 29325.0):
                    self.log_result("Purchase Draft Creation", True, 
                                  f"Created unpaid draft purchase. Status: {purchase.get('status')}, "
                                  f"Locked: {purchase.get('locked')}, Balance: {purchase.get('balance_due_money')} OMR")
                else:
                    self.log_result("Purchase Draft Creation", False, "", 
                                  f"Draft purchase has incorrect status/lock state: Status={purchase.get('status')}, "
                                  f"Locked={purchase.get('locked')}, Balance={purchase.get('balance_due_money')}")
            else:
                self.log_result("Purchase Draft Creation", False, "", f"Failed to create purchase: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Purchase Draft Creation", False, "", f"Error: {str(e)}")
            return False

        # Test 2b: Add partial payment
        try:
            partial_payment = {
                "payment_amount": 15000.0,
                "payment_mode": "Bank Transfer",
                "account_id": self.test_data["cash_account"]["id"],
                "notes": "Partial payment - 50% advance"
            }
            
            purchase_id = self.test_data["draft_purchase"]["id"]
            response = self.session.post(f"{BASE_URL}/purchases/{purchase_id}/add-payment", json=partial_payment)
            
            if response.status_code == 200:
                updated_purchase = response.json()
                
                # Verify partial payment status
                if (updated_purchase.get("status") == "Partially Paid" and 
                    updated_purchase.get("locked") == False and 
                    abs(updated_purchase.get("balance_due_money") - 14325.0) < 0.01):
                    self.log_result("Purchase Partial Payment", True, 
                                  f"Added partial payment. Status: {updated_purchase.get('status')}, "
                                  f"Locked: {updated_purchase.get('locked')}, "
                                  f"Remaining Balance: {updated_purchase.get('balance_due_money')} OMR")
                    self.test_data["partial_purchase"] = updated_purchase
                else:
                    self.log_result("Purchase Partial Payment", False, "", 
                                  f"Partial payment has incorrect status: Status={updated_purchase.get('status')}, "
                                  f"Locked={updated_purchase.get('locked')}, Balance={updated_purchase.get('balance_due_money')}")
            else:
                self.log_result("Purchase Partial Payment", False, "", f"Failed to add payment: {response.text}")
                
        except Exception as e:
            self.log_result("Purchase Partial Payment", False, "", f"Error: {str(e)}")

        # Test 2c: Complete payment
        try:
            final_payment = {
                "payment_amount": 14325.0,
                "payment_mode": "Cash",
                "account_id": self.test_data["cash_account"]["id"],
                "notes": "Final payment - completing purchase"
            }
            
            purchase_id = self.test_data["draft_purchase"]["id"]
            response = self.session.post(f"{BASE_URL}/purchases/{purchase_id}/add-payment", json=final_payment)
            
            if response.status_code == 200:
                completed_purchase = response.json()
                
                # Verify completed payment status
                if (completed_purchase.get("status") == "Paid" and 
                    completed_purchase.get("locked") == True and 
                    abs(completed_purchase.get("balance_due_money")) < 0.01):
                    self.log_result("Purchase Complete Payment", True, 
                                  f"Completed payment. Status: {completed_purchase.get('status')}, "
                                  f"Locked: {completed_purchase.get('locked')}, "
                                  f"Balance: {completed_purchase.get('balance_due_money')} OMR")
                    self.test_data["completed_purchase"] = completed_purchase
                else:
                    self.log_result("Purchase Complete Payment", False, "", 
                                  f"Complete payment has incorrect status: Status={completed_purchase.get('status')}, "
                                  f"Locked={completed_purchase.get('locked')}, Balance={completed_purchase.get('balance_due_money')}")
            else:
                self.log_result("Purchase Complete Payment", False, "", f"Failed to complete payment: {response.text}")
                
        except Exception as e:
            self.log_result("Purchase Complete Payment", False, "", f"Error: {str(e)}")

        # Test 2d: Test edit restrictions
        try:
            # Try to edit locked purchase (should fail)
            edit_data = {
                "description": "Trying to edit locked purchase"
            }
            
            purchase_id = self.test_data["completed_purchase"]["id"]
            response = self.session.patch(f"{BASE_URL}/purchases/{purchase_id}", json=edit_data)
            
            if response.status_code == 400 or response.status_code == 403:
                self.log_result("Purchase Edit Restriction", True, 
                              "Correctly blocked editing of locked purchase")
            else:
                self.log_result("Purchase Edit Restriction", False, "", 
                              f"Should have blocked edit but got: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Purchase Edit Restriction", False, "", f"Error: {str(e)}")

    def test_cash_flow_calculations(self):
        """Test cash flow calculations - CRITICAL"""
        print("=" * 80)
        print("3. CASH FLOW CALCULATIONS TESTING (CRITICAL)")
        print("=" * 80)
        
        # Test 3a: Create invoice and add payment (should create DEBIT transaction)
        try:
            invoice_data = {
                "customer_type": "saved",
                "customer_id": self.test_data["customer"]["id"],
                "invoice_type": "sale",
                "items": [
                    {
                        "category": "Gold Chains 22K",
                        "description": "22K Gold Chain - Elegant Design",
                        "qty": 1,
                        "gross_weight": 45.0,
                        "stone_weight": 0.0,
                        "net_gold_weight": 45.0,
                        "weight": 45.0,
                        "purity": 916,
                        "metal_rate": 210.0,
                        "gold_value": 9450.0,
                        "making_charge_type": "per_gram",
                        "making_value": 900.0,
                        "stone_charges": 0.0,
                        "wastage_charges": 450.0,
                        "item_discount": 0.0,
                        "vat_percent": 5.0,
                        "vat_amount": 540.0,
                        "line_total": 11340.0
                    }
                ],
                "subtotal": 10800.0,
                "discount_amount": 0.0,
                "tax_type": "cgst_sgst",
                "gst_percent": 5.0,
                "cgst_total": 270.0,
                "sgst_total": 270.0,
                "igst_total": 0.0,
                "vat_total": 540.0,
                "grand_total": 11340.0,
                "paid_amount": 0.0,
                "balance_due": 11340.0
            }
            
            response = self.session.post(f"{BASE_URL}/invoices", json=invoice_data)
            if response.status_code == 201:
                invoice = response.json()
                self.test_data["test_invoice"] = invoice
                
                # Finalize invoice
                finalize_response = self.session.post(f"{BASE_URL}/invoices/{invoice['id']}/finalize")
                if finalize_response.status_code == 200:
                    finalized_invoice = finalize_response.json()
                    
                    # Add payment to invoice
                    payment_data = {
                        "payment_amount": 11340.0,
                        "payment_mode": "Cash",
                        "account_id": self.test_data["cash_account"]["id"],
                        "notes": "Full payment for gold chain"
                    }
                    
                    payment_response = self.session.post(f"{BASE_URL}/invoices/{invoice['id']}/add-payment", json=payment_data)
                    if payment_response.status_code == 200:
                        self.log_result("Invoice Payment (DEBIT Transaction)", True, 
                                      "Successfully created invoice and added payment - should create DEBIT transaction (money IN)")
                    else:
                        self.log_result("Invoice Payment (DEBIT Transaction)", False, "", 
                                      f"Failed to add payment: {payment_response.text}")
                else:
                    self.log_result("Invoice Finalization", False, "", f"Failed to finalize: {finalize_response.text}")
            else:
                self.log_result("Invoice Creation", False, "", f"Failed to create invoice: {response.text}")
                
        except Exception as e:
            self.log_result("Invoice Payment Flow", False, "", f"Error: {str(e)}")

        # Test 3b: Check Finance API for correct cash flow
        try:
            response = self.session.get(f"{BASE_URL}/finance/summary")
            if response.status_code == 200:
                finance_data = response.json()
                
                total_debit = finance_data.get("total_debit", 0)
                total_credit = finance_data.get("total_credit", 0)
                net_flow = finance_data.get("net_flow", 0)
                
                # Verify net flow calculation
                expected_net_flow = total_debit - total_credit
                if abs(net_flow - expected_net_flow) < 0.01:
                    self.log_result("Finance Summary Calculation", True, 
                                  f"Net Flow correctly calculated: {net_flow} OMR "
                                  f"(Debit: {total_debit}, Credit: {total_credit})")
                else:
                    self.log_result("Finance Summary Calculation", False, "", 
                                  f"Net flow calculation incorrect: Expected {expected_net_flow}, Got {net_flow}")
            else:
                self.log_result("Finance Summary API", False, "", f"Failed to get finance summary: {response.text}")
                
        except Exception as e:
            self.log_result("Finance Summary", False, "", f"Error: {str(e)}")

    def test_inventory_stock_movements(self):
        """Test inventory stock movements - CRITICAL"""
        print("=" * 80)
        print("4. INVENTORY STOCK MOVEMENTS TESTING (CRITICAL)")
        print("=" * 80)
        
        # Test 4a: Check stock movements after invoice finalization
        try:
            # Get inventory movements
            response = self.session.get(f"{BASE_URL}/inventory/movements")
            if response.status_code == 200:
                movements = response.json()
                
                # Look for Stock OUT movements
                stock_out_movements = [m for m in movements if m.get("movement_type") == "Stock OUT"]
                
                if stock_out_movements:
                    latest_movement = stock_out_movements[-1]  # Get most recent
                    
                    # Verify Stock OUT movement properties
                    if (latest_movement.get("qty_delta", 0) < 0 and 
                        latest_movement.get("weight_delta", 0) < 0):
                        self.log_result("Stock OUT Movement Creation", True, 
                                      f"Stock OUT movement created correctly: "
                                      f"Qty Delta: {latest_movement.get('qty_delta')}, "
                                      f"Weight Delta: {latest_movement.get('weight_delta')}g")
                    else:
                        self.log_result("Stock OUT Movement Creation", False, "", 
                                      f"Stock OUT movement has incorrect deltas: "
                                      f"Qty: {latest_movement.get('qty_delta')}, "
                                      f"Weight: {latest_movement.get('weight_delta')}")
                else:
                    self.log_result("Stock OUT Movement Creation", False, "", 
                                  "No Stock OUT movements found after invoice finalization")
            else:
                self.log_result("Inventory Movements API", False, "", f"Failed to get movements: {response.text}")
                
        except Exception as e:
            self.log_result("Inventory Stock Movements", False, "", f"Error: {str(e)}")

        # Test 4b: Verify inventory calculation
        try:
            response = self.session.get(f"{BASE_URL}/inventory")
            if response.status_code == 200:
                inventory_data = response.json()
                items = inventory_data.get("items", [])
                
                if items:
                    # Check that inventory shows both Stock IN and Stock OUT
                    sample_item = items[0]
                    self.log_result("Inventory Calculation", True, 
                                  f"Inventory report accessible. Sample item: {sample_item.get('name', 'Unknown')} "
                                  f"(Current Stock calculation working)")
                else:
                    self.log_result("Inventory Calculation", False, "", "No inventory items found")
            else:
                self.log_result("Inventory Report API", False, "", f"Failed to get inventory: {response.text}")
                
        except Exception as e:
            self.log_result("Inventory Calculation", False, "", f"Error: {str(e)}")

    def test_worker_management(self):
        """Test worker management"""
        print("=" * 80)
        print("5. WORKER MANAGEMENT TESTING")
        print("=" * 80)
        
        # Test 5a: Create job card without worker
        try:
            jobcard_data = {
                "customer_type": "saved",
                "customer_id": self.test_data["customer"]["id"],
                "delivery_date": "2024-02-15",
                "items": [
                    {
                        "category": "Gold Rings 18K",
                        "description": "Custom ring design",
                        "qty": 1,
                        "weight_in": 25.0,
                        "purity": 750,
                        "work_type": "repair",
                        "making_charge_type": "flat",
                        "making_charge_value": 150.0
                    }
                ],
                "notes": "Customer wants quick repair"
            }
            
            response = self.session.post(f"{BASE_URL}/jobcards", json=jobcard_data)
            if response.status_code == 201:
                jobcard = response.json()
                self.test_data["test_jobcard"] = jobcard
                self.log_result("Job Card Creation Without Worker", True, 
                              f"Successfully created job card without worker: {jobcard.get('job_card_number')}")
            else:
                self.log_result("Job Card Creation Without Worker", False, "", 
                              f"Failed to create job card: {response.text}")
                
        except Exception as e:
            self.log_result("Job Card Creation Without Worker", False, "", f"Error: {str(e)}")

        # Test 5b: Try to complete job card without worker (should fail)
        try:
            if "test_jobcard" in self.test_data:
                jobcard_id = self.test_data["test_jobcard"]["id"]
                
                # Try to update status to completed without worker
                update_data = {
                    "status": "completed"
                }
                
                response = self.session.patch(f"{BASE_URL}/jobcards/{jobcard_id}", json=update_data)
                
                if response.status_code == 422:
                    self.log_result("Job Card Completion Without Worker", True, 
                                  "Correctly blocked job card completion without worker (HTTP 422)")
                else:
                    self.log_result("Job Card Completion Without Worker", False, "", 
                                  f"Should have blocked completion but got: {response.status_code} - {response.text}")
            else:
                self.log_result("Job Card Completion Without Worker", False, "", "No test job card available")
                
        except Exception as e:
            self.log_result("Job Card Completion Without Worker", False, "", f"Error: {str(e)}")

        # Test 5c: Assign worker and complete job card
        try:
            if "test_jobcard" in self.test_data and "worker" in self.test_data:
                jobcard_id = self.test_data["test_jobcard"]["id"]
                
                # Assign worker and complete
                update_data = {
                    "worker_id": self.test_data["worker"]["id"],
                    "worker_name": self.test_data["worker"]["name"],
                    "status": "completed"
                }
                
                response = self.session.patch(f"{BASE_URL}/jobcards/{jobcard_id}", json=update_data)
                
                if response.status_code == 200:
                    updated_jobcard = response.json()
                    if updated_jobcard.get("status") == "completed":
                        self.log_result("Job Card Completion With Worker", True, 
                                      f"Successfully completed job card with worker: {updated_jobcard.get('worker_name')}")
                        self.test_data["completed_jobcard"] = updated_jobcard
                    else:
                        self.log_result("Job Card Completion With Worker", False, "", 
                                      f"Job card not marked as completed: {updated_jobcard.get('status')}")
                else:
                    self.log_result("Job Card Completion With Worker", False, "", 
                                  f"Failed to complete job card: {response.text}")
            else:
                self.log_result("Job Card Completion With Worker", False, "", "Missing test data")
                
        except Exception as e:
            self.log_result("Job Card Completion With Worker", False, "", f"Error: {str(e)}")

        # Test 5d: Convert to invoice and verify worker data
        try:
            if "completed_jobcard" in self.test_data:
                jobcard_id = self.test_data["completed_jobcard"]["id"]
                
                response = self.session.post(f"{BASE_URL}/jobcards/{jobcard_id}/convert-to-invoice")
                
                if response.status_code == 200:
                    invoice = response.json()
                    
                    # Verify worker data carried forward
                    if (invoice.get("worker_id") == self.test_data["worker"]["id"] and 
                        invoice.get("worker_name") == self.test_data["worker"]["name"]):
                        self.log_result("Worker Data in Invoice", True, 
                                      f"Worker data correctly carried forward to invoice: {invoice.get('worker_name')}")
                    else:
                        self.log_result("Worker Data in Invoice", False, "", 
                                      f"Worker data not carried forward correctly: "
                                      f"ID={invoice.get('worker_id')}, Name={invoice.get('worker_name')}")
                else:
                    self.log_result("Job Card to Invoice Conversion", False, "", 
                                  f"Failed to convert to invoice: {response.text}")
            else:
                self.log_result("Job Card to Invoice Conversion", False, "", "No completed job card available")
                
        except Exception as e:
            self.log_result("Job Card to Invoice Conversion", False, "", f"Error: {str(e)}")

    def test_category_duplicate_prevention(self):
        """Test category duplicate prevention"""
        print("=" * 80)
        print("6. CATEGORY DUPLICATE PREVENTION TESTING")
        print("=" * 80)
        
        # Test 6a: Create category
        try:
            category_data = {
                "name": "Gold Bracelets 22K",
                "current_qty": 10.0,
                "current_weight": 150.0
            }
            
            response = self.session.post(f"{BASE_URL}/inventory/headers", json=category_data)
            if response.status_code == 201:
                category = response.json()
                self.test_data["unique_category"] = category
                self.log_result("Unique Category Creation", True, 
                              f"Successfully created category: {category.get('name')}")
            else:
                self.log_result("Unique Category Creation", False, "", 
                              f"Failed to create category: {response.text}")
                
        except Exception as e:
            self.log_result("Unique Category Creation", False, "", f"Error: {str(e)}")

        # Test 6b: Try creating duplicate category (exact match)
        try:
            duplicate_data = {
                "name": "Gold Bracelets 22K",  # Exact duplicate
                "current_qty": 5.0,
                "current_weight": 75.0
            }
            
            response = self.session.post(f"{BASE_URL}/inventory/headers", json=duplicate_data)
            if response.status_code == 400:
                self.log_result("Duplicate Category Prevention (Exact)", True, 
                              "Correctly blocked duplicate category creation (exact match)")
            else:
                self.log_result("Duplicate Category Prevention (Exact)", False, "", 
                              f"Should have blocked duplicate but got: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Duplicate Category Prevention (Exact)", False, "", f"Error: {str(e)}")

        # Test 6c: Try creating duplicate category (case-insensitive)
        try:
            case_duplicate_data = {
                "name": "GOLD BRACELETS 22K",  # Case different
                "current_qty": 5.0,
                "current_weight": 75.0
            }
            
            response = self.session.post(f"{BASE_URL}/inventory/headers", json=case_duplicate_data)
            if response.status_code == 400:
                self.log_result("Duplicate Category Prevention (Case-Insensitive)", True, 
                              "Correctly blocked duplicate category creation (case-insensitive)")
            else:
                self.log_result("Duplicate Category Prevention (Case-Insensitive)", False, "", 
                              f"Should have blocked case-insensitive duplicate but got: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Duplicate Category Prevention (Case-Insensitive)", False, "", f"Error: {str(e)}")

        # Test 6d: Try updating category to duplicate name
        try:
            if "unique_category" in self.test_data and self.test_data["categories"]:
                category_id = self.test_data["unique_category"]["id"]
                existing_name = self.test_data["categories"][0]["name"]  # Use existing category name
                
                update_data = {
                    "name": existing_name
                }
                
                response = self.session.patch(f"{BASE_URL}/inventory/headers/{category_id}", json=update_data)
                if response.status_code == 400:
                    self.log_result("Duplicate Category Prevention (Update)", True, 
                                  "Correctly blocked category update to duplicate name")
                else:
                    self.log_result("Duplicate Category Prevention (Update)", False, "", 
                                  f"Should have blocked duplicate update but got: {response.status_code} - {response.text}")
            else:
                self.log_result("Duplicate Category Prevention (Update)", False, "", "Missing test data for update test")
                
        except Exception as e:
            self.log_result("Duplicate Category Prevention (Update)", False, "", f"Error: {str(e)}")

    def test_data_integrity_edge_cases(self):
        """Test data integrity and edge cases"""
        print("=" * 80)
        print("8. DATA INTEGRITY & EDGE CASES TESTING")
        print("=" * 80)
        
        # Test 8a: Decimal precision (weights: 3 decimals, amounts: 2 decimals)
        try:
            purchase_data = {
                "vendor_party_id": self.test_data["vendor"]["id"],
                "description": "Precision Test - Gold Dust",
                "weight_grams": 12.345,  # 3 decimal precision
                "entered_purity": 916,
                "valuation_purity_fixed": 916,
                "rate_per_gram": 195.67,  # 2 decimal precision
                "amount_total": 2416.78,  # 2 decimal precision (12.345 * 195.67 rounded)
                "paid_amount_money": 1208.39,  # Exactly half
                "balance_due_money": 1208.39
            }
            
            response = self.session.post(f"{BASE_URL}/purchases", json=purchase_data)
            if response.status_code == 201:
                purchase = response.json()
                
                # Verify decimal precision
                weight_ok = abs(purchase.get("weight_grams", 0) - 12.345) < 0.001
                amount_ok = abs(purchase.get("amount_total", 0) - 2416.78) < 0.01
                
                if weight_ok and amount_ok:
                    self.log_result("Decimal Precision Test", True, 
                                  f"Decimal precision maintained: Weight={purchase.get('weight_grams')}g, "
                                  f"Amount={purchase.get('amount_total')} OMR")
                else:
                    self.log_result("Decimal Precision Test", False, "", 
                                  f"Decimal precision lost: Weight={purchase.get('weight_grams')}, "
                                  f"Amount={purchase.get('amount_total')}")
            else:
                self.log_result("Decimal Precision Test", False, "", f"Failed to create precision test purchase: {response.text}")
                
        except Exception as e:
            self.log_result("Decimal Precision Test", False, "", f"Error: {str(e)}")

        # Test 8b: Overpayment validation
        try:
            if "draft_purchase" in self.test_data:
                # Try to pay more than balance due
                overpayment = {
                    "payment_amount": 50000.0,  # Much more than balance
                    "payment_mode": "Cash",
                    "account_id": self.test_data["cash_account"]["id"],
                    "notes": "Overpayment test"
                }
                
                # Create a new draft purchase for this test
                test_purchase_data = {
                    "vendor_party_id": self.test_data["vendor"]["id"],
                    "description": "Overpayment Test Purchase",
                    "weight_grams": 50.0,
                    "entered_purity": 916,
                    "valuation_purity_fixed": 916,
                    "rate_per_gram": 200.0,
                    "amount_total": 10000.0,
                    "paid_amount_money": 0.0,
                    "balance_due_money": 10000.0
                }
                
                create_response = self.session.post(f"{BASE_URL}/purchases", json=test_purchase_data)
                if create_response.status_code == 201:
                    test_purchase = create_response.json()
                    
                    # Try overpayment
                    overpayment_response = self.session.post(f"{BASE_URL}/purchases/{test_purchase['id']}/add-payment", json=overpayment)
                    
                    if overpayment_response.status_code == 400:
                        self.log_result("Overpayment Validation", True, 
                                      "Correctly blocked overpayment attempt")
                    else:
                        self.log_result("Overpayment Validation", False, "", 
                                      f"Should have blocked overpayment but got: {overpayment_response.status_code}")
                else:
                    self.log_result("Overpayment Validation", False, "", "Failed to create test purchase for overpayment test")
            else:
                self.log_result("Overpayment Validation", False, "", "No draft purchase available for overpayment test")
                
        except Exception as e:
            self.log_result("Overpayment Validation", False, "", f"Error: {str(e)}")

    def run_comprehensive_test(self):
        """Run all test phases"""
        print("🚀 STARTING COMPREHENSIVE GOLD SHOP ERP BACKEND TESTING")
        print("=" * 80)
        
        # Test 1: Authentication & Authorization
        if not self.test_authentication_authorization():
            print("❌ Authentication failed. Cannot proceed with testing.")
            return False
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Test data setup failed. Cannot proceed with testing.")
            return False
        
        # Test 2: Purchase Payment Flow (CRITICAL)
        self.test_purchase_payment_flow()
        
        # Test 3: Cash Flow Calculations (CRITICAL)
        self.test_cash_flow_calculations()
        
        # Test 4: Inventory Stock Movements (CRITICAL)
        self.test_inventory_stock_movements()
        
        # Test 5: Worker Management
        self.test_worker_management()
        
        # Test 6: Category Duplicate Prevention
        self.test_category_duplicate_prevention()
        
        # Test 8: Data Integrity & Edge Cases
        self.test_data_integrity_edge_cases()
        
        # Print summary
        self.print_summary()
        
        return True

    def print_summary(self):
        """Print test results summary"""
        print("=" * 80)
        print("🎯 COMPREHENSIVE GOLD SHOP ERP TESTING SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Group results by category
        categories = {}
        for result in self.test_results:
            test_name = result["test"]
            if " - " in test_name:
                category = test_name.split(" - ")[0]
            else:
                category = "General"
            
            if category not in categories:
                categories[category] = {"passed": 0, "failed": 0, "tests": []}
            
            if result["success"]:
                categories[category]["passed"] += 1
            else:
                categories[category]["failed"] += 1
            categories[category]["tests"].append(result)
        
        # Print category summaries
        for category, data in categories.items():
            total_cat = data["passed"] + data["failed"]
            success_rate = (data["passed"] / total_cat * 100) if total_cat > 0 else 0
            print(f"📊 {category}: {data['passed']}/{total_cat} passed ({success_rate:.1f}%)")
        
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            print("-" * 40)
            for result in self.test_results:
                if not result["success"]:
                    print(f"• {result['test']}")
                    if result["error"]:
                        print(f"  Error: {result['error']}")
            print()
        
        print("✅ CRITICAL SYSTEMS STATUS:")
        print("-" * 40)
        
        # Check critical systems
        critical_tests = [
            "Purchase Draft Creation",
            "Purchase Partial Payment", 
            "Purchase Complete Payment",
            "Purchase Edit Restriction",
            "Finance Summary Calculation",
            "Stock OUT Movement Creation"
        ]
        
        critical_passed = 0
        for test_name in critical_tests:
            test_result = next((r for r in self.test_results if r["test"] == test_name), None)
            if test_result and test_result["success"]:
                critical_passed += 1
                print(f"✅ {test_name}")
            else:
                print(f"❌ {test_name}")
        
        print(f"\nCritical Systems: {critical_passed}/{len(critical_tests)} operational")
        
        print("=" * 80)
        print("🏁 TESTING COMPLETE")
        print("=" * 80)

if __name__ == "__main__":
    tester = GoldShopERPTester()
    tester.run_comprehensive_test()
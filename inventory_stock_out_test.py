#!/usr/bin/env python3
"""
CRITICAL INVENTORY FIX TESTING - Stock OUT Movement Creation on Invoice Finalization

CONTEXT:
Fixed a critical bug where Stock OUT movements were NOT being created when invoices were finalized. 
This caused inventory reports to only show Stock IN (from purchases) and never Stock OUT (from sales), 
making inventory totals incorrect.

FIX IMPLEMENTED:
Restructured invoice finalization logic (backend/server.py lines 4782-4834) to ALWAYS create Stock OUT 
movements for every invoice item with weight > 0, regardless of whether a matching inventory header exists.

TESTING REQUIREMENTS:

TEST SCENARIO 1: Full Invoice Flow with Matching Inventory
1. Create a vendor (POST /api/parties)
2. Create a purchase (POST /api/purchases) with category "Gold Ring", weight 10.5g, purity 22
3. Finalize purchase (POST /api/purchases/{id}/finalize) - should create Stock IN movement
4. Verify Stock IN movement exists (GET /api/stock-movements) - should have movement_type="Stock IN", qty_delta=1, weight_delta=10.5
5. Create a customer (POST /api/parties with party_type="customer")
6. Create an invoice (POST /api/invoices) with one item: category="Gold Ring", weight=5.0g, qty=1, purity=22
7. Finalize invoice (POST /api/invoices/{id}/finalize)
8. VERIFY Stock OUT movement created (GET /api/stock-movements) - MUST have:
   - movement_type="Stock OUT"
   - qty_delta=-1 (negative!)
   - weight_delta=-5.0 (negative!)
   - reference_type="invoice"
   - reference_id={invoice_id}
9. VERIFY inventory header reduced: current_qty should be 0 (1 - 1), current_weight should be 5.5g (10.5 - 5.0)
10. VERIFY inventory report (GET /api/reports/inventory) shows:
    - total_in: 1 qty, 10.5g weight
    - total_out: 1 qty, 5.0g weight
    - net_quantity: 0 (1 - 1)
    - net_weight: 5.5g (10.5 - 5.0)

TEST SCENARIO 2: Invoice with Non-Existent Category (Edge Case)
1. Create another invoice with item category="Non-Existent Category", weight=3.0g, qty=1
2. Finalize this invoice (POST /api/invoices/{id}/finalize)
3. VERIFY Stock OUT movement STILL created even though no matching inventory header:
   - movement_type="Stock OUT"
   - header_name="Non-Existent Category"
   - header_id=null (or None)
   - qty_delta=-1, weight_delta=-3.0
   - reference_type="invoice", reference_id={invoice_id}
4. This ensures complete audit trail even for items without inventory headers

TEST SCENARIO 3: Invoice with No Category (Edge Case)
1. Create invoice with item where category=null/empty but description="Custom Gold Item", weight=2.5g
2. Finalize invoice
3. VERIFY Stock OUT movement created with:
   - header_name="Custom Gold Item" (or "Uncategorized" if description also empty)
   - qty_delta=-1, weight_delta=-2.5

CRITICAL VALIDATION POINTS:
✅ Stock OUT movements MUST be created for ALL invoice items with weight > 0
✅ qty_delta and weight_delta MUST be negative
✅ movement_type MUST be "Stock OUT"
✅ reference_type MUST be "invoice" with correct reference_id
✅ Inventory report totals MUST calculate: Current Stock = SUM(Stock IN) - SUM(Stock OUT)
✅ Stock OUT movements created even if no matching inventory header

AUTH CREDENTIALS:
Use existing test user credentials: username="admin", password="admin123"
"""

import requests
import json
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal

# Configuration - Use the external URL from frontend/.env
BASE_URL = "https://complete-search-fix.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class InventoryStockOutTester:
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

    def authenticate(self):
        """Authenticate with admin user"""
        try:
            # Login with admin credentials
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
                
                self.log_result("Authentication", True, "Successfully authenticated as admin")
                return True
            else:
                self.log_result("Authentication", False, "", f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, "", f"Authentication error: {str(e)}")
            return False

    def test_scenario_1_full_invoice_flow(self):
        """TEST SCENARIO 1: Full Invoice Flow with Matching Inventory"""
        print("=" * 80)
        print("TEST SCENARIO 1: Full Invoice Flow with Matching Inventory")
        print("=" * 80)
        
        try:
            # Step 1: Create a vendor
            timestamp = int(time.time())
            vendor_data = {
                "name": f"Test Gold Vendor {timestamp}",
                "phone": f"+968-{timestamp % 10000}-{(timestamp // 10000) % 10000}",
                "address": "Gold Souk, Muscat",
                "party_type": "vendor",
                "notes": "Test vendor for inventory testing"
            }
            
            response = self.session.post(f"{BASE_URL}/parties", json=vendor_data)
            if response.status_code in [200, 201]:
                vendor = response.json()
                self.test_data["vendor"] = vendor
                self.log_result("Step 1 - Create Vendor", True, f"Created vendor: {vendor['name']}")
            else:
                self.log_result("Step 1 - Create Vendor", False, "", f"Failed to create vendor: {response.status_code} - {response.text}")
                return False

            # Step 2: Create a purchase with category "Gold Ring"
            purchase_data = {
                "vendor_party_id": vendor["id"],
                "description": "Gold Ring Purchase - 10.5g at 22K purity",
                "weight_grams": 10.5,
                "entered_purity": 22,
                "valuation_purity_fixed": 916,
                "rate_per_gram": 200.0,
                "amount_total": 2100.0,
                "paid_amount_money": 0.0,
                "balance_due_money": 2100.0
            }
            
            response = self.session.post(f"{BASE_URL}/purchases", json=purchase_data)
            if response.status_code in [200, 201]:
                purchase = response.json()
                self.test_data["purchase"] = purchase
                self.log_result("Step 2 - Create Purchase", True, 
                              f"Created purchase: {purchase['weight_grams']}g at {purchase['rate_per_gram']} OMR/g")
            else:
                self.log_result("Step 2 - Create Purchase", False, "", f"Failed to create purchase: {response.status_code} - {response.text}")
                return False

            # Step 3: Finalize purchase (should create Stock IN movement)
            response = self.session.post(f"{BASE_URL}/purchases/{purchase['id']}/finalize")
            if response.status_code == 200:
                finalized_purchase = response.json()
                self.test_data["finalized_purchase"] = finalized_purchase
                self.log_result("Step 3 - Finalize Purchase", True, 
                              f"Finalized purchase - should create Stock IN movement")
            else:
                self.log_result("Step 3 - Finalize Purchase", False, "", f"Failed to finalize purchase: {response.status_code} - {response.text}")
                return False

            # Step 4: Verify Stock IN movement exists
            response = self.session.get(f"{BASE_URL}/stock-movements")
            if response.status_code == 200:
                movements_data = response.json()
                movements = movements_data.get('items', []) if isinstance(movements_data, dict) else movements_data
                
                stock_in_movements = [m for m in movements if m.get('movement_type') == 'Stock IN' 
                                    and m.get('reference_type') == 'purchase' 
                                    and m.get('reference_id') == purchase['id']]
                
                if stock_in_movements:
                    stock_in = stock_in_movements[0]
                    expected_qty = 1
                    expected_weight = 10.5
                    
                    if (stock_in.get('qty_delta') == expected_qty and 
                        abs(stock_in.get('weight_delta', 0) - expected_weight) < 0.001):
                        self.log_result("Step 4 - Verify Stock IN Movement", True, 
                                      f"Stock IN movement found: qty_delta={stock_in.get('qty_delta')}, "
                                      f"weight_delta={stock_in.get('weight_delta')}")
                        self.test_data["stock_in_movement"] = stock_in
                    else:
                        self.log_result("Step 4 - Verify Stock IN Movement", False, "", 
                                      f"Stock IN movement has incorrect values: qty_delta={stock_in.get('qty_delta')}, "
                                      f"weight_delta={stock_in.get('weight_delta')}")
                        return False
                else:
                    self.log_result("Step 4 - Verify Stock IN Movement", False, "", 
                                  "No Stock IN movement found for purchase")
                    return False
            else:
                self.log_result("Step 4 - Verify Stock IN Movement", False, "", 
                              f"Failed to get stock movements: {response.status_code} - {response.text}")
                return False

            # Step 5: Create a customer
            timestamp = int(time.time())
            customer_data = {
                "name": f"Test Gold Customer {timestamp}",
                "phone": f"+968-{(timestamp + 1000) % 10000}-{((timestamp + 1000) // 10000) % 10000}",
                "address": "Ruwi, Muscat",
                "party_type": "customer",
                "notes": "Test customer for inventory testing"
            }
            
            response = self.session.post(f"{BASE_URL}/parties", json=customer_data)
            if response.status_code in [200, 201]:
                customer = response.json()
                self.test_data["customer"] = customer
                self.log_result("Step 5 - Create Customer", True, f"Created customer: {customer['name']}")
            else:
                self.log_result("Step 5 - Create Customer", False, "", f"Failed to create customer: {response.status_code} - {response.text}")
                return False

            # Step 6: Create an invoice with Gold Ring category
            invoice_data = {
                "customer_type": "saved",
                "customer_id": customer["id"],
                "invoice_type": "sale",
                "items": [
                    {
                        "category": "Gold Ring",  # This should match the inventory category
                        "description": "22K Gold Ring - 5.0g",
                        "qty": 1,
                        "gross_weight": 5.0,
                        "stone_weight": 0.0,
                        "net_gold_weight": 5.0,
                        "weight": 5.0,
                        "purity": 22,
                        "metal_rate": 200.0,
                        "gold_value": 1000.0,
                        "making_charge_type": "flat",
                        "making_value": 200.0,
                        "stone_charges": 0.0,
                        "wastage_charges": 50.0,
                        "item_discount": 0.0,
                        "vat_percent": 5.0,
                        "vat_amount": 62.5,
                        "line_total": 1312.5
                    }
                ],
                "subtotal": 1250.0,
                "discount_amount": 0.0,
                "tax_type": "cgst_sgst",
                "gst_percent": 5.0,
                "cgst_total": 31.25,
                "sgst_total": 31.25,
                "igst_total": 0.0,
                "vat_total": 62.5,
                "grand_total": 1312.5,
                "paid_amount": 0.0,
                "balance_due": 1312.5
            }
            
            response = self.session.post(f"{BASE_URL}/invoices", json=invoice_data)
            if response.status_code == 201:
                invoice = response.json()
                self.test_data["invoice"] = invoice
                self.log_result("Step 6 - Create Invoice", True, 
                              f"Created invoice: {invoice['invoice_number']} with Gold Ring item (5.0g)")
            else:
                self.log_result("Step 6 - Create Invoice", False, "", f"Failed to create invoice: {response.text}")
                return False

            # Step 7: Finalize invoice (CRITICAL - should create Stock OUT movement)
            response = self.session.post(f"{BASE_URL}/invoices/{invoice['id']}/finalize")
            if response.status_code == 200:
                finalized_invoice = response.json()
                self.test_data["finalized_invoice"] = finalized_invoice
                self.log_result("Step 7 - Finalize Invoice", True, 
                              f"Finalized invoice - should create Stock OUT movement")
            else:
                self.log_result("Step 7 - Finalize Invoice", False, "", f"Failed to finalize invoice: {response.text}")
                return False

            # Step 8: VERIFY Stock OUT movement created (CRITICAL TEST)
            response = self.session.get(f"{BASE_URL}/stock-movements")
            if response.status_code == 200:
                movements_data = response.json()
                movements = movements_data.get('items', []) if isinstance(movements_data, dict) else movements_data
                
                stock_out_movements = [m for m in movements if m.get('movement_type') == 'Stock OUT' 
                                     and m.get('reference_type') == 'invoice' 
                                     and m.get('reference_id') == invoice['id']]
                
                if stock_out_movements:
                    stock_out = stock_out_movements[0]
                    expected_qty = -1  # MUST be negative
                    expected_weight = -5.0  # MUST be negative
                    
                    qty_ok = stock_out.get('qty_delta') == expected_qty
                    weight_ok = abs(stock_out.get('weight_delta', 0) - expected_weight) < 0.001
                    ref_type_ok = stock_out.get('reference_type') == 'invoice'
                    ref_id_ok = stock_out.get('reference_id') == invoice['id']
                    
                    if qty_ok and weight_ok and ref_type_ok and ref_id_ok:
                        self.log_result("Step 8 - CRITICAL: Verify Stock OUT Movement", True, 
                                      f"✅ Stock OUT movement CORRECTLY created: "
                                      f"qty_delta={stock_out.get('qty_delta')}, "
                                      f"weight_delta={stock_out.get('weight_delta')}, "
                                      f"reference_type={stock_out.get('reference_type')}, "
                                      f"reference_id={stock_out.get('reference_id')}")
                        self.test_data["stock_out_movement"] = stock_out
                    else:
                        self.log_result("Step 8 - CRITICAL: Verify Stock OUT Movement", False, "", 
                                      f"❌ Stock OUT movement has incorrect values: "
                                      f"qty_delta={stock_out.get('qty_delta')} (expected {expected_qty}), "
                                      f"weight_delta={stock_out.get('weight_delta')} (expected {expected_weight}), "
                                      f"reference_type={stock_out.get('reference_type')}, "
                                      f"reference_id={stock_out.get('reference_id')}")
                        return False
                else:
                    self.log_result("Step 8 - CRITICAL: Verify Stock OUT Movement", False, "", 
                                  "❌ CRITICAL BUG: No Stock OUT movement found for invoice finalization!")
                    return False
            else:
                self.log_result("Step 8 - CRITICAL: Verify Stock OUT Movement", False, "", 
                              f"Failed to get stock movements: {response.text}")
                return False

            # Step 9: Verify inventory header reduced
            response = self.session.get(f"{BASE_URL}/inventory/headers")
            if response.status_code == 200:
                headers_data = response.json()
                headers = headers_data.get('items', []) if isinstance(headers_data, dict) else headers_data
                
                gold_ring_headers = [h for h in headers if h.get('name') == 'Gold Ring']
                
                if gold_ring_headers:
                    header = gold_ring_headers[0]
                    expected_qty = 0  # 1 (from purchase) - 1 (from sale) = 0
                    expected_weight = 5.5  # 10.5 (from purchase) - 5.0 (from sale) = 5.5
                    
                    qty_ok = abs(header.get('current_qty', 0) - expected_qty) < 0.001
                    weight_ok = abs(header.get('current_weight', 0) - expected_weight) < 0.001
                    
                    if qty_ok and weight_ok:
                        self.log_result("Step 9 - Verify Inventory Header Reduced", True, 
                                      f"✅ Inventory correctly updated: "
                                      f"current_qty={header.get('current_qty')}, "
                                      f"current_weight={header.get('current_weight')}")
                    else:
                        self.log_result("Step 9 - Verify Inventory Header Reduced", False, "", 
                                      f"❌ Inventory not correctly updated: "
                                      f"current_qty={header.get('current_qty')} (expected {expected_qty}), "
                                      f"current_weight={header.get('current_weight')} (expected {expected_weight})")
                        return False
                else:
                    self.log_result("Step 9 - Verify Inventory Header Reduced", False, "", 
                                  "Gold Ring inventory header not found")
                    return False
            else:
                self.log_result("Step 9 - Verify Inventory Header Reduced", False, "", 
                              f"Failed to get inventory headers: {response.text}")
                return False

            # Step 10: Verify inventory report shows correct totals
            response = self.session.get(f"{BASE_URL}/reports/inventory")
            if response.status_code == 200:
                report = response.json()
                
                # Find Gold Ring in the report
                gold_ring_items = [item for item in report.get('items', []) if item.get('name') == 'Gold Ring']
                
                if gold_ring_items:
                    item = gold_ring_items[0]
                    
                    # Check totals
                    total_in_qty = item.get('total_in_qty', 0)
                    total_out_qty = item.get('total_out_qty', 0)
                    net_qty = item.get('net_quantity', 0)
                    
                    total_in_weight = item.get('total_in_weight', 0)
                    total_out_weight = item.get('total_out_weight', 0)
                    net_weight = item.get('net_weight', 0)
                    
                    # Expected values
                    expected_in_qty = 1
                    expected_out_qty = 1
                    expected_net_qty = 0
                    expected_in_weight = 10.5
                    expected_out_weight = 5.0
                    expected_net_weight = 5.5
                    
                    qty_checks = (
                        abs(total_in_qty - expected_in_qty) < 0.001 and
                        abs(total_out_qty - expected_out_qty) < 0.001 and
                        abs(net_qty - expected_net_qty) < 0.001
                    )
                    
                    weight_checks = (
                        abs(total_in_weight - expected_in_weight) < 0.001 and
                        abs(total_out_weight - expected_out_weight) < 0.001 and
                        abs(net_weight - expected_net_weight) < 0.001
                    )
                    
                    if qty_checks and weight_checks:
                        self.log_result("Step 10 - Verify Inventory Report", True, 
                                      f"✅ Inventory report correct: "
                                      f"IN({total_in_qty}qty, {total_in_weight}g), "
                                      f"OUT({total_out_qty}qty, {total_out_weight}g), "
                                      f"NET({net_qty}qty, {net_weight}g)")
                    else:
                        self.log_result("Step 10 - Verify Inventory Report", False, "", 
                                      f"❌ Inventory report incorrect: "
                                      f"IN({total_in_qty}qty, {total_in_weight}g), "
                                      f"OUT({total_out_qty}qty, {total_out_weight}g), "
                                      f"NET({net_qty}qty, {net_weight}g)")
                        return False
                else:
                    self.log_result("Step 10 - Verify Inventory Report", False, "", 
                                  "Gold Ring not found in inventory report")
                    return False
            else:
                self.log_result("Step 10 - Verify Inventory Report", False, "", 
                              f"Failed to get inventory report: {response.text}")
                return False

            return True
            
        except Exception as e:
            self.log_result("Scenario 1 - Exception", False, "", f"Error: {str(e)}")
            return False

    def test_scenario_2_non_existent_category(self):
        """TEST SCENARIO 2: Invoice with Non-Existent Category (Edge Case)"""
        print("=" * 80)
        print("TEST SCENARIO 2: Invoice with Non-Existent Category (Edge Case)")
        print("=" * 80)
        
        try:
            # Use existing customer from scenario 1
            if "customer" not in self.test_data:
                self.log_result("Scenario 2 - Prerequisites", False, "", "Customer not found from scenario 1")
                return False

            # Step 1: Create invoice with non-existent category
            invoice_data = {
                "customer_type": "saved",
                "customer_id": self.test_data["customer"]["id"],
                "invoice_type": "sale",
                "items": [
                    {
                        "category": "Non-Existent Category",  # This category doesn't exist in inventory
                        "description": "Custom Gold Item - 3.0g",
                        "qty": 1,
                        "gross_weight": 3.0,
                        "stone_weight": 0.0,
                        "net_gold_weight": 3.0,
                        "weight": 3.0,
                        "purity": 22,
                        "metal_rate": 200.0,
                        "gold_value": 600.0,
                        "making_charge_type": "flat",
                        "making_value": 100.0,
                        "stone_charges": 0.0,
                        "wastage_charges": 30.0,
                        "item_discount": 0.0,
                        "vat_percent": 5.0,
                        "vat_amount": 36.5,
                        "line_total": 766.5
                    }
                ],
                "subtotal": 730.0,
                "discount_amount": 0.0,
                "tax_type": "cgst_sgst",
                "gst_percent": 5.0,
                "cgst_total": 18.25,
                "sgst_total": 18.25,
                "igst_total": 0.0,
                "vat_total": 36.5,
                "grand_total": 766.5,
                "paid_amount": 0.0,
                "balance_due": 766.5
            }
            
            response = self.session.post(f"{BASE_URL}/invoices", json=invoice_data)
            if response.status_code == 201:
                invoice = response.json()
                self.test_data["invoice_2"] = invoice
                self.log_result("Step 1 - Create Invoice with Non-Existent Category", True, 
                              f"Created invoice: {invoice['invoice_number']} with Non-Existent Category (3.0g)")
            else:
                self.log_result("Step 1 - Create Invoice with Non-Existent Category", False, "", 
                              f"Failed to create invoice: {response.text}")
                return False

            # Step 2: Finalize invoice
            response = self.session.post(f"{BASE_URL}/invoices/{invoice['id']}/finalize")
            if response.status_code == 200:
                finalized_invoice = response.json()
                self.test_data["finalized_invoice_2"] = finalized_invoice
                self.log_result("Step 2 - Finalize Invoice with Non-Existent Category", True, 
                              f"Finalized invoice - should create Stock OUT movement even without inventory header")
            else:
                self.log_result("Step 2 - Finalize Invoice with Non-Existent Category", False, "", 
                              f"Failed to finalize invoice: {response.text}")
                return False

            # Step 3: VERIFY Stock OUT movement STILL created
            response = self.session.get(f"{BASE_URL}/stock-movements")
            if response.status_code == 200:
                movements_data = response.json()
                movements = movements_data.get('items', []) if isinstance(movements_data, dict) else movements_data
                
                stock_out_movements = [m for m in movements if m.get('movement_type') == 'Stock OUT' 
                                     and m.get('reference_type') == 'invoice' 
                                     and m.get('reference_id') == invoice['id']]
                
                if stock_out_movements:
                    stock_out = stock_out_movements[0]
                    expected_qty = -1  # MUST be negative
                    expected_weight = -3.0  # MUST be negative
                    expected_header_name = "Non-Existent Category"
                    
                    qty_ok = stock_out.get('qty_delta') == expected_qty
                    weight_ok = abs(stock_out.get('weight_delta', 0) - expected_weight) < 0.001
                    header_name_ok = stock_out.get('header_name') == expected_header_name
                    header_id_null = stock_out.get('header_id') is None
                    ref_type_ok = stock_out.get('reference_type') == 'invoice'
                    ref_id_ok = stock_out.get('reference_id') == invoice['id']
                    
                    if qty_ok and weight_ok and header_name_ok and header_id_null and ref_type_ok and ref_id_ok:
                        self.log_result("Step 3 - CRITICAL: Verify Stock OUT Movement for Non-Existent Category", True, 
                                      f"✅ Stock OUT movement CORRECTLY created even without inventory header: "
                                      f"qty_delta={stock_out.get('qty_delta')}, "
                                      f"weight_delta={stock_out.get('weight_delta')}, "
                                      f"header_name='{stock_out.get('header_name')}', "
                                      f"header_id={stock_out.get('header_id')}")
                        self.test_data["stock_out_movement_2"] = stock_out
                    else:
                        self.log_result("Step 3 - CRITICAL: Verify Stock OUT Movement for Non-Existent Category", False, "", 
                                      f"❌ Stock OUT movement has incorrect values: "
                                      f"qty_delta={stock_out.get('qty_delta')} (expected {expected_qty}), "
                                      f"weight_delta={stock_out.get('weight_delta')} (expected {expected_weight}), "
                                      f"header_name='{stock_out.get('header_name')}' (expected '{expected_header_name}'), "
                                      f"header_id={stock_out.get('header_id')} (expected None)")
                        return False
                else:
                    self.log_result("Step 3 - CRITICAL: Verify Stock OUT Movement for Non-Existent Category", False, "", 
                                  "❌ CRITICAL BUG: No Stock OUT movement found for invoice with non-existent category!")
                    return False
            else:
                self.log_result("Step 3 - CRITICAL: Verify Stock OUT Movement for Non-Existent Category", False, "", 
                              f"Failed to get stock movements: {response.text}")
                return False

            return True
            
        except Exception as e:
            self.log_result("Scenario 2 - Exception", False, "", f"Error: {str(e)}")
            return False

    def test_scenario_3_no_category(self):
        """TEST SCENARIO 3: Invoice with No Category (Edge Case)"""
        print("=" * 80)
        print("TEST SCENARIO 3: Invoice with No Category (Edge Case)")
        print("=" * 80)
        
        try:
            # Use existing customer from scenario 1
            if "customer" not in self.test_data:
                self.log_result("Scenario 3 - Prerequisites", False, "", "Customer not found from scenario 1")
                return False

            # Step 1: Create invoice with no category but description
            invoice_data = {
                "customer_type": "saved",
                "customer_id": self.test_data["customer"]["id"],
                "invoice_type": "sale",
                "items": [
                    {
                        "category": None,  # No category
                        "description": "Custom Gold Item",  # Should use this as header_name
                        "qty": 1,
                        "gross_weight": 2.5,
                        "stone_weight": 0.0,
                        "net_gold_weight": 2.5,
                        "weight": 2.5,
                        "purity": 22,
                        "metal_rate": 200.0,
                        "gold_value": 500.0,
                        "making_charge_type": "flat",
                        "making_value": 80.0,
                        "stone_charges": 0.0,
                        "wastage_charges": 25.0,
                        "item_discount": 0.0,
                        "vat_percent": 5.0,
                        "vat_amount": 30.25,
                        "line_total": 635.25
                    }
                ],
                "subtotal": 605.0,
                "discount_amount": 0.0,
                "tax_type": "cgst_sgst",
                "gst_percent": 5.0,
                "cgst_total": 15.125,
                "sgst_total": 15.125,
                "igst_total": 0.0,
                "vat_total": 30.25,
                "grand_total": 635.25,
                "paid_amount": 0.0,
                "balance_due": 635.25
            }
            
            response = self.session.post(f"{BASE_URL}/invoices", json=invoice_data)
            if response.status_code == 201:
                invoice = response.json()
                self.test_data["invoice_3"] = invoice
                self.log_result("Step 1 - Create Invoice with No Category", True, 
                              f"Created invoice: {invoice['invoice_number']} with no category but description (2.5g)")
            else:
                self.log_result("Step 1 - Create Invoice with No Category", False, "", 
                              f"Failed to create invoice: {response.text}")
                return False

            # Step 2: Finalize invoice
            response = self.session.post(f"{BASE_URL}/invoices/{invoice['id']}/finalize")
            if response.status_code == 200:
                finalized_invoice = response.json()
                self.test_data["finalized_invoice_3"] = finalized_invoice
                self.log_result("Step 2 - Finalize Invoice with No Category", True, 
                              f"Finalized invoice - should create Stock OUT movement with description as header_name")
            else:
                self.log_result("Step 2 - Finalize Invoice with No Category", False, "", 
                              f"Failed to finalize invoice: {response.text}")
                return False

            # Step 3: VERIFY Stock OUT movement created with fallback naming
            response = self.session.get(f"{BASE_URL}/stock-movements")
            if response.status_code == 200:
                movements_data = response.json()
                movements = movements_data.get('items', []) if isinstance(movements_data, dict) else movements_data
                
                stock_out_movements = [m for m in movements if m.get('movement_type') == 'Stock OUT' 
                                     and m.get('reference_type') == 'invoice' 
                                     and m.get('reference_id') == invoice['id']]
                
                if stock_out_movements:
                    stock_out = stock_out_movements[0]
                    expected_qty = -1  # MUST be negative
                    expected_weight = -2.5  # MUST be negative
                    # Should use description as header_name when category is null
                    expected_header_name = "Custom Gold Item"
                    
                    qty_ok = stock_out.get('qty_delta') == expected_qty
                    weight_ok = abs(stock_out.get('weight_delta', 0) - expected_weight) < 0.001
                    header_name_ok = stock_out.get('header_name') == expected_header_name
                    ref_type_ok = stock_out.get('reference_type') == 'invoice'
                    ref_id_ok = stock_out.get('reference_id') == invoice['id']
                    
                    if qty_ok and weight_ok and header_name_ok and ref_type_ok and ref_id_ok:
                        self.log_result("Step 3 - CRITICAL: Verify Stock OUT Movement with Fallback Naming", True, 
                                      f"✅ Stock OUT movement CORRECTLY created with fallback naming: "
                                      f"qty_delta={stock_out.get('qty_delta')}, "
                                      f"weight_delta={stock_out.get('weight_delta')}, "
                                      f"header_name='{stock_out.get('header_name')}'")
                        self.test_data["stock_out_movement_3"] = stock_out
                    else:
                        self.log_result("Step 3 - CRITICAL: Verify Stock OUT Movement with Fallback Naming", False, "", 
                                      f"❌ Stock OUT movement has incorrect values: "
                                      f"qty_delta={stock_out.get('qty_delta')} (expected {expected_qty}), "
                                      f"weight_delta={stock_out.get('weight_delta')} (expected {expected_weight}), "
                                      f"header_name='{stock_out.get('header_name')}' (expected '{expected_header_name}')")
                        return False
                else:
                    self.log_result("Step 3 - CRITICAL: Verify Stock OUT Movement with Fallback Naming", False, "", 
                                  "❌ CRITICAL BUG: No Stock OUT movement found for invoice with no category!")
                    return False
            else:
                self.log_result("Step 3 - CRITICAL: Verify Stock OUT Movement with Fallback Naming", False, "", 
                              f"Failed to get stock movements: {response.text}")
                return False

            return True
            
        except Exception as e:
            self.log_result("Scenario 3 - Exception", False, "", f"Error: {str(e)}")
            return False

    def run_comprehensive_test(self):
        """Run all test scenarios"""
        print("🚀 STARTING CRITICAL INVENTORY FIX TESTING - Stock OUT Movement Creation")
        print("=" * 80)
        
        # Authenticate
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with testing.")
            return False
        
        # Run test scenarios
        scenario_1_success = self.test_scenario_1_full_invoice_flow()
        scenario_2_success = self.test_scenario_2_non_existent_category()
        scenario_3_success = self.test_scenario_3_no_category()
        
        # Print summary
        self.print_summary()
        
        # Overall success
        overall_success = scenario_1_success and scenario_2_success and scenario_3_success
        
        if overall_success:
            print("🎉 ALL CRITICAL TESTS PASSED - Stock OUT Movement Creation Fix is WORKING!")
        else:
            print("❌ CRITICAL TESTS FAILED - Stock OUT Movement Creation Fix has ISSUES!")
        
        return overall_success

    def print_summary(self):
        """Print test results summary"""
        print("=" * 80)
        print("🎯 CRITICAL INVENTORY FIX TESTING SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
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
        
        print("✅ PASSED TESTS:")
        print("-" * 40)
        for result in self.test_results:
            if result["success"]:
                print(f"• {result['test']}")
        
        print("=" * 80)
        print("🏁 CRITICAL INVENTORY FIX TESTING COMPLETE")
        print("=" * 80)

if __name__ == "__main__":
    tester = InventoryStockOutTester()
    tester.run_comprehensive_test()
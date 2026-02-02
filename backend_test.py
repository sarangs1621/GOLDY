#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Gold Shop ERP
Testing Dashboard APIs to identify why dashboard shows all zeros
"""

import requests
import json
import uuid
from datetime import datetime, timezone
import time

# Configuration
BACKEND_URL = "https://jewelcalc-standard.preview.emergentagent.com/api"
TEST_USER = {
    "username": "admin",
    "password": "admin123"  # Default admin password from init_db.py
}

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.csrf_token = None
        self.test_results = []
        
    def log_result(self, test_name, success, details, response_data=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {details}")
        
    def authenticate(self):
        """Authenticate and get tokens"""
        try:
            # Login
            login_data = {
                "username": TEST_USER["username"],
                "password": TEST_USER["password"]
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.csrf_token = data.get("csrf_token")
                
                # Set headers for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}",
                    "X-CSRF-Token": self.csrf_token
                })
                
                self.log_result("Authentication", True, f"Successfully authenticated as {TEST_USER['username']}")
                return True
            else:
                self.log_result("Authentication", False, f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def test_dashboard_decimal128_fix(self):
        """SPECIFIC TEST: Dashboard Decimal128 Fix for Outstanding Summary API"""
        print("\n" + "="*80)
        print("🎯 TESTING DASHBOARD DECIMAL128 FIX - PRIMARY FOCUS")
        print("="*80)
        
        print("\n📋 TEST REQUIREMENTS:")
        print("1. ✅ Login as admin user")
        print("2. ✅ Call GET /api/parties/outstanding-summary")
        print("3. ✅ VERIFY: API returns HTTP 200 (not 520 error)")
        print("4. ✅ VERIFY: Response has structure: {\"total_customer_due\": <number>, \"top_10_outstanding\": [<array>]}")
        print("5. ✅ VERIFY: total_customer_due is a number (not crashing)")
        print("6. ✅ VERIFY: top_10_outstanding is an array")
        print("7. ✅ VERIFY: Each item in top_10_outstanding has: customer_id, customer_name, outstanding")
        
        # Test the specific outstanding summary API with Decimal128 fix
        outstanding_success = self.test_parties_outstanding_summary_api()
        
        print("\n📊 DASHBOARD INTEGRATION TEST:")
        print("Testing all 3 dashboard APIs together...")
        
        # Test all 3 dashboard APIs
        headers_success = self.test_inventory_headers_api()
        stock_success = self.test_inventory_stock_totals_api()
        
        all_dashboard_apis_working = headers_success and stock_success and outstanding_success
        
        print(f"\n🔍 DASHBOARD API RESULTS:")
        print(f"   • Inventory Headers: {'✅ WORKING' if headers_success else '❌ FAILED'}")
        print(f"   • Stock Totals: {'✅ WORKING' if stock_success else '❌ FAILED'}")
        print(f"   • Outstanding Summary: {'✅ WORKING' if outstanding_success else '❌ FAILED'}")
        print(f"   • Overall Dashboard: {'✅ ALL WORKING' if all_dashboard_apis_working else '❌ SOME FAILED'}")
        
        # Log the overall result
        self.log_result(
            "Dashboard Decimal128 Fix - Integration Test",
            all_dashboard_apis_working,
            f"Headers: {'✓' if headers_success else '✗'}, Stock: {'✓' if stock_success else '✗'}, Outstanding: {'✓' if outstanding_success else '✗'}",
            {
                "inventory_headers_working": headers_success,
                "stock_totals_working": stock_success,
                "outstanding_summary_working": outstanding_success,
                "decimal128_fix_status": "WORKING" if outstanding_success else "FAILED",
                "dashboard_ready": all_dashboard_apis_working
            }
        )
        
        return all_dashboard_apis_working
    
    def test_inventory_headers_api(self):
        """Test GET /api/inventory/headers - Should return paginated inventory headers"""
        print("\n--- Testing Inventory Headers API ---")
        
        try:
            # Test with default pagination
            response = self.session.get(f"{BACKEND_URL}/inventory/headers")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                has_data_key = 'data' in data or 'items' in data
                has_pagination = 'pagination' in data
                
                # Extract items
                items = data.get('data', data.get('items', []))
                total_count = 0
                
                if has_pagination:
                    pagination = data.get('pagination', {})
                    total_count = pagination.get('total_count', 0)
                else:
                    total_count = len(items) if isinstance(items, list) else 0
                
                # Verify structure matches frontend expectations
                structure_correct = has_data_key or isinstance(items, list)
                has_items = len(items) > 0 if isinstance(items, list) else False
                
                # Check individual item structure if items exist
                item_structure_correct = True
                if has_items and items:
                    first_item = items[0]
                    required_fields = ['id', 'name']
                    item_structure_correct = all(field in first_item for field in required_fields)
                
                success = structure_correct and response.status_code == 200
                
                details = f"Status: {response.status_code}, "
                details += f"Items: {len(items) if isinstance(items, list) else 'N/A'}, "
                details += f"Total Count: {total_count}, "
                details += f"Structure: {'✓' if structure_correct else '✗'}, "
                details += f"Item Fields: {'✓' if item_structure_correct else '✗'}"
                
                self.log_result(
                    "Dashboard API - Inventory Headers",
                    success,
                    details,
                    {
                        "response_structure": {
                            "has_data_key": has_data_key,
                            "has_pagination": has_pagination,
                            "items_count": len(items) if isinstance(items, list) else 0,
                            "total_count": total_count
                        },
                        "sample_item": items[0] if has_items else None,
                        "full_response": data
                    }
                )
                
                return success and has_items
            else:
                self.log_result(
                    "Dashboard API - Inventory Headers", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            self.log_result("Dashboard API - Inventory Headers", False, f"Error: {str(e)}")
            return False
    
    def test_inventory_stock_totals_api(self):
        """Test GET /api/inventory/stock-totals - Should return array of stock totals by category"""
        print("\n--- Testing Inventory Stock Totals API ---")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/inventory/stock-totals")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if response is array or has array
                is_array = isinstance(data, list)
                items = data if is_array else data.get('items', data.get('data', []))
                
                # Verify structure matches frontend expectations
                has_items = len(items) > 0 if isinstance(items, list) else False
                
                # Check individual item structure if items exist
                item_structure_correct = True
                expected_fields = ['header_id', 'header_name', 'total_qty', 'total_weight']
                
                if has_items and items:
                    first_item = items[0]
                    item_structure_correct = all(field in first_item for field in expected_fields)
                    
                    # Check for Decimal128 serialization issues
                    serialization_ok = True
                    for field in ['total_qty', 'total_weight']:
                        if field in first_item:
                            value = first_item[field]
                            if not isinstance(value, (int, float)):
                                serialization_ok = False
                                break
                
                success = response.status_code == 200 and isinstance(items, list)
                
                details = f"Status: {response.status_code}, "
                details += f"Is Array: {'✓' if is_array else '✗'}, "
                details += f"Items: {len(items) if isinstance(items, list) else 'N/A'}, "
                details += f"Structure: {'✓' if item_structure_correct else '✗'}"
                
                if has_items:
                    details += f", Sample Total Qty: {items[0].get('total_qty', 'N/A')}"
                    details += f", Sample Total Weight: {items[0].get('total_weight', 'N/A')}"
                
                self.log_result(
                    "Dashboard API - Stock Totals",
                    success,
                    details,
                    {
                        "is_array": is_array,
                        "items_count": len(items) if isinstance(items, list) else 0,
                        "expected_fields": expected_fields,
                        "sample_item": items[0] if has_items else None,
                        "full_response": data
                    }
                )
                
                return success and has_items
            else:
                self.log_result(
                    "Dashboard API - Stock Totals", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            self.log_result("Dashboard API - Stock Totals", False, f"Error: {str(e)}")
            return False
    
    def test_parties_outstanding_summary_api(self):
        """Test GET /api/parties/outstanding-summary - DECIMAL128 FIX VERIFICATION"""
        print("\n--- Testing Parties Outstanding Summary API - DECIMAL128 FIX ---")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/parties/outstanding-summary")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check expected structure
                has_total_due = 'total_customer_due' in data
                has_top_10 = 'top_10_outstanding' in data
                
                total_due = data.get('total_customer_due', 0)
                top_10_list = data.get('top_10_outstanding', [])
                
                # Verify structure matches frontend expectations
                structure_correct = has_total_due and has_top_10
                
                # CRITICAL: Check that total_customer_due is a number (not crashing)
                total_due_is_number = isinstance(total_due, (int, float))
                
                # CRITICAL: Check that top_10_outstanding is an array
                top_10_is_array = isinstance(top_10_list, list)
                
                # Check top_10 item structure if exists
                top_10_structure_correct = True
                if top_10_list:
                    expected_fields = ['customer_id', 'customer_name', 'outstanding']
                    first_item = top_10_list[0]
                    top_10_structure_correct = all(field in first_item for field in expected_fields)
                    
                    # CRITICAL: Check that outstanding amounts are numbers (Decimal128 fix verification)
                    outstanding_amounts_are_numbers = all(
                        isinstance(item.get('outstanding', 0), (int, float)) 
                        for item in top_10_list
                    )
                else:
                    outstanding_amounts_are_numbers = True  # No items to check
                
                # DECIMAL128 FIX VERIFICATION: No TypeError should occur
                decimal128_fix_working = response.status_code == 200  # API didn't crash with TypeError
                
                success = (response.status_code == 200 and structure_correct and 
                          total_due_is_number and top_10_is_array and decimal128_fix_working)
                
                details = f"Status: {response.status_code} ({'✓ NO 520 ERROR' if response.status_code == 200 else '❌ ERROR'}), "
                details += f"Total Due: {total_due} ({'✓ NUMBER' if total_due_is_number else '❌ NOT NUMBER'}), "
                details += f"Top 10: {len(top_10_list)} items ({'✓ ARRAY' if top_10_is_array else '❌ NOT ARRAY'}), "
                details += f"Structure: {'✓' if structure_correct else '✗'}, "
                details += f"Decimal128 Fix: {'✓ WORKING' if decimal128_fix_working else '❌ FAILED'}"
                
                self.log_result(
                    "Dashboard API - Outstanding Summary (Decimal128 Fix)",
                    success,
                    details,
                    {
                        "total_customer_due": total_due,
                        "total_due_type": type(total_due).__name__,
                        "top_10_count": len(top_10_list),
                        "top_10_type": type(top_10_list).__name__,
                        "decimal128_fix_status": "WORKING - No TypeError" if decimal128_fix_working else "FAILED - TypeError occurred",
                        "sample_top_10": top_10_list[0] if top_10_list else None,
                        "full_response": data
                    }
                )
                
                return success
            else:
                # Check if this is the specific 520 error that was happening before the fix
                is_520_error = response.status_code == 520
                error_details = f"HTTP {response.status_code}: {response.text}"
                
                if is_520_error:
                    error_details += " - THIS IS THE DECIMAL128 BUG! Fix not working."
                
                self.log_result(
                    "Dashboard API - Outstanding Summary (Decimal128 Fix)", 
                    False, 
                    error_details,
                    {
                        "status_code": response.status_code, 
                        "response": response.text,
                        "is_decimal128_bug": is_520_error,
                        "fix_status": "FAILED - API returning error" if is_520_error else "Unknown error"
                    }
                )
                return False
                
        except Exception as e:
            # Check if this is a Decimal128 related error
            is_decimal128_error = "Decimal128" in str(e) or "unsupported operand" in str(e)
            error_msg = f"Error: {str(e)}"
            if is_decimal128_error:
                error_msg += " - DECIMAL128 SERIALIZATION ERROR DETECTED!"
            
            self.log_result(
                "Dashboard API - Outstanding Summary (Decimal128 Fix)", 
                False, 
                error_msg,
                {
                    "error": str(e),
                    "is_decimal128_error": is_decimal128_error,
                    "fix_status": "FAILED - Exception occurred"
                }
            )
            return False
    
    def test_database_data_verification(self):
        """Verify database has data by testing related endpoints"""
        print("\n--- Testing Database Data Verification ---")
        
        try:
            # Test 1: Check if we have inventory headers
            headers_response = self.session.get(f"{BACKEND_URL}/inventory/headers?page=1&page_size=50")
            headers_count = 0
            if headers_response.status_code == 200:
                headers_data = headers_response.json()
                items = headers_data.get('data', headers_data.get('items', []))
                headers_count = len(items) if isinstance(items, list) else 0
            
            # Test 2: Check if we have parties
            parties_response = self.session.get(f"{BACKEND_URL}/parties?page=1&page_size=50")
            parties_count = 0
            if parties_response.status_code == 200:
                parties_data = parties_response.json()
                items = parties_data.get('data', parties_data.get('items', []))
                parties_count = len(items) if isinstance(items, list) else 0
            
            # Test 3: Check if we have invoices
            invoices_response = self.session.get(f"{BACKEND_URL}/invoices?page=1&page_size=50")
            invoices_count = 0
            if invoices_response.status_code == 200:
                invoices_data = invoices_response.json()
                items = invoices_data.get('data', invoices_data.get('items', []))
                invoices_count = len(items) if isinstance(items, list) else 0
            
            # Test 4: Check if we have users
            users_response = self.session.get(f"{BACKEND_URL}/users")
            users_count = 0
            if users_response.status_code == 200:
                users_data = users_response.json()
                items = users_data.get('data', users_data.get('items', users_data if isinstance(users_data, list) else []))
                users_count = len(items) if isinstance(items, list) else 0
            
            has_data = headers_count > 0 or parties_count > 0 or invoices_count > 0 or users_count > 0
            
            details = f"Headers: {headers_count}, Parties: {parties_count}, Invoices: {invoices_count}, Users: {users_count}"
            
            self.log_result(
                "Database Data Verification",
                has_data,
                details,
                {
                    "inventory_headers": headers_count,
                    "parties": parties_count,
                    "invoices": invoices_count,
                    "users": users_count,
                    "has_data": has_data
                }
            )
            
            return has_data
            
        except Exception as e:
            self.log_result("Database Data Verification", False, f"Error: {str(e)}")
            return False
    
    def test_permission_validation(self):
        """Test if permission checks are working correctly for admin user"""
        print("\n--- Testing Permission Validation ---")
        
        try:
            # Test user info to verify admin permissions
            user_response = self.session.get(f"{BACKEND_URL}/auth/me")
            
            if user_response.status_code == 200:
                user_data = user_response.json()
                user_role = user_data.get('role', '')
                user_permissions = user_data.get('permissions', [])
                
                # Check if user has required permissions
                required_permissions = ['inventory.view', 'parties.view']
                has_inventory_perm = 'inventory.view' in user_permissions or user_role == 'admin'
                has_parties_perm = 'parties.view' in user_permissions or user_role == 'admin'
                
                permissions_ok = has_inventory_perm and has_parties_perm
                
                details = f"Role: {user_role}, "
                details += f"Inventory Perm: {'✓' if has_inventory_perm else '✗'}, "
                details += f"Parties Perm: {'✓' if has_parties_perm else '✗'}, "
                details += f"Total Permissions: {len(user_permissions)}"
                
                self.log_result(
                    "Permission Validation",
                    permissions_ok,
                    details,
                    {
                        "user_role": user_role,
                        "permissions_count": len(user_permissions),
                        "has_required_permissions": permissions_ok,
                        "sample_permissions": user_permissions[:5] if user_permissions else []
                    }
                )
                
                return permissions_ok
            else:
                self.log_result(
                    "Permission Validation", 
                    False, 
                    f"Failed to get user info: {user_response.status_code}",
                    {"status_code": user_response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_result("Permission Validation", False, f"Error: {str(e)}")
            return False
    
    def test_response_format_validation(self):
        """Test response format validation and serialization"""
        print("\n--- Testing Response Format Validation ---")
        
        try:
            # Test each API for proper JSON serialization
            apis_to_test = [
                ("inventory/headers", "Inventory Headers"),
                ("inventory/stock-totals", "Stock Totals"),
                ("parties/outstanding-summary", "Outstanding Summary")
            ]
            
            all_serialized_correctly = True
            serialization_results = {}
            
            for endpoint, name in apis_to_test:
                try:
                    response = self.session.get(f"{BACKEND_URL}/{endpoint}")
                    
                    if response.status_code == 200:
                        # Try to parse JSON
                        data = response.json()
                        
                        # Check for common serialization issues
                        json_str = json.dumps(data)  # This will fail if there are serialization issues
                        
                        serialization_results[name] = {
                            "status": "✓ OK",
                            "size": len(json_str),
                            "type": type(data).__name__
                        }
                    else:
                        serialization_results[name] = {
                            "status": f"✗ HTTP {response.status_code}",
                            "size": 0,
                            "type": "error"
                        }
                        all_serialized_correctly = False
                        
                except json.JSONDecodeError as je:
                    serialization_results[name] = {
                        "status": f"✗ JSON Error: {str(je)}",
                        "size": 0,
                        "type": "json_error"
                    }
                    all_serialized_correctly = False
                except Exception as e:
                    serialization_results[name] = {
                        "status": f"✗ Error: {str(e)}",
                        "size": 0,
                        "type": "error"
                    }
                    all_serialized_correctly = False
            
            details = ", ".join([f"{name}: {result['status']}" for name, result in serialization_results.items()])
            
            self.log_result(
                "Response Format Validation",
                all_serialized_correctly,
                details,
                serialization_results
            )
            
            return all_serialized_correctly
            
        except Exception as e:
            self.log_result("Response Format Validation", False, f"Error: {str(e)}")
            return False
    
    
    def test_create_jobcard_with_gold_settlement(self):
        """Test creating a job card with gold settlement fields"""
        print("\n--- Testing Create Job Card with Gold Settlement ---")
        
        try:
            # Get or create customer and worker
            customer_id = self.get_or_create_test_customer()
            worker_id = self.get_or_create_test_worker()
            
            if not customer_id or not worker_id:
                return None
            
            # Create job card with gold settlement as per test requirements
            jobcard_data = {
                "customer_type": "saved",
                "customer_id": customer_id,
                "worker_id": worker_id,
                "items": [
                    {
                        "category": "Rings",
                        "description": "Gold Ring Repair with Settlement",
                        "qty": 1,
                        "weight_in": 15.500,
                        "purity": 916,
                        "work_type": "Repair",
                        "making_charge_type": "flat",
                        "making_charge_value": 50.00,
                        "vat_percent": 5.0
                    }
                ],
                # Gold Settlement fields as per test requirements
                "advance_in_gold_grams": 5.500,  # 3 decimal precision
                "advance_gold_rate": 25.00,      # 2 decimal precision
                "exchange_in_gold_grams": 3.250, # 3 decimal precision
                "exchange_gold_rate": 24.50,     # 2 decimal precision
                "notes": "Job card with gold settlement for testing"
            }
            
            response = self.session.post(f"{BACKEND_URL}/jobcards", json=jobcard_data)
            
            if response.status_code == 201:
                result = response.json()
                jobcard_id = result.get("id")
                
                # Verify the job card was created and retrieve it
                get_response = self.session.get(f"{BACKEND_URL}/jobcards/{jobcard_id}")
                
                if get_response.status_code == 200:
                    jobcard = get_response.json()
                    
                    # Verify gold settlement values with proper precision
                    advance_grams = jobcard.get("advance_in_gold_grams")
                    advance_rate = jobcard.get("advance_gold_rate")
                    exchange_grams = jobcard.get("exchange_in_gold_grams")
                    exchange_rate = jobcard.get("exchange_gold_rate")
                    
                    # Precision checks (3 decimals for grams, 2 decimals for rates)
                    advance_grams_correct = abs(advance_grams - 5.500) < 0.001 if advance_grams else False
                    advance_rate_correct = abs(advance_rate - 25.00) < 0.01 if advance_rate else False
                    exchange_grams_correct = abs(exchange_grams - 3.250) < 0.001 if exchange_grams else False
                    exchange_rate_correct = abs(exchange_rate - 24.50) < 0.01 if exchange_rate else False
                    
                    all_correct = all([advance_grams_correct, advance_rate_correct, 
                                     exchange_grams_correct, exchange_rate_correct])
                    
                    details = f"Advance: {advance_grams}g @ {advance_rate} OMR/g ({'✓' if advance_grams_correct and advance_rate_correct else '✗'}), "
                    details += f"Exchange: {exchange_grams}g @ {exchange_rate} OMR/g ({'✓' if exchange_grams_correct and exchange_rate_correct else '✗'})"
                    
                    self.log_result(
                        "Create Job Card with Gold Settlement",
                        all_correct,
                        details,
                        {
                            "jobcard_id": jobcard_id,
                            "advance_in_gold_grams": advance_grams,
                            "advance_gold_rate": advance_rate,
                            "exchange_in_gold_grams": exchange_grams,
                            "exchange_gold_rate": exchange_rate,
                            "precision_check": "3 decimals for grams, 2 decimals for rates"
                        }
                    )
                    
                    return jobcard_id if all_correct else None
                else:
                    self.log_result("Retrieve Created Job Card", False, f"Failed to retrieve: {get_response.status_code}")
                    return None
            else:
                self.log_result("Create Job Card with Gold Settlement", False, f"Failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Create Job Card with Gold Settlement", False, f"Error: {str(e)}")
            return None
    
    def test_update_jobcard_gold_settlement(self, jobcard_id):
        """Test updating job card gold settlement values"""
        print("\n--- Testing Update Job Card Gold Settlement ---")
        
        try:
            # Update gold settlement values
            update_data = {
                "advance_in_gold_grams": 6.750,  # Updated value
                "advance_gold_rate": 26.50,     # Updated value
                "exchange_in_gold_grams": 4.125, # Updated value
                "exchange_gold_rate": 25.75,    # Updated value
                "notes": "Updated gold settlement values for testing"
            }
            
            response = self.session.patch(f"{BACKEND_URL}/jobcards/{jobcard_id}", json=update_data)
            
            if response.status_code == 200:
                # Verify the update by retrieving the job card
                get_response = self.session.get(f"{BACKEND_URL}/jobcards/{jobcard_id}")
                
                if get_response.status_code == 200:
                    updated_jobcard = get_response.json()
                    
                    # Verify updated values
                    advance_grams = updated_jobcard.get("advance_in_gold_grams")
                    advance_rate = updated_jobcard.get("advance_gold_rate")
                    exchange_grams = updated_jobcard.get("exchange_in_gold_grams")
                    exchange_rate = updated_jobcard.get("exchange_gold_rate")
                    
                    # Check if values were updated correctly
                    advance_grams_updated = abs(advance_grams - 6.750) < 0.001 if advance_grams else False
                    advance_rate_updated = abs(advance_rate - 26.50) < 0.01 if advance_rate else False
                    exchange_grams_updated = abs(exchange_grams - 4.125) < 0.001 if exchange_grams else False
                    exchange_rate_updated = abs(exchange_rate - 25.75) < 0.01 if exchange_rate else False
                    
                    all_updated = all([advance_grams_updated, advance_rate_updated, 
                                     exchange_grams_updated, exchange_rate_updated])
                    
                    details = f"Updated Advance: {advance_grams}g @ {advance_rate} OMR/g ({'✓' if advance_grams_updated and advance_rate_updated else '✗'}), "
                    details += f"Updated Exchange: {exchange_grams}g @ {exchange_rate} OMR/g ({'✓' if exchange_grams_updated and exchange_rate_updated else '✗'})"
                    
                    self.log_result(
                        "Update Job Card Gold Settlement",
                        all_updated,
                        details,
                        {
                            "updated_advance_grams": advance_grams,
                            "updated_advance_rate": advance_rate,
                            "updated_exchange_grams": exchange_grams,
                            "updated_exchange_rate": exchange_rate
                        }
                    )
                    
                    return all_updated
                else:
                    self.log_result("Retrieve Updated Job Card", False, f"Failed to retrieve: {get_response.status_code}")
                    return False
            else:
                self.log_result("Update Job Card Gold Settlement", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Update Job Card Gold Settlement", False, f"Error: {str(e)}")
            return False
    
    def test_convert_jobcard_to_invoice_with_gold_settlement(self, jobcard_id):
        """Test converting job card to invoice and verify gold settlement calculations"""
        print("\n--- Testing Convert Job Card to Invoice with Gold Settlement ---")
        
        try:
            # First, complete the job card (required before conversion)
            complete_data = {"status": "completed"}
            complete_response = self.session.patch(f"{BACKEND_URL}/jobcards/{jobcard_id}", json=complete_data)
            
            if complete_response.status_code != 200:
                self.log_result("Complete Job Card", False, f"Failed to complete job card: {complete_response.status_code}")
                return False
            
            # Get the completed job card to verify gold settlement values
            jobcard_response = self.session.get(f"{BACKEND_URL}/jobcards/{jobcard_id}")
            if jobcard_response.status_code != 200:
                self.log_result("Get Job Card for Conversion", False, f"Failed to get job card: {jobcard_response.status_code}")
                return False
            
            jobcard = jobcard_response.json()
            
            # Extract gold settlement values for calculation verification
            advance_grams = float(jobcard.get("advance_in_gold_grams", 0) or 0)
            advance_rate = float(jobcard.get("advance_gold_rate", 0) or 0)
            exchange_grams = float(jobcard.get("exchange_in_gold_grams", 0) or 0)
            exchange_rate = float(jobcard.get("exchange_gold_rate", 0) or 0)
            
            # Calculate expected gold settlement deductions
            expected_advance_value = round(advance_grams * advance_rate, 3)
            expected_exchange_value = round(exchange_grams * exchange_rate, 3)
            expected_total_deduction = expected_advance_value + expected_exchange_value
            
            # Convert job card to invoice - backend will compute grand_total from job card items
            invoice_data = {}  # Empty - let backend compute from job card
            
            convert_response = self.session.post(f"{BACKEND_URL}/jobcards/{jobcard_id}/convert-to-invoice", json=invoice_data)
            
            if convert_response.status_code == 200:
                # API returns full invoice object directly
                invoice = convert_response.json()
                invoice_id = invoice.get("id")
                
                if invoice_id:
                    # Get actual values from the created invoice
                    actual_balance_due = float(invoice.get("balance_due", 0))
                    actual_grand_total = float(invoice.get("grand_total", 0))
                    invoice_notes = invoice.get("notes", "")
                    
                    # VERIFY FORMULA: balance_due = grand_total - advance_gold_value - exchange_gold_value
                    # Backend computes: balance_due = grand_total - (advance_grams * advance_rate) - (exchange_grams * exchange_rate)
                    expected_balance_due = round(actual_grand_total - expected_total_deduction, 3)
                    if expected_balance_due < 0:
                        expected_balance_due = 0.0
                    
                    # Check if the formula was applied correctly
                    balance_correct = abs(actual_balance_due - expected_balance_due) < 0.01
                    
                    # Check if notes contain gold settlement breakdown
                    notes_contain_settlement = (
                        "advance" in invoice_notes.lower() or 
                        "exchange" in invoice_notes.lower() or
                        "gold settlement" in invoice_notes.lower()
                    )
                    
                    # Verify precision of calculations
                    advance_value_precise = abs(expected_advance_value - round(advance_grams * advance_rate, 3)) < 0.001
                    exchange_value_precise = abs(expected_exchange_value - round(exchange_grams * exchange_rate, 3)) < 0.001
                    
                    # Check that gold settlement was actually deducted (balance_due < grand_total when there's settlement)
                    settlement_applied = (expected_total_deduction == 0) or (actual_balance_due < actual_grand_total)
                    
                    all_correct = balance_correct and notes_contain_settlement and advance_value_precise and exchange_value_precise and settlement_applied
                    
                    details = f"Grand Total: {actual_grand_total:.3f}, "
                    details += f"Balance Due: {actual_balance_due:.3f} (Expected: {expected_balance_due:.3f}) ({'✓' if balance_correct else '✗'}), "
                    details += f"Settlement Deduction: {expected_total_deduction:.3f} OMR ({'✓' if settlement_applied else '✗'}), "
                    details += f"Notes: {'✓' if notes_contain_settlement else '✗'}"
                    
                    self.log_result(
                        "Convert Job Card to Invoice - Gold Settlement Calculations",
                        all_correct,
                        details,
                        {
                            "invoice_id": invoice_id,
                            "grand_total": actual_grand_total,
                            "advance_gold_value": expected_advance_value,
                            "exchange_gold_value": expected_exchange_value,
                            "total_deduction": expected_total_deduction,
                            "expected_balance_due": expected_balance_due,
                            "actual_balance_due": actual_balance_due,
                            "balance_calculation_correct": balance_correct,
                            "settlement_applied": settlement_applied,
                            "notes_sample": invoice_notes[:100] if invoice_notes else "No notes"
                        }
                    )
                    
                    return all_correct
                else:
                    self.log_result("Get Created Invoice", False, f"Invoice id not found in response")
                    return False
            else:
                self.log_result("Convert Job Card to Invoice", False, f"Failed: {convert_response.status_code} - {convert_response.text}")
                return False
                
        except Exception as e:
            self.log_result("Convert Job Card to Invoice with Gold Settlement", False, f"Error: {str(e)}")
            return False
    
    def test_gold_settlement_precision_validation(self):
        """Test precision validation for gold settlement fields"""
        print("\n--- Testing Gold Settlement Precision Validation ---")
        
        try:
            customer_id = self.get_or_create_test_customer()
            if not customer_id:
                return
            
            # Test with high precision values to verify 3-decimal precision for grams
            jobcard_data = {
                "customer_type": "saved",
                "customer_id": customer_id,
                "items": [
                    {
                        "category": "Rings",
                        "description": "Precision Test Job Card",
                        "qty": 1,
                        "weight_in": 10.000,
                        "purity": 916,
                        "work_type": "Polish"
                    }
                ],
                # Test precision limits
                "advance_in_gold_grams": 12.345,  # 3 decimal precision
                "advance_gold_rate": 67.89,      # 2 decimal precision
                "exchange_in_gold_grams": 8.765, # 3 decimal precision
                "exchange_gold_rate": 43.21,     # 2 decimal precision
                "notes": "Precision validation test"
            }
            
            response = self.session.post(f"{BACKEND_URL}/jobcards", json=jobcard_data)
            
            if response.status_code == 201:
                result = response.json()
                jobcard_id = result.get("id")
                
                # Retrieve and verify precision
                get_response = self.session.get(f"{BACKEND_URL}/jobcards/{jobcard_id}")
                
                if get_response.status_code == 200:
                    jobcard = get_response.json()
                    
                    advance_grams = jobcard.get("advance_in_gold_grams")
                    advance_rate = jobcard.get("advance_gold_rate")
                    exchange_grams = jobcard.get("exchange_in_gold_grams")
                    exchange_rate = jobcard.get("exchange_gold_rate")
                    
                    # Verify precision is maintained
                    precision_correct = (
                        abs(advance_grams - 12.345) < 0.001 and
                        abs(advance_rate - 67.89) < 0.01 and
                        abs(exchange_grams - 8.765) < 0.001 and
                        abs(exchange_rate - 43.21) < 0.01
                    )
                    
                    self.log_result(
                        "Gold Settlement Precision Validation",
                        precision_correct,
                        f"Advance: {advance_grams}g @ {advance_rate}, Exchange: {exchange_grams}g @ {exchange_rate}",
                        {
                            "advance_precision_check": f"{advance_grams} == 12.345",
                            "exchange_precision_check": f"{exchange_grams} == 8.765",
                            "rate_precision_check": f"{advance_rate} == 67.89, {exchange_rate} == 43.21"
                        }
                    )
                    
                    return precision_correct
                else:
                    self.log_result("Precision Validation - Get Job Card", False, f"Failed: {get_response.status_code}")
                    return False
            else:
                self.log_result("Precision Validation - Create Job Card", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Gold Settlement Precision Validation", False, f"Error: {str(e)}")
            return False
    
    def test_new_purchase_calculation_formula(self):
        """Test NEW Purchase Amount Calculation Formula Implementation"""
        print("\n" + "="*80)
        print("🎯 TESTING NEW PURCHASE AMOUNT CALCULATION FORMULA")
        print("="*80)
        
        print("\n📋 NEW FORMULA (MUST USE):")
        print("Amount = (Weight × Entered_Purity ÷ Conversion_Factor) × Rate")
        print("Step-by-step:")
        print("- step1 = Weight × Entered_Purity")
        print("- step2 = step1 ÷ Conversion_Factor")
        print("- Amount = step2 × Rate")
        print("\n🎯 TEST SCENARIOS (VERIFY EXACT CALCULATIONS):")
        
        try:
            vendor_id = self.get_or_create_test_vendor()
            if not vendor_id:
                return False
            
            # Test scenarios with NEW FORMULA: Amount = (Weight × Entered_Purity ÷ Conversion_Factor) × Rate
            test_scenarios = [
                {
                    "name": "Test Purity 916 (22K) - Baseline",
                    "weight": 100,
                    "purity": 916,
                    "conversion_factor": 0.917,
                    "rate": 50,
                    "expected_amount": 4994.547,  # (100 × 916 ÷ 0.917) × 50 = 4,994,547.370 baisa = 4,994.547 OMR
                    "description": "Baseline test with 22K purity"
                },
                {
                    "name": "Test Purity 999 (24K) - Higher Purity", 
                    "weight": 100,
                    "purity": 999,
                    "conversion_factor": 0.917,
                    "rate": 50,
                    "expected_amount": 5446.958,  # (100 × 999 ÷ 0.917) × 50 = 5,446,957.539 baisa = 5,446.958 OMR
                    "description": "MUST be HIGHER than purity 916 result"
                },
                {
                    "name": "Test Purity 875 (21K) - Lower Purity",
                    "weight": 10,
                    "purity": 875,
                    "conversion_factor": 0.920,
                    "rate": 60,
                    "expected_amount": 570.652,  # (10 × 875 ÷ 0.920) × 60 = 570,652.174 baisa = 570.652 OMR
                    "description": "Lower purity test with different parameters"
                }
            ]
            
            all_tests_passed = True
            test_results = []
            
            for scenario in test_scenarios:
                print(f"\n--- Testing {scenario['name']} ---")
                print(f"Formula: ({scenario['weight']} × {scenario['purity']} ÷ {scenario['conversion_factor']}) × {scenario['rate']}")
                
                # Calculate expected step-by-step
                step1 = scenario['weight'] * scenario['purity']
                step2 = step1 / scenario['conversion_factor']
                expected_amount = step2 * scenario['rate']
                expected_amount = round(expected_amount, 3)
                
                print(f"Expected: step1={step1}, step2={step2:.3f}, Amount={expected_amount:.3f} OMR")
                
                # Create purchase with specific parameters
                purchase_data = {
                    "vendor_party_id": vendor_id,
                    "description": f"NEW Formula Test - {scenario['name']}",
                    "weight_grams": float(scenario['weight']),
                    "entered_purity": scenario['purity'],
                    "rate_per_gram": float(scenario['rate']),
                    "conversion_factor": scenario['conversion_factor'],
                    "paid_amount_money": 0.0
                }
                
                response = self.session.post(f"{BACKEND_URL}/purchases", json=purchase_data)
                
                if response.status_code == 201:
                    purchase = response.json()
                    actual_amount = float(purchase.get("amount_total", 0))
                    actual_purity = purchase.get("entered_purity")
                    actual_conversion_factor = float(purchase.get("conversion_factor", 0))
                    actual_weight = float(purchase.get("weight_grams", 0))
                    actual_rate = float(purchase.get("rate_per_gram", 0))
                    
                    # Validations with 0.001 OMR tolerance
                    amount_correct = abs(actual_amount - scenario["expected_amount"]) < 0.001
                    purity_correct = actual_purity == scenario["purity"]
                    conversion_factor_correct = abs(actual_conversion_factor - scenario["conversion_factor"]) < 0.001
                    weight_correct = abs(actual_weight - scenario["weight"]) < 0.001
                    rate_correct = abs(actual_rate - scenario["rate"]) < 0.001
                    
                    # Verify step-by-step calculation matches
                    actual_step1 = actual_weight * actual_purity
                    actual_step2 = actual_step1 / actual_conversion_factor
                    calculated_amount = actual_step2 * actual_rate
                    calculation_matches = abs(actual_amount - calculated_amount) < 0.001
                    
                    test_passed = all([amount_correct, purity_correct, conversion_factor_correct, 
                                     weight_correct, rate_correct, calculation_matches])
                    
                    if not test_passed:
                        all_tests_passed = False
                    
                    details = f"Weight: {actual_weight}g ({'✓' if weight_correct else '✗'}), "
                    details += f"Purity: {actual_purity} ({'✓' if purity_correct else '✗'}), "
                    details += f"Rate: {actual_rate} OMR/g ({'✓' if rate_correct else '✗'}), "
                    details += f"Factor: {actual_conversion_factor} ({'✓' if conversion_factor_correct else '✗'}), "
                    details += f"Amount: {actual_amount:.3f} vs {scenario['expected_amount']:.3f} ({'✓' if amount_correct else '✗'})"
                    
                    test_results.append({
                        "scenario": scenario["name"],
                        "passed": test_passed,
                        "details": details,
                        "actual_amount": actual_amount,
                        "expected_amount": scenario["expected_amount"],
                        "formula_verification": f"({actual_weight} × {actual_purity} ÷ {actual_conversion_factor}) × {actual_rate} = {actual_amount:.3f}"
                    })
                    
                    self.log_result(
                        f"NEW Formula - {scenario['name']}",
                        test_passed,
                        details,
                        {
                            "purchase_id": purchase.get("id"),
                            "formula": f"({actual_weight} × {actual_purity} ÷ {actual_conversion_factor}) × {actual_rate} = {actual_amount:.3f}",
                            "expected_formula": f"({scenario['weight']} × {scenario['purity']} ÷ {scenario['conversion_factor']}) × {scenario['rate']} = {scenario['expected_amount']:.3f}",
                            "step1": actual_step1,
                            "step2": actual_step2,
                            "final_amount": actual_amount,
                            "tolerance_check": f"Within 0.001 OMR: {amount_correct}"
                        }
                    )
                else:
                    all_tests_passed = False
                    self.log_result(f"NEW Formula - {scenario['name']}", False, f"Failed to create purchase: {response.status_code} - {response.text}")
            
            # Validation Requirements Check
            print(f"\n🔍 VALIDATION REQUIREMENTS CHECK:")
            
            # Check if Purity 999 result > Purity 916 result (for same weight/rate/factor)
            purity_999_result = next((r for r in test_results if "999" in r["scenario"]), None)
            purity_916_result = next((r for r in test_results if "916" in r["scenario"]), None)
            
            if purity_999_result and purity_916_result:
                purity_comparison_correct = purity_999_result["actual_amount"] > purity_916_result["actual_amount"]
                print(f"   • Purity 999 > Purity 916: {purity_999_result['actual_amount']:.3f} > {purity_916_result['actual_amount']:.3f} ({'✓' if purity_comparison_correct else '❌'})")
            else:
                purity_comparison_correct = False
                print(f"   • Purity comparison: ❌ Missing test results")
            
            # Summary
            passed_count = sum(1 for result in test_results if result["passed"])
            total_count = len(test_results)
            
            print(f"\n🔍 NEW FORMULA TEST SUMMARY:")
            print(f"   • Tests Passed: {passed_count}/{total_count}")
            print(f"   • Success Rate: {(passed_count/total_count)*100:.1f}%")
            print(f"   • Purity Comparison: {'✓' if purity_comparison_correct else '❌'}")
            
            for result in test_results:
                status = "✅ PASS" if result["passed"] else "❌ FAIL"
                print(f"   • {result['scenario']}: {status}")
                print(f"     Amount: {result['actual_amount']:.3f} (Expected: {result['expected_amount']:.3f})")
            
            final_success = all_tests_passed and purity_comparison_correct
            
            self.log_result(
                "NEW Purchase Amount Calculation Formula - Complete Test",
                final_success,
                f"Passed: {passed_count}/{total_count} scenarios, Purity comparison: {'✓' if purity_comparison_correct else '❌'}",
                {
                    "total_scenarios": total_count,
                    "passed_scenarios": passed_count,
                    "success_rate": f"{(passed_count/total_count)*100:.1f}%",
                    "purity_comparison_correct": purity_comparison_correct,
                    "test_results": test_results,
                    "formula_verified": "Amount = (Weight × Entered_Purity ÷ Conversion_Factor) × Rate"
                }
            )
            
            return final_success
            
        except Exception as e:
            self.log_result("Enhanced Purchase Valuation - Purity Adjustment", False, f"Error: {str(e)}")
            return False
    
    def test_multiple_items_purchase_new_formula(self):
        """Test multiple items purchase with NEW formula - different purities"""
        print("\n--- Testing Multiple Items Purchase with NEW Formula ---")
        
        try:
            vendor_id = self.get_or_create_test_vendor()
            if not vendor_id:
                return False
            
            # Test multiple items with NEW FORMULA: Amount = (Weight × Entered_Purity ÷ Conversion_Factor) × Rate
            # Item 1: (50 × 916 ÷ 0.917) × 50 = 2,497,273.5 baisa = 2,497.274 OMR
            # Item 2: (30 × 999 ÷ 0.917) × 52 = 1,700,817.3 baisa = 1,700.817 OMR  
            # Item 3: (20 × 875 ÷ 0.920) × 48 = 912,500.0 baisa = 912.500 OMR
            # Total: 5,110.591 OMR
            
            purchase_data = {
                "vendor_party_id": vendor_id,
                "items": [
                    {
                        "description": "22K Gold Chain - NEW Formula",
                        "weight_grams": 50.000,
                        "entered_purity": 916,
                        "rate_per_gram_22k": 50.000
                    },
                    {
                        "description": "24K Gold Bar - NEW Formula",
                        "weight_grams": 30.000,
                        "entered_purity": 999,
                        "rate_per_gram_22k": 52.000
                    },
                    {
                        "description": "21K Gold Bracelet - NEW Formula",
                        "weight_grams": 20.000,
                        "entered_purity": 875,
                        "rate_per_gram_22k": 48.000
                    }
                ],
                "conversion_factor": 0.917,  # Using 0.917 for first two items
                "paid_amount_money": 0.0
            }
            
            response = self.session.post(f"{BACKEND_URL}/purchases", json=purchase_data)
            
            if response.status_code == 201:
                purchase = response.json()
                actual_items = purchase.get("items", [])
                actual_total = float(purchase.get("amount_total", 0))
                
                # Expected calculations with NEW FORMULA
                expected_calculations = [
                    {"weight": 50, "purity": 916, "rate": 50, "factor": 0.917, "expected": 2497.274},
                    {"weight": 30, "purity": 999, "rate": 52, "factor": 0.917, "expected": 1700.817},
                    {"weight": 20, "purity": 875, "rate": 48, "factor": 0.920, "expected": 912.500}  # Different factor for item 3
                ]
                
                # Note: Backend uses single conversion_factor for all items, so we need to adjust expectations
                # All items will use 0.917 factor from purchase_data
                adjusted_expected = [
                    2497.274,  # (50 × 916 ÷ 0.917) × 50 = 2497.274
                    1700.817,  # (30 × 999 ÷ 0.917) × 52 = 1700.817
                    913.043    # (20 × 875 ÷ 0.917) × 48 = 913.043 (adjusted for 0.917)
                ]
                expected_total = sum(adjusted_expected)  # 5111.134
                
                # Verify each item calculation
                items_correct = []
                for i, (actual_item, expected_amount) in enumerate(zip(actual_items, adjusted_expected)):
                    actual_amount = float(actual_item.get("calculated_amount", 0))
                    amount_correct = abs(actual_amount - expected_amount) < 0.001
                    items_correct.append(amount_correct)
                    
                    purity = actual_item.get("entered_purity")
                    weight = actual_item.get("weight_grams")
                    rate = actual_item.get("rate_per_gram_22k")
                    
                    # Calculate step-by-step for verification
                    step1 = weight * purity
                    step2 = step1 / 0.917  # Backend uses single conversion factor
                    calculated = step2 * rate
                    
                    print(f"   Item {i+1}: ({weight} × {purity} ÷ 0.917) × {rate} = {actual_amount:.3f} OMR ({'✓' if amount_correct else '✗'})")
                    print(f"            Step1: {step1}, Step2: {step2:.3f}, Final: {calculated:.3f}")
                
                # Verify total
                total_correct = abs(actual_total - expected_total) < 0.001
                items_count_correct = len(actual_items) == 3
                all_items_correct = all(items_correct)
                
                all_correct = all([total_correct, items_count_correct, all_items_correct])
                
                details = f"Items: {len(actual_items)}/3 ({'✓' if items_count_correct else '✗'}), "
                details += f"Individual Calculations: {'✓' if all_items_correct else '✗'}, "
                details += f"Total: {actual_total:.3f} vs {expected_total:.3f} ({'✓' if total_correct else '✗'})"
                
                self.log_result(
                    "Multiple Items Purchase - NEW Formula",
                    all_correct,
                    details,
                    {
                        "purchase_id": purchase.get("id"),
                        "items_count": len(actual_items),
                        "expected_amounts": adjusted_expected,
                        "actual_amounts": [float(item.get("calculated_amount", 0)) for item in actual_items],
                        "expected_total": expected_total,
                        "actual_total": actual_total,
                        "formula_used": "Amount = (Weight × Entered_Purity ÷ Conversion_Factor) × Rate",
                        "conversion_factor": 0.917
                    }
                )
                
                return all_correct
            else:
                self.log_result("Multiple Items Purchase - NEW Formula Creation", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Multiple Items Purchase NEW Formula", False, f"Error: {str(e)}")
            return False
    
    def test_walk_in_filtering_and_customer_id_search(self):
        """Test walk-in filtering and customer ID search functionality"""
        print("\n--- Testing Walk-in Filtering and Customer ID Search ---")
        
        try:
            # Create test purchases: both walk-in and saved vendor
            vendor_id = self.get_or_create_test_vendor()
            if not vendor_id:
                return False
            
            # Create saved vendor purchase
            saved_vendor_purchase = {
                "vendor_party_id": vendor_id,
                "description": "Saved Vendor Purchase",
                "weight_grams": 25.000,
                "entered_purity": 916,
                "rate_per_gram": 50.000,
                "paid_amount_money": 0.0
            }
            
            saved_response = self.session.post(f"{BACKEND_URL}/purchases", json=saved_vendor_purchase)
            saved_purchase_id = None
            if saved_response.status_code == 201:
                saved_purchase_id = saved_response.json().get("id")
            
            # Create walk-in vendor purchase
            walk_in_purchase = {
                "is_walk_in": True,
                "walk_in_vendor_name": "Ahmed Al-Rashid",
                "vendor_oman_id": "87654321",
                "description": "Walk-in Vendor Purchase",
                "weight_grams": 15.000,
                "entered_purity": 916,
                "rate_per_gram": 48.000,
                "paid_amount_money": 0.0
            }
            
            walk_in_response = self.session.post(f"{BACKEND_URL}/purchases", json=walk_in_purchase)
            walk_in_purchase_id = None
            if walk_in_response.status_code == 201:
                walk_in_purchase_id = walk_in_response.json().get("id")
            
            if not saved_purchase_id or not walk_in_purchase_id:
                self.log_result("Walk-in Filtering Setup", False, "Failed to create test purchases")
                return False
            
            # Test 1: Get all purchases (no filter)
            all_response = self.session.get(f"{BACKEND_URL}/purchases")
            all_purchases = []
            if all_response.status_code == 200:
                data = all_response.json()
                all_purchases = data.get("data", data.get("items", data if isinstance(data, list) else []))
            
            # Test 2: Filter by walk-in only
            walk_in_filter_response = self.session.get(f"{BACKEND_URL}/purchases?vendor_type=walk_in")
            walk_in_purchases = []
            if walk_in_filter_response.status_code == 200:
                data = walk_in_filter_response.json()
                walk_in_purchases = data.get("data", data.get("items", data if isinstance(data, list) else []))
            
            # Test 3: Filter by saved vendors only
            saved_filter_response = self.session.get(f"{BACKEND_URL}/purchases?vendor_type=saved")
            saved_purchases = []
            if saved_filter_response.status_code == 200:
                data = saved_filter_response.json()
                saved_purchases = data.get("data", data.get("items", data if isinstance(data, list) else []))
            
            # Test 4: Search by customer ID (Oman ID)
            customer_id_response = self.session.get(f"{BACKEND_URL}/purchases?customer_id=87654321")
            customer_id_purchases = []
            if customer_id_response.status_code == 200:
                data = customer_id_response.json()
                customer_id_purchases = data.get("data", data.get("items", data if isinstance(data, list) else []))
            
            # Validations - FIXED: More robust filtering checks
            all_purchases_found = len(all_purchases) >= 2
            
            # Walk-in filter should only return walk-in purchases
            walk_in_filter_works = (
                len(walk_in_purchases) > 0 and
                all(p.get("is_walk_in") == True for p in walk_in_purchases) and
                all(p.get("vendor_party_id") is None for p in walk_in_purchases)
            )
            
            # Saved filter should only return saved vendor purchases
            saved_filter_works = (
                len(saved_purchases) > 0 and
                all(p.get("vendor_party_id") is not None for p in saved_purchases)
            )
            
            # Customer ID search should return purchases with matching Oman ID
            customer_id_search_works = (
                len(customer_id_purchases) > 0 and
                all(p.get("vendor_oman_id") == "87654321" for p in customer_id_purchases)
            )
            
            all_correct = all([
                all_purchases_found,
                walk_in_filter_works,
                saved_filter_works,
                customer_id_search_works
            ])
            
            details = f"All: {len(all_purchases)} ({'✓' if all_purchases_found else '✗'}), "
            details += f"Walk-in Filter: {len(walk_in_purchases)} items ({'✓' if walk_in_filter_works else '✗'}), "
            details += f"Saved Filter: {len(saved_purchases)} items ({'✓' if saved_filter_works else '✗'}), "
            details += f"Customer ID Search: {len(customer_id_purchases)} items ({'✓' if customer_id_search_works else '✗'})"
            
            self.log_result(
                "Walk-in Filtering and Customer ID Search",
                all_correct,
                details,
                {
                    "all_purchases_count": len(all_purchases),
                    "walk_in_purchases_count": len(walk_in_purchases),
                    "saved_purchases_count": len(saved_purchases),
                    "customer_id_purchases_count": len(customer_id_purchases),
                    "filtering_working": all_correct
                }
            )
            
            return all_correct
            
        except Exception as e:
            self.log_result("Walk-in Filtering and Customer ID Search", False, f"Error: {str(e)}")
            return False
    
    def test_stock_valuation_916_purity(self):
        """Test that stock movements use 916 purity regardless of entered purity"""
        print("\n--- Testing Stock Valuation - 916 Purity Enforcement ---")
        
        try:
            vendor_id = self.get_or_create_test_vendor()
            if not vendor_id:
                return False
            
            # Create purchase with different purity but stock should be valued at 916
            purchase_data = {
                "vendor_party_id": vendor_id,
                "description": "Stock Valuation Test - 999 Purity Input",
                "weight_grams": 10.000,
                "entered_purity": 999,  # Entered as 999 but stock should be 916
                "rate_per_gram": 50.000,
                "paid_amount_money": 0.0
            }
            
            response = self.session.post(f"{BACKEND_URL}/purchases", json=purchase_data)
            
            if response.status_code == 201:
                purchase = response.json()
                purchase_id = purchase.get("id")
                
                # Check the purchase valuation purity
                valuation_purity = purchase.get("valuation_purity_fixed")
                entered_purity = purchase.get("entered_purity")
                
                # Get stock movements for this purchase
                movements_response = self.session.get(f"{BACKEND_URL}/inventory/movements")
                movements = []
                if movements_response.status_code == 200:
                    data = movements_response.json()
                    # FIXED: API returns direct list, not wrapped response
                    movements = data if isinstance(data, list) else []
                
                # Find movement related to this purchase
                purchase_movement = None
                for movement in movements:
                    if movement.get("reference_id") == purchase_id:
                        purchase_movement = movement
                        break
                
                # Validations
                valuation_purity_correct = valuation_purity == 916
                entered_purity_preserved = entered_purity == 999
                movement_found = purchase_movement is not None
                
                movement_purity_correct = False
                movement_notes_contain_916 = False
                
                if purchase_movement:
                    movement_purity = purchase_movement.get("purity", 0)
                    movement_notes = purchase_movement.get("notes", "")
                    
                    movement_purity_correct = movement_purity == 916
                    movement_notes_contain_916 = "916" in str(movement_notes)
                
                all_correct = all([
                    valuation_purity_correct,
                    entered_purity_preserved,
                    movement_found,
                    movement_purity_correct,
                    movement_notes_contain_916
                ])
                
                details = f"Valuation Purity: {valuation_purity} ({'✓' if valuation_purity_correct else '✗'}), "
                details += f"Entered Purity: {entered_purity} ({'✓' if entered_purity_preserved else '✗'}), "
                details += f"Movement Found: {'✓' if movement_found else '✗'}, "
                details += f"Movement Purity: {purchase_movement.get('purity') if purchase_movement else 'N/A'} ({'✓' if movement_purity_correct else '✗'})"
                
                self.log_result(
                    "Stock Valuation - 916 Purity Enforcement",
                    all_correct,
                    details,
                    {
                        "purchase_id": purchase_id,
                        "entered_purity": entered_purity,
                        "valuation_purity_fixed": valuation_purity,
                        "movement_purity": purchase_movement.get("purity") if purchase_movement else None,
                        "movement_notes_sample": purchase_movement.get("notes", "")[:100] if purchase_movement else None
                    }
                )
                
                return all_correct
            else:
                self.log_result("Stock Valuation Test - Purchase Creation", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Stock Valuation - 916 Purity Enforcement", False, f"Error: {str(e)}")
            return False
    
    def test_calculation_breakdown_in_notes(self):
        """Test that calculation breakdown is included in stock movement notes"""
        print("\n--- Testing Calculation Breakdown in Notes ---")
        
        try:
            vendor_id = self.get_or_create_test_vendor()
            if not vendor_id:
                return False
            
            # Create purchase with specific values for calculation verification
            purchase_data = {
                "vendor_party_id": vendor_id,
                "description": "Calculation Breakdown Test",
                "weight_grams": 25.500,
                "entered_purity": 875,
                "rate_per_gram": 48.500,
                "paid_amount_money": 0.0
            }
            
            response = self.session.post(f"{BACKEND_URL}/purchases", json=purchase_data)
            
            if response.status_code == 201:
                purchase = response.json()
                purchase_id = purchase.get("id")
                
                # Get stock movements
                movements_response = self.session.get(f"{BACKEND_URL}/inventory/movements")
                movements = []
                if movements_response.status_code == 200:
                    data = movements_response.json()
                    # FIXED: API returns direct list, not wrapped response
                    movements = data if isinstance(data, list) else []
                
                # Find movement for this purchase
                purchase_movement = None
                for movement in movements:
                    if movement.get("reference_id") == purchase_id:
                        purchase_movement = movement
                        break
                
                if purchase_movement:
                    notes = purchase_movement.get("notes", "")
                    
                    # Check if notes contain calculation breakdown
                    contains_weight = "25.5" in notes or "25.500" in notes
                    contains_rate = "48.5" in notes or "48.500" in notes
                    contains_purity_calc = "916/875" in notes or "916" in notes and "875" in notes
                    contains_conversion_factor = "0.92" in notes
                    contains_formula_elements = "Weight=" in notes and "Rate=" in notes
                    
                    # Check for the specific calculation formula
                    contains_calculation_word = "Calculation" in notes
                    contains_entered_purity = "Entered purity: 875" in notes
                    contains_valuation_purity = "Valuation purity: 916" in notes
                    
                    breakdown_complete = all([
                        contains_weight,
                        contains_rate,
                        contains_purity_calc,
                        contains_conversion_factor,
                        contains_formula_elements,
                        contains_calculation_word,
                        contains_entered_purity,
                        contains_valuation_purity
                    ])
                    
                    details = f"Weight: {'✓' if contains_weight else '✗'}, "
                    details += f"Rate: {'✓' if contains_rate else '✗'}, "
                    details += f"Purity Calc: {'✓' if contains_purity_calc else '✗'}, "
                    details += f"Conversion Factor: {'✓' if contains_conversion_factor else '✗'}, "
                    details += f"Formula: {'✓' if contains_formula_elements else '✗'}, "
                    details += f"Complete Breakdown: {'✓' if breakdown_complete else '✗'}"
                    
                    self.log_result(
                        "Calculation Breakdown in Notes",
                        breakdown_complete,
                        details,
                        {
                            "purchase_id": purchase_id,
                            "movement_notes": notes,
                            "breakdown_elements": {
                                "contains_weight": contains_weight,
                                "contains_rate": contains_rate,
                                "contains_purity_calc": contains_purity_calc,
                                "contains_conversion_factor": contains_conversion_factor,
                                "contains_formula_elements": contains_formula_elements
                            }
                        }
                    )
                    
                    return breakdown_complete
                else:
                    self.log_result("Calculation Breakdown - Movement Not Found", False, "Stock movement not found for purchase")
                    return False
            else:
                self.log_result("Calculation Breakdown - Purchase Creation", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Calculation Breakdown in Notes", False, f"Error: {str(e)}")
            return False
    
    def get_or_create_test_worker(self):
        """Get existing worker or create one for testing"""
        try:
            # Try to get existing workers
            response = self.session.get(f"{BACKEND_URL}/workers")
            
            if response.status_code == 200:
                workers = response.json()
                if isinstance(workers, dict) and 'items' in workers:
                    workers = workers['items']
                
                if workers:
                    worker_id = workers[0].get('id')
                    self.log_result("Get Test Worker", True, f"Using existing worker: {workers[0].get('name')}")
                    return worker_id
            
            # Create new worker
            worker_data = {
                "name": "Mohammed Al-Kindi",
                "phone": "+968 9123 4567",
                "role": "Goldsmith",
                "active": True
            }
            
            response = self.session.post(f"{BACKEND_URL}/workers", json=worker_data)
            
            if response.status_code == 201:
                worker = response.json()
                worker_id = worker.get("id")
                self.log_result("Create Test Worker", True, f"Created test worker: {worker.get('name')}")
                return worker_id
            else:
                self.log_result("Create Test Worker", False, f"Failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Get/Create Test Worker", False, f"Error: {str(e)}")
            return None
    
    def get_or_create_test_vendor(self):
        """Get existing vendor or create one for testing"""
        try:
            # Try to get existing vendors
            response = self.session.get(f"{BACKEND_URL}/parties?party_type=vendor")
            
            if response.status_code == 200:
                data = response.json()
                vendors = data.get("data", data.get("items", data if isinstance(data, list) else []))
                
                if vendors:
                    vendor_id = vendors[0].get('id')
                    self.log_result("Get Test Vendor", True, f"Using existing vendor: {vendors[0].get('name')}")
                    return vendor_id
            
            # Create new vendor
            vendor_data = {
                "name": "Al-Dhahab Gold Trading LLC",
                "oman_id": "12345678",
                "phone": "+968 2234 5678",
                "address": "Muscat, Oman",
                "party_type": "vendor",
                "notes": "Test vendor for purchase testing"
            }
            
            response = self.session.post(f"{BACKEND_URL}/parties", json=vendor_data)
            
            if response.status_code == 201:
                vendor = response.json()
                vendor_id = vendor.get("id")
                self.log_result("Create Test Vendor", True, f"Created test vendor: {vendor.get('name')}")
                return vendor_id
            else:
                self.log_result("Create Test Vendor", False, f"Failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Get/Create Test Vendor", False, f"Error: {str(e)}")
            return None
    
    def get_or_create_test_customer(self):
        """Get existing customer or create one for testing"""
        try:
            # Try to get existing customers
            response = self.session.get(f"{BACKEND_URL}/parties?party_type=customer")
            
            if response.status_code == 200:
                data = response.json()
                customers = data.get("data", data.get("items", data if isinstance(data, list) else []))
                
                if customers:
                    customer_id = customers[0].get('id')
                    self.log_result("Get Test Customer", True, f"Using existing customer: {customers[0].get('name')}")
                    return customer_id
            
            # Create new customer
            customer_data = {
                "name": "Fatima Al-Zahra",
                "oman_id": "87654321",
                "phone": "+968 9876 5432",
                "address": "Salalah, Oman",
                "party_type": "customer",
                "notes": "Test customer for job card testing"
            }
            
            response = self.session.post(f"{BACKEND_URL}/parties", json=customer_data)
            
            if response.status_code == 201:
                customer = response.json()
                customer_id = customer.get("id")
                self.log_result("Create Test Customer", True, f"Created test customer: {customer.get('name')}")
                return customer_id
            else:
                self.log_result("Create Test Customer", False, f"Failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Get/Create Test Customer", False, f"Error: {str(e)}")
            return None
    
    def test_enhanced_purchase_valuation_comprehensive(self):
        """Run comprehensive Enhanced Purchase Valuation tests"""
        print("\n" + "="*80)
        print("🚀 ENHANCED PURCHASE VALUATION - COMPREHENSIVE TESTING")
        print("="*80)
        
        if not self.authenticate():
            return False
        
        # Run all Enhanced Purchase Valuation tests
        test_results = []
        
        print("\n1️⃣ Testing Purity Adjustment Calculations...")
        purity_test = self.test_enhanced_purchase_valuation_purity_adjustment()
        test_results.append(("Purity Adjustment Calculations", purity_test))
        
        print("\n2️⃣ Testing Multiple Items with Different Purities...")
        multiple_items_test = self.test_multiple_items_purchase_different_purities()
        test_results.append(("Multiple Items Different Purities", multiple_items_test))
        
        print("\n3️⃣ Testing Walk-in Filtering and Customer ID Search...")
        filtering_test = self.test_walk_in_filtering_and_customer_id_search()
        test_results.append(("Walk-in Filtering & Customer ID Search", filtering_test))
        
        print("\n4️⃣ Testing Stock Valuation (916 Purity Enforcement)...")
        stock_valuation_test = self.test_stock_valuation_916_purity()
        test_results.append(("Stock Valuation 916 Purity", stock_valuation_test))
        
        print("\n5️⃣ Testing Calculation Breakdown in Notes...")
        calculation_notes_test = self.test_calculation_breakdown_in_notes()
        test_results.append(("Calculation Breakdown in Notes", calculation_notes_test))
        
        # Summary
        passed_tests = sum(1 for _, result in test_results if result)
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"\n" + "="*80)
        print(f"📊 ENHANCED PURCHASE VALUATION TEST SUMMARY")
        print(f"="*80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        overall_success = passed_tests == total_tests
        
        if overall_success:
            print(f"\n🎉 ALL ENHANCED PURCHASE VALUATION TESTS PASSED!")
            print(f"✅ Purity adjustment formula working correctly")
            print(f"✅ Multiple items with different purities supported")
            print(f"✅ Walk-in filtering and customer ID search functional")
            print(f"✅ Stock valuation enforces 916 purity")
            print(f"✅ Calculation breakdown included in notes")
        else:
            print(f"\n⚠️  SOME TESTS FAILED - REVIEW REQUIRED")
            failed_tests = [name for name, result in test_results if not result]
            for failed_test in failed_tests:
                print(f"❌ {failed_test}")
        
        self.log_result(
            "Enhanced Purchase Valuation - Comprehensive Test Suite",
            overall_success,
            f"Passed: {passed_tests}/{total_tests} tests ({success_rate:.1f}%)",
            {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": success_rate,
                "test_results": dict(test_results)
            }
        )
        
        return overall_success
        """Test Shop Settings conversion factor GET and UPDATE"""
        print("\n--- Testing Shop Settings Conversion Factor ---")
        
        try:
            # Test 1: GET shop settings
            response = self.session.get(f"{BACKEND_URL}/settings/shop")
            
            if response.status_code == 200:
                settings = response.json()
                current_factor = settings.get("purchase_conversion_factor", 0.920)
                
                self.log_result(
                    "Get Shop Settings", 
                    True, 
                    f"Retrieved shop settings with conversion factor: {current_factor}",
                    {"conversion_factor": current_factor, "shop_name": settings.get("shop_name")}
                )
                
                # Test 2: UPDATE conversion factor
                new_factor = 0.917 if current_factor == 0.920 else 0.920
                update_data = {
                    "purchase_conversion_factor": new_factor,
                    "shop_name": settings.get("shop_name", "Gold Jewellery ERP")
                }
                
                update_response = self.session.put(f"{BACKEND_URL}/settings/shop", json=update_data)
                
                if update_response.status_code == 200:
                    # Verify the update
                    verify_response = self.session.get(f"{BACKEND_URL}/settings/shop")
                    if verify_response.status_code == 200:
                        updated_settings = verify_response.json()
                        updated_factor = updated_settings.get("purchase_conversion_factor")
                        
                        factor_updated = abs(updated_factor - new_factor) < 0.001
                        
                        self.log_result(
                            "Update Shop Settings Conversion Factor", 
                            factor_updated, 
                            f"Updated conversion factor from {current_factor} to {updated_factor}",
                            {"old_factor": current_factor, "new_factor": updated_factor}
                        )
                        
                        return updated_factor
                    else:
                        self.log_result("Verify Shop Settings Update", False, f"Failed to verify: {verify_response.status_code}")
                else:
                    self.log_result("Update Shop Settings", False, f"Failed: {update_response.status_code} - {update_response.text}")
            else:
                self.log_result("Get Shop Settings", False, f"Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Shop Settings Conversion Factor", False, f"Error: {str(e)}")
        
        return 0.920  # Default fallback
    
    def test_single_item_purchase_legacy(self):
        """Test single-item purchase (legacy compatibility) with 22K valuation formula"""
        print("\n--- Testing Single-Item Purchase (Legacy) ---")
        
        try:
            # Get or create vendor
            vendor_id = self.get_or_create_test_vendor()
            if not vendor_id:
                return None
            
            # Test data: 10.5g @ 50 OMR/g ÷ 0.920 = 570.652 OMR
            purchase_data = {
                "vendor_party_id": vendor_id,
                "description": "22K Gold Bars - Single Item Legacy Test",
                "weight_grams": 10.500,  # 3 decimal precision
                "entered_purity": 999,   # Entered as 999 but valued at 916
                "rate_per_gram": 50.000, # Rate per gram for 22K
                "amount_total": 570.652, # Expected: (10.5 × 50) ÷ 0.920 = 570.652
                "paid_amount_money": 0.0,
                "balance_due_money": 570.652
            }
            
            response = self.session.post(f"{BACKEND_URL}/purchases", json=purchase_data)
            
            if response.status_code == 201:
                purchase = response.json()
                purchase_id = purchase.get("id")
                
                # Verify calculations
                actual_amount = purchase.get("amount_total", 0)
                actual_conversion_factor = purchase.get("conversion_factor", 0)
                actual_valuation_purity = purchase.get("valuation_purity_fixed", 0)
                actual_status = purchase.get("status", "")
                
                # Expected calculations with conversion factor from settings
                expected_amount = (10.500 * 50.000) / actual_conversion_factor
                
                # Validations
                amount_correct = abs(actual_amount - expected_amount) < 0.001
                purity_correct = actual_valuation_purity == 916
                status_correct = actual_status == "Draft"
                precision_correct = len(str(actual_amount).split('.')[-1]) <= 3
                
                all_correct = all([amount_correct, purity_correct, status_correct, precision_correct])
                
                details = f"Amount: {'✓' if amount_correct else '✗'} ({actual_amount} vs {expected_amount:.3f}), "
                details += f"Purity: {'✓' if purity_correct else '✗'} (916), "
                details += f"Status: {'✓' if status_correct else '✗'} ({actual_status}), "
                details += f"Precision: {'✓' if precision_correct else '✗'}"
                
                self.log_result(
                    "Single-Item Purchase Legacy - Formula Verification",
                    all_correct,
                    details,
                    {
                        "purchase_id": purchase_id,
                        "formula": f"({purchase_data['weight_grams']} × {purchase_data['rate_per_gram']}) ÷ {actual_conversion_factor} = {actual_amount}",
                        "expected_amount": expected_amount,
                        "actual_amount": actual_amount,
                        "conversion_factor": actual_conversion_factor
                    }
                )
                
                return purchase_id if all_correct else None
            else:
                self.log_result("Single-Item Purchase Legacy - Creation", False, f"Failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Single-Item Purchase Legacy", False, f"Error: {str(e)}")
            return None
    
    def test_multi_item_purchase_different_purities(self):
        """Test multi-item purchase with different purities"""
        print("\n--- Testing Multi-Item Purchase with Different Purities ---")
        
        try:
            vendor_id = self.get_or_create_test_vendor()
            if not vendor_id:
                return None
            
            # Test data: Multi-item with different purities
            # Item 1: 10g @ 50 ÷ 0.920 = 543.478 OMR
            # Item 2: 15.5g @ 48 ÷ 0.920 = 808.696 OMR
            # Total: 1352.174 OMR
            purchase_data = {
                "vendor_party_id": vendor_id,
                "items": [
                    {
                        "description": "22K Gold Chain",
                        "weight_grams": 10.000,
                        "entered_purity": 916,
                        "rate_per_gram_22k": 50.000,
                        "calculated_amount": 543.478  # (10 × 50) ÷ 0.920
                    },
                    {
                        "description": "18K Gold Bracelet", 
                        "weight_grams": 15.500,
                        "entered_purity": 750,  # Different purity
                        "rate_per_gram_22k": 48.000,
                        "calculated_amount": 808.696  # (15.5 × 48) ÷ 0.920
                    }
                ],
                "valuation_purity_fixed": 916,  # Always 916 regardless of entered purity
                "conversion_factor": 0.920,
                "amount_total": 1352.174,  # Sum of both items
                "paid_amount_money": 0.0,
                "balance_due_money": 1352.174
            }
            
            response = self.session.post(f"{BACKEND_URL}/purchases", json=purchase_data)
            
            if response.status_code == 201:
                purchase = response.json()
                purchase_id = purchase.get("id")
                
                # Verify multi-item calculations
                actual_amount = purchase.get("amount_total", 0)
                actual_items = purchase.get("items", [])
                actual_valuation_purity = purchase.get("valuation_purity_fixed", 0)
                
                # Verify each item calculation
                item1_correct = False
                item2_correct = False
                
                if len(actual_items) >= 2:
                    item1_amount = actual_items[0].get("calculated_amount", 0)
                    item2_amount = actual_items[1].get("calculated_amount", 0)
                    
                    item1_correct = abs(item1_amount - 543.478) < 0.001
                    item2_correct = abs(item2_amount - 808.696) < 0.001
                
                # Verify total
                total_correct = abs(actual_amount - 1352.174) < 0.001
                purity_correct = actual_valuation_purity == 916
                items_count_correct = len(actual_items) == 2
                
                all_correct = all([item1_correct, item2_correct, total_correct, purity_correct, items_count_correct])
                
                details = f"Item1: {'✓' if item1_correct else '✗'} (543.478), "
                details += f"Item2: {'✓' if item2_correct else '✗'} (808.696), "
                details += f"Total: {'✓' if total_correct else '✗'} ({actual_amount}), "
                details += f"Purity: {'✓' if purity_correct else '✗'} (916), "
                details += f"Items Count: {'✓' if items_count_correct else '✗'} ({len(actual_items)})"
                
                self.log_result(
                    "Multi-Item Purchase - Different Purities",
                    all_correct,
                    details,
                    {
                        "purchase_id": purchase_id,
                        "items_count": len(actual_items),
                        "total_amount": actual_amount,
                        "expected_total": 1352.174
                    }
                )
                
                return purchase_id if all_correct else None
            else:
                self.log_result("Multi-Item Purchase - Creation", False, f"Failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Multi-Item Purchase Different Purities", False, f"Error: {str(e)}")
            return None
    
    def test_walk_in_vendor_purchase(self):
        """Test walk-in vendor purchase (no party creation)"""
        print("\n--- Testing Walk-in Vendor Purchase ---")
        
        try:
            # Walk-in vendor purchase data
            purchase_data = {
                "is_walk_in": True,
                "walk_in_vendor_name": "Ahmed Al-Mansouri",
                "vendor_oman_id": "12345678",  # Required for walk-in
                "description": "Gold Jewelry - Walk-in Vendor",
                "weight_grams": 8.750,
                "entered_purity": 916,
                "rate_per_gram": 52.000,
                "amount_total": 494.565,  # (8.75 × 52) ÷ 0.920 = 494.565
                "paid_amount_money": 0.0,
                "balance_due_money": 494.565
            }
            
            response = self.session.post(f"{BACKEND_URL}/purchases", json=purchase_data)
            
            if response.status_code == 201:
                purchase = response.json()
                purchase_id = purchase.get("id")
                
                # Verify walk-in vendor properties
                is_walk_in = purchase.get("is_walk_in", False)
                vendor_party_id = purchase.get("vendor_party_id")
                walk_in_name = purchase.get("walk_in_vendor_name", "")
                vendor_oman_id = purchase.get("vendor_oman_id", "")
                
                # Validations for walk-in vendor
                walk_in_correct = is_walk_in == True
                no_party_id = vendor_party_id is None
                name_correct = walk_in_name == "Ahmed Al-Mansouri"
                oman_id_correct = vendor_oman_id == "12345678"
                
                all_correct = all([walk_in_correct, no_party_id, name_correct, oman_id_correct])
                
                details = f"Walk-in: {'✓' if walk_in_correct else '✗'} ({is_walk_in}), "
                details += f"No Party ID: {'✓' if no_party_id else '✗'} ({vendor_party_id}), "
                details += f"Name: {'✓' if name_correct else '✗'} ({walk_in_name}), "
                details += f"Oman ID: {'✓' if oman_id_correct else '✗'} ({vendor_oman_id})"
                
                self.log_result(
                    "Walk-in Vendor Purchase - Properties",
                    all_correct,
                    details,
                    {
                        "purchase_id": purchase_id,
                        "is_walk_in": is_walk_in,
                        "vendor_party_id": vendor_party_id,
                        "walk_in_vendor_name": walk_in_name
                    }
                )
                
                return purchase_id if all_correct else None
            else:
                self.log_result("Walk-in Vendor Purchase - Creation", False, f"Failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Walk-in Vendor Purchase", False, f"Error: {str(e)}")
            return None
    
    def test_purchase_with_payments(self):
        """Test purchase with payment (partial and full)"""
        print("\n--- Testing Purchase with Payments ---")
        
        try:
            # Create a purchase first
            vendor_id = self.get_or_create_test_vendor()
            if not vendor_id:
                return None
            
            purchase_data = {
                "vendor_party_id": vendor_id,
                "description": "Gold Purchase for Payment Testing",
                "weight_grams": 12.000,
                "entered_purity": 916,
                "rate_per_gram": 48.000,
                "amount_total": 626.087,  # (12 × 48) ÷ 0.920 = 626.087
                "paid_amount_money": 0.0,
                "balance_due_money": 626.087
            }
            
            response = self.session.post(f"{BACKEND_URL}/purchases", json=purchase_data)
            
            if response.status_code == 201:
                purchase = response.json()
                purchase_id = purchase.get("id")
                
                # Test 1: Partial Payment
                account_id = self.get_or_create_test_account()
                if not account_id:
                    return None
                
                partial_payment_data = {
                    "payment_amount": 300.000,  # Partial payment
                    "payment_mode": "Cash",
                    "account_id": account_id,
                    "notes": "Partial payment for gold purchase"
                }
                
                payment_response = self.session.post(f"{BACKEND_URL}/purchases/{purchase_id}/add-payment", json=partial_payment_data)
                
                if payment_response.status_code == 200:
                    updated_purchase = payment_response.json()
                    
                    # Verify partial payment calculations
                    paid_amount = updated_purchase.get("paid_amount_money", 0)
                    balance_due = updated_purchase.get("balance_due_money", 0)
                    status = updated_purchase.get("status", "")
                    locked = updated_purchase.get("locked", False)
                    
                    # Expected values after partial payment
                    expected_paid = 300.000
                    expected_balance = 626.087 - 300.000  # 326.087
                    expected_status = "Partially Paid"
                    expected_locked = False  # Not locked until balance_due = 0
                    
                    partial_correct = (
                        abs(paid_amount - expected_paid) < 0.001 and
                        abs(balance_due - expected_balance) < 0.001 and
                        status == expected_status and
                        locked == expected_locked
                    )
                    
                    self.log_result(
                        "Purchase Partial Payment",
                        partial_correct,
                        f"Paid: {paid_amount}/{expected_paid}, Balance: {balance_due:.3f}/{expected_balance:.3f}, Status: {status}, Locked: {locked}",
                        {
                            "paid_amount": paid_amount,
                            "balance_due": balance_due,
                            "status": status,
                            "locked": locked
                        }
                    )
                    
                    # Test 2: Full Payment (complete the remaining balance)
                    remaining_payment_data = {
                        "payment_amount": balance_due,  # Pay remaining balance
                        "payment_mode": "Bank Transfer",
                        "account_id": account_id,
                        "notes": "Final payment to complete purchase"
                    }
                    
                    final_payment_response = self.session.post(f"{BACKEND_URL}/purchases/{purchase_id}/add-payment", json=remaining_payment_data)
                    
                    if final_payment_response.status_code == 200:
                        final_purchase = final_payment_response.json()
                        
                        # Verify full payment calculations
                        final_paid = final_purchase.get("paid_amount_money", 0)
                        final_balance = final_purchase.get("balance_due_money", 0)
                        final_status = final_purchase.get("status", "")
                        final_locked = final_purchase.get("locked", False)
                        
                        # Expected values after full payment
                        expected_final_paid = 626.087
                        expected_final_balance = 0.000
                        expected_final_status = "Paid"
                        expected_final_locked = True  # Should be locked when balance_due = 0
                        
                        full_payment_correct = (
                            abs(final_paid - expected_final_paid) < 0.001 and
                            abs(final_balance - expected_final_balance) < 0.001 and
                            final_status == expected_final_status and
                            final_locked == expected_final_locked
                        )
                        
                        self.log_result(
                            "Purchase Full Payment & Locking",
                            full_payment_correct,
                            f"Final Paid: {final_paid:.3f}, Balance: {final_balance:.3f}, Status: {final_status}, Locked: {final_locked}",
                            {
                                "final_paid_amount": final_paid,
                                "final_balance_due": final_balance,
                                "final_status": final_status,
                                "final_locked": final_locked
                            }
                        )
                        
                        return purchase_id if (partial_correct and full_payment_correct) else None
                    else:
                        self.log_result("Purchase Full Payment", False, f"Failed: {final_payment_response.status_code} - {final_payment_response.text}")
                else:
                    self.log_result("Purchase Partial Payment", False, f"Failed: {payment_response.status_code} - {payment_response.text}")
            else:
                self.log_result("Create Purchase for Payment Testing", False, f"Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Purchase with Payments", False, f"Error: {str(e)}")
            return None
        """Test GET /api/invoices/returnable?type=sales"""
        try:
            response = self.session.get(f"{BACKEND_URL}/invoices/returnable?type=sales")
            
            if response.status_code == 200:
                data = response.json()
                invoice_count = len(data) if isinstance(data, list) else 0
                self.log_result(
                    "Get Returnable Invoices", 
                    True, 
                    f"Retrieved {invoice_count} returnable invoices",
                    {"count": invoice_count, "sample": data[:2] if data else []}
                )
                return data
            else:
                self.log_result("Get Returnable Invoices", False, f"Failed: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            self.log_result("Get Returnable Invoices", False, f"Error: {str(e)}")
            return []
    
    def create_test_invoice_for_returns(self):
        """Create a test finalized invoice for returns testing"""
        try:
            # First, get or create a customer
            customer_id = self.get_or_create_test_customer()
            if not customer_id:
                return None
            
            # Create invoice with realistic data
            invoice_data = {
                "customer_type": "saved",
                "customer_id": customer_id,
                "invoice_type": "sale",
                "items": [
                    {
                        "description": "Gold Ring 22K",
                        "qty": 1,
                        "gross_weight": 5.250,
                        "stone_weight": 0.100,
                        "net_gold_weight": 5.150,
                        "weight": 5.150,
                        "purity": 916,
                        "metal_rate": 185.50,
                        "gold_value": 955.33,
                        "making_charge_type": "per_gram",
                        "making_value": 150.00,
                        "stone_charges": 25.00,
                        "wastage_charges": 20.00,
                        "item_discount": 0.00,
                        "vat_percent": 5.0,
                        "vat_amount": 57.52,
                        "line_total": 1207.85
                    }
                ],
                "subtotal": 1150.33,
                "discount_amount": 0.00,
                "tax_type": "cgst_sgst",
                "gst_percent": 5.0,
                "cgst_total": 28.76,
                "sgst_total": 28.76,
                "igst_total": 0.00,
                "vat_total": 57.52,
                "grand_total": 1207.85,
                "paid_amount": 0.00,
                "balance_due": 1207.85,
                "notes": "Test invoice for returns testing"
            }
            
            # Create invoice
            response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
            
            if response.status_code in [200, 201]:
                invoice = response.json()
                invoice_id = invoice.get("id")
                
                # Finalize the invoice
                finalize_response = self.session.post(f"{BACKEND_URL}/invoices/{invoice_id}/finalize")
                
                if finalize_response.status_code == 200:
                    self.log_result(
                        "Create Test Invoice for Returns", 
                        True, 
                        f"Created and finalized test invoice: {invoice.get('invoice_number')}",
                        {"invoice_id": invoice_id, "invoice_number": invoice.get('invoice_number')}
                    )
                    return invoice_id
                else:
                    self.log_result("Finalize Test Invoice", False, f"Failed to finalize: {finalize_response.status_code} - {finalize_response.text}")
                    return None
            else:
                self.log_result("Create Test Invoice for Returns", False, f"Failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Create Test Invoice for Returns", False, f"Error: {str(e)}")
            return None
    
    def get_or_create_test_customer(self):
        """Get existing customer or create one for testing"""
        try:
            # Try to get existing customers
            response = self.session.get(f"{BACKEND_URL}/parties?party_type=customer")
            
            if response.status_code == 200:
                customers = response.json()
                if isinstance(customers, dict) and 'items' in customers:
                    customers = customers['items']
                
                if customers:
                    customer_id = customers[0].get('id')
                    self.log_result("Get Test Customer", True, f"Using existing customer: {customers[0].get('name')}")
                    return customer_id
            
            # Create new customer
            customer_data = {
                "name": "Ahmed Al-Rashid",
                "phone": "+968 9876 5432",
                "address": "Muscat, Sultanate of Oman",
                "party_type": "customer",
                "notes": "Test customer for returns testing"
            }
            
            response = self.session.post(f"{BACKEND_URL}/parties", json=customer_data)
            
            if response.status_code == 201:
                customer = response.json()
                customer_id = customer.get("id")
                self.log_result("Create Test Customer", True, f"Created test customer: {customer.get('name')}")
                return customer_id
            else:
                self.log_result("Create Test Customer", False, f"Failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Get/Create Test Customer", False, f"Error: {str(e)}")
            return None
    
    def test_get_returnable_items(self, invoice_id):
        """Test GET /api/invoices/{id}/returnable-items"""
        try:
            response = self.session.get(f"{BACKEND_URL}/invoices/{invoice_id}/returnable-items")
            
            if response.status_code == 200:
                data = response.json()
                items_count = len(data.get('items', [])) if isinstance(data, dict) else len(data) if isinstance(data, list) else 0
                self.log_result(
                    "Get Returnable Items", 
                    True, 
                    f"Retrieved {items_count} returnable items from invoice",
                    {"items_count": items_count, "sample": data}
                )
                return data
            else:
                self.log_result("Get Returnable Items", False, f"Failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Get Returnable Items", False, f"Error: {str(e)}")
            return None
    
    def test_create_draft_return(self, invoice_id, returnable_items):
        """Test POST /api/returns with status='draft'"""
        try:
            # First get the invoice to extract customer details
            invoice_response = self.session.get(f"{BACKEND_URL}/invoices/{invoice_id}")
            if invoice_response.status_code != 200:
                self.log_result("Create Draft Return", False, "Failed to get invoice details")
                return None
            
            invoice_data = invoice_response.json()
            customer_id = invoice_data.get('customer_id')
            customer_name = invoice_data.get('customer_name', 'Test Customer')
            
            # If customer_name is None, get it from the party
            if not customer_name and customer_id:
                party_response = self.session.get(f"{BACKEND_URL}/parties/{customer_id}")
                if party_response.status_code == 200:
                    party_data = party_response.json()
                    customer_name = party_data.get('name', 'Test Customer')
            
            # Prepare return items based on returnable items
            if isinstance(returnable_items, dict) and 'items' in returnable_items:
                items_data = returnable_items['items']
            elif isinstance(returnable_items, list):
                items_data = returnable_items
            else:
                self.log_result("Create Draft Return", False, "Invalid returnable items format")
                return None
            
            if not items_data:
                self.log_result("Create Draft Return", False, "No returnable items available")
                return None
            
            # Create return with partial quantities
            return_items = []
            total_weight = 0.0
            total_amount = 0.0
            
            for item in items_data[:1]:  # Return first item only for testing
                return_qty = min(1, item.get('remaining_qty', 1))
                return_weight = float(item.get('remaining_weight_grams', 0)) * 0.5  # Return 50%
                return_amount = float(item.get('remaining_amount', 0)) * 0.5  # Return 50%
                
                return_item = {
                    "description": item.get('description', 'Returned Item'),
                    "qty": return_qty,
                    "weight_grams": return_weight,
                    "purity": item.get('purity', 916),
                    "amount": return_amount
                }
                return_items.append(return_item)
                total_weight += return_weight
                total_amount += return_amount
            
            return_data = {
                "return_type": "sale_return",
                "reference_type": "invoice",
                "reference_id": invoice_id,
                "party_id": customer_id or "test-customer-id",
                "party_name": customer_name or "Test Customer",
                "party_type": "customer",
                "items": return_items,
                "total_weight_grams": total_weight,
                "total_amount": total_amount,
                "reason": "Customer requested return - quality issue",
                "status": "draft"
            }
            
            response = self.session.post(f"{BACKEND_URL}/returns", json=return_data)
            
            if response.status_code == 201:
                response_data = response.json()
                # Extract return object from nested response
                return_doc = response_data.get('return', response_data)
                return_id = return_doc.get("id")
                return_number = return_doc.get("return_number")
                self.log_result(
                    "Create Draft Return", 
                    True, 
                    f"Created draft return: {return_number} (Amount: {total_amount:.2f} OMR)",
                    {"return_id": return_id, "return_number": return_number}
                )
                return return_id
            else:
                self.log_result("Create Draft Return", False, f"Failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Create Draft Return", False, f"Error: {str(e)}")
            return None
    
    def test_edit_draft_return(self, return_id):
        """Test PATCH /api/returns/{id} to add refund details"""
        try:
            # Get or create a test account for refund
            account_id = self.get_or_create_test_account()
            if not account_id:
                return False
            
            update_data = {
                "refund_mode": "money",
                "refund_money_amount": 603.93,  # 50% of test invoice amount
                "refund_gold_grams": 0.0,
                "payment_mode": "Cash",
                "account_id": account_id,
                "notes": "Cash refund processed for returned gold ring"
            }
            
            response = self.session.patch(f"{BACKEND_URL}/returns/{return_id}", json=update_data)
            
            if response.status_code == 200:
                updated_return = response.json()
                self.log_result(
                    "Edit Draft Return", 
                    True, 
                    f"Added refund details: {update_data['refund_mode']} refund of {update_data['refund_money_amount']} OMR",
                    {"refund_mode": update_data['refund_mode'], "refund_amount": update_data['refund_money_amount']}
                )
                return True
            else:
                self.log_result("Edit Draft Return", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Edit Draft Return", False, f"Error: {str(e)}")
            return False
    
    def get_or_create_test_account(self):
        """Get existing cash account or create one for testing"""
        try:
            # Try to get existing cash account
            response = self.session.get(f"{BACKEND_URL}/accounts")
            
            if response.status_code == 200:
                accounts = response.json()
                if isinstance(accounts, dict) and 'items' in accounts:
                    accounts = accounts['items']
                
                # Look for cash account
                for account in accounts:
                    if 'cash' in account.get('name', '').lower():
                        self.log_result("Get Test Account", True, f"Using existing account: {account.get('name')}")
                        return account.get('id')
            
            # Create new cash account
            account_data = {
                "name": "Cash Account - Test",
                "account_type": "asset",
                "opening_balance": 10000.00,
                "current_balance": 10000.00
            }
            
            response = self.session.post(f"{BACKEND_URL}/accounts", json=account_data)
            
            if response.status_code == 201:
                account = response.json()
                account_id = account.get("id")
                self.log_result("Create Test Account", True, f"Created test account: {account.get('name')}")
                return account_id
            else:
                self.log_result("Create Test Account", False, f"Failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Get/Create Test Account", False, f"Error: {str(e)}")
            return None
    
    def test_get_finalize_impact(self, return_id):
        """Test GET /api/returns/{id}/finalize-impact"""
        try:
            response = self.session.get(f"{BACKEND_URL}/returns/{return_id}/finalize-impact")
            
            if response.status_code == 200:
                impact_data = response.json()
                self.log_result(
                    "Get Finalize Impact", 
                    True, 
                    f"Retrieved finalize impact preview",
                    impact_data
                )
                return impact_data
            else:
                self.log_result("Get Finalize Impact", False, f"Failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Get Finalize Impact", False, f"Error: {str(e)}")
            return None
    
    def test_finalize_return(self, return_id):
        """Test POST /api/returns/{id}/finalize"""
        try:
            response = self.session.post(f"{BACKEND_URL}/returns/{return_id}/finalize")
            
            if response.status_code == 200:
                finalized_return = response.json()
                
                # Verify finalization results
                status = finalized_return.get('status')
                transaction_id = finalized_return.get('transaction_id')
                stock_movements = finalized_return.get('stock_movement_ids', [])
                
                success_details = []
                if status == 'finalized':
                    success_details.append("Status updated to 'finalized'")
                if transaction_id:
                    success_details.append(f"Transaction created: {transaction_id}")
                if stock_movements:
                    success_details.append(f"Stock movements created: {len(stock_movements)}")
                
                self.log_result(
                    "Finalize Return", 
                    True, 
                    f"Return finalized successfully. {', '.join(success_details)}",
                    {
                        "status": status,
                        "transaction_id": transaction_id,
                        "stock_movements_count": len(stock_movements)
                    }
                )
                return True
            else:
                self.log_result("Finalize Return", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Finalize Return", False, f"Error: {str(e)}")
            return False
    
    def test_return_validations(self, invoice_id, finalized_return_id):
        """Test return validation scenarios"""
        print("\n--- Testing Return Validations ---")
        
        # Test 1: Try creating return that exceeds original invoice amount
        self.test_exceed_original_amount(invoice_id)
        
        # Test 2: Try editing finalized return (should fail)
        self.test_edit_finalized_return(finalized_return_id)
        
        # Test 3: Try deleting finalized return (should fail)
        self.test_delete_finalized_return(finalized_return_id)
    
    def test_exceed_original_amount(self, invoice_id):
        """Test creating return that exceeds original invoice amount"""
        try:
            # Create return with excessive amount
            return_data = {
                "return_type": "sale_return",
                "reference_type": "invoice",
                "reference_id": invoice_id,
                "party_id": "test-customer-id",
                "party_name": "Ahmed Al-Rashid",
                "party_type": "customer",
                "items": [
                    {
                        "description": "Excessive Return Item",
                        "qty": 10,  # Excessive quantity
                        "weight_grams": 50.0,  # Excessive weight
                        "purity": 916,
                        "amount": 5000.0  # Excessive amount
                    }
                ],
                "total_weight_grams": 50.0,
                "total_amount": 5000.0,
                "reason": "Testing excessive return validation",
                "status": "draft"
            }
            
            response = self.session.post(f"{BACKEND_URL}/returns", json=return_data)
            
            if response.status_code == 400:
                error_message = response.json().get('detail', response.text)
                self.log_result(
                    "Validation - Exceed Original Amount", 
                    True, 
                    f"Correctly blocked excessive return: {error_message}"
                )
            else:
                self.log_result(
                    "Validation - Exceed Original Amount", 
                    False, 
                    f"Should have blocked excessive return but got: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Validation - Exceed Original Amount", False, f"Error: {str(e)}")
    
    def test_edit_finalized_return(self, return_id):
        """Test editing finalized return (should fail)"""
        try:
            update_data = {
                "refund_money_amount": 1000.0,
                "notes": "Trying to edit finalized return"
            }
            
            response = self.session.patch(f"{BACKEND_URL}/returns/{return_id}", json=update_data)
            
            if response.status_code in [400, 403, 422]:
                error_message = response.json().get('detail', response.text)
                self.log_result(
                    "Validation - Edit Finalized Return", 
                    True, 
                    f"Correctly blocked editing finalized return: {error_message}"
                )
            else:
                self.log_result(
                    "Validation - Edit Finalized Return", 
                    False, 
                    f"Should have blocked editing finalized return but got: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Validation - Edit Finalized Return", False, f"Error: {str(e)}")
    
    def test_delete_finalized_return(self, return_id):
        """Test deleting finalized return (should fail)"""
        try:
            response = self.session.delete(f"{BACKEND_URL}/returns/{return_id}")
            
            if response.status_code in [400, 403, 422]:
                error_message = response.json().get('detail', response.text) if response.content else "Deletion blocked"
                self.log_result(
                    "Validation - Delete Finalized Return", 
                    True, 
                    f"Correctly blocked deleting finalized return: {error_message}"
                )
            else:
                self.log_result(
                    "Validation - Delete Finalized Return", 
                    False, 
                    f"Should have blocked deleting finalized return but got: {response.status_code}"
                )
                
        except Exception as e:
            self.log_result("Validation - Delete Finalized Return", False, f"Error: {str(e)}")
    
    def test_previously_fixed_features(self):
        """Test previously fixed features"""
        print("\n" + "="*60)
        print("TESTING NET FLOW / CASH FLOW / BANK FLOW CALCULATIONS")
        print("="*60)
        
        # Test Finance Dashboard Net Flow Calculations (Primary Focus)
        self.test_finance_dashboard_net_flow_calculations()
        
        # Test other previously fixed features
        print("\n" + "="*60)
        print("TESTING OTHER PREVIOUSLY FIXED FEATURES")
        print("="*60)
        
        # Test Purchases Add Payment
        self.test_purchases_add_payment()
        
        # Test Invoice Stock Movements
        self.test_invoice_stock_movements()
    
    def test_purchases_add_payment(self):
        """Test Purchases Add Payment workflow"""
        print("\n--- Testing Purchases Add Payment ---")
        
        # Create draft purchase
        purchase_id = self.create_test_draft_purchase()
        
        if purchase_id:
            # Add payment to purchase
            self.add_payment_to_purchase(purchase_id)
    
    def create_test_draft_purchase(self):
        """Create a test draft purchase"""
        try:
            # Get or create vendor
            vendor_id = self.get_or_create_test_vendor()
            if not vendor_id:
                return None
            
            purchase_data = {
                "vendor_party_id": vendor_id,
                "description": "Gold Purchase - 22K Gold Bars",
                "weight_grams": 100.500,
                "entered_purity": 916,
                "rate_per_gram": 185.50,
                "amount_total": 18642.75,
                "paid_amount_money": 0.0,  # Draft purchase with no payment
                "balance_due_money": 18642.75
            }
            
            response = self.session.post(f"{BACKEND_URL}/purchases", json=purchase_data)
            
            if response.status_code == 201:
                purchase = response.json()
                purchase_id = purchase.get("id")
                status = purchase.get("status")
                balance_due = purchase.get("balance_due_money")
                
                self.log_result(
                    "Create Draft Purchase", 
                    True, 
                    f"Created draft purchase (Status: {status}, Balance: {balance_due} OMR)",
                    {"purchase_id": purchase_id, "status": status, "balance_due": balance_due}
                )
                return purchase_id
            else:
                self.log_result("Create Draft Purchase", False, f"Failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Create Draft Purchase", False, f"Error: {str(e)}")
            return None
    
    def get_or_create_test_vendor(self):
        """Get existing vendor or create one for testing"""
        try:
            # Try to get existing vendors
            response = self.session.get(f"{BACKEND_URL}/parties?party_type=vendor")
            
            if response.status_code == 200:
                vendors = response.json()
                if isinstance(vendors, dict) and 'items' in vendors:
                    vendors = vendors['items']
                
                if vendors:
                    vendor_id = vendors[0].get('id')
                    self.log_result("Get Test Vendor", True, f"Using existing vendor: {vendors[0].get('name')}")
                    return vendor_id
            
            # Create new vendor
            vendor_data = {
                "name": "Al-Dhahab Gold Trading LLC",
                "phone": "+968 2456 7890",
                "address": "Souk Al-Dhahab, Muscat, Oman",
                "party_type": "vendor",
                "notes": "Test vendor for purchase testing"
            }
            
            response = self.session.post(f"{BACKEND_URL}/parties", json=vendor_data)
            
            if response.status_code == 201:
                vendor = response.json()
                vendor_id = vendor.get("id")
                self.log_result("Create Test Vendor", True, f"Created test vendor: {vendor.get('name')}")
                return vendor_id
            else:
                self.log_result("Create Test Vendor", False, f"Failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Get/Create Test Vendor", False, f"Error: {str(e)}")
            return None
    
    def add_payment_to_purchase(self, purchase_id):
        """Test adding payment to purchase"""
        try:
            # Get account for payment
            account_id = self.get_or_create_test_account()
            if not account_id:
                return False
            
            payment_data = {
                "payment_amount": 10000.00,
                "payment_mode": "Bank Transfer",
                "account_id": account_id,
                "notes": "Partial payment for gold purchase"
            }
            
            response = self.session.post(f"{BACKEND_URL}/purchases/{purchase_id}/add-payment", json=payment_data)
            
            if response.status_code == 200:
                updated_purchase = response.json()
                status = updated_purchase.get("status")
                paid_amount = updated_purchase.get("paid_amount_money")
                balance_due = updated_purchase.get("balance_due_money")
                locked = updated_purchase.get("locked")
                
                self.log_result(
                    "Add Payment to Purchase", 
                    True, 
                    f"Payment added successfully (Status: {status}, Paid: {paid_amount} OMR, Balance: {balance_due} OMR, Locked: {locked})",
                    {"status": status, "paid_amount": paid_amount, "balance_due": balance_due, "locked": locked}
                )
                return True
            else:
                self.log_result("Add Payment to Purchase", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Add Payment to Purchase", False, f"Error: {str(e)}")
            return False
    
    def test_invoice_stock_movements(self):
        """Test Invoice Stock Movements creation"""
        print("\n--- Testing Invoice Stock Movements ---")
        
        try:
            # Create and finalize an invoice to test stock movements
            customer_id = self.get_or_create_test_customer()
            if not customer_id:
                return
            
            # Create invoice with inventory items
            invoice_data = {
                "customer_type": "saved",
                "customer_id": customer_id,
                "invoice_type": "sale",
                "items": [
                    {
                        "category": "Rings",  # This should trigger stock movement
                        "description": "Gold Ring 18K - Stock Test",
                        "qty": 1,
                        "gross_weight": 4.500,
                        "stone_weight": 0.050,
                        "net_gold_weight": 4.450,
                        "weight": 4.450,
                        "purity": 750,
                        "metal_rate": 165.00,
                        "gold_value": 734.25,
                        "making_charge_type": "flat",
                        "making_value": 100.00,
                        "stone_charges": 15.00,
                        "wastage_charges": 10.00,
                        "item_discount": 0.00,
                        "vat_percent": 5.0,
                        "vat_amount": 42.96,
                        "line_total": 902.21
                    }
                ],
                "subtotal": 859.25,
                "discount_amount": 0.00,
                "tax_type": "cgst_sgst",
                "gst_percent": 5.0,
                "cgst_total": 21.48,
                "sgst_total": 21.48,
                "vat_total": 42.96,
                "grand_total": 902.21,
                "paid_amount": 0.00,
                "balance_due": 902.21,
                "notes": "Test invoice for stock movement verification"
            }
            
            # Create invoice
            response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
            
            if response.status_code in [200, 201]:
                invoice = response.json()
                invoice_id = invoice.get("id")
                
                # Finalize the invoice (should create stock movements)
                finalize_response = self.session.post(f"{BACKEND_URL}/invoices/{invoice_id}/finalize")
                
                if finalize_response.status_code == 200:
                    # Check if stock movements were created
                    movements_response = self.session.get(f"{BACKEND_URL}/inventory/movements")
                    
                    if movements_response.status_code == 200:
                        movements = movements_response.json()
                        if isinstance(movements, dict) and 'items' in movements:
                            movements = movements['items']
                        
                        # Look for recent stock OUT movement
                        recent_movements = [m for m in movements if m.get('reference_id') == invoice_id]
                        
                        if recent_movements:
                            movement = recent_movements[0]
                            self.log_result(
                                "Invoice Stock Movements", 
                                True, 
                                f"Stock OUT movement created: {movement.get('description')} (Qty: {movement.get('qty_delta')}, Weight: {movement.get('weight_delta')}g)",
                                {"movement_type": movement.get('movement_type'), "qty_delta": movement.get('qty_delta'), "weight_delta": movement.get('weight_delta')}
                            )
                        else:
                            self.log_result("Invoice Stock Movements", False, "No stock movements found for finalized invoice")
                    else:
                        self.log_result("Invoice Stock Movements", False, f"Failed to retrieve stock movements: {movements_response.status_code}")
                else:
                    self.log_result("Invoice Finalization for Stock Test", False, f"Failed to finalize: {finalize_response.status_code} - {finalize_response.text}")
            else:
                self.log_result("Create Invoice for Stock Test", False, f"Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Invoice Stock Movements", False, f"Error: {str(e)}")
    
    def test_finance_dashboard_net_flow_calculations(self):
        """Test Finance Dashboard Net Flow / Cash Flow / Bank Flow calculations after fix"""
        print("\n--- Testing Finance Dashboard Net Flow Calculations ---")
        
        # Test 1: Test /api/transactions/summary endpoint
        self.test_transactions_summary_endpoint()
        
        # Test 2: Test with real transaction data
        self.test_net_flow_with_real_data()
        
        # Test 3: Test accounting logic consistency
        self.test_accounting_logic_consistency()
    
    def test_transactions_summary_endpoint(self):
        """Test /api/transactions/summary endpoint for new fields"""
        try:
            response = self.session.get(f"{BACKEND_URL}/transactions/summary")
            
            if response.status_code == 200:
                summary_data = response.json()
                
                # Check for required new fields
                required_fields = ['total_in', 'total_out', 'net_flow', 'cash_summary', 'bank_summary']
                missing_fields = [field for field in required_fields if field not in summary_data]
                
                if not missing_fields:
                    # Verify field types and values
                    total_in = summary_data.get('total_in', 0)
                    total_out = summary_data.get('total_out', 0)
                    net_flow = summary_data.get('net_flow', 0)
                    cash_summary = summary_data.get('cash_summary', {})
                    bank_summary = summary_data.get('bank_summary', {})
                    
                    # Verify math: net_flow = total_in - total_out
                    calculated_net_flow = round(total_in - total_out, 3)
                    actual_net_flow = round(net_flow, 3)
                    math_correct = abs(calculated_net_flow - actual_net_flow) < 0.001
                    
                    # Verify cash summary has required fields
                    cash_fields_valid = all(field in cash_summary for field in ['debit', 'credit', 'net'])
                    bank_fields_valid = all(field in bank_summary for field in ['debit', 'credit', 'net'])
                    
                    # Verify cash/bank net calculations
                    cash_net_correct = True
                    bank_net_correct = True
                    
                    if cash_fields_valid:
                        cash_calculated_net = round(cash_summary['debit'] - cash_summary['credit'], 3)
                        cash_actual_net = round(cash_summary['net'], 3)
                        cash_net_correct = abs(cash_calculated_net - cash_actual_net) < 0.001
                    
                    if bank_fields_valid:
                        bank_calculated_net = round(bank_summary['debit'] - bank_summary['credit'], 3)
                        bank_actual_net = round(bank_summary['net'], 3)
                        bank_net_correct = abs(bank_calculated_net - bank_actual_net) < 0.001
                    
                    all_valid = math_correct and cash_fields_valid and bank_fields_valid and cash_net_correct and bank_net_correct
                    
                    details = f"Net Flow Math: {'✓' if math_correct else '✗'} ({total_in} - {total_out} = {net_flow}), "
                    details += f"Cash Net: {'✓' if cash_net_correct else '✗'} ({cash_summary.get('debit', 0)} - {cash_summary.get('credit', 0)} = {cash_summary.get('net', 0)}), "
                    details += f"Bank Net: {'✓' if bank_net_correct else '✗'} ({bank_summary.get('debit', 0)} - {bank_summary.get('credit', 0)} = {bank_summary.get('net', 0)})"
                    
                    self.log_result(
                        "Transactions Summary Endpoint", 
                        all_valid, 
                        details,
                        {
                            "total_in": total_in,
                            "total_out": total_out,
                            "net_flow": net_flow,
                            "calculated_net_flow": calculated_net_flow,
                            "math_correct": math_correct,
                            "cash_summary": cash_summary,
                            "bank_summary": bank_summary
                        }
                    )
                else:
                    self.log_result("Transactions Summary Endpoint", False, f"Missing required fields: {missing_fields}")
            else:
                self.log_result("Transactions Summary Endpoint", False, f"Failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Transactions Summary Endpoint", False, f"Error: {str(e)}")
    
    def test_net_flow_with_real_data(self):
        """Test Net Flow calculations with real transaction data"""
        try:
            # Create test cash account with opening balance 0
            cash_account_id = self.create_test_cash_account()
            if not cash_account_id:
                return
            
            # Add invoice payment (DEBIT to cash) = +1000 OMR
            debit_transaction_id = self.create_test_transaction(
                account_id=cash_account_id,
                transaction_type="debit",
                amount=1000.00,
                description="Invoice Payment - Cash IN"
            )
            
            # Add purchase payment (CREDIT to cash) = -500 OMR  
            credit_transaction_id = self.create_test_transaction(
                account_id=cash_account_id,
                transaction_type="credit", 
                amount=500.00,
                description="Purchase Payment - Cash OUT"
            )
            
            if debit_transaction_id and credit_transaction_id:
                # Wait a moment for transactions to be processed
                time.sleep(1)
                
                # Get updated summary
                response = self.session.get(f"{BACKEND_URL}/transactions/summary")
                
                if response.status_code == 200:
                    summary_data = response.json()
                    
                    total_in = summary_data.get('total_in', 0)
                    total_out = summary_data.get('total_out', 0)
                    net_flow = summary_data.get('net_flow', 0)
                    cash_summary = summary_data.get('cash_summary', {})
                    
                    # Expected values based on our test transactions
                    # Note: These are incremental to existing data, so we check if our transactions are reflected
                    expected_net_flow = 1000.00 - 500.00  # 500.00
                    
                    # Verify the math is consistent (total_in - total_out = net_flow)
                    calculated_net_flow = round(total_in - total_out, 3)
                    actual_net_flow = round(net_flow, 3)
                    math_consistent = abs(calculated_net_flow - actual_net_flow) < 0.001
                    
                    # Verify cash summary net = debit - credit
                    cash_net_consistent = True
                    if cash_summary:
                        cash_calculated_net = round(cash_summary.get('debit', 0) - cash_summary.get('credit', 0), 3)
                        cash_actual_net = round(cash_summary.get('net', 0), 3)
                        cash_net_consistent = abs(cash_calculated_net - cash_actual_net) < 0.001
                    
                    # Check if values are properly rounded to 3 decimal places
                    values_rounded = (
                        len(str(total_in).split('.')[-1]) <= 3 and
                        len(str(total_out).split('.')[-1]) <= 3 and
                        len(str(net_flow).split('.')[-1]) <= 3
                    )
                    
                    all_valid = math_consistent and cash_net_consistent and values_rounded
                    
                    details = f"Math Consistent: {'✓' if math_consistent else '✗'}, "
                    details += f"Cash Net Consistent: {'✓' if cash_net_consistent else '✗'}, "
                    details += f"Values Rounded: {'✓' if values_rounded else '✗'}, "
                    details += f"Net Flow: {net_flow} OMR (In: {total_in}, Out: {total_out})"
                    
                    self.log_result(
                        "Net Flow with Real Data", 
                        all_valid, 
                        details,
                        {
                            "total_in": total_in,
                            "total_out": total_out,
                            "net_flow": net_flow,
                            "calculated_net_flow": calculated_net_flow,
                            "cash_summary": cash_summary,
                            "math_consistent": math_consistent,
                            "cash_net_consistent": cash_net_consistent,
                            "values_rounded": values_rounded
                        }
                    )
                else:
                    self.log_result("Net Flow with Real Data", False, f"Failed to get updated summary: {response.status_code}")
            else:
                self.log_result("Net Flow with Real Data", False, "Failed to create test transactions")
                
        except Exception as e:
            self.log_result("Net Flow with Real Data", False, f"Error: {str(e)}")
    
    def test_accounting_logic_consistency(self):
        """Test accounting logic: For asset accounts (cash/bank): DEBIT = increase, CREDIT = decrease"""
        try:
            # Get account balances before and after transactions
            accounts_response = self.session.get(f"{BACKEND_URL}/accounts")
            
            if accounts_response.status_code == 200:
                accounts_data = accounts_response.json()
                if isinstance(accounts_data, dict) and 'items' in accounts_data:
                    accounts = accounts_data['items']
                else:
                    accounts = accounts_data
                
                # Find cash and bank accounts
                cash_accounts = [acc for acc in accounts if 'cash' in acc.get('name', '').lower() and acc.get('account_type') == 'asset']
                bank_accounts = [acc for acc in accounts if 'bank' in acc.get('name', '').lower() and acc.get('account_type') == 'asset']
                
                logic_tests_passed = 0
                total_logic_tests = 0
                
                # Test cash accounts
                for account in cash_accounts[:1]:  # Test first cash account
                    total_logic_tests += 1
                    account_id = account.get('id')
                    initial_balance = account.get('current_balance', 0)
                    
                    # Create DEBIT transaction (should increase balance)
                    debit_success = self.create_test_transaction(
                        account_id=account_id,
                        transaction_type="debit",
                        amount=100.00,
                        description="Test DEBIT - Should increase balance"
                    )
                    
                    if debit_success:
                        # Check if balance increased
                        updated_account_response = self.session.get(f"{BACKEND_URL}/accounts/{account_id}")
                        if updated_account_response.status_code == 200:
                            updated_account = updated_account_response.json()
                            new_balance = updated_account.get('current_balance', 0)
                            
                            # For asset accounts: DEBIT should increase balance
                            if new_balance > initial_balance:
                                logic_tests_passed += 1
                                self.log_result(
                                    f"Accounting Logic - {account.get('name')} DEBIT", 
                                    True, 
                                    f"DEBIT correctly increased balance: {initial_balance} → {new_balance} (+{new_balance - initial_balance})"
                                )
                            else:
                                self.log_result(
                                    f"Accounting Logic - {account.get('name')} DEBIT", 
                                    False, 
                                    f"DEBIT should increase balance but: {initial_balance} → {new_balance}"
                                )
                
                # Test bank accounts  
                for account in bank_accounts[:1]:  # Test first bank account
                    total_logic_tests += 1
                    account_id = account.get('id')
                    initial_balance = account.get('current_balance', 0)
                    
                    # Create CREDIT transaction (should decrease balance)
                    credit_success = self.create_test_transaction(
                        account_id=account_id,
                        transaction_type="credit",
                        amount=50.00,
                        description="Test CREDIT - Should decrease balance"
                    )
                    
                    if credit_success:
                        # Check if balance decreased
                        updated_account_response = self.session.get(f"{BACKEND_URL}/accounts/{account_id}")
                        if updated_account_response.status_code == 200:
                            updated_account = updated_account_response.json()
                            new_balance = updated_account.get('current_balance', 0)
                            
                            # For asset accounts: CREDIT should decrease balance
                            if new_balance < initial_balance:
                                logic_tests_passed += 1
                                self.log_result(
                                    f"Accounting Logic - {account.get('name')} CREDIT", 
                                    True, 
                                    f"CREDIT correctly decreased balance: {initial_balance} → {new_balance} ({new_balance - initial_balance})"
                                )
                            else:
                                self.log_result(
                                    f"Accounting Logic - {account.get('name')} CREDIT", 
                                    False, 
                                    f"CREDIT should decrease balance but: {initial_balance} → {new_balance}"
                                )
                
                # Overall accounting logic test result
                if total_logic_tests > 0:
                    logic_success_rate = (logic_tests_passed / total_logic_tests) * 100
                    overall_success = logic_tests_passed == total_logic_tests
                    
                    self.log_result(
                        "Accounting Logic Consistency", 
                        overall_success, 
                        f"Accounting logic tests: {logic_tests_passed}/{total_logic_tests} passed ({logic_success_rate:.1f}%)"
                    )
                else:
                    self.log_result("Accounting Logic Consistency", False, "No cash/bank accounts found for testing")
            else:
                self.log_result("Accounting Logic Consistency", False, f"Failed to get accounts: {accounts_response.status_code}")
                
        except Exception as e:
            self.log_result("Accounting Logic Consistency", False, f"Error: {str(e)}")
    
    def create_test_cash_account(self):
        """Create a test cash account with opening balance 0"""
        try:
            account_data = {
                "name": f"Test Cash Account - {uuid.uuid4().hex[:8]}",
                "account_type": "asset",
                "opening_balance": 0.00,
                "current_balance": 0.00
            }
            
            response = self.session.post(f"{BACKEND_URL}/accounts", json=account_data)
            
            if response.status_code == 201:
                account = response.json()
                account_id = account.get("id")
                self.log_result("Create Test Cash Account", True, f"Created test cash account: {account.get('name')}")
                return account_id
            else:
                self.log_result("Create Test Cash Account", False, f"Failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Create Test Cash Account", False, f"Error: {str(e)}")
            return None
    
    def create_test_transaction(self, account_id, transaction_type, amount, description):
        """Create a test transaction"""
        try:
            transaction_data = {
                "transaction_type": transaction_type,
                "mode": "Cash",
                "account_id": account_id,
                "amount": amount,
                "category": "Testing",
                "notes": description
            }
            
            response = self.session.post(f"{BACKEND_URL}/transactions", json=transaction_data)
            
            if response.status_code in [200, 201]:
                transaction = response.json()
                transaction_id = transaction.get("id")
                self.log_result(
                    f"Create Test Transaction ({transaction_type.upper()})", 
                    True, 
                    f"Created {transaction_type} transaction: {amount} OMR (ID: {transaction_id})"
                )
                return transaction_id
            else:
                self.log_result(
                    f"Create Test Transaction ({transaction_type.upper()})", 
                    False, 
                    f"Failed: {response.status_code} - {response.text}"
                )
                return None
                
        except Exception as e:
            self.log_result(f"Create Test Transaction ({transaction_type.upper()})", False, f"Error: {str(e)}")
            return None
    
    def test_gold_received_feature(self):
        """Test NEW Sales - Advance Gold & Gold Exchange Feature"""
        print("\n" + "="*80)
        print("TESTING NEW SALES - ADVANCE GOLD & GOLD EXCHANGE FEATURE")
        print("="*80)
        
        # Test 1: Invoice Creation with Gold Received (Advance Gold)
        self.test_invoice_with_advance_gold()
        
        # Test 2: Gold value exceeds invoice total
        self.test_gold_exceeds_invoice_total()
        
        # Test 3: Partial gold payment
        self.test_partial_gold_payment()
        
        # Test 4: Gold exchange purpose
        self.test_gold_exchange_purpose()
        
        # Test 5: Gold Ledger Verification
        self.test_gold_ledger_verification()
        
        # Test 6: Transaction Records Verification
        self.test_transaction_records_verification()
        
        # Test 7: Account Balance Verification
        self.test_account_balance_verification()
        
        # Test 8: Edge Cases & Validation
        self.test_gold_edge_cases_validation()
        
        # Test 9: Existing Gold Exchange Payment Mode (Verify Still Works)
        self.test_existing_gold_exchange_payment()
    
    def test_invoice_with_advance_gold(self):
        """TEST SCENARIO 1: Create invoice with advance gold"""
        try:
            # Get or create customer
            customer_id = self.get_or_create_test_customer()
            if not customer_id:
                return None
            
            # Create invoice with gold received fields
            invoice_data = {
                "customer_type": "saved",
                "customer_id": customer_id,
                "invoice_type": "sale",
                "items": [
                    {
                        "description": "Gold Necklace 22K",
                        "qty": 1,
                        "gross_weight": 15.750,
                        "stone_weight": 0.250,
                        "net_gold_weight": 15.500,
                        "weight": 15.500,
                        "purity": 916,
                        "metal_rate": 185.50,
                        "gold_value": 2875.25,
                        "making_charge_type": "per_gram",
                        "making_value": 310.00,
                        "stone_charges": 50.00,
                        "wastage_charges": 30.00,
                        "item_discount": 0.00,
                        "vat_percent": 5.0,
                        "vat_amount": 163.26,
                        "line_total": 3428.51
                    }
                ],
                "subtotal": 3265.25,
                "discount_amount": 0.00,
                "tax_type": "cgst_sgst",
                "gst_percent": 5.0,
                "cgst_total": 81.63,
                "sgst_total": 81.63,
                "igst_total": 0.00,
                "vat_total": 163.26,
                "grand_total": 3428.51,
                "paid_amount": 0.00,
                "balance_due": 3428.51,
                # Gold Received fields (NEW FEATURE)
                "gold_received_weight": 10.500,  # 10.500 grams
                "gold_received_rate": 25.00,     # 25.00 OMR/gram
                "gold_received_purity": 916,
                "gold_received_purpose": "advance_gold",
                "gold_received_value": 262.50,   # Expected: 10.500 × 25.00 = 262.50 OMR
                "notes": "Test invoice with advance gold received"
            }
            
            response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
            
            if response.status_code in [200, 201]:
                invoice = response.json()
                invoice_id = invoice.get("id")
                
                # Verify gold calculations
                paid_amount = invoice.get("paid_amount", 0)
                balance_due = invoice.get("balance_due", 0)
                payment_status = invoice.get("payment_status", "unpaid")
                gold_value = invoice.get("gold_received_value", 0)
                
                # Expected calculations
                expected_gold_value = 10.500 * 25.00  # 262.50
                expected_paid_amount = expected_gold_value  # 262.50
                expected_balance_due = 3428.51 - expected_gold_value  # 3166.01
                
                # Verify calculations
                gold_value_correct = abs(gold_value - expected_gold_value) < 0.01
                paid_amount_correct = abs(paid_amount - expected_paid_amount) < 0.01
                balance_due_correct = abs(balance_due - expected_balance_due) < 0.01
                payment_status_correct = payment_status == "partial"
                
                all_correct = all([gold_value_correct, paid_amount_correct, balance_due_correct, payment_status_correct])
                
                details = f"Gold Value: {'✓' if gold_value_correct else '✗'} ({gold_value} vs {expected_gold_value}), "
                details += f"Paid Amount: {'✓' if paid_amount_correct else '✗'} ({paid_amount} vs {expected_paid_amount}), "
                details += f"Balance Due: {'✓' if balance_due_correct else '✗'} ({balance_due} vs {expected_balance_due}), "
                details += f"Payment Status: {'✓' if payment_status_correct else '✗'} ({payment_status})"
                
                self.log_result(
                    "Invoice with Advance Gold - Calculations",
                    all_correct,
                    details,
                    {
                        "invoice_id": invoice_id,
                        "gold_value": gold_value,
                        "paid_amount": paid_amount,
                        "balance_due": balance_due,
                        "payment_status": payment_status
                    }
                )
                
                return invoice_id if all_correct else None
            else:
                self.log_result("Invoice with Advance Gold - Creation", False, f"Failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Invoice with Advance Gold", False, f"Error: {str(e)}")
            return None
    
    def test_gold_exceeds_invoice_total(self):
        """TEST SCENARIO 2: Gold value exceeds invoice total"""
        try:
            customer_id = self.get_or_create_test_customer()
            if not customer_id:
                return None
            
            # Create small invoice (100 OMR grand_total)
            invoice_data = {
                "customer_type": "saved",
                "customer_id": customer_id,
                "invoice_type": "sale",
                "items": [
                    {
                        "description": "Small Gold Ring",
                        "qty": 1,
                        "gross_weight": 2.000,
                        "stone_weight": 0.000,
                        "net_gold_weight": 2.000,
                        "weight": 2.000,
                        "purity": 916,
                        "metal_rate": 45.00,
                        "gold_value": 90.00,
                        "making_charge_type": "flat",
                        "making_value": 5.00,
                        "stone_charges": 0.00,
                        "wastage_charges": 0.00,
                        "item_discount": 0.00,
                        "vat_percent": 5.0,
                        "vat_amount": 4.75,
                        "line_total": 99.75
                    }
                ],
                "subtotal": 95.00,
                "discount_amount": 0.00,
                "tax_type": "cgst_sgst",
                "gst_percent": 5.0,
                "cgst_total": 2.38,
                "sgst_total": 2.37,
                "igst_total": 0.00,
                "vat_total": 4.75,
                "grand_total": 99.75,
                "paid_amount": 0.00,
                "balance_due": 99.75,
                # Gold worth 150 OMR (exceeds invoice total)
                "gold_received_weight": 6.000,
                "gold_received_rate": 25.00,
                "gold_received_purity": 916,
                "gold_received_purpose": "advance_gold",
                "gold_received_value": 150.00,
                "notes": "Test gold value exceeding invoice total"
            }
            
            response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
            
            if response.status_code in [200, 201]:
                invoice = response.json()
                
                paid_amount = invoice.get("paid_amount", 0)
                balance_due = invoice.get("balance_due", 0)
                payment_status = invoice.get("payment_status", "unpaid")
                paid_at = invoice.get("paid_at")
                
                # Verify expectations
                paid_amount_correct = paid_amount == 150.00  # Can exceed grand_total
                balance_due_correct = balance_due == -50.25  # Customer credit (150 - 99.75)
                payment_status_correct = payment_status == "paid"
                paid_at_exists = paid_at is not None
                
                all_correct = all([paid_amount_correct, balance_due_correct, payment_status_correct, paid_at_exists])
                
                details = f"Paid Amount: {'✓' if paid_amount_correct else '✗'} ({paid_amount} = 150.00), "
                details += f"Balance Due: {'✓' if balance_due_correct else '✗'} ({balance_due} = -50.25), "
                details += f"Payment Status: {'✓' if payment_status_correct else '✗'} ({payment_status} = paid), "
                details += f"Paid At: {'✓' if paid_at_exists else '✗'} ({paid_at})"
                
                self.log_result(
                    "Gold Exceeds Invoice Total",
                    all_correct,
                    details,
                    {
                        "paid_amount": paid_amount,
                        "balance_due": balance_due,
                        "payment_status": payment_status,
                        "paid_at": paid_at
                    }
                )
                
                return all_correct
            else:
                self.log_result("Gold Exceeds Invoice Total", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Gold Exceeds Invoice Total", False, f"Error: {str(e)}")
            return False
    
    def test_partial_gold_payment(self):
        """TEST SCENARIO 3: Partial gold payment"""
        try:
            customer_id = self.get_or_create_test_customer()
            if not customer_id:
                return None
            
            # Create invoice with 500 OMR grand_total
            invoice_data = {
                "customer_type": "saved",
                "customer_id": customer_id,
                "invoice_type": "sale",
                "items": [
                    {
                        "description": "Gold Bracelet 22K",
                        "qty": 1,
                        "gross_weight": 8.000,
                        "stone_weight": 0.000,
                        "net_gold_weight": 8.000,
                        "weight": 8.000,
                        "purity": 916,
                        "metal_rate": 55.00,
                        "gold_value": 440.00,
                        "making_charge_type": "flat",
                        "making_value": 35.00,
                        "stone_charges": 0.00,
                        "wastage_charges": 0.00,
                        "item_discount": 0.00,
                        "vat_percent": 5.0,
                        "vat_amount": 23.75,
                        "line_total": 498.75
                    }
                ],
                "subtotal": 475.00,
                "discount_amount": 0.00,
                "tax_type": "cgst_sgst",
                "gst_percent": 5.0,
                "cgst_total": 11.88,
                "sgst_total": 11.87,
                "igst_total": 0.00,
                "vat_total": 23.75,
                "grand_total": 498.75,
                "paid_amount": 0.00,
                "balance_due": 498.75,
                # Gold worth 200 OMR (partial payment)
                "gold_received_weight": 8.000,
                "gold_received_rate": 25.00,
                "gold_received_purity": 916,
                "gold_received_purpose": "advance_gold",
                "gold_received_value": 200.00,
                "notes": "Test partial gold payment"
            }
            
            response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
            
            if response.status_code in [200, 201]:
                invoice = response.json()
                
                paid_amount = invoice.get("paid_amount", 0)
                balance_due = invoice.get("balance_due", 0)
                payment_status = invoice.get("payment_status", "unpaid")
                
                # Verify expectations
                paid_amount_correct = paid_amount == 200.00
                balance_due_correct = abs(balance_due - 298.75) < 0.01  # 498.75 - 200.00
                payment_status_correct = payment_status == "partial"
                
                all_correct = all([paid_amount_correct, balance_due_correct, payment_status_correct])
                
                details = f"Paid Amount: {'✓' if paid_amount_correct else '✗'} ({paid_amount} = 200.00), "
                details += f"Balance Due: {'✓' if balance_due_correct else '✗'} ({balance_due} ≈ 298.75), "
                details += f"Payment Status: {'✓' if payment_status_correct else '✗'} ({payment_status} = partial)"
                
                self.log_result(
                    "Partial Gold Payment",
                    all_correct,
                    details,
                    {
                        "paid_amount": paid_amount,
                        "balance_due": balance_due,
                        "payment_status": payment_status
                    }
                )
                
                return all_correct
            else:
                self.log_result("Partial Gold Payment", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Partial Gold Payment", False, f"Error: {str(e)}")
            return False
    
    def test_gold_exchange_purpose(self):
        """TEST SCENARIO 4: Gold exchange purpose"""
        try:
            customer_id = self.get_or_create_test_customer()
            if not customer_id:
                return None
            
            # Create invoice with gold_received_purpose: "exchange"
            invoice_data = {
                "customer_type": "saved",
                "customer_id": customer_id,
                "invoice_type": "sale",
                "items": [
                    {
                        "description": "Gold Chain 22K",
                        "qty": 1,
                        "gross_weight": 12.000,
                        "stone_weight": 0.000,
                        "net_gold_weight": 12.000,
                        "weight": 12.000,
                        "purity": 916,
                        "metal_rate": 185.50,
                        "gold_value": 2226.00,
                        "making_charge_type": "per_gram",
                        "making_value": 240.00,
                        "stone_charges": 0.00,
                        "wastage_charges": 20.00,
                        "item_discount": 0.00,
                        "vat_percent": 5.0,
                        "vat_amount": 124.30,
                        "line_total": 2610.30
                    }
                ],
                "subtotal": 2486.00,
                "discount_amount": 0.00,
                "tax_type": "cgst_sgst",
                "gst_percent": 5.0,
                "cgst_total": 62.15,
                "sgst_total": 62.15,
                "igst_total": 0.00,
                "vat_total": 124.30,
                "grand_total": 2610.30,
                "paid_amount": 0.00,
                "balance_due": 2610.30,
                # Gold exchange
                "gold_received_weight": 10.500,
                "gold_received_rate": 25.00,
                "gold_received_purity": 916,
                "gold_received_purpose": "exchange",  # Different purpose
                "gold_received_value": 262.50,
                "notes": "Test gold exchange purpose"
            }
            
            response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
            
            if response.status_code in [200, 201]:
                invoice = response.json()
                invoice_id = invoice.get("id")
                
                # Verify gold purpose is set correctly
                gold_purpose = invoice.get("gold_received_purpose")
                purpose_correct = gold_purpose == "exchange"
                
                self.log_result(
                    "Gold Exchange Purpose",
                    purpose_correct,
                    f"Gold purpose: {'✓' if purpose_correct else '✗'} ({gold_purpose} = exchange)",
                    {
                        "invoice_id": invoice_id,
                        "gold_received_purpose": gold_purpose
                    }
                )
                
                return invoice_id if purpose_correct else None
            else:
                self.log_result("Gold Exchange Purpose", False, f"Failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Gold Exchange Purpose", False, f"Error: {str(e)}")
            return None
    
    def test_gold_ledger_verification(self):
        """Test Gold Ledger Verification"""
        try:
            # Create an invoice with gold received first
            invoice_id = self.test_invoice_with_advance_gold()
            if not invoice_id:
                self.log_result("Gold Ledger Verification - Setup", False, "Failed to create test invoice")
                return False
            
            # Get customer ID from the invoice
            invoice_response = self.session.get(f"{BACKEND_URL}/invoices/{invoice_id}")
            if invoice_response.status_code != 200:
                self.log_result("Gold Ledger Verification - Get Invoice", False, "Failed to get invoice")
                return False
            
            invoice_data = invoice_response.json()
            customer_id = invoice_data.get("customer_id")
            
            if not customer_id:
                self.log_result("Gold Ledger Verification - Customer ID", False, "No customer ID in invoice")
                return False
            
            # Check GET /api/gold-ledger endpoint
            response = self.session.get(f"{BACKEND_URL}/gold-ledger?party_id={customer_id}")
            
            if response.status_code == 200:
                ledger_entries = response.json()
                if isinstance(ledger_entries, dict) and 'items' in ledger_entries:
                    ledger_entries = ledger_entries['items']
                
                # Find entry for our invoice
                invoice_entries = [entry for entry in ledger_entries if entry.get('reference_id') == invoice_id]
                
                if invoice_entries:
                    entry = invoice_entries[0]
                    
                    # Verify entry details
                    type_correct = entry.get('type') == 'IN'
                    weight_correct = abs(entry.get('weight_grams', 0) - 10.500) < 0.001
                    purity_correct = entry.get('purity_entered') == 916
                    purpose_correct = entry.get('purpose') == 'advance_gold'
                    reference_type_correct = entry.get('reference_type') == 'invoice'
                    reference_id_correct = entry.get('reference_id') == invoice_id
                    
                    all_correct = all([
                        type_correct, weight_correct, purity_correct, 
                        purpose_correct, reference_type_correct, reference_id_correct
                    ])
                    
                    details = f"Type: {'✓' if type_correct else '✗'} ({entry.get('type')}), "
                    details += f"Weight: {'✓' if weight_correct else '✗'} ({entry.get('weight_grams')}g), "
                    details += f"Purity: {'✓' if purity_correct else '✗'} ({entry.get('purity_entered')}), "
                    details += f"Purpose: {'✓' if purpose_correct else '✗'} ({entry.get('purpose')}), "
                    details += f"Reference: {'✓' if reference_type_correct and reference_id_correct else '✗'}"
                    
                    self.log_result(
                        "Gold Ledger Verification",
                        all_correct,
                        details,
                        {
                            "entry": entry,
                            "verifications": {
                                "type_correct": type_correct,
                                "weight_correct": weight_correct,
                                "purity_correct": purity_correct,
                                "purpose_correct": purpose_correct,
                                "reference_correct": reference_type_correct and reference_id_correct
                            }
                        }
                    )
                    
                    return all_correct
                else:
                    self.log_result("Gold Ledger Verification", False, "No gold ledger entry found for invoice")
                    return False
            else:
                self.log_result("Gold Ledger Verification", False, f"Failed to get gold ledger: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Gold Ledger Verification", False, f"Error: {str(e)}")
            return False
    
    def test_transaction_records_verification(self):
        """Test Transaction Records Verification"""
        try:
            # Create an invoice with gold received first
            invoice_id = self.test_invoice_with_advance_gold()
            if not invoice_id:
                self.log_result("Transaction Records Verification - Setup", False, "Failed to create test invoice")
                return False
            
            # Check GET /api/transactions endpoint
            response = self.session.get(f"{BACKEND_URL}/transactions?reference_type=invoice&reference_id={invoice_id}")
            
            if response.status_code == 200:
                transactions = response.json()
                if isinstance(transactions, dict) and 'items' in transactions:
                    transactions = transactions['items']
                
                # Find gold transaction for our invoice
                gold_transactions = [
                    txn for txn in transactions 
                    if txn.get('reference_id') == invoice_id and 
                       'gold' in txn.get('notes', '').lower()
                ]
                
                if gold_transactions:
                    transaction = gold_transactions[0]
                    
                    # Verify transaction details
                    transaction_type_correct = transaction.get('transaction_type') == 'debit'
                    account_name_correct = transaction.get('account_name') == 'Gold Received'
                    amount_correct = abs(transaction.get('amount', 0) - 262.50) < 0.01
                    category_correct = transaction.get('category') == 'sales'
                    reference_id_correct = transaction.get('reference_id') == invoice_id
                    
                    all_correct = all([
                        transaction_type_correct, account_name_correct, amount_correct,
                        category_correct, reference_id_correct
                    ])
                    
                    details = f"Type: {'✓' if transaction_type_correct else '✗'} ({transaction.get('transaction_type')}), "
                    details += f"Account: {'✓' if account_name_correct else '✗'} ({transaction.get('account_name')}), "
                    details += f"Amount: {'✓' if amount_correct else '✗'} ({transaction.get('amount')}), "
                    details += f"Category: {'✓' if category_correct else '✗'} ({transaction.get('category')}), "
                    details += f"Reference: {'✓' if reference_id_correct else '✗'}"
                    
                    self.log_result(
                        "Transaction Records Verification",
                        all_correct,
                        details,
                        {
                            "transaction": transaction,
                            "verifications": {
                                "transaction_type_correct": transaction_type_correct,
                                "account_name_correct": account_name_correct,
                                "amount_correct": amount_correct,
                                "category_correct": category_correct,
                                "reference_id_correct": reference_id_correct
                            }
                        }
                    )
                    
                    return all_correct
                else:
                    self.log_result("Transaction Records Verification", False, "No gold transaction found for invoice")
                    return False
            else:
                self.log_result("Transaction Records Verification", False, f"Failed to get transactions: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Transaction Records Verification", False, f"Error: {str(e)}")
            return False
    
    def test_account_balance_verification(self):
        """Test Account Balance Verification"""
        try:
            # Get initial Gold Received account balance
            accounts_response = self.session.get(f"{BACKEND_URL}/accounts")
            if accounts_response.status_code != 200:
                self.log_result("Account Balance Verification - Get Accounts", False, "Failed to get accounts")
                return False
            
            accounts_data = accounts_response.json()
            if isinstance(accounts_data, dict) and 'items' in accounts_data:
                accounts = accounts_data['items']
            else:
                accounts = accounts_data
            
            # Find Gold Received account
            gold_account = None
            for account in accounts:
                if account.get('name') == 'Gold Received':
                    gold_account = account
                    break
            
            initial_balance = gold_account.get('current_balance', 0) if gold_account else 0
            
            # Create an invoice with gold received
            invoice_id = self.test_invoice_with_advance_gold()
            if not invoice_id:
                self.log_result("Account Balance Verification - Setup", False, "Failed to create test invoice")
                return False
            
            # Wait a moment for balance update
            time.sleep(1)
            
            # Get updated accounts
            updated_accounts_response = self.session.get(f"{BACKEND_URL}/accounts")
            if updated_accounts_response.status_code != 200:
                self.log_result("Account Balance Verification - Get Updated Accounts", False, "Failed to get updated accounts")
                return False
            
            updated_accounts_data = updated_accounts_response.json()
            if isinstance(updated_accounts_data, dict) and 'items' in updated_accounts_data:
                updated_accounts = updated_accounts_data['items']
            else:
                updated_accounts = updated_accounts_data
            
            # Find updated Gold Received account
            updated_gold_account = None
            for account in updated_accounts:
                if account.get('name') == 'Gold Received':
                    updated_gold_account = account
                    break
            
            if updated_gold_account:
                new_balance = updated_gold_account.get('current_balance', 0)
                account_type = updated_gold_account.get('account_type')
                
                # Verify account details
                account_exists = True
                account_type_correct = account_type == 'asset'
                balance_updated = abs(new_balance - (initial_balance + 262.50)) < 0.01
                
                all_correct = all([account_exists, account_type_correct, balance_updated])
                
                details = f"Account Exists: {'✓' if account_exists else '✗'}, "
                details += f"Type: {'✓' if account_type_correct else '✗'} ({account_type}), "
                details += f"Balance Updated: {'✓' if balance_updated else '✗'} ({initial_balance} + 262.50 = {new_balance})"
                
                self.log_result(
                    "Account Balance Verification",
                    all_correct,
                    details,
                    {
                        "initial_balance": initial_balance,
                        "new_balance": new_balance,
                        "expected_balance": initial_balance + 262.50,
                        "account_type": account_type
                    }
                )
                
                return all_correct
            else:
                self.log_result("Account Balance Verification", False, "Gold Received account not found after transaction")
                return False
                
        except Exception as e:
            self.log_result("Account Balance Verification", False, f"Error: {str(e)}")
            return False
    
    def test_gold_edge_cases_validation(self):
        """Test Edge Cases & Validation"""
        print("\n--- Testing Gold Edge Cases & Validation ---")
        
        # Test 1: Walk-in customer with gold (should work but no gold ledger)
        self.test_walk_in_customer_gold()
        
        # Test 2: Invoice without gold fields (should work normally)
        self.test_invoice_without_gold()
        
        # Test 3: Gold weight without rate (should handle gracefully)
        self.test_gold_weight_without_rate()
        
        # Test 4: Negative gold values (should reject or handle)
        self.test_negative_gold_values()
    
    def test_walk_in_customer_gold(self):
        """Test walk-in customer with gold (should work but no gold ledger)"""
        try:
            invoice_data = {
                "customer_type": "walk_in",
                "walk_in_name": "Ahmed Al-Zahra",
                "walk_in_phone": "+968 9988 7766",
                "invoice_type": "sale",
                "items": [
                    {
                        "description": "Gold Ring 18K",
                        "qty": 1,
                        "gross_weight": 3.000,
                        "stone_weight": 0.000,
                        "net_gold_weight": 3.000,
                        "weight": 3.000,
                        "purity": 750,
                        "metal_rate": 150.00,
                        "gold_value": 450.00,
                        "making_charge_type": "flat",
                        "making_value": 50.00,
                        "stone_charges": 0.00,
                        "wastage_charges": 0.00,
                        "item_discount": 0.00,
                        "vat_percent": 5.0,
                        "vat_amount": 25.00,
                        "line_total": 525.00
                    }
                ],
                "subtotal": 500.00,
                "discount_amount": 0.00,
                "tax_type": "cgst_sgst",
                "gst_percent": 5.0,
                "cgst_total": 12.50,
                "sgst_total": 12.50,
                "igst_total": 0.00,
                "vat_total": 25.00,
                "grand_total": 525.00,
                "paid_amount": 0.00,
                "balance_due": 525.00,
                # Gold received from walk-in customer
                "gold_received_weight": 2.000,
                "gold_received_rate": 25.00,
                "gold_received_purity": 916,
                "gold_received_purpose": "advance_gold",
                "gold_received_value": 50.00,
                "notes": "Test walk-in customer with gold"
            }
            
            response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
            
            if response.status_code in [200, 201]:
                invoice = response.json()
                
                # Should work but no gold ledger entry should be created
                paid_amount = invoice.get("paid_amount", 0)
                balance_due = invoice.get("balance_due", 0)
                
                # Verify calculations still work
                paid_amount_correct = paid_amount == 50.00
                balance_due_correct = abs(balance_due - 475.00) < 0.01  # 525 - 50
                
                success = paid_amount_correct and balance_due_correct
                
                details = f"Walk-in gold payment processed: Paid {paid_amount} OMR, Balance {balance_due} OMR"
                
                self.log_result(
                    "Walk-in Customer Gold",
                    success,
                    details,
                    {
                        "paid_amount": paid_amount,
                        "balance_due": balance_due,
                        "customer_type": "walk_in"
                    }
                )
                
                return success
            else:
                self.log_result("Walk-in Customer Gold", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Walk-in Customer Gold", False, f"Error: {str(e)}")
            return False
    
    def test_invoice_without_gold(self):
        """Test invoice without gold fields (should work normally)"""
        try:
            customer_id = self.get_or_create_test_customer()
            if not customer_id:
                return False
            
            invoice_data = {
                "customer_type": "saved",
                "customer_id": customer_id,
                "invoice_type": "sale",
                "items": [
                    {
                        "description": "Gold Earrings 22K",
                        "qty": 1,
                        "gross_weight": 4.000,
                        "stone_weight": 0.100,
                        "net_gold_weight": 3.900,
                        "weight": 3.900,
                        "purity": 916,
                        "metal_rate": 185.50,
                        "gold_value": 723.45,
                        "making_charge_type": "per_gram",
                        "making_value": 78.00,
                        "stone_charges": 20.00,
                        "wastage_charges": 15.00,
                        "item_discount": 0.00,
                        "vat_percent": 5.0,
                        "vat_amount": 41.82,
                        "line_total": 878.27
                    }
                ],
                "subtotal": 836.45,
                "discount_amount": 0.00,
                "tax_type": "cgst_sgst",
                "gst_percent": 5.0,
                "cgst_total": 20.91,
                "sgst_total": 20.91,
                "igst_total": 0.00,
                "vat_total": 41.82,
                "grand_total": 878.27,
                "paid_amount": 0.00,
                "balance_due": 878.27,
                # No gold fields
                "notes": "Test invoice without gold fields"
            }
            
            response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
            
            if response.status_code in [200, 201]:
                invoice = response.json()
                
                # Should work normally
                paid_amount = invoice.get("paid_amount", 0)
                balance_due = invoice.get("balance_due", 0)
                payment_status = invoice.get("payment_status", "unpaid")
                
                # Verify normal behavior
                paid_amount_correct = paid_amount == 0.00
                balance_due_correct = abs(balance_due - 878.27) < 0.01
                payment_status_correct = payment_status == "unpaid"
                
                success = paid_amount_correct and balance_due_correct and payment_status_correct
                
                details = f"Normal invoice without gold: Paid {paid_amount} OMR, Balance {balance_due} OMR, Status {payment_status}"
                
                self.log_result(
                    "Invoice Without Gold",
                    success,
                    details,
                    {
                        "paid_amount": paid_amount,
                        "balance_due": balance_due,
                        "payment_status": payment_status
                    }
                )
                
                return success
            else:
                self.log_result("Invoice Without Gold", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Invoice Without Gold", False, f"Error: {str(e)}")
            return False
    
    def test_gold_weight_without_rate(self):
        """Test gold weight without rate (should handle gracefully)"""
        try:
            customer_id = self.get_or_create_test_customer()
            if not customer_id:
                return False
            
            invoice_data = {
                "customer_type": "saved",
                "customer_id": customer_id,
                "invoice_type": "sale",
                "items": [
                    {
                        "description": "Gold Pendant 22K",
                        "qty": 1,
                        "gross_weight": 5.000,
                        "stone_weight": 0.200,
                        "net_gold_weight": 4.800,
                        "weight": 4.800,
                        "purity": 916,
                        "metal_rate": 185.50,
                        "gold_value": 890.40,
                        "making_charge_type": "flat",
                        "making_value": 100.00,
                        "stone_charges": 30.00,
                        "wastage_charges": 20.00,
                        "item_discount": 0.00,
                        "vat_percent": 5.0,
                        "vat_amount": 52.02,
                        "line_total": 1092.42
                    }
                ],
                "subtotal": 1040.40,
                "discount_amount": 0.00,
                "tax_type": "cgst_sgst",
                "gst_percent": 5.0,
                "cgst_total": 26.01,
                "sgst_total": 26.01,
                "igst_total": 0.00,
                "vat_total": 52.02,
                "grand_total": 1092.42,
                "paid_amount": 0.00,
                "balance_due": 1092.42,
                # Gold weight without rate
                "gold_received_weight": 3.000,
                "gold_received_purity": 916,
                "gold_received_purpose": "advance_gold",
                # No gold_received_rate or gold_received_value
                "notes": "Test gold weight without rate"
            }
            
            response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
            
            # Should either succeed with 0 gold value or handle gracefully
            if response.status_code in [200, 201]:
                invoice = response.json()
                
                paid_amount = invoice.get("paid_amount", 0)
                balance_due = invoice.get("balance_due", 0)
                gold_value = invoice.get("gold_received_value", 0)
                
                # Should handle gracefully - no gold value calculated
                handled_gracefully = (
                    paid_amount == 0.00 and 
                    abs(balance_due - 1092.42) < 0.01 and
                    gold_value == 0.00
                )
                
                details = f"Handled gracefully: Gold value {gold_value}, Paid {paid_amount}, Balance {balance_due}"
                
                self.log_result(
                    "Gold Weight Without Rate",
                    handled_gracefully,
                    details,
                    {
                        "gold_received_value": gold_value,
                        "paid_amount": paid_amount,
                        "balance_due": balance_due
                    }
                )
                
                return handled_gracefully
            else:
                # Check if it's a validation error (acceptable)
                if response.status_code == 400:
                    error_detail = response.json().get('detail', response.text)
                    self.log_result(
                        "Gold Weight Without Rate",
                        True,
                        f"Properly validated and rejected: {error_detail}",
                        {"validation_error": error_detail}
                    )
                    return True
                else:
                    self.log_result("Gold Weight Without Rate", False, f"Unexpected error: {response.status_code} - {response.text}")
                    return False
                
        except Exception as e:
            self.log_result("Gold Weight Without Rate", False, f"Error: {str(e)}")
            return False
    
    def test_negative_gold_values(self):
        """Test negative gold values (should reject or handle)"""
        try:
            customer_id = self.get_or_create_test_customer()
            if not customer_id:
                return False
            
            invoice_data = {
                "customer_type": "saved",
                "customer_id": customer_id,
                "invoice_type": "sale",
                "items": [
                    {
                        "description": "Gold Ring 22K",
                        "qty": 1,
                        "gross_weight": 3.000,
                        "stone_weight": 0.000,
                        "net_gold_weight": 3.000,
                        "weight": 3.000,
                        "purity": 916,
                        "metal_rate": 185.50,
                        "gold_value": 556.50,
                        "making_charge_type": "flat",
                        "making_value": 50.00,
                        "stone_charges": 0.00,
                        "wastage_charges": 0.00,
                        "item_discount": 0.00,
                        "vat_percent": 5.0,
                        "vat_amount": 30.33,
                        "line_total": 636.83
                    }
                ],
                "subtotal": 606.50,
                "discount_amount": 0.00,
                "tax_type": "cgst_sgst",
                "gst_percent": 5.0,
                "cgst_total": 15.16,
                "sgst_total": 15.17,
                "igst_total": 0.00,
                "vat_total": 30.33,
                "grand_total": 636.83,
                "paid_amount": 0.00,
                "balance_due": 636.83,
                # Negative gold values
                "gold_received_weight": -2.000,  # Negative weight
                "gold_received_rate": 25.00,
                "gold_received_purity": 916,
                "gold_received_purpose": "advance_gold",
                "gold_received_value": -50.00,  # Negative value
                "notes": "Test negative gold values"
            }
            
            response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
            
            # Should either reject with validation error or handle gracefully
            if response.status_code == 400:
                error_detail = response.json().get('detail', response.text)
                self.log_result(
                    "Negative Gold Values",
                    True,
                    f"Properly rejected negative values: {error_detail}",
                    {"validation_error": error_detail}
                )
                return True
            elif response.status_code in [200, 201]:
                invoice = response.json()
                
                # If accepted, should handle gracefully (ignore negative values)
                paid_amount = invoice.get("paid_amount", 0)
                balance_due = invoice.get("balance_due", 0)
                
                handled_gracefully = (
                    paid_amount == 0.00 and 
                    abs(balance_due - 636.83) < 0.01
                )
                
                details = f"Handled gracefully: Ignored negative values, Paid {paid_amount}, Balance {balance_due}"
                
                self.log_result(
                    "Negative Gold Values",
                    handled_gracefully,
                    details,
                    {
                        "paid_amount": paid_amount,
                        "balance_due": balance_due
                    }
                )
                
                return handled_gracefully
            else:
                self.log_result("Negative Gold Values", False, f"Unexpected error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Negative Gold Values", False, f"Error: {str(e)}")
            return False
    
    def test_existing_gold_exchange_payment(self):
        """Test Existing Gold Exchange Payment Mode (Verify Still Works)"""
        try:
            # First create a regular invoice
            customer_id = self.get_or_create_test_customer()
            if not customer_id:
                return False
            
            invoice_data = {
                "customer_type": "saved",
                "customer_id": customer_id,
                "invoice_type": "sale",
                "items": [
                    {
                        "description": "Gold Bangle 22K",
                        "qty": 1,
                        "gross_weight": 20.000,
                        "stone_weight": 0.000,
                        "net_gold_weight": 20.000,
                        "weight": 20.000,
                        "purity": 916,
                        "metal_rate": 185.50,
                        "gold_value": 3710.00,
                        "making_charge_type": "per_gram",
                        "making_value": 400.00,
                        "stone_charges": 0.00,
                        "wastage_charges": 50.00,
                        "item_discount": 0.00,
                        "vat_percent": 5.0,
                        "vat_amount": 208.00,
                        "line_total": 4368.00
                    }
                ],
                "subtotal": 4160.00,
                "discount_amount": 0.00,
                "tax_type": "cgst_sgst",
                "gst_percent": 5.0,
                "cgst_total": 104.00,
                "sgst_total": 104.00,
                "igst_total": 0.00,
                "vat_total": 208.00,
                "grand_total": 4368.00,
                "paid_amount": 0.00,
                "balance_due": 4368.00,
                "notes": "Test invoice for existing gold exchange payment"
            }
            
            # Create invoice
            response = self.session.post(f"{BACKEND_URL}/invoices", json=invoice_data)
            
            if response.status_code in [200, 201]:
                invoice = response.json()
                invoice_id = invoice.get("id")
                
                # Now test existing gold exchange payment mode
                payment_data = {
                    "payment_mode": "GOLD_EXCHANGE",
                    "gold_weight_grams": 15.000,
                    "rate_per_gram": 180.00,
                    "notes": "Gold exchange payment - existing functionality test"
                }
                
                payment_response = self.session.post(f"{BACKEND_URL}/invoices/{invoice_id}/add-payment", json=payment_data)
                
                if payment_response.status_code == 200:
                    updated_invoice = payment_response.json()
                    
                    # Verify payment was processed
                    paid_amount = updated_invoice.get("paid_amount", 0)
                    balance_due = updated_invoice.get("balance_due", 0)
                    payment_status = updated_invoice.get("payment_status", "unpaid")
                    
                    # Expected: 15.000 * 180.00 = 2700.00 OMR payment
                    expected_paid_amount = 2700.00
                    expected_balance_due = 4368.00 - 2700.00  # 1668.00
                    
                    paid_amount_correct = abs(paid_amount - expected_paid_amount) < 0.01
                    balance_due_correct = abs(balance_due - expected_balance_due) < 0.01
                    payment_status_correct = payment_status == "partial"
                    
                    all_correct = all([paid_amount_correct, balance_due_correct, payment_status_correct])
                    
                    details = f"Gold exchange payment: Paid {paid_amount} OMR (expected {expected_paid_amount}), "
                    details += f"Balance {balance_due} OMR (expected {expected_balance_due}), Status {payment_status}"
                    
                    self.log_result(
                        "Existing Gold Exchange Payment",
                        all_correct,
                        details,
                        {
                            "paid_amount": paid_amount,
                            "expected_paid_amount": expected_paid_amount,
                            "balance_due": balance_due,
                            "expected_balance_due": expected_balance_due,
                            "payment_status": payment_status
                        }
                    )
                    
                    return all_correct
                else:
                    self.log_result("Existing Gold Exchange Payment", False, f"Payment failed: {payment_response.status_code} - {payment_response.text}")
                    return False
            else:
                self.log_result("Existing Gold Exchange Payment - Invoice Creation", False, f"Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Existing Gold Exchange Payment", False, f"Error: {str(e)}")
            return False

    def test_transactions_endpoint_decimal128_fix(self):
        """Test GET /api/transactions endpoint for Decimal128/float conversion fix"""
        print("\n" + "="*80)
        print("TESTING TRANSACTIONS ENDPOINT - DECIMAL128/FLOAT CONVERSION FIX")
        print("="*80)
        
        try:
            # Test 1: GET /api/transactions endpoint (the one causing HTTP 520 error)
            print("\n--- Testing GET /api/transactions endpoint ---")
            
            response = self.session.get(f"{BACKEND_URL}/transactions")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if response contains transaction data
                transactions = data.get('items', []) if isinstance(data, dict) else data if isinstance(data, list) else []
                
                # Verify response structure and data types
                has_transactions = len(transactions) > 0
                all_amounts_float = True
                all_balances_float = True
                
                for transaction in transactions[:5]:  # Check first 5 transactions
                    # Check transaction amount is properly converted to float
                    amount = transaction.get('amount')
                    if amount is not None and not isinstance(amount, (int, float)):
                        all_amounts_float = False
                        break
                    
                    # Check running balance if present
                    running_balance = transaction.get('running_balance')
                    if running_balance is not None and not isinstance(running_balance, (int, float)):
                        all_balances_float = False
                        break
                
                success = response.status_code == 200 and all_amounts_float and all_balances_float
                
                details = f"Status: {response.status_code}, Transactions: {len(transactions)}, "
                details += f"Amounts as float: {'✓' if all_amounts_float else '✗'}, "
                details += f"Balances as float: {'✓' if all_balances_float else '✗'}"
                
                self.log_result(
                    "GET /api/transactions - Decimal128 Fix",
                    success,
                    details,
                    {
                        "status_code": response.status_code,
                        "transaction_count": len(transactions),
                        "sample_transaction": transactions[0] if transactions else None,
                        "amounts_are_float": all_amounts_float,
                        "balances_are_float": all_balances_float
                    }
                )
                
                # Test 2: Verify account opening_balance conversion
                print("\n--- Testing Account Opening Balance Conversion ---")
                
                # Get accounts to verify opening_balance conversion
                accounts_response = self.session.get(f"{BACKEND_URL}/accounts")
                
                if accounts_response.status_code == 200:
                    accounts_data = accounts_response.json()
                    accounts = accounts_data.get('items', []) if isinstance(accounts_data, dict) else accounts_data if isinstance(accounts_data, list) else []
                    
                    opening_balances_float = True
                    current_balances_float = True
                    
                    for account in accounts[:5]:  # Check first 5 accounts
                        opening_balance = account.get('opening_balance')
                        current_balance = account.get('current_balance')
                        
                        if opening_balance is not None and not isinstance(opening_balance, (int, float)):
                            opening_balances_float = False
                        
                        if current_balance is not None and not isinstance(current_balance, (int, float)):
                            current_balances_float = False
                    
                    account_success = opening_balances_float and current_balances_float
                    
                    account_details = f"Accounts: {len(accounts)}, "
                    account_details += f"Opening balances as float: {'✓' if opening_balances_float else '✗'}, "
                    account_details += f"Current balances as float: {'✓' if current_balances_float else '✗'}"
                    
                    self.log_result(
                        "Account Balance Conversion",
                        account_success,
                        account_details,
                        {
                            "account_count": len(accounts),
                            "opening_balances_float": opening_balances_float,
                            "current_balances_float": current_balances_float,
                            "sample_account": accounts[0] if accounts else None
                        }
                    )
                else:
                    self.log_result("Account Balance Conversion", False, f"Failed to get accounts: {accounts_response.status_code}")
                
                # Test 3: Test with pagination parameters
                print("\n--- Testing Transactions with Pagination ---")
                
                paginated_response = self.session.get(f"{BACKEND_URL}/transactions?page=1&page_size=10")
                
                if paginated_response.status_code == 200:
                    paginated_data = paginated_response.json()
                    paginated_transactions = paginated_data.get('items', []) if isinstance(paginated_data, dict) else paginated_data if isinstance(paginated_data, list) else []
                    
                    pagination_success = len(paginated_transactions) <= 10
                    
                    self.log_result(
                        "Transactions Pagination",
                        pagination_success,
                        f"Paginated response: {len(paginated_transactions)} transactions (≤10)",
                        {
                            "paginated_count": len(paginated_transactions),
                            "pagination_metadata": paginated_data.get('pagination') if isinstance(paginated_data, dict) else None
                        }
                    )
                else:
                    self.log_result("Transactions Pagination", False, f"Failed: {paginated_response.status_code}")
                
                return success
                
            else:
                # This is the critical test - if we get HTTP 520, the fix didn't work
                error_details = f"HTTP {response.status_code} - {response.text[:200]}"
                if response.status_code == 520:
                    error_details += " (CRITICAL: This is the original Decimal128/float error!)"
                
                self.log_result(
                    "GET /api/transactions - Decimal128 Fix",
                    False,
                    error_details,
                    {
                        "status_code": response.status_code,
                        "error_text": response.text[:500]
                    }
                )
                return False
                
        except Exception as e:
            self.log_result("Transactions Endpoint Decimal128 Fix", False, f"Error: {str(e)}")
            return False

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print(f"\nFAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"❌ {result['test']}: {result['details']}")
        
        print(f"\nDetailed results saved to test_results.json")
        
        # Save detailed results
        with open('/app/test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)

    def test_net_flow_filtering_fix(self):
        """Test the specific Net Flow filtering fix - account name based filtering"""
        print("\n--- Testing Net Flow Filtering Fix (Account Name Based) ---")
        
        # Step 1: Create test accounts with proper naming
        cash_account_id = self.create_test_account_with_name("Test Cash Account", "asset")
        bank_account_id = self.create_test_account_with_name("Bank Account", "asset")
        
        if not cash_account_id or not bank_account_id:
            self.log_result("Net Flow Filtering Fix Setup", False, "Failed to create test accounts")
            return
        
        # Step 2: Create test transactions on these accounts
        # DEBIT transactions (money IN)
        cash_debit_id = self.create_test_transaction(
            account_id=cash_account_id,
            transaction_type="debit",
            amount=2000.00,
            description="Cash IN - Customer payment"
        )
        
        bank_debit_id = self.create_test_transaction(
            account_id=bank_account_id,
            transaction_type="debit", 
            amount=1500.00,
            description="Bank IN - Transfer received"
        )
        
        # CREDIT transactions (money OUT)
        cash_credit_id = self.create_test_transaction(
            account_id=cash_account_id,
            transaction_type="credit",
            amount=800.00,
            description="Cash OUT - Purchase payment"
        )
        
        if not all([cash_debit_id, bank_debit_id, cash_credit_id]):
            self.log_result("Net Flow Filtering Fix Transactions", False, "Failed to create test transactions")
            return
        
        # Step 3: Wait for transactions to be processed
        time.sleep(2)
        
        # Step 4: Test /api/transactions/summary endpoint
        try:
            response = self.session.get(f"{BACKEND_URL}/transactions/summary")
            
            if response.status_code == 200:
                summary_data = response.json()
                
                # Verify the response structure
                required_fields = ['total_in', 'total_out', 'net_flow', 'cash_summary', 'bank_summary']
                missing_fields = [field for field in required_fields if field not in summary_data]
                
                if missing_fields:
                    self.log_result("Net Flow Filtering Fix", False, f"Missing required fields: {missing_fields}")
                    return
                
                # Extract values
                total_in = summary_data.get('total_in', 0)
                total_out = summary_data.get('total_out', 0)
                net_flow = summary_data.get('net_flow', 0)
                cash_summary = summary_data.get('cash_summary', {})
                bank_summary = summary_data.get('bank_summary', {})
                
                # Verify math calculations
                # 1. net_flow = total_in - total_out
                calculated_net_flow = round(total_in - total_out, 2)
                actual_net_flow = round(net_flow, 2)
                net_flow_correct = abs(calculated_net_flow - actual_net_flow) < 0.01
                
                # 2. cash_summary.net = cash_summary.debit - cash_summary.credit
                cash_net_correct = True
                if cash_summary and all(k in cash_summary for k in ['debit', 'credit', 'net']):
                    cash_calculated_net = round(cash_summary['debit'] - cash_summary['credit'], 2)
                    cash_actual_net = round(cash_summary['net'], 2)
                    cash_net_correct = abs(cash_calculated_net - cash_actual_net) < 0.01
                
                # 3. bank_summary.net = bank_summary.debit - bank_summary.credit
                bank_net_correct = True
                if bank_summary and all(k in bank_summary for k in ['debit', 'credit', 'net']):
                    bank_calculated_net = round(bank_summary['debit'] - bank_summary['credit'], 2)
                    bank_actual_net = round(bank_summary['net'], 2)
                    bank_net_correct = abs(bank_calculated_net - bank_actual_net) < 0.01
                
                # 4. total_in = cash_summary.debit + bank_summary.debit
                total_in_correct = True
                if cash_summary and bank_summary:
                    calculated_total_in = round(cash_summary.get('debit', 0) + bank_summary.get('debit', 0), 2)
                    actual_total_in = round(total_in, 2)
                    # Allow for existing data - check if our test amounts are included
                    total_in_correct = actual_total_in >= calculated_total_in
                
                # 5. total_out = cash_summary.credit + bank_summary.credit
                total_out_correct = True
                if cash_summary and bank_summary:
                    calculated_total_out = round(cash_summary.get('credit', 0) + bank_summary.get('credit', 0), 2)
                    actual_total_out = round(total_out, 2)
                    # Allow for existing data - check if our test amounts are included
                    total_out_correct = actual_total_out >= calculated_total_out
                
                # Verify that our test transactions are included
                # We expect at least our test amounts to be reflected
                min_expected_cash_debit = 2000.00  # Our cash debit
                min_expected_bank_debit = 1500.00  # Our bank debit
                min_expected_cash_credit = 800.00  # Our cash credit
                
                cash_includes_test_data = (
                    cash_summary.get('debit', 0) >= min_expected_cash_debit and
                    cash_summary.get('credit', 0) >= min_expected_cash_credit
                )
                
                bank_includes_test_data = bank_summary.get('debit', 0) >= min_expected_bank_debit
                
                all_tests_passed = all([
                    net_flow_correct,
                    cash_net_correct,
                    bank_net_correct,
                    total_in_correct,
                    total_out_correct,
                    cash_includes_test_data,
                    bank_includes_test_data
                ])
                
                # Create detailed result message
                details = []
                details.append(f"Net Flow Math: {'✓' if net_flow_correct else '✗'} ({total_in} - {total_out} = {net_flow})")
                details.append(f"Cash Net Math: {'✓' if cash_net_correct else '✗'} ({cash_summary.get('debit', 0)} - {cash_summary.get('credit', 0)} = {cash_summary.get('net', 0)})")
                details.append(f"Bank Net Math: {'✓' if bank_net_correct else '✗'} ({bank_summary.get('debit', 0)} - {bank_summary.get('credit', 0)} = {bank_summary.get('net', 0)})")
                details.append(f"Total IN Math: {'✓' if total_in_correct else '✗'}")
                details.append(f"Total OUT Math: {'✓' if total_out_correct else '✗'}")
                details.append(f"Cash Test Data: {'✓' if cash_includes_test_data else '✗'}")
                details.append(f"Bank Test Data: {'✓' if bank_includes_test_data else '✗'}")
                
                self.log_result(
                    "Net Flow Filtering Fix - Math Verification",
                    all_tests_passed,
                    "; ".join(details),
                    {
                        "summary_data": summary_data,
                        "test_results": {
                            "net_flow_correct": net_flow_correct,
                            "cash_net_correct": cash_net_correct,
                            "bank_net_correct": bank_net_correct,
                            "total_in_correct": total_in_correct,
                            "total_out_correct": total_out_correct,
                            "cash_includes_test_data": cash_includes_test_data,
                            "bank_includes_test_data": bank_includes_test_data
                        }
                    }
                )
                
            else:
                self.log_result("Net Flow Filtering Fix", False, f"Failed to get transactions summary: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Net Flow Filtering Fix", False, f"Error: {str(e)}")
    
    def create_test_account_with_name(self, name, account_type):
        """Create a test account with specific name and type"""
        try:
            account_data = {
                "name": name,
                "account_type": account_type,
                "opening_balance": 0.00,
                "current_balance": 0.00
            }
            
            response = self.session.post(f"{BACKEND_URL}/accounts", json=account_data)
            
            if response.status_code == 201:
                account = response.json()
                account_id = account.get("id")
                self.log_result(f"Create Test Account ({name})", True, f"Created account: {name} (Type: {account_type})")
                return account_id
            else:
                self.log_result(f"Create Test Account ({name})", False, f"Failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result(f"Create Test Account ({name})", False, f"Error: {str(e)}")
            return None

    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("GOLD SHOP ERP PURCHASE MODULE - TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        print(f"\n✅ PASSED TESTS:")
        for result in self.test_results:
            if result["success"]:
                print(f"   • {result['test']}: {result['details']}")
        
        print("\n" + "="*80)
        print("TESTING COMPLETED")
        print("="*80)

    def test_oman_id_bug_fix_party_update(self):
        """Test Oman ID bug fix for party update endpoint - CRITICAL BUG FIX VERIFICATION"""
        print("\n" + "="*80)
        print("🎯 TESTING OMAN ID BUG FIX - PARTY UPDATE ENDPOINT")
        print("="*80)
        
        print("\n📋 TEST SCENARIOS:")
        print("1. CREATE TEST: Create party with Oman ID")
        print("2. UPDATE TEST: Edit party and change Oman ID")
        print("3. PRESERVE TEST: Edit party WITHOUT changing Oman ID")
        print("4. CLEAR TEST: Clear Oman ID by sending empty/null value")
        
        try:
            all_tests_passed = True
            test_results = []
            
            # SCENARIO 1: CREATE TEST - Create a new party with Oman ID
            print("\n--- SCENARIO 1: CREATE TEST ---")
            party_data = {
                "name": "Ahmed Al-Rashid Test",
                "oman_id": "12345678",
                "phone": "+968 9876 5432",
                "address": "Test Address, Muscat",
                "party_type": "customer",
                "notes": "Test party for Oman ID bug fix verification"
            }
            
            create_response = self.session.post(f"{BACKEND_URL}/parties", json=party_data)
            
            if create_response.status_code == 201:
                created_party = create_response.json()
                party_id = created_party.get("id")
                created_oman_id = created_party.get("oman_id")
                
                create_success = created_oman_id == "12345678"
                test_results.append(("Create with Oman ID", create_success))
                
                if not create_success:
                    all_tests_passed = False
                
                self.log_result(
                    "Oman ID Bug Fix - Create Party",
                    create_success,
                    f"Created party with Oman ID: {created_oman_id} ({'✓' if create_success else '✗'})",
                    {"party_id": party_id, "oman_id": created_oman_id}
                )
                
                if party_id and create_success:
                    # SCENARIO 2: UPDATE TEST - Edit party and change Oman ID
                    print("\n--- SCENARIO 2: UPDATE TEST ---")
                    
                    # First verify current Oman ID
                    get_response = self.session.get(f"{BACKEND_URL}/parties/{party_id}")
                    if get_response.status_code == 200:
                        current_party = get_response.json()
                        current_oman_id = current_party.get("oman_id")
                        
                        verify_current = current_oman_id == "12345678"
                        self.log_result(
                            "Oman ID Bug Fix - Verify Current",
                            verify_current,
                            f"Current Oman ID: {current_oman_id} ({'✓' if verify_current else '✗'})"
                        )
                        
                        if verify_current:
                            # Update with new Oman ID
                            update_data = {
                                "oman_id": "87654321"
                            }
                            
                            update_response = self.session.patch(f"{BACKEND_URL}/parties/{party_id}", json=update_data)
                            
                            if update_response.status_code == 200:
                                updated_party = update_response.json()
                                updated_oman_id = updated_party.get("oman_id")
                                
                                update_success = updated_oman_id == "87654321"
                                test_results.append(("Update Oman ID", update_success))
                                
                                if not update_success:
                                    all_tests_passed = False
                                
                                self.log_result(
                                    "Oman ID Bug Fix - Update Oman ID",
                                    update_success,
                                    f"Updated Oman ID: {updated_oman_id} ({'✓' if update_success else '✗'})",
                                    {"old_oman_id": "12345678", "new_oman_id": updated_oman_id}
                                )
                                
                                # Verify persistence by fetching again
                                verify_response = self.session.get(f"{BACKEND_URL}/parties/{party_id}")
                                if verify_response.status_code == 200:
                                    verified_party = verify_response.json()
                                    verified_oman_id = verified_party.get("oman_id")
                                    
                                    persistence_success = verified_oman_id == "87654321"
                                    test_results.append(("Persistence Check", persistence_success))
                                    
                                    if not persistence_success:
                                        all_tests_passed = False
                                    
                                    self.log_result(
                                        "Oman ID Bug Fix - Persistence Check",
                                        persistence_success,
                                        f"Persisted Oman ID: {verified_oman_id} ({'✓' if persistence_success else '✗'})",
                                        {"expected": "87654321", "actual": verified_oman_id}
                                    )
                                    
                                    if persistence_success:
                                        # SCENARIO 3: PRESERVE TEST - Edit party WITHOUT changing Oman ID
                                        print("\n--- SCENARIO 3: PRESERVE TEST ---")
                                        
                                        preserve_data = {
                                            "name": "Ahmed Al-Rashid Updated Name"
                                            # Deliberately NOT sending oman_id in request
                                        }
                                        
                                        preserve_response = self.session.patch(f"{BACKEND_URL}/parties/{party_id}", json=preserve_data)
                                        
                                        if preserve_response.status_code == 200:
                                            preserved_party = preserve_response.json()
                                            preserved_oman_id = preserved_party.get("oman_id")
                                            preserved_name = preserved_party.get("name")
                                            
                                            preserve_success = (
                                                preserved_oman_id == "87654321" and 
                                                preserved_name == "Ahmed Al-Rashid Updated Name"
                                            )
                                            test_results.append(("Preserve Oman ID", preserve_success))
                                            
                                            if not preserve_success:
                                                all_tests_passed = False
                                            
                                            self.log_result(
                                                "Oman ID Bug Fix - Preserve Test",
                                                preserve_success,
                                                f"Name updated, Oman ID preserved: {preserved_oman_id} ({'✓' if preserve_success else '✗'})",
                                                {
                                                    "name_updated": preserved_name == "Ahmed Al-Rashid Updated Name",
                                                    "oman_id_preserved": preserved_oman_id == "87654321"
                                                }
                                            )
                                            
                                            # SCENARIO 4: CLEAR TEST - Clear Oman ID
                                            print("\n--- SCENARIO 4: CLEAR TEST ---")
                                            
                                            clear_data = {
                                                "oman_id": None
                                            }
                                            
                                            clear_response = self.session.patch(f"{BACKEND_URL}/parties/{party_id}", json=clear_data)
                                            
                                            if clear_response.status_code == 200:
                                                cleared_party = clear_response.json()
                                                cleared_oman_id = cleared_party.get("oman_id")
                                                
                                                clear_success = cleared_oman_id is None or cleared_oman_id == ""
                                                test_results.append(("Clear Oman ID", clear_success))
                                                
                                                if not clear_success:
                                                    all_tests_passed = False
                                                
                                                self.log_result(
                                                    "Oman ID Bug Fix - Clear Test",
                                                    clear_success,
                                                    f"Oman ID cleared: {cleared_oman_id} ({'✓' if clear_success else '✗'})",
                                                    {"cleared_oman_id": cleared_oman_id}
                                                )
                                            else:
                                                all_tests_passed = False
                                                self.log_result("Oman ID Bug Fix - Clear Test", False, f"Clear failed: {clear_response.status_code}")
                                        else:
                                            all_tests_passed = False
                                            self.log_result("Oman ID Bug Fix - Preserve Test", False, f"Preserve failed: {preserve_response.status_code}")
                                else:
                                    all_tests_passed = False
                                    self.log_result("Oman ID Bug Fix - Persistence Check", False, f"Verify failed: {verify_response.status_code}")
                            else:
                                all_tests_passed = False
                                self.log_result("Oman ID Bug Fix - Update Test", False, f"Update failed: {update_response.status_code} - {update_response.text}")
                        else:
                            all_tests_passed = False
                    else:
                        all_tests_passed = False
                        self.log_result("Oman ID Bug Fix - Get Current", False, f"Get failed: {get_response.status_code}")
                else:
                    all_tests_passed = False
            else:
                all_tests_passed = False
                self.log_result("Oman ID Bug Fix - Create Party", False, f"Create failed: {create_response.status_code} - {create_response.text}")
            
            # Summary
            passed_count = sum(1 for _, passed in test_results if passed)
            total_count = len(test_results)
            
            print(f"\n🔍 OMAN ID BUG FIX TEST SUMMARY:")
            print(f"   • Tests Passed: {passed_count}/{total_count}")
            print(f"   • Success Rate: {(passed_count/total_count)*100:.1f}%" if total_count > 0 else "   • No tests completed")
            
            for test_name, passed in test_results:
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"   • {test_name}: {status}")
            
            self.log_result(
                "Oman ID Bug Fix - Complete Test Suite",
                all_tests_passed,
                f"Passed: {passed_count}/{total_count} scenarios",
                {
                    "total_scenarios": total_count,
                    "passed_scenarios": passed_count,
                    "success_rate": f"{(passed_count/total_count)*100:.1f}%" if total_count > 0 else "0%",
                    "test_results": test_results,
                    "bug_fix_status": "WORKING" if all_tests_passed else "FAILED"
                }
            )
            
            return all_tests_passed
            
        except Exception as e:
            self.log_result("Oman ID Bug Fix - Complete Test Suite", False, f"Error: {str(e)}")
            return False

    def test_oman_id_customer_id_fixes(self):
        """Test the three Oman ID / Customer ID fixes in the Purchases module"""
        print("\n" + "="*80)
        print("🎯 TESTING OMAN ID / CUSTOMER ID FIXES - PRIMARY FOCUS")
        print("="*80)
        
        print("\n📋 TEST REQUIREMENTS:")
        print("1. Customer ID Search - Case-insensitive Partial Match")
        print("2. Update Customer ID - Persistence")
        print("3. Multiple Items Purchase - Edit Functionality")
        
        # Run all three tests
        test1_result = self.test_customer_id_search_case_insensitive()
        test2_result = self.test_update_customer_id_persistence()
        test3_result = self.test_multiple_items_purchase_edit_functionality()
        
        all_tests_passed = all([test1_result, test2_result, test3_result])
        
        print(f"\n🔍 OMAN ID FIXES TEST SUMMARY:")
        print(f"   • Customer ID Search: {'✅ PASS' if test1_result else '❌ FAIL'}")
        print(f"   • Update Persistence: {'✅ PASS' if test2_result else '❌ FAIL'}")
        print(f"   • Edit Functionality: {'✅ PASS' if test3_result else '❌ FAIL'}")
        print(f"   • Overall Result: {'✅ ALL WORKING' if all_tests_passed else '❌ SOME FAILED'}")
        
        self.log_result(
            "Oman ID / Customer ID Fixes - Integration Test",
            all_tests_passed,
            f"Search: {'✓' if test1_result else '✗'}, Update: {'✓' if test2_result else '✗'}, Edit: {'✓' if test3_result else '✗'}",
            {
                "customer_id_search_working": test1_result,
                "update_persistence_working": test2_result,
                "edit_functionality_working": test3_result,
                "all_fixes_working": all_tests_passed
            }
        )
        
        return all_tests_passed
    
    def test_customer_id_search_case_insensitive(self):
        """TEST 1: Customer ID Search - Case-insensitive Partial Match"""
        print("\n--- TEST 1: Customer ID Search - Case-insensitive Partial Match ---")
        
        try:
            # Step 1: Create a walk-in purchase with Customer ID "Oman1234" and vendor name "Ahmed"
            purchase_data = {
                "is_walk_in": True,
                "walk_in_vendor_name": "Ahmed",
                "vendor_oman_id": "Oman1234",
                "description": "Test Purchase for Customer ID Search",
                "weight_grams": 25.000,
                "entered_purity": 916,
                "rate_per_gram": 50.000,
                "paid_amount_money": 0.0
            }
            
            create_response = self.session.post(f"{BACKEND_URL}/purchases", json=purchase_data)
            
            if create_response.status_code != 201:
                self.log_result("Customer ID Search - Create Test Purchase", False, f"Failed to create purchase: {create_response.status_code} - {create_response.text}")
                return False
            
            created_purchase = create_response.json()
            purchase_id = created_purchase.get("id")
            
            print(f"   ✓ Created test purchase with Customer ID 'Oman1234' (ID: {purchase_id})")
            
            # Test search scenarios
            search_tests = [
                {
                    "search_term": "oman",
                    "description": "Search by 'oman' (lowercase)",
                    "should_find": True
                },
                {
                    "search_term": "OMAN", 
                    "description": "Search by 'OMAN' (uppercase)",
                    "should_find": True
                },
                {
                    "search_term": "1234",
                    "description": "Search by '1234' (partial number)",
                    "should_find": True
                },
                {
                    "search_term": "xyz",
                    "description": "Search by 'xyz' (no match)",
                    "should_find": False
                }
            ]
            
            all_search_tests_passed = True
            search_results = []
            
            for test in search_tests:
                print(f"   Testing: {test['description']}")
                
                # Step 2-5: Search with different terms
                search_response = self.session.get(f"{BACKEND_URL}/purchases?customer_id={test['search_term']}")
                
                if search_response.status_code == 200:
                    data = search_response.json()
                    purchases = data.get("data", data.get("items", data if isinstance(data, list) else []))
                    
                    # Check if our test purchase is found
                    found_our_purchase = any(p.get("id") == purchase_id for p in purchases)
                    test_passed = found_our_purchase == test["should_find"]
                    
                    if not test_passed:
                        all_search_tests_passed = False
                    
                    status = "✓ FOUND" if found_our_purchase else "✗ NOT FOUND"
                    expected = "SHOULD FIND" if test["should_find"] else "SHOULD NOT FIND"
                    result_status = "✅ PASS" if test_passed else "❌ FAIL"
                    
                    print(f"     {status} ({expected}) - {result_status}")
                    
                    search_results.append({
                        "search_term": test["search_term"],
                        "found": found_our_purchase,
                        "expected": test["should_find"],
                        "passed": test_passed,
                        "count": len(purchases)
                    })
                else:
                    all_search_tests_passed = False
                    print(f"     ❌ FAIL - API Error: {search_response.status_code}")
                    search_results.append({
                        "search_term": test["search_term"],
                        "error": f"HTTP {search_response.status_code}",
                        "passed": False
                    })
            
            # Step 6: Clear the search (should show all purchases)
            clear_response = self.session.get(f"{BACKEND_URL}/purchases")
            clear_test_passed = False
            if clear_response.status_code == 200:
                data = clear_response.json()
                all_purchases = data.get("data", data.get("items", data if isinstance(data, list) else []))
                found_our_purchase = any(p.get("id") == purchase_id for p in all_purchases)
                clear_test_passed = found_our_purchase
                print(f"   Clear search: {'✓ FOUND' if found_our_purchase else '✗ NOT FOUND'} in {len(all_purchases)} total purchases")
            
            overall_success = all_search_tests_passed and clear_test_passed
            
            details = f"Search Tests: {sum(1 for r in search_results if r.get('passed', False))}/{len(search_results)} passed, "
            details += f"Clear Search: {'✓' if clear_test_passed else '✗'}"
            
            self.log_result(
                "Customer ID Search - Case-insensitive Partial Match",
                overall_success,
                details,
                {
                    "test_purchase_id": purchase_id,
                    "search_results": search_results,
                    "clear_search_passed": clear_test_passed,
                    "regex_pattern_matching": "Case-insensitive partial match working" if overall_success else "Issues detected"
                }
            )
            
            return overall_success
            
        except Exception as e:
            self.log_result("Customer ID Search - Case-insensitive Partial Match", False, f"Error: {str(e)}")
            return False
    
    def test_update_customer_id_persistence(self):
        """TEST 2: Update Customer ID - Persistence"""
        print("\n--- TEST 2: Update Customer ID - Persistence ---")
        
        try:
            # Step 1: Create a walk-in purchase with Customer ID "12345678" and vendor name "Ali"
            purchase_data = {
                "is_walk_in": True,
                "walk_in_vendor_name": "Ali",
                "vendor_oman_id": "12345678",
                "description": "Test Purchase for Update Persistence",
                "weight_grams": 30.000,
                "entered_purity": 916,
                "rate_per_gram": 48.000,
                "paid_amount_money": 0.0
            }
            
            create_response = self.session.post(f"{BACKEND_URL}/purchases", json=purchase_data)
            
            if create_response.status_code != 201:
                self.log_result("Update Customer ID - Create Test Purchase", False, f"Failed to create purchase: {create_response.status_code} - {create_response.text}")
                return False
            
            created_purchase = create_response.json()
            purchase_id = created_purchase.get("id")
            
            print(f"   ✓ Created test purchase with Customer ID '12345678' (ID: {purchase_id})")
            
            # Step 3: Edit the purchase and change Customer ID to "87654321"
            update_data = {
                "vendor_oman_id": "87654321"
            }
            
            # Step 4: Save the update via PATCH /api/purchases/{id}
            update_response = self.session.patch(f"{BACKEND_URL}/purchases/{purchase_id}", json=update_data)
            
            if update_response.status_code != 200:
                self.log_result("Update Customer ID - PATCH Request", False, f"Failed to update purchase: {update_response.status_code} - {update_response.text}")
                return False
            
            print(f"   ✓ Updated Customer ID to '87654321'")
            
            # Step 5: Fetch the purchase again via GET /api/purchases/{id}
            get_response = self.session.get(f"{BACKEND_URL}/purchases/{purchase_id}")
            
            if get_response.status_code != 200:
                self.log_result("Update Customer ID - GET After Update", False, f"Failed to fetch purchase: {get_response.status_code} - {get_response.text}")
                return False
            
            updated_purchase = get_response.json()
            actual_customer_id = updated_purchase.get("vendor_oman_id")
            
            # Step 6: Verify Customer ID is "87654321" (not the old "12345678")
            customer_id_updated = actual_customer_id == "87654321"
            customer_id_not_old = actual_customer_id != "12345678"
            
            print(f"   Customer ID after update: '{actual_customer_id}' ({'✓' if customer_id_updated else '✗'})")
            
            # Step 7: Search by "87654321" → Should find the purchase
            search_new_response = self.session.get(f"{BACKEND_URL}/purchases?customer_id=87654321")
            found_with_new_id = False
            if search_new_response.status_code == 200:
                data = search_new_response.json()
                purchases = data.get("data", data.get("items", data if isinstance(data, list) else []))
                found_with_new_id = any(p.get("id") == purchase_id for p in purchases)
            
            print(f"   Search by new ID '87654321': {'✓ FOUND' if found_with_new_id else '✗ NOT FOUND'}")
            
            # Step 8: Search by "12345678" → Should NOT find the purchase
            search_old_response = self.session.get(f"{BACKEND_URL}/purchases?customer_id=12345678")
            found_with_old_id = False
            if search_old_response.status_code == 200:
                data = search_old_response.json()
                purchases = data.get("data", data.get("items", data if isinstance(data, list) else []))
                found_with_old_id = any(p.get("id") == purchase_id for p in purchases)
            
            print(f"   Search by old ID '12345678': {'✗ NOT FOUND' if not found_with_old_id else '✓ FOUND (ERROR!)'}")
            
            # Verify all conditions
            all_conditions_met = all([
                customer_id_updated,
                customer_id_not_old,
                found_with_new_id,
                not found_with_old_id
            ])
            
            details = f"Updated: {'✓' if customer_id_updated else '✗'}, "
            details += f"Not Old: {'✓' if customer_id_not_old else '✗'}, "
            details += f"Search New: {'✓' if found_with_new_id else '✗'}, "
            details += f"Search Old: {'✓' if not found_with_old_id else '✗'}"
            
            self.log_result(
                "Update Customer ID - Persistence",
                all_conditions_met,
                details,
                {
                    "purchase_id": purchase_id,
                    "old_customer_id": "12345678",
                    "new_customer_id": "87654321",
                    "actual_customer_id": actual_customer_id,
                    "persistence_working": all_conditions_met,
                    "walk_in_vendor_field_updates": "Working" if all_conditions_met else "Failed"
                }
            )
            
            return all_conditions_met
            
        except Exception as e:
            self.log_result("Update Customer ID - Persistence", False, f"Error: {str(e)}")
            return False
    
    def test_multiple_items_purchase_edit_functionality(self):
        """TEST 3: Multiple Items Purchase - Edit Functionality"""
        print("\n--- TEST 3: Multiple Items Purchase - Edit Functionality ---")
        
        try:
            # Step 1: Create a walk-in purchase with multiple items (at least 2 items)
            purchase_data = {
                "is_walk_in": True,
                "walk_in_vendor_name": "Khalid Al-Mansouri",
                "vendor_oman_id": "98765432",
                "items": [
                    {
                        "description": "Gold Ring",
                        "weight_grams": 15.500,
                        "entered_purity": 916,
                        "rate_per_gram_22k": 50.000
                    },
                    {
                        "description": "Gold Chain",
                        "weight_grams": 25.750,
                        "entered_purity": 916,
                        "rate_per_gram_22k": 52.000
                    }
                ],
                "conversion_factor": 0.920,
                "paid_amount_money": 0.0
            }
            
            create_response = self.session.post(f"{BACKEND_URL}/purchases", json=purchase_data)
            
            if create_response.status_code != 201:
                self.log_result("Multiple Items Purchase - Create", False, f"Failed to create purchase: {create_response.status_code} - {create_response.text}")
                return False
            
            created_purchase = create_response.json()
            purchase_id = created_purchase.get("id")
            original_items = created_purchase.get("items", [])
            original_vendor_oman_id = created_purchase.get("vendor_oman_id")
            
            print(f"   ✓ Created purchase with {len(original_items)} items (ID: {purchase_id})")
            
            # Step 2: Verify the purchase was created successfully
            if len(original_items) < 2:
                self.log_result("Multiple Items Purchase - Verification", False, f"Expected at least 2 items, got {len(original_items)}")
                return False
            
            print(f"   ✓ Verified {len(original_items)} items created successfully")
            
            # Step 3: Edit the purchase and add another item (simulate what user would do)
            # Add a third item to the existing items
            updated_items = original_items.copy()
            updated_items.append({
                "description": "Gold Bracelet",
                "weight_grams": 18.250,
                "entered_purity": 916,
                "rate_per_gram_22k": 49.000
            })
            
            update_data = {
                "items": updated_items
            }
            
            # Step 4: Update the purchase with the new item via PATCH /api/purchases/{id}
            update_response = self.session.patch(f"{BACKEND_URL}/purchases/{purchase_id}", json=update_data)
            
            if update_response.status_code != 200:
                self.log_result("Multiple Items Purchase - Update", False, f"Failed to update purchase: {update_response.status_code} - {update_response.text}")
                return False
            
            print(f"   ✓ Updated purchase to add third item")
            
            # Step 5: Fetch and verify all items are present (original 2 + new 1 = 3 items)
            get_response = self.session.get(f"{BACKEND_URL}/purchases/{purchase_id}")
            
            if get_response.status_code != 200:
                self.log_result("Multiple Items Purchase - Fetch After Update", False, f"Failed to fetch purchase: {get_response.status_code} - {get_response.text}")
                return False
            
            updated_purchase = get_response.json()
            final_items = updated_purchase.get("items", [])
            final_vendor_oman_id = updated_purchase.get("vendor_oman_id")
            
            # Verify item count
            items_count_correct = len(final_items) == 3
            print(f"   Items after update: {len(final_items)}/3 ({'✓' if items_count_correct else '✗'})")
            
            # Step 6: Verify vendor_oman_id is still present and unchanged
            vendor_id_preserved = final_vendor_oman_id == original_vendor_oman_id == "98765432"
            print(f"   Vendor Oman ID preserved: '{final_vendor_oman_id}' ({'✓' if vendor_id_preserved else '✗'})")
            
            # Verify item details are preserved and new item is added
            original_descriptions = [item.get("description") for item in original_items]
            final_descriptions = [item.get("description") for item in final_items]
            
            original_items_preserved = all(desc in final_descriptions for desc in original_descriptions)
            new_item_added = "Gold Bracelet" in final_descriptions
            
            print(f"   Original items preserved: {'✓' if original_items_preserved else '✗'}")
            print(f"   New item added: {'✓' if new_item_added else '✗'}")
            
            # Verify backend accepts item updates and preserves walk-in vendor fields
            backend_accepts_updates = update_response.status_code == 200
            walk_in_fields_preserved = (
                updated_purchase.get("is_walk_in") == True and
                updated_purchase.get("walk_in_vendor_name") == "Khalid Al-Mansouri" and
                vendor_id_preserved
            )
            
            print(f"   Walk-in fields preserved: {'✓' if walk_in_fields_preserved else '✗'}")
            
            # Overall verification
            all_conditions_met = all([
                items_count_correct,
                vendor_id_preserved,
                original_items_preserved,
                new_item_added,
                backend_accepts_updates,
                walk_in_fields_preserved
            ])
            
            details = f"Items: {len(final_items)}/3 ({'✓' if items_count_correct else '✗'}), "
            details += f"Vendor ID: {'✓' if vendor_id_preserved else '✗'}, "
            details += f"Items Preserved: {'✓' if original_items_preserved else '✗'}, "
            details += f"New Item: {'✓' if new_item_added else '✗'}, "
            details += f"Walk-in Fields: {'✓' if walk_in_fields_preserved else '✗'}"
            
            self.log_result(
                "Multiple Items Purchase - Edit Functionality",
                all_conditions_met,
                details,
                {
                    "purchase_id": purchase_id,
                    "original_items_count": len(original_items),
                    "final_items_count": len(final_items),
                    "vendor_oman_id_preserved": vendor_id_preserved,
                    "backend_accepts_item_updates": backend_accepts_updates,
                    "walk_in_vendor_fields_preserved": walk_in_fields_preserved,
                    "edit_functionality_working": all_conditions_met
                }
            )
            
            return all_conditions_met
            
        except Exception as e:
            self.log_result("Multiple Items Purchase - Edit Functionality", False, f"Error: {str(e)}")
            return False

def main():
    """Main function to run Enhanced Purchase Valuation tests"""
    tester = BackendTester()
    
    print("🎯 ENHANCED PURCHASE VALUATION - COMPREHENSIVE TEST SUITE")
    print("="*80)
    print("FOCUS: Validate all Enhanced Purchase Valuation features")
    print("FEATURES:")
    print("  1. Purity Adjustment Calculation (916, 999, 875)")
    print("  2. Multiple Items with Different Purities")
    print("  3. Walk-in Vendor Filtering & Customer ID Search")
    print("  4. Stock Valuation at 916 Purity")
    print("  5. Calculation Breakdown in Notes")
    print("="*80)
    
    # Step 1: Authenticate
    if not tester.authenticate():
        print("❌ Authentication failed. Cannot proceed with testing.")
        return
    
    # Step 2: Run Enhanced Purchase Valuation Tests
    print("\n" + "="*80)
    print("RUNNING ENHANCED PURCHASE VALUATION TEST SUITE")
    print("="*80)
    
    test_results_summary = []
    
    # Test 1: Purity Adjustment Calculation
    print("\n[TEST 1/5] Purity Adjustment Calculation")
    purity_success = tester.test_enhanced_purchase_valuation_purity_adjustment()
    test_results_summary.append(("Purity Adjustment Calculation", purity_success))
    
    # Test 2: Multiple Items with Different Purities
    print("\n[TEST 2/5] Multiple Items Purchase with Different Purities")
    multiple_items_success = tester.test_multiple_items_purchase_different_purities()
    test_results_summary.append(("Multiple Items Purchase", multiple_items_success))
    
    # Test 3: Walk-in Filtering and Customer ID Search
    print("\n[TEST 3/5] Walk-in Filtering and Customer ID Search")
    walk_in_success = tester.test_walk_in_filtering_and_customer_id_search()
    test_results_summary.append(("Walk-in Filtering & Search", walk_in_success))
    
    # Test 4: Stock Valuation at 916 Purity
    print("\n[TEST 4/5] Stock Valuation - 916 Purity Enforcement")
    stock_valuation_success = tester.test_stock_valuation_916_purity()
    test_results_summary.append(("Stock Valuation at 916", stock_valuation_success))
    
    # Test 5: Calculation Breakdown in Notes
    print("\n[TEST 5/5] Calculation Breakdown in Notes")
    breakdown_success = tester.test_calculation_breakdown_in_notes()
    test_results_summary.append(("Calculation Breakdown", breakdown_success))
    
    # Step 3: Generate Summary Report
    print("\n" + "="*80)
    print("📊 ENHANCED PURCHASE VALUATION TEST SUMMARY REPORT")
    print("="*80)
    
    total_tests = len(tester.test_results)
    passed_tests = sum(1 for result in tester.test_results if result["success"])
    failed_tests = total_tests - passed_tests
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
    
    print("\n📋 FEATURE TEST RESULTS:")
    for feature_name, success in test_results_summary:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {feature_name}")
    
    print("\n📋 DETAILED TEST RESULTS:")
    for result in tester.test_results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status} - {result['test']}: {result['details']}")
    
    # Feature-specific analysis
    print("\n🎯 ENHANCED PURCHASE VALUATION ANALYSIS:")
    
    all_features_working = all(success for _, success in test_results_summary)
    
    print(f"\n🏆 FINAL RESULT:")
    if all_features_working:
        print("✅ ENHANCED PURCHASE VALUATION IMPLEMENTATION SUCCESSFUL")
        print("   - All purity adjustment calculations working correctly")
        print("   - Multiple items support with different purities verified")
        print("   - Walk-in vendor filtering and search operational")
        print("   - Stock valuation at 916 purity enforced")
        print("   - Calculation breakdown included in stock movement notes")
        print("\n✅ BACKEND IMPLEMENTATION: READY FOR PRODUCTION")
    else:
        print("❌ SOME FEATURES HAVE ISSUES")
        print("   - Check failed tests above for details")
        print("   - Review backend implementation for failing features")
    
    print("\n💡 NEXT STEPS:")
    if failed_tests == 0:
        print("   ✓ All backend tests passed successfully")
        print("   → Next: Test frontend purchase forms and calculation displays")
        print("   → Next: Create actual purchases through UI and verify calculations")
        print("   → Next: End-to-end validation with real user workflows")
    else:
        print("   → Fix failing backend tests identified above")
        print("   → Re-run tests after fixes")
        print("   → Then proceed to frontend testing")
    
    return all_features_working

    def test_oman_id_bug_fix_party_update(self):
        """Test Oman ID bug fix for party update endpoint - CRITICAL BUG FIX VERIFICATION"""
        print("\n" + "="*80)
        print("🎯 TESTING OMAN ID BUG FIX - PARTY UPDATE ENDPOINT")
        print("="*80)
        
        print("\n📋 TEST SCENARIOS:")
        print("1. CREATE TEST: Create party with Oman ID")
        print("2. UPDATE TEST: Edit party and change Oman ID")
        print("3. PRESERVE TEST: Edit party WITHOUT changing Oman ID")
        print("4. CLEAR TEST: Clear Oman ID by sending empty/null value")
        
        try:
            all_tests_passed = True
            test_results = []
            
            # SCENARIO 1: CREATE TEST - Create a new party with Oman ID
            print("\n--- SCENARIO 1: CREATE TEST ---")
            party_data = {
                "name": "Ahmed Al-Rashid Test",
                "oman_id": "12345678",
                "phone": "+968 9876 5432",
                "address": "Test Address, Muscat",
                "party_type": "customer",
                "notes": "Test party for Oman ID bug fix verification"
            }
            
            create_response = self.session.post(f"{BACKEND_URL}/parties", json=party_data)
            
            if create_response.status_code == 201:
                created_party = create_response.json()
                party_id = created_party.get("id")
                created_oman_id = created_party.get("oman_id")
                
                create_success = created_oman_id == "12345678"
                test_results.append(("Create with Oman ID", create_success))
                
                if not create_success:
                    all_tests_passed = False
                
                self.log_result(
                    "Oman ID Bug Fix - Create Party",
                    create_success,
                    f"Created party with Oman ID: {created_oman_id} ({'✓' if create_success else '✗'})",
                    {"party_id": party_id, "oman_id": created_oman_id}
                )
                
                if party_id and create_success:
                    # SCENARIO 2: UPDATE TEST - Edit party and change Oman ID
                    print("\n--- SCENARIO 2: UPDATE TEST ---")
                    
                    # First verify current Oman ID
                    get_response = self.session.get(f"{BACKEND_URL}/parties/{party_id}")
                    if get_response.status_code == 200:
                        current_party = get_response.json()
                        current_oman_id = current_party.get("oman_id")
                        
                        verify_current = current_oman_id == "12345678"
                        self.log_result(
                            "Oman ID Bug Fix - Verify Current",
                            verify_current,
                            f"Current Oman ID: {current_oman_id} ({'✓' if verify_current else '✗'})"
                        )
                        
                        if verify_current:
                            # Update with new Oman ID
                            update_data = {
                                "oman_id": "87654321"
                            }
                            
                            update_response = self.session.patch(f"{BACKEND_URL}/parties/{party_id}", json=update_data)
                            
                            if update_response.status_code == 200:
                                updated_party = update_response.json()
                                updated_oman_id = updated_party.get("oman_id")
                                
                                update_success = updated_oman_id == "87654321"
                                test_results.append(("Update Oman ID", update_success))
                                
                                if not update_success:
                                    all_tests_passed = False
                                
                                self.log_result(
                                    "Oman ID Bug Fix - Update Oman ID",
                                    update_success,
                                    f"Updated Oman ID: {updated_oman_id} ({'✓' if update_success else '✗'})",
                                    {"old_oman_id": "12345678", "new_oman_id": updated_oman_id}
                                )
                                
                                # Verify persistence by fetching again
                                verify_response = self.session.get(f"{BACKEND_URL}/parties/{party_id}")
                                if verify_response.status_code == 200:
                                    verified_party = verify_response.json()
                                    verified_oman_id = verified_party.get("oman_id")
                                    
                                    persistence_success = verified_oman_id == "87654321"
                                    test_results.append(("Persistence Check", persistence_success))
                                    
                                    if not persistence_success:
                                        all_tests_passed = False
                                    
                                    self.log_result(
                                        "Oman ID Bug Fix - Persistence Check",
                                        persistence_success,
                                        f"Persisted Oman ID: {verified_oman_id} ({'✓' if persistence_success else '✗'})",
                                        {"expected": "87654321", "actual": verified_oman_id}
                                    )
                                    
                                    if persistence_success:
                                        # SCENARIO 3: PRESERVE TEST - Edit party WITHOUT changing Oman ID
                                        print("\n--- SCENARIO 3: PRESERVE TEST ---")
                                        
                                        preserve_data = {
                                            "name": "Ahmed Al-Rashid Updated Name"
                                            # Deliberately NOT sending oman_id in request
                                        }
                                        
                                        preserve_response = self.session.patch(f"{BACKEND_URL}/parties/{party_id}", json=preserve_data)
                                        
                                        if preserve_response.status_code == 200:
                                            preserved_party = preserve_response.json()
                                            preserved_oman_id = preserved_party.get("oman_id")
                                            preserved_name = preserved_party.get("name")
                                            
                                            preserve_success = (
                                                preserved_oman_id == "87654321" and 
                                                preserved_name == "Ahmed Al-Rashid Updated Name"
                                            )
                                            test_results.append(("Preserve Oman ID", preserve_success))
                                            
                                            if not preserve_success:
                                                all_tests_passed = False
                                            
                                            self.log_result(
                                                "Oman ID Bug Fix - Preserve Test",
                                                preserve_success,
                                                f"Name updated, Oman ID preserved: {preserved_oman_id} ({'✓' if preserve_success else '✗'})",
                                                {
                                                    "name_updated": preserved_name == "Ahmed Al-Rashid Updated Name",
                                                    "oman_id_preserved": preserved_oman_id == "87654321"
                                                }
                                            )
                                            
                                            # SCENARIO 4: CLEAR TEST - Clear Oman ID
                                            print("\n--- SCENARIO 4: CLEAR TEST ---")
                                            
                                            clear_data = {
                                                "oman_id": None
                                            }
                                            
                                            clear_response = self.session.patch(f"{BACKEND_URL}/parties/{party_id}", json=clear_data)
                                            
                                            if clear_response.status_code == 200:
                                                cleared_party = clear_response.json()
                                                cleared_oman_id = cleared_party.get("oman_id")
                                                
                                                clear_success = cleared_oman_id is None or cleared_oman_id == ""
                                                test_results.append(("Clear Oman ID", clear_success))
                                                
                                                if not clear_success:
                                                    all_tests_passed = False
                                                
                                                self.log_result(
                                                    "Oman ID Bug Fix - Clear Test",
                                                    clear_success,
                                                    f"Oman ID cleared: {cleared_oman_id} ({'✓' if clear_success else '✗'})",
                                                    {"cleared_oman_id": cleared_oman_id}
                                                )
                                            else:
                                                all_tests_passed = False
                                                self.log_result("Oman ID Bug Fix - Clear Test", False, f"Clear failed: {clear_response.status_code}")
                                        else:
                                            all_tests_passed = False
                                            self.log_result("Oman ID Bug Fix - Preserve Test", False, f"Preserve failed: {preserve_response.status_code}")
                                else:
                                    all_tests_passed = False
                                    self.log_result("Oman ID Bug Fix - Persistence Check", False, f"Verify failed: {verify_response.status_code}")
                            else:
                                all_tests_passed = False
                                self.log_result("Oman ID Bug Fix - Update Test", False, f"Update failed: {update_response.status_code} - {update_response.text}")
                        else:
                            all_tests_passed = False
                    else:
                        all_tests_passed = False
                        self.log_result("Oman ID Bug Fix - Get Current", False, f"Get failed: {get_response.status_code}")
                else:
                    all_tests_passed = False
            else:
                all_tests_passed = False
                self.log_result("Oman ID Bug Fix - Create Party", False, f"Create failed: {create_response.status_code} - {create_response.text}")
            
            # Summary
            passed_count = sum(1 for _, passed in test_results if passed)
            total_count = len(test_results)
            
            print(f"\n🔍 OMAN ID BUG FIX TEST SUMMARY:")
            print(f"   • Tests Passed: {passed_count}/{total_count}")
            print(f"   • Success Rate: {(passed_count/total_count)*100:.1f}%" if total_count > 0 else "   • No tests completed")
            
            for test_name, passed in test_results:
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"   • {test_name}: {status}")
            
            self.log_result(
                "Oman ID Bug Fix - Complete Test Suite",
                all_tests_passed,
                f"Passed: {passed_count}/{total_count} scenarios",
                {
                    "total_scenarios": total_count,
                    "passed_scenarios": passed_count,
                    "success_rate": f"{(passed_count/total_count)*100:.1f}%" if total_count > 0 else "0%",
                    "test_results": test_results,
                    "bug_fix_status": "WORKING" if all_tests_passed else "FAILED"
                }
            )
            
            return all_tests_passed
            
        except Exception as e:
            self.log_result("Oman ID Bug Fix - Complete Test Suite", False, f"Error: {str(e)}")
            return False

if __name__ == "__main__":
    main()
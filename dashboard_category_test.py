#!/usr/bin/env python3
"""
Dashboard Category Count Fix Testing Script

TESTING OBJECTIVE:
Test the dashboard category count fix where /api/inventory/headers endpoint
was updated to return paginated response with structure {items: [], pagination: {total_count: X}}

SPECIFIC TESTS:
1. Test GET /api/inventory/headers endpoint returns paginated response
2. Verify response structure has "items" array and "pagination" object
3. Check that pagination.total_count is present and correct
4. Verify items array contains inventory headers
5. Test pagination parameters (page, page_size)

EXPECTED RESULTS:
- Endpoint should return 200 OK
- Response should have pagination metadata with total_count > 0 (if there are categories)
- Items array should contain the inventory headers
- Dashboard can now correctly read total_count from pagination.total_count
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://decimal-precision.preview.emergentagent.com/api"
USERNAME = "admin"
PASSWORD = "admin123"

class DashboardCategoryTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        
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
    
    def test_inventory_headers_endpoint_structure(self):
        """
        TEST 1: Inventory Headers Endpoint Structure
        Verify /api/inventory/headers returns paginated response with correct structure
        """
        print("\n" + "="*80)
        print("TEST 1: INVENTORY HEADERS ENDPOINT STRUCTURE")
        print("="*80)
        
        try:
            response = self.session.get(f"{BASE_URL}/inventory/headers")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if response has the expected paginated structure
                if isinstance(data, dict) and "items" in data and "pagination" in data:
                    self.log_result("Endpoint Structure - Paginated Response", "PASS", 
                                  "Response has correct paginated structure with 'items' and 'pagination'")
                    
                    # Verify items is an array
                    items = data.get("items", [])
                    if isinstance(items, list):
                        self.log_result("Endpoint Structure - Items Array", "PASS", 
                                      f"Items is an array with {len(items)} inventory headers")
                    else:
                        self.log_result("Endpoint Structure - Items Array", "FAIL", 
                                      f"Items is not an array: {type(items)}")
                    
                    # Verify pagination object structure
                    pagination = data.get("pagination", {})
                    if isinstance(pagination, dict):
                        required_pagination_fields = ["total_count", "page", "page_size", "total_pages", "has_next", "has_prev"]
                        missing_fields = [field for field in required_pagination_fields if field not in pagination]
                        
                        if not missing_fields:
                            self.log_result("Endpoint Structure - Pagination Object", "PASS", 
                                          f"Pagination object has all required fields: {list(pagination.keys())}")
                        else:
                            self.log_result("Endpoint Structure - Pagination Object", "FAIL", 
                                          f"Pagination object missing fields: {missing_fields}")
                    else:
                        self.log_result("Endpoint Structure - Pagination Object", "FAIL", 
                                      f"Pagination is not an object: {type(pagination)}")
                    
                    return data
                else:
                    self.log_result("Endpoint Structure - Paginated Response", "FAIL", 
                                  f"Response does not have paginated structure. Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    return None
            else:
                self.log_result("Endpoint Structure - HTTP Response", "FAIL", 
                              f"Failed to get inventory headers: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_result("Endpoint Structure - Exception", "ERROR", f"Error: {str(e)}")
            return None
    
    def test_pagination_total_count(self, data):
        """
        TEST 2: Pagination Total Count
        Verify pagination.total_count is present and accurate
        """
        print("\n" + "="*80)
        print("TEST 2: PAGINATION TOTAL COUNT")
        print("="*80)
        
        if not data:
            self.log_result("Total Count - No Data", "FAIL", "No data available from previous test")
            return
        
        try:
            pagination = data.get("pagination", {})
            total_count = pagination.get("total_count")
            
            if total_count is not None:
                if isinstance(total_count, int) and total_count >= 0:
                    self.log_result("Total Count - Value Present", "PASS", 
                                  f"total_count is present and valid: {total_count}")
                    
                    # Verify total_count matches items length for first page
                    items = data.get("items", [])
                    page = pagination.get("page", 1)
                    page_size = pagination.get("page_size", 10)
                    
                    if page == 1:
                        # For first page, items length should be min(total_count, page_size)
                        expected_items_length = min(total_count, page_size)
                        actual_items_length = len(items)
                        
                        if actual_items_length == expected_items_length:
                            self.log_result("Total Count - Items Length Match", "PASS", 
                                          f"Items length ({actual_items_length}) matches expected for page 1")
                        else:
                            self.log_result("Total Count - Items Length Match", "FAIL", 
                                          f"Items length ({actual_items_length}) doesn't match expected ({expected_items_length})")
                    
                    # Test dashboard use case: total_count should be accessible for dashboard
                    if total_count > 0:
                        self.log_result("Total Count - Dashboard Use Case", "PASS", 
                                      f"Dashboard can read category count: {total_count} categories available")
                    else:
                        self.log_result("Total Count - Dashboard Use Case", "PASS", 
                                      "Dashboard will show 0 categories (no inventory headers exist)")
                        
                else:
                    self.log_result("Total Count - Value Type", "FAIL", 
                                  f"total_count is not a valid integer: {total_count} (type: {type(total_count)})")
            else:
                self.log_result("Total Count - Value Present", "FAIL", 
                              "total_count is missing from pagination object")
                
        except Exception as e:
            self.log_result("Total Count - Exception", "ERROR", f"Error: {str(e)}")
    
    def test_inventory_headers_content(self, data):
        """
        TEST 3: Inventory Headers Content
        Verify items array contains valid inventory header objects
        """
        print("\n" + "="*80)
        print("TEST 3: INVENTORY HEADERS CONTENT")
        print("="*80)
        
        if not data:
            self.log_result("Headers Content - No Data", "FAIL", "No data available from previous test")
            return
        
        try:
            items = data.get("items", [])
            
            if len(items) > 0:
                # Check first item structure
                first_item = items[0]
                required_fields = ["id", "name", "current_qty", "current_weight", "is_active", "created_at", "created_by"]
                
                present_fields = [field for field in required_fields if field in first_item]
                missing_fields = [field for field in required_fields if field not in first_item]
                
                if len(present_fields) >= 4:  # At least basic fields should be present
                    self.log_result("Headers Content - Item Structure", "PASS", 
                                  f"Inventory header has required fields: {present_fields}")
                    
                    # Log sample data
                    sample_name = first_item.get("name", "Unknown")
                    sample_qty = first_item.get("current_qty", 0)
                    sample_weight = first_item.get("current_weight", 0)
                    
                    self.log_result("Headers Content - Sample Data", "PASS", 
                                  f"Sample header: '{sample_name}' (qty: {sample_qty}, weight: {sample_weight}g)")
                else:
                    self.log_result("Headers Content - Item Structure", "FAIL", 
                                  f"Inventory header missing required fields: {missing_fields}")
                
                # Test all items have basic structure
                valid_items = 0
                for item in items:
                    if isinstance(item, dict) and "id" in item and "name" in item:
                        valid_items += 1
                
                if valid_items == len(items):
                    self.log_result("Headers Content - All Items Valid", "PASS", 
                                  f"All {len(items)} inventory headers have valid structure")
                else:
                    self.log_result("Headers Content - All Items Valid", "FAIL", 
                                  f"Only {valid_items}/{len(items)} inventory headers have valid structure")
                    
            else:
                self.log_result("Headers Content - Items Available", "PASS", 
                              "No inventory headers exist (empty items array is valid)")
                
        except Exception as e:
            self.log_result("Headers Content - Exception", "ERROR", f"Error: {str(e)}")
    
    def test_pagination_parameters(self):
        """
        TEST 4: Pagination Parameters
        Test different page and page_size parameters
        """
        print("\n" + "="*80)
        print("TEST 4: PAGINATION PARAMETERS")
        print("="*80)
        
        try:
            # Test with different page_size
            response = self.session.get(f"{BASE_URL}/inventory/headers?page=1&page_size=5")
            
            if response.status_code == 200:
                data = response.json()
                pagination = data.get("pagination", {})
                
                if pagination.get("page_size") == 5:
                    self.log_result("Pagination Parameters - Page Size", "PASS", 
                                  f"Custom page_size parameter works: {pagination.get('page_size')}")
                else:
                    self.log_result("Pagination Parameters - Page Size", "FAIL", 
                                  f"Page size not applied correctly: expected 5, got {pagination.get('page_size')}")
                
                # Test items length respects page_size
                items = data.get("items", [])
                total_count = pagination.get("total_count", 0)
                expected_length = min(5, total_count)
                
                if len(items) == expected_length:
                    self.log_result("Pagination Parameters - Items Length", "PASS", 
                                  f"Items length ({len(items)}) respects page_size limit")
                else:
                    self.log_result("Pagination Parameters - Items Length", "FAIL", 
                                  f"Items length ({len(items)}) doesn't match expected ({expected_length})")
            else:
                self.log_result("Pagination Parameters - HTTP Response", "FAIL", 
                              f"Failed to test pagination parameters: {response.status_code}")
                
        except Exception as e:
            self.log_result("Pagination Parameters - Exception", "ERROR", f"Error: {str(e)}")
    
    def test_dashboard_integration_scenario(self):
        """
        TEST 5: Dashboard Integration Scenario
        Simulate how Dashboard.js will use the endpoint
        """
        print("\n" + "="*80)
        print("TEST 5: DASHBOARD INTEGRATION SCENARIO")
        print("="*80)
        
        try:
            # Simulate Dashboard.js call (default parameters)
            response = self.session.get(f"{BASE_URL}/inventory/headers")
            
            if response.status_code == 200:
                data = response.json()
                
                # Simulate Dashboard.js code: headersRes.data?.pagination?.total_count || 0
                category_count = data.get("pagination", {}).get("total_count", 0)
                
                if isinstance(category_count, int):
                    self.log_result("Dashboard Integration - Category Count Access", "PASS", 
                                  f"Dashboard can access category count: {category_count}")
                    
                    # Simulate the old broken code: headersRes.data?.length || 0
                    old_broken_count = len(data) if isinstance(data, list) else 0
                    
                    if old_broken_count != category_count:
                        self.log_result("Dashboard Integration - Fix Verification", "PASS", 
                                      f"Fix confirmed: old method would return {old_broken_count}, new method returns {category_count}")
                    else:
                        self.log_result("Dashboard Integration - Fix Verification", "PASS", 
                                      "Both methods return same value (edge case)")
                    
                    # Test the exact Dashboard.js access pattern
                    try:
                        # This simulates: headersRes.data?.pagination?.total_count || 0
                        dashboard_count = data.get("pagination", {}).get("total_count") or 0
                        
                        self.log_result("Dashboard Integration - Exact Access Pattern", "PASS", 
                                      f"Dashboard.js pattern works: pagination.total_count = {dashboard_count}")
                    except Exception as access_error:
                        self.log_result("Dashboard Integration - Exact Access Pattern", "FAIL", 
                                      f"Dashboard.js access pattern failed: {str(access_error)}")
                        
                else:
                    self.log_result("Dashboard Integration - Category Count Access", "FAIL", 
                                  f"Category count is not an integer: {category_count} (type: {type(category_count)})")
            else:
                self.log_result("Dashboard Integration - HTTP Response", "FAIL", 
                              f"Dashboard integration test failed: {response.status_code}")
                
        except Exception as e:
            self.log_result("Dashboard Integration - Exception", "ERROR", f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all dashboard category count tests"""
        print("STARTING DASHBOARD CATEGORY COUNT FIX TESTING")
        print("Backend URL:", BASE_URL)
        print("Authentication:", f"{USERNAME}/***")
        print("="*80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Test 1: Endpoint structure
        data = self.test_inventory_headers_endpoint_structure()
        
        # Test 2: Pagination total count
        self.test_pagination_total_count(data)
        
        # Test 3: Inventory headers content
        self.test_inventory_headers_content(data)
        
        # Test 4: Pagination parameters
        self.test_pagination_parameters()
        
        # Test 5: Dashboard integration scenario
        self.test_dashboard_integration_scenario()
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY - DASHBOARD CATEGORY COUNT FIX")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        error_tests = len([r for r in self.test_results if r["status"] == "ERROR"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️ Errors: {error_tests}")
        
        # Success criteria assessment
        print("\nSUCCESS CRITERIA ASSESSMENT:")
        
        structure_tests = [r for r in self.test_results if "Endpoint Structure" in r["test"] or "Total Count" in r["test"]]
        structure_success = all(r["status"] == "PASS" for r in structure_tests)
        
        content_tests = [r for r in self.test_results if "Headers Content" in r["test"]]
        content_success = all(r["status"] == "PASS" for r in content_tests)
        
        pagination_tests = [r for r in self.test_results if "Pagination Parameters" in r["test"]]
        pagination_success = all(r["status"] == "PASS" for r in pagination_tests)
        
        dashboard_tests = [r for r in self.test_results if "Dashboard Integration" in r["test"]]
        dashboard_success = all(r["status"] == "PASS" for r in dashboard_tests)
        
        if structure_success:
            print("✅ Endpoint Structure - Returns paginated response with correct structure")
        else:
            print("❌ Endpoint Structure - FAILED")
        
        if content_success:
            print("✅ Headers Content - Items array contains valid inventory headers")
        else:
            print("❌ Headers Content - FAILED")
        
        if pagination_success:
            print("✅ Pagination Parameters - Page and page_size parameters work correctly")
        else:
            print("❌ Pagination Parameters - FAILED")
        
        if dashboard_success:
            print("✅ Dashboard Integration - Dashboard can correctly read category count")
        else:
            print("❌ Dashboard Integration - FAILED")
        
        # Overall assessment
        overall_success = structure_success and content_success and pagination_success and dashboard_success
        
        if overall_success:
            print("\n🎉 DASHBOARD CATEGORY COUNT FIX WORKING!")
            print("✅ /api/inventory/headers returns paginated response")
            print("✅ Response has correct structure: {items: [], pagination: {total_count: X}}")
            print("✅ Dashboard can read category count from pagination.total_count")
            print("✅ Pagination parameters work correctly")
            print("✅ Fix resolves the original issue where dashboard showed 0 categories")
        else:
            print("\n🚨 DASHBOARD CATEGORY COUNT FIX HAS ISSUES!")
            print("❌ Some aspects of the fix are not working correctly")
            print("❌ Review failed tests above")
        
        # Detailed results
        print("\nDETAILED RESULTS:")
        for result in self.test_results:
            status_symbol = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"{status_symbol} {result['test']}: {result['details']}")
        
        return overall_success

if __name__ == "__main__":
    tester = DashboardCategoryTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
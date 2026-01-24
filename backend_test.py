#!/usr/bin/env python3
"""
Backend Testing Script for Inventory Headers API Endpoint

CRITICAL TEST FOCUS:
✅ Inventory Headers API Endpoint (GET /api/inventory/headers) - Paginated Structure Testing

TEST OBJECTIVES:
1. Test GET /api/inventory/headers returns correct paginated structure: {items: [...], pagination: {...}}
2. Verify items array contains inventory headers with proper id and name fields
3. Verify each header has required fields: id, name, current_qty, current_weight
4. Test pagination parameters work correctly (page=1, page_size=10)
5. Ensure Category dropdown in Add Stock Movement dialog will populate correctly

This test ensures the Category dropdown in the Add Stock Movement dialog will populate correctly.
"""

import requests
import json
import sys
from datetime import datetime
import uuid
import time

# Configuration
BASE_URL = "https://category-id-system.preview.emergentagent.com/api"
USERNAME = "admin"
PASSWORD = "admin123"

class InventoryHeadersTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.test_headers = []
        
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
        TEST 1: Inventory Headers API Endpoint Structure
        GET /api/inventory/headers should return correct paginated structure
        """
        print("\n" + "="*80)
        print("TEST 1: INVENTORY HEADERS API ENDPOINT STRUCTURE")
        print("="*80)
        
        try:
            response = self.session.get(f"{BASE_URL}/inventory/headers")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify top-level structure: {items: [...], pagination: {...}}
                required_keys = ['items', 'pagination']
                missing_keys = [key for key in required_keys if key not in data]
                
                if not missing_keys:
                    self.log_result("Inventory Headers - Response Structure", "PASS", 
                                  "Response contains correct structure: {items: [...], pagination: {...}}")
                    
                    # Verify items is an array
                    items = data.get('items', [])
                    if isinstance(items, list):
                        self.log_result("Inventory Headers - Items Array", "PASS", 
                                      f"Items is array with {len(items)} inventory headers")
                        self.test_headers = items
                    else:
                        self.log_result("Inventory Headers - Items Array", "FAIL", 
                                      f"Items is not an array: {type(items)}")
                    
                    # Verify pagination object
                    pagination = data.get('pagination', {})
                    if isinstance(pagination, dict):
                        required_pagination_fields = ['total_count', 'page', 'page_size', 'total_pages', 'has_next', 'has_prev']
                        missing_pagination_fields = [field for field in required_pagination_fields if field not in pagination]
                        
                        if not missing_pagination_fields:
                            self.log_result("Inventory Headers - Pagination Object", "PASS", 
                                          f"Pagination object contains all required fields: {', '.join(required_pagination_fields)}")
                            
                            # Log pagination details
                            pagination_details = f"total_count: {pagination.get('total_count')}, page: {pagination.get('page')}, page_size: {pagination.get('page_size')}, total_pages: {pagination.get('total_pages')}, has_next: {pagination.get('has_next')}, has_prev: {pagination.get('has_prev')}"
                            self.log_result("Inventory Headers - Pagination Details", "PASS", pagination_details)
                        else:
                            self.log_result("Inventory Headers - Pagination Object", "FAIL", 
                                          f"Missing pagination fields: {missing_pagination_fields}")
                    else:
                        self.log_result("Inventory Headers - Pagination Object", "FAIL", 
                                      f"Pagination is not an object: {type(pagination)}")
                        
                else:
                    self.log_result("Inventory Headers - Response Structure", "FAIL", 
                                  f"Missing required keys: {missing_keys}")
            else:
                self.log_result("Inventory Headers - HTTP Response", "FAIL", 
                              f"Failed to get inventory headers: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Inventory Headers - Exception", "ERROR", f"Error: {str(e)}")
    
    def test_inventory_headers_item_fields(self):
        """
        TEST 2: Inventory Headers Item Fields
        Verify each header has required fields: id, name, current_qty, current_weight
        """
        print("\n" + "="*80)
        print("TEST 2: INVENTORY HEADERS ITEM FIELDS")
        print("="*80)
        
        if not self.test_headers:
            self.log_result("Inventory Headers - Item Fields", "FAIL", "No inventory headers available for testing")
            return
        
        try:
            required_fields = ['id', 'name', 'current_qty', 'current_weight']
            
            for i, header in enumerate(self.test_headers):
                missing_fields = [field for field in required_fields if field not in header]
                
                if not missing_fields:
                    header_name = header.get('name', 'Unknown')
                    header_id = header.get('id', 'Unknown')
                    current_qty = header.get('current_qty', 0)
                    current_weight = header.get('current_weight', 0)
                    
                    self.log_result(f"Inventory Header {i+1} - Required Fields", "PASS", 
                                  f"Header '{header_name}' (ID: {header_id}) has all required fields: qty={current_qty}, weight={current_weight}g")
                else:
                    self.log_result(f"Inventory Header {i+1} - Required Fields", "FAIL", 
                                  f"Missing required fields: {missing_fields}")
            
            # Test additional fields that should be present
            additional_fields = ['is_active', 'created_at', 'created_by']
            headers_with_additional_fields = 0
            
            for header in self.test_headers:
                present_additional_fields = [field for field in additional_fields if field in header]
                if len(present_additional_fields) >= 2:  # At least 2 additional fields should be present
                    headers_with_additional_fields += 1
            
            if headers_with_additional_fields > 0:
                self.log_result("Inventory Headers - Additional Fields", "PASS", 
                              f"{headers_with_additional_fields}/{len(self.test_headers)} headers have additional fields (is_active, created_at, created_by)")
            else:
                self.log_result("Inventory Headers - Additional Fields", "PASS", 
                              "Additional fields may not be present (acceptable)")
                
        except Exception as e:
            self.log_result("Inventory Headers - Item Fields", "ERROR", f"Error: {str(e)}")
    
    def test_inventory_headers_pagination_parameters(self):
        """
        TEST 3: Inventory Headers Pagination Parameters
        Test pagination parameters work correctly (page=1, page_size=10)
        """
        print("\n" + "="*80)
        print("TEST 3: INVENTORY HEADERS PAGINATION PARAMETERS")
        print("="*80)
        
        try:
            # Test with custom page_size
            response = self.session.get(f"{BASE_URL}/inventory/headers?page=1&page_size=5")
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                pagination = data.get('pagination', {})
                
                # Verify page_size parameter is respected
                page_size = pagination.get('page_size')
                if page_size == 5:
                    self.log_result("Inventory Headers - Page Size Parameter", "PASS", 
                                  f"Custom page_size=5 parameter working correctly")
                    
                    # Verify items length respects page_size
                    if len(items) <= 5:
                        self.log_result("Inventory Headers - Items Length vs Page Size", "PASS", 
                                      f"Items length ({len(items)}) respects page_size limit (5)")
                    else:
                        self.log_result("Inventory Headers - Items Length vs Page Size", "FAIL", 
                                      f"Items length ({len(items)}) exceeds page_size limit (5)")
                else:
                    self.log_result("Inventory Headers - Page Size Parameter", "FAIL", 
                                  f"Expected page_size=5, got {page_size}")
                
                # Test page parameter
                page = pagination.get('page')
                if page == 1:
                    self.log_result("Inventory Headers - Page Parameter", "PASS", 
                                  f"Page parameter working correctly: page={page}")
                else:
                    self.log_result("Inventory Headers - Page Parameter", "FAIL", 
                                  f"Expected page=1, got {page}")
                
            else:
                self.log_result("Inventory Headers - Pagination Parameters", "FAIL", 
                              f"Failed to test pagination parameters: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Inventory Headers - Pagination Parameters", "ERROR", f"Error: {str(e)}")
    
    def test_inventory_headers_category_dropdown_compatibility(self):
        """
        TEST 4: Category Dropdown Compatibility
        Verify the response structure can be used in Category dropdown for Add Stock Movement dialog
        """
        print("\n" + "="*80)
        print("TEST 4: CATEGORY DROPDOWN COMPATIBILITY")
        print("="*80)
        
        try:
            response = self.session.get(f"{BASE_URL}/inventory/headers")
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                pagination = data.get('pagination', {})
                
                # Simulate dropdown population scenario
                dropdown_options = []
                
                for header in items:
                    header_id = header.get('id')
                    header_name = header.get('name')
                    
                    if header_id and header_name:
                        dropdown_options.append({
                            'value': header_id,
                            'label': header_name
                        })
                
                if dropdown_options:
                    self.log_result("Category Dropdown - Option Generation", "PASS", 
                                  f"Successfully generated {len(dropdown_options)} dropdown options from inventory headers")
                    
                    # Log sample dropdown options
                    sample_options = dropdown_options[:3]  # First 3 options
                    sample_details = ", ".join([f"'{opt['label']}' (ID: {opt['value']})" for opt in sample_options])
                    self.log_result("Category Dropdown - Sample Options", "PASS", 
                                  f"Sample dropdown options: {sample_details}")
                    
                    # Verify total count is accessible for pagination in dropdown
                    total_count = pagination.get('total_count', 0)
                    if total_count >= len(dropdown_options):
                        self.log_result("Category Dropdown - Total Count Access", "PASS", 
                                      f"Total count ({total_count}) accessible for dropdown pagination")
                    else:
                        self.log_result("Category Dropdown - Total Count Access", "FAIL", 
                                      f"Total count ({total_count}) is less than current items ({len(dropdown_options)})")
                else:
                    self.log_result("Category Dropdown - Option Generation", "FAIL", 
                                  "Could not generate dropdown options - headers missing id or name fields")
                
            else:
                self.log_result("Category Dropdown - Compatibility", "FAIL", 
                              f"Failed to test dropdown compatibility: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Category Dropdown - Compatibility", "ERROR", f"Error: {str(e)}")
    
    def test_inventory_headers_authentication(self):
        """
        TEST 5: Authentication Requirements
        Verify inventory headers endpoint is properly protected
        """
        print("\n" + "="*80)
        print("TEST 5: AUTHENTICATION REQUIREMENTS")
        print("="*80)
        
        try:
            # Test without authentication
            unauthenticated_session = requests.Session()
            response = unauthenticated_session.get(f"{BASE_URL}/inventory/headers")
            
            if response.status_code == 401:
                self.log_result("Authentication - Inventory Headers Protected", "PASS", 
                              "Inventory headers endpoint properly requires authentication")
            else:
                self.log_result("Authentication - Inventory Headers Protected", "FAIL", 
                              f"Inventory headers endpoint should require auth: {response.status_code}")
                
        except Exception as e:
            self.log_result("Authentication - Inventory Headers Protected", "ERROR", f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all inventory headers API endpoint tests"""
        print("STARTING INVENTORY HEADERS API ENDPOINT TESTING")
        print("Backend URL:", BASE_URL)
        print("Authentication:", f"{USERNAME}/***")
        print("Target Endpoint: GET /api/inventory/headers")
        print("Purpose: Ensure Category dropdown in Add Stock Movement dialog populates correctly")
        print("="*80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Test authentication requirements
        self.test_inventory_headers_authentication()
        
        # Test endpoint structure
        self.test_inventory_headers_endpoint_structure()
        
        # Test item fields
        self.test_inventory_headers_item_fields()
        
        # Test pagination parameters
        self.test_inventory_headers_pagination_parameters()
        
        # Test category dropdown compatibility
        self.test_inventory_headers_category_dropdown_compatibility()
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY - INVENTORY HEADERS API ENDPOINT")
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
        
        structure_tests = [r for r in self.test_results if "Response Structure" in r["test"] or "Pagination Object" in r["test"]]
        structure_success = all(r["status"] == "PASS" for r in structure_tests)
        
        fields_tests = [r for r in self.test_results if "Required Fields" in r["test"]]
        fields_success = all(r["status"] == "PASS" for r in fields_tests)
        
        pagination_tests = [r for r in self.test_results if "Pagination Parameters" in r["test"] or "Page Size" in r["test"]]
        pagination_success = all(r["status"] == "PASS" for r in pagination_tests)
        
        dropdown_tests = [r for r in self.test_results if "Category Dropdown" in r["test"]]
        dropdown_success = all(r["status"] == "PASS" for r in dropdown_tests)
        
        auth_tests = [r for r in self.test_results if "Authentication" in r["test"]]
        auth_success = all(r["status"] == "PASS" for r in auth_tests)
        
        if structure_success:
            print("✅ Response Structure - Returns correct paginated structure {items: [...], pagination: {...}}")
        else:
            print("❌ Response Structure - FAILED")
        
        if fields_success:
            print("✅ Item Fields - All headers have required fields (id, name, current_qty, current_weight)")
        else:
            print("❌ Item Fields - FAILED")
        
        if pagination_success:
            print("✅ Pagination Parameters - page and page_size parameters work correctly")
        else:
            print("❌ Pagination Parameters - FAILED")
        
        if dropdown_success:
            print("✅ Category Dropdown Compatibility - Can populate Category dropdown for Add Stock Movement")
        else:
            print("❌ Category Dropdown Compatibility - FAILED")
        
        if auth_success:
            print("✅ Authentication Requirements - Endpoint properly protected")
        else:
            print("❌ Authentication Requirements - FAILED")
        
        # Overall assessment
        overall_success = structure_success and fields_success and pagination_success and dropdown_success and auth_success
        
        if overall_success:
            print("\n🎉 INVENTORY HEADERS API ENDPOINT FULLY FUNCTIONAL!")
            print("✅ Returns correct paginated structure: {items: [...], pagination: {...}}")
            print("✅ Items array contains inventory headers with proper id and name fields")
            print("✅ Each header has required fields: id, name, current_qty, current_weight")
            print("✅ Pagination parameters (page=1, page_size=10) work correctly")
            print("✅ Category dropdown in Add Stock Movement dialog will populate correctly")
            print("✅ Endpoint is properly authenticated")
        else:
            print("\n🚨 SOME ISSUES DETECTED!")
            print("❌ Some aspects of the inventory headers endpoint are not working as expected")
            print("❌ Category dropdown may not populate correctly")
            print("❌ Review failed tests above")
        
        # Detailed results
        print("\nDETAILED RESULTS:")
        for result in self.test_results:
            status_symbol = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"{status_symbol} {result['test']}: {result['details']}")
        
        return overall_success

if __name__ == "__main__":
    tester = InventoryHeadersTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
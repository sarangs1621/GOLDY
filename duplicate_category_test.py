#!/usr/bin/env python3
"""
Backend Testing Script for Duplicate Category Name Prevention

CRITICAL TEST FOCUS:
✅ Duplicate Category Name Prevention in Inventory Headers API
- POST /api/inventory/headers (Create new category)
- PATCH /api/inventory/headers/{header_id} (Update existing category)

TEST OBJECTIVES:
1. Create duplicate category (exact match) - should fail with 400
2. Create duplicate category (case-insensitive) - should fail with 400  
3. Create duplicate with extra spaces - should fail with 400
4. Create unique category - should succeed
5. Update to duplicate name - should fail with 400
6. Update to same name (self-update) - should succeed
7. Create category after deleting one - should succeed

This test ensures proper duplicate prevention with case-insensitive matching and whitespace handling.
"""

import requests
import json
import sys
from datetime import datetime
import uuid
import time

# Configuration
BASE_URL = "https://decimal-precision.preview.emergentagent.com/api"
USERNAME = "admin"
PASSWORD = "admin123"

class DuplicateCategoryTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.csrf_token = None
        self.test_results = []
        self.test_categories = []
        self.existing_categories = []
        
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
        """Authenticate and get JWT token and CSRF token"""
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json={
                "username": USERNAME,
                "password": PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.csrf_token = data.get("csrf_token")
                
                # Set Authorization header
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                
                # Set CSRF token header for all future requests
                if self.csrf_token:
                    self.session.headers.update({"X-CSRF-Token": self.csrf_token})
                
                self.log_result("Authentication", "PASS", f"Successfully authenticated as {USERNAME} with CSRF token")
                return True
            else:
                self.log_result("Authentication", "FAIL", f"Failed to authenticate: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Authentication", "ERROR", f"Authentication error: {str(e)}")
            return False
    
    def get_existing_categories(self):
        """Get list of existing categories"""
        try:
            response = self.session.get(f"{BASE_URL}/inventory/headers")
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                self.existing_categories = items
                
                category_names = [item.get('name', 'Unknown') for item in items]
                self.log_result("Setup - Get Existing Categories", "PASS", 
                              f"Found {len(items)} existing categories: {', '.join(category_names[:5])}")
                return len(items) > 0
            else:
                self.log_result("Setup - Get Existing Categories", "FAIL", 
                              f"Failed to get categories: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Setup - Get Existing Categories", "ERROR", f"Error: {str(e)}")
            return False
    
    def setup_test_data(self):
        """Create initial test categories for testing"""
        try:
            # Create some initial categories for testing
            initial_categories = ["Gold Rings", "Gold Chains", "Gold Earrings"]
            
            for category_name in initial_categories:
                response = self.session.post(f"{BASE_URL}/inventory/headers", json={
                    "name": category_name
                })
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    self.log_result("Setup - Create Initial Category", "PASS", 
                                  f"Created initial category '{category_name}' with ID: {data.get('id')}")
                else:
                    # Category might already exist, which is fine
                    self.log_result("Setup - Create Initial Category", "PASS", 
                                  f"Category '{category_name}' may already exist (status: {response.status_code})")
            
            # Refresh existing categories list
            return self.get_existing_categories()
                
        except Exception as e:
            self.log_result("Setup - Create Initial Categories", "ERROR", f"Error: {str(e)}")
            return False
    
    def test_create_duplicate_exact_match(self):
        """
        TEST 1: Create duplicate category (exact match)
        Try to create a category with a name that already exists
        Expected: 400 error with message "Category '{name}' already exists"
        """
        print("\n" + "="*80)
        print("TEST 1: CREATE DUPLICATE CATEGORY (EXACT MATCH)")
        print("="*80)
        
        if not self.existing_categories:
            self.log_result("Create Duplicate - Exact Match", "FAIL", "No existing categories to test against")
            return
        
        try:
            # Use the first existing category name
            existing_name = self.existing_categories[0].get('name')
            
            response = self.session.post(f"{BASE_URL}/inventory/headers", json={
                "name": existing_name
            })
            
            if response.status_code == 400:
                response_data = response.json()
                error_detail = response_data.get('detail', '')
                
                if 'already exists' in error_detail.lower():
                    self.log_result("Create Duplicate - Exact Match", "PASS", 
                                  f"Correctly rejected duplicate '{existing_name}': {error_detail}")
                else:
                    self.log_result("Create Duplicate - Exact Match", "FAIL", 
                                  f"Wrong error message for duplicate '{existing_name}': {error_detail}")
            else:
                self.log_result("Create Duplicate - Exact Match", "FAIL", 
                              f"Expected 400 error, got {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Create Duplicate - Exact Match", "ERROR", f"Error: {str(e)}")
    
    def test_create_duplicate_case_insensitive(self):
        """
        TEST 2: Create duplicate category (case-insensitive)
        If category "Gold Rings" exists, try creating "gold rings" or "GOLD RINGS"
        Expected: 400 error with message indicating duplicate
        """
        print("\n" + "="*80)
        print("TEST 2: CREATE DUPLICATE CATEGORY (CASE-INSENSITIVE)")
        print("="*80)
        
        if not self.existing_categories:
            self.log_result("Create Duplicate - Case Insensitive", "FAIL", "No existing categories to test against")
            return
        
        try:
            # Use the first existing category name and change case
            existing_name = self.existing_categories[0].get('name')
            test_variations = [
                existing_name.lower(),
                existing_name.upper(),
                existing_name.title()
            ]
            
            for variation in test_variations:
                if variation != existing_name:  # Only test if it's actually different
                    response = self.session.post(f"{BASE_URL}/inventory/headers", json={
                        "name": variation
                    })
                    
                    if response.status_code == 400:
                        response_data = response.json()
                        error_detail = response_data.get('detail', '')
                        
                        if 'already exists' in error_detail.lower():
                            self.log_result("Create Duplicate - Case Insensitive", "PASS", 
                                          f"Correctly rejected case variation '{variation}' of '{existing_name}': {error_detail}")
                        else:
                            self.log_result("Create Duplicate - Case Insensitive", "FAIL", 
                                          f"Wrong error message for case variation '{variation}': {error_detail}")
                    else:
                        self.log_result("Create Duplicate - Case Insensitive", "FAIL", 
                                      f"Expected 400 error for '{variation}', got {response.status_code}: {response.text}")
                    break  # Test only one variation
                
        except Exception as e:
            self.log_result("Create Duplicate - Case Insensitive", "ERROR", f"Error: {str(e)}")
    
    def test_create_duplicate_with_spaces(self):
        """
        TEST 3: Create duplicate with extra spaces
        If category "Gold Rings" exists, try creating " Gold Rings " or "Gold  Rings"
        Expected: Should handle whitespace and detect duplicate (400 error)
        """
        print("\n" + "="*80)
        print("TEST 3: CREATE DUPLICATE CATEGORY (WITH EXTRA SPACES)")
        print("="*80)
        
        if not self.existing_categories:
            self.log_result("Create Duplicate - Extra Spaces", "FAIL", "No existing categories to test against")
            return
        
        try:
            # Use the first existing category name and add spaces
            existing_name = self.existing_categories[0].get('name')
            test_variations = [
                f" {existing_name} ",  # Leading and trailing spaces
                f"  {existing_name}  ",  # Multiple spaces
                existing_name.replace(" ", "  ") if " " in existing_name else f"{existing_name} "  # Double spaces or add space
            ]
            
            for variation in test_variations:
                if variation.strip() == existing_name:  # This should be detected as duplicate
                    response = self.session.post(f"{BASE_URL}/inventory/headers", json={
                        "name": variation
                    })
                    
                    if response.status_code == 400:
                        response_data = response.json()
                        error_detail = response_data.get('detail', '')
                        
                        if 'already exists' in error_detail.lower():
                            self.log_result("Create Duplicate - Extra Spaces", "PASS", 
                                          f"Correctly rejected space variation '{variation}' of '{existing_name}': {error_detail}")
                        else:
                            self.log_result("Create Duplicate - Extra Spaces", "FAIL", 
                                          f"Wrong error message for space variation '{variation}': {error_detail}")
                    else:
                        self.log_result("Create Duplicate - Extra Spaces", "FAIL", 
                                      f"Expected 400 error for '{variation}', got {response.status_code}: {response.text}")
                    break  # Test only one variation
                
        except Exception as e:
            self.log_result("Create Duplicate - Extra Spaces", "ERROR", f"Error: {str(e)}")
    
    def test_create_unique_category(self):
        """
        TEST 4: Create unique category
        Create a category with a completely new unique name like "Test Category 12345"
        Expected: 201/200 success
        """
        print("\n" + "="*80)
        print("TEST 4: CREATE UNIQUE CATEGORY")
        print("="*80)
        
        try:
            # Generate unique category name
            unique_name = f"Test Category {uuid.uuid4().hex[:8]}"
            
            response = self.session.post(f"{BASE_URL}/inventory/headers", json={
                "name": unique_name
            })
            
            if response.status_code in [200, 201]:
                response_data = response.json()
                created_id = response_data.get('id')
                created_name = response_data.get('name')
                
                if created_name == unique_name:
                    self.log_result("Create Unique Category", "PASS", 
                                  f"Successfully created unique category '{unique_name}' with ID: {created_id}")
                    
                    # Store for cleanup
                    self.test_categories.append({
                        'id': created_id,
                        'name': created_name
                    })
                else:
                    self.log_result("Create Unique Category", "FAIL", 
                                  f"Created category name mismatch: expected '{unique_name}', got '{created_name}'")
            else:
                self.log_result("Create Unique Category", "FAIL", 
                              f"Expected 200/201 success, got {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Create Unique Category", "ERROR", f"Error: {str(e)}")
    
    def test_update_to_duplicate_name(self):
        """
        TEST 5: Update to duplicate name
        Update an existing category to a name that another category already has
        Expected: 400 error
        """
        print("\n" + "="*80)
        print("TEST 5: UPDATE TO DUPLICATE NAME")
        print("="*80)
        
        if len(self.existing_categories) < 2:
            self.log_result("Update to Duplicate", "FAIL", "Need at least 2 existing categories to test update to duplicate")
            return
        
        try:
            # Use first category to update, second category's name as target
            category_to_update = self.existing_categories[0]
            target_name = self.existing_categories[1].get('name')
            update_id = category_to_update.get('id')
            
            response = self.session.patch(f"{BASE_URL}/inventory/headers/{update_id}", json={
                "name": target_name
            })
            
            if response.status_code == 400:
                response_data = response.json()
                error_detail = response_data.get('detail', '')
                
                if 'already exists' in error_detail.lower():
                    self.log_result("Update to Duplicate", "PASS", 
                                  f"Correctly rejected update to duplicate name '{target_name}': {error_detail}")
                else:
                    self.log_result("Update to Duplicate", "FAIL", 
                                  f"Wrong error message for duplicate update: {error_detail}")
            else:
                self.log_result("Update to Duplicate", "FAIL", 
                              f"Expected 400 error, got {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Update to Duplicate", "ERROR", f"Error: {str(e)}")
    
    def test_update_to_same_name(self):
        """
        TEST 6: Update to same name (self-update)
        Update a category keeping the same name (maybe just changing case)
        Expected: Should succeed (200 OK)
        """
        print("\n" + "="*80)
        print("TEST 6: UPDATE TO SAME NAME (SELF-UPDATE)")
        print("="*80)
        
        if not self.existing_categories:
            self.log_result("Update to Same Name", "FAIL", "No existing categories to test against")
            return
        
        try:
            # Use first existing category
            category = self.existing_categories[0]
            category_id = category.get('id')
            current_name = category.get('name')
            
            # Test updating to same name (case variation)
            same_name_variation = current_name.title() if current_name != current_name.title() else current_name.lower()
            
            response = self.session.patch(f"{BASE_URL}/inventory/headers/{category_id}", json={
                "name": same_name_variation
            })
            
            if response.status_code == 200:
                response_data = response.json()
                updated_name = response_data.get('name')
                
                self.log_result("Update to Same Name", "PASS", 
                              f"Successfully updated category to same name variation: '{current_name}' -> '{updated_name}'")
            else:
                self.log_result("Update to Same Name", "FAIL", 
                              f"Expected 200 success, got {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Update to Same Name", "ERROR", f"Error: {str(e)}")
    
    def test_create_after_delete(self):
        """
        TEST 7: Create category after deleting one
        If possible, delete a category, then try to create one with the same name
        Expected: Should succeed (deleted categories don't count)
        """
        print("\n" + "="*80)
        print("TEST 7: CREATE CATEGORY AFTER DELETING ONE")
        print("="*80)
        
        if not self.test_categories:
            self.log_result("Create After Delete", "FAIL", "No test categories available for deletion test")
            return
        
        try:
            # Use the category we created in test 4
            test_category = self.test_categories[0]
            category_id = test_category.get('id')
            category_name = test_category.get('name')
            
            # First, delete the category
            delete_response = self.session.delete(f"{BASE_URL}/inventory/headers/{category_id}")
            
            if delete_response.status_code == 200:
                self.log_result("Create After Delete - Deletion", "PASS", 
                              f"Successfully deleted category '{category_name}'")
                
                # Wait a moment for deletion to process
                time.sleep(1)
                
                # Now try to create a category with the same name
                create_response = self.session.post(f"{BASE_URL}/inventory/headers", json={
                    "name": category_name
                })
                
                if create_response.status_code in [200, 201]:
                    create_data = create_response.json()
                    new_id = create_data.get('id')
                    new_name = create_data.get('name')
                    
                    self.log_result("Create After Delete - Recreation", "PASS", 
                                  f"Successfully recreated category '{new_name}' after deletion (new ID: {new_id})")
                    
                    # Update test_categories for cleanup
                    self.test_categories[0] = {
                        'id': new_id,
                        'name': new_name
                    }
                else:
                    self.log_result("Create After Delete - Recreation", "FAIL", 
                                  f"Failed to recreate deleted category: {create_response.status_code} - {create_response.text}")
            else:
                self.log_result("Create After Delete - Deletion", "FAIL", 
                              f"Failed to delete category: {delete_response.status_code} - {delete_response.text}")
                
        except Exception as e:
            self.log_result("Create After Delete", "ERROR", f"Error: {str(e)}")
    
    def cleanup_test_categories(self):
        """Clean up test categories created during testing"""
        print("\n" + "="*80)
        print("CLEANUP: REMOVING TEST CATEGORIES")
        print("="*80)
        
        for category in self.test_categories:
            try:
                category_id = category.get('id')
                category_name = category.get('name')
                
                response = self.session.delete(f"{BASE_URL}/inventory/headers/{category_id}")
                
                if response.status_code == 200:
                    self.log_result("Cleanup", "PASS", f"Deleted test category '{category_name}'")
                else:
                    self.log_result("Cleanup", "FAIL", f"Failed to delete '{category_name}': {response.status_code}")
                    
            except Exception as e:
                self.log_result("Cleanup", "ERROR", f"Error cleaning up category: {str(e)}")
    
    def run_all_tests(self):
        """Run all duplicate category prevention tests"""
        print("STARTING DUPLICATE CATEGORY NAME PREVENTION TESTING")
        print("Backend URL:", BASE_URL)
        print("Authentication:", f"{USERNAME}/***")
        print("Target Endpoints: POST /api/inventory/headers, PATCH /api/inventory/headers/{id}")
        print("Purpose: Test duplicate category name prevention with case-insensitive matching")
        print("="*80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Get existing categories for testing
        if not self.get_existing_categories():
            print("⚠️ No existing categories found. Creating initial test data...")
            if not self.setup_test_data():
                print("❌ Failed to setup test data. Cannot proceed with tests.")
                return False
        
        # Run all tests
        self.test_create_duplicate_exact_match()
        self.test_create_duplicate_case_insensitive()
        self.test_create_duplicate_with_spaces()
        self.test_create_unique_category()
        self.test_update_to_duplicate_name()
        self.test_update_to_same_name()
        self.test_create_after_delete()
        
        # Cleanup
        self.cleanup_test_categories()
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY - DUPLICATE CATEGORY NAME PREVENTION")
        print("="*80)
        
        total_tests = len([r for r in self.test_results if not r["test"].startswith("Setup") and not r["test"].startswith("Cleanup")])
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS" and not r["test"].startswith("Setup") and not r["test"].startswith("Cleanup")])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL" and not r["test"].startswith("Setup") and not r["test"].startswith("Cleanup")])
        error_tests = len([r for r in self.test_results if r["status"] == "ERROR" and not r["test"].startswith("Setup") and not r["test"].startswith("Cleanup")])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️ Errors: {error_tests}")
        
        # Success criteria assessment
        print("\nSUCCESS CRITERIA ASSESSMENT:")
        
        duplicate_prevention_tests = [r for r in self.test_results if "Duplicate" in r["test"] and r["status"] == "PASS"]
        unique_creation_tests = [r for r in self.test_results if "Unique Category" in r["test"] and r["status"] == "PASS"]
        update_tests = [r for r in self.test_results if "Update" in r["test"] and r["status"] == "PASS"]
        delete_recreation_tests = [r for r in self.test_results if "Create After Delete" in r["test"] and r["status"] == "PASS"]
        
        if len(duplicate_prevention_tests) >= 3:
            print("✅ Duplicate Prevention - Correctly rejects duplicate category names (exact, case-insensitive, spaces)")
        else:
            print("❌ Duplicate Prevention - FAILED")
        
        if len(unique_creation_tests) >= 1:
            print("✅ Unique Creation - Successfully creates categories with unique names")
        else:
            print("❌ Unique Creation - FAILED")
        
        if len(update_tests) >= 1:
            print("✅ Update Validation - Properly handles category name updates")
        else:
            print("❌ Update Validation - FAILED")
        
        if len(delete_recreation_tests) >= 1:
            print("✅ Delete/Recreate - Allows recreation of deleted category names")
        else:
            print("❌ Delete/Recreate - FAILED")
        
        # Overall assessment
        overall_success = (len(duplicate_prevention_tests) >= 3 and 
                          len(unique_creation_tests) >= 1 and 
                          len(update_tests) >= 1 and
                          failed_tests == 0)
        
        if overall_success:
            print("\n🎉 DUPLICATE CATEGORY NAME PREVENTION FULLY FUNCTIONAL!")
            print("✅ Correctly prevents duplicate category names (case-insensitive)")
            print("✅ Handles whitespace properly in category names")
            print("✅ Allows unique category creation")
            print("✅ Validates category name updates properly")
            print("✅ Allows recreation after deletion")
        else:
            print("\n🚨 SOME ISSUES DETECTED!")
            print("❌ Duplicate category name prevention may not be working correctly")
            print("❌ Review failed tests above")
        
        # Detailed results
        print("\nDETAILED RESULTS:")
        for result in self.test_results:
            if not result["test"].startswith("Setup") and not result["test"].startswith("Cleanup"):
                status_symbol = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
                print(f"{status_symbol} {result['test']}: {result['details']}")
        
        return overall_success

if __name__ == "__main__":
    tester = DuplicateCategoryTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
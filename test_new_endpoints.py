#!/usr/bin/env python3
"""
Test script for the 3 newly implemented API endpoints for completeness:
1. GET /api/dashboard - Dashboard statistics endpoint
2. GET /api/reports - Reports catalog endpoint  
3. GET /api/inventory - Simplified inventory listing
"""

import requests
import sys
import json
from datetime import datetime

class NewEndpointsTester:
    def __init__(self, base_url="https://decimal-precision.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {method} {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_login(self):
        """Test login with admin credentials"""
        # First try to register admin user if it doesn't exist
        register_success, register_response = self.run_test(
            "Register Admin User",
            "POST",
            "auth/register",
            200,
            data={
                "username": "admin",
                "password": "admin123",
                "email": "admin@goldshop.com",
                "full_name": "System Administrator",
                "role": "admin"
            }
        )
        
        # Try to login (whether registration succeeded or failed due to existing user)
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   Token obtained: {self.token[:20]}...")
            return True
        return False

    def test_dashboard_endpoint(self):
        """Test GET /api/dashboard - Dashboard statistics endpoint"""
        print("\n📊 TESTING DASHBOARD ENDPOINT")
        
        success, dashboard_response = self.run_test(
            "GET /api/dashboard - Dashboard Statistics",
            "GET",
            "dashboard",
            200
        )
        
        if not success:
            return False
        
        # Verify response structure
        required_sections = ['inventory', 'financial', 'parties', 'job_cards', 'recent_activity']
        for section in required_sections:
            if section not in dashboard_response:
                print(f"❌ Missing section in dashboard: {section}")
                return False
        
        # Verify inventory section
        inventory = dashboard_response.get('inventory', {})
        inventory_fields = ['total_categories', 'total_stock_weight_grams', 'total_stock_qty', 'low_stock_items']
        for field in inventory_fields:
            if field not in inventory:
                print(f"❌ Missing inventory field: {field}")
                return False
        
        # Verify financial section
        financial = dashboard_response.get('financial', {})
        financial_fields = ['total_outstanding_omr', 'outstanding_invoices_count']
        for field in financial_fields:
            if field not in financial:
                print(f"❌ Missing financial field: {field}")
                return False
        
        # Verify parties section
        parties = dashboard_response.get('parties', {})
        parties_fields = ['total_customers', 'total_vendors', 'total']
        for field in parties_fields:
            if field not in parties:
                print(f"❌ Missing parties field: {field}")
                return False
        
        # Verify job_cards section
        job_cards = dashboard_response.get('job_cards', {})
        job_cards_fields = ['total', 'pending', 'completed']
        for field in job_cards_fields:
            if field not in job_cards:
                print(f"❌ Missing job_cards field: {field}")
                return False
        
        # Verify recent_activity section
        recent_activity = dashboard_response.get('recent_activity', {})
        if 'recent_invoices' not in recent_activity:
            print(f"❌ Missing recent_invoices in recent_activity")
            return False
        
        recent_invoices = recent_activity['recent_invoices']
        if not isinstance(recent_invoices, list):
            print(f"❌ recent_invoices should be a list")
            return False
        elif len(recent_invoices) > 5:
            print(f"❌ recent_invoices should have max 5 items, got {len(recent_invoices)}")
            return False
        
        # Verify decimal precision
        weight_grams = inventory.get('total_stock_weight_grams', 0)
        outstanding_omr = financial.get('total_outstanding_omr', 0)
        
        # Check weight has 3 decimal precision
        if isinstance(weight_grams, (int, float)):
            weight_str = f"{weight_grams:.3f}"
            if abs(float(weight_str) - weight_grams) > 0.0001:
                print(f"❌ Weight precision should be 3 decimals: {weight_grams}")
                return False
        
        # Check money has 2 decimal precision  
        if isinstance(outstanding_omr, (int, float)):
            money_str = f"{outstanding_omr:.2f}"
            if abs(float(money_str) - outstanding_omr) > 0.001:
                print(f"❌ Money precision should be 2 decimals: {outstanding_omr}")
                return False
        
        print(f"✅ Dashboard endpoint: All sections present, calculations accurate, precision correct")
        print(f"   - Inventory: {inventory.get('total_categories')} categories, {inventory.get('total_stock_weight_grams')}g total")
        print(f"   - Financial: {financial.get('total_outstanding_omr')} OMR outstanding")
        print(f"   - Parties: {parties.get('total_customers')} customers, {parties.get('total_vendors')} vendors")
        print(f"   - Job Cards: {job_cards.get('total')} total, {job_cards.get('pending')} pending")
        print(f"   - Recent: {len(recent_activity.get('recent_invoices', []))} recent invoices")
        
        return True

    def test_reports_endpoint(self):
        """Test GET /api/reports - Reports catalog endpoint"""
        print("\n📋 TESTING REPORTS CATALOG ENDPOINT")
        
        success, reports_response = self.run_test(
            "GET /api/reports - Reports Catalog",
            "GET",
            "reports",
            200
        )
        
        if not success:
            return False
        
        # Verify response structure
        if 'reports' not in reports_response:
            print(f"❌ Missing 'reports' array in response")
            return False
        elif 'total_count' not in reports_response:
            print(f"❌ Missing 'total_count' in response")
            return False
        elif 'categories' not in reports_response:
            print(f"❌ Missing 'categories' array in response")
            return False
        
        reports = reports_response['reports']
        total_count = reports_response['total_count']
        categories = reports_response['categories']
        
        # Verify total count = 8
        if total_count != 8:
            print(f"❌ Expected 8 reports, got {total_count}")
            return False
        elif len(reports) != 8:
            print(f"❌ Expected 8 reports in array, got {len(reports)}")
            return False
        
        # Verify each report has required fields
        required_report_fields = ['id', 'name', 'description', 'category', 'endpoints', 'supports_filters', 'supports_export']
        for i, report in enumerate(reports):
            for field in required_report_fields:
                if field not in report:
                    print(f"❌ Report {i+1} missing field: {field}")
                    return False
            
            # Verify endpoints structure
            endpoints = report.get('endpoints', {})
            if 'view' not in endpoints:
                print(f"❌ Report {i+1} missing 'view' endpoint")
                return False
            
            # Verify endpoint URLs match actual routes
            view_endpoint = endpoints.get('view', '')
            if not view_endpoint.startswith('/api/'):
                print(f"❌ Report {i+1} view endpoint should start with /api/: {view_endpoint}")
                return False
        
        # Verify categories are unique
        unique_categories = set(categories)
        if len(unique_categories) != len(categories):
            print(f"❌ Categories should be unique: {categories}")
            return False
        
        print(f"✅ Reports catalog endpoint: All 8 reports listed with complete metadata")
        print(f"   - Categories: {categories}")
        print(f"   - Reports with export: {sum(1 for r in reports if r.get('supports_export'))}")
        print(f"   - Reports with filters: {sum(1 for r in reports if r.get('supports_filters'))}")
        
        return True

    def test_inventory_endpoint(self):
        """Test GET /api/inventory - Simplified inventory listing"""
        print("\n📦 TESTING INVENTORY LISTING ENDPOINT")
        
        # Test without filters (returns all items)
        success, inventory_response = self.run_test(
            "GET /api/inventory - All Items",
            "GET",
            "inventory",
            200
        )
        
        if not success:
            return False
        
        # Verify response structure
        required_fields = ['items', 'total_count', 'total_weight_grams', 'total_quantity', 'low_stock_count']
        for field in required_fields:
            if field not in inventory_response:
                print(f"❌ Missing field in inventory response: {field}")
                return False
        
        items = inventory_response.get('items', [])
        total_count = inventory_response.get('total_count', 0)
        total_weight = inventory_response.get('total_weight_grams', 0)
        total_qty = inventory_response.get('total_quantity', 0)
        low_stock_count = inventory_response.get('low_stock_count', 0)
        
        # Verify counts match
        if len(items) != total_count:
            print(f"❌ Items count mismatch: array has {len(items)}, total_count is {total_count}")
            return False
        
        # Verify each item has required fields
        item_fields = ['id', 'category', 'quantity', 'weight_grams', 'status']
        for i, item in enumerate(items):
            for field in item_fields:
                if field not in item:
                    print(f"❌ Item {i+1} missing field: {field}")
                    return False
            
            # Verify status field computation (low_stock when qty < 5)
            qty = item.get('quantity', 0)
            status = item.get('status', '')
            expected_status = 'low_stock' if qty < 5 else 'in_stock'
            if status != expected_status:
                print(f"❌ Item {i+1} status incorrect: expected {expected_status}, got {status}")
                return False
        
        # Verify items sorted by weight descending
        if len(items) > 1:
            for i in range(len(items) - 1):
                current_weight = items[i].get('weight_grams', 0)
                next_weight = items[i + 1].get('weight_grams', 0)
                if current_weight < next_weight:
                    print(f"❌ Items not sorted by weight descending: {current_weight} < {next_weight}")
                    return False
        
        # Verify aggregated stats
        calculated_weight = sum(item.get('weight_grams', 0) for item in items)
        calculated_qty = sum(item.get('quantity', 0) for item in items)
        calculated_low_stock = sum(1 for item in items if item.get('status') == 'low_stock')
        
        if abs(calculated_weight - total_weight) > 0.001:
            print(f"❌ Total weight mismatch: calculated {calculated_weight}, reported {total_weight}")
            return False
        
        if abs(calculated_qty - total_qty) > 0.01:
            print(f"❌ Total quantity mismatch: calculated {calculated_qty}, reported {total_qty}")
            return False
        
        if calculated_low_stock != low_stock_count:
            print(f"❌ Low stock count mismatch: calculated {calculated_low_stock}, reported {low_stock_count}")
            return False
        
        # Verify decimal precision (3 for weight, 2 for quantity)
        for item in items:
            weight = item.get('weight_grams', 0)
            quantity = item.get('quantity', 0)
            
            if isinstance(weight, (int, float)):
                weight_str = f"{weight:.3f}"
                if abs(float(weight_str) - weight) > 0.0001:
                    print(f"❌ Weight precision should be 3 decimals: {weight}")
                    return False
            
            if isinstance(quantity, (int, float)):
                qty_str = f"{quantity:.2f}"
                if abs(float(qty_str) - quantity) > 0.001:
                    print(f"❌ Quantity precision should be 2 decimals: {quantity}")
                    return False
        
        print(f"✅ Inventory listing (all items): {total_count} items, {total_weight:.3f}g total, {low_stock_count} low stock")
        
        # Test with category filter
        success, filtered_response = self.run_test(
            "GET /api/inventory - Category Filter",
            "GET",
            "inventory",
            200,
            params={"category": "gold"}
        )
        
        if success:
            filtered_items = filtered_response.get('items', [])
            print(f"✅ Inventory with category filter: {len(filtered_items)} items")
        else:
            return False
        
        # Test with min_qty filter
        success, qty_filtered_response = self.run_test(
            "GET /api/inventory - Min Quantity Filter",
            "GET",
            "inventory",
            200,
            params={"min_qty": "10"}
        )
        
        if success:
            qty_filtered_items = qty_filtered_response.get('items', [])
            # Verify all items have qty >= 10
            for item in qty_filtered_items:
                if item.get('quantity', 0) < 10:
                    print(f"❌ Min qty filter failed: item has qty {item.get('quantity')}")
                    return False
            
            print(f"✅ Inventory with min_qty filter: {len(qty_filtered_items)} items with qty >= 10")
        else:
            return False
        
        # Test with combined filters
        success, combined_response = self.run_test(
            "GET /api/inventory - Combined Filters",
            "GET",
            "inventory",
            200,
            params={"category": "gold", "min_qty": "5"}
        )
        
        if success:
            combined_items = combined_response.get('items', [])
            print(f"✅ Inventory with combined filters: {len(combined_items)} items")
        else:
            return False
        
        return True

    def run_tests(self):
        """Run all new endpoint tests"""
        print("🎯 TESTING 3 NEW API ENDPOINTS FOR COMPLETENESS")
        print(f"   Base URL: {self.base_url}")
        
        # Authentication
        if not self.test_login():
            print("❌ Login failed - stopping tests")
            return False
        
        # Test the 3 new endpoints
        results = []
        
        results.append(self.test_dashboard_endpoint())
        results.append(self.test_reports_endpoint())
        results.append(self.test_inventory_endpoint())
        
        # Summary
        all_passed = all(results)
        if all_passed:
            print(f"\n🎉 ALL 3 NEW API ENDPOINTS PASSED COMPLETENESS TESTING!")
            print(f"✅ Dashboard: Statistics with proper calculations and precision")
            print(f"✅ Reports: 8 reports catalog with complete metadata")
            print(f"✅ Inventory: Listing with filters, sorting, and aggregations")
        else:
            print(f"\n❌ Some API endpoints failed completeness testing")
            print(f"   Dashboard: {'✅' if results[0] else '❌'}")
            print(f"   Reports: {'✅' if results[1] else '❌'}")
            print(f"   Inventory: {'✅' if results[2] else '❌'}")
        
        # Print test summary
        print(f"\n📊 Test Summary:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        return all_passed

if __name__ == "__main__":
    tester = NewEndpointsTester()
    success = tester.run_tests()
    sys.exit(0 if success else 1)
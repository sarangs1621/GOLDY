#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Pagination Endpoints
Testing all 7 pagination endpoints that were previously returning 520 errors
"""

import requests
import json
import sys
from datetime import datetime, timezone

# Backend URL from environment
BACKEND_URL = "https://map-function-fix-1.preview.emergentagent.com/api"

# Test credentials
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"

class PaginationTester:
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_results = []
        
    def authenticate(self):
        """Authenticate and get JWT token"""
        print("🔐 Authenticating...")
        
        login_data = {
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        }
        
        try:
            response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
                print(f"✅ Authentication successful - User: {data['user']['full_name']}")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def test_pagination_endpoint(self, endpoint_name, url, test_params=None):
        """Test a single pagination endpoint with comprehensive checks"""
        print(f"\n📊 Testing {endpoint_name}")
        print(f"URL: {url}")
        
        if test_params is None:
            test_params = [
                {"page": 1, "per_page": 50},
                {"page": 1, "per_page": 25},
                {"page": 1, "per_page": 100},
                {"page": 2, "per_page": 50}
            ]
        
        endpoint_results = {
            "endpoint": endpoint_name,
            "url": url,
            "tests": [],
            "overall_status": "PASS"
        }
        
        for params in test_params:
            test_result = self._test_single_request(endpoint_name, url, params)
            endpoint_results["tests"].append(test_result)
            
            if test_result["status"] != "PASS":
                endpoint_results["overall_status"] = "FAIL"
        
        self.test_results.append(endpoint_results)
        return endpoint_results
    
    def _test_single_request(self, endpoint_name, url, params):
        """Test a single request with specific parameters"""
        print(f"  🔍 Testing with params: {params}")
        
        test_result = {
            "params": params,
            "status": "FAIL",
            "status_code": None,
            "response_structure": {},
            "pagination_metadata": {},
            "errors": []
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            test_result["status_code"] = response.status_code
            
            # Check status code
            if response.status_code != 200:
                test_result["errors"].append(f"Expected 200, got {response.status_code}")
                print(f"    ❌ Status Code: {response.status_code}")
                if response.status_code == 520:
                    print(f"    🚨 CRITICAL: Still getting 520 Internal Server Error!")
                return test_result
            
            # Parse JSON response
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                test_result["errors"].append(f"Invalid JSON response: {str(e)}")
                print(f"    ❌ Invalid JSON response")
                return test_result
            
            # Check response structure
            if not isinstance(data, dict):
                test_result["errors"].append("Response is not a dictionary")
                print(f"    ❌ Response is not a dictionary")
                return test_result
            
            # Check required top-level keys
            required_keys = ["items", "pagination"]
            missing_keys = [key for key in required_keys if key not in data]
            if missing_keys:
                test_result["errors"].append(f"Missing required keys: {missing_keys}")
                print(f"    ❌ Missing keys: {missing_keys}")
                return test_result
            
            # Check items array
            items = data.get("items", [])
            if not isinstance(items, list):
                test_result["errors"].append("'items' is not a list")
                print(f"    ❌ 'items' is not a list")
                return test_result
            
            test_result["response_structure"]["items_count"] = len(items)
            test_result["response_structure"]["items_type"] = "list"
            
            # Check pagination metadata
            pagination = data.get("pagination", {})
            if not isinstance(pagination, dict):
                test_result["errors"].append("'pagination' is not a dictionary")
                print(f"    ❌ 'pagination' is not a dictionary")
                return test_result
            
            # Check required pagination fields
            required_pagination_fields = [
                "total_count", "page", "per_page", "total_pages", "has_next", "has_prev"
            ]
            missing_pagination_fields = [field for field in required_pagination_fields if field not in pagination]
            if missing_pagination_fields:
                test_result["errors"].append(f"Missing pagination fields: {missing_pagination_fields}")
                print(f"    ❌ Missing pagination fields: {missing_pagination_fields}")
                return test_result
            
            # Validate pagination values
            total_count = pagination.get("total_count", 0)
            page = pagination.get("page", 0)
            per_page = pagination.get("per_page", 0)
            total_pages = pagination.get("total_pages", 0)
            has_next = pagination.get("has_next", False)
            has_prev = pagination.get("has_prev", False)
            
            test_result["pagination_metadata"] = {
                "total_count": total_count,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev
            }
            
            # Validate pagination calculations
            expected_total_pages = (total_count + per_page - 1) // per_page if per_page > 0 else 0
            if total_pages != expected_total_pages:
                test_result["errors"].append(f"Incorrect total_pages calculation: expected {expected_total_pages}, got {total_pages}")
            
            # Validate has_next and has_prev
            expected_has_next = page < total_pages
            expected_has_prev = page > 1
            
            if has_next != expected_has_next:
                test_result["errors"].append(f"Incorrect has_next: expected {expected_has_next}, got {has_next}")
            
            if has_prev != expected_has_prev:
                test_result["errors"].append(f"Incorrect has_prev: expected {expected_has_prev}, got {has_prev}")
            
            # Validate items count for current page
            expected_items_count = min(per_page, max(0, total_count - (page - 1) * per_page))
            if len(items) != expected_items_count and total_count > 0:
                # Allow for empty results when no data exists
                if not (total_count == 0 and len(items) == 0):
                    test_result["errors"].append(f"Incorrect items count: expected {expected_items_count}, got {len(items)}")
            
            # If no errors, mark as PASS
            if not test_result["errors"]:
                test_result["status"] = "PASS"
                print(f"    ✅ PASS - Items: {len(items)}, Total: {total_count}, Page: {page}/{total_pages}")
            else:
                print(f"    ❌ FAIL - Errors: {test_result['errors']}")
            
        except requests.exceptions.RequestException as e:
            test_result["errors"].append(f"Request error: {str(e)}")
            print(f"    ❌ Request error: {str(e)}")
        except Exception as e:
            test_result["errors"].append(f"Unexpected error: {str(e)}")
            print(f"    ❌ Unexpected error: {str(e)}")
        
        return test_result
    
    def create_test_data(self):
        """Create minimal test data if needed"""
        print("\n📝 Creating test data if needed...")
        
        # Create a test party for data population
        party_data = {
            "name": "Pagination Test Party",
            "phone": "99999999",
            "address": "Test Address",
            "party_type": "customer",
            "notes": "Created for pagination testing"
        }
        
        try:
            response = requests.post(f"{BACKEND_URL}/parties", json=party_data, headers=self.headers)
            if response.status_code == 200:
                party = response.json()
                print(f"✅ Created test party: {party['name']} (ID: {party['id']})")
                return party["id"]
            else:
                print(f"⚠️ Could not create test party: {response.status_code}")
                return None
        except Exception as e:
            print(f"⚠️ Error creating test data: {str(e)}")
            return None
    
    def run_all_pagination_tests(self):
        """Run tests for all 7 pagination endpoints"""
        print("🚀 Starting Comprehensive Pagination Endpoint Testing")
        print("=" * 80)
        
        if not self.authenticate():
            return False
        
        # Create test data
        test_party_id = self.create_test_data()
        
        # Define all 7 pagination endpoints to test
        endpoints = [
            {
                "name": "Parties",
                "url": f"{BACKEND_URL}/parties",
                "priority": "previously_fixed"
            },
            {
                "name": "Gold Ledger", 
                "url": f"{BACKEND_URL}/gold-ledger",
                "priority": "previously_fixed"
            },
            {
                "name": "Purchases",
                "url": f"{BACKEND_URL}/purchases", 
                "priority": "previously_fixed"
            },
            {
                "name": "Job Cards",
                "url": f"{BACKEND_URL}/jobcards",
                "priority": "newly_fixed"
            },
            {
                "name": "Invoices",
                "url": f"{BACKEND_URL}/invoices",
                "priority": "newly_fixed"
            },
            {
                "name": "Transactions",
                "url": f"{BACKEND_URL}/transactions",
                "priority": "newly_fixed"
            },
            {
                "name": "Audit Logs",
                "url": f"{BACKEND_URL}/audit-logs",
                "priority": "newly_fixed"
            }
        ]
        
        print(f"\n📋 Testing {len(endpoints)} pagination endpoints:")
        for i, endpoint in enumerate(endpoints, 1):
            print(f"  {i}. {endpoint['name']} ({endpoint['priority']})")
        
        # Test each endpoint
        all_passed = True
        
        # Test newly fixed endpoints first (priority)
        newly_fixed = [ep for ep in endpoints if ep["priority"] == "newly_fixed"]
        previously_fixed = [ep for ep in endpoints if ep["priority"] == "previously_fixed"]
        
        print(f"\n🎯 PRIORITY: Testing 4 newly fixed endpoints first...")
        for endpoint in newly_fixed:
            result = self.test_pagination_endpoint(endpoint["name"], endpoint["url"])
            if result["overall_status"] != "PASS":
                all_passed = False
        
        print(f"\n🔄 VERIFICATION: Testing 3 previously fixed endpoints...")
        for endpoint in previously_fixed:
            result = self.test_pagination_endpoint(endpoint["name"], endpoint["url"])
            if result["overall_status"] != "PASS":
                all_passed = False
        
        # Print comprehensive summary
        self.print_comprehensive_summary()
        
        return all_passed
    
    def print_comprehensive_summary(self):
        """Print detailed test results summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE PAGINATION TESTING RESULTS")
        print("=" * 80)
        
        total_endpoints = len(self.test_results)
        passed_endpoints = len([r for r in self.test_results if r["overall_status"] == "PASS"])
        failed_endpoints = total_endpoints - passed_endpoints
        
        print(f"\n📈 OVERALL SUMMARY:")
        print(f"  Total Endpoints Tested: {total_endpoints}")
        print(f"  ✅ Passed: {passed_endpoints}")
        print(f"  ❌ Failed: {failed_endpoints}")
        print(f"  Success Rate: {(passed_endpoints/total_endpoints)*100:.1f}%")
        
        # Detailed results by endpoint
        print(f"\n📋 DETAILED RESULTS:")
        
        for result in self.test_results:
            status_icon = "✅" if result["overall_status"] == "PASS" else "❌"
            print(f"\n{status_icon} {result['endpoint']}")
            
            # Count test cases
            total_tests = len(result["tests"])
            passed_tests = len([t for t in result["tests"] if t["status"] == "PASS"])
            
            print(f"    Tests: {passed_tests}/{total_tests} passed")
            
            # Show failed test details
            failed_tests = [t for t in result["tests"] if t["status"] == "FAIL"]
            if failed_tests:
                print(f"    ❌ Failed Tests:")
                for test in failed_tests:
                    print(f"      - Params: {test['params']}")
                    print(f"        Status Code: {test['status_code']}")
                    if test["errors"]:
                        print(f"        Errors: {test['errors']}")
            else:
                # Show sample successful test
                if result["tests"]:
                    sample_test = result["tests"][0]
                    if "pagination_metadata" in sample_test:
                        meta = sample_test["pagination_metadata"]
                        print(f"    📊 Sample Data: {meta.get('total_count', 0)} total items, {meta.get('total_pages', 0)} pages")
        
        # Critical issues summary
        critical_issues = []
        for result in self.test_results:
            if result["overall_status"] == "FAIL":
                for test in result["tests"]:
                    if test["status_code"] == 520:
                        critical_issues.append(f"{result['endpoint']}: Still returning 520 Internal Server Error")
                    elif test["status_code"] != 200:
                        critical_issues.append(f"{result['endpoint']}: HTTP {test['status_code']}")
        
        if critical_issues:
            print(f"\n🚨 CRITICAL ISSUES:")
            for issue in critical_issues:
                print(f"  - {issue}")
        
        # Success summary
        working_endpoints = [r["endpoint"] for r in self.test_results if r["overall_status"] == "PASS"]
        if working_endpoints:
            print(f"\n✅ WORKING ENDPOINTS:")
            for endpoint in working_endpoints:
                print(f"  - {endpoint}")
        
        print("\n" + "=" * 80)

def main():
    """Main test execution"""
    tester = PaginationTester()
    
    print("🧪 PAGINATION ENDPOINTS COMPREHENSIVE TESTING")
    print("Testing all 7 pagination endpoints for 520 error fixes")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    
    success = tester.run_all_pagination_tests()
    
    if success:
        print("\n🎉 ALL PAGINATION ENDPOINTS WORKING CORRECTLY!")
        sys.exit(0)
    else:
        print("\n⚠️ SOME PAGINATION ENDPOINTS HAVE ISSUES")
        sys.exit(1)

if __name__ == "__main__":
    main()
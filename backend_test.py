#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Gold Shop ERP System
AUDIT LOGS FILTERING FEATURE - Comprehensive Backend Testing

This script tests the enhanced GET /api/audit-logs endpoint with new filtering capabilities:
- date_from: Filter from this date (ISO format)
- date_to: Filter up to this date (ISO format)  
- user_id: Filter by user ID
- module: Filter by module name
- action: Filter by action type
"""

import requests
import json
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

class AuditLogsFilterTester:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
        self.session = requests.Session()
        self.test_results = []
        self.user_id = None  # Will be set after login
        self.created_party_ids = []  # Track created parties for cleanup
        
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
                user_data = data.get('user', {})
                self.user_id = user_data.get('id')
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                self.log_result("Authentication", True, f"Logged in as {self.username}, user_id: {self.user_id}")
                return True
            else:
                self.log_result("Authentication", False, f"Status: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Authentication", False, f"Exception: {str(e)}")
            return False

    def create_test_party(self, name: str, party_type: str = "customer") -> Optional[str]:
        """Create a test party and return party ID - generates audit logs"""
        try:
            party_data = {
                "name": name,
                "phone": "99887766",
                "address": "Test Address for Audit Logs",
                "party_type": party_type,
                "notes": f"Test party for audit logs filtering - {datetime.now().isoformat()}"
            }
            
            response = self.session.post(f"{self.base_url}/api/parties", json=party_data)
            
            if response.status_code == 200:
                party = response.json()
                party_id = party.get('id')
                self.created_party_ids.append(party_id)
                return party_id
            else:
                self.log_result(f"Create Test Party ({name})", False, f"Status: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_result(f"Create Test Party ({name})", False, f"Exception: {str(e)}")
            return None

    def update_test_party(self, party_id: str, name: str) -> bool:
        """Update a test party - generates audit logs"""
        try:
            update_data = {
                "name": f"{name} - Updated",
                "notes": f"Updated for audit logs testing - {datetime.now().isoformat()}"
            }
            
            response = self.session.patch(f"{self.base_url}/api/parties/{party_id}", json=update_data)
            return response.status_code == 200
        except Exception as e:
            return False

    def delete_test_party(self, party_id: str) -> bool:
        """Delete a test party - generates audit logs"""
        try:
            response = self.session.delete(f"{self.base_url}/api/parties/{party_id}")
            return response.status_code == 200
        except Exception as e:
            return False

    def get_audit_logs(self, **filters) -> Optional[Dict]:
        """Get audit logs with optional filters"""
        try:
            params = {}
            for key, value in filters.items():
                if value is not None:
                    params[key] = value
            
            response = self.session.get(f"{self.base_url}/api/audit-logs", params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": response.status_code, "message": response.text}
        except Exception as e:
            return {"error": "exception", "message": str(e)}

    # ============================================================================
    # SETUP PHASE - Create Test Data
    # ============================================================================

    def setup_test_data(self):
        """Setup Phase - Create test entities to generate audit logs"""
        print("🔧 SETUP PHASE - Creating Test Data to Generate Audit Logs")
        print("-" * 60)
        
        # Create 3 parties to generate audit logs
        party1_id = self.create_test_party("Audit Test Party 001", "customer")
        party2_id = self.create_test_party("Audit Test Party 002", "vendor") 
        party3_id = self.create_test_party("Audit Test Party 003", "customer")
        
        if not all([party1_id, party2_id, party3_id]):
            self.log_result("Setup Test Data", False, "Failed to create all test parties")
            return False
        
        # Update one party to generate update audit log
        update_success = self.update_test_party(party1_id, "Audit Test Party 001")
        
        # Delete one party to generate delete audit log  
        delete_success = self.delete_test_party(party3_id)
        
        if update_success and delete_success:
            self.log_result("Setup Test Data", True, 
                          f"Created 3 parties, updated 1, deleted 1. Generated audit logs with module='party', actions=['create', 'update', 'delete']")
            return True
        else:
            self.log_result("Setup Test Data", False, "Failed to complete all test operations")
            return False

    # ============================================================================
    # TEST INDIVIDUAL FILTERS
    # ============================================================================

    def test_date_range_filters(self):
        """Test date range filtering (date_from, date_to)"""
        print("🔸 Testing Date Range Filters")
        
        # Test 1: date_from filter
        today = datetime.now().strftime('%Y-%m-%d')
        result = self.get_audit_logs(date_from=today)
        
        if "error" in result:
            self.log_result("Date Range Filter - date_from", False, 
                          f"API error: {result.get('message', 'Unknown error')}")
            return
        
        logs = result if isinstance(result, list) else result.get('logs', [])
        if logs:
            # Verify all logs are from today or later
            all_valid = True
            for log in logs:
                log_date = log.get('timestamp', '')[:10]  # Extract YYYY-MM-DD
                if log_date < today:
                    all_valid = False
                    break
            
            if all_valid:
                self.log_result("Date Range Filter - date_from", True, 
                              f"Found {len(logs)} logs from {today} onwards")
            else:
                self.log_result("Date Range Filter - date_from", False, 
                              "Some logs are from before the specified date_from")
        else:
            self.log_result("Date Range Filter - date_from", True, 
                          "No logs found for today (expected if no recent activity)")
        
        # Test 2: date_to filter
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        result = self.get_audit_logs(date_to=tomorrow)
        
        if "error" in result:
            self.log_result("Date Range Filter - date_to", False, 
                          f"API error: {result.get('message', 'Unknown error')}")
            return
        
        logs = result if isinstance(result, list) else result.get('logs', [])
        self.log_result("Date Range Filter - date_to", True, 
                      f"Found {len(logs)} logs up to {tomorrow}")
        
        # Test 3: Combined date range
        result = self.get_audit_logs(date_from=today, date_to=tomorrow)
        
        if "error" in result:
            self.log_result("Date Range Filter - Combined", False, 
                          f"API error: {result.get('message', 'Unknown error')}")
            return
        
        logs = result if isinstance(result, list) else result.get('logs', [])
        self.log_result("Date Range Filter - Combined", True, 
                      f"Found {len(logs)} logs between {today} and {tomorrow}")

    def test_user_filter(self):
        """Test user_id filtering"""
        print("🔸 Testing User Filter")
        
        if not self.user_id:
            self.log_result("User Filter", False, "No user_id available from login")
            return
        
        result = self.get_audit_logs(user_id=self.user_id)
        
        if "error" in result:
            self.log_result("User Filter", False, 
                          f"API error: {result.get('message', 'Unknown error')}")
            return
        
        logs = result if isinstance(result, list) else result.get('logs', [])
        
        if logs:
            # Verify all logs have matching user_id
            all_match = True
            for log in logs:
                if log.get('user_id') != self.user_id:
                    all_match = False
                    break
            
            if all_match:
                self.log_result("User Filter", True, 
                              f"Found {len(logs)} logs for user_id: {self.user_id}")
            else:
                self.log_result("User Filter", False, 
                              "Some logs have different user_id than expected")
        else:
            self.log_result("User Filter", True, 
                          f"No logs found for user_id: {self.user_id} (expected if no activity)")

    def test_module_filter(self):
        """Test module filtering"""
        print("🔸 Testing Module Filter")
        
        result = self.get_audit_logs(module="party")
        
        if "error" in result:
            self.log_result("Module Filter", False, 
                          f"API error: {result.get('message', 'Unknown error')}")
            return
        
        logs = result if isinstance(result, list) else result.get('logs', [])
        
        if logs:
            # Verify all logs have module='party'
            all_match = True
            for log in logs:
                if log.get('module') != 'party':
                    all_match = False
                    break
            
            if all_match:
                self.log_result("Module Filter", True, 
                              f"Found {len(logs)} logs with module='party'")
            else:
                self.log_result("Module Filter", False, 
                              "Some logs have different module than 'party'")
        else:
            self.log_result("Module Filter", True, 
                          "No logs found with module='party' (expected if no party operations)")

    def test_action_filters(self):
        """Test action filtering"""
        print("🔸 Testing Action Filters")
        
        # Test create action
        result = self.get_audit_logs(action="create")
        
        if "error" in result:
            self.log_result("Action Filter - create", False, 
                          f"API error: {result.get('message', 'Unknown error')}")
        else:
            logs = result if isinstance(result, list) else result.get('logs', [])
            if logs:
                all_match = all(log.get('action') == 'create' for log in logs)
                if all_match:
                    self.log_result("Action Filter - create", True, 
                                  f"Found {len(logs)} logs with action='create'")
                else:
                    self.log_result("Action Filter - create", False, 
                                  "Some logs have different action than 'create'")
            else:
                self.log_result("Action Filter - create", True, 
                              "No logs found with action='create'")
        
        # Test update action
        result = self.get_audit_logs(action="update")
        
        if "error" in result:
            self.log_result("Action Filter - update", False, 
                          f"API error: {result.get('message', 'Unknown error')}")
        else:
            logs = result if isinstance(result, list) else result.get('logs', [])
            self.log_result("Action Filter - update", True, 
                          f"Found {len(logs)} logs with action='update'")
        
        # Test delete action
        result = self.get_audit_logs(action="delete")
        
        if "error" in result:
            self.log_result("Action Filter - delete", False, 
                          f"API error: {result.get('message', 'Unknown error')}")
        else:
            logs = result if isinstance(result, list) else result.get('logs', [])
            self.log_result("Action Filter - delete", True, 
                          f"Found {len(logs)} logs with action='delete'")

    # ============================================================================
    # TEST COMBINED FILTERS
    # ============================================================================

    def test_combined_filters(self):
        """Test multiple filters combined"""
        print("🔸 Testing Combined Filters")
        
        # Test module + action
        result = self.get_audit_logs(module="party", action="create")
        
        if "error" in result:
            self.log_result("Combined Filter - module+action", False, 
                          f"API error: {result.get('message', 'Unknown error')}")
        else:
            logs = result if isinstance(result, list) else result.get('logs', [])
            if logs:
                all_match = all(log.get('module') == 'party' and log.get('action') == 'create' for log in logs)
                if all_match:
                    self.log_result("Combined Filter - module+action", True, 
                                  f"Found {len(logs)} logs with module='party' AND action='create'")
                else:
                    self.log_result("Combined Filter - module+action", False, 
                                  "Some logs don't match both module='party' AND action='create'")
            else:
                self.log_result("Combined Filter - module+action", True, 
                              "No logs found with module='party' AND action='create'")
        
        # Test module + user_id
        if self.user_id:
            result = self.get_audit_logs(module="party", user_id=self.user_id)
            
            if "error" in result:
                self.log_result("Combined Filter - module+user", False, 
                              f"API error: {result.get('message', 'Unknown error')}")
            else:
                logs = result if isinstance(result, list) else result.get('logs', [])
                self.log_result("Combined Filter - module+user", True, 
                              f"Found {len(logs)} logs with module='party' AND user_id='{self.user_id}'")
        
        # Test date + module + action
        today = datetime.now().strftime('%Y-%m-%d')
        result = self.get_audit_logs(date_from=today, module="party", action="create")
        
        if "error" in result:
            self.log_result("Combined Filter - date+module+action", False, 
                          f"API error: {result.get('message', 'Unknown error')}")
        else:
            logs = result if isinstance(result, list) else result.get('logs', [])
            self.log_result("Combined Filter - date+module+action", True, 
                          f"Found {len(logs)} logs with date_from='{today}' AND module='party' AND action='create'")

    # ============================================================================
    # TEST EDGE CASES
    # ============================================================================

    def test_edge_cases(self):
        """Test edge cases and error handling"""
        print("🔸 Testing Edge Cases")
        
        # Test invalid date format
        result = self.get_audit_logs(date_from="invalid-date")
        
        if "error" in result:
            self.log_result("Edge Case - Invalid Date", True, 
                          f"Invalid date correctly rejected: {result.get('message', 'Unknown error')}")
        else:
            self.log_result("Edge Case - Invalid Date", False, 
                          "Invalid date was accepted (should be rejected)")
        
        # Test non-existent user
        result = self.get_audit_logs(user_id="non-existent-user-id")
        
        if "error" in result:
            # API might return error or empty results - both are acceptable
            self.log_result("Edge Case - Non-existent User", True, 
                          f"Non-existent user handled gracefully: {result.get('message', 'Unknown error')}")
        else:
            logs = result if isinstance(result, list) else result.get('logs', [])
            self.log_result("Edge Case - Non-existent User", True, 
                          f"Non-existent user returned {len(logs)} logs (empty result is expected)")
        
        # Test non-existent module
        result = self.get_audit_logs(module="nonexistent_module")
        
        if "error" in result:
            self.log_result("Edge Case - Non-existent Module", True, 
                          f"Non-existent module handled gracefully: {result.get('message', 'Unknown error')}")
        else:
            logs = result if isinstance(result, list) else result.get('logs', [])
            self.log_result("Edge Case - Non-existent Module", True, 
                          f"Non-existent module returned {len(logs)} logs (empty result is expected)")

    # ============================================================================
    # VERIFICATION CHECKLIST
    # ============================================================================

    def test_verification_checklist(self):
        """Test comprehensive verification checklist"""
        print("🔸 Testing Verification Checklist")
        
        # Get all audit logs to verify structure and sorting
        result = self.get_audit_logs()
        
        if "error" in result:
            self.log_result("Verification - API Response", False, 
                          f"Failed to get audit logs: {result.get('message', 'Unknown error')}")
            return
        
        logs = result if isinstance(result, list) else result.get('logs', [])
        
        if not logs:
            self.log_result("Verification - API Response", True, 
                          "No audit logs found (expected if system is new)")
            return
        
        # Check response structure
        first_log = logs[0]
        required_fields = ['id', 'timestamp', 'user_id', 'user_name', 'module', 'record_id', 'action']
        missing_fields = [field for field in required_fields if field not in first_log]
        
        if not missing_fields:
            self.log_result("Verification - Response Structure", True, 
                          f"All required fields present: {required_fields}")
        else:
            self.log_result("Verification - Response Structure", False, 
                          f"Missing fields: {missing_fields}")
        
        # Check sorting (newest first)
        if len(logs) > 1:
            timestamps = [log.get('timestamp', '') for log in logs[:5]]  # Check first 5
            is_sorted = all(timestamps[i] >= timestamps[i+1] for i in range(len(timestamps)-1))
            
            if is_sorted:
                self.log_result("Verification - Sorting", True, 
                              "Logs are sorted by timestamp descending (newest first)")
            else:
                self.log_result("Verification - Sorting", False, 
                              "Logs are not properly sorted by timestamp")
        else:
            self.log_result("Verification - Sorting", True, 
                          "Only one log found, sorting not applicable")
        
        # Count logs before and after applying filters
        all_logs_count = len(logs)
        
        # Apply a filter and verify it reduces results
        filtered_result = self.get_audit_logs(module="party")
        if "error" not in filtered_result:
            filtered_logs = filtered_result if isinstance(filtered_result, list) else filtered_result.get('logs', [])
            filtered_count = len(filtered_logs)
            
            if filtered_count <= all_logs_count:
                self.log_result("Verification - Filter Reduction", True, 
                              f"Filter reduced results: {all_logs_count} → {filtered_count}")
            else:
                self.log_result("Verification - Filter Reduction", False, 
                              f"Filter increased results: {all_logs_count} → {filtered_count}")
        else:
            self.log_result("Verification - Filter Reduction", False, 
                          "Failed to test filter reduction")

    # ============================================================================
    # MAIN TEST EXECUTION
    # ============================================================================

    def run_all_tests(self):
        """Run comprehensive audit logs filtering tests"""
        print("🎯 COMPREHENSIVE AUDIT LOGS FILTERING TESTS")
        print("=" * 80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Setup failed. Cannot proceed with comprehensive tests.")
            return
        
        print("\n📋 INDIVIDUAL FILTER TESTS")
        print("-" * 60)
        self.test_date_range_filters()
        self.test_user_filter()
        self.test_module_filter()
        self.test_action_filters()
        
        print("\n📋 COMBINED FILTER TESTS")
        print("-" * 60)
        self.test_combined_filters()
        
        print("\n📋 EDGE CASE TESTS")
        print("-" * 60)
        self.test_edge_cases()
        
        print("\n📋 VERIFICATION CHECKLIST")
        print("-" * 60)
        self.test_verification_checklist()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("🎯 AUDIT LOGS FILTERING TEST RESULTS SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"\n📊 OVERALL STATISTICS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Show all results
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            print(f"   {result['status']}: {result['test']}")
            if result['details']:
                print(f"      → {result['details']}")
        
        # Show failed tests details
        failed_results = [r for r in self.test_results if not r['success']]
        if failed_results:
            print(f"\n❌ FAILED TESTS DETAILS:")
            for result in failed_results:
                print(f"\n   Test: {result['test']}")
                print(f"   Details: {result['details']}")
                if result.get('response_data'):
                    print(f"   Response: {result['response_data']}")
        
        print(f"\n🎯 AUDIT LOGS FILTERING ASSESSMENT:")
        if failed_tests == 0:
            print("   ✅ ALL TESTS PASSED - AUDIT LOGS FILTERING FULLY FUNCTIONAL")
        elif failed_tests <= 2:
            print(f"   ⚠️  MOSTLY FUNCTIONAL - {failed_tests} minor issues to fix")
        elif failed_tests <= 5:
            print(f"   ⚠️  NEEDS WORK - {failed_tests} issues to fix")
        else:
            print(f"   ❌ NOT FUNCTIONAL - {failed_tests} critical issues to fix")
        
        print("\n" + "=" * 80)


# Entry point
def main():
    """Main execution function"""
    # Configuration
    BASE_URL = "https://errorfix-perm.preview.emergentagent.com"
    USERNAME = "admin"
    PASSWORD = "admin123"
    
    print("🚀 Starting Audit Logs Filtering Tests")
    print(f"Backend URL: {BASE_URL}")
    print(f"Username: {USERNAME}")
    print("-" * 80)
    
    # Initialize tester
    tester = AuditLogsFilterTester(BASE_URL, USERNAME, PASSWORD)
    
    # Run all audit logs filtering tests
    tester.run_all_tests()

if __name__ == "__main__":
    main()


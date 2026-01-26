#!/usr/bin/env python3
"""
FOCUSED AUTHENTICATION TESTING - Avoiding Rate Limits
Testing core authentication functionality with proper delays
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8001/api"
HEADERS = {"Content-Type": "application/json"}

class FocusedAuthTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
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

    def test_core_authentication(self):
        """Test core authentication functionality"""
        print("🔐 CORE AUTHENTICATION TESTING")
        print("=" * 60)
        
        # Test 1: Admin Login Success
        try:
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["access_token", "token_type", "user", "csrf_token"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    user = data["user"]
                    user_required_fields = ["id", "username", "email", "role", "permissions", "is_active"]
                    user_missing_fields = [field for field in user_required_fields if field not in user]
                    
                    if not user_missing_fields:
                        permissions_count = len(user.get("permissions", []))
                        self.log_result("Admin Login - Complete Success", True, 
                                      f"✅ Login successful with all required fields\n"
                                      f"    - Token type: {data['token_type']}\n"
                                      f"    - Role: {user['role']}\n"
                                      f"    - Permissions: {permissions_count}\n"
                                      f"    - Active: {user['is_active']}\n"
                                      f"    - CSRF token length: {len(data['csrf_token'])}")
                        
                        # Store for later tests
                        self.admin_token = data["access_token"]
                        self.admin_csrf = data["csrf_token"]
                        self.admin_user = user
                    else:
                        self.log_result("Admin Login - Complete Success", False, "", 
                                      f"Missing user fields: {user_missing_fields}")
                else:
                    self.log_result("Admin Login - Complete Success", False, "", 
                                  f"Missing response fields: {missing_fields}")
            else:
                self.log_result("Admin Login - Complete Success", False, "", 
                              f"Login failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Admin Login - Complete Success", False, "", f"Error: {str(e)}")
        
        # Wait to avoid rate limiting
        time.sleep(2)
        
        # Test 2: Staff Login Success
        try:
            login_data = {
                "username": "staff",
                "password": "staff123"
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                user = data["user"]
                permissions_count = len(user.get("permissions", []))
                
                self.log_result("Staff Login - Complete Success", True, 
                              f"✅ Staff login successful\n"
                              f"    - Role: {user['role']}\n"
                              f"    - Permissions: {permissions_count}\n"
                              f"    - Active: {user['is_active']}")
                
                # Store for later tests
                self.staff_token = data["access_token"]
                self.staff_csrf = data["csrf_token"]
                self.staff_user = user
            else:
                self.log_result("Staff Login - Complete Success", False, "", 
                              f"Staff login failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Staff Login - Complete Success", False, "", f"Error: {str(e)}")
        
        # Wait to avoid rate limiting
        time.sleep(2)

    def test_authentication_security(self):
        """Test authentication security features"""
        print("🛡️ AUTHENTICATION SECURITY TESTING")
        print("=" * 60)
        
        # Test 3: Invalid Credentials
        try:
            login_data = {
                "username": "admin",
                "password": "wrongpassword"
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 401:
                self.log_result("Invalid Credentials Security", True, 
                              "✅ Correctly rejected invalid password with 401")
            else:
                self.log_result("Invalid Credentials Security", False, "", 
                              f"Expected 401, got {response.status_code}")
                
        except Exception as e:
            self.log_result("Invalid Credentials Security", False, "", f"Error: {str(e)}")
        
        # Wait to avoid rate limiting
        time.sleep(2)
        
        # Test 4: Non-existent User
        try:
            login_data = {
                "username": "nonexistentuser",
                "password": "anypassword"
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if response.status_code == 401:
                self.log_result("Non-existent User Security", True, 
                              "✅ Correctly rejected non-existent user with 401")
            else:
                self.log_result("Non-existent User Security", False, "", 
                              f"Expected 401, got {response.status_code}")
                
        except Exception as e:
            self.log_result("Non-existent User Security", False, "", f"Error: {str(e)}")
        
        # Wait to avoid rate limiting
        time.sleep(2)

    def test_token_functionality(self):
        """Test JWT token functionality"""
        print("🎫 TOKEN FUNCTIONALITY TESTING")
        print("=" * 60)
        
        # Test 5: /auth/me endpoint with valid token
        if hasattr(self, 'admin_token'):
            try:
                headers = {
                    "Authorization": f"Bearer {self.admin_token}",
                    "Content-Type": "application/json"
                }
                
                response = self.session.get(f"{BASE_URL}/auth/me", headers=headers)
                
                if response.status_code == 200:
                    user_data = response.json()
                    if user_data.get("username") == "admin":
                        self.log_result("Token Validation - /auth/me", True, 
                                      f"✅ Successfully retrieved user data\n"
                                      f"    - Username: {user_data['username']}\n"
                                      f"    - Role: {user_data['role']}\n"
                                      f"    - Permissions: {len(user_data.get('permissions', []))}")
                    else:
                        self.log_result("Token Validation - /auth/me", False, "", 
                                      f"Wrong user data returned: {user_data.get('username')}")
                else:
                    self.log_result("Token Validation - /auth/me", False, "", 
                                  f"Failed: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.log_result("Token Validation - /auth/me", False, "", f"Error: {str(e)}")
        
        # Wait to avoid rate limiting
        time.sleep(2)
        
        # Test 6: Protected endpoint with valid token
        if hasattr(self, 'admin_token') and hasattr(self, 'admin_csrf'):
            try:
                headers = {
                    "Authorization": f"Bearer {self.admin_token}",
                    "X-CSRF-Token": self.admin_csrf,
                    "Content-Type": "application/json"
                }
                
                response = self.session.get(f"{BASE_URL}/parties", headers=headers)
                
                if response.status_code == 200:
                    parties_data = response.json()
                    self.log_result("Protected Endpoint Access", True, 
                                  f"✅ Successfully accessed /parties endpoint\n"
                                  f"    - Response type: {type(parties_data)}\n"
                                  f"    - Has data: {len(parties_data) if isinstance(parties_data, list) else 'dict/other'}")
                else:
                    self.log_result("Protected Endpoint Access", False, "", 
                                  f"Failed: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.log_result("Protected Endpoint Access", False, "", f"Error: {str(e)}")
        
        # Wait to avoid rate limiting
        time.sleep(2)
        
        # Test 7: Protected endpoint without token
        try:
            response = self.session.get(f"{BASE_URL}/parties")
            
            if response.status_code == 401:
                self.log_result("No Token Protection", True, 
                              "✅ Correctly rejected request without token (401)")
            else:
                self.log_result("No Token Protection", False, "", 
                              f"Expected 401, got {response.status_code}")
                
        except Exception as e:
            self.log_result("No Token Protection", False, "", f"Error: {str(e)}")
        
        # Wait to avoid rate limiting
        time.sleep(2)

    def test_permission_system(self):
        """Test permission system"""
        print("🔑 PERMISSION SYSTEM TESTING")
        print("=" * 60)
        
        # Test 8: Admin vs Staff Permission Comparison
        if hasattr(self, 'admin_user') and hasattr(self, 'staff_user'):
            try:
                admin_permissions = self.admin_user.get("permissions", [])
                staff_permissions = self.staff_user.get("permissions", [])
                
                admin_count = len(admin_permissions)
                staff_count = len(staff_permissions)
                
                # Check if admin has more permissions than staff
                if admin_count > staff_count:
                    self.log_result("Permission Hierarchy", True, 
                                  f"✅ Correct permission hierarchy\n"
                                  f"    - Admin permissions: {admin_count}\n"
                                  f"    - Staff permissions: {staff_count}\n"
                                  f"    - Admin has {admin_count - staff_count} more permissions")
                else:
                    self.log_result("Permission Hierarchy", False, "", 
                                  f"Admin should have more permissions than staff. "
                                  f"Admin: {admin_count}, Staff: {staff_count}")
                
                # Check specific permissions
                admin_only_permissions = set(admin_permissions) - set(staff_permissions)
                if admin_only_permissions:
                    self.log_result("Admin-Only Permissions", True, 
                                  f"✅ Admin has exclusive permissions\n"
                                  f"    - Exclusive count: {len(admin_only_permissions)}\n"
                                  f"    - Examples: {list(admin_only_permissions)[:5]}")
                else:
                    self.log_result("Admin-Only Permissions", False, "", 
                                  "Admin should have some exclusive permissions")
                    
            except Exception as e:
                self.log_result("Permission System Testing", False, "", f"Error: {str(e)}")

    def test_logout_functionality(self):
        """Test logout functionality"""
        print("🚪 LOGOUT FUNCTIONALITY TESTING")
        print("=" * 60)
        
        # Test 9: Logout endpoint
        if hasattr(self, 'admin_token') and hasattr(self, 'admin_csrf'):
            try:
                headers = {
                    "Authorization": f"Bearer {self.admin_token}",
                    "X-CSRF-Token": self.admin_csrf,
                    "Content-Type": "application/json"
                }
                
                response = self.session.post(f"{BASE_URL}/auth/logout", headers=headers)
                
                if response.status_code == 200:
                    logout_data = response.json()
                    self.log_result("Logout Functionality", True, 
                                  f"✅ Successfully logged out\n"
                                  f"    - Response: {logout_data.get('message', 'No message')}")
                else:
                    self.log_result("Logout Functionality", False, "", 
                                  f"Logout failed: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.log_result("Logout Functionality", False, "", f"Error: {str(e)}")

    def run_focused_tests(self):
        """Run focused authentication tests"""
        print("🎯 FOCUSED AUTHENTICATION TESTING")
        print("=" * 80)
        print("Testing core authentication functionality with proper rate limiting delays")
        print("=" * 80)
        
        self.test_core_authentication()
        self.test_authentication_security()
        self.test_token_functionality()
        self.test_permission_system()
        self.test_logout_functionality()
        
        self.print_summary()

    def print_summary(self):
        """Print test results summary"""
        print("=" * 80)
        print("📊 FOCUSED AUTHENTICATION TESTING SUMMARY")
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
        
        # Overall assessment
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED - AUTHENTICATION SYSTEM FULLY FUNCTIONAL")
        elif passed_tests >= total_tests * 0.8:
            print("✅ MOSTLY FUNCTIONAL - Minor issues detected")
        elif passed_tests >= total_tests * 0.6:
            print("⚠️ PARTIALLY FUNCTIONAL - Some issues need attention")
        else:
            print("❌ SIGNIFICANT ISSUES - Authentication system needs fixes")
        
        print("=" * 80)

if __name__ == "__main__":
    tester = FocusedAuthTester()
    tester.run_focused_tests()
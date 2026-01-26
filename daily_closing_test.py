#!/usr/bin/env python3
"""
Daily Closing Auto-Calculation Feature Testing
Testing the new GET /api/daily-closings/calculate/{date} endpoint

Test Scenarios:
1. Setup test data (transactions and previous closing records)
2. Test auto-calculation for day WITH previous closing
3. Test auto-calculation for FIRST day (no previous closing)
4. Test date with NO transactions
5. Test invalid date format
6. Test precision (3 decimal places for money values)
"""

import requests
import json
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional

class DailyClosingTester:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
        self.session = requests.Session()
        self.test_results = []
        
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
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                self.log_result("Authentication", True, f"Logged in as {self.username}")
                return True
            else:
                self.log_result("Authentication", False, f"Status: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Authentication", False, f"Exception: {str(e)}")
            return False

    def create_test_account(self, name: str, account_type: str = "asset") -> Optional[str]:
        """Create a test account and return account ID"""
        try:
            account_data = {
                "name": name,
                "account_type": account_type,
                "opening_balance": 0.0,
                "current_balance": 0.0
            }
            
            response = self.session.post(f"{self.base_url}/api/accounts", json=account_data)
            
            if response.status_code == 200:
                account = response.json()
                return account.get('id')
            else:
                self.log_result(f"Create Test Account ({name})", False, f"Status: {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_result(f"Create Test Account ({name})", False, f"Exception: {str(e)}")
            return None

    def create_test_transaction(self, date: str, transaction_type: str, amount: float, account_id: str, category: str = "Test") -> Optional[str]:
        """Create a test transaction"""
        try:
            transaction_data = {
                "date": date,
                "transaction_type": transaction_type,
                "mode": "Cash",
                "account_id": account_id,
                "amount": amount,
                "category": category,
                "notes": f"Test transaction for daily closing - {transaction_type} {amount}"
            }
            
            response = self.session.post(f"{self.base_url}/api/transactions", json=transaction_data)
            
            if response.status_code == 200:
                transaction = response.json()
                return transaction.get('id')
            else:
                return None
        except Exception as e:
            return None

    def create_daily_closing(self, date: str, actual_closing: float) -> Optional[str]:
        """Create a daily closing record"""
        try:
            closing_data = {
                "date": date,
                "actual_closing": actual_closing,
                "notes": "Test daily closing record"
            }
            
            response = self.session.post(f"{self.base_url}/api/daily-closings", json=closing_data)
            
            if response.status_code == 200:
                closing = response.json()
                return closing.get('id')
            else:
                return None
        except Exception as e:
            return None

    def get_daily_closing_calculation(self, date: str) -> Optional[Dict]:
        """Get daily closing auto-calculation for a specific date"""
        try:
            response = self.session.get(f"{self.base_url}/api/daily-closings/calculate/{date}")
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": response.status_code, "message": response.text}
        except Exception as e:
            return {"error": "exception", "message": str(e)}

    def test_setup_test_data(self):
        """Test Scenario 1: Setup Test Data"""
        print("🔸 Test Scenario 1: Setup Test Data")
        
        # Create test account
        account_id = self.create_test_account("Daily Closing Test Cash Account", "asset")
        if not account_id:
            self.log_result("Setup - Create Test Account", False, "Failed to create test account")
            return None
        
        # Create previous day's closing record (2025-01-14)
        closing_id = self.create_daily_closing("2025-01-14T23:59:59Z", 1000.500)
        if not closing_id:
            self.log_result("Setup - Create Previous Closing", False, "Failed to create previous day closing")
            return None
        
        # Create transactions for 2025-01-15
        transactions = []
        
        # Credit transactions (money coming in)
        credit1_id = self.create_test_transaction("2025-01-15T10:00:00Z", "credit", 500.250, account_id, "Sale")
        credit2_id = self.create_test_transaction("2025-01-15T14:00:00Z", "credit", 750.375, account_id, "Payment Received")
        
        # Debit transactions (money going out)
        debit1_id = self.create_test_transaction("2025-01-15T11:00:00Z", "debit", 200.125, account_id, "Purchase")
        debit2_id = self.create_test_transaction("2025-01-15T16:00:00Z", "debit", 150.000, account_id, "Expense")
        
        if credit1_id and credit2_id and debit1_id and debit2_id:
            transactions = [credit1_id, credit2_id, debit1_id, debit2_id]
            self.log_result("Setup - Create Test Transactions", True, 
                          f"Created 4 transactions: 2 credits (500.250, 750.375), 2 debits (200.125, 150.000)")
        else:
            self.log_result("Setup - Create Test Transactions", False, "Failed to create all test transactions")
            return None
        
        # Create transactions for first day test (2025-01-10 - no previous closing)
        first_day_transactions = []
        first_credit = self.create_test_transaction("2025-01-10T10:00:00Z", "credit", 300.000, account_id, "First Day Sale")
        first_debit = self.create_test_transaction("2025-01-10T15:00:00Z", "debit", 100.000, account_id, "First Day Expense")
        
        if first_credit and first_debit:
            first_day_transactions = [first_credit, first_debit]
            self.log_result("Setup - Create First Day Transactions", True, 
                          "Created transactions for first day test (2025-01-10)")
        else:
            self.log_result("Setup - Create First Day Transactions", False, "Failed to create first day transactions")
        
        return {
            "account_id": account_id,
            "closing_id": closing_id,
            "transactions": transactions,
            "first_day_transactions": first_day_transactions
        }

    def test_calculation_with_previous_closing(self):
        """Test Scenario 2: Auto-Calculation for Day WITH Previous Closing"""
        print("🔸 Test Scenario 2: Auto-Calculation for Day WITH Previous Closing")
        
        # Test date: 2025-01-15 (should have previous closing from 2025-01-14)
        result = self.get_daily_closing_calculation("2025-01-15")
        
        if "error" in result:
            self.log_result("Calculation WITH Previous Closing", False, 
                          f"API call failed: {result.get('message', 'Unknown error')}")
            return
        
        # Verify response structure
        required_fields = [
            "opening_cash", "total_credit", "total_debit", "expected_closing",
            "transaction_count", "credit_count", "debit_count", "has_previous_closing"
        ]
        
        missing_fields = [field for field in required_fields if field not in result]
        if missing_fields:
            self.log_result("Calculation WITH Previous Closing", False, 
                          f"Missing required fields: {missing_fields}")
            return
        
        # Verify calculations
        opening_cash = result.get("opening_cash", 0)
        total_credit = result.get("total_credit", 0)
        total_debit = result.get("total_debit", 0)
        expected_closing = result.get("expected_closing", 0)
        transaction_count = result.get("transaction_count", 0)
        credit_count = result.get("credit_count", 0)
        debit_count = result.get("debit_count", 0)
        has_previous_closing = result.get("has_previous_closing", False)
        
        # Expected values
        expected_opening = 1000.500  # From previous day's closing
        expected_total_credit = 500.250 + 750.375  # 1250.625
        expected_total_debit = 200.125 + 150.000   # 350.125
        expected_expected_closing = expected_opening + expected_total_credit - expected_total_debit  # 1900.000
        
        # Verify values with precision tolerance
        tolerance = 0.001
        
        checks = [
            (abs(opening_cash - expected_opening) < tolerance, f"opening_cash: expected {expected_opening}, got {opening_cash}"),
            (abs(total_credit - expected_total_credit) < tolerance, f"total_credit: expected {expected_total_credit}, got {total_credit}"),
            (abs(total_debit - expected_total_debit) < tolerance, f"total_debit: expected {expected_total_debit}, got {total_debit}"),
            (abs(expected_closing - expected_expected_closing) < tolerance, f"expected_closing: expected {expected_expected_closing}, got {expected_closing}"),
            (transaction_count == 4, f"transaction_count: expected 4, got {transaction_count}"),
            (credit_count == 2, f"credit_count: expected 2, got {credit_count}"),
            (debit_count == 2, f"debit_count: expected 2, got {debit_count}"),
            (has_previous_closing == True, f"has_previous_closing: expected True, got {has_previous_closing}")
        ]
        
        failed_checks = [check[1] for check in checks if not check[0]]
        
        if not failed_checks:
            self.log_result("Calculation WITH Previous Closing", True, 
                          f"All calculations correct: opening={opening_cash}, credit={total_credit}, debit={total_debit}, expected={expected_closing}")
        else:
            self.log_result("Calculation WITH Previous Closing", False, 
                          f"Calculation errors: {'; '.join(failed_checks)}")

    def test_calculation_first_day_no_previous(self):
        """Test Scenario 3: Auto-Calculation for FIRST Day (No Previous Closing)"""
        print("🔸 Test Scenario 3: Auto-Calculation for FIRST Day (No Previous Closing)")
        
        # Test date: 2025-01-10 (should have no previous closing)
        result = self.get_daily_closing_calculation("2025-01-10")
        
        if "error" in result:
            self.log_result("Calculation FIRST Day", False, 
                          f"API call failed: {result.get('message', 'Unknown error')}")
            return
        
        # Verify response structure
        opening_cash = result.get("opening_cash", 0)
        total_credit = result.get("total_credit", 0)
        total_debit = result.get("total_debit", 0)
        expected_closing = result.get("expected_closing", 0)
        has_previous_closing = result.get("has_previous_closing", True)  # Should be False
        
        # Expected values for first day
        expected_opening = 0.0  # No previous closing
        expected_total_credit = 300.000
        expected_total_debit = 100.000
        expected_expected_closing = expected_opening + expected_total_credit - expected_total_debit  # 200.000
        
        # Verify values
        tolerance = 0.001
        
        checks = [
            (abs(opening_cash - expected_opening) < tolerance, f"opening_cash: expected {expected_opening}, got {opening_cash}"),
            (abs(total_credit - expected_total_credit) < tolerance, f"total_credit: expected {expected_total_credit}, got {total_credit}"),
            (abs(total_debit - expected_total_debit) < tolerance, f"total_debit: expected {expected_total_debit}, got {total_debit}"),
            (abs(expected_closing - expected_expected_closing) < tolerance, f"expected_closing: expected {expected_expected_closing}, got {expected_closing}"),
            (has_previous_closing == False, f"has_previous_closing: expected False, got {has_previous_closing}")
        ]
        
        failed_checks = [check[1] for check in checks if not check[0]]
        
        if not failed_checks:
            self.log_result("Calculation FIRST Day", True, 
                          f"First day calculation correct: opening={opening_cash}, credit={total_credit}, debit={total_debit}, expected={expected_closing}")
        else:
            self.log_result("Calculation FIRST Day", False, 
                          f"First day calculation errors: {'; '.join(failed_checks)}")

    def test_calculation_no_transactions(self):
        """Test Scenario 4: Test Date with NO Transactions"""
        print("🔸 Test Scenario 4: Test Date with NO Transactions")
        
        # Test date: 2025-01-20 (future date with no transactions)
        result = self.get_daily_closing_calculation("2025-01-20")
        
        if "error" in result:
            self.log_result("Calculation NO Transactions", False, 
                          f"API call failed: {result.get('message', 'Unknown error')}")
            return
        
        # Verify response for empty day
        transaction_count = result.get("transaction_count", -1)
        total_credit = result.get("total_credit", -1)
        total_debit = result.get("total_debit", -1)
        credit_count = result.get("credit_count", -1)
        debit_count = result.get("debit_count", -1)
        
        # Expected values for empty day
        checks = [
            (transaction_count == 0, f"transaction_count: expected 0, got {transaction_count}"),
            (total_credit == 0.0, f"total_credit: expected 0.0, got {total_credit}"),
            (total_debit == 0.0, f"total_debit: expected 0.0, got {total_debit}"),
            (credit_count == 0, f"credit_count: expected 0, got {credit_count}"),
            (debit_count == 0, f"debit_count: expected 0, got {debit_count}")
        ]
        
        failed_checks = [check[1] for check in checks if not check[0]]
        
        if not failed_checks:
            self.log_result("Calculation NO Transactions", True, 
                          f"Empty day calculation correct: all counts and totals are 0")
        else:
            self.log_result("Calculation NO Transactions", False, 
                          f"Empty day calculation errors: {'; '.join(failed_checks)}")

    def test_invalid_date_format(self):
        """Test Scenario 5: Test Invalid Date Format"""
        print("🔸 Test Scenario 5: Test Invalid Date Format")
        
        # Test with invalid date format
        result = self.get_daily_closing_calculation("invalid-date")
        
        if "error" in result and result["error"] == 400:
            self.log_result("Invalid Date Format", True, 
                          f"Invalid date correctly rejected with 400 error: {result.get('message', 'No message')}")
        else:
            self.log_result("Invalid Date Format", False, 
                          f"Expected 400 error for invalid date, got: {result}")

    def test_precision_verification(self):
        """Test Scenario 6: Test Precision (3 decimal places)"""
        print("🔸 Test Scenario 6: Test Precision Verification")
        
        # Test with the date that has precise decimal values (2025-01-15)
        result = self.get_daily_closing_calculation("2025-01-15")
        
        if "error" in result:
            self.log_result("Precision Verification", False, 
                          f"API call failed: {result.get('message', 'Unknown error')}")
            return
        
        # Check that all money values have exactly 3 decimal places when converted to string
        money_fields = ["opening_cash", "total_credit", "total_debit", "expected_closing"]
        precision_checks = []
        
        for field in money_fields:
            value = result.get(field, 0)
            # Convert to string and check decimal places
            value_str = f"{value:.3f}"
            # Verify it has exactly 3 decimal places
            if '.' in value_str:
                decimal_part = value_str.split('.')[1]
                if len(decimal_part) == 3:
                    precision_checks.append(True)
                else:
                    precision_checks.append(False)
                    self.log_result("Precision Check", False, 
                                  f"{field}: {value} doesn't have 3 decimal places")
            else:
                precision_checks.append(False)
                self.log_result("Precision Check", False, 
                              f"{field}: {value} has no decimal places")
        
        if all(precision_checks):
            self.log_result("Precision Verification", True, 
                          "All money values have exactly 3 decimal places precision")
        else:
            self.log_result("Precision Verification", False, 
                          "Some money values don't have proper 3 decimal precision")

    def run_all_tests(self):
        """Run all daily closing calculation tests"""
        print("🎯 DAILY CLOSING AUTO-CALCULATION FEATURE TESTING")
        print("=" * 80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        print("\n📋 DAILY CLOSING CALCULATION TESTS")
        print("-" * 60)
        
        # Test Scenario 1: Setup test data
        test_data = self.test_setup_test_data()
        if not test_data:
            print("❌ Failed to setup test data. Cannot proceed with remaining tests.")
            return
        
        # Test Scenario 2: Calculation with previous closing
        self.test_calculation_with_previous_closing()
        
        # Test Scenario 3: First day calculation (no previous closing)
        self.test_calculation_first_day_no_previous()
        
        # Test Scenario 4: No transactions
        self.test_calculation_no_transactions()
        
        # Test Scenario 5: Invalid date format
        self.test_invalid_date_format()
        
        # Test Scenario 6: Precision verification
        self.test_precision_verification()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("🎯 DAILY CLOSING CALCULATION TEST RESULTS")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"\n📊 OVERALL STATISTICS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            print(f"   {result['status']}: {result['test']}")
            if result['details']:
                print(f"      {result['details']}")
        
        # Show failed tests details
        failed_results = [r for r in self.test_results if not r['success']]
        if failed_results:
            print(f"\n❌ FAILED TESTS DETAILS:")
            for result in failed_results:
                print(f"\n   Test: {result['test']}")
                print(f"   Details: {result['details']}")
                if result.get('response_data'):
                    print(f"   Response: {result['response_data']}")
        
        print(f"\n🎯 FEATURE READINESS ASSESSMENT:")
        if failed_tests == 0:
            print("   ✅ ALL TESTS PASSED - DAILY CLOSING FEATURE IS PRODUCTION READY")
        elif failed_tests <= 1:
            print(f"   ⚠️  MOSTLY READY - {failed_tests} minor issue to fix")
        elif failed_tests <= 2:
            print(f"   ⚠️  NEEDS WORK - {failed_tests} issues to fix")
        else:
            print(f"   ❌ NOT READY - {failed_tests} critical issues to fix")
        
        print("\n" + "=" * 80)

def main():
    """Main execution function"""
    # Configuration
    BASE_URL = "https://decimal-precision.preview.emergentagent.com"
    USERNAME = "admin"
    PASSWORD = "admin123"
    
    print("🚀 Starting Daily Closing Auto-Calculation Feature Testing")
    print(f"Backend URL: {BASE_URL}")
    print(f"Username: {USERNAME}")
    print("-" * 80)
    
    # Initialize tester
    tester = DailyClosingTester(BASE_URL, USERNAME, PASSWORD)
    
    # Run all tests
    tester.run_all_tests()

if __name__ == "__main__":
    main()
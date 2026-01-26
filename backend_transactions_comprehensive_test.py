#!/usr/bin/env python3
"""
COMPREHENSIVE MODULE 6 — TRANSACTIONS & MONEY FLOW BACKEND TESTING

This script tests the enhanced transaction management system including:
1. Enhanced GET /api/transactions endpoint with 6 filters (account_id, account_type, transaction_type, reference_type, start_date, end_date)
2. Running balance calculation (balance_before, balance_after for each transaction)
3. New GET /api/transactions/summary endpoint
4. Transaction source enrichment (Invoice Payment, Purchase Payment, Manual Entry)
5. Account type enrichment (cash/bank distinction)

Test Credentials: admin/admin123
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import uuid
from decimal import Decimal

# Configuration
BASE_URL = "https://decimal-precision.preview.emergentagent.com/api"
USERNAME = "admin"
PASSWORD = "admin123"

class TransactionsComprehensiveTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.test_account_id = None
        self.test_cash_account_id = None
        self.test_bank_account_id = None
        
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
    
    def setup_test_accounts(self):
        """Setup test accounts for testing"""
        try:
            # Get existing accounts
            response = self.session.get(f"{BASE_URL}/accounts")
            if response.status_code != 200:
                self.log_result("Account Setup", "FAIL", f"Failed to get accounts: {response.status_code}")
                return False
            
            accounts = response.json()
            
            # Find cash and bank accounts
            cash_accounts = [acc for acc in accounts if acc.get('account_type') in ['cash', 'petty']]
            bank_accounts = [acc for acc in accounts if acc.get('account_type') == 'bank']
            
            if cash_accounts:
                self.test_cash_account_id = cash_accounts[0]['id']
                self.log_result("Cash Account Setup", "PASS", f"Using cash account: {cash_accounts[0]['name']} (ID: {self.test_cash_account_id})")
            else:
                # Create a test cash account
                account_data = {
                    "name": "Test Cash Account",
                    "account_type": "cash",
                    "opening_balance": 1000.0
                }
                response = self.session.post(f"{BASE_URL}/accounts", json=account_data)
                if response.status_code == 200:
                    account = response.json()
                    self.test_cash_account_id = account['id']
                    self.log_result("Cash Account Creation", "PASS", f"Created test cash account: {account['name']}")
                else:
                    self.log_result("Cash Account Creation", "FAIL", f"Failed to create cash account: {response.status_code}")
                    return False
            
            if bank_accounts:
                self.test_bank_account_id = bank_accounts[0]['id']
                self.log_result("Bank Account Setup", "PASS", f"Using bank account: {bank_accounts[0]['name']} (ID: {self.test_bank_account_id})")
            else:
                # Create a test bank account
                account_data = {
                    "name": "Test Bank Account",
                    "account_type": "bank",
                    "opening_balance": 5000.0
                }
                response = self.session.post(f"{BASE_URL}/accounts", json=account_data)
                if response.status_code == 200:
                    account = response.json()
                    self.test_bank_account_id = account['id']
                    self.log_result("Bank Account Creation", "PASS", f"Created test bank account: {account['name']}")
                else:
                    self.log_result("Bank Account Creation", "FAIL", f"Failed to create bank account: {response.status_code}")
                    return False
            
            return True
            
        except Exception as e:
            self.log_result("Account Setup", "ERROR", f"Error setting up accounts: {str(e)}")
            return False
    
    def test_basic_transaction_retrieval(self):
        """Test basic transaction retrieval without filters"""
        print("\n" + "="*80)
        print("PART 1: BASIC TRANSACTION RETRIEVAL")
        print("="*80)
        
        try:
            response = self.session.get(f"{BASE_URL}/transactions")
            if response.status_code != 200:
                self.log_result("Basic Transaction Retrieval", "FAIL", f"Failed to get transactions: {response.status_code}")
                return
            
            data = response.json()
            
            # Verify response structure
            required_fields = ['items', 'pagination']
            for field in required_fields:
                if field not in data:
                    self.log_result("Response Structure", "FAIL", f"Missing field: {field}")
                    return
            
            self.log_result("Response Structure", "PASS", "Response has required fields: items, pagination")
            
            # Check pagination metadata
            pagination = data['pagination']
            pagination_fields = ['total_count', 'page', 'per_page', 'total_pages', 'has_next', 'has_prev']
            for field in pagination_fields:
                if field not in pagination:
                    self.log_result("Pagination Structure", "FAIL", f"Missing pagination field: {field}")
                    return
            
            self.log_result("Pagination Structure", "PASS", "Pagination has all required fields")
            
            # Verify transaction fields
            transactions = data['items']
            if transactions:
                txn = transactions[0]
                required_txn_fields = ['transaction_number', 'date', 'transaction_type', 'account_name', 'amount', 'category']
                new_fields = ['account_type', 'account_current_balance', 'transaction_source', 'balance_before', 'balance_after']
                
                for field in required_txn_fields:
                    if field not in txn:
                        self.log_result("Transaction Fields", "FAIL", f"Missing required field: {field}")
                        return
                
                for field in new_fields:
                    if field not in txn:
                        self.log_result("Enhanced Transaction Fields", "FAIL", f"Missing enhanced field: {field}")
                        return
                
                self.log_result("Transaction Fields", "PASS", "All required and enhanced fields present")
                self.log_result("Enhanced Fields", "PASS", f"New fields verified: account_type={txn.get('account_type')}, transaction_source={txn.get('transaction_source')}")
            else:
                self.log_result("Transaction Data", "PASS", "No transactions found (empty system)")
            
        except Exception as e:
            self.log_result("Basic Transaction Retrieval", "ERROR", f"Error: {str(e)}")
    
    def test_individual_filters(self):
        """Test individual filters"""
        print("\n" + "="*80)
        print("PART 2: INDIVIDUAL FILTER TESTING")
        print("="*80)
        
        # Test account_type=cash filter
        try:
            response = self.session.get(f"{BASE_URL}/transactions?account_type=cash")
            if response.status_code == 200:
                data = response.json()
                transactions = data['items']
                
                # Verify all transactions are from cash/petty accounts
                cash_only = all(txn.get('account_type') in ['cash', 'petty'] for txn in transactions)
                if cash_only:
                    self.log_result("Cash Filter", "PASS", f"All {len(transactions)} transactions are from cash/petty accounts")
                else:
                    non_cash = [txn for txn in transactions if txn.get('account_type') not in ['cash', 'petty']]
                    self.log_result("Cash Filter", "FAIL", f"Found {len(non_cash)} non-cash transactions in cash filter")
            else:
                self.log_result("Cash Filter", "FAIL", f"Failed to get cash transactions: {response.status_code}")
        except Exception as e:
            self.log_result("Cash Filter", "ERROR", f"Error: {str(e)}")
        
        # Test account_type=bank filter
        try:
            response = self.session.get(f"{BASE_URL}/transactions?account_type=bank")
            if response.status_code == 200:
                data = response.json()
                transactions = data['items']
                
                # Verify all transactions are from bank accounts
                bank_only = all(txn.get('account_type') == 'bank' for txn in transactions)
                if bank_only:
                    self.log_result("Bank Filter", "PASS", f"All {len(transactions)} transactions are from bank accounts")
                else:
                    non_bank = [txn for txn in transactions if txn.get('account_type') != 'bank']
                    self.log_result("Bank Filter", "FAIL", f"Found {len(non_bank)} non-bank transactions in bank filter")
            else:
                self.log_result("Bank Filter", "FAIL", f"Failed to get bank transactions: {response.status_code}")
        except Exception as e:
            self.log_result("Bank Filter", "ERROR", f"Error: {str(e)}")
        
        # Test transaction_type=credit filter
        try:
            response = self.session.get(f"{BASE_URL}/transactions?transaction_type=credit")
            if response.status_code == 200:
                data = response.json()
                transactions = data['items']
                
                # Verify all transactions are credit
                credit_only = all(txn.get('transaction_type') == 'credit' for txn in transactions)
                if credit_only:
                    self.log_result("Credit Filter", "PASS", f"All {len(transactions)} transactions are credit type")
                else:
                    non_credit = [txn for txn in transactions if txn.get('transaction_type') != 'credit']
                    self.log_result("Credit Filter", "FAIL", f"Found {len(non_credit)} non-credit transactions in credit filter")
            else:
                self.log_result("Credit Filter", "FAIL", f"Failed to get credit transactions: {response.status_code}")
        except Exception as e:
            self.log_result("Credit Filter", "ERROR", f"Error: {str(e)}")
        
        # Test transaction_type=debit filter
        try:
            response = self.session.get(f"{BASE_URL}/transactions?transaction_type=debit")
            if response.status_code == 200:
                data = response.json()
                transactions = data['items']
                
                # Verify all transactions are debit
                debit_only = all(txn.get('transaction_type') == 'debit' for txn in transactions)
                if debit_only:
                    self.log_result("Debit Filter", "PASS", f"All {len(transactions)} transactions are debit type")
                else:
                    non_debit = [txn for txn in transactions if txn.get('transaction_type') != 'debit']
                    self.log_result("Debit Filter", "FAIL", f"Found {len(non_debit)} non-debit transactions in debit filter")
            else:
                self.log_result("Debit Filter", "FAIL", f"Failed to get debit transactions: {response.status_code}")
        except Exception as e:
            self.log_result("Debit Filter", "ERROR", f"Error: {str(e)}")
        
        # Test reference_type filters
        reference_types = [
            ("invoice", "Invoice Payment"),
            ("purchase", "Purchase Payment"),
            ("manual", "Manual Entry")
        ]
        
        for ref_type, expected_source in reference_types:
            try:
                response = self.session.get(f"{BASE_URL}/transactions?reference_type={ref_type}")
                if response.status_code == 200:
                    data = response.json()
                    transactions = data['items']
                    
                    if ref_type == "manual":
                        # Manual should have reference_type=None
                        manual_only = all(txn.get('reference_type') is None for txn in transactions)
                        source_correct = all(txn.get('transaction_source') == expected_source for txn in transactions)
                    else:
                        # Invoice/Purchase should have reference_type set
                        ref_correct = all(txn.get('reference_type') == ref_type for txn in transactions)
                        source_correct = all(txn.get('transaction_source') == expected_source for txn in transactions)
                        manual_only = ref_correct
                    
                    if manual_only and source_correct:
                        self.log_result(f"{ref_type.title()} Reference Filter", "PASS", f"All {len(transactions)} transactions have correct reference_type and transaction_source='{expected_source}'")
                    else:
                        self.log_result(f"{ref_type.title()} Reference Filter", "FAIL", f"Reference type or transaction source mismatch")
                else:
                    self.log_result(f"{ref_type.title()} Reference Filter", "FAIL", f"Failed to get {ref_type} transactions: {response.status_code}")
            except Exception as e:
                self.log_result(f"{ref_type.title()} Reference Filter", "ERROR", f"Error: {str(e)}")
    
    def test_date_range_filters(self):
        """Test date range filtering"""
        print("\n" + "="*80)
        print("PART 3: DATE RANGE FILTER TESTING")
        print("="*80)
        
        # Test date range filter
        try:
            start_date = "2025-01-01T00:00:00Z"
            end_date = "2025-01-31T23:59:59Z"
            
            response = self.session.get(f"{BASE_URL}/transactions?start_date={start_date}&end_date={end_date}")
            if response.status_code == 200:
                data = response.json()
                transactions = data['items']
                
                # Verify all transactions are within date range
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                
                date_violations = []
                for txn in transactions:
                    txn_date = datetime.fromisoformat(txn['date'].replace('Z', '+00:00'))
                    if not (start_dt <= txn_date <= end_dt):
                        date_violations.append(txn)
                
                if not date_violations:
                    self.log_result("Date Range Filter", "PASS", f"All {len(transactions)} transactions are within date range")
                else:
                    self.log_result("Date Range Filter", "FAIL", f"Found {len(date_violations)} transactions outside date range")
            else:
                self.log_result("Date Range Filter", "FAIL", f"Failed to get transactions with date range: {response.status_code}")
        except Exception as e:
            self.log_result("Date Range Filter", "ERROR", f"Error: {str(e)}")
        
        # Test start_date only
        try:
            start_date = "2025-01-15T00:00:00Z"
            
            response = self.session.get(f"{BASE_URL}/transactions?start_date={start_date}")
            if response.status_code == 200:
                data = response.json()
                transactions = data['items']
                
                # Verify all transactions are from start date onwards
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                
                early_violations = []
                for txn in transactions:
                    txn_date = datetime.fromisoformat(txn['date'].replace('Z', '+00:00'))
                    if txn_date < start_dt:
                        early_violations.append(txn)
                
                if not early_violations:
                    self.log_result("Start Date Only Filter", "PASS", f"All {len(transactions)} transactions are from start date onwards")
                else:
                    self.log_result("Start Date Only Filter", "FAIL", f"Found {len(early_violations)} transactions before start date")
            else:
                self.log_result("Start Date Only Filter", "FAIL", f"Failed to get transactions with start date: {response.status_code}")
        except Exception as e:
            self.log_result("Start Date Only Filter", "ERROR", f"Error: {str(e)}")
        
        # Test end_date only
        try:
            end_date = "2025-01-15T23:59:59Z"
            
            response = self.session.get(f"{BASE_URL}/transactions?end_date={end_date}")
            if response.status_code == 200:
                data = response.json()
                transactions = data['items']
                
                # Verify all transactions are up to end date
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                
                late_violations = []
                for txn in transactions:
                    txn_date = datetime.fromisoformat(txn['date'].replace('Z', '+00:00'))
                    if txn_date > end_dt:
                        late_violations.append(txn)
                
                if not late_violations:
                    self.log_result("End Date Only Filter", "PASS", f"All {len(transactions)} transactions are up to end date")
                else:
                    self.log_result("End Date Only Filter", "FAIL", f"Found {len(late_violations)} transactions after end date")
            else:
                self.log_result("End Date Only Filter", "FAIL", f"Failed to get transactions with end date: {response.status_code}")
        except Exception as e:
            self.log_result("End Date Only Filter", "ERROR", f"Error: {str(e)}")
    
    def test_combined_filters(self):
        """Test combined filters"""
        print("\n" + "="*80)
        print("PART 4: COMBINED FILTER TESTING")
        print("="*80)
        
        # Test cash + credit combination
        try:
            response = self.session.get(f"{BASE_URL}/transactions?account_type=cash&transaction_type=credit")
            if response.status_code == 200:
                data = response.json()
                transactions = data['items']
                
                # Verify all are cash credits
                valid_transactions = all(
                    txn.get('account_type') in ['cash', 'petty'] and txn.get('transaction_type') == 'credit'
                    for txn in transactions
                )
                
                if valid_transactions:
                    self.log_result("Cash + Credit Filter", "PASS", f"All {len(transactions)} transactions are cash account credits")
                else:
                    self.log_result("Cash + Credit Filter", "FAIL", "Found transactions that don't match cash + credit criteria")
            else:
                self.log_result("Cash + Credit Filter", "FAIL", f"Failed to get cash credit transactions: {response.status_code}")
        except Exception as e:
            self.log_result("Cash + Credit Filter", "ERROR", f"Error: {str(e)}")
        
        # Test bank + debit combination
        try:
            response = self.session.get(f"{BASE_URL}/transactions?account_type=bank&transaction_type=debit")
            if response.status_code == 200:
                data = response.json()
                transactions = data['items']
                
                # Verify all are bank debits
                valid_transactions = all(
                    txn.get('account_type') == 'bank' and txn.get('transaction_type') == 'debit'
                    for txn in transactions
                )
                
                if valid_transactions:
                    self.log_result("Bank + Debit Filter", "PASS", f"All {len(transactions)} transactions are bank account debits")
                else:
                    self.log_result("Bank + Debit Filter", "FAIL", "Found transactions that don't match bank + debit criteria")
            else:
                self.log_result("Bank + Debit Filter", "FAIL", f"Failed to get bank debit transactions: {response.status_code}")
        except Exception as e:
            self.log_result("Bank + Debit Filter", "ERROR", f"Error: {str(e)}")
        
        # Test invoice + credit combination
        try:
            response = self.session.get(f"{BASE_URL}/transactions?reference_type=invoice&transaction_type=credit")
            if response.status_code == 200:
                data = response.json()
                transactions = data['items']
                
                # Verify all are invoice payment credits
                valid_transactions = all(
                    txn.get('reference_type') == 'invoice' and 
                    txn.get('transaction_type') == 'credit' and
                    txn.get('transaction_source') == 'Invoice Payment'
                    for txn in transactions
                )
                
                if valid_transactions:
                    self.log_result("Invoice + Credit Filter", "PASS", f"All {len(transactions)} transactions are invoice payment credits")
                else:
                    self.log_result("Invoice + Credit Filter", "FAIL", "Found transactions that don't match invoice + credit criteria")
            else:
                self.log_result("Invoice + Credit Filter", "FAIL", f"Failed to get invoice credit transactions: {response.status_code}")
        except Exception as e:
            self.log_result("Invoice + Credit Filter", "ERROR", f"Error: {str(e)}")
    
    def test_running_balance_validation(self):
        """Test running balance calculation accuracy"""
        print("\n" + "="*80)
        print("PART 5: RUNNING BALANCE VALIDATION")
        print("="*80)
        
        try:
            # Get transactions for a specific account
            if not self.test_cash_account_id:
                self.log_result("Running Balance Test", "FAIL", "No test cash account available")
                return
            
            response = self.session.get(f"{BASE_URL}/transactions?account_id={self.test_cash_account_id}&per_page=100")
            if response.status_code != 200:
                self.log_result("Running Balance Test", "FAIL", f"Failed to get account transactions: {response.status_code}")
                return
            
            data = response.json()
            transactions = data['items']
            
            if not transactions:
                self.log_result("Running Balance Test", "PASS", "No transactions found for balance validation")
                return
            
            # Verify balance calculations
            balance_errors = []
            for txn in transactions:
                balance_before = txn.get('balance_before', 0)
                balance_after = txn.get('balance_after', 0)
                amount = txn.get('amount', 0)
                txn_type = txn.get('transaction_type')
                
                # Calculate expected balance_after
                if txn_type == 'credit':
                    expected_after = balance_before + amount
                else:  # debit
                    expected_after = balance_before - amount
                
                # Check if calculation is correct (within 0.001 tolerance)
                if abs(balance_after - expected_after) > 0.001:
                    balance_errors.append({
                        'transaction_id': txn.get('id'),
                        'type': txn_type,
                        'amount': amount,
                        'balance_before': balance_before,
                        'balance_after': balance_after,
                        'expected_after': expected_after,
                        'difference': balance_after - expected_after
                    })
            
            if not balance_errors:
                self.log_result("Running Balance Calculation", "PASS", f"All {len(transactions)} transactions have correct balance calculations")
            else:
                self.log_result("Running Balance Calculation", "FAIL", f"Found {len(balance_errors)} transactions with incorrect balance calculations")
                for error in balance_errors[:3]:  # Show first 3 errors
                    print(f"   Error: {error['type']} {error['amount']} - Before: {error['balance_before']}, After: {error['balance_after']}, Expected: {error['expected_after']}")
            
            # Verify balance precision (3 decimals)
            precision_errors = []
            for txn in transactions:
                balance_before = txn.get('balance_before', 0)
                balance_after = txn.get('balance_after', 0)
                
                # Check if values are rounded to 3 decimals
                if (round(balance_before, 3) != balance_before or 
                    round(balance_after, 3) != balance_after):
                    precision_errors.append(txn.get('id'))
            
            if not precision_errors:
                self.log_result("Balance Precision", "PASS", "All balance values are rounded to 3 decimals")
            else:
                self.log_result("Balance Precision", "FAIL", f"Found {len(precision_errors)} transactions with incorrect precision")
            
        except Exception as e:
            self.log_result("Running Balance Validation", "ERROR", f"Error: {str(e)}")
    
    def test_transactions_summary_basic(self):
        """Test basic transaction summary endpoint"""
        print("\n" + "="*80)
        print("PART 6: TRANSACTION SUMMARY BASIC TESTING")
        print("="*80)
        
        try:
            response = self.session.get(f"{BASE_URL}/transactions/summary")
            if response.status_code != 200:
                self.log_result("Summary Endpoint", "FAIL", f"Failed to get transaction summary: {response.status_code}")
                return
            
            data = response.json()
            
            # Verify required fields
            required_fields = ['total_credit', 'total_debit', 'net_flow', 'transaction_count', 
                             'cash_summary', 'bank_summary', 'account_breakdown']
            
            for field in required_fields:
                if field not in data:
                    self.log_result("Summary Structure", "FAIL", f"Missing field: {field}")
                    return
            
            self.log_result("Summary Structure", "PASS", "All required fields present in summary")
            
            # Verify cash_summary structure
            cash_summary = data['cash_summary']
            cash_fields = ['credit', 'debit', 'net']
            for field in cash_fields:
                if field not in cash_summary:
                    self.log_result("Cash Summary Structure", "FAIL", f"Missing cash summary field: {field}")
                    return
            
            # Verify bank_summary structure
            bank_summary = data['bank_summary']
            bank_fields = ['credit', 'debit', 'net']
            for field in bank_fields:
                if field not in bank_summary:
                    self.log_result("Bank Summary Structure", "FAIL", f"Missing bank summary field: {field}")
                    return
            
            self.log_result("Summary Subsections", "PASS", "Cash and bank summary structures are correct")
            
            # Verify account_breakdown structure
            account_breakdown = data['account_breakdown']
            if account_breakdown:
                account = account_breakdown[0]
                account_fields = ['account_id', 'account_name', 'account_type', 'credit', 'debit', 'net']
                for field in account_fields:
                    if field not in account:
                        self.log_result("Account Breakdown Structure", "FAIL", f"Missing account breakdown field: {field}")
                        return
            
            self.log_result("Account Breakdown Structure", "PASS", "Account breakdown structure is correct")
            
            # Verify calculations
            total_credit = data['total_credit']
            total_debit = data['total_debit']
            net_flow = data['net_flow']
            
            expected_net = total_credit - total_debit
            if abs(net_flow - expected_net) < 0.001:
                self.log_result("Net Flow Calculation", "PASS", f"Net flow calculation correct: {net_flow} = {total_credit} - {total_debit}")
            else:
                self.log_result("Net Flow Calculation", "FAIL", f"Net flow incorrect: {net_flow}, expected {expected_net}")
            
            # Verify cash summary calculations
            cash_net = cash_summary['net']
            expected_cash_net = cash_summary['credit'] - cash_summary['debit']
            if abs(cash_net - expected_cash_net) < 0.001:
                self.log_result("Cash Net Calculation", "PASS", f"Cash net calculation correct: {cash_net}")
            else:
                self.log_result("Cash Net Calculation", "FAIL", f"Cash net incorrect: {cash_net}, expected {expected_cash_net}")
            
            # Verify bank summary calculations
            bank_net = bank_summary['net']
            expected_bank_net = bank_summary['credit'] - bank_summary['debit']
            if abs(bank_net - expected_bank_net) < 0.001:
                self.log_result("Bank Net Calculation", "PASS", f"Bank net calculation correct: {bank_net}")
            else:
                self.log_result("Bank Net Calculation", "FAIL", f"Bank net incorrect: {bank_net}, expected {expected_bank_net}")
            
        except Exception as e:
            self.log_result("Transaction Summary Basic", "ERROR", f"Error: {str(e)}")
    
    def test_summary_with_date_filter(self):
        """Test transaction summary with date filter"""
        print("\n" + "="*80)
        print("PART 7: SUMMARY WITH DATE FILTER")
        print("="*80)
        
        try:
            start_date = "2025-01-01T00:00:00Z"
            end_date = "2025-01-31T23:59:59Z"
            
            response = self.session.get(f"{BASE_URL}/transactions/summary?start_date={start_date}&end_date={end_date}")
            if response.status_code != 200:
                self.log_result("Summary Date Filter", "FAIL", f"Failed to get summary with date filter: {response.status_code}")
                return
            
            data = response.json()
            
            # Verify structure is same as basic summary
            required_fields = ['total_credit', 'total_debit', 'net_flow', 'transaction_count', 
                             'cash_summary', 'bank_summary', 'account_breakdown']
            
            for field in required_fields:
                if field not in data:
                    self.log_result("Summary Date Filter Structure", "FAIL", f"Missing field: {field}")
                    return
            
            self.log_result("Summary Date Filter Structure", "PASS", "Date filtered summary has correct structure")
            
            # Verify calculations are still correct
            total_credit = data['total_credit']
            total_debit = data['total_debit']
            net_flow = data['net_flow']
            
            expected_net = total_credit - total_debit
            if abs(net_flow - expected_net) < 0.001:
                self.log_result("Date Filtered Net Calculation", "PASS", f"Date filtered net flow calculation correct: {net_flow}")
            else:
                self.log_result("Date Filtered Net Calculation", "FAIL", f"Date filtered net flow incorrect: {net_flow}, expected {expected_net}")
            
        except Exception as e:
            self.log_result("Summary Date Filter", "ERROR", f"Error: {str(e)}")
    
    def test_account_breakdown_validation(self):
        """Test account breakdown validation in summary"""
        print("\n" + "="*80)
        print("PART 8: ACCOUNT BREAKDOWN VALIDATION")
        print("="*80)
        
        try:
            response = self.session.get(f"{BASE_URL}/transactions/summary")
            if response.status_code != 200:
                self.log_result("Account Breakdown Test", "FAIL", f"Failed to get summary: {response.status_code}")
                return
            
            data = response.json()
            account_breakdown = data['account_breakdown']
            
            # Verify each account breakdown
            breakdown_errors = []
            precision_errors = []
            
            for account in account_breakdown:
                credit = account.get('credit', 0)
                debit = account.get('debit', 0)
                net = account.get('net', 0)
                
                # Verify net calculation
                expected_net = credit - debit
                if abs(net - expected_net) > 0.001:
                    breakdown_errors.append({
                        'account_name': account.get('account_name'),
                        'credit': credit,
                        'debit': debit,
                        'net': net,
                        'expected_net': expected_net
                    })
                
                # Verify precision (3 decimals)
                if (round(credit, 3) != credit or 
                    round(debit, 3) != debit or 
                    round(net, 3) != net):
                    precision_errors.append(account.get('account_name'))
            
            if not breakdown_errors:
                self.log_result("Account Net Calculations", "PASS", f"All {len(account_breakdown)} accounts have correct net calculations")
            else:
                self.log_result("Account Net Calculations", "FAIL", f"Found {len(breakdown_errors)} accounts with incorrect net calculations")
            
            if not precision_errors:
                self.log_result("Account Breakdown Precision", "PASS", "All account breakdown values are rounded to 3 decimals")
            else:
                self.log_result("Account Breakdown Precision", "FAIL", f"Found {len(precision_errors)} accounts with incorrect precision")
            
        except Exception as e:
            self.log_result("Account Breakdown Validation", "ERROR", f"Error: {str(e)}")
    
    def test_manual_transaction_flow(self):
        """Test end-to-end manual transaction creation flow"""
        print("\n" + "="*80)
        print("PART 9: MANUAL TRANSACTION CREATION FLOW")
        print("="*80)
        
        if not self.test_cash_account_id:
            self.log_result("Manual Transaction Flow", "FAIL", "No test cash account available")
            return
        
        try:
            # Get initial account balance
            response = self.session.get(f"{BASE_URL}/accounts")
            if response.status_code != 200:
                self.log_result("Get Initial Balance", "FAIL", f"Failed to get accounts: {response.status_code}")
                return
            
            accounts = response.json()
            test_account = next((acc for acc in accounts if acc['id'] == self.test_cash_account_id), None)
            if not test_account:
                self.log_result("Find Test Account", "FAIL", "Test cash account not found")
                return
            
            initial_balance = test_account['current_balance']
            self.log_result("Initial Balance Check", "PASS", f"Initial balance: {initial_balance} OMR")
            
            # Create CREDIT transaction
            credit_amount = 500.0
            credit_data = {
                "transaction_type": "credit",
                "mode": "cash",
                "account_id": self.test_cash_account_id,
                "amount": credit_amount,
                "category": "sales",
                "notes": "Test credit transaction"
            }
            
            response = self.session.post(f"{BASE_URL}/transactions", json=credit_data)
            if response.status_code != 200:
                self.log_result("Create Credit Transaction", "FAIL", f"Failed to create credit transaction: {response.status_code} - {response.text}")
                return
            
            credit_txn = response.json()
            self.log_result("Create Credit Transaction", "PASS", f"Created credit transaction: {credit_txn['id']}")
            
            # Verify account balance increased
            response = self.session.get(f"{BASE_URL}/accounts")
            accounts = response.json()
            test_account = next((acc for acc in accounts if acc['id'] == self.test_cash_account_id), None)
            new_balance = test_account['current_balance']
            expected_balance = initial_balance + credit_amount
            
            if abs(new_balance - expected_balance) < 0.01:
                self.log_result("Credit Balance Update", "PASS", f"Balance increased correctly: {new_balance} OMR (expected: {expected_balance})")
            else:
                self.log_result("Credit Balance Update", "FAIL", f"Balance incorrect: {new_balance} OMR, expected: {expected_balance}")
            
            # Verify transaction appears in list with correct balance_before and balance_after
            response = self.session.get(f"{BASE_URL}/transactions?account_id={self.test_cash_account_id}&per_page=1")
            if response.status_code == 200:
                data = response.json()
                transactions = data['items']
                if transactions:
                    latest_txn = transactions[0]
                    if latest_txn['id'] == credit_txn['id']:
                        balance_before = latest_txn.get('balance_before', 0)
                        balance_after = latest_txn.get('balance_after', 0)
                        
                        if (abs(balance_before - initial_balance) < 0.01 and 
                            abs(balance_after - expected_balance) < 0.01):
                            self.log_result("Credit Running Balance", "PASS", f"Running balance correct: before={balance_before}, after={balance_after}")
                        else:
                            self.log_result("Credit Running Balance", "FAIL", f"Running balance incorrect: before={balance_before}, after={balance_after}")
                    else:
                        self.log_result("Credit Transaction Retrieval", "FAIL", "Latest transaction ID doesn't match created transaction")
                else:
                    self.log_result("Credit Transaction Retrieval", "FAIL", "No transactions found after creation")
            
            # Create DEBIT transaction
            debit_amount = 200.0
            debit_data = {
                "transaction_type": "debit",
                "mode": "cash",
                "account_id": self.test_cash_account_id,
                "amount": debit_amount,
                "category": "expense",
                "notes": "Test debit transaction"
            }
            
            response = self.session.post(f"{BASE_URL}/transactions", json=debit_data)
            if response.status_code != 200:
                self.log_result("Create Debit Transaction", "FAIL", f"Failed to create debit transaction: {response.status_code} - {response.text}")
                return
            
            debit_txn = response.json()
            self.log_result("Create Debit Transaction", "PASS", f"Created debit transaction: {debit_txn['id']}")
            
            # Verify account balance decreased
            response = self.session.get(f"{BASE_URL}/accounts")
            accounts = response.json()
            test_account = next((acc for acc in accounts if acc['id'] == self.test_cash_account_id), None)
            final_balance = test_account['current_balance']
            expected_final = expected_balance - debit_amount
            
            if abs(final_balance - expected_final) < 0.01:
                self.log_result("Debit Balance Update", "PASS", f"Balance decreased correctly: {final_balance} OMR (expected: {expected_final})")
            else:
                self.log_result("Debit Balance Update", "FAIL", f"Balance incorrect: {final_balance} OMR, expected: {expected_final}")
            
            # Verify running balance in transaction list
            response = self.session.get(f"{BASE_URL}/transactions?account_id={self.test_cash_account_id}&per_page=1")
            if response.status_code == 200:
                data = response.json()
                transactions = data['items']
                if transactions:
                    latest_txn = transactions[0]
                    if latest_txn['id'] == debit_txn['id']:
                        balance_before = latest_txn.get('balance_before', 0)
                        balance_after = latest_txn.get('balance_after', 0)
                        
                        if (abs(balance_before - expected_balance) < 0.01 and 
                            abs(balance_after - expected_final) < 0.01):
                            self.log_result("Debit Running Balance", "PASS", f"Running balance correct: before={balance_before}, after={balance_after}")
                        else:
                            self.log_result("Debit Running Balance", "FAIL", f"Running balance incorrect: before={balance_before}, after={balance_after}")
            
        except Exception as e:
            self.log_result("Manual Transaction Flow", "ERROR", f"Error: {str(e)}")
    
    def test_balance_consistency_check(self):
        """Test balance consistency across endpoints"""
        print("\n" + "="*80)
        print("PART 12: BALANCE CONSISTENCY CHECK")
        print("="*80)
        
        if not self.test_cash_account_id:
            self.log_result("Balance Consistency", "FAIL", "No test cash account available")
            return
        
        try:
            # Get current balance from accounts endpoint
            response = self.session.get(f"{BASE_URL}/accounts")
            if response.status_code != 200:
                self.log_result("Get Account Balance", "FAIL", f"Failed to get accounts: {response.status_code}")
                return
            
            accounts = response.json()
            test_account = next((acc for acc in accounts if acc['id'] == self.test_cash_account_id), None)
            if not test_account:
                self.log_result("Find Test Account", "FAIL", "Test account not found")
                return
            
            current_balance = test_account['current_balance']
            opening_balance = test_account['opening_balance']
            
            # Get all transactions for this account
            response = self.session.get(f"{BASE_URL}/transactions?account_id={self.test_cash_account_id}&per_page=1000")
            if response.status_code != 200:
                self.log_result("Get Account Transactions", "FAIL", f"Failed to get transactions: {response.status_code}")
                return
            
            data = response.json()
            transactions = data['items']
            
            # Calculate expected balance
            calculated_balance = opening_balance
            total_credits = 0
            total_debits = 0
            
            for txn in transactions:
                amount = txn.get('amount', 0)
                if txn.get('transaction_type') == 'credit':
                    calculated_balance += amount
                    total_credits += amount
                else:
                    calculated_balance -= amount
                    total_debits += amount
            
            # Check if calculated balance matches current balance
            if abs(calculated_balance - current_balance) < 0.001:
                self.log_result("Balance Consistency", "PASS", f"Balance consistent: {current_balance} OMR (calculated: {calculated_balance})")
            else:
                self.log_result("Balance Consistency", "FAIL", f"Balance inconsistent: current={current_balance}, calculated={calculated_balance}")
            
            self.log_result("Balance Calculation Details", "PASS", f"Opening: {opening_balance}, Credits: {total_credits}, Debits: {total_debits}, Final: {calculated_balance}")
            
        except Exception as e:
            self.log_result("Balance Consistency Check", "ERROR", f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all comprehensive transaction tests"""
        print("STARTING COMPREHENSIVE MODULE 6 — TRANSACTIONS & MONEY FLOW BACKEND TESTING")
        print("Backend URL:", BASE_URL)
        print("Authentication:", f"{USERNAME}/***")
        print("="*80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Setup test accounts
        if not self.setup_test_accounts():
            print("❌ Account setup failed. Cannot proceed with tests.")
            return False
        
        # Run all test parts
        self.test_basic_transaction_retrieval()
        self.test_individual_filters()
        self.test_date_range_filters()
        self.test_combined_filters()
        self.test_running_balance_validation()
        self.test_transactions_summary_basic()
        self.test_summary_with_date_filter()
        self.test_account_breakdown_validation()
        self.test_manual_transaction_flow()
        self.test_balance_consistency_check()
        
        # Summary
        print("\n" + "="*80)
        print("COMPREHENSIVE TRANSACTION TESTING SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        error_tests = len([r for r in self.test_results if r["status"] == "ERROR"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️ Errors: {error_tests}")
        
        # Critical findings
        print("\nCRITICAL FINDINGS:")
        critical_failures = []
        for result in self.test_results:
            if result["status"] == "FAIL" and any(keyword in result["test"] for keyword in 
                ["Balance", "Filter", "Summary", "Calculation", "Structure"]):
                critical_failures.append(result)
        
        if critical_failures:
            print("🚨 CRITICAL ISSUES DETECTED:")
            for failure in critical_failures:
                print(f"   ❌ {failure['test']}: {failure['details']}")
        else:
            print("✅ All critical transaction and money flow features are working correctly")
            print("✅ Enhanced filtering system operational")
            print("✅ Running balance calculations accurate")
            print("✅ Transaction summary endpoint functional")
            print("✅ Account type enrichment working")
            print("✅ Transaction source enrichment working")
        
        return failed_tests == 0 and error_tests == 0

if __name__ == "__main__":
    tester = TransactionsComprehensiveTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
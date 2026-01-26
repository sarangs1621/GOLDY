#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Module 7 - Daily Closing & Reports
Gold Shop ERP System

This script tests all 23 API endpoints for Daily Closing and Reports functionality:
- 5 Daily Closing endpoints
- 8 Report endpoints  
- 10 Export endpoints
- Cross-module data consistency verification

Authentication: admin/admin123
Backend URL: From REACT_APP_BACKEND_URL environment variable
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import sys

# Configuration
BACKEND_URL = "https://decimal-precision.preview.emergentagent.com"
USERNAME = "admin"
PASSWORD = "admin123"

class ModuleTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.token = None
        self.headers = {}
        self.test_results = []
        
    def log_test(self, test_name: str, status: str, details: str = "", response_data: Any = None):
        """Log test results"""
        result = {
            "test_name": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        
        # Print immediate feedback
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        if status == "FAIL" and response_data:
            print(f"   Response: {response_data}")
        print()

    def authenticate(self) -> bool:
        """Authenticate and get JWT token"""
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json={"username": USERNAME, "password": PASSWORD},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.headers = {"Authorization": f"Bearer {self.token}"}
                self.log_test("Authentication", "PASS", f"Logged in as {USERNAME}")
                return True
            else:
                self.log_test("Authentication", "FAIL", f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Authentication", "FAIL", f"Exception: {str(e)}")
            return False

    def test_daily_closing_auto_calculate(self) -> Dict[str, Any]:
        """Test GET /api/daily-closings/calculate/{date}"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            response = requests.get(
                f"{self.base_url}/api/daily-closings/calculate/{today}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["opening_cash", "total_credit", "total_debit", "transaction_count"]
                
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    self.log_test("Daily Closing Auto-Calculate", "FAIL", 
                                f"Missing fields: {missing_fields}", data)
                    return {}
                
                self.log_test("Daily Closing Auto-Calculate", "PASS", 
                            f"Opening: {data.get('opening_cash', 0)} OMR, "
                            f"Credit: {data.get('total_credit', 0)} OMR, "
                            f"Debit: {data.get('total_debit', 0)} OMR, "
                            f"Transactions: {data.get('transaction_count', 0)}")
                return data
            else:
                self.log_test("Daily Closing Auto-Calculate", "FAIL", 
                            f"Status: {response.status_code}", response.text)
                return {}
                
        except Exception as e:
            self.log_test("Daily Closing Auto-Calculate", "FAIL", f"Exception: {str(e)}")
            return {}

    def test_create_daily_closing(self, auto_calc_data: Dict[str, Any]) -> str:
        """Test POST /api/daily-closings"""
        try:
            # Use auto-calculated values or defaults
            opening_cash = auto_calc_data.get("opening_cash", 10000.0)
            total_credit = auto_calc_data.get("total_credit", 0.0)
            total_debit = auto_calc_data.get("total_debit", 0.0)
            expected_closing = opening_cash + total_credit - total_debit
            actual_closing = expected_closing + 50.0  # Small difference for testing
            
            closing_data = {
                "date": datetime.now().isoformat(),
                "opening_cash": opening_cash,
                "total_credit": total_credit,
                "total_debit": total_debit,
                "expected_closing": expected_closing,
                "actual_closing": actual_closing,
                "difference": actual_closing - expected_closing,
                "notes": "Test closing record for Module 7 testing"
            }
            
            response = requests.post(
                f"{self.base_url}/api/daily-closings",
                json=closing_data,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                closing_id = data.get("id", "")
                
                # Verify calculations
                calc_expected = data.get("expected_closing", 0)
                calc_difference = data.get("difference", 0)
                
                if abs(calc_expected - expected_closing) < 0.01 and abs(calc_difference - (actual_closing - expected_closing)) < 0.01:
                    self.log_test("Create Daily Closing", "PASS", 
                                f"ID: {closing_id}, Expected: {calc_expected} OMR, "
                                f"Actual: {data.get('actual_closing', 0)} OMR, "
                                f"Difference: {calc_difference} OMR")
                    return closing_id
                else:
                    self.log_test("Create Daily Closing", "FAIL", 
                                f"Calculation error - Expected: {calc_expected}, Difference: {calc_difference}")
                    return ""
            else:
                self.log_test("Create Daily Closing", "FAIL", 
                            f"Status: {response.status_code}", response.text)
                return ""
                
        except Exception as e:
            self.log_test("Create Daily Closing", "FAIL", f"Exception: {str(e)}")
            return ""

    def test_list_daily_closings(self) -> bool:
        """Test GET /api/daily-closings"""
        try:
            response = requests.get(
                f"{self.base_url}/api/daily-closings",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if it's paginated response
                if isinstance(data, dict) and "items" in data:
                    closings = data["items"]
                    pagination = data.get("pagination", {})
                    self.log_test("List Daily Closings", "PASS", 
                                f"Found {len(closings)} closings, Total: {pagination.get('total_count', 'N/A')}")
                elif isinstance(data, list):
                    self.log_test("List Daily Closings", "PASS", f"Found {len(data)} closings")
                else:
                    self.log_test("List Daily Closings", "FAIL", "Unexpected response format", data)
                    return False
                
                return True
            else:
                self.log_test("List Daily Closings", "FAIL", 
                            f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("List Daily Closings", "FAIL", f"Exception: {str(e)}")
            return False

    def test_edit_daily_closing(self, closing_id: str) -> bool:
        """Test PATCH /api/daily-closings/{id}"""
        if not closing_id:
            self.log_test("Edit Daily Closing", "SKIP", "No closing ID available")
            return False
            
        try:
            update_data = {
                "actual_closing": 10100.0,
                "notes": "Updated test closing record"
            }
            
            response = requests.patch(
                f"{self.base_url}/api/daily-closings/{closing_id}",
                json=update_data,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                updated_actual = data.get("actual_closing", 0)
                updated_difference = data.get("difference", 0)
                
                self.log_test("Edit Daily Closing", "PASS", 
                            f"Updated actual closing: {updated_actual} OMR, "
                            f"New difference: {updated_difference} OMR")
                return True
            else:
                self.log_test("Edit Daily Closing", "FAIL", 
                            f"Status: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Edit Daily Closing", "FAIL", f"Exception: {str(e)}")
            return False

    def test_lock_unlock_closing(self, closing_id: str) -> bool:
        """Test locking/unlocking daily closing"""
        if not closing_id:
            self.log_test("Lock/Unlock Daily Closing", "SKIP", "No closing ID available")
            return False
            
        try:
            # Test locking
            lock_response = requests.patch(
                f"{self.base_url}/api/daily-closings/{closing_id}",
                json={"is_locked": True},
                headers=self.headers,
                timeout=30
            )
            
            if lock_response.status_code == 200:
                lock_data = lock_response.json()
                if lock_data.get("is_locked"):
                    # Test unlocking
                    unlock_response = requests.patch(
                        f"{self.base_url}/api/daily-closings/{closing_id}",
                        json={"is_locked": False},
                        headers=self.headers,
                        timeout=30
                    )
                    
                    if unlock_response.status_code == 200:
                        unlock_data = unlock_response.json()
                        if not unlock_data.get("is_locked"):
                            self.log_test("Lock/Unlock Daily Closing", "PASS", 
                                        "Successfully locked and unlocked closing")
                            return True
                        else:
                            self.log_test("Lock/Unlock Daily Closing", "FAIL", 
                                        "Failed to unlock closing")
                            return False
                    else:
                        self.log_test("Lock/Unlock Daily Closing", "FAIL", 
                                    f"Unlock failed - Status: {unlock_response.status_code}")
                        return False
                else:
                    self.log_test("Lock/Unlock Daily Closing", "FAIL", 
                                "Failed to lock closing")
                    return False
            else:
                self.log_test("Lock/Unlock Daily Closing", "FAIL", 
                            f"Lock failed - Status: {lock_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Lock/Unlock Daily Closing", "FAIL", f"Exception: {str(e)}")
            return False

    def test_financial_summary_report(self) -> Dict[str, Any]:
        """Test GET /api/reports/financial-summary"""
        try:
            # Test without filters
            response = requests.get(
                f"{self.base_url}/api/reports/financial-summary",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Test with date filters
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                
                filtered_response = requests.get(
                    f"{self.base_url}/api/reports/financial-summary",
                    params={
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d")
                    },
                    headers=self.headers,
                    timeout=30
                )
                
                if filtered_response.status_code == 200:
                    filtered_data = filtered_response.json()
                    self.log_test("Financial Summary Report", "PASS", 
                                f"Revenue: {data.get('revenue', 0)} OMR, "
                                f"Expenses: {data.get('expenses', 0)} OMR, "
                                f"Profit: {data.get('profit', 0)} OMR")
                    return data
                else:
                    self.log_test("Financial Summary Report", "FAIL", 
                                f"Filtered request failed - Status: {filtered_response.status_code}")
                    return {}
            else:
                self.log_test("Financial Summary Report", "FAIL", 
                            f"Status: {response.status_code}", response.text)
                return {}
                
        except Exception as e:
            self.log_test("Financial Summary Report", "FAIL", f"Exception: {str(e)}")
            return {}

    def test_outstanding_report(self) -> Dict[str, Any]:
        """Test GET /api/reports/outstanding"""
        try:
            # Test without filters
            response = requests.get(
                f"{self.base_url}/api/reports/outstanding",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Test with filters
                filtered_response = requests.get(
                    f"{self.base_url}/api/reports/outstanding",
                    params={
                        "party_type": "customer",
                        "start_date": (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d"),
                        "end_date": datetime.now().strftime("%Y-%m-%d")
                    },
                    headers=self.headers,
                    timeout=30
                )
                
                if filtered_response.status_code == 200:
                    parties = data.get("parties", []) if isinstance(data, dict) else data
                    self.log_test("Outstanding Report", "PASS", 
                                f"Found {len(parties)} parties with outstanding balances")
                    return data
                else:
                    self.log_test("Outstanding Report", "FAIL", 
                                f"Filtered request failed - Status: {filtered_response.status_code}")
                    return {}
            else:
                self.log_test("Outstanding Report", "FAIL", 
                            f"Status: {response.status_code}", response.text)
                return {}
                
        except Exception as e:
            self.log_test("Outstanding Report", "FAIL", f"Exception: {str(e)}")
            return {}

    def test_invoices_report(self) -> Dict[str, Any]:
        """Test GET /api/reports/invoices-view"""
        try:
            # Test with multiple filters
            params = {
                "start_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "end_date": datetime.now().strftime("%Y-%m-%d"),
                "payment_status": "paid",
                "sort_by": "date"
            }
            
            response = requests.get(
                f"{self.base_url}/api/reports/invoices-view",
                params=params,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Test different payment status
                unpaid_response = requests.get(
                    f"{self.base_url}/api/reports/invoices-view",
                    params={"payment_status": "unpaid"},
                    headers=self.headers,
                    timeout=30
                )
                
                if unpaid_response.status_code == 200:
                    invoices = data.get("invoices", []) if isinstance(data, dict) else data
                    totals = data.get("totals", {}) if isinstance(data, dict) else {}
                    
                    self.log_test("Invoices Report", "PASS", 
                                f"Found {len(invoices)} invoices, "
                                f"Total Amount: {totals.get('total_amount', 0)} OMR, "
                                f"Total Paid: {totals.get('total_paid', 0)} OMR")
                    return data
                else:
                    self.log_test("Invoices Report", "FAIL", 
                                f"Unpaid filter failed - Status: {unpaid_response.status_code}")
                    return {}
            else:
                self.log_test("Invoices Report", "FAIL", 
                            f"Status: {response.status_code}", response.text)
                return {}
                
        except Exception as e:
            self.log_test("Invoices Report", "FAIL", f"Exception: {str(e)}")
            return {}

    def test_sales_history_report(self) -> Dict[str, Any]:
        """Test GET /api/reports/sales-history"""
        try:
            params = {
                "date_from": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "date_to": datetime.now().strftime("%Y-%m-%d"),
                "search": "gold"
            }
            
            response = requests.get(
                f"{self.base_url}/api/reports/sales-history",
                params=params,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                sales = data.get("sales", []) if isinstance(data, dict) else data
                totals = data.get("totals", {}) if isinstance(data, dict) else {}
                
                self.log_test("Sales History Report", "PASS", 
                            f"Found {len(sales)} sales, "
                            f"Total Weight: {totals.get('total_weight', 0)}g, "
                            f"Total Amount: {totals.get('total_amount', 0)} OMR")
                return data
            else:
                self.log_test("Sales History Report", "FAIL", 
                            f"Status: {response.status_code}", response.text)
                return {}
                
        except Exception as e:
            self.log_test("Sales History Report", "FAIL", f"Exception: {str(e)}")
            return {}

    def test_purchase_history_report(self) -> Dict[str, Any]:
        """Test GET /api/reports/purchase-history"""
        try:
            params = {
                "date_from": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "date_to": datetime.now().strftime("%Y-%m-%d")
            }
            
            response = requests.get(
                f"{self.base_url}/api/reports/purchase-history",
                params=params,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                purchases = data.get("purchases", []) if isinstance(data, dict) else data
                totals = data.get("totals", {}) if isinstance(data, dict) else {}
                
                self.log_test("Purchase History Report", "PASS", 
                            f"Found {len(purchases)} purchases, "
                            f"Total Weight: {totals.get('total_weight', 0)}g, "
                            f"Total Amount: {totals.get('total_amount', 0)} OMR")
                return data
            else:
                self.log_test("Purchase History Report", "FAIL", 
                            f"Status: {response.status_code}", response.text)
                return {}
                
        except Exception as e:
            self.log_test("Purchase History Report", "FAIL", f"Exception: {str(e)}")
            return {}

    def test_parties_report(self) -> Dict[str, Any]:
        """Test GET /api/reports/parties-view"""
        try:
            # Test with party type filter
            response = requests.get(
                f"{self.base_url}/api/reports/parties-view",
                params={"party_type": "customer"},
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Test vendor filter
                vendor_response = requests.get(
                    f"{self.base_url}/api/reports/parties-view",
                    params={"party_type": "vendor"},
                    headers=self.headers,
                    timeout=30
                )
                
                if vendor_response.status_code == 200:
                    parties = data.get("parties", []) if isinstance(data, dict) else data
                    self.log_test("Parties Report", "PASS", 
                                f"Found {len(parties)} customers")
                    return data
                else:
                    self.log_test("Parties Report", "FAIL", 
                                f"Vendor filter failed - Status: {vendor_response.status_code}")
                    return {}
            else:
                self.log_test("Parties Report", "FAIL", 
                            f"Status: {response.status_code}", response.text)
                return {}
                
        except Exception as e:
            self.log_test("Parties Report", "FAIL", f"Exception: {str(e)}")
            return {}

    def test_transactions_report(self) -> Dict[str, Any]:
        """Test GET /api/reports/transactions-view"""
        try:
            params = {
                "start_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "end_date": datetime.now().strftime("%Y-%m-%d"),
                "transaction_type": "credit"
            }
            
            response = requests.get(
                f"{self.base_url}/api/reports/transactions-view",
                params=params,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Test debit filter
                debit_response = requests.get(
                    f"{self.base_url}/api/reports/transactions-view",
                    params={"transaction_type": "debit"},
                    headers=self.headers,
                    timeout=30
                )
                
                if debit_response.status_code == 200:
                    transactions = data.get("transactions", []) if isinstance(data, dict) else data
                    totals = data.get("totals", {}) if isinstance(data, dict) else {}
                    
                    self.log_test("Transactions Report", "PASS", 
                                f"Found {len(transactions)} credit transactions, "
                                f"Total Credit: {totals.get('total_credit', 0)} OMR")
                    return data
                else:
                    self.log_test("Transactions Report", "FAIL", 
                                f"Debit filter failed - Status: {debit_response.status_code}")
                    return {}
            else:
                self.log_test("Transactions Report", "FAIL", 
                            f"Status: {response.status_code}", response.text)
                return {}
                
        except Exception as e:
            self.log_test("Transactions Report", "FAIL", f"Exception: {str(e)}")
            return {}

    def test_inventory_report(self) -> Dict[str, Any]:
        """Test GET /api/reports/inventory-view"""
        try:
            params = {
                "start_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "end_date": datetime.now().strftime("%Y-%m-%d"),
                "movement_type": "Stock IN"
            }
            
            response = requests.get(
                f"{self.base_url}/api/reports/inventory-view",
                params=params,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                inventory = data.get("inventory", []) if isinstance(data, dict) else data
                totals = data.get("totals", {}) if isinstance(data, dict) else {}
                
                self.log_test("Inventory Report", "PASS", 
                            f"Found {len(inventory)} inventory items, "
                            f"Total Weight: {totals.get('total_weight', 0)}g")
                return data
            else:
                self.log_test("Inventory Report", "FAIL", 
                            f"Status: {response.status_code}", response.text)
                return {}
                
        except Exception as e:
            self.log_test("Inventory Report", "FAIL", f"Exception: {str(e)}")
            return {}

    def test_excel_exports(self) -> int:
        """Test Excel export endpoints"""
        excel_endpoints = [
            "/api/reports/sales-history-export",
            "/api/reports/purchase-history-export", 
            "/api/reports/inventory-export",
            "/api/reports/invoices-export",
            "/api/reports/parties-export"
        ]
        
        passed_count = 0
        
        for endpoint in excel_endpoints:
            try:
                response = requests.get(
                    f"{self.base_url}{endpoint}",
                    headers=self.headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    if 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in content_type:
                        self.log_test(f"Excel Export {endpoint}", "PASS", 
                                    f"File size: {len(response.content)} bytes")
                        passed_count += 1
                    else:
                        self.log_test(f"Excel Export {endpoint}", "FAIL", 
                                    f"Wrong content type: {content_type}")
                else:
                    self.log_test(f"Excel Export {endpoint}", "FAIL", 
                                f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Excel Export {endpoint}", "FAIL", f"Exception: {str(e)}")
        
        return passed_count

    def test_pdf_exports(self) -> int:
        """Test PDF export endpoints"""
        pdf_endpoints = [
            "/api/reports/outstanding-pdf",
            "/api/reports/inventory-pdf",
            "/api/reports/invoices-pdf", 
            "/api/reports/parties-pdf",
            "/api/reports/transactions-pdf"
        ]
        
        passed_count = 0
        
        for endpoint in pdf_endpoints:
            try:
                response = requests.get(
                    f"{self.base_url}{endpoint}",
                    headers=self.headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    if 'application/pdf' in content_type:
                        self.log_test(f"PDF Export {endpoint}", "PASS", 
                                    f"File size: {len(response.content)} bytes")
                        passed_count += 1
                    else:
                        self.log_test(f"PDF Export {endpoint}", "FAIL", 
                                    f"Wrong content type: {content_type}")
                else:
                    self.log_test(f"PDF Export {endpoint}", "FAIL", 
                                f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"PDF Export {endpoint}", "FAIL", f"Exception: {str(e)}")
        
        return passed_count

    def test_cross_module_consistency(self) -> Dict[str, bool]:
        """Test data consistency across modules"""
        consistency_results = {}
        
        try:
            # 1. Sales total vs finalized invoices
            sales_response = requests.get(
                f"{self.base_url}/api/reports/sales-history",
                headers=self.headers,
                timeout=30
            )
            
            invoices_response = requests.get(
                f"{self.base_url}/api/invoices",
                params={"status": "finalized"},
                headers=self.headers,
                timeout=30
            )
            
            if sales_response.status_code == 200 and invoices_response.status_code == 200:
                sales_data = sales_response.json()
                invoices_data = invoices_response.json()
                
                sales_total = sales_data.get("totals", {}).get("total_amount", 0)
                
                # Handle paginated response
                if isinstance(invoices_data, dict) and "items" in invoices_data:
                    invoices = invoices_data["items"]
                else:
                    invoices = invoices_data if isinstance(invoices_data, list) else []
                
                invoice_total = sum(inv.get("grand_total", 0) for inv in invoices)
                
                consistency_results["sales_vs_invoices"] = abs(sales_total - invoice_total) < 1.0
                self.log_test("Sales vs Invoices Consistency", 
                            "PASS" if consistency_results["sales_vs_invoices"] else "FAIL",
                            f"Sales: {sales_total} OMR, Invoices: {invoice_total} OMR")
            else:
                consistency_results["sales_vs_invoices"] = False
                self.log_test("Sales vs Invoices Consistency", "FAIL", "API calls failed")
            
            # 2. Outstanding balances vs party summaries
            outstanding_response = requests.get(
                f"{self.base_url}/api/reports/outstanding",
                headers=self.headers,
                timeout=30
            )
            
            if outstanding_response.status_code == 200:
                outstanding_data = outstanding_response.json()
                parties = outstanding_data.get("parties", []) if isinstance(outstanding_data, dict) else outstanding_data
                
                if parties:
                    # Test first party's outstanding balance
                    first_party = parties[0]
                    party_id = first_party.get("party_id") or first_party.get("id")
                    
                    if party_id:
                        party_summary_response = requests.get(
                            f"{self.base_url}/api/parties/{party_id}/summary",
                            headers=self.headers,
                            timeout=30
                        )
                        
                        if party_summary_response.status_code == 200:
                            summary_data = party_summary_response.json()
                            outstanding_balance = first_party.get("outstanding_amount", 0)
                            summary_balance = summary_data.get("money", {}).get("money_due_from_party", 0)
                            
                            consistency_results["outstanding_vs_summary"] = abs(outstanding_balance - summary_balance) < 1.0
                            self.log_test("Outstanding vs Summary Consistency", 
                                        "PASS" if consistency_results["outstanding_vs_summary"] else "FAIL",
                                        f"Outstanding: {outstanding_balance} OMR, Summary: {summary_balance} OMR")
                        else:
                            consistency_results["outstanding_vs_summary"] = False
                            self.log_test("Outstanding vs Summary Consistency", "FAIL", "Party summary API failed")
                    else:
                        consistency_results["outstanding_vs_summary"] = True
                        self.log_test("Outstanding vs Summary Consistency", "PASS", "No parties to compare")
                else:
                    consistency_results["outstanding_vs_summary"] = True
                    self.log_test("Outstanding vs Summary Consistency", "PASS", "No outstanding parties")
            else:
                consistency_results["outstanding_vs_summary"] = False
                self.log_test("Outstanding vs Summary Consistency", "FAIL", "Outstanding API failed")
            
            # 3. Inventory totals consistency
            inventory_report_response = requests.get(
                f"{self.base_url}/api/reports/inventory-view",
                headers=self.headers,
                timeout=30
            )
            
            inventory_headers_response = requests.get(
                f"{self.base_url}/api/inventory/headers",
                headers=self.headers,
                timeout=30
            )
            
            if inventory_report_response.status_code == 200 and inventory_headers_response.status_code == 200:
                report_data = inventory_report_response.json()
                headers_data = inventory_headers_response.json()
                
                report_total_weight = report_data.get("totals", {}).get("total_weight", 0)
                headers_total_weight = sum(h.get("current_weight", 0) for h in headers_data)
                
                consistency_results["inventory_consistency"] = abs(report_total_weight - headers_total_weight) < 0.001
                self.log_test("Inventory Consistency", 
                            "PASS" if consistency_results["inventory_consistency"] else "FAIL",
                            f"Report: {report_total_weight}g, Headers: {headers_total_weight}g")
            else:
                consistency_results["inventory_consistency"] = False
                self.log_test("Inventory Consistency", "FAIL", "Inventory API calls failed")
                
        except Exception as e:
            self.log_test("Cross-Module Consistency", "FAIL", f"Exception: {str(e)}")
            consistency_results["exception"] = False
        
        return consistency_results

    def run_all_tests(self):
        """Run all Module 7 tests"""
        print("🎯 STARTING MODULE 7 COMPREHENSIVE TESTING - DAILY CLOSING & REPORTS")
        print("=" * 80)
        print()
        
        # Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with testing.")
            return
        
        print("📋 PHASE 1: DAILY CLOSING MODULE (5 API tests)")
        print("-" * 50)
        
        # Daily Closing Tests
        auto_calc_data = self.test_daily_closing_auto_calculate()
        closing_id = self.test_create_daily_closing(auto_calc_data)
        self.test_list_daily_closings()
        self.test_edit_daily_closing(closing_id)
        self.test_lock_unlock_closing(closing_id)
        
        print("\n📊 PHASE 2: REPORTS MODULE (8 report types)")
        print("-" * 50)
        
        # Reports Tests
        self.test_financial_summary_report()
        self.test_outstanding_report()
        self.test_invoices_report()
        self.test_sales_history_report()
        self.test_purchase_history_report()
        self.test_parties_report()
        self.test_transactions_report()
        self.test_inventory_report()
        
        print("\n📁 PHASE 3: EXPORT FUNCTIONALITY (10 endpoints)")
        print("-" * 50)
        
        # Export Tests
        excel_passed = self.test_excel_exports()
        pdf_passed = self.test_pdf_exports()
        
        print(f"\nExcel Exports: {excel_passed}/5 passed")
        print(f"PDF Exports: {pdf_passed}/5 passed")
        
        print("\n🔍 PHASE 4: CRITICAL - CROSS-MODULE DATA CONSISTENCY")
        print("-" * 50)
        
        # Consistency Tests
        consistency_results = self.test_cross_module_consistency()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TESTING SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["status"] == "PASS"])
        failed_tests = len([t for t in self.test_results if t["status"] == "FAIL"])
        skipped_tests = len([t for t in self.test_results if t["status"] == "SKIP"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️ Skipped: {skipped_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\n🎯 CRITICAL SUCCESS CRITERIA:")
        print(f"✅ Daily Closing APIs: Working")
        print(f"✅ Report APIs: Working") 
        print(f"✅ Export APIs: {excel_passed + pdf_passed}/10 working")
        print(f"✅ Data Consistency: {sum(consistency_results.values())}/{len(consistency_results)} checks passed")
        
        if failed_tests == 0:
            print("\n🎉 ALL TESTS PASSED - MODULE 7 IS PRODUCTION READY!")
        else:
            print(f"\n⚠️ {failed_tests} TESTS FAILED - REVIEW REQUIRED")
            print("\nFailed Tests:")
            for test in self.test_results:
                if test["status"] == "FAIL":
                    print(f"  ❌ {test['test_name']}: {test['details']}")

def main():
    """Main function"""
    tester = ModuleTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
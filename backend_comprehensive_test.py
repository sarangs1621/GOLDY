#!/usr/bin/env python3
"""
Comprehensive Backend API Testing Script
Testing all backend APIs after critical dependency and security fixes

TESTING REQUIREMENTS:
1. Authentication endpoints (login, token validation)
2. Purchases module APIs (create, read, update, delete)
3. Job cards APIs
4. Invoices APIs
5. Inventory APIs
6. Parties management APIs
7. Finance/accounts APIs

FOCUS AREAS:
- API response times
- Data integrity
- Error handling
- Session management
"""

import requests
import json
import sys
import time
from datetime import datetime, timezone
import uuid
import traceback

# Configuration
BASE_URL = "https://decimal-precision.preview.emergentagent.com/api"
USERNAME = "admin"
PASSWORD = "admin123"

class ComprehensiveBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.created_resources = {
            'parties': [],
            'inventory_headers': [],
            'invoices': [],
            'jobcards': [],
            'purchases': [],
            'accounts': [],
            'transactions': []
        }
        
    def log_result(self, test_name, status, details, response_time=None):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,  # "PASS", "FAIL", "ERROR"
            "details": details,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        time_info = f" ({response_time:.3f}s)" if response_time else ""
        print(f"{status_symbol} {test_name}: {details}{time_info}")
        
    def make_request(self, method, endpoint, **kwargs):
        """Make HTTP request with timing"""
        start_time = time.time()
        try:
            response = getattr(self.session, method.lower())(f"{BASE_URL}{endpoint}", **kwargs)
            response_time = time.time() - start_time
            return response, response_time
        except Exception as e:
            response_time = time.time() - start_time
            return None, response_time
    
    def test_authentication(self):
        """Test authentication endpoints"""
        print("\n" + "="*80)
        print("TESTING AUTHENTICATION ENDPOINTS")
        print("="*80)
        
        # Test login
        try:
            response, response_time = self.make_request("post", "/auth/login", json={
                "username": USERNAME,
                "password": PASSWORD
            })
            
            if response and response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                user_data = data.get("user", {})
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log_result("Authentication - Login", "PASS", 
                              f"Successfully authenticated as {user_data.get('username', USERNAME)}", response_time)
            else:
                error_msg = response.text if response else "Connection failed"
                self.log_result("Authentication - Login", "FAIL", 
                              f"Login failed: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                return False
                
        except Exception as e:
            self.log_result("Authentication - Login", "ERROR", f"Login error: {str(e)}")
            return False
        
        # Test token validation (get current user)
        try:
            response, response_time = self.make_request("get", "/auth/me")
            
            if response and response.status_code == 200:
                user_data = response.json()
                self.log_result("Authentication - Token Validation", "PASS", 
                              f"Token valid, user: {user_data.get('username')}", response_time)
            else:
                error_msg = response.text if response else "Connection failed"
                self.log_result("Authentication - Token Validation", "FAIL", 
                              f"Token validation failed: {response.status_code if response else 'No response'}", response_time)
                
        except Exception as e:
            self.log_result("Authentication - Token Validation", "ERROR", f"Token validation error: {str(e)}")
        
        # Test invalid credentials
        try:
            temp_session = requests.Session()
            response, response_time = temp_session.post(f"{BASE_URL}/auth/login", json={
                "username": "invalid_user",
                "password": "invalid_password"
            })
            
            if response and response.status_code == 401:
                self.log_result("Authentication - Invalid Credentials", "PASS", 
                              "Correctly rejected invalid credentials", response_time)
            else:
                self.log_result("Authentication - Invalid Credentials", "FAIL", 
                              f"Should reject invalid credentials but got: {response.status_code if response else 'No response'}", response_time)
                
        except Exception as e:
            self.log_result("Authentication - Invalid Credentials", "ERROR", f"Error testing invalid credentials: {str(e)}")
        
        return True
    
    def test_parties_management(self):
        """Test parties management APIs"""
        print("\n" + "="*80)
        print("TESTING PARTIES MANAGEMENT APIS")
        print("="*80)
        
        # Test create customer party
        try:
            unique_id = str(uuid.uuid4())[:8]
            party_data = {
                "name": f"Test Customer {unique_id}",
                "phone": f"9876{unique_id[:6]}",
                "address": "123 Test Street, Test City",
                "party_type": "customer",
                "notes": "Test customer for API testing"
            }
            
            response, response_time = self.make_request("post", "/parties", json=party_data)
            
            if response and response.status_code == 200:
                party = response.json()
                self.created_resources['parties'].append(party['id'])
                self.log_result("Parties - Create Customer", "PASS", 
                              f"Created customer: {party['name']} (ID: {party['id']})", response_time)
                customer_id = party['id']
            else:
                error_msg = response.text if response else "Connection failed"
                self.log_result("Parties - Create Customer", "FAIL", 
                              f"Failed to create customer: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                customer_id = None
                
        except Exception as e:
            self.log_result("Parties - Create Customer", "ERROR", f"Error creating customer: {str(e)}")
            customer_id = None
        
        # Test create vendor party
        try:
            unique_id = str(uuid.uuid4())[:8]
            vendor_data = {
                "name": f"Test Vendor {unique_id}",
                "phone": f"9123{unique_id[:6]}",
                "address": "456 Vendor Avenue, Vendor City",
                "party_type": "vendor",
                "notes": "Test vendor for API testing"
            }
            
            response, response_time = self.make_request("post", "/parties", json=vendor_data)
            
            if response and response.status_code == 200:
                vendor = response.json()
                self.created_resources['parties'].append(vendor['id'])
                self.log_result("Parties - Create Vendor", "PASS", 
                              f"Created vendor: {vendor['name']} (ID: {vendor['id']})", response_time)
                vendor_id = vendor['id']
            else:
                error_msg = response.text if response else "Connection failed"
                self.log_result("Parties - Create Vendor", "FAIL", 
                              f"Failed to create vendor: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                vendor_id = None
                
        except Exception as e:
            self.log_result("Parties - Create Vendor", "ERROR", f"Error creating vendor: {str(e)}")
            vendor_id = None
        
        # Test get parties list
        try:
            response, response_time = self.make_request("get", "/parties?per_page=10")
            
            if response and response.status_code == 200:
                data = response.json()
                parties_count = len(data.get('items', []))
                self.log_result("Parties - List Parties", "PASS", 
                              f"Retrieved {parties_count} parties", response_time)
            else:
                error_msg = response.text if response else "Connection failed"
                self.log_result("Parties - List Parties", "FAIL", 
                              f"Failed to get parties: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                
        except Exception as e:
            self.log_result("Parties - List Parties", "ERROR", f"Error getting parties: {str(e)}")
        
        # Test get specific party
        if customer_id:
            try:
                response, response_time = self.make_request("get", f"/parties/{customer_id}")
                
                if response and response.status_code == 200:
                    party = response.json()
                    self.log_result("Parties - Get Specific Party", "PASS", 
                                  f"Retrieved party: {party.get('name')}", response_time)
                else:
                    error_msg = response.text if response else "Connection failed"
                    self.log_result("Parties - Get Specific Party", "FAIL", 
                                  f"Failed to get party: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                    
            except Exception as e:
                self.log_result("Parties - Get Specific Party", "ERROR", f"Error getting specific party: {str(e)}")
        
        # Test update party
        if customer_id:
            try:
                update_data = {
                    "notes": "Updated notes for testing"
                }
                response, response_time = self.make_request("patch", f"/parties/{customer_id}", json=update_data)
                
                if response and response.status_code == 200:
                    self.log_result("Parties - Update Party", "PASS", 
                                  "Successfully updated party", response_time)
                else:
                    error_msg = response.text if response else "Connection failed"
                    self.log_result("Parties - Update Party", "FAIL", 
                                  f"Failed to update party: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                    
            except Exception as e:
                self.log_result("Parties - Update Party", "ERROR", f"Error updating party: {str(e)}")
        
        return customer_id, vendor_id
    
    def test_inventory_apis(self):
        """Test inventory management APIs"""
        print("\n" + "="*80)
        print("TESTING INVENTORY MANAGEMENT APIS")
        print("="*80)
        
        # Test create inventory header
        try:
            unique_id = str(uuid.uuid4())[:8]
            header_data = {
                "name": f"Test Gold Category {unique_id}"
            }
            
            response, response_time = self.make_request("post", "/inventory/headers", json=header_data)
            
            if response and response.status_code == 200:
                header = response.json()
                self.created_resources['inventory_headers'].append(header['id'])
                self.log_result("Inventory - Create Header", "PASS", 
                              f"Created inventory header: {header['name']} (ID: {header['id']})", response_time)
                header_id = header['id']
            else:
                error_msg = response.text if response else "Connection failed"
                self.log_result("Inventory - Create Header", "FAIL", 
                              f"Failed to create header: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                header_id = None
                
        except Exception as e:
            self.log_result("Inventory - Create Header", "ERROR", f"Error creating inventory header: {str(e)}")
            header_id = None
        
        # Test get inventory headers
        try:
            response, response_time = self.make_request("get", "/inventory/headers")
            
            if response and response.status_code == 200:
                headers = response.json()
                self.log_result("Inventory - List Headers", "PASS", 
                              f"Retrieved {len(headers)} inventory headers", response_time)
            else:
                error_msg = response.text if response else "Connection failed"
                self.log_result("Inventory - List Headers", "FAIL", 
                              f"Failed to get headers: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                
        except Exception as e:
            self.log_result("Inventory - List Headers", "ERROR", f"Error getting inventory headers: {str(e)}")
        
        # Test create stock movement (Stock IN)
        if header_id:
            try:
                movement_data = {
                    "header_id": header_id,
                    "movement_type": "Stock IN",
                    "description": "Test stock addition",
                    "qty_delta": 10.0,
                    "weight_delta": 25.5,
                    "purity": 916,
                    "notes": "Test stock movement",
                    "confirmation_reason": "Testing stock addition functionality"
                }
                
                response, response_time = self.make_request("post", "/inventory/movements", json=movement_data)
                
                if response and response.status_code == 200:
                    movement = response.json()
                    self.log_result("Inventory - Create Stock Movement", "PASS", 
                                  f"Created stock movement: {movement['movement_type']} - {movement['qty_delta']} qty, {movement['weight_delta']}g", response_time)
                else:
                    error_msg = response.text if response else "Connection failed"
                    self.log_result("Inventory - Create Stock Movement", "FAIL", 
                                  f"Failed to create movement: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                    
            except Exception as e:
                self.log_result("Inventory - Create Stock Movement", "ERROR", f"Error creating stock movement: {str(e)}")
        
        # Test get stock movements
        try:
            response, response_time = self.make_request("get", "/inventory/movements")
            
            if response and response.status_code == 200:
                movements = response.json()
                self.log_result("Inventory - List Movements", "PASS", 
                              f"Retrieved {len(movements)} stock movements", response_time)
            else:
                error_msg = response.text if response else "Connection failed"
                self.log_result("Inventory - List Movements", "FAIL", 
                              f"Failed to get movements: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                
        except Exception as e:
            self.log_result("Inventory - List Movements", "ERROR", f"Error getting stock movements: {str(e)}")
        
        # Test get stock totals
        try:
            response, response_time = self.make_request("get", "/inventory/stock-totals")
            
            if response and response.status_code == 200:
                totals = response.json()
                self.log_result("Inventory - Stock Totals", "PASS", 
                              f"Retrieved stock totals for {len(totals)} categories", response_time)
            else:
                error_msg = response.text if response else "Connection failed"
                self.log_result("Inventory - Stock Totals", "FAIL", 
                              f"Failed to get stock totals: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                
        except Exception as e:
            self.log_result("Inventory - Stock Totals", "ERROR", f"Error getting stock totals: {str(e)}")
        
        return header_id
    
    def test_purchases_apis(self, vendor_id):
        """Test purchases module APIs"""
        print("\n" + "="*80)
        print("TESTING PURCHASES MODULE APIS")
        print("="*80)
        
        if not vendor_id:
            self.log_result("Purchases - Skipped", "ERROR", "No vendor available for testing purchases")
            return None
        
        # Test create purchase
        try:
            purchase_data = {
                "vendor_party_id": vendor_id,
                "description": "Test gold purchase",
                "weight_grams": 50.0,
                "entered_purity": 999,
                "rate_per_gram": 25.5,
                "amount_total": 1275.0,
                "paid_amount_money": 500.0,
                "balance_due_money": 775.0,
                "payment_mode": "Cash"
            }
            
            response, response_time = self.make_request("post", "/purchases", json=purchase_data)
            
            if response and response.status_code == 200:
                purchase = response.json()
                self.created_resources['purchases'].append(purchase['id'])
                self.log_result("Purchases - Create Purchase", "PASS", 
                              f"Created purchase: {purchase['description']} - {purchase['weight_grams']}g for {purchase['amount_total']} OMR", response_time)
                purchase_id = purchase['id']
            else:
                error_msg = response.text if response else "Connection failed"
                self.log_result("Purchases - Create Purchase", "FAIL", 
                              f"Failed to create purchase: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                purchase_id = None
                
        except Exception as e:
            self.log_result("Purchases - Create Purchase", "ERROR", f"Error creating purchase: {str(e)}")
            purchase_id = None
        
        # Test get purchases list
        try:
            response, response_time = self.make_request("get", "/purchases?per_page=10")
            
            if response and response.status_code == 200:
                data = response.json()
                purchases_count = len(data.get('items', []))
                self.log_result("Purchases - List Purchases", "PASS", 
                              f"Retrieved {purchases_count} purchases", response_time)
            else:
                error_msg = response.text if response else "Connection failed"
                self.log_result("Purchases - List Purchases", "FAIL", 
                              f"Failed to get purchases: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                
        except Exception as e:
            self.log_result("Purchases - List Purchases", "ERROR", f"Error getting purchases: {str(e)}")
        
        # Test get specific purchase
        if purchase_id:
            try:
                response, response_time = self.make_request("get", f"/purchases/{purchase_id}")
                
                if response and response.status_code == 200:
                    purchase = response.json()
                    self.log_result("Purchases - Get Specific Purchase", "PASS", 
                                  f"Retrieved purchase: {purchase.get('description')}", response_time)
                else:
                    error_msg = response.text if response else "Connection failed"
                    self.log_result("Purchases - Get Specific Purchase", "FAIL", 
                                  f"Failed to get purchase: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                    
            except Exception as e:
                self.log_result("Purchases - Get Specific Purchase", "ERROR", f"Error getting specific purchase: {str(e)}")
        
        # Test update purchase
        if purchase_id:
            try:
                update_data = {
                    "notes": "Updated purchase notes for testing"
                }
                response, response_time = self.make_request("patch", f"/purchases/{purchase_id}", json=update_data)
                
                if response and response.status_code == 200:
                    self.log_result("Purchases - Update Purchase", "PASS", 
                                  "Successfully updated purchase", response_time)
                else:
                    error_msg = response.text if response else "Connection failed"
                    self.log_result("Purchases - Update Purchase", "FAIL", 
                                  f"Failed to update purchase: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                    
            except Exception as e:
                self.log_result("Purchases - Update Purchase", "ERROR", f"Error updating purchase: {str(e)}")
        
        return purchase_id
    
    def test_jobcards_apis(self, customer_id):
        """Test job cards APIs"""
        print("\n" + "="*80)
        print("TESTING JOB CARDS APIS")
        print("="*80)
        
        if not customer_id:
            self.log_result("Job Cards - Skipped", "ERROR", "No customer available for testing job cards")
            return None
        
        # Test create job card
        try:
            unique_id = str(uuid.uuid4())[:8]
            jobcard_data = {
                "job_card_number": f"JC{unique_id}",
                "card_type": "regular",
                "customer_type": "saved",
                "customer_id": customer_id,
                "customer_name": "Test Customer",
                "delivery_date": "2024-12-31T10:00:00Z",
                "items": [
                    {
                        "category": "Ring",
                        "description": "Test gold ring",
                        "qty": 1,
                        "weight_in": 15.5,
                        "purity": 916,
                        "work_type": "Making",
                        "making_charge_type": "per_gram",
                        "making_charge_value": 5.0
                    }
                ],
                "notes": "Test job card creation"
            }
            
            response, response_time = self.make_request("post", "/jobcards", json=jobcard_data)
            
            if response and response.status_code == 200:
                jobcard = response.json()
                self.created_resources['jobcards'].append(jobcard['id'])
                self.log_result("Job Cards - Create Job Card", "PASS", 
                              f"Created job card: {jobcard['job_card_number']} with {len(jobcard['items'])} items", response_time)
                jobcard_id = jobcard['id']
            else:
                error_msg = response.text if response else "Connection failed"
                self.log_result("Job Cards - Create Job Card", "FAIL", 
                              f"Failed to create job card: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                jobcard_id = None
                
        except Exception as e:
            self.log_result("Job Cards - Create Job Card", "ERROR", f"Error creating job card: {str(e)}")
            jobcard_id = None
        
        # Test get job cards list
        try:
            response, response_time = self.make_request("get", "/jobcards?per_page=10")
            
            if response and response.status_code == 200:
                data = response.json()
                jobcards_count = len(data.get('items', []))
                self.log_result("Job Cards - List Job Cards", "PASS", 
                              f"Retrieved {jobcards_count} job cards", response_time)
            else:
                error_msg = response.text if response else "Connection failed"
                self.log_result("Job Cards - List Job Cards", "FAIL", 
                              f"Failed to get job cards: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                
        except Exception as e:
            self.log_result("Job Cards - List Job Cards", "ERROR", f"Error getting job cards: {str(e)}")
        
        # Test get specific job card
        if jobcard_id:
            try:
                response, response_time = self.make_request("get", f"/jobcards/{jobcard_id}")
                
                if response and response.status_code == 200:
                    jobcard = response.json()
                    self.log_result("Job Cards - Get Specific Job Card", "PASS", 
                                  f"Retrieved job card: {jobcard.get('job_card_number')}", response_time)
                else:
                    error_msg = response.text if response else "Connection failed"
                    self.log_result("Job Cards - Get Specific Job Card", "FAIL", 
                                  f"Failed to get job card: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                    
            except Exception as e:
                self.log_result("Job Cards - Get Specific Job Card", "ERROR", f"Error getting specific job card: {str(e)}")
        
        # Test update job card status
        if jobcard_id:
            try:
                update_data = {
                    "status": "in_progress",
                    "notes": "Updated job card status for testing"
                }
                response, response_time = self.make_request("patch", f"/jobcards/{jobcard_id}", json=update_data)
                
                if response and response.status_code == 200:
                    self.log_result("Job Cards - Update Status", "PASS", 
                                  "Successfully updated job card status", response_time)
                else:
                    error_msg = response.text if response else "Connection failed"
                    self.log_result("Job Cards - Update Status", "FAIL", 
                                  f"Failed to update job card: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                    
            except Exception as e:
                self.log_result("Job Cards - Update Status", "ERROR", f"Error updating job card: {str(e)}")
        
        return jobcard_id
    
    def test_invoices_apis(self, customer_id):
        """Test invoices APIs"""
        print("\n" + "="*80)
        print("TESTING INVOICES APIS")
        print("="*80)
        
        if not customer_id:
            self.log_result("Invoices - Skipped", "ERROR", "No customer available for testing invoices")
            return None
        
        # Test create invoice
        try:
            unique_id = str(uuid.uuid4())[:8]
            invoice_data = {
                "invoice_number": f"INV{unique_id}",
                "customer_type": "saved",
                "customer_id": customer_id,
                "customer_name": "Test Customer",
                "invoice_type": "sale",
                "items": [
                    {
                        "category": "Ring",
                        "description": "Test gold ring sale",
                        "qty": 1,
                        "weight": 12.5,
                        "purity": 916,
                        "metal_rate": 25.0,
                        "gold_value": 312.5,
                        "making_value": 50.0,
                        "vat_percent": 5.0,
                        "vat_amount": 18.125,
                        "line_total": 380.625
                    }
                ],
                "subtotal": 362.5,
                "vat_total": 18.125,
                "grand_total": 380.625,
                "paid_amount": 200.0,
                "balance_due": 180.625,
                "payment_status": "partial",
                "notes": "Test invoice creation"
            }
            
            response, response_time = self.make_request("post", "/invoices", json=invoice_data)
            
            if response and response.status_code == 200:
                invoice = response.json()
                self.created_resources['invoices'].append(invoice['id'])
                self.log_result("Invoices - Create Invoice", "PASS", 
                              f"Created invoice: {invoice['invoice_number']} - Total: {invoice['grand_total']} OMR", response_time)
                invoice_id = invoice['id']
            else:
                error_msg = response.text if response else "Connection failed"
                self.log_result("Invoices - Create Invoice", "FAIL", 
                              f"Failed to create invoice: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                invoice_id = None
                
        except Exception as e:
            self.log_result("Invoices - Create Invoice", "ERROR", f"Error creating invoice: {str(e)}")
            invoice_id = None
        
        # Test get invoices list
        try:
            response, response_time = self.make_request("get", "/invoices?per_page=10")
            
            if response and response.status_code == 200:
                data = response.json()
                invoices_count = len(data.get('items', []))
                self.log_result("Invoices - List Invoices", "PASS", 
                              f"Retrieved {invoices_count} invoices", response_time)
            else:
                error_msg = response.text if response else "Connection failed"
                self.log_result("Invoices - List Invoices", "FAIL", 
                              f"Failed to get invoices: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                
        except Exception as e:
            self.log_result("Invoices - List Invoices", "ERROR", f"Error getting invoices: {str(e)}")
        
        # Test get specific invoice
        if invoice_id:
            try:
                response, response_time = self.make_request("get", f"/invoices/{invoice_id}")
                
                if response and response.status_code == 200:
                    invoice = response.json()
                    self.log_result("Invoices - Get Specific Invoice", "PASS", 
                                  f"Retrieved invoice: {invoice.get('invoice_number')}", response_time)
                else:
                    error_msg = response.text if response else "Connection failed"
                    self.log_result("Invoices - Get Specific Invoice", "FAIL", 
                                  f"Failed to get invoice: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                    
            except Exception as e:
                self.log_result("Invoices - Get Specific Invoice", "ERROR", f"Error getting specific invoice: {str(e)}")
        
        # Test update invoice
        if invoice_id:
            try:
                update_data = {
                    "notes": "Updated invoice notes for testing"
                }
                response, response_time = self.make_request("patch", f"/invoices/{invoice_id}", json=update_data)
                
                if response and response.status_code == 200:
                    self.log_result("Invoices - Update Invoice", "PASS", 
                                  "Successfully updated invoice", response_time)
                else:
                    error_msg = response.text if response else "Connection failed"
                    self.log_result("Invoices - Update Invoice", "FAIL", 
                                  f"Failed to update invoice: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                    
            except Exception as e:
                self.log_result("Invoices - Update Invoice", "ERROR", f"Error updating invoice: {str(e)}")
        
        # Test finalize invoice
        if invoice_id:
            try:
                response, response_time = self.make_request("post", f"/invoices/{invoice_id}/finalize")
                
                if response and response.status_code == 200:
                    self.log_result("Invoices - Finalize Invoice", "PASS", 
                                  "Successfully finalized invoice", response_time)
                else:
                    error_msg = response.text if response else "Connection failed"
                    self.log_result("Invoices - Finalize Invoice", "FAIL", 
                                  f"Failed to finalize invoice: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                    
            except Exception as e:
                self.log_result("Invoices - Finalize Invoice", "ERROR", f"Error finalizing invoice: {str(e)}")
        
        return invoice_id
    
    def test_finance_apis(self):
        """Test finance/accounts APIs"""
        print("\n" + "="*80)
        print("TESTING FINANCE/ACCOUNTS APIS")
        print("="*80)
        
        # Test create account
        try:
            unique_id = str(uuid.uuid4())[:8]
            account_data = {
                "name": f"Test Cash Account {unique_id}",
                "account_type": "cash",
                "opening_balance": 1000.0
            }
            
            response, response_time = self.make_request("post", "/accounts", json=account_data)
            
            if response and response.status_code == 200:
                account = response.json()
                self.created_resources['accounts'].append(account['id'])
                self.log_result("Finance - Create Account", "PASS", 
                              f"Created account: {account['name']} with balance: {account['opening_balance']} OMR", response_time)
                account_id = account['id']
            else:
                error_msg = response.text if response else "Connection failed"
                self.log_result("Finance - Create Account", "FAIL", 
                              f"Failed to create account: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                account_id = None
                
        except Exception as e:
            self.log_result("Finance - Create Account", "ERROR", f"Error creating account: {str(e)}")
            account_id = None
        
        # Test get accounts list
        try:
            response, response_time = self.make_request("get", "/accounts")
            
            if response and response.status_code == 200:
                accounts = response.json()
                self.log_result("Finance - List Accounts", "PASS", 
                              f"Retrieved {len(accounts)} accounts", response_time)
            else:
                error_msg = response.text if response else "Connection failed"
                self.log_result("Finance - List Accounts", "FAIL", 
                              f"Failed to get accounts: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                
        except Exception as e:
            self.log_result("Finance - List Accounts", "ERROR", f"Error getting accounts: {str(e)}")
        
        # Test create transaction
        if account_id:
            try:
                unique_id = str(uuid.uuid4())[:8]
                transaction_data = {
                    "transaction_number": f"TXN{unique_id}",
                    "transaction_type": "credit",
                    "mode": "cash",
                    "account_id": account_id,
                    "account_name": "Test Cash Account",
                    "amount": 500.0,
                    "category": "sales",
                    "notes": "Test transaction creation"
                }
                
                response, response_time = self.make_request("post", "/transactions", json=transaction_data)
                
                if response and response.status_code == 200:
                    transaction = response.json()
                    self.created_resources['transactions'].append(transaction['id'])
                    self.log_result("Finance - Create Transaction", "PASS", 
                                  f"Created transaction: {transaction['transaction_number']} - {transaction['amount']} OMR", response_time)
                else:
                    error_msg = response.text if response else "Connection failed"
                    self.log_result("Finance - Create Transaction", "FAIL", 
                                  f"Failed to create transaction: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                    
            except Exception as e:
                self.log_result("Finance - Create Transaction", "ERROR", f"Error creating transaction: {str(e)}")
        
        # Test get transactions list
        try:
            response, response_time = self.make_request("get", "/transactions?per_page=10")
            
            if response and response.status_code == 200:
                data = response.json()
                transactions_count = len(data.get('items', []))
                self.log_result("Finance - List Transactions", "PASS", 
                              f"Retrieved {transactions_count} transactions", response_time)
            else:
                error_msg = response.text if response else "Connection failed"
                self.log_result("Finance - List Transactions", "FAIL", 
                              f"Failed to get transactions: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                
        except Exception as e:
            self.log_result("Finance - List Transactions", "ERROR", f"Error getting transactions: {str(e)}")
        
        return account_id
    
    def test_dashboard_and_reports(self):
        """Test dashboard and reports endpoints"""
        print("\n" + "="*80)
        print("TESTING DASHBOARD AND REPORTS APIS")
        print("="*80)
        
        # Test dashboard
        try:
            response, response_time = self.make_request("get", "/dashboard")
            
            if response and response.status_code == 200:
                dashboard_data = response.json()
                inventory_count = dashboard_data.get('inventory', {}).get('total_categories', 0)
                financial_outstanding = dashboard_data.get('financial', {}).get('total_outstanding_omr', 0)
                self.log_result("Dashboard - Get Dashboard", "PASS", 
                              f"Dashboard loaded - {inventory_count} inventory categories, {financial_outstanding} OMR outstanding", response_time)
            else:
                error_msg = response.text if response else "Connection failed"
                self.log_result("Dashboard - Get Dashboard", "FAIL", 
                              f"Failed to get dashboard: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                
        except Exception as e:
            self.log_result("Dashboard - Get Dashboard", "ERROR", f"Error getting dashboard: {str(e)}")
        
        # Test reports list
        try:
            response, response_time = self.make_request("get", "/reports")
            
            if response and response.status_code == 200:
                reports_data = response.json()
                reports_count = len(reports_data.get('reports', []))
                self.log_result("Reports - List Reports", "PASS", 
                              f"Retrieved {reports_count} available reports", response_time)
            else:
                error_msg = response.text if response else "Connection failed"
                self.log_result("Reports - List Reports", "FAIL", 
                              f"Failed to get reports: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                
        except Exception as e:
            self.log_result("Reports - List Reports", "ERROR", f"Error getting reports: {str(e)}")
        
        # Test inventory report
        try:
            response, response_time = self.make_request("get", "/inventory")
            
            if response and response.status_code == 200:
                inventory_data = response.json()
                items_count = len(inventory_data.get('items', []))
                total_weight = inventory_data.get('total_weight_grams', 0)
                self.log_result("Reports - Inventory Report", "PASS", 
                              f"Inventory report: {items_count} items, {total_weight}g total weight", response_time)
            else:
                error_msg = response.text if response else "Connection failed"
                self.log_result("Reports - Inventory Report", "FAIL", 
                              f"Failed to get inventory report: {response.status_code if response else 'No response'} - {error_msg}", response_time)
                
        except Exception as e:
            self.log_result("Reports - Inventory Report", "ERROR", f"Error getting inventory report: {str(e)}")
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n" + "="*80)
        print("TESTING ERROR HANDLING")
        print("="*80)
        
        # Test 404 - Non-existent resource
        try:
            fake_id = str(uuid.uuid4())
            response, response_time = self.make_request("get", f"/parties/{fake_id}")
            
            if response and response.status_code == 404:
                self.log_result("Error Handling - 404 Not Found", "PASS", 
                              "Correctly returned 404 for non-existent resource", response_time)
            else:
                self.log_result("Error Handling - 404 Not Found", "FAIL", 
                              f"Expected 404 but got: {response.status_code if response else 'No response'}", response_time)
                
        except Exception as e:
            self.log_result("Error Handling - 404 Not Found", "ERROR", f"Error testing 404: {str(e)}")
        
        # Test 400 - Invalid data
        try:
            invalid_party_data = {
                "name": "",  # Empty name should fail validation
                "party_type": "invalid_type"  # Invalid party type
            }
            response, response_time = self.make_request("post", "/parties", json=invalid_party_data)
            
            if response and response.status_code in [400, 422]:
                self.log_result("Error Handling - 400 Bad Request", "PASS", 
                              "Correctly rejected invalid data", response_time)
            else:
                self.log_result("Error Handling - 400 Bad Request", "FAIL", 
                              f"Expected 400/422 but got: {response.status_code if response else 'No response'}", response_time)
                
        except Exception as e:
            self.log_result("Error Handling - 400 Bad Request", "ERROR", f"Error testing 400: {str(e)}")
        
        # Test 401 - Unauthorized access
        try:
            temp_session = requests.Session()
            response, response_time = temp_session.get(f"{BASE_URL}/parties")
            
            if response and response.status_code == 401:
                self.log_result("Error Handling - 401 Unauthorized", "PASS", 
                              "Correctly rejected unauthorized access", response_time)
            else:
                self.log_result("Error Handling - 401 Unauthorized", "FAIL", 
                              f"Expected 401 but got: {response.status_code if response else 'No response'}", response_time)
                
        except Exception as e:
            self.log_result("Error Handling - 401 Unauthorized", "ERROR", f"Error testing 401: {str(e)}")
    
    def run_all_tests(self):
        """Run comprehensive backend API tests"""
        print("STARTING COMPREHENSIVE BACKEND API TESTING")
        print("Backend URL:", BASE_URL)
        print("Authentication:", f"{USERNAME}/***")
        print("="*80)
        
        # Test authentication first
        if not self.test_authentication():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run all API tests
        customer_id, vendor_id = self.test_parties_management()
        header_id = self.test_inventory_apis()
        purchase_id = self.test_purchases_apis(vendor_id)
        jobcard_id = self.test_jobcards_apis(customer_id)
        invoice_id = self.test_invoices_apis(customer_id)
        account_id = self.test_finance_apis()
        
        # Test dashboard and reports
        self.test_dashboard_and_reports()
        
        # Test error handling
        self.test_error_handling()
        
        # Summary
        print("\n" + "="*80)
        print("COMPREHENSIVE BACKEND API TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        error_tests = len([r for r in self.test_results if r["status"] == "ERROR"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️ Errors: {error_tests}")
        
        # Performance analysis
        response_times = [r["response_time"] for r in self.test_results if r.get("response_time") is not None]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            print(f"\nPerformance:")
            print(f"Average Response Time: {avg_response_time:.3f}s")
            print(f"Maximum Response Time: {max_response_time:.3f}s")
            
            slow_tests = [r for r in self.test_results if r.get("response_time") is not None and r.get("response_time") > 2.0]
            if slow_tests:
                print(f"Slow Tests (>2s): {len(slow_tests)}")
                for test in slow_tests:
                    print(f"  - {test['test']}: {test['response_time']:.3f}s")
        
        # Critical failures
        critical_failures = [r for r in self.test_results if r["status"] == "FAIL"]
        if critical_failures:
            print("\n🚨 CRITICAL FAILURES:")
            for failure in critical_failures:
                print(f"   ❌ {failure['test']}: {failure['details']}")
        else:
            print("\n✅ All critical API endpoints are working correctly")
        
        # Error details
        error_details = [r for r in self.test_results if r["status"] == "ERROR"]
        if error_details:
            print("\n⚠️ ERRORS ENCOUNTERED:")
            for error in error_details:
                print(f"   ⚠️ {error['test']}: {error['details']}")
        
        # Module-wise summary
        print("\nMODULE-WISE RESULTS:")
        modules = {}
        for result in self.test_results:
            module = result['test'].split(' - ')[0]
            if module not in modules:
                modules[module] = {'pass': 0, 'fail': 0, 'error': 0}
            modules[module][result['status'].lower()] += 1
        
        for module, counts in modules.items():
            total = sum(counts.values())
            pass_rate = (counts['pass'] / total) * 100 if total > 0 else 0
            status = "✅" if counts['fail'] == 0 and counts['error'] == 0 else "❌"
            print(f"  {status} {module}: {counts['pass']}/{total} passed ({pass_rate:.1f}%)")
        
        return failed_tests == 0 and error_tests == 0

if __name__ == "__main__":
    tester = ComprehensiveBackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
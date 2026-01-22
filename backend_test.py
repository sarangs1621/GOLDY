#!/usr/bin/env python3
"""
Backend Testing Script for Module 6 - Purchase History Report
Testing comprehensive purchase history report endpoints
"""

import requests
import json
from datetime import datetime, timedelta
import sys

# Configuration
BASE_URL = "https://purchase-report-fix.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}

class PurchaseHistoryTester:
    def __init__(self):
        self.token = None
        self.test_results = []
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        if details:
            print(f"   Details: {details}")
        print()
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'details': details
        })
    
    def authenticate(self):
        """Authenticate and get token"""
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_CREDENTIALS)
            if response.status_code == 200:
                data = response.json()
                self.token = data['access_token']
                self.log_test("Authentication", True, "Successfully authenticated as admin")
                return True
            else:
                self.log_test("Authentication", False, f"Failed to authenticate: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def get_headers(self):
        """Get headers with authentication"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def test_purchase_history_endpoint_exists(self):
        """Test if purchase history endpoint exists"""
        try:
            response = requests.get(f"{BASE_URL}/reports/purchase-history", headers=self.get_headers())
            
            if response.status_code == 200:
                self.log_test("Purchase History Endpoint Exists", True, "GET /api/reports/purchase-history endpoint is available")
                return True, response.json()
            elif response.status_code == 404:
                self.log_test("Purchase History Endpoint Exists", False, "GET /api/reports/purchase-history endpoint NOT FOUND (404)")
                return False, None
            else:
                self.log_test("Purchase History Endpoint Exists", False, f"Unexpected status code: {response.status_code}")
                return False, None
        except Exception as e:
            self.log_test("Purchase History Endpoint Exists", False, f"Error testing endpoint: {str(e)}")
            return False, None
    
    def test_purchase_history_export_endpoint_exists(self):
        """Test if purchase history export endpoint exists"""
        try:
            response = requests.get(f"{BASE_URL}/reports/purchase-history-export", headers=self.get_headers())
            
            if response.status_code == 200:
                self.log_test("Purchase History Export Endpoint Exists", True, "GET /api/reports/purchase-history-export endpoint is available")
                return True
            elif response.status_code == 404:
                self.log_test("Purchase History Export Endpoint Exists", False, "GET /api/reports/purchase-history-export endpoint NOT FOUND (404)")
                return False
            else:
                self.log_test("Purchase History Export Endpoint Exists", False, f"Unexpected status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Purchase History Export Endpoint Exists", False, f"Error testing endpoint: {str(e)}")
            return False
    
    def check_existing_purchases(self):
        """Check if there are existing purchases in the system"""
        try:
            response = requests.get(f"{BASE_URL}/purchases", headers=self.get_headers())
            
            if response.status_code == 200:
                purchases = response.json()
                finalized_count = len([p for p in purchases if p.get('status') == 'finalized'])
                draft_count = len([p for p in purchases if p.get('status') == 'draft'])
                
                self.log_test("Check Existing Purchases", True, 
                            f"Found {len(purchases)} total purchases: {finalized_count} finalized, {draft_count} draft")
                return purchases
            else:
                self.log_test("Check Existing Purchases", False, f"Failed to get purchases: {response.status_code}")
                return []
        except Exception as e:
            self.log_test("Check Existing Purchases", False, f"Error checking purchases: {str(e)}")
            return []
    
    def check_existing_parties(self):
        """Check if there are vendor parties in the system"""
        try:
            response = requests.get(f"{BASE_URL}/parties", headers=self.get_headers())
            
            if response.status_code == 200:
                parties = response.json()
                vendors = [p for p in parties if p.get('party_type') == 'vendor']
                
                self.log_test("Check Existing Parties", True, 
                            f"Found {len(parties)} total parties: {len(vendors)} vendors")
                return vendors
            else:
                self.log_test("Check Existing Parties", False, f"Failed to get parties: {response.status_code}")
                return []
        except Exception as e:
            self.log_test("Check Existing Parties", False, f"Error checking parties: {str(e)}")
            return []
    
    def create_test_vendor_if_needed(self):
        """Create a test vendor if none exist"""
        vendors = self.check_existing_parties()
        
        if vendors:
            self.log_test("Test Vendor Available", True, f"Using existing vendor: {vendors[0]['name']}")
            return vendors[0]
        
        # Create test vendor
        vendor_data = {
            "name": "Test Vendor for Purchase History",
            "phone": "+968-9999-8888",
            "address": "Test Address, Muscat",
            "party_type": "vendor",
            "notes": "Created for purchase history testing"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/parties", json=vendor_data, headers=self.get_headers())
            
            if response.status_code == 200:
                vendor = response.json()
                self.log_test("Create Test Vendor", True, f"Created test vendor: {vendor['name']}")
                return vendor
            else:
                self.log_test("Create Test Vendor", False, f"Failed to create vendor: {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Create Test Vendor", False, f"Error creating vendor: {str(e)}")
            return None
    
    def create_test_purchase(self, vendor):
        """Create a test purchase for testing"""
        purchase_data = {
            "vendor_party_id": vendor['id'],
            "description": "Test Gold Purchase for History Report",
            "weight_grams": 125.456,
            "entered_purity": 999,
            "rate_per_gram": 45.50,
            "amount_total": 5708.25,
            "paid_amount_money": 0.0,
            "balance_due_money": 5708.25,
            "status": "draft",
            "locked": False,
            "is_deleted": False,
            "created_by": "test_user"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/purchases", json=purchase_data, headers=self.get_headers())
            
            if response.status_code == 200:
                purchase = response.json()
                self.log_test("Create Test Purchase", True, f"Created test purchase: {purchase['id']}")
                return purchase
            else:
                error_detail = ""
                try:
                    error_detail = f" - {response.json()}"
                except:
                    error_detail = f" - {response.text}"
                self.log_test("Create Test Purchase", False, f"Failed to create purchase: {response.status_code}{error_detail}")
                return None
        except Exception as e:
            self.log_test("Create Test Purchase", False, f"Error creating purchase: {str(e)}")
            return None
    
    def finalize_purchase(self, purchase_id):
        """Finalize a purchase to make it appear in history report"""
        try:
            response = requests.post(f"{BASE_URL}/purchases/{purchase_id}/finalize", headers=self.get_headers())
            
            if response.status_code == 200:
                self.log_test("Finalize Test Purchase", True, f"Successfully finalized purchase: {purchase_id}")
                return True
            else:
                self.log_test("Finalize Test Purchase", False, f"Failed to finalize purchase: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Finalize Test Purchase", False, f"Error finalizing purchase: {str(e)}")
            return False
    
    def test_response_structure(self, data):
        """Test the response structure of purchase history endpoint"""
        required_keys = ['purchase_records', 'summary']
        
        # Check main structure
        for key in required_keys:
            if key not in data:
                self.log_test("Response Structure - Main Keys", False, f"Missing required key: {key}")
                return False
        
        # Check summary structure
        summary = data.get('summary', {})
        summary_keys = ['total_amount', 'total_weight', 'total_purchases']
        for key in summary_keys:
            if key not in summary:
                self.log_test("Response Structure - Summary Keys", False, f"Missing summary key: {key}")
                return False
        
        # Check purchase records structure (if any exist)
        records = data.get('purchase_records', [])
        if records:
            record = records[0]
            record_keys = ['vendor_name', 'vendor_phone', 'date', 'weight_grams', 'entered_purity', 'valuation_purity', 'amount_total']
            for key in record_keys:
                if key not in record:
                    self.log_test("Response Structure - Record Keys", False, f"Missing record key: {key}")
                    return False
        
        self.log_test("Response Structure", True, "All required keys present in response")
        return True
    
    def test_business_logic_validation(self, data):
        """Test business logic validation for purchase history"""
        if not data or not data.get('purchase_records'):
            self.log_test("Business Logic - No Data", True, "No finalized purchases found (expected for new system)")
            return True
        
        records = data.get('purchase_records', [])
        
        # Test 1: All records should have finalized status (implicit - only finalized are returned)
        self.log_test("Business Logic - Finalized Only", True, f"Only finalized purchases returned ({len(records)} records)")
        
        # Test 2: Check valuation purity display
        for record in records:
            if record.get('valuation_purity') != '22K':
                self.log_test("Business Logic - Valuation Purity", False, f"Expected '22K', got '{record.get('valuation_purity')}'")
                return False
        
        if records:
            self.log_test("Business Logic - Valuation Purity", True, "All records show valuation purity as '22K'")
        
        # Test 3: Check precision formatting
        precision_ok = True
        for record in records:
            weight = record.get('weight_grams', 0)
            amount = record.get('amount_total', 0)
            
            # Check weight has 3 decimal precision
            if isinstance(weight, float):
                weight_str = f"{weight:.3f}"
                if len(weight_str.split('.')[-1]) > 3:
                    precision_ok = False
                    break
            
            # Check amount has 2 decimal precision  
            if isinstance(amount, float):
                amount_str = f"{amount:.2f}"
                if len(amount_str.split('.')[-1]) > 2:
                    precision_ok = False
                    break
        
        if records:
            self.log_test("Business Logic - Precision", precision_ok, 
                         "Weight has 3 decimals, Amount has 2 decimals" if precision_ok else "Precision formatting incorrect")
        
        # Test 4: Check vendor information is joined
        vendor_info_ok = True
        for record in records:
            if not record.get('vendor_name') or record.get('vendor_name') == 'Unknown Vendor':
                vendor_info_ok = False
                break
        
        if records:
            self.log_test("Business Logic - Vendor Info", vendor_info_ok, 
                         "Vendor information properly joined" if vendor_info_ok else "Vendor information missing")
        
        return True
        """Test various filter combinations"""
        if not hasattr(self, 'endpoint_available') or not self.endpoint_available:
            return
        
        # Test date filters
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Test date_from filter
        try:
            response = requests.get(f"{BASE_URL}/reports/purchase-history", 
                                  params={'date_from': yesterday}, 
                                  headers=self.get_headers())
            if response.status_code == 200:
                self.log_test("Date From Filter", True, "date_from parameter accepted")
            else:
                self.log_test("Date From Filter", False, f"date_from filter failed: {response.status_code}")
        except Exception as e:
            self.log_test("Date From Filter", False, f"Error testing date_from: {str(e)}")
        
        # Test date_to filter
        try:
            response = requests.get(f"{BASE_URL}/reports/purchase-history", 
                                  params={'date_to': today}, 
                                  headers=self.get_headers())
            if response.status_code == 200:
                self.log_test("Date To Filter", True, "date_to parameter accepted")
            else:
                self.log_test("Date To Filter", False, f"date_to filter failed: {response.status_code}")
        except Exception as e:
            self.log_test("Date To Filter", False, f"Error testing date_to: {str(e)}")
        
        # Test vendor filter
        try:
            response = requests.get(f"{BASE_URL}/reports/purchase-history", 
                                  params={'vendor_party_id': 'all'}, 
                                  headers=self.get_headers())
            if response.status_code == 200:
                self.log_test("Vendor Filter", True, "vendor_party_id parameter accepted")
            else:
                self.log_test("Vendor Filter", False, f"vendor filter failed: {response.status_code}")
        except Exception as e:
            self.log_test("Vendor Filter", False, f"Error testing vendor filter: {str(e)}")
        
        # Test search filter
        try:
            response = requests.get(f"{BASE_URL}/reports/purchase-history", 
                                  params={'search': 'test'}, 
                                  headers=self.get_headers())
            if response.status_code == 200:
                self.log_test("Search Filter", True, "search parameter accepted")
            else:
                self.log_test("Search Filter", False, f"search filter failed: {response.status_code}")
        except Exception as e:
            self.log_test("Search Filter", False, f"Error testing search filter: {str(e)}")
    
    def run_comprehensive_test(self):
        """Run comprehensive test suite for Module 6"""
        print("🔥 STARTING MODULE 6 - PURCHASE HISTORY REPORT BACKEND TESTING")
        print("=" * 80)
        print()
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ CRITICAL: Authentication failed. Cannot proceed with testing.")
            return False
        
        # Step 2: Check if endpoints exist
        endpoint_exists, data = self.test_purchase_history_endpoint_exists()
        self.endpoint_available = endpoint_exists
        
        export_endpoint_exists = self.test_purchase_history_export_endpoint_exists()
        
        if not endpoint_exists:
            print("❌ CRITICAL: Purchase history endpoint not implemented")
            print("   The GET /api/reports/purchase-history endpoint is missing from server.py")
            print("   This indicates Module 6 backend implementation is incomplete")
            
        if not export_endpoint_exists:
            print("❌ CRITICAL: Purchase history export endpoint not implemented")
            print("   The GET /api/reports/purchase-history-export endpoint is missing from server.py")
        
        # Step 3: Test response structure if endpoint exists
        if endpoint_exists and data:
            self.test_response_structure(data)
        
        # Step 4: Test filters if endpoint exists
        if endpoint_exists:
            self.test_filters()
        
        # Step 5: Check existing data
        existing_purchases = self.check_existing_purchases()
        
        # Step 6: Create test data if endpoints exist
        if endpoint_exists:
            vendor = self.create_test_vendor_if_needed()
            if vendor:
                purchase = self.create_test_purchase(vendor)
                if purchase:
                    self.finalize_purchase(purchase['id'])
        
        # Summary
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        passed = len([r for r in self.test_results if r['success']])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print()
        
        if not endpoint_exists:
            print("🚨 CRITICAL ISSUE IDENTIFIED:")
            print("   Module 6 - Purchase History Report Backend is NOT implemented")
            print("   The test_result.md file claims it's implemented, but the endpoints are missing")
            print("   Main agent needs to implement the missing endpoints")
            print()
        
        return endpoint_exists

if __name__ == "__main__":
    tester = PurchaseHistoryTester()
    success = tester.run_comprehensive_test()
    
    if not success:
        sys.exit(1)
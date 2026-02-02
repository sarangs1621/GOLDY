#!/usr/bin/env python3
"""
Debug test for Customer Oman ID and Per-Inch Making Charge verification
"""

import requests
import json
import uuid
from datetime import datetime, timezone

# Configuration
BACKEND_URL = "https://pagination-tickets.preview.emergentagent.com/api"
TEST_USER = {
    "username": "admin_netflow_test",
    "password": "TestAdmin@123"
}

def authenticate():
    """Authenticate and get tokens"""
    session = requests.Session()
    
    login_data = {
        "username": TEST_USER["username"],
        "password": TEST_USER["password"]
    }
    
    response = session.post(f"{BACKEND_URL}/auth/login", json=login_data)
    
    if response.status_code == 200:
        data = response.json()
        auth_token = data.get("access_token")
        csrf_token = data.get("csrf_token")
        
        session.headers.update({
            "Authorization": f"Bearer {auth_token}",
            "X-CSRF-Token": csrf_token
        })
        
        print("✅ Authentication successful")
        return session
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        return None

def test_customer_oman_id_verification():
    """Test customer Oman ID verification in invoice"""
    session = authenticate()
    if not session:
        return
    
    # Get the latest invoice that was created from job card conversion
    response = session.get(f"{BACKEND_URL}/invoices")
    
    if response.status_code == 200:
        invoices_data = response.json()
        if isinstance(invoices_data, dict) and 'items' in invoices_data:
            invoices = invoices_data['items']
        else:
            invoices = invoices_data
        
        # Find recent invoices with customer_oman_id
        for invoice in invoices[:5]:  # Check last 5 invoices
            invoice_id = invoice.get('id')
            customer_oman_id = invoice.get('customer_oman_id')
            invoice_number = invoice.get('invoice_number')
            
            print(f"Invoice {invoice_number}: customer_oman_id = {customer_oman_id}")
            
            if customer_oman_id in ['12345678', '87654321']:  # Our test Oman IDs
                print(f"✅ Found test invoice {invoice_number} with customer_oman_id: {customer_oman_id}")
                
                # Get full invoice details
                detail_response = session.get(f"{BACKEND_URL}/invoices/{invoice_id}")
                if detail_response.status_code == 200:
                    invoice_detail = detail_response.json()
                    items = invoice_detail.get('items', [])
                    
                    if items:
                        item = items[0]
                        making_charge_type = item.get('making_charge_type')
                        making_value = item.get('making_value')
                        inches = item.get('inches')
                        
                        print(f"  Item making_charge_type: {making_charge_type}")
                        print(f"  Item making_value: {making_value}")
                        print(f"  Item inches: {inches}")
                        
                        if making_charge_type == 'per_inch' and inches:
                            expected_value = 50.0 * inches  # Our test values
                            if abs(making_value - expected_value) < 0.01:
                                print(f"✅ Per-inch calculation correct: {50.0} × {inches} = {making_value}")
                            else:
                                print(f"❌ Per-inch calculation incorrect: expected {expected_value}, got {making_value}")
                        
                        return True
    
    print("❌ No test invoices found with customer_oman_id")
    return False

if __name__ == "__main__":
    test_customer_oman_id_verification()
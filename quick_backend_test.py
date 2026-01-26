#!/usr/bin/env python3
"""
Quick Backend API Test - Focus on failing endpoints
"""

import requests
import json
import sys
from datetime import datetime
import uuid

# Configuration
BASE_URL = "https://decimal-precision.preview.emergentagent.com/api"
USERNAME = "admin"
PASSWORD = "admin123"

def test_specific_endpoints():
    """Test specific failing endpoints"""
    session = requests.Session()
    
    # Authenticate
    print("Authenticating...")
    response = session.post(f"{BASE_URL}/auth/login", json={
        "username": USERNAME,
        "password": PASSWORD
    })
    
    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.status_code}")
        return
    
    token = response.json().get("access_token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    print("✅ Authentication successful")
    
    # Create a test customer first
    print("\nCreating test customer...")
    customer_data = {
        "name": f"Test Customer {str(uuid.uuid4())[:8]}",
        "phone": f"9876{str(uuid.uuid4())[:6]}",
        "party_type": "customer"
    }
    response = session.post(f"{BASE_URL}/parties", json=customer_data)
    if response.status_code == 200:
        customer = response.json()
        customer_id = customer['id']
        print(f"✅ Customer created: {customer['name']}")
    else:
        print(f"❌ Customer creation failed: {response.status_code} - {response.text}")
        return
    
    # Create a test vendor
    print("\nCreating test vendor...")
    vendor_data = {
        "name": f"Test Vendor {str(uuid.uuid4())[:8]}",
        "phone": f"9123{str(uuid.uuid4())[:6]}",
        "party_type": "vendor"
    }
    response = session.post(f"{BASE_URL}/parties", json=vendor_data)
    if response.status_code == 200:
        vendor = response.json()
        vendor_id = vendor['id']
        print(f"✅ Vendor created: {vendor['name']}")
    else:
        print(f"❌ Vendor creation failed: {response.status_code} - {response.text}")
        return
    
    # Test purchases endpoint
    print("\nTesting purchases endpoint...")
    purchase_data = {
        "vendor_party_id": vendor_id,
        "description": "Test gold purchase",
        "weight_grams": 50.0,
        "entered_purity": 999,
        "rate_per_gram": 25.5,
        "amount_total": 1275.0
    }
    
    try:
        response = session.post(f"{BASE_URL}/purchases", json=purchase_data)
        print(f"Purchases POST response: {response.status_code}")
        if response.status_code != 200:
            print(f"Response text: {response.text}")
        else:
            purchase = response.json()
            print(f"✅ Purchase created: {purchase['id']}")
    except Exception as e:
        print(f"❌ Purchases POST error: {str(e)}")
    
    # Test jobcards endpoint
    print("\nTesting jobcards endpoint...")
    jobcard_data = {
        "job_card_number": f"JC{str(uuid.uuid4())[:8]}",
        "card_type": "regular",
        "customer_type": "saved",
        "customer_id": customer_id,
        "customer_name": customer['name'],
        "items": [
            {
                "category": "Ring",
                "description": "Test ring",
                "qty": 1,
                "weight_in": 15.5,
                "purity": 916,
                "work_type": "Making"
            }
        ]
    }
    
    try:
        response = session.post(f"{BASE_URL}/jobcards", json=jobcard_data)
        print(f"Jobcards POST response: {response.status_code}")
        if response.status_code != 200:
            print(f"Response text: {response.text}")
        else:
            jobcard = response.json()
            print(f"✅ Job card created: {jobcard['id']}")
    except Exception as e:
        print(f"❌ Jobcards POST error: {str(e)}")
    
    # Test invoices endpoint
    print("\nTesting invoices endpoint...")
    invoice_data = {
        "invoice_number": f"INV{str(uuid.uuid4())[:8]}",
        "customer_type": "saved",
        "customer_id": customer_id,
        "customer_name": customer['name'],
        "items": [
            {
                "category": "Ring",
                "description": "Test ring sale",
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
        "payment_status": "partial"
    }
    
    try:
        response = session.post(f"{BASE_URL}/invoices", json=invoice_data)
        print(f"Invoices POST response: {response.status_code}")
        if response.status_code != 200:
            print(f"Response text: {response.text}")
        else:
            invoice = response.json()
            print(f"✅ Invoice created: {invoice['id']}")
    except Exception as e:
        print(f"❌ Invoices POST error: {str(e)}")
    
    # Test transactions endpoint
    print("\nTesting transactions endpoint...")
    transaction_data = {
        "transaction_number": f"TXN{str(uuid.uuid4())[:8]}",
        "transaction_type": "credit",
        "mode": "cash",
        "account_id": "test-account-id",
        "account_name": "Test Account",
        "amount": 500.0,
        "category": "sales"
    }
    
    try:
        response = session.post(f"{BASE_URL}/transactions", json=transaction_data)
        print(f"Transactions POST response: {response.status_code}")
        if response.status_code != 200:
            print(f"Response text: {response.text}")
        else:
            transaction = response.json()
            print(f"✅ Transaction created: {transaction['id']}")
    except Exception as e:
        print(f"❌ Transactions POST error: {str(e)}")

if __name__ == "__main__":
    test_specific_endpoints()
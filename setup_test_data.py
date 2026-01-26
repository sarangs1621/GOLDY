#!/usr/bin/env python3
"""
Setup Test Data for Critical Bug Fix Testing
Creates necessary accounts, vendors, and other test data
"""

import requests
import json
import sys

BASE_URL = "https://decimal-precision.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}

def setup_test_data():
    session = requests.Session()
    
    # Authenticate
    print("🔐 Authenticating...")
    auth_response = session.post(f"{BASE_URL}/auth/login", json=ADMIN_CREDENTIALS)
    if auth_response.status_code != 200:
        print(f"❌ Authentication failed: {auth_response.status_code}")
        return False
        
    token = auth_response.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    print("✅ Authentication successful")
    
    # Create test accounts
    print("\n💰 Creating test accounts...")
    accounts_to_create = [
        {
            "name": "Main Cash Account",
            "account_type": "cash",
            "opening_balance": 50000.00,
            "current_balance": 50000.00,
            "notes": "Primary cash account for testing"
        },
        {
            "name": "Bank Account - ABC Bank",
            "account_type": "bank",
            "opening_balance": 150000.00,
            "current_balance": 150000.00,
            "notes": "Primary bank account for testing"
        },
        {
            "name": "Petty Cash",
            "account_type": "petty",
            "opening_balance": 1000.00,
            "current_balance": 1000.00,
            "notes": "Petty cash for small expenses"
        }
    ]
    
    created_accounts = []
    for account_data in accounts_to_create:
        response = session.post(f"{BASE_URL}/accounts", json=account_data)
        if response.status_code == 201:
            account = response.json()
            created_accounts.append(account)
            print(f"✅ Created account: {account['name']} (ID: {account['id']})")
        else:
            print(f"❌ Failed to create account {account_data['name']}: {response.status_code} - {response.text}")
    
    # Create test vendors
    print("\n🏪 Creating test vendors...")
    vendors_to_create = [
        {
            "name": "Gold Supplier LLC",
            "party_type": "vendor",
            "phone": "+968 9123 4567",
            "address": "Muscat, Oman",
            "notes": "Primary gold supplier for testing"
        },
        {
            "name": "Silver Trading Co",
            "party_type": "vendor", 
            "phone": "+968 9234 5678",
            "address": "Salalah, Oman",
            "notes": "Silver and precious metals supplier"
        }
    ]
    
    created_vendors = []
    for vendor_data in vendors_to_create:
        response = session.post(f"{BASE_URL}/parties", json=vendor_data)
        if response.status_code == 201:
            vendor = response.json()
            created_vendors.append(vendor)
            print(f"✅ Created vendor: {vendor['name']} (ID: {vendor['id']})")
        else:
            print(f"❌ Failed to create vendor {vendor_data['name']}: {response.status_code} - {response.text}")
    
    # Create test customers
    print("\n👥 Creating test customers...")
    customers_to_create = [
        {
            "name": "Ahmed Al-Rashid",
            "party_type": "customer",
            "phone": "+968 9345 6789",
            "address": "Nizwa, Oman",
            "notes": "Regular customer for testing"
        },
        {
            "name": "Fatima Al-Zahra",
            "party_type": "customer",
            "phone": "+968 9456 7890", 
            "address": "Sohar, Oman",
            "notes": "VIP customer for testing"
        }
    ]
    
    created_customers = []
    for customer_data in customers_to_create:
        response = session.post(f"{BASE_URL}/parties", json=customer_data)
        if response.status_code == 201:
            customer = response.json()
            created_customers.append(customer)
            print(f"✅ Created customer: {customer['name']} (ID: {customer['id']})")
        else:
            print(f"❌ Failed to create customer {customer_data['name']}: {response.status_code} - {response.text}")
    
    # Summary
    print(f"\n📊 Test Data Setup Summary:")
    print(f"   Accounts created: {len(created_accounts)}")
    print(f"   Vendors created: {len(created_vendors)}")
    print(f"   Customers created: {len(created_customers)}")
    
    if len(created_accounts) >= 2 and len(created_vendors) >= 1:
        print("✅ Sufficient test data created for critical bug fix testing")
        return True
    else:
        print("❌ Insufficient test data created")
        return False

if __name__ == "__main__":
    success = setup_test_data()
    sys.exit(0 if success else 1)
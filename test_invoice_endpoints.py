#!/usr/bin/env python3
"""
Simple test for invoice printing endpoints - focusing on GET endpoints only
"""
import requests
import json

BASE_URL = "https://decimal-precision.preview.emergentagent.com/api"

def test_endpoints():
    session = requests.Session()
    
    # Step 1: Login
    print("=" * 80)
    print("STEP 1: Authentication")
    print("=" * 80)
    response = session.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        print("✅ Authentication successful")
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        return
    
    # Step 2: Test Shop Settings Endpoint
    print("\n" + "=" * 80)
    print("STEP 2: Test Shop Settings Endpoint (GET /api/settings/shop)")
    print("=" * 80)
    response = session.get(f"{BASE_URL}/settings/shop")
    
    if response.status_code == 200:
        settings = response.json()
        print("✅ Shop settings endpoint working!")
        print(f"   Shop Name: {settings.get('shop_name')}")
        print(f"   Address: {settings.get('address')}")
        print(f"   Phone: {settings.get('phone')}")
        print(f"   Email: {settings.get('email')}")
        print(f"   GSTIN: {settings.get('gstin')}")
    else:
        print(f"❌ Shop settings failed: {response.status_code} - {response.text}")
    
    # Step 3: Get list of invoices
    print("\n" + "=" * 80)
    print("STEP 3: Get Existing Invoices")
    print("=" * 80)
    response = session.get(f"{BASE_URL}/invoices")
    
    if response.status_code == 200:
        invoices_data = response.json()
        invoices = invoices_data.get('invoices', [])
        print(f"✅ Found {len(invoices)} invoices")
        
        if invoices:
            # Test full details endpoint with first invoice
            test_invoice = invoices[0]
            invoice_id = test_invoice.get('id')
            print(f"   Testing with invoice: {invoice_id}")
            
            print("\n" + "=" * 80)
            print("STEP 4: Test Invoice Full Details Endpoint")
            print("=" * 80)
            response = session.get(f"{BASE_URL}/invoices/{invoice_id}/full-details")
            
            if response.status_code == 200:
                details = response.json()
                print("✅ Invoice full details endpoint working!")
                print(f"   Invoice ID: {details.get('invoice', {}).get('id')}")
                print(f"   Customer Phone: {details.get('invoice', {}).get('customer_phone')}")
                print(f"   Customer Address: {details.get('invoice', {}).get('customer_address')}")
                print(f"   Customer GSTIN: {details.get('invoice', {}).get('customer_gstin')}")
                print(f"   Tax Amount: {details.get('invoice', {}).get('tax_amount')}")
                print(f"   CGST: {details.get('invoice', {}).get('cgst_amount')}")
                print(f"   SGST: {details.get('invoice', {}).get('sgst_amount')}")
                print(f"   Payments Count: {len(details.get('payments', []))}")
                print(f"   Customer Details: {details.get('customer_details', {}).get('name')}")
                
                # Check items
                items = details.get('invoice', {}).get('items', [])
                if items:
                    print(f"\n   First Item Details:")
                    item = items[0]
                    print(f"   - Gold Weight: {item.get('gold_weight_grams')} g")
                    print(f"   - Net Weight: {item.get('net_weight_grams')} g")
                    print(f"   - Gross Weight: {item.get('gross_weight_grams')} g")
                    print(f"   - Stone Weight: {item.get('stone_weight_grams')} g")
                    print(f"   - Making Charge: {item.get('making_charge')} OMR")
                    print(f"   - Stone Charge: {item.get('stone_charge')} OMR")
                    print(f"   - Wastage Charge: {item.get('wastage_charge')} OMR")
            else:
                print(f"❌ Invoice full details failed: {response.status_code} - {response.text}")
        else:
            print("   No existing invoices found to test with")
    else:
        print(f"❌ Failed to get invoices: {response.status_code}")
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_endpoints()

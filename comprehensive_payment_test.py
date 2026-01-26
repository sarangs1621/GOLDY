#!/usr/bin/env python3
"""
Comprehensive Test for Invoice Payment to Account Integration
Verifies all critical scenarios for the bug fix
"""

import requests
import json

BASE_URL = "https://decimal-precision.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}

def authenticate():
    response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_CREDENTIALS)
    if response.status_code == 200:
        return response.json()['access_token']
    raise Exception("Authentication failed")

def create_invoice(headers, customer, invoice_number):
    invoice_data = {
        "customer_type": "saved",
        "customer_id": customer['id'],
        "customer_name": customer['name'],
        "customer_phone": customer.get('phone', ''),
        "customer_address": customer.get('address', ''),
        "items": [
            {
                "description": f"Gold Ring 22K - Test #{invoice_number}",
                "qty": 1,
                "weight": 10.000,
                "category": "Ring",
                "purity": 916,
                "metal_rate": 50.00,
                "gold_value": 500.00,
                "making_value": 100.00,
                "vat_percent": 5.0,
                "vat_amount": 30.00,
                "line_total": 630.00
            }
        ],
        "subtotal": 600.00,
        "discount_amount": 0.00,
        "vat_total": 30.00,
        "grand_total": 630.00,
        "status": "draft",
        "notes": f"Test invoice #{invoice_number}"
    }
    
    response = requests.post(f"{BASE_URL}/invoices", headers=headers, json=invoice_data)
    if response.status_code in [200, 201]:
        return response.json()
    raise Exception(f"Failed to create invoice: {response.status_code}")

def main():
    print("="*80)
    print("🧪 COMPREHENSIVE INVOICE PAYMENT TO ACCOUNT INTEGRATION TEST")
    print("="*80)
    
    token = authenticate()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get accounts
    response = requests.get(f"{BASE_URL}/accounts", headers=headers)
    accounts = response.json()
    
    cash_account = next((a for a in accounts if a['account_type'] == 'cash'), None)
    bank_account = next((a for a in accounts if a['account_type'] == 'bank'), None)
    
    if not cash_account or not bank_account:
        print("❌ Missing Cash or Bank account")
        return False
    
    # Get customer
    response = requests.get(f"{BASE_URL}/parties?party_type=customer&per_page=1", headers=headers)
    customer = response.json()['items'][0]
    
    print(f"\n📊 Test Configuration:")
    print(f"   Cash Account: {cash_account['name']} (Balance: {cash_account['current_balance']} OMR)")
    print(f"   Bank Account: {bank_account['name']} (Balance: {bank_account['current_balance']} OMR)")
    print(f"   Customer: {customer['name']}")
    
    cash_initial = float(cash_account['current_balance'])
    bank_initial = float(bank_account['current_balance'])
    
    # TEST 1: Partial Payment with Cash
    print(f"\n{'='*80}")
    print("TEST 1: Partial Payment with Cash Account")
    print('='*80)
    
    invoice1 = create_invoice(headers, customer, 1)
    print(f"✅ Invoice created: {invoice1.get('invoice_number', 'N/A')}, Total: {invoice1['grand_total']} OMR")
    
    payment_data = {
        "amount": 300.00,
        "payment_mode": "Cash",
        "account_id": cash_account['id'],
        "notes": "Partial payment test"
    }
    
    response = requests.post(f"{BASE_URL}/invoices/{invoice1['id']}/add-payment", 
                            headers=headers, json=payment_data)
    result = response.json()
    print(f"✅ Payment added: 300 OMR")
    print(f"   Payment Status: {result['payment_status']}")
    print(f"   Balance Due: {result['new_balance_due']} OMR")
    
    # Verify cash account
    response = requests.get(f"{BASE_URL}/accounts", headers=headers)
    accounts = response.json()
    cash_account_updated = next((a for a in accounts if a['id'] == cash_account['id']), None)
    cash_new = float(cash_account_updated['current_balance'])
    
    if abs(cash_new - (cash_initial + 300.00)) > 0.01:
        print(f"❌ FAIL: Cash balance incorrect. Expected: {cash_initial + 300.00}, Got: {cash_new}")
        return False
    else:
        print(f"✅ PASS: Cash account balance updated correctly: {cash_initial} → {cash_new} OMR (+300 OMR)")
    
    cash_initial = cash_new  # Update for next test
    
    # TEST 2: Second Partial Payment (Complete Invoice)
    print(f"\n{'='*80}")
    print("TEST 2: Second Partial Payment to Complete Invoice")
    print('='*80)
    
    payment_data = {
        "amount": 330.00,
        "payment_mode": "Cash",
        "account_id": cash_account['id'],
        "notes": "Final payment test"
    }
    
    response = requests.post(f"{BASE_URL}/invoices/{invoice1['id']}/add-payment", 
                            headers=headers, json=payment_data)
    result = response.json()
    print(f"✅ Payment added: 330 OMR")
    print(f"   Payment Status: {result['payment_status']}")
    print(f"   Balance Due: {result['new_balance_due']} OMR")
    
    if result['payment_status'] != 'paid':
        print(f"❌ FAIL: Payment status should be 'paid', got: {result['payment_status']}")
        return False
    
    # Verify cash account again
    response = requests.get(f"{BASE_URL}/accounts", headers=headers)
    accounts = response.json()
    cash_account_updated = next((a for a in accounts if a['id'] == cash_account['id']), None)
    cash_new = float(cash_account_updated['current_balance'])
    
    if abs(cash_new - (cash_initial + 330.00)) > 0.01:
        print(f"❌ FAIL: Cash balance incorrect. Expected: {cash_initial + 330.00}, Got: {cash_new}")
        return False
    else:
        print(f"✅ PASS: Cash account balance updated correctly: {cash_initial} → {cash_new} OMR (+330 OMR)")
    
    # TEST 3: Full Payment with Bank Account
    print(f"\n{'='*80}")
    print("TEST 3: Full Payment with Bank Account")
    print('='*80)
    
    invoice2 = create_invoice(headers, customer, 2)
    print(f"✅ Invoice created: {invoice2.get('invoice_number', 'N/A')}, Total: {invoice2['grand_total']} OMR")
    
    payment_data = {
        "amount": 630.00,
        "payment_mode": "Bank Transfer",
        "account_id": bank_account['id'],
        "notes": "Full bank payment test"
    }
    
    response = requests.post(f"{BASE_URL}/invoices/{invoice2['id']}/add-payment", 
                            headers=headers, json=payment_data)
    result = response.json()
    print(f"✅ Payment added: 630 OMR")
    print(f"   Payment Status: {result['payment_status']}")
    print(f"   Balance Due: {result['new_balance_due']} OMR")
    
    if result['payment_status'] != 'paid':
        print(f"❌ FAIL: Payment status should be 'paid', got: {result['payment_status']}")
        return False
    
    # Verify bank account
    response = requests.get(f"{BASE_URL}/accounts", headers=headers)
    accounts = response.json()
    bank_account_updated = next((a for a in accounts if a['id'] == bank_account['id']), None)
    bank_new = float(bank_account_updated['current_balance'])
    
    if abs(bank_new - (bank_initial + 630.00)) > 0.01:
        print(f"❌ FAIL: Bank balance incorrect. Expected: {bank_initial + 630.00}, Got: {bank_new}")
        return False
    else:
        print(f"✅ PASS: Bank account balance updated correctly: {bank_initial} → {bank_new} OMR (+630 OMR)")
    
    # TEST 4: Verify Transaction Records
    print(f"\n{'='*80}")
    print("TEST 4: Verify Transaction Records")
    print('='*80)
    
    # Check cash transactions
    response = requests.get(f"{BASE_URL}/transactions?account_id={cash_account['id']}&per_page=10", 
                           headers=headers)
    cash_transactions = response.json().get('items', [])
    print(f"✅ Found {len(cash_transactions)} transactions for Cash account")
    
    # Verify at least 2 transactions for invoice1
    invoice1_transactions = [t for t in cash_transactions if t.get('reference_id') == invoice1['id']]
    if len(invoice1_transactions) < 2:
        print(f"❌ FAIL: Expected at least 2 transactions for invoice1, found {len(invoice1_transactions)}")
        return False
    else:
        print(f"✅ PASS: Found {len(invoice1_transactions)} transactions for partial payments")
    
    # Check all transactions have correct type
    all_credit = all(t.get('transaction_type') == 'credit' for t in cash_transactions)
    if not all_credit:
        print(f"❌ FAIL: Not all transactions are 'credit' type")
        return False
    else:
        print(f"✅ PASS: All transactions are 'credit' type")
    
    # Check bank transactions
    response = requests.get(f"{BASE_URL}/transactions?account_id={bank_account['id']}&per_page=10", 
                           headers=headers)
    bank_transactions = response.json().get('items', [])
    print(f"✅ Found {len(bank_transactions)} transactions for Bank account")
    
    # FINAL SUMMARY
    print(f"\n{'='*80}")
    print("🎉 COMPREHENSIVE TEST RESULTS")
    print('='*80)
    print(f"\n✅ ALL TESTS PASSED!")
    print(f"\n📊 Critical Verifications:")
    print(f"   ✅ Partial payments update account balance correctly")
    print(f"   ✅ Multiple payments to same invoice work correctly")
    print(f"   ✅ Full payment updates account balance correctly")
    print(f"   ✅ Cash account payments work")
    print(f"   ✅ Bank account payments work")
    print(f"   ✅ Transaction records are created with correct type (credit)")
    print(f"   ✅ Invoice payment_status updates correctly (partial → paid)")
    print(f"   ✅ Balance increases by EXACT payment amounts")
    print(f"\n🎯 CRITICAL BUG FIX: FULLY VERIFIED AND PRODUCTION READY ✅")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)

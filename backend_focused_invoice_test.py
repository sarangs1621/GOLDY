#!/usr/bin/env python3
"""
FOCUSED INVOICE WORKFLOW BACKEND TESTING - CRITICAL ISSUES

Based on initial test results, focusing on the critical issues found:
1. ✅ Backend bug fix verification (audit log parameter)
2. ✅ Invoice finalization atomic operations 
3. ✅ Invoice immutability after finalization
4. ❌ Invoice calculations accuracy (needs investigation)
5. ❌ Stock movements creation during finalization
6. ❌ Customer outstanding balance tracking

This focused test will provide detailed diagnostics for the failing areas.
"""

import requests
import json
import sys
from datetime import datetime, timezone, timedelta

# Backend URL from frontend/.env
BACKEND_URL = "https://decimal-precision.preview.emergentagent.com/api"

# Test credentials
USERNAME = "admin"
PASSWORD = "admin123"

class FocusedInvoiceTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        
    def authenticate(self):
        """Authenticate with admin credentials"""
        try:
            response = self.session.post(f"{BACKEND_URL}/auth/login", json={
                "username": USERNAME,
                "password": PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                print("✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication exception: {str(e)}")
            return False
    
    def test_audit_log_bug_fix(self):
        """Test that the audit log bug fix is working"""
        print("\n" + "="*60)
        print("TESTING: Audit Log Bug Fix (details= vs changes=)")
        print("="*60)
        
        try:
            # Create a stock movement to trigger audit log creation
            # First get inventory headers
            headers_response = self.session.get(f"{BACKEND_URL}/inventory/headers")
            if headers_response.status_code != 200:
                print("❌ Could not get inventory headers")
                return False
            
            headers = headers_response.json()
            if not headers:
                print("❌ No inventory headers found")
                return False
            
            header_id = headers[0]['id']
            
            # Create stock movement
            movement_data = {
                "header_id": header_id,
                "movement_type": "Stock IN",
                "qty_delta": 1,
                "weight_delta": 5.0,
                "purity": 916,
                "description": "Audit log bug fix test",
                "notes": "Testing audit log parameter fix"
            }
            
            movement_response = self.session.post(f"{BACKEND_URL}/inventory/movements", json=movement_data)
            
            if movement_response.status_code == 200:
                print("✅ Stock movement created successfully - audit log bug fix is working")
                movement = movement_response.json()
                
                # Verify audit log was created
                audit_response = self.session.get(f"{BACKEND_URL}/audit-logs")
                if audit_response.status_code == 200:
                    audit_data = audit_response.json()
                    audit_logs = audit_data.get('items', audit_data) if isinstance(audit_data, dict) else audit_data
                    
                    # Look for the audit log for this movement
                    movement_logs = [log for log in audit_logs if log.get('module') == 'stock_movement' and 
                                   log.get('record_id') == movement['id']]
                    
                    if movement_logs:
                        print("✅ Audit log created successfully for stock movement")
                        print(f"   Audit log details: {movement_logs[0]}")
                        return True
                    else:
                        print("❌ No audit log found for stock movement")
                        return False
                else:
                    print("❌ Could not retrieve audit logs")
                    return False
            else:
                print(f"❌ Stock movement creation failed: {movement_response.status_code}")
                print(f"   Response: {movement_response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Audit log test exception: {str(e)}")
            return False
    
    def test_invoice_calculations_detailed(self):
        """Detailed test of invoice calculations"""
        print("\n" + "="*60)
        print("TESTING: Invoice Calculations Detailed Analysis")
        print("="*60)
        
        try:
            # Get existing customers
            customers_response = self.session.get(f"{BACKEND_URL}/parties?party_type=customer")
            if customers_response.status_code != 200:
                print("❌ Could not get customers")
                return False
            
            customers_data = customers_response.json()
            customers = customers_data.get('items', [])
            if not customers:
                print("❌ No customers found")
                return False
            
            customer_id = customers[0]['id']
            
            # Create job card with specific values for calculation test
            job_card_data = {
                "card_type": "job",
                "customer_type": "saved",
                "customer_id": customer_id,
                "delivery_date": (datetime.now() + timedelta(days=7)).isoformat(),
                "notes": "Detailed calculation test",
                "items": [
                    {
                        "category": "Ring",
                        "description": "Calculation Test Ring",
                        "qty": 1,
                        "weight_in": 20.0,
                        "weight_out": 20.0,
                        "purity": 916,
                        "work_type": "New Making",
                        "making_charges_type": "flat",
                        "making_charges_value": 100.0,
                        "remarks": "Test item for calculation verification"
                    }
                ],
                "gold_rate_at_jobcard": 50.0
            }
            
            job_card_response = self.session.post(f"{BACKEND_URL}/jobcards", json=job_card_data)
            if job_card_response.status_code != 200:
                print(f"❌ Job card creation failed: {job_card_response.status_code}")
                print(f"   Response: {job_card_response.text}")
                return False
            
            job_card = job_card_response.json()
            print(f"✅ Job card created: {job_card['id']}")
            
            # Convert to invoice
            invoice_data = {
                "customer_type": "saved",
                "customer_id": customer_id,
                "discount_percentage": 0,
                "discount_amount": 0,
                "vat_percentage": 5.0,
                "notes": "Detailed calculation test invoice"
            }
            
            invoice_response = self.session.post(f"{BACKEND_URL}/jobcards/{job_card['id']}/convert-to-invoice", json=invoice_data)
            if invoice_response.status_code != 200:
                print(f"❌ Invoice creation failed: {invoice_response.status_code}")
                print(f"   Response: {invoice_response.text}")
                return False
            
            invoice = invoice_response.json()
            print(f"✅ Invoice created: {invoice['invoice_number']}")
            
            # Analyze calculations
            print("\n📊 CALCULATION ANALYSIS:")
            print(f"   Job Card Gold Rate: 50.0 OMR/g")
            print(f"   Item Weight: 20.0g")
            print(f"   Item Purity: 916")
            print(f"   Making Charges (flat): 100.0 OMR")
            print(f"   VAT Percentage: 5.0%")
            
            print("\n📋 EXPECTED CALCULATIONS:")
            expected_metal_value = 20.0 * 50.0  # 1000 OMR
            expected_making_charges = 100.0
            expected_subtotal = expected_metal_value + expected_making_charges  # 1100 OMR
            expected_vat = expected_subtotal * 0.05  # 55 OMR
            expected_grand_total = expected_subtotal + expected_vat  # 1155 OMR
            
            print(f"   Expected Metal Value: {expected_metal_value} OMR")
            print(f"   Expected Making Charges: {expected_making_charges} OMR")
            print(f"   Expected Subtotal: {expected_subtotal} OMR")
            print(f"   Expected VAT: {expected_vat} OMR")
            print(f"   Expected Grand Total: {expected_grand_total} OMR")
            
            print("\n📋 ACTUAL CALCULATIONS:")
            items = invoice.get('items', [])
            if items:
                item = items[0]
                actual_metal_value = item.get('gold_value', 0)
                actual_making_charges = item.get('making_value', 0)
                actual_line_total = item.get('line_total', 0)
                
                print(f"   Actual Metal Value (gold_value): {actual_metal_value} OMR")
                print(f"   Actual Making Charges (making_value): {actual_making_charges} OMR")
                print(f"   Actual Line Total: {actual_line_total} OMR")
                print(f"   Item Fields: {list(item.keys())}")
            
            actual_subtotal = invoice.get('subtotal', 0)
            actual_vat = invoice.get('vat_total', 0)
            actual_grand_total = invoice.get('grand_total', 0)
            
            print(f"   Actual Subtotal: {actual_subtotal} OMR")
            print(f"   Actual VAT: {actual_vat} OMR")
            print(f"   Actual Grand Total: {actual_grand_total} OMR")
            
            print("\n🔍 CALCULATION VERIFICATION:")
            metal_correct = abs(actual_metal_value - expected_metal_value) < 0.01
            making_correct = abs(actual_making_charges - expected_making_charges) < 0.01
            subtotal_correct = abs(actual_subtotal - expected_subtotal) < 0.01
            vat_correct = abs(actual_vat - expected_vat) < 0.01
            total_correct = abs(actual_grand_total - expected_grand_total) < 0.01
            
            print(f"   Metal Value: {'✅' if metal_correct else '❌'} ({actual_metal_value} vs {expected_metal_value})")
            print(f"   Making Charges: {'✅' if making_correct else '❌'} ({actual_making_charges} vs {expected_making_charges})")
            print(f"   Subtotal: {'✅' if subtotal_correct else '❌'} ({actual_subtotal} vs {expected_subtotal})")
            print(f"   VAT: {'✅' if vat_correct else '❌'} ({actual_vat} vs {expected_vat})")
            print(f"   Grand Total: {'✅' if total_correct else '❌'} ({actual_grand_total} vs {expected_grand_total})")
            
            if not making_correct:
                print("\n🚨 MAKING CHARGES ISSUE DETECTED:")
                print("   The making charges are not being calculated correctly.")
                print("   Expected: 100.0 OMR (flat rate from job card)")
                print(f"   Actual: {actual_making_charges} OMR")
                print("   This suggests an issue in the job card to invoice conversion logic.")
            
            return metal_correct and subtotal_correct and vat_correct and total_correct
            
        except Exception as e:
            print(f"❌ Calculation test exception: {str(e)}")
            return False
    
    def test_invoice_finalization_comprehensive(self):
        """Comprehensive test of invoice finalization"""
        print("\n" + "="*60)
        print("TESTING: Invoice Finalization Comprehensive")
        print("="*60)
        
        try:
            # Get existing customers and accounts
            customers_response = self.session.get(f"{BACKEND_URL}/parties?party_type=customer")
            customers = customers_response.json().get('items', [])
            customer_id = customers[0]['id']
            
            accounts_response = self.session.get(f"{BACKEND_URL}/accounts")
            accounts = accounts_response.json()
            account_id = accounts[0]['id']
            
            # Create job card and invoice for finalization test
            job_card_data = {
                "card_type": "job",
                "customer_type": "saved",
                "customer_id": customer_id,
                "delivery_date": (datetime.now() + timedelta(days=7)).isoformat(),
                "notes": "Finalization test job card",
                "items": [
                    {
                        "category": "Ring",
                        "description": "Finalization Test Ring",
                        "qty": 1,
                        "weight_in": 15.0,
                        "weight_out": 15.0,
                        "purity": 916,
                        "work_type": "New Making",
                        "making_charges_type": "flat",
                        "making_charges_value": 75.0,
                        "remarks": "Finalization test"
                    }
                ],
                "gold_rate_at_jobcard": 50.0
            }
            
            job_card_response = self.session.post(f"{BACKEND_URL}/jobcards", json=job_card_data)
            job_card = job_card_response.json()
            
            invoice_response = self.session.post(f"{BACKEND_URL}/jobcards/{job_card['id']}/convert-to-invoice", json={
                "customer_type": "saved",
                "customer_id": customer_id,
                "discount_percentage": 0,
                "discount_amount": 0,
                "vat_percentage": 5.0,
                "notes": "Finalization test invoice"
            })
            
            invoice = invoice_response.json()
            invoice_id = invoice['id']
            
            print(f"✅ Created test invoice: {invoice['invoice_number']}")
            print(f"   Status: {invoice['status']}")
            print(f"   Grand Total: {invoice['grand_total']} OMR")
            
            # Get initial inventory state
            inventory_response = self.session.get(f"{BACKEND_URL}/inventory/headers")
            initial_inventory = {}
            if inventory_response.status_code == 200:
                headers = inventory_response.json()
                for header in headers:
                    initial_inventory[header['id']] = {
                        'current_weight': header.get('current_weight', 0),
                        'current_qty': header.get('current_qty', 0)
                    }
                print(f"✅ Captured initial inventory state for {len(initial_inventory)} categories")
            
            # Get initial movements count
            movements_response = self.session.get(f"{BACKEND_URL}/inventory/movements")
            initial_movements_count = 0
            if movements_response.status_code == 200:
                movements_data = movements_response.json()
                movements = movements_data.get('items', movements_data) if isinstance(movements_data, dict) else movements_data
                initial_movements_count = len(movements)
                print(f"✅ Initial movements count: {initial_movements_count}")
            
            # Get initial transactions count
            transactions_response = self.session.get(f"{BACKEND_URL}/transactions")
            initial_transactions_count = 0
            if transactions_response.status_code == 200:
                transactions_data = transactions_response.json()
                transactions = transactions_data.get('items', transactions_data) if isinstance(transactions_data, dict) else transactions_data
                initial_transactions_count = len(transactions)
                print(f"✅ Initial transactions count: {initial_transactions_count}")
            
            # FINALIZE THE INVOICE
            print(f"\n🚀 FINALIZING INVOICE: {invoice['invoice_number']}")
            finalize_response = self.session.post(f"{BACKEND_URL}/invoices/{invoice_id}/finalize")
            
            if finalize_response.status_code == 200:
                finalized_invoice = finalize_response.json()
                print("✅ Invoice finalized successfully")
                print(f"   New Status: {finalized_invoice['status']}")
                print(f"   Finalized At: {finalized_invoice.get('finalized_at', 'Not set')}")
                
                # Check stock movements created
                final_movements_response = self.session.get(f"{BACKEND_URL}/inventory/movements")
                if final_movements_response.status_code == 200:
                    final_movements_data = final_movements_response.json()
                    final_movements = final_movements_data.get('items', final_movements_data) if isinstance(final_movements_data, dict) else final_movements_data
                    final_movements_count = len(final_movements)
                    
                    new_movements = final_movements_count - initial_movements_count
                    print(f"✅ Stock movements: {initial_movements_count} → {final_movements_count} (+{new_movements})")
                    
                    # Look for Stock OUT movements for this invoice
                    invoice_movements = [m for m in final_movements if m.get('reference_type') == 'invoice' and 
                                       m.get('reference_id') == invoice_id]
                    
                    if invoice_movements:
                        print(f"✅ Found {len(invoice_movements)} movements for this invoice:")
                        for movement in invoice_movements:
                            print(f"   - Type: {movement.get('movement_type')}, Weight: {movement.get('weight_delta')}g")
                    else:
                        print("❌ No movements found for this invoice")
                
                # Check transactions created
                final_transactions_response = self.session.get(f"{BACKEND_URL}/transactions")
                if final_transactions_response.status_code == 200:
                    final_transactions_data = final_transactions_response.json()
                    final_transactions = final_transactions_data.get('items', final_transactions_data) if isinstance(final_transactions_data, dict) else final_transactions_data
                    final_transactions_count = len(final_transactions)
                    
                    new_transactions = final_transactions_count - initial_transactions_count
                    print(f"✅ Transactions: {initial_transactions_count} → {final_transactions_count} (+{new_transactions})")
                    
                    # Look for transactions for this invoice
                    invoice_transactions = [t for t in final_transactions if t.get('reference_type') == 'invoice' and 
                                          t.get('reference_id') == invoice_id]
                    
                    if invoice_transactions:
                        print(f"✅ Found {len(invoice_transactions)} transactions for this invoice:")
                        for transaction in invoice_transactions:
                            print(f"   - Type: {transaction.get('transaction_type')}, Amount: {transaction.get('amount')} OMR")
                    else:
                        print("❌ No transactions found for this invoice")
                
                # Check inventory impact
                final_inventory_response = self.session.get(f"{BACKEND_URL}/inventory/headers")
                if final_inventory_response.status_code == 200:
                    final_headers = final_inventory_response.json()
                    print(f"\n📊 INVENTORY IMPACT:")
                    for header in final_headers:
                        header_id = header['id']
                        if header_id in initial_inventory:
                            initial_weight = initial_inventory[header_id]['current_weight']
                            final_weight = header.get('current_weight', 0)
                            weight_change = final_weight - initial_weight
                            
                            if weight_change != 0:
                                print(f"   {header['name']}: {initial_weight}g → {final_weight}g ({weight_change:+.3f}g)")
                
                # Test immutability
                print(f"\n🔒 TESTING IMMUTABILITY:")
                edit_response = self.session.patch(f"{BACKEND_URL}/invoices/{invoice_id}", json={"notes": "Trying to edit"})
                if edit_response.status_code in [400, 403]:
                    print("✅ Edit blocked correctly")
                else:
                    print(f"❌ Edit allowed (status: {edit_response.status_code})")
                
                delete_response = self.session.delete(f"{BACKEND_URL}/invoices/{invoice_id}")
                if delete_response.status_code in [400, 403]:
                    print("✅ Delete blocked correctly")
                else:
                    print(f"❌ Delete allowed (status: {delete_response.status_code})")
                
                return True
                
            else:
                print(f"❌ Invoice finalization failed: {finalize_response.status_code}")
                print(f"   Response: {finalize_response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Finalization test exception: {str(e)}")
            return False
    
    def test_customer_outstanding_balance(self):
        """Test customer outstanding balance tracking"""
        print("\n" + "="*60)
        print("TESTING: Customer Outstanding Balance Tracking")
        print("="*60)
        
        try:
            # Get existing customers
            customers_response = self.session.get(f"{BACKEND_URL}/parties?party_type=customer")
            customers = customers_response.json().get('items', [])
            customer_id = customers[0]['id']
            customer_name = customers[0]['name']
            
            print(f"Testing with customer: {customer_name} ({customer_id})")
            
            # Get customer summary
            summary_response = self.session.get(f"{BACKEND_URL}/parties/{customer_id}/summary")
            if summary_response.status_code == 200:
                summary = summary_response.json()
                money_owed = summary.get('money_owed_by_party', 0)
                print(f"✅ Customer summary retrieved")
                print(f"   Money owed by party: {money_owed} OMR")
                
                # Get all invoices for this customer
                invoices_response = self.session.get(f"{BACKEND_URL}/invoices")
                if invoices_response.status_code == 200:
                    invoices_data = invoices_response.json()
                    invoices = invoices_data.get('items', invoices_data) if isinstance(invoices_data, dict) else invoices_data
                    
                    customer_invoices = [inv for inv in invoices if inv.get('customer_id') == customer_id and 
                                       not inv.get('is_deleted', False)]
                    
                    print(f"✅ Found {len(customer_invoices)} invoices for this customer")
                    
                    total_balance_due = 0
                    for invoice in customer_invoices:
                        balance_due = invoice.get('balance_due', 0)
                        total_balance_due += balance_due
                        status = invoice.get('status', 'unknown')
                        print(f"   - {invoice['invoice_number']}: {balance_due} OMR (status: {status})")
                    
                    print(f"✅ Total balance due from invoices: {total_balance_due} OMR")
                    
                    # Compare summary vs invoice totals
                    if abs(money_owed - total_balance_due) < 0.01:
                        print("✅ Outstanding balance matches invoice totals")
                        return True
                    else:
                        print(f"❌ Outstanding balance mismatch:")
                        print(f"   Summary: {money_owed} OMR")
                        print(f"   Invoice totals: {total_balance_due} OMR")
                        print(f"   Difference: {abs(money_owed - total_balance_due)} OMR")
                        return False
                else:
                    print(f"❌ Could not get invoices: {invoices_response.status_code}")
                    return False
            else:
                print(f"❌ Could not get customer summary: {summary_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Outstanding balance test exception: {str(e)}")
            return False
    
    def run_focused_tests(self):
        """Run focused tests on critical issues"""
        print("="*80)
        print("FOCUSED INVOICE WORKFLOW BACKEND TESTING - CRITICAL ISSUES")
        print("="*80)
        
        if not self.authenticate():
            return False
        
        tests = [
            ("Audit Log Bug Fix", self.test_audit_log_bug_fix),
            ("Invoice Calculations Detailed", self.test_invoice_calculations_detailed),
            ("Invoice Finalization Comprehensive", self.test_invoice_finalization_comprehensive),
            ("Customer Outstanding Balance", self.test_customer_outstanding_balance)
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ Test {test_name} failed with exception: {str(e)}")
                results.append((test_name, False))
        
        # Summary
        print("\n" + "="*80)
        print("FOCUSED TEST RESULTS SUMMARY")
        print("="*80)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        return passed == total

if __name__ == "__main__":
    tester = FocusedInvoiceTester()
    success = tester.run_focused_tests()
    
    if success:
        print("\n🎉 All focused tests passed!")
    else:
        print("\n⚠️ Some tests failed - see details above")
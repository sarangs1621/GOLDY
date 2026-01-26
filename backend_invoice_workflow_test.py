#!/usr/bin/env python3
"""
COMPREHENSIVE INVOICE WORKFLOW BACKEND TESTING

This script tests the complete invoice lifecycle backend functionality as requested:
- Authentication with admin/admin123
- Invoice creation from job card
- Draft invoice modifications
- Invoice finalization atomic operations
- Payment processing scenarios
- Invoice calculations accuracy
- Invoice immutability after finalization
- Abandoned draft testing
- Customer outstanding balance

CRITICAL TESTS TO EXECUTE:
Phase 1: Invoice Creation from Job Card
Phase 2: Draft Invoice Modifications
Phase 3: Invoice Finalization Atomic Operations
Phase 4: Payment Processing Scenarios
Phase 5: Invoice Calculations Accuracy
Phase 6: Invoice Immutability After Finalization
Phase 7: Abandoned Draft Testing
Phase 8: Customer Outstanding Balance
"""

import requests
import json
import sys
from datetime import datetime, timezone
from decimal import Decimal

# Backend URL from frontend/.env
BACKEND_URL = "https://decimal-precision.preview.emergentagent.com/api"

# Test credentials
USERNAME = "admin"
PASSWORD = "admin123"

class InvoiceWorkflowTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        self.created_entities = {
            'customers': [],
            'inventory_headers': [],
            'accounts': [],
            'job_cards': [],
            'invoices': [],
            'movements': [],
            'transactions': []
        }
        
    def log_result(self, phase, test_name, status, details=""):
        """Log test result"""
        result = {
            'phase': phase,
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_symbol} {phase} - {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
    
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
                self.log_result("AUTH", "Admin Login", "PASS", f"Token received: {self.token[:20]}...")
                return True
            else:
                self.log_result("AUTH", "Admin Login", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("AUTH", "Admin Login", "FAIL", f"Exception: {str(e)}")
            return False
    
    def setup_test_data(self):
        """Setup required test data if not exists"""
        try:
            # Create test customer if needed
            customers_response = self.session.get(f"{BACKEND_URL}/parties?party_type=customer")
            if customers_response.status_code == 200:
                customers_data = customers_response.json()
                customers = customers_data.get('items', [])
                if not customers:
                    # Create test customer
                    customer_data = {
                        "name": "Test Customer Invoice",
                        "party_type": "customer",
                        "phone": "99887766",
                        "address": "Test Address for Invoice Testing"
                    }
                    customer_response = self.session.post(f"{BACKEND_URL}/parties", json=customer_data)
                    if customer_response.status_code == 200:
                        customer = customer_response.json()
                        self.created_entities['customers'].append(customer['id'])
                        self.log_result("SETUP", "Create Test Customer", "PASS", f"Customer ID: {customer['id']}")
                    else:
                        self.log_result("SETUP", "Create Test Customer", "FAIL", customer_response.text)
                        return False
                else:
                    self.created_entities['customers'].append(customers[0]['id'])
                    self.log_result("SETUP", "Use Existing Customer", "PASS", f"Customer ID: {customers[0]['id']}")
            
            # Check inventory headers with initial stock
            inventory_response = self.session.get(f"{BACKEND_URL}/inventory/headers")
            if inventory_response.status_code == 200:
                headers = inventory_response.json()
                gold_header = None
                for header in headers:
                    if header.get('current_weight', 0) > 0:
                        gold_header = header
                        break
                
                if not gold_header:
                    # Create stock movement to add initial inventory
                    if headers:
                        header_id = headers[0]['id']
                        movement_data = {
                            "header_id": header_id,
                            "movement_type": "Stock IN",
                            "qty_delta": 10,
                            "weight_delta": 100.0,  # 100g gold
                            "purity": 916,
                            "description": "Initial stock for invoice testing",
                            "notes": "Test setup - 100g gold at 916 purity"
                        }
                        movement_response = self.session.post(f"{BACKEND_URL}/inventory/movements", json=movement_data)
                        if movement_response.status_code == 200:
                            self.log_result("SETUP", "Create Initial Stock", "PASS", "100g gold added")
                        else:
                            self.log_result("SETUP", "Create Initial Stock", "FAIL", movement_response.text)
                            return False
                else:
                    self.log_result("SETUP", "Existing Stock Found", "PASS", f"Weight: {gold_header.get('current_weight')}g")
            
            # Check cash/bank accounts with balance
            accounts_response = self.session.get(f"{BACKEND_URL}/accounts")
            if accounts_response.status_code == 200:
                accounts = accounts_response.json()
                cash_account = None
                for account in accounts:
                    if account.get('current_balance', 0) > 0:
                        cash_account = account
                        break
                
                if cash_account:
                    self.created_entities['accounts'].append(cash_account['id'])
                    self.log_result("SETUP", "Cash Account Found", "PASS", f"Balance: {cash_account.get('current_balance')} OMR")
                else:
                    # Create cash account with initial balance
                    account_data = {
                        "name": "Test Cash Account",
                        "account_type": "cash",
                        "opening_balance": 5000.0,
                        "current_balance": 5000.0,
                        "description": "Test cash account for invoice testing"
                    }
                    account_response = self.session.post(f"{BACKEND_URL}/accounts", json=account_data)
                    if account_response.status_code == 200:
                        account = account_response.json()
                        self.created_entities['accounts'].append(account['id'])
                        self.log_result("SETUP", "Create Cash Account", "PASS", f"Account ID: {account['id']}, Balance: 5000 OMR")
                    else:
                        self.log_result("SETUP", "Create Cash Account", "FAIL", account_response.text)
                        return False
            
            # Create job card with items for invoice conversion
            job_card_data = {
                "card_type": "job",  # Required field
                "customer_type": "saved",
                "customer_id": self.created_entities['customers'][0],
                "worker_id": None,
                "delivery_date": (datetime.now() + timedelta(days=7)).isoformat(),
                "notes": "Test job card for invoice workflow testing",
                "items": [
                    {
                        "category": "Ring",
                        "description": "Gold Ring 22K",
                        "qty": 1,
                        "weight_in": 20.0,
                        "weight_out": 20.0,
                        "purity": 916,
                        "work_type": "New Making",
                        "making_charges_type": "flat",
                        "making_charges_value": 100.0,
                        "remarks": "Test ring for invoice"
                    }
                ],
                "gold_rate_at_jobcard": 50.0  # 50 OMR per gram
            }
            
            job_card_response = self.session.post(f"{BACKEND_URL}/jobcards", json=job_card_data)
            if job_card_response.status_code == 200:
                job_card = job_card_response.json()
                self.created_entities['job_cards'].append(job_card['id'])
                self.log_result("SETUP", "Create Test Job Card", "PASS", f"Job Card ID: {job_card['id']}")
            else:
                self.log_result("SETUP", "Create Test Job Card", "FAIL", job_card_response.text)
                return False
            
            return True
            
        except Exception as e:
            self.log_result("SETUP", "Test Data Setup", "FAIL", f"Exception: {str(e)}")
            return False
    
    def phase1_invoice_creation_from_job_card(self):
        """Phase 1: Invoice Creation from Job Card"""
        try:
            job_card_id = self.created_entities['job_cards'][0]
            
            # Create invoice from job card
            invoice_data = {
                "customer_type": "saved",
                "customer_id": self.created_entities['customers'][0],
                "discount_percentage": 0,
                "discount_amount": 0,
                "vat_percentage": 5.0,
                "notes": "Test invoice from job card"
            }
            
            response = self.session.post(f"{BACKEND_URL}/jobcards/{job_card_id}/convert-to-invoice", json=invoice_data)
            
            if response.status_code == 200:
                invoice = response.json()
                self.created_entities['invoices'].append(invoice['id'])
                
                # Verify invoice created with status='draft'
                if invoice.get('status') == 'draft':
                    self.log_result("PHASE1", "Invoice Status Draft", "PASS", "Status correctly set to 'draft'")
                else:
                    self.log_result("PHASE1", "Invoice Status Draft", "FAIL", f"Status: {invoice.get('status')}")
                
                # Verify items mapped correctly from job card
                items = invoice.get('items', [])
                if len(items) > 0:
                    item = items[0]
                    if item.get('weight_grams') == 20.0 and item.get('purity') == 916:
                        self.log_result("PHASE1", "Items Mapping", "PASS", "Items correctly mapped from job card")
                    else:
                        self.log_result("PHASE1", "Items Mapping", "FAIL", f"Weight: {item.get('weight_grams')}, Purity: {item.get('purity')}")
                else:
                    self.log_result("PHASE1", "Items Mapping", "FAIL", "No items found in invoice")
                
                # Verify calculations
                expected_metal_value = 20.0 * 50.0  # weight × gold_rate = 1000 OMR
                expected_making_charges = 100.0
                expected_subtotal = expected_metal_value + expected_making_charges  # 1100 OMR
                expected_vat = expected_subtotal * 0.05  # 55 OMR
                expected_grand_total = expected_subtotal + expected_vat  # 1155 OMR
                
                actual_subtotal = invoice.get('subtotal', 0)
                actual_vat = invoice.get('vat_total', 0)
                actual_grand_total = invoice.get('grand_total', 0)
                
                if abs(actual_grand_total - expected_grand_total) < 0.01:
                    self.log_result("PHASE1", "Calculations Accuracy", "PASS", 
                                  f"Grand Total: {actual_grand_total} OMR (Expected: {expected_grand_total})")
                else:
                    self.log_result("PHASE1", "Calculations Accuracy", "FAIL", 
                                  f"Grand Total: {actual_grand_total} OMR (Expected: {expected_grand_total})")
                
                # Verify NO inventory impact (draft state)
                inventory_response = self.session.get(f"{BACKEND_URL}/inventory/movements")
                if inventory_response.status_code == 200:
                    movements = inventory_response.json().get('data', [])
                    stock_out_movements = [m for m in movements if m.get('movement_type') == 'Stock OUT' and 
                                         m.get('reference_type') == 'invoice' and m.get('reference_id') == invoice['id']]
                    
                    if len(stock_out_movements) == 0:
                        self.log_result("PHASE1", "No Inventory Impact Draft", "PASS", "No Stock OUT movements for draft invoice")
                    else:
                        self.log_result("PHASE1", "No Inventory Impact Draft", "FAIL", f"Found {len(stock_out_movements)} Stock OUT movements")
                
                # Verify NO financial impact (draft state)
                transactions_response = self.session.get(f"{BACKEND_URL}/transactions")
                if transactions_response.status_code == 200:
                    transactions = transactions_response.json().get('data', [])
                    invoice_transactions = [t for t in transactions if t.get('reference_type') == 'invoice' and 
                                          t.get('reference_id') == invoice['id']]
                    
                    if len(invoice_transactions) == 0:
                        self.log_result("PHASE1", "No Financial Impact Draft", "PASS", "No transactions for draft invoice")
                    else:
                        self.log_result("PHASE1", "No Financial Impact Draft", "FAIL", f"Found {len(invoice_transactions)} transactions")
                
                return True
                
            else:
                self.log_result("PHASE1", "Invoice Creation", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("PHASE1", "Invoice Creation from Job Card", "FAIL", f"Exception: {str(e)}")
            return False
    
    def phase2_draft_invoice_modifications(self):
        """Phase 2: Draft Invoice Modifications"""
        try:
            if not self.created_entities['invoices']:
                self.log_result("PHASE2", "Draft Modifications", "SKIP", "No invoices to test")
                return False
            
            invoice_id = self.created_entities['invoices'][0]
            
            # GET invoice to verify draft badge
            get_response = self.session.get(f"{BACKEND_URL}/invoices/{invoice_id}")
            if get_response.status_code == 200:
                invoice = get_response.json()
                if invoice.get('status') == 'draft':
                    self.log_result("PHASE2", "Draft Badge Verification", "PASS", "Invoice status is 'draft'")
                else:
                    self.log_result("PHASE2", "Draft Badge Verification", "FAIL", f"Status: {invoice.get('status')}")
            
            # PUT request to modify draft invoice
            update_data = {
                "notes": "Updated notes for draft invoice testing",
                "discount_percentage": 5.0,
                "discount_amount": 57.75  # 5% of 1155 OMR
            }
            
            update_response = self.session.patch(f"{BACKEND_URL}/invoices/{invoice_id}", json=update_data)
            if update_response.status_code == 200:
                self.log_result("PHASE2", "Draft Invoice Update", "PASS", "Draft invoice updated successfully")
                
                # Verify changes saved correctly
                verify_response = self.session.get(f"{BACKEND_URL}/invoices/{invoice_id}")
                if verify_response.status_code == 200:
                    updated_invoice = verify_response.json()
                    if (updated_invoice.get('notes') == update_data['notes'] and 
                        abs(updated_invoice.get('discount_percentage', 0) - update_data['discount_percentage']) < 0.01):
                        self.log_result("PHASE2", "Changes Verification", "PASS", "Changes saved correctly")
                    else:
                        self.log_result("PHASE2", "Changes Verification", "FAIL", "Changes not saved correctly")
            else:
                self.log_result("PHASE2", "Draft Invoice Update", "FAIL", f"Status: {update_response.status_code}")
            
            # Test DELETE draft invoice (create a new one first)
            # Create another draft invoice for deletion test
            job_card_id = self.created_entities['job_cards'][0]
            delete_invoice_data = {
                "customer_type": "saved",
                "customer_id": self.created_entities['customers'][0],
                "discount_percentage": 0,
                "discount_amount": 0,
                "vat_percentage": 5.0,
                "notes": "Invoice for deletion test"
            }
            
            create_response = self.session.post(f"{BACKEND_URL}/jobcards/{job_card_id}/convert-to-invoice", json=delete_invoice_data)
            if create_response.status_code == 200:
                delete_invoice = create_response.json()
                delete_invoice_id = delete_invoice['id']
                
                # Delete the draft invoice
                delete_response = self.session.delete(f"{BACKEND_URL}/invoices/{delete_invoice_id}")
                if delete_response.status_code == 200:
                    self.log_result("PHASE2", "Draft Invoice Deletion", "PASS", "Draft invoice deleted successfully")
                    
                    # Verify deletion - should return 404
                    verify_delete_response = self.session.get(f"{BACKEND_URL}/invoices/{delete_invoice_id}")
                    if verify_delete_response.status_code == 404:
                        self.log_result("PHASE2", "Deletion Verification", "PASS", "Deleted invoice not found (404)")
                    else:
                        self.log_result("PHASE2", "Deletion Verification", "FAIL", f"Status: {verify_delete_response.status_code}")
                else:
                    self.log_result("PHASE2", "Draft Invoice Deletion", "FAIL", f"Status: {delete_response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_result("PHASE2", "Draft Invoice Modifications", "FAIL", f"Exception: {str(e)}")
            return False
    
    def phase3_invoice_finalization_atomic_operations(self):
        """Phase 3: Invoice Finalization Atomic Operations"""
        try:
            if not self.created_entities['invoices']:
                self.log_result("PHASE3", "Finalization", "SKIP", "No invoices to test")
                return False
            
            invoice_id = self.created_entities['invoices'][0]
            
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
            
            # Get initial account balance
            account_id = self.created_entities['accounts'][0]
            account_response = self.session.get(f"{BACKEND_URL}/accounts/{account_id}")
            initial_balance = 0
            if account_response.status_code == 200:
                account = account_response.json()
                initial_balance = account.get('current_balance', 0)
            
            # Finalize invoice with payment details
            finalize_response = self.session.post(f"{BACKEND_URL}/invoices/{invoice_id}/finalize")
            
            if finalize_response.status_code == 200:
                finalized_invoice = finalize_response.json()
                
                # Verify invoice status changed to 'finalized'
                if finalized_invoice.get('status') == 'finalized':
                    self.log_result("PHASE3", "Status Change to Finalized", "PASS", "Status correctly changed to 'finalized'")
                else:
                    self.log_result("PHASE3", "Status Change to Finalized", "FAIL", f"Status: {finalized_invoice.get('status')}")
                
                # Verify Stock OUT movement created
                movements_response = self.session.get(f"{BACKEND_URL}/inventory/movements")
                if movements_response.status_code == 200:
                    movements = movements_response.json().get('data', [])
                    stock_out_movements = [m for m in movements if m.get('movement_type') == 'Stock OUT' and 
                                         m.get('reference_type') == 'invoice' and m.get('reference_id') == invoice_id]
                    
                    if len(stock_out_movements) > 0:
                        movement = stock_out_movements[0]
                        if movement.get('weight_delta') < 0:  # Should be negative for Stock OUT
                            self.log_result("PHASE3", "Stock OUT Movement Created", "PASS", 
                                          f"Weight Delta: {movement.get('weight_delta')}g")
                        else:
                            self.log_result("PHASE3", "Stock OUT Movement Created", "FAIL", 
                                          f"Weight Delta should be negative: {movement.get('weight_delta')}")
                    else:
                        self.log_result("PHASE3", "Stock OUT Movement Created", "FAIL", "No Stock OUT movement found")
                
                # Verify inventory header current_weight decreased
                final_inventory_response = self.session.get(f"{BACKEND_URL}/inventory/headers")
                if final_inventory_response.status_code == 200:
                    final_headers = final_inventory_response.json()
                    weight_decreased = False
                    for header in final_headers:
                        header_id = header['id']
                        if header_id in initial_inventory:
                            initial_weight = initial_inventory[header_id]['current_weight']
                            final_weight = header.get('current_weight', 0)
                            if final_weight < initial_weight:
                                weight_decreased = True
                                self.log_result("PHASE3", "Inventory Weight Decrease", "PASS", 
                                              f"Weight: {initial_weight}g → {final_weight}g")
                                break
                    
                    if not weight_decreased:
                        self.log_result("PHASE3", "Inventory Weight Decrease", "FAIL", "No weight decrease detected")
                
                # Verify Finance transaction created
                transactions_response = self.session.get(f"{BACKEND_URL}/transactions")
                if transactions_response.status_code == 200:
                    transactions = transactions_response.json().get('data', [])
                    invoice_transactions = [t for t in transactions if t.get('reference_type') == 'invoice' and 
                                          t.get('reference_id') == invoice_id]
                    
                    if len(invoice_transactions) > 0:
                        transaction = invoice_transactions[0]
                        if transaction.get('transaction_type') == 'credit':
                            self.log_result("PHASE3", "Finance Transaction Created", "PASS", 
                                          f"Type: {transaction.get('transaction_type')}, Amount: {transaction.get('amount')}")
                        else:
                            self.log_result("PHASE3", "Finance Transaction Created", "FAIL", 
                                          f"Expected credit, got: {transaction.get('transaction_type')}")
                    else:
                        self.log_result("PHASE3", "Finance Transaction Created", "FAIL", "No transaction found")
                
                # Verify Job Card status updated (if applicable)
                if finalized_invoice.get('jobcard_id'):
                    jobcard_response = self.session.get(f"{BACKEND_URL}/jobcards/{finalized_invoice['jobcard_id']}")
                    if jobcard_response.status_code == 200:
                        jobcard = jobcard_response.json()
                        if jobcard.get('locked', False):
                            self.log_result("PHASE3", "Job Card Locked", "PASS", "Job card locked after invoice finalization")
                        else:
                            self.log_result("PHASE3", "Job Card Locked", "FAIL", "Job card not locked")
                
                # Verify audit logs created
                audit_response = self.session.get(f"{BACKEND_URL}/audit-logs")
                if audit_response.status_code == 200:
                    audit_logs = audit_response.json().get('data', [])
                    finalize_logs = [log for log in audit_logs if log.get('module') == 'invoice' and 
                                   log.get('record_id') == invoice_id and log.get('action') == 'finalize']
                    
                    if len(finalize_logs) > 0:
                        self.log_result("PHASE3", "Audit Logs Created", "PASS", f"Found {len(finalize_logs)} audit log(s)")
                    else:
                        self.log_result("PHASE3", "Audit Logs Created", "FAIL", "No finalize audit logs found")
                
                return True
                
            else:
                self.log_result("PHASE3", "Invoice Finalization", "FAIL", f"Status: {finalize_response.status_code}, Response: {finalize_response.text}")
                return False
                
        except Exception as e:
            self.log_result("PHASE3", "Invoice Finalization Atomic Operations", "FAIL", f"Exception: {str(e)}")
            return False
    
    def phase4_payment_processing_scenarios(self):
        """Phase 4: Payment Processing Scenarios"""
        try:
            # Test Case A - Full Payment
            job_card_id = self.created_entities['job_cards'][0]
            
            # Create invoice for full payment test
            full_payment_invoice_data = {
                "customer_type": "saved",
                "customer_id": self.created_entities['customers'][0],
                "discount_percentage": 0,
                "discount_amount": 0,
                "vat_percentage": 5.0,
                "notes": "Full payment test invoice"
            }
            
            full_payment_response = self.session.post(f"{BACKEND_URL}/jobcards/{job_card_id}/convert-to-invoice", json=full_payment_invoice_data)
            if full_payment_response.status_code == 200:
                full_payment_invoice = full_payment_response.json()
                grand_total = full_payment_invoice.get('grand_total', 0)
                
                # Add full payment
                payment_data = {
                    "amount": grand_total,
                    "payment_mode": "Cash",
                    "account_id": self.created_entities['accounts'][0],
                    "notes": "Full payment test"
                }
                
                payment_response = self.session.post(f"{BACKEND_URL}/invoices/{full_payment_invoice['id']}/add-payment", json=payment_data)
                if payment_response.status_code == 200:
                    # Verify balance_due = 0
                    verify_response = self.session.get(f"{BACKEND_URL}/invoices/{full_payment_invoice['id']}")
                    if verify_response.status_code == 200:
                        updated_invoice = verify_response.json()
                        balance_due = updated_invoice.get('balance_due', 0)
                        if abs(balance_due) < 0.01:
                            self.log_result("PHASE4", "Full Payment Balance Due", "PASS", f"Balance Due: {balance_due} OMR")
                        else:
                            self.log_result("PHASE4", "Full Payment Balance Due", "FAIL", f"Balance Due: {balance_due} OMR (Expected: 0)")
                else:
                    self.log_result("PHASE4", "Full Payment Processing", "FAIL", f"Status: {payment_response.status_code}")
            
            # Test Case B - Partial Payment
            partial_payment_response = self.session.post(f"{BACKEND_URL}/jobcards/{job_card_id}/convert-to-invoice", json={
                "customer_type": "saved",
                "customer_id": self.created_entities['customers'][0],
                "discount_percentage": 0,
                "discount_amount": 0,
                "vat_percentage": 5.0,
                "notes": "Partial payment test invoice"
            })
            
            if partial_payment_response.status_code == 200:
                partial_payment_invoice = partial_payment_response.json()
                grand_total = partial_payment_invoice.get('grand_total', 0)
                partial_amount = grand_total * 0.6  # 60% payment
                
                # Add partial payment
                partial_payment_data = {
                    "amount": partial_amount,
                    "payment_mode": "Cash",
                    "account_id": self.created_entities['accounts'][0],
                    "notes": "Partial payment test - 60%"
                }
                
                partial_payment_response = self.session.post(f"{BACKEND_URL}/invoices/{partial_payment_invoice['id']}/add-payment", json=partial_payment_data)
                if partial_payment_response.status_code == 200:
                    # Verify balance_due = 40% of grand_total
                    verify_response = self.session.get(f"{BACKEND_URL}/invoices/{partial_payment_invoice['id']}")
                    if verify_response.status_code == 200:
                        updated_invoice = verify_response.json()
                        balance_due = updated_invoice.get('balance_due', 0)
                        expected_balance = grand_total - partial_amount
                        
                        if abs(balance_due - expected_balance) < 0.01:
                            self.log_result("PHASE4", "Partial Payment Balance Due", "PASS", 
                                          f"Balance Due: {balance_due} OMR (Expected: {expected_balance})")
                        else:
                            self.log_result("PHASE4", "Partial Payment Balance Due", "FAIL", 
                                          f"Balance Due: {balance_due} OMR (Expected: {expected_balance})")
                        
                        # Verify customer receivable tracking
                        customer_id = self.created_entities['customers'][0]
                        customer_summary_response = self.session.get(f"{BACKEND_URL}/parties/{customer_id}/summary")
                        if customer_summary_response.status_code == 200:
                            summary = customer_summary_response.json()
                            money_owed = summary.get('money_owed_by_party', 0)
                            if money_owed > 0:
                                self.log_result("PHASE4", "Customer Receivable Tracking", "PASS", 
                                              f"Money Owed: {money_owed} OMR")
                            else:
                                self.log_result("PHASE4", "Customer Receivable Tracking", "FAIL", 
                                              f"Money Owed: {money_owed} OMR")
                else:
                    self.log_result("PHASE4", "Partial Payment Processing", "FAIL", f"Status: {partial_payment_response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_result("PHASE4", "Payment Processing Scenarios", "FAIL", f"Exception: {str(e)}")
            return False
    
    def phase5_invoice_calculations_accuracy(self):
        """Phase 5: Invoice Calculations Accuracy"""
        try:
            # Test with specific values as mentioned in review request
            # Item 1: Weight 20g, Purity 916, Gold Rate 50 OMR/g, Making Flat 100 OMR
            
            # Create specific job card for calculation test
            calc_job_card_data = {
                "card_type": "job",  # Required field
                "customer_type": "saved",
                "customer_id": self.created_entities['customers'][0],
                "worker_id": None,
                "delivery_date": (datetime.now() + timedelta(days=7)).isoformat(),
                "notes": "Calculation accuracy test job card",
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
                        "remarks": "Calculation test item"
                    }
                ],
                "gold_rate_at_jobcard": 50.0  # 50 OMR per gram
            }
            
            calc_job_card_response = self.session.post(f"{BACKEND_URL}/jobcards", json=calc_job_card_data)
            if calc_job_card_response.status_code == 200:
                calc_job_card = calc_job_card_response.json()
                
                # Create invoice from this job card
                calc_invoice_data = {
                    "customer_type": "saved",
                    "customer_id": self.created_entities['customers'][0],
                    "discount_percentage": 0,
                    "discount_amount": 0,
                    "vat_percentage": 5.0,
                    "notes": "Calculation accuracy test invoice"
                }
                
                calc_invoice_response = self.session.post(f"{BACKEND_URL}/jobcards/{calc_job_card['id']}/convert-to-invoice", json=calc_invoice_data)
                if calc_invoice_response.status_code == 200:
                    calc_invoice = calc_invoice_response.json()
                    
                    # Expected calculations:
                    # Expected metal_value: 20 × 50 = 1000 OMR
                    # Expected making_charges: 100 OMR
                    # Expected subtotal: 1100 OMR
                    # Expected VAT (5%): 55 OMR
                    # Expected grand_total: 1155 OMR
                    
                    expected_metal_value = 20.0 * 50.0  # 1000 OMR
                    expected_making_charges = 100.0
                    expected_subtotal = expected_metal_value + expected_making_charges  # 1100 OMR
                    expected_vat = expected_subtotal * 0.05  # 55 OMR
                    expected_grand_total = expected_subtotal + expected_vat  # 1155 OMR
                    
                    # Get actual values
                    actual_subtotal = calc_invoice.get('subtotal', 0)
                    actual_vat = calc_invoice.get('vat_total', 0)
                    actual_grand_total = calc_invoice.get('grand_total', 0)
                    
                    # Verify metal value calculation
                    items = calc_invoice.get('items', [])
                    if items:
                        item = items[0]
                        actual_metal_value = item.get('metal_value', 0)
                        if abs(actual_metal_value - expected_metal_value) < 0.01:
                            self.log_result("PHASE5", "Metal Value Calculation", "PASS", 
                                          f"Metal Value: {actual_metal_value} OMR (Expected: {expected_metal_value})")
                        else:
                            self.log_result("PHASE5", "Metal Value Calculation", "FAIL", 
                                          f"Metal Value: {actual_metal_value} OMR (Expected: {expected_metal_value})")
                        
                        # Verify making charges
                        actual_making_charges = item.get('making_charges', 0)
                        if abs(actual_making_charges - expected_making_charges) < 0.01:
                            self.log_result("PHASE5", "Making Charges Calculation", "PASS", 
                                          f"Making Charges: {actual_making_charges} OMR (Expected: {expected_making_charges})")
                        else:
                            self.log_result("PHASE5", "Making Charges Calculation", "FAIL", 
                                          f"Making Charges: {actual_making_charges} OMR (Expected: {expected_making_charges})")
                    
                    # Verify subtotal
                    if abs(actual_subtotal - expected_subtotal) < 0.01:
                        self.log_result("PHASE5", "Subtotal Calculation", "PASS", 
                                      f"Subtotal: {actual_subtotal} OMR (Expected: {expected_subtotal})")
                    else:
                        self.log_result("PHASE5", "Subtotal Calculation", "FAIL", 
                                      f"Subtotal: {actual_subtotal} OMR (Expected: {expected_subtotal})")
                    
                    # Verify VAT
                    if abs(actual_vat - expected_vat) < 0.01:
                        self.log_result("PHASE5", "VAT Calculation", "PASS", 
                                      f"VAT: {actual_vat} OMR (Expected: {expected_vat})")
                    else:
                        self.log_result("PHASE5", "VAT Calculation", "FAIL", 
                                      f"VAT: {actual_vat} OMR (Expected: {expected_vat})")
                    
                    # Verify grand total
                    if abs(actual_grand_total - expected_grand_total) < 0.01:
                        self.log_result("PHASE5", "Grand Total Calculation", "PASS", 
                                      f"Grand Total: {actual_grand_total} OMR (Expected: {expected_grand_total})")
                    else:
                        self.log_result("PHASE5", "Grand Total Calculation", "FAIL", 
                                      f"Grand Total: {actual_grand_total} OMR (Expected: {expected_grand_total})")
                    
                    return True
                else:
                    self.log_result("PHASE5", "Calculation Test Invoice Creation", "FAIL", f"Status: {calc_invoice_response.status_code}")
            else:
                self.log_result("PHASE5", "Calculation Test Job Card Creation", "FAIL", f"Status: {calc_job_card_response.status_code}")
            
            return False
            
        except Exception as e:
            self.log_result("PHASE5", "Invoice Calculations Accuracy", "FAIL", f"Exception: {str(e)}")
            return False
    
    def phase6_invoice_immutability_after_finalization(self):
        """Phase 6: Invoice Immutability After Finalization"""
        try:
            if not self.created_entities['invoices']:
                self.log_result("PHASE6", "Immutability Test", "SKIP", "No finalized invoices to test")
                return False
            
            # Use the first invoice which should be finalized from Phase 3
            finalized_invoice_id = self.created_entities['invoices'][0]
            
            # Verify invoice is finalized
            get_response = self.session.get(f"{BACKEND_URL}/invoices/{finalized_invoice_id}")
            if get_response.status_code == 200:
                invoice = get_response.json()
                if invoice.get('status') != 'finalized':
                    self.log_result("PHASE6", "Invoice Status Check", "SKIP", f"Invoice not finalized: {invoice.get('status')}")
                    return False
            
            # Attempt PUT request to edit finalized invoice
            edit_data = {
                "notes": "Attempting to edit finalized invoice",
                "discount_percentage": 10.0
            }
            
            edit_response = self.session.patch(f"{BACKEND_URL}/invoices/{finalized_invoice_id}", json=edit_data)
            if edit_response.status_code in [400, 403]:
                self.log_result("PHASE6", "Edit Finalized Invoice Blocked", "PASS", 
                              f"Edit blocked with status {edit_response.status_code}")
            else:
                self.log_result("PHASE6", "Edit Finalized Invoice Blocked", "FAIL", 
                              f"Edit allowed with status {edit_response.status_code}")
            
            # Attempt DELETE finalized invoice
            delete_response = self.session.delete(f"{BACKEND_URL}/invoices/{finalized_invoice_id}")
            if delete_response.status_code in [400, 403]:
                self.log_result("PHASE6", "Delete Finalized Invoice Blocked", "PASS", 
                              f"Delete blocked with status {delete_response.status_code}")
            else:
                self.log_result("PHASE6", "Delete Finalized Invoice Blocked", "FAIL", 
                              f"Delete allowed with status {delete_response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_result("PHASE6", "Invoice Immutability After Finalization", "FAIL", f"Exception: {str(e)}")
            return False
    
    def phase7_abandoned_draft_testing(self):
        """Phase 7: Abandoned Draft Testing"""
        try:
            # Create draft invoice
            job_card_id = self.created_entities['job_cards'][0]
            
            abandoned_invoice_data = {
                "customer_type": "saved",
                "customer_id": self.created_entities['customers'][0],
                "discount_percentage": 0,
                "discount_amount": 0,
                "vat_percentage": 5.0,
                "notes": "Abandoned draft test invoice"
            }
            
            abandoned_response = self.session.post(f"{BACKEND_URL}/jobcards/{job_card_id}/convert-to-invoice", json=abandoned_invoice_data)
            if abandoned_response.status_code == 200:
                abandoned_invoice = abandoned_response.json()
                abandoned_invoice_id = abandoned_invoice['id']
                
                # Leave it without finalizing and delete it
                delete_response = self.session.delete(f"{BACKEND_URL}/invoices/{abandoned_invoice_id}")
                if delete_response.status_code == 200:
                    self.log_result("PHASE7", "Abandoned Draft Deletion", "PASS", "Draft deleted successfully")
                    
                    # Verify draft can be deleted without affecting inventory
                    movements_response = self.session.get(f"{BACKEND_URL}/inventory/movements")
                    if movements_response.status_code == 200:
                        movements = movements_response.json().get('data', [])
                        abandoned_movements = [m for m in movements if m.get('reference_type') == 'invoice' and 
                                             m.get('reference_id') == abandoned_invoice_id]
                        
                        if len(abandoned_movements) == 0:
                            self.log_result("PHASE7", "No Inventory Impact on Deletion", "PASS", "No movements created for abandoned draft")
                        else:
                            self.log_result("PHASE7", "No Inventory Impact on Deletion", "FAIL", f"Found {len(abandoned_movements)} movements")
                    
                    # Verify no finance impact
                    transactions_response = self.session.get(f"{BACKEND_URL}/transactions")
                    if transactions_response.status_code == 200:
                        transactions = transactions_response.json().get('data', [])
                        abandoned_transactions = [t for t in transactions if t.get('reference_type') == 'invoice' and 
                                                t.get('reference_id') == abandoned_invoice_id]
                        
                        if len(abandoned_transactions) == 0:
                            self.log_result("PHASE7", "No Finance Impact on Deletion", "PASS", "No transactions created for abandoned draft")
                        else:
                            self.log_result("PHASE7", "No Finance Impact on Deletion", "FAIL", f"Found {len(abandoned_transactions)} transactions")
                    
                    return True
                else:
                    self.log_result("PHASE7", "Abandoned Draft Deletion", "FAIL", f"Status: {delete_response.status_code}")
            else:
                self.log_result("PHASE7", "Abandoned Draft Creation", "FAIL", f"Status: {abandoned_response.status_code}")
            
            return False
            
        except Exception as e:
            self.log_result("PHASE7", "Abandoned Draft Testing", "FAIL", f"Exception: {str(e)}")
            return False
    
    def phase8_customer_outstanding_balance(self):
        """Phase 8: Customer Outstanding Balance"""
        try:
            customer_id = self.created_entities['customers'][0]
            
            # Get customer summary to check outstanding balance
            summary_response = self.session.get(f"{BACKEND_URL}/parties/{customer_id}/summary")
            if summary_response.status_code == 200:
                summary = summary_response.json()
                money_owed = summary.get('money_owed_by_party', 0)
                
                if money_owed > 0:
                    self.log_result("PHASE8", "Customer Outstanding Balance", "PASS", 
                                  f"Outstanding Balance: {money_owed} OMR")
                    
                    # Verify this matches invoice balance_due totals
                    invoices_response = self.session.get(f"{BACKEND_URL}/invoices")
                    if invoices_response.status_code == 200:
                        invoices = invoices_response.json().get('data', [])
                        customer_invoices = [inv for inv in invoices if inv.get('customer_id') == customer_id and 
                                           not inv.get('is_deleted', False)]
                        
                        total_balance_due = sum(inv.get('balance_due', 0) for inv in customer_invoices)
                        
                        if abs(money_owed - total_balance_due) < 0.01:
                            self.log_result("PHASE8", "Outstanding Balance Accuracy", "PASS", 
                                          f"Summary: {money_owed} OMR, Invoice Total: {total_balance_due} OMR")
                        else:
                            self.log_result("PHASE8", "Outstanding Balance Accuracy", "FAIL", 
                                          f"Summary: {money_owed} OMR, Invoice Total: {total_balance_due} OMR")
                else:
                    self.log_result("PHASE8", "Customer Outstanding Balance", "INFO", 
                                  f"No outstanding balance: {money_owed} OMR")
                
                return True
            else:
                self.log_result("PHASE8", "Customer Summary Retrieval", "FAIL", f"Status: {summary_response.status_code}")
                return False
            
        except Exception as e:
            self.log_result("PHASE8", "Customer Outstanding Balance", "FAIL", f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all invoice workflow tests"""
        print("=" * 80)
        print("COMPREHENSIVE INVOICE WORKFLOW BACKEND TESTING")
        print("=" * 80)
        
        # Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Test data setup failed. Cannot proceed with tests.")
            return False
        
        # Run all phases
        phases = [
            ("Phase 1: Invoice Creation from Job Card", self.phase1_invoice_creation_from_job_card),
            ("Phase 2: Draft Invoice Modifications", self.phase2_draft_invoice_modifications),
            ("Phase 3: Invoice Finalization Atomic Operations", self.phase3_invoice_finalization_atomic_operations),
            ("Phase 4: Payment Processing Scenarios", self.phase4_payment_processing_scenarios),
            ("Phase 5: Invoice Calculations Accuracy", self.phase5_invoice_calculations_accuracy),
            ("Phase 6: Invoice Immutability After Finalization", self.phase6_invoice_immutability_after_finalization),
            ("Phase 7: Abandoned Draft Testing", self.phase7_abandoned_draft_testing),
            ("Phase 8: Customer Outstanding Balance", self.phase8_customer_outstanding_balance)
        ]
        
        for phase_name, phase_func in phases:
            print(f"\n{'-' * 60}")
            print(f"RUNNING: {phase_name}")
            print(f"{'-' * 60}")
            phase_func()
        
        # Print summary
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 80)
        print("TEST RESULTS SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        skipped_tests = len([r for r in self.test_results if r['status'] in ['SKIP', 'INFO']])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️ Skipped/Info: {skipped_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"   - {result['phase']} - {result['test']}: {result['details']}")
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    from datetime import timedelta
    
    tester = InvoiceWorkflowTester()
    success = tester.run_all_tests()
    
    if success:
        print("✅ Invoice workflow testing completed successfully!")
    else:
        print("❌ Invoice workflow testing failed!")
        sys.exit(1)
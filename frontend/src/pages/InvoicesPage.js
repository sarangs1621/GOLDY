import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { FileText, Printer, CheckCircle, Lock, DollarSign, AlertTriangle, Eye, Trash2 } from 'lucide-react';
import { ConfirmationDialog } from '../components/ConfirmationDialog';
import jsPDF from 'jspdf';
import 'jspdf-autotable';

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [finalizing, setFinalizing] = useState(null);
  const [showPaymentDialog, setShowPaymentDialog] = useState(false);
  const [showViewDialog, setShowViewDialog] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [viewInvoice, setViewInvoice] = useState(null);
  const [paymentData, setPaymentData] = useState({
    amount: '',
    payment_mode: 'Cash',
    account_id: '',
    notes: '',
    // Gold exchange specific fields
    gold_weight_grams: '',
    rate_per_gram: '',
    purity_entered: '916'
  });

  useEffect(() => {
    loadInvoices();
    loadAccounts();
  }, []);

  const loadInvoices = async () => {
    try {
      const response = await axios.get(`${API}/invoices`);
      setInvoices(response.data.items || []);
    } catch (error) {
      toast.error('Failed to load invoices');
    }
  };

  const loadAccounts = async () => {
    try {
      const response = await axios.get(`${API}/accounts`);
      setAccounts(response.data);
    } catch (error) {
      console.error('Failed to load accounts:', error);
    }
  };

  const handlePrintInvoice = (invoice) => {
    try {
      const doc = new jsPDF();
      
      // Header
      doc.setFontSize(20);
      doc.setFont(undefined, 'bold');
      doc.text('Gold Shop ERP', 105, 20, { align: 'center' });
      
      doc.setFontSize(14);
      doc.text('TAX INVOICE', 105, 30, { align: 'center' });
      
      // Invoice Details
      doc.setFontSize(10);
      doc.setFont(undefined, 'normal');
      doc.text(`Invoice #: ${invoice.invoice_number || 'N/A'}`, 20, 45);
      doc.text(`Date: ${invoice.date ? new Date(invoice.date).toLocaleDateString() : 'N/A'}`, 20, 52);
      doc.text(`Customer: ${invoice.customer_name || 'Walk-in Customer'}`, 20, 59);
      doc.text(`Type: ${invoice.invoice_type ? invoice.invoice_type.toUpperCase() : 'SALE'}`, 20, 66);
      
      // Items table
      const tableData = (invoice.items || []).map(item => [
        item.description || '',
        (item.qty || 0).toString(),
        (item.purity || 916).toString(),
        (item.weight || 0).toFixed(3),
        (item.metal_rate || 0).toFixed(3),
        (item.gold_value || 0).toFixed(3),
        (item.making_value || 0).toFixed(3),
        (item.vat_amount || 0).toFixed(3),
        (item.line_total || 0).toFixed(3)
      ]);
      
      doc.autoTable({
        startY: 75,
        head: [['Description', 'Qty', 'Purity', 'Weight(g)', 'Rate', 'Gold Val', 'Making', 'VAT', 'Total']],
        body: tableData,
        theme: 'grid',
        headStyles: { 
          fillColor: [6, 95, 70], 
          fontSize: 8,
          fontStyle: 'bold',
          halign: 'center'
        },
        bodyStyles: { fontSize: 8 },
        columnStyles: {
          0: { cellWidth: 40 },
          1: { cellWidth: 15, halign: 'right' },
          2: { cellWidth: 15, halign: 'right' },
          3: { cellWidth: 20, halign: 'right' },
          4: { cellWidth: 18, halign: 'right' },
          5: { cellWidth: 18, halign: 'right' },
          6: { cellWidth: 18, halign: 'right' },
          7: { cellWidth: 15, halign: 'right' },
          8: { cellWidth: 20, halign: 'right' }
        },
        margin: { left: 10, right: 10 }
      });
      
      // Totals section
      const finalY = doc.lastAutoTable.finalY + 15;
      doc.setFontSize(10);
      doc.setFont(undefined, 'normal');
      
      const rightAlign = 190;
      let currentY = finalY;
      
      doc.text('Subtotal:', 140, currentY);
      doc.text(`${(invoice.subtotal || 0).toFixed(3)} OMR`, rightAlign, currentY, { align: 'right' });
      
      // MODULE 7: Show discount line if discount exists
      const discountAmount = invoice.discount_amount || 0;
      if (discountAmount > 0) {
        currentY += 7;
        doc.text('Discount:', 140, currentY);
        doc.text(`-${discountAmount.toFixed(3)} OMR`, rightAlign, currentY, { align: 'right' });
      }
      
      currentY += 7;
      doc.text('VAT Total:', 140, currentY);
      doc.text(`${(invoice.vat_total || 0).toFixed(3)} OMR`, rightAlign, currentY, { align: 'right' });
      
      // Grand Total - Bold
      currentY += 9;
      doc.setFont(undefined, 'bold');
      doc.setFontSize(12);
      doc.text('Grand Total:', 140, currentY);
      doc.text(`${(invoice.grand_total || 0).toFixed(3)} OMR`, rightAlign, currentY, { align: 'right' });
      
      // Balance Due
      currentY += 8;
      doc.setFontSize(10);
      const balanceDue = invoice.balance_due || 0;
      const balanceColor = balanceDue > 0 ? [200, 0, 0] : [0, 150, 0];
      doc.setTextColor(...balanceColor);
      doc.text('Balance Due:', 140, currentY);
      doc.text(`${balanceDue.toFixed(3)} OMR`, rightAlign, currentY, { align: 'right' });
      
      // Payment Status
      doc.setTextColor(0, 0, 0);
      doc.setFont(undefined, 'normal');
      doc.setFontSize(9);
      const statusText = `Status: ${(invoice.payment_status || 'unpaid').toUpperCase()}`;
      doc.text(statusText, 20, currentY);
      
      // Footer
      doc.setFont(undefined, 'italic');
      doc.setFontSize(8);
      doc.text('Thank you for your business!', 105, 280, { align: 'center' });
      doc.text('This is a computer generated invoice', 105, 285, { align: 'center' });
      
      // Save the PDF
      doc.save(`Invoice_${invoice.invoice_number || 'unknown'}.pdf`);
      toast.success('Invoice PDF generated successfully');
    } catch (error) {
      console.error('Error generating PDF:', error);
      toast.error('Failed to generate invoice PDF');
    }
  };

  const handleFinalizeInvoice = async (invoiceId, invoiceNumber) => {
    if (!window.confirm(`Are you sure you want to finalize invoice ${invoiceNumber}?\n\nThis will:\n• Deduct stock from inventory\n• Lock the invoice (cannot be edited or deleted)\n• Lock any linked job card\n• Create customer ledger entry\n\nThis action cannot be undone.`)) {
      return;
    }

    setFinalizing(invoiceId);
    try {
      await axios.post(`${API}/invoices/${invoiceId}/finalize`);
      toast.success('Invoice finalized successfully! Stock has been deducted.');
      loadInvoices(); // Reload to show updated status
    } catch (error) {
      console.error('Error finalizing invoice:', error);
      const errorMsg = error.response?.data?.detail || 'Failed to finalize invoice';
      toast.error(errorMsg);
    } finally {
      setFinalizing(null);
    }
  };

  const handleViewInvoice = (invoice) => {
    setViewInvoice(invoice);
    setShowViewDialog(true);
  };

  const handleOpenPaymentDialog = (invoice) => {
    setSelectedInvoice(invoice);
    setPaymentData({
      amount: invoice.balance_due.toFixed(3),  // Default to full balance
      payment_mode: 'Cash',
      account_id: accounts.length > 0 ? accounts[0].id : '',
      notes: '',
      // Gold exchange specific fields
      gold_weight_grams: '',
      rate_per_gram: '',
      purity_entered: '916'
    });
    setShowPaymentDialog(true);
  };

  const handleAddPayment = async () => {
    // GOLD_EXCHANGE mode validation
    if (paymentData.payment_mode === 'GOLD_EXCHANGE') {
      // Check if customer is saved (not walk-in)
      if (selectedInvoice.customer_type === 'walk_in') {
        toast.error('Gold Exchange payment is only available for saved customers, not walk-in customers');
        return;
      }

      if (!paymentData.gold_weight_grams || parseFloat(paymentData.gold_weight_grams) <= 0) {
        toast.error('Please enter a valid gold weight');
        return;
      }

      if (!paymentData.rate_per_gram || parseFloat(paymentData.rate_per_gram) <= 0) {
        toast.error('Please enter a valid rate per gram');
        return;
      }

      try {
        const response = await axios.post(
          `${API}/invoices/${selectedInvoice.id}/add-payment`,
          {
            payment_mode: 'GOLD_EXCHANGE',
            gold_weight_grams: parseFloat(paymentData.gold_weight_grams),
            rate_per_gram: parseFloat(paymentData.rate_per_gram),
            purity_entered: parseInt(paymentData.purity_entered) || 916,
            notes: paymentData.notes
          }
        );

        toast.success(`Gold exchange payment added! Transaction #${response.data.transaction_number}`);
        toast.info(`Gold used: ${response.data.gold_weight_grams}g | Value: ${response.data.gold_money_value} OMR`);
        
        setShowPaymentDialog(false);
        loadInvoices();
      } catch (error) {
        console.error('Error adding gold exchange payment:', error);
        const errorMsg = error.response?.data?.detail || 'Failed to add gold exchange payment';
        toast.error(errorMsg);
      }
      return;
    }

    // Standard payment mode validation
    if (!paymentData.amount || parseFloat(paymentData.amount) <= 0) {
      toast.error('Please enter a valid payment amount');
      return;
    }

    if (!paymentData.account_id) {
      toast.error('Please select an account');
      return;
    }

    try {
      const response = await axios.post(
        `${API}/invoices/${selectedInvoice.id}/add-payment`,
        {
          amount: parseFloat(paymentData.amount),
          payment_mode: paymentData.payment_mode,
          account_id: paymentData.account_id,
          notes: paymentData.notes
        }
      );

      // Show warning for walk-in partial payments
      if (response.data.is_walk_in_partial_payment) {
        toast.warning('⚠️ Walk-in customer with outstanding balance. Full payment is recommended.');
      } else {
        toast.success(`Payment added successfully! Transaction #${response.data.transaction_number}`);
      }

      setShowPaymentDialog(false);
      loadInvoices(); // Reload to show updated payment status
    } catch (error) {
      console.error('Error adding payment:', error);
      const errorMsg = error.response?.data?.detail || 'Failed to add payment';
      toast.error(errorMsg);
    }
  };


  const getPaymentStatusBadge = (status) => {
    const variants = {
      unpaid: 'bg-red-100 text-red-800',
      partial: 'bg-yellow-100 text-yellow-800',
      paid: 'bg-green-100 text-green-800'
    };
    return <Badge className={variants[status] || 'bg-gray-100 text-gray-800'}>{status}</Badge>;
  };

  const getInvoiceStatusBadge = (status) => {
    if (status === 'finalized') {
      return <Badge className="bg-emerald-100 text-emerald-800"><Lock className="w-3 h-3 mr-1 inline" />Finalized</Badge>;
    }
    return <Badge className="bg-blue-100 text-blue-800">Draft</Badge>;
  };

  return (
    <div data-testid="invoices-page">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-serif font-semibold text-gray-900 mb-2">Invoices</h1>
          <p className="text-muted-foreground">Manage sales and service invoices</p>
        </div>
      </div>

      {/* Info Card about Draft/Finalized workflow */}
      <Card className="mb-6 border-blue-200 bg-blue-50">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-blue-600 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold text-blue-900 mb-1">Invoice Workflow</h3>
              <p className="text-sm text-blue-800">
                <strong>Draft Invoices:</strong> Can be edited or deleted. Stock is NOT deducted yet.
                <br />
                <strong>Finalized Invoices:</strong> Stock is deducted, invoice is locked, job card is locked, and customer ledger entry is created. This action cannot be undone.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-xl font-serif">All Invoices</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full" data-testid="invoices-table">
              <thead className="bg-muted/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Invoice #</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Customer</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Type</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase">Grand Total</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase">Balance Due</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Invoice Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Payment Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Actions</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((inv) => (
                  <tr key={inv.id} className="border-t hover:bg-muted/30">
                    <td className="px-4 py-3 font-mono font-semibold">{inv.invoice_number}</td>
                    <td className="px-4 py-3 text-sm">{new Date(inv.date).toLocaleDateString()}</td>
                    <td className="px-4 py-3">
                      {inv.customer_type === 'walk_in' ? (
                        <div>
                          <div>{inv.walk_in_name || 'Walk-in Customer'}</div>
                          <Badge variant="outline" className="mt-1 text-xs bg-amber-50 text-amber-700">
                            Walk-in
                          </Badge>
                        </div>
                      ) : (
                        inv.customer_name || '-'
                      )}
                    </td>
                    <td className="px-4 py-3 capitalize text-sm">{inv.invoice_type}</td>
                    <td className="px-4 py-3 text-right font-mono">{inv.grand_total.toFixed(3)}</td>
                    <td className="px-4 py-3 text-right font-mono">{inv.balance_due.toFixed(3)}</td>
                    <td className="px-4 py-3">{getInvoiceStatusBadge(inv.status || 'draft')}</td>
                    <td className="px-4 py-3">{getPaymentStatusBadge(inv.payment_status)}</td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        <Button
                          data-testid={`view-${inv.invoice_number}`}
                          size="sm"
                          variant="outline"
                          className="text-indigo-600 hover:text-indigo-700"
                          onClick={() => handleViewInvoice(inv)}
                        >
                          <Eye className="w-4 h-4 mr-1" /> View
                        </Button>
                        {(inv.status === 'draft' || !inv.status) && (
                          <Button
                            data-testid={`finalize-${inv.invoice_number}`}
                            size="sm"
                            variant="default"
                            className="bg-emerald-600 hover:bg-emerald-700"
                            onClick={() => handleFinalizeInvoice(inv.id, inv.invoice_number)}
                            disabled={finalizing === inv.id}
                          >
                            {finalizing === inv.id ? (
                              <>Processing...</>
                            ) : (
                              <><CheckCircle className="w-4 h-4 mr-1" /> Finalize</>
                            )}
                          </Button>
                        )}
                        {inv.balance_due > 0 && (
                          <Button
                            data-testid={`payment-${inv.invoice_number}`}
                            size="sm"
                            variant="outline"
                            className="text-blue-600 hover:text-blue-700"
                            onClick={() => handleOpenPaymentDialog(inv)}
                          >
                            <DollarSign className="w-4 h-4 mr-1" /> Add Payment
                          </Button>
                        )}
                        <Button
                          data-testid={`print-${inv.invoice_number}`}
                          size="sm"
                          variant="outline"
                          onClick={() => handlePrintInvoice(inv)}
                        >
                          <Printer className="w-4 h-4 mr-1" /> Print
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Payment Dialog */}
      <Dialog open={showPaymentDialog} onOpenChange={setShowPaymentDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Add Payment - {selectedInvoice?.invoice_number}</DialogTitle>
          </DialogHeader>

          {selectedInvoice && (
            <div className="space-y-6">
              {/* Invoice Summary */}
              <div className="p-4 bg-muted/50 rounded-lg space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Grand Total:</span>
                  <span className="font-mono font-semibold">{selectedInvoice.grand_total.toFixed(3)} OMR</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Paid Amount:</span>
                  <span className="font-mono">{selectedInvoice.paid_amount.toFixed(3)} OMR</span>
                </div>
                <div className="flex justify-between text-base font-semibold border-t pt-2">
                  <span>Balance Due:</span>
                  <span className="font-mono text-red-600">{selectedInvoice.balance_due.toFixed(3)} OMR</span>
                </div>
              </div>

              {/* Walk-in Warning */}
              {selectedInvoice.customer_type === 'walk_in' && (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2">
                  <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
                  <div className="text-sm text-amber-800">
                    <p className="font-semibold">Walk-in Customer</p>
                    <p>Full payment is recommended. Outstanding balance tracking is limited for walk-in customers.</p>
                  </div>
                </div>
              )}

              {/* Payment Form */}
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Payment Mode *</Label>
                  <Select 
                    value={paymentData.payment_mode} 
                    onValueChange={(value) => setPaymentData({...paymentData, payment_mode: value})}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Cash">Cash</SelectItem>
                      <SelectItem value="Bank Transfer">Bank Transfer</SelectItem>
                      <SelectItem value="Card">Card</SelectItem>
                      <SelectItem value="UPI/Online">UPI/Online</SelectItem>
                      <SelectItem value="Cheque">Cheque</SelectItem>
                      <SelectItem value="GOLD_EXCHANGE">Gold Exchange</SelectItem>
                    </SelectContent>
                  </Select>
                  {paymentData.payment_mode === 'GOLD_EXCHANGE' && (
                    <p className="text-xs text-amber-600 mt-1">
                      💰 Use customer's gold balance to pay invoice (saved customers only)
                    </p>
                  )}
                </div>

                {/* Conditional Fields for GOLD_EXCHANGE */}
                {paymentData.payment_mode === 'GOLD_EXCHANGE' ? (
                  <>
                    {/* Gold Exchange Fields */}
                    <div className="space-y-4 p-4 bg-amber-50 border border-amber-200 rounded-lg">
                      <h4 className="font-semibold text-sm text-amber-900">Gold Exchange Details</h4>
                      
                      <div className="space-y-2">
                        <Label>Gold Weight (grams) *</Label>
                        <Input
                          type="number"
                          step="0.001"
                          min="0"
                          value={paymentData.gold_weight_grams}
                          onChange={(e) => {
                            const weight = e.target.value;
                            const rate = paymentData.rate_per_gram;
                            setPaymentData({
                              ...paymentData, 
                              gold_weight_grams: weight,
                              // Auto-calculate amount if rate is available
                              amount: (weight && rate) ? (parseFloat(weight) * parseFloat(rate)).toFixed(3) : ''
                            });
                          }}
                          placeholder="e.g., 25.500"
                        />
                        <p className="text-xs text-gray-600">Amount of gold customer will use for payment</p>
                      </div>

                      <div className="space-y-2">
                        <Label>Rate per Gram (OMR) *</Label>
                        <Input
                          type="number"
                          step="0.01"
                          min="0"
                          value={paymentData.rate_per_gram}
                          onChange={(e) => {
                            const rate = e.target.value;
                            const weight = paymentData.gold_weight_grams;
                            setPaymentData({
                              ...paymentData, 
                              rate_per_gram: rate,
                              // Auto-calculate amount if weight is available
                              amount: (weight && rate) ? (parseFloat(weight) * parseFloat(rate)).toFixed(3) : ''
                            });
                          }}
                          placeholder="e.g., 20.00"
                        />
                        <p className="text-xs text-gray-600">Gold conversion rate to money</p>
                      </div>

                      <div className="space-y-2">
                        <Label>Purity</Label>
                        <Input
                          type="number"
                          value={paymentData.purity_entered}
                          onChange={(e) => setPaymentData({...paymentData, purity_entered: e.target.value})}
                          placeholder="916"
                        />
                        <p className="text-xs text-gray-600">Default: 916 (22K gold standard)</p>
                      </div>

                      {paymentData.gold_weight_grams && paymentData.rate_per_gram && (
                        <div className="p-3 bg-green-50 border border-green-200 rounded">
                          <p className="text-sm font-semibold text-green-900">
                            Calculated Payment Value: {(parseFloat(paymentData.gold_weight_grams) * parseFloat(paymentData.rate_per_gram)).toFixed(3)} OMR
                          </p>
                          <p className="text-xs text-green-700 mt-1">
                            {paymentData.gold_weight_grams}g × {paymentData.rate_per_gram} OMR/g
                          </p>
                        </div>
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label>Notes (Optional)</Label>
                      <Input
                        value={paymentData.notes}
                        onChange={(e) => setPaymentData({...paymentData, notes: e.target.value})}
                        placeholder="Payment notes or reference"
                      />
                    </div>
                  </>
                ) : (
                  <>
                    {/* Standard Payment Fields */}
                    <div className="space-y-2">
                      <Label>Payment Amount (OMR) *</Label>
                      <Input
                        type="number"
                        step="0.001"
                        value={paymentData.amount}
                        onChange={(e) => setPaymentData({...paymentData, amount: e.target.value})}
                        placeholder="Enter payment amount"
                      />
                      <button
                        type="button"
                        onClick={() => setPaymentData({...paymentData, amount: selectedInvoice.balance_due.toFixed(3)})}
                        className="text-xs text-blue-600 hover:text-blue-700"
                      >
                        Set to full balance ({selectedInvoice.balance_due.toFixed(3)} OMR)
                      </button>
                    </div>

                    <div className="space-y-2">
                      <Label>Account (Where money goes) *</Label>
                      <Select 
                        value={paymentData.account_id} 
                        onValueChange={(value) => setPaymentData({...paymentData, account_id: value})}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select account" />
                        </SelectTrigger>
                        <SelectContent>
                          {accounts.map(account => (
                            <SelectItem key={account.id} value={account.id}>
                              {account.name} ({account.account_type})
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label>Notes (Optional)</Label>
                      <Input
                        value={paymentData.notes}
                        onChange={(e) => setPaymentData({...paymentData, notes: e.target.value})}
                        placeholder="Payment notes or reference"
                      />
                    </div>
                  </>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={() => setShowPaymentDialog(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleAddPayment}
                  className="flex-1"
                >
                  Add Payment
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* View Invoice Dialog */}
      <Dialog open={showViewDialog} onOpenChange={setShowViewDialog}>
        <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif">Invoice Details</DialogTitle>
          </DialogHeader>

          {viewInvoice && (
            <div className="space-y-6">
              {/* Invoice Header */}
              <div className="grid grid-cols-2 gap-6 p-4 bg-muted/50 rounded-lg">
                <div className="space-y-2">
                  <div>
                    <p className="text-xs text-muted-foreground">Invoice Number</p>
                    <p className="font-mono font-semibold text-lg">{viewInvoice.invoice_number}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Invoice Type</p>
                    <p className="capitalize font-medium">{viewInvoice.invoice_type}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Date</p>
                    <p className="font-medium">{new Date(viewInvoice.date).toLocaleDateString()}</p>
                  </div>
                </div>
                <div className="space-y-2">
                  <div>
                    <p className="text-xs text-muted-foreground">Customer</p>
                    {viewInvoice.customer_type === 'walk_in' ? (
                      <div>
                        <p className="font-medium">{viewInvoice.walk_in_name || 'Walk-in Customer'}</p>
                        <Badge variant="outline" className="mt-1 text-xs bg-amber-50 text-amber-700">
                          Walk-in
                        </Badge>
                      </div>
                    ) : (
                      <p className="font-medium">{viewInvoice.customer_name || '-'}</p>
                    )}
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Invoice Status</p>
                    <div className="mt-1">{getInvoiceStatusBadge(viewInvoice.status || 'draft')}</div>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Payment Status</p>
                    <div className="mt-1">{getPaymentStatusBadge(viewInvoice.payment_status)}</div>
                  </div>
                </div>
              </div>

              {/* Timestamps */}
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h3 className="text-sm font-semibold text-blue-900 mb-2">Timestamps</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-blue-700">Created At:</p>
                    <p className="font-mono text-blue-900">
                      {viewInvoice.created_at ? new Date(viewInvoice.created_at).toLocaleString() : 'N/A'}
                    </p>
                  </div>
                  {viewInvoice.finalized_at && (
                    <div>
                      <p className="text-blue-700">Finalized At:</p>
                      <p className="font-mono text-blue-900">
                        {new Date(viewInvoice.finalized_at).toLocaleString()}
                      </p>
                    </div>
                  )}
                  {viewInvoice.finalized_by && (
                    <div>
                      <p className="text-blue-700">Finalized By:</p>
                      <p className="font-mono text-blue-900">{viewInvoice.finalized_by}</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Items Table */}
              <div>
                <h3 className="text-lg font-semibold mb-3">Items</h3>
                <div className="overflow-x-auto border rounded-lg">
                  <table className="w-full text-sm">
                    <thead className="bg-muted/50">
                      <tr>
                        <th className="px-3 py-2 text-left font-semibold">Description</th>
                        <th className="px-3 py-2 text-right font-semibold">Qty</th>
                        <th className="px-3 py-2 text-right font-semibold">Purity</th>
                        <th className="px-3 py-2 text-right font-semibold">Weight (g)</th>
                        <th className="px-3 py-2 text-right font-semibold">Rate</th>
                        <th className="px-3 py-2 text-right font-semibold">Gold Value</th>
                        <th className="px-3 py-2 text-right font-semibold">Making</th>
                        <th className="px-3 py-2 text-right font-semibold">VAT</th>
                        <th className="px-3 py-2 text-right font-semibold">Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(viewInvoice.items || []).map((item, idx) => (
                        <tr key={idx} className="border-t hover:bg-muted/20">
                          <td className="px-3 py-2">{item.description || '-'}</td>
                          <td className="px-3 py-2 text-right font-mono">{item.qty || 0}</td>
                          <td className="px-3 py-2 text-right font-mono">{item.purity || 916}K</td>
                          <td className="px-3 py-2 text-right font-mono">{(item.weight || 0).toFixed(3)}</td>
                          <td className="px-3 py-2 text-right font-mono">{(item.metal_rate || 0).toFixed(3)}</td>
                          <td className="px-3 py-2 text-right font-mono">{(item.gold_value || 0).toFixed(3)}</td>
                          <td className="px-3 py-2 text-right font-mono">{(item.making_value || 0).toFixed(3)}</td>
                          <td className="px-3 py-2 text-right font-mono">{(item.vat_amount || 0).toFixed(3)}</td>
                          <td className="px-3 py-2 text-right font-mono font-semibold">{(item.line_total || 0).toFixed(3)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Enhanced Cost Components Breakdown */}
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-200 mb-4">
                <h3 className="text-lg font-semibold text-blue-900 mb-3 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  Cost Components Breakdown
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-white rounded-md p-3 border border-blue-100">
                    <div className="text-xs text-gray-600 mb-1">Total Metal Value</div>
                    <div className="font-mono font-bold text-amber-700">
                      {(viewInvoice.items || []).reduce((sum, item) => sum + (item.gold_value || 0), 0).toFixed(3)} OMR
                    </div>
                    <div className="text-xs text-gray-500 mt-1">Weight × Rate</div>
                  </div>
                  
                  <div className="bg-white rounded-md p-3 border border-blue-100">
                    <div className="text-xs text-gray-600 mb-1">Total Making Charges</div>
                    <div className="font-mono font-bold text-green-700">
                      {(viewInvoice.items || []).reduce((sum, item) => sum + (item.making_value || 0), 0).toFixed(3)} OMR
                    </div>
                    <div className="text-xs text-gray-500 mt-1">Labor & Craftsmanship</div>
                  </div>
                  
                  <div className="bg-white rounded-md p-3 border border-blue-100">
                    <div className="text-xs text-gray-600 mb-1">Total VAT</div>
                    <div className="font-mono font-bold text-blue-700">
                      {(viewInvoice.vat_total || 0).toFixed(3)} OMR
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {viewInvoice.items && viewInvoice.items.length > 0 
                        ? `@ ${viewInvoice.items[0].vat_percent || 5}%` 
                        : '@ 5%'}
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-md p-3">
                    <div className="text-xs text-blue-100 mb-1">Grand Total</div>
                    <div className="font-mono font-bold text-xl">
                      {(viewInvoice.grand_total || 0).toFixed(2)} OMR
                    </div>
                    <div className="text-xs text-blue-200 mt-1">Inc. All Charges</div>
                  </div>
                </div>
                
                {/* Weight Summary */}
                <div className="mt-3 pt-3 border-t border-blue-200">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-blue-800 font-medium">Total Weight:</span>
                    <span className="font-mono font-semibold text-blue-900">
                      {(viewInvoice.items || []).reduce((sum, item) => sum + (item.weight || 0), 0).toFixed(3)}g
                    </span>
                  </div>
                </div>
              </div>

              {/* Totals Section */}
              <div className="grid grid-cols-2 gap-6">
                {/* Left side - Payment Details */}
                <div className="space-y-3">
                  <h3 className="text-lg font-semibold">Payment Details</h3>
                  <div className="p-4 bg-muted/30 rounded-lg space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Paid Amount:</span>
                      <span className="font-mono font-medium text-green-700">{(viewInvoice.paid_amount || 0).toFixed(3)} OMR</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Balance Due:</span>
                      <span className="font-mono font-semibold text-red-700">{(viewInvoice.balance_due || 0).toFixed(3)} OMR</span>
                    </div>
                    {viewInvoice.payment_mode && (
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Payment Mode:</span>
                        <span className="font-medium">{viewInvoice.payment_mode}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Right side - Amount Totals */}
                <div className="space-y-3">
                  <h3 className="text-lg font-semibold">Amount Breakdown</h3>
                  <div className="p-4 bg-muted/30 rounded-lg space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Subtotal:</span>
                      <span className="font-mono">{(viewInvoice.subtotal || 0).toFixed(3)} OMR</span>
                    </div>
                    {viewInvoice.discount_amount > 0 && (
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Discount:</span>
                        <span className="font-mono text-red-600">-{(viewInvoice.discount_amount || 0).toFixed(3)} OMR</span>
                      </div>
                    )}
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">VAT Total:</span>
                      <span className="font-mono">{(viewInvoice.vat_total || 0).toFixed(3)} OMR</span>
                    </div>
                    {viewInvoice.round_off_amount !== 0 && viewInvoice.round_off_amount !== null && (
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Round Off:</span>
                        <span className="font-mono">{(viewInvoice.round_off_amount || 0).toFixed(3)} OMR</span>
                      </div>
                    )}
                    <div className="flex justify-between text-base font-bold border-t pt-2 mt-2">
                      <span>Grand Total:</span>
                      <span className="font-mono text-lg">{(viewInvoice.grand_total || 0).toFixed(3)} OMR</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 pt-4">
                <Button
                  variant="outline"
                  onClick={() => setShowViewDialog(false)}
                  className="flex-1"
                >
                  Close
                </Button>
                <Button
                  onClick={() => {
                    handlePrintInvoice(viewInvoice);
                    setShowViewDialog(false);
                  }}
                  className="flex-1"
                >
                  <Printer className="w-4 h-4 mr-2" /> Print Invoice
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

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
import { FileText, Printer, CheckCircle, Lock, DollarSign, AlertTriangle } from 'lucide-react';
import jsPDF from 'jspdf';
import 'jspdf-autotable';

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [finalizing, setFinalizing] = useState(null);
  const [showPaymentDialog, setShowPaymentDialog] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [paymentData, setPaymentData] = useState({
    amount: '',
    payment_mode: 'Cash',
    account_id: '',
    notes: ''
  });

  useEffect(() => {
    loadInvoices();
  }, []);

  const loadInvoices = async () => {
    try {
      const response = await axios.get(`${API}/invoices`);
      setInvoices(response.data);
    } catch (error) {
      toast.error('Failed to load invoices');
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
      doc.text('Subtotal:', 140, finalY);
      doc.text(`${(invoice.subtotal || 0).toFixed(3)} OMR`, rightAlign, finalY, { align: 'right' });
      
      doc.text('VAT Total:', 140, finalY + 7);
      doc.text(`${(invoice.vat_total || 0).toFixed(3)} OMR`, rightAlign, finalY + 7, { align: 'right' });
      
      // Grand Total - Bold
      doc.setFont(undefined, 'bold');
      doc.setFontSize(12);
      doc.text('Grand Total:', 140, finalY + 16);
      doc.text(`${(invoice.grand_total || 0).toFixed(3)} OMR`, rightAlign, finalY + 16, { align: 'right' });
      
      // Balance Due
      doc.setFontSize(10);
      const balanceDue = invoice.balance_due || 0;
      const balanceColor = balanceDue > 0 ? [200, 0, 0] : [0, 150, 0];
      doc.setTextColor(...balanceColor);
      doc.text('Balance Due:', 140, finalY + 24);
      doc.text(`${balanceDue.toFixed(3)} OMR`, rightAlign, finalY + 24, { align: 'right' });
      
      // Payment Status
      doc.setTextColor(0, 0, 0);
      doc.setFont(undefined, 'normal');
      doc.setFontSize(9);
      const statusText = `Status: ${(invoice.payment_status || 'unpaid').toUpperCase()}`;
      doc.text(statusText, 20, finalY + 24);
      
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
                    <td className="px-4 py-3">{inv.customer_name || '-'}</td>
                    <td className="px-4 py-3 capitalize text-sm">{inv.invoice_type}</td>
                    <td className="px-4 py-3 text-right font-mono">{inv.grand_total.toFixed(3)}</td>
                    <td className="px-4 py-3 text-right font-mono">{inv.balance_due.toFixed(3)}</td>
                    <td className="px-4 py-3">{getInvoiceStatusBadge(inv.status || 'draft')}</td>
                    <td className="px-4 py-3">{getPaymentStatusBadge(inv.payment_status)}</td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
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
    </div>
  );
}

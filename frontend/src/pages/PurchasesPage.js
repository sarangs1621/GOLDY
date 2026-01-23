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
import { Package, CheckCircle, Lock, Edit, ShoppingCart, Calendar, Trash2 } from 'lucide-react';
import { extractErrorMessage } from '../utils/errorHandler';
import { ConfirmationDialog } from '../components/ConfirmationDialog';

export default function PurchasesPage() {
  const [purchases, setPurchases] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [showDialog, setShowDialog] = useState(false);
  const [editingPurchase, setEditingPurchase] = useState(null);
  const [finalizing, setFinalizing] = useState(null);
  
  // Filters
  const [filterVendor, setFilterVendor] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const [formData, setFormData] = useState({
    vendor_party_id: '',
    date: new Date().toISOString().split('T')[0],
    description: '',
    weight_grams: '',
    entered_purity: '999',
    rate_per_gram: '',
    amount_total: '',
    // Payment fields
    paid_amount_money: '0',
    payment_mode: 'Cash',
    account_id: '',
    // Gold settlement fields
    advance_in_gold_grams: '',
    exchange_in_gold_grams: ''
  });

  useEffect(() => {
    loadPurchases();
    loadVendors();
    loadAccounts();
  }, []);

  const loadPurchases = async () => {
    try {
      const params = new URLSearchParams();
      if (filterVendor && filterVendor !== 'all') params.append('vendor_party_id', filterVendor);
      if (filterStatus && filterStatus !== 'all') params.append('status', filterStatus);
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      
      const response = await axios.get(`${API}/purchases?${params.toString()}`);
      setPurchases(response.data.items || []);
    } catch (error) {
      toast.error('Failed to load purchases');
    }
  };

  const loadVendors = async () => {
    try {
      const response = await axios.get(`${API}/parties?party_type=vendor`);
      setVendors(response.data.items || []);
    } catch (error) {
      console.error('Failed to load vendors:', error);
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

  useEffect(() => {
    loadPurchases();
  }, [filterVendor, filterStatus, startDate, endDate]);

  const handleOpenDialog = (purchase = null) => {
    if (purchase) {
      setEditingPurchase(purchase);
      setFormData({
        vendor_party_id: purchase.vendor_party_id || '',
        date: purchase.date ? new Date(purchase.date).toISOString().split('T')[0] : new Date().toISOString().split('T')[0],
        description: purchase.description || '',
        weight_grams: purchase.weight_grams || '',
        entered_purity: purchase.entered_purity || '999',
        rate_per_gram: purchase.rate_per_gram || '',
        amount_total: purchase.amount_total || '',
        paid_amount_money: purchase.paid_amount_money || '0',
        payment_mode: purchase.payment_mode || 'Cash',
        account_id: purchase.account_id || '',
        advance_in_gold_grams: purchase.advance_in_gold_grams || '',
        exchange_in_gold_grams: purchase.exchange_in_gold_grams || ''
      });
    } else {
      setEditingPurchase(null);
      setFormData({
        vendor_party_id: vendors.length > 0 ? vendors[0].id : '',
        date: new Date().toISOString().split('T')[0],
        description: '',
        weight_grams: '',
        entered_purity: '999',
        rate_per_gram: '',
        amount_total: '',
        paid_amount_money: '0',
        payment_mode: 'Cash',
        account_id: accounts.length > 0 ? accounts[0].id : '',
        advance_in_gold_grams: '',
        exchange_in_gold_grams: ''
      });
    }
    setShowDialog(true);
  };

  const handleSavePurchase = async () => {
    if (!formData.vendor_party_id) {
      toast.error('Please select a vendor');
      return;
    }

    if (!formData.weight_grams || parseFloat(formData.weight_grams) <= 0) {
      toast.error('Please enter a valid weight');
      return;
    }

    if (!formData.rate_per_gram || parseFloat(formData.rate_per_gram) <= 0) {
      toast.error('Please enter a valid rate per gram');
      return;
    }

    if (!formData.amount_total || parseFloat(formData.amount_total) <= 0) {
      toast.error('Please enter a valid total amount');
      return;
    }

    try {
      const payload = {
        vendor_party_id: formData.vendor_party_id,
        date: formData.date,
        description: formData.description,
        weight_grams: parseFloat(formData.weight_grams),
        entered_purity: parseInt(formData.entered_purity),
        rate_per_gram: parseFloat(formData.rate_per_gram),
        amount_total: parseFloat(formData.amount_total),
        paid_amount_money: parseFloat(formData.paid_amount_money) || 0,
        payment_mode: formData.payment_mode,
        account_id: formData.account_id || null,
        advance_in_gold_grams: formData.advance_in_gold_grams ? parseFloat(formData.advance_in_gold_grams) : null,
        exchange_in_gold_grams: formData.exchange_in_gold_grams ? parseFloat(formData.exchange_in_gold_grams) : null
      };

      if (editingPurchase) {
        await axios.patch(`${API}/purchases/${editingPurchase.id}`, payload);
        toast.success('Purchase updated successfully');
      } else {
        await axios.post(`${API}/purchases`, payload);
        toast.success('Purchase created successfully');
      }

      setShowDialog(false);
      loadPurchases();
    } catch (error) {
      console.error('Error saving purchase:', error);
      const errorMsg = extractErrorMessage(error, 'Failed to save purchase');
      toast.error(errorMsg);
    }
  };

  const handleFinalizePurchase = async (purchase) => {
    if (window.confirm(`Finalize purchase for ${purchase.weight_grams}g from ${getVendorName(purchase.vendor_party_id)}?\n\nThis will:\n• Create Stock IN movement (add inventory)\n• Lock the purchase (no further edits)\n• Record vendor payable for balance due\n• Create payment transactions if applicable`)) {
      setFinalizing(purchase.id);
      try {
        await axios.post(`${API}/purchases/${purchase.id}/finalize`);
        toast.success('Purchase finalized successfully!');
        loadPurchases();
      } catch (error) {
        console.error('Error finalizing purchase:', error);
        const errorMsg = extractErrorMessage(error, 'Failed to finalize purchase');
        toast.error(errorMsg);
      } finally {
        setFinalizing(null);
      }
    }
  };

  const getVendorName = (vendorId) => {
    const vendor = vendors.find(v => v.id === vendorId);
    return vendor ? vendor.name : 'Unknown Vendor';
  };

  const getStatusBadge = (status) => {
    if (status === 'finalized') {
      return <Badge className="bg-green-100 text-green-800"><Lock className="w-3 h-3 mr-1 inline" />Finalized</Badge>;
    }
    return <Badge className="bg-blue-100 text-blue-800">Draft</Badge>;
  };

  // Calculate summary stats
  const totalPurchases = purchases.length;
  const draftPurchases = purchases.filter(p => p.status === 'draft').length;
  const finalizedPurchases = purchases.filter(p => p.status === 'finalized').length;
  const totalWeight = purchases.reduce((sum, p) => sum + (p.weight_grams || 0), 0);
  const totalValue = purchases.reduce((sum, p) => sum + (p.amount_total || 0), 0);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Purchases</h1>
        <Button onClick={() => handleOpenDialog()}>
          <ShoppingCart className="w-4 h-4 mr-2" /> New Purchase
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Purchases</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalPurchases}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Draft</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{draftPurchases}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Finalized</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{finalizedPurchases}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Weight</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalWeight.toFixed(3)}g</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Value</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalValue.toFixed(2)} OMR</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label>Vendor</Label>
              <Select value={filterVendor} onValueChange={setFilterVendor}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Vendors</SelectItem>
                  {vendors.map(vendor => (
                    <SelectItem key={vendor.id} value={vendor.id}>{vendor.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Status</Label>
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="draft">Draft</SelectItem>
                  <SelectItem value="finalized">Finalized</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Start Date</Label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>End Date</Label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Purchases Table */}
      <Card>
        <CardHeader>
          <CardTitle>Purchase Records</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3">Date</th>
                  <th className="text-left p-3">Vendor</th>
                  <th className="text-left p-3">Description</th>
                  <th className="text-right p-3">Weight (g)</th>
                  <th className="text-right p-3">Purity</th>
                  <th className="text-right p-3">Rate/g</th>
                  <th className="text-right p-3">Amount</th>
                  <th className="text-right p-3">Paid</th>
                  <th className="text-right p-3">Balance</th>
                  <th className="text-center p-3">Status</th>
                  <th className="text-center p-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {purchases.length === 0 ? (
                  <tr>
                    <td colSpan="11" className="text-center p-8 text-gray-500">
                      <Package className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p>No purchases found</p>
                    </td>
                  </tr>
                ) : (
                  purchases.map((purchase) => (
                    <tr key={purchase.id} className="border-b hover:bg-gray-50">
                      <td className="p-3">{new Date(purchase.date).toLocaleDateString()}</td>
                      <td className="p-3">{getVendorName(purchase.vendor_party_id)}</td>
                      <td className="p-3">{purchase.description}</td>
                      <td className="p-3 text-right font-mono">{purchase.weight_grams.toFixed(3)}</td>
                      <td className="p-3 text-right">{purchase.entered_purity}K</td>
                      <td className="p-3 text-right font-mono">{purchase.rate_per_gram.toFixed(2)}</td>
                      <td className="p-3 text-right font-mono">{purchase.amount_total.toFixed(2)}</td>
                      <td className="p-3 text-right font-mono">{purchase.paid_amount_money.toFixed(2)}</td>
                      <td className="p-3 text-right font-mono font-semibold text-red-600">
                        {purchase.balance_due_money.toFixed(2)}
                      </td>
                      <td className="p-3 text-center">{getStatusBadge(purchase.status)}</td>
                      <td className="p-3">
                        <div className="flex gap-2 justify-center">
                          {purchase.status === 'draft' && (
                            <>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleOpenDialog(purchase)}
                              >
                                <Edit className="w-4 h-4" />
                              </Button>
                              <Button
                                size="sm"
                                onClick={() => handleFinalizePurchase(purchase)}
                                disabled={finalizing === purchase.id}
                              >
                                <CheckCircle className="w-4 h-4 mr-1" />
                                {finalizing === purchase.id ? 'Finalizing...' : 'Finalize'}
                              </Button>
                            </>
                          )}
                          {purchase.status === 'finalized' && (
                            <Badge className="bg-green-100 text-green-800">
                              <Lock className="w-3 h-3 mr-1" />Locked
                            </Badge>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Create/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingPurchase ? 'Edit Purchase' : 'New Purchase'}</DialogTitle>
          </DialogHeader>

          <div className="space-y-6">
            {/* Basic Information */}
            <div className="space-y-4">
              <h3 className="font-semibold text-sm text-gray-700">Basic Information</h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Vendor *</Label>
                  <Select value={formData.vendor_party_id} onValueChange={(value) => setFormData({...formData, vendor_party_id: value})}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select vendor" />
                    </SelectTrigger>
                    <SelectContent>
                      {vendors.map(vendor => (
                        <SelectItem key={vendor.id} value={vendor.id}>{vendor.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Date *</Label>
                  <Input
                    type="date"
                    value={formData.date}
                    onChange={(e) => setFormData({...formData, date: e.target.value})}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Description</Label>
                <Input
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  placeholder="Purchase description or notes"
                />
              </div>
            </div>

            {/* Gold Details */}
            <div className="space-y-4 p-4 bg-amber-50 border border-amber-200 rounded-lg">
              <h3 className="font-semibold text-sm text-amber-900">Gold Details</h3>
              
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Weight (grams) *</Label>
                  <Input
                    type="number"
                    step="0.001"
                    min="0"
                    value={formData.weight_grams}
                    onChange={(e) => setFormData({...formData, weight_grams: e.target.value})}
                    placeholder="0.000"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Entered Purity</Label>
                  <Input
                    type="number"
                    value={formData.entered_purity}
                    onChange={(e) => setFormData({...formData, entered_purity: e.target.value})}
                    placeholder="999"
                  />
                  <p className="text-xs text-gray-600">Purity as claimed by vendor</p>
                </div>

                <div className="space-y-2">
                  <Label>Rate per Gram (OMR) *</Label>
                  <Input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.rate_per_gram}
                    onChange={(e) => setFormData({...formData, rate_per_gram: e.target.value})}
                    placeholder="0.00"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Total Amount (OMR) *</Label>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.amount_total}
                  onChange={(e) => setFormData({...formData, amount_total: e.target.value})}
                  placeholder="0.00"
                />
              </div>

              <div className="p-3 bg-blue-50 border border-blue-200 rounded text-sm">
                <p className="text-blue-900">
                  <strong>Note:</strong> Stock will be added at <strong>916 purity (22K)</strong> for valuation purposes, regardless of entered purity.
                </p>
              </div>
            </div>

            {/* Payment Details */}
            <div className="space-y-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <h3 className="font-semibold text-sm text-green-900">Payment Details (Optional)</h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Paid Amount (OMR)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.paid_amount_money}
                    onChange={(e) => setFormData({...formData, paid_amount_money: e.target.value})}
                    placeholder="0.00"
                  />
                  <p className="text-xs text-gray-600">Amount paid during purchase</p>
                </div>

                <div className="space-y-2">
                  <Label>Payment Mode</Label>
                  <Select value={formData.payment_mode} onValueChange={(value) => setFormData({...formData, payment_mode: value})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Cash">Cash</SelectItem>
                      <SelectItem value="Bank Transfer">Bank Transfer</SelectItem>
                      <SelectItem value="Card">Card</SelectItem>
                      <SelectItem value="UPI">UPI</SelectItem>
                      <SelectItem value="Cheque">Cheque</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Payment Account</Label>
                <Select value={formData.account_id} onValueChange={(value) => setFormData({...formData, account_id: value})}>
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

              {formData.amount_total && formData.paid_amount_money && (
                <div className="p-3 bg-white border rounded">
                  <div className="flex justify-between text-sm">
                    <span>Total Amount:</span>
                    <span className="font-mono">{parseFloat(formData.amount_total || 0).toFixed(2)} OMR</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Paid Amount:</span>
                    <span className="font-mono">{parseFloat(formData.paid_amount_money || 0).toFixed(2)} OMR</span>
                  </div>
                  <div className="flex justify-between text-sm font-semibold border-t pt-2 mt-2">
                    <span>Balance Due:</span>
                    <span className="font-mono text-red-600">
                      {(parseFloat(formData.amount_total || 0) - parseFloat(formData.paid_amount_money || 0)).toFixed(2)} OMR
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Gold Settlement */}
            <div className="space-y-4 p-4 bg-purple-50 border border-purple-200 rounded-lg">
              <h3 className="font-semibold text-sm text-purple-900">Gold Settlement (Optional)</h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Advance Gold Used (grams)</Label>
                  <Input
                    type="number"
                    step="0.001"
                    min="0"
                    value={formData.advance_in_gold_grams}
                    onChange={(e) => setFormData({...formData, advance_in_gold_grams: e.target.value})}
                    placeholder="0.000"
                  />
                  <p className="text-xs text-gray-600">Gold we previously gave vendor, now used as credit</p>
                </div>

                <div className="space-y-2">
                  <Label>Exchange Gold Received (grams)</Label>
                  <Input
                    type="number"
                    step="0.001"
                    min="0"
                    value={formData.exchange_in_gold_grams}
                    onChange={(e) => setFormData({...formData, exchange_in_gold_grams: e.target.value})}
                    placeholder="0.000"
                  />
                  <p className="text-xs text-gray-600">Gold exchanged from vendor during purchase</p>
                </div>
              </div>
            </div>

            {/* Cost Breakdown Section */}
            {formData.weight_grams > 0 && formData.rate_per_gram > 0 && (
              <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg p-4 border border-purple-200">
                <h3 className="font-semibold text-purple-900 mb-3 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  Purchase Cost Breakdown
                </h3>
                
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {/* Weight */}
                  <div className="bg-white rounded-md p-3 border border-purple-100">
                    <div className="text-xs text-gray-600 mb-1">Weight</div>
                    <div className="font-mono font-bold text-amber-700">
                      {parseFloat(formData.weight_grams || 0).toFixed(3)}g
                    </div>
                    <div className="text-xs text-gray-500 mt-1">Gold purchased</div>
                  </div>
                  
                  {/* Rate */}
                  <div className="bg-white rounded-md p-3 border border-purple-100">
                    <div className="text-xs text-gray-600 mb-1">Rate per Gram</div>
                    <div className="font-mono font-bold text-blue-700">
                      {parseFloat(formData.rate_per_gram || 0).toFixed(3)} OMR
                    </div>
                    <div className="text-xs text-gray-500 mt-1">@ 916 purity</div>
                  </div>
                  
                  {/* Calculated Amount */}
                  <div className="bg-white rounded-md p-3 border border-purple-100">
                    <div className="text-xs text-gray-600 mb-1">Calculated Amount</div>
                    <div className="font-mono font-bold text-green-700">
                      {(parseFloat(formData.weight_grams || 0) * parseFloat(formData.rate_per_gram || 0)).toFixed(3)} OMR
                    </div>
                    <div className="text-xs text-gray-500 mt-1">Weight × Rate</div>
                  </div>
                </div>
                
                {/* Payment Summary */}
                <div className="mt-3 pt-3 border-t border-purple-200">
                  <div className="grid grid-cols-3 gap-3 text-sm">
                    <div className="flex flex-col">
                      <span className="text-gray-600 text-xs">Total Amount</span>
                      <span className="font-mono font-bold text-lg text-purple-900">
                        {parseFloat(formData.amount_total || 0).toFixed(2)} OMR
                      </span>
                    </div>
                    
                    <div className="flex flex-col">
                      <span className="text-gray-600 text-xs">Paid Now</span>
                      <span className="font-mono font-semibold text-green-600">
                        {parseFloat(formData.paid_amount_money || 0).toFixed(2)} OMR
                      </span>
                    </div>
                    
                    <div className="flex flex-col">
                      <span className="text-gray-600 text-xs">Balance Due</span>
                      <span className="font-mono font-semibold text-red-600">
                        {(parseFloat(formData.amount_total || 0) - parseFloat(formData.paid_amount_money || 0)).toFixed(2)} OMR
                      </span>
                    </div>
                  </div>
                </div>
                
                {/* Gold Settlement Info */}
                {(parseFloat(formData.advance_in_gold_grams || 0) > 0 || parseFloat(formData.exchange_in_gold_grams || 0) > 0) && (
                  <div className="mt-3 pt-3 border-t border-purple-200">
                    <div className="text-xs font-semibold text-purple-800 mb-2">Gold Settlement:</div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {parseFloat(formData.advance_in_gold_grams || 0) > 0 && (
                        <div className="flex justify-between bg-orange-50 px-2 py-1 rounded">
                          <span className="text-gray-700">Advance Settled:</span>
                          <span className="font-mono font-semibold text-orange-700">
                            {parseFloat(formData.advance_in_gold_grams).toFixed(3)}g
                          </span>
                        </div>
                      )}
                      {parseFloat(formData.exchange_in_gold_grams || 0) > 0 && (
                        <div className="flex justify-between bg-green-50 px-2 py-1 rounded">
                          <span className="text-gray-700">Gold Exchanged:</span>
                          <span className="font-mono font-semibold text-green-700">
                            {parseFloat(formData.exchange_in_gold_grams).toFixed(3)}g
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3">
              <Button variant="outline" onClick={() => setShowDialog(false)} className="flex-1">
                Cancel
              </Button>
              <Button onClick={handleSavePurchase} className="flex-1">
                {editingPurchase ? 'Update Purchase' : 'Create Purchase'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

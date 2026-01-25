import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { API } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { Package, CheckCircle, Lock, Edit, ShoppingCart, Calendar, Trash2, Eye, AlertTriangle } from 'lucide-react';
import { extractErrorMessage } from '../utils/errorHandler';
import { ConfirmationDialog } from '../components/ConfirmationDialog';
import { 
  validateWeight, 
  validateRate, 
  validateAmount, 
  validatePaidAmount, 
  validatePurity,
  validateSelection 
} from '../utils/validation';
import { FormErrorMessage } from '../components/FormErrorMessage';
import { PageLoadingSpinner, TableLoadingSpinner, ButtonLoadingSpinner } from '../components/LoadingSpinner';
import { TableEmptyState } from '../components/EmptyState';
import Pagination from '../components/Pagination';
import { formatWeight, formatCurrency, safeToFixed } from '../utils/numberFormat';
import { formatDateTime, formatDate } from '../utils/dateTimeUtils';

export default function PurchasesPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [purchases, setPurchases] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [vendors, setVendors] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [showDialog, setShowDialog] = useState(false);
  const [editingPurchase, setEditingPurchase] = useState(null);
  const [finalizing, setFinalizing] = useState(null);
  
  // Loading states
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // View dialog state
  const [showViewDialog, setShowViewDialog] = useState(false);
  const [viewPurchase, setViewPurchase] = useState(null);
  
  // Confirmation Dialogs
  const [showFinalizeConfirm, setShowFinalizeConfirm] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [confirmPurchase, setConfirmPurchase] = useState(null);
  const [impactData, setImpactData] = useState(null);
  const [confirmLoading, setConfirmLoading] = useState(false);
  
  // Filters
  const [filterVendor, setFilterVendor] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  
  // Form validation errors
  const [errors, setErrors] = useState({});

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

  // Get current page from URL, default to 1
  const currentPage = parseInt(searchParams.get('page') || '1', 10);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    setIsLoading(true);
    try {
      await Promise.all([
        loadPurchases(),
        loadVendors(),
        loadAccounts()
      ]);
    } catch (error) {
      console.error('Error loading initial data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadPurchases = async () => {
    try {
      const params = new URLSearchParams();
      params.append('page', currentPage);
      params.append('page_size', 10);
      if (filterVendor && filterVendor !== 'all') params.append('vendor_party_id', filterVendor);
      if (filterStatus && filterStatus !== 'all') params.append('status', filterStatus);
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      
      const response = await API.get(`/api/purchases?${params.toString()}`);
      setPurchases(response.data.items || []);
      setPagination(response.data.pagination);
    } catch (error) {
      toast.error('Failed to load purchases');
    }
  };

  const loadVendors = async () => {
    try {
      const response = await API.get(`/api/parties?party_type=vendor&page_size=1000`);
      setVendors(response.data.items || []);
    } catch (error) {
      console.error('Failed to load vendors:', error);
    }
  };

  const loadAccounts = async () => {
    try {
      const response = await API.get(`/api/accounts`);
      setAccounts(response.data);
    } catch (error) {
      console.error('Failed to load accounts:', error);
    }
  };

  useEffect(() => {
    loadPurchases();
  }, [filterVendor, filterStatus, startDate, endDate, currentPage]);

  const handlePageChange = (newPage) => {
    setSearchParams({ page: newPage.toString() });
  };

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
    setErrors({}); // Clear errors when opening dialog
    setShowDialog(true);
  };

  // Validate individual field
  const validateField = (fieldName, value) => {
    let validation = { isValid: true, error: '' };

    switch (fieldName) {
      case 'vendor_party_id':
        validation = validateSelection(value, 'vendor');
        break;
      case 'weight_grams':
        validation = validateWeight(value);
        break;
      case 'rate_per_gram':
        validation = validateRate(value);
        break;
      case 'amount_total':
        validation = validateAmount(value);
        break;
      case 'paid_amount_money':
        validation = validatePaidAmount(value, formData.amount_total);
        break;
      case 'entered_purity':
        validation = validatePurity(value);
        break;
      default:
        break;
    }

    setErrors(prev => ({
      ...prev,
      [fieldName]: validation.error
    }));

    return validation.isValid;
  };

  // Validate all required fields
  const validateForm = () => {
    const newErrors = {};
    let isValid = true;

    // Vendor validation
    const vendorValidation = validateSelection(formData.vendor_party_id, 'vendor');
    if (!vendorValidation.isValid) {
      newErrors.vendor_party_id = vendorValidation.error;
      isValid = false;
    }

    // Weight validation
    const weightValidation = validateWeight(formData.weight_grams);
    if (!weightValidation.isValid) {
      newErrors.weight_grams = weightValidation.error;
      isValid = false;
    }

    // Rate validation
    const rateValidation = validateRate(formData.rate_per_gram);
    if (!rateValidation.isValid) {
      newErrors.rate_per_gram = rateValidation.error;
      isValid = false;
    }

    // Amount validation
    const amountValidation = validateAmount(formData.amount_total);
    if (!amountValidation.isValid) {
      newErrors.amount_total = amountValidation.error;
      isValid = false;
    }

    // Paid amount validation
    const paidValidation = validatePaidAmount(formData.paid_amount_money, formData.amount_total);
    if (!paidValidation.isValid) {
      newErrors.paid_amount_money = paidValidation.error;
      isValid = false;
    }

    // Purity validation
    const purityValidation = validatePurity(formData.entered_purity);
    if (!purityValidation.isValid) {
      newErrors.entered_purity = purityValidation.error;
      isValid = false;
    }

    setErrors(newErrors);
    return isValid;
  };

  const handleSavePurchase = async () => {
    // Validate form before submission
    if (!validateForm()) {
      toast.error('Please fix the errors in the form');
      return;
    }

    setIsSubmitting(true);
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
        await API.patch(`/api/purchases/${editingPurchase.id}`, payload);
        toast.success('Purchase updated successfully');
      } else {
        await API.post(`/api/purchases`, payload);
        toast.success('Purchase created successfully');
      }

      setShowDialog(false);
      setErrors({}); // Clear errors on success
      loadPurchases();
    } catch (error) {
      console.error('Error saving purchase:', error);
      const errorMsg = extractErrorMessage(error, 'Failed to save purchase');
      toast.error(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFinalizePurchase = async (purchase) => {
    setConfirmPurchase(purchase);
    setConfirmLoading(true);
    try {
      const response = await API.get(`/api/purchases/${purchase.id}/finalize-impact`);
      setImpactData(response.data);
      setShowFinalizeConfirm(true);
    } catch (error) {
      console.error('Error fetching finalize impact:', error);
      toast.error('Failed to load confirmation data');
    } finally {
      setConfirmLoading(false);
    }
  };

  const confirmFinalizePurchase = async () => {
    if (!confirmPurchase) return;
    
    setConfirmLoading(true);
    setFinalizing(confirmPurchase.id);
    try {
      await API.post(`/api/purchases/${confirmPurchase.id}/finalize`);
      toast.success('Purchase finalized successfully!');
      setShowFinalizeConfirm(false);
      setConfirmPurchase(null);
      setImpactData(null);
      loadPurchases();
    } catch (error) {
      console.error('Error finalizing purchase:', error);
      const errorMsg = extractErrorMessage(error, 'Failed to finalize purchase');
      toast.error(errorMsg);
    } finally {
      setFinalizing(null);
      setConfirmLoading(false);
    }
  };

  const handleDeletePurchase = async (purchase) => {
    setConfirmPurchase(purchase);
    setConfirmLoading(true);
    try {
      const response = await API.get(`/api/purchases/${purchase.id}/delete-impact`);
      setImpactData(response.data);
      setShowDeleteConfirm(true);
    } catch (error) {
      console.error('Error fetching delete impact:', error);
      toast.error('Failed to load confirmation data');
    } finally {
      setConfirmLoading(false);
    }
  };

  const confirmDeletePurchase = async () => {
    if (!confirmPurchase) return;
    
    setConfirmLoading(true);
    try {
      await API.delete(`/api/purchases/${confirmPurchase.id}`);
      toast.success('Purchase deleted successfully!');
      setShowDeleteConfirm(false);
      setConfirmPurchase(null);
      setImpactData(null);
      loadPurchases();
    } catch (error) {
      console.error('Error deleting purchase:', error);
      const errorMsg = extractErrorMessage(error, 'Failed to delete purchase');
      toast.error(errorMsg);
    } finally {
      setConfirmLoading(false);
    }
  };

  const handleViewPurchase = (purchase) => {
    setViewPurchase(purchase);
    setShowViewDialog(true);
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

  // Show loading spinner while data is being fetched
  if (isLoading) {
    return <PageLoadingSpinner text="Loading purchases..." />;
  }

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
            <div className="text-2xl font-bold">{safeToFixed(totalWeight, 3)}g</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Total Value</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{safeToFixed(totalValue, 2)} OMR</div>
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
                  <TableEmptyState
                    colSpan={11}
                    icon="cart"
                    title="No purchases recorded"
                    message="Start by creating your first purchase to track gold inventory and vendor transactions."
                    action={{
                      label: "Create Purchase",
                      onClick: () => handleOpenDialog(),
                      icon: ShoppingCart
                    }}
                  />
                ) : (
                  purchases.map((purchase) => (
                    <tr key={purchase.id} className="border-b hover:bg-gray-50">
                      <td className="p-3">{formatDate(purchase.date)}</td>
                      <td className="p-3">{getVendorName(purchase.vendor_party_id)}</td>
                      <td className="p-3">{purchase.description}</td>
                      <td className="p-3 text-right font-mono">{safeToFixed(purchase.weight_grams, 3)}</td>
                      <td className="p-3 text-right">{purchase.entered_purity}K</td>
                      <td className="p-3 text-right font-mono">{safeToFixed(purchase.rate_per_gram, 2)}</td>
                      <td className="p-3 text-right font-mono">{safeToFixed(purchase.amount_total, 2)}</td>
                      <td className="p-3 text-right font-mono">{safeToFixed(purchase.paid_amount_money, 2)}</td>
                      <td className="p-3 text-right font-mono font-semibold text-red-600">
                        {safeToFixed(purchase.balance_due_money, 2)}
                      </td>
                      <td className="p-3 text-center">{getStatusBadge(purchase.status)}</td>
                      <td className="p-3">
                        <div className="flex gap-2 justify-center">
                          {/* View button - always available */}
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-indigo-600 hover:text-indigo-700"
                            onClick={() => handleViewPurchase(purchase)}
                            title="View Purchase Details"
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          
                          {purchase.status === 'draft' && (
                            <>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleOpenDialog(purchase)}
                                title="Edit Purchase"
                              >
                                <Edit className="w-4 h-4" />
                              </Button>
                              <Button
                                size="sm"
                                onClick={() => handleFinalizePurchase(purchase)}
                                disabled={finalizing === purchase.id}
                                title="Finalize Purchase"
                              >
                                <CheckCircle className="w-4 h-4 mr-1" />
                                {finalizing === purchase.id ? 'Finalizing...' : 'Finalize'}
                              </Button>
                              <Button
                                size="sm"
                                variant="destructive"
                                onClick={() => handleDeletePurchase(purchase)}
                                title="Delete Purchase"
                              >
                                <Trash2 className="w-4 h-4" />
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

          {/* Pagination Controls */}
          {pagination && (
            <Pagination
              pagination={pagination}
              onPageChange={handlePageChange}
            />
          )}
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
                  <Select 
                    value={formData.vendor_party_id} 
                    onValueChange={(value) => {
                      setFormData({...formData, vendor_party_id: value});
                      validateField('vendor_party_id', value);
                    }}
                  >
                    <SelectTrigger className={errors.vendor_party_id ? 'border-red-500' : ''}>
                      <SelectValue placeholder="Select vendor" />
                    </SelectTrigger>
                    <SelectContent>
                      {vendors.map(vendor => (
                        <SelectItem key={vendor.id} value={vendor.id}>{vendor.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormErrorMessage error={errors.vendor_party_id} />
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
                    onBlur={(e) => validateField('weight_grams', e.target.value)}
                    placeholder="0.000"
                    className={errors.weight_grams ? 'border-red-500' : ''}
                  />
                  <FormErrorMessage error={errors.weight_grams} />
                </div>

                <div className="space-y-2">
                  <Label>Entered Purity *</Label>
                  <Input
                    type="number"
                    value={formData.entered_purity}
                    onChange={(e) => setFormData({...formData, entered_purity: e.target.value})}
                    onBlur={(e) => validateField('entered_purity', e.target.value)}
                    placeholder="999"
                    className={errors.entered_purity ? 'border-red-500' : ''}
                  />
                  <FormErrorMessage error={errors.entered_purity} />
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
                    onBlur={(e) => validateField('rate_per_gram', e.target.value)}
                    placeholder="0.00"
                    className={errors.rate_per_gram ? 'border-red-500' : ''}
                  />
                  <FormErrorMessage error={errors.rate_per_gram} />
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
                  onBlur={(e) => validateField('amount_total', e.target.value)}
                  placeholder="0.00"
                  className={errors.amount_total ? 'border-red-500' : ''}
                />
                <FormErrorMessage error={errors.amount_total} />
              </div>

              <div className="p-3 bg-blue-50 border border-blue-200 rounded text-sm">
                <p className="text-blue-900">
                  <strong>Note:</strong> Stock will be added at <strong>916 purity (22K)</strong> for valuation purposes, regardless of entered purity.
                </p>
              </div>

              {/* Cost Breakdown Preview - Option C */}
              {formData.weight_grams && formData.rate_per_gram && formData.amount_total && (
                <div className="mt-4 p-4 bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-300 rounded-lg">
                  <div className="flex items-center gap-2 mb-3">
                    <svg className="w-5 h-5 text-amber-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                    </svg>
                    <h4 className="font-semibold text-amber-900">Purchase Cost Breakdown</h4>
                  </div>
                  
                  <div className="space-y-2 text-sm">
                    {/* Base Calculation */}
                    <div className="flex items-center justify-between p-2 bg-white rounded border border-amber-200">
                      <span className="text-gray-700">Weight × Rate</span>
                      <span className="font-mono font-semibold text-amber-900">
                        {(parseFloat(formData.weight_grams || 0) * parseFloat(formData.rate_per_gram || 0)).toFixed(2)} OMR
                      </span>
                    </div>
                    <div className="text-xs text-gray-600 pl-2">
                      {parseFloat(formData.weight_grams || 0).toFixed(3)}g × {parseFloat(formData.rate_per_gram || 0).toFixed(2)} OMR/g
                    </div>

                    {/* Purity Info */}
                    <div className="flex items-center justify-between p-2 bg-white rounded border border-amber-200">
                      <span className="text-gray-700">Entered Purity</span>
                      <span className="font-mono font-semibold">{formData.entered_purity}K</span>
                    </div>
                    <div className="text-xs text-indigo-600 pl-2 font-medium">
                      ✓ Stock valued at 916K (22K) standard
                    </div>

                    {/* Total Amount */}
                    <div className="flex items-center justify-between p-3 bg-gradient-to-r from-amber-600 to-orange-600 text-white rounded-lg mt-3">
                      <span className="font-semibold">Total Purchase Amount</span>
                      <span className="font-mono font-bold text-xl">
                        {parseFloat(formData.amount_total || 0).toFixed(2)} OMR
                      </span>
                    </div>

                    {/* Additional charges indicator */}
                    {parseFloat(formData.amount_total || 0) !== (parseFloat(formData.weight_grams || 0) * parseFloat(formData.rate_per_gram || 0)) && (
                      <div className="text-xs text-orange-600 pl-2 mt-1 font-medium">
                        ℹ️ Amount includes adjustments: {(parseFloat(formData.amount_total || 0) - (parseFloat(formData.weight_grams || 0) * parseFloat(formData.rate_per_gram || 0))).toFixed(2)} OMR
                      </div>
                    )}
                  </div>
                </div>
              )}
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
                    onBlur={(e) => validateField('paid_amount_money', e.target.value)}
                    placeholder="0.00"
                    className={errors.paid_amount_money ? 'border-red-500' : ''}
                  />
                  <FormErrorMessage error={errors.paid_amount_money} />
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
                <div className="p-4 bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-300 rounded-lg">
                  <h4 className="font-semibold text-green-900 mb-3 flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                    Payment Breakdown
                  </h4>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center p-2 bg-white rounded border border-green-200">
                      <span className="text-gray-700">Total Amount:</span>
                      <span className="font-mono font-bold text-lg text-gray-900">{parseFloat(formData.amount_total || 0).toFixed(2)} OMR</span>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-white rounded border border-green-200">
                      <span className="text-gray-700">Paid Amount:</span>
                      <span className="font-mono font-semibold text-green-700">{parseFloat(formData.paid_amount_money || 0).toFixed(2)} OMR</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-lg mt-2">
                      <span className="font-semibold">Balance Due:</span>
                      <span className="font-mono font-bold text-xl">
                        {(parseFloat(formData.amount_total || 0) - parseFloat(formData.paid_amount_money || 0)).toFixed(2)} OMR
                      </span>
                    </div>
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
              <Button 
                variant="outline" 
                onClick={() => setShowDialog(false)} 
                className="flex-1"
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button 
                onClick={handleSavePurchase} 
                className="flex-1"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <ButtonLoadingSpinner className="mr-2" />
                    Saving...
                  </>
                ) : (
                  editingPurchase ? 'Update Purchase' : 'Create Purchase'
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Enhanced Finalize Confirmation Dialog with Comprehensive Cost Breakdown */}
      <Dialog open={showFinalizeConfirm} onOpenChange={setShowFinalizeConfirm}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold flex items-center gap-2">
              <CheckCircle className="w-6 h-6 text-yellow-600" />
              Finalize Purchase Confirmation
            </DialogTitle>
          </DialogHeader>

          {confirmPurchase && (
            <div className="space-y-6">
              {/* Purchase Header Info */}
              <div className="bg-slate-100 rounded-lg p-4 border border-slate-300">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-600">Vendor</p>
                    <p className="text-lg font-bold text-slate-900">{getVendorName(confirmPurchase.vendor_party_id)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-slate-600">Date</p>
                    <p className="text-lg font-semibold">{formatDate(confirmPurchase.date)}</p>
                  </div>
                </div>
                {confirmPurchase.description && (
                  <div className="mt-3">
                    <p className="text-sm text-slate-600">Description</p>
                    <p className="text-sm font-medium text-slate-800">{confirmPurchase.description}</p>
                  </div>
                )}
              </div>

              {/* Gold Details & Calculation Section */}
              <div className="bg-gradient-to-br from-amber-50 via-yellow-50 to-amber-50 border-2 border-amber-300 rounded-xl p-5 shadow-md">
                <h3 className="font-bold text-lg text-amber-900 mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Gold Details & Calculation
                </h3>

                {/* Gold Details Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                  <div className="bg-white rounded-lg p-3 border border-amber-200 shadow-sm">
                    <div className="text-xs text-amber-700 font-medium uppercase mb-1">Weight</div>
                    <div className="font-mono font-bold text-lg text-amber-900">
                      {(confirmPurchase.weight_grams || 0).toFixed(3)} g
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg p-3 border border-amber-200 shadow-sm">
                    <div className="text-xs text-amber-700 font-medium uppercase mb-1">Entered Purity</div>
                    <div className="font-mono font-bold text-lg text-amber-900">
                      {confirmPurchase.entered_purity || 999}K
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg p-3 border border-green-200 shadow-sm">
                    <div className="text-xs text-green-700 font-medium uppercase mb-1">Valuation Purity</div>
                    <div className="font-mono font-bold text-lg text-green-900">
                      916K (22K)
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg p-3 border border-blue-200 shadow-sm">
                    <div className="text-xs text-blue-700 font-medium uppercase mb-1">Rate per Gram</div>
                    <div className="font-mono font-bold text-lg text-blue-900">
                      {(confirmPurchase.rate_per_gram || 0).toFixed(2)} OMR
                    </div>
                  </div>
                </div>

                {/* Calculation Formula */}
                <div className="bg-gradient-to-r from-amber-100 to-yellow-100 rounded-lg p-4 border border-amber-300 mb-4">
                  <div className="text-sm font-semibold text-amber-900 mb-2">Cost Calculation:</div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-700">Weight × Rate per Gram</span>
                    <span className="font-mono font-bold text-amber-900">
                      {(confirmPurchase.weight_grams || 0).toFixed(3)}g × {(confirmPurchase.rate_per_gram || 0).toFixed(2)} OMR/g = {((confirmPurchase.weight_grams || 0) * (confirmPurchase.rate_per_gram || 0)).toFixed(2)} OMR
                    </span>
                  </div>
                </div>

                {/* Total Purchase Amount - Prominent Display */}
                <div className="bg-gradient-to-r from-amber-600 via-yellow-600 to-amber-700 rounded-xl p-4 shadow-lg border-2 border-amber-500">
                  <div className="flex items-center justify-between">
                    <span className="text-white font-bold text-base">Total Purchase Amount</span>
                    <span className="font-mono font-bold text-3xl text-white">
                      {(confirmPurchase.amount_total || 0).toFixed(2)} OMR
                    </span>
                  </div>
                  {/* Additional charges indicator */}
                  {Math.abs((confirmPurchase.amount_total || 0) - ((confirmPurchase.weight_grams || 0) * (confirmPurchase.rate_per_gram || 0))) > 0.01 && (
                    <div className="text-xs text-amber-100 mt-2 flex items-center gap-1">
                      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                      </svg>
                      Includes adjustment: {((confirmPurchase.amount_total || 0) - ((confirmPurchase.weight_grams || 0) * (confirmPurchase.rate_per_gram || 0))).toFixed(2)} OMR
                    </div>
                  )}
                </div>
              </div>

              {/* Payment Breakdown Section */}
              <div className="bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-300 rounded-xl p-5 shadow-md">
                <h3 className="font-bold text-lg text-green-900 mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                  Payment Breakdown
                </h3>

                <div className="space-y-3">
                  <div className="flex justify-between items-center p-3 bg-white rounded-lg border border-blue-200">
                    <span className="text-gray-700 font-medium">Total Amount:</span>
                    <span className="font-mono font-bold text-lg text-blue-900">
                      {(confirmPurchase.amount_total || 0).toFixed(2)} OMR
                    </span>
                  </div>
                  
                  <div className="flex justify-between items-center p-3 bg-white rounded-lg border border-green-200">
                    <span className="text-gray-700 font-medium">Paid Amount:</span>
                    <span className="font-mono font-bold text-lg text-green-700">
                      {(confirmPurchase.paid_amount_money || 0).toFixed(2)} OMR
                    </span>
                  </div>
                  
                  <div className="flex justify-between items-center p-4 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-lg shadow-md">
                    <span className="font-bold text-base">Balance Due to Vendor:</span>
                    <span className="font-mono font-bold text-2xl">
                      {(confirmPurchase.balance_due_money || 0).toFixed(2)} OMR
                    </span>
                  </div>

                  {/* Payment Details */}
                  {confirmPurchase.paid_amount_money > 0 && (
                    <div className="grid grid-cols-2 gap-3 mt-3 pt-3 border-t border-green-200">
                      <div className="bg-white rounded p-2 border border-green-100">
                        <p className="text-xs text-gray-600">Payment Mode</p>
                        <p className="font-semibold text-sm text-gray-900">{confirmPurchase.payment_mode || 'Cash'}</p>
                      </div>
                      {confirmPurchase.account_id && (
                        <div className="bg-white rounded p-2 border border-green-100">
                          <p className="text-xs text-gray-600">Payment Account</p>
                          <p className="font-semibold text-sm text-gray-900">
                            {accounts.find(a => a.id === confirmPurchase.account_id)?.name || 'N/A'}
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Gold Settlement Section - Only if applicable */}
              {(confirmPurchase.advance_in_gold_grams > 0 || confirmPurchase.exchange_in_gold_grams > 0) && (
                <div className="bg-gradient-to-br from-purple-50 to-indigo-50 border-2 border-purple-300 rounded-xl p-5 shadow-md">
                  <h3 className="font-bold text-lg text-purple-900 mb-4 flex items-center gap-2">
                    <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                    </svg>
                    Gold Settlement Details
                  </h3>

                  <div className="grid grid-cols-2 gap-3">
                    {confirmPurchase.advance_in_gold_grams > 0 && (
                      <div className="bg-white rounded-lg p-3 border border-purple-200">
                        <div className="text-xs text-purple-700 font-medium uppercase mb-1">Advance Gold Returned</div>
                        <div className="font-mono font-bold text-lg text-purple-900">
                          {(confirmPurchase.advance_in_gold_grams || 0).toFixed(3)} g
                        </div>
                        <div className="text-xs text-purple-600 mt-1">Previously given to vendor</div>
                      </div>
                    )}
                    
                    {confirmPurchase.exchange_in_gold_grams > 0 && (
                      <div className="bg-white rounded-lg p-3 border border-purple-200">
                        <div className="text-xs text-purple-700 font-medium uppercase mb-1">Exchange Gold Received</div>
                        <div className="font-mono font-bold text-lg text-purple-900">
                          {(confirmPurchase.exchange_in_gold_grams || 0).toFixed(3)} g
                        </div>
                        <div className="text-xs text-purple-600 mt-1">Gold exchanged</div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Impact Summary Section */}
              <div className="bg-gradient-to-br from-indigo-50 to-blue-50 border-2 border-indigo-300 rounded-xl p-5 shadow-md">
                <h3 className="font-bold text-lg text-indigo-900 mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Impact Summary
                </h3>

                <div className="space-y-3">
                  {/* Stock Increase */}
                  <div className="flex items-start gap-3 p-3 bg-white rounded-lg border border-green-200">
                    <div className="flex-shrink-0 w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                      <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11l5-5m0 0l5 5m-5-5v12" />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold text-gray-900">Stock Increase</p>
                      <p className="text-sm text-gray-700">
                        Inventory will increase by <span className="font-mono font-bold text-green-700">{(confirmPurchase.weight_grams || 0).toFixed(3)}g</span> at <span className="font-bold text-green-700">916 purity (22K)</span> valuation standard
                      </p>
                    </div>
                  </div>

                  {/* Vendor Payable */}
                  {confirmPurchase.balance_due_money > 0 && (
                    <div className="flex items-start gap-3 p-3 bg-white rounded-lg border border-amber-200">
                      <div className="flex-shrink-0 w-8 h-8 bg-amber-100 rounded-full flex items-center justify-center">
                        <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <div className="flex-1">
                        <p className="font-semibold text-gray-900">Vendor Payable</p>
                        <p className="text-sm text-gray-700">
                          Outstanding balance of <span className="font-mono font-bold text-amber-700">{(confirmPurchase.balance_due_money || 0).toFixed(2)} OMR</span> will be recorded as payable to vendor
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Financial Transaction */}
                  {confirmPurchase.paid_amount_money > 0 && (
                    <div className="flex items-start gap-3 p-3 bg-white rounded-lg border border-blue-200">
                      <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                        <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                      </div>
                      <div className="flex-1">
                        <p className="font-semibold text-gray-900">Financial Transaction</p>
                        <p className="text-sm text-gray-700">
                          Debit transaction of <span className="font-mono font-bold text-blue-700">{(confirmPurchase.paid_amount_money || 0).toFixed(2)} OMR</span> will be recorded in selected account
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Status Change */}
                  <div className="flex items-start gap-3 p-3 bg-white rounded-lg border border-indigo-200">
                    <div className="flex-shrink-0 w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center">
                      <Lock className="w-4 h-4 text-indigo-600" />
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold text-gray-900">Status Change</p>
                      <p className="text-sm text-gray-700">
                        Purchase status will change from <Badge className="mx-1 bg-blue-100 text-blue-800">Draft</Badge> to <Badge className="mx-1 bg-green-100 text-green-800">Finalized</Badge>
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Irreversible Action Warning */}
              <div className="bg-red-50 border-2 border-red-300 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-bold text-red-900 text-base mb-1">⚠️ IRREVERSIBLE ACTION</p>
                    <p className="text-sm text-red-800">
                      This action cannot be undone. Once finalized, the purchase will be locked and cannot be edited or deleted. 
                      All inventory, financial, and vendor records will be permanently updated.
                    </p>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 pt-2">
                <Button 
                  variant="outline" 
                  onClick={() => setShowFinalizeConfirm(false)}
                  disabled={confirmLoading}
                  className="flex-1 border-2"
                >
                  Cancel
                </Button>
                <Button 
                  onClick={confirmFinalizePurchase}
                  disabled={confirmLoading}
                  className="flex-1 bg-yellow-600 hover:bg-yellow-700 text-white font-bold"
                >
                  {confirmLoading ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Finalizing...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Confirm & Finalize Purchase
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* View Purchase Dialog - Option C Enhancement */}
      <Dialog open={showViewDialog} onOpenChange={setShowViewDialog}>
        <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-2xl font-serif">Purchase Details</DialogTitle>
          </DialogHeader>

          {viewPurchase && (
            <div className="space-y-6">
              {/* Purchase Header */}
              <div className="grid grid-cols-2 gap-6 p-4 bg-muted/50 rounded-lg">
                <div className="space-y-2">
                  <div>
                    <p className="text-xs text-muted-foreground">Purchase Date</p>
                    <p className="font-medium">{formatDate(viewPurchase.date)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Vendor</p>
                    <p className="font-semibold text-lg">{getVendorName(viewPurchase.vendor_party_id)}</p>
                  </div>
                  {viewPurchase.description && (
                    <div>
                      <p className="text-xs text-muted-foreground">Description</p>
                      <p className="font-medium text-sm">{viewPurchase.description}</p>
                    </div>
                  )}
                </div>
                <div className="space-y-2">
                  <div>
                    <p className="text-xs text-muted-foreground">Purchase Status</p>
                    <div className="mt-1">{getStatusBadge(viewPurchase.status)}</div>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Created At</p>
                    <p className="font-mono text-sm">
                      {formatDateTime(viewPurchase.created_at)}
                    </p>
                  </div>
                  {viewPurchase.finalized_at && (
                    <div>
                      <p className="text-xs text-muted-foreground">Finalized At</p>
                      <p className="font-mono text-sm">
                        {formatDateTime(viewPurchase.finalized_at)}
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* ENHANCED Gold Details Section - Option C Improvements */}
              <div className="bg-gradient-to-br from-amber-50 via-yellow-50 to-amber-50 border-2 border-amber-300 rounded-xl p-5 shadow-lg">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-bold text-lg text-amber-900 flex items-center gap-2">
                    <svg className="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Gold Details & Calculation
                  </h3>
                  <Badge className="bg-amber-100 text-amber-800 px-3 py-1">Gold Purchase</Badge>
                </div>

                {/* Gold Details Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
                  <div className="bg-white rounded-lg p-3 border-2 border-amber-200 shadow-sm">
                    <div className="text-xs text-amber-700 font-medium uppercase mb-1">Weight</div>
                    <div className="font-mono font-bold text-xl text-amber-900">
                      {(viewPurchase.weight_grams || 0).toFixed(3)} g
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-lg p-3 border-2 border-amber-200 shadow-sm">
                    <div className="text-xs text-amber-700 font-medium uppercase mb-1">Entered Purity</div>
                    <div className="font-mono font-bold text-xl text-amber-900">
                      {viewPurchase.entered_purity || 999}K
                    </div>
                    <div className="text-xs text-amber-600 mt-1">As received</div>
                  </div>
                  
                  <div className="bg-white rounded-lg p-3 border-2 border-green-200 shadow-sm">
                    <div className="text-xs text-green-700 font-medium uppercase mb-1">Valuation Purity</div>
                    <div className="font-mono font-bold text-xl text-green-900">
                      916K (22K)
                    </div>
                    <div className="text-xs text-green-600 mt-1">For inventory</div>
                  </div>
                  
                  <div className="bg-white rounded-lg p-3 border-2 border-blue-200 shadow-sm">
                    <div className="text-xs text-blue-700 font-medium uppercase mb-1">Rate per Gram</div>
                    <div className="font-mono font-bold text-xl text-blue-900">
                      {(viewPurchase.rate_per_gram || 0).toFixed(2)} OMR
                    </div>
                  </div>
                </div>

                {/* Calculation Breakdown */}
                <div className="bg-gradient-to-r from-amber-100 to-yellow-100 rounded-lg p-4 border border-amber-300 mb-4">
                  <div className="text-sm font-semibold text-amber-900 mb-3">Cost Calculation:</div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-700">Base Amount:</span>
                      <span className="font-mono font-semibold text-amber-900">
                        {(viewPurchase.weight_grams || 0).toFixed(3)}g × {(viewPurchase.rate_per_gram || 0).toFixed(2)} OMR/g = {((viewPurchase.weight_grams || 0) * (viewPurchase.rate_per_gram || 0)).toFixed(2)} OMR
                      </span>
                    </div>
                    {viewPurchase.entered_purity !== 916 && (
                      <div className="text-xs text-amber-700 italic border-t pt-2 border-amber-200">
                        💡 Note: Gold entered as {viewPurchase.entered_purity}K but valued at 916K (22K standard) for inventory purposes
                      </div>
                    )}
                  </div>
                </div>

                {/* Total Amount Card */}
                <div className="bg-gradient-to-r from-amber-600 via-yellow-600 to-amber-700 rounded-xl p-5 shadow-xl border-2 border-amber-400">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-amber-100 text-xs font-medium uppercase mb-1">Total Purchase Amount</div>
                      <div className="font-mono font-black text-4xl text-white">
                        {(viewPurchase.amount_total || 0).toFixed(2)} <span className="text-xl text-amber-200">OMR</span>
                      </div>
                    </div>
                    <svg className="w-16 h-16 text-white/30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Payment Breakdown Section */}
              <div className="bg-gradient-to-br from-green-50 via-emerald-50 to-green-50 border-2 border-green-300 rounded-xl p-5 shadow-lg">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-bold text-lg text-green-900 flex items-center gap-2">
                    <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Payment Breakdown
                  </h3>
                  <Badge className="bg-green-100 text-green-800 px-3 py-1">Financial Details</Badge>
                </div>

                {/* Payment Details Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div className="bg-white rounded-lg p-4 border-2 border-blue-200 shadow-sm">
                    <div className="text-xs text-blue-700 font-medium uppercase mb-1">Total Amount</div>
                    <div className="font-mono font-bold text-2xl text-blue-900">
                      {(viewPurchase.amount_total || 0).toFixed(2)} OMR
                    </div>
                    <div className="text-xs text-blue-600 mt-1">Purchase value</div>
                  </div>
                  
                  <div className="bg-white rounded-lg p-4 border-2 border-green-200 shadow-sm">
                    <div className="text-xs text-green-700 font-medium uppercase mb-1">Paid Amount</div>
                    <div className="font-mono font-bold text-2xl text-green-900">
                      {(viewPurchase.paid_amount_money || 0).toFixed(2)} OMR
                    </div>
                    <div className="text-xs text-green-600 mt-1">Payment made</div>
                  </div>
                  
                  <div className="bg-white rounded-lg p-4 border-2 border-red-200 shadow-sm">
                    <div className="text-xs text-red-700 font-medium uppercase mb-1">Balance Due</div>
                    <div className="font-mono font-bold text-2xl text-red-900">
                      {(viewPurchase.balance_due_money || 0).toFixed(2)} OMR
                    </div>
                    <div className="text-xs text-red-600 mt-1">Outstanding to vendor</div>
                  </div>
                </div>

                {/* Payment Mode & Account */}
                <div className="bg-white rounded-lg p-4 border border-green-200">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-green-700 font-medium">Payment Mode:</span>
                      <span className="ml-2 font-mono">{viewPurchase.payment_mode || 'Cash'}</span>
                    </div>
                    {viewPurchase.account_id && (
                      <div>
                        <span className="text-green-700 font-medium">Account Used:</span>
                        <span className="ml-2 font-mono">{accounts.find(a => a.id === viewPurchase.account_id)?.name || 'N/A'}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Gold Settlement Section (if applicable) */}
              {(viewPurchase.advance_in_gold_grams || viewPurchase.exchange_in_gold_grams) && (
                <div className="bg-gradient-to-br from-purple-50 via-indigo-50 to-purple-50 border-2 border-purple-300 rounded-xl p-5 shadow-lg">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-bold text-lg text-purple-900 flex items-center gap-2">
                      <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                      </svg>
                      Gold Settlement
                    </h3>
                    <Badge className="bg-purple-100 text-purple-800 px-3 py-1">Gold Exchange</Badge>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    {viewPurchase.advance_in_gold_grams > 0 && (
                      <div className="bg-white rounded-lg p-4 border-2 border-purple-200 shadow-sm">
                        <div className="text-xs text-purple-700 font-medium uppercase mb-1">Advance Gold Returned</div>
                        <div className="font-mono font-bold text-xl text-purple-900">
                          {(viewPurchase.advance_in_gold_grams || 0).toFixed(3)} g
                        </div>
                        <div className="text-xs text-purple-600 mt-1">Gold given back to vendor</div>
                      </div>
                    )}
                    
                    {viewPurchase.exchange_in_gold_grams > 0 && (
                      <div className="bg-white rounded-lg p-4 border-2 border-indigo-200 shadow-sm">
                        <div className="text-xs text-indigo-700 font-medium uppercase mb-1">Exchange Gold</div>
                        <div className="font-mono font-bold text-xl text-indigo-900">
                          {(viewPurchase.exchange_in_gold_grams || 0).toFixed(3)} g
                        </div>
                        <div className="text-xs text-indigo-600 mt-1">Gold exchanged</div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-3 pt-4">
                <Button
                  variant="outline"
                  onClick={() => setShowViewDialog(false)}
                  className="flex-1"
                >
                  Close
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <ConfirmationDialog
        open={showDeleteConfirm}
        onOpenChange={setShowDeleteConfirm}
        onConfirm={confirmDeletePurchase}
        title="Delete Purchase?"
        description={`Are you sure you want to delete this purchase from ${confirmPurchase ? getVendorName(confirmPurchase.vendor_party_id) : ''}?`}
        impact={impactData}
        actionLabel="Delete Purchase"
        actionType="danger"
        loading={confirmLoading}
      />
    </div>
  );
}

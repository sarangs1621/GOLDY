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
import { Plus, FileText, Trash2, Edit, AlertTriangle } from 'lucide-react';

export default function JobCardsPage() {
  const [jobcards, setJobcards] = useState([]);
  const [parties, setParties] = useState([]);
  const [inventoryHeaders, setInventoryHeaders] = useState([]);
  const [showDialog, setShowDialog] = useState(false);
  const [editingJobCard, setEditingJobCard] = useState(null);
  const [showConvertDialog, setShowConvertDialog] = useState(false);
  const [convertingJobCard, setConvertingJobCard] = useState(null);
  const [convertData, setConvertData] = useState({
    customer_type: 'saved',
    customer_id: '',
    customer_name: '',
    walk_in_name: '',
    walk_in_phone: ''
  });
  const [formData, setFormData] = useState({
    card_type: 'individual',
    customer_type: 'saved',  // 'saved' or 'walk_in'
    customer_id: '',
    customer_name: '',
    walk_in_name: '',
    walk_in_phone: '',
    worker_id: '',
    delivery_date: '',
    notes: '',
    status: 'created',
    items: [{
      category: 'Chain',
      description: '',
      qty: 1,
      weight_in: 0,
      weight_out: 0,
      purity: 916,
      work_type: 'polish',
      remarks: '',
      making_charge_type: 'flat',
      making_charge_value: 0,
      vat_percent: 5
    }]
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [jobcardsRes, partiesRes, headersRes] = await Promise.all([
        axios.get(`${API}/jobcards`),
        axios.get(`${API}/parties?party_type=customer`),
        axios.get(`${API}/inventory/headers`)
      ]);
      setJobcards(jobcardsRes.data);
      setParties(partiesRes.data);
      setInventoryHeaders(headersRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    }
  };

  const handleCreateJobCard = async () => {
    try {
      // Validate based on customer type
      if (formData.customer_type === 'saved') {
        if (!formData.customer_id) {
          toast.error('Please select a customer');
          return;
        }
      } else if (formData.customer_type === 'walk_in') {
        if (!formData.walk_in_name || !formData.walk_in_name.trim()) {
          toast.error('Please enter customer name for walk-in');
          return;
        }
      }

      const data = {
        ...formData,
        items: formData.items.map(item => ({
          ...item,
          qty: parseInt(item.qty),
          weight_in: parseFloat(item.weight_in),
          weight_out: item.weight_out ? parseFloat(item.weight_out) : null,
          purity: parseInt(item.purity),
          making_charge_value: item.making_charge_value ? parseFloat(item.making_charge_value) : null,
          vat_percent: item.vat_percent ? parseFloat(item.vat_percent) : null
        }))
      };

      // Add customer name for saved customers
      if (formData.customer_type === 'saved') {
        const customer = parties.find(p => p.id === formData.customer_id);
        data.customer_name = customer?.name || '';
      }
      
      if (editingJobCard) {
        // Update existing job card
        await axios.patch(`${API}/jobcards/${editingJobCard.id}`, data);
        toast.success('Job card updated successfully');
      } else {
        // Create new job card
        await axios.post(`${API}/jobcards`, data);
        toast.success('Job card created successfully');
      }
      
      handleCloseDialog();
      loadData();
    } catch (error) {
      const errorMsg = error.response?.data?.detail || `Failed to ${editingJobCard ? 'update' : 'create'} job card`;
      toast.error(errorMsg);
    }
  };

  const handleConvertToInvoice = async (jobcard) => {
    // Open dialog to select customer type
    setConvertingJobCard(jobcard);
    setConvertData({
      customer_type: 'saved',
      customer_id: jobcard.customer_id || '',
      customer_name: jobcard.customer_name || '',
      walk_in_name: '',
      walk_in_phone: ''
    });
    setShowConvertDialog(true);
  };

  const handleConfirmConvert = async () => {
    try {
      const payload = {
        customer_type: convertData.customer_type,
      };

      if (convertData.customer_type === 'saved') {
        if (!convertData.customer_id) {
          toast.error('Please select a customer');
          return;
        }
        payload.customer_id = convertData.customer_id;
        payload.customer_name = convertData.customer_name;
      } else {
        if (!convertData.walk_in_name.trim()) {
          toast.error('Please enter customer name for walk-in');
          return;
        }
        payload.walk_in_name = convertData.walk_in_name;
        payload.walk_in_phone = convertData.walk_in_phone;
      }

      const response = await axios.post(
        `${API}/jobcards/${convertingJobCard.id}/convert-to-invoice`, 
        payload
      );
      
      toast.success(`Invoice ${response.data.invoice_number} created successfully`);
      setShowConvertDialog(false);
      setConvertingJobCard(null);
      loadData();
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to convert to invoice';
      toast.error(errorMsg);
    }
  };

  const handleEditJobCard = (jobcard) => {
    setEditingJobCard(jobcard);
    // Format delivery_date to YYYY-MM-DD for input
    const deliveryDate = jobcard.delivery_date ? new Date(jobcard.delivery_date).toISOString().split('T')[0] : '';
    setFormData({
      card_type: jobcard.card_type,
      customer_type: jobcard.customer_type || 'saved',
      customer_id: jobcard.customer_id || '',
      customer_name: jobcard.customer_name || '',
      walk_in_name: jobcard.walk_in_name || '',
      walk_in_phone: jobcard.walk_in_phone || '',
      worker_id: jobcard.worker_id || '',
      delivery_date: deliveryDate,
      notes: jobcard.notes || '',
      status: jobcard.status || 'created',
      items: jobcard.items.map(item => ({
        ...item,
        making_charge_type: item.making_charge_type || 'flat',
        making_charge_value: item.making_charge_value || 0,
        vat_percent: item.vat_percent || 5
      }))
    });
    setShowDialog(true);
  };

  const handleDeleteJobCard = async (jobcardId, jobcardNumber) => {
    if (!window.confirm(`Are you sure you want to delete job card ${jobcardNumber}? This action cannot be undone.`)) {
      return;
    }

    try {
      await axios.delete(`${API}/jobcards/${jobcardId}`);
      toast.success('Job card deleted successfully');
      loadData();
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to delete job card';
      toast.error(errorMsg);
    }
  };

  const handleCloseDialog = () => {
    setShowDialog(false);
    setEditingJobCard(null);
    // Reset form to default - use first inventory header if available
    const defaultCategory = inventoryHeaders.length > 0 ? inventoryHeaders[0].name : 'Chain';
    
    setFormData({
      card_type: 'individual',
      customer_type: 'saved',
      customer_id: '',
      customer_name: '',
      walk_in_name: '',
      walk_in_phone: '',
      worker_id: '',
      delivery_date: '',
      notes: '',
      status: 'created',
      items: [{
        category: defaultCategory,
        description: '',
        qty: 1,
        weight_in: 0,
        weight_out: 0,
        purity: 916,
        work_type: 'polish',
        remarks: '',
        making_charge_type: 'flat',
        making_charge_value: 0,
        vat_percent: 5
      }]
    });
  };

  const addItem = () => {
    // Use first inventory header as default category if available
    const defaultCategory = inventoryHeaders.length > 0 ? inventoryHeaders[0].name : 'Chain';
    
    setFormData({
      ...formData,
      items: [...formData.items, {
        category: defaultCategory,
        description: '',
        qty: 1,
        weight_in: 0,
        weight_out: 0,
        purity: 916,
        work_type: 'polish',
        remarks: '',
        making_charge_type: 'flat',
        making_charge_value: 0,
        vat_percent: 5
      }]
    });
  };

  const removeItem = (index) => {
    if (formData.items.length > 1) {
      const newItems = formData.items.filter((_, idx) => idx !== index);
      setFormData({ ...formData, items: newItems });
    } else {
      toast.error('At least one item is required');
    }
  };

  const updateItem = (index, field, value) => {
    const newItems = [...formData.items];
    newItems[index][field] = value;
    setFormData({ ...formData, items: newItems });
  };

  const getStatusBadge = (status) => {
    const variants = {
      created: 'bg-blue-100 text-blue-800',
      'in progress': 'bg-yellow-100 text-yellow-800',
      completed: 'bg-green-100 text-green-800',
      delivered: 'bg-purple-100 text-purple-800',
      cancelled: 'bg-red-100 text-red-800'
    };
    return <Badge className={variants[status] || 'bg-gray-100 text-gray-800'}>{status}</Badge>;
  };

  return (
    <div data-testid="jobcards-page">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-serif font-semibold text-gray-900 mb-2">Job Cards</h1>
          <p className="text-muted-foreground">Manage repair and custom work orders</p>
        </div>
        <Button data-testid="create-jobcard-button" onClick={() => setShowDialog(true)}>
          <Plus className="w-4 h-4 mr-2" /> Create Job Card
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-xl font-serif">All Job Cards</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full" data-testid="jobcards-table">
              <thead className="bg-muted/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Job Card #</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Customer</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Items</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Actions</th>
                </tr>
              </thead>
              <tbody>
                {jobcards.map((jc) => (
                  <tr key={jc.id} className="border-t hover:bg-muted/30">
                    <td className="px-4 py-3 font-mono font-semibold">{jc.job_card_number}</td>
                    <td className="px-4 py-3">{jc.customer_name || '-'}</td>
                    <td className="px-4 py-3 text-sm">{new Date(jc.date_created).toLocaleDateString()}</td>
                    <td className="px-4 py-3">{getStatusBadge(jc.status)}</td>
                    <td className="px-4 py-3 text-sm">{jc.items.length} items</td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        {/* Edit button - show for all unlocked job cards */}
                        {!jc.locked && (
                          <Button
                            data-testid={`edit-${jc.job_card_number}`}
                            size="sm"
                            variant="outline"
                            onClick={() => handleEditJobCard(jc)}
                          >
                            <Edit className="w-4 h-4 mr-1" /> Edit
                          </Button>
                        )}
                        
                        {/* Delete button - show for all unlocked job cards */}
                        {!jc.locked && (
                          <Button
                            data-testid={`delete-${jc.job_card_number}`}
                            size="sm"
                            variant="outline"
                            className="text-red-600 hover:text-red-700"
                            onClick={() => handleDeleteJobCard(jc.id, jc.job_card_number)}
                          >
                            <Trash2 className="w-4 h-4 mr-1" /> Delete
                          </Button>
                        )}
                        
                        {/* Convert to Invoice button - only for completed job cards */}
                        {jc.status === 'completed' && (
                          <Button
                            data-testid={`convert-${jc.job_card_number}`}
                            size="sm"
                            variant="outline"
                            onClick={() => handleConvertToInvoice(jc)}
                          >
                            <FileText className="w-4 h-4 mr-1" /> Convert to Invoice
                          </Button>
                        )}
                        
                        {/* Locked indicator */}
                        {jc.locked && (
                          <Badge className="bg-gray-100 text-gray-700">
                            <AlertTriangle className="w-3 h-3 mr-1" /> Locked
                          </Badge>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingJobCard ? 'Edit Job Card' : 'Create New Job Card'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-6 mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Card Type</Label>
                <Select value={formData.card_type} onValueChange={(val) => setFormData({...formData, card_type: val})}>
                  <SelectTrigger data-testid="card-type-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="individual">Individual</SelectItem>
                    <SelectItem value="template">Template</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Customer</Label>
                <Select value={formData.customer_id} onValueChange={(val) => setFormData({...formData, customer_id: val})}>
                  <SelectTrigger data-testid="customer-select">
                    <SelectValue placeholder="Select customer" />
                  </SelectTrigger>
                  <SelectContent>
                    {parties.map(p => (
                      <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Delivery Date</Label>
                <Input
                  data-testid="delivery-date-input"
                  type="date"
                  value={formData.delivery_date}
                  onChange={(e) => setFormData({...formData, delivery_date: e.target.value})}
                />
              </div>
              <div>
                <Label>Status</Label>
                <Select value={formData.status} onValueChange={(val) => setFormData({...formData, status: val})}>
                  <SelectTrigger data-testid="status-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="created">Created</SelectItem>
                    <SelectItem value="in progress">In Progress</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                    <SelectItem value="delivered">Delivered</SelectItem>
                    <SelectItem value="cancelled">Cancelled</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Notes</Label>
                <Input
                  value={formData.notes}
                  onChange={(e) => setFormData({...formData, notes: e.target.value})}
                  placeholder="Optional notes"
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-4">
                <Label className="text-lg">Items</Label>
                <Button data-testid="add-item-button" size="sm" variant="outline" onClick={addItem}>
                  <Plus className="w-4 h-4 mr-1" /> Add Item
                </Button>
              </div>
              {formData.items.map((item, idx) => (
                <div key={idx} className="grid grid-cols-4 gap-3 mb-4 p-4 border rounded-md relative">
                  {/* Remove button */}
                  {formData.items.length > 1 && (
                    <Button
                      data-testid={`remove-item-${idx}`}
                      size="sm"
                      variant="ghost"
                      className="absolute top-2 right-2 h-8 w-8 p-0"
                      onClick={() => removeItem(idx)}
                    >
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </Button>
                  )}
                  
                  <div>
                    <Label className="text-xs">Category</Label>
                    <Select 
                      value={item.category} 
                      onValueChange={(val) => updateItem(idx, 'category', val)}
                    >
                      <SelectTrigger data-testid={`item-category-${idx}`}>
                        <SelectValue placeholder="Select category" />
                      </SelectTrigger>
                      <SelectContent>
                        {inventoryHeaders.map(header => (
                          <SelectItem key={header.id} value={header.name}>
                            {header.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-xs">Description</Label>
                    <Input
                      data-testid={`item-description-${idx}`}
                      value={item.description}
                      onChange={(e) => updateItem(idx, 'description', e.target.value)}
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Qty</Label>
                    <Input
                      data-testid={`item-qty-${idx}`}
                      type="number"
                      value={item.qty}
                      onChange={(e) => updateItem(idx, 'qty', e.target.value)}
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Weight IN (g)</Label>
                    <Input
                      data-testid={`item-weight-in-${idx}`}
                      type="number"
                      step="0.001"
                      value={item.weight_in}
                      onChange={(e) => updateItem(idx, 'weight_in', e.target.value)}
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Purity</Label>
                    <Input
                      type="number"
                      value={item.purity}
                      onChange={(e) => updateItem(idx, 'purity', e.target.value)}
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Work Type</Label>
                    <Select value={item.work_type} onValueChange={(val) => updateItem(idx, 'work_type', val)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="polish">Polish</SelectItem>
                        <SelectItem value="resize">Resize</SelectItem>
                        <SelectItem value="repair">Repair</SelectItem>
                        <SelectItem value="custom">Custom</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {/* Making Charge Type */}
                  <div>
                    <Label className="text-xs">Making Charge Type</Label>
                    <Select 
                      value={item.making_charge_type || 'flat'} 
                      onValueChange={(val) => updateItem(idx, 'making_charge_type', val)}
                    >
                      <SelectTrigger data-testid={`making-charge-type-${idx}`}>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="flat">Flat Rate</SelectItem>
                        <SelectItem value="per_gram">Per Gram</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {/* Making Charge Value */}
                  <div>
                    <Label className="text-xs">
                      Making Charge ({item.making_charge_type === 'per_gram' ? 'OMR/g' : 'OMR'})
                    </Label>
                    <Input
                      data-testid={`making-charge-value-${idx}`}
                      type="number"
                      step="0.001"
                      value={item.making_charge_value || 0}
                      onChange={(e) => updateItem(idx, 'making_charge_value', e.target.value)}
                    />
                  </div>
                  
                  {/* VAT Percent */}
                  <div>
                    <Label className="text-xs">VAT %</Label>
                    <Input
                      data-testid={`vat-percent-${idx}`}
                      type="number"
                      step="0.1"
                      value={item.vat_percent || 5}
                      onChange={(e) => updateItem(idx, 'vat_percent', e.target.value)}
                    />
                  </div>
                  
                  <div className="col-span-2">
                    <Label className="text-xs">Remarks</Label>
                    <Input
                      value={item.remarks}
                      onChange={(e) => updateItem(idx, 'remarks', e.target.value)}
                    />
                  </div>
                </div>
              ))}
            </div>

            <Button data-testid="save-jobcard-button" onClick={handleCreateJobCard} className="w-full">
              {editingJobCard ? 'Update Job Card' : 'Create Job Card'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Convert to Invoice Dialog */}
      <Dialog open={showConvertDialog} onOpenChange={setShowConvertDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Convert to Invoice - Select Customer Type</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-6">
            {/* Customer Type Selection */}
            <div className="space-y-3">
              <Label className="text-base font-semibold">Customer Type *</Label>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="customer_type"
                    value="saved"
                    checked={convertData.customer_type === 'saved'}
                    onChange={(e) => setConvertData({...convertData, customer_type: e.target.value})}
                    className="w-4 h-4"
                  />
                  <span className="font-medium">Saved Customer</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="customer_type"
                    value="walk_in"
                    checked={convertData.customer_type === 'walk_in'}
                    onChange={(e) => setConvertData({...convertData, customer_type: e.target.value})}
                    className="w-4 h-4"
                  />
                  <span className="font-medium">Walk-in Customer</span>
                </label>
              </div>
            </div>

            {/* Saved Customer Section */}
            {convertData.customer_type === 'saved' && (
              <div className="space-y-3 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex items-center gap-2 text-blue-700 text-sm font-medium">
                  <span>📋</span>
                  <span>Saved customers allow ledger tracking and outstanding balance</span>
                </div>
                <div className="space-y-2">
                  <Label>Select Customer *</Label>
                  <Select 
                    value={convertData.customer_id} 
                    onValueChange={(value) => {
                      const selected = parties.find(p => p.id === value);
                      setConvertData({
                        ...convertData, 
                        customer_id: value,
                        customer_name: selected?.name || ''
                      });
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select a customer" />
                    </SelectTrigger>
                    <SelectContent>
                      {parties.map(party => (
                        <SelectItem key={party.id} value={party.id}>
                          {party.name} {party.phone && `- ${party.phone}`}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            )}

            {/* Walk-in Customer Section */}
            {convertData.customer_type === 'walk_in' && (
              <div className="space-y-3 p-4 bg-amber-50 rounded-lg border border-amber-200">
                <div className="flex items-center gap-2 text-amber-700 text-sm font-medium">
                  <AlertTriangle className="w-4 h-4" />
                  <span>Walk-in customers are NOT saved in Parties. Full payment recommended.</span>
                </div>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>Customer Name *</Label>
                    <Input
                      value={convertData.walk_in_name}
                      onChange={(e) => setConvertData({...convertData, walk_in_name: e.target.value})}
                      placeholder="Enter customer name"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Phone Number</Label>
                    <Input
                      value={convertData.walk_in_phone}
                      onChange={(e) => setConvertData({...convertData, walk_in_phone: e.target.value})}
                      placeholder="Enter phone number (optional)"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => setShowConvertDialog(false)}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                onClick={handleConfirmConvert}
                className="flex-1"
              >
                Convert to Invoice
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

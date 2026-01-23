import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API, useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { Plus, FileText, Trash2, Edit, AlertTriangle, Save, FolderOpen, Settings } from 'lucide-react';

export default function JobCardsPage() {
  const { user } = useAuth();
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
    walk_in_phone: '',
    discount_amount: 0  // MODULE 7: Discount amount
  });
  
  // Template state
  const [templates, setTemplates] = useState([]);
  const [showTemplateDialog, setShowTemplateDialog] = useState(false);
  const [showManageTemplatesDialog, setShowManageTemplatesDialog] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [saveAsTemplate, setSaveAsTemplate] = useState(false);
  
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
    gold_rate_at_jobcard: '',  // MODULE 8: Gold rate at time of job card creation
    status: 'created',
    template_name: '',  // For templates
    delivery_days_offset: '',  // For templates: days from creation
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
    loadTemplates();
  }, []);

  const loadData = async () => {
    try {
      const [jobcardsRes, partiesRes, headersRes] = await Promise.all([
        axios.get(`${API}/jobcards`),
        axios.get(`${API}/parties?party_type=customer`),
        axios.get(`${API}/inventory/headers`)
      ]);
      setJobcards(jobcardsRes.data.items || []);
      setParties(partiesRes.data.items || []);
      setInventoryHeaders(headersRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await axios.get(`${API}/jobcard-templates`);
      setTemplates(response.data.items || []);
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  };

  const handleCreateJobCard = async () => {
    try {
      // Check if saving as template
      if (saveAsTemplate) {
        return await handleSaveTemplate();
      }

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

      // Confirmation for status change to completed or delivered (only when editing)
      if (editingJobCard) {
        const oldStatus = editingJobCard.status || 'created';
        const newStatus = formData.status;
        
        // Normalize statuses for comparison
        const normalizeStatus = (status) => status?.toLowerCase().replace(/\s+/g, '_');
        const oldNormalized = normalizeStatus(oldStatus);
        const newNormalized = normalizeStatus(newStatus);
        
        // Check if transitioning to completed or delivered
        if (newNormalized === 'completed' && oldNormalized !== 'completed') {
          if (!window.confirm(`Mark job card as COMPLETED?\n\nThis indicates the work is finished and ready for customer pickup.\n\nContinue?`)) {
            return;
          }
        } else if (newNormalized === 'delivered' && oldNormalized !== 'delivered') {
          if (!window.confirm(`Mark job card as DELIVERED?\n\nThis indicates the customer has received the item.\n\nThis action will allow converting to invoice.\n\nContinue?`)) {
            return;
          }
        }
      }

      const data = {
        ...formData,
        gold_rate_at_jobcard: formData.gold_rate_at_jobcard ? parseFloat(formData.gold_rate_at_jobcard) : null,
        delivery_days_offset: formData.delivery_days_offset ? parseInt(formData.delivery_days_offset) : null,
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

  // Template functions
  const handleSaveTemplate = async () => {
    try {
      if (!formData.template_name || !formData.template_name.trim()) {
        toast.error('Please enter a template name');
        return;
      }

      const templateData = {
        card_type: 'template',
        template_name: formData.template_name.trim(),
        worker_id: formData.worker_id || null,
        notes: formData.notes || null,
        gold_rate_at_jobcard: formData.gold_rate_at_jobcard ? parseFloat(formData.gold_rate_at_jobcard) : null,
        delivery_days_offset: formData.delivery_days_offset ? parseInt(formData.delivery_days_offset) : null,
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

      if (editingTemplate) {
        await axios.patch(`${API}/jobcard-templates/${editingTemplate.id}`, templateData);
        toast.success('Template updated successfully');
      } else {
        await axios.post(`${API}/jobcard-templates`, templateData);
        toast.success('Template saved successfully');
      }
      
      handleCloseDialog();
      loadTemplates();
      setShowManageTemplatesDialog(false);
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to save template';
      toast.error(errorMsg);
    }
  };

  const handleLoadTemplate = (template) => {
    // Calculate delivery date based on delivery_days_offset
    let deliveryDate = '';
    if (template.delivery_days_offset) {
      const futureDate = new Date();
      futureDate.setDate(futureDate.getDate() + template.delivery_days_offset);
      deliveryDate = futureDate.toISOString().split('T')[0];
    }

    setFormData({
      ...formData,
      card_type: 'individual', // Always create as individual job card
      worker_id: template.worker_id || '',
      notes: template.notes || '',
      gold_rate_at_jobcard: template.gold_rate_at_jobcard || '',
      delivery_date: deliveryDate,
      items: template.items.map(item => ({...item})) // Deep copy items
    });
    
    setShowTemplateDialog(false);
    toast.success(`Template "${template.template_name}" loaded`);
  };

  const handleEditTemplate = (template) => {
    setEditingTemplate(template);
    setSaveAsTemplate(true);
    
    setFormData({
      card_type: 'template',
      customer_type: 'saved',
      customer_id: '',
      customer_name: '',
      walk_in_name: '',
      walk_in_phone: '',
      worker_id: template.worker_id || '',
      delivery_date: '',
      notes: template.notes || '',
      gold_rate_at_jobcard: template.gold_rate_at_jobcard || '',
      status: 'created',
      template_name: template.template_name || '',
      delivery_days_offset: template.delivery_days_offset || '',
      items: template.items.map(item => ({...item}))
    });
    
    setShowManageTemplatesDialog(false);
    setShowDialog(true);
  };

  const handleDeleteTemplate = async (templateId, templateName) => {
    if (!window.confirm(`Are you sure you want to delete template "${templateName}"?`)) {
      return;
    }

    try {
      await axios.delete(`${API}/jobcard-templates/${templateId}`);
      toast.success('Template deleted successfully');
      loadTemplates();
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to delete template';
      toast.error(errorMsg);
    }
  };

  const handleConvertToInvoice = async (jobcard) => {
    // Open dialog to select customer type - pre-populate based on job card
    setConvertingJobCard(jobcard);
    
    if (jobcard.customer_type === 'walk_in') {
      // Job card is for walk-in customer
      setConvertData({
        customer_type: 'walk_in',
        customer_id: '',
        customer_name: '',
        walk_in_name: jobcard.walk_in_name || '',
        walk_in_phone: jobcard.walk_in_phone || '',
        discount_amount: 0  // MODULE 7: Initialize discount
      });
    } else {
      // Job card is for saved customer
      setConvertData({
        customer_type: 'saved',
        customer_id: jobcard.customer_id || '',
        customer_name: jobcard.customer_name || '',
        walk_in_name: '',
        walk_in_phone: '',
        discount_amount: 0  // MODULE 7: Initialize discount
      });
    }
    
    setShowConvertDialog(true);
  };

  const handleConfirmConvert = async () => {
    try {
      const payload = {
        customer_type: convertData.customer_type,
        discount_amount: parseFloat(convertData.discount_amount) || 0  // MODULE 7: Include discount
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
      gold_rate_at_jobcard: jobcard.gold_rate_at_jobcard || '',  // MODULE 8: Load gold rate
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
    setEditingTemplate(null);
    setSaveAsTemplate(false);
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
      gold_rate_at_jobcard: '',  // MODULE 8: Reset gold rate
      status: 'created',
      template_name: '',
      delivery_days_offset: '',
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
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            onClick={() => setShowManageTemplatesDialog(true)}
          >
            <Settings className="w-4 h-4 mr-2" /> Manage Templates
          </Button>
          <Button data-testid="create-jobcard-button" onClick={() => setShowDialog(true)}>
            <Plus className="w-4 h-4 mr-2" /> Create Job Card
          </Button>
        </div>
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
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span>{jc.customer_type === 'walk_in' ? jc.walk_in_name : jc.customer_name || '-'}</span>
                        {jc.customer_type === 'walk_in' && (
                          <Badge className="bg-amber-100 text-amber-800 text-xs">Walk-in</Badge>
                        )}
                      </div>
                    </td>
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
              {editingTemplate ? 'Edit Template' : editingJobCard ? 'Edit Job Card' : saveAsTemplate ? 'Save as Template' : 'Create New Job Card'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-6 mt-4">
            {/* Load Template Button - Only show when creating new job card */}
            {!editingJobCard && !saveAsTemplate && !editingTemplate && (
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowTemplateDialog(true)}
                  className="flex-1"
                >
                  <FolderOpen className="w-4 h-4 mr-2" /> Load from Template
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setSaveAsTemplate(true)}
                  className="flex-1"
                  disabled={user?.role !== 'admin'}
                >
                  <Save className="w-4 h-4 mr-2" /> Save as Template {user?.role !== 'admin' && '(Admin Only)'}
                </Button>
              </div>
            )}

            {/* Template Name Field - Show when saving as template */}
            {(saveAsTemplate || editingTemplate) && (
              <div className="p-4 bg-amber-50 rounded-lg border border-amber-200">
                <Label className="text-base font-semibold">Template Name *</Label>
                <Input
                  value={formData.template_name}
                  onChange={(e) => setFormData({...formData, template_name: e.target.value})}
                  placeholder="Enter template name (e.g., 'Standard Ring Polish')"
                  className="mt-2"
                />
                <p className="text-xs text-amber-700 mt-1">This template will be available to all users</p>
              </div>
            )}

            {/* Customer Type Selection - Hide for templates */}
            {!saveAsTemplate && !editingTemplate && (
              <div className="mb-6 space-y-3 p-4 bg-gray-50 rounded-lg border">
                <Label className="text-base font-semibold">Customer Type *</Label>
                <div className="flex gap-6">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="job_customer_type"
                      value="saved"
                      checked={formData.customer_type === 'saved'}
                      onChange={(e) => setFormData({
                        ...formData, 
                        customer_type: e.target.value,
                        walk_in_name: '',
                        walk_in_phone: ''
                      })}
                      className="w-4 h-4"
                    />
                    <span className="font-medium">Saved Customer</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="job_customer_type"
                      value="walk_in"
                      checked={formData.customer_type === 'walk_in'}
                      onChange={(e) => setFormData({
                        ...formData, 
                        customer_type: e.target.value,
                        customer_id: '',
                        customer_name: ''
                      })}
                      className="w-4 h-4"
                    />
                    <span className="font-medium">Walk-in Customer</span>
                  </label>
                </div>
              </div>
            )}

            {/* Grid for Card Type and Customer Selection - Hide for templates */}
            {!saveAsTemplate && !editingTemplate && (
              <div className="grid grid-cols-2 gap-4">
                {/* Saved Customer Section */}
                {formData.customer_type === 'saved' && (
                  <div className="col-span-2">
                    <Label>Customer *</Label>
                    <Select value={formData.customer_id} onValueChange={(val) => {
                      const selected = parties.find(p => p.id === val);
                      setFormData({
                        ...formData, 
                        customer_id: val,
                        customer_name: selected?.name || ''
                      });
                    }}>
                      <SelectTrigger data-testid="customer-select">
                        <SelectValue placeholder="Select customer" />
                      </SelectTrigger>
                      <SelectContent>
                        {parties.map(p => (
                          <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground mt-1">
                      ✓ Ledger tracking and outstanding balance enabled
                    </p>
                  </div>
                )}
                
                {/* Walk-in Customer Section */}
                {formData.customer_type === 'walk_in' && (
                  <>
                    <div>
                      <Label>Customer Name *</Label>
                      <Input
                        data-testid="walk-in-name-input"
                        value={formData.walk_in_name}
                        onChange={(e) => setFormData({...formData, walk_in_name: e.target.value})}
                        placeholder="Enter customer name"
                      />
                    </div>
                    <div>
                      <Label>Phone Number</Label>
                      <Input
                        data-testid="walk-in-phone-input"
                        value={formData.walk_in_phone}
                        onChange={(e) => setFormData({...formData, walk_in_phone: e.target.value})}
                        placeholder="Enter phone (optional)"
                      />
                      <p className="text-xs text-amber-600 mt-1">
                        ⚠ Walk-in customers are NOT saved in Parties
                      </p>
                    </div>
                  </>
                )}
              </div>
            )}
            
            <div className="grid grid-cols-2 gap-4">
              {/* For templates: show days offset; For job cards: show actual date */}
              {(saveAsTemplate || editingTemplate) ? (
                <div>
                  <Label>Delivery Days from Creation</Label>
                  <Input
                    type="number"
                    min="0"
                    value={formData.delivery_days_offset}
                    onChange={(e) => setFormData({...formData, delivery_days_offset: e.target.value})}
                    placeholder="e.g., 7"
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Number of days from job card creation to delivery
                  </p>
                </div>
              ) : (
                <div>
                  <Label>Delivery Date</Label>
                  <Input
                    data-testid="delivery-date-input"
                    type="date"
                    value={formData.delivery_date}
                    onChange={(e) => setFormData({...formData, delivery_date: e.target.value})}
                  />
                </div>
              )}
              
              {/* Hide status field for templates */}
              {!saveAsTemplate && !editingTemplate && (
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
              )}
            </div>
            
            {/* MODULE 8: Gold Rate Field */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Gold Rate (per gram) - OMR</Label>
                <Input
                  data-testid="gold-rate-input"
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.gold_rate_at_jobcard}
                  onChange={(e) => setFormData({...formData, gold_rate_at_jobcard: e.target.value})}
                  placeholder="e.g., 20.00"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Optional: This rate will auto-fill when converting to invoice
                </p>
              </div>
            </div>
            
            <div>
              <Label>Notes {(saveAsTemplate || editingTemplate) && '/ Instructions'}</Label>
              <Input
                value={formData.notes}
                onChange={(e) => setFormData({...formData, notes: e.target.value})}
                placeholder={(saveAsTemplate || editingTemplate) ? "Optional instructions for using this template" : "Optional notes"}
              />
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
              {editingTemplate ? 'Update Template' : saveAsTemplate ? 'Save Template' : editingJobCard ? 'Update Job Card' : 'Create Job Card'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Load Template Dialog */}
      <Dialog open={showTemplateDialog} onOpenChange={setShowTemplateDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Load from Template</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            {templates.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <p>No templates available</p>
                <p className="text-sm mt-2">Admins can create templates by using "Save as Template" button</p>
              </div>
            ) : (
              <div className="grid gap-3">
                {templates.map((template) => (
                  <Card key={template.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h3 className="font-semibold text-lg">{template.template_name}</h3>
                          {template.notes && (
                            <p className="text-sm text-muted-foreground mt-1">{template.notes}</p>
                          )}
                          <div className="flex gap-4 mt-2 text-xs text-muted-foreground">
                            <span>Items: {template.items?.length || 0}</span>
                            {template.delivery_days_offset && (
                              <span>Delivery: {template.delivery_days_offset} days</span>
                            )}
                            {template.gold_rate_at_jobcard && (
                              <span>Gold Rate: {template.gold_rate_at_jobcard} OMR/g</span>
                            )}
                          </div>
                        </div>
                        <Button
                          size="sm"
                          onClick={() => handleLoadTemplate(template)}
                        >
                          Load
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Manage Templates Dialog */}
      <Dialog open={showManageTemplatesDialog} onOpenChange={setShowManageTemplatesDialog}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Manage Templates</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            {templates.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <p>No templates available</p>
                {user?.role === 'admin' && (
                  <p className="text-sm mt-2">Create your first template using "Save as Template" button when creating a job card</p>
                )}
              </div>
            ) : (
              <div className="space-y-3">
                {templates.map((template) => (
                  <Card key={template.id}>
                    <CardContent className="p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h3 className="font-semibold text-lg">{template.template_name}</h3>
                          {template.notes && (
                            <p className="text-sm text-muted-foreground mt-1">{template.notes}</p>
                          )}
                          <div className="flex gap-4 mt-2 text-xs text-muted-foreground">
                            <span>Items: {template.items?.length || 0}</span>
                            {template.delivery_days_offset && (
                              <span>Delivery: {template.delivery_days_offset} days</span>
                            )}
                            {template.gold_rate_at_jobcard && (
                              <span>Gold Rate: {template.gold_rate_at_jobcard} OMR/g</span>
                            )}
                          </div>
                          
                          {/* Display template items */}
                          <div className="mt-3 space-y-1">
                            {template.items?.map((item, idx) => (
                              <div key={idx} className="text-xs bg-gray-50 p-2 rounded">
                                <span className="font-medium">{item.category}</span>
                                {item.description && ` - ${item.description}`}
                                <span className="text-muted-foreground ml-2">
                                  ({item.purity}K, {item.work_type})
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                        <div className="flex gap-2 ml-4">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleLoadTemplate(template)}
                          >
                            <FolderOpen className="w-4 h-4" />
                          </Button>
                          {user?.role === 'admin' && (
                            <>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleEditTemplate(template)}
                              >
                                <Edit className="w-4 h-4" />
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                className="text-red-600 hover:text-red-700"
                                onClick={() => handleDeleteTemplate(template.id, template.template_name)}
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Convert to Invoice Dialog */}
      <Dialog open={showConvertDialog} onOpenChange={setShowConvertDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Convert to Invoice - Customer Details</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-6">
            {/* Info about job card customer type */}
            {convertingJobCard && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
                <span className="font-semibold">Job Card Customer: </span>
                {convertingJobCard.customer_type === 'walk_in' 
                  ? `Walk-in (${convertingJobCard.walk_in_name})`
                  : `Saved Customer (${convertingJobCard.customer_name})`
                }
              </div>
            )}
            
            {/* MODULE 8: Display Gold Rate from Job Card */}
            {convertingJobCard && convertingJobCard.gold_rate_at_jobcard && (
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm">
                <span className="font-semibold text-amber-900">💰 Gold Rate from Job Card: </span>
                <span className="text-amber-800 font-mono">{convertingJobCard.gold_rate_at_jobcard} OMR/gram</span>
                <p className="text-xs text-amber-700 mt-1">This rate will be auto-filled in the invoice</p>
              </div>
            )}
            
            {/* Customer Type Selection */}
            <div className="space-y-3">
              <Label className="text-base font-semibold">Invoice Customer Type *</Label>
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

            {/* MODULE 7: Discount Amount Field */}
            <div className="space-y-2">
              <Label>Discount Amount (OMR)</Label>
              <Input
                type="number"
                step="0.001"
                min="0"
                value={convertData.discount_amount || ''}
                onChange={(e) => setConvertData({...convertData, discount_amount: e.target.value})}
                placeholder="0.000"
              />
              <p className="text-xs text-gray-500">Optional: Enter discount amount to be applied before VAT calculation</p>
            </div>

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

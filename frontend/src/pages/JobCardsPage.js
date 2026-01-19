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
import { Plus, FileText } from 'lucide-react';

export default function JobCardsPage() {
  const [jobcards, setJobcards] = useState([]);
  const [parties, setParties] = useState([]);
  const [showDialog, setShowDialog] = useState(false);
  const [formData, setFormData] = useState({
    card_type: 'individual',
    customer_id: '',
    worker_id: '',
    delivery_date: '',
    notes: '',
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
      const [jobcardsRes, partiesRes] = await Promise.all([
        axios.get(`${API}/jobcards`),
        axios.get(`${API}/parties?party_type=customer`)
      ]);
      setJobcards(jobcardsRes.data);
      setParties(partiesRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    }
  };

  const handleCreateJobCard = async () => {
    try {
      const customer = parties.find(p => p.id === formData.customer_id);
      const data = {
        ...formData,
        customer_name: customer?.name || '',
        items: formData.items.map(item => ({
          ...item,
          qty: parseInt(item.qty),
          weight_in: parseFloat(item.weight_in),
          weight_out: item.weight_out ? parseFloat(item.weight_out) : null,
          purity: parseInt(item.purity)
        }))
      };
      
      await axios.post(`${API}/jobcards`, data);
      toast.success('Job card created successfully');
      setShowDialog(false);
      loadData();
    } catch (error) {
      toast.error('Failed to create job card');
    }
  };

  const handleConvertToInvoice = async (jobcardId) => {
    try {
      const response = await axios.post(`${API}/jobcards/${jobcardId}/convert-to-invoice`);
      toast.success(`Invoice ${response.data.invoice_number} created successfully`);
      loadData();
    } catch (error) {
      toast.error('Failed to convert to invoice');
    }
  };

  const addItem = () => {
    setFormData({
      ...formData,
      items: [...formData.items, {
        category: 'Chain',
        description: '',
        qty: 1,
        weight_in: 0,
        weight_out: 0,
        purity: 916,
        work_type: 'polish',
        remarks: ''
      }]
    });
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
                      {jc.status === 'completed' && (
                        <Button
                          data-testid={`convert-${jc.job_card_number}`}
                          size="sm"
                          variant="outline"
                          onClick={() => handleConvertToInvoice(jc.id)}
                        >
                          <FileText className="w-4 h-4 mr-1" /> Convert to Invoice
                        </Button>
                      )}
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
            <DialogTitle>Create New Job Card</DialogTitle>
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
                <div key={idx} className="grid grid-cols-4 gap-3 mb-4 p-4 border rounded-md">
                  <div>
                    <Label className="text-xs">Category</Label>
                    <Input
                      data-testid={`item-category-${idx}`}
                      value={item.category}
                      onChange={(e) => updateItem(idx, 'category', e.target.value)}
                    />
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

            <Button data-testid="save-jobcard-button" onClick={handleCreateJobCard} className="w-full">Create Job Card</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

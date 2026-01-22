import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { API } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '../components/ui/alert-dialog';
import { toast } from 'sonner';
import { Plus, Users as UsersIcon, Edit, Trash2, Eye, TrendingUp, TrendingDown, Search, Calendar } from 'lucide-react';

export default function PartiesPage() {
  const [parties, setParties] = useState([]);
  const [showDialog, setShowDialog] = useState(false);
  const [showLedgerDialog, setShowLedgerDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showGoldDepositDialog, setShowGoldDepositDialog] = useState(false);
  const [editingParty, setEditingParty] = useState(null);
  const [deletingParty, setDeleteingParty] = useState(null);
  const [ledgerData, setLedgerData] = useState(null);
  const [goldEntries, setGoldEntries] = useState([]);
  const [moneyLedger, setMoneyLedger] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  
  // Filters for party detail view
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [ledgerSearchTerm, setLedgerSearchTerm] = useState('');
  
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    address: '',
    party_type: 'customer',
    notes: ''
  });
  
  // MODULE 9: Gold deposit form data
  const [depositFormData, setDepositFormData] = useState({
    weight_grams: '',
    purity_entered: '',
    purpose: 'job_work',
    notes: ''
  });

  useEffect(() => {
    loadParties();
  }, []);

  const loadParties = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/parties`);
      setParties(response.data);
    } catch (error) {
      toast.error('Failed to load parties');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!formData.name.trim()) {
      toast.error('Name is required');
      return;
    }

    try {
      if (editingParty) {
        await axios.patch(`${API}/parties/${editingParty.id}`, formData);
        toast.success('Party updated successfully');
      } else {
        await axios.post(`${API}/parties`, formData);
        toast.success('Party created successfully');
      }
      
      setShowDialog(false);
      setEditingParty(null);
      setFormData({
        name: '',
        phone: '',
        address: '',
        party_type: 'customer',
        notes: ''
      });
      loadParties();
    } catch (error) {
      toast.error(editingParty ? 'Failed to update party' : 'Failed to create party');
    }
  };

  const handleEdit = (party) => {
    setEditingParty(party);
    setFormData({
      name: party.name,
      phone: party.phone || '',
      address: party.address || '',
      party_type: party.party_type,
      notes: party.notes || ''
    });
    setShowDialog(true);
  };

  const handleDelete = async () => {
    try {
      await axios.delete(`${API}/parties/${deletingParty.id}`);
      toast.success('Party deleted successfully');
      setShowDeleteDialog(false);
      setDeleteingParty(null);
      loadParties();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete party');
    }
  };

  const handleViewLedger = async (party) => {
    try {
      // Fetch comprehensive summary
      const summaryResponse = await axios.get(`${API}/parties/${party.id}/summary`);
      setLedgerData(summaryResponse.data);
      
      // Fetch gold ledger entries
      const goldResponse = await axios.get(`${API}/gold-ledger?party_id=${party.id}`);
      setGoldEntries(goldResponse.data);
      
      // Fetch invoices and transactions for money ledger
      const ledgerResponse = await axios.get(`${API}/parties/${party.id}/ledger`);
      
      // Combine invoices and transactions into a unified money ledger
      const combinedLedger = [];
      
      // Add invoices
      ledgerResponse.data.invoices.forEach(inv => {
        combinedLedger.push({
          id: inv.id,
          date: inv.date,
          type: 'Invoice',
          reference: inv.invoice_number,
          amount: inv.grand_total,
          balance: inv.balance_due,
          status: inv.payment_status
        });
      });
      
      // Add transactions
      ledgerResponse.data.transactions.forEach(txn => {
        combinedLedger.push({
          id: txn.id,
          date: txn.date,
          type: txn.transaction_type === 'credit' ? 'Receipt' : 'Payment',
          reference: txn.transaction_number,
          amount: txn.amount,
          balance: null,
          notes: txn.notes
        });
      });
      
      // Sort by date descending
      combinedLedger.sort((a, b) => new Date(b.date) - new Date(a.date));
      setMoneyLedger(combinedLedger);
      
      // Reset filters
      setDateFrom('');
      setDateTo('');
      setLedgerSearchTerm('');
      
      setShowLedgerDialog(true);
    } catch (error) {
      toast.error('Failed to load party details');
      console.error(error);
    }
  };

  // MODULE 9: Handle opening gold deposit dialog
  const handleOpenGoldDeposit = () => {
    setDepositFormData({
      weight_grams: '',
      purity_entered: '',
      purpose: 'job_work',
      notes: ''
    });
    setShowGoldDepositDialog(true);
  };

  // MODULE 9: Handle creating gold deposit
  const handleCreateGoldDeposit = async () => {
    // Validation
    if (!depositFormData.weight_grams || parseFloat(depositFormData.weight_grams) <= 0) {
      toast.error('Please enter a valid weight');
      return;
    }
    if (!depositFormData.purity_entered || parseFloat(depositFormData.purity_entered) <= 0) {
      toast.error('Please enter a valid purity');
      return;
    }

    try {
      setLoading(true);
      const depositPayload = {
        party_id: ledgerData.party.id,
        weight_grams: parseFloat(depositFormData.weight_grams),
        purity_entered: parseInt(depositFormData.purity_entered),
        purpose: depositFormData.purpose,
        notes: depositFormData.notes || undefined
      };

      await axios.post(`${API}/gold-deposits`, depositPayload);
      toast.success('Gold deposit recorded successfully');
      
      // Reload gold entries and summary
      const goldResponse = await axios.get(`${API}/gold-ledger?party_id=${ledgerData.party.id}`);
      setGoldEntries(goldResponse.data);
      
      const summaryResponse = await axios.get(`${API}/parties/${ledgerData.party.id}/summary`);
      setLedgerData(summaryResponse.data);
      
      // Close dialog and reset form
      setShowGoldDepositDialog(false);
      setDepositFormData({
        weight_grams: '',
        purity_entered: '',
        purpose: 'job_work',
        notes: ''
      });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to record gold deposit');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // Filtered gold entries based on date and search
  const filteredGoldEntries = useMemo(() => {
    return goldEntries.filter(entry => {
      const entryDate = new Date(entry.date);
      const fromDate = dateFrom ? new Date(dateFrom) : null;
      const toDate = dateTo ? new Date(dateTo) : null;
      
      // Date filter
      if (fromDate && entryDate < fromDate) return false;
      if (toDate && entryDate > toDate) return false;
      
      // Search filter
      if (ledgerSearchTerm) {
        const searchLower = ledgerSearchTerm.toLowerCase();
        return (
          entry.purpose?.toLowerCase().includes(searchLower) ||
          entry.notes?.toLowerCase().includes(searchLower) ||
          entry.type?.toLowerCase().includes(searchLower)
        );
      }
      
      return true;
    });
  }, [goldEntries, dateFrom, dateTo, ledgerSearchTerm]);

  // Filtered money ledger based on date and search
  const filteredMoneyLedger = useMemo(() => {
    return moneyLedger.filter(entry => {
      const entryDate = new Date(entry.date);
      const fromDate = dateFrom ? new Date(dateFrom) : null;
      const toDate = dateTo ? new Date(dateTo) : null;
      
      // Date filter
      if (fromDate && entryDate < fromDate) return false;
      if (toDate && entryDate > toDate) return false;
      
      // Search filter
      if (ledgerSearchTerm) {
        const searchLower = ledgerSearchTerm.toLowerCase();
        return (
          entry.reference?.toLowerCase().includes(searchLower) ||
          entry.type?.toLowerCase().includes(searchLower) ||
          entry.notes?.toLowerCase().includes(searchLower)
        );
      }
      
      return true;
    });
  }, [moneyLedger, dateFrom, dateTo, ledgerSearchTerm]);

  const filteredParties = parties.filter(party => {
    const matchesSearch = party.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (party.phone && party.phone.includes(searchTerm));
    const matchesType = filterType === 'all' || party.party_type === filterType;
    return matchesSearch && matchesType;
  });

  return (
    <div data-testid="parties-page">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-serif font-semibold text-gray-900 mb-2">Parties</h1>
          <p className="text-muted-foreground">Manage customers and vendors</p>
        </div>
        <Button data-testid="add-party-button" onClick={() => {
          setEditingParty(null);
          setFormData({
            name: '',
            phone: '',
            address: '',
            party_type: 'customer',
            notes: ''
          });
          setShowDialog(true);
        }}>
          <Plus className="w-4 h-4 mr-2" /> Add Party
        </Button>
      </div>

      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search by name or phone..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="customer">Customers</SelectItem>
                <SelectItem value="vendor">Vendors</SelectItem>
                <SelectItem value="worker">Workers</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-xl font-serif">All Parties ({filteredParties.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">Loading...</div>
          ) : filteredParties.length === 0 ? (
            <div className="text-center py-12">
              <UsersIcon className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No parties found</p>
              <Button className="mt-4" onClick={() => setShowDialog(true)}>
                <Plus className="w-4 h-4 mr-2" /> Add First Party
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full" data-testid="parties-table">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Name</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Phone</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Type</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Address</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredParties.map((party) => (
                    <tr key={party.id} className="border-t hover:bg-muted/30">
                      <td className="px-4 py-3 font-medium">{party.name}</td>
                      <td className="px-4 py-3 text-sm font-mono">{party.phone || '-'}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded text-xs font-medium capitalize ${
                          party.party_type === 'customer' ? 'bg-blue-100 text-blue-800' : 
                          party.party_type === 'vendor' ? 'bg-purple-100 text-purple-800' :
                          'bg-green-100 text-green-800'
                        }`}>
                          {party.party_type}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm">{party.address || '-'}</td>
                      <td className="px-4 py-3">
                        <div className="flex justify-end gap-2">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleViewLedger(party)}
                            title="View Ledger"
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleEdit(party)}
                            title="Edit"
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => {
                              setDeleteingParty(party);
                              setShowDeleteDialog(true);
                            }}
                            className="text-destructive hover:text-destructive"
                            title="Delete"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingParty ? 'Edit Party' : 'Add New Party'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div>
              <Label>Name *</Label>
              <Input
                data-testid="party-name-input"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                required
              />
            </div>
            <div>
              <Label>Phone</Label>
              <Input
                data-testid="party-phone-input"
                value={formData.phone}
                onChange={(e) => setFormData({...formData, phone: e.target.value})}
              />
            </div>
            <div>
              <Label>Type</Label>
              <Select value={formData.party_type} onValueChange={(val) => setFormData({...formData, party_type: val})}>
                <SelectTrigger data-testid="party-type-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="customer">Customer</SelectItem>
                  <SelectItem value="vendor">Vendor</SelectItem>
                  <SelectItem value="worker">Worker</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Address</Label>
              <Input
                value={formData.address}
                onChange={(e) => setFormData({...formData, address: e.target.value})}
              />
            </div>
            <div>
              <Label>Notes</Label>
              <Input
                value={formData.notes}
                onChange={(e) => setFormData({...formData, notes: e.target.value})}
              />
            </div>
            <Button data-testid="save-party-button" onClick={handleCreate} className="w-full">
              {editingParty ? 'Update Party' : 'Save Party'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={showLedgerDialog} onOpenChange={setShowLedgerDialog}>
        <DialogContent className="max-w-7xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-2xl">Party Report - {ledgerData?.party?.name}</DialogTitle>
            <p className="text-sm text-muted-foreground">
              {ledgerData?.party?.party_type && (
                <span className="capitalize">{ledgerData.party.party_type}</span>
              )}
              {ledgerData?.party?.phone && ` • ${ledgerData.party.phone}`}
            </p>
          </DialogHeader>
          {ledgerData && (
            <div className="space-y-6 mt-4">
              {/* Summary Cards - 4 cards in a grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Gold They Owe Us */}
                <Card className="border-amber-200 bg-amber-50">
                  <CardContent className="pt-6">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-xs text-muted-foreground font-medium uppercase">Gold They Owe Us</p>
                        <p className="text-2xl font-bold text-amber-700 mt-1">
                          {ledgerData.gold.gold_due_from_party.toFixed(3)}g
                        </p>
                      </div>
                      <TrendingDown className="w-5 h-5 text-amber-600" />
                    </div>
                  </CardContent>
                </Card>

                {/* Gold We Owe Them */}
                <Card className="border-orange-200 bg-orange-50">
                  <CardContent className="pt-6">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-xs text-muted-foreground font-medium uppercase">Gold We Owe Them</p>
                        <p className="text-2xl font-bold text-orange-700 mt-1">
                          {ledgerData.gold.gold_due_to_party.toFixed(3)}g
                        </p>
                      </div>
                      <TrendingUp className="w-5 h-5 text-orange-600" />
                    </div>
                  </CardContent>
                </Card>

                {/* Money They Owe Us */}
                <Card className="border-green-200 bg-green-50">
                  <CardContent className="pt-6">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-xs text-muted-foreground font-medium uppercase">Money They Owe Us</p>
                        <p className="text-2xl font-bold text-green-700 mt-1">
                          {ledgerData.money.money_due_from_party.toFixed(2)} OMR
                        </p>
                      </div>
                      <TrendingDown className="w-5 h-5 text-green-600" />
                    </div>
                  </CardContent>
                </Card>

                {/* Money We Owe Them */}
                <Card className="border-red-200 bg-red-50">
                  <CardContent className="pt-6">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-xs text-muted-foreground font-medium uppercase">Money We Owe Them</p>
                        <p className="text-2xl font-bold text-red-700 mt-1">
                          {ledgerData.money.money_due_to_party.toFixed(2)} OMR
                        </p>
                      </div>
                      <TrendingUp className="w-5 h-5 text-red-600" />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Filters Section */}
              <Card>
                <CardContent className="pt-6">
                  <div className="flex flex-wrap gap-4 items-end">
                    <div className="flex-1 min-w-[200px]">
                      <Label className="text-xs">Search</Label>
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                        <Input
                          placeholder="Search entries..."
                          value={ledgerSearchTerm}
                          onChange={(e) => setLedgerSearchTerm(e.target.value)}
                          className="pl-10"
                        />
                      </div>
                    </div>
                    <div className="min-w-[160px]">
                      <Label className="text-xs">From Date</Label>
                      <div className="relative">
                        <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                        <Input
                          type="date"
                          value={dateFrom}
                          onChange={(e) => setDateFrom(e.target.value)}
                          className="pl-10"
                        />
                      </div>
                    </div>
                    <div className="min-w-[160px]">
                      <Label className="text-xs">To Date</Label>
                      <div className="relative">
                        <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                        <Input
                          type="date"
                          value={dateTo}
                          onChange={(e) => setDateTo(e.target.value)}
                          className="pl-10"
                        />
                      </div>
                    </div>
                    {(dateFrom || dateTo || ledgerSearchTerm) && (
                      <Button 
                        variant="outline" 
                        onClick={() => {
                          setDateFrom('');
                          setDateTo('');
                          setLedgerSearchTerm('');
                        }}
                      >
                        Clear Filters
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Gold Ledger Table */}
              <div>
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-amber-500"></span>
                  Gold Ledger ({filteredGoldEntries.length} entries)
                </h3>
                <Card>
                  <CardContent className="p-0">
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead className="bg-muted/50">
                          <tr>
                            <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Date</th>
                            <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Type</th>
                            <th className="px-4 py-3 text-right text-xs font-semibold uppercase">Weight (g)</th>
                            <th className="px-4 py-3 text-right text-xs font-semibold uppercase">Purity</th>
                            <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Purpose</th>
                            <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Notes</th>
                          </tr>
                        </thead>
                        <tbody>
                          {filteredGoldEntries.length === 0 ? (
                            <tr>
                              <td colSpan="6" className="px-4 py-8 text-center text-muted-foreground">
                                No gold ledger entries found
                              </td>
                            </tr>
                          ) : (
                            filteredGoldEntries.map(entry => (
                              <tr key={entry.id} className="border-t hover:bg-muted/30">
                                <td className="px-4 py-3">{new Date(entry.date).toLocaleDateString()}</td>
                                <td className="px-4 py-3">
                                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                                    entry.type === 'IN' 
                                      ? 'bg-green-100 text-green-800' 
                                      : 'bg-blue-100 text-blue-800'
                                  }`}>
                                    {entry.type}
                                  </span>
                                </td>
                                <td className="px-4 py-3 text-right font-mono">{entry.weight_grams.toFixed(3)}</td>
                                <td className="px-4 py-3 text-right font-mono">{entry.purity_entered}K</td>
                                <td className="px-4 py-3 capitalize">{entry.purpose.replace('_', ' ')}</td>
                                <td className="px-4 py-3 text-muted-foreground">{entry.notes || '-'}</td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Money Ledger Table */}
              <div>
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-green-500"></span>
                  Money Ledger ({filteredMoneyLedger.length} entries)
                </h3>
                <Card>
                  <CardContent className="p-0">
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead className="bg-muted/50">
                          <tr>
                            <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Date</th>
                            <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Type</th>
                            <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Reference</th>
                            <th className="px-4 py-3 text-right text-xs font-semibold uppercase">Amount (OMR)</th>
                            <th className="px-4 py-3 text-right text-xs font-semibold uppercase">Balance</th>
                            <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {filteredMoneyLedger.length === 0 ? (
                            <tr>
                              <td colSpan="6" className="px-4 py-8 text-center text-muted-foreground">
                                No money ledger entries found
                              </td>
                            </tr>
                          ) : (
                            filteredMoneyLedger.map(entry => (
                              <tr key={entry.id} className="border-t hover:bg-muted/30">
                                <td className="px-4 py-3">{new Date(entry.date).toLocaleDateString()}</td>
                                <td className="px-4 py-3">
                                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                                    entry.type === 'Invoice' 
                                      ? 'bg-blue-100 text-blue-800' 
                                      : entry.type === 'Receipt'
                                      ? 'bg-green-100 text-green-800'
                                      : 'bg-purple-100 text-purple-800'
                                  }`}>
                                    {entry.type}
                                  </span>
                                </td>
                                <td className="px-4 py-3 font-mono">{entry.reference}</td>
                                <td className="px-4 py-3 text-right font-mono">{entry.amount.toFixed(2)}</td>
                                <td className="px-4 py-3 text-right font-mono">
                                  {entry.balance !== null ? entry.balance.toFixed(2) : '-'}
                                </td>
                                <td className="px-4 py-3">
                                  {entry.status ? (
                                    <span className={`px-2 py-1 rounded text-xs font-medium capitalize ${
                                      entry.status === 'paid' 
                                        ? 'bg-green-100 text-green-800' 
                                        : entry.status === 'unpaid'
                                        ? 'bg-red-100 text-red-800'
                                        : 'bg-yellow-100 text-yellow-800'
                                    }`}>
                                      {entry.status}
                                    </span>
                                  ) : '-'}
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete <strong>{deletingParty?.name}</strong>. 
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

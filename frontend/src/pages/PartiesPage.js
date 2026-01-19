import React, { useState, useEffect } from 'react';
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
import { Plus, Users as UsersIcon, Edit, Trash2, Eye } from 'lucide-react';

export default function PartiesPage() {
  const [parties, setParties] = useState([]);
  const [showDialog, setShowDialog] = useState(false);
  const [showLedgerDialog, setShowLedgerDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [editingParty, setEditingParty] = useState(null);
  const [deletingParty, setDeleteingParty] = useState(null);
  const [ledgerData, setLedgerData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    address: '',
    party_type: 'customer',
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
      const response = await axios.get(`${API}/parties/${party.id}/ledger`);
      setLedgerData({ party, ...response.data });
      setShowLedgerDialog(true);
    } catch (error) {
      toast.error('Failed to load ledger');
    }
  };

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
            <Button data-testid="save-party-button" onClick={handleCreate} className="w-full">Save Party</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

import React, { useState, useEffect, useMemo } from 'react';
import { API } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '../components/ui/alert-dialog';
import { toast } from 'sonner';
import { Plus, Users, Edit, Trash2, Search, UserCheck, UserX } from 'lucide-react';
import { Badge } from '../components/ui/badge';

export default function WorkersPage() {
  const [workers, setWorkers] = useState([]);
  const [showDialog, setShowDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [editingWorker, setEditingWorker] = useState(null);
  const [deletingWorker, setDeletingWorker] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterActive, setFilterActive] = useState('all'); // 'all', 'active', 'inactive'
  
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    role: '',
    active: true
  });

  useEffect(() => {
    loadWorkers();
  }, []);

  const loadWorkers = async () => {
    try {
      setLoading(true);
      const response = await API.get(`/api/workers`);
      setWorkers(response.data.items || []);
    } catch (error) {
      toast.error('Failed to load workers');
      console.error(error);
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
      if (editingWorker) {
        await API.patch(`/api/workers/${editingWorker.id}`, formData);
        toast.success('Worker updated successfully');
      } else {
        await API.post(`/api/workers`, formData);
        toast.success('Worker created successfully');
      }
      
      setShowDialog(false);
      setEditingWorker(null);
      setFormData({
        name: '',
        phone: '',
        role: '',
        active: true
      });
      loadWorkers();
    } catch (error) {
      const errorMsg = error.response?.data?.detail || (editingWorker ? 'Failed to update worker' : 'Failed to create worker');
      toast.error(errorMsg);
      console.error(error);
    }
  };

  const handleEdit = (worker) => {
    setEditingWorker(worker);
    setFormData({
      name: worker.name,
      phone: worker.phone || '',
      role: worker.role || '',
      active: worker.active !== undefined ? worker.active : true
    });
    setShowDialog(true);
  };

  const handleDeleteClick = (worker) => {
    setDeletingWorker(worker);
    setShowDeleteDialog(true);
  };

  const handleDelete = async () => {
    try {
      await API.delete(`/api/workers/${deletingWorker.id}`);
      toast.success('Worker deleted successfully');
      setShowDeleteDialog(false);
      setDeletingWorker(null);
      loadWorkers();
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to delete worker';
      toast.error(errorMsg);
      console.error(error);
    }
  };

  const handleOpenCreateDialog = () => {
    setEditingWorker(null);
    setFormData({
      name: '',
      phone: '',
      role: '',
      active: true
    });
    setShowDialog(true);
  };

  // Filtered workers based on search and active filter
  const filteredWorkers = useMemo(() => {
    return workers.filter(worker => {
      // Active filter
      if (filterActive === 'active' && !worker.active) return false;
      if (filterActive === 'inactive' && worker.active) return false;
      
      // Search filter
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        return (
          worker.name?.toLowerCase().includes(searchLower) ||
          worker.phone?.toLowerCase().includes(searchLower) ||
          worker.role?.toLowerCase().includes(searchLower)
        );
      }
      
      return true;
    });
  }, [workers, searchTerm, filterActive]);

  return (
    <div>
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle className="flex items-center gap-2">
              <Users className="w-6 h-6" />
              Workers Management
            </CardTitle>
            <Button onClick={handleOpenCreateDialog} className="gap-2">
              <Plus className="w-4 h-4" />
              Add Worker
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* Search and Filter Section */}
          <div className="mb-6 flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Search by name, phone, or role..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={filterActive} onValueChange={setFilterActive}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Workers</SelectItem>
                <SelectItem value="active">Active Only</SelectItem>
                <SelectItem value="inactive">Inactive Only</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Workers Table */}
          {loading ? (
            <div className="text-center py-8">Loading workers...</div>
          ) : filteredWorkers.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              {searchTerm || filterActive !== 'all' 
                ? 'No workers found matching your filters' 
                : 'No workers yet. Click "Add Worker" to create one.'}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4">Name</th>
                    <th className="text-left py-3 px-4">Phone</th>
                    <th className="text-left py-3 px-4">Role</th>
                    <th className="text-left py-3 px-4">Status</th>
                    <th className="text-right py-3 px-4">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredWorkers.map((worker) => (
                    <tr key={worker.id} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4 font-medium">{worker.name}</td>
                      <td className="py-3 px-4">{worker.phone || '-'}</td>
                      <td className="py-3 px-4">{worker.role || '-'}</td>
                      <td className="py-3 px-4">
                        {worker.active ? (
                          <Badge variant="success" className="gap-1">
                            <UserCheck className="w-3 h-3" />
                            Active
                          </Badge>
                        ) : (
                          <Badge variant="secondary" className="gap-1">
                            <UserX className="w-3 h-3" />
                            Inactive
                          </Badge>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEdit(worker)}
                          className="mr-2"
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteClick(worker)}
                        >
                          <Trash2 className="w-4 h-4 text-red-500" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create/Edit Worker Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingWorker ? 'Edit Worker' : 'Add New Worker'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Enter worker name"
              />
            </div>
            <div>
              <Label htmlFor="phone">Phone</Label>
              <Input
                id="phone"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                placeholder="Enter phone number"
              />
            </div>
            <div>
              <Label htmlFor="role">Role</Label>
              <Input
                id="role"
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                placeholder="e.g., Polisher, Goldsmith, Setter"
              />
            </div>
            <div>
              <Label htmlFor="active">Status</Label>
              <Select 
                value={formData.active ? 'active' : 'inactive'}
                onValueChange={(value) => setFormData({ ...formData, active: value === 'active' })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="inactive">Inactive</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreate}>
              {editingWorker ? 'Update' : 'Create'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Worker</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{deletingWorker?.name}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-red-500 hover:bg-red-600">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { toast } from 'sonner';
import { Plus, Package } from 'lucide-react';
import Pagination from '../components/Pagination';
import { useURLPagination } from '../hooks/useURLPagination';

export default function InventoryPage() {
  const { currentPage, setPage, pagination, setPagination } = useURLPagination();
  const [headers, setHeaders] = useState([]);
  const [movements, setMovements] = useState([]);
  const [stockTotals, setStockTotals] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [showAddHeader, setShowAddHeader] = useState(false);
  const [showAddMovement, setShowAddMovement] = useState(false);
  const [newHeader, setNewHeader] = useState('');
  const [movementForm, setMovementForm] = useState({
    movement_type: 'Stock IN',
    header_id: '',
    description: '',
    qty_delta: 0,
    weight_delta: 0,
    purity: 916,
    notes: ''
  });

  useEffect(() => {
    loadInventoryData();
  }, [currentPage]);

  const loadInventoryData = async () => {
    try {
      const [headersRes, movementsRes, totalsRes, inventoryRes] = await Promise.all([
        axios.get(`${API}/inventory/headers`),
        axios.get(`${API}/inventory/movements`),
        axios.get(`${API}/inventory/stock-totals`),
        axios.get(`${API}/inventory`, {
          params: { page: currentPage, page_size: 10 }
        })
      ]);

      setHeaders(Array.isArray(headersRes.data) ? headersRes.data : []);
      setMovements(Array.isArray(movementsRes.data) ? movementsRes.data : []);
      setStockTotals(Array.isArray(totalsRes.data) ? totalsRes.data : []);
      setInventory(Array.isArray(inventoryRes.data.items) ? inventoryRes.data.items : []);
      setPagination(inventoryRes.data.pagination);
    } catch (error) {
      console.error('Failed to load inventory:', error);
      toast.error('Failed to load inventory data');
      // Ensure arrays are set even on error
      setHeaders([]);
      setMovements([]);
      setStockTotals([]);
      setInventory([]);
    }
  };

  const handleAddHeader = async () => {
    if (!newHeader.trim()) return;

    try {
      await axios.post(`${API}/inventory/headers`, { name: newHeader });
      toast.success('Category added successfully');
      setNewHeader('');
      setShowAddHeader(false);
      loadInventoryData();
    } catch (error) {
      toast.error('Failed to add category');
    }
  };

  const handleAddMovement = async () => {
    try {
      const data = {
        ...movementForm,
        qty_delta: movementForm.movement_type.includes('OUT') || movementForm.movement_type.includes('Adjustment OUT') 
          ? -Math.abs(parseFloat(movementForm.qty_delta)) 
          : Math.abs(parseFloat(movementForm.qty_delta)),
        weight_delta: movementForm.movement_type.includes('OUT') || movementForm.movement_type.includes('Adjustment OUT')
          ? -Math.abs(parseFloat(movementForm.weight_delta))
          : Math.abs(parseFloat(movementForm.weight_delta)),
        purity: parseInt(movementForm.purity)
      };

      await axios.post(`${API}/inventory/movements`, data);
      toast.success('Stock movement added successfully');
      setShowAddMovement(false);
      setMovementForm({
        movement_type: 'Stock IN',
        header_id: '',
        description: '',
        qty_delta: 0,
        weight_delta: 0,
        purity: 916,
        notes: ''
      });
      loadInventoryData();
    } catch (error) {
      toast.error('Failed to add movement');
    }
  };

  return (
    <div data-testid="inventory-page">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-serif font-semibold text-gray-900 mb-2">Inventory</h1>
          <p className="text-muted-foreground">Manage stock categories and movements</p>
        </div>
        <div className="flex gap-3">
          <Dialog open={showAddHeader} onOpenChange={setShowAddHeader}>
            <DialogTrigger asChild>
              <Button data-testid="add-category-button" variant="outline">
                <Package className="w-4 h-4 mr-2" /> Add Category
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add New Category</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 mt-4">
                <div>
                  <Label>Category Name</Label>
                  <Input
                    data-testid="category-name-input"
                    value={newHeader}
                    onChange={(e) => setNewHeader(e.target.value)}
                    placeholder="e.g., Chain, Ring, Bangle"
                  />
                </div>
                <Button data-testid="save-category-button" onClick={handleAddHeader} className="w-full">Save Category</Button>
              </div>
            </DialogContent>
          </Dialog>

          <Dialog open={showAddMovement} onOpenChange={setShowAddMovement}>
            <DialogTrigger asChild>
              <Button data-testid="add-movement-button">
                <Plus className="w-4 h-4 mr-2" /> Add Movement
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Add Stock Movement</DialogTitle>
              </DialogHeader>
              <div className="grid grid-cols-2 gap-4 mt-4">
                <div>
                  <Label>Movement Type</Label>
                  <Select value={movementForm.movement_type} onValueChange={(val) => setMovementForm({...movementForm, movement_type: val})}>
                    <SelectTrigger data-testid="movement-type-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Stock IN">Stock IN</SelectItem>
                      <SelectItem value="Stock OUT">Stock OUT</SelectItem>
                      <SelectItem value="Adjustment IN">Adjustment IN</SelectItem>
                      <SelectItem value="Adjustment OUT">Adjustment OUT</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Category</Label>
                  <Select value={movementForm.header_id} onValueChange={(val) => setMovementForm({...movementForm, header_id: val})}>
                    <SelectTrigger data-testid="category-select">
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent>
                      {Array.isArray(headers) && headers.map(h => (
                        <SelectItem key={h.id} value={h.id}>{h.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="col-span-2">
                  <Label>Description</Label>
                  <Input
                    data-testid="description-input"
                    value={movementForm.description}
                    onChange={(e) => setMovementForm({...movementForm, description: e.target.value})}
                  />
                </div>
                <div>
                  <Label>Quantity</Label>
                  <Input
                    data-testid="quantity-input"
                    type="number"
                    value={movementForm.qty_delta}
                    onChange={(e) => setMovementForm({...movementForm, qty_delta: e.target.value})}
                  />
                </div>
                <div>
                  <Label>Weight (grams)</Label>
                  <Input
                    data-testid="weight-input"
                    type="number"
                    step="0.001"
                    value={movementForm.weight_delta}
                    onChange={(e) => setMovementForm({...movementForm, weight_delta: e.target.value})}
                  />
                </div>
                <div>
                  <Label>Purity</Label>
                  <Input
                    data-testid="purity-input"
                    type="number"
                    value={movementForm.purity}
                    onChange={(e) => setMovementForm({...movementForm, purity: e.target.value})}
                  />
                </div>
                <div>
                  <Label>Notes</Label>
                  <Input
                    value={movementForm.notes}
                    onChange={(e) => setMovementForm({...movementForm, notes: e.target.value})}
                  />
                </div>
              </div>
              <Button data-testid="save-movement-button" onClick={handleAddMovement} className="w-full mt-4">Save Movement</Button>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="grid gap-6 mb-8">
        {/* Main Inventory Items Table with Pagination */}
        <Card>
          <CardHeader>
            <CardTitle className="text-xl font-serif">Inventory Items</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full" data-testid="inventory-table">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Category</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold uppercase">Quantity</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold uppercase">Weight (g)</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold uppercase">Status</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Created At</th>
                  </tr>
                </thead>
                <tbody>
                  {Array.isArray(inventory) && inventory.map((item) => (
                    <tr key={item.id} className="border-t hover:bg-muted/30">
                      <td className="px-4 py-3 font-medium">{item.category}</td>
                      <td className="px-4 py-3 text-right font-mono">{item.quantity}</td>
                      <td className="px-4 py-3 text-right font-mono">{item.weight_grams.toFixed(3)}</td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          item.status === 'low_stock' ? 'bg-amber-100 text-amber-800' : 'bg-green-100 text-green-800'
                        }`}>
                          {item.status === 'low_stock' ? 'Low Stock' : 'In Stock'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm">{new Date(item.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {inventory.length === 0 && (
                <div className="text-center py-12 text-muted-foreground">
                  <Package className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>No inventory items found</p>
                </div>
              )}
            </div>
          </CardContent>
          {pagination && <Pagination pagination={pagination} onPageChange={setPage} />}
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-xl font-serif">Stock Totals by Category</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full" data-testid="stock-totals-table">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Category</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold uppercase">Quantity</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold uppercase">Weight (g)</th>
                  </tr>
                </thead>
                <tbody>
                  {Array.isArray(stockTotals) && stockTotals.map((item, idx) => (
                    <tr key={idx} className="border-t hover:bg-muted/30">
                      <td className="px-4 py-3 font-medium">{item.header_name}</td>
                      <td className="px-4 py-3 text-right font-mono">{item.total_qty}</td>
                      <td className="px-4 py-3 text-right font-mono">{item.total_weight.toFixed(3)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-xl font-serif">Recent Movements</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full" data-testid="movements-table">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Date</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Type</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Category</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase">Description</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold uppercase">Qty</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold uppercase">Weight (g)</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold uppercase">Purity</th>
                  </tr>
                </thead>
                <tbody>
                  {Array.isArray(movements) && movements.slice(0, 20).map((mov) => (
                    <tr key={mov.id} className="border-t hover:bg-muted/30">
                      <td className="px-4 py-3 text-sm">{new Date(mov.date).toLocaleDateString()}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          mov.movement_type.includes('IN') ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {mov.movement_type}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm">{mov.header_name}</td>
                      <td className="px-4 py-3 text-sm">{mov.description}</td>
                      <td className="px-4 py-3 text-right font-mono">{mov.qty_delta > 0 ? '+' : ''}{mov.qty_delta}</td>
                      <td className="px-4 py-3 text-right font-mono">{mov.weight_delta > 0 ? '+' : ''}{mov.weight_delta.toFixed(3)}</td>
                      <td className="px-4 py-3 text-right font-mono">{mov.purity}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { toast } from 'sonner';
import { 
  Download, FileSpreadsheet, TrendingUp, DollarSign, Package, 
  Filter, Eye, Search, Calendar, RefreshCw 
} from 'lucide-react';

export default function ReportsPageEnhanced() {
  const [loading, setLoading] = useState(false);
  const [financialSummary, setFinancialSummary] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Filter states
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [invoiceType, setInvoiceType] = useState('');
  const [paymentStatus, setPaymentStatus] = useState('');
  const [partyType, setPartyType] = useState('');
  const [movementType, setMovementType] = useState('');
  const [category, setCategory] = useState('');
  const [transactionType, setTransactionType] = useState('');
  
  // Data states
  const [inventoryData, setInventoryData] = useState(null);
  const [partiesData, setPartiesData] = useState(null);
  const [invoicesData, setInvoicesData] = useState(null);
  const [transactionsData, setTransactionsData] = useState(null);
  const [categories, setCategories] = useState([]);
  const [accounts, setAccounts] = useState([]);
  
  // Detail view states
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [selectedParty, setSelectedParty] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);

  useEffect(() => {
    loadFinancialSummary();
    loadCategories();
    loadAccounts();
  }, []);

  const loadFinancialSummary = async () => {
    try {
      const params = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      
      const response = await axios.get(`${API}/reports/financial-summary`, { params });
      setFinancialSummary(response.data);
    } catch (error) {
      console.error('Failed to load financial summary');
    }
  };

  const loadCategories = async () => {
    try {
      const response = await axios.get(`${API}/inventory/headers`);
      setCategories(response.data);
    } catch (error) {
      console.error('Failed to load categories');
    }
  };

  const loadAccounts = async () => {
    try {
      const response = await axios.get(`${API}/accounts`);
      setAccounts(response.data);
    } catch (error) {
      console.error('Failed to load accounts');
    }
  };

  const loadInventoryReport = async () => {
    try {
      setLoading(true);
      const params = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      if (movementType) params.movement_type = movementType;
      if (category) params.category = category;
      
      const response = await axios.get(`${API}/reports/inventory-view`, { params });
      setInventoryData(response.data);
    } catch (error) {
      toast.error('Failed to load inventory report');
    } finally {
      setLoading(false);
    }
  };

  const loadPartiesReport = async () => {
    try {
      setLoading(true);
      const params = {};
      if (partyType) params.party_type = partyType;
      
      const response = await axios.get(`${API}/reports/parties-view`, { params });
      setPartiesData(response.data);
    } catch (error) {
      toast.error('Failed to load parties report');
    } finally {
      setLoading(false);
    }
  };

  const loadInvoicesReport = async () => {
    try {
      setLoading(true);
      const params = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      if (invoiceType) params.invoice_type = invoiceType;
      if (paymentStatus) params.payment_status = paymentStatus;
      
      const response = await axios.get(`${API}/reports/invoices-view`, { params });
      setInvoicesData(response.data);
    } catch (error) {
      toast.error('Failed to load invoices report');
    } finally {
      setLoading(false);
    }
  };

  const loadTransactionsReport = async () => {
    try {
      setLoading(true);
      const params = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      if (transactionType) params.transaction_type = transactionType;
      
      const response = await axios.get(`${API}/reports/transactions-view`, { params });
      setTransactionsData(response.data);
    } catch (error) {
      toast.error('Failed to load transactions report');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (type) => {
    try {
      setLoading(true);
      const params = {};
      
      // Add common filters
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      
      // Add type-specific filters
      if (type === 'inventory') {
        if (movementType) params.movement_type = movementType;
        if (category) params.category = category;
      } else if (type === 'invoices') {
        if (invoiceType) params.invoice_type = invoiceType;
        if (paymentStatus) params.payment_status = paymentStatus;
      } else if (type === 'parties') {
        if (partyType) params.party_type = partyType;
      }

      const endpoints = {
        inventory: '/reports/inventory-export',
        parties: '/reports/parties-export',
        invoices: '/reports/invoices-export'
      };

      const response = await axios.get(`${API}${endpoints[type]}`, {
        params,
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${type}_export_${new Date().toISOString().split('T')[0]}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success(`${type.charAt(0).toUpperCase() + type.slice(1)} exported successfully`);
    } catch (error) {
      toast.error('Failed to export data');
    } finally {
      setLoading(false);
    }
  };

  const viewInvoiceDetail = async (invoiceId) => {
    try {
      const response = await axios.get(`${API}/reports/invoice/${invoiceId}`);
      setSelectedInvoice(response.data);
      setDetailDialogOpen(true);
    } catch (error) {
      toast.error('Failed to load invoice details');
    }
  };

  const viewPartyLedger = async (partyId) => {
    try {
      const params = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      
      const response = await axios.get(`${API}/reports/party/${partyId}/ledger-report`, { params });
      setSelectedParty(response.data);
      setDetailDialogOpen(true);
    } catch (error) {
      toast.error('Failed to load party ledger');
    }
  };

  const viewCategoryStock = async (headerId) => {
    try {
      const params = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      
      const response = await axios.get(`${API}/reports/inventory/${headerId}/stock-report`, { params });
      setSelectedCategory(response.data);
      setDetailDialogOpen(true);
    } catch (error) {
      toast.error('Failed to load stock report');
    }
  };

  const clearFilters = () => {
    setStartDate('');
    setEndDate('');
    setInvoiceType('');
    setPaymentStatus('');
    setPartyType('');
    setMovementType('');
    setCategory('');
    setTransactionType('');
  };

  const applyFilters = () => {
    loadFinancialSummary();
    if (activeTab === 'inventory') loadInventoryReport();
    if (activeTab === 'invoices') loadInvoicesReport();
    if (activeTab === 'parties') loadPartiesReport();
    if (activeTab === 'transactions') loadTransactionsReport();
  };

  return (
    <div data-testid="reports-page">
      <div className="mb-8">
        <h1 className="text-4xl font-serif font-semibold text-gray-900 mb-2">Reports & Analytics</h1>
        <p className="text-muted-foreground">Comprehensive reports with advanced filtering</p>
      </div>

      {/* Financial Summary Cards */}
      {financialSummary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Sales</CardTitle>
              <TrendingUp className="w-4 h-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{financialSummary.total_sales.toFixed(2)} OMR</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Purchases</CardTitle>
              <Package className="w-4 h-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{financialSummary.total_purchases.toFixed(2)} OMR</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Net Profit</CardTitle>
              <DollarSign className="w-4 h-4 text-purple-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{financialSummary.net_profit.toFixed(2)} OMR</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Outstanding</CardTitle>
              <TrendingUp className="w-4 h-4 text-orange-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{financialSummary.total_outstanding.toFixed(2)} OMR</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filter Section */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="w-5 h-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {/* Date Range */}
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

            {/* Type-specific filters based on active tab */}
            {activeTab === 'invoices' && (
              <>
                <div className="space-y-2">
                  <Label>Invoice Type</Label>
                  <Select value={invoiceType} onValueChange={setInvoiceType}>
                    <SelectTrigger>
                      <SelectValue placeholder="All Types" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">All Types</SelectItem>
                      <SelectItem value="sale">Sale</SelectItem>
                      <SelectItem value="purchase">Purchase</SelectItem>
                      <SelectItem value="service">Service</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Payment Status</Label>
                  <Select value={paymentStatus} onValueChange={setPaymentStatus}>
                    <SelectTrigger>
                      <SelectValue placeholder="All Status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">All Status</SelectItem>
                      <SelectItem value="paid">Paid</SelectItem>
                      <SelectItem value="unpaid">Unpaid</SelectItem>
                      <SelectItem value="partial">Partial</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </>
            )}

            {activeTab === 'parties' && (
              <div className="space-y-2">
                <Label>Party Type</Label>
                <Select value={partyType} onValueChange={setPartyType}>
                  <SelectTrigger>
                    <SelectValue placeholder="All Types" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All Types</SelectItem>
                    <SelectItem value="customer">Customer</SelectItem>
                    <SelectItem value="vendor">Vendor</SelectItem>
                    <SelectItem value="worker">Worker</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}

            {activeTab === 'inventory' && (
              <>
                <div className="space-y-2">
                  <Label>Movement Type</Label>
                  <Select value={movementType} onValueChange={setMovementType}>
                    <SelectTrigger>
                      <SelectValue placeholder="All Types" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">All Types</SelectItem>
                      <SelectItem value="in">In</SelectItem>
                      <SelectItem value="out">Out</SelectItem>
                      <SelectItem value="adjustment">Adjustment</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Category</Label>
                  <Select value={category} onValueChange={setCategory}>
                    <SelectTrigger>
                      <SelectValue placeholder="All Categories" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">All Categories</SelectItem>
                      {categories.map((cat) => (
                        <SelectItem key={cat.id} value={cat.name}>
                          {cat.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </>
            )}

            {activeTab === 'transactions' && (
              <div className="space-y-2">
                <Label>Transaction Type</Label>
                <Select value={transactionType} onValueChange={setTransactionType}>
                  <SelectTrigger>
                    <SelectValue placeholder="All Types" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All Types</SelectItem>
                    <SelectItem value="credit">Credit</SelectItem>
                    <SelectItem value="debit">Debit</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>

          <div className="flex gap-2 mt-4">
            <Button onClick={applyFilters} disabled={loading}>
              <Search className="w-4 h-4 mr-2" />
              Apply Filters
            </Button>
            <Button variant="outline" onClick={clearFilters}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Clear
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Tabbed Reports */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="inventory">Inventory</TabsTrigger>
          <TabsTrigger value="invoices">Invoices</TabsTrigger>
          <TabsTrigger value="parties">Parties</TabsTrigger>
          <TabsTrigger value="transactions">Transactions</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-xl font-serif flex items-center gap-2">
                  <Package className="w-5 h-5" />
                  Inventory Report
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">
                  Export all inventory movements and stock levels to Excel
                </p>
                <Button 
                  onClick={() => handleExport('inventory')} 
                  disabled={loading}
                  className="w-full"
                >
                  <Download className="w-4 h-4 mr-2" />
                  <FileSpreadsheet className="w-4 h-4 mr-2" />
                  Export Inventory
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-xl font-serif flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  Parties Report
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">
                  Export all customers and vendors with their details
                </p>
                <Button 
                  onClick={() => handleExport('parties')} 
                  disabled={loading}
                  className="w-full"
                >
                  <Download className="w-4 h-4 mr-2" />
                  <FileSpreadsheet className="w-4 h-4 mr-2" />
                  Export Parties
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-xl font-serif flex items-center gap-2">
                  <DollarSign className="w-5 h-5" />
                  Invoices Report
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">
                  Export all invoices with payment status and amounts
                </p>
                <Button 
                  onClick={() => handleExport('invoices')} 
                  disabled={loading}
                  className="w-full"
                >
                  <Download className="w-4 h-4 mr-2" />
                  <FileSpreadsheet className="w-4 h-4 mr-2" />
                  Export Invoices
                </Button>
              </CardContent>
            </Card>
          </div>

          <Card className="mt-6">
            <CardHeader>
              <CardTitle className="text-xl font-serif">Financial Summary</CardTitle>
            </CardHeader>
            <CardContent>
              {financialSummary ? (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Total Credit</p>
                    <p className="text-lg font-bold">{financialSummary.total_credit.toFixed(2)} OMR</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Total Debit</p>
                    <p className="text-lg font-bold">{financialSummary.total_debit.toFixed(2)} OMR</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Account Balance</p>
                    <p className="text-lg font-bold">{financialSummary.total_account_balance.toFixed(2)} OMR</p>
                  </div>
                </div>
              ) : (
                <p className="text-muted-foreground">Loading financial summary...</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Inventory Tab */}
        <TabsContent value="inventory">
          <Card className="mt-6">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Inventory Movements</CardTitle>
              <div className="flex gap-2">
                <Button onClick={loadInventoryReport} disabled={loading}>
                  <Eye className="w-4 h-4 mr-2" />
                  View Report
                </Button>
                <Button onClick={() => handleExport('inventory')} disabled={loading}>
                  <Download className="w-4 h-4 mr-2" />
                  Export
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {inventoryData ? (
                <>
                  <div className="grid grid-cols-3 gap-4 mb-4 p-4 bg-gray-50 rounded">
                    <div>
                      <p className="text-sm text-muted-foreground">Total In</p>
                      <p className="text-lg font-bold">{inventoryData.summary.total_in} pcs</p>
                      <p className="text-sm">{inventoryData.summary.total_weight_in.toFixed(2)}g</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Total Out</p>
                      <p className="text-lg font-bold">{inventoryData.summary.total_out} pcs</p>
                      <p className="text-sm">{inventoryData.summary.total_weight_out.toFixed(2)}g</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Net Stock</p>
                      <p className="text-lg font-bold">{inventoryData.summary.net_quantity} pcs</p>
                      <p className="text-sm">{inventoryData.summary.net_weight.toFixed(2)}g</p>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Date</TableHead>
                          <TableHead>Type</TableHead>
                          <TableHead>Category</TableHead>
                          <TableHead>Description</TableHead>
                          <TableHead>Qty</TableHead>
                          <TableHead>Weight (g)</TableHead>
                          <TableHead>Purity</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {inventoryData.movements.map((movement) => (
                          <TableRow key={movement.id}>
                            <TableCell>{new Date(movement.date).toLocaleDateString()}</TableCell>
                            <TableCell>{movement.movement_type}</TableCell>
                            <TableCell>{movement.header_name}</TableCell>
                            <TableCell>{movement.description}</TableCell>
                            <TableCell>{movement.qty_delta}</TableCell>
                            <TableCell>{movement.weight_delta}</TableCell>
                            <TableCell>{movement.purity}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                  <p className="text-sm text-muted-foreground mt-2">
                    Showing {inventoryData.count} movements
                  </p>
                </>
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  Click "View Report" to load inventory data
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Invoices Tab */}
        <TabsContent value="invoices">
          <Card className="mt-6">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Invoices Report</CardTitle>
              <div className="flex gap-2">
                <Button onClick={loadInvoicesReport} disabled={loading}>
                  <Eye className="w-4 h-4 mr-2" />
                  View Report
                </Button>
                <Button onClick={() => handleExport('invoices')} disabled={loading}>
                  <Download className="w-4 h-4 mr-2" />
                  Export
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {invoicesData ? (
                <>
                  <div className="grid grid-cols-3 gap-4 mb-4 p-4 bg-gray-50 rounded">
                    <div>
                      <p className="text-sm text-muted-foreground">Total Amount</p>
                      <p className="text-lg font-bold">{invoicesData.summary.total_amount.toFixed(2)} OMR</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Total Paid</p>
                      <p className="text-lg font-bold">{invoicesData.summary.total_paid.toFixed(2)} OMR</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Total Balance</p>
                      <p className="text-lg font-bold">{invoicesData.summary.total_balance.toFixed(2)} OMR</p>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Invoice #</TableHead>
                          <TableHead>Date</TableHead>
                          <TableHead>Customer</TableHead>
                          <TableHead>Type</TableHead>
                          <TableHead>Amount</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {invoicesData.invoices.map((invoice) => (
                          <TableRow key={invoice.id}>
                            <TableCell className="font-medium">{invoice.invoice_number}</TableCell>
                            <TableCell>{new Date(invoice.date).toLocaleDateString()}</TableCell>
                            <TableCell>{invoice.customer_name}</TableCell>
                            <TableCell className="capitalize">{invoice.invoice_type}</TableCell>
                            <TableCell>{invoice.grand_total.toFixed(2)} OMR</TableCell>
                            <TableCell>
                              <span className={`px-2 py-1 rounded text-xs ${
                                invoice.payment_status === 'paid' ? 'bg-green-100 text-green-800' :
                                invoice.payment_status === 'unpaid' ? 'bg-red-100 text-red-800' :
                                'bg-yellow-100 text-yellow-800'
                              }`}>
                                {invoice.payment_status}
                              </span>
                            </TableCell>
                            <TableCell>
                              <Button 
                                size="sm" 
                                variant="ghost"
                                onClick={() => viewInvoiceDetail(invoice.id)}
                              >
                                <Eye className="w-4 h-4" />
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                  <p className="text-sm text-muted-foreground mt-2">
                    Showing {invoicesData.count} invoices
                  </p>
                </>
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  Click "View Report" to load invoices data
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Parties Tab */}
        <TabsContent value="parties">
          <Card className="mt-6">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Parties Report</CardTitle>
              <div className="flex gap-2">
                <Button onClick={loadPartiesReport} disabled={loading}>
                  <Eye className="w-4 h-4 mr-2" />
                  View Report
                </Button>
                <Button onClick={() => handleExport('parties')} disabled={loading}>
                  <Download className="w-4 h-4 mr-2" />
                  Export
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {partiesData ? (
                <>
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Name</TableHead>
                          <TableHead>Phone</TableHead>
                          <TableHead>Type</TableHead>
                          <TableHead>Outstanding</TableHead>
                          <TableHead>Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {partiesData.parties.map((party) => (
                          <TableRow key={party.id}>
                            <TableCell className="font-medium">{party.name}</TableCell>
                            <TableCell>{party.phone}</TableCell>
                            <TableCell className="capitalize">{party.party_type}</TableCell>
                            <TableCell>{party.outstanding.toFixed(2)} OMR</TableCell>
                            <TableCell>
                              <Button 
                                size="sm" 
                                variant="ghost"
                                onClick={() => viewPartyLedger(party.id)}
                              >
                                <Eye className="w-4 h-4 mr-1" />
                                Ledger
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                  <p className="text-sm text-muted-foreground mt-2">
                    Showing {partiesData.count} parties
                  </p>
                </>
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  Click "View Report" to load parties data
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Transactions Tab */}
        <TabsContent value="transactions">
          <Card className="mt-6">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Financial Transactions</CardTitle>
              <Button onClick={loadTransactionsReport} disabled={loading}>
                <Eye className="w-4 h-4 mr-2" />
                View Report
              </Button>
            </CardHeader>
            <CardContent>
              {transactionsData ? (
                <>
                  <div className="grid grid-cols-3 gap-4 mb-4 p-4 bg-gray-50 rounded">
                    <div>
                      <p className="text-sm text-muted-foreground">Total Credit</p>
                      <p className="text-lg font-bold">{transactionsData.summary.total_credit.toFixed(2)} OMR</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Total Debit</p>
                      <p className="text-lg font-bold">{transactionsData.summary.total_debit.toFixed(2)} OMR</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Net Balance</p>
                      <p className="text-lg font-bold">{transactionsData.summary.net_balance.toFixed(2)} OMR</p>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Transaction #</TableHead>
                          <TableHead>Date</TableHead>
                          <TableHead>Type</TableHead>
                          <TableHead>Account</TableHead>
                          <TableHead>Party</TableHead>
                          <TableHead>Amount</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {transactionsData.transactions.map((txn) => (
                          <TableRow key={txn.id}>
                            <TableCell className="font-medium">{txn.transaction_number}</TableCell>
                            <TableCell>{new Date(txn.date).toLocaleDateString()}</TableCell>
                            <TableCell className="capitalize">
                              <span className={`px-2 py-1 rounded text-xs ${
                                txn.transaction_type === 'credit' ? 'bg-green-100 text-green-800' :
                                'bg-red-100 text-red-800'
                              }`}>
                                {txn.transaction_type}
                              </span>
                            </TableCell>
                            <TableCell>{txn.account_name}</TableCell>
                            <TableCell>{txn.party_name || '-'}</TableCell>
                            <TableCell>{txn.amount.toFixed(2)} OMR</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                  <p className="text-sm text-muted-foreground mt-2">
                    Showing {transactionsData.count} transactions
                  </p>
                </>
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  Click "View Report" to load transactions data
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Detail Dialog */}
      <Dialog open={detailDialogOpen} onOpenChange={setDetailDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {selectedInvoice && 'Invoice Details'}
              {selectedParty && 'Party Ledger'}
              {selectedCategory && 'Stock Report'}
            </DialogTitle>
          </DialogHeader>
          
          {/* Invoice Detail */}
          {selectedInvoice && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Invoice Number</p>
                  <p className="font-medium">{selectedInvoice.invoice.invoice_number}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Customer</p>
                  <p className="font-medium">{selectedInvoice.invoice.customer_name}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Grand Total</p>
                  <p className="font-medium">{selectedInvoice.invoice.grand_total.toFixed(2)} OMR</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Payment Status</p>
                  <p className="font-medium capitalize">{selectedInvoice.invoice.payment_status}</p>
                </div>
              </div>

              <div>
                <h3 className="font-semibold mb-2">Items</h3>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Description</TableHead>
                      <TableHead>Qty</TableHead>
                      <TableHead>Weight</TableHead>
                      <TableHead>Amount</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {selectedInvoice.invoice.items.map((item) => (
                      <TableRow key={item.id}>
                        <TableCell>{item.description}</TableCell>
                        <TableCell>{item.qty}</TableCell>
                        <TableCell>{item.weight}g</TableCell>
                        <TableCell>{item.line_total.toFixed(2)} OMR</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}

          {/* Party Ledger */}
          {selectedParty && (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4 p-4 bg-gray-50 rounded">
                <div>
                  <p className="text-sm text-muted-foreground">Total Invoiced</p>
                  <p className="font-bold">{selectedParty.summary.total_invoiced.toFixed(2)} OMR</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Paid</p>
                  <p className="font-bold">{selectedParty.summary.total_paid.toFixed(2)} OMR</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Outstanding</p>
                  <p className="font-bold">{selectedParty.summary.total_outstanding.toFixed(2)} OMR</p>
                </div>
              </div>

              <div>
                <h3 className="font-semibold mb-2">Invoices</h3>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Invoice #</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Balance</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {selectedParty.invoices.map((inv) => (
                      <TableRow key={inv.id}>
                        <TableCell>{inv.invoice_number}</TableCell>
                        <TableCell>{new Date(inv.date).toLocaleDateString()}</TableCell>
                        <TableCell>{inv.grand_total.toFixed(2)} OMR</TableCell>
                        <TableCell>{inv.balance_due.toFixed(2)} OMR</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              <div>
                <h3 className="font-semibold mb-2">Transactions</h3>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Transaction #</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Amount</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {selectedParty.transactions.map((txn) => (
                      <TableRow key={txn.id}>
                        <TableCell>{txn.transaction_number}</TableCell>
                        <TableCell>{new Date(txn.date).toLocaleDateString()}</TableCell>
                        <TableCell className="capitalize">{txn.transaction_type}</TableCell>
                        <TableCell>{txn.amount.toFixed(2)} OMR</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}

          {/* Category Stock Report */}
          {selectedCategory && (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4 p-4 bg-gray-50 rounded">
                <div>
                  <p className="text-sm text-muted-foreground">Current Stock</p>
                  <p className="font-bold">{selectedCategory.summary.current_stock} pcs</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Current Weight</p>
                  <p className="font-bold">{selectedCategory.summary.current_weight.toFixed(2)}g</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Movements</p>
                  <p className="font-bold">{selectedCategory.count}</p>
                </div>
              </div>

              <div>
                <h3 className="font-semibold mb-2">Recent Movements</h3>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Qty</TableHead>
                      <TableHead>Weight</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {selectedCategory.movements.slice(0, 10).map((mov) => (
                      <TableRow key={mov.id}>
                        <TableCell>{new Date(mov.date).toLocaleDateString()}</TableCell>
                        <TableCell>{mov.movement_type}</TableCell>
                        <TableCell>{mov.description}</TableCell>
                        <TableCell>{mov.qty_delta}</TableCell>
                        <TableCell>{mov.weight_delta}g</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

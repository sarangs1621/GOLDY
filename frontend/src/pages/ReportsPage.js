import React, { useState, useEffect } from 'react';
import { formatWeight, formatCurrency, safeToFixed } from '../utils/numberFormat';
import { API } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';
import { Download, FileSpreadsheet, TrendingUp, DollarSign, Package } from 'lucide-react';

export default function ReportsPage() {
  const [loading, setLoading] = useState(false);
  const [financialSummary, setFinancialSummary] = useState(null);

  useEffect(() => {
    loadFinancialSummary();
  }, []);

  const loadFinancialSummary = async () => {
    try {
      const response = await API.get('/api/reports/financial-summary');
      setFinancialSummary(response.data);
    } catch (error) {
      console.error('Failed to load financial summary');
    }
  };

  const handleExport = async (type) => {
    try {
      setLoading(true);
      const endpoints = {
        inventory: '/api/reports/inventory-export',
        parties: '/api/reports/parties-export',
        invoices: '/api/reports/invoices-export'
      };

      const response = await API.get(endpoints[type], {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${type}_export.xlsx`);
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

  return (
    <div data-testid="reports-page">
      <div className="mb-8">
        <h1 className="text-4xl font-serif font-semibold text-gray-900 mb-2">Reports</h1>
        <p className="text-muted-foreground">Financial reports and data exports</p>
      </div>

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

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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
    </div>
  );
}

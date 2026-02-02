import React, { useState, useEffect } from 'react';
import { API } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Package, AlertTriangle, Users, TrendingUp } from 'lucide-react';
import { formatWeight, formatCurrency } from '../utils/numberFormat';
import Pagination from '../components/Pagination';

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalHeaders: 0,
    totalStock: 0,
    totalOutstanding: 0,
    lowStockItems: 0
  });
  const [stockTotals, setStockTotals] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [pagination, setPagination] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, [currentPage, pageSize]);

  const loadDashboardData = async () => {
    try {
      const [headersRes, stockRes, outstandingRes] = await Promise.all([
        API.get(`/api/inventory/headers?page_size=1000`),
        API.get(`/api/inventory/stock-totals?page=${currentPage}&page_size=${pageSize}`),
        API.get(`/api/parties/outstanding-summary`)
      ]);

      // For stats, we need all stock data to calculate totals
      const allStockRes = await API.get(`/api/inventory/stock-totals?page=1&page_size=1000`);
      const allStockData = allStockRes.data?.items || [];

      setStats({
        totalHeaders: headersRes.data?.pagination?.total_count || 0,
        totalStock: allStockData.reduce((sum, item) => sum + (item.total_weight || 0), 0) || 0,
        totalOutstanding: outstandingRes.data?.total_customer_due || 0,
        lowStockItems: allStockData.filter(item => item.total_qty < 5).length || 0
      });

      setStockTotals(stockRes.data?.items || []);
      setPagination(stockRes.data?.pagination || null);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
      // Set safe default values on error
      setStats({
        totalHeaders: 0,
        totalStock: 0,
        totalOutstanding: 0,
        lowStockItems: 0
      });
      setStockTotals([]);
      setPagination(null);
    }
  };

  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
  };

  return (
    <div data-testid="dashboard-page">
      <div className="mb-8">
        <h1 className="text-4xl font-serif font-semibold text-gray-900 mb-2">Dashboard</h1>
        <p className="text-muted-foreground">Overview of your gold shop operations</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card className="border-l-4 border-l-primary">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Categories</CardTitle>
            <Package className="w-5 h-5 text-primary" strokeWidth={1.5} />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-mono font-semibold text-gray-900">{stats.totalHeaders}</div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-accent">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Total Stock</CardTitle>
            <TrendingUp className="w-5 h-5 text-accent" strokeWidth={1.5} />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-mono font-semibold text-gray-900">{formatWeight(stats.totalStock)}<span className="text-sm ml-1">g</span></div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-destructive">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Outstanding</CardTitle>
            <Users className="w-5 h-5 text-destructive" strokeWidth={1.5} />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-mono font-semibold text-gray-900">{formatCurrency(stats.totalOutstanding)}<span className="text-sm ml-1">OMR</span></div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-orange-500">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Low Stock</CardTitle>
            <AlertTriangle className="w-5 h-5 text-orange-500" strokeWidth={1.5} />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-mono font-semibold text-gray-900">{stats.lowStockItems}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-xl font-serif">Stock Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full" data-testid="stock-summary-table">
              <thead className="bg-muted/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">Category</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-muted-foreground uppercase tracking-wider">Quantity</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-muted-foreground uppercase tracking-wider">Weight (g)</th>
                </tr>
              </thead>
              <tbody>
                {stockTotals.map((item, idx) => (
                  <tr key={idx} className="border-t hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3 font-medium">{item.header_name}</td>
                    <td className="px-4 py-3 text-right font-mono">{item.total_qty}</td>
                    <td className="px-4 py-3 text-right font-mono">{formatWeight(item.total_weight || 0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {pagination && (
            <Pagination 
              pagination={pagination} 
              onPageChange={handlePageChange} 
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

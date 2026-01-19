import '@/App.css';
import '@/index.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { DashboardLayout } from './components/DashboardLayout';
import { Toaster } from './components/ui/sonner';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';
import InventoryPage from './pages/InventoryPage';
import JobCardsPage from './pages/JobCardsPage';
import InvoicesPage from './pages/InvoicesPage';
import PartiesPage from './pages/PartiesPage';
import FinancePage from './pages/FinancePage';
import DailyClosingPage from './pages/DailyClosingPage';
import ReportsPage from './pages/ReportsPageEnhanced';
import AuditLogsPage from './pages/AuditLogsPage';
import SettingsPage from './pages/SettingsPage';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardLayout>
                  <Dashboard />
                </DashboardLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/inventory"
            element={
              <ProtectedRoute>
                <DashboardLayout>
                  <InventoryPage />
                </DashboardLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/jobcards"
            element={
              <ProtectedRoute>
                <DashboardLayout>
                  <JobCardsPage />
                </DashboardLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/invoices"
            element={
              <ProtectedRoute>
                <DashboardLayout>
                  <InvoicesPage />
                </DashboardLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/parties"
            element={
              <ProtectedRoute>
                <DashboardLayout>
                  <PartiesPage />
                </DashboardLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/finance"
            element={
              <ProtectedRoute>
                <DashboardLayout>
                  <FinancePage />
                </DashboardLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/daily-closing"
            element={
              <ProtectedRoute>
                <DashboardLayout>
                  <DailyClosingPage />
                </DashboardLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/reports"
            element={
              <ProtectedRoute>
                <DashboardLayout>
                  <ReportsPage />
                </DashboardLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/audit-logs"
            element={
              <ProtectedRoute>
                <DashboardLayout>
                  <AuditLogsPage />
                </DashboardLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <DashboardLayout>
                  <SettingsPage />
                </DashboardLayout>
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </AuthProvider>
  );
}

export default App;

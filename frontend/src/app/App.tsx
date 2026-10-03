import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'

import { AppShell } from '../components/AppShell'
import { ErrorBoundary } from '../components/ErrorBoundary'

const DashboardPage = lazy(() =>
  import('../pages/DashboardPage').then((m) => ({ default: m.DashboardPage })),
)
const OrdersPage = lazy(() =>
  import('../pages/OrdersPage').then((m) => ({ default: m.OrdersPage })),
)
const OrderDetailPage = lazy(() =>
  import('../pages/OrderDetailPage').then((m) => ({ default: m.OrderDetailPage })),
)
const InventoryPage = lazy(() =>
  import('../pages/InventoryPage').then((m) => ({ default: m.InventoryPage })),
)
const AlertsPage = lazy(() =>
  import('../pages/AlertsPage').then((m) => ({ default: m.AlertsPage })),
)
const ReconciliationPage = lazy(() =>
  import('../pages/ReconciliationPage').then((m) => ({ default: m.ReconciliationPage })),
)
const ReconciliationDetailPage = lazy(() =>
  import('../pages/ReconciliationDetailPage').then((m) => ({ default: m.ReconciliationDetailPage })),
)
const ExceptionsPage = lazy(() =>
  import('../pages/ExceptionsPage').then((m) => ({ default: m.ExceptionsPage })),
)
const IntegrationsPage = lazy(() =>
  import('../pages/IntegrationsPage').then((m) => ({ default: m.IntegrationsPage })),
)
const AutomationPage = lazy(() =>
  import('../pages/AutomationPage').then((m) => ({ default: m.AutomationPage })),
)

function PageLoadingFallback() {
  return (
    <div className="p-6 max-w-[1440px] w-full space-y-4 animate-pulse">
      <div className="h-8 w-48 bg-gray-200 rounded-md" />
      <div className="h-4 w-80 bg-gray-100 rounded-md mb-6" />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="h-24 bg-gray-100 rounded-[10px]" />
        <div className="h-24 bg-gray-100 rounded-[10px]" />
        <div className="h-24 bg-gray-100 rounded-[10px]" />
        <div className="h-24 bg-gray-100 rounded-[10px]" />
      </div>
      <div className="h-64 bg-gray-100 rounded-xl" />
    </div>
  )
}

export function App() {
  return (
    <AppShell>
      <ErrorBoundary>
        <Suspense fallback={<PageLoadingFallback />}>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/orders" element={<OrdersPage />} />
            <Route path="/orders/:orderId" element={<OrderDetailPage />} />
            <Route path="/inventory" element={<InventoryPage />} />
            <Route path="/alerts" element={<AlertsPage />} />
            <Route path="/reconciliation" element={<ReconciliationPage />} />
            <Route path="/reconciliation/:id" element={<ReconciliationDetailPage />} />
            <Route path="/exceptions" element={<ExceptionsPage />} />
            <Route path="/integrations" element={<IntegrationsPage />} />
            <Route path="/automation" element={<AutomationPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </ErrorBoundary>
    </AppShell>
  )
}

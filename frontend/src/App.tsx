// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'sonner';
import { ErrorBoundary } from './components/ui/error-boundary';
import { queryClient } from './lib/api/queryClient';
import { useAuthStore } from './lib/stores/authStore';
import { AppLayout } from './components/layout/AppLayout';
import Dashboard from './routes/Dashboard';
import AssetInventory from './routes/AssetInventory';
import DEXDashboard from './routes/DEXDashboard';
import ComplianceDashboard from './routes/ComplianceDashboard';
import CABPortal from './routes/CABPortal';
import DeploymentWizard from './routes/DeploymentWizard';
import DeploymentsSidebar from './routes/deployments/DeploymentsSidebar';
import AuditTrail from './routes/AuditTrail';
import EvidenceViewer from './routes/EvidenceViewer';
import Settings from './routes/settings';
import AIAgentHub from './routes/AIAgentHub';
import WorkflowPage from './routes/ai/WorkflowPage';
import AdminDemoData from './routes/AdminDemoData';
import PolicyDocuments from './routes/admin/PolicyDocuments';
import Notifications from './routes/Notifications';
import Login from './routes/Login';
import { LicenseDashboard } from './routes/licenses';
import {
  PortfolioManagerDashboard,
  ApplicationManagerPerformance,
  TrueUpForecasts,
  PackagingRequests,
} from './routes/portfolio';
import CMDBDashboard from './routes/cmdb/CMDBDashboard';
import CommunicationsDashboard from './routes/communications/CommunicationsDashboard';
import DiscoveryDashboard from './routes/discovery/DiscoveryDashboard';
import DocumentationDashboard from './routes/documentation/DocumentationDashboard';
import AdvisorDashboard from './routes/automation-advisor/AdvisorDashboard';
import IAMSecurityDashboard from './routes/iam-security/IAMSecurityDashboard';
import RequestCoordinationDashboard from './routes/request-coordination/RequestCoordinationDashboard';
import SecOpsDashboard from './routes/secops/SecOpsDashboard';
import SREDashboard from './routes/sre/SREDashboard';
import KBTriageDashboard from './routes/kb-triage/KBTriageDashboard';
import SLAGovernanceDashboard from './routes/sla-governance/SLAGovernanceDashboard';
import PlanningDashboard from './routes/planning/PlanningDashboard';

function App() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const checkSession = useAuthStore((state) => state.checkSession);

  // Check session on mount and periodically
  React.useEffect(() => {
    // Check immediately
    checkSession();

    // Check every 5 minutes
    const interval = setInterval(() => {
      checkSession();
    }, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, [checkSession]);

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        {/* Skip to content link for accessibility */}
        <a href="#main-content" className="skip-to-content">
          Skip to main content
        </a>
        <Toaster
          position="top-right"
          richColors
          theme="dark"
          closeButton
          toastOptions={{
            duration: 5000,
            style: {
              background: 'hsl(var(--card))',
              border: '1px solid hsl(var(--border))',
            },
          }}
        />
        <Routes>
          <Route path="/login" element={<Login />} />

          {/* Protected routes wrapped in AppLayout */}
          <Route element={isAuthenticated ? <AppLayout /> : <Navigate to="/login" />}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/dex" element={<DEXDashboard />} />
            <Route path="/assets" element={<AssetInventory />} />
            <Route path="/compliance" element={<ComplianceDashboard />} />
            <Route path="/cab" element={<CABPortal />} />
            <Route path="/deploy" element={<DeploymentWizard />} />
            <Route path="/deployments/stack" element={<DeploymentsSidebar />} />
            <Route path="/audit" element={<AuditTrail />} />
            <Route path="/evidence/:id" element={<EvidenceViewer />} />
            <Route path="/ai-agents" element={<AIAgentHub />} />
            <Route path="/ai/workflows/:executionId" element={<WorkflowPage />} />
            <Route path="/licenses" element={<LicenseDashboard />} />
            <Route path="/portfolios" element={<PortfolioManagerDashboard />} />
            <Route path="/performance" element={<ApplicationManagerPerformance />} />
            <Route path="/forecasts" element={<TrueUpForecasts />} />
            <Route path="/packaging-requests" element={<PackagingRequests />} />
            <Route path="/notifications" element={<Notifications />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/admin/demo-data" element={<AdminDemoData />} />
            <Route path="/admin/policy-documents" element={<PolicyDocuments />} />
            {/* ALM Agent Dashboards */}
            <Route path="/cmdb" element={<CMDBDashboard />} />
            <Route path="/communications" element={<CommunicationsDashboard />} />
            <Route path="/discovery" element={<DiscoveryDashboard />} />
            <Route path="/documentation" element={<DocumentationDashboard />} />
            <Route path="/automation-advisor" element={<AdvisorDashboard />} />
            <Route path="/iam-security" element={<IAMSecurityDashboard />} />
            <Route path="/request-coordination" element={<RequestCoordinationDashboard />} />
            <Route path="/secops" element={<SecOpsDashboard />} />
            <Route path="/sre" element={<SREDashboard />} />
            <Route path="/kb-triage" element={<KBTriageDashboard />} />
            <Route path="/sla-governance" element={<SLAGovernanceDashboard />} />
            <Route path="/planning" element={<PlanningDashboard />} />
          </Route>
        </Routes>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;

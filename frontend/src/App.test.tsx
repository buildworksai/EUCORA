// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@/test/utils';
import App from './App';

vi.mock('./components/layout/AppLayout', () => ({
  AppLayout: () => <div>Layout</div>,
}));
vi.mock('./routes/Dashboard', () => ({ default: () => <div>Dashboard Page</div> }));
vi.mock('./routes/Login', () => ({ default: () => <div>Login Page</div> }));
vi.mock('./routes/AssetInventory', () => ({ default: () => <div>Asset Inventory</div> }));
vi.mock('./routes/DEXDashboard', () => ({ default: () => <div>DEX</div> }));
vi.mock('./routes/ComplianceDashboard', () => ({ default: () => <div>Compliance</div> }));
vi.mock('./routes/CABPortal', () => ({ default: () => <div>CAB</div> }));
vi.mock('./routes/DeploymentWizard', () => ({ default: () => <div>Deploy</div> }));
vi.mock('./routes/AuditTrail', () => ({ default: () => <div>Audit</div> }));
vi.mock('./routes/EvidenceViewer', () => ({ default: () => <div>Evidence</div> }));
vi.mock('./routes/AIAgentHub', () => ({ default: () => <div>AI</div> }));
vi.mock('./routes/AdminDemoData', () => ({ default: () => <div>Admin Demo</div> }));
vi.mock('./routes/settings', () => ({ default: () => <div>Settings</div> }));

const authState = { isAuthenticated: false };

vi.mock('./lib/stores/authStore', () => ({
  useAuthStore: (selector: any) => (selector ? selector(authState) : authState),
}));

describe('App', () => {
  beforeEach(() => {
    authState.isAuthenticated = false;
  });

  it('redirects unauthenticated users to login', () => {
    window.history.pushState({}, '', '/dashboard');
    render(<App />);

    expect(screen.getByText('Login Page')).toBeInTheDocument();
  });

  it('renders dashboard when authenticated', () => {
    authState.isAuthenticated = true;
    window.history.pushState({}, '', '/dashboard');
    render(<App />);

    expect(screen.getByText('Layout')).toBeInTheDocument();
  });
});

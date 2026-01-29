// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/utils';
import Dashboard from './Dashboard';
import CABPortal from './CABPortal';
import AuditTrail from './AuditTrail';
import EvidenceViewer from './EvidenceViewer';
import DeploymentWizard from './DeploymentWizard';
import AdminDemoData from './AdminDemoData';
import AIAgentHub from './AIAgentHub';
import ComplianceDashboard from './ComplianceDashboard';
import Login from './Login';

const navigateMock = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => navigateMock,
    useParams: () => ({ id: 'e1' }),
  };
});

vi.mock('recharts', () => {
  const ChartStub = ({ children }: { children?: React.ReactNode }) => <div>{children}</div>;
  const EmptyStub = () => <div />;
  return {
    AreaChart: ChartStub,
    Area: ChartStub,
    BarChart: ChartStub,
    Bar: ChartStub,
    XAxis: EmptyStub,
    YAxis: EmptyStub,
    Tooltip: EmptyStub,
    ResponsiveContainer: ChartStub,
    PieChart: ChartStub,
    Pie: ChartStub,
    Cell: EmptyStub,
    Legend: EmptyStub,
  };
});

vi.mock('@/lib/stores/authStore', () => ({
  useAuthStore: () => ({
    user: { role: 'admin', is_staff: true, is_superuser: true },
    login: vi.fn().mockResolvedValue(true),
    isAuthenticated: false,
    isLoading: false,
    error: null,
    clearError: vi.fn(),
  }),
}));

vi.mock('@/lib/api/hooks/useDeployments', () => ({
  useDeployments: () => ({ data: [], isLoading: false, error: null }),
  useCreateDeployment: () => ({ mutateAsync: vi.fn().mockResolvedValue({ correlation_id: 'c1' }), isPending: false }),
}));

vi.mock('@/lib/api/hooks/useCAB', () => ({
  usePendingApprovals: () => ({ data: [], isLoading: false }),
  useApproveDeployment: () => ({ mutate: vi.fn(), isPending: false }),
  useRejectDeployment: () => ({ mutate: vi.fn(), isPending: false }),
}));

vi.mock('@/lib/api/hooks/useHealth', () => ({
  useHealth: () => ({ data: { status: 'ok' } }),
}));

vi.mock('@/lib/api/hooks/useEvents', () => ({
  useEvents: () => ({ data: [], isLoading: false, error: null }),
}));

vi.mock('@/lib/api/hooks/useEvidence', () => ({
  useEvidencePack: () => ({
    data: {
      correlation_id: 'e1',
      app_name: 'App',
      version: '1.0',
      artifact_hash: 'hash',
      sbom_data: {},
      vulnerability_scan_results: {},
      is_validated: true,
      created_at: '',
    },
    isLoading: false,
    error: null,
  }),
}));

vi.mock('@/lib/api/hooks/useDemoData', () => ({
  useDemoDataStats: () => ({
    data: {
      counts: {
        assets: 10,
        applications: 5,
        deployments: 3,
        ring_deployments: 2,
        cab_approvals: 4,
        evidence_packs: 6,
        events: 9,
        users: 1,
      },
      last_seeded: null,
    },
    isLoading: false,
  }),
  useDemoMode: () => ({ data: { demo_mode: true } }),
  useSeedDemoData: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useClearDemoData: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useSetDemoMode: () => ({ mutateAsync: vi.fn(), isPending: false }),
}));

vi.mock('@/lib/api/hooks/useAI', () => ({
  useAIAgentStats: () => ({
    data: {
      active_tasks: 0,
      awaiting_approval: 0,
      completed_today: 0,
      tokens_used: 0,
    },
    isLoading: false,
  }),
  useAIAgentTasks: () => ({ data: { tasks: [] }, isLoading: false }),
}));

describe('routes', () => {
  it('renders Dashboard', () => {
    render(<Dashboard />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  it('renders CAB Portal', () => {
    render(<CABPortal />);
    expect(screen.getByText('CAB Portal')).toBeInTheDocument();
  });

  it('renders Audit Trail', () => {
    render(<AuditTrail />);
    expect(screen.getByText('Audit Trail')).toBeInTheDocument();
  });

  it('renders Evidence Viewer', () => {
    render(<EvidenceViewer />);
    expect(screen.getByText('Evidence Pack')).toBeInTheDocument();
  });

  it('renders Deployment Wizard', () => {
    render(<DeploymentWizard />);
    expect(screen.getByText('New Deployment')).toBeInTheDocument();
  });

  it('renders Admin Demo Data', () => {
    render(<AdminDemoData />);
    expect(screen.getByText('Demo Data Administration')).toBeInTheDocument();
  });

  it('renders AI Agent Hub', () => {
    render(<AIAgentHub />);
    expect(screen.getByText('AI Agent Hub')).toBeInTheDocument();
  });

  it('renders Compliance Dashboard', () => {
    render(<ComplianceDashboard />);
    expect(screen.getByText('Compliance & Security')).toBeInTheDocument();
  });

  it('renders Login page', () => {
    render(<Login />);
    expect(screen.getByText('Welcome Back')).toBeInTheDocument();
  });
});

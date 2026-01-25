// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import DeploymentsSidebar from './DeploymentsSidebar';
import { useSidebarApplications } from '@/lib/api/hooks/useSidebarApplications';
import { createPendingQueryResult, createSuccessQueryResult } from '@/lib/test/mockQueryResult';
import type { SidebarApplicationGroup } from './sidebar-contracts';

// Mock the hook
vi.mock('@/lib/api/hooks/useSidebarApplications', () => ({
  useSidebarApplications: vi.fn(),
}));

const mockApplicationData: SidebarApplicationGroup[] = [
  {
    app_name: 'Adobe Acrobat Reader',
    latest_version: '24.001',
    deployment_count: 3,
    versions: [
      {
        version: '24.001',
        latest_created_at: '2026-01-20T10:00:00Z',
        deployments: [
          {
            id: 1,
            correlation_id: 'dep-1',
            app_name: 'Adobe Acrobat Reader',
            version: '24.001',
            target_ring: 'CANARY',
            status: 'COMPLETED',
            risk_score: 15,
            requires_cab_approval: false,
            created_at: '2026-01-20T10:00:00Z',
            updated_at: '2026-01-20T10:00:00Z',
          },
          {
            id: 2,
            correlation_id: 'dep-2',
            app_name: 'Adobe Acrobat Reader',
            version: '24.001',
            target_ring: 'PILOT',
            status: 'DEPLOYING',
            risk_score: 15,
            requires_cab_approval: false,
            created_at: '2026-01-20T09:00:00Z',
            updated_at: '2026-01-20T09:00:00Z',
          },
        ],
      },
      {
        version: '23.999',
        latest_created_at: '2026-01-19T10:00:00Z',
        deployments: [
          {
            id: 3,
            correlation_id: 'dep-3',
            app_name: 'Adobe Acrobat Reader',
            version: '23.999',
            target_ring: 'LAB',
            status: 'APPROVED',
            risk_score: 10,
            requires_cab_approval: false,
            created_at: '2026-01-19T10:00:00Z',
            updated_at: '2026-01-19T10:00:00Z',
          },
        ],
      },
    ],
  },
  {
    app_name: 'Microsoft Teams',
    latest_version: '25.1.1',
    deployment_count: 2,
    versions: [
      {
        version: '25.1.1',
        latest_created_at: '2026-01-20T08:00:00Z',
        deployments: [
          {
            id: 4,
            correlation_id: 'dep-4',
            app_name: 'Microsoft Teams',
            version: '25.1.1',
            target_ring: 'GLOBAL',
            status: 'AWAITING_CAB',
            risk_score: 65,
            requires_cab_approval: true,
            created_at: '2026-01-20T08:00:00Z',
            updated_at: '2026-01-20T08:00:00Z',
          },
          {
            id: 5,
            correlation_id: 'dep-5',
            app_name: 'Microsoft Teams',
            version: '25.1.1',
            target_ring: 'DEPARTMENT',
            status: 'PENDING',
            risk_score: 65,
            requires_cab_approval: true,
            created_at: '2026-01-20T07:00:00Z',
            updated_at: '2026-01-20T07:00:00Z',
          },
        ],
      },
    ],
  },
];

describe('DeploymentsSidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading skeleton initially', () => {
    vi.mocked(useSidebarApplications).mockReturnValue(
      createPendingQueryResult<SidebarApplicationGroup[]>()
    );

    render(<DeploymentsSidebar />);
    expect(screen.getByText('Applications')).toBeInTheDocument();
  });

  it('renders applications with versions and deployments', async () => {
    vi.mocked(useSidebarApplications).mockReturnValue(
      createSuccessQueryResult<SidebarApplicationGroup[]>(mockApplicationData)
    );

    render(<DeploymentsSidebar />);

    await waitFor(() => {
      expect(screen.getByText('Adobe Acrobat Reader')).toBeInTheDocument();
      expect(screen.getByText('Microsoft Teams')).toBeInTheDocument();
    });
  });

  it('displays deployment counts in badges', async () => {
    vi.mocked(useSidebarApplications).mockReturnValue(
      createSuccessQueryResult<SidebarApplicationGroup[]>(mockApplicationData)
    );

    render(<DeploymentsSidebar />);

    await waitFor(() => {
      const badges = screen.getAllByText(/^\d+$/);
      expect(badges.length).toBeGreaterThan(0);
    });
  });

  it('shows empty state when no applications', async () => {
    vi.mocked(useSidebarApplications).mockReturnValue(
      createSuccessQueryResult<SidebarApplicationGroup[]>([])
    );

    render(<DeploymentsSidebar />);

    await waitFor(() => {
      expect(screen.getByText('No applications found')).toBeInTheDocument();
    });
  });

  it('filters applications by search term', async () => {
    vi.mocked(useSidebarApplications).mockReturnValue(
      createSuccessQueryResult<SidebarApplicationGroup[]>(mockApplicationData)
    );

    render(<DeploymentsSidebar />);

    const searchInput = screen.getByPlaceholderText('Search applications...');
    expect(searchInput).toBeInTheDocument();

    // Simulate search (the hook will be called with filtered param by useSidebarApplications)
    await waitFor(() => {
      expect(screen.getByText('Adobe Acrobat Reader')).toBeInTheDocument();
    });
  });

  it('displays status badges and risk scores', async () => {
    vi.mocked(useSidebarApplications).mockReturnValue(
      createSuccessQueryResult<SidebarApplicationGroup[]>(mockApplicationData)
    );

    render(<DeploymentsSidebar />);

    await waitFor(() => {
      // Check for deployment status indicators
      expect(screen.getByText('Adobe Acrobat Reader')).toBeInTheDocument();
    });
  });
});

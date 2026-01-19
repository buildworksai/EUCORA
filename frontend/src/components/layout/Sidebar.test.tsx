// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@/test/utils';
import { Sidebar } from './Sidebar';
import { useAuthStore } from '@/lib/stores/authStore';
import { useUIStore } from '@/lib/stores/uiStore';

// Mock stores
vi.mock('@/lib/stores/authStore', () => ({
  useAuthStore: vi.fn(),
}));

vi.mock('@/lib/stores/uiStore', () => ({
  useUIStore: vi.fn(),
}));

describe('Sidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders navigation items', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { role: 'admin' },
    } as ReturnType<typeof useAuthStore>);
    vi.mocked(useUIStore).mockReturnValue({
      sidebarOpen: true,
    } as ReturnType<typeof useUIStore>);

    render(<Sidebar />);
    
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('DEX & Green IT')).toBeInTheDocument();
    expect(screen.getByText('Asset Inventory')).toBeInTheDocument();
  });

  it('filters nav items based on user permissions', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: { role: 'viewer', permissions: ['dashboard:read'] },
    } as ReturnType<typeof useAuthStore>);
    vi.mocked(useUIStore).mockReturnValue({
      sidebarOpen: true,
    } as ReturnType<typeof useUIStore>);

    render(<Sidebar />);
    
    // Should show Dashboard (has permission)
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });
});


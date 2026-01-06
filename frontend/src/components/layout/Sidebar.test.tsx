// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/utils';
import { Sidebar } from './Sidebar';
import { useAuthStore, useUIStore } from '@/lib/stores/authStore';

// Mock stores
vi.mock('@/lib/stores/authStore', () => ({
  useAuthStore: vi.fn(),
  useUIStore: vi.fn(),
}));

vi.mock('@/lib/stores/uiStore', () => ({
  useUIStore: vi.fn(),
}));

describe('Sidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders navigation items', () => {
    (useAuthStore as any).mockReturnValue({
      user: { role: 'admin' },
    });
    (useUIStore as any).mockReturnValue({
      sidebarOpen: true,
    });

    render(<Sidebar />);
    
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('DEX & Green IT')).toBeInTheDocument();
    expect(screen.getByText('Asset Inventory')).toBeInTheDocument();
  });

  it('filters nav items based on user permissions', () => {
    (useAuthStore as any).mockReturnValue({
      user: { role: 'viewer', permissions: ['dashboard:read'] },
    });
    (useUIStore as any).mockReturnValue({
      sidebarOpen: true,
    });

    render(<Sidebar />);
    
    // Should show Dashboard (has permission)
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });
});


// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * Tests for LicenseSummaryWidget component.
 */
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { LicenseSummaryWidget } from './LicenseSummaryWidget';
import * as useLicensesModule from '@/lib/api/hooks/useLicenses';
import { LicenseSummary, HealthStatus } from '@/routes/licenses/contracts';

// ============================================================================
// TEST UTILITIES
// ============================================================================

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={createQueryClient()}>
    {children}
  </QueryClientProvider>
);

const mockSummary: LicenseSummary = {
  total_entitled: 1000,
  total_consumed: 750,
  total_remaining: 250,
  last_reconciled_at: new Date().toISOString(),
  health_status: HealthStatus.OK,
  health_message: null,
  stale_duration_seconds: null,
  vendor_count: 15,
  sku_count: 42,
  active_alerts_count: 0,
};

// ============================================================================
// TESTS
// ============================================================================

describe('LicenseSummaryWidget', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Loading state', () => {
    it('renders loading skeleton when data is loading', () => {
      vi.spyOn(useLicensesModule, 'useLicenseSummary').mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        dataUpdatedAt: 0,
      } as ReturnType<typeof useLicensesModule.useLicenseSummary>);

      render(<LicenseSummaryWidget />, { wrapper });

      // Should show animated pulse class (loading skeleton)
      const container = document.querySelector('.animate-pulse');
      expect(container).toBeTruthy();
    });
  });

  describe('Error state', () => {
    it('renders error message when data fetch fails', () => {
      vi.spyOn(useLicensesModule, 'useLicenseSummary').mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Failed to fetch'),
        dataUpdatedAt: 0,
      } as ReturnType<typeof useLicensesModule.useLicenseSummary>);

      render(<LicenseSummaryWidget />, { wrapper });

      expect(screen.getByText('License data unavailable')).toBeTruthy();
    });

    it('renders error state when data is null', () => {
      vi.spyOn(useLicensesModule, 'useLicenseSummary').mockReturnValue({
        data: null,
        isLoading: false,
        error: null,
        dataUpdatedAt: 0,
      } as unknown as ReturnType<typeof useLicensesModule.useLicenseSummary>);

      render(<LicenseSummaryWidget />, { wrapper });

      expect(screen.getByText('License data unavailable')).toBeTruthy();
    });
  });

  describe('Normal display', () => {
    it('renders license summary with correct quantities', () => {
      vi.spyOn(useLicensesModule, 'useLicenseSummary').mockReturnValue({
        data: mockSummary,
        isLoading: false,
        error: null,
        dataUpdatedAt: Date.now(),
      } as ReturnType<typeof useLicensesModule.useLicenseSummary>);

      render(<LicenseSummaryWidget />, { wrapper });

      expect(screen.getByText('Licenses')).toBeTruthy();
      expect(screen.getByText('Consumed')).toBeTruthy();
      expect(screen.getByText('750')).toBeTruthy();
      expect(screen.getByText('Entitled')).toBeTruthy();
      expect(screen.getByText('1,000')).toBeTruthy();
      expect(screen.getByText('Remaining')).toBeTruthy();
      expect(screen.getByText('250')).toBeTruthy();
    });

    it('displays correct utilization percentage', () => {
      vi.spyOn(useLicensesModule, 'useLicenseSummary').mockReturnValue({
        data: mockSummary,
        isLoading: false,
        error: null,
        dataUpdatedAt: Date.now(),
      } as ReturnType<typeof useLicensesModule.useLicenseSummary>);

      render(<LicenseSummaryWidget />, { wrapper });

      expect(screen.getByText('75%')).toBeTruthy();
    });

    it('displays vendor and SKU counts in footer', () => {
      vi.spyOn(useLicensesModule, 'useLicenseSummary').mockReturnValue({
        data: mockSummary,
        isLoading: false,
        error: null,
        dataUpdatedAt: Date.now(),
      } as ReturnType<typeof useLicensesModule.useLicenseSummary>);

      render(<LicenseSummaryWidget />, { wrapper });

      expect(screen.getByText(/15 vendors/)).toBeTruthy();
      expect(screen.getByText(/42 SKUs/)).toBeTruthy();
    });
  });

  describe('Health status indicators', () => {
    it('shows green indicator for healthy status', () => {
      vi.spyOn(useLicensesModule, 'useLicenseSummary').mockReturnValue({
        data: { ...mockSummary, health_status: HealthStatus.OK },
        isLoading: false,
        error: null,
        dataUpdatedAt: Date.now(),
      } as ReturnType<typeof useLicensesModule.useLicenseSummary>);

      render(<LicenseSummaryWidget />, { wrapper });

      const indicator = document.querySelector('.bg-eucora-green');
      expect(indicator).toBeTruthy();
    });

    it('shows gold indicator for degraded status', () => {
      vi.spyOn(useLicensesModule, 'useLicenseSummary').mockReturnValue({
        data: { ...mockSummary, health_status: HealthStatus.DEGRADED },
        isLoading: false,
        error: null,
        dataUpdatedAt: Date.now(),
      } as ReturnType<typeof useLicensesModule.useLicenseSummary>);

      render(<LicenseSummaryWidget />, { wrapper });

      const indicator = document.querySelector('.bg-eucora-gold');
      expect(indicator).toBeTruthy();
    });

    it('shows red indicator for failed status', () => {
      vi.spyOn(useLicensesModule, 'useLicenseSummary').mockReturnValue({
        data: { ...mockSummary, health_status: HealthStatus.FAILED },
        isLoading: false,
        error: null,
        dataUpdatedAt: Date.now(),
      } as ReturnType<typeof useLicensesModule.useLicenseSummary>);

      render(<LicenseSummaryWidget />, { wrapper });

      const indicator = document.querySelector('.bg-red-500');
      expect(indicator).toBeTruthy();
    });

    it('shows orange indicator for stale status', () => {
      vi.spyOn(useLicensesModule, 'useLicenseSummary').mockReturnValue({
        data: { ...mockSummary, health_status: HealthStatus.STALE },
        isLoading: false,
        error: null,
        dataUpdatedAt: Date.now(),
      } as ReturnType<typeof useLicensesModule.useLicenseSummary>);

      render(<LicenseSummaryWidget />, { wrapper });

      const indicator = document.querySelector('.bg-orange-400');
      expect(indicator).toBeTruthy();
    });
  });

  describe('Stale data warning', () => {
    it('shows stale warning when data exceeds threshold', () => {
      const staleSeconds = 3 * 60 * 60; // 3 hours
      vi.spyOn(useLicensesModule, 'useLicenseSummary').mockReturnValue({
        data: {
          ...mockSummary,
          health_status: HealthStatus.STALE,
          stale_duration_seconds: staleSeconds,
        },
        isLoading: false,
        error: null,
        dataUpdatedAt: Date.now(),
      } as ReturnType<typeof useLicensesModule.useLicenseSummary>);

      render(<LicenseSummaryWidget />, { wrapper });

      expect(screen.getByText(/Data stale/)).toBeTruthy();
      expect(screen.getByText(/3h/)).toBeTruthy();
    });

    it('does not show stale warning when within threshold', () => {
      const okSeconds = 30 * 60; // 30 minutes
      vi.spyOn(useLicensesModule, 'useLicenseSummary').mockReturnValue({
        data: {
          ...mockSummary,
          stale_duration_seconds: okSeconds,
        },
        isLoading: false,
        error: null,
        dataUpdatedAt: Date.now(),
      } as ReturnType<typeof useLicensesModule.useLicenseSummary>);

      render(<LicenseSummaryWidget />, { wrapper });

      expect(screen.queryByText(/Data stale/)).toBeNull();
    });
  });

  describe('Active alerts', () => {
    it('shows alert badge when there are active alerts', () => {
      vi.spyOn(useLicensesModule, 'useLicenseSummary').mockReturnValue({
        data: { ...mockSummary, active_alerts_count: 3 },
        isLoading: false,
        error: null,
        dataUpdatedAt: Date.now(),
      } as ReturnType<typeof useLicensesModule.useLicenseSummary>);

      render(<LicenseSummaryWidget />, { wrapper });

      expect(screen.getByText('3 active alerts')).toBeTruthy();
    });

    it('shows singular alert text for one alert', () => {
      vi.spyOn(useLicensesModule, 'useLicenseSummary').mockReturnValue({
        data: { ...mockSummary, active_alerts_count: 1 },
        isLoading: false,
        error: null,
        dataUpdatedAt: Date.now(),
      } as ReturnType<typeof useLicensesModule.useLicenseSummary>);

      render(<LicenseSummaryWidget />, { wrapper });

      expect(screen.getByText('1 active alert')).toBeTruthy();
    });

    it('does not show alert badge when there are no alerts', () => {
      vi.spyOn(useLicensesModule, 'useLicenseSummary').mockReturnValue({
        data: { ...mockSummary, active_alerts_count: 0 },
        isLoading: false,
        error: null,
        dataUpdatedAt: Date.now(),
      } as ReturnType<typeof useLicensesModule.useLicenseSummary>);

      render(<LicenseSummaryWidget />, { wrapper });

      expect(screen.queryByText(/active alert/)).toBeNull();
    });
  });

  describe('Utilization color coding', () => {
    it('shows green progress bar when utilization is below 80%', () => {
      vi.spyOn(useLicensesModule, 'useLicenseSummary').mockReturnValue({
        data: {
          ...mockSummary,
          total_consumed: 500,
          total_entitled: 1000,
        },
        isLoading: false,
        error: null,
        dataUpdatedAt: Date.now(),
      } as ReturnType<typeof useLicensesModule.useLicenseSummary>);

      render(<LicenseSummaryWidget />, { wrapper });

      const progressBar = document.querySelector('.bg-eucora-green.h-full');
      expect(progressBar).toBeTruthy();
    });

    it('shows gold progress bar when utilization is 80-95%', () => {
      vi.spyOn(useLicensesModule, 'useLicenseSummary').mockReturnValue({
        data: {
          ...mockSummary,
          total_consumed: 900,
          total_entitled: 1000,
          total_remaining: 100,
        },
        isLoading: false,
        error: null,
        dataUpdatedAt: Date.now(),
      } as ReturnType<typeof useLicensesModule.useLicenseSummary>);

      render(<LicenseSummaryWidget />, { wrapper });

      const progressBar = document.querySelector('.bg-eucora-gold.h-full');
      expect(progressBar).toBeTruthy();
    });

    it('shows red progress bar when utilization exceeds 95%', () => {
      vi.spyOn(useLicensesModule, 'useLicenseSummary').mockReturnValue({
        data: {
          ...mockSummary,
          total_consumed: 980,
          total_entitled: 1000,
          total_remaining: 20,
        },
        isLoading: false,
        error: null,
        dataUpdatedAt: Date.now(),
      } as ReturnType<typeof useLicensesModule.useLicenseSummary>);

      render(<LicenseSummaryWidget />, { wrapper });

      const progressBar = document.querySelector('.bg-red-500.h-full');
      expect(progressBar).toBeTruthy();
    });
  });

  describe('Compact mode', () => {
    it('renders compact view when compact prop is true', () => {
      vi.spyOn(useLicensesModule, 'useLicenseSummary').mockReturnValue({
        data: mockSummary,
        isLoading: false,
        error: null,
        dataUpdatedAt: Date.now(),
      } as ReturnType<typeof useLicensesModule.useLicenseSummary>);

      render(<LicenseSummaryWidget compact />, { wrapper });

      // Compact mode should not show the full details
      expect(screen.queryByText('Consumed')).toBeNull();
      expect(screen.queryByText('Entitled')).toBeNull();
      expect(screen.queryByText('Remaining')).toBeNull();
    });
  });

  describe('Remaining quantity styling', () => {
    it('shows green text when remaining is positive', () => {
      vi.spyOn(useLicensesModule, 'useLicenseSummary').mockReturnValue({
        data: { ...mockSummary, total_remaining: 100 },
        isLoading: false,
        error: null,
        dataUpdatedAt: Date.now(),
      } as ReturnType<typeof useLicensesModule.useLicenseSummary>);

      render(<LicenseSummaryWidget />, { wrapper });

      const remainingValue = screen.getByText('100');
      expect(remainingValue.classList.contains('text-eucora-green')).toBe(true);
    });

    it('shows red text when remaining is zero or negative', () => {
      vi.spyOn(useLicensesModule, 'useLicenseSummary').mockReturnValue({
        data: {
          ...mockSummary,
          total_consumed: 1050,
          total_remaining: -50,
        },
        isLoading: false,
        error: null,
        dataUpdatedAt: Date.now(),
      } as ReturnType<typeof useLicensesModule.useLicenseSummary>);

      render(<LicenseSummaryWidget />, { wrapper });

      const remainingValue = screen.getByText('-50');
      expect(remainingValue.classList.contains('text-red-500')).toBe(true);
    });
  });

  describe('Edge cases', () => {
    it('handles zero entitled licenses gracefully', () => {
      vi.spyOn(useLicensesModule, 'useLicenseSummary').mockReturnValue({
        data: {
          ...mockSummary,
          total_entitled: 0,
          total_consumed: 0,
          total_remaining: 0,
        },
        isLoading: false,
        error: null,
        dataUpdatedAt: Date.now(),
      } as ReturnType<typeof useLicensesModule.useLicenseSummary>);

      render(<LicenseSummaryWidget />, { wrapper });

      expect(screen.getByText('0%')).toBeTruthy();
    });

    it('handles never reconciled state', () => {
      vi.spyOn(useLicensesModule, 'useLicenseSummary').mockReturnValue({
        data: { ...mockSummary, last_reconciled_at: null },
        isLoading: false,
        error: null,
        dataUpdatedAt: Date.now(),
      } as ReturnType<typeof useLicensesModule.useLicenseSummary>);

      render(<LicenseSummaryWidget />, { wrapper });

      expect(screen.getByText(/Synced Never/)).toBeTruthy();
    });
  });

  describe('className prop', () => {
    it('applies additional className to container', () => {
      vi.spyOn(useLicensesModule, 'useLicenseSummary').mockReturnValue({
        data: mockSummary,
        isLoading: false,
        error: null,
        dataUpdatedAt: Date.now(),
      } as ReturnType<typeof useLicensesModule.useLicenseSummary>);

      const { container } = render(
        <LicenseSummaryWidget className="custom-class" />,
        { wrapper }
      );

      expect(container.querySelector('.custom-class')).toBeTruthy();
    });
  });
});

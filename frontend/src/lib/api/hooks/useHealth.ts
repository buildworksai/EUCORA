/**
 * TanStack Query hooks for system health checks.
 */
import { useQuery } from '@tanstack/react-query';
import { api } from '../client';

export interface HealthCheck {
  status: 'healthy' | 'unhealthy';
  checks: {
    database?: { status: string; error?: string };
    cache?: { status: string; error?: string };
    application?: { name: string; organization: string; version: string };
  };
}

/**
 * Fetch system health status.
 */
export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      return api.get<HealthCheck>('/health/');
    },
    staleTime: 120000, // 2 minutes
    refetchInterval: 180000, // Poll every 3 minutes
    retry: 1, // Don't retry health checks aggressively
  });
}

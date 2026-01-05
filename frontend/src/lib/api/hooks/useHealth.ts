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
    staleTime: 10000, // 10 seconds
    refetchInterval: 30000, // Poll every 30 seconds
    retry: 1, // Don't retry health checks aggressively
  });
}


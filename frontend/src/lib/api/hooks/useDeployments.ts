/**
 * TanStack Query hooks for deployment intents.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';
import type { DeploymentIntent } from '@/types/api';

export interface DeploymentFilters {
  status?: string;
  ring?: string;
  app_name?: string;
}

export interface CreateDeploymentData {
  app_name: string;
  version: string;
  target_ring: string;
  evidence_pack?: Record<string, unknown>;
}

export interface DeploymentListResponse {
  deployments: DeploymentIntent[];
}

/**
 * Fetch list of deployments with optional filters.
 */
export function useDeployments(filters?: DeploymentFilters) {
  return useQuery({
    queryKey: ['deployments', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.ring) params.append('ring', filters.ring);
      if (filters?.app_name) params.append('app_name', filters.app_name);

      const queryString = params.toString();
      const response = await api.get<DeploymentListResponse>(
        `/deployments/list${queryString ? `?${queryString}` : ''}`
      );
      return response.deployments;
    },
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Poll every minute for real-time updates
    refetchOnWindowFocus: true,
  });
}

/**
 * Fetch single deployment by correlation ID.
 */
export function useDeployment(correlationId: string) {
  return useQuery({
    queryKey: ['deployment', correlationId],
    queryFn: async () => {
      return api.get<DeploymentIntent>(`/deployments/${correlationId}/`);
    },
    enabled: !!correlationId,
    staleTime: 30000,
    refetchInterval: 30000, // Poll every 30 seconds for status updates
  });
}

/**
 * Create new deployment intent.
 */
export function useCreateDeployment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateDeploymentData) => {
      return api.post<{ correlation_id: string; status: string; risk_score: number; requires_cab_approval: boolean }>(
        '/deployments/',
        data
      );
    },
    onSuccess: () => {
      // Invalidate and refetch deployment list
      queryClient.invalidateQueries({ queryKey: ['deployments'] });
    },
  });
}

/**
 * Promote deployment to next ring.
 */
export function usePromoteRing(correlationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      // Note: This endpoint may need to be added to backend
      return api.post<DeploymentIntent>(`/deployments/${correlationId}/promote/`, {});
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deployment', correlationId] });
      queryClient.invalidateQueries({ queryKey: ['deployments'] });
    },
  });
}

/**
 * Rollback deployment.
 */
export function useRollbackDeployment(correlationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      // Note: This endpoint may need to be added to backend
      return api.post<DeploymentIntent>(`/deployments/${correlationId}/rollback/`, {});
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deployment', correlationId] });
      queryClient.invalidateQueries({ queryKey: ['deployments'] });
    },
  });
}


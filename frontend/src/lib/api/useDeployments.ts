/**
 * TanStack Query hooks for deployment intents.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from './client';
import type { DeploymentIntent } from '@/types/api';

export function useDeployments(filters?: { status?: string; ring?: string }) {
    return useQuery({
        queryKey: ['deployments', filters],
        queryFn: () => {
            const params = new URLSearchParams(filters as Record<string, string>);
            return api.get<DeploymentIntent[]>(`/api/v1/deployment-intents/?${params}`);
        },
    });
}

export function useDeployment(id: number) {
    return useQuery({
        queryKey: ['deployment', id],
        queryFn: () => api.get<DeploymentIntent>(`/api/v1/deployment-intents/${id}/`),
    });
}

export function useCreateDeployment() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: { app_name: string; version: string; target_ring: string; evidence_pack: unknown }) =>
            api.post<DeploymentIntent>('/api/v1/deployment-intents/', data),
        onSuccess: () => {
            // Invalidate cache to refetch deployment list
            queryClient.invalidateQueries({ queryKey: ['deployments'] });
        },
    });
}

export function usePromoteRing(id: number) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: () => api.post<DeploymentIntent>(`/api/v1/deployment-intents/${id}/promote_ring/`, {}),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['deployment', id] });
            queryClient.invalidateQueries({ queryKey: ['deployments'] });
        },
    });
}

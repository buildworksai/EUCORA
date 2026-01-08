/**
 * TanStack Query hooks for CAB (Change Advisory Board) workflows.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';
import { toast } from 'sonner';

export interface CABApproval {
  id: number;
  deployment_intent: string;
  correlation_id: string;
  decision: 'PENDING' | 'APPROVED' | 'REJECTED' | 'CONDITIONAL';
  approver: string | null;
  comments: string;
  conditions: string[];
  submitted_at: string;
  reviewed_at: string | null;
  app_name: string;
  version: string;
  risk_score: number;
}

export interface CABApprovalListResponse {
  approvals: CABApproval[];
}

export interface ApproveDeploymentData {
  comments: string;
  conditions?: string[];
}

/**
 * Fetch pending CAB approvals.
 */
export function usePendingApprovals() {
  return useQuery({
    queryKey: ['cab-approvals', 'pending'],
    queryFn: async () => {
      const response = await api.get<CABApprovalListResponse>('/cab/pending/');
      return response.approvals;
    },
    staleTime: 15000, // 15 seconds
    refetchInterval: 30000, // Poll every 30 seconds for new approvals
    refetchOnWindowFocus: true,
  });
}

/**
 * Fetch all CAB approvals (for history/audit).
 */
export function useCABApprovals(filters?: { decision?: string }) {
  return useQuery({
    queryKey: ['cab-approvals', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.decision) params.append('decision', filters.decision);

      const queryString = params.toString();
      const response = await api.get<CABApprovalListResponse>(
        `/cab/approvals${queryString ? `?${queryString}` : ''}`
      );
      return response.approvals;
    },
    staleTime: 60000, // 1 minute
  });
}

/**
 * Approve deployment intent.
 */
export function useApproveDeployment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ correlationId, data }: { correlationId: string; data: ApproveDeploymentData }) => {
      const response = await api.post<{ message: string; decision: string }>(
        `/cab/${correlationId}/approve`,
        data
      );
      return { correlationId, ...response };
    },
    onSuccess: ({ correlationId, decision }) => {
      queryClient.invalidateQueries({ queryKey: ['cab-approvals'] });
      queryClient.invalidateQueries({ queryKey: ['deployments'] });
      queryClient.invalidateQueries({ queryKey: ['deployment', correlationId] });
      
      toast.success('Deployment approved', {
        description: decision === 'CONDITIONAL' ? 'Approved with conditions' : 'Deployment can proceed',
      });
    },
    onError: (error) => {
      // Suppress authentication errors for demo/testing
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      if (!errorMessage.includes('401') && !errorMessage.includes('403') && !errorMessage.includes('Unauthorized')) {
        toast.error('Failed to approve deployment', {
          description: errorMessage,
        });
      }
    },
  });
}

/**
 * Reject deployment intent.
 */
export function useRejectDeployment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ correlationId, comments }: { correlationId: string; comments: string }) => {
      const response = await api.post<{ message: string }>(
        `/cab/${correlationId}/reject`,
        { comments }
      );
      return { correlationId, ...response };
    },
    onSuccess: ({ correlationId }) => {
      queryClient.invalidateQueries({ queryKey: ['cab-approvals'] });
      queryClient.invalidateQueries({ queryKey: ['deployments'] });
      queryClient.invalidateQueries({ queryKey: ['deployment', correlationId] });
      
      toast.success('Deployment rejected', {
        description: 'Deployment has been blocked',
      });
    },
    onError: (error) => {
      // Suppress authentication errors for demo/testing
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      if (!errorMessage.includes('401') && !errorMessage.includes('403') && !errorMessage.includes('Unauthorized')) {
        toast.error('Failed to reject deployment', {
          description: errorMessage,
        });
      }
    },
  });
}


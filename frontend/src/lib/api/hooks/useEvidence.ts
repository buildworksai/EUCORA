/**
 * TanStack Query hooks for evidence packs.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';
import { toast } from 'sonner';

export interface EvidencePack {
  correlation_id: string;
  app_name: string;
  version: string;
  artifact_hash: string;
  artifact_signature?: string;
  artifact_path?: string;
  sbom_data: Record<string, unknown>;
  vulnerability_scan_results: Record<string, unknown>;
  scan_policy_decision?: 'PASS' | 'FAIL' | 'EXCEPTION';
  rollback_plan?: string;
  is_validated: boolean;
  created_at: string;
}

export interface UploadEvidenceData {
  app_name: string;
  version: string;
  artifact: File;
  sbom_data?: Record<string, unknown>;
  vulnerability_scan_results?: Record<string, unknown>;
  rollback_plan?: string;
}

/**
 * Fetch evidence pack by correlation ID.
 */
export function useEvidencePack(correlationId: string) {
  return useQuery({
    queryKey: ['evidence', correlationId],
    queryFn: async () => {
      return api.get<EvidencePack>(`/evidence/${correlationId}/`);
    },
    enabled: !!correlationId,
    staleTime: 300000, // 5 minutes (evidence packs don't change)
  });
}

/**
 * Upload evidence pack with artifact file.
 */
export function useUploadEvidencePack() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: UploadEvidenceData) => {
      const formData = new FormData();
      formData.append('app_name', data.app_name);
      formData.append('version', data.version);
      formData.append('artifact', data.artifact);
      
      if (data.sbom_data) {
        formData.append('sbom_data', JSON.stringify(data.sbom_data));
      }
      
      if (data.vulnerability_scan_results) {
        formData.append('vulnerability_scan_results', JSON.stringify(data.vulnerability_scan_results));
      }
      
      if (data.rollback_plan) {
        formData.append('rollback_plan', data.rollback_plan);
      }

      return api.postFormData<{ correlation_id: string; artifact_hash: string; is_validated: boolean }>(
        '/evidence/',
        formData
      );
    },
    onSuccess: ({ correlation_id, is_validated }) => {
      queryClient.invalidateQueries({ queryKey: ['evidence', correlation_id] });
      
      if (!is_validated) {
        toast.warning('Evidence pack uploaded but validation failed', {
          description: 'Please review SBOM, vulnerability scan, and rollback plan',
        });
      } else {
        toast.success('Evidence pack uploaded successfully', {
          description: `Correlation ID: ${correlation_id}`,
        });
      }
    },
    onError: (error) => {
      // Suppress authentication errors for demo/testing
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      if (!errorMessage.includes('401') && !errorMessage.includes('403') && !errorMessage.includes('Unauthorized')) {
        toast.error('Failed to upload evidence pack', {
          description: errorMessage,
        });
      }
    },
  });
}


// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * BuildWorks.AI-27001: CAB domain contracts
 * BuildWorks.AI-27002: Types, endpoints, and examples for CAB workflows
 * BuildWorks.AI-27004: Use ENDPOINTS constant, never hardcode URL strings
 */

/**
 * CAB domain types
 */
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

export interface RejectDeploymentData {
  comments: string;
}

export interface ApproveDeploymentResponse {
  message: string;
  decision: string;
}

export interface RejectDeploymentResponse {
  message: string;
}

/**
 * BuildWorks.AI-27004: ENDPOINTS constant - never hardcode URL strings
 */
export const ENDPOINTS = {
  CAB_PENDING: '/cab/pending/',
  CAB_APPROVALS: '/cab/approvals',
  CAB_APPROVE: (correlationId: string) => `/cab/${correlationId}/approve`,
  CAB_REJECT: (correlationId: string) => `/cab/${correlationId}/reject`,
} as const;

/**
 * Example usage:
 *
 * ```typescript
 * import { ENDPOINTS, type CABApprovalListResponse } from './contracts';
 * import { api } from '@/lib/api/client';
 *
 * const response = await api.get<CABApprovalListResponse>(ENDPOINTS.CAB_PENDING);
 * ```
 */

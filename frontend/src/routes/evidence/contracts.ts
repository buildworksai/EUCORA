// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * BuildWorks.AI-27001: Evidence domain contracts
 * BuildWorks.AI-27002: Types, endpoints, and examples for evidence packs
 * BuildWorks.AI-27004: Use ENDPOINTS constant, never hardcode URL strings
 */

import type { EvidencePack } from '@/types/api';

/**
 * Evidence domain types
 */
export interface EvidencePackDetail extends EvidencePack {
  deployment_intent?: {
    correlation_id: string;
    app_name: string;
    version: string;
    target_ring: string;
  };
}

export interface EvidencePackListResponse {
  evidence_packs: EvidencePack[];
  count: number;
}

/**
 * BuildWorks.AI-27004: ENDPOINTS constant - never hardcode URL strings
 */
export const ENDPOINTS = {
  EVIDENCE_LIST: '/evidence/',
  EVIDENCE_DETAIL: (id: number) => `/evidence/${id}/`,
  EVIDENCE_BY_CORRELATION: (correlationId: string) => `/evidence/correlation/${correlationId}/`,
} as const;

/**
 * Example usage:
 *
 * ```typescript
 * import { ENDPOINTS, type EvidencePackDetail } from './contracts';
 * import { api } from '@/lib/api/client';
 *
 * const response = await api.get<EvidencePackDetail>(ENDPOINTS.EVIDENCE_DETAIL(123));
 * ```
 */

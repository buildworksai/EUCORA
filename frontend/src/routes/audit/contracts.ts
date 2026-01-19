// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * BuildWorks.AI-27001: Audit domain contracts
 * BuildWorks.AI-27002: Types, endpoints, and examples for audit trail
 * BuildWorks.AI-27004: Use ENDPOINTS constant, never hardcode URL strings
 */

import type { DeploymentEvent } from '@/types/api';

/**
 * Audit domain types
 */
export interface AuditEvent extends DeploymentEvent {
  user?: string;
  action?: string;
  resource_type?: string;
}

export interface AuditEventListResponse {
  events: AuditEvent[];
  count: number;
  page: number;
  page_size: number;
}

export interface AuditFilters {
  correlation_id?: string;
  event_type?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}

/**
 * BuildWorks.AI-27004: ENDPOINTS constant - never hardcode URL strings
 */
export const ENDPOINTS = {
  AUDIT_EVENTS: '/events/',
  AUDIT_EVENT_DETAIL: (id: number) => `/events/${id}/`,
  AUDIT_BY_CORRELATION: (correlationId: string) => `/events/correlation/${correlationId}/`,
} as const;

/**
 * Example usage:
 * 
 * ```typescript
 * import { ENDPOINTS, type AuditEventListResponse } from './contracts';
 * import { api } from '@/lib/api/client';
 * 
 * const response = await api.get<AuditEventListResponse>(ENDPOINTS.AUDIT_EVENTS);
 * ```
 */

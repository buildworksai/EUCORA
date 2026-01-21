// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * BuildWorks.AI-27001: Compliance domain contracts
 * BuildWorks.AI-27002: Types, endpoints, and examples for compliance dashboard
 * BuildWorks.AI-27004: Use ENDPOINTS constant, never hardcode URL strings
 */

/**
 * Compliance domain types
 */
export interface ComplianceMetrics {
  total_deployments: number;
  compliant_deployments: number;
  non_compliant_deployments: number;
  compliance_rate: number;
  risk_distribution: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  cab_approval_rate: number;
  scan_pass_rate: number;
}

export interface ComplianceReport {
  period: string;
  metrics: ComplianceMetrics;
  violations: ComplianceViolation[];
}

export interface ComplianceViolation {
  id: number;
  correlation_id: string;
  violation_type: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  description: string;
  detected_at: string;
  resolved: boolean;
}

export interface ComplianceReportResponse {
  report: ComplianceReport;
}

export interface ComplianceTrendPoint {
  date: string;
  score: number;
}

export interface ComplianceDistributionDatum {
  name: string;
  value: number;
  color: string;
  [key: string]: string | number;
}

export interface ComplianceStatsResponse {
  overall_compliance: number;
  critical_vulnerabilities: number;
  policy_conflicts: number;
  pending_updates: number;
  compliance_trend: ComplianceTrendPoint[];
  vulnerability_data: ComplianceDistributionDatum[];
  os_distribution: ComplianceDistributionDatum[];
  total_assets: number;
  active_assets: number;
}

/**
 * BuildWorks.AI-27004: ENDPOINTS constant - never hardcode URL strings
 */
export const ENDPOINTS = {
  COMPLIANCE_METRICS: '/compliance/metrics/',
  COMPLIANCE_REPORT: '/compliance/report/',
  COMPLIANCE_VIOLATIONS: '/compliance/violations/',
  COMPLIANCE_STATS: '/health/compliance-stats',
} as const;

/**
 * Example usage:
 * 
 * ```typescript
 * import { ENDPOINTS, type ComplianceMetrics } from './contracts';
 * import { api } from '@/lib/api/client';
 * 
 * const response = await api.get<ComplianceMetrics>(ENDPOINTS.COMPLIANCE_METRICS);
 * ```
 */

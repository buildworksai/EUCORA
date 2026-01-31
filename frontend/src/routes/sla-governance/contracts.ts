// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * E19: SLA Governance Agent - Type Contracts
 */

// API Endpoints
export const ENDPOINTS = {
  services: '/api/sla-governance/services/',
  serviceDetail: (id: string) => `/api/sla-governance/services/${id}/`,
  slas: '/api/sla-governance/slas/',
  slaDetail: (id: string) => `/api/sla-governance/slas/${id}/`,
  slaApprove: (id: string) => `/api/sla-governance/slas/${id}/approve/`,
  slaActivate: (id: string) => `/api/sla-governance/slas/${id}/activate/`,
  targets: '/api/sla-governance/targets/',
  targetDetail: (id: string) => `/api/sla-governance/targets/${id}/`,
  kpis: '/api/sla-governance/kpis/',
  kpiDetail: (id: string) => `/api/sla-governance/kpis/${id}/`,
  kpiLinks: '/api/sla-governance/kpi-links/',
  measurements: '/api/sla-governance/measurements/',
  compliance: '/api/sla-governance/compliance/',
  complianceAtRisk: '/api/sla-governance/compliance/at-risk/',
  breaches: '/api/sla-governance/breaches/',
  breachDetail: (id: string) => `/api/sla-governance/breaches/${id}/`,
  templates: '/api/sla-governance/templates/',
  templateDetail: (id: string) => `/api/sla-governance/templates/${id}/`,
  parseRequest: '/api/sla-governance/parse-request/parse/',
  reportsSummary: '/api/sla-governance/reports/summary/',
  reportsTrends: '/api/sla-governance/reports/trends/',
} as const;

// SLA Status Types
export type SLAStatus = 'draft' | 'pending_approval' | 'active' | 'expired';

export interface ServiceCatalogItem {
  id: string;
  name: string;
  description: string;
  category: string;
  owner: string;
  status: string;
  servicenow_sys_id: string | null;
  sla_count: number;
  created_at: string;
  updated_at: string;
}

export interface SLADefinition {
  id: string;
  correlation_id: string;
  name: string;
  description: string;
  service: string;
  service_name: string;
  version: string;
  effective_from: string;
  effective_until: string | null;
  status: SLAStatus;
  original_request: string | null;
  created_by: string;
  created_by_name: string;
  approved_by: string | null;
  approved_by_name: string | null;
  approved_at: string | null;
  target_count: number;
  compliance_status: string | null;
  breach_count: number;
  created_at: string;
  updated_at: string;
}

export type MetricType = 'availability' | 'response_time' | 'resolution_time' | 'quality';

export interface SLATarget {
  id: string;
  sla: string;
  name: string;
  metric_type: MetricType;
  target_value: number;
  target_unit: string;
  measurement_period: string;
  applies_to: Record<string, unknown> | null;
  kpi_count: number;
  created_at: string;
  updated_at: string;
}

export type KPIDirection = 'higher_better' | 'lower_better';

export interface KPIDefinition {
  id: string;
  name: string;
  description: string;
  formula: string;
  data_sources: string[];
  unit: string;
  direction: KPIDirection;
  thresholds: Record<string, unknown>;
  is_active: boolean;
  measurement_count: number;
  latest_value: number | null;
  latest_status: string | null;
  created_at: string;
  updated_at: string;
}

export interface SLAKPILink {
  id: string;
  sla_target: string;
  sla_target_name: string;
  kpi: string;
  kpi_name: string;
  weight: number;
  created_at: string;
  updated_at: string;
}

export type MeasurementStatus = 'green' | 'yellow' | 'red';

export interface KPIMeasurement {
  id: string;
  kpi: string;
  kpi_name: string;
  kpi_unit: string;
  measurement_time: string;
  value: number;
  status: MeasurementStatus;
  data_points: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export type ComplianceStatus = 'compliant' | 'at_risk' | 'breached';

export interface SLACompliance {
  id: string;
  correlation_id: string;
  sla: string;
  sla_name: string;
  sla_version: string;
  period_start: string;
  period_end: string;
  overall_compliance: number;
  target_compliances: Record<string, number>;
  breach_count: number;
  near_miss_count: number;
  status: ComplianceStatus;
  created_at: string;
  updated_at: string;
}

export type BreachSeverity = 'critical' | 'high' | 'medium' | 'low';

export interface SLABreach {
  id: string;
  correlation_id: string;
  sla: string;
  sla_name: string;
  target: string;
  target_name: string;
  breach_time: string;
  severity: BreachSeverity;
  target_value: number;
  actual_value: number;
  root_cause: string | null;
  remediation: string | null;
  servicenow_incident: string | null;
  created_at: string;
  updated_at: string;
}

export interface SLATemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  default_targets: unknown[];
  variables: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SLASummaryReport {
  total_slas: number;
  active_slas: number;
  at_risk_count: number;
  breach_count: number;
}

export interface SLATrend {
  date: string;
  compliance: number;
  status: ComplianceStatus;
}

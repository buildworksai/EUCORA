// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * E17: SecOps Agent - Type Contracts
 */

// API Endpoints
export const ENDPOINTS = {
  scanners: '/api/secops/scanners/',
  scannerDetail: (id: string) => `/api/secops/scanners/${id}/`,
  scannerSync: (id: string) => `/api/secops/scanners/${id}/sync/`,
  scannerTest: (id: string) => `/api/secops/scanners/${id}/test/`,
  vulnerabilities: '/api/secops/vulnerabilities/',
  vulnerabilityDetail: (id: string) => `/api/secops/vulnerabilities/${id}/`,
  vulnerabilityInstances: (id: string) => `/api/secops/vulnerabilities/${id}/instances/`,
  instances: '/api/secops/instances/',
  instanceDetail: (id: string) => `/api/secops/instances/${id}/`,
  instanceRemediate: (id: string) => `/api/secops/instances/${id}/remediate/`,
  instanceAcceptRisk: (id: string) => `/api/secops/instances/${id}/accept-risk/`,
  instanceFalsePositive: (id: string) => `/api/secops/instances/${id}/false-positive/`,
  remediationPlans: '/api/secops/remediation-plans/',
  remediationPlanDetail: (id: string) => `/api/secops/remediation-plans/${id}/`,
  remediationPlanApprove: (id: string) => `/api/secops/remediation-plans/${id}/approve/`,
  remediationPlanExecute: (id: string) => `/api/secops/remediation-plans/${id}/execute/`,
  siem: '/api/secops/siem/',
  siemDetail: (id: string) => `/api/secops/siem/${id}/`,
  siemTest: (id: string) => `/api/secops/siem/${id}/test/`,
  siemSyncAlerts: (id: string) => `/api/secops/siem/${id}/sync_alerts/`,
  alerts: '/api/secops/alerts/',
  alertDetail: (id: string) => `/api/secops/alerts/${id}/`,
  alertCorrelate: (id: string) => `/api/secops/alerts/${id}/correlate/`,
  alertCreateIncident: (id: string) => `/api/secops/alerts/${id}/create_incident/`,
  complianceBaselines: '/api/secops/compliance-baselines/',
  complianceBaselineDetail: (id: string) => `/api/secops/compliance-baselines/${id}/`,
  complianceChecks: '/api/secops/compliance-checks/',
  complianceCheckRun: '/api/secops/compliance-checks/run_check/',
  reportsSummary: '/api/secops/reports/summary/',
  reportsRiskTrend: '/api/secops/reports/risk_trend/',
  reportsComplianceStatus: '/api/secops/reports/compliance_status/',
} as const;

// Scanner Types
export type ScannerType = 'qualys' | 'nessus' | 'rapid7' | 'defender';

export interface VulnerabilityScanner {
  id: string;
  name: string;
  scanner_type: ScannerType;
  connection_config: Record<string, unknown>;
  sync_schedule: string;
  last_sync: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Vulnerability Types
export type Severity = 'critical' | 'high' | 'medium' | 'low';

export interface Vulnerability {
  id: string;
  cve_id: string;
  title: string;
  description: string;
  severity: Severity;
  cvss_score: number | null;
  cvss_vector: string | null;
  exploitability_score: number | null;
  published_date: string;
  modified_date: string;
  references: string[];
  affected_products: string[];
  instance_count: number;
  created_at: string;
  updated_at: string;
}

export type VulnerabilityInstanceStatus = 'open' | 'remediated' | 'accepted' | 'false_positive';

export interface VulnerabilityInstance {
  id: string;
  correlation_id: string;
  vulnerability: string;
  vulnerability_cve: string;
  vulnerability_title: string;
  vulnerability_severity: Severity;
  asset_id: string;
  asset_name: string;
  application: string | null;
  scanner: string;
  scanner_name: string;
  detected_at: string;
  status: VulnerabilityInstanceStatus;
  remediation_due: string | null;
  remediated_at: string | null;
  remediation_notes: string | null;
  created_at: string;
  updated_at: string;
}

// Remediation Types
export type RemediationType = 'patch' | 'config' | 'compensating' | 'upgrade';
export type RiskLevel = 'R1' | 'R2' | 'R3';
export type RemediationPlanStatus = 'draft' | 'pending_approval' | 'approved' | 'executing' | 'completed' | 'rejected';

export interface RemediationPlan {
  id: string;
  correlation_id: string;
  name: string;
  vulnerability: string;
  vulnerability_cve: string;
  remediation_type: RemediationType;
  description: string;
  steps: Array<Record<string, unknown>>;
  affected_instances: string[];
  risk_level: RiskLevel;
  status: RemediationPlanStatus;
  approved_by: string | null;
  approved_by_name: string | null;
  approved_at: string | null;
  executed_at: string | null;
  completed_at: string | null;
  affected_instance_count: number;
  created_at: string;
  updated_at: string;
}

// SIEM Types
export type SIEMType = 'sentinel' | 'splunk' | 'qradar' | 'elastic';
export type AlertSeverity = 'critical' | 'high' | 'medium' | 'low' | 'informational';
export type AlertStatus = 'new' | 'investigating' | 'resolved' | 'false_positive';

export interface SIEMConnection {
  id: string;
  name: string;
  siem_type: SIEMType;
  connection_config: Record<string, unknown>;
  is_active: boolean;
  alert_count: number;
  created_at: string;
  updated_at: string;
}

export interface SecurityAlert {
  id: string;
  correlation_id: string;
  siem: string;
  siem_name: string;
  alert_id: string;
  title: string;
  severity: AlertSeverity;
  description: string;
  source: string;
  affected_assets: string[];
  alert_time: string;
  status: AlertStatus;
  related_vulnerabilities: string[];
  remediation_plan: string | null;
  related_vulnerability_count: number;
  created_at: string;
  updated_at: string;
}

// Compliance Types
export type Framework = 'cis' | 'nist' | 'soc2' | 'iso27001';

export interface ComplianceBaseline {
  id: string;
  name: string;
  framework: Framework;
  version: string;
  controls: Array<Record<string, unknown>>;
  is_active: boolean;
  control_count: number;
  check_count: number;
  created_at: string;
  updated_at: string;
}

export interface ComplianceCheck {
  id: string;
  correlation_id: string;
  baseline: string;
  baseline_name: string;
  framework: Framework;
  asset_id: string;
  check_time: string;
  overall_score: number;
  passed_controls: number;
  failed_controls: number;
  control_results: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

// Report Types
export interface SecOpsSummary {
  critical_vulnerabilities: number;
  high_vulnerabilities: number;
  medium_vulnerabilities: number;
  pending_remediation_plans: number;
  executing_remediation_plans: number;
  critical_alerts: number;
  high_alerts: number;
}

export interface RiskTrend {
  trends: Array<{ date: string; count: number }>;
}

export interface ComplianceStatus {
  compliance_status: Array<{
    baseline_id: string;
    framework: Framework;
    name: string;
    average_score: number;
    check_count: number;
  }>;
}

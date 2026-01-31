// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * E18: SRE Agent - Type Contracts
 */

// API Endpoints
export const ENDPOINTS = {
  monitoringPlatforms: '/api/sre/monitoring-platforms/',
  monitoringPlatformDetail: (id: string) => `/api/sre/monitoring-platforms/${id}/`,
  monitoringPlatformTest: (id: string) => `/api/sre/monitoring-platforms/${id}/test/`,
  healthEndpoints: '/api/sre/health-endpoints/',
  healthEndpointDetail: (id: string) => `/api/sre/health-endpoints/${id}/`,
  healthEndpointCheck: (id: string) => `/api/sre/health-endpoints/${id}/check/`,
  healthEndpointHistory: (id: string) => `/api/sre/health-endpoints/${id}/history/`,
  healthCheckResults: '/api/sre/health-check-results/',
  slos: '/api/sre/slos/',
  sloDetail: (id: string) => `/api/sre/slos/${id}/`,
  sloMetrics: (id: string) => `/api/sre/slos/${id}/metrics/`,
  sloErrorBudget: (id: string) => `/api/sre/slos/${id}/error_budget/`,
  sloMetricsList: '/api/sre/slo-metrics/',
  selfHealingRules: '/api/sre/self-healing-rules/',
  selfHealingRuleDetail: (id: string) => `/api/sre/self-healing-rules/${id}/`,
  selfHealingRuleTest: (id: string) => `/api/sre/self-healing-rules/${id}/test/`,
  selfHealingRuleExecute: (id: string) => `/api/sre/self-healing-rules/${id}/execute/`,
  selfHealingExecutions: '/api/sre/self-healing-executions/',
  selfHealingExecutionDetail: (id: string) => `/api/sre/self-healing-executions/${id}/`,
  selfHealingExecutionApprove: (id: string) => `/api/sre/self-healing-executions/${id}/approve/`,
  runbooks: '/api/sre/runbooks/',
  runbookDetail: (id: string) => `/api/sre/runbooks/${id}/`,
  runbookExecute: (id: string) => `/api/sre/runbooks/${id}/execute/`,
  runbookExecutions: '/api/sre/runbook-executions/',
  runbookExecutionDetail: (id: string) => `/api/sre/runbook-executions/${id}/`,
  runbookExecutionStepComplete: (id: string) => `/api/sre/runbook-executions/${id}/step_complete/`,
  reportsOverview: '/api/sre/reports/overview/',
  reportsSLOStatus: '/api/sre/reports/slo_status/',
  reportsHealingActivity: '/api/sre/reports/healing_activity/',
} as const;

// Monitoring Platform Types
export type PlatformType = 'prometheus' | 'datadog' | 'azure_monitor' | 'newrelic';

export interface MonitoringPlatform {
  id: string;
  name: string;
  platform_type: PlatformType;
  connection_config: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Health Endpoint Types
export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy';

export interface HealthEndpoint {
  id: string;
  name: string;
  application: string | null;
  application_name: string | null;
  url: string;
  method: string;
  expected_status: number;
  timeout_seconds: number;
  check_interval_minutes: number;
  is_active: boolean;
  last_check_status: string;
  created_at: string;
  updated_at: string;
}

export interface HealthCheckResult {
  id: string;
  endpoint: string;
  endpoint_name: string;
  endpoint_url: string;
  check_time: string;
  status: HealthStatus;
  response_time_ms: number | null;
  status_code: number | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

// SLO Types
export type SLOType = 'availability' | 'latency' | 'error_rate' | 'throughput';
export type MeasurementWindow = 'hourly' | 'daily' | 'weekly' | 'monthly';

export interface SLODefinition {
  id: string;
  name: string;
  service_name: string;
  slo_type: SLOType;
  target_value: number;
  target_unit: string;
  measurement_window: MeasurementWindow;
  error_budget_policy: Record<string, unknown> | null;
  is_active: boolean;
  metric_count: number;
  current_compliance: number;
  created_at: string;
  updated_at: string;
}

export interface SLOMetric {
  id: string;
  slo: string;
  slo_name: string;
  service_name: string;
  measurement_time: string;
  actual_value: number;
  target_met: boolean;
  error_budget_remaining: number | null;
  burn_rate: number | null;
  created_at: string;
  updated_at: string;
}

// Self-Healing Types
export type TriggerType = 'threshold' | 'pattern' | 'schedule' | 'alert';
export type TargetType = 'service' | 'process' | 'disk' | 'connection';
export type ScriptType = 'powershell' | 'bash' | 'python';
export type ExecutionStatus = 'pending' | 'approved' | 'executing' | 'completed' | 'failed';

export interface SelfHealingRule {
  id: string;
  name: string;
  description: string;
  trigger_type: TriggerType;
  trigger_config: Record<string, unknown>;
  target_type: TargetType;
  target_config: Record<string, unknown>;
  remediation_script: string;
  script_type: ScriptType;
  risk_level: RiskLevel;
  requires_approval: boolean;
  max_executions_per_hour: number;
  cooldown_minutes: number;
  is_active: boolean;
  execution_count: number;
  created_at: string;
  updated_at: string;
}

export interface SelfHealingExecution {
  id: string;
  correlation_id: string;
  rule: string;
  rule_name: string;
  trigger_event: Record<string, unknown>;
  status: ExecutionStatus;
  approved_by: string | null;
  approved_by_name: string | null;
  started_at: string | null;
  completed_at: string | null;
  output: string | null;
  error_message: string | null;
  metrics_before: Record<string, unknown> | null;
  metrics_after: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

// Runbook Types
export type AutomationLevel = 'manual' | 'semi_auto' | 'full_auto';
export type RiskLevel = 'R1' | 'R2' | 'R3';
export type RunbookExecutionStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled';

export interface Runbook {
  id: string;
  name: string;
  description: string;
  category: string;
  steps: Array<Record<string, unknown>>;
  automation_level: AutomationLevel;
  risk_level: RiskLevel;
  estimated_duration_minutes: number;
  is_active: boolean;
  execution_count: number;
  step_count: number;
  created_at: string;
  updated_at: string;
}

export interface RunbookExecution {
  id: string;
  correlation_id: string;
  runbook: string;
  runbook_name: string;
  executed_by: string | null;
  executed_by_name: string | null;
  trigger_reason: string;
  status: RunbookExecutionStatus;
  current_step: number;
  step_results: Array<Record<string, unknown>>;
  started_at: string | null;
  completed_at: string | null;
  evidence: Array<Record<string, unknown>>;
  created_at: string;
  updated_at: string;
}

// Report Types
export interface SREOverview {
  healthy_endpoints: number;
  unhealthy_endpoints: number;
  active_slos: number;
  compliant_slos: number;
  active_healing_rules: number;
  recent_executions: number;
}

export interface SLOStatus {
  slo_status: Array<{
    slo_id: string;
    name: string;
    service_name: string;
    slo_type: SLOType;
    target_value: number;
    current_value: number | null;
    target_met: boolean | null;
    error_budget_remaining: number | null;
  }>;
}

export interface HealingActivity {
  total_executions: number;
  successful: number;
  failed: number;
  pending: number;
  success_rate: number;
}

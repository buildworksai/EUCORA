// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * E15: IAM Security Agent - Type Contracts
 */

// API Endpoints
export const ENDPOINTS = {
  providers: '/api/iam-security/providers/',
  providerDetail: (id: string) => `/api/iam-security/providers/${id}/`,
  providerTest: (id: string) => `/api/iam-security/providers/${id}/test/`,
  providerSync: (id: string) => `/api/iam-security/providers/${id}/sync/`,
  signIns: '/api/iam-security/sign-ins/',
  permissionChanges: '/api/iam-security/permission-changes/',
  anomalies: '/api/iam-security/anomalies/',
  anomalyDetail: (id: string) => `/api/iam-security/anomalies/${id}/`,
  anomalyInvestigate: (id: string) => `/api/iam-security/anomalies/${id}/investigate/`,
  anomalyResolve: (id: string) => `/api/iam-security/anomalies/${id}/resolve/`,
  anomalyFalsePositive: (id: string) => `/api/iam-security/anomalies/${id}/false-positive/`,
  rules: '/api/iam-security/rules/',
  ruleDetail: (id: string) => `/api/iam-security/rules/${id}/`,
  ruleTest: (id: string) => `/api/iam-security/rules/${id}/test/`,
  alerts: '/api/iam-security/alerts/',
  disableAccount: '/api/iam-security/actions/disable-account/',
  revokePermissions: '/api/iam-security/actions/revoke-permissions/',
  forcePasswordReset: '/api/iam-security/actions/force-password-reset/',
  reportsSummary: '/api/iam-security/reports/summary/',
  reportsTrends: '/api/iam-security/reports/trends/',
} as const;

// Provider Types
export type ProviderType = 'entra_id' | 'okta' | 'ad' | 'servicenow';

export interface IdentityProvider {
  id: string;
  name: string;
  provider_type: ProviderType;
  tenant_id: string | null;
  connection_config: Record<string, unknown>;
  sync_interval_minutes: number;
  last_sync: string | null;
  is_active: boolean;
  sign_in_count: number;
  anomaly_count: number;
  created_at: string;
  updated_at: string;
}

// Event Types
export type SignInStatus = 'success' | 'failure';

export interface SignInEvent {
  id: string;
  provider: string;
  provider_name: string;
  event_id: string;
  user_principal: string;
  user_display_name: string;
  app_display_name: string | null;
  client_ip: string | null;
  location: Record<string, unknown> | null;
  device_detail: Record<string, unknown> | null;
  status: SignInStatus;
  failure_reason: string | null;
  risk_level: string | null;
  event_time: string;
  created_at: string;
}

// Anomaly Types
export type AnomalyType =
  | 'suspicious_login'
  | 'authentication_attack'
  | 'unusual_activity'
  | 'new_device'
  | 'privilege_change'
  | 'dormant_activation'
  | 'service_account_abuse';

export type AnomalySeverity = 'low' | 'medium' | 'high' | 'critical';
export type AnomalyStatus = 'new' | 'investigating' | 'resolved' | 'false_positive';

export interface AnomalyDetection {
  id: string;
  correlation_id: string;
  provider: string;
  provider_name: string;
  anomaly_type: AnomalyType;
  severity: AnomalySeverity;
  user_principal: string;
  description: string;
  evidence: Record<string, unknown>;
  related_events: string[];
  detection_rule: string;
  status: AnomalyStatus;
  assigned_to: string | null;
  assigned_to_username: string | null;
  resolved_at: string | null;
  resolution_notes: string | null;
  alert_count: number;
  created_at: string;
  updated_at: string;
}

// Detection Rule Types
export interface DetectionRule {
  id: string;
  name: string;
  description: string;
  anomaly_type: AnomalyType;
  severity: AnomalySeverity;
  rule_config: Record<string, unknown>;
  threshold_config: Record<string, unknown>;
  is_active: boolean;
  last_triggered: string | null;
  trigger_count: number;
  created_at: string;
  updated_at: string;
}

// Summary Types
export interface SecuritySummary {
  total_anomalies: number;
  critical: number;
  high: number;
  new: number;
}

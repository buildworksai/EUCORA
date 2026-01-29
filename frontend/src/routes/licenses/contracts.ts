// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * License Management types and API endpoints.
 *
 * This module defines the contract between the frontend and the Django backend
 * license_management app. All types mirror the backend serializers.
 */

// ============================================================================
// ENUMS & CONSTANTS
// ============================================================================

export const LicenseModelType = {
  DEVICE: 'device',
  USER: 'user',
  CONCURRENT: 'concurrent',
  SUBSCRIPTION: 'subscription',
  FEATURE: 'feature',
  CORE: 'core',
  INSTANCE: 'instance',
} as const;
export type LicenseModelType = typeof LicenseModelType[keyof typeof LicenseModelType];

export const EntitlementStatus = {
  ACTIVE: 'active',
  EXPIRED: 'expired',
  PENDING: 'pending',
  SUSPENDED: 'suspended',
  TERMINATED: 'terminated',
} as const;
export type EntitlementStatus = typeof EntitlementStatus[keyof typeof EntitlementStatus];

export const AssignmentStatus = {
  ACTIVE: 'active',
  REVOKED: 'revoked',
  EXPIRED: 'expired',
  PENDING: 'pending',
} as const;
export type AssignmentStatus = typeof AssignmentStatus[keyof typeof AssignmentStatus];

export const AlertSeverity = {
  INFO: 'info',
  WARNING: 'warning',
  CRITICAL: 'critical',
} as const;
export type AlertSeverity = typeof AlertSeverity[keyof typeof AlertSeverity];

export const AlertType = {
  OVERCONSUMPTION: 'overconsumption',
  EXPIRING: 'expiring',
  SPIKE: 'spike',
  UNDERUTILIZED: 'underutilized',
  RECONCILIATION_FAILED: 'reconciliation_failed',
  STALE_DATA: 'stale_data',
} as const;
export type AlertType = typeof AlertType[keyof typeof AlertType];

export const ReconciliationStatus = {
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
} as const;
export type ReconciliationStatus = typeof ReconciliationStatus[keyof typeof ReconciliationStatus];

export const HealthStatus = {
  OK: 'ok',
  DEGRADED: 'degraded',
  FAILED: 'failed',
  STALE: 'stale',
} as const;
export type HealthStatus = typeof HealthStatus[keyof typeof HealthStatus];

export const PrincipalType = {
  USER: 'user',
  DEVICE: 'device',
  SERVICE: 'service',
} as const;
export type PrincipalType = typeof PrincipalType[keyof typeof PrincipalType];

// ============================================================================
// TYPES - SUMMARY
// ============================================================================

/**
 * License summary with health status.
 * Used for sidebar widget and dashboard overview.
 */
export interface LicenseSummary {
  total_entitled: number;
  total_consumed: number;
  total_remaining: number;
  last_reconciled_at: string | null;
  health_status: HealthStatus;
  health_message: string | null;
  stale_duration_seconds: number | null;
  vendor_count: number;
  sku_count: number;
  active_alerts_count: number;
}

// ============================================================================
// TYPES - VENDOR
// ============================================================================

export interface Vendor {
  id: string;
  name: string;
  identifier: string;
  website: string;
  support_contact: string;
  notes: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface VendorListItem {
  id: string;
  name: string;
  identifier: string;
  is_active: boolean;
  sku_count: number;
}

// ============================================================================
// TYPES - SKU
// ============================================================================

export interface LicenseSKU {
  id: string;
  vendor: string;
  vendor_name: string;
  sku_code: string;
  name: string;
  description: string;
  license_model_type: LicenseModelType;
  unit_rules: Record<string, unknown>;
  normalization_rules: Record<string, unknown>;
  is_active: boolean;
  requires_approval: boolean;
  cost_per_unit: string | null;
  currency: string;
  created_at: string;
  updated_at: string;
}

export interface LicenseSKUListItem {
  id: string;
  vendor_name: string;
  sku_code: string;
  name: string;
  license_model_type: LicenseModelType;
  is_active: boolean;
  entitled: number;
  consumed: number;
  remaining: number;
}

// ============================================================================
// TYPES - ENTITLEMENT
// ============================================================================

export interface Entitlement {
  id: string;
  sku: string;
  sku_name: string;
  vendor_name: string;
  contract_id: string;
  entitled_quantity: number;
  start_date: string;
  end_date: string | null;
  renewal_date: string | null;
  terms: Record<string, unknown>;
  document_refs: string[];
  status: EntitlementStatus;
  notes: string;
  created_by: string | null;
  created_by_username: string | null;
  approved_by: string | null;
  approved_by_username: string | null;
  approved_at: string | null;
  correlation_id: string;
  is_expired: boolean;
  days_until_expiry: number | null;
  created_at: string;
  updated_at: string;
}

export interface EntitlementCreate {
  sku: string;
  contract_id: string;
  entitled_quantity: number;
  start_date: string;
  end_date?: string | null;
  renewal_date?: string | null;
  terms?: Record<string, unknown>;
  notes?: string;
}

// ============================================================================
// TYPES - POOL
// ============================================================================

export interface LicensePool {
  id: string;
  sku: string;
  sku_name: string;
  name: string;
  description: string;
  scope_type: 'global' | 'region' | 'bu' | 'department' | 'site';
  scope_value: string;
  entitled_quantity_override: number | null;
  reserved_quantity: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// TYPES - ASSIGNMENT
// ============================================================================

export interface Assignment {
  id: string;
  pool: string;
  pool_name: string;
  sku_name: string;
  principal_type: PrincipalType;
  principal_id: string;
  principal_name: string;
  assigned_at: string;
  expires_at: string | null;
  status: AssignmentStatus;
  assigned_by: string | null;
  assigned_by_username: string | null;
  revoked_by: string | null;
  revoked_at: string | null;
  revocation_reason: string;
  created_at: string;
  updated_at: string;
}

export interface AssignmentCreate {
  pool: string;
  principal_type: PrincipalType;
  principal_id: string;
  principal_name?: string;
  expires_at?: string | null;
}

// ============================================================================
// TYPES - CONSUMPTION
// ============================================================================

export interface ConsumptionSnapshot {
  id: string;
  sku: string;
  sku_name: string;
  pool: string | null;
  pool_name: string | null;
  reconciled_at: string;
  ruleset_version: string;
  entitled: number;
  consumed: number;
  reserved: number;
  remaining: number;
  utilization_percent: string;
  evidence_pack_hash: string;
  evidence_pack_ref: string;
  reconciliation_run: string | null;
}

export interface ConsumptionSignal {
  id: string;
  source_system: string;
  raw_id: string;
  timestamp: string;
  principal_type: PrincipalType;
  principal_id: string;
  principal_name: string;
  sku: string;
  sku_name: string;
  confidence: number;
  raw_payload_hash: string;
  is_processed: boolean;
  processed_at: string | null;
  created_at: string;
}

// ============================================================================
// TYPES - RECONCILIATION
// ============================================================================

export interface ReconciliationRun {
  id: string;
  status: ReconciliationStatus;
  ruleset_version: string;
  started_at: string;
  completed_at: string | null;
  skus_total: number;
  skus_processed: number;
  snapshots_created: number;
  signals_processed: number;
  errors: Array<{ message: string; sku?: string; timestamp?: string }>;
  diff_summary: Record<string, unknown>;
  triggered_by: string | null;
  triggered_by_username: string | null;
  trigger_type: 'manual' | 'scheduled' | 'signal';
  duration_seconds: number | null;
  progress_percent: number;
  correlation_id: string;
}

// ============================================================================
// TYPES - ALERTS
// ============================================================================

export interface LicenseAlert {
  id: string;
  sku: string;
  sku_name: string;
  pool: string | null;
  pool_name: string | null;
  alert_type: AlertType;
  severity: AlertSeverity;
  message: string;
  details: Record<string, unknown>;
  detected_at: string;
  acknowledged: boolean;
  acknowledged_by: string | null;
  acknowledged_by_username: string | null;
  acknowledged_at: string | null;
  resolution_notes: string;
  auto_resolved: boolean;
  resolved_at: string | null;
}

// ============================================================================
// TYPES - IMPORT
// ============================================================================

export interface ImportJob {
  id: string;
  import_type: 'entitlements' | 'vendors' | 'skus' | 'assignments';
  status: 'pending' | 'validating' | 'importing' | 'completed' | 'failed';
  file_name: string;
  file_hash: string;
  file_ref: string;
  total_rows: number;
  processed_rows: number;
  success_count: number;
  error_count: number;
  validation_errors: Array<{ row: number; field: string; message: string }>;
  import_errors: Array<{ row: number; message: string }>;
  started_at: string | null;
  completed_at: string | null;
  uploaded_by: string | null;
  uploaded_by_username: string | null;
  correlation_id: string;
  created_at: string;
}

// ============================================================================
// TYPES - PAGINATED RESPONSES
// ============================================================================

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// ============================================================================
// API ENDPOINTS
// ============================================================================

/**
 * All license management API endpoints.
 * Never hardcode URLs - always use these constants.
 */
export const ENDPOINTS = {
  // Summary
  SUMMARY: '/licenses/summary/',

  // Vendors
  VENDORS: '/licenses/vendors/',
  VENDOR: (id: string) => `/licenses/vendors/${id}/`,

  // SKUs
  SKUS: '/licenses/skus/',
  SKU: (id: string) => `/licenses/skus/${id}/`,
  SKU_CONSUMPTION: (id: string) => `/licenses/skus/${id}/consumption/`,

  // Entitlements
  ENTITLEMENTS: '/licenses/entitlements/',
  ENTITLEMENT: (id: string) => `/licenses/entitlements/${id}/`,
  ENTITLEMENT_APPROVE: (id: string) => `/licenses/entitlements/${id}/approve/`,

  // Pools
  POOLS: '/licenses/pools/',
  POOL: (id: string) => `/licenses/pools/${id}/`,

  // Assignments
  ASSIGNMENTS: '/licenses/assignments/',
  ASSIGNMENT: (id: string) => `/licenses/assignments/${id}/`,
  ASSIGNMENT_REVOKE: (id: string) => `/licenses/assignments/${id}/revoke/`,

  // Consumption
  SNAPSHOTS: '/licenses/snapshots/',
  SNAPSHOT: (id: string) => `/licenses/snapshots/${id}/`,
  SNAPSHOT_EVIDENCE: (id: string) => `/licenses/snapshots/${id}/evidence/`,
  SIGNALS: '/licenses/signals/',
  INGEST_SIGNAL: '/licenses/ingest/',

  // Reconciliation
  RECONCILIATION_RUNS: '/licenses/reconciliation-runs/',
  RECONCILE: '/licenses/reconcile/',

  // Alerts
  ALERTS: '/licenses/alerts/',
  ALERT: (id: string) => `/licenses/alerts/${id}/`,
  ALERT_ACKNOWLEDGE: (id: string) => `/licenses/alerts/${id}/acknowledge/`,

  // Import
  IMPORT_JOBS: '/licenses/imports/',
  IMPORT_JOB: (id: string) => `/licenses/imports/${id}/`,
} as const;

// ============================================================================
// QUERY FILTERS
// ============================================================================

export interface VendorFilters {
  is_active?: boolean;
}

export interface SKUFilters {
  vendor?: string;
  is_active?: boolean;
  license_model_type?: LicenseModelType;
}

export interface EntitlementFilters {
  sku?: string;
  status?: EntitlementStatus;
}

export interface AssignmentFilters {
  pool?: string;
  status?: AssignmentStatus;
  principal_type?: PrincipalType;
  principal_id?: string;
}

export interface AlertFilters {
  severity?: AlertSeverity;
  alert_type?: AlertType;
  acknowledged?: boolean;
  sku?: string;
}

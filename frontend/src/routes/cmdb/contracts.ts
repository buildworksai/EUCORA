// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * E10: CMDB Integration Agent - Type Contracts
 */

// API Endpoints
export const ENDPOINTS = {
  connections: '/api/cmdb/connections/',
  connectionDetail: (id: string) => `/api/cmdb/connections/${id}/`,
  connectionTest: (id: string) => `/api/cmdb/connections/${id}/test/`,
  mappings: '/api/cmdb/mappings/',
  mappingDetail: (id: string) => `/api/cmdb/mappings/${id}/`,
  validationRules: '/api/cmdb/validation-rules/',
  validationRuleDetail: (id: string) => `/api/cmdb/validation-rules/${id}/`,
  syncRecords: '/api/cmdb/sync/',
  syncStart: (connectionId: string) => `/api/cmdb/connections/${connectionId}/start_sync/`,
  discrepancies: '/api/cmdb/discrepancies/',
  discrepancyDetail: (id: string) => `/api/cmdb/discrepancies/${id}/`,
  discrepancyApprove: (id: string) => `/api/cmdb/discrepancies/${id}/approve/`,
  discrepancyReject: (id: string) => `/api/cmdb/discrepancies/${id}/reject/`,
  reports: '/api/cmdb/reports/',
  qualityScore: '/api/cmdb/reports/quality_score/',
  syncHistory: '/api/cmdb/reports/sync_history/',
} as const;

// Connection Types
export type CMDBConnectionAuthType = 'basic' | 'oauth' | 'api_key';

export interface CMDBConnection {
  id: string;
  name: string;
  instance_url: string;
  auth_type: CMDBConnectionAuthType;
  is_active: boolean;
  test_status: 'pending' | 'success' | 'failed';
  test_message: string;
  last_sync: string | null;
  last_sync_status: string | null;
  created_at: string;
  updated_at: string;
}

export interface CMDBConnectionCreate {
  name: string;
  instance_url: string;
  auth_type: CMDBConnectionAuthType;
  credentials: Record<string, string>;
}

// Table Mapping Types
export type SyncDirection = 'source_to_cmdb' | 'cmdb_to_source' | 'bidirectional';

export interface CMDBTableMapping {
  id: string;
  connection: string;
  connection_name: string;
  source_table: string;
  cmdb_table: string;
  field_mappings: Record<string, string>;
  sync_direction: SyncDirection;
  is_active: boolean;
  created_at: string;
}

// Validation Rule Types
export type ValidationRuleType = 'required' | 'format' | 'regex' | 'range' | 'reference' | 'custom';
export type ValidationSeverity = 'error' | 'warning' | 'info';

export interface CMDBValidationRule {
  id: string;
  name: string;
  description: string;
  table_name: string;
  field_name: string;
  rule_type: ValidationRuleType;
  rule_config: Record<string, unknown>;
  severity: ValidationSeverity;
  is_active: boolean;
  created_at: string;
}

// Sync Record Types
export type SyncStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface CMDBSyncRecord {
  id: string;
  correlation_id: string;
  connection: string;
  connection_name: string;
  sync_type: 'full' | 'incremental' | 'validation_only';
  status: SyncStatus;
  started_at: string | null;
  completed_at: string | null;
  records_processed: number;
  records_created: number;
  records_updated: number;
  records_failed: number;
  errors: string[];
  initiated_by: string | null;
  initiated_by_username: string | null;
}

// Discrepancy Types
export type DiscrepancyType = 'missing' | 'mismatch' | 'orphan' | 'duplicate' | 'stale' | 'incomplete';
export type DiscrepancyStatus = 'open' | 'approved' | 'rejected' | 'auto_resolved' | 'ignored';

export interface CMDBDiscrepancy {
  id: string;
  correlation_id: string;
  sync_record: string;
  discrepancy_type: DiscrepancyType;
  table_name: string;
  source_record_id: string | null;
  cmdb_sys_id: string | null;
  field_name: string | null;
  source_value: string | null;
  cmdb_value: string | null;
  recommended_action: string;
  status: DiscrepancyStatus;
  resolved_at: string | null;
  resolved_by: string | null;
  resolved_by_username: string | null;
  resolution_notes: string;
  created_at: string;
}

// Report Types
export interface CMDBQualityScore {
  overall_score: number;
  completeness: number;
  accuracy: number;
  consistency: number;
  timeliness: number;
  records_analyzed: number;
  issues_found: number;
  calculated_at: string;
}

export interface CMDBSyncHistory {
  date: string;
  sync_count: number;
  records_processed: number;
  success_rate: number;
}

// Dashboard Types
export interface CMDBDashboardData {
  connections: {
    total: number;
    active: number;
    healthy: number;
  };
  sync: {
    last_sync: string | null;
    total_syncs: number;
    success_rate: number;
  };
  discrepancies: {
    open: number;
    by_type: Record<DiscrepancyType, number>;
  };
  quality: CMDBQualityScore;
}

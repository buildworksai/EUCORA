// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * E14: Discovery Agent - Type Contracts
 */

// API Endpoints
export const ENDPOINTS = {
  sources: '/api/discovery/sources/',
  sourceDetail: (id: string) => `/api/discovery/sources/${id}/`,
  sourceSync: (id: string) => `/api/discovery/sources/${id}/sync/`,
  runs: '/api/discovery/runs/',
  runDetail: (id: string) => `/api/discovery/runs/${id}/`,
  runApplications: (id: string) => `/api/discovery/runs/${id}/applications/`,
  applications: '/api/discovery/applications/',
  applicationDetail: (id: string) => `/api/discovery/applications/${id}/`,
  applicationApprove: (id: string) => `/api/discovery/applications/${id}/approve/`,
  applicationRestrict: (id: string) => `/api/discovery/applications/${id}/restrict/`,
  applicationsMerge: '/api/discovery/applications/merge/',
  licenseGaps: '/api/discovery/license-gaps/',
  licenseGapDetail: (id: string) => `/api/discovery/license-gaps/${id}/`,
  licenseGapAcknowledge: (id: string) => `/api/discovery/license-gaps/${id}/acknowledge/`,
  licenseGapResolve: (id: string) => `/api/discovery/license-gaps/${id}/resolve/`,
  patchGaps: '/api/discovery/patch-gaps/',
  patchGapDetail: (id: string) => `/api/discovery/patch-gaps/${id}/`,
  patchGapPlan: (id: string) => `/api/discovery/patch-gaps/${id}/plan/`,
  reports: '/api/discovery/reports/',
  reportGenerate: '/api/discovery/reports/generate/',
  reportExport: (id: string) => `/api/discovery/reports/${id}/export/`,
  dashboard: '/api/discovery/dashboard/',
} as const;

// Discovery Source Types
export type DiscoverySourceType = 'sccm' | 'intune' | 'ad' | 'cmdb' | 'spreadsheet' | 'network_scan';
export type SyncSchedule = 'manual' | 'hourly' | 'daily' | 'weekly';

export interface DiscoverySource {
  id: string;
  name: string;
  source_type: DiscoverySourceType;
  connection_config: Record<string, unknown>;
  sync_schedule: SyncSchedule;
  last_sync: string | null;
  last_sync_status: 'success' | 'failed' | null;
  is_active: boolean;
  include_patterns: string[];
  exclude_patterns: string[];
  run_count: number;
  created_at: string;
  updated_at: string;
}

// Discovery Run Types
export type RunType = 'full' | 'incremental' | 'validation';
export type RunStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface DiscoveryRun {
  id: string;
  correlation_id: string;
  source: string;
  source_name: string;
  run_type: RunType;
  status: RunStatus;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
  records_discovered: number;
  records_new: number;
  records_updated: number;
  records_normalized: number;
  normalization_failures: number;
  errors: string[];
  initiated_by: string | null;
  initiated_by_username: string | null;
  created_at: string;
}

// Normalized Application Types
export type ApplicationType = 'desktop' | 'web' | 'mobile' | 'service' | 'driver' | 'other';

export interface NormalizedApplication {
  id: string;
  name: string;
  publisher: string;
  category: string | null;
  application_type: ApplicationType;
  is_managed: boolean;
  is_approved: boolean;
  is_restricted: boolean;
  portfolio_app: string | null;
  license_sku: string | null;
  fingerprint: string;
  total_installs: number;
  first_discovered: string | null;
  last_discovered: string | null;
  version_count: number;
  discovered_count: number;
  license_gap_count: number;
  patch_gap_count: number;
  latest_version: string | null;
  created_at: string;
  updated_at: string;
}

// Application Version Types
export interface ApplicationVersion {
  id: string;
  application: string;
  version: string;
  version_major: number | null;
  version_minor: number | null;
  version_patch: number | null;
  release_date: string | null;
  end_of_life: string | null;
  has_security_updates: boolean;
  is_current: boolean;
  install_count: number;
  first_seen: string | null;
  last_seen: string | null;
  created_at: string;
}

// License Gap Types
export type LicenseGapType = 'missing_license' | 'over_deployment' | 'under_licensed' | 'expired';
export type RiskLevel = 'critical' | 'high' | 'medium' | 'low';
export type GapStatus = 'open' | 'acknowledged' | 'resolved' | 'exception';

export interface LicenseGap {
  id: string;
  correlation_id: string;
  application: string;
  application_name: string;
  application_publisher: string;
  gap_type: LicenseGapType;
  detected_installs: number;
  licensed_count: number;
  gap_count: number;
  risk_level: RiskLevel;
  estimated_cost: number | null;
  status: GapStatus;
  resolved_at: string | null;
  resolved_by: string | null;
  resolved_by_username: string | null;
  resolution_notes: string;
  created_at: string;
}

// Patch Gap Types
export type PatchGapType = 'security_patch' | 'major_upgrade' | 'eol_version' | 'minor_update';
export type PatchSeverity = 'critical' | 'high' | 'medium' | 'low';
export type PatchGapStatus = 'open' | 'planned' | 'in_progress' | 'resolved' | 'exception';

export interface PatchGap {
  id: string;
  correlation_id: string;
  application: string;
  application_name: string;
  current_version: string;
  current_version_str: string;
  target_version: string | null;
  target_version_str: string | null;
  affected_devices: number;
  gap_type: PatchGapType;
  severity: PatchSeverity;
  cve_ids: string[];
  status: PatchGapStatus;
  planned_date: string | null;
  created_at: string;
}

// Report Types
export type ReportType =
  | 'inventory'
  | 'shadow_it'
  | 'license_compliance'
  | 'patch_compliance'
  | 'risk_assessment';

export interface DiscoveryReport {
  id: string;
  correlation_id: string;
  report_type: ReportType;
  title: string;
  description: string;
  summary: Record<string, unknown>;
  details: Record<string, unknown>;
  generated_by: string | null;
  generated_by_username: string | null;
  generated_at: string;
  sources_included: string[];
  date_range_start: string | null;
  date_range_end: string | null;
  created_at: string;
}

// Dashboard Types
export interface DiscoveryDashboardData {
  total_applications: number;
  managed_applications: number;
  unmanaged_applications: number;
  shadow_it_count: number;
  license_gaps_count: number;
  patch_gaps_count: number;
  total_installs: number;
  last_discovery: string | null;
  applications_by_category: Record<string, number>;
  risk_distribution: Record<string, number>;
}

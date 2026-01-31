// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * E20: Planning Agent - Type Contracts
 */

// API Endpoints
export const ENDPOINTS = {
  plans: '/api/planning/plans/',
  planDetail: (id: string) => `/api/planning/plans/${id}/`,
  planApprove: (id: string) => `/api/planning/plans/${id}/approve/`,
  planExecute: (id: string) => `/api/planning/plans/${id}/execute/`,
  rings: '/api/planning/rings/',
  ringDetail: (id: string) => `/api/planning/rings/${id}/`,
  devices: '/api/planning/devices/',
  deviceDetail: (id: string) => `/api/planning/devices/${id}/`,
  windows: '/api/planning/windows/',
  windowDetail: (id: string) => `/api/planning/windows/${id}/`,
  freezes: '/api/planning/freezes/',
  freezeDetail: (id: string) => `/api/planning/freezes/${id}/`,
  blastRadius: '/api/planning/blast-radius/',
  blastRadiusDetail: (id: string) => `/api/planning/blast-radius/${id}/`,
  rollback: '/api/planning/rollback/',
  rollbackDetail: (id: string) => `/api/planning/rollback/${id}/`,
  generate: '/api/planning/generate/generate/',
  reportsSummary: '/api/planning/reports/summary/',
} as const;

// Plan Status Types
export type PlanStatus = 'draft' | 'pending_approval' | 'approved' | 'executing' | 'completed' | 'cancelled';

export interface DeploymentPlan {
  id: string;
  correlation_id: string;
  name: string;
  application: string;
  application_name: string;
  version: string;
  target_scope: Record<string, unknown>;
  status: PlanStatus;
  input_request: string;
  reasoning: string;
  overall_risk_score: number;
  risk_factors: Record<string, unknown>;
  created_by: string;
  created_by_name: string;
  approved_by: string | null;
  approved_by_name: string | null;
  approved_at: string | null;
  ring_count: number;
  total_devices: number;
  created_at: string;
  updated_at: string;
}

export type RingStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'paused';

export interface RingAssignment {
  id: string;
  plan: string;
  plan_name: string;
  ring_number: number;
  ring_name: string;
  device_count: number;
  device_count_actual: number;
  device_criteria: Record<string, unknown>;
  scheduled_start: string;
  scheduled_end: string;
  success_threshold: number;
  status: RingStatus;
  created_at: string;
  updated_at: string;
}

export type DeviceCriticality = 'vip' | 'standard' | 'low';

export interface RingDevice {
  id: string;
  ring: string;
  ring_name: string;
  device_id: string;
  device_name: string;
  user_principal: string | null;
  selection_reason: string;
  health_score: number | null;
  criticality: DeviceCriticality;
  created_at: string;
  updated_at: string;
}

export interface DeploymentWindow {
  id: string;
  name: string;
  description: string;
  day_of_week: number[];
  start_time: string;
  end_time: string;
  timezone: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ChangeFreezePeriod {
  id: string;
  name: string;
  reason: string;
  start_date: string;
  end_date: string;
  scope: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface BlastRadiusAnalysis {
  id: string;
  correlation_id: string;
  plan: string;
  plan_name: string;
  total_users_affected: number;
  vip_users_affected: number;
  departments_affected: string[];
  regions_affected: string[];
  critical_systems_affected: string[];
  productivity_impact_score: number;
  recommendations: string[];
  created_at: string;
  updated_at: string;
}

export interface RollbackPlan {
  id: string;
  deployment_plan: string;
  deployment_plan_name: string;
  trigger_conditions: string[];
  rollback_steps: Array<{
    ring: string;
    action: string;
    estimated_minutes: number;
  }>;
  estimated_duration_minutes: number;
  requires_cab_approval: boolean;
  tested: boolean;
  tested_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PlanningSummaryReport {
  total_plans: number;
  active_plans: number;
  approved_plans: number;
  completed_plans: number;
}

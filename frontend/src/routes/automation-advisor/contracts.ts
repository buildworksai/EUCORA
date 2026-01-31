// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * E13: Automation Advisor Agent - Type Contracts
 */

// API Endpoints
export const ENDPOINTS = {
  analyze: '/api/automation-advisor/analyze/',
  analyses: '/api/automation-advisor/analyses/',
  analysisDetail: (id: string) => `/api/automation-advisor/analyses/${id}/`,
  patterns: '/api/automation-advisor/patterns/',
  patternDetail: (id: string) => `/api/automation-advisor/patterns/${id}/`,
  candidates: '/api/automation-advisor/candidates/',
  candidateDetail: (id: string) => `/api/automation-advisor/candidates/${id}/`,
  candidateReview: (id: string) => `/api/automation-advisor/candidates/${id}/review/`,
  candidateApprove: (id: string) => `/api/automation-advisor/candidates/${id}/approve/`,
  candidateReject: (id: string) => `/api/automation-advisor/candidates/${id}/reject/`,
  roiConfig: '/api/automation-advisor/roi-config/',
  reportsSummary: '/api/automation-advisor/reports/summary/',
} as const;

// Pattern Types
export type PatternType = 'repetitive' | 'manual' | 'error_prone';
export type Source = 'servicenow' | 'eucora' | 'logs';

export interface TaskPattern {
  id: string;
  name: string;
  pattern_type: PatternType;
  source: Source;
  occurrence_count: number;
  avg_duration_minutes: number;
  error_rate: number;
  last_detected: string;
  is_active: boolean;
  candidate_count: number;
  created_at: string;
  updated_at: string;
}

// Candidate Types
export type CandidateStatus = 'identified' | 'reviewed' | 'approved' | 'implemented' | 'rejected';

export interface AutomationCandidate {
  id: string;
  correlation_id: string;
  pattern: string;
  pattern_name: string;
  title: string;
  description: string;
  current_process: string;
  proposed_automation: string;
  frequency_score: number;
  time_impact_score: number;
  error_reduction_score: number;
  complexity_score: number;
  overall_score: number;
  annual_occurrences: number;
  time_saved_per_occurrence: number;
  estimated_annual_savings: number;
  development_cost_estimate: number;
  payback_period_months: number;
  status: CandidateStatus;
  reviewed_by: string | null;
  reviewed_by_username: string | null;
  reviewed_at: string | null;
  implementation_notes: string | null;
  created_at: string;
  updated_at: string;
}

// Analysis Types
export type AnalysisStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface AutomationAnalysis {
  id: string;
  correlation_id: string;
  name: string;
  date_range_start: string;
  date_range_end: string;
  sources_analyzed: string[];
  status: AnalysisStatus;
  started_at: string | null;
  completed_at: string | null;
  patterns_detected: number;
  candidates_generated: number;
  created_at: string;
  updated_at: string;
}

// ROI Configuration Types
export interface ROIConfiguration {
  id: string;
  name: string;
  hourly_labor_cost: number;
  development_hourly_rate: number;
  complexity_multipliers: {
    low: number;
    medium: number;
    high: number;
  };
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

// Summary Types
export interface AutomationSummary {
  total_opportunities: number;
  pending_review: number;
  approved: number;
  implemented: number;
  potential_annual_savings: number;
}

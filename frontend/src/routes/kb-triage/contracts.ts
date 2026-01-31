// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * E21: KB & Triage Agent - Type Contracts
 */

// API Endpoints
export const ENDPOINTS = {
  sources: '/api/kb-triage/sources/',
  sourceDetail: (id: string) => `/api/kb-triage/sources/${id}/`,
  sourceSync: (id: string) => `/api/kb-triage/sources/${id}/sync/`,
  sourceTest: (id: string) => `/api/kb-triage/sources/${id}/test/`,
  articles: '/api/kb-triage/articles/',
  articleSearch: '/api/kb-triage/articles/search/',
  triage: '/api/kb-triage/triage/',
  triageDetail: (id: string) => `/api/kb-triage/triage/${id}/`,
  triageSuggestions: (id: string) => `/api/kb-triage/triage/${id}/suggestions/`,
  triageResolutionSteps: (id: string) => `/api/kb-triage/triage/${id}/resolution-steps/`,
  triageFeedback: (id: string) => `/api/kb-triage/triage/${id}/feedback/`,
  feedback: '/api/kb-triage/feedback/',
  patterns: '/api/kb-triage/patterns/',
  patternDetail: (id: string) => `/api/kb-triage/patterns/${id}/`,
  patternInvestigate: (id: string) => `/api/kb-triage/patterns/${id}/investigate/`,
  patternResolve: (id: string) => `/api/kb-triage/patterns/${id}/resolve/`,
  reportsAccuracy: '/api/kb-triage/reports/accuracy/',
  reportsCategories: '/api/kb-triage/reports/categories/',
  reportsPatterns: '/api/kb-triage/reports/patterns/',
} as const;

// Knowledge Source Types
export type SourceType = 'servicenow_kb' | 'confluence' | 'sharepoint' | 'vendor' | 'custom';

export interface KnowledgeSource {
  id: string;
  name: string;
  source_type: SourceType;
  connection_config: Record<string, unknown>;
  sync_schedule: string;
  last_sync: string | null;
  article_count: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeArticle {
  id: string;
  source: string;
  source_name: string;
  external_id: string;
  title: string;
  content: string;
  category: string | null;
  tags: string[];
  url: string | null;
  author: string | null;
  published_date: string | null;
  last_updated: string | null;
  view_count: number;
  helpful_count: number;
  created_at: string;
  updated_at: string;
}

// Triage Types
export type TriageStatus = 'pending' | 'triaged' | 'escalated' | 'resolved';
export type Priority = '1' | '2' | '3' | '4';

export interface TriageRequest {
  id: string;
  correlation_id: string;
  servicenow_number: string | null;
  caller_name: string;
  caller_email: string | null;
  affected_service: string | null;
  short_description: string;
  description: string;
  symptoms: string[];
  suggested_category: string | null;
  suggested_subcategory: string | null;
  suggested_priority: Priority | null;
  suggested_assignment_group: string | null;
  confidence_score: number | null;
  reasoning: string | null;
  status: TriageStatus;
  triage_time_ms: number | null;
  suggestion_count: number;
  resolution_step_count: number;
  created_at: string;
  updated_at: string;
}

export type SuggestionType = 'article' | 'script' | 'escalation' | 'workaround';

export interface TriageSuggestion {
  id: string;
  triage_request: string;
  suggestion_type: SuggestionType;
  title: string;
  content: string;
  source_article: string | null;
  source_article_title: string | null;
  relevance_score: number;
  was_helpful: boolean | null;
  feedback: string | null;
  created_at: string;
  updated_at: string;
}

export type StepStatus = 'pending' | 'completed' | 'skipped' | 'failed';

export interface ResolutionStep {
  id: string;
  triage_request: string;
  step_number: number;
  instruction: string;
  expected_outcome: string | null;
  script: string | null;
  script_type: string | null;
  requires_approval: boolean;
  status: StepStatus;
  completed_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

// Pattern Types
export type PatternType = 'recurring' | 'trending' | 'correlated';
export type PatternStatus = 'active' | 'investigating' | 'resolved';

export interface IncidentPattern {
  id: string;
  correlation_id: string;
  name: string;
  pattern_type: PatternType;
  description: string;
  category: string;
  occurrence_count: number;
  affected_users: number;
  first_detected: string;
  last_detected: string;
  related_change: string | null;
  status: PatternStatus;
  root_cause: string | null;
  resolution: string | null;
  created_at: string;
  updated_at: string;
}

export type FeedbackType = 'category' | 'priority' | 'assignment' | 'resolution';

export interface TriageFeedback {
  id: string;
  triage_request: string;
  feedback_type: FeedbackType;
  was_accurate: boolean;
  correct_value: string | null;
  comments: string | null;
  submitted_by: string | null;
  submitted_by_name: string | null;
  created_at: string;
  updated_at: string;
}

// Report Types
export interface TriageAccuracy {
  overall_accuracy: number;
  total_feedback: number;
  accurate_feedback: number;
  by_type: Record<FeedbackType, { total: number; accurate: number; accuracy: number }>;
}

export interface CategoryDistribution {
  categories: Array<{ suggested_category: string | null; count: number }>;
}

export interface PatternStatistics {
  active_patterns: number;
  investigating_patterns: number;
  by_type: Record<PatternType, number>;
}

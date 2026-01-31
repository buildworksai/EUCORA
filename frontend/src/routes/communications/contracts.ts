// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * E11: Change Communications Agent - Type Contracts
 */

// API Endpoints
export const ENDPOINTS = {
  changes: '/api/change-communications/changes/',
  changeDetail: (id: string) => `/api/change-communications/changes/${id}/`,
  changeSync: (id: string) => `/api/change-communications/changes/${id}/sync/`,
  changeClose: (id: string) => `/api/change-communications/changes/${id}/close/`,
  changeTimeline: (id: string) => `/api/change-communications/changes/${id}/timeline/`,
  stakeholders: '/api/change-communications/stakeholders/',
  stakeholderDetail: (id: string) => `/api/change-communications/stakeholders/${id}/`,
  templates: '/api/change-communications/templates/',
  templateDetail: (id: string) => `/api/change-communications/templates/${id}/`,
  templatePreview: (id: string) => `/api/change-communications/templates/${id}/preview/`,
  communications: '/api/change-communications/communications/',
  communicationDetail: (id: string) => `/api/change-communications/communications/${id}/`,
  communicationRetry: (id: string) => `/api/change-communications/communications/${id}/retry/`,
  kbArticles: '/api/change-communications/kb-articles/',
  dashboard: '/api/change-communications/dashboard/',
} as const;

// Change Record Types
export type ChangeState =
  | 'draft'
  | 'submitted'
  | 'peer_review'
  | 'cab_review'
  | 'approved'
  | 'scheduled'
  | 'in_progress'
  | 'completed'
  | 'cancelled'
  | 'failed';

export type ChangeType = 'standard' | 'normal' | 'emergency' | 'expedited';
export type ChangePriority = 'critical' | 'high' | 'medium' | 'low';
export type ChangeRiskLevel = 'R1' | 'R2' | 'R3';

export interface ChangeRecord {
  id: string;
  correlation_id: string;
  change_number: string;
  servicenow_sys_id: string | null;
  title: string;
  description: string;
  change_type: ChangeType;
  priority: ChangePriority;
  risk_level: ChangeRiskLevel;
  state: ChangeState;
  requested_by: string | null;
  requested_by_username: string | null;
  assigned_to: string | null;
  assigned_to_username: string | null;
  planned_start: string | null;
  planned_end: string | null;
  actual_start: string | null;
  actual_end: string | null;
  affected_services: string[];
  implementation_plan: string;
  backout_plan: string;
  test_plan: string;
  communications_sent: number;
  kb_articles_linked: number;
  created_at: string;
  updated_at: string;
}

// Stakeholder Group Types
export type NotificationChannel = 'email' | 'teams' | 'slack' | 'servicenow';

export interface StakeholderGroup {
  id: string;
  name: string;
  description: string;
  channel: NotificationChannel;
  channel_config: Record<string, string>;
  member_count: number | null;
  is_active: boolean;
  auto_notify: boolean;
  change_types: ChangeType[];
  priority_threshold: ChangePriority;
  created_at: string;
}

// Communication Template Types
export type TemplateType =
  | 'change_submitted'
  | 'change_approved'
  | 'change_scheduled'
  | 'change_started'
  | 'change_completed'
  | 'change_failed'
  | 'change_cancelled'
  | 'emergency_notification'
  | 'maintenance_window'
  | 'custom';

export interface CommunicationTemplate {
  id: string;
  name: string;
  description: string;
  template_type: TemplateType;
  channel: NotificationChannel;
  subject_template: string;
  body_template: string;
  available_variables: string[];
  is_active: boolean;
  is_default: boolean;
  usage_count: number;
  created_at: string;
}

// Communication Types
export type DeliveryStatus = 'pending' | 'sent' | 'delivered' | 'failed' | 'bounced';

export interface Communication {
  id: string;
  correlation_id: string;
  change: string;
  change_number: string;
  template: string | null;
  template_name: string | null;
  stakeholder_group: string;
  stakeholder_group_name: string;
  channel: NotificationChannel;
  subject: string;
  body: string;
  status: DeliveryStatus;
  sent_at: string | null;
  delivered_at: string | null;
  error_message: string;
  retry_count: number;
  sent_by: string | null;
  sent_by_username: string | null;
  created_at: string;
}

// KB Article Types
export interface KBArticleLink {
  id: string;
  change: string;
  change_number: string;
  article_number: string;
  title: string;
  article_url: string | null;
  article_type: 'troubleshooting' | 'how_to' | 'known_issue' | 'release_notes' | 'faq';
  created_by_agent: boolean;
  created_at: string;
}

// Audit Event Types
export interface ChangeAuditEvent {
  id: string;
  change: string;
  event_type: string;
  details: Record<string, unknown>;
  performed_by: string | null;
  performed_by_username: string | null;
  created_at: string;
}

// Dashboard Types
export interface ChangeDashboardData {
  changes: {
    total: number;
    by_state: Record<ChangeState, number>;
    by_type: Record<ChangeType, number>;
    by_priority: Record<ChangePriority, number>;
  };
  communications: {
    total_sent: number;
    pending: number;
    failed: number;
    success_rate: number;
  };
  kb_articles: {
    total_linked: number;
    agent_created: number;
  };
  recent_changes: ChangeRecord[];
}

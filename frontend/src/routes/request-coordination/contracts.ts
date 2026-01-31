// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * E16: Request Coordination Agent - Type Contracts
 */

// API Endpoints
export const ENDPOINTS = {
  requests: '/api/request-coordination/requests/',
  requestDetail: (id: string) => `/api/request-coordination/requests/${id}/`,
  requestSync: '/api/request-coordination/requests/sync/',
  requestTimeline: (id: string) => `/api/request-coordination/requests/${id}/timeline/`,
  stakeholders: '/api/request-coordination/stakeholders/',
  stakeholderDetail: (id: string) => `/api/request-coordination/stakeholders/${id}/`,
  communications: '/api/request-coordination/communications/',
  communicationSend: '/api/request-coordination/communications/send/',
  escalationRules: '/api/request-coordination/escalation-rules/',
  escalationRuleDetail: (id: string) => `/api/request-coordination/escalation-rules/${id}/`,
  escalations: '/api/request-coordination/escalations/',
  escalationResolve: (id: string) => `/api/request-coordination/escalations/${id}/resolve/`,
  templates: '/api/request-coordination/templates/',
  templateDetail: (id: string) => `/api/request-coordination/templates/${id}/`,
  reportsSLACompliance: '/api/request-coordination/reports/sla-compliance/',
  reportsWorkload: '/api/request-coordination/reports/workload/',
  reportsTrends: '/api/request-coordination/reports/trends/',
} as const;

// Request Types
export type RequestType = 'software_install' | 'access_request' | 'hardware' | 'config_change' | 'exception';
export type RequestStatus = 'new' | 'in_progress' | 'pending' | 'resolved' | 'closed' | 'cancelled';
export type RequestPriority = '1' | '2' | '3' | '4';

export interface TrackedRequest {
  id: string;
  correlation_id: string;
  servicenow_number: string;
  servicenow_sys_id: string;
  request_type: RequestType;
  short_description: string;
  requestor_email: string;
  requestor_name: string;
  assigned_to: string | null;
  assignment_group: string | null;
  status: RequestStatus;
  priority: RequestPriority;
  sla_due: string | null;
  is_escalated: boolean;
  escalation_level: number;
  last_updated: string;
  blocked_reason: string | null;
  stakeholder_count: number;
  communication_count: number;
  escalation_count: number;
  sla_status: string;
  created_at: string;
  updated_at: string;
}

// Stakeholder Types
export type StakeholderRole = 'requestor' | 'approver' | 'watcher' | 'manager';

export interface RequestStakeholder {
  id: string;
  request: string;
  email: string;
  name: string;
  role: StakeholderRole;
  notification_preferences: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

// Status Update Types
export interface RequestStatusUpdate {
  id: string;
  request: string;
  old_status: string;
  new_status: string;
  update_notes: string | null;
  updated_by: string;
  created_at: string;
}

// Communication Types
export type CommunicationType = 'status_update' | 'sla_warning' | 'escalation' | 'completion' | 'weekly_digest';
export type CommunicationChannel = 'email' | 'teams' | 'slack' | 'servicenow';
export type CommunicationStatus = 'pending' | 'sent' | 'delivered' | 'failed';

export interface RequestCommunication {
  id: string;
  correlation_id: string;
  request: string;
  communication_type: CommunicationType;
  channel: CommunicationChannel;
  recipients: string[];
  subject: string;
  body: string;
  sent_at: string | null;
  status: CommunicationStatus;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

// Escalation Types
export type EscalationTriggerType = 'sla_warning' | 'sla_breach' | 'blocked' | 'reassignment';

export interface EscalationRule {
  id: string;
  name: string;
  description: string;
  request_type: string | null;
  trigger_type: EscalationTriggerType;
  trigger_config: Record<string, unknown>;
  escalation_actions: Array<Record<string, unknown>>;
  is_active: boolean;
  trigger_count: number;
  created_at: string;
  updated_at: string;
}

export interface EscalationEvent {
  id: string;
  correlation_id: string;
  request: string;
  request_number: string;
  rule: string | null;
  rule_name: string | null;
  trigger_reason: string;
  escalation_level: number;
  actions_taken: Array<Record<string, unknown>>;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
}

// Template Types
export interface CommunicationTemplate {
  id: string;
  name: string;
  communication_type: CommunicationType;
  channel: CommunicationChannel;
  subject_template: string;
  body_template: string;
  variables: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Report Types
export interface SLAComplianceReport {
  total: number;
  compliant: number;
  at_risk: number;
  breached: number;
  compliance_rate: number;
}

export interface WorkloadReport {
  workload: Array<{ assignment_group: string; count: number }>;
}

export interface TrendsReport {
  trends: Array<{ created_at__date: string; count: number }>;
}

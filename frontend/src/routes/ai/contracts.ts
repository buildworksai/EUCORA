// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * BuildWorks.AI-27001: AI Agents domain contracts
 * BuildWorks.AI-27002: Types, endpoints, and examples for AI agent hub
 * BuildWorks.AI-27004: Use ENDPOINTS constant, never hardcode URL strings
 */

/**
 * AI Agents domain types
 */
export interface AIAgent {
  id: number;
  name: string;
  description: string;
  provider: 'OPENAI' | 'ANTHROPIC' | 'GROQ';
  model: string;
  status: 'ACTIVE' | 'INACTIVE' | 'ERROR';
  last_used: string | null;
  usage_count: number;
}

export interface AIAgentListResponse {
  agents: AIAgent[];
}

export interface AIChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

export interface AIChatRequest {
  agent_id: number;
  messages: AIChatMessage[];
  context?: Record<string, unknown>;
}

export interface AIChatResponse {
  message: AIChatMessage;
  usage?: {
    tokens: number;
    cost?: number;
  };
}

/**
 * Workflow types for E8: AI Agent Workflows
 */
export type RiskLevel = 'R1' | 'R2' | 'R3';
export type ExecutionStatus = 'pending' | 'running' | 'awaiting_approval' | 'approved' | 'rejected' | 'completed' | 'failed' | 'cancelled';
export type StepStatus = 'pending' | 'running' | 'awaiting_input' | 'awaiting_approval' | 'completed' | 'skipped' | 'failed';
export type StepType = 'ai_action' | 'approval_gate' | 'user_input';

export interface WorkflowStepDefinition {
  name: string;
  type: StepType;
  description: string;
  instructions?: string;
  task?: string;
  risk_level?: RiskLevel;
  policy_tags?: string[];
  output_schema?: Record<string, unknown>;
}

export interface WorkflowDefinition {
  id: string;
  agent_type: string;
  name: string;
  description: string;
  steps: WorkflowStepDefinition[];
  required_policies: string[];
  risk_level: RiskLevel;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PolicyChunk {
  id: string;
  content: string;
  document_id: string;
  document_title: string;
  category: string;
  similarity: number;
  heading?: string;
  chunk_index?: number;
}

export interface WorkflowStep {
  id: string;
  step_index: number;
  name: string;
  description: string;
  step_type: StepType;
  status: StepStatus;
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown>;
  policies_considered: PolicyChunk[];
  prompt_used?: string;
  llm_response?: string;
  tokens_used: number;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  created_at: string;
}

export interface WorkflowExecution {
  id: string;
  correlation_id: string;
  workflow: WorkflowDefinition;
  initiated_by: number;
  initiated_by_username: string;
  status: ExecutionStatus;
  current_step_index: number;
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown>;
  policy_context: PolicyChunk[];
  approved_by?: number;
  approved_by_username?: string;
  approved_at?: string;
  rejection_reason?: string;
  started_at?: string;
  completed_at?: string;
  steps: WorkflowStep[];
  created_at: string;
  updated_at: string;
}

export interface StartWorkflowRequest {
  input_data: Record<string, unknown>;
}

export interface ApproveWorkflowStepRequest {
  notes?: string;
}

export interface RejectWorkflowStepRequest {
  reason: string;
}

/**
 * BuildWorks.AI-27004: ENDPOINTS constant - never hardcode URL strings
 */
export const ENDPOINTS = {
  AI_AGENTS_LIST: '/ai-agents/',
  AI_AGENT_DETAIL: (id: number) => `/ai-agents/${id}/`,
  AI_CHAT: '/ai-agents/chat/',
  // Workflow endpoints
  WORKFLOWS_LIST: '/api/v1/ai/workflows/',
  WORKFLOW_DETAIL: (id: string) => `/api/v1/ai/workflows/${id}/`,
  WORKFLOW_START: (id: string) => `/api/v1/ai/workflows/${id}/start/`,
  EXECUTIONS_LIST: '/api/v1/ai/executions/',
  EXECUTION_DETAIL: (id: string) => `/api/v1/ai/executions/${id}/`,
  EXECUTION_APPROVE: (id: string) => `/api/v1/ai/executions/${id}/approve/`,
  EXECUTION_REJECT: (id: string) => `/api/v1/ai/executions/${id}/reject/`,
  EXECUTION_CANCEL: (id: string) => `/api/v1/ai/executions/${id}/cancel/`,
} as const;

/**
 * Example usage:
 *
 * ```typescript
 * import { ENDPOINTS, type AIAgentListResponse } from './contracts';
 * import { api } from '@/lib/api/client';
 *
 * const response = await api.get<AIAgentListResponse>(ENDPOINTS.AI_AGENTS_LIST);
 * ```
 */

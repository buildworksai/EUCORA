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
 * BuildWorks.AI-27004: ENDPOINTS constant - never hardcode URL strings
 */
export const ENDPOINTS = {
  AI_AGENTS_LIST: '/ai-agents/',
  AI_AGENT_DETAIL: (id: number) => `/ai-agents/${id}/`,
  AI_CHAT: '/ai-agents/chat/',
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

// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * Knowledge domain contracts
 */

export type EmbeddingProvider = 'openai' | 'cohere' | 'local';

export interface EmbeddingConfig {
  id: string;
  provider: EmbeddingProvider;
  provider_label: string;
  model_name: string;
  dimensions: number;
  api_key?: string; // Write-only
  api_endpoint?: string;
  is_active: boolean;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface EmbeddingConfigCreate {
  provider: EmbeddingProvider;
  model_name: string;
  dimensions: number;
  api_key?: string;
  api_endpoint?: string;
  is_active?: boolean;
  is_default?: boolean;
}

export interface KnowledgeStats {
  total_vectors: number;
  policy_documents: number;
  deployments: number;
  last_indexed: string | null;
}

export interface TestEmbeddingResult {
  success: boolean;
  message: string;
  dimensions?: number;
}

/**
 * ENDPOINTS constant - never hardcode URL strings
 */
export const ENDPOINTS = {
  CONFIG: '/api/v1/knowledge/config/',
  CONFIG_DETAIL: (id: string) => `/api/v1/knowledge/config/${id}/`,
  CONFIG_TEST: (id: string) => `/api/v1/knowledge/config/${id}/test/`,
  STATS: '/api/v1/knowledge/search/stats/',
} as const;

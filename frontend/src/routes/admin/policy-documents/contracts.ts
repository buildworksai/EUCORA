// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * Policy Documents domain contracts
 */

export type DocumentStatus =
  | 'draft'
  | 'processing'
  | 'active'
  | 'deprecated'
  | 'archived'
  | 'failed';

export type CategoryType =
  | 'compliance'
  | 'security'
  | 'operational'
  | 'governance'
  | 'application'
  | 'custom';

export interface DocumentCategory {
  id: string;
  name: string;
  category_type: CategoryType;
  category_type_label: string;
  description: string;
  icon: string;
  color: string;
  is_system: boolean;
  created_at: string;
  updated_at: string;
}

export interface PolicyDocument {
  id: string;
  correlation_id: string;
  title: string;
  description: string;
  category: DocumentCategory;
  tags: string[];
  file_name: string;
  file_type: string;
  file_size: number;
  storage_path: string;
  content_hash: string;
  status: DocumentStatus;
  status_label: string;
  processing_error?: string;
  chunk_count: number;
  version: number;
  parent_document?: string;
  effective_date?: string;
  review_date?: string;
  author: string;
  uploaded_by?: string;
  uploaded_by_username?: string;
  created_at: string;
  updated_at: string;
}

export interface PolicyDocumentDetail extends PolicyDocument {
  chunks?: DocumentChunk[];
}

export interface DocumentChunk {
  id: string;
  document: string;
  chunk_index: number;
  content: string;
  heading?: string;
  page_number?: number;
  start_char: number;
  end_char: number;
  embedding_model?: string;
  created_at: string;
}

export interface PolicyDocumentCreate {
  title: string;
  description?: string;
  category_id: string;
  tags?: string[];
  effective_date?: string;
  review_date?: string;
  author?: string;
}

/**
 * ENDPOINTS constant - never hardcode URL strings
 */
export const ENDPOINTS = {
  CATEGORIES: '/api/v1/policy-documents/categories/',
  CATEGORY_DETAIL: (id: string) => `/api/v1/policy-documents/categories/${id}/`,
  DOCUMENTS: '/api/v1/policy-documents/',
  DOCUMENT_DETAIL: (id: string) => `/api/v1/policy-documents/${id}/`,
  UPLOAD: '/api/v1/policy-documents/upload/',
  DOWNLOAD: (id: string) => `/api/v1/policy-documents/${id}/download/`,
  REPROCESS: (id: string) => `/api/v1/policy-documents/${id}/reprocess/`,
  SEARCH: '/api/v1/policy-documents/search/',
  SEMANTIC_SEARCH: '/api/v1/policy-documents/semantic_search/',
} as const;

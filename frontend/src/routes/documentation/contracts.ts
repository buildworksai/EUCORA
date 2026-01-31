// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * E12: Documentation Agent - Type Contracts
 */

// API Endpoints
export const ENDPOINTS = {
  repositories: '/api/documentation/repositories/',
  repositoryDetail: (id: string) => `/api/documentation/repositories/${id}/`,
  repositoryAnalyze: (id: string) => `/api/documentation/repositories/${id}/analyze/`,
  analyses: '/api/documentation/analyses/',
  analysisDetail: (id: string) => `/api/documentation/analyses/${id}/`,
  analysisModules: (id: string) => `/api/documentation/analyses/${id}/modules/`,
  analysisQuality: (id: string) => `/api/documentation/analyses/${id}/quality/`,
  documents: '/api/documentation/documents/',
  documentDetail: (id: string) => `/api/documentation/documents/${id}/`,
  documentReview: (id: string) => `/api/documentation/documents/${id}/review/`,
  documentPublish: (id: string) => `/api/documentation/documents/${id}/publish/`,
  templates: '/api/documentation/templates/',
  templateDetail: (id: string) => `/api/documentation/templates/${id}/`,
  generate: '/api/documentation/generate/generate/',
  generateApiDocs: '/api/documentation/generate/api-docs/',
  generateRunbook: '/api/documentation/generate/runbook/',
  generateAdr: '/api/documentation/generate/adr/',
} as const;

// Repository Types
export type RepoType = 'github' | 'gitlab' | 'local';

export interface CodeRepository {
  id: string;
  name: string;
  repo_type: RepoType;
  url: string | null;
  local_path: string | null;
  default_branch: string;
  auth_config: Record<string, string> | null;
  last_analyzed: string | null;
  is_active: boolean;
  analysis_count: number;
  created_at: string;
  updated_at: string;
}

// Analysis Types
export type AnalysisStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface CodeAnalysis {
  id: string;
  correlation_id: string;
  repository: string;
  repository_name: string;
  commit_sha: string;
  branch: string;
  status: AnalysisStatus;
  started_at: string | null;
  completed_at: string | null;
  summary: {
    modules?: number;
    classes?: number;
    functions?: number;
  } | null;
  errors: string[];
  module_count: number;
  document_count: number;
  created_at: string;
  updated_at: string;
}

// Module Types
export type ModuleType = 'package' | 'class' | 'function' | 'endpoint' | 'component' | 'hook' | 'type';

export interface DocumentedModule {
  id: string;
  analysis: string;
  module_path: string;
  module_type: ModuleType;
  name: string;
  docstring: string | null;
  generated_doc: string | null;
  signature: string | null;
  dependencies: string[];
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

// Document Types
export type DocType = 'api' | 'readme' | 'architecture' | 'runbook' | 'adr' | 'test';
export type DocFormat = 'markdown' | 'openapi' | 'mermaid';
export type DocStatus = 'draft' | 'review' | 'published';

export interface GeneratedDocument {
  id: string;
  correlation_id: string;
  analysis: string;
  analysis_repository: string;
  doc_type: DocType;
  title: string;
  content: string;
  format: DocFormat;
  target_path: string | null;
  status: DocStatus;
  reviewed_by: string | null;
  reviewed_by_username: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

// Template Types
export interface DocumentationTemplate {
  id: string;
  name: string;
  doc_type: DocType;
  template_content: string;
  variables: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Quality Score Types
export interface QualityScore {
  overall_score: number;
  coverage: number;
  completeness: number;
  avg_docstring_length: number;
  total_modules: number;
  documented_modules: number;
  total_documents: number;
  complete_documents: number;
}

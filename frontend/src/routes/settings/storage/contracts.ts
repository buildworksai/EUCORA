// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * BuildWorks.AI-27001: Storage domain contracts
 * BuildWorks.AI-27002: Types, endpoints, and examples for storage
 * BuildWorks.AI-27004: Use ENDPOINTS constant, never hardcode URL strings
 */

/**
 * Storage domain types
 */

export type ProviderType = 'minio' | 'aws_s3' | 'azure_blob';

export type ProviderStatus =
  | 'configured'
  | 'testing'
  | 'healthy'
  | 'degraded'
  | 'failed'
  | 'disabled';

export type AWSAuthMethod = 'access_key' | 'iam_role' | 'assume_role';

export type AzureAuthMethod =
  | 'connection_string'
  | 'account_key'
  | 'sas_token'
  | 'managed_identity'
  | 'service_principal';

export interface StorageProvider {
  id: string;
  name: string;
  provider_type: ProviderType;
  provider_type_label: string;
  priority: number;
  is_primary: boolean;
  is_enabled: boolean;
  status: ProviderStatus;
  status_label: string;
  last_health_check?: string;
  health_check_error?: string;
  configured_by?: string;
  configured_by_username?: string;
  created_at: string;
  updated_at: string;
}

export interface StorageProviderDetail extends StorageProvider {
  minio_config?: MinIOConfig;
  s3_config?: AWSS3Config;
  azure_config?: AzureBlobConfig;
}

export interface MinIOConfig {
  endpoint_url: string;
  bucket_name: string;
  access_key_id?: string; // Write-only
  secret_access_key?: string; // Write-only
  use_ssl: boolean;
  region: string;
  path_style: boolean;
}

export interface AWSS3Config {
  bucket_name: string;
  region: string;
  auth_method: AWSAuthMethod;
  auth_method_label: string;
  access_key_id?: string; // Write-only
  secret_access_key?: string; // Write-only
  role_arn?: string;
  external_id?: string;
  endpoint_url?: string;
  kms_key_id?: string;
}

export interface AzureBlobConfig {
  account_name: string;
  container_name: string;
  auth_method: AzureAuthMethod;
  auth_method_label: string;
  connection_string?: string; // Write-only
  account_key?: string; // Write-only
  sas_token?: string; // Write-only
  tenant_id?: string;
  client_id?: string;
  client_secret?: string; // Write-only
}

export interface StorageProviderCreate {
  name: string;
  provider_type: ProviderType;
  priority?: number;
  is_primary?: boolean;
  is_enabled?: boolean;
  minio_config?: MinIOConfig;
  s3_config?: AWSS3Config;
  azure_config?: AzureBlobConfig;
}

export interface StorageMetrics {
  id: string;
  provider: string;
  provider_name: string;
  recorded_at: string;
  total_bytes: number;
  used_bytes: number;
  object_count: number;
  uploads: number;
  downloads: number;
  deletes: number;
  bytes_uploaded: number;
  bytes_downloaded: number;
  failed_operations: number;
}

export interface TestResult {
  name: string;
  success: boolean;
  message: string;
  latency_ms?: number;
}

export interface ConnectionTestResult {
  success: boolean;
  message: string;
  latency_ms?: number;
  tests: TestResult[];
}

export interface HealthStatus {
  is_healthy: boolean;
  primary_provider?: StorageProvider;
  available_providers: number;
  total_providers: number;
}

/**
 * ENDPOINTS constant - never hardcode URL strings
 */
export const ENDPOINTS = {
  PROVIDERS: '/api/v1/storage/providers/',
  PROVIDER_DETAIL: (id: string) => `/api/v1/storage/providers/${id}/`,
  PROVIDER_TEST: (id: string) => `/api/v1/storage/providers/${id}/test/`,
  PROVIDER_SET_PRIMARY: (id: string) => `/api/v1/storage/providers/${id}/set-primary/`,
  PROVIDER_METRICS: (id: string) => `/api/v1/storage/providers/${id}/metrics/`,
  HEALTH: '/api/v1/storage/health/',
} as const;

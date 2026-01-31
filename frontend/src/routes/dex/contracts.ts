// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI

/**
 * DEX Integration API contracts.
 */

export interface DEXProvider {
  id: string;
  correlation_id: string;
  name: string;
  provider_type: '1e' | 'mock';
  is_enabled: boolean;
  server_url?: string;
  auth_method: 'ntlm' | 'basic' | 'api_key';
  sync_interval_minutes: number;
  last_sync_at?: string;
  last_sync_status?: string;
  last_sync_error?: string;
  retention_days: number;
  created_at: string;
  updated_at: string;
}

export interface DEXDeviceMetrics {
  id: string;
  correlation_id: string;
  device_id: string;
  device_name: string;
  asset?: string;
  dex_score?: number;
  performance_score?: number;
  stability_score?: number;
  responsiveness_score?: number;
  boot_time_seconds?: number;
  login_time_seconds?: number;
  user_sentiment?: string;
  sentiment_score?: number;
  carbon_footprint_kg?: number;
  power_consumption_kwh?: number;
  collected_at: string;
  source: string;
  created_at: string;
  updated_at: string;
}

export interface DEXAggregateMetrics {
  id: string;
  correlation_id: string;
  period_start: string;
  period_end: string;
  aggregation_type: string;
  total_devices: number;
  devices_with_dex: number;
  avg_dex_score?: number;
  min_dex_score?: number;
  max_dex_score?: number;
  dex_score_std_dev?: number;
  avg_boot_time?: number;
  p50_boot_time?: number;
  p95_boot_time?: number;
  positive_sentiment_count: number;
  neutral_sentiment_count: number;
  negative_sentiment_count: number;
  total_carbon_kg?: number;
  total_power_kwh?: number;
  created_at: string;
  updated_at: string;
}

export interface DEXDashboardSummary {
  avg_dex_score: number;
  total_devices: number;
  devices_with_dex: number;
  avg_boot_time?: number;
  total_carbon_kg?: number;
  total_power_kwh?: number;
  positive_sentiment_pct: number;
  neutral_sentiment_pct: number;
  negative_sentiment_pct: number;
}

export interface GreenITSummary {
  total_carbon_kg: number;
  total_power_kwh: number;
  avg_carbon_per_device: number;
  avg_power_per_device: number;
  device_count: number;
}

export const ENDPOINTS = {
  provider: '/api/v1/dex/provider/',
  providerTest: '/api/v1/dex/provider/test/',
  providerSync: '/api/v1/dex/provider/sync/',
  metrics: '/api/v1/dex/metrics/',
  aggregates: '/api/v1/dex/aggregates/',
  dashboardSummary: '/api/v1/dex/dashboard/summary/',
  greenITSummary: '/api/v1/dex/green-it/summary/',
} as const;

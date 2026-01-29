// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * BuildWorks.AI-27001: Assets domain contracts
 * BuildWorks.AI-27002: Types, endpoints, and examples for asset inventory
 * BuildWorks.AI-27004: Use ENDPOINTS constant, never hardcode URL strings
 */

/**
 * Asset domain types
 */
export interface Asset {
  id: number;
  hostname: string;
  platform: 'WINDOWS' | 'MACOS' | 'LINUX' | 'MOBILE';
  os_version: string;
  device_type: string;
  user_sentiment?: 'Positive' | 'Neutral' | 'Negative';
  dex_score?: number;
  boot_time?: number;
  carbon_footprint?: number;
  last_seen: string;
  created_at: string;
}

export interface AssetsResponse {
  assets: Asset[];
  count: number;
  page: number;
  page_size: number;
}

export interface AssetFilters {
  platform?: string;
  device_type?: string;
  page?: number;
  page_size?: number;
}

/**
 * BuildWorks.AI-27004: ENDPOINTS constant - never hardcode URL strings
 */
export const ENDPOINTS = {
  ASSETS_LIST: '/assets/',
  ASSET_DETAIL: (id: number) => `/assets/${id}/`,
} as const;

/**
 * Example usage:
 *
 * ```typescript
 * import { ENDPOINTS, type AssetsResponse } from './contracts';
 * import { api } from '@/lib/api/client';
 *
 * const response = await api.get<AssetsResponse>(ENDPOINTS.ASSETS_LIST + '?page_size=1000');
 * ```
 */

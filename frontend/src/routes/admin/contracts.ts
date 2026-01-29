// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * BuildWorks.AI-27001: Admin demo data contracts
 * BuildWorks.AI-27002: Types, endpoints, and examples for demo data administration
 * BuildWorks.AI-27004: Use ENDPOINTS constant, never hardcode URL strings
 */

export interface DemoDataCounts {
  assets: number;
  applications: number;
  deployments: number;
  ring_deployments: number;
  cab_approvals: number;
  evidence_packs: number;
  events: number;
  users: number;
}

export interface DemoDataStatsResponse {
  counts: DemoDataCounts;
  demo_mode_enabled: boolean;
  last_seeded?: string | null;
}

export interface SeedDemoDataRequest {
  assets?: number;
  applications?: number;
  deployments?: number;
  users?: number;
  events?: number;
  batch_size?: number;
  clear_existing?: boolean;
  use_backup?: boolean;
  force_seed?: boolean;
}

export type SeedDemoDataResponse =
  | {
      status: 'success';
      counts: DemoDataCounts;
      message: string;
      method: 'sync_seed' | 'backup_restore';
    }
  | {
      status: 'queued';
      message: string;
      task_id: string;
      method: 'async_seed';
    }
  | {
      status: 'error';
      error: string;
    };

export interface ClearDemoDataResponse {
  status: string;
  counts: DemoDataCounts;
}

export interface DemoModeResponse {
  demo_mode_enabled: boolean;
}

export const ENDPOINTS = {
  DEMO_DATA_STATS: '/admin/demo-data-stats',
  SEED_DEMO_DATA: '/admin/seed-demo-data',
  CLEAR_DEMO_DATA: '/admin/clear-demo-data',
  DEMO_MODE: '/admin/demo-mode',
} as const;

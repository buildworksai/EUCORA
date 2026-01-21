// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * BuildWorks.AI-27001: Deployment sidebar domain contracts
 * BuildWorks.AI-27004: Use ENDPOINTS constant, never hardcode URL strings
 */

import type { DeploymentIntent } from '@/types/api';

/**
 * Sidebar application group with nested versions and deployments.
 */
export interface SidebarApplicationGroup {
  app_name: string;
  latest_version: string;
  deployment_count: number;
  versions: SidebarVersionEntry[];
}

export interface SidebarVersionEntry {
  version: string;
  latest_created_at: string;
  deployments: DeploymentIntent[];
}

export interface ApplicationListResponse {
  applications: SidebarApplicationGroup[];
}

/**
 * ENDPOINTS constant for sidebar application listing.
 */
export const SIDEBAR_ENDPOINTS = {
  APPLICATIONS_WITH_VERSIONS: '/deployments/applications',
} as const;

/**
 * Example usage:
 *
 * ```typescript
 * import { SIDEBAR_ENDPOINTS, type ApplicationListResponse } from './sidebar-contracts';
 * import { api } from '@/lib/api/client';
 *
 * const response = await api.get<ApplicationListResponse>(SIDEBAR_ENDPOINTS.APPLICATIONS_WITH_VERSIONS);
 * ```
 */

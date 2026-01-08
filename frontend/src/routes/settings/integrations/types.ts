// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * Integration config types for Settings UI.
 */
import type { CMDBConfig, EntraIdConfig, MonitoringConfig, TicketingConfig } from '@/types/auth';

export type MDMConfig = {
  platform: 'abm' | 'android_enterprise';
  apiUrl: string;
  organizationId: string;
  serverToken: string;
  syncInterval: number;
  isConfigured: boolean;
};

export type IntegrationsState = {
  entraId: EntraIdConfig;
  cmdb: CMDBConfig;
  ticketing: TicketingConfig;
  mdm: MDMConfig;
  monitoring: MonitoringConfig;
};

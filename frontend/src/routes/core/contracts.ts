// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * BuildWorks.AI-27001: Core domain contracts
 * BuildWorks.AI-27002: Types, endpoints, and examples for core functionality
 * BuildWorks.AI-27004: Use ENDPOINTS constant, never hardcode URL strings
 */

/**
 * Core domain types
 */
export interface HealthCheck {
  status: 'healthy' | 'unhealthy';
  checks: {
    database?: { status: string; error?: string };
    cache?: { status: string; error?: string };
    application?: { name: string; organization: string; version: string };
  };
}

export interface Notification {
  id: number;
  type: 'INFO' | 'WARNING' | 'ERROR' | 'SUCCESS';
  title: string;
  message: string;
  read: boolean;
  created_at: string;
  link?: string;
}

export interface NotificationListResponse {
  notifications: Notification[];
  unread_count: number;
}

export interface MarkNotificationReadResponse {
  message: string;
}

/**
 * BuildWorks.AI-27004: ENDPOINTS constant - never hardcode URL strings
 */
export const ENDPOINTS = {
  HEALTH: '/health/',
  NOTIFICATIONS: '/notifications/',
  NOTIFICATION_READ: (id: number) => `/notifications/${id}/read/`,
  NOTIFICATIONS_MARK_ALL_READ: '/notifications/mark-all-read/',
} as const;

/**
 * Example usage:
 *
 * ```typescript
 * import { ENDPOINTS, type HealthCheck } from './contracts';
 * import { api } from '@/lib/api/client';
 *
 * const response = await api.get<HealthCheck>(ENDPOINTS.HEALTH);
 * ```
 */

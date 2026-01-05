// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * Authentication types for EUCORA session-based auth.
 */

export type UserRole = 'admin' | 'operator' | 'viewer' | 'demo';

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  avatar?: string;
  department?: string;
  lastLogin?: Date;
  createdAt?: Date;
  isActive: boolean;
  permissions: Permission[];
  // Django-compatible fields
  is_staff?: boolean;
  is_superuser?: boolean;
}

export interface Permission {
  resource: string;
  actions: ('read' | 'write' | 'delete' | 'admin')[];
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface AuthResponse {
  user: User;
  sessionId: string;
  expiresAt: string;
}

// Integration configuration types
export interface EntraIdConfig {
  tenantId: string;
  clientId: string;
  clientSecret?: string;
  redirectUri: string;
  scopes: string[];
  isConfigured: boolean;
}

export interface CMDBConfig {
  type: 'servicenow' | 'jira' | 'freshservice' | 'custom';
  apiUrl: string;
  apiKey?: string;
  username?: string;
  syncInterval: number; // minutes
  isConfigured: boolean;
}

export interface TicketingConfig {
  type: 'servicenow' | 'jira' | 'freshservice' | 'zendesk' | 'custom';
  apiUrl: string;
  apiKey?: string;
  projectKey?: string;
  defaultPriority: string;
  isConfigured: boolean;
}

export interface MonitoringConfig {
  type: 'datadog' | 'splunk' | 'elastic' | 'prometheus' | 'custom';
  apiUrl: string;
  apiKey?: string;
  dashboardUrl?: string;
  alertWebhook?: string;
  isConfigured: boolean;
}

export interface SystemIntegrations {
  entraId: EntraIdConfig;
  cmdb: CMDBConfig;
  ticketing: TicketingConfig;
  monitoring: MonitoringConfig;
}

// Default permissions per role
export const DEFAULT_PERMISSIONS: Record<UserRole, Permission[]> = {
  admin: [
    { resource: '*', actions: ['read', 'write', 'delete', 'admin'] },
  ],
  operator: [
    { resource: 'deployments', actions: ['read', 'write'] },
    { resource: 'assets', actions: ['read', 'write'] },
    { resource: 'cab', actions: ['read', 'write'] },
    { resource: 'audit', actions: ['read'] },
    { resource: 'settings', actions: ['read'] },
  ],
  viewer: [
    { resource: 'dashboard', actions: ['read'] },
    { resource: 'deployments', actions: ['read'] },
    { resource: 'assets', actions: ['read'] },
    { resource: 'audit', actions: ['read'] },
  ],
  demo: [
    { resource: 'dashboard', actions: ['read'] },
    { resource: 'deployments', actions: ['read'] },
    { resource: 'assets', actions: ['read'] },
    { resource: 'cab', actions: ['read'] },
    { resource: 'audit', actions: ['read'] },
    { resource: 'settings', actions: ['read'] },
  ],
};

// Mock users for development
export const MOCK_USERS: Record<string, User & { password: string }> = {
  'admin@eucora.com': {
    id: '1',
    email: 'admin@eucora.com',
    password: 'admin@134',
    firstName: 'System',
    lastName: 'Administrator',
    role: 'admin',
    department: 'IT Operations',
    isActive: true,
    permissions: DEFAULT_PERMISSIONS.admin,
    createdAt: new Date('2024-01-01'),
    lastLogin: new Date(),
    is_staff: true,
    is_superuser: true,
  },
  'demo@eucora.com': {
    id: '2',
    email: 'demo@eucora.com',
    password: 'admin@134',
    firstName: 'Demo',
    lastName: 'User',
    role: 'demo',
    department: 'Engineering',
    isActive: true,
    permissions: DEFAULT_PERMISSIONS.demo,
    createdAt: new Date('2024-06-01'),
    lastLogin: new Date(),
    is_staff: false,
    is_superuser: false,
  },
};

// Helper to check permissions
export function hasPermission(
  user: User | null,
  resource: string,
  action: 'read' | 'write' | 'delete' | 'admin'
): boolean {
  if (!user) return false;
  
  return user.permissions.some(
    (p) =>
      (p.resource === '*' || p.resource === resource) &&
      p.actions.includes(action)
  );
}

export function isAdmin(user: User | null): boolean {
  return user?.role === 'admin';
}

export function isDemo(user: User | null): boolean {
  return user?.role === 'demo';
}


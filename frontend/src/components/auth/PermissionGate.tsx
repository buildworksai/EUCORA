// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * PermissionGate component - Component-level permission guard.
 *
 * Conditionally renders children based on permission.
 * Returns null or fallback if user lacks permission.
 *
 * Permission checking hierarchy:
 * 1. If user is admin (from auth store), always allow
 * 2. If RBAC permissions are loading, show children (optimistic)
 * 3. Check RBAC API permissions for fine-grained control
 */
import { ReactNode } from 'react';
import { ResourceType, ActionType } from '@/routes/settings/rbac/contracts';
import { usePermissions } from '@/lib/auth/usePermissions';
import { useAuthStore } from '@/lib/stores/authStore';
import { isAdmin } from '@/types/auth';

interface PermissionGateProps {
  resource: ResourceType;
  action: ActionType;
  children: ReactNode;
  fallback?: ReactNode;
  /** If true, hide content while permissions are loading. Default: false (optimistic) */
  requireLoaded?: boolean;
}

export function PermissionGate({
  resource,
  action,
  children,
  fallback = null,
  requireLoaded = false,
}: PermissionGateProps) {
  const { user } = useAuthStore();
  const { hasPermission, isLoading, isAdmin: isRbacAdmin } = usePermissions();

  // Admin users from auth store have full access
  if (isAdmin(user)) {
    return <>{children}</>;
  }

  // RBAC admin has full access
  if (isRbacAdmin) {
    return <>{children}</>;
  }

  // While loading, show content (optimistic) unless requireLoaded is true
  if (isLoading && !requireLoaded) {
    return <>{children}</>;
  }

  // Check fine-grained RBAC permissions
  if (!hasPermission(resource, action)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}

// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * PermissionGate component - Component-level permission guard.
 *
 * Conditionally renders children based on permission.
 * Returns null or fallback if user lacks permission.
 */
import { ReactNode } from 'react';
import { ResourceType, ActionType } from '@/routes/settings/rbac/contracts';
import { usePermissions } from '@/lib/auth/usePermissions';

interface PermissionGateProps {
  resource: ResourceType;
  action: ActionType;
  children: ReactNode;
  fallback?: ReactNode;
}

export function PermissionGate({
  resource,
  action,
  children,
  fallback = null,
}: PermissionGateProps) {
  const { hasPermission } = usePermissions();

  if (!hasPermission(resource, action)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}

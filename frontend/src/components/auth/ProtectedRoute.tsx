// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * ProtectedRoute component - Route-level permission guard.
 *
 * Wraps routes to check permissions before rendering.
 * Shows AccessDenied component if user lacks permission.
 */
import { ReactNode } from 'react';
import { ResourceType, ActionType } from '@/routes/settings/rbac/contracts';
import { usePermissions } from '@/lib/auth/usePermissions';
import { AccessDenied } from './AccessDenied';
import { Loader2 } from 'lucide-react';

interface ProtectedRouteProps {
  resource: ResourceType;
  action: ActionType;
  children: ReactNode;
  fallback?: ReactNode;
}

export function ProtectedRoute({
  resource,
  action,
  children,
  fallback,
}: ProtectedRouteProps) {
  const { hasPermission, isLoading } = usePermissions();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-eucora-teal" />
      </div>
    );
  }

  if (!hasPermission(resource, action)) {
    return fallback || <AccessDenied resource={resource} action={action} />;
  }

  return <>{children}</>;
}

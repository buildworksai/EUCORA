// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * AccessDenied component - Shows access denied message.
 */
import { ShieldX } from 'lucide-react';
import { ResourceType, ActionType } from '@/routes/settings/rbac/contracts';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface AccessDeniedProps {
  resource: ResourceType;
  action: ActionType;
}

export function AccessDenied({ resource, action }: AccessDeniedProps) {
  return (
    <div className="container mx-auto py-8">
      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShieldX className="h-5 w-5 text-destructive" />
            Access Denied
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertTitle>Permission Required</AlertTitle>
            <AlertDescription>
              You do not have permission to {action} {resource}.
              <br />
              Please contact your administrator if you believe this is an error.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    </div>
  );
}

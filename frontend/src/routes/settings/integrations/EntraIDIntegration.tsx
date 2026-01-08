// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Cloud, Save } from 'lucide-react';
import type { EntraIdConfig } from '@/types/auth';

type EntraIDIntegrationProps = {
  config: EntraIdConfig;
  onChange: (updates: Partial<EntraIdConfig>) => void;
  onSave: () => void;
};

export default function EntraIDIntegration({ config, onChange, onSave }: EntraIDIntegrationProps) {
  return (
    <Card className="glass">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/10">
              <Cloud className="h-5 w-5 text-blue-500" />
            </div>
            <div>
              <CardTitle className="text-lg">Microsoft Entra ID</CardTitle>
              <CardDescription>Single sign-on and directory integration</CardDescription>
            </div>
          </div>
          <Badge variant={config.isConfigured ? 'default' : 'secondary'}>
            {config.isConfigured ? 'Connected' : 'Not Configured'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Tenant ID</Label>
            <Input
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              value={config.tenantId}
              onChange={(e) => onChange({ tenantId: e.target.value })}
            />
          </div>
          <div className="space-y-2">
            <Label>Client ID</Label>
            <Input
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              value={config.clientId}
              onChange={(e) => onChange({ clientId: e.target.value })}
            />
          </div>
        </div>
        <div className="space-y-2">
          <Label>Redirect URI</Label>
          <Input
            value={config.redirectUri}
            onChange={(e) => onChange({ redirectUri: e.target.value })}
          />
        </div>
      </CardContent>
      <CardFooter>
        <Button onClick={onSave} className="bg-blue-500 hover:bg-blue-600">
          <Save className="mr-2 h-4 w-4" />
          Save Configuration
        </Button>
      </CardFooter>
    </Card>
  );
}

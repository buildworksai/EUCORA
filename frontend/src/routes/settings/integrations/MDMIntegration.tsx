// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Save, Smartphone } from 'lucide-react';
import type { MDMConfig } from './types';

type MDMIntegrationProps = {
  config: MDMConfig;
  onChange: (updates: Partial<MDMConfig>) => void;
  onSave: () => void;
};

export default function MDMIntegration({ config, onChange, onSave }: MDMIntegrationProps) {
  return (
    <Card className="glass">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-indigo-500/10">
              <Smartphone className="h-5 w-5 text-indigo-500" />
            </div>
            <div>
              <CardTitle className="text-lg">MDM Integration</CardTitle>
              <CardDescription>Apple Business Manager and Android Enterprise</CardDescription>
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
            <Label>Platform</Label>
            <Select
              value={config.platform}
              onValueChange={(value: MDMConfig['platform']) => onChange({ platform: value })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="abm">Apple Business Manager</SelectItem>
                <SelectItem value="android_enterprise">Android Enterprise</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Sync Interval (minutes)</Label>
            <Input
              type="number"
              value={config.syncInterval}
              onChange={(e) => onChange({ syncInterval: parseInt(e.target.value, 10) || 360 })}
            />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Organization ID</Label>
            <Input
              placeholder="org-123456"
              value={config.organizationId}
              onChange={(e) => onChange({ organizationId: e.target.value })}
            />
          </div>
          <div className="space-y-2">
            <Label>API URL</Label>
            <Input
              placeholder="https://mdm.apple.com/api"
              value={config.apiUrl}
              onChange={(e) => onChange({ apiUrl: e.target.value })}
            />
          </div>
        </div>
        <div className="space-y-2">
          <Label>Server Token</Label>
          <Input
            placeholder="paste-server-token"
            value={config.serverToken}
            onChange={(e) => onChange({ serverToken: e.target.value })}
          />
        </div>
      </CardContent>
      <CardFooter>
        <Button onClick={onSave} className="bg-indigo-500 hover:bg-indigo-600">
          <Save className="mr-2 h-4 w-4" />
          Save Configuration
        </Button>
      </CardFooter>
    </Card>
  );
}

// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Database, Save } from 'lucide-react';
import type { CMDBConfig } from '@/types/auth';

type CMDBIntegrationProps = {
  config: CMDBConfig;
  onChange: (updates: Partial<CMDBConfig>) => void;
  onSave: () => void;
};

export default function CMDBIntegration({ config, onChange, onSave }: CMDBIntegrationProps) {
  return (
    <Card className="glass">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-500/10">
              <Database className="h-5 w-5 text-purple-500" />
            </div>
            <div>
              <CardTitle className="text-lg">CMDB Integration</CardTitle>
              <CardDescription>Configuration management database sync</CardDescription>
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
            <Label>CMDB Type</Label>
            <Select
              value={config.type}
              onValueChange={(value: CMDBConfig['type']) => onChange({ type: value })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="servicenow">ServiceNow</SelectItem>
                <SelectItem value="jira">Jira Assets</SelectItem>
                <SelectItem value="freshservice">Freshservice</SelectItem>
                <SelectItem value="custom">Custom API</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Sync Interval (minutes)</Label>
            <Input
              type="number"
              value={config.syncInterval}
              onChange={(e) => onChange({ syncInterval: parseInt(e.target.value, 10) || 60 })}
            />
          </div>
        </div>
        <div className="space-y-2">
          <Label>API URL</Label>
          <Input
            placeholder="https://your-instance.service-now.com/api"
            value={config.apiUrl}
            onChange={(e) => onChange({ apiUrl: e.target.value })}
          />
        </div>
      </CardContent>
      <CardFooter>
        <Button onClick={onSave} className="bg-purple-500 hover:bg-purple-600">
          <Save className="mr-2 h-4 w-4" />
          Save Configuration
        </Button>
      </CardFooter>
    </Card>
  );
}

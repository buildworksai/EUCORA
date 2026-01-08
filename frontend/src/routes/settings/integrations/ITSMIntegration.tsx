// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Activity, Save } from 'lucide-react';
import type { TicketingConfig } from '@/types/auth';

type ITSMIntegrationProps = {
  config: TicketingConfig;
  onChange: (updates: Partial<TicketingConfig>) => void;
  onSave: () => void;
};

export default function ITSMIntegration({ config, onChange, onSave }: ITSMIntegrationProps) {
  return (
    <Card className="glass">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-500/10">
              <Activity className="h-5 w-5 text-green-500" />
            </div>
            <div>
              <CardTitle className="text-lg">ITSM / Ticketing</CardTitle>
              <CardDescription>Change request and incident management</CardDescription>
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
            <Label>System Type</Label>
            <Select
              value={config.type}
              onValueChange={(value: TicketingConfig['type']) => onChange({ type: value })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="servicenow">ServiceNow</SelectItem>
                <SelectItem value="jira">Jira Service Management</SelectItem>
                <SelectItem value="freshservice">Freshservice</SelectItem>
                <SelectItem value="zendesk">Zendesk</SelectItem>
                <SelectItem value="custom">Custom API</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Project Key</Label>
            <Input
              placeholder="EUCORA"
              value={config.projectKey || ''}
              onChange={(e) => onChange({ projectKey: e.target.value })}
            />
          </div>
        </div>
        <div className="space-y-2">
          <Label>API URL</Label>
          <Input
            placeholder="https://your-instance.atlassian.net"
            value={config.apiUrl}
            onChange={(e) => onChange({ apiUrl: e.target.value })}
          />
        </div>
      </CardContent>
      <CardFooter>
        <Button onClick={onSave} className="bg-green-500 hover:bg-green-600">
          <Save className="mr-2 h-4 w-4" />
          Save Configuration
        </Button>
      </CardFooter>
    </Card>
  );
}

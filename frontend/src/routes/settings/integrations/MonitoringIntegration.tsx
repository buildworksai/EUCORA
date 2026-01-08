// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Save, Server } from 'lucide-react';
import type { MonitoringConfig } from '@/types/auth';

type MonitoringIntegrationProps = {
  config: MonitoringConfig;
  onChange: (updates: Partial<MonitoringConfig>) => void;
  onSave: () => void;
};

export default function MonitoringIntegration({ config, onChange, onSave }: MonitoringIntegrationProps) {
  return (
    <Card className="glass">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-orange-500/10">
              <Server className="h-5 w-5 text-orange-500" />
            </div>
            <div>
              <CardTitle className="text-lg">Monitoring Integration</CardTitle>
              <CardDescription>Observability and alerting integration</CardDescription>
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
              value={config.type}
              onValueChange={(value: MonitoringConfig['type']) => onChange({ type: value })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="datadog">Datadog</SelectItem>
                <SelectItem value="splunk">Splunk</SelectItem>
                <SelectItem value="elastic">Elastic Stack</SelectItem>
                <SelectItem value="prometheus">Prometheus/Grafana</SelectItem>
                <SelectItem value="custom">Custom</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>API URL</Label>
            <Input
              placeholder="https://api.datadoghq.com"
              value={config.apiUrl}
              onChange={(e) => onChange({ apiUrl: e.target.value })}
            />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Dashboard URL</Label>
            <Input
              placeholder="https://app.datadoghq.com/dashboard/..."
              value={config.dashboardUrl || ''}
              onChange={(e) => onChange({ dashboardUrl: e.target.value })}
            />
          </div>
          <div className="space-y-2">
            <Label>Alert Webhook</Label>
            <Input
              placeholder="https://eucora.example.com/webhooks/alerts"
              value={config.alertWebhook || ''}
              onChange={(e) => onChange({ alertWebhook: e.target.value })}
            />
          </div>
        </div>
      </CardContent>
      <CardFooter>
        <Button onClick={onSave} className="bg-orange-500 hover:bg-orange-600">
          <Save className="mr-2 h-4 w-4" />
          Save Configuration
        </Button>
      </CardFooter>
    </Card>
  );
}

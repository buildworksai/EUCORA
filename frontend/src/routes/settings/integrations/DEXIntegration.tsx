// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { MonitorCheck, Save, TestTube } from 'lucide-react';
import { useState } from 'react';
import { api } from '@/lib/api/client';
import { ENDPOINTS, type DEXProvider } from '../../dex/contracts';

type DEXIntegrationProps = {
  config: DEXProvider | null;
  onChange: (updates: Partial<DEXProvider>) => void;
  onSave: () => void;
};

export default function DEXIntegration({ config, onChange, onSave }: DEXIntegrationProps) {
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  const handleTestConnection = async () => {
    if (!config) return;

    setIsTesting(true);
    setTestResult(null);

    try {
      const response = await api.post<{ status: string; message?: string }>(ENDPOINTS.providerTest, {});
      setTestResult({
        success: response.status === 'success',
        message: response.message || 'Connection test completed',
      });
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Connection test failed';
      setTestResult({
        success: false,
        message: errorMessage,
      });
    } finally {
      setIsTesting(false);
    }
  };

  if (!config) {
    return (
      <Card className="glass">
        <CardContent className="pt-6">
          <p className="text-muted-foreground">Loading DEX provider configuration...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-500/10">
              <MonitorCheck className="h-5 w-5 text-green-500" />
            </div>
            <div>
              <CardTitle className="text-lg">1E DEX Platform</CardTitle>
              <CardDescription>Digital Employee Experience monitoring and Green IT metrics</CardDescription>
            </div>
          </div>
          <Badge variant={config.is_enabled && config.last_sync_status === 'success' ? 'default' : 'secondary'}>
            {config.is_enabled && config.last_sync_status === 'success' ? 'Connected' : 'Not Configured'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label>Provider Type</Label>
          <Select
            value={config.provider_type}
            onValueChange={(value: '1e' | 'mock') => onChange({ provider_type: value })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1e">1E DEX Platform</SelectItem>
              <SelectItem value="mock">Mock Data (Demo)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {config.provider_type === '1e' && (
          <>
            <div className="space-y-2">
              <Label>1E Server URL</Label>
              <Input
                placeholder="https://1e-server.example.com"
                value={config.server_url || ''}
                onChange={(e) => onChange({ server_url: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Authentication Method</Label>
              <Select
                value={config.auth_method}
                onValueChange={(value: 'ntlm' | 'basic' | 'api_key') => onChange({ auth_method: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ntlm">Windows Authentication (NTLM)</SelectItem>
                  <SelectItem value="basic">Basic Authentication</SelectItem>
                  <SelectItem value="api_key">API Key</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {(config.auth_method === 'ntlm' || config.auth_method === 'basic') && (
              <div className="p-3 rounded-md bg-blue-500/10 text-blue-500 text-sm">
                Credentials are managed securely and cannot be viewed or edited here. Contact your administrator to update authentication credentials.
              </div>
            )}
            {config.auth_method === 'api_key' && (
              <div className="p-3 rounded-md bg-blue-500/10 text-blue-500 text-sm">
                API key is managed securely and cannot be viewed or edited here. Contact your administrator to update the API key.
              </div>
            )}
          </>
        )}

        <div className="space-y-2">
          <Label>Sync Interval (minutes)</Label>
          <Input
            type="number"
            min="1"
            value={config.sync_interval_minutes}
            onChange={(e) => onChange({ sync_interval_minutes: parseInt(e.target.value) || 60 })}
          />
        </div>

        {testResult && (
          <div className={`p-3 rounded-md ${testResult.success ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}`}>
            {testResult.message}
          </div>
        )}

        {config.last_sync_error && (
          <div className="p-3 rounded-md bg-red-500/10 text-red-500">
            Last sync error: {config.last_sync_error}
          </div>
        )}
      </CardContent>
      <CardFooter className="flex gap-2">
        {config.provider_type === '1e' && (
          <Button
            variant="outline"
            onClick={handleTestConnection}
            disabled={isTesting}
          >
            <TestTube className="mr-2 h-4 w-4" />
            {isTesting ? 'Testing...' : 'Test Connection'}
          </Button>
        )}
        <Button onClick={onSave} className="bg-green-500 hover:bg-green-600">
          <Save className="mr-2 h-4 w-4" />
          Save Configuration
        </Button>
      </CardFooter>
    </Card>
  );
}

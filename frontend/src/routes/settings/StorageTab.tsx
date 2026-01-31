// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog } from '@/components/ui/dialog';
import { HardDrive, Plus, CheckCircle2, XCircle, AlertCircle, Loader2, Settings } from 'lucide-react';
import { toast } from 'sonner';
import {
  useStorageProviders,
  useStorageHealth,
  useTestConnection,
  useSetPrimary,
  useDeleteProvider,
} from '@/lib/api/hooks/useStorage';
import { StorageProvider, ProviderStatus } from '@/routes/settings/storage/contracts';
import { PermissionGate } from '@/components/auth/PermissionGate';
import { ProviderDialog } from '@/components/storage';

const getStatusBadge = (status: ProviderStatus) => {
  switch (status) {
    case 'healthy':
      return (
        <Badge variant="outline" className="bg-green-500/10 text-green-500 border-green-500/30">
          <CheckCircle2 className="mr-1 h-3 w-3" />
          Healthy
        </Badge>
      );
    case 'failed':
      return (
        <Badge variant="outline" className="bg-red-500/10 text-red-500 border-red-500/30">
          <XCircle className="mr-1 h-3 w-3" />
          Failed
        </Badge>
      );
    case 'degraded':
      return (
        <Badge variant="outline" className="bg-yellow-500/10 text-yellow-500 border-yellow-500/30">
          <AlertCircle className="mr-1 h-3 w-3" />
          Degraded
        </Badge>
      );
    case 'testing':
      return (
        <Badge variant="outline" className="bg-blue-500/10 text-blue-500 border-blue-500/30">
          <Loader2 className="mr-1 h-3 w-3 animate-spin" />
          Testing
        </Badge>
      );
    default:
      return (
        <Badge variant="outline" className="bg-gray-500/10 text-gray-500 border-gray-500/30">
          {status}
        </Badge>
      );
  }
};


export default function StorageTab() {
  const [selectedProvider, setSelectedProvider] = useState<StorageProvider | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const { data: providers, isLoading: providersLoading } = useStorageProviders();
  const { data: health, isLoading: healthLoading } = useStorageHealth();
  const testConnectionMutation = useTestConnection();
  const setPrimaryMutation = useSetPrimary();
  const deleteProviderMutation = useDeleteProvider();

  const handleTestConnection = async (providerId: string) => {
    try {
      const result = await testConnectionMutation.mutateAsync(providerId);
      if (result.success) {
        toast.success('Connection test passed');
      } else {
        toast.error(`Connection test failed: ${result.message}`);
      }
    } catch {
      toast.error('Failed to test connection');
    }
  };

  const handleSetPrimary = async (providerId: string) => {
    try {
      await setPrimaryMutation.mutateAsync(providerId);
      toast.success('Primary provider updated');
    } catch {
      toast.error('Failed to set primary provider');
    }
  };

  const handleDelete = async (providerId: string) => {
    if (!confirm('Are you sure you want to delete this provider?')) {
      return;
    }

    try {
      await deleteProviderMutation.mutateAsync(providerId);
      toast.success('Provider deleted');
    } catch {
      toast.error('Failed to delete provider');
    }
  };

  const primaryProvider = providers?.find((p) => p.is_primary);

  return (
    <div className="space-y-6">
      {/* Storage Health Overview */}
      <Card className="glass">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <HardDrive className="h-5 w-5 text-eucora-teal" />
            Storage Health
          </CardTitle>
        </CardHeader>
        <CardContent>
          {healthLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-eucora-teal" />
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <p className="text-sm text-muted-foreground">Primary Provider</p>
                <p className="text-2xl font-bold">
                  {primaryProvider?.name || 'None'}
                </p>
                {primaryProvider && getStatusBadge(primaryProvider.status)}
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Available Providers</p>
                <p className="text-2xl font-bold">
                  {health?.available_providers || 0} / {health?.total_providers || 0}
                </p>
                <p className="text-sm text-muted-foreground">
                  {health?.is_healthy ? 'All systems operational' : 'Some providers unavailable'}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">System Status</p>
                <p className="text-2xl font-bold">
                  {health?.is_healthy ? (
                    <span className="text-green-500">Healthy</span>
                  ) : (
                    <span className="text-red-500">Degraded</span>
                  )}
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Configured Providers */}
      <Card className="glass">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Storage Providers</CardTitle>
              <CardDescription>Configure object storage backends</CardDescription>
            </div>
            <PermissionGate resource="storage_config" action="create">
              <Button onClick={() => setIsDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Add Provider
              </Button>
            </PermissionGate>
          </div>
        </CardHeader>
        <CardContent>
          {providersLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-eucora-teal" />
            </div>
          ) : providers && providers.length > 0 ? (
            <div className="space-y-3">
              {providers.map((provider) => (
                <div
                  key={provider.id}
                  className="flex items-center justify-between p-4 rounded-lg border bg-card"
                >
                  <div className="flex items-center gap-4">
                    <HardDrive className="h-8 w-8 text-eucora-teal" />
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium">{provider.name}</p>
                        {provider.is_primary && (
                          <Badge variant="outline" className="bg-eucora-gold/10 text-eucora-gold">
                            Primary
                          </Badge>
                        )}
                        {getStatusBadge(provider.status)}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {provider.provider_type_label} • Priority: {provider.priority}
                      </p>
                      {provider.last_health_check && (
                        <p className="text-xs text-muted-foreground">
                          Last check: {new Date(provider.last_health_check).toLocaleString()}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <PermissionGate resource="storage_config" action="execute">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleTestConnection(provider.id)}
                        disabled={testConnectionMutation.isPending}
                      >
                        {testConnectionMutation.isPending ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          'Test'
                        )}
                      </Button>
                    </PermissionGate>
                    {!provider.is_primary && (
                      <PermissionGate resource="storage_config" action="update">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleSetPrimary(provider.id)}
                          disabled={setPrimaryMutation.isPending}
                        >
                          Set Primary
                        </Button>
                      </PermissionGate>
                    )}
                    <PermissionGate resource="storage_config" action="update">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedProvider(provider);
                          setIsDialogOpen(true);
                        }}
                      >
                        <Settings className="h-4 w-4" />
                      </Button>
                    </PermissionGate>
                    <PermissionGate resource="storage_config" action="delete">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDelete(provider.id)}
                        disabled={deleteProviderMutation.isPending}
                      >
                        Delete
                      </Button>
                    </PermissionGate>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <HardDrive className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No storage providers configured</p>
              <p className="text-sm">Add a provider to get started</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={(open) => {
        if (!open) {
          setIsDialogOpen(false);
          setSelectedProvider(null);
        }
      }}>
        <ProviderDialog
          provider={selectedProvider}
          onClose={() => {
            setIsDialogOpen(false);
            setSelectedProvider(null);
          }}
          onSave={() => {
            setIsDialogOpen(false);
            setSelectedProvider(null);
            toast.success(selectedProvider ? 'Provider updated successfully' : 'Provider created successfully');
          }}
        />
      </Dialog>
    </div>
  );
}

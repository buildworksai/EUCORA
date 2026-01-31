// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { useState } from 'react';
import {
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { useCreateProvider, useUpdateProvider } from '@/lib/api/hooks/useStorage';
import {
  StorageProvider,
  StorageProviderCreate,
  ProviderType,
  MinIOConfig,
  AWSS3Config,
  AzureBlobConfig,
} from '@/routes/settings/storage/contracts';
import { MinIOConfigForm } from './MinIOConfigForm';
import { S3ConfigForm } from './S3ConfigForm';
import { AzureBlobConfigForm } from './AzureBlobConfigForm';
import { Loader2 } from 'lucide-react';

interface ProviderDialogProps {
  provider?: StorageProvider | null;
  preselectedType?: ProviderType | null;
  onClose: () => void;
  onSave: () => void;
}

export function ProviderDialog({ provider = null, preselectedType = null, onClose, onSave }: ProviderDialogProps) {
  // Initialize state from provider props with defaults
  const [name, setName] = useState(provider?.name ?? '');
  const [providerType, setProviderType] = useState<ProviderType>(provider?.provider_type ?? preselectedType ?? 'minio');
  const [priority, setPriority] = useState(provider?.priority ?? 100);
  const [isPrimary, setIsPrimary] = useState(provider?.is_primary ?? false);
  const [isEnabled, setIsEnabled] = useState(provider?.is_enabled ?? true);

  // Config forms state with proper types
  const [minioConfig, setMinioConfig] = useState<MinIOConfig | null>(null);
  const [s3Config, setS3Config] = useState<AWSS3Config | null>(null);
  const [azureConfig, setAzureConfig] = useState<AzureBlobConfig | null>(null);

  const createMutation = useCreateProvider();
  const updateMutation = useUpdateProvider();

  const handleSave = async () => {
    if (!name) {
      return;
    }

    const data: StorageProviderCreate = {
      name,
      provider_type: providerType,
      priority,
      is_primary: isPrimary,
      is_enabled: isEnabled,
    };

    if (providerType === 'minio' && minioConfig) {
      data.minio_config = minioConfig;
    } else if (providerType === 'aws_s3' && s3Config) {
      data.s3_config = s3Config;
    } else if (providerType === 'azure_blob' && azureConfig) {
      data.azure_config = azureConfig;
    }

    try {
      if (provider) {
        await updateMutation.mutateAsync({ id: provider.id, data });
      } else {
        await createMutation.mutateAsync(data);
      }
      onSave();
    } catch {
      // Error handled by mutation
    }
  };

  return (
    <DialogContent className="glass max-w-3xl max-h-[90vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle>{provider ? 'Edit Storage Provider' : 'Add Storage Provider'}</DialogTitle>
        <DialogDescription>Configure object storage backend</DialogDescription>
      </DialogHeader>

      <div className="space-y-6 py-4">
        {/* Basic Info */}
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Provider Name *</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="My Storage" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Provider Type *</Label>
              <Select value={providerType} onValueChange={(value: ProviderType) => setProviderType(value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="minio">MinIO (S3-Compatible)</SelectItem>
                  <SelectItem value="aws_s3">AWS S3</SelectItem>
                  <SelectItem value="azure_blob">Azure Blob Storage</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Priority</Label>
              <Input
                type="number"
                value={priority}
                onChange={(e) => setPriority(parseInt(e.target.value) || 100)}
                placeholder="100"
              />
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Switch checked={isPrimary} onCheckedChange={setIsPrimary} />
              <Label>Set as Primary Provider</Label>
            </div>
            <div className="flex items-center gap-2">
              <Switch checked={isEnabled} onCheckedChange={setIsEnabled} />
              <Label>Enabled</Label>
            </div>
          </div>
        </div>

        {/* Provider-Specific Config */}
        {providerType === 'minio' && (
          <MinIOConfigForm config={minioConfig} onChange={setMinioConfig} />
        )}
        {providerType === 'aws_s3' && <S3ConfigForm config={s3Config} onChange={setS3Config} />}
        {providerType === 'azure_blob' && (
          <AzureBlobConfigForm config={azureConfig} onChange={setAzureConfig} />
        )}
      </div>

      <DialogFooter>
        <Button variant="outline" onClick={onClose}>
          Cancel
        </Button>
        <Button
          onClick={handleSave}
          disabled={!name || createMutation.isPending || updateMutation.isPending}
          className="bg-eucora-teal hover:bg-eucora-teal-dark"
        >
          {(createMutation.isPending || updateMutation.isPending) && (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          )}
          {provider ? 'Update' : 'Create'} Provider
        </Button>
      </DialogFooter>
    </DialogContent>
  );
}

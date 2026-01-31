// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { useState, useEffect, useRef } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AzureBlobConfig, AzureAuthMethod } from '@/routes/settings/storage/contracts';

interface AzureBlobConfigFormProps {
  config?: AzureBlobConfig | null;
  onChange: (config: AzureBlobConfig) => void;
}

export function AzureBlobConfigForm({ config, onChange }: AzureBlobConfigFormProps) {
  // Initialize from config prop
  const [accountName, setAccountName] = useState(config?.account_name ?? '');
  const [containerName, setContainerName] = useState(config?.container_name ?? '');
  const [authMethod, setAuthMethod] = useState<AzureAuthMethod>(config?.auth_method ?? 'connection_string');
  const [connectionString, setConnectionString] = useState(config?.connection_string ?? '');
  const [accountKey, setAccountKey] = useState(config?.account_key ?? '');
  const [sasToken, setSasToken] = useState(config?.sas_token ?? '');
  const [tenantId, setTenantId] = useState(config?.tenant_id ?? '');
  const [clientId, setClientId] = useState(config?.client_id ?? '');
  const [clientSecret, setClientSecret] = useState(config?.client_secret ?? '');

  // Track if initial onChange has been called
  const hasCalledInitialOnChange = useRef(false);

  const buildConfig = (): AzureBlobConfig => {
    const azureConfig: AzureBlobConfig = {
      account_name: accountName,
      container_name: containerName,
      auth_method: authMethod,
      auth_method_label: '',
    };

    if (authMethod === 'connection_string') {
      azureConfig.connection_string = connectionString;
    } else if (authMethod === 'account_key') {
      azureConfig.account_key = accountKey;
    } else if (authMethod === 'sas_token') {
      azureConfig.sas_token = sasToken;
    } else if (authMethod === 'service_principal') {
      azureConfig.tenant_id = tenantId;
      azureConfig.client_id = clientId;
      azureConfig.client_secret = clientSecret;
    }

    return azureConfig;
  };

  // Call onChange on mount to populate parent state with defaults
  useEffect(() => {
    if (!hasCalledInitialOnChange.current) {
      hasCalledInitialOnChange.current = true;
      onChange(buildConfig());
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Call onChange when any field changes
  useEffect(() => {
    if (hasCalledInitialOnChange.current) {
      onChange(buildConfig());
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    accountName,
    containerName,
    authMethod,
    connectionString,
    accountKey,
    sasToken,
    tenantId,
    clientId,
    clientSecret,
  ]);

  return (
    <div className="space-y-4 border-t pt-4">
      <h3 className="font-semibold">Azure Blob Storage Configuration</h3>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Storage Account Name *</Label>
          <Input value={accountName} onChange={(e) => setAccountName(e.target.value)} placeholder="eucorastorage" />
        </div>
        <div className="space-y-2">
          <Label>Container Name *</Label>
          <Input value={containerName} onChange={(e) => setContainerName(e.target.value)} placeholder="eucora-data" />
        </div>
        <div className="space-y-2 col-span-2">
          <Label>Authentication Method *</Label>
          <Select value={authMethod} onValueChange={(value: AzureAuthMethod) => setAuthMethod(value)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="connection_string">Connection String</SelectItem>
              <SelectItem value="account_key">Account Key</SelectItem>
              <SelectItem value="sas_token">SAS Token</SelectItem>
              <SelectItem value="managed_identity">Managed Identity</SelectItem>
              <SelectItem value="service_principal">Service Principal</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {authMethod === 'connection_string' && (
          <div className="space-y-2 col-span-2">
            <Label>Connection String *</Label>
            <Input
              type="password"
              value={connectionString}
              onChange={(e) => setConnectionString(e.target.value)}
              placeholder="DefaultEndpointsProtocol=https;AccountName=..."
            />
          </div>
        )}

        {authMethod === 'account_key' && (
          <div className="space-y-2 col-span-2">
            <Label>Account Key *</Label>
            <Input
              type="password"
              value={accountKey}
              onChange={(e) => setAccountKey(e.target.value)}
              placeholder="..."
            />
          </div>
        )}

        {authMethod === 'sas_token' && (
          <div className="space-y-2 col-span-2">
            <Label>SAS Token *</Label>
            <Input
              type="password"
              value={sasToken}
              onChange={(e) => setSasToken(e.target.value)}
              placeholder="?sv=..."
            />
          </div>
        )}

        {authMethod === 'service_principal' && (
          <>
            <div className="space-y-2">
              <Label>Tenant ID *</Label>
              <Input value={tenantId} onChange={(e) => setTenantId(e.target.value)} placeholder="..." />
            </div>
            <div className="space-y-2">
              <Label>Client ID *</Label>
              <Input value={clientId} onChange={(e) => setClientId(e.target.value)} placeholder="..." />
            </div>
            <div className="space-y-2 col-span-2">
              <Label>Client Secret *</Label>
              <Input
                type="password"
                value={clientSecret}
                onChange={(e) => setClientSecret(e.target.value)}
                placeholder="..."
              />
            </div>
          </>
        )}

        {authMethod === 'managed_identity' && (
          <div className="col-span-2 text-sm text-muted-foreground">
            Managed Identity will be used automatically when running on Azure (VM, App Service, etc.)
          </div>
        )}
      </div>
    </div>
  );
}

// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { useEffect, useMemo, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Check, Eye, EyeOff, Save, Sparkles } from 'lucide-react';
import { useConfigureProvider, useModelProviders } from '@/lib/api/hooks/useAI';
import { toast } from 'sonner';
import { PROVIDERS } from './data';
import { useAuthStore } from '@/lib/stores/authStore';
import { isDemo } from '@/types/auth';

type ProviderConfigState = {
  api_key?: string;
  model_name?: string;
  endpoint_url?: string;
  max_tokens?: number;
  temperature?: number;
  is_default?: boolean;
};

export default function AIProvidersTab() {
  const { user } = useAuthStore();
  const userIsDemo = isDemo(user);
  const [showKey, setShowKey] = useState<Record<string, boolean>>({});
  const [providerConfigs, setProviderConfigs] = useState<Record<string, ProviderConfigState>>({});

  const { data } = useModelProviders();
  const providers = data?.providers ?? [];
  const { mutate: configureProvider, isPending: isSaving } = useConfigureProvider();

  const providersKey = useMemo(() => JSON.stringify(providers.map((provider) => provider.id)), [providers]);

  useEffect(() => {
    if (providers.length === 0) return;

    const configs: Record<string, ProviderConfigState> = {};
    providers.forEach((provider) => {
      configs[provider.provider_type] = {
        model_name: provider.model_name,
        endpoint_url: provider.endpoint_url,
        max_tokens: provider.max_tokens,
        temperature: provider.temperature,
        is_default: provider.is_default,
      };
    });
    setProviderConfigs(configs);
  }, [providersKey, providers]);

  const toggleKey = (providerId: string) => {
    setShowKey((prev) => ({ ...prev, [providerId]: !prev[providerId] }));
  };

  const handleSaveProvider = (providerId: string) => {
    const providerConfig = PROVIDERS.find((provider) => provider.id === providerId);
    const config = providerConfigs[providerId] || {};

    if (!providerConfig) return;
    if (userIsDemo) {
      toast.info('Configuration changes are disabled in demo mode');
      return;
    }

    configureProvider(
      {
        provider_type: providerId,
        api_key: config.api_key || '',
        model_name: config.model_name || providerConfig.models[0],
        display_name: providerConfig.name,
        endpoint_url: config.endpoint_url,
        max_tokens: config.max_tokens,
        temperature: config.temperature,
        is_default: config.is_default,
      },
      {
        onSuccess: () => {
          toast.success(`${providerConfig.name} configuration saved`);
          setProviderConfigs((prev) => ({
            ...prev,
            [providerId]: { ...prev[providerId], api_key: '' },
          }));
        },
        onError: () => {
          toast.error(`Failed to save ${providerConfig.name} configuration`);
        },
      }
    );
  };

  return (
    <>
      <Card className="glass border-eucora-teal/30">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-eucora-teal" />
            <CardTitle>Default AI Provider</CardTitle>
          </div>
          <CardDescription>
            Select the default provider for &quot;Ask Amani&quot; and agent workflows.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <Select
              value={providers.find((provider) => provider.is_default)?.provider_type || ''}
              onValueChange={(value) => {
                if (userIsDemo) {
                  toast.info('Configuration changes are disabled in demo mode');
                  return;
                }
                const provider = providers.find((item) => item.provider_type === value);
                if (!provider) return;
                configureProvider(
                  {
                    provider_type: provider.provider_type,
                    api_key: '',
                    model_name: provider.model_name,
                    display_name: provider.display_name,
                    is_default: true,
                  },
                  {
                    onSuccess: () => toast.success('Default provider updated'),
                  }
                );
              }}
            >
              <SelectTrigger className="w-full max-w-xs">
                <SelectValue placeholder="Select default provider" />
              </SelectTrigger>
              <SelectContent>
                {providers
                  .filter((provider) => provider.is_active && provider.key_configured)
                  .map((provider) => {
                    const providerConfig = PROVIDERS.find((item) => item.id === provider.provider_type);
                    const IconComponent = providerConfig?.icon;
                    return (
                      <SelectItem key={provider.id} value={provider.provider_type}>
                        <div className="flex items-center gap-2">
                          {IconComponent && <IconComponent className="h-4 w-4" />}
                          {provider.display_name} ({provider.model_name})
                        </div>
                      </SelectItem>
                    );
                  })}
              </SelectContent>
            </Select>
            {providers.filter((provider) => provider.is_default && provider.is_active).length === 0 && (
              <Badge variant="outline" className="text-yellow-500 border-yellow-500">
                No default provider set
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        {PROVIDERS.map((provider) => {
          const existingProvider = providers.find((item) => item.provider_type === provider.id);
          const isConfigured = existingProvider?.key_configured || false;
          const config = providerConfigs[provider.id] || {};

          return (
            <Card
              key={provider.id}
              className={`glass transition-all ${isConfigured ? 'border-green-500/30' : ''}`}
            >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <provider.icon className="h-5 w-5 text-eucora-teal" />
                    <CardTitle className="text-base">{provider.name}</CardTitle>
                  </div>
                  {isConfigured && (
                    <Badge variant="outline" className="text-green-500 border-green-500">
                      <Check className="h-3 w-3 mr-1" /> Configured
                    </Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Model</Label>
                  <Select
                    value={config.model_name || provider.models[0]}
                    onValueChange={(value) =>
                      setProviderConfigs((prev) => ({
                        ...prev,
                        [provider.id]: { ...prev[provider.id], model_name: value },
                      }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {provider.models.map((model) => (
                        <SelectItem key={model} value={model}>
                          {model}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>
                    API Key{' '}
                    {isConfigured && (
                      <span className="text-muted-foreground text-xs">(leave blank to keep existing)</span>
                    )}
                  </Label>
                  <div className="flex gap-2">
                    <Input
                      type={showKey[provider.id] ? 'text' : 'password'}
                      placeholder={provider.placeholder}
                      value={config.api_key || ''}
                      onChange={(e) =>
                        setProviderConfigs((prev) => ({
                          ...prev,
                          [provider.id]: { ...prev[provider.id], api_key: e.target.value },
                        }))
                      }
                    />
                    <Button variant="ghost" size="icon" onClick={() => toggleKey(provider.id)}>
                      {showKey[provider.id] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>

                {provider.hasEndpoint && (
                  <div className="space-y-2">
                    <Label>Endpoint URL</Label>
                    <Input
                      placeholder="https://your-endpoint.openai.azure.com/"
                      value={config.endpoint_url || ''}
                      onChange={(e) =>
                        setProviderConfigs((prev) => ({
                          ...prev,
                          [provider.id]: { ...prev[provider.id], endpoint_url: e.target.value },
                        }))
                      }
                    />
                  </div>
                )}
              </CardContent>
              <CardFooter className="pt-0">
                <Button
                  className="w-full bg-eucora-teal hover:bg-eucora-teal-dark"
                  onClick={() => handleSaveProvider(provider.id)}
                  disabled={isSaving}
                >
                  <Save className="mr-2 h-4 w-4" />
                  {isConfigured ? 'Update' : 'Save'}
                </Button>
              </CardFooter>
            </Card>
          );
        })}
      </div>
    </>
  );
}

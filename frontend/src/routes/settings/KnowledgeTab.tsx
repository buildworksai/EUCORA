// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Brain, Plus, Loader2, CheckCircle2, XCircle, Database } from 'lucide-react';
import { toast } from 'sonner';
import {
  useEmbeddingConfigs,
  useCreateEmbeddingConfig,
  useUpdateEmbeddingConfig,
  useDeleteEmbeddingConfig,
  useTestEmbeddingProvider,
  useKnowledgeStats,
} from '@/lib/api/hooks/useKnowledge';
import { EmbeddingConfig, EmbeddingProvider } from '@/routes/settings/knowledge/contracts';
import { PermissionGate } from '@/components/auth/PermissionGate';

const PROVIDER_MODELS: Record<EmbeddingProvider, { name: string; dimensions: number }[]> = {
  openai: [
    { name: 'text-embedding-3-small', dimensions: 1536 },
    { name: 'text-embedding-3-large', dimensions: 3072 },
    { name: 'text-embedding-ada-002', dimensions: 1536 },
  ],
  cohere: [
    { name: 'embed-english-v3.0', dimensions: 1024 },
    { name: 'embed-multilingual-v3.0', dimensions: 1024 },
  ],
  local: [
    { name: 'all-MiniLM-L6-v2', dimensions: 384 },
    { name: 'all-mpnet-base-v2', dimensions: 768 },
  ],
};

interface ConfigDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  config?: EmbeddingConfig | null;
}

function ConfigDialog({ open, onOpenChange, config }: ConfigDialogProps) {
  const [provider, setProvider] = useState<EmbeddingProvider>(config?.provider || 'openai');
  const [modelName, setModelName] = useState(config?.model_name || '');
  const [apiKey, setApiKey] = useState('');
  const [apiEndpoint, setApiEndpoint] = useState(config?.api_endpoint || '');
  const [isDefault, setIsDefault] = useState(config?.is_default || false);
  const [isActive, setIsActive] = useState(config?.is_active ?? true);

  const createMutation = useCreateEmbeddingConfig();
  const updateMutation = useUpdateEmbeddingConfig();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const selectedModel = PROVIDER_MODELS[provider].find((m) => m.name === modelName);
    if (!selectedModel) {
      toast.error('Please select a model');
      return;
    }

    const data = {
      provider,
      model_name: modelName,
      dimensions: selectedModel.dimensions,
      api_key: apiKey || undefined,
      api_endpoint: apiEndpoint || undefined,
      is_default: isDefault,
      is_active: isActive,
    };

    try {
      if (config) {
        await updateMutation.mutateAsync({ id: config.id, data });
        toast.success('Configuration updated');
      } else {
        await createMutation.mutateAsync(data);
        toast.success('Configuration created');
      }
      onOpenChange(false);
    } catch {
      toast.error('Failed to save configuration');
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{config ? 'Edit' : 'Create'} Embedding Configuration</DialogTitle>
          <DialogDescription>Configure embedding provider for vector storage</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="provider">Provider</Label>
            <Select value={provider} onValueChange={(v) => setProvider(v as EmbeddingProvider)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="openai">OpenAI</SelectItem>
                <SelectItem value="cohere">Cohere</SelectItem>
                <SelectItem value="local">Local (Sentence Transformers)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="model">Model</Label>
            <Select value={modelName} onValueChange={setModelName}>
              <SelectTrigger>
                <SelectValue placeholder="Select model" />
              </SelectTrigger>
              <SelectContent>
                {PROVIDER_MODELS[provider].map((model) => (
                  <SelectItem key={model.name} value={model.name}>
                    {model.name} ({model.dimensions}D)
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {provider !== 'local' && (
            <>
              <div className="space-y-2">
                <Label htmlFor="api_key">API Key</Label>
                <Input
                  id="api_key"
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder={config ? 'Leave blank to keep existing' : 'Enter API key'}
                />
              </div>
              {provider === 'openai' && (
                <div className="space-y-2">
                  <Label htmlFor="api_endpoint">API Endpoint (Optional)</Label>
                  <Input
                    id="api_endpoint"
                    value={apiEndpoint}
                    onChange={(e) => setApiEndpoint(e.target.value)}
                    placeholder="https://api.openai.com/v1"
                  />
                </div>
              )}
            </>
          )}

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="is_default"
                checked={isDefault}
                onChange={(e) => setIsDefault(e.target.checked)}
                className="rounded"
              />
              <Label htmlFor="is_default">Set as default</Label>
            </div>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="is_active"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                className="rounded"
              />
              <Label htmlFor="is_active">Active</Label>
            </div>
          </div>

          <div className="flex justify-end space-x-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={createMutation.isPending || updateMutation.isPending}>
              {createMutation.isPending || updateMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                'Save'
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default function KnowledgeTab() {
  const [selectedConfig, setSelectedConfig] = useState<EmbeddingConfig | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const { data: configs, isLoading: configsLoading } = useEmbeddingConfigs();
  const { data: stats, isLoading: statsLoading } = useKnowledgeStats();
  const testMutation = useTestEmbeddingProvider();
  const deleteMutation = useDeleteEmbeddingConfig();

  const handleTest = async (config: EmbeddingConfig) => {
    try {
      const result = await testMutation.mutateAsync({ id: config.id });
      if (result.success) {
        toast.success(`Test passed: ${result.dimensions} dimensions`);
      } else {
        toast.error(`Test failed: ${result.message}`);
      }
    } catch {
      toast.error('Failed to test configuration');
    }
  };

  const handleDelete = async (config: EmbeddingConfig) => {
    if (!confirm('Are you sure you want to delete this configuration?')) {
      return;
    }

    try {
      await deleteMutation.mutateAsync(config.id);
      toast.success('Configuration deleted');
    } catch {
      toast.error('Failed to delete configuration');
    }
  };

  return (
    <div className="space-y-6">
      <Card className="glass">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Knowledge Index Statistics
          </CardTitle>
          <CardDescription>Overview of vector storage index</CardDescription>
        </CardHeader>
        <CardContent>
          {statsLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : stats ? (
            <div className="grid grid-cols-4 gap-4">
              <div>
                <div className="text-2xl font-bold">{stats.total_vectors.toLocaleString()}</div>
                <div className="text-sm text-muted-foreground">Total Vectors</div>
              </div>
              <div>
                <div className="text-2xl font-bold">{stats.policy_documents.toLocaleString()}</div>
                <div className="text-sm text-muted-foreground">Policy Documents</div>
              </div>
              <div>
                <div className="text-2xl font-bold">{stats.deployments.toLocaleString()}</div>
                <div className="text-sm text-muted-foreground">Deployments</div>
              </div>
              <div>
                <div className="text-2xl font-bold">
                  {stats.last_indexed ? new Date(stats.last_indexed).toLocaleDateString() : 'Never'}
                </div>
                <div className="text-sm text-muted-foreground">Last Indexed</div>
              </div>
            </div>
          ) : (
            <div className="text-center text-muted-foreground py-8">No statistics available</div>
          )}
        </CardContent>
      </Card>

      <PermissionGate resource="knowledge_config" action="create">
        <Card className="glass">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Database className="h-5 w-5" />
                  Embedding Configurations
                </CardTitle>
                <CardDescription>Configure embedding providers for vector storage</CardDescription>
              </div>
              <Button onClick={() => setIsDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Add Configuration
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {configsLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : configs && configs.length > 0 ? (
              <div className="space-y-4">
                {configs.map((config) => (
                  <div
                    key={config.id}
                    className="flex items-center justify-between p-4 border rounded-lg"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{config.provider_label}</span>
                        <Badge variant="outline">{config.model_name}</Badge>
                        {config.is_default && (
                          <Badge variant="default">Default</Badge>
                        )}
                        {config.is_active ? (
                          <Badge variant="outline" className="bg-green-500/10 text-green-500">
                            <CheckCircle2 className="mr-1 h-3 w-3" />
                            Active
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="bg-gray-500/10 text-gray-500">
                            <XCircle className="mr-1 h-3 w-3" />
                            Inactive
                          </Badge>
                        )}
                      </div>
                      <div className="text-sm text-muted-foreground mt-1">
                        {config.dimensions} dimensions
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleTest(config)}
                        disabled={testMutation.isPending}
                      >
                        {testMutation.isPending ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          'Test'
                        )}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedConfig(config);
                          setIsDialogOpen(true);
                        }}
                      >
                        Edit
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDelete(config)}
                        disabled={deleteMutation.isPending}
                      >
                        Delete
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-muted-foreground py-8">
                No configurations found. Create one to get started.
              </div>
            )}
          </CardContent>
        </Card>
      </PermissionGate>

      <ConfigDialog
        open={isDialogOpen}
        onOpenChange={(open) => {
          setIsDialogOpen(open);
          if (!open) {
            setSelectedConfig(null);
          }
        }}
        config={selectedConfig}
      />
    </div>
  );
}

// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { useState, useEffect, useRef } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { MinIOConfig } from '@/routes/settings/storage/contracts';

interface MinIOConfigFormProps {
  config?: MinIOConfig | null;
  onChange: (config: MinIOConfig) => void;
}

export function MinIOConfigForm({ config, onChange }: MinIOConfigFormProps) {
  // Initialize from config prop
  const [endpointUrl, setEndpointUrl] = useState(config?.endpoint_url ?? '');
  const [bucketName, setBucketName] = useState(config?.bucket_name ?? '');
  const [accessKeyId, setAccessKeyId] = useState(config?.access_key_id ?? '');
  const [secretAccessKey, setSecretAccessKey] = useState(config?.secret_access_key ?? '');
  const [useSsl, setUseSsl] = useState(config?.use_ssl ?? true);
  const [region, setRegion] = useState(config?.region ?? 'us-east-1');
  const [pathStyle, setPathStyle] = useState(config?.path_style ?? true);

  // Track if this is initial mount to avoid triggering onChange on mount
  const isInitialMount = useRef(true);

  useEffect(() => {
    // Skip initial mount to avoid unnecessary onChange calls
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }

    onChange({
      endpoint_url: endpointUrl,
      bucket_name: bucketName,
      access_key_id: accessKeyId,
      secret_access_key: secretAccessKey,
      use_ssl: useSsl,
      region,
      path_style: pathStyle,
    });
  }, [endpointUrl, bucketName, accessKeyId, secretAccessKey, useSsl, region, pathStyle, onChange]);

  return (
    <div className="space-y-4 border-t pt-4">
      <h3 className="font-semibold">MinIO Configuration</h3>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Endpoint URL *</Label>
          <Input
            value={endpointUrl}
            onChange={(e) => setEndpointUrl(e.target.value)}
            placeholder="http://minio.local:9000"
          />
        </div>
        <div className="space-y-2">
          <Label>Bucket Name *</Label>
          <Input value={bucketName} onChange={(e) => setBucketName(e.target.value)} placeholder="eucora-storage" />
        </div>
        <div className="space-y-2">
          <Label>Access Key ID *</Label>
          <Input
            type="password"
            value={accessKeyId}
            onChange={(e) => setAccessKeyId(e.target.value)}
            placeholder="minioadmin"
          />
        </div>
        <div className="space-y-2">
          <Label>Secret Access Key *</Label>
          <Input
            type="password"
            value={secretAccessKey}
            onChange={(e) => setSecretAccessKey(e.target.value)}
            placeholder="minioadmin"
          />
        </div>
        <div className="space-y-2">
          <Label>Region</Label>
          <Input value={region} onChange={(e) => setRegion(e.target.value)} placeholder="us-east-1" />
        </div>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Switch checked={useSsl} onCheckedChange={setUseSsl} />
          <Label>Use SSL</Label>
        </div>
        <div className="flex items-center gap-2">
          <Switch checked={pathStyle} onCheckedChange={setPathStyle} />
          <Label>Path-Style URLs</Label>
        </div>
      </div>
    </div>
  );
}

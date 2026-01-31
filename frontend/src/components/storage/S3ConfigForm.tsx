// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { useState, useEffect, useRef } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AWSS3Config, AWSAuthMethod } from '@/routes/settings/storage/contracts';

interface S3ConfigFormProps {
  config?: AWSS3Config | null;
  onChange: (config: AWSS3Config) => void;
}

const AWS_REGIONS = [
  'us-east-1',
  'us-east-2',
  'us-west-1',
  'us-west-2',
  'eu-west-1',
  'eu-west-2',
  'eu-central-1',
  'ap-southeast-1',
  'ap-southeast-2',
  'ap-northeast-1',
];

export function S3ConfigForm({ config, onChange }: S3ConfigFormProps) {
  // Initialize from config prop
  const [bucketName, setBucketName] = useState(config?.bucket_name ?? '');
  const [region, setRegion] = useState(config?.region ?? 'us-east-1');
  const [authMethod, setAuthMethod] = useState<AWSAuthMethod>(config?.auth_method ?? 'access_key');
  const [accessKeyId, setAccessKeyId] = useState(config?.access_key_id ?? '');
  const [secretAccessKey, setSecretAccessKey] = useState(config?.secret_access_key ?? '');
  const [roleArn, setRoleArn] = useState(config?.role_arn ?? '');
  const [externalId, setExternalId] = useState(config?.external_id ?? '');
  const [endpointUrl, setEndpointUrl] = useState(config?.endpoint_url ?? '');
  const [kmsKeyId, setKmsKeyId] = useState(config?.kms_key_id ?? '');

  // Track if initial onChange has been called
  const hasCalledInitialOnChange = useRef(false);

  const buildConfig = (): AWSS3Config => {
    const s3Config: AWSS3Config = {
      bucket_name: bucketName,
      region,
      auth_method: authMethod,
      auth_method_label: '',
    };

    if (authMethod === 'access_key') {
      s3Config.access_key_id = accessKeyId;
      s3Config.secret_access_key = secretAccessKey;
    } else if (authMethod === 'assume_role') {
      s3Config.role_arn = roleArn;
      s3Config.external_id = externalId;
    }

    if (endpointUrl) s3Config.endpoint_url = endpointUrl;
    if (kmsKeyId) s3Config.kms_key_id = kmsKeyId;

    return s3Config;
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
  }, [bucketName, region, authMethod, accessKeyId, secretAccessKey, roleArn, externalId, endpointUrl, kmsKeyId]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="space-y-4 border-t pt-4">
      <h3 className="font-semibold">AWS S3 Configuration</h3>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Bucket Name *</Label>
          <Input value={bucketName} onChange={(e) => setBucketName(e.target.value)} placeholder="eucora-storage" />
        </div>
        <div className="space-y-2">
          <Label>AWS Region *</Label>
          <Select value={region} onValueChange={setRegion}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {AWS_REGIONS.map((r) => (
                <SelectItem key={r} value={r}>
                  {r}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2 col-span-2">
          <Label>Authentication Method *</Label>
          <Select value={authMethod} onValueChange={(value: AWSAuthMethod) => setAuthMethod(value)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="access_key">Access Key + Secret</SelectItem>
              <SelectItem value="iam_role">IAM Role (EC2/ECS/EKS)</SelectItem>
              <SelectItem value="assume_role">Assume Role (Cross-Account)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {authMethod === 'access_key' && (
          <>
            <div className="space-y-2">
              <Label>Access Key ID *</Label>
              <Input
                type="password"
                value={accessKeyId}
                onChange={(e) => setAccessKeyId(e.target.value)}
                placeholder="AKIA..."
              />
            </div>
            <div className="space-y-2">
              <Label>Secret Access Key *</Label>
              <Input
                type="password"
                value={secretAccessKey}
                onChange={(e) => setSecretAccessKey(e.target.value)}
                placeholder="..."
              />
            </div>
          </>
        )}

        {authMethod === 'assume_role' && (
          <>
            <div className="space-y-2">
              <Label>Role ARN *</Label>
              <Input
                value={roleArn}
                onChange={(e) => setRoleArn(e.target.value)}
                placeholder="arn:aws:iam::123456789012:role/EUCORAStorage"
              />
            </div>
            <div className="space-y-2">
              <Label>External ID</Label>
              <Input value={externalId} onChange={(e) => setExternalId(e.target.value)} placeholder="Optional" />
            </div>
          </>
        )}

        <div className="space-y-2">
          <Label>Endpoint URL (Optional)</Label>
          <Input
            value={endpointUrl}
            onChange={(e) => setEndpointUrl(e.target.value)}
            placeholder="For S3-compatible services"
          />
        </div>
        <div className="space-y-2">
          <Label>KMS Key ID (Optional)</Label>
          <Input value={kmsKeyId} onChange={(e) => setKmsKeyId(e.target.value)} placeholder="For server-side encryption" />
        </div>
      </div>
    </div>
  );
}

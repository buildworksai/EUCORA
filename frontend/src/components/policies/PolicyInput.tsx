// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface PolicyInputProps {
  label: string;
  description?: string;
  type?: 'text' | 'number' | 'email' | 'url';
  value: string | number;
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  min?: number;
  max?: number;
}

export function PolicyInput({
  label,
  description,
  type = 'text',
  value,
  onChange,
  placeholder,
  disabled,
  min,
  max,
}: PolicyInputProps) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      {description && <p className="text-sm text-muted-foreground">{description}</p>}
      <Input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        min={min}
        max={max}
      />
    </div>
  );
}

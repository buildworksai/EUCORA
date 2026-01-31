// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';

interface PolicyToggleProps {
  label: string;
  description?: string;
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  disabled?: boolean;
}

export function PolicyToggle({ label, description, checked, onCheckedChange, disabled }: PolicyToggleProps) {
  return (
    <div className="flex items-center justify-between space-x-2">
      <div className="space-y-0.5">
        <Label htmlFor={label}>{label}</Label>
        {description && <p className="text-sm text-muted-foreground">{description}</p>}
      </div>
      <Switch id={label} checked={checked} onCheckedChange={onCheckedChange} disabled={disabled} />
    </div>
  );
}

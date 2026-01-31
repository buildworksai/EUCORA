// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { PolicyInput } from './PolicyInput';
import { PolicySection } from './PolicySection';
import { PolicySelect } from './PolicySelect';
import { PolicyToggle } from './PolicyToggle';
import { Download, Trash2, RefreshCw, Settings, Power, Shield } from 'lucide-react';
import { useState } from 'react';

interface PolicySettingsFormProps {
  platform: string;
  settings: Record<string, Record<string, unknown>>;
  onChange: (settings: Record<string, Record<string, unknown>>) => void;
}

export function PolicySettingsForm({ settings, onChange }: PolicySettingsFormProps) {
  const [localSettings, setLocalSettings] = useState<Record<string, Record<string, unknown>>>(settings);

  const updateSetting = (category: string, key: string, value: unknown) => {
    const updated = {
      ...localSettings,
      [category]: {
        ...localSettings[category],
        [key]: value,
      },
    };
    setLocalSettings(updated);
    onChange(updated);
  };

  const getSetting = (category: string, key: string, defaultValue: unknown = false) => {
    return localSettings[category]?.[key] ?? defaultValue;
  };

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Installation Policies */}
      <PolicySection title="Installation" icon={<Download className="w-4 h-4" />}>
        <PolicyToggle
          label="Require Administrator"
          description="Install with admin privileges"
          checked={getSetting('installation', 'require_admin', false) as boolean}
          onCheckedChange={(checked) => updateSetting('installation', 'require_admin', checked)}
        />
        <PolicyToggle
          label="Silent Installation"
          description="Install without user interaction"
          checked={getSetting('installation', 'silent_install', false) as boolean}
          onCheckedChange={(checked) => updateSetting('installation', 'silent_install', checked)}
        />
        <PolicyToggle
          label="Block Manual Installation"
          description="Prevent users from installing outside MDM"
          checked={getSetting('installation', 'block_manual', false) as boolean}
          onCheckedChange={(checked) => updateSetting('installation', 'block_manual', checked)}
        />
      </PolicySection>

      {/* Uninstall Policies */}
      <PolicySection title="Uninstall" icon={<Trash2 className="w-4 h-4" />}>
        <PolicySelect
          label="Uninstall Mode"
          options={[
            { value: 'disabled', label: 'Disabled (Users cannot uninstall)' },
            { value: 'admin_only', label: 'Admin Only' },
            { value: 'user_allowed', label: 'User Allowed' },
          ]}
          value={(getSetting('uninstall', 'mode', 'user_allowed') as string) || 'user_allowed'}
          onValueChange={(value) => updateSetting('uninstall', 'mode', value)}
        />
      </PolicySection>

      {/* Update Policies */}
      <PolicySection title="Updates" icon={<RefreshCw className="w-4 h-4" />}>
        <PolicySelect
          label="Update Mode"
          options={[
            { value: 'auto', label: 'Automatic Updates' },
            { value: 'notify', label: 'Notify Before Update' },
            { value: 'admin_only', label: 'Admin Triggered Only' },
            { value: 'blocked', label: 'Block Updates' },
          ]}
          value={(getSetting('update', 'mode', 'auto') as string) || 'auto'}
          onValueChange={(value) => updateSetting('update', 'mode', value)}
        />
        {getSetting('update', 'mode') !== 'blocked' && (
          <PolicyToggle
            label="Force Updates"
            description="Apply updates without user deferral"
            checked={getSetting('update', 'force_update', false) as boolean}
            onCheckedChange={(checked) => updateSetting('update', 'force_update', checked)}
          />
        )}
      </PolicySection>

      {/* Configuration Enforcement */}
      <PolicySection title="Configuration" icon={<Settings className="w-4 h-4" />}>
        <PolicyToggle
          label="Enforce Configuration"
          description="Apply and maintain settings profile"
          checked={getSetting('configuration', 'enforce', false) as boolean}
          onCheckedChange={(checked) => updateSetting('configuration', 'enforce', checked)}
        />
        <PolicyToggle
          label="Detect Drift"
          description="Report configuration changes"
          checked={getSetting('configuration', 'detect_drift', false) as boolean}
          onCheckedChange={(checked) => updateSetting('configuration', 'detect_drift', checked)}
        />
        {(getSetting('configuration', 'enforce') as boolean) && (
          <PolicyToggle
            label="Auto-Remediate"
            description="Automatically fix drift"
            checked={getSetting('configuration', 'remediate_drift', false) as boolean}
            onCheckedChange={(checked) => updateSetting('configuration', 'remediate_drift', checked)}
          />
        )}
      </PolicySection>

      {/* Restart Policies */}
      <PolicySection title="Device Restart" icon={<Power className="w-4 h-4" />}>
        <PolicySelect
          label="Restart Behavior"
          options={[
            { value: 'none', label: 'No Restart Required' },
            { value: 'prompt', label: 'Prompt User' },
            { value: 'defer', label: 'Allow Deferral' },
            { value: 'force', label: 'Force Restart' },
          ]}
          value={(getSetting('restart', 'mode', 'none') as string) || 'none'}
          onValueChange={(value) => updateSetting('restart', 'mode', value)}
        />
        {getSetting('restart', 'mode') === 'defer' && (
          <PolicyInput
            label="Deferral Period (hours)"
            type="number"
            value={String((getSetting('restart', 'deferral_hours', 4) as number) || 4)}
            onChange={(value) => updateSetting('restart', 'deferral_hours', parseInt(value, 10))}
            min={1}
            max={24}
          />
        )}
        {getSetting('restart', 'mode') === 'force' && (
          <PolicyInput
            label="Grace Period (minutes)"
            type="number"
            value={String((getSetting('restart', 'grace_period_minutes', 15) as number) || 15)}
            onChange={(value) => updateSetting('restart', 'grace_period_minutes', parseInt(value, 10))}
            min={1}
            max={60}
          />
        )}
      </PolicySection>

      {/* Compliance Policies */}
      <PolicySection title="Compliance" icon={<Shield className="w-4 h-4" />}>
        <PolicyToggle
          label="Required for Compliance"
          description="Device marked non-compliant without this app"
          checked={getSetting('compliance', 'required_for_compliance', false) as boolean}
          onCheckedChange={(checked) => updateSetting('compliance', 'required_for_compliance', checked)}
        />
        {(getSetting('compliance', 'required_for_compliance') as boolean) && (
          <PolicyToggle
            label="Conditional Access Integration"
            description="Block resources if app not installed"
            checked={getSetting('compliance', 'conditional_access', false) as boolean}
            onCheckedChange={(checked) => updateSetting('compliance', 'conditional_access', checked)}
          />
        )}
      </PolicySection>
    </div>
  );
}

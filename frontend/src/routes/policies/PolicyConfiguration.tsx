// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { PolicySettingsForm } from '@/components/policies/PolicySettingsForm';
import { TemplatePickerDialog } from '@/components/policies/TemplatePickerDialog';
import { useCreatePolicy } from '@/lib/api/hooks/usePolicies';
import { useState } from 'react';
import { Save } from 'lucide-react';
import type { PolicyTemplate, SettingCategory } from './contracts';

interface PolicyConfigurationProps {
  applicationId: string;
  versionId?: string;
}

export default function PolicyConfiguration({ applicationId, versionId }: PolicyConfigurationProps) {
  const [showTemplates, setShowTemplates] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState('windows');
  const [settings, setSettings] = useState<Record<string, Record<string, unknown>>>({
    installation: {},
    uninstall: {},
    update: {},
    configuration: {},
    restart: {},
    compliance: {},
  });

  const createPolicy = useCreatePolicy();

  const handleSave = async () => {
    try {
      // Check if policy exists (would need to fetch existing policy)
      // For now, create new policy
      await createPolicy.mutateAsync({
        name: `Policy for ${selectedPlatform}`,
        application: applicationId,
        application_version: versionId || null,
        platform: selectedPlatform,
        settings: Object.entries(settings).flatMap(([category, categorySettings]) =>
          Object.entries(categorySettings).map(([key, value]) => ({
            category: category as SettingCategory,
            setting_key: key,
            setting_value: value,
            intune_mapping: {},
            jamf_mapping: {},
            sccm_mapping: {},
          }))
        ),
      });
    } catch {
      // Error already handled by toast notification
    }
  };

  const handleApplyTemplate = (template: PolicyTemplate) => {
    // Apply template settings
    setSettings(template.settings);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Deployment Policies</h2>
          <p className="text-muted-foreground">
            Configure how this application is installed, updated, and managed
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowTemplates(true)}>
            Apply Template
          </Button>
          <Button onClick={handleSave} disabled={createPolicy.isPending}>
            <Save className="w-4 h-4 mr-2" />
            Save Policies
          </Button>
        </div>
      </div>

      {/* Platform Tabs */}
      <Tabs value={selectedPlatform} onValueChange={setSelectedPlatform}>
        <TabsList>
          <TabsTrigger value="windows">Windows</TabsTrigger>
          <TabsTrigger value="macos">macOS</TabsTrigger>
          <TabsTrigger value="linux">Linux</TabsTrigger>
          <TabsTrigger value="ios">iOS</TabsTrigger>
          <TabsTrigger value="android">Android</TabsTrigger>
        </TabsList>

        <TabsContent value="windows">
          <PolicySettingsForm platform="windows" settings={settings} onChange={setSettings} />
        </TabsContent>
        <TabsContent value="macos">
          <PolicySettingsForm platform="macos" settings={settings} onChange={setSettings} />
        </TabsContent>
        <TabsContent value="linux">
          <PolicySettingsForm platform="linux" settings={settings} onChange={setSettings} />
        </TabsContent>
        <TabsContent value="ios">
          <PolicySettingsForm platform="ios" settings={settings} onChange={setSettings} />
        </TabsContent>
        <TabsContent value="android">
          <PolicySettingsForm platform="android" settings={settings} onChange={setSettings} />
        </TabsContent>
      </Tabs>

      {/* Template Picker Dialog */}
      <TemplatePickerDialog
        open={showTemplates}
        onOpenChange={setShowTemplates}
        onSelect={handleApplyTemplate}
        platform={selectedPlatform}
      />
    </div>
  );
}

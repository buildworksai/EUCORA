// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { useState } from 'react';
import { toast } from 'sonner';
import EntraIDIntegration from './integrations/EntraIDIntegration';
import CMDBIntegration from './integrations/CMDBIntegration';
import ITSMIntegration from './integrations/ITSMIntegration';
import MDMIntegration from './integrations/MDMIntegration';
import MonitoringIntegration from './integrations/MonitoringIntegration';
import type { IntegrationsState } from './integrations/types';
import { useAuthStore } from '@/lib/stores/authStore';
import { isDemo } from '@/types/auth';

const defaultIntegrations: IntegrationsState = {
  entraId: {
    tenantId: '',
    clientId: '',
    redirectUri: 'https://eucora.example.com/auth/callback',
    scopes: ['User.Read', 'Directory.Read.All'],
    isConfigured: false,
  },
  cmdb: {
    type: 'servicenow',
    apiUrl: '',
    syncInterval: 60,
    isConfigured: false,
  },
  ticketing: {
    type: 'jira',
    apiUrl: '',
    projectKey: 'EUCORA',
    defaultPriority: 'Medium',
    isConfigured: false,
  },
  mdm: {
    platform: 'abm',
    apiUrl: '',
    organizationId: '',
    serverToken: '',
    syncInterval: 360,
    isConfigured: false,
  },
  monitoring: {
    type: 'datadog',
    apiUrl: '',
    dashboardUrl: '',
    alertWebhook: '',
    isConfigured: false,
  },
};

export default function IntegrationsTab() {
  const { user } = useAuthStore();
  const userIsDemo = isDemo(user);
  const [integrations, setIntegrations] = useState<IntegrationsState>(defaultIntegrations);

  const handleSaveIntegration = (type: keyof IntegrationsState) => {
    if (userIsDemo) {
      toast.info('Integration configuration is disabled in demo mode');
      return;
    }

    setIntegrations((prev) => ({
      ...prev,
      [type]: { ...prev[type], isConfigured: true },
    }));
    toast.success(`${type} integration configured successfully`);
  };

  return (
    <div className="space-y-6">
      <EntraIDIntegration
        config={integrations.entraId}
        onChange={(updates) =>
          setIntegrations((prev) => ({ ...prev, entraId: { ...prev.entraId, ...updates } }))
        }
        onSave={() => handleSaveIntegration('entraId')}
      />
      <CMDBIntegration
        config={integrations.cmdb}
        onChange={(updates) =>
          setIntegrations((prev) => ({ ...prev, cmdb: { ...prev.cmdb, ...updates } }))
        }
        onSave={() => handleSaveIntegration('cmdb')}
      />
      <ITSMIntegration
        config={integrations.ticketing}
        onChange={(updates) =>
          setIntegrations((prev) => ({ ...prev, ticketing: { ...prev.ticketing, ...updates } }))
        }
        onSave={() => handleSaveIntegration('ticketing')}
      />
      <MDMIntegration
        config={integrations.mdm}
        onChange={(updates) =>
          setIntegrations((prev) => ({ ...prev, mdm: { ...prev.mdm, ...updates } }))
        }
        onSave={() => handleSaveIntegration('mdm')}
      />
      <MonitoringIntegration
        config={integrations.monitoring}
        onChange={(updates) =>
          setIntegrations((prev) => ({ ...prev, monitoring: { ...prev.monitoring, ...updates } }))
        }
        onSave={() => handleSaveIntegration('monitoring')}
      />
    </div>
  );
}

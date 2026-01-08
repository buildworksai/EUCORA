// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * Settings page with Profile, AI Providers, User Management, and Integrations.
 */
import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Settings as SettingsIcon, Sparkles } from 'lucide-react';
import { useAuthStore } from '@/lib/stores/authStore';
import { isAdmin, isDemo } from '@/types/auth';
import ProfileTab from './ProfileTab';
import AIProvidersTab from './AIProvidersTab';
import UsersTab from './UsersTab';
import IntegrationsTab from './IntegrationsTab';

export default function Settings() {
  const [searchParams, setSearchParams] = useSearchParams();
  const tabFromUrl = searchParams.get('tab') || 'profile';

  const { user } = useAuthStore();
  const userIsAdmin = isAdmin(user);
  const userIsDemo = isDemo(user);

  const [activeTab, setActiveTab] = useState(tabFromUrl);

  useEffect(() => {
    setActiveTab(tabFromUrl);
  }, [tabFromUrl]);

  const handleTabChange = useCallback(
    (tab: string) => {
      setActiveTab(tab);
      setSearchParams({ tab });
    },
    [setSearchParams]
  );

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight flex items-center gap-3">
          <SettingsIcon className="h-8 w-8 text-eucora-teal" />
          Settings
        </h2>
        <p className="text-muted-foreground mt-1">
          Manage your preferences, integrations, and system configurations.
        </p>
      </div>

      {userIsDemo && (
        <div className="flex items-center gap-3 p-4 bg-eucora-teal/10 border border-eucora-teal/20 rounded-lg">
          <Sparkles className="h-5 w-5 text-eucora-teal" />
          <div>
            <p className="text-sm font-medium text-eucora-teal">Demo Mode Active</p>
            <p className="text-xs text-muted-foreground">
              Configuration changes are view-only in demo mode.
            </p>
          </div>
        </div>
      )}

      <Tabs value={activeTab} className="space-y-6" onValueChange={handleTabChange}>
        <TabsList className={`glass grid w-full ${userIsAdmin ? 'grid-cols-4' : 'grid-cols-2'}`}>
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="ai">AI Providers</TabsTrigger>
          {userIsAdmin && <TabsTrigger value="users">Users</TabsTrigger>}
          {userIsAdmin && <TabsTrigger value="integrations">Integrations</TabsTrigger>}
        </TabsList>

        <TabsContent value="profile" className="space-y-6">
          <ProfileTab />
        </TabsContent>
        <TabsContent value="ai" className="space-y-6">
          <AIProvidersTab />
        </TabsContent>
        {userIsAdmin && (
          <TabsContent value="users" className="space-y-6">
            <UsersTab />
          </TabsContent>
        )}
        {userIsAdmin && (
          <TabsContent value="integrations" className="space-y-6">
            <IntegrationsTab />
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
}

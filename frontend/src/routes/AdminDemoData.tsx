// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { useAuthStore } from '@/lib/stores/authStore';
import { isAdmin } from '@/types/auth';
import {
  useClearDemoData,
  useDemoDataStats,
  useDemoMode,
  useSeedDemoData,
  useSetDemoMode,
} from '@/lib/api/hooks/useDemoData';

export default function AdminDemoData() {
  const { user } = useAuthStore();
  const userIsAdmin = isAdmin(user);

  const { data: statsData, isLoading: statsLoading, refetch: refetchStats } = useDemoDataStats();
  const { data: demoModeData, refetch: refetchDemoMode } = useDemoMode();
  const seedMutation = useSeedDemoData();
  const clearMutation = useClearDemoData();
  const setDemoModeMutation = useSetDemoMode();

  const [formState, setFormState] = useState({
    assets: 50000,
    applications: 5000,
    deployments: 10000,
    users: 1000,
    events: 100000,
    batch_size: 1000,
    clear_existing: true,
  });

  if (!userIsAdmin) {
    return <Navigate to="/dashboard" replace />;
  }

  // api.get returns the response directly, not wrapped in data
  const counts = statsData?.counts;
  const demoModeEnabled = demoModeData?.demo_mode_enabled ?? false;

  const handleSeed = async () => {
    try {
      const result = await seedMutation.mutateAsync(formState);
      // Refetch stats to show updated counts
      await refetchStats();
      if (result.status === 'queued') {
        toast.success('Demo data seeding started in background. Check stats for progress.');
      } else {
        toast.success('Demo data seeding completed');
      }
    } catch (error) {
      console.error('Seeding error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to seed demo data';
      toast.error(errorMessage);
      // Refetch anyway to show current state
      await refetchStats();
    }
  };

  const handleClear = async () => {
    try {
      await clearMutation.mutateAsync();
      toast.success('Demo data cleared');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to clear demo data');
    }
  };

  const handleDemoModeToggle = async (enabled: boolean) => {
    try {
      const result = await setDemoModeMutation.mutateAsync(enabled);
      // Verify the result matches what we sent
      if (result?.demo_mode_enabled === enabled) {
        // Manually refetch to ensure UI updates
        await Promise.all([refetchDemoMode(), refetchStats()]);
        toast.success(`Demo mode ${enabled ? 'enabled' : 'disabled'}`);
      } else {
        // Still refetch even if result doesn't match
        await Promise.all([refetchDemoMode(), refetchStats()]);
        toast.warning(`Demo mode toggle may not have applied. Current state: ${result?.demo_mode_enabled}`);
      }
    } catch (error) {
      console.error('Demo mode toggle error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to update demo mode';
      toast.error(errorMessage);
      // Refetch anyway to get current state
      await Promise.all([refetchDemoMode(), refetchStats()]);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Demo Data Administration</h2>
          <p className="text-muted-foreground">
            Seed, reset, and toggle demo data across the platform.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">Demo Mode</span>
          <Switch
            checked={demoModeEnabled}
            onCheckedChange={handleDemoModeToggle}
            disabled={setDemoModeMutation.isPending}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="glass">
          <CardHeader>
            <CardTitle>Assets</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">
              {statsLoading ? '—' : counts?.assets.toLocaleString() ?? 0}
            </div>
          </CardContent>
        </Card>
        <Card className="glass">
          <CardHeader>
            <CardTitle>Applications</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">
              {statsLoading ? '—' : counts?.applications.toLocaleString() ?? 0}
            </div>
          </CardContent>
        </Card>
        <Card className="glass">
          <CardHeader>
            <CardTitle>Deployments</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold">
              {statsLoading ? '—' : counts?.deployments.toLocaleString() ?? 0}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card className="glass">
          <CardHeader>
            <CardTitle>Ring Deployments</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold">
              {statsLoading ? '—' : counts?.ring_deployments.toLocaleString() ?? 0}
            </div>
          </CardContent>
        </Card>
        <Card className="glass">
          <CardHeader>
            <CardTitle>CAB Approvals</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold">
              {statsLoading ? '—' : counts?.cab_approvals.toLocaleString() ?? 0}
            </div>
          </CardContent>
        </Card>
        <Card className="glass">
          <CardHeader>
            <CardTitle>Evidence Packs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold">
              {statsLoading ? '—' : counts?.evidence_packs.toLocaleString() ?? 0}
            </div>
          </CardContent>
        </Card>
        <Card className="glass">
          <CardHeader>
            <CardTitle>Events</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold">
              {statsLoading ? '—' : counts?.events.toLocaleString() ?? 0}
            </div>
          </CardContent>
        </Card>
        <Card className="glass">
          <CardHeader>
            <CardTitle>Users</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-semibold">
              {statsLoading ? '—' : counts?.users.toLocaleString() ?? 0}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="glass">
        <CardHeader>
          <CardTitle>Seed Demo Data</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { key: 'assets', label: 'Assets' },
            { key: 'applications', label: 'Applications' },
            { key: 'deployments', label: 'Deployments' },
            { key: 'users', label: 'Users' },
            { key: 'events', label: 'Events' },
            { key: 'batch_size', label: 'Batch Size' },
          ].map((field) => (
            <div key={field.key} className="space-y-2">
              <Label htmlFor={field.key}>{field.label}</Label>
              <Input
                id={field.key}
                type="number"
                min={1}
                value={String(formState[field.key as keyof typeof formState] ?? '')}
                onChange={(event) =>
                  setFormState((prev) => ({
                    ...prev,
                    [field.key]: Number(event.target.value),
                  }))
                }
              />
            </div>
          ))}
          <div className="flex items-center gap-3 mt-2">
            <Switch
              checked={formState.clear_existing}
              onCheckedChange={(value) =>
                setFormState((prev) => ({ ...prev, clear_existing: value }))
              }
            />
            <span className="text-sm text-muted-foreground">Clear existing demo data before seeding</span>
          </div>
          <div className="md:col-span-3 flex items-center justify-end gap-3">
            <Button
              className="bg-eucora-deepBlue text-white"
              onClick={handleSeed}
              disabled={seedMutation.isPending}
            >
              {seedMutation.isPending ? 'Seeding...' : 'Seed Demo Data'}
            </Button>
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="destructive" disabled={clearMutation.isPending}>
                  {clearMutation.isPending ? 'Clearing...' : 'Clear Demo Data'}
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Clear demo data?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This removes demo-only assets, applications, deployments, evidence packs, and events.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction onClick={handleClear}>Confirm</AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

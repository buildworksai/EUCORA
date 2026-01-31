// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * E14: Discovery Agent Dashboard
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  Search,
  Package,
  AlertTriangle,
  CheckCircle,
  Shield,
  BarChart3,
  Play,
  Eye,
  Ban,
} from 'lucide-react';
import { api } from '@/lib/api/client';
import {
  ENDPOINTS,
  type NormalizedApplication,
  type LicenseGap,
  type PatchGap,
  type DiscoveryDashboardData,
} from './contracts';

// Stat Card Component
function StatCard({
  icon: Icon,
  label,
  value,
  subtext,
  color,
}: {
  icon: React.ElementType;
  label: string;
  value: number | string;
  subtext?: string;
  color: string;
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-2xl font-bold">{value}</p>
          {subtext && <p className="text-xs text-gray-400">{subtext}</p>}
        </div>
      </div>
    </div>
  );
}

// Application Card Component
function ApplicationCard({
  app,
  onApprove,
  onRestrict,
}: {
  app: NormalizedApplication;
  onApprove: (id: string) => void;
  onRestrict: (id: string) => void;
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Package className="h-5 w-5 text-blue-500" />
            <h4 className="font-medium">{app.name}</h4>
          </div>
          <p className="text-sm text-gray-500 mt-1">{app.publisher}</p>
        </div>
        <div className="flex items-center gap-2">
          {app.is_approved && (
            <span className="px-2 py-0.5 bg-green-100 text-green-800 rounded-full text-xs">
              Approved
            </span>
          )}
          {app.is_restricted && (
            <span className="px-2 py-0.5 bg-red-100 text-red-800 rounded-full text-xs">
              Restricted
            </span>
          )}
          {!app.is_managed && !app.is_approved && (
            <span className="px-2 py-0.5 bg-yellow-100 text-yellow-800 rounded-full text-xs">
              Shadow IT
            </span>
          )}
        </div>
      </div>
      <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
        <span>{app.total_installs} installs</span>
        <span>{app.version_count} versions</span>
        {app.latest_version && <span>v{app.latest_version}</span>}
      </div>
      <div className="mt-3 flex items-center gap-2">
        {app.license_gap_count > 0 && (
          <span className="flex items-center gap-1 text-xs text-yellow-600">
            <AlertTriangle className="h-3 w-3" />
            {app.license_gap_count} license gaps
          </span>
        )}
        {app.patch_gap_count > 0 && (
          <span className="flex items-center gap-1 text-xs text-red-600">
            <Shield className="h-3 w-3" />
            {app.patch_gap_count} patch gaps
          </span>
        )}
      </div>
      {!app.is_approved && !app.is_restricted && (
        <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700 flex gap-2">
          <button
            onClick={() => onApprove(app.id)}
            className="flex items-center gap-1 px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200"
          >
            <CheckCircle className="h-3 w-3" />
            Approve
          </button>
          <button
            onClick={() => onRestrict(app.id)}
            className="flex items-center gap-1 px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200"
          >
            <Ban className="h-3 w-3" />
            Restrict
          </button>
        </div>
      )}
    </div>
  );
}

// License Gap Row Component
function LicenseGapRow({
  gap,
  onAcknowledge,
  onResolve,
}: {
  gap: LicenseGap;
  onAcknowledge: (id: string) => void;
  onResolve: (id: string) => void;
}) {
  const riskColors: Record<string, string> = {
    critical: 'bg-red-100 text-red-800',
    high: 'bg-orange-100 text-orange-800',
    medium: 'bg-yellow-100 text-yellow-800',
    low: 'bg-green-100 text-green-800',
  };

  return (
    <tr className="border-b border-gray-200 dark:border-gray-700">
      <td className="py-3 px-4 text-sm">{gap.application_name}</td>
      <td className="py-3 px-4 text-sm">{gap.gap_type.replace('_', ' ')}</td>
      <td className="py-3 px-4">
        <span className={`px-2 py-0.5 rounded-full text-xs ${riskColors[gap.risk_level]}`}>
          {gap.risk_level}
        </span>
      </td>
      <td className="py-3 px-4 text-sm">
        {gap.detected_installs} / {gap.licensed_count}
      </td>
      <td className="py-3 px-4 text-sm font-medium text-red-600">
        {gap.gap_count > 0 ? `+${gap.gap_count}` : gap.gap_count}
      </td>
      <td className="py-3 px-4 text-sm">
        {gap.estimated_cost ? `$${gap.estimated_cost.toLocaleString()}` : '-'}
      </td>
      <td className="py-3 px-4">
        {gap.status === 'open' && (
          <div className="flex gap-2">
            <button
              onClick={() => onAcknowledge(gap.id)}
              className="text-xs text-blue-600 hover:underline"
            >
              Acknowledge
            </button>
            <button
              onClick={() => onResolve(gap.id)}
              className="text-xs text-green-600 hover:underline"
            >
              Resolve
            </button>
          </div>
        )}
        {gap.status !== 'open' && (
          <span className="text-xs text-gray-500">{gap.status}</span>
        )}
      </td>
    </tr>
  );
}

// Patch Gap Row Component
function PatchGapRow({ gap, onPlan }: { gap: PatchGap; onPlan: (id: string) => void }) {
  const severityColors: Record<string, string> = {
    critical: 'bg-red-100 text-red-800',
    high: 'bg-orange-100 text-orange-800',
    medium: 'bg-yellow-100 text-yellow-800',
    low: 'bg-green-100 text-green-800',
  };

  return (
    <tr className="border-b border-gray-200 dark:border-gray-700">
      <td className="py-3 px-4 text-sm">{gap.application_name}</td>
      <td className="py-3 px-4 text-sm">{gap.gap_type.replace('_', ' ')}</td>
      <td className="py-3 px-4">
        <span className={`px-2 py-0.5 rounded-full text-xs ${severityColors[gap.severity]}`}>
          {gap.severity}
        </span>
      </td>
      <td className="py-3 px-4 text-sm">
        {gap.current_version_str}
        {gap.target_version_str && (
          <span className="text-gray-400"> → {gap.target_version_str}</span>
        )}
      </td>
      <td className="py-3 px-4 text-sm">{gap.affected_devices}</td>
      <td className="py-3 px-4 text-sm">
        {gap.cve_ids.length > 0 && (
          <span className="text-red-600">{gap.cve_ids.length} CVEs</span>
        )}
      </td>
      <td className="py-3 px-4">
        {gap.status === 'open' && (
          <button
            onClick={() => onPlan(gap.id)}
            className="text-xs text-blue-600 hover:underline"
          >
            Plan Remediation
          </button>
        )}
        {gap.status !== 'open' && (
          <span className="text-xs text-gray-500">{gap.status}</span>
        )}
      </td>
    </tr>
  );
}

export default function DiscoveryDashboard() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<
    'overview' | 'applications' | 'license-gaps' | 'patch-gaps' | 'shadow-it'
  >('overview');
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch dashboard data
  const { data: dashboard } = useQuery({
    queryKey: ['discovery-dashboard'],
    queryFn: () => api.get<DiscoveryDashboardData>(ENDPOINTS.dashboard),
  });

  // Fetch applications
  const { data: applications = [] } = useQuery({
    queryKey: ['normalized-applications', searchQuery],
    queryFn: () => {
      const params = searchQuery ? `?search=${encodeURIComponent(searchQuery)}` : '';
      return api.get<NormalizedApplication[]>(`${ENDPOINTS.applications}${params}`);
    },
  });

  // Fetch license gaps
  const { data: licenseGaps = [] } = useQuery({
    queryKey: ['license-gaps'],
    queryFn: () => api.get<LicenseGap[]>(ENDPOINTS.licenseGaps),
  });

  // Fetch patch gaps
  const { data: patchGaps = [] } = useQuery({
    queryKey: ['patch-gaps'],
    queryFn: () => api.get<PatchGap[]>(ENDPOINTS.patchGaps),
  });

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: (id: string) => api.post<NormalizedApplication>(ENDPOINTS.applicationApprove(id), {}),
    onSuccess: () => {
      toast.success('Application approved');
      queryClient.invalidateQueries({ queryKey: ['normalized-applications'] });
      queryClient.invalidateQueries({ queryKey: ['discovery-dashboard'] });
    },
  });

  // Restrict mutation
  const restrictMutation = useMutation({
    mutationFn: (id: string) => api.post<NormalizedApplication>(ENDPOINTS.applicationRestrict(id), {}),
    onSuccess: () => {
      toast.success('Application restricted');
      queryClient.invalidateQueries({ queryKey: ['normalized-applications'] });
      queryClient.invalidateQueries({ queryKey: ['discovery-dashboard'] });
    },
  });

  // Acknowledge license gap mutation
  const acknowledgeMutation = useMutation({
    mutationFn: (id: string) => api.post<LicenseGap>(ENDPOINTS.licenseGapAcknowledge(id), {}),
    onSuccess: () => {
      toast.success('License gap acknowledged');
      queryClient.invalidateQueries({ queryKey: ['license-gaps'] });
    },
  });

  // Resolve license gap mutation
  const resolveMutation = useMutation({
    mutationFn: (id: string) => api.post<LicenseGap>(ENDPOINTS.licenseGapResolve(id), {}),
    onSuccess: () => {
      toast.success('License gap resolved');
      queryClient.invalidateQueries({ queryKey: ['license-gaps'] });
    },
  });

  // Plan patch gap mutation
  const planMutation = useMutation({
    mutationFn: (id: string) => api.post<PatchGap>(ENDPOINTS.patchGapPlan(id), {}),
    onSuccess: () => {
      toast.success('Remediation planned');
      queryClient.invalidateQueries({ queryKey: ['patch-gaps'] });
    },
  });

  const shadowItApps = applications.filter((app: NormalizedApplication) => !app.is_managed && !app.is_approved);
  const openLicenseGaps = licenseGaps.filter((g: LicenseGap) => g.status === 'open');
  const openPatchGaps = patchGaps.filter((g: PatchGap) => g.status === 'open');

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Search className="h-6 w-6 text-green-500" />
            Discovery Agent
          </h1>
          <p className="text-gray-500 mt-1">
            Discover, normalize, and analyze applications across your environment
          </p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
          <Play className="h-4 w-4" />
          Run Discovery
        </button>
      </div>

      {/* Stats */}
      {dashboard && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            icon={Package}
            label="Total Applications"
            value={dashboard.total_applications}
            subtext={`${dashboard.managed_applications} managed`}
            color="bg-blue-100 text-blue-600"
          />
          <StatCard
            icon={Eye}
            label="Shadow IT"
            value={dashboard.shadow_it_count}
            color="bg-yellow-100 text-yellow-600"
          />
          <StatCard
            icon={AlertTriangle}
            label="License Gaps"
            value={dashboard.license_gaps_count}
            color="bg-orange-100 text-orange-600"
          />
          <StatCard
            icon={Shield}
            label="Patch Gaps"
            value={dashboard.patch_gaps_count}
            color="bg-red-100 text-red-600"
          />
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="flex gap-4">
          {(
            ['overview', 'applications', 'license-gaps', 'patch-gaps', 'shadow-it'] as const
          ).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`pb-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab
                  ? 'border-green-500 text-green-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab
                .split('-')
                .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                .join(' ')}
              {tab === 'shadow-it' && shadowItApps.length > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-yellow-100 text-yellow-800 rounded-full text-xs">
                  {shadowItApps.length}
                </span>
              )}
              {tab === 'license-gaps' && openLicenseGaps.length > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-orange-100 text-orange-800 rounded-full text-xs">
                  {openLicenseGaps.length}
                </span>
              )}
              {tab === 'patch-gaps' && openPatchGaps.length > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-red-100 text-red-800 rounded-full text-xs">
                  {openPatchGaps.length}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Applications by Category */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-blue-500" />
              Applications by Category
            </h3>
            {dashboard && Object.keys(dashboard.applications_by_category).length > 0 ? (
              <div className="space-y-2">
                {Object.entries(dashboard.applications_by_category).map(([category, count]) => (
                  <div key={category} className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">{category || 'Uncategorized'}</span>
                    <span className="font-medium">{count as number}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No category data available</p>
            )}
          </div>

          {/* Risk Distribution */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <Shield className="h-5 w-5 text-red-500" />
              Risk Distribution
            </h3>
            {dashboard && Object.keys(dashboard.risk_distribution).length > 0 ? (
              <div className="space-y-2">
                {Object.entries(dashboard.risk_distribution).map(([level, count]) => {
                  const colors: Record<string, string> = {
                    critical: 'text-red-600',
                    high: 'text-orange-600',
                    medium: 'text-yellow-600',
                    low: 'text-green-600',
                  };
                  return (
                    <div key={level} className="flex justify-between items-center">
                      <span className={`text-sm font-medium ${colors[level] || ''}`}>
                        {level.charAt(0).toUpperCase() + level.slice(1)}
                      </span>
                      <span className="font-medium">{count as number}</span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No risk data available</p>
            )}
          </div>
        </div>
      )}

      {/* Applications Tab */}
      {activeTab === 'applications' && (
        <div>
          <div className="mb-4">
            <input
              type="text"
              placeholder="Search applications..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full max-w-md px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {applications.map((app: NormalizedApplication) => (
              <ApplicationCard
                key={app.id}
                app={app}
                onApprove={(id) => approveMutation.mutate(id)}
                onRestrict={(id) => restrictMutation.mutate(id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* License Gaps Tab */}
      {activeTab === 'license-gaps' && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Application
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Gap Type
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Risk
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Installs / Licensed
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Gap
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Est. Cost
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {licenseGaps.map((gap: LicenseGap) => (
                  <LicenseGapRow
                    key={gap.id}
                    gap={gap}
                    onAcknowledge={(id) => acknowledgeMutation.mutate(id)}
                    onResolve={(id) => resolveMutation.mutate(id)}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Patch Gaps Tab */}
      {activeTab === 'patch-gaps' && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Application
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Gap Type
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Severity
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Version
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Affected Devices
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    CVEs
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {patchGaps.map((gap: PatchGap) => (
                  <PatchGapRow key={gap.id} gap={gap} onPlan={(id) => planMutation.mutate(id)} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Shadow IT Tab */}
      {activeTab === 'shadow-it' && (
        <div>
          <div className="mb-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
            <div className="flex items-center gap-2 text-yellow-800 dark:text-yellow-200">
              <AlertTriangle className="h-5 w-5" />
              <span className="font-medium">Shadow IT Applications</span>
            </div>
            <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
              These applications are detected in your environment but are not managed or approved.
              Review and take action to either approve for use or restrict.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {shadowItApps.map((app: NormalizedApplication) => (
              <ApplicationCard
                key={app.id}
                app={app}
                onApprove={(id) => approveMutation.mutate(id)}
                onRestrict={(id) => restrictMutation.mutate(id)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

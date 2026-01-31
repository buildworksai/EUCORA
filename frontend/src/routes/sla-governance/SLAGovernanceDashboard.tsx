// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * E19: SLA Governance Dashboard
 */
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Target, AlertTriangle, CheckCircle, TrendingUp, RefreshCw } from 'lucide-react';
import { api } from '@/lib/api/client';
import {
  ENDPOINTS,
  type SLASummaryReport,
  type SLACompliance,
  type SLABreach,
} from './contracts';

export default function SLAGovernanceDashboard() {
  const queryClient = useQueryClient();

  const { data: summary } = useQuery<SLASummaryReport>({
    queryKey: ['sla-governance', 'summary'],
    queryFn: () => api.get<SLASummaryReport>(ENDPOINTS.reportsSummary),
  });

  const { data: atRisk } = useQuery<SLACompliance[]>({
    queryKey: ['sla-governance', 'at-risk'],
    queryFn: async () => {
      const response = await api.get<{ results: SLACompliance[] } | SLACompliance[]>(ENDPOINTS.complianceAtRisk);
      return Array.isArray(response) ? response : response.results || [];
    },
  });

  const { data: breaches } = useQuery<SLABreach[]>({
    queryKey: ['sla-governance', 'breaches'],
    queryFn: async () => {
      const response = await api.get<{ results: SLABreach[] } | SLABreach[]>(ENDPOINTS.breaches + '?limit=10');
      return Array.isArray(response) ? response : response.results || [];
    },
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'compliant':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'at_risk':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'breached':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'high':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      default:
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">SLA Governance</h1>
        <button
          onClick={() => queryClient.invalidateQueries({ queryKey: ['sla-governance'] })}
          className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg flex items-center gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <Target className="h-5 w-5 text-blue-500" />
            <h3 className="font-semibold">Total SLAs</h3>
          </div>
          <p className="text-3xl font-bold">{summary?.total_slas || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="h-5 w-5 text-green-500" />
            <h3 className="font-semibold">Active SLAs</h3>
          </div>
          <p className="text-3xl font-bold text-green-600">{summary?.active_slas || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="h-5 w-5 text-yellow-500" />
            <h3 className="font-semibold">At Risk</h3>
          </div>
          <p className="text-3xl font-bold text-yellow-600">{summary?.at_risk_count || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="h-5 w-5 text-red-500" />
            <h3 className="font-semibold">Breaches</h3>
          </div>
          <p className="text-3xl font-bold text-red-600">{summary?.breach_count || 0}</p>
        </div>
      </div>

      {/* At-Risk SLAs */}
      <section>
        <h2 className="text-lg font-semibold mb-4">SLAs At Risk</h2>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  SLA
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Compliance
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Period
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {atRisk?.map((compliance: SLACompliance) => (
                <tr key={compliance.id}>
                  <td className="px-6 py-4 whitespace-nowrap">{compliance.sla_name}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {compliance.overall_compliance.toFixed(1)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 rounded text-xs ${getStatusColor(compliance.status)}`}>
                      {compliance.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {compliance.period_start} to {compliance.period_end}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Recent Breaches */}
      <section>
        <h2 className="text-lg font-semibold mb-4">Recent Breaches</h2>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  SLA
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Target
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Severity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Breach Time
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {breaches?.map((breach: SLABreach) => (
                <tr key={breach.id}>
                  <td className="px-6 py-4 whitespace-nowrap">{breach.sla_name}</td>
                  <td className="px-6 py-4 whitespace-nowrap">{breach.target_name}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 rounded text-xs ${getSeverityColor(breach.severity)}`}>
                      {breach.severity}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {new Date(breach.breach_time).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

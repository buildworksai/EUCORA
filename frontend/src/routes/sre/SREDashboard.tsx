// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * E18: SRE Dashboard
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { HeartPulse, Activity, TrendingUp, Wrench, RefreshCw, Play } from 'lucide-react';
import { api } from '@/lib/api/client';
import { ENDPOINTS, type SREOverview, type HealthEndpoint, type SelfHealingExecution } from './contracts';

export default function SREDashboard() {
  const queryClient = useQueryClient();

  const { data: overview } = useQuery({
    queryKey: ['sre', 'overview'],
    queryFn: () => api.get<SREOverview>(ENDPOINTS.reportsOverview),
  });

  const { data: endpoints } = useQuery({
    queryKey: ['sre', 'health-endpoints'],
    queryFn: async () => {
      const response = await api.get<{ results: HealthEndpoint[] } | HealthEndpoint[]>(ENDPOINTS.healthEndpoints + '?is_active=true');
      return Array.isArray(response) ? response : response.results || [];
    },
  });

  const { data: healingExecutions } = useQuery({
    queryKey: ['sre', 'healing-executions'],
    queryFn: async () => {
      const response = await api.get<{ results: SelfHealingExecution[] } | SelfHealingExecution[]>(ENDPOINTS.selfHealingExecutions + '?status=pending&limit=10');
      return Array.isArray(response) ? response : response.results || [];
    },
  });

  const checkHealthMutation = useMutation({
    mutationFn: async (id: string) => {
      return api.post(ENDPOINTS.healthEndpointCheck(id), {});
    },
    onSuccess: () => {
      toast.success('Health check completed');
      queryClient.invalidateQueries({ queryKey: ['sre'] });
    },
  });

  const getHealthColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'degraded':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'unhealthy':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">SRE</h1>
        <button
          onClick={() => queryClient.invalidateQueries({ queryKey: ['sre'] })}
          className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg flex items-center gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* System Health Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <HeartPulse className="h-5 w-5 text-green-500" />
            <h3 className="font-semibold">Healthy</h3>
          </div>
          <p className="text-3xl font-bold text-green-600">{overview?.healthy_endpoints || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <Activity className="h-5 w-5 text-red-500" />
            <h3 className="font-semibold">Unhealthy</h3>
          </div>
          <p className="text-3xl font-bold text-red-600">{overview?.unhealthy_endpoints || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="h-5 w-5 text-blue-500" />
            <h3 className="font-semibold">Active SLOs</h3>
          </div>
          <p className="text-3xl font-bold text-blue-600">{overview?.active_slos || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <Wrench className="h-5 w-5 text-purple-500" />
            <h3 className="font-semibold">Healing Rules</h3>
          </div>
          <p className="text-3xl font-bold text-purple-600">{overview?.active_healing_rules || 0}</p>
        </div>
      </div>

      {/* Self-Healing Activity */}
      {healingExecutions && healingExecutions.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-4">Pending Self-Healing Executions</h2>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium">Rule</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Triggered</th>
                </tr>
              </thead>
              <tbody>
                {healingExecutions.slice(0, 10).map((execution: SelfHealingExecution) => (
                  <tr key={execution.id} className="border-t border-gray-200 dark:border-gray-700">
                    <td className="px-4 py-3 text-sm">{execution.rule_name}</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-1 rounded text-xs bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">
                        {execution.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">{new Date(execution.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Health Endpoints */}
      <section>
        <h2 className="text-lg font-semibold mb-4">Health Endpoints</h2>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium">Name</th>
                <th className="px-4 py-3 text-left text-sm font-medium">URL</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Interval</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {endpoints?.slice(0, 20).map((endpoint: HealthEndpoint) => (
                <tr key={endpoint.id} className="border-t border-gray-200 dark:border-gray-700">
                  <td className="px-4 py-3 text-sm font-medium">{endpoint.name}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{endpoint.url}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs ${getHealthColor(endpoint.last_check_status)}`}>
                      {endpoint.last_check_status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">{endpoint.check_interval_minutes} min</td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => checkHealthMutation.mutate(endpoint.id)}
                      disabled={checkHealthMutation.isPending}
                      className="px-3 py-1 bg-blue-100 hover:bg-blue-200 text-blue-700 rounded text-sm flex items-center gap-1 disabled:opacity-50"
                    >
                      <Play className="h-3 w-3" />
                      Check
                    </button>
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

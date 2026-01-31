// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * E20: Planning Dashboard
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { CalendarClock, CheckCircle, Clock, AlertCircle, RefreshCw } from 'lucide-react';
import { api } from '@/lib/api/client';
import {
  ENDPOINTS,
  type PlanningSummaryReport,
  type DeploymentPlan,
} from './contracts';

export default function PlanningDashboard() {
  const queryClient = useQueryClient();

  const { data: summary } = useQuery<PlanningSummaryReport>({
    queryKey: ['planning', 'summary'],
    queryFn: () => api.get<PlanningSummaryReport>(ENDPOINTS.reportsSummary),
  });

  const { data: plans } = useQuery<DeploymentPlan[]>({
    queryKey: ['planning', 'plans'],
    queryFn: async () => {
      const response = await api.get<{ results: DeploymentPlan[] } | DeploymentPlan[]>(ENDPOINTS.plans + '?status=executing&status=approved');
      return Array.isArray(response) ? response : response.results || [];
    },
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'executing':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'pending_approval':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'completed':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  const approveMutation = useMutation({
    mutationFn: async (id: string) => {
      return api.post(ENDPOINTS.planApprove(id), {});
    },
    onSuccess: () => {
      toast.success('Plan approved');
      queryClient.invalidateQueries({ queryKey: ['planning'] });
    },
  });

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Planning</h1>
        <button
          onClick={() => queryClient.invalidateQueries({ queryKey: ['planning'] })}
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
            <CalendarClock className="h-5 w-5 text-blue-500" />
            <h3 className="font-semibold">Total Plans</h3>
          </div>
          <p className="text-3xl font-bold">{summary?.total_plans || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="h-5 w-5 text-blue-500" />
            <h3 className="font-semibold">Active Plans</h3>
          </div>
          <p className="text-3xl font-bold text-blue-600">{summary?.active_plans || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="h-5 w-5 text-green-500" />
            <h3 className="font-semibold">Approved</h3>
          </div>
          <p className="text-3xl font-bold text-green-600">{summary?.approved_plans || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="h-5 w-5 text-gray-500" />
            <h3 className="font-semibold">Completed</h3>
          </div>
          <p className="text-3xl font-bold">{summary?.completed_plans || 0}</p>
        </div>
      </div>

      {/* Active Plans */}
      <section>
        <h2 className="text-lg font-semibold mb-4">Active Plans</h2>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Plan Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Application
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Version
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Risk Score
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {plans?.map((plan: DeploymentPlan) => (
                <tr key={plan.id}>
                  <td className="px-6 py-4 whitespace-nowrap">{plan.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap">{plan.application_name}</td>
                  <td className="px-6 py-4 whitespace-nowrap">{plan.version}</td>
                  <td className="px-6 py-4 whitespace-nowrap">{plan.overall_risk_score.toFixed(1)}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 rounded text-xs ${getStatusColor(plan.status)}`}>
                      {plan.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {plan.status === 'pending_approval' && (
                      <button
                        onClick={() => approveMutation.mutate(plan.id)}
                        className="px-3 py-1 bg-green-500 hover:bg-green-600 text-white rounded text-sm"
                      >
                        Approve
                      </button>
                    )}
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

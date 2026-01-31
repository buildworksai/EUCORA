// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * E17: SecOps Dashboard
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Shield, AlertTriangle, CheckCircle, FileText, RefreshCw } from 'lucide-react';
import { api } from '@/lib/api/client';
import { ENDPOINTS, type SecOpsSummary, type VulnerabilityInstance, type RemediationPlan } from './contracts';

export default function SecOpsDashboard() {
  const queryClient = useQueryClient();

  const { data: summary } = useQuery({
    queryKey: ['secops', 'summary'],
    queryFn: () => api.get<SecOpsSummary>(ENDPOINTS.reportsSummary),
  });

  const { data: vulnerabilities } = useQuery({
    queryKey: ['secops', 'instances'],
    queryFn: async () => {
      const response = await api.get<{ results: VulnerabilityInstance[] } | VulnerabilityInstance[]>(ENDPOINTS.instances + '?status=open&limit=20');
      return Array.isArray(response) ? response : response.results || [];
    },
  });

  const { data: remediationPlans } = useQuery({
    queryKey: ['secops', 'remediation-plans'],
    queryFn: async () => {
      const response = await api.get<{ results: RemediationPlan[] } | RemediationPlan[]>(ENDPOINTS.remediationPlans + '?status=pending_approval');
      return Array.isArray(response) ? response : response.results || [];
    },
  });

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

  const remediateMutation = useMutation({
    mutationFn: async (id: string) => {
      return api.post(ENDPOINTS.instanceRemediate(id), { notes: 'Remediated via dashboard' });
    },
    onSuccess: () => {
      toast.success('Vulnerability marked as remediated');
      queryClient.invalidateQueries({ queryKey: ['secops'] });
    },
  });

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">SecOps</h1>
        <button
          onClick={() => queryClient.invalidateQueries({ queryKey: ['secops'] })}
          className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg flex items-center gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Risk Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            <h3 className="font-semibold">Critical</h3>
          </div>
          <p className="text-3xl font-bold text-red-600">{summary?.critical_vulnerabilities || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <Shield className="h-5 w-5 text-orange-500" />
            <h3 className="font-semibold">High</h3>
          </div>
          <p className="text-3xl font-bold text-orange-600">{summary?.high_vulnerabilities || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <FileText className="h-5 w-5 text-yellow-500" />
            <h3 className="font-semibold">Pending Plans</h3>
          </div>
          <p className="text-3xl font-bold text-yellow-600">{summary?.pending_remediation_plans || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="h-5 w-5 text-green-500" />
            <h3 className="font-semibold">Executing</h3>
          </div>
          <p className="text-3xl font-bold text-green-600">{summary?.executing_remediation_plans || 0}</p>
        </div>
      </div>

      {/* Remediation Plans */}
      {remediationPlans && remediationPlans.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-4">Pending Remediation Plans</h2>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium">Plan Name</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">CVE</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Type</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Risk Level</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Affected Instances</th>
                </tr>
              </thead>
              <tbody>
                {remediationPlans.slice(0, 10).map((plan: RemediationPlan) => (
                  <tr key={plan.id} className="border-t border-gray-200 dark:border-gray-700">
                    <td className="px-4 py-3 text-sm">{plan.name}</td>
                    <td className="px-4 py-3 text-sm font-mono">{plan.vulnerability_cve}</td>
                    <td className="px-4 py-3 text-sm">{plan.remediation_type}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-1 rounded text-xs ${
                          plan.risk_level === 'R3'
                            ? 'bg-red-100 text-red-800'
                            : plan.risk_level === 'R2'
                              ? 'bg-orange-100 text-orange-800'
                              : 'bg-blue-100 text-blue-800'
                        }`}
                      >
                        {plan.risk_level}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">{plan.affected_instance_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Vulnerability Queue */}
      <section>
        <h2 className="text-lg font-semibold mb-4">Vulnerability Queue</h2>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium">CVE</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Severity</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Asset</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Detected</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {vulnerabilities?.slice(0, 20).map((vuln: VulnerabilityInstance) => (
                <tr key={vuln.id} className="border-t border-gray-200 dark:border-gray-700">
                  <td className="px-4 py-3 text-sm font-mono">{vuln.vulnerability_cve}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs ${getSeverityColor(vuln.vulnerability_severity)}`}>
                      {vuln.vulnerability_severity}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">{vuln.asset_name}</td>
                  <td className="px-4 py-3 text-sm">{new Date(vuln.detected_at).toLocaleDateString()}</td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200">
                      {vuln.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {vuln.status === 'open' && (
                      <button
                        onClick={() => remediateMutation.mutate(vuln.id)}
                        disabled={remediateMutation.isPending}
                        className="px-3 py-1 bg-green-100 hover:bg-green-200 text-green-700 rounded text-sm disabled:opacity-50"
                      >
                        Mark Remediated
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

// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * E15: IAM Security Dashboard
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Shield, AlertTriangle, AlertCircle, Clock } from 'lucide-react';
import { api } from '@/lib/api/client';
import { ENDPOINTS, type AnomalyDetection, type SecuritySummary } from './contracts';

export default function IAMSecurityDashboard() {
  const queryClient = useQueryClient();

  const { data: summary } = useQuery({
    queryKey: ['iam-security', 'summary'],
    queryFn: () => api.get<SecuritySummary>(ENDPOINTS.reportsSummary),
  });

  const { data: anomalies } = useQuery({
    queryKey: ['iam-security', 'anomalies'],
    queryFn: () => api.get<AnomalyDetection[]>(ENDPOINTS.anomalies),
  });

  const investigateMutation = useMutation({
    mutationFn: async (id: string) => {
      return api.post(ENDPOINTS.anomalyInvestigate(id), {});
    },
    onSuccess: () => {
      toast.success('Anomaly marked as investigating');
      queryClient.invalidateQueries({ queryKey: ['iam-security'] });
    },
  });

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800';
      case 'high':
        return 'bg-orange-100 text-orange-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">IAM Security</h1>
      </div>

      {/* Threat Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <Shield className="h-5 w-5 text-blue-500" />
            <h3 className="font-semibold">Total Anomalies</h3>
          </div>
          <p className="text-3xl font-bold">{summary?.total_anomalies || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            <h3 className="font-semibold">Critical</h3>
          </div>
          <p className="text-3xl font-bold text-red-600">{summary?.critical || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="h-5 w-5 text-orange-500" />
            <h3 className="font-semibold">High</h3>
          </div>
          <p className="text-3xl font-bold text-orange-600">{summary?.high || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="h-5 w-5 text-yellow-500" />
            <h3 className="font-semibold">New</h3>
          </div>
          <p className="text-3xl font-bold text-yellow-600">{summary?.new || 0}</p>
        </div>
      </div>

      {/* Anomaly Queue */}
      <section>
        <h2 className="text-lg font-semibold mb-4">Anomaly Queue</h2>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium">Type</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Severity</th>
                <th className="px-4 py-3 text-left text-sm font-medium">User</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Description</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {anomalies?.slice(0, 20).map((anomaly: AnomalyDetection) => (
                <tr key={anomaly.id} className="border-t border-gray-200 dark:border-gray-700">
                  <td className="px-4 py-3 text-sm">{anomaly.anomaly_type}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs ${getSeverityColor(anomaly.severity)}`}>
                      {anomaly.severity}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">{anomaly.user_principal}</td>
                  <td className="px-4 py-3 text-sm">{anomaly.description}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-1 rounded text-xs ${
                        anomaly.status === 'resolved'
                          ? 'bg-green-100 text-green-800'
                          : anomaly.status === 'investigating'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {anomaly.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {anomaly.status === 'new' && (
                      <button
                        onClick={() => investigateMutation.mutate(anomaly.id)}
                        className="px-3 py-1 bg-blue-100 hover:bg-blue-200 text-blue-700 rounded text-sm"
                      >
                        Investigate
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

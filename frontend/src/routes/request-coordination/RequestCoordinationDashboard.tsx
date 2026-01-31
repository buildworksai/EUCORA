// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * E16: Request Coordination Dashboard
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Clock, AlertTriangle, CheckCircle, TrendingUp } from 'lucide-react';
import { api } from '@/lib/api/client';
import {
  ENDPOINTS,
  type TrackedRequest,
  type EscalationEvent,
  type SLAComplianceReport,
} from './contracts';

export default function RequestCoordinationDashboard() {
  const queryClient = useQueryClient();

  const { data: requests } = useQuery({
    queryKey: ['request-coordination', 'requests'],
    queryFn: () => api.get<TrackedRequest[]>(ENDPOINTS.requests),
  });

  const { data: escalations } = useQuery({
    queryKey: ['request-coordination', 'escalations'],
    queryFn: () => api.get<EscalationEvent[]>(ENDPOINTS.escalations),
  });

  const { data: slaCompliance } = useQuery({
    queryKey: ['request-coordination', 'sla-compliance'],
    queryFn: () => api.get<SLAComplianceReport>(ENDPOINTS.reportsSLACompliance),
  });

  // Workload report available but not displayed in current UI
  // const { data: workload } = useQuery({
  //   queryKey: ['request-coordination', 'workload'],
  //   queryFn: () => api.get<WorkloadReport>(ENDPOINTS.reportsWorkload),
  // });

  const syncMutation = useMutation({
    mutationFn: async (connectionId: string) => {
      return api.post(ENDPOINTS.requestSync, { connection_id: connectionId });
    },
    onSuccess: () => {
      toast.success('Requests synced successfully');
      queryClient.invalidateQueries({ queryKey: ['request-coordination'] });
    },
    onError: () => {
      toast.error('Failed to sync requests');
    },
  });

  const resolveEscalationMutation = useMutation({
    mutationFn: async (id: string) => {
      return api.post(ENDPOINTS.escalationResolve(id), { un_escalate: true });
    },
    onSuccess: () => {
      toast.success('Escalation resolved');
      queryClient.invalidateQueries({ queryKey: ['request-coordination'] });
    },
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'resolved':
      case 'closed':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case '1':
        return 'bg-red-100 text-red-800';
      case '2':
        return 'bg-orange-100 text-orange-800';
      case '3':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  const openRequests = requests?.filter((r) => !['resolved', 'closed', 'cancelled'].includes(r.status)) || [];
  const slaAtRisk = requests?.filter((r) => r.sla_status === 'warning' || r.sla_status === 'breached') || [];
  const escalatedRequests = requests?.filter((r) => r.is_escalated) || [];
  const completedToday =
    requests?.filter((r) => r.status === 'closed' && new Date(r.updated_at).toDateString() === new Date().toDateString()) ||
    [];

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Request Coordination</h1>
        <button
          onClick={() => syncMutation.mutate('mock-connection-id')}
          disabled={syncMutation.isPending}
          className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg disabled:opacity-50"
        >
          {syncMutation.isPending ? 'Syncing...' : 'Sync Requests'}
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="h-5 w-5 text-blue-500" />
            <h3 className="font-semibold">Open Requests</h3>
          </div>
          <p className="text-3xl font-bold">{openRequests.length}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="h-5 w-5 text-orange-500" />
            <h3 className="font-semibold">SLA at Risk</h3>
          </div>
          <p className="text-3xl font-bold text-orange-600">{slaAtRisk.length}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="h-5 w-5 text-red-500" />
            <h3 className="font-semibold">Escalated</h3>
          </div>
          <p className="text-3xl font-bold text-red-600">{escalatedRequests.length}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="h-5 w-5 text-green-500" />
            <h3 className="font-semibold">Completed Today</h3>
          </div>
          <p className="text-3xl font-bold text-green-600">{completedToday.length}</p>
        </div>
      </div>

      {/* SLA Compliance */}
      {slaCompliance && (
        <section>
          <h2 className="text-lg font-semibold mb-4">SLA Compliance</h2>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-3xl font-bold">{slaCompliance.compliance_rate.toFixed(1)}%</p>
                <p className="text-sm text-gray-500">Compliance Rate</p>
              </div>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <p className="text-2xl font-bold text-green-600">{slaCompliance.compliant}</p>
                  <p className="text-xs text-gray-500">Compliant</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-orange-600">{slaCompliance.at_risk}</p>
                  <p className="text-xs text-gray-500">At Risk</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-red-600">{slaCompliance.breached}</p>
                  <p className="text-xs text-gray-500">Breached</p>
                </div>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Request Queue */}
      <section>
        <h2 className="text-lg font-semibold mb-4">Request Queue</h2>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium">Number</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Description</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Requestor</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Priority</th>
                <th className="px-4 py-3 text-left text-sm font-medium">SLA Due</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Escalated</th>
              </tr>
            </thead>
            <tbody>
              {requests?.slice(0, 20).map((request: TrackedRequest) => (
                <tr key={request.id} className="border-t border-gray-200 dark:border-gray-700">
                  <td className="px-4 py-3 text-sm font-mono">{request.servicenow_number}</td>
                  <td className="px-4 py-3 text-sm">{request.short_description}</td>
                  <td className="px-4 py-3 text-sm">{request.requestor_name}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs ${getStatusColor(request.status)}`}>
                      {request.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs ${getPriorityColor(request.priority)}`}>
                      {request.priority}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {request.sla_due ? new Date(request.sla_due).toLocaleString() : '-'}
                  </td>
                  <td className="px-4 py-3">
                    {request.is_escalated ? (
                      <span className="px-2 py-1 rounded text-xs bg-red-100 text-red-800">
                        L{request.escalation_level}
                      </span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Escalation Queue */}
      {escalations && escalations.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-4">Escalation Queue</h2>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium">Request</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Level</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Reason</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Created</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {escalations
                  .filter((e) => !e.resolved_at)
                  .slice(0, 10)
                  .map((escalation: EscalationEvent) => (
                    <tr key={escalation.id} className="border-t border-gray-200 dark:border-gray-700">
                      <td className="px-4 py-3 text-sm font-mono">{escalation.request_number}</td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-1 rounded text-xs bg-red-100 text-red-800">
                          L{escalation.escalation_level}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm">{escalation.trigger_reason}</td>
                      <td className="px-4 py-3 text-sm">{new Date(escalation.created_at).toLocaleString()}</td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() => resolveEscalationMutation.mutate(escalation.id)}
                          className="px-3 py-1 bg-green-100 hover:bg-green-200 text-green-700 rounded text-sm"
                        >
                          Resolve
                        </button>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}

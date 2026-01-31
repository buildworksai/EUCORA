// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * E10: CMDB Integration Dashboard
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  Database,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Settings,
  Play,
  FileText,
} from 'lucide-react';
import { api } from '@/lib/api/client';
import {
  ENDPOINTS,
  type CMDBConnection,
  type CMDBDiscrepancy,
  type CMDBSyncRecord,
  type CMDBQualityScore,
} from './contracts';

// Quality Score Card Component
function QualityScoreCard({ score }: { score: CMDBQualityScore | undefined }) {
  if (!score) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-2 mb-4">
          <FileText className="h-5 w-5 text-blue-500" />
          <h3 className="font-semibold">Data Quality</h3>
        </div>
        <p className="text-gray-500">No quality data available</p>
      </div>
    );
  }

  const getScoreColor = (val: number) => {
    if (val >= 90) return 'text-green-600';
    if (val >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-blue-500" />
          <h3 className="font-semibold">Data Quality</h3>
        </div>
        <span className={`text-2xl font-bold ${getScoreColor(score.overall_score)}`}>
          {score.overall_score}%
        </span>
      </div>
      <div className="space-y-3">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">Completeness</span>
          <span className={getScoreColor(score.completeness)}>{score.completeness}%</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">Accuracy</span>
          <span className={getScoreColor(score.accuracy)}>{score.accuracy}%</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">Consistency</span>
          <span className={getScoreColor(score.consistency)}>{score.consistency}%</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">Timeliness</span>
          <span className={getScoreColor(score.timeliness)}>{score.timeliness}%</span>
        </div>
      </div>
      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500">
        {score.records_analyzed} records analyzed • {score.issues_found} issues found
      </div>
    </div>
  );
}

// Connection Card Component
function ConnectionCard({
  connection,
  onSync,
  isSyncing,
}: {
  connection: CMDBConnection;
  onSync: (id: string) => void;
  isSyncing: boolean;
}) {
  const statusIcon = {
    success: <CheckCircle className="h-4 w-4 text-green-500" />,
    failed: <XCircle className="h-4 w-4 text-red-500" />,
    pending: <Clock className="h-4 w-4 text-yellow-500" />,
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Database className="h-8 w-8 text-blue-500" />
          <div>
            <h4 className="font-medium">{connection.name}</h4>
            <p className="text-sm text-gray-500">{connection.instance_url}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {statusIcon[connection.test_status]}
          <button
            onClick={() => onSync(connection.id)}
            disabled={isSyncing || !connection.is_active}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50"
            title="Start Sync"
          >
            {isSyncing ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>
      {connection.last_sync && (
        <p className="mt-2 text-xs text-gray-500">
          Last sync: {new Date(connection.last_sync).toLocaleString()}
        </p>
      )}
    </div>
  );
}

// Discrepancy Row Component
function DiscrepancyRow({
  discrepancy,
  onApprove,
  onReject,
}: {
  discrepancy: CMDBDiscrepancy;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
}) {
  const typeColors: Record<string, string> = {
    missing: 'bg-red-100 text-red-800',
    mismatch: 'bg-yellow-100 text-yellow-800',
    orphan: 'bg-purple-100 text-purple-800',
    duplicate: 'bg-orange-100 text-orange-800',
    stale: 'bg-gray-100 text-gray-800',
    incomplete: 'bg-blue-100 text-blue-800',
  };

  return (
    <tr className="border-b border-gray-200 dark:border-gray-700">
      <td className="py-3 px-4">
        <span
          className={`px-2 py-1 rounded-full text-xs font-medium ${typeColors[discrepancy.discrepancy_type]}`}
        >
          {discrepancy.discrepancy_type}
        </span>
      </td>
      <td className="py-3 px-4 text-sm">{discrepancy.table_name}</td>
      <td className="py-3 px-4 text-sm">{discrepancy.field_name || '-'}</td>
      <td className="py-3 px-4 text-sm">
        <div className="flex flex-col gap-1">
          <span className="text-gray-500">Source: {discrepancy.source_value || 'null'}</span>
          <span className="text-gray-500">CMDB: {discrepancy.cmdb_value || 'null'}</span>
        </div>
      </td>
      <td className="py-3 px-4 text-sm">{discrepancy.recommended_action}</td>
      <td className="py-3 px-4">
        {discrepancy.status === 'open' && (
          <div className="flex gap-2">
            <button
              onClick={() => onApprove(discrepancy.id)}
              className="p-1 rounded bg-green-100 hover:bg-green-200 text-green-700"
              title="Approve"
            >
              <CheckCircle className="h-4 w-4" />
            </button>
            <button
              onClick={() => onReject(discrepancy.id)}
              className="p-1 rounded bg-red-100 hover:bg-red-200 text-red-700"
              title="Reject"
            >
              <XCircle className="h-4 w-4" />
            </button>
          </div>
        )}
        {discrepancy.status !== 'open' && (
          <span
            className={`px-2 py-1 rounded text-xs ${
              discrepancy.status === 'approved'
                ? 'bg-green-100 text-green-800'
                : 'bg-gray-100 text-gray-800'
            }`}
          >
            {discrepancy.status}
          </span>
        )}
      </td>
    </tr>
  );
}

export default function CMDBDashboard() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'overview' | 'discrepancies' | 'history'>('overview');

  // Fetch connections
  const { data: connections = [], isLoading: loadingConnections } = useQuery({
    queryKey: ['cmdb-connections'],
    queryFn: () => api.get<CMDBConnection[]>(ENDPOINTS.connections),
  });

  // Fetch discrepancies
  const { data: discrepancies = [], isLoading: loadingDiscrepancies } = useQuery({
    queryKey: ['cmdb-discrepancies'],
    queryFn: () => api.get<CMDBDiscrepancy[]>(ENDPOINTS.discrepancies),
  });

  // Fetch quality score
  const { data: qualityScore } = useQuery({
    queryKey: ['cmdb-quality-score'],
    queryFn: () => api.get<CMDBQualityScore>(ENDPOINTS.qualityScore),
  });

  // Fetch sync records
  const { data: syncRecords = [] } = useQuery({
    queryKey: ['cmdb-sync-records'],
    queryFn: () => api.get<CMDBSyncRecord[]>(ENDPOINTS.syncRecords),
  });

  // Start sync mutation
  const syncMutation = useMutation({
    mutationFn: (connectionId: string) => api.post<CMDBSyncRecord>(ENDPOINTS.syncStart(connectionId), {}),
    onSuccess: () => {
      toast.success('Sync started successfully');
      queryClient.invalidateQueries({ queryKey: ['cmdb-sync-records'] });
    },
    onError: () => {
      toast.error('Failed to start sync');
    },
  });

  // Approve discrepancy mutation
  const approveMutation = useMutation({
    mutationFn: (id: string) => api.post<CMDBDiscrepancy>(ENDPOINTS.discrepancyApprove(id), {}),
    onSuccess: () => {
      toast.success('Discrepancy approved');
      queryClient.invalidateQueries({ queryKey: ['cmdb-discrepancies'] });
    },
  });

  // Reject discrepancy mutation
  const rejectMutation = useMutation({
    mutationFn: (id: string) => api.post<CMDBDiscrepancy>(ENDPOINTS.discrepancyReject(id), {}),
    onSuccess: () => {
      toast.success('Discrepancy rejected');
      queryClient.invalidateQueries({ queryKey: ['cmdb-discrepancies'] });
    },
  });

  const openDiscrepancies = discrepancies.filter((d: CMDBDiscrepancy) => d.status === 'open');

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Database className="h-6 w-6 text-blue-500" />
            CMDB Integration
          </h1>
          <p className="text-gray-500 mt-1">
            Manage ServiceNow CMDB connections, sync operations, and discrepancies
          </p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          <Settings className="h-4 w-4" />
          Configure
        </button>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="flex gap-4">
          {(['overview', 'discrepancies', 'history'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`pb-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
              {tab === 'discrepancies' && openDiscrepancies.length > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-red-100 text-red-800 rounded-full text-xs">
                  {openDiscrepancies.length}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Connections */}
          <div className="lg:col-span-2 space-y-4">
            <h3 className="font-semibold text-lg">CMDB Connections</h3>
            {loadingConnections ? (
              <div className="text-center py-8 text-gray-500">Loading connections...</div>
            ) : connections.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No CMDB connections configured. Add a connection to get started.
              </div>
            ) : (
              <div className="space-y-3">
                {connections.map((conn: CMDBConnection) => (
                  <ConnectionCard
                    key={conn.id}
                    connection={conn}
                    onSync={(id) => syncMutation.mutate(id)}
                    isSyncing={syncMutation.isPending}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Quality Score */}
          <div>
            <QualityScoreCard score={qualityScore} />
          </div>
        </div>
      )}

      {/* Discrepancies Tab */}
      {activeTab === 'discrepancies' && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              <h3 className="font-semibold">Discrepancies</h3>
              <span className="text-sm text-gray-500">({discrepancies.length} total)</span>
            </div>
          </div>
          {loadingDiscrepancies ? (
            <div className="text-center py-8 text-gray-500">Loading discrepancies...</div>
          ) : discrepancies.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No discrepancies found. Run a sync to detect discrepancies.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-900">
                  <tr>
                    <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                      Type
                    </th>
                    <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                      Table
                    </th>
                    <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                      Field
                    </th>
                    <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                      Values
                    </th>
                    <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                      Recommended
                    </th>
                    <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {discrepancies.map((d: CMDBDiscrepancy) => (
                    <DiscrepancyRow
                      key={d.id}
                      discrepancy={d}
                      onApprove={(id) => approveMutation.mutate(id)}
                      onReject={(id) => rejectMutation.mutate(id)}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* History Tab */}
      {activeTab === 'history' && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold">Sync History</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Connection
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Type
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Records
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Started
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 uppercase">
                    Duration
                  </th>
                </tr>
              </thead>
              <tbody>
                {syncRecords.map((record: CMDBSyncRecord) => (
                  <tr key={record.id} className="border-b border-gray-200 dark:border-gray-700">
                    <td className="py-3 px-4 text-sm">{record.connection_name}</td>
                    <td className="py-3 px-4 text-sm">{record.sync_type}</td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          record.status === 'completed'
                            ? 'bg-green-100 text-green-800'
                            : record.status === 'failed'
                              ? 'bg-red-100 text-red-800'
                              : record.status === 'running'
                                ? 'bg-blue-100 text-blue-800'
                                : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {record.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-sm">
                      {record.records_processed} processed / {record.records_created} created /{' '}
                      {record.records_updated} updated
                    </td>
                    <td className="py-3 px-4 text-sm">
                      {record.started_at ? new Date(record.started_at).toLocaleString() : '-'}
                    </td>
                    <td className="py-3 px-4 text-sm">
                      {record.started_at && record.completed_at
                        ? `${Math.round(
                            (new Date(record.completed_at).getTime() -
                              new Date(record.started_at).getTime()) /
                              1000
                          )}s`
                        : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

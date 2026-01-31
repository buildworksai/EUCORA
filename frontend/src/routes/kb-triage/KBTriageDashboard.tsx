// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * E21: KB & Triage Dashboard
 */
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { BookOpen, Search, TrendingUp, CheckCircle, RefreshCw } from 'lucide-react';
import { api } from '@/lib/api/client';
import { ENDPOINTS, type TriageRequest, type TriageAccuracy, type IncidentPattern } from './contracts';

export default function KBTriageDashboard() {
  const queryClient = useQueryClient();

  const { data: accuracy } = useQuery({
    queryKey: ['kb-triage', 'accuracy'],
    queryFn: () => api.get<TriageAccuracy>(ENDPOINTS.reportsAccuracy),
  });

  const { data: triageRequests } = useQuery({
    queryKey: ['kb-triage', 'triage'],
    queryFn: () => api.get<TriageRequest[]>(ENDPOINTS.triage + '?status=pending&limit=20'),
  });

  const { data: patterns } = useQuery({
    queryKey: ['kb-triage', 'patterns'],
    queryFn: () => api.get<IncidentPattern[]>(ENDPOINTS.patterns + '?status=active&limit=10'),
  });

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">KB & Triage</h1>
        <button
          onClick={() => queryClient.invalidateQueries({ queryKey: ['kb-triage'] })}
          className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg flex items-center gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Triage Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <BookOpen className="h-5 w-5 text-blue-500" />
            <h3 className="font-semibold">Pending</h3>
          </div>
          <p className="text-3xl font-bold">{triageRequests?.length || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="h-5 w-5 text-green-500" />
            <h3 className="font-semibold">Accuracy</h3>
          </div>
          <p className="text-3xl font-bold text-green-600">
            {accuracy ? `${accuracy.overall_accuracy.toFixed(1)}%` : '0%'}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <Search className="h-5 w-5 text-purple-500" />
            <h3 className="font-semibold">Total Feedback</h3>
          </div>
          <p className="text-3xl font-bold text-purple-600">{accuracy?.total_feedback || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="h-5 w-5 text-orange-500" />
            <h3 className="font-semibold">Accurate</h3>
          </div>
          <p className="text-3xl font-bold text-orange-600">{accuracy?.accurate_feedback || 0}</p>
        </div>
      </div>

      {/* Incident Patterns */}
      {patterns && patterns.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-4">Active Incident Patterns</h2>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium">Pattern</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Type</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Occurrences</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Affected Users</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Last Detected</th>
                </tr>
              </thead>
              <tbody>
                {patterns.slice(0, 10).map((pattern: IncidentPattern) => (
                  <tr key={pattern.id} className="border-t border-gray-200 dark:border-gray-700">
                    <td className="px-4 py-3 text-sm font-medium">{pattern.name}</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-1 rounded text-xs bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">
                        {pattern.pattern_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">{pattern.occurrence_count}</td>
                    <td className="px-4 py-3 text-sm">{pattern.affected_users}</td>
                    <td className="px-4 py-3 text-sm">{new Date(pattern.last_detected).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Triage Queue */}
      <section>
        <h2 className="text-lg font-semibold mb-4">Triage Queue</h2>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium">Ticket</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Caller</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Description</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Category</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Priority</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {triageRequests?.slice(0, 20).map((request: TriageRequest) => (
                <tr key={request.id} className="border-t border-gray-200 dark:border-gray-700">
                  <td className="px-4 py-3 text-sm font-mono">{request.servicenow_number || 'N/A'}</td>
                  <td className="px-4 py-3 text-sm">{request.caller_name}</td>
                  <td className="px-4 py-3 text-sm">{request.short_description}</td>
                  <td className="px-4 py-3 text-sm">{request.suggested_category || 'N/A'}</td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200">
                      {request.suggested_priority || 'N/A'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {request.confidence_score ? `${(request.confidence_score * 100).toFixed(0)}%` : 'N/A'}
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

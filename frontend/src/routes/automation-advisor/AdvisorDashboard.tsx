// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * E13: Automation Advisor Dashboard
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { TrendingUp, DollarSign, Clock, CheckCircle } from 'lucide-react';
import { api } from '@/lib/api/client';
import { ENDPOINTS, type AutomationCandidate, type AutomationSummary } from './contracts';

export default function AdvisorDashboard() {
  const queryClient = useQueryClient();

  const { data: summary } = useQuery({
    queryKey: ['automation-advisor', 'summary'],
    queryFn: () => api.get<AutomationSummary>(ENDPOINTS.reportsSummary),
  });

  const { data: candidates } = useQuery({
    queryKey: ['automation-advisor', 'candidates'],
    queryFn: () => api.get<AutomationCandidate[]>(ENDPOINTS.candidates),
  });

  const approveMutation = useMutation({
    mutationFn: async (id: string) => {
      return api.post(ENDPOINTS.candidateApprove(id), {});
    },
    onSuccess: () => {
      toast.success('Candidate approved');
      queryClient.invalidateQueries({ queryKey: ['automation-advisor'] });
    },
  });

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Automation Advisor</h1>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="h-5 w-5 text-blue-500" />
            <h3 className="font-semibold">Total Opportunities</h3>
          </div>
          <p className="text-3xl font-bold">{summary?.total_opportunities || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <DollarSign className="h-5 w-5 text-green-500" />
            <h3 className="font-semibold">Potential Savings</h3>
          </div>
          <p className="text-3xl font-bold">
            ${((summary?.potential_annual_savings || 0) / 1000).toFixed(0)}K
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="h-5 w-5 text-yellow-500" />
            <h3 className="font-semibold">Pending Review</h3>
          </div>
          <p className="text-3xl font-bold">{summary?.pending_review || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="h-5 w-5 text-green-500" />
            <h3 className="font-semibold">Implemented</h3>
          </div>
          <p className="text-3xl font-bold">{summary?.implemented || 0}</p>
        </div>
      </div>

      {/* Top Opportunities */}
      <section>
        <h2 className="text-lg font-semibold mb-4">Top Opportunities</h2>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium">Title</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Score</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Annual Savings</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Payback</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Status</th>
                <th className="px-4 py-3 text-left text-sm font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {candidates?.slice(0, 10).map((candidate: AutomationCandidate) => (
                <tr key={candidate.id} className="border-t border-gray-200 dark:border-gray-700">
                  <td className="px-4 py-3 text-sm">{candidate.title}</td>
                  <td className="px-4 py-3 text-sm">{candidate.overall_score.toFixed(1)}</td>
                  <td className="px-4 py-3 text-sm">
                    ${(candidate.estimated_annual_savings / 1000).toFixed(1)}K
                  </td>
                  <td className="px-4 py-3 text-sm">{candidate.payback_period_months.toFixed(1)} months</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-1 rounded text-xs ${
                        candidate.status === 'approved'
                          ? 'bg-green-100 text-green-800'
                          : candidate.status === 'rejected'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {candidate.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {candidate.status === 'identified' && (
                      <button
                        onClick={() => approveMutation.mutate(candidate.id)}
                        className="px-3 py-1 bg-green-100 hover:bg-green-200 text-green-700 rounded text-sm"
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
